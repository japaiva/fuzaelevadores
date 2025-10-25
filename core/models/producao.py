# core/models/producao.py

"""
Models relacionados ao fluxo de produção:
Lista de Materiais → Requisição de Compras → Orçamento → Pedido de Compra
Portal de Produção - Sistema Elevadores FUZA
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

from .base import STATUS_PEDIDO_CHOICES, PRIORIDADE_PEDIDO_CHOICES

class ListaMateriais(models.Model):
    
    # Relacionamento com proposta
    proposta = models.OneToOneField(
        'Proposta',
        on_delete=models.CASCADE,
        related_name='lista_materiais',
        verbose_name="Proposta"
    )
    
    # Status e controle - ✅ SIMPLIFICADO
    status = models.CharField(
        max_length=20,
        choices=[
            ('calculando', 'Calculando'),      # Processando cálculo
            ('em_edicao', 'Em Edição'),        # Calculada, pode editar
            ('aprovada', 'Aprovada'),          # Aprovada para requisição
        ],
        default='calculando',
        verbose_name="Status"
    )
        
    # Dados calculados originais (para comparação)
    dados_calculo_original = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dados Cálculo Original"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    observacoes_internas = models.TextField(
        blank=True,
        verbose_name="Observações Internas"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='listas_materiais_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='listas_materiais_atualizadas',
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = "Lista de Materiais"
        verbose_name_plural = "Listas de Materiais"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Lista Materiais - {self.proposta.numero}"
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        classes = {
            'calculando': 'bg-warning',      # Amarelo
            'em_edicao': 'bg-info',          # Azul
            'aprovada': 'bg-success',        # Verde
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def pode_editar(self):
        """Verifica se a lista pode ser editada"""
        return self.status == 'em_edicao'  # ✅ CORRIGIDO: Só em edição
    
    @property
    def pode_gerar_requisicao(self):
        """Verifica se pode gerar requisição"""
        return self.status == 'aprovada' and self.itens.exists()
    
    @property
    def calcular_valor_total(self):
        """Calcula valor total da lista de materiais"""
        if not self.pk:
            return 0
        return self.itens.aggregate(
            total=models.Sum(
                models.F('quantidade') * models.F('valor_unitario_estimado'),
                output_field=models.DecimalField(max_digits=12, decimal_places=2)
            )
        )['total'] or 0


class ItemListaMateriais(models.Model):
    """
    Item da lista de materiais
    """
    
    lista = models.ForeignKey(
        ListaMateriais,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_lista_materiais'
    )
    
    # Quantidades
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantidade"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )
    
    # Valores estimados
    valor_unitario_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Unitário Estimado"
    )
    valor_total_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Total Estimado"
    )
    
    # Controle
    item_calculado = models.BooleanField(
        default=True,
        verbose_name="Item Calculado",
        help_text="Se foi calculado automaticamente ou adicionado manualmente"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item da Lista de Materiais"
        verbose_name_plural = "Itens das Listas de Materiais"
        unique_together = ['lista', 'produto']
        ordering = ['produto__codigo']
    
    def __str__(self):
        return f"{self.lista} - {self.produto.codigo}"
    
    def save(self, *args, **kwargs):
        """Override para calcular valores"""
        # Definir unidade baseada no produto
        if not self.unidade:
            self.unidade = self.produto.unidade_medida
        
        # Calcular valor total estimado
        if self.quantidade and self.valor_unitario_estimado:
            self.valor_total_estimado = self.quantidade * self.valor_unitario_estimado
        
        super().save(*args, **kwargs)


class RequisicaoCompra(models.Model):
    """
    Requisição de compra gerada a partir da lista de materiais
    """
    
    # Identificação
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número da Requisição"
    )
    
    # Relacionamentos
    lista_materiais = models.ForeignKey(
        ListaMateriais,
        on_delete=models.PROTECT,
        related_name='requisicoes',
        verbose_name="Lista de Materiais",
        blank=True,
        null=True,
        help_text="Opcional - Se não informada, adicione itens manualmente"
    )
    
    # Status e prioridade
    status = models.CharField(
        max_length=20,
        choices=[
            ('rascunho', 'Rascunho'),
            ('aberta', 'Aberta'),
            ('cotando', 'Em Cotação'),
            ('orcada', 'Orçada'),
            ('aprovada', 'Aprovada'),
            ('cancelada', 'Cancelada'),
        ],
        default='rascunho',
        verbose_name="Status"
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_PEDIDO_CHOICES,
        default='NORMAL',
        verbose_name="Prioridade"
    )
    
    # Datas
    data_requisicao = models.DateField(
        default=date.today,
        verbose_name="Data da Requisição"
    )
    data_necessidade = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Necessidade"
    )
    
    # Solicitante
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requisicoes_solicitadas',
        verbose_name="Solicitante"
    )
    departamento = models.CharField(
        max_length=50,
        default='Produção',
        verbose_name="Departamento"
    )
    
    # Observações
    justificativa = models.TextField(
        blank=True,
        verbose_name="Justificativa"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    observacoes_compras = models.TextField(
        blank=True,
        verbose_name="Observações do Setor de Compras"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requisicoes_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requisicoes_atualizadas',
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = "Requisição de Compra"
        verbose_name_plural = "Requisições de Compra"
        ordering = ['-data_requisicao', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['data_requisicao']),
        ]
    
    def __str__(self):
        if self.lista_materiais:
            return f"REQ {self.numero} - {self.lista_materiais.proposta.numero}"
        return f"REQ {self.numero}"
    
    def save(self, *args, **kwargs):
        """Override para gerar número automático"""
        if not self.numero:
            self.numero = self.gerar_numero()
        super().save(*args, **kwargs)
    
    def gerar_numero(self):
        """Gera número automático no formato REQ-AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')
        
        # Buscar o último número do mês
        ultima_requisicao = RequisicaoCompra.objects.filter(
            numero__startswith=f'REQ-{ano_mes}'
        ).order_by('-numero').first()
        
        if ultima_requisicao:
            try:
                ultimo_seq = int(ultima_requisicao.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1
        
        return f'REQ-{ano_mes}{proximo_seq:04d}'
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        classes = {
            'rascunho': 'bg-secondary',
            'aberta': 'bg-info',
            'cotando': 'bg-warning',
            'orcada': 'bg-primary',
            'aprovada': 'bg-success',
            'cancelada': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def pode_editar(self):
        """Verifica se a requisição pode ser editada"""
        return self.status in ['rascunho', 'aberta']
    
    @property
    def pode_cancelar(self):
        """Verifica se a requisição pode ser cancelada"""
        return self.status not in ['cancelada', 'aprovada']
    
    def get_total_itens(self):
        """Retorna o número total de itens"""
        if not self.pk:
            return 0
        return self.itens.count()
    
    def get_valor_total_estimado(self):
        """Retorna valor total estimado dos itens"""
        if not self.pk:
            return 0
        return self.itens.aggregate(
            total=models.Sum('valor_total_estimado')
        )['total'] or 0


class ItemRequisicaoCompra(models.Model):
    """
    Item da requisição de compra
    """
    
    requisicao = models.ForeignKey(
        RequisicaoCompra,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_requisicao'
    )
    
    # Quantidades
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantidade"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )
    
    # Valores estimados
    valor_unitario_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Unitário Estimado"
    )
    valor_total_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Total Estimado"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item da Requisição"
        verbose_name_plural = "Itens das Requisições"
        unique_together = ['requisicao', 'produto']
        ordering = ['produto__codigo']
    
    def __str__(self):
        return f"{self.requisicao.numero} - {self.produto.codigo}"
    
    def save(self, *args, **kwargs):
        """Override para calcular valores"""
        if not self.unidade:
            self.unidade = self.produto.unidade_medida
        
        if self.quantidade and self.valor_unitario_estimado:
            self.valor_total_estimado = self.quantidade * self.valor_unitario_estimado
        
        super().save(*args, **kwargs)


class OrcamentoCompra(models.Model):
    """
    Orçamento de compra que puxa itens de uma ou mais requisições
    """
    
    # Identificação
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número do Orçamento"
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título do Orçamento"
    )
    
    # Relacionamentos com requisições
    requisicoes = models.ManyToManyField(
        RequisicaoCompra,
        related_name='orcamentos',
        verbose_name="Requisições"
    )
    
    # Status e prioridade
    status = models.CharField(
        max_length=20,
        choices=[
            ('rascunho', 'Rascunho'),
            ('cotando', 'Em Cotação'),
            ('cotado', 'Cotado'),
            ('analise', 'Em Análise'),
            ('aprovado', 'Aprovado'),
            ('rejeitado', 'Rejeitado'),
            ('cancelado', 'Cancelado'),
        ],
        default='rascunho',
        verbose_name="Status"
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_PEDIDO_CHOICES,
        default='NORMAL',
        verbose_name="Prioridade"
    )
    
    # Datas
    data_orcamento = models.DateField(
        default=date.today,
        verbose_name="Data do Orçamento"
    )
    data_validade = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Validade"
    )
    data_necessidade = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Necessidade"
    )
    
    # Responsáveis
    comprador_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orcamentos_comprador',
        verbose_name="Comprador Responsável"
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orcamentos_solicitante',
        verbose_name="Solicitante"
    )
    
    # Valores
    valor_total_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total Estimado"
    )
    valor_total_cotado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total Cotado"
    )
    
    # Observações
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    observacoes_internas = models.TextField(
        blank=True,
        verbose_name="Observações Internas"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orcamentos_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orcamentos_atualizados',
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = "Orçamento de Compra"
        verbose_name_plural = "Orçamentos de Compra"
        ordering = ['-data_orcamento', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['data_orcamento']),
        ]
    
    def __str__(self):
        return f"ORC {self.numero} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        """Override para gerar número automático"""
        if not self.numero:
            self.numero = self.gerar_numero()
        
        # Definir data de validade padrão se não informada
        if not self.data_validade:
            self.data_validade = self.data_orcamento + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def gerar_numero(self):
        """Gera número automático no formato ORC-AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')
        
        ultimo_orcamento = OrcamentoCompra.objects.filter(
            numero__startswith=f'{ano_mes}'
        ).order_by('-numero').first()
        
        if ultimo_orcamento:
            try:
                ultimo_seq = int(ultimo_orcamento.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1
        
        return f'{ano_mes}{proximo_seq:04d}'
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        classes = {
            'rascunho': 'bg-secondary',
            'cotando': 'bg-warning',
            'cotado': 'bg-info',
            'analise': 'bg-primary',
            'aprovado': 'bg-success',
            'rejeitado': 'bg-danger',
            'cancelado': 'bg-dark',
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def pode_editar(self):
        """Verifica se o orçamento pode ser editado"""
        return self.status in ['rascunho', 'cotando']
    
    @property
    def pode_cancelar(self):
        """Verifica se o orçamento pode ser cancelado"""
        return self.status not in ['cancelado', 'aprovado']
    
    @property
    def pode_gerar_pedido(self):
        """Verifica se pode gerar pedido de compra"""
        return self.status == 'aprovado' and self.itens.exists()
    
    @property
    def esta_vencido(self):
        """Verifica se o orçamento está vencido"""
        if not self.data_validade:
            return False
        return date.today() > self.data_validade
    
    def get_total_itens(self):
        """Retorna o número total de itens"""
        if not self.pk:
            return 0
        return self.itens.count()
    
    def get_total_fornecedores(self):
        """Retorna o número de fornecedores diferentes"""
        if not self.pk:
            return 0
        return self.itens.values('fornecedor').distinct().count()
    
    def calcular_valores(self):
        """Calcula valores totais do orçamento"""
        if not self.pk:
            return
        
        # Somar valores estimados e cotados
        totais = self.itens.aggregate(
            total_estimado=models.Sum('valor_total_estimado'),
            total_cotado=models.Sum('valor_total_cotado')
        )
        
        self.valor_total_estimado = totais['total_estimado'] or 0
        self.valor_total_cotado = totais['total_cotado'] or 0


class ItemOrcamentoCompra(models.Model):
    """
    Item do orçamento de compra com cotações
    """
    
    orcamento = models.ForeignKey(
        OrcamentoCompra,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_orcamento'
    )
    
    # Quantidades
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantidade"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )
    
    # Valores estimados (da requisição)
    valor_unitario_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Unitário Estimado"
    )
    valor_total_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Total Estimado"
    )
    
    # Cotação selecionada
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='itens_orcamento',
        verbose_name="Fornecedor Selecionado"
    )
    valor_unitario_cotado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Unitário Cotado"
    )
    valor_total_cotado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Total Cotado"
    )
    prazo_entrega = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Prazo Entrega (dias)"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    observacoes_cotacao = models.TextField(
        blank=True,
        verbose_name="Observações da Cotação"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item do Orçamento"
        verbose_name_plural = "Itens dos Orçamentos"
        unique_together = ['orcamento', 'produto']
        ordering = ['produto__codigo']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.produto.codigo}"
    
    def save(self, *args, **kwargs):
        """Override para calcular valores"""
        if not self.unidade:
            self.unidade = self.produto.unidade_medida
        
        # Calcular valor total estimado
        if self.quantidade and self.valor_unitario_estimado:
            self.valor_total_estimado = self.quantidade * self.valor_unitario_estimado
        
        # Calcular valor total cotado
        if self.quantidade and self.valor_unitario_cotado:
            self.valor_total_cotado = self.quantidade * self.valor_unitario_cotado
        
        super().save(*args, **kwargs)
        
        # Recalcular valores do orçamento
        if self.orcamento.pk:
            self.orcamento.calcular_valores()
            self.orcamento.save(update_fields=['valor_total_estimado', 'valor_total_cotado'])
    
    @property
    def tem_cotacao(self):
        """Verifica se o item tem cotação"""
        return bool(self.fornecedor and self.valor_unitario_cotado)
    
    @property
    def economia_percentual(self):
        """Calcula economia percentual entre estimado e cotado"""
        if not (self.valor_total_estimado and self.valor_total_cotado):
            return 0
        
        if self.valor_total_estimado > 0:
            economia = ((self.valor_total_estimado - self.valor_total_cotado) / self.valor_total_estimado) * 100
            return round(economia, 2)
        return 0


class HistoricoOrcamentoCompra(models.Model):
    """
    Histórico de alterações no orçamento de compra
    """
    orcamento = models.ForeignKey(
        OrcamentoCompra,
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
        verbose_name = "Histórico do Orçamento"
        verbose_name_plural = "Histórico dos Orçamentos"
        ordering = ['-data_alteracao']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.acao} - {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"