# producao/views/produtos_acabados.py

"""
CRUD de Produtos Acabados (Tipo = PA)
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models import Produto, GrupoProduto
from core.forms import ProdutoForm

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD PRODUTOS ACABADOS (TIPO = PA)
# =============================================================================

@portal_producao
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

    grupos = GrupoProduto.objects.filter(ativo=True, tipo_produto='PA').order_by('codigo')

    return render(request, 'producao/produtos/produto_acabado_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'status_filtro': status,
        'query': query
    })


@portal_producao
def produto_acabado_create(request):
    """Criar novo produto acabado"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)

        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PA'
            # Definir valores padrão para campos não exibidos no form simplificado
            if not produto.unidade_medida:
                produto.unidade_medida = 'UN'
            produto.controla_estoque = False  # PA não controla estoque direto
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.save()

            messages.success(request, f'Produto acabado "{produto.codigo} - {produto.nome}" criado com sucesso.')
            return redirect('producao:produto_acabado_list')
        else:
            messages.error(request, 'Erro ao criar produto acabado. Verifique os dados informados.')
            logger.error(f'Erros no formulário PA: {form.errors}')
    else:
        # Inicializar form com valores padrão para PA
        form = ProdutoForm(initial={
            'unidade_medida': 'UN',
            'controla_estoque': False,
            'status': 'ATIVO'
        })

    # Filtrar grupos apenas do tipo PA
    form.fields['grupo'].queryset = GrupoProduto.objects.filter(tipo_produto='PA', ativo=True).order_by('codigo')

    return render(request, 'producao/produtos/produto_acabado_form.html', {'form': form})


@portal_producao
def produto_acabado_update(request, pk):
    """Editar produto acabado"""
    from core.models import SubgrupoProduto

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

    # Filtrar grupos apenas do tipo PA
    form.fields['grupo'].queryset = GrupoProduto.objects.filter(tipo_produto='PA', ativo=True).order_by('codigo')

    # Filtrar subgrupos do grupo atual do produto
    if produto.grupo:
        form.fields['subgrupo'].queryset = SubgrupoProduto.objects.filter(
            grupo=produto.grupo, ativo=True
        ).order_by('codigo')

    return render(request, 'producao/produtos/produto_acabado_form.html', {
        'form': form,
        'produto': produto
    })


@portal_producao
def produto_acabado_delete(request, pk):
    """Excluir produto acabado"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PA')

    if request.method == 'POST':
        try:
            codigo_nome = f"{produto.codigo} - {produto.nome}"
            produto.delete()
            messages.success(request, f'Produto acabado "{codigo_nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir produto acabado: {str(e)}')

        return redirect('producao:produto_acabado_list')

    return render(request, 'producao/produtos/produto_acabado_delete.html', {'produto': produto})


@portal_producao
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