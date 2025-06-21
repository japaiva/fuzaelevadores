# vendedor/views/propostas.py

"""
Views para CRUD básico de propostas - listagem, detalhes e exclusão
✅ ATUALIZADA: Para usar template unificado
"""

import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import Proposta
from core.forms.propostas import PropostaFiltroForm
from core.views.propostas import proposta_detail_base

logger = logging.getLogger(__name__)


@login_required
def proposta_list(request):
    """Lista de propostas - APENAS com filtros escolhidos pelo usuário no formulário"""
    
    # 🎯 TODAS as propostas inicialmente - SEM FILTROS AUTOMÁTICOS
    propostas_list = Proposta.objects.all().select_related('cliente', 'vendedor').order_by('-criado_em')
    
    # Aplicar APENAS os filtros do formulário
    form = PropostaFiltroForm(request.GET)
    if form.is_valid():
        
        # Filtro por status (se selecionado)
        if form.cleaned_data.get('status'):
            propostas_list = propostas_list.filter(status=form.cleaned_data['status'])
        
        # Filtro por modelo de elevador (se selecionado)
        if form.cleaned_data.get('modelo_elevador'):
            propostas_list = propostas_list.filter(modelo_elevador=form.cleaned_data['modelo_elevador'])
        
        # Filtro por cliente (se selecionado)
        if form.cleaned_data.get('cliente'):
            propostas_list = propostas_list.filter(cliente=form.cleaned_data['cliente'])
        
        # Filtro por período (se selecionado)
        periodo = form.cleaned_data.get('periodo')
        if periodo:
            hoje = date.today()
            if periodo == 'hoje':
                propostas_list = propostas_list.filter(criado_em__date=hoje)
            elif periodo == 'semana':
                inicio_semana = hoje - timedelta(days=hoje.weekday())
                propostas_list = propostas_list.filter(criado_em__date__gte=inicio_semana)
            elif periodo == 'mes':
                propostas_list = propostas_list.filter(
                    criado_em__year=hoje.year,
                    criado_em__month=hoje.month
                )
            elif periodo == 'ano':
                propostas_list = propostas_list.filter(criado_em__year=hoje.year)
        
        # Filtro por vendedor (se selecionado)
        vendedor_filter = form.cleaned_data.get('vendedor')
        if vendedor_filter:
            if vendedor_filter == 'SEM_VENDEDOR':
                propostas_list = propostas_list.filter(vendedor__isnull=True)
            else:
                propostas_list = propostas_list.filter(vendedor__pk=vendedor_filter)
        
        # Filtro por validade (se selecionado)
        validade = form.cleaned_data.get('validade')
        if validade:
            hoje = date.today()
            if validade == 'vencidas':
                propostas_list = propostas_list.filter(data_validade__lt=hoje)
            elif validade == 'vence_hoje':
                propostas_list = propostas_list.filter(data_validade=hoje)
            elif validade == 'vence_semana':
                propostas_list = propostas_list.filter(
                    data_validade__lte=hoje + timedelta(days=7),
                    data_validade__gte=hoje
                )
            elif validade == 'vigentes':
                propostas_list = propostas_list.filter(data_validade__gte=hoje)
        
        # Busca textual (se preenchida)
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            propostas_list = propostas_list.filter(
                Q(numero__icontains=query) |
                Q(nome_projeto__icontains=query) |
                Q(cliente__nome__icontains=query) |
                Q(cliente__nome_fantasia__icontains=query)
            )
    
    # Paginação
    paginator = Paginator(propostas_list, 15)
    page = request.GET.get('page', 1)
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    context = {
        'pedidos': propostas,  # ✅ Usar 'pedidos' para compatibilidade com template
        'propostas': propostas,  # ✅ Manter ambos para flexibilidade
        'form': form,
        'total_propostas': propostas_list.count(),
    }
    
    return render(request, 'vendedor/pedido_list.html', context)


@login_required
def proposta_detail(request, pk):
    """
    Detalhes da proposta - Vendedor
    ✅ ATUALIZADA: Usa template unificado
    """
    # 🎯 REMOVIDO: vendedor=request.user
    proposta = get_object_or_404(Proposta, pk=pk)
    
    extra_context = {
        'is_vendedor': True,
        'is_producao': False,  # ✅ ADICIONADO: Para controlar exibição
        'base_template': 'vendedor/base_vendedor.html',
    }
    
    # ✅ MUDANÇA: Usa template unificado
    return proposta_detail_base(
        request, 
        pk, 
        'base/proposta_detail_unified.html', 
        extra_context
    )


@login_required
def proposta_delete(request, pk):
    """Excluir proposta - SEM filtro por vendedor"""
    # 🎯 REMOVIDO: vendedor=request.user
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar se pode excluir
    if proposta.status not in ['rascunho', 'simulado', 'pendente']:
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        try:
            numero = proposta.numero
            nome_projeto = proposta.nome_projeto
            
            # Log da exclusão
            logger.info(
                f"Proposta {numero} ({nome_projeto}) excluída pelo usuário {request.user.username}"
            )
            
            # Excluir (cascata remove histórico e anexos)
            proposta.delete()
            
            messages.success(request,
                f'Proposta {numero} - {nome_projeto} excluída com sucesso.'
            )
            return redirect('vendedor:pedido_list')
            
        except Exception as e:
            logger.error(f"Erro ao excluir proposta {proposta.numero}: {str(e)}")
            messages.error(request, f'Erro ao excluir proposta: {str(e)}')
            return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # ✅ Compatibilidade
        'pode_excluir': True,
    }
    
    return render(request, 'vendedor/pedido_confirm_delete.html', context)