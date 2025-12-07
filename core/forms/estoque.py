# core/forms/estoque.py

"""
Formulários relacionados a estoque, locais e tipos de movimento
"""

from django import forms
from django.core.exceptions import ValidationError

from core.models import Fornecedor, Cliente, PedidoCompra, Produto
from core.models.estoque import (
    LocalEstoque,
    TipoMovimentoEntrada,
    TipoMovimentoSaida,
    MovimentoEntrada,
    ItemMovimentoEntrada,
    MovimentoSaida,
    ItemMovimentoSaida,
    OrdemProducao,
    ItemConsumoOP,
    TIPO_LOCAL_ESTOQUE_CHOICES,
    TIPO_PARCEIRO_CHOICES,
    STATUS_MOVIMENTO_CHOICES,
    STATUS_OP_CHOICES,
)
from .base import BaseModelForm, BaseFiltroForm, AuditMixin


# ===============================================
# LOCAL DE ESTOQUE
# ===============================================

class LocalEstoqueForm(BaseModelForm, AuditMixin):
    """Formulário para cadastro de locais de estoque"""

    class Meta:
        model = LocalEstoque
        fields = [
            'nome', 'tipo', 'fornecedor', 'endereco', 'observacoes', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex: Almoxarifado Central, Laser ABC'
            }),
            'endereco': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Endereço do local (opcional)'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Observações (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].required = True

        # Filtrar apenas fornecedores ativos
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
        self.fields['fornecedor'].required = False

        # Adicionar classe JS para controle dinâmico
        self.fields['tipo'].widget.attrs['class'] = 'form-select tipo-local-select'
        self.fields['fornecedor'].widget.attrs['class'] = 'form-select fornecedor-select'

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        fornecedor = cleaned_data.get('fornecedor')

        if tipo == 'terceiros' and not fornecedor:
            self.add_error('fornecedor', 'Fornecedor é obrigatório para estoque em terceiros.')

        if tipo == 'proprio' and fornecedor:
            self.add_error('fornecedor', 'Não informe fornecedor para estoque próprio.')

        return cleaned_data


class LocalEstoqueFiltroForm(BaseFiltroForm):
    """Formulário de filtro para locais de estoque"""

    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + list(TIPO_LOCAL_ESTOQUE_CHOICES),
        label='Tipo'
    )
    ativo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('1', 'Ativos'), ('0', 'Inativos')],
        label='Status'
    )


# ===============================================
# TIPO MOVIMENTO ENTRADA
# ===============================================

class TipoMovimentoEntradaForm(BaseModelForm, AuditMixin):
    """Formulário para cadastro de tipos de movimento de entrada"""

    class Meta:
        model = TipoMovimentoEntrada
        fields = [
            'codigo', 'descricao', 'tipo_parceiro', 'tipo_produto', 'tipo_operacao',
            'exige_nota_fiscal', 'movimenta_terceiros', 'observacoes', 'ativo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ex: 1101, 1202, 1902'
            }),
            'descricao': forms.TextInput(attrs={
                'placeholder': 'Ex: Compra de Matéria Prima'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Observações sobre este tipo de entrada'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = True
        self.fields['descricao'].required = True


class TipoMovimentoEntradaFiltroForm(BaseFiltroForm):
    """Formulário de filtro para tipos de movimento de entrada"""

    tipo_parceiro = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(TIPO_PARCEIRO_CHOICES),
        label='Tipo Parceiro'
    )
    ativo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('1', 'Ativos'), ('0', 'Inativos')],
        label='Status'
    )


# ===============================================
# TIPO MOVIMENTO SAÍDA
# ===============================================

