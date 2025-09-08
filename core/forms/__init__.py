# core/forms/__init__.py

# === CLASSES BASE ===
from .base import (
    BaseModelForm,
    BaseFiltroForm, 
    AuditMixin,
    ValidacaoComumMixin,
    MoneyInput,
    PercentageInput,
    QuantityInput,
    CustomDateInput,
    DateAwareModelForm,
    validar_positivo,
    validar_porcentagem,
    validar_codigo_sequencial
)

# === FORMULÁRIOS DE USUÁRIOS ===
from .usuarios import (
    UsuarioForm,
    UsuarioFiltroForm,
    AlterarSenhaForm
)

# === FORMULÁRIOS DE CLIENTES ===
from .clientes import (
    ClienteForm,
    ClienteCreateForm,
    ClienteFiltroForm,
    BuscaClienteForm,
    ClienteEnderecoForm,
    ClienteContatoForm
)

# === FORMULÁRIOS DE FORNECEDORES ===
from .fornecedores import (
    FornecedorForm,
    FornecedorProdutoForm,
    FornecedorProdutoFormSet,
    FornecedorFiltroForm,
    CotacaoForm,
    AvaliacaoFornecedorForm
)

# === FORMULÁRIOS DE PRODUTOS ===
from .produtos import (
    GrupoProdutoForm,
    SubgrupoProdutoForm,
    ProdutoForm,
    GrupoProdutoFiltroForm,
    SubgrupoProdutoFiltroForm,
    ProdutoFiltroForm,
    ProdutoEstoqueForm,
    ProdutoPrecoForm
)

# === FORMULÁRIOS DE COMPRAS ===
from .compras import (
    PedidoCompraForm,
    ItemPedidoCompraForm,
    ItemPedidoCompraFormSet,
    PedidoCompraFiltroForm,
    AlterarStatusPedidoForm,
    RecebimentoItemForm,
    RecebimentoPedidoForm
)

# === FORMULÁRIOS DE PROPOSTAS ===
from .propostas import (
    PropostaClienteElevadorForm,
    PropostaCabinePortasForm,
    PropostaComercialForm,
    PropostaFiltroForm,
    ClienteCreateForm as PropostaClienteCreateForm,
    AnexoPropostaForm,  
    PropostaStatusForm,
)

# Formulários de Vistoria
from .vistoria import (
    PropostaVistoriaForm,
    VistoriaHistoricoForm,
    VistoriaFiltroForm,
)


# === FORMULÁRIOS DE PARÂMETROS ===
from .parametros import (
    ParametrosGeraisForm,
    ConfiguracaoEmailForm,
    ConfiguracaoSistemaForm,
    PermissoesForm
)

# === FORMULÁRIOS DE PRODUÇÃO ===
from .producao import (    # Lista de Materiais
    ListaMateriaisForm,
    ItemListaMateriaisForm,
    ItemListaMateriaisFormSet,
    
    # Requisição de Compra
    RequisicaoCompraForm,
    RequisicaoCompraFiltroForm,
    
    # Orçamento de Compra
    OrcamentoCompraForm,
    ItemOrcamentoCompraForm,
    ItemOrcamentoCompraFormSet,
    OrcamentoCompraFiltroForm,
    AlterarStatusOrcamentoForm,
)

# === FORMULÁRIOS DE REGRAS YAML ===
from .regras_yaml import (
    RegraYAMLForm,
    RegraYAMLFiltroForm
)

# === LISTA DE TODOS OS FORMULÁRIOS DISPONÍVEIS ===
__all__ = [
    # Classes Base
    'BaseModelForm',
    'BaseFiltroForm', 
    'AuditMixin',
    'ValidacaoComumMixin',
    'MoneyInput',
    'PercentageInput',
    'QuantityInput',
    'CustomDateInput',
    'DateAwareModelForm',
    'validar_positivo',
    'validar_porcentagem',
    'validar_codigo_sequencial',
    
    # Usuários
    'UsuarioForm',
    'UsuarioFiltroForm',
    'AlterarSenhaForm',
    
    # Clientes
    'ClienteForm',
    'ClienteCreateForm',
    'ClienteFiltroForm',
    'BuscaClienteForm',
    'ClienteEnderecoForm',
    'ClienteContatoForm',
    
    # Fornecedores
    'FornecedorForm',
    'FornecedorProdutoForm',
    'FornecedorProdutoFormSet',
    'FornecedorFiltroForm',
    'CotacaoForm',
    'AvaliacaoFornecedorForm',
    
    # Produtos
    'GrupoProdutoForm',
    'SubgrupoProdutoForm',
    'ProdutoForm',
    'GrupoProdutoFiltroForm',
    'SubgrupoProdutoFiltroForm',
    'ProdutoFiltroForm',
    'ProdutoEstoqueForm',
    'ProdutoPrecoForm',
    
    # Compras
    'PedidoCompraForm',
    'ItemPedidoCompraForm',
    'ItemPedidoCompraFormSet',
    'PedidoCompraFiltroForm',
    'AlterarStatusPedidoForm',
    'RecebimentoItemForm',
    'RecebimentoPedidoForm',
    
    # Propostas
    'PropostaClienteElevadorForm',
    'PropostaCabinePortasForm',
    'PropostaComercialForm',
    'PropostaFiltroForm',
    'PropostaClienteCreateForm',
    'AnexoPropostaForm',
    'PropostaStatusForm',

    # Vistorias
    'PropostaVistoriaForm',
    'VistoriaHistoricoForm',
    'VistoriaFiltroForm',
    
    # Parâmetros
    'ParametrosGeraisForm',
    'ConfiguracaoEmailForm',
    'ConfiguracaoSistemaForm',
    'PermissoesForm',
    
    # Produção - Fluxo Completo
    'ListaMateriaisForm',
    'ItemListaMateriaisForm', 
    'ItemListaMateriaisFormSet',
    'RequisicaoCompraForm',
    'RequisicaoCompraFiltroForm',
    'OrcamentoCompraForm',
    'ItemOrcamentoCompraForm',
    'ItemOrcamentoCompraFormSet',
    'OrcamentoCompraFiltroForm',
    'AlterarStatusOrcamentoForm',
    
    # Regras YAML - Motor de Regras Configurável
    'RegraYAMLForm',
    'RegraYAMLFiltroForm',
]