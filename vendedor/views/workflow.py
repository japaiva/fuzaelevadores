# vendedor/views/workflow.py

"""
Views para o workflow de criação/edição de propostas em 3 etapas
NOVA FUNCIONALIDADE: Campos valor_calculado, valor_base, valor_proposta
"""

import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from core.models import Proposta, Cliente
from core.forms.propostas import (
    PropostaClienteElevadorForm,
    PropostaCabinePortasForm,
    PropostaComercialForm
)

logger = logging.getLogger(__name__)


@login_required
def proposta_step1(request, pk=None):
    """
    Etapa 1: Cliente + Elevador + Poço
    - pk=None: Criar nova proposta
    - pk=UUID: Editar proposta existente
    """
    
    # Determinar se é edição ou criação
    editing = pk is not None
    proposta = None
    
    if editing:
        # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode editar
        proposta = get_object_or_404(Proposta, pk=pk)
        
        # Verificar se pode editar
        if not proposta.pode_editar:
            messages.error(request, 
                f'Proposta {proposta.numero} não pode ser editada. '
                f'Status atual: {proposta.get_status_display()}'
            )
            return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        form = PropostaClienteElevadorForm(request.POST, instance=proposta)
        
        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                
                proposta.save()
                
                # Log da ação
                acao = "atualizada" if editing else "criada"
                logger.info(f"Proposta {proposta.numero} {acao} pelo usuário {request.user.username}")
                
                
                # Redirecionar para próxima etapa
                return redirect('vendedor:proposta_step2', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao salvar proposta: {str(e)}")
                messages.error(request, f'Erro ao salvar proposta: {str(e)}')
        else:
            messages.error(request, 
                'Erro no formulário. Verifique os campos destacados.'
            )
    else:
        form = PropostaClienteElevadorForm(instance=proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
        'pedido': proposta,  # ✅ Compatibilidade com templates atuais
        'editing': editing,
    }
    
    return render(request, 'vendedor/pedido_step1.html', context)


@login_required
def proposta_step2(request, pk):
    """
    Etapa 2: Cabine + Portas
    """
    # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode editar
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar se pode editar
    if not proposta.pode_editar:
        messages.error(request, 
            f'Proposta {proposta.numero} não pode ser editada. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        form = PropostaCabinePortasForm(request.POST, instance=proposta)
        
        if form.is_valid():
            try:
                proposta = form.save()
                
                # Log da ação
                logger.info(f"Etapa 2 da proposta {proposta.numero} salva pelo usuário {request.user.username}")
                
                
                # Redirecionar para próxima etapa
                return redirect('vendedor:proposta_step3', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao salvar etapa 2 da proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao salvar dados: {str(e)}')
        else:
            messages.error(request, 
                'Erro no formulário. Verifique os campos destacados.'
            )
    else:
        form = PropostaCabinePortasForm(instance=proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
        'pedido': proposta,  # ✅ Compatibilidade
        'editing': True,  # Step 2 sempre é edição
    }
    
    return render(request, 'vendedor/pedido_step2.html', context)


@login_required
def proposta_step3(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)

    # Verificar se pode editar
    if not proposta.pode_editar:
        messages.error(request, 
            f'Proposta {proposta.numero} não pode ser editada. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:pedido_list')

    if request.method == 'POST':
        form = PropostaComercialForm(request.POST, instance=proposta)

        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                # ... (sua lógica de salvamento) ...
                proposta.save() 
                logger.info(
                    f"Etapa 3 da proposta {proposta.numero} salva pelo usuário {request.user.username}. "
                    f"Valor final: R$ {proposta.valor_proposta or 0:.2f}"
                )
                return redirect('vendedor:pedido_list')
            except Exception as e:
                logger.error(f"Erro ao finalizar proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao finalizar proposta: {str(e)}')
        else:
            # --- Ponto de depuração: Adicione estas linhas ---
            logger.error(f"Erro de validação no formulário da Etapa 3 da proposta {proposta.numero}. Erros: {form.errors}")
            # Se quiser depurar interativamente (o servidor vai pausar aqui):
            # import pdb; pdb.set_trace() 
            # --------------------------------------------------
            messages.error(request, 
                'Erro no formulário. Verifique os campos destacados.'
            )
    else:
        form = PropostaComercialForm(instance=proposta)

    context = {
        'form': form,
        'proposta': proposta,
        'pedido': proposta,
        'editing': True,
    }

    return render(request, 'vendedor/pedido_step3.html', context)
