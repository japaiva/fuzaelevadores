# core/models/estoque.py

"""
Models relacionados a controle de estoque, movimentações e locais
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


# ===============================================
# CHOICES PARA ESTOQUE
# ===============================================

TIPO_LOCAL_ESTOQUE_CHOICES = [
    ('proprio', 'Estoque Próprio'),
    ('terceiros', 'Em Poder de Terceiros'),
]

TIPO_PARCEIRO_CHOICES = [
    ('fornecedor', 'Fornecedor'),
    ('cliente', 'Cliente'),
    ('interno', 'Interno/Nenhum'),
]

TIPO_PRODUTO_MOVIMENTO_CHOICES = [
    ('MP', 'Matéria-Prima'),
    ('PI', 'Produto Intermediário'),
    ('PA', 'Produto Acabado'),
]

TIPO_OPERACAO_CHOICES = [
    ('movto', 'Movimento'),
    ('op', 'OP/Requisição'),
]

STATUS_MOVIMENTO_CHOICES = [
    ('rascunho', 'Rascunho'),
    ('confirmado', 'Confirmado'),
    ('cancelado', 'Cancelado'),
]


# ===============================================
# LOCAL DE ESTOQUE
# ===============================================

class LocalEstoque(models.Model):
    """
    Local onde o estoque pode estar armazenado.
    Pode ser próprio (na fábrica) ou em terceiros (beneficiadores).
    """

    nome = models.CharField(
        max_length=100,
        verbose_name="Nome do Local"
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_LOCAL_ESTOQUE_CHOICES,
        default='proprio',
        verbose_name="Tipo"
    )
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.PROTECT,
        related_name='locais_estoque',
        blank=True,
        null=True,
        verbose_name="Fornecedor Responsável",
        help_text="Obrigatório se tipo = Em Poder de Terceiros"
    )
    endereco = models.TextField(
        blank=True,
        verbose_name="Endereço"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='locais_estoque_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Local de Estoque"
        verbose_name_plural = "Locais de Estoque"
        ordering = ['tipo', 'nome']

    def __str__(self):
        if self.tipo == 'terceiros' and self.fornecedor:
            return f"{self.nome} ({self.fornecedor})"
        return self.nome

    def clean(self):
        """Validação: se terceiros, fornecedor é obrigatório"""
        if self.tipo == 'terceiros' and not self.fornecedor:
            raise ValidationError({
                'fornecedor': 'Fornecedor é obrigatório para estoque em terceiros.'
            })
        if self.tipo == 'proprio' and self.fornecedor:
            raise ValidationError({
                'fornecedor': 'Não informe fornecedor para estoque próprio.'
            })


# ===============================================
# TIPO DE MOVIMENTO - ENTRADA
# ===============================================

class TipoMovimentoEntrada(models.Model):
    """
    Tipos de movimento de entrada (CFOPs de entrada).
    Define a natureza da entrada e quem é o parceiro.
    """

    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Código",
        help_text="Ex: 1101, 1202, 1902"
    )
    descricao = models.CharField(
        max_length=100,
        verbose_name="Descrição"
    )
    tipo_parceiro = models.CharField(
        max_length=15,
        choices=TIPO_PARCEIRO_CHOICES,
        default='fornecedor',
        verbose_name="Tipo de Parceiro",
        help_text="Define se a entrada é de fornecedor, cliente ou interno"
    )
    tipo_produto = models.CharField(
        max_length=2,
        choices=TIPO_PRODUTO_MOVIMENTO_CHOICES,
        default='MP',
        verbose_name="Tipo de Produto",
        help_text="Tipo de produto permitido: MP, PI ou PA"
    )
    tipo_operacao = models.CharField(
        max_length=10,
        choices=TIPO_OPERACAO_CHOICES,
        default='movto',
        verbose_name="Tipo de Operação",
        help_text="Define se será usado em Movimento ou OP/Requisição"
    )
    exige_nota_fiscal = models.BooleanField(
        default=False,
        verbose_name="Exige Nota Fiscal",
        help_text="Se marcado, NF será obrigatória para este tipo"
    )
    movimenta_terceiros = models.BooleanField(
        default=False,
        verbose_name="Movimenta Terceiros",
        help_text="Se marcado, indica entrada/retorno de material de terceiros"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tipos_movimento_entrada_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Movimento de Entrada"
        verbose_name_plural = "Tipos de Movimento de Entrada"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# ===============================================
# TIPO DE MOVIMENTO - SAÍDA
# ===============================================

class TipoMovimentoSaida(models.Model):
    """
    Tipos de movimento de saída (CFOPs de saída).
    Define a natureza da saída e quem é o parceiro.
    """

    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Código",
        help_text="Ex: 5101, 5901, 5949"
    )
    descricao = models.CharField(
        max_length=100,
        verbose_name="Descrição"
    )
    tipo_parceiro = models.CharField(
        max_length=15,
        choices=TIPO_PARCEIRO_CHOICES,
        default='cliente',
        verbose_name="Tipo de Parceiro",
        help_text="Define se a saída é para cliente, fornecedor ou interno"
    )
    tipo_produto = models.CharField(
        max_length=2,
        choices=TIPO_PRODUTO_MOVIMENTO_CHOICES,
        default='MP',
        verbose_name="Tipo de Produto",
        help_text="Tipo de produto permitido: MP, PI ou PA"
    )
    tipo_operacao = models.CharField(
        max_length=10,
        choices=TIPO_OPERACAO_CHOICES,
        default='movto',
        verbose_name="Tipo de Operação",
        help_text="Define se será usado em Movimento ou OP/Requisição"
    )
    exige_nota_fiscal = models.BooleanField(
        default=False,
        verbose_name="Exige Nota Fiscal",
        help_text="Se marcado, NF será obrigatória para este tipo"
    )
    movimenta_terceiros = models.BooleanField(
        default=False,
        verbose_name="Movimenta Terceiros",
        help_text="Se marcado, indica saída/remessa de material para terceiros"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tipos_movimento_saida_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Movimento de Saída"
        verbose_name_plural = "Tipos de Movimento de Saída"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# ===============================================
# MOVIMENTO DE ENTRADA
# ===============================================

class MovimentoEntrada(models.Model):
    """
    Movimento de entrada de materiais no estoque.
    Pode ou não ter nota fiscal vinculada.
    """

    # Identificação interna (automático)
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número Interno"
    )

    # Tipo de movimento
    tipo_movimento = models.ForeignKey(
        TipoMovimentoEntrada,
        on_delete=models.PROTECT,
        related_name='movimentos',
        verbose_name="Tipo de Movimento"
    )

    # Parceiros (um ou outro, baseado no tipo_movimento.tipo_parceiro)
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.PROTECT,
        related_name='entradas_estoque',
        blank=True,
        null=True,
        verbose_name="Fornecedor"
    )
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.PROTECT,
        related_name='entradas_estoque',
        blank=True,
        null=True,
        verbose_name="Cliente"
    )

    # Vinculo com pedido de compra (opcional)
    pedido_compra = models.ForeignKey(
        'PedidoCompra',
        on_delete=models.PROTECT,
        related_name='entradas_estoque',
        blank=True,
        null=True,
        verbose_name="Pedido de Compra",
        help_text="Opcional - Vincular a um pedido de compra"
    )

    # Dados da Nota Fiscal (opcionais)
    numero_nf = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número NF"
    )
    serie_nf = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Série NF"
    )
    chave_acesso = models.CharField(
        max_length=44,
        blank=True,
        verbose_name="Chave de Acesso NFe"
    )
    data_emissao_nf = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Emissão NF"
    )

    # Datas
    data_movimento = models.DateField(
        default=date.today,
        verbose_name="Data do Movimento"
    )
    data_entrada = models.DateField(
        default=date.today,
        verbose_name="Data da Entrada"
    )

    # Valores
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total"
    )
    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Frete"
    )
    valor_desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Desconto"
    )

    # Status
    status = models.CharField(
        max_length=15,
        choices=STATUS_MOVIMENTO_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='entradas_estoque_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='entradas_estoque_atualizadas',
        blank=True,
        null=True
    )
    confirmado_em = models.DateTimeField(blank=True, null=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='entradas_estoque_confirmadas',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Movimento de Entrada"
        verbose_name_plural = "Movimentos de Entrada"
        ordering = ['-data_movimento', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['data_movimento']),
            models.Index(fields=['fornecedor']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.tipo_movimento.descricao}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.gerar_numero()
        super().save(*args, **kwargs)

    def gerar_numero(self):
        """Gera número automático no formato ENT-AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')

        ultima = MovimentoEntrada.objects.filter(
            numero__startswith=f'ENT-{ano_mes}'
        ).order_by('-numero').first()

        if ultima:
            try:
                ultimo_seq = int(ultima.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1

        return f'ENT-{ano_mes}{proximo_seq:04d}'

    @property
    def tem_nota_fiscal(self):
        """Retorna True se tem NF vinculada"""
        return bool(self.numero_nf)

    def clean(self):
        """Validações"""
        errors = {}

        # Validar parceiro baseado no tipo
        if self.tipo_movimento_id:
            tipo_parceiro = self.tipo_movimento.tipo_parceiro
            if tipo_parceiro == 'fornecedor' and not self.fornecedor:
                errors['fornecedor'] = 'Fornecedor é obrigatório para este tipo de movimento.'
            if tipo_parceiro == 'cliente' and not self.cliente:
                errors['cliente'] = 'Cliente é obrigatório para este tipo de movimento.'

            # Validar NF se exigida
            if self.tipo_movimento.exige_nota_fiscal and not self.numero_nf:
                errors['numero_nf'] = 'Nota Fiscal é obrigatória para este tipo de movimento.'

        if errors:
            raise ValidationError(errors)

    def calcular_valor_total(self):
        """Calcula o valor total baseado nos itens"""
        total = sum(item.valor_total for item in self.itens.all())
        self.valor_total = total + self.valor_frete - self.valor_desconto
        return self.valor_total


class ItemMovimentoEntrada(models.Model):
    """
    Itens de um movimento de entrada
    """

    movimento = models.ForeignKey(
        MovimentoEntrada,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Movimento"
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_entrada',
        verbose_name="Produto"
    )

    # Quantidades
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )

    # Valores
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Valor Unitário"
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total"
    )

    # Rastreabilidade
    lote = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Lote"
    )
    data_validade = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Validade"
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Item de Entrada"
        verbose_name_plural = "Itens de Entrada"
        ordering = ['id']

    def __str__(self):
        return f"{self.produto.codigo} - {self.quantidade} {self.unidade}"

    def save(self, *args, **kwargs):
        # Preencher unidade do produto
        if not self.unidade and self.produto:
            self.unidade = self.produto.unidade_medida

        # Calcular valor total
        if self.quantidade and self.valor_unitario:
            self.valor_total = self.quantidade * self.valor_unitario

        super().save(*args, **kwargs)


