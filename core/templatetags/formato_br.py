# core/templatetags/formato_br.py

from django import template
from core.utils.formatters import formato_numero_br, formato_moeda_br, formato_percentual_br

register = template.Library()


@register.filter
def formato_br(value):
    """
    Formata números para o padrão brasileiro (vírgula para decimal, ponto para milhares)
    """
    return formato_numero_br(value)


@register.filter
def formato_moeda(value):
    """
    Formata valores monetários no padrão brasileiro
    """
    return formato_moeda_br(value, incluir_simbolo=True)


@register.filter
def formato_percentual(value):
    """
    Formata percentuais
    """
    return formato_percentual_br(value)


@register.filter
def moeda_sem_simbolo(value):
    """
    Formata valores monetários sem o símbolo R$
    """
    return formato_moeda_br(value, incluir_simbolo=False)


@register.simple_tag
def currency(value, show_symbol=True):
    """
    Tag para formatação mais flexível de moeda
    Uso: {% currency valor %} ou {% currency valor False %}
    """
    return formato_moeda_br(value, incluir_simbolo=show_symbol)