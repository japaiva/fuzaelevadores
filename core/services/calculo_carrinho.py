# core/services/calculos/calculo_carrinho.py - VERSÃO REFATORADA PARA ESTRUTURA HIERÁRQUICA

import logging
import math
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
    Serviço para cálculo completo do carrinho (chassi + plataforma + barra roscada)
    CORRIGIDO seguindo calculations.py original
    REFATORADO para retornar estrutura hierárquica de componentes.
    """
    
    @staticmethod
    def calcular_custo_carrinho(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos do carrinho - VERSÃO REFATORADA ESTRUTURADA"""
        
        # Estrutura para armazenar os componentes detalhados por subcategoria
        componentes_carrinho_estruturado = {
            "chassi": {"total_subcategoria": Decimal('0'), "itens": {}},
            "plataforma": {"total_subcategoria": Decimal('0'), "itens": {}},
            "barra_roscada": {"total_subcategoria": Decimal('0'), "itens": {}}
        }
        total_carrinho_categoria = Decimal('0')
        
        # Extrair valores com conversão segura para Decimal
        capacidade = safe_decimal(dimensionamento.get('cab', {}).get('capacidade', 0))
        largura_cabine = safe_decimal(dimensionamento.get('cab', {}).get('largura', 0))
        altura_cabine = safe_decimal(dimensionamento.get('cab', {}).get('altura', 0))
        comprimento_cabine = safe_decimal(dimensionamento.get('cab', {}).get('compr', 0))
        
        # === CHASSI ===
        
        # Travessas do chassi
        if capacidade <= 1000:
            codigo_travessa = "01.03.00001"  # PE01 → 01.03.00001
        elif capacidade <= 1800:
            codigo_travessa = "01.03.00002"  # PE02 → 01.03.00002
        else:
            codigo_travessa = "01.03.00003"  # PE03 → 01.03.00003
        
        qtd_travessas = 4
        if capacidade > 2000:
            qtd_travessas += 4
        
        if codigo_travessa in custos_db:
            produto_travessa = custos_db[codigo_travessa]
            valor_unitario_travessa = safe_decimal(produto_travessa.custo_medio or produto_travessa.preco_venda or 125)
            
            comprimento_travessa = largura_cabine + Decimal('0.17')
            quantidade_total_travessas = safe_decimal(qtd_travessas) * comprimento_travessa
            valor_travessas = quantidade_total_travessas * valor_unitario_travessa
            
            componentes_carrinho_estruturado["chassi"]["itens"][codigo_travessa] = {
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
            componentes_carrinho_estruturado["chassi"]["total_subcategoria"] += valor_travessas
            total_carrinho_categoria += valor_travessas
        
        # Longarinas do chassi
        if capacidade <= 1500:
            codigo_longarina = "01.03.00005"  # PE04 → 01.03.00005
        elif capacidade <= 2000:
            codigo_longarina = "01.03.00006"  # PE05 → 01.03.00006
        else:
            codigo_longarina = "01.03.00007"  # PE06 → 01.03.00007
        
        qtd_longarinas = 2
        
        if codigo_longarina in custos_db:
            produto_longarina = custos_db[codigo_longarina]
            valor_unitario_longarina = safe_decimal(produto_longarina.custo_medio or produto_longarina.preco_venda or 150)
            
            comprimento_longarina = altura_cabine + Decimal('0.70')
            quantidade_total_longarinas = safe_decimal(qtd_longarinas) * comprimento_longarina
            valor_longarinas = quantidade_total_longarinas * valor_unitario_longarina
            
            componentes_carrinho_estruturado["chassi"]["itens"][codigo_longarina] = {
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
            componentes_carrinho_estruturado["chassi"]["total_subcategoria"] += valor_longarinas
            total_carrinho_categoria += valor_longarinas
        
        # Parafusos para chassi
        codigo_parafuso_chassi = "01.04.00008"  # FE02 → 01.04.00008
        if codigo_parafuso_chassi in custos_db:
            produto_parafuso = custos_db[codigo_parafuso_chassi]
            valor_unitario_parafuso = safe_decimal(produto_parafuso.custo_medio or produto_parafuso.preco_venda or 3)
            qtd_parafusos_chassi = 65
            valor_parafusos_chassi = safe_decimal(qtd_parafusos_chassi) * valor_unitario_parafuso
            
            componentes_carrinho_estruturado["chassi"]["itens"][f"{codigo_parafuso_chassi}_chassi"] = {
                'codigo': codigo_parafuso_chassi,
                'descricao': produto_parafuso.nome,
                'categoria': produto_parafuso.grupo.nome if produto_parafuso.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso.subgrupo.nome if produto_parafuso.subgrupo else 'Chassi',
                'quantidade': qtd_parafusos_chassi,
                'unidade': produto_parafuso.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso),
                'valor_total': float(valor_parafusos_chassi),
                'explicacao': f"Parafusos chassi: {qtd_parafusos_chassi} unidades fixas"
            }
            componentes_carrinho_estruturado["chassi"]["total_subcategoria"] += valor_parafusos_chassi
            total_carrinho_categoria += valor_parafusos_chassi
        
        # === PLATAFORMA ===
        
        # Perfis externos da plataforma (2 de cada direção)
        if capacidade <= 1000:
            codigo_perfil_externo = "01.03.00008"  # PE07 → 01.03.00008
        elif capacidade <= 1800:
            codigo_perfil_externo = "01.03.00009"  # PE08 → 01.03.00009
        else:
            codigo_perfil_externo = "01.03.00010"  # PE09 → 01.03.00010
        
        if codigo_perfil_externo in custos_db:
            produto_perfil_externo = custos_db[codigo_perfil_externo]
            valor_unitario_perfil_externo = safe_decimal(produto_perfil_externo.custo_medio or produto_perfil_externo.preco_venda or 80)
            
            # 2 perfis na largura + 2 perfis no comprimento
            qtd_perfis_largura = Decimal('2') * largura_cabine
            qtd_perfis_comprimento = Decimal('2') * comprimento_cabine
            quantidade_total_externos = qtd_perfis_largura + qtd_perfis_comprimento
            valor_perfis_externos = quantidade_total_externos * valor_unitario_perfil_externo
            
            componentes_carrinho_estruturado["plataforma"]["itens"][codigo_perfil_externo] = {
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
            componentes_carrinho_estruturado["plataforma"]["total_subcategoria"] += valor_perfis_externos
            total_carrinho_categoria += valor_perfis_externos
        
        # Perfis internos da plataforma
        if capacidade <= 1000:
            codigo_perfil_interno = "01.03.00011"  # PE10 → 01.03.00011
        elif capacidade <= 1800:
            codigo_perfil_interno = "01.03.00012"  # PE11 → 01.03.00012
        else:
            codigo_perfil_interno = "01.03.00013"  # PE12 → 01.03.00013
        
        if codigo_perfil_interno in custos_db:
            produto_perfil_interno = custos_db[codigo_perfil_interno]
            valor_unitario_perfil_interno = safe_decimal(produto_perfil_interno.custo_medio or produto_perfil_interno.preco_venda or 70)
            
            qtd_perfis_internos = round(float(largura_cabine / Decimal('0.35')))  # 35cm = 0.35m
            quantidade_total_internos = safe_decimal(qtd_perfis_internos) * comprimento_cabine
            valor_perfis_internos = quantidade_total_internos * valor_unitario_perfil_interno
            
            componentes_carrinho_estruturado["plataforma"]["itens"][codigo_perfil_interno] = {
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
            componentes_carrinho_estruturado["plataforma"]["total_subcategoria"] += valor_perfis_internos
            total_carrinho_categoria += valor_perfis_internos
        
        # Parafusos para plataforma (reutiliza o mesmo código 01.04.00008 do chassi)
        if codigo_parafuso_chassi in custos_db:
            # O produto_parafuso e valor_unitario_parafuso já foram definidos no cálculo do chassi
            qtd_parafusos_plataforma = 24 + (4 * qtd_perfis_internos)
            valor_parafusos_plataforma = safe_decimal(qtd_parafusos_plataforma) * valor_unitario_parafuso
            
            componentes_carrinho_estruturado["plataforma"]["itens"][f"{codigo_parafuso_chassi}_plataforma"] = {
                'codigo': codigo_parafuso_chassi,
                'descricao': produto_parafuso.nome,
                'categoria': produto_parafuso.grupo.nome if produto_parafuso.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso.subgrupo.nome if produto_parafuso.subgrupo else 'Plataforma',
                'quantidade': qtd_parafusos_plataforma,
                'unidade': produto_parafuso.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso),
                'valor_total': float(valor_parafusos_plataforma),
                'explicacao': f"Parafusos plataforma: 24 + (4 x {qtd_perfis_internos}) = {qtd_parafusos_plataforma}"
            }
            componentes_carrinho_estruturado["plataforma"]["total_subcategoria"] += valor_parafusos_plataforma
            total_carrinho_categoria += valor_parafusos_plataforma
        
        # === BARRA ROSCADA ===
        
        # Barras roscadas
        codigo_barra_roscada = "01.03.00004"  # PE25 → 01.03.00004
        if codigo_barra_roscada in custos_db:
            produto_barra = custos_db[codigo_barra_roscada]
            valor_unitario_barra = safe_decimal(produto_barra.custo_medio or produto_barra.preco_venda or 120)
            
            comprimento_barra_unitario = (comprimento_cabine / Decimal('2')) / Decimal('0.60')
            qtd_barras_necessarias = 4
            comprimento_total_barras = comprimento_barra_unitario * safe_decimal(qtd_barras_necessarias)
            qtd_barras_compradas = math.ceil(float(comprimento_total_barras / Decimal('3')))  # Arredonda para cima
            valor_barras = safe_decimal(qtd_barras_compradas) * valor_unitario_barra
            
            componentes_carrinho_estruturado["barra_roscada"]["itens"][codigo_barra_roscada] = {
                'codigo': codigo_barra_roscada,
                'descricao': produto_barra.nome,
                'categoria': produto_barra.grupo.nome if produto_barra.grupo else 'ESTRUTURA',
                'subcategoria': produto_barra.subgrupo.nome if produto_barra.subgrupo else 'Barra Roscada',
                'quantidade': qtd_barras_compradas,
                'unidade': produto_barra.unidade_medida,
                'valor_unitario': float(valor_unitario_barra),
                'valor_total': float(valor_barras),
                'explicacao': f"Barras roscadas: {float(comprimento_total_barras):.2f}m total = {qtd_barras_compradas} barras de 3m"
            }
            componentes_carrinho_estruturado["barra_roscada"]["total_subcategoria"] += valor_barras
            total_carrinho_categoria += valor_barras
        
        # Parafusos para barras roscadas (FE01)
        codigo_parafuso_barra_fe01 = "01.04.00009"  # FE01 → 01.04.00009
        if codigo_parafuso_barra_fe01 in custos_db:
            produto_parafuso_barra = custos_db[codigo_parafuso_barra_fe01]
            valor_unitario_parafuso_barra = safe_decimal(produto_parafuso_barra.custo_medio or produto_parafuso_barra.preco_venda or 2)
            qtd_parafusos_barra_fe01 = 16  # 4 parafusos por barra x 4 barras
            valor_parafusos_barra_fe01 = safe_decimal(qtd_parafusos_barra_fe01) * valor_unitario_parafuso_barra
            
            componentes_carrinho_estruturado["barra_roscada"]["itens"][f"{codigo_parafuso_barra_fe01}_barra"] = {
                'codigo': codigo_parafuso_barra_fe01,
                'descricao': produto_parafuso_barra.nome,
                'categoria': produto_parafuso_barra.grupo.nome if produto_parafuso_barra.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso_barra.subgrupo.nome if produto_parafuso_barra.subgrupo else 'Barra Roscada',
                'quantidade': qtd_parafusos_barra_fe01,
                'unidade': produto_parafuso_barra.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso_barra),
                'valor_total': float(valor_parafusos_barra_fe01),
                'explicacao': f"Parafusos barras roscadas (FE01): {qtd_parafusos_barra_fe01} unidades"
            }
            componentes_carrinho_estruturado["barra_roscada"]["total_subcategoria"] += valor_parafusos_barra_fe01
            total_carrinho_categoria += valor_parafusos_barra_fe01
        
        # Parafusos para barras roscadas (FE02)
        codigo_parafuso_barra_fe02 = "01.04.00008"  # FE02 → 01.04.00008
        if codigo_parafuso_barra_fe02 in custos_db:
            produto_parafuso_barra_fe02 = custos_db[codigo_parafuso_barra_fe02]
            valor_unitario_parafuso_barra_fe02 = safe_decimal(produto_parafuso_barra_fe02.custo_medio or produto_parafuso_barra_fe02.preco_venda or 3)
            qtd_parafusos_barra_fe02 = 16  # 4 parafusos por barra x 4 barras
            valor_parafusos_barra_fe02 = safe_decimal(qtd_parafusos_barra_fe02) * valor_unitario_parafuso_barra_fe02
            
            componentes_carrinho_estruturado["barra_roscada"]["itens"][f"{codigo_parafuso_barra_fe02}_barra"] = {
                'codigo': codigo_parafuso_barra_fe02,
                'descricao': produto_parafuso_barra_fe02.nome,
                'categoria': produto_parafuso_barra_fe02.grupo.nome if produto_parafuso_barra_fe02.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso_barra_fe02.subgrupo.nome if produto_parafuso_barra_fe02.subgrupo else 'Barra Roscada',
                'quantidade': qtd_parafusos_barra_fe02,
                'unidade': produto_parafuso_barra_fe02.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso_barra_fe02),
                'valor_total': float(valor_parafusos_barra_fe02),
                'explicacao': f"Parafusos barras roscadas (FE02): {qtd_parafusos_barra_fe02} unidades"
            }
            componentes_carrinho_estruturado["barra_roscada"]["total_subcategoria"] += valor_parafusos_barra_fe02
            total_carrinho_categoria += valor_parafusos_barra_fe02
        
        # Suportes para barras roscadas (PE26)
        codigo_suporte_barra_pe26 = "01.03.00016"  # PE26 → 01.03.00016
        if codigo_suporte_barra_pe26 in custos_db:
            produto_suporte_pe26 = custos_db[codigo_suporte_barra_pe26]
            valor_unitario_suporte_pe26 = safe_decimal(produto_suporte_pe26.custo_medio or produto_suporte_pe26.preco_venda or 25)
            qtd_suportes_pe26 = 4  # 1 suporte por barra
            valor_suportes_pe26 = safe_decimal(qtd_suportes_pe26) * valor_unitario_suporte_pe26
            
            componentes_carrinho_estruturado["barra_roscada"]["itens"][codigo_suporte_barra_pe26] = {
                'codigo': codigo_suporte_barra_pe26,
                'descricao': produto_suporte_pe26.nome,
                'categoria': produto_suporte_pe26.grupo.nome if produto_suporte_pe26.grupo else 'ESTRUTURA',
                'subcategoria': produto_suporte_pe26.subgrupo.nome if produto_suporte_pe26.subgrupo else 'Barra Roscada',
                'quantidade': qtd_suportes_pe26,
                'unidade': produto_suporte_pe26.unidade_medida,
                'valor_unitario': float(valor_unitario_suporte_pe26),
                'valor_total': float(valor_suportes_pe26),
                'explicacao': f"Suportes barra roscada (PE26): {qtd_suportes_pe26} unidades"
            }
            componentes_carrinho_estruturado["barra_roscada"]["total_subcategoria"] += valor_suportes_pe26
            total_carrinho_categoria += valor_suportes_pe26
        
        # Suportes para barras roscadas (PE27)
        codigo_suporte_barra_pe27 = "01.03.00017"  # PE27 → 01.03.00017
        if codigo_suporte_barra_pe27 in custos_db:
            produto_suporte_pe27 = custos_db[codigo_suporte_barra_pe27]
            valor_unitario_suporte_pe27 = safe_decimal(produto_suporte_pe27.custo_medio or produto_suporte_pe27.preco_venda or 30)
            qtd_suportes_pe27 = 4  # 1 suporte por barra
            valor_suportes_pe27 = safe_decimal(qtd_suportes_pe27) * valor_unitario_suporte_pe27
            
            componentes_carrinho_estruturado["barra_roscada"]["itens"][codigo_suporte_barra_pe27] = {
                'codigo': codigo_suporte_barra_pe27,
                'descricao': produto_suporte_pe27.nome,
                'categoria': produto_suporte_pe27.grupo.nome if produto_suporte_pe27.grupo else 'ESTRUTURA',
                'subcategoria': produto_suporte_pe27.subgrupo.nome if produto_suporte_pe27.subgrupo else 'Barra Roscada',
                'quantidade': qtd_suportes_pe27,
                'unidade': produto_suporte_pe27.unidade_medida,
                'valor_unitario': float(valor_unitario_suporte_pe27),
                'valor_total': float(valor_suportes_pe27),
                'explicacao': f"Suportes barra roscada (PE27): {qtd_suportes_pe27} unidades"
            }
            componentes_carrinho_estruturado["barra_roscada"]["total_subcategoria"] += valor_suportes_pe27
            total_carrinho_categoria += valor_suportes_pe27
        
        # Converte os totais de subcategorias para float antes de retornar para JSONField
        for sub_cat in componentes_carrinho_estruturado.values():
            sub_cat['total_subcategoria'] = float(sub_cat['total_subcategoria'])
            
        return {
            'componentes': componentes_carrinho_estruturado, # Retorna a estrutura aninhada
            'total': total_carrinho_categoria # Total da categoria principal (Carrinho)
        }