# vendedor/views/relatorios.py

"""
Views para relatórios e geração de PDFs
"""

import logging
from datetime import date
from collections import Counter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from core.models import Proposta

logger = logging.getLogger(__name__)


@login_required
def gerar_pdf_orcamento(request, pk):
    """Gerar PDF do orçamento"""
    # 🎯 REMOVIDO: vendedor=request.user
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.preco_venda_calculado:
        messages.warning(request, 'Execute os cálculos antes de gerar o orçamento.')
        return redirect('vendedor:pedido_detail', pk=pk)
    
    # TODO: Implementar geração de PDF
    messages.info(request, 'Geração de PDF do orçamento em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def gerar_pdf_demonstrativo(request, pk):
    """Gerar PDF do demonstrativo técnico"""
    # 🎯 REMOVIDO: vendedor=request.user
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # TODO: Implementar geração de PDF
    messages.info(request, 'Geração de PDF demonstrativo em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def relatorios_vendedor(request):
    """Relatórios e estatísticas do vendedor"""
    # Propostas do vendedor específico
    # Para relatórios pessoais, mantemos o filtro por vendedor
    propostas = Proposta.objects.filter(vendedor=request.user)
    
    stats = {
        'total': propostas.count(),
        'rascunho': propostas.filter(status='rascunho').count(),
        'pendente': propostas.filter(status='pendente').count(),  # ✅ TROCAR
        'aprovado': propostas.filter(status='aprovado').count(),
        'rejeitado': propostas.filter(status='rejeitado').count(),  # ✅ ADICIONAR
    }

    
    # Propostas por mês (últimos 12 meses)
    hoje = date.today()
    stats_mensais = []
    
    for i in range(12):
        mes = hoje.month - i
        ano = hoje.year
        
        if mes <= 0:
            mes += 12
            ano -= 1
        
        count = propostas.filter(
            criado_em__year=ano,
            criado_em__month=mes
        ).count()
        
        valor_total = sum(
            float(p.preco_negociado or p.preco_venda_calculado or 0)
            for p in propostas.filter(criado_em__year=ano, criado_em__month=mes)
        )
        
        stats_mensais.append({
            'mes': f"{mes:02d}/{ano}",
            'count': count,
            'valor': valor_total
        })
    
    stats_mensais.reverse()
    
    # Top clientes
    clientes_count = Counter()
    clientes_valor = Counter()
    
    for proposta in propostas:
        cliente_nome = proposta.cliente.nome
        clientes_count[cliente_nome] += 1
        valor = float(proposta.preco_negociado or proposta.preco_venda_calculado or 0)
        clientes_valor[cliente_nome] += valor
    
    top_clientes_count = clientes_count.most_common(5)
    top_clientes_valor = clientes_valor.most_common(5)
    
    context = {
        'stats': stats,
        'stats_mensais': stats_mensais,
        'top_clientes_count': top_clientes_count,
        'top_clientes_valor': top_clientes_valor,
        'total_propostas': propostas.count(),
    }
    
    return render(request, 'vendedor/relatorios.html', context)