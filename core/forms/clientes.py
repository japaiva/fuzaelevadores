# core/forms/clientes.py

"""
Formulários relacionados a clientes
"""

from django import forms
from django.core.exceptions import ValidationError
import re

from core.models import Cliente
from core.utils.validators import validar_cpf, validar_cnpj, validar_cpf_cnpj_unico
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, ValidacaoComumMixin
from core.choices import get_tipo_pessoa_choices, ESTADOS_BRASIL


class ClienteForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """Formulário completo para cliente no Portal Gestor"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome', 'nome_fantasia', 'cpf_cnpj',
            'telefone', 'email', 'contato_principal',
            'cep', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'estado', 'observacoes'
        ]
        widgets = {
            'tipo_pessoa': forms.Select(attrs={
                'onchange': 'toggleCpfCnpjMask(this.value)'
            }),
            'nome': forms.TextInput(attrs={

            }),
            'nome_fantasia': forms.TextInput(attrs={

            }),
            'cpf_cnpj': forms.TextInput(attrs={

                'data-mask': 'cpf'
            }),
            'telefone': forms.TextInput(attrs={
                'placeholder': '(11) 99999-9999',  
                'data-mask': 'phone'
            }),
            'email': forms.EmailInput(attrs={

            }),
            'contato_principal': forms.TextInput(attrs={

            }),
            'cep': forms.TextInput(attrs={
                'placeholder': '99999-999',  
                'data-mask': 'cep'
            }),
            'endereco': forms.TextInput(attrs={

            }),
            'numero': forms.TextInput(attrs={
  
            }),
            'complemento': forms.TextInput(attrs={

            }),
            'bairro': forms.TextInput(attrs={

            }),
            'cidade': forms.TextInput(attrs={

            }),
            'estado': forms.Select(choices=ESTADOS_BRASIL), # Use ESTADOS_BRASIL from core.choices
            'observacoes': forms.Textarea(attrs={
                'rows': 3

            }),
        }
        labels = {
            'tipo_pessoa': 'Tipo de Pessoa',
            'nome': 'Nome/Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'cpf_cnpj': 'CPF/CNPJ',
            'telefone': 'Telefone',
            'email': 'Email',
            'contato_principal': 'Contato Principal',
            'cep': 'CEP',
            'endereco': 'Logradouro',
            'numero': 'Número',
            'complemento': 'Complemento',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'Estado',
            'observacoes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_pessoa'].choices = get_tipo_pessoa_choices() # Set choices dynamically
        
        # Campos obrigatórios
        self.fields['tipo_pessoa'].required = True
        self.fields['nome'].required = True
    
    def clean_cpf_cnpj(self):
        """Validação específica do CPF/CNPJ"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        tipo_pessoa = self.cleaned_data.get('tipo_pessoa')
        
        if not cpf_cnpj:
            return cpf_cnpj
        
        # Remove caracteres não numéricos
        cpf_cnpj_numerico = re.sub(r'\D', '', cpf_cnpj)
        
        # Validar formato baseado no tipo de pessoa
        if tipo_pessoa == 'PF':
            try:
                return validar_cpf(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        elif tipo_pessoa == 'PJ':
            try:
                return validar_cnpj(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        
        return cpf_cnpj
    
    def clean_estado(self):
        """Validar estado"""
        estado = self.cleaned_data.get('estado')
        if estado:
            estado = estado.upper()
            # The choice widget handles the valid options now.
            # If you need stricter validation (e.g., only specific states based on business rules),
            # you would add it here. For now, the `forms.Select` with `ESTADOS_BRASIL` is sufficient.
        return estado
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        cpf_cnpj = cleaned_data.get('cpf_cnpj')
        
        # Validar unicidade se CPF/CNPJ foi fornecido
        if cpf_cnpj:
            try:
                validar_cpf_cnpj_unico(cpf_cnpj, instance=self.instance, model_class=Cliente)
            except ValidationError as e:
                self.add_error('cpf_cnpj', e.message)
        
        return cleaned_data


class ClienteCreateForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """Formulário simplificado para criação rápida de cliente no Portal Vendedor"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome', 'nome_fantasia', 'cpf_cnpj',
            'telefone', 'email', 'contato_principal',
            'endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep'
        ]
        widgets = {
            'tipo_pessoa': forms.Select(attrs={
                'onchange': 'toggleCpfCnpjMask(this.value)'
            }),
            'nome': forms.TextInput(attrs={

                'required': True
            }),
            'nome_fantasia': forms.TextInput(attrs={

            }),
            'cpf_cnpj': forms.TextInput(attrs={

                'data-mask': 'cpf'
            }),
            'telefone': forms.TextInput(attrs={
                'placeholder': '(11) 99999-9999',
                'data-mask': 'phone'
            }),
            'email': forms.EmailInput(attrs={

            }),
            'contato_principal': forms.TextInput(attrs={

            }),
            'endereco': forms.TextInput(attrs={

            }),
            'numero': forms.TextInput(attrs={

            }),
            'bairro': forms.TextInput(attrs={
  
            }),
            'cidade': forms.TextInput(attrs={

            }),
            'estado': forms.Select(choices=ESTADOS_BRASIL), # Use ESTADOS_BRASIL from core.choices
            'cep': forms.TextInput(attrs={
                'placeholder': '99999-999',  
                'data-mask': 'cep'
            }),
        }
        labels = {
            'tipo_pessoa': 'Tipo',
            'nome': 'Nome/Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'cpf_cnpj': 'CPF/CNPJ',
            'telefone': 'Telefone',
            'email': 'Email',
            'contato_principal': 'Contato',
            'endereco': 'Endereço',
            'numero': 'Número',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'UF',
            'cep': 'CEP',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_pessoa'].choices = get_tipo_pessoa_choices() # Set choices dynamically

        self.fields['nome'].required = True
        self.fields['tipo_pessoa'].required = True
        
        # Aplicar classes menores para formulário de criação rápida
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                # Check if 'form-control' is already there to avoid duplicates, then add size
                if 'form-control' in field.widget.attrs.get('class', ''):
                    if 'form-control-sm' not in field.widget.attrs.get('class', ''):
                        field.widget.attrs['class'] += ' form-control-sm'
                elif isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Textarea, forms.Select)):
                    field.widget.attrs['class'] = 'form-control form-control-sm'

    def clean_cpf_cnpj(self):
        """Validação específica do CPF/CNPJ"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        tipo_pessoa = self.cleaned_data.get('tipo_pessoa')
        
        if not cpf_cnpj:
            return cpf_cnpj
        
        # Remove caracteres não numéricos
        cpf_cnpj_numerico = re.sub(r'\D', '', cpf_cnpj)
        
        # Validar formato baseado no tipo de pessoa
        if tipo_pessoa == 'PF':
            try:
                return validar_cpf(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        elif tipo_pessoa == 'PJ':
            try:
                return validar_cnpj(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        
        return cpf_cnpj
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        cpf_cnpj = cleaned_data.get('cpf_cnpj')
        
        # Validar unicidade se CPF/CNPJ foi fornecido
        if cpf_cnpj:
            try:
                validar_cpf_cnpj_unico(cpf_cnpj, instance=self.instance, model_class=Cliente)
            except ValidationError as e:
                self.add_error('cpf_cnpj', e.message)
        
        return cleaned_data


class ClienteFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de clientes"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    tipo = forms.ChoiceField(
        required=False,
        label='Tipo'
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = [('', 'Todos')] + get_tipo_pessoa_choices() # Set choices dynamically
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por nome, CPF/CNPJ ou email...'


class BuscaClienteForm(forms.Form):
    """Formulário para busca rápida de clientes"""
    
    q = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite nome, CPF/CNPJ ou email...',
            'autocomplete': 'off'
        }),
        label='Buscar Cliente'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].required = True


class ClienteEnderecoForm(forms.ModelForm):
    """Formulário específico para endereço do cliente"""
    
    class Meta:
        model = Cliente
        fields = ['cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado']
        widgets = {
            'cep': forms.TextInput(attrs={
                'placeholder': '00000-000',
                'data-mask': 'cep',
                'onblur': 'buscarCep(this.value)'
            }),
            'endereco': forms.TextInput(attrs={
                'placeholder': 'Rua, Avenida, etc.'
            }),
            'numero': forms.TextInput(attrs={
                'placeholder': 'Número'
            }),
            'complemento': forms.TextInput(attrs={
                'placeholder': 'Apto, Sala, etc.'
            }),
            'bairro': forms.TextInput(attrs={
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'placeholder': 'Cidade'
            }),
            'estado': forms.Select(choices=ESTADOS_BRASIL), # Use ESTADOS_BRASIL from core.choices
        }
        labels = {
            'cep': 'CEP',
            'endereco': 'Logradouro',
            'numero': 'Número',
            'complemento': 'Complemento',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'Estado',
        }


class ClienteContatoForm(forms.ModelForm):
    """Formulário específico para contato do cliente"""
    
    class Meta:
        model = Cliente
        fields = ['telefone', 'email', 'contato_principal']
        widgets = {
            'telefone': forms.TextInput(attrs={
                'placeholder': '(11) 99999-9999',
                'data-mask': 'phone'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'email@exemplo.com'
            }),
            'contato_principal': forms.TextInput(attrs={
                'placeholder': 'Nome do responsável'
            }),
        }
        labels = {
            'telefone': 'Telefone',
            'email': 'Email',
            'contato_principal': 'Contato Principal',
        }