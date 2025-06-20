# core/management/commands/atualizar_precos.py

"""
Django Management Command para atualizar preços dos produtos
baseado no arquivo atcalc.xlsx

Uso:
python manage.py atualizar_precos
python manage.py atualizar_precos --arquivo atcalc.xlsx --preview
python manage.py atualizar_precos --campo custo_medio
python manage.py atualizar_precos --campo preco_venda
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
import os
import pandas as pd
from decimal import Decimal
from core.models import Produto

class Command(BaseCommand):
    help = 'Atualiza preços dos produtos baseado no arquivo Excel'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            default='atcalc.xlsx',
            help='Arquivo Excel com os preços (padrão: atcalc.xlsx)'
        )
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Apenas mostra o que seria alterado, sem fazer mudanças'
        )
        parser.add_argument(
            '--campo',
            type=str,
            choices=['custo_medio', 'preco_venda', 'ambos'],
            default='custo_medio',
            help='Campo a ser atualizado (padrão: custo_medio)'
        )
        parser.add_argument(
            '--zero-tambem',
            action='store_true',
            help='Atualizar também produtos com preço 0'
        )
        parser.add_argument(
            '--sobrescrever',
            action='store_true',
            help='Sobrescrever preços existentes (padrão: apenas produtos sem preço)'
        )
    
    def handle(self, *args, **options):
        arquivo_excel = options['arquivo']
        preview = options['preview']
        campo = options['campo']
        zero_tambem = options['zero_tambem']
        sobrescrever = options['sobrescrever']
        
        self.stdout.write("💰 ATUALIZANDO PREÇOS DOS PRODUTOS - SISTEMA FUZA")
        self.stdout.write("=" * 60)
        
        # 1. Carregar mapeamento de preços do Excel
        mapeamento_precos = self.carregar_precos_excel(arquivo_excel, zero_tambem)
        if not mapeamento_precos:
            return
        
        self.stdout.write(f"📋 Produtos com preços encontrados: {len(mapeamento_precos)}")
        
        # 2. Preview ou execução
        if preview:
            self.mostrar_preview(mapeamento_precos, campo, sobrescrever)
        else:
            self.executar_atualizacao(mapeamento_precos, campo, sobrescrever)
    
    def carregar_precos_excel(self, arquivo_excel, incluir_zero=False):
        """Carrega preços do arquivo Excel"""
        try:
            if not os.path.exists(arquivo_excel):
                self.stdout.write(
                    self.style.ERROR(f"❌ Arquivo não encontrado: {arquivo_excel}")
                )
                return None
            
            df = pd.read_excel(arquivo_excel)
            mapeamento_precos = {}
            
            for _, row in df.iterrows():
                if row['STATUS_BUSCA'] == 'ENCONTRADO':
                    codigo_novo = row['CODIGO']
                    codigo_antigo = row['CODIGO_ANTERIOR']
                    custo = row['custo'] if pd.notna(row['custo']) else 0
                    
                    # Filtrar por critério de preço
                    if not incluir_zero and custo <= 0:
                        continue
                    
                    if pd.notna(codigo_novo) and pd.notna(codigo_antigo):
                        mapeamento_precos[codigo_novo] = {
                            'codigo_antigo': codigo_antigo,
                            'preco': Decimal(str(custo)) if custo > 0 else Decimal('0'),
                            'preco_original': custo
                        }
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Preços carregados: {len(mapeamento_precos)} produtos")
            )
            return mapeamento_precos
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro ao carregar preços: {e}")
            )
            return None
    
    def encontrar_produtos_para_atualizar(self, mapeamento_precos, campo, sobrescrever):
        """Encontra produtos que podem ser atualizados"""
        produtos_encontrados = []
        produtos_nao_encontrados = []
        
        for codigo_novo, info_preco in mapeamento_precos.items():
            try:
                produto = Produto.objects.get(codigo=codigo_novo)
                
                # Verificar se deve atualizar baseado nos critérios
                deve_atualizar = False
                valor_atual = None
                
                if campo == 'custo_medio' or campo == 'ambos':
                    valor_atual = produto.custo_medio
                    if sobrescrever or not valor_atual or valor_atual == 0:
                        deve_atualizar = True
                
                if campo == 'preco_venda' or campo == 'ambos':
                    valor_atual = produto.preco_venda
                    if sobrescrever or not valor_atual or valor_atual == 0:
                        deve_atualizar = True
                
                if deve_atualizar:
                    produtos_encontrados.append({
                        'produto': produto,
                        'preco_novo': info_preco['preco'],
                        'preco_original': info_preco['preco_original'],
                        'codigo_antigo': info_preco['codigo_antigo'],
                        'custo_atual': produto.custo_medio,
                        'preco_atual': produto.preco_venda
                    })
                
            except Produto.DoesNotExist:
                produtos_nao_encontrados.append({
                    'codigo': codigo_novo,
                    'codigo_antigo': info_preco['codigo_antigo'],
                    'preco': info_preco['preco_original']
                })
        
        return produtos_encontrados, produtos_nao_encontrados
    
    def mostrar_preview(self, mapeamento_precos, campo, sobrescrever):
        """Mostra preview das alterações"""
        self.stdout.write("\n🔍 PREVIEW DAS ALTERAÇÕES DE PREÇOS")
        self.stdout.write("=" * 50)
        
        produtos_encontrados, produtos_nao_encontrados = self.encontrar_produtos_para_atualizar(
            mapeamento_precos, campo, sobrescrever
        )
        
        if produtos_encontrados:
            self.stdout.write(f"\n📦 PRODUTOS QUE SERÃO ATUALIZADOS ({len(produtos_encontrados)}):")
            self.stdout.write("-" * 60)
            
            for item in produtos_encontrados[:20]:  # Mostrar apenas os primeiros 20
                produto = item['produto']
                preco_novo = item['preco_novo']
                
                info_atual = ""
                if campo == 'custo_medio' or campo == 'ambos':
                    info_atual += f"Custo: {item['custo_atual'] or 'R$ 0,00'} → R$ {preco_novo}"
                if campo == 'preco_venda' or campo == 'ambos':
                    if info_atual:
                        info_atual += " | "
                    info_atual += f"Venda: {item['preco_atual'] or 'R$ 0,00'} → R$ {preco_novo}"
                
                self.stdout.write(
                    f"  {produto.codigo} - {produto.nome[:50]}"
                )
                self.stdout.write(f"    {info_atual}")
                self.stdout.write("")
            
            if len(produtos_encontrados) > 20:
                self.stdout.write(f"  ... e mais {len(produtos_encontrados) - 20} produtos")
        
        if produtos_nao_encontrados:
            self.stdout.write(f"\n❌ PRODUTOS NÃO ENCONTRADOS NO BANCO ({len(produtos_nao_encontrados)}):")
            self.stdout.write("-" * 60)
            
            for item in produtos_nao_encontrados[:10]:
                self.stdout.write(
                    f"  {item['codigo']} (era: {item['codigo_antigo']}) - R$ {item['preco']}"
                )
            
            if len(produtos_nao_encontrados) > 10:
                self.stdout.write(f"  ... e mais {len(produtos_nao_encontrados) - 10} produtos")
        
        # Resumo
        self.stdout.write(f"\n📊 RESUMO DO PREVIEW:")
        self.stdout.write(f"Campo(s) a atualizar: {campo}")
        self.stdout.write(f"Produtos serão atualizados: {len(produtos_encontrados)}")
        self.stdout.write(f"Produtos não encontrados: {len(produtos_nao_encontrados)}")
        self.stdout.write(f"Sobrescrever existentes: {'Sim' if sobrescrever else 'Não'}")
    
    def executar_atualizacao(self, mapeamento_precos, campo, sobrescrever):
        """Executa a atualização dos preços"""
        self.stdout.write("\n💰 EXECUTANDO ATUALIZAÇÃO DE PREÇOS")
        self.stdout.write("=" * 40)
        
        produtos_encontrados, produtos_nao_encontrados = self.encontrar_produtos_para_atualizar(
            mapeamento_precos, campo, sobrescrever
        )
        
        if not produtos_encontrados:
            self.stdout.write(
                self.style.WARNING("ℹ️ Nenhum produto para atualizar encontrado")
            )
            return
        
        # Executar atualizações em transação
        try:
            with transaction.atomic():
                atualizados = 0
                
                for item in produtos_encontrados:
                    produto = item['produto']
                    preco_novo = item['preco_novo']
                    
                    campos_alterados = []
                    
                    # Atualizar campos conforme solicitado
                    if campo == 'custo_medio' or campo == 'ambos':
                        produto.custo_medio = preco_novo
                        campos_alterados.append('custo_medio')
                    
                    if campo == 'preco_venda' or campo == 'ambos':
                        produto.preco_venda = preco_novo
                        campos_alterados.append('preco_venda')
                    
                    # Salvar produto
                    produto.save(update_fields=campos_alterados)
                    atualizados += 1
                    
                    if atualizados <= 10:  # Mostrar detalhes dos primeiros 10
                        self.stdout.write(
                            f"  ✓ {produto.codigo} - {produto.nome[:40]} → R$ {preco_novo}"
                        )
                
                # Resultado final
                self.stdout.write(f"\n📊 RESULTADO DA ATUALIZAÇÃO:")
                self.stdout.write(f"Produtos atualizados: {atualizados}")
                self.stdout.write(f"Campo(s) alterado(s): {campo}")
                
                if produtos_nao_encontrados:
                    self.stdout.write(f"Produtos não encontrados: {len(produtos_nao_encontrados)}")
                
                self.stdout.write(
                    self.style.SUCCESS(f"\n✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro durante a atualização: {e}")
            )
            raise
    
    def mostrar_estatisticas_gerais(self, mapeamento_precos):
        """Mostra estatísticas dos preços carregados"""
        if not mapeamento_precos:
            return
        
        precos = [float(info['preco']) for info in mapeamento_precos.values() if info['preco'] > 0]
        
        if precos:
            self.stdout.write(f"\n📈 ESTATÍSTICAS DOS PREÇOS:")
            self.stdout.write(f"Menor preço: R$ {min(precos):.2f}")
            self.stdout.write(f"Maior preço: R$ {max(precos):.2f}")
            self.stdout.write(f"Preço médio: R$ {sum(precos) / len(precos):.2f}")
            self.stdout.write(f"Total de produtos com preço: {len(precos)}")