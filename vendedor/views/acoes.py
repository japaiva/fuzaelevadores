# vendedor/views/acoes.py

"""
Views para ações das propostas: calcular, duplicar, enviar, etc.
"""

import logging
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from core.models import Proposta, AnexoProposta, HistoricoProposta

logger = logging.getLogger(__name__)


@login_required
def proposta_calcular(request, pk):
    """
    Executar cálculos da proposta
    ATUALIZADA: Usar novos campos de valor
    """
    # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode calcular
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.pode_calcular():  # ✅ CORRIGIDO: método correto
        messages.error(request,
            f'Proposta {proposta.numero} não pode ter valores calculados. '
            f'Verifique se todos os dados obrigatórios foram preenchidos.'
        )
        return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        try:
            # Importar serviço de cálculo
            from core.services.calculo_pedido import CalculoPedidoService
            
            # Executar cálculo completo
            resultado = CalculoPedidoService.calcular_custos_completo(proposta)
            
            # Recarregar proposta para obter valores atualizados
            proposta.refresh_from_db()
            
            if proposta.preco_venda_calculado:
                messages.success(request,
                    f'Cálculos executados com sucesso! '
                    f'Valor calculado: R$ {proposta.preco_venda_calculado:.2f}'
                )
                
                # Redirecionar para step 3 se ainda em rascunho
                if proposta.status == 'rascunho':
                    return redirect('vendedor:proposta_step3', pk=proposta.pk)
                else:
                    return redirect('vendedor:proposta_detail', pk=proposta.pk)
            else:
                messages.error(request, 'Erro: Cálculo não retornou valor válido.')
                
        except Exception as e:
            logger.error(f"Erro ao calcular proposta {proposta.numero}: {str(e)}")
            messages.error(request, f'Erro ao calcular proposta: {str(e)}')
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'pode_calcular': proposta.pode_calcular(),  # ✅ CORRIGIDO: método correto
    }
    
    return render(request, 'vendedor/proposta_calcular.html', context)


@login_required
def proposta_duplicar(request, pk):
    """
    Duplicar proposta existente
    """
    # 🎯 REMOVIDO: filtro por vendedor - qualquer um pode duplicar
    proposta_original = get_object_or_404(Proposta, pk=pk)
    
    if request.method == 'POST':
        try:
            # Criar nova proposta baseada na original
            nova_proposta = Proposta.objects.create(
                # Dados do cliente
                cliente=proposta_original.cliente,
                nome_projeto=f"{proposta_original.nome_projeto} (Cópia)",
                faturado_por=proposta_original.faturado_por,
                observacoes=proposta_original.observacoes,
                
                # Vendedor
                vendedor=request.user,  
                
                # Dados do elevador
                modelo_elevador=proposta_original.modelo_elevador,
                capacidade=proposta_original.capacidade,
                capacidade_pessoas=proposta_original.capacidade_pessoas,
                acionamento=proposta_original.acionamento,
                tracao=proposta_original.tracao,
                contrapeso=proposta_original.contrapeso,
                
                # Dimensões do poço
                largura_poco=proposta_original.largura_poco,
                comprimento_poco=proposta_original.comprimento_poco,
                altura_poco=proposta_original.altura_poco,
                pavimentos=proposta_original.pavimentos,
                
                # Dados da cabine
                material_cabine=proposta_original.material_cabine,
                material_cabine_outro=proposta_original.material_cabine_outro,
                valor_cabine_outro=proposta_original.valor_cabine_outro,
                espessura_cabine=proposta_original.espessura_cabine,
                saida_cabine=proposta_original.saida_cabine,
                altura_cabine=proposta_original.altura_cabine,
                piso_cabine=proposta_original.piso_cabine,
                material_piso_cabine=proposta_original.material_piso_cabine,
                material_piso_cabine_outro=proposta_original.material_piso_cabine_outro,
                valor_piso_cabine_outro=proposta_original.valor_piso_cabine_outro,
                
                # Porta da cabine
                modelo_porta_cabine=proposta_original.modelo_porta_cabine,
                material_porta_cabine=proposta_original.material_porta_cabine,
                material_porta_cabine_outro=proposta_original.material_porta_cabine_outro,
                valor_porta_cabine_outro=proposta_original.valor_porta_cabine_outro,
                folhas_porta_cabine=proposta_original.folhas_porta_cabine,
                largura_porta_cabine=proposta_original.largura_porta_cabine,
                altura_porta_cabine=proposta_original.altura_porta_cabine,
                
                # Porta do pavimento
                modelo_porta_pavimento=proposta_original.modelo_porta_pavimento,
                material_porta_pavimento=proposta_original.material_porta_pavimento,
                material_porta_pavimento_outro=proposta_original.material_porta_pavimento_outro,
                valor_porta_pavimento_outro=proposta_original.valor_porta_pavimento_outro,
                folhas_porta_pavimento=proposta_original.folhas_porta_pavimento,
                largura_porta_pavimento=proposta_original.largura_porta_pavimento,
                altura_porta_pavimento=proposta_original.altura_porta_pavimento,
                
                # === NÃO DUPLICAR VALORES COMERCIAIS ===
                # Status sempre rascunho
                status='rascunho',
                
                # === NÃO DUPLICAR: ===
                # - preco_venda_calculado (será recalculado)
                # - valor_proposta (será definido pelo vendedor)
                # - data_validade (será definida automaticamente)
                # - forma_pagamento (será definida pelo vendedor)
            )
            
            # Log da ação
            logger.info(
                f"Proposta {proposta_original.numero} duplicada como {nova_proposta.numero} "
                f"pelo usuário {request.user.username}"
            )
            
            messages.success(request,
                f'Proposta duplicada com sucesso! '
                f'Nova proposta: {nova_proposta.numero}'
            )
            
            # Redirecionar para edição da nova proposta
            return redirect('vendedor:proposta_step3', pk=nova_proposta.pk)
            
        except Exception as e:
            logger.error(f"Erro ao duplicar proposta {proposta_original.numero}: {str(e)}")
            messages.error(request, f'Erro ao duplicar proposta: {str(e)}')
            return redirect('vendedor:proposta_detail', pk=proposta_original.pk)
    
    context = {
        'proposta': proposta_original,
        'pedido': proposta_original,  # Compatibilidade
    }
    
    return render(request, 'vendedor/proposta_duplicar.html', context)


