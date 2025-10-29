# 📊 Análise do Sistema - Workflow de Projetos FUZA

**Data:** 2025-10-28
**Objetivo:** Mapear o sistema atual e identificar o que precisa ser implementado para o sistema de workflow/tarefas

---

## 🔍 O QUE JÁ EXISTE

### ✅ **1. Modelo Proposta (core/models/propostas.py)**

**Arquivo:** 1133 linhas - modelo MUITO completo

**Status disponíveis:**
```python
STATUS_CHOICES = [
    ('rascunho', 'Rascunho'),
    ('aprovado', 'Aprovado'),
    ('rejeitado', 'Rejeitado'),
]
```

**Campos relacionados a vistoria:**
- `status_obra` - Status da obra ('', 'medicao_ok', 'em_vistoria', 'obra_ok')
- `data_vistoria_medicao` - Data da primeira vistoria
- `data_proxima_vistoria` - Próxima vistoria agendada
- `data_aprovacao` - Quando foi aprovada

**Métodos/Properties relacionados:**
- `pode_agendar_vistoria` → True se status == 'aprovado'
- `status_obra_badge_class` → Classes CSS para badges
- `proxima_vistoria_vencida` → Verifica se vistoria atrasou
- `dias_proxima_vistoria` → Quantos dias faltam
- `percentual_conclusao` → % de preenchimento da proposta

**Permissões já implementadas:**
- ✅ aprovar_proposta
- ✅ rejeitar_proposta
- ✅ realizar_vistoria
- ✅ agendar_vistoria
- ✅ aprovar_medicao

---

### ✅ **2. Modelo VistoriaHistorico (core/models/propostas2.py)**

**Modelo COMPLETO para rastreio de vistorias**

```python
class VistoriaHistorico(models.Model):
    proposta = ForeignKey(Proposta, related_name='vistorias')
    responsavel = ForeignKey(Usuario)

    # Datas
    data_agendada = DateField()
    data_realizada = DateField(null=True)

    # Tipo
    tipo_vistoria = CharField(choices=[
        ('medicao', 'Medição Inicial'),
        ('acompanhamento', 'Acompanhamento'),
        ('obra_pronta', 'Obra Pronta'),
        ('entrega', 'Entrega'),
    ])

    # Status
    status = CharField(choices=[
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('reagendada', 'Reagendada'),
    ])
```

**Já existe histórico completo de vistorias!** ✅

---

### ✅ **3. Modelo AnexoProposta (core/models/propostas2.py)**

**Sistema de UPLOAD de arquivos já implementado!**

```python
class AnexoProposta(models.Model):
    proposta = ForeignKey(Proposta, related_name='anexos')
    nome = CharField(max_length=200)
    tipo = CharField(choices=[
        ('orcamento', 'Orçamento'),
        ('demonstrativo', 'Demonstrativo de Cálculo'),
        ('contrato', 'Contrato'),
        ('projeto', 'Projeto Técnico'),  ← JÁ TEM!
        ('foto', 'Foto'),
        ('documento', 'Documento'),
        ('outro', 'Outro'),
    ])
    arquivo = FileField(upload_to='propostas/anexos/%Y/%m/')
    tamanho = PositiveIntegerField()
    observacoes = TextField()

    enviado_por = ForeignKey(Usuario)
    enviado_em = DateTimeField(auto_now_add=True)
```

**Já existe sistema de anexos com tipo 'projeto'!** ✅

---

### ✅ **4. Fluxo de Produção**

**Arquivo:** `core/models/producao.py`

**Fluxo já implementado:**
```
Proposta (aprovada)
   ↓
ListaMateriais (calculando → em_edicao → aprovada)
   ↓
RequisicaoCompra (rascunho → aprovado → confirmado → parcial → recebido)
   ↓
OrcamentoCompra (rascunho → cotando → cotado → analise → aprovado)
```

**Modelos existentes:**
- ✅ ListaMateriais (1-para-1 com Proposta)
- ✅ ItemListaMateriais
- ✅ RequisicaoCompra
- ✅ ItemRequisicaoCompra
- ✅ OrcamentoCompra
- ✅ ItemOrcamentoCompra
- ✅ HistoricoOrcamentoCompra

