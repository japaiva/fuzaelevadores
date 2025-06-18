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
from core.services.calculo_pedido import CalculoPedidoService # Import the full calculation service
from core.services.pricing import PricingService # Import PricingService for parameters

logger = logging.getLogger(__name__)

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
    CORRIGIDA: Retorna HTML direto no GET
    """
    if request.method == 'GET':
        # Retornar formulário HTML diretamente
        from core.forms.clientes import ClienteCreateForm
        form = ClienteCreateForm()
        
        # Render do template como HTML direto
        from django.template.loader import render_to_string
        html = render_to_string('vendedor/cliente_create_modal.html', {
            'form': form
        }, request=request)
        
        # 🎯 MUDANÇA: Retorna HttpResponse com HTML, não JSON
        from django.http import HttpResponse
        return HttpResponse(html)
    
    elif request.method == 'POST':
        from core.forms.clientes import ClienteCreateForm
        form = ClienteCreateForm(request.POST)
        
        if form.is_valid():
            try:
                cliente = form.save(commit=False)
                cliente.criado_por = request.user  # Definir quem criou
                cliente.save()
                
                logger.info(f"Cliente {cliente.nome} criado via AJAX pelo usuário {request.user.username}")
                
                return JsonResponse({
                    'success': True,
                    'cliente': {
                        'id': cliente.id,
                        'nome': cliente.nome,
                        'nome_fantasia': cliente.nome_fantasia or '',
                        'tipo_pessoa': cliente.get_tipo_pessoa_display(),
                    }
                })
                
            except Exception as e:
                logger.error(f"Erro ao salvar cliente via AJAX: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                }, status=500)
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)


@login_required
@require_http_methods(["GET"])
def api_dados_precificacao(request, pk):
    """
    API para carregar dados de precificação da proposta
    CORRIGIDA: Usar campos corretos do modelo
    """
    try:
        proposta = get_object_or_404(Proposta, pk=pk)
        
        # Retrieve dynamic pricing parameters using the service
        parametros_precificacao = PricingService._get_parametros()

        dados = {
            'success': True,
            'dados': {
                # preco_venda_calculado is the single calculated price
                'valorCalculado': float(proposta.preco_venda_calculado or 0),
                # valorProposta is the user-negotiated value
                'valorProposta': float(proposta.valor_proposta or 0),
                
                # === CAMPOS MANTIDOS PARA COMPATIBILIDADE (eventually remove) ===
                'precoCalculado': float(proposta.preco_venda_calculado or 0),
                'precoNegociado': float(proposta.valor_proposta or 0),
                
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
                
                # Percentuais (agora vêm do PricingService)
                'percentualMargem': parametros_precificacao.get('margem', 30.0),
                'percentualComissao': parametros_precificacao.get('comissao', 3.0),
                'percentualImpostos': parametros_precificacao.get(f'fat.{proposta.faturado_por}', 10.0),
                
                # Alçada do usuário
                'alcadaMaxima': parametros_precificacao.get('desc.alcada1', 5.0),
                
                # Capacidades da proposta
                'podeCalcular': proposta.pode_calcular(),
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
    CORRIGIDA: Usar valor_proposta (campo correto)
    """
    try:
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
        
        # ✅ CORRIGIDA: Usar valor_proposta (campo que existe)
        if 'valor_proposta' in dados:
            valor_proposta = Decimal(str(dados['valor_proposta']))
        elif 'preco_negociado' in dados:  # Compatibilidade, will be removed
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
        
        # The 'base' for discount calculation is now preco_venda_calculado.
        # This field is set by api_calcular_preco.
        # We don't set preco_sem_impostos anymore as it was removed.
        
        # Atualizar status se necessário
        if proposta.status == 'rascunho' and valor_proposta > Decimal('0'):
            proposta.status = 'pendente'
        
        proposta.save()
        
        # Log da ação
        logger.info(
            f"Valor da proposta {proposta.numero} atualizado para R$ {valor_proposta:.2f} "
            f"pelo usuário {request.user.username}"
        )
        
        # ✅ CORRIGIDA: Calcular informações adicionais usando campos corretos
        desconto_aplicado = Decimal('0')
        # Calculate discount against preco_venda_calculado
        if proposta.preco_venda_calculado and proposta.preco_venda_calculado > Decimal('0'):
            desconto_aplicado = ((proposta.preco_venda_calculado - valor_proposta) / proposta.preco_venda_calculado) * 100
        
        return JsonResponse({
            'success': True,
            'data': {
                'valorProposta': float(valor_proposta),
                'valorCalculado': float(proposta.preco_venda_calculado or 0), # Now explicitly returning preco_venda_calculado as 'base'
                'descontoAplicado': max(0, float(desconto_aplicado)),
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
    CORRIGIDA: Usar CalculoPedidoService para cálculo completo
    """
    try:
        proposta = get_object_or_404(Proposta, pk=pk)
        
        if not proposta.pode_calcular():
            return JsonResponse({
                'success': False,
                'error': 'Proposta não possui dados suficientes para cálculo. Por favor, preencha as informações do elevador (Step 1 e 2).'
            }, status=400) # Changed status to 400 as it's a client-side data issue, not a server error
        
        # === LÓGICA DE CÁLCULO: INVOCAÇÃO DO SERVIÇO COMPLETO ===
        try:
            # Calling the comprehensive calculation service
            calculo_resultado = CalculoPedidoService.calcular_custos_completo(proposta) #

            # After calculation, reload the proposal to get the latest saved values
            proposta.refresh_from_db()

            # Prepare the response data
            valor_calculado = proposta.preco_venda_calculado or Decimal('0')
            custo_producao = proposta.custo_producao or Decimal('0')
            custo_materiais = proposta.custo_materiais or Decimal('0')
            custo_mao_obra = proposta.custo_mao_obra or Decimal('0')
            custo_instalacao = proposta.custo_instalacao or Decimal('0')
            valor_proposta_final = proposta.valor_proposta or Decimal('0') # The currently saved negotiated price

            # Log da ação
            logger.info(
                f"Cálculo completo executado para proposta {proposta.numero} via API: "
                f"Preço calculado: R$ {valor_calculado:.2f} (custo: R$ {custo_producao:.2f})"
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'valorCalculado': float(valor_calculado), # System calculated price
                    'valorProposta': float(valor_proposta_final), # User negotiated price
                    'custoProducao': float(custo_producao),
                    'custoMateriais': float(custo_materiais),
                    'custoMaoObra': float(custo_mao_obra),
                    'custoInstalacao': float(custo_instalacao),
                    'explicacao': proposta.explicacao_calculo # Use the explanation from the service
                }
            })
            
        except Exception as calc_error:
            logger.error(f"Erro no cálculo da proposta {proposta.numero}: {str(calc_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Erro no cálculo: {str(calc_error)}. Verifique se todos os dados necessários estão preenchidos.'
            }, status=500)
        
    except Exception as e:
        logger.error(f"Erro geral ao calcular proposta {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)