# Correções no Sistema de Permissões

## O que foi corrigido?

### 1. Nomenclatura de Grupos Padronizada
**Antes:** Grupo "Produção" (com acento e cedilha)
**Depois:** Grupo "Producao" (sem acento, capitalizado)

**Motivo:** Evitar problemas de encoding e manter consistência com os outros grupos.

### 2. Logging Adequado nos Signals
**Antes:** Uso de `print()` para debug
**Depois:** Uso de `logging` com níveis apropriados (info, warning, error)

**Benefício:** Logs aparecem em produção e podem ser configurados via settings.

### 3. Remoção de Duplicação - PerfilUsuario
**Antes:** Dados duplicados em `Usuario` e `PerfilUsuario`
**Depois:** Todos os dados apenas em `Usuario`

**Benefício:** Menos chances de desincronização, mais simples de manter.

---

## Como aplicar as correções?

### Passo 1: Executar migração de grupos
```bash
python manage.py migrar_grupo_producao
```

Este comando vai:
- Renomear grupo "Produção" → "Producao"
- Manter todos os usuários e permissões
- Ou mesclar com grupo "Producao" existente, se houver

### Passo 2: Reconfigurar permissões
```bash
python manage.py setup_permissoes
```

Este comando vai:
- Criar ou atualizar todos os 9 grupos
- Atribuir permissões corretas a cada grupo
- Garantir que Admin tem todas as permissões

### Passo 3: Verificar usuários
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import Group

# Ver usuários do grupo Producao
grupo = Group.objects.get(name='Producao')
print(f"Usuários em {grupo.name}:")
for user in grupo.user_set.all():
    print(f"  - {user.username} (nível: {user.nivel})")

# Ver permissões do grupo
print(f"\nPermissões ({grupo.permissions.count()}):")
for perm in grupo.permissions.all()[:10]:
    print(f"  - {perm.codename}")
```

---

## Mapeamento de Níveis → Grupos

| Nível (field) | Grupo (Django) | Sincronização |
|---------------|----------------|---------------|
| `admin` | Admin | Automática via signal |
| `gestor` | Gestor | Automática via signal |
| `vendedor` | Vendedor | Automática via signal |
| `financeiro` | Financeiro | Automática via signal |
| `vistoria` | Vistoria | Automática via signal |
| `producao` | Producao | Automática via signal |
| `compras` | Compras | Automática via signal |
| `engenharia` | Engenharia | Automática via signal |
| `almoxarifado` | Almoxarifado | Automática via signal |

**Como funciona:**
1. Quando você cria/atualiza um usuário e define `nivel='producao'`
2. O signal `adicionar_usuario_ao_grupo` é executado
3. O usuário é automaticamente adicionado ao grupo `Producao`
4. As permissões do grupo são aplicadas ao usuário

---

## Sistema Híbrido de Permissões

### Nível 1: Middleware (Controle de Portal)
Controla quem pode acessar cada portal baseado em `user.nivel`:

```python
# fuza_elevadores/middleware.py
portal_permissions = {
    '/gestor/': ['admin', 'gestor', 'financeiro'],
    '/vendedor/': ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria'],
    '/producao/': ['admin', 'gestor', 'producao', 'compras', 'engenharia', 'almoxarifado'],
}
```

### Nível 2: Decorators (Controle de View/Ação)
Controla quem pode executar ações específicas baseado em permissões:

```python
from core.utils.permissions import require_permission

@login_required
@require_permission('core.aprovar_proposta')
def aprovar_proposta(request, pk):
    # Apenas usuários com essa permissão podem aprovar
    ...
```

### Nível 3: Templates (UI Condicional)
Esconde botões/links que o usuário não pode usar:

```django
{% if perms.core.aprovar_desconto_10 %}
    <button>Aprovar Desconto</button>
{% endif %}
```

---

## Próximos Passos (Pendentes)

### ✅ Já feito:
- [x] Padronizar nomenclatura de grupos
- [x] Melhorar logging nos signals
- [x] Remover uso de PerfilUsuario nas views
- [x] Marcar PerfilUsuario como deprecado

### ⏳ A fazer:
- [ ] Adicionar `@require_permission` nas views críticas
- [ ] Adicionar verificações de permissão nas templates
- [ ] Criar sistema de notificações/workflow
- [ ] Remover modelo PerfilUsuario completamente (migration)
- [ ] Adicionar testes de permissão

---

## Referência Rápida - Decorators Disponíveis

### Para Function-Based Views:

```python
from core.utils.permissions import (
    require_nivel,
    require_permission,
    require_any_permission,
    require_nivel_and_permission
)

# Apenas para gestor e admin
@require_nivel('gestor', 'admin')
def minha_view(request):
    ...

# Requer permissão específica
@require_permission('core.aprovar_proposta')
def aprovar(request):
    ...

# Requer QUALQUER UMA das permissões
@require_any_permission('core.aprovar_desconto_5', 'core.aprovar_desconto_10')
def aprovar_desconto(request):
    ...

# Combina nível E permissão
@require_nivel_and_permission(['gestor', 'admin'], ['core.visualizar_custos'])
def ver_custos(request):
    ...
```

### Para Class-Based Views:

```python
from core.utils.permissions import (
    NivelRequiredMixin,
    PermissionRequiredMixin,
    AnyPermissionRequiredMixin
)

class MinhaView(NivelRequiredMixin, View):
    niveis_permitidos = ['admin', 'gestor']
    ...

class AprovarView(PermissionRequiredMixin, View):
    permission_required = 'core.aprovar_proposta'
    ...
```

---

## Troubleshooting

### Problema: Usuário não consegue acessar portal

**Verificar:**
1. Usuário tem `nivel` definido?
   ```python
   user = Usuario.objects.get(username='joao')
   print(user.nivel)  # deve retornar algo como 'producao'
   ```

2. O `nivel` está no middleware?
   ```python
   # Verificar em fuza_elevadores/middleware.py linha 182
   # Se não estiver, adicionar
   ```

3. Signal adicionou ao grupo?
   ```python
   print(user.groups.all())  # deve mostrar o grupo
   ```

### Problema: Signal não está funcionando

**Verificar:**
1. Signal está registrado em `core/apps.py`?
   ```python
   def ready(self):
       import core.signals
   ```

2. Logs aparecem?
   ```bash
   python manage.py shell
   >>> import logging
   >>> logging.basicConfig(level=logging.INFO)
   >>> from core.models import Usuario
   >>> u = Usuario.objects.get(pk=1)
   >>> u.nivel = 'producao'
   >>> u.save()  # deve aparecer log
   ```

### Problema: Grupo não tem permissões

**Solução:**
```bash
python manage.py setup_permissoes
```

Isso recria/atualiza todos os grupos com as permissões corretas.

---

## Contato / Suporte

Se encontrar problemas:
1. Verifique os logs: `tail -f logs/django.log`
2. Execute shell: `python manage.py shell`
3. Teste manualmente as permissões

Arquivos importantes:
- `core/signals.py` - Auto atribuição de grupos
- `core/utils/permissions.py` - Decorators e mixins
- `core/management/commands/setup_permissoes.py` - Configuração de grupos
- `fuza_elevadores/middleware.py` - Controle de portal
