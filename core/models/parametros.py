# core/models/parametros.py

"""
Models relacionados a parâmetros gerais do sistema
ATUALIZADO COM NOVOS CAMPOS DE COMPRAS
"""

from django.db import models
from django.conf import settings


class ParametrosGerais(models.Model):
    """Parâmetros gerais do sistema - ATUALIZADO"""
    
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
    
    # === NOVOS CAMPOS PARA COMPRAS ===
    comprador_responsavel = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Comprador Responsável",
        help_text="Nome do responsável pelas compras"
    )
    contato_compras = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Contato de Compras",
        help_text="Email ou telefone do setor de compras"
    )

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
    
    @property
    def endereco_completo(self):
        """Retorna endereço completo formatado"""
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
    def dados_empresa_completos(self):
        """Verifica se os dados básicos da empresa estão completos"""
        campos_obrigatorios = [
            self.razao_social,
            self.cnpj,
            self.endereco,
            self.cidade,
            self.telefone
        ]
        return all(campo for campo in campos_obrigatorios)
    
    @property
    def dados_compras_completos(self):
        """Verifica se os dados de compras estão completos"""
        return bool(self.comprador_responsavel and self.contato_compras)
    
    def save(self, *args, **kwargs):
        """Override para aplicar formatações"""
        
        # Formatar CEP se fornecido
        if self.cep:
            import re
            cep_numerico = re.sub(r'\D', '', self.cep)
            if len(cep_numerico) == 8:
                self.cep = f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        
        # Formatar CNPJ se fornecido
        if self.cnpj:
            import re
            cnpj_numerico = re.sub(r'\D', '', self.cnpj)
            if len(cnpj_numerico) == 14:
                self.cnpj = f"{cnpj_numerico[:2]}.{cnpj_numerico[2:5]}.{cnpj_numerico[5:8]}/{cnpj_numerico[8:12]}-{cnpj_numerico[12:]}"
        
        super().save(*args, **kwargs)