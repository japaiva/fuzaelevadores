# vendedor/forms.py - VERSÃO 2 ETAPAS COMPLETA

from django import forms
from .models import Pedido, AnexoPedido
from core.models import Cliente


class PedidoClienteElevadorForm(forms.ModelForm):
    """
    Formulário unificado para a Etapa 1: Cliente + Elevador + Poço
    """
    
    class Meta:
        model = Pedido
        fields = [
            # Dados do Cliente
            'cliente',
            'nome_projeto', 
            'observacoes',
            'faturado_por',
            
            # Dados do Elevador
            'modelo_elevador',
            'capacidade_pessoas',
            'capacidade',
            'acionamento',
            'tracao',
            'contrapeso',
            
            # Dados do Poço
            'largura_poco',
            'comprimento_poco',
            'altura_poco',
            'pavimentos',
        ]
        
        widgets = {
            # Cliente
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'nome_projeto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Edifício Residencial Solar',
                'required': True
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações iniciais sobre o projeto...'
            }),
            'faturado_por': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            
            # Elevador
            'modelo_elevador': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'capacidade_pessoas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
                'placeholder': '8'
            }),
            'capacidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 50,
                'max': 10000,
                'step': 10,
                'placeholder': '640',
                'readonly': True  # Será habilitado via JavaScript
            }),
            'acionamento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'tracao': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contrapeso': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Poço
            'largura_poco': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.8,
                'max': 10,
                'step': 0.01,
                'placeholder': '2.00',
                'required': True
            }),
            'comprimento_poco': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.8,
                'max': 10,
                'step': 0.01,
                'placeholder': '2.00',
                'required': True
            }),
            'altura_poco': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2.0,
                'max': 50,
                'step': 0.01,
                'placeholder': '7.20',
                'required': True
            }),
            'pavimentos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 50,
                'placeholder': '3',
                'required': True
            }),
        }
        
        labels = {
            'cliente': 'Cliente',
            'nome_projeto': 'Nome do Projeto',
            'observacoes': 'Observações Iniciais',
            'faturado_por': 'Faturado por',
            'modelo_elevador': 'Modelo do Elevador',
            'capacidade_pessoas': 'Capacidade (Pessoas)',
            'capacidade': 'Capacidade (kg)',
            'acionamento': 'Acionamento',
            'tracao': 'Tração',
            'contrapeso': 'Contrapeso',
            'largura_poco': 'Largura do Poço (m)',
            'comprimento_poco': 'Comprimento do Poço (m)',
            'altura_poco': 'Altura do Poço (m)',
            'pavimentos': 'Número de Pavimentos',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset dos clientes
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome')
        self.fields['cliente'].empty_label = "-- Selecione um cliente --"
        
        # Tornar alguns campos opcionais baseado no modelo
        self.fields['capacidade_pessoas'].required = False
        self.fields['capacidade'].required = False  # Será calculado automaticamente
        self.fields['tracao'].required = False
        self.fields['contrapeso'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        modelo = cleaned_data.get('modelo_elevador')
        capacidade_pessoas = cleaned_data.get('capacidade_pessoas')
        capacidade = cleaned_data.get('capacidade')
        acionamento = cleaned_data.get('acionamento')
        
        # Validações específicas por modelo
        if modelo == 'Passageiro':
            if not capacidade_pessoas:
                raise forms.ValidationError({
                    'capacidade_pessoas': 'Para elevador de passageiro, informe o número de pessoas.'
                })
            # Calcular capacidade automaticamente
            cleaned_data['capacidade'] = capacidade_pessoas * 80
        else:
            # Para outros modelos, capacidade é obrigatória
            if not capacidade or capacidade <= 0:
                raise forms.ValidationError({
                    'capacidade': 'Para este tipo de elevador, informe a capacidade em kg.'
                })
        
        # Validações por acionamento
        if acionamento == 'Motor':
            if not cleaned_data.get('tracao'):
                raise forms.ValidationError({
                    'tracao': 'Para acionamento por motor, informe o tipo de tração.'
                })
            if not cleaned_data.get('contrapeso'):
                raise forms.ValidationError({
                    'contrapeso': 'Para acionamento por motor, informe o tipo de contrapeso.'
                })
        
        # Validações de dimensões
        largura = cleaned_data.get('largura_poco')
        comprimento = cleaned_data.get('comprimento_poco')
        altura = cleaned_data.get('altura_poco')
        pavimentos = cleaned_data.get('pavimentos')
        
        if largura and comprimento:
            area = largura * comprimento
            if area < 2.0:
                raise forms.ValidationError({
                    'largura_poco': 'Área do poço muito pequena (mínimo 2.0m²).'
                })
        
        if altura and pavimentos and pavimentos > 1:
            altura_pavimento = altura / (pavimentos - 1)
            if altura_pavimento < 2.5:
                raise forms.ValidationError({
                    'altura_poco': f'Altura por pavimento muito baixa ({altura_pavimento:.2f}m). Mínimo recomendado: 2.5m.'
                })
        
        return cleaned_data


class PedidoCabinePortasForm(forms.ModelForm):
    """
    Formulário unificado para a Etapa 2: Cabine + Portas
    """
    
    class Meta:
        model = Pedido
        fields = [
            # Dados da Cabine
            'material_cabine',
            'material_cabine_outro',
            'valor_cabine_outro',
            'espessura_cabine',
            'saida_cabine',
            'altura_cabine',
            'piso_cabine',
            'material_piso_cabine',
            'material_piso_cabine_outro',
            'valor_piso_cabine_outro',
            
            # Porta da Cabine
            'modelo_porta_cabine',
            'material_porta_cabine',
            'material_porta_cabine_outro',
            'valor_porta_cabine_outro',
            'folhas_porta_cabine',
            'largura_porta_cabine',
            'altura_porta_cabine',
            
            # Porta do Pavimento
            'modelo_porta_pavimento',
            'material_porta_pavimento',
            'material_porta_pavimento_outro',
            'valor_porta_pavimento_outro',
            'folhas_porta_pavimento',
            'largura_porta_pavimento',
            'altura_porta_pavimento',
        ]
        
        widgets = {
            # Cabine - Material
            'material_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_cabine_outro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Alumínio Anodizado'
            }),
            'valor_cabine_outro': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01,
                'placeholder': '0,00'
            }),
            'espessura_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'saida_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'altura_cabine': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2.0,
                'max': 4.0,
                'step': 0.01,
                'placeholder': '2.30',
                'required': True
            }),
            
            # Cabine - Piso
            'piso_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_piso_cabine': forms.Select(attrs={
                'class': 'form-select'
            }),
            'material_piso_cabine_outro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Granito Preto'
            }),
            'valor_piso_cabine_outro': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01,
                'placeholder': '0,00'
            }),
            
            # Porta da Cabine
            'modelo_porta_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_porta_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_porta_cabine_outro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Vidro Temperado'
            }),
            'valor_porta_cabine_outro': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01,
                'placeholder': '0,00'
            }),
            'folhas_porta_cabine': forms.Select(attrs={
                'class': 'form-select'
            }),
            'largura_porta_cabine': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.6,
                'max': 2.0,
                'step': 0.01,
                'placeholder': '0.80',
                'required': True
            }),
            'altura_porta_cabine': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1.8,
                'max': 2.5,
                'step': 0.01,
                'placeholder': '2.00',
                'required': True
            }),
            
            # Porta do Pavimento
            'modelo_porta_pavimento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_porta_pavimento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_porta_pavimento_outro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Madeira Mogno'
            }),
            'valor_porta_pavimento_outro': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01,
                'placeholder': '0,00'
            }),
            'folhas_porta_pavimento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'largura_porta_pavimento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.6,
                'max': 2.0,
                'step': 0.01,
                'placeholder': '0.80',
                'required': True
            }),
            'altura_porta_pavimento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1.8,
                'max': 2.5,
                'step': 0.01,
                'placeholder': '2.00',
                'required': True
            }),
        }
        
        labels = {
            # Cabine
            'material_cabine': 'Material da Cabine',
            'material_cabine_outro': 'Nome do Material',
            'valor_cabine_outro': 'Valor (R$)',
            'espessura_cabine': 'Espessura',
            'saida_cabine': 'Saída',
            'altura_cabine': 'Altura da Cabine (m)',
            'piso_cabine': 'Responsável pelo Piso',
            'material_piso_cabine': 'Material do Piso',
            'material_piso_cabine_outro': 'Nome do Material do Piso',
            'valor_piso_cabine_outro': 'Valor (R$)',
            
            # Porta Cabine
            'modelo_porta_cabine': 'Modelo',
            'material_porta_cabine': 'Material',
            'material_porta_cabine_outro': 'Nome do Material',
            'valor_porta_cabine_outro': 'Valor (R$)',
            'folhas_porta_cabine': 'Folhas',
            'largura_porta_cabine': 'Largura (m)',
            'altura_porta_cabine': 'Altura (m)',
            
            # Porta Pavimento
            'modelo_porta_pavimento': 'Modelo',
            'material_porta_pavimento': 'Material',
            'material_porta_pavimento_outro': 'Nome do Material',
            'valor_porta_pavimento_outro': 'Valor (R$)',
            'folhas_porta_pavimento': 'Folhas',
            'largura_porta_pavimento': 'Largura (m)',
            'altura_porta_pavimento': 'Altura (m)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar alguns campos opcionais
        self.fields['material_cabine_outro'].required = False
        self.fields['valor_cabine_outro'].required = False
        self.fields['material_piso_cabine'].required = False
        self.fields['material_piso_cabine_outro'].required = False
        self.fields['valor_piso_cabine_outro'].required = False
        self.fields['material_porta_cabine_outro'].required = False
        self.fields['valor_porta_cabine_outro'].required = False
        self.fields['folhas_porta_cabine'].required = False
        self.fields['material_porta_pavimento_outro'].required = False
        self.fields['valor_porta_pavimento_outro'].required = False
        self.fields['folhas_porta_pavimento'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar material "Outro" da cabine
        material_cabine = cleaned_data.get('material_cabine')
        if material_cabine == 'Outro':
            material_outro = cleaned_data.get('material_cabine_outro')
            valor_outro = cleaned_data.get('valor_cabine_outro')
            
            if not material_outro:
                raise forms.ValidationError({
                    'material_cabine_outro': 'Informe o nome do material da cabine.'
                })
            
            if not valor_outro or valor_outro <= 0:
                raise forms.ValidationError({
                    'valor_cabine_outro': 'Informe um valor válido para o material da cabine.'
                })
        
        # Validar piso da cabine
        piso_cabine = cleaned_data.get('piso_cabine')
        if piso_cabine == 'Por conta da empresa':
            material_piso = cleaned_data.get('material_piso_cabine')
            if not material_piso:
                raise forms.ValidationError({
                    'material_piso_cabine': 'Selecione o material do piso.'
                })
            
            if material_piso == 'Outro':
                material_piso_outro = cleaned_data.get('material_piso_cabine_outro')
                valor_piso_outro = cleaned_data.get('valor_piso_cabine_outro')
                
                if not material_piso_outro:
                    raise forms.ValidationError({
                        'material_piso_cabine_outro': 'Informe o nome do material do piso.'
                    })
                
                if not valor_piso_outro or valor_piso_outro <= 0:
                    raise forms.ValidationError({
                        'valor_piso_cabine_outro': 'Informe um valor válido para o material do piso.'
                    })
        
        # Validar porta da cabine
        modelo_porta_cabine = cleaned_data.get('modelo_porta_cabine')
        material_porta_cabine = cleaned_data.get('material_porta_cabine')
        
        if modelo_porta_cabine == 'Automática':
            folhas_cabine = cleaned_data.get('folhas_porta_cabine')
            if not folhas_cabine:
                raise forms.ValidationError({
                    'folhas_porta_cabine': 'Para porta automática, selecione o número de folhas.'
                })
        
        if material_porta_cabine == 'Outro':
            material_outro = cleaned_data.get('material_porta_cabine_outro')
            valor_outro = cleaned_data.get('valor_porta_cabine_outro')
            
            if not material_outro:
                raise forms.ValidationError({
                    'material_porta_cabine_outro': 'Informe o nome do material da porta da cabine.'
                })
            
            if not valor_outro or valor_outro <= 0:
                raise forms.ValidationError({
                    'valor_porta_cabine_outro': 'Informe um valor válido para o material da porta da cabine.'
                })
        
        # Validar porta do pavimento
        modelo_porta_pavimento = cleaned_data.get('modelo_porta_pavimento')
        material_porta_pavimento = cleaned_data.get('material_porta_pavimento')
        
        if modelo_porta_pavimento == 'Automática':
            folhas_pavimento = cleaned_data.get('folhas_porta_pavimento')
            if not folhas_pavimento:
                raise forms.ValidationError({
                    'folhas_porta_pavimento': 'Para porta automática, selecione o número de folhas.'
                })
        
        if material_porta_pavimento == 'Outro':
            material_outro = cleaned_data.get('material_porta_pavimento_outro')
            valor_outro = cleaned_data.get('valor_porta_pavimento_outro')
            
            if not material_outro:
                raise forms.ValidationError({
                    'material_porta_pavimento_outro': 'Informe o nome do material da porta do pavimento.'
                })
            
            if not valor_outro or valor_outro <= 0:
                raise forms.ValidationError({
                    'valor_porta_pavimento_outro': 'Informe um valor válido para o material da porta do pavimento.'
                })
        
        # Validar dimensões
        altura_cabine = cleaned_data.get('altura_cabine')
        if altura_cabine and altura_cabine < 2.0:
            raise forms.ValidationError({
                'altura_cabine': 'Altura da cabine muito baixa (mínimo 2.0m).'
            })
        
        return cleaned_data


# =============================================================================
# FORMULÁRIOS AUXILIARES
# =============================================================================

class PedidoFiltroForm(forms.Form):
    """Formulário para filtros da lista de pedidos"""
    
    STATUS_CHOICES = [('', 'Todos')] + Pedido.STATUS_CHOICES
    MODELO_CHOICES = [('', 'Todos')] + [
        ('Passageiro', 'Passageiro'),
        ('Carga', 'Carga'),
        ('Monta Prato', 'Monta Prato'),
        ('Plataforma Acessibilidade', 'Plataforma Acessibilidade'),
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
        empty_label='Todos os clientes',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    periodo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('hoje', 'Hoje'),
            ('semana', 'Esta semana'),
            ('mes', 'Este mês'),
            ('ano', 'Este ano'),
        ],
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


class ClienteCreateForm(forms.ModelForm):
    """Formulário para criação rápida de cliente"""
    
    class Meta:
        model = Cliente
        fields = [
            'nome',
            'nome_fantasia', 
            'tipo_pessoa',
            'cpf_cnpj',
            'telefone',
            'email',
            'endereco',
            'cidade',
            'estado',
            'cep',
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo ou razão social',
                'required': True
            }),
            'nome_fantasia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome fantasia (opcional)'
            }),
            'tipo_pessoa': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CPF ou CNPJ'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, número, complemento'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00000-000'
            }),
        }
        
        labels = {
            'nome': 'Nome/Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'tipo_pessoa': 'Tipo de Pessoa',
            'cpf_cnpj': 'CPF/CNPJ',
            'telefone': 'Telefone',
            'email': 'Email',
            'endereco': 'Endereço',
            'cidade': 'Cidade',
            'estado': 'Estado',
            'cep': 'CEP',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar alguns campos opcionais para criação rápida
        self.fields['nome_fantasia'].required = False
        self.fields['cpf_cnpj'].required = False
        self.fields['telefone'].required = False
        self.fields['email'].required = False
        self.fields['endereco'].required = False
        self.fields['cidade'].required = False
        self.fields['estado'].required = False
        self.fields['cep'].required = False
    
    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if cpf_cnpj:
            # Remover caracteres especiais
            cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
            
            # Validação básica de tamanho
            if len(cpf_cnpj) not in [11, 14]:
                raise forms.ValidationError('CPF deve ter 11 dígitos e CNPJ deve ter 14 dígitos.')
        
        return cpf_cnpj
    
    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remover caracteres especiais
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            
            # Validação básica de tamanho
            if len(telefone_limpo) < 10:
                raise forms.ValidationError('Telefone deve ter pelo menos 10 dígitos.')
        
        return telefone
    
    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if cep:
            # Remover caracteres especiais
            cep_limpo = ''.join(filter(str.isdigit, cep))
            
            # Validação básica de tamanho
            if len(cep_limpo) != 8:
                raise forms.ValidationError('CEP deve ter 8 dígitos.')
        
        return cep


class AnexoPedidoForm(forms.ModelForm):
    """Formulário para upload de anexos"""
    
    class Meta:
        model = AnexoPedido
        fields = ['nome', 'tipo', 'arquivo', 'observacoes']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do arquivo'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o arquivo...'
            }),
        }
        
        labels = {
            'nome': 'Nome do Arquivo',
            'tipo': 'Tipo do Arquivo',
            'arquivo': 'Arquivo',
            'observacoes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar observações opcional
        self.fields['observacoes'].required = False
    
    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Validar tamanho do arquivo (máximo 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Arquivo muito grande. Tamanho máximo: 10MB.')
            
            # Validar extensão
            import os
            nome, extensao = os.path.splitext(arquivo.name)
            extensoes_permitidas = [
                '.pdf', '.jpg', '.jpeg', '.png', 
                '.doc', '.docx', '.xls', '.xlsx'
            ]
            
            if extensao.lower() not in extensoes_permitidas:
                raise forms.ValidationError(
                    f'Extensão não permitida. Use: {", ".join(extensoes_permitidas)}'
                )
        
        return arquivo