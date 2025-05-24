# vendedor/utils.py - Versão simplificada

# Re-exportar funções do core para manter compatibilidade
from core.utils.formatters import (
    extrair_especificacoes_do_pedido,
    agrupar_respostas_por_pagina,
    safe_decimal,
    safe_int
)

# Funções específicas do vendedor podem ficar aqui
def gerar_numero_pedido_sequencial():
    """Gera número sequencial para pedidos"""
    from datetime import datetime
    from .models import Pedido
    
    ano_atual = datetime.now().year
    ultimo_pedido = Pedido.objects.filter(
        numero__startswith=f'PED{ano_atual}'
    ).order_by('-numero').first()
    
    if ultimo_pedido:
        ultimo_numero = int(ultimo_pedido.numero[-4:])
        novo_numero = ultimo_numero + 1
    else:
        novo_numero = 1
    
    return f'PED{ano_atual}{novo_numero:04d}'


def validar_permissoes_vendedor(user, pedido):
    """Valida se o vendedor pode editar o pedido"""
    if not user.is_authenticated:
        return False, "Usuário não autenticado"
    
    if pedido.vendedor != user:
        return False, "Você não tem permissão para editar este pedido"
    
    if not pedido.pode_editar:
        return False, "Este pedido não pode mais ser editado"
    
    return True, ""


def calcular_estatisticas_vendedor(user):
    """Calcula estatísticas básicas do vendedor"""
    from .models import Pedido
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)
    inicio_ano = hoje.replace(month=1, day=1)
    
    stats = {
        'total': Pedido.objects.filter(vendedor=user).count(),
        'hoje': Pedido.objects.filter(vendedor=user, criado_em__date=hoje).count(),
        'mes': Pedido.objects.filter(vendedor=user, criado_em__date__gte=inicio_mes).count(),
        'ano': Pedido.objects.filter(vendedor=user, criado_em__date__gte=inicio_ano).count(),
    }
    
    # Estatísticas por status
    stats_status = list(
        Pedido.objects.filter(vendedor=user, criado_em__date__gte=inicio_ano)
        .values('status')
        .annotate(count=Count('status'))
        .order_by('-count')
    )
    
    # Estatísticas por modelo
    stats_modelo = list(
        Pedido.objects.filter(vendedor=user, criado_em__date__gte=inicio_ano)
        .values('modelo_elevador')
        .annotate(count=Count('modelo_elevador'))
        .order_by('-count')
    )
    
    return {
        'stats': stats,
        'stats_status': stats_status,
        'stats_modelo': stats_modelo
    }