**Permissões já implementadas:**
- ✅ aprovar_lista_materiais
- ✅ editar_lista_materiais_aprovada
- ✅ visualizar_custos_lista
- ✅ aprovar_requisicao
- ✅ cancelar_requisicao
- ✅ aprovar_orcamento_ate_5000/10000/50000

**Status tracking já existe!** ✅

---

### ✅ **5. Dashboards Existentes**

**Vendedor Dashboard** (`vendedor/views/dashboard.py`)
- Básico, sem estatísticas
- Apenas redireciona

**Produção Dashboard** (`producao/views/dashboard.py`)
- ✅ Estatísticas de produtos (MP, PI, PA)
- ✅ Estatísticas de fornecedores
- ✅ Produtos com estoque baixo
- ✅ Produtos indisponíveis
- ❌ NÃO mostra propostas/projetos em andamento

**Gestor Dashboard** (`gestor/views.py`)
- ✅ Total de usuários
- ✅ Total de produtos
- ✅ Total de fornecedores
- ✅ Produtos sem estoque
- ❌ NÃO mostra propostas/projetos

---

### ✅ **6. Sistema de Permissões**

**Já implementado:**
- ✅ 8 níveis de usuário
- ✅ 8 grupos com permissões padrão
- ✅ Sistema automático de atribuição
- ✅ Middleware de controle de acesso aos portais
- ✅ Decorators para views
- ✅ Permissões customizadas (26 no total)

---

## ❌ O QUE FALTA IMPLEMENTAR

### 1. **Campo de Etapa/Stage na Proposta**

**Atualmente:**
- Proposta tem apenas `status` ('rascunho', 'aprovado', 'rejeitado')
- Não tem campo de "etapa atual do processo"

**Precisa:**
```python
etapa_atual = CharField(choices=[
    ('proposta', 'Proposta em Análise'),
    ('vistoria', 'Aguardando Vistoria'),
    ('projeto_executivo', 'Aguardando Projeto Executivo'),
    ('lista_materiais', 'Aguardando Lista de Materiais'),
    ('compras', 'Em Processo de Compras'),
    ('fabricacao', 'Em Fabricação'),
    ('instalacao', 'Aguardando Instalação'),
    ('entregue', 'Entregue'),
])
```

---

### 2. **Modelo Tarefa (NOVO)**

**Não existe sistema de tarefas!**

Precisa criar:
```python
class Tarefa(models.Model):
    proposta = ForeignKey(Proposta)
    tipo = CharField(...)  # vistoria, projeto_executivo, etc
    titulo = CharField()
    descricao = TextField()

    status = CharField()  # pendente, em_andamento, concluida
    perfis_responsaveis = JSONField()  # ['engenharia', 'admin']
    usuario_responsavel = ForeignKey(Usuario, null=True)

    prazo_dias = IntegerField()
    data_criacao = DateTimeField()
    data_conclusao = DateTimeField(null=True)
    prioridade = CharField()  # baixa, normal, alta, urgente
```

---

### 3. **Dashboards com Tarefas Pendentes**

**Atualmente:** Dashboards mostram estatísticas de produtos/fornecedores

**Precisa:**
- Dashboard do Vendedor → Mostrar propostas aguardando vistoria
- Dashboard de Engenharia → Mostrar propostas aguardando projeto executivo
- Dashboard de Produção → Mostrar propostas aguardando lista de materiais
- Dashboard Admin → Visão completa de todas as etapas

**Exemplo:**
```
┌──────────────────────────────────┐
│ ⚠️ Tarefas Urgentes (3)          │
│ - Projeto Executivo #25001       │
│   Prazo: Vencido há 2 dias       │
│ - Vistoria #25003                │
│   Prazo: Vence hoje              │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ 📋 Minhas Tarefas (8)            │
│ - Lista Materiais #25004         │
│   Prazo: 3 dias                  │
│ - Upload Projeto #25005          │
│   Prazo: 5 dias                  │
└──────────────────────────────────┘
```

---

### 4. **Views de Tarefas**

Precisa criar:
```
/vendedor/tarefas/          # Lista tarefas do vendedor
/engenharia/tarefas/        # Lista tarefas de engenharia
/producao/tarefas/          # Lista tarefas de produção
/gestor/tarefas/            # Admin vê todas
```

---

### 5. **Automação de Criação de Tarefas**

**Não existe automação!**

