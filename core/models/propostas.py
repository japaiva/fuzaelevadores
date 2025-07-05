# core/models/propostas.py - MODELO COMPLETO CORRIGIDO

"""
Modelo de Propostas com estrutura de custos contabilmente correta
"""

from django.db import models
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

class Proposta(models.Model):
    """
    Modelo completo para propostas de elevadores
    ATUALIZADO: Estrutura de custos contabilmente correta
    """
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('simulado', 'Simulado'),
        ('pendente', 'Pendente'),
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

    TIPO_ENTREGA_CHOICES = [
        ('assinatura', 'Na Assinatura do Contrato'),
        ('inicio_obra', 'No Início da Obra'),
        ('50_obra', '50% da Obra'),
        ('entrega', 'Na Entrega'),
        ('personalizado', 'Personalizado'),
    ]

    # === IDENTIFICAÇÃO ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=8, unique=True, verbose_name="Número da Proposta")
    nome_projeto = models.CharField(max_length=200, verbose_name="Nome do Projeto")
    
    # === RELACIONAMENTOS ===
    cliente = models.ForeignKey('Cliente', on_delete=models.PROTECT, verbose_name="Cliente")
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='propostas_vendedor',
        verbose_name="Vendedor",
        null=True, blank=True,  # ← ADICIONAR ESTA LINHA
        limit_choices_to={'nivel': 'vendedor'}
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='propostas_atualizadas',
        blank=True, 
        null=True
    )
    
    # === STATUS E CONTROLE ===
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # === DADOS COMERCIAIS ===
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
    prazo_entrega_dias = models.PositiveIntegerField(
        default=45,
        verbose_name="Prazo de Entrega (dias)",
        help_text="Prazo em dias corridos para entrega após aprovação"
    )
    
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
    
    # === DADOS DO ELEVADOR === (Step 1)
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
    contrapeso = models.CharField(
        max_length=20,
        choices=[('Traseiro', 'Traseiro'), ('Lateral', 'Lateral')],
        blank=True, null=True,
        verbose_name="Contrapeso"
    )
    
    # Dimensões do Poço
    largura_poco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Largura do Poço (m)"
    )
    comprimento_poco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Comprimento do Poço (m)"
    )
    altura_poco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Altura do Poço (m)"
    )
    pavimentos = models.IntegerField(verbose_name="Número de Pavimentos")

    # === DADOS DAS PORTAS === (Step 2)
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
            ('Inox', 'Inox'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
            ('Outro', 'Outro'),
        ],
        null=True, blank=True,
        verbose_name="Material Porta Cabine"
    )
    material_porta_cabine_outro = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Material Porta Cabine (Outro)"
    )
    valor_porta_cabine_outro = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor Material Porta Cabine (Outro)"
    )
    folhas_porta_cabine = models.CharField(
        max_length=10,
        choices=[('2', '2'), ('3', '3'), ('Central', 'Central')],
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
            ('Inox', 'Inox'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
            ('Outro', 'Outro'),
        ],
        null=True, blank=True,
        verbose_name="Material Porta Pavimento"
    )
    material_porta_pavimento_outro = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Material Porta Pavimento (Outro)"
    )
    valor_porta_pavimento_outro = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor Material Porta Pavimento (Outro)"
    )
    folhas_porta_pavimento = models.CharField(
        max_length=10,
        choices=[('2', '2'), ('3', '3'), ('Central', 'Central')],
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

    # === DADOS DA CABINE === (Step 2)
    material_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Inox 430', 'Inox 430'),
            ('Inox 304', 'Inox 304'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
            ('Outro', 'Outro'),
        ],
        null=True, blank=True,
        verbose_name="Material da Cabine"
    )
    material_cabine_outro = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Material da Cabine (Outro)"
    )
    valor_cabine_outro = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor Material da Cabine (Outro)"
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
            ('Outro', 'Outro'),
        ],
        blank=True,
        verbose_name="Material do Piso"
    )
    material_piso_cabine_outro = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Material do Piso (Outro)"
    )
    valor_piso_cabine_outro = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor Material do Piso (Outro)"
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
    
    # ✅ NOVO CAMPO
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
    
    # ✅ NOVO CAMPO
    custo_total_projeto = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Custo Total do Projeto",
        help_text="Custo de Produção + Custo de Instalação"
    )
    
    # =================================================================
    # FORMAÇÃO DE PREÇO
    # =================================================================
    
    # ✅ NOVO CAMPO
    margem_lucro = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Margem de Lucro",
        help_text="30% sobre custo total do projeto"
    )
    
    # ✅ NOVO CAMPO
    preco_com_margem = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Preço com Margem",
        help_text="Custo Total + Margem de Lucro"
    )
    
    # ✅ NOVO CAMPO
    comissao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Comissão",
        help_text="3% sobre preço com margem"
    )
    
    # ✅ NOVO CAMPO
    preco_com_comissao = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Preço com Comissão",
        help_text="Preço com Margem + Comissão"
    )
    
    # ✅ NOVO CAMPO
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
    
    def __str__(self):
        valor_display = f"R$ {self.valor_proposta:,.2f}" if self.valor_proposta else "Valor não definido"
        return f"{self.numero} - {self.nome_projeto} - {valor_display}"
    
    def save(self, *args, **kwargs):
        """Salvar com número automático formato 25.00001 e definir data de validade"""
        if not self.numero:
            # Gerar número sequencial formato YY.00001
            from datetime import datetime
            
            ano_atual = datetime.now().year
            ano_dois_digitos = str(ano_atual)[-2:]  # Pega os dois últimos dígitos do ano
            
            # Buscar último número do ano atual
            ultimo_pedido = Proposta.objects.filter(
                numero__startswith=f'{ano_dois_digitos}.'
            ).order_by('-numero').first()
            
            if ultimo_pedido:
                try:
                    # Extrair número sequencial: "25.00001" -> "00001" -> 1
                    numero_parte = ultimo_pedido.numero.split('.')[1]
                    ultimo_numero = int(numero_parte)
                    novo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    novo_numero = 1
            else:
                novo_numero = 1
            
            # Formato: YY.00001 (ex: 25.00001)
            self.numero = f'{ano_dois_digitos}.{novo_numero:05d}'
        
        # Definir data de validade padrão se não informada
        if not self.data_validade:
            from datetime import date, timedelta
            self.data_validade = date.today() + timedelta(days=30)

        # Se valor_proposta não foi definido pelo usuário, usar o calculado como base
        if self.preco_venda_calculado and self.valor_proposta is None:
            self.valor_proposta = self.preco_venda_calculado

        super().save(*args, **kwargs)

    # =================================================================
    # PROPRIEDADES CALCULADAS
    # =================================================================
    
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

    # === PROPRIEDADES DE STATUS ===
    
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
        from datetime import date
        return date.today() > self.data_validade
    
    @property
    def dias_para_vencer(self):
        """Retorna quantos dias faltam para vencer"""
        if not self.data_validade:
            return None
        from datetime import date
        delta = self.data_validade - date.today()
        return delta.days
    
    # === MÉTODOS DE CÁLCULO COMERCIAL ===
    
    def calcular_parcelas(self):
        """Calcula as datas de vencimento das parcelas"""
        if not self.primeira_parcela or not self.numero_parcelas:
            return []
        
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        parcelas = []
        data_atual = self.primeira_parcela
        
        # Definir incremento baseado no tipo de parcela
        incrementos = {
            'mensal': relativedelta(months=1),
            'bimestral': relativedelta(months=2),
            'trimestral': relativedelta(months=3),
            'semestral': relativedelta(months=6),
            'anual': relativedelta(years=1),
            'personalizado': relativedelta(months=1),  # Padrão
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
        # Verificar campos obrigatórios básicos
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
        
        # Todos os campos obrigatórios devem estar preenchidos
        campos_preenchidos = all(campo is not None and str(campo).strip() != '' for campo in campos_obrigatorios)
        
        # Verificar valores numéricos positivos
        valores_positivos = (
            self.capacidade and float(self.capacidade) > 0 and
            self.largura_poco and float(self.largura_poco) > 0 and
            self.comprimento_poco and float(self.comprimento_poco) > 0 and
            self.altura_poco and float(self.altura_poco) > 0 and
            self.pavimentos and int(self.pavimentos) >= 2 and
            self.altura_cabine and float(self.altura_cabine) > 0
        )
        
        return campos_preenchidos and valores_positivos


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