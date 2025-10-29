# 🎨 Visualização: Pedido de Compra com Vínculo à Requisição

## Tela de Criação/Edição de Pedido de Compra

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📝 Criar Pedido de Compra                                         [Voltar à Lista] │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📄 Dados do Pedido                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Fornecedor: [Selecionar Fornecedor ▼]                                             │
│  Data Emissão: [DD/MM/AAAA]    Prazo: [15] dias    Entrega: [DD/MM/AAAA]          │
│  Prioridade: [Normal ▼]        Pagamento: [30 dias]                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📦 Itens do Pedido                                      [+ Adicionar Item]          │
├──┬──────────────────┬────────────────────────┬─────┬─────────┬─────────┬───────┬───┤
│# │ Produto *        │ Requisição             │ Qtd │ Valor   │ Total   │ Obs   │ × │
├──┼──────────────────┼────────────────────────┼─────┼─────────┼─────────┼───────┼───┤
│  │                  │                        │     │         │         │       │   │
│1 │[Buscar produto..]│┏━━━━━━━━━━━━━━━━━━━━┓ │[10] │R$ [100] │R$ 1000  │[...]  │[🗑]│
│  │✓ MP-001 - Aço   │┃Vincular à Requisição┃ │     │         │         │       │   │
│  │                  │┗━━━━━━━━━━━━━━━━━━━━┛ │     │         │         │       │   │
│  │                  │▼ Sem vínculo           │     │         │         │       │   │
│  │                  │  Req 2024-001 - MP-001 │     │         │         │       │   │
│  │                  │    (Saldo: 50 KG)      │     │         │         │       │   │
│  │                  │  Req 2024-003 - MP-001 │     │         │         │       │   │
│  │                  │    (Saldo: 30 KG)      │     │         │         │       │   │
│  │                  │                        │     │         │         │       │   │
│  │                  │ℹ️ Opcional - controla   │     │         │         │       │   │
│  │                  │  saldo                 │     │         │         │       │   │
├──┼──────────────────┼────────────────────────┼─────┼─────────┼─────────┼───────┼───┤
│  │                  │                        │     │         │         │       │   │
│2 │[Buscar produto..]│[Sem vínculo        ▼] │[5]  │R$ [200] │R$ 1000  │[...]  │[🗑]│
│  │✓ PI-002 - Motor │ℹ️ Opcional              │     │         │         │       │   │
├──┴──────────────────┴────────────────────────┴─────┴─────────┴─────────┴───────┴───┤
│  [+ Adicionar Item]                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💰 Resumo Financeiro                                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Subtotal: R$ 2.000,00    Desconto: [0]%    Frete: R$ [0,00]                      │
│  TOTAL: R$ 2.000,00                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                               [Cancelar]  [Salvar Pedido]
```

---

## 🎯 Destaques Visuais

### Campo de Requisição

```
┌─────────────────────────────────────┐
│ ┃ Vincular à Requisição         ▼ │ ← Borda AZUL (3px esquerda)
├─────────────────────────────────────┤
│   Sem vínculo com requisição       │
│   ────────────────────────────────  │
│   Req 2024-001 - MP-001 - Aço      │
│     (Saldo: 50.00 KG)               │
│   Req 2024-003 - MP-001 - Aço      │
│     (Saldo: 30.00 KG)               │
│   Req 2024-005 - MP-001 - Aço      │
│     (Saldo: 15.50 KG)               │
└─────────────────────────────────────┘
  ℹ️ Opcional - controla saldo
