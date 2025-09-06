# vendas/views/vistoria.py

"""
Views para o módulo de vistoria - acompanhamento da obra
"""

import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.http import JsonResponse

from core.models import Proposta, VistoriaHistorico
from core.forms import (
    PropostaVistoriaForm, 
    VistoriaHistoricoForm, 
    VistoriaRealizadaForm,
    VistoriaFiltroForm
)

logger = logging.getLogger(__name__)


@login_required
def vistoria_list(request):
    """
    Lista de propostas para vistoria - apenas propostas aprovadas
    """
    # Filtrar apenas propostas aprovadas
    propostas_query = Proposta.objects.filter(
        status='aprovado'
    ).select_related('cliente', 'vendedor').order_by('-data_proxima_vistoria', '-criado_em')
    
    # Aplicar filtros do formulário
    form = VistoriaFiltroForm(request.GET)
    if form.is_valid():
        
        # Filtro por status da obra
        if form.cleaned_data.get('status_obra'):
            propostas_query = propostas_query.filter(status_obra=form.cleaned_data['status_obra'])
        
        # Filtro por responsável
        if form.cleaned_data.get('responsavel'):
            propostas_query = propostas_query.filter(
                vistorias__responsavel=form.cleaned_data['responsavel']
            ).distinct()
        
        # Filtro por período de vistoria
        periodo = form.cleaned_data.get('periodo_vistoria')
        if periodo:
            hoje = date.today()
            if periodo == 'vencidas':
                propostas_query = propostas_query.filter(
                    data_proxima_vistoria__lt=hoje
                )
            elif periodo == 'hoje':
                propostas_query = propostas_query.filter(
                    data_proxima_vistoria=hoje
                )
            elif periodo == 'semana':
                fim_semana = hoje + timedelta(days=7)
                propostas_query = propostas_query.filter(
                    data_proxima_vistoria__lte=fim_semana,
                    data_proxima_vistoria__gte=hoje
                )
            elif periodo == 'mes':
                fim_mes = hoje + timedelta(days=30)
                propostas_query = propostas_query.filter(
                    data_proxima_vistoria__lte=fim_mes,
                    data_proxima_vistoria__gte=hoje
                )
        
        # Busca textual
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            propostas_query = propostas_query.filter(
                Q(numero__icontains=query) |
                Q(nome_projeto__icontains=query) |
                Q(cliente__nome__icontains=query) |
                Q(cliente__nome_fantasia__icontains=query)
            )
    
    # Adicionar informações de vistoria
    propostas_query = propostas_query.annotate(
        total_vistorias=Count('vistorias'),
        ultima_vistoria=Max('vistorias__data_realizada')
    )
    
    # Paginação
    paginator = Paginator(propostas_query, 15)
    page = request.GET.get('page', 1)
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    # Estatísticas rápidas
    estatisticas = {
        'total_propostas': propostas_query.count(),
        'sem_vistoria': propostas_query.filter(status_obra='').count(),
        'medicao_ok': propostas_query.filter(status_obra='medicao_ok').count(),
        'em_vistoria': propostas_query.filter(status_obra='em_vistoria').count(),
        'obra_ok': propostas_query.filter(status_obra='obra_ok').count(),
        'vencidas': propostas_query.filter(
            data_proxima_vistoria__lt=date.today()
        ).count(),
    }
    
    context = {
        'propostas': propostas,
        'form': form,
        'estatisticas': estatisticas,
    }
    
    return render(request, 'vendas/vistoria/vistoria_list.html', context)


