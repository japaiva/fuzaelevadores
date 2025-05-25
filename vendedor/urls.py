# vendedor/urls.py - VERSÃO 2 ETAPAS
from django.urls import path
from . import views
from core.views import VendedorLoginView

app_name = 'vendedor'

urlpatterns = [
    # Autenticação
    path('login/', VendedorLoginView.as_view(), name='login'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # CRUD Pedidos
    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedidos/<uuid:pk>/', views.pedido_detail, name='pedido_detail'),
    path('pedidos/<uuid:pk>/editar/', views.pedido_edit, name='pedido_edit'),  # Redireciona para step1
    path('pedidos/<uuid:pk>/excluir/', views.pedido_delete, name='pedido_delete'),
    path('pedidos/<uuid:pk>/duplicar/', views.pedido_duplicar, name='pedido_duplicar'),
    
    # Workflow em 2 etapas (criação + edição)
    path('pedidos/novo/cliente-elevador/', views.pedido_step1, name='pedido_step1'),  # pk=None (criação)
    path('pedidos/<uuid:pk>/cliente-elevador/', views.pedido_step1, name='pedido_step1'),  # com pk (edição)
    path('pedidos/<uuid:pk>/cabine-portas/', views.pedido_step2, name='pedido_step2'),
    
    # Ações do pedido
    path('pedidos/<uuid:pk>/alterar-status/', views.pedido_change_status, name='pedido_change_status'),
    
    # Cliente via AJAX
    path('cliente/novo/', views.cliente_create_ajax, name='cliente_create_ajax'),
    
    # Anexos
    path('pedidos/<uuid:pk>/anexos/upload/', views.pedido_anexo_upload, name='pedido_anexo_upload'),
    path('pedidos/<uuid:pk>/anexos/<int:anexo_id>/excluir/', views.pedido_anexo_delete, name='pedido_anexo_delete'),
    
    # Geração de PDFs
    path('pedidos/<uuid:pk>/pdf/orcamento/', views.gerar_pdf_orcamento, name='pdf_orcamento'),
    path('pedidos/<uuid:pk>/pdf/demonstrativo/', views.gerar_pdf_demonstrativo, name='pdf_demonstrativo'),
    
    # APIs AJAX
    path('api/cliente/<int:cliente_id>/', views.api_cliente_info, name='api_cliente_info'),
]