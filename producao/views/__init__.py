# producao/views/__init__.py

"""
Portal de Produção - Views
Sistema Elevadores FUZA

Estrutura modular das views do portal de produção:
- dashboard: Páginas principais e estatísticas
- fornecedores: CRUD de fornecedores
- grupos: CRUD de grupos e subgrupos de produtos
- materias_primas: CRUD de matérias-primas (MP)
- produtos_intermediarios: CRUD de produtos intermediários (PI)
- produtos_acabados: CRUD de produtos acabados (PA)
- pedidos_compra: Sistema completo de pedidos de compra
- lista_materiais_itens: CRUD de itens da lista de materiais
- apis: Endpoints AJAX e APIs
- relatorios: Relatórios específicos da produção
"""

# =============================================================================
# IMPORTS DAS VIEWS MODULARES
# =============================================================================

# Dashboard e páginas principais
from .dashboard import home, dashboard, dashboard_analytics

from .orcamentos_compra import (
    # CRUD Views
    orcamento_compra_list,
    orcamento_compra_create,
    orcamento_compra_detail,
    orcamento_compra_update,
    orcamento_compra_delete,
    
    # Action Views  
    orcamento_compra_alterar_status,
    orcamento_compra_duplicar,
    orcamento_compra_gerar_pedido,
)

from .requisicoes_compra import (
    requisicao_compra_list,
    requisicao_compra_create,
    requisicao_compra_detail,
    requisicao_compra_update,
    requisicao_compra_delete,
    requisicao_compra_alterar_status,
    requisicao_compra_gerar_orcamento
)

# CRUD Fornecedores
from .fornecedores import (
    fornecedor_list, fornecedor_create, fornecedor_update,
    fornecedor_delete, fornecedor_toggle_status,
    produto_fornecedores, fornecedor_produto_toggle
)

# CRUD Grupos e Subgrupos
from .grupos import (
    grupo_list, grupo_create, grupo_update, grupo_delete, grupo_toggle_status,
    subgrupo_list, subgrupo_create, subgrupo_update, subgrupo_delete, subgrupo_toggle_status
)

# CRUD Matérias-Primas
from .materias_primas import (
    materiaprima_list, materiaprima_create, materiaprima_update,
    materiaprima_detail, materiaprima_delete, materiaprima_toggle_status
)

# CRUD Produtos Intermediários
from .produtos_intermediarios import (
    produto_intermediario_list, produto_intermediario_create, produto_intermediario_update,
    produto_intermediario_delete, produto_intermediario_toggle_status
)

# CRUD Produtos Acabados
from .produtos_acabados import (
    produto_acabado_list, produto_acabado_create, produto_acabado_update,
    produto_acabado_delete, produto_acabado_toggle_status
)

# Sistema de Pedidos de Compra
from .pedidos_compra import (
    pedido_compra_list, pedido_compra_create, pedido_compra_detail,
    pedido_compra_update, pedido_compra_delete, pedido_compra_alterar_status,
    pedido_compra_gerar_pdf, pedido_compra_duplicar,
    pedido_compra_recebimento, receber_item_pedido
)

# Propostas e Lista de Materiais
from .propostas_producao import (
    proposta_list_producao,
    proposta_detail_producao,
    gerar_lista_materiais,
    lista_materiais_edit,
    lista_materiais_aprovar,
)

# CRUD Itens da Lista de Materiais
from .lista_materiais_itens import (
    item_lista_materiais_list,
    item_lista_materiais_create,
    item_lista_materiais_update,
    item_lista_materiais_delete,
    api_buscar_produtos
)

# APIs e AJAX
from .apis import (
    get_subgrupos_by_grupo, get_info_produto_codigo,
    api_produto_info, api_fornecedor_produtos
)

# Relatórios
from .relatorios import (
    relatorio_estoque_baixo, relatorio_produtos_sem_fornecedor,
    relatorio_producao
)

# =============================================================================
# LISTA DE TODAS AS VIEWS EXPORTADAS
# =============================================================================

__all__ = [
    # Dashboard
    'home', 'dashboard', 'dashboard_analytics',

    # Orcamento Compra
    'orcamento_compra_list',
    'orcamento_compra_create', 
    'orcamento_compra_detail',
    'orcamento_compra_update',
    'orcamento_compra_delete',
    'orcamento_compra_alterar_status',
    'orcamento_compra_duplicar',
    'orcamento_compra_gerar_pedido',

    # Propostas e Lista de Materiais da Produção
    'proposta_list_producao',
    'proposta_detail_producao',
    'gerar_lista_materiais',
    'lista_materiais_edit',
    'lista_materiais_aprovar',

    # CRUD Itens da Lista de Materiais
    'item_lista_materiais_list',
    'item_lista_materiais_create',
    'item_lista_materiais_update',
    'item_lista_materiais_delete',
    'api_buscar_produtos',

    # Fornecedores
    'fornecedor_list', 'fornecedor_create', 'fornecedor_update',
    'fornecedor_delete', 'fornecedor_toggle_status',
    'produto_fornecedores', 'fornecedor_produto_toggle',

    # Requisicoes Compra
    'requisicao_compra_list', 'requisicao_compra_create', 'requisicao_compra_detail',
    'requisicao_compra_update', 'requisicao_compra_delete',
    'requisicao_compra_alterar_status', 'requisicao_compra_gerar_orcamento',

    # Grupos e Subgrupos
    'grupo_list', 'grupo_create', 'grupo_update', 'grupo_delete', 'grupo_toggle_status',
    'subgrupo_list', 'subgrupo_create', 'subgrupo_update', 'subgrupo_delete', 'subgrupo_toggle_status',
    
    # Matérias-Primas
    'materiaprima_list', 'materiaprima_create', 'materiaprima_update',
    'materiaprima_detail', 'materiaprima_delete', 'materiaprima_toggle_status',
    
    # Produtos Intermediários
    'produto_intermediario_list', 'produto_intermediario_create', 'produto_intermediario_update',
    'produto_intermediario_delete', 'produto_intermediario_toggle_status',
    
    # Produtos Acabados
    'produto_acabado_list', 'produto_acabado_create', 'produto_acabado_update',
    'produto_acabado_delete', 'produto_acabado_toggle_status',
    
    # Pedidos de Compra
    'pedido_compra_list', 'pedido_compra_create', 'pedido_compra_detail',
    'pedido_compra_update', 'pedido_compra_delete', 'pedido_compra_alterar_status',
    'pedido_compra_gerar_pdf', 'pedido_compra_duplicar',
    'pedido_compra_recebimento', 'receber_item_pedido',
    
    # APIs
    'get_subgrupos_by_grupo', 'get_info_produto_codigo',
    'api_produto_info', 'api_fornecedor_produtos',
    
    # Relatórios
    'relatorio_estoque_baixo', 'relatorio_produtos_sem_fornecedor',
    'relatorio_producao',
]