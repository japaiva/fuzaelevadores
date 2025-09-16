# core/forms/vistoria_medicao.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from core.models import Proposta, VistoriaHistorico, VaoPortaVistoria, criar_vaos_porta_automaticos
from .base import BaseModelForm, AuditMixin, ValidacaoComumMixin, CustomDateInput, QuantityInput


class VistoriaMedicaoForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """
    Formulário específico para vistoria de medição inicial
    Inclui todos os campos de medição técnica
    """
    
    class Meta:
        model = VistoriaHistorico
        fields = [
            # Dados básicos da vistoria
            'data_realizada',
            'observacoes',
            'recomendacoes',
            'proxima_vistoria_sugerida',
            
            # === MEDIÇÕES TÉCNICAS ===
            # FOSSO
            'fosso_altura',
            'fosso_largura', 
            'fosso_profundidade',
            'fosso_obs',
            
            # POÇO
            'poco_largura',
            'poco_profundidade', 
            'poco_obs',
            
            # CINTAS
            'cintas_largura',
            'cintas_distancia',
            'cintas_obs',
            
            # CASA DE MÁQUINA
            'casa_maquina_altura',
            'casa_maquina_gancho',
            'casa_maquina_energia',
            'casa_maquina_obs',
        ]
        
        widgets = {
            # Dados básicos
            'data_realizada': CustomDateInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações gerais da medição...'
            }),
            'recomendacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recomendações técnicas...'
            }),
            'proxima_vistoria_sugerida': CustomDateInput(attrs={
                'class': 'form-control'
            }),
            
            # === MEDIÇÕES ===
            # FOSSO
            'fosso_altura': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'fosso_largura': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'fosso_profundidade': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'fosso_obs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Condições do fosso, problemas encontrados...'
            }),
            
            # POÇO
            'poco_largura': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'poco_profundidade': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'poco_obs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Condições do poço...'
            }),
            
            # CINTAS
            'cintas_largura': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'cintas_distancia': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'cintas_obs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Estado das cintas, alinhamento...'
            }),
            
            # CASA DE MÁQUINA
            'casa_maquina_altura': QuantityInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'form-control medida-input'
            }),
            'casa_maquina_gancho': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[(True, 'Sim'), (False, 'Não')]),
            'casa_maquina_energia': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[(True, 'Sim'), (False, 'Não')]),
            'casa_maquina_obs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Condições da casa de máquina...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.proposta = kwargs.pop('proposta', None)
        super().__init__(*args, **kwargs)
        
        # Definir data padrão para hoje
        if not self.instance.pk and not self.initial.get('data_realizada'):
            self.initial['data_realizada'] = date.today()
        
        # Definir próxima vistoria para 15 dias
        if not self.instance.pk and not self.initial.get('proxima_vistoria_sugerida'):
            self.initial['proxima_vistoria_sugerida'] = date.today() + timedelta(days=15)
        
        # Preencher valores iniciais baseados na proposta se disponível
        if self.proposta and not self.instance.pk:
            # Usar dimensões da proposta como referência inicial
            if hasattr(self.proposta, 'largura_poco') and self.proposta.largura_poco:
                self.initial['poco_largura'] = self.proposta.largura_poco
            if hasattr(self.proposta, 'comprimento_poco') and self.proposta.comprimento_poco:
                self.initial['poco_profundidade'] = self.proposta.comprimento_poco
            if hasattr(self.proposta, 'altura_poco') and self.proposta.altura_poco:
                self.initial['casa_maquina_altura'] = self.proposta.altura_poco
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar data de realização
        data_realizada = cleaned_data.get('data_realizada')
        if data_realizada and data_realizada < date.today() - timedelta(days=30):
            raise ValidationError({
                'data_realizada': 'Data da medição não pode ser muito antiga (máximo 30 dias).'
            })
        
        # Validar próxima vistoria
        proxima_vistoria = cleaned_data.get('proxima_vistoria_sugerida')
        if proxima_vistoria and proxima_vistoria <= date.today():
            raise ValidationError({
                'proxima_vistoria_sugerida': 'A próxima vistoria deve ser futura.'
            })
        
        # Validações de medidas (opcionais mas se preenchidas devem ser válidas)
        medidas_fosso = [
            cleaned_data.get('fosso_altura'),
            cleaned_data.get('fosso_largura'),
            cleaned_data.get('fosso_profundidade')
        ]
        
        medidas_poco = [
            cleaned_data.get('poco_largura'),
            cleaned_data.get('poco_profundidade')
        ]
        
        medidas_cintas = [
            cleaned_data.get('cintas_largura'),
            cleaned_data.get('cintas_distancia')
        ]
        
        # Se pelo menos uma medida do fosso foi preenchida, validar consistência
        if any(medidas_fosso):
            for campo, valor in [
                ('fosso_altura', cleaned_data.get('fosso_altura')),
                ('fosso_largura', cleaned_data.get('fosso_largura')),
                ('fosso_profundidade', cleaned_data.get('fosso_profundidade'))
            ]:
                if valor is not None and (valor <= 0 or valor > 50):
                    raise ValidationError({
                        campo: 'Medida deve estar entre 0.01 e 50 metros.'
                    })
        
        # Validações similares para poço e cintas
        for campo, valor in [
            ('poco_largura', cleaned_data.get('poco_largura')),
            ('poco_profundidade', cleaned_data.get('poco_profundidade')),
            ('cintas_largura', cleaned_data.get('cintas_largura')),
            ('cintas_distancia', cleaned_data.get('cintas_distancia')),
            ('casa_maquina_altura', cleaned_data.get('casa_maquina_altura'))
        ]:
            if valor is not None and (valor <= 0 or valor > 50):
                raise ValidationError({
                    campo: 'Medida deve estar entre 0.01 e 50 metros.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        vistoria = super().save(commit=False)
        
        # Definir campos específicos de medição
        vistoria.tipo_vistoria = 'medicao'
        vistoria.status_vistoria = 'realizada'
        
        if commit:
            vistoria.save()
            
            # Criar vãos de porta automaticamente baseado no número de pavimentos
            if self.proposta and hasattr(self.proposta, 'pavimentos'):
                criar_vaos_porta_automaticos(vistoria, self.proposta.pavimentos)
        
        return vistoria


class VaoPortaVistoriaFormSet(forms.BaseInlineFormSet):
    """
    FormSet para gerenciar os vãos de porta por pavimento
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar formulários individuais
        for form in self.forms:
            form.fields['largura'].widget.attrs.update({
                'class': 'form-control medida-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
            form.fields['altura'].widget.attrs.update({
                'class': 'form-control medida-input', 
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
            form.fields['observacoes'].widget.attrs.update({
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observações específicas...'
            })
    
    def clean(self):
        """Validação do formset"""
        super().clean()
        
        if any(self.errors):
            return
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                largura = form.cleaned_data.get('largura')
                altura = form.cleaned_data.get('altura')
                
                if largura and (largura <= 0 or largura > 5):
                    raise ValidationError('Largura dos vãos deve estar entre 0.01 e 5 metros.')
                
                if altura and (altura <= 0 or altura > 4):
                    raise ValidationError('Altura dos vãos deve estar entre 0.01 e 4 metros.')


# Factory para criar o formset
VaoPortaFormSet = forms.inlineformset_factory(
    VistoriaHistorico,
    VaoPortaVistoria,
    formset=VaoPortaVistoriaFormSet,
    fields=['pavimento', 'largura', 'altura', 'observacoes'],
    extra=0,  # Não criar forms extras - usar os criados automaticamente
    can_delete=False,  # Não permitir deletar pavimentos
    widgets={
        'pavimento': forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True  # Pavimento não pode ser alterado
        }),
        'largura': QuantityInput(attrs={
            'class': 'form-control medida-input',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        'altura': QuantityInput(attrs={
            'class': 'form-control medida-input',
            'step': '0.01', 
            'min': '0',
            'placeholder': '0.00'
        }),
        'observacoes': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Obs. específicas do pavimento...'
        })
    }
)