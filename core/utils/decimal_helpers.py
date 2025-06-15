# =============================================================================
# ARQUIVO: core/utils/decimal_helpers.py (CORRIGIDO)
# =============================================================================

from decimal import Decimal, InvalidOperation
from typing import Union, Any

def safe_decimal(value: Union[int, float, str, Decimal, None]) -> Decimal:
    """
    Converte qualquer valor numérico para Decimal de forma segura
    
    Args:
        value: Valor a ser convertido
        
    Returns:
        Decimal: Valor convertido ou Decimal('0') se inválido
    """
    if value is None or value == '':
        return Decimal('0')
    
    if isinstance(value, Decimal):
        return value
    
    try:
        # Converter para string primeiro para evitar problemas de precisão com float
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Converte valor para float de forma segura
    
    Args:
        value: Valor a ser convertido
        default: Valor padrão se conversão falhar
        
    Returns:
        float: Valor convertido
    """
    try:
        if value is None or value == '':
            return default
        return float(str(value).replace(',', '.'))
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """
    Converte valor para inteiro de forma segura
    
    Args:
        value: Valor a ser convertido
        default: Valor padrão se conversão falhar
        
    Returns:
        int: Valor convertido
    """
    try:
        if value is None or value == '':
            return default
        return int(float(str(value).replace(',', '.')))
    except (ValueError, TypeError):
        return default

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