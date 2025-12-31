# producao/urls.py - COMPLETO COM MOTOR DE REGRAS

from django.urls import path
from . import views

# Ordens de Producao ainda importadas do gestor (sera migrado depois)
from gestor.views import (
    ordem_producao_list, ordem_producao_create, ordem_producao_detail,
    ordem_producao_update, ordem_producao_delete,
    ordem_producao_liberar, ordem_producao_iniciar,
    ordem_producao_apontar, ordem_producao_concluir, ordem_producao_cancelar,
)

app_name = 'producao'

urlpatterns = [
    # Dashboard e Home
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/analytics/', views.dashboard_analytics, name='dashboard_analytics'),

    # =======================================================================
    # ✅ TAREFAS E WORKFLOW
    # =======================================================================
    path('tarefas/', views.lista_tarefas, name='tarefas'),
    path('tarefas/<int:tarefa_id>/', views.detalhes_tarefa, name='tarefa_detalhes'),
    path('tarefas/<int:tarefa_id>/iniciar/', views.iniciar_tarefa, name='tarefa_iniciar'),
    path('tarefas/<int:tarefa_id>/concluir/', views.concluir_tarefa, name='tarefa_concluir'),
    path('tarefas/<int:tarefa_id>/cancelar/', views.cancelar_tarefa, name='tarefa_cancelar'),
    path('api/tarefas/contador/', views.contador_tarefas_pendentes, name='tarefas_contador'),

    # =======================================================================
    # 🔧 MOTOR DE REGRAS YAML
    # =======================================================================
    path('regras-yaml/', views.regras_yaml_list, name='regras_yaml_list'),
    path('regras-yaml/nova/', views.regra_yaml_create, name='regra_yaml_create'),
    path('regras-yaml/<int:pk>/', views.regra_yaml_detail, name='regra_yaml_detail'),
    path('regras-yaml/<int:pk>/editar/', views.regra_yaml_update, name='regra_yaml_update'),
    path('regras-yaml/<int:pk>/excluir/', views.regra_yaml_delete, name='regra_yaml_delete'),
    path('regras-yaml/<int:pk>/toggle-status/', views.regra_yaml_toggle_status, name='regra_yaml_toggle_status'),
    path('regras-yaml/<int:pk>/validar/', views.regra_yaml_validar, name='regra_yaml_validar'),

    # =======================================================================
    # 📐 FÓRMULAS DE CÁLCULO (Documentação)
    # =======================================================================
    path('formulas-calculo/', views.formulas_calculo, name='formulas_calculo'),

    # =======================================================================
    # 👥 FORNECEDORES
    # =======================================================================
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_create, name='fornecedor_create'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_update, name='fornecedor_update'),
    path('fornecedores/<int:pk>/excluir/', views.fornecedor_delete, name='fornecedor_delete'),
    path('fornecedores/<int:pk>/toggle-status/', views.fornecedor_toggle_status, name='fornecedor_toggle_status'),
    path('fornecedores/<int:pk>/produtos/', views.produto_fornecedores, name='produto_fornecedores'),
    path('fornecedores/<int:pk>/produtos/toggle/', views.fornecedor_produto_toggle, name='fornecedor_produto_toggle'),
    
    # =======================================================================
    # 📦 GRUPOS E SUBGRUPOS
    # =======================================================================
    path('grupos/', views.grupo_list, name='grupo_list'),
    path('grupos/novo/', views.grupo_create, name='grupo_create'),
    path('grupos/<int:pk>/editar/', views.grupo_update, name='grupo_update'),
    path('grupos/<int:pk>/excluir/', views.grupo_delete, name='grupo_delete'),
    path('grupos/<int:pk>/toggle-status/', views.grupo_toggle_status, name='grupo_toggle_status'),
    
    path('subgrupos/', views.subgrupo_list, name='subgrupo_list'),
    path('subgrupos/novo/', views.subgrupo_create, name='subgrupo_create'),
    path('subgrupos/<int:pk>/editar/', views.subgrupo_update, name='subgrupo_update'),
    path('subgrupos/<int:pk>/excluir/', views.subgrupo_delete, name='subgrupo_delete'),
    path('subgrupos/<int:pk>/toggle-status/', views.subgrupo_toggle_status, name='subgrupo_toggle_status'),
    
    # =======================================================================
    # 🏭 MATÉRIAS-PRIMAS
    # =======================================================================
    path('materias-primas/', views.materiaprima_list, name='materiaprima_list'),
    path('materias-primas/nova/', views.materiaprima_create, name='materiaprima_create'),
    path('materias-primas/<uuid:pk>/', views.materiaprima_detail, name='materiaprima_detail'),
    path('materias-primas/<uuid:pk>/editar/', views.materiaprima_update, name='materiaprima_update'),
    path('materias-primas/<uuid:pk>/excluir/', views.materiaprima_delete, name='materiaprima_delete'),
    path('materias-primas/<uuid:pk>/toggle-status/', views.materiaprima_toggle_status, name='materiaprima_toggle_status'),
    path('materias-primas/<uuid:pk>/toggle-utilizado/', views.materiaprima_toggle_utilizado, name='materiaprima_toggle_utilizado'),
    
    # =======================================================================
    # 🔧 PRODUTOS INTERMEDIÁRIOS
    # =======================================================================
    path('produtos-intermediarios/', views.produto_intermediario_list, name='produto_intermediario_list'),
    path('produtos-intermediarios/novo/', views.produto_intermediario_create, name='produto_intermediario_create'),
    path('produtos-intermediarios/<uuid:pk>/editar/', views.produto_intermediario_update, name='produto_intermediario_update'),
    path('produtos-intermediarios/<uuid:pk>/excluir/', views.produto_intermediario_delete, name='produto_intermediario_delete'),
    path('produtos-intermediarios/<uuid:pk>/toggle-status/', views.produto_intermediario_toggle_status, name='produto_intermediario_toggle_status'),
    path('produtos-intermediarios/<uuid:pk>/toggle-utilizado/', views.produto_intermediario_toggle_utilizado, name='produto_intermediario_toggle_utilizado'),
    
    # Estrutura de Componentes
    path('produtos-intermediarios/<uuid:pk>/estrutura/', views.produto_intermediario_estrutura, name='produto_intermediario_estrutura'),
    path('produtos-intermediarios/<uuid:pk>/calcular-custo/', views.produto_intermediario_calcular_custo, name='produto_intermediario_calcular_custo'),
    
    # =======================================================================
    # 📋 PRODUTOS ACABADOS
    # =======================================================================
    path('produtos-acabados/', views.produto_acabado_list, name='produto_acabado_list'),
    path('produtos-acabados/novo/', views.produto_acabado_create, name='produto_acabado_create'),
    path('produtos-acabados/<uuid:pk>/editar/', views.produto_acabado_update, name='produto_acabado_update'),
    path('produtos-acabados/<uuid:pk>/excluir/', views.produto_acabado_delete, name='produto_acabado_delete'),
    path('produtos-acabados/<uuid:pk>/toggle-status/', views.produto_acabado_toggle_status, name='produto_acabado_toggle_status'),
    
    # =======================================================================
    # 📝 PROPOSTAS - Visualização no Portal de Produção
    # =======================================================================
    path('propostas/', views.proposta_list_producao, name='proposta_list_producao'),
    path('ordens-producao-projetos/', views.op_list, name='op_list'),
    path('propostas/<uuid:pk>/', views.proposta_detail_producao, name='proposta_detail_producao'),
    path('propostas/<uuid:pk>/alterar-status-producao/', views.alterar_status_producao, name='alterar_status_producao'),
    path('propostas/<uuid:pk>/gerar-lista-materiais/', views.gerar_lista_materiais, name='gerar_lista_materiais'),
    path('propostas/<uuid:pk>/upload-projeto-executivo/', views.upload_projeto_executivo, name='upload_projeto_executivo'),
    path('propostas/<uuid:pk>/upload-projeto-elevador/', views.upload_projeto_elevador, name='upload_projeto_elevador'),

    # =======================================================================
    # 📋 LISTAS DE MATERIAIS
    # =======================================================================
    path('listas-materiais/<uuid:pk>/editar/', views.lista_materiais_edit, name='lista_materiais_edit'),
    path('listas-materiais/<uuid:pk>/aprovar/', views.lista_materiais_aprovar, name='lista_materiais_aprovar'),
    
    # CRUD de Itens da Lista de Materiais
    path('listas-materiais/<int:lista_id>/itens/', views.item_lista_materiais_list, name='item_lista_materiais_list'),
    path('listas-materiais/<int:lista_id>/itens/novo/', views.item_lista_materiais_create, name='item_lista_materiais_create'),
    path('listas-materiais/<int:lista_id>/itens/<int:item_id>/editar/', views.item_lista_materiais_update, name='item_lista_materiais_update'),
    path('listas-materiais/<int:lista_id>/itens/<int:item_id>/excluir/', views.item_lista_materiais_delete, name='item_lista_materiais_delete'),
    
    # =======================================================================
    # 🛒 REQUISIÇÕES DE COMPRA
    # =======================================================================
    path('requisicoes-compra/', views.requisicao_compra_list, name='requisicao_compra_list'),
    path('requisicoes-compra/nova/', views.requisicao_compra_create, name='requisicao_compra_create'),
    path('requisicoes-compra/<int:pk>/', views.requisicao_compra_detail, name='requisicao_compra_detail'),
    path('requisicoes-compra/<int:pk>/editar/', views.requisicao_compra_update, name='requisicao_compra_update'),
    path('requisicoes-compra/<int:pk>/excluir/', views.requisicao_compra_delete, name='requisicao_compra_delete'),
    path('requisicoes-compra/<int:pk>/toggle-status/', views.requisicao_compra_toggle_status, name='requisicao_compra_toggle_status'),
    path('requisicoes-compra/<int:pk>/alterar-status/', views.requisicao_compra_alterar_status, name='requisicao_compra_alterar_status'),
    path('requisicoes-compra/<int:pk>/gerar-orcamento/', views.requisicao_compra_gerar_orcamento, name='requisicao_compra_gerar_orcamento'),
    
    # =======================================================================
    # 💰 ORÇAMENTOS DE COMPRA
    # =======================================================================
    path('orcamentos-compra/', views.orcamento_compra_list, name='orcamento_compra_list'),
    path('orcamentos-compra/novo/', views.orcamento_compra_create, name='orcamento_compra_create'),
    path('orcamentos-compra/<int:pk>/', views.orcamento_compra_detail, name='orcamento_compra_detail'),
    path('orcamentos-compra/<int:pk>/editar/', views.orcamento_compra_update, name='orcamento_compra_update'),
    path('orcamentos-compra/<int:pk>/excluir/', views.orcamento_compra_delete, name='orcamento_compra_delete'),
    path('orcamentos-compra/<int:pk>/alterar-status/', views.orcamento_compra_alterar_status, name='orcamento_compra_alterar_status'),
    path('orcamentos-compra/<int:pk>/duplicar/', views.orcamento_compra_duplicar, name='orcamento_compra_duplicar'),
    path('orcamentos-compra/<int:pk>/gerar-pedido/', views.orcamento_compra_gerar_pedido, name='orcamento_compra_gerar_pedido'),
    
    # =======================================================================
    # 📦 PEDIDOS DE COMPRA
    # =======================================================================
    path('pedidos-compra/', views.pedido_compra_list, name='pedido_compra_list'),
    path('pedidos-compra/novo/', views.pedido_compra_create, name='pedido_compra_create'),
    path('pedidos-compra/<int:pk>/', views.pedido_compra_detail, name='pedido_compra_detail'),
    path('pedidos-compra/<int:pk>/editar/', views.pedido_compra_update, name='pedido_compra_update'),
    path('pedidos-compra/<int:pk>/excluir/', views.pedido_compra_delete, name='pedido_compra_delete'),
    path('pedidos-compra/<int:pk>/alterar-status/', views.pedido_compra_alterar_status, name='pedido_compra_alterar_status'),
    path('pedidos-compra/<int:pk>/toggle-status/', views.pedido_compra_toggle_status, name='pedido_compra_toggle_status'),
    path('pedidos-compra/<int:pk>/pdf/', views.pedido_compra_gerar_pdf, name='pedido_compra_gerar_pdf'),
    path('pedidos-compra/<int:pk>/duplicar/', views.pedido_compra_duplicar, name='pedido_compra_duplicar'),
    path('pedidos-compra/<int:pk>/recebimento/', views.pedido_compra_recebimento, name='pedido_compra_recebimento'),
    path('pedidos-compra/<int:pedido_pk>/item/<int:item_pk>/receber/', views.receber_item_pedido, name='receber_item_pedido'),

    # Criar pedido a partir de requisição
    path('pedidos-compra/from-requisicao/<int:requisicao_pk>/', views.pedido_compra_from_requisicao, name='pedido_compra_from_requisicao'),

    # (Opcional) Criar pedido a partir de orçamento - para uso futuro
    path('pedidos-compra/from-orcamento/<int:orcamento_pk>/', views.pedido_compra_from_orcamento, name='pedido_compra_from_orcamento'),

    # =======================================================================
    # 📊 RELATÓRIOS DE SALDO DE REQUISIÇÕES
    # =======================================================================
    path('relatorios/saldos-requisicoes/', views.relatorio_saldos_requisicoes, name='relatorio_saldos_requisicoes'),
    path('relatorios/saldos-requisicoes/exportar-excel/', views.exportar_saldos_requisicoes_excel, name='exportar_saldos_requisicoes_excel'),
    path('requisicoes/<int:pk>/saldo/', views.requisicao_saldo_detail, name='requisicao_saldo_detail'),

    # =======================================================================
    # 🔄 RECLASSIFICAÇÃO DE PRODUTOS
    # =======================================================================
    path('reclassificar-produto/', views.reclassificar_produto_form, name='reclassificar_produto_form'),
    path('reclassificar-produto/executar/', views.reclassificar_produto_executar, name='reclassificar_produto_executar'),
    
    # =======================================================================
    # 📊 RELATÓRIOS
    # =======================================================================
    path('relatorios/estoque-baixo/', views.relatorio_estoque_baixo, name='relatorio_estoque_baixo'),
    path('relatorios/produtos-sem-fornecedor/', views.relatorio_produtos_sem_fornecedor, name='relatorio_produtos_sem_fornecedor'),
    path('relatorios/producao/', views.relatorio_producao, name='relatorio_producao'),
    path('relatorios/produtos-pi-por-tipo/', views.relatorio_produtos_pi_por_tipo, name='relatorio_produtos_pi_por_tipo'),
    path('relatorios/produtos-completo/', views.relatorio_produtos_completo, name='relatorio_produtos_completo'),
    
    # =======================================================================
    # 🔌 APIs AJAX E ENDPOINTS
    # =======================================================================
    
    # APIs Gerais
    path('api/subgrupos/', views.get_subgrupos_by_grupo, name='api_subgrupos'),
    path('api/grupos-todos/', views.api_grupos_todos, name='api_grupos_todos'),
    path('api/produto-codigo/', views.get_info_produto_codigo, name='api_produto_codigo'),
    path('api/produto-info/', views.api_produto_info, name='api_produto_info'),
    path('api/fornecedor/<int:fornecedor_id>/produtos/', views.api_fornecedor_produtos, name='api_fornecedor_produtos'),
    path('api/buscar-produtos/', views.api_buscar_produtos, name='api_buscar_produtos'),
    path('api/tipo-pi-info/', views.api_tipo_pi_info, name='api_tipo_pi_info'),
    
    # APIs para Estrutura de Componentes
    path('api/buscar-produtos-estrutura/', views.api_buscar_produtos_estrutura, name='api_buscar_produtos_estrutura'),
    path('api/estrutura/adicionar-componente/', views.api_adicionar_componente_estrutura, name='api_adicionar_componente_estrutura'),
    path('api/estrutura/componente/<int:componente_id>/remover/', views.api_remover_componente_estrutura, name='api_remover_componente_estrutura'),
    path('api/estrutura/componente/<int:componente_id>/editar/', views.api_editar_componente_estrutura, name='api_editar_componente_estrutura'),
    path('api/estrutura/produto/<uuid:produto_id>/aplicar-custo/', views.api_aplicar_custo_estrutura, name='api_aplicar_custo_estrutura'),
    path('api/estrutura/produto/<uuid:produto_id>/componentes/', views.api_listar_componentes_estrutura, name='api_listar_componentes_estrutura'),
    
    # APIs para Reclassificação
    path('api/buscar-produto-reclassificar/', views.api_buscar_produto_para_reclassificar, name='api_buscar_produto_reclassificar'),
    path('api/subgrupos-reclassificacao/', views.api_subgrupos_por_grupo_reclassificacao, name='api_subgrupos_reclassificacao'),
    path('api/preview-novo-codigo/', views.api_preview_novo_codigo, name='api_preview_novo_codigo'),
    
    # APIs para Relatórios
    path('api/subgrupos-relatorio/', views.api_subgrupos_por_grupo_relatorio, name='api_subgrupos_relatorio'),

    # =======================================================================
    # ESTOQUE - Locais
    # =======================================================================
    path('locais-estoque/', views.local_estoque_list, name='local_estoque_list'),
    path('locais-estoque/novo/', views.local_estoque_create, name='local_estoque_create'),
    path('locais-estoque/<int:pk>/editar/', views.local_estoque_update, name='local_estoque_update'),
    path('locais-estoque/<int:pk>/excluir/', views.local_estoque_delete, name='local_estoque_delete'),
    path('locais-estoque/<int:pk>/alternar-status/', views.local_estoque_toggle_status, name='local_estoque_toggle_status'),

    # =======================================================================
    # ESTOQUE - Tipos de Movimento
    # =======================================================================
    path('tipos-movimento-entrada/', views.tipo_movimento_entrada_list, name='tipo_movimento_entrada_list'),
    path('tipos-movimento-entrada/novo/', views.tipo_movimento_entrada_create, name='tipo_movimento_entrada_create'),
    path('tipos-movimento-entrada/<int:pk>/editar/', views.tipo_movimento_entrada_update, name='tipo_movimento_entrada_update'),
    path('tipos-movimento-entrada/<int:pk>/excluir/', views.tipo_movimento_entrada_delete, name='tipo_movimento_entrada_delete'),
    path('tipos-movimento-entrada/<int:pk>/alternar-status/', views.tipo_movimento_entrada_toggle_status, name='tipo_movimento_entrada_toggle_status'),

    path('tipos-movimento-saida/', views.tipo_movimento_saida_list, name='tipo_movimento_saida_list'),
    path('tipos-movimento-saida/novo/', views.tipo_movimento_saida_create, name='tipo_movimento_saida_create'),
    path('tipos-movimento-saida/<int:pk>/editar/', views.tipo_movimento_saida_update, name='tipo_movimento_saida_update'),
    path('tipos-movimento-saida/<int:pk>/excluir/', views.tipo_movimento_saida_delete, name='tipo_movimento_saida_delete'),
    path('tipos-movimento-saida/<int:pk>/alternar-status/', views.tipo_movimento_saida_toggle_status, name='tipo_movimento_saida_toggle_status'),

    # =======================================================================
    # ESTOQUE - Movimentos de Entrada
    # =======================================================================
    path('entradas/', views.movimento_entrada_list, name='movimento_entrada_list'),
    path('entradas/nova/', views.movimento_entrada_create, name='movimento_entrada_create'),
    path('entradas/<int:pk>/', views.movimento_entrada_detail, name='movimento_entrada_detail'),
    path('entradas/<int:pk>/editar/', views.movimento_entrada_update, name='movimento_entrada_update'),
    path('entradas/<int:pk>/excluir/', views.movimento_entrada_delete, name='movimento_entrada_delete'),
    path('entradas/<int:pk>/confirmar/', views.movimento_entrada_confirmar, name='movimento_entrada_confirmar'),
    path('entradas/<int:pk>/cancelar/', views.movimento_entrada_cancelar, name='movimento_entrada_cancelar'),

    # =======================================================================
    # ESTOQUE - Movimentos de Saida
    # =======================================================================
    path('saidas/', views.movimento_saida_list, name='movimento_saida_list'),
    path('saidas/nova/', views.movimento_saida_create, name='movimento_saida_create'),
    path('saidas/<int:pk>/', views.movimento_saida_detail, name='movimento_saida_detail'),
    path('saidas/<int:pk>/editar/', views.movimento_saida_update, name='movimento_saida_update'),
    path('saidas/<int:pk>/excluir/', views.movimento_saida_delete, name='movimento_saida_delete'),
    path('saidas/<int:pk>/confirmar/', views.movimento_saida_confirmar, name='movimento_saida_confirmar'),
    path('saidas/<int:pk>/cancelar/', views.movimento_saida_cancelar, name='movimento_saida_cancelar'),

    # =======================================================================
    # ESTOQUE - Posicao
    # =======================================================================
    path('posicao-estoque/', views.posicao_estoque, name='posicao_estoque'),

    # =======================================================================
    # REQUISIÇÃO DE MATERIAL
    # =======================================================================
    path('requisicao-material/', views.requisicao_material_list, name='requisicao_material_list'),
    path('requisicao-material/nova/', views.requisicao_material_create, name='requisicao_material_create'),
    path('requisicao-material/<int:pk>/', views.requisicao_material_detail, name='requisicao_material_detail'),
    path('requisicao-material/<int:pk>/editar/', views.requisicao_material_update, name='requisicao_material_update'),
    path('requisicao-material/<int:pk>/excluir/', views.requisicao_material_delete, name='requisicao_material_delete'),
    path('requisicao-material/<int:pk>/alterar-status/', views.requisicao_material_alterar_status, name='requisicao_material_alterar_status'),

    # APIs para itens da requisição
    path('requisicao-material/<int:pk>/adicionar-item/', views.api_adicionar_item_requisicao, name='api_adicionar_item_requisicao'),
    path('requisicao-material/<int:pk>/remover-item/<int:item_pk>/', views.api_remover_item_requisicao, name='api_remover_item_requisicao'),
    path('requisicao-material/<int:pk>/buscar-produtos/', views.api_buscar_produtos_requisicao, name='api_buscar_produtos_requisicao'),

    # =======================================================================
    # ORDENS DE PRODUCAO
    # =======================================================================
    path('ordens-producao/', ordem_producao_list, name='ordem_producao_list'),
    path('ordens-producao/nova/', ordem_producao_create, name='ordem_producao_create'),
    path('ordens-producao/<int:pk>/', ordem_producao_detail, name='ordem_producao_detail'),
    path('ordens-producao/<int:pk>/editar/', ordem_producao_update, name='ordem_producao_update'),
    path('ordens-producao/<int:pk>/excluir/', ordem_producao_delete, name='ordem_producao_delete'),
    path('ordens-producao/<int:pk>/liberar/', ordem_producao_liberar, name='ordem_producao_liberar'),
    path('ordens-producao/<int:pk>/iniciar/', ordem_producao_iniciar, name='ordem_producao_iniciar'),
    path('ordens-producao/<int:pk>/apontar/', ordem_producao_apontar, name='ordem_producao_apontar'),
    path('ordens-producao/<int:pk>/concluir/', ordem_producao_concluir, name='ordem_producao_concluir'),
    path('ordens-producao/<int:pk>/cancelar/', ordem_producao_cancelar, name='ordem_producao_cancelar'),
]