# core/forms/parametros.py

"""
Formulários relacionados a parâmetros gerais - ATUALIZADOS
"""

from django import forms
from django.core.exceptions import ValidationError
import re

from core.models import ParametrosGerais
# Import ESTADOS_BRASIL from core.choices
from .base import BaseModelForm, AuditMixin, ValidacaoComumMixin, MoneyInput, PercentageInput
from ..choices import ESTADOS_BRASIL


class ParametrosGeraisForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """Formulário para parâmetros gerais do sistema - ATUALIZADO"""
    
    class Meta:
        model = ParametrosGerais
        fields = [
            # Dados da empresa
            'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual',
            'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
            'telefone', 'email',
            # Compras
            'comprador_responsavel', 'contato_compras',
            # Custos indiretos (NOVOS)
            'percentual_mao_obra', 'percentual_indiretos_fabricacao', 'percentual_instalacao',
            # Formação de preço
            'margem_padrao', 'comissao_padrao',
            # Descontos
            'desconto_alcada_1', 'desconto_alcada_2',
            # Faturamento
            'faturamento_elevadores', 'faturamento_fuza', 'faturamento_manutencao',
        ]
        widgets = {
            'razao_social': forms.TextInput(attrs={
                'placeholder': 'Razão social da empresa'
            }),
            'nome_fantasia': forms.TextInput(attrs={
                'placeholder': 'Nome fantasia (opcional)'
            }),
            'cnpj': forms.TextInput(attrs={
                'data-mask': '00.000.000/0000-00',
                'placeholder': '00.000.000/0000-00'
            }),
            'inscricao_estadual': forms.TextInput(attrs={
                'placeholder': 'Inscrição estadual'
            }),
            'endereco': forms.TextInput(attrs={
                'placeholder': 'Logradouro'
            }),
            'numero': forms.TextInput(attrs={
                'placeholder': 'Número'
            }),
            'complemento': forms.TextInput(attrs={
                'placeholder': 'Complemento'
            }),
            'bairro': forms.TextInput(attrs={
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'placeholder': 'Cidade'
            }),
            'estado': forms.Select(choices=ESTADOS_BRASIL), # Use ESTADOS_BRASIL from core.choices
            'cep': forms.TextInput(attrs={
                'data-mask': '00000-000',
                'placeholder': '00000-000'
            }),
            'telefone': forms.TextInput(attrs={
                'data-mask': '(00) 00000-0000',
                'placeholder': '(00) 00000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'contato@empresa.com'
            }),
            
            # NOVOS CAMPOS DE COMPRAS
            'comprador_responsavel': forms.TextInput(attrs={
                'placeholder': 'Nome do responsável pelas compras'
            }),
            'contato_compras': forms.TextInput(attrs={
                'placeholder': 'Email ou telefone do setor de compras'
            }),
            
            # CUSTOS INDIRETOS (NOVOS)
            'percentual_mao_obra': PercentageInput(),
            'percentual_indiretos_fabricacao': PercentageInput(),
            'percentual_instalacao': PercentageInput(),

            # FORMAÇÃO DE PREÇO
            'margem_padrao': PercentageInput(),
            'comissao_padrao': PercentageInput(),

            # DESCONTOS
            'desconto_alcada_1': PercentageInput(),
            'desconto_alcada_2': PercentageInput(),

            # FATURAMENTO
            'faturamento_elevadores': PercentageInput(),
            'faturamento_fuza': PercentageInput(),
            'faturamento_manutencao': PercentageInput(),
        }
        labels = {
            'razao_social': 'Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'cnpj': 'CNPJ',
            'inscricao_estadual': 'Inscrição Estadual',
            'endereco': 'Logradouro',
            'numero': 'Número',
            'complemento': 'Complemento',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'Estado',
            'cep': 'CEP',
            'telefone': 'Telefone',
            'email': 'Email',
            
            # NOVOS CAMPOS
            'comprador_responsavel': 'Comprador Responsável',
            'contato_compras': 'Contato de Compras',
            
            # CUSTOS INDIRETOS
            'percentual_mao_obra': 'Mão de Obra (%)',
            'percentual_indiretos_fabricacao': 'Indiretos Fabricação (%)',
            'percentual_instalacao': 'Instalação (%)',

            # FORMAÇÃO DE PREÇO
            'margem_padrao': 'Margem de Lucro (%)',
            'comissao_padrao': 'Comissão (%)',

            # DESCONTOS
            'desconto_alcada_1': 'Desconto Alçada 1 (%)',
            'desconto_alcada_2': 'Desconto Alçada 2 (%)',

            # FATURAMENTO
            'faturamento_elevadores': 'Faturamento Elevadores (%)',
            'faturamento_fuza': 'Faturamento FUZA (%)',
            'faturamento_manutencao': 'Faturamento Manutenção (%)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apenas razão social é obrigatória
        self.fields['razao_social'].required = True
        
        # Help texts informativos
        self.fields['comprador_responsavel'].help_text = 'Nome que aparecerá nos pedidos de compra'
        self.fields['contato_compras'].help_text = 'Email ou telefone que aparecerá nos pedidos'
        self.fields['desconto_alcada_1'].help_text = 'Desconto máximo para nível 1'
        self.fields['desconto_alcada_2'].help_text = 'Desconto máximo para nível 2 (deve ser maior que alçada 1)'

    def clean_cnpj(self):
        """Validar CNPJ"""
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remove caracteres não numéricos
            cnpj_numerico = re.sub(r'\D', '', cnpj)
            
            if len(cnpj_numerico) != 14:
                raise ValidationError('CNPJ deve ter 14 dígitos.')
            
            # Formatação básica (validação completa pode ser implementada depois)
            return f"{cnpj_numerico[:2]}.{cnpj_numerico[2:5]}.{cnpj_numerico[5:8]}/{cnpj_numerico[8:12]}-{cnpj_numerico[12:]}"
        
        return cnpj

    def clean_desconto_alcada_1(self):
        """Validar desconto alçada 1"""
        desconto = self.cleaned_data.get('desconto_alcada_1')
        if desconto is not None and (desconto < 0 or desconto > 100):
            raise ValidationError('Desconto deve estar entre 0 e 100%.')
        return desconto

    def clean_desconto_alcada_2(self):
        """Validar desconto alçada 2"""
        desconto = self.cleaned_data.get('desconto_alcada_2')
        if desconto is not None and (desconto < 0 or desconto > 100):
            raise ValidationError('Desconto deve estar entre 0 e 100%.')
        return desconto

    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        
        # Validar alçadas de desconto
        alcada_1 = cleaned_data.get('desconto_alcada_1')
        alcada_2 = cleaned_data.get('desconto_alcada_2')
        
        if alcada_1 and alcada_2 and alcada_2 <= alcada_1:
            self.add_error('desconto_alcada_2', 'Alçada 2 deve ser maior que Alçada 1.')
        
        # Validar porcentagens de faturamento
        porcentagens_faturamento = [
            cleaned_data.get('faturamento_elevadores'),
            cleaned_data.get('faturamento_fuza'),
            cleaned_data.get('faturamento_manutencao')
        ]
        
        return cleaned_data


class ConfiguracaoEmailForm(forms.Form):
    """Formulário para configurações de email"""
    
    servidor_smtp = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'smtp.gmail.com'
        }),
        label='Servidor SMTP'
    )
    
    porta = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'placeholder': '587'
        }),
        label='Porta',
        initial=587
    )
    
    usuario = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'usuario@empresa.com'
        }),
        label='Usuário (Email)'
    )
    
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Senha do email'
        }),
        label='Senha'
    )
    
    usar_tls = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        initial=True,
        label='Usar TLS/SSL'
    )
    
    email_teste = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'teste@exemplo.com'
        }),
        required=False,
        label='Email para Teste'
    )


