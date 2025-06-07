# core/models.py - VERSÃO COMPLETA CORRIGIDA

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django import forms 
from django.core.exceptions import ValidationError
from django.db import transaction
import uuid, re

from core.utils.validators import validar_cpf, validar_cnpj, formatar_cpf, formatar_cnpj, validar_cpf_cnpj_unico

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


# Atualizações no core/models.py

class GrupoProduto(models.Model):
    """Grupos de produtos com classificação por tipo"""
    
    TIPO_PRODUTO_CHOICES = [
        ('MP', 'Matéria Prima'),
        ('PI', 'Produto Intermediário'),
        ('PA', 'Produto Acabado'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=100, unique=True)
    tipo_produto = models.CharField(
        max_length=2, 
        choices=TIPO_PRODUTO_CHOICES, 
        default='MP',
        verbose_name="Tipo de Produto"
    )
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='grupos_produtos_criados'
    )
    
    class Meta:
        verbose_name = "Grupo de Produto"
        verbose_name_plural = "Grupos de Produtos"
        ordering = ['codigo', 'nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def tipo_produto_display_badge(self):
        """Retorna classe CSS para badge do tipo"""
        badges = {
            'MP': 'bg-primary',      # Matéria Prima - Azul
            'PI': 'bg-warning',      # Produto Intermediário - Amarelo
            'PA': 'bg-success',      # Produto Acabado - Verde
        }
        return badges.get(self.tipo_produto, 'bg-secondary')


class SubgrupoProduto(models.Model):
    """Subgrupos de produtos com controle sequencial"""
    grupo = models.ForeignKey(
        GrupoProduto, 
        on_delete=models.CASCADE, 
        related_name='subgrupos'
    )
    codigo = models.CharField(max_length=10, verbose_name="Código")
    nome = models.CharField(max_length=100)
    ultimo_numero = models.IntegerField(
        default=0, 
        verbose_name="Último Número"
    )
    ativo = models.BooleanField(default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='subgrupos_produtos_criados'
    )
    
    class Meta:
        verbose_name = "Subgrupo de Produto"
        verbose_name_plural = "Subgrupos de Produtos"
        unique_together = ['grupo', 'codigo']
        ordering = ['grupo__codigo', 'codigo', 'nome']
    
    def __str__(self):
        return f"{self.grupo.codigo}.{self.codigo} - {self.nome}"
    
    def get_proximo_numero(self):
        """Retorna o próximo número sequencial para produtos deste subgrupo"""
        self.ultimo_numero += 1
        self.save(update_fields=['ultimo_numero'])
        return self.ultimo_numero
    
    @property
    def codigo_completo(self):
        """Retorna código completo grupo.subgrupo"""
        return f"{self.grupo.codigo}.{self.codigo}"


class Cliente(models.Model):
    """Cadastro básico de clientes com validação de CPF/CNPJ"""
    
    TIPO_PESSOA_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    # Identificação
    tipo_pessoa = models.CharField(max_length=2, choices=TIPO_PESSOA_CHOICES, verbose_name="Tipo de Pessoa")
    nome = models.CharField(max_length=200, verbose_name="Nome/Razão Social")
    nome_fantasia = models.CharField(max_length=200, blank=True, verbose_name="Nome Fantasia")
    cpf_cnpj = models.CharField(
        max_length=18, 
        blank=True, 
        verbose_name="CPF/CNPJ",
        help_text="Digite apenas números ou use a formatação padrão"
    )
    
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
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='clientes_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='clientes_atualizados', 
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['ativo']),
        ]
        constraints = [
            # Constraint para garantir unicidade de CPF/CNPJ não vazio
            models.UniqueConstraint(
                fields=['cpf_cnpj'],
                condition=models.Q(cpf_cnpj__isnull=False) & ~models.Q(cpf_cnpj=''),
                name='unique_cpf_cnpj_not_empty'
            )
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
    
    @property
    def cpf_cnpj_formatado(self):
        """Retorna CPF/CNPJ formatado para exibição"""
        if not self.cpf_cnpj:
            return ""
        
        if self.tipo_pessoa == 'PF':
            return formatar_cpf(self.cpf_cnpj)
        else:
            return formatar_cnpj(self.cpf_cnpj)
    
    def clean(self):
        """Validações personalizadas"""
        errors = {}
        
        # Validação do CPF/CNPJ
        if self.cpf_cnpj:
            # Remove caracteres não numéricos para validação
            cpf_cnpj_numerico = re.sub(r'\D', '', self.cpf_cnpj)
            
            if self.tipo_pessoa == 'PF':
                try:
                    self.cpf_cnpj = validar_cpf(cpf_cnpj_numerico)
                except ValidationError as e:
                    errors['cpf_cnpj'] = e.message
            elif self.tipo_pessoa == 'PJ':
                try:
                    self.cpf_cnpj = validar_cnpj(cpf_cnpj_numerico)
                except ValidationError as e:
                    errors['cpf_cnpj'] = e.message
            
            # Validar unicidade
            try:
                validar_cpf_cnpj_unico(self.cpf_cnpj, instance=self, model_class=Cliente)
            except ValidationError as e:
                errors['cpf_cnpj'] = e.message
        
        # Validação do CEP
        if self.cep:
            cep_numerico = re.sub(r'\D', '', self.cep)
            if len(cep_numerico) != 8:
                errors['cep'] = 'CEP deve ter 8 dígitos.'
            else:
                # Formatar CEP para armazenamento: 00000-000
                self.cep = f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override do save para aplicar validações e formatações"""
        # Executar validações
        self.clean()
        
        # Formatar CPF/CNPJ para armazenamento (apenas números)
        if self.cpf_cnpj:
            self.cpf_cnpj = re.sub(r'\D', '', self.cpf_cnpj)
        
        super().save(*args, **kwargs)


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


class Produto(models.Model):
    """
    Modelo unificado para Matéria Prima, Produto Intermediário e Produto Acabado
    CORRIGIDO: Geração automática de código baseada em grupo/subgrupo
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
    grupo = models.ForeignKey(
        GrupoProduto, 
        on_delete=models.PROTECT, 
        verbose_name="Grupo",
        related_name='produtos'
    )
    subgrupo = models.ForeignKey(
        SubgrupoProduto, 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True,
        related_name='produtos'
    )
    
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
    fornecedor_principal = models.ForeignKey(
        Fornecedor, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='produtos_principal'
    )
    prazo_entrega_padrao = models.IntegerField(blank=True, null=True, verbose_name="Prazo Entrega (dias)")
    
    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVO')
    disponivel = models.BooleanField(default=True, verbose_name="Disponível para Uso")
    motivo_indisponibilidade = models.TextField(blank=True, verbose_name="Motivo Indisponibilidade")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='produtos_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='produtos_atualizados'
    )
    
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
    

    def gerar_codigo_automatico(self):
        """
        Gera código automático no formato GG.SS.NNNNN
        onde GG = código do grupo, SS = código do subgrupo, NNNNN = número sequencial (até 99999)
        """
        if not self.subgrupo:
            raise ValidationError('Subgrupo é obrigatório para gerar código automático.')
        
        if not self.grupo:
            raise ValidationError('Grupo é obrigatório para gerar código automático.')
        
        # Usar transaction para evitar race conditions
        with transaction.atomic():
            # Buscar o subgrupo com lock para garantir dados atualizados
            subgrupo = SubgrupoProduto.objects.select_for_update().get(id=self.subgrupo.id)
            
            # Incrementar o último número
            proximo_numero = subgrupo.ultimo_numero + 1
            
            # Verificar se não passou do limite de 99999
            if proximo_numero > 99999:
                raise ValidationError(
                    f'Limite de produtos atingido para o subgrupo {subgrupo.codigo_completo}. '
                    f'Máximo permitido: 99999 produtos.'
                )
            
            # Gerar código: GG.SS.NNNNN (5 dígitos agora)
            codigo_gerado = f"{self.grupo.codigo}.{subgrupo.codigo}.{proximo_numero:05d}"
            
            # Verificar se o código já existe (proteção extra)
            while Produto.objects.filter(codigo=codigo_gerado).exists():
                # Se existir, incrementar novamente
                proximo_numero += 1
                if proximo_numero > 99999:
                    raise ValidationError(
                        f'Limite de produtos atingido para o subgrupo {subgrupo.codigo_completo}. '
                        f'Máximo permitido: 99999 produtos.'
                    )
                codigo_gerado = f"{self.grupo.codigo}.{subgrupo.codigo}.{proximo_numero:05d}"
            
            # Atualizar o último número no subgrupo
            subgrupo.ultimo_numero = proximo_numero
            subgrupo.save(update_fields=['ultimo_numero'])
            
            # Definir o código no produto
            self.codigo = codigo_gerado
            
            return codigo_gerado

    def save(self, *args, **kwargs):
        """
        Override do save para gerar código automático no formato GG.SS.NNNNN
        """
        # Garantir que o tipo coincida com o grupo
        if self.grupo and self.grupo.tipo_produto:
            self.tipo = self.grupo.tipo_produto
        
        # Gerar código automático se não existir e tiver subgrupo
        if not self.codigo and self.subgrupo:
            # Usar transaction para evitar race conditions
            with transaction.atomic():
                # Buscar o subgrupo novamente para garantir dados atualizados
                subgrupo = SubgrupoProduto.objects.select_for_update().get(id=self.subgrupo.id)
                
                # Incrementar o último número
                proximo_numero = subgrupo.ultimo_numero + 1
                
                # Verificar limite
                if proximo_numero > 99999:
                    raise ValidationError(
                        f'Limite de produtos atingido para o subgrupo {subgrupo.codigo_completo}. '
                        f'Máximo permitido: 99999 produtos.'
                    )
                
                # Gerar código: GG.SS.NNNNN (5 dígitos)
                self.codigo = f"{self.grupo.codigo}.{subgrupo.codigo}.{proximo_numero:05d}"
                
                # Atualizar o último número no subgrupo
                subgrupo.ultimo_numero = proximo_numero
                subgrupo.save(update_fields=['ultimo_numero'])
        
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validações personalizadas do produto
        """
        # O tipo do produto deve coincidir com o tipo do grupo
        if self.grupo and self.grupo.tipo_produto:
            self.tipo = self.grupo.tipo_produto
        
        # Gerar código automático se não fornecido
        if not self.codigo and self.subgrupo:
            self.gerar_codigo_automatico()
        
        # Validar unicidade do código
        if self.codigo:
            produtos_existentes = Produto.objects.filter(codigo=self.codigo)
            if self.pk:
                produtos_existentes = produtos_existentes.exclude(pk=self.pk)
            
            if produtos_existentes.exists():
                raise ValidationError({'codigo': 'Já existe um produto com este código.'})

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


class ParametrosGerais(models.Model):
    # === DADOS DA EMPRESA ===
    razao_social = models.CharField(max_length=200, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=200, blank=True)
    cnpj = models.CharField(max_length=18, blank=True)
    inscricao_estadual = models.CharField(max_length=20, blank=True)

    endereco = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    cep = models.CharField(max_length=10, blank=True)

    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # === PARÂMETROS NUMÉRICOS ===
    margem_padrao = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    comissao_padrao = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    desconto_alcada_1 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    desconto_alcada_2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    faturamento_elevadores = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    faturamento_fuza = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    faturamento_manutencao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='parametros_criados'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='parametros_atualizados',
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Parâmetros Gerais"
        verbose_name_plural = "Parâmetros Gerais"
        db_table = 'parametros_gerais'

    def __str__(self):
        return f"Parâmetros Gerais - {self.razao_social or 'Sistema'}"