# gestor/urls.py
from django.urls import path
from . import views
from core.views import GestorLoginView

# Importar views de producao para PI e MP
from producao.views import (
    # Matérias-Primas
    materiaprima_list as producao_mp_list,
    materiaprima_create as producao_mp_create,
    materiaprima_update as producao_mp_update,
    materiaprima_delete as producao_mp_delete,
    materiaprima_toggle_status as producao_mp_toggle_status,
    materiaprima_toggle_utilizado as producao_mp_toggle_utilizado,
    materiaprima_detail as producao_mp_detail,

    # Produtos Intermediários
    produto_intermediario_list as producao_pi_list,
    produto_intermediario_create as producao_pi_create,
    produto_intermediario_update as producao_pi_update,
    produto_intermediario_delete as producao_pi_delete,
    produto_intermediario_toggle_status as producao_pi_toggle_status,
    produto_intermediario_toggle_utilizado as producao_pi_toggle_utilizado,
    produto_intermediario_estrutura as producao_pi_estrutura,
    produto_intermediario_calcular_custo as producao_pi_calcular_custo,

    # APIs de Estrutura
    api_buscar_produtos_estrutura,
    api_adicionar_componente_estrutura,
    api_remover_componente_estrutura,
    api_editar_componente_estrutura,
    api_aplicar_custo_estrutura,
    api_listar_componentes_estrutura,

    # APIs gerais
    get_subgrupos_by_grupo,
)

app_name = 'gestor'

