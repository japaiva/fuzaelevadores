# Sistema de Permissões Simplificado

## Visão Geral

O sistema foi simplificado para usar **apenas níveis (hardcoded)** ao invés de grupos e permissões do Django.

### Princípio Básico

**Quem tem acesso ao módulo, pode fazer TUDO dentro dele.**

Não há mais verificações granulares de permissão por ação. O controle é feito apenas no nível de acesso aos portais.

---

## Como Funciona

### 1. Níveis (9 papéis)

Cada usuário tem um `nivel` (campo CharField no modelo Usuario):

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

### 2. Acesso aos Portais

O **middleware** (`PermissaoPortalMiddleware`) controla acesso aos portais baseado no nível:

```python
portal_permissions = {
    '/gestor/': ['admin', 'gestor', 'financeiro'],
    '/vendedor/': ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria'],
    '/producao/': ['admin', 'gestor', 'producao', 'compras', 'engenharia', 'almoxarifado'],
    '/configuracao/': ['admin', 'gestor'],
}
```

**Se o usuário tem acesso ao portal, pode fazer TUDO dentro dele.**

---

## Matriz de Acesso

| Nível          | Portal Vendedor | Portal Produção | Portal Gestor |
|----------------|-----------------|-----------------|---------------|
| **Admin**      | ✅ TUDO         | ✅ TUDO         | ✅ TUDO       |
| **Gestor**     | ✅ TUDO         | ✅ TUDO         | ✅ TUDO       |
| **Vendedor**   | ✅ TUDO         | ❌              | ❌            |
| **Compras**    | ❌              | ✅ TUDO         | ❌            |
| **Engenharia** | ✅ TUDO         | ✅ TUDO         | ❌            |
| **Financeiro** | ❌              | ❌              | ✅ TUDO       |
| **Vistoria**   | ✅ TUDO         | ❌              | ❌            |
| **Produção**   | ❌              | ✅ TUDO         | ❌            |
| **Almoxarifado**| ❌             | ✅ TUDO         | ❌            |

---

## Mudanças Implementadas

### ✅ Sistema de Grupos e Permissões COMPLETAMENTE REMOVIDO

**Antes:**
- Signal adicionava usuário ao grupo Django
- Grupos tinham permissões granulares
- Views verificavam `user.has_perm('app.permission')`
- Interface para gerenciar grupos e permissões no Portal Gestor

**Agora:**
- Signal desativado (comentado) em `core/signals.py`
- Grupos ignorados completamente
- Views verificam apenas `usuario.nivel`
- **Views de permissões removidas:** `usuario_permissoes`, `grupos_permissoes_list`, `grupo_permissoes_edit`
- **URLs removidas:** 3 rotas de gerenciamento de permissões
- **Menu limpo:** Removido link "Grupos de Permissões" do Portal Gestor
- **Templates limpos:** Removido botão "Gerenciar Permissões" da lista de usuários

### ✅ Sistema de Tarefas Simplificado

**Antes:**
- Tarefa tinha `grupo_destino` (ForeignKey para Group)
- Filtrava por: `Q(grupo_destino__in=usuario.groups.all())`

**Agora:**
- Tarefa tem `nivel_destino` (CharField: 'engenharia', 'compras', etc.)
- Filtra por: `Q(nivel_destino=usuario.nivel)`

**Exemplo:**
```python
# Criar tarefa para engenharia
Tarefa.objects.create(
    tipo='projeto_executivo',
    titulo='Enviar Projeto Executivo - Proposta #123',
    nivel_destino='engenharia',  # Todos com nivel='engenharia' veem
    prioridade='normal'
)
```

### ✅ Views Atualizadas

Todas as views de tarefas foram atualizadas para usar `nivel_destino`:

```python
# producao/views/tarefas.py

# Lista de tarefas
tarefas = Tarefa.objects.filter(
    Q(usuario_destino=usuario) |
    Q(nivel_destino=usuario.nivel)  # Sistema simplificado
)

# Verificação de permissão
tem_permissao = (
    tarefa.usuario_destino == usuario or
    tarefa.nivel_destino == usuario.nivel or  # Sistema simplificado
    usuario.is_superuser or
    usuario.nivel in ['admin', 'gestor']
)
```

---

## Arquivos Modificados

### 1. `core/signals.py`
- **Desativado:** `adicionar_usuario_ao_grupo()` - Signal de grupos
- **Desativado:** `criar_perfil_usuario()` - PerfilUsuario deprecated
- **Atualizado:** `criar_tarefa_proposta_aprovada()` - Usa `nivel_destino='engenharia'`

### 2. `core/models/workflow.py`
- **Adicionado:** Campo `nivel_destino` (CharField com choices)
- **Deprecated:** Campo `grupo_destino` (marcado para remoção futura)
- **Atualizado:** Index usa `nivel_destino` ao invés de `grupo_destino`

