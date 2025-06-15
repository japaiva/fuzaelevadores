# vendedor/views.py - VERSÃO COMPLETA CORRIGIDA

import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.models import Cliente, Proposta, HistoricoProposta
from core.forms.propostas import (
    PropostaClienteElevadorForm, 
    PropostaCabinePortasForm,
    PropostaComercialForm,
    PropostaFiltroForm,
    ClienteCreateForm
)
from core.views.propostas import (
    proposta_detail_base,
    executar_calculos_proposta,
    api_dados_precificacao_base,
    api_salvar_preco_base
)

logger = logging.getLogger(__name__)

# =============================================================================
# DASHBOARD E PÁGINAS PRINCIPAIS
# =============================================================================

@login_required
def home(request):
    """Página inicial - redireciona para dashboard"""
    return redirect('vendedor:dashboard')

@login_required
def dashboard(request):
    """Dashboard principal do vendedor"""
    # Propostas do vendedor
    propostas = Proposta.objects.filter(vendedor=request.user)
    
    # Estatísticas
    stats = {
        'total': propostas.count(),
        'rascunho': propostas.filter(status='rascunho').count(),
        'simulado': propostas.filter(status='simulado').count(),
        'proposta_gerada': propostas.filter(status='proposta_gerada').count(),
        'aprovado': propostas.filter(status='aprovado').count(),
        'em_producao': propostas.filter(status='em_producao').count(),
    }
    
    # Propostas recentes
    propostas_recentes = propostas.select_related('cliente').order_by('-criado_em')[:8]
    
    # Propostas por status para gráfico
    stats_status = [
        {'status': 'Rascunho', 'count': stats['rascunho'], 'color': 'secondary'},
        {'status': 'Simulado', 'count': stats['simulado'], 'color': 'info'},
        {'status': 'Proposta Gerada', 'count': stats['proposta_gerada'], 'color': 'primary'},
        {'status': 'Aprovado', 'count': stats['aprovado'], 'color': 'success'},
        {'status': 'Em Produção', 'count': stats['em_producao'], 'color': 'warning'},
    ]
    
    # Alertas
    alertas = []
    
    # Propostas próximas do vencimento
    propostas_vencendo = propostas.filter(
        data_validade__lte=date.today() + timedelta(days=7),
        data_validade__gte=date.today(),
        status__in=['simulado', 'proposta_gerada', 'enviado_cliente']
    ).count()
    
    if propostas_vencendo > 0:
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Propostas Vencendo',
            'mensagem': f'{propostas_vencendo} proposta(s) vencem em 7 dias',
            'url': f"/vendedor/propostas/?validade=vence_semana"
        })
    
    # Propostas vencidas
    propostas_vencidas = propostas.filter(
        data_validade__lt=date.today(),
        status__in=['simulado', 'proposta_gerada', 'enviado_cliente']
    ).count()
    
    if propostas_vencidas > 0:
        alertas.append({
            'tipo': 'danger',
            'titulo': 'Propostas Vencidas',
            'mensagem': f'{propostas_vencidas} proposta(s) vencida(s)',
            'url': f"/vendedor/propostas/?validade=vencidas"
        })
    
    context = {
        'stats': stats,
        'stats_status': stats_status,
        'propostas_recentes': propostas_recentes,
        'alertas': alertas,
    }
    
    return render(request, 'vendedor/dashboard.html', context)

# =============================================================================
# GESTÃO DE PROPOSTAS
# =============================================================================

