# vendedor/forms.py

from django import forms
from .models import Pedido, AnexoPedido
from core.models import Cliente
from core.forms import ClienteCreateForm

class PedidoClienteForm(forms.ModelForm):
    """Form para dados do cliente do pedido"""
    
    class Meta:
        model = Pedido
        fields = ['cliente', 'nome_projeto', 'faturado_por', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'nome_projeto': forms.TextInput(attrs={'class': 'form-control'}),
            'faturado_por': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome')
        self.fields['cliente'].required = True
        self.fields['nome_projeto'].required = True

class PedidoElevadorForm(forms.ModelForm):
    """Form para dados do elevador"""
    
    class Meta:
        model = Pedido
        fields = [
            'modelo_elevador', 'capacidade', 'capacidade_pessoas',
            'acionamento', 'tracao', 'contrapeso',
            'largura_poco', 'comprimento_poco', 'altura_poco', 'pavimentos'
        ]
        widgets = {
            'modelo_elevador': forms.Select(attrs={'class': 'form-select'}),
            'capacidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacidade_pessoas': forms.NumberInput(attrs={'class': 'form-control'}),
            'acionamento': forms.Select(attrs={'class': 'form-select'}),
            'tracao': forms.Select(attrs={'class': 'form-select'}),
            'contrapeso': forms.Select(attrs={'class': 'form-select'}),
            'largura_poco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comprimento_poco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'altura_poco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pavimentos': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['capacidade_pessoas'].required = False
        
        # ⭐ CORREÇÃO: Tornar capacidade não obrigatória no formulário
        # pois será calculada automaticamente para elevador de passageiro
        self.fields['capacidade'].required = False
        
        # Valores padrão
        if not self.instance.pk:
            self.initial.update({
                'capacidade': 80,
                'capacidade_pessoas': 1,
                'acionamento': 'Motor',
                'tracao': '1x1',
                'contrapeso': 'Lateral',
                'largura_poco': 2.00,
                'comprimento_poco': 2.00,
                'altura_poco': 3.00,
                'pavimentos': 2,
            })
    
    def clean(self):
        cleaned_data = super().clean()
        modelo = cleaned_data.get('modelo_elevador')
        capacidade = cleaned_data.get('capacidade')
        capacidade_pessoas = cleaned_data.get('capacidade_pessoas')
        acionamento = cleaned_data.get('acionamento')
        
        # Validar capacidade para elevador de passageiro
        if modelo == 'Passageiro':
            if not capacidade_pessoas:
                raise forms.ValidationError({
                    'capacidade_pessoas': 'Número de pessoas é obrigatório para elevador de passageiro.'
                })
            # Calcular capacidade em kg baseada no número de pessoas
            cleaned_data['capacidade'] = capacidade_pessoas * 80
        else:
            # Para outros tipos de elevador, capacidade é obrigatória
            if not capacidade or capacidade <= 0:
                raise forms.ValidationError({
                    'capacidade': 'Capacidade em kg é obrigatória para este tipo de elevador.'
                })
        
        # Validar campos de tração para hidráulico
        if acionamento == 'Hidraulico':
            cleaned_data['tracao'] = ''
            cleaned_data['contrapeso'] = ''
        elif acionamento == 'Carretel':
            cleaned_data['contrapeso'] = ''
        
        # Validações de dimensões
        largura_poco = cleaned_data.get('largura_poco')
        comprimento_poco = cleaned_data.get('comprimento_poco')
        altura_poco = cleaned_data.get('altura_poco')
        pavimentos = cleaned_data.get('pavimentos')
        
        if largura_poco and largura_poco <= 0:
            raise forms.ValidationError({
                'largura_poco': 'A largura do poço deve ser maior que zero.'
            })
            
        if comprimento_poco and comprimento_poco <= 0:
            raise forms.ValidationError({
                'comprimento_poco': 'O comprimento do poço deve ser maior que zero.'
            })
            
        if altura_poco and altura_poco <= 0:
            raise forms.ValidationError({
                'altura_poco': 'A altura do poço deve ser maior que zero.'
            })
            
        if pavimentos and pavimentos < 2:
            raise forms.ValidationError({
                'pavimentos': 'O número de pavimentos deve ser pelo menos 2.'
            })
        
        return cleaned_data
class PedidoPortasForm(forms.ModelForm):
    """Form para dados das portas"""
    
    class Meta:
        model = Pedido
        fields = [
            # Porta da Cabine
            'modelo_porta_cabine', 'material_porta_cabine', 
            'material_porta_cabine_outro', 'valor_porta_cabine_outro',
            'folhas_porta_cabine', 'largura_porta_cabine', 'altura_porta_cabine',
            # Porta do Pavimento
            'modelo_porta_pavimento', 'material_porta_pavimento',
            'material_porta_pavimento_outro', 'valor_porta_pavimento_outro',
            'folhas_porta_pavimento', 'largura_porta_pavimento', 'altura_porta_pavimento'
        ]
        widgets = {
            # Porta da Cabine
            'modelo_porta_cabine': forms.Select(attrs={'class': 'form-select'}),
            'material_porta_cabine': forms.Select(attrs={'class': 'form-select'}),
            'material_porta_cabine_outro': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_porta_cabine_outro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'folhas_porta_cabine': forms.Select(attrs={'class': 'form-select'}),
            'largura_porta_cabine': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'altura_porta_cabine': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # Porta do Pavimento
            'modelo_porta_pavimento': forms.Select(attrs={'class': 'form-select'}),
            'material_porta_pavimento': forms.Select(attrs={'class': 'form-select'}),
            'material_porta_pavimento_outro': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_porta_pavimento_outro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'folhas_porta_pavimento': forms.Select(attrs={'class': 'form-select'}),
            'largura_porta_pavimento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'altura_porta_pavimento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Valores padrão
        if not self.instance.pk:
            self.initial.update({
                'modelo_porta_cabine': 'Automática',
                'material_porta_cabine': 'Inox',
                'folhas_porta_cabine': '2',
                'largura_porta_cabine': 0.80,
                'altura_porta_cabine': 2.00,
                'modelo_porta_pavimento': 'Automática',
                'material_porta_pavimento': 'Inox',
                'folhas_porta_pavimento': '2',
                'largura_porta_pavimento': 0.80,
                'altura_porta_pavimento': 2.00,
            })
        
        # Campos condicionais
        self.fields['material_porta_cabine_outro'].required = False
        self.fields['valor_porta_cabine_outro'].required = False
        self.fields['folhas_porta_cabine'].required = False
        self.fields['material_porta_pavimento_outro'].required = False
        self.fields['valor_porta_pavimento_outro'].required = False
        self.fields['folhas_porta_pavimento'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar material "Outro" da porta da cabine
        material_cabine = cleaned_data.get('material_porta_cabine')
        if material_cabine == 'Outro':
            if not cleaned_data.get('material_porta_cabine_outro'):
                raise forms.ValidationError({
                    'material_porta_cabine_outro': 'Nome do material é obrigatório quando "Outro" é selecionado.'
                })
            if not cleaned_data.get('valor_porta_cabine_outro'):
                raise forms.ValidationError({
                    'valor_porta_cabine_outro': 'Valor do material é obrigatório quando "Outro" é selecionado.'
                })
        
        # Validar material "Outro" da porta do pavimento
        material_pavimento = cleaned_data.get('material_porta_pavimento')
        if material_pavimento == 'Outro':
            if not cleaned_data.get('material_porta_pavimento_outro'):
                raise forms.ValidationError({
                    'material_porta_pavimento_outro': 'Nome do material é obrigatório quando "Outro" é selecionado.'
                })
            if not cleaned_data.get('valor_porta_pavimento_outro'):
                raise forms.ValidationError({
                    'valor_porta_pavimento_outro': 'Valor do material é obrigatório quando "Outro" é selecionado.'
                })
        
        # Validar folhas para portas automáticas
        modelo_cabine = cleaned_data.get('modelo_porta_cabine')
        if modelo_cabine == 'Automática' and not cleaned_data.get('folhas_porta_cabine'):
            raise forms.ValidationError({
                'folhas_porta_cabine': 'Número de folhas é obrigatório para porta automática.'
            })
        
        modelo_pavimento = cleaned_data.get('modelo_porta_pavimento')
        if modelo_pavimento == 'Automática' and not cleaned_data.get('folhas_porta_pavimento'):
            raise forms.ValidationError({
                'folhas_porta_pavimento': 'Número de folhas é obrigatório para porta automática.'
            })
        
        return cleaned_data


class PedidoCabineForm(forms.ModelForm):
    """Form para dados da cabine"""
    
    class Meta:
        model = Pedido
        fields = [
            'material_cabine', 'material_cabine_outro', 'valor_cabine_outro',
            'espessura_cabine', 'saida_cabine', 'altura_cabine',
            'piso_cabine', 'material_piso_cabine', 
            'material_piso_cabine_outro', 'valor_piso_cabine_outro'
        ]
        widgets = {
            'material_cabine': forms.Select(attrs={'class': 'form-select'}),
            'material_cabine_outro': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_cabine_outro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'espessura_cabine': forms.Select(attrs={'class': 'form-select'}),
            'saida_cabine': forms.Select(attrs={'class': 'form-select'}),
            'altura_cabine': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'piso_cabine': forms.Select(attrs={'class': 'form-select'}),
            'material_piso_cabine': forms.Select(attrs={'class': 'form-select'}),
            'material_piso_cabine_outro': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_piso_cabine_outro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Valores padrão
        if not self.instance.pk:
            self.initial.update({
                'material_cabine': 'Inox 430',
                'espessura_cabine': '1,2',
                'saida_cabine': 'Padrão',
                'altura_cabine': 2.30,
                'piso_cabine': 'Por conta do cliente',
                'material_piso_cabine': 'Antiderrapante',
            })
        
        # Campos condicionais
        self.fields['material_cabine_outro'].required = False
        self.fields['valor_cabine_outro'].required = False
        self.fields['material_piso_cabine'].required = False
        self.fields['material_piso_cabine_outro'].required = False
        self.fields['valor_piso_cabine_outro'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar material "Outro" da cabine
        material = cleaned_data.get('material_cabine')
        if material == 'Outro':
            if not cleaned_data.get('material_cabine_outro'):
                raise forms.ValidationError({
                    'material_cabine_outro': 'Nome do material é obrigatório quando "Outro" é selecionado.'
                })
            if not cleaned_data.get('valor_cabine_outro'):
                raise forms.ValidationError({
                    'valor_cabine_outro': 'Valor do material é obrigatório quando "Outro" é selecionado.'
                })
        
        # Validar material do piso se for por conta da empresa
        piso = cleaned_data.get('piso_cabine')
        if piso == 'Por conta da empresa':
            material_piso = cleaned_data.get('material_piso_cabine')
            if material_piso == 'Outro':
                if not cleaned_data.get('material_piso_cabine_outro'):
                    raise forms.ValidationError({
                        'material_piso_cabine_outro': 'Nome do material é obrigatório quando "Outro" é selecionado.'
                    })
                if not cleaned_data.get('valor_piso_cabine_outro'):
                    raise forms.ValidationError({
                        'valor_piso_cabine_outro': 'Valor do material é obrigatório quando "Outro" é selecionado.'
                    })
        
        return cleaned_data


class PedidoResumoForm(forms.ModelForm):
    """Form para revisar e finalizar o pedido"""
    
    class Meta:
        model = Pedido
        fields = ['preco_venda_final', 'percentual_desconto', 'observacoes']
        widgets = {
            'preco_venda_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'percentual_desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preco_venda_final'].required = False
        self.fields['percentual_desconto'].required = False


class AnexoPedidoForm(forms.ModelForm):
    """Form para upload de anexos"""
    
    class Meta:
        model = AnexoPedido
        fields = ['nome', 'tipo', 'arquivo', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observacoes'].required = False


class PedidoFiltroForm(forms.Form):
    """Form para filtros da listagem de pedidos"""
    
    STATUS_CHOICES = [('', 'Todos os Status')] + Pedido.STATUS_CHOICES
    
    MODELO_CHOICES = [('', 'Todos os Modelos')] + [
        ('Passageiro', 'Passageiro'),
        ('Carga', 'Carga'),
        ('Monta Prato', 'Monta Prato'),
        ('Plataforma Acessibilidade', 'Plataforma Acessibilidade'),
    ]
    
    PERIODO_CHOICES = [
        ('', 'Todos os Períodos'),
        ('hoje', 'Hoje'),
        ('semana', 'Esta Semana'),
        ('mes', 'Este Mês'),
        ('trimestre', 'Este Trimestre'),
        ('ano', 'Este Ano'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    modelo_elevador = forms.ChoiceField(
        choices=MODELO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(ativo=True).order_by('nome'),
        required=False,
        empty_label="Todos os Clientes",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    periodo = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por número, projeto ou cliente...'
        })
    )
