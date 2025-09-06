# core/views/status.py
"""
View compartilhada para alterar status de propostas
Usada tanto pelo vendedor quanto pela produção
✅ CORRIGIDO: Redirecionamento para lista + campo observacao_status
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from core.models import Proposta, HistoricoProposta
from core.forms.propostas import PropostaStatusForm

logger = logging.getLogger(__name__)


@login_required
def proposta_alterar_status(request, pk, redirect_view_name='proposta_list'):
    """
    View compartilhada para alterar status da proposta
    
    Args:
        pk: ID da proposta
        redirect_view_name: Nome da view para redirect após sucesso
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar permissões básicas
    user_level = getattr(request.user, 'nivel', 'vendedor')
    
    if request.method == 'POST':
        form = PropostaStatusForm(request.POST, instance=proposta, usuario=request.user)
        
        if form.is_valid():
            try:
                # Capturar status anterior
                status_anterior = proposta.status
                
                # Salvar nova proposta
                proposta = form.save(commit=False)
                proposta.atualizado_por = request.user
                proposta.save()
                
                # Registrar no histórico
                observacao = form.cleaned_data.get('observacao_status', '')
                if not observacao:
                    observacao = f'Status alterado para {proposta.get_status_display()}'
                
                HistoricoProposta.objects.create(
                    proposta=proposta,
                    status_anterior=status_anterior,
                    status_novo=proposta.status,
                    observacao=observacao,
                    usuario=request.user
                )
                
                # Log da ação
                logger.info(
                    f"Status da proposta {proposta.numero} alterado de '{status_anterior}' "
                    f"para '{proposta.status}' pelo usuário {request.user.username}"
                )
                
                messages.success(request,
                    f'Status da proposta {proposta.numero} alterado para '
                    f'"{proposta.get_status_display()}" com sucesso!'
                )
                
                # ✅ CORRIGIDO: Redirect adequado para lista vs detail
                if redirect_view_name in ['vendedor:proposta_list', 'producao:proposta_list']:
                    return redirect(redirect_view_name)
                else:
                    # Para views que precisam de parâmetros (detail)
                    return redirect(redirect_view_name, pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao alterar status da proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao alterar status: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados.')
    else:
        form = PropostaStatusForm(instance=proposta, usuario=request.user)
    
    # Preparar contexto
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'form': form,
        'user_level': user_level,
        'status_choices': Proposta.STATUS_CHOICES,
    }
    
    return render(request, 'shared/proposta_status.html', context)


@login_required  
def proposta_alterar_status_ajax(request, pk):
    """
    Versão AJAX para alterar status rapidamente
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        novo_status = request.POST.get('status')
        observacao = request.POST.get('observacao', '')
        
        # Validar status
        status_validos = [choice[0] for choice in Proposta.STATUS_CHOICES]
        if novo_status not in status_validos:
            return JsonResponse({'success': False, 'error': 'Status inválido'})
        
        # Capturar status anterior
        status_anterior = proposta.status
        
        # Atualizar proposta
        proposta.status = novo_status
        proposta.atualizado_por = request.user
        proposta.save()
        
        # Registrar no histórico
        if not observacao:
            observacao = f'Status alterado via AJAX'
        
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=status_anterior,
            status_novo=novo_status,
            observacao=observacao,
            usuario=request.user
        )
        
        # Log da ação
        logger.info(
            f"Status da proposta {proposta.numero} alterado via AJAX de '{status_anterior}' "
            f"para '{novo_status}' pelo usuário {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Status alterado para "{proposta.get_status_display()}"',
            'novo_status': novo_status,
            'novo_status_display': proposta.get_status_display(),
            'badge_class': proposta.status_badge_class,
        })
        
    except Exception as e:
        logger.error(f"Erro ao alterar status via AJAX da proposta {pk}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


# Para o vendedor - wrapper específico
@login_required
def vendedor_proposta_alterar_status(request, pk):
    """Wrapper para o vendedor - ✅ CORRIGIDO: vai para lista"""
    return proposta_alterar_status(request, pk, 'vendedor:proposta_list')


# Para a produção - wrapper específico  
@login_required
def producao_proposta_alterar_status(request, pk):
    """Wrapper para a produção - ✅ CORRIGIDO: vai para lista"""
    return proposta_alterar_status(request, pk, 'producao:proposta_list')