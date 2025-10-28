# 🚀 Quickstart - Sistema de Permissões

## Setup Inicial (3 passos)

```bash
# 1. Rodar migrations
source .venv/bin/activate
python manage.py migrate

# 2. Criar grupos e permissões
python manage.py setup_permissoes

# 3. Pronto! Sistema configurado ✓
```

---

## Novos Perfis Criados

| Perfil | Portal | Principais Funções |
|--------|--------|-------------------|
| `financeiro` | Gestor | Visualizar custos, aprovar orçamentos até R$ 50k |
| `vistoria` | Vendedor | Realizar vistorias e medições de obra |
| `producao` | Produção | Gerenciar listas de materiais |

---

## Como Criar Usuário

```python
from core.models import Usuario

# Criar usuário - ele é automaticamente adicionado ao grupo correto!
usuario = Usuario.objects.create(
    username='maria',
    nivel='financeiro',  # ← Vai automaticamente para grupo "Financeiro"
)
usuario.set_password('senha123')
usuario.save()
```

---

## Como Usar nas Views

### Function-Based Views

```python
from core.utils.permissions import require_permission, require_nivel

# Exigir permissão
@require_permission('core.aprovar_desconto_10')
def minha_view(request):
    pass

# Exigir nível
@require_nivel('admin', 'gestor')
def outra_view(request):
    pass
```

### Class-Based Views

```python
from core.utils.permissions import PermissionRequiredMixin

class MinhaView(PermissionRequiredMixin, ListView):
    permission_required = 'core.aprovar_proposta'
```

---

## Como Usar nos Templates

```django
{% if perms.core.visualizar_custos %}
    <td>R$ {{ proposta.custo }}</td>
{% else %}
    <td>-</td>
{% endif %}
```

---

## Verificar Permissões no Código

```python
from core.utils.permissions import pode_aprovar_desconto

# Pode aprovar 8% de desconto?
if pode_aprovar_desconto(request.user, 8.0):
    # Sim!
    pass
```

---

## Interface Web

**Gerenciar permissões:**
1. Portal Gestor → Cadastros → Usuários
2. Clique no ícone 🔑 ao lado do usuário
3. Selecione grupos e permissões individuais
4. Salvar

**Ver grupos:**
- Portal Gestor → Cadastros → Grupos de Permissões

---

## Permissões Mais Usadas

| Permissão | Descrição |
|-----------|-----------|
| `aprovar_desconto_5` | Aprovar até 5% |
| `aprovar_desconto_10` | Aprovar até 10% |
| `aprovar_desconto_15` | Aprovar até 15% |
| `visualizar_custos` | Ver custos e margens |
| `visualizar_todas_propostas` | Ver propostas de todos |
| `aprovar_proposta` | Aprovar proposta |
| `realizar_vistoria` | Fazer vistoria |
| `aprovar_lista_materiais` | Aprovar lista |
| `aprovar_orcamento_ate_10000` | Aprovar até R$ 10k |

---

## Troubleshooting Rápido

**Usuário sem permissões?**
```bash
python manage.py setup_permissoes
```

**Precisa recriar tudo?**
```bash
python manage.py migrate --run-syncdb
python manage.py setup_permissoes
```

---

📖 **Documentação completa:** Veja `PERMISSOES.md`