### 3. `producao/views/tarefas.py`
- **Atualizado:** `lista_tarefas()` - Filtra por `nivel_destino`
- **Atualizado:** `detalhes_tarefa()` - Verifica permissão por `nivel_destino`
- **Atualizado:** `iniciar_tarefa()` - Verifica permissão por `nivel_destino`
- **Atualizado:** `concluir_tarefa()` - Verifica permissão por `nivel_destino`
- **Atualizado:** `contador_tarefas_pendentes()` - Conta por `nivel_destino`

### 4. Migrations
- **Nova:** `0047_add_nivel_destino_tarefa` - Adiciona campo e índice

---

## Como Usar

### Criar Usuário

```python
from core.models import Usuario

# Criar usuário engenharia
user = Usuario.objects.create_user(
    username='joao',
    password='senha123',
    nivel='engenharia'  # Define o nível
)

# Pronto! Não precisa adicionar a grupos manualmente
```

### Criar Tarefa

```python
from core.models import Tarefa

# Tarefa para todos os usuários de engenharia
Tarefa.objects.create(
    tipo='projeto_executivo',
    titulo='Enviar Projeto Executivo - Proposta #123',
    descricao='Detalhes...',
    nivel_destino='engenharia',  # Todos com nivel='engenharia' veem
    prioridade='alta'
)

# Tarefa para usuário específico
Tarefa.objects.create(
    tipo='criar_lista_materiais',
    titulo='Criar Lista de Materiais - Proposta #456',
    usuario_destino=user_especifico,  # Apenas este usuário vê
    prioridade='normal'
)
```

### Verificar Acesso

```python
# Em qualquer view
usuario = request.user

# Verificar se pode acessar portal produção
pode_producao = usuario.nivel in ['admin', 'gestor', 'producao', 'compras', 'engenharia', 'almoxarifado']

# Verificar se é admin/gestor
eh_gestor = usuario.nivel in ['admin', 'gestor']
```

---

## Workflow: Proposta Aprovada

### Fluxo Automático

1. **Vendedor aprova proposta** no Portal Vendedor
   - Muda `proposta.status = 'aprovado'`
   - Salva proposta

2. **Signal cria tarefa automaticamente**
   ```python
   Tarefa.objects.create(
       tipo='projeto_executivo',
       titulo='Enviar Projeto Executivo - Proposta #123',
       descricao='...',
       nivel_destino='engenharia',
       prioridade='normal'
   )
   ```

3. **Engenheiros veem a tarefa**
   - Todos os usuários com `nivel='engenharia'` veem no menu **Adm → Tarefas**
   - Badge mostra quantidade de tarefas pendentes

4. **Engenheiro conclui a tarefa**
   - Clica em "Concluir"
   - Adiciona observações (opcional)
   - Tarefa marcada como concluída
   - Registro no histórico

---

## Próximos Passos (Futuro)

### Para expandir o workflow:

1. **Novos tipos de tarefa:**
   - Adicionar em `Tarefa.TIPO_CHOICES`
   - Criar signal específico para gerar automaticamente

2. **Novos triggers:**
   - Criar signals em `core/signals.py`
   - Exemplo: Requisição aprovada → Tarefa para compras

3. **Dashboard de tarefas:**
   - Criar widget no portal gestor com visão geral
   - Gráficos de tarefas por status/nível

---

## Resumo: O Que Mudou?

| Aspecto                  | Antes (Complexo)           | Agora (Simplificado)         |
|--------------------------|----------------------------|------------------------------|
| Controle de acesso       | Middleware + Permissions   | Apenas Middleware (nível)    |
| Atribuição de tarefas    | Grupo Django               | nivel_destino (string)       |
| Verificação de permissão | `user.has_perm()`          | `usuario.nivel in [...]`     |
| Signal de grupos         | Ativo                      | Desativado                   |
| Complexidade             | Alta (grupos + permissões) | Baixa (apenas níveis)        |

---

---

## Arquivos Removidos/Desativados

### Código Python
- `core/signals.py` → Signal `adicionar_usuario_ao_grupo()` desativado
- `core/signals.py` → Signal `criar_perfil_usuario()` desativado
- `gestor/views.py` → View `usuario_permissoes()` removida
- `gestor/views.py` → View `grupos_permissoes_list()` removida
- `gestor/views.py` → View `grupo_permissoes_edit()` removida
- `gestor/urls.py` → 3 URLs de permissões removidas

### Templates (não usados mais)
- `templates/gestor/usuario_permissoes.html` (órfão)
- `templates/gestor/grupos_permissoes_list.html` (órfão)
- `templates/gestor/grupo_permissoes_edit.html` (órfão)

### Interface
- Menu "Grupos de Permissões" removido de `base_gestor.html`
- Botão "Gerenciar Permissões" removido de `usuario_list.html`

---

**Autor:** Sistema FUZA
**Data:** 02/11/2025
**Versão:** 2.0 (Sistema Completamente Simplificado - Grupos Removidos)
