# core/forms/propostas.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from core.models import (
    Proposta, Cliente, Usuario, AnexoProposta, VistoriaHistorico
)
from .base import (
    BaseModelForm, AuditMixin, ValidacaoComumMixin, MoneyInput, 
    QuantityInput, PercentageInput, CustomDateInput
)

class PropostaClienteElevadorForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """
    Formulário Step 1: Projeto + Elevador + Poço
    ATUALIZADO: Agora inclui vendedor e documentacao_prefeitura
    """
    class Meta:
        model = Proposta
        fields = [
            # ✅ DADOS DO PROJETO (reorganizado)
            'vendedor',  # ← MOVIDO do Step 3 para Step 1
            'cliente',
            'nome_projeto',
            'faturado_por',
            'normas_abnt', 
            'documentacao_prefeitura',  # ← MOVIDO do Step 3 para Step 1
            'local_instalacao',
                    
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
            # ✅ PROJETO
            'vendedor': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'nome_projeto': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'faturado_por': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'normas_abnt': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'documentacao_prefeitura': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'local_instalacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            
            # Elevador
            'modelo_elevador': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'capacidade_pessoas': QuantityInput(attrs={
                'min': 1,
                'max': 50,
                'placeholder': '0',
                'step': 1,
            }),
            'capacidade': QuantityInput(attrs={
                'min': 50,
                'max': 10000,
                'step': 10,
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
            'largura_poco': QuantityInput(attrs={
                'min': 0.8,
                'max': 10,
                'step': 0.01
            }),
            'comprimento_poco': QuantityInput(attrs={
                'min': 0.8,
                'max': 10,
                'step': 0.01
            }),
            'altura_poco': QuantityInput(attrs={
                'min': 2.0,
                'max': 50,
                'step': 0.01
            }),
            'pavimentos': QuantityInput(attrs={
                'min': 2,
                'max': 50,
                'step': 1,
                'placeholder': '0',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ CONFIGURAR VENDEDORES
        self.fields['vendedor'].queryset = Usuario.objects.filter(
            nivel='vendedor', 
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['vendedor'].empty_label = "-- Selecione um vendedor --"
        
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

        # ✅ VALIDAÇÃO DO VENDEDOR (agora obrigatório no Step 1)
        vendedor = cleaned_data.get('vendedor')
        if not vendedor:
            self.add_error('vendedor', 'Vendedor é obrigatório.')

        # Validações do elevador (mantidas)
        modelo_elevador = cleaned_data.get('modelo_elevador')
        capacidade_pessoas = cleaned_data.get('capacidade_pessoas')
        capacidade_kg_from_post = cleaned_data.get('capacidade')

        if modelo_elevador == 'Passageiro':
            if not capacidade_pessoas or capacidade_pessoas <= 0:
                self.add_error('capacidade_pessoas', 'Para elevador de Passageiro, a capacidade em pessoas é obrigatória e deve ser maior que zero.')
                cleaned_data['capacidade'] = None
            else:
                # Sobrescreve o valor de 'capacidade' com o valor calculado
                cleaned_data['capacidade'] = capacidade_pessoas * 80
        else: # Para outros modelos (Carga, etc.)
            if not capacidade_kg_from_post or float(capacidade_kg_from_post) <= 0:
                self.add_error('capacidade', 'Para este modelo de elevador, a capacidade em kg é obrigatória e deve ser maior que zero.')
                cleaned_data['capacidade'] = None

        # Lógica para Acionamento, Tração e Contrapeso
        acionamento = cleaned_data.get('acionamento')
        if acionamento == 'Hidraulico':
            cleaned_data['tracao'] = None
            cleaned_data['contrapeso'] = None
        elif acionamento == 'Carretel':
            cleaned_data['contrapeso'] = None

        return cleaned_data


class PropostaCabinePortasForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """
    Formulário Step 2: Cabine + Portas (mantido igual)
    """
    class Meta:
        model = Proposta
        fields = [
            # Dados da Cabine
            'material_cabine',
            'espessura_cabine',
            'saida_cabine',
            'altura_cabine',
            'piso_cabine',
            'material_piso_cabine',
            
            # Porta da Cabine
            'modelo_porta_cabine',
            'material_porta_cabine',
            'folhas_porta_cabine',
            'largura_porta_cabine',
            'altura_porta_cabine',
            
            # Porta do Pavimento
            'modelo_porta_pavimento',
            'material_porta_pavimento',
            'folhas_porta_pavimento',
            'largura_porta_pavimento',
            'altura_porta_pavimento',
        ]
        
        widgets = {
            # Cabine
            'material_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'saida_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'altura_cabine': QuantityInput(attrs={
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'piso_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_piso_cabine': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Porta Cabine
            'modelo_porta_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_porta_cabine': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'largura_porta_cabine': QuantityInput(attrs={
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'altura_porta_cabine': QuantityInput(attrs={
                'step': '0.01',
                'placeholder': '0,00'
            }),
            
            # Porta Pavimento
            'modelo_porta_pavimento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material_porta_pavimento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'largura_porta_pavimento': QuantityInput(attrs={
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'altura_porta_pavimento': QuantityInput(attrs={
                'step': '0.01',
                'placeholder': '0,00'
            }),
        }
class PropostaComercialForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    class Meta:
        model = Proposta
        fields = [
            'valor_proposta', 
            'numero_contrato',
            'data_contrato', 
            'data_vistoria_medicao',
            'prazo_entrega_dias',
            'data_validade',
            'previsao_conclusao_obra', 
            'forma_pagamento',
            'valor_entrada',
            'percentual_entrada',
            'data_vencimento_entrada',
            'numero_parcelas',
            'valor_parcela',
            'tipo_parcela',
            'primeira_parcela',
        ]
        
        widgets = {
            # ✅ VALOR SEM FORMATAÇÃO - widget simples
            'valor_proposta': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'style': 'font-weight: bold; font-size: 1.1em;',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'numero_contrato': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            
            # Datas
            'data_contrato': CustomDateInput(attrs={
                'class': 'form-control'
            }),
            'data_vistoria_medicao': CustomDateInput(attrs={
                'class': 'form-control'
            }),
            'data_validade': CustomDateInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'previsao_conclusao_obra': CustomDateInput(attrs={
                'class': 'form-control'
            }),
            'data_vencimento_entrada': CustomDateInput(attrs={
                'class': 'form-control'
            }),
            'primeira_parcela': CustomDateInput(attrs={
                'class': 'form-control'
            }),
            
            # Outros campos
            'prazo_entrega_dias': QuantityInput(attrs={
                'min': 1,
                'max': 365,
                'placeholder': '45',
                'required': True
            }),
            'forma_pagamento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            
            # ✅ VALORES DE ENTRADA SEM FORMATAÇÃO
            'valor_entrada': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'percentual_entrada': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'numero_parcelas': QuantityInput(attrs={
                'min': '1',
                'max': '60',
                'placeholder': '1'
            }),
            'valor_parcela': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'tipo_parcela': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        hoje = date.today()
        data_30_dias = hoje + timedelta(days=30)
        data_90_dias = hoje + timedelta(days=90)
        
        # Para NOVAS propostas (sem PK), definir valores padrão
        if not self.instance.pk:
            if not self.initial.get('data_contrato'):
                self.initial['data_contrato'] = hoje.strftime('%Y-%m-%d')
            
            if not self.initial.get('data_validade'):
                self.initial['data_validade'] = data_30_dias.strftime('%Y-%m-%d')
            
            if not self.initial.get('previsao_conclusao_obra'):
                self.initial['previsao_conclusao_obra'] = data_90_dias.strftime('%Y-%m-%d')
            
            if not self.initial.get('data_vistoria_medicao'):
                self.initial['data_vistoria_medicao'] = hoje.strftime('%Y-%m-%d')
            
            if not self.initial.get('primeira_parcela'):
                self.initial['primeira_parcela'] = data_30_dias.strftime('%Y-%m-%d')
        
        # Para propostas EXISTENTES, usar valores do banco ou definir padrões para campos vazios
        else:
            if not self.instance.data_contrato:
                self.initial['data_contrato'] = hoje.strftime('%Y-%m-%d')
            
            if not self.instance.data_vistoria_medicao:
                self.initial['data_vistoria_medicao'] = hoje.strftime('%Y-%m-%d')
            
            if not self.instance.data_validade:
                self.initial['data_validade'] = data_30_dias.strftime('%Y-%m-%d')
            
            if not self.instance.previsao_conclusao_obra:
                self.initial['previsao_conclusao_obra'] = data_90_dias.strftime('%Y-%m-%d')
            
            if not self.instance.primeira_parcela:
                self.initial['primeira_parcela'] = data_30_dias.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        
        # ✅ VALIDAÇÃO SIMPLES DO VALOR DA PROPOSTA
        valor_proposta = cleaned_data.get('valor_proposta')
        if not valor_proposta or float(valor_proposta) <= 0:
            self.add_error('valor_proposta', 'O valor da proposta é obrigatório e deve ser maior que zero.')
        
        # Validações da forma de pagamento
        forma_pagamento = cleaned_data.get('forma_pagamento')
        
        if forma_pagamento == 'vista':
            cleaned_data['numero_parcelas'] = 1
            cleaned_data['valor_entrada'] = None
            cleaned_data['percentual_entrada'] = None
            
        elif forma_pagamento == 'entrada_parcelas':
            valor_entrada = cleaned_data.get('valor_entrada')
            percentual_entrada = cleaned_data.get('percentual_entrada')
            numero_parcelas = cleaned_data.get('numero_parcelas', 0)
            
            if not valor_entrada and not percentual_entrada:
                raise ValidationError({
                    'valor_entrada': 'Informe o valor ou percentual da entrada.'
                })
            
            if numero_parcelas < 1:
                raise ValidationError({
                    'numero_parcelas': 'Informe o número de parcelas.'
                })
                
        elif forma_pagamento == 'parcelado':
            cleaned_data['valor_entrada'] = None
            cleaned_data['percentual_entrada'] = None
            
            numero_parcelas = cleaned_data.get('numero_parcelas', 0)
            if numero_parcelas < 1:
                raise ValidationError({
                    'numero_parcelas': 'Informe o número de parcelas.'
                })
        
        # Validar datas
        data_validade = cleaned_data.get('data_validade')
        if data_validade and data_validade <= date.today():
            raise ValidationError({
                'data_validade': 'A data de validade deve ser futura.'
            })
        
        previsao_conclusao_obra = cleaned_data.get('previsao_conclusao_obra')
        if previsao_conclusao_obra and previsao_conclusao_obra <= date.today():
            raise ValidationError({
                'previsao_conclusao_obra': 'A previsão de conclusão da obra deve ser futura.'
            })
        
        data_vistoria_medicao = cleaned_data.get('data_vistoria_medicao')
        if data_vistoria_medicao:
            data_limite_passado = date.today() - timedelta(days=30)
            if data_vistoria_medicao < data_limite_passado:
                raise ValidationError({
                    'data_vistoria_medicao': 'A data de vistoria/medição não pode ser muito antiga (máximo 30 dias no passado).'
                })
        
        return cleaned_data
class PropostaStatusForm(forms.ModelForm):
    """Formulário para alteração de status da proposta"""
    
    observacao_status = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        required=False,
        label="Observação"
    )
    
    class Meta:
        model = Proposta
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        # Limitar opções de status baseado no status atual
        if self.instance and self.instance.status:
            status_atual = self.instance.status
            if status_atual == 'rascunho':
                # De rascunho pode ir para aprovado ou rejeitado
                choices = [
                    ('rascunho', 'Rascunho'),
                    ('aprovado', 'Aprovado'),
                    ('rejeitado', 'Rejeitado'),
                ]
            elif status_atual == 'aprovado':
                # De aprovado só pode voltar para rascunho
                choices = [
                    ('aprovado', 'Aprovado'),
                    ('rascunho', 'Rascunho'),
                ]
            elif status_atual == 'rejeitado':
                # De rejeitado pode ir para rascunho ou aprovado
                choices = [
                    ('rejeitado', 'Rejeitado'),
                    ('rascunho', 'Rascunho'),
                    ('aprovado', 'Aprovado'),
                ]
            else:
                choices = Proposta.STATUS_CHOICES
            
            self.fields['status'].choices = choices


class ClienteCreateForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
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


class AnexoPropostaForm(BaseModelForm):
    """Formulário para upload de anexos"""
    
    class Meta:
        model = AnexoProposta
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
    
    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Validar tamanho do arquivo (máximo 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise ValidationError('Arquivo muito grande. Tamanho máximo: 10MB.')
            
            # Validar extensão
            import os
            nome, extensao = os.path.splitext(arquivo.name)
            extensoes_permitidas = [
                '.pdf', '.jpg', '.jpeg', '.png', 
                '.doc', '.docx', '.xls', '.xlsx'
            ]
            
            if extensao.lower() not in extensoes_permitidas:
                raise ValidationError(
                    f'Extensão não permitida. Use: {", ".join(extensoes_permitidas)}'
                )
        
        return arquivo


class PropostaValorForm(forms.ModelForm):
    """Formulário específico para edição rápida do valor da proposta"""
    
    class Meta:
        model = Proposta
        fields = ['valor_proposta']
        widgets = {
            'valor_proposta': MoneyInput(attrs={
                'required': True,
                'placeholder': '0,00',
                'class': 'form-control form-control-lg',
                'style': 'font-weight: bold; font-size: 1.2em;'
            })
        }
    
    def clean_valor_proposta(self):
        valor = self.cleaned_data.get('valor_proposta')
        if not valor or float(valor) <= 0:
            raise ValidationError('O valor da proposta deve ser maior que zero.')
        return valor


class PropostaFiltroForm(forms.Form):
    """Formulário para filtros na listagem de propostas"""
    
    STATUS_CHOICES = [('', 'Todos')] + Proposta.STATUS_CHOICES
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
        empty_label='Todos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(nivel='vendedor', is_active=True).order_by('first_name'),
        required=False,
        empty_label='Todos',
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
    
    validade = forms.ChoiceField(
        choices=[
            ('', 'Todas'),
            ('vencidas', 'Vencidas'),
            ('vence_hoje', 'Vencem hoje'),
            ('vence_semana', 'Vencem esta semana'),
            ('vigentes', 'Vigentes'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    # Filtro por faixa de valor
    valor_min = forms.DecimalField(
        required=False,
        widget=MoneyInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Valor mínimo'
        })
    )
    
    valor_max = forms.DecimalField(
        required=False,
        widget=MoneyInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Valor máximo'
        })
    )
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por número, projeto ou cliente...'
        })
    )