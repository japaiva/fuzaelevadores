# producao/views/apis.py

"""
APIs AJAX e Endpoints
Portal de Produção - Sistema Elevadores FUZA
"""

import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from core.models import (
    GrupoProduto, SubgrupoProduto, Produto, Fornecedor, FornecedorProduto
)

logger = logging.getLogger(__name__)

# =============================================================================
# APIs AJAX
# =============================================================================

@login_required
@require_GET
def get_subgrupos_by_grupo(request):
    """
    API endpoint para retornar subgrupos de um grupo específico
    Used by AJAX in forms when grupo is selected
    """
    grupo_id = request.GET.get('grupo_id')

    if not grupo_id:
        return JsonResponse({'error': 'grupo_id é obrigatório'}, status=400)

    try:
        grupo = GrupoProduto.objects.get(id=grupo_id, ativo=True)
        subgrupos = SubgrupoProduto.objects.filter(
            grupo=grupo,
            ativo=True
        ).order_by('codigo')

        subgrupos_data = [
            {
                'id': subgrupo.id,
                'codigo': subgrupo.codigo,
                'nome': subgrupo.nome,
                'codigo_completo': f"{grupo.codigo}.{subgrupo.codigo}",
                'ultimo_numero': subgrupo.ultimo_numero
            }
            for subgrupo in subgrupos
        ]

        return JsonResponse({
            'success': True,
            'grupo': {
                'id': grupo.id,
                'codigo': grupo.codigo,
                'nome': grupo.nome,
                'tipo_produto': grupo.tipo_produto,
                'tipo_produto_display': grupo.get_tipo_produto_display()
            },
            'subgrupos': subgrupos_data
        })

    except GrupoProduto.DoesNotExist:
        return JsonResponse({'error': 'Grupo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_info_produto_codigo(request):
    """
    API endpoint para preview do código que será gerado para um produto
    """
    grupo_id = request.GET.get('grupo_id')
    subgrupo_id = request.GET.get('subgrupo_id')

    if not grupo_id or not subgrupo_id:
        return JsonResponse({'error': 'grupo_id e subgrupo_id são obrigatórios'}, status=400)

    try:
        grupo = GrupoProduto.objects.get(id=grupo_id, ativo=True)
        subgrupo = SubgrupoProduto.objects.get(id=subgrupo_id, grupo=grupo, ativo=True)

        # Preview do próximo código que seria gerado
        proximo_numero = subgrupo.ultimo_numero + 1
        codigo_preview = f"{grupo.codigo}.{subgrupo.codigo}.{proximo_numero:04d}"

        return JsonResponse({
            'success': True,
            'grupo': {
                'codigo': grupo.codigo,
                'nome': grupo.nome,
                'tipo_produto': grupo.tipo_produto,
                'tipo_produto_display': grupo.get_tipo_produto_display()
            },
            'subgrupo': {
                'codigo': subgrupo.codigo,
                'nome': subgrupo.nome,
                'ultimo_numero': subgrupo.ultimo_numero
            },
            'codigo_preview': codigo_preview,
            'proximo_numero': proximo_numero
        })

    except (GrupoProduto.DoesNotExist, SubgrupoProduto.DoesNotExist):
        return JsonResponse({'error': 'Grupo ou subgrupo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_produto_info(request):
    """API para buscar informações do produto"""
    produto_id = request.GET.get('produto_id')
    fornecedor_id = request.GET.get('fornecedor_id')

    if not produto_id:
        return JsonResponse({'error': 'produto_id é obrigatório'}, status=400)

    try:
        produto = Produto.objects.get(id=produto_id)

        # Dados básicos do produto
        data = {
            'codigo': produto.codigo,
            'nome': produto.nome,
            'unidade': produto.unidade_medida,
            'estoque_atual': float(produto.estoque_atual) if produto.estoque_atual else 0,
            'estoque_minimo': float(produto.estoque_minimo) if produto.estoque_minimo else 0,
            'custo_medio': float(produto.custo_medio) if produto.custo_medio else None,
        }

        # Buscar preço do fornecedor se especificado
        if fornecedor_id:
            fornecedor_produto = FornecedorProduto.objects.filter(
                produto=produto,
                fornecedor_id=fornecedor_id,
                ativo=True
            ).first()

            if fornecedor_produto:
                data['preco_fornecedor'] = float(fornecedor_produto.preco_unitario) if fornecedor_produto.preco_unitario else None
                data['prazo_entrega'] = fornecedor_produto.prazo_entrega
                data['quantidade_minima'] = float(fornecedor_produto.quantidade_minima) if fornecedor_produto.quantidade_minima else 1

        return JsonResponse({'success': True, 'produto': data})

    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_fornecedor_produtos(request, fornecedor_id):
    """API para buscar produtos de um fornecedor"""
    try:
        fornecedor = Fornecedor.objects.get(id=fornecedor_id, ativo=True)

        produtos = Produto.objects.filter(
            fornecedores_produto__fornecedor=fornecedor,
            fornecedores_produto__ativo=True,
            status='ATIVO',
            disponivel=True
        ).select_related('grupo', 'subgrupo').order_by('codigo')

        produtos_data = []
        for produto in produtos:
            fornecedor_produto = produto.fornecedores_produto.filter(
                fornecedor=fornecedor,
                ativo=True
            ).first()

            produtos_data.append({
                'id': produto.id,
                'codigo': produto.codigo,
                'nome': produto.nome,
                'unidade': produto.unidade_medida,
                'preco': float(fornecedor_produto.preco_unitario) if fornecedor_produto and fornecedor_produto.preco_unitario else None,
                'estoque_atual': float(produto.estoque_atual) if produto.estoque_atual else 0,
                'estoque_minimo': float(produto.estoque_minimo) if produto.estoque_minimo else 0,
            })

        return JsonResponse({
            'success': True,
            'fornecedor': {
                'id': fornecedor.id,
                'nome': fornecedor.nome_fantasia or fornecedor.razao_social
            },
            'produtos': produtos_data
        })

    except Fornecedor.DoesNotExist:
        return JsonResponse({'error': 'Fornecedor não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)