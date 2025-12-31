# Memória de Contexto - Fuza Elevadores

## Última Atualização
**Data:** 2025-12-31

---

## COMANDOS IMPORTANTES

### Docker - Build e Push (Multi-plataforma)
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t joseantoniopaiva/fuza:latest --push .
```

### Git - Commit e Push
```bash
git add .
git commit -m "Descrição das alterações"
git push origin main
```

---

## ONDE PARAMOS

### Última Sessão (2025-12-31)
**Status:** Concluído com sucesso

**O que foi feito:**
1. **Página "Fórmulas de Cálculo"** - Criada documentação completa do fluxo de cálculo em 5 etapas
2. **Validação YAML corrigida** - Alinhado critério (`utilizado=True, status='ATIVO'`)
3. **Produtos atualizados** - 8 produtos marcados como utilizados/ativos
4. **Produtos criados** - 4 novos: 01.04.00009, 01.04.00013, 03.01.00004, 03.01.00005
5. **Botão calcular** - Sempre visível na lista de propostas do vendedor
6. **Link no vendedor** - Acesso às Fórmulas de Cálculo com botão "Voltar" inteligente

### Próxima Ação
**Migração gradual MP → PI** - Substituir produtos Matéria Prima por Produto Intermediário conforme estruturas forem construídas.

---

## Sobre o Projeto
- **Nome:** Sistema Elevadores Fuza
- **Framework:** Django (Python 3.13)
- **Banco de Dados:** PostgreSQL
- **Status:** Funcionando em desenvolvimento

## Estrutura de Apps
| App | Descrição |
|-----|-----------|
| `core` | Models principais (Produto, Proposta, Parâmetros) |
| `vendedor` | Portal de vendas e simulações |
| `gestor` | Painel do gestor |
| `producao` | Controle de produção |

---

## ESTRUTURA DE PREÇOS (Mapeamento Completo)

### Modelo Produto (`core/models/produtos.py`)
```
Campos de Custo:
- custo_material (Decimal) - Custo de materiais/componentes
- custo_servico (Decimal) - Custo de mão de obra/serviços
- custo_total (property) - custo_material + custo_servico

Campos de Preço:
- preco_venda (Decimal) - Preço de venda padrão
- margem_padrao (Decimal) - Margem padrão (%)
```

### Produtos Intermediários (PI)
- Tipos: `MONTADO_INTERNO` e `MONTADO_EXTERNO`
- Usam **EstruturaProduto** para definir componentes
- Campo `formula_quantidade` para fórmulas dinâmicas
- **Recalculam custos automaticamente** ao salvar

### EstruturaProduto (`core/models/produtos.py`)
```
- produto_pai: FK para PI ou PA
- produto_filho: FK para MP, PI ou PA
- quantidade: Decimal
- formula_quantidade: TextField (FÓRMULAS DINÂMICAS!)
- percentual_perda: Decimal (default=0)
- quantidade_com_perda (property): quantidade * (1 + percentual_perda/100)
- custo_total_componente (property): custo_unitario * quantidade_com_perda
```

### Parametrização (`core/models/parametros.py`)
```
ParametrosGerais:
- percentual_mao_obra: 15% (MOD)
- percentual_indiretos_fabricacao: 5%
- percentual_instalacao: 5%
- margem_padrao: 30%
- comissao_padrao: 3%
- desconto_alcada_1, desconto_alcada_2: Alçadas de desconto

Impostos Dinâmicos (por tipo de faturamento):
- faturamento_elevadores: 10%
- faturamento_fuza: 8%
- faturamento_manutencao: 5%
```

### Motor de Regras YAML (`core/models/regras_yaml.py`)
```
RegraYAML:
- tipo: CABINE | CARRINHO | TRACAO | SISTEMAS
- conteudo_yaml: TextField com regras de cálculo
- Valida códigos de produtos contra a base (utilizado=True, status='ATIVO')
```

### Serviços de Cálculo
```
core/services/pricing.py:
- FormacaoPreco: Aplica margem + comissão + impostos

core/services/calculo_pedido.py:
- CalculoPedidoService: Orquestração principal do cálculo

core/services/calculo_pedido_yaml.py:
- CalculoPedidoYAMLService: Motor de regras YAML

vendedor/views/pricing_engine.py:
- calcular_precos(): Margem/comissão/impostos por dentro (gross-up)
```

### Fluxo de Cálculo de Preço (5 Etapas)
```
1. ESPECIFICAÇÕES DO ELEVADOR
   └─> Cliente, modelo, capacidade, cabine, portas, etc.

2. DIMENSIONAMENTO (Regras YAML)
   ├─> 2.1 CABINE
   ├─> 2.2 CARRINHO
   ├─> 2.3 TRAÇÃO
   └─> 2.4 SISTEMAS

3. CUSTOS VIA YAML
   └─> Soma de código_produto * quantidade

4. CUSTOS INDIRETOS
   ├─> MOD: 15% sobre custos diretos
   ├─> Indiretos Fabricação: 5%
   └─> Instalação: 5%
   = CUSTO DE PRODUÇÃO

5. FORMAÇÃO DE PREÇO
   ├─> Margem: 30% sobre custo_total_projeto
   ├─> Comissão: 3% sobre preco_com_margem
   └─> Impostos: Dinâmicos (baseado em faturado_por)
   = PREÇO DE VENDA CALCULADO
```

---

## Arquivos Principais

### Preços e Cálculos
| Arquivo | Descrição |
|---------|-----------|
| `core/models/produtos.py` | Produto, EstruturaProduto, Grupos |
| `core/models/propostas.py` | Proposta com formação de preço |
| `core/models/parametros.py` | ParametrosGerais (margens, impostos) |
| `core/models/regras_yaml.py` | RegraYAML (cabine, carrinho, etc.) |
| `core/services/pricing.py` | FormacaoPreco |
| `core/services/calculo_pedido.py` | CalculoPedidoService |
| `core/services/calculo_pedido_yaml.py` | Motor YAML |
| `vendedor/views/acoes.py` | View proposta_calcular |
| `vendedor/views/apis.py` | APIs AJAX de preço |

### Templates Importantes
| Arquivo | Descrição |
|---------|-----------|
| `templates/vendedor/proposta_step3.html` | Interface de cálculo |
| `templates/vendedor/proposta_list.html` | Lista de propostas (botão calcular) |
| `templates/producao/formulas_calculo.html` | Documentação das fórmulas |
| `templates/vendedor/base_vendedor.html` | Menu vendedor |
| `templates/producao/base_producao.html` | Menu produção |

---

## Histórico de Conversas

### Sessão 2025-12-31
**Ações realizadas:**
1. Criada página "Fórmulas de Cálculo" com documentação do fluxo de 5 etapas
2. Corrigida inconsistência na validação YAML (usar mesmo critério do cálculo)
3. Atualizados 8 produtos para utilizado=True, status='ATIVO'
4. Criados 4 produtos faltantes: 01.04.00009, 01.04.00013, 03.01.00004, 03.01.00005
5. Botão calcular sempre visível na lista de propostas
6. Link para Fórmulas de Cálculo no menu vendedor com volta inteligente

**Status:** Todas as 4 regras YAML validando corretamente

### Sessão 2025-12-26
**Ações realizadas:**
1. Verificação geral do projeto - OK
2. Mapeamento completo da estrutura de preços
3. Identificação do fluxo de cálculo
4. Documentação dos arquivos relevantes

---

## Notas Técnicas
- URLs `configuracao/` e `api/` estão comentadas em `urls.py`
- DEBUG=True (ambiente de desenvolvimento)
- Logs configurados em `/logs/`
- Sem testes automatizados
