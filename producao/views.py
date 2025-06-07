# producao/views.py

import logging
from datetime import datetime, timedelta
from django.db import models
from django.urls import reverse
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_GET

from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    FornecedorProduto, SimulacaoElevador
)
from core.forms import (
    ProdutoForm, GrupoProdutoForm, SubgrupoProdutoForm, 
    FornecedorForm, FornecedorProdutoFormSet
)

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

# Atualização da view grupo_list em producao/views.py

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