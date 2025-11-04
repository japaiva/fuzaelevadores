# Sistema de Upload de Fotos para Vistorias

## Visão Geral

O sistema permite fazer upload de múltiplas fotos durante o registro de vistorias, armazenando-as no MinIO (storage S3-compatible).

## Arquivos Modificados/Criados

### 1. Storage MinIO
- **Arquivo**: `core/storage.py` (NOVO)
- **Função**: Storage customizado para integração com MinIO usando django-storages

### 2. Formulário de Vistoria
- **Arquivo**: `core/forms/vistoria.py`
- **Mudanças**: Adicionado campo `fotos` com suporte para múltiplos arquivos

### 3. View de Vistoria
- **Arquivo**: `vendedor/views/vistoria.py`
- **Mudanças**:
  - Adicionada função `processar_upload_fotos()` para gerenciar upload
  - Atualizada `vistoria_create()` para processar fotos do formulário

### 4. Template de Criação
- **Arquivo**: `templates/vendedor/vistoria/vistoria_create.html`
- **Mudanças**:
  - Adicionado `enctype="multipart/form-data"` no form
  - Adicionado campo de upload de fotos com preview
  - JavaScript para preview das imagens antes do upload

### 5. Template de Detalhes
- **Arquivo**: `templates/vendedor/vistoria/vistoria_detail.html`
- **Mudanças**:
  - Adicionada seção de galeria de fotos
  - Estilos CSS para exibição das fotos

## Configuração do MinIO

### 1. Variáveis de Ambiente
Configure as seguintes variáveis no arquivo `.env`:

```bash
AWS_ACCESS_KEY_ID=seu-access-key-minio
AWS_SECRET_ACCESS_KEY=sua-secret-key-minio
AWS_STORAGE_BUCKET_NAME=fuza-elevadores
AWS_S3_ENDPOINT_URL=http://localhost:9000  # Ajuste para seu servidor MinIO
```

### 2. Instalar MinIO (se ainda não tiver)

**Docker**:
```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=sua-senha-aqui" \
  minio/minio server /data --console-address ":9001"
```

**Acesse o console**: http://localhost:9001

### 3. Criar Bucket
1. Acesse o console do MinIO
2. Crie um bucket chamado `fuza-elevadores` (ou o nome definido em `AWS_STORAGE_BUCKET_NAME`)
3. Configure as permissões do bucket para permitir leitura pública (se necessário)

## Como Usar

### 1. Ao Criar uma Vistoria

1. Acesse a tela de criação de vistoria
2. Preencha os dados normais da vistoria
3. No campo "Fotos da Vistoria", clique em "Escolher arquivos"
4. Selecione uma ou múltiplas fotos
5. Visualize o preview das fotos selecionadas
6. Clique em "Registrar Vistoria"

As fotos serão enviadas para o MinIO e as URLs serão salvas no campo `fotos_anexos` da vistoria.

### 2. Visualizar Fotos

1. Acesse os detalhes de uma vistoria que possui fotos
2. Role até a seção "Fotos da Vistoria"
3. Clique em qualquer foto para abrir em tamanho maior em nova aba

## Estrutura de Armazenamento

As fotos são organizadas no MinIO da seguinte forma:

```
bucket: fuza-elevadores/
  └── vistorias/
      └── [numero-proposta]/
          ├── [uuid1].jpg
          ├── [uuid2].png
          └── [uuid3].heic
```

## Estrutura de Dados

### Campo `fotos_anexos` (JSONField)

```json
[
  {
    "url": "http://minio:9000/fuza-elevadores/vistorias/PROP-2024-001/abc123.jpg",
    "nome": "foto_fosso.jpg",
    "tamanho": 245678,
    "caminho": "vistorias/PROP-2024-001/abc123.jpg"
  },
  {
    "url": "http://minio:9000/fuza-elevadores/vistorias/PROP-2024-001/def456.png",
    "nome": "foto_cabine.png",
    "tamanho": 189234,
    "caminho": "vistorias/PROP-2024-001/def456.png"
  }
]
```

## Formatos Aceitos

- JPG / JPEG
- PNG
- HEIC (formato nativo do iPhone)
- Outros formatos de imagem suportados pelo navegador

## Próximos Passos (Opcional)

### Melhorias Futuras

1. **Compressão de Imagens**: Adicionar compressão automática antes do upload
2. **Galeria com Lightbox**: Integrar biblioteca como PhotoSwipe ou Lightbox2
3. **Upload Progressivo**: Mostrar barra de progresso durante upload
4. **Limite de Tamanho**: Adicionar validação de tamanho máximo por foto
5. **Exclusão de Fotos**: Permitir remover fotos individualmente
6. **Anotações**: Permitir adicionar descrições/anotações em cada foto

### Exemplo de Compressão (usando Pillow)

```python
from PIL import Image
from io import BytesIO

def comprimir_imagem(imagem, qualidade=85):
    """Comprime imagem antes do upload"""
    img = Image.open(imagem)

    # Converter RGBA para RGB se necessário
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    # Redimensionar se muito grande
    max_size = (1920, 1920)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Salvar com compressão
    output = BytesIO()
    img.save(output, format='JPEG', quality=qualidade, optimize=True)
    output.seek(0)

    return output
```

## Troubleshooting

### Erro: "ConnectionError: [Errno 111] Connection refused"
- Verifique se o MinIO está rodando
- Confirme o endpoint correto em `AWS_S3_ENDPOINT_URL`

### Fotos não aparecem
- Verifique as permissões do bucket no MinIO
- Confirme que `AWS_DEFAULT_ACL = 'public-read'` está configurado no settings.py

### Upload muito lento
- Considere adicionar compressão de imagens
- Verifique a conexão de rede com o servidor MinIO

## Segurança

### Recomendações de Produção

1. Use HTTPS para o endpoint do MinIO
2. Configure CORS adequadamente
3. Implemente autenticação de acesso às fotos
4. Faça backup regular do bucket
5. Configure lifecycle policies para arquivos antigos

## Suporte

Para dúvidas ou problemas, consulte:
- Documentação do django-storages: https://django-storages.readthedocs.io/
- Documentação do MinIO: https://min.io/docs/minio/
