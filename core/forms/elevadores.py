# core/forms/elevadores.py

"""
Formulários relacionados ao motor de regras de elevadores
"""

from django import forms
from django.core.exceptions import ValidationError
import json

from core.models import (
    EspecificacaoElevador, OpcaoEspecificacao, RegraComponente,
    ComponenteDerivado, SimulacaoElevador, Produto
)
# Import the getter functions from core.choices
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, MoneyInput
from core.choices import (
    get_especificacao_elevador_tipo_choices,
    get_simulacao_elevador_status_choices
)


class EspecificacaoElevadorForm(BaseModelForm, AuditMixin):
    """Formulário para especificações de elevadores"""
    
    class Meta:
        model = EspecificacaoElevador
        fields = ['codigo', 'nome', 'tipo', 'descricao', 'obrigatoria', 'ordem', 'ativa']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ex: MAT, DIM, CAP...',
                'maxlength': '20'
            }),
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome da especificação'
            }),
            # Remove `choices` from widget definition here, set in __init__
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descrição da especificação...'
            }),
            'ordem': forms.NumberInput(attrs={
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
        }
        labels = {
            'codigo': 'Código',
            'nome': 'Nome',
            'tipo': 'Tipo',
            'descricao': 'Descrição',
            'obrigatoria': 'Especificação Obrigatória',
            'ordem': 'Ordem de Apresentação',
            'ativa': 'Ativa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for tipo field dynamically
        self.fields['tipo'].choices = get_especificacao_elevador_tipo_choices()

        # Campos obrigatórios
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        self.fields['tipo'].required = True
    
    def clean_codigo(self):
        """Validar unicidade do código"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Verificar se já existe outra especificação com o mesmo código
            especificacoes_existentes = EspecificacaoElevador.objects.filter(codigo=codigo)
            
            # Se for edição, excluir a própria especificação da verificação
            if self.instance.pk:
                especificacoes_existentes = especificacoes_existentes.exclude(pk=self.instance.pk)
            
            if especificacoes_existentes.exists():
                raise ValidationError('Já existe uma especificação com este código.')
        
        return codigo


class OpcaoEspecificacaoForm(BaseModelForm, AuditMixin):
    """Formulário para opções de especificações"""
    
    class Meta:
        model = OpcaoEspecificacao
        fields = [
            'especificacao', 'codigo', 'nome', 'descricao', 
            'valor_numerico', 'unidade', 'ordem', 'ativa'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ex: IN430, PT45...',
                'maxlength': '20'
            }),
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome da opção'
            }),
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descrição da opção...'
            }),
            'valor_numerico': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'unidade': forms.TextInput(attrs={
                'placeholder': 'kg, m, mm...',
                'maxlength': '10'
            }),
            'ordem': forms.NumberInput(attrs={
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
        }
        labels = {
            'especificacao': 'Especificação',
            'codigo': 'Código',
            'nome': 'Nome',
            'descricao': 'Descrição',
            'valor_numerico': 'Valor Numérico',
            'unidade': 'Unidade',
            'ordem': 'Ordem',
            'ativa': 'Ativa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas especificações ativas
        self.fields['especificacao'].queryset = EspecificacaoElevador.objects.filter(ativa=True).order_by('ordem', 'nome')
        
        # Campos obrigatórios
        self.fields['especificacao'].required = True
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
    
    def clean(self):
        """Validações personalizadas"""
        cleaned_data = super().clean()
        especificacao = cleaned_data.get('especificacao')
        codigo = cleaned_data.get('codigo')
        
        # Validar unicidade do código dentro da especificação
        if especificacao and codigo:
            opcoes_existentes = OpcaoEspecificacao.objects.filter(
                especificacao=especificacao, 
                codigo=codigo
            )
            
            # Se for edição, excluir a própria opção da verificação
            if self.instance.pk:
                opcoes_existentes = opcoes_existentes.exclude(pk=self.instance.pk)
            
            if opcoes_existentes.exists():
                self.add_error('codigo', 
                    f'Já existe uma opção com o código "{codigo}" nesta especificação.')
        
        return cleaned_data


class RegraComponenteForm(BaseModelForm, AuditMixin):
    """Formulário para regras de componentes"""
    
    class Meta:
        model = RegraComponente
        fields = [
            'nome', 'descricao', 'condicoes', 'componente', 
            'formula_quantidade', 'prioridade', 'ativa'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome da regra'
            }),
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descrição da regra...'
            }),
            'condicoes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '{"material": "Inox 430", "espessura": "1.2"}',
                'class': 'form-control font-monospace'
            }),
            'formula_quantidade': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Ex: altura * 2 + largura',
                'class': 'form-control font-monospace'
            }),
            'prioridade': forms.NumberInput(attrs={
                'min': '1',
                'step': '1',
                'placeholder': '100'
            }),
        }
        labels = {
            'nome': 'Nome da Regra',
            'descricao': 'Descrição',
            'condicoes': 'Condições (JSON)',
            'componente': 'Componente',
            'formula_quantidade': 'Fórmula de Quantidade',
            'prioridade': 'Prioridade',
            'ativa': 'Ativa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas produtos ativos
        self.fields['componente'].queryset = Produto.objects.filter(
            status='ATIVO',
            disponivel=True
        ).order_by('codigo')
        
        # Campos obrigatórios
        self.fields['nome'].required = True
        self.fields['componente'].required = True
        
        # Help texts
        self.fields['condicoes'].help_text = 'JSON com as condições para aplicar esta regra'
        self.fields['formula_quantidade'].help_text = 'Fórmula para calcular a quantidade (opcional)'
        self.fields['prioridade'].help_text = 'Menor número = maior prioridade'
    
    def clean_condicoes(self):
        """Validar JSON das condições"""
        condicoes = self.cleaned_data.get('condicoes')
        if condicoes:
            try:
                # Tentar fazer parse do JSON
                parsed_json = json.loads(condicoes)
                
                # Verificar se é um dicionário
                if not isinstance(parsed_json, dict):
                    raise ValidationError('Condições devem ser um objeto JSON válido.')
                
                # Verificar se não está vazio
                if not parsed_json:
                    raise ValidationError('Condições não podem estar vazias.')
                
                return condicoes
                
            except json.JSONDecodeError as e:
                raise ValidationError(f'JSON inválido: {str(e)}')
        
        return condicoes


class ComponenteDerivadoForm(BaseModelForm, AuditMixin):
    """Formulário para componentes derivados"""
    
    class Meta:
        model = ComponenteDerivado
        fields = [
            'componente_origem', 'componente_destino', 'tipo_calculo',
            'multiplicador', 'formula', 'ativa'
        ]
        widgets = {
            'multiplicador': forms.NumberInput(attrs={
                'step': '0.0001',
                'placeholder': '1.0000'
            }),
            'formula': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Fórmula personalizada...',
                'class': 'form-control font-monospace'
            }),
        }
        labels = {
            'componente_origem': 'Componente Origem',
            'componente_destino': 'Componente Destino',
            'tipo_calculo': 'Tipo de Cálculo',
            'multiplicador': 'Multiplicador',
            'formula': 'Fórmula Personalizada',
            'ativa': 'Ativa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas produtos ativos
        queryset_produtos = Produto.objects.filter(
            status='ATIVO',
            disponivel=True
        ).order_by('codigo')
        
        self.fields['componente_origem'].queryset = queryset_produtos
        self.fields['componente_destino'].queryset = queryset_produtos
        
        # Campos obrigatórios
        self.fields['componente_origem'].required = True
        self.fields['componente_destino'].required = True
        self.fields['tipo_calculo'].required = True
    
    def clean(self):
        """Validações personalizadas"""
        cleaned_data = super().clean()
        origem = cleaned_data.get('componente_origem')
        destino = cleaned_data.get('componente_destino')
        
        # Validar que origem e destino são diferentes
        if origem and destino and origem == destino:
            self.add_error('componente_destino', 
                'Componente destino deve ser diferente do componente origem.')
        
        # Validar unicidade da relação
        if origem and destino:
            derivados_existentes = ComponenteDerivado.objects.filter(
                componente_origem=origem,
                componente_destino=destino
            )
            
            # Se for edição, excluir o próprio derivado da verificação
            if self.instance.pk:
                derivados_existentes = derivados_existentes.exclude(pk=self.instance.pk)
            
            if derivados_existentes.exists():
                self.add_error('componente_destino',
                    'Já existe uma relação entre estes componentes.')
        
        return cleaned_data


class SimulacaoElevadorForm(BaseModelForm, AuditMixin):
    """Formulário para simulações de elevadores"""
    
    class Meta:
        model = SimulacaoElevador
        fields = ['numero', 'nome', 'cliente_nome', 'cliente_contato', 'observacoes']
        widgets = {
            'numero': forms.TextInput(attrs={
                'placeholder': 'Número da simulação'
            }),
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome do projeto'
            }),
            'cliente_nome': forms.TextInput(attrs={
                'placeholder': 'Nome do cliente'
            }),
            'cliente_contato': forms.TextInput(attrs={
                'placeholder': 'Contato do cliente'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Observações sobre a simulação...'
            }),
        }
        labels = {
            'numero': 'Número',
            'nome': 'Nome do Projeto',
            'cliente_nome': 'Nome do Cliente',
            'cliente_contato': 'Contato do Cliente',
            'observacoes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['nome'].required = True
        self.fields['cliente_nome'].required = True
    
    def clean_numero(self):
        """Validar unicidade do número"""
        numero = self.cleaned_data.get('numero')
        if numero:
            # Verificar se já existe outra simulação com o mesmo número
            simulacoes_existentes = SimulacaoElevador.objects.filter(numero=numero)
            
            # Se for edição, excluir a própria simulação da verificação
            if self.instance.pk:
                simulacoes_existentes = simulacoes_existentes.exclude(pk=self.instance.pk)
            
            if simulacoes_existentes.exists():
                raise ValidationError('Já existe uma simulação com este número.')
        
        return numero


class EspecificacaoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de especificações"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativa', 'Ativas'),
        ('inativa', 'Inativas'),
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
        self.fields['tipo'].choices = [('', 'Todos os Tipos')] + get_especificacao_elevador_tipo_choices() # Call the function here
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código ou nome...'


class SimulacaoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de simulações"""
    
    STATUS_CHOICES = [
        ('', 'Todos os Status'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, # This will be set dynamically below
        required=False,
        label='Status'
    )
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm'
        }),
        label='Data Início'
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm'
        }),
        label='Data Fim'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('', 'Todos os Status')] + get_simulacao_elevador_status_choices() # Call the function here
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por número, nome ou cliente...'