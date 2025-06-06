# core/forms.py - CORREÇÃO DOS RELACIONAMENTOS

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from datetime import datetime
import re

from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    EspecificacaoElevador, OpcaoEspecificacao, RegraComponente,
    ComponenteDerivado, SimulacaoElevador, FornecedorProduto, Cliente,
    ParametrosGerais
)
from core.utils.validators import validar_cpf, validar_cnpj, validar_cpf_cnpj_unico

class UsuarioForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'nivel', 'telefone', 
                  'codigo_loja', 'codigo_vendedor', 'is_active']
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'codigo_loja': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'codigo_vendedor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(UsuarioForm, self).__init__(*args, **kwargs)
        
        # Se estiver editando um usuário existente, não exigir senha
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
        
        # Adicionar atributos de classe para os widgets que não foram especificados
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs') or 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "As senhas não coincidem.")
        
        # Validação para códigos de loja e vendedor
        codigo_loja = cleaned_data.get('codigo_loja')
        if codigo_loja and (len(codigo_loja) != 3 or not codigo_loja.isdigit()):
            self.add_error('codigo_loja', "O código da loja deve ter exatamente 3 dígitos numéricos.")
        
        codigo_vendedor = cleaned_data.get('codigo_vendedor')
        if codigo_vendedor and (len(codigo_vendedor) != 3 or not codigo_vendedor.isdigit()):
            self.add_error('codigo_vendedor', "O código do vendedor deve ter exatamente 3 dígitos numéricos.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Se uma senha foi fornecida, codificá-la
        password = self.cleaned_data.get('password')
        if password:
            user.password = make_password(password)
        
        if commit:
            user.save()
        
        return user


# =============================================================================
# ⭐ FORMULÁRIOS CORRIGIDOS PARA GRUPOS E SUBGRUPOS
# =============================================================================

# Atualizações no core/forms.py

class GrupoProdutoForm(forms.ModelForm):
    class Meta:
        model = GrupoProduto
        fields = ['codigo', 'nome', 'tipo_produto', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 01, 02, 03...'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do grupo'
            }),
            'tipo_produto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class SubgrupoProdutoForm(forms.ModelForm):
    class Meta:
        model = SubgrupoProduto
        fields = ['grupo', 'codigo', 'nome', 'ultimo_numero', 'ativo']
        widgets = {
            'grupo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 01, 02, 03...'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do subgrupo'
            }),
            'ultimo_numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': '0'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas grupos ativos
        self.fields['grupo'].queryset = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        
        # Se for edição, mostrar informações adicionais
        if self.instance.pk:
            produtos_count = self.instance.produtos.count()
            
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
            
            if produtos_count > 0:
                self.fields['nome'].help_text = f"Produtos vinculados: {produtos_count}"
                
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
            queryset = SubgrupoProduto.objects.filter(grupo=grupo, codigo=codigo)
            
            # Se for edição, excluir o próprio registro da verificação
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    f'Já existe um subgrupo com o código "{codigo}" no grupo "{grupo.nome}".'
                )
        
        return codigo
# =============================================================================
# ⭐ FORMULÁRIO DE PRODUTO CORRIGIDO
# =============================================================================

class ProdutoForm(forms.ModelForm):
    """
    Formulário atualizado que usa a nova lógica de grupos/subgrupos
    e geração automática de códigos
    """
    
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
                'class': 'form-control',
                'placeholder': 'Nome do produto'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Descrição do produto...'
            }),
            'grupo': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'updateSubgrupos(this.value)'
            }),
            'subgrupo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unidade_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'peso_unitario': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'controla_estoque': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'custo_medio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'fornecedor_principal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'prazo_entrega_padrao': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dias'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'disponivel': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['grupo'].required = True
        self.fields['subgrupo'].required = True
        self.fields['nome'].required = True
        
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

    def save(self, commit=True):
        """Override para garantir que o tipo seja definido corretamente"""
        produto = super().save(commit=False)
        
        # Garantir que o tipo coincida com o grupo
        if produto.grupo and produto.grupo.tipo_produto:
            produto.tipo = produto.grupo.tipo_produto
        
        if commit:
            produto.save()
        
        return produto


# =============================================================================
# ⭐ FORMULÁRIOS PARA FILTROS E BUSCAS
# =============================================================================

