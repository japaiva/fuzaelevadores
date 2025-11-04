# core/models/propostas2.py - VERSÃO COMPLETA CORRIGIDA

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from datetime import date, timedelta
from .propostas import Proposta

class VistoriaHistorico(models.Model):
    """
    Histórico de todas as vistorias realizadas na proposta
    ATUALIZADO: Agora inclui campos de medição técnica
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
    
    # Observações e recomendações (para todos os tipos)
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

    alteracoes_realizadas = models.TextField(
        blank=True,
        verbose_name="Alterações Realizadas", 
        help_text="Resumo das alterações feitas durante esta vistoria"
    )
    
    # Data da próxima vistoria (se aplicável)
    proxima_vistoria_sugerida = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Próxima Vistoria Sugerida"
    )
    
    # === CAMPOS DE MEDIÇÃO TÉCNICA ===
    # (Preenchidos apenas quando tipo_vistoria = 'medicao')
    
    # FOSSO
    fosso_altura = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Altura do Fosso (m)",
        help_text="Altura medida do fosso"
    )
    fosso_largura = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Largura do Fosso (m)"
    )
    fosso_profundidade = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Profundidade do Fosso (m)"
    )
    fosso_obs = models.TextField(
        blank=True,
        verbose_name="Observações do Fosso",
        help_text="Condições, problemas ou observações específicas"
    )
    
    # POÇO
    poco_largura = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Largura do Poço (m)"
    )
    poco_profundidade = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Profundidade do Poço (m)"
    )
    poco_obs = models.TextField(
        blank=True,
        verbose_name="Observações do Poço"
    )
    
    # CINTAS
    cintas_largura = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Largura das Cintas (m)"
    )
    cintas_distancia = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Distância entre Cintas (m)"
    )
    cintas_obs = models.TextField(
        blank=True,
        verbose_name="Observações das Cintas"
    )
    
    # CASA DE MÁQUINA
    casa_maquina_altura = models.DecimalField(
        max_digits=8, decimal_places=3, blank=True, null=True,
        verbose_name="Altura Casa de Máquina (m)"
    )
    casa_maquina_gancho = models.BooleanField(
        default=False,
        verbose_name="Gancho Instalado"
    )
    casa_maquina_energia = models.BooleanField(
        default=False,
        verbose_name="Ponto de Energia"
    )
    casa_maquina_obs = models.TextField(
        blank=True,
        verbose_name="Observações Casa de Máquina"
    )
    
    # Fotos e anexos (JSON para flexibilidade)
    fotos_anexos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Fotos e Anexos",
        help_text="Lista de URLs/caminhos para fotos e anexos"
    )

    # Assinatura digital
    assinatura_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="URL da Assinatura",
        help_text="URL da assinatura digital no MinIO"
    )
    assinatura_nome = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nome do Assinante",
        help_text="Nome de quem assinou a vistoria"
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
        return date.today() > self.data_agendada
    
    @property
    def dias_para_vistoria(self):
        """Retorna quantos dias para a vistoria"""
        if self.status_vistoria in ['realizada', 'cancelada']:
            return None
        delta = self.data_agendada - date.today()
        return delta.days
    
    @property
    def eh_medicao(self):
        """Verifica se é uma vistoria de medição"""
        return self.tipo_vistoria == 'medicao'
    
    @property
    def tem_dados_medicao(self):
        """Verifica se tem dados de medição preenchidos"""
        return any([
            self.fosso_altura, self.fosso_largura, self.fosso_profundidade,
            self.poco_largura, self.poco_profundidade,
            self.cintas_largura, self.cintas_distancia,
            self.casa_maquina_altura
        ])
    
    def pode_realizar(self):
        """Verifica se a vistoria pode ser marcada como realizada"""
        return self.status_vistoria == 'agendada'
    
    def pode_cancelar(self):
        """Verifica se a vistoria pode ser cancelada"""
        return self.status_vistoria == 'agendada'
    
    def pode_reagendar(self):
        """Verifica se a vistoria pode ser reagendada"""
        return self.status_vistoria in ['agendada', 'cancelada']


# === MODELO PARA VÃOS DE PORTA POR PAVIMENTO ===

class VaoPortaVistoria(models.Model):
    """
    Medições específicas dos vãos de porta por pavimento
    """
    vistoria = models.ForeignKey(
        VistoriaHistorico,
        on_delete=models.CASCADE,
        related_name='vaos_porta'
    )
    
    pavimento = models.CharField(
        max_length=20,
        verbose_name="Pavimento",
        help_text="Ex: Térreo, 1º Andar, 2º Andar, etc."
    )
    
    largura = models.DecimalField(
        max_digits=8, decimal_places=3,
        verbose_name="Largura do Vão (m)"
    )
    
    altura = models.DecimalField(
        max_digits=8, decimal_places=3,
        verbose_name="Altura do Vão (m)"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Condições específicas deste pavimento"
    )
    
    class Meta:
        verbose_name = "Vão de Porta"
        verbose_name_plural = "Vãos de Porta"
        ordering = ['pavimento']
        unique_together = ['vistoria', 'pavimento']
    
    def __str__(self):
        return f"{self.pavimento} - {self.largura}m x {self.altura}m"


# === FUNÇÃO HELPER PARA CRIAR VÃOS AUTOMATICAMENTE ===

def criar_vaos_porta_automaticos(vistoria, numero_pavimentos):
    """
    Cria vãos de porta baseado no número de pavimentos da proposta
    """
    nomes_pavimentos = [
        "Térreo", "1º Andar", "2º Andar", "3º Andar", "4º Andar",
        "5º Andar", "6º Andar", "7º Andar", "8º Andar", "9º Andar", "10º Andar"
    ]
    
    for i in range(numero_pavimentos):
        nome = nomes_pavimentos[i] if i < len(nomes_pavimentos) else f"{i+1}º Andar"
        
        VaoPortaVistoria.objects.get_or_create(
            vistoria=vistoria,
            pavimento=nome,
            defaults={
                'largura': 0.80,  # Valor padrão
                'altura': 2.10,   # Valor padrão
                'observacoes': ''
            }
        )


# =============================================================================
# FUNÇÃO PARA ATUALIZAR STATUS DA OBRA (mantida do código original)
# =============================================================================

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
        return date.today() > self.data_vencimento
    
    @property
    def dias_para_vencer(self):
        """Retorna quantos dias faltam para vencer"""
        if self.pago:
            return None
        delta = self.data_vencimento - date.today()
        return delta.days