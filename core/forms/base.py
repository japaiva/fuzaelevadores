# core/forms/base.py

"""
Classes base e utilitários compartilhados para formulários
"""

from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
import re

# Importações de utilitários
from core.utils.view_utils import CustomDateInput, CustomDateTimeInput, DateAwareModelForm

# Import choices from the new choices.py file
from core.choices import (
    get_nivel_usuario_choices,
    get_tipo_pessoa_choices,
    get_tipo_produto_choices,
    get_status_pedido_choices,
    get_prioridade_pedido_choices,
    ESTADOS_BRASIL
)


class BaseModelForm(forms.ModelForm):
    """Classe base para formulários do sistema com funcionalidades comuns"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS padrão automaticamente
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            
            # Adicionar classes CSS baseadas no tipo de widget
            if isinstance(field.widget, forms.CheckboxInput):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.Textarea):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
                if 'rows' not in field.widget.attrs:
                    field.widget.attrs['rows'] = 3
            else:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'


class BaseFiltroForm(forms.Form):
    """Classe base para formulários de filtro"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar...'
        }),
        label='Buscar'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS pequenas para filtros
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            elif isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            elif isinstance(field.widget, CustomDateInput):
                field.widget.attrs.update({'class': 'form-control form-control-sm'})


# Widgets customizados comuns
class MoneyInput(forms.TextInput): # ALTERADO PARA forms.TextInput
    """Widget para campos monetários"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'inputmode': 'decimal', # Sugere teclado numérico em dispositivos móveis
            'pattern': '[0-9]*[.,]?[0-9]*', # Validação regex básica para ponto ou vírgula
            'placeholder': '0,00'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class PercentageInput(forms.TextInput): # ALTERADO PARA forms.TextInput
    """Widget para campos de porcentagem"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'inputmode': 'decimal',
            'pattern': '[0-9]*[.,]?[0-9]*',
            'placeholder': '0,00'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class QuantityInput(forms.TextInput): # ALTERADO PARA forms.TextInput
    """Widget para campos de quantidade"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'inputmode': 'decimal',
            'pattern': '[0-9]*[.,]?[0-9]*',
            'placeholder': '0,00'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


# Mixins para funcionalidades comuns
class AuditMixin:
    """Mixin para formulários que precisam de auditoria"""
    
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        
        if user:
            if not instance.pk:
                # Novo registro
                if hasattr(instance, 'criado_por'):
                    instance.criado_por = user
            
            # Atualização
            if hasattr(instance, 'atualizado_por'):
                instance.atualizado_por = user
        
        if commit:
            instance.save()
        
        return instance


class ValidacaoComumMixin:
    """Mixin com validações comuns do sistema"""
    
    def clean_telefone(self):
        """Validação comum para telefones"""
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove caracteres não numéricos
            telefone_numerico = re.sub(r'\D', '', telefone)
            if len(telefone_numerico) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')
        return telefone
    
    def clean_email(self):
        """Validação comum para emails"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_cep(self):
        """Validação comum para CEP"""
        cep = self.cleaned_data.get('cep')
        if cep:
            cep_numerico = re.sub(r'\D', '', cep)
            if len(cep_numerico) != 8:
                raise ValidationError('CEP deve ter 8 dígitos.')
            return f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        return cep


# Validadores comuns
def validar_positivo(value):
    """Validador para números positivos"""
    if value is not None and value <= 0:
        raise ValidationError('Este valor deve ser maior que zero.')


def validar_porcentagem(value):
    """Validador para porcentagens (0-100)"""
    if value is not None and (value < 0 or value > 100):
        raise ValidationError('Porcentagem deve estar entre 0 e 100.')


def validar_codigo_sequencial(value):
    """Validador para códigos sequenciais (apenas números)"""
    if value and not value.isdigit():
        raise ValidationError('Código deve conter apenas números.')