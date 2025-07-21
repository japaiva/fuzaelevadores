# core/services/calculos/calculo_sistemas.py - VERSÃO CORRIGIDA
# ATUALIZAÇÃO: Usa EXCLUSIVAMENTE a propriedade 'custo_total' do produto.

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CalculoSistemasService:
    """
    Serviço para cálculo dos sistemas complementares
    CORRIGIDO seguindo calculations.py original
    REFATORADO para retornar estrutura hierárquica de componentes.
    """

    @staticmethod
    def calcular_custo_sistemas(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos dos sistemas complementares - VERSÃO REFATORADA ESTRUTURADA"""

        # Estrutura para armazenar os componentes detalhados por subcategoria
        componentes_sistemas_estruturado = {
            "iluminacao": {"total_subcategoria": Decimal('0'), "itens": {}},
            "ventilacao": {"total_subcategoria": Decimal('0'), "itens": {}}
        }
        total_sistemas_categoria = Decimal('0')

        comprimento_cabine = dimensionamento.get('cab', {}).get('compr', 0)

        # === ILUMINAÇÃO ===

        # Iluminação (seguindo lógica original)
        qtd_lampadas = 2 if comprimento_cabine <= 1.80 else 4
        codigo_lampada = "02.05.00002"

        if codigo_lampada in custos_db:
            produto_lampada = custos_db[codigo_lampada]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_lampada = produto_lampada.custo_total or Decimal('0')
            valor_lampadas = Decimal(str(qtd_lampadas)) * valor_unitario_lampada

            componentes_sistemas_estruturado["iluminacao"]["itens"][codigo_lampada] = {
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
            componentes_sistemas_estruturado["iluminacao"]["total_subcategoria"] += valor_lampadas
            total_sistemas_categoria += valor_lampadas

        # === VENTILAÇÃO ===

        # Ventilação (só para elevador de passageiro)
        if 'Passageiro' in pedido.modelo_elevador:
            qtd_ventiladores = 1
            codigo_ventilador = "02.05.00005"

            if codigo_ventilador in custos_db:
                produto_ventilador = custos_db[codigo_ventilador]
                # CORREÇÃO: Usar SOMENTE custo_total
                valor_unitario_ventilador = produto_ventilador.custo_total or Decimal('0')
                valor_ventiladores = Decimal(str(qtd_ventiladores)) * valor_unitario_ventilador

                componentes_sistemas_estruturado["ventilacao"]["itens"][codigo_ventilador] = {
                    'codigo': codigo_ventilador,
                    'descricao': produto_ventilador.nome,
                    'categoria': produto_ventilador.grupo.nome if produto_ventilador.grupo else 'ELETRICO',
                    'subcategoria': produto_ventilador.subgrupo.nome if produto_ventilador.subgrupo else 'Ventilação',
                    'quantidade': qtd_ventiladores,
                    'unidade': produto_ventilador.unidade_medida,
                    'valor_unitario': float(valor_unitario_ventilador),
                    'valor_total': float(valor_ventiladores),
                    'explicacao': "Ventilador para elevador de passageiro"
                }
                componentes_sistemas_estruturado["ventilacao"]["total_subcategoria"] += valor_ventiladores
                total_sistemas_categoria += valor_ventiladores

        # Converte os totais de subcategorias para float antes de retornar para JSONField
        for sub_cat in componentes_sistemas_estruturado.values():
            sub_cat['total_subcategoria'] = float(sub_cat['total_subcategoria'])

        return {
            'componentes': componentes_sistemas_estruturado,
            'total': total_sistemas_categoria
        }