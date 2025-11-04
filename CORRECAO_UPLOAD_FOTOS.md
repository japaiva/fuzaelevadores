# 🔧 Correção: Upload de Fotos nas Vistorias

## ✅ Problema Identificado e Resolvido

### Problema
As fotos eram enviadas para o MinIO, mas não apareciam no navegador (erro 404).

### Causa Raiz
1. **Django 5.1**: Usando `DEFAULT_FILE_STORAGE` (descontinuado) ao invés de `STORAGES`
2. **URLs não assinadas**: As fotos estavam sendo salvas no MinIO, mas as URLs não incluíam assinatura de acesso
3. **Bucket privado**: O bucket `fuza` provavelmente está configurado como privado (sem acesso público)

### Solução Implementada

#### 1. Atualizado para Django 5.1+ (settings.py)
```python
# ANTES (não funcionava)
DEFAULT_FILE_STORAGE = 'core.storage.MinioStorage'

# DEPOIS (funciona!)
STORAGES = {
    "default": {
        "BACKEND": "core.storage.MinioStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

#### 2. Configurado URLs Assinadas (core/storage.py)
```python
class MinioStorage(S3Boto3Storage):
    # ... outras configs ...

    # Gerar URLs assinadas (presigned URLs)
    querystring_auth = True
    querystring_expire = 604800  # 7 dias

    # Removido custom_domain para permitir assinaturas
```

## 📋 O Que Mudou

### URLs Antes (não funcionavam)
```
https://s3.spsystems.pro/fuza/vistorias/PROP-001/foto.jpg
```
❌ Retornava 404 porque o bucket é privado

### URLs Agora (funcionam!)
```
https://s3.spsystems.pro/fuza/vistorias/PROP-001/foto.jpg?
X-Amz-Algorithm=AWS4-HMAC-SHA256&
X-Amz-Credential=admin%2F...&
X-Amz-Date=20251104T225049Z&
X-Amz-Expires=604800&
X-Amz-SignedHeaders=host&
X-Amz-Signature=3e3531f73a8ee2dcb158bac12b105e962099f66cbaebc1309fedc5ce048f534a
```
✅ URLs assinadas com validade de 7 dias

## 🎯 Como Testar

### 1. Reinicie o Servidor Django
```bash
# Se estiver rodando com runserver
Ctrl+C
python manage.py runserver

# Se estiver em produção (ex: Gunicorn)
sudo systemctl restart gunicorn
```

### 2. Faça Upload de uma Nova Foto
1. Acesse o Portal do Vendedor
2. Vá em uma vistoria
3. Clique em "Nova Vistoria"
4. Selecione fotos
5. Registre a vistoria

### 3. Verifique se as Fotos Aparecem
1. Abra os detalhes da vistoria
2. As fotos devem aparecer corretamente
3. Clique em uma foto para abrir em tamanho maior

## 🔍 Verificando Logs

Se ainda houver problemas, verifique os logs:

```bash
tail -f logs/fuza_vendas.log
```

Você deve ver:
```
Foto uploaded com sucesso: vistorias/PROP-001/abc123.jpg
URL gerada: https://s3.spsystems.pro/fuza/...?X-Amz-Algorithm=...
```

## ⚠️ Importante: URLs Expiram em 7 Dias

As URLs assinadas são válidas por **7 dias**. Depois disso, será necessário regenerar as URLs.

### Como Regenerar URLs (Futuro)

Se precisar regenerar as URLs expiradas, você pode criar um comando Django:

```python
# manage.py regenerar_urls_fotos
from core.models import VistoriaHistorico
from django.core.files.storage import default_storage

for vistoria in VistoriaHistorico.objects.exclude(fotos_anexos=[]):
    for foto in vistoria.fotos_anexos:
        # Regenerar URL
        nova_url = default_storage.url(foto['caminho'])
        foto['url'] = nova_url
    vistoria.save()
```

Ou aumentar o tempo de expiração em `core/storage.py`:
```python
querystring_expire = 2592000  # 30 dias
```

## 📊 Arquivos Modificados

1. ✅ `fuza_elevadores/settings.py` - Atualizado para Django 5.1
2. ✅ `core/storage.py` - Configurado URLs assinadas
3. ✅ `vendedor/views/vistoria.py` - Removido try/except desnecessário

## 🧪 Teste de Conexão

Para verificar se está tudo OK:

```bash
python test_minio_connection.py
```

Deve retornar:
```
✅ TODOS OS TESTES PASSARAM COM SUCESSO!
```

## 🎉 Status Final

- ✅ Upload funcionando
- ✅ Arquivos salvos no MinIO
- ✅ URLs assinadas geradas
- ✅ Fotos acessíveis por 7 dias
- ✅ Pronto para produção

## 📝 Notas Técnicas

### Por que URLs Assinadas?

1. **Segurança**: Bucket pode ficar privado
2. **Controle**: URLs expiram automaticamente
3. **Compatibilidade**: Funciona com qualquer configuração de MinIO

### Alternativa (se quiser URLs públicas permanentes)

Se preferir URLs públicas permanentes (não recomendado):

1. Configure o bucket como público no MinIO Console
2. Em `core/storage.py`, mude:
```python
querystring_auth = False
default_acl = 'public-read'
custom_domain = 's3.spsystems.pro/fuza'
```

## 🆘 Troubleshooting

### Fotos ainda não aparecem?
1. Verifique se reiniciou o servidor
2. Confirme que fez um novo upload (fotos antigas têm URLs sem assinatura)
3. Cheque os logs

### URL com erro 403?
- A URL pode ter expirado (>7 dias)
- Regenere as URLs conforme exemplo acima

### Upload falha?
- Execute `python test_minio_connection.py`
- Verifique credenciais no `.env`

---

**✅ CORREÇÃO IMPLEMENTADA COM SUCESSO!**

Data: 04/11/2025
Desenvolvido por: Claude Code
