# core/models/elevadores.py

"""
Models relacionados ao motor de regras configurável de elevadores
"""

from django.db import models
from django.conf import settings

from .base import (
    TIPO_ESPECIFICACAO_CHOICES, 
    TIPO_CALCULO_CHOICES, 
    STATUS_SIMULACAO_CHOICES
)


class EspecificacaoElevador(models.Model):
    """
    Define os tipos de especificações possíveis para elevadores
    """
    
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=20, choices=TIPO_ESPECIFICACAO_CHOICES, verbose_name="Tipo")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    obrigatoria = models.BooleanField(default=True, verbose_name="Obrigatória")
    ordem = models.IntegerField(default=0, verbose_name="Ordem de Apresentação")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Especificação de Elevador"
        verbose_name_plural = "Especificações de Elevadores"
        ordering = ['ordem', 'nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class OpcaoEspecificacao(models.Model):
    """
    Define as opções disponíveis para cada especificação
    """
    especificacao = models.ForeignKey(EspecificacaoElevador, on_delete=models.CASCADE, related_name='opcoes')
    codigo = models.CharField(max_length=20, verbose_name="Código")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    valor_numerico = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                       verbose_name="Valor Numérico")
    unidade = models.CharField(max_length=10, blank=True, verbose_name="Unidade")
    ordem = models.IntegerField(default=0, verbose_name="Ordem")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    motivo_bloqueio = models.TextField(blank=True, verbose_name="Motivo do Bloqueio")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Opção de Especificação"
        verbose_name_plural = "Opções de Especificações"
        ordering = ['especificacao__ordem', 'ordem', 'nome']
        unique_together = ['especificacao', 'codigo']
    
    def __str__(self):
        return f"{self.especificacao.codigo}.{self.codigo} - {self.nome}"


class RegraComponente(models.Model):
    """
    Define regras para seleção automática de componentes baseado nas especificações
    """
    nome = models.CharField(max_length=100, verbose_name="Nome da Regra")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    
    # Condições em formato JSON
    # Exemplo: {"material": "Inox 430", "espessura": "1,2", "categoria": "Residencial"}
    condicoes = models.JSONField(default=dict, verbose_name="Condições")
    
    # Componente selecionado quando as condições forem atendidas
    componente = models.ForeignKey('Produto', on_delete=models.CASCADE, verbose_name="Componente")
    
    # Fórmula para calcular quantidade (opcional)
    formula_quantidade = models.TextField(
        blank=True,
        verbose_name="Fórmula Quantidade",
        help_text="Ex: 'altura * 2 + largura' ou valor fixo como '4'"
    )
    
    # Prioridade (menor número = maior prioridade)
    prioridade = models.IntegerField(default=100, verbose_name="Prioridade")
    
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Regra de Componente"
        verbose_name_plural = "Regras de Componentes"
        ordering = ['prioridade', 'nome']
    
    def __str__(self):
        return f"{self.nome} → {self.componente.codigo}"


class ComponenteDerivado(models.Model):
    """
    Define componentes que são derivados de outros componentes
    (ex: corte, dobra, pintura, etc.)
    """
    
    componente_origem = models.ForeignKey(
        'Produto', 
        on_delete=models.CASCADE, 
        related_name='derivados',
        verbose_name="Componente Origem"
    )
    componente_destino = models.ForeignKey(
        'Produto', 
        on_delete=models.CASCADE, 
        related_name='origem_derivacao',
        verbose_name="Componente Destino"
    )
    
    tipo_calculo = models.CharField(max_length=20, choices=TIPO_CALCULO_CHOICES, default='proporcional')
    multiplicador = models.DecimalField(max_digits=10, decimal_places=4, default=1.0, 
                                      verbose_name="Multiplicador")
    formula = models.TextField(blank=True, verbose_name="Fórmula Personalizada")
    
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Componente Derivado"
        verbose_name_plural = "Componentes Derivados"
        unique_together = ['componente_origem', 'componente_destino']
    
    def __str__(self):
        return f"{self.componente_origem.codigo} → {self.componente_destino.codigo}"


class SimulacaoElevador(models.Model):
    """
    Armazena simulações de elevadores feitas pelos vendedores
    """
    
    numero = models.CharField(max_length=20, unique=True, verbose_name="Número")
    nome = models.CharField(max_length=200, verbose_name="Nome do Projeto")
    cliente_nome = models.CharField(max_length=200, verbose_name="Nome do Cliente")
    cliente_contato = models.CharField(max_length=200, blank=True, verbose_name="Contato do Cliente")
    
    # Especificações selecionadas (JSON)
    especificacoes = models.JSONField(default=dict, verbose_name="Especificações")
    
    # Resultado da simulação
    componentes_calculados = models.JSONField(default=list, verbose_name="Componentes Calculados")
    codigo_produto_gerado = models.CharField(max_length=50, blank=True, verbose_name="Código Produto")
    preco_calculado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True,
                                        verbose_name="Preço Calculado")
    
    status = models.CharField(max_length=20, choices=STATUS_SIMULACAO_CHOICES, default='rascunho')
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Simulação de Elevador"
        verbose_name_plural = "Simulações de Elevadores"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.numero} - {self.nome}"