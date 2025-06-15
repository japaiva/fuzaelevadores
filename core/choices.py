# core/choices.py

from django.apps import apps
from core.models.base import (
    TIPO_PRODUTO_CHOICES,
    STATUS_PEDIDO_CHOICES,
    PRIORIDADE_PEDIDO_CHOICES,
    NIVEL_USUARIO_CHOICES,
    TIPO_PESSOA_CHOICES # ADDED THIS IMPORT for Cliente choices
) 

def get_nivel_usuario_choices():
    return NIVEL_USUARIO_CHOICES

def get_tipo_pessoa_choices():
    # Corrected: Directly return TIPO_PESSOA_CHOICES from core.models.base
    return TIPO_PESSOA_CHOICES

def get_tipo_produto_choices():
    return TIPO_PRODUTO_CHOICES

def get_status_pedido_choices():
    return STATUS_PEDIDO_CHOICES

def get_prioridade_pedido_choices():
    return PRIORIDADE_PEDIDO_CHOICES

# NEW: Getter functions for EspecificacaoElevador and SimulacaoElevador choices
def get_especificacao_elevador_tipo_choices():
    EspecificacaoElevador = apps.get_model('core', 'EspecificacaoElevador')
    return EspecificacaoElevador.TIPO_CHOICES

def get_simulacao_elevador_status_choices():
    SimulacaoElevador = apps.get_model('core', 'SimulacaoElevador')
    return SimulacaoElevador.STATUS_CHOICES

# Constants for widgets (if not tied to a model and used broadly)
ESTADOS_BRASIL = [
    ('', 'Selecione...'),
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'),
    ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'),
    ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
    ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'),
    ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'),
    ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
]