# Sistema de Permissões - FUZA Elevadores

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Níveis de Usuário](#níveis-de-usuário)
3. [Grupos de Permissões](#grupos-de-permissões)
4. [Permissões Customizadas](#permissões-customizadas)
5. [Como Usar](#como-usar)
6. [API e Decorators](#api-e-decorators)
7. [Configuração Inicial](#configuração-inicial)
8. [Troubleshooting](#troubleshooting)

---

## Visão Geral

O sistema de permissões do FUZA usa uma **abordagem híbrida**:

```
┌──────────────────────────────────────────────────┐
│ 1. Nível de Usuário (nivel)                     │
│    → Define qual PORTAL pode acessar            │
│                                                  │
│ 2. Grupo Django                                 │
│    → Permissões PADRÃO do tipo de usuário      │
│                                                  │
│ 3. Permissões Individuais                       │
│    → Customizações ESPECÍFICAS por usuário      │
└──────────────────────────────────────────────────┘
```

### Vantagens:
- ✅ **Flexível**: Customize permissões por usuário quando necessário
- ✅ **Escalável**: A maioria dos usuários usa permissões padrão do grupo
- ✅ **Automático**: Usuários são adicionados aos grupos automaticamente
- ✅ **Granular**: Controle fino sobre ações específicas (ex: aprovar 5% vs 10% desconto)

---

## Níveis de Usuário

**Arquivo:** `core/models/base.py`

| Nível | Descrição | Acessa Portais |
|-------|-----------|----------------|
| `admin` | Administrador do sistema | Todos |
| `gestor` | Gerente/gestor | `/gestor/`, `/configuracao/` |
| `vendedor` | Vendedor | `/vendedor/` |
| `financeiro` | Financeiro | `/gestor/` |
| `vistoria` | Equipe de vistoria | `/vendedor/` |
| `producao` | Equipe de produção | `/producao/` |
| `compras` | Equipe de compras | `/producao/` |
| `engenharia` | Engenharia | `/vendedor/`, `/producao/` |

### Como o nível funciona:

1. **Middleware** (`fuza_elevadores/middleware.py`) bloqueia acesso aos portais baseado no nível
2. **LoginView** valida se o usuário pode fazer login no portal específico
3. **home_view** redireciona automaticamente para o dashboard correto

---

## Grupos de Permissões

Grupos são criados automaticamente com o comando `setup_permissoes`:

### Admin (214 permissões)
- ✅ **Acesso total** ao sistema
- Todas as permissões disponíveis

### Gestor (34 permissões)
**Propostas:**
- Criar, editar, excluir, visualizar propostas
- Aprovar descontos até 20%
- Visualizar custos e margens
- Visualizar propostas de outros vendedores
- Aprovar/rejeitar propostas
- Aprovar medições de obra

**Produção:**
- Aprovar listas de materiais
- Editar listas aprovadas
- Aprovar requisições e orçamentos (sem limite)

**Outros:**
- Gerenciar clientes e produtos

### Vendedor (11 permissões)
**Propostas:**
- Criar e editar propostas próprias
- Aprovar descontos até 5%
- Agendar vistorias
- Exportar relatórios

**Outros:**
- Visualizar e criar clientes
- Visualizar produtos

### Financeiro (8 permissões)
**Foco:** Visualização financeira e aprovações de valor

- Visualizar propostas com custos
- Visualizar propostas de todos vendedores
- Aprovar orçamentos até R$ 50.000
- Exportar relatórios

### Vistoria (6 permissões)
**Foco:** Vistoria e medição de obras

- Visualizar e editar propostas
- Realizar vistorias
- Agendar vistorias
- Aprovar medições de obra

### Produção (16 permissões)
**Foco:** Gestão de listas de materiais e requisições

- Visualizar propostas
- Gerenciar listas de materiais
- Aprovar listas de materiais
- Gerenciar requisições de compra
- Aprovar requisições
- Gerenciar e visualizar orçamentos
- Gerenciar produtos

### Compras (15 permissões)
**Foco:** Cotações e orçamentos

- Visualizar propostas e listas
- Gerenciar requisições (edição)
- **Gerenciar orçamentos** (foco principal)
- Aprovar orçamentos até R$ 10.000
- Cancelar orçamentos
- Gerenciar produtos e fornecedores

### Engenharia (14 permissões)
**Foco:** Visão técnica e custos

- Visualizar e editar propostas
- Visualizar custos e margens
- Visualizar propostas de todos
- Gerenciar listas de materiais
- Aprovar listas
- Editar listas aprovadas
- Gerenciar produtos

---

## Permissões Customizadas

### Propostas (core.Proposta)

**Descontos:**
- `aprovar_desconto_5` - Pode aprovar desconto até 5%
- `aprovar_desconto_10` - Pode aprovar desconto até 10%
- `aprovar_desconto_15` - Pode aprovar desconto até 15%
- `aprovar_desconto_20` - Pode aprovar desconto até 20%
- `aprovar_desconto_ilimitado` - Pode aprovar desconto ilimitado

**Visualização:**
- `visualizar_custos` - Pode visualizar custos e margens
- `visualizar_todas_propostas` - Pode ver propostas de outros vendedores
- `exportar_relatorios` - Pode exportar relatórios

**Edição:**
- `editar_proposta_alheia` - Pode editar propostas de outros
- `aprovar_proposta` - Pode aprovar propostas
- `rejeitar_proposta` - Pode rejeitar propostas

**Vistoria:**
- `realizar_vistoria` - Pode realizar vistorias
- `agendar_vistoria` - Pode agendar vistorias
- `aprovar_medicao` - Pode aprovar medições de obra

### Listas de Materiais (core.ListaMateriais)

- `aprovar_lista_materiais` - Pode aprovar lista de materiais
- `editar_lista_materiais_aprovada` - Pode editar lista já aprovada
- `visualizar_custos_lista` - Pode visualizar custos da lista

### Requisições de Compra (core.RequisicaoCompra)

- `aprovar_requisicao` - Pode aprovar requisições de compra
- `cancelar_requisicao` - Pode cancelar requisições
- `editar_requisicao_aprovada` - Pode editar requisições aprovadas

### Orçamentos de Compra (core.OrcamentoCompra)

- `aprovar_orcamento_ate_5000` - Pode aprovar até R$ 5.000
- `aprovar_orcamento_ate_10000` - Pode aprovar até R$ 10.000
- `aprovar_orcamento_ate_50000` - Pode aprovar até R$ 50.000
- `aprovar_orcamento_ilimitado` - Pode aprovar sem limite
- `cancelar_orcamento` - Pode cancelar orçamentos
- `editar_orcamento_aprovado` - Pode editar orçamentos aprovados

---

## Como Usar

### 1. Criar um Novo Usuário

```python
from core.models import Usuario

# O signal adiciona automaticamente ao grupo correto!
usuario = Usuario.objects.create(
    username='maria.silva',
    first_name='Maria',
    last_name='Silva',
    email='maria@empresa.com',
    nivel='vendedor',  # ← Automaticamente adicionado ao grupo "Vendedor"
)
usuario.set_password('senha123')
usuario.save()
```

### 2. Adicionar Permissão Individual

**Via Admin Django:**
```python
from django.contrib.auth.models import Permission

# Dar permissão de 10% para um vendedor específico
perm = Permission.objects.get(codename='aprovar_desconto_10')
usuario.user_permissions.add(perm)
```

**Via Interface Web:**
1. Acesse: Portal Gestor → Cadastros → Usuários
2. Clique no ícone de **chave** (🔑) ao lado do usuário
3. Marque as permissões desejadas
4. Salvar

### 3. Verificar Permissões no Código

**Em Views:**
```python
from core.utils.permissions import require_permission, require_nivel

# Exigir permissão específica
@require_permission('core.aprovar_desconto_10')
def aprovar_desconto(request, proposta_id):
    proposta = get_object_or_404(Proposta, id=proposta_id)
    # ... lógica ...

# Exigir nível de usuário
@require_nivel('admin', 'gestor')
def relatorio_gerencial(request):
    # ... lógica ...
```

**Em Templates:**
```django
{% if perms.core.aprovar_desconto_10 %}
    <button class="btn btn-primary">Aprovar até 10%</button>
{% endif %}

{% if perms.core.visualizar_custos %}
    <td>R$ {{ proposta.custo_total }}</td>
{% else %}
    <td>-</td>
{% endif %}
```

**Verificação Manual:**
```python
# Verificar se pode aprovar desconto de 8%
from core.utils.permissions import pode_aprovar_desconto

if pode_aprovar_desconto(request.user, 8.0):
    # Aprovar
    pass

# Verificar valor máximo
from core.utils.permissions import get_max_desconto_percentual

max_desc = get_max_desconto_percentual(request.user)  # 5.0, 10.0, 15.0...
```

### 4. Class-Based Views

```python
from django.views.generic import ListView
from core.utils.permissions import NivelRequiredMixin, PermissionRequiredMixin

class PropostaListView(NivelRequiredMixin, ListView):
    model = Proposta
    niveis_permitidos = ['admin', 'gestor', 'vendedor']

class AprovarPropostaView(PermissionRequiredMixin, UpdateView):
    model = Proposta
    permission_required = 'core.aprovar_proposta'
```

---

## API e Decorators

### Decorators para Function-Based Views

**Arquivo:** `core/utils/permissions.py`

#### `@require_nivel(*niveis)`
```python
@require_nivel('admin', 'gestor')
def minha_view(request):
    # Apenas admin e gestor podem acessar
    pass
```

#### `@require_permission(*permissions)`
```python
@require_permission('core.aprovar_proposta')
def aprovar(request, proposta_id):
    # Apenas quem tem a permissão pode acessar
    pass
```

#### `@require_any_permission(*permissions)`
```python
@require_any_permission('core.aprovar_desconto_5', 'core.aprovar_desconto_10')
def aprovar_desconto(request):
    # Precisa ter PELO MENOS UMA das permissões
    pass
```

### Mixins para Class-Based Views

#### `NivelRequiredMixin`
```python
class MinhaView(NivelRequiredMixin, View):
    niveis_permitidos = ['admin', 'gestor']
```

#### `PermissionRequiredMixin`
```python
class MinhaView(PermissionRequiredMixin, View):
    permission_required = 'core.aprovar_proposta'
    # ou múltiplas:
    permission_required = ['core.aprovar_proposta', 'core.visualizar_custos']
```

#### `AnyPermissionRequiredMixin`
```python
class MinhaView(AnyPermissionRequiredMixin, View):
    permissions_required = ['core.aprovar_desconto_5', 'core.aprovar_desconto_10']
```

### Helper Functions

**Arquivo:** `core/utils/permissions.py`

```python
from core.utils.permissions import (
    get_max_desconto_percentual,
    get_max_valor_orcamento,
    pode_aprovar_desconto,
    pode_aprovar_orcamento,
)

# Qual % máximo de desconto o usuário pode dar?
max_desc = get_max_desconto_percentual(request.user)  # 5.0, 10.0, 15.0, 20.0, 100.0

# Qual valor máximo de orçamento pode aprovar?
max_valor = get_max_valor_orcamento(request.user)  # 5000, 10000, 50000, None (ilimitado)

# Pode aprovar desconto específico?
if pode_aprovar_desconto(request.user, 7.5):
    # Sim, pode!
    pass

# Pode aprovar orçamento de R$ 8.000?
if pode_aprovar_orcamento(request.user, Decimal('8000.00')):
    # Sim, pode!
    pass
```

---

## Configuração Inicial

### 1. Executar Migrations

```bash
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 2. Criar Grupos e Permissões

```bash
python manage.py setup_permissoes
```

**Saída esperada:**
```
✓ Grupo Admin criado
  → 214 permissões atribuídas ao Admin
✓ Grupo Gestor criado
  → 34 permissões atribuídas ao Gestor
✓ Grupo Vendedor criado
  → 11 permissões atribuídas ao Vendedor
...
```

### 3. Criar Superusuário (Admin)

```bash
python manage.py createsuperuser --username admin --email admin@fuza.com
```

### 4. Testar o Sistema

1. Acesse: http://localhost:8000/gestor/login/
2. Login: admin / [sua senha]
3. Navegue: Cadastros → Usuários
4. Crie um novo usuário com nível "vendedor"
5. Clique no ícone 🔑 para gerenciar permissões

---

## Troubleshooting

### Problema: Usuário não tem permissões

**Verifique:**
1. O usuário está em algum grupo?
   ```python
   user.groups.all()  # Deve retornar grupos
   ```

2. O grupo tem permissões?
   ```python
   grupo = Group.objects.get(name='Vendedor')
   grupo.permissions.all()  # Deve ter permissões
   ```

3. Execute novamente o setup:
   ```bash
   python manage.py setup_permissoes
   ```

### Problema: Sinal não está funcionando

**Verifique se `core/apps.py` tem:**
```python
def ready(self):
    import core.signals  # ← Deve estar presente!
```

**Teste manualmente:**
```python
from core.models import Usuario
from django.contrib.auth.models import Group

usuario = Usuario.objects.get(username='teste')
grupo = Group.objects.get(name='Vendedor')
usuario.groups.add(grupo)
```

### Problema: Permissão não aparece

**Verifique se a migração foi aplicada:**
```bash
python manage.py showmigrations core
```

**Recrie as permissões:**
```bash
python manage.py migrate --run-syncdb
python manage.py setup_permissoes
```

### Problema: Middleware bloqueando acesso

**Verifique `fuza_elevadores/middleware.py`:**

```python
portal_permissions = {
    '/gestor/': ['admin', 'gestor', 'financeiro'],
    '/vendedor/': ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria'],
    '/producao/': ['admin', 'gestor', 'producao', 'compras', 'engenharia'],
    '/configuracao/': ['admin', 'gestor'],
}
```

---

## Referências

**Arquivos Importantes:**

| Arquivo | Descrição |
|---------|-----------|
| `core/models/base.py` | Definição dos níveis de usuário |
| `core/models/propostas.py` | Permissões de propostas |
| `core/models/producao.py` | Permissões de produção |
| `core/signals.py` | Adiciona usuários aos grupos automaticamente |
| `core/utils/permissions.py` | Decorators e helpers |
| `core/management/commands/setup_permissoes.py` | Comando de setup |
| `fuza_elevadores/middleware.py` | Controle de acesso aos portais |
| `gestor/views.py` | Views de gerenciamento de permissões |

**URLs de Gerenciamento:**
- `/gestor/usuarios/` - Lista de usuários
- `/gestor/usuarios/{id}/permissoes/` - Gerenciar permissões do usuário
- `/gestor/permissoes/grupos/` - Lista de grupos
- `/gestor/permissoes/grupos/{id}/editar/` - Editar permissões do grupo

---

## Contato

Para dúvidas ou sugestões sobre o sistema de permissões, entre em contato com a equipe de desenvolvimento.

**Versão:** 1.0
**Data:** 2025-10-28
**Autor:** Sistema FUZA Elevadores
