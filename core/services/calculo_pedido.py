# core/services/calculo_pedido.py - ARQUIVO PRINCIPAL UNIFICADO - VERSÃO COMPLETA CORRIGIDA

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
    VERSÃO CORRIGIDA: Nova estrutura contábil linear
    """
    
    @staticmethod
    def _calcular_custos_componentes(pedido, dimensionamento) -> Dict[str, Any]:
        """
        Calcula os custos de produção completos usando módulos especializados
        CORRIGIDO: Nova estrutura contábil linear
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
        
        # =================================================================
        # CÁLCULO DOS COMPONENTES POR CATEGORIA
        # =================================================================
        
        # CABINE - Chapas do Corpo, Piso e Parafusos
        logger.info("Calculando custos da cabine...")
        try:
            custo_cabine = CalculoCabineService.calcular_custo_cabine(pedido, dimensionamento, custos_db)
            componentes_consolidados["CABINE"] = custo_cabine['componentes']
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
            custo_sistemas = CalculoSistemasService.calcular_custo_sistemas(pedido, dimensionamento, custos_db)
            componentes_consolidados["SIST_COMPLEMENTARES"] = custo_sistemas['componentes']
            componentes_consolidados["SIST_COMPLEMENTARES"]["total_categoria"] = float(custo_sistemas['total'])
            custos_por_categoria['SIST_COMPLEMENTARES'] = safe_decimal(custo_sistemas['total'])
            logger.info(f"Custo sistemas: R$ {custo_sistemas['total']}")
        except Exception as e:
            logger.error(f"Erro no cálculo dos sistemas: {e}")
            componentes_consolidados["SIST_COMPLEMENTARES"] = {}
            custos_por_categoria['SIST_COMPLEMENTARES'] = Decimal('0')
        
        # =================================================================
        # CUSTOS BASE (materiais dos componentes)
        # =================================================================
        custo_materiais = sum(custos_por_categoria.values())  # R$ 10.000
        
        # =================================================================
        # CUSTOS DE PRODUÇÃO (FÁBRICA)
        # =================================================================
        custo_mao_obra_producao = custo_materiais * Decimal('0.15')     # 15% = R$ 1.500
        custo_indiretos_fabricacao = custo_materiais * Decimal('0.05')  # 5% = R$ 500
        
        # CUSTO DE PRODUÇÃO = só fábrica (SEM instalação)
        custo_producao = custo_materiais + custo_mao_obra_producao + custo_indiretos_fabricacao
        # R$ 10.000 + R$ 1.500 + R$ 500 = R$ 12.000
        
        # =================================================================
        # CUSTO DE INSTALAÇÃO (SEPARADO)
        # =================================================================
        custo_instalacao = custo_materiais * Decimal('0.05')  # 5% = R$ 500
        
        # =================================================================
        # CUSTO TOTAL DO PROJETO
        # =================================================================
        custo_total_projeto = custo_producao + custo_instalacao  # R$ 12.500
        
        # =================================================================
        # FORMAÇÃO DE PREÇO LINEAR
        # =================================================================
        
        # 1. Margem de Lucro (30% sobre custo total)
        margem_lucro = custo_total_projeto * Decimal('0.30')  # R$ 3.750
        preco_com_margem = custo_total_projeto + margem_lucro  # R$ 16.250
        
        # 2. Comissão (3% sobre preço com margem)
        comissao = preco_com_margem * Decimal('0.03')  # R$ 487,50
        preco_com_comissao = preco_com_margem + comissao  # R$ 16.737,50
        
        # 3. Impostos (10% sobre preço com comissão)
        impostos = pedido.calcular_impostos_dinamicos(preco_com_comissao)
        preco_final = preco_com_comissao + impostos  # R$ 18.411,25
        
        # =================================================================
        # LOGS DETALHADOS
        # =================================================================
        logger.info(f"=== RESUMO DOS CUSTOS ===")
        logger.info(f"  - Cabine: R$ {custos_por_categoria['CABINE']}")
        logger.info(f"  - Carrinho: R$ {custos_por_categoria['CARRINHO']}")
        logger.info(f"  - Tração: R$ {custos_por_categoria['TRACAO']}")
        logger.info(f"  - Sistemas: R$ {custos_por_categoria['SIST_COMPLEMENTARES']}")
        logger.info(f"  - TOTAL MATERIAIS: R$ {custo_materiais}")
        logger.info(f"")
        logger.info(f"=== CUSTOS DE PRODUÇÃO ===")
        logger.info(f"  - MOD Produção (15%): R$ {custo_mao_obra_producao}")
        logger.info(f"  - Custos Indiretos (5%): R$ {custo_indiretos_fabricacao}")
        logger.info(f"  - CUSTO DE PRODUÇÃO: R$ {custo_producao}")
        logger.info(f"")
        logger.info(f"=== PROJETO COMPLETO ===")
        logger.info(f"  - Custo Instalação (5%): R$ {custo_instalacao}")
        logger.info(f"  - CUSTO TOTAL PROJETO: R$ {custo_total_projeto}")
        logger.info(f"")
        logger.info(f"=== FORMAÇÃO DE PREÇO ===")
        logger.info(f"  - Margem Lucro (30%): R$ {margem_lucro}")
        logger.info(f"  - Preço c/ Margem: R$ {preco_com_margem}")
        logger.info(f"  - Comissão (3%): R$ {comissao}")
        logger.info(f"  - Preço c/ Comissão: R$ {preco_com_comissao}")
        logger.info(f"  - Impostos (10%): R$ {impostos}")
        logger.info(f"  - PREÇO FINAL: R$ {preco_final}")
        
        return {
            'componentes': componentes_consolidados,
            'custos_por_categoria': custos_por_categoria,
            # Custos base
            'custo_materiais': custo_materiais,
            'custo_mao_obra_producao': custo_mao_obra_producao,
            'custo_indiretos_fabricacao': custo_indiretos_fabricacao,
            'custo_instalacao': custo_instalacao,
            # Totais de custo
            'custo_producao': custo_producao,
            'custo_total_projeto': custo_total_projeto,
            # Formação de preço
            'margem_lucro': margem_lucro,
            'preco_com_margem': preco_com_margem,
            'comissao': comissao,
            'preco_com_comissao': preco_com_comissao,
            'impostos': impostos,
            'preco_final': preco_final,
            # Outros
            'total_componentes': len(componentes_consolidados)
        }

    @staticmethod
    @transaction.atomic
    def calcular_custos_completo(pedido):
        """
        Calcula tudo: dimensionamento + custos + preços e salva no pedido
        VERSÃO CORRIGIDA: Nova estrutura contábil
        
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
            custos_resultado = CalculoPedidoService._calcular_custos_componentes(pedido, dimensionamento)
            logger.info(f"Custos calculados - Total: R$ {custos_resultado['custo_total_projeto']}")
            
            # 4. Calcular formação de preço (usando PricingService para compatibilidade)
            # Nota: PricingService agora recebe custo_total_projeto como base
            formacao_preco_result = PricingService.calcular_formacao_preco(
                custos_resultado['custo_total_projeto'], 
                pedido.faturado_por
            )
            logger.info(f"Preço calculado - Sugerido: R$ {custos_resultado['preco_final']}")
            
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
                'custo_mao_obra': float(custos_resultado['custo_mao_obra_producao']),
                'custo_indiretos': float(custos_resultado['custo_indiretos_fabricacao']),
                'custo_producao': float(custos_resultado['custo_producao']),
                'custo_instalacao': float(custos_resultado['custo_instalacao']),
                'custo_total_projeto': float(custos_resultado['custo_total_projeto'])
            }
        }
    
    @staticmethod
    def _salvar_calculos_no_pedido(pedido, dimensionamento, explicacao, custos_resultado, formacao_preco_result, ficha_tecnica):
        """
        Salva todos os cálculos no pedido
        VERSÃO CORRIGIDA: Nova estrutura de campos
        """
        # Dimensões calculadas
        cab = dimensionamento.get('cab', {})
        pedido.largura_cabine_calculada = cab.get('largura')
        pedido.comprimento_cabine_calculado = cab.get('compr')
        pedido.capacidade_cabine_calculada = cab.get('capacidade')
        pedido.tracao_cabine_calculada = cab.get('tracao')
        
        # =================================================================
        # CUSTOS DETALHADOS
        # =================================================================
        pedido.custo_materiais = custos_resultado['custo_materiais']
        pedido.custo_mao_obra = custos_resultado['custo_mao_obra_producao']
        pedido.custo_indiretos_fabricacao = custos_resultado['custo_indiretos_fabricacao']
        pedido.custo_instalacao = custos_resultado['custo_instalacao']
        
        # =================================================================
        # TOTAIS DE CUSTO
        # =================================================================
        pedido.custo_producao = custos_resultado['custo_producao']
        pedido.custo_total_projeto = custos_resultado['custo_total_projeto']
        
        # =================================================================
        # FORMAÇÃO DE PREÇO
        # =================================================================
        pedido.margem_lucro = custos_resultado['margem_lucro']
        pedido.preco_com_margem = custos_resultado['preco_com_margem']
        pedido.comissao = custos_resultado['comissao']
        pedido.preco_com_comissao = custos_resultado['preco_com_comissao']
        pedido.impostos = custos_resultado['impostos']
        
        # =================================================================
        # PREÇO FINAL
        # =================================================================
        pedido.preco_venda_calculado = custos_resultado['preco_final']
        
        # Se ainda não tem valor negociado, usar o calculado como base
        if pedido.valor_proposta is None:
            pedido.valor_proposta = pedido.preco_venda_calculado
        
        # Calcular desconto se houver diferença
        if pedido.preco_venda_calculado and pedido.valor_proposta:
            if pedido.preco_venda_calculado > pedido.valor_proposta:
                pedido.percentual_desconto = (
                    (pedido.preco_venda_calculado - pedido.valor_proposta) / 
                    pedido.preco_venda_calculado * 100
                )
            else:
                pedido.percentual_desconto = Decimal('0')
        
        # =================================================================
        # DADOS DETALHADOS EM JSON
        # =================================================================
        pedido.ficha_tecnica = ficha_tecnica
        pedido.dimensionamento_detalhado = dimensionamento
        pedido.explicacao_calculo = explicacao
        
        pedido.custos_detalhados = {
            'componentes': custos_resultado['componentes'],
            'custos_por_categoria': {k: float(v) for k, v in custos_resultado['custos_por_categoria'].items()},
            'resumo': {
                'custo_materiais': float(custos_resultado['custo_materiais']),
                'custo_mao_obra_producao': float(custos_resultado['custo_mao_obra_producao']),
                'custo_indiretos_fabricacao': float(custos_resultado['custo_indiretos_fabricacao']),
                'custo_instalacao': float(custos_resultado['custo_instalacao']),
                'custo_producao': float(custos_resultado['custo_producao']),
                'custo_total_projeto': float(custos_resultado['custo_total_projeto']),
                'margem_lucro': float(custos_resultado['margem_lucro']),
                'preco_com_margem': float(custos_resultado['preco_com_margem']),
                'comissao': float(custos_resultado['comissao']),
                'preco_com_comissao': float(custos_resultado['preco_com_comissao']),
                'impostos': float(custos_resultado['impostos']),
                'preco_final': float(custos_resultado['preco_final'])
            }
        }
        
        # Manter componentes_calculados para compatibilidade
        pedido.componentes_calculados = custos_resultado['componentes']
        
        pedido.formacao_preco = formacao_preco_result
        
        # Atualizar status se necessário
        if pedido.status == 'rascunho':
            if pedido.preco_venda_calculado:
                pedido.status = 'simulado'
        
        pedido.save()
        logger.info(f"Cálculos salvos no pedido {pedido.numero}")

    @staticmethod
    def recalcular_proposta_existente(pedido):
        """
        Recalcula uma proposta existente mantendo valores negociados
        Útil para atualizar cálculos após mudanças nos parâmetros
        """
        try:
            logger.info(f"Recalculando proposta existente {pedido.numero}")
            
            # Salvar valor negociado atual
            valor_proposta_atual = pedido.valor_proposta
            
            # Executar cálculo completo
            resultado = CalculoPedidoService.calcular_custos_completo(pedido)
            
            # Restaurar valor negociado se existia
            if valor_proposta_atual:
                pedido.valor_proposta = valor_proposta_atual
                
                # Recalcular desconto
                if pedido.preco_venda_calculado and pedido.valor_proposta:
                    if pedido.preco_venda_calculado > pedido.valor_proposta:
                        pedido.percentual_desconto = (
                            (pedido.preco_venda_calculado - pedido.valor_proposta) / 
                            pedido.preco_venda_calculado * 100
                        )
                    else:
                        pedido.percentual_desconto = Decimal('0')
                
                pedido.save()
            
            logger.info(f"Recálculo finalizado para proposta {pedido.numero}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no recálculo da proposta {pedido.numero}: {str(e)}")
            raise ValueError(f"Erro no recálculo: {str(e)}")

    @staticmethod
    def obter_resumo_custos(pedido) -> Dict[str, Any]:
        """
        Retorna resumo dos custos de uma proposta
        Útil para APIs e dashboards
        """
        try:
            if not pedido.custo_total_projeto:
                return {'erro': 'Proposta não possui cálculos executados'}
            
            resumo = {
                'custos_base': {
                    'materiais': float(pedido.custo_materiais or 0),
                    'mao_obra': float(pedido.custo_mao_obra or 0),
                    'indiretos': float(pedido.custo_indiretos_fabricacao or 0),
                    'instalacao': float(pedido.custo_instalacao or 0)
                },
                'totais_custo': {
                    'producao': float(pedido.custo_producao or 0),
                    'total_projeto': float(pedido.custo_total_projeto or 0)
                },
                'formacao_preco': {
                    'margem_lucro': float(pedido.margem_lucro or 0),
                    'comissao': float(pedido.comissao or 0),
                    'impostos': float(pedido.impostos or 0),
                    'preco_calculado': float(pedido.preco_venda_calculado or 0)
                },
                'resultado_final': {
                    'valor_proposta': float(pedido.valor_proposta or 0),
                    'desconto_percentual': float(pedido.percentual_desconto or 0),
                    'lucro_bruto': float(pedido.lucro_bruto),
                    'margem_real': float(pedido.margem_real_percentual),
                    'economia_cliente': float(pedido.economia_cliente)
                }
            }
            
            return resumo
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo de custos: {str(e)}")
            return {'erro': str(e)}


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
        return {
            'percentual_mao_obra': 15.0,
            'percentual_indiretos': 5.0,
            'percentual_instalacao': 5.0,
            'percentual_margem': 30.0,
            'percentual_comissao': 3.0,
            'percentual_impostos': 10.0
        }