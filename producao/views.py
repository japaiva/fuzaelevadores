# producao/views.py - CORREÇÃO DOS IMPORTS

import logging
from datetime import datetime, timedelta, timezone
from django.db import models
from django.urls import reverse
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_GET, require_POST

from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    FornecedorProduto, PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra
)
from core.forms import (
    ProdutoForm, GrupoProdutoForm, SubgrupoProdutoForm, 
    FornecedorForm, FornecedorProdutoFormSet,
    PedidoCompraForm, ItemPedidoCompraFormSet, PedidoCompraFiltroForm,
    AlterarStatusPedidoForm, RecebimentoItemForm
)

from core.utils.pdf_generator import gerar_pdf_pedido_compra

logger = logging.getLogger(__name__)

# =============================================================================
# PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial do Portal de Produção"""
    return render(request, 'producao/home.html')

@login_required
def dashboard(request):
    """Dashboard da produção com estatísticas"""
    context = {
        'total_materias_primas': Produto.objects.filter(tipo='MP').count(),
        'total_produtos_intermediarios': Produto.objects.filter(tipo='PI').count(),
        'total_produtos_acabados': Produto.objects.filter(tipo='PA').count(),
        'total_fornecedores': Fornecedor.objects.filter(ativo=True).count(),
        'produtos_sem_estoque': Produto.objects.filter(
            controla_estoque=True, 
            estoque_atual__lte=models.F('estoque_minimo')
        ).count() if Produto.objects.exists() else 0,
        'produtos_indisponiveis': Produto.objects.filter(disponivel=False).count(),
    }
    return render(request, 'producao/dashboard.html', context)

# =============================================================================
# CRUD FORNECEDORES
# =============================================================================

