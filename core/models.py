# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django import forms  # Adicionar este import
import uuid

class Usuario(AbstractUser):
    NIVEL_CHOICES = [
        ('admin', 'Admin'),
        ('gestor', 'Gestor'),
        ('vendedor', 'Vendedor'),
        ('compras', 'Compras'),
        ('engenharia', 'Engenharia'),
    ]

    # Desabilitar relacionamentos explicitamente
    groups = None
    user_permissions = None
    
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    codigo_loja = models.CharField(max_length=3, blank=True, null=True, 
                                  help_text="Código de 3 dígitos da loja")
    codigo_vendedor = models.CharField(max_length=3, blank=True, null=True, 
                                      help_text="Código de 3 dígitos do vendedor")
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    nivel = models.CharField(
        max_length=20,
        choices=Usuario.NIVEL_CHOICES,
        default='vendedor'
    )
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_nivel_display()}"


class GrupoProduto(models.Model):
    """Grupos de produtos (equivale a Categoria)"""
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Grupo de Produto"
        verbose_name_plural = "Grupos de Produtos"
        ordering = ['codigo', 'nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class SubgrupoProduto(models.Model):
    """Subgrupos de produtos"""
    grupo = models.ForeignKey(GrupoProduto, on_delete=models.CASCADE, related_name='subgrupos')
    codigo = models.CharField(max_length=10, verbose_name="Código")
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Subgrupo de Produto"
        verbose_name_plural = "Subgrupos de Produtos"
        unique_together = ['grupo', 'codigo']
        ordering = ['grupo__codigo', 'codigo', 'nome']
    
    def __str__(self):
        return f"{self.grupo.codigo}.{self.codigo} - {self.nome}"


class Fornecedor(models.Model):
    """Cadastro de fornecedores"""
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)
    contato_principal = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.JSONField(default=dict, blank=True)
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['razao_social']
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social


