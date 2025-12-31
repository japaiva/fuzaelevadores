# core/models/propostas.py

from django.db import models
from django.conf import settings
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
import uuid

import logging
logger = logging.getLogger(__name__)

class Proposta(models.Model):

    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('vista', 'À Vista'),
        ('parcelado', 'Parcelado'),
        ('entrada_parcelas', 'Entrada + Parcelas'),
        ('financiamento', 'Financiamento'),
        ('leasing', 'Leasing'),
    ]

    TIPO_PARCELA_CHOICES = [
        ('mensal', 'Mensal'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('personalizado', 'Personalizado'),
    ]

    STATUS_OBRA_CHOICES = [
        ('', 'Aguardando Medição'),
        ('medicao_ok', 'Medição OK'),
        ('em_vistoria', 'Em Vistoria'),
        ('obra_ok', 'Obra OK'),
    ]

    # === IDENTIFICAÇÃO E STATUS ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=8, unique=True, verbose_name="Número da Proposta")

    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='propostas_atualizadas',
        blank=True, 
        null=True
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    status_obra = models.CharField(
        max_length=20, 
        choices=STATUS_OBRA_CHOICES, 
        blank=True,
        verbose_name="Status da Obra",
        help_text="Status do acompanhamento da obra civil"
    )
    
    data_vistoria_medicao = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Data da Vistoria/Medição",
        help_text="Data da primeira vistoria para medição"
    )
    
    data_proxima_vistoria = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Data da Próxima Vistoria",
        help_text="Data agendada para próxima vistoria"
    )

    data_aprovacao = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Data de Aprovação",
        help_text="Data e hora quando a proposta foi aprovada"
    )

    # === ETAPA 1 - CLIENTE/ELEVADOR ===
    # CLIENTE
    cliente = models.ForeignKey('Cliente', on_delete=models.PROTECT, verbose_name="Cliente")
    nome_projeto = models.CharField(max_length=200, verbose_name="Nome do Projeto")
    
    # Faturamento
    faturado_por = models.CharField(
        max_length=20,
        choices=[
            ('Elevadores', 'Elevadores'),
            ('Fuza', 'Fuza'),
            ('Manutenção', 'Manutenção'),
        ],
        default='Elevadores',
        verbose_name="Faturado por"
    )

    # Normas ABNT
    normas_abnt = models.CharField(
        max_length=20,
        choices=[
            ('NBR 16858', 'NBR 16858 - 2024'),
            ('NBR 16042', 'NBR 16042 - 2020'),
        ],
        default='NBR 16858',
        verbose_name="Normas ABNT",
        help_text="Norma técnica aplicável ao elevador"
    )

    local_instalacao = models.TextField(blank=True)

    # ELEVADOR
    # Modelo e Capacidade
    modelo_elevador = models.CharField(
        max_length=50, 
        choices=[
            ('Passageiro', 'Passageiro'),
            ('Carga', 'Carga'), 
            ('Monta Prato', 'Monta Prato'),
            ('Plataforma Acessibilidade', 'Plataforma Acessibilidade'),
        ],
        verbose_name="Modelo do Elevador"
    )
    capacidade = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Capacidade (kg)"
    )
    capacidade_pessoas = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name="Capacidade (pessoas)"
    )
    
    # Acionamento e Tração
    acionamento = models.CharField(
        max_length=20,
        choices=[
            ('Motor', 'Motor'),
            ('Hidraulico', 'Hidráulico'),
            ('Carretel', 'Carretel'),
        ],
        verbose_name="Acionamento"
    )
    tracao = models.CharField(
        max_length=10,
        choices=[('1x1', '1x1'), ('2x1', '2x1')],
        blank=True, null=True,
        verbose_name="Tração"
    )


    # NOVO CAMPO: Tipo Motor (condicional para acionamento Motor)
    tipo_motor = models.CharField(
        max_length=20,
        choices=[
            ('com_engrenagem', 'Com Engrenagem'),
            ('sem_engrenagem', 'Sem Engrenagem'),
        ],
        blank=True, null=True,
        verbose_name="Tipo Motor",
        help_text="Aplicável apenas para acionamento tipo Motor"
    )

