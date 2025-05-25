# vendedor/views.py - VERSÃO 2 ETAPAS

import logging
from datetime import datetime, timedelta
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

# IMPORTS CORRIGIDOS - usando os services do core
from core.services.dimensionamento import DimensionamentoService
from core.services.pricing import PricingService
from core.utils.formatters import extrair_especificacoes_do_pedido, agrupar_respostas_por_pagina, safe_decimal, safe_int

from .models import Pedido, HistoricoPedido, AnexoPedido
from .forms import (
    PedidoClienteElevadorForm, PedidoCabinePortasForm, 
    AnexoPedidoForm, PedidoFiltroForm, ClienteCreateForm
)

from .utils import validar_permissoes_vendedor, calcular_estatisticas_vendedor
from core.models import Cliente

logger = logging.getLogger(__name__)

# =============================================================================
# DASHBOARD E PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial do vendedor"""
    # Estatísticas básicas
    dados_stats = calcular_estatisticas_vendedor(request.user)
    
    # Pedidos recentes
    pedidos_recentes = Pedido.objects.filter(vendedor=request.user).order_by('-criado_em')[:5]
    
    # Status para cards
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
    # Usar função utilitária para calcular estatísticas
    dados_stats = calcular_estatisticas_vendedor(request.user)
    
    # Pedidos recentes
    pedidos_recentes = Pedido.objects.filter(vendedor=request.user).order_by('-criado_em')[:5]
    
    context = {
        **dados_stats['stats'],
        'stats_status': dados_stats['stats_status'],
        'stats_modelo': dados_stats['stats_modelo'], 
        'pedidos_recentes': pedidos_recentes,
    }
    return render(request, 'vendedor/dashboard.html', context)


# =============================================================================
# WORKFLOW DO PEDIDO EM 2 ETAPAS
# =============================================================================

