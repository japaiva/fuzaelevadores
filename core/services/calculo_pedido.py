# core/services/calculo_pedido.py - HÍBRIDO: CABINE YAML + RESTO HARD CODED

import logging
from decimal import Decimal
from typing import Dict, Any, Union
from django.db import transaction
from django.db.models import Q

from core.models import Produto, ParametrosGerais
from core.services.dimensionamento import DimensionamentoService
from core.services.pricing import PricingService

# ✅ IMPORT PARA CABINE YAML
from core.services.calculo_pedido_yaml import CalculoPedidoYAMLService

# ✅ IMPORTS PARA HARD CODED (carrinho, tração, sistemas)
from .calculo_carrinho import CalculoCarrinhoService
from .calculo_tracao import CalculoTracaoService
from .calculo_sistemas import CalculoSistemasService
from core.utils.formatters import extrair_especificacoes_do_pedido

logger = logging.getLogger(__name__)


def safe_decimal(value: Union[int, float, str, Decimal, None]) -> Decimal:
    """Converte qualquer valor para Decimal de forma segura"""
    if value is None:
        return Decimal('0.00')
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        logger.warning(f"Valor inválido convertido para 0: {value}")
        return Decimal('0.00')


class CalculoPedidoService:
    """
    Serviço principal para cálculos de pedidos de elevadores
    ✅ HÍBRIDO: CABINE via YAML + CARRINHO/TRAÇÃO/SISTEMAS via hard-coded
    ✅ PARAMETRIZADO: Custos indiretos e formação de preço via ParametrosGerais
    """

    @staticmethod
    def _obter_parametros():
        """
        Obtém os parâmetros de cálculo do banco de dados.
        Retorna valores padrão se não existir registro.
        """
        try:
            params = ParametrosGerais.objects.first()
            if params:
                return {
                    'percentual_mao_obra': params.percentual_mao_obra / Decimal('100'),
                    'percentual_indiretos_fabricacao': params.percentual_indiretos_fabricacao / Decimal('100'),
                    'percentual_instalacao': params.percentual_instalacao / Decimal('100'),
                    'margem_padrao': params.margem_padrao / Decimal('100'),
                    'comissao_padrao': params.comissao_padrao / Decimal('100'),
                }
        except Exception as e:
            logger.warning(f"Erro ao obter parâmetros: {e}. Usando valores padrão.")

        # Valores padrão caso não exista registro
        return {
            'percentual_mao_obra': Decimal('0.15'),           # 15%
            'percentual_indiretos_fabricacao': Decimal('0.05'),  # 5%
            'percentual_instalacao': Decimal('0.05'),         # 5%
            'margem_padrao': Decimal('0.30'),                 # 30%
            'comissao_padrao': Decimal('0.03'),               # 3%
        }

    @staticmethod
    def _calcular_custos_componentes(pedido, dimensionamento) -> Dict[str, Any]:
        """
        Calcula os custos de produção completos
        ✅ YAML OBRIGATÓRIO PARA TUDO - SEM FALLBACK HARD-CODED
        """

        qs = Produto.objects.filter(
            utilizado=True,
            status='ATIVO',
        ).filter(
            Q(tipo__istartswith='MP') | Q(tipo__istartswith='PI')
        )
        custos_db = {p.codigo.strip(): p for p in qs}

        logger.info(f"Produtos disponíveis para cálculo: {len(custos_db)}")

        componentes_consolidados = {}
        custos_por_categoria = {}
        
        # ✅ USAR O SERVIÇO YAML AVANÇADO
        from core.services.calculo_pedido_yaml import CalculoPedidoYAMLService
        yaml_service = CalculoPedidoYAMLService(custos_db)
        
        # =================================================================
        # 1. CABINE - YAML OBRIGATÓRIO
        # =================================================================
        try:
            logger.info("🔥 CALCULANDO CABINE VIA YAML...")
            resultado_wrap = yaml_service.calcular_completo(pedido, dimensionamento, categorias=['cabine'])
            resultado_cabine_yaml = resultado_wrap['categorias']['CABINE']

            if not resultado_cabine_yaml.get('sucesso'):
                erros_cabine = '; '.join(resultado_cabine_yaml.get('erros', ['Erro desconhecido']))
                raise ValueError(f"YAML CABINE falhou: {erros_cabine}")
            
            # ✅ TRANSFORMAR estrutura YAML para compatibilidade com template
            cabine_compativel = {}
            if 'subcategorias' in resultado_cabine_yaml:
                for nome_subcat, dados_subcat in resultado_cabine_yaml['subcategorias'].items():
                    cabine_compativel[nome_subcat] = dados_subcat
            cabine_compativel['total_categoria'] = resultado_cabine_yaml.get('total_categoria', 0)
            
            componentes_consolidados["CABINE"] = cabine_compativel
            custos_por_categoria['CABINE'] = safe_decimal(resultado_cabine_yaml.get('total_categoria', 0))
            logger.info(f"✅ CABINE YAML: R$ {custos_por_categoria['CABINE']}")
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO - CABINE YAML falhou: {e}")
            raise ValueError(f"Erro no cálculo YAML da CABINE: {str(e)}")

        # =================================================================
        # 2. CARRINHO - YAML OBRIGATÓRIO (SEM FALLBACK)
        # =================================================================
        try:
            logger.info("🔥 CALCULANDO CARRINHO VIA YAML...")
            resultado_wrap = yaml_service.calcular_completo(pedido, dimensionamento, categorias=['carrinho'])
            resultado_carrinho_yaml = resultado_wrap['categorias']['CARRINHO']

            if not resultado_carrinho_yaml.get('sucesso'):
                erros_carrinho = '; '.join(resultado_carrinho_yaml.get('erros', ['Erro desconhecido']))
                # ❌ SEM FALLBACK - ERRO DIRETO
                raise ValueError(f"YAML CARRINHO falhou: {erros_carrinho}")
            
            # ✅ TRANSFORMAR estrutura YAML para compatibilidade
            carrinho_compativel = {}
            if 'subcategorias' in resultado_carrinho_yaml:
                for nome_subcat, dados_subcat in resultado_carrinho_yaml['subcategorias'].items():
                    carrinho_compativel[nome_subcat] = dados_subcat
            carrinho_compativel['total_categoria'] = resultado_carrinho_yaml.get('total_categoria', 0)
            
            componentes_consolidados["CARRINHO"] = carrinho_compativel
            custos_por_categoria['CARRINHO'] = safe_decimal(resultado_carrinho_yaml.get('total_categoria', 0))
            logger.info(f"✅ CARRINHO YAML: R$ {custos_por_categoria['CARRINHO']}")
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO - CARRINHO YAML falhou: {e}")
            # ❌ PROPAGAR ERRO - NÃO HÁ FALLBACK
            raise ValueError(f"Erro no cálculo YAML do CARRINHO: {str(e)}")

        # =================================================================
        # 3. TRAÇÃO - YAML OBRIGATÓRIO (SEM FALLBACK)
        # =================================================================
        try:
            logger.info("🔥 CALCULANDO TRAÇÃO VIA YAML...")
            resultado_wrap = yaml_service.calcular_completo(pedido, dimensionamento, categorias=['tracao'])
            resultado_tracao_yaml = resultado_wrap['categorias']['TRACAO']

            if not resultado_tracao_yaml.get('sucesso'):
                erros_tracao = '; '.join(resultado_tracao_yaml.get('erros', ['Erro desconhecido']))
                # ❌ SEM FALLBACK - ERRO DIRETO
                raise ValueError(f"YAML TRAÇÃO falhou: {erros_tracao}")
            
            # ✅ TRANSFORMAR estrutura YAML para compatibilidade
            tracao_compativel = {}
            if 'subcategorias' in resultado_tracao_yaml:
                for nome_subcat, dados_subcat in resultado_tracao_yaml['subcategorias'].items():
                    tracao_compativel[nome_subcat] = dados_subcat
            tracao_compativel['total_categoria'] = resultado_tracao_yaml.get('total_categoria', 0)
            
            componentes_consolidados["TRACAO"] = tracao_compativel
            custos_por_categoria['TRACAO'] = safe_decimal(resultado_tracao_yaml.get('total_categoria', 0))
            logger.info(f"✅ TRAÇÃO YAML: R$ {custos_por_categoria['TRACAO']}")
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO - TRAÇÃO YAML falhou: {e}")
            # ❌ PROPAGAR ERRO - NÃO HÁ FALLBACK
            raise ValueError(f"Erro no cálculo YAML da TRAÇÃO: {str(e)}")

        # =================================================================
        # 4. SISTEMAS - YAML OBRIGATÓRIO (SEM FALLBACK)
        # =================================================================
        try:
            logger.info("🔥 CALCULANDO SISTEMAS VIA YAML...")
            resultado_wrap = yaml_service.calcular_completo(pedido, dimensionamento, categorias=['sistemas'])
            resultado_sistemas_yaml = resultado_wrap['categorias']['SIST_COMPLEMENTARES']

            if not resultado_sistemas_yaml.get('sucesso'):
                erros_sistemas = '; '.join(resultado_sistemas_yaml.get('erros', ['Erro desconhecido']))
                # ❌ SEM FALLBACK - ERRO DIRETO
                raise ValueError(f"YAML SISTEMAS falhou: {erros_sistemas}")
            
            # ✅ TRANSFORMAR estrutura YAML para compatibilidade
            sistemas_compativel = {}
            if 'subcategorias' in resultado_sistemas_yaml:
                for nome_subcat, dados_subcat in resultado_sistemas_yaml['subcategorias'].items():
                    sistemas_compativel[nome_subcat] = dados_subcat
            sistemas_compativel['total_categoria'] = resultado_sistemas_yaml.get('total_categoria', 0)
            
            componentes_consolidados["SIST_COMPLEMENTARES"] = sistemas_compativel
            custos_por_categoria['SIST_COMPLEMENTARES'] = safe_decimal(resultado_sistemas_yaml.get('total_categoria', 0))
            logger.info(f"✅ SISTEMAS YAML: R$ {custos_por_categoria['SIST_COMPLEMENTARES']}")
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO - SISTEMAS YAML falhou: {e}")
            # ❌ PROPAGAR ERRO - NÃO HÁ FALLBACK
            raise ValueError(f"Erro no cálculo YAML dos SISTEMAS: {str(e)}")
        
        # =================================================================
        # TOTALIZAÇÕES E FORMAÇÃO DE PREÇO (PARAMETRIZADO)
        # =================================================================

        custo_materiais = sum(custos_por_categoria.values())
        logger.info(f"📊 TOTAL MATERIAIS: R$ {custo_materiais}")

        # ✅ OBTER PARÂMETROS DO BANCO DE DADOS
        params = CalculoPedidoService._obter_parametros()
        logger.info(f"📋 Parâmetros: MOD={params['percentual_mao_obra']*100}%, "
                    f"Indiretos={params['percentual_indiretos_fabricacao']*100}%, "
                    f"Instalação={params['percentual_instalacao']*100}%, "
                    f"Margem={params['margem_padrao']*100}%, "
                    f"Comissão={params['comissao_padrao']*100}%")

        # MOD, indiretos, etc. (PARAMETRIZADO)
        custo_mao_obra_producao = custo_materiais * params['percentual_mao_obra']
        custo_indiretos_fabricacao = custo_materiais * params['percentual_indiretos_fabricacao']
        custo_instalacao = custo_materiais * params['percentual_instalacao']

        # CUSTO DE PRODUÇÃO = só fábrica (SEM instalação)
        custo_producao = custo_materiais + custo_mao_obra_producao + custo_indiretos_fabricacao

        # CUSTO TOTAL DO PROJETO
        custo_total_projeto = custo_producao + custo_instalacao

        # FORMAÇÃO DE PREÇO LINEAR (PARAMETRIZADO)
        margem_lucro = custo_total_projeto * params['margem_padrao']
        preco_com_margem = custo_total_projeto + margem_lucro

        comissao = preco_com_margem * params['comissao_padrao']
        preco_com_comissao = preco_com_margem + comissao

        impostos = pedido.calcular_impostos_dinamicos(preco_com_comissao)
        preco_final = preco_com_comissao + impostos
        
        # LOGS DE SUCESSO TOTAL
        logger.info(f"=== SUCESSO: TODOS OS CÁLCULOS VIA YAML ===")
        logger.info(f"  - CABINE (YAML): R$ {custos_por_categoria.get('CABINE', 0)}")
        logger.info(f"  - CARRINHO (YAML): R$ {custos_por_categoria.get('CARRINHO', 0)}")
        logger.info(f"  - TRAÇÃO (YAML): R$ {custos_por_categoria.get('TRACAO', 0)}")
        logger.info(f"  - SISTEMAS (YAML): R$ {custos_por_categoria.get('SIST_COMPLEMENTARES', 0)}")
        logger.info(f"  - TOTAL MATERIAIS: R$ {custo_materiais}")
        logger.info(f"  - PREÇO FINAL: R$ {preco_final}")
        logger.info(f"===== 🎉 TUDO FUNCIONANDO VIA YAML! =====")
        
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
            'total_componentes': len(componentes_consolidados),
            # ✅ TODOS VIA YAML
            'metodo_usado': {
                'CABINE': 'YAML',
                'CARRINHO': 'YAML',
                'TRACAO': 'YAML',
                'SIST_COMPLEMENTARES': 'YAML'
            },
            # ✅ PARÂMETROS USADOS (para auditoria)
            'parametros_usados': {
                'percentual_mao_obra': float(params['percentual_mao_obra'] * 100),
                'percentual_indiretos_fabricacao': float(params['percentual_indiretos_fabricacao'] * 100),
                'percentual_instalacao': float(params['percentual_instalacao'] * 100),
                'margem_padrao': float(params['margem_padrao'] * 100),
                'comissao_padrao': float(params['comissao_padrao'] * 100),
            }
        }

    # ============================================================================
    # RESTO DOS MÉTODOS PERMANECE IGUAL (calcular_custos_completo, etc.)
    # ============================================================================

    @staticmethod
    @transaction.atomic
    def calcular_custos_completo(pedido):
        """
        Calcula tudo: dimensionamento + custos + preços e salva no pedido
        ✅ MANTIDO: Só mudou a parte de cálculo de materiais para híbrido
        """
        try:
            logger.info(f"Iniciando cálculo completo HÍBRIDO para pedido {pedido.numero}")
            
            # 1. Extrair especificações do pedido
            especificacoes = extrair_especificacoes_do_pedido(pedido)
            logger.info(f"Especificações extraídas: {list(especificacoes.keys())}")
            
            # 2. Calcular dimensionamento
            dimensionamento, explicacao_dimensionamento = DimensionamentoService.calcular_dimensionamento_completo(especificacoes)
            logger.info(f"Dimensionamento calculado - Cabine: {dimensionamento.get('cab', {}).get('largura', 0)}x{dimensionamento.get('cab', {}).get('compr', 0)}m")
            
            # 3. ✅ HÍBRIDO: Calcular custos (CABINE YAML + resto hard-coded)
            custos_resultado = CalculoPedidoService._calcular_custos_componentes(pedido, dimensionamento)
            logger.info(f"Custos HÍBRIDOS calculados - Total: R$ {custos_resultado['custo_total_projeto']}")
            logger.info(f"Método usado: {custos_resultado['metodo_usado']}")
            
            # 4. Calcular formação de preço (compatibilidade)
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
            
            logger.info(f"✅ Cálculo HÍBRIDO completo finalizado para pedido {pedido.numero}")
            
            return {
                'success': True,
                'dimensionamento': dimensionamento,
                'explicacao': explicacao_dimensionamento,
                'custos': custos_resultado,
                'formacao_preco': formacao_preco_result,
                'ficha_tecnica': ficha_tecnica,
                'metodo_usado': custos_resultado['metodo_usado']  # ✅ PARA DEBUG
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo HÍBRIDO do pedido {pedido.numero}: {str(e)}")
            raise ValueError(f"Erro nos cálculos: {str(e)}")
    
    @staticmethod
    def _montar_ficha_tecnica(pedido, dimensionamento, custos_resultado) -> Dict[str, Any]:
        """Monta a ficha técnica resumida - MANTIDO IGUAL"""
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
            },
            # ✅ ADICIONAR INFO DO MÉTODO USADO
            'metodo_calculo': custos_resultado.get('metodo_usado', {})
        }
    
    @staticmethod
    def _salvar_calculos_no_pedido(pedido, dimensionamento, explicacao, custos_resultado, formacao_preco_result, ficha_tecnica):
        """Salva todos os cálculos no pedido - MANTIDO IGUAL"""
        # Dimensões calculadas
        cab = dimensionamento.get('cab', {})
        pedido.largura_cabine_calculada = cab.get('largura')
        pedido.comprimento_cabine_calculado = cab.get('compr')
        pedido.capacidade_cabine_calculada = cab.get('capacidade')
        pedido.tracao_cabine_calculada = cab.get('tracao')
        
        # Custos detalhados
        pedido.custo_materiais = custos_resultado['custo_materiais']
        pedido.custo_mao_obra = custos_resultado['custo_mao_obra_producao']
        pedido.custo_indiretos_fabricacao = custos_resultado['custo_indiretos_fabricacao']
        pedido.custo_instalacao = custos_resultado['custo_instalacao']
        
        # Totais de custo
        pedido.custo_producao = custos_resultado['custo_producao']
        pedido.custo_total_projeto = custos_resultado['custo_total_projeto']
        
        # Formação de preço
        pedido.margem_lucro = custos_resultado['margem_lucro']
        pedido.preco_com_margem = custos_resultado['preco_com_margem']
        pedido.comissao = custos_resultado['comissao']
        pedido.preco_com_comissao = custos_resultado['preco_com_comissao']
        pedido.impostos = custos_resultado['impostos']
        
        # Preço final
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
        
        # Dados detalhados em JSON
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
            },
            # ✅ SALVAR MÉTODO USADO PARA DEBUG
            'metodo_usado': custos_resultado.get('metodo_usado', {})
        }
        
        # Manter componentes_calculados para compatibilidade
        pedido.componentes_calculados = custos_resultado['componentes']
        pedido.formacao_preco = formacao_preco_result
        
        # Atualizar status se necessário
        if pedido.status == 'rascunho':
            if pedido.preco_venda_calculado:
                pedido.status = 'simulado'
        
        pedido.save()
        logger.info(f"Cálculos HÍBRIDOS salvos no pedido {pedido.numero}")

    # ============================================================================
    # MÉTODOS ADICIONAIS MANTIDOS IGUAIS
    # ============================================================================

    @staticmethod
    def recalcular_proposta_existente(pedido):
        """Recalcula uma proposta existente mantendo valores negociados"""
        try:
            logger.info(f"Recalculando proposta existente {pedido.numero} - MODO HÍBRIDO")
            
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
            
            logger.info(f"Recálculo HÍBRIDO finalizado para proposta {pedido.numero}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no recálculo HÍBRIDO da proposta {pedido.numero}: {str(e)}")
            raise ValueError(f"Erro no recálculo: {str(e)}")

    @staticmethod
    def obter_resumo_custos(pedido) -> Dict[str, Any]:
        """Retorna resumo dos custos de uma proposta"""
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
                },
                # ✅ ADICIONAR INFO DO MÉTODO USADO
                'metodo_calculo': pedido.custos_detalhados.get('metodo_usado', {}) if pedido.custos_detalhados else {}
            }
            
            return resumo
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo de custos: {str(e)}")
            return {'erro': str(e)}