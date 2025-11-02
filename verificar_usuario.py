#!/usr/bin/env python
# Script para verificar grupos do usuário

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuza_elevadores.settings')
django.setup()

from core.models import Usuario
from core.models import Tarefa

print("="*60)
print("VERIFICAÇÃO DE USUÁRIOS E TAREFAS")
print("="*60)

# Listar usuários
print("\n📋 USUÁRIOS CADASTRADOS:")
print("-"*60)
for user in Usuario.objects.all():
    grupos = ", ".join([g.name for g in user.groups.all()])
    print(f"• {user.username}")
    print(f"  Nível: {user.nivel}")
    print(f"  Grupos: {grupos or 'Nenhum'}")
    print()

# Listar tarefas
print("\n✅ TAREFAS CRIADAS:")
print("-"*60)
tarefas = Tarefa.objects.all()
if tarefas.exists():
    for tarefa in tarefas:
        print(f"• ID: {tarefa.id}")
        print(f"  Título: {tarefa.titulo}")
        print(f"  Status: {tarefa.status}")
        print(f"  Grupo destino: {tarefa.grupo_destino}")
        print(f"  Proposta: #{tarefa.proposta.numero if tarefa.proposta else 'N/A'}")
        print()
else:
    print("Nenhuma tarefa encontrada.")
    print("\nPossíveis motivos:")
    print("1. Nenhuma proposta foi aprovada ainda")
    print("2. O signal não foi executado")
    print("3. Grupo 'Engenharia' não existe")

print("\n" + "="*60)
