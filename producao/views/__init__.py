# producao/views/__init__.py - ATUALIZADO COM MOTOR DE REGRAS COMPLETO

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
    requisicao_compra_toggle_status,
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
    materiaprima_detail, materiaprima_delete, materiaprima_toggle_status,
    materiaprima_toggle_utilizado
)
from .produtos_intermediarios import (
    # Views básicas CRUD
    produto_intermediario_list, produto_intermediario_create, produto_intermediario_update,
    produto_intermediario_delete, produto_intermediario_toggle_status,
    produto_intermediario_toggle_utilizado,
    
    # PRINCIPAIS: ESTRUTURA E CUSTO (já com verificações condicionais)
    produto_intermediario_estrutura,       # FUNCIONALIDADE PRINCIPAL
    produto_intermediario_calcular_custo,  # CALCULAR CUSTO AUTOMÁTICO
    
    # APIs PARA ESTRUTURA DE COMPONENTES (placeholders preparados)
    api_buscar_produtos_estrutura,         # Buscar produtos para estrutura
    api_adicionar_componente_estrutura,    # Adicionar componente AJAX
    api_remover_componente_estrutura,      # Remover componente AJAX
    api_editar_componente_estrutura,       # Editar componente AJAX
    api_aplicar_custo_estrutura,           # Aplicar custo calculado AJAX
    api_listar_componentes_estrutura,      #  Listar componentes da estrutura
    
    # API DE INFORMAÇÕES
    api_tipo_pi_info,                      # API info sobre tipos PI
    
    # RELATÓRIO
    relatorio_produtos_pi_por_tipo,        # Relatório por tipo PI
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
    pedido_compra_toggle_status, pedido_compra_gerar_pdf, pedido_compra_duplicar,
    pedido_compra_recebimento, receber_item_pedido,
    # NOVO: Controle de Saldo Requisição -> Pedido
    pedido_compra_from_requisicao,
    pedido_compra_from_orcamento,
    relatorio_saldos_requisicoes,
    requisicao_saldo_detail,
    exportar_saldos_requisicoes_excel,
)

from .relatorios_produtos import (
    relatorio_produtos_completo,
    api_subgrupos_por_grupo_relatorio
)

# Propostas e Lista de Materiais
from .propostas_producao import (
    proposta_list_producao,
    proposta_detail_producao,
    gerar_lista_materiais,
    lista_materiais_edit,
    lista_materiais_aprovar,
    upload_projeto_executivo,
    upload_projeto_elevador,
)

# CRUD Itens da Lista de Materiais
from .lista_materiais_itens import (
    item_lista_materiais_list,
    item_lista_materiais_create,
    item_lista_materiais_update,
    item_lista_materiais_delete,
    api_buscar_produtos
)

from .reclassificacao import (
    reclassificar_produto_form,
    reclassificar_produto_executar,
    api_buscar_produto_para_reclassificar,
    api_subgrupos_por_grupo_reclassificacao,
    api_preview_novo_codigo
)

# APIs e AJAX
from .apis import (
    get_subgrupos_by_grupo, get_info_produto_codigo,
    api_produto_info, api_fornecedor_produtos, api_buscar_produtos, api_grupos_todos
)

# Relatórios
from .relatorios import (
    relatorio_estoque_baixo, relatorio_produtos_sem_fornecedor,
    relatorio_producao
)

# =============================================================================
# REGRAS YAML - SISTEMA CONFIGURÁVEL SIMPLES
# =============================================================================
from .regras_yaml import (
    # CRUD Regras YAML
    regras_yaml_list,
    regra_yaml_create,
    regra_yaml_detail,
    regra_yaml_update,
    regra_yaml_delete,

    # Actions Regras YAML
    regra_yaml_toggle_status,
    regra_yaml_validar,
)

# =============================================================================
# SISTEMA DE WORKFLOW E TAREFAS
# =============================================================================
from .tarefas import (
    lista_tarefas,
    detalhes_tarefa,
    iniciar_tarefa,
    concluir_tarefa,
    cancelar_tarefa,
    contador_tarefas_pendentes,
)

