# producao/views/pedidos_compra.py

"""
Sistema Completo de Pedidos de Compra - CORRIGIDO
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
    PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra,
    Fornecedor, Produto, OrcamentoCompra, ItemOrcamentoCompra,
    RequisicaoCompra, ItemRequisicaoCompra
)
from core.forms import (
    PedidoCompraForm, ItemPedidoCompraFormSet, PedidoCompraFiltroForm,
    AlterarStatusPedidoForm
)

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD PEDIDOS DE COMPRA
# =============================================================================

@login_required
def pedido_compra_list(request):
    """Lista de pedidos de compra com filtros"""
    pedidos_list = PedidoCompra.objects.select_related(
        'fornecedor', 'criado_por'
    ).prefetch_related('itens').order_by('-data_emissao')

    # Aplicar filtros
    form_filtros = PedidoCompraFiltroForm(request.GET)
    if form_filtros.is_valid():
        data = form_filtros.cleaned_data

        if data.get('fornecedor'):
            pedidos_list = pedidos_list.filter(fornecedor=data['fornecedor'])

        if data.get('status'):
            pedidos_list = pedidos_list.filter(status=data['status'])

        if data.get('prioridade'):
            pedidos_list = pedidos_list.filter(prioridade=data['prioridade'])

        if data.get('data_inicio'):
            pedidos_list = pedidos_list.filter(data_emissao__date__gte=data['data_inicio'])

        if data.get('data_fim'):
            pedidos_list = pedidos_list.filter(data_emissao__date__lte=data['data_fim'])

        if data.get('q'):
            query = data['q']
            pedidos_list = pedidos_list.filter(
                Q(numero__icontains=query) |
                Q(fornecedor__razao_social__icontains=query) |
                Q(fornecedor__nome_fantasia__icontains=query) |
                Q(observacoes__icontains=query)
            )

    # Paginação
    paginator = Paginator(pedidos_list, 15)
    page = request.GET.get('page', 1)

    try:
        pedidos = paginator.page(page)
    except:
        pedidos = paginator.page(1)

    context = {
        'pedidos': pedidos,
        'form_filtros': form_filtros,
        'total_pedidos': pedidos_list.count(),
    }

    return render(request, 'producao/pedidos/pedido_compra_list.html', context)


@login_required
def pedido_compra_create(request):
    """Criar novo pedido de compra"""

    if request.method == 'POST':

        form = PedidoCompraForm(request.POST)
        formset = ItemPedidoCompraFormSet(request.POST)

        # --- LOGGING MELHORADO ---
        logger.debug(f"POST request recebido para criar pedido.")
        logger.debug(f"Form principal válido: {form.is_valid()}")
        if not form.is_valid():
            logger.debug(f"Erros no form principal: {form.errors}")

        logger.debug(f"Formset de itens válido: {formset.is_valid()}")
        if not formset.is_valid():
            logger.debug(f"Erros no formset (non_form_errors): {formset.non_form_errors()}")
            for i, item_form in enumerate(formset):
                if item_form.errors:
                    logger.debug(f"Erros no item {i}: {item_form.errors}")

        # --- VERIFICAÇÃO CORRIGIDA DE ITENS VÁLIDOS ---
        itens_validos_e_nao_deletados = 0
        for form_item in formset:
            # Verificar se o form é válido E não está marcado para exclusão E tem dados relevantes
            if (form_item.is_valid() and 
                not form_item.cleaned_data.get('DELETE', False) and
                form_item.cleaned_data.get('produto') is not None and
                form_item.cleaned_data.get('quantidade') is not None and
                form_item.cleaned_data.get('valor_unitario') is not None and
                form_item.cleaned_data.get('quantidade') > 0 and
                form_item.cleaned_data.get('valor_unitario') > 0):
                itens_validos_e_nao_deletados += 1

        logger.debug(f"Total de itens válidos e não deletados: {itens_validos_e_nao_deletados}")

        if form.is_valid() and formset.is_valid() and itens_validos_e_nao_deletados > 0:
            try:
                with transaction.atomic():
                    # Criar pedido
                    pedido = form.save(commit=False)
                    pedido.criado_por = request.user
                    pedido.atualizado_por = request.user
                    pedido.save()

                    # Usar o método save() do formset que é mais confiável
                    itens_salvos = formset.save(commit=False)
                    
                    # Processar itens salvos
                    for item in itens_salvos:
                        item.pedido = pedido
                        if not item.unidade and item.produto:
                            item.unidade = item.produto.unidade_medida
                        item.valor_total = item.quantidade * item.valor_unitario
                        item.save()
                        logger.debug(f"Novo item salvo: {item.produto.codigo if item.produto else 'N/A'}")

                    # Processar itens marcados para exclusão (se houver)
                    for item_deletado in formset.deleted_objects:
                        item_deletado.delete()
                        logger.debug(f"Item excluído: {item_deletado.pk}")

                    # Recalcular valores do pedido
                    pedido.recalcular_valores()

                    # Registrar no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=request.user,
                        acao='Pedido criado',
                        observacao=f'Pedido criado com {len(itens_salvos)} itens'
                    )

                    messages.success(request, f'Pedido {pedido.numero} criado com sucesso!')
                    return redirect('producao:pedido_compra_detail', pk=pedido.pk)

            except Exception as e:
                logger.error(f"Erro ao criar pedido: {str(e)}", exc_info=True)
                messages.error(request, f'Erro ao criar pedido: {str(e)}')
        else:
            # Mensagens de erro mais específicas
            if not form.is_valid():
                messages.error(request, 'Erro nos dados do pedido. Verifique os campos obrigatórios.')
            elif not formset.is_valid():
                messages.error(request, 'Erro nos itens do pedido. Verifique os dados informados.')
            elif itens_validos_e_nao_deletados == 0:
                messages.error(request, 'Adicione pelo menos um item válido ao pedido.')
            
            # Log dos erros específicos do formset para debug
            for i, item_form in enumerate(formset):
                if item_form.errors:
                    logger.debug(f"Erros específicos no form {i}: {item_form.errors}")
    else:
        form = PedidoCompraForm()
        formset = ItemPedidoCompraFormSet()

    # Coletar mapeamento produto -> requisições para filtro dinâmico
    produto_requisicoes = {}
    for form_item in formset:
        if hasattr(form_item, 'produto_requisicoes'):
            produto_requisicoes.update(form_item.produto_requisicoes)

    context = {
        'form': form,
        'formset': formset,
        'title': 'Novo Pedido de Compra',
        'produto_requisicoes_json': json.dumps(produto_requisicoes)
    }

    return render(request, 'producao/pedidos/pedido_compra_form.html', context)


@login_required
def pedido_compra_detail(request, pk):
    """Detalhes do pedido de compra"""
    pedido = get_object_or_404(
        PedidoCompra.objects.select_related('fornecedor', 'criado_por')
        .prefetch_related('itens__produto', 'historico__usuario'),
        pk=pk
    )

    context = {
        'pedido': pedido,
        'pode_editar': pedido.pode_editar,
        'pode_cancelar': pedido.pode_cancelar,
    }

    return render(request, 'producao/pedidos/pedido_compra_detail.html', context)


@login_required
def pedido_compra_update(request, pk):
    """Editar pedido de compra"""
    pedido = get_object_or_404(PedidoCompra, pk=pk)

    if not pedido.pode_editar:
        messages.error(request, f'Pedido {pedido.numero} não pode ser editado no status atual.')
        return redirect('producao:pedido_compra_detail', pk=pk)

    if request.method == 'POST':
        form = PedidoCompraForm(request.POST, instance=pedido)
        formset = ItemPedidoCompraFormSet(request.POST, instance=pedido)

        # --- LOGGING MELHORADO ---
        logger.debug(f"POST request recebido para atualizar pedido {pk}.")
        logger.debug(f"Form principal válido: {form.is_valid()}")
        if not form.is_valid():
            logger.debug(f"Erros no form principal: {form.errors}")

        logger.debug(f"Formset de itens válido: {formset.is_valid()}")
        if not formset.is_valid():
            logger.debug(f"Erros no formset (non_form_errors): {formset.non_form_errors()}")
            for i, item_form in enumerate(formset):
                if item_form.errors:
                    logger.debug(f"Erros no item {i}: {item_form.errors}")

        # --- VERIFICAÇÃO CORRIGIDA DE ITENS VÁLIDOS ---
        itens_validos_e_nao_deletados = 0
        for form_item in formset:
            # Verificar se o form é válido E não está marcado para exclusão E tem dados relevantes
            if (form_item.is_valid() and 
                not form_item.cleaned_data.get('DELETE', False) and
                form_item.cleaned_data.get('produto') is not None and
                form_item.cleaned_data.get('quantidade') is not None and
                form_item.cleaned_data.get('valor_unitario') is not None and
                form_item.cleaned_data.get('quantidade') > 0 and
                form_item.cleaned_data.get('valor_unitario') > 0):
                itens_validos_e_nao_deletados += 1
        
        logger.debug(f"Total de itens válidos e não deletados: {itens_validos_e_nao_deletados}")

        if form.is_valid() and formset.is_valid() and itens_validos_e_nao_deletados > 0:
            try:
                with transaction.atomic():
                    # Salvar pedido
                    pedido = form.save(commit=False)
                    pedido.atualizado_por = request.user
                    pedido.save()

                    # Usar o método save() do formset que é mais confiável
                    itens_salvos = formset.save(commit=False)
                    
                    # Processar itens salvos (novos e atualizados)
                    for item in itens_salvos:
                        item.pedido = pedido
                        if not item.unidade and item.produto:
                            item.unidade = item.produto.unidade_medida
                        item.valor_total = item.quantidade * item.valor_unitario
                        item.save()
                        logger.debug(f"Item salvo/atualizado: {item.produto.codigo if item.produto else 'N/A'}")

                    # Processar itens marcados para exclusão
                    for item_deletado in formset.deleted_objects:
                        item_deletado.delete()
                        logger.debug(f"Item excluído: {item_deletado.pk}")

                    # Recalcular valores
                    pedido.recalcular_valores()

                    # Registrar no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=request.user,
                        acao='Pedido atualizado',
                        observacao='Dados do pedido foram alterados'
                    )

                    messages.success(request, f'Pedido {pedido.numero} atualizado com sucesso!')
                    return redirect('producao:pedido_compra_detail', pk=pedido.pk)

            except Exception as e:
                logger.error(f"Erro ao atualizar pedido: {str(e)}", exc_info=True)
                messages.error(request, f'Erro ao atualizar pedido: {str(e)}')
        else:
            # Mensagens de erro mais específicas
            if not form.is_valid():
                messages.error(request, 'Erro nos dados do pedido. Verifique os campos obrigatórios.')
            elif not formset.is_valid():
                messages.error(request, 'Erro nos itens do pedido. Verifique os dados informados.')
            elif itens_validos_e_nao_deletados == 0:
                messages.error(request, 'Adicione pelo menos um item válido ao pedido.')
            
            # Log dos erros específicos do formset para debug
            for i, item_form in enumerate(formset):
                if item_form.errors:
                    logger.debug(f"Erros específicos no form {i}: {item_form.errors}")
    else:
        form = PedidoCompraForm(instance=pedido)
        formset = ItemPedidoCompraFormSet(instance=pedido)

    # Coletar mapeamento produto -> requisições para filtro dinâmico
    produto_requisicoes = {}
    for form_item in formset:
        if hasattr(form_item, 'produto_requisicoes'):
            produto_requisicoes.update(form_item.produto_requisicoes)

    context = {
        'form': form,
        'formset': formset,
        'pedido': pedido,
        'title': f'Editar Pedido {pedido.numero}',
        'produto_requisicoes_json': json.dumps(produto_requisicoes)
    }

    return render(request, 'producao/pedidos/pedido_compra_form.html', context)


@login_required
def pedido_compra_delete(request, pk):
    """Excluir pedido de compra"""
    pedido = get_object_or_404(PedidoCompra, pk=pk)

    # Verificar se pode ser excluído
    if pedido.status not in ['RASCUNHO', 'ENVIADO']:
        messages.error(request, f'Pedido {pedido.numero} não pode ser excluído no status atual: {pedido.get_status_display()}.')
        return redirect('producao:pedido_compra_detail', pk=pk)

    if request.method == 'POST':
        try:
            numero = pedido.numero
            with transaction.atomic():
                # Excluir pedido (cascata exclui itens e histórico)
                pedido.delete()

            messages.success(request, f'Pedido {numero} excluído com sucesso!')
            return redirect('producao:pedido_compra_list')

        except Exception as e:
            messages.error(request, f'Erro ao excluir pedido: {str(e)}')
            return redirect('producao:pedido_compra_detail', pk=pk)

    return render(request, 'producao/pedidos/pedido_compra_delete.html', {'pedido': pedido})


@login_required
def pedido_compra_alterar_status(request, pk):
    """Alterar status do pedido"""
    pedido = get_object_or_404(PedidoCompra, pk=pk)

    if request.method == 'POST':
        form = AlterarStatusPedidoForm(request.POST, instance=pedido)

        if form.is_valid():
            # Salvar com o usuário
            form.save(user=request.user)
            messages.success(request, f'Status do pedido alterado para "{pedido.get_status_display()}".')
            return redirect('producao:pedido_compra_detail', pk=pk)
    else:
        form = AlterarStatusPedidoForm(instance=pedido)

    context = {
        'form': form,
        'pedido': pedido
    }

    return render(request, 'producao/pedidos/pedido_compra_alterar_status.html', context)


@login_required
def pedido_compra_gerar_pdf(request, pk):
    """Gerar PDF do pedido de compra"""
    pedido = get_object_or_404(
        PedidoCompra.objects.select_related('fornecedor')
        .prefetch_related('itens__produto'),
        pk=pk
    )

    try:
        # Importar o gerador de PDF
        from core.utils.pdf_generator import gerar_pdf_pedido_compra

        # Gerar PDF
        pdf_buffer = gerar_pdf_pedido_compra(pedido)

        # Registrar no histórico
        HistoricoPedidoCompra.objects.create(
            pedido=pedido,
            usuario=request.user,
            acao='PDF gerado',
            observacao='PDF do pedido foi gerado e baixado'
        )

        # Preparar resposta
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Pedido_Compra_{pedido.numero}.pdf"'

        # Fechar buffer
        pdf_buffer.close()

        return response

    except ImportError as e:
        messages.error(request, 'Erro: Módulo reportlab não encontrado. Instale com: pip install reportlab')
        return redirect('producao:pedido_compra_detail', pk=pk)
    except AttributeError as e:
        if 'desconto_valor' in str(e):
            messages.error(request, 'Erro: Propriedade desconto_valor não encontrada no modelo PedidoCompra. Verifique o modelo.')
        else:
            messages.error(request, f'Erro de atributo: {str(e)}')
        return redirect('producao:pedido_compra_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('producao:pedido_compra_detail', pk=pk)


@login_required
def pedido_compra_duplicar(request, pk):
    """Duplicar pedido de compra"""
    pedido_original = get_object_or_404(PedidoCompra, pk=pk)

    try:
        with transaction.atomic():
            # Criar novo pedido
            novo_pedido = PedidoCompra(
                fornecedor=pedido_original.fornecedor,
                prioridade=pedido_original.prioridade,
                condicao_pagamento=pedido_original.condicao_pagamento,
                prazo_entrega=pedido_original.prazo_entrega,
                desconto_percentual=pedido_original.desconto_percentual,
                valor_frete=pedido_original.valor_frete,
                observacoes=pedido_original.observacoes,
                observacoes_internas=f"Duplicado do pedido {pedido_original.numero}",
                criado_por=request.user,
                atualizado_por=request.user
            )
            novo_pedido.save()

            # Copiar itens
            for item_original in pedido_original.itens.all():
                ItemPedidoCompra.objects.create(
                    pedido=novo_pedido,
                    produto=item_original.produto,
                    quantidade=item_original.quantidade,
                    valor_unitario=item_original.valor_unitario,
                    observacoes=item_original.observacoes
                )

            # Recalcular valores
            novo_pedido.recalcular_valores()

            # Registrar no histórico
            HistoricoPedidoCompra.objects.create(
                pedido=novo_pedido,
                usuario=request.user,
                acao='Pedido duplicado',
                observacao=f'Duplicado a partir do pedido {pedido_original.numero}'
            )

            messages.success(request, f'Pedido duplicado com sucesso! Novo número: {novo_pedido.numero}')
            return redirect('producao:pedido_compra_detail', pk=novo_pedido.pk)

    except Exception as e:
        messages.error(request, f'Erro ao duplicar pedido: {str(e)}')
        return redirect('producao:pedido_compra_detail', pk=pk)


# =============================================================================
# RECEBIMENTO DE MATERIAIS
# =============================================================================

@login_required
def pedido_compra_recebimento(request, pk):
    """Tela de recebimento de materiais"""
    pedido = get_object_or_404(
        PedidoCompra.objects.select_related('fornecedor')
        .prefetch_related('itens__produto'),
        pk=pk
    )

    if pedido.status not in ['CONFIRMADO', 'PARCIAL']:
        messages.error(request, 'Pedido deve estar confirmado para recebimento.')
        return redirect('producao:pedido_compra_detail', pk=pk)

    context = {
        'pedido': pedido,
        'itens_pendentes': pedido.itens.filter(quantidade_recebida__lt=models.F('quantidade')),
    }

    return render(request, 'producao/pedidos/pedido_compra_recebimento.html', context)


@login_required
@require_POST
def receber_item_pedido(request, pedido_pk, item_pk):
    """Receber item específico do pedido"""
    pedido = get_object_or_404(PedidoCompra, pk=pedido_pk)
    item = get_object_or_404(ItemPedidoCompra, pk=item_pk, pedido=pedido)

    try:
        data = json.loads(request.body)
        quantidade_recebida = float(data.get('quantidade', 0))

        if quantidade_recebida <= 0:
            return JsonResponse({'success': False, 'error': 'Quantidade deve ser maior que zero'})

        quantidade_pendente = item.quantidade - item.quantidade_recebida
        if quantidade_recebida > quantidade_pendente:
            return JsonResponse({
                'success': False,
                'error': f'Quantidade não pode ser maior que {quantidade_pendente}'
            })

        with transaction.atomic():
            # Atualizar item
            item.quantidade_recebida += quantidade_recebida
            item.data_recebimento = timezone.now()
            item.save()

            # Atualizar estoque do produto se controla estoque
            if item.produto.controla_estoque:
                item.produto.estoque_atual += quantidade_recebida
                item.produto.save()

            # Verificar se pedido está totalmente recebido
            itens_pendentes = pedido.itens.filter(quantidade_recebida__lt=models.F('quantidade'))

            if not itens_pendentes.exists():
                # Todos os itens foram recebidos
                pedido.status = 'RECEBIDO'
                pedido.data_entrega_real = timezone.now().date()
            elif pedido.status == 'CONFIRMADO':
                # Primeiro recebimento parcial
                pedido.status = 'PARCIAL'

            pedido.atualizado_por = request.user
            pedido.save()

            # Registrar no histórico
            HistoricoPedidoCompra.objects.create(
                pedido=pedido,
                usuario=request.user,
                acao='Item recebido',
                observacao=f'Recebido {quantidade_recebida} {item.unidade} do produto {item.produto.codigo}'
            )

        return JsonResponse({
            'success': True,
            'item_status': 'COMPLETO' if item.quantidade_recebida >= item.quantidade else 'PARCIAL',
            'pedido_status': pedido.status,
            'quantidade_recebida': float(item.quantidade_recebida),
            'quantidade_pendente': float(item.quantidade - item.quantidade_recebida)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# CRIAR PEDIDO A PARTIR DE REQUISIÇÃO
# =============================================================================

@login_required
def pedido_compra_from_requisicao(request, requisicao_pk):
    """Criar pedido de compra a partir de uma requisição"""
    requisicao = get_object_or_404(
        RequisicaoCompra.objects.select_related(
            'solicitante', 'lista_materiais__proposta'
        ).prefetch_related('itens__produto'),
        pk=requisicao_pk
    )

    if requisicao.status not in ['aberta', 'aprovada']:
        messages.error(request, 'Somente requisições abertas ou aprovadas podem gerar pedidos.')
        return redirect('producao:requisicao_compra_detail', pk=requisicao_pk)

    if request.method == 'POST':
        form = PedidoCompraForm(request.POST)

        # IDs dos itens selecionados
        itens_selecionados = request.POST.getlist('itens_selecionados')

        if not itens_selecionados:
            messages.error(request, 'Selecione pelo menos um item da requisição.')
        elif form.is_valid():
            try:
                with transaction.atomic():
                    # Criar pedido
                    pedido = form.save(commit=False)
                    pedido.criado_por = request.user
                    pedido.atualizado_por = request.user
                    pedido.save()

                    # Criar itens do pedido vinculando à requisição
                    itens_criados = 0
                    for item_req_id in itens_selecionados:
                        item_req = ItemRequisicaoCompra.objects.get(id=item_req_id)

                        # Verificar saldo disponível
                        saldo = item_req.quantidade_saldo
                        if saldo <= 0:
                            continue  # Pula itens sem saldo

                        # Quantidade do pedido (pode ser parcial)
                        quantidade_pedido = request.POST.get(f'quantidade_{item_req_id}', saldo)
                        quantidade_pedido = float(quantidade_pedido)

                        # Limitar ao saldo disponível
                        if quantidade_pedido > saldo:
                            quantidade_pedido = saldo

                        if quantidade_pedido > 0:
                            ItemPedidoCompra.objects.create(
                                pedido=pedido,
                                produto=item_req.produto,
                                item_requisicao=item_req,  # VINCULO COM REQUISIÇÃO
                                quantidade=quantidade_pedido,
                                valor_unitario=item_req.valor_unitario_estimado or 0,
                                unidade=item_req.unidade,
                                observacoes=item_req.observacoes
                            )
                            itens_criados += 1

                    if itens_criados == 0:
                        messages.error(request, 'Nenhum item válido foi adicionado ao pedido.')
                        pedido.delete()
                        return redirect('producao:requisicao_compra_detail', pk=requisicao_pk)

                    # Recalcular valores
                    pedido.recalcular_valores()

                    # Registrar no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=request.user,
                        acao='Pedido criado de requisição',
                        observacao=f'Criado a partir da requisição {requisicao.numero} com {itens_criados} itens'
                    )

                    messages.success(request, f'Pedido {pedido.numero} criado com sucesso!')
                    return redirect('producao:pedido_compra_detail', pk=pedido.pk)

            except Exception as e:
                logger.error(f"Erro ao criar pedido de requisição: {str(e)}", exc_info=True)
                messages.error(request, f'Erro ao criar pedido: {str(e)}')
    else:
        # Formulário inicial
        form = PedidoCompraForm(initial={
            'prioridade': requisicao.prioridade,
            'prazo_entrega': 15,
        })

    context = {
        'form': form,
        'requisicao': requisicao,
        'title': f'Criar Pedido da Requisição {requisicao.numero}'
    }

    return render(request, 'producao/pedidos/pedido_from_requisicao.html', context)


# =============================================================================
# CRIAR PEDIDO A PARTIR DE ORÇAMENTO (SE NECESSÁRIO NO FUTURO)
# =============================================================================

@login_required
def pedido_compra_from_orcamento(request, orcamento_pk):
    """Criar pedido de compra a partir de um orçamento aprovado"""
    orcamento = get_object_or_404(
        OrcamentoCompra.objects.select_related('fornecedor')
        .prefetch_related('itens__produto', 'requisicoes'),
        pk=orcamento_pk
    )

    if orcamento.status != 'aprovado':
        messages.error(request, 'Somente orçamentos aprovados podem gerar pedidos.')
        return redirect('producao:orcamento_compra_detail', pk=orcamento_pk)

    if request.method == 'POST':
        form = PedidoCompraForm(request.POST)

        # IDs dos itens selecionados
        itens_selecionados = request.POST.getlist('itens_selecionados')

        if not itens_selecionados:
            messages.error(request, 'Selecione pelo menos um item do orçamento.')
            form = PedidoCompraForm(initial={
                'fornecedor': orcamento.fornecedor,
                'prioridade': 'NORMAL',
            })
        elif form.is_valid():
            try:
                with transaction.atomic():
                    # Criar pedido
                    pedido = form.save(commit=False)
                    pedido.orcamento = orcamento
                    pedido.fornecedor = orcamento.fornecedor
                    pedido.criado_por = request.user
                    pedido.atualizado_por = request.user
                    pedido.save()

                    # Criar itens do pedido vinculando às requisições
                    itens_criados = 0
                    for item_orc_id in itens_selecionados:
                        item_orc = ItemOrcamentoCompra.objects.get(id=item_orc_id)

                        # Buscar item de requisição correspondente
                        item_req = ItemRequisicaoCompra.objects.filter(
                            requisicao__in=orcamento.requisicoes.all(),
                            produto=item_orc.produto
                        ).first()

                        quantidade_item = request.POST.get(f'quantidade_{item_orc_id}', item_orc.quantidade)

                        ItemPedidoCompra.objects.create(
                            pedido=pedido,
                            produto=item_orc.produto,
                            item_requisicao=item_req,  # VINCULO COM REQUISIÇÃO
                            quantidade=float(quantidade_item),
                            valor_unitario=item_orc.valor_unitario_cotado or item_orc.valor_unitario_estimado,
                            unidade=item_orc.unidade,
                            observacoes=item_orc.observacoes
                        )
                        itens_criados += 1

                    # Recalcular valores
                    pedido.recalcular_valores()

                    # Registrar no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=request.user,
                        acao='Pedido criado de orçamento',
                        observacao=f'Criado a partir do orçamento {orcamento.numero} com {itens_criados} itens'
                    )

                    messages.success(request, f'Pedido {pedido.numero} criado com sucesso a partir do orçamento!')
                    return redirect('producao:pedido_compra_detail', pk=pedido.pk)

            except Exception as e:
                logger.error(f"Erro ao criar pedido de orçamento: {str(e)}", exc_info=True)
                messages.error(request, f'Erro ao criar pedido: {str(e)}')
    else:
        # Formulário inicial com dados do orçamento
        form = PedidoCompraForm(initial={
            'fornecedor': orcamento.fornecedor,
            'prioridade': 'NORMAL',
            'condicao_pagamento': orcamento.condicao_pagamento,
            'prazo_entrega': 15,
        })

    context = {
        'form': form,
        'orcamento': orcamento,
        'title': f'Criar Pedido do Orçamento {orcamento.numero}'
    }

    return render(request, 'producao/pedidos/pedido_from_orcamento.html', context)


# =============================================================================
# RELATÓRIOS DE SALDO
# =============================================================================

@login_required
def relatorio_saldos_requisicoes(request):
    """Relatório geral de saldo de requisições"""

    # Filtrar requisições (exceto canceladas e rascunho) que necessitam acompanhamento de saldo
    requisicoes = RequisicaoCompra.objects.filter(
        status__in=['aberta', 'cotando', 'orcada', 'aprovada']
    ).select_related(
        'solicitante', 'lista_materiais__proposta'
    ).prefetch_related(
        'itens__produto', 'itens__itens_pedido__pedido'
    ).order_by('-data_requisicao')

    # Aplicar filtros
    status_filtro = request.GET.get('status')
    if status_filtro:
        requisicoes = requisicoes.filter(status=status_filtro)

    prioridade_filtro = request.GET.get('prioridade')
    if prioridade_filtro:
        requisicoes = requisicoes.filter(prioridade=prioridade_filtro)

    busca = request.GET.get('q')
    if busca:
        requisicoes = requisicoes.filter(
            Q(numero__icontains=busca) |
            Q(lista_materiais__proposta__numero__icontains=busca) |
            Q(solicitante__username__icontains=busca)
        )

    # Filtrar apenas com saldo pendente (PADRÃO: DESATIVADO - mostra todas)
    mostrar_apenas_pendentes = request.GET.get('pendentes') == 'true'

    # Filtro por status de atendimento
    status_atendimento_filtro = request.GET.get('status_atendimento')

    requisicoes_com_info = []
    for req in requisicoes:
        percentual = req.percentual_atendido_geral
        status_atend = req.status_atendimento_geral

        # Se filtro "apenas pendentes" ativado, não mostrar completos
        if mostrar_apenas_pendentes and status_atend == 'completo':
            continue

        # Se filtro de status de atendimento ativado, filtrar
        if status_atendimento_filtro and status_atend != status_atendimento_filtro:
            continue

        requisicoes_com_info.append({
            'requisicao': req,
            'percentual_atendido': percentual,
            'status_atendimento': status_atend,
            'total_itens': req.get_total_itens(),
            'pedidos_vinculados': req.get_pedidos_vinculados().count()
        })

    # Paginação
    paginator = Paginator(requisicoes_com_info, 20)
    page = request.GET.get('page', 1)
    try:
        requisicoes_page = paginator.page(page)
    except:
        requisicoes_page = paginator.page(1)

    context = {
        'requisicoes': requisicoes_page,
        'total_requisicoes': len(requisicoes_com_info),
        'status_filtro': status_filtro,
        'prioridade_filtro': prioridade_filtro,
        'busca': busca,
        'mostrar_apenas_pendentes': mostrar_apenas_pendentes,
        'status_atendimento_filtro': status_atendimento_filtro,
    }

    return render(request, 'producao/relatorios/relatorio_saldos.html', context)


@login_required
def requisicao_saldo_detail(request, pk):
    """Detalhamento de saldo de uma requisição específica"""
    requisicao = get_object_or_404(
        RequisicaoCompra.objects.select_related(
            'solicitante', 'lista_materiais__proposta'
        ).prefetch_related(
            'itens__produto',
            'itens__itens_pedido__pedido__fornecedor'
        ),
        pk=pk
    )

    # Montar informações de cada item
    itens_info = []
    for item in requisicao.itens.all():
        pedidos_vinculados = item.itens_pedido.select_related('pedido__fornecedor').all()

        itens_info.append({
            'item': item,
            'saldo': item.quantidade_saldo,
            'percentual': item.percentual_atendido,
            'status': item.status_atendimento,
            'pedidos': pedidos_vinculados
        })

    # Pedidos vinculados à requisição
    pedidos_vinculados = requisicao.get_pedidos_vinculados()

    context = {
        'requisicao': requisicao,
        'itens_info': itens_info,
        'pedidos_vinculados': pedidos_vinculados,
        'percentual_geral': requisicao.percentual_atendido_geral,
        'status_geral': requisicao.status_atendimento_geral,
    }

    return render(request, 'producao/requisicoes/requisicao_saldo_detail.html', context)