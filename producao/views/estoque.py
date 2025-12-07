# producao/views/estoque.py

"""
Views de Estoque - Portal Producao
Locais de Estoque, Tipos de Movimento, Movimentacoes e Posicao
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.forms import inlineformset_factory
from django.utils import timezone

from core.decorators import portal_producao
from core.models import (
    LocalEstoque, TipoMovimentoEntrada, TipoMovimentoSaida,
    MovimentoEntrada, ItemMovimentoEntrada,
    MovimentoSaida, ItemMovimentoSaida,
    Estoque, MovimentoEstoque
)
from core.forms import (
    LocalEstoqueForm, LocalEstoqueFiltroForm,
    TipoMovimentoEntradaForm, TipoMovimentoEntradaFiltroForm,
    TipoMovimentoSaidaForm, TipoMovimentoSaidaFiltroForm,
    MovimentoEntradaForm, ItemMovimentoEntradaForm, MovimentoEntradaFiltroForm,
    MovimentoSaidaForm, ItemMovimentoSaidaForm, MovimentoSaidaFiltroForm,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CRUD LOCAL DE ESTOQUE
# =============================================================================

@portal_producao
def local_estoque_list(request):
    """Lista locais de estoque"""
    locais_list = LocalEstoque.objects.all().select_related('fornecedor').order_by('tipo', 'nome')

    # Filtros
    tipo = request.GET.get('tipo')
    if tipo:
        locais_list = locais_list.filter(tipo=tipo)

    status = request.GET.get('ativo')
    if status == '1':
        locais_list = locais_list.filter(ativo=True)
    elif status == '0':
        locais_list = locais_list.filter(ativo=False)

    query = request.GET.get('q')
    if query:
        locais_list = locais_list.filter(
            Q(nome__icontains=query) |
            Q(fornecedor__razao_social__icontains=query) |
            Q(fornecedor__nome_fantasia__icontains=query)
        )

    # Paginacao
    paginator = Paginator(locais_list, 15)
    page = request.GET.get('page', 1)

    try:
        locais = paginator.page(page)
    except PageNotAnInteger:
        locais = paginator.page(1)
    except EmptyPage:
        locais = paginator.page(paginator.num_pages)

    context = {
        'locais': locais,
        'filtro_form': LocalEstoqueFiltroForm(request.GET),
    }
    return render(request, 'producao/estoque/local_estoque_list.html', context)


@portal_producao
def local_estoque_create(request):
    """Criar novo local de estoque"""
    if request.method == 'POST':
        form = LocalEstoqueForm(request.POST)
        if form.is_valid():
            local = form.save(commit=False)
            local.criado_por = request.user
            local.save()
            messages.success(request, f'Local "{local.nome}" criado com sucesso.')
            return redirect('producao:local_estoque_list')
    else:
        form = LocalEstoqueForm()

    return render(request, 'producao/estoque/local_estoque_form.html', {'form': form})


@portal_producao
def local_estoque_update(request, pk):
    """Editar local de estoque"""
    local = get_object_or_404(LocalEstoque, pk=pk)

    if request.method == 'POST':
        form = LocalEstoqueForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            messages.success(request, f'Local "{local.nome}" atualizado com sucesso.')
            return redirect('producao:local_estoque_list')
    else:
        form = LocalEstoqueForm(instance=local)

    return render(request, 'producao/estoque/local_estoque_form.html', {'form': form, 'local': local})


@portal_producao
def local_estoque_delete(request, pk):
    """Excluir local de estoque"""
    local = get_object_or_404(LocalEstoque, pk=pk)

    if request.method == 'POST':
        try:
            nome = local.nome
            local.delete()
            messages.success(request, f'Local "{nome}" excluido com sucesso.')
            return redirect('producao:local_estoque_list')
        except ProtectedError:
            messages.error(request, 'Este local esta vinculado a movimentacoes e nao pode ser excluido.')
            return redirect('producao:local_estoque_list')

    return render(request, 'producao/estoque/local_estoque_delete.html', {'local': local})


@portal_producao
def local_estoque_toggle_status(request, pk):
    """Ativar/Desativar local de estoque"""
    local = get_object_or_404(LocalEstoque, pk=pk)
    local.ativo = not local.ativo
    local.save()

    status_text = "ativado" if local.ativo else "desativado"
    messages.success(request, f'Local "{local.nome}" {status_text} com sucesso.')

    return redirect('producao:local_estoque_list')


# =============================================================================
# CRUD TIPO MOVIMENTO ENTRADA
# =============================================================================

@portal_producao
def tipo_movimento_entrada_list(request):
    """Lista tipos de movimento de entrada"""
    tipos_list = TipoMovimentoEntrada.objects.all().order_by('codigo')

    # Filtros
    tipo_parceiro = request.GET.get('tipo_parceiro')
    if tipo_parceiro:
        tipos_list = tipos_list.filter(tipo_parceiro=tipo_parceiro)

    status = request.GET.get('ativo')
    if status == '1':
        tipos_list = tipos_list.filter(ativo=True)
    elif status == '0':
        tipos_list = tipos_list.filter(ativo=False)

    query = request.GET.get('q')
    if query:
        tipos_list = tipos_list.filter(
            Q(codigo__icontains=query) |
            Q(descricao__icontains=query)
        )

    # Paginacao
    paginator = Paginator(tipos_list, 15)
    page = request.GET.get('page', 1)

    try:
        tipos = paginator.page(page)
    except PageNotAnInteger:
        tipos = paginator.page(1)
    except EmptyPage:
        tipos = paginator.page(paginator.num_pages)

    context = {
        'tipos': tipos,
        'filtro_form': TipoMovimentoEntradaFiltroForm(request.GET),
    }
    return render(request, 'producao/estoque/tipo_movimento_entrada_list.html', context)


def _processar_tipos_produto(request):
    """Processa checkboxes de tipos de produto permitidos"""
    tipos_permitidos = []
    if request.POST.get('tipo_produto_mp'):
        tipos_permitidos.append('MP')
    if request.POST.get('tipo_produto_pi'):
        tipos_permitidos.append('PI')
    if request.POST.get('tipo_produto_pa'):
        tipos_permitidos.append('PA')
    return tipos_permitidos


@portal_producao
def tipo_movimento_entrada_create(request):
    """Criar novo tipo de movimento de entrada"""
    if request.method == 'POST':
        form = TipoMovimentoEntradaForm(request.POST)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.criado_por = request.user
            tipo.tipos_produto_permitidos = _processar_tipos_produto(request)
            tipo.save()
            messages.success(request, f'Tipo "{tipo.descricao}" criado com sucesso.')
            return redirect('producao:tipo_movimento_entrada_list')
    else:
        form = TipoMovimentoEntradaForm()

    return render(request, 'producao/estoque/tipo_movimento_entrada_form.html', {'form': form})


@portal_producao
def tipo_movimento_entrada_update(request, pk):
    """Editar tipo de movimento de entrada"""
    tipo = get_object_or_404(TipoMovimentoEntrada, pk=pk)

    if request.method == 'POST':
        form = TipoMovimentoEntradaForm(request.POST, instance=tipo)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.tipos_produto_permitidos = _processar_tipos_produto(request)
            tipo.save()
            messages.success(request, f'Tipo "{tipo.descricao}" atualizado com sucesso.')
            return redirect('producao:tipo_movimento_entrada_list')
    else:
        form = TipoMovimentoEntradaForm(instance=tipo)

    return render(request, 'producao/estoque/tipo_movimento_entrada_form.html', {'form': form, 'tipo': tipo})


@portal_producao
def tipo_movimento_entrada_delete(request, pk):
    """Excluir tipo de movimento de entrada"""
    tipo = get_object_or_404(TipoMovimentoEntrada, pk=pk)

    if request.method == 'POST':
        try:
            descricao = tipo.descricao
            tipo.delete()
            messages.success(request, f'Tipo "{descricao}" excluido com sucesso.')
            return redirect('producao:tipo_movimento_entrada_list')
        except ProtectedError:
            messages.error(request, 'Este tipo esta vinculado a movimentacoes e nao pode ser excluido.')
            return redirect('producao:tipo_movimento_entrada_list')

    return render(request, 'producao/estoque/tipo_movimento_entrada_delete.html', {'tipo': tipo})


@portal_producao
def tipo_movimento_entrada_toggle_status(request, pk):
    """Ativar/Desativar tipo de movimento de entrada"""
    tipo = get_object_or_404(TipoMovimentoEntrada, pk=pk)
    tipo.ativo = not tipo.ativo
    tipo.save()

    status_text = "ativado" if tipo.ativo else "desativado"
    messages.success(request, f'Tipo "{tipo.descricao}" {status_text} com sucesso.')

    return redirect('producao:tipo_movimento_entrada_list')


# =============================================================================
# CRUD TIPO MOVIMENTO SAIDA
# =============================================================================

@portal_producao
def tipo_movimento_saida_list(request):
    """Lista tipos de movimento de saida"""
    tipos_list = TipoMovimentoSaida.objects.all().order_by('codigo')

    # Filtros
    tipo_parceiro = request.GET.get('tipo_parceiro')
    if tipo_parceiro:
        tipos_list = tipos_list.filter(tipo_parceiro=tipo_parceiro)

    status = request.GET.get('ativo')
    if status == '1':
        tipos_list = tipos_list.filter(ativo=True)
    elif status == '0':
        tipos_list = tipos_list.filter(ativo=False)

    query = request.GET.get('q')
    if query:
        tipos_list = tipos_list.filter(
            Q(codigo__icontains=query) |
            Q(descricao__icontains=query)
        )

    # Paginacao
    paginator = Paginator(tipos_list, 15)
    page = request.GET.get('page', 1)

    try:
        tipos = paginator.page(page)
    except PageNotAnInteger:
        tipos = paginator.page(1)
    except EmptyPage:
        tipos = paginator.page(paginator.num_pages)

    context = {
        'tipos': tipos,
        'filtro_form': TipoMovimentoSaidaFiltroForm(request.GET),
    }
    return render(request, 'producao/estoque/tipo_movimento_saida_list.html', context)


@portal_producao
def tipo_movimento_saida_create(request):
    """Criar novo tipo de movimento de saida"""
    if request.method == 'POST':
        form = TipoMovimentoSaidaForm(request.POST)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.criado_por = request.user
            tipo.tipos_produto_permitidos = _processar_tipos_produto(request)
            tipo.save()
            messages.success(request, f'Tipo "{tipo.descricao}" criado com sucesso.')
            return redirect('producao:tipo_movimento_saida_list')
    else:
        form = TipoMovimentoSaidaForm()

    return render(request, 'producao/estoque/tipo_movimento_saida_form.html', {'form': form})


@portal_producao
def tipo_movimento_saida_update(request, pk):
    """Editar tipo de movimento de saida"""
    tipo = get_object_or_404(TipoMovimentoSaida, pk=pk)

    if request.method == 'POST':
        form = TipoMovimentoSaidaForm(request.POST, instance=tipo)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.tipos_produto_permitidos = _processar_tipos_produto(request)
            tipo.save()
            messages.success(request, f'Tipo "{tipo.descricao}" atualizado com sucesso.')
            return redirect('producao:tipo_movimento_saida_list')
    else:
        form = TipoMovimentoSaidaForm(instance=tipo)

    return render(request, 'producao/estoque/tipo_movimento_saida_form.html', {'form': form, 'tipo': tipo})


@portal_producao
def tipo_movimento_saida_delete(request, pk):
    """Excluir tipo de movimento de saida"""
    tipo = get_object_or_404(TipoMovimentoSaida, pk=pk)

    if request.method == 'POST':
        try:
            descricao = tipo.descricao
            tipo.delete()
            messages.success(request, f'Tipo "{descricao}" excluido com sucesso.')
            return redirect('producao:tipo_movimento_saida_list')
        except ProtectedError:
            messages.error(request, 'Este tipo esta vinculado a movimentacoes e nao pode ser excluido.')
            return redirect('producao:tipo_movimento_saida_list')

    return render(request, 'producao/estoque/tipo_movimento_saida_delete.html', {'tipo': tipo})


@portal_producao
def tipo_movimento_saida_toggle_status(request, pk):
    """Ativar/Desativar tipo de movimento de saida"""
    tipo = get_object_or_404(TipoMovimentoSaida, pk=pk)
    tipo.ativo = not tipo.ativo
    tipo.save()

    status_text = "ativado" if tipo.ativo else "desativado"
    messages.success(request, f'Tipo "{tipo.descricao}" {status_text} com sucesso.')

    return redirect('producao:tipo_movimento_saida_list')


# =============================================================================
# MOVIMENTO DE ENTRADA
# =============================================================================

# FormSet para itens de entrada
ItemEntradaFormSet = inlineformset_factory(
    MovimentoEntrada,
    ItemMovimentoEntrada,
    form=ItemMovimentoEntradaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


@portal_producao
def movimento_entrada_list(request):
    """Lista movimentos de entrada"""
    movimentos_list = MovimentoEntrada.objects.select_related(
        'tipo_movimento', 'fornecedor', 'cliente', 'criado_por'
    ).order_by('-data_movimento', '-numero')

    # Filtros
    status = request.GET.get('status')
    if status:
        movimentos_list = movimentos_list.filter(status=status)

    tipo_movimento = request.GET.get('tipo_movimento')
    if tipo_movimento:
        movimentos_list = movimentos_list.filter(tipo_movimento_id=tipo_movimento)

    fornecedor = request.GET.get('fornecedor')
    if fornecedor:
        movimentos_list = movimentos_list.filter(fornecedor_id=fornecedor)

    data_de = request.GET.get('data_de')
    if data_de:
        movimentos_list = movimentos_list.filter(data_movimento__gte=data_de)

    data_ate = request.GET.get('data_ate')
    if data_ate:
        movimentos_list = movimentos_list.filter(data_movimento__lte=data_ate)

    query = request.GET.get('q')
    if query:
        movimentos_list = movimentos_list.filter(
            Q(numero__icontains=query) |
            Q(numero_nf__icontains=query) |
            Q(fornecedor__razao_social__icontains=query)
        )

    # Paginacao
    paginator = Paginator(movimentos_list, 15)
    page = request.GET.get('page', 1)

    try:
        movimentos = paginator.page(page)
    except PageNotAnInteger:
        movimentos = paginator.page(1)
    except EmptyPage:
        movimentos = paginator.page(paginator.num_pages)

    context = {
        'movimentos': movimentos,
        'filtro_form': MovimentoEntradaFiltroForm(request.GET),
    }
    return render(request, 'producao/estoque/movimento_entrada_list.html', context)


@portal_producao
def movimento_entrada_create(request):
    """Criar novo movimento de entrada"""
    if request.method == 'POST':
        form = MovimentoEntradaForm(request.POST)
        formset = ItemEntradaFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.criado_por = request.user
            movimento.save()

            # Salvar itens
            formset.instance = movimento
            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Entrada "{movimento.numero}" criada com sucesso.')
            return redirect('producao:movimento_entrada_detail', pk=movimento.pk)
    else:
        form = MovimentoEntradaForm()
        formset = ItemEntradaFormSet(prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'tipos_movimento': TipoMovimentoEntrada.objects.filter(
            ativo=True, tipo_operacao='movto'
        ).values('id', 'tipo_parceiro', 'tipo_produto', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'producao/estoque/movimento_entrada_form.html', context)


@portal_producao
def movimento_entrada_detail(request, pk):
    """Visualizar movimento de entrada"""
    movimento = get_object_or_404(
        MovimentoEntrada.objects.select_related(
            'tipo_movimento', 'fornecedor', 'cliente',
            'pedido_compra', 'criado_por', 'confirmado_por'
        ).prefetch_related('itens__produto'),
        pk=pk
    )

    context = {
        'movimento': movimento,
        'itens': movimento.itens.all(),
    }
    return render(request, 'producao/estoque/movimento_entrada_detail.html', context)


@portal_producao
def movimento_entrada_update(request, pk):
    """Editar movimento de entrada"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    # So permite editar rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser editados.')
        return redirect('producao:movimento_entrada_detail', pk=pk)

    if request.method == 'POST':
        form = MovimentoEntradaForm(request.POST, instance=movimento)
        formset = ItemEntradaFormSet(request.POST, instance=movimento, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.atualizado_por = request.user
            movimento.save()

            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Entrada "{movimento.numero}" atualizada com sucesso.')
            return redirect('producao:movimento_entrada_detail', pk=movimento.pk)
    else:
        form = MovimentoEntradaForm(instance=movimento)
        formset = ItemEntradaFormSet(instance=movimento, prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'movimento': movimento,
        'tipos_movimento': TipoMovimentoEntrada.objects.filter(
            ativo=True, tipo_operacao='movto'
        ).values('id', 'tipo_parceiro', 'tipo_produto', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'producao/estoque/movimento_entrada_form.html', context)


@portal_producao
def movimento_entrada_delete(request, pk):
    """Excluir movimento de entrada"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    # So permite excluir rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser excluidos.')
        return redirect('producao:movimento_entrada_detail', pk=pk)

    if request.method == 'POST':
        numero = movimento.numero
        movimento.delete()
        messages.success(request, f'Entrada "{numero}" excluida com sucesso.')
        return redirect('producao:movimento_entrada_list')

    return render(request, 'producao/estoque/movimento_entrada_delete.html', {'movimento': movimento})


@portal_producao
def movimento_entrada_confirmar(request, pk):
    """Confirmar movimento de entrada - atualiza estoque"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Este movimento ja foi confirmado ou cancelado.')
        return redirect('producao:movimento_entrada_detail', pk=pk)

    if not movimento.itens.exists():
        messages.error(request, 'Adicione pelo menos um item antes de confirmar.')
        return redirect('producao:movimento_entrada_detail', pk=pk)

    # Buscar local de estoque padrao (primeiro proprio ativo)
    local_estoque = LocalEstoque.objects.filter(tipo='proprio', ativo=True).first()
    if not local_estoque:
        messages.error(request, 'Nenhum local de estoque proprio cadastrado.')
        return redirect('producao:movimento_entrada_detail', pk=pk)

    # Processar cada item
    for item in movimento.itens.all():
        # Buscar ou criar posicao de estoque
        estoque, created = Estoque.objects.get_or_create(
            produto=item.produto,
            local_estoque=local_estoque,
            defaults={'quantidade': 0, 'custo_medio': 0}
        )

        saldo_anterior = estoque.quantidade
        custo_medio_anterior = estoque.custo_medio

        # Calcular novo custo medio (media ponderada)
        if estoque.quantidade + item.quantidade > 0:
            valor_atual = estoque.quantidade * estoque.custo_medio
            valor_entrada = item.quantidade * item.valor_unitario
            novo_custo_medio = (valor_atual + valor_entrada) / (estoque.quantidade + item.quantidade)
        else:
            novo_custo_medio = item.valor_unitario

        # Atualizar estoque
        estoque.quantidade += item.quantidade
        estoque.custo_medio = novo_custo_medio
        estoque.ultima_entrada = movimento.data_movimento
        estoque.atualizar_valor_total()
        estoque.save()

        # Atualizar estoque_atual no produto
        item.produto.estoque_atual += item.quantidade
        item.produto.save(update_fields=['estoque_atual'])

        # Registrar historico
        MovimentoEstoque.objects.create(
            produto=item.produto,
            local_estoque=local_estoque,
            tipo='entrada',
            quantidade=item.quantidade,
            saldo_anterior=saldo_anterior,
            saldo_posterior=estoque.quantidade,
            custo_unitario=item.valor_unitario,
            custo_medio_anterior=custo_medio_anterior,
            custo_medio_posterior=novo_custo_medio,
            documento_tipo='entrada',
            documento_numero=movimento.numero,
            documento_id=movimento.id,
            data_movimento=movimento.data_movimento,
            criado_por=request.user,
            observacoes=f'Entrada confirmada: {movimento.tipo_movimento.descricao}'
        )

    # Atualizar status do movimento
    movimento.status = 'confirmado'
    movimento.confirmado_em = timezone.now()
    movimento.confirmado_por = request.user
    movimento.save()

    messages.success(request, f'Entrada "{movimento.numero}" confirmada. Estoque atualizado.')
    return redirect('producao:movimento_entrada_detail', pk=pk)


@portal_producao
def movimento_entrada_cancelar(request, pk):
    """Cancelar movimento de entrada"""
    movimento = get_object_or_404(MovimentoEntrada, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser cancelados.')
        return redirect('producao:movimento_entrada_detail', pk=pk)

    movimento.status = 'cancelado'
    movimento.save()

    messages.warning(request, f'Entrada "{movimento.numero}" foi cancelada.')
    return redirect('producao:movimento_entrada_list')


# =============================================================================
# MOVIMENTO DE SAIDA
# =============================================================================

# FormSet para itens de saida
ItemSaidaFormSet = inlineformset_factory(
    MovimentoSaida,
    ItemMovimentoSaida,
    form=ItemMovimentoSaidaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


@portal_producao
def movimento_saida_list(request):
    """Lista movimentos de saida"""
    movimentos_list = MovimentoSaida.objects.select_related(
        'tipo_movimento', 'fornecedor', 'cliente', 'criado_por'
    ).order_by('-data_movimento', '-numero')

    # Filtros
    status = request.GET.get('status')
    if status:
        movimentos_list = movimentos_list.filter(status=status)

    tipo_movimento = request.GET.get('tipo_movimento')
    if tipo_movimento:
        movimentos_list = movimentos_list.filter(tipo_movimento_id=tipo_movimento)

    cliente = request.GET.get('cliente')
    if cliente:
        movimentos_list = movimentos_list.filter(cliente_id=cliente)

    data_de = request.GET.get('data_de')
    if data_de:
        movimentos_list = movimentos_list.filter(data_movimento__gte=data_de)

    data_ate = request.GET.get('data_ate')
    if data_ate:
        movimentos_list = movimentos_list.filter(data_movimento__lte=data_ate)

    query = request.GET.get('q')
    if query:
        movimentos_list = movimentos_list.filter(
            Q(numero__icontains=query) |
            Q(numero_nf__icontains=query) |
            Q(cliente__razao_social__icontains=query)
        )

    # Paginacao
    paginator = Paginator(movimentos_list, 15)
    page = request.GET.get('page', 1)

    try:
        movimentos = paginator.page(page)
    except PageNotAnInteger:
        movimentos = paginator.page(1)
    except EmptyPage:
        movimentos = paginator.page(paginator.num_pages)

    context = {
        'movimentos': movimentos,
        'filtro_form': MovimentoSaidaFiltroForm(request.GET),
    }
    return render(request, 'producao/estoque/movimento_saida_list.html', context)


@portal_producao
def movimento_saida_create(request):
    """Criar novo movimento de saida"""
    if request.method == 'POST':
        form = MovimentoSaidaForm(request.POST)
        formset = ItemSaidaFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.criado_por = request.user
            movimento.save()

            # Salvar itens
            formset.instance = movimento
            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Saida "{movimento.numero}" criada com sucesso.')
            return redirect('producao:movimento_saida_detail', pk=movimento.pk)
    else:
        form = MovimentoSaidaForm()
        formset = ItemSaidaFormSet(prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'tipos_movimento': TipoMovimentoSaida.objects.filter(
            ativo=True, tipo_operacao='movto'
        ).values('id', 'tipo_parceiro', 'tipo_produto', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'producao/estoque/movimento_saida_form.html', context)


@portal_producao
def movimento_saida_detail(request, pk):
    """Visualizar movimento de saida"""
    movimento = get_object_or_404(
        MovimentoSaida.objects.select_related(
            'tipo_movimento', 'fornecedor', 'cliente',
            'criado_por', 'confirmado_por'
        ).prefetch_related('itens__produto'),
        pk=pk
    )

    context = {
        'movimento': movimento,
        'itens': movimento.itens.all(),
    }
    return render(request, 'producao/estoque/movimento_saida_detail.html', context)


@portal_producao
def movimento_saida_update(request, pk):
    """Editar movimento de saida"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    # So permite editar rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser editados.')
        return redirect('producao:movimento_saida_detail', pk=pk)

    if request.method == 'POST':
        form = MovimentoSaidaForm(request.POST, instance=movimento)
        formset = ItemSaidaFormSet(request.POST, instance=movimento, prefix='itens')

        if form.is_valid() and formset.is_valid():
            movimento = form.save(commit=False)
            movimento.atualizado_por = request.user
            movimento.save()

            formset.save()

            # Recalcular valor total
            movimento.calcular_valor_total()
            movimento.save()

            messages.success(request, f'Saida "{movimento.numero}" atualizada com sucesso.')
            return redirect('producao:movimento_saida_detail', pk=movimento.pk)
    else:
        form = MovimentoSaidaForm(instance=movimento)
        formset = ItemSaidaFormSet(instance=movimento, prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'movimento': movimento,
        'tipos_movimento': TipoMovimentoSaida.objects.filter(
            ativo=True, tipo_operacao='movto'
        ).values('id', 'tipo_parceiro', 'tipo_produto', 'movimenta_terceiros', 'exige_nota_fiscal'),
    }
    return render(request, 'producao/estoque/movimento_saida_form.html', context)


@portal_producao
def movimento_saida_delete(request, pk):
    """Excluir movimento de saida"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    # So permite excluir rascunhos
    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser excluidos.')
        return redirect('producao:movimento_saida_detail', pk=pk)

    if request.method == 'POST':
        numero = movimento.numero
        movimento.delete()
        messages.success(request, f'Saida "{numero}" excluida com sucesso.')
        return redirect('producao:movimento_saida_list')

    return render(request, 'producao/estoque/movimento_saida_delete.html', {'movimento': movimento})


@portal_producao
def movimento_saida_confirmar(request, pk):
    """Confirmar movimento de saida - atualiza estoque"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Este movimento ja foi confirmado ou cancelado.')
        return redirect('producao:movimento_saida_detail', pk=pk)

    if not movimento.itens.exists():
        messages.error(request, 'Adicione pelo menos um item antes de confirmar.')
        return redirect('producao:movimento_saida_detail', pk=pk)

    # Buscar local de estoque padrao (primeiro proprio ativo)
    local_estoque = LocalEstoque.objects.filter(tipo='proprio', ativo=True).first()
    if not local_estoque:
        messages.error(request, 'Nenhum local de estoque proprio cadastrado.')
        return redirect('producao:movimento_saida_detail', pk=pk)

    # Verificar se ha estoque suficiente
    erros_estoque = []
    for item in movimento.itens.all():
        try:
            estoque = Estoque.objects.get(
                produto=item.produto,
                local_estoque=local_estoque
            )
            if estoque.quantidade_disponivel < item.quantidade:
                erros_estoque.append(
                    f'{item.produto.codigo}: disponivel {estoque.quantidade_disponivel}, solicitado {item.quantidade}'
                )
        except Estoque.DoesNotExist:
            erros_estoque.append(f'{item.produto.codigo}: sem estoque no local')

    if erros_estoque:
        messages.error(request, 'Estoque insuficiente: ' + '; '.join(erros_estoque))
        return redirect('producao:movimento_saida_detail', pk=pk)

    # Processar cada item
    for item in movimento.itens.all():
        estoque = Estoque.objects.get(
            produto=item.produto,
            local_estoque=local_estoque
        )

        saldo_anterior = estoque.quantidade
        custo_medio_anterior = estoque.custo_medio

        # Atualizar estoque (saida nao altera custo medio)
        estoque.quantidade -= item.quantidade
        estoque.ultima_saida = movimento.data_movimento
        estoque.atualizar_valor_total()
        estoque.save()

        # Atualizar estoque_atual no produto
        item.produto.estoque_atual -= item.quantidade
        item.produto.save(update_fields=['estoque_atual'])

        # Usar custo medio como valor unitario se nao informado
        valor_unitario = item.valor_unitario if item.valor_unitario else estoque.custo_medio

        # Registrar historico
        MovimentoEstoque.objects.create(
            produto=item.produto,
            local_estoque=local_estoque,
            tipo='saida',
            quantidade=item.quantidade,
            saldo_anterior=saldo_anterior,
            saldo_posterior=estoque.quantidade,
            custo_unitario=valor_unitario,
            custo_medio_anterior=custo_medio_anterior,
            custo_medio_posterior=estoque.custo_medio,
            documento_tipo='saida',
            documento_numero=movimento.numero,
            documento_id=movimento.id,
            data_movimento=movimento.data_movimento,
            criado_por=request.user,
            observacoes=f'Saida confirmada: {movimento.tipo_movimento.descricao}'
        )

    # Atualizar status do movimento
    movimento.status = 'confirmado'
    movimento.confirmado_em = timezone.now()
    movimento.confirmado_por = request.user
    movimento.save()

    messages.success(request, f'Saida "{movimento.numero}" confirmada. Estoque atualizado.')
    return redirect('producao:movimento_saida_detail', pk=pk)


@portal_producao
def movimento_saida_cancelar(request, pk):
    """Cancelar movimento de saida"""
    movimento = get_object_or_404(MovimentoSaida, pk=pk)

    if movimento.status != 'rascunho':
        messages.error(request, 'Apenas movimentos em rascunho podem ser cancelados.')
        return redirect('producao:movimento_saida_detail', pk=pk)

    movimento.status = 'cancelado'
    movimento.save()

    messages.warning(request, f'Saida "{movimento.numero}" foi cancelada.')
    return redirect('producao:movimento_saida_list')


# =============================================================================
# POSICAO DE ESTOQUE (Consulta)
# =============================================================================

@portal_producao
def posicao_estoque(request):
    """Consulta posicao de estoque"""
    estoques_list = Estoque.objects.select_related(
        'produto', 'local_estoque'
    ).filter(quantidade__gt=0).order_by('produto__codigo', 'local_estoque__nome')

    # Filtros
    local = request.GET.get('local')
    if local:
        estoques_list = estoques_list.filter(local_estoque_id=local)

    tipo_local = request.GET.get('tipo_local')
    if tipo_local:
        estoques_list = estoques_list.filter(local_estoque__tipo=tipo_local)

    query = request.GET.get('q')
    if query:
        estoques_list = estoques_list.filter(
            Q(produto__codigo__icontains=query) |
            Q(produto__descricao__icontains=query)
        )

    # Totais
    total_valor = estoques_list.aggregate(total=Sum('valor_total'))['total'] or 0

    # Paginacao
    paginator = Paginator(estoques_list, 20)
    page = request.GET.get('page', 1)

    try:
        estoques = paginator.page(page)
    except PageNotAnInteger:
        estoques = paginator.page(1)
    except EmptyPage:
        estoques = paginator.page(paginator.num_pages)

    context = {
        'estoques': estoques,
        'total_valor': total_valor,
        'locais': LocalEstoque.objects.filter(ativo=True).order_by('tipo', 'nome'),
    }
    return render(request, 'producao/estoque/posicao_estoque.html', context)
