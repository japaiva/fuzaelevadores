# vendedor/urls.py - VERSÃO CORRIGIDA FINAL

from django.urls import path
from . import views

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
    path('pedidos/', views.proposta_list, name='pedido_list'),
    path('pedidos/<uuid:pk>/', views.proposta_detail, name='pedido_detail'),
    
    # URLs alternativas (futuro)
    path('propostas/', views.proposta_list, name='proposta_list'),
    path('propostas/<uuid:pk>/', views.proposta_detail, name='proposta_detail'),
    
    # =============================================================================
    # WORKFLOW EM 3 ETAPAS - CORRIGIDO COM ROTAS DE CRIAÇÃO
    # =============================================================================
    
    # Criar nova proposta (SEM PK) 
    path('pedidos/novo/', views.proposta_step1, name='pedido_create'),
    path('pedidos/novo/step1/', views.proposta_step1, name='pedido_step1'),  # ← ADICIONADO
    path('propostas/novo/', views.proposta_step1, name='proposta_create'),
    path('propostas/novo/step1/', views.proposta_step1, name='proposta_step1'),  # ← ADICIONADO
    
    # Editar proposta existente (COM PK) - PADRÃO PEDIDO (templates atuais)
    path('pedidos/<uuid:pk>/step1/', views.proposta_step1, name='pedido_step1_edit'),
    path('pedidos/<uuid:pk>/step2/', views.proposta_step2, name='pedido_step2'),
    path('pedidos/<uuid:pk>/step3/', views.proposta_step3, name='pedido_step3'),
    
    # Editar proposta existente (COM PK) - PADRÃO PROPOSTA (futuro)
    path('propostas/<uuid:pk>/step1/', views.proposta_step1, name='proposta_step1_edit'),
    path('propostas/<uuid:pk>/step2/', views.proposta_step2, name='proposta_step2'),
    path('propostas/<uuid:pk>/step3/', views.proposta_step3, name='proposta_step3'),
    
    # =============================================================================
    # AÇÕES DAS PROPOSTAS - AMBOS OS PADRÕES
    # =============================================================================
    
    # Padrão pedido (templates atuais)
    path('pedidos/<uuid:pk>/calcular/', views.proposta_calcular, name='pedido_calcular'),
    path('pedidos/<uuid:pk>/duplicar/', views.proposta_duplicar, name='pedido_duplicar'),
    path('pedidos/<uuid:pk>/excluir/', views.proposta_delete, name='pedido_delete'),
    path('pedidos/<uuid:pk>/enviar-cliente/', views.proposta_enviar_cliente, name='pedido_enviar_cliente'),
    path('pedidos/<uuid:pk>/gerar-numero/', views.proposta_gerar_numero_definitivo, name='pedido_gerar_numero'),
    path('pedidos/<uuid:pk>/historico/', views.proposta_historico, name='pedido_historico'),
    path('pedidos/<uuid:pk>/anexos/', views.proposta_anexos, name='pedido_anexos'),
    
    # Padrão proposta (futuro)
    path('propostas/<uuid:pk>/calcular/', views.proposta_calcular, name='proposta_calcular'),
    path('propostas/<uuid:pk>/duplicar/', views.proposta_duplicar, name='proposta_duplicar'),
    path('propostas/<uuid:pk>/excluir/', views.proposta_delete, name='proposta_delete'),
    path('propostas/<uuid:pk>/enviar-cliente/', views.proposta_enviar_cliente, name='proposta_enviar_cliente'),
    path('propostas/<uuid:pk>/gerar-numero/', views.proposta_gerar_numero_definitivo, name='proposta_gerar_numero'),
    path('propostas/<uuid:pk>/historico/', views.proposta_historico, name='proposta_historico'),
    path('propostas/<uuid:pk>/anexos/', views.proposta_anexos, name='proposta_anexos'),
    
    # =============================================================================
    # GERAÇÃO DE PDFs - AMBOS OS PADRÕES
    # =============================================================================
    
    # Padrão pedido
    path('pedidos/<uuid:pk>/pdf/orcamento/', views.gerar_pdf_orcamento, name='gerar_pdf_orcamento'),
    path('pedidos/<uuid:pk>/pdf/demonstrativo/', views.gerar_pdf_demonstrativo, name='gerar_pdf_demonstrativo'),
    
    # Padrão proposta
    path('propostas/<uuid:pk>/pdf/orcamento/', views.gerar_pdf_orcamento, name='proposta_pdf_orcamento'),
    path('propostas/<uuid:pk>/pdf/demonstrativo/', views.gerar_pdf_demonstrativo, name='proposta_pdf_demonstrativo'),
    
    # =============================================================================
    # APIS AJAX - AMBOS OS PADRÕES
    # =============================================================================
    
    # APIs padrão pedido (compatibilidade com templates atuais)
    path('api/pedidos/<uuid:pk>/dados-precificacao/', views.api_dados_precificacao, name='api_dados_precificacao'),
    path('api/pedidos/<uuid:pk>/salvar-preco/', views.api_salvar_preco_negociado, name='api_salvar_preco_negociado'),
    
    # APIs padrão proposta (futuro)
    path('api/propostas/<uuid:pk>/dados-precificacao/', views.api_dados_precificacao, name='api_proposta_dados_precificacao'),
    path('api/propostas/<uuid:pk>/salvar-preco/', views.api_salvar_preco_negociado, name='api_proposta_salvar_preco'),
    
    # APIs de cliente (sem mudança)
    path('api/clientes/<int:cliente_id>/info/', views.api_cliente_info, name='api_cliente_info'),
    path('api/clientes/create/', views.cliente_create_ajax, name='cliente_create_ajax'),
    
]

# =============================================================================
# RESUMO DAS CORREÇÕES APLICADAS
# =============================================================================

"""
PROBLEMA CORRIGIDO:

1. ✅ ROTAS DE CRIAÇÃO ADICIONADAS
   - path('pedidos/novo/step1/', views.proposta_step1, name='pedido_step1')
   - Permite {% url 'vendedor:pedido_step1' %} sem argumentos

2. ✅ ROTAS DE EDIÇÃO MANTIDAS  
   - path('pedidos/<uuid:pk>/step1/', views.proposta_step1, name='pedido_step1_edit')
   - Permite {% url 'vendedor:pedido_step1_edit' pk=pedido.pk %}

3. ✅ COMPATIBILIDADE TOTAL
   - Templates podem usar qualquer padrão
   - Criação e edição funcionam separadamente
   - Sem conflitos de URL

AGORA FUNCIONA:
- /vendedor/pedidos/novo/ → Criar proposta
- /vendedor/pedidos/novo/step1/ → Step 1 de criação  
- /vendedor/pedidos/{uuid}/step1/ → Step 1 de edição
- /vendedor/pedidos/{uuid}/step2/ → Step 2
- /vendedor/pedidos/{uuid}/step3/ → Step 3
"""