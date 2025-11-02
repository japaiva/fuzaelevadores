# core/signals.py

"""
Signals para gerenciamento automático de permissões
Sistema de Elevadores FUZA
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from core.models import Usuario

logger = logging.getLogger(__name__)


# Mapeamento de níveis para grupos
# Importante: os nomes dos grupos são capitalizados SEM acento
# para evitar problemas de encoding e manter consistência
NIVEL_TO_GROUP = {
    'admin': 'Admin',
    'gestor': 'Gestor',
    'vendedor': 'Vendedor',
    'financeiro': 'Financeiro',
    'vistoria': 'Vistoria',
    'producao': 'Producao',  # SEM acento
    'compras': 'Compras',
    'engenharia': 'Engenharia',
    'almoxarifado': 'Almoxarifado',
}


# DESATIVADO: Sistema simplificado usa apenas níveis, sem grupos
# @receiver(post_save, sender=Usuario)
# def adicionar_usuario_ao_grupo(sender, instance, created, **kwargs):
#     """
#     DESATIVADO - Sistema simplificado não usa grupos
#     Controle de acesso é feito apenas por nível (hardcoded no middleware)
#     """
#     pass


# DESATIVADO: PerfilUsuario é duplicação desnecessária
# @receiver(post_save, sender=Usuario)
# def criar_perfil_usuario(sender, instance, created, **kwargs):
#     """
#     DESATIVADO - PerfilUsuario será removido
#     Todas as informações estão no modelo Usuario
#     """
#     pass


# ====================================
# SIGNALS DE WORKFLOW
# ====================================

@receiver(post_save, sender='core.Proposta')
def criar_tarefa_proposta_aprovada(sender, instance, created, **kwargs):
    """
    Signal que cria uma tarefa para engenharia quando proposta é aprovada

    Workflow:
    1. Vendedor aprova proposta (status = 'aprovado')
    2. Sistema cria tarefa automaticamente para nível Engenharia
    3. Tarefa: "Enviar Projeto Executivo para proposta #XXX"
    4. Usuários com nível 'engenharia' veem a tarefa e podem concluí-la
    """
    from core.models import Tarefa

    # Verificar se a proposta foi aprovada
    if instance.status != 'aprovado':
        return

    # Evitar duplicação: verificar se já existe tarefa para esta proposta
    tarefa_existente = Tarefa.objects.filter(
        proposta=instance,
        tipo='projeto_executivo',
        status__in=['pendente', 'em_andamento']
    ).exists()

    if tarefa_existente:
        logger.debug(f"Tarefa de projeto executivo para proposta {instance.numero} já existe")
        return

    # Criar a tarefa (sistema simplificado: usa nivel_destino)
    try:
        tarefa = Tarefa.objects.create(
            tipo='projeto_executivo',
            titulo=f"Enviar Projeto Executivo - Proposta #{instance.numero}",
            descricao=(
                f"A proposta #{instance.numero} foi aprovada e precisa de projeto executivo.\n\n"
                f"Cliente: {instance.cliente}\n"
                f"Valor: R$ {instance.valor_total:,.2f}\n"
                f"Vendedor: {instance.vendedor if hasattr(instance, 'vendedor') else 'N/A'}\n\n"
                f"Por favor, envie o projeto executivo para o cliente."
            ),
            proposta=instance,
            nivel_destino='engenharia',  # Sistema simplificado: usa nível ao invés de grupo
            prioridade='normal',
            criada_por=instance.atualizado_por,  # Quem aprovou a proposta
        )

        logger.info(
            f"✓ Tarefa #{tarefa.id} criada: Projeto executivo para proposta {instance.numero} "
            f"(destinada ao nível: engenharia)"
        )

    except Exception as e:
        logger.exception(f"Erro ao criar tarefa para proposta {instance.numero}: {e}")
