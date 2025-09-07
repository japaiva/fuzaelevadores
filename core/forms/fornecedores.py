# core/forms/fornecedores.py

"""
Formulários relacionados a fornecedores
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from core.models import Fornecedor, FornecedorProduto, Produto
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, ValidacaoComumMixin, MoneyInput, QuantityInput


class FornecedorForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """Formulário para cadastro de fornecedores"""
    
    class Meta:
        model = Fornecedor
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 'contato_principal',
            'telefone', 'email', 'endereco', 'ativo'
        ]
        widgets = {
            'razao_social': forms.TextInput(attrs={
                'placeholder': 'Razão social do fornecedor'
            }),
            'nome_fantasia': forms.TextInput(attrs={
                'placeholder': 'Nome fantasia (opcional)'
            }),
            'cnpj': forms.TextInput(attrs={
                'data-mask': '00.000.000/0000-00',
                'placeholder': '00.000.000/0000-00'
            }),
            'contato_principal': forms.TextInput(attrs={
                'placeholder': 'Nome do contato principal'
            }),
            'telefone': forms.TextInput(attrs={
                'data-mask': '(00) 00000-0000',
                'placeholder': '(00) 00000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'email@fornecedor.com'
            }),
            'endereco': forms.Textarea(attrs={
                'rows': 3
            }),
        }
        labels = {
            'razao_social': 'Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'cnpj': 'CNPJ',
            'contato_principal': 'Contato Principal',
            'telefone': 'Telefone',
            'email': 'Email',
            'endereco': 'Endereço',
            'ativo': 'Fornecedor Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['razao_social'].required = True
    
    def clean_cnpj(self):
        """Validar CNPJ"""
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remove caracteres não numéricos
            import re
            cnpj_numerico = re.sub(r'\D', '', cnpj)
            
            if len(cnpj_numerico) != 14:
                raise ValidationError('CNPJ deve ter 14 dígitos.')
            
            # Verificar unicidade
            fornecedores_existentes = Fornecedor.objects.filter(cnpj=cnpj_numerico)
            
            # Se for edição, excluir o próprio fornecedor da verificação
            if self.instance.pk:
                fornecedores_existentes = fornecedores_existentes.exclude(pk=self.instance.pk)
            
            if fornecedores_existentes.exists():
                raise ValidationError('Já existe um fornecedor com este CNPJ.')
            
            return cnpj_numerico
        
        return cnpj


class FornecedorProdutoForm(BaseModelForm, AuditMixin):
    """Formulário para relacionamento fornecedor-produto"""
    
    class Meta:
        model = FornecedorProduto
        fields = [
            'fornecedor', 'codigo_fornecedor', 'preco_unitario', 'prioridade',
            'prazo_entrega', 'quantidade_minima', 'observacoes', 'ativo'
        ]
        widgets = {
            'codigo_fornecedor': forms.TextInput(attrs={
                'placeholder': 'Código usado pelo fornecedor'
            }),
            'preco_unitario': MoneyInput(),
            'prazo_entrega': forms.NumberInput(attrs={
                'min': '0',
                'step': '1',
                'placeholder': 'Dias'
            }),
            'quantidade_minima': QuantityInput(),
            'observacoes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Condições especiais, descontos, etc.'
            }),
        }
        labels = {
            'fornecedor': 'Fornecedor',
            'codigo_fornecedor': 'Código do Fornecedor',
            'preco_unitario': 'Preço Unitário',
            'prioridade': 'Prioridade',
            'prazo_entrega': 'Prazo Entrega (dias)',
            'quantidade_minima': 'Quantidade Mínima',
            'observacoes': 'Observações',
            'ativo': 'Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas fornecedores ativos
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
        
        # Campos obrigatórios
        self.fields['fornecedor'].required = True
        self.fields['prioridade'].required = True
    
    def clean_preco_unitario(self):
        """Validar preço unitário"""
        preco = self.cleaned_data.get('preco_unitario')
        if preco is not None and preco <= 0:
            raise ValidationError('Preço unitário deve ser maior que zero.')
        return preco
    
    def clean_quantidade_minima(self):
        """Validar quantidade mínima"""
        quantidade = self.cleaned_data.get('quantidade_minima')
        if quantidade is not None and quantidade <= 0:
            raise ValidationError('Quantidade mínima deve ser maior que zero.')
        return quantidade


# Formset para gerenciar múltiplos fornecedores por produto
FornecedorProdutoFormSet = inlineformset_factory(
    Produto,
    FornecedorProduto,
    form=FornecedorProdutoForm,
    extra=1,
    can_delete=True,
    fields=['fornecedor', 'codigo_fornecedor', 'preco_unitario', 'prioridade', 'prazo_entrega', 'ativo']
)


class FornecedorFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de fornecedores"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por razão social, nome fantasia ou CNPJ...'


class CotacaoForm(forms.Form):
    """Formulário para solicitação de cotação"""
    
    fornecedores = forms.ModelMultipleChoiceField(
        queryset=Fornecedor.objects.filter(ativo=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Fornecedores para Cotação'
    )
    
    produtos = forms.ModelMultipleChoiceField(
        queryset=Produto.objects.filter(status='ATIVO', disponivel=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Produtos para Cotação'
    )
    
    data_limite = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Data Limite para Resposta'
    )
    
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Informações adicionais para a cotação...'
        }),
        required=False,
        label='Observações'
    )
    
    def clean_data_limite(self):
        """Validar data limite"""
        from datetime import date
        data_limite = self.cleaned_data.get('data_limite')
        
        if data_limite and data_limite <= date.today():
            raise ValidationError('Data limite deve ser no futuro.')
        
        return data_limite


class AvaliacaoFornecedorForm(forms.Form):
    """Formulário para avaliação de fornecedores"""
    
    NOTA_CHOICES = [
        (1, '1 - Muito Ruim'),
        (2, '2 - Ruim'),
        (3, '3 - Regular'),
        (4, '4 - Bom'),
        (5, '5 - Excelente'),
    ]
    
    qualidade_produtos = forms.ChoiceField(
        choices=NOTA_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Qualidade dos Produtos'
    )
    
    pontualidade_entrega = forms.ChoiceField(
        choices=NOTA_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Pontualidade na Entrega'
    )
    
    atendimento = forms.ChoiceField(
        choices=NOTA_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Qualidade do Atendimento'
    )
    
    preco_competitivo = forms.ChoiceField(
        choices=NOTA_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Preço Competitivo'
    )
    
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Comentários sobre o fornecedor...'
        }),
        required=False,
        label='Observações'
    )
    
    recomendaria = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label='Recomendaria este fornecedor'
    )