# core/forms/produtos.py - ATUALIZAÇÃO 1: FORMULÁRIOS - VERSÃO CORRIGIDA COMPLETA

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
    """
    Formulário para produtos - ✅ VERSÃO CORRIGIDA COMPLETA
    CORREÇÃO: Verificações seguras de relacionamentos
    """
    
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'grupo', 'subgrupo', 'descricao',
            'tipo_pi',
            'unidade_medida', 'peso_unitario',
            'codigo_ncm', 'codigo_produto_fornecedor',
            'controla_estoque', 'estoque_atual', 'estoque_minimo',
            # ===== NOVA ESTRUTURA DE CUSTOS =====
            'custo_material',        # ✅ Campo principal
            'custo_servico',         # ✅ Campo principal
            # ===== CAMPOS LEGACY (mantidos para compatibilidade) =====
            'custo_medio',           # 🔄 Sincronizado automaticamente
            'custo_industrializacao', # 🔄 Sincronizado automaticamente
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
                'class': 'form-select'
            }),
            'subgrupo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_pi': forms.Select(attrs={
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
            # ===== CAMPOS DE CUSTO CORRIGIDOS =====
            'custo_material': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
                'class': 'form-control'
            }),
            'custo_servico': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
                'class': 'form-control'
            }),
            # ===== CAMPOS LEGACY =====
            'custo_medio': forms.HiddenInput(),           # Oculto - sincronizado via JS
            'custo_industrializacao': forms.HiddenInput(), # Oculto - sincronizado via JS
            
            'estoque_atual': QuantityInput(),
            'estoque_minimo': QuantityInput(),
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
            # ===== NOVOS LABELS =====
            'custo_material': 'Custo Material',
            'custo_servico': 'Custo Serviço',
            'controla_estoque': 'Controla Estoque',
            'estoque_atual': 'Estoque Atual',
            'estoque_minimo': 'Estoque Mínimo',
            'fornecedor_principal': 'Fornecedor Principal',
            'prazo_entrega_padrao': 'Prazo Entrega Padrão (dias)',
            'status': 'Status',
            'disponivel': 'Disponível para Uso',
            'utilizado': 'Material Utilizado',
        }

    # ===================================================================
    # ✅ MÉTODOS AUXILIARES PARA VERIFICAÇÃO SEGURA DE RELACIONAMENTOS
    # ===================================================================
    
    def _tem_grupo_seguro(self):
        """
        Verifica se a instância tem grupo de forma segura
        Evita o erro RelatedObjectDoesNotExist
        """
        if not self.instance or not self.instance.pk:
            return False
        
        try:
            return bool(self.instance.grupo)
        except:
            return False

    def _get_grupo_seguro(self):
        """
        Retorna o grupo da instância de forma segura
        Retorna None se não existir ou houver erro
        """
        if not self._tem_grupo_seguro():
            return None
        
        try:
            return self.instance.grupo
        except:
            return None

    def _tem_subgrupo_seguro(self):
        """
        Verifica se a instância tem subgrupo de forma segura
        """
        if not self.instance or not self.instance.pk:
            return False
        
        try:
            return bool(self.instance.subgrupo)
        except:
            return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar choices dos campos
        self.fields['unidade_medida'].choices = UNIDADE_MEDIDA_CHOICES
        self.fields['status'].choices = STATUS_PRODUTO_CHOICES
        self.fields['tipo_pi'].choices = [('', 'Selecione o tipo')] + Produto.TIPO_PI_CHOICES
        self.fields['tipo_pi'].required = False  # Será validado no clean()

        # Campos obrigatórios básicos
        self.fields['grupo'].required = True
        self.fields['subgrupo'].required = True
        self.fields['nome'].required = True
        self.fields['unidade_medida'].required = True
        
        # ===== CAMPOS DE CUSTO - INICIALIZAR COMO NÃO OBRIGATÓRIOS =====
        self.fields['custo_material'].required = False
        self.fields['custo_servico'].required = False
        
        # Filtrar apenas grupos ativos
        self.fields['grupo'].queryset = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        
        # ===== CONFIGURAÇÃO ESPECÍFICA POR TIPO DE PRODUTO - ✅ CORRIGIDA =====
        produto_tipo = None
        
        # ✅ VERIFICAÇÃO SEGURA PARA INSTÂNCIA EXISTENTE
        if self._tem_grupo_seguro():
            grupo = self._get_grupo_seguro()
            if grupo:
                produto_tipo = grupo.tipo_produto
        
        # Se não conseguiu pelo instance, tentar pelos dados do formulário
        if not produto_tipo and 'grupo' in self.data:
            try:
                grupo_id = int(self.data.get('grupo'))
                grupo = GrupoProduto.objects.get(id=grupo_id)
                produto_tipo = grupo.tipo_produto
            except (ValueError, TypeError, GrupoProduto.DoesNotExist):
                pass
        
        # ===== CONFIGURAÇÃO PARA MATÉRIAS-PRIMAS (MP) =====
        if produto_tipo == 'MP':
            # Para MP: mostrar apenas custo_material
            self.fields['custo_material'].help_text = "Custo unitário da matéria prima"
            
            # Ocultar custo_servico para MP
            self.fields['custo_servico'].widget = forms.HiddenInput()
            self.fields['custo_servico'].required = False
            
            # Ocultar tipo_pi para MP
            self.fields['tipo_pi'].widget = forms.HiddenInput()
            
        # ===== CONFIGURAÇÃO PARA PRODUTOS INTERMEDIÁRIOS (PI) =====
        elif produto_tipo == 'PI':
            self.fields['tipo_pi'].required = True
            
            # Configurar campos de custo baseado no tipo_pi
            tipo_pi = None
            if self.instance and self.instance.pk:
                tipo_pi = getattr(self.instance, 'tipo_pi', None)
            elif 'tipo_pi' in self.data:
                tipo_pi = self.data.get('tipo_pi')
            
            if tipo_pi == 'COMPRADO':
                self.fields['custo_material'].help_text = "Custo total do produto comprado"
                self.fields['custo_servico'].widget = forms.HiddenInput()
            elif tipo_pi in ['MONTADO_INTERNO', 'MONTADO_EXTERNO']:
                self.fields['custo_material'].help_text = "Custo de materiais/componentes"
                self.fields['custo_servico'].help_text = "Custo de mão de obra/serviços"
            elif tipo_pi == 'SERVICO_INTERNO':
                self.fields['custo_material'].widget = forms.HiddenInput()
                self.fields['custo_servico'].help_text = "Custo da mão de obra interna"
            elif tipo_pi == 'SERVICO_EXTERNO':
                self.fields['custo_material'].widget = forms.HiddenInput()
                self.fields['custo_servico'].help_text = "Custo do serviço terceirizado"
        
        # ===== CONFIGURAÇÃO PARA PRODUTOS ACABADOS (PA) =====
        elif produto_tipo == 'PA':
            self.fields['custo_material'].help_text = "Custo de materiais/componentes"
            self.fields['custo_servico'].help_text = "Custo de mão de obra/serviços"
            # Ocultar tipo_pi para PA
            self.fields['tipo_pi'].widget = forms.HiddenInput()
        
        # ===== MIGRAÇÃO AUTOMÁTICA DE DADOS LEGACY - ✅ CORRIGIDA =====
        if self.instance and self.instance.pk:
            # Se tem dados legacy mas não tem nos novos campos, migrar
            if getattr(self.instance, 'custo_medio', None) and not getattr(self.instance, 'custo_material', None):
                self.fields['custo_material'].initial = self.instance.custo_medio
            
            if getattr(self.instance, 'custo_industrializacao', None) and not getattr(self.instance, 'custo_servico', None):
                self.fields['custo_servico'].initial = self.instance.custo_industrializacao
        
        # ===== CONFIGURAÇÃO DINÂMICA DE SUBGRUPOS - ✅ CORRIGIDA =====
        if 'grupo' in self.data:
            try:
                grupo_id = int(self.data.get('grupo'))
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.filter(
                    grupo_id=grupo_id, 
                    ativo=True
                ).order_by('codigo')
            except (ValueError, TypeError):
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        elif self._tem_grupo_seguro():
            # ✅ USAR MÉTODO SEGURO
            grupo = self._get_grupo_seguro()
            if grupo:
                self.fields['subgrupo'].queryset = grupo.subgrupos.filter(ativo=True).order_by('codigo')
            else:
                self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        else:
            self.fields['subgrupo'].queryset = SubgrupoProduto.objects.none()
        
        # Help text apenas para modo edição - ✅ CORRIGIDO
        if self.instance.pk and getattr(self.instance, 'codigo', None):
            self.fields['nome'].help_text = f"Código atual: {self.instance.codigo}"

    def clean_custo_material(self):
        """Validar custo material - CORRIGIDO"""
        custo = self.cleaned_data.get('custo_material')
        
        # Permitir valores None, vazios ou zero
        if custo is None or custo == '' or custo == 0:
            return None
        
        # Validar se é positivo (se preenchido)
        if custo is not None and custo < 0:
            raise ValidationError('Custo material deve ser maior ou igual a zero.')
        
        return custo

    def clean_custo_servico(self):
        """Validar custo serviço - CORRIGIDO"""
        custo = self.cleaned_data.get('custo_servico')
        
        # Permitir valores None, vazios ou zero
        if custo is None or custo == '' or custo == 0:
            return None
        
        # Validar se é positivo (se preenchido)
        if custo is not None and custo < 0:
            raise ValidationError('Custo serviço deve ser maior ou igual a zero.')
        
        return custo

    def clean_estoque_minimo(self):
        """Validar estoque mínimo"""
        estoque_minimo = self.cleaned_data.get('estoque_minimo')
        if estoque_minimo is not None:
            validar_positivo(estoque_minimo)
        return estoque_minimo

    def clean(self):
        """Validações personalizadas - ✅ CORRIGIDAS"""
        cleaned_data = super().clean()
        grupo = cleaned_data.get('grupo')
        subgrupo = cleaned_data.get('subgrupo')
        tipo_pi = cleaned_data.get('tipo_pi')
        fornecedor_principal = cleaned_data.get('fornecedor_principal')
        custo_material = cleaned_data.get('custo_material')
        custo_servico = cleaned_data.get('custo_servico')
        
        # Validar relacionamento grupo/subgrupo
        if grupo and subgrupo:
            if subgrupo.grupo != grupo:
                self.add_error('subgrupo', 'O subgrupo selecionado não pertence ao grupo escolhido.')
        
        # ===== VALIDAÇÕES ESPECÍFICAS POR TIPO - CORRIGIDAS =====
        if grupo:
            produto_tipo = grupo.tipo_produto
            
            # Validações para MP
            if produto_tipo == 'MP':
                if not custo_material or custo_material <= 0:
                    self.add_error('custo_material', 'Custo da matéria prima é obrigatório e deve ser maior que zero.')
                # Para MP, limpar custo_servico
                cleaned_data['custo_servico'] = None
            
            # Validações para PI
            elif produto_tipo == 'PI':
                if not tipo_pi:
                    self.add_error('tipo_pi', 'Tipo do Produto Intermediário é obrigatório para produtos PI.')
                else:
                    # Validações específicas por tipo_pi
                    if tipo_pi == 'COMPRADO':
                        if not fornecedor_principal:
                            self.add_error('fornecedor_principal', 'Fornecedor principal é obrigatório para produtos comprados.')
                        if not custo_material or custo_material <= 0:
                            self.add_error('custo_material', 'Custo material é obrigatório para produtos comprados.')
                        # Para comprados, limpar custo_servico
                        cleaned_data['custo_servico'] = None
                    
                    elif tipo_pi in ['MONTADO_INTERNO', 'MONTADO_EXTERNO']:
                        if tipo_pi == 'MONTADO_EXTERNO' and not fornecedor_principal:
                            self.add_error('fornecedor_principal', 'Fornecedor principal é obrigatório para produtos montados externamente.')
                        # Para montados: permitir custos zerados (serão calculados pela estrutura)
                        # Não é obrigatório ter custos para produtos montados
                    
                    elif tipo_pi == 'SERVICO_INTERNO':
                        if not custo_servico or custo_servico <= 0:
                            self.add_error('custo_servico', 'Custo de serviço é obrigatório para serviços internos.')
                        # Para serviços, limpar custo_material
                        cleaned_data['custo_material'] = None
                    
                    elif tipo_pi == 'SERVICO_EXTERNO':
                        if not fornecedor_principal:
                            self.add_error('fornecedor_principal', 'Prestador principal é obrigatório para serviços externos.')
                        if not custo_servico or custo_servico <= 0:
                            self.add_error('custo_servico', 'Custo de serviço é obrigatório para serviços externos.')
                        # Para serviços, limpar custo_material
                        cleaned_data['custo_material'] = None
            
            # Validações para PA
            elif produto_tipo == 'PA':
                # PA não exige custo - será calculado na Ordem de Produção
                pass
        
        return cleaned_data

    def save(self, commit=True):
        """
        Override para sincronizar campos legacy e definir tipo corretamente - ✅ CORRIGIDO
        """
        produto = super().save(commit=False)
        
        # Debug: Imprimir valores recebidos
        print(f"🐛 DEBUG SAVE - Valores recebidos:")
        print(f"  custo_material: {produto.custo_material}")
        print(f"  custo_servico: {produto.custo_servico}")
        print(f"  custo_medio (legacy): {produto.custo_medio}")
        print(f"  custo_industrializacao (legacy): {produto.custo_industrializacao}")
        
        # Definir tipo baseado no grupo
        if produto.grupo and produto.grupo.tipo_produto:
            produto.tipo = produto.grupo.tipo_produto
        
        # Limpar tipo_pi se não for PI
        if produto.tipo != 'PI':
            produto.tipo_pi = None
        
        # ===== SINCRONIZAÇÃO COM CAMPOS LEGACY - CORRIGIDA =====
        # IMPORTANTE: NÃO sobrescrever os valores novos com os legacy!
        
        # Manter os valores dos novos campos como estão (não mexer neles)
        custo_material_final = produto.custo_material
        custo_servico_final = produto.custo_servico
        
        # Apenas sincronizar os campos legacy para manter compatibilidade
        if custo_material_final is not None:
            produto.custo_medio = custo_material_final
        else:
            produto.custo_medio = None
            
        if custo_servico_final is not None:
            produto.custo_industrializacao = custo_servico_final
        else:
            produto.custo_industrializacao = None
        
        # ===== REGRAS ESPECÍFICAS POR TIPO =====
        # Para MP: garantir que custo_servico seja sempre None
        if produto.tipo == 'MP':
            produto.custo_servico = None
            produto.custo_industrializacao = None
        
        # Para serviços: garantir que custo_material seja sempre None
        elif produto.tipo == 'PI' and produto.tipo_pi in ['SERVICO_INTERNO', 'SERVICO_EXTERNO']:
            produto.custo_material = None
            produto.custo_medio = None
        
        # Para produtos comprados: garantir que custo_servico seja sempre None
        elif produto.tipo == 'PI' and produto.tipo_pi == 'COMPRADO':
            produto.custo_servico = None
            produto.custo_industrializacao = None
        
        # Debug: Imprimir valores finais
        print(f"🐛 DEBUG SAVE - Valores finais:")
        print(f"  custo_material: {produto.custo_material}")
        print(f"  custo_servico: {produto.custo_servico}")
        print(f"  custo_medio (legacy): {produto.custo_medio}")
        print(f"  custo_industrializacao (legacy): {produto.custo_industrializacao}")
        
        if commit:
            produto.save()
        
        return produto


# ===================================================================
# FORMULÁRIOS DE FILTRO - SEM ALTERAÇÕES
# ===================================================================

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
        self.fields['tipo_pi'].choices = [('', 'Todos os Tipos PI')] + Produto.TIPO_PI_CHOICES
        self.fields['q'].widget.attrs['placeholder'] = 'Buscar por código, nome ou descrição...'


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


# ===================================================================
# FORMULÁRIOS SIMPLES - SEM ALTERAÇÕES
# ===================================================================

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