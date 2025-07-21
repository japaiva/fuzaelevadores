# core/models/produtos.py - ATUALIZAÇÃO: Cálculo automático de custos ao salvar

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

# Adicione estas classes no INÍCIO do arquivo core/models/produtos.py

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
    
    TIPO_PI_CHOICES = [
        ('COMPRADO', 'Comprado Pronto'),
        ('MONTADO_INTERNO', 'Montado Internamente'),
        ('MONTADO_EXTERNO', 'Montado Externamente'),
        ('SERVICO_INTERNO', 'Serviço Interno'),
        ('SERVICO_EXTERNO', 'Serviço Externo'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    tipo = models.CharField(max_length=2, choices=TIPO_PRODUTO_CHOICES, verbose_name="Tipo")
    
    # Tipo do Produto Intermediário
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
        'GrupoProduto', 
        on_delete=models.PROTECT, 
        verbose_name="Grupo",
        related_name='produtos'
    )
    subgrupo = models.ForeignKey(
        'SubgrupoProduto', 
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
        null=True,
        blank=True,
        verbose_name="Estoque Mínimo"
    )
    estoque_atual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Estoque Atual"
    )

    # ====================================================================
    # CUSTOS ATUALIZADOS - SEPARAÇÃO MATERIAL E SERVIÇO
    # ====================================================================
    
    custo_material = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Custo Material",
        help_text="Custo de materiais/componentes do produto"
    )
    
    custo_servico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Custo Serviço",
        help_text="Custo de mão de obra/serviços do produto"
    )
    
    # CAMPO LEGACY - mantido para compatibilidade
    custo_medio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Custo Médio (Legacy)",
        help_text="Campo mantido para compatibilidade. Use custo_material + custo_servico"
    )

    # CAMPO LEGACY - mantido para compatibilidade
    custo_industrializacao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Custo Industrialização (Legacy)",
        help_text="Campo mantido para compatibilidade. Use custo_servico"
    )

    # Outros campos de preço
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
            models.Index(fields=['tipo_pi']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    # ====================================================================
    # PROPRIEDADES PARA CUSTOS TOTAIS
    # ====================================================================
    
    @property
    def custo_total(self):
        """Retorna a soma do custo material + custo serviço"""
        custo_mat = self.custo_material or 0
        custo_serv = self.custo_servico or 0
        return custo_mat + custo_serv
    
    @property
    def custo_total_legacy(self):
        """Retorna a soma dos campos legacy (compatibilidade)"""
        custo_base = self.custo_medio or 0
        custo_indust = self.custo_industrializacao or 0
        return custo_base + custo_indust
    
    # ====================================================================
    # MÉTODOS PARA CÁLCULO AUTOMÁTICO DE CUSTOS
    # ====================================================================
    
    def calcular_custo_por_estrutura(self):
        """
        Calcula custos de material e serviço baseado na estrutura de componentes
        Retorna (custo_material, custo_servico)
        """
        if not self.pode_ter_estrutura:
            return (0, 0)
        
        # Verificar se tem estrutura
        if not hasattr(self, 'componentes') or not self.componentes.exists():
            return (0, 0)
        
        custo_material_total = 0
        custo_servico_total = 0
        
        for componente in self.componentes.select_related('produto_filho'):
            produto_filho = componente.produto_filho
            quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100))
            
            # Calcular custo do componente
            if produto_filho.tipo == 'MP':
                # Matéria-prima sempre é material
                custo_unitario_material = produto_filho.custo_material or 0
                custo_unitario_servico = 0
                
            elif produto_filho.tipo == 'PI':
                if produto_filho.tipo_pi in ['SERVICO_INTERNO', 'SERVICO_EXTERNO']:
                    # Serviços são 100% serviço
                    custo_unitario_material = 0
                    custo_unitario_servico = produto_filho.custo_total
                else:
                    # Outros tipos de PI: pegar os custos separados
                    custo_unitario_material = produto_filho.custo_material or 0
                    custo_unitario_servico = produto_filho.custo_servico or 0
            else:
                # PA: pegar os custos separados
                custo_unitario_material = produto_filho.custo_material or 0
                custo_unitario_servico = produto_filho.custo_servico or 0
            
            # Aplicar quantidade
            custo_material_total += custo_unitario_material * quantidade_com_perda
            custo_servico_total += custo_unitario_servico * quantidade_com_perda
        
        return (custo_material_total, custo_servico_total)
    
    def aplicar_custo_calculado(self, salvar=True):
        """
        Aplica o custo calculado pela estrutura aos campos do produto
        """
        if not self.pode_ter_estrutura:
            return False
        
        custo_material, custo_servico = self.calcular_custo_por_estrutura()
        
        if custo_material > 0 or custo_servico > 0:
            self.custo_material = custo_material
            self.custo_servico = custo_servico
            
            # Manter compatibilidade com campos legacy
            self.custo_medio = custo_material
            self.custo_industrializacao = custo_servico
            
            if salvar:
                self.save(update_fields=[
                    'custo_material', 'custo_servico', 
                    'custo_medio', 'custo_industrializacao',
                    'atualizado_em', 'atualizado_por'
                ])
            
            return True
        
        return False
    
    def clean(self):
        """Validações personalizadas do produto"""
        super().clean()
        
        # O tipo do produto deve coincidir com o tipo do grupo
        if self.grupo and self.grupo.tipo_produto:
            self.tipo = self.grupo.tipo_produto
        
        # Validação tipo_pi para produtos PI
        if self.tipo == 'PI':
            if not self.tipo_pi:
                raise ValidationError({
                    'tipo_pi': 'Tipo do Produto Intermediário é obrigatório para produtos PI.'
                })
            
            # Validação específica para serviços externos (requer fornecedor)
            if self.tipo_pi == 'SERVICO_EXTERNO' and not self.fornecedor_principal:
                raise ValidationError({
                    'fornecedor_principal': 'Prestador principal é obrigatório para serviços externos.'
                })
                
            # Validação específica para produtos comprados (requer fornecedor)
            if self.tipo_pi == 'COMPRADO' and not self.fornecedor_principal:
                raise ValidationError({
                    'fornecedor_principal': 'Fornecedor principal é obrigatório para produtos comprados.'
                })
                
            # Validação específica para montados externos (requer fornecedor)
            if self.tipo_pi == 'MONTADO_EXTERNO' and not self.fornecedor_principal:
                raise ValidationError({
                    'fornecedor_principal': 'Fornecedor principal é obrigatório para produtos montados externamente.'
                })
        else:
            # Para MP e PA, tipo_pi deve ser None
            self.tipo_pi = None
    
    def save(self, *args, **kwargs):
        """
        Override do save para:
        1. Gerar código automático
        2. Calcular custos automaticamente para produtos montados
        3. Manter compatibilidade com campos legacy
        """
        # Garantir que o tipo coincida com o grupo
        if self.grupo and self.grupo.tipo_produto:
            self.tipo = self.grupo.tipo_produto
        
        # Gerar código automático se não existir e tiver subgrupo
        if not self.codigo and self.subgrupo:
            with transaction.atomic():
                subgrupo = SubgrupoProduto.objects.select_for_update().get(id=self.subgrupo.id)
                proximo_numero = subgrupo.ultimo_numero + 1
                
                if proximo_numero > 99999:
                    raise ValidationError(
                        f'Limite de produtos atingido para o subgrupo {subgrupo.codigo_completo}. '
                        f'Máximo permitido: 99999 produtos.'
                    )
                
                self.codigo = f"{self.grupo.codigo}.{subgrupo.codigo}.{proximo_numero:05d}"
                subgrupo.ultimo_numero = proximo_numero
                subgrupo.save(update_fields=['ultimo_numero'])
        
        # ============================================================
        # CÁLCULO AUTOMÁTICO DE CUSTOS PARA PRODUTOS MONTADOS
        # ============================================================
        
        # Verificar se deve calcular custos automaticamente
        deve_calcular_custos = (
            self.tipo == 'PI' and 
            self.tipo_pi in ['MONTADO_INTERNO', 'MONTADO_EXTERNO'] and
            self.pk  # Só calcular se o produto já existe (tem estrutura)
        )
        
        if deve_calcular_custos:
            try:
                # Tentar calcular custos pela estrutura
                custo_material_calc, custo_servico_calc = self.calcular_custo_por_estrutura()
                
                if custo_material_calc > 0 or custo_servico_calc > 0:
                    # Aplicar custos calculados
                    self.custo_material = custo_material_calc
                    self.custo_servico = custo_servico_calc
                    
                    # Manter compatibilidade com campos legacy
                    self.custo_medio = custo_material_calc
                    self.custo_industrializacao = custo_servico_calc
                    
                    # Log da operação (opcional)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f'Custos recalculados automaticamente para {self.codigo}: '
                        f'Material: R$ {custo_material_calc:.2f}, '
                        f'Serviço: R$ {custo_servico_calc:.2f}'
                    )
            
            except Exception as e:
                # Se falhar o cálculo, apenas logar o erro e continuar
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Falha ao calcular custos para {self.codigo}: {str(e)}')
        
        # Salvar o produto
        super().save(*args, **kwargs)
    
    # ====================================================================
    # MÉTODOS E PROPRIEDADES EXISTENTES (MANTIDOS)
    # ====================================================================
    
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
            'SERVICO_INTERNO': 'bg-secondary',
            'SERVICO_EXTERNO': 'bg-dark',
        }
        return badges.get(self.tipo_pi, 'bg-primary')
    
    @property
    def disponibilidade_info(self):
        """Informações sobre disponibilidade para o motor de regras"""
        if not self.disponivel:
            return {
                'disponivel': False,
                'motivo': self.motivo_indisponibilidade,
                'tipo': 'bloqueio_manual'
            }
        
        if self.controla_estoque and self.estoque_atual <= (self.estoque_minimo or 0):
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


