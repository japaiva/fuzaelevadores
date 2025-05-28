# vendedor/views.py - VERSÃO CORRIGIDA E LIMPA

import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from core.services.calculo_pedido import CalculoPedidoService
from core.utils.formatters import extrair_especificacoes_do_pedido, agrupar_respostas_por_pagina, safe_decimal, safe_int

from .models import Pedido, HistoricoPedido, AnexoPedido
from .forms import (
    PedidoClienteElevadorForm, PedidoCabinePortasForm, 
    AnexoPedidoForm, PedidoFiltroForm, ClienteCreateForm
)

from .utils import validar_permissoes_vendedor, calcular_estatisticas_vendedor
from core.models import Cliente

logger = logging.getLogger(__name__)

def safe_json_load(json_field):
    """Função auxiliar para carregar JSONField de forma segura"""
    if json_field is None:
        return {}
    if isinstance(json_field, dict):
        return json_field
    if isinstance(json_field, str):
        try:
            return json.loads(json_field)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

# =============================================================================
# PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial do vendedor"""
    dados_stats = calcular_estatisticas_vendedor(request.user)
    pedidos_recentes = Pedido.objects.filter(vendedor=request.user).order_by('-criado_em')[:5]
    
    total_pedidos = dados_stats['stats']['total']
    pedidos_abertos = Pedido.objects.filter(
        vendedor=request.user, 
        status__in=['rascunho', 'simulado', 'orcamento_gerado']
    ).count()
    pedidos_aprovados = Pedido.objects.filter(vendedor=request.user, status='aprovado').count()
    
    context = {
        'total_pedidos': total_pedidos,
        'pedidos_abertos': pedidos_abertos,
        'pedidos_aprovados': pedidos_aprovados,
        'pedidos_recentes': pedidos_recentes,
    }
    return render(request, 'vendedor/home.html', context)


@login_required
def dashboard(request):
    """Dashboard principal do vendedor"""
    dados_stats = calcular_estatisticas_vendedor(request.user)
    pedidos_recentes = Pedido.objects.filter(vendedor=request.user).order_by('-criado_em')[:5]
    
    context = {
        **dados_stats['stats'],
        'stats_status': dados_stats['stats_status'],
        'stats_modelo': dados_stats['stats_modelo'], 
        'pedidos_recentes': pedidos_recentes,
    }
    return render(request, 'vendedor/dashboard.html', context)

# =============================================================================
# CÁLCULOS DO PEDIDO
# =============================================================================

