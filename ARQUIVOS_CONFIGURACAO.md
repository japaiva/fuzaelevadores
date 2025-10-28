# 📁 Arquivos de Configuração - FUZA Elevadores

## 🎯 Arquivos Principais

### **1. Configuração Django - settings.py**
**Localização:** `/Users/joseantoniopaiva/pythonprojects/fuza/fuza_elevadores/settings.py`

**O que contém:**
- ✅ SECRET_KEY e DEBUG
- ✅ Configuração do banco de dados (PostgreSQL)
- ✅ Apps instalados (INSTALLED_APPS)
- ✅ Middleware (incluindo nossos middlewares customizados)
- ✅ Templates e arquivos estáticos
- ✅ Configuração de arquivos (MinIO/S3)
- ✅ Sistema de logging
- ✅ Configurações específicas do FUZA (FUZA_ELEVADORES_SETTINGS)
- ✅ REST Framework
- ✅ Alçadas de desconto por nível de usuário

**Principais Seções:**

```python
# Segurança
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Banco de Dados
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:password@localhost:5432/fuzadb',
        conn_max_age=600
    )
}

# Apps Instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
    'vendedor',
    'gestor',
    'producao',
    'configuracao',
    'api',
]

# Middleware (incluindo nossos customizados)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'fuza_elevadores.middleware.AppContextMiddleware',
    'fuza_elevadores.middleware.PermissaoPortalMiddleware',  # ← Nosso middleware de permissões
    'fuza_elevadores.middleware.SimulacaoContextMiddleware',
    'fuza_elevadores.middleware.ComponenteDisponibilidadeMiddleware',
    'fuza_elevadores.middleware.FuzaLogMiddleware',
]

# Modelo de usuário customizado
AUTH_USER_MODEL = 'core.Usuario'

# Configurações específicas do FUZA
FUZA_ELEVADORES_SETTINGS = {
    'ALACADAS_DESCONTO': {
        'vendedor': 5.0,
        'gestor': 15.0,
        'admin': 100.0,
    },
    'DEMONSTRATIVO_CUSTO_NIVEIS': ['admin', 'engenharia'],
    'PROPOSTA_COMERCIAL_NIVEIS': ['vendedor', 'gestor', 'admin'],
}
```

---

### **2. Variáveis de Ambiente - .env**
**Localização:** `/Users/joseantoniopaiva/pythonprojects/fuza/.env`

**O que contém:**
- ✅ SECRET_KEY do Django
- ✅ DEBUG mode
- ✅ ALLOWED_HOSTS
- ✅ DATABASE_URL (PostgreSQL)
- ✅ Credenciais MinIO (AWS_*)
- ✅ API Keys (OpenAI, Groq, Anthropic, Pinecone)

**Estrutura:**
```bash
# Geral
SECRET_KEY="sua-chave-secreta-aqui"
DEBUG=True
ALLOWED_HOSTS=fuza.spsystems.pro,localhost,127.0.0.1

# Banco de Dados
DATABASE_URL="postgresql://usuario:senha@host:porta/database"

# Armazenamento MinIO (S3-compatible)
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=senha
AWS_STORAGE_BUCKET_NAME=fuza
AWS_S3_ENDPOINT_URL=https://s3.spsystems.pro

# APIs Externas (opcionais)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
PINECONE_API_KEY=pcsk_...
```

⚠️ **IMPORTANTE:** Este arquivo **NÃO** deve ser commitado no Git (está no `.gitignore`)

---

### **3. URLs Principal - urls.py**
**Localização:** `/Users/joseantoniopaiva/pythonprojects/fuza/fuza_elevadores/urls.py`

**O que contém:**
- ✅ Roteamento dos 3 portais (gestor, vendedor, producao)
- ✅ Admin Django
- ✅ Views de autenticação (login, logout, perfil)
- ✅ Página inicial

