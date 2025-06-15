# =============================================================================
# ARQUIVO: vendedor/utils.py (SIMPLIFICADO)
# =============================================================================

from datetime import datetime, timedelta
from django.db.models import Count

# Importar apenas o que precisa do core
from core.utils import safe_int


def gerar_numero_proposta_sequencial():
    """Gera número sequencial para propostas"""
    from core.models import Proposta
    
    ano_atual = datetime.now().year
    ultima_proposta = Proposta.objects.filter(
        numero__startswith=f'PROP{ano_atual}'
    ).order_by('-numero').first()
    
    if ultima_proposta:
        # Extrair número da proposta: PROP2025001 -> 001
        numero_str = ultima_proposta.numero.replace(f'PROP{ano_atual}', '')
        ultimo_numero = safe_int(numero_str)
        novo_numero = ultimo_numero + 1
    else:
        novo_numero = 1
    
    return f'PROP{ano_atual}{novo_numero:03d}'


def validar_permissoes_vendedor(user, proposta, acao='visualizar'):
    """
    Valida permissões do vendedor para ações na proposta
    
    Returns:
        tuple: (bool, str) - (tem_permissao, mensagem_erro)
    """
    if not user.is_authenticated:
        return False, "Usuário não autenticado"
    
    # Vendedor só pode acessar suas próprias propostas
    if proposta.vendedor != user:
        return False, "Você só pode acessar suas próprias propostas."
    
    if acao == 'visualizar':
        return True, ""
    
    elif acao == 'editar':
        if not proposta.pode_editar:
            return False, f"Proposta em {proposta.get_status_display()} não pode ser editada."
        return True, ""
    
    elif acao == 'excluir':
        if proposta.status not in ['rascunho', 'simulado']:
            return False, "Apenas propostas em rascunho ou simulado podem ser excluídas."
        return True, ""
    
    elif acao == 'calcular':
        if not proposta.pode_calcular():
            return False, "Proposta não tem dados suficientes para cálculo."
        return True, ""
    
    return False, "Ação não reconhecida."


def calcular_estatisticas_vendedor(user):
    """Calcula estatísticas básicas do vendedor"""
    from core.models import Proposta
    
    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)
    inicio_ano = hoje.replace(month=1, day=1)
    
    propostas = Proposta.objects.filter(vendedor=user)
    
    stats = {
        'total': propostas.count(),
        'hoje': propostas.filter(criado_em__date=hoje).count(),
        'mes': propostas.filter(criado_em__date__gte=inicio_mes).count(),
        'ano': propostas.filter(criado_em__date__gte=inicio_ano).count(),
    }
    
    # Estatísticas por status
    stats_status = list(
        propostas.filter(criado_em__date__gte=inicio_ano)
        .values('status')
        .annotate(count=Count('status'))
        .order_by('-count')
    )
    
    # Estatísticas por modelo
    stats_modelo = list(
        propostas.filter(criado_em__date__gte=inicio_ano)
        .values('modelo_elevador')
        .annotate(count=Count('modelo_elevador'))
        .order_by('-count')
    )
    
    return {
        'stats': stats,
        'stats_status': stats_status,
        'stats_modelo': stats_modelo
    }
