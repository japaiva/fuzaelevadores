# Generated manually for data migration

from django.db import migrations


def migrate_status_data(apps, schema_editor):
    """
    Migra dados de status_producao para status_financeiro:
    - Se status_producao era 'liberado', copia para status_financeiro
    - Reseta status_producao para '' (Aguardando)
    """
    Proposta = apps.get_model('core', 'Proposta')

    # Copiar 'liberado' de status_producao para status_financeiro
    propostas_liberadas = Proposta.objects.filter(status_producao='liberado')
    for proposta in propostas_liberadas:
        proposta.status_financeiro = 'liberado'
        proposta.status_producao = ''
        proposta.save()


def reverse_migration(apps, schema_editor):
    """Reverter migração (opcional)"""
    Proposta = apps.get_model('core', 'Proposta')

    # Reverter: se status_financeiro='liberado', voltar para status_producao
    propostas_liberadas = Proposta.objects.filter(status_financeiro='liberado')
    for proposta in propostas_liberadas:
        proposta.status_producao = 'liberado'
        proposta.status_financeiro = ''
        proposta.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_add_status_financeiro'),
    ]

    operations = [
        migrations.RunPython(migrate_status_data, reverse_migration),
    ]
