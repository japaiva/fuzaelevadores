# vendedor/views.py - Versão corrigida

import logging
from datetime import datetime, timedelta
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

# IMPORTS CORRIGIDOS - usando os services do core
from core.services.dimensionamento import DimensionamentoService
from core.services.pricing import PricingService
from core.utils.formatters import extrair_especificacoes_do_pedido, agrupar_respostas_por_pagina, safe_decimal, safe_int

from .models import Pedido, HistoricoPedido, AnexoPedido
from .forms import (
    PedidoClienteForm, PedidoElevadorForm, PedidoPortasForm, 
    PedidoCabineForm, PedidoResumoForm, AnexoPedidoForm, PedidoFiltroForm
)
from .utils import validar_permissoes_vendedor, calcular_estatisticas_vendedor
from core.models import Cliente

logger = logging.getLogger(__name__)

# =============================================================================
# DASHBOARD E PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial do vendedor"""
    # Estatísticas básicas
    dados_stats = calcular_estatisticas_vendedor(request.user)
    
    # Pedidos recentes
    pedidos_recentes = Pedido.objects.filter(vendedor=request.user).order_by('-criado_em')[:5]
    
    # Status para cards
    total_pedidos = dados_stats['stats']['total']
    pedidos_abertos = Pedido.objects.filter(
        vendedor=request.user, 
        status__in=['rascunho', 'simulado', 'orcamento_gerado']
    ).count()
    pedidos_aprovados = Pedido.objects.filter(vendedor=request.user, status='aprovado').count()
    
    context = {
        'total_pedidos': total_pedidos,
        'pedidos_abertos': pedidos_abertos,
        'pedidos_aprovados': pedidos_aprovados,
        'pedidos_recentes': pedidos_recentes,
    }
    return render(request, 'vendedor/home.html', context)


@login_required
def dashboard(request):
    """Dashboard principal do vendedor"""
    # Usar função utilitária para calcular estatísticas
    dados_stats = calcular_estatisticas_vendedor(request.user)
    
    # Pedidos recentes
    pedidos_recentes = Pedido.objects.filter(vendedor=request.user).order_by('-criado_em')[:5]
    
    context = {
        **dados_stats['stats'],
        'stats_status': dados_stats['stats_status'],
        'stats_modelo': dados_stats['stats_modelo'], 
        'pedidos_recentes': pedidos_recentes,
    }
    return render(request, 'vendedor/dashboard.html', context)


# =============================================================================
# WORKFLOW DO PEDIDO = SIMULAÇÃO INTEGRADA
# =============================================================================

@login_required
def pedido_step1_cliente(request):
    """Etapa 1: Dados do Cliente - USA template pedido_create_step1.html"""
    
    if request.method == 'POST':
        form = PedidoClienteForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.vendedor = request.user
            pedido.atualizado_por = request.user
            pedido.status = 'rascunho'
            pedido.save()
            
            # Registrar no histórico
            HistoricoPedido.objects.create(
                pedido=pedido,
                status_novo='rascunho',
                observacao='Pedido criado',
                usuario=request.user
            )
            
            messages.success(request, f'Pedido {pedido.numero} criado com sucesso.')
            return redirect('vendedor:pedido_create_step2', pk=pedido.pk)
    else:
        form = PedidoClienteForm()
    
    # Buscar clientes para o select
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'vendedor/pedido_create_step1.html', {
        'form': form,
        'clientes': clientes,
    })


@login_required
def pedido_step2_elevador(request, pk):
    """Etapa 2: Dados do Elevador - USA template pedido_create_step2.html"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Validar permissões
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    if request.method == 'POST':
        form = PedidoElevadorForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            
            # Ajustar capacidade para passageiro
            if pedido.modelo_elevador == "Passageiro" and pedido.capacidade_pessoas:
                pedido.capacidade = pedido.capacidade_pessoas * 80
            
            pedido.atualizado_por = request.user
            pedido.save()
            
            return redirect('vendedor:pedido_create_step3', pk=pedido.pk)
    else:
        form = PedidoElevadorForm(instance=pedido)
    
    return render(request, 'vendedor/pedido_create_step2.html', {
        'form': form,
        'pedido': pedido,
    })


@login_required
def pedido_step3_portas(request, pk):
    """Etapa 3: Dados das Portas - USA template pedido_create_step3.html"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Validar permissões
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    if request.method == 'POST':
        form = PedidoPortasForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.atualizado_por = request.user
            pedido.save()
            
            return redirect('vendedor:pedido_create_step4', pk=pedido.pk)
    else:
        form = PedidoPortasForm(instance=pedido)
    
    return render(request, 'vendedor/pedido_create_step3.html', {
        'form': form,
        'pedido': pedido,
    })


