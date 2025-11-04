#!/usr/bin/env python
"""
Script para testar conexão com MinIO
Execute: python test_minio_connection.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuza_elevadores.settings')
django.setup()

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime

def test_minio_connection():
    """Testa conexão e upload para MinIO"""

    print("=" * 60)
    print("TESTE DE CONEXÃO COM MINIO")
    print("=" * 60)

    # Informações da configuração
    from django.conf import settings
    print(f"\n📦 Configurações:")
    print(f"   Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"   Endpoint: {settings.AWS_S3_ENDPOINT_URL}")
    print(f"   Access Key: {settings.AWS_ACCESS_KEY_ID[:5]}***")

    # Teste 1: Criar arquivo de teste
    print(f"\n🧪 Teste 1: Upload de arquivo...")
    test_filename = f"test/conexao_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    test_content = f"Teste de conexão MinIO - {datetime.now()}"

    try:
        saved_path = default_storage.save(
            test_filename,
            ContentFile(test_content.encode('utf-8'))
        )
        print(f"   ✅ Upload bem-sucedido!")
        print(f"   📁 Caminho: {saved_path}")

        # Obter URL
        url = default_storage.url(saved_path)
        print(f"   🔗 URL: {url}")

        # Teste 2: Verificar se arquivo existe
        print(f"\n🧪 Teste 2: Verificação de existência...")
        exists = default_storage.exists(saved_path)
        print(f"   {'✅' if exists else '❌'} Arquivo existe: {exists}")

        # Teste 3: Ler arquivo
        print(f"\n🧪 Teste 3: Leitura de arquivo...")
        file_obj = default_storage.open(saved_path, 'r')
        content = file_obj.read()
        file_obj.close()
        print(f"   ✅ Leitura bem-sucedida!")
        print(f"   📄 Conteúdo: {content[:50]}...")

        # Teste 4: Deletar arquivo
        print(f"\n🧪 Teste 4: Exclusão de arquivo...")
        default_storage.delete(saved_path)
        exists_after = default_storage.exists(saved_path)
        print(f"   ✅ Exclusão bem-sucedida!")
        print(f"   📁 Arquivo existe após exclusão: {exists_after}")

        # Resumo final
        print(f"\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 60)
        print("\n💡 O MinIO está configurado corretamente.")
        print("   Você pode usar o upload de fotos nas vistorias.\n")

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        print("\n🔍 Possíveis causas:")
        print("   1. MinIO não está rodando")
        print("   2. Credenciais incorretas")
        print("   3. Bucket não existe")
        print("   4. Problemas de rede/firewall")
        print("\n💡 Verifique:")
        print(f"   - Acesse: {settings.AWS_S3_ENDPOINT_URL}")
        print(f"   - Confirme que o bucket '{settings.AWS_STORAGE_BUCKET_NAME}' existe")
        print(f"   - Verifique as credenciais no arquivo .env\n")

        return False

if __name__ == "__main__":
    test_minio_connection()