**Estrutura:**
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),

    # Autenticação
    path('login/', ...),
    path('perfil/', perfil, name='perfil'),
    path('logout/', logout_view, name='logout'),

    # Portais
    path('gestor/', include('gestor.urls')),
    path('vendedor/', include('vendedor.urls')),
    path('producao/', include('producao.urls')),
]
```

---

### **4. Middleware Customizado**
**Localização:** `/Users/joseantoniopaiva/pythonprojects/fuza/fuza_elevadores/middleware.py`

**Contém 5 middlewares customizados:**

1. **AppContextMiddleware** - Define contexto do portal baseado na URL
2. **PermissaoPortalMiddleware** - ⭐ **Controla acesso aos portais por nível**
3. **SimulacaoContextMiddleware** - Gerencia simulações ativas
4. **ComponenteDisponibilidadeMiddleware** - Verifica estoque baixo
5. **FuzaLogMiddleware** - Sistema de logging

**Configuração de Permissões de Portais:**
```python
portal_permissions = {
    '/gestor/': ['admin', 'gestor', 'financeiro'],
    '/vendedor/': ['admin', 'gestor', 'vendedor', 'engenharia', 'vistoria'],
    '/producao/': ['admin', 'gestor', 'producao', 'compras', 'engenharia'],
    '/configuracao/': ['admin', 'gestor'],
}
```

---

### **5. WSGI (Produção)**
**Localização:** `/Users/joseantoniopaiva/pythonprojects/fuza/fuza_elevadores/wsgi.py`

Usado para deploy em produção (Gunicorn, uWSGI, etc.)

---

### **6. ASGI (Async)**
**Localização:** `/Users/joseantoniopaiva/pythonprojects/fuza/fuza_elevadores/asgi.py`

Usado para aplicações assíncronas (WebSockets, etc.)

---

## 📦 URLs dos Apps

### Gestor
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/gestor/urls.py`

**Principais rotas:**
```python
/gestor/dashboard/
/gestor/usuarios/
/gestor/usuarios/<id>/permissoes/  # ← Nova rota de permissões
/gestor/permissoes/grupos/         # ← Nova rota de grupos
/gestor/clientes/
/gestor/fornecedores/
/gestor/materias-primas/
/gestor/grupos/
/gestor/subgrupos/
```

### Vendedor
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/vendedor/urls.py`

**Principais rotas:**
```python
/vendedor/dashboard/
/vendedor/propostas/
/vendedor/simulacoes/
/vendedor/clientes/
/vendedor/vistoria/
```

### Produção
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/producao/urls.py`

**Principais rotas:**
```python
/producao/dashboard/
/producao/listas-materiais/
/producao/requisicoes/
/producao/orcamentos/
/producao/fornecedores/
```

---

## 🔧 Apps Configuration

### Core App
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/core/apps.py`

```python
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals  # ← Carrega signals de permissões
```

### Gestor App
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/gestor/apps.py`

### Vendedor App
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/vendedor/apps.py`

### Produção App
**Arquivo:** `/Users/joseantoniopaiva/pythonprojects/fuza/producao/apps.py`

---

## 🗂️ Estrutura de Diretórios

```
fuza/
├── .env                          # ← Variáveis de ambiente (NÃO COMMITAR)
├── .gitignore                    # Arquivos ignorados pelo Git
├── manage.py                     # Script de gerenciamento Django
├── requirements.txt              # Dependências Python
├── dockerfile                    # Configuração Docker
├── PERMISSOES.md                 # ← Documentação de permissões (NOVA)
├── PERMISSOES_QUICKSTART.md      # ← Guia rápido (NOVO)
├── ARQUIVOS_CONFIGURACAO.md      # ← Este arquivo (NOVO)
│
├── fuza_elevadores/              # ← Pasta principal de configuração
│   ├── settings.py               # ← Configuração principal ⭐
│   ├── urls.py                   # ← URLs principal ⭐
│   ├── wsgi.py                   # Deploy produção
│   ├── asgi.py                   # Deploy assíncrono
│   └── middleware.py             # ← Middlewares customizados ⭐
│
├── core/                         # App principal
│   ├── apps.py                   # ← Configuração do app (carrega signals)
│   ├── models/                   # Modelos do banco
│   ├── views/                    # Views
│   ├── forms/                    # Formulários
│   ├── signals.py                # ← Signals de permissões (NOVO)
│   ├── utils/
│   │   └── permissions.py        # ← Decorators de permissões (NOVO)
│   └── management/commands/
│       └── setup_permissoes.py   # ← Comando de setup (NOVO)
│
├── gestor/                       # Portal do Gestor
│   ├── apps.py
│   ├── urls.py                   # ← URLs do gestor
│   └── views.py                  # Views (incluindo permissões)
│
├── vendedor/                     # Portal do Vendedor
│   ├── apps.py
│   ├── urls.py
│   └── views/
│
├── producao/                     # Portal de Produção
│   ├── apps.py
│   ├── urls.py
│   └── views/
│
├── templates/                    # Templates HTML
│   ├── base.html
│   ├── gestor/
│   │   ├── base_gestor.html
│   │   ├── usuario_permissoes.html      # ← NOVO
│   │   ├── grupos_permissoes_list.html  # ← NOVO
│   │   └── grupo_permissoes_edit.html   # ← NOVO
│   ├── vendedor/
│   └── producao/
│
└── static/                       # Arquivos estáticos (CSS, JS, imagens)
```

---

## 🔐 Configurações de Segurança

### No settings.py:

```python
# Produção
DEBUG = False  # ← Sempre False em produção
SECRET_KEY = 'chave-aleatória-longa'  # ← Via .env
ALLOWED_HOSTS = ['fuza.spsystems.pro']  # ← Domínios permitidos

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 🗄️ Configuração do Banco de Dados

