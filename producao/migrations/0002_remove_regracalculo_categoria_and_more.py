# producao/migrations/0002_fix_regracalculo_removal.py
# Migração MANUAL para corrigir problemas de unique_together

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('producao', '0001_initial'),
    ]

    operations = [
        # 1. PRIMEIRO: Remover unique_together que usa 'categoria'
        migrations.AlterUniqueTogether(
            name='regracalculo',
            unique_together=set(),
        ),
        
        # 2. SEGUNDO: Remover os campos
        migrations.RemoveField(
            model_name='regracalculo',
            name='categoria',
        ),
        migrations.RemoveField(
            model_name='componentederivado',
            name='criado_por',
        ),
        migrations.RemoveField(
            model_name='historicoregra',
            name='regra',
        ),
        migrations.RemoveField(
            model_name='historicoregra',
            name='usuario',
        ),
        migrations.RemoveField(
            model_name='regracalculo',
            name='atualizado_por',
        ),
        migrations.RemoveField(
            model_name='regracalculo',
            name='criado_por',
        ),
        
        # 3. TERCEIRO: Deletar os modelos
        migrations.DeleteModel(
            name='CategoriaRegra',
        ),
        migrations.DeleteModel(
            name='ComponenteDerivado',
        ),
        migrations.DeleteModel(
            name='HistoricoRegra',
        ),
        migrations.DeleteModel(
            name='RegraCalculo',
        ),
    ]