@login_required
def pedido_calcular(request, pk):
    """Executa os cálculos do pedido com logs detalhados"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Validar permissões
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    # Verificar se pode calcular
    if not pedido.pode_calcular():
        messages.error(request, 'Pedido não tem dados suficientes para cálculo. Complete as especificações primeiro.')
        return redirect('vendedor:pedido_step1', pk=pedido.pk)
    
    try:
        logger.info(f"=== INICIANDO CÁLCULOS PARA PEDIDO {pedido.numero} ===")
        
        # LOG DOS DADOS ANTES DO CÁLCULO
        logger.info(f"ANTES DO CÁLCULO:")
        logger.info(f"  - Status: {pedido.status}")
        logger.info(f"  - Cliente: {pedido.cliente.nome}")
        logger.info(f"  - Modelo: {pedido.modelo_elevador}")
        logger.info(f"  - Capacidade: {pedido.capacidade}")
        logger.info(f"  - Acionamento: {pedido.acionamento}")
        logger.info(f"  - Poço: {pedido.largura_poco}x{pedido.comprimento_poco}x{pedido.altura_poco}")
        logger.info(f"  - Material cabine: {pedido.material_cabine}")
        logger.info(f"  - Altura cabine: {pedido.altura_cabine}")
        
        # EXECUTAR CÁLCULOS
        resultado = CalculoPedidoService.calcular_custos_completo(pedido)
        
        if resultado['success']:
            # Recarregar o pedido do banco para garantir que temos os dados atualizados
            pedido.refresh_from_db()
            
            logger.info(f"DEPOIS DO CÁLCULO - DADOS SALVOS:")
            logger.info(f"  - Status: {pedido.status}")
            logger.info(f"  - Largura cabine calculada: {pedido.largura_cabine_calculada}")
            logger.info(f"  - Comprimento cabine calculado: {pedido.comprimento_cabine_calculado}")
            logger.info(f"  - Capacidade cabine calculada: {pedido.capacidade_cabine_calculada}")
            logger.info(f"  - Custo produção: {pedido.custo_producao}")
            logger.info(f"  - Preço calculado: {pedido.preco_venda_calculado}")
            
            # Verificar JSONFields
            ficha_tecnica = safe_json_load(pedido.ficha_tecnica)
            dimensionamento = safe_json_load(pedido.dimensionamento_detalhado)
            formacao_preco = safe_json_load(pedido.formacao_preco)
            
            logger.info(f"  - Ficha técnica: {len(ficha_tecnica)} chaves")
            logger.info(f"  - Dimensionamento: {len(dimensionamento)} chaves")
            logger.info(f"  - Formação preço: {len(formacao_preco)} chaves")
            logger.info(f"  - Explicação: {len(pedido.explicacao_calculo or '')} caracteres")
            
            # Registrar no histórico
            HistoricoPedido.objects.create(
                pedido=pedido,
                status_anterior=pedido.status,
                status_novo='simulado',
                observacao='Cálculos executados com sucesso',
                usuario=request.user
            )
            
            messages.success(request, f'Cálculos do pedido {pedido.numero} executados com sucesso!')
            
            # MOSTRAR RESUMO DOS DADOS CALCULADOS
            if ficha_tecnica and 'dimensoes_cabine' in ficha_tecnica:
                dim = ficha_tecnica['dimensoes_cabine']
                messages.info(request, 
                    f"Cabine: {dim.get('largura', 0):.2f}m x {dim.get('comprimento', 0):.2f}m x {dim.get('altura', 0):.2f}m"
                )
            
            if pedido.custo_producao:
                messages.info(request, f"Custo: R$ {pedido.custo_producao:,.2f}")
            
            if pedido.preco_venda_calculado:
                messages.info(request, f"Preço: R$ {pedido.preco_venda_calculado:,.2f}")
            
            logger.info(f"Cálculos finalizados com sucesso para pedido {pedido.numero}")
            
        else:
            messages.error(request, 'Erro nos cálculos. Verifique os logs para mais detalhes.')
            logger.error(f"Erro nos cálculos do pedido {pedido.numero}")
            
    except Exception as e:
        logger.error(f"ERRO AO CALCULAR PEDIDO {pedido.numero}: {str(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        messages.error(request, f'Erro nos cálculos: {str(e)}')
    
    return redirect('vendedor:pedido_detail', pk=pedido.pk)

# =============================================================================
# WORKFLOW DO PEDIDO EM 2 ETAPAS
# =============================================================================

@login_required
def pedido_step1(request, pk=None):
    """Etapa 1: Cliente + Elevador + Poço"""
    
    # Determinar se é criação ou edição
    if pk:
        # EDIÇÃO
        pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
        pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
        if not pode_editar:
            messages.error(request, mensagem)
            return redirect('vendedor:pedido_detail', pk=pedido.pk)
        editing = True
    else:
        # CRIAÇÃO
        pedido = None
        editing = False
    
    if request.method == 'POST':
        if editing:
            # EDIÇÃO
            form = PedidoClienteElevadorForm(request.POST, instance=pedido)
            if form.is_valid():
                try:
                    pedido = form.save(commit=False)
                    pedido.atualizado_por = request.user
                    pedido.save()
                    
                    HistoricoPedido.objects.create(
                        pedido=pedido,
                        status_novo=pedido.status,
                        observacao='Dados de cliente/elevador atualizados',
                        usuario=request.user
                    )
                    
                    return redirect('vendedor:pedido_step2', pk=pedido.pk)
                    
                except Exception as e:
                    logger.error(f"Erro ao atualizar pedido {pedido.numero}: {str(e)}")
                    messages.error(request, f'Erro ao atualizar pedido: {str(e)}')
        else:
            # CRIAÇÃO
            form = PedidoClienteElevadorForm(request.POST)
            if form.is_valid():
                try:
                    pedido = form.save(commit=False)
                    pedido.vendedor = request.user
                    pedido.atualizado_por = request.user
                    pedido.status = 'rascunho'
                    
                    # Valores padrão para segunda etapa
                    pedido.modelo_porta_cabine = 'Automática'
                    pedido.material_porta_cabine = 'Inox'
                    pedido.folhas_porta_cabine = '2'
                    pedido.largura_porta_cabine = 0.80
                    pedido.altura_porta_cabine = 2.00
                    pedido.modelo_porta_pavimento = 'Automática'
                    pedido.material_porta_pavimento = 'Inox'
                    pedido.folhas_porta_pavimento = '2'
                    pedido.largura_porta_pavimento = 0.80
                    pedido.altura_porta_pavimento = 2.00
                    pedido.material_cabine = 'Inox 430'
                    pedido.espessura_cabine = '1,2'
                    pedido.saida_cabine = 'Padrão'
                    pedido.altura_cabine = 2.30
                    pedido.piso_cabine = 'Por conta do cliente'
                    
                    logger.info(f"Criando pedido para cliente {pedido.cliente.nome}")
                    pedido.save()
                    logger.info(f"Pedido {pedido.numero} criado com sucesso")
                    
                    HistoricoPedido.objects.create(
                        pedido=pedido,
                        status_novo='rascunho',
                        observacao='Pedido criado com valores padrão',
                        usuario=request.user
                    )
                    
                    return redirect('vendedor:pedido_step2', pk=pedido.pk)
                    
                except Exception as e:
                    logger.error(f"Erro ao criar pedido: {str(e)}")
                    messages.error(request, f'Erro ao criar pedido: {str(e)}')
                    
        if form.errors:
            logger.warning(f"Form inválido: {form.errors}")
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        # GET request
        if editing:
            form = PedidoClienteElevadorForm(instance=pedido)
        else:
            form = PedidoClienteElevadorForm()
    
    # Buscar clientes para o select
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'vendedor/pedido_step1.html', {
        'form': form,
        'pedido': pedido,  # None para criação, objeto para edição
        'clientes': clientes,
        'editing': editing,
    })


@login_required
def pedido_step2(request, pk):
    """Etapa 2: Cabine + Portas - COM EXECUÇÃO AUTOMÁTICA DE CÁLCULOS"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    editing = pedido.status != 'rascunho' or bool(pedido.preco_venda_calculado)
    
    if request.method == 'POST':
        form = PedidoCabinePortasForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.atualizado_por = request.user
            pedido.save()
            
            # EXECUTAR CÁLCULOS AUTOMÁTICOS SE POSSÍVEL
            try:
                if pedido.pode_calcular():
                    logger.info(f"Step 2: Executando cálculos automáticos para pedido {pedido.numero}")
                    
                    resultado = CalculoPedidoService.calcular_custos_completo(pedido)
                    
                    if resultado['success']:
                        logger.info(f"Cálculos executados com sucesso no step 2")
                    else:
                        logger.warning(f"Problemas nos cálculos do pedido {pedido.numero}")
                        messages.warning(request, 'Pedido salvo, mas houve problemas nos cálculos.')
                else:
                    logger.info("Pedido salvo, mas não foi possível calcular ainda (dados insuficientes)")
                    messages.info(request, 'Pedido salvo. Execute os cálculos quando estiver pronto.')
                
            except Exception as e:
                logger.error(f"Erro ao calcular no step 2: {str(e)}")
                messages.warning(request, f'Pedido salvo, mas erro nos cálculos: {str(e)}')
            
            # Registrar no histórico
            HistoricoPedido.objects.create(
                pedido=pedido,
                status_anterior='rascunho' if not editing else pedido.status,
                status_novo=pedido.status,
                observacao='Especificações da cabine/portas finalizadas',
                usuario=request.user
            )
            
            return redirect('vendedor:pedido_detail', pk=pedido.pk)
    else:
        form = PedidoCabinePortasForm(instance=pedido)
    
    return render(request, 'vendedor/pedido_step2.html', {
        'form': form,
        'pedido': pedido,
        'editing': editing,
    })