### Via .env:
```bash
DATABASE_URL="postgresql://usuario:senha@host:porta/database"
```

### No settings.py:
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:password@localhost:5432/fuzadb',
        conn_max_age=600  # Conexões persistentes
    )
}
```

---

## 📝 Sistema de Logging

### No settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'fuza_debug.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_simulacoes': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'fuza_simulacoes.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'fuza.simulacoes': {
            'handlers': ['file_simulacoes'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Logs gerados:**
- `logs/fuza_debug.log` - Debug geral
- `logs/fuza_simulacoes.log` - Simulações
- `logs/fuza_vendas.log` - Vendas

---

## 🚀 Como Modificar Configurações

### 1. Variáveis de Ambiente (.env)
```bash
# Edite o arquivo .env
nano .env

# Reinicie o servidor
python manage.py runserver
```

### 2. Settings Django
```bash
# Edite settings.py
nano fuza_elevadores/settings.py

# Reinicie o servidor
python manage.py runserver
```

### 3. Adicionar Nova Rota
```python
# Edite o urls.py do app
nano gestor/urls.py

# Adicione a rota
path('nova-rota/', views.minha_view, name='minha_view'),

# Não precisa reiniciar em desenvolvimento (auto-reload)
```

### 4. Modificar Middleware
```bash
# Edite o middleware
nano fuza_elevadores/middleware.py

# Reinicie o servidor
python manage.py runserver
```

---

## 📊 Comandos Úteis

### Ver configurações atuais:
```bash
python manage.py diffsettings
```

### Verificar configuração do projeto:
```bash
python manage.py check
```

### Ver todas as URLs:
```bash
python manage.py show_urls  # (se django-extensions instalado)
```

### Aplicar migrations:
```bash
python manage.py migrate
```

### Criar superusuário:
```bash
python manage.py createsuperuser
```

### Rodar servidor de desenvolvimento:
```bash
python manage.py runserver
```

### Rodar em produção (Gunicorn):
```bash
gunicorn fuza_elevadores.wsgi:application --bind 0.0.0.0:8000
```

---

## 🔍 Ordem de Carregamento

1. **.env** → Carregado primeiro pelo `load_dotenv()`
2. **settings.py** → Lê variáveis do .env
3. **middleware.py** → Carregado pelo MIDDLEWARE no settings
4. **urls.py** → Define roteamento
5. **apps.py (ready)** → Carrega signals
6. **signals.py** → Registra signals

---

## ⚠️ Arquivos Sensíveis (NÃO COMMITAR)

❌ `.env` - Contém credenciais
❌ `db.sqlite3` - Banco local
❌ `*.pyc` - Bytecode Python
❌ `__pycache__/` - Cache Python
❌ `.venv/` - Ambiente virtual
❌ `logs/*.log` - Logs do sistema

✅ Todos já estão no `.gitignore`

---

## 📚 Referências Rápidas

| Configuração | Arquivo | Linha Aproximada |
|--------------|---------|------------------|
| Apps instalados | `settings.py` | 70-85 |
| Banco de dados | `settings.py` | 50-60 |
| Middleware | `settings.py` | 90-110 |
| Permissões portais | `middleware.py` | 180-190 |
| Alçadas desconto | `settings.py` | 200-210 |
| URLs principais | `urls.py` | 10-30 |
| Modelo de usuário | `settings.py` | 160 |
| Logging | `settings.py` | 130-170 |

---

**Versão:** 1.0
**Data:** 2025-10-28
**Sistema:** FUZA Elevadores
