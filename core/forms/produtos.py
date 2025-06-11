# core/forms/produtos.py

"""
Formulários relacionados a produtos, grupos e estruturas
"""

from django import forms
from django.core.exceptions import ValidationError

from core.models import GrupoProduto, SubgrupoProduto, Produto
# Import the function to get choices
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, MoneyInput, QuantityInput, validar_positivo
from core.choices import get_tipo_produto_choices # Import the function
from core.models.base import UNIDADE_MEDIDA_CHOICES, STATUS_PRODUTO_CHOICES  # Import choices directly


class GrupoProdutoForm(BaseModelForm, AuditMixin):
    """Formulário para grupos de produtos"""
    
    class Meta:
        model = GrupoProduto
        fields = ['codigo', 'nome', 'tipo_produto', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ex: 01, 02, 03...',
                'maxlength': '10'
            }),
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome do grupo'
            }),
            # The 'tipo_produto' field is set in __init__ using the dynamic choices
        }
        labels = {
            'codigo': 'Código',
            'nome': 'Nome do Grupo',
            'tipo_produto': 'Tipo de Produto',
            'ativo': 'Grupo Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for tipo_produto field dynamically
        self.fields['tipo_produto'].choices = get_tipo_produto_choices() # Call the function here

        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        self.fields['tipo_produto'].required = True
    
    def clean_codigo(self):
        """Validar unicidade do código"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Verificar se já existe outro grupo com o mesmo código
            grupos_existentes = GrupoProduto.objects.filter(codigo=codigo)
            
            # Se for edição, excluir o próprio grupo da verificação
            if self.instance.pk:
                grupos_existentes = grupos_existentes.exclude(pk=self.instance.pk)
            
            if grupos_existentes.exists():
                raise ValidationError('Já existe um grupo com este código.')
        
        return codigo


class SubgrupoProdutoForm(BaseModelForm, AuditMixin):
    """Formulário para subgrupos de produtos"""
    
    class Meta:
        model = SubgrupoProduto
        fields = ['grupo', 'codigo', 'nome', 'ultimo_numero', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ex: 01, 02, 03...',
                'maxlength': '10'
            }),
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome do subgrupo'
            }),
            'ultimo_numero': forms.NumberInput(attrs={
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
        }
        labels = {
            'grupo': 'Grupo',
            'codigo': 'Código',
            'nome': 'Nome do Subgrupo',
            'ultimo_numero': 'Último Número Usado',
            'ativo': 'Subgrupo Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas grupos ativos
        self.fields['grupo'].queryset = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        
        # Campos obrigatórios
        self.fields['grupo'].required = True
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        
        # Se for edição, mostrar informações adicionais
        if self.instance.pk:
            produtos_count = self.instance.produtos.count()
            
            if produtos_count > 0:
                self.fields['nome'].help_text = f"Produtos vinculados: {produtos_count}"
                
                # Descobrir o maior número usado analisando os códigos dos produtos
                maior_numero_usado = 0
                for produto in self.instance.produtos.all():
                    try:
                        # Formato: GG.SS.NNNNN - pegar os últimos 5 dígitos
                        partes = produto.codigo.split('.')
                        if len(partes) >= 3:
                            numero_produto = int(partes[-1])
                            if numero_produto > maior_numero_usado:
                                maior_numero_usado = numero_produto
                    except (ValueError, IndexError):
                        continue
                
                # Se o último número for menor que o maior usado, mostrar aviso
                if maior_numero_usado > self.instance.ultimo_numero:
                    self.fields['ultimo_numero'].help_text = f"⚠️ Maior número usado: {maior_numero_usado}"
                    self.fields['ultimo_numero'].widget.attrs['class'] += ' border-warning'
    
    def clean_codigo(self):
        """Validar unicidade do código dentro do grupo"""
        codigo = self.cleaned_data.get('codigo')
        grupo = self.cleaned_data.get('grupo')
        
        if codigo and grupo:
            # Verificar se já existe outro subgrupo com o mesmo código no mesmo grupo
            subgrupos_existentes = SubgrupoProduto.objects.filter(grupo=grupo, codigo=codigo)
            
            # Se for edição, excluir o próprio subgrupo da verificação
            if self.instance.pk:
                subgrupos_existentes = subgrupos_existentes.exclude(pk=self.instance.pk)
            
            if subgrupos_existentes.exists():
                raise ValidationError(
                    f'Já existe um subgrupo com o código "{codigo}" no grupo "{grupo.nome}".'
                )
        
        return codigo


class ProdutoForm(BaseModelForm, AuditMixin):
    """Formulário para produtos com geração automática de códigos"""
    
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'grupo', 'subgrupo',
            'unidade_medida', 'peso_unitario',
            'controla_estoque', 'estoque_minimo', 'custo_medio',
            'fornecedor_principal', 'prazo_entrega_padrao', 'status', 'disponivel'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome do produto',
                'class': 'form-control'
            }),
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descrição do produto...',
                'class': 'form-control'
            }),
            'grupo': forms.Select(attrs={
                'onchange': 'updateSubgrupos(this.value)',
                'class': 'form-select'
            }),
            'subgrupo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unidade_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'peso_unitario': forms.NumberInput(attrs={
                'step': '0.001',
                'min': '0',
                'placeholder': '0.000',
                'class': 'form-control'
            }),
            'estoque_minimo': QuantityInput(),
            'custo_medio': MoneyInput(),
            'prazo_entrega_padrao': forms.NumberInput(attrs={
                'min': '0',
                'step': '1',
                'placeholder': 'Dias',
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fornecedor_principal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'controla_estoque': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'disponivel': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nome': 'Nome do Produto',
            'descricao': 'Descrição',
            'grupo': 'Grupo',
            'subgrupo': 'Subgrupo',
            'unidade_medida': 'Unidade de Medida',
            'peso_unitario': 'Peso Unitário (kg)',
            'controla_estoque': 'Controla Estoque',
            'estoque_minimo': 'Estoque Mínimo',
            'custo_medio': 'Custo Médio',
            'fornecedor_principal': 'Fornecedor Principal',
            'prazo_entrega_padrao': 'Prazo Entrega Padrão (dias)',
            'status': 'Status',
            'disponivel': 'Disponível para Uso',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar choices dos campos
        self.fields['unidade_medida'].choices = UNIDADE_MEDIDA_CHOICES
        self.fields['status'].choices = STATUS_PRODUTO_CHOICES

        # Campos obrigatórios
        self.fields['grupo'].required = True
        self.fields['subgrupo'].required = True
        self.fields['nome'].required = True
        self.fields['unidade_medida'].required = True
        
        # Filtrar apenas grupos ativos
        self.fields['grupo'].queryset = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        
        # Filtrar subgrupos baseado no grupo selecionado
        if 'grupo' in self.data:
            # Se tem dados do POST, usar o grupo selecionado
            try:
                grupo_id = int(self.data.get('grupo'))
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.filter(
                    grupo_id=grupo_id, 
                    ativo=True
                ).order_by('codigo')
            except (ValueError, TypeError):
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        elif self.instance.pk and hasattr(self.instance, 'grupo') and self.instance.grupo:
            # Se é edição de produto existente
            self.fields['subgrupo'].queryset = self.instance.grupo.subgrupos.filter(ativo=True).order_by('codigo')
        else:
            # Para produtos novos, não mostrar subgrupos até que um grupo seja selecionado
            self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        
        # Informações de ajuda
        self.fields['grupo'].help_text = "Selecione o grupo - o tipo do produto será definido automaticamente"
        self.fields['subgrupo'].help_text = "Selecione o subgrupo - o código será gerado automaticamente"
        
        # Se for edição, mostrar o código atual
        if self.instance.pk and self.instance.codigo:
            self.fields['nome'].help_text = f"Código atual: {self.instance.codigo}"
    
    def clean_estoque_minimo(self):
        """Validar estoque mínimo"""
        estoque_minimo = self.cleaned_data.get('estoque_minimo')
        if estoque_minimo is not None:
            validar_positivo(estoque_minimo)
        return estoque_minimo
    
    def clean_custo_medio(self):
        """Validar custo médio"""
        custo_medio = self.cleaned_data.get('custo_medio')
        if custo_medio is not None:
            validar_positivo(custo_medio)
        return custo_medio
    
    def clean(self):
        """Validações personalizadas"""
        cleaned_data = super().clean()
        grupo = cleaned_data.get('grupo')
        subgrupo = cleaned_data.get('subgrupo')
        
        # Validar se o subgrupo pertence ao grupo selecionado
        if grupo and subgrupo:
            if subgrupo.grupo != grupo:
                self.add_error('subgrupo', 'O subgrupo selecionado não pertence ao grupo escolhido.')
        
        return cleaned_data

    def save(self, commit=True): # Removed 'user=None' from method signature
        """Override para garantir que o tipo seja definido corretamente"""
        produto = super().save(commit=False) # Removed user=user
        
        # Garantir que o tipo coincida com o grupo
        if produto.grupo and produto.grupo.tipo_produto:
            produto.tipo = produto.grupo.tipo_produto
        
        if commit:
            produto.save()
        
        return produto


class GrupoProdutoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de grupos"""
    
    # Use the function to get choices
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    tipo_produto = forms.ChoiceField(
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
        self.fields['tipo_produto'].choices = [('', 'Todos os Tipos')] + get_tipo_produto_choices() # Call the function here
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código ou nome...'


class SubgrupoProdutoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de subgrupos"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    grupo = forms.ModelChoiceField(
        queryset=GrupoProduto.objects.filter(ativo=True).order_by('codigo'),
        required=False,
        empty_label="Todos os Grupos",
        label='Grupo'
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código ou nome...'


class ProdutoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de produtos"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
        ('disponivel', 'Disponíveis'),
        ('indisponivel', 'Indisponíveis'),
    ]
    
    grupo = forms.ModelChoiceField(
        queryset=GrupoProduto.objects.filter(ativo=True).order_by('codigo'),
        required=False,
        empty_label="Todos os Grupos",
        label='Grupo'
    )
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
        self.fields['tipo'].choices = [('', 'Todos os Tipos')] + get_tipo_produto_choices() # Call the function here
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código, nome ou descrição...'


class ProdutoEstoqueForm(forms.ModelForm):
    """Formulário simplificado para atualização de estoque"""
    
    class Meta:
        model = Produto
        fields = ['estoque_atual', 'estoque_minimo']
        widgets = {
            'estoque_atual': QuantityInput(),
            'estoque_minimo': QuantityInput(),
        }
        labels = {
            'estoque_atual': 'Estoque Atual',
            'estoque_minimo': 'Estoque Mínimo',
        }
    
    def clean_estoque_atual(self):
        """Validar estoque atual"""
        estoque_atual = self.cleaned_data.get('estoque_atual')
        if estoque_atual is not None:
            validar_positivo(estoque_atual)
        return estoque_atual
    
    def clean_estoque_minimo(self):
        """Validar estoque mínimo"""
        estoque_minimo = self.cleaned_data.get('estoque_minimo')
        if estoque_minimo is not None:
            validar_positivo(estoque_minimo)
        return estoque_minimo


class ProdutoPrecoForm(forms.ModelForm):
    """Formulário simplificado para atualização de preços"""
    
    class Meta:
        model = Produto
        fields = ['custo_medio', 'preco_venda', 'margem_padrao']
        widgets = {
            'custo_medio': MoneyInput(),
            'preco_venda': MoneyInput(),
            'margem_padrao': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1000',
                'placeholder': '0,00'
            }),
        }
        labels = {
            'custo_medio': 'Custo Médio',
            'preco_venda': 'Preço de Venda',
            'margem_padrao': 'Margem Padrão (%)',
        }
    
    def clean_custo_medio(self):
        """Validar custo médio"""
        custo_medio = self.cleaned_data.get('custo_medio')
        if custo_medio is not None:
            validar_positivo(custo_medio)
        return custo_medio
    
    def clean_preco_venda(self):
        """Validar preço de venda"""
        preco_venda = self.cleaned_data.get('preco_venda')
        if preco_venda is not None:
            validar_positivo(preco_venda)
        return preco_venda