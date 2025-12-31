# producao/views/regras_yaml.py - Views SIMPLES para Regras YAML

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models.regras_yaml import RegraYAML
from core.forms.regras_yaml import RegraYAMLForm, RegraYAMLFiltroForm

logger = logging.getLogger(__name__)

# =============================================================================
# CRUD REGRAS YAML
# =============================================================================

@portal_producao
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


@portal_producao
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


@portal_producao
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


@portal_producao
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


@portal_producao
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


@portal_producao
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


@portal_producao
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


# =============================================================================
# FÓRMULAS DE CÁLCULO - DOCUMENTAÇÃO
# =============================================================================

@portal_producao
def formulas_calculo(request):
    """
    Exibe a documentação das fórmulas de cálculo de dimensionamento.
    Inclui os parâmetros atuais configurados no sistema.
    """
    from core.models import ParametrosGerais

    # Obter parâmetros atuais
    params_obj = ParametrosGerais.objects.first()

    params = {
        'percentual_mao_obra': params_obj.percentual_mao_obra if params_obj else 15.00,
        'percentual_indiretos_fabricacao': params_obj.percentual_indiretos_fabricacao if params_obj else 5.00,
        'percentual_instalacao': params_obj.percentual_instalacao if params_obj else 5.00,
        'margem_padrao': params_obj.margem_padrao if params_obj else 30.00,
        'comissao_padrao': params_obj.comissao_padrao if params_obj else 3.00,
    }

    # Obter regras YAML e validar códigos
    import yaml
    regras_yaml = RegraYAML.objects.all().order_by('tipo')
    regras_com_erro = []

    def extrair_contexto_codigo(dados, caminho_partes):
        """Navega pelo YAML e extrai o contexto (nome/descricao) do código"""
        try:
            obj = dados
            for parte in caminho_partes:
                if '[' in parte:
                    key = parte.split('[')[0]
                    idx = int(parte.split('[')[1].replace(']', ''))
                    obj = obj[key][idx]
                else:
                    obj = obj[parte]
            return obj.get('nome', '') or obj.get('descricao', '') or ''
        except:
            return ''

    for regra in regras_yaml:
        # Revalidar para pegar erros atualizados
        regra.validar_codigos_produtos()
        if not regra.validado and regra.ultimo_erro:
            # Extrair códigos com contexto
            try:
                dados_yaml = yaml.safe_load(regra.conteudo_yaml)
            except:
                dados_yaml = {}

            codigos_detalhados = []
            for linha in regra.ultimo_erro.split('\n'):
                if 'codigo_produto' in linha and ': ' in linha:
                    caminho, codigo = linha.rsplit(': ', 1)
                    # Extrair contexto do caminho (ir até o pai do codigo_produto)
                    partes = caminho.replace('].', '].').split('.')
                    partes_pai = partes[:-1]  # Remove 'codigo_produto'
                    contexto = extrair_contexto_codigo(dados_yaml, partes_pai)
                    codigos_detalhados.append({
                        'codigo': codigo.strip(),
                        'contexto': contexto
                    })

            regras_com_erro.append({
                'tipo': regra.get_tipo_display(),
                'nome': regra.nome,
                'ativa': regra.ativa,
                'codigos': codigos_detalhados
            })

    return render(request, 'producao/formulas_calculo.html', {
        'params': params,
        'regras_yaml': regras_yaml,
        'regras_com_erro': regras_com_erro,
    })