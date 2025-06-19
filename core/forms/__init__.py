# core/forms/__init__.py

"""
Importações dos formulários do sistema FUZA
Mantém imports explícitos para melhor controle e debug
"""

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

# === FORMULÁRIOS DE ELEVADORES ===
from .elevadores import (
    EspecificacaoElevadorForm,
    OpcaoEspecificacaoForm,
    RegraComponenteForm,
    ComponenteDerivadoForm,
    SimulacaoElevadorForm,
    EspecificacaoFiltroForm,
    SimulacaoFiltroForm
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
    AnexoPropostaForm
)

# === FORMULÁRIOS DE PARÂMETROS ===
from .parametros import (
    ParametrosGeraisForm,
    ConfiguracaoEmailForm,
    ConfiguracaoSistemaForm,
    PermissoesForm
)

# === FORMULÁRIOS DE PRODUÇÃO ===
from .producao import (
    # Lista de Materiais
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
    
    # Elevadores
    'EspecificacaoElevadorForm',
    'OpcaoEspecificacaoForm',
    'RegraComponenteForm',
    'ComponenteDerivadoForm',
    'SimulacaoElevadorForm',
    'EspecificacaoFiltroForm',
    'SimulacaoFiltroForm',
    
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
]