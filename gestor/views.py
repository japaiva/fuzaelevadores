# gestor/views.py

import logging
from datetime import datetime, timedelta
from django.db import models
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count
from django.db.models.deletion import ProtectedError

from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    EspecificacaoElevador, OpcaoEspecificacao, RegraComponente,
    ComponenteDerivado, SimulacaoElevador, Cliente, ParametrosGerais,
    SequenciaProduto
)
from core.forms import (
    UsuarioForm, ProdutoForm, GrupoProdutoForm, SubgrupoProdutoForm, 
    FornecedorForm, EspecificacaoElevadorForm, OpcaoEspecificacaoForm,
    RegraComponenteForm, ComponenteDerivadoForm, ClienteForm,
    ParametrosGeraisForm
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
def usuario_delete(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        try:
            usuario.delete()
            messages.success(request, 'Usuário excluído com sucesso.')
            return redirect('gestor:usuario_list')
        except ProtectedError:
            messages.error(request, 'Este usuário está vinculado a outros dados e não pode ser excluído.')
            return redirect('gestor:usuario_list')

    return render(request, 'gestor/usuario_delete.html', {'usuario': usuario})

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
def grupo_delete(request, pk):
    grupo = get_object_or_404(GrupoProduto, pk=pk)

    if request.method == 'POST':
        try:
            grupo.delete()
            messages.success(request, 'Grupo excluído com sucesso.')
            return redirect('gestor:grupo_list')
        except ProtectedError:
            messages.error(request, 'Este grupo não pode ser excluído pois possui subgrupos ou produtos vinculados.')
            return redirect('gestor:grupo_list')

    return render(request, 'gestor/grupo_delete.html', {'grupo': grupo})

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
def subgrupo_delete(request, pk):
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)

    if request.method == 'POST':
        try:
            subgrupo.delete()
            messages.success(request, 'Subgrupo excluído com sucesso.')
            return redirect('gestor:subgrupo_list')
        except ProtectedError:
            messages.error(request, 'Este subgrupo não pode ser excluído pois possui produtos vinculados.')
            return redirect('gestor:subgrupo_list')

    return render(request, 'gestor/subgrupo_delete.html', {'subgrupo': subgrupo})

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
            return redirect('gestor:fornecedor_list')  # ← MUDANÇA: vai para lista
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
            return redirect('gestor:fornecedor_list')  # ← MUDANÇA: vai para lista
    else:
        form = FornecedorForm(instance=fornecedor)
    return render(request, 'gestor/fornecedor_form.html', {'form': form, 'fornecedor': fornecedor})

@login_required
def fornecedor_delete(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        fornecedor.delete()
        messages.success(request, 'Fornecedor excluído com sucesso.')
        return redirect('gestor:fornecedor_list')

    return render(request, 'gestor/fornecedor_delete.html', {'fornecedor': fornecedor})

# TEMPORARIAMENTE DESABILITADO
# @login_required
# def fornecedor_detail(request, pk):
#     fornecedor = get_object_or_404(Fornecedor, pk=pk)
#     
#     # Produtos deste fornecedor
#     produtos = Produto.objects.filter(fornecedor_principal=fornecedor).order_by('codigo')
#     
#     context = {
#         'fornecedor': fornecedor,
#         'produtos': produtos,
#         'total_produtos': produtos.count()
#     }
#     return render(request, 'gestor/fornecedor_detail.html', context)

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
            #return redirect('gestor:produto_detail', pk=produto.pk)
            return redirect('gestor:produto_list') 
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
            #return redirect('gestor:produto_detail', pk=produto.pk)
            return redirect('gestor:produto_list') 
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'gestor/produto_form.html', {'form': form, 'produto': produto})

#@login_required
#def produto_detail(request, pk):
#    produto = get_object_or_404(Produto, pk=pk)
#    
#    # Componentes que usam este produto
#    usado_em = produto.usado_em.select_related('produto_pai').all()
#    
#    # Componentes deste produto (se for PI ou PA)
#    if produto.tipo in ['PI', 'PA']:
#        componentes = produto.componentes.select_related('produto_filho').all()
#    else:
#        componentes = []
#    
#    # Derivados deste produto
#    derivados = produto.derivados.select_related('componente_destino').all()
#    
#    context = {
#        'produto': produto,
#        'usado_em': usado_em,
#       'componentes': componentes,
#       'derivados': derivados,
#        'disponibilidade_info': produto.disponibilidade_info
#    }
#    return render(request, 'gestor/produto_detail.html', context)

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
    
    #return redirect('gestor:produto_detail', pk=pk)
    return redirect('gestor:produto_list') 

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
    
# Adicione estes imports no topo do seu gestor/views.py:

from core.models import FornecedorProduto
from core.forms import FornecedorProdutoFormSet

# Adicione estas views ao final do seu gestor/views.py:

@login_required
def produto_fornecedores(request, pk):
    """Gerenciar fornecedores de um produto"""
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        formset = FornecedorProdutoFormSet(request.POST, instance=produto)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.criado_por_id:  # Só define se for novo
                    instance.criado_por = request.user
                instance.save()
            formset.save_m2m()
            messages.success(request, 'Fornecedores atualizados com sucesso.')
            #return redirect('gestor:produto_detail', pk=produto.pk)
            return redirect('gestor:produto_list') 
    else:
        formset = FornecedorProdutoFormSet(instance=produto)
    
    return render(request, 'gestor/produto_fornecedores.html', {
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
    
    #return redirect('gestor:produto_detail', pk=fornecedor_produto.produto.pk)
    return redirect('gestor:produto_list') 

# =============================================================================
# CRUD CLIENTES
# =============================================================================

@login_required
def cliente_list(request):
    clientes_list = Cliente.objects.all().order_by('nome')
    
    # Filtros
    tipo = request.GET.get('tipo')
    if tipo:
        clientes_list = clientes_list.filter(tipo_pessoa=tipo)
    
    status = request.GET.get('status')
    if status == 'ativo':
        clientes_list = clientes_list.filter(ativo=True)
    elif status == 'inativo':
        clientes_list = clientes_list.filter(ativo=False)
    
    query = request.GET.get('q')
    if query:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=query) | 
            Q(nome_fantasia__icontains=query) |
            Q(cpf_cnpj__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(clientes_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    return render(request, 'gestor/cliente_list.html', {
        'clientes': clientes,
        'tipo_filtro': tipo,
        'status_filtro': status,
        'query': query
    })

@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.criado_por = request.user
            cliente.atualizado_por = request.user
            cliente.save()
            messages.success(request, f'Cliente "{cliente.nome}" criado com sucesso.')
            #return redirect('gestor:cliente_detail', pk=cliente.id)
            return redirect('gestor:cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'gestor/cliente_form.html', {'form': form})

@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.atualizado_por = request.user
            cliente.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso.')
            #return redirect('gestor:cliente_detail', pk=cliente.id)
            return redirect('gestor:cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'gestor/cliente_form.html', {'form': form, 'cliente': cliente})


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente excluído com sucesso.')
        return redirect('gestor:cliente_list')

    return render(request, 'gestor/cliente_delete.html', {'cliente': cliente})


# @login_required
# def cliente_detail(request, pk):
#     cliente = get_object_or_404(Cliente, pk=pk)
#     return render(request, 'gestor/cliente_detail.html', {'cliente': cliente})

@login_required
def cliente_toggle_status(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.ativo = not cliente.ativo
    cliente.atualizado_por = request.user
    cliente.save()
    
    status_text = "ativado" if cliente.ativo else "desativado"
    messages.success(request, f'Cliente "{cliente.nome}" {status_text} com sucesso.')
    
    return redirect('gestor:cliente_list')


# Substitua as views de matéria-prima no gestor/views.py

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
    
    return render(request, 'gestor/materiaprima_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'status_filtro': status,
        'query': query
    })

@login_required
def materiaprima_create(request):
    """Criar nova matéria-prima"""
    if request.method == 'POST':
        # Debug
        print("Dados POST recebidos:", request.POST)
        
        form = ProdutoForm(request.POST)
        
        # Forçar tipo como MP
        form.instance.tipo = 'MP'
        
        if form.is_valid():
            print("Form é válido")
            produto = form.save(commit=False)
            produto.tipo = 'MP'  # Garantir que seja MP
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            
            # Gerar código se não fornecido
            if not produto.codigo:
                produto.gerar_codigo_automatico()
            
            produto.save()
            messages.success(request, f'Matéria-prima "{produto.nome}" criada com sucesso.')
            return redirect('gestor:materiaprima_list') 
        else:
            print("Erros do form:", form.errors)
            messages.error(request, 'Erro ao criar matéria-prima. Verifique os dados informados.')
    else:
        # Inicializar com tipo MP
        form = ProdutoForm(initial={'tipo': 'MP'})
    
    return render(request, 'gestor/materiaprima_form.html', {'form': form})

@login_required
def materiaprima_update(request, pk):
    """Editar matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if request.method == 'POST':
        # Debug
        print("Dados POST recebidos:", request.POST)
        
        form = ProdutoForm(request.POST, instance=produto)
        
        if form.is_valid():
            print("Form é válido")
            produto = form.save(commit=False)
            produto.tipo = 'MP'  # Garantir que continue sendo MP
            produto.atualizado_por = request.user
            produto.save()
            messages.success(request, f'Matéria-prima "{produto.nome}" atualizada com sucesso.')
            return redirect('gestor:materiaprima_list') 
        else:
            print("Erros do form:", form.errors)
            messages.error(request, 'Erro ao atualizar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'gestor/materiaprima_form.html', {
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
    
    return redirect('gestor:materiaprima_list')

@login_required
def materiaprima_delete(request, pk):
    """Excluir matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if request.method == 'POST':
        nome_produto = produto.nome
        codigo_produto = produto.codigo
        
        try:
            # Verificar se pode ser excluído (não está sendo usado)
            usado_em = produto.usado_em.count()
            if usado_em > 0:
                messages.error(request, 
                    f'Não é possível excluir a matéria-prima "{nome_produto}" pois ela está sendo usada em {usado_em} produto(s).')
                return redirect('gestor:materiaprima_list')
            
            # Verificar fornecedores
            fornecedores = produto.fornecedores_produto.count()
            if fornecedores > 0:
                # Remover relacionamentos com fornecedores primeiro
                produto.fornecedores_produto.all().delete()
            
            produto.delete()
            messages.success(request, 
                f'Matéria-prima "{codigo_produto} - {nome_produto}" excluída com sucesso.')
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir matéria-prima: {str(e)}')
        
        return redirect('gestor:materiaprima_list')
    
    # GET - Mostrar confirmação
    context = {
        'produto': produto,
        'usado_em_count': produto.usado_em.count(),
        'fornecedores_count': produto.fornecedores_produto.count()
    }
    return render(request, 'gestor/materiaprima_delete.html', context)

# =============================================================================
# CRUD PRODUTOS INTERMEDIÁRIOS (TIPO = PI) - Para implementar depois
# =============================================================================

@login_required
def produto_intermediario_list(request):
    """Lista apenas produtos do tipo Produto Intermediário (PI)"""
    # TODO: Implementar quando necessário
    pass

@login_required
def produto_intermediario_create(request):
    """Criar novo produto intermediário"""
    # TODO: Implementar quando necessário
    pass

@login_required
def produto_intermediario_update(request, pk):
    """Editar produto intermediário"""
    # TODO: Implementar quando necessário
    pass

# =============================================================================
# CRUD PRODUTOS ACABADOS (TIPO = PA) - Para implementar depois
# =============================================================================

@login_required
def produto_acabado_list(request):
    """Lista apenas produtos do tipo Produto Acabado (PA)"""
    # TODO: Implementar quando necessário
    pass

@login_required
def produto_acabado_create(request):
    """Criar novo produto acabado"""
    # TODO: Implementar quando necessário
    pass

@login_required
def produto_acabado_update(request, pk):
    """Editar produto acabado"""
    # TODO: Implementar quando necessário
    pass



# =============================================================================
# PARÂMETROS GERAIS
# =============================================================================


def parametros_gerais_view(request):
    parametros, _ = ParametrosGerais.objects.get_or_create(id=1)  # <- Garante existência
    if request.method == 'POST':
        form = ParametrosGeraisForm(request.POST, instance=parametros)
        if form.is_valid():
            instancia = form.save(commit=False)
            instancia.atualizado_por = request.user
            instancia.save()
            return redirect('gestor:parametros_gerais')
    else:
        form = ParametrosGeraisForm(instance=parametros)
    return render(request, 'gestor/parametros_gerais.html', {'form': form})


# =============================================================================
# API PARA CÓDIGO AUTOMÁTICO
# =============================================================================

@login_required
def api_proximo_codigo(request, tipo):
    """
    API para obter o próximo código para um tipo de produto
    """
    if request.user.nivel not in ['admin', 'gestor']:
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        # Só gera o código, não incrementa ainda (isso acontece no save)
        sequencia, created = SequenciaProduto.objects.get_or_create(
            tipo=tipo,
            defaults={
                'prefixo': tipo,
                'proximo_numero': 1,
                'numero_digitos': 4
            }
        )
        
        numero_formatado = str(sequencia.proximo_numero).zfill(sequencia.numero_digitos)
        codigo_previsto = f"{sequencia.prefixo}{numero_formatado}"
        
        return JsonResponse({
            'codigo': codigo_previsto,
            'tipo': tipo,
            'prefixo': sequencia.prefixo,
            'numero': sequencia.proximo_numero
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =============================================================================
# API PARA VALIDAR CÓDIGO ÚNICO
# =============================================================================

@login_required  
def api_validar_codigo(request, codigo):
    """
    API para validar se um código já existe
    """
    exists = Produto.objects.filter(codigo=codigo).exists()
    
    return JsonResponse({
        'exists': exists,
        'valid': not exists,
        'message': 'Código já existe' if exists else 'Código disponível'
    })

# =============================================================================
# RELATÓRIOS E ESTATÍSTICAS
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
    
    return render(request, 'gestor/relatorio_estoque_baixo.html', context)

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
    
    return render(request, 'gestor/relatorio_produtos_sem_fornecedor.html', context)

# =============================================================================
# CONFIGURAÇÕES DO SISTEMA
# =============================================================================

@login_required
def configurar_sequencias(request):
    """
    Tela para configurar as sequências de códigos
    """
    if request.user.nivel not in ['admin']:
        messages.error(request, 'Apenas administradores podem acessar esta página.')
        return redirect('gestor:dashboard')
    
    sequencias = SequenciaProduto.objects.all().order_by('tipo')
    
    if request.method == 'POST':
        # Processar alterações nas sequências
        for sequencia in sequencias:
            proximo_numero = request.POST.get(f'proximo_numero_{sequencia.tipo}')
            prefixo = request.POST.get(f'prefixo_{sequencia.tipo}')
            numero_digitos = request.POST.get(f'numero_digitos_{sequencia.tipo}')
            
            if proximo_numero and prefixo and numero_digitos:
                sequencia.proximo_numero = int(proximo_numero)
                sequencia.prefixo = prefixo
                sequencia.numero_digitos = int(numero_digitos)
                sequencia.save()
        
        messages.success(request, 'Sequências atualizadas com sucesso!')
        return redirect('gestor:configurar_sequencias')
    
    context = {
        'sequencias': sequencias,
    }
    
    return render(request, 'gestor/configurar_sequencias.html', context)

# =============================================================================
# DASHBOARD COM GRÁFICOS (OPCIONAL)
# =============================================================================

@login_required
def dashboard_analytics(request):
    """
    Dashboard com analytics mais detalhados
    """
    # Estatísticas por tipo de produto
    stats_por_tipo = Produto.objects.values('tipo').annotate(
        total=Count('id'),
        ativos=Count('id', filter=Q(status='ATIVO')),
        inativos=Count('id', filter=Q(status='INATIVO'))
    ).order_by('tipo')
    
    # Produtos mais caros
    produtos_caros = Produto.objects.filter(
        preco_venda__isnull=False,
        status='ATIVO'
    ).order_by('-preco_venda')[:10]
    
    # Fornecedores com mais produtos
    fornecedores_top = Fornecedor.objects.annotate(
        total_produtos=Count('produtos_fornecedor')
    ).filter(total_produtos__gt=0).order_by('-total_produtos')[:10]
    
    context = {
        'stats_por_tipo': stats_por_tipo,
        'produtos_caros': produtos_caros,
        'fornecedores_top': fornecedores_top,
    }
    
    return render(request, 'gestor/dashboard_analytics.html', context)