@login_required
def proposta_list(request):
    """Lista de propostas do vendedor com filtros avançados"""
    propostas_list = Proposta.objects.filter(
        vendedor=request.user
    ).select_related('cliente').order_by('-criado_em')
    
    # Aplicar filtros
    form = PropostaFiltroForm(request.GET)
    if form.is_valid():
        # Filtro por status
        if form.cleaned_data.get('status'):
            propostas_list = propostas_list.filter(status=form.cleaned_data['status'])
        
        # Filtro por modelo
        if form.cleaned_data.get('modelo_elevador'):
            propostas_list = propostas_list.filter(modelo_elevador=form.cleaned_data['modelo_elevador'])
        
        # Filtro por período
        periodo = form.cleaned_data.get('periodo')
        if periodo:
            hoje = date.today()
            if periodo == 'hoje':
                propostas_list = propostas_list.filter(criado_em__date=hoje)
            elif periodo == 'semana':
                inicio_semana = hoje - timedelta(days=hoje.weekday())
                propostas_list = propostas_list.filter(criado_em__date__gte=inicio_semana)
            elif periodo == 'mes':
                propostas_list = propostas_list.filter(
                    criado_em__year=hoje.year,
                    criado_em__month=hoje.month
                )
            elif periodo == 'ano':
                propostas_list = propostas_list.filter(criado_em__year=hoje.year)
        
        # Filtro por validade
        validade = form.cleaned_data.get('validade')
        if validade:
            hoje = date.today()
            if validade == 'vencidas':
                propostas_list = propostas_list.filter(data_validade__lt=hoje)
            elif validade == 'vence_hoje':
                propostas_list = propostas_list.filter(data_validade=hoje)
            elif validade == 'vence_semana':
                propostas_list = propostas_list.filter(
                    data_validade__lte=hoje + timedelta(days=7),
                    data_validade__gte=hoje
                )
            elif validade == 'vigentes':
                propostas_list = propostas_list.filter(data_validade__gte=hoje)
        
        # Busca textual
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            propostas_list = propostas_list.filter(
                Q(numero__icontains=query) |
                Q(nome_projeto__icontains=query) |
                Q(cliente__nome__icontains=query) |
                Q(cliente__nome_fantasia__icontains=query)
            )
    
    # Paginação
    paginator = Paginator(propostas_list, 15)
    page = request.GET.get('page', 1)
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    context = {
        'propostas': propostas,
        'form': form,
        'total_propostas': propostas_list.count(),
    }
    
    return render(request, 'vendedor/pedido_list.html', context)

@login_required
def proposta_detail(request, pk):
    """Detalhes da proposta - usando view base compartilhada"""
    extra_context = {
        'is_vendedor': True,
        'base_template': 'vendedor/base_vendedor.html',
    }
    return proposta_detail_base(request, pk, 'base/proposta_detail.html', extra_context)

# =============================================================================
# WORKFLOW EM 3 ETAPAS - CORRIGIDO PARA COMPATIBILIDADE TOTAL
# =============================================================================