# ===============================================
# MOVIMENTO DE SAÍDA
# ===============================================

class MovimentoSaida(models.Model):
    """
    Movimento de saída de materiais do estoque.
    Pode ou não ter nota fiscal vinculada.
    """

    # Identificação interna (automático)
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número Interno"
    )

    # Tipo de movimento
    tipo_movimento = models.ForeignKey(
        TipoMovimentoSaida,
        on_delete=models.PROTECT,
        related_name='movimentos',
        verbose_name="Tipo de Movimento"
    )

    # Parceiros (um ou outro, baseado no tipo_movimento.tipo_parceiro)
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.PROTECT,
        related_name='saidas_estoque',
        blank=True,
        null=True,
        verbose_name="Fornecedor"
    )
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.PROTECT,
        related_name='saidas_estoque',
        blank=True,
        null=True,
        verbose_name="Cliente"
    )

    # Dados da Nota Fiscal (opcionais)
    numero_nf = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número NF"
    )
    serie_nf = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Série NF"
    )
    chave_acesso = models.CharField(
        max_length=44,
        blank=True,
        verbose_name="Chave de Acesso NFe"
    )
    data_emissao_nf = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Emissão NF"
    )

    # Datas
    data_movimento = models.DateField(
        default=date.today,
        verbose_name="Data do Movimento"
    )
    data_saida = models.DateField(
        default=date.today,
        verbose_name="Data da Saída"
    )

    # Valores
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total"
    )
    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Frete"
    )
    valor_desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Desconto"
    )

    # Status
    status = models.CharField(
        max_length=15,
        choices=STATUS_MOVIMENTO_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='saidas_estoque_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='saidas_estoque_atualizadas',
        blank=True,
        null=True
    )
    confirmado_em = models.DateTimeField(blank=True, null=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='saidas_estoque_confirmadas',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Movimento de Saída"
        verbose_name_plural = "Movimentos de Saída"
        ordering = ['-data_movimento', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['data_movimento']),
            models.Index(fields=['cliente']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.tipo_movimento.descricao}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.gerar_numero()
        super().save(*args, **kwargs)

    def gerar_numero(self):
        """Gera número automático no formato SAI-AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')

        ultima = MovimentoSaida.objects.filter(
            numero__startswith=f'SAI-{ano_mes}'
        ).order_by('-numero').first()

        if ultima:
            try:
                ultimo_seq = int(ultima.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1

        return f'SAI-{ano_mes}{proximo_seq:04d}'

    @property
    def tem_nota_fiscal(self):
        """Retorna True se tem NF vinculada"""
        return bool(self.numero_nf)

    def clean(self):
        """Validações"""
        errors = {}

        # Validar parceiro baseado no tipo
        if self.tipo_movimento_id:
            tipo_parceiro = self.tipo_movimento.tipo_parceiro
            if tipo_parceiro == 'fornecedor' and not self.fornecedor:
                errors['fornecedor'] = 'Fornecedor é obrigatório para este tipo de movimento.'
            if tipo_parceiro == 'cliente' and not self.cliente:
                errors['cliente'] = 'Cliente é obrigatório para este tipo de movimento.'

            # Validar NF se exigida
            if self.tipo_movimento.exige_nota_fiscal and not self.numero_nf:
                errors['numero_nf'] = 'Nota Fiscal é obrigatória para este tipo de movimento.'

        if errors:
            raise ValidationError(errors)

    def calcular_valor_total(self):
        """Calcula o valor total baseado nos itens"""
        total = sum(item.valor_total for item in self.itens.all())
        self.valor_total = total + self.valor_frete - self.valor_desconto
        return self.valor_total


class ItemMovimentoSaida(models.Model):
    """
    Itens de um movimento de saída
    """

    movimento = models.ForeignKey(
        MovimentoSaida,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Movimento"
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_saida',
        verbose_name="Produto"
    )

    # Quantidades
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )

    # Valores
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Valor Unitário"
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total"
    )

    # Rastreabilidade
    lote = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Lote"
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Item de Saída"
        verbose_name_plural = "Itens de Saída"
        ordering = ['id']

    def __str__(self):
        return f"{self.produto.codigo} - {self.quantidade} {self.unidade}"

    def save(self, *args, **kwargs):
        # Preencher unidade do produto
        if not self.unidade and self.produto:
            self.unidade = self.produto.unidade_medida

        # Calcular valor total
        if self.quantidade and self.valor_unitario:
            self.valor_total = self.quantidade * self.valor_unitario

        super().save(*args, **kwargs)


# ===============================================
# REQUISIÇÃO DE MATERIAL (PRODUÇÃO)
# ===============================================

STATUS_REQUISICAO_MATERIAL_CHOICES = [
    ('rascunho', 'Rascunho'),
    ('pendente', 'Pendente'),
    ('atendida', 'Atendida'),
    ('parcial', 'Parcialmente Atendida'),
    ('cancelada', 'Cancelada'),
]


class RequisicaoMaterial(models.Model):
    """
    Requisição de Material para Produção.
    Vinculada a uma Proposta (OP).
    """

    # Identificação interna (automático)
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número"
    )

    # Tipo de movimento (filtrado para tipo_operacao='op')
    tipo_movimento = models.ForeignKey(
        TipoMovimentoSaida,
        on_delete=models.PROTECT,
        related_name='requisicoes_material',
        verbose_name="Tipo de Movimento"
    )

    # Vinculo com Proposta (OP) - opcional
    proposta = models.ForeignKey(
        'Proposta',
        on_delete=models.PROTECT,
        related_name='requisicoes_material',
        verbose_name="Proposta (OP)",
        blank=True,
        null=True
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

    # Status
    status = models.CharField(
        max_length=15,
        choices=STATUS_REQUISICAO_MATERIAL_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requisicoes_material_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requisicoes_material_atualizadas',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Requisição de Material"
        verbose_name_plural = "Requisições de Material"
        ordering = ['-data_requisicao', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['proposta']),
        ]

    def __str__(self):
        if self.proposta:
            return f"{self.numero} - OP {self.proposta.numero}"
        return f"{self.numero} - {self.tipo_movimento.descricao}"

    @property
    def tipo_produto(self):
        """Retorna o tipo de produto do tipo de movimento"""
        return self.tipo_movimento.tipo_produto if self.tipo_movimento_id else 'MP'

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.gerar_numero()
        super().save(*args, **kwargs)

    def gerar_numero(self):
        """Gera número automático no formato REQ-AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')

        ultima = RequisicaoMaterial.objects.filter(
            numero__startswith=f'REQ-{ano_mes}'
        ).order_by('-numero').first()

        if ultima:
            try:
                ultimo_seq = int(ultima.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1

        return f'REQ-{ano_mes}{proximo_seq:04d}'


class ItemRequisicaoMaterial(models.Model):
    """
    Itens de uma Requisição de Material
    """

    requisicao = models.ForeignKey(
        RequisicaoMaterial,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Requisição"
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='itens_requisicao_material',
        verbose_name="Produto"
    )

    # Quantidades
    quantidade_solicitada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade Solicitada"
    )
    quantidade_atendida = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade Atendida"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Item de Requisição"
        verbose_name_plural = "Itens de Requisição"
        ordering = ['id']

    def __str__(self):
        return f"{self.produto.codigo} - {self.quantidade_solicitada} {self.unidade}"

    def save(self, *args, **kwargs):
        # Preencher unidade do produto
        if not self.unidade and self.produto:
            self.unidade = self.produto.unidade_medida
        super().save(*args, **kwargs)

    @property
    def quantidade_pendente(self):
        """Quantidade ainda não atendida"""
        return self.quantidade_solicitada - self.quantidade_atendida

    @property
    def percentual_atendido(self):
        """Percentual atendido"""
        if self.quantidade_solicitada > 0:
            return (self.quantidade_atendida / self.quantidade_solicitada) * 100
        return 0


# ===============================================
# POSIÇÃO DE ESTOQUE
# ===============================================

class Estoque(models.Model):
    """
    Posição atual de estoque por produto e local.
    Atualizado automaticamente pelas movimentações.
    """

    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='posicoes_estoque',
        verbose_name="Produto"
    )
    local_estoque = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='posicoes',
        verbose_name="Local de Estoque"
    )

    # Quantidades
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade"
    )
    quantidade_reservada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade Reservada"
    )

    # Custo
    custo_medio = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Médio"
    )
    valor_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Valor Total em Estoque"
    )

    # Controle
    ultima_entrada = models.DateField(
        blank=True,
        null=True,
        verbose_name="Última Entrada"
    )
    ultima_saida = models.DateField(
        blank=True,
        null=True,
        verbose_name="Última Saída"
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Posição de Estoque"
        verbose_name_plural = "Posições de Estoque"
        unique_together = ['produto', 'local_estoque']
        ordering = ['produto__codigo', 'local_estoque__nome']
        indexes = [
            models.Index(fields=['produto', 'local_estoque']),
            models.Index(fields=['quantidade']),
        ]

    def __str__(self):
        return f"{self.produto.codigo} @ {self.local_estoque.nome}: {self.quantidade}"

    @property
    def quantidade_disponivel(self):
        """Quantidade disponível (total - reservada)"""
        return self.quantidade - self.quantidade_reservada

    def atualizar_valor_total(self):
        """Atualiza o valor total em estoque"""
        self.valor_total = self.quantidade * self.custo_medio
        return self.valor_total


# ===============================================
# HISTÓRICO DE MOVIMENTAÇÃO
# ===============================================

class MovimentoEstoque(models.Model):
    """
    Histórico de todas as movimentações de estoque.
    Registro imutável para rastreabilidade.
    """

    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste_positivo', 'Ajuste Positivo'),
        ('ajuste_negativo', 'Ajuste Negativo'),
        ('transferencia_entrada', 'Transferência (Entrada)'),
        ('transferencia_saida', 'Transferência (Saída)'),
    ]

    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='movimentos_estoque',
        verbose_name="Produto"
    )
    local_estoque = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='movimentos',
        verbose_name="Local de Estoque"
    )

    # Tipo e quantidade
    tipo = models.CharField(
        max_length=25,
        choices=TIPO_CHOICES,
        verbose_name="Tipo"
    )
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade"
    )

    # Saldos (para rastreabilidade)
    saldo_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Saldo Anterior"
    )
    saldo_posterior = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Saldo Posterior"
    )

    # Custos
    custo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Unitário"
    )
    custo_medio_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Médio Anterior"
    )
    custo_medio_posterior = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Médio Posterior"
    )

    # Rastreabilidade - origem do movimento
    documento_tipo = models.CharField(
        max_length=30,
        verbose_name="Tipo de Documento",
        help_text="entrada, saida, ajuste, op"
    )
    documento_numero = models.CharField(
        max_length=30,
        verbose_name="Número do Documento"
    )
    documento_id = models.IntegerField(
        verbose_name="ID do Documento"
    )

    # Data e hora
    data_movimento = models.DateField(
        verbose_name="Data do Movimento"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimentos_estoque_criados'
    )

    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Movimento de Estoque"
        verbose_name_plural = "Movimentos de Estoque"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['produto', 'local_estoque']),
            models.Index(fields=['data_movimento']),
            models.Index(fields=['documento_tipo', 'documento_id']),
        ]

    def __str__(self):
        sinal = '+' if 'entrada' in self.tipo or 'positivo' in self.tipo else '-'
        return f"{self.produto.codigo} {sinal}{self.quantidade} ({self.documento_numero})"


