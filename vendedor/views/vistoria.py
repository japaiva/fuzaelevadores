# vendedor/views/vistoria.py - VERSÃO CORRIGIDA

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
    VistoriaFiltroForm
)

logger = logging.getLogger(__name__)


@login_required
def vistoria_list(request):
    """
    Lista de propostas para vistoria - apenas propostas aprovadas e não finalizadas
    """
    # Filtrar apenas propostas aprovadas E não finalizadas    
    propostas_query = Proposta.objects.filter(
        status='aprovado'
    ).exclude(
        status_obra='obra_ok'
    ).select_related('cliente', 'vendedor').order_by('data_proxima_vistoria', '-criado_em')

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
        'hoje': date.today(),  # Para comparações no template
    }
    
    return render(request, 'vendedor/vistoria/vistoria_list.html', context)


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
    
    return render(request, 'vendedor/vistoria/vistoria_proposta_detail.html', context)


@login_required
def vistoria_create(request, proposta_pk):
    """
    Criar nova vistoria no histórico - VERSÃO SIMPLIFICADA
    Como o lançamento já indica que aconteceu, não precisamos de vistoria_realizar separada
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
                
                # SEMPRE marcar como realizada, pois o lançamento indica que aconteceu
                vistoria.status_vistoria = 'realizada'
                vistoria.data_realizada = vistoria.data_agendada  # Data da vistoria é quando aconteceu
                
                # Salvar vistoria primeiro
                vistoria.save()
                
                # ATUALIZAR DADOS NA PROPOSTA conforme solicitado
                
                # 1. Atualizar status da obra se informado
                novo_status = request.POST.get('status_obra_novo', '')
                if novo_status:
                    # Atualizar status da obra diretamente
                    status_anterior = proposta.status_obra
                    proposta.status_obra = novo_status
                    vistoria.status_obra_novo = novo_status  # Salvar no registro da vistoria também
                
                # 2. Atualizar próxima vistoria na proposta
                if vistoria.proxima_vistoria_sugerida:
                    proposta.data_proxima_vistoria = vistoria.proxima_vistoria_sugerida
                else:
                    proposta.data_proxima_vistoria = None
                
                # 3. Atualizar previsão de conclusão da obra se informado
                previsao_entrega = request.POST.get('previsao_entrega_obra')
                if previsao_entrega:
                    from datetime import datetime
                    try:
                        proposta.previsao_conclusao_obra = datetime.strptime(previsao_entrega, '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Ignora se data inválida
                
                # 4. Salvar todas as alterações na proposta
                proposta.save()
                
                logger.info(
                    f"Vistoria criada e marcada como realizada para proposta {proposta.numero} "
                    f"pelo usuário {request.user.username}"
                )
                
                messages.success(request, 'Vistoria registrada com sucesso!')
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
    
    return render(request, 'vendedor/vistoria/vistoria_create.html', context)


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
    
    return render(request, 'vendedor/vistoria/vistoria_detail.html', context)


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
        from core.models import HistoricoProposta
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=f"Obra: {status_anterior or 'Aguardando'}",
            status_novo=f"Obra: {novo_status}",
            observacao="Alteração rápida via interface de vistoria",
            usuario=request.user
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