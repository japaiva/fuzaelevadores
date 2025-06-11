# producao/views/produtos_intermediarios.py

"""
CRUD de Produtos Intermediários (Tipo = PI)
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models import Produto, GrupoProduto
from core.forms import ProdutoForm

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD PRODUTOS INTERMEDIÁRIOS (TIPO = PI)
# =============================================================================

@login_required
def produto_intermediario_list(request):
    """Lista apenas produtos do tipo Produto Intermediário (PI)"""
    produtos_list = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='PI').order_by('codigo')

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
def produto_intermediario_delete(request, pk):
    """Excluir produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI')

    if request.method == 'POST':
        try:
            codigo_nome = f"{produto.codigo} - {produto.nome}"
            produto.delete()
            messages.success(request, f'Produto intermediário "{codigo_nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir produto intermediário: {str(e)}')

        return redirect('producao:produto_intermediario_list')

    return render(request, 'producao/produto_intermediario_delete.html', {'produto': produto})


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