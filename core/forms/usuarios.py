# core/forms/usuarios.py

"""
Formulários relacionados a usuários e perfis
"""

from django import forms
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from core.models import Usuario # Keep this import, as the form uses the model directly
from .base import BaseModelForm, AuditMixin, ValidacaoComumMixin
from core.choices import get_nivel_usuario_choices # Import the function


class UsuarioForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """Formulário para criação e edição de usuários"""
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label="Confirmar Senha"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label="Senha"
    )
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'nivel', 
            'telefone', 'codigo_loja', 'codigo_vendedor', 'is_active'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Nome de usuário único'
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Nome'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'email@exemplo.com'
            }),
            'telefone': forms.TextInput(attrs={
                'placeholder': '(11) 99999-9999',
                'data-mask': 'phone'
            }),
            'codigo_loja': forms.TextInput(attrs={
                'maxlength': '3',
                'placeholder': '001'
            }),
            'codigo_vendedor': forms.TextInput(attrs={
                'maxlength': '3',
                'placeholder': '001'
            }),
        }
        labels = {
            'username': 'Nome de Usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
            'nivel': 'Nível de Acesso',
            'telefone': 'Telefone',
            'codigo_loja': 'Código da Loja',
            'codigo_vendedor': 'Código do Vendedor',
            'is_active': 'Usuário Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for nivel field dynamically
        self.fields['nivel'].choices = get_nivel_usuario_choices()

        # If estiver editando um usuário existente, não exigir senha
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = "Deixe em branco para manter a senha atual"
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
        
        # Campo obrigatórios
        self.fields['username'].required = True
        self.fields['first_name'].required = True
        self.fields['nivel'].required = True
    
    def clean_username(self):
        """Validar unicidade do username"""
        username = self.cleaned_data.get('username')
        if username:
            # Verificar se já existe outro usuário com o mesmo username
            usuarios_existentes = Usuario.objects.filter(username=username)
            
            # Se for edição, excluir o próprio usuário da verificação
            if self.instance.pk:
                usuarios_existentes = usuarios_existentes.exclude(pk=self.instance.pk)
            
            if usuarios_existentes.exists():
                raise ValidationError('Já existe um usuário com este nome.')
        
        return username
    
    def clean_codigo_loja(self):
        """Validar código da loja"""
        codigo_loja = self.cleaned_data.get('codigo_loja')
        if codigo_loja:
            if len(codigo_loja) != 3 or not codigo_loja.isdigit():
                raise ValidationError('O código da loja deve ter exatamente 3 dígitos numéricos.')
        return codigo_loja
    
    def clean_codigo_vendedor(self):
        """Validar código do vendedor"""
        codigo_vendedor = self.cleaned_data.get('codigo_vendedor')
        if codigo_vendedor:
            if len(codigo_vendedor) != 3 or not codigo_vendedor.isdigit():
                raise ValidationError('O código do vendedor deve ter exatamente 3 dígitos numéricos.')
        return codigo_vendedor
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        # Validar confirmação de senha
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "As senhas não coincidem.")
        
        # Validar força da senha para novos usuários
        if password and not self.instance.pk:
            if len(password) < 6:
                self.add_error('password', "A senha deve ter pelo menos 6 caracteres.")
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        """Override para codificar senha"""
        usuario = super().save(commit=False, user=user)
        
        # Se uma senha foi fornecida, codificá-la
        password = self.cleaned_data.get('password')
        if password:
            usuario.password = make_password(password)
        
        if commit:
            usuario.save()
        
        return usuario


class UsuarioFiltroForm(forms.Form):
    """Formulário para filtros na listagem de usuários"""
    
    # Use the function to get choices
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    nivel = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por nome, username ou email...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nivel'].choices = [('', 'Todos os Níveis')] + get_nivel_usuario_choices()


class AlterarSenhaForm(forms.Form):
    """Formulário para alterar senha do usuário"""
    
    senha_atual = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha atual'
        }),
        label='Senha Atual'
    )
    nova_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a nova senha'
        }),
        label='Nova Senha',
        min_length=6
    )
    confirmar_nova_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a nova senha'
        }),
        label='Confirmar Nova Senha'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_senha_atual(self):
        """Validar senha atual"""
        senha_atual = self.cleaned_data.get('senha_atual')
        if not self.user.check_password(senha_atual):
            raise ValidationError('Senha atual incorreta.')
        return senha_atual
    
    def clean(self):
        """Validar confirmação da nova senha"""
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_nova_senha = cleaned_data.get('confirmar_nova_senha')
        
        if nova_senha and confirmar_nova_senha:
            if nova_senha != confirmar_nova_senha:
                self.add_error('confirmar_nova_senha', 'As senhas não coincidem.')
        
        return cleaned_data
    
    def save(self):
        """Alterar a senha do usuário"""
        nova_senha = self.cleaned_data.get('nova_senha')
        self.user.set_password(nova_senha)
        self.user.save()
        return self.user