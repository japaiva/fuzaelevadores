# core/views/__init__.py

"""
Importações das views do sistema FUZA
Mantém apenas as views base e compartilhadas
"""

# === VIEWS BASE E COMPARTILHADAS ===
from .base import (
    home_view,
    logout_view,
    perfil,
    GestorLoginView,
    VendedorLoginView,
    ProducaoLoginView
)

from .propostas import (
    proposta_detail_base
)

# === LISTA DE EXPORTAÇÕES ===
__all__ = [
    # Views Base
    'home_view',
    'logout_view', 
    'perfil',
    'GestorLoginView',
    'VendedorLoginView',
    'ProducaoLoginView',
    
    # Views Compartilhadas de Propostas
    'proposta_detail_base',
]