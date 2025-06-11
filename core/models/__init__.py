# core/models/__init__.py

"""
Modelos do Sistema FUZA Elevadores
Organização modular dos models
"""

# Importar todos os models para disponibilizá-los
from .base import *
from .usuarios import *
from .produtos import *
from .fornecedores import *
from .clientes import *
from .elevadores import *
from .compras import *
from .parametros import *

# Lista de todos os models para facilitar importações
__all__ = [
    # Base/Choices
    'STATUS_PEDIDO_CHOICES',
    'PRIORIDADE_PEDIDO_CHOICES',
    
    # Usuários
    'Usuario',
    'PerfilUsuario',
    
    # Produtos
    'GrupoProduto',
    'SubgrupoProduto',
    'Produto',
    'EstruturaProduto',
    
    # Fornecedores
    'Fornecedor',
    'FornecedorProduto',
    
    # Clientes
    'Cliente',
    
    # Elevadores
    'EspecificacaoElevador',
    'OpcaoEspecificacao',
    'RegraComponente',
    'ComponenteDerivado',
    'SimulacaoElevador',
    
    # Compras
    'PedidoCompra',
    'ItemPedidoCompra',
    'HistoricoPedidoCompra',
    
    # Parâmetros
    'ParametrosGerais',
]