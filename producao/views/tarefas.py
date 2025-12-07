# producao/views/tarefas.py

"""
Views para gerenciamento de tarefas do sistema de workflow
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone

from core.models import Tarefa, HistoricoTarefa


@portal_producao
def lista_tarefas(request):
    """
    Lista tarefas do usuário ou do seu nível

    Sistema simplificado:
    - Tarefas atribuídas diretamente ao usuário
    - Tarefas atribuídas ao nível do usuário (ex: engenharia, compras)
    - Filtros por status, prioridade
    """
    usuario = request.user

    # Obter tarefas do usuário e do seu nível (sistema simplificado)
    tarefas = Tarefa.objects.filter(
        Q(usuario_destino=usuario) |  # Atribuídas diretamente
        Q(nivel_destino=usuario.nivel)  # Atribuídas ao nível do usuário
    ).select_related(
        'proposta',
        'requisicao',
        'lista_materiais',
        'usuario_destino',
        'criada_por',
        'concluida_por'
    ).order_by('status', '-prioridade', 'data_criacao')

    # Filtros
    status_filtro = request.GET.get('status', '')
    tipo_filtro = request.GET.get('tipo', '')
    prioridade_filtro = request.GET.get('prioridade', '')

    if status_filtro:
        tarefas = tarefas.filter(status=status_filtro)
    else:
        # Por padrão, não mostrar concluídas
        tarefas = tarefas.exclude(status='concluida')

    if tipo_filtro:
        tarefas = tarefas.filter(tipo=tipo_filtro)

    if prioridade_filtro:
        tarefas = tarefas.filter(prioridade=prioridade_filtro)

    # Estatísticas
    total_pendentes = Tarefa.objects.filter(
        Q(usuario_destino=usuario) | Q(nivel_destino=usuario.nivel),
        status='pendente'
    ).count()

    total_em_andamento = Tarefa.objects.filter(
        Q(usuario_destino=usuario) | Q(nivel_destino=usuario.nivel),
        status='em_andamento'
    ).count()

    total_atrasadas = Tarefa.objects.filter(
        Q(usuario_destino=usuario) | Q(nivel_destino=usuario.nivel),
        status__in=['pendente', 'em_andamento'],
        prazo__lt=timezone.now().date()
    ).count()

    context = {
        'tarefas': tarefas,
        'total_pendentes': total_pendentes,
        'total_em_andamento': total_em_andamento,
        'total_atrasadas': total_atrasadas,
        'status_filtro': status_filtro,
        'tipo_filtro': tipo_filtro,
        'prioridade_filtro': prioridade_filtro,
        'status_choices': Tarefa.STATUS_CHOICES,
        'tipo_choices': Tarefa.TIPO_CHOICES,
        'prioridade_choices': Tarefa.PRIORIDADE_CHOICES,
    }

    return render(request, 'producao/tarefas/lista.html', context)


@portal_producao
def detalhes_tarefa(request, tarefa_id):
    """
    Mostra detalhes de uma tarefa específica
    Sistema simplificado: verifica permissão por nível
    """
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)

    # Verificar se o usuário tem permissão para ver esta tarefa (sistema simplificado)
    usuario = request.user
    tem_permissao = (
        tarefa.usuario_destino == usuario or
        tarefa.nivel_destino == usuario.nivel or
        usuario.is_superuser or
        usuario.nivel in ['admin', 'gestor']
    )

    if not tem_permissao:
        messages.error(request, 'Você não tem permissão para visualizar esta tarefa.')
        return redirect('producao:tarefas')

    # Histórico da tarefa
    historico = tarefa.historico.all().order_by('-data')

    context = {
        'tarefa': tarefa,
        'historico': historico,
    }

    return render(request, 'producao/tarefas/detalhes.html', context)


@portal_producao
def iniciar_tarefa(request, tarefa_id):
    """
    Marca a tarefa como 'em_andamento'
    Sistema simplificado: verifica permissão por nível
    """
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    usuario = request.user

    # Verificar permissão (sistema simplificado)
    tem_permissao = (
        tarefa.usuario_destino == usuario or
        tarefa.nivel_destino == usuario.nivel or
        usuario.is_superuser
    )

    if not tem_permissao:
        messages.error(request, 'Você não tem permissão para iniciar esta tarefa.')
        return redirect('producao:tarefas')

    # Verificar status
    if tarefa.status != 'pendente':
        messages.warning(request, f'Esta tarefa já está {tarefa.get_status_display()}.')
        return redirect('producao:tarefa_detalhes', tarefa_id=tarefa_id)

    # Iniciar tarefa
    tarefa.iniciar(usuario)

    # Registrar no histórico
    HistoricoTarefa.objects.create(
        tarefa=tarefa,
        usuario=usuario,
        acao='iniciada',
        descricao=f'{usuario.get_full_name() or usuario.username} iniciou a tarefa'
    )

    messages.success(request, 'Tarefa iniciada com sucesso!')
    return redirect('producao:tarefa_detalhes', tarefa_id=tarefa_id)


@portal_producao
def concluir_tarefa(request, tarefa_id):
    """
    Marca a tarefa como concluída
    Sistema simplificado: verifica permissão por nível
    """
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    usuario = request.user

    # Verificar permissão (sistema simplificado)
    tem_permissao = (
        tarefa.usuario_destino == usuario or
        tarefa.nivel_destino == usuario.nivel or
        usuario.is_superuser
    )

    if not tem_permissao:
        messages.error(request, 'Você não tem permissão para concluir esta tarefa.')
        return redirect('producao:tarefas')

    # Verificar status
    if tarefa.status == 'concluida':
        messages.warning(request, 'Esta tarefa já está concluída.')
        return redirect('producao:tarefa_detalhes', tarefa_id=tarefa_id)

    if request.method == 'POST':
        observacoes = request.POST.get('observacoes', '')

        # Concluir tarefa
        tarefa.concluir(usuario, observacoes)

        # Registrar no histórico
        HistoricoTarefa.objects.create(
            tarefa=tarefa,
            usuario=usuario,
            acao='concluida',
            descricao=f'{usuario.get_full_name() or usuario.username} concluiu a tarefa'
        )

        messages.success(request, 'Tarefa concluída com sucesso!')
        return redirect('producao:tarefas')

    context = {
        'tarefa': tarefa,
    }

    return render(request, 'producao/tarefas/concluir.html', context)


@portal_producao
def cancelar_tarefa(request, tarefa_id):
    """
    Cancela uma tarefa
    """
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    usuario = request.user

    # Apenas gestor/admin ou quem criou pode cancelar
    pode_cancelar = (
        usuario.is_superuser or
        usuario.nivel in ['admin', 'gestor'] or
        tarefa.criada_por == usuario
    )

    if not pode_cancelar:
        messages.error(request, 'Você não tem permissão para cancelar esta tarefa.')
        return redirect('producao:tarefas')

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')

        # Cancelar tarefa
        tarefa.cancelar(usuario, motivo)

        # Registrar no histórico
        HistoricoTarefa.objects.create(
            tarefa=tarefa,
            usuario=usuario,
            acao='cancelada',
            descricao=f'{usuario.get_full_name() or usuario.username} cancelou a tarefa: {motivo}'
        )

        messages.success(request, 'Tarefa cancelada.')
        return redirect('producao:tarefas')

    context = {
        'tarefa': tarefa,
    }

    return render(request, 'producao/tarefas/cancelar.html', context)


@portal_producao
def contador_tarefas_pendentes(request):
    """
    API que retorna o número de tarefas pendentes do usuário
    Usado para atualizar badge no menu
    Sistema simplificado: filtra por nível
    """
    usuario = request.user

    pendentes = Tarefa.objects.filter(
        Q(usuario_destino=usuario) | Q(nivel_destino=usuario.nivel),
        status='pendente'
    ).count()

    return JsonResponse({'count': pendentes})
