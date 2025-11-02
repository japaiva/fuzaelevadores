# producao/views/materias_primas.py

"""
CRUD de Matérias-Primas (Tipo = MP)
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models import Produto, GrupoProduto, SubgrupoProduto
from core.forms import ProdutoForm

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD MATÉRIAS-PRIMAS (TIPO = MP)
# =============================================================================

@login_required
def materiaprima_list(request):
    """Lista apenas produtos do tipo Matéria Prima (MP)"""
    produtos_list = Produto.objects.select_related(
        'grupo', 'subgrupo', 'fornecedor_principal'
    ).filter(tipo='MP').order_by('codigo')

    # Filtros
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

    grupos = GrupoProduto.objects.filter(ativo=True, tipo_produto='MP').order_by('codigo')

    if grupo_id:
        subgrupos = SubgrupoProduto.objects.filter(
            grupo_id=grupo_id,
            ativo=True
        ).order_by('codigo')
    else:
        subgrupos = SubgrupoProduto.objects.filter(
            grupo__tipo_produto='MP',
            ativo=True
        ).select_related('grupo').order_by('grupo__codigo', 'codigo')

    return render(request, 'producao/produtos/materiaprima_list.html', {
        'produtos': produtos,
        'grupos': grupos,
        'subgrupos': subgrupos,
        'grupo_filtro': grupo_id,
        'subgrupo_filtro': subgrupo_id,
        'status_filtro': status,
        'utilizado_filtro': utilizado,
        'query': query
    })

@login_required
def materiaprima_create(request):
    """Criar nova matéria-prima"""
    if request.method == 'POST':
        post_data = request.POST.copy()
        
        if 'estoque_minimo' in post_data and not post_data['estoque_minimo']:
            post_data['estoque_minimo'] = None

        form = ProdutoForm(post_data)

        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'MP'
            produto.criado_por = request.user
            produto.atualizado_por = request.user
            produto.tipo_pi = None
            produto.save()

            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" criada com sucesso.')
            return redirect('producao:materiaprima_list')
        else:
            messages.error(request, 'Erro ao criar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm()

    # FIX: Filtrar o queryset do campo 'grupo' para mostrar apenas grupos do tipo 'MP'
    form.fields['grupo'].queryset = GrupoProduto.objects.filter(tipo_produto='MP', ativo=True).order_by('codigo')

    return render(request, 'producao/produtos/materiaprima_form.html', {'form': form})

@login_required
def materiaprima_update(request, pk):
    """Editar matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')

    # Preservar parâmetros de paginação e filtros
    page = request.GET.get('page', '1')
    grupo = request.GET.get('grupo', '')
    subgrupo = request.GET.get('subgrupo', '')
    status = request.GET.get('status', '')
    utilizado = request.GET.get('utilizado', '')
    query = request.GET.get('q', '')

    if request.method == 'POST':
        post_data = request.POST.copy()

        if 'estoque_minimo' in post_data and not post_data['estoque_minimo']:
            post_data['estoque_minimo'] = None

        form = ProdutoForm(post_data, instance=produto)

        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'MP'
            produto.atualizado_por = request.user
            produto.tipo_pi = None
            produto.save()

            messages.success(request, f'Matéria-prima "{produto.codigo} - {produto.nome}" atualizada com sucesso.')

            # Construir URL de redirect com parâmetros preservados
            redirect_url = 'producao:materiaprima_list'
            params = []
            if page and page != '1':
                params.append(f'page={page}')
            if grupo:
                params.append(f'grupo={grupo}')
            if subgrupo:
                params.append(f'subgrupo={subgrupo}')
            if status:
                params.append(f'status={status}')
            if utilizado:
                params.append(f'utilizado={utilizado}')
            if query:
                params.append(f'q={query}')

            if params:
                from django.urls import reverse
                url = reverse(redirect_url) + '?' + '&'.join(params)
                return redirect(url)
            else:
                return redirect(redirect_url)
        else:
            messages.error(request, 'Erro ao atualizar matéria-prima. Verifique os dados informados.')
    else:
        form = ProdutoForm(instance=produto)

    # FIX: Filtrar o queryset do campo 'grupo' para mostrar apenas grupos do tipo 'MP'
    form.fields['grupo'].queryset = GrupoProduto.objects.filter(tipo_produto='MP', ativo=True).order_by('codigo')

    return render(request, 'producao/produtos/materiaprima_form.html', {
        'form': form,
        'produto': produto,
        'return_params': {
            'page': page, 'grupo': grupo, 'subgrupo': subgrupo,
            'status': status, 'utilizado': utilizado, 'q': query
        }
    })

@login_required
def materiaprima_detail(request, pk):
    """Visualizar detalhes de uma matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')
    context = {'produto': produto}
    return render(request, 'producao/produtos/materiaprima_detail.html', context)


@login_required
def materiaprima_delete(request, pk):
    """Excluir matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')

    if request.method == 'POST':
        try:
            codigo_nome = f"{produto.codigo} - {produto.nome}"
            produto.delete()
            messages.success(request, f'Matéria-prima "{codigo_nome}" excluída com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir matéria-prima: {str(e)}')

        return redirect('producao:materiaprima_list')

    return render(request, 'producao/produtos/materiaprima_delete.html', {'produto': produto})


@login_required
def materiaprima_toggle_status(request, pk):
    """Ativar/desativar matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')

    if produto.status == 'ATIVO':
        produto.status = 'INATIVO'
        status_text = "desativada"
    else:
        produto.status = 'ATIVO'
        status_text = "ativada"

    produto.atualizado_por = request.user
    produto.save()
    messages.success(request, f'Matéria-prima "{produto.nome}" {status_text} com sucesso.')

    return redirect('producao:materiaprima_list')


@login_required
def materiaprima_toggle_utilizado(request, pk):
    """Toggle do campo utilizado para matéria-prima"""
    produto = get_object_or_404(Produto, pk=pk, tipo='MP')

    if produto.utilizado:
        produto.utilizado = False
        utilizado_text = "marcada como não utilizada"
    else:
        produto.utilizado = True
        utilizado_text = "marcada como utilizada"

    produto.atualizado_por = request.user
    produto.save()
    messages.success(request, f'Matéria-prima "{produto.nome}" {utilizado_text} com sucesso.')

    return redirect('producao:materiaprima_list')