# =============================================================================
# GESTÃO DE PEDIDOS
# =============================================================================

@login_required
def pedido_list(request):
    """Lista de pedidos do vendedor"""
    pedidos_list = Pedido.objects.filter(vendedor=request.user).select_related('cliente').order_by('-criado_em')
    
    # Aplicar filtros
    form = PedidoFiltroForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('status'):
            pedidos_list = pedidos_list.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            pedidos_list = pedidos_list.filter(
                Q(numero__icontains=query) |
                Q(nome_projeto__icontains=query) |
                Q(cliente__nome__icontains=query)
            )
    
    # Paginação
    paginator = Paginator(pedidos_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        pedidos = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        pedidos = paginator.page(1)
    
    context = {
        'pedidos': pedidos,
        'form': form,
    }
    return render(request, 'vendedor/pedido_list.html', context)


@login_required
def pedido_detail(request, pk):
    """Detalhes do pedido - VERSÃO REDESENHADA E DEBUGADA"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    logger.info(f"=== CARREGANDO DETALHES DO PEDIDO {pedido.numero} ===")
    
    # EXTRAIR DADOS DOS JSONFields DE FORMA SEGURA
    ficha_tecnica = safe_json_load(pedido.ficha_tecnica)
    dimensionamento = safe_json_load(pedido.dimensionamento_detalhado)
    formacao_preco = safe_json_load(pedido.formacao_preco)
    explicacao = pedido.explicacao_calculo or ''
    
    # PROTEÇÃO EXTRA: Verificar custos_detalhados e componentes_calculados
    custos_detalhados = safe_json_load(pedido.custos_detalhados)
    componentes_calculados = safe_json_load(pedido.componentes_calculados)
    
    # DEBUG: Log da estrutura dos dados JSON
    logger.info(f"DIAGNÓSTICO COMPLETO:")
    logger.info(f"  - Status: {pedido.status}")
    logger.info(f"  - Custo produção: {pedido.custo_producao}")
    logger.info(f"  - Preço calculado: {pedido.preco_venda_calculado}")
    logger.info(f"  - Ficha técnica carregada: {len(ficha_tecnica)} chaves")
    logger.info(f"  - Dimensionamento carregado: {len(dimensionamento)} chaves")
    logger.info(f"  - Formação preço carregada: {len(formacao_preco)} chaves")
    logger.info(f"  - Explicação carregada: {len(explicacao)} caracteres")
    
    # DEBUG ESPECÍFICO: Estrutura dos custos detalhados
    if custos_detalhados:
        logger.info(f"  - Custos detalhados: {len(custos_detalhados)} categorias")
        for categoria, dados in custos_detalhados.items():
            logger.info(f"    * {categoria}: {type(dados)} - {dados if not isinstance(dados, (list, dict)) else f'Estrutura com {len(dados)} itens'}")
    
    # DEBUG ESPECÍFICO: Estrutura dos componentes calculados  
    if componentes_calculados:
        logger.info(f"  - Componentes calculados: {len(componentes_calculados)} tipos")
        for tipo, dados in componentes_calculados.items():
            logger.info(f"    * {tipo}: {type(dados)} - {dados if not isinstance(dados, (list, dict)) else f'Estrutura com {len(dados)} itens'}")
    
    # Calcular áreas e volumes
    area_poco = 0
    volume_poco = 0
    area_cabine = 0
    
    try:
        if pedido.largura_poco and pedido.comprimento_poco:
            area_poco = Decimal(str(pedido.largura_poco)) * Decimal(str(pedido.comprimento_poco))
            if pedido.altura_poco:
                volume_poco = area_poco * Decimal(str(pedido.altura_poco))
        
        if pedido.largura_cabine_calculada and pedido.comprimento_cabine_calculado:
            area_cabine = Decimal(str(pedido.largura_cabine_calculada)) * Decimal(str(pedido.comprimento_cabine_calculado))
    except (TypeError, ValueError, InvalidOperation) as e:
        logger.warning(f"Erro ao calcular áreas/volumes: {e}")
        area_poco = 0
        volume_poco = 0
        area_cabine = 0
    
    # Determinar nível do usuário
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # LIMPEZA DE DADOS PARA TEMPLATE
    # Garantir que custos_detalhados seja um dict válido
    if not isinstance(custos_detalhados, dict):
        custos_detalhados = {}
        
    # Garantir que componentes_calculados seja um dict válido
    if not isinstance(componentes_calculados, dict):
        componentes_calculados = {}
    
    logger.info(f"ENVIANDO PARA TEMPLATE:")
    logger.info(f"  - ficha_tecnica: {bool(ficha_tecnica)} ({len(ficha_tecnica)} chaves)")
    logger.info(f"  - dimensionamento: {bool(dimensionamento)} ({len(dimensionamento)} chaves)")
    logger.info(f"  - formacao_preco: {bool(formacao_preco)} ({len(formacao_preco)} chaves)")
    logger.info(f"  - explicacao: {bool(explicacao)} ({len(explicacao)} chars)")
    logger.info(f"  - custos_detalhados: {bool(custos_detalhados)} ({len(custos_detalhados)} chaves)")
    logger.info(f"  - componentes_calculados: {bool(componentes_calculados)} ({len(componentes_calculados)} chaves)")
    
    context = {
        'pedido': pedido,
        'ficha_tecnica': ficha_tecnica,
        'dimensionamento': dimensionamento,
        'explicacao': explicacao,
        'formacao_preco': formacao_preco,
        'user_level': user_level,
        'area_poco': area_poco,
        'volume_poco': volume_poco,
        'area_cabine': area_cabine,
        # Não enviar os JSONs originais para evitar conflitos no template
        # O template deve usar pedido.custos_detalhados e pedido.componentes_calculados
    }
    
    return render(request, 'vendedor/pedido_detail.html', context)

@login_required
def pedido_edit(request, pk):
    """Editar pedido existente - redireciona para step 1"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    # Redirecionar para o primeiro passo
    return redirect('vendedor:pedido_step1', pk=pedido.pk)


@login_required
def pedido_delete(request, pk):
    """Excluir pedido com validações de segurança"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Verificar se o pedido pode ser excluído
    if pedido.status not in ['rascunho', 'simulado']:
        messages.error(request, 
            f'Não é possível excluir o pedido {pedido.numero}. '
            f'Apenas pedidos em rascunho ou simulado podem ser excluídos.'
        )
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    if request.method == 'POST':
        try:
            numero = pedido.numero
            nome_projeto = pedido.nome_projeto
            
            # Log da exclusão antes de apagar
            logger.info(
                f"Pedido {numero} ({nome_projeto}) excluído pelo usuário {request.user.username}"
            )
            
            # Excluir pedido (cascata remove histórico e anexos automaticamente)
            pedido.delete()
            
            messages.success(request, 
                f'Pedido {numero} - {nome_projeto} excluído com sucesso.'
            )
            return redirect('vendedor:pedido_list')
            
        except Exception as e:
            logger.error(f"Erro ao excluir pedido {pedido.numero}: {str(e)}")
            messages.error(request, 
                f'Erro ao excluir pedido: {str(e)}. Tente novamente.'
            )
            return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    # GET request - mostrar página de confirmação
    context = {
        'pedido': pedido,
        'pode_excluir': True,
    }
    
    return render(request, 'vendedor/pedido_confirm_delete.html', context)


@login_required
def pedido_duplicar(request, pk):
    """Duplicar pedido existente"""
    pedido_original = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Criar uma cópia do pedido
    pedido_copia = Pedido.objects.get(pk=pedido_original.pk)
    pedido_copia.pk = None  # Remove o ID para criar novo
    pedido_copia.numero = None  # Será gerado automaticamente
    pedido_copia.status = 'rascunho'
    pedido_copia.nome_projeto = f"Cópia de {pedido_original.nome_projeto}"
    pedido_copia.atualizado_por = request.user
    pedido_copia.save()
    
    messages.success(request, f'Pedido duplicado com sucesso. Novo número: {pedido_copia.numero}')
    return redirect('vendedor:pedido_edit', pk=pedido_copia.pk)

# =============================================================================
# APIS AJAX
# =============================================================================

@login_required
def api_cliente_info(request, cliente_id):
    """API para retornar informações do cliente"""
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id, ativo=True)
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'nome_fantasia': cliente.nome_fantasia or '',
                'telefone': cliente.telefone or '',
                'email': cliente.email or '',
                'contato_principal': cliente.contato_principal or '',
                'endereco_completo': cliente.endereco_completo,
                'tipo_pessoa': cliente.get_tipo_pessoa_display(),
                'cpf_cnpj': cliente.cpf_cnpj or '',
            }
        })
        
    except Cliente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cliente não encontrado'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar cliente {cliente_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        })


@login_required
def cliente_create_ajax(request):
    """Cria cliente via AJAX para não perder o contexto do vendedor"""
    if request.method == 'POST':
        form = ClienteCreateForm(request.POST)
        if form.is_valid():
            try:
                cliente = form.save(commit=False)
                cliente.criado_por = request.user
                cliente.save()
                
                logger.info(f"Cliente {cliente.nome} criado via AJAX pelo vendedor {request.user}")
                
                return JsonResponse({
                    'success': True,
                    'cliente': {
                        'id': cliente.id,
                        'nome': cliente.nome,
                        'nome_fantasia': cliente.nome_fantasia or '',
                        'telefone': cliente.telefone or '',
                        'email': cliente.email or '',
                        'endereco_completo': cliente.endereco_completo,
                    }
                })
                
            except Exception as e:
                logger.error(f"Erro ao criar cliente via AJAX: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'errors': {'Erro': [str(e)]}
                })
        else:
            # Formatar erros para exibição
            formatted_errors = {}
            for field, errors in form.errors.items():
                field_label = form.fields[field].label or field
                formatted_errors[field_label] = errors
                
            return JsonResponse({
                'success': False,
                'errors': formatted_errors
            })
    
    # GET request - retorna formulário
    form = ClienteCreateForm()
    return render(request, 'vendedor/cliente_create_modal.html', {
        'form': form
    })

# =============================================================================
# GERAÇÃO DE PDFs
# =============================================================================

@login_required
def gerar_pdf_orcamento(request, pk):
    """Gerar PDF do orçamento comercial"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    try:
        # Usar dados persistidos do pedido
        formacao_preco = pedido.formacao_preco or {}
        ficha_tecnica = pedido.ficha_tecnica or {}
        
        # Verificar se tem dados suficientes
        if not formacao_preco or not pedido.preco_venda_calculado:
            messages.warning(request, 'Execute os cálculos do pedido antes de gerar o orçamento.')
            return redirect('vendedor:pedido_detail', pk=pk)
        
        # TEMPORÁRIO: Mostrar mensagem até implementar o service
        messages.info(request, 'Geração de PDF de orçamento em desenvolvimento.')
        return redirect('vendedor:pedido_detail', pk=pk)
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF orçamento para pedido {pedido.numero}: {str(e)}")
        messages.error(request, 'Erro interno ao gerar PDF. Tente novamente.')
        return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def gerar_pdf_demonstrativo(request, pk):
    """Gerar PDF do demonstrativo técnico/custo"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Verificar permissão para dados técnicos
    if getattr(request.user, 'nivel', 'vendedor') not in ['admin', 'engenharia']:
        messages.error(request, 'Você não tem permissão para acessar dados técnicos.')
        return redirect('vendedor:pedido_detail', pk=pk)
    
    try:
        # Usar dados persistidos do pedido
        dimensionamento = pedido.dimensionamento_detalhado or {}
        explicacao = pedido.explicacao_calculo or ''
        custos_detalhados = pedido.custos_detalhados or {}
        componentes = pedido.componentes_calculados or {}
        
        # Verificar se tem dados suficientes
        if not dimensionamento or not custos_detalhados:
            messages.warning(request, 'Execute os cálculos do pedido antes de gerar o demonstrativo.')
            return redirect('vendedor:pedido_detail', pk=pk)
        
        # TEMPORÁRIO: Mostrar mensagem até implementar o service
        messages.info(request, 'Geração de PDF demonstrativo em desenvolvimento.')
        return redirect('vendedor:pedido_detail', pk=pk)
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF demonstrativo para pedido {pedido.numero}: {str(e)}")
        messages.error(request, 'Erro interno ao gerar PDF. Tente novamente.')
        return redirect('vendedor:pedido_detail', pk=pk)

# =============================================================================
# VIEWS TEMPORÁRIAS
# =============================================================================

@login_required
def pedido_change_status(request, pk):
    """Alterar status do pedido"""
    messages.info(request, 'Funcionalidade de alteração de status em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required  
def pedido_anexo_upload(request, pk):
    """Upload de anexos do pedido"""
    messages.info(request, 'Funcionalidade de upload de anexos em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def pedido_anexo_delete(request, pk, anexo_id):
    """Excluir anexo do pedido"""
    messages.info(request, 'Funcionalidade de exclusão de anexos em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def api_dados_precificacao(request, pk):
    """
    API para retornar dados de precificação do pedido com parâmetros atualizados
    """
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    try:
        # Tentar importar o PricingService, se não existir usar valores default
        try:
            from core.services.pricing import PricingService
            parametros = PricingService._get_parametros()
        except ImportError:
            # Fallback: valores padrão se o service não existir
            parametros = {
                'comissao': 3.0,
                'margem': 30.0,
                'fat.Elevadores': 10.0,
                'fat.Fuza': 8.0,
                'fat.Manutenção': 5.0,
                'desc.alcada1': 5.0
            }
        
        # Mapear percentual de impostos baseado no "faturado_por"
        mapeamento_impostos = {
            'Elevadores': parametros.get('fat.Elevadores', 10.0),
            'Fuza': parametros.get('fat.Fuza', 8.0), 
            'Manutenção': parametros.get('fat.Manutenção', 5.0),
        }
        
        # Montar dados do pedido
        dados_pedido = {
            'custoProducao': float(pedido.custo_producao or 0),
            'percentualMargem': parametros.get('margem', 30.0),
            'percentualComissao': parametros.get('comissao', 3.0),
            'percentualImpostos': mapeamento_impostos.get(pedido.faturado_por, 10.0),
            'precoCalculado': float(pedido.preco_venda_calculado or 0),
            'precoNegociado': float(pedido.preco_negociado or 0),
            'alcadaMaxima': parametros.get('desc.alcada1', 5.0),
            'faturadoPor': pedido.faturado_por,
        }
        
        # Se não tem preço negociado, usar o calculado
        if dados_pedido['precoNegociado'] == 0:
            dados_pedido['precoNegociado'] = dados_pedido['precoCalculado']
        
        logger.info(f"Dados de precificação para pedido {pedido.numero}:")
        logger.info(f"  - Custo produção: R$ {dados_pedido['custoProducao']:,.2f}")
        logger.info(f"  - Faturado por: {dados_pedido['faturadoPor']}")
        logger.info(f"  - Impostos: {dados_pedido['percentualImpostos']}%")
        logger.info(f"  - Margem: {dados_pedido['percentualMargem']}%")
        logger.info(f"  - Comissão: {dados_pedido['percentualComissao']}%")
        logger.info(f"  - Alçada: {dados_pedido['alcadaMaxima']}%")
        
        return JsonResponse({
            'success': True,
            'dados': dados_pedido,
            'parametros': parametros
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados de precificação: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def api_salvar_preco_negociado(request, pk):
    """
    API para salvar preço negociado pelo vendedor
    """
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Verificar se pode editar
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        return JsonResponse({
            'success': False,
            'error': mensagem
        })
    
    try:
        # Dados do POST
        data = json.loads(request.body)
        preco_negociado = data.get('preco_negociado')
        
        if not preco_negociado:
            return JsonResponse({
                'success': False,
                'error': 'Preço negociado é obrigatório'
            })
        
        # Converter para Decimal
        try:
            preco_negociado = Decimal(str(preco_negociado))
        except (InvalidOperation, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Preço inválido'
            })
        
        # Buscar parâmetros para validação de alçada
        try:
            from core.services.pricing import PricingService
            parametros = PricingService._get_parametros()
        except ImportError:
            parametros = {'desc.alcada1': 5.0}
            
        alcada_maxima = parametros.get('desc.alcada1', 5.0)
        
        # Calcular desconto
        preco_original = pedido.preco_venda_calculado or Decimal('0')
        if preco_original <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Pedido precisa ter preço calculado antes de negociar'
            })
        
        desconto = preco_original - preco_negociado
        percentual_desconto = (desconto / preco_original) * 100
        
        # Validar alçada
        if percentual_desconto > Decimal(str(alcada_maxima)):
            return JsonResponse({
                'success': False,
                'error': f'Desconto de {percentual_desconto:.1f}% está acima da alçada máxima de {alcada_maxima}%'
            })
        
        # Calcular preço com impostos (usando percentual do faturado_por)
        mapeamento_impostos = {
            'Elevadores': 10.0,
            'Fuza': 8.0, 
            'Manutenção': 5.0,
        }
        percentual_impostos = mapeamento_impostos.get(pedido.faturado_por, 10.0)
        preco_com_impostos = preco_negociado * (1 + percentual_impostos / 100)
        
        # Criar formação de preço simplificada
        nova_formacao = {
            'custo_producao': float(pedido.custo_producao or 0),
            'percentual_margem': 30.0,
            'valor_margem': float(pedido.custo_producao or 0) * 0.30,
            'percentual_desconto': float(percentual_desconto),
            'valor_desconto': float(desconto),
            'percentual_comissao': 3.0,
            'valor_comissao': float(preco_negociado) * 0.03,
            'preco_sem_impostos': float(preco_negociado),
            'percentual_impostos': percentual_impostos,
            'valor_impostos': float(preco_com_impostos - preco_negociado),
            'preco_com_impostos': float(preco_com_impostos)
        }
        
        # Salvar no pedido
        pedido.preco_negociado = preco_negociado
        pedido.preco_venda_final = preco_com_impostos
        pedido.percentual_desconto = percentual_desconto
        pedido.formacao_preco = nova_formacao
        pedido.atualizado_por = request.user
        pedido.save()
        
        # Registrar no histórico
        HistoricoPedido.objects.create(
            pedido=pedido,
            status_anterior=pedido.status,
            status_novo=pedido.status,
            observacao=f'Preço negociado: R$ {preco_negociado:,.2f} (desconto: {percentual_desconto:.1f}%)',
            usuario=request.user
        )
        
        logger.info(f"Preço negociado salvo para pedido {pedido.numero}:")
        logger.info(f"  - Preço original: R$ {preco_original:,.2f}")
        logger.info(f"  - Preço negociado: R$ {preco_negociado:,.2f}")
        logger.info(f"  - Desconto: {percentual_desconto:.1f}%")
        
        return JsonResponse({
            'success': True,
            'message': 'Preço salvo com sucesso',
            'dados': {
                'preco_negociado': float(preco_negociado),
                'preco_final': float(pedido.preco_venda_final),
                'percentual_desconto': float(percentual_desconto),
                'formacao_preco': nova_formacao
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar preço negociado: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })


