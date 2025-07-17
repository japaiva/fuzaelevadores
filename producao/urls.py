# producao/urls.py - URLS ATUALIZADAS SEM DETAIL PI

from django.urls import path
from . import views

app_name = 'producao'

urlpatterns = [
    # Dashboard e Home
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Fornecedores
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_create, name='fornecedor_create'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_update, name='fornecedor_update'),
    path('fornecedores/<int:pk>/excluir/', views.fornecedor_delete, name='fornecedor_delete'),
    path('fornecedores/<int:pk>/toggle-status/', views.fornecedor_toggle_status, name='fornecedor_toggle_status'),
    
    # Grupos
    path('grupos/', views.grupo_list, name='grupo_list'),
    path('grupos/novo/', views.grupo_create, name='grupo_create'),
    path('grupos/<int:pk>/editar/', views.grupo_update, name='grupo_update'),
    path('grupos/<int:pk>/excluir/', views.grupo_delete, name='grupo_delete'),
    path('grupos/<int:pk>/toggle-status/', views.grupo_toggle_status, name='grupo_toggle_status'),
    
    # Subgrupos
    path('subgrupos/', views.subgrupo_list, name='subgrupo_list'),
    path('subgrupos/novo/', views.subgrupo_create, name='subgrupo_create'),
    path('subgrupos/<int:pk>/editar/', views.subgrupo_update, name='subgrupo_update'),
    path('subgrupos/<int:pk>/excluir/', views.subgrupo_delete, name='subgrupo_delete'),
    path('subgrupos/<int:pk>/toggle-status/', views.subgrupo_toggle_status, name='subgrupo_toggle_status'),
    
    # Matérias-Primas (SEM ALTERAÇÕES)
    path('materias-primas/', views.materiaprima_list, name='materiaprima_list'),
    path('materias-primas/nova/', views.materiaprima_create, name='materiaprima_create'),
    path('materias-primas/<uuid:pk>/editar/', views.materiaprima_update, name='materiaprima_update'),
    path('materias-primas/<uuid:pk>/excluir/', views.materiaprima_delete, name='materiaprima_delete'),
    path('materias-primas/<uuid:pk>/toggle-status/', views.materiaprima_toggle_status, name='materiaprima_toggle_status'),
    path('materias-primas/<uuid:pk>/toggle-utilizado/', views.materiaprima_toggle_utilizado, name='materiaprima_toggle_utilizado'),
    path('materias-primas/<uuid:pk>/', views.materiaprima_detail, name='materiaprima_detail'),
    
    # =========================================================================
    # <<<< PRODUTOS INTERMEDIÁRIOS - SEM DETAIL, COM ESTRUTURA PRINCIPAL
    # =========================================================================
    path('produtos-intermediarios/', views.produto_intermediario_list, name='produto_intermediario_list'),
    path('produtos-intermediarios/novo/', views.produto_intermediario_create, name='produto_intermediario_create'),
    path('produtos-intermediarios/<uuid:pk>/editar/', views.produto_intermediario_update, name='produto_intermediario_update'),
    path('produtos-intermediarios/<uuid:pk>/excluir/', views.produto_intermediario_delete, name='produto_intermediario_delete'),
    path('produtos-intermediarios/<uuid:pk>/toggle-status/', views.produto_intermediario_toggle_status, name='produto_intermediario_toggle_status'),
    path('produtos-intermediarios/<uuid:pk>/toggle-utilizado/', views.produto_intermediario_toggle_utilizado, name='produto_intermediario_toggle_utilizado'),
    
    # <<<< ESTRUTURA DE COMPONENTES - FUNCIONALIDADE PRINCIPAL
    path('produtos-intermediarios/<uuid:pk>/estrutura/', 
         views.produto_intermediario_estrutura, 
         name='produto_intermediario_estrutura'),
    
    # <<<< CALCULAR CUSTO BASEADO NA ESTRUTURA
    path('produtos-intermediarios/<uuid:pk>/calcular-custo/', 
         views.produto_intermediario_calcular_custo, 
         name='produto_intermediario_calcular_custo'),
    
    # Produtos Acabados (SEM ALTERAÇÕES)
    path('produtos-acabados/', views.produto_acabado_list, name='produto_acabado_list'),
    path('produtos-acabados/novo/', views.produto_acabado_create, name='produto_acabado_create'),
    path('produtos-acabados/<uuid:pk>/editar/', views.produto_acabado_update, name='produto_acabado_update'),
    path('produtos-acabados/<uuid:pk>/excluir/', views.produto_acabado_delete, name='produto_acabado_delete'),
    path('produtos-acabados/<uuid:pk>/toggle-status/', views.produto_acabado_toggle_status, name='produto_acabado_toggle_status'),
    
    # PROPOSTAS - Visualização no Portal de Produção (SEM ALTERAÇÕES)
    path('propostas/', views.proposta_list_producao, name='proposta_list_producao'),
    path('propostas/<uuid:pk>/', views.proposta_detail_producao, name='proposta_detail_producao'),
    path('propostas/<uuid:pk>/gerar-lista-materiais/', views.gerar_lista_materiais, name='gerar_lista_materiais'),
    
    # LISTAS DE MATERIAIS (SEM ALTERAÇÕES)
    path('listas-materiais/<uuid:pk>/editar/', views.lista_materiais_edit, name='lista_materiais_edit'),
    path('listas-materiais/<uuid:pk>/aprovar/', views.lista_materiais_aprovar, name='lista_materiais_aprovar'),
    
    # REQUISIÇÕES DE COMPRA (SEM ALTERAÇÕES)
    path('requisicoes-compra/', views.requisicao_compra_list, name='requisicao_compra_list'),
    path('requisicoes-compra/nova/', views.requisicao_compra_create, name='requisicao_compra_create'),
    path('requisicoes-compra/<int:pk>/', views.requisicao_compra_detail, name='requisicao_compra_detail'),
    path('requisicoes-compra/<int:pk>/editar/', views.requisicao_compra_update, name='requisicao_compra_update'),
    path('requisicoes-compra/<int:pk>/excluir/', views.requisicao_compra_delete, name='requisicao_compra_delete'),
    path('requisicoes-compra/<int:pk>/alterar-status/', views.requisicao_compra_alterar_status, name='requisicao_compra_alterar_status'),
    path('requisicoes-compra/<int:pk>/gerar-orcamento/', views.requisicao_compra_gerar_orcamento, name='requisicao_compra_gerar_orcamento'),
    
    # ORÇAMENTOS DE COMPRA (SEM ALTERAÇÕES)
    path('orcamentos-compra/', views.orcamento_compra_list, name='orcamento_compra_list'),
    path('orcamentos-compra/novo/', views.orcamento_compra_create, name='orcamento_compra_create'),
    path('orcamentos-compra/<int:pk>/', views.orcamento_compra_detail, name='orcamento_compra_detail'),
    path('orcamentos-compra/<int:pk>/editar/', views.orcamento_compra_update, name='orcamento_compra_update'),
    path('orcamentos-compra/<int:pk>/excluir/', views.orcamento_compra_delete, name='orcamento_compra_delete'),
    path('orcamentos-compra/<int:pk>/alterar-status/', views.orcamento_compra_alterar_status, name='orcamento_compra_alterar_status'),
    path('orcamentos-compra/<int:pk>/duplicar/', views.orcamento_compra_duplicar, name='orcamento_compra_duplicar'),
    path('orcamentos-compra/<int:pk>/gerar-pedido/', views.orcamento_compra_gerar_pedido, name='orcamento_compra_gerar_pedido'),
    
    # PEDIDOS DE COMPRA (SEM ALTERAÇÕES)
    path('pedidos-compra/', views.pedido_compra_list, name='pedido_compra_list'),
    path('pedidos-compra/novo/', views.pedido_compra_create, name='pedido_compra_create'),
    path('pedidos-compra/<int:pk>/', views.pedido_compra_detail, name='pedido_compra_detail'),
    path('pedidos-compra/<int:pk>/editar/', views.pedido_compra_update, name='pedido_compra_update'),
    path('pedidos-compra/<int:pk>/excluir/', views.pedido_compra_delete, name='pedido_compra_delete'),
    path('pedidos-compra/<int:pk>/alterar-status/', views.pedido_compra_alterar_status, name='pedido_compra_alterar_status'),
    path('pedidos-compra/<int:pk>/pdf/', views.pedido_compra_gerar_pdf, name='pedido_compra_gerar_pdf'),
    path('pedidos-compra/<int:pk>/duplicar/', views.pedido_compra_duplicar, name='pedido_compra_duplicar'),
    path('pedidos-compra/<int:pk>/recebimento/', views.pedido_compra_recebimento, name='pedido_compra_recebimento'),
    path('pedidos-compra/<int:pedido_pk>/item/<int:item_pk>/receber/', views.receber_item_pedido, name='receber_item_pedido'),
    
    # CRUD DE ITENS DA LISTA DE MATERIAIS (SEM ALTERAÇÕES)
    path('listas-materiais/<int:lista_id>/itens/', 
        views.item_lista_materiais_list, 
        name='item_lista_materiais_list'),

    path('listas-materiais/<int:lista_id>/itens/novo/', 
        views.item_lista_materiais_create, 
        name='item_lista_materiais_create'),

    path('listas-materiais/<int:lista_id>/itens/<int:item_id>/editar/', 
        views.item_lista_materiais_update, 
        name='item_lista_materiais_update'),

    path('listas-materiais/<int:lista_id>/itens/<int:item_id>/excluir/', 
        views.item_lista_materiais_delete, 
        name='item_lista_materiais_delete'),

    # =========================================================================
    # <<<< APIs AJAX PARA ESTRUTURA DE COMPONENTES
    # =========================================================================
    
    # APIs existentes (SEM ALTERAÇÕES)
    path('api/subgrupos/', views.get_subgrupos_by_grupo, name='api_subgrupos'),
    path('api/produto-codigo/', views.get_info_produto_codigo, name='api_produto_codigo'),
    path('api/produto-info/', views.api_produto_info, name='api_produto_info'),
    path('api/fornecedor/<int:fornecedor_id>/produtos/', views.api_fornecedor_produtos, name='api_fornecedor_produtos'),
    path('api/buscar-produtos/', views.api_buscar_produtos, name='api_buscar_produtos'),
    
    # <<<< API PARA TIPOS DE PI
    path('api/tipo-pi-info/', views.api_tipo_pi_info, name='api_tipo_pi_info'),

    # <<<< APIS PARA ESTRUTURA DE COMPONENTES
    path('api/buscar-produtos-estrutura/', 
        views.api_buscar_produtos_estrutura, 
        name='api_buscar_produtos_estrutura'),

    path('api/estrutura/adicionar-componente/', 
        views.api_adicionar_componente_estrutura, 
        name='api_adicionar_componente_estrutura'),

    path('api/estrutura/componente/<int:componente_id>/remover/', 
        views.api_remover_componente_estrutura, 
        name='api_remover_componente_estrutura'),

    path('api/estrutura/componente/<int:componente_id>/editar/', 
        views.api_editar_componente_estrutura, 
        name='api_editar_componente_estrutura'),

    path('api/estrutura/produto/<uuid:produto_id>/aplicar-custo/', 
        views.api_aplicar_custo_estrutura, 
        name='api_aplicar_custo_estrutura'),

    # <<<< API PARA LISTAR COMPONENTES EM TEMPO REAL
    path('api/estrutura/produto/<uuid:produto_id>/componentes/', 
        views.api_listar_componentes_estrutura, 
        name='api_listar_componentes_estrutura'),
    
    # =========================================================================
    # <<<< RELATÓRIOS
    # =========================================================================
    
    # Relatórios existentes (SEM ALTERAÇÕES)
    path('relatorios/estoque-baixo/', views.relatorio_estoque_baixo, name='relatorio_estoque_baixo'),
    path('relatorios/produtos-sem-fornecedor/', views.relatorio_produtos_sem_fornecedor, name='relatorio_produtos_sem_fornecedor'),
    path('relatorios/producao/', views.relatorio_producao, name='relatorio_producao'),
    
    # <<<< RELATÓRIO PARA PI
    path('relatorios/produtos-pi-por-tipo/', views.relatorio_produtos_pi_por_tipo, name='relatorio_produtos_pi_por_tipo'),
]
