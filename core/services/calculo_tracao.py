# core/services/calculos/calculo_tracao.py - VERSÃO REFATORADA PARA ESTRUTURA HIERÁRQUICA

import logging
from decimal import Decimal
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class CalculoTracaoService:
    """
    Serviço para cálculo completo do sistema de tração
    CORRIGIDO seguindo calculations.py original
    REFATORADO para retornar estrutura hierárquica de componentes.
    """
    
    @staticmethod
    def calcular_custo_tracao(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos de tração - VERSÃO REFATORADA ESTRUTURADA"""
        
        # Estrutura para armazenar os componentes detalhados por subcategoria
        componentes_tracao_estruturado = {
            "acionamento": {"total_subcategoria": Decimal('0'), "itens": {}},
            "tracionamento": {"total_subcategoria": Decimal('0'), "itens": {}},
            "contrapeso": {"total_subcategoria": Decimal('0'), "itens": {}},
            "guias": {"total_subcategoria": Decimal('0'), "itens": {}}
        }
        total_tracao_categoria = Decimal('0')
        
        capacidade = dimensionamento.get('cab', {}).get('capacidade', 0)
        tracao_cabine = dimensionamento.get('cab', {}).get('tracao', 0)
        largura_cabine = dimensionamento.get('cab', {}).get('largura', 0)
        
        # === ACIONAMENTO ===
        
        if pedido.acionamento == 'Hidraulico':
            # Sistema hidráulico
            codigo_hidraulico = "05.03.00002"  # MO01 → 02.01.00003
            if codigo_hidraulico in custos_db:
                produto_hidraulico = custos_db[codigo_hidraulico]
                valor_unitario_hidraulico = produto_hidraulico.custo_medio or produto_hidraulico.preco_venda or Decimal('3000')
                
                componentes_tracao_estruturado["acionamento"]["itens"][codigo_hidraulico] = {
                    'codigo': codigo_hidraulico,
                    'descricao': produto_hidraulico.nome,
                    'categoria': produto_hidraulico.grupo.nome if produto_hidraulico.grupo else 'HIDRAULICO',
                    'subcategoria': produto_hidraulico.subgrupo.nome if produto_hidraulico.subgrupo else 'Acionamento',
                    'quantidade': 1,
                    'unidade': produto_hidraulico.unidade_medida,
                    'valor_unitario': float(valor_unitario_hidraulico),
                    'valor_total': float(valor_unitario_hidraulico),
                    'explicacao': "Sistema hidráulico completo"
                }
                componentes_tracao_estruturado["acionamento"]["total_subcategoria"] += valor_unitario_hidraulico
                total_tracao_categoria += valor_unitario_hidraulico
        
        elif pedido.acionamento == 'Motor':
            
            # === TRACIONAMENTO (Componentes específicos para Motor) ===
            
            # Motor elétrico (MO02 → 02.01.00004)
            codigo_motor = "06.01.00004"  # MO02 → 02.01.00004 (Motor 7,5 cv - 630 kg)
            if codigo_motor in custos_db:
                produto_motor = custos_db[codigo_motor]
                valor_unitario_motor = produto_motor.custo_medio or produto_motor.preco_venda or Decimal('2000')
                
                componentes_tracao_estruturado["tracionamento"]["itens"][codigo_motor] = {
                    'codigo': codigo_motor,
                    'descricao': produto_motor.nome,
                    'categoria': produto_motor.grupo.nome if produto_motor.grupo else 'MOTOR',
                    'subcategoria': produto_motor.subgrupo.nome if produto_motor.subgrupo else 'Tracionamento',
                    'quantidade': 1,
                    'unidade': produto_motor.unidade_medida,
                    'valor_unitario': float(valor_unitario_motor),
                    'valor_total': float(valor_unitario_motor),
                    'explicacao': "Motor para acionamento"
                }
                componentes_tracao_estruturado["tracionamento"]["total_subcategoria"] += valor_unitario_motor
                total_tracao_categoria += valor_unitario_motor
            
            # Polias (se tração 2x1)
            if pedido.tracao == "2x1":
                qtd_polias = 1
                if largura_cabine > 2:
                    qtd_polias = 2
                
                if qtd_polias > 0:
                    codigo_polia = "03.03.00006"  # PE13 → 01.03.00014
                    
                    if codigo_polia in custos_db:
                        produto_polia = custos_db[codigo_polia]
                        valor_unitario_polia = produto_polia.custo_medio or produto_polia.preco_venda or Decimal('300')
                        valor_polias = Decimal(str(qtd_polias)) * valor_unitario_polia
                        
                        componentes_tracao_estruturado["tracionamento"]["itens"][codigo_polia] = {
                            'codigo': codigo_polia,
                            'descricao': produto_polia.nome,
                            'categoria': produto_polia.grupo.nome if produto_polia.grupo else 'TRACAO',
                            'subcategoria': produto_polia.subgrupo.nome if produto_polia.subgrupo else 'Tracionamento',
                            'quantidade': qtd_polias,
                            'unidade': produto_polia.unidade_medida,
                            'valor_unitario': float(valor_unitario_polia),
                            'valor_total': float(valor_polias),
                            'explicacao': f"Polias para tração 2x1: {qtd_polias} unidades ({'2 se largura > 2m' if qtd_polias == 2 else '1 se largura <= 2m'})"
                        }
                        componentes_tracao_estruturado["tracionamento"]["total_subcategoria"] += valor_polias
                        total_tracao_categoria += valor_polias
                
                # Travessa da polia (se 2 polias)
                if qtd_polias > 1:
                    codigo_travessa_polia = "03.03.00004"  # PE15 → 01.03.00015
                    if codigo_travessa_polia in custos_db:
                        produto_travessa_polia = custos_db[codigo_travessa_polia]
                        valor_unitario_travessa = produto_travessa_polia.custo_medio or produto_travessa_polia.preco_venda or Decimal('20')
                        comprimento_travessa = largura_cabine / 2
                        valor_travessa_polia = comprimento_travessa * valor_unitario_travessa
                        
                        componentes_tracao_estruturado["tracionamento"]["itens"][codigo_travessa_polia] = {
                            'codigo': codigo_travessa_polia,
                            'descricao': produto_travessa_polia.nome,
                            'categoria': produto_travessa_polia.grupo.nome if produto_travessa_polia.grupo else 'TRACAO',
                            'subcategoria': produto_travessa_polia.subgrupo.nome if produto_travessa_polia.subgrupo else 'Tracionamento',
                            'quantidade': float(comprimento_travessa),
                            'unidade': produto_travessa_polia.unidade_medida,
                            'valor_unitario': float(valor_unitario_travessa),
                            'valor_total': float(valor_travessa_polia),
                            'explicacao': f"Travessa da polia: {comprimento_travessa:.2f}m (largura cabine / 2)"
                        }
                        componentes_tracao_estruturado["tracionamento"]["total_subcategoria"] += valor_travessa_polia
                        total_tracao_categoria += valor_travessa_polia
            
            # Cabo de aço
            codigo_cabo = "03.04.00003"  # PE14 → 02.02.00001 (Cabo aço 5/16)
            if codigo_cabo in custos_db:
                produto_cabo = custos_db[codigo_cabo]
                valor_unitario_cabo = produto_cabo.custo_medio or produto_cabo.preco_venda or Decimal('25')
                comprimento_cabo = float(pedido.altura_poco)
                
                if pedido.tracao == "2x1":
                    comprimento_cabo *= 2
                comprimento_cabo += 5  # 5m adicionais
                
                valor_cabo = Decimal(str(comprimento_cabo)) * valor_unitario_cabo
                
                componentes_tracao_estruturado["tracionamento"]["itens"][codigo_cabo] = {
                    'codigo': codigo_cabo,
                    'descricao': produto_cabo.nome,
                    'categoria': produto_cabo.grupo.nome if produto_cabo.grupo else 'TRACAO',
                    'subcategoria': produto_cabo.subgrupo.nome if produto_cabo.subgrupo else 'Tracionamento',
                    'quantidade': comprimento_cabo,
                    'unidade': produto_cabo.unidade_medida,
                    'valor_unitario': float(valor_unitario_cabo),
                    'valor_total': float(valor_cabo),
                    'explicacao': f"Cabo de aço: {comprimento_cabo:.1f}m ({'2x altura' if pedido.tracao == '2x1' else 'altura'} + 5m)"
                }
                componentes_tracao_estruturado["tracionamento"]["total_subcategoria"] += valor_cabo
                total_tracao_categoria += valor_cabo
            
            # === CONTRAPESO ===
            
            # Contrapeso
            contrapeso_tipo = CalculoTracaoService._determinar_tipo_contrapeso(pedido, tracao_cabine)
            if contrapeso_tipo and contrapeso_tipo in custos_db:
                produto_contrapeso = custos_db[contrapeso_tipo]
                valor_unitario_contrapeso = produto_contrapeso.custo_medio or produto_contrapeso.preco_venda or Decimal('800')
                
                componentes_tracao_estruturado["contrapeso"]["itens"][contrapeso_tipo] = {
                    'codigo': contrapeso_tipo,
                    'descricao': produto_contrapeso.nome,
                    'categoria': produto_contrapeso.grupo.nome if produto_contrapeso.grupo else 'CONTRAPESO',
                    'subcategoria': produto_contrapeso.subgrupo.nome if produto_contrapeso.subgrupo else 'Contrapeso',
                    'quantidade': 1,
                    'unidade': produto_contrapeso.unidade_medida,
                    'valor_unitario': float(valor_unitario_contrapeso),
                    'valor_total': float(valor_unitario_contrapeso),
                    'explicacao': f"Contrapeso {pedido.contrapeso.lower()}"
                }
                componentes_tracao_estruturado["contrapeso"]["total_subcategoria"] += valor_unitario_contrapeso
                total_tracao_categoria += valor_unitario_contrapeso
            
            # Pedras para contrapeso
            codigo_pedra, qtd_pedras = CalculoTracaoService._calcular_pedras_contrapeso(contrapeso_tipo, tracao_cabine)
            if codigo_pedra and codigo_pedra in custos_db and qtd_pedras > 0:
                produto_pedra = custos_db[codigo_pedra]
                valor_unitario_pedra = produto_pedra.custo_medio or produto_pedra.preco_venda or Decimal('45')
                valor_pedras = Decimal(str(qtd_pedras)) * valor_unitario_pedra
                
                componentes_tracao_estruturado["contrapeso"]["itens"][codigo_pedra] = {
                    'codigo': codigo_pedra,
                    'descricao': produto_pedra.nome,
                    'categoria': produto_pedra.grupo.nome if produto_pedra.grupo else 'CONTRAPESO',
                    'subcategoria': produto_pedra.subgrupo.nome if produto_pedra.subgrupo else 'Contrapeso',
                    'quantidade': qtd_pedras,
                    'unidade': produto_pedra.unidade_medida,
                    'valor_unitario': float(valor_unitario_pedra),
                    'valor_total': float(valor_pedras),
                    'explicacao': f"Pedras contrapeso: {qtd_pedras} unidades (tração {tracao_cabine:.0f}kg)"
                }
                componentes_tracao_estruturado["contrapeso"]["total_subcategoria"] += valor_pedras
                total_tracao_categoria += valor_pedras
            
            # === GUIAS ===
            
            # Guias do elevador
            codigo_guia_elevador = "03.01.00005"  # PE21 → 02.03.00001
            if codigo_guia_elevador in custos_db:
                produto_guia = custos_db[codigo_guia_elevador]
                valor_unitario_guia = produto_guia.custo_medio or produto_guia.preco_venda or Decimal('180')
                qtd_guias = round(float(pedido.altura_poco) / 5 * 2)
                valor_guias = Decimal(str(qtd_guias)) * valor_unitario_guia
                
                componentes_tracao_estruturado["guias"]["itens"][codigo_guia_elevador] = {
                    'codigo': codigo_guia_elevador,
                    'descricao': produto_guia.nome,
                    'categoria': produto_guia.grupo.nome if produto_guia.grupo else 'GUIAS',
                    'subcategoria': produto_guia.subgrupo.nome if produto_guia.subgrupo else 'Guia',
                    'quantidade': qtd_guias,
                    'unidade': produto_guia.unidade_medida,
                    'valor_unitario': float(valor_unitario_guia),
                    'valor_total': float(valor_guias),
                    'explicacao': f"Guias elevador: {qtd_guias} unidades ((altura / 5) * 2)"
                }
            # Suportes das guias do elevador
            codigo_suporte_guia = "03.02.0010"  # PE22 → 02.03.00002
            if codigo_suporte_guia in custos_db:
                produto_suporte = custos_db[codigo_suporte_guia]
                valor_unitario_suporte = produto_suporte.custo_medio or produto_suporte.preco_venda or Decimal('35')
                qtd_suportes = round(float(pedido.altura_poco) / 5 * 2)
                valor_suportes = Decimal(str(qtd_suportes)) * valor_unitario_suporte
                
                componentes_tracao_estruturado["guias"]["itens"][codigo_suporte_guia] = {
                    'codigo': codigo_suporte_guia,
                    'descricao': produto_suporte.nome,
                    'categoria': produto_suporte.grupo.nome if produto_suporte.grupo else 'GUIAS',
                    'subcategoria': produto_suporte.subgrupo.nome if produto_suporte.subgrupo else 'Guia',
                    'quantidade': qtd_suportes,
                    'unidade': produto_suporte.unidade_medida,
                    'valor_unitario': float(valor_unitario_suporte),
                    'valor_total': float(valor_suportes),
                    'explicacao': f"Suportes guia elevador: {qtd_suportes} unidades"
                }
                componentes_tracao_estruturado["guias"]["total_subcategoria"] += valor_suportes
                total_tracao_categoria += valor_suportes
            
            # Guias do contrapeso
            if contrapeso_tipo:
                codigo_guia_contrapeso = "03.01.00004"  # PE23 → 02.03.00003
                if codigo_guia_contrapeso in custos_db:
                    produto_guia_cp = custos_db[codigo_guia_contrapeso]
                    valor_unitario_guia_cp = produto_guia_cp.custo_medio or produto_guia_cp.preco_venda or Decimal('160')
                    qtd_guias_cp = round(float(pedido.altura_poco) / 5 * 2)
                    valor_guias_cp = Decimal(str(qtd_guias_cp)) * valor_unitario_guia_cp
                    
                    componentes_tracao_estruturado["guias"]["itens"][codigo_guia_contrapeso] = {
                        'codigo': codigo_guia_contrapeso,
                        'descricao': produto_guia_cp.nome,
                        'categoria': produto_guia_cp.grupo.nome if produto_guia_cp.grupo else 'GUIAS',
                        'subcategoria': produto_guia_cp.subgrupo.nome if produto_guia_cp.subgrupo else 'Guia',
                        'quantidade': qtd_guias_cp,
                        'unidade': produto_guia_cp.unidade_medida,
                        'valor_unitario': float(valor_unitario_guia_cp),
                        'valor_total': float(valor_guias_cp),
                        'explicacao': f"Guias contrapeso: {qtd_guias_cp} unidades"
                    }
                    componentes_tracao_estruturado["guias"]["total_subcategoria"] += valor_guias_cp
                    total_tracao_categoria += valor_guias_cp
                
                # Suportes das guias do contrapeso
                codigo_suporte_guia_cp = "03.02.00011"  # PE24 → 02.03.00004
                if codigo_suporte_guia_cp in custos_db:
                    produto_suporte_cp = custos_db[codigo_suporte_guia_cp]
                    valor_unitario_suporte_cp = produto_suporte_cp.custo_medio or produto_suporte_cp.preco_venda or Decimal('30')
                    qtd_suportes_cp = 4 + (pedido.pavimentos * 2)
                    valor_suportes_cp = Decimal(str(qtd_suportes_cp)) * valor_unitario_suporte_cp
                    
                    componentes_tracao_estruturado["guias"]["itens"][codigo_suporte_guia_cp] = {
                        'codigo': codigo_suporte_guia_cp,
                        'descricao': produto_suporte_cp.nome,
                        'categoria': produto_suporte_cp.grupo.nome if produto_suporte_cp.grupo else 'GUIAS',
                        'subcategoria': produto_suporte_cp.subgrupo.nome if produto_suporte_cp.subgrupo else 'Guia',
                        'quantidade': qtd_suportes_cp,
                        'unidade': produto_suporte_cp.unidade_medida,
                        'valor_unitario': float(valor_unitario_suporte_cp),
                        'valor_total': float(valor_suportes_cp),
                        'explicacao': f"Suportes guia contrapeso: {qtd_suportes_cp} unidades (4 + pavimentos * 2)"
                    }
                    componentes_tracao_estruturado["guias"]["total_subcategoria"] += valor_suportes_cp
                    total_tracao_categoria += valor_suportes_cp
        
        # Parafusos gerais para tração
        codigo_parafuso_tracao = "01.02.00007"  # FE03 → 01.02.00007
        if codigo_parafuso_tracao in custos_db:
            produto_parafuso = custos_db[codigo_parafuso_tracao]
            valor_unitario_parafuso = produto_parafuso.custo_medio or produto_parafuso.preco_venda or Decimal('4')
            qtd_parafusos = 50  # Quantidade estimada
            valor_parafusos = Decimal(str(qtd_parafusos)) * valor_unitario_parafuso
            
            componentes_tracao_estruturado["guias"]["itens"][codigo_parafuso_tracao] = {
                'codigo': codigo_parafuso_tracao,
                'descricao': produto_parafuso.nome,
                'categoria': produto_parafuso.grupo.nome if produto_parafuso.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso.subgrupo.nome if produto_parafuso.subgrupo else 'Guia',
                'quantidade': qtd_parafusos,
                'unidade': produto_parafuso.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso),
                'valor_total': float(valor_parafusos),
                'explicacao': f"Parafusos sistema de tração: {qtd_parafusos} unidades"
            }
            componentes_tracao_estruturado["guias"]["total_subcategoria"] += valor_parafusos
            total_tracao_categoria += valor_parafusos
        
        # Converte os totais de subcategorias para float antes de retornar para JSONField
        for sub_cat in componentes_tracao_estruturado.values():
            sub_cat['total_subcategoria'] = float(sub_cat['total_subcategoria'])
            
        return {
            'componentes': componentes_tracao_estruturado, # Retorna a estrutura aninhada
            'total': total_tracao_categoria # Total da categoria principal (Tração)
        }
    
    # =============================================================================
    # MÉTODOS AUXILIARES
    # =============================================================================
    
    @staticmethod
    def _determinar_tipo_contrapeso(pedido, tracao_cabine: float) -> str:
        """Determina o tipo de contrapeso baseado na posição e dimensões"""
        if pedido.contrapeso == "Lateral":
            if float(pedido.comprimento_poco) < 1.90:
                return "03.06.00001" if tracao_cabine <= 1000 else "03.06.00001"  # PE16/PE17 → 02.04.00001/02.04.00002
            else:
                return "03.06.00002"  # PE18 → 02.04.00003
        elif pedido.contrapeso == "Traseiro":
            if float(pedido.largura_poco) < 1.90:
                return "03.06.00001" if tracao_cabine <= 1000 else "03.06.00001"  # PE16/PE17 → 02.04.00001/02.04.00002
            else:
                return "03.06.00002"  # PE18 → 02.04.00003
        return None
    
    @staticmethod
    def _calcular_pedras_contrapeso(contrapeso_tipo: str, tracao_cabine: float) -> Tuple[str, int]:
        """Calcula a quantidade de pedras necessárias"""
        if contrapeso_tipo in ["03.06.00001", "03.06.00001"]:  # PE16/PE17 → 02.04.00001/02.04.00002
            codigo_pedra = "03.06.00006"  # PE19 → 02.04.00004 (Pedra pequena)
            qtd_pedras = int(tracao_cabine / 45)
        elif contrapeso_tipo == "03.06.00002":  # PE18 → 02.04.00003
            codigo_pedra = "03.06.00005"  # PE20 → 02.04.00005 (Pedra grande)
            qtd_pedras = int(tracao_cabine / 75)
        else:
            return None, 0
        
        return codigo_pedra, qtd_pedras