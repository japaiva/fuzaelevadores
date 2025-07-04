# Generated by Django 5.1.7 on 2025-07-04 22:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_proposta_contrapeso_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposta',
            name='contrapeso',
            field=models.CharField(blank=True, choices=[('Traseiro', 'Traseiro'), ('Lateral', 'Lateral')], max_length=20, null=True, verbose_name='Contrapeso'),
        ),
        migrations.AlterField(
            model_name='proposta',
            name='tracao',
            field=models.CharField(blank=True, choices=[('1x1', '1x1'), ('2x1', '2x1')], max_length=10, null=True, verbose_name='Tração'),
        ),
        migrations.AlterField(
            model_name='proposta',
            name='vendedor',
            field=models.ForeignKey(blank=True, limit_choices_to={'nivel': 'vendedor'}, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='propostas_vendedor', to=settings.AUTH_USER_MODEL, verbose_name='Vendedor'),
        ),
    ]