Precisa implementar:
- Quando proposta aprovada → Criar tarefa de vistoria
- Quando vistoria concluída → Criar tarefa de projeto executivo
- Quando projeto executivo enviado → Criar tarefa de lista de materiais
- Quando lista aprovada → Criar tarefa de compras
- E assim por diante...

**Service sugerido:** `core/services/workflow.py`

---

### 6. **Badges de Notificação nos Menus**

**Não existe!**

Precisa adicionar:
```html
<a href="/vendedor/tarefas/">
    Minhas Tarefas <span class="badge bg-danger">3</span>
</a>
```

---

### 7. **Timeline/Histórico do Projeto**

**Não existe visão consolidada!**

Precisa criar view que mostre:
- ✅ Proposta criada em 01/10
- ✅ Proposta aprovada em 05/10
- ✅ Vistoria realizada em 10/10
- ⏳ Aguardando projeto executivo (há 5 dias)
- ⏹️ Lista de materiais (não iniciado)
- ⏹️ Compras (não iniciado)
- ⏹️ Fabricação (não iniciado)
- ⏹️ Instalação (não iniciado)
- ⏹️ Entrega (não iniciado)

---

### 8. **Filtros por Perfil de Usuário**

**Não implementado!**

Cada perfil deve ver apenas suas etapas:

| Perfil | Etapas Visíveis |
|--------|----------------|
| Vendedor | proposta → vistoria |
| Vistoria | vistoria |
| Engenharia | projeto_executivo → lista_materiais |
| Produção | lista_materiais → fabricacao |
| Compras | compras |
| Admin | TODAS |

---

### 9. **Views de Upload Específicas**

**AnexoProposta existe, mas falta views específicas!**

Precisa criar:
```
/engenharia/projeto/<id>/upload/      # Upload projeto executivo
/vendedor/vistoria/<id>/upload/       # Upload relatório vistoria
/producao/documento/<id>/upload/      # Upload docs de fabricação
```

---

### 10. **Recálculo de Tarefas**

**Não existe!**

Precisa implementar:
- Comando ou botão para "Recalcular tarefas"
- Verificar status de cada proposta
- Criar tarefas pendentes automaticamente
- Marcar como concluída se condição satisfeita

---

## 📋 FLUXO COMPLETO MAPEADO

### **Etapa 1: VENDAS**
```
Proposta (rascunho)
   ↓ [vendedor cria e preenche]
Proposta (aprovado)
   ↓ [gestor/admin aprova]
Agendar Vistoria
   ↓ [vendedor/vistoria agenda]
Realizar Vistoria
   ↓ [vistoria realiza e registra no VistoriaHistorico]
Status Obra = medicao_ok
```

**Modelos envolvidos:**
- ✅ Proposta
- ✅ VistoriaHistorico
- ❌ Tarefa (FALTA)

---

### **Etapa 2: ENGENHARIA**
```
Aguardando Projeto Executivo
   ↓ [engenharia elabora]
Upload Projeto Executivo
   ↓ [engenharia faz upload no AnexoProposta tipo='projeto']
Projeto Aprovado
```

**Modelos envolvidos:**
- ✅ AnexoProposta
- ❌ Tarefa (FALTA)
- ❌ Campo etapa_atual (FALTA)

---

### **Etapa 3: PRODUÇÃO**
```
Criar Lista de Materiais
   ↓ [produção/engenharia cria]
ListaMateriais (calculando → em_edicao)
   ↓ [ajusta quantidades]
ListaMateriais (aprovada)
   ↓ [gestor/engenharia aprova]
Criar Requisição de Compra
   ↓ [produção cria]
RequisicaoCompra (aprovada)
```

**Modelos envolvidos:**
- ✅ ListaMateriais
- ✅ ItemListaMateriais
- ✅ RequisicaoCompra
- ❌ Tarefa (FALTA)

---

### **Etapa 4: COMPRAS**
```
Criar Orçamento de Compra
   ↓ [compras cria]
OrcamentoCompra (cotando)
   ↓ [cotações com fornecedores]
OrcamentoCompra (aprovado)
   ↓ [gestor aprova]
Realizar Pedido
```

**Modelos envolvidos:**
- ✅ OrcamentoCompra
- ✅ ItemOrcamentoCompra
- ❌ Tarefa (FALTA)

---

