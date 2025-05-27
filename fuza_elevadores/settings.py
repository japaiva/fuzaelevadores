from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
import sys

# Debug para identificar problemas de logging
print("=== INICIANDO CONFIGURAÇÃO SISTEMA ELEVADORES FUZA ===")
print(f"Diretório de execução atual: {os.getcwd()}")

# Carrega variáveis do arquivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR: {BASE_DIR}")

# Criar diretório de logs com notificação
logs_dir = os.path.join(BASE_DIR, 'logs')
print(f"Tentando criar diretório de logs em: {logs_dir}")
try:
    os.makedirs(logs_dir, exist_ok=True)
    print(f"✓ Diretório de logs criado/verificado com sucesso: {logs_dir}")
    print(f"  Permissões do diretório: {oct(os.stat(logs_dir).st_mode)[-3:]}")
except Exception as e:
    print(f"✗ ERRO ao criar diretório de logs: {str(e)}")

# Tentar criar arquivo de teste para verificar permissões
try:
    test_log_path = os.path.join(logs_dir, 'test_write.log')
    print(f"Tentando escrever arquivo de teste em: {test_log_path}")
    with open(test_log_path, 'w') as f:
        f.write('Teste de escrita de log - Sistema Fuza OK')
    print(f"✓ Teste de escrita no diretório de logs bem-sucedido")
except Exception as e:
    print(f"✗ ERRO ao escrever arquivo de teste: {str(e)}")

# Security
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Configuração MinIO (via django-storages)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = 'us-east-1'  # Região padrão para compatibilidade
AWS_S3_ADDRESSING_STYLE = 'path'  # Importante: usar 'path' em vez de 'virtual'

# Usa MinIO como armazenamento padrão
DEFAULT_FILE_STORAGE = 'core.storage.MinioStorage'
MEDIA_URL = '/media/'

# Static Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# API KEYS
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Aplicações instaladas - Específicas do Sistema Fuza
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'storages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    
    # Apps do Sistema Fuza
    'core',
    'configuracao',  # Motor de regras configurável
    'vendedor',      # Portal do vendedor
    'producao',      # Portal de producao
    'gestor',        # Portal do gestor
    'api',           # APIs REST
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Middlewares da Fuza
    'fuza_elevadores.middleware.AppContextMiddleware',
    'fuza_elevadores.middleware.PermissaoPortalMiddleware',
    'fuza_elevadores.middleware.SimulacaoContextMiddleware',
    'fuza_elevadores.middleware.ComponenteDisponibilidadeMiddleware',
    'fuza_elevadores.middleware.FuzaLogMiddleware',
]

ROOT_URLCONF = 'fuza_elevadores.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fuza_elevadores.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Auth settings
AUTH_USER_MODEL = 'core.Usuario'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'

# Mensagens
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Segurança
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://elevadores-fuza.com']

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Configurações específicas do Sistema Fuza
FUZA_ELEVADORES_SETTINGS = {
    # Motor de Regras Configurável
    'MOTOR_REGRAS_ATIVO': True,
    'VALIDACAO_DISPONIBILIDADE_TEMPO_REAL': True,
    'GERACAO_CODIGO_PRODUTO_AUTOMATICA': True,
    
    # Produção Antecipada
    'PRODUCAO_ANTECIPADA_ATIVA': True,
    'MEDICAO_PRE_PROJETO': True,
    'VISTORIA_ENCORPADA': True,
    'CONTRATOS_BLINDADOS': True,
    
    # Níveis de Permissão
    'ALACADAS_DESCONTO': {
        'vendedor': 5.0,     # 5% máximo
        'gestor': 15.0,      # 15% máximo  
        'admin': 100.0,      # Sem limite
    },
    
    # Simulação
    'ETAPAS_SIMULACAO': ['cliente', 'elevador', 'portas', 'cabine'],
    'TEMPO_SESSAO_SIMULACAO': 3600,  # 1 hora
    'BACKUP_AUTOMATICO_SIMULACAO': True,
    
    # Formação de Preço
    'TIPOS_FATURAMENTO': ['Elevadores', 'Fuza', 'Manutenção'],
    'MARGEM_PADRAO': 30.0,
    'COMISSAO_PADRAO': 3.0,
    'IMPOSTOS_PADRAO': {
        'Elevadores': 10.0,
        'Fuza': 8.5,
        'Manutenção': 12.0,
    },
    
    # PDFs
    'DEMONSTRATIVO_CUSTO_NIVEIS': ['admin', 'engenharia'],
    'PROPOSTA_COMERCIAL_NIVEIS': ['vendedor', 'gestor', 'admin'],
    
    # Notificações
    'NOTIFICAR_ESTOQUE_BAIXO': True,
    'NOTIFICAR_COMPONENTE_INDISPONIVEL': True,
    'NOTIFICAR_APROVACAO_NECESSARIA': True,
}

# Configurações de logging - Sistema Fuza
print("Configurando sistema de logging do Sistema Fuza...")

# Verifica permissões no diretório de logs
LOG_DEBUG_PATH = os.path.join(logs_dir, 'fuza_debug.log')
LOG_SIMULACOES_PATH = os.path.join(logs_dir, 'fuza_simulacoes.log')
LOG_VENDAS_PATH = os.path.join(logs_dir, 'fuza_vendas.log')

print(f"Arquivos de log que serão usados:")
print(f" - Debug: {LOG_DEBUG_PATH}")
print(f" - Simulações: {LOG_SIMULACOES_PATH}")
print(f" - Vendas: {LOG_VENDAS_PATH}")

# Testa escrita nos arquivos de log
for log_path, log_name in [(LOG_DEBUG_PATH, 'debug'), (LOG_SIMULACOES_PATH, 'simulacoes'), (LOG_VENDAS_PATH, 'vendas')]:
    try:
        with open(log_path, 'a') as f:
            f.write(f'Teste de inicialização - Sistema Fuza {log_name}.log\n')
        print(f"✓ Teste de escrita em {log_name}.log bem-sucedido")
    except Exception as e:
        print(f"✗ ERRO ao escrever em {log_name}.log: {str(e)}")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'fuza_format': {
            'format': '[FUZA-{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'fuza_format',
            'stream': sys.stdout,
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_DEBUG_PATH,
            'formatter': 'fuza_format',
        },
        'simulacoes_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_SIMULACOES_PATH,
            'formatter': 'fuza_format',
        },
        'vendas_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_VENDAS_PATH,
            'formatter': 'fuza_format',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'debug_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console', 'debug_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'configuracao': {
            'handlers': ['console', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'vendedor': {
            'handlers': ['console', 'simulacoes_file', 'vendas_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'compras': {
            'handlers': ['console', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'gestor': {
            'handlers': ['console', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Logger específico para simulações
        'fuza.simulacoes': {
            'handlers': ['console', 'simulacoes_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Logger específico para vendas
        'fuza.vendas': {
            'handlers': ['console', 'vendas_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

print("=== CONFIGURAÇÃO SISTEMA FUZA CONCLUÍDA ===")

# Teste final do sistema de logging
import logging
logger = logging.getLogger('fuza.simulacoes')
logger.info("Sistema Elevadores Fuza inicializado com sucesso")
