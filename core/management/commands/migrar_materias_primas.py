# core/management/commands/migrar_materias_primas.py

import os
import json
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model

from core.models import (
    Produto, GrupoProduto, SubgrupoProduto, Fornecedor
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Migra matérias-primas da planilha Componentes Custos.xlsx'

    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            default='matprima.xlsx',
            help='Nome do arquivo da planilha (deve estar na raiz do projeto)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar no banco (apenas mostra o que seria feito)'
        )

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 MODO DRY-RUN - Nenhum dado será salvo no banco')
            )
        
        self.stdout.write('🚀 Iniciando migração de matérias-primas...')
        
        try:
            with transaction.atomic():
                # Ler dados da planilha
                dados_planilha = self._ler_planilha(arquivo)
                
                # Criar estruturas base
                grupo, subgrupo, fornecedor, usuario = self._criar_estruturas_base()
                
                # Migrar produtos
                produtos_criados = self._migrar_produtos(
                    dados_planilha, grupo, subgrupo, fornecedor, usuario, dry_run
                )
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ DRY-RUN concluído! {len(produtos_criados)} produtos seriam criados.'
                        )
                    )
                    # Rollback forçado no dry-run
                    raise CommandError("Rollback do dry-run")
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Migração concluída! {len(produtos_criados)} produtos criados.'
                        )
                    )
                    
        except CommandError as e:
            if "Rollback do dry-run" not in str(e):
                raise e
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro na migração: {str(e)}')
            )
            raise

    def _ler_planilha(self, arquivo):
        """Lê os dados da planilha Excel"""
        try:
            import openpyxl
        except ImportError:
            raise CommandError(
                "Instale openpyxl: pip install openpyxl"
            )
        
        if not os.path.exists(arquivo):
            raise CommandError(f"Arquivo não encontrado: {arquivo}")
        
        self.stdout.write(f'📖 Lendo planilha: {arquivo}')
        
        workbook = openpyxl.load_workbook(arquivo, data_only=True)  # data_only=True para resolver fórmulas
        worksheet = workbook.active
        
        dados = []
        erros_linha = []
        
        for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), 2):
            if not row or not row[0]:  # Skip se linha vazia ou sem código
                continue
            
            try:
                codigo_num, codigo_antigo, descricao, unidade, valor = row[:5]  # Garantir máximo 5 colunas
                
                # Tratar código numérico - pode ser fórmula ou número
                if isinstance(codigo_num, str) and codigo_num.startswith('='):
                    # Se é fórmula, pular esta linha
                    erros_linha.append(f"Linha {row_num}: Fórmula encontrada no código: {codigo_num}")
                    continue
                
                # Converter para inteiro de forma segura
                try:
                    codigo_numerico = int(float(codigo_num)) if codigo_num else 0
                except (ValueError, TypeError):
                    erros_linha.append(f"Linha {row_num}: Código inválido: {codigo_num}")
                    continue
                
                if codigo_numerico <= 0:
                    erros_linha.append(f"Linha {row_num}: Código deve ser maior que zero: {codigo_numerico}")
                    continue
                
                # Gerar código MP baseado no número da planilha
                codigo_mp = f"MP{codigo_numerico:04d}"  # MP0001, MP0002, etc.
                
                # Verificar se descrição existe
                if not descricao or str(descricao).strip() == '':
                    erros_linha.append(f"Linha {row_num}: Descrição vazia")
                    continue
                
                # Mapear unidades conforme padrão
                unidade_mapeada = self._mapear_unidade(unidade)
                
                # Garantir que valor seja decimal
                try:
                    valor_decimal = Decimal(str(valor)) if valor else Decimal('0.00')
                except (ValueError, TypeError):
                    valor_decimal = Decimal('0.00')
                    erros_linha.append(f"Linha {row_num}: Valor inválido convertido para 0.00: {valor}")
                
                dados.append({
                    'codigo_mp': codigo_mp,
                    'codigo_antigo': str(codigo_antigo).strip() if codigo_antigo else '',
                    'descricao': str(descricao).strip(),
                    'unidade_original': unidade,
                    'unidade_mapeada': unidade_mapeada,
                    'valor': valor_decimal,
                    'linha_planilha': row_num
                })
                
            except Exception as e:
                erros_linha.append(f"Linha {row_num}: Erro inesperado: {str(e)}")
                continue
        
        # Mostrar erros encontrados
        if erros_linha:
            self.stdout.write(self.style.WARNING('⚠️  Linhas com problemas encontradas:'))
            for erro in erros_linha:
                self.stdout.write(f'   • {erro}')
            self.stdout.write('')
        
        self.stdout.write(f'📊 {len(dados)} produtos válidos encontrados na planilha')
        return dados

    def _mapear_unidade(self, unidade_original):
        """Mapeia unidades da planilha para o padrão do sistema"""
        mapeamento = {
            'qtd': 'UN',    # Unidade
            'm2': 'M2',     # Metro Quadrado  
            'm': 'MT',      # Metro
            'mm2': 'M2',    # Metro Quadrado (mm² vira M²)
        }
        
        unidade_lower = str(unidade_original).lower().strip()
        return mapeamento.get(unidade_lower, 'UN')  # Default: Unidade

    def _criar_estruturas_base(self):
        """Cria ou recupera grupo, subgrupo, fornecedor e usuário"""
        
        # Buscar usuário admin
        usuario = User.objects.filter(is_superuser=True).first()
        if not usuario:
            usuario = User.objects.first()
        if not usuario:
            raise CommandError("Nenhum usuário encontrado no sistema")
        
        self.stdout.write(f'👤 Usando usuário: {usuario.username}')
        
        # Criar/buscar grupo G1
        grupo, created = GrupoProduto.objects.get_or_create(
            codigo='G1',
            defaults={
                'nome': 'Matérias Primas',
                'descricao': 'Grupo de matérias primas migradas da planilha',
                'criado_por': usuario
            }
        )
        status = "criado" if created else "encontrado"
        self.stdout.write(f'📁 Grupo G1 {status}: {grupo.nome}')
        
        # Criar/buscar subgrupo SG1
        subgrupo, created = SubgrupoProduto.objects.get_or_create(
            grupo=grupo,
            codigo='SG1',
            defaults={
                'nome': 'Componentes Gerais',
                'descricao': 'Subgrupo de componentes gerais',
                'criado_por': usuario
            }
        )
        status = "criado" if created else "encontrado"
        self.stdout.write(f'📂 Subgrupo SG1 {status}: {subgrupo.nome}')
        
        # Criar/buscar fornecedor padrão
        fornecedor, created = Fornecedor.objects.get_or_create(
            razao_social='Fornecedor Padrão',
            defaults={
                'nome_fantasia': 'Padrão',
                'criado_por': usuario
            }
        )
        status = "criado" if created else "encontrado"
        self.stdout.write(f'🏪 Fornecedor {status}: {fornecedor.razao_social}')
        
        return grupo, subgrupo, fornecedor, usuario

    def _migrar_produtos(self, dados, grupo, subgrupo, fornecedor, usuario, dry_run):
        """Migra os produtos da planilha"""
        produtos_criados = []
        produtos_com_erro = []
        
        self.stdout.write('🔄 Iniciando migração dos produtos...')
        
        for item in dados:
            try:
                # Usar código MP já definido na planilha
                codigo_mp = item['codigo_mp']
                
                # Verificar se já existe
                if Produto.objects.filter(codigo=codigo_mp).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Produto {codigo_mp} já existe - pulando"
                        )
                    )
                    continue
                
                if not dry_run:
                    # Criar produto real
                    produto = Produto.objects.create(
                        codigo=codigo_mp,  # MP0101, MP0102, MP0103...
                        nome=item['descricao'],
                        descricao=f"Migrado da planilha - Código original: {item['codigo_antigo']} - Linha {item['linha_planilha']}",
                        tipo='MP',  # Matéria Prima
                        grupo=grupo,
                        subgrupo=subgrupo,
                        unidade_medida=item['unidade_mapeada'],
                        custo_medio=item['valor'],
                        preco_venda=item['valor'] * Decimal('1.3'),  # Margem 30%
                        fornecedor_principal=fornecedor,
                        status='ATIVO',
                        disponivel=True,
                        criado_por=usuario,
                        atualizado_por=usuario
                    )
                    produtos_criados.append(produto)
                    
                    self.stdout.write(
                        f'✅ {item["codigo_antigo"]} → {codigo_mp} - {item["descricao"]}'
                    )
                else:
                    # Apenas simular no dry-run
                    produtos_criados.append({
                        'codigo_antigo': item['codigo_antigo'],
                        'codigo_mp': codigo_mp,
                        'nome': item['descricao'],
                        'unidade': item['unidade_mapeada'],
                        'custo': item['valor']
                    })
                    
                    self.stdout.write(
                        f'🧪 {item["codigo_antigo"]} → {codigo_mp} - {item["descricao"]}'
                    )
                
                if len(produtos_criados) % 10 == 0:
                    self.stdout.write(f'📦 {len(produtos_criados)} produtos processados...')
                    
            except Exception as e:
                erro_msg = f"Erro no produto {item['codigo_antigo']} → {item['codigo_mp']}: {str(e)}"
                produtos_com_erro.append(erro_msg)
                self.stdout.write(self.style.ERROR(f"❌ {erro_msg}"))
        
        # Relatório final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'📊 RELATÓRIO DA MIGRAÇÃO:')
        self.stdout.write(f'✅ Produtos processados: {len(produtos_criados)}')
        self.stdout.write(f'❌ Produtos com erro: {len(produtos_com_erro)}')
        
        if produtos_com_erro:
            self.stdout.write('\n🚨 ERROS ENCONTRADOS:')
            for erro in produtos_com_erro:
                self.stdout.write(f'   • {erro}')
        
        # Mostrar próxima numeração
        if not dry_run and produtos_criados:
            self.stdout.write(f'\n🔢 Próximo produto MP disponível: MP{len(produtos_criados) + 176:04d}')
        elif dry_run and produtos_criados:
            self.stdout.write(f'\n🔢 Próximo produto MP seria: MP{len(produtos_criados) + 176:04d}')
        
        return produtos_criados