@login_required
def pedido_step4_cabine(request, pk):
    """Etapa 4: Dados da Cabine - USA template pedido_create_step4.html"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Validar permissões
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    if request.method == 'POST':
        form = PedidoCabineForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            
            # EXECUTAR CÁLCULOS USANDO OS NOVOS SERVICES
            try:
                # Extrair especificações do pedido
                especificacoes = extrair_especificacoes_do_pedido(pedido)
                
                # Calcular dimensionamento usando o service
                dimensionamento, explicacao = DimensionamentoService.calcular_dimensionamento_completo(especificacoes)
                
                # Salvar dimensões calculadas no pedido
                if 'cab' in dimensionamento:
                    pedido.largura_cabine_calculada = dimensionamento['cab']['largura']
                    pedido.comprimento_cabine_calculado = dimensionamento['cab']['compr']
                    pedido.capacidade_cabine_calculada = dimensionamento['cab']['capacidade']
                    pedido.tracao_cabine_calculada = dimensionamento['cab']['tracao']
                
                # Salvar dados calculados
                pedido.dimensionamento_detalhado = dimensionamento
                pedido.explicacao_calculo = explicacao
                
                # Calcular custo base (temporário - depois implementar componentes)
                custo_base = 15000.0  # Valor base temporário
                
                # Calcular formação de preço usando o service
                formacao_preco = PricingService.calcular_formacao_preco(custo_base, pedido.faturado_por)
                
                # Salvar valores comerciais
                pedido.custo_producao = custo_base
                pedido.preco_venda_calculado = formacao_preco['preco_sem_impostos']
                pedido.formacao_preco = formacao_preco
                
                logger.info(f"Cálculos executados com sucesso para pedido {pedido.numero}")
                
            except Exception as e:
                logger.error(f"Erro ao calcular dimensionamento para pedido {pedido.numero}: {str(e)}")
                messages.warning(request, 'Houve um problema nos cálculos. Verifique os dados inseridos.')
                # Mesmo com erro, salva o pedido para não perder os dados
            
            pedido.atualizado_por = request.user
            pedido.save()
            
            return redirect('vendedor:pedido_resumo', pk=pedido.pk)
    else:
        form = PedidoCabineForm(instance=pedido)
    
    return render(request, 'vendedor/pedido_create_step4.html', {
        'form': form,
        'pedido': pedido,
    })


@login_required
def pedido_resumo(request, pk):
    """Etapa 5: Resumo Final - USA template pedido_resumo.html"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Extrair especificações para exibição usando as funções do core
    especificacoes = extrair_especificacoes_do_pedido(pedido)
    especificacoes_agrupadas = agrupar_respostas_por_pagina(especificacoes)
    
    # Usar dados já calculados e salvos no pedido
    dimensionamento = pedido.dimensionamento_detalhado or {}
    formacao_preco = pedido.formacao_preco or {}
    
    # Preparar grupos de componentes (vazio por enquanto)
    grupos = {}
    componentes = pedido.componentes_calculados or {}
    
    # Se não tiver formação de preço, calcular uma básica
    if not formacao_preco and pedido.custo_producao:
        formacao_preco = PricingService.calcular_formacao_preco(
            float(pedido.custo_producao), 
            pedido.faturado_por
        )
    
    context = {
        'pedido': pedido,
        'respostas': especificacoes,
        'respostas_agrupadas': especificacoes_agrupadas,
        'dimensionamento': dimensionamento,
        'explicacao': pedido.explicacao_calculo or '',
        'componentes': componentes,
        'grupos': grupos,
        'custo_total': pedido.custo_producao or 0,
        'formacao_preco': formacao_preco,
        'user_level': getattr(request.user, 'nivel', 'vendedor'),
    }
    
    return render(request, 'vendedor/pedido_resumo.html', context)


