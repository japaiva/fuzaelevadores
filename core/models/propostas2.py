# Adicionar no core/models/propostas.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .propostas import Proposta

class VistoriaHistorico(models.Model):
    """
    Histórico de todas as vistorias realizadas na proposta
    """
    STATUS_VISTORIA_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('reagendada', 'Reagendada'),
    ]
    
    TIPO_VISTORIA_CHOICES = [
        ('medicao', 'Medição Inicial'),
        ('acompanhamento', 'Acompanhamento'),
        ('obra_pronta', 'Obra Pronta'),
        ('entrega', 'Entrega'),
    ]
    
    # Relacionamentos
    proposta = models.ForeignKey(
        'Proposta', 
        on_delete=models.CASCADE, 
        related_name='vistorias'
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        verbose_name="Responsável pela Vistoria"
    )
    
    # Dados da vistoria
    data_agendada = models.DateField(
        verbose_name="Data Agendada"
    )
    data_realizada = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Data Realizada"
    )
    
    tipo_vistoria = models.CharField(
        max_length=20,
        choices=TIPO_VISTORIA_CHOICES,
        default='acompanhamento',
        verbose_name="Tipo de Vistoria"
    )
    
    status_vistoria = models.CharField(
        max_length=20,
        choices=STATUS_VISTORIA_CHOICES,
        default='agendada',
        verbose_name="Status da Vistoria"
    )
    
    # Status da obra antes/depois
    status_obra_anterior = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Status Anterior da Obra"
    )
    status_obra_novo = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Novo Status da Obra"
    )
    
    # Observações e recomendações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações gerais da vistoria"
    )
    
    recomendacoes = models.TextField(
        blank=True,
        verbose_name="Recomendações",
        help_text="Recomendações técnicas e pendências"
    )
    
    # Data da próxima vistoria (se aplicável)
    proxima_vistoria_sugerida = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Próxima Vistoria Sugerida"
    )
    
    # Fotos e anexos (JSON para flexibilidade)
    fotos_anexos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Fotos e Anexos",
        help_text="Lista de URLs/caminhos para fotos e anexos"
    )
    
    # Dados técnicos específicos (JSON para flexibilidade)
    dados_tecnicos = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dados Técnicos",
        help_text="Medições, condições da obra, etc."
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vistorias_atualizadas',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Vistoria"
        verbose_name_plural = "Vistorias"
        ordering = ['-data_agendada', '-criado_em']
        indexes = [
            models.Index(fields=['proposta', '-data_agendada']),
            models.Index(fields=['responsavel', 'data_agendada']),
            models.Index(fields=['status_vistoria']),
            models.Index(fields=['tipo_vistoria']),
        ]
    
    def __str__(self):
        return f"Vistoria {self.proposta.numero} - {self.get_tipo_vistoria_display()} - {self.data_agendada.strftime('%d/%m/%Y')}"
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        badges = {
            'agendada': 'bg-info',
            'realizada': 'bg-success',
            'cancelada': 'bg-danger',
            'reagendada': 'bg-warning',
        }
        return badges.get(self.status_vistoria, 'bg-secondary')
    
    @property
    def esta_vencida(self):
        """Verifica se a vistoria está vencida"""
        if self.status_vistoria in ['realizada', 'cancelada']:
            return False
        from datetime import date
        return date.today() > self.data_agendada
    
    @property
    def dias_para_vistoria(self):
        """Retorna quantos dias para a vistoria"""
        if self.status_vistoria in ['realizada', 'cancelada']:
            return None
        from datetime import date
        delta = self.data_agendada - date.today()
        return delta.days
    
    def pode_realizar(self):
        """Verifica se a vistoria pode ser marcada como realizada"""
        return self.status_vistoria == 'agendada'
    
    def pode_cancelar(self):
        """Verifica se a vistoria pode ser cancelada"""
        return self.status_vistoria == 'agendada'
    
    def pode_reagendar(self):
        """Verifica se a vistoria pode ser reagendada"""
        return self.status_vistoria in ['agendada', 'cancelada']


