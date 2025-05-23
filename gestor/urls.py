# gestor/urls.py
from django.urls import path
from . import views
from core.views import GestorLoginView

app_name = 'gestor'

urlpatterns = [
    # Página de login
    path('login/', GestorLoginView.as_view(), name='login'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # CRUD Usuários
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_update, name='usuario_update'),
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
    
    # CRUD Fornecedores
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_create, name='fornecedor_create'),
    path('fornecedores/<int:pk>/', views.fornecedor_detail, name='fornecedor_detail'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_update, name='fornecedor_update'),
    path('fornecedores/<int:pk>/alternar-status/', views.fornecedor_toggle_status, name='fornecedor_toggle_status'),
    
    # CRUD Produtos
    path('produtos/', views.produto_list, name='produto_list'),
    path('produtos/novo/', views.produto_create, name='produto_create'),
    path('produtos/<uuid:pk>/', views.produto_detail, name='produto_detail'),
    path('produtos/<uuid:pk>/editar/', views.produto_update, name='produto_update'),
    path('produtos/<uuid:pk>/alternar-status/', views.produto_toggle_status, name='produto_toggle_status'),
    path('produtos/<uuid:pk>/alternar-disponibilidade/', views.produto_toggle_disponibilidade, name='produto_toggle_disponibilidade'),

    # Gestão de fornecedores do produto
    path('produtos/<uuid:pk>/fornecedores/', views.produto_fornecedores, name='produto_fornecedores'),
    path('fornecedor-produto/<int:pk>/toggle/', views.fornecedor_produto_toggle, name='fornecedor_produto_toggle'),
    
    # 🆕 CRUD CLIENTES
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/alternar-status/', views.cliente_toggle_status, name='cliente_toggle_status'),
    
    # APIs para AJAX
    path('api/subgrupos-por-grupo/<int:grupo_id>/', views.api_subgrupos_por_grupo, name='api_subgrupos_por_grupo'),
    path('api/produto-por-codigo/<str:codigo>/', views.api_produto_por_codigo, name='api_produto_por_codigo'),
]