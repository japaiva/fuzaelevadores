# producao/urls.py - URLS CORRIGIDAS

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
    
    # Matérias-Primas
    path('materias-primas/', views.materiaprima_list, name='materiaprima_list'),
    path('materias-primas/nova/', views.materiaprima_create, name='materiaprima_create'),
    path('materias-primas/<uuid:pk>/editar/', views.materiaprima_update, name='materiaprima_update'),
    path('materias-primas/<uuid:pk>/excluir/', views.materiaprima_delete, name='materiaprima_delete'),
    path('materias-primas/<uuid:pk>/toggle-status/', views.materiaprima_toggle_status, name='materiaprima_toggle_status'),
    path('materias-primas/<uuid:pk>/', views.materiaprima_detail, name='materiaprima_detail'),
    
    # Produtos Intermediários
    path('produtos-intermediarios/', views.produto_intermediario_list, name='produto_intermediario_list'),
    path('produtos-intermediarios/novo/', views.produto_intermediario_create, name='produto_intermediario_create'),
    path('produtos-intermediarios/<uuid:pk>/editar/', views.produto_intermediario_update, name='produto_intermediario_update'),
    path('produtos-intermediarios/<uuid:pk>/excluir/', views.produto_intermediario_delete, name='produto_intermediario_delete'),
    path('produtos-intermediarios/<uuid:pk>/toggle-status/', views.produto_intermediario_toggle_status, name='produto_intermediario_toggle_status'),
    
    # Produtos Acabados
    path('produtos-acabados/', views.produto_acabado_list, name='produto_acabado_list'),
    path('produtos-acabados/novo/', views.produto_acabado_create, name='produto_acabado_create'),
    path('produtos-acabados/<uuid:pk>/editar/', views.produto_acabado_update, name='produto_acabado_update'),
    path('produtos-acabados/<uuid:pk>/excluir/', views.produto_acabado_delete, name='produto_acabado_delete'),
    path('produtos-acabados/<uuid:pk>/toggle-status/', views.produto_acabado_toggle_status, name='produto_acabado_toggle_status'),
    
    # PEDIDOS DE COMPRA - URLS CORRIGIDAS
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
    
    # APIs AJAX
    path('api/subgrupos/', views.get_subgrupos_by_grupo, name='api_subgrupos'),
    path('api/produto-codigo/', views.get_info_produto_codigo, name='api_produto_codigo'),
    path('api/produto-info/', views.api_produto_info, name='api_produto_info'),
    path('api/fornecedor/<int:fornecedor_id>/produtos/', views.api_fornecedor_produtos, name='api_fornecedor_produtos'),
    
    # Relatórios
    path('relatorios/estoque-baixo/', views.relatorio_estoque_baixo, name='relatorio_estoque_baixo'),
    path('relatorios/produtos-sem-fornecedor/', views.relatorio_produtos_sem_fornecedor, name='relatorio_produtos_sem_fornecedor'),
    path('relatorios/producao/', views.relatorio_producao, name='relatorio_producao'),
]