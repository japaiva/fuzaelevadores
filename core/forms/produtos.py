# core/forms/produtos.py - ATUALIZAÇÃO 1: FORMULÁRIOS

from django import forms
from django.core.exceptions import ValidationError

from core.models import GrupoProduto, SubgrupoProduto, Produto
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, MoneyInput, QuantityInput, validar_positivo

from core.choices import get_tipo_produto_choices 
from core.models.base import UNIDADE_MEDIDA_CHOICES, STATUS_PRODUTO_CHOICES 


class GrupoProdutoForm(BaseModelForm, AuditMixin):
    """Formulário para grupos de produtos - SEM ALTERAÇÕES"""
    
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
        }
        labels = {
            'codigo': 'Código',
            'nome': 'Nome do Grupo',
            'tipo_produto': 'Tipo de Produto',
            'ativo': 'Grupo Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_produto'].choices = get_tipo_produto_choices()
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        self.fields['tipo_produto'].required = True
    
    def clean_codigo(self):
        """Validar unicidade do código"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            grupos_existentes = GrupoProduto.objects.filter(codigo=codigo)
            if self.instance.pk:
                grupos_existentes = grupos_existentes.exclude(pk=self.instance.pk)
            if grupos_existentes.exists():
                raise ValidationError('Já existe um grupo com este código.')
        return codigo


class SubgrupoProdutoForm(BaseModelForm, AuditMixin):
    """Formulário para subgrupos de produtos - SEM ALTERAÇÕES"""
    
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
        self.fields['grupo'].queryset = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        self.fields['grupo'].required = True
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        
        if self.instance.pk:
            produtos_count = self.instance.produtos.count()
            if produtos_count > 0:
                self.fields['nome'].help_text = f"Produtos vinculados: {produtos_count}"
                
                # Descobrir o maior número usado
                maior_numero_usado = 0
                for produto in self.instance.produtos.all():
                    try:
                        partes = produto.codigo.split('.')
                        if len(partes) >= 3:
                            numero_produto = int(partes[-1])
                            if numero_produto > maior_numero_usado:
                                maior_numero_usado = numero_produto
                    except (ValueError, IndexError):
                        continue
                
                if maior_numero_usado > self.instance.ultimo_numero:
                    self.fields['ultimo_numero'].help_text = f"⚠️ Maior número usado: {maior_numero_usado}"
                    self.fields['ultimo_numero'].widget.attrs['class'] += ' border-warning'
    
    def clean_codigo(self):
        """Validar unicidade do código dentro do grupo"""
        codigo = self.cleaned_data.get('codigo')
        grupo = self.cleaned_data.get('grupo')
        
        if codigo and grupo:
            subgrupos_existentes = SubgrupoProduto.objects.filter(grupo=grupo, codigo=codigo)
            if self.instance.pk:
                subgrupos_existentes = subgrupos_existentes.exclude(pk=self.instance.pk)
            if subgrupos_existentes.exists():
                raise ValidationError(
                    f'Já existe um subgrupo com o código "{codigo}" no grupo "{grupo.nome}".'
                )
        return codigo


class ProdutoForm(BaseModelForm, AuditMixin):
    
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'grupo', 'subgrupo',
            'tipo_pi',
            'unidade_medida', 'peso_unitario',
            'codigo_ncm', 'codigo_produto_fornecedor',
            'controla_estoque', 'estoque_atual', 'estoque_minimo', # <<< campo 'estoque_atual' ADICIONADO AQUI
            'custo_medio', 'custo_industrializacao',
            'fornecedor_principal', 'prazo_entrega_padrao', 
            'status', 'disponivel', 'utilizado'
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
                'onchange': 'updateSubgruposAndTipo(this.value)',
                'class': 'form-select'
            }),
            'subgrupo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_pi': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleEstruturaFields()'
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
            'codigo_ncm': forms.TextInput(attrs={
                'placeholder': '0000.00.00',
                'maxlength': '20',
                'class': 'form-control'
            }),
            'codigo_produto_fornecedor': forms.TextInput(attrs={
                'placeholder': 'Código do fornecedor',
                'maxlength': '50',
                'class': 'form-control'
            }),
            'custo_industrializacao': MoneyInput(),
            'estoque_atual': QuantityInput(), # <<< WIDGET ADICIONADO
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
            'utilizado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nome': 'Nome do Produto',
            'descricao': 'Descrição',
            'grupo': 'Grupo',
            'subgrupo': 'Subgrupo',
            'tipo_pi': 'Tipo do Produto Intermediário',
            'unidade_medida': 'Unidade de Medida',
            'peso_unitario': 'Peso Unitário (kg)',
            'codigo_ncm': 'Código NCM',
            'codigo_produto_fornecedor': 'Código no Fornecedor',
            'custo_industrializacao': 'Custo Industrialização',
            'controla_estoque': 'Controla Estoque',
            'estoque_atual': 'Estoque Atual', # <<< LABEL ADICIONADO
            'estoque_minimo': 'Estoque Mínimo',
            'custo_medio': 'Custo Médio',
            'fornecedor_principal': 'Fornecedor Principal',
            'prazo_entrega_padrao': 'Prazo Entrega Padrão (dias)',
            'status': 'Status',
            'disponivel': 'Disponível para Uso',
            'utilizado': 'Material Utilizado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar choices dos campos
        self.fields['unidade_medida'].choices = UNIDADE_MEDIDA_CHOICES
        self.fields['status'].choices = STATUS_PRODUTO_CHOICES
        
        self.fields['tipo_pi'].choices = [('', 'Selecione o tipo')] + Produto.TIPO_PI_CHOICES

        # Campos obrigatórios
        self.fields['grupo'].required = True
        self.fields['subgrupo'].required = True
        self.fields['nome'].required = True
        self.fields['unidade_medida'].required = True
        
        # Filtrar apenas grupos ativos
        self.fields['grupo'].queryset = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        
        if self.instance.pk:
            if self.instance.tipo != 'PI':
                self.fields['tipo_pi'].widget = forms.HiddenInput()
                self.fields['tipo_pi'].required = False
            else:
                self.fields['tipo_pi'].required = True
        else:
            self.fields['tipo_pi'].required = False
        
        if 'grupo' in self.data:
            try:
                grupo_id = int(self.data.get('grupo'))
                grupo = GrupoProduto.objects.get(id=grupo_id)
                
                if grupo.tipo_produto == 'PI':
                    self.fields['tipo_pi'].required = True
                    self.fields['tipo_pi'].widget.attrs['style'] = 'display: block;'
                else:
                    self.fields['tipo_pi'].widget = forms.HiddenInput()
                    self.fields['tipo_pi'].required = False
                
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.filter(
                    grupo_id=grupo_id, 
                    ativo=True
                ).order_by('codigo')
            except (ValueError, TypeError, GrupoProduto.DoesNotExist):
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        elif self.instance.pk and hasattr(self.instance, 'grupo') and self.instance.grupo:
            self.fields['subgrupo'].queryset = self.instance.grupo.subgrupos.filter(ativo=True).order_by('codigo')
        else:
            self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        
        self.fields['grupo'].help_text = "Selecione o grupo - o tipo do produto será definido automaticamente"
        self.fields['subgrupo'].help_text = "Selecione o subgrupo - o código será gerado automaticamente"
        self.fields['utilizado'].help_text = "Marque se este material já foi utilizado em algum projeto"
        
        self.fields['tipo_pi'].help_text = """
        <strong>Comprado:</strong> Produto pronto do fornecedor<br>
        <strong>Montado Interno:</strong> Montagem na fábrica<br>
        <strong>Montado Externo:</strong> Montagem terceirizada<br>
        <strong>Serviço:</strong> Prestação de serviço
        """
        
        if self.instance.pk and self.instance.codigo:
            self.fields['nome'].help_text = f"Código atual: {self.instance.codigo}"

    def clean_custo_industrializacao(self):
        """Validar custo de industrialização"""
        custo = self.cleaned_data.get('custo_industrializacao')
        if custo is not None:
            validar_positivo(custo)
        return custo

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
        tipo_pi = cleaned_data.get('tipo_pi')
        fornecedor_principal = cleaned_data.get('fornecedor_principal')
        
        if grupo and subgrupo:
            if subgrupo.grupo != grupo:
                self.add_error('subgrupo', 'O subgrupo selecionado não pertence ao grupo escolhido.')
        
        if grupo and grupo.tipo_produto == 'PI':
            if not tipo_pi:
                self.add_error('tipo_pi', 'Tipo do Produto Intermediário é obrigatório para produtos PI.')
                
            if tipo_pi in ['COMPRADO', 'MONTADO_EXTERNO', 'SERVICO_EXTERNO']:
                if not fornecedor_principal:
                    campo_nome = 'Prestador principal' if tipo_pi == 'SERVICO_EXTERNO' else 'Fornecedor principal'
                    self.add_error('fornecedor_principal', f'{campo_nome} é obrigatório para este tipo.')
        
        return cleaned_data


    def save(self, commit=True):
        """Override para garantir que o tipo seja definido corretamente"""
        produto = super().save(commit=False)
        
        if produto.grupo and produto.grupo.tipo_produto:
            produto.tipo = produto.grupo.tipo_produto
        
        if commit:
            produto.save()
        
        return produto



# <<<< NOVOS FORMULÁRIOS DE FILTRO ATUALIZADOS

class ProdutoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de produtos - ATUALIZADO"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
        ('disponivel', 'Disponíveis'),
        ('indisponivel', 'Indisponíveis'),
    ]
    
    UTILIZADO_CHOICES = [
        ('', 'Todos'),
        ('utilizado', 'Utilizados'),
        ('nao_utilizado', 'Não Utilizados'),
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
    # <<<< NOVO FILTRO PARA TIPO_PI
    tipo_pi = forms.ChoiceField(
        required=False,
        label='Tipo PI'
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status'
    )
    utilizado = forms.ChoiceField(
        choices=UTILIZADO_CHOICES,
        required=False,
        label='Utilização'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = [('', 'Todos os Tipos')] + get_tipo_produto_choices()
        
        # <<<< CONFIGURAR CHOICES DO TIPO_PI
        self.fields['tipo_pi'].choices = [('', 'Todos os Tipos PI')] + Produto.TIPO_PI_CHOICES
        
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código, nome ou descrição...'


# Outros formulários permanecem inalterados...
class GrupoProdutoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de grupos - SEM ALTERAÇÕES"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    tipo_produto = forms.ChoiceField(required=False, label='Tipo')
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label='Status')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_produto'].choices = [('', 'Todos os Tipos')] + get_tipo_produto_choices()
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código ou nome...'


class SubgrupoProdutoFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de subgrupos - SEM ALTERAÇÕES"""
    
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
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label='Status')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código ou nome...'


# Formulários simples permanecem inalterados...
class ProdutoEstoqueForm(forms.ModelForm):
    """Formulário simplificado para atualização de estoque - SEM ALTERAÇÕES"""
    
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


class ProdutoPrecoForm(forms.ModelForm):
    """Formulário simplificado para atualização de preços - SEM ALTERAÇÕES"""
    
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


class ProdutoUtilizadoForm(forms.ModelForm):
    """Formulário simplificado para alterar status de utilização - SEM ALTERAÇÕES"""
    
    class Meta:
        model = Produto
        fields = ['utilizado']
        widgets = {
            'utilizado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'utilizado': 'Material Utilizado',
        }