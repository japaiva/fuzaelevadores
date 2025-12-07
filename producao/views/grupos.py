# producao/views/grupos.py

"""
CRUD de Grupos e Subgrupos de Produtos
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db.models.deletion import ProtectedError

from core.models import GrupoProduto, SubgrupoProduto
from core.forms import GrupoProdutoForm, SubgrupoProdutoForm

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD GRUPOS DE PRODUTOS
# =============================================================================

@portal_producao
def grupo_list(request):
    """Lista de grupos de produtos com filtros"""
    grupos_list = GrupoProduto.objects.all().order_by('codigo')

    # Filtros
    status = request.GET.get('status')
    if status == 'ativo':
        grupos_list = grupos_list.filter(ativo=True)
    elif status == 'inativo':
        grupos_list = grupos_list.filter(ativo=False)

    # Filtro por tipo de produto
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

    return render(request, 'producao/produtos/grupo_list.html', {
        'grupos': grupos,
        'status_filtro': status,
        'tipo_filtro': tipo,
        'query': query
    })


@portal_producao
def grupo_create(request):
    """Criar novo grupo de produtos"""
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
    
    return render(request, 'producao/produtos/grupo_form.html', {'form': form})


@portal_producao
def grupo_update(request, pk):
    """Editar grupo de produtos"""
    grupo = get_object_or_404(GrupoProduto, pk=pk)
    
    if request.method == 'POST':
        form = GrupoProdutoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupo "{grupo.nome}" atualizado com sucesso.')
            return redirect('producao:grupo_list')
    else:
        form = GrupoProdutoForm(instance=grupo)
    
    return render(request, 'producao/produtos/grupo_form.html', {
        'form': form, 
        'grupo': grupo
    })


@portal_producao
def grupo_delete(request, pk):
    """Excluir grupo de produtos"""
    grupo = get_object_or_404(GrupoProduto, pk=pk)

    if request.method == 'POST':
        try:
            nome = grupo.nome
            grupo.delete()
            messages.success(request, f'Grupo "{nome}" excluído com sucesso.')
        except ProtectedError:
            messages.error(request, 'Este grupo não pode ser excluído pois possui subgrupos ou produtos vinculados.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir grupo: {str(e)}')
        
        return redirect('producao:grupo_list')

    return render(request, 'producao/produtos/grupo_delete.html', {'grupo': grupo})


@portal_producao
def grupo_toggle_status(request, pk):
    """Ativar/desativar grupo"""
    grupo = get_object_or_404(GrupoProduto, pk=pk)
    grupo.ativo = not grupo.ativo
    grupo.save()

    status_text = "ativado" if grupo.ativo else "desativado"
    messages.success(request, f'Grupo "{grupo.nome}" {status_text} com sucesso.')

    return redirect('producao:grupo_list')


# =============================================================================
# CRUD SUBGRUPOS DE PRODUTOS
# =============================================================================

@portal_producao
def subgrupo_list(request):
    """Lista de subgrupos de produtos com filtros"""
    subgrupos_list = SubgrupoProduto.objects.select_related('grupo').order_by('grupo__codigo', 'codigo')

    # Filtros
    grupo_id = request.GET.get('grupo')
    if grupo_id:
        subgrupos_list = subgrupos_list.filter(grupo_id=grupo_id)

    # Filtro por tipo de produto
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

    return render(request, 'producao/produtos/subgrupo_list.html', {
        'subgrupos': subgrupos,
        'grupos': grupos,
        'grupo_filtro': grupo_id,
        'tipo_filtro': tipo,
        'status_filtro': status,
        'query': query
    })


@portal_producao
def subgrupo_create(request):
    """Criar novo subgrupo de produtos"""
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

    return render(request, 'producao/produtos/subgrupo_form.html', {'form': form})


@portal_producao
def subgrupo_update(request, pk):
    """Editar subgrupo de produtos"""
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)
    
    if request.method == 'POST':
        form = SubgrupoProdutoForm(request.POST, instance=subgrupo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subgrupo "{subgrupo.nome}" atualizado com sucesso.')
            return redirect('producao:subgrupo_list')
    else:
        form = SubgrupoProdutoForm(instance=subgrupo)
    
    return render(request, 'producao/produtos/subgrupo_form.html', {
        'form': form, 
        'subgrupo': subgrupo
    })


@portal_producao
def subgrupo_delete(request, pk):
    """Excluir subgrupo de produtos"""
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)

    if request.method == 'POST':
        try:
            nome = subgrupo.nome
            subgrupo.delete()
            messages.success(request, f'Subgrupo "{nome}" excluído com sucesso.')
        except ProtectedError:
            messages.error(request, 'Este subgrupo não pode ser excluído pois possui produtos vinculados.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir subgrupo: {str(e)}')
        
        return redirect('producao:subgrupo_list')

    return render(request, 'producao/produtos/subgrupo_delete.html', {'subgrupo': subgrupo})


@portal_producao
def subgrupo_toggle_status(request, pk):
    """Ativar/desativar subgrupo"""
    subgrupo = get_object_or_404(SubgrupoProduto, pk=pk)
    subgrupo.ativo = not subgrupo.ativo
    subgrupo.save()

    status_text = "ativado" if subgrupo.ativo else "desativado"
    messages.success(request, f'Subgrupo "{subgrupo.nome}" {status_text} com sucesso.')

    return redirect('producao:subgrupo_list')