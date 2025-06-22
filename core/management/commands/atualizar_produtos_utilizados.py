# management/commands/atualizar_produtos_utilizados.py

"""
Script para marcar produtos como utilizados baseado nos códigos realmente usados nos cálculos
Ignora comentários e pega apenas os códigos efetivamente utilizados no sistema
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Produto
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Atualiza campo utilizado dos produtos baseado nos códigos usados nos cálculos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações (apenas mostra o que seria feito)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reseta todos os produtos para não utilizados antes de aplicar',
        )

    def handle(self, *args, **options):
        """Executa a atualização dos produtos utilizados"""
        
        # =====================================================================
        # CÓDIGOS REALMENTE UTILIZADOS NOS CÁLCULOS (SEM COMENTÁRIOS)
        # =====================================================================
        
        codigos_utilizados = {
            # === CABINE ===
            # Chapas corpo - Material
            "01.01.00013",  # Inox 304 1,2mm
            "01.01.00014",  # Inox 304 1,5mm  
            "01.01.00016",  # Inox 430 1,2mm
            "01.01.00017",  # Inox 430 1,5mm
            "01.01.00018",  # Chapa Pintada 1,2mm
            "01.01.00019",  # Chapa Pintada 1,5mm
            "01.01.00003",  # Alumínio 1,2mm
            "01.01.00004",  # Alumínio 1,5mm
            
            # Chapas piso
            "01.01.00005",  # Antiderrapante
            "01.01.00008",  # Padrão piso
            
            # Corte/dobra
            "05.02.00002",  # Corte/dobra inox
            "05.02.00001",  # Corte/dobra alumínio
            
            # Parafusos cabine
            "01.04.00009",  # Parafusos chapas
            "01.04.00013",  # Parafusos piso
            
            # === CARRINHO ===
            # Travessas chassi
            "05.01.00010",  # <= 1000kg
            "05.01.00011",  # <= 1800kg
            "05.01.00012",  # > 1800kg
            
            # Longarinas chassi
            "05.01.00001",  # <= 1500kg
            "05.01.00002",  # <= 2000kg
            "05.01.00003",  # > 2000kg
            
            # Perfis externos plataforma
            "05.01.00004",  # <= 1000kg
            "05.01.00005",  # <= 1800kg
            "05.01.00006",  # > 1800kg
            
            # Perfis internos plataforma
            "05.01.00007",  # <= 1000kg
            "05.01.00008",  # <= 1800kg
            "05.01.00009",  # > 1800kg
            
            # Parafusos carrinho
            "01.04.00008",  # Parafusos chassi/plataforma
            
            # Barras roscadas e suportes
            "01.03.00004",  # Barra roscada
            "03.04.00016",  # Suporte PE26
            "03.04.00017",  # Suporte PE27
            
            # === TRAÇÃO ===
            # Acionamento
            "05.03.00002",  # Sistema hidráulico
            "06.01.00004",  # Motor elétrico
            
            # Polias e travessa
            "03.03.00006",  # Polias
            "03.03.00004",  # Travessa polia
            
            # Cabo de aço
            "03.04.00003",  # Cabo aço 5/16
            
            # Contrapesos
            "03.06.00001",  # Contrapeso pequeno/médio
            "03.06.00002",  # Contrapeso grande
            
            # Pedras contrapeso
            "03.06.00006",  # Pedra pequena
            "03.06.00005",  # Pedra grande
            
            # Guias elevador
            "03.01.00005",  # Guias elevador
            "03.02.00010",  # Suportes guia elevador (CORRIGIDO - era 03.02.0010)
            
            # Guias contrapeso
            "03.01.00004",  # Guias contrapeso
            "03.02.00011",  # Suportes guia contrapeso
            
            # Parafusos tração
            "01.02.00007",  # Parafusos gerais tração
            
            # === SISTEMAS COMPLEMENTARES ===
            # Iluminação
            "02.05.00002",  # Lâmpadas LED
            
            # Ventilação
            "02.05.00005",  # Ventilador
        }
        
        self.stdout.write(f"Total de códigos utilizados encontrados: {len(codigos_utilizados)}")
        
        try:
            with transaction.atomic():
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING("=== MODO DRY-RUN (sem alterações) ==="))
                
                # Reset se solicitado
                if options['reset']:
                    if options['dry_run']:
                        count_reset = Produto.objects.filter(utilizado=True).count()
                        self.stdout.write(f"[DRY-RUN] Resetaria {count_reset} produtos para não utilizados")
                    else:
                        count_reset = Produto.objects.filter(utilizado=True).update(utilizado=False)
                        self.stdout.write(f"✅ Reset: {count_reset} produtos marcados como não utilizados")
                
                # Contadores
                produtos_encontrados = 0
                produtos_atualizados = 0
                produtos_nao_encontrados = []
                
                # Processar cada código utilizado
                for codigo in sorted(codigos_utilizados):
                    try:
                        produto = Produto.objects.get(codigo=codigo)
                        produtos_encontrados += 1
                        
                        if not produto.utilizado:
                            if options['dry_run']:
                                self.stdout.write(f"[DRY-RUN] Marcaria como utilizado: {codigo} - {produto.nome}")
                            else:
                                produto.utilizado = True
                                produto.save(update_fields=['utilizado'])
                                self.stdout.write(f"✅ Marcado como utilizado: {codigo} - {produto.nome}")
                            produtos_atualizados += 1
                        else:
                            self.stdout.write(f"ℹ️  Já utilizado: {codigo} - {produto.nome}")
                    
                    except Produto.DoesNotExist:
                        produtos_nao_encontrados.append(codigo)
                        self.stdout.write(
                            self.style.ERROR(f"❌ Produto não encontrado: {codigo}")
                        )
                
                # Relatório final
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS("RELATÓRIO FINAL"))
                self.stdout.write("="*70)
                self.stdout.write(f"📊 Códigos processados: {len(codigos_utilizados)}")
                self.stdout.write(f"✅ Produtos encontrados: {produtos_encontrados}")
                self.stdout.write(f"🔄 Produtos atualizados: {produtos_atualizados}")
                self.stdout.write(f"❌ Produtos não encontrados: {len(produtos_nao_encontrados)}")
                
                if produtos_nao_encontrados:
                    self.stdout.write("\n📋 CÓDIGOS NÃO ENCONTRADOS:")
                    for codigo in sorted(produtos_nao_encontrados):
                        self.stdout.write(f"   - {codigo}")
                    self.stdout.write("\n⚠️  Verifique se estes produtos existem no cadastro!")
                
                # Estatísticas finais
                if not options['dry_run']:
                    total_utilizados = Produto.objects.filter(utilizado=True).count()
                    total_produtos = Produto.objects.count()
                    percentual = (total_utilizados / total_produtos * 100) if total_produtos > 0 else 0
                    
                    self.stdout.write(f"\n📈 ESTATÍSTICAS GERAIS:")
                    self.stdout.write(f"   Total produtos cadastrados: {total_produtos}")
                    self.stdout.write(f"   Produtos utilizados: {total_utilizados}")
                    self.stdout.write(f"   Percentual utilizado: {percentual:.1f}%")
                
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING("\n🔍 Execute sem --dry-run para aplicar as alterações"))
                else:
                    self.stdout.write(self.style.SUCCESS("\n✅ Atualização concluída com sucesso!"))
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro durante execução: {str(e)}")
            )
            raise