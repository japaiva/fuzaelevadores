# core/forms/vistoria.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from core.models import Proposta, VistoriaHistorico, Usuario
from .base import BaseModelForm, AuditMixin, ValidacaoComumMixin


class PropostaVistoriaForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """
    Formulário para alterar os campos de vistoria na proposta
    """
    class Meta:
        model = Proposta
        fields = [
            'status_obra',
            'data_vistoria_medicao', 
            'data_proxima_vistoria'
        ]
        
        widgets = {
            'status_obra': forms.Select(attrs={
                'class': 'form-select',
                'required': False
            }),
            'data_vistoria_medicao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_proxima_vistoria': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Definir data de hoje + 7 dias como padrão para próxima vistoria
        if not self.instance.pk and not self.initial.get('data_proxima_vistoria'):
            self.initial['data_proxima_vistoria'] = date.today() + timedelta(days=7)
        
        # Se está sendo preenchida pela primeira vez, usar data de hoje
        if not self.instance.pk and not self.initial.get('data_vistoria_medicao'):
            self.initial['data_vistoria_medicao'] = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        
        data_vistoria = cleaned_data.get('data_vistoria_medicao')
        data_proxima = cleaned_data.get('data_proxima_vistoria')
        status_obra = cleaned_data.get('status_obra')
        
        # Validar datas
        if data_vistoria and data_vistoria > date.today():
            raise ValidationError({
                'data_vistoria_medicao': 'A data da vistoria não pode ser futura.'
            })
        
        if data_proxima and data_proxima <= date.today():
            raise ValidationError({
                'data_proxima_vistoria': 'A data da próxima vistoria deve ser futura.'
            })
        
        # Se status da obra for definido, data da vistoria deve ser preenchida
        if status_obra and not data_vistoria:
            raise ValidationError({
                'data_vistoria_medicao': 'Para definir status da obra, a data da vistoria é obrigatória.'
            })
        
        return cleaned_data


class VistoriaHistoricoForm(BaseModelForm, AuditMixin, ValidacaoComumMixin):
    """
    Formulário para criar/editar registro de vistoria
    """
    # Campo adicional para selecionar novo status da obra
    status_obra_novo = forms.ChoiceField(
        choices=[('', 'Manter status atual')] + Proposta.STATUS_OBRA_CHOICES,
        required=False,
        label="Novo Status da Obra",
        help_text="Selecione se esta vistoria deve alterar o status da obra"
    )
    
    class Meta:
        model = VistoriaHistorico
        fields = [
            'data_agendada',
            'tipo_vistoria',
            'observacoes',
            'recomendacoes',
            'proxima_vistoria_sugerida',
        ]
        
        widgets = {
            'data_agendada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipo_vistoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações gerais da vistoria...'
            }),
            'recomendacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Recomendações técnicas e pendências...'
            }),
            'proxima_vistoria_sugerida': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.proposta = kwargs.pop('proposta', None)
        super().__init__(*args, **kwargs)
        
        # Definir data padrão para hoje
        if not self.instance.pk and not self.initial.get('data_agendada'):
            self.initial['data_agendada'] = date.today()
        
        # Definir próxima vistoria para 15 dias
        if not self.instance.pk and not self.initial.get('proxima_vistoria_sugerida'):
            self.initial['proxima_vistoria_sugerida'] = date.today() + timedelta(days=15)
    
    def clean(self):
        cleaned_data = super().clean()
        
        data_agendada = cleaned_data.get('data_agendada')
        proxima_vistoria = cleaned_data.get('proxima_vistoria_sugerida')
        
        # Validar datas
        if data_agendada and data_agendada < date.today() - timedelta(days=30):
            raise ValidationError({
                'data_agendada': 'Data da vistoria não pode ser muito antiga (máximo 30 dias).'
            })
        
        if proxima_vistoria and proxima_vistoria <= date.today():
            raise ValidationError({
                'proxima_vistoria_sugerida': 'A próxima vistoria deve ser futura.'
            })
        
        return cleaned_data


class VistoriaRealizadaForm(forms.ModelForm):
    """
    Formulário para marcar vistoria como realizada
    """
    # Campo adicional para alterar status da obra
    status_obra_novo = forms.ChoiceField(
        choices=[('', 'Manter status atual')] + Proposta.STATUS_OBRA_CHOICES,
        required=False,
        label="Alterar Status da Obra",
        help_text="Selecione para alterar o status da obra baseado nesta vistoria"
    )
    
    class Meta:
        model = VistoriaHistorico
        fields = [
            'data_realizada',
            'observacoes',
            'recomendacoes',
            'proxima_vistoria_sugerida'
        ]
        
        widgets = {
            'data_realizada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'O que foi observado na vistoria...'
            }),
            'recomendacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Recomendações e pendências encontradas...'
            }),
            'proxima_vistoria_sugerida': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Definir data realizada como hoje
        if not self.initial.get('data_realizada'):
            self.initial['data_realizada'] = date.today()
        
        # Próxima vistoria em 15 dias por padrão
        if not self.initial.get('proxima_vistoria_sugerida'):
            self.initial['proxima_vistoria_sugerida'] = date.today() + timedelta(days=15)
    
    def clean(self):
        cleaned_data = super().clean()
        
        data_realizada = cleaned_data.get('data_realizada')
        proxima_vistoria = cleaned_data.get('proxima_vistoria_sugerida')
        
        # Validar data realizada
        if data_realizada and data_realizada > date.today():
            raise ValidationError({
                'data_realizada': 'A data realizada não pode ser futura.'
            })
        
        if data_realizada and hasattr(self.instance, 'data_agendada') and data_realizada < self.instance.data_agendada:
            raise ValidationError({
                'data_realizada': 'A data realizada não pode ser anterior à data agendada.'
            })
        
        # Validar próxima vistoria
        if proxima_vistoria and proxima_vistoria <= date.today():
            raise ValidationError({
                'proxima_vistoria_sugerida': 'A próxima vistoria deve ser futura.'
            })
        
        return cleaned_data


class VistoriaFiltroForm(forms.Form):
    """
    Formulário para filtros na listagem de vistorias
    """
    STATUS_OBRA_CHOICES = [('', 'Todos')] + Proposta.STATUS_OBRA_CHOICES
    STATUS_VISTORIA_CHOICES = [('', 'Todos')] + [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('reagendada', 'Reagendada'),
    ]
    TIPO_VISTORIA_CHOICES = [('', 'Todos')] + [
        ('medicao', 'Medição Inicial'), 
        ('acompanhamento', 'Acompanhamento'), 
        ('obra_pronta', 'Obra Pronta'), 
        ('entrega', 'Entrega')
    ]
    
    status_obra = forms.ChoiceField(
        choices=STATUS_OBRA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    status_vistoria = forms.ChoiceField(
        choices=STATUS_VISTORIA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    tipo_vistoria = forms.ChoiceField(
        choices=TIPO_VISTORIA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    responsavel = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(is_active=True).order_by('first_name'),
        required=False,
        empty_label='Todos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    periodo_vistoria = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('vencidas', 'Vencidas'),
            ('hoje', 'Hoje'),
            ('semana', 'Esta semana'),
            ('mes', 'Este mês'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por número, projeto ou cliente...'
        })
    )