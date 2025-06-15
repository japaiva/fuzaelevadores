# ===============================================================================
# CORE/VIEWS/PROPOSTAS.PY - VIEWS BASE COMPARTILHADAS (SUBSTITUI TUDO ANTERIOR)
# ===============================================================================

import logging
import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.models import ParametrosGerais, Proposta, HistoricoProposta
from core.services.calculo_pedido import CalculoPedidoService

logger = logging.getLogger(__name__)

def safe_json_load(json_field):
    """Carrega JSONField de forma segura"""
    try:
        if isinstance(json_field, dict):
            return json_field
        return json.loads(json_field) if json_field else {}
    except:
        return {}

# ===============================================================================
# VIEW BASE PRINCIPAL
# ===============================================================================

def proposta_detail_base(request, pk, template_name, extra_context=None):
    """
    View base para detalhe de proposta 
    - Usada por vendedor/views.py e producao/views.py
    - Evita duplicação de código
    """
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # Filtro por permissão
    if user_level == 'vendedor':
        proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    else:
        proposta = get_object_or_404(Proposta, pk=pk)
    
    # Preparar dados JSON
    ficha_tecnica = safe_json_load(proposta.ficha_tecnica)
    dimensionamento = safe_json_load(proposta.dimensionamento_detalhado)
    formacao_preco = safe_json_load(proposta.formacao_preco)
    explicacao = proposta.explicacao_calculo or ''
    
    # Calcular áreas básicas
    area_poco = 0
    try:
        if proposta.largura_poco and proposta.comprimento_poco:
            area_poco = float(proposta.largura_poco) * float(proposta.comprimento_poco)
    except:
        pass
    
    # Contexto base
    context = {
        'proposta': proposta,
        'ficha_tecnica': ficha_tecnica,
        'dimensionamento': dimensionamento,
        'explicacao': explicacao,
        'formacao_preco': formacao_preco,
        'user_level': user_level,
        'area_poco': area_poco,
    }
    
    # Adicionar contexto específico
    if extra_context:
        context.update(extra_context)
    
    return render(request, template_name, context)

# ===============================================================================
# FUNÇÃO DE CÁLCULOS COMPARTILHADA
# ===============================================================================

def executar_calculos_proposta(proposta, user):
    """Executa cálculos - usada por vendedor e produção"""
    try:
        logger.info(f"Iniciando cálculos para proposta {proposta.numero}")
        
        resultado = CalculoPedidoService.calcular_custos_completo(proposta)
        
        if resultado['success']:
            proposta.refresh_from_db()
            
            # Histórico
            HistoricoProposta.objects.create(
                proposta=proposta,
                status_anterior=proposta.status,
                status_novo='simulado',
                observacao='Cálculos executados com sucesso',
                usuario=user
            )
            
            logger.info(f"Cálculos concluídos - Custo: {proposta.custo_producao}, Preço: {proposta.preco_venda_calculado}")
            return {'success': True, 'message': 'Cálculos executados com sucesso!'}
        else:
            return {'success': False, 'message': 'Erro nos cálculos.'}
            
    except Exception as e:
        logger.error(f"Erro ao calcular proposta {proposta.numero}: {str(e)}")
        return {'success': False, 'message': f'Erro: {str(e)}'}

# ===============================================================================
# APIS COMPARTILHADAS
# ===============================================================================

