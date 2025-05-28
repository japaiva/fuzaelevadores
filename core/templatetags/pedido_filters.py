# vendedor/templatetags/pedido_filters.py

from django import template
from decimal import Decimal # Você pode remover se não estiver usando Decimal em nenhum dos filtros

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplica dois valores"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide dois valores"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def sub(value, arg):
    """Subtrai dois valores"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_custom(value, arg):
    """Soma dois valores (complementa o add nativo)"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calcula percentual"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

# --- Adicione este filtro para resolver o erro 'replace' ---
@register.filter(name='replace')
def replace(value, arg):
    """
    Substitui todas as ocorrências de uma substring por outra.
    Uso: {{ minha_variavel|replace:"texto_antigo,texto_novo" }}
    """
    if isinstance(value, str) and isinstance(arg, str) and ',' in arg:
        try:
            old_text, new_text = arg.split(',', 1) # Divide apenas no primeiro vírgula
            return value.replace(old_text, new_text)
        except ValueError:
            # Caso o split não funcione como esperado
            return value
    return value # Retorna o valor original se o argumento não for válido ou não for string