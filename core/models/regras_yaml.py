# core/models/regras_yaml.py - Sistema de Regras YAML SIMPLES - CORRIGIDO

import yaml
import json
from decimal import Decimal
from django.db import models
from django.conf import settings  # ✅ ADICIONADO
from django.core.exceptions import ValidationError
from core.models import Produto


class TipoRegra(models.TextChoices):
    """Tipos de regras disponíveis"""
    CABINE = 'cabine', 'Cabine'
    CARRINHO = 'carrinho', 'Carrinho'
    TRACAO = 'tracao', 'Tração'
    SISTEMAS = 'sistemas', 'Sistemas'


class RegraYAML(models.Model):
    """
    Modelo para armazenar regras de cálculo em formato YAML
    Substitui o motor de regras hard-coded por configurações editáveis
    """
    tipo = models.CharField(
        max_length=20,
        choices=TipoRegra.choices,
        unique=True,
        help_text="Tipo da regra (cabine, carrinho, tração, sistemas)"
    )
    
    nome = models.CharField(
        max_length=100,
        help_text="Nome descritivo da regra"
    )
    
    descricao = models.TextField(
        blank=True,
        help_text="Descrição detalhada do que a regra faz"
    )
    
    conteudo_yaml = models.TextField(
        help_text="Conteúdo da regra em formato YAML"
    )
    
    versao = models.PositiveIntegerField(
        default=1,
        help_text="Versão da regra para controle de mudanças"
    )
    
    ativa = models.BooleanField(
        default=True,
        help_text="Se a regra está ativa e deve ser utilizada"
    )
    
    validado = models.BooleanField(
        default=False,
        help_text="Se a regra foi validada e todos os códigos existem"
    )
    
    ultimo_erro = models.TextField(
        blank=True,
        help_text="Último erro encontrado na validação"
    )
    
    # Auditoria - ✅ CORRIGIDO
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ CORRIGIDO: settings.AUTH_USER_MODEL
        on_delete=models.PROTECT,
        related_name='regras_yaml_criadas'
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ CORRIGIDO: settings.AUTH_USER_MODEL
        on_delete=models.PROTECT,
        related_name='regras_yaml_atualizadas'
    )
    
    class Meta:
        verbose_name = "Regra YAML"
        verbose_name_plural = "Regras YAML"
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome} (v{self.versao})"
    
    def clean(self):
        """Validações do modelo"""
        super().clean()
        
        # Validar YAML
        try:
            yaml.safe_load(self.conteudo_yaml)
        except yaml.YAMLError as e:
            raise ValidationError({
                'conteudo_yaml': f'YAML inválido: {str(e)}'
            })
    
    def save(self, *args, **kwargs):
        """Override do save para incrementar versão"""
        # Incrementar versão se o conteúdo mudou
        if self.pk:
            regra_anterior = RegraYAML.objects.get(pk=self.pk)
            if regra_anterior.conteudo_yaml != self.conteudo_yaml:
                self.versao += 1
                self.validado = False  # Revalidar quando mudou
        
        super().save(*args, **kwargs)
    
    def get_dados_yaml(self):
        """Retorna os dados do YAML como dicionário Python"""
        try:
            return yaml.safe_load(self.conteudo_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"Erro ao parsear YAML: {str(e)}")
    
    def validar_codigos_produtos(self):
        """
        Valida se todos os códigos de produtos referenciados no YAML existem
        """
        try:
            dados = yaml.safe_load(self.conteudo_yaml)
            codigos_faltantes = []
            
            def extrair_codigos(obj, caminho=""):
                """Extrai recursivamente todos os códigos de produto"""
                if isinstance(obj, dict):
                    for chave, valor in obj.items():
                        novo_caminho = f"{caminho}.{chave}" if caminho else chave
                        
                        if chave == 'codigo_produto':
                            # Verificar se o código existe
                            if not Produto.objects.filter(codigo=valor, disponivel=True).exists():
                                codigos_faltantes.append(f"{novo_caminho}: {valor}")
                        
                        elif isinstance(valor, (dict, list)):
                            extrair_codigos(valor, novo_caminho)
                
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        novo_caminho = f"{caminho}[{i}]"
                        extrair_codigos(item, novo_caminho)
            
            extrair_codigos(dados)
            
            if codigos_faltantes:
                self.ultimo_erro = f"Códigos não encontrados:\n" + "\n".join(codigos_faltantes)
                self.validado = False
            else:
                self.ultimo_erro = ""
                self.validado = True
            
            return self.validado
            
        except Exception as e:
            self.ultimo_erro = f"Erro na validação: {str(e)}"
            self.validado = False
            return False