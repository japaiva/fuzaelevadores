# core/signals_saldo.py

"""
Signals para controle automático de saldo de requisições vinculadas a pedidos
Sistema de Elevadores FUZA
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import models
from core.models import ItemPedidoCompra, PedidoCompra


@receiver(post_save, sender=ItemPedidoCompra)
def atualizar_saldo_requisicao_ao_salvar_item(sender, instance, created, **kwargs):
    """
    Atualiza o saldo da requisição quando um item de pedido é criado ou atualizado
    """
    if not instance.item_requisicao:
        return

    # Recalcula para todos os status (inclusive RASCUNHO)
    # O método recalcular_quantidades já filtra os status corretos
    instance.item_requisicao.recalcular_quantidades()


@receiver(post_delete, sender=ItemPedidoCompra)
def atualizar_saldo_requisicao_ao_deletar_item(sender, instance, **kwargs):
    """
    Atualiza o saldo da requisição quando um item de pedido é deletado
    """
    if not instance.item_requisicao:
        return

    instance.item_requisicao.recalcular_quantidades()


@receiver(post_save, sender=PedidoCompra)
def atualizar_saldo_requisicao_ao_alterar_status_pedido(sender, instance, created, **kwargs):
    """
    Recalcula saldo de todas as requisições quando o status do pedido muda
    Exemplo: cancelar um pedido devolve o saldo para as requisições
    """
    if not created:  # Só processar em updates, não em criação
        # Recalcular saldo de todos os itens de requisição vinculados
        itens_requisicao_ids = instance.itens.filter(
            item_requisicao__isnull=False
        ).values_list('item_requisicao_id', flat=True).distinct()

        from core.models import ItemRequisicaoCompra
        for item_req_id in itens_requisicao_ids:
            try:
                item_req = ItemRequisicaoCompra.objects.get(id=item_req_id)
                item_req.recalcular_quantidades()
            except ItemRequisicaoCompra.DoesNotExist:
                pass


# Signal para atualizar quantidade_recebida do item de requisição
@receiver(post_save, sender=ItemPedidoCompra)
def atualizar_quantidade_recebida_requisicao(sender, instance, **kwargs):
    """
    Quando quantidade_recebida é atualizada no item do pedido,
    propaga para o item da requisição
    """
    if not instance.item_requisicao:
        return

    # Somar todas as quantidades recebidas de todos os pedidos vinculados a este item de requisição
    total_recebido = instance.item_requisicao.itens_pedido.filter(
        pedido__status__in=['ENVIADO', 'CONFIRMADO', 'PARCIAL', 'RECEBIDO']
    ).aggregate(
        total=models.Sum('quantidade_recebida')
    )['total'] or 0

    instance.item_requisicao.quantidade_recebida = total_recebido
    instance.item_requisicao.save(update_fields=['quantidade_recebida'])


# Validação para evitar pedidos com quantidade maior que o saldo
@receiver(pre_save, sender=ItemPedidoCompra)
def validar_quantidade_contra_saldo(sender, instance, **kwargs):
    """
    Valida se a quantidade do pedido não excede o saldo disponível da requisição
    """
    if not instance.item_requisicao:
        return

    # Se está criando ou alterando a quantidade
    if instance.pk:  # Está editando
        try:
            old_instance = ItemPedidoCompra.objects.get(pk=instance.pk)
            if old_instance.quantidade == instance.quantidade:
                # Quantidade não mudou, não precisa validar
                return
        except ItemPedidoCompra.DoesNotExist:
            pass

    # Calcular saldo disponível
    saldo_disponivel = instance.item_requisicao.quantidade_saldo

    # Se está editando, adicionar a quantidade anterior ao saldo
    if instance.pk:
        try:
            old_instance = ItemPedidoCompra.objects.get(pk=instance.pk)
            # Só conta se o pedido estava em status que "reserva" saldo (não CANCELADO)
            if old_instance.pedido.status in ['RASCUNHO', 'ENVIADO', 'CONFIRMADO', 'PARCIAL', 'RECEBIDO']:
                saldo_disponivel += old_instance.quantidade
        except ItemPedidoCompra.DoesNotExist:
            pass

    # Validar se a nova quantidade não excede o saldo
    # NOTA: Esta validação está como warning, não como erro hard
    # Você pode descomentar a exceção se quiser bloquear
    if instance.quantidade > saldo_disponivel:
        print(f"⚠️ AVISO: Quantidade do pedido ({instance.quantidade}) excede saldo disponível ({saldo_disponivel}) "
              f"para o item {instance.item_requisicao.produto.codigo} da requisição {instance.item_requisicao.requisicao.numero}")
        # from django.core.exceptions import ValidationError
        # raise ValidationError(
        #     f"Quantidade do pedido ({instance.quantidade}) excede saldo disponível ({saldo_disponivel}) "
        #     f"da requisição {instance.item_requisicao.requisicao.numero}"
        # )
