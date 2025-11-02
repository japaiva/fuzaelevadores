# producao/views/propostas_producao.py

import json
import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone

from core.models import Proposta, ListaMateriais, ItemListaMateriais, Produto, Cliente, Usuario
from core.forms import ListaMateriaisForm, ItemListaMateriaisForm, ItemListaMateriaisFormSet
from core.forms.propostas import PropostaFiltroForm
from core.services.calculo_pedido import CalculoPedidoService
from core.views.propostas import proposta_detail_base

logger = logging.getLogger(__name__)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_valor_total_seguro(lista_materiais):
    """
    Helper function para obter valor total de forma segura
    """
    if not lista_materiais:
        return 0
        
    try:
        valor = lista_materiais.calcular_valor_total()
        
        # Se for callable, chama
        if callable(valor):
            return valor()
        
        # Se for None, retorna 0
        if valor is None:
            return 0
            
        # Tenta converter para float
        return float(valor)
        
    except Exception as e:
        logger.warning(f"Erro ao obter valor total: {e}")
        return 0


# =============================================================================
# PROPOSTAS NO PORTAL DE PRODUÇÃO
# =============================================================================

@login_required
def proposta_list_producao(request):
    """
    Lista de propostas para o portal de produção
    ✅ ATUALIZADA: Idêntica ao portal vendedor com filtros completos
    """
    
    # 🎯 TODAS as propostas inicialmente - SEM FILTROS AUTOMÁTICOS
    propostas_list = Proposta.objects.all().select_related('cliente', 'vendedor').order_by('-criado_em')
    
    # Aplicar APENAS os filtros do formulário (idêntico ao vendedor)
    form = PropostaFiltroForm(request.GET)
    if form.is_valid():
        
        # Filtro por status (se selecionado)
        if form.cleaned_data.get('status'):
            propostas_list = propostas_list.filter(status=form.cleaned_data['status'])
        
        # Filtro por modelo de elevador (se selecionado)
        if form.cleaned_data.get('modelo_elevador'):
            propostas_list = propostas_list.filter(modelo_elevador=form.cleaned_data['modelo_elevador'])
        
        # Filtro por cliente (se selecionado)
        if form.cleaned_data.get('cliente'):
            propostas_list = propostas_list.filter(cliente=form.cleaned_data['cliente'])
        
        # Filtro por período (se selecionado)
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
        
        # Filtro por vendedor (se selecionado)
        vendedor_filter = form.cleaned_data.get('vendedor')
        if vendedor_filter:
            propostas_list = propostas_list.filter(vendedor=vendedor_filter)
        
        # Filtro por validade (se selecionado)
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
        
        # Filtro por faixa de valor (se informado)
        if form.cleaned_data.get('valor_min'):
            propostas_list = propostas_list.filter(valor_proposta__gte=form.cleaned_data['valor_min'])
        
        if form.cleaned_data.get('valor_max'):
            propostas_list = propostas_list.filter(valor_proposta__lte=form.cleaned_data['valor_max'])
        
        # Busca textual (se preenchida)
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
    
    return render(request, 'producao/propostas/proposta_list_producao.html', context)


@login_required
def proposta_detail_producao(request, pk):
    """
    Detalhe da proposta no portal de produção
    ✅ CORRIGIDO: Tratamento seguro do calcular_valor_total
    """
    
    # Verificar se já tem lista de materiais
    lista_materiais = None
    valor_total_lista = 0
    
    try:
        proposta = get_object_or_404(Proposta, pk=pk)
        lista_materiais = proposta.lista_materiais
        
        # ✅ CORREÇÃO: Tratamento seguro do valor total
        if lista_materiais:
            valor_total_lista = get_valor_total_seguro(lista_materiais)
                
    except ListaMateriais.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Erro ao buscar lista de materiais: {e}")
    
    # Contexto específico da produção
    extra_context = {
        'is_producao': True,
        'lista_materiais': lista_materiais,
        'pode_gerar_lista': proposta.pode_calcular(),
        'tem_lista': lista_materiais is not None,
        'base_template': 'producao/base_producao.html',
        
        # Informações específicas para produção
        'pode_aprovar': lista_materiais and lista_materiais.status == 'em_edicao',
        'total_itens': lista_materiais.itens.count() if lista_materiais else 0,
        'valor_total': valor_total_lista,  # ✅ CORRIGIDO: Usa variável tratada
    }
    
    # ✅ MUDANÇA PRINCIPAL: Usa template unificado
    return proposta_detail_base(
        request, 
        pk, 
        'base/proposta_detail_unified.html',
        extra_context
    )


