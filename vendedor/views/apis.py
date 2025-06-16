# vendedor/views/apis.py

"""
APIs AJAX para o portal do vendedor
NOVA FUNCIONALIDADE: API para calcular preço no Step 3
"""

import json
import logging
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.models import Proposta, Cliente, Usuario

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def api_dados_precificacao(request, pk):
    """
    API para carregar dados de precificação da proposta
    ATUALIZADA: Novos campos de valor
    """
    try:
        # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode acessar
        proposta = get_object_or_404(Proposta, pk=pk)
        
        dados = {
            'success': True,
            'dados': {
                # === NOVOS CAMPOS ===
                'valorCalculado': float(proposta.valor_calculado or 0),
                'valorBase': float(proposta.valor_base or 0),
                'valorProposta': float(proposta.valor_proposta or 0),
                
                # === CAMPOS MANTIDOS PARA COMPATIBILIDADE ===
                'precoCalculado': float(proposta.valor_calculado or 0),  # Compatibilidade
                'precoNegociado': float(proposta.valor_proposta or 0),   # Compatibilidade
                
                # Dados da proposta
                'numero': proposta.numero,
                'status': proposta.status,
                'cliente': proposta.cliente.nome,
                'modelo': proposta.get_modelo_elevador_display(),
                'capacidade': float(proposta.capacidade),
                
                # Custos detalhados
                'custoProducao': float(proposta.custo_producao or 0),
                'custoMateriais': float(proposta.custo_materiais or 0),
                'custoMaoObra': float(proposta.custo_mao_obra or 0),
                'custoInstalacao': float(proposta.custo_instalacao or 0),
                
                # Percentuais (simulados - futuramente vir do motor de regras)
                'percentualMargem': 30.0,
                'percentualComissao': 3.0,
                'percentualImpostos': 10.0,
                
                # Alçada do usuário (simulado - futuramente vir das permissões)
                'alcadaMaxima': 15.0,  # 15% de desconto máximo
                
                # Capacidades da proposta
                'podeCalcular': proposta.pode_calcular,
                'podeEditar': proposta.pode_editar,
                'temCalculos': proposta.tem_calculos,
            }
        }
        
        return JsonResponse(dados)
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados de precificação da proposta {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_salvar_preco_negociado(request, pk):
    """
    API para salvar preço negociado da proposta
    ATUALIZADA: Usar valor_proposta em vez de preco_negociado
    """
    try:
        # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode salvar
        proposta = get_object_or_404(Proposta, pk=pk)
        
        if not proposta.pode_editar:
            return JsonResponse({
                'success': False,
                'error': 'Proposta não pode ser editada'
            }, status=403)
        
        # Obter dados do request
        if request.content_type == 'application/json':
            dados = json.loads(request.body)
        else:
            dados = request.POST
        
        # === NOVA LÓGICA: valor_proposta ===
        if 'valor_proposta' in dados:
            valor_proposta = Decimal(str(dados['valor_proposta']))
        elif 'preco_negociado' in dados:  # Compatibilidade
            valor_proposta = Decimal(str(dados['preco_negociado']))
        else:
            return JsonResponse({
                'success': False,
                'error': 'Valor da proposta não informado'
            }, status=400)
        
        if valor_proposta < 0:
            return JsonResponse({
                'success': False,
                'error': 'Valor da proposta não pode ser negativo'
            }, status=400)
        
        # Atualizar proposta
        proposta.valor_proposta = valor_proposta
        
        # Se valor_base não existe, usar valor_calculado
        if not proposta.valor_base and proposta.valor_calculado:
            proposta.valor_base = proposta.valor_calculado
        
        # Atualizar status se necessário
        if proposta.status == 'rascunho' and valor_proposta > 0:
            proposta.status = 'pendente'
        
        proposta.save()
        
        # Log da ação
        logger.info(
            f"Valor da proposta {proposta.numero} atualizado para R$ {valor_proposta:.2f} "
            f"pelo usuário {request.user.username}"
        )
        
        # Calcular informações adicionais
        desconto_aplicado = 0
        if proposta.valor_base and proposta.valor_base > 0:
            desconto_aplicado = ((proposta.valor_base - valor_proposta) / proposta.valor_base) * 100
        
        return JsonResponse({
            'success': True,
            'data': {
                'valorProposta': float(valor_proposta),
                'valorBase': float(proposta.valor_base or 0),
                'descontoAplicado': max(0, desconto_aplicado),
                'status': proposta.status,
                'statusDisplay': proposta.get_status_display(),
            }
        })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'error': 'Valor inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao salvar preço da proposta {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_calcular_preco(request, pk):
    """
    API para calcular preço base da proposta via botão no Step 3
    NOVA FUNCIONALIDADE
    """
    try:
        # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode calcular
        proposta = get_object_or_404(Proposta, pk=pk)
        
        if not proposta.pode_calcular:
            return JsonResponse({
                'success': False,
                'error': 'Proposta não pode ter valores calculados'
            }, status=403)
        
        # Verificar se proposta possui dados suficientes
        if not proposta.pode_calcular_valores():
            return JsonResponse({
                'success': False,
                'error': 'Proposta não possui dados suficientes para cálculo. Verifique se todos os campos obrigatórios estão preenchidos.'
            }, status=400)
        
        # === LÓGICA DE CÁLCULO ===
        # TODO: Implementar motor de regras real
        # Por enquanto, cálculo simulado baseado na capacidade
        
        try:
            # Valor base por kg
            valor_por_kg = 150  # R$ 150 por kg
            
            # Cálculo inicial
            valor_base_simulado = float(proposta.capacidade) * valor_por_kg
            
            # Multiplicadores por modelo
            multiplicadores = {
                'Passageiro': 1.2,
                'Carga': 1.0,
                'Monta Prato': 0.8,
                'Plataforma Acessibilidade': 1.5,
            }
            
            multiplicador = multiplicadores.get(proposta.modelo_elevador, 1.0)
            
            # Ajustes por acionamento
            if proposta.acionamento == 'Hidraulico':
                multiplicador *= 1.1
            elif proposta.acionamento == 'Motor':
                multiplicador *= 1.3
            elif proposta.acionamento == 'Carretel':
                multiplicador *= 1.0
            
            # Ajustes por número de pavimentos
            if proposta.pavimentos > 5:
                multiplicador *= 1 + (proposta.pavimentos - 5) * 0.05
            
            # Valor calculado final
            valor_calculado = Decimal(str(valor_base_simulado * multiplicador))
            
            # Simular custos detalhados
            custo_materiais = valor_calculado * Decimal('0.4')  # 40% materiais
            custo_mao_obra = valor_calculado * Decimal('0.25')  # 25% mão de obra
            custo_instalacao = valor_calculado * Decimal('0.15')  # 15% instalação
            custo_producao = custo_materiais + custo_mao_obra + custo_instalacao
            
            # Atualizar proposta
            proposta.valor_calculado = valor_calculado
            proposta.custo_producao = custo_producao
            proposta.custo_materiais = custo_materiais
            proposta.custo_mao_obra = custo_mao_obra
            proposta.custo_instalacao = custo_instalacao
            
            # Se valor_base não existe, usar o calculado
            if not proposta.valor_base:
                proposta.valor_base = valor_calculado
            
            # Se valor_proposta não existe, usar valor_base
            if not proposta.valor_proposta:
                proposta.valor_proposta = proposta.valor_base
            
            proposta.save()
            
            # Log da ação
            logger.info(
                f"Preço calculado para proposta {proposta.numero}: "
                f"R$ {valor_calculado:.2f} (custo: R$ {custo_producao:.2f})"
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'valorCalculado': float(valor_calculado),
                    'valorBase': float(proposta.valor_base),
                    'valorProposta': float(proposta.valor_proposta or 0),
                    'custoProducao': float(custo_producao),
                    'custoMateriais': float(custo_materiais),
                    'custoMaoObra': float(custo_mao_obra),
                    'custoInstalacao': float(custo_instalacao),
                    'explicacao': f"Cálculo baseado em {proposta.capacidade}kg × R$ {valor_por_kg}/kg × {multiplicador:.2f} (multiplicador)"
                }
            })
            
        except Exception as calc_error:
            logger.error(f"Erro no cálculo da proposta {proposta.numero}: {str(calc_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Erro no cálculo: {str(calc_error)}'
            }, status=500)
        
    except Exception as e:
        logger.error(f"Erro geral ao calcular proposta {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_cliente_info(request, cliente_id):
    """
    API para carregar informações do cliente
    """
    try:
        cliente = get_object_or_404(Cliente, pk=cliente_id, ativo=True)
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'nome_fantasia': cliente.nome_fantasia,
                'tipo_pessoa': cliente.tipo_pessoa,
                'cpf_cnpj': cliente.cpf_cnpj,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'endereco': cliente.endereco,
                'cidade': cliente.cidade,
                'estado': cliente.estado,
                'cep': cliente.cep,
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao carregar cliente {cliente_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def cliente_create_ajax(request):
    """
    API para criar cliente via modal AJAX
    """
    if request.method == 'GET':
        # Retornar formulário HTML
        from core.forms.propostas import ClienteCreateForm
        form = ClienteCreateForm()
        
        # Render do formulário como HTML
        from django.template.loader import render_to_string
        html = render_to_string('vendedor/cliente_create_form.html', {
            'form': form
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    
    elif request.method == 'POST':
        from core.forms.propostas import ClienteCreateForm
        form = ClienteCreateForm(request.POST)
        
        if form.is_valid():
            try:
                cliente = form.save()
                
                logger.info(f"Cliente {cliente.nome} criado via AJAX pelo usuário {request.user.username}")
                
                return JsonResponse({
                    'success': True,
                    'cliente': {
                        'id': cliente.id,
                        'nome': cliente.nome,
                        'nome_fantasia': cliente.nome_fantasia,
                    }
                })
                
            except Exception as e:
                logger.error(f"Erro ao salvar cliente via AJAX: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })


# === FUNÇÕES AUXILIARES ===

def _formatar_valor_brasileiro(valor):
    """Formatar valor para padrão brasileiro"""
    if not valor:
        return "0,00"
    return f"{float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _validar_desconto_usuario(usuario, percentual_desconto):
    """
    Validar se usuário pode aplicar o desconto
    TODO: Implementar sistema de alçadas real
    """
    # Simulação de alçadas por nível de usuário
    alcadas = {
        'vendedor': 10.0,
        'supervisor': 20.0,
        'gerente': 35.0,
        'diretor': 50.0,
    }
    
    nivel_usuario = getattr(usuario, 'nivel', 'vendedor')
    alcada_maxima = alcadas.get(nivel_usuario, 5.0)
    
    return percentual_desconto <= alcada_maxima, alcada_maxima