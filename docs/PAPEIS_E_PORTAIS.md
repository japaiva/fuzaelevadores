# Sistema de Papéis e Acesso aos Portais

## Visão Geral

O sistema usa **papéis (níveis)** para determinar a qual portal cada usuário tem acesso. É um sistema híbrido que combina:

1. **Nível do usuário** (`nivel`) → Determina acesso aos portais
2. **Grupo Django** → Atribuído automaticamente baseado no nível
3. **Permissões** → Gerenciadas pelo grupo

---

## 1. Papéis Disponíveis (9 níveis)

```python
NIVEL_USUARIO_CHOICES = [
    ('admin', 'Admin'),
    ('gestor', 'Gestor'),
    ('vendedor', 'Vendedor'),
    ('compras', 'Compras'),
    ('engenharia', 'Engenharia'),
    ('financeiro', 'Financeiro'),
    ('vistoria', 'Vistoria'),
    ('producao', 'Produção'),
    ('almoxarifado', 'Almoxarifado'),
]
```

---

## 2. Portais do Sistema (3 principais)

### Portal Vendedor (`/vendedor/`)
- **Cor:** Verde (success)
- **Função:** Criar simulações, propostas, acompanhar clientes
- **Acesso:** vendedor, engenharia, vistoria, gestor, admin

### Portal Produção (`/producao/`)
- **Cor:** Azul (info)
- **Função:** Compras, requisições, listas de materiais, fornecedores, tarefas
- **Acesso:** producao, compras, engenharia, almoxarifado, gestor, admin

### Portal Gestor (`/gestor/`)
- **Cor:** Azul escuro (primary)
- **Função:** Visão completa, relatórios, aprovações, gestão geral
- **Acesso:** gestor, financeiro, admin

### Configurações (`/configuracao/`)
- **Cor:** Amarelo (warning)
- **Função:** Configurações do sistema
- **Acesso:** gestor, admin

---

## 3. Matriz de Acesso Papel × Portal

| Papel          | Portal Vendedor | Portal Produção | Portal Gestor | Configurações |
|----------------|-----------------|-----------------|---------------|---------------|
| **Admin**      | ✅              | ✅              | ✅            | ✅            |
| **Gestor**     | ✅              | ✅              | ✅            | ✅            |
| **Vendedor**   | ✅              | ❌              | ❌            | ❌            |
| **Compras**    | ❌              | ✅              | ❌            | ❌            |
| **Engenharia** | ✅              | ✅              | ❌            | ❌            |
| **Financeiro** | ❌              | ❌              | ✅            | ❌            |
| **Vistoria**   | ✅              | ❌              | ❌            | ❌            |
| **Produção**   | ❌              | ✅              | ❌            | ❌            |
| **Almoxarifado** | ❌            | ✅              | ❌            | ❌            |

---

## 4. Como Funciona na Prática

### Quando um usuário é criado/atualizado:

1. **Você define o nível** (ex: `nivel='engenharia'`)
2. **Signal automático** (`core/signals.py`) adiciona ao grupo Django correspondente:
   - `nivel='engenharia'` → Grupo `'Engenharia'`
   - `nivel='producao'` → Grupo `'Producao'`
3. **Grupo já tem permissões** configuradas via `setup_permissoes.py`

### Quando o usuário acessa uma URL:

1. **Middleware** (`PermissaoPortalMiddleware`) verifica o caminho
2. Compara o `nivel` do usuário com a lista permitida
3. Bloqueia ou permite o acesso

**Exemplo:**
```python
# Usuário com nivel='compras' tenta acessar /vendedor/clientes/
# Middleware verifica:
# - '/vendedor/' exige nivel em ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria']
# - 'compras' NÃO está na lista
# - BLOQUEADO ❌
```

---

## 5. Mapeamento Nível → Grupo

```python
NIVEL_TO_GROUP = {
    'admin': 'Admin',
    'gestor': 'Gestor',
    'vendedor': 'Vendedor',
    'financeiro': 'Financeiro',
    'vistoria': 'Vistoria',
    'producao': 'Producao',     # SEM acento
    'compras': 'Compras',
    'engenharia': 'Engenharia',
    'almoxarifado': 'Almoxarifado',
}
```

**Importante:** O grupo é sempre **sem acento** (`Producao`), mas o label exibido é "Produção".

---