class TipoMovimentoSaidaForm(BaseModelForm, AuditMixin):
    """Formulário para cadastro de tipos de movimento de saída"""

    class Meta:
        model = TipoMovimentoSaida
        fields = [
            'codigo', 'descricao', 'tipo_parceiro', 'tipo_produto', 'tipo_operacao',
            'exige_nota_fiscal', 'movimenta_terceiros', 'observacoes', 'ativo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ex: 5101, 5901, 5949'
            }),
            'descricao': forms.TextInput(attrs={
                'placeholder': 'Ex: Venda de Produto, Remessa p/ Beneficiamento'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Observações sobre este tipo de saída'
            }),
        }
        help_texts = {
            'tipo_parceiro': 'Define se o campo Cliente ou Fornecedor será exibido na saída',
            'exige_nota_fiscal': 'Se marcado, será obrigatório informar NF ao lançar saída deste tipo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = True
        self.fields['descricao'].required = True


class TipoMovimentoSaidaFiltroForm(BaseFiltroForm):
    """Formulário de filtro para tipos de movimento de saída"""

    tipo_parceiro = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(TIPO_PARCEIRO_CHOICES),
        label='Tipo Parceiro'
    )
    ativo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('1', 'Ativos'), ('0', 'Inativos')],
        label='Status'
    )


# ===============================================
# MOVIMENTO DE ENTRADA
# ===============================================

class MovimentoEntradaForm(BaseModelForm, AuditMixin):
    """Formulário para movimento de entrada"""

    class Meta:
        model = MovimentoEntrada
        fields = [
            'tipo_movimento', 'fornecedor', 'cliente', 'pedido_compra',
            'numero_nf', 'serie_nf', 'chave_acesso', 'data_emissao_nf',
            'data_movimento', 'data_entrada',
            'valor_frete', 'valor_desconto', 'observacoes'
        ]
        widgets = {
            'data_movimento': forms.DateInput(attrs={'type': 'date'}),
            'data_entrada': forms.DateInput(attrs={'type': 'date'}),
            'data_emissao_nf': forms.DateInput(attrs={'type': 'date'}),
            'numero_nf': forms.TextInput(attrs={'placeholder': 'Número da NF (opcional)'}),
            'serie_nf': forms.TextInput(attrs={'placeholder': 'Série'}),
            'chave_acesso': forms.TextInput(attrs={'placeholder': 'Chave de acesso NFe (44 dígitos)'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
            'valor_frete': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_desconto': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tipo de movimento - apenas ativos e tipo_operacao='movto'
        self.fields['tipo_movimento'].queryset = TipoMovimentoEntrada.objects.filter(
            ativo=True, tipo_operacao='movto'
        )

        # Fornecedores ativos
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
        self.fields['fornecedor'].required = False

        # Clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome')
        self.fields['cliente'].required = False

        # Pedidos de compra em aberto
        self.fields['pedido_compra'].queryset = PedidoCompra.objects.filter(
            status__in=['confirmado', 'parcial']
        ).order_by('-data_emissao')
        self.fields['pedido_compra'].required = False

        # Classes CSS para JS dinâmico
        self.fields['tipo_movimento'].widget.attrs['class'] = 'form-select tipo-movimento-select'
        self.fields['fornecedor'].widget.attrs['class'] = 'form-select parceiro-fornecedor'
        self.fields['cliente'].widget.attrs['class'] = 'form-select parceiro-cliente'

    def clean(self):
        cleaned_data = super().clean()
        tipo_movimento = cleaned_data.get('tipo_movimento')

        if tipo_movimento:
            # Validar parceiro baseado no tipo
            tipo_parceiro = tipo_movimento.tipo_parceiro
            fornecedor = cleaned_data.get('fornecedor')
            cliente = cleaned_data.get('cliente')

            if tipo_parceiro == 'fornecedor' and not fornecedor:
                self.add_error('fornecedor', 'Fornecedor é obrigatório para este tipo de movimento.')
            if tipo_parceiro == 'cliente' and not cliente:
                self.add_error('cliente', 'Cliente é obrigatório para este tipo de movimento.')

            # Validar NF se exigida
            if tipo_movimento.exige_nota_fiscal and not cleaned_data.get('numero_nf'):
                self.add_error('numero_nf', 'Nota Fiscal é obrigatória para este tipo de movimento.')

        return cleaned_data


class ItemMovimentoEntradaForm(forms.ModelForm):
    """Formulário para item de movimento de entrada"""

    class Meta:
        model = ItemMovimentoEntrada
        fields = ['produto', 'quantidade', 'unidade', 'valor_unitario', 'lote', 'data_validade', 'observacoes']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'step': '0.0001', 'min': '0.0001', 'class': 'form-control item-quantidade'}),
            'valor_unitario': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'class': 'form-control item-valor-unitario'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control item-unidade', 'readonly': True}),
            'lote': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lote (opcional)'}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Obs.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Produtos ativos (matérias-primas)
        self.fields['produto'].queryset = Produto.objects.filter(status='ATIVO').order_by('codigo')
        self.fields['produto'].widget.attrs['class'] = 'form-select item-produto'


class MovimentoEntradaFiltroForm(BaseFiltroForm):
    """Formulário de filtro para movimentos de entrada"""

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(STATUS_MOVIMENTO_CHOICES),
        label='Status'
    )
    tipo_movimento = forms.ModelChoiceField(
        required=False,
        queryset=TipoMovimentoEntrada.objects.filter(ativo=True, tipo_operacao='movto'),
        label='Tipo',
        empty_label='Todos'
    )
    data_de = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data De'
    )
    data_ate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data Até'
    )
    fornecedor = forms.ModelChoiceField(
        required=False,
        queryset=Fornecedor.objects.filter(ativo=True).order_by('razao_social'),
        label='Fornecedor',
        empty_label='Todos'
    )


