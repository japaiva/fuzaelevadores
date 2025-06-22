# management/commands/verificar_codigos_calculos.py

"""
Script para extrair e verificar todos os códigos de produtos usados nos cálculos
Útil para auditoria e manutenção dos códigos
"""

from django.core.management.base import BaseCommand
from core.models import Produto
import re
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica códigos de produtos usados nos arquivos de cálculo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verificar-existencia',
            action='store_true',
            help='Verifica se todos os códigos existem no banco de dados',
        )

    def handle(self, *args, **options):
        """Extrai códigos dos cálculos e verifica se existem"""
        
        # =====================================================================
        # CÓDIGOS EXTRAÍDOS DOS ARQUIVOS DE CÁLCULO (ANÁLISE MANUAL)
        # =====================================================================
        
        # Padrão de códigos: XX.XX.XXXXX (2 dígitos, ponto, 2 dígitos, ponto, 5 dígitos)
        
        codigos_por_modulo = {
            'CABINE': {
                'chapas_corpo': [
                    "01.01.00013",  # _determinar_codigo_chapa - Inox 304 1,2mm
                    "01.01.00014",  # _determinar_codigo_chapa - Inox 304 1,5mm
                    "01.01.00016",  # _determinar_codigo_chapa - Inox 430 1,2mm
                    "01.01.00017",  # _determinar_codigo_chapa - Inox 430 1,5mm
                    "01.01.00018",  # _determinar_codigo_chapa - Chapa Pintada 1,2mm
                    "01.01.00019",  # _determinar_codigo_chapa - Chapa Pintada 1,5mm
                    "01.01.00003",  # _determinar_codigo_chapa - Alumínio 1,2mm
                    "01.01.00004",  # _determinar_codigo_chapa - Alumínio 1,5mm
                ],
                'chapas_piso': [
                    "01.01.00005",  # calcular_custo_cabine - Antiderrapante
                    "01.01.00008",  # calcular_custo_cabine - Padrão piso
                ],
                'servicos': [
                    "05.02.00002",  # calcular_custo_cabine - Corte/dobra inox
                    "05.02.00001",  # calcular_custo_cabine - Corte/dobra alumínio
                ],
                'fixacao': [
                    "01.04.00009",  # calcular_custo_cabine - Parafusos chapas
                    "01.04.00013",  # calcular_custo_cabine - Parafusos piso
                ]
            },
            
            'CARRINHO': {
                'travessas_chassi': [
                    "05.01.00010",  # calcular_custo_carrinho - capacidade <= 1000
                    "05.01.00011",  # calcular_custo_carrinho - capacidade <= 1800
                    "05.01.00012",  # calcular_custo_carrinho - capacidade > 1800
                ],
                'longarinas_chassi': [
                    "05.01.00001",  # calcular_custo_carrinho - capacidade <= 1500
                    "05.01.00002",  # calcular_custo_carrinho - capacidade <= 2000
                    "05.01.00003",  # calcular_custo_carrinho - capacidade > 2000
                ],
                'perfis_externos': [
                    "05.01.00004",  # calcular_custo_carrinho - capacidade <= 1000
                    "05.01.00005",  # calcular_custo_carrinho - capacidade <= 1800
                    "05.01.00006",  # calcular_custo_carrinho - capacidade > 1800
                ],
                'perfis_internos': [
                    "05.01.00007",  # calcular_custo_carrinho - capacidade <= 1000
                    "05.01.00008",  # calcular_custo_carrinho - capacidade <= 1800
                    "05.01.00009",  # calcular_custo_carrinho - capacidade > 1800
                ],
                'fixacao': [
                    "01.04.00008",  # calcular_custo_carrinho - Parafusos chassi/plataforma
                ],
                'barras_roscadas': [
                    "01.03.00004",  # calcular_custo_carrinho - Barra roscada
                    "03.04.00016",  # calcular_custo_carrinho - Suporte PE26
                    "03.04.00017",  # calcular_custo_carrinho - Suporte PE27
                ]
            },
            
            'TRACAO': {
                'acionamento': [
                    "05.03.00002",  # calcular_custo_tracao - Sistema hidráulico
                    "06.01.00004",  # calcular_custo_tracao - Motor elétrico
                ],
                'tracionamento': [
                    "03.03.00006",  # calcular_custo_tracao - Polias
                    "03.03.00004",  # calcular_custo_tracao - Travessa polia
                    "03.04.00003",  # calcular_custo_tracao - Cabo aço 5/16
                ],
                'contrapeso': [
                    "03.06.00001",  # _determinar_tipo_contrapeso - Contrapeso pequeno/médio
                    "03.06.00002",  # _determinar_tipo_contrapeso - Contrapeso grande
                    "03.06.00006",  # _calcular_pedras_contrapeso - Pedra pequena
                    "03.06.00005",  # _calcular_pedras_contrapeso - Pedra grande
                ],
                'guias': [
                    "03.01.00005",  # calcular_custo_tracao - Guias elevador
                    "03.02.00010",  # calcular_custo_tracao - Suportes guia elevador (CORRIGIDO)
                    "03.01.00004",  # calcular_custo_tracao - Guias contrapeso
                    "03.02.00011",  # calcular_custo_tracao - Suportes guia contrapeso
                    "01.02.00007",  # calcular_custo_tracao - Parafusos gerais tração
                ]
            },
            
            'SISTEMAS': {
                'iluminacao': [
                    "02.05.00002",  # calcular_custo_sistemas - Lâmpadas LED
                ],
                'ventilacao': [
                    "02.05.00005",  # calcular_custo_sistemas - Ventilador
                ]
            }
        }
        
        # Flatten all codes
        todos_codigos = set()
        for modulo, categorias in codigos_por_modulo.items():
            for categoria, codigos in categorias.items():
                todos_codigos.update(codigos)
        
        self.stdout.write(f"📊 Total de códigos únicos encontrados: {len(todos_codigos)}")
        
        # Exibir por módulo
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📋 CÓDIGOS POR MÓDULO DE CÁLCULO")
        self.stdout.write("="*70)
        
        for modulo, categorias in codigos_por_modulo.items():
            self.stdout.write(f"\n🔧 {modulo}")
            for categoria, codigos in categorias.items():
                self.stdout.write(f"  📁 {categoria.replace('_', ' ').title()}: {len(codigos)} códigos")
                for codigo in sorted(codigos):
                    self.stdout.write(f"     - {codigo}")
        
        # Verificar existência se solicitado
        if options['verificar_existencia']:
            self.stdout.write("\n" + "="*70)
            self.stdout.write("🔍 VERIFICAÇÃO DE EXISTÊNCIA NO BANCO")
            self.stdout.write("="*70)
            
            encontrados = 0
            nao_encontrados = []
            
            for codigo in sorted(todos_codigos):
                try:
                    produto = Produto.objects.get(codigo=codigo)
                    encontrados += 1
                    status_utilizado = "✅ UTILIZADO" if produto.utilizado else "⚪ NÃO UTILIZADO"
                    self.stdout.write(f"✅ {codigo} - {produto.nome[:50]} - {status_utilizado}")
                except Produto.DoesNotExist:
                    nao_encontrados.append(codigo)
                    self.stdout.write(f"❌ {codigo} - PRODUTO NÃO ENCONTRADO")
            
            # Estatísticas
            self.stdout.write("\n" + "="*70)
            self.stdout.write("📈 ESTATÍSTICAS")
            self.stdout.write("="*70)
            self.stdout.write(f"✅ Produtos encontrados: {encontrados}")
            self.stdout.write(f"❌ Produtos não encontrados: {len(nao_encontrados)}")
            self.stdout.write(f"📊 Taxa de sucesso: {(encontrados/len(todos_codigos)*100):.1f}%")
            
            if nao_encontrados:
                self.stdout.write(f"\n⚠️  CÓDIGOS NÃO ENCONTRADOS:")
                for codigo in sorted(nao_encontrados):
                    self.stdout.write(f"   - {codigo}")
                    
                self.stdout.write(f"\n💡 SUGESTÃO: Cadastre estes produtos antes de executar os cálculos")
            
            # Verificar produtos utilizados vs calculados
            produtos_utilizados = Produto.objects.filter(utilizado=True)
            codigos_utilizados_db = set(produtos_utilizados.values_list('codigo', flat=True))
            
            # Produtos marcados como utilizados mas não estão nos cálculos
            utilizados_nao_calculados = codigos_utilizados_db - todos_codigos
            if utilizados_nao_calculados:
                self.stdout.write(f"\n⚠️  PRODUTOS MARCADOS COMO UTILIZADOS MAS NÃO ESTÃO NOS CÁLCULOS:")
                for codigo in sorted(utilizados_nao_calculados):
                    try:
                        produto = Produto.objects.get(codigo=codigo)
                        self.stdout.write(f"   - {codigo} - {produto.nome}")
                    except Produto.DoesNotExist:
                        self.stdout.write(f"   - {codigo} - PRODUTO DELETADO")
            
        self.stdout.write(f"\n✅ Verificação concluída!")
        
        # Lista final para copy/paste
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📋 LISTA PARA COPY/PASTE (Python set)")
        self.stdout.write("="*70)
        self.stdout.write("codigos_utilizados = {")
        for codigo in sorted(todos_codigos):
            self.stdout.write(f'    "{codigo}",')
        self.stdout.write("}")