@login_required
def finalizar_pedido(request, pk):
    """Finalizar pedido após o resumo"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    if request.method == 'POST':
        # Aplicar desconto se fornecido
        desconto = safe_decimal(request.POST.get('desconto_aplicado', 0))
        if desconto and desconto > 0:
            pedido.percentual_desconto = desconto
            
            # Recalcular preço final se tiver formação de preço
            if pedido.formacao_preco and pedido.preco_venda_calculado:
                preco_original = float(pedido.preco_venda_calculado)
                novo_preco = preco_original * (1 - desconto / 100)
                
                # Recalcular formação de preço usando o service
                nova_formacao = PricingService.recalcular_com_desconto(
                    pedido.formacao_preco, 
                    novo_preco
                )
                pedido.formacao_preco = nova_formacao
                pedido.preco_venda_final = novo_preco
        else:
            pedido.preco_venda_final = pedido.preco_venda_calculado
        
        # Verificar se precisa aprovação (desconto acima da alçada)
        alcada_desconto = pedido.formacao_preco.get('alcada_desconto', 5.0) if pedido.formacao_preco else 5.0
        
        if desconto > alcada_desconto:
            pedido.status = 'orcamento_gerado'  # Aguarda aprovação
            messages.info(request, f'Pedido {pedido.numero} gerado e enviado para aprovação devido ao desconto aplicado.')
        else:
            pedido.status = 'simulado'
            messages.success(request, f'Pedido {pedido.numero} finalizado com sucesso!')
        
        # Registrar no histórico
        HistoricoPedido.objects.create(
            pedido=pedido,
            status_anterior='rascunho',
            status_novo=pedido.status,
            observacao='Pedido finalizado após simulação',
            usuario=request.user
        )
        
        pedido.atualizado_por = request.user
        pedido.save()
        
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    return redirect('vendedor:pedido_resumo', pk=pk)


# =============================================================================
# GESTÃO DE PEDIDOS
# =============================================================================

@login_required
def pedido_list(request):
    """Lista de pedidos do vendedor"""
    pedidos_list = Pedido.objects.filter(vendedor=request.user).select_related('cliente').order_by('-criado_em')
    
    # Aplicar filtros
    form = PedidoFiltroForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('status'):
            pedidos_list = pedidos_list.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            pedidos_list = pedidos_list.filter(
                Q(numero__icontains=query) |
                Q(nome_projeto__icontains=query) |
                Q(cliente__nome__icontains=query)
            )
    
    # Paginação
    paginator = Paginator(pedidos_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        pedidos = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        pedidos = paginator.page(1)
    
    context = {
        'pedidos': pedidos,
        'form': form,
    }
    return render(request, 'vendedor/pedido_list.html', context)


@login_required
def pedido_detail(request, pk):
    """Detalhes do pedido"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Histórico do pedido
    historico = pedido.historico.all()[:10]
    
    # Anexos do pedido
    anexos = pedido.anexos.all().order_by('-enviado_em')
    
    context = {
        'pedido': pedido,
        'historico': historico,
        'anexos': anexos,
    }
    return render(request, 'vendedor/pedido_detail.html', context)


@login_required
def pedido_edit(request, pk):
    """Editar pedido existente"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    # Redirecionar para o primeiro passo da edição
    return redirect('vendedor:pedido_create_step2', pk=pedido.pk)


@login_required
def pedido_delete(request, pk):
    """Excluir pedido (apenas rascunhos)"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    if pedido.status != 'rascunho':
        messages.error(request, 'Apenas pedidos em rascunho podem ser excluídos.')
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    if request.method == 'POST':
        numero = pedido.numero
        pedido.delete()
        messages.success(request, f'Pedido {numero} excluído com sucesso.')
        return redirect('vendedor:pedido_list')
    
    return render(request, 'vendedor/pedido_confirm_delete.html', {'pedido': pedido})


@login_required
def pedido_duplicar(request, pk):
    """Duplicar pedido existente"""
    pedido_original = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Criar uma cópia do pedido
    pedido_copia = Pedido.objects.get(pk=pedido_original.pk)
    pedido_copia.pk = None  # Remove o ID para criar novo
    pedido_copia.numero = None  # Será gerado automaticamente
    pedido_copia.status = 'rascunho'
    pedido_copia.nome_projeto = f"Cópia de {pedido_original.nome_projeto}"
    pedido_copia.atualizado_por = request.user
    pedido_copia.save()
    
    messages.success(request, f'Pedido duplicado com sucesso. Novo número: {pedido_copia.numero}')
    return redirect('vendedor:pedido_edit', pk=pedido_copia.pk)


# =============================================================================
# GERAÇÃO DE PDFs - TEMPORÁRIO (depois mover para core)
# =============================================================================

@login_required
def gerar_pdf_orcamento(request, pk):
    """Gerar PDF do orçamento"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    messages.info(request, 'Geração de PDF em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def gerar_pdf_demonstrativo(request, pk):
    """Gerar PDF da proposta técnica"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Verificar permissão para dados técnicos
    if getattr(request.user, 'nivel', 'vendedor') not in ['admin', 'engenharia']:
        messages.error(request, 'Você não tem permissão para acessar dados técnicos.')
        return redirect('vendedor:pedido_detail', pk=pk)
    
    messages.info(request, 'Geração de PDF em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


# =============================================================================
# APIs AJAX
# =============================================================================

@login_required
def api_cliente_info(request, cliente_id):
    """API para retornar informações do cliente"""
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'nome_fantasia': cliente.nome_fantasia,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'endereco_completo': cliente.endereco_completo,
                'tipo_pessoa': cliente.get_tipo_pessoa_display(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def api_pedido_stats(request):
    """API para estatísticas do vendedor"""
    try:
        dados_stats = calcular_estatisticas_vendedor(request.user)
        
        return JsonResponse({
            'success': True,
            'stats': dados_stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# Views temporárias para evitar erros 404
@login_required
def pedido_change_status(request, pk):
    messages.info(request, 'Funcionalidade em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required  
def pedido_anexo_upload(request, pk):
    messages.info(request, 'Funcionalidade em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def pedido_anexo_delete(request, pk, anexo_id):
    messages.info(request, 'Funcionalidade em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)