# gestor/views.py

import logging
from datetime import datetime, timedelta
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count

from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    EspecificacaoElevador, OpcaoEspecificacao, RegraComponente,
    ComponenteDerivado, SimulacaoElevador
)
from core.forms import (
    UsuarioForm, ProdutoForm, GrupoProdutoForm, SubgrupoProdutoForm, 
    FornecedorForm, EspecificacaoElevadorForm, OpcaoEspecificacaoForm,
    RegraComponenteForm, ComponenteDerivadoForm
)

logger = logging.getLogger(__name__)

# =============================================================================
# PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial do Portal do Gestor"""
    return render(request, 'gestor/home.html')

@login_required
def dashboard(request):
    """Dashboard do gestor com estatísticas"""
    context = {
        'total_usuarios': Usuario.objects.count(),
        'total_produtos': Produto.objects.count(),
        'total_fornecedores': Fornecedor.objects.filter(ativo=True).count(),
        'total_simulacoes': SimulacaoElevador.objects.count(),
        'produtos_sem_estoque': Produto.objects.filter(
            controla_estoque=True, 
            estoque_atual__lte=models.F('estoque_minimo')
        ).count() if Produto.objects.exists() else 0,
    }
    return render(request, 'gestor/dashboard.html', context)

# =============================================================================
# CRUD USUÁRIOS
# =============================================================================

@login_required
def usuario_list(request):
    usuarios_list = Usuario.objects.all().order_by('username')
    
    # Filtros
    nivel = request.GET.get('nivel')
    if nivel:
        usuarios_list = usuarios_list.filter(nivel=nivel)
    
    status = request.GET.get('status')
    if status == 'ativo':
        usuarios_list = usuarios_list.filter(is_active=True)
    elif status == 'inativo':
        usuarios_list = usuarios_list.filter(is_active=False)
    
    query = request.GET.get('q')
    if query:
        usuarios_list = usuarios_list.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(usuarios_list, 10)
    page = request.GET.get('page', 1)
    
    try:
        usuarios = paginator.page(page)
    except PageNotAnInteger:
        usuarios = paginator.page(1)
    except EmptyPage:
        usuarios = paginator.page(paginator.num_pages)
    
    return render(request, 'gestor/usuario_list.html', {
        'usuarios': usuarios,
        'nivel_filtro': nivel,
        'status_filtro': status,
        'query': query
    })

@login_required
def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso.')
            return redirect('gestor:usuario_list')
    else:
        form = UsuarioForm()
    return render(request, 'gestor/usuario_form.html', {'form': form})

@login_required
def usuario_update(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso.')
            return redirect('gestor:usuario_list')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'gestor/usuario_form.html', {'form': form, 'usuario': usuario})