def api_dados_precificacao_base(request, pk):
    """API para dados de precificação - compartilhada entre portais"""
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # Buscar proposta com filtro correto
    if user_level == 'vendedor':
        proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    else:
        proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        parametros = ParametrosGerais.objects.first()
        if not parametros:
            return JsonResponse({'success': False, 'error': 'Parâmetros não encontrados'})
        
        # Impostos por tipo
        impostos = {
            'Elevadores': float(parametros.faturamento_elevadores or 10.0),
            'Fuza': float(parametros.faturamento_fuza or 8.0),
            'Manutenção': float(parametros.faturamento_manutencao or 5.0),
        }
        
        # Alçada por nível
        alcada = float(parametros.desconto_alcada_2 or 15.0 if user_level in ['admin', 'gestor'] 
                      else parametros.desconto_alcada_1 or 5.0)
        
        dados = {
            'custoProducao': float(proposta.custo_producao or 0),
            'percentualMargem': float(parametros.margem_padrao or 30.0),
            'percentualComissao': float(parametros.comissao_padrao or 3.0),
            'percentualImpostos': impostos.get(proposta.faturado_por, 10.0),
            'precoCalculado': float(proposta.preco_venda_calculado or 0),
            'precoNegociado': float(proposta.preco_negociado or proposta.preco_venda_calculado or 0),
            'alcadaMaxima': alcada,
            'userLevel': user_level,
        }
        
        return JsonResponse({'success': True, 'dados': dados, 'parametros': {
            'margem': float(parametros.margem_padrao or 30.0),
            'comissao': float(parametros.comissao_padrao or 3.0),
            'alcada1': float(parametros.desconto_alcada_1 or 5.0),
            'alcada2': float(parametros.desconto_alcada_2 or 15.0),
        }})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_salvar_preco_base(request, pk):
    """API para salvar preço - compartilhada entre portais"""
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # Buscar proposta
    if user_level == 'vendedor':
        proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    else:
        proposta = get_object_or_404(Proposta, pk=pk)
    
    # Validar permissão
    if user_level not in ['vendedor', 'gestor', 'admin']:
        return JsonResponse({'success': False, 'error': 'Sem permissão para alterar preços'})
    
    try:
        data = json.loads(request.body)
        preco_negociado = Decimal(str(data.get('preco_negociado')))
        
        parametros = ParametrosGerais.objects.first()
        if not parametros:
            return JsonResponse({'success': False, 'error': 'Parâmetros não encontrados'})
        
        # Validar alçada
        alcada = float(parametros.desconto_alcada_2 or 15.0 if user_level in ['admin', 'gestor'] 
                      else parametros.desconto_alcada_1 or 5.0)
        
        preco_original = proposta.preco_venda_calculado or Decimal('0')
        if preco_original <= 0:
            return JsonResponse({'success': False, 'error': 'Preço calculado não encontrado'})
        
        percentual_desconto = ((preco_original - preco_negociado) / preco_original) * 100
        
        if percentual_desconto > Decimal(str(alcada)):
            return JsonResponse({
                'success': False,
                'error': f'Desconto {percentual_desconto:.1f}% acima da alçada ({alcada}%)'
            })
        
        # Salvar
        proposta.preco_negociado = preco_negociado
        proposta.percentual_desconto = percentual_desconto
        proposta.atualizado_por = request.user
        proposta.save()
        
        # Histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=proposta.status,
            status_novo=proposta.status,
            observacao=f'Preço negociado: R$ {preco_negociado:,.2f} ({percentual_desconto:.1f}% desconto)',
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Preço salvo com sucesso',
            'dados': {
                'preco_negociado': float(preco_negociado),
                'percentual_desconto': float(percentual_desconto)
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ===============================================================================
# VENDEDOR/VIEWS.PY - REFATORADO E LIMPO
# ===============================================================================

"""
Views do portal do vendedor - usando as views base para evitar duplicação
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import Cliente, Proposta
from core.forms.propostas import (
    PropostaClienteElevadorForm, 
    PropostaCabinePortasForm,
    PropostaComercialForm,
    PropostaFiltroForm,
    ClienteCreateForm
)
from core.views.propostas import (
    proposta_detail_base,
    executar_calculos_proposta,
    api_dados_precificacao_base,
    api_salvar_preco_base
)

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Dashboard do vendedor"""
    propostas = Proposta.objects.filter(vendedor=request.user)
    
    stats = {
        'total': propostas.count(),
        'rascunho': propostas.filter(status='rascunho').count(),
        'simulado': propostas.filter(status='simulado').count(),
        'aprovado': propostas.filter(status='aprovado').count(),
    }
    
    propostas_recentes = propostas.order_by('-criado_em')[:5]
    
    return render(request, 'vendedor/dashboard.html', {
        'stats': stats,
        'propostas_recentes': propostas_recentes,
    })

@login_required
def proposta_list(request):
    """Lista de propostas do vendedor"""
    propostas_list = Proposta.objects.filter(vendedor=request.user).select_related('cliente').order_by('-criado_em')
    
    # Aplicar filtros simples
    form = PropostaFiltroForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('status'):
            propostas_list = propostas_list.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            propostas_list = propostas_list.filter(
                Q(numero__icontains=query) |
                Q(nome_projeto__icontains=query) |
                Q(cliente__nome__icontains=query)
            )
    
    # Paginação
    paginator = Paginator(propostas_list, 15)
    page = request.GET.get('page', 1)
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    return render(request, 'vendedor/proposta_list.html', {
        'propostas': propostas,
        'form': form,
    })

@login_required
def proposta_detail(request, pk):
    """Detalhes da proposta - usando view base"""
    extra_context = {
        'is_vendedor': True,
        'base_template': 'vendedor/base_vendedor.html',
    }
    return proposta_detail_base(request, pk, 'base/proposta_detail.html', extra_context)

# Workflow em 3 etapas
@login_required
def proposta_step1(request, pk=None):
    """Etapa 1: Cliente + Elevador + Poço"""
    if pk:
        proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
        editing = True
    else:
        proposta = None
        editing = False
    
    if request.method == 'POST':
        form = PropostaClienteElevadorForm(request.POST, instance=proposta)
        if form.is_valid():
            proposta = form.save(commit=False)
            if not editing:
                proposta.vendedor = request.user
                proposta.status = 'rascunho'
                # Valores padrão
                proposta.modelo_porta_cabine = 'Automática'
                proposta.material_porta_cabine = 'Inox'
                proposta.material_cabine = 'Inox 430'
                proposta.altura_cabine = 2.30
            
            proposta.atualizado_por = request.user
            proposta.save()
            
            return redirect('vendedor:proposta_step2', pk=proposta.pk)
    else:
        form = PropostaClienteElevadorForm(instance=proposta)
    
    return render(request, 'vendedor/proposta_step1.html', {
        'form': form,
        'proposta': proposta,
        'editing': editing,
    })

@login_required
def proposta_step2(request, pk):
    """Etapa 2: Cabine + Portas"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    if request.method == 'POST':
        form = PropostaCabinePortasForm(request.POST, instance=proposta)
        if form.is_valid():
            proposta = form.save(commit=False)
            proposta.atualizado_por = request.user
            proposta.save()
            
            # Executar cálculos automáticos
            resultado = executar_calculos_proposta(proposta, request.user)
            if resultado['success']:
                messages.success(request, resultado['message'])
            else:
                messages.warning(request, f"Proposta salva, mas {resultado['message']}")
            
            return redirect('vendedor:proposta_step3', pk=proposta.pk)
    else:
        form = PropostaCabinePortasForm(instance=proposta)
    
    return render(request, 'vendedor/proposta_step2.html', {
        'form': form,
        'proposta': proposta,
    })

@login_required 
def proposta_step3(request, pk):
    """Etapa 3: Dados Comerciais - NOVA ETAPA"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    if request.method == 'POST':
        form = PropostaComercialForm(request.POST, instance=proposta)
        if form.is_valid():
            proposta = form.save(commit=False)
            proposta.atualizado_por = request.user
            proposta.save()
            
            messages.success(request, 'Dados comerciais salvos com sucesso!')
            return redirect('vendedor:proposta_detail', pk=proposta.pk)
    else:
        form = PropostaComercialForm(instance=proposta)
    
    return render(request, 'vendedor/proposta_step3.html', {
        'form': form,
        'proposta': proposta,
    })

@login_required
def proposta_calcular(request, pk):
    """Calcular proposta manualmente"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    if not proposta.pode_calcular():
        messages.error(request, 'Proposta não tem dados suficientes para cálculo.')
        return redirect('vendedor:proposta_step1', pk=proposta.pk)
    
    resultado = executar_calculos_proposta(proposta, request.user)
    
    if resultado['success']:
        messages.success(request, resultado['message'])
        if proposta.custo_producao:
            messages.info(request, f"Custo: R$ {proposta.custo_producao:,.2f}")
        if proposta.preco_venda_calculado:
            messages.info(request, f"Preço: R$ {proposta.preco_venda_calculado:,.2f}")
    else:
        messages.error(request, resultado['message'])
    
    return redirect('vendedor:proposta_detail', pk=proposta.pk)

# APIs - delegando para as funções base
@login_required
def api_dados_precificacao(request, pk):
    return api_dados_precificacao_base(request, pk)

@login_required
@require_POST
def api_salvar_preco_negociado(request, pk):
    return api_salvar_preco_base(request, pk)

# ===============================================================================
# PRODUCAO/VIEWS.PY - SIMPLES E FOCADO
# ===============================================================================

"""
Views do portal da produção - usando as views base
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from core.models import Proposta, HistoricoProposta
from core.views.propostas import (
    proposta_detail_base,
    api_dados_precificacao_base,
    api_salvar_preco_base
)

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Dashboard da produção"""
    propostas_producao = Proposta.objects.filter(
        status__in=['aprovado', 'em_producao']
    ).select_related('cliente', 'vendedor').order_by('-criado_em')[:10]
    
    stats = {
        'aprovadas': Proposta.objects.filter(status='aprovado').count(),
        'em_producao': Proposta.objects.filter(status='em_producao').count(),
        'concluidas': Proposta.objects.filter(status='concluido').count(),
    }
    
    return render(request, 'producao/dashboard.html', {
        'stats': stats,
        'propostas_producao': propostas_producao,
    })

@login_required
def proposta_list(request):
    """Lista de propostas para produção"""
    propostas_list = Proposta.objects.filter(
        status__in=['proposta_gerada', 'enviado_cliente', 'aprovado', 'em_producao', 'concluido']
    ).select_related('cliente', 'vendedor').order_by('-atualizado_em')
    
    # Filtros básicos
    status_filter = request.GET.get('status')
    search = request.GET.get('q')
    
    if status_filter:
        propostas_list = propostas_list.filter(status=status_filter)
    
    if search:
        propostas_list = propostas_list.filter(
            Q(numero__icontains=search) |
            Q(nome_projeto__icontains=search) |
            Q(cliente__nome__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(propostas_list, 20)
    page = request.GET.get('page', 1)
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    return render(request, 'producao/proposta_list.html', {
        'propostas': propostas,
        'status_filter': status_filter,
        'search': search,
    })

@login_required
def proposta_detail(request, pk):
    """Detalhes da proposta para produção - usando view base"""
    extra_context = {
        'is_producao': True,
        'pode_alterar_status': True,
        'pode_ver_custos': True,
        'base_template': 'producao/base_producao.html',
    }
    return proposta_detail_base(request, pk, 'base/proposta_detail.html', extra_context)

@login_required
@require_POST
def alterar_status_proposta(request, pk):
    """Alterar status da proposta"""
    proposta = get_object_or_404(Proposta, pk=pk)
    
    novo_status = request.POST.get('status')
    observacao = request.POST.get('observacao', '')
    
    # Validar transições permitidas para produção
    transicoes_validas = {
        'aprovado': ['em_producao'],
        'em_producao': ['concluido', 'aprovado'],
    }
    
    if proposta.status not in transicoes_validas:
        messages.error(request, f'Status {proposta.get_status_display()} não pode ser alterado pela produção.')
        return redirect('producao:proposta_detail', pk=pk)
    
    if novo_status not in transicoes_validas[proposta.status]:
        messages.error(request, 'Transição de status inválida.')
        return redirect('producao:proposta_detail', pk=pk)
    
    try:
        # Alterar status
        status_anterior = proposta.status
        proposta.status = novo_status
        proposta.atualizado_por = request.user
        proposta.save()
        
        # Histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=status_anterior,
            status_novo=novo_status,
            observacao=observacao or f'Status alterado pela produção',
            usuario=request.user
        )
        
        messages.success(request, f'Status alterado para {proposta.get_status_display()} com sucesso!')
        
    except Exception as e:
        logger.error(f"Erro ao alterar status da proposta {proposta.numero}: {str(e)}")
        messages.error(request, f'Erro ao alterar status: {str(e)}')
    
    return redirect('producao:proposta_detail', pk=pk)

# APIs - reutilizando as funções base
@login_required
def api_dados_precificacao(request, pk):
    return api_dados_precificacao_base(request, pk)

@login_required
@require_POST  
def api_salvar_preco_negociado(request, pk):
    # Só gestores podem alterar preço na produção
    user_level = getattr(request.user, 'nivel', 'producao')
    if user_level not in ['gestor', 'admin']:
        return JsonResponse({
            'success': False, 
            'error': 'Apenas gestores podem alterar preços na produção'
        })
    return api_salvar_preco_base(request, pk)