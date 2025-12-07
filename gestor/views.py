# gestor/views.py

import logging
from datetime import datetime, timedelta
from django.db import models
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import (
    portal_gestor, modulo_cadastros, modulo_estoque, modulo_estoque_movimento,
    modulo_ordem_producao, modulo_usuarios, modulo_parametros
)
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count
from django.db.models.deletion import ProtectedError

from django.forms import inlineformset_factory
from django.utils import timezone

from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    Cliente, ParametrosGerais,
    LocalEstoque, TipoMovimentoEntrada, TipoMovimentoSaida,
    MovimentoEntrada, ItemMovimentoEntrada,
    MovimentoSaida, ItemMovimentoSaida,
    Estoque, MovimentoEstoque,
    # FASE 4 - Ordens de Producao
    OrdemProducao, ItemConsumoOP
)
from core.forms import (
    UsuarioForm, ProdutoForm, GrupoProdutoForm, SubgrupoProdutoForm,
    FornecedorForm, ClienteForm, ParametrosGeraisForm,
    LocalEstoqueForm, LocalEstoqueFiltroForm,
    TipoMovimentoEntradaForm, TipoMovimentoEntradaFiltroForm,
    TipoMovimentoSaidaForm, TipoMovimentoSaidaFiltroForm,
    MovimentoEntradaForm, ItemMovimentoEntradaForm, MovimentoEntradaFiltroForm,
    MovimentoSaidaForm, ItemMovimentoSaidaForm, MovimentoSaidaFiltroForm,
    # FASE 4 - Ordens de Producao
    OrdemProducaoForm, OrdemProducaoFiltroForm, ApontamentoProducaoForm
)

logger = logging.getLogger(__name__)

# =============================================================================
# PÁGINAS PRINCIPAIS
# =============================================================================

@portal_gestor
def home(request):
    """Página inicial do Portal do Gestor - redireciona direto para painel de projetos"""
    return redirect('gestor:painel_projetos')

@portal_gestor
def dashboard(request):
    """Dashboard do gestor com estatísticas"""
    context = {
        'total_usuarios': Usuario.objects.count(),
        'total_produtos': Produto.objects.count(),
        'total_fornecedores': Fornecedor.objects.filter(ativo=True).count(),
        'produtos_sem_estoque': Produto.objects.filter(
            controla_estoque=True, 
            estoque_atual__lte=models.F('estoque_minimo')
        ).count() if Produto.objects.exists() else 0,
    }
    return render(request, 'gestor/dashboard.html', context)

# =============================================================================
# CRUD USUÁRIOS (apenas admin)
# =============================================================================

@modulo_usuarios
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

@modulo_usuarios
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

@modulo_usuarios
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

@modulo_usuarios
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

@modulo_usuarios
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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



@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
def fornecedor_toggle_status(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    fornecedor.ativo = not fornecedor.ativo
    fornecedor.save()
    
    status_text = "ativado" if fornecedor.ativo else "desativado"
    messages.success(request, f'Fornecedor "{fornecedor.razao_social}" {status_text} com sucesso.')
    
    return redirect('gestor:fornecedor_list')

# =============================================================================
# APIs AJAX
# =============================================================================

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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

@modulo_cadastros
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


@modulo_cadastros
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

@modulo_cadastros
def cliente_toggle_status(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.ativo = not cliente.ativo
    cliente.atualizado_por = request.user
    cliente.save()
    
    status_text = "ativado" if cliente.ativo else "desativado"
    messages.success(request, f'Cliente "{cliente.nome}" {status_text} com sucesso.')
    
    return redirect('gestor:cliente_list')

# =============================================================================
# CRUD MATÉRIAS-PRIMAS (TIPO = PI) 
# =============================================================================

@modulo_estoque
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

@modulo_estoque
def materiaprima_create(request):
    """Criar nova matéria-prima - SIMPLIFICADO"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'MP'  # Forçar tipo MP
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            # O código será gerado automaticamente no save()
            produto.save()
            
            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" criada com sucesso.')
            return redirect('gestor:materiaprima_list') 
        else:
            messages.error(request, 'Erro ao criar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm()
    
    return render(request, 'gestor/materiaprima_form.html', {'form': form})

@modulo_estoque
def materiaprima_update(request, pk):
    """Editar matéria-prima - SIMPLIFICADO"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'MP'  # Garantir que continue sendo MP
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" atualizada com sucesso.')
            return redirect('gestor:materiaprima_list') 
        else:
            messages.error(request, 'Erro ao atualizar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'gestor/materiaprima_form.html', {
        'form': form, 
        'produto': produto
    })

@modulo_estoque
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

@modulo_estoque
def materiaprima_delete(request, pk):
    """Excluir matéria-prima - SIMPLIFICADO igual ao fornecedor"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    
    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" excluída com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir matéria-prima: {str(e)}')
        
        return redirect('gestor:materiaprima_list')
    
    return render(request, 'gestor/materiaprima_delete.html', {'produto': produto})

# =============================================================================
# CRUD PRODUTOS INTERMEDIÁRIOS (TIPO = PI)
# =============================================================================

@modulo_estoque
def produto_intermediario_list(request):
    """Lista apenas produtos do tipo Produto Intermediário (PI)"""
    produtos_list = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='PI').order_by('codigo')

    # Filtros
    grupo_id = request.GET.get('grupo')
    if grupo_id:
        produtos_list = produtos_list.filter(grupo_id=grupo_id)

    tipo_pi = request.GET.get('tipo_pi')
    if tipo_pi:
        produtos_list = produtos_list.filter(tipo_pi=tipo_pi)

    status = request.GET.get('status')
    if status == 'ativo':
        produtos_list = produtos_list.filter(status='ATIVO')
    elif status == 'inativo':
        produtos_list = produtos_list.filter(status='INATIVO')

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
    grupos = GrupoProduto.objects.filter(ativo=True, tipo_produto='PI').order_by('nome')

    return render(request, 'gestor/produto_intermediario_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'tipo_pi_filtro': tipo_pi,
        'status_filtro': status,
        'query': query
    })


@modulo_estoque
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
            return redirect('gestor:produto_intermediario_list')
        else:
            messages.error(request, 'Erro ao criar produto intermediário. Verifique os dados informados.')
    else:
        form = ProdutoForm()

    return render(request, 'gestor/produto_intermediario_form.html', {'form': form})


@modulo_estoque
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
            return redirect('gestor:produto_intermediario_list')
        else:
            messages.error(request, 'Erro ao atualizar produto intermediário. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)

    return render(request, 'gestor/produto_intermediario_form.html', {
        'form': form,
        'produto': produto
    })


@modulo_estoque
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

    return redirect('gestor:produto_intermediario_list')


@modulo_estoque
def produto_intermediario_delete(request, pk):
    """Excluir produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI')

    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, f'Produto intermediário "{produto.codigo} - {produto.nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir produto intermediário: {str(e)}')

        return redirect('gestor:produto_intermediario_list')

    return render(request, 'gestor/produto_intermediario_delete.html', {'produto': produto})


