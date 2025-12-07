# producao/views/fornecedores.py

"""
CRUD de Fornecedores
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models import Fornecedor, FornecedorProduto, Produto
from core.forms import FornecedorForm, FornecedorProdutoFormSet

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD FORNECEDORES
# =============================================================================

@portal_producao
def fornecedor_list(request):
    """Lista de fornecedores com filtros e paginação"""
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


@portal_producao
def fornecedor_create(request):
    """Criar novo fornecedor"""
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


@portal_producao
def fornecedor_update(request, pk):
    """Editar fornecedor"""
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fornecedor "{fornecedor.razao_social}" atualizado com sucesso.')
            return redirect('producao:fornecedor_list')
    else:
        form = FornecedorForm(instance=fornecedor)
    
    return render(request, 'producao/fornecedor_form.html', {
        'form': form, 
        'fornecedor': fornecedor
    })


@portal_producao
def fornecedor_delete(request, pk):
    """Excluir fornecedor"""
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        try:
            nome = fornecedor.razao_social
            fornecedor.delete()
            messages.success(request, f'Fornecedor "{nome}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir fornecedor: {str(e)}')
        
        return redirect('producao:fornecedor_list')

    return render(request, 'producao/fornecedor_delete.html', {'fornecedor': fornecedor})


@portal_producao
def fornecedor_toggle_status(request, pk):
    """Ativar/desativar fornecedor"""
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    fornecedor.ativo = not fornecedor.ativo
    fornecedor.save()

    status_text = "ativado" if fornecedor.ativo else "desativado"
    messages.success(request, f'Fornecedor "{fornecedor.razao_social}" {status_text} com sucesso.')

    return redirect('producao:fornecedor_list')


# =============================================================================
# GESTÃO DE FORNECEDORES DO PRODUTO
# =============================================================================

@portal_producao
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


@portal_producao
def fornecedor_produto_toggle(request, pk):
    """Ativar/desativar relação fornecedor-produto"""
    fornecedor_produto = get_object_or_404(FornecedorProduto, pk=pk)
    fornecedor_produto.ativo = not fornecedor_produto.ativo
    fornecedor_produto.save()

    status_text = "ativado" if fornecedor_produto.ativo else "desativado"
    messages.success(request, f'Fornecedor {status_text} para este produto.')

    return redirect('producao:fornecedor_list')