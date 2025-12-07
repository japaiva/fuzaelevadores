# vendedor/views/acoes.py

import logging
from datetime import date
from decimal import Decimal  # ✅ IMPORT ADICIONADO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_vendedor
from django.contrib import messages
from django.http import JsonResponse

from core.models import Proposta, AnexoProposta, HistoricoProposta, ParametrosGerais

logger = logging.getLogger(__name__)


@portal_vendedor
def proposta_calcular(request, pk):
    """
    Executar cálculos completos com impostos dinâmicos baseados em parâmetros
    ✅ VERSÃO CORRIGIDA: Sem funções não definidas + impostos dinâmicos
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.pode_calcular():
        messages.error(request,
            f'Proposta {proposta.numero} não pode ter valores calculados. '
            f'Verifique se todos os dados obrigatórios foram preenchidos.'
        )
        return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    # ✅ APENAS POST - Executar cálculos
    if request.method == 'POST':
        try:
            # === CARREGAR PARÂMETROS DO SISTEMA ===
            parametros = ParametrosGerais.objects.first()
            
            # === EXECUTAR CÁLCULOS TÉCNICOS VIA SERVICE (COM IMPOSTOS DINÂMICOS) ===
            from core.services.calculo_pedido import CalculoPedidoService
            resultado = CalculoPedidoService.calcular_custos_completo(proposta)
            
            # === VERIFICAR SE CÁLCULO FOI EXECUTADO COM SUCESSO ===
            if not proposta.preco_venda_calculado:
                messages.error(request, 'Erro: Cálculo não retornou valor válido.')
                return redirect('vendedor:proposta_detail', pk=proposta.pk)
            
            # === SALVAR PROPOSTA ===
            proposta.save()
            
            # === MENSAGEM DE SUCESSO COM PERCENTUAL USADO ===
            if proposta.preco_venda_calculado:
                # Determinar percentual usado para a mensagem
                percentual_usado = "10% (padrão)"
                if parametros:
                    if proposta.faturado_por == 'Elevadores' and parametros.faturamento_elevadores is not None:
                        percentual_usado = f"{parametros.faturamento_elevadores}% (Elevadores)"
                    elif proposta.faturado_por == 'Fuza' and parametros.faturamento_fuza is not None:
                        percentual_usado = f"{parametros.faturamento_fuza}% (Fuza)"
                    elif proposta.faturado_por == 'Manutenção' and parametros.faturamento_manutencao is not None:
                        percentual_usado = f"{parametros.faturamento_manutencao}% (Manutenção)"
                
                messages.success(request,
                    f'Cálculos executados com sucesso! '
                    f'Valor calculado: R$ {proposta.preco_venda_calculado:,.2f} '
                    f'| Impostos: {percentual_usado}'
                )
                
                # Log da ação
                logger.info(
                    f"Cálculos executados para proposta {proposta.numero} "
                    f"pelo usuário {request.user.username} - "
                    f"Valor: R$ {proposta.preco_venda_calculado:,.2f}"
                )
                
                # Redirecionar baseado no status
                if proposta.status == 'rascunho':
                    return redirect('vendedor:proposta_step3', pk=proposta.pk)
                else:
                    return redirect('vendedor:proposta_detail', pk=proposta.pk)
            else:
                messages.error(request, 'Erro: Cálculo não retornou valor válido.')
                return redirect('vendedor:proposta_detail', pk=proposta.pk)
                
        except Exception as e:
            logger.error(f"Erro ao calcular proposta {proposta.numero}: {str(e)}")
            messages.error(request, f'Erro inesperado nos cálculos: {str(e)}')
            return redirect('vendedor:proposta_detail', pk=proposta.pk)
    
    # ✅ GET REQUEST: Mostrar página de confirmação
    parametros = ParametrosGerais.objects.first()
    context = {
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'pode_calcular': proposta.pode_calcular(),
        'parametros': parametros,
    }
    
    return render(request, 'vendedor/proposta_calcular.html', context)


@portal_vendedor
def proposta_duplicar(request, pk):
    """
    Duplicar proposta existente
    """
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
                
                # ✅ INCLUIR NORMAS ABNT SE EXISTE
                normas_abnt=proposta_original.normas_abnt if hasattr(proposta_original, 'normas_abnt') else 'NBR 16858',
                
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


@portal_vendedor
def proposta_enviar_cliente(request, pk):
    """
    Enviar proposta para o cliente
    """
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
            proposta.status = 'aprovado'
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


@portal_vendedor
def proposta_gerar_numero_definitivo(request, pk):
    """
    Gerar número definitivo da proposta
    """
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


@portal_vendedor
def proposta_historico(request, pk):
    """
    Histórico de mudanças da proposta
    """
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


@portal_vendedor
def proposta_anexos(request, pk):
    """
    Gerenciar anexos da proposta
    """
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