# OPÇÃO 1: MANAGEMENT COMMAND (RECOMENDADO)
# Crie o arquivo: core/management/commands/migrar_codigos_produtos.py

import os
import django
from django.core.management.base import BaseCommand
from django.db import transaction
import re

class Command(BaseCommand):
    help = 'Migra códigos de produtos de 4 para 5 dígitos (GG.SS.NNNN → GG.SS.NNNNN)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar alterações (apenas mostra o que seria feito)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra detalhes de cada produto alterado',
        )
    
    def handle(self, *args, **options):
        from core.models import Produto
        
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando migração de códigos de produtos...\n')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  MODO DRY-RUN: Nenhuma alteração será salva!\n')
            )
        
        # Buscar todos os produtos com códigos no formato antigo
        produtos = Produto.objects.all()
        produtos_alterados = 0
        produtos_ja_corretos = 0
        produtos_sem_codigo = 0
        produtos_com_erro = 0
        
        with transaction.atomic():
            for produto in produtos:
                if not produto.codigo:
                    produtos_sem_codigo += 1
                    if verbose:
                        self.stdout.write(f"❌ Produto {produto.id}: sem código")
                    continue
                
                # Regex para encontrar padrão GG.SS.NNNN (4 dígitos)
                match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', produto.codigo)
                
                if match:
                    # Código no formato antigo - precisa migrar
                    grupo_codigo = match.group(1)
                    subgrupo_codigo = match.group(2)
                    numero = int(match.group(3))
                    
                    # Converter para 5 dígitos
                    novo_codigo = f"{grupo_codigo}.{subgrupo_codigo}.{numero:05d}"
                    
                    if verbose:
                        self.stdout.write(
                            f"🔄 Produto {produto.id}: {produto.codigo} → {novo_codigo}"
                        )
                    
                    if not dry_run:
                        produto.codigo = novo_codigo
                        produto.save(update_fields=['codigo'])
                    
                    produtos_alterados += 1
                    
                elif re.match(r'^(\d{2})\.(\d{2})\.(\d{5})$', produto.codigo):
                    # Código já no formato correto (5 dígitos)
                    produtos_ja_corretos += 1
                    if verbose:
                        self.stdout.write(
                            f"✅ Produto {produto.id}: {produto.codigo} (já correto)"
                        )
                else:
                    # Código em formato não reconhecido
                    produtos_com_erro += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"⚠️  Produto {produto.id}: código '{produto.codigo}' em formato não reconhecido"
                        )
                    )
            
            if dry_run:
                # Em dry-run, sempre fazer rollback
                transaction.set_rollback(True)
        
        # Relatório final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RELATÓRIO DA MIGRAÇÃO:'))
        self.stdout.write(f"✅ Produtos alterados: {produtos_alterados}")
        self.stdout.write(f"✅ Produtos já corretos: {produtos_ja_corretos}")
        self.stdout.write(f"⚠️  Produtos sem código: {produtos_sem_codigo}")
        self.stdout.write(f"❌ Produtos com erro: {produtos_com_erro}")
        self.stdout.write(f"📈 Total processado: {produtos.count()}")
        
        if dry_run:
            self.stdout.write('\n' + self.style.WARNING(
                '⚠️  Nenhuma alteração foi salva (modo dry-run).\n'
                'Para aplicar as alterações, execute sem --dry-run'
            ))
        else:
            self.stdout.write('\n' + self.style.SUCCESS(
                '🎉 Migração concluída com sucesso!'
            ))


# =============================================================================
# OPÇÃO 2: SCRIPT DJANGO STANDALONE
# Crie o arquivo: scripts/migrar_codigos.py
# =============================================================================

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuza_elevadores.settings')
django.setup()

from django.db import transaction
from core.models import Produto
import re

