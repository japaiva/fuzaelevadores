# core/views/status.py - VIEW ATUALIZADA PARA ALTERAÇÃO DE STATUS

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
import logging

from core.models import Proposta, HistoricoProposta
from core.forms import PropostaStatusForm

logger = logging.getLogger(__name__)

@login_required
# vendedor/views/propostas.py - Adicionar esta view

@login_required
def vendedor_proposta_alterar_status(request, pk):
    """
    Alterar status da proposta - Versão simplificada
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if request.method == 'POST':
        form = PropostaStatusForm(request.POST, instance=proposta)
        
        if form.is_valid():
            try:
                # Capturar dados antes do save
                status_anterior = proposta.status
                status_novo = form.cleaned_data['status']
                observacao = form.cleaned_data.get('observacao_status', '')
                data_vistoria = form.cleaned_data.get('data_vistoria_medicao_prevista')
                
                # Salvar proposta com novo status
                proposta = form.save()
                
                # Lógica específica para status aprovado
                if status_novo == 'aprovado' and data_vistoria:
                    # Definir data da próxima vistoria
                    proposta.data_proxima_vistoria = data_vistoria
                    
                    # Definir status da obra como aguardando medição
                    proposta.status_obra = ''  # Empty string = "Aguardando Medição"
                    
                    proposta.save()
                
                # Criar histórico da mudança
                from core.models import HistoricoProposta
                HistoricoProposta.objects.create(
                    proposta=proposta,
                    status_anterior=status_anterior,
                    status_novo=status_novo,
                    observacao=observacao or f"Status alterado para {proposta.get_status_display()}",
                    usuario=request.user
                )
                
                # Log da alteração
                logger.info(
                    f"Status da proposta {proposta.numero} alterado de "
                    f"{status_anterior} para {status_novo} pelo usuário {request.user.username}"
                )
                
                # Mensagem de sucesso personalizada
                if status_novo == 'aprovado':
                    messages.success(request, 
                        f'Proposta {proposta.numero} aprovada com sucesso! '
                    )
                elif status_novo == 'rejeitado':
                    messages.success(request, 
                        f'Proposta {proposta.numero} rejeitada.'
                    )
                else:
                    messages.success(request, 
                        f'Status da proposta {proposta.numero} alterado para {proposta.get_status_display()}'
                    )
                
                return redirect('vendedor:pedido_detail', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao alterar status da proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao alterar status: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados preenchidos.')
    else:
        form = PropostaStatusForm(instance=proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
        'base_template': 'vendedor/base_vendedor.html',
    }
    
    return render(request, 'shared/proposta_status.html', context)