# ===============================================
# ORDEM DE PRODUCAO - FASE 4
# ===============================================

STATUS_OP_CHOICES = [
    ('rascunho', 'Rascunho'),
    ('liberada', 'Liberada'),
    ('em_producao', 'Em Producao'),
    ('concluida', 'Concluida'),
    ('cancelada', 'Cancelada'),
]

STATUS_ITEM_OP_CHOICES = [
    ('pendente', 'Pendente'),
    ('reservado', 'Reservado'),
    ('consumido', 'Consumido'),
    ('cancelado', 'Cancelado'),
]


class OrdemProducao(models.Model):
    """
    Ordem de Producao para fabricacao de produtos (PA ou PI).
    Consome materiais (MP/PI) baseado na estrutura do produto.
    """

    # Identificacao (automatico)
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numero da OP"
    )

    # Produto a ser produzido (PA ou PI montado)
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='ordens_producao',
        verbose_name="Produto",
        help_text="Produto a ser fabricado (PA ou PI)"
    )

    # Quantidades
    quantidade_planejada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade Planejada"
    )
    quantidade_produzida = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade Produzida"
    )

    # Status
    status = models.CharField(
        max_length=15,
        choices=STATUS_OP_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )

    # Prioridade
    prioridade = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Prioridade",
        help_text="1 = Urgente, 5 = Normal, 10 = Baixa"
    )

    # Locais de estoque
    local_producao = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='ops_producao',
        verbose_name="Local de Producao",
        help_text="Onde a producao acontece"
    )
    local_destino = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='ops_destino',
        verbose_name="Local de Destino",
        help_text="Onde o produto acabado sera armazenado"
    )

    # Datas planejadas
    data_inicio_planejada = models.DateField(
        blank=True,
        null=True,
        verbose_name="Inicio Planejado"
    )
    data_fim_planejada = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fim Planejado"
    )

    # Datas reais
    data_inicio_real = models.DateField(
        blank=True,
        null=True,
        verbose_name="Inicio Real"
    )
    data_fim_real = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fim Real"
    )

    # Custos
    custo_previsto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Custo Previsto"
    )
    custo_real = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Custo Real"
    )

    # Vinculo com proposta/pedido (opcional)
    proposta = models.ForeignKey(
        'Proposta',
        on_delete=models.SET_NULL,
        related_name='ordens_producao',
        blank=True,
        null=True,
        verbose_name="Proposta"
    )

    # Observacoes
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ops_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ops_atualizadas',
        blank=True,
        null=True
    )
    liberado_em = models.DateTimeField(blank=True, null=True)
    liberado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ops_liberadas',
        blank=True,
        null=True
    )
    concluido_em = models.DateTimeField(blank=True, null=True)
    concluido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ops_concluidas',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Ordem de Producao"
        verbose_name_plural = "Ordens de Producao"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['status']),
            models.Index(fields=['produto']),
            models.Index(fields=['data_inicio_planejada']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.produto.codigo}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.gerar_numero()
        super().save(*args, **kwargs)

    def gerar_numero(self):
        """Gera numero automatico no formato OP-AAMM0001"""
        agora = timezone.now()
        ano_mes = agora.strftime('%y%m')

        ultima = OrdemProducao.objects.filter(
            numero__startswith=f'OP-{ano_mes}'
        ).order_by('-numero').first()

        if ultima:
            try:
                ultimo_seq = int(ultima.numero[-4:])
                proximo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                proximo_seq = 1
        else:
            proximo_seq = 1

        return f'OP-{ano_mes}{proximo_seq:04d}'

    @property
    def percentual_concluido(self):
        """Percentual de conclusao"""
        if self.quantidade_planejada > 0:
            return (self.quantidade_produzida / self.quantidade_planejada) * 100
        return 0

    @property
    def pode_liberar(self):
        """Verifica se a OP pode ser liberada"""
        return self.status == 'rascunho' and self.itens_consumo.exists()

    @property
    def pode_iniciar(self):
        """Verifica se a OP pode iniciar producao"""
        return self.status == 'liberada'

    @property
    def pode_concluir(self):
        """Verifica se a OP pode ser concluida"""
        return self.status == 'em_producao' and self.quantidade_produzida > 0

    @property
    def pode_cancelar(self):
        """Verifica se a OP pode ser cancelada"""
        return self.status in ('rascunho', 'liberada')

    def calcular_materiais_necessarios(self):
        """
        Calcula os materiais necessarios baseado na estrutura do produto.
        Cria os ItemConsumoOP automaticamente.
        """
        from core.models import EstruturaProduto

        # Limpar itens existentes se rascunho
        if self.status == 'rascunho':
            self.itens_consumo.all().delete()

        # Buscar estrutura do produto
        estrutura = EstruturaProduto.objects.filter(
            produto_pai=self.produto
        ).select_related('produto_filho')

        custo_total = 0

        for componente in estrutura:
            # Quantidade necessaria = qtd estrutura * qtd planejada * (1 + % perda)
            qtd_necessaria = (
                componente.quantidade *
                self.quantidade_planejada *
                (1 + (componente.percentual_perda / 100))
            )

            # Criar item de consumo
            item = ItemConsumoOP.objects.create(
                ordem_producao=self,
                produto=componente.produto_filho,
                quantidade_prevista=qtd_necessaria,
                unidade=componente.unidade,
                local_estoque=self.local_producao,
                custo_unitario_previsto=componente.produto_filho.custo_total or 0
            )

            custo_total += item.quantidade_prevista * item.custo_unitario_previsto

        self.custo_previsto = custo_total
        self.save(update_fields=['custo_previsto'])

        return self.itens_consumo.count()

    def liberar(self, usuario):
        """Libera a OP para producao"""
        if not self.pode_liberar:
            raise ValidationError("OP nao pode ser liberada.")

        # Reservar materiais
        for item in self.itens_consumo.all():
            item.reservar()

        self.status = 'liberada'
        self.liberado_em = timezone.now()
        self.liberado_por = usuario
        self.save()

    def iniciar_producao(self, usuario):
        """Inicia a producao"""
        if not self.pode_iniciar:
            raise ValidationError("OP nao pode iniciar producao.")

        self.status = 'em_producao'
        self.data_inicio_real = date.today()
        self.atualizado_por = usuario
        self.save()

    def registrar_producao(self, quantidade, usuario):
        """Registra quantidade produzida"""
        if self.status != 'em_producao':
            raise ValidationError("OP nao esta em producao.")

        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser positiva.")

        self.quantidade_produzida += quantidade
        self.atualizado_por = usuario
        self.save()

    def concluir(self, usuario):
        """Conclui a OP"""
        if not self.pode_concluir:
            raise ValidationError("OP nao pode ser concluida.")

        # Consumir materiais que ainda nao foram consumidos
        for item in self.itens_consumo.filter(status='reservado'):
            item.consumir()

        # Calcular custo real
        self.custo_real = sum(
            item.quantidade_consumida * item.custo_unitario_real
            for item in self.itens_consumo.all()
        )

        self.status = 'concluida'
        self.data_fim_real = date.today()
        self.concluido_em = timezone.now()
        self.concluido_por = usuario
        self.save()

    def cancelar(self, usuario, motivo=''):
        """Cancela a OP"""
        if not self.pode_cancelar:
            raise ValidationError("OP nao pode ser cancelada.")

        # Liberar reservas
        for item in self.itens_consumo.filter(status='reservado'):
            item.cancelar()

        self.status = 'cancelada'
        self.atualizado_por = usuario
        if motivo:
            self.observacoes = f"{self.observacoes}\n\nMotivo cancelamento: {motivo}".strip()
        self.save()


