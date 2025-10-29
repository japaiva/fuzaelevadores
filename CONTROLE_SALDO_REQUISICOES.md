# Sistema de Controle de Saldo de Requisições

## Resumo da Implementação

Implementado sistema completo de controle de saldo entre **Requisições de Compra** e **Pedidos de Compra**, permitindo rastreabilidade e gestão de quantidades.

---

## ✅ Alterações Realizadas

### 1. **Modelo ItemRequisicaoCompra** (`core/models/producao.py`)

**Campos Adicionados:**
```python
quantidade_solicitada = DecimalField()  # Renomeado de 'quantidade'
quantidade_em_pedido = DecimalField(default=0)  # Calculado automaticamente
quantidade_recebida = DecimalField(default=0)   # Atualizado por signals
```

**Properties Adicionadas:**
- `quantidade_saldo`: Saldo disponível (solicitada - em_pedido - recebida)
- `percentual_atendido`: % já atendido
- `status_atendimento`: 'completo', 'em_andamento', 'parcial' ou 'pendente'

**Métodos:**
- `recalcular_quantidades()`: Recalcula quantidade_em_pedido baseado nos pedidos vinculados

---

### 2. **Modelo RequisicaoCompra** (`core/models/producao.py`)

**Métodos Adicionados:**
- `get_pedidos_vinculados()`: Retorna todos os pedidos relacionados aos itens
- `percentual_atendido_geral`: Percentual geral de atendimento (property)
- `status_atendimento_geral`: Status geral da requisição (property)

---

### 3. **Modelo PedidoCompra** (`core/models/compras.py`)

**Campo Adicionado:**
```python
orcamento = ForeignKey('OrcamentoCompra', blank=True, null=True)
```

**Método Adicionado:**
- `get_requisicoes_vinculadas()`: Retorna requisições vinculadas através dos itens

---

### 4. **Modelo ItemPedidoCompra** (`core/models/compras.py`)

**Campo Adicionado:**
```python
item_requisicao = ForeignKey('ItemRequisicaoCompra',
                             blank=True, null=True,
                             related_name='itens_pedido')
```

Este campo é a **CHAVE** para rastreabilidade:
- Vincula item do pedido ao item da requisição
- Permite controle de saldo automático
- Permite relatórios de atendimento

---

### 5. **Signals para Controle Automático** (`core/signals_saldo.py`)

**Signals Implementados:**

#### `atualizar_saldo_requisicao_ao_salvar_item`
Atualiza saldo da requisição quando item de pedido é criado/editado

#### `atualizar_saldo_requisicao_ao_deletar_item`
Devolve saldo quando item de pedido é deletado

#### `atualizar_saldo_requisicao_ao_alterar_status_pedido`
Recalcula saldo quando status do pedido muda (ex: cancelamento)

#### `atualizar_quantidade_recebida_requisicao`
Propaga quantidade recebida do pedido para a requisição

#### `validar_quantidade_contra_saldo`
Valida (warning) se quantidade do pedido não excede saldo disponível

**Lógica de Contagem:**
- Só conta pedidos com status: 'ENVIADO', 'CONFIRMADO', 'PARCIAL', 'RECEBIDO'
- Pedidos 'RASCUNHO' ou 'CANCELADO' NÃO afetam o saldo

---

### 6. **Formulários Atualizados** (`core/forms/producao.py`)

**ItemRequisicaoCompraForm:**
- Campo `quantidade` → `quantidade_solicitada`
- Labels e widgets atualizados

**ItemRequisicaoCompraFormSet:**
- Fields atualizados

---

##📊 Fluxo de Funcionamento

```
1. CRIAÇÃO DA REQUISIÇÃO
   REQ-001
   └─ Item A: 100 un (quantidade_solicitada=100, saldo=100)

2. CRIAÇÃO DO ORÇAMENTO
   ORC-001 (vinculado a REQ-001)
   └─ Item A: 100 un @ R$ 10

3. APROVAÇÃO DO ORÇAMENTO
   Status: aprovado

4. CRIAÇÃO DO PEDIDO (Parcial)
   PED-001 (vinculado a ORC-001)
   └─ Item A: 60 un (item_requisicao = REQ-001 Item A)

   ➜ SIGNAL atualiza REQ-001 Item A:
      quantidade_em_pedido = 60
      saldo = 40

5. CRIAR OUTRO PEDIDO (Parcial)
   PED-002
   └─ Item A: 30 un (item_requisicao = REQ-001 Item A)

   ➜ SIGNAL atualiza REQ-001 Item A:
      quantidade_em_pedido = 90
      saldo = 10

6. RECEBIMENTO
   PED-001 Item A: quantidade_recebida = 60

   ➜ SIGNAL atualiza REQ-001 Item A:
      quantidade_recebida = 60
      saldo = 10 (ainda há 30 em pedido pendente)

7. CANCELAMENTO DE PEDIDO
   PED-002: status = 'CANCELADO'

   ➜ SIGNAL recalcula REQ-001 Item A:
      quantidade_em_pedido = 60 (só PED-001)
      saldo = 40 (devolveu o saldo)
```

---

## 🎯 Funcionalidades Implementadas

### ✅ Regras Atendidas

1. **Mais de uma requisição em um pedido** ✅
   - `ItemPedidoCompra.item_requisicao` permite vincular qualquer requisição

2. **Alguns itens de uma requisição em um pedido** ✅
   - Cada item do pedido vincula-se individualmente

