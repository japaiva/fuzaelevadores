# producao/views/relatorios.py

"""
Relatórios Específicos da Produção
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.db import models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count

from core.models import Produto, Fornecedor, GrupoProduto, SubgrupoProduto

logger = logging.getLogger(__name__)

# =============================================================================
# RELATÓRIOS ESPECÍFICOS DA PRODUÇÃO
# =============================================================================

@login_required
def relatorio_estoque_baixo(request):
    """Relatório de produtos com estoque baixo"""
    produtos_estoque_baixo = Produto.objects.filter(
        controla_estoque=True,
        estoque_atual__lte=models.F('estoque_minimo'),
        status='ATIVO'
    ).select_related('grupo', 'subgrupo').order_by('codigo')

    context = {
        'produtos': produtos_estoque_baixo,
        'total': produtos_estoque_baixo.count()
    }

    return render(request, 'producao/relatorio_estoque_baixo.html', context)


@login_required
def relatorio_produtos_sem_fornecedor(request):
    """Relatório de produtos sem fornecedor principal"""
    produtos_sem_fornecedor = Produto.objects.filter(
        fornecedor_principal__isnull=True,
        status='ATIVO'
    ).select_related('grupo', 'subgrupo').order_by('codigo')

    context = {
        'produtos': produtos_sem_fornecedor,
        'total': produtos_sem_fornecedor.count()
    }

    return render(request, 'producao/relatorio_produtos_sem_fornecedor.html', context)


@login_required
def relatorio_producao(request):
    """Relatório específico da produção com estatísticas por tipo"""
    
    # Estatísticas por tipo de produto
    stats_producao = {
        'materias_primas': {
            'total': Produto.objects.filter(tipo='MP').count(),
            'ativas': Produto.objects.filter(tipo='MP', status='ATIVO').count(),
            'estoque_baixo': Produto.objects.filter(
                tipo='MP',
                controla_estoque=True,
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
        },
        'produtos_intermediarios': {
            'total': Produto.objects.filter(tipo='PI').count(),
            'ativas': Produto.objects.filter(tipo='PI', status='ATIVO').count(),
            'estoque_baixo': Produto.objects.filter(
                tipo='PI',
                controla_estoque=True,
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
        },
        'produtos_acabados': {
            'total': Produto.objects.filter(tipo='PA').count(),
            'ativas': Produto.objects.filter(tipo='PA', status='ATIVO').count(),
            'estoque_baixo': Produto.objects.filter(
                tipo='PA',
                controla_estoque=True,
                estoque_atual__lte=models.F('estoque_minimo')
            ).count(),
        }
    }

    # Estatísticas de grupos por tipo
    grupos_stats = {}
    for tipo in ['MP', 'PI', 'PA']:
        grupos_stats[tipo] = GrupoProduto.objects.filter(tipo_produto=tipo).annotate(
            total_produtos=Count('produtos'),
            produtos_ativos=Count('produtos', filter=Q(produtos__status='ATIVO'))
        ).order_by('codigo')

    # Top 10 produtos por valor de estoque
    produtos_valor_estoque = Produto.objects.filter(
        controla_estoque=True,
        estoque_atual__gt=0,
        custo_medio__gt=0,
        status='ATIVO'
    ).extra(
        select={'valor_estoque': 'estoque_atual * custo_medio'}
    ).order_by('-valor_estoque')[:10]

    context = {
        'stats_producao': stats_producao,
        'grupos_stats': grupos_stats,
        'produtos_valor_estoque': produtos_valor_estoque,
        'total_fornecedores': Fornecedor.objects.filter(ativo=True).count(),
    }

    return render(request, 'producao/relatorio_producao.html', context)