@login_required
def proposta_step1(request, pk=None):
    """Etapa 1: Cliente + Elevador + Poço"""
    
    if pk:
        # EDIÇÃO
        proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
        
        # Verificar se pode editar
        if not proposta.pode_editar:
            messages.error(request, 
                f'Proposta em {proposta.get_status_display()} não pode ser editada.'
            )
            return redirect('vendedor:pedido_detail', pk=proposta.pk)
        
        editing = True
    else:
        # CRIAÇÃO
        proposta = None
        editing = False
    
    if request.method == 'POST':
        if editing:
            form = PropostaClienteElevadorForm(request.POST, instance=proposta)
        else:
            form = PropostaClienteElevadorForm(request.POST)
            
        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                
                if not editing:
                    # Nova proposta
                    proposta.vendedor = request.user
                    proposta.status = 'rascunho'
                    
                    # Definir valores padrão para as próximas etapas
                    proposta.modelo_porta_cabine = 'Automática'
                    proposta.material_porta_cabine = 'Inox'
                    proposta.folhas_porta_cabine = '2'
                    proposta.largura_porta_cabine = 0.80
                    proposta.altura_porta_cabine = 2.00
                    
                    proposta.modelo_porta_pavimento = 'Automática'
                    proposta.material_porta_pavimento = 'Inox'
                    proposta.folhas_porta_pavimento = '2'
                    proposta.largura_porta_pavimento = 0.80
                    proposta.altura_porta_pavimento = 2.00
                    
                    proposta.material_cabine = 'Inox 430'
                    proposta.espessura_cabine = '1,2'
                    proposta.saida_cabine = 'Padrão'
                    proposta.altura_cabine = 2.30
                    proposta.piso_cabine = 'Por conta do cliente'
                    
                    # Valores comerciais padrão
                    proposta.data_validade = date.today() + timedelta(days=30)
                    proposta.prazo_entrega_dias = 45
                    proposta.forma_pagamento = 'parcelado'
                    proposta.numero_parcelas = 3
                    proposta.tipo_parcela = 'mensal'
                
                proposta.atualizado_por = request.user
                proposta.save()
                
                # Registrar no histórico
                HistoricoProposta.objects.create(
                    proposta=proposta,
                    status_anterior=proposta.status if editing else '',
                    status_novo=proposta.status,
                    observacao='Dados de cliente/elevador ' + ('atualizados' if editing else 'criados'),
                    usuario=request.user
                )
                
                messages.success(request, 
                    f'Proposta {proposta.numero} {"atualizada" if editing else "criada"} com sucesso!'
                )
                
                return redirect('vendedor:pedido_step2', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao {'atualizar' if editing else 'criar'} proposta: {str(e)}")
                messages.error(request, f'Erro ao salvar proposta: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        if editing:
            form = PropostaClienteElevadorForm(instance=proposta)
        else:
            form = PropostaClienteElevadorForm()
    
    # CORREÇÃO PRINCIPAL: Usar 'pedido' para compatibilidade com templates
    context = {
        'form': form,
        'pedido': proposta,      # ✅ OBRIGATÓRIO - Para compatibilidade com templates atuais
        'proposta': proposta,    # ✅ Para futuros templates
        'editing': editing,
        'step': 1,
        'step_title': 'Cliente, Elevador e Poço',
    }
    
    return render(request, 'vendedor/pedido_step1.html', context)

@login_required
def proposta_step2(request, pk):
    """Etapa 2: Cabine + Portas"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # Verificar se pode editar
    if not proposta.pode_editar:
        messages.error(request, 
            f'Proposta em {proposta.get_status_display()} não pode ser editada.'
        )
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    editing = proposta.status != 'rascunho' or bool(proposta.preco_venda_calculado)
    
    if request.method == 'POST':
        form = PropostaCabinePortasForm(request.POST, instance=proposta)
        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                proposta.atualizado_por = request.user
                proposta.save()
                
                # Executar cálculos automáticos se possível
                if proposta.pode_calcular():
                    logger.info(f"Executando cálculos automáticos para proposta {proposta.numero}")
                    
                    resultado = executar_calculos_proposta(proposta, request.user)
                    
                    if resultado['success']:
                        messages.success(request, 'Especificações salvas e cálculos executados!')
                        
                        # Mostrar resumo dos cálculos
                        if proposta.custo_producao:
                            messages.info(request, f"Custo de produção: R$ {proposta.custo_producao:,.2f}")
                        if proposta.preco_venda_calculado:
                            messages.info(request, f"Preço calculado: R$ {proposta.preco_venda_calculado:,.2f}")
                    else:
                        messages.warning(request, f"Especificações salvas, mas {resultado['message']}")
                else:
                    messages.info(request, 'Especificações salvas. Complete os dados para executar cálculos.')
                
                # Registrar no histórico
                HistoricoProposta.objects.create(
                    proposta=proposta,
                    status_anterior=proposta.status,
                    status_novo=proposta.status,
                    observacao='Especificações da cabine/portas finalizadas',
                    usuario=request.user
                )
                
                return redirect('vendedor:pedido_step3', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao salvar especificações da proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao salvar especificações: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = PropostaCabinePortasForm(instance=proposta)
    
    # CORREÇÃO: Usar 'pedido' para compatibilidade
    context = {
        'form': form,
        'pedido': proposta,      # ✅ OBRIGATÓRIO - Para compatibilidade
        'proposta': proposta,    # ✅ Para futuros templates
        'editing': editing,
        'step': 2,
        'step_title': 'Cabine e Portas',
    }
    
    return render(request, 'vendedor/pedido_step2.html', context)

@login_required 
def proposta_step3(request, pk):
    """Etapa 3: Dados Comerciais"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # Verificar se pode editar
    if not proposta.pode_editar:
        messages.error(request, 
            f'Proposta em {proposta.get_status_display()} não pode ser editada.'
        )
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        form = PropostaComercialForm(request.POST, instance=proposta)
        if form.is_valid():
            try:
                proposta = form.save(commit=False)
                proposta.atualizado_por = request.user
                
                # Atualizar status se ainda for rascunho
                if proposta.status == 'rascunho':
                    proposta.status = 'simulado'
                
                proposta.save()
                
                # Registrar no histórico
                HistoricoProposta.objects.create(
                    proposta=proposta,
                    status_anterior='rascunho' if proposta.status == 'simulado' else proposta.status,
                    status_novo=proposta.status,
                    observacao='Dados comerciais finalizados - Proposta completa',
                    usuario=request.user
                )
                
                messages.success(request, 
                    f'Proposta {proposta.numero} finalizada com sucesso! '
                    f'Status: {proposta.get_status_display()}'
                )
                
                return redirect('vendedor:pedido_detail', pk=proposta.pk)
                
            except Exception as e:
                logger.error(f"Erro ao finalizar proposta {proposta.numero}: {str(e)}")
                messages.error(request, f'Erro ao salvar dados comerciais: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = PropostaComercialForm(instance=proposta)
    
    # CORREÇÃO: Usar 'pedido' para compatibilidade
    context = {
        'form': form,
        'pedido': proposta,      # ✅ OBRIGATÓRIO - Para compatibilidade
        'proposta': proposta,    # ✅ Para futuros templates
        'step': 3,
        'step_title': 'Dados Comerciais',
    }
    
    return render(request, 'vendedor/pedido_step3.html', context)

# =============================================================================
# AÇÕES DAS PROPOSTAS
# =============================================================================

@login_required
def proposta_calcular(request, pk):
    """Executar cálculos da proposta manualmente"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # Verificar se pode calcular
    if not proposta.pode_calcular():
        messages.error(request, 
            'Proposta não tem dados suficientes para cálculo. '
            'Complete as especificações primeiro.'
        )
        return redirect('vendedor:pedido_step1', pk=proposta.pk)
    
    # Executar cálculos
    resultado = executar_calculos_proposta(proposta, request.user)
    
    if resultado['success']:
        messages.success(request, resultado['message'])
        
        # Mostrar resumo dos resultados
        proposta.refresh_from_db()
        if proposta.custo_producao:
            messages.info(request, f"Custo de produção: R$ {proposta.custo_producao:,.2f}")
        if proposta.preco_venda_calculado:
            messages.info(request, f"Preço calculado: R$ {proposta.preco_venda_calculado:,.2f}")
        
        # Mostrar dimensões se calculadas
        if proposta.largura_cabine_calculada and proposta.comprimento_cabine_calculado:
            messages.info(request, 
                f"Cabine: {proposta.largura_cabine_calculada:.2f}m x "
                f"{proposta.comprimento_cabine_calculado:.2f}m x "
                f"{proposta.altura_cabine:.2f}m"
            )
    else:
        messages.error(request, resultado['message'])
    
    return redirect('vendedor:pedido_detail', pk=proposta.pk)

@login_required
def proposta_duplicar(request, pk):
    """Duplicar proposta existente"""
    proposta_original = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    try:
        # Criar cópia
        proposta_copia = Proposta.objects.get(pk=proposta_original.pk)
        proposta_copia.pk = None  # Remove o ID para criar novo
        proposta_copia.numero = None  # Será gerado automaticamente
        proposta_copia.status = 'rascunho'
        proposta_copia.nome_projeto = f"Cópia de {proposta_original.nome_projeto}"
        proposta_copia.atualizado_por = request.user
        
        # Limpar dados calculados
        proposta_copia.preco_venda_calculado = None
        proposta_copia.preco_negociado = None
        proposta_copia.custo_producao = None
        proposta_copia.custo_materiais = None
        proposta_copia.custo_mao_obra = None
        proposta_copia.custo_instalacao = None
        proposta_copia.largura_cabine_calculada = None
        proposta_copia.comprimento_cabine_calculado = None
        proposta_copia.capacidade_cabine_calculada = None
        proposta_copia.tracao_cabine_calculada = None
        proposta_copia.percentual_desconto = 0
        
        # Limpar JSONs
        proposta_copia.ficha_tecnica = {}
        proposta_copia.dimensionamento_detalhado = {}
        proposta_copia.explicacao_calculo = ''
        proposta_copia.custos_detalhados = {}
        proposta_copia.formacao_preco = {}
        proposta_copia.componentes_calculados = {}
        
        # Atualizar datas
        proposta_copia.data_validade = date.today() + timedelta(days=30)
        
        proposta_copia.save()
        
        # Registrar no histórico
        HistoricoProposta.objects.create(
            proposta=proposta_copia,
            status_anterior='',
            status_novo='rascunho',
            observacao=f'Proposta duplicada de {proposta_original.numero}',
            usuario=request.user
        )
        
        messages.success(request, 
            f'Proposta duplicada com sucesso! Novo número: {proposta_copia.numero}'
        )
        
        return redirect('vendedor:pedido_step1', pk=proposta_copia.pk)
        
    except Exception as e:
        logger.error(f"Erro ao duplicar proposta {proposta_original.numero}: {str(e)}")
        messages.error(request, f'Erro ao duplicar proposta: {str(e)}')
        return redirect('vendedor:pedido_detail', pk=proposta_original.pk)

@login_required
def proposta_delete(request, pk):
    """Excluir proposta"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # Verificar se pode excluir
    if proposta.status not in ['rascunho', 'simulado']:
        messages.error(request, 
            f'Apenas propostas em rascunho ou simulado podem ser excluídas. '
            f'Status atual: {proposta.get_status_display()}'
        )
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    if request.method == 'POST':
        try:
            numero = proposta.numero
            nome_projeto = proposta.nome_projeto
            
            # Log da exclusão
            logger.info(
                f"Proposta {numero} ({nome_projeto}) excluída pelo vendedor {request.user.username}"
            )
            
            # Excluir (cascata remove histórico e anexos)
            proposta.delete()
            
            messages.success(request, 
                f'Proposta {numero} - {nome_projeto} excluída com sucesso.'
            )
            return redirect('vendedor:pedido_list')
            
        except Exception as e:
            logger.error(f"Erro ao excluir proposta {proposta.numero}: {str(e)}")
            messages.error(request, f'Erro ao excluir proposta: {str(e)}')
            return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # ✅ Compatibilidade
        'pode_excluir': True,
    }
    
    return render(request, 'vendedor/pedido_confirm_delete.html', context)

# =============================================================================
# APIS AJAX
# =============================================================================

@login_required
def api_dados_precificacao(request, pk):
    """API para dados de precificação - delegando para função base"""
    return api_dados_precificacao_base(request, pk)

@login_required
@require_POST
def api_salvar_preco_negociado(request, pk):
    """API para salvar preço negociado - delegando para função base"""
    return api_salvar_preco_base(request, pk)

@login_required
def api_cliente_info(request, cliente_id):
    """API para informações do cliente"""
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id, ativo=True)
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'nome_fantasia': cliente.nome_fantasia or '',
                'telefone': cliente.telefone or '',
                'email': cliente.email or '',
                'contato_principal': cliente.contato_principal or '',
                'endereco_completo': cliente.endereco_completo,
                'tipo_pessoa': cliente.get_tipo_pessoa_display(),
                'cpf_cnpj': cliente.cpf_cnpj or '',
            }
        })
        
    except Cliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})
    except Exception as e:
        logger.error(f"Erro ao buscar cliente {cliente_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Erro interno'})

@login_required
def cliente_create_ajax(request):
    """Criar cliente via AJAX"""
    if request.method == 'POST':
        form = ClienteCreateForm(request.POST)
        if form.is_valid():
            try:
                cliente = form.save(commit=False)
                cliente.criado_por = request.user
                cliente.save()
                
                logger.info(f"Cliente {cliente.nome} criado via AJAX pelo vendedor {request.user}")
                
                return JsonResponse({
                    'success': True,
                    'cliente': {
                        'id': cliente.id,
                        'nome': cliente.nome,
                        'nome_fantasia': cliente.nome_fantasia or '',
                        'telefone': cliente.telefone or '',
                        'email': cliente.email or '',
                        'endereco_completo': cliente.endereco_completo,
                    }
                })
                
            except Exception as e:
                logger.error(f"Erro ao criar cliente via AJAX: {str(e)}")
                return JsonResponse({'success': False, 'errors': {'Erro': [str(e)]}})
        else:
            # Formatar erros
            formatted_errors = {}
            for field, errors in form.errors.items():
                field_label = form.fields[field].label or field
                formatted_errors[field_label] = errors
                
            return JsonResponse({'success': False, 'errors': formatted_errors})
    
    # GET request
    form = ClienteCreateForm()
    return render(request, 'vendedor/cliente_create_modal.html', {'form': form})

# =============================================================================
# VIEWS COMPLEMENTARES (simplificadas)
# =============================================================================

@login_required
def gerar_pdf_orcamento(request, pk):
    """Gerar PDF do orçamento"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    if not proposta.preco_venda_calculado:
        messages.warning(request, 'Execute os cálculos antes de gerar o orçamento.')
        return redirect('vendedor:pedido_detail', pk=pk)
    
    # TODO: Implementar geração de PDF
    messages.info(request, 'Geração de PDF do orçamento em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)

@login_required
def gerar_pdf_demonstrativo(request, pk):
    """Gerar PDF do demonstrativo técnico"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # TODO: Implementar geração de PDF
    messages.info(request, 'Geração de PDF demonstrativo em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)

@login_required
def proposta_historico(request, pk):
    """Visualizar histórico de mudanças da proposta"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    historico = HistoricoProposta.objects.filter(
        proposta=proposta
    ).select_related('usuario').order_by('-data_mudanca')
    
    context = {
        'proposta': proposta,
        'pedido': proposta,  # ✅ Compatibilidade
        'historico': historico,
    }
    
    return render(request, 'vendedor/proposta_historico.html', context)

@login_required
def proposta_anexos(request, pk):
    """Gerenciar anexos da proposta"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # TODO: Implementar gestão de anexos
    messages.info(request, 'Gestão de anexos em desenvolvimento.')
    return redirect('vendedor:pedido_detail', pk=pk)

@login_required
def proposta_enviar_cliente(request, pk):
    """Enviar proposta para o cliente por email"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    # Verificar se pode enviar
    if proposta.status not in ['simulado', 'proposta_gerada']:
        messages.error(request, 
            f'Proposta em {proposta.get_status_display()} não pode ser enviada.'
        )
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    if not proposta.preco_venda_calculado:
        messages.error(request, 'Execute os cálculos antes de enviar a proposta.')
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    try:
        # Atualizar status
        proposta.status = 'enviado_cliente'
        proposta.atualizado_por = request.user
        proposta.save()
        
        # Registrar no histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior='simulado',
            status_novo='enviado_cliente',
            observacao='Proposta enviada ao cliente por email',
            usuario=request.user
        )
        
        # TODO: Implementar envio de email
        messages.success(request, 
            f'Proposta {proposta.numero} marcada como enviada ao cliente.'
        )
        
        # Futuramente aqui será implementado o envio real do email
        messages.info(request, 'Funcionalidade de envio por email em desenvolvimento.')
        
    except Exception as e:
        logger.error(f"Erro ao enviar proposta {proposta.numero}: {str(e)}")
        messages.error(request, f'Erro ao enviar proposta: {str(e)}')
    
    return redirect('vendedor:pedido_detail', pk=pk)

@login_required
def proposta_gerar_numero_definitivo(request, pk):
    """Gerar número definitivo da proposta (transforma de simulação em proposta oficial)"""
    proposta = get_object_or_404(Proposta, pk=pk, vendedor=request.user)
    
    if proposta.status != 'simulado':
        messages.error(request, 'Apenas propostas simuladas podem gerar número definitivo.')
        return redirect('vendedor:pedido_detail', pk=proposta.pk)
    
    try:
        # Atualizar status
        status_anterior = proposta.status
        proposta.status = 'proposta_gerada'
        proposta.atualizado_por = request.user
        proposta.save()
        
        # Registrar no histórico
        HistoricoProposta.objects.create(
            proposta=proposta,
            status_anterior=status_anterior,
            status_novo='proposta_gerada',
            observacao='Número definitivo gerado - Proposta oficial',
            usuario=request.user
        )
        
        messages.success(request, 
            f'Proposta {proposta.numero} agora é oficial! '
            f'Status: {proposta.get_status_display()}'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar número definitivo para proposta {proposta.numero}: {str(e)}")
        messages.error(request, f'Erro ao gerar número definitivo: {str(e)}')
    
    return redirect('vendedor:pedido_detail', pk=pk)

@login_required
def relatorios_vendedor(request):
    """Relatórios e estatísticas do vendedor"""
    # Propostas do vendedor
    propostas = Proposta.objects.filter(vendedor=request.user)
    
    # Estatísticas básicas
    stats = {
        'total': propostas.count(),
        'rascunho': propostas.filter(status='rascunho').count(),
        'simulado': propostas.filter(status='simulado').count(),
        'proposta_gerada': propostas.filter(status='proposta_gerada').count(),
        'aprovado': propostas.filter(status='aprovado').count(),
        'em_producao': propostas.filter(status='em_producao').count(),
    }
    
    # Propostas por mês (últimos 12 meses)
    from datetime import datetime
    from django.db.models import Count
    
    hoje = date.today()
    stats_mensais = []
    
    for i in range(12):
        mes = hoje.month - i
        ano = hoje.year
        
        if mes <= 0:
            mes += 12
            ano -= 1
        
        count = propostas.filter(
            criado_em__year=ano,
            criado_em__month=mes
        ).count()
        
        valor_total = sum(
            float(p.preco_negociado or p.preco_venda_calculado or 0)
            for p in propostas.filter(criado_em__year=ano, criado_em__month=mes)
        )
        
        stats_mensais.append({
            'mes': f"{mes:02d}/{ano}",
            'count': count,
            'valor': valor_total
        })
    
    stats_mensais.reverse()
    
    # Top clientes
    from collections import Counter
    clientes_count = Counter()
    clientes_valor = Counter()
    
    for proposta in propostas:
        cliente_nome = proposta.cliente.nome
        clientes_count[cliente_nome] += 1
        valor = float(proposta.preco_negociado or proposta.preco_venda_calculado or 0)
        clientes_valor[cliente_nome] += valor
    
    top_clientes_count = clientes_count.most_common(5)
    top_clientes_valor = clientes_valor.most_common(5)
    
    context = {
        'stats': stats,
        'stats_mensais': stats_mensais,
        'top_clientes_count': top_clientes_count,
        'top_clientes_valor': top_clientes_valor,
        'total_propostas': propostas.count(),
    }
    
    return render(request, 'vendedor/relatorios.html', context)