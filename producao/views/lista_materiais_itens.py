# producao/views/lista_materiais_itens.py
# NOVO: CRUD simples para itens da lista de materiais

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from django.db import models
from django.core.paginator import Paginator

from core.models import ListaMateriais, ItemListaMateriais, Produto


@portal_producao
def item_lista_materiais_list(request, lista_id):
    """Lista os itens de uma lista de materiais específica"""
    lista = get_object_or_404(ListaMateriais, id=lista_id)
    
    # Buscar itens com filtros opcionais
    itens_query = lista.itens.select_related('produto__grupo', 'produto__subgrupo').order_by('produto__codigo')
    
    # Filtro por busca
    search = request.GET.get('q', '')
    if search:
        itens_query = itens_query.filter(
            produto__codigo__icontains=search
        ) | itens_query.filter(
            produto__nome__icontains=search
        )
    
    # Paginação
    paginator = Paginator(itens_query, 20)
    page = request.GET.get('page', 1)
    try:
        itens = paginator.page(page)
    except:
        itens = paginator.page(1)
    
    context = {
        'lista': lista,
        'itens': itens,
        'search': search,
        'pode_editar': lista.pode_editar,
        'total_itens': itens_query.count(),
        'proposta': lista.proposta,
    }
    return render(request, 'producao/lista_materiais/item_list.html', context)


@portal_producao
def item_lista_materiais_create(request, lista_id):
    """Criar novo item na lista de materiais"""
    lista = get_object_or_404(ListaMateriais, id=lista_id)
    
    # Verificar se pode editar
    if not lista.pode_editar:
        messages.error(request, 'Esta lista não pode mais ser editada.')
        return redirect('producao:item_lista_materiais_list', lista_id=lista.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                produto_id = request.POST.get('produto')
                quantidade = float(request.POST.get('quantidade', 0))
                observacoes = request.POST.get('observacoes', '')
                
                # Validações básicas
                if not produto_id:
                    messages.error(request, 'Produto é obrigatório.')
                    return redirect('producao:item_lista_materiais_create', lista_id=lista.id)
                
                if quantidade <= 0:
                    messages.error(request, 'Quantidade deve ser maior que zero.')
                    return redirect('producao:item_lista_materiais_create', lista_id=lista.id)
                
                produto = get_object_or_404(Produto, pk=produto_id, tipo='MP', disponivel=True)
                
                # Verificar se produto já existe na lista
                if lista.itens.filter(produto=produto).exists():
                    messages.error(request, f'O produto {produto.codigo} já está na lista.')
                    return redirect('producao:item_lista_materiais_create', lista_id=lista.id)
                
                # Criar item
                ItemListaMateriais.objects.create(
                    lista=lista,
                    produto=produto,
                    quantidade=quantidade,
                    unidade=produto.unidade_medida,
                    observacoes=observacoes,
                    item_calculado=False  # Item adicionado manualmente
                )
                
                return redirect('producao:item_lista_materiais_list', lista_id=lista.id)
                
        except Exception as e:
            messages.error(request, f'Erro ao adicionar item: {str(e)}')
    
    # Buscar produtos disponíveis
    produtos = Produto.objects.filter(
        tipo='MP', 
        disponivel=True,
        status='ATIVO'
    ).select_related('grupo', 'subgrupo').order_by('codigo')
    
    context = {
        'lista': lista,
        'produtos': produtos,
        'proposta': lista.proposta,
    }
    return render(request, 'producao/lista_materiais/item_form.html', context)


@portal_producao
def item_lista_materiais_update(request, lista_id, item_id):
    """Editar item da lista de materiais"""
    lista = get_object_or_404(ListaMateriais, id=lista_id)
    item = get_object_or_404(ItemListaMateriais, id=item_id, lista=lista)
    
    # Verificar se pode editar
    if not lista.pode_editar:
        messages.error(request, 'Esta lista não pode mais ser editada.')
        return redirect('producao:item_lista_materiais_list', lista_id=lista.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                produto_id = request.POST.get('produto')
                quantidade = float(request.POST.get('quantidade', 0))
                observacoes = request.POST.get('observacoes', '')
                
                # Validações básicas
                if not produto_id:
                    messages.error(request, 'Produto é obrigatório.')
                    return redirect('producao:item_lista_materiais_update', lista_id=lista.id, item_id=item.id)
                
                if quantidade <= 0:
                    messages.error(request, 'Quantidade deve ser maior que zero.')
                    return redirect('producao:item_lista_materiais_update', lista_id=lista.id, item_id=item.id)
                
                produto = get_object_or_404(Produto, pk=produto_id, tipo='MP', disponivel=True)
                
                # Verificar se produto já existe na lista (exceto o item atual)
                if lista.itens.filter(produto=produto).exclude(id=item.id).exists():
                    messages.error(request, f'O produto {produto.codigo} já está na lista.')
                    return redirect('producao:item_lista_materiais_update', lista_id=lista.id, item_id=item.id)
                
                # Atualizar item
                item.produto = produto
                item.quantidade = quantidade
                item.unidade = produto.unidade_medida
                item.observacoes = observacoes
                item.save()
                
                messages.success(request, f'Item {produto.codigo} atualizado com sucesso!')
                return redirect('producao:item_lista_materiais_list', lista_id=lista.id)
                
        except Exception as e:
            messages.error(request, f'Erro ao atualizar item: {str(e)}')
    
    # Buscar produtos disponíveis
    produtos = Produto.objects.filter(
        tipo='MP', 
        disponivel=True,
        status='ATIVO'
    ).select_related('grupo', 'subgrupo').order_by('codigo')
    
    context = {
        'lista': lista,
        'item': item,
        'produtos': produtos,
        'proposta': lista.proposta,
        'editing': True,
    }
    return render(request, 'producao/lista_materiais/item_form.html', context)


@portal_producao
def item_lista_materiais_delete(request, lista_id, item_id):
    """Excluir item da lista de materiais"""
    lista = get_object_or_404(ListaMateriais, id=lista_id)
    item = get_object_or_404(ItemListaMateriais, id=item_id, lista=lista)
    
    # Verificar se pode editar
    if not lista.pode_editar:
        messages.error(request, 'Esta lista não pode mais ser editada.')
        return redirect('producao:item_lista_materiais_list', lista_id=lista.id)
    
    if request.method == 'POST':
        try:
            produto_codigo = item.produto.codigo
            item.delete()
            messages.success(request, f'Item {produto_codigo} removido da lista!')
            return redirect('producao:item_lista_materiais_list', lista_id=lista.id)
        except Exception as e:
            messages.error(request, f'Erro ao remover item: {str(e)}')
    
    context = {
        'lista': lista,
        'item': item,
        'proposta': lista.proposta,
    }
    return render(request, 'producao/lista_materiais/item_delete.html', context)


@portal_producao
def api_buscar_produtos(request):
    """API para buscar produtos por código ou nome"""
    termo = request.GET.get('q', '').strip()
    
    if len(termo) < 2:
        return JsonResponse({'produtos': []})
    
    produtos = Produto.objects.filter(
        tipo='MP',
        disponivel=True,
        status='ATIVO'
    ).filter(
        models.Q(codigo__icontains=termo) | 
        models.Q(nome__icontains=termo)
    ).select_related('grupo').order_by('codigo')[:20]
    
    produtos_data = []
    for produto in produtos:
        produtos_data.append({
            'id': produto.pk,
            'codigo': produto.codigo,
            'nome': produto.nome,
            'unidade_medida': produto.unidade_medida,
            'grupo': produto.grupo.nome if produto.grupo else '',
        })
    
    return JsonResponse({'produtos': produtos_data})