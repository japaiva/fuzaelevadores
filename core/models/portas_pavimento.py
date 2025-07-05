# core/models/portas_pavimento.py - VERSÃO ENXUTA

from django.db import models
from decimal import Decimal

class PortaPavimento(models.Model):
    MODELO_CHOICES = [
        ('Automática', 'Automática'),
        ('Pantográfica', 'Pantográfica'),
        ('Pivotante', 'Pivotante'),
        ('Guilhotina', 'Guilhotina'),
    ]
    
    MATERIAL_CHOICES = [
        ('Inox 430', 'Inox 430'),
        ('Inox 304', 'Inox 304'),
        ('Chapa Pintada', 'Chapa Pintada'),
        ('Alumínio', 'Alumínio'),
    ]
    
    proposta = models.ForeignKey('Proposta', on_delete=models.CASCADE, related_name='portas_pavimento')
    andar = models.IntegerField(verbose_name="Andar")
    nome_andar = models.CharField(max_length=50, verbose_name="Nome do Andar")
    modelo = models.CharField(max_length=20, choices=MODELO_CHOICES)
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Porta do Pavimento"
        verbose_name_plural = "Portas dos Pavimentos"
        ordering = ['proposta', 'andar']
        unique_together = ['proposta', 'andar']
    
    def __str__(self):
        return f"{self.proposta.numero} - {self.nome_andar} - {self.modelo} {self.material}"
    
    def save(self, *args, **kwargs):
        if not self.nome_andar:
            if self.andar == 0:
                self.nome_andar = "Térreo"
            else:
                self.nome_andar = f"{self.andar}º Andar"
        super().save(*args, **kwargs)