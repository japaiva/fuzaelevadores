# core/templatetags/math_filters.py

from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiplica dois valores.
    Uso: {{ valor|mul:multiplicador }}
    """
    try:
        if value is None or arg is None:
            return 0
        
        # Converter para Decimal para maior precisão
        val = Decimal(str(value))
        multiplier = Decimal(str(arg))
        
        result = val * multiplier
        return float(result)
        
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def div(value, arg):
    """
    Divide dois valores.
    Uso: {{ valor|div:divisor }}
    """
    try:
        if value is None or arg is None or float(arg) == 0:
            return 0
        
        val = Decimal(str(value))
        divisor = Decimal(str(arg))
        
        result = val / divisor
        return float(result)
        
    except (ValueError, InvalidOperation, TypeError, ZeroDivisionError):
        return 0

@register.filter
def add_decimal(value, arg):
    """
    Soma dois valores com precisão decimal.
    Uso: {{ valor|add_decimal:valor2 }}
    """
    try:
        if value is None:
            value = 0
        if arg is None:
            arg = 0
        
        val = Decimal(str(value))
        addend = Decimal(str(arg))
        
        result = val + addend
        return float(result)
        
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """
    Subtrai dois valores.
    Uso: {{ valor|subtract:valor2 }}
    """
    try:
        if value is None:
            value = 0
        if arg is None:
            arg = 0
        
        val = Decimal(str(value))
        subtrahend = Decimal(str(arg))
        
        result = val - subtrahend
        return float(result)
        
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Calcula a porcentagem de um valor em relação ao total.
    Uso: {{ valor|percentage:total }}
    """
    try:
        if value is None or total is None or float(total) == 0:
            return 0
        
        val = Decimal(str(value))
        tot = Decimal(str(total))
        
        result = (val / tot) * 100
        return round(float(result), 2)
        
    except (ValueError, InvalidOperation, TypeError, ZeroDivisionError):
        return 0

@register.filter
def absolute(value):
    """
    Retorna o valor absoluto.
    Uso: {{ valor|absolute }}
    """
    try:
        if value is None:
            return 0
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def round_decimal(value, places=2):
    """
    Arredonda um valor para o número especificado de casas decimais.
    Uso: {{ valor|round_decimal:2 }}
    """
    try:
        if value is None:
            return 0
        
        val = Decimal(str(value))
        rounded = round(val, int(places))
        return float(rounded)
        
    except (ValueError, InvalidOperation, TypeError):
        return 0