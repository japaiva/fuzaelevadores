# core/services/calculos/calculo_sistemas.py - APENAS COMPONENTES REAIS

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CalculoSistemasService:
    """
    Serviço para cálculo dos sistemas complementares
    APENAS componentes que existem no arquivo original
    """
    
    @staticmethod
    def calcular_custo_sistemas(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos dos sistemas complementares - APENAS COMPONENTES REAIS"""
        componentes = {}
        total = Decimal('0')
        
        comprimento_cabine = dimensionamento.get('cab', {}).get('compr', 0)
        
        # Iluminação
        qtd_lampadas = 2 if comprimento_cabine <= 1.80 else 4
        codigo_lampada = "MP0174"  # CC01 → MP0174
        
        if codigo_lampada in custos_db:
            produto_lampada = custos_db[codigo_lampada]
            valor_unitario_lampada = produto_lampada.custo_medio or produto_lampada.preco_venda or Decimal('150')
            valor_lampadas = Decimal(str(qtd_lampadas)) * valor_unitario_lampada
            
            componentes[codigo_lampada] = {
                'codigo': codigo_lampada,
                'descricao': produto_lampada.nome,
                'categoria': produto_lampada.grupo.nome if produto_lampada.grupo else 'ELETRICO',
                'subcategoria': produto_lampada.subgrupo.nome if produto_lampada.subgrupo else 'Iluminação',
                'quantidade': qtd_lampadas,
                'unidade': produto_lampada.unidade_medida,
                'valor_unitario': float(valor_unitario_lampada),
                'valor_total': float(valor_lampadas),
                'explicacao': f"Lâmpadas LED: {qtd_lampadas} unidades ({'2 se <= 1,80m' if qtd_lampadas == 2 else '4 se > 1,80m'})"
            }
            total += valor_lampadas
        
        # Ventilação (só para elevador de passageiro)
        if 'Passageiro' in pedido.modelo_elevador:
            codigo_ventilador = "MP0175"  # CC02 → MP0175
            if codigo_ventilador in custos_db:
                produto_ventilador = custos_db[codigo_ventilador]
                valor_unitario_ventilador = produto_ventilador.custo_medio or produto_ventilador.preco_venda or Decimal('200')
                
                componentes[codigo_ventilador] = {
                    'codigo': codigo_ventilador,
                    'descricao': produto_ventilador.nome,
                    'categoria': produto_ventilador.grupo.nome if produto_ventilador.grupo else 'ELETRICO',
                    'subcategoria': produto_ventilador.subgrupo.nome if produto_ventilador.subgrupo else 'Ventilação',
                    'quantidade': 1,
                    'unidade': produto_ventilador.unidade_medida,
                    'valor_unitario': float(valor_unitario_ventilador),
                    'valor_total': float(valor_unitario_ventilador),
                    'explicacao': "Ventilador para elevador de passageiro"
                }
                total += valor_unitario_ventilador
        
        return {'componentes': componentes, 'total': total}
    
    # =============================================================================
    # MÉTODOS AUXILIARES
    # =============================================================================
    
    @staticmethod
    def _calcular_componente_customizado(pedido, codigo_base: str, quantidade: float, tipo_material: str) -> Dict[str, Any]:
        """Calcula componente com material customizado (Outro)"""
        if tipo_material == "porta_cabine":
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