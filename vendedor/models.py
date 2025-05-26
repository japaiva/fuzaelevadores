# vendedor/models.py - MODELO COMPLETO CORRIGIDO - PARTE 1

from django.db import models
from django.conf import settings
from core.models import Cliente
import uuid
from datetime import datetime


class Pedido(models.Model):
    """
    Modelo completo para pedidos de elevadores - sistema novo que substitui as simulações
    """
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('simulado', 'Simulado'),
        ('orcamento_gerado', 'Orçamento Gerado'),
        ('enviado_cliente', 'Enviado ao Cliente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('em_producao', 'Em Produção'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    # === IDENTIFICAÇÃO ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=20, unique=True, verbose_name="Número do Pedido")
    nome_projeto = models.CharField(max_length=200, verbose_name="Nome do Projeto")
    
    # === RELACIONAMENTOS ===
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='pedidos_vendedor',
        verbose_name="Vendedor"
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='pedidos_atualizados',
        blank=True, 
        null=True
    )
    
    # === STATUS E CONTROLE ===
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # === DADOS DO ELEVADOR ===
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
        blank=True,
        verbose_name="Tração"
    )
    contrapeso = models.CharField(
        max_length=20,
        choices=[('Traseiro', 'Traseiro'), ('Lateral', 'Lateral')],
        blank=True,
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

# === DADOS DAS PORTAS ===
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
        verbose_name="Largura Porta Cabine (m)"
    )
    altura_porta_cabine = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
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
        verbose_name="Largura Porta Pavimento (m)"
    )
    altura_porta_pavimento = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Altura Porta Pavimento (m)"
    )

# === DADOS DA CABINE ===
    material_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Inox 430', 'Inox 430'),
            ('Inox 304', 'Inox 304'),
            ('Chapa Pintada', 'Chapa Pintada'),
            ('Alumínio', 'Alumínio'),
            ('Outro', 'Outro'),
        ],
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
        verbose_name="Espessura"
    )
    saida_cabine = models.CharField(
        max_length=20,
        choices=[('Padrão', 'Padrão'), ('Oposta', 'Oposta')],
        verbose_name="Saída"
    )
    altura_cabine = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Altura da Cabine (m)"
    )
    
    # Piso da Cabine
    piso_cabine = models.CharField(
        max_length=50,
        choices=[
            ('Por conta do cliente', 'Por conta do cliente'),
            ('Por conta da empresa', 'Por conta da empresa'),
        ],
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
    
    # === DADOS COMERCIAIS ===
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
    
    # === CUSTOS DETALHADOS ===
    custo_materiais = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Custo de Materiais"
    )
    custo_mao_obra = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Custo de Mão de Obra"
    )
    custo_instalacao = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Custo de Instalação"
    )
    custo_producao = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Custo de Produção"
    )
    
    # === PREÇOS ===
    preco_venda_calculado = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Preço de Venda Calculado"
    )
    preco_sem_impostos = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Preço sem Impostos"
    )
    preco_negociado = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Preço Negociado"
    )
    preco_venda_final = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Preço de Venda Final"
    )
    percentual_desconto = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Desconto (%)"
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
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['vendedor', 'status']),
            models.Index(fields=['cliente']),
            models.Index(fields=['-criado_em']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.nome_projeto}"
    
    def save(self, *args, **kwargs):
        """Salvar com número automático"""
        if not self.numero:
            # Gerar número sequencial SEM prefixo PED para economizar espaço
            from datetime import datetime
            
            ano_atual = datetime.now().year
            ultimo_pedido = Pedido.objects.filter(
                criado_em__year=ano_atual
            ).order_by('-numero').first()
            
            if ultimo_pedido:
                # Extrair número sequencial do último pedido
                try:
                    # Se o número atual tem PED, remover
                    numero_limpo = ultimo_pedido.numero.replace('PED', '').replace(str(ano_atual), '')
                    ultimo_numero = int(numero_limpo)
                    novo_numero = ultimo_numero + 1
                except ValueError:
                    # Se não conseguir extrair, começar do 1
                    novo_numero = 1
            else:
                novo_numero = 1
            
            # Formato: 2025001, 2025002, etc. (ano + sequencial de 3 dígitos)
            self.numero = f'{ano_atual}{novo_numero:03d}'
        
        super().save(*args, **kwargs)

