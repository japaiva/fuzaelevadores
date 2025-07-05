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

from core.models import Proposta, HistoricoProposta,ParametrosGerais 
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

# core/views/propostas.py - ATUALIZAR proposta_detail_base

def proposta_detail_base(request, pk, template_name, extra_context=None):
    """
    View base para detalhe de proposta 
    - Usada por vendedor/views.py e producao/views.py
    - ✅ ATUALIZADA: Inclui parâmetros para impostos dinâmicos
    """
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # ✅ CARREGAR PARÂMETROS PARA IMPOSTOS DINÂMICOS
    from core.models import ParametrosGerais
    parametros = ParametrosGerais.objects.first()
    
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
        'parametros': parametros,  # ✅ ADICIONADO: Para impostos dinâmicos
    }
    
    # Adicionar contexto específico (vendedor/produção)
    if extra_context:
        context.update(extra_context)
    
    return render(request, template_name, context)
