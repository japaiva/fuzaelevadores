# core/models/clientes.py

"""
Models relacionados a clientes
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import re

from .base import TIPO_PESSOA_CHOICES
from core.utils.validators import validar_cpf, validar_cnpj, formatar_cpf, formatar_cnpj, validar_cpf_cnpj_unico


class Cliente(models.Model):
    """Cadastro básico de clientes com validação de CPF/CNPJ"""
    
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