## 6. Código de Controle de Acesso

### Middleware (`fuza_elevadores/middleware.py:157-200`)

```python
portal_permissions = {
    '/gestor/': ['admin', 'gestor', 'financeiro'],
    '/vendedor/': ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria'],
    '/producao/': ['admin', 'gestor', 'producao', 'compras', 'engenharia', 'almoxarifado'],
    '/configuracao/': ['admin', 'gestor'],
}
```

Se o usuário não tiver o nível permitido, recebe **403 Forbidden**.

---

## 7. Exemplos Práticos

### Exemplo 1: Vendedor
- **Nível:** `vendedor`
- **Grupo:** `Vendedor`
- **Acesso:**
  - ✅ `/vendedor/` - Pode criar simulações, propostas
  - ❌ `/producao/` - NÃO pode ver compras/fornecedores
  - ❌ `/gestor/` - NÃO pode ver relatórios gerenciais

### Exemplo 2: Engenharia
- **Nível:** `engenharia`
- **Grupo:** `Engenharia`
- **Acesso:**
  - ✅ `/vendedor/` - Pode ver propostas, acompanhar projetos
  - ✅ `/producao/` - Pode ver listas de materiais, requisições, **TAREFAS**
  - ❌ `/gestor/` - NÃO pode ver relatórios gerenciais

### Exemplo 3: Compras
- **Nível:** `compras`
- **Grupo:** `Compras`
- **Acesso:**
  - ❌ `/vendedor/` - NÃO pode criar propostas
  - ✅ `/producao/` - Pode gerenciar fornecedores, criar pedidos, requisições
  - ❌ `/gestor/` - NÃO pode ver relatórios gerenciais

### Exemplo 4: Gestor
- **Nível:** `gestor`
- **Grupo:** `Gestor`
- **Acesso:**
  - ✅ `/vendedor/` - Pode ver e aprovar propostas
  - ✅ `/producao/` - Pode acompanhar toda produção
  - ✅ `/gestor/` - Acesso completo a relatórios e métricas
  - ✅ `/configuracao/` - Pode alterar configurações

---

## 8. Sistema de Tarefas (Workflow)

### Quem vê as tarefas?

As tarefas aparecem no **Portal Produção** (`/producao/`) no menu **Adm → Tarefas**.

**Filtro de visibilidade:**
- Usuário vê tarefas onde:
  - `grupo_destino` está nos grupos do usuário **OU**
  - `usuario_destino` é o próprio usuário

**Exemplo:**
- Proposta aprovada → Cria tarefa com `grupo_destino='Engenharia'`
- Todos os usuários do grupo **Engenharia** veem a tarefa
- Outros grupos **não veem** a tarefa

---

## 9. Resumo: Qual papel tem acesso a qual módulo?

### Vendas (Portal Vendedor)
- Vendedor, Engenharia, Vistoria, Gestor, Admin

### Produção (Portal Produção)
- Produção, Compras, Engenharia, Almoxarifado, Gestor, Admin

### Gestão (Portal Gestor)
- Gestor, Financeiro, Admin

### Configurações
- Gestor, Admin

---

## 10. Recomendações

### Para simplificar, considere:

1. **3 perfis principais:**
   - **Comercial** → Acessa Vendedor
   - **Operações** → Acessa Produção
   - **Gestão** → Acessa tudo

2. **Níveis especializados** dentro de cada perfil:
   - Comercial: vendedor, vistoria, engenharia
   - Operações: producao, compras, almoxarifado, engenharia
   - Gestão: gestor, financeiro, admin

3. **Engenharia é ponte:** Acessa Vendedor E Produção
   - Vê propostas no Vendedor
   - Recebe tarefas na Produção
   - Faz ligação entre comercial e operações

---

## 11. Próximos Passos

Para implementar o "Painel de Projetos" que você mencionou:

1. **Dashboard unificado no Portal Gestor** (visão completa)
2. **Widget de propostas no Portal Vendedor** (apenas status comercial)
3. **Widget de tarefas no Portal Produção** (apenas execução)

Cada portal mostra **apenas o relevante** para aquele nível.

---

**Arquivo:** `fuza_elevadores/middleware.py:157` (controle de acesso)
**Arquivo:** `core/signals.py:17` (mapeamento nivel → grupo)
**Arquivo:** `core/models/base.py:54` (definição dos níveis)
