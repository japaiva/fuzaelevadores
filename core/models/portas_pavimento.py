# core/models/portas_pavimento.py - VERSÃO ATUALIZADA COM MEZANINO

from django.db import models
from decimal import Decimal

class PortaPavimento(models.Model):
    MODELO_CHOICES = [
        ('Automática', 'Automática'),
        ('Pantográfica', 'Pantográfica'),
        ('Pivotante', 'Pivotante'),
        ('Guilhotina', 'Guilhotina'),
        ('Camarão', 'Camarão'),
        ('Cancela', 'Cancela'),
        ('Rampa', 'Rampa'),
    ]
    
    MATERIAL_CHOICES = [
        ('Inox 430', 'Inox 430'),
        ('Inox 304', 'Inox 304'),
        ('Chapa Pintada', 'Chapa Pintada'),
        ('Alumínio', 'Alumínio'),
    ]
    
    SAIDA_CHOICES = [
        ('normal', 'Normal'),
        ('oposta', 'Oposta'),
    ]
    
    ABERTURA_CHOICES = [
        ('direita', 'Direita'),
        ('esquerda', 'Esquerda'),
        ('central', 'Central'),
    ]
    
    # === CAMPOS EXISTENTES ===
    proposta = models.ForeignKey('Proposta', on_delete=models.CASCADE, related_name='portas_pavimento')
    andar = models.IntegerField(verbose_name="Andar")
    nome_andar = models.CharField(max_length=50, verbose_name="Nome do Andar")
    modelo = models.CharField(max_length=20, choices=MODELO_CHOICES)
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # === NOVOS CAMPOS ===
    ativo = models.BooleanField(
        default=True, 
        verbose_name="Pavimento Ativo",
        help_text="Desmarque se este pavimento não terá porta"
    )
    
    # Configurações únicas por pavimento
    saida = models.CharField(
        max_length=10,
        choices=SAIDA_CHOICES,
        default='normal',
        verbose_name="Saída do Elevador"
    )
    
    abertura_porta = models.CharField(
        max_length=10,
        choices=ABERTURA_CHOICES,
        default='direita',
        verbose_name="Abertura da Porta"
    )
    
    # Dimensões obrigatórias e únicas
    largura = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('0.80'),
        verbose_name="Largura (m)",
        help_text="Largura específica da porta deste pavimento"
    )
    
    altura = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('2.10'),
        verbose_name="Altura (m)",
        help_text="Altura específica da porta deste pavimento"
    )
    
    # Folhas (número de folhas da porta)
    folhas = models.CharField(
        max_length=10,
        choices=[
            ('2', '2 Folhas'),
            ('3', '3 Folhas'),
            ('4', '4 Folhas'),
        ],
        blank=True,
        verbose_name="Número de Folhas",
        help_text="Aplicável apenas para portas automáticas"
    )
    
    # Observações específicas do pavimento
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Características especiais deste pavimento"
    )
    
    class Meta:
        verbose_name = "Porta do Pavimento"
        verbose_name_plural = "Portas dos Pavimentos"
        ordering = ['proposta', 'andar']
        unique_together = ['proposta', 'andar']
    
    def __str__(self):
        status = "" if self.ativo else " (Inativo)"
        return f"{self.proposta.numero} - {self.nome_andar} - {self.modelo} {self.material}{status}"
    
    def save(self, *args, **kwargs):
        # Auto-gerar nome do andar se não informado
        if not self.nome_andar:
            if self.andar == 0:
                self.nome_andar = "Térreo"
            elif self.andar == 1:
                # ✅ NOVO: Andar 1 agora é Mezanino
                self.nome_andar = "Mezanino"
            elif self.andar < 0:
                self.nome_andar = f"Subsolo {abs(self.andar)}" if abs(self.andar) > 1 else "Subsolo"
            else:
                # ✅ AJUSTADO: Andares 2+ agora são numerados corretamente
                # Andar 2 = 1º Andar, Andar 3 = 2º Andar, etc.
                self.nome_andar = f"{self.andar - 1}º Andar"
        
        super().save(*args, **kwargs)
    
    @property
    def configuracao_resumo(self):
        """Retorna resumo da configuração desta porta"""
        resumo = f"{self.modelo} {self.material} - {self.largura}x{self.altura}m"
        
        if self.saida != 'normal':
            resumo += f" - Saída {self.saida}"
        
        if self.abertura_porta != 'direita':
            resumo += f" - Abertura {self.abertura_porta}"
            
        if self.folhas:
            resumo += f" - {self.folhas} folhas"
        
        return resumo
    
    @property
    def area_porta(self):
        """Calcula área da porta"""
        return float(self.largura) * float(self.altura)