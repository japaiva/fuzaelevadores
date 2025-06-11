# core/models/base.py

"""
Choices e constantes base para o sistema
"""

# ===============================================
# CHOICES PARA FORMULÁRIOS E MODELS
# ===============================================

STATUS_PEDIDO_CHOICES = [
    ('RASCUNHO', 'Rascunho'),
    ('ENVIADO', 'Enviado'),
    ('CONFIRMADO', 'Confirmado'),
    ('PARCIAL', 'Parcialmente Recebido'),
    ('RECEBIDO', 'Recebido'),
    ('CANCELADO', 'Cancelado'),
]

PRIORIDADE_PEDIDO_CHOICES = [
    ('BAIXA', 'Baixa'),
    ('NORMAL', 'Normal'),
    ('ALTA', 'Alta'),
    ('URGENTE', 'Urgente'),
]

TIPO_PRODUTO_CHOICES = [
    ('MP', 'Matéria Prima'),
    ('PI', 'Produto Intermediário'),
    ('PA', 'Produto Acabado'),
]

UNIDADE_MEDIDA_CHOICES = [
    ('UN', 'Unidade'),
    ('KG', 'Quilograma'),
    ('MT', 'Metro'),
    ('M2', 'Metro Quadrado'),
    ('M3', 'Metro Cúbico'),
    ('PC', 'Peça'),
    ('CJ', 'Conjunto'),
]

STATUS_PRODUTO_CHOICES = [
    ('ATIVO', 'Ativo'),
    ('INATIVO', 'Inativo'),
    ('DESCONTINUADO', 'Descontinuado'),
]

TIPO_PESSOA_CHOICES = [
    ('PF', 'Pessoa Física'),
    ('PJ', 'Pessoa Jurídica'),
]

NIVEL_USUARIO_CHOICES = [
    ('admin', 'Admin'),
    ('gestor', 'Gestor'),
    ('vendedor', 'Vendedor'),
    ('compras', 'Compras'),
    ('engenharia', 'Engenharia'),
]

PRIORIDADE_FORNECEDOR_CHOICES = [
    (1, 'Principal'),
    (2, 'Secundário'),
    (3, 'Terceiro'),
    (4, 'Backup'),
]

TIPO_CALCULO_CHOICES = [
    ('proporcional', 'Proporcional'),
    ('fixo', 'Valor Fixo'),
    ('formula', 'Fórmula'),
]

TIPO_ESPECIFICACAO_CHOICES = [
    ('categoria', 'Categoria'),
    ('material', 'Material'),
    ('acabamento', 'Acabamento'),
    ('dimensao', 'Dimensão'),
    ('capacidade', 'Capacidade'),
    ('velocidade', 'Velocidade'),
    ('paradas', 'Número de Paradas'),
    ('opcional', 'Opcional'),
]

STATUS_SIMULACAO_CHOICES = [
    ('rascunho', 'Rascunho'),
    ('simulado', 'Simulado'),
    ('proposta', 'Proposta Gerada'),
    ('aprovado', 'Aprovado'),
    ('rejeitado', 'Rejeitado'),
]