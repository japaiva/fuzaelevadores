# core/models/__init__.py

"""
Importações dos models do sistema FUZA
"""

# === MODELS PRINCIPAIS ===
from .usuarios import Usuario, PerfilUsuario
from .clientes import Cliente
from .fornecedores import Fornecedor, FornecedorProduto
from .parametros import ParametrosGerais
from .produtos import GrupoProduto, SubgrupoProduto, Produto
from .compras import PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra
from .elevadores import (
    EspecificacaoElevador, 
    OpcaoEspecificacao, 
    RegraComponente, 
    ComponenteDerivado, 
    SimulacaoElevador
)
from .propostas import Proposta, HistoricoProposta, AnexoProposta, ParcelaProposta

# === MODELS DE PRODUÇÃO ===
from .producao import (
    ListaMateriais,
    ItemListaMateriais,
    RequisicaoCompra,
    ItemRequisicaoCompra,
    OrcamentoCompra,
    ItemOrcamentoCompra,
    HistoricoOrcamentoCompra
)

from .portas_pavimento import PortaPavimento

# === LISTA ESSENCIAL ===
__all__ = [
    # Usuários
    'Usuario',
    'PerfilUsuario',
    
    # Cadastros Base
    'Cliente',
    'Fornecedor',
    'FornecedorProduto',
    'ParametrosGerais',
    
    # Produtos
    'GrupoProduto',
    'SubgrupoProduto', 
    'Produto',
    
    # Compras
    'PedidoCompra',
    'ItemPedidoCompra',
    'HistoricoPedidoCompra',
    
    # Elevadores
    'EspecificacaoElevador',
    'OpcaoEspecificacao',
    'RegraComponente',
    'ComponenteDerivado',
    'SimulacaoElevador',
    
    # Propostas
    'Proposta',
    'HistoricoProposta',
    'AnexoProposta',
    'ParcelaProposta',
    'PortaPavimento',
    
    # Produção - Fluxo Completo
    'ListaMateriais',
    'ItemListaMateriais',
    'RequisicaoCompra', 
    'ItemRequisicaoCompra',
    'OrcamentoCompra',
    'ItemOrcamentoCompra',
    'HistoricoOrcamentoCompra',
]