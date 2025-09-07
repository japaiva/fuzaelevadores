# vendedor/views/__init__.py - IMPORTAÇÕES MODULARES

"""
Estrutura modular das views do vendedor
Todas as importações centralizadas para compatibilidade
"""

# Dashboard e páginas principais
from .dashboard import (
    home,
    dashboard,
)

# CRUD básico de propostas (SEM filtros automáticos)
from .propostas import (
    proposta_list,
    proposta_detail, 
    proposta_delete,
)

# Workflow em 3 etapas
from .workflow import (
    proposta_step1,
    proposta_step2,
    proposta_step3,
    atualizar_portas_individuais,
    criar_portas_individuais,
)

# Ações das propostas
from .acoes import (
    proposta_calcular,
    proposta_duplicar,
    proposta_enviar_cliente,
    proposta_gerar_numero_definitivo,
    proposta_historico,
    proposta_anexos,
)

# APIs AJAX
from .apis import (
    api_dados_precificacao,
    api_salvar_preco_negociado,
    api_cliente_info,
    api_calcular_preco,
    cliente_create_ajax,
)

# PDFs e relatórios
from .contrato import (
    gerar_contrato_pdf,
)

# Views de Vistoria
from .vistoria import (
    vistoria_list,
    vistoria_proposta_detail,
    vistoria_agendar_primeira,
    vistoria_create,
    vistoria_realizar,
    vistoria_detail,
    vistoria_cancelar,
    api_vistoria_quick_status,
)

# Exports para compatibilidade
__all__ = [
    # Dashboard
    'home',
    'dashboard', 
    
    # Propostas CRUD
    'proposta_list',
    'proposta_detail',
    'proposta_delete',
    
    # Workflow
    'proposta_step1',
    'proposta_step2', 
    'proposta_step3',
    'atualizar_portas_individuais',
    'criar_portas_individuais',


    # Ações
    'proposta_calcular',
    'proposta_duplicar',
    'proposta_enviar_cliente',
    'proposta_gerar_numero_definitivo',
    'proposta_historico',
    'proposta_anexos',
    
    # APIs
    'api_dados_precificacao',
    'api_salvar_preco_negociado',
    'api_cliente_info',
    'cliente_create_ajax',
    'api_calcular_preco',


    # Vistorias
    'vistoria_list',
    'vistoria_proposta_detail',
    'vistoria_agendar_primeira',
    'vistoria_create',
    'vistoria_realizar',
    'vistoria_detail',
    'vistoria_cancelar',
    'api_vistoria_quick_status',


]