### **Etapa 5: FABRICAÇÃO**
```
Materiais Recebidos
   ↓
Em Fabricação
   ↓
Produtos Prontos
```

**Modelos envolvidos:**
- ❌ NÃO TEM MODELO ESPECÍFICO
- ❌ Tarefa (FALTA)

---

### **Etapa 6: INSTALAÇÃO**
```
Agendar Instalação
   ↓
Instalar Elevador
   ↓
Testes e Ajustes
```

**Modelos envolvidos:**
- ❌ NÃO TEM MODELO ESPECÍFICO
- ❌ Pode usar VistoriaHistorico tipo='entrega'

---

### **Etapa 7: ENTREGA**
```
Entrega ao Cliente
   ↓
Upload Termo de Entrega
   ↓
Proposta (entregue)
```

**Modelos envolvidos:**
- ✅ AnexoProposta tipo='documento'
- ❌ Campo etapa_atual = 'entregue' (FALTA)

---

## 🎯 RESUMO: O QUE PRECISA SER FEITO

### **Prioridade 1 - Core do Sistema**
1. ✅ Adicionar campo `etapa_atual` na Proposta
2. ✅ Criar modelo `Tarefa`
3. ✅ Criar service `workflow.py` para automação
4. ✅ Criar comando de recálculo de tarefas

### **Prioridade 2 - Dashboards**
5. ✅ Refatorar dashboards para mostrar propostas/tarefas
6. ✅ Criar dashboard de tarefas por perfil
7. ✅ Adicionar badges de notificação nos menus
8. ✅ Criar timeline/histórico do projeto

### **Prioridade 3 - Views**
9. ✅ Criar views de upload específicas
10. ✅ Criar views de listagem de tarefas
11. ✅ Criar view de detalhes da tarefa
12. ✅ Implementar filtros por perfil

### **Prioridade 4 - UX**
13. ✅ Cards de tarefas urgentes
14. ✅ Alertas de prazos vencidos
15. ✅ Notificações visuais
16. ✅ Timeline visual do projeto

---

## 💡 RECOMENDAÇÕES

### **Abordagem Sugerida: INCREMENTAL**

**Fase 1: Core (1-2 dias)**
- Adicionar campo `etapa_atual` à Proposta
- Criar modelo Tarefa
- Criar migration
- Criar service de workflow básico

**Fase 2: Automação (1 dia)**
- Implementar gatilhos de criação automática
- Signal quando proposta aprovada
- Signal quando upload de arquivo
- Comando de recálculo

**Fase 3: Dashboards (1-2 dias)**
- Refatorar dashboards existentes
- Adicionar listagem de tarefas
- Badges de notificação
- Cards de urgência

**Fase 4: Views (1 dia)**
- Views de upload específicas
- Views de listagem de tarefas
- Timeline do projeto

---

## ⚙️ ARQUITETURA SUGERIDA

```
core/
├── models/
│   ├── propostas.py         # Adicionar campo etapa_atual
│   ├── tarefas.py          # NOVO - Modelo Tarefa
│   └── propostas2.py        # Já tem AnexoProposta e VistoriaHistorico
│
├── services/
│   └── workflow.py          # NOVO - Lógica de automação
│
├── management/commands/
│   └── recalcular_tarefas.py  # NOVO - Comando recálculo
│
└── signals.py               # Adicionar signals de workflow

vendedor/views/
├── dashboard.py             # Refatorar - mostrar tarefas
└── tarefas.py              # NOVO - Views de tarefas

producao/views/
├── dashboard.py             # Refatorar - mostrar tarefas
└── tarefas.py              # NOVO - Views de tarefas

gestor/views.py              # Adicionar timeline de projeto
```

---

## 📊 DADOS NECESSÁRIOS DO USUÁRIO

Antes de implementar, precisamos confirmar:

1. **Quais são TODAS as etapas do processo?** (para definir choices de etapa_atual)
2. **Quais documentos devem ser uploadados em cada etapa?**
3. **Quais são os prazos padrão para cada tarefa?**
4. **Quem é responsável por cada etapa?** (perfis)
5. **Existe etapa de fabricação/instalação que precisa de modelo específico?**
6. **Como é o processo de entrega ao cliente?**

---

**Análise concluída! Aguardando suas respostas para prosseguir com a implementação.** ✅
