# core/forms/producao.py

"""
Formulários relacionados ao fluxo de produção:
Lista de Materiais → Requisição de Compras → Orçamento → Pedido de Compra
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

from core.models import (
    ListaMateriais, ItemListaMateriais,
    RequisicaoCompra, ItemRequisicaoCompra,
    OrcamentoCompra, ItemOrcamentoCompra, HistoricoOrcamentoCompra,
    Fornecedor, Produto, Proposta
)
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, MoneyInput, QuantityInput, CustomDateInput, DateAwareModelForm
from core.choices import get_prioridade_pedido_choices

# =============================================================================
# LISTA DE MATERIAIS
# =============================================================================

class ListaMateriaisForm(BaseModelForm, AuditMixin):
    """Formulário para lista de materiais"""
    
    class Meta:
        model = ListaMateriais
        fields = ['status', 'observacoes', 'observacoes_internas']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'observacoes_internas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
        labels = {
            'status': 'Status',
            'observacoes': 'Observações',
            'observacoes_internas': 'Observações Internas',
        }


class ItemListaMateriaisForm(BaseModelForm):
    """Formulário para itens da lista de materiais"""
    
    class Meta:
        model = ItemListaMateriais
        fields = ['produto', 'quantidade', 'valor_unitario_estimado', 'observacoes']
        widgets = {
            'produto': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'quantidade': QuantityInput(),
            'valor_unitario_estimado': MoneyInput(),
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações do item...'
            }),
        }
        labels = {
            'produto': 'Produto',
            'quantidade': 'Quantidade',
            'valor_unitario_estimado': 'Valor Unitário Estimado',
            'observacoes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.filter(
            status='ATIVO',
            disponivel=True
        ).select_related('grupo', 'subgrupo').order_by('codigo')
        
        self.fields['produto'].required = True
        self.fields['quantidade'].required = True


# Formset para itens da lista de materiais
ItemListaMateriaisFormSet = inlineformset_factory(
    ListaMateriais,
    ItemListaMateriais,
    form=ItemListaMateriaisForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=['produto', 'quantidade', 'valor_unitario_estimado', 'observacoes']
)


# =============================================================================
# REQUISIÇÃO DE COMPRA
# =============================================================================

class RequisicaoCompraForm(DateAwareModelForm, AuditMixin):
    """Formulário para requisição de compra"""
    
    class Meta:
        model = RequisicaoCompra
        fields = [
            'lista_materiais', 'status', 'prioridade',
            'data_requisicao', 'data_necessidade',
            'solicitante', 'departamento',
            'justificativa', 'observacoes', 'observacoes_compras'
        ]
        widgets = {
            'lista_materiais': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_requisicao': CustomDateInput(),
            'data_necessidade': CustomDateInput(),
            'solicitante': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'departamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Produção, Engenharia...'
            }),
            'justificativa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Justificativa para a requisição...'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações gerais...'
            }),
            'observacoes_compras': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações do setor de compras...'
            }),
        }
        labels = {
            'lista_materiais': 'Lista de Materiais',
            'status': 'Status',
            'prioridade': 'Prioridade',
            'data_requisicao': 'Data da Requisição',
            'data_necessidade': 'Data de Necessidade',
            'solicitante': 'Solicitante',
            'departamento': 'Departamento',
            'justificativa': 'Justificativa',
            'observacoes': 'Observações',
            'observacoes_compras': 'Observações de Compras',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prioridade'].choices = get_prioridade_pedido_choices()
        
        # Filtrar apenas listas aprovadas
        self.fields['lista_materiais'].queryset = ListaMateriais.objects.filter(
            status='aprovada'
        ).select_related('proposta').order_by('-criado_em')
        
        # Filtrar usuários ativos
        from core.models import Usuario
        self.fields['solicitante'].queryset = Usuario.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Campos obrigatórios
        self.fields['lista_materiais'].required = False  # OPCIONAL - pode criar requisição sem lista
        self.fields['data_requisicao'].required = True
        self.fields['solicitante'].required = True
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['data_requisicao'].initial = date.today()
            self.fields['departamento'].initial = 'Produção'


class RequisicaoCompraFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de requisições"""
    
    STATUS_CHOICES = [
        ('', 'Todos os Status'),
        ('rascunho', 'Rascunho'),
        ('aberta', 'Aberta'),
        ('cotando', 'Em Cotação'),
        ('orcada', 'Orçada'),
        ('aprovada', 'Aprovada'),
        ('cancelada', 'Cancelada'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    prioridade = forms.ChoiceField(
        required=False,
        label='Prioridade',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    data_inicio = forms.DateField(
        required=False,
        label="Data Início",
        widget=CustomDateInput(attrs={
            'class': 'form-control'
        })
    )
    data_fim = forms.DateField(
        required=False,
        label="Data Fim",
        widget=CustomDateInput(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prioridade'].choices = [('', 'Todas as Prioridades')] + get_prioridade_pedido_choices()
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por número, proposta...'


# =============================================================================
# ITENS DA REQUISIÇÃO DE COMPRA
# =============================================================================

class ItemRequisicaoCompraForm(BaseModelForm):
    """Formulário para itens da requisição de compra - COM BUSCA DE PRODUTOS"""

    # Campo adicional para busca de produtos
    produto_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control produto-search-input',
            'placeholder': 'Digite código ou nome do produto...',
            'autocomplete': 'off',
        }),
        label='Buscar Produto'
    )

    class Meta:
        model = ItemRequisicaoCompra
        fields = ['produto', 'quantidade', 'valor_unitario_estimado', 'observacoes']
        widgets = {
            'produto': forms.HiddenInput(),  # Campo hidden, será preenchido via JS
            'quantidade': QuantityInput(attrs={
                'class': 'form-control'
            }),
            'valor_unitario_estimado': forms.HiddenInput(),  # Hidden - não obrigatório na requisição
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações do item...'
            }),
        }
        labels = {
            'produto': 'Produto Selecionado',
            'quantidade': 'Quantidade',
            'valor_unitario_estimado': 'Valor Unitário Estimado',
            'observacoes': 'Observações',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Se já tem produto selecionado, mostrar no campo de busca
        if self.instance.pk and self.instance.produto:
            produto = self.instance.produto
            self.fields['produto_search'].initial = f"{produto.codigo} - {produto.nome}"

        # Definir queryset para aceitar qualquer produto ativo
        self.fields['produto'].queryset = Produto.objects.filter(
            status='ATIVO'
        )

        # Campos obrigatórios
        self.fields['produto'].required = True
        self.fields['quantidade'].required = True
        self.fields['valor_unitario_estimado'].required = False  # NÃO OBRIGATÓRIO

    def clean_produto(self):
        """Validar produto selecionado"""
        produto = self.cleaned_data.get('produto')

        if not produto:
            raise ValidationError('Selecione um produto.')

        # Se recebeu UUID como string, buscar o produto
        if isinstance(produto, str):
            try:
                import uuid
                produto_uuid = uuid.UUID(produto)
                produto_obj = Produto.objects.get(pk=produto_uuid)
            except (ValueError, Produto.DoesNotExist) as e:
                raise ValidationError(f'Produto não encontrado: {produto}')
        else:
            produto_obj = produto

        # Verificar se produto está ativo
        if produto_obj.status != 'ATIVO':
            raise ValidationError('Produto selecionado não está ativo.')

        return produto_obj

    def clean_valor_unitario_estimado(self):
        """Permitir valor vazio (não obrigatório na requisição)"""
        valor = self.cleaned_data.get('valor_unitario_estimado')
        # Se vazio, retornar None
        if valor == '' or valor is None:
            return None
        return valor


# FORMSET PARA ITENS DA REQUISIÇÃO
ItemRequisicaoCompraFormSet = inlineformset_factory(
    RequisicaoCompra,
    ItemRequisicaoCompra,
    form=ItemRequisicaoCompraForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=['produto', 'quantidade', 'valor_unitario_estimado', 'observacoes']
)


# =============================================================================
# ORÇAMENTO DE COMPRA
# =============================================================================

class OrcamentoCompraForm(DateAwareModelForm, AuditMixin):
    """Formulário principal do orçamento de compra"""
    
    class Meta:
        model = OrcamentoCompra
        fields = [
            'titulo', 'requisicoes', 'status', 'prioridade',
            'data_orcamento', 'data_validade', 'data_necessidade',
            'comprador_responsavel', 'solicitante',
            'descricao', 'observacoes', 'observacoes_internas'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do orçamento...',
                'required': True
            }),
            'requisicoes': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_orcamento': CustomDateInput(),
            'data_validade': CustomDateInput(),
            'data_necessidade': CustomDateInput(),
            'comprador_responsavel': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'solicitante': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do orçamento...'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações gerais...'
            }),
            'observacoes_internas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações internas...'
            }),
        }
        labels = {
            'titulo': 'Título do Orçamento',
            'requisicoes': 'Requisições',
            'status': 'Status',
            'prioridade': 'Prioridade',
            'data_orcamento': 'Data do Orçamento',
            'data_validade': 'Data de Validade',
            'data_necessidade': 'Data de Necessidade',
            'comprador_responsavel': 'Comprador Responsável',
            'solicitante': 'Solicitante',
            'descricao': 'Descrição',
            'observacoes': 'Observações',
            'observacoes_internas': 'Observações Internas',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prioridade'].choices = get_prioridade_pedido_choices()
        
        # Filtrar apenas requisições que podem ser orçadas
        self.fields['requisicoes'].queryset = RequisicaoCompra.objects.filter(
            status__in=['aberta', 'cotando']
        ).select_related('lista_materiais__proposta').order_by('-data_requisicao')
        
        # Filtrar usuários ativos
        from core.models import Usuario
        usuarios_compras = Usuario.objects.filter(
            is_active=True,
            nivel__in=['admin', 'gestor', 'compras']
        ).order_by('first_name', 'last_name')
        
        self.fields['comprador_responsavel'].queryset = usuarios_compras
        self.fields['solicitante'].queryset = Usuario.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Campos obrigatórios
        self.fields['titulo'].required = True
        self.fields['data_orcamento'].required = True
        self.fields['comprador_responsavel'].required = True
        self.fields['solicitante'].required = True
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['data_orcamento'].initial = date.today()
            self.fields['data_validade'].initial = date.today() + timedelta(days=30)
    
    def clean_data_validade(self):
        """Validar data de validade"""
        data_validade = self.cleaned_data.get('data_validade')
        data_orcamento = self.cleaned_data.get('data_orcamento')
        
        if data_validade and data_orcamento:
            if data_validade <= data_orcamento:
                raise ValidationError('Data de validade deve ser posterior à data do orçamento.')
        
        return data_validade


class ItemOrcamentoCompraForm(BaseModelForm):
    """Formulário para itens do orçamento de compra"""
    
    class Meta:
        model = ItemOrcamentoCompra
        fields = [
            'produto', 'quantidade', 'valor_unitario_estimado',
            'fornecedor', 'valor_unitario_cotado', 'prazo_entrega',
            'observacoes', 'observacoes_cotacao'
        ]
        widgets = {
            'produto': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'quantidade': QuantityInput(),
            'valor_unitario_estimado': MoneyInput(),
            'fornecedor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'valor_unitario_cotado': MoneyInput(),
            'prazo_entrega': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': 'Dias'
            }),
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações do item...'
            }),
            'observacoes_cotacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações da cotação...'
            }),
        }
        labels = {
            'produto': 'Produto',
            'quantidade': 'Quantidade',
            'valor_unitario_estimado': 'Valor Unitário Estimado',
            'fornecedor': 'Fornecedor',
            'valor_unitario_cotado': 'Valor Unitário Cotado',
            'prazo_entrega': 'Prazo Entrega (dias)',
            'observacoes': 'Observações',
            'observacoes_cotacao': 'Observações da Cotação',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar produtos disponíveis
        self.fields['produto'].queryset = Produto.objects.filter(
            status='ATIVO',
            disponivel=True
        ).select_related('grupo', 'subgrupo').order_by('codigo')
        
        # Filtrar fornecedores ativos
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(
            ativo=True
        ).order_by('razao_social')
        
        # Campos obrigatórios
        self.fields['produto'].required = True
        self.fields['quantidade'].required = True
    
    def clean_quantidade(self):
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade is None or quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        return quantidade
    
    def clean_valor_unitario_cotado(self):
        valor = self.cleaned_data.get('valor_unitario_cotado')
        if valor is not None and valor <= 0:
            raise ValidationError('Valor unitário deve ser maior que zero.')
        return valor


# Formset para itens do orçamento
ItemOrcamentoCompraFormSet = inlineformset_factory(
    OrcamentoCompra,
    ItemOrcamentoCompra,
    form=ItemOrcamentoCompraForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=[
        'produto', 'quantidade', 'valor_unitario_estimado',
        'fornecedor', 'valor_unitario_cotado', 'prazo_entrega',
        'observacoes', 'observacoes_cotacao'
    ]
)


class OrcamentoCompraFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de orçamentos"""
    
    STATUS_CHOICES = [
        ('', 'Todos os Status'),
        ('rascunho', 'Rascunho'),
        ('cotando', 'Em Cotação'),
        ('cotado', 'Cotado'),
        ('analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('cancelado', 'Cancelado'),
    ]
    
    SITUACAO_CHOICES = [
        ('', 'Todas as Situações'),
        ('vigente', 'Vigentes'),
        ('vencido', 'Vencidos'),
        ('vence_hoje', 'Vencem Hoje'),
        ('vence_semana', 'Vencem esta Semana'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    prioridade = forms.ChoiceField(
        required=False,
        label='Prioridade',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    situacao = forms.ChoiceField(
        choices=SITUACAO_CHOICES,
        required=False,
        label='Situação',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    # CORREÇÃO: ModelChoiceField precisa de queryset definido
    comprador = forms.ModelChoiceField(
        queryset=None,  # Será definido no __init__
        required=False,
        empty_label="Todos os Compradores",
        label='Comprador',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    data_inicio = forms.DateField(
        required=False,
        label="Data Início",
        widget=CustomDateInput(attrs={
            'class': 'form-control'
        })
    )
    data_fim = forms.DateField(
        required=False,
        label="Data Fim",
        widget=CustomDateInput(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prioridade'].choices = [('', 'Todas as Prioridades')] + get_prioridade_pedido_choices()
        
        # Filtrar compradores - CORREÇÃO: definir queryset no __init__
        from core.models import Usuario
        self.fields['comprador'].queryset = Usuario.objects.filter(
            is_active=True,
            nivel__in=['admin', 'gestor', 'compras']
        ).order_by('first_name', 'last_name')
        
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por número, título...'


class AlterarStatusOrcamentoForm(BaseModelForm):
    """Formulário para alterar status dos orçamentos"""
    
    class Meta:
        model = OrcamentoCompra
        fields = ['status', 'observacoes_internas']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'observacoes_internas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a mudança de status...'
            }),
        }
        labels = {
            'status': 'Novo Status',
            'observacoes_internas': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Definir choices para status baseado no status atual
        if self.instance.pk:
            status_atual = self.instance.status
            
            all_status_choices = [
                ('rascunho', 'Rascunho'),
                ('cotando', 'Em Cotação'),
                ('cotado', 'Cotado'),
                ('analise', 'Em Análise'),
                ('aprovado', 'Aprovado'),
                ('rejeitado', 'Rejeitado'),
                ('cancelado', 'Cancelado'),
            ]
            
            status_choices = []
            
            if status_atual == 'rascunho':
                status_choices = [
                    ('rascunho', 'Rascunho'),
                    ('cotando', 'Em Cotação'),
                    ('cancelado', 'Cancelado'),
                ]
            elif status_atual == 'cotando':
                status_choices = [
                    ('cotando', 'Em Cotação'),
                    ('cotado', 'Cotado'),
                    ('cancelado', 'Cancelado'),
                ]
            elif status_atual == 'cotado':
                status_choices = [
                    ('cotado', 'Cotado'),
                    ('analise', 'Em Análise'),
                    ('cancelado', 'Cancelado'),
                ]
            elif status_atual == 'analise':
                status_choices = [
                    ('analise', 'Em Análise'),
                    ('aprovado', 'Aprovado'),
                    ('rejeitado', 'Rejeitado'),
                    ('cancelado', 'Cancelado'),
                ]
            else:
                # Para aprovado, rejeitado e cancelado, manter o status atual
                status_choices = [
                    (status_atual, next(display for value, display in all_status_choices if value == status_atual))
                ]
            
            self.fields['status'].choices = status_choices
        else:
            self.fields['status'].choices = [
                ('rascunho', 'Rascunho'),
                ('cotando', 'Em Cotação'),
                ('cotado', 'Cotado'),
                ('analise', 'Em Análise'),
                ('aprovado', 'Aprovado'),
                ('rejeitado', 'Rejeitado'),
                ('cancelado', 'Cancelado'),
            ]
        
        # Help text baseado no status atual
        if self.instance.pk:
            self.fields['status'].help_text = f"Status atual: {self.instance.get_status_display()}"
    
    def save(self, commit=True, user=None):
        """Override para registrar mudança de status no histórico"""
        orcamento = super().save(commit=False)
        
        if commit:
            # Verificar se o status mudou
            if self.instance.pk:
                orcamento_original = OrcamentoCompra.objects.get(pk=self.instance.pk)
                status_anterior = orcamento_original.status
                
                if status_anterior != orcamento.status:
                    # Salvar o orçamento primeiro
                    orcamento.save()
                    
                    # Criar registro no histórico
                    HistoricoOrcamentoCompra.objects.create(
                        orcamento=orcamento,
                        usuario=user,
                        acao=f'Status alterado de {status_anterior} para {orcamento.status}',
                        observacao=self.cleaned_data.get('observacoes_internas', '')
                    )
                else:
                    orcamento.save()
            else:
                orcamento.save()
        
        return orcamento