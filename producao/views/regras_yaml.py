# producao/views/regras_yaml.py - Views SIMPLES para Regras YAML

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models.regras_yaml import RegraYAML
from core.forms.regras_yaml import RegraYAMLForm, RegraYAMLFiltroForm

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD REGRAS YAML
# =============================================================================

@login_required
def regras_yaml_list(request):
    """Lista regras YAML com filtros"""
    regras_list = RegraYAML.objects.select_related(
        'criado_por', 'atualizado_por'
    ).order_by('tipo', 'nome')

    # Aplicar filtros
    form_filtro = RegraYAMLFiltroForm(request.GET)
    
    if form_filtro.is_valid():
        if form_filtro.cleaned_data['tipo']:
            regras_list = regras_list.filter(tipo=form_filtro.cleaned_data['tipo'])
        
        if form_filtro.cleaned_data['status']:
            status = form_filtro.cleaned_data['status']
            if status == 'ativo':
                regras_list = regras_list.filter(ativa=True)
            elif status == 'inativo':
                regras_list = regras_list.filter(ativa=False)
            elif status == 'validado':
                regras_list = regras_list.filter(validado=True)
            elif status == 'erro':
                regras_list = regras_list.filter(validado=False)
        
        if form_filtro.cleaned_data['q']:
            query = form_filtro.cleaned_data['q']
            regras_list = regras_list.filter(
                Q(nome__icontains=query) |
                Q(descricao__icontains=query)
            )

    # Paginação
    paginator = Paginator(regras_list, 10)
    page = request.GET.get('page', 1)

    try:
        regras = paginator.page(page)
    except PageNotAnInteger:
        regras = paginator.page(1)
    except EmptyPage:
        regras = paginator.page(paginator.num_pages)

    return render(request, 'producao/regras_yaml/regras_yaml_list.html', {
        'regras': regras,
        'form_filtro': form_filtro
    })


@login_required
def regra_yaml_create(request):
    """Criar nova regra YAML"""
    if request.method == 'POST':
        form = RegraYAMLForm(request.POST)
        
        if form.is_valid():
            regra = form.save(commit=False)
            regra.criado_por = request.user
            regra.atualizado_por = request.user
            regra.save()
            
            # Validar códigos de produtos
            regra.validar_codigos_produtos()
            regra.save(update_fields=['validado', 'ultimo_erro'])

            messages.success(request, f'Regra "{regra.nome}" criada com sucesso.')
            return redirect('producao:regras_yaml_list')
        else:
            messages.error(request, 'Erro ao criar regra. Verifique os dados informados.')
    else:
        form = RegraYAMLForm()

    return render(request, 'producao/regras_yaml/regra_yaml_form.html', {
        'form': form,
        'titulo': 'Nova Regra'
    })


@login_required
def regra_yaml_update(request, pk):
    """Editar regra YAML"""
    regra = get_object_or_404(RegraYAML, pk=pk)

    if request.method == 'POST':
        form = RegraYAMLForm(request.POST, instance=regra)
        
        if form.is_valid():
            regra = form.save(commit=False)
            regra.atualizado_por = request.user
            regra.save()
            
            # Validar códigos de produtos
            regra.validar_codigos_produtos()
            regra.save(update_fields=['validado', 'ultimo_erro'])

            messages.success(request, f'Regra "{regra.nome}" atualizada com sucesso.')
            return redirect('producao:regras_yaml_list')
        else:
            messages.error(request, 'Erro ao atualizar regra. Verifique os dados informados.')
    else:
        form = RegraYAMLForm(instance=regra)

    return render(request, 'producao/regras_yaml/regra_yaml_form.html', {
        'form': form,
        'regra': regra,
        'titulo': f'Editar Regra: {regra.nome}'
    })


@login_required
def regra_yaml_detail(request, pk):
    """Visualizar detalhes de uma regra YAML"""
    regra = get_object_or_404(RegraYAML, pk=pk)
    
    # Tentar parsear o YAML para exibir
    dados_yaml = None
    try:
        dados_yaml = regra.get_dados_yaml()
    except Exception as e:
        messages.error(request, f'Erro ao parsear YAML: {str(e)}')
    
    return render(request, 'producao/regras_yaml/regra_yaml_detail.html', {
        'regra': regra,
        'dados_yaml': dados_yaml
    })


@login_required
def regra_yaml_delete(request, pk):
    """Excluir regra YAML"""
    regra = get_object_or_404(RegraYAML, pk=pk)

    if request.method == 'POST':
        try:
            nome = regra.nome
            regra.delete()
            messages.success(request, f'Regra "{nome}" excluída com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir regra: {str(e)}')

        return redirect('producao:regras_yaml_list')

    return render(request, 'producao/regras_yaml/regra_yaml_delete.html', {
        'regra': regra
    })


@login_required
def regra_yaml_toggle_status(request, pk):
    """Ativar/desativar regra YAML"""
    regra = get_object_or_404(RegraYAML, pk=pk)

    if regra.ativa:
        regra.ativa = False
        status_text = "desativada"
    else:
        regra.ativa = True
        status_text = "ativada"

    regra.atualizado_por = request.user
    regra.save()
    
    messages.success(request, f'Regra "{regra.nome}" {status_text} com sucesso.')
    return redirect('producao:regras_yaml_list')


@login_required
def regra_yaml_validar(request, pk):
    """Validar códigos de produtos da regra"""
    regra = get_object_or_404(RegraYAML, pk=pk)
    
    try:
        if regra.validar_codigos_produtos():
            regra.save(update_fields=['validado', 'ultimo_erro'])
            messages.success(request, f'Regra "{regra.nome}" validada com sucesso!')
        else:
            regra.save(update_fields=['validado', 'ultimo_erro'])
            messages.warning(request, f'Regra "{regra.nome}" contém erros: {regra.ultimo_erro}')
    except Exception as e:
        messages.error(request, f'Erro na validação: {str(e)}')
    
    return redirect('producao:regras_yaml_list')