# core/forms/compras.py

"""
Formulários relacionados a pedidos de compra - ATUALIZADOS COM FORM-CONTROL
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

from core.models import PedidoCompra, ItemPedidoCompra, HistoricoPedidoCompra, Fornecedor, Produto, ParametrosGerais
from .base import BaseModelForm, BaseFiltroForm, AuditMixin, MoneyInput, QuantityInput, CustomDateInput, DateAwareModelForm
from core.choices import get_status_pedido_choices, get_prioridade_pedido_choices


class PedidoCompraForm(DateAwareModelForm, AuditMixin):
    """Formulário principal do pedido de compra - ATUALIZADO"""
    
    class Meta:
        model = PedidoCompra
        fields = [
            'fornecedor', 'data_emissao', 'prazo_entrega', 'data_entrega_prevista',
            'prioridade', 'condicao_pagamento', 'desconto_percentual',
            'valor_frete', 'observacoes', 'observacoes_internas',
            'comprador_responsavel', 'contato_compras'
        ]
        widgets = {
            'fornecedor': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'data_emissao': CustomDateInput(attrs={
                'class': 'form-control',
                'onchange': 'calcularDataEntrega()'
            }),
            'prazo_entrega': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dias',
                'min': '1',
                'step': '1',
                'onchange': 'calcularDataEntrega()'
            }),
            'data_entrega_prevista': CustomDateInput(attrs={
                'class': 'form-control',
                'onchange': 'calcularPrazoEntrega()'
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'condicao_pagamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 30/60/90 dias, À vista, etc.'
            }),
            'desconto_percentual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
            'valor_frete': MoneyInput(attrs={
                'class': 'form-control'
            }),
            'comprador_responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do comprador responsável'
            }),
            'contato_compras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email ou telefone de contato'
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
            'fornecedor': 'Fornecedor',
            'data_emissao': 'Data de Emissão',
            'prazo_entrega': 'Prazo (dias)',
            'data_entrega_prevista': 'Data Entrega Prevista',
            'prioridade': 'Prioridade',
            'condicao_pagamento': 'Condição de Pagamento',
            'desconto_percentual': 'Desconto (%)',
            'valor_frete': 'Valor do Frete',
            'comprador_responsavel': 'Comprador Responsável',
            'contato_compras': 'Contato de Compras',
            'observacoes': 'Observações Gerais',
            'observacoes_internas': 'Observações Internas',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prioridade'].choices = get_prioridade_pedido_choices() # Set choices dynamically
        
        # Filtrar apenas fornecedores ativos
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
        
        # Campos obrigatórios
        self.fields['fornecedor'].required = True
        self.fields['data_emissao'].required = True
        self.fields['prazo_entrega'].required = True
        
        # Valores padrão para novos pedidos
        if not self.instance.pk:
            self.fields['data_emissao'].initial = date.today()
            self.fields['prazo_entrega'].initial = 7
            
            # Preencher dados do comprador dos parâmetros
            try:
                parametros = ParametrosGerais.objects.first()
                if parametros:
                    if parametros.comprador_responsavel:
                        self.fields['comprador_responsavel'].initial = parametros.comprador_responsavel
                    if parametros.contato_compras:
                        self.fields['contato_compras'].initial = parametros.contato_compras
            except ParametrosGerais.DoesNotExist:
                pass
        
        # Help texts
        self.fields['prazo_entrega'].help_text = 'Prazo de entrega em dias úteis'
        self.fields['desconto_percentual'].help_text = 'Desconto em % sobre o valor total dos itens'
        self.fields['valor_frete'].help_text = 'Valor do frete a ser adicionado ao pedido'
        self.fields['comprador_responsavel'].help_text = 'Preenchido automaticamente dos parâmetros'
        self.fields['contato_compras'].help_text = 'Preenchido automaticamente dos parâmetros'
    
    def clean_prazo_entrega(self):
        """Validar prazo de entrega"""
        prazo = self.cleaned_data.get('prazo_entrega')
        if prazo is not None and prazo < 1:
            raise ValidationError('Prazo deve ser de pelo menos 1 dia.')
        return prazo
    
    def clean_desconto_percentual(self):
        """Validar desconto percentual"""
        desconto = self.cleaned_data.get('desconto_percentual')
        if desconto is not None and (desconto < 0 or desconto > 100):
            raise ValidationError('Desconto deve estar entre 0 e 100%.')
        return desconto
    
    def clean(self):
        """Validações customizadas"""
        cleaned_data = super().clean()
        data_emissao = cleaned_data.get('data_emissao')
        prazo_entrega = cleaned_data.get('prazo_entrega')
        data_entrega_prevista = cleaned_data.get('data_entrega_prevista')
        
        # Se temos emissão e prazo mas não temos data de entrega, calcular
        if data_emissao and prazo_entrega and not data_entrega_prevista:
            cleaned_data['data_entrega_prevista'] = data_emissao + timedelta(days=prazo_entrega)
        
        # Validar que data de entrega não é anterior à emissão
        if data_emissao and data_entrega_prevista:
            if data_entrega_prevista < data_emissao:
                self.add_error('data_entrega_prevista', 'Data de entrega não pode ser anterior à data de emissão.')
        
        return cleaned_data


# core/forms/compras.py - ATUALIZAR O ItemPedidoCompraForm

class ItemPedidoCompraForm(BaseModelForm):
    """Formulário para itens do pedido de compra - COM BUSCA DE PRODUTOS"""
    
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
        model = ItemPedidoCompra
        fields = ['produto', 'quantidade', 'valor_unitario', 'observacoes', 'item_requisicao']
        widgets = {
            'produto': forms.HiddenInput(),  # Campo hidden, será preenchido via JS
            'quantidade': QuantityInput(attrs={
                'class': 'form-control'
            }),
            'valor_unitario': MoneyInput(attrs={
                'class': 'form-control'
            }),
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações do item...'
            }),
            'item_requisicao': forms.Select(attrs={
                'class': 'form-control form-select-sm',
            }),
        }
        labels = {
            'produto': 'Produto Selecionado',
            'quantidade': 'Quantidade',
            'valor_unitario': 'Valor Unitário',
            'observacoes': 'Observações',
            'item_requisicao': 'Vincular à Requisição (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Se já tem produto selecionado, mostrar no campo de busca
        if self.instance.pk and self.instance.produto:
            produto = self.instance.produto
            self.fields['produto_search'].initial = f"{produto.codigo} - {produto.nome}"

        # Configurar campo item_requisicao (opcional)
        from core.models import ItemRequisicaoCompra
        self.fields['item_requisicao'].required = False
        self.fields['item_requisicao'].empty_label = "Sem vínculo com requisição"

        # Filtrar apenas itens de requisições abertas/aprovadas com saldo
        itens_requisicao = ItemRequisicaoCompra.objects.filter(
            requisicao__status__in=['aberta', 'aprovada']
        ).select_related('requisicao', 'produto')

        # Guardar mapeamento produto_id -> itens para uso no JavaScript
        # E coletar IDs de produtos com requisição
        self.produto_requisicoes = {}
        produtos_com_requisicao_ids = set()

        # Criar choices customizados com informação de saldo
        choices = [('', 'Sem vínculo com requisição')]
        for item in itens_requisicao:
            if item.quantidade_saldo > 0:
                label = f"Req {item.requisicao.numero} - {item.produto.codigo} (Saldo: {item.quantidade_saldo} {item.unidade})"
                choices.append((item.pk, label))

                # Mapear produto_id para esta requisição (para filtro JS)
                produto_id = str(item.produto.pk)
                if produto_id not in self.produto_requisicoes:
                    self.produto_requisicoes[produto_id] = []
                self.produto_requisicoes[produto_id].append({
                    'id': item.pk,
                    'label': label
                })

                # Adicionar produto aos IDs com requisição
                produtos_com_requisicao_ids.add(item.produto.pk)

        # Definir queryset para aceitar produtos ativos E (disponíveis OU com requisição)
        from django.db.models import Q
        self.fields['produto'].queryset = Produto.objects.filter(
            status='ATIVO'
        ).filter(
            Q(disponivel=True) |  # Produto disponível
            Q(pk__in=produtos_com_requisicao_ids)  # OU tem requisição aberta
        )

        self.fields['item_requisicao'].choices = choices
        self.fields['item_requisicao'].help_text = "Vincule este item a uma requisição para controlar o saldo"

        # Campos obrigatórios
        self.fields['produto'].required = True
        self.fields['quantidade'].required = True
        self.fields['valor_unitario'].required = True
    
    def clean_produto_search(self):
        """Validar que um produto foi selecionado"""
        produto_search = self.cleaned_data.get('produto_search')
        produto = self.cleaned_data.get('produto')
        
        # Se não tem produto selecionado mas tem texto de busca
        if produto_search and not produto:
            raise ValidationError(
                'Selecione um produto da lista de sugestões.'
            )
        
        return produto_search
    
    def clean_produto(self):
        """Validar produto selecionado"""
        produto = self.cleaned_data.get('produto')

        if not produto:
            raise ValidationError('Selecione um produto.')

        # 🔧 CORREÇÃO 2: Lidar com UUID string vs objeto Produto
        if isinstance(produto, str):
            try:
                # Se recebeu UUID como string, buscar o produto
                import uuid
                produto_uuid = uuid.UUID(produto)  # Validar formato UUID
                produto_obj = Produto.objects.get(pk=produto_uuid)
            except (ValueError, Produto.DoesNotExist) as e:
                # 🔍 DEBUG: Mostrar erro específico
                print(f"❌ ERRO UUID: {e} - Valor recebido: {produto}")
                raise ValidationError(f'Produto não encontrado: {produto}')
        else:
            # Se já é um objeto Produto
            produto_obj = produto

        # Verificar se produto está ativo e disponível
        if produto_obj.status != 'ATIVO' or not produto_obj.disponivel:
            raise ValidationError('Produto selecionado não está disponível.')

        # 🔧 CORREÇÃO 3: Retornar o objeto Produto, não a string
        return produto_obj

    def clean(self):
        """Validação cruzada entre campos"""
        cleaned_data = super().clean()
        item_requisicao = cleaned_data.get('item_requisicao')
        quantidade = cleaned_data.get('quantidade')
        produto = cleaned_data.get('produto')

        # Se vinculou a uma requisição, validar saldo e produto
        if item_requisicao and quantidade:
            # Verificar se o produto do pedido é o mesmo da requisição
            if produto and item_requisicao.produto != produto:
                self.add_error('item_requisicao',
                    f'O produto selecionado ({produto.codigo}) não corresponde ao produto da requisição ({item_requisicao.produto.codigo}).')

            # Verificar se não excede o saldo disponível
            if quantidade > item_requisicao.quantidade_saldo:
                self.add_error('quantidade',
                    f'Quantidade ({quantidade}) excede o saldo disponível ({item_requisicao.quantidade_saldo} {item_requisicao.unidade}).')

        return cleaned_data


# FORMSET PARA ITENS DO PEDIDO
ItemPedidoCompraFormSet = inlineformset_factory(
    PedidoCompra,
    ItemPedidoCompra,
    form=ItemPedidoCompraForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=['produto', 'quantidade', 'valor_unitario', 'observacoes', 'item_requisicao']
)


class PedidoCompraFiltroForm(BaseFiltroForm):
    """Formulário para filtros na listagem de pedidos"""
    
    STATUS_PRAZO_CHOICES = [
        ('', 'Todos os Prazos'),
        ('vencido', 'Vencidos'),
        ('urgente', 'Urgentes'),
        ('em_dia', 'Em Dia'),
    ]
    
    fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.filter(ativo=True).order_by('razao_social'),
        required=False,
        empty_label="Todos os Fornecedores",
        label='Fornecedor',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    status = forms.ChoiceField(
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
    status_prazo = forms.ChoiceField(
        choices=STATUS_PRAZO_CHOICES,
        required=False,
        label='Status Prazo',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    data_inicio = forms.DateField(
        required=False,
        label="Data Emissão Início",
        widget=CustomDateInput(attrs={
            'class': 'form-control'
        })
    )
    data_fim = forms.DateField(
        required=False,
        label="Data Emissão Fim",
        widget=CustomDateInput(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('', 'Todos os Status')] + get_status_pedido_choices() # Set dynamically
        self.fields['prioridade'].choices = [('', 'Todas as Prioridades')] + get_prioridade_pedido_choices() # Set dynamically
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por número, fornecedor...'


class AlterarStatusPedidoForm(BaseModelForm):
    """Formulário para alterar status dos pedidos de compra"""
    
    class Meta:
        model = PedidoCompra
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
            
            # Use a copy of the original choices to modify
            all_status_choices = list(get_status_pedido_choices())
            status_choices = []

            if status_atual == 'RASCUNHO':
                status_choices = [
                    ('RASCUNHO', 'Rascunho'),
                    ('ENVIADO', 'Enviado'),
                    ('CANCELADO', 'Cancelado'),
                ]
            elif status_atual == 'ENVIADO':
                status_choices = [
                    ('ENVIADO', 'Enviado'),
                    ('CONFIRMADO', 'Confirmado'),
                    ('CANCELADO', 'Cancelado'),
                ]
            elif status_atual == 'CONFIRMADO':
                status_choices = [
                    ('CONFIRMADO', 'Confirmado'),
                    ('PARCIAL', 'Parcialmente Recebido'),
                    ('RECEBIDO', 'Recebido'),
                ]
            elif status_atual == 'PARCIAL':
                status_choices = [
                    ('PARCIAL', 'Parcialmente Recebido'),
                    ('RECEBIDO', 'Recebido'),
                ]
            else:
                # Para RECEBIDO e CANCELADO, apenas manter o status atual
                status_choices = [
                    (status_atual, next(display for value, display in all_status_choices if value == status_atual))
                ]
            
            self.fields['status'].choices = status_choices
        else:
            # For new instances, allow all choices or a default subset
            self.fields['status'].choices = get_status_pedido_choices()

        # Help text baseado no status atual
        if self.instance.pk:
            self.fields['status'].help_text = f"Status atual: {self.instance.get_status_display()}"
    
    def save(self, commit=True, user=None):
        """Override para registrar mudança de status no histórico"""
        pedido = super().save(commit=False)
        
        if commit:
            # Verificar se o status mudou
            if self.instance.pk:
                pedido_original = PedidoCompra.objects.get(pk=self.instance.pk)
                status_anterior = pedido_original.status
                
                if status_anterior != pedido.status:
                    # Salvar o pedido primeiro
                    pedido.save()
                    
                    # Criar registro no histórico
                    HistoricoPedidoCompra.objects.create(
                        pedido=pedido,
                        usuario=user,
                        acao=f'Status alterado de {status_anterior} para {pedido.status}',
                        observacao=self.cleaned_data.get('observacoes_internas', '')
                    )
                else:
                    pedido.save()
            else:
                pedido.save()
        
        return pedido


class RecebimentoItemForm(forms.Form):
    """Formulário para registrar recebimento de itens do pedido"""
    
    quantidade_recebida = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=QuantityInput(attrs={
            'class': 'form-control'
        }),
        label='Quantidade Recebida'
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observações sobre o recebimento...'
        }),
        label='Observações'
    )
    
    def __init__(self, *args, **kwargs):
        self.item_pedido = kwargs.pop('item_pedido', None)
        super().__init__(*args, **kwargs)
        
        if self.item_pedido:
            # Calcular quantidade pendente
            quantidade_pendente = self.item_pedido.quantidade_pendente
            
            # Definir valor máximo e inicial
            self.fields['quantidade_recebida'].max_value = quantidade_pendente
            self.fields['quantidade_recebida'].initial = quantidade_pendente
            
            # Help text informativo
            self.fields['quantidade_recebida'].help_text = f"""
                Quantidade pedida: {self.item_pedido.quantidade}<br>
                Já recebido: {self.item_pedido.quantidade_recebida}<br>
                Pendente: {quantidade_pendente}
            """
    
    def clean_quantidade_recebida(self):
        """Validar quantidade recebida"""
        quantidade = self.cleaned_data.get('quantidade_recebida')
        
        if self.item_pedido and quantidade:
            quantidade_pendente = self.item_pedido.quantidade_pendente
            
            if quantidade > quantidade_pendente:
                raise ValidationError(
                    f'Quantidade recebida ({quantidade}) não pode ser maior que '
                    f'a quantidade pendente ({quantidade_pendente})'
                )
            
            if quantidade <= 0:
                raise ValidationError('Quantidade deve ser maior que zero')
        
        return quantidade


class RecebimentoPedidoForm(forms.Form):
    """Formulário para recebimento completo ou parcial do pedido"""
    
    TIPO_RECEBIMENTO_CHOICES = [
        ('PARCIAL', 'Recebimento Parcial'),
        ('TOTAL', 'Recebimento Total'),
    ]
    
    tipo_recebimento = forms.ChoiceField(
        choices=TIPO_RECEBIMENTO_CHOICES,
        widget=forms.RadioSelect(attrs={
            'onchange': 'toggleRecebimentoOptions(this.value)'
        }),
        label='Tipo de Recebimento'
    )
    
    observacoes_gerais = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações gerais sobre o recebimento...'
        }),
        label='Observações Gerais'
    )
    
    def __init__(self, *args, **kwargs):
        self.pedido = kwargs.pop('pedido', None)
        super().__init__(*args, **kwargs)
        
        if self.pedido:
            # Adicionar campos dinâmicos para cada item do pedido
            for item in self.pedido.itens.all():
                quantidade_pendente = item.quantidade_pendente
                
                if quantidade_pendente > 0:  # Só mostrar itens pendentes
                    field_name = f'item_{item.id}_quantidade'
                    self.fields[field_name] = forms.DecimalField(
                        max_digits=10,
                        decimal_places=2,
                        min_value=0,
                        max_value=quantidade_pendente,
                        initial=quantidade_pendente,
                        required=False,
                        widget=QuantityInput(attrs={
                            'class': 'form-control'
                        }),
                        label=f'{item.produto.nome} (Pendente: {quantidade_pendente})'
                    )
                    
                    # Campo de observações por item
                    obs_field_name = f'item_{item.id}_observacoes'
                    self.fields[obs_field_name] = forms.CharField(
                        required=False,
                        widget=forms.TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Observações do item...'
                        }),
                        label='Observações'
                    )
    
    def clean(self):
        """Validações do formulário"""
        cleaned_data = super().clean()
        
        # Verificar se pelo menos um item foi marcado para recebimento
        tem_quantidade = False
        
        for field_name, value in cleaned_data.items():
            if field_name.startswith('item_') and field_name.endswith('_quantidade'):
                if value and value > 0:
                    tem_quantidade = True
                    break
        
        if not tem_quantidade:
            raise ValidationError(
                'Pelo menos um item deve ter quantidade maior que zero para recebimento.'
            )
        
        return cleaned_data