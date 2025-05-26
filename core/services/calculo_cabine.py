# core/services/calculos/calculo_cabine.py - CÁLCULO COMPLETO DA CABINE

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CalculoCabineService:
    """
    Serviço especializado no cálculo de componentes da cabine
    Replica EXATAMENTE a lógica do arquivo original
    """
    
    @staticmethod
    def calcular_custo_cabine(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos da cabine - VERSÃO COMPLETA"""
        componentes = {}
        total = Decimal('0')
        
        # Chapas do corpo
        qtd_chapas_corpo = dimensionamento.get('cab', {}).get('chp', {}).get('corpo', 0)
        
        if qtd_chapas_corpo > 0:
            if pedido.material_cabine == "Outro":
                # Material customizado
                componente_customizado = CalculoCabineService._calcular_componente_customizado(
                    pedido, "CH99", qtd_chapas_corpo, "cabine"
                )
                componentes["CH99_cabine"] = componente_customizado
                total += componente_customizado['valor_total']
            else:
                # Material padrão
                codigo_chapa = CalculoCabineService._determinar_codigo_chapa(pedido.material_cabine, pedido.espessura_cabine)
                
                if codigo_chapa and codigo_chapa in custos_db:
                    produto = custos_db[codigo_chapa]
                    valor_unitario = produto.custo_medio or produto.preco_venda or Decimal('100')
                    valor_total = Decimal(str(qtd_chapas_corpo)) * valor_unitario
                    
                    componentes[codigo_chapa] = {
                        'codigo': codigo_chapa,
                        'descricao': produto.nome,
                        'categoria': produto.grupo.nome if produto.grupo else 'MATERIAL',
                        'subcategoria': produto.subgrupo.nome if produto.subgrupo else 'Corpo Cabine',
                        'quantidade': qtd_chapas_corpo,
                        'unidade': produto.unidade_medida,
                        'valor_unitario': float(valor_unitario),
                        'valor_total': float(valor_total),
                        'explicacao': f"Chapas corpo cabine: {qtd_chapas_corpo} unidades"
                    }
                    total += valor_total
                    
                    # Componente adicional para corte/dobra se for Inox
                    if 'Inox' in pedido.material_cabine:
                        codigo_adicional = 'MP0111'  # CH50 → MP0111 (Corte/dobra inox)
                        if codigo_adicional in custos_db:
                            produto_adicional = custos_db[codigo_adicional]
                            valor_unitario_adicional = produto_adicional.custo_medio or produto_adicional.preco_venda or Decimal('50')
                            valor_adicional = Decimal(str(qtd_chapas_corpo)) * valor_unitario_adicional
                            
                            componentes[f"{codigo_adicional}_cabine"] = {
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
                            total += valor_adicional
        
        # Chapas do piso (se por conta da empresa)
        if pedido.piso_cabine == "Por conta da empresa":
            qtd_chapas_piso = dimensionamento.get('cab', {}).get('chp', {}).get('piso', 0)
            
            if qtd_chapas_piso > 0:
                if pedido.material_piso_cabine == "Outro":
                    # Material customizado do piso
                    componente_piso_customizado = CalculoCabineService._calcular_componente_customizado(
                        pedido, "CH99", qtd_chapas_piso, "piso"
                    )
                    componentes["CH99_piso"] = componente_piso_customizado
                    total += componente_piso_customizado['valor_total']
                else:
                    # Material padrão do piso
                    codigo_piso = CalculoCabineService._determinar_codigo_piso(pedido.material_piso_cabine)
                    
                    if codigo_piso and codigo_piso in custos_db:
                        produto_piso = custos_db[codigo_piso]
                        valor_unitario_piso = produto_piso.custo_medio or produto_piso.preco_venda or Decimal('80')
                        valor_piso = Decimal(str(qtd_chapas_piso)) * valor_unitario_piso
                        
                        componentes[f"{codigo_piso}_piso"] = {
                            'codigo': codigo_piso,
                            'descricao': produto_piso.nome,
                            'categoria': produto_piso.grupo.nome if produto_piso.grupo else 'MATERIAL',
                            'subcategoria': produto_piso.subgrupo.nome if produto_piso.subgrupo else 'Piso Cabine',
                            'quantidade': qtd_chapas_piso,
                            'unidade': produto_piso.unidade_medida,
                            'valor_unitario': float(valor_unitario_piso),
                            'valor_total': float(valor_piso),
                            'explicacao': f"Chapas piso cabine: {qtd_chapas_piso} unidades"
                        }
                        total += valor_piso
        
        # Parafusos das chapas
        codigo_parafuso_chapa = "MP0113"  # FE01 → MP0113
        if codigo_parafuso_chapa in custos_db:
            produto_parafuso = custos_db[codigo_parafuso_chapa]
            valor_unitario_parafuso = produto_parafuso.custo_medio or produto_parafuso.preco_venda or Decimal('2')
            qtd_parafusos = (13 * dimensionamento.get('cab', {}).get('pnl', {}).get('lateral', 0) + 
                            2 * dimensionamento.get('cab', {}).get('pnl', {}).get('fundo', 0) + 
                            2 * dimensionamento.get('cab', {}).get('pnl', {}).get('teto', 0))
            
            if qtd_parafusos > 0:
                valor_parafusos = Decimal(str(qtd_parafusos)) * valor_unitario_parafuso
                
                componentes[codigo_parafuso_chapa] = {
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
                total += valor_parafusos
        
        return {'componentes': componentes, 'total': total}
    
    # =============================================================================
    # MÉTODOS AUXILIARES
    # =============================================================================
    
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
        else:
            nome_material = "Material Customizado"
            valor_material = Decimal('0')
        
        valor_total = Decimal(str(quantidade)) * valor_material
        
        return {
            'codigo': f"MP0999_{tipo_material}",
            'descricao': nome_material or "Material Customizado",
            'categoria': 'CUSTOMIZADO',
            'subcategoria': 'Material Outro',
            'quantidade': quantidade,
            'unidade': 'un',
            'valor_unitario': float(valor_material),
            'valor_total': float(valor_total),
            'explicacao': f"Material customizado: {nome_material} - {quantidade} unidades"
        }