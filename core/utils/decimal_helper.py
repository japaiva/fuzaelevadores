# core/utils/decimal_helpers.py - FUNÇÕES PARA CONVERSÃO SEGURA

from decimal import Decimal
from typing import Union

def safe_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
    """
    Converte qualquer valor numérico para Decimal de forma segura
    """
    if value is None:
        return Decimal('0')
    
    if isinstance(value, Decimal):
        return value
    
    # Converter para string primeiro para evitar problemas de precisão com float
    return Decimal(str(value))

def safe_multiply(a: Union[int, float, str, Decimal], b: Union[int, float, str, Decimal]) -> Decimal:
    """
    Multiplicação segura entre valores que podem ser float ou Decimal
    """
    return safe_decimal(a) * safe_decimal(b)

def safe_add(*values: Union[int, float, str, Decimal]) -> Decimal:
    """
    Soma segura de múltiplos valores
    """
    total = Decimal('0')
    for value in values:
        total += safe_decimal(value)
    return total