# === PROPRIEDADES DE STATUS ===
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        badges = {
            'rascunho': 'bg-secondary',
            'simulado': 'bg-info',
            'orcamento_gerado': 'bg-primary',
            'enviado_cliente': 'bg-warning',
            'aprovado': 'bg-success',
            'rejeitado': 'bg-danger',
            'em_producao': 'bg-dark',
            'concluido': 'bg-success',
            'cancelado': 'bg-danger',
        }
        return badges.get(self.status, 'bg-secondary')
    
    @property
    def pode_editar(self):
        """Verifica se o pedido ainda pode ser editado"""
        return self.status in ['rascunho', 'simulado']
    
    @property
    def pode_simular(self):
        """Verifica se o pedido pode ser simulado"""
        return self.status in ['rascunho', 'simulado']
    
    @property
    def pode_gerar_orcamento(self):
        """Verifica se pode gerar orçamento"""
        return self.status in ['simulado', 'orcamento_gerado']
    
    @property
    def pode_excluir(self):
        """Verifica se o pedido pode ser excluído"""
        return self.status in ['rascunho', 'simulado']
    
    # === MÉTODOS DE DISPLAY PARA O TEMPLATE ===
    
    def get_modelo_elevador_display(self):
        """Display personalizado para modelo do elevador"""
        choices = {
            'Passageiro': 'Elevador de Passageiro',
            'Carga': 'Elevador de Carga', 
            'Monta Prato': 'Monta Prato',
            'Plataforma Acessibilidade': 'Plataforma de Acessibilidade',
        }
        return choices.get(self.modelo_elevador, self.modelo_elevador)
    
    def get_acionamento_display(self):
        """Display personalizado para acionamento"""
        choices = {
            'Motor': 'Motor Elétrico',
            'Hidraulico': 'Hidráulico',
            'Carretel': 'Carretel',
        }
        return choices.get(self.acionamento, self.acionamento)
    
    def get_tracao_display(self):
        """Display personalizado para tração"""
        choices = {
            '1x1': 'Tração 1:1',
            '2x1': 'Tração 2:1',
        }
        return choices.get(self.tracao, self.tracao)
    
    def get_contrapeso_display(self):
        """Display personalizado para contrapeso"""
        choices = {
            'Lateral': 'Contrapeso Lateral',
            'Traseiro': 'Contrapeso Traseiro',
        }
        return choices.get(self.contrapeso, self.contrapeso)
    
    def get_faturado_por_display(self):
        """Display personalizado para faturado por"""
        choices = {
            'Elevadores': 'Elevadores',
            'Fuza': 'Fuza',
            'Manutenção': 'Manutenção',
        }
        return choices.get(self.faturado_por, self.faturado_por)
    
    def get_modelo_porta_cabine_display(self):
        """Display personalizado para modelo porta cabine"""
        choices = {
            'Automática': 'Automática',
            'Pantográfica': 'Pantográfica',
            'Pivotante': 'Pivotante',
            'Guilhotina': 'Guilhotina',
            'Camarão': 'Camarão',
            'Cancela': 'Cancela',
            'Rampa': 'Rampa',
        }
        return choices.get(self.modelo_porta_cabine, self.modelo_porta_cabine)
    
    def get_material_porta_cabine_display(self):
        """Display personalizado para material porta cabine"""
        if self.material_porta_cabine == 'Outro' and self.material_porta_cabine_outro:
            return self.material_porta_cabine_outro
        
        choices = {
            'Inox': 'Inox',
            'Chapa Pintada': 'Chapa Pintada',
            'Alumínio': 'Alumínio',
            'Outro': 'Outro',
        }
        return choices.get(self.material_porta_cabine, self.material_porta_cabine)
    
    def get_modelo_porta_pavimento_display(self):
        """Display personalizado para modelo porta pavimento"""
        choices = {
            'Automática': 'Automática',
            'Pantográfica': 'Pantográfica',
            'Pivotante': 'Pivotante',
            'Guilhotina': 'Guilhotina',
            'Camarão': 'Camarão',
            'Cancela': 'Cancela',
            'Rampa': 'Rampa',
        }
        return choices.get(self.modelo_porta_pavimento, self.modelo_porta_pavimento)
    
    def get_material_porta_pavimento_display(self):
        """Display personalizado para material porta pavimento"""
        if self.material_porta_pavimento == 'Outro' and self.material_porta_pavimento_outro:
            return self.material_porta_pavimento_outro
        
        choices = {
            'Inox': 'Inox',
            'Chapa Pintada': 'Chapa Pintada',
            'Alumínio': 'Alumínio',
            'Outro': 'Outro',
        }
        return choices.get(self.material_porta_pavimento, self.material_porta_pavimento)
    
    def get_material_cabine_display(self):
        """Display personalizado para material cabine"""
        if self.material_cabine == 'Outro' and self.material_cabine_outro:
            return self.material_cabine_outro
        
        choices = {
            'Inox 430': 'Inox 430',
            'Inox 304': 'Inox 304',
            'Chapa Pintada': 'Chapa Pintada',
            'Alumínio': 'Alumínio',
            'Outro': 'Outro',
        }
        return choices.get(self.material_cabine, self.material_cabine)
    
    def get_espessura_cabine_display(self):
        """Display personalizado para espessura cabine"""
        choices = {
            '1,2': '1,2mm',
            '1,5': '1,5mm',
            '2,0': '2,0mm',
        }
        return choices.get(self.espessura_cabine, self.espessura_cabine)
    
    def get_saida_cabine_display(self):
        """Display personalizado para saída cabine"""
        choices = {
            'Padrão': 'Saída Padrão',
            'Oposta': 'Saída Oposta',
        }
        return choices.get(self.saida_cabine, self.saida_cabine)
    
    def get_piso_cabine_display(self):
        """Display personalizado para piso cabine"""
        choices = {
            'Por conta do cliente': 'Por conta do cliente',
            'Por conta da empresa': 'Por conta da empresa',
        }
        return choices.get(self.piso_cabine, self.piso_cabine)
    
    def get_material_piso_cabine_display(self):
        """Display personalizado para material piso cabine"""
        if self.material_piso_cabine == 'Outro' and self.material_piso_cabine_outro:
            return self.material_piso_cabine_outro
        
        choices = {
            'Antiderrapante': 'Antiderrapante',
            'Outro': 'Outro',
        }
        return choices.get(self.material_piso_cabine, self.material_piso_cabine)

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
        """Verifica se o pedido tem cálculos executados"""
        return bool(self.dimensionamento_detalhado or self.ficha_tecnica or self.custo_producao)
    
    @property
    def tem_precos(self):
        """Verifica se o pedido tem preços calculados"""
        return bool(self.formacao_preco or self.preco_venda_calculado)
    
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
        """Calcula percentual de conclusão do pedido"""
        campos_obrigatorios = [
            self.cliente_id,
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
            """Verifica se o pedido pode ser calculado"""
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
            
            # Log para debug
            if not campos_preenchidos:
                campos_vazios = [i for i, campo in enumerate(campos_obrigatorios) if not campo or str(campo).strip() == '']
                print(f"DEBUG: Campos vazios no pedido {self.numero}: {campos_vazios}")
            
            if not valores_positivos:
                print(f"DEBUG: Valores inválidos no pedido {self.numero}")
                print(f"  - Capacidade: {self.capacidade}")
                print(f"  - Largura poço: {self.largura_poco}")
                print(f"  - Comprimento poço: {self.comprimento_poco}")
                print(f"  - Altura poço: {self.altura_poco}")
                print(f"  - Pavimentos: {self.pavimentos}")
                print(f"  - Altura cabine: {self.altura_cabine}")
            
            return campos_preenchidos and valores_positivos
    
class HistoricoPedido(models.Model):
    """
    Modelo para rastrear mudanças de status dos pedidos
    """
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=20, blank=True)
    status_novo = models.CharField(max_length=20)
    observacao = models.TextField(blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_mudanca = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Histórico do Pedido"
        verbose_name_plural = "Históricos dos Pedidos"
        ordering = ['-data_mudanca']
    
    def __str__(self):
        return f"{self.pedido.numero} - {self.status_anterior} → {self.status_novo}"

class AnexoPedido(models.Model):
    """
    Modelo para anexos dos pedidos (PDFs, imagens, etc.)
    """
    TIPO_CHOICES = [
        ('orcamento', 'Orçamento'),
        ('demonstrativo', 'Demonstrativo de Cálculo'),
        ('contrato', 'Contrato'),
        ('projeto', 'Projeto Técnico'),
        ('foto', 'Foto'),
        ('outro', 'Outro'),
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='anexos')
    nome = models.CharField(max_length=200, verbose_name="Nome do Arquivo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    arquivo = models.FileField(upload_to='pedidos/anexos/%Y/%m/', verbose_name="Arquivo")
    tamanho = models.PositiveIntegerField(blank=True, null=True, verbose_name="Tamanho (bytes)")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    enviado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Anexo do Pedido"
        verbose_name_plural = "Anexos dos Pedidos"
        ordering = ['-enviado_em']
    
    def __str__(self):
        return f"{self.pedido.numero} - {self.nome}"
    
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