```

**Quando SELECIONADO:**
```
┌─────────────────────────────────────┐
│ ┃ Req 2024-001 - MP-001         ▼ │ ← Fundo AZUL CLARO (#e7f3ff)
└─────────────────────────────────────┘
  ℹ️ Opcional - controla saldo
```

---

## ⚡ Funcionalidades

### 1. **Dropdown Inteligente**
- Mostra apenas requisições **abertas** ou **aprovadas**
- Filtra apenas itens com **saldo disponível > 0**
- Exibe informações: `Req XXXX - CODIGO (Saldo: X.XX UN)`

### 2. **Validações Automáticas**

#### ✅ Validação de Produto
```
❌ ERRO: O produto selecionado (MP-002) não corresponde
         ao produto da requisição (MP-001).
```

#### ✅ Validação de Quantidade
```
❌ ERRO: Quantidade (100) excede o saldo disponível
         (50.00 KG).
```

### 3. **Comportamento**

| Situação | Comportamento |
|----------|---------------|
| Sem vínculo | Campo opcional fica vazio - pedido sem controle de saldo |
| Com vínculo | Valida produto e quantidade - atualiza saldo automaticamente |
| Produto diferente | Erro - impede salvar |
| Quantidade excedida | Erro - impede salvar |

---

## 📊 Exemplo de Uso

### Cenário 1: Vincular Item a Requisição

1. **Selecionar Produto**: Busca e seleciona "MP-001 - Aço Inox"
2. **Escolher Requisição**: Dropdown mostra:
   ```
   Req 2024-001 - MP-001 (Saldo: 50.00 KG)
   Req 2024-003 - MP-001 (Saldo: 30.00 KG)
   ```
3. **Seleciona**: Req 2024-001
4. **Informar Quantidade**: 20 KG (dentro do saldo de 50)
5. **Salvar**: ✅ Item vinculado - saldo atualiza para 30 KG

### Cenário 2: Criar Pedido sem Vínculo

1. **Selecionar Produto**: Busca e seleciona "PI-005 - Motor Elétrico"
2. **Deixar Requisição**: "Sem vínculo com requisição" (padrão)
3. **Informar Quantidade**: 5 UN
4. **Salvar**: ✅ Pedido criado normalmente - sem controle de saldo

### Cenário 3: Erro de Validação

1. **Selecionar Produto**: MP-001
2. **Escolher Requisição**: Req 2024-001 (Saldo: 50 KG)
3. **Informar Quantidade**: 100 KG ❌
4. **Ao Salvar**:
   ```
   ❌ Quantidade (100) excede o saldo disponível (50.00 KG).
   ```

---

## 🎨 Estilos CSS Aplicados

```css
/* Campo com borda azul destacada */
select[name$="item_requisicao"] {
  border-left: 3px solid #0d6efd;  /* Azul Bootstrap */
  font-size: 0.875rem;
}

/* Foco com shadow azul */
select[name$="item_requisicao"]:focus {
  border-left: 3px solid #0a58ca;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.15);
}

/* Fundo azul claro quando selecionado */
select[name$="item_requisicao"]:not([value=""]) {
  background-color: #e7f3ff;
}
```

---

## 📝 Informações Adicionais

### Label e Help Text
- **Label**: "Requisição" (coluna da tabela)
- **Help Text**: "ℹ️ Opcional - controla saldo"
- **Empty Label**: "Sem vínculo com requisição"

### Formato do Dropdown
```
Req [NUMERO] - [CODIGO_PRODUTO] (Saldo: [QUANTIDADE] [UNIDADE])
```

**Exemplos:**
- `Req 2024-001 - MP-001 (Saldo: 50.00 KG)`
- `Req 2024-003 - PI-005 (Saldo: 10.00 UN)`
- `Req 2024-010 - PA-120 (Saldo: 2.50 M)`

---

## ✅ Status da Implementação

✅ Formulário atualizado com campo `item_requisicao`
✅ Validações de produto e quantidade implementadas
✅ Template atualizado com nova coluna
✅ CSS aplicado para destaque visual
✅ Help text e informações de uso
✅ Filtro de requisições com saldo disponível
✅ Sistema check sem erros

**🎉 PRONTO PARA USO!**

---

## 🚀 Como Testar

1. Acesse: **Pedidos de Compra → Novo Pedido**
2. Preencha fornecedor e dados básicos
3. Adicione um item ao pedido
4. Busque e selecione um produto
5. **NOVO**: No campo "Requisição", escolha uma requisição ou deixe "Sem vínculo"
6. Preencha quantidade e valor
7. Salve o pedido

Se vincular a uma requisição, o sistema automaticamente:
- ✅ Valida o produto
- ✅ Valida a quantidade contra o saldo
- ✅ Atualiza o saldo da requisição
- ✅ Registra o vínculo para rastreabilidade