@login_required
def pedido_edit(request, pk):
    """Editar pedido existente - redireciona para step 1"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    # Redirecionar para o primeiro passo (agora unificado)
    return redirect('vendedor:pedido_step1', pk=pedido.pk)


@login_required
def pedido_step1(request, pk=None):
    """Etapa 1: Cliente + Elevador + Poço - UNIFICADO"""
    
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
                    
                    # Definir valores padrão para campos da segunda etapa
                    # Dados das portas padrão
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
                    
                    # Dados da cabine padrão
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
                    
                    messages.success(request, f'Pedido {pedido.numero} criado com sucesso.')
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
    """Etapa 2: Cabine + Portas - UNIFICADO com cálculos"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Validar permissões
    pode_editar, mensagem = validar_permissoes_vendedor(request.user, pedido)
    if not pode_editar:
        messages.error(request, mensagem)
        return redirect('vendedor:pedido_detail', pk=pedido.pk)
    
    editing = pedido.status != 'rascunho' or bool(pedido.preco_venda_calculado)
    
    if request.method == 'POST':
        form = PedidoCabinePortasForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            
            # EXECUTAR CÁLCULOS AUTOMÁTICOS
            try:
                especificacoes = extrair_especificacoes_do_pedido(pedido)
                dimensionamento, explicacao = DimensionamentoService.calcular_dimensionamento_completo(especificacoes)
                
                if 'cab' in dimensionamento:
                    pedido.largura_cabine_calculada = dimensionamento['cab']['largura']
                    pedido.comprimento_cabine_calculado = dimensionamento['cab']['compr']
                    pedido.capacidade_cabine_calculada = dimensionamento['cab']['capacidade']
                    pedido.tracao_cabine_calculada = dimensionamento['cab']['tracao']
                
                pedido.dimensionamento_detalhado = dimensionamento
                pedido.explicacao_calculo = explicacao
                
                # Calcular preços
                custo_base = 15000.0
                formacao_preco = PricingService.calcular_formacao_preco(custo_base, pedido.faturado_por)
                
                pedido.custo_producao = custo_base
                pedido.preco_venda_calculado = formacao_preco['preco_sem_impostos']
                pedido.formacao_preco = formacao_preco
                
                # Atualizar status para simulado
                if pedido.status == 'rascunho':
                    pedido.status = 'simulado'
                
                logger.info(f"Cálculos executados com sucesso para pedido {pedido.numero}")
                
            except Exception as e:
                logger.error(f"Erro ao calcular dimensionamento: {str(e)}")
                messages.warning(request, 'Houve um problema nos cálculos.')
            
            pedido.atualizado_por = request.user
            pedido.save()
            
            # Registrar no histórico
            HistoricoPedido.objects.create(
                pedido=pedido,
                status_anterior='rascunho',
                status_novo=pedido.status,
                observacao='Pedido finalizado com cálculos automáticos',
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
# GESTÃO DE PEDIDOS - MANTÉM IGUAL
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
    """Detalhes do pedido - VERSÃO UNIFICADA (antigo detail + resumo)"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Extrair especificações para exibição (se houver)
    especificacoes = {}
    if pedido.cliente:  # Só tenta extrair se tem dados básicos
        try:
            especificacoes = extrair_especificacoes_do_pedido(pedido)
        except Exception as e:
            logger.warning(f"Erro ao extrair especificações do pedido {pedido.numero}: {str(e)}")
    
    # Usar dados já calculados e salvos no pedido
    dimensionamento = pedido.dimensionamento_detalhado or {}
    formacao_preco = pedido.formacao_preco or {}
    explicacao = pedido.explicacao_calculo or ''
    
    # Calcular áreas e volumes para exibição
    area_poco = 0
    volume_poco = 0
    area_cabine = 0
    
    if pedido.largura_poco and pedido.comprimento_poco:
        area_poco = float(pedido.largura_poco) * float(pedido.comprimento_poco)
        
        if pedido.altura_poco:
            volume_poco = area_poco * float(pedido.altura_poco)
    
    if pedido.largura_cabine_calculada and pedido.comprimento_cabine_calculado:
        area_cabine = float(pedido.largura_cabine_calculada) * float(pedido.comprimento_cabine_calculado)
    
    # Histórico do pedido
    historico = pedido.historico.all()[:10]
    
    # Anexos do pedido
    anexos = pedido.anexos.all().order_by('-enviado_em')
    
    # Determinar nível do usuário para exibir dados
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    context = {
        'pedido': pedido,
        'especificacoes': especificacoes,
        'dimensionamento': dimensionamento,
        'explicacao': explicacao,
        'formacao_preco': formacao_preco,
        'historico': historico,
        'anexos': anexos,
        'user_level': user_level,
        # Valores calculados para o template
        'area_poco': area_poco,
        'volume_poco': volume_poco,
        'area_cabine': area_cabine,
    }
    
    return render(request, 'vendedor/pedido_detail.html', context)


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
# APIS AJAX - MANTÉM IGUAL
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
# VIEWS TEMPORÁRIAS
# =============================================================================

@login_required
def gerar_pdf_orcamento(request, pk):
    """Gerar PDF do orçamento"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    messages.info(request, 'Geração de PDF em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def gerar_pdf_demonstrativo(request, pk):
    """Gerar PDF da proposta técnica"""
    pedido = get_object_or_404(Pedido, pk=pk, vendedor=request.user)
    
    # Verificar permissão para dados técnicos
    if getattr(request.user, 'nivel', 'vendedor') not in ['admin', 'engenharia']:
        messages.error(request, 'Você não tem permissão para acessar dados técnicos.')
        return redirect('vendedor:pedido_detail', pk=pk)
    
    messages.info(request, 'Geração de PDF em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def pedido_change_status(request, pk):
    messages.info(request, 'Funcionalidade em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required  
def pedido_anexo_upload(request, pk):
    messages.info(request, 'Funcionalidade em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)


@login_required
def pedido_anexo_delete(request, pk, anexo_id):
    messages.info(request, 'Funcionalidade em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)