@login_required
def lista_materiais_detail(request, pk):
    """
    View para detalhar/gerenciar lista de materiais de uma proposta
    ✅ CORRIGIDO: Tratamento seguro do valor total
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        lista_materiais = proposta.lista_materiais
    except ListaMateriais.DoesNotExist:
        lista_materiais = None
    
    context = {
        'proposta': proposta,
        'lista_materiais': lista_materiais,
        'pode_gerar_lista': proposta.pode_calcular(),
        'tem_lista': lista_materiais is not None,
        'pode_aprovar': lista_materiais and lista_materiais.status == 'em_edicao',
        'total_itens': lista_materiais.itens.count() if lista_materiais else 0,
        'valor_total': get_valor_total_seguro(lista_materiais),  # ✅ CORRIGIDO
    }
    
    return render(request, 'producao/propostas/lista_materiais_detail.html', context)


# =============================================================================
# LISTA DE MATERIAIS - CRUD OPERATIONS
# =============================================================================

@login_required
def gerar_lista_materiais(request, pk):
    """
    Gera/regenera lista de materiais a partir dos cálculos da proposta
    ✅ CORRIGIDO: Status direto para 'em_edicao'
    """
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
                logger.info(f"Lista existente da proposta {proposta.numero} foi excluída para regeneração")
            except ListaMateriais.DoesNotExist:
                pass
            
            # Executar cálculos completos
            logger.info(f"Iniciando cálculo da lista de materiais para proposta {proposta.numero}")
            resultado = CalculoPedidoService.calcular_custos_completo(proposta)
            
            # Converter Decimals para float no resultado antes de salvar no JSON
            custos_serializaveis = {}
            if resultado.get('custos'):
                def converter_decimais(obj):
                    if isinstance(obj, dict):
                        return {k: converter_decimais(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [converter_decimais(item) for item in obj]
                    elif hasattr(obj, '__dict__') and hasattr(obj, '_meta'):  # Modelo Django
                        return str(obj)
                    elif str(type(obj).__name__) == 'Decimal':
                        return float(obj)
                    else:
                        return obj
                
                custos_serializaveis = converter_decimais(resultado.get('custos', {}))
            
            # ✅ CORREÇÃO PRINCIPAL: Criar lista já com status 'em_edicao'
            lista_materiais = ListaMateriais.objects.create(
                proposta=proposta,
                status='em_edicao',  # ✅ MUDANÇA: Direto para "em_edicao" após cálculo
                dados_calculo_original=custos_serializaveis,
                observacoes=f'Lista gerada automaticamente em {timezone.now().strftime("%d/%m/%Y %H:%M")}',
                criado_por=request.user,
                atualizado_por=request.user
            )
            
            # Extrair componentes calculados e criar itens
            componentes = proposta.componentes_calculados
            total_itens_criados = 0
            
            logger.info(f"Processando componentes calculados da proposta {proposta.numero}")
            
            if componentes:
                for categoria, categoria_dados in componentes.items():
                    if isinstance(categoria_dados, dict):
                        # Verificar se tem 'itens' diretamente na categoria
                        if 'itens' in categoria_dados:
                            # Processar itens da categoria
                            for codigo, item_dados in categoria_dados['itens'].items():
                                if isinstance(item_dados, dict) and 'codigo' in item_dados:
                                    total_itens_criados += processar_item_lista(
                                        lista_materiais, item_dados, logger
                                    )
                        else:
                            # Processar subcategorias
                            for subcategoria, sub_dados in categoria_dados.items():
                                if isinstance(sub_dados, dict) and 'itens' in sub_dados:
                                    # Processar itens da subcategoria
                                    for codigo, item_dados in sub_dados['itens'].items():
                                        if isinstance(item_dados, dict) and 'codigo' in item_dados:
                                            total_itens_criados += processar_item_lista(
                                                lista_materiais, item_dados, logger
                                            )
            
            logger.info(f"Lista de materiais criada com {total_itens_criados} itens para proposta {proposta.numero}")
            
            messages.success(request, 
                f'Lista de materiais gerada com sucesso! '
                f'{total_itens_criados} itens criados. '
                f'Status: Em Edição - você pode revisar e editar os itens.'
            )
            
            return redirect('producao:proposta_list_producao')
            
    except Exception as e:
        logger.error(f"Erro ao gerar lista de materiais para proposta {proposta.numero}: {str(e)}")
        messages.error(request, f'Erro ao gerar lista de materiais: {str(e)}')
        return redirect('producao:proposta_detail_producao', pk=pk)

def processar_item_lista(lista_materiais, item_dados, logger):
    """
    Helper function para processar um item da lista de materiais.
    Consolida itens existentes ou cria novos.
    """
    try:
        produto = Produto.objects.get(
            codigo=item_dados['codigo'],
            tipo='MP'  # Apenas matérias-primas
        )

        quantidade_nova = item_dados.get('quantidade', 1)
        valor_unitario_estimado = item_dados.get('valor_unitario', 0)
        observacoes = item_dados.get('explicacao', '')
        unidade = item_dados.get('unidade', produto.unidade_medida)

        # Tentar obter o item existente ou criar um novo
        item_existente, created = ItemListaMateriais.objects.get_or_create(
            lista=lista_materiais,
            produto=produto,
            defaults={
                'quantidade': quantidade_nova,
                'unidade': unidade,
                'valor_unitario_estimado': valor_unitario_estimado,
                'observacoes': observacoes,
                'item_calculado': True
            }
        )

        if not created:
            # Se o item já existia, atualiza a quantidade e outros campos se necessário
            item_existente.quantidade += quantidade_nova
            # Se o valor_unitario_estimado existente for nulo, usa o novo valor
            if not item_existente.valor_unitario_estimado:
                item_existente.valor_unitario_estimado = valor_unitario_estimado
            
            # Adicionar novas observações se não estiverem já presentes
            if observacoes and observacoes not in item_existente.observacoes:
                item_existente.observacoes += f"; {observacoes}"

            item_existente.save()
            logger.info(f"Item {produto.codigo} consolidado. Nova quantidade: {item_existente.quantidade}")
        else:
            logger.info(f"Novo item {produto.codigo} criado.")
            
        return 1

    except Produto.DoesNotExist:
        logger.warning(f"Produto {item_dados['codigo']} não encontrado para lista de materiais.")
        return 0
    except Exception as e:
        logger.error(f"Erro ao processar item {item_dados.get('codigo', 'desconhecido')}: {str(e)}")
        return 0

@login_required
def lista_materiais_edit(request, pk):
    """
    Interface editável para lista de materiais
    ✅ CORRIGIDO: Verificação de status + tratamento seguro do valor total
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar se tem lista de materiais
    try:
        lista_materiais = proposta.lista_materiais
    except ListaMateriais.DoesNotExist:
        messages.error(request, 'Proposta não possui lista de materiais. Gere a lista primeiro.')
        return redirect('producao:proposta_list_producao')
    
    # ✅ VERIFICAÇÃO DE PERMISSÃO: Só pode editar se status for 'em_edicao'
    if lista_materiais.status != 'em_edicao':
        messages.error(request, f'Lista não pode ser editada. Status atual: {lista_materiais.get_status_display()}')
        return redirect('producao:proposta_list_producao')
    
    if request.method == 'POST':
        form = ListaMateriaisForm(request.POST, instance=lista_materiais)
        formset = ItemListaMateriaisFormSet(request.POST, instance=lista_materiais)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Salvar lista
                    lista = form.save(commit=False)
                    lista.atualizado_por = request.user
                    # ✅ MANTER STATUS: Permanece 'em_edicao' após salvar edições
                    lista.save()
                    
                    # Salvar itens
                    formset.save()
                    
                    messages.success(request, 'Lista de materiais atualizada com sucesso!')
                    return redirect('producao:proposta_list_producao')
                    
            except Exception as e:
                logger.error(f"Erro ao salvar lista de materiais: {str(e)}")
                messages.error(request, f'Erro ao salvar lista: {str(e)}')
        else:
            messages.error(request, 'Erro nos dados. Verifique os campos marcados.')
    else:
        form = ListaMateriaisForm(instance=lista_materiais)
        formset = ItemListaMateriaisFormSet(instance=lista_materiais)
    
    # ✅ CORREÇÃO: Tratamento seguro do valor total
    valor_total_lista = get_valor_total_seguro(lista_materiais)
    
    context = {
        'proposta': proposta,
        'lista_materiais': lista_materiais,
        'form': form,
        'formset': formset,
        'total_itens': lista_materiais.itens.count(),
        'valor_total': valor_total_lista,  # ✅ CORRIGIDO
        'pode_aprovar': lista_materiais.status == 'em_edicao',  # ✅ SIMPLIFICADO
    }
    
    return render(request, 'producao/propostas/lista_materiais_edit.html', context)


