# core/management/commands/setup_permissoes.py

"""
Comando para criar grupos de usuários com permissões padrão
Uso: python manage.py setup_permissoes
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Proposta, ListaMateriais, RequisicaoCompra, OrcamentoCompra


class Command(BaseCommand):
    help = 'Cria grupos de usuários com permissões padrão do sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando setup de permissões...'))

        # Limpar grupos existentes (opcional - comentar se não quiser)
        # Group.objects.all().delete()

        # ====================================
        # GRUPO: ADMIN
        # ====================================
        grupo_admin, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Admin criado'))

        # Admin tem TODAS as permissões
        all_permissions = Permission.objects.all()
        grupo_admin.permissions.set(all_permissions)
        self.stdout.write(self.style.SUCCESS(f'  → {all_permissions.count()} permissões atribuídas ao Admin'))


        # ====================================
        # GRUPO: GESTOR
        # ====================================
        grupo_gestor, created = Group.objects.get_or_create(name='Gestor')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Gestor criado'))

        permissoes_gestor = [
            # Propostas - gestor pode tudo
            'add_proposta', 'change_proposta', 'delete_proposta', 'view_proposta',
            'aprovar_desconto_15', 'aprovar_desconto_20',
            'visualizar_custos', 'visualizar_todas_propostas', 'exportar_relatorios',
            'editar_proposta_alheia', 'aprovar_proposta', 'rejeitar_proposta',
            'aprovar_medicao',

            # Produção
            'view_listamateriais', 'change_listamateriais', 'aprovar_lista_materiais',
            'visualizar_custos_lista', 'editar_lista_materiais_aprovada',

            'view_requisicaocompra', 'change_requisicaocompra',
            'aprovar_requisicao', 'cancelar_requisicao', 'editar_requisicao_aprovada',

            'view_orcamentocompra', 'change_orcamentocompra',
            'aprovar_orcamento_ilimitado', 'cancelar_orcamento', 'editar_orcamento_aprovado',

            # Outras entidades
            'view_cliente', 'add_cliente', 'change_cliente',
            'view_produto', 'add_produto', 'change_produto',
        ]
        self._adicionar_permissoes(grupo_gestor, permissoes_gestor)


        # ====================================
        # GRUPO: VENDEDOR
        # ====================================
        grupo_vendedor, created = Group.objects.get_or_create(name='Vendedor')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Vendedor criado'))

        permissoes_vendedor = [
            # Propostas - pode criar, editar as próprias, visualizar
            'add_proposta', 'change_proposta', 'view_proposta', 'delete_proposta',
            'aprovar_desconto_5',  # Até 5% de desconto
            'exportar_relatorios',
            'agendar_vistoria',

            # Clientes
            'view_cliente', 'add_cliente', 'change_cliente',

            # Produtos (apenas visualização)
            'view_produto',
        ]
        self._adicionar_permissoes(grupo_vendedor, permissoes_vendedor)


        # ====================================
        # GRUPO: FINANCEIRO
        # ====================================
        grupo_financeiro, created = Group.objects.get_or_create(name='Financeiro')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Financeiro criado'))

        permissoes_financeiro = [
            # Propostas - visualização completa com custos
            'view_proposta', 'visualizar_custos', 'visualizar_todas_propostas',
            'exportar_relatorios',

            # Orçamentos - aprovação financeira
            'view_orcamentocompra', 'aprovar_orcamento_ate_50000',

            # Clientes
            'view_cliente', 'change_cliente',
        ]
        self._adicionar_permissoes(grupo_financeiro, permissoes_financeiro)


        # ====================================
        # GRUPO: VISTORIA
        # ====================================
        grupo_vistoria, created = Group.objects.get_or_create(name='Vistoria')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Vistoria criado'))

        permissoes_vistoria = [
            # Propostas - vistoria e medição
            'view_proposta', 'change_proposta',
            'realizar_vistoria', 'agendar_vistoria', 'aprovar_medicao',

            # Clientes
            'view_cliente',
        ]
        self._adicionar_permissoes(grupo_vistoria, permissoes_vistoria)


        # ====================================
        # GRUPO: PRODUÇÃO
        # ====================================
        grupo_producao, created = Group.objects.get_or_create(name='Produção')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Produção criado'))

        permissoes_producao = [
            # Propostas - apenas visualização
            'view_proposta',

            # Listas de materiais
            'view_listamateriais', 'add_listamateriais', 'change_listamateriais',
            'aprovar_lista_materiais', 'visualizar_custos_lista',

            # Requisições
            'view_requisicaocompra', 'add_requisicaocompra', 'change_requisicaocompra',
            'aprovar_requisicao',

            # Orçamentos
            'view_orcamentocompra', 'add_orcamentocompra', 'change_orcamentocompra',

            # Produtos
            'view_produto', 'add_produto', 'change_produto',
        ]
        self._adicionar_permissoes(grupo_producao, permissoes_producao)


        # ====================================
        # GRUPO: COMPRAS
        # ====================================
        grupo_compras, created = Group.objects.get_or_create(name='Compras')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Compras criado'))

        permissoes_compras = [
            # Propostas - apenas visualização
            'view_proposta',

            # Listas de materiais - visualização
            'view_listamateriais', 'visualizar_custos_lista',

            # Requisições
            'view_requisicaocompra', 'change_requisicaocompra',

            # Orçamentos - foco principal
            'view_orcamentocompra', 'add_orcamentocompra', 'change_orcamentocompra',
            'aprovar_orcamento_ate_10000', 'cancelar_orcamento',

            # Produtos
            'view_produto', 'change_produto',

            # Fornecedores
            'view_fornecedor', 'add_fornecedor', 'change_fornecedor',
        ]
        self._adicionar_permissoes(grupo_compras, permissoes_compras)


        # ====================================
        # GRUPO: ENGENHARIA
        # ====================================
        grupo_engenharia, created = Group.objects.get_or_create(name='Engenharia')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Engenharia criado'))

        permissoes_engenharia = [
            # Propostas - visualização com custos
            'view_proposta', 'change_proposta',
            'visualizar_custos', 'visualizar_todas_propostas',

            # Listas de materiais
            'view_listamateriais', 'change_listamateriais',
            'aprovar_lista_materiais', 'visualizar_custos_lista',
            'editar_lista_materiais_aprovada',

            # Requisições
            'view_requisicaocompra', 'change_requisicaocompra',

            # Produtos
            'view_produto', 'add_produto', 'change_produto',
        ]
        self._adicionar_permissoes(grupo_engenharia, permissoes_engenharia)


        # ====================================
        # GRUPO: ALMOXARIFADO
        # ====================================
        grupo_almoxarifado, created = Group.objects.get_or_create(name='Almoxarifado')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo Almoxarifado criado'))

        permissoes_almoxarifado = [
            # Propostas - apenas visualização
            'view_proposta',

            # Listas de materiais - visualização
            'view_listamateriais', 'visualizar_custos_lista',

            # Requisições - visualização
            'view_requisicaocompra',

            # Orçamentos - visualização
            'view_orcamentocompra',

            # Produtos - gestão de estoque
            'view_produto', 'change_produto',
        ]
        self._adicionar_permissoes(grupo_almoxarifado, permissoes_almoxarifado)


        # ====================================
        # RESUMO
        # ====================================
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Setup de permissões concluído com sucesso!'))
        self.stdout.write(self.style.SUCCESS('='*60))

        grupos = Group.objects.all()
        for grupo in grupos:
            count = grupo.permissions.count()
            self.stdout.write(f'  • {grupo.name}: {count} permissões')

        self.stdout.write(self.style.WARNING('\nPróximos passos:'))
        self.stdout.write('  1. Adicione usuários aos grupos apropriados')
        self.stdout.write('  2. Customize permissões individuais se necessário')
        self.stdout.write('  3. Execute: python manage.py makemigrations')
        self.stdout.write('  4. Execute: python manage.py migrate')


    def _adicionar_permissoes(self, grupo, codenames):
        """Helper para adicionar permissões ao grupo"""
        permissoes_adicionadas = 0
        permissoes_nao_encontradas = []

        for codename in codenames:
            try:
                perm = Permission.objects.get(codename=codename)
                grupo.permissions.add(perm)
                permissoes_adicionadas += 1
            except Permission.DoesNotExist:
                permissoes_nao_encontradas.append(codename)

        self.stdout.write(
            self.style.SUCCESS(f'  → {permissoes_adicionadas} permissões atribuídas ao grupo {grupo.name}')
        )

        if permissoes_nao_encontradas:
            self.stdout.write(
                self.style.WARNING(f'  ⚠ Permissões não encontradas: {", ".join(permissoes_nao_encontradas[:5])}')
            )
            if len(permissoes_nao_encontradas) > 5:
                self.stdout.write(
                    self.style.WARNING(f'    ... e mais {len(permissoes_nao_encontradas) - 5}')
                )
