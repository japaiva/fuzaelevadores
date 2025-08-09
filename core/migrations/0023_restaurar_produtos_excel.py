from django.db import migrations
import openpyxl
import os

def restaurar_produtos_do_excel(apps, schema_editor):
    from django.conf import settings

    Produto = apps.get_model('core', 'Produto')
    caminho_arquivo = os.path.join(settings.BASE_DIR, 'core/static/produtos.xlsx')

    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return

    try:
        workbook = openpyxl.load_workbook(caminho_arquivo)
        planilha = workbook.active
    except Exception as e:
        print(f"❌ Erro ao abrir o arquivo: {e}")
        return

    produtos_criados = 0
    produtos_existentes = 0

    for linha in planilha.iter_rows(min_row=2, values_only=True):
        codigo, nome, unidade, estoque_minimo, estoque_maximo, ncm = linha

        if not codigo:
            continue

        codigo = str(codigo).strip()

        if Produto.objects.filter(codigo=codigo).exists():
            produtos_existentes += 1
            continue

        Produto.objects.create(
            codigo=codigo,
            nome=nome.strip() if nome else '',
            unidade=unidade.strip() if unidade else '',
            estoque_minimo=estoque_minimo or 0,
            estoque_maximo=estoque_maximo or 0,
            ncm=ncm.strip() if ncm else '',
        )
        produtos_criados += 1

    print(f"✅ Produtos criados: {produtos_criados}")
    print(f"ℹ️ Produtos já existentes (ignorados): {produtos_existentes}")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_recodificacao_completa_produtos'),
    ]

    operations = [
        migrations.RunPython(restaurar_produtos_do_excel),
    ]