# vendedor/views/vistoria_medicao.py

import logging
import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from core.models import Proposta, VistoriaHistorico, criar_vaos_porta_automaticos
from core.forms.vistoria_medicao import VistoriaMedicaoForm, VaoPortaFormSet

logger = logging.getLogger(__name__)


@login_required
def vistoria_medicao_create(request, proposta_pk):
    """
    Criar vistoria de medição inicial - com formulário específico
    """
    proposta = get_object_or_404(Proposta, pk=proposta_pk)
    
    # Verificar se pode fazer medição
    if proposta.status != 'aprovado':
        messages.error(request, 
            f'Apenas propostas aprovadas podem ter medições. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:vistoria_list')
    
    # Verificar se já existe medição
    medicao_existente = VistoriaHistorico.objects.filter(
        proposta=proposta,
        tipo_vistoria='medicao',
        status_vistoria='realizada'
    ).first()
    
    if medicao_existente:
        messages.warning(request,
            f'Esta proposta já possui uma medição realizada em '
            f'{medicao_existente.data_realizada.strftime("%d/%m/%Y")}. '
            f'Use "Nova Vistoria" para acompanhamento.'
        )
        return redirect('vendedor:vistoria_proposta_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        form = VistoriaMedicaoForm(request.POST, proposta=proposta)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Salvar vistoria
                    vistoria = form.save(commit=False)
                    vistoria.proposta = proposta
                    vistoria.responsavel = request.user
                    vistoria.status_obra_anterior = proposta.status_obra
                    vistoria.data_agendada = date.today()  # Medição é realizada hoje
                    
                    # Capturar novo status da obra
                    novo_status = request.POST.get('status_obra_novo', '')
                    if novo_status:
                        vistoria.status_obra_novo = novo_status
                    
                    # Salvar vistoria primeiro
                    vistoria.save()

                    # Debug: Ver dados recebidos
                    logger.info("=== DEBUG VÃOS DE PORTA (Backend) ===")
                    for key, value in request.POST.items():
                        if 'vaos_porta' in key:
                            logger.info(f"{key} = {value}")

                    # Processar FormSet de vãos de porta
                    vaos_formset = VaoPortaFormSet(request.POST, instance=vistoria, prefix='vaos_porta')
                    logger.info(f"FormSet válido: {vaos_formset.is_valid()}")
                    logger.info(f"Número de forms no formset: {len(vaos_formset.forms)}")

                    if vaos_formset.is_valid():
                        # Debug: Ver dados de cada form antes de salvar
                        for i, form in enumerate(vaos_formset.forms):
                            logger.info(f"Form {i} cleaned_data: {form.cleaned_data}")

                        vaos_saved = vaos_formset.save()
                        logger.info(f"{len(vaos_saved)} vãos de porta salvos para vistoria {vistoria.pk}")

                        # Debug: Ver o que foi salvo
                        for vao in vaos_saved:
                            logger.info(f"Vão salvo: {vao.pavimento} - {vao.largura}m x {vao.altura}m")
                    else:
                        # Log dos erros do formset
                        logger.warning(f"Erros no formset de vãos: {vaos_formset.errors}")
                        logger.warning(f"Erros non-form: {vaos_formset.non_form_errors()}")
                    
                    # Atualizar dados na proposta
                    if novo_status:
                        proposta.status_obra = novo_status
                    
                    # Atualizar data de medição na proposta
                    proposta.data_vistoria_medicao = vistoria.data_realizada
                    
                    # Atualizar próxima vistoria
                    if vistoria.proxima_vistoria_sugerida:
                        proposta.data_proxima_vistoria = vistoria.proxima_vistoria_sugerida
                    
                    # Atualizar previsão de entrega
                    previsao_entrega = request.POST.get('previsao_entrega_obra')
                    if previsao_entrega:
                        from datetime import datetime
                        try:
                            proposta.previsao_conclusao_obra = datetime.strptime(
                                previsao_entrega, '%Y-%m-%d'
                            ).date()
                        except ValueError:
                            pass
                    
                    proposta.save()
                    
                    logger.info(
                        f"Medição inicial criada para proposta {proposta.numero} "
                        f"pelo usuário {request.user.username}"
                    )
                    
                    messages.success(request, 'Medição inicial registrada com sucesso!')
                    return redirect('vendedor:vistoria_proposta_detail', pk=proposta.pk)
                    
            except Exception as e:
                logger.error(f"Erro ao criar medição: {str(e)}")
                messages.error(request, f'Erro ao registrar medição: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados informados.')
    
    else:
        form = VistoriaMedicaoForm(proposta=proposta)

    # Criar FormSet vazio para vãos de porta (será populado via JavaScript)
    vaos_formset = VaoPortaFormSet(instance=None, prefix='vaos_porta')

    # Buscar especificações de andares da proposta
    portas_pavimento = proposta.portas_pavimento.all().order_by('andar')

    # Preparar dados dos andares para JavaScript
    andares_data = []
    for porta in portas_pavimento:
        andares_data.append({
            'andar': porta.andar,
            'nome_andar': porta.nome_andar,
            'largura': float(porta.largura) if porta.largura else 0,
            'altura': float(porta.altura) if porta.altura else 0,
            'modelo': porta.modelo or '',
            'material': porta.material or '',
        })

    context = {
        'form': form,
        'vaos_formset': vaos_formset,
        'proposta': proposta,
        'is_medicao': True,
        'numero_pavimentos': getattr(proposta, 'pavimentos', 0),
        'andares_data': json.dumps(andares_data),  # Serializar para JSON
    }

    return render(request, 'vendedor/vistoria/vistoria_medicao_create.html', context)


@login_required
def vistoria_medicao_detail(request, pk):
    """
    Detalhes de uma vistoria de medição - com todos os dados técnicos
    """
    vistoria = get_object_or_404(
        VistoriaHistorico, 
        pk=pk,
        tipo_vistoria='medicao'
    )
    
    # Buscar vãos de porta relacionados
    vaos_porta = vistoria.vaos_porta.all().order_by('id')  # Ordenar por ID (ordem de criação)

    context = {
        'vistoria': vistoria,
        'proposta': vistoria.proposta,
        'vaos_porta': vaos_porta,
        'is_medicao': True,
    }
    
    return render(request, 'vendedor/vistoria/vistoria_medicao_detail.html', context)


@login_required
def vistoria_medicao_edit(request, pk):
    """
    Editar medição (apenas se ainda não foi processada pela produção)
    """
    vistoria = get_object_or_404(
        VistoriaHistorico,
        pk=pk,
        tipo_vistoria='medicao'
    )
    
    # Verificar se pode editar
    if vistoria.status_vistoria != 'realizada':
        messages.error(request, 'Apenas medições realizadas podem ser editadas.')
        return redirect('vendedor:vistoria_medicao_detail', pk=vistoria.pk)
    
    # TODO: Adicionar verificação se já foi processada pela produção
    # if vistoria.processada_producao:
    #     messages.error(request, 'Esta medição já foi processada pela produção e não pode ser alterada.')
    #     return redirect('vendedor:vistoria_medicao_detail', pk=vistoria.pk)
    
    if request.method == 'POST':
        form = VistoriaMedicaoForm(request.POST, instance=vistoria, proposta=vistoria.proposta)
        vaos_formset = VaoPortaFormSet(request.POST, instance=vistoria, prefix='vaos_porta')

        if form.is_valid() and vaos_formset.is_valid():
            try:
                with transaction.atomic():
                    # Salvar vistoria atualizada
                    vistoria_atualizada = form.save(commit=False)
                    vistoria_atualizada.atualizado_por = request.user
                    vistoria_atualizada.save()
                    
                    # Salvar vãos de porta
                    vaos_formset.save()
                    
                    # Atualizar status da obra se necessário
                    novo_status = request.POST.get('status_obra_novo', '')
                    if novo_status and novo_status != vistoria.proposta.status_obra:
                        vistoria.proposta.status_obra = novo_status
                        vistoria.proposta.save()
                        
                        vistoria_atualizada.status_obra_novo = novo_status
                        vistoria_atualizada.save()
                    
                    logger.info(
                        f"Medição {vistoria.pk} editada pelo usuário {request.user.username}"
                    )
                    
                    messages.success(request, 'Medição atualizada com sucesso!')
                    return redirect('vendedor:vistoria_medicao_detail', pk=vistoria.pk)
                    
            except Exception as e:
                logger.error(f"Erro ao editar medição: {str(e)}")
                messages.error(request, f'Erro ao atualizar medição: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados informados.')
    
    else:
        form = VistoriaMedicaoForm(instance=vistoria, proposta=vistoria.proposta)
        vaos_formset = VaoPortaFormSet(instance=vistoria, prefix='vaos_porta')
    
    context = {
        'form': form,
        'vaos_formset': vaos_formset,
        'vistoria': vistoria,
        'proposta': vistoria.proposta,
        'is_medicao': True,
        'is_edit': True,
    }
    
    return render(request, 'vendedor/vistoria/vistoria_medicao_create.html', context)


@login_required 
def vistoria_primeira_medicao(request, proposta_pk):
    """
    Agendamento/realização da primeira medição
    Redirecionamento para o formulário de medição apropriado
    """
    proposta = get_object_or_404(Proposta, pk=proposta_pk)
    
    # Verificar se pode fazer primeira medição
    if proposta.status != 'aprovado':
        messages.error(request,
            f'Apenas propostas aprovadas podem ter medição. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:vistoria_list')
    
    # Se já tem medição, redirecionar para nova vistoria normal
    if proposta.data_vistoria_medicao:
        messages.info(request,
            'Esta proposta já possui medição inicial. '
            'Use "Nova Vistoria" para acompanhamento.'
        )
        return redirect('vendedor:vistoria_create', proposta_pk=proposta.pk)
    
    # Redirecionar para formulário de medição
    return redirect('vendedor:vistoria_medicao_create', proposta_pk=proposta.pk)