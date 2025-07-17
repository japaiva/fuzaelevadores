# producao/views/produtos_intermediarios.py - ATUALIZADO COM NOVOS TIPOS DE SERVIÇO

"""
CRUD de Produtos Intermediários (Tipo = PI) 
Portal de Produção - Sistema Elevadores FUZA
ATUALIZADO: Suporte para SERVICO_INTERNO e SERVICO_EXTERNO
"""

import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods

# IMPORTS PRINCIPAIS
from core.models import Produto, GrupoProduto, SubgrupoProduto #
from core.forms import ProdutoForm #

# IMPORT CONDICIONAL DA ESTRUTURA
try:
    from core.models import EstruturaProduto #
    ESTRUTURA_DISPONIVEL = True #
except ImportError:
    EstruturaProduto = None #
    ESTRUTURA_DISPONIVEL = False #

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD PRODUTOS INTERMEDIÁRIOS - OTIMIZADO PARA ESTRUTURAS
# =============================================================================

@login_required
def produto_intermediario_list(request):
    """Lista produtos PI com informações de estrutura otimizadas"""
    
    # QUERY OTIMIZADA COM PREFETCH PARA ESTRUTURAS
    produtos_query = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='PI') #
    
    # Adicionar prefetch de estrutura se disponível
    if ESTRUTURA_DISPONIVEL: #
        produtos_query = produtos_query.prefetch_related(
            Prefetch(
                'componentes',
                queryset=EstruturaProduto.objects.select_related(
                    'produto_filho', 'produto_filho__grupo'
                )
            )
        ) #
    
    produtos_list = produtos_query.order_by('codigo')

    # Filtros existentes (mantidos)
    grupo_id = request.GET.get('grupo')
    if grupo_id and grupo_id.isdigit():
        produtos_list = produtos_list.filter(grupo_id=grupo_id)
    else:
        grupo_id = None

    subgrupo_id = request.GET.get('subgrupo')
    if subgrupo_id and subgrupo_id.isdigit():
        produtos_list = produtos_list.filter(subgrupo_id=subgrupo_id)
    else:
        subgrupo_id = None

    status = request.GET.get('status')
    if status == 'ativo':
        produtos_list = produtos_list.filter(status='ATIVO')
    elif status == 'inativo':
        produtos_list = produtos_list.filter(status='INATIVO')
    elif status == 'disponivel':
        produtos_list = produtos_list.filter(disponivel=True)
    elif status == 'indisponivel':
        produtos_list = produtos_list.filter(disponivel=False)

    utilizado = request.GET.get('utilizado')
    if utilizado == 'utilizado':
        produtos_list = produtos_list.filter(utilizado=True)
    elif utilizado == 'nao_utilizado':
        produtos_list = produtos_list.filter(utilizado=False)

    tipo_pi = request.GET.get('tipo_pi')
    if tipo_pi and tipo_pi in dict(Produto.TIPO_PI_CHOICES): #
        produtos_list = produtos_list.filter(tipo_pi=tipo_pi)

    query = request.GET.get('q')
    if query:
        produtos_list = produtos_list.filter(
            Q(codigo__icontains=query) |
            Q(nome__icontains=query) |
            Q(descricao__icontains=query)
        )

    # Paginação
    paginator = Paginator(produtos_list, 20)
    page = request.GET.get('page', 1)

    try:
        produtos = paginator.page(page)
    except PageNotAnInteger:
        produtos = paginator.page(1)
    except EmptyPage:
        produtos = paginator.page(paginator.num_pages)

    # Para os filtros
    grupos = GrupoProduto.objects.filter(ativo=True, tipo_produto='PI').order_by('codigo') #
    
    if grupo_id:
        subgrupos = SubgrupoProduto.objects.filter(
            grupo_id=grupo_id, ativo=True
        ).order_by('codigo') #
    else:
        subgrupos = SubgrupoProduto.objects.filter(
            grupo__tipo_produto='PI', ativo=True
        ).select_related('grupo').order_by('grupo__codigo', 'codigo') #

    return render(request, 'producao/produtos/produto_intermediario_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'subgrupos': subgrupos,
        'grupo_filtro': grupo_id,
        'subgrupo_filtro': subgrupo_id,
        'status_filtro': status,
        'utilizado_filtro': utilizado,
        'tipo_pi_filtro': tipo_pi,
        'tipo_pi_choices': Produto.TIPO_PI_CHOICES, #
        'query': query,
        'estrutura_disponivel': ESTRUTURA_DISPONIVEL, #
    })


