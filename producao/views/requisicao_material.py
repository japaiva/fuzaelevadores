# producao/views/requisicao_material.py

"""
Views para Requisição de Material
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q

from core.models.estoque import (
    RequisicaoMaterial,
    ItemRequisicaoMaterial,
)
from core.forms.estoque import (
    RequisicaoMaterialForm,
    ItemRequisicaoMaterialForm,
    ItemRequisicaoFormSet,
    RequisicaoMaterialFiltroForm,
)
from core.models.estoque import TipoMovimentoSaida
from core.decorators import portal_producao


# ===============================================
# CRUD REQUISIÇÃO DE MATERIAL
# ===============================================

@portal_producao
def requisicao_material_list(request):
    """Lista de Requisições de Material"""

    form_filtro = RequisicaoMaterialFiltroForm(request.GET)
    requisicoes_list = RequisicaoMaterial.objects.select_related(
        'tipo_movimento', 'proposta__cliente', 'criado_por'
    ).order_by('-data_requisicao', '-numero')

    # Aplicar filtros
    if form_filtro.is_valid():
        status = form_filtro.cleaned_data.get('status')
        tipo_movimento = form_filtro.cleaned_data.get('tipo_movimento')
        data_de = form_filtro.cleaned_data.get('data_de')
        data_ate = form_filtro.cleaned_data.get('data_ate')
        busca = form_filtro.cleaned_data.get('busca')

        if status:
            requisicoes_list = requisicoes_list.filter(status=status)
        if tipo_movimento:
            requisicoes_list = requisicoes_list.filter(tipo_movimento=tipo_movimento)
        if data_de:
            requisicoes_list = requisicoes_list.filter(data_requisicao__gte=data_de)
        if data_ate:
            requisicoes_list = requisicoes_list.filter(data_requisicao__lte=data_ate)
        if busca:
            requisicoes_list = requisicoes_list.filter(
                Q(numero__icontains=busca) |
                Q(proposta__numero__icontains=busca)
            )

    # Paginação
    paginator = Paginator(requisicoes_list, 20)
    page = request.GET.get('page')
    requisicoes = paginator.get_page(page)

    context = {
        'requisicoes': requisicoes,
        'form_filtro': form_filtro,
    }

    return render(request, 'producao/requisicao_material/requisicao_material_list.html', context)


@portal_producao
def requisicao_material_create(request):
    """Criar nova Requisição de Material"""

    if request.method == 'POST':
        form = RequisicaoMaterialForm(request.POST, user=request.user)
        formset = ItemRequisicaoFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            requisicao = form.save()
            formset.instance = requisicao
            formset.save()
            messages.success(request, f'Requisição {requisicao.numero} criada com sucesso!')
            return redirect('producao:requisicao_material_detail', pk=requisicao.pk)
    else:
        form = RequisicaoMaterialForm(user=request.user)
        formset = ItemRequisicaoFormSet(prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Requisição de Material',
        'tipos_movimento': TipoMovimentoSaida.objects.filter(
            ativo=True, tipo_operacao='op'
        ).values('id', 'tipo_parceiro', 'tipo_produto'),
    }

    return render(request, 'producao/requisicao_material/requisicao_material_form.html', context)


@portal_producao
def requisicao_material_detail(request, pk):
    """Detalhes da Requisição de Material"""

    requisicao = get_object_or_404(
        RequisicaoMaterial.objects.select_related('proposta__cliente', 'criado_por', 'tipo_movimento'),
        pk=pk
    )
    itens = requisicao.itens.select_related('produto').all()

    context = {
        'requisicao': requisicao,
        'itens': itens,
    }

    return render(request, 'producao/requisicao_material/requisicao_material_detail.html', context)


@portal_producao
def requisicao_material_update(request, pk):
    """Editar Requisição de Material"""

    requisicao = get_object_or_404(RequisicaoMaterial, pk=pk)

    # Não permitir edição se não estiver em rascunho
    if requisicao.status != 'rascunho':
        messages.error(request, 'Apenas requisições em rascunho podem ser editadas.')
        return redirect('producao:requisicao_material_detail', pk=pk)

    if request.method == 'POST':
        form = RequisicaoMaterialForm(request.POST, instance=requisicao, user=request.user)
        formset = ItemRequisicaoFormSet(request.POST, instance=requisicao, prefix='itens')

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Requisição atualizada com sucesso!')
            return redirect('producao:requisicao_material_detail', pk=pk)
    else:
        form = RequisicaoMaterialForm(instance=requisicao, user=request.user)
        formset = ItemRequisicaoFormSet(instance=requisicao, prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'requisicao': requisicao,
        'titulo': f'Editar Requisição {requisicao.numero}',
        'tipos_movimento': TipoMovimentoSaida.objects.filter(
            ativo=True, tipo_operacao='op'
        ).values('id', 'tipo_parceiro', 'tipo_produto'),
    }

    return render(request, 'producao/requisicao_material/requisicao_material_form.html', context)


@portal_producao
def requisicao_material_delete(request, pk):
    """Excluir Requisição de Material"""

    requisicao = get_object_or_404(RequisicaoMaterial, pk=pk)

    # Não permitir exclusão se não estiver em rascunho
    if requisicao.status != 'rascunho':
        messages.error(request, 'Apenas requisições em rascunho podem ser excluídas.')
        return redirect('producao:requisicao_material_detail', pk=pk)

    if request.method == 'POST':
        numero = requisicao.numero
        requisicao.delete()
        messages.success(request, f'Requisição {numero} excluída com sucesso!')
        return redirect('producao:requisicao_material_list')

    context = {
        'requisicao': requisicao,
    }

    return render(request, 'producao/requisicao_material/requisicao_material_delete.html', context)


# ===============================================
# AÇÕES - ALTERAR STATUS
# ===============================================

@portal_producao
@require_POST
def requisicao_material_alterar_status(request, pk):
    """Alterar status da Requisição de Material"""

    requisicao = get_object_or_404(RequisicaoMaterial, pk=pk)
    novo_status = request.POST.get('status', '')

    status_validos = ['rascunho', 'pendente', 'atendida', 'parcial', 'cancelada']
    if novo_status not in status_validos:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Status inválido'})
        messages.error(request, 'Status inválido.')
        return redirect('producao:requisicao_material_detail', pk=pk)

    # Validações de transição
    if novo_status == 'pendente' and requisicao.status != 'rascunho':
        msg = 'Apenas requisições em rascunho podem ser enviadas.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect('producao:requisicao_material_detail', pk=pk)

    if novo_status == 'pendente' and not requisicao.itens.exists():
        msg = 'A requisição precisa ter itens para ser enviada.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect('producao:requisicao_material_detail', pk=pk)

    requisicao.status = novo_status
    requisicao.atualizado_por = request.user
    requisicao.save()

    status_display = dict(requisicao._meta.get_field('status').choices).get(novo_status, novo_status)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Status alterado para {status_display}',
            'novo_status': novo_status,
            'novo_status_display': status_display
        })

    messages.success(request, f'Status alterado para {status_display}.')
    return redirect('producao:requisicao_material_detail', pk=pk)


# ===============================================
# ITENS DA REQUISIÇÃO - API AJAX
# ===============================================

@portal_producao
@require_POST
def api_adicionar_item_requisicao(request, pk):
    """Adicionar item à requisição via AJAX"""

    requisicao = get_object_or_404(RequisicaoMaterial, pk=pk)

    if requisicao.status != 'rascunho':
        return JsonResponse({
            'success': False,
            'message': 'Apenas requisições em rascunho podem ser editadas.'
        })

    from core.models import Produto

    produto_id = request.POST.get('produto_id')
    quantidade = request.POST.get('quantidade')
    observacoes = request.POST.get('observacoes', '')

    try:
        produto = Produto.objects.get(pk=produto_id)
        quantidade = float(quantidade)

        if quantidade <= 0:
            return JsonResponse({'success': False, 'message': 'Quantidade inválida.'})

        # Verificar se produto já está na requisição
        item_existente = requisicao.itens.filter(produto=produto).first()
        if item_existente:
            item_existente.quantidade_solicitada += quantidade
            item_existente.save()
            item = item_existente
        else:
            item = ItemRequisicaoMaterial.objects.create(
                requisicao=requisicao,
                produto=produto,
                quantidade_solicitada=quantidade,
                unidade=produto.unidade,
                observacoes=observacoes
            )

        return JsonResponse({
            'success': True,
            'message': 'Item adicionado com sucesso!',
            'item': {
                'id': item.id,
                'produto_codigo': produto.codigo,
                'produto_descricao': produto.descricao,
                'quantidade_solicitada': str(item.quantidade_solicitada),
                'unidade': item.unidade,
            }
        })

    except Produto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Produto não encontrado.'})
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Quantidade inválida.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@portal_producao
@require_POST
def api_remover_item_requisicao(request, pk, item_pk):
    """Remover item da requisição via AJAX"""

    requisicao = get_object_or_404(RequisicaoMaterial, pk=pk)

    if requisicao.status != 'rascunho':
        return JsonResponse({
            'success': False,
            'message': 'Apenas requisições em rascunho podem ser editadas.'
        })

    item = get_object_or_404(ItemRequisicaoMaterial, pk=item_pk, requisicao=requisicao)
    item.delete()

    return JsonResponse({
        'success': True,
        'message': 'Item removido com sucesso!'
    })


@portal_producao
def api_buscar_produtos_requisicao(request, pk):
    """Buscar produtos para adicionar à requisição"""

    requisicao = get_object_or_404(RequisicaoMaterial.objects.select_related('tipo_movimento'), pk=pk)
    termo = request.GET.get('q', '')

    from core.models import Produto

    # Filtrar pelo tipo de produto do tipo de movimento
    tipo_produto = requisicao.tipo_movimento.tipo_produto if requisicao.tipo_movimento_id else 'MP'
    produtos = Produto.objects.filter(
        status='ATIVO',
        tipo=tipo_produto
    )

    if termo:
        produtos = produtos.filter(
            Q(codigo__icontains=termo) |
            Q(descricao__icontains=termo)
        )

    produtos = produtos[:20]

    data = [{
        'id': p.id,
        'codigo': p.codigo,
        'descricao': p.descricao,
        'unidade': p.unidade,
    } for p in produtos]

    return JsonResponse({'produtos': data})
