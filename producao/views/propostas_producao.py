# producao/views/propostas_producao.py

"""
Views para Propostas e Lista de Materiais no Portal de Produção
Portal de Produção - Sistema Elevadores FUZA
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from pytz import timezone

from core.models import Proposta, ListaMateriais, ItemListaMateriais, Produto
from core.forms import ListaMateriaisForm, ItemListaMateriaisForm, ItemListaMateriaisFormSet
from core.services.calculo_pedido import CalculoPedidoService
from core.views.propostas import proposta_detail_base  # ✅ IMPORTAÇÃO ADICIONADA

logger = logging.getLogger(__name__)

# =============================================================================
# PROPOSTAS NO PORTAL DE PRODUÇÃO
# =============================================================================

@login_required
def proposta_list_producao(request):
    """Lista de propostas para o portal de produção"""
    
    # Filtrar apenas propostas relevantes para produção
    propostas_list = Proposta.objects.filter(
        status__in=['aprovado', 'simulado','pendente']  # Propostas que podem gerar lista de materiais
    ).select_related('cliente', 'vendedor').order_by('-criado_em')
    
    # Filtros básicos
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    if search:
        propostas_list = propostas_list.filter(
            Q(numero__icontains=search) |
            Q(nome_projeto__icontains=search) |
            Q(cliente__nome__icontains=search)
        )
    
    if status_filter:
        propostas_list = propostas_list.filter(status=status_filter)
    
    # Paginação
    paginator = Paginator(propostas_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        propostas = paginator.page(page)
    except:
        propostas = paginator.page(1)
    
    context = {
        'propostas': propostas,
        'search': search,
        'status_filter': status_filter,
        'status_choices': [
            ('', 'Todos os Status'),
            ('simulado', 'Simulado'),
            ('aprovado', 'Aprovado'),
        ],
        'total_propostas': propostas_list.count(),
    }
    
    return render(request, 'producao/propostas/proposta_list_producao.html', context)

@login_required
def proposta_detail_producao(request, pk):
    """
    Detalhe da proposta no portal de produção
    ✅ ATUALIZADA: Usa o template compartilhado igual ao vendedor
    """
    
    # Verificar se já tem lista de materiais
    lista_materiais = None
    try:
        proposta = get_object_or_404(Proposta, pk=pk)
        lista_materiais = proposta.lista_materiais
    except ListaMateriais.DoesNotExist:
        pass
    
    # Contexto específico da produção
    extra_context = {
        'is_producao': True,
        'lista_materiais': lista_materiais,
        'pode_gerar_lista': proposta.pode_calcular(),
        'tem_lista': lista_materiais is not None,
        'base_template': 'producao/base_producao.html',
        
        # Informações específicas para produção
        'pode_aprovar': lista_materiais.status in ['pronta', 'editada'] if lista_materiais else False,
        'total_itens': lista_materiais.itens.count() if lista_materiais else 0,
        'valor_total': lista_materiais.calcular_valor_total() if lista_materiais else 0,
    }
    
    # ✅ MUDANÇA PRINCIPAL: Usa template unificado
    return proposta_detail_base(
        request, 
        pk, 
        'base/proposta_detail_unified.html',
        extra_context
    )


# =============================================================================
# LISTA DE MATERIAIS
# =============================================================================

@login_required
def gerar_lista_materiais(request, pk):
    """Gera/regenera lista de materiais a partir dos cálculos da proposta"""
    proposta = get_object_or_404(Proposta, pk=pk)
    
    if not proposta.pode_calcular():
        messages.error(request, 'Proposta não tem dados suficientes para calcular lista de materiais.')
        return redirect('producao:proposta_detail_producao', pk=pk)
    
    try:
        with transaction.atomic():
            # Se já existe lista, excluir para regenerar
            try:
                lista_existente = proposta.lista_materiais
                lista_existente.delete()
                messages.info(request, 'Lista de materiais anterior foi substituída.')
            except ListaMateriais.DoesNotExist:
                pass
            
            # Executar cálculos completos
            resultado = CalculoPedidoService.calcular_custos_completo(proposta)
            
            # Criar nova lista de materiais
            lista_materiais = ListaMateriais.objects.create(
                proposta=proposta,
                status='pronta',
                dados_calculo_original=resultado.get('custos', {}),
                observacoes=f'Lista gerada automaticamente em {timezone.now().strftime("%d/%m/%Y %H:%M")}',
                criado_por=request.user,
                atualizado_por=request.user
            )
            
            # Extrair componentes calculados e criar itens
            componentes = proposta.componentes_calculados
            total_itens_criados = 0
            
            if componentes:
                for categoria, categoria_dados in componentes.items():
                    if isinstance(categoria_dados, dict) and 'itens' in str(categoria_dados):
                        # Processar subcategorias
                        for subcategoria, sub_dados in categoria_dados.items():
                            if isinstance(sub_dados, dict) and 'itens' in sub_dados:
                                # Processar itens da subcategoria
                                for codigo, item_dados in sub_dados['itens'].items():
                                    if isinstance(item_dados, dict) and 'codigo' in item_dados:
                                        # Buscar produto pelo código
                                        try:
                                            produto = Produto.objects.get(
                                                codigo=item_dados['codigo'],
                                                tipo='MP'  # Apenas matérias-primas
                                            )
                                            
                                            # Criar item da lista
                                            ItemListaMateriais.objects.create(
                                                lista=lista_materiais,
                                                produto=produto,
                                                quantidade=item_dados.get('quantidade', 1),
                                                unidade=item_dados.get('unidade', produto.unidade_medida),
                                                valor_unitario_estimado=item_dados.get('valor_unitario', 0),
                                                observacoes=item_dados.get('explicacao', ''),
                                                item_calculado=True
                                            )
                                            total_itens_criados += 1
                                            
                                        except Produto.DoesNotExist:
                                            logger.warning(f"Produto {item_dados['codigo']} não encontrado para lista de materiais")
                                            continue
            
            messages.success(request, 
                f'Lista de materiais gerada com sucesso! '
                f'{total_itens_criados} itens criados. '
                f'Agora você pode editar a lista conforme necessário.'
            )
            
            return redirect('producao:lista_materiais_edit', pk=proposta.pk)
            
    except Exception as e:
        logger.error(f"Erro ao gerar lista de materiais para proposta {proposta.numero}: {str(e)}")
        messages.error(request, f'Erro ao gerar lista de materiais: {str(e)}')
        return redirect('producao:proposta_detail_producao', pk=pk)


@login_required
def lista_materiais_edit(request, pk):
    """Interface editável para lista de materiais"""
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar se tem lista de materiais
    try:
        lista_materiais = proposta.lista_materiais
    except ListaMateriais.DoesNotExist:
        messages.error(request, 'Proposta não possui lista de materiais. Gere a lista primeiro.')
        return redirect('producao:proposta_detail_producao', pk=pk)
    
    if request.method == 'POST':
        form = ListaMateriaisForm(request.POST, instance=lista_materiais)
        formset = ItemListaMateriaisFormSet(request.POST, instance=lista_materiais)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Salvar lista
                    lista = form.save(commit=False)
                    lista.atualizado_por = request.user
                    lista.status = 'editada'
                    lista.save()
                    
                    # Salvar itens
                    formset.save()
                    
                    messages.success(request, 'Lista de materiais atualizada com sucesso!')
                    return redirect('producao:lista_materiais_edit', pk=pk)
                    
            except Exception as e:
                logger.error(f"Erro ao salvar lista de materiais: {str(e)}")
                messages.error(request, f'Erro ao salvar lista: {str(e)}')
        else:
            messages.error(request, 'Erro nos dados. Verifique os campos marcados.')
    else:
        form = ListaMateriaisForm(instance=lista_materiais)
        formset = ItemListaMateriaisFormSet(instance=lista_materiais)
    
    context = {
        'proposta': proposta,
        'lista_materiais': lista_materiais,
        'form': form,
        'formset': formset,
        'total_itens': lista_materiais.itens.count(),
        'valor_total': lista_materiais.calcular_valor_total(),
        'pode_aprovar': lista_materiais.status in ['pronta', 'editada'],
    }
    
    return render(request, 'producao/propostas/lista_materiais_edit.html', context)


@login_required
def lista_materiais_aprovar(request, pk):
    """Aprovar lista de materiais para gerar requisição"""
    proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        lista_materiais = proposta.lista_materiais
    except ListaMateriais.DoesNotExist:
        messages.error(request, 'Proposta não possui lista de materiais.')
        return redirect('producao:proposta_detail_producao', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                lista_materiais.status = 'aprovada'
                lista_materiais.atualizado_por = request.user
                lista_materiais.save()
                
                messages.success(request, 
                    'Lista de materiais aprovada! '
                    'Agora você pode gerar uma requisição de compra.'
                )
                
                # Redirecionar para criar requisição com lista pré-selecionada
                return redirect(f"{reverse('producao:requisicao_compra_create')}?lista_materiais={lista_materiais.pk}")
                
        except Exception as e:
            logger.error(f"Erro ao aprovar lista de materiais: {str(e)}")
            messages.error(request, f'Erro ao aprovar lista: {str(e)}')
    
    context = {
        'proposta': proposta,
        'lista_materiais': lista_materiais,
    }
    
    return render(request, 'producao/propostas/lista_materiais_aprovar.html', context)


# =============================================================================
# AJAX APIs
# =============================================================================

@login_required
def api_produto_info(request):
    """API para buscar informações de produto por código"""
    codigo = request.GET.get('codigo', '')
    
    if not codigo:
        return JsonResponse({'success': False, 'error': 'Código não informado'})
    
    try:
        produto = Produto.objects.get(codigo=codigo, tipo='MP', disponivel=True)
        
        return JsonResponse({
            'success': True,
            'produto': {
                'id': produto.pk,
                'codigo': produto.codigo,
                'nome': produto.nome,
                'unidade_medida': produto.unidade_medida,
                'custo_medio': float(produto.custo_medio or 0),
                'grupo': produto.grupo.nome if produto.grupo else '',
            }
        })
        
    except Produto.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': f'Produto {codigo} não encontrado ou indisponível'
        })