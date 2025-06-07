# management/commands/popular_grupos_subgrupos.py - VERSÃO CORRIGIDA

import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, connection
from core.models import GrupoProduto, SubgrupoProduto, Produto

User = get_user_model()

class Command(BaseCommand):
    """
    Comando para importar grupos, subgrupos e produtos dos arquivos Excel
    
    Usage: python manage.py popular_grupos_subgrupos --grupos=grpsgr.xlsx --produtos=produto.xlsx --limpar
    """
    help = 'Importa grupos, subgrupos e produtos a partir de arquivos Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grupos',
            type=str,
            default='grpsgr.xlsx',
            help='Arquivo Excel com grupos e subgrupos'
        )
        parser.add_argument(
            '--produtos',
            type=str,
            default='produto.xlsx',
            help='Arquivo Excel com produtos'
        )
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Limpa todos os dados antes de importar'
        )

    def limpar_dados_completo(self):
        """Limpeza completa e forçada dos dados"""
        self.stdout.write('🗑️ Iniciando limpeza completa dos dados...')
        
        # Contar antes da limpeza
        produtos_antes = Produto.objects.filter(tipo='MP').count()
        subgrupos_antes = SubgrupoProduto.objects.count()
        grupos_antes = GrupoProduto.objects.count()
        
        self.stdout.write(f'   📦 Produtos MP antes: {produtos_antes}')
        self.stdout.write(f'   📂 Subgrupos antes: {subgrupos_antes}')
        self.stdout.write(f'   📁 Grupos antes: {grupos_antes}')
        
        # Limpeza forçada em ordem correta
        with transaction.atomic():
            # 1. Deletar produtos primeiro (para evitar FK constraints)
            produtos_deletados = Produto.objects.filter(tipo='MP').delete()
            self.stdout.write(f'   ❌ Produtos deletados: {produtos_deletados[0] if produtos_deletados[0] else 0}')
            
            # 2. Deletar subgrupos
            subgrupos_deletados = SubgrupoProduto.objects.all().delete()
            self.stdout.write(f'   ❌ Subgrupos deletados: {subgrupos_deletados[0] if subgrupos_deletados[0] else 0}')
            
            # 3. Deletar grupos
            grupos_deletados = GrupoProduto.objects.all().delete()
            self.stdout.write(f'   ❌ Grupos deletados: {grupos_deletados[0] if grupos_deletados[0] else 0}')
        
        # Forçar commit da transação
        connection.commit()
        
        # Verificar se limpeza foi efetiva
        produtos_depois = Produto.objects.filter(tipo='MP').count()
        subgrupos_depois = SubgrupoProduto.objects.count()
        grupos_depois = GrupoProduto.objects.count()
        
        self.stdout.write(f'   📦 Produtos MP restantes: {produtos_depois}')
        self.stdout.write(f'   📂 Subgrupos restantes: {subgrupos_depois}')
        self.stdout.write(f'   📁 Grupos restantes: {grupos_depois}')
        
        if produtos_depois == 0 and subgrupos_depois == 0 and grupos_depois == 0:
            self.stdout.write(self.style.SUCCESS('✅ Limpeza completa bem-sucedida!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Alguns registros podem não ter sido removidos'))
        
        return True

    def handle(self, *args, **options):
        arquivo_grupos = options['grupos']
        arquivo_produtos = options['produtos']
        limpar = options['limpar']

        # Verificar se arquivos existem
        if not os.path.exists(arquivo_grupos):
            self.stdout.write(self.style.ERROR(f'Arquivo {arquivo_grupos} não encontrado!'))
            return

        if not os.path.exists(arquivo_produtos):
            self.stdout.write(self.style.ERROR(f'Arquivo {arquivo_produtos} não encontrado!'))
            return

        # Obter usuário admin
        try:
            usuario_admin = User.objects.filter(is_superuser=True).first()
            if not usuario_admin:
                self.stdout.write(self.style.ERROR('Nenhum usuário administrador encontrado!'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao buscar usuário admin: {e}'))
            return

        try:
            # ==========================================
            # LIMPEZA COMPLETA (SE SOLICITADA)
            # ==========================================
            if limpar:
                self.limpar_dados_completo()

            # ==========================================
            # LER ARQUIVOS EXCEL
            # ==========================================
            self.stdout.write('\n📖 Lendo arquivos Excel...')
            
            # Ler grupos e subgrupos
            df_grupos = pd.read_excel(arquivo_grupos)
            self.stdout.write(f'   📁 {len(df_grupos)} registros de grupos/subgrupos')
            
            # Ler produtos
            df_produtos = pd.read_excel(arquivo_produtos)
            self.stdout.write(f'   📦 {len(df_produtos)} produtos encontrados')

            # Processar com transação
            with transaction.atomic():
                # ==========================================
                # PROCESSAR GRUPOS E SUBGRUPOS
                # ==========================================
                grupos_data = {}
                subgrupos_data = []

                for _, row in df_grupos.iterrows():
                    codigo = str(row['CODIGO']).strip()
                    grupo_nome = str(row['GRUPO']).strip()
                    subgrupo_nome = str(row['SUBGRUPO']).strip()

                    # Extrair códigos
                    partes_codigo = codigo.split('.')
                    grupo_codigo = partes_codigo[0].zfill(2)  # Garantir 2 dígitos: 01, 02, etc.
                    subgrupo_codigo = partes_codigo[1].zfill(2) if len(partes_codigo) > 1 else '01'

                    # Dados únicos do grupo
                    if grupo_codigo not in grupos_data:
                        grupos_data[grupo_codigo] = {
                            'nome': grupo_nome,
                            'tipo_produto': 'MP'
                        }

                    # Dados do subgrupo
                    subgrupos_data.append({
                        'grupo_codigo': grupo_codigo,
                        'codigo': subgrupo_codigo,
                        'nome': subgrupo_nome
                    })

                # ==========================================
                # CRIAR GRUPOS
                # ==========================================
                self.stdout.write('\n📁 Criando grupos...')
                grupos_criados = 0
                grupos_objetos = {}
                
                for codigo, dados in grupos_data.items():
                    grupo, created = GrupoProduto.objects.get_or_create(
                        codigo=codigo,
                        defaults={
                            'nome': dados['nome'],
                            'tipo_produto': 'MP',
                            'descricao': f'Grupo importado: {dados["nome"]}',
                            'ativo': True,
                            'criado_por': usuario_admin
                        }
                    )
                    grupos_objetos[codigo] = grupo
                    
                    if created:
                        grupos_criados += 1
                        self.stdout.write(f'  ✅ {codigo} - {dados["nome"]}')
                    else:
                        self.stdout.write(f'  ➡️ {codigo} - {dados["nome"]} (já existe)')

                # ==========================================
                # CRIAR SUBGRUPOS
                # ==========================================
                self.stdout.write('\n📂 Criando subgrupos...')
                subgrupos_criados = 0
                subgrupos_objetos = {}
                
                # Remover duplicatas
                subgrupos_unicos = {}
                for subgrupo_data in subgrupos_data:
                    chave = f"{subgrupo_data['grupo_codigo']}.{subgrupo_data['codigo']}"
                    if chave not in subgrupos_unicos:
                        subgrupos_unicos[chave] = subgrupo_data
                
                for chave, subgrupo_data in subgrupos_unicos.items():
                    grupo = grupos_objetos[subgrupo_data['grupo_codigo']]
                    
                    subgrupo, created = SubgrupoProduto.objects.get_or_create(
                        grupo=grupo,
                        codigo=subgrupo_data['codigo'],
                        defaults={
                            'nome': subgrupo_data['nome'],
                            'descricao': f'Subgrupo importado: {subgrupo_data["nome"]}',
                            'ultimo_numero': 0,
                            'ativo': True,
                            'criado_por': usuario_admin
                        }
                    )
                    subgrupos_objetos[chave] = subgrupo
                    
                    if created:
                        subgrupos_criados += 1
                        self.stdout.write(f'  ✅ {chave} - {subgrupo_data["nome"]}')
                    else:
                        self.stdout.write(f'  ➡️ {chave} - {subgrupo_data["nome"]} (já existe)')

                # ==========================================
                # IMPORTAR PRODUTOS
                # ==========================================
                self.stdout.write(f'\n📦 Importando {len(df_produtos)} produtos...')
                produtos_criados = 0
                produtos_duplicados = 0
                produtos_erro = 0
                
                for index, row in df_produtos.iterrows():
                    try:
                        # Extrair dados do produto
                        gr_sg = str(row['GR-SG']).strip() if pd.notna(row['GR-SG']) else None
                        nome_produto = str(row['NOME_SUGERIDO']).strip() if pd.notna(row['NOME_SUGERIDO']) else f'Produto {index}'
                        
                        # Normalizar GR-SG para formato 01.01
                        if gr_sg:
                            partes = gr_sg.split('.')
                            if len(partes) == 2:
                                gr_sg_normalizado = f"{partes[0].zfill(2)}.{partes[1].zfill(2)}"
                            else:
                                gr_sg_normalizado = gr_sg
                        else:
                            continue
                        
                        # Descrição
                        descricao_partes = []
                        if 'NOME_ANTERIOR' in df_produtos.columns and pd.notna(row['NOME_ANTERIOR']):
                            descricao_partes.append(f"Nome anterior: {str(row['NOME_ANTERIOR']).strip()}")
                        if 'CODIGO_ANTERIOR' in df_produtos.columns and pd.notna(row['CODIGO_ANTERIOR']):
                            descricao_partes.append(f"Código anterior: {str(row['CODIGO_ANTERIOR']).strip()}")
                        
                        descricao = " | ".join(descricao_partes) if descricao_partes else 'Matéria-prima importada'
                        
                        # Encontrar subgrupo
                        if gr_sg_normalizado in subgrupos_objetos:
                            subgrupo = subgrupos_objetos[gr_sg_normalizado]
                            
                            # SEMPRE criar produto (sem verificar se existe)
                            produto = Produto.objects.create(
                                nome=nome_produto,
                                descricao=descricao,
                                tipo='MP',
                                grupo=subgrupo.grupo,
                                subgrupo=subgrupo,
                                unidade_medida='UN',
                                controla_estoque=True,
                                estoque_minimo=5,
                                estoque_atual=0,
                                status='ATIVO',
                                disponivel=True,
                                criado_por=usuario_admin,
                                atualizado_por=usuario_admin
                            )
                            produtos_criados += 1
                            
                            # Log de progresso
                            if produtos_criados % 50 == 0:
                                self.stdout.write(f'  📦 {produtos_criados} produtos criados...')
                        else:
                            produtos_erro += 1
                            if produtos_erro <= 10:
                                self.stdout.write(
                                    self.style.WARNING(f'⚠️ Subgrupo não encontrado: {gr_sg_normalizado}')
                                )
                    
                    except Exception as e:
                        produtos_erro += 1
                        if produtos_erro <= 5:
                            self.stdout.write(
                                self.style.WARNING(f'⚠️ Erro linha {index}: {e}')
                            )

                # ==========================================
                # ATUALIZAR CONTADORES DOS SUBGRUPOS
                # ==========================================
                self.stdout.write('\n🔢 Atualizando contadores...')
                
                for chave, subgrupo in subgrupos_objetos.items():
                    total_produtos = Produto.objects.filter(subgrupo=subgrupo).count()
                    if total_produtos > 0:
                        subgrupo.ultimo_numero = total_produtos
                        subgrupo.save(update_fields=['ultimo_numero'])
                        self.stdout.write(f'  🔢 {chave}: {total_produtos} produtos')

                # ==========================================
                # RELATÓRIO FINAL
                # ==========================================
                self.stdout.write('\n' + '='*80)
                self.stdout.write(self.style.SUCCESS('🎉 IMPORTAÇÃO CONCLUÍDA!'))
                self.stdout.write('='*80)
                
                self.stdout.write(f'📁 Grupos criados: {grupos_criados}')
                self.stdout.write(f'📂 Subgrupos criados: {subgrupos_criados}')
                self.stdout.write(f'📦 Produtos criados: {produtos_criados}')
                if produtos_erro > 0:
                    self.stdout.write(f'⚠️ Produtos com erro: {produtos_erro}')
                
                # Totais finais
                self.stdout.write(f'\n📊 TOTAIS NO SISTEMA:')
                self.stdout.write(f'   📁 Grupos: {GrupoProduto.objects.count()}')
                self.stdout.write(f'   📂 Subgrupos: {SubgrupoProduto.objects.count()}')
                self.stdout.write(f'   📦 Matérias-primas: {Produto.objects.filter(tipo="MP").count()}')

                # Exemplo de próximo código
                primeiro_subgrupo = SubgrupoProduto.objects.order_by('grupo__codigo', 'codigo').first()
                if primeiro_subgrupo:
                    proximo_codigo = f"{primeiro_subgrupo.grupo.codigo}.{primeiro_subgrupo.codigo}.{primeiro_subgrupo.ultimo_numero + 1:04d}"
                    self.stdout.write(f'\n💡 Próximo produto será: {proximo_codigo}')

                self.stdout.write('\n' + '='*80)
                self.stdout.write(self.style.SUCCESS('✨ Sistema pronto para uso!'))
                self.stdout.write('='*80)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {e}'))
            import traceback
            traceback.print_exc()
            raise