# ===============================================
# MOVIMENTO DE SAÍDA
# ===============================================

class MovimentoSaidaForm(BaseModelForm, AuditMixin):
    """Formulário para movimento de saída"""

    class Meta:
        model = MovimentoSaida
        fields = [
            'tipo_movimento', 'fornecedor', 'cliente',
            'numero_nf', 'serie_nf', 'chave_acesso', 'data_emissao_nf',
            'data_movimento', 'data_saida',
            'valor_frete', 'valor_desconto', 'observacoes'
        ]
        widgets = {
            'data_movimento': forms.DateInput(attrs={'type': 'date'}),
            'data_saida': forms.DateInput(attrs={'type': 'date'}),
            'data_emissao_nf': forms.DateInput(attrs={'type': 'date'}),
            'numero_nf': forms.TextInput(attrs={'placeholder': 'Número da NF (opcional)'}),
            'serie_nf': forms.TextInput(attrs={'placeholder': 'Série'}),
            'chave_acesso': forms.TextInput(attrs={'placeholder': 'Chave de acesso NFe (44 dígitos)'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
            'valor_frete': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_desconto': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tipo de movimento - apenas ativos e tipo_operacao='movto'
        self.fields['tipo_movimento'].queryset = TipoMovimentoSaida.objects.filter(
            ativo=True, tipo_operacao='movto'
        )

        # Fornecedores ativos
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
        self.fields['fornecedor'].required = False

        # Clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome')
        self.fields['cliente'].required = False

        # Classes CSS para JS dinâmico
        self.fields['tipo_movimento'].widget.attrs['class'] = 'form-select tipo-movimento-select'
        self.fields['fornecedor'].widget.attrs['class'] = 'form-select parceiro-fornecedor'
        self.fields['cliente'].widget.attrs['class'] = 'form-select parceiro-cliente'

    def clean(self):
        cleaned_data = super().clean()
        tipo_movimento = cleaned_data.get('tipo_movimento')

        if tipo_movimento:
            # Validar parceiro baseado no tipo
            tipo_parceiro = tipo_movimento.tipo_parceiro
            fornecedor = cleaned_data.get('fornecedor')
            cliente = cleaned_data.get('cliente')

            if tipo_parceiro == 'fornecedor' and not fornecedor:
                self.add_error('fornecedor', 'Fornecedor é obrigatório para este tipo de movimento.')
            if tipo_parceiro == 'cliente' and not cliente:
                self.add_error('cliente', 'Cliente é obrigatório para este tipo de movimento.')

            # Validar NF se exigida
            if tipo_movimento.exige_nota_fiscal and not cleaned_data.get('numero_nf'):
                self.add_error('numero_nf', 'Nota Fiscal é obrigatória para este tipo de movimento.')

        return cleaned_data


class ItemMovimentoSaidaForm(forms.ModelForm):
    """Formulário para item de movimento de saída"""

    class Meta:
        model = ItemMovimentoSaida
        fields = ['produto', 'quantidade', 'unidade', 'valor_unitario', 'lote', 'observacoes']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'step': '0.0001', 'min': '0.0001', 'class': 'form-control item-quantidade'}),
            'valor_unitario': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'class': 'form-control item-valor-unitario'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control item-unidade', 'readonly': True}),
            'lote': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lote (opcional)'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Obs.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Produtos ativos
        self.fields['produto'].queryset = Produto.objects.filter(status='ATIVO').order_by('codigo')
        self.fields['produto'].widget.attrs['class'] = 'form-select item-produto'


class MovimentoSaidaFiltroForm(BaseFiltroForm):
    """Formulário de filtro para movimentos de saída"""

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(STATUS_MOVIMENTO_CHOICES),
        label='Status'
    )
    tipo_movimento = forms.ModelChoiceField(
        required=False,
        queryset=TipoMovimentoSaida.objects.filter(ativo=True, tipo_operacao='movto'),
        label='Tipo',
        empty_label='Todos'
    )
    data_de = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data De'
    )
    data_ate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data Até'
    )
    cliente = forms.ModelChoiceField(
        required=False,
        queryset=Cliente.objects.filter(ativo=True).order_by('nome'),
        label='Cliente',
        empty_label='Todos'
    )