class Produto(models.Model):
    """
    Modelo unificado para Matéria Prima, Produto Intermediário e Produto Acabado
    """
    
    TIPO_CHOICES = [
        ('MP', 'Matéria Prima'),
        ('PI', 'Produto Intermediário'),
        ('PA', 'Produto Acabado'),
    ]
    
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('KG', 'Quilograma'),
        ('MT', 'Metro'),
        ('M2', 'Metro Quadrado'),
        ('M3', 'Metro Cúbico'),
        ('PC', 'Peça'),
        ('CJ', 'Conjunto'),
    ]
    
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo'),
        ('DESCONTINUADO', 'Descontinuado'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, verbose_name="Tipo")
    
    # Classificação
    grupo = models.ForeignKey(GrupoProduto, on_delete=models.PROTECT, verbose_name="Grupo")
    subgrupo = models.ForeignKey(SubgrupoProduto, on_delete=models.PROTECT, blank=True, null=True)
    
    # Características técnicas (JSON flexível)
    especificacoes_tecnicas = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Especificações técnicas em formato flexível",
        verbose_name="Especificações Técnicas"
    )
    
    # Unidades e medidas
    unidade_medida = models.CharField(max_length=3, choices=UNIDADE_CHOICES, verbose_name="Unidade")
    peso_unitario = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="Peso (kg)")
    dimensoes = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Dimensões: altura, largura, profundidade, diâmetro, etc."
    )
    
    # Controle de estoque
    controla_estoque = models.BooleanField(default=True, verbose_name="Controla Estoque")
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Estoque Mínimo")
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Estoque Atual")
    
    # Precificação
    custo_medio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Custo Médio")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Preço Venda")
    margem_padrao = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Margem Padrão (%)")
    
    # Fornecimento (para MPs) - MANTIDO PARA COMPATIBILIDADE
    fornecedor_principal = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, blank=True, null=True)
    prazo_entrega_padrao = models.IntegerField(blank=True, null=True, verbose_name="Prazo Entrega (dias)")
    
    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVO')
    disponivel = models.BooleanField(default=True, verbose_name="Disponível para Uso")
    motivo_indisponibilidade = models.TextField(blank=True, verbose_name="Motivo Indisponibilidade")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='produtos_criados')
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='produtos_atualizados')
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['tipo', 'grupo']),
            models.Index(fields=['disponivel', 'status']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def disponibilidade_info(self):
        """Informações sobre disponibilidade para o motor de regras"""
        if not self.disponivel:
            return {
                'disponivel': False,
                'motivo': self.motivo_indisponibilidade,
                'tipo': 'bloqueio_manual'
            }
        
        if self.controla_estoque and self.estoque_atual <= self.estoque_minimo:
            return {
                'disponivel': False,
                'motivo': f'Estoque baixo: {self.estoque_atual} (mín: {self.estoque_minimo})',
                'tipo': 'estoque_baixo'
            }
            
        return {'disponivel': True, 'motivo': '', 'tipo': 'ok'}

    @property
    def fornecedor_principal_novo(self):
        """Retorna o fornecedor principal baseado na nova estrutura"""
        fornecedor_principal = self.fornecedores_produto.filter(
            ativo=True, 
            prioridade=1
        ).first()
        
        if fornecedor_principal:
            return fornecedor_principal.fornecedor
        
        # Fallback para o campo antigo se existir
        return self.fornecedor_principal
    
    @property
    def melhor_preco(self):
        """Retorna o melhor preço entre os fornecedores ativos"""
        precos = self.fornecedores_produto.filter(
            ativo=True,
            preco_unitario__isnull=False
        ).values_list('preco_unitario', flat=True)
        
        return min(precos) if precos else None
    
    @property
    def menor_prazo_entrega(self):
        """Retorna o menor prazo de entrega"""
        prazos = self.fornecedores_produto.filter(
            ativo=True,
            prazo_entrega__isnull=False
        ).values_list('prazo_entrega', flat=True)
        
        return min(prazos) if prazos else self.prazo_entrega_padrao
    
    def fornecedores_ordenados(self):
        """Retorna fornecedores ordenados por prioridade"""
        return self.fornecedores_produto.filter(ativo=True).order_by('prioridade')


class FornecedorProduto(models.Model):
    """
    Relacionamento N:N entre Fornecedor e Produto com informações específicas
    """
    PRIORIDADE_CHOICES = [
        (1, 'Principal'),
        (2, 'Secundário'),
        (3, 'Terceiro'),
        (4, 'Backup'),
    ]
    
    produto = models.ForeignKey(
        Produto, 
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
        choices=PRIORIDADE_CHOICES, 
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


# Modelo para relacionamento entre produtos (composição/estrutura)
class EstruturaProduto(models.Model):
    """
    Define a estrutura/composição de produtos intermediários e acabados
    """
    produto_pai = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name='componentes',
        limit_choices_to={'tipo__in': ['PI', 'PA']}
    )
    produto_filho = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name='usado_em'
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Quantidade")
    unidade = models.CharField(max_length=3, choices=Produto.UNIDADE_CHOICES)
    
    # Para cálculos dinâmicos
    formula_quantidade = models.TextField(
        blank=True,
        help_text="Fórmula para cálculo dinâmico da quantidade (ex: 'altura * 2 + 0.5')"
    )
    
    # Perda/desperdício
    percentual_perda = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="% Perda"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Estrutura do Produto"
        verbose_name_plural = "Estruturas dos Produtos"
        unique_together = ['produto_pai', 'produto_filho']
    
    def __str__(self):
        return f"{self.produto_pai.codigo} → {self.produto_filho.codigo}"


# =============================================================================
# MODELOS PARA MOTOR DE REGRAS CONFIGURÁVEL
# =============================================================================

class EspecificacaoElevador(models.Model):
    """
    Define os tipos de especificações possíveis para elevadores
    """
    TIPO_CHOICES = [
        ('categoria', 'Categoria'),
        ('material', 'Material'),
        ('acabamento', 'Acabamento'),
        ('dimensao', 'Dimensão'),
        ('capacidade', 'Capacidade'),
        ('velocidade', 'Velocidade'),
        ('paradas', 'Número de Paradas'),
        ('opcional', 'Opcional'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
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
    componente = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name="Componente")
    
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
    TIPO_CALCULO_CHOICES = [
        ('proporcional', 'Proporcional'),
        ('fixo', 'Valor Fixo'),
        ('formula', 'Fórmula'),
    ]
    
    componente_origem = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name='derivados',
        verbose_name="Componente Origem"
    )
    componente_destino = models.ForeignKey(
        Produto, 
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


# =============================================================================
# MODELOS PARA SIMULAÇÕES E PROPOSTAS
# =============================================================================

class SimulacaoElevador(models.Model):
    """
    Armazena simulações de elevadores feitas pelos vendedores
    """
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('simulado', 'Simulado'),
        ('proposta', 'Proposta Gerada'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]
    
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
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
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
    

# Adicionar este modelo em core/models.py

class Cliente(models.Model):
    """Cadastro básico de clientes"""
    
    TIPO_PESSOA_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    # Identificação
    tipo_pessoa = models.CharField(max_length=2, choices=TIPO_PESSOA_CHOICES, verbose_name="Tipo de Pessoa")
    nome = models.CharField(max_length=200, verbose_name="Nome/Razão Social")
    nome_fantasia = models.CharField(max_length=200, blank=True, verbose_name="Nome Fantasia")
    cpf_cnpj = models.CharField(max_length=18, blank=True, verbose_name="CPF/CNPJ")
    
    # Contato
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="Email")
    contato_principal = models.CharField(max_length=100, blank=True, verbose_name="Contato Principal")
    
    # Endereço
    cep = models.CharField(max_length=10, blank=True, verbose_name="CEP")
    endereco = models.CharField(max_length=200, blank=True, verbose_name="Logradouro")
    numero = models.CharField(max_length=20, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    
    # Observações e status
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clientes_criados')
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clientes_atualizados', null=True, blank=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return self.nome
    
    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        partes = []
        if self.endereco:
            endereco_numero = f"{self.endereco}, {self.numero}" if self.numero else self.endereco
            partes.append(endereco_numero)
        if self.complemento:
            partes.append(self.complemento)
        if self.bairro:
            partes.append(self.bairro)
        if self.cidade:
            cidade_estado = f"{self.cidade} - {self.estado}" if self.estado else self.cidade
            partes.append(cidade_estado)
        if self.cep:
            partes.append(f"CEP: {self.cep}")
        
        return ", ".join(partes) if partes else ""
    
    def clean(self):
        """Validações personalizadas"""
        from django.core.exceptions import ValidationError
        
        if self.cpf_cnpj:
            cpf_cnpj_numerico = ''.join(filter(str.isdigit, self.cpf_cnpj))
            
            if self.tipo_pessoa == 'PF' and len(cpf_cnpj_numerico) != 11:
                raise ValidationError({'cpf_cnpj': 'CPF deve ter 11 dígitos.'})
            elif self.tipo_pessoa == 'PJ' and len(cpf_cnpj_numerico) != 14:
                raise ValidationError({'cpf_cnpj': 'CNPJ deve ter 14 dígitos.'})
        
        if self.cep:
            cep_numerico = ''.join(filter(str.isdigit, self.cep))
            if len(cep_numerico) != 8:
                raise ValidationError({'cep': 'CEP deve ter 8 dígitos.'})