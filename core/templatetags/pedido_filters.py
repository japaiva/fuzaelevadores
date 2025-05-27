# vendedor/templatetags/pedido_filters.py

from django import template
from decimal import Decimal

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