@login_required
def usuario_toggle_status(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    status_text = "ativado" if usuario.is_active else "desativado"
    messages.success(request, f'Usuário {usuario.username} {status_text} com sucesso.')
    
    return redirect('gestor:usuario_list')

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
    
    query = request.GET.get('q')
    if query:
        grupos_list = grupos_list.filter(
            Q(codigo__icontains=query) | 
            Q(nome__icontains=query)
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
    
    return render(request, 'gestor/grupo_list.html', {
        'grupos': grupos,
        'status_filtro': status,
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
            return redirect('gestor:grupo_list')
    else:
        form = GrupoProdutoForm()
    return render(request, 'gestor/grupo_form.html', {'form': form})

@login_required
def grupo_update(request, pk):
    grupo = get_object_or_404(GrupoProduto, pk=pk)
    if request.method == 'POST':
        form = GrupoProdutoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupo "{grupo.nome}" atualizado com sucesso.')
            return redirect('gestor:grupo_list')
    else:
        form = GrupoProdutoForm(instance=grupo)
    return render(request, 'gestor/grupo_form.html', {'form': form, 'grupo': grupo})

@login_required
def grupo_toggle_status(request, pk):
    grupo = get_object_or_404(GrupoProduto, pk=pk)
    grupo.ativo = not grupo.ativo
    grupo.save()
    
    status_text = "ativado" if grupo.ativo else "desativado"
    messages.success(request, f'Grupo "{grupo.nome}" {status_text} com sucesso.')
    
    return redirect('gestor:grupo_list')

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
    
    return render(request, 'gestor/subgrupo_list.html', {
        'subgrupos': subgrupos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
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
            return redirect('gestor:subgrupo_list')
    else:
        # Se veio com grupo pré-selecionado
        grupo_id = request.GET.get('grupo')
        initial = {}
        if grupo_id:
            initial['grupo'] = grupo_id
        form = SubgrupoProdutoForm(initial=initial)
    
    return render(request, 'gestor/subgrupo_form.html', {'form': form})

@login_required
def subgrupo_update(request, pk):
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)
    if request.method == 'POST':
        form = SubgrupoProdutoForm(request.POST, instance=subgrupo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subgrupo "{subgrupo.nome}" atualizado com sucesso.')
            return redirect('gestor:subgrupo_list')
    else:
        form = SubgrupoProdutoForm(instance=subgrupo)
    return render(request, 'gestor/subgrupo_form.html', {'form': form, 'subgrupo': subgrupo})

@login_required
def subgrupo_toggle_status(request, pk):
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)
    subgrupo.ativo = not subgrupo.ativo
    subgrupo.save()
    
    status_text = "ativado" if subgrupo.ativo else "desativado"
    messages.success(request, f'Subgrupo "{subgrupo.nome}" {status_text} com sucesso.')
    
    return redirect('gestor:subgrupo_list')

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
    
    return render(request, 'gestor/fornecedor_list.html', {
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
            return redirect('gestor:fornecedor_list')
    else:
        form = FornecedorForm()
    return render(request, 'gestor/fornecedor_form.html', {'form': form})

@login_required
def fornecedor_update(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fornecedor "{fornecedor.razao_social}" atualizado com sucesso.')
            return redirect('gestor:fornecedor_list')
    else:
        form = FornecedorForm(instance=fornecedor)
    return render(request, 'gestor/fornecedor_form.html', {'form': form, 'fornecedor': fornecedor})

@login_required
def fornecedor_detail(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    # Produtos deste fornecedor
    produtos = Produto.objects.filter(fornecedor_principal=fornecedor).order_by('codigo')
    
    context = {
        'fornecedor': fornecedor,
        'produtos': produtos,
        'total_produtos': produtos.count()
    }
    return render(request, 'gestor/fornecedor_detail.html', context)

@login_required
def fornecedor_toggle_status(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    fornecedor.ativo = not fornecedor.ativo
    fornecedor.save()
    
    status_text = "ativado" if fornecedor.ativo else "desativado"
    messages.success(request, f'Fornecedor "{fornecedor.razao_social}" {status_text} com sucesso.')
    
    return redirect('gestor:fornecedor_list')

# =============================================================================
# CRUD PRODUTOS
# =============================================================================

@login_required
def produto_list(request):
    produtos_list = Produto.objects.select_related('grupo', 'subgrupo', 'fornecedor_principal').order_by('codigo')
    
    # Filtros
    tipo = request.GET.get('tipo')
    if tipo:
        produtos_list = produtos_list.filter(tipo=tipo)
    
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
    
    # Para os filtros
    grupos = GrupoProduto.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'gestor/produto_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'tipo_filtro': tipo,
        'grupo_filtro': grupo_id,
        'status_filtro': status,
        'query': query
    })

@login_required
def produto_create(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.save()
            messages.success(request, f'Produto "{produto.nome}" criado com sucesso.')
            return redirect('gestor:produto_detail', pk=produto.pk)
    else:
        form = ProdutoForm()
    return render(request, 'gestor/produto_form.html', {'form': form})

@login_required
def produto_update(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.atualizado_por = request.user
            produto.save()
            messages.success(request, f'Produto "{produto.nome}" atualizado com sucesso.')
            return redirect('gestor:produto_detail', pk=produto.pk)
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'gestor/produto_form.html', {'form': form, 'produto': produto})

@login_required
def produto_detail(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    # Componentes que usam este produto
    usado_em = produto.usado_em.select_related('produto_pai').all()
    
    # Componentes deste produto (se for PI ou PA)
    if produto.tipo in ['PI', 'PA']:
        componentes = produto.componentes.select_related('produto_filho').all()
    else:
        componentes = []
    
    # Derivados deste produto
    derivados = produto.derivados.select_related('componente_destino').all()
    
    context = {
        'produto': produto,
        'usado_em': usado_em,
        'componentes': componentes,
        'derivados': derivados,
        'disponibilidade_info': produto.disponibilidade_info
    }
    return render(request, 'gestor/produto_detail.html', context)

@login_required
def produto_toggle_status(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if produto.status == 'ATIVO':
        produto.status = 'INATIVO'
        status_text = "desativado"
    else:
        produto.status = 'ATIVO'
        status_text = "ativado"
    
    produto.save()
    messages.success(request, f'Produto "{produto.nome}" {status_text} com sucesso.')
    
    return redirect('gestor:produto_list')

@login_required
def produto_toggle_disponibilidade(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    produto.disponivel = not produto.disponivel
    produto.save()
    
    status_text = "disponibilizado" if produto.disponivel else "indisponibilizado"
    messages.success(request, f'Produto "{produto.nome}" {status_text} com sucesso.')
    
    return redirect('gestor:produto_detail', pk=pk)

# =============================================================================
# APIs AJAX
# =============================================================================

@login_required
def api_subgrupos_por_grupo(request, grupo_id):
    """API para buscar subgrupos por grupo"""
    subgrupos = SubgrupoProduto.objects.filter(grupo_id=grupo_id, ativo=True).order_by('nome')
    
    data = [
        {
            'id': subgrupo.id,
            'codigo': subgrupo.codigo,
            'nome': subgrupo.nome
        }
        for subgrupo in subgrupos
    ]
    
    return JsonResponse({'subgrupos': data})

@login_required
def api_produto_por_codigo(request, codigo):
    """API para buscar produto por código"""
    produto = Produto.objects.filter(codigo=codigo).first()
    
    if produto:
        return JsonResponse({
            'success': True,
            'id': str(produto.id),
            'nome': produto.nome,
            'tipo': produto.tipo,
            'disponivel': produto.disponivel,
            'estoque_atual': float(produto.estoque_atual),
            'preco_venda': float(produto.preco_venda) if produto.preco_venda else None
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Produto não encontrado'
        })