urlpatterns = [
    # Página de login
    path('login/', GestorLoginView.as_view(), name='login'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Parâmetros Gerais
    path('parametros/', views.parametros_gerais_view, name='parametros_gerais'),
    
    # CRUD Usuários
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_update, name='usuario_update'),
    path('usuario/<int:pk>/delete/', views.usuario_delete, name='usuario_delete'),
    path('usuarios/<int:pk>/alternar-status/', views.usuario_toggle_status, name='usuario_toggle_status'),
    
    # CRUD Grupos de Produtos
    path('grupos/', views.grupo_list, name='grupo_list'),
    path('grupos/novo/', views.grupo_create, name='grupo_create'),
    path('grupos/<int:pk>/editar/', views.grupo_update, name='grupo_update'),
    path('grupos/<int:pk>/alternar-status/', views.grupo_toggle_status, name='grupo_toggle_status'),
    
    # CRUD Subgrupos de Produtos
    path('subgrupos/', views.subgrupo_list, name='subgrupo_list'),
    path('subgrupos/novo/', views.subgrupo_create, name='subgrupo_create'),
    path('subgrupos/<int:pk>/editar/', views.subgrupo_update, name='subgrupo_update'),
    path('subgrupos/<int:pk>/alternar-status/', views.subgrupo_toggle_status, name='subgrupo_toggle_status'),

    path('grupo/<int:pk>/delete/', views.grupo_delete, name='grupo_delete'),
    path('subgrupo/<int:pk>/delete/', views.subgrupo_delete, name='subgrupo_delete'),
    
    # CRUD Fornecedores
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_create, name='fornecedor_create'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_update, name='fornecedor_update'),
    path('fornecedor/<int:pk>/delete/', views.fornecedor_delete, name='fornecedor_delete'),
    path('fornecedores/<int:pk>/alternar-status/', views.fornecedor_toggle_status, name='fornecedor_toggle_status'),
    
    # Gestão de fornecedores do produto
    path('produtos/<uuid:pk>/fornecedores/', views.produto_fornecedores, name='produto_fornecedores'),
    path('fornecedor-produto/<int:pk>/toggle/', views.fornecedor_produto_toggle, name='fornecedor_produto_toggle'),
    
    # CRUD CLIENTES
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('cliente/<int:pk>/delete/', views.cliente_delete, name='cliente_delete'),
    path('clientes/<int:pk>/alternar-status/', views.cliente_toggle_status, name='cliente_toggle_status'),
    
    # =======================================================================
    # MATÉRIAS-PRIMAS (usando views de producao)
    # =======================================================================
    path('materias-primas/', producao_mp_list, name='materiaprima_list'),
    path('materias-primas/nova/', producao_mp_create, name='materiaprima_create'),
    path('materias-primas/<uuid:pk>/', producao_mp_detail, name='materiaprima_detail'),
    path('materias-primas/<uuid:pk>/editar/', producao_mp_update, name='materiaprima_update'),
    path('materias-primas/<uuid:pk>/excluir/', producao_mp_delete, name='materiaprima_delete'),
    path('materias-primas/<uuid:pk>/toggle-status/', producao_mp_toggle_status, name='materiaprima_toggle_status'),
    path('materias-primas/<uuid:pk>/toggle-utilizado/', producao_mp_toggle_utilizado, name='materiaprima_toggle_utilizado'),

    # =======================================================================
    # PRODUTOS INTERMEDIÁRIOS (usando views de producao)
    # =======================================================================
    path('produtos-intermediarios/', producao_pi_list, name='produto_intermediario_list'),
    path('produtos-intermediarios/novo/', producao_pi_create, name='produto_intermediario_create'),
    path('produtos-intermediarios/<uuid:pk>/editar/', producao_pi_update, name='produto_intermediario_update'),
    path('produtos-intermediarios/<uuid:pk>/excluir/', producao_pi_delete, name='produto_intermediario_delete'),
    path('produtos-intermediarios/<uuid:pk>/toggle-status/', producao_pi_toggle_status, name='produto_intermediario_toggle_status'),
    path('produtos-intermediarios/<uuid:pk>/toggle-utilizado/', producao_pi_toggle_utilizado, name='produto_intermediario_toggle_utilizado'),

    # Estrutura de Componentes
    path('produtos-intermediarios/<uuid:pk>/estrutura/', producao_pi_estrutura, name='produto_intermediario_estrutura'),
    path('produtos-intermediarios/<uuid:pk>/calcular-custo/', producao_pi_calcular_custo, name='produto_intermediario_calcular_custo'),

    # =======================================================================
    # PRODUTOS ACABADOS (usando views gestor)
    # =======================================================================
    path('produtos-acabados/', views.produto_acabado_list, name='produto_acabado_list'),
    path('produtos-acabados/novo/', views.produto_acabado_create, name='produto_acabado_create'),
    path('produtos-acabados/<uuid:pk>/editar/', views.produto_acabado_update, name='produto_acabado_update'),
    path('produtos-acabados/<uuid:pk>/status/', views.produto_acabado_toggle_status, name='produto_acabado_toggle_status'),
    path('produtos-acabados/<uuid:pk>/excluir/', views.produto_acabado_delete, name='produto_acabado_delete'),

    # =======================================================================
    # APIs PARA AJAX
    # =======================================================================
    path('api/subgrupos-por-grupo/<int:grupo_id>/', views.api_subgrupos_por_grupo, name='api_subgrupos_por_grupo'),
    path('api/produto-por-codigo/<str:codigo>/', views.api_produto_por_codigo, name='api_produto_por_codigo'),

    # APIs para estrutura de componentes (redirecionam para producao)
    path('api/subgrupos/', get_subgrupos_by_grupo, name='api_subgrupos'),
    path('api/buscar-produtos-estrutura/', api_buscar_produtos_estrutura, name='api_buscar_produtos_estrutura'),
    path('api/estrutura/adicionar-componente/', api_adicionar_componente_estrutura, name='api_adicionar_componente_estrutura'),
    path('api/estrutura/componente/<int:componente_id>/remover/', api_remover_componente_estrutura, name='api_remover_componente_estrutura'),
    path('api/estrutura/componente/<int:componente_id>/editar/', api_editar_componente_estrutura, name='api_editar_componente_estrutura'),
    path('api/estrutura/produto/<uuid:produto_id>/aplicar-custo/', api_aplicar_custo_estrutura, name='api_aplicar_custo_estrutura'),
    path('api/estrutura/produto/<uuid:produto_id>/componentes/', api_listar_componentes_estrutura, name='api_listar_componentes_estrutura'),
    
    # Relatórios
    path('relatorios/estoque-baixo/', views.relatorio_estoque_baixo, name='relatorio_estoque_baixo'),
    path('relatorios/produtos-sem-fornecedor/', views.relatorio_produtos_sem_fornecedor, name='relatorio_produtos_sem_fornecedor'),
    
    # Dashboard analytics (opcional)
    path('analytics/', views.dashboard_analytics, name='dashboard_analytics'),

    # Painel de Projetos
    path('painel-projetos/', views.painel_projetos, name='painel_projetos'),
    path('painel-projetos/<uuid:pk>/', views.projeto_detail, name='projeto_detail'),

    # Financeiro - Liberação Produção
    path('liberacao-producao/', views.liberacao_producao, name='liberacao_producao'),
    path('liberacao-producao/<uuid:pk>/salvar/', views.liberacao_producao_salvar, name='liberacao_producao_salvar'),

    # === ESTOQUE - CADASTROS ===

    # Locais de Estoque
    path('locais-estoque/', views.local_estoque_list, name='local_estoque_list'),
    path('locais-estoque/novo/', views.local_estoque_create, name='local_estoque_create'),
    path('locais-estoque/<int:pk>/editar/', views.local_estoque_update, name='local_estoque_update'),
    path('locais-estoque/<int:pk>/excluir/', views.local_estoque_delete, name='local_estoque_delete'),
    path('locais-estoque/<int:pk>/alternar-status/', views.local_estoque_toggle_status, name='local_estoque_toggle_status'),

    # Tipos de Movimento de Entrada
    path('tipos-movimento-entrada/', views.tipo_movimento_entrada_list, name='tipo_movimento_entrada_list'),
    path('tipos-movimento-entrada/novo/', views.tipo_movimento_entrada_create, name='tipo_movimento_entrada_create'),
    path('tipos-movimento-entrada/<int:pk>/editar/', views.tipo_movimento_entrada_update, name='tipo_movimento_entrada_update'),
    path('tipos-movimento-entrada/<int:pk>/excluir/', views.tipo_movimento_entrada_delete, name='tipo_movimento_entrada_delete'),
    path('tipos-movimento-entrada/<int:pk>/alternar-status/', views.tipo_movimento_entrada_toggle_status, name='tipo_movimento_entrada_toggle_status'),

    # Tipos de Movimento de Saída
    path('tipos-movimento-saida/', views.tipo_movimento_saida_list, name='tipo_movimento_saida_list'),
    path('tipos-movimento-saida/novo/', views.tipo_movimento_saida_create, name='tipo_movimento_saida_create'),
    path('tipos-movimento-saida/<int:pk>/editar/', views.tipo_movimento_saida_update, name='tipo_movimento_saida_update'),
    path('tipos-movimento-saida/<int:pk>/excluir/', views.tipo_movimento_saida_delete, name='tipo_movimento_saida_delete'),
    path('tipos-movimento-saida/<int:pk>/alternar-status/', views.tipo_movimento_saida_toggle_status, name='tipo_movimento_saida_toggle_status'),

    # Movimentos de Entrada
    path('entradas/', views.movimento_entrada_list, name='movimento_entrada_list'),
    path('entradas/nova/', views.movimento_entrada_create, name='movimento_entrada_create'),
    path('entradas/<int:pk>/', views.movimento_entrada_detail, name='movimento_entrada_detail'),
    path('entradas/<int:pk>/editar/', views.movimento_entrada_update, name='movimento_entrada_update'),
    path('entradas/<int:pk>/excluir/', views.movimento_entrada_delete, name='movimento_entrada_delete'),
    path('entradas/<int:pk>/confirmar/', views.movimento_entrada_confirmar, name='movimento_entrada_confirmar'),
    path('entradas/<int:pk>/cancelar/', views.movimento_entrada_cancelar, name='movimento_entrada_cancelar'),

    # Movimentos de Saída
    path('saidas/', views.movimento_saida_list, name='movimento_saida_list'),
    path('saidas/nova/', views.movimento_saida_create, name='movimento_saida_create'),
    path('saidas/<int:pk>/', views.movimento_saida_detail, name='movimento_saida_detail'),
    path('saidas/<int:pk>/editar/', views.movimento_saida_update, name='movimento_saida_update'),
    path('saidas/<int:pk>/excluir/', views.movimento_saida_delete, name='movimento_saida_delete'),
    path('saidas/<int:pk>/confirmar/', views.movimento_saida_confirmar, name='movimento_saida_confirmar'),
    path('saidas/<int:pk>/cancelar/', views.movimento_saida_cancelar, name='movimento_saida_cancelar'),

    # Posição de Estoque
    path('posicao-estoque/', views.posicao_estoque, name='posicao_estoque'),

    # =======================================================================
    # ORDENS DE PRODUCAO (FASE 4)
    # =======================================================================
    path('ordens-producao/', views.ordem_producao_list, name='ordem_producao_list'),
    path('ordens-producao/nova/', views.ordem_producao_create, name='ordem_producao_create'),
    path('ordens-producao/<int:pk>/', views.ordem_producao_detail, name='ordem_producao_detail'),
    path('ordens-producao/<int:pk>/editar/', views.ordem_producao_update, name='ordem_producao_update'),
    path('ordens-producao/<int:pk>/excluir/', views.ordem_producao_delete, name='ordem_producao_delete'),
    path('ordens-producao/<int:pk>/liberar/', views.ordem_producao_liberar, name='ordem_producao_liberar'),
    path('ordens-producao/<int:pk>/iniciar/', views.ordem_producao_iniciar, name='ordem_producao_iniciar'),
    path('ordens-producao/<int:pk>/apontar/', views.ordem_producao_apontar, name='ordem_producao_apontar'),
    path('ordens-producao/<int:pk>/concluir/', views.ordem_producao_concluir, name='ordem_producao_concluir'),
    path('ordens-producao/<int:pk>/cancelar/', views.ordem_producao_cancelar, name='ordem_producao_cancelar'),
]