# =============================================================================
# LISTA DE TODAS AS VIEWS EXPORTADAS - ATUALIZADA COM MOTOR DE REGRAS COMPLETO
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
    'upload_projeto_executivo',
    'upload_projeto_elevador',

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
    'requisicao_compra_update', 'requisicao_compra_delete', 'requisicao_compra_toggle_status',
    'requisicao_compra_alterar_status', 'requisicao_compra_gerar_orcamento',

    # Grupos e Subgrupos
    'grupo_list', 'grupo_create', 'grupo_update', 'grupo_delete', 'grupo_toggle_status',
    'subgrupo_list', 'subgrupo_create', 'subgrupo_update', 'subgrupo_delete', 'subgrupo_toggle_status',
    
    # Matérias-Primas
    'materiaprima_list', 'materiaprima_create', 'materiaprima_update',
    'materiaprima_detail', 'materiaprima_delete', 'materiaprima_toggle_status',
    'materiaprima_toggle_utilizado',
    
    # <<<< Produtos Intermediários - COM ESTRUTURA CORRIGIDA
    'produto_intermediario_list', 'produto_intermediario_create', 'produto_intermediario_update',
    'produto_intermediario_delete', 'produto_intermediario_toggle_status',
    'produto_intermediario_toggle_utilizado',
    
    # PRINCIPAIS: FUNCIONALIDADES DE ESTRUTURA (com verificações condicionais)
    'produto_intermediario_estrutura',       # FUNCIONALIDADE PRINCIPAL
    'produto_intermediario_calcular_custo',  # CALCULAR CUSTO AUTOMÁTICO
    
    # APIs PARA ESTRUTURA DE COMPONENTES (placeholders preparados)
    'api_buscar_produtos_estrutura',         # Buscar produtos para estrutura
    'api_adicionar_componente_estrutura',    # Adicionar componente AJAX
    'api_remover_componente_estrutura',      # Remover componente AJAX
    'api_editar_componente_estrutura',       # Editar componente AJAX
    'api_aplicar_custo_estrutura',           # Aplicar custo calculado AJAX
    'api_listar_componentes_estrutura',      # Listar componentes da estrutura
    
    # API DE INFORMAÇÕES
    'api_tipo_pi_info',                      # API info sobre tipos PI
    
    # RELATÓRIO
    'relatorio_produtos_pi_por_tipo',        # Relatório por tipo PI
    
    # Produtos Acabados
    'produto_acabado_list', 'produto_acabado_create', 'produto_acabado_update',
    'produto_acabado_delete', 'produto_acabado_toggle_status',
    
    # Pedidos de Compra
    'pedido_compra_list', 'pedido_compra_create', 'pedido_compra_detail',
    'pedido_compra_update', 'pedido_compra_delete', 'pedido_compra_alterar_status',
    'pedido_compra_toggle_status', 'pedido_compra_gerar_pdf', 'pedido_compra_duplicar',
    'pedido_compra_recebimento', 'receber_item_pedido',
    # Controle de Saldo Requisição -> Pedido
    'pedido_compra_from_requisicao', 'pedido_compra_from_orcamento',
    'relatorio_saldos_requisicoes', 'requisicao_saldo_detail', 'exportar_saldos_requisicoes_excel',
    
    # <<<< NOVO: RECLASSIFICAÇÃO DE PRODUTOS
    'reclassificar_produto_form',
    'reclassificar_produto_executar',
    'api_buscar_produto_para_reclassificar',
    'api_subgrupos_por_grupo_reclassificacao',
    'api_preview_novo_codigo',

    # CRUD Regras YAML
    'regras_yaml_list',
    'regra_yaml_create',
    'regra_yaml_detail',
    'regra_yaml_update',
    'regra_yaml_delete',
    
    # Actions Regras YAML
    'regra_yaml_toggle_status',
    'regra_yaml_validar',

    # Tarefas e Workflow
    'lista_tarefas',
    'detalhes_tarefa',
    'iniciar_tarefa',
    'concluir_tarefa',
    'cancelar_tarefa',
    'contador_tarefas_pendentes',

    # APIs Gerais
    'get_subgrupos_by_grupo', 'get_info_produto_codigo',
    'api_produto_info', 'api_fornecedor_produtos',
    'api_tipo_pi_info',  # API PARA TIPOS PI
    
    # Relatórios Gerais
    'relatorio_estoque_baixo', 'relatorio_produtos_sem_fornecedor',
    'relatorio_producao',
    'relatorio_produtos_pi_por_tipo',  # NOVO RELATÓRIO PI
    'relatorio_produtos_completo',      # RELATÓRIO PRODUTOS COMPLETO
    'api_subgrupos_por_grupo_relatorio', # API PARA RELATÓRIOS
]