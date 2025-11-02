# core/management/commands/migrar_grupo_producao.py

"""
Comando para migrar grupo "Produção" (com acento) para "Producao" (sem acento)
Uso: python manage.py migrar_grupo_producao

Este comando deve ser executado UMA VEZ para corrigir a inconsistência
de nomenclatura nos grupos existentes.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction


class Command(BaseCommand):
    help = 'Migra grupo "Produção" para "Producao" (remove acento para consistência)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando migração de grupo Produção → Producao...'))

        try:
            with transaction.atomic():
                # Tentar encontrar o grupo com acento
                grupo_antigo = Group.objects.filter(name='Produção').first()

                if not grupo_antigo:
                    self.stdout.write(self.style.WARNING('⚠ Grupo "Produção" não encontrado'))
                    self.stdout.write('  Verificando se "Producao" já existe...')

                    grupo_novo = Group.objects.filter(name='Producao').first()
                    if grupo_novo:
                        self.stdout.write(self.style.SUCCESS('✓ Grupo "Producao" já existe'))
                        self.stdout.write('  Nenhuma ação necessária')
                    else:
                        self.stdout.write(self.style.WARNING('  Grupo "Producao" também não existe'))
                        self.stdout.write('  Execute: python manage.py setup_permissoes')
                    return

                # Verificar se já existe grupo "Producao" (sem acento)
                grupo_novo = Group.objects.filter(name='Producao').first()

                if grupo_novo:
                    # Já existe grupo sem acento, mover usuários e permissões
                    self.stdout.write(self.style.WARNING('⚠ Grupo "Producao" já existe'))
                    self.stdout.write('  Movendo usuários e permissões de "Produção" para "Producao"...')

                    # Mover usuários
                    usuarios_movidos = 0
                    for usuario in grupo_antigo.user_set.all():
                        grupo_novo.user_set.add(usuario)
                        usuarios_movidos += 1

                    # Copiar permissões (se houver diferença)
                    permissoes_antigas = set(grupo_antigo.permissions.all())
                    permissoes_novas = set(grupo_novo.permissions.all())
                    permissoes_faltantes = permissoes_antigas - permissoes_novas

                    if permissoes_faltantes:
                        grupo_novo.permissions.add(*permissoes_faltantes)
                        self.stdout.write(f'  → {len(permissoes_faltantes)} permissões copiadas')

                    # Remover grupo antigo
                    grupo_antigo.delete()

                    self.stdout.write(self.style.SUCCESS(f'✓ {usuarios_movidos} usuários movidos'))
                    self.stdout.write(self.style.SUCCESS('✓ Grupo "Produção" removido'))

                else:
                    # Simplesmente renomear o grupo
                    self.stdout.write('  Renomeando grupo "Produção" → "Producao"...')
                    grupo_antigo.name = 'Producao'
                    grupo_antigo.save()

                    usuarios_count = grupo_antigo.user_set.count()
                    permissoes_count = grupo_antigo.permissions.count()

                    self.stdout.write(self.style.SUCCESS('✓ Grupo renomeado com sucesso'))
                    self.stdout.write(f'  → {usuarios_count} usuários mantidos')
                    self.stdout.write(f'  → {permissoes_count} permissões mantidas')

                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('Migração concluída com sucesso!'))
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write('\nPróximos passos:')
                self.stdout.write('  1. Verifique os usuários do grupo: python manage.py shell')
                self.stdout.write('     >>> Group.objects.get(name="Producao").user_set.all()')
                self.stdout.write('  2. Execute setup_permissoes para garantir permissões corretas')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante migração: {e}'))
            raise
