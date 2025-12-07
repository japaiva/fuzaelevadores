# vendedor/views/contratos.py

"""
Views para geração de contratos a partir de propostas aprovadas
"""

import os
from datetime import date
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import portal_vendedor
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
import logging

from core.models import Proposta

logger = logging.getLogger(__name__)


@portal_vendedor
def gerar_contrato_pdf(request, pk):
    """
    Gera contrato em PDF a partir da proposta aprovada
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    # Verificar se proposta foi aprovada

    if not proposta.numero_contrato:
        numero_contrato = gerar_numero_contrato()
        proposta.numero_contrato = numero_contrato
        proposta.data_contrato = date.today()
        proposta.save()
        
    # Preparar contexto para o template
    context = {
        'proposta': proposta,
        'cliente': proposta.cliente,
        'data_atual': date.today(),
        'local_instalacao': proposta.cliente.endereco_completo,  # ou campo específico
        # Dados da empresa (fixos)
        'empresa': {
            'nome': 'ELEVADORES FUZA LTDA EPP',
            'cnpj': '10.614.614/0001-17',
            'endereco': 'Rua Edmundo de Paula Coelho, 38 - Limoeiro',
            'cep': '08235-790',
            'cidade': 'São Paulo - SP',
            'telefone': '(11) 0000-0000',  # Ajustar conforme necessário
            'email': 'contato@elevadoresfuza.com.br'
        }
    }
        
    # Renderizar HTML
    html_content = render_to_string('contrato/contrato_template.html', context)
        
    # Caminho para CSS customizado (se existir)
    css_path = os.path.join(settings.BASE_DIR, 'static/css/contrato.css')
    stylesheets = []
    if os.path.exists(css_path):
        stylesheets.append(CSS(css_path))
        
    # Gerar PDF
    pdf = HTML(
        string=html_content, 
        base_url=request.build_absolute_uri()
    ).write_pdf(stylesheets=stylesheets)
        
    # Resposta HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'Contrato_{proposta.numero}_{proposta.cliente.nome[:20]}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
    # Log da operação
    logger.info(f"Contrato gerado com sucesso: {proposta.numero_contrato} - {proposta.cliente.nome}")
        
    return response
        

def gerar_numero_contrato():
    """
    Gera número sequencial para contrato no formato CONT-AAMM-001
    """
    from datetime import datetime
    
    ano_mes = datetime.now().strftime('%y%m')  # AAMM
    
    # Buscar último número do mês atual
    ultimo_contrato = Proposta.objects.filter(
        numero_contrato__startswith=f'CONT-{ano_mes}'
    ).order_by('-numero_contrato').first()
    
    if ultimo_contrato:
        try:
            # Extrair número sequencial: "CONT-2501-001" -> "001" -> 1
            numero_parte = ultimo_contrato.numero_contrato.split('-')[-1]
            ultimo_numero = int(numero_parte)
            novo_numero = ultimo_numero + 1
        except (ValueError, IndexError):
            novo_numero = 1
    else:
        novo_numero = 1
    
    return f'CONT-{ano_mes}-{novo_numero:03d}'


@login_required  
def preview_contrato_html(request, pk):
    """
    Preview do contrato em HTML (para debug/desenvolvimento)
    """
    proposta = get_object_or_404(Proposta, pk=pk)
    
    context = {
        'proposta': proposta,
        'cliente': proposta.cliente,
        'data_atual': date.today(),
        'local_instalacao': proposta.cliente.endereco_completo,
        'empresa': {
            'nome': 'ELEVADORES FUZA LTDA EPP',
            'cnpj': '10.614.614/0001-17',
            'endereco': 'Rua Edmundo de Paula Coelho, 38 - Limoeiro',
            'cep': '08235-790',
            'cidade': 'São Paulo - SP',
            'telefone': '(11) 0000-0000',
            'email': 'contato@elevadoresfuza.com.br'
        }
    }
    
    return render_to_string('contratos/contrato_template.html', context)