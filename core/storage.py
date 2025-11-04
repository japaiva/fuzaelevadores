# core/storage.py
"""
Storage customizado para MinIO usando django-storages
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MinioStorage(S3Boto3Storage):
    """
    Storage customizado para MinIO.
    Usa as configurações AWS_* do settings.py

    IMPORTANTE: Usa URLs assinadas (presigned URLs) que expiram em 7 dias.
    Isso garante que as fotos sejam acessíveis mesmo sem permissões públicas no bucket.
    """
    # Configurações do MinIO
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    file_overwrite = False
    object_parameters = {'CacheControl': 'max-age=86400'}
    # Usar URLs assinadas para garantir acesso
    querystring_auth = True
    querystring_expire = 604800  # 7 dias em segundos
    signature_version = 's3v4'
    region_name = 'us-east-1'
    # Não definir custom_domain ao usar URLs assinadas
    # custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
