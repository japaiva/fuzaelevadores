# core/models/__init__.py

"""
Importações dos models do sistema FUZA
"""

# === MODELS PRINCIPAIS ===
from .usuarios import Usuario, PerfilUsuario
from .clientes import Cliente
from .fornecedores import Fornecedor, FornecedorProduto
from .parametros import ParametrosGerais
from .produtos import GrupoProduto, SubgrupoProduto, Produto, EstruturaProduto
from .compras import PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra
from .propostas import Proposta
from .propostas2 import (
    HistoricoProposta, 
    AnexoProposta, 
    ParcelaProposta, 
    VistoriaHistorico,
    VaoPortaVistoria,
    criar_vaos_porta_automaticos
)

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
from .regras_yaml import RegraYAML, TipoRegra

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
    'EstruturaProduto',
    
    # Compras
    'PedidoCompra',
    'ItemPedidoCompra',
    'HistoricoPedidoCompra',
    
    # Propostas
    'Proposta',
    'HistoricoProposta',
    'AnexoProposta',
    'ParcelaProposta',
    'PortaPavimento',
    'VistoriaHistorico',
    
    # Medição
    'VaoPortaVistoria',
    'criar_vaos_porta_automaticos',
    
    # Produção - Fluxo Completo
    'ListaMateriais',
    'ItemListaMateriais',
    'RequisicaoCompra', 
    'ItemRequisicaoCompra',
    'OrcamentoCompra',
    'ItemOrcamentoCompra',
    'HistoricoOrcamentoCompra',
    
    # Motor de Regras
    'RegraYAML',
    'TipoRegra',
]