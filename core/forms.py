# core/forms.py
from django import forms
from core.models import (
    Usuario, Produto, GrupoProduto, SubgrupoProduto, Fornecedor,
    EspecificacaoElevador, OpcaoEspecificacao, RegraComponente,
    ComponenteDerivado, SimulacaoElevador
)
from django.contrib.auth.hashers import make_password
from datetime import datetime

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


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'codigo', 'nome', 'descricao', 'tipo', 'grupo', 'subgrupo',
            'especificacoes_tecnicas', 'unidade_medida', 'peso_unitario', 'dimensoes',
            'controla_estoque', 'estoque_minimo', 'custo_medio', 'preco_venda', 'margem_padrao',
            'fornecedor_principal', 'prazo_entrega_padrao', 'status', 'disponivel'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'subgrupo': forms.Select(attrs={'class': 'form-select'}),
            'especificacoes_tecnicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON: {"material": "Inox 430", "espessura": "1.2"}'}),
            'unidade_medida': forms.Select(attrs={'class': 'form-select'}),
            'peso_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'dimensoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'JSON: {"altura": 2.0, "largura": 1.0}'}),
            'controla_estoque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estoque_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custo_medio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_venda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'margem_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fornecedor_principal': forms.Select(attrs={'class': 'form-select'}),
            'prazo_entrega_padrao': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'disponivel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].required = True
        
        # Filtrar subgrupos baseado no grupo selecionado
        if 'grupo' in self.data:
            try:
                grupo_id = int(self.data.get('grupo'))
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.filter(grupo_id=grupo_id, ativo=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.grupo:
            self.fields['subgrupo'].queryset = self.instance.grupo.subgrupos.filter(ativo=True)
        else:
            self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()


class GrupoProdutoForm(forms.ModelForm):
    class Meta:
        model = GrupoProduto
        fields = ['codigo', 'nome', 'descricao', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubgrupoProdutoForm(forms.ModelForm):
    class Meta:
        model = SubgrupoProduto
        fields = ['grupo', 'codigo', 'nome', 'descricao', 'ativo']
        widgets = {
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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