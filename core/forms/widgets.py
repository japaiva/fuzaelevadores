# core/forms/widgets.py - CRIAR ESTE ARQUIVO OU ADICIONAR SE JÁ EXISTE

from django import forms
from django.urls import reverse_lazy

class ProdutoSearchWidget(forms.TextInput):
    """
    Widget simples para busca de produtos com autocomplete
    Solução direta sem bibliotecas externas complexas
    """
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control produto-search-input',
            'placeholder': 'Digite código ou nome do produto...',
            'autocomplete': 'off',
            'data-api-url': reverse_lazy('producao:api_buscar_produtos'),
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
    
    class Media:
        css = {
            'all': ('css/produto-search.css',)
        }
        js = ('js/produto-search.js',)