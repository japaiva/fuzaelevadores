# producao/views/dashboard.py

"""
Dashboard e páginas principais do Portal de Produção
Sistema Elevadores FUZA
"""

import logging
from django.db import models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count

from core.models import (
    Produto, Fornecedor, GrupoProduto, SubgrupoProduto
)

logger = logging.getLogger(__name__)

# =============================================================================
# PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial do Portal de Produção"""
    return render(request, 'producao/home.html')


@login_required
def dashboard(request):
    """Dashboard da produção com estatísticas básicas"""
    context = {
        'total_materias_primas': Produto.objects.filter(tipo='MP').count(),
        'total_produtos_intermediarios': Produto.objects.filter(tipo='PI').count(),
        'total_produtos_acabados': Produto.objects.filter(tipo='PA').count(),
        'total_fornecedores': Fornecedor.objects.filter(ativo=True).count(),
        'produtos_sem_estoque': Produto.objects.filter(
            controla_estoque=True,
            estoque_atual__lte=models.F('estoque_minimo')
        ).count() if Produto.objects.exists() else 0,
        'produtos_indisponiveis': Produto.objects.filter(disponivel=False).count(),
    }
    return render(request, 'producao/dashboard.html', context)


@login_required
def dashboard_analytics(request):
    """Dashboard com analytics detalhados para produção"""
    
    # Estatísticas por tipo de produto
    stats_por_tipo = Produto.objects.values('tipo').annotate(
        total=Count('id'),
        ativos=Count('id', filter=Q(status='ATIVO')),
        inativos=Count('id', filter=Q(status='INATIVO'))
    ).order_by('tipo')

    # Produtos com maior valor (mais importantes)
    produtos_importantes = Produto.objects.filter(
        preco_venda__isnull=False,
        status='ATIVO'
    ).order_by('-preco_venda')[:10]

    # Fornecedores com mais produtos
    fornecedores_principais = Fornecedor.objects.annotate(
        total_produtos=Count('produtos_fornecedor')
    ).filter(total_produtos__gt=0).order_by('-total_produtos')[:10]

    # Estatísticas de estoque por tipo
    stats_estoque = {}
    for tipo in ['MP', 'PI', 'PA']:
        produtos_tipo = Produto.objects.filter(tipo=tipo, controla_estoque=True)
        stats_estoque[tipo] = {
            'total_controlados': produtos_tipo.count(),
            'estoque_baixo': produtos_tipo.filter(
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
            'sem_estoque': produtos_tipo.filter(estoque_atual=0).count(),
        }

    context = {
        'stats_por_tipo': stats_por_tipo,
        'stats_estoque': stats_estoque,
        'produtos_importantes': produtos_importantes,
        'fornecedores_principais': fornecedores_principais,
    }

    return render(request, 'producao/dashboard_analytics.html', context)