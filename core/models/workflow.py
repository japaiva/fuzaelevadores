# core/models/workflow.py

"""
Sistema de Workflow e Notificações
Gerencia tarefas automáticas geradas por eventos do sistema
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group


class Tarefa(models.Model):
    """
    Representa uma tarefa/notificação no sistema de workflow

    Exemplo de uso:
    - Proposta aprovada → gera tarefa para engenharia enviar projeto executivo
    - Requisição criada → gera tarefa para compras criar orçamentos
    - Lista de materiais aprovada → gera tarefa para produção iniciar fabricação
    """

    TIPO_CHOICES = [
        ('projeto_executivo', 'Enviar Projeto Executivo'),
        ('criar_lista_materiais', 'Criar Lista de Materiais'),
        ('criar_orcamentos', 'Criar Orçamentos de Compra'),
        ('aprovar_orcamentos', 'Aprovar Orçamentos'),
        ('iniciar_producao', 'Iniciar Produção'),
        ('agendar_instalacao', 'Agendar Instalação'),
        ('outro', 'Outra Tarefa'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    # Identificação da tarefa
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name='Tipo da Tarefa'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Descrição curta da tarefa'
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição',
        help_text='Detalhes adicionais sobre a tarefa'
    )

    # Relacionamentos
    proposta = models.ForeignKey(
        'core.Proposta',
        on_delete=models.CASCADE,
        related_name='tarefas',
        null=True,
        blank=True,
        verbose_name='Proposta Relacionada'
    )

    requisicao = models.ForeignKey(
        'core.RequisicaoCompra',
        on_delete=models.CASCADE,
        related_name='tarefas',
        null=True,
        blank=True,
        verbose_name='Requisição Relacionada'
    )

    lista_materiais = models.ForeignKey(
        'core.ListaMateriais',
        on_delete=models.CASCADE,
        related_name='tarefas',
        null=True,
        blank=True,
        verbose_name='Lista de Materiais Relacionada'
    )

    # Destinatários (quem deve fazer a tarefa)
    # Sistema simplificado: usa nivel_destino ao invés de grupo
    nivel_destino = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Nível Responsável',
        help_text='Nível que deve executar a tarefa (ex: engenharia, compras)',
        choices=[
            ('admin', 'Admin'),
            ('gestor', 'Gestor'),
            ('vendedor', 'Vendedor'),
            ('compras', 'Compras'),
            ('engenharia', 'Engenharia'),
            ('financeiro', 'Financeiro'),
            ('vistoria', 'Vistoria'),
            ('producao', 'Produção'),
            ('almoxarifado', 'Almoxarifado'),
        ]
    )

    # DEPRECATED: grupo_destino será removido
    grupo_destino = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas',
        verbose_name='Grupo Responsável (DEPRECATED)',
        help_text='DEPRECATED - Use nivel_destino'
    )

    usuario_destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_atribuidas',
        verbose_name='Usuário Responsável',
        help_text='Usuário específico responsável (opcional)'
    )

    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )

    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default='normal',
        verbose_name='Prioridade'
    )

    # Datas
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    data_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Início',
        help_text='Quando a tarefa foi iniciada'
    )

    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão'
    )

    prazo = models.DateField(
        null=True,
        blank=True,
        verbose_name='Prazo',
        help_text='Data limite para conclusão'
    )

    # Rastreamento
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_criadas',
        verbose_name='Criada Por',
        help_text='Usuário que criou a tarefa (ou sistema)'
    )

    concluida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_concluidas',
        verbose_name='Concluída Por'
    )

    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações',
        help_text='Notas sobre a conclusão da tarefa'
    )

    class Meta:
        db_table = 'workflow_tarefas'
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['status', 'nivel_destino']),
            models.Index(fields=['status', 'usuario_destino']),
            models.Index(fields=['proposta', 'status']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo} ({self.get_status_display()})"

    @property
    def esta_atrasada(self):
        """Verifica se a tarefa está atrasada"""
        if self.prazo and self.status in ['pendente', 'em_andamento']:
            from django.utils import timezone
            return timezone.now().date() > self.prazo
        return False

    @property
    def dias_em_aberto(self):
        """Retorna quantos dias a tarefa está em aberto"""
        from django.utils import timezone
        if self.status in ['pendente', 'em_andamento']:
            return (timezone.now() - self.data_criacao).days
        return None

    def iniciar(self, usuario):
        """Marca a tarefa como em andamento"""
        from django.utils import timezone
        self.status = 'em_andamento'
        self.data_inicio = timezone.now()
        if not self.usuario_destino:
            self.usuario_destino = usuario
        self.save()

    def concluir(self, usuario, observacoes=None):
        """Marca a tarefa como concluída"""
        from django.utils import timezone
        self.status = 'concluida'
        self.data_conclusao = timezone.now()
        self.concluida_por = usuario
        if observacoes:
            self.observacoes = observacoes
        self.save()

    def cancelar(self, usuario, motivo=None):
        """Cancela a tarefa"""
        from django.utils import timezone
        self.status = 'cancelada'
        self.data_conclusao = timezone.now()
        self.concluida_por = usuario
        if motivo:
            self.observacoes = f"Cancelada: {motivo}"
        self.save()


class HistoricoTarefa(models.Model):
    """
    Registro de mudanças nas tarefas para auditoria
    """
    tarefa = models.ForeignKey(
        Tarefa,
        on_delete=models.CASCADE,
        related_name='historico',
        verbose_name='Tarefa'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )

    acao = models.CharField(
        max_length=50,
        verbose_name='Ação',
        help_text='criada, iniciada, concluida, cancelada, atribuida'
    )

    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Detalhes da ação realizada'
    )

    data = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data'
    )

    class Meta:
        db_table = 'workflow_historico_tarefas'
        verbose_name = 'Histórico de Tarefa'
        verbose_name_plural = 'Histórico de Tarefas'
        ordering = ['-data']

    def __str__(self):
        return f"{self.tarefa} - {self.acao} por {self.usuario} em {self.data}"
