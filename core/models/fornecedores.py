# core/models/fornecedores.py

"""
Models relacionados a fornecedores
"""

from django.db import models
from django.conf import settings

from .base import PRIORIDADE_FORNECEDOR_CHOICES


class Fornecedor(models.Model):
    """Cadastro de fornecedores"""
    
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)
    contato_principal = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='fornecedores_criados'
    )
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['razao_social']
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social


class FornecedorProduto(models.Model):
    """
    Relacionamento N:N entre Fornecedor e Produto com informações específicas
    """
    
    produto = models.ForeignKey(
        'Produto', 
        on_delete=models.CASCADE, 
        related_name='fornecedores_produto'
    )
    fornecedor = models.ForeignKey(
        Fornecedor, 
        on_delete=models.CASCADE, 
        related_name='produtos_fornecedor'
    )
    
    # Informações específicas desta relação
    codigo_fornecedor = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Código do Fornecedor",
        help_text="Código que o fornecedor usa para este produto"
    )
    preco_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Preço Unitário"
    )
    prioridade = models.IntegerField(
        choices=PRIORIDADE_FORNECEDOR_CHOICES, 
        default=2,
        verbose_name="Prioridade"
    )
    prazo_entrega = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name="Prazo Entrega (dias)"
    )
    quantidade_minima = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1,
        verbose_name="Quantidade Mínima"
    )
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações",
        help_text="Condições especiais, descontos, etc."
    )
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    ultima_cotacao = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Última Cotação"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='fornecedor_produto_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Fornecedor do Produto"
        verbose_name_plural = "Fornecedores dos Produtos"
        unique_together = ['produto', 'fornecedor']
        ordering = ['prioridade', '-ativo', 'fornecedor__razao_social']
    
    def __str__(self):
        return f"{self.produto.codigo} → {self.fornecedor.nome_fantasia or self.fornecedor.razao_social}"
    
    @property
    def prioridade_display_badge(self):
        """Retorna classe CSS para badge de prioridade"""
        badges = {
            1: 'bg-success',     # Principal
            2: 'bg-primary',     # Secundário  
            3: 'bg-info',        # Terceiro
            4: 'bg-warning',     # Backup
        }
        return badges.get(self.prioridade, 'bg-secondary')