# ====================================================================
# CLASSE ESTRUTURAPRODUTO ATUALIZADA
# ====================================================================

class EstruturaProduto(models.Model):
    """
    Define a estrutura/composição de produtos intermediários e acabados
    ATUALIZADA PARA SUPORTAR TIPOS DE PI E CÁLCULO AUTOMÁTICO
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
    
    def save(self, *args, **kwargs):
        """
        Override do save para recalcular custos do produto pai automaticamente
        """
        super().save(*args, **kwargs)
        
        # Recalcular custos do produto pai após salvar componente
        if self.produto_pai and self.produto_pai.pode_ter_estrutura:
            try:
                self.produto_pai.aplicar_custo_calculado(salvar=True)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f'Falha ao recalcular custos do produto pai {self.produto_pai.codigo} '
                    f'após salvar componente: {str(e)}'
                )
    
    def delete(self, *args, **kwargs):
        """
        Override do delete para recalcular custos do produto pai após remoção
        """
        produto_pai = self.produto_pai
        super().delete(*args, **kwargs)
        
        # Recalcular custos do produto pai após remover componente
        if produto_pai and produto_pai.pode_ter_estrutura:
            try:
                produto_pai.aplicar_custo_calculado(salvar=True)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f'Falha ao recalcular custos do produto pai {produto_pai.codigo} '
                    f'após remover componente: {str(e)}'
                )
    
    @property
    def quantidade_com_perda(self):
        """Retorna quantidade considerando a perda"""
        return self.quantidade * (1 + (self.percentual_perda / 100))
    
    @property
    def custo_total_componente(self):
        """Retorna custo total do componente (quantidade * preço * perda)"""
        custo_unitario = self.produto_filho.custo_total or 0
        return custo_unitario * self.quantidade_com_perda