# No modelo Proposta, adicionar após o campo 'saida_cabine':

    # Abertura da Cabine (direção de abertura da porta)
    abertura_cabine = models.CharField(
        max_length=10,
        choices=[
            ('direita', 'Direita'),
            ('esquerda', 'Esquerda'),
            ('central', 'Central'),
        ],
        default='direita',
        verbose_name="Abertura da Cabine"
    )



    contrapeso = models.CharField(
        max_length=20,
        choices=[('Traseiro', 'Traseiro'), ('Lateral', 'Lateral')],
        blank=True, null=True,
        verbose_name="Contrapeso"
    )
    
    largura_poco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Largura do Poço (m)"
    )
    comprimento_poco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Comprimento do Poço (m)"
    )
    altura_poco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Altura do Poço (m)"
    )
    pavimentos = models.IntegerField(verbose_name="Número de Pavimentos")

    # === ETAPA 2 - CABINE/PORTAS ===
    # CABINE

    material_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Inox 430', 'Inox 430'),
            ('Inox 304', 'Inox 304'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
        ],
        null=True, blank=True,
        verbose_name="Material da Cabine"
    )
    
    espessura_cabine = models.CharField(
        max_length=10,
        choices=[('1,2', '1,2 mm'), ('1,5', '1,5 mm'), ('2,0', '2,0 mm')],
        null=True, blank=True,
        verbose_name="Espessura"
    )
    saida_cabine = models.CharField(
        max_length=20,
        choices=[('Padrão', 'Padrão'), ('Oposta', 'Oposta')],
        null=True, blank=True,
        verbose_name="Saída"
    )
    altura_cabine = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Altura da Cabine (m)"
    )
    
    # Piso da Cabine
    piso_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Por conta do cliente', 'Por conta do cliente'),
            ('Por conta da empresa', 'Por conta da empresa'),
        ],
        null=True, blank=True,
        verbose_name="Piso"
    )
    material_piso_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Antiderrapante', 'Antiderrapante'),
        ],
        blank=True,
        verbose_name="Material do Piso"
    )

    # Porta da Cabine
    modelo_porta_cabine = models.CharField(
        max_length=20,
        choices=[
            ('Automática', 'Automática'),
            ('Pantográfica', 'Pantográfica'),
            ('Pivotante', 'Pivotante'),
            ('Guilhotina', 'Guilhotina'),
            ('Camarão', 'Camarão'),
            ('Cancela', 'Cancela'),
            ('Rampa', 'Rampa'),
        ],
        null=True, blank=True,
        verbose_name="Modelo Porta Cabine"
    )

    material_porta_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Inox 430', 'Inox 430'),
            ('Inox 304', 'Inox 304'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
        ],
        null=True, blank=True,
        verbose_name="Material Porta Cabine"
    )

    folhas_porta_cabine = models.CharField(
        max_length=10,
        choices=[('2', '2'), ('3', '3'), ('4', '4')],
        blank=True,
        verbose_name="Folhas Porta Cabine"
    )
    largura_porta_cabine = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Largura Porta Cabine (m)"
    )
    altura_porta_cabine = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Altura Porta Cabine (m)"
    )
    
    # Porta do Pavimento
    modelo_porta_pavimento = models.CharField(
        max_length=20,
        choices=[
            ('Automática', 'Automática'),
            ('Pantográfica', 'Pantográfica'),
            ('Pivotante', 'Pivotante'),
            ('Guilhotina', 'Guilhotina'),
            ('Camarão', 'Camarão'),
            ('Cancela', 'Cancela'),
            ('Rampa', 'Rampa'),
        ],
        null=True, blank=True,
        verbose_name="Modelo Porta Pavimento"
    )

    material_porta_pavimento = models.CharField(
        max_length=50,
        choices=[
            ('Inox 430', 'Inox 430'),
            ('Inox 304', 'Inox 304'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
        ],
        null=True, blank=True,
        verbose_name="Material Porta Pavimento"
    )

    folhas_porta_pavimento = models.CharField(
        max_length=10,
        choices=[('2', '2'), ('3', '3'), ('4', '4')],
        blank=True,
        verbose_name="Folhas Porta Pavimento"
    )
    largura_porta_pavimento = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Largura Porta Pavimento (m)"
    )
    altura_porta_pavimento = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Altura Porta Pavimento (m)"
    )

    # === ETAPA 3 - RESUMO/COMERCIAL ===
    # RESUMO
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='propostas_vendedor',
        verbose_name="Vendedor",
        null=True, blank=True,
        limit_choices_to={'nivel': 'vendedor'}
    )

    numero_contrato = models.CharField(max_length=20, blank=True, null=True)
    data_contrato = models.DateField(blank=True, null=True)

    documentacao_prefeitura = models.CharField(
        max_length=20,
        choices=[
            ('cliente', 'Por conta do cliente'),
            ('empresa', 'Por conta da empresa'),
        ],
        default='cliente',
        verbose_name="Documentação Prefeitura"
    )
    
    # DADOS COMERCIAIS
    valor_proposta = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name="Valor da Proposta",
        help_text="Valor final negociado com o cliente"
    )
    
    # Validade e Vencimento
    data_validade = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Validade da Proposta",
        help_text="Data até quando a proposta é válida"
    )

    previsao_conclusao_obra = models.DateField(
        blank=True,
        null=True,
        verbose_name="Previsão Conclusão da Obra",
        help_text="Data prevista para conclusão da obra civil"
    )

    prazo_entrega_dias = models.PositiveIntegerField(
        default=45,
        verbose_name="Prazo de Entrega (dias)",
        help_text="Prazo em dias corridos para entrega após aprovação"
    )
    
    # Forma de Pagamento
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        default='parcelado',
        verbose_name="Forma de Pagamento"
    )
    
    # Entrada (quando aplicável)
    valor_entrada = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor da Entrada"
    )
    percentual_entrada = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Percentual da Entrada (%)"
    )
    data_vencimento_entrada = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Vencimento da Entrada"
    )
    
    # Parcelamento
    numero_parcelas = models.PositiveIntegerField(
        default=1,
        verbose_name="Número de Parcelas"
    )
    valor_parcela = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor da Parcela"
    )
    tipo_parcela = models.CharField(
        max_length=15,
        choices=TIPO_PARCELA_CHOICES,
        default='mensal',
        verbose_name="Tipo de Parcela"
    )
    primeira_parcela = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Vencimento da 1ª Parcela"
    )
       
    # === DIMENSÕES CALCULADAS ===
    largura_cabine_calculada = models.DecimalField(
        max_digits=8, 
        decimal_places=3, 
        blank=True, 
        null=True,
        verbose_name="Largura Cabine Calculada (m)"
    )
    comprimento_cabine_calculado = models.DecimalField(
        max_digits=8, 
        decimal_places=3, 
        blank=True, 
        null=True,
        verbose_name="Comprimento Cabine Calculado (m)"
    )
    capacidade_cabine_calculada = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Capacidade Cabine Calculada (kg)"
    )
    tracao_cabine_calculada = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Tração Cabine Calculada (kg)"
    )
    
    # =================================================================
    # CUSTOS DETALHADOS (Estrutura Contábil Correta)
    # =================================================================
    
    custo_materiais = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custo de Materiais",
        help_text="Materiais diretos (cabine + carrinho + tração + sistemas)"
    )
    
    custo_mao_obra = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custo de Mão de Obra Produção",
        help_text="15% dos materiais - MOD para fabricação"
    )
    
    custo_indiretos_fabricacao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custos Indiretos de Fabricação",
        help_text="5% dos materiais - energia, depreciação, etc."
    )
    
    custo_instalacao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custo de Instalação",
        help_text="5% dos materiais - serviços no cliente"
    )
    
    # =================================================================
    # TOTAIS DE CUSTO
    # =================================================================
    
    custo_producao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custo de Produção",
        help_text="Materiais + MOD + Custos Indiretos (SEM instalação)"
    )
    
    custo_total_projeto = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custo Total do Projeto",
        help_text="Custo de Produção + Custo de Instalação"
    )
    
    # =================================================================
    # FORMAÇÃO DE PREÇO
    # =================================================================
    
    margem_lucro = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Margem de Lucro",
        help_text="30% sobre custo total do projeto"
    )
    
    preco_com_margem = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Preço com Margem",
        help_text="Custo Total + Margem de Lucro"
    )
    
    comissao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Comissão",
        help_text="3% sobre preço com margem"
    )
    
    preco_com_comissao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Preço com Comissão",
        help_text="Preço com Margem + Comissão"
    )
    
    impostos = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Impostos",
        help_text="10% sobre preço com comissão"
    )
    
    # =================================================================
    # PREÇOS FINAIS
    # =================================================================
    
    preco_venda_calculado = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Preço de Venda Calculado",
        help_text="Preço sugerido pelo sistema (com todos os componentes)"
    )
    
    percentual_desconto = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Desconto Aplicado (%)",
        help_text="Percentual de desconto sobre o preço calculado"
    )

    # === DADOS DETALHADOS (JSON) ===
    ficha_tecnica = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Ficha Técnica"
    )
    componentes_calculados = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Componentes Calculados"
    )
    dimensionamento_detalhado = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Dimensionamento Detalhado"
    )
    explicacao_calculo = models.TextField(
        blank=True, 
        verbose_name="Explicação do Cálculo"
    )
    custos_detalhados = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Custos Detalhados"
    )
    formacao_preco = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Formação de Preço"
    )

    # === ARQUIVOS DE PROJETO ===
    arquivo_projeto_executivo = models.FileField(
        upload_to='projetos/executivos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Arquivo Projeto Executivo",
        help_text="PDF do projeto executivo"
    )
    data_upload_projeto_executivo = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data Upload Projeto Executivo",
        help_text="Data e hora do upload do projeto executivo"
    )

    arquivo_projeto_elevador = models.FileField(
        upload_to='projetos/elevadores/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Arquivo Projeto Elevador",
        help_text="PDF do projeto do elevador"
    )
    data_upload_projeto_elevador = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data Upload Projeto Elevador",
        help_text="Data e hora do upload do projeto do elevador"
    )

    # === CICLO DE VIDA DO PROJETO ===
    data_entrega_obra = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Entrega Obra",
        help_text="Data efetiva da entrega da obra civil"
    )

    data_autorizacao_producao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Autorização Produção",
        help_text="Data de autorização para iniciar produção"
    )

    data_compra = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Compra",
        help_text="Data de realização das compras de materiais"
    )

    data_inicio_producao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Início Produção",
        help_text="Data efetiva de início da produção"
    )

    data_previsao_conclusao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Previsão Conclusão",
        help_text="Data prevista para conclusão da produção"
    )

    data_conclusao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Conclusão",
        help_text="Data efetiva de conclusão da produção"
    )

    data_previsao_entrega = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Previsão Entrega",
        help_text="Data prevista para entrega ao cliente"
    )

    data_entrega = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Entrega",
        help_text="Data efetiva de entrega ao cliente"
    )

    # === LIBERAÇÃO PRODUÇÃO (FINANCEIRO) ===
    STATUS_FINANCEIRO_CHOICES = [
        ('', 'Pendente'),
        ('liberado', 'Liberado'),
    ]

    status_financeiro = models.CharField(
        max_length=20,
        choices=STATUS_FINANCEIRO_CHOICES,
        blank=True,
        default='',
        verbose_name="Status Financeiro",
        help_text="Status de liberação financeira para produção"
    )

    # === STATUS PRODUÇÃO ===
    STATUS_PRODUCAO_CHOICES = [
        ('', 'Aguardando'),
        ('em_producao', 'Em Produção'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    status_producao = models.CharField(
        max_length=20,
        choices=STATUS_PRODUCAO_CHOICES,
        blank=True,
        default='',
        verbose_name="Status Produção",
        help_text="Status do projeto na produção"
    )
    numero_op = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número OP",
        help_text="Número da Ordem de Produção"
    )
    data_liberacao_producao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data Liberação Produção",
        help_text="Data de liberação para produção pelo financeiro"
    )

    # === AUDITORIA ===
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['vendedor', 'status']),
            models.Index(fields=['cliente']),
            models.Index(fields=['-criado_em']),
            models.Index(fields=['status']),
            models.Index(fields=['data_validade']),
            models.Index(fields=['valor_proposta']),
        ]
        permissions = [
            # Permissões de desconto
            ("aprovar_desconto_5", "Pode aprovar desconto até 5%"),
            ("aprovar_desconto_10", "Pode aprovar desconto até 10%"),
            ("aprovar_desconto_15", "Pode aprovar desconto até 15%"),
            ("aprovar_desconto_20", "Pode aprovar desconto até 20%"),
            ("aprovar_desconto_ilimitado", "Pode aprovar desconto ilimitado"),

            # Permissões de visualização
            ("visualizar_custos", "Pode visualizar custos e margens"),
            ("visualizar_todas_propostas", "Pode visualizar propostas de outros vendedores"),
            ("exportar_relatorios", "Pode exportar relatórios"),

            # Permissões de edição
            ("editar_proposta_alheia", "Pode editar propostas de outros vendedores"),
            ("aprovar_proposta", "Pode aprovar propostas"),
            ("rejeitar_proposta", "Pode rejeitar propostas"),

            # Permissões de vistoria
            ("realizar_vistoria", "Pode realizar vistorias"),
            ("agendar_vistoria", "Pode agendar vistorias"),
            ("aprovar_medicao", "Pode aprovar medições de obra"),
        ]
    
    def __str__(self):
        valor_display = f"R$ {self.valor_proposta:,.2f}" if self.valor_proposta else "Valor não definido"
        return f"{self.numero} - {self.nome_projeto} - {valor_display}"
    
    def save(self, *args, **kwargs):
        """
        Salvar com número automático formato 25.00001, definir data de validade
        e ATUALIZAR automaticamente data_proxima_vistoria baseada em data_vistoria_medicao
        """
        # Verificar se há instância anterior para comparar mudanças
        instancia_anterior = None
        if self.pk:
            try:
                instancia_anterior = Proposta.objects.get(pk=self.pk)
            except Proposta.DoesNotExist:
                pass
        
        # Gerar número automático se novo
        if not self.numero:
            from datetime import datetime
            
            ano_atual = datetime.now().year
            ano_dois_digitos = str(ano_atual)[-2:]
            
            ultimo_pedido = Proposta.objects.filter(
                numero__startswith=f'{ano_dois_digitos}.'
            ).order_by('-numero').first()
            
            if ultimo_pedido:
                try:
                    numero_parte = ultimo_pedido.numero.split('.')[1]
                    ultimo_numero = int(numero_parte)
                    novo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    novo_numero = 1
            else:
                novo_numero = 1
            
            self.numero = f'{ano_dois_digitos}.{novo_numero:05d}'
        
        # Definir data de validade padrão se não informada
        if not self.data_validade:
            self.data_validade = date.today() + timedelta(days=30)

        if instancia_anterior and instancia_anterior.status != 'aprovado' and self.status == 'aprovado':
            self.data_aprovacao = timezone.now()

        # ✅ NOVA FUNCIONALIDADE: Auto-update de próxima vistoria
        if self.data_vistoria_medicao:
            # Verificar se data_vistoria_medicao mudou ou é uma nova proposta
            data_medicao_mudou = (
                instancia_anterior is None or  # Nova proposta
                instancia_anterior.data_vistoria_medicao != self.data_vistoria_medicao  # Data mudou
            )
            
            if data_medicao_mudou:
                # Calcular próxima vistoria baseada na data de medição
                # Padrão: 15 dias após a medição
                proxima_vistoria = self.data_vistoria_medicao
                
                # Só atualizar se ainda não foi definida manualmente ou se a medição mudou
                if not self.data_proxima_vistoria or data_medicao_mudou:
                    self.data_proxima_vistoria = proxima_vistoria
                    
                    # Log da atualização automática
                    logger.info(
                        f"Proposta {self.numero}: data_proxima_vistoria atualizada automaticamente "
                        f"para {proxima_vistoria.strftime('%d/%m/%Y')} "
                        f"(15 dias após medição de {self.data_vistoria_medicao.strftime('%d/%m/%Y')})"
                    )

        # Se valor_proposta não foi definido pelo usuário, usar o calculado como base
        if self.preco_venda_calculado and self.valor_proposta is None:
            self.valor_proposta = self.preco_venda_calculado

        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Override do método delete para garantir limpeza completa
        """
        try:
            # Log detalhado antes da exclusão
            logger.info(f"Iniciando exclusão da proposta {self.numero}")
            
            # Contar relacionamentos que serão excluídos
            from core.models import PortaPavimento, HistoricoProposta, AnexoProposta
            
            portas_count = PortaPavimento.objects.filter(proposta=self).count()
            historico_count = HistoricoProposta.objects.filter(proposta=self).count()
            anexos_count = AnexoProposta.objects.filter(proposta=self).count()
            
            # Log dos relacionamentos
            if portas_count > 0:
                logger.info(f"Serão excluídas {portas_count} portas individuais")
            if historico_count > 0:
                logger.info(f"Serão excluídos {historico_count} registros de histórico")
            if anexos_count > 0:
                logger.info(f"Serão excluídos {anexos_count} anexos")
            
            # Exclusão manual das portas (garantir que aconteça)
            PortaPavimento.objects.filter(proposta=self).delete()
            
            # Chamar delete padrão (que já cuida do cascata automático)
            super().delete(*args, **kwargs)
            
            logger.info(f"Proposta {self.numero} excluída com sucesso")
            
        except Exception as e:
            logger.error(f"Erro na exclusão da proposta {self.numero}: {str(e)}")
            raise  # Re-raise para que o erro seja tratado pela view
    
    def calcular_impostos_dinamicos(self, base_calculo=None):
        """
        Calcula impostos baseado no campo 'faturado_por' e parâmetros do sistema
        """
        from core.models import ParametrosGerais
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        
        valor_base = base_calculo or self.preco_com_comissao
        
        if not valor_base:
            logger.warning(f"Proposta {self.numero}: Sem base para cálculo de impostos")
            return Decimal('0.00')
        
        try:
            parametros = ParametrosGerais.objects.first()
            if not parametros:
                return Decimal(str(valor_base)) * Decimal('0.10')
            
            percentual_impostos = None
            
            if self.faturado_por == 'Elevadores':
                percentual_impostos = parametros.faturamento_elevadores
            elif self.faturado_por == 'Fuza':
                percentual_impostos = parametros.faturamento_fuza
            elif self.faturado_por == 'Manutenção':
                percentual_impostos = parametros.faturamento_manutencao
            
            if percentual_impostos and percentual_impostos > 0:
                percentual_decimal = Decimal(str(percentual_impostos)) / Decimal('100')
                return Decimal(str(valor_base)) * percentual_decimal
            else:
                return Decimal(str(valor_base)) * Decimal('0.10')
                
        except Exception as e:
            logger.error(f"Erro no cálculo de impostos para proposta {self.numero}: {e}")
            return Decimal(str(valor_base)) * Decimal('0.10')

    def calcular_precos_completo(self):
        """
        Recalcula toda a formação de preço com impostos dinâmicos
        """
        if not self.custo_total_projeto:
            return False
        
        # 1. Margem de Lucro (30%)
        self.margem_lucro = self.custo_total_projeto * Decimal('0.30')
        self.preco_com_margem = self.custo_total_projeto + self.margem_lucro
        
        # 2. Comissão (3%)
        self.comissao = self.preco_com_margem * Decimal('0.03')
        self.preco_com_comissao = self.preco_com_margem + self.comissao
        
        # 3. Impostos (DINÂMICO baseado em faturado_por)
        self.impostos = self.calcular_impostos_dinamicos()
        self.preco_venda_calculado = self.preco_com_comissao + self.impostos
        
        # 4. Se não há valor negociado, usar o calculado
        if not self.valor_proposta:
            self.valor_proposta = self.preco_venda_calculado
        
        return True

    # =================================================================
    # PROPRIEDADES CALCULADAS
    # =================================================================

    @property
    def velocidade_calculada(self):
        """Calcula velocidade baseada no modelo e capacidade"""
        if self.modelo_elevador == 'Passageiro':
            if self.capacidade <= 320:
                return "0.5"
            elif self.capacidade <= 630:
                return "0.63"
            else:
                return "1.0"
        return "0.5"

    @property
    def potencia_motor_calculada(self):
        """Calcula potência do motor baseada na capacidade"""
        if self.capacidade <= 320:
            return 20.0
        elif self.capacidade <= 630:
            return 25.0
        elif self.capacidade <= 1000:
            return 30.0
        else:
            return 40.0

    @property
    def lucro_bruto(self):
        """Lucro bruto: valor proposta - custo total"""
        if self.valor_proposta and self.custo_total_projeto:
            return self.valor_proposta - self.custo_total_projeto
        return Decimal('0')
    
    @property
    def margem_real_percentual(self):
        """Margem real sobre custo total"""
        if self.lucro_bruto and self.custo_total_projeto and self.custo_total_projeto > 0:
            return (self.lucro_bruto / self.custo_total_projeto) * 100
        return Decimal('0')
    
    @property
    def economia_cliente(self):
        """Economia do cliente em relação ao preço calculado"""
        if self.preco_venda_calculado and self.valor_proposta:
            return self.preco_venda_calculado - self.valor_proposta
        return Decimal('0')

    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        badges = {
            'rascunho': 'bg-warning',
            'simulado': 'bg-info',
            'pendente': 'bg-info',
            'aprovado': 'bg-success',
            'rejeitado': 'bg-danger',
        }
        return badges.get(self.status, 'bg-secondary')
    
    @property
    def pode_editar(self):
        """Verifica se a proposta ainda pode ser editada"""
        return self.status in ['rascunho', 'simulado', 'pendente']
    
    @property
    def pode_excluir(self):
        """Verifica se a proposta pode ser excluída"""
        return self.status in ['rascunho', 'simulado', 'pendente']
    
    @property
    def esta_vencida(self):
        """Verifica se a proposta está vencida"""
        if not self.data_validade:
            return False
        return date.today() > self.data_validade
    
    @property
    def dias_para_vencer(self):
        """Retorna quantos dias faltam para vencer"""
        if not self.data_validade:
            return None
        delta = self.data_validade - date.today()
        return delta.days
    
    def calcular_parcelas(self):
        """Calcula as datas de vencimento das parcelas"""
        if not self.primeira_parcela or not self.numero_parcelas:
            return []
        
        from dateutil.relativedelta import relativedelta
        
        parcelas = []
        data_atual = self.primeira_parcela
        
        incrementos = {
            'mensal': relativedelta(months=1),
            'bimestral': relativedelta(months=2),
            'trimestral': relativedelta(months=3),
            'semestral': relativedelta(months=6),
            'anual': relativedelta(years=1),
            'personalizado': relativedelta(months=1),
        }
        
        incremento = incrementos.get(self.tipo_parcela, relativedelta(months=1))
        
        for i in range(self.numero_parcelas):
            parcelas.append({
                'numero': i + 1,
                'vencimento': data_atual,
                'valor': self.valor_parcela or 0
            })
            data_atual += incremento
        
        return parcelas
    
    def calcular_totais_pagamento(self):
        """Calcula os totais do plano de pagamento"""
        entrada = self.valor_entrada or 0
        parcelas = (self.valor_parcela or 0) * (self.numero_parcelas or 0)
        total = entrada + parcelas
        
        return {
            'valor_entrada': entrada,
            'total_parcelas': parcelas,
            'total_geral': total,
            'numero_parcelas': self.numero_parcelas or 0
        }
    
    # === MÉTODOS DE DISPLAY ===
    
    def get_modelo_elevador_display(self):
        """Display personalizado para modelo do elevador"""
        choices = {
            'Passageiro': 'Elevador de Passageiro',
            'Carga': 'Elevador de Carga', 
            'Monta Prato': 'Monta Prato',
            'Plataforma Acessibilidade': 'Plataforma de Acessibilidade',
        }
        return choices.get(self.modelo_elevador, self.modelo_elevador)
    
    def get_forma_pagamento_display_detalhado(self):
        """Display detalhado da forma de pagamento"""
        if self.forma_pagamento == 'vista':
            return "À Vista"
        elif self.forma_pagamento == 'parcelado':
            return f"Parcelado em {self.numero_parcelas}x"
        elif self.forma_pagamento == 'entrada_parcelas':
            return f"Entrada + {self.numero_parcelas}x"
        else:
            return self.get_forma_pagamento_display()
    
    # === PROPRIEDADES CALCULADAS ===
    
    @property
    def area_poco(self):
        """Calcula área do poço"""
        if self.largura_poco and self.comprimento_poco:
            return float(self.largura_poco) * float(self.comprimento_poco)
        return 0
    
    @property
    def volume_poco(self):
        """Calcula volume do poço"""
        if self.area_poco and self.altura_poco:
            return self.area_poco * float(self.altura_poco)
        return 0
    
    @property
    def area_cabine_calculada(self):
        """Calcula área da cabine"""
        if self.largura_cabine_calculada and self.comprimento_cabine_calculado:
            return float(self.largura_cabine_calculada) * float(self.comprimento_cabine_calculado)
        return 0
    
    @property
    def tem_calculos(self):
        """Verifica se a proposta tem cálculos executados"""
        return bool(self.dimensionamento_detalhado or self.ficha_tecnica or self.custo_producao)
    
    @property
    def tem_precos(self):
        """Verifica se a proposta tem preços calculados"""
        return bool(self.formacao_preco or self.preco_venda_calculado or self.valor_proposta)
    
    @property
    def resumo_elevador(self):
        """Retorna um resumo das características do elevador"""
        resumo = [
            f"Modelo: {self.get_modelo_elevador_display()}",
            f"Capacidade: {self.capacidade} kg",
            f"Acionamento: {self.get_acionamento_display()}",
        ]
        
        if self.largura_cabine_calculada and self.comprimento_cabine_calculado:
            resumo.append(
                f"Cabine: {self.largura_cabine_calculada:.2f}m x "
                f"{self.comprimento_cabine_calculado:.2f}m x "
                f"{self.altura_cabine:.2f}m"
            )
        
        return " | ".join(resumo)
    

    @property
    def pode_agendar_vistoria(self):
        """Verifica se a proposta pode ter vistoria agendada"""
        return self.status == 'aprovado'
    
    @property
    def status_obra_badge_class(self):
        """Retorna classe CSS para badge de status da obra"""
        badges = {
            '': 'bg-secondary',
            'medicao_ok': 'bg-success',
            'em_vistoria': 'bg-warning',
            'obra_ok': 'bg-primary',
        }
        return badges.get(self.status_obra, 'bg-secondary')
    
    @property
    def proxima_vistoria_vencida(self):
        """Verifica se a próxima vistoria está vencida"""
        if not self.data_proxima_vistoria:
            return False
        return date.today() > self.data_proxima_vistoria
    
    @property
    def dias_proxima_vistoria(self):
        """Retorna quantos dias para a próxima vistoria"""
        if not self.data_proxima_vistoria:
            return None
        delta = self.data_proxima_vistoria - date.today()
        return delta.days

    
    @property
    def percentual_conclusao(self):
        """Calcula percentual de conclusão da proposta"""
        campos_obrigatorios = [
            self.cliente_id,
            self.valor_proposta,
            self.modelo_elevador,
            self.capacidade,
            self.acionamento,
            self.largura_poco,
            self.comprimento_poco,
            self.altura_poco,
            self.pavimentos,
            self.modelo_porta_cabine,
            self.material_porta_cabine,
            self.modelo_porta_pavimento,
            self.material_porta_pavimento,
            self.material_cabine,
            self.espessura_cabine,
            self.altura_cabine,
        ]
        
        preenchidos = sum(1 for campo in campos_obrigatorios if campo)
        return int((preenchidos / len(campos_obrigatorios)) * 100)
    
    def pode_calcular(self):
        """Verifica se a proposta pode ser calculada"""
        campos_obrigatorios = [
            self.cliente_id,
            self.modelo_elevador,
            self.capacidade,
            self.acionamento,
            self.largura_poco,
            self.comprimento_poco,
            self.altura_poco,
            self.pavimentos,
            self.material_cabine,
            self.altura_cabine,
        ]
        
        campos_preenchidos = all(campo is not None and str(campo).strip() != '' for campo in campos_obrigatorios)
        
        valores_positivos = (
            self.capacidade and float(self.capacidade) > 0 and
            self.largura_poco and float(self.largura_poco) > 0 and
            self.comprimento_poco and float(self.comprimento_poco) > 0 and
            self.altura_poco and float(self.altura_poco) > 0 and
            self.pavimentos and int(self.pavimentos) >= 2 and
            self.altura_cabine and float(self.altura_cabine) > 0
        )
        
        return campos_preenchidos and valores_positivos