@login_required
def vistoria_proposta_detail(request, pk):
    """
    Detalhes da proposta para vistoria - com histórico de vistorias
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar se pode fazer vistoria
    if proposta.status != 'aprovado':
        messages.error(request, 
            f'Apenas propostas aprovadas podem ter vistorias. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:vistoria_list')
    
    # Histórico de vistorias
    vistorias = VistoriaHistorico.objects.filter(
        proposta=proposta
    ).order_by('-data_agendada')
    
    context = {
        'proposta': proposta,
        'vistorias': vistorias,
        'pode_agendar_vistoria': proposta.pode_agendar_vistoria,
    }
    
    return render(request, 'vendas/vistoria/vistoria_proposta_detail.html', context)


@login_required
def vistoria_agendar_primeira(request, pk):
    """
    Agendar primeira vistoria - altera dados da proposta
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.pode_agendar_vistoria:
        messages.error(request, 'Esta proposta não pode ter vistoria agendada.')
        return redirect('vendedor:vistoria_list')
    
    if request.method == 'POST':
        form = PropostaVistoriaForm(request.POST, instance=proposta)
        
        if form.is_valid():
            try:
                proposta = form.save()
                
                # Criar primeiro registro no histórico se data foi informada
                if proposta.data_vistoria_medicao:
                    VistoriaHistorico.objects.create(
                        proposta=proposta,
                        responsavel=request.user,
                        data_agendada=proposta.data_vistoria_medicao,
                        tipo_vistoria='medicao',
                        observacoes='Primeira vistoria para medição',
                        status_obra_anterior='',
                        status_obra_novo=proposta.status_obra or '',
                        proxima_vistoria_sugerida=proposta.data_proxima_vistoria,
                        status_vistoria='realizada' if proposta.status_obra else 'agendada'
                    )
                
                logger.info(
                    f"Primeira vistoria agendada para proposta {proposta.numero} "
                    f"pelo usuário {request.user.username}"
                )
                
                messages.success(request, 
                    f'Vistoria agendada para proposta {proposta.numero}!'
                )
                
                return redirect('vendedor:vistoria_proposta_detail', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao agendar vistoria: {str(e)}")
                messages.error(request, f'Erro ao agendar vistoria: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados.')
    else:
        form = PropostaVistoriaForm(instance=proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
    }
    
    return render(request, 'vendas/vistoria/vistoria_agendar_primeira.html', context)


@login_required
def vistoria_create(request, proposta_pk):
    """
    Criar nova vistoria no histórico
    """
    proposta = get_object_or_404(Proposta, pk=proposta_pk)
    
    if request.method == 'POST':
        form = VistoriaHistoricoForm(request.POST, proposta=proposta)
        
        if form.is_valid():
            try:
                vistoria = form.save(commit=False)
                vistoria.proposta = proposta
                vistoria.responsavel = request.user
                vistoria.status_obra_anterior = proposta.status_obra
                vistoria.save()
                
                # Atualizar status da obra se informado
                novo_status = form.cleaned_data.get('status_obra_novo')
                if novo_status:
                    from core.models import atualizar_status_obra_proposta
                    atualizar_status_obra_proposta(
                        proposta, 
                        novo_status, 
                        request.user,
                        f"Alterado via vistoria de {vistoria.data_agendada.strftime('%d/%m/%Y')}"
                    )
                
                # Atualizar próxima vistoria na proposta
                if vistoria.proxima_vistoria_sugerida:
                    proposta.data_proxima_vistoria = vistoria.proxima_vistoria_sugerida
                    proposta.save()
                
                logger.info(
                    f"Vistoria criada para proposta {proposta.numero} "
                    f"pelo usuário {request.user.username}"
                )
                
                messages.success(request, 'Vistoria agendada com sucesso!')
                return redirect('vendedor:vistoria_proposta_detail', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao criar vistoria: {str(e)}")
                messages.error(request, f'Erro ao criar vistoria: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados.')
    else:
        form = VistoriaHistoricoForm(proposta=proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
    }
    
    return render(request, 'vendas/vistoria/vistoria_create.html', context)


@login_required
def vistoria_realizar(request, pk):
    """
    Marcar vistoria como realizada
    """
    vistoria = get_object_or_404(VistoriaHistorico, pk=pk)
    
    if not vistoria.pode_realizar():
        messages.error(request, 'Esta vistoria não pode ser marcada como realizada.')
        return redirect('vendedor:vistoria_proposta_detail', pk=vistoria.proposta.pk)
    
    if request.method == 'POST':
        form = VistoriaRealizadaForm(request.POST, instance=vistoria)
        
        if form.is_valid():
            try:
                vistoria = form.save(commit=False)
                vistoria.status_vistoria = 'realizada'
                vistoria.atualizado_por = request.user
                vistoria.save()
                
                # Atualizar status da obra se informado
                novo_status = form.cleaned_data.get('status_obra_novo')
                if novo_status:
                    from core.models import atualizar_status_obra_proposta
                    atualizar_status_obra_proposta(
                        vistoria.proposta, 
                        novo_status, 
                        request.user,
                        f"Alterado via vistoria realizada em {vistoria.data_realizada.strftime('%d/%m/%Y')}"
                    )
                
                # Atualizar próxima vistoria na proposta
                if vistoria.proxima_vistoria_sugerida:
                    vistoria.proposta.data_proxima_vistoria = vistoria.proxima_vistoria_sugerida
                    vistoria.proposta.save()
                
                logger.info(
                    f"Vistoria {vistoria.pk} marcada como realizada "
                    f"pelo usuário {request.user.username}"
                )
                
                messages.success(request, 'Vistoria marcada como realizada!')
                return redirect('vendedor:vistoria_proposta_detail', pk=vistoria.proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao realizar vistoria: {str(e)}")
                messages.error(request, f'Erro ao realizar vistoria: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados.')
    else:
        form = VistoriaRealizadaForm(instance=vistoria)
    
    context = {
        'form': form,
        'vistoria': vistoria,
        'proposta': vistoria.proposta,
    }
    
    return render(request, 'vendas/vistoria/vistoria_realizar.html', context)


@login_required
def vistoria_detail(request, pk):
    """
    Detalhes de uma vistoria específica
    """
    vistoria = get_object_or_404(VistoriaHistorico, pk=pk)
    
    context = {
        'vistoria': vistoria,
        'proposta': vistoria.proposta,
    }
    
    return render(request, 'vendas/vistoria/vistoria_detail.html', context)


@login_required
def vistoria_cancelar(request, pk):
    """
    Cancelar vistoria agendada
    """
    vistoria = get_object_or_404(VistoriaHistorico, pk=pk)
    
    if not vistoria.pode_cancelar():
        messages.error(request, 'Esta vistoria não pode ser cancelada.')
        return redirect('vendedor:vistoria_proposta_detail', pk=vistoria.proposta.pk)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        try:
            vistoria.status_vistoria = 'cancelada'
            vistoria.observacoes += f"\n\nCANCELADA: {motivo}" if motivo else "\n\nVistoria cancelada"
            vistoria.atualizado_por = request.user
            vistoria.save()
            
            logger.info(
                f"Vistoria {vistoria.pk} cancelada pelo usuário {request.user.username}. "
                f"Motivo: {motivo}"
            )
            
            messages.success(request, 'Vistoria cancelada com sucesso!')
            
        except Exception as e:
            logger.error(f"Erro ao cancelar vistoria: {str(e)}")
            messages.error(request, f'Erro ao cancelar vistoria: {str(e)}')
    
    return redirect('vendedor:vistoria_proposta_detail', pk=vistoria.proposta.pk)


@login_required
def vistoria_calendario(request):
    """
    Calendário de vistorias agendadas
    """
    # Buscar vistorias agendadas dos próximos 30 dias
    hoje = date.today()
    fim_periodo = hoje + timedelta(days=30)
    
    vistorias = VistoriaHistorico.objects.filter(
        data_agendada__gte=hoje,
        data_agendada__lte=fim_periodo,
        status_vistoria='agendada'
    ).select_related('proposta', 'responsavel').order_by('data_agendada')
    
    # Organizar por data
    vistorias_por_data = {}
    for vistoria in vistorias:
        data_str = vistoria.data_agendada.strftime('%Y-%m-%d')
        if data_str not in vistorias_por_data:
            vistorias_por_data[data_str] = []
        vistorias_por_data[data_str].append(vistoria)
    
    context = {
        'vistorias_por_data': vistorias_por_data,
        'periodo_inicio': hoje,
        'periodo_fim': fim_periodo,
    }
    
    return render(request, 'vendas/vistoria/vistoria_calendario.html', context)


# === APIs AJAX ===

@login_required
def api_vistoria_quick_status(request, proposta_pk):
    """
    API para alterar rapidamente o status da obra
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        proposta = get_object_or_404(Proposta, pk=proposta_pk)
        novo_status = request.POST.get('status_obra', '')
        
        if novo_status not in [choice[0] for choice in Proposta.STATUS_OBRA_CHOICES]:
            return JsonResponse({'success': False, 'error': 'Status inválido'})
        
        status_anterior = proposta.status_obra
        proposta.status_obra = novo_status
        proposta.save()
        
        # Criar entrada no histórico
        from core.models import atualizar_status_obra_proposta
        atualizar_status_obra_proposta(
            proposta, 
            novo_status, 
            request.user,
            "Alteração rápida via interface de vistoria"
        )
        
        return JsonResponse({
            'success': True,
            'status_anterior': status_anterior,
            'status_novo': novo_status,
            'status_display': proposta.get_status_obra_display(),
            'badge_class': proposta.status_obra_badge_class
        })
        
    except Exception as e:
        logger.error(f"Erro na alteração rápida de status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})