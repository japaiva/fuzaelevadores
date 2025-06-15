# producao/views/proposta.py - VIEWS PARA O PORTAL DE PRODUÇÃO

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.models import Proposta, HistoricoProposta
from core.views.propostas import (
    proposta_detail_base,
    api_dados_precificacao_base,
    api_salvar_preco_base,
    validar_permissoes_proposta
)
from vendedor.utils import calcular_estatisticas_producao

logger = logging.getLogger(__name__)

# =============================================================================
# PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial da produção"""
    return redirect('producao:dashboard')


@login_required
def dashboard(request):
    """Dashboard principal da produção"""
    dados_stats = calcular_estatisticas_producao(request.user)
    
    # Propostas em produção
    propostas_producao = Proposta.objects.filter(
        status__in=['aprovado', 'em_producao']
    ).select_related('cliente', 'vendedor').order_by('-criado_em')[:10]
    
    # Propostas aprovadas aguardando produção
    propostas_aguardando = Proposta.objects.filter(
        status='aprovado'
    ).select_related('cliente', 'vendedor').order_by('criado_em')[:5]
    
    context = {
        **dados_stats,
        'propostas_producao': propostas_producao,
        'propostas_aguardando': propostas_aguardando,
    }
    return render(request, 'producao/dashboard.html', context)

# =============================================================================
# GESTÃO DE PROPOSTAS
# =============================================================================

@login_required
def proposta_list(request):
    """Lista de propostas para produção"""
    # Filtrar apenas propostas relevantes para produção
    propostas_list = Proposta.objects.filter(
        status__in=['proposta_gerada', 'enviado_cliente', 'aprovado', 'em_producao', 'concluido']
    ).select_related('cliente', 'vendedor').order_by('-atualizado_em')
    
    # Filtros básicos
    status_filter = request.GET.get('status')
    vendedor_filter = request.GET.get('vendedor')
    cliente_filter = request.GET.get('cliente')
    search = request.GET.get('q')
    
    if status_filter:
        propostas_list = propostas_list.filter(status=status_filter)
    
    if vendedor_filter:
        propostas_list = propostas_list.filter(vendedor_id=vendedor_filter)
    
    if cliente_filter:
        propostas_list = propostas_list.filter(cliente_id=cliente_filter)
    
    if search:
        propostas_list = propostas_list.filter(
            Q(numero__icontains=search) |
            Q(nome_projeto__icontains=search) |
            Q(cliente__nome__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(propostas_list, 20)
    page = request.GET.get('page', 1)
    
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    # Dados para filtros
    status_choices = [
        ('proposta_gerada', 'Proposta Gerada'),
        ('enviado_cliente', 'Enviado ao Cliente'),
        ('aprovado', 'Aprovado'),
        ('em_producao', 'Em Produção'),
        ('concluido', 'Concluído'),
    ]
    
    context = {
        'propostas': propostas,
        'status_choices': status_choices,
        'status_filter': status_filter,
        'vendedor_filter': vendedor_filter,
        'cliente_filter': cliente_filter,
        'search': search,
    }
    
    return render(request, 'producao/proposta_list.html', context)


@login_required
def proposta_detail(request, pk):
    """Detalhes da proposta para produção - usando view base"""
    extra_context = {
        'is_producao': True,
        'pode_alterar_status': True,  # Produção pode alterar status
        'pode_ver_custos': True,      # Produção vê custos detalhados
    }
    return proposta_detail_base(request, pk, 'producao/proposta_detail.html', extra_context)

# =============================================================================
# GESTÃO DE STATUS
# =============================================================================

@login_required
@require_POST
def alterar_status_proposta(request, pk):
    """Alterar status da proposta (específico para produção)"""
    proposta = get_object_or_404(Proposta, pk=pk)
    
    novo_status = request.POST.get('status')
    observacao = request.POST.get('observacao', '')
    
    # Validar transições de status permitidas para produção
    transicoes_validas = {
        'aprovado': ['em_producao'],
        'em_producao': ['concluido', 'aprovado'],  # Pode voltar se necessário
        'proposta_gerada': ['em_producao'],  # Caso especial
    }
    
    status_atual = proposta.status
    
    if status_atual not in transicoes_validas:
        messages.error(request, f'Status {proposta.get_status_display()} não pode ser alterado pela produção.')
        return redirect('producao:proposta_detail', pk=pk)
    
    if novo_status not in transicoes_validas[status_atual]:
        messages.error(request, f'Transição de {proposta.get_status_display()} para {novo_status} não é válida.')
        return redirect('producao:proposta_detail', pk=pk)
    
    try:
        # Salvar status anterior
        status_anterior = proposta.status
        
        # Atualizar proposta
        proposta.status = novo_status
        proposta.atualizado_por = request.user
        proposta.save()
        
        # Registrar histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=status_anterior,
            status_novo=novo_status,
            observacao=observacao or f'Status alterado pela produção',
            usuario=request.user
        )
        
        messages.success(request, f'Status alterado para {proposta.get_status_display()} com sucesso!')
        
    except Exception as e:
        logger.error(f"Erro ao alterar status da proposta {proposta.numero}: {str(e)}")
        messages.error(request, f'Erro ao alterar status: {str(e)}')
    
    return redirect('producao:proposta_detail', pk=pk)

# =============================================================================
# APIS (REAPROVEITANDO AS BASES)
# =============================================================================

@login_required
def api_dados_precificacao(request, pk):
    """API para dados de precificação - produção pode ver todos os dados"""
    return api_dados_precificacao_base(request, pk)


@login_required
@require_POST
def api_salvar_preco_negociado(request, pk):
    """API para salvar preço - produção pode alterar se for gestor"""
    user_level = getattr(request.user, 'nivel', 'producao')
    
    if user_level not in ['gestor', 'admin']:
        return JsonResponse({
            'success': False, 
            'error': 'Apenas gestores podem alterar preços na produção'
        })
    
    return api_salvar_preco_base(request, pk)

# =============================================================================
# RELATÓRIOS DE PRODUÇÃO
# =============================================================================

@login_required
def relatorio_producao(request):
    """Relatório de produção (em desenvolvimento)"""
    # Estatísticas básicas
    total_aprovadas = Proposta.objects.filter(status='aprovado').count()
    total_em_producao = Proposta.objects.filter(status='em_producao').count()
    total_concluidas = Proposta.objects.filter(status='concluido').count()
    
    context = {
        'total_aprovadas': total_aprovadas,
        'total_em_producao': total_em_producao,
        'total_concluidas': total_concluidas,
    }
    
    return render(request, 'producao/relatorio_producao.html', context)


@login_required
def gerar_ordem_producao(request, pk):
    """Gerar ordem de produção (em desenvolvimento)"""
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if proposta.status != 'aprovado':
        messages.error(request, 'Apenas propostas aprovadas podem gerar ordem de produção.')
        return redirect('producao:proposta_detail', pk=pk)
    
    messages.info(request, 'Geração de ordem de produção em desenvolvimento.')
    return redirect('producao:proposta_detail', pk=pk)