@login_required
def produto_intermediario_create(request):
    """Criar novo produto intermediário"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST) #
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PI' #
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.save()
            messages.success(request, f'Produto intermediário "{produto.codigo} - {produto.nome}" criado com sucesso.')
            return redirect('producao:produto_intermediario_list')
        else:
            messages.error(request, 'Erro ao criar produto intermediário. Verifique os dados informados.')
    else:
        form = ProdutoForm() #
    
    # FIX: Filtrar o queryset do campo 'grupo' para mostrar apenas grupos do tipo 'PI'
    form.fields['grupo'].queryset = GrupoProduto.objects.filter(tipo_produto='PI', ativo=True).order_by('codigo') #

    return render(request, 'producao/produtos/produto_intermediario_form.html', {'form': form}) #


@login_required
def produto_intermediario_update(request, pk):
    """Editar produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI') #
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto) #
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'PI' #
            produto.atualizado_por = request.user
            produto.save()
            messages.success(request, f'Produto intermediário "{produto.codigo} - {produto.nome}" atualizado com sucesso.')
            return redirect('producao:produto_intermediario_list')
        else:
            messages.error(request, 'Erro ao atualizar produto intermediário. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto) #

    # FIX: Filtrar o queryset do campo 'grupo' para mostrar apenas grupos do tipo 'PI'
    form.fields['grupo'].queryset = GrupoProduto.objects.filter(tipo_produto='PI', ativo=True).order_by('codigo') #

    return render(request, 'producao/produtos/produto_intermediario_form.html', {
        'form': form, 'produto': produto
    }) #


@login_required
def produto_intermediario_delete(request, pk):
    """Excluir produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI') #
    if request.method == 'POST':
        try:
            codigo_nome = f"{produto.codigo} - {produto.nome}"
            if ESTRUTURA_DISPONIVEL and hasattr(produto, 'usado_em'): #
                if produto.usado_em.exists():
                    estruturas_onde_usado = produto.usado_em.select_related('produto_pai').all()
                    produtos_pai = [e.produto_pai.codigo for e in estruturas_onde_usado]
                    messages.error(request, f'Não é possível excluir "{codigo_nome}" pois é usado como componente em: {", ".join(produtos_pai)}.')
                    return redirect('producao:produto_intermediario_list')
            produto.delete()
            messages.success(request, f'Produto intermediário "{codigo_nome}" excluído com sucesso.')
        except Exception as e:
            logger.error(f'Erro ao excluir produto intermediário {produto.codigo}: {str(e)}')
            messages.error(request, f'Erro ao excluir produto intermediário: {str(e)}')
        return redirect('producao:produto_intermediario_list')

    context = {'produto': produto, 'estrutura_disponivel': ESTRUTURA_DISPONIVEL} #
    if ESTRUTURA_DISPONIVEL and hasattr(produto, 'usado_em'): #
        context.update({
            'estruturas_onde_usado': produto.usado_em.select_related('produto_pai').all(),
            'tem_estrutura_propria': hasattr(produto, 'componentes') and produto.componentes.exists(), #
            'total_componentes': produto.componentes.count() if hasattr(produto, 'componentes') else 0, #
        })
    return render(request, 'producao/produtos/produto_intermediario_delete.html', context) #


@login_required
def produto_intermediario_toggle_status(request, pk):
    """Ativar/desativar produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI') #
    produto.status = 'INATIVO' if produto.status == 'ATIVO' else 'ATIVO' #
    produto.atualizado_por = request.user
    produto.save()
    status_text = "desativado" if produto.status == 'INATIVO' else "ativado"
    messages.success(request, f'Produto intermediário "{produto.nome}" {status_text} com sucesso.')
    return redirect('producao:produto_intermediario_list')


@login_required
def produto_intermediario_toggle_utilizado(request, pk):
    """Toggle do campo utilizado para produto intermediário"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI') #
    produto.utilizado = not produto.utilizado #
    produto.atualizado_por = request.user
    produto.save()
    utilizado_text = "marcado como utilizado" if produto.utilizado else "marcado como não utilizado"
    messages.success(request, f'Produto intermediário "{produto.nome}" {utilizado_text} com sucesso.')
    return redirect('producao:produto_intermediario_list')


# =============================================================================
# FUNCIONALIDADE PRINCIPAL: ESTRUTURA DE COMPONENTES - CORRIGIDA
# =============================================================================

@login_required
def produto_intermediario_estrutura(request, pk):
    """
    Gerenciar estrutura de componentes de produto intermediário
    CORRIGIDO: Agora carrega componentes existentes do banco de dados
    """
    produto = get_object_or_404(Produto, pk=pk, tipo='PI') #
    
    if not ESTRUTURA_DISPONIVEL: #
        messages.info(request, 'A funcionalidade de estrutura de componentes será implementada em breve.')
        return redirect('producao:produto_intermediario_list')
    
    if not produto.pode_ter_estrutura: #
        messages.warning(request, f'O produto "{produto.nome}" do tipo "{produto.get_tipo_pi_display()}" não suporta estrutura de componentes.')
        return redirect('producao:produto_intermediario_list')
    
    # CARREGAR COMPONENTES EXISTENTES COM OTIMIZAÇÃO
    try:
        componentes_existentes = produto.componentes.select_related(
            'produto_filho', 'produto_filho__grupo', 'produto_filho__subgrupo'
        ).order_by('produto_filho__codigo') #
        
        total_componentes = componentes_existentes.count()
        
        # CALCULAR CUSTO TOTAL DA ESTRUTURA
        custo_calculado = 0
        for componente in componentes_existentes:
            custo_unitario = componente.produto_filho.custo_total if hasattr(componente.produto_filho, 'custo_total') else 0 #
            quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100)) #
            custo_calculado += custo_unitario * quantidade_com_perda
            
        logger.info(f'Produto {produto.codigo}: {total_componentes} componentes, custo R$ {custo_calculado:.2f}')
            
    except Exception as e:
        logger.error(f'Erro ao carregar estrutura do produto {produto.codigo}: {str(e)}')
        componentes_existentes = EstruturaProduto.objects.none()
        total_componentes = 0
        custo_calculado = 0
    
    context = {
        'produto': produto,
        'componentes_existentes': componentes_existentes,
        'total_componentes': total_componentes,
        'custo_calculado': custo_calculado,
        'estrutura_disponivel': ESTRUTURA_DISPONIVEL, #
        'custo_atual_produto': produto.custo_medio or 0, #
    }
    
    return render(request, 'producao/produtos/produto_intermediario_estrutura.html', context) #


@login_required
def produto_intermediario_calcular_custo(request, pk):
    """Calcular custo de produto intermediário baseado na estrutura"""
    produto = get_object_or_404(Produto, pk=pk, tipo='PI') #
    
    if not ESTRUTURA_DISPONIVEL: #
        messages.info(request, 'Funcionalidade de cálculo de custo será implementada quando a estrutura estiver pronta.')
        return redirect('producao:produto_intermediario_list')
    
    if not produto.pode_ter_estrutura: #
        messages.error(request, f'O produto "{produto.nome}" não suporta cálculo automático de custo.')
        return redirect('producao:produto_intermediario_list')
    
    try:
        if not produto.componentes.exists(): #
            messages.warning(request, f'O produto "{produto.nome}" não possui estrutura de componentes definida.')
            return redirect('producao:produto_intermediario_estrutura', pk=pk)
        
        # CALCULAR CUSTO BASEADO NA ESTRUTURA REAL
        custo_calculado = 0
        componentes_processados = 0
        
        for componente in produto.componentes.select_related('produto_filho'): #
            produto_filho = componente.produto_filho #
            custo_unitario = produto_filho.custo_total if hasattr(produto_filho, 'custo_total') else (produto_filho.custo_medio or 0) #
            
            if custo_unitario > 0:
                quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100)) #
                custo_componente = custo_unitario * quantidade_com_perda
                custo_calculado += custo_componente
                componentes_processados += 1
            else:
                logger.warning(f'Componente {produto_filho.codigo} sem custo definido')
        
        if componentes_processados == 0:
            messages.error(request, 'Nenhum componente possui custo definido. Verifique os custos dos componentes primeiro.')
            return redirect('producao:produto_intermediario_estrutura', pk=pk)
        
        if custo_calculado > 0:
            custo_anterior = produto.custo_medio or 0
            produto.custo_medio = custo_calculado #
            produto.atualizado_por = request.user
            produto.save(update_fields=['custo_medio', 'atualizado_por', 'atualizado_em'])
            
            messages.success(request, f'Custo recalculado para "{produto.nome}": R$ {custo_anterior:.2f} → R$ {custo_calculado:.2f}')
            logger.info(f'Custo aplicado no produto {produto.codigo}: R$ {custo_anterior:.2f} → R$ {custo_calculado:.2f}')
        else:
            messages.error(request, 'Custo calculado resultou em R$ 0,00. Verifique os custos dos componentes.')
            
    except Exception as e:
        logger.error(f'Erro ao calcular custo do produto {produto.codigo}: {str(e)}')
        messages.error(request, f'Erro ao calcular custo: {str(e)}')
    
    return redirect('producao:produto_intermediario_list')


# =============================================================================
# API ATUALIZADA PARA NOVOS TIPOS DE SERVIÇO
# =============================================================================

@login_required
def api_tipo_pi_info(request):
    """API para retornar informações sobre tipos de PI via AJAX - ATUALIZADA"""
    tipo_pi = request.GET.get('tipo_pi')
    
    if not tipo_pi or tipo_pi not in dict(Produto.TIPO_PI_CHOICES): #
        return JsonResponse({'success': False, 'error': 'Tipo PI inválido'})
    
    # ATUALIZADA: Incluindo novos tipos de serviço
    tipo_info = {
        'COMPRADO': {
            'descricao': 'Produto pronto adquirido de fornecedor', #
            'pode_estrutura': False, #
            'custo_manual': True, #
            'campos_obrigatorios': ['fornecedor_principal', 'custo_medio'], #
            'exemplo': 'Porta cabine pronta, Motor de elevador, Botoeira completa' #
        },
        'MONTADO_INTERNO': {
            'descricao': 'Produto montado internamente na fábrica', #
            'pode_estrutura': True, #
            'custo_manual': False, #
            'campos_obrigatorios': [], #
            'exemplo': 'Porta montada com perfis próprios, Quadro de comando customizado' #
        },
        'MONTADO_EXTERNO': {
            'descricao': 'Produto montado por terceiros (terceirizado)', #
            'pode_estrutura': True, #
            'custo_manual': False, #
            'campos_obrigatorios': ['fornecedor_principal'], #
            'exemplo': 'Painel cortado/dobrado, Porta montada por terceiro' #
        },
        'SERVICO_INTERNO': {
            'descricao': 'Serviço prestado internamente pela empresa', #
            'pode_estrutura': False, #
            'custo_manual': True, #
            'campos_obrigatorios': ['custo_industrializacao'], #
            'exemplo': 'Mão de obra montagem, Projeto técnico, Supervisão' #
        },
        'SERVICO_EXTERNO': {
            'descricao': 'Serviço prestado por terceiros', #
            'pode_estrutura': False, #
            'custo_manual': True, #
            'campos_obrigatorios': ['fornecedor_principal', 'custo_industrializacao'], #
            'exemplo': 'Transporte, Instalação terceirizada, Consultoria externa' #
        }
    }
    
    return JsonResponse({
        'success': True,
        'tipo_pi': tipo_pi,
        'estrutura_disponivel': ESTRUTURA_DISPONIVEL, #
        'info': tipo_info.get(tipo_pi, {})
    })


@login_required
def relatorio_produtos_pi_por_tipo(request):
    """Relatório de produtos intermediários agrupados por tipo - ATUALIZADO"""
    from django.db.models import Count, Avg
    
    stats_por_tipo = []
    
    # ATUALIZADA: Usando os novos choices
    for tipo_codigo, tipo_nome in Produto.TIPO_PI_CHOICES: #
        produtos = Produto.objects.filter(tipo='PI', tipo_pi=tipo_codigo)
        
        if produtos.exists():
            stats = {
                'tipo_codigo': tipo_codigo,
                'tipo_nome': tipo_nome,
                'total_produtos': produtos.count(),
                'produtos_ativos': produtos.filter(status='ATIVO').count(),
                'produtos_com_custo': produtos.filter(custo_medio__isnull=False).count(),
                'custo_medio': produtos.filter(custo_medio__isnull=False).aggregate(media=Avg('custo_medio'))['media'] or 0,
                'pode_estrutura': tipo_codigo in ['MONTADO_INTERNO', 'MONTADO_EXTERNO'], #
            }
            
            if stats['pode_estrutura'] and ESTRUTURA_DISPONIVEL: #
                try:
                    stats['produtos_com_estrutura'] = produtos.filter(componentes__isnull=False).distinct().count()
                except Exception:
                    stats['produtos_com_estrutura'] = 0
            else:
                stats['produtos_com_estrutura'] = 0
            
            stats_por_tipo.append(stats)
    
    produtos_sem_tipo = Produto.objects.filter(tipo='PI', tipo_pi__isnull=True).count()
    
    context = {
        'stats_por_tipo': stats_por_tipo,
        'produtos_sem_tipo': produtos_sem_tipo,
        'total_pi': Produto.objects.filter(tipo='PI').count(),
        'estrutura_disponivel': ESTRUTURA_DISPONIVEL, #
    }
    
    return render(request, 'producao/relatorios/produtos_pi_por_tipo.html', context) #


# =============================================================================
# APIs AJAX PARA ESTRUTURA - MANTIDAS IGUAIS
# =============================================================================

@login_required
@require_http_methods(["GET"])
def api_listar_componentes_estrutura(request, produto_id):
    """API PRINCIPAL: Listar componentes da estrutura em tempo real"""
    if not ESTRUTURA_DISPONIVEL: #
        return JsonResponse({'success': False, 'error': 'Funcionalidade ainda não disponível'})
    
    try:
        produto = get_object_or_404(Produto, pk=produto_id, tipo='PI') #
        
        logger.info(f'📊 API: Listando componentes para produto {produto.codigo}')
        
        if not produto.pode_ter_estrutura: #
            return JsonResponse({
                'success': True, 
                'componentes': [],
                'total': 0,
                'message': f'Produto "{produto.nome}" não suporta estrutura de componentes',
                'produto': {
                    'id': str(produto.pk),
                    'codigo': produto.codigo,
                    'nome': produto.nome,
                    'tipo_pi': produto.tipo_pi
                }
            })
        
        # BUSCAR COMPONENTES COM RELACIONAMENTOS OTIMIZADOS
        componentes = produto.componentes.select_related(
            'produto_filho', 'produto_filho__grupo', 'produto_filho__subgrupo'
        ).order_by('produto_filho__codigo') #
        
        componentes_data = []
        custo_total_estrutura = 0
        
        for componente in componentes:
            try:
                # CALCULAR CUSTOS CORRETAMENTE
                custo_unitario = 0
                if hasattr(componente.produto_filho, 'custo_total'): #
                    custo_unitario = componente.produto_filho.custo_total or 0 #
                elif componente.produto_filho.custo_medio: #
                    custo_unitario = componente.produto_filho.custo_medio #
                
                quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100)) #
                custo_total_componente = custo_unitario * quantidade_com_perda #
                custo_total_estrutura += custo_total_componente
                
                componente_data = {
                    'id': componente.id,
                    'produto_filho': {
                        'id': str(componente.produto_filho.pk),
                        'codigo': componente.produto_filho.codigo,
                        'nome': componente.produto_filho.nome,
                        'tipo': componente.produto_filho.tipo,
                        'custo_total': float(custo_unitario),
                        'grupo_nome': componente.produto_filho.grupo.nome if componente.produto_filho.grupo else '',
                        'subgrupo_nome': componente.produto_filho.subgrupo.nome if componente.produto_filho.subgrupo else ''
                    },
                    'quantidade': float(componente.quantidade),
                    'unidade': componente.unidade,
                    'percentual_perda': float(componente.percentual_perda),
                    'quantidade_com_perda': float(quantidade_com_perda),
                    'custo_total': float(custo_total_componente)
                }
                
                componentes_data.append(componente_data)
                logger.debug(f'Componente {componente.produto_filho.codigo}: R$ {custo_total_componente:.2f}')
                
            except Exception as e:
                logger.error(f'Erro ao processar componente {componente.id}: {str(e)}')
                continue
        
        logger.info(f'✅ API: Retornando {len(componentes_data)} componentes, custo total R$ {custo_total_estrutura:.2f}')
        
        return JsonResponse({
            'success': True,
            'componentes': componentes_data,
            'total': len(componentes_data),
            'custo_total_estrutura': float(custo_total_estrutura),
            'produto': {
                'id': str(produto.pk),
                'codigo': produto.codigo,
                'nome': produto.nome,
                'tipo_pi': produto.tipo_pi,
                'custo_atual': float(produto.custo_medio or 0)
            }
        })
        
    except Produto.DoesNotExist:
        logger.error(f'Produto {produto_id} não encontrado')
        return JsonResponse({'success': False, 'error': 'Produto não encontrado'}, status=404)
        
    except Exception as e:
        logger.error(f'Erro ao listar componentes do produto {produto_id}: {str(e)}')
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_buscar_produtos_estrutura(request):
    """API para buscar produtos (MP e PI) para adicionar na estrutura"""
    if not ESTRUTURA_DISPONIVEL: #
        return JsonResponse({'success': False, 'error': 'Funcionalidade ainda não disponível'})
    
    termo = request.GET.get('q', '').strip()
    produto_pai_id = request.GET.get('produto_pai_id')
    
    if not termo or len(termo) < 2:
        return JsonResponse({'success': True, 'produtos': []})
    
    try:
        produtos_query = Produto.objects.filter(
            Q(codigo__icontains=termo) | Q(nome__icontains=termo) | Q(descricao__icontains=termo),
            tipo__in=['MP', 'PI'], status='ATIVO', disponivel=True
        ).select_related('grupo', 'subgrupo') #
        
        if produto_pai_id:
            produtos_query = produtos_query.exclude(pk=produto_pai_id)
        
        produtos_query = produtos_query.order_by('codigo')[:20]
        
        produtos_data = []
        for produto in produtos_query:
            produtos_data.append({
                'id': str(produto.pk),
                'codigo': produto.codigo,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'tipo_display': produto.get_tipo_display(),
                'unidade_medida': produto.unidade_medida, #
                'custo_medio': float(produto.custo_medio) if produto.custo_medio else 0.0, #
                'custo_industrializacao': float(produto.custo_industrializacao) if produto.custo_industrializacao else 0.0, #
                'custo_total': float(produto.custo_total) if hasattr(produto, 'custo_total') else 0.0, #
                'grupo_nome': produto.grupo.nome if produto.grupo else '',
                'subgrupo_nome': produto.subgrupo.nome if produto.subgrupo else '',
                'estoque_atual': float(produto.estoque_atual) if produto.estoque_atual else 0.0, #
                'texto_completo': f"{produto.codigo} - {produto.nome}",
                'disponibilidade': produto.disponibilidade_info if hasattr(produto, 'disponibilidade_info') else {'disponivel': True} #
            })
        
        return JsonResponse({
            'success': True,
            'produtos': produtos_data,
            'total_encontrados': len(produtos_data),
            'termo_busca': termo
        })
        
    except Exception as e:
        logger.error(f'Erro na API de busca de produtos para estrutura: {str(e)}')
        return JsonResponse({'success': False, 'error': f'Erro ao buscar produtos: {str(e)}'}, status=500)

@login_required
@require_http_methods(["POST"])
def api_adicionar_componente_estrutura(request):
    """API para adicionar componente à estrutura"""
    if not ESTRUTURA_DISPONIVEL: #
        return JsonResponse({'success': False, 'error': 'Funcionalidade ainda não disponível'})
    
    try:
        data = json.loads(request.body)
        
        produto_pai_id = data.get('produto_pai_id')
        produto_filho_id = data.get('produto_filho_id')
        quantidade = data.get('quantidade')
        unidade = data.get('unidade')
        percentual_perda = data.get('percentual_perda', 0)
        
        if not all([produto_pai_id, produto_filho_id, quantidade, unidade]):
            return JsonResponse({'success': False, 'error': 'Dados obrigatórios não informados'}, status=400)
        
        produto_pai = get_object_or_404(Produto, pk=produto_pai_id, tipo='PI') #
        produto_filho = get_object_or_404(Produto, pk=produto_filho_id, tipo__in=['MP', 'PI']) #
        
        if not produto_pai.pode_ter_estrutura: #
            return JsonResponse({'success': False, 'error': f'Produto "{produto_pai.nome}" não suporta estrutura de componentes'}, status=400)
        
        if EstruturaProduto.objects.filter(produto_pai=produto_pai, produto_filho=produto_filho).exists(): #
            return JsonResponse({'success': False, 'error': f'Componente "{produto_filho.codigo}" já está na estrutura'}, status=400)
        
        with transaction.atomic():
            componente = EstruturaProduto.objects.create(
                produto_pai=produto_pai,
                produto_filho=produto_filho,
                quantidade=float(quantidade),
                unidade=unidade,
                percentual_perda=float(percentual_perda),
                criado_por=request.user
            ) #
            
            logger.info(f'Componente adicionado: {produto_pai.codigo} → {produto_filho.codigo} (qtd: {quantidade})')
        
        # Calcular custos
        custo_unitario = produto_filho.custo_total if hasattr(produto_filho, 'custo_total') else (produto_filho.custo_medio or 0) #
        quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100)) #
        custo_total = custo_unitario * quantidade_com_perda #
        
        return JsonResponse({
            'success': True,
            'componente': {
                'id': componente.id,
                'produto_filho': {
                    'id': str(produto_filho.pk),
                    'codigo': produto_filho.codigo,
                    'nome': produto_filho.nome,
                    'tipo': produto_filho.tipo,
                    'custo_total': float(custo_unitario)
                },
                'quantidade': float(componente.quantidade),
                'unidade': componente.unidade,
                'percentual_perda': float(componente.percentual_perda),
                'quantidade_com_perda': float(quantidade_com_perda),
                'custo_total': float(custo_total)
            },
            'message': f'Componente "{produto_filho.codigo}" adicionado com sucesso!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f'Erro ao adicionar componente: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_editar_componente_estrutura(request, componente_id):
    """API para editar componente da estrutura"""
    if not ESTRUTURA_DISPONIVEL: #
        return JsonResponse({'success': False, 'error': 'Funcionalidade ainda não disponível'})
    
    try:
        data = json.loads(request.body)
        componente = get_object_or_404(EstruturaProduto, pk=componente_id) #
        
        if 'quantidade' in data:
            componente.quantidade = float(data['quantidade'])
        if 'percentual_perda' in data:
            componente.percentual_perda = float(data['percentual_perda'])
        if 'unidade' in data:
            componente.unidade = data['unidade']
        
        componente.save()
        logger.info(f'Componente editado: {componente.id} - nova qtd: {componente.quantidade}')
        
        # Recalcular custos
        custo_unitario = componente.produto_filho.custo_total if hasattr(componente.produto_filho, 'custo_total') else (componente.produto_filho.custo_medio or 0) #
        quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100)) #
        custo_total = custo_unitario * quantidade_com_perda #
        
        return JsonResponse({
            'success': True,
            'componente': {
                'id': componente.id,
                'quantidade': float(componente.quantidade),
                'unidade': componente.unidade,
                'percentual_perda': float(componente.percentual_perda),
                'quantidade_com_perda': float(quantidade_com_perda),
                'custo_total': float(custo_total)
            },
            'message': 'Componente atualizado com sucesso!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f'Erro ao editar componente {componente_id}: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_remover_componente_estrutura(request, componente_id):
    """API para remover componente da estrutura"""
    if not ESTRUTURA_DISPONIVEL: #
        return JsonResponse({'success': False, 'error': 'Funcionalidade ainda não disponível'})
    
    try:
        componente = get_object_or_404(EstruturaProduto, pk=componente_id) #
        produto_pai_codigo = componente.produto_pai.codigo
        produto_filho_codigo = componente.produto_filho.codigo
        
        componente.delete()
        logger.info(f'Componente removido: {produto_pai_codigo} → {produto_filho_codigo}')
        
        return JsonResponse({
            'success': True,
            'message': f'Componente "{produto_filho_codigo}" removido com sucesso!'
        })
        
    except Exception as e:
        logger.error(f'Erro ao remover componente {componente_id}: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_aplicar_custo_estrutura(request, produto_id):
    """API para aplicar custo calculado da estrutura no produto"""
    if not ESTRUTURA_DISPONIVEL: #
        return JsonResponse({'success': False, 'error': 'Funcionalidade ainda não disponível'})
    
    try:
        produto = get_object_or_404(Produto, pk=produto_id, tipo='PI') #
        
        if not produto.pode_ter_estrutura: #
            return JsonResponse({'success': False, 'error': f'Produto "{produto.nome}" não suporta cálculo de custo por estrutura'}, status=400)
        
        if not produto.componentes.exists(): #
            return JsonResponse({'success': False, 'error': 'Produto não possui estrutura de componentes definida'}, status=400)
        
        # Calcular custo baseado na estrutura
        custo_anterior = produto.custo_medio or 0 #
        custo_calculado = 0
        
        for componente in produto.componentes.select_related('produto_filho'): #
            custo_unitario = componente.produto_filho.custo_total if hasattr(componente.produto_filho, 'custo_total') else (componente.produto_filho.custo_medio or 0) #
            if custo_unitario > 0:
                quantidade_com_perda = componente.quantidade * (1 + (componente.percentual_perda / 100)) #
                custo_calculado += custo_unitario * quantidade_com_perda
        
        if custo_calculado <= 0:
            return JsonResponse({'success': False, 'error': 'Não foi possível calcular o custo. Verifique se todos os componentes têm custos definidos.'}, status=400)
        
        # Aplicar o custo calculado
        with transaction.atomic():
            produto.custo_medio = custo_calculado
            produto.atualizado_por = request.user
            produto.save(update_fields=['custo_medio', 'atualizado_por', 'atualizado_em'])
        
        logger.info(f'Custo aplicado no produto {produto.codigo}: R$ {custo_anterior:.2f} → R$ {custo_calculado:.2f}')
        
        return JsonResponse({
            'success': True,
            'custo_anterior': float(custo_anterior),
            'custo_novo': float(custo_calculado),
            'diferenca': float(custo_calculado - custo_anterior),
            'produto_codigo': produto.codigo,
            'produto_nome': produto.nome,
            'message': f'Custo atualizado: R$ {custo_anterior:.2f} → R$ {custo_calculado:.2f}'
        })
        
    except Exception as e:
        logger.error(f'Erro ao aplicar custo no produto {produto_id}: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)