# ===============================================
# ORDEM DE PRODUCAO - FASE 4
# ===============================================

class OrdemProducaoForm(BaseModelForm, AuditMixin):
    """Formulario para Ordem de Producao"""

    class Meta:
        model = OrdemProducao
        fields = [
            'produto', 'quantidade_planejada', 'prioridade',
            'local_producao', 'local_destino',
            'data_inicio_planejada', 'data_fim_planejada',
            'proposta', 'observacoes'
        ]
        widgets = {
            'quantidade_planejada': forms.NumberInput(attrs={
                'step': '0.0001', 'min': '0.0001', 'class': 'form-control'
            }),
            'prioridade': forms.NumberInput(attrs={
                'min': '1', 'max': '10', 'class': 'form-control'
            }),
            'data_inicio_planejada': forms.DateInput(attrs={'type': 'date'}),
            'data_fim_planejada': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Produtos que podem ser produzidos (PA e PI montados)
        self.fields['produto'].queryset = Produto.objects.filter(
            status='ATIVO'
        ).filter(
            # PA ou PI com estrutura
            tipo__in=['PA', 'PI']
        ).order_by('codigo')
        self.fields['produto'].widget.attrs['class'] = 'form-select'

        # Locais de estoque proprios
        locais_proprios = LocalEstoque.objects.filter(ativo=True, tipo='proprio')
        self.fields['local_producao'].queryset = locais_proprios
        self.fields['local_destino'].queryset = locais_proprios

        # Proposta opcional
        self.fields['proposta'].required = False

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade_planejada')

        if produto and quantidade:
            # Verificar se produto tem estrutura
            if not produto.componentes.exists():
                self.add_error(
                    'produto',
                    f'O produto {produto.codigo} nao possui estrutura de componentes cadastrada.'
                )

        return cleaned_data


class OrdemProducaoFiltroForm(BaseFiltroForm):
    """Formulario de filtro para Ordens de Producao"""

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(STATUS_OP_CHOICES),
        label='Status'
    )
    prioridade = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('1', '1 - Urgente'),
            ('5', '5 - Normal'),
            ('10', '10 - Baixa'),
        ],
        label='Prioridade'
    )
    data_de = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data De'
    )
    data_ate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data Ate'
    )
    produto = forms.ModelChoiceField(
        required=False,
        queryset=Produto.objects.filter(tipo__in=['PA', 'PI']).order_by('codigo'),
        label='Produto',
        empty_label='Todos'
    )