@login_required
def lista_materiais_aprovar(request, pk):
    """
    Aprovar lista de materiais para gerar requisição
    ✅ CORRIGIDO: Verificação de status simplificada
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    try:
        lista_materiais = proposta.lista_materiais
    except ListaMateriais.DoesNotExist:
        messages.error(request, 'Proposta não possui lista de materiais.')
        return redirect('producao:proposta_list_producao')
    
    # ✅ VERIFICAÇÃO: Só pode aprovar se estiver 'em_edicao'
    if lista_materiais.status != 'em_edicao':
        messages.error(request, f'Lista não pode ser aprovada. Status atual: {lista_materiais.get_status_display()}')
        return redirect('producao:proposta_list_producao')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                lista_materiais.status = 'aprovada'  # ✅ MUDANÇA: 'em_edicao' → 'aprovada'
                lista_materiais.atualizado_por = request.user
                lista_materiais.save()
                
                logger.info(f"Lista de materiais da proposta {proposta.numero} foi aprovada por {request.user}")
                
                messages.success(request, 
                    'Lista de materiais aprovada! '
                    'Agora você pode gerar uma requisição de compra.'
                )
                
                # Redirecionar para criar requisição (se existir) ou voltar para lista
                try:
                    return redirect(f"{reverse('producao:requisicao_compra_create')}?lista_materiais={lista_materiais.pk}")
                except:
                    # Se URL de requisição não existir, voltar para lista de propostas
                    return redirect('producao:proposta_list_producao')
                
        except Exception as e:
            logger.error(f"Erro ao aprovar lista de materiais: {str(e)}")
            messages.error(request, f'Erro ao aprovar lista: {str(e)}')
            return redirect('producao:proposta_list_producao')
    
    context = {
        'proposta': proposta,
        'lista_materiais': lista_materiais,
        'valor_total': get_valor_total_seguro(lista_materiais),  # ✅ CORRIGIDO
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


# =============================================================================
# VIEWS ADICIONAIS PARA CRUD DE ITENS DA LISTA
# =============================================================================

@login_required
def item_lista_materiais_list(request, lista_id):
    """
    Lista simples dos itens da lista de materiais para edição CRUD
    """
    lista_materiais = get_object_or_404(ListaMateriais, pk=lista_id)
    
    # Verificar se pode editar
    if lista_materiais.status != 'em_edicao':
        messages.error(request, f'Lista não pode ser editada. Status: {lista_materiais.get_status_display()}')
        return redirect('producao:proposta_list_producao')
    
    itens = lista_materiais.itens.select_related('produto', 'produto__grupo').order_by('produto__codigo')
    
    context = {
        'lista_materiais': lista_materiais,
        'proposta': lista_materiais.proposta,
        'itens': itens,
        'total_itens': itens.count(),
        'valor_total': get_valor_total_seguro(lista_materiais),
    }
    
    return render(request, 'producao/propostas/item_lista_materiais_list.html', context)


@login_required
def item_lista_materiais_create(request, lista_id):
    """
    Adicionar novo item à lista de materiais
    """
    lista_materiais = get_object_or_404(ListaMateriais, pk=lista_id)
    
    # Verificar se pode editar
    if lista_materiais.status != 'em_edicao':
        messages.error(request, 'Lista não pode ser editada.')
        return redirect('producao:item_lista_materiais_list', lista_id=lista_id)
    
    if request.method == 'POST':
        form = ItemListaMateriaisForm(request.POST)
        if form.is_valid():
            try:
                item = form.save(commit=False)
                item.lista = lista_materiais
                item.item_calculado = False  # Item adicionado manualmente
                item.save()
                
                messages.success(request, f'Item {item.produto.codigo} adicionado com sucesso!')
                return redirect('producao:item_lista_materiais_list', lista_id=lista_id)
                
            except Exception as e:
                logger.error(f"Erro ao criar item: {str(e)}")
                messages.error(request, f'Erro ao criar item: {str(e)}')
        else:
            messages.error(request, 'Erro nos dados do formulário.')
    else:
        form = ItemListaMateriaisForm()
    
    context = {
        'form': form,
        'lista_materiais': lista_materiais,
        'proposta': lista_materiais.proposta,
        'action': 'Adicionar',
    }
    
    return render(request, 'producao/propostas/item_lista_materiais_form.html', context)


@login_required
def item_lista_materiais_edit(request, lista_id, item_id):
    """
    Editar item da lista de materiais
    """
    lista_materiais = get_object_or_404(ListaMateriais, pk=lista_id)
    item = get_object_or_404(ItemListaMateriais, pk=item_id, lista=lista_materiais)
    
    # Verificar se pode editar
    if lista_materiais.status != 'em_edicao':
        messages.error(request, 'Lista não pode ser editada.')
        return redirect('producao:item_lista_materiais_list', lista_id=lista_id)
    
    if request.method == 'POST':
        form = ItemListaMateriaisForm(request.POST, instance=item)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Item {item.produto.codigo} atualizado com sucesso!')
                return redirect('producao:item_lista_materiais_list', lista_id=lista_id)
                
            except Exception as e:
                logger.error(f"Erro ao atualizar item: {str(e)}")
                messages.error(request, f'Erro ao atualizar item: {str(e)}')
        else:
            messages.error(request, 'Erro nos dados do formulário.')
    else:
        form = ItemListaMateriaisForm(instance=item)
    
    context = {
        'form': form,
        'lista_materiais': lista_materiais,
        'proposta': lista_materiais.proposta,
        'item': item,
        'action': 'Editar',
    }
    
    return render(request, 'producao/propostas/item_lista_materiais_form.html', context)


@login_required
def item_lista_materiais_delete(request, lista_id, item_id):
    """
    Excluir item da lista de materiais
    """
    lista_materiais = get_object_or_404(ListaMateriais, pk=lista_id)
    item = get_object_or_404(ItemListaMateriais, pk=item_id, lista=lista_materiais)
    
    # Verificar se pode editar
    if lista_materiais.status != 'em_edicao':
        messages.error(request, 'Lista não pode ser editada.')
        return redirect('producao:item_lista_materiais_list', lista_id=lista_id)
    
    if request.method == 'POST':
        try:
            codigo_produto = item.produto.codigo
            item.delete()
            messages.success(request, f'Item {codigo_produto} excluído com sucesso!')
            
        except Exception as e:
            logger.error(f"Erro ao excluir item: {str(e)}")
            messages.error(request, f'Erro ao excluir item: {str(e)}')
            
        return redirect('producao:item_lista_materiais_list', lista_id=lista_id)
    
    context = {
        'item': item,
        'lista_materiais': lista_materiais,
        'proposta': lista_materiais.proposta,
    }

    return render(request, 'producao/propostas/item_lista_materiais_delete.html', context)


# =============================================================================
# UPLOAD DE PROJETOS
# =============================================================================

@login_required
def upload_projeto_executivo(request, pk):
    """Upload de Projeto Executivo"""
    from django.utils import timezone

    proposta = get_object_or_404(Proposta, pk=pk)

    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']

        # Validar extensão
        if not arquivo.name.lower().endswith('.pdf'):
            messages.error(request, 'Apenas arquivos PDF são permitidos.')
            return redirect('producao:proposta_detail_producao', pk=pk)

        # Salvar arquivo
        proposta.arquivo_projeto_executivo = arquivo
        proposta.data_upload_projeto_executivo = timezone.now()
        proposta.save()

        messages.success(
            request,
            f'Projeto Executivo enviado com sucesso em {proposta.data_upload_projeto_executivo.strftime("%d/%m/%Y às %H:%M")}'
        )
        return redirect('producao:proposta_detail_producao', pk=pk)

    context = {
        'proposta': proposta,
        'tipo_projeto': 'Executivo'
    }

    return render(request, 'producao/propostas/upload_projeto.html', context)


@login_required
def upload_projeto_elevador(request, pk):
    """Upload de Projeto do Elevador"""
    from django.utils import timezone

    proposta = get_object_or_404(Proposta, pk=pk)

    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']

        # Validar extensão
        if not arquivo.name.lower().endswith('.pdf'):
            messages.error(request, 'Apenas arquivos PDF são permitidos.')
            return redirect('producao:proposta_detail_producao', pk=pk)

        # Salvar arquivo
        proposta.arquivo_projeto_elevador = arquivo
        proposta.data_upload_projeto_elevador = timezone.now()
        proposta.save()

        messages.success(
            request,
            f'Projeto do Elevador enviado com sucesso em {proposta.data_upload_projeto_elevador.strftime("%d/%m/%Y às %H:%M")}'
        )
        return redirect('producao:proposta_detail_producao', pk=pk)

    context = {
        'proposta': proposta,
        'tipo_projeto': 'Elevador'
    }

    return render(request, 'producao/propostas/upload_projeto.html', context)