@login_required
def proposta_enviar_cliente(request, pk):
    """
    Enviar proposta para o cliente
    """
    # 🎯 REMOVIDO: filtro por vendedor
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.valor_proposta:
        messages.error(request,
            'Proposta deve ter um valor definido antes de ser enviada ao cliente.'
        )
        return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        try:
            # Atualizar status
            status_anterior = proposta.status
            proposta.status = 'aprovado'  # ✅ CORRIGIDO: usar status que existe no modelo
            proposta.save()
            
            # Registrar no histórico
            HistoricoProposta.objects.create(
                proposta=proposta,
                status_anterior=status_anterior,
                status_novo='aprovado',
                observacao='Proposta enviada para o cliente',
                usuario=request.user
            )
            
            # Log da ação
            logger.info(
                f"Proposta {proposta.numero} enviada para cliente "
                f"pelo usuário {request.user.username}"
            )
            
            messages.success(request,
                f'Proposta {proposta.numero} enviada para o cliente com sucesso!'
            )
            
            return redirect('vendedor:proposta_detail', pk=proposta.pk)
            
        except Exception as e:
            logger.error(f"Erro ao enviar proposta {proposta.numero}: {str(e)}")
            messages.error(request, f'Erro ao enviar proposta: {str(e)}')
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
    }
    
    return render(request, 'vendedor/proposta_enviar.html', context)


@login_required
def proposta_gerar_numero_definitivo(request, pk):
    """
    Gerar número definitivo da proposta
    """
    # 🎯 REMOVIDO: filtro por vendedor
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if proposta.status != 'rascunho':
        messages.error(request,
            'Apenas propostas em rascunho podem ter números regenerados.'
        )
        return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    try:
        numero_anterior = proposta.numero
        
        # Forçar regeneração do número
        proposta.numero = ''
        proposta.save()  # save() irá gerar novo número
        
        # Log da ação
        logger.info(
            f"Número da proposta regenerado de {numero_anterior} para {proposta.numero} "
            f"pelo usuário {request.user.username}"
        )
        
        messages.success(request,
            f'Número da proposta atualizado de {numero_anterior} para {proposta.numero}'
        )
        
    except Exception as e:
        logger.error(f"Erro ao regenerar número da proposta: {str(e)}")
        messages.error(request, f'Erro ao regenerar número: {str(e)}')
    
    return redirect('vendedor:proposta_detail', pk=proposta.pk)


@login_required
def proposta_historico(request, pk):
    """
    Histórico de mudanças da proposta
    """
    # 🎯 REMOVIDO: filtro por vendedor
    proposta = get_object_or_404(Proposta, pk=pk)
    
    historico = HistoricoProposta.objects.filter(
        proposta=proposta
    ).select_related('usuario').order_by('-data_mudanca')
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'historico': historico,
    }
    
    return render(request, 'vendedor/proposta_historico.html', context)


@login_required
def proposta_anexos(request, pk):
    """
    Gerenciar anexos da proposta
    """
    # 🎯 REMOVIDO: filtro por vendedor
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if request.method == 'POST':
        from core.forms.propostas import AnexoPropostaForm
        form = AnexoPropostaForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                anexo = form.save(commit=False)
                anexo.proposta = proposta
                anexo.enviado_por = request.user
                
                # Calcular tamanho do arquivo
                if anexo.arquivo:
                    anexo.tamanho = anexo.arquivo.size
                
                anexo.save()
                
                messages.success(request,
                    f'Anexo "{anexo.nome}" adicionado com sucesso!'
                )
                
                return redirect('vendedor:proposta_anexos', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao salvar anexo: {str(e)}")
                messages.error(request, f'Erro ao salvar anexo: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os dados.')
    else:
        from core.forms.propostas import AnexoPropostaForm
        form = AnexoPropostaForm()
    
    anexos = AnexoProposta.objects.filter(
        proposta=proposta
    ).select_related('enviado_por').order_by('-enviado_em')
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'anexos': anexos,
        'form': form,
    }
    
    return render(request, 'vendedor/proposta_anexos.html', context)