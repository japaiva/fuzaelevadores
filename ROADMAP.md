# ROADMAP - Sistema FUZA Elevadores

## Visao Geral do Projeto

Sistema ERP para gestao de elevadores, incluindo:
- Portal Vendedor (propostas, simulacoes, contratos)
- Portal Gestor (cadastros, estoque, configuracoes)
- Portal Producao (compras, requisicoes, OPs)

---

## Modulo de Estoque - Status Atual

### FASE 1 - Cadastros Base (CONCLUIDA)
- [x] LocalEstoque (almoxarifado, producao, terceiros, beneficiamento)
- [x] TipoMovimentoEntrada (compra, devolucao, transferencia, ajuste)
- [x] TipoMovimentoSaida (producao, venda, transferencia, ajuste)
- [x] Views CRUD completas
- [x] Templates e menu

### FASE 2 - Movimentacoes (CONCLUIDA)
- [x] MovimentoEntrada com itens
- [x] MovimentoSaida com itens
- [x] Numeracao automatica (ENT-AAMM0001, SAI-AAMM0001)
- [x] Workflow: Rascunho -> Confirmado -> Cancelado
- [x] Atualizacao automatica de estoque_atual do Produto
- [x] Posicao de Estoque (visao consolidada)
- [x] Suporte a local de terceiros (beneficiamento)

### FASE 3 - Ajustes (PENDENTE)
- [ ] Inventario fisico (contagem e ajuste)
- [ ] Transferencias entre locais
- [ ] Ajustes manuais (quebra, perda, bonificacao)
- [ ] Historico de movimentacoes por produto

### FASE 4 - Ordens de Producao (CONCLUIDA)
- [x] Modelo OrdemProducao
- [x] Modelo ItemConsumoOP (materiais a consumir)
- [x] Calculo automatico de materiais baseado na estrutura
- [x] Workflow: Rascunho -> Liberada -> Em Producao -> Concluida -> Cancelada
- [x] Reserva de materiais ao liberar
- [x] Consumo de MP/PI ao concluir
- [x] Producao de PA/PI com entrada no estoque
- [x] Integracao com estrutura de componentes
- [x] Apontamento de producao parcial
- [x] Templates completos (lista, form, detalhe, apontar, excluir)

### FASE 5 - Integracoes (FUTURO)
- [ ] Integracao Pedido Compra -> Entrada Estoque
- [ ] Integracao OP -> Saida Estoque (consumo)
- [ ] Integracao OP -> Entrada Estoque (producao)
- [ ] Custo medio automatico

### FASE 6 - Relatorios (FUTURO)
- [ ] Kardex por produto
- [ ] Curva ABC
- [ ] Produtos sem movimentacao
- [ ] Previsao de compras

---

## Modulo de Produtos - Status

### Materias-Primas (MP) - CONCLUIDO
- [x] CRUD completo
- [x] Filtros por grupo, subgrupo, status
- [x] Toggle utilizado/nao utilizado
- [x] Localizacao: Portal Producao (menu Gestor aponta para producao)

### Produtos Intermediarios (PI) - CONCLUIDO
- [x] CRUD completo
- [x] Tipos: Comprado, Montado Interno/Externo, Servico Interno/Externo
- [x] Estrutura de componentes (BOM)
- [x] Calculo de custo automatico baseado na estrutura
- [x] Localizacao: Portal Producao (menu Gestor aponta para producao)

### Produtos Acabados (PA) - CONCLUIDO
- [x] CRUD completo
- [x] Campos: custo_material, custo_servico, custo_total
- [x] Localizacao: Portal Gestor

---

## Estrutura de Menus

### Portal Gestor (/gestor/)
```
Cadastros
├── Grupos de Produtos
├── Subgrupos de Produtos
├── Materias-Primas (-> producao)
├── Produtos Intermediarios (-> producao)
├── Produtos Acabados
├── Fornecedores
├── Clientes
├── Locais de Estoque
├── Tipos Mov. Entrada
└── Tipos Mov. Saida

Estoque
├── Entradas
├── Saidas
├── Posicao Estoque
├── Ajustes (pendente)
└── Ordens de Producao (FASE 4)
```

### Portal Producao (/producao/)
```
Suprimentos
├── Requisicao de Compra
├── Orcamento de Compra
├── Pedido de Compra
├── Saldo Requisicao
├── Fornecedores
└── Relatorio Produtos
```

---

## Modelos Principais

### Estoque (core/models/estoque.py)
- LocalEstoque
- TipoMovimentoEntrada
- TipoMovimentoSaida
- MovimentoEntrada + ItemMovimentoEntrada
- MovimentoSaida + ItemMovimentoSaida
- OrdemProducao (FASE 4)
- ItemConsumoOP (FASE 4)

### Produtos (core/models/produtos.py)
- GrupoProduto
- SubgrupoProduto
- Produto (tipo: MP, PI, PA)
- EstruturaProduto (componentes)

---

## Proximos Passos

1. **FASE 3 - Ajustes**
   - Inventario fisico (contagem e ajuste)
   - Transferencias entre locais
   - Ajustes manuais (quebra, perda, bonificacao)

2. **FASE 5 - Integracoes**
   - Pedido Compra -> Entrada Estoque automatica
   - Custo medio automatico na entrada

3. **Melhorias Futuras**
   - Controle de acesso por nivel (atualmente aberto)
   - Relatorios avancados (Kardex, Curva ABC)
   - Dashboard de producao

---

## Anotacoes Tecnicas

### Geracao de Codigo Automatico
- Produtos: GG.SS.NNNNN (grupo.subgrupo.sequencial)
- Movimentos Entrada: ENT-AAMM0001
- Movimentos Saida: SAI-AAMM0001
- Ordens Producao: OP-AAMM0001

### Sistema de Custos
- MP: custo_medio (atualizado na entrada)
- PI: custo_material + custo_servico = custo_total (calculado da estrutura)
- PA: custo_material + custo_servico = custo_total

### Workflow de OP
```
RASCUNHO -> LIBERADA -> EM_PRODUCAO -> CONCLUIDA
                    \-> CANCELADA
```

---

*Ultima atualizacao: 2025-12-07*
*FASE 4 (Ordens de Producao) concluida nesta data*
