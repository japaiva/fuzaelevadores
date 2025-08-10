# core/forms/regras_yaml.py - Formulário SIMPLES para Regras YAML

import yaml
from django import forms
from django.core.exceptions import ValidationError
from core.models.regras_yaml import RegraYAML, TipoRegra
from .base import BaseModelForm, AuditMixin


class RegraYAMLForm(BaseModelForm, AuditMixin):
    """Formulário simples para edição de regras YAML"""
    
    class Meta:
        model = RegraYAML
        fields = ['tipo', 'nome', 'descricao', 'conteudo_yaml', 'ativa']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome descritivo da regra'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do que a regra faz...'
            }),
            'conteudo_yaml': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 20,
                'placeholder': 'Digite o conteúdo YAML aqui...'
            }),
            'ativa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'tipo': 'Tipo da Regra',
            'nome': 'Nome',
            'descricao': 'Descrição',
            'conteudo_yaml': 'Conteúdo YAML',
            'ativa': 'Regra Ativa'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar choices
        self.fields['tipo'].choices = TipoRegra.choices
        
        # Tornar campos obrigatórios
        self.fields['tipo'].required = True
        self.fields['nome'].required = True
        self.fields['conteudo_yaml'].required = True
        
        # Help texts
        self.fields['tipo'].help_text = "Tipo de cálculo que a regra controla"
        self.fields['nome'].help_text = "Nome único para identificar a regra"
        self.fields['conteudo_yaml'].help_text = "Estrutura YAML com as regras de cálculo"
        
        # Se é edição, mostrar informações extras
        if self.instance.pk:
            self.fields['nome'].help_text = f"Versão atual: {self.instance.versao}"
            
            # Mostrar status de validação
            if self.instance.validado:
                self.fields['ativa'].help_text = "✅ Regra validada e pronta para uso"
            else:
                self.fields['ativa'].help_text = f"⚠️ Regra precisa ser validada"
                if self.instance.ultimo_erro:
                    self.fields['ativa'].help_text += f". Erro: {self.instance.ultimo_erro}"
        
        # Exemplo baseado no tipo
        if not self.instance.pk:
            self.fields['conteudo_yaml'].widget.attrs['placeholder'] = self._get_exemplo_yaml()
    
    def clean_conteudo_yaml(self):
        """Validar sintaxe YAML"""
        conteudo = self.cleaned_data.get('conteudo_yaml')
        
        if not conteudo:
            raise ValidationError('Conteúdo YAML é obrigatório.')
        
        try:
            # Tentar parsear o YAML
            dados = yaml.safe_load(conteudo)
            
            # Verificar se não está vazio
            if not dados:
                raise ValidationError('YAML não pode estar vazio.')
            
            # Verificar estrutura básica
            tipo = self.cleaned_data.get('tipo')
            if tipo and tipo not in dados:
                raise ValidationError(f'YAML deve conter a seção "{tipo}" no nível raiz.')
            
        except yaml.YAMLError as e:
            raise ValidationError(f'YAML inválido: {str(e)}')
        
        return conteudo
    
    def clean(self):
        """Validações extras"""
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        
        # Verificar se já existe regra ativa para este tipo (apenas para criação)
        if not self.instance.pk and tipo:
            if RegraYAML.objects.filter(tipo=tipo, ativa=True).exists():
                self.add_error('tipo', f'Já existe uma regra ativa para o tipo "{tipo}". Desative a existente primeiro.')
        
        return cleaned_data
    
    def _get_exemplo_yaml(self):
        """Exemplo básico de YAML para cabine"""
        return """cabine:
  # 1) PAINEL (mesmo produto para laterais e teto)
  painel_catalogo:
    - material: "Inox 304"
      espessura: "1,5"
      codigo_produto: "01.01.00014"
    - material: "Inox 430"
      espessura: "1,5"
      codigo_produto: "01.01.00017"
      
  # 2) FIXAÇÃO DOS PAINÉIS
  fixacao_paineis:
    codigo_produto: "01.04.00009"
    qty_formula: "13 * pnl.lateral + 2 * pnl.fundo + 2 * pnl.teto"
    
  # 3) PISO
  piso:
    empresa_antiderrapante: "01.01.00005"
    empresa_outros: "01.01.00008"
    cliente: "01.01.00008"
    
  # 4) FIXAÇÃO DO PISO
  fixacao_piso:
    codigo_produto: "01.04.00013"
    qty_formula: "13 * chp.piso"
"""


class RegraYAMLFiltroForm(forms.Form):
    """Formulário para filtros na listagem de regras"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
        ('validado', 'Validados'),
        ('erro', 'Com Erro'),
    ]
    
    tipo = forms.ChoiceField(
        choices=[('', 'Todos os Tipos')] + list(TipoRegra.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por nome ou descrição...'
        })
    )