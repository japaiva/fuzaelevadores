# core/views/propostas.py - APENAS FUNÇÕES BASE COMPARTILHADAS

"""
CORE Views - APENAS funções base compartilhadas entre vendedor e produção
Remove duplicação e mantém apenas o essencial
"""

import logging
import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.models import ParametrosGerais, Proposta, HistoricoProposta

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
# VIEW BASE PRINCIPAL - COMPARTILHADA
# ===============================================================================

def proposta_detail_base(request, pk, template_name, extra_context=None):
    """
    View base para detalhe de proposta 
    - Usada por vendedor/views.py e producao/views.py
    - Evita duplicação de código
    """
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # 🎯 SEM FILTROS - deixa para as views específicas decidirem
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
    
    # Contexto base mínimo
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade com templates antigos
        'ficha_tecnica': ficha_tecnica,
        'dimensionamento': dimensionamento,
        'explicacao': explicacao,
        'formacao_preco': formacao_preco,
        'user_level': user_level,
        'area_poco': area_poco,
    }
    
    # Adicionar contexto específico (vendedor/produção)
    if extra_context:
        context.update(extra_context)
    
    return render(request, template_name, context)

# ===============================================================================
# FUNÇÃO DE CÁLCULOS COMPARTILHADA
# ===============================================================================

def executar_calculos_proposta(proposta, user):
    """
    Executa cálculos - usada por vendedor e produção
    TODO: Implementar motor de regras real
    """
    try:
        logger.info(f"Iniciando cálculos para proposta {proposta.numero}")
        
        # Simulação de cálculo (substitua pela lógica real)
        valor_por_kg = 150
        valor_base = float(proposta.capacidade) * valor_por_kg
        
        multiplicadores = {
            'Passageiro': 1.2,
            'Carga': 1.0,
            'Monta Prato': 0.8,
            'Plataforma Acessibilidade': 1.5,
        }
        
        multiplicador = multiplicadores.get(proposta.modelo_elevador, 1.0)
        valor_calculado = Decimal(str(valor_base * multiplicador))
        
        # Simular custos
        custo_materiais = valor_calculado * Decimal('0.4')
        custo_mao_obra = valor_calculado * Decimal('0.25') 
        custo_instalacao = valor_calculado * Decimal('0.15')
        custo_producao = custo_materiais + custo_mao_obra + custo_instalacao
        
        # Atualizar proposta
        proposta.preco_venda_calculado = valor_calculado  # Campo antigo
        proposta.valor_calculado = valor_calculado  # Campo novo
        proposta.custo_producao = custo_producao
        proposta.custo_materiais = custo_materiais
        proposta.custo_mao_obra = custo_mao_obra
        proposta.custo_instalacao = custo_instalacao
        
        if not proposta.valor_base:
            proposta.valor_base = valor_calculado
            
        proposta.status = 'simulado'
        proposta.save()
        
        # Histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior='rascunho',
            status_novo='simulado',
            observacao='Cálculos executados com sucesso',
            usuario=user
        )
        
        logger.info(f"Cálculos concluídos - Custo: {proposta.custo_producao}, Preço: {proposta.preco_venda_calculado}")
        return {'success': True, 'message': 'Cálculos executados com sucesso!'}
        
    except Exception as e:
        logger.error(f"Erro ao calcular proposta {proposta.numero}: {str(e)}")
        return {'success': False, 'message': f'Erro: {str(e)}'}

# ===============================================================================
# APIS BASE COMPARTILHADAS
# ===============================================================================

def api_dados_precificacao_base(request, pk):
    """API para dados de precificação - compartilhada entre portais"""
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # 🎯 SEM FILTROS - deixa para as views específicas decidirem
    proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        parametros = ParametrosGerais.objects.first()
        if not parametros:
            return JsonResponse({'success': False, 'error': 'Parâmetros não encontrados'})
        
        # Alçada por nível
        alcada = float(parametros.desconto_alcada_2 or 15.0 if user_level in ['admin', 'gestor'] 
                      else parametros.desconto_alcada_1 or 5.0)
        
        dados = {
            'custoProducao': float(proposta.custo_producao or 0),
            'percentualMargem': float(parametros.margem_padrao or 30.0),
            'percentualComissao': float(parametros.comissao_padrao or 3.0),
            'percentualImpostos': 10.0,  # Simplificado
            'precoCalculado': float(proposta.preco_venda_calculado or 0),
            'precoNegociado': float(proposta.preco_negociado or 0),
            'alcadaMaxima': alcada,
            'userLevel': user_level,
        }
        
        return JsonResponse({'success': True, 'dados': dados})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_salvar_preco_base(request, pk):
    """API para salvar preço - compartilhada entre portais"""
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    # 🎯 SEM FILTROS - deixa para as views específicas decidirem
    proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        data = json.loads(request.body)
        preco_negociado = Decimal(str(data.get('preco_negociado')))
        
        # Validação básica
        if preco_negociado < 0:
            return JsonResponse({'success': False, 'error': 'Valor não pode ser negativo'})
        
        # Salvar
        proposta.preco_negociado = preco_negociado
        proposta.save()
        
        # Histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=proposta.status,
            status_novo=proposta.status,
            observacao=f'Preço negociado: R$ {preco_negociado:,.2f}',
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Preço salvo com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})