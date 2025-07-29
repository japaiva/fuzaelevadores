# core/services/calculos/calculo_carrinho.py - VERSÃO CORRIGIDA
# ATUALIZAÇÃO: Usa EXCLUSIVAMENTE a propriedade 'custo_total' do produto.

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
    CORRIGIDO: Acesso correto aos dados e variável qtd_perfis_internos inicializada
    """

    @staticmethod
    def calcular_custo_carrinho(pedido, dimensionamento, custos_db) -> Dict[str, Any]:
        """Calcula custos do carrinho - VERSÃO FINAL CORRIGIDA"""

        # Estrutura para armazenar os componentes detalhados por subcategoria
        componentes_carrinho_estruturado = {
            "chassi": {"total_subcategoria": Decimal('0'), "itens": {}},
            "plataforma": {"total_subcategoria": Decimal('0'), "itens": {}},
            "barra_roscada": {"total_subcategoria": Decimal('0'), "itens": {}}
        }
        total_carrinho_categoria = Decimal('0')

        # ✅ Extrair valores CORRETOS
        cab_dados = dimensionamento.get('cab', {})

        capacidade = safe_decimal(cab_dados.get('capacidade', 0))
        if capacidade == 0:
            capacidade = safe_decimal(getattr(pedido, 'capacidade_cabine_calculada', 0))
        if capacidade == 0:
            capacidade = safe_decimal(pedido.capacidade)

        largura_cabine = safe_decimal(cab_dados.get('largura', 0))
        if largura_cabine == 0:
            largura_cabine = safe_decimal(getattr(pedido, 'largura_cabine_calculada', 0))

        altura_cabine = safe_decimal(cab_dados.get('altura', 0))
        if altura_cabine == 0:
            altura_cabine = safe_decimal(pedido.altura_cabine)

        comprimento_cabine = safe_decimal(cab_dados.get('compr', 0))
        if comprimento_cabine == 0:
            comprimento_cabine = safe_decimal(getattr(pedido, 'comprimento_cabine_calculado', 0))

        # ✅ LOG DE DEBUG DETALHADO
        logger.info(f"=== CÁLCULO CARRINHO - PEDIDO {getattr(pedido, 'numero', 'S/N')} ===")
        logger.info(f"Valores finais - Capacidade: {capacidade}kg, "
                   f"Largura: {largura_cabine}m, Altura: {altura_cabine}m, "
                   f"Comprimento: {comprimento_cabine}m")

        if not capacidade or not largura_cabine or not comprimento_cabine:
            logger.warning(f"CARRINHO: Dados insuficientes para cálculo!")
            return {
                'componentes': componentes_carrinho_estruturado,
                'total': Decimal('0')
            }

        # === CHASSI ===
        logger.info("=== CALCULANDO CHASSI ===")

        if capacidade <= 1000:
            codigo_travessa = "05.01.00010"
        elif capacidade <= 1800:
            codigo_travessa = "05.01.00011"
        else:
            codigo_travessa = "05.01.00012"

        qtd_travessas = 4
        if capacidade > 2000:
            qtd_travessas += 4

        logger.info(f"Travessas: código {codigo_travessa}, quantidade {qtd_travessas}")

        if codigo_travessa in custos_db:
            produto_travessa = custos_db[codigo_travessa]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_travessa = safe_decimal(produto_travessa.custo_total)

            comprimento_travessa = largura_cabine + Decimal('0.17')
            quantidade_total_travessas = safe_decimal(qtd_travessas) * comprimento_travessa
            valor_travessas = quantidade_total_travessas * valor_unitario_travessa

            logger.info(f"  - Valor total travessas: R$ {valor_travessas}")

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
        else:
            logger.error(f"ERRO: Código travessa {codigo_travessa} NÃO encontrado na base!")

        # Longarinas do chassi
        if capacidade <= 1500:
            codigo_longarina = "05.01.00001"
        elif capacidade <= 2000:
            codigo_longarina = "05.01.00002"
        else:
            codigo_longarina = "05.01.00003"

        qtd_longarinas = 2

        if codigo_longarina in custos_db:
            produto_longarina = custos_db[codigo_longarina]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_longarina = safe_decimal(produto_longarina.custo_total)

            altura_poco = safe_decimal(pedido.altura_poco)
            comprimento_longarina = altura_poco + Decimal('0.70')
            quantidade_total_longarinas = safe_decimal(qtd_longarinas) * comprimento_longarina
            valor_longarinas = quantidade_total_longarinas * valor_unitario_longarina

            logger.info(f"  - Valor total longarinas: R$ {valor_longarinas}")

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
        else:
            logger.error(f"ERRO: Código longarina {codigo_longarina} NÃO encontrado na base!")

        # Parafusos para chassi
        codigo_parafuso_chassi = "01.04.00008"
        if codigo_parafuso_chassi in custos_db:
            produto_parafuso = custos_db[codigo_parafuso_chassi]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_parafuso = safe_decimal(produto_parafuso.custo_total)
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
        logger.info("=== CALCULANDO PLATAFORMA ===")

        qtd_perfis_internos = 0

        if capacidade <= 1000:
            codigo_perfil_externo = "05.01.00004"
        elif capacidade <= 1800:
            codigo_perfil_externo = "05.01.00005"
        else:
            codigo_perfil_externo = "05.01.00006"

        if codigo_perfil_externo in custos_db:
            produto_perfil_externo = custos_db[codigo_perfil_externo]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_perfil_externo = safe_decimal(produto_perfil_externo.custo_total)

            qtd_perfis_largura = Decimal('2') * largura_cabine
            qtd_perfis_comprimento = Decimal('2') * comprimento_cabine
            quantidade_total_externos = qtd_perfis_largura + qtd_perfis_comprimento
            valor_perfis_externos = quantidade_total_externos * valor_unitario_perfil_externo

            logger.info(f"  - Perfis externos: {quantidade_total_externos}m, valor: R$ {valor_perfis_externos}")

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
            codigo_perfil_interno = "05.01.00007"
        elif capacidade <= 1800:
            codigo_perfil_interno = "05.01.00008"
        else:
            codigo_perfil_interno = "05.01.00009"

        if codigo_perfil_interno in custos_db:
            produto_perfil_interno = custos_db[codigo_perfil_interno]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_perfil_interno = safe_decimal(produto_perfil_interno.custo_total)

            qtd_perfis_internos = round(float(largura_cabine / Decimal('0.35')))
            quantidade_total_internos = safe_decimal(qtd_perfis_internos) * comprimento_cabine
            valor_perfis_internos = quantidade_total_internos * valor_unitario_perfil_interno

            logger.info(f"  - Perfis internos: {qtd_perfis_internos} x {comprimento_cabine}m = {quantidade_total_internos}m, valor: R$ {valor_perfis_internos}")

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

        # Parafusos para plataforma (reutiliza o mesmo código do chassi)
        if codigo_parafuso_chassi in custos_db:
            qtd_parafusos_plataforma = 24 + (4 * qtd_perfis_internos)
            valor_parafusos_plataforma = safe_decimal(qtd_parafusos_plataforma) * valor_unitario_parafuso

            logger.info(f"  - Parafusos plataforma: 24 + (4 x {qtd_perfis_internos}) = {qtd_parafusos_plataforma}, valor: R$ {valor_parafusos_plataforma}")

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
        logger.info("=== CALCULANDO BARRA ROSCADA ===")

        # Barras roscadas
        codigo_barra_roscada = "01.03.00004"
        if codigo_barra_roscada in custos_db:
            produto_barra = custos_db[codigo_barra_roscada]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_barra = safe_decimal(produto_barra.custo_total)

            altura_poco = safe_decimal(pedido.altura_poco)
            comprimento_barra_unitario = (comprimento_cabine / Decimal('2')) / Decimal('0.60')
            qtd_barras_necessarias = 4
            comprimento_total_barras = comprimento_barra_unitario * safe_decimal(qtd_barras_necessarias)
            qtd_barras_compradas = math.ceil(float(comprimento_total_barras / Decimal('3')))
            valor_barras = safe_decimal(qtd_barras_compradas) * valor_unitario_barra

            logger.info(f"  - Barras roscadas: {qtd_barras_compradas} barras de 3m, valor: R$ {valor_barras}")

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
        codigo_parafuso_barra_fe01 = "01.04.00009"
        if codigo_parafuso_barra_fe01 in custos_db:
            produto_parafuso_barra = custos_db[codigo_parafuso_barra_fe01]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_parafuso_barra_fe01 = safe_decimal(produto_parafuso_barra.custo_total)
            qtd_parafusos_barra_fe01 = 16
            valor_parafusos_barra_fe01 = safe_decimal(qtd_parafusos_barra_fe01) * valor_unitario_parafuso_barra_fe01

            componentes_carrinho_estruturado["barra_roscada"]["itens"][f"{codigo_parafuso_barra_fe01}_barra"] = {
                'codigo': codigo_parafuso_barra_fe01,
                'descricao': produto_parafuso_barra.nome,
                'categoria': produto_parafuso_barra.grupo.nome if produto_parafuso_barra.grupo else 'FIXACAO',
                'subcategoria': produto_parafuso_barra.subgrupo.nome if produto_parafuso_barra.subgrupo else 'Barra Roscada',
                'quantidade': qtd_parafusos_barra_fe01,
                'unidade': produto_parafuso_barra.unidade_medida,
                'valor_unitario': float(valor_unitario_parafuso_barra_fe01),
                'valor_total': float(valor_parafusos_barra_fe01),
                'explicacao': f"Parafusos barras roscadas (FE01): {qtd_parafusos_barra_fe01} unidades"
            }
            componentes_carrinho_estruturado["barra_roscada"]["total_subcategoria"] += valor_parafusos_barra_fe01
            total_carrinho_categoria += valor_parafusos_barra_fe01

        # Parafusos para barras roscadas (FE02)
        codigo_parafuso_barra_fe02 = "01.04.00008"
        if codigo_parafuso_barra_fe02 in custos_db:
            produto_parafuso_barra_fe02 = custos_db[codigo_parafuso_barra_fe02]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_parafuso_barra_fe02 = safe_decimal(produto_parafuso_barra_fe02.custo_total)
            qtd_parafusos_barra_fe02 = 16
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
        codigo_suporte_barra_pe26 = "03.04.00016"
        if codigo_suporte_barra_pe26 in custos_db:
            produto_suporte_pe26 = custos_db[codigo_suporte_barra_pe26]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_suporte_pe26 = safe_decimal(produto_suporte_pe26.custo_total)
            qtd_suportes_pe26 = 4
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
        codigo_suporte_barra_pe27 = "03.04.00017"
        if codigo_suporte_barra_pe27 in custos_db:
            produto_suporte_pe27 = custos_db[codigo_suporte_barra_pe27]
            # CORREÇÃO: Usar SOMENTE custo_total
            valor_unitario_suporte_pe27 = safe_decimal(produto_suporte_pe27.custo_total)
            qtd_suportes_pe27 = 4
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

        for sub_cat in componentes_carrinho_estruturado.values():
            sub_cat['total_subcategoria'] = float(sub_cat['total_subcategoria'])

        logger.info(f"=== RESULTADO FINAL CARRINHO ===")
        logger.info(f"Chassi: R$ {componentes_carrinho_estruturado['chassi']['total_subcategoria']}")
        logger.info(f"Plataforma: R$ {componentes_carrinho_estruturado['plataforma']['total_subcategoria']}")
        logger.info(f"Barra Roscada: R$ {componentes_carrinho_estruturado['barra_roscada']['total_subcategoria']}")
        logger.info(f"TOTAL CARRINHO: R$ {total_carrinho_categoria}")
        logger.info(f"===================================")

        return {
            'componentes': componentes_carrinho_estruturado,
            'total': total_carrinho_categoria
        }