class GrupoProdutoFiltroForm(forms.Form):
    """Formulário para filtros na listagem de grupos"""
    
    TIPO_CHOICES = [('', 'Todos os Tipos')] + GrupoProduto.TIPO_PRODUTO_CHOICES
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    tipo_produto = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por código ou nome...'
        })
    )


class SubgrupoProdutoFiltroForm(forms.Form):
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
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por código ou nome...'
        })
    )


# =============================================================================
# DEMAIS FORMULÁRIOS (mantidos iguais)
# =============================================================================

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 'contato_principal',
            'telefone', 'email', 'endereco', 'ativo'
        ]
        widgets = {
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '00.000.000/0000-00'}),
            'contato_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EspecificacaoElevadorForm(forms.ModelForm):
    class Meta:
        model = EspecificacaoElevador
        fields = ['codigo', 'nome', 'tipo', 'descricao', 'obrigatoria', 'ordem', 'ativa']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'obrigatoria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class OpcaoEspecificacaoForm(forms.ModelForm):
    class Meta:
        model = OpcaoEspecificacao
        fields = ['especificacao', 'codigo', 'nome', 'descricao', 'valor_numerico', 'unidade', 'ordem', 'ativa']
        widgets = {
            'especificacao': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor_numerico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RegraComponenteForm(forms.ModelForm):
    class Meta:
        model = RegraComponente
        fields = ['nome', 'descricao', 'condicoes', 'componente', 'formula_quantidade', 'prioridade', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'condicoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON: {"material": "Inox 430", "espessura": "1.2"}'}),
            'componente': forms.Select(attrs={'class': 'form-select'}),
            'formula_quantidade': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ex: altura * 2 + largura'}),
            'prioridade': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ComponenteDerivadoForm(forms.ModelForm):
    class Meta:
        model = ComponenteDerivado
        fields = ['componente_origem', 'componente_destino', 'tipo_calculo', 'multiplicador', 'formula', 'ativa']
        widgets = {
            'componente_origem': forms.Select(attrs={'class': 'form-select'}),
            'componente_destino': forms.Select(attrs={'class': 'form-select'}),
            'tipo_calculo': forms.Select(attrs={'class': 'form-select'}),
            'multiplicador': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'formula': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SimulacaoElevadorForm(forms.ModelForm):
    class Meta:
        model = SimulacaoElevador
        fields = ['numero', 'nome', 'cliente_nome', 'cliente_contato', 'observacoes']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_contato': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

# Formulário para múltiplos fornecedores por produto
class FornecedorProdutoForm(forms.ModelForm):
    class Meta:
        model = FornecedorProduto
        fields = [
            'fornecedor', 'codigo_fornecedor', 'preco_unitario', 'prioridade',
            'prazo_entrega', 'quantidade_minima', 'observacoes', 'ativo'
        ]
        widgets = {
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'codigo_fornecedor': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'prazo_entrega': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantidade_minima': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Formset para gerenciar múltiplos fornecedores
FornecedorProdutoFormSet = forms.inlineformset_factory(
    Produto,
    FornecedorProduto,
    form=FornecedorProdutoForm,
    extra=1,
    can_delete=True,
    fields=['fornecedor', 'codigo_fornecedor', 'preco_unitario', 'prioridade', 'prazo_entrega', 'ativo']
)

# =============================================================================
# ⭐ FORMULÁRIOS DE CLIENTE (mantidos iguais)
# =============================================================================

class ClienteForm(forms.ModelForm):
    """Formulário completo para cliente no Portal Gestor"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome', 'nome_fantasia', 'cpf_cnpj',
            'telefone', 'email', 'contato_principal',
            'cep', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'estado', 'observacoes'
        ]
        widgets = {
            'tipo_pessoa': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleCpfCnpjMask(this.value)'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo ou Razão Social'
            }),
            'nome_fantasia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome Fantasia (para PJ)'
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CPF ou CNPJ',
                'data-mask': 'cpf'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
                'data-mask': 'phone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'contato_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00000-000',
                'data-mask': 'cep'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, Avenida, etc.'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apto, Sala, etc.'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UF',
                'maxlength': '2'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais...'
            }),
        }
    
    def clean_cpf_cnpj(self):
        """Validação específica do CPF/CNPJ"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        tipo_pessoa = self.cleaned_data.get('tipo_pessoa')
        
        if not cpf_cnpj:
            return cpf_cnpj
        
        # Remove caracteres não numéricos
        cpf_cnpj_numerico = re.sub(r'\D', '', cpf_cnpj)
        
        # Validar formato baseado no tipo de pessoa
        if tipo_pessoa == 'PF':
            try:
                return validar_cpf(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        elif tipo_pessoa == 'PJ':
            try:
                return validar_cnpj(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        
        return cpf_cnpj
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        cpf_cnpj = cleaned_data.get('cpf_cnpj')
        
        # Validar unicidade se CPF/CNPJ foi fornecido
        if cpf_cnpj:
            try:
                validar_cpf_cnpj_unico(cpf_cnpj, instance=self.instance, model_class=Cliente)
            except ValidationError as e:
                self.add_error('cpf_cnpj', e.message)
        
        return cleaned_data

class ClienteCreateForm(forms.ModelForm):
    """Formulário simplificado para criação rápida de cliente no Portal Vendedor"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome', 'nome_fantasia', 'cpf_cnpj',
            'telefone', 'email', 'contato_principal',
            'endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep'
        ]
        widgets = {
            'tipo_pessoa': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'onchange': 'toggleCpfCnpjMask(this.value)'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Nome completo ou Razão Social',
                'required': True
            }),
            'nome_fantasia': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Nome Fantasia (opcional)'
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'CPF ou CNPJ',
                'data-mask': 'cpf'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '(11) 99999-9999',
                'data-mask': 'phone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'email@exemplo.com'
            }),
            'contato_principal': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Nome do responsável'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Rua, Avenida, etc.'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Número'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Cidade'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'UF',
                'maxlength': '2'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '00000-000',
                'data-mask': 'cep'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].required = True
        self.fields['tipo_pessoa'].required = True
    
    def clean_cpf_cnpj(self):
        """Validação específica do CPF/CNPJ"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        tipo_pessoa = self.cleaned_data.get('tipo_pessoa')
        
        if not cpf_cnpj:
            return cpf_cnpj
        
        # Remove caracteres não numéricos
        cpf_cnpj_numerico = re.sub(r'\D', '', cpf_cnpj)
        
        # Validar formato baseado no tipo de pessoa
        if tipo_pessoa == 'PF':
            try:
                return validar_cpf(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        elif tipo_pessoa == 'PJ':
            try:
                return validar_cnpj(cpf_cnpj_numerico)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        
        return cpf_cnpj
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        cpf_cnpj = cleaned_data.get('cpf_cnpj')
        
        # Validar unicidade se CPF/CNPJ foi fornecido
        if cpf_cnpj:
            try:
                validar_cpf_cnpj_unico(cpf_cnpj, instance=self.instance, model_class=Cliente)
            except ValidationError as e:
                self.add_error('cpf_cnpj', e.message)
        
        return cleaned_data

class ClienteFiltroForm(forms.Form):
    """Formulário para filtros na listagem de clientes"""
    
    TIPO_CHOICES = [('', 'Todos')] + Cliente.TIPO_PESSOA_CHOICES
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por nome, CPF/CNPJ ou email...'
        })
    )

class ParametrosGeraisForm(forms.ModelForm):
    class Meta:
        model = ParametrosGerais
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual',
            'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
            'telefone', 'email',
            'margem_padrao', 'faturamento_elevadores', 'faturamento_fuza', 'faturamento_manutencao',
            'comissao_padrao', 'desconto_alcada_1', 'desconto_alcada_2'
        ]
        widgets = {
            field: forms.TextInput(attrs={'class': 'form-control'}) for field in fields
        }
        widgets.update({
            'estado': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('', 'Selecione...'),
                ('SP', 'São Paulo'),
                ('RJ', 'Rio de Janeiro'),
                ('MG', 'Minas Gerais'),
                # ... adicione os demais estados se quiser
            ]),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'margem_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'faturamento_elevadores': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'faturamento_fuza': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'faturamento_manutencao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comissao_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'desconto_alcada_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'desconto_alcada_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['razao_social'].required = True  # Apenas este obrigatório

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if cep:
            cep_numerico = re.sub(r'\D', '', cep)
            if len(cep_numerico) != 8:
                raise forms.ValidationError('CEP deve ter 8 dígitos.')
            return f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        return cep

    def clean(self):
        cleaned = super().clean()
        a1 = cleaned.get('desconto_alcada_1')
        a2 = cleaned.get('desconto_alcada_2')
        if a1 and a2 and a2 <= a1:
            self.add_error('desconto_alcada_2', 'Alçada 2 deve ser maior que Alçada 1.')
        return cleaned