# core/services/calculo_pedido.py - ARQUIVO PRINCIPAL UNIFICADO - VERSÃO ATUALIZADA

import logging
from decimal import Decimal
from typing import Dict, Any, Union
from django.db import transaction

from core.models import Produto, ParametrosGerais
from core.services.dimensionamento import DimensionamentoService
from core.services.pricing import PricingService
# SERVICES ESPECÍFICOS - importados diretamente
from .calculo_cabine import CalculoCabineService
from .calculo_carrinho import CalculoCarrinhoService
from .calculo_tracao import CalculoTracaoService
from .calculo_sistemas import CalculoSistemasService
from core.utils.formatters import extrair_especificacoes_do_pedido

logger = logging.getLogger(__name__)


def safe_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
    """Converte qualquer valor numérico para Decimal de forma segura"""
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class CalculoPedidoService:
    """
    Serviço principal para cálculos de pedidos de elevadores
    Orquestra os diferentes módulos de cálculo
    """
    
    @staticmethod
    def _calcular_custos_componentes(pedido, dimensionamento) -> Dict[str, Any]:
        """
        Calcula os custos de produção completos usando módulos especializados
        Método interno que substitui o ComponentesCalculoService
        REFATORADO para consolidar a nova estrutura de componentes
        """
        # Buscar todos os produtos ativos (MPs - Matéria Prima)
        custos_db = {p.codigo: p for p in Produto.objects.filter(
            disponivel=True, 
            status='ATIVO',
            tipo='MP'  # Só matérias primas
        )}
        
        logger.info(f"Produtos disponíveis para cálculo: {len(custos_db)}")
        
        # Dicionário que armazenará a estrutura hierárquica final dos componentes
        componentes_consolidados = {} 
        custos_por_categoria = {}
        
        # CABINE - Chapas do Corpo, Piso e Parafusos
        logger.info("Calculando custos da cabine...")
        try:
            # calculo_cabine.py agora retorna {'componentes': {...}, 'total': Decimal}
            custo_cabine = CalculoCabineService.calcular_custo_cabine(pedido, dimensionamento, custos_db)
            componentes_consolidados["CABINE"] = custo_cabine['componentes']
            # Adiciona o total da categoria ao dicionário de componentes consolidados para fácil acesso no template
            componentes_consolidados["CABINE"]["total_categoria"] = float(custo_cabine['total'])
            custos_por_categoria['CABINE'] = safe_decimal(custo_cabine['total'])
            logger.info(f"Custo cabine: R$ {custo_cabine['total']}")
        except Exception as e:
            logger.error(f"Erro no cálculo da cabine: {e}")
            componentes_consolidados["CABINE"] = {}
            custos_por_categoria['CABINE'] = Decimal('0')
        
        # CARRINHO - Chassi, Plataforma, Travessas, Longarinas, Perfis e Barras
        logger.info("Calculando custos do carrinho...")
        try:
            # **ASSUMIMOS QUE calculo_carrinho.py SERÁ REFATORADO DE FORMA SIMILAR**
            custo_carrinho = CalculoCarrinhoService.calcular_custo_carrinho(pedido, dimensionamento, custos_db)
            componentes_consolidados["CARRINHO"] = custo_carrinho['componentes']
            componentes_consolidados["CARRINHO"]["total_categoria"] = float(custo_carrinho['total'])
            custos_por_categoria['CARRINHO'] = safe_decimal(custo_carrinho['total'])
            logger.info(f"Custo carrinho: R$ {custo_carrinho['total']}")
        except Exception as e:
            logger.error(f"Erro no cálculo do carrinho: {e}")
            componentes_consolidados["CARRINHO"] = {}
            custos_por_categoria['CARRINHO'] = Decimal('0')
        
        # TRAÇÃO - Motor, Cabos, Contrapeso, Guias e Polias
        logger.info("Calculando custos de tração...")
        try:
            # **ASSUMIMOS QUE calculo_tracao.py SERÁ REFATORADO DE FORMA SIMILAR**
            custo_tracao = CalculoTracaoService.calcular_custo_tracao(pedido, dimensionamento, custos_db)
            componentes_consolidados["TRACAO"] = custo_tracao['componentes']
            componentes_consolidados["TRACAO"]["total_categoria"] = float(custo_tracao['total'])
            custos_por_categoria['TRACAO'] = safe_decimal(custo_tracao['total'])
            logger.info(f"Custo tração: R$ {custo_tracao['total']}")
        except Exception as e:
            logger.error(f"Erro no cálculo da tração: {e}")
            componentes_consolidados["TRACAO"] = {}
            custos_por_categoria['TRACAO'] = Decimal('0')
        
        # SISTEMAS COMPLEMENTARES - Iluminação, Ventilação, Comando, Botoeiras e Portas
        logger.info("Calculando custos dos sistemas complementares...")
        try:
            # **ASSUMIMOS QUE calculo_sistemas.py SERÁ REFATORADO DE FORMA SIMILAR**
            custo_sistemas = CalculoSistemasService.calcular_custo_sistemas(pedido, dimensionamento, custos_db)
            componentes_consolidados["SIST_COMPLEMENTARES"] = custo_sistemas['componentes']
            componentes_consolidados["SIST_COMPLEMENTARES"]["total_categoria"] = float(custo_sistemas['total'])
            custos_por_categoria['SIST_COMPLEMENTARES'] = safe_decimal(custo_sistemas['total'])
            logger.info(f"Custo sistemas: R$ {custo_sistemas['total']}")
        except Exception as e:
            logger.error(f"Erro no cálculo dos sistemas: {e}")
            componentes_consolidados["SIST_COMPLEMENTARES"] = {}
            custos_por_categoria['SIST_COMPLEMENTARES'] = Decimal('0')
        
        # Totais - CONVERSÃO SEGURA PARA DECIMAL
        custo_materiais = sum(custos_por_categoria.values())  # Agora todos são Decimal
        custo_mao_obra = custo_materiais * Decimal('0.15')  # 15% dos materiais
        custo_instalacao = custo_materiais * Decimal('0.10')  # 10% dos materiais
        custo_total = custo_materiais + custo_mao_obra + custo_instalacao
        
        logger.info(f"RESUMO DOS CUSTOS:")
        logger.info(f"  - Cabine: R$ {custos_por_categoria['CABINE']}")
        logger.info(f"  - Carrinho: R$ {custos_por_categoria['CARRINHO']}")
        logger.info(f"  - Tração: R$ {custos_por_categoria['TRACAO']}")
        logger.info(f"  - Sistemas: R$ {custos_por_categoria['SIST_COMPLEMENTARES']}")
        logger.info(f"  - Total Materiais: R$ {custo_materiais}")
        logger.info(f"  - Mão de Obra (15%): R$ {custo_mao_obra}")
        logger.info(f"  - Instalação (10%): R$ {custo_instalacao}")
        logger.info(f"  - CUSTO TOTAL: R$ {custo_total}")
        
        return {
            'componentes': componentes_consolidados, # AGORA ESTE CONTÉM A ESTRUTURA HIERÁRQUICA
            'custos_por_categoria': custos_por_categoria,
            'custo_materiais': custo_materiais,
            'custo_mao_obra': custo_mao_obra,
            'custo_instalacao': custo_instalacao,
            'custo_total': custo_total,
            'total_componentes': len(componentes_consolidados)
        }

    @staticmethod
    @transaction.atomic
    def calcular_custos_completo(pedido):
        """
        Calcula tudo: dimensionamento + custos + preços e salva no pedido
        
        Args:
            pedido: Instância do modelo Pedido
            
        Returns:
            dict: Resultado completo dos cálculos
        """
        try:
            logger.info(f"Iniciando cálculo completo para pedido {pedido.numero}")
            
            # 1. Extrair especificações do pedido
            especificacoes = extrair_especificacoes_do_pedido(pedido)
            logger.info(f"Especificações extraídas: {list(especificacoes.keys())}")
            
            # 2. Calcular dimensionamento
            dimensionamento, explicacao_dimensionamento = DimensionamentoService.calcular_dimensionamento_completo(especificacoes)
            logger.info(f"Dimensionamento calculado - Cabine: {dimensionamento.get('cab', {}).get('largura', 0)}x{dimensionamento.get('cab', {}).get('compr', 0)}m")
            
            # 3. Calcular custos de produção usando métodos internos
            # O 'componentes' no resultado agora é a estrutura hierárquica
            custos_resultado = CalculoPedidoService._calcular_custos_componentes(pedido, dimensionamento)
            logger.info(f"Custos calculados - Total: R$ {custos_resultado['custo_total']}")
            
            # 4. Calcular formação de preço
            # PricingService now directly returns the final calculated price to be stored in preco_venda_calculado
            formacao_preco_result = PricingService.calcular_formacao_preco(
                custos_resultado['custo_total'], 
                pedido.faturado_por
            )
            logger.info(f"Preço calculado - Sugerido: R$ {formacao_preco_result['preco_com_impostos']}")
            
            # 5. Montar ficha técnica
            ficha_tecnica = CalculoPedidoService._montar_ficha_tecnica(pedido, dimensionamento, custos_resultado)
            
            # 6. Salvar tudo no pedido
            CalculoPedidoService._salvar_calculos_no_pedido(
                pedido, dimensionamento, explicacao_dimensionamento, 
                custos_resultado, formacao_preco_result, ficha_tecnica
            )
            
            logger.info(f"Cálculo completo finalizado para pedido {pedido.numero}")
            
            return {
                'success': True,
                'dimensionamento': dimensionamento,
                'explicacao': explicacao_dimensionamento,
                'custos': custos_resultado,
                'formacao_preco': formacao_preco_result,
                'ficha_tecnica': ficha_tecnica
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo completo do pedido {pedido.numero}: {str(e)}")
            raise ValueError(f"Erro nos cálculos: {str(e)}")
    
    @staticmethod
    def _montar_ficha_tecnica(pedido, dimensionamento, custos_resultado) -> Dict[str, Any]:
        """Monta a ficha técnica resumida"""
        cab = dimensionamento.get('cab', {})
        
        return {
            'dimensoes_cabine': {
                'largura': float(cab.get('largura', 0)),
                'comprimento': float(cab.get('compr', 0)),
                'altura': float(cab.get('altura', 0)),
                'area': float(cab.get('largura', 0)) * float(cab.get('compr', 0)),
                'volume': float(cab.get('largura', 0)) * float(cab.get('compr', 0)) * float(cab.get('altura', 0))
            },
            'capacidade_tracao': {
                'capacidade_cabine': float(cab.get('capacidade', 0)),
                'tracao_cabine': float(cab.get('tracao', 0))
            },
            'paineis_chapas': {
                'paineis_lateral': cab.get('pnl', {}).get('lateral', 0),
                'paineis_fundo': cab.get('pnl', {}).get('fundo', 0),
                'paineis_teto': cab.get('pnl', {}).get('teto', 0),
                'chapas_corpo': cab.get('chp', {}).get('corpo', 0),
                'chapas_piso': cab.get('chp', {}).get('piso', 0),
                'chapas_total': cab.get('chp', {}).get('corpo', 0) + cab.get('chp', {}).get('piso', 0)
            },
            'resumo_elevador': f"{pedido.get_modelo_elevador_display()} {pedido.capacidade}kg, {pedido.get_acionamento_display()}, {pedido.get_material_cabine_display()} {pedido.get_espessura_cabine_display()}",
            'custos_resumo': {
                'custo_materiais': float(custos_resultado['custo_materiais']),
                'custo_mao_obra': float(custos_resultado['custo_mao_obra']),
                'custo_instalacao': float(custos_resultado['custo_instalacao']),
                'custo_total': float(custos_resultado['custo_total'])
            }
        }
    
    @staticmethod
    def _salvar_calculos_no_pedido(pedido, dimensionamento, explicacao, custos_resultado, formacao_preco_result, ficha_tecnica):
        """Salva todos os cálculos no pedido"""
        # Dimensões calculadas
        cab = dimensionamento.get('cab', {})
        pedido.largura_cabine_calculada = cab.get('largura')
        pedido.comprimento_cabine_calculado = cab.get('compr')
        pedido.capacidade_cabine_calculada = cab.get('capacidade')
        pedido.tracao_cabine_calculada = cab.get('tracao')
        
        # Custos
        pedido.custo_materiais = custos_resultado['custo_materiais']
        pedido.custo_mao_obra = custos_resultado['custo_mao_obra']
        pedido.custo_instalacao = custos_resultado['custo_instalacao']
        pedido.custo_producao = custos_resultado['custo_total']
        
        # Preços
        # This is the single calculated price that the system suggests.
        pedido.preco_venda_calculado = formacao_preco_result['preco_com_impostos'] # Use preco_com_impostos from PricingService
        # pedido.preco_sem_impostos = formacao_preco['preco_sem_impostos'] # REMOVIDO: Unificado
        
        # Dados detalhados em JSON
        pedido.ficha_tecnica = ficha_tecnica
        pedido.dimensionamento_detalhado = dimensionamento
        pedido.explicacao_calculo = explicacao
        # AQUI É O PONTO CHAVE: salvamos a nova estrutura hierárquica
        pedido.custos_detalhados = {
            'componentes': custos_resultado['componentes'], # A nova estrutura aninhada
            'custos_por_categoria': {k: float(v) for k, v in custos_resultado['custos_por_categoria'].items()},
            'resumo': {
                'custo_materiais': float(custos_resultado['custo_materiais']),
                'custo_mao_obra': float(custos_resultado['custo_mao_obra']),
                'custo_instalacao': float(custos_resultado['custo_instalacao']),
                'custo_total': float(custos_resultado['custo_total'])
            }
        }
        # Podemos remover 'componentes_calculados' se 'custos_detalhados.componentes' for o único local
        # Por enquanto, para segurança, vamos manter e garantir que receba a nova estrutura
        pedido.componentes_calculados = custos_resultado['componentes']
        
        pedido.formacao_preco = formacao_preco_result # Changed to formacao_preco_result
        
        # Atualizar status se necessário
        if pedido.status == 'rascunho':
            # Only set valor_proposta if it hasn't been manually set by the user yet.
            if pedido.valor_proposta is None:
                pedido.valor_proposta = pedido.preco_venda_calculado # Default to calculated if not set
            
            # If a calculated price or a manually set price exists, mark as simulated/pending
            if pedido.preco_venda_calculado or pedido.valor_proposta:
                 pedido.status = 'simulado' # More appropriate for calculated but not finalized
            
        pedido.save()
        logger.info(f"Cálculos salvos no pedido {pedido.numero}")


class ParametrosService:
    """
    Serviço para gerenciar parâmetros de cálculo
    """
    
    @staticmethod
    def get_parametro(nome: str, default=None):
        """Busca um parâmetro pelo nome"""
        try:
            # TODO: Implementar busca de parâmetros quando modelo estiver pronto
            # param = ParametroCalculo.objects.get(parametro=nome, ativo=True)
            # return param.valor
            return default
        except Exception:
            return default
    
    @staticmethod
    def get_parametros_categoria(categoria: str) -> Dict[str, Any]:
        """Busca todos os parâmetros de uma categoria"""
        # TODO: Implementar quando modelo estiver pronto
        return {}
    
    @staticmethod
    def get_todos_parametros() -> Dict[str, Any]:
        """Busca todos os parâmetros ativos"""
        # TODO: Implementar quando modelo estiver pronto
        return {}