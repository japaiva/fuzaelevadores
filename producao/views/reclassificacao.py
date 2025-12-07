# producao/views/reclassificacao.py - VERSÃO SUPER SIMPLES

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_producao
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.models import Produto, GrupoProduto, SubgrupoProduto

logger = logging.getLogger(__name__)

@portal_producao
def reclassificar_produto_form(request):
    """Formulário simples de reclassificação"""
    return render(request, 'producao/produtos/reclassificar_produto.html')

@portal_producao
def reclassificar_produto_executar(request):
    """Executar reclassificação"""
    if request.method != 'POST':
        return redirect('producao:reclassificar_produto_form')
    
    codigo = request.POST.get('codigo_original', '').strip()
    novo_tipo = request.POST.get('novo_tipo', '').strip()
    novo_grupo_id = request.POST.get('novo_grupo_id')
    novo_subgrupo_id = request.POST.get('novo_subgrupo_id')
    
    if not all([codigo, novo_tipo, novo_grupo_id, novo_subgrupo_id]):
        messages.error(request, 'Todos os campos são obrigatórios.')
        return redirect('producao:reclassificar_produto_form')
    
    try:
        produto = Produto.objects.get(codigo=codigo)
        grupo = GrupoProduto.objects.get(id=novo_grupo_id, tipo_produto=novo_tipo)
        subgrupo = SubgrupoProduto.objects.get(id=novo_subgrupo_id, grupo=grupo)
        
        with transaction.atomic():
            # Gerar novo código
            subgrupo_locked = SubgrupoProduto.objects.select_for_update().get(id=subgrupo.id)
            proximo_numero = subgrupo_locked.ultimo_numero + 1
            novo_codigo = f"{grupo.codigo}.{subgrupo_locked.codigo}.{proximo_numero:05d}"
            
            # Verificar se código já existe
            while Produto.objects.filter(codigo=novo_codigo).exists():
                proximo_numero += 1
                novo_codigo = f"{grupo.codigo}.{subgrupo_locked.codigo}.{proximo_numero:05d}"
            
            # Atualizar produto
            codigo_antigo = produto.codigo
            produto.codigo = novo_codigo
            produto.tipo = novo_tipo
            produto.grupo = grupo
            produto.subgrupo = subgrupo
            produto.atualizado_por = request.user
            
            if novo_tipo == 'MP':
                produto.tipo_pi = None
            
            produto.save()
            
            # Atualizar contador
            subgrupo_locked.ultimo_numero = proximo_numero
            subgrupo_locked.save()
            
            messages.success(request, f'Produto reclassificado: {codigo_antigo} → {novo_codigo}')
            
            return redirect('producao:materiaprima_list' if novo_tipo == 'MP' else 'producao:produto_intermediario_list')
            
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('producao:reclassificar_produto_form')

@portal_producao
def api_buscar_produto_para_reclassificar(request):
    """API para buscar produto"""
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({'success': False, 'error': 'Código não informado'})
    
    try:
        produto = Produto.objects.select_related('grupo', 'subgrupo').get(codigo=codigo)
        
        return JsonResponse({
            'success': True,
            'produto': {
                'codigo': produto.codigo,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'tipo_display': produto.get_tipo_display(),
                'grupo': {
                    'id': produto.grupo.id if produto.grupo else None,
                    'codigo': produto.grupo.codigo if produto.grupo else '',
                    'nome': produto.grupo.nome if produto.grupo else ''
                }
            }
        })
        
    except Produto.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Produto "{codigo}" não encontrado'})

@portal_producao
def api_grupos_por_tipo(request):
    """API para carregar grupos"""
    grupos_mp = list(GrupoProduto.objects.filter(
        tipo_produto='MP', ativo=True
    ).values('id', 'codigo', 'nome'))
    
    grupos_pi = list(GrupoProduto.objects.filter(
        tipo_produto='PI', ativo=True
    ).values('id', 'codigo', 'nome'))
    
    return JsonResponse({
        'success': True,
        'grupos_mp': grupos_mp,
        'grupos_pi': grupos_pi
    })

@portal_producao
def api_subgrupos_por_grupo_reclassificacao(request):
    """API para carregar subgrupos"""
    grupo_id = request.GET.get('grupo_id')
    
    if not grupo_id:
        return JsonResponse({'success': False, 'error': 'Grupo não informado'})
    
    subgrupos = list(SubgrupoProduto.objects.filter(
        grupo_id=grupo_id, ativo=True
    ).values('id', 'codigo', 'nome'))
    
    return JsonResponse({
        'success': True,
        'subgrupos': subgrupos
    })

@portal_producao
def api_preview_novo_codigo(request):
    """API para preview do código"""
    grupo_id = request.GET.get('grupo_id')
    subgrupo_id = request.GET.get('subgrupo_id')
    
    if not all([grupo_id, subgrupo_id]):
        return JsonResponse({'success': False, 'error': 'IDs inválidos'})
    
    try:
        grupo = GrupoProduto.objects.get(id=grupo_id)
        subgrupo = SubgrupoProduto.objects.get(id=subgrupo_id, grupo=grupo)
        
        proximo_numero = subgrupo.ultimo_numero + 1
        codigo_preview = f"{grupo.codigo}.{subgrupo.codigo}.{proximo_numero:05d}"
        
        return JsonResponse({
            'success': True,
            'preview': {
                'codigo_completo': codigo_preview
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})