class ConfiguracaoSistemaForm(forms.Form):
    """Formulário para configurações gerais do sistema"""
    
    nome_sistema = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'FUZA Elevadores'
        }),
        label='Nome do Sistema',
        max_length=100
    )
    
    versao_sistema = forms.CharField(
        widget=forms.TextInput(attrs={
            'readonly': True
        }),
        label='Versão do Sistema',
        initial='1.0.0'
    )
    
    manutencao_ativa = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label='Modo Manutenção Ativo'
    )
    
    mensagem_manutencao = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Sistema temporariamente indisponível para manutenção...'
        }),
        required=False,
        label='Mensagem de Manutenção'
    )
    
    debug_ativo = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label='Modo Debug Ativo',
        help_text='⚠️ Apenas para desenvolvimento'
    )
    
    backup_automatico = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        initial=True,
        label='Backup Automático'
    )
    
    frequencia_backup = forms.ChoiceField(
        choices=[
            ('diario', 'Diário'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal'),
        ],
        widget=forms.Select(),
        initial='semanal',
        label='Frequência do Backup'
    )


class PermissoesForm(forms.Form):
    """Formulário para configuração de permissões"""
    
    MODULOS_CHOICES = [
        ('vendas', 'Módulo de Vendas'),
        ('compras', 'Módulo de Compras'),
        ('producao', 'Módulo de Produção'),
        ('engenharia', 'Módulo de Engenharia'),
        ('financeiro', 'Módulo Financeiro'),
        ('relatorios', 'Relatórios'),
        ('configuracoes', 'Configurações'),
    ]
    
    NIVEIS_CHOICES = [
        ('visualizar', 'Visualizar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('aprovar', 'Aprovar'),
    ]
    
    modulos_ativos = forms.MultipleChoiceField(
        choices=MODULOS_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        label='Módulos Ativos'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Criar campos dinâmicos para cada nível de usuário
        from core.models import Usuario # Keep this local import if only used here
        for nivel_code, nivel_name in Usuario.NIVEL_CHOICES:
            field_name = f'permissoes_{nivel_code}'
            self.fields[field_name] = forms.MultipleChoiceField(
                choices=self.NIVEIS_CHOICES,
                widget=forms.CheckboxSelectMultiple(),
                required=False,
                label=f'Permissões - {nivel_name}'
            )