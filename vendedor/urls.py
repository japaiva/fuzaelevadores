# vendedor/urls.py - SEU ARQUIVO CORRIGIDO COM AS ALTERAÇÕES

from django.urls import path
from . import views
from core.views.status import vendedor_proposta_alterar_status

app_name = 'vendedor'

urlpatterns = [
    # =============================================================================
    # DASHBOARD E PÁGINAS PRINCIPAIS
    # =============================================================================
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # =============================================================================
    # GESTÃO DE PROPOSTAS/PEDIDOS - COMPATIBILIDADE TOTAL
    # =============================================================================
    
    # URLs principais (mantém padrão atual para compatibilidade)
    path('pedidos/', views.proposta_list, name='proposta_list'),
    path('pedidos/<uuid:pk>/', views.proposta_detail, name='pedido_detail'),
    
    # URLs alternativas (futuro)
    path('propostas/', views.proposta_list, name='proposta_list'),
    path('propostas/<uuid:pk>/', views.proposta_detail, name='proposta_detail'),
    
    # =============================================================================
    # WORKFLOW EM 3 ETAPAS - CORRIGIDO COM ROTAS DE CRIAÇÃO
    # =============================================================================
    
    # Criar nova proposta (SEM PK) 
 
    path('propostas/novo/', views.proposta_step1, name='proposta_create'),
    path('propostas/novo/step1/', views.proposta_step1, name='proposta_step1'),
       
    # Editar proposta existente (COM PK) - PADRÃO PROPOSTA (futuro)
    path('propostas/<uuid:pk>/step1/', views.proposta_step1, name='proposta_step1_edit'),
    path('propostas/<uuid:pk>/step2/', views.proposta_step2, name='proposta_step2'),
    path('propostas/<uuid:pk>/step3/', views.proposta_step3, name='proposta_step3'),
    
    # =============================================================================
    # MÓDULO DE VISTORIA
    # =============================================================================
    
    # Lista principal de vistorias
    path('vistorias/', views.vistoria_list, name='vistoria_list'),
    path('vistorias/calendario/', views.vistoria_calendario, name='vistoria_calendario'),
    
    # Proposta específica para vistoria
    path('vistorias/proposta/<uuid:pk>/', views.vistoria_proposta_detail, name='vistoria_proposta_detail'),
    path('vistorias/proposta/<uuid:pk>/agendar-primeira/', views.vistoria_agendar_primeira, name='vistoria_agendar_primeira'),
    
    # CRUD de vistorias
    path('vistorias/proposta/<uuid:proposta_pk>/nova/', views.vistoria_create, name='vistoria_create'),
    path('vistorias/<int:pk>/', views.vistoria_detail, name='vistoria_detail'),
    path('vistorias/<int:pk>/realizar/', views.vistoria_realizar, name='vistoria_realizar'),
    path('vistorias/<int:pk>/cancelar/', views.vistoria_cancelar, name='vistoria_cancelar'),
    
    # APIs AJAX
    path('api/vistorias/proposta/<uuid:proposta_pk>/quick-status/', views.api_vistoria_quick_status, name='api_vistoria_quick_status'),
    
    # =============================================================================
    # AÇÕES DAS PROPOSTAS - AMBOS OS PADRÕES
    # =============================================================================
    
    path('propostas/<uuid:pk>/calcular/', views.proposta_calcular, name='proposta_calcular'),
    path('propostas/<uuid:pk>/duplicar/', views.proposta_duplicar, name='proposta_duplicar'),
    path('propostas/<uuid:pk>/excluir/', views.proposta_delete, name='proposta_delete'),
    path('propostas/<uuid:pk>/enviar-cliente/', views.proposta_enviar_cliente, name='proposta_enviar_cliente'),
    path('propostas/<uuid:pk>/gerar-numero/', views.proposta_gerar_numero_definitivo, name='proposta_gerar_numero'),
    path('propostas/<uuid:pk>/historico/', views.proposta_historico, name='proposta_historico'),
    path('propostas/<uuid:pk>/anexos/', views.proposta_anexos, name='proposta_anexos'),
    path('propostas/<uuid:pk>/status/', vendedor_proposta_alterar_status, name='proposta_status'),

    path('proposta/<uuid:pk>/contrato/', views.gerar_contrato_pdf, name='gerar_contrato_pdf'),
    
    # =============================================================================
    # APIS AJAX - AMBOS OS PADRÕES
    # =============================================================================
    
    # APIs padrão proposta (futuro)
    path('api/propostas/<uuid:pk>/dados-precificacao/', views.api_dados_precificacao, name='api_proposta_dados_precificacao'),
    path('api/propostas/<uuid:pk>/salvar-preco/', views.api_salvar_preco_negociado, name='api_proposta_salvar_preco'),
    path('api/propostas/<uuid:pk>/calcular/', views.api_calcular_preco, name='api_proposta_calcular_preco'), # Note 'calcular/' matching your log
    
    # APIs de cliente (sem mudança)
    path('api/clientes/<int:cliente_id>/info/', views.api_cliente_info, name='api_cliente_info'),
    path('api/clientes/create/', views.cliente_create_ajax, name='cliente_create_ajax'),
    

]