3. **Quantidade parcial de um item** ✅
   - `quantidade_em_pedido` soma todas as quantidades parciais

4. **Ver pedidos relacionados por item** ✅
   - `ItemRequisicaoCompra.itens_pedido.all()`
   - `RequisicaoCompra.get_pedidos_vinculados()`

5. **Lançar baixa de saldo** ✅
   - Via `quantidade_recebida` no `ItemPedidoCompra`
   - Propaga automaticamente via signal

6. **Relatório de saldos** ⏳
   - Models prontos com properties
   - Views e templates pendentes

7. **Cancelar pedido devolve saldo** ✅
   - Signal `atualizar_saldo_requisicao_ao_alterar_status_pedido`

---

## 🔧 Próximos Passos (Pendentes)

### 1. **Aplicar Migration**

```bash
# Na linha de comando interativa
python manage.py makemigrations core
# Quando perguntar sobre quantidade_solicitada, escolha opção 1
# Digite 0 como valor default one-off

python manage.py migrate
```

**IMPORTANTE**: A migration vai:
- Renomear `quantidade` → `quantidade_solicitada`
- Adicionar `quantidade_em_pedido` (default=0)
- Adicionar `quantidade_recebida` (default=0)
- Adicionar `item_requisicao` em `ItemPedidoCompra`
- Adicionar `orcamento` em `PedidoCompra`

### 2. **Criar Views de Gestão de Pedidos**

```python
# producao/views/pedidos.py
- pedido_list
- pedido_create_from_orcamento
- pedido_detail
- pedido_editar
- pedido_enviar
- pedido_cancelar
- pedido_receber (para baixa de material)
```

### 3. **Criar Views de Relatórios**

```python
# producao/views/relatorios.py
- requisicoes_saldo (lista requisições com saldo pendente)
- requisicao_detail_saldo (detalhes de saldo por item)
- pedidos_vinculados (pedidos de uma requisição)
```

### 4. **Criar Templates**

```
templates/producao/
├── pedido_list.html
├── pedido_form.html
├── pedido_detail.html
├── pedido_recebimento.html
├── requisicao_detail.html (atualizar com info de saldo)
└── relatorio_saldos.html
```

### 5. **Adicionar URLs**

```python
# producao/urls.py
path('pedidos/', pedido_list, name='pedido_list'),
path('pedidos/novo/<int:orcamento_id>/', pedido_create, name='pedido_create'),
path('pedidos/<int:pk>/', pedido_detail, name='pedido_detail'),
path('relatorios/saldos/', relatorio_saldos, name='relatorio_saldos'),
```

### 6. **Atualizar Templates Existentes**

- **requisicao_detail.html**: Mostrar tabela de saldo com colunas:
  - Produto | Qtd Solicitada | Em Pedido | Recebida | Saldo | Pedidos

- **requisicao_list.html**: Adicionar coluna de % atendimento

---

## 📝 Exemplo de Uso nas Views

```python
# Criar pedido vinculado a requisição
pedido = PedidoCompra.objects.create(
    fornecedor=fornecedor,
    orcamento=orcamento,  # opcional
    ...
)

# Adicionar item vinculado à requisição
item_req = ItemRequisicaoCompra.objects.get(id=item_req_id)
ItemPedidoCompra.objects.create(
    pedido=pedido,
    produto=item_req.produto,
    item_requisicao=item_req,  # ← CHAVE
    quantidade=50,  # quantidade parcial
    valor_unitario=10,
)

# Saldo é atualizado automaticamente via signal!
# item_req.quantidade_saldo agora reflete a compra

# Consultar saldo
print(f"Saldo: {item_req.quantidade_saldo}")
print(f"Status: {item_req.status_atendimento}")
print(f"% Atendido: {item_req.percentual_atendido}%")

# Ver pedidos vinculados à requisição
pedidos = item_req.requisicao.get_pedidos_vinculados()
```

---

## 🛡️ Validações e Segurança

1. **Validação de Saldo**: Signal `validar_quantidade_contra_saldo` emite warning se quantidade exceder saldo (pode ser convertido para erro hard)

2. **Recalculo Automático**: Signals garantem que saldo sempre está correto

3. **Status de Pedido**: Só pedidos ativos afetam o saldo

4. **Cascade Protegido**: `item_requisicao` usa `PROTECT` para evitar deleção acidental

---

## 🎓 Conceitos Importantes

**Saldo Disponível** = Quantidade Solicitada - Quantidade em Pedido - Quantidade Recebida

**Quantidade em Pedido**: Soma de todos os itens de pedidos ATIVOS vinculados

**Status de Atendimento**:
- `pendente`: Nada foi pedido/recebido
- `parcial`: Algo foi pedido/recebido, mas não tudo
- `em_andamento`: Tudo em pedido mas não totalmente recebido
- `completo`: Tudo recebido

---

## 📚 Arquivos Modificados

- ✅ `core/models/producao.py` - ItemRequisicaoCompra, RequisicaoCompra
- ✅ `core/models/compras.py` - PedidoCompra, ItemPedidoCompra
- ✅ `core/signals_saldo.py` - NOVO - Signals de controle
- ✅ `core/apps.py` - Import dos signals
- ✅ `core/forms/producao.py` - Formulários atualizados

---

**Status**: ⚠️ **Implementação Core Completa - Aguardando Migration + Views/Templates**
