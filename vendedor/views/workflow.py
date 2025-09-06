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

from core.models import Proposta, Cliente, PortaPavimento
from core.forms.propostas import (
    PropostaClienteElevadorForm,
    PropostaCabinePortasForm,
    PropostaComercialForm
)

# ❌ REMOVIDO: Import que não existe
# from core.services.porta_pavimento import PortaPavimentoService

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
        'pedido': proposta,  # Compatibilidade com templates atuais
        'editing': editing,
    }
    
    return render(request, 'vendedor/proposta_step1.html', context)


@login_required
def proposta_step2(request, pk):
    """
    Etapa 2: Cabine + Portas + Portas Diferenciadas
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.pode_editar:
        messages.error(request, f'Proposta {proposta.numero} não pode ser editada.')
        return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        form = PropostaCabinePortasForm(request.POST, instance=proposta)
        
        if form.is_valid():
            try:
                proposta = form.save()
                
                # === LÓGICA CLEAN: Gerenciar portas diferenciadas ===
                portas_diferenciadas = request.POST.get('portas_diferenciadas') == 'on'
                tem_portas_individuais = PortaPavimento.objects.filter(proposta=proposta).exists()
                
                if portas_diferenciadas and not tem_portas_individuais:
                    # CRIAR registros individuais
                    criar_portas_individuais(proposta)
                
                elif not portas_diferenciadas and tem_portas_individuais:
                    # APAGAR registros individuais
                    PortaPavimento.objects.filter(proposta=proposta).delete()
                
                elif portas_diferenciadas and tem_portas_individuais:
                    # ATUALIZAR registros existentes
                    atualizar_portas_individuais(proposta, request.POST)
                
                logger.info(f"Etapa 2 da proposta {proposta.numero} salva pelo usuário {request.user.username}")
                return redirect('vendedor:proposta_step3', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao salvar etapa 2 da proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao salvar dados: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os campos destacados.')
    else:
        form = PropostaCabinePortasForm(instance=proposta)
    
    # Dados para o template
    tem_portas_individuais = PortaPavimento.objects.filter(proposta=proposta).exists()
    portas_individuais = PortaPavimento.objects.filter(proposta=proposta).order_by('andar') if tem_portas_individuais else []
    
    context = {
        'form': form,
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'editing': True,
        'tem_portas_individuais': tem_portas_individuais,
        'portas_individuais': portas_individuais,
    }
    
    return render(request, 'vendedor/proposta_step2.html', context)


@login_required
def proposta_step3(request, pk):
    """
    Etapa 3: Dados Comerciais
    """
    proposta = get_object_or_404(Proposta, pk=pk)

    if not proposta.pode_editar:
        messages.error(request, 
            f'Proposta {proposta.numero} não pode ser editada. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:proposta_list')

    if request.method == 'POST':
        form = PropostaComercialForm(request.POST, instance=proposta)

        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                proposta.save() 
                logger.info(
                    f"Etapa 3 da proposta {proposta.numero} salva pelo usuário {request.user.username}. "
                    f"Valor final: R$ {proposta.valor_proposta or 0:.2f}"
                )
                return redirect('vendedor:proposta_list')
            except Exception as e:
                logger.error(f"Erro ao finalizar proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao finalizar proposta: {str(e)}')
        else:
            logger.error(f"Erro de validação no formulário da Etapa 3 da proposta {proposta.numero}. Erros: {form.errors}")
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

    return render(request, 'vendedor/proposta_step3.html', context)


# === FUNÇÕES AUXILIARES ===

def criar_portas_individuais(proposta):
    """
    Criar registros individuais baseados na proposta
    ✅ CORRIGIDO: Só modelo e material
    """
    for andar in range(proposta.pavimentos):
        PortaPavimento.objects.create(
            proposta=proposta,
            andar=andar,
            modelo=proposta.modelo_porta_pavimento,
            material=proposta.material_porta_pavimento,
            # ✅ REMOVIDO: largura e altura (não existem mais no modelo)
        )

def atualizar_portas_individuais(proposta, post_data):
    """
    Atualizar registros individuais com dados do POST
    ✅ CORRIGIDO: Só modelo e material
    """
    portas = PortaPavimento.objects.filter(proposta=proposta)
    
    for porta in portas:
        porta.modelo = post_data.get(f'porta_modelo_{porta.andar}', porta.modelo)
        porta.material = post_data.get(f'porta_material_{porta.andar}', porta.material)
        porta.save()

# === FUNÇÕES LEGADAS (não usadas mais, podem ser removidas) ===

def criar_portas_padrao_para_todos_pavimentos(proposta):
    """
    ❌ FUNÇÃO LEGADA - não é mais usada
    Pode ser removida
    """
    PortaPavimento.objects.filter(proposta=proposta).delete()
    
    for andar in range(proposta.pavimentos):
        PortaPavimento.objects.create(
            proposta=proposta,
            andar=andar,
            modelo=proposta.modelo_porta_pavimento,
            material=proposta.material_porta_pavimento,
        )