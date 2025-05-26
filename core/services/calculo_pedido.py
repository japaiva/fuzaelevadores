# core/services/calculo_pedido.py

import logging
from decimal import Decimal
from typing import Dict, Any, Tuple
from django.db import transaction

from core.models import Produto, ParametrosGerais
from core.services.dimensionamento import DimensionamentoService
from core.services.pricing import PricingService
from core.utils.formatters import extrair_especificacoes_do_pedido

logger = logging.getLogger(__name__)


class CalculoPedidoService:
    """
    Serviço principal para cálculos de pedidos de elevadores
    Integra dimensionamento, custos e preços
    """
    
    @staticmethod
    @transaction.atomic
    def calcular_completo(pedido):
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
            
            # 2. Calcular dimensionamento
            dimensionamento, explicacao_dimensionamento = DimensionamentoService.calcular_dimensionamento_completo(especificacoes)
            
            # 3. Calcular custos de produção
            custos_resultado = CalculoPedidoService._calcular_custos_producao(pedido, dimensionamento)
            
            # 4. Calcular formação de preço
            formacao_preco = PricingService.calcular_formacao_preco(
                custos_resultado['custo_total'], 
                pedido.faturado_por
            )
            
            # 5. Montar ficha técnica
            ficha_tecnica = CalculoPedidoService._montar_ficha_tecnica(pedido, dimensionamento, custos_resultado)
            
            # 6. Salvar tudo no pedido
            CalculoPedidoService._salvar_calculos_no_pedido(
                pedido, dimensionamento, explicacao_dimensionamento, 
                custos_resultado, formacao_preco, ficha_tecnica
            )
            
            logger.info(f"Cálculo completo finalizado para pedido {pedido.numero}")
            
            return {
                'success': True,
                'dimensionamento': dimensionamento,
                'explicacao': explicacao_dimensionamento,
                'custos': custos_resultado,
                'formacao_preco': formacao_preco,
                'ficha_tecnica': ficha_tecnica
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo completo do pedido {pedido.numero}: {str(e)}")
            raise ValueError(f"Erro nos cálculos: {str(e)}")
    
    @staticmethod
    def _calcular_custos_producao(pedido, dimensionamento) -> Dict[str, Any]:
        """
        Calcula os custos de produção (versão hard coded inicial)
        """
        # Buscar todos os custos ativos
        custos_db = {c.codigo: c for c in Custo.objects.filter(ativo=True)}
        
        componentes = {}
        custos_por_categoria = {}
        
        # CABINE - Chapas do Corpo
        custo_cabine = CalculoPedidoService._calcular_custo_cabine(pedido, dimensionamento, custos_db)
        componentes.update(custo_cabine['componentes'])
        custos_por_categoria['CABINE'] = custo_cabine['total']
        
        # CARRINHO - Chassi e Plataforma
        custo_carrinho = CalculoPedidoService._calcular_custo_carrinho(pedido, dimensionamento, custos_db)
        componentes.update(custo_carrinho['componentes'])
        custos_por_categoria['CARRINHO'] = custo_carrinho['total']
        
        # TRAÇÃO - Motor, Cabos, Contrapeso
        custo_tracao = CalculoPedidoService._calcular_custo_tracao(pedido, dimensionamento, custos_db)
        componentes.update(custo_tracao['componentes'])
        custos_por_categoria['TRACAO'] = custo_tracao['total']
        
        # SISTEMAS COMPLEMENTARES - Iluminação, Ventilação
        custo_sistemas = CalculoPedidoService._calcular_custo_sistemas(pedido, dimensionamento, custos_db)
        componentes.update(custo_sistemas['componentes'])
        custos_por_categoria['SIST_COMPLEMENTARES'] = custo_sistemas['total']
        
        # Totais
        custo_materiais = sum(custos_por_categoria.values())
        custo_mao_obra = custo_materiais * Decimal('0.15')  # 15% dos materiais
        custo_instalacao = custo_materiais * Decimal('0.10')  # 10% dos materiais
        custo_total = custo_materiais + custo_mao_obra + custo_instalacao
        
        return {
            'componentes': componentes,
            'custos_por_categoria': custos_por_categoria,
            'custo_materiais': custo_materiais,
            'custo_mao_obra': custo_mao_obra,
            'custo_instalacao': custo_instalacao,
            'custo_total': custo_total
        }
    
    @staticmethod
    def _calcular_custo_cabine(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos da cabine"""
        componentes = {}
        total = Decimal('0')
        
        # Chapas do corpo
        qtd_chapas_corpo = dimensionamento.get('cab', {}).get('chp', {}).get('corpo', 0)
        
        if qtd_chapas_corpo > 0:
            if pedido.material_cabine == "Outro":
                # Material customizado
                componente_customizado = CalculoPedidoService._calcular_componente_customizado(
                    pedido, "CH99", qtd_chapas_corpo, "cabine"
                )
                componentes["CH99_cabine"] = componente_customizado
                total += componente_customizado['valor_total']
            else:
                # Material padrão
                codigo_chapa = CalculoPedidoService._determinar_codigo_chapa(pedido.material_cabine, pedido.espessura_cabine)
                
                if codigo_chapa and codigo_chapa in custos_db:
                    custo_item = custos_db[codigo_chapa]
                    valor_total = Decimal(str(qtd_chapas_corpo)) * custo_item.valor
                    
                    componentes[codigo_chapa] = {
                        'codigo': codigo_chapa,
                        'descricao': custo_item.descricao,
                        'categoria': custo_item.categoria,
                        'subcategoria': custo_item.subcategoria,
                        'quantidade': qtd_chapas_corpo,
                        'unidade': custo_item.unidade,
                        'valor_unitario': custo_item.valor,
                        'valor_total': valor_total,
                        'explicacao': f"Chapas corpo cabine: {qtd_chapas_corpo} unidades"
                    }
                    total += valor_total
                    
                    # Componente adicional para corte/dobra se for Inox
                    if 'Inox' in pedido.material_cabine:
                        codigo_adicional = 'MP0111'  # CH50 → MP0111 (Corte/dobra inox)
                        if codigo_adicional in custos_db:
                            custo_adicional = custos_db[codigo_adicional]
                            valor_adicional = Decimal(str(qtd_chapas_corpo)) * custo_adicional.valor
                            
                            componentes[f"{codigo_adicional}_cabine"] = {
                                'codigo': codigo_adicional,
                                'descricao': custo_adicional.descricao,
                                'categoria': custo_adicional.categoria,
                                'subcategoria': custo_adicional.subcategoria,
                                'quantidade': qtd_chapas_corpo,
                                'unidade': custo_adicional.unidade,
                                'valor_unitario': custo_adicional.valor,
                                'valor_total': valor_adicional,
                                'explicacao': f"Corte/dobra para {qtd_chapas_corpo} chapas de {pedido.material_cabine}"
                            }
                            total += valor_adicional
        
        # Chapas do piso (se por conta da empresa)
        if pedido.piso_cabine == "Por conta da empresa":
            qtd_chapas_piso = dimensionamento.get('cab', {}).get('chp', {}).get('piso', 0)
            
            if qtd_chapas_piso > 0:
                if pedido.material_piso_cabine == "Outro":
                    # Material customizado do piso
                    componente_piso_customizado = CalculoPedidoService._calcular_componente_customizado(
                        pedido, "CH99", qtd_chapas_piso, "piso"
                    )
                    componentes["CH99_piso"] = componente_piso_customizado
                    total += componente_piso_customizado['valor_total']
                else:
                    # Material padrão do piso
                    codigo_piso = CalculoPedidoService._determinar_codigo_piso(pedido.material_piso_cabine)
                    
                    if codigo_piso and codigo_piso in custos_db:
                        custo_piso = custos_db[codigo_piso]
                        valor_piso = Decimal(str(qtd_chapas_piso)) * custo_piso.valor
                        
                        componentes[f"{codigo_piso}_piso"] = {
                            'codigo': codigo_piso,
                            'descricao': custo_piso.descricao,
                            'categoria': custo_piso.categoria,
                            'subcategoria': custo_piso.subcategoria,
                            'quantidade': qtd_chapas_piso,
                            'unidade': custo_piso.unidade,
                            'valor_unitario': custo_piso.valor,
                            'valor_total': valor_piso,
                            'explicacao': f"Chapas piso cabine: {qtd_chapas_piso} unidades"
                        }
                        total += valor_piso
        
        # Parafusos das chapas
        codigo_parafuso_chapa = "MP0113"  # FE01 → MP0113
        if codigo_parafuso_chapa in custos_db:
            custo_parafuso = custos_db[codigo_parafuso_chapa]
            qtd_parafusos = (13 * dimensionamento.get('cab', {}).get('pnl', {}).get('lateral', 0) + 
                            2 * dimensionamento.get('cab', {}).get('pnl', {}).get('fundo', 0) + 
                            2 * dimensionamento.get('cab', {}).get('pnl', {}).get('teto', 0))
            
            if qtd_parafusos > 0:
                valor_parafusos = Decimal(str(qtd_parafusos)) * custo_parafuso.valor
                
                componentes[codigo_parafuso_chapa] = {
                    'codigo': codigo_parafuso_chapa,
                    'descricao': custo_parafuso.descricao,
                    'categoria': custo_parafuso.categoria,
                    'subcategoria': custo_parafuso.subcategoria,
                    'quantidade': qtd_parafusos,
                    'unidade': custo_parafuso.unidade,
                    'valor_unitario': custo_parafuso.valor,
                    'valor_total': valor_parafusos,
                    'explicacao': f"Parafusos chapas: (13 x {dimensionamento.get('cab', {}).get('pnl', {}).get('lateral', 0)}) + (2 x {dimensionamento.get('cab', {}).get('pnl', {}).get('fundo', 0)}) + (2 x {dimensionamento.get('cab', {}).get('pnl', {}).get('teto', 0)}) = {qtd_parafusos}"
                }
                total += valor_parafusos
        
        return {'componentes': componentes, 'total': total}
    
    @staticmethod
    def _calcular_custo_carrinho(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos do carrinho (chassi + plataforma)"""
        componentes = {}
        total = Decimal('0')
        
        capacidade = dimensionamento.get('cab', {}).get('capacidade', 0)
        largura_cabine = dimensionamento.get('cab', {}).get('largura', 0)
        altura_cabine = dimensionamento.get('cab', {}).get('altura', 0)
        comprimento_cabine = dimensionamento.get('cab', {}).get('compr', 0)
        
        # Travessas do chassi
        if capacidade <= 1000:
            codigo_travessa = "MP0122"  # PE01 → MP0122
        elif capacidade <= 1800:
            codigo_travessa = "MP0123"  # PE02 → MP0123
        else:
            codigo_travessa = "MP0124"  # PE03 → MP0124
        
        qtd_travessas = 4
        if capacidade > 2000:
            qtd_travessas += 4
        
        if codigo_travessa in custos_db:
            custo_travessa = custos_db[codigo_travessa]
            # Comprimento = largura cabine + 0.17m
            comprimento_travessa = largura_cabine + 0.17
            quantidade_total_travessas = qtd_travessas * comprimento_travessa
            valor_travessas = Decimal(str(quantidade_total_travessas)) * custo_travessa.valor
            
            componentes[codigo_travessa] = {
                'codigo': codigo_travessa,
                'descricao': custo_travessa.descricao,
                'categoria': custo_travessa.categoria,
                'subcategoria': custo_travessa.subcategoria,
                'quantidade': quantidade_total_travessas,
                'unidade': custo_travessa.unidade,
                'valor_unitario': custo_travessa.valor,
                'valor_total': valor_travessas,
                'explicacao': f"Travessas chassi: {qtd_travessas} x {comprimento_travessa:.2f}m ({'base 4' + (', +4 se > 2000kg' if capacidade > 2000 else '')})"
            }
            total += valor_travessas
        
        # Longarinas do chassi
        if capacidade <= 1500:
            codigo_longarina = "MP0125"  # PE04 → MP0125
        elif capacidade <= 2000:
            codigo_longarina = "MP0126"  # PE05 → MP0126
        else:
            codigo_longarina = "MP0127"  # PE06 → MP0127
        
        qtd_longarinas = 2
        
        if codigo_longarina in custos_db:
            custo_longarina = custos_db[codigo_longarina]
            comprimento_longarina = altura_cabine + 0.70
            quantidade_total_longarinas = qtd_longarinas * comprimento_longarina
            valor_longarinas = Decimal(str(quantidade_total_longarinas)) * custo_longarina.valor
            
            componentes[codigo_longarina] = {
                'codigo': codigo_longarina,
                'descricao': custo_longarina.descricao,
                'categoria': custo_longarina.categoria,
                'subcategoria': custo_longarina.subcategoria,
                'quantidade': quantidade_total_longarinas,
                'unidade': custo_longarina.unidade,
                'valor_unitario': custo_longarina.valor,
                'valor_total': valor_longarinas,
                'explicacao': f"Longarinas chassi: {qtd_longarinas} x {comprimento_longarina:.2f}m (altura + 0.70m)"
            }
            total += valor_longarinas
        
        # Parafusos para chassi
        codigo_parafuso_chassi = "MP0114"  # FE02 → MP0114
        if codigo_parafuso_chassi in custos_db:
            custo_parafuso = custos_db[codigo_parafuso_chassi]
            qtd_parafusos_chassi = 65
            valor_parafusos_chassi = Decimal(str(qtd_parafusos_chassi)) * custo_parafuso.valor
            
            componentes[f"{codigo_parafuso_chassi}_chassi"] = {
                'codigo': codigo_parafuso_chassi,
                'descricao': custo_parafuso.descricao,
                'categoria': custo_parafuso.categoria,
                'subcategoria': custo_parafuso.subcategoria,
                'quantidade': qtd_parafusos_chassi,
                'unidade': custo_parafuso.unidade,
                'valor_unitario': custo_parafuso.valor,
                'valor_total': valor_parafusos_chassi,
                'explicacao': f"Parafusos chassi: {qtd_parafusos_chassi} unidades fixas"
            }
            total += valor_parafusos_chassi
        
        # Perfis externos da plataforma
        if capacidade <= 1000:
            codigo_perfil_externo = "MP0131"  # PE10 → MP0131
        elif capacidade <= 1800:
            codigo_perfil_externo = "MP0132"  # PE11 → MP0132
        else:
            codigo_perfil_externo = "MP0133"  # PE12 → MP0133
        
        if codigo_perfil_externo in custos_db:
            custo_perfil_externo = custos_db[codigo_perfil_externo]
            # 2 perfis na largura + 2 perfis no comprimento
            qtd_perfis_largura = 2 * largura_cabine
            qtd_perfis_comprimento = 2 * comprimento_cabine
            quantidade_total_externos = qtd_perfis_largura + qtd_perfis_comprimento
            valor_perfis_externos = Decimal(str(quantidade_total_externos)) * custo_perfil_externo.valor
            
            componentes[codigo_perfil_externo] = {
                'codigo': codigo_perfil_externo,
                'descricao': custo_perfil_externo.descricao,
                'categoria': custo_perfil_externo.categoria,
                'subcategoria': custo_perfil_externo.subcategoria,
                'quantidade': quantidade_total_externos,
                'unidade': custo_perfil_externo.unidade,
                'valor_unitario': custo_perfil_externo.valor,
                'valor_total': valor_perfis_externos,
                'explicacao': f"Perfis externos: (2 x {largura_cabine:.2f}m) + (2 x {comprimento_cabine:.2f}m) = {quantidade_total_externos:.2f}m"
            }
            total += valor_perfis_externos
        
        # Perfis internos da plataforma
        if capacidade <= 1000:
            codigo_perfil_interno = "MP0128"  # PE07 → MP0128
        elif capacidade <= 1800:
            codigo_perfil_interno = "MP0129"  # PE08 → MP0129
        else:
            codigo_perfil_interno = "MP0130"  # PE09 → MP0130
        
        if codigo_perfil_interno in custos_db:
            custo_perfil_interno = custos_db[codigo_perfil_interno]
            qtd_perfis_internos = round(largura_cabine / 0.35)  # 35cm = 0.35m
            quantidade_total_internos = qtd_perfis_internos * comprimento_cabine
            valor_perfis_internos = Decimal(str(quantidade_total_internos)) * custo_perfil_interno.valor
            
            componentes[codigo_perfil_interno] = {
                'codigo': codigo_perfil_interno,
                'descricao': custo_perfil_interno.descricao,
                'categoria': custo_perfil_interno.categoria,
                'subcategoria': custo_perfil_interno.subcategoria,
                'quantidade': quantidade_total_internos,
                'unidade': custo_perfil_interno.unidade,
                'valor_unitario': custo_perfil_interno.valor,
                'valor_total': valor_perfis_internos,
                'explicacao': f"Perfis internos: {qtd_perfis_internos} x {comprimento_cabine:.2f}m (largura/0.35 arredondado)"
            }
            total += valor_perfis_internos
        
        # Parafusos para plataforma
        if codigo_parafuso_chassi in custos_db:  # Reutiliza o mesmo código
            qtd_parafusos_plataforma = 24 + (4 * qtd_perfis_internos)
            valor_parafusos_plataforma = Decimal(str(qtd_parafusos_plataforma)) * custo_parafuso.valor
            
            componentes[f"{codigo_parafuso_chassi}_plataforma"] = {
                'codigo': codigo_parafuso_chassi,
                'descricao': custo_parafuso.descricao,
                'categoria': custo_parafuso.categoria,
                'subcategoria': custo_parafuso.subcategoria,
                'quantidade': qtd_parafusos_plataforma,
                'unidade': custo_parafuso.unidade,
                'valor_unitario': custo_parafuso.valor,
                'valor_total': valor_parafusos_plataforma,
                'explicacao': f"Parafusos plataforma: 24 + (4 x {qtd_perfis_internos}) = {qtd_parafusos_plataforma}"
            }
            total += valor_parafusos_plataforma
        
        # Barras roscadas
        codigo_barra_roscada = "MP0146"  # PE25 → MP0146
        if codigo_barra_roscada in custos_db:
            custo_barra = custos_db[codigo_barra_roscada]
            comprimento_barra_unitario = (comprimento_cabine / 2) / 0.60
            qtd_barras_necessarias = 4
            comprimento_total_barras = comprimento_barra_unitario * qtd_barras_necessarias
            qtd_barras_compradas = round(comprimento_total_barras / 3 + 0.5)  # Arredonda para cima (3m cada)
            valor_barras = Decimal(str(qtd_barras_compradas)) * custo_barra.valor
            
            componentes[codigo_barra_roscada] = {
                'codigo': codigo_barra_roscada,
                'descricao': custo_barra.descricao,
                'categoria': custo_barra.categoria,
                'subcategoria': custo_barra.subcategoria,
                'quantidade': qtd_barras_compradas,
                'unidade': custo_barra.unidade,
                'valor_unitario': custo_barra.valor,
                'valor_total': valor_barras,
                'explicacao': f"Barras roscadas: {comprimento_total_barras:.2f}m total = {qtd_barras_compradas} barras de 3m"
            }
            total += valor_barras
        
        # Parafusos e suportes para barras roscadas
        codigo_parafuso_barra = "MP0113"  # FE01 → MP0113
        if codigo_parafuso_barra in custos_db:
            custo_parafuso_barra = custos_db[codigo_parafuso_barra]
            qtd_parafusos_barra = 16  # 4 parafusos por barra x 4 barras
            valor_parafusos_barra = Decimal(str(qtd_parafusos_barra)) * custo_parafuso_barra.valor
            
            componentes[f"{codigo_parafuso_barra}_barra"] = {
                'codigo': codigo_parafuso_barra,
                'descricao': custo_parafuso_barra.descricao,
                'categoria': custo_parafuso_barra.categoria,
                'subcategoria': custo_parafuso_barra.subcategoria,
                'quantidade': qtd_parafusos_barra,
                'unidade': custo_parafuso_barra.unidade,
                'valor_unitario': custo_parafuso_barra.valor,
                'valor_total': valor_parafusos_barra,
                'explicacao': f"Parafusos barras roscadas: {qtd_parafusos_barra} unidades (4 por barra)"
            }
            total += valor_parafusos_barra
        
        # Suportes para barras roscadas
        codigo_suporte_barra = "MP0147"  # PE26 → MP0147
        if codigo_suporte_barra in custos_db:
            custo_suporte_barra = custos_db[codigo_suporte_barra]
            qtd_suportes = 4  # 1 suporte por barra
            valor_suportes = Decimal(str(qtd_suportes)) * custo_suporte_barra.valor
            
            componentes[codigo_suporte_barra] = {
                'codigo': codigo_suporte_barra,
                'descricao': custo_suporte_barra.descricao,
                'categoria': custo_suporte_barra.categoria,
                'subcategoria': custo_suporte_barra.subcategoria,
                'quantidade': qtd_suportes,
                'unidade': custo_suporte_barra.unidade,
                'valor_unitario': custo_suporte_barra.valor,
                'valor_total': valor_suportes,
                'explicacao': f"Suportes barra roscada: {qtd_suportes} unidades (1 por barra)"
            }
            total += valor_suportes
        
        return {'componentes': componentes, 'total': total}
    
    @staticmethod
    def _calcular_custo_tracao(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos de tração"""
        componentes = {}
        total = Decimal('0')
        
        capacidade = dimensionamento.get('cab', {}).get('capacidade', 0)
        tracao_cabine = dimensionamento.get('cab', {}).get('tracao', 0)
        largura_cabine = dimensionamento.get('cab', {}).get('largura', 0)
        
        if pedido.acionamento == 'Motor':
            # Motor e sistema de tração
            codigo_motor = "MP0119"  # MO02 → MP0119 (Motor 7,5 cv - 630 kg)
            if codigo_motor in custos_db:
                custo_motor = custos_db[codigo_motor]
                
                componentes[codigo_motor] = {
                    'codigo': codigo_motor,
                    'descricao': custo_motor.descricao,
                    'categoria': custo_motor.categoria,
                    'subcategoria': custo_motor.subcategoria,
                    'quantidade': 1,
                    'unidade': custo_motor.unidade,
                    'valor_unitario': custo_motor.valor,
                    'valor_total': custo_motor.valor,
                    'explicacao': "Motor para acionamento"
                }
                total += custo_motor.valor
            
            # Polias (se tração 2x1)
            if pedido.tracao == "2x1":
                qtd_polias = 2 if largura_cabine > 2 else 1
                codigo_polia = "MP0134"  # PE13 → MP0134
                
                if codigo_polia in custos_db:
                    custo_polia = custos_db[codigo_polia]
                    valor_polias = Decimal(str(qtd_polias)) * custo_polia.valor
                    
                    componentes[codigo_polia] = {
                        'codigo': codigo_polia,
                        'descricao': custo_polia.descricao,
                        'categoria': custo_polia.categoria,
                        'subcategoria': custo_polia.subcategoria,
                        'quantidade': qtd_polias,
                        'unidade': custo_polia.unidade,
                        'valor_unitario': custo_polia.valor,
                        'valor_total': valor_polias,
                        'explicacao': f"Polias para tração 2x1: {qtd_polias} unidades ({'2 se largura > 2m' if qtd_polias == 2 else '1 se largura <= 2m'})"
                    }
                    total += valor_polias
                
                # Travessa da polia (se 2 polias)
                if qtd_polias > 1:
                    codigo_travessa_polia = "MP0136"  # PE15 → MP0136 (Cabo aço 3/8 usado como travessa)
                    if codigo_travessa_polia in custos_db:
                        custo_travessa_polia = custos_db[codigo_travessa_polia]
                        comprimento_travessa = largura_cabine / 2
                        valor_travessa_polia = comprimento_travessa * custo_travessa_polia.valor
                        
                        componentes[codigo_travessa_polia] = {
                            'codigo': codigo_travessa_polia,
                            'descricao': custo_travessa_polia.descricao,
                            'categoria': custo_travessa_polia.categoria,
                            'subcategoria': custo_travessa_polia.subcategoria,
                            'quantidade': comprimento_travessa,
                            'unidade': custo_travessa_polia.unidade,
                            'valor_unitario': custo_travessa_polia.valor,
                            'valor_total': valor_travessa_polia,
                            'explicacao': f"Travessa da polia: {comprimento_travessa:.2f}m (largura cabine / 2)"
                        }
                        total += valor_travessa_polia
            
            # Cabo de aço
            codigo_cabo = "MP0135"  # PE14 → MP0135 (Cabo aço 5/16)
            if codigo_cabo in custos_db:
                custo_cabo = custos_db[codigo_cabo]
                comprimento_cabo = float(pedido.altura_poco)
                
                if pedido.tracao == "2x1":
                    comprimento_cabo *= 2
                comprimento_cabo += 5  # 5m adicionais
                
                valor_cabo = comprimento_cabo * custo_cabo.valor
                
                componentes[codigo_cabo] = {
                    'codigo': codigo_cabo,
                    'descricao': custo_cabo.descricao,
                    'categoria': custo_cabo.categoria,
                    'subcategoria': custo_cabo.subcategoria,
                    'quantidade': comprimento_cabo,
                    'unidade': custo_cabo.unidade,
                    'valor_unitario': custo_cabo.valor,
                    'valor_total': valor_cabo,
                    'explicacao': f"Cabo de aço: {comprimento_cabo:.1f}m ({'2x altura' if pedido.tracao == '2x1' else 'altura'} + 5m)"
                }
                total += valor_cabo
            
            # Contrapeso
            contrapeso_tipo = CalculoPedidoService._determinar_tipo_contrapeso(pedido, tracao_cabine)
            if contrapeso_tipo and contrapeso_tipo in custos_db:
                custo_contrapeso = custos_db[contrapeso_tipo]
                
                componentes[contrapeso_tipo] = {
                    'codigo': contrapeso_tipo,
                    'descricao': custo_contrapeso.descricao,
                    'categoria': custo_contrapeso.categoria,
                    'subcategoria': custo_contrapeso.subcategoria,
                    'quantidade': 1,
                    'unidade': custo_contrapeso.unidade,
                    'valor_unitario': custo_contrapeso.valor,
                    'valor_total': custo_contrapeso.valor,
                    'explicacao': f"Contrapeso {pedido.contrapeso.lower()}"
                }
                total += custo_contrapeso.valor
            
            # Pedras para contrapeso
            codigo_pedra, qtd_pedras = CalculoPedidoService._calcular_pedras_contrapeso(contrapeso_tipo, tracao_cabine)
            if codigo_pedra and codigo_pedra in custos_db and qtd_pedras > 0:
                custo_pedra = custos_db[codigo_pedra]
                valor_pedras = Decimal(str(qtd_pedras)) * custo_pedra.valor
                
                componentes[codigo_pedra] = {
                    'codigo': codigo_pedra,
                    'descricao': custo_pedra.descricao,
                    'categoria': custo_pedra.categoria,
                    'subcategoria': custo_pedra.subcategoria,
                    'quantidade': qtd_pedras,
                    'unidade': custo_pedra.unidade,
                    'valor_unitario': custo_pedra.valor,
                    'valor_total': valor_pedras,
                    'explicacao': f"Pedras contrapeso: {qtd_pedras} unidades (tração {tracao_cabine:.0f}kg)"
                }
                total += valor_pedras
            
            # Guias do elevador
            codigo_guia_elevador = "MP0142"  # PE21 → MP0142
            if codigo_guia_elevador in custos_db:
                custo_guia = custos_db[codigo_guia_elevador]
                qtd_guias = round(float(pedido.altura_poco) / 5 * 2)
                valor_guias = Decimal(str(qtd_guias)) * custo_guia.valor
                
                componentes[codigo_guia_elevador] = {
                    'codigo': codigo_guia_elevador,
                    'descricao': custo_guia.descricao,
                    'categoria': custo_guia.categoria,
                    'subcategoria': custo_guia.subcategoria,
                    'quantidade': qtd_guias,
                    'unidade': custo_guia.unidade,
                    'valor_unitario': custo_guia.valor,
                    'valor_total': valor_guias,
                    'explicacao': f"Guias elevador: {qtd_guias} unidades ((altura / 5) * 2)"
                }
                total += valor_guias
            
            # Suportes das guias do elevador
            codigo_suporte_guia = "MP0143"  # PE22 → MP0143
            if codigo_suporte_guia in custos_db:
                custo_suporte = custos_db[codigo_suporte_guia]
                qtd_suportes = round(float(pedido.altura_poco) / 5 * 2)
                valor_suportes = Decimal(str(qtd_suportes)) * custo_suporte.valor
                
                componentes[codigo_suporte_guia] = {
                    'codigo': codigo_suporte_guia,
                    'descricao': custo_suporte.descricao,
                    'categoria': custo_suporte.categoria,
                    'subcategoria': custo_suporte.subcategoria,
                    'quantidade': qtd_suportes,
                    'unidade': custo_suporte.unidade,
                    'valor_unitario': custo_suporte.valor,
                    'valor_total': valor_suportes,
                    'explicacao': f"Suportes guia elevador: {qtd_suportes} unidades"
                }
                total += valor_suportes
            
            # Guias do contrapeso
            if contrapeso_tipo:
                codigo_guia_contrapeso = "MP0144"  # PE23 → MP0144
                if codigo_guia_contrapeso in custos_db:
                    custo_guia_cp = custos_db[codigo_guia_contrapeso]
                    qtd_guias_cp = round(float(pedido.altura_poco) / 5 * 2)
                    valor_guias_cp = Decimal(str(qtd_guias_cp)) * custo_guia_cp.valor
                    
                    componentes[codigo_guia_contrapeso] = {
                        'codigo': codigo_guia_contrapeso,
                        'descricao': custo_guia_cp.descricao,
                        'categoria': custo_guia_cp.categoria,
                        'subcategoria': custo_guia_cp.subcategoria,
                        'quantidade': qtd_guias_cp,
                        'unidade': custo_guia_cp.unidade,
                        'valor_unitario': custo_guia_cp.valor,
                        'valor_total': valor_guias_cp,
                        'explicacao': f"Guias contrapeso: {qtd_guias_cp} unidades"
                    }
                    total += valor_guias_cp
                
                # Suportes das guias do contrapeso
                codigo_suporte_guia_cp = "MP0145"  # PE24 → MP0145
                if codigo_suporte_guia_cp in custos_db:
                    custo_suporte_cp = custos_db[codigo_suporte_guia_cp]
                    qtd_suportes_cp = 4 + (pedido.pavimentos * 2)
                    valor_suportes_cp = Decimal(str(qtd_suportes_cp)) * custo_suporte_cp.valor
                    
                    componentes[codigo_suporte_guia_cp] = {
                        'codigo': codigo_suporte_guia_cp,
                        'descricao': custo_suporte_cp.descricao,
                        'categoria': custo_suporte_cp.categoria,
                        'subcategoria': custo_suporte_cp.subcategoria,
                        'quantidade': qtd_suportes_cp,
                        'unidade': custo_suporte_cp.unidade,
                        'valor_unitario': custo_suporte_cp.valor,
                        'valor_total': valor_suportes_cp,
                        'explicacao': f"Suportes guia contrapeso: {qtd_suportes_cp} unidades (4 + pavimentos * 2)"
                    }
                    total += valor_suportes_cp
        
        elif pedido.acionamento == 'Hidraulico':
            # Sistema hidráulico
            codigo_hidraulico = "MP0118"  # MO01 → MP0118
            if codigo_hidraulico in custos_db:
                custo_hidraulico = custos_db[codigo_hidraulico]
                
                componentes[codigo_hidraulico] = {
                    'codigo': codigo_hidraulico,
                    'descricao': custo_hidraulico.descricao,
                    'categoria': custo_hidraulico.categoria,
                    'subcategoria': custo_hidraulico.subcategoria,
                    'quantidade': 1,
                    'unidade': custo_hidraulico.unidade,
                    'valor_unitario': custo_hidraulico.valor,
                    'valor_total': custo_hidraulico.valor,
                    'explicacao': "Sistema hidráulico completo"
                }
                total += custo_hidraulico.valor
        
        # Parafusos gerais para tração
        codigo_parafuso_tracao = "MP0115"  # FE03 → MP0115
        if codigo_parafuso_tracao in custos_db:
            custo_parafuso = custos_db[codigo_parafuso_tracao]
            qtd_parafusos = 50  # Quantidade estimada
            valor_parafusos = Decimal(str(qtd_parafusos)) * custo_parafuso.valor
            
            componentes[codigo_parafuso_tracao] = {
                'codigo': codigo_parafuso_tracao,
                'descricao': custo_parafuso.descricao,
                'categoria': custo_parafuso.categoria,
                'subcategoria': custo_parafuso.subcategoria,
                'quantidade': qtd_parafusos,
                'unidade': custo_parafuso.unidade,
                'valor_unitario': custo_parafuso.valor,
                'valor_total': valor_parafusos,
                'explicacao': f"Parafusos sistema de tração: {qtd_parafusos} unidades"
            }
            total += valor_parafusos
        
        return {'componentes': componentes, 'total': total}
    
    @staticmethod
    def _determinar_tipo_contrapeso(pedido, tracao_cabine: float) -> str:
        """Determina o tipo de contrapeso baseado na posição e dimensões"""
        if pedido.contrapeso == "Lateral":
            if float(pedido.comprimento_poco) < 1.90:
                return "MP0137" if tracao_cabine <= 1000 else "MP0138"  # PE16/PE17 → MP0137/MP0138
            else:
                return "MP0139"  # PE18 → MP0139
        elif pedido.contrapeso == "Traseiro":
            if float(pedido.largura_poco) < 1.90:
                return "MP0137" if tracao_cabine <= 1000 else "MP0138"  # PE16/PE17 → MP0137/MP0138
            else:
                return "MP0139"  # PE18 → MP0139
        return None
    
    @staticmethod
    def _calcular_pedras_contrapeso(contrapeso_tipo: str, tracao_cabine: float) -> Tuple[str, int]:
        """Calcula a quantidade de pedras necessárias"""
        if contrapeso_tipo in ["MP0137", "MP0138"]:  # PE16/PE17 → MP0137/MP0138
            codigo_pedra = "MP0140"  # PE19 → MP0140 (Pedra pequena)
            qtd_pedras = int(tracao_cabine / 45)
        elif contrapeso_tipo == "MP0139":  # PE18 → MP0139
            codigo_pedra = "MP0141"  # PE20 → MP0141 (Pedra grande)
            qtd_pedras = int(tracao_cabine / 75)
        else:
            return None, 0
        
        return codigo_pedra, qtd_pedras
    
    @staticmethod
    def _calcular_custo_sistemas(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos dos sistemas complementares"""
        componentes = {}
        total = Decimal('0')
        
        comprimento_cabine = dimensionamento.get('cab', {}).get('compr', 0)
        
        # Iluminação
        qtd_lampadas = 2 if comprimento_cabine <= 1.80 else 4
        codigo_lampada = "MP0174"  # CC01 → MP0174
        
        if codigo_lampada in custos_db:
            custo_lampada = custos_db[codigo_lampada]
            valor_lampadas = Decimal(str(qtd_lampadas)) * custo_lampada.valor
            
            componentes[codigo_lampada] = {
                'codigo': codigo_lampada,
                'descricao': custo_lampada.descricao,
                'categoria': custo_lampada.categoria,
                'subcategoria': custo_lampada.subcategoria,
                'quantidade': qtd_lampadas,
                'unidade': custo_lampada.unidade,
                'valor_unitario': custo_lampada.valor,
                'valor_total': valor_lampadas,
                'explicacao': f"Lâmpadas LED: {qtd_lampadas} unidades ({'2 se <= 1,80m' if qtd_lampadas == 2 else '4 se > 1,80m'})"
            }
            total += valor_lampadas
        
        # Ventilação (só para elevador de passageiro)
        if 'Passageiro' in pedido.modelo_elevador:
            codigo_ventilador = "MP0175"  # CC02 → MP0175
            if codigo_ventilador in custos_db:
                custo_ventilador = custos_db[codigo_ventilador]
                
                componentes[codigo_ventilador] = {
                    'codigo': codigo_ventilador,
                    'descricao': custo_ventilador.descricao,
                    'categoria': custo_ventilador.categoria,
                    'subcategoria': custo_ventilador.subcategoria,
                    'quantidade': 1,
                    'unidade': custo_ventilador.unidade,
                    'valor_unitario': custo_ventilador.valor,
                    'valor_total': custo_ventilador.valor,
                    'explicacao': "Ventilador para elevador de passageiro"
                }
                total += custo_ventilador.valor
        
        return {'componentes': componentes, 'total': total}
    
    @staticmethod
    def _determinar_codigo_chapa(material_cabine: str, espessura_cabine: str) -> str:
        """Determina o código da chapa baseado no material e espessura"""
        if "Inox 304" in material_cabine:
            return "MP0103" if espessura_cabine == "1,2" else "MP0104"  # CH03 → MP0103, CH04 → MP0104
        elif "Inox 430" in material_cabine:
            return "MP0101" if espessura_cabine == "1,2" else "MP0102"  # CH01 → MP0101, CH02 → MP0102
        elif "Chapa Pintada" in material_cabine:
            return "MP0105" if espessura_cabine == "1,2" else "MP0106"  # CH05 → MP0105, CH06 → MP0106
        elif "Alumínio" in material_cabine:
            return "MP0107" if espessura_cabine == "1,2" else "MP0108"  # CH07 → MP0107, CH08 → MP0108
        elif material_cabine == "Outro":
            return "MP0999"  # Código para material customizado
        return None
    
    @staticmethod
    def _determinar_codigo_piso(material_piso: str) -> str:
        """Determina o código do piso baseado no material"""
        if material_piso == "Antiderrapante":
            return "MP0109"  # CH09 → MP0109
        elif material_piso == "Outro":
            return "MP0999"  # Código para material customizado
        return "MP0110"  # CH10 → MP0110 (Padrão)
    
    @staticmethod
    def _calcular_componente_customizado(pedido, codigo_base: str, quantidade: float, tipo_material: str) -> Dict[str, Any]:
        """Calcula componente com material customizado (Outro)"""
        if tipo_material == "cabine":
            nome_material = pedido.material_cabine_outro
            valor_material = pedido.valor_cabine_outro or Decimal('0')
        elif tipo_material == "piso":
            nome_material = pedido.material_piso_cabine_outro
            valor_material = pedido.valor_piso_cabine_outro or Decimal('0')
        elif tipo_material == "porta_cabine":
            nome_material = pedido.material_porta_cabine_outro
            valor_material = pedido.valor_porta_cabine_outro or Decimal('0')
        elif tipo_material == "porta_pavimento":
            nome_material = pedido.material_porta_pavimento_outro
            valor_material = pedido.valor_porta_pavimento_outro or Decimal('0')
        else:
            nome_material = "Material Customizado"
            valor_material = Decimal('0')
        
        valor_total = Decimal(str(quantidade)) * valor_material
        
        return {
            'codigo': f"MP0999_{tipo_material}",  # Código customizado
            'descricao': nome_material or "Material Customizado",
            'categoria': 'CUSTOMIZADO',
            'subcategoria': 'Material Outro',
            'quantidade': quantidade,
            'unidade': 'un',
            'valor_unitario': valor_material,
            'valor_total': valor_total,
            'explicacao': f"Material customizado: {nome_material} - {quantidade} unidades"
        }
    
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
    def _salvar_calculos_no_pedido(pedido, dimensionamento, explicacao, custos_resultado, formacao_preco, ficha_tecnica):
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
        pedido.preco_venda_calculado = formacao_preco['preco_sem_impostos']
        pedido.preco_sem_impostos = formacao_preco['preco_sem_impostos']
        
        # Dados detalhados em JSON
        pedido.ficha_tecnica = ficha_tecnica
        pedido.dimensionamento_detalhado = dimensionamento
        pedido.explicacao_calculo = explicacao
        pedido.custos_detalhados = {
            'componentes': custos_resultado['componentes'],
            'custos_por_categoria': {k: float(v) for k, v in custos_resultado['custos_por_categoria'].items()},
            'resumo': {
                'custo_materiais': float(custos_resultado['custo_materiais']),
                'custo_mao_obra': float(custos_resultado['custo_mao_obra']),
                'custo_instalacao': float(custos_resultado['custo_instalacao']),
                'custo_total': float(custos_resultado['custo_total'])
            }
        }
        pedido.componentes_calculados = custos_resultado['componentes']
        pedido.formacao_preco = formacao_preco
        
        # Atualizar status se necessário
        if pedido.status == 'rascunho':
            pedido.status = 'simulado'
        
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
            param = ParametroCalculo.objects.get(parametro=nome, ativo=True)
            return param.valor
        except ParametroCalculo.DoesNotExist:
            return default
    
    @staticmethod
    def get_parametros_categoria(categoria: str) -> Dict[str, Any]:
        """Busca todos os parâmetros de uma categoria"""
        params = ParametroCalculo.objects.filter(categoria=categoria, ativo=True)
        return {param.parametro: param.valor for param in params}
    
    @staticmethod
    def get_todos_parametros() -> Dict[str, Any]:
        """Busca todos os parâmetros ativos"""
        params = ParametroCalculo.objects.filter(ativo=True)
        return {param.parametro: param.valor for param in params}