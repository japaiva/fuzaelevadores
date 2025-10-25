# producao/views/requisicoes_compra.py

"""
CRUD de Requisições de Compra - baseado no padrão dos orçamentos
Portal de Produção - Sistema Elevadores FUZA
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from core.models import (
    RequisicaoCompra, ItemRequisicaoCompra,
    ListaMateriais, Produto
)
from core.forms import (
    RequisicaoCompraForm, RequisicaoCompraFiltroForm,
    ItemRequisicaoCompraFormSet
)

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD REQUISIÇÕES DE COMPRA
# =============================================================================

@login_required
def requisicao_compra_list(request):
    """Lista de requisições de compra com filtros"""
    requisicoes_list = RequisicaoCompra.objects.select_related(
        'lista_materiais__proposta', 'solicitante', 'criado_por'
    ).prefetch_related('itens').order_by('-data_requisicao')

    # Aplicar filtros
    form_filtros = RequisicaoCompraFiltroForm(request.GET)
    if form_filtros.is_valid():
        data = form_filtros.cleaned_data

        if data.get('status'):
            requisicoes_list = requisicoes_list.filter(status=data['status'])

        if data.get('prioridade'):
            requisicoes_list = requisicoes_list.filter(prioridade=data['prioridade'])

        if data.get('data_inicio'):
            requisicoes_list = requisicoes_list.filter(data_requisicao__gte=data['data_inicio'])

        if data.get('data_fim'):
            requisicoes_list = requisicoes_list.filter(data_requisicao__lte=data['data_fim'])

        if data.get('q'):
            query = data['q']
            requisicoes_list = requisicoes_list.filter(
                Q(numero__icontains=query) |
                Q(lista_materiais__proposta__numero__icontains=query) |
                Q(justificativa__icontains=query) |
                Q(observacoes__icontains=query)
            )

    # Paginação
    paginator = Paginator(requisicoes_list, 15)
    page = request.GET.get('page', 1)

    try:
        requisicoes = paginator.page(page)
    except:
        requisicoes = paginator.page(1)

    context = {
        'requisicoes': requisicoes,
        'form_filtros': form_filtros,
        'total_requisicoes': requisicoes_list.count(),
    }

    return render(request, 'producao/requisicoes/requisicao_compra_list.html', context)


@login_required
def requisicao_compra_create(request):
    """Criar nova requisição de compra"""
    # Pegar lista_materiais_id da URL se vier da lista de materiais
    lista_materiais_id = request.GET.get('lista_materiais')

    if request.method == 'POST':
        form = RequisicaoCompraForm(request.POST)
        formset = ItemRequisicaoCompraFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Criar requisição
                    requisicao = form.save(commit=False)
                    requisicao.criado_por = request.user
                    requisicao.atualizado_por = request.user
                    requisicao.save()

                    # Salvar itens do formset
                    formset.instance = requisicao
                    formset.save()

                    messages.success(request, f'Requisição {requisicao.numero} criada com sucesso!')
                    return redirect('producao:requisicao_compra_detail', pk=requisicao.pk)

            except Exception as e:
                logger.error(f"Erro ao criar requisição: {str(e)}")
                messages.error(request, f'Erro ao criar requisição: {str(e)}')
        else:
            # Mostrar erros específicos
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                        logger.error(f"Erro no campo {field}: {error}")

            if not formset.is_valid():
                for i, form_item in enumerate(formset):
                    if form_item.errors:
                        for field, errors in form_item.errors.items():
                            for error in errors:
                                messages.error(request, f'Item {i+1} - {field}: {error}')
                                logger.error(f"Erro no item {i+1}, campo {field}: {error}")

                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, f'Erro geral: {error}')
                        logger.error(f"Erro geral do formset: {error}")

            messages.error(request, 'Erro ao criar requisição. Verifique os dados informados.')
    else:
        # Inicializar form e formset
        initial = {}
        if lista_materiais_id:
            try:
                lista_materiais = ListaMateriais.objects.get(pk=lista_materiais_id)
                initial['lista_materiais'] = lista_materiais
                initial['data_necessidade'] = lista_materiais.proposta.prazo_entrega_dias
            except ListaMateriais.DoesNotExist:
                pass

        form = RequisicaoCompraForm(initial=initial)

        # Se tem lista de materiais, inicializar formset com os itens
        formset_initial = []
        if lista_materiais_id:
            try:
                lista_materiais = ListaMateriais.objects.get(pk=lista_materiais_id)
                for item in lista_materiais.itens.all():
                    formset_initial.append({
                        'produto': item.produto,
                        'produto_search': f"{item.produto.codigo} - {item.produto.nome}",
                        'quantidade': item.quantidade,
                        'valor_unitario_estimado': item.valor_unitario_estimado,
                        'observacoes': item.observacoes
                    })
            except ListaMateriais.DoesNotExist:
                pass

        formset = ItemRequisicaoCompraFormSet(initial=formset_initial)

    context = {
        'form': form,
        'formset': formset,
        'title': 'Nova Requisição de Compra'
    }

    return render(request, 'producao/requisicoes/requisicao_compra_form.html', context)


@login_required
def requisicao_compra_detail(request, pk):
    """Detalhes da requisição de compra"""
    requisicao = get_object_or_404(
        RequisicaoCompra.objects.select_related(
            'lista_materiais__proposta', 'solicitante', 'criado_por'
        ).prefetch_related('itens__produto', 'orcamentos'),
        pk=pk
    )

    context = {
        'requisicao': requisicao,
        'pode_editar': requisicao.pode_editar,
        'pode_cancelar': requisicao.pode_cancelar,
    }

    return render(request, 'producao/requisicoes/requisicao_compra_detail.html', context)


@login_required
def requisicao_compra_update(request, pk):
    """Editar requisição de compra"""
    requisicao = get_object_or_404(RequisicaoCompra, pk=pk)

    if not requisicao.pode_editar:
        messages.error(request, f'Requisição {requisicao.numero} não pode ser editada no status atual.')
        return redirect('producao:requisicao_compra_detail', pk=pk)

    if request.method == 'POST':
        form = RequisicaoCompraForm(request.POST, instance=requisicao)
        formset = ItemRequisicaoCompraFormSet(request.POST, instance=requisicao)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    requisicao = form.save(commit=False)
                    requisicao.atualizado_por = request.user
                    requisicao.save()

                    # Salvar itens do formset
                    formset.save()

                    messages.success(request, f'Requisição {requisicao.numero} atualizada com sucesso!')
                    return redirect('producao:requisicao_compra_detail', pk=requisicao.pk)

            except Exception as e:
                logger.error(f"Erro ao atualizar requisição: {str(e)}")
                messages.error(request, f'Erro ao atualizar requisição: {str(e)}')
        else:
            # Mostrar erros específicos
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                        logger.error(f"Erro no campo {field}: {error}")

            if not formset.is_valid():
                for i, form_item in enumerate(formset):
                    if form_item.errors:
                        for field, errors in form_item.errors.items():
                            for error in errors:
                                messages.error(request, f'Item {i+1} - {field}: {error}')
                                logger.error(f"Erro no item {i+1}, campo {field}: {error}")

                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, f'Erro geral: {error}')
                        logger.error(f"Erro geral do formset: {error}")

            messages.error(request, 'Erro ao atualizar requisição. Verifique os dados informados.')
    else:
        form = RequisicaoCompraForm(instance=requisicao)
        formset = ItemRequisicaoCompraFormSet(instance=requisicao)

    context = {
        'form': form,
        'formset': formset,
        'requisicao': requisicao,
        'title': f'Editar Requisição {requisicao.numero}'
    }

    return render(request, 'producao/requisicoes/requisicao_compra_form.html', context)


@login_required
def requisicao_compra_delete(request, pk):
    """Excluir requisição de compra"""
    requisicao = get_object_or_404(RequisicaoCompra, pk=pk)

    # Verificar se pode ser excluída
    if requisicao.status not in ['rascunho', 'aberta']:
        messages.error(request, f'Requisição {requisicao.numero} não pode ser excluída no status atual: {requisicao.get_status_display()}.')
        return redirect('producao:requisicao_compra_detail', pk=pk)

    if request.method == 'POST':
        try:
            numero = requisicao.numero
            with transaction.atomic():
                requisicao.delete()

            messages.success(request, f'Requisição {numero} excluída com sucesso!')
            return redirect('producao:requisicao_compra_list')

        except Exception as e:
            messages.error(request, f'Erro ao excluir requisição: {str(e)}')
            return redirect('producao:requisicao_compra_detail', pk=pk)

    return render(request, 'producao/requisicoes/requisicao_compra_delete.html', {'requisicao': requisicao})


@login_required
def requisicao_compra_alterar_status(request, pk):
    """Alterar status da requisição"""
    requisicao = get_object_or_404(RequisicaoCompra, pk=pk)

    if request.method == 'POST':
        novo_status = request.POST.get('status')
        observacao = request.POST.get('observacao', '')

        # Validar transições de status
        status_validos = {
            'rascunho': ['aberta', 'cancelada'],
            'aberta': ['cotando', 'cancelada'],
            'cotando': ['orcada', 'cancelada'],
            'orcada': ['aprovada', 'cancelada'],
            'aprovada': [],  # Status final
            'cancelada': []  # Status final
        }

        if novo_status not in status_validos.get(requisicao.status, []):
            messages.error(request, 'Transição de status não permitida.')
            return redirect('producao:requisicao_compra_detail', pk=pk)

        try:
            requisicao.status = novo_status
            requisicao.atualizado_por = request.user
            requisicao.save()

            messages.success(request, f'Status alterado para "{requisicao.get_status_display()}".')
            return redirect('producao:requisicao_compra_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'Erro ao alterar status: {str(e)}')

    # Definir opções de status baseado no status atual
    status_choices = []
    if requisicao.status == 'rascunho':
        status_choices = [
            ('rascunho', 'Rascunho'),
            ('aberta', 'Aberta'),
            ('cancelada', 'Cancelada'),
        ]
    elif requisicao.status == 'aberta':
        status_choices = [
            ('aberta', 'Aberta'),
            ('cotando', 'Em Cotação'),
            ('cancelada', 'Cancelada'),
        ]
    elif requisicao.status == 'cotando':
        status_choices = [
            ('cotando', 'Em Cotação'),
            ('orcada', 'Orçada'),
            ('cancelada', 'Cancelada'),
        ]
    elif requisicao.status == 'orcada':
        status_choices = [
            ('orcada', 'Orçada'),
            ('aprovada', 'Aprovada'),
            ('cancelada', 'Cancelada'),
        ]

    context = {
        'requisicao': requisicao,
        'status_choices': status_choices
    }

    return render(request, 'producao/requisicoes/requisicao_compra_alterar_status.html', context)


@login_required
def requisicao_compra_gerar_orcamento(request, pk):
    """Gerar orçamento a partir da requisição"""
    requisicao = get_object_or_404(RequisicaoCompra, pk=pk)

    if requisicao.status not in ['orcada', 'aprovada']:
        messages.error(request, 'Requisição deve estar cotada ou aprovada para gerar orçamento.')
        return redirect('producao:requisicao_compra_detail', pk=pk)

    try:
        from core.models import OrcamentoCompra, ItemOrcamentoCompra
        
        with transaction.atomic():
            # Criar orçamento
            orcamento = OrcamentoCompra(
                titulo=f"Orçamento - {requisicao.lista_materiais.proposta.numero}",
                prioridade=requisicao.prioridade,
                data_necessidade=requisicao.data_necessidade,
                comprador_responsavel=request.user,
                solicitante=requisicao.solicitante,
                descricao=f"Gerado a partir da requisição {requisicao.numero}",
                observacoes=requisicao.observacoes,
                observacoes_internas=f"Requisição: {requisicao.numero}",
                criado_por=request.user,
                atualizado_por=request.user
            )
            orcamento.save()

            # Adicionar requisição ao orçamento
            orcamento.requisicoes.add(requisicao)

            # Copiar itens
            for item in requisicao.itens.all():
                ItemOrcamentoCompra.objects.create(
                    orcamento=orcamento,
                    produto=item.produto,
                    quantidade=item.quantidade,
                    valor_unitario_estimado=item.valor_unitario_estimado or 0,
                    observacoes=item.observacoes
                )

            # Recalcular valores
            orcamento.calcular_valores()
            orcamento.save(update_fields=['valor_total_estimado', 'valor_total_cotado'])

            # Atualizar status da requisição
            requisicao.status = 'orcada'
            requisicao.atualizado_por = request.user
            requisicao.save()

            messages.success(request, f'Orçamento {orcamento.numero} gerado com sucesso!')
            return redirect('producao:orcamento_compra_detail', pk=orcamento.pk)

    except Exception as e:
        messages.error(request, f'Erro ao gerar orçamento: {str(e)}')
        return redirect('producao:requisicao_compra_detail', pk=pk)