def migrar_codigos_produtos(dry_run=True, verbose=False):
    """
    Migra códigos de produtos de 4 para 5 dígitos
    
    Args:
        dry_run (bool): Se True, não salva as alterações
        verbose (bool): Se True, mostra detalhes de cada alteração
    """
    print("🚀 Iniciando migração de códigos de produtos...")
    
    if dry_run:
        print("⚠️  MODO DRY-RUN: Nenhuma alteração será salva!")
    
    produtos = Produto.objects.all()
    produtos_alterados = 0
    produtos_ja_corretos = 0
    produtos_sem_codigo = 0
    produtos_com_erro = 0
    
    try:
        with transaction.atomic():
            for produto in produtos:
                if not produto.codigo:
                    produtos_sem_codigo += 1
                    if verbose:
                        print(f"❌ Produto {produto.id}: sem código")
                    continue
                
                # Regex para encontrar padrão GG.SS.NNNN (4 dígitos)
                match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', produto.codigo)
                
                if match:
                    # Código no formato antigo - precisa migrar
                    grupo_codigo = match.group(1)
                    subgrupo_codigo = match.group(2)
                    numero = int(match.group(3))
                    
                    # Converter para 5 dígitos
                    novo_codigo = f"{grupo_codigo}.{subgrupo_codigo}.{numero:05d}"
                    
                    if verbose:
                        print(f"🔄 Produto {produto.id}: {produto.codigo} → {novo_codigo}")
                    
                    if not dry_run:
                        produto.codigo = novo_codigo
                        produto.save(update_fields=['codigo'])
                    
                    produtos_alterados += 1
                    
                elif re.match(r'^(\d{2})\.(\d{2})\.(\d{5})$', produto.codigo):
                    # Código já no formato correto (5 dígitos)
                    produtos_ja_corretos += 1
                    if verbose:
                        print(f"✅ Produto {produto.id}: {produto.codigo} (já correto)")
                else:
                    # Código em formato não reconhecido
                    produtos_com_erro += 1
                    print(f"⚠️  Produto {produto.id}: código '{produto.codigo}' em formato não reconhecido")
            
            if dry_run:
                # Em dry-run, sempre fazer rollback
                transaction.set_rollback(True)
    
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False
    
    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO DA MIGRAÇÃO:")
    print(f"✅ Produtos alterados: {produtos_alterados}")
    print(f"✅ Produtos já corretos: {produtos_ja_corretos}")
    print(f"⚠️  Produtos sem código: {produtos_sem_codigo}")
    print(f"❌ Produtos com erro: {produtos_com_erro}")
    print(f"📈 Total processado: {produtos.count()}")
    
    if dry_run:
        print("\n⚠️  Nenhuma alteração foi salva (modo dry-run).")
        print("Para aplicar as alterações, execute com dry_run=False")
    else:
        print("\n🎉 Migração concluída com sucesso!")
    
    return True

if __name__ == "__main__":
    # Executar script
    migrar_codigos_produtos(dry_run=True, verbose=True)

# =============================================================================
# OPÇÃO 3: FUNÇÃO SIMPLES PARA USAR NO SHELL DO DJANGO
# =============================================================================

def migrar_codigos_shell():
    """
    Função simples para executar no shell do Django:
    python manage.py shell
    >>> exec(open('scripts/migrar_codigos_shell.py').read())
    """
    from core.models import Produto
    from django.db import transaction
    import re
    
    with transaction.atomic():
        produtos = Produto.objects.all()
        alterados = 0
        
        for produto in produtos:
            if produto.codigo:
                # Buscar padrão GG.SS.NNNN
                match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', produto.codigo)
                if match:
                    grupo, subgrupo, numero = match.groups()
                    novo_codigo = f"{grupo}.{subgrupo}.{int(numero):05d}"
                    produto.codigo = novo_codigo
                    produto.save(update_fields=['codigo'])
                    print(f"Alterado: {match.group(0)} → {novo_codigo}")
                    alterados += 1
        
        print(f"\n✅ {alterados} produtos alterados!")


# =============================================================================
# INSTRUÇÕES DE USO:
# =============================================================================

"""
MÉTODO 1 - Management Command (RECOMENDADO):

1. Crie a pasta: core/management/commands/
2. Crie o arquivo: core/management/commands/migrar_codigos_produtos.py
3. Cole o código da OPÇÃO 1
4. Execute:

# Testar primeiro (não salva alterações):
python manage.py migrar_codigos_produtos --dry-run --verbose

# Aplicar as alterações:
python manage.py migrar_codigos_produtos --verbose

MÉTODO 2 - Script Standalone:

1. Crie a pasta: scripts/
2. Crie o arquivo: scripts/migrar_codigos.py  
3. Cole o código da OPÇÃO 2
4. Execute: python scripts/migrar_codigos.py

MÉTODO 3 - Shell do Django:

python manage.py shell
>>> from core.models import Produto
>>> # Cole aqui a função migrar_codigos_shell() da OPÇÃO 3
>>> migrar_codigos_shell()
"""