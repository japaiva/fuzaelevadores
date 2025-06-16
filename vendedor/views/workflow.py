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
                
                # Definir vendedor se for nova proposta
                if not editing:
                    proposta.vendedor = request.user
                    # vendedor_responsavel será definido automaticamente no save()
                
                proposta.save()
                
                # Log da ação
                acao = "atualizada" if editing else "criada"
                logger.info(f"Proposta {proposta.numero} {acao} pelo usuário {request.user.username}")
                
                # Mensagem de sucesso
                if editing:
                    messages.success(request, 
                        f'Dados do cliente/elevador da proposta {proposta.numero} atualizados com sucesso!'
                    )
                else:
                    messages.success(request, 
                        f'Proposta {proposta.numero} criada com sucesso! Prossiga para configurar a cabine.'
                    )
                
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
                
                messages.success(request, 
                    f'Dados da cabine/portas da proposta {proposta.numero} salvos com sucesso!'
                )
                
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
    """
    Etapa 3: Dados Comerciais
    NOVA FUNCIONALIDADE: valor_calculado, valor_base, valor_proposta
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
        form = PropostaComercialForm(request.POST, instance=proposta)
        
        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                
                # 🎯 NOVA LÓGICA: Sincronizar campos de valor
                
                # Se valor_proposta foi preenchido mas valor_base não, usar valor_calculado como base
                if proposta.valor_proposta and not proposta.valor_base and proposta.valor_calculado:
                    proposta.valor_base = proposta.valor_calculado
                
                # Se valor_proposta não foi preenchido, usar valor_base ou valor_calculado
                if not proposta.valor_proposta:
                    proposta.valor_proposta = proposta.valor_base or proposta.valor_calculado
                
                # Atualizar status se necessário
                if proposta.status == 'rascunho' and proposta.valor_proposta:
                    proposta.status = 'pendente'
                
                proposta.save()
                
                # Log da ação
                logger.info(
                    f"Etapa 3 da proposta {proposta.numero} salva pelo usuário {request.user.username}. "
                    f"Valor final: R$ {proposta.valor_proposta or 0:.2f}"
                )
                
                messages.success(request, 
                    f'Proposta {proposta.numero} finalizada com sucesso! '
                    f'Valor: R$ {proposta.valor_proposta:.2f}'
                )
                
                # Redirecionar para detalhes da proposta
                return redirect('vendedor:proposta_detail', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao finalizar proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao finalizar proposta: {str(e)}')
        else:
            messages.error(request, 
                'Erro no formulário. Verifique os campos destacados.'
            )
    else:
        form = PropostaComercialForm(instance=proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
        'pedido': proposta,  # ✅ Compatibilidade
        'editing': True,  # Step 3 sempre é edição
    }
    
    return render(request, 'vendedor/pedido_step3.html', context)


# === FUNÇÃO AUXILIAR PARA CALCULAR VALOR BASE ===

def _calcular_preco_base(proposta):
    """
    Função auxiliar para calcular preço base quando solicitado via botão
    NOVA FUNCIONALIDADE: Atualiza valor_calculado
    """
    try:
        # Verificar se proposta pode ter valores calculados
        if not proposta.pode_calcular_valores():
            return {
                'success': False,
                'error': 'Proposta não possui dados suficientes para cálculo'
            }
        
        # TODO: Implementar lógica real de cálculo baseada no motor de regras
        # Por enquanto, valor simulado baseado na capacidade
        valor_base_simulado = float(proposta.capacidade) * 150  # R$ 150 por kg
        
        # Ajustes por modelo
        multiplicadores = {
            'Passageiro': 1.2,
            'Carga': 1.0,
            'Monta Prato': 0.8,
            'Plataforma Acessibilidade': 1.5,
        }
        
        multiplicador = multiplicadores.get(proposta.modelo_elevador, 1.0)
        valor_calculado = Decimal(str(valor_base_simulado * multiplicador))
        
        # Atualizar proposta
        proposta.valor_calculado = valor_calculado
        
        # Se valor_base não existe, usar o calculado
        if not proposta.valor_base:
            proposta.valor_base = valor_calculado
        
        proposta.save()
        
        logger.info(f"Preço calculado para proposta {proposta.numero}: R$ {valor_calculado:.2f}")
        
        return {
            'success': True,
            'valor_calculado': float(valor_calculado),
            'valor_base': float(proposta.valor_base),
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular preço da proposta {proposta.numero}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@login_required
def api_calcular_preco(request, pk):
    """
    API para calcular preço via botão no Step 3
    NOVA FUNCIONALIDADE
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    # 🎯 REMOVIDO: filtro por vendedor
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.pode_calcular:
        return JsonResponse({
            'success': False, 
            'error': 'Proposta não pode ter valores calculados'
        })
    
    resultado = _calcular_preco_base(proposta)
    return JsonResponse(resultado)