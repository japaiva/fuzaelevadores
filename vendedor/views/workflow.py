# vendedor/views/workflow.py - STEP 2 ATUALIZADO

"""
Views para o workflow de criação/edição de propostas em 3 etapas
NOVA FUNCIONALIDADE: Portas detalhadas por pavimento como padrão
"""

import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_vendedor
from django.contrib import messages
from django.http import JsonResponse

from core.models import Proposta, Cliente, PortaPavimento
from core.forms.propostas import (
    PropostaClienteElevadorForm,
    PropostaCabinePortasForm,
    PropostaComercialForm
)

logger = logging.getLogger(__name__)

@portal_vendedor
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


@portal_vendedor
def proposta_step2(request, pk):
    """
    Etapa 2: Cabine + Portas + Detalhamento por Pavimento (PADRÃO)
    NOVA LÓGICA: Sempre trabalha com portas individuais por pavimento
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
                
                # ✅ NOVA LÓGICA: Sempre gerenciar portas por pavimento
                processar_portas_pavimento(proposta, request.POST)
                
                logger.info(f"Etapa 2 da proposta {proposta.numero} salva pelo usuário {request.user.username}")
                return redirect('vendedor:proposta_step3', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao salvar etapa 2 da proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao salvar dados: {str(e)}')
        else:
            messages.error(request, 'Erro no formulário. Verifique os campos destacados.')
    else:
        form = PropostaCabinePortasForm(instance=proposta)
    
    # ✅ SEMPRE preparar dados de portas por pavimento
    portas_pavimento = preparar_portas_pavimento(proposta)
    
    context = {
        'form': form,
        'proposta': proposta,
        'pedido': proposta,  # Compatibilidade
        'editing': True,
        'portas_pavimento': portas_pavimento,
        'total_pavimentos': proposta.pavimentos,
    }
    
    return render(request, 'vendedor/proposta_step2.html', context)


def preparar_portas_pavimento(proposta):
    """
    Prepara dados das portas por pavimento
    Se não existem, cria com base nos padrões da proposta
    """
    portas_existentes = PortaPavimento.objects.filter(proposta=proposta).order_by('andar')
    
    # Debug: Log inicial
    logger.debug(f"preparar_portas_pavimento: proposta {proposta.numero}, pavimentos: {proposta.pavimentos}")
    logger.debug(f"Portas existentes no banco: {portas_existentes.count()}")
    
    # Se já existem portas cadastradas, usar elas
    if portas_existentes.exists():
        logger.debug("Carregando portas existentes do banco...")
        
        # Debug: Mostrar o que está no banco
        for porta in portas_existentes:
            logger.debug(f"Banco - Andar {porta.andar}: {porta.largura}x{porta.altura} - {porta.modelo} {porta.material}")
        
        # Criar lista garantindo que temos todas as portas (caso algum andar esteja faltando)
        portas_dict = {porta.andar: porta for porta in portas_existentes}
        portas_ordenadas = []
        
        for andar in range(proposta.pavimentos):
            if andar in portas_dict:
                porta_existente = portas_dict[andar]
                portas_ordenadas.append(porta_existente)
                logger.debug(f"Retornando andar {andar}: {porta_existente.largura}x{porta_existente.altura}")
            else:
                # Criar porta temporária para andar faltante
                porta_temp = criar_porta_temporaria(proposta, andar)
                portas_ordenadas.append(porta_temp)
                logger.debug(f"Criando temporário andar {andar}: {porta_temp.largura}x{porta_temp.altura}")
        
        logger.debug(f"Total portas retornadas: {len(portas_ordenadas)}")
        return portas_ordenadas
    
    # Se não existem, criar estrutura padrão baseada na proposta
    logger.debug("Criando portas temporárias (não existem no banco)")
    portas_padrao = []
    
    for andar in range(proposta.pavimentos):
        porta = criar_porta_temporaria(proposta, andar)
        portas_padrao.append(porta)
        logger.debug(f"Criando padrão andar {andar}: {porta.largura}x{porta.altura}")
    
    return portas_padrao


def criar_porta_temporaria(proposta, andar):
    """
    Cria uma porta temporária (não salva no banco) com valores padrão
    """
    # Gerar nome do andar
    if andar == 0:
        nome_andar = "Térreo"
    elif andar < 0:
        nome_andar = f"Subsolo {abs(andar)}" if abs(andar) > 1 else "Subsolo"
    else:
        nome_andar = f"{andar}º Andar"
    
    # Criar objeto temporário (não salvo no banco ainda)
    porta = PortaPavimento(
        proposta=proposta,
        andar=andar,
        nome_andar=nome_andar,
        ativo=True,
        saida='normal',
        abertura_porta='direita',
        modelo=proposta.modelo_porta_pavimento or 'Automática',
        material=proposta.material_porta_pavimento or 'Inox 430',
        largura=proposta.largura_porta_pavimento or Decimal('0.80'),
        altura=proposta.altura_porta_pavimento or Decimal('2.10'),
        folhas=proposta.folhas_porta_pavimento or '2',
    )
    
    return porta


def processar_portas_pavimento(proposta, post_data):
    """
    Processa e salva as portas individuais por pavimento
    """
    # Remover portas existentes para recriar
    PortaPavimento.objects.filter(proposta=proposta).delete()
    
    # Criar portas baseadas nos dados do POST
    for andar in range(proposta.pavimentos):
        # Extrair dados do POST para este andar
        nome_andar = post_data.get(f'porta_nome_{andar}', '')
        ativo = post_data.get(f'porta_ativo_{andar}') == 'on'
        saida = post_data.get(f'porta_saida_{andar}', 'normal')
        abertura_porta = post_data.get(f'porta_abertura_{andar}', 'direita')
        modelo = post_data.get(f'porta_modelo_{andar}', proposta.modelo_porta_pavimento)
        material = post_data.get(f'porta_material_{andar}', proposta.material_porta_pavimento)
        largura_raw = post_data.get(f'porta_largura_{andar}')
        altura_raw = post_data.get(f'porta_altura_{andar}')
        folhas = post_data.get(f'porta_folhas_{andar}', proposta.folhas_porta_pavimento)
        observacoes = post_data.get(f'porta_observacoes_{andar}', '')
        
        # Gerar nome padrão se não informado
        if not nome_andar:
            if andar == 0:
                nome_andar = "Térreo"
            else:
                nome_andar = f"{andar}º Andar"
        
        # Processar largura
        try:
            largura = Decimal(str(largura_raw)) if largura_raw and largura_raw.strip() else None
        except (ValueError, TypeError):
            largura = None
        
        if not largura:
            largura = proposta.largura_porta_pavimento or Decimal('0.80')
        
        # Processar altura
        try:
            altura = Decimal(str(altura_raw)) if altura_raw and altura_raw.strip() else None
        except (ValueError, TypeError):
            altura = None
            
        if not altura:
            altura = proposta.altura_porta_pavimento or Decimal('2.10')
        
        # Criar registro no banco
        PortaPavimento.objects.create(
            proposta=proposta,
            andar=andar,
            nome_andar=nome_andar,
            ativo=ativo,
            saida=saida,
            abertura_porta=abertura_porta,
            modelo=modelo,
            material=material,
            largura=largura,
            altura=altura,
            folhas=folhas if folhas else proposta.folhas_porta_pavimento,
            observacoes=observacoes,
        )
    
    logger.info(f"Processadas {proposta.pavimentos} portas individuais para proposta {proposta.numero}")
    
    # Debug: Log dos valores processados
    logger.debug(f"Valores POST processados para proposta {proposta.numero}:")
    for andar in range(proposta.pavimentos):
        largura_debug = post_data.get(f'porta_largura_{andar}')
        altura_debug = post_data.get(f'porta_altura_{andar}')
        logger.debug(f"Andar {andar}: largura={largura_debug}, altura={altura_debug}")


@portal_vendedor
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