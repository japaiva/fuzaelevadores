# core/models/produtos.py

"""
Models relacionados a produtos, grupos e estruturas
VERSÃO ATUALIZADA COM TIPOS DE PRODUTOS INTERMEDIÁRIOS
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
import uuid

from .base import (
    TIPO_PRODUTO_CHOICES, 
    UNIDADE_MEDIDA_CHOICES, 
    STATUS_PRODUTO_CHOICES
)

class GrupoProduto(models.Model):
    """Grupos de produtos com classificação por tipo"""
    
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

class Produto(models.Model):
    """
    Modelo unificado para Matéria Prima, Produto Intermediário e Produto Acabado
    Com geração automática de código baseada em grupo/subgrupo
    ATUALIZADO COM TIPOS DE PRODUTOS INTERMEDIÁRIOS
    """
    
    # NOVO: Tipos de Produtos Intermediários
    TIPO_PI_CHOICES = [
        ('COMPRADO', 'Comprado Pronto'),
        ('MONTADO_INTERNO', 'Montado Internamente'),
        ('MONTADO_EXTERNO', 'Montado Externamente'),
        ('SERVICO', 'Serviço'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    tipo = models.CharField(max_length=2, choices=TIPO_PRODUTO_CHOICES, verbose_name="Tipo")
    
    # NOVO CAMPO: Tipo do Produto Intermediário
    tipo_pi = models.CharField(
        max_length=20,
        choices=TIPO_PI_CHOICES,
        null=True,
        blank=True,
        verbose_name="Tipo do Produto Intermediário",
        help_text="Apenas para Produtos Intermediários (PI)"
    )
    
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
    unidade_medida = models.CharField(max_length=3, choices=UNIDADE_MEDIDA_CHOICES, verbose_name="Unidade")
    peso_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        blank=True, 
        null=True, 
        verbose_name="Peso (kg)"
    )
    dimensoes = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Dimensões: altura, largura, profundidade, diâmetro, etc."
    )
    
    # Controle de estoque
    controla_estoque = models.BooleanField(default=True, verbose_name="Controla Estoque")
    estoque_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Estoque Mínimo"
    )
    estoque_atual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Estoque Atual"
    )
    
    # Custos e preços
    custo_medio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Custo Médio"
    )

    custo_industrializacao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Custo Industrialização"
    )

    preco_venda = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Preço Venda"
    )
    margem_padrao = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Margem Padrão (%)"
    )

    # Fornecimento
    fornecedor_principal = models.ForeignKey(
        'Fornecedor', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='produtos_principal'
    )
    prazo_entrega_padrao = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name="Prazo Entrega (dias)"
    )
    
    codigo_ncm = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Código NCM"
    )

    codigo_produto_fornecedor = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Código no Fornecedor"
    )

    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_PRODUTO_CHOICES, default='ATIVO')
    disponivel = models.BooleanField(default=True, verbose_name="Disponível para Uso")
    motivo_indisponibilidade = models.TextField(
        blank=True, 
        verbose_name="Motivo Indisponibilidade"
    )
    
    utilizado = models.BooleanField(
        default=False, 
        verbose_name="Material Utilizado",
        help_text="Indica se este material já foi utilizado em algum projeto"
    )
    
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
            models.Index(fields=['utilizado']),
            models.Index(fields=['tipo_pi']),  # NOVO ÍNDICE
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def clean(self):
        """Validações personalizadas do produto"""
        super().clean()
        
        # O tipo do produto deve coincidir com o tipo do grupo
        if self.grupo and self.grupo.tipo_produto:
            self.tipo = self.grupo.tipo_produto
        
        # NOVA VALIDAÇÃO: tipo_pi apenas para produtos PI
        if self.tipo == 'PI':
            if not self.tipo_pi:
                raise ValidationError({
                    'tipo_pi': 'Tipo do Produto Intermediário é obrigatório para produtos PI.'
                })
        else:
            # Para MP e PA, tipo_pi deve ser None
            self.tipo_pi = None
        
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
            
            # Gerar código: GG.SS.NNNNN (5 dígitos)
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

    # =================================================================================
    # NOVAS PROPERTIES E MÉTODOS PARA TIPOS DE PI
    # =================================================================================
    
    @property
    def pode_ter_estrutura(self):
        """Retorna True se o produto pode ter estrutura de componentes"""
        return (
            self.tipo == 'PI' and 
            self.tipo_pi in ['MONTADO_INTERNO', 'MONTADO_EXTERNO']
        )
    
    @property
    def tipo_pi_display_badge(self):
        """Retorna classe CSS para badge do tipo PI"""
        badges = {
            'COMPRADO': 'bg-info',
            'MONTADO_INTERNO': 'bg-success',
            'MONTADO_EXTERNO': 'bg-warning',
            'SERVICO': 'bg-secondary',
        }
        return badges.get(self.tipo_pi, 'bg-primary')
    
    def calcular_custo_estrutura(self):
        """Calcula custo baseado na estrutura de componentes"""
        if not self.pode_ter_estrutura:
            return None
            
        custo_total = 0
        
        for componente in self.componentes.all():
            produto_filho = componente.produto_filho
            quantidade = componente.quantidade
            
            # Pegar custo do componente
            if produto_filho.tipo == 'MP':
                custo_unitario = produto_filho.custo_total or 0
            elif produto_filho.tipo == 'PI':
                if produto_filho.tipo_pi in ['MONTADO_INTERNO', 'MONTADO_EXTERNO']:
                    # Recursivo - calcular custo do componente primeiro
                    custo_unitario = produto_filho.calcular_custo_estrutura() or produto_filho.custo_total or 0
                else:
                    custo_unitario = produto_filho.custo_total or 0
            else:
                custo_unitario = produto_filho.custo_total or 0
            
            # Aplicar quantidade e perda
            quantidade_com_perda = quantidade * (1 + (componente.percentual_perda / 100))
            custo_componente = custo_unitario * quantidade_com_perda
            custo_total += custo_componente
        
        return custo_total

    # =================================================================================
    # PROPERTIES EXISTENTES (MANTIDAS)
    # =================================================================================

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
    def status_utilizado_display(self):
        """Retorna classe CSS para badge do status utilizado"""
        return 'bg-warning' if self.utilizado else 'bg-success'
    
    @property
    def fornecedor_principal_novo(self):
        """Retorna o fornecedor principal baseado na nova estrutura"""
        # Se existir um relacionamento futuro com fornecedores_produto, usar:
        if hasattr(self, 'fornecedores_produto'):
            fornecedor_principal = self.fornecedores_produto.filter(
                ativo=True, 
                prioridade=1
            ).first()
            
            if fornecedor_principal:
                return fornecedor_principal.fornecedor
        
        # Fallback para o campo atual
        return self.fornecedor_principal
    
    @property
    def custo_total(self):
        """Retorna a soma do custo médio + custo de industrialização"""
        custo_base = self.custo_medio or 0
        custo_indust = self.custo_industrializacao or 0
        return custo_base + custo_indust
    
    @property
    def melhor_preco(self):
        """Retorna o melhor preço entre os fornecedores ativos ou preço atual"""
        # Se existir relacionamento futuro com fornecedores_produto:
        if hasattr(self, 'fornecedores_produto'):
            precos = self.fornecedores_produto.filter(
                ativo=True,
                preco_unitario__isnull=False
            ).values_list('preco_unitario', flat=True)
            
            if precos:
                return min(precos)
        
        # Por enquanto, retornar o custo médio ou preço de venda
        return self.custo_medio or self.preco_venda
    
    @property
    def menor_prazo_entrega(self):
        """Retorna o menor prazo de entrega"""
        # Se existir relacionamento futuro com fornecedores_produto:
        if hasattr(self, 'fornecedores_produto'):
            prazos = self.fornecedores_produto.filter(
                ativo=True,
                prazo_entrega__isnull=False
            ).values_list('prazo_entrega', flat=True)
            
            if prazos:
                return min(prazos)
        
        # Fallback para o campo atual
        return self.prazo_entrega_padrao
    
    def fornecedores_ordenados(self):
        """Retorna fornecedores ordenados por prioridade"""
        # Se existir relacionamento futuro com fornecedores_produto:
        if hasattr(self, 'fornecedores_produto'):
            return self.fornecedores_produto.filter(ativo=True).order_by('prioridade')
        
        # Por enquanto, retornar lista com o fornecedor principal se existir
        if self.fornecedor_principal:
            return [self.fornecedor_principal]
        
        return []


class EstruturaProduto(models.Model):
    """
    Define a estrutura/composição de produtos intermediários e acabados
    ATUALIZADA PARA SUPORTAR TIPOS DE PI
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
    unidade = models.CharField(max_length=3, choices=UNIDADE_MEDIDA_CHOICES)
    
    # Para cálculos dinâmicos (futuro)
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
    
    def clean(self):
        """Validações da estrutura"""
        super().clean()
        
        # Verificar se produto pai pode ter estrutura
        if self.produto_pai and not self.produto_pai.pode_ter_estrutura:
            raise ValidationError(
                f'O produto "{self.produto_pai}" não suporta estrutura de componentes.'
            )
        
        # Evitar referência circular
        if self.produto_pai == self.produto_filho:
            raise ValidationError('Um produto não pode ser componente de si mesmo.')
    
    @property
    def quantidade_com_perda(self):
        """Retorna quantidade considerando a perda"""
        return self.quantidade * (1 + (self.percentual_perda / 100))
    
    @property
    def custo_total_componente(self):
        """Retorna custo total do componente (quantidade * preço * perda)"""
        custo_unitario = self.produto_filho.custo_total or 0
        return custo_unitario * self.quantidade_com_perda