# =============================================================================
# CRUD PRODUTOS ACABADOS (TIPO = PA)
# =============================================================================

@modulo_cadastros
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
    grupos = GrupoProduto.objects.filter(ativo=True, tipo_produto='PA').order_by('nome')

    return render(request, 'gestor/produto_acabado_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'status_filtro': status,
        'query': query
    })


@modulo_cadastros
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
            return redirect('gestor:produto_acabado_list')
        else:
            messages.error(request, 'Erro ao criar produto acabado. Verifique os dados informados.')
    else:
        form = ProdutoForm()

    return render(request, 'gestor/produto_acabado_form.html', {'form': form})


@modulo_cadastros
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
            return redirect('gestor:produto_acabado_list')
        else:
            messages.error(request, 'Erro ao atualizar produto acabado. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)

    return render(request, 'gestor/produto_acabado_form.html', {
        'form': form,
        'produto': produto
    })


@modulo_cadastros
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

    return redirect('gestor:produto_acabado_list')


@modulo_cadastros
def produto_acabado_delete(request, pk):
    """Excluir produto acabado"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PA')

    if request.method == 'POST':
        try:
            produto.delete()
            messages.success(request, f'Produto acabado "{produto.codigo} - {produto.nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir produto acabado: {str(e)}')

        return redirect('gestor:produto_acabado_list')

    return render(request, 'gestor/produto_acabado_delete.html', {'produto': produto})



# =============================================================================
# PARÂMETROS GERAIS
# =============================================================================


@modulo_parametros
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
# RELATÓRIOS E ESTATÍSTICAS
# =============================================================================

@portal_gestor
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

@portal_gestor
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
# DASHBOARD COM GRÁFICOS (OPCIONAL)
# =============================================================================

@portal_gestor
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


# =============================================================================
# PAINEL DE PROJETOS
# =============================================================================

@portal_gestor
def painel_projetos(request):
    """
    Painel de Projetos - Lista de propostas com filtros
    Filtros: Status Pedido, Status Financeiro, Status Produção, Status Obra, Busca
    """
    from core.models import Proposta

    propostas = Proposta.objects.select_related(
        'cliente',
        'vendedor'
    ).order_by('-data_aprovacao')

    # Filtro Status Pedido (padrão: aprovado)
    filtro_status = request.GET.get('status', 'aprovado')
    if filtro_status and filtro_status != 'todos':
        propostas = propostas.filter(status=filtro_status)

    # Filtro Status Financeiro
    filtro_status_financeiro = request.GET.get('status_financeiro', 'todos')
    if filtro_status_financeiro != 'todos':
        propostas = propostas.filter(status_financeiro=filtro_status_financeiro)

    # Filtro Status Produção
    filtro_status_producao = request.GET.get('status_producao', 'todos')
    if filtro_status_producao != 'todos':
        propostas = propostas.filter(status_producao=filtro_status_producao)

    # Filtro Status Obra
    filtro_status_obra = request.GET.get('status_obra', 'todos')
    if filtro_status_obra != 'todos':
        propostas = propostas.filter(status_obra=filtro_status_obra)

    # Busca
    query = request.GET.get('q', '')
    if query:
        propostas = propostas.filter(
            Q(numero__icontains=query) |
            Q(nome_projeto__icontains=query) |
            Q(cliente__nome__icontains=query) |
            Q(numero_op__icontains=query)
        )

    # Paginação
    paginator = Paginator(propostas, 25)
    page = request.GET.get('page', 1)

    try:
        propostas_page = paginator.page(page)
    except PageNotAnInteger:
        propostas_page = paginator.page(1)
    except EmptyPage:
        propostas_page = paginator.page(paginator.num_pages)

    context = {
        'propostas': propostas_page,
        'filtro_status': filtro_status,
        'filtro_status_financeiro': filtro_status_financeiro,
        'filtro_status_producao': filtro_status_producao,
        'filtro_status_obra': filtro_status_obra,
        'query': query,
        'status_choices': Proposta.STATUS_CHOICES,
        'status_financeiro_choices': Proposta.STATUS_FINANCEIRO_CHOICES,
        'status_producao_choices': Proposta.STATUS_PRODUCAO_CHOICES,
        'status_obra_choices': Proposta.STATUS_OBRA_CHOICES,
    }

    return render(request, 'gestor/painel_projetos.html', context)


@portal_gestor
def projeto_detail(request, pk):
    """
    Detalhe do Projeto - Mostra todas as informações, especificações e projetos
    """
    from core.models import Proposta

    proposta = get_object_or_404(
        Proposta.objects.select_related('cliente', 'vendedor').prefetch_related('portas_pavimento'),
        pk=pk
    )

    # Dados de dimensionamento (se existir)
    dimensionamento = proposta.dimensionamento_detalhado or {}

    context = {
        'proposta': proposta,
        'pedido': proposta,  # alias para compatibilidade com tabs
        'dimensionamento': dimensionamento,
    }

    return render(request, 'gestor/projeto_detail.html', context)


# =============================================================================
# LIBERAÇÃO PRODUÇÃO (FINANCEIRO)
# =============================================================================

@portal_gestor
def liberacao_producao(request):
    """
    Liberação Produção - Lista propostas aprovadas para alterar status financeiro
    Filtro fixo: status = aprovado
    Filtro: status_financeiro (Pendente, Liberado)
    Permite alterar status entre '' (pendente) e 'liberado'
    """
    from core.models import Proposta

    # Filtro fixo: apenas aprovados
    propostas = Proposta.objects.filter(
        status='aprovado'
    ).select_related(
        'cliente',
        'vendedor'
    ).order_by('-data_aprovacao')

    # Filtro por status_financeiro
    filtro_status = request.GET.get('status_financeiro', '')
    if filtro_status == 'pendente':
        propostas = propostas.filter(status_financeiro='')
    elif filtro_status == 'liberado':
        propostas = propostas.filter(status_financeiro='liberado')

    # Busca
    query = request.GET.get('q', '')
    if query:
        propostas = propostas.filter(
            Q(numero__icontains=query) |
            Q(nome_projeto__icontains=query) |
            Q(cliente__nome__icontains=query) |
            Q(numero_op__icontains=query)
        )

    # Paginação
    paginator = Paginator(propostas, 20)
    page = request.GET.get('page', 1)

    try:
        propostas_page = paginator.page(page)
    except PageNotAnInteger:
        propostas_page = paginator.page(1)
    except EmptyPage:
        propostas_page = paginator.page(paginator.num_pages)

    context = {
        'propostas': propostas_page,
        'filtro_status': filtro_status,
        'query': query,
    }

    return render(request, 'gestor/liberacao_producao.html', context)


@portal_gestor
def liberacao_producao_salvar(request, pk):
    """
    Alterar status financeiro de uma proposta (via AJAX)
    Status permitidos: '' (pendente) e 'liberado'
    Se liberado: salva OP e Data
    Se pendente: limpa OP e Data
    """
    from core.models import Proposta

    if request.method == 'POST':
        proposta = get_object_or_404(Proposta, pk=pk)

        novo_status = request.POST.get('status_financeiro', '').strip()

        # Validar status permitido (só aceita '' ou 'liberado' nesta tela)
        if novo_status not in ['', 'liberado']:
            return JsonResponse({
                'success': False,
                'message': 'Status não permitido nesta tela.'
            }, status=400)

        if novo_status == 'liberado':
            # Liberar - salvar OP e Data
            numero_op = request.POST.get('numero_op', '').strip()
            data_liberacao = request.POST.get('data_liberacao_producao', '').strip()

            proposta.status_financeiro = 'liberado'
            proposta.numero_op = numero_op if numero_op else None

            if data_liberacao:
                try:
                    proposta.data_liberacao_producao = datetime.strptime(data_liberacao, '%Y-%m-%d').date()
                except ValueError:
                    proposta.data_liberacao_producao = None
            else:
                proposta.data_liberacao_producao = None

            proposta.save()
            return JsonResponse({
                'success': True,
                'message': f'Projeto {proposta.numero} liberado com sucesso.',
                'status': 'liberado'
            })
        else:
            # Voltar para pendente - limpar OP e Data
            proposta.status_financeiro = ''
            proposta.numero_op = None
            proposta.data_liberacao_producao = None
            proposta.save()
            return JsonResponse({
                'success': True,
                'message': f'Projeto {proposta.numero} voltou para pendente.',
                'status': ''
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)


# =============================================================================
# SISTEMA SIMPLIFICADO - Permissões removidas
# =============================================================================
# As views de gerenciamento de permissões foram removidas.
# O sistema agora usa apenas níveis (hardcoded) para controle de acesso.
# Veja docs/SISTEMA_SIMPLIFICADO.md para mais detalhes.


# =============================================================================
# CRUD LOCAL DE ESTOQUE
# =============================================================================

@modulo_cadastros
def local_estoque_list(request):
    """Lista locais de estoque"""
    locais_list = LocalEstoque.objects.all().select_related('fornecedor').order_by('tipo', 'nome')

    # Filtros
    tipo = request.GET.get('tipo')
    if tipo:
        locais_list = locais_list.filter(tipo=tipo)

    status = request.GET.get('ativo')
    if status == '1':
        locais_list = locais_list.filter(ativo=True)
    elif status == '0':
        locais_list = locais_list.filter(ativo=False)

    query = request.GET.get('q')
    if query:
        locais_list = locais_list.filter(
            Q(nome__icontains=query) |
            Q(fornecedor__razao_social__icontains=query) |
            Q(fornecedor__nome_fantasia__icontains=query)
        )

    # Paginação
    paginator = Paginator(locais_list, 15)
    page = request.GET.get('page', 1)

    try:
        locais = paginator.page(page)
    except PageNotAnInteger:
        locais = paginator.page(1)
    except EmptyPage:
        locais = paginator.page(paginator.num_pages)

    context = {
        'locais': locais,
        'filtro_form': LocalEstoqueFiltroForm(request.GET),
    }
    return render(request, 'gestor/estoque/local_estoque_list.html', context)


@modulo_cadastros
def local_estoque_create(request):
    """Criar novo local de estoque"""
    if request.method == 'POST':
        form = LocalEstoqueForm(request.POST)
        if form.is_valid():
            local = form.save(commit=False)
            local.criado_por = request.user
            local.save()
            messages.success(request, f'Local "{local.nome}" criado com sucesso.')
            return redirect('gestor:local_estoque_list')
    else:
        form = LocalEstoqueForm()

    return render(request, 'gestor/estoque/local_estoque_form.html', {'form': form})


@modulo_cadastros
def local_estoque_update(request, pk):
    """Editar local de estoque"""
    local = get_object_or_404(LocalEstoque, pk=pk)

    if request.method == 'POST':
        form = LocalEstoqueForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            messages.success(request, f'Local "{local.nome}" atualizado com sucesso.')
            return redirect('gestor:local_estoque_list')
    else:
        form = LocalEstoqueForm(instance=local)

    return render(request, 'gestor/estoque/local_estoque_form.html', {'form': form, 'local': local})


@modulo_cadastros
def local_estoque_delete(request, pk):
    """Excluir local de estoque"""
    local = get_object_or_404(LocalEstoque, pk=pk)

    if request.method == 'POST':
        try:
            nome = local.nome
            local.delete()
            messages.success(request, f'Local "{nome}" excluído com sucesso.')
            return redirect('gestor:local_estoque_list')
        except ProtectedError:
            messages.error(request, 'Este local está vinculado a movimentações e não pode ser excluído.')
            return redirect('gestor:local_estoque_list')

    return render(request, 'gestor/estoque/local_estoque_delete.html', {'local': local})


@modulo_cadastros
def local_estoque_toggle_status(request, pk):
    """Ativar/Desativar local de estoque"""
    local = get_object_or_404(LocalEstoque, pk=pk)
    local.ativo = not local.ativo
    local.save()

    status_text = "ativado" if local.ativo else "desativado"
    messages.success(request, f'Local "{local.nome}" {status_text} com sucesso.')

    return redirect('gestor:local_estoque_list')


# =============================================================================
# CRUD TIPO MOVIMENTO ENTRADA
# =============================================================================

@modulo_cadastros
def tipo_movimento_entrada_list(request):
    """Lista tipos de movimento de entrada"""
    tipos_list = TipoMovimentoEntrada.objects.all().order_by('codigo')

    # Filtros
    tipo_parceiro = request.GET.get('tipo_parceiro')
    if tipo_parceiro:
        tipos_list = tipos_list.filter(tipo_parceiro=tipo_parceiro)

    status = request.GET.get('ativo')
    if status == '1':
        tipos_list = tipos_list.filter(ativo=True)
    elif status == '0':
        tipos_list = tipos_list.filter(ativo=False)

    query = request.GET.get('q')
    if query:
        tipos_list = tipos_list.filter(
            Q(codigo__icontains=query) |
            Q(descricao__icontains=query)
        )

    # Paginação
    paginator = Paginator(tipos_list, 15)
    page = request.GET.get('page', 1)

    try:
        tipos = paginator.page(page)
    except PageNotAnInteger:
        tipos = paginator.page(1)
    except EmptyPage:
        tipos = paginator.page(paginator.num_pages)

    context = {
        'tipos': tipos,
        'filtro_form': TipoMovimentoEntradaFiltroForm(request.GET),
    }
    return render(request, 'gestor/estoque/tipo_movimento_entrada_list.html', context)


@modulo_cadastros
def tipo_movimento_entrada_create(request):
    """Criar novo tipo de movimento de entrada"""
    if request.method == 'POST':
        form = TipoMovimentoEntradaForm(request.POST)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.criado_por = request.user
            tipo.save()
            messages.success(request, f'Tipo "{tipo.descricao}" criado com sucesso.')
            return redirect('gestor:tipo_movimento_entrada_list')
    else:
        form = TipoMovimentoEntradaForm()

    return render(request, 'gestor/estoque/tipo_movimento_entrada_form.html', {'form': form})


@modulo_cadastros
def tipo_movimento_entrada_update(request, pk):
    """Editar tipo de movimento de entrada"""
    tipo = get_object_or_404(TipoMovimentoEntrada, pk=pk)

    if request.method == 'POST':
        form = TipoMovimentoEntradaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tipo "{tipo.descricao}" atualizado com sucesso.')
            return redirect('gestor:tipo_movimento_entrada_list')
    else:
        form = TipoMovimentoEntradaForm(instance=tipo)

    return render(request, 'gestor/estoque/tipo_movimento_entrada_form.html', {'form': form, 'tipo': tipo})


@modulo_cadastros
def tipo_movimento_entrada_delete(request, pk):
    """Excluir tipo de movimento de entrada"""
    tipo = get_object_or_404(TipoMovimentoEntrada, pk=pk)

    if request.method == 'POST':
        try:
            descricao = tipo.descricao
            tipo.delete()
            messages.success(request, f'Tipo "{descricao}" excluído com sucesso.')
            return redirect('gestor:tipo_movimento_entrada_list')
        except ProtectedError:
            messages.error(request, 'Este tipo está vinculado a movimentações e não pode ser excluído.')
            return redirect('gestor:tipo_movimento_entrada_list')

    return render(request, 'gestor/estoque/tipo_movimento_entrada_delete.html', {'tipo': tipo})


@modulo_cadastros
def tipo_movimento_entrada_toggle_status(request, pk):
    """Ativar/Desativar tipo de movimento de entrada"""
    tipo = get_object_or_404(TipoMovimentoEntrada, pk=pk)
    tipo.ativo = not tipo.ativo
    tipo.save()

    status_text = "ativado" if tipo.ativo else "desativado"
    messages.success(request, f'Tipo "{tipo.descricao}" {status_text} com sucesso.')

    return redirect('gestor:tipo_movimento_entrada_list')


# =============================================================================
# CRUD TIPO MOVIMENTO SAÍDA
# =============================================================================

@modulo_cadastros
def tipo_movimento_saida_list(request):
    """Lista tipos de movimento de saída"""
    tipos_list = TipoMovimentoSaida.objects.all().order_by('codigo')

    # Filtros
    tipo_parceiro = request.GET.get('tipo_parceiro')
    if tipo_parceiro:
        tipos_list = tipos_list.filter(tipo_parceiro=tipo_parceiro)

    status = request.GET.get('ativo')
    if status == '1':
        tipos_list = tipos_list.filter(ativo=True)
    elif status == '0':
        tipos_list = tipos_list.filter(ativo=False)

    query = request.GET.get('q')
    if query:
        tipos_list = tipos_list.filter(
            Q(codigo__icontains=query) |
            Q(descricao__icontains=query)
        )

    # Paginação
    paginator = Paginator(tipos_list, 15)
    page = request.GET.get('page', 1)

    try:
        tipos = paginator.page(page)
    except PageNotAnInteger:
        tipos = paginator.page(1)
    except EmptyPage:
        tipos = paginator.page(paginator.num_pages)

    context = {
        'tipos': tipos,
        'filtro_form': TipoMovimentoSaidaFiltroForm(request.GET),
    }
    return render(request, 'gestor/estoque/tipo_movimento_saida_list.html', context)


@modulo_cadastros
def tipo_movimento_saida_create(request):
    """Criar novo tipo de movimento de saída"""
    if request.method == 'POST':
        form = TipoMovimentoSaidaForm(request.POST)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.criado_por = request.user
            tipo.save()
            messages.success(request, f'Tipo "{tipo.descricao}" criado com sucesso.')
            return redirect('gestor:tipo_movimento_saida_list')
    else:
        form = TipoMovimentoSaidaForm()

    return render(request, 'gestor/estoque/tipo_movimento_saida_form.html', {'form': form})


@modulo_cadastros
def tipo_movimento_saida_update(request, pk):
    """Editar tipo de movimento de saída"""
    tipo = get_object_or_404(TipoMovimentoSaida, pk=pk)

    if request.method == 'POST':
        form = TipoMovimentoSaidaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tipo "{tipo.descricao}" atualizado com sucesso.')
            return redirect('gestor:tipo_movimento_saida_list')
    else:
        form = TipoMovimentoSaidaForm(instance=tipo)

    return render(request, 'gestor/estoque/tipo_movimento_saida_form.html', {'form': form, 'tipo': tipo})


@modulo_cadastros
def tipo_movimento_saida_delete(request, pk):
    """Excluir tipo de movimento de saída"""
    tipo = get_object_or_404(TipoMovimentoSaida, pk=pk)

    if request.method == 'POST':
        try:
            descricao = tipo.descricao
            tipo.delete()
            messages.success(request, f'Tipo "{descricao}" excluído com sucesso.')
            return redirect('gestor:tipo_movimento_saida_list')
        except ProtectedError:
            messages.error(request, 'Este tipo está vinculado a movimentações e não pode ser excluído.')
            return redirect('gestor:tipo_movimento_saida_list')

    return render(request, 'gestor/estoque/tipo_movimento_saida_delete.html', {'tipo': tipo})


@modulo_cadastros
def tipo_movimento_saida_toggle_status(request, pk):
    """Ativar/Desativar tipo de movimento de saída"""
    tipo = get_object_or_404(TipoMovimentoSaida, pk=pk)
    tipo.ativo = not tipo.ativo
    tipo.save()

    status_text = "ativado" if tipo.ativo else "desativado"
    messages.success(request, f'Tipo "{tipo.descricao}" {status_text} com sucesso.')

    return redirect('gestor:tipo_movimento_saida_list')


# =============================================================================
# MOVIMENTO DE ENTRADA
# =============================================================================

# FormSet para itens de entrada
ItemEntradaFormSet = inlineformset_factory(
    MovimentoEntrada,
    ItemMovimentoEntrada,
    form=ItemMovimentoEntradaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


@modulo_estoque_movimento
def movimento_entrada_list(request):
    """Lista movimentos de entrada"""
    movimentos_list = MovimentoEntrada.objects.select_related(
        'tipo_movimento', 'fornecedor', 'cliente', 'local_estoque', 'criado_por'
    ).order_by('-data_movimento', '-numero')

    # Filtros
    status = request.GET.get('status')
    if status:
        movimentos_list = movimentos_list.filter(status=status)

    tipo_movimento = request.GET.get('tipo_movimento')
    if tipo_movimento:
        movimentos_list = movimentos_list.filter(tipo_movimento_id=tipo_movimento)

    fornecedor = request.GET.get('fornecedor')
    if fornecedor:
        movimentos_list = movimentos_list.filter(fornecedor_id=fornecedor)

    data_de = request.GET.get('data_de')
    if data_de:
        movimentos_list = movimentos_list.filter(data_movimento__gte=data_de)

    data_ate = request.GET.get('data_ate')
    if data_ate:
        movimentos_list = movimentos_list.filter(data_movimento__lte=data_ate)

    query = request.GET.get('q')
    if query:
        movimentos_list = movimentos_list.filter(
            Q(numero__icontains=query) |
            Q(numero_nf__icontains=query) |
            Q(fornecedor__razao_social__icontains=query)
        )

    # Paginação
    paginator = Paginator(movimentos_list, 15)
    page = request.GET.get('page', 1)

    try:
        movimentos = paginator.page(page)
    except PageNotAnInteger:
        movimentos = paginator.page(1)
    except EmptyPage:
        movimentos = paginator.page(paginator.num_pages)

    context = {
        'movimentos': movimentos,
        'filtro_form': MovimentoEntradaFiltroForm(request.GET),
    }
    return render(request, 'gestor/estoque/movimento_entrada_list.html', context)


@modulo_estoque_movimento
def movimento_entrada_create(request):
    """Criar novo movimento de entrada"""
    if request.method == 'POST':
        form = MovimentoEntradaForm(request.POST)
        formset = ItemEntradaFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.criado_por = request.user
            movimento.save()

            # Salvar itens
            formset.instance = movimento
            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Entrada "{movimento.numero}" criada com sucesso.')
            return redirect('gestor:movimento_entrada_detail', pk=movimento.pk)
    else:
        form = MovimentoEntradaForm()
        formset = ItemEntradaFormSet(prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'tipos_movimento': TipoMovimentoEntrada.objects.filter(ativo=True).values('id', 'tipo_parceiro', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'gestor/estoque/movimento_entrada_form.html', context)


@modulo_estoque_movimento
def movimento_entrada_detail(request, pk):
    """Visualizar movimento de entrada"""
    movimento = get_object_or_404(
        MovimentoEntrada.objects.select_related(
            'tipo_movimento', 'fornecedor', 'cliente', 'local_estoque',
            'local_estoque_origem', 'pedido_compra', 'criado_por', 'confirmado_por'
        ).prefetch_related('itens__produto'),
        pk=pk
    )

    context = {
        'movimento': movimento,
        'itens': movimento.itens.all(),
    }
    return render(request, 'gestor/estoque/movimento_entrada_detail.html', context)


@modulo_estoque_movimento
def movimento_entrada_update(request, pk):
    """Editar movimento de entrada"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    # Só permite editar rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser editados.')
        return redirect('gestor:movimento_entrada_detail', pk=pk)

    if request.method == 'POST':
        form = MovimentoEntradaForm(request.POST, instance=movimento)
        formset = ItemEntradaFormSet(request.POST, instance=movimento, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.atualizado_por = request.user
            movimento.save()

            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Entrada "{movimento.numero}" atualizada com sucesso.')
            return redirect('gestor:movimento_entrada_detail', pk=movimento.pk)
    else:
        form = MovimentoEntradaForm(instance=movimento)
        formset = ItemEntradaFormSet(instance=movimento, prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'movimento': movimento,
        'tipos_movimento': TipoMovimentoEntrada.objects.filter(ativo=True).values('id', 'tipo_parceiro', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'gestor/estoque/movimento_entrada_form.html', context)


@modulo_estoque_movimento
def movimento_entrada_delete(request, pk):
    """Excluir movimento de entrada"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    # Só permite excluir rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser excluídos.')
        return redirect('gestor:movimento_entrada_detail', pk=pk)

    if request.method == 'POST':
        numero = movimento.numero
        movimento.delete()
        messages.success(request, f'Entrada "{numero}" excluída com sucesso.')
        return redirect('gestor:movimento_entrada_list')

    return render(request, 'gestor/estoque/movimento_entrada_delete.html', {'movimento': movimento})


@modulo_estoque_movimento
def movimento_entrada_confirmar(request, pk):
    """Confirmar movimento de entrada - atualiza estoque"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Este movimento já foi confirmado ou cancelado.')
        return redirect('gestor:movimento_entrada_detail', pk=pk)

    if not movimento.itens.exists():
        messages.error(request, 'Adicione pelo menos um item antes de confirmar.')
        return redirect('gestor:movimento_entrada_detail', pk=pk)

    # Processar cada item
    for item in movimento.itens.all():
        # Buscar ou criar posição de estoque
        estoque, created = Estoque.objects.get_or_create(
            produto=item.produto,
            local_estoque=movimento.local_estoque,
            defaults={'quantidade': 0, 'custo_medio': 0}
        )

        saldo_anterior = estoque.quantidade
        custo_medio_anterior = estoque.custo_medio

        # Calcular novo custo médio (média ponderada)
        if estoque.quantidade + item.quantidade > 0:
            valor_atual = estoque.quantidade * estoque.custo_medio
            valor_entrada = item.quantidade * item.valor_unitario
            novo_custo_medio = (valor_atual + valor_entrada) / (estoque.quantidade + item.quantidade)
        else:
            novo_custo_medio = item.valor_unitario

        # Atualizar estoque
        estoque.quantidade += item.quantidade
        estoque.custo_medio = novo_custo_medio
        estoque.ultima_entrada = movimento.data_movimento
        estoque.atualizar_valor_total()
        estoque.save()

        # Registrar histórico
        MovimentoEstoque.objects.create(
            produto=item.produto,
            local_estoque=movimento.local_estoque,
            tipo='entrada',
            quantidade=item.quantidade,
            saldo_anterior=saldo_anterior,
            saldo_posterior=estoque.quantidade,
            custo_unitario=item.valor_unitario,
            custo_medio_anterior=custo_medio_anterior,
            custo_medio_posterior=novo_custo_medio,
            documento_tipo='entrada',
            documento_numero=movimento.numero,
            documento_id=movimento.id,
            data_movimento=movimento.data_movimento,
            criado_por=request.user,
            observacoes=f'Entrada confirmada: {movimento.tipo_movimento.descricao}'
        )

        # Se movimenta terceiros (retorno beneficiamento), baixar do local de origem
        if movimento.tipo_movimento.movimenta_terceiros and movimento.local_estoque_origem:
            estoque_origem, _ = Estoque.objects.get_or_create(
                produto=item.produto,
                local_estoque=movimento.local_estoque_origem,
                defaults={'quantidade': 0, 'custo_medio': 0}
            )

            saldo_anterior_origem = estoque_origem.quantidade
            estoque_origem.quantidade -= item.quantidade
            estoque_origem.ultima_saida = movimento.data_movimento
            estoque_origem.atualizar_valor_total()
            estoque_origem.save()

            # Registrar histórico da baixa
            MovimentoEstoque.objects.create(
                produto=item.produto,
                local_estoque=movimento.local_estoque_origem,
                tipo='saida',
                quantidade=item.quantidade,
                saldo_anterior=saldo_anterior_origem,
                saldo_posterior=estoque_origem.quantidade,
                custo_unitario=estoque_origem.custo_medio,
                custo_medio_anterior=estoque_origem.custo_medio,
                custo_medio_posterior=estoque_origem.custo_medio,
                documento_tipo='entrada',
                documento_numero=movimento.numero,
                documento_id=movimento.id,
                data_movimento=movimento.data_movimento,
                criado_por=request.user,
                observacoes=f'Baixa terceiros - Retorno: {movimento.tipo_movimento.descricao}'
            )

    # Atualizar status do movimento
    movimento.status = 'confirmado'
    movimento.confirmado_em = timezone.now()
    movimento.confirmado_por = request.user
    movimento.save()

    messages.success(request, f'Entrada "{movimento.numero}" confirmada. Estoque atualizado.')
    return redirect('gestor:movimento_entrada_detail', pk=pk)


@modulo_estoque_movimento
def movimento_entrada_cancelar(request, pk):
    """Cancelar movimento de entrada"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser cancelados.')
        return redirect('gestor:movimento_entrada_detail', pk=pk)

    movimento.status = 'cancelado'
    movimento.save()

    messages.warning(request, f'Entrada "{movimento.numero}" foi cancelada.')
    return redirect('gestor:movimento_entrada_list')


# =============================================================================
# MOVIMENTO DE SAÍDA
# =============================================================================

# FormSet para itens de saída
ItemSaidaFormSet = inlineformset_factory(
    MovimentoSaida,
    ItemMovimentoSaida,
    form=ItemMovimentoSaidaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


@modulo_estoque_movimento
def movimento_saida_list(request):
    """Lista movimentos de saída"""
    movimentos_list = MovimentoSaida.objects.select_related(
        'tipo_movimento', 'fornecedor', 'cliente', 'local_estoque', 'criado_por'
    ).order_by('-data_movimento', '-numero')

    # Filtros
    status = request.GET.get('status')
    if status:
        movimentos_list = movimentos_list.filter(status=status)

    tipo_movimento = request.GET.get('tipo_movimento')
    if tipo_movimento:
        movimentos_list = movimentos_list.filter(tipo_movimento_id=tipo_movimento)

    cliente = request.GET.get('cliente')
    if cliente:
        movimentos_list = movimentos_list.filter(cliente_id=cliente)

    data_de = request.GET.get('data_de')
    if data_de:
        movimentos_list = movimentos_list.filter(data_movimento__gte=data_de)

    data_ate = request.GET.get('data_ate')
    if data_ate:
        movimentos_list = movimentos_list.filter(data_movimento__lte=data_ate)

    query = request.GET.get('q')
    if query:
        movimentos_list = movimentos_list.filter(
            Q(numero__icontains=query) |
            Q(numero_nf__icontains=query) |
            Q(cliente__razao_social__icontains=query)
        )

    # Paginação
    paginator = Paginator(movimentos_list, 15)
    page = request.GET.get('page', 1)

    try:
        movimentos = paginator.page(page)
    except PageNotAnInteger:
        movimentos = paginator.page(1)
    except EmptyPage:
        movimentos = paginator.page(paginator.num_pages)

    context = {
        'movimentos': movimentos,
        'filtro_form': MovimentoSaidaFiltroForm(request.GET),
    }
    return render(request, 'gestor/estoque/movimento_saida_list.html', context)


@modulo_estoque_movimento
def movimento_saida_create(request):
    """Criar novo movimento de saída"""
    if request.method == 'POST':
        form = MovimentoSaidaForm(request.POST)
        formset = ItemSaidaFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.criado_por = request.user
            movimento.save()

            # Salvar itens
            formset.instance = movimento
            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Saída "{movimento.numero}" criada com sucesso.')
            return redirect('gestor:movimento_saida_detail', pk=movimento.pk)
    else:
        form = MovimentoSaidaForm()
        formset = ItemSaidaFormSet(prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'tipos_movimento': TipoMovimentoSaida.objects.filter(ativo=True).values('id', 'tipo_parceiro', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'gestor/estoque/movimento_saida_form.html', context)


@modulo_estoque_movimento
def movimento_saida_detail(request, pk):
    """Visualizar movimento de saída"""
    movimento = get_object_or_404(
        MovimentoSaida.objects.select_related(
            'tipo_movimento', 'fornecedor', 'cliente', 'local_estoque',
            'local_estoque_destino', 'criado_por', 'confirmado_por'
        ).prefetch_related('itens__produto'),
        pk=pk
    )

    context = {
        'movimento': movimento,
        'itens': movimento.itens.all(),
    }
    return render(request, 'gestor/estoque/movimento_saida_detail.html', context)


@modulo_estoque_movimento
def movimento_saida_update(request, pk):
    """Editar movimento de saída"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    # Só permite editar rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser editados.')
        return redirect('gestor:movimento_saida_detail', pk=pk)

    if request.method == 'POST':
        form = MovimentoSaidaForm(request.POST, instance=movimento)
        formset = ItemSaidaFormSet(request.POST, instance=movimento, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.atualizado_por = request.user
            movimento.save()

            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Saída "{movimento.numero}" atualizada com sucesso.')
            return redirect('gestor:movimento_saida_detail', pk=movimento.pk)
    else:
        form = MovimentoSaidaForm(instance=movimento)
        formset = ItemSaidaFormSet(instance=movimento, prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'movimento': movimento,
        'tipos_movimento': TipoMovimentoSaida.objects.filter(ativo=True).values('id', 'tipo_parceiro', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'gestor/estoque/movimento_saida_form.html', context)


@modulo_estoque_movimento
def movimento_saida_delete(request, pk):
    """Excluir movimento de saída"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    # Só permite excluir rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser excluídos.')
        return redirect('gestor:movimento_saida_detail', pk=pk)

    if request.method == 'POST':
        numero = movimento.numero
        movimento.delete()
        messages.success(request, f'Saída "{numero}" excluída com sucesso.')
        return redirect('gestor:movimento_saida_list')

    return render(request, 'gestor/estoque/movimento_saida_delete.html', {'movimento': movimento})


@modulo_estoque_movimento
def movimento_saida_confirmar(request, pk):
    """Confirmar movimento de saída - atualiza estoque"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Este movimento já foi confirmado ou cancelado.')
        return redirect('gestor:movimento_saida_detail', pk=pk)

    if not movimento.itens.exists():
        messages.error(request, 'Adicione pelo menos um item antes de confirmar.')
        return redirect('gestor:movimento_saida_detail', pk=pk)

    # Verificar se há estoque suficiente
    erros_estoque = []
    for item in movimento.itens.all():
        try:
            estoque = Estoque.objects.get(
                produto=item.produto,
                local_estoque=movimento.local_estoque
            )
            if estoque.quantidade_disponivel < item.quantidade:
                erros_estoque.append(
                    f'{item.produto.codigo}: disponível {estoque.quantidade_disponivel}, solicitado {item.quantidade}'
                )
        except Estoque.DoesNotExist:
            erros_estoque.append(f'{item.produto.codigo}: sem estoque no local')

    if erros_estoque:
        messages.error(request, 'Estoque insuficiente: ' + '; '.join(erros_estoque))
        return redirect('gestor:movimento_saida_detail', pk=pk)

    # Processar cada item
    for item in movimento.itens.all():
        estoque = Estoque.objects.get(
            produto=item.produto,
            local_estoque=movimento.local_estoque
        )

        saldo_anterior = estoque.quantidade
        custo_medio_anterior = estoque.custo_medio

        # Atualizar estoque (saída não altera custo médio)
        estoque.quantidade -= item.quantidade
        estoque.ultima_saida = movimento.data_movimento
        estoque.atualizar_valor_total()
        estoque.save()

        # Usar custo médio como valor unitário se não informado
        valor_unitario = item.valor_unitario if item.valor_unitario else estoque.custo_medio

        # Registrar histórico
        MovimentoEstoque.objects.create(
            produto=item.produto,
            local_estoque=movimento.local_estoque,
            tipo='saida',
            quantidade=item.quantidade,
            saldo_anterior=saldo_anterior,
            saldo_posterior=estoque.quantidade,
            custo_unitario=valor_unitario,
            custo_medio_anterior=custo_medio_anterior,
            custo_medio_posterior=estoque.custo_medio,
            documento_tipo='saida',
            documento_numero=movimento.numero,
            documento_id=movimento.id,
            data_movimento=movimento.data_movimento,
            criado_por=request.user,
            observacoes=f'Saída confirmada: {movimento.tipo_movimento.descricao}'
        )

        # Se movimenta terceiros (remessa beneficiamento), adicionar no local de destino
        if movimento.tipo_movimento.movimenta_terceiros and movimento.local_estoque_destino:
            estoque_destino, _ = Estoque.objects.get_or_create(
                produto=item.produto,
                local_estoque=movimento.local_estoque_destino,
                defaults={'quantidade': 0, 'custo_medio': estoque.custo_medio}
            )

            saldo_anterior_destino = estoque_destino.quantidade
            estoque_destino.quantidade += item.quantidade
            estoque_destino.ultima_entrada = movimento.data_movimento
            estoque_destino.atualizar_valor_total()
            estoque_destino.save()

            # Registrar histórico da entrada em terceiros
            MovimentoEstoque.objects.create(
                produto=item.produto,
                local_estoque=movimento.local_estoque_destino,
                tipo='entrada',
                quantidade=item.quantidade,
                saldo_anterior=saldo_anterior_destino,
                saldo_posterior=estoque_destino.quantidade,
                custo_unitario=estoque.custo_medio,
                custo_medio_anterior=estoque_destino.custo_medio,
                custo_medio_posterior=estoque_destino.custo_medio,
                documento_tipo='saida',
                documento_numero=movimento.numero,
                documento_id=movimento.id,
                data_movimento=movimento.data_movimento,
                criado_por=request.user,
                observacoes=f'Entrada terceiros - Remessa: {movimento.tipo_movimento.descricao}'
            )

    # Atualizar status do movimento
    movimento.status = 'confirmado'
    movimento.confirmado_em = timezone.now()
    movimento.confirmado_por = request.user
    movimento.save()

    messages.success(request, f'Saída "{movimento.numero}" confirmada. Estoque atualizado.')
    return redirect('gestor:movimento_saida_detail', pk=pk)


@modulo_estoque_movimento
def movimento_saida_cancelar(request, pk):
    """Cancelar movimento de saída"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser cancelados.')
        return redirect('gestor:movimento_saida_detail', pk=pk)

    movimento.status = 'cancelado'
    movimento.save()

    messages.warning(request, f'Saída "{movimento.numero}" foi cancelada.')
    return redirect('gestor:movimento_saida_list')


# =============================================================================
# POSIÇÃO DE ESTOQUE (Consulta)
# =============================================================================

@modulo_estoque
def posicao_estoque(request):
    """Consulta posição de estoque"""
    estoques_list = Estoque.objects.select_related(
        'produto', 'local_estoque'
    ).filter(quantidade__gt=0).order_by('produto__codigo', 'local_estoque__nome')

    # Filtros
    local = request.GET.get('local')
    if local:
        estoques_list = estoques_list.filter(local_estoque_id=local)

    tipo_local = request.GET.get('tipo_local')
    if tipo_local:
        estoques_list = estoques_list.filter(local_estoque__tipo=tipo_local)

    query = request.GET.get('q')
    if query:
        estoques_list = estoques_list.filter(
            Q(produto__codigo__icontains=query) |
            Q(produto__descricao__icontains=query)
        )

    # Totais
    total_valor = estoques_list.aggregate(total=Sum('valor_total'))['total'] or 0

    # Paginação
    paginator = Paginator(estoques_list, 20)
    page = request.GET.get('page', 1)

    try:
        estoques = paginator.page(page)
    except PageNotAnInteger:
        estoques = paginator.page(1)
    except EmptyPage:
        estoques = paginator.page(paginator.num_pages)

    context = {
        'estoques': estoques,
        'total_valor': total_valor,
        'locais': LocalEstoque.objects.filter(ativo=True).order_by('tipo', 'nome'),
    }
    return render(request, 'gestor/estoque/posicao_estoque.html', context)


# =============================================================================
# FASE 4 - ORDENS DE PRODUCAO
# =============================================================================

@modulo_ordem_producao
def ordem_producao_list(request):
    """Lista de Ordens de Producao"""
    ops_list = OrdemProducao.objects.select_related(
        'produto', 'local_producao', 'local_destino', 'criado_por'
    ).order_by('-criado_em')

    # Filtros
    status = request.GET.get('status')
    if status:
        ops_list = ops_list.filter(status=status)

    prioridade = request.GET.get('prioridade')
    if prioridade:
        ops_list = ops_list.filter(prioridade=prioridade)

    query = request.GET.get('q')
    if query:
        ops_list = ops_list.filter(
            Q(numero__icontains=query) |
            Q(produto__codigo__icontains=query) |
            Q(produto__nome__icontains=query)
        )

    # Estatisticas
    stats = {
        'total': OrdemProducao.objects.count(),
        'rascunho': OrdemProducao.objects.filter(status='rascunho').count(),
        'liberada': OrdemProducao.objects.filter(status='liberada').count(),
        'em_producao': OrdemProducao.objects.filter(status='em_producao').count(),
        'concluida': OrdemProducao.objects.filter(status='concluida').count(),
    }

    # Paginacao
    paginator = Paginator(ops_list, 20)
    page = request.GET.get('page', 1)

    try:
        ops = paginator.page(page)
    except PageNotAnInteger:
        ops = paginator.page(1)
    except EmptyPage:
        ops = paginator.page(paginator.num_pages)

    context = {
        'ops': ops,
        'stats': stats,
        'status_filtro': status,
        'query': query,
    }
    return render(request, 'gestor/ordem_producao/op_list.html', context)


@modulo_ordem_producao
def ordem_producao_create(request):
    """Criar nova Ordem de Producao"""
    if request.method == 'POST':
        form = OrdemProducaoForm(request.POST)
        if form.is_valid():
            op = form.save(commit=False)
            op.criado_por = request.user
            op.save()

            # Calcular materiais necessarios baseado na estrutura
            qtd_itens = op.calcular_materiais_necessarios()

            messages.success(
                request,
                f'OP {op.numero} criada com sucesso! {qtd_itens} materiais calculados.'
            )
            return redirect('gestor:ordem_producao_detail', pk=op.pk)
    else:
        form = OrdemProducaoForm()

    context = {
        'form': form,
        'titulo': 'Nova Ordem de Producao',
    }
    return render(request, 'gestor/ordem_producao/op_form.html', context)


@modulo_ordem_producao
def ordem_producao_detail(request, pk):
    """Detalhes da Ordem de Producao"""
    op = get_object_or_404(
        OrdemProducao.objects.select_related(
            'produto', 'local_producao', 'local_destino',
            'criado_por', 'liberado_por', 'concluido_por'
        ).prefetch_related('itens_consumo__produto'),
        pk=pk
    )

    # Adicionar informacao de estoque disponivel para cada item
    itens_consumo = []
    for item in op.itens_consumo.select_related('produto'):
        item.estoque_disponivel = item.produto.estoque_disponivel if hasattr(item.produto, 'estoque_disponivel') else 0
        itens_consumo.append(item)

    context = {
        'op': op,
        'itens_consumo': itens_consumo,
    }
    return render(request, 'gestor/ordem_producao/op_detail.html', context)


@modulo_ordem_producao
def ordem_producao_update(request, pk):
    """Editar Ordem de Producao (somente rascunho)"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if op.status != 'rascunho':
        messages.error(request, 'Apenas OPs em rascunho podem ser editadas.')
        return redirect('gestor:ordem_producao_detail', pk=pk)

    if request.method == 'POST':
        form = OrdemProducaoForm(request.POST, instance=op)
        if form.is_valid():
            op = form.save(commit=False)
            op.atualizado_por = request.user
            op.save()

            # Recalcular materiais se quantidade mudou
            op.calcular_materiais_necessarios()

            messages.success(request, f'OP {op.numero} atualizada com sucesso!')
            return redirect('gestor:ordem_producao_detail', pk=pk)
    else:
        form = OrdemProducaoForm(instance=op)

    context = {
        'form': form,
        'op': op,
        'titulo': f'Editar OP {op.numero}',
    }
    return render(request, 'gestor/ordem_producao/op_form.html', context)


@modulo_ordem_producao
def ordem_producao_delete(request, pk):
    """Excluir Ordem de Producao (somente rascunho)"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if op.status != 'rascunho':
        messages.error(request, 'Apenas OPs em rascunho podem ser excluidas.')
        return redirect('gestor:ordem_producao_detail', pk=pk)

    if request.method == 'POST':
        numero = op.numero
        op.delete()
        messages.success(request, f'OP {numero} excluida com sucesso!')
        return redirect('gestor:ordem_producao_list')

    context = {'op': op}
    return render(request, 'gestor/ordem_producao/op_delete.html', context)


@modulo_ordem_producao
def ordem_producao_liberar(request, pk):
    """Liberar OP para producao (reservar materiais)"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if request.method == 'POST':
        try:
            op.liberar(request.user)
            messages.success(
                request,
                f'OP {op.numero} liberada! Materiais reservados no estoque.'
            )
        except Exception as e:
            messages.error(request, f'Erro ao liberar OP: {str(e)}')

    return redirect('gestor:ordem_producao_detail', pk=pk)


@modulo_ordem_producao
def ordem_producao_iniciar(request, pk):
    """Iniciar producao"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if request.method == 'POST':
        try:
            op.iniciar_producao(request.user)
            messages.success(request, f'Producao iniciada para OP {op.numero}!')
        except Exception as e:
            messages.error(request, f'Erro ao iniciar producao: {str(e)}')

    return redirect('gestor:ordem_producao_detail', pk=pk)


@modulo_ordem_producao
def ordem_producao_apontar(request, pk):
    """Apontar producao (registrar quantidade produzida)"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if op.status != 'em_producao':
        messages.error(request, 'OP nao esta em producao.')
        return redirect('gestor:ordem_producao_detail', pk=pk)

    if request.method == 'POST':
        form = ApontamentoProducaoForm(request.POST)
        if form.is_valid():
            try:
                quantidade = form.cleaned_data['quantidade_produzida']
                op.registrar_producao(quantidade, request.user)
                messages.success(
                    request,
                    f'Apontamento registrado: {quantidade} unidades. '
                    f'Total produzido: {op.quantidade_produzida}/{op.quantidade_planejada}'
                )
            except Exception as e:
                messages.error(request, f'Erro no apontamento: {str(e)}')
            return redirect('gestor:ordem_producao_detail', pk=pk)
    else:
        form = ApontamentoProducaoForm()

    quantidade_restante = op.quantidade_planejada - op.quantidade_produzida

    context = {
        'form': form,
        'op': op,
        'quantidade_restante': quantidade_restante,
        'apontamentos': [],  # Historico futuro
    }
    return render(request, 'gestor/ordem_producao/op_apontar.html', context)


@modulo_ordem_producao
def ordem_producao_concluir(request, pk):
    """Concluir OP (consumir materiais e dar entrada no PA)"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if request.method == 'POST':
        try:
            op.concluir(request.user)

            # Dar entrada do produto no estoque
            produto = op.produto
            posicao, created = Estoque.objects.get_or_create(
                produto=produto,
                local_estoque=op.local_destino,
                defaults={'quantidade': 0, 'custo_medio': 0}
            )
            posicao.quantidade += op.quantidade_produzida
            posicao.ultima_entrada = timezone.now().date()
            posicao.save()

            # Atualizar estoque do produto
            produto.estoque_atual += op.quantidade_produzida
            produto.save(update_fields=['estoque_atual'])

            messages.success(
                request,
                f'OP {op.numero} concluida! {op.quantidade_produzida} unidades '
                f'de {produto.codigo} entraram no estoque.'
            )
        except Exception as e:
            messages.error(request, f'Erro ao concluir OP: {str(e)}')

    return redirect('gestor:ordem_producao_detail', pk=pk)


@modulo_ordem_producao
def ordem_producao_cancelar(request, pk):
    """Cancelar OP"""
    op = get_object_or_404(OrdemProducao, pk=pk)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        try:
            op.cancelar(request.user, motivo)
            messages.success(request, f'OP {op.numero} cancelada.')
        except Exception as e:
            messages.error(request, f'Erro ao cancelar OP: {str(e)}')

    return redirect('gestor:ordem_producao_detail', pk=pk)