# ===== FUNÇÃO PARA ATUALIZAR STATUS DA OBRA =====

def atualizar_status_obra_proposta(proposta, novo_status, usuario, observacao=""):
    """
    Função helper para atualizar status da obra e criar histórico
    """
    status_anterior = proposta.status_obra
    proposta.status_obra = novo_status
    proposta.save()
    
    # Criar entrada no histórico da proposta
    from .propostas import HistoricoProposta
    HistoricoProposta.objects.create(
        proposta=proposta,
        status_anterior=f"Obra: {status_anterior or 'Aguardando'}",
        status_novo=f"Obra: {novo_status}",
        observacao=f"Status da obra alterado. {observacao}".strip(),
        usuario=usuario
    )
    
    return proposta

# =============================================================================
# MODELOS RELACIONADOS (mantém os existentes)
# =============================================================================

class HistoricoProposta(models.Model):
    """
    Modelo para rastrear mudanças de status das propostas
    """
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=20, blank=True)
    status_novo = models.CharField(max_length=20)
    observacao = models.TextField(blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_mudanca = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Histórico da Proposta"
        verbose_name_plural = "Históricos das Propostas"
        ordering = ['-data_mudanca']
    
    def __str__(self):
        return f"{self.proposta.numero} - {self.status_anterior} → {self.status_novo}"


class AnexoProposta(models.Model):
    """
    Modelo para anexos das propostas (PDFs, imagens, etc.)
    """
    TIPO_CHOICES = [
        ('proposta', 'Proposta Comercial'),
        ('orcamento', 'Orçamento'),
        ('demonstrativo', 'Demonstrativo de Cálculo'),
        ('contrato', 'Contrato'),
        ('projeto', 'Projeto Técnico'),
        ('foto', 'Foto'),
        ('documento', 'Documento'),
        ('outro', 'Outro'),
    ]
    
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='anexos')
    nome = models.CharField(max_length=200, verbose_name="Nome do Arquivo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    arquivo = models.FileField(upload_to='propostas/anexos/%Y/%m/', verbose_name="Arquivo")
    tamanho = models.PositiveIntegerField(blank=True, null=True, verbose_name="Tamanho (bytes)")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    enviado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Anexo da Proposta"
        verbose_name_plural = "Anexos das Propostas"
        ordering = ['-enviado_em']
    
    def __str__(self):
        return f"{self.proposta.numero} - {self.nome}"
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        if not self.tamanho:
            return "N/A"
        
        if self.tamanho < 1024:
            return f"{self.tamanho} bytes"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"


class ParcelaProposta(models.Model):
    """
    Modelo para controle detalhado das parcelas da proposta
    """
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='parcelas')
    numero_parcela = models.PositiveIntegerField(verbose_name="Número da Parcela")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor da Parcela")
    descricao = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Descrição",
        help_text="Ex: Entrada, 1ª Parcela, etc."
    )
    
    # Controle de pagamento (para uso futuro)
    pago = models.BooleanField(default=False, verbose_name="Pago")
    data_pagamento = models.DateField(blank=True, null=True, verbose_name="Data do Pagamento")
    valor_pago = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Valor Pago"
    )
    
    class Meta:
        verbose_name = "Parcela da Proposta"
        verbose_name_plural = "Parcelas das Propostas"
        ordering = ['proposta', 'numero_parcela']
        unique_together = ['proposta', 'numero_parcela']
    
    def __str__(self):
        return f"{self.proposta.numero} - Parcela {self.numero_parcela}"
    
    @property
    def esta_vencida(self):
        """Verifica se a parcela está vencida"""
        if self.pago:
            return False
        from datetime import date
        return date.today() > self.data_vencimento
    
    @property
    def dias_para_vencer(self):
        """Retorna quantos dias faltam para vencer"""
        if self.pago:
            return None
        from datetime import date
        delta = self.data_vencimento - date.today()
        return delta.days