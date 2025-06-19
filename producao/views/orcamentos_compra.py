# producao/views/orcamentos_compra.py

"""
CRUD de Orçamentos de Compra - baseado no padrão dos pedidos
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
    OrcamentoCompra, ItemOrcamentoCompra, HistoricoOrcamentoCompra,
    RequisicaoCompra, Fornecedor, Produto
)
from core.forms import (
    OrcamentoCompraForm, ItemOrcamentoCompraFormSet, OrcamentoCompraFiltroForm,
    AlterarStatusOrcamentoForm
)

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD ORÇAMENTOS DE COMPRA
# =============================================================================

@login_required
def orcamento_compra_list(request):
    """Lista de orçamentos de compra com filtros"""
    orcamentos_list = OrcamentoCompra.objects.select_related(
        'comprador_responsavel', 'solicitante', 'criado_por'
    ).prefetch_related('itens', 'requisicoes').order_by('-data_orcamento')

    # Aplicar filtros
    form_filtros = OrcamentoCompraFiltroForm(request.GET)
    if form_filtros.is_valid():
        data = form_filtros.cleaned_data

        if data.get('status'):
            orcamentos_list = orcamentos_list.filter(status=data['status'])

        if data.get('prioridade'):
            orcamentos_list = orcamentos_list.filter(prioridade=data['prioridade'])

        if data.get('comprador'):
            orcamentos_list = orcamentos_list.filter(comprador_responsavel=data['comprador'])

        if data.get('situacao'):
            from datetime import date
            hoje = date.today()
            
            if data['situacao'] == 'vigente':
                orcamentos_list = orcamentos_list.filter(data_validade__gte=hoje)
            elif data['situacao'] == 'vencido':
                orcamentos_list = orcamentos_list.filter(data_validade__lt=hoje)
            elif data['situacao'] == 'vence_hoje':
                orcamentos_list = orcamentos_list.filter(data_validade=hoje)
            elif data['situacao'] == 'vence_semana':
                uma_semana = hoje + timedelta(days=7)
                orcamentos_list = orcamentos_list.filter(
                    data_validade__gte=hoje,
                    data_validade__lte=uma_semana
                )

        if data.get('data_inicio'):
            orcamentos_list = orcamentos_list.filter(data_orcamento__gte=data['data_inicio'])

        if data.get('data_fim'):
            orcamentos_list = orcamentos_list.filter(data_orcamento__lte=data['data_fim'])

        if data.get('q'):
            query = data['q']
            orcamentos_list = orcamentos_list.filter(
                Q(numero__icontains=query) |
                Q(titulo__icontains=query) |
                Q(descricao__icontains=query) |
                Q(observacoes__icontains=query)
            )

    # Paginação
    paginator = Paginator(orcamentos_list, 15)
    page = request.GET.get('page', 1)

    try:
        orcamentos = paginator.page(page)
    except:
        orcamentos = paginator.page(1)

    context = {
        'orcamentos': orcamentos,
        'form_filtros': form_filtros,
        'total_orcamentos': orcamentos_list.count(),
    }

    return render(request, 'producao/orcamentos/orcamento_compra_list.html', context)


@login_required
def orcamento_compra_create(request):
    """Criar novo orçamento de compra"""

    if request.method == 'POST':
        form = OrcamentoCompraForm(request.POST)
        formset = ItemOrcamentoCompraFormSet(request.POST)

        # Verificar se há pelo menos um item válido
        itens_validos = 0
        for form_item in formset:
            if form_item.is_valid() and not form_item.cleaned_data.get('DELETE', False):
                if (form_item.cleaned_data.get('produto') and
                    form_item.cleaned_data.get('quantidade')):
                    itens_validos += 1

        if form.is_valid() and formset.is_valid() and itens_validos > 0:
            try:
                with transaction.atomic():
                    # Criar orçamento
                    orcamento = form.save(commit=False)
                    orcamento.criado_por = request.user
                    orcamento.atualizado_por = request.user

                    # Salvar orçamento sem calcular valores ainda
                    orcamento.valor_total_estimado = 0
                    orcamento.valor_total_cotado = 0
                    orcamento.save()

                    # Salvar itens
                    itens_salvos = 0
                    for form_item in formset:
                        if (form_item.is_valid() and
                            not form_item.cleaned_data.get('DELETE', False) and
                            form_item.cleaned_data.get('produto')):

                            item = form_item.save(commit=False)
                            item.orcamento = orcamento

                            # Garantir que tem unidade
                            if not item.unidade:
                                item.unidade = item.produto.unidade_medida

                            item.save()
                            itens_salvos += 1

                    # Recalcular valores do orçamento
                    orcamento.calcular_valores()
                    orcamento.save(update_fields=['valor_total_estimado', 'valor_total_cotado'])

                    # Registrar no histórico
                    HistoricoOrcamentoCompra.objects.create(
                        orcamento=orcamento,
                        usuario=request.user,
                        acao='Orçamento criado',
                        observacao=f'Orçamento criado com {itens_salvos} itens'
                    )

                    messages.success(request, f'Orçamento {orcamento.numero} criado com sucesso!')
                    return redirect('producao:orcamento_compra_detail', pk=orcamento.pk)

            except Exception as e:
                logger.error(f"Erro ao criar orçamento: {str(e)}")
                messages.error(request, f'Erro ao criar orçamento: {str(e)}')
        else:
            if itens_validos == 0:
                messages.error(request, 'Adicione pelo menos um item válido ao orçamento.')
            else:
                messages.error(request, 'Erro ao criar orçamento. Verifique os dados informados.')
    else:
        form = OrcamentoCompraForm()
        formset = ItemOrcamentoCompraFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Novo Orçamento de Compra'
    }

    return render(request, 'producao/orcamentos/orcamento_compra_form.html', context)


@login_required
def orcamento_compra_detail(request, pk):
    """Detalhes do orçamento de compra"""
    orcamento = get_object_or_404(
        OrcamentoCompra.objects.select_related('comprador_responsavel', 'solicitante', 'criado_por')
        .prefetch_related('itens__produto', 'itens__fornecedor', 'requisicoes', 'historico__usuario'),
        pk=pk
    )

    context = {
        'orcamento': orcamento,
        'pode_editar': orcamento.pode_editar,
        'pode_cancelar': orcamento.pode_cancelar,
        'pode_gerar_pedido': orcamento.pode_gerar_pedido,
    }

    return render(request, 'producao/orcamentos/orcamento_compra_detail.html', context)


@login_required
def orcamento_compra_update(request, pk):
    """Editar orçamento de compra"""
    orcamento = get_object_or_404(OrcamentoCompra, pk=pk)

    if not orcamento.pode_editar:
        messages.error(request, f'Orçamento {orcamento.numero} não pode ser editado no status atual.')
        return redirect('producao:orcamento_compra_detail', pk=pk)

    if request.method == 'POST':
        form = OrcamentoCompraForm(request.POST, instance=orcamento)
        formset = ItemOrcamentoCompraFormSet(request.POST, instance=orcamento)

        # Verificar itens válidos
        itens_validos = 0
        for form_item in formset:
            if form_item.is_valid() and not form_item.cleaned_data.get('DELETE', False):
                if (form_item.cleaned_data.get('produto') and
                    form_item.cleaned_data.get('quantidade')):
                    itens_validos += 1

        if form.is_valid() and formset.is_valid() and itens_validos > 0:
            try:
                with transaction.atomic():
                    # Salvar orçamento
                    orcamento = form.save(commit=False)
                    orcamento.atualizado_por = request.user
                    orcamento.save()

                    # Salvar itens
                    formset.save()

                    # Recalcular valores
                    orcamento.calcular_valores()
                    orcamento.save(update_fields=['valor_total_estimado', 'valor_total_cotado'])

                    # Registrar no histórico
                    HistoricoOrcamentoCompra.objects.create(
                        orcamento=orcamento,
                        usuario=request.user,
                        acao='Orçamento atualizado',
                        observacao='Dados do orçamento foram alterados'
                    )

                    messages.success(request, f'Orçamento {orcamento.numero} atualizado com sucesso!')
                    return redirect('producao:orcamento_compra_detail', pk=orcamento.pk)

            except Exception as e:
                logger.error(f"Erro ao atualizar orçamento: {str(e)}")
                messages.error(request, f'Erro ao atualizar orçamento: {str(e)}')
        else:
            if itens_validos == 0:
                messages.error(request, 'Adicione pelo menos um item válido ao orçamento.')
            else:
                messages.error(request, 'Erro ao atualizar orçamento. Verifique os dados informados.')
    else:
        form = OrcamentoCompraForm(instance=orcamento)
        formset = ItemOrcamentoCompraFormSet(instance=orcamento)

    context = {
        'form': form,
        'formset': formset,
        'orcamento': orcamento,
        'title': f'Editar Orçamento {orcamento.numero}'
    }

    return render(request, 'producao/orcamentos/orcamento_compra_form.html', context)


@login_required
def orcamento_compra_delete(request, pk):
    """Excluir orçamento de compra"""
    orcamento = get_object_or_404(OrcamentoCompra, pk=pk)

    # Verificar se pode ser excluído
    if orcamento.status not in ['rascunho', 'cotando']:
        messages.error(request, f'Orçamento {orcamento.numero} não pode ser excluído no status atual: {orcamento.get_status_display()}.')
        return redirect('producao:orcamento_compra_detail', pk=pk)

    if request.method == 'POST':
        try:
            numero = orcamento.numero
            with transaction.atomic():
                # Excluir orçamento (cascata exclui itens e histórico)
                orcamento.delete()

            messages.success(request, f'Orçamento {numero} excluído com sucesso!')
            return redirect('producao:orcamento_compra_list')

        except Exception as e:
            messages.error(request, f'Erro ao excluir orçamento: {str(e)}')
            return redirect('producao:orcamento_compra_detail', pk=pk)

    return render(request, 'producao/orcamentos/orcamento_compra_delete.html', {'orcamento': orcamento})


@login_required
def orcamento_compra_alterar_status(request, pk):
    """Alterar status do orçamento"""
    orcamento = get_object_or_404(OrcamentoCompra, pk=pk)

    if request.method == 'POST':
        form = AlterarStatusOrcamentoForm(request.POST, instance=orcamento)

        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, f'Status do orçamento alterado para "{orcamento.get_status_display()}".')
            return redirect('producao:orcamento_compra_detail', pk=pk)
    else:
        form = AlterarStatusOrcamentoForm(instance=orcamento)

    context = {
        'form': form,
        'orcamento': orcamento
    }

    return render(request, 'producao/orcamentos/orcamento_compra_alterar_status.html', context)


@login_required
def orcamento_compra_duplicar(request, pk):
    """Duplicar orçamento de compra"""
    orcamento_original = get_object_or_404(OrcamentoCompra, pk=pk)

    try:
        with transaction.atomic():
            # Criar novo orçamento
            novo_orcamento = OrcamentoCompra(
                titulo=f"{orcamento_original.titulo} (Cópia)",
                prioridade=orcamento_original.prioridade,
                comprador_responsavel=orcamento_original.comprador_responsavel,
                solicitante=orcamento_original.solicitante,
                descricao=orcamento_original.descricao,
                observacoes=orcamento_original.observacoes,
                observacoes_internas=f"Duplicado do orçamento {orcamento_original.numero}",
                criado_por=request.user,
                atualizado_por=request.user
            )
            novo_orcamento.save()

            # Copiar requisições
            novo_orcamento.requisicoes.set(orcamento_original.requisicoes.all())

            # Copiar itens
            for item_original in orcamento_original.itens.all():
                ItemOrcamentoCompra.objects.create(
                    orcamento=novo_orcamento,
                    produto=item_original.produto,
                    quantidade=item_original.quantidade,
                    valor_unitario_estimado=item_original.valor_unitario_estimado,
                    fornecedor=item_original.fornecedor,
                    valor_unitario_cotado=item_original.valor_unitario_cotado,
                    prazo_entrega=item_original.prazo_entrega,
                    observacoes=item_original.observacoes,
                    observacoes_cotacao=item_original.observacoes_cotacao
                )

            # Recalcular valores
            novo_orcamento.calcular_valores()
            novo_orcamento.save(update_fields=['valor_total_estimado', 'valor_total_cotado'])

            # Registrar no histórico
            HistoricoOrcamentoCompra.objects.create(
                orcamento=novo_orcamento,
                usuario=request.user,
                acao='Orçamento duplicado',
                observacao=f'Duplicado a partir do orçamento {orcamento_original.numero}'
            )

            messages.success(request, f'Orçamento duplicado com sucesso! Novo número: {novo_orcamento.numero}')
            return redirect('producao:orcamento_compra_detail', pk=novo_orcamento.pk)

    except Exception as e:
        messages.error(request, f'Erro ao duplicar orçamento: {str(e)}')
        return redirect('producao:orcamento_compra_detail', pk=pk)


@login_required
def orcamento_compra_gerar_pedido(request, pk):
    """Gerar pedido de compra a partir do orçamento"""
    orcamento = get_object_or_404(OrcamentoCompra, pk=pk)

    if not orcamento.pode_gerar_pedido:
        messages.error(request, 'Orçamento deve estar aprovado para gerar pedido de compra.')
        return redirect('producao:orcamento_compra_detail', pk=pk)

    try:
        from core.models import PedidoCompra, ItemPedidoCompra
        
        # Agrupar itens por fornecedor
        itens_por_fornecedor = {}
        for item in orcamento.itens.filter(fornecedor__isnull=False):
            if item.fornecedor not in itens_por_fornecedor:
                itens_por_fornecedor[item.fornecedor] = []
            itens_por_fornecedor[item.fornecedor].append(item)

        pedidos_criados = []

        with transaction.atomic():
            for fornecedor, itens in itens_por_fornecedor.items():
                # Criar pedido para cada fornecedor
                pedido = PedidoCompra(
                    fornecedor=fornecedor,
                    prioridade=orcamento.prioridade,
                    data_entrega_prevista=orcamento.data_necessidade,
                    observacoes=f"Gerado a partir do orçamento {orcamento.numero}",
                    observacoes_internas=f"Orçamento: {orcamento.numero} - {orcamento.titulo}",
                    criado_por=request.user,
                    atualizado_por=request.user
                )
                pedido.save()

                # Adicionar itens do fornecedor
                for item in itens:
                    ItemPedidoCompra.objects.create(
                        pedido=pedido,
                        produto=item.produto,
                        quantidade=item.quantidade,
                        valor_unitario=item.valor_unitario_cotado or item.valor_unitario_estimado or 0,
                        observacoes=item.observacoes
                    )

                # Recalcular valores do pedido
                pedido.recalcular_valores()
                pedidos_criados.append(pedido)

            # Registrar no histórico do orçamento
            HistoricoOrcamentoCompra.objects.create(
                orcamento=orcamento,
                usuario=request.user,
                acao='Pedidos gerados',
                observacao=f'Gerados {len(pedidos_criados)} pedidos de compra'
            )

            if len(pedidos_criados) == 1:
                messages.success(request, f'Pedido {pedidos_criados[0].numero} gerado com sucesso!')
                return redirect('producao:pedido_compra_detail', pk=pedidos_criados[0].pk)
            else:
                numeros = [p.numero for p in pedidos_criados]
                messages.success(request, f'Pedidos gerados com sucesso: {", ".join(numeros)}')
                return redirect('producao:pedido_compra_list')

    except Exception as e:
        messages.error(request, f'Erro ao gerar pedido de compra: {str(e)}')
        return redirect('producao:orcamento_compra_detail', pk=pk)