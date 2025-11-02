# core/models/compras.py

"""
Models relacionados a pedidos de compra - ATUALIZADO COM ALTERAÇÕES SOLICITADAS
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

from .base import STATUS_PEDIDO_CHOICES, PRIORIDADE_PEDIDO_CHOICES


class PedidoCompra(models.Model):
    """
    Pedido de compra de matérias-primas e produtos
    ATUALIZADO com campos de data melhorados
    """
    
    # Identificação
    numero = models.CharField(max_length=20, unique=True, verbose_name="Número")

    # Relacionamento com orçamento (opcional)
    orcamento = models.ForeignKey(
        'OrcamentoCompra',
        on_delete=models.PROTECT,
        related_name='pedidos_compra',
        blank=True,
        null=True,
        verbose_name="Orçamento de Origem",
        help_text="Opcional - Orçamento que gerou este pedido"
    )

    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.PROTECT,
        related_name='pedidos_compra'
    )
    
    # === DATAS REORGANIZADAS ===
    data_emissao = models.DateField(
        default=date.today,
        verbose_name="Data de Emissão",
        help_text="Data de emissão do pedido"
    )
    prazo_entrega = models.IntegerField(
        default=7,
        verbose_name="Prazo de Entrega (dias)",
        help_text="Prazo de entrega em dias úteis"
    )
    data_entrega_prevista = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Data Entrega Prevista",
        help_text="Calculada automaticamente com base na data de emissão + prazo"
    )
    data_entrega_real = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Data Entrega Real"
    )
    
    # === CAMPOS DE CONTROLE INTERNO ===
    comprador_responsavel = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Comprador Responsável",
        help_text="Preenchido automaticamente dos parâmetros"
    )
    contato_compras = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Contato de Compras",
        help_text="Preenchido automaticamente dos parâmetros"
    )
    
    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_PEDIDO_CHOICES, default='RASCUNHO')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_PEDIDO_CHOICES, default='NORMAL')
    
    # Valores
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Total")
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Desconto %")
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Desconto R$")
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Frete")
    valor_final = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Final")
    
    # Condições comerciais
    condicao_pagamento = models.CharField(max_length=100, blank=True, verbose_name="Condição de Pagamento")
    
    # Observações
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    observacoes_internas = models.TextField(blank=True, verbose_name="Observações Internas")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='pedidos_compra_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='pedidos_compra_atualizados',
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = "Pedido de Compra"
        verbose_name_plural = "Pedidos de Compra"
        ordering = ['-data_emissao', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['fornecedor', 'status']),
            models.Index(fields=['data_emissao']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.fornecedor.razao_social}"
    
    def clean(self):
        """Validações customizadas"""
        errors = {}
        
        # Calcular data de entrega se não fornecida
        if self.data_emissao and self.prazo_entrega and not self.data_entrega_prevista:
            self.data_entrega_prevista = self.calcular_data_entrega()
        
        # Validar que data de entrega não é anterior à emissão
        if self.data_emissao and self.data_entrega_prevista:
            if self.data_entrega_prevista < self.data_emissao:
                errors['data_entrega_prevista'] = 'Data de entrega não pode ser anterior à data de emissão.'
        
        if errors:
            raise ValidationError(errors)
    
    def calcular_data_entrega(self):
        """Calcula data de entrega baseada na data de emissão + prazo"""
        if not self.data_emissao or not self.prazo_entrega:
            return None
        
        # Adiciona os dias de prazo à data de emissão
        # Aqui você pode implementar lógica para dias úteis se necessário
        return self.data_emissao + timedelta(days=self.prazo_entrega)
    
    def calcular_prazo_entrega(self):
        """Calcula prazo baseado nas datas de emissão e entrega"""
        if not self.data_emissao or not self.data_entrega_prevista:
            return None
        
        delta = self.data_entrega_prevista - self.data_emissao
        return delta.days
    
    def atualizar_dados_compras(self):
        """Atualiza dados do comprador dos parâmetros gerais"""
        try:
            from .parametros import ParametrosGerais
            parametros = ParametrosGerais.objects.first()
            if parametros:
                if parametros.comprador_responsavel:
                    self.comprador_responsavel = parametros.comprador_responsavel
                if parametros.contato_compras:
                    self.contato_compras = parametros.contato_compras
        except Exception:
            pass
    
    def save(self, *args, **kwargs):
        """Override para gerar número automático e calcular datas"""
        # Gerar número no formato AAMM0001
        if not self.numero:
            self.numero = self.gerar_numero()
        
        # Atualizar dados de compras dos parâmetros
        if not self.comprador_responsavel or not self.contato_compras:
            self.atualizar_dados_compras()
        
        # Calcular data de entrega se necessário
        if self.data_emissao and self.prazo_entrega and not self.data_entrega_prevista:
            self.data_entrega_prevista = self.calcular_data_entrega()
        
        # Executar validações
        self.clean()
        
        # Salvar primeiro, depois calcular valores
        super().save(*args, **kwargs)
        
        # Agora calcular valores (com ID já definido)
        self.calcular_valores()
        
        # Salvar novamente com valores calculados
        if hasattr(self, '_calcular_valores_executado'):
            # Evitar loop infinito - só salvar os campos de valores
            super().save(update_fields=['valor_total', 'desconto_valor', 'valor_final'])
    
    def gerar_numero(self):
        """Gera número automático no formato AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')  # Formato AAMM (24 para 2024, etc)
        
        # Buscar o último número do mês
        ultimo_pedido = PedidoCompra.objects.filter(
            numero__startswith=f'{ano_mes}'
        ).order_by('-numero').first()
        
        if ultimo_pedido:
            # Extrair o número sequencial (últimos 4 dígitos)
            try:
                ultimo_seq = int(ultimo_pedido.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1
        
        return f'{ano_mes}{proximo_seq:04d}'
        
    def calcular_valores(self):
        """Calcula os valores totais do pedido"""
        # Só calcular se o pedido tem ID (foi salvo)
        if not self.pk:
            return
        
        # Marcar que estamos calculando para evitar loop
        self._calcular_valores_executado = True
        
        # Somar valor dos itens
        total_itens = self.itens.aggregate(
            total=models.Sum(
                models.F('quantidade') * models.F('valor_unitario'),
                output_field=models.DecimalField(max_digits=12, decimal_places=2)
            )
        )['total'] or 0
        
        self.valor_total = total_itens
        
        # Aplicar desconto percentual
        if self.desconto_percentual > 0:
            self.desconto_valor = (self.valor_total * self.desconto_percentual / 100)
        
        # Calcular valor final
        self.valor_final = self.valor_total - self.desconto_valor + self.valor_frete
    
    def recalcular_valores(self):
        """Método público para recalcular valores"""
        self.calcular_valores()
        self.save(update_fields=['valor_total', 'desconto_valor', 'valor_final'])
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        classes = {
            'RASCUNHO': 'bg-secondary',
            'ENVIADO': 'bg-info', 
            'CONFIRMADO': 'bg-primary',
            'PARCIAL': 'bg-warning',
            'RECEBIDO': 'bg-success',
            'CANCELADO': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def prioridade_badge_class(self):
        """Retorna classe CSS para badge de prioridade"""
        classes = {
            'BAIXA': 'bg-light text-dark',
            'NORMAL': 'bg-info',
            'ALTA': 'bg-warning',
            'URGENTE': 'bg-danger',
        }
        return classes.get(self.prioridade, 'bg-info')
    
    @property
    def pode_editar(self):
        """Verifica se o pedido pode ser editado"""
        return self.status in ['RASCUNHO', 'ENVIADO']
    
    @property
    def pode_cancelar(self):
        """Verifica se o pedido pode ser cancelado"""
        return self.status not in ['RECEBIDO', 'CANCELADO']
    
    @property
    def dias_para_entrega(self):
        """Calcula quantos dias faltam para a entrega"""
        if not self.data_entrega_prevista:
            return None
        
        hoje = date.today()
        delta = self.data_entrega_prevista - hoje
        return delta.days
    
    @property
    def status_prazo(self):
        """Retorna status do prazo: 'em_dia', 'atrasado', 'vencido'"""
        if not self.data_entrega_prevista:
            return 'indefinido'
        
        dias = self.dias_para_entrega
        if dias is None:
            return 'indefinido'
        elif dias < 0:
            return 'vencido'
        elif dias <= 2:
            return 'urgente'
        else:
            return 'em_dia'
    
    def get_total_quantidade(self):
        """Retorna a quantidade total de itens"""
        if not self.pk:
            return 0
        return self.itens.aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0
    
    def get_total_itens(self):
        """Retorna o número total de itens diferentes"""
        if not self.pk:
            return 0
        return self.itens.count()

    def get_requisicoes_vinculadas(self):
        """Retorna requisições vinculadas através dos itens"""
        if not self.pk:
            from .producao import RequisicaoCompra
            return RequisicaoCompra.objects.none()

        from .producao import RequisicaoCompra
        requisicoes_ids = self.itens.filter(
            item_requisicao__isnull=False
        ).values_list('item_requisicao__requisicao', flat=True).distinct()

        return RequisicaoCompra.objects.filter(id__in=requisicoes_ids)


class ItemPedidoCompra(models.Model):
    """
    Item do pedido de compra
    """
    pedido = models.ForeignKey(
        PedidoCompra,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_pedido_compra'
    )

    # VÍNCULO COM REQUISIÇÃO - CHAVE PARA RASTREABILIDADE
    item_requisicao = models.ForeignKey(
        'ItemRequisicaoCompra',
        on_delete=models.PROTECT,
        related_name='itens_pedido',
        blank=True,
        null=True,
        verbose_name="Item da Requisição",
        help_text="Item da requisição que este pedido atende"
    )

    # Quantidades
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    unidade = models.CharField(max_length=10, verbose_name="Unidade")
    
    # Valores
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Unitário")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")
    
    # Recebimento
    quantidade_recebida = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Quantidade Recebida"
    )
    data_recebimento = models.DateTimeField(blank=True, null=True, verbose_name="Data Recebimento")
    
    # Observações do item
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item do Pedido de Compra"
        verbose_name_plural = "Itens dos Pedidos de Compra"
        ordering = ['id']
        # Removido unique_together: permite mesmo produto múltiplas vezes
        # (útil quando vinculado a requisições diferentes)
    
    def __str__(self):
        return f"{self.pedido.numero} - {self.produto.codigo}"
    
    def save(self, *args, **kwargs):
        """Override para calcular valor total"""
        # Definir unidade baseada no produto
        if not self.unidade:
            self.unidade = self.produto.unidade_medida
        
        # Calcular valor total
        self.valor_total = self.quantidade * self.valor_unitario
        
        super().save(*args, **kwargs)
        
        # Recalcular valores do pedido usando método público
        if self.pedido.pk:
            self.pedido.recalcular_valores()
    
    def delete(self, *args, **kwargs):
        """Override para recalcular valores do pedido após exclusão"""
        pedido = self.pedido
        super().delete(*args, **kwargs)
        
        # Recalcular valores do pedido usando método público
        if pedido.pk:
            pedido.recalcular_valores()
    
    @property
    def quantidade_pendente(self):
        """Quantidade ainda não recebida"""
        return self.quantidade - self.quantidade_recebida
    
    @property
    def percentual_recebido(self):
        """Percentual recebido do item"""
        if self.quantidade > 0:
            return (self.quantidade_recebida / self.quantidade) * 100
        return 0
    
    @property
    def status_recebimento(self):
        """Status do recebimento do item"""
        if self.quantidade_recebida == 0:
            return 'PENDENTE'
        elif self.quantidade_recebida >= self.quantidade:
            return 'COMPLETO'
        else:
            return 'PARCIAL'
    
    @property
    def status_recebimento_badge_class(self):
        """Classe CSS para badge de status de recebimento"""
        classes = {
            'PENDENTE': 'bg-warning',
            'PARCIAL': 'bg-info',
            'COMPLETO': 'bg-success',
        }
        return classes.get(self.status_recebimento, 'bg-secondary')


class HistoricoPedidoCompra(models.Model):
    """
    Histórico de alterações no pedido de compra
    """
    pedido = models.ForeignKey(
        PedidoCompra, 
        on_delete=models.CASCADE, 
        related_name='historico'
    )
    
    # Informações da alteração
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT
    )
    acao = models.CharField(max_length=100, verbose_name="Ação")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    
    # Dados antes/depois (JSON)
    dados_anteriores = models.JSONField(default=dict, blank=True)
    dados_novos = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Histórico do Pedido"
        verbose_name_plural = "Histórico dos Pedidos"
        ordering = ['-data_alteracao']
    
    def __str__(self):
        return f"{self.pedido.numero} - {self.acao} - {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"