class ApontamentoProducaoForm(forms.Form):
    """Formulario para apontamento de producao"""

    quantidade_produzida = forms.DecimalField(
        max_digits=12,
        decimal_places=4,
        min_value=0.0001,
        label='Quantidade Produzida',
        widget=forms.NumberInput(attrs={
            'step': '0.0001',
            'min': '0.0001',
            'class': 'form-control'
        })
    )
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        label='Observacoes'
    )


# ===============================================
# REQUISIÇÃO DE MATERIAL
# ===============================================

from core.models.estoque import (
    RequisicaoMaterial,
    ItemRequisicaoMaterial,
    STATUS_REQUISICAO_MATERIAL_CHOICES,
    TIPO_PRODUTO_MOVIMENTO_CHOICES,
)
from core.models import Proposta


class RequisicaoMaterialForm(BaseModelForm, AuditMixin):
    """Formulário para Requisição de Material"""

    class Meta:
        model = RequisicaoMaterial
        fields = [
            'tipo_movimento', 'proposta',
            'data_requisicao', 'data_necessidade',
            'observacoes'
        ]
        widgets = {
            'data_requisicao': forms.DateInput(attrs={'type': 'date'}),
            'data_necessidade': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Tipo de movimento - apenas ativos e tipo_operacao='op'
        self.fields['tipo_movimento'].queryset = TipoMovimentoSaida.objects.filter(
            ativo=True, tipo_operacao='op'
        ).order_by('codigo')
        self.fields['tipo_movimento'].widget.attrs['class'] = 'form-select tipo-movimento-select'

        # Propostas liberadas para produção - mostrar OP
        self.fields['proposta'].queryset = Proposta.objects.filter(
            data_liberacao_producao__isnull=False
        ).order_by('-numero_op')
        self.fields['proposta'].label_from_instance = lambda obj: f"OP {obj.numero_op} - {obj.cliente.nome}" if obj.numero_op else obj.numero
        self.fields['proposta'].widget.attrs['class'] = 'form-select'
        self.fields['proposta'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and not instance.pk:
            instance.criado_por = self.user
        elif self.user:
            instance.atualizado_por = self.user
        if commit:
            instance.save()
        return instance


class ItemRequisicaoMaterialForm(forms.ModelForm):
    """Formulário para item de Requisição de Material"""

    class Meta:
        model = ItemRequisicaoMaterial
        fields = ['produto', 'quantidade_solicitada', 'unidade', 'observacoes']
        widgets = {
            'quantidade_solicitada': forms.NumberInput(attrs={
                'step': '0.0001', 'min': '0.0001', 'class': 'form-control form-control-sm item-quantidade'
            }),
            'unidade': forms.TextInput(attrs={
                'class': 'form-control form-control-sm item-unidade', 'readonly': True
            }),
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control form-control-sm', 'placeholder': 'Obs.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Produtos ativos
        self.fields['produto'].queryset = Produto.objects.filter(
            status='ATIVO'
        ).order_by('codigo')
        self.fields['produto'].widget.attrs['class'] = 'form-select form-select-sm item-produto'


# Formset para itens de Requisição de Material
ItemRequisicaoFormSet = forms.inlineformset_factory(
    RequisicaoMaterial,
    ItemRequisicaoMaterial,
    form=ItemRequisicaoMaterialForm,
    fields=['produto', 'quantidade_solicitada', 'unidade', 'observacoes'],
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)


class RequisicaoMaterialFiltroForm(BaseFiltroForm):
    """Formulário de filtro para Requisições de Material"""

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(STATUS_REQUISICAO_MATERIAL_CHOICES),
        label='Status'
    )
    tipo_movimento = forms.ModelChoiceField(
        required=False,
        queryset=TipoMovimentoSaida.objects.filter(ativo=True, tipo_operacao='op'),
        label='Tipo',
        empty_label='Todos'
    )
    data_de = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data De'
    )
    data_ate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data Até'
    )