class ItemConsumoOP(models.Model):
    """
    Itens a serem consumidos em uma Ordem de Producao.
    Gerados automaticamente a partir da estrutura do produto.
    """

    ordem_producao = models.ForeignKey(
        OrdemProducao,
        on_delete=models.CASCADE,
        related_name='itens_consumo',
        verbose_name="Ordem de Producao"
    )
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='consumos_op',
        verbose_name="Produto"
    )

    # Quantidades
    quantidade_prevista = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade Prevista"
    )
    quantidade_reservada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade Reservada"
    )
    quantidade_consumida = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade Consumida"
    )
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade"
    )

    # Local de onde sera consumido
    local_estoque = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='itens_consumo_op',
        verbose_name="Local de Estoque"
    )

    # Custos
    custo_unitario_previsto = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Unitario Previsto"
    )
    custo_unitario_real = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Unitario Real"
    )

    # Status do item
    status = models.CharField(
        max_length=15,
        choices=STATUS_ITEM_OP_CHOICES,
        default='pendente',
        verbose_name="Status"
    )

    # Observacoes
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )

    class Meta:
        verbose_name = "Item de Consumo OP"
        verbose_name_plural = "Itens de Consumo OP"
        ordering = ['produto__codigo']

    def __str__(self):
        return f"{self.produto.codigo} - {self.quantidade_prevista} {self.unidade}"

    @property
    def custo_total_previsto(self):
        return self.quantidade_prevista * self.custo_unitario_previsto

    @property
    def custo_total_real(self):
        return self.quantidade_consumida * self.custo_unitario_real

    @property
    def estoque_disponivel(self):
        """Retorna o estoque disponivel do produto no local"""
        try:
            posicao = Estoque.objects.get(
                produto=self.produto,
                local_estoque=self.local_estoque
            )
            return posicao.quantidade_disponivel
        except Estoque.DoesNotExist:
            return 0

    @property
    def tem_estoque_suficiente(self):
        """Verifica se tem estoque suficiente para reservar"""
        return self.estoque_disponivel >= self.quantidade_prevista

    def reservar(self):
        """Reserva a quantidade no estoque"""
        if self.status != 'pendente':
            raise ValidationError("Item ja foi processado.")

        # Buscar ou criar posicao de estoque
        posicao, created = Estoque.objects.get_or_create(
            produto=self.produto,
            local_estoque=self.local_estoque,
            defaults={'quantidade': 0, 'custo_medio': 0}
        )

        if posicao.quantidade_disponivel < self.quantidade_prevista:
            raise ValidationError(
                f"Estoque insuficiente de {self.produto.codigo}. "
                f"Disponivel: {posicao.quantidade_disponivel}, "
                f"Necessario: {self.quantidade_prevista}"
            )

        # Reservar
        posicao.quantidade_reservada += self.quantidade_prevista
        posicao.save()

        self.quantidade_reservada = self.quantidade_prevista
        self.custo_unitario_real = posicao.custo_medio
        self.status = 'reservado'
        self.save()

    def consumir(self, quantidade=None):
        """Consome a quantidade do estoque"""
        if self.status not in ('reservado', 'pendente'):
            raise ValidationError("Item nao pode ser consumido.")

        qtd_consumir = quantidade or self.quantidade_reservada or self.quantidade_prevista

        # Buscar posicao de estoque
        try:
            posicao = Estoque.objects.get(
                produto=self.produto,
                local_estoque=self.local_estoque
            )
        except Estoque.DoesNotExist:
            raise ValidationError(f"Nao ha estoque de {self.produto.codigo}.")

        # Baixar do estoque
        if self.status == 'reservado':
            posicao.quantidade_reservada -= self.quantidade_reservada
        posicao.quantidade -= qtd_consumir
        posicao.ultima_saida = date.today()
        posicao.save()

        # Atualizar produto
        self.produto.estoque_atual -= qtd_consumir
        self.produto.save(update_fields=['estoque_atual'])

        # Atualizar item
        self.quantidade_consumida = qtd_consumir
        self.quantidade_reservada = 0
        self.custo_unitario_real = posicao.custo_medio
        self.status = 'consumido'
        self.save()

    def cancelar(self):
        """Cancela a reserva"""
        if self.status != 'reservado':
            self.status = 'cancelado'
            self.save()
            return

        # Liberar reserva
        try:
            posicao = Estoque.objects.get(
                produto=self.produto,
                local_estoque=self.local_estoque
            )
            posicao.quantidade_reservada -= self.quantidade_reservada
            posicao.save()
        except Estoque.DoesNotExist:
            pass

        self.quantidade_reservada = 0
        self.status = 'cancelado'
        self.save()
