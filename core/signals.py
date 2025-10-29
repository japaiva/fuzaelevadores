# core/signals.py

"""
Signals para gerenciamento automático de permissões
Sistema de Elevadores FUZA
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from core.models import Usuario


# Mapeamento de níveis para grupos
NIVEL_TO_GROUP = {
    'admin': 'Admin',
    'gestor': 'Gestor',
    'vendedor': 'Vendedor',
    'financeiro': 'Financeiro',
    'vistoria': 'Vistoria',
    'producao': 'Produção',
    'compras': 'Compras',
    'engenharia': 'Engenharia',
    'almoxarifado': 'Almoxarifado',
}


@receiver(post_save, sender=Usuario)
def adicionar_usuario_ao_grupo(sender, instance, created, **kwargs):
    """
    Signal que adiciona automaticamente o usuário ao grupo correspondente
    ao seu nível quando é criado ou atualizado

    Executa quando:
    - Usuário é criado (created=True)
    - Usuário tem o nível alterado

    Lógica:
    1. Remove usuário de TODOS os grupos baseados em nível
    2. Adiciona ao grupo correspondente ao nível atual
    """

    # Só processar se o usuário tem nível definido
    if not instance.nivel:
        return

    # Obter o nome do grupo baseado no nível
    grupo_nome = NIVEL_TO_GROUP.get(instance.nivel)

    if not grupo_nome:
        print(f"⚠️ Nível '{instance.nivel}' não mapeado para nenhum grupo")
        return

    try:
        # Obter ou criar o grupo
        grupo, grupo_criado = Group.objects.get_or_create(name=grupo_nome)

        if grupo_criado:
            print(f"✓ Grupo '{grupo_nome}' criado automaticamente")

        # Remover usuário de todos os grupos de nível
        # (para evitar conflito se o nível foi alterado)
        grupos_nivel = Group.objects.filter(name__in=NIVEL_TO_GROUP.values())
        instance.groups.remove(*grupos_nivel)

        # Adicionar ao grupo correto
        instance.groups.add(grupo)

        if created:
            print(f"✓ Usuário '{instance.username}' adicionado ao grupo '{grupo_nome}'")
        else:
            print(f"✓ Usuário '{instance.username}' movido para grupo '{grupo_nome}'")

    except Exception as e:
        print(f"❌ Erro ao adicionar usuário ao grupo: {e}")


@receiver(post_save, sender=Usuario)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Signal para criar PerfilUsuario automaticamente quando um usuário é criado
    """
    if created:
        from core.models import PerfilUsuario

        try:
            PerfilUsuario.objects.get_or_create(
                usuario=instance,
                defaults={
                    'nivel': instance.nivel if instance.nivel else 'vendedor',
                    'telefone': instance.telefone if instance.telefone else '',
                }
            )
            print(f"✓ Perfil criado para usuário '{instance.username}'")
        except Exception as e:
            print(f"❌ Erro ao criar perfil: {e}")