@login_required
def fornecedor_list(request):
    fornecedores_list = Fornecedor.objects.all().order_by('razao_social')
    
    # Filtros
    status = request.GET.get('status')
    if status == 'ativo':
        fornecedores_list = fornecedores_list.filter(ativo=True)
    elif status == 'inativo':
        fornecedores_list = fornecedores_list.filter(ativo=False)
    
    query = request.GET.get('q')
    if query:
        fornecedores_list = fornecedores_list.filter(
            Q(razao_social__icontains=query) | 
            Q(nome_fantasia__icontains=query) |
            Q(cnpj__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(fornecedores_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        fornecedores = paginator.page(page)
    except PageNotAnInteger:
        fornecedores = paginator.page(1)
    except EmptyPage:
        fornecedores = paginator.page(paginator.num_pages)
    
    return render(request, 'producao/fornecedor_list.html', {
        'fornecedores': fornecedores,
        'status_filtro': status,
        'query': query
    })

@login_required
def fornecedor_create(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save(commit=False)
            fornecedor.criado_por = request.user
            fornecedor.save()
            messages.success(request, f'Fornecedor "{fornecedor.razao_social}" criado com sucesso.')
            return redirect('producao:fornecedor_list')
    else:
        form = FornecedorForm()
    return render(request, 'producao/fornecedor_form.html', {'form': form})

@login_required
def fornecedor_update(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fornecedor "{fornecedor.razao_social}" atualizado com sucesso.')
            return redirect('producao:fornecedor_list')
    else:
        form = FornecedorForm(instance=fornecedor)
    return render(request, 'producao/fornecedor_form.html', {'form': form, 'fornecedor': fornecedor})

@login_required
def fornecedor_delete(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        fornecedor.delete()
        messages.success(request, 'Fornecedor excluído com sucesso.')
        return redirect('producao:fornecedor_list')

    return render(request, 'producao/fornecedor_delete.html', {'fornecedor': fornecedor})

@login_required
def fornecedor_toggle_status(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    fornecedor.ativo = not fornecedor.ativo
    fornecedor.save()
    
    status_text = "ativado" if fornecedor.ativo else "desativado"
    messages.success(request, f'Fornecedor "{fornecedor.razao_social}" {status_text} com sucesso.')
    
    return redirect('producao:fornecedor_list')

# =============================================================================
# CRUD GRUPOS DE PRODUTOS
# =============================================================================

@login_required
def grupo_list(request):
    grupos_list = GrupoProduto.objects.all().order_by('codigo')
    
    # Filtros
    status = request.GET.get('status')
    if status == 'ativo':
        grupos_list = grupos_list.filter(ativo=True)
    elif status == 'inativo':
        grupos_list = grupos_list.filter(ativo=False)
    
    # NOVO: Filtro por tipo de produto
    tipo = request.GET.get('tipo')
    if tipo in ['MP', 'PI', 'PA']:
        grupos_list = grupos_list.filter(tipo_produto=tipo)
    
    query = request.GET.get('q')
    if query:
        grupos_list = grupos_list.filter(
            Q(codigo__icontains=query) | 
            Q(nome__icontains=query) |
            Q(descricao__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(grupos_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        grupos = paginator.page(page)
    except PageNotAnInteger:
        grupos = paginator.page(1)
    except EmptyPage:
        grupos = paginator.page(paginator.num_pages)
    
    return render(request, 'producao/grupo_list.html', {
        'grupos': grupos,
        'status_filtro': status,
        'tipo_filtro': tipo,  # NOVO: Passar tipo para o template
        'query': query
    })

@login_required
def grupo_create(request):
    if request.method == 'POST':
        form = GrupoProdutoForm(request.POST)
        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.criado_por = request.user
            grupo.save()
            messages.success(request, f'Grupo "{grupo.nome}" criado com sucesso.')
            return redirect('producao:grupo_list')
    else:
        form = GrupoProdutoForm()
    return render(request, 'producao/grupo_form.html', {'form': form})

@login_required
def grupo_update(request, pk):
    grupo = get_object_or_404(GrupoProduto, pk=pk)
    if request.method == 'POST':
        form = GrupoProdutoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupo "{grupo.nome}" atualizado com sucesso.')
            return redirect('producao:grupo_list')
    else:
        form = GrupoProdutoForm(instance=grupo)
    return render(request, 'producao/grupo_form.html', {'form': form, 'grupo': grupo})

@login_required
def grupo_delete(request, pk):
    grupo = get_object_or_404(GrupoProduto, pk=pk)

    if request.method == 'POST':
        try:
            grupo.delete()
            messages.success(request, 'Grupo excluído com sucesso.')
            return redirect('producao:grupo_list')
        except ProtectedError:
            messages.error(request, 'Este grupo não pode ser excluído pois possui subgrupos ou produtos vinculados.')
            return redirect('producao:grupo_list')

    return render(request, 'producao/grupo_delete.html', {'grupo': grupo})

@login_required
def grupo_toggle_status(request, pk):
    grupo = get_object_or_404(GrupoProduto, pk=pk)
    grupo.ativo = not grupo.ativo
    grupo.save()
    
    status_text = "ativado" if grupo.ativo else "desativado"
    messages.success(request, f'Grupo "{grupo.nome}" {status_text} com sucesso.')
    
    return redirect('producao:grupo_list')

# =============================================================================
# CRUD SUBGRUPOS DE PRODUTOS
# =============================================================================

@login_required
def subgrupo_list(request):
    subgrupos_list = SubgrupoProduto.objects.select_related('grupo').order_by('grupo__codigo', 'codigo')
    
    # Filtros
    grupo_id = request.GET.get('grupo')
    if grupo_id:
        subgrupos_list = subgrupos_list.filter(grupo_id=grupo_id)
    
    # NOVO: Filtro por tipo de produto
    tipo = request.GET.get('tipo')
    if tipo:
        subgrupos_list = subgrupos_list.filter(grupo__tipo_produto=tipo)
    
    status = request.GET.get('status')
    if status == 'ativo':
        subgrupos_list = subgrupos_list.filter(ativo=True)
    elif status == 'inativo':
        subgrupos_list = subgrupos_list.filter(ativo=False)
    
    query = request.GET.get('q')
    if query:
        subgrupos_list = subgrupos_list.filter(
            Q(codigo__icontains=query) | 
            Q(nome__icontains=query) |
            Q(grupo__nome__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(subgrupos_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        subgrupos = paginator.page(page)
    except PageNotAnInteger:
        subgrupos = paginator.page(1)
    except EmptyPage:
        subgrupos = paginator.page(paginator.num_pages)
    
    # Para o filtro de grupos
    grupos = GrupoProduto.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'producao/subgrupo_list.html', {
        'subgrupos': subgrupos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'tipo_filtro': tipo,  # NOVO
        'status_filtro': status,
        'query': query
    })

@login_required
def subgrupo_create(request):
    if request.method == 'POST':
        form = SubgrupoProdutoForm(request.POST)
        if form.is_valid():
            subgrupo = form.save(commit=False)
            subgrupo.criado_por = request.user
            subgrupo.save()
            messages.success(request, f'Subgrupo "{subgrupo.nome}" criado com sucesso.')
            return redirect('producao:subgrupo_list')
    else:
        # Se veio com grupo pré-selecionado
        grupo_id = request.GET.get('grupo')
        initial = {}
        if grupo_id:
            initial['grupo'] = grupo_id
        form = SubgrupoProdutoForm(initial=initial)
    
    return render(request, 'producao/subgrupo_form.html', {'form': form})

@login_required
def subgrupo_update(request, pk):
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)
    if request.method == 'POST':
        form = SubgrupoProdutoForm(request.POST, instance=subgrupo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subgrupo "{subgrupo.nome}" atualizado com sucesso.')
            return redirect('producao:subgrupo_list')
    else:
        form = SubgrupoProdutoForm(instance=subgrupo)
    return render(request, 'producao/subgrupo_form.html', {'form': form, 'subgrupo': subgrupo})

@login_required
def subgrupo_delete(request, pk):
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)

    if request.method == 'POST':
        try:
            subgrupo.delete()
            messages.success(request, 'Subgrupo excluído com sucesso.')
            return redirect('producao:subgrupo_list')
        except ProtectedError:
            messages.error(request, 'Este subgrupo não pode ser excluído pois possui produtos vinculados.')
            return redirect('producao:subgrupo_list')

    return render(request, 'producao/subgrupo_delete.html', {'subgrupo': subgrupo})

@login_required
def subgrupo_toggle_status(request, pk):
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)
    subgrupo.ativo = not subgrupo.ativo
    subgrupo.save()
    
    status_text = "ativado" if subgrupo.ativo else "desativado"
    messages.success(request, f'Subgrupo "{subgrupo.nome}" {status_text} com sucesso.')
    
    return redirect('producao:subgrupo_list')

# =============================================================================
# CRUD MATÉRIAS-PRIMAS (TIPO = MP) 
# =============================================================================

@login_required
def materiaprima_list(request):
    """Lista apenas produtos do tipo Matéria Prima (MP)"""
    produtos_list = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='MP').order_by('codigo')
    
    # Filtros
    grupo_id = request.GET.get('grupo')
    if grupo_id:
        produtos_list = produtos_list.filter(grupo_id=grupo_id)
    
    subgrupo_id = request.GET.get('subgrupo')
    if subgrupo_id:
        produtos_list = produtos_list.filter(subgrupo_id=subgrupo_id)
    
    status = request.GET.get('status')
    if status == 'ativo':
        produtos_list = produtos_list.filter(status='ATIVO')
    elif status == 'inativo':
        produtos_list = produtos_list.filter(status='INATIVO')
    elif status == 'disponivel':
        produtos_list = produtos_list.filter(disponivel=True)
    elif status == 'indisponivel':
        produtos_list = produtos_list.filter(disponivel=False)
    
    query = request.GET.get('q')
    if query:
        produtos_list = produtos_list.filter(
            Q(codigo__icontains=query) | 
            Q(nome__icontains=query) |
            Q(descricao__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(produtos_list, 20)
    page = request.GET.get('page', 1)
    
    try:
        produtos = paginator.page(page)
    except PageNotAnInteger:
        produtos = paginator.page(1)
    except EmptyPage:
        produtos = paginator.page(paginator.num_pages)
    
    # Para os filtros
    grupos = GrupoProduto.objects.filter(ativo=True, tipo_produto='MP').order_by('codigo')
    
    # Subgrupos - se tem grupo selecionado, filtrar por grupo
    if grupo_id:
        subgrupos = SubgrupoProduto.objects.filter(
            grupo_id=grupo_id, 
            ativo=True
        ).order_by('codigo')
    else:
        # Se não tem grupo selecionado, mostrar apenas subgrupos de grupos MP
        subgrupos = SubgrupoProduto.objects.filter(
            grupo__tipo_produto='MP',
            ativo=True
        ).select_related('grupo').order_by('grupo__codigo', 'codigo')
    
    return render(request, 'producao/materiaprima_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'subgrupos': subgrupos,
        'grupo_filtro': grupo_id,
        'subgrupo_filtro': subgrupo_id,
        'status_filtro': status,
        'query': query
    })


@login_required
def materiaprima_create(request):
    """Criar nova matéria-prima"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'MP'
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" criada com sucesso.')
            return redirect('producao:materiaprima_list') 
        else:
            messages.error(request, 'Erro ao criar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm()
    
    return render(request, 'producao/materiaprima_form.html', {'form': form})

@login_required
def materiaprima_update(request, pk):
    """Editar matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'MP'
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" atualizada com sucesso.')
            return redirect('producao:materiaprima_list') 
        else:
            messages.error(request, 'Erro ao atualizar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'producao/materiaprima_form.html', {
        'form': form, 
        'produto': produto
    })

@login_required
def materiaprima_toggle_status(request, pk):
    """Ativar/desativar matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if produto.status == 'ATIVO':
        produto.status = 'INATIVO'
        status_text = "desativada"
    else:
        produto.status = 'ATIVO'
        status_text = "ativada"
    
    produto.atualizado_por = request.user
    produto.save()
    messages.success(request, f'Matéria-prima "{produto.nome}" {status_text} com sucesso.')
    
    return redirect('producao:materiaprima_list')

@login_required
def materiaprima_detail(request, pk):
    """Visualizar detalhes de uma matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    context = {
        'produto': produto,
    }
    
    return render(request, 'producao/materiaprima_detail.html', context)

@login_required
def materiaprima_delete(request, pk):
    """Excluir matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" excluída com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir matéria-prima: {str(e)}')
        
        return redirect('producao:materiaprima_list')
    
    return render(request, 'producao/materiaprima_delete.html', {'produto': produto})

# =============================================================================
# CRUD PRODUTOS INTERMEDIÁRIOS (TIPO = PI)
# =============================================================================

@login_required
def produto_intermediario_list(request):
    """Lista apenas produtos do tipo Produto Intermediário (PI)"""
    produtos_list = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='PI').order_by('codigo')
    
    # Filtros similares às matérias-primas
    grupo_id = request.GET.get('grupo')
    if grupo_id:
        produtos_list = produtos_list.filter(grupo_id=grupo_id)
    
    status = request.GET.get('status')
    if status == 'ativo':
        produtos_list = produtos_list.filter(status='ATIVO')
    elif status == 'inativo':
        produtos_list = produtos_list.filter(status='INATIVO')
    elif status == 'disponivel':
        produtos_list = produtos_list.filter(disponivel=True)
    elif status == 'indisponivel':
        produtos_list = produtos_list.filter(disponivel=False)
    
    query = request.GET.get('q')
    if query:
        produtos_list = produtos_list.filter(
            Q(codigo__icontains=query) | 
            Q(nome__icontains=query) |
            Q(descricao__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(produtos_list, 20)
    page = request.GET.get('page', 1)
    
    try:
        produtos = paginator.page(page)
    except PageNotAnInteger:
        produtos = paginator.page(1)
    except EmptyPage:
        produtos = paginator.page(paginator.num_pages)
    
    grupos = GrupoProduto.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'producao/produto_intermediario_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'status_filtro': status,
        'query': query
    })

@login_required
def produto_intermediario_create(request):
    """Criar novo produto intermediário"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PI'
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Produto intermediário "{produto.codigo} - {produto.nome}" criado com sucesso.')
            return redirect('producao:produto_intermediario_list') 
        else:
            messages.error(request, 'Erro ao criar produto intermediário. Verifique os dados informados.')
    else:
        form = ProdutoForm()
    
    return render(request, 'producao/produto_intermediario_form.html', {'form': form})

@login_required
def produto_intermediario_update(request, pk):
    """Editar produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PI'
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Produto intermediário "{produto.codigo} - {produto.nome}" atualizado com sucesso.')
            return redirect('producao:produto_intermediario_list') 
        else:
            messages.error(request, 'Erro ao atualizar produto intermediário. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'producao/produto_intermediario_form.html', {
        'form': form, 
        'produto': produto
    })

@login_required
def produto_intermediario_toggle_status(request, pk):
    """Ativar/desativar produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI')
    
    if produto.status == 'ATIVO':
        produto.status = 'INATIVO'
        status_text = "desativado"
    else:
        produto.status = 'ATIVO'
        status_text = "ativado"
    
    produto.atualizado_por = request.user
    produto.save()
    messages.success(request, f'Produto intermediário "{produto.nome}" {status_text} com sucesso.')
    
    return redirect('producao:produto_intermediario_list')

@login_required
def produto_intermediario_delete(request, pk):
    """Excluir produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI')
    
    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, f'Produto intermediário "{produto.codigo} - {produto.nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir produto intermediário: {str(e)}')
        
        return redirect('producao:produto_intermediario_list')
    
    return render(request, 'producao/produto_intermediario_delete.html', {'produto': produto})

# =============================================================================
# CRUD PRODUTOS ACABADOS (TIPO = PA)
# =============================================================================

@login_required
def produto_acabado_list(request):
    """Lista apenas produtos do tipo Produto Acabado (PA)"""
    produtos_list = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='PA').order_by('codigo')
    
    # Filtros
    grupo_id = request.GET.get('grupo')
    if grupo_id:
        produtos_list = produtos_list.filter(grupo_id=grupo_id)
    
    status = request.GET.get('status')
    if status == 'ativo':
        produtos_list = produtos_list.filter(status='ATIVO')
    elif status == 'inativo':
        produtos_list = produtos_list.filter(status='INATIVO')
    elif status == 'disponivel':
        produtos_list = produtos_list.filter(disponivel=True)
    elif status == 'indisponivel':
        produtos_list = produtos_list.filter(disponivel=False)
    
    query = request.GET.get('q')
    if query:
        produtos_list = produtos_list.filter(
            Q(codigo__icontains=query) | 
            Q(nome__icontains=query) |
            Q(descricao__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(produtos_list, 20)
    page = request.GET.get('page', 1)
    
    try:
        produtos = paginator.page(page)
    except PageNotAnInteger:
        produtos = paginator.page(1)
    except EmptyPage:
        produtos = paginator.page(paginator.num_pages)
    
    grupos = GrupoProduto.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'producao/produto_acabado_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'status_filtro': status,
        'query': query
    })

@login_required
def produto_acabado_create(request):
    """Criar novo produto acabado"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PA'
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Produto acabado "{produto.codigo} - {produto.nome}" criado com sucesso.')
            return redirect('producao:produto_acabado_list') 
        else:
            messages.error(request, 'Erro ao criar produto acabado. Verifique os dados informados.')
    else:
        form = ProdutoForm()
    
    return render(request, 'producao/produto_acabado_form.html', {'form': form})

@login_required
def produto_acabado_update(request, pk):
    """Editar produto acabado"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PA')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PA'
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Produto acabado "{produto.codigo} - {produto.nome}" atualizado com sucesso.')
            return redirect('producao:produto_acabado_list') 
        else:
            messages.error(request, 'Erro ao atualizar produto acabado. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'producao/produto_acabado_form.html', {
        'form': form, 
        'produto': produto
    })

@login_required
def produto_acabado_toggle_status(request, pk):
    """Ativar/desativar produto acabado"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PA')
    
    if produto.status == 'ATIVO':
        produto.status = 'INATIVO'
        status_text = "desativado"
    else:
        produto.status = 'ATIVO'
        status_text = "ativado"
    
    produto.atualizado_por = request.user
    produto.save()
    messages.success(request, f'Produto acabado "{produto.nome}" {status_text} com sucesso.')
    
    return redirect('producao:produto_acabado_list')

@login_required
def produto_acabado_delete(request, pk):
    """Excluir produto acabado"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PA')
    
    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, f'Produto acabado "{produto.codigo} - {produto.nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir produto acabado: {str(e)}')
        
        return redirect('producao:produto_acabado_list')
    
    return render(request, 'producao/produto_acabado_delete.html', {'produto': produto})

# =============================================================================
# GESTÃO DE FORNECEDORES DO PRODUTO
# =============================================================================

@login_required
def produto_fornecedores(request, pk):
    """Gerenciar fornecedores de um produto"""
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        formset = FornecedorProdutoFormSet(request.POST, instance=produto)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.criado_por_id:
                    instance.criado_por = request.user
                instance.save()
            formset.save_m2m()
            messages.success(request, 'Fornecedores atualizados com sucesso.')
            return redirect('producao:fornecedor_list') 
    else:
        formset = FornecedorProdutoFormSet(instance=produto)
    
    return render(request, 'producao/produto_fornecedores.html', {
        'produto': produto,
        'formset': formset
    })

@login_required
def fornecedor_produto_toggle(request, pk):
    """Ativar/desativar relação fornecedor-produto"""
    fornecedor_produto = get_object_or_404(FornecedorProduto, pk=pk)
    fornecedor_produto.ativo = not fornecedor_produto.ativo
    fornecedor_produto.save()
    
    status_text = "ativado" if fornecedor_produto.ativo else "desativado"
    messages.success(request, f'Fornecedor {status_text} para este produto.')
    
    return redirect('producao:fornecedor_list') 

# =============================================================================
# APIs AJAX
# =============================================================================

@login_required
@require_GET
def get_subgrupos_by_grupo(request):
    """
    API endpoint para retornar subgrupos de um grupo específico
    Used by AJAX in forms when grupo is selected
    """
    grupo_id = request.GET.get('grupo_id')
    
    if not grupo_id:
        return JsonResponse({'error': 'grupo_id é obrigatório'}, status=400)
    
    try:
        grupo = GrupoProduto.objects.get(id=grupo_id, ativo=True)
        subgrupos = SubgrupoProduto.objects.filter(
            grupo=grupo, 
            ativo=True
        ).order_by('codigo')
        
        subgrupos_data = [
            {
                'id': subgrupo.id,
                'codigo': subgrupo.codigo,
                'nome': subgrupo.nome,
                'codigo_completo': f"{grupo.codigo}.{subgrupo.codigo}",
                'ultimo_numero': subgrupo.ultimo_numero
            }
            for subgrupo in subgrupos
        ]
        
        return JsonResponse({
            'success': True,
            'grupo': {
                'id': grupo.id,
                'codigo': grupo.codigo,
                'nome': grupo.nome,
                'tipo_produto': grupo.tipo_produto,
                'tipo_produto_display': grupo.get_tipo_produto_display()
            },
            'subgrupos': subgrupos_data
        })
        
    except GrupoProduto.DoesNotExist:
        return JsonResponse({'error': 'Grupo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_info_produto_codigo(request):
    """
    API endpoint para preview do código que será gerado para um produto
    """
    grupo_id = request.GET.get('grupo_id')
    subgrupo_id = request.GET.get('subgrupo_id')
    
    if not grupo_id or not subgrupo_id:
        return JsonResponse({'error': 'grupo_id e subgrupo_id são obrigatórios'}, status=400)
    
    try:
        grupo = GrupoProduto.objects.get(id=grupo_id, ativo=True)
        subgrupo = SubgrupoProduto.objects.get(id=subgrupo_id, grupo=grupo, ativo=True)
        
        # Preview do próximo código que seria gerado
        proximo_numero = subgrupo.ultimo_numero + 1
        codigo_preview = f"{grupo.codigo}.{subgrupo.codigo}.{proximo_numero:04d}"
        
        return JsonResponse({
            'success': True,
            'grupo': {
                'codigo': grupo.codigo,
                'nome': grupo.nome,
                'tipo_produto': grupo.tipo_produto,
                'tipo_produto_display': grupo.get_tipo_produto_display()
            },
            'subgrupo': {
                'codigo': subgrupo.codigo,
                'nome': subgrupo.nome,
                'ultimo_numero': subgrupo.ultimo_numero
            },
            'codigo_preview': codigo_preview,
            'proximo_numero': proximo_numero
        })
        
    except (GrupoProduto.DoesNotExist, SubgrupoProduto.DoesNotExist):
        return JsonResponse({'error': 'Grupo ou subgrupo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =============================================================================
# RELATÓRIOS ESPECÍFICOS DA PRODUÇÃO
# =============================================================================

@login_required
def relatorio_estoque_baixo(request):
    """Relatório de produtos com estoque baixo"""
    produtos_estoque_baixo = Produto.objects.filter(
        controla_estoque=True,
        estoque_atual__lte=models.F('estoque_minimo'),
        status='ATIVO'
    ).select_related('grupo', 'subgrupo').order_by('codigo')
    
    context = {
        'produtos': produtos_estoque_baixo,
        'total': produtos_estoque_baixo.count()
    }
    
    return render(request, 'producao/relatorio_estoque_baixo.html', context)

@login_required
def relatorio_produtos_sem_fornecedor(request):
    """Relatório de produtos sem fornecedor principal"""
    produtos_sem_fornecedor = Produto.objects.filter(
        fornecedor_principal__isnull=True,
        status='ATIVO'
    ).select_related('grupo', 'subgrupo').order_by('codigo')
    
    context = {
        'produtos': produtos_sem_fornecedor,
        'total': produtos_sem_fornecedor.count()
    }
    
    return render(request, 'producao/relatorio_produtos_sem_fornecedor.html', context)

@login_required
def relatorio_producao(request):
    """Relatório específico da produção com estatísticas por tipo"""
    stats_producao = {
        'materias_primas': {
            'total': Produto.objects.filter(tipo='MP').count(),
            'ativas': Produto.objects.filter(tipo='MP', status='ATIVO').count(),
            'estoque_baixo': Produto.objects.filter(
                tipo='MP', 
                controla_estoque=True, 
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
        },
        'produtos_intermediarios': {
            'total': Produto.objects.filter(tipo='PI').count(),
            'ativas': Produto.objects.filter(tipo='PI', status='ATIVO').count(),
            'estoque_baixo': Produto.objects.filter(
                tipo='PI', 
                controla_estoque=True, 
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
        },
        'produtos_acabados': {
            'total': Produto.objects.filter(tipo='PA').count(),
            'ativas': Produto.objects.filter(tipo='PA', status='ATIVO').count(),
            'estoque_baixo': Produto.objects.filter(
                tipo='PA', 
                controla_estoque=True, 
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
        }
    }
    
    context = {
        'stats_producao': stats_producao,
        'total_fornecedores': Fornecedor.objects.filter(ativo=True).count(),
    }
    
    return render(request, 'producao/relatorio_producao.html', context)

# =============================================================================
# DASHBOARD COM ANALYTICS
# =============================================================================

@login_required
def dashboard_analytics(request):
    """Dashboard com analytics detalhados para produção"""
    # Estatísticas por tipo de produto
    stats_por_tipo = Produto.objects.values('tipo').annotate(
        total=Count('id'),
        ativos=Count('id', filter=Q(status='ATIVO')),
        inativos=Count('id', filter=Q(status='INATIVO'))
    ).order_by('tipo')
    
    # Produtos com maior giro (mais caros)
    produtos_importantes = Produto.objects.filter(
        preco_venda__isnull=False,
        status='ATIVO'
    ).order_by('-preco_venda')[:10]
    
    # Fornecedores com mais produtos
    fornecedores_principais = Fornecedor.objects.annotate(
        total_produtos=Count('produtos_fornecedor')
    ).filter(total_produtos__gt=0).order_by('-total_produtos')[:10]
    
    context = {
        'stats_por_tipo': stats_por_tipo,
        'produtos_importantes': produtos_importantes,
        'fornecedores_principais': fornecedores_principais,
    }
    
    return render(request, 'producao/dashboard_analytics.html', context)

# =============================================================================
# CRUD PEDIDOS DE COMPRA - VERSÃO CORRIGIDA
# =============================================================================
# producao/views.py - VIEWS PEDIDOS DE COMPRA COMPLETAS

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from core.models import (
    PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra, 
    Fornecedor, Produto
)
from core.forms import (
    PedidoCompraForm, ItemPedidoCompraFormSet, PedidoCompraFiltroForm,
    AlterarStatusPedidoForm
)

# =============================================================================
# CRUD PEDIDOS DE COMPRA - VERSÃO COMPLETA
# =============================================================================
# producao/views.py - VIEWS PEDIDOS DE COMPRA COMPLETAS

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from core.models import (
    PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra, 
    Fornecedor, Produto
)
from core.forms import (
    PedidoCompraForm, ItemPedidoCompraFormSet, PedidoCompraFiltroForm,
    AlterarStatusPedidoForm
)

# =============================================================================
# CRUD PEDIDOS DE COMPRA - VERSÃO COMPLETA
# =============================================================================

@login_required
def pedido_compra_list(request):
    """Lista de pedidos de compra com filtros"""
    pedidos_list = PedidoCompra.objects.select_related(
        'fornecedor', 'criado_por'
    ).prefetch_related('itens').order_by('-data_pedido')
    
    # Aplicar filtros
    form_filtros = PedidoCompraFiltroForm(request.GET)
    if form_filtros.is_valid():
        data = form_filtros.cleaned_data
        
        if data.get('fornecedor'):
            pedidos_list = pedidos_list.filter(fornecedor=data['fornecedor'])
        
        if data.get('status'):
            pedidos_list = pedidos_list.filter(status=data['status'])
        
        if data.get('prioridade'):
            pedidos_list = pedidos_list.filter(prioridade=data['prioridade'])
        
        if data.get('data_inicio'):
            pedidos_list = pedidos_list.filter(data_pedido__date__gte=data['data_inicio'])
        
        if data.get('data_fim'):
            pedidos_list = pedidos_list.filter(data_pedido__date__lte=data['data_fim'])
        
        if data.get('q'):
            query = data['q']
            pedidos_list = pedidos_list.filter(
                Q(numero__icontains=query) | 
                Q(fornecedor__razao_social__icontains=query) |
                Q(fornecedor__nome_fantasia__icontains=query) |
                Q(observacoes__icontains=query)
            )
    
    # Paginação
    paginator = Paginator(pedidos_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        pedidos = paginator.page(page)
    except:
        pedidos = paginator.page(1)
    
    context = {
        'pedidos': pedidos,
        'form_filtros': form_filtros,
        'total_pedidos': pedidos_list.count(),
    }
    
    return render(request, 'producao/pedido_compra_list.html', context)


@login_required
def pedido_compra_create(request):
    """Criar novo pedido de compra - VERSÃO CORRIGIDA"""
    
    if request.method == 'POST':
        form = PedidoCompraForm(request.POST)
        formset = ItemPedidoCompraFormSet(request.POST)
        
        print("=== DEBUG PEDIDO COMPRA CREATE ===")
        print(f"Form válido: {form.is_valid()}")
        print(f"Formset válido: {formset.is_valid()}")
        
        if not form.is_valid():
            print("ERROS DO FORM:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        
        if not formset.is_valid():
            print("ERROS DO FORMSET:")
            print(f"  Non form errors: {formset.non_form_errors}")
            for i, form_item in enumerate(formset):
                if form_item.errors:
                    print(f"  Erro no item {i}: {form_item.errors}")
        
        # Verificar se há pelo menos um item válido
        itens_validos = 0
        for form_item in formset:
            if form_item.is_valid() and not form_item.cleaned_data.get('DELETE', False):
                # Verificar se os campos obrigatórios estão preenchidos
                if (form_item.cleaned_data.get('produto') and 
                    form_item.cleaned_data.get('quantidade') and 
                    form_item.cleaned_data.get('valor_unitario')):
                    itens_validos += 1
        
        print(f"Itens válidos encontrados: {itens_validos}")
        
        if form.is_valid() and formset.is_valid() and itens_validos > 0:
            try:
                with transaction.atomic():
                    # Criar pedido
                    pedido = form.save(commit=False)
                    pedido.criado_por = request.user
                    pedido.atualizado_por = request.user
                    
                    # Salvar pedido sem calcular valores ainda
                    pedido.valor_total = 0
                    pedido.valor_final = 0
                    pedido.save()
                    
                    print(f"Pedido criado com ID: {pedido.pk}")
                    
                    # Salvar itens
                    itens_salvos = 0
                    for form_item in formset:
                        if (form_item.is_valid() and 
                            not form_item.cleaned_data.get('DELETE', False) and
                            form_item.cleaned_data.get('produto')):
                            
                            item = form_item.save(commit=False)
                            item.pedido = pedido
                            
                            # Garantir que tem unidade
                            if not item.unidade:
                                item.unidade = item.produto.unidade_medida
                            
                            # Calcular valor total do item
                            item.valor_total = item.quantidade * item.valor_unitario
                            item.save()
                            itens_salvos += 1
                            
                            print(f"Item salvo: {item.produto.codigo} - Qtd: {item.quantidade} - Valor: {item.valor_unitario}")
                    
                    print(f"Total de itens salvos: {itens_salvos}")
                    
                    # Recalcular valores do pedido
                    pedido.recalcular_valores()
                    
                    # Registrar no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=request.user,
                        acao='Pedido criado',
                        observacao=f'Pedido criado com {itens_salvos} itens'
                    )
                    
                    messages.success(request, f'Pedido {pedido.numero} criado com sucesso!')
                    return redirect('producao:pedido_compra_detail', pk=pedido.pk)
                    
            except Exception as e:
                print(f"ERRO AO SALVAR: {str(e)}")
                messages.error(request, f'Erro ao criar pedido: {str(e)}')
        else:
            if itens_validos == 0:
                messages.error(request, 'Adicione pelo menos um item válido ao pedido.')
            else:
                messages.error(request, 'Erro ao criar pedido. Verifique os dados informados.')
    else:
        form = PedidoCompraForm()
        formset = ItemPedidoCompraFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Novo Pedido de Compra'
    }
    
    return render(request, 'producao/pedido_compra_form.html', context)


@login_required
def pedido_compra_detail(request, pk):
    """Detalhes do pedido de compra"""
    pedido = get_object_or_404(
        PedidoCompra.objects.select_related('fornecedor', 'criado_por')
        .prefetch_related('itens__produto', 'historico__usuario'),
        pk=pk
    )
    
    context = {
        'pedido': pedido,
        'pode_editar': pedido.pode_editar,
        'pode_cancelar': pedido.pode_cancelar,
    }
    
    return render(request, 'producao/pedido_compra_detail.html', context)


@login_required
def pedido_compra_update(request, pk):
    """Editar pedido de compra"""
    pedido = get_object_or_404(PedidoCompra, pk=pk)
    
    if not pedido.pode_editar:
        messages.error(request, f'Pedido {pedido.numero} não pode ser editado no status atual.')
        return redirect('producao:pedido_compra_detail', pk=pk)
    
    if request.method == 'POST':
        form = PedidoCompraForm(request.POST, instance=pedido)
        formset = ItemPedidoCompraFormSet(request.POST, instance=pedido)
        
        print("=== DEBUG PEDIDO UPDATE ===")
        print(f"Form válido: {form.is_valid()}")
        print(f"Formset válido: {formset.is_valid()}")
        
        # Verificar itens válidos
        itens_validos = 0
        for form_item in formset:
            if form_item.is_valid() and not form_item.cleaned_data.get('DELETE', False):
                if (form_item.cleaned_data.get('produto') and 
                    form_item.cleaned_data.get('quantidade') and 
                    form_item.cleaned_data.get('valor_unitario')):
                    itens_validos += 1
        
        if form.is_valid() and formset.is_valid() and itens_validos > 0:
            try:
                with transaction.atomic():
                    # Salvar pedido
                    pedido = form.save(commit=False)
                    pedido.atualizado_por = request.user
                    pedido.save()
                    
                    # Salvar itens
                    formset.save()
                    
                    # Recalcular valores
                    pedido.recalcular_valores()
                    
                    # Registrar no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=request.user,
                        acao='Pedido atualizado',
                        observacao='Dados do pedido foram alterados'
                    )
                    
                    messages.success(request, f'Pedido {pedido.numero} atualizado com sucesso!')
                    return redirect('producao:pedido_compra_detail', pk=pedido.pk)
                    
            except Exception as e:
                print(f"ERRO AO ATUALIZAR: {str(e)}")
                messages.error(request, f'Erro ao atualizar pedido: {str(e)}')
        else:
            if itens_validos == 0:
                messages.error(request, 'Adicione pelo menos um item válido ao pedido.')
            else:
                messages.error(request, 'Erro ao atualizar pedido. Verifique os dados informados.')
    else:
        form = PedidoCompraForm(instance=pedido)
        formset = ItemPedidoCompraFormSet(instance=pedido)
    
    context = {
        'form': form,
        'formset': formset,
        'pedido': pedido,
        'title': f'Editar Pedido {pedido.numero}'
    }
    
    return render(request, 'producao/pedido_compra_form.html', context)


@login_required
def pedido_compra_delete(request, pk):
    """Excluir pedido de compra"""
    pedido = get_object_or_404(PedidoCompra, pk=pk)
    
    # Verificar se pode ser excluído
    if pedido.status not in ['RASCUNHO', 'ENVIADO']:
        messages.error(request, f'Pedido {pedido.numero} não pode ser excluído no status atual: {pedido.get_status_display()}.')
        return redirect('producao:pedido_compra_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            numero = pedido.numero
            with transaction.atomic():
                # Excluir pedido (cascata exclui itens e histórico)
                pedido.delete()
                
            messages.success(request, f'Pedido {numero} excluído com sucesso!')
            return redirect('producao:pedido_compra_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir pedido: {str(e)}')
            return redirect('producao:pedido_compra_detail', pk=pk)
    
    return render(request, 'producao/pedido_compra_delete.html', {'pedido': pedido})


@login_required
def pedido_compra_alterar_status(request, pk):
    """Alterar status do pedido"""
    pedido = get_object_or_404(PedidoCompra, pk=pk)
    
    if request.method == 'POST':
        form = AlterarStatusPedidoForm(request.POST, instance=pedido)
        form._user = request.user  # Passar usuário para o form
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Status do pedido alterado para "{pedido.get_status_display()}".')
            return redirect('producao:pedido_compra_detail', pk=pk)
    else:
        form = AlterarStatusPedidoForm(instance=pedido)
    
    context = {
        'form': form,
        'pedido': pedido
    }
    
    return render(request, 'producao/pedido_compra_alterar_status.html', context)


@login_required
def pedido_compra_gerar_pdf(request, pk):
    """Gerar PDF do pedido de compra"""
    pedido = get_object_or_404(
        PedidoCompra.objects.select_related('fornecedor')
        .prefetch_related('itens__produto'),
        pk=pk
    )
    
    try:
        # Importar o gerador de PDF
        from core.utils.pdf_generator import gerar_pdf_pedido_compra
        
        # Gerar PDF
        pdf_buffer = gerar_pdf_pedido_compra(pedido)
        
        # Registrar no histórico
        HistoricoPedidoCompra.objects.create(
            pedido=pedido,
            usuario=request.user,
            acao='PDF gerado',
            observacao='PDF do pedido foi gerado e baixado'
        )
        
        # Preparar resposta
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Pedido_Compra_{pedido.numero}.pdf"'
        
        # Fechar buffer
        pdf_buffer.close()
        
        return response
        
    except ImportError as e:
        messages.error(request, f'Erro: Módulo reportlab não encontrado. Instale com: pip install reportlab')
        return redirect('producao:pedido_compra_detail', pk=pk)
    except AttributeError as e:
        if 'desconto_valor' in str(e):
            messages.error(request, 'Erro: Propriedade desconto_valor não encontrada no modelo PedidoCompra. Verifique o modelo.')
        else:
            messages.error(request, f'Erro de atributo: {str(e)}')
        return redirect('producao:pedido_compra_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('producao:pedido_compra_detail', pk=pk)

@login_required
def pedido_compra_duplicar(request, pk):
    """Duplicar pedido de compra"""
    pedido_original = get_object_or_404(PedidoCompra, pk=pk)
    
    try:
        with transaction.atomic():
            # Criar novo pedido
            novo_pedido = PedidoCompra(
                fornecedor=pedido_original.fornecedor,
                prioridade=pedido_original.prioridade,
                condicao_pagamento=pedido_original.condicao_pagamento,
                prazo_entrega=pedido_original.prazo_entrega,
                desconto_percentual=pedido_original.desconto_percentual,
                valor_frete=pedido_original.valor_frete,
                observacoes=pedido_original.observacoes,
                observacoes_internas=f"Duplicado do pedido {pedido_original.numero}",
                criado_por=request.user,
                atualizado_por=request.user
            )
            novo_pedido.save()
            
            # Copiar itens
            for item_original in pedido_original.itens.all():
                ItemPedidoCompra.objects.create(
                    pedido=novo_pedido,
                    produto=item_original.produto,
                    quantidade=item_original.quantidade,
                    valor_unitario=item_original.valor_unitario,
                    observacoes=item_original.observacoes
                )
            
            # Recalcular valores
            novo_pedido.recalcular_valores()
            
            # Registrar no histórico
            HistoricoPedidoCompra.objects.create(
                pedido=novo_pedido,
                usuario=request.user,
                acao='Pedido duplicado',
                observacao=f'Duplicado a partir do pedido {pedido_original.numero}'
            )
            
            messages.success(request, f'Pedido duplicado com sucesso! Novo número: {novo_pedido.numero}')
            return redirect('producao:pedido_compra_detail', pk=novo_pedido.pk)
            
    except Exception as e:
        messages.error(request, f'Erro ao duplicar pedido: {str(e)}')
        return redirect('producao:pedido_compra_detail', pk=pk)


# =============================================================================
# RECEBIMENTO DE MATERIAIS
# =============================================================================

@login_required
def pedido_compra_recebimento(request, pk):
    """Tela de recebimento de materiais"""
    pedido = get_object_or_404(
        PedidoCompra.objects.select_related('fornecedor')
        .prefetch_related('itens__produto'),
        pk=pk
    )
    
    if pedido.status not in ['CONFIRMADO', 'PARCIAL']:
        messages.error(request, 'Pedido deve estar confirmado para recebimento.')
        return redirect('producao:pedido_compra_detail', pk=pk)
    
    context = {
        'pedido': pedido,
        'itens_pendentes': pedido.itens.filter(quantidade_recebida__lt=models.F('quantidade')),
    }
    
    return render(request, 'producao/pedido_compra_recebimento.html', context)


@login_required
@require_POST
def receber_item_pedido(request, pedido_pk, item_pk):
    """Receber item específico do pedido"""
    pedido = get_object_or_404(PedidoCompra, pk=pedido_pk)
    item = get_object_or_404(ItemPedidoCompra, pk=item_pk, pedido=pedido)
    
    try:
        data = json.loads(request.body)
        quantidade_recebida = float(data.get('quantidade', 0))
        
        if quantidade_recebida <= 0:
            return JsonResponse({'success': False, 'error': 'Quantidade deve ser maior que zero'})
        
        quantidade_pendente = item.quantidade - item.quantidade_recebida
        if quantidade_recebida > quantidade_pendente:
            return JsonResponse({
                'success': False, 
                'error': f'Quantidade não pode ser maior que {quantidade_pendente}'
            })
        
        with transaction.atomic():
            # Atualizar item
            item.quantidade_recebida += quantidade_recebida
            item.data_recebimento = timezone.now()
            item.save()
            
            # Atualizar estoque do produto se controla estoque
            if item.produto.controla_estoque:
                item.produto.estoque_atual += quantidade_recebida
                item.produto.save()
            
            # Verificar se pedido está totalmente recebido
            itens_pendentes = pedido.itens.filter(quantidade_recebida__lt=models.F('quantidade'))
            
            if not itens_pendentes.exists():
                # Todos os itens foram recebidos
                pedido.status = 'RECEBIDO'
                pedido.data_entrega_real = timezone.now().date()
            elif pedido.status == 'CONFIRMADO':
                # Primeiro recebimento parcial
                pedido.status = 'PARCIAL'
            
            pedido.atualizado_por = request.user
            pedido.save()
            
            # Registrar no histórico
            HistoricoPedidoCompra.objects.create(
                pedido=pedido,
                usuario=request.user,
                acao='Item recebido',
                observacao=f'Recebido {quantidade_recebida} {item.unidade} do produto {item.produto.codigo}'
            )
        
        return JsonResponse({
            'success': True,
            'item_status': 'COMPLETO' if item.quantidade_recebida >= item.quantidade else 'PARCIAL',
            'pedido_status': pedido.status,
            'quantidade_recebida': float(item.quantidade_recebida),
            'quantidade_pendente': float(item.quantidade - item.quantidade_recebida)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# APIs AJAX
# =============================================================================

@login_required
def api_produto_info(request):
    """API para buscar informações do produto"""
    produto_id = request.GET.get('produto_id')
    fornecedor_id = request.GET.get('fornecedor_id')
    
    if not produto_id:
        return JsonResponse({'error': 'produto_id é obrigatório'}, status=400)
    
    try:
        produto = Produto.objects.get(id=produto_id)
        
        # Dados básicos do produto
        data = {
            'codigo': produto.codigo,
            'nome': produto.nome,
            'unidade': produto.unidade_medida,
            'estoque_atual': float(produto.estoque_atual) if produto.estoque_atual else 0,
            'estoque_minimo': float(produto.estoque_minimo) if produto.estoque_minimo else 0,
            'custo_medio': float(produto.custo_medio) if produto.custo_medio else None,
        }
        
        # Buscar preço do fornecedor se especificado
        if fornecedor_id:
            from core.models import FornecedorProduto
            fornecedor_produto = FornecedorProduto.objects.filter(
                produto=produto,
                fornecedor_id=fornecedor_id,
                ativo=True
            ).first()
            
            if fornecedor_produto:
                data['preco_fornecedor'] = float(fornecedor_produto.preco_unitario) if fornecedor_produto.preco_unitario else None
                data['prazo_entrega'] = fornecedor_produto.prazo_entrega
                data['quantidade_minima'] = float(fornecedor_produto.quantidade_minima) if fornecedor_produto.quantidade_minima else 1
        
        return JsonResponse({'success': True, 'produto': data})
        
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_fornecedor_produtos(request, fornecedor_id):
    """API para buscar produtos de um fornecedor"""
    try:
        fornecedor = Fornecedor.objects.get(id=fornecedor_id, ativo=True)
        
        produtos = Produto.objects.filter(
            fornecedores_produto__fornecedor=fornecedor,
            fornecedores_produto__ativo=True,
            status='ATIVO',
            disponivel=True
        ).select_related('grupo', 'subgrupo').order_by('codigo')
        
        produtos_data = []
        for produto in produtos:
            fornecedor_produto = produto.fornecedores_produto.filter(
                fornecedor=fornecedor,
                ativo=True
            ).first()
            
            produtos_data.append({
                'id': produto.id,
                'codigo': produto.codigo,
                'nome': produto.nome,
                'unidade': produto.unidade_medida,
                'preco': float(fornecedor_produto.preco_unitario) if fornecedor_produto and fornecedor_produto.preco_unitario else None,
                'estoque_atual': float(produto.estoque_atual) if produto.estoque_atual else 0,
                'estoque_minimo': float(produto.estoque_minimo) if produto.estoque_minimo else 0,
            })
        
        return JsonResponse({
            'success': True,
            'fornecedor': {
                'id': fornecedor.id,
                'nome': fornecedor.nome_fantasia or fornecedor.razao_social
            },
            'produtos': produtos_data
        })
        
    except Fornecedor.DoesNotExist:
        return JsonResponse({'error': 'Fornecedor não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)