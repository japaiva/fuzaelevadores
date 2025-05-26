# core/services/calculo_carrinho.py - VERSÃO CORRIGIDA PARA DECIMAL

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger(__name__)


def safe_decimal(value):
    """Converte qualquer valor para Decimal de forma segura"""
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class CalculoCarrinhoService:
    """
    Serviço para cálculo completo do carrinho (chassi + plataforma)
    VERSÃO CORRIGIDA - todas operações usam Decimal
    """
    
    @staticmethod
    def calcular_custo_carrinho(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos do carrinho (chassi + plataforma) - VERSÃO DECIMAL SEGURA"""
        componentes = {}
        total = Decimal('0')
        
        # Extrair valores com conversão segura para Decimal
        capacidade = safe_decimal(dimensionamento.get('cab', {}).get('capacidade', 0))
        largura_cabine = safe_decimal(dimensionamento.get('cab', {}).get('largura', 0))
        altura_cabine = safe_decimal(dimensionamento.get('cab', {}).get('altura', 0))
        comprimento_cabine = safe_decimal(dimensionamento.get('cab', {}).get('compr', 0))
        
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
            produto_travessa = custos_db[codigo_travessa]
            valor_unitario_travessa = safe_decimal(produto_travessa.custo_medio or produto_travessa.preco_venda or 125)
            
            # CORREÇÃO: Todas operações em Decimal
            comprimento_travessa = largura_cabine + Decimal('0.17')
            quantidade_total_travessas = safe_decimal(qtd_travessas) * comprimento_travessa
            valor_travessas = quantidade_total_travessas * valor_unitario_travessa
            
            componentes[codigo_travessa] = {
                'codigo': codigo_travessa,
                'descricao': produto_travessa.nome,
                'categoria': produto_travessa.grupo.nome if produto_travessa.grupo else 'ESTRUTURA',
                'subcategoria': produto_travessa.subgrupo.nome if produto_travessa.subgrupo else 'Chassi',
                'quantidade': float(quantidade_total_travessas),
                'unidade': produto_travessa.unidade_medida,
                'valor_unitario': float(valor_unitario_travessa),
                'valor_total': float(valor_travessas),
                'explicacao': f"Travessas chassi: {qtd_travessas} x {float(comprimento_travessa):.2f}m ({'base 4' + (', +4 se > 2000kg' if capacidade > 2000 else '')})"
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
            produto_longarina = custos_db[codigo_longarina]
            valor_unitario_longarina = safe_decimal(produto_longarina.custo_medio or produto_longarina.preco_venda or 150)
            
            # CORREÇÃO: Todas operações em Decimal
            comprimento_longarina = altura_cabine + Decimal('0.70')
            quantidade_total_longarinas = safe_decimal(qtd_longarinas) * comprimento_longarina
            valor_longarinas = quantidade_total_longarinas * valor_unitario_longarina
            
            componentes[codigo_longarina] = {
                'codigo': codigo_longarina,
                'descricao': produto_longarina.nome,
                'categoria': produto_longarina.grupo.nome if produto_longarina.grupo else 'ESTRUTURA',
                'subcategoria': produto_longarina.subgrupo.nome if produto_longarina.subgrupo else 'Chassi',
                'quantidade': float(quantidade_total_longarinas),
                'unidade': produto_longarina.unidade_medida,
                'valor_unitario': float(valor_unitario_longarina),
                'valor_total': float(valor_longarinas),
                'explicacao': f"Longarinas chassi: {qtd_longarinas} x {float(comprimento_longarina):.2f}m (altura + 0.70m)"
            }
            total += valor_longarinas
        
        # Parafusos para chassi
        codigo_parafuso_chassi = "MP0114"  # FE02 → MP0114
        if codigo_parafuso_chassi in custos_db:
            produto_parafuso = custos_db[codigo_parafuso_chassi]
            valor_unitario_parafuso = safe_decimal(produto_parafuso.custo_medio or produto_parafuso.preco_venda or 3)
            qtd_parafusos_chassi = 65
            valor_parafusos_chassi = safe_decimal(qtd_parafusos_chassi) * valor_unitario_parafuso
            
            componentes[f"{codigo_parafuso_chassi}_chassi"] = {
                'codigo': codigo_parafuso_chassi,
                'descricao': produto_parafuso.nome,
                'categoria': produto_parafuso.grupo.nome if produto_parafuso.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso.subgrupo.nome if produto_parafuso.subgrupo else 'Parafusos',
                'quantidade': qtd_parafusos_chassi,
                'unidade': produto_parafuso.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso),
                'valor_total': float(valor_parafusos_chassi),
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
            produto_perfil_externo = custos_db[codigo_perfil_externo]
            valor_unitario_perfil_externo = safe_decimal(produto_perfil_externo.custo_medio or produto_perfil_externo.preco_venda or 80)
            
            # CORREÇÃO: Todas operações em Decimal
            qtd_perfis_largura = Decimal('2') * largura_cabine
            qtd_perfis_comprimento = Decimal('2') * comprimento_cabine
            quantidade_total_externos = qtd_perfis_largura + qtd_perfis_comprimento
            valor_perfis_externos = quantidade_total_externos * valor_unitario_perfil_externo
            
            componentes[codigo_perfil_externo] = {
                'codigo': codigo_perfil_externo,
                'descricao': produto_perfil_externo.nome,
                'categoria': produto_perfil_externo.grupo.nome if produto_perfil_externo.grupo else 'ESTRUTURA',
                'subcategoria': produto_perfil_externo.subgrupo.nome if produto_perfil_externo.subgrupo else 'Plataforma',
                'quantidade': float(quantidade_total_externos),
                'unidade': produto_perfil_externo.unidade_medida,
                'valor_unitario': float(valor_unitario_perfil_externo),
                'valor_total': float(valor_perfis_externos),
                'explicacao': f"Perfis externos: (2 x {float(largura_cabine):.2f}m) + (2 x {float(comprimento_cabine):.2f}m) = {float(quantidade_total_externos):.2f}m"
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
            produto_perfil_interno = custos_db[codigo_perfil_interno]
            valor_unitario_perfil_interno = safe_decimal(produto_perfil_interno.custo_medio or produto_perfil_interno.preco_venda or 70)
            
            # CORREÇÃO: Cálculo seguro do arredondamento
            qtd_perfis_internos = int((largura_cabine / Decimal('0.35')).to_integral_value())
            quantidade_total_internos = safe_decimal(qtd_perfis_internos) * comprimento_cabine
            valor_perfis_internos = quantidade_total_internos * valor_unitario_perfil_interno
            
            componentes[codigo_perfil_interno] = {
                'codigo': codigo_perfil_interno,
                'descricao': produto_perfil_interno.nome,
                'categoria': produto_perfil_interno.grupo.nome if produto_perfil_interno.grupo else 'ESTRUTURA',
                'subcategoria': produto_perfil_interno.subgrupo.nome if produto_perfil_interno.subgrupo else 'Plataforma',
                'quantidade': float(quantidade_total_internos),
                'unidade': produto_perfil_interno.unidade_medida,
                'valor_unitario': float(valor_unitario_perfil_interno),
                'valor_total': float(valor_perfis_internos),
                'explicacao': f"Perfis internos: {qtd_perfis_internos} x {float(comprimento_cabine):.2f}m (largura/0.35 arredondado)"
            }
            total += valor_perfis_internos
        
        # Parafusos para plataforma
        if codigo_parafuso_chassi in custos_db:  # Reutiliza o mesmo código
            qtd_parafusos_plataforma = 24 + (4 * qtd_perfis_internos)
            valor_parafusos_plataforma = safe_decimal(qtd_parafusos_plataforma) * valor_unitario_parafuso
            
            componentes[f"{codigo_parafuso_chassi}_plataforma"] = {
                'codigo': codigo_parafuso_chassi,
                'descricao': produto_parafuso.nome,
                'categoria': produto_parafuso.grupo.nome if produto_parafuso.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso.subgrupo.nome if produto_parafuso.subgrupo else 'Parafusos',
                'quantidade': qtd_parafusos_plataforma,
                'unidade': produto_parafuso.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso),
                'valor_total': float(valor_parafusos_plataforma),
                'explicacao': f"Parafusos plataforma: 24 + (4 x {qtd_perfis_internos}) = {qtd_parafusos_plataforma}"
            }
            total += valor_parafusos_plataforma
        
        # Barras roscadas
        codigo_barra_roscada = "MP0146"  # PE25 → MP0146
        if codigo_barra_roscada in custos_db:
            produto_barra = custos_db[codigo_barra_roscada]
            valor_unitario_barra = safe_decimal(produto_barra.custo_medio or produto_barra.preco_venda or 120)
            
            # CORREÇÃO: Cálculos seguros
            comprimento_barra_unitario = (comprimento_cabine / Decimal('2')) / Decimal('0.60')
            qtd_barras_necessarias = 4
            comprimento_total_barras = comprimento_barra_unitario * safe_decimal(qtd_barras_necessarias)
            qtd_barras_compradas = int((comprimento_total_barras / Decimal('3')).to_integral_value()) + 1  # Arredonda para cima
            valor_barras = safe_decimal(qtd_barras_compradas) * valor_unitario_barra
            
            componentes[codigo_barra_roscada] = {
                'codigo': codigo_barra_roscada,
                'descricao': produto_barra.nome,
                'categoria': produto_barra.grupo.nome if produto_barra.grupo else 'ESTRUTURA',
                'subcategoria': produto_barra.subgrupo.nome if produto_barra.subgrupo else 'Barras Roscadas',
                'quantidade': qtd_barras_compradas,
                'unidade': produto_barra.unidade_medida,
                'valor_unitario': float(valor_unitario_barra),
                'valor_total': float(valor_barras),
                'explicacao': f"Barras roscadas: {float(comprimento_total_barras):.2f}m total = {qtd_barras_compradas} barras de 3m"
            }
            total += valor_barras
        
        # Parafusos e suportes para barras roscadas
        codigo_parafuso_barra = "MP0113"  # FE01 → MP0113
        if codigo_parafuso_barra in custos_db:
            produto_parafuso_barra = custos_db[codigo_parafuso_barra]
            valor_unitario_parafuso_barra = safe_decimal(produto_parafuso_barra.custo_medio or produto_parafuso_barra.preco_venda or 2)
            qtd_parafusos_barra = 16  # 4 parafusos por barra x 4 barras
            valor_parafusos_barra = safe_decimal(qtd_parafusos_barra) * valor_unitario_parafuso_barra
            
            componentes[f"{codigo_parafuso_barra}_barra"] = {
                'codigo': codigo_parafuso_barra,
                'descricao': produto_parafuso_barra.nome,
                'categoria': produto_parafuso_barra.grupo.nome if produto_parafuso_barra.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso_barra.subgrupo.nome if produto_parafuso_barra.subgrupo else 'Parafusos',
                'quantidade': qtd_parafusos_barra,
                'unidade': produto_parafuso_barra.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso_barra),
                'valor_total': float(valor_parafusos_barra),
                'explicacao': f"Parafusos barras roscadas: {qtd_parafusos_barra} unidades (4 por barra)"
            }
            total += valor_parafusos_barra
        
        # Suportes para barras roscadas
        codigo_suporte_barra = "MP0147"  # PE26 → MP0147
        if codigo_suporte_barra in custos_db:
            produto_suporte_barra = custos_db[codigo_suporte_barra]
            valor_unitario_suporte_barra = safe_decimal(produto_suporte_barra.custo_medio or produto_suporte_barra.preco_venda or 25)
            qtd_suportes = 4  # 1 suporte por barra
            valor_suportes = safe_decimal(qtd_suportes) * valor_unitario_suporte_barra
            
            componentes[codigo_suporte_barra] = {
                'codigo': codigo_suporte_barra,
                'descricao': produto_suporte_barra.nome,
                'categoria': produto_suporte_barra.grupo.nome if produto_suporte_barra.grupo else 'ESTRUTURA',
                'subcategoria': produto_suporte_barra.subgrupo.nome if produto_suporte_barra.subgrupo else 'Suportes',
                'quantidade': qtd_suportes,
                'unidade': produto_suporte_barra.unidade_medida,
                'valor_unitario': float(valor_unitario_suporte_barra),
                'valor_total': float(valor_suportes),
                'explicacao': f"Suportes barra roscada: {qtd_suportes} unidades (1 por barra)"
            }
            total += valor_suportes
        
        return {'componentes': componentes, 'total': total}