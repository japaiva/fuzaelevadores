# core/services/calculos/calculo_cabine.py - VERSÃO REFATORADA PARA ESTRUTURA HIERÁRQUICA

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CalculoCabineService:
    """
    Serviço especializado no cálculo de componentes da cabine
    CORRIGIDO para seguir a lógica original do calculations.py
    REFATORADO para retornar estrutura hierárquica de componentes.
    """
    
    @staticmethod
    def calcular_custo_cabine(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos da cabine - VERSÃO REFATORADA ESTRUTURADA"""
        
        # Estrutura para armazenar os componentes detalhados por subcategoria
        componentes_cabine_estruturado = {
            "chapas_corpo": {"total_subcategoria": Decimal('0'), "itens": {}},
            "chapas_piso": {"total_subcategoria": Decimal('0'), "itens": {}},
            "fixacao_cabine": {"total_subcategoria": Decimal('0'), "itens": {}} # Nova subcategoria para parafusos
        }
        total_cabine_categoria = Decimal('0')
        
        # Chapas do corpo
        qtd_chapas_corpo = dimensionamento.get('cab', {}).get('chp', {}).get('corpo', 0)
        
        if qtd_chapas_corpo > 0:
            if pedido.material_cabine == "Outro":
                # Material customizado
                componente_customizado = CalculoCabineService._calcular_componente_customizado(
                    pedido, "MP0999", qtd_chapas_corpo, "cabine"
                )
                componentes_cabine_estruturado["chapas_corpo"]["itens"]["MP0999_cabine"] = componente_customizado
                componentes_cabine_estruturado["chapas_corpo"]["total_subcategoria"] += Decimal(str(componente_customizado['valor_total']))
                total_cabine_categoria += Decimal(str(componente_customizado['valor_total']))
            else:
                # Material padrão
                codigo_chapa = CalculoCabineService._determinar_codigo_chapa(pedido.material_cabine, pedido.espessura_cabine)
                
                if codigo_chapa and codigo_chapa in custos_db:
                    produto = custos_db[codigo_chapa]
                    valor_unitario = produto.custo_medio or produto.preco_venda or Decimal('100')
                    valor_total = Decimal(str(qtd_chapas_corpo)) * valor_unitario
                    
                    componentes_cabine_estruturado["chapas_corpo"]["itens"][codigo_chapa] = {
                        'codigo': codigo_chapa,
                        'descricao': produto.nome,
                        'categoria': produto.grupo.nome if produto.grupo else 'MATERIAL',
                        'subcategoria': produto.subgrupo.nome if produto.subgrupo else 'Chapas',
                        'quantidade': qtd_chapas_corpo,
                        'unidade': produto.unidade_medida,
                        'valor_unitario': float(valor_unitario),
                        'valor_total': float(valor_total),
                        'explicacao': f"Chapas corpo cabine: {qtd_chapas_corpo} unidades"
                    }
                    componentes_cabine_estruturado["chapas_corpo"]["total_subcategoria"] += valor_total
                    total_cabine_categoria += valor_total
                    
                    # Componente adicional para corte/dobra se for Inox ou Alumínio
                    if 'Inox' in pedido.material_cabine:
                        codigo_adicional = 'MP0111'  # CH50 → MP0111 (Corte/dobra inox)
                        if codigo_adicional in custos_db:
                            produto_adicional = custos_db[codigo_adicional]
                            valor_unitario_adicional = produto_adicional.custo_medio or produto_adicional.preco_venda or Decimal('50')
                            valor_adicional = Decimal(str(qtd_chapas_corpo)) * valor_unitario_adicional
                            
                            componentes_cabine_estruturado["chapas_corpo"]["itens"][f"{codigo_adicional}_corte"] = {
                                'codigo': codigo_adicional,
                                'descricao': produto_adicional.nome,
                                'categoria': produto_adicional.grupo.nome if produto_adicional.grupo else 'SERVICO',
                                'subcategoria': produto_adicional.subgrupo.nome if produto_adicional.subgrupo else 'Corte/Dobra',
                                'quantidade': qtd_chapas_corpo,
                                'unidade': produto_adicional.unidade_medida,
                                'valor_unitario': float(valor_unitario_adicional),
                                'valor_total': float(valor_adicional),
                                'explicacao': f"Corte/dobra para {qtd_chapas_corpo} chapas de {pedido.material_cabine}"
                            }
                            componentes_cabine_estruturado["chapas_corpo"]["total_subcategoria"] += valor_adicional
                            total_cabine_categoria += valor_adicional
                    elif 'Alumínio' in pedido.material_cabine:
                        codigo_adicional = 'MP0112'  # CH51 → MP0112 (Corte/dobra alumínio)
                        if codigo_adicional in custos_db:
                            produto_adicional = custos_db[codigo_adicional]
                            valor_unitario_adicional = produto_adicional.custo_medio or produto_adicional.preco_venda or Decimal('45')
                            valor_adicional = Decimal(str(qtd_chapas_corpo)) * valor_unitario_adicional
                            
                            componentes_cabine_estruturado["chapas_corpo"]["itens"][f"{codigo_adicional}_corte"] = {
                                'codigo': codigo_adicional,
                                'descricao': produto_adicional.nome,
                                'categoria': produto_adicional.grupo.nome if produto_adicional.grupo else 'SERVICO',
                                'subcategoria': produto_adicional.subgrupo.nome if produto_adicional.subgrupo else 'Corte/Dobra',
                                'quantidade': qtd_chapas_corpo,
                                'unidade': produto_adicional.unidade_medida,
                                'valor_unitario': float(valor_unitario_adicional),
                                'valor_total': float(valor_adicional),
                                'explicacao': f"Corte/dobra para {qtd_chapas_corpo} chapas de {pedido.material_cabine}"
                            }
                            componentes_cabine_estruturado["chapas_corpo"]["total_subcategoria"] += valor_adicional
                            total_cabine_categoria += valor_adicional
        
        # Parafusos das chapas do corpo (agora em 'fixacao_cabine')
        codigo_parafuso_chapa = "MP0113"  # FE01 → MP0113
        if codigo_parafuso_chapa in custos_db:
            produto_parafuso = custos_db[codigo_parafuso_chapa]
            valor_unitario_parafuso = produto_parafuso.custo_medio or produto_parafuso.preco_venda or Decimal('2')
            qtd_parafusos = (13 * dimensionamento.get('cab', {}).get('pnl', {}).get('lateral', 0) + 
                            2 * dimensionamento.get('cab', {}).get('pnl', {}).get('fundo', 0) + 
                            2 * dimensionamento.get('cab', {}).get('pnl', {}).get('teto', 0))
            
            if qtd_parafusos > 0:
                valor_parafusos = Decimal(str(qtd_parafusos)) * valor_unitario_parafuso
                
                componentes_cabine_estruturado["fixacao_cabine"]["itens"][codigo_parafuso_chapa] = {
                    'codigo': codigo_parafuso_chapa,
                    'descricao': produto_parafuso.nome,
                    'categoria': produto_parafuso.grupo.nome if produto_parafuso.grupo else 'FIXACAO',
                    'subcategoria': produto_parafuso.subgrupo.nome if produto_parafuso.subgrupo else 'Parafusos',
                    'quantidade': qtd_parafusos,
                    'unidade': produto_parafuso.unidade_medida,
                    'valor_unitario': float(valor_unitario_parafuso),
                    'valor_total': float(valor_parafusos),
                    'explicacao': f"Parafusos chapas: (13 x {dimensionamento.get('cab', {}).get('pnl', {}).get('lateral', 0)}) + (2 x {dimensionamento.get('cab', {}).get('pnl', {}).get('fundo', 0)}) + (2 x {dimensionamento.get('cab', {}).get('pnl', {}).get('teto', 0)}) = {qtd_parafusos}"
                }
                componentes_cabine_estruturado["fixacao_cabine"]["total_subcategoria"] += valor_parafusos
                total_cabine_categoria += valor_parafusos
        
        # Chapas do piso - SEMPRE calcular (seguindo lógica original)
        qtd_chapas_piso = dimensionamento.get('cab', {}).get('chp', {}).get('piso', 0)
        
        if qtd_chapas_piso > 0:
            # Determinar código do piso baseado na lógica original
            if pedido.piso_cabine == "Por conta da empresa":
                if pedido.material_piso_cabine == "Antiderrapante":
                    codigo_piso = "MP0109"  # CH09 → MP0109
                elif pedido.material_piso_cabine == "Outro":
                    codigo_piso = "MP0999"  # Material customizado
                else:
                    codigo_piso = "MP0110"  # CH10 → MP0110 (padrão)
            else:
                # Por conta do cliente - mas ainda precisa das chapas base
                codigo_piso = "MP0110"  # CH10 → MP0110
            
            if codigo_piso == "MP0999":
                # Material customizado do piso
                componente_piso_customizado = CalculoCabineService._calcular_componente_customizado(
                    pedido, "MP0999", qtd_chapas_piso, "piso"
                )
                componentes_cabine_estruturado["chapas_piso"]["itens"]["MP0999_piso"] = componente_piso_customizado
                componentes_cabine_estruturado["chapas_piso"]["total_subcategoria"] += Decimal(str(componente_piso_customizado['valor_total']))
                total_cabine_categoria += Decimal(str(componente_piso_customizado['valor_total']))
            else:
                # Material padrão do piso
                if codigo_piso in custos_db:
                    produto_piso = custos_db[codigo_piso]
                    valor_unitario_piso = produto_piso.custo_medio or produto_piso.preco_venda or Decimal('80')
                    valor_piso = Decimal(str(qtd_chapas_piso)) * valor_unitario_piso
                    
                    componentes_cabine_estruturado["chapas_piso"]["itens"][codigo_piso] = {
                        'codigo': codigo_piso,
                        'descricao': produto_piso.nome,
                        'categoria': produto_piso.grupo.nome if produto_piso.grupo else 'MATERIAL',
                        'subcategoria': produto_piso.subgrupo.nome if produto_piso.subgrupo else 'Chapas Piso',
                        'quantidade': qtd_chapas_piso,
                        'unidade': produto_piso.unidade_medida,
                        'valor_unitario': float(valor_unitario_piso),
                        'valor_total': float(valor_piso),
                        'explicacao': f"Chapas piso cabine: {qtd_chapas_piso} unidades"
                    }
                    componentes_cabine_estruturado["chapas_piso"]["total_subcategoria"] += valor_piso
                    total_cabine_categoria += valor_piso
            
            # Parafusos para o piso (agora em 'fixacao_cabine')
            codigo_parafuso_piso = "MP0116"  # FE04 → MP0116
            if codigo_parafuso_piso in custos_db:
                produto_parafuso_piso = custos_db[codigo_parafuso_piso]
                valor_unitario_parafuso_piso = produto_parafuso_piso.custo_medio or produto_parafuso_piso.preco_venda or Decimal('1.5')
                qtd_parafusos_piso = 13 * qtd_chapas_piso
                valor_parafusos_piso = Decimal(str(qtd_parafusos_piso)) * valor_unitario_parafuso_piso
                
                componentes_cabine_estruturado["fixacao_cabine"]["itens"][codigo_parafuso_piso] = {
                    'codigo': codigo_parafuso_piso,
                    'descricao': produto_parafuso_piso.nome,
                    'categoria': produto_parafuso_piso.grupo.nome if produto_parafuso_piso.grupo else 'FIXACAO',
                    'subcategoria': produto_parafuso_piso.subgrupo.nome if produto_parafuso_piso.subgrupo else 'Parafusos',
                    'quantidade': qtd_parafusos_piso,
                    'unidade': produto_parafuso_piso.unidade_medida,
                    'valor_unitario': float(valor_unitario_parafuso_piso),
                    'valor_total': float(valor_parafusos_piso),
                    'explicacao': f"Parafusos piso: 13 x {qtd_chapas_piso} = {qtd_parafusos_piso}"
                }
                componentes_cabine_estruturado["fixacao_cabine"]["total_subcategoria"] += valor_parafusos_piso
                total_cabine_categoria += valor_parafusos_piso
        
        # Converte os totais de subcategorias para float antes de retornar para JSONField
        for sub_cat in componentes_cabine_estruturado.values():
            sub_cat['total_subcategoria'] = float(sub_cat['total_subcategoria'])
        
        return {
            'componentes': componentes_cabine_estruturado, # Retorna a estrutura aninhada
            'total': total_cabine_categoria # Total da categoria principal (Cabine)
        }
    
    # =============================================================================
    # MÉTODOS AUXILIARES
    # =============================================================================
    
    @staticmethod
    def _determinar_codigo_chapa(material_cabine: str, espessura_cabine: str) -> str:
        """Determina o código da chapa baseado no material e espessura"""
        # Conversão seguindo a lógica original: CH01-CH08 → MP0101-MP0108
        if "Inox 304" in material_cabine:
            return "MP0103" if espessura_cabine == "1,2" else "MP0104"  # CH03 → MP0103, CH04 → MP0104
        elif "Inox 430" in material_cabine:
            return "MP0101" if espessura_cabine == "1,2" else "MP0102"  # CH01 → MP0101, CH02 → MP0102
        elif "Chapa Pintada" in material_cabine:
            return "MP0105" if espessura_cabine == "1,2" else "MP0106"  # CH05 → MP0105, CH06 → MP0106
        elif "Alumínio" in material_cabine:
            return "MP0107" if espessura_cabine == "1,2" else "MP0108"  # CH07 → MP0107, CH08 → MP0108
        return None
    
    @staticmethod
    def _calcular_componente_customizado(pedido, codigo_base: str, quantidade: float, tipo_material: str) -> Dict[str, Any]:
        """Calcula componente com material customizado (Outro)"""
        if tipo_material == "cabine":
            nome_material = pedido.material_cabine_outro
            valor_material = pedido.valor_cabine_outro or Decimal('0')
        elif tipo_material == "piso":
            nome_material = pedido.material_piso_cabine_outro
            valor_material = pedido.valor_piso_cabine_outro or Decimal('0')
        else:
            nome_material = "Material Customizado"
            valor_material = Decimal('0')
        
        valor_total = Decimal(str(quantidade)) * valor_material
        
        return {
            'codigo': f"{codigo_base}_{tipo_material}", # Ajustei o código base para incluir tipo_material para unicidade
            'descricao': nome_material or "Material Customizado",
            'categoria': 'CUSTOMIZADO',
            'subcategoria': 'Material Outro',
            'quantidade': quantidade,
            'unidade': 'un',
            'valor_unitario': float(valor_material),
            'valor_total': float(valor_total),
            'explicacao': f"Material customizado: {nome_material} - {quantidade} unidades"
        }