# core/utils/pdf_generator.py - VERSÃO CORRIGIDA COM CONTATOS DOS PARÂMETROS

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from core.models import ParametrosGerais
import requests
from PIL import Image as PILImage


def gerar_pdf_pedido_compra(pedido):
    """
    Gera PDF do pedido de compra - VERSÃO CORRIGIDA COM CONTATOS DOS PARÂMETROS
    """
    buffer = BytesIO()
    
    # Configurar documento com margens otimizadas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f'Pedido de Compra {pedido.numero}'
    )
    
    # Buscar parâmetros da empresa
    try:
        parametros = ParametrosGerais.objects.first()
    except:
        parametros = None
    
    # Estilos melhorados com tamanhos reduzidos
    styles = getSampleStyleSheet()
    
    # Cores da identidade visual
    COR_PRIMARIA = colors.HexColor('#1a365d')      # Azul escuro
    COR_SECUNDARIA = colors.HexColor('#2c5282')    # Azul médio
    COR_ACCENT = colors.HexColor('#3182ce')        # Azul claro
    COR_TEXTO = colors.HexColor('#2d3748')         # Cinza escuro
    COR_BACKGROUND = colors.HexColor('#f7fafc')    # Cinza muito claro
    
    # Estilo para título principal (reduzido)
    titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=8,
        alignment=TA_CENTER,
        textColor=COR_PRIMARIA,
        fontName='Helvetica-Bold'
    )
    
    # Estilo normal reduzido
    normal_style = ParagraphStyle(
        'NormalMelhorado',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=COR_TEXTO,
        alignment=TA_LEFT
    )
    
    # Estilo para empresa reduzido - SEM ESPAÇAMENTO APÓS
    empresa_style = ParagraphStyle(
        'EmpresaStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=COR_TEXTO,
        spaceAfter=0
    )
    
    # Lista de elementos do PDF
    elementos = []
    
    # =============================================================================
    # CABEÇALHO DA EMPRESA
    # =============================================================================
    
    if parametros:
        # Nome da empresa em destaque
        elementos.append(Paragraph(f"<b>{parametros.razao_social}</b>", titulo_principal))
        elementos.append(Spacer(1, 2))
        
        if parametros.nome_fantasia:
            elementos.append(Paragraph(parametros.nome_fantasia, empresa_style))
        
        # Informações da empresa em tabela organizada
        empresa_info = []
        
        # Endereço
        endereco_parts = []
        if parametros.endereco:
            endereco_parts.append(parametros.endereco)
            if parametros.numero:
                endereco_parts[-1] += f", {parametros.numero}"
        if parametros.bairro:
            endereco_parts.append(parametros.bairro)
        if parametros.cidade and parametros.estado:
            endereco_parts.append(f"{parametros.cidade} - {parametros.estado}")
        if parametros.cep:
            endereco_parts.append(f"CEP: {parametros.cep}")
        
        if endereco_parts:
            empresa_info.append([Paragraph(" • ".join(endereco_parts), empresa_style)])
        
        # Contatos da empresa
        contatos = []
        if parametros.telefone:
            contatos.append(f"Tel: {parametros.telefone}")
        if parametros.email:
            contatos.append(f"Email: {parametros.email}")
        if parametros.cnpj:
            contatos.append(f"CNPJ: {parametros.cnpj}")
        
        if contatos:
            empresa_info.append([Paragraph(" • ".join(contatos), empresa_style)])
        
        if empresa_info:
            empresa_table = Table(empresa_info, colWidths=[18*cm])
            empresa_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elementos.append(empresa_table)
    

    elementos.append(Spacer(1, 4))
    
    # =============================================================================
    # TÍTULO DO DOCUMENTO
    # =============================================================================
    
    elementos.append(Paragraph("PEDIDO DE COMPRA", titulo_principal))
    elementos.append(Spacer(1, 4))
    
    # =============================================================================
    # INFORMAÇÕES DO PEDIDO - INCLUINDO CONTATOS DOS PARÂMETROS
    # =============================================================================
    
    # Dados do pedido em layout de cards
    pedido_data = [
        [
            Paragraph("<b>Número:</b>", normal_style),
            Paragraph(f"<b>{pedido.numero}</b>", normal_style),
            Paragraph("<b>Data:</b>", normal_style),
            Paragraph(pedido.data_emissao.strftime('%d/%m/%Y'), normal_style)
        ],
        [
            Paragraph("<b>Status:</b>", normal_style),
            Paragraph(f"<b>{pedido.get_status_display()}</b>", normal_style),
            Paragraph("<b>Prioridade:</b>", normal_style),
            Paragraph(f"<b>{pedido.get_prioridade_display()}</b>", normal_style)
        ]
    ]
    
    if pedido.data_entrega_prevista:
        pedido_data.append([
            Paragraph("<b>Entrega Prevista:</b>", normal_style),
            Paragraph(pedido.data_entrega_prevista.strftime('%d/%m/%Y'), normal_style),
            Paragraph("<b>Prazo:</b>", normal_style),
            Paragraph(f"{pedido.prazo_entrega} dias" if pedido.prazo_entrega else "N/I", normal_style)
        ])
    
    # ADICIONAR LINHA COM CONTATOS DOS PARÂMETROS
    if parametros and (parametros.comprador_responsavel or parametros.contato_compras):
        pedido_data.append([
            Paragraph("<b>Comprador:</b>", normal_style),
            Paragraph(parametros.comprador_responsavel or "N/I", normal_style),
            Paragraph("<b>Contato Compras:</b>", normal_style),
            Paragraph(parametros.contato_compras or "N/I", normal_style)
        ])
    
    pedido_table = Table(pedido_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 6*cm])
    pedido_table.setStyle(TableStyle([
        # Backgrounds alternados
        ('BACKGROUND', (0, 0), (1, -1), COR_BACKGROUND),
        ('BACKGROUND', (2, 0), (3, -1), COR_BACKGROUND),
        
        # Bordas e espaçamento
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        
        # Bordas arredondadas (efeito visual)
        ('LINEBELOW', (0, 0), (-1, 0), 2, COR_ACCENT),
    ]))
    
    elementos.append(pedido_table)
    elementos.append(Spacer(1, 18))
    
    # =============================================================================
    # DADOS DO FORNECEDOR
    # =============================================================================
    
    fornecedor = pedido.fornecedor
    fornecedor_data = [
        [Paragraph("<b>Fornecedor:</b>", normal_style), Paragraph(fornecedor.razao_social, normal_style)],
    ]
    
    if fornecedor.nome_fantasia:
        fornecedor_data.append([
            Paragraph("<b>Nome Fantasia:</b>", normal_style), 
            Paragraph(fornecedor.nome_fantasia, normal_style)
        ])
    
    if fornecedor.cnpj:
        fornecedor_data.append([
            Paragraph("<b>CNPJ:</b>", normal_style), 
            Paragraph(fornecedor.cnpj, normal_style)
        ])
    
    if fornecedor.endereco:
        fornecedor_data.append([
            Paragraph("<b>Endereço:</b>", normal_style), 
            Paragraph(fornecedor.endereco, normal_style)
        ])
    
    # Contatos do fornecedor
    contatos_fornecedor = []
    if fornecedor.telefone:
        contatos_fornecedor.append(f"<b>Tel:</b> {fornecedor.telefone}")
    if fornecedor.email:
        contatos_fornecedor.append(f"<b>Email:</b> {fornecedor.email}")
    if fornecedor.contato_principal:
        contatos_fornecedor.append(f"<b>Contato:</b> {fornecedor.contato_principal}")
    
    if contatos_fornecedor:
        fornecedor_data.append([
            Paragraph("<b>Contatos:</b>", normal_style), 
            Paragraph(" | ".join(contatos_fornecedor), normal_style)
        ])
    
    fornecedor_table = Table(fornecedor_data, colWidths=[4*cm, 14*cm])
    fornecedor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), COR_BACKGROUND),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elementos.append(fornecedor_table)
    elementos.append(Spacer(1, 18))
    
    # =============================================================================
    # ITENS DO PEDIDO
    # =============================================================================
    
    # Estilo para descrição com quebra de linha (reduzido)
    descricao_style = ParagraphStyle(
        'DescricaoStyle',
        parent=normal_style,
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        wordWrap='LTR'
    )
    
    # Estilo para números alinhados à direita
    numero_style = ParagraphStyle(
        'NumeroStyle',
        parent=normal_style,
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        wordWrap='LTR'
    )

    # Cabeçalho da tabela com cores - TEXTO BRANCO GARANTIDO
    itens_data = [
        [
            Paragraph('<b><font color="white">Item</font></b>', normal_style),
            Paragraph('<b><font color="white">Código</font></b>', normal_style),
            Paragraph('<b><font color="white">Descrição</font></b>', normal_style),
            Paragraph('<b><font color="white">Qtd</font></b>', normal_style),
            Paragraph('<b><font color="white">Un</font></b>', normal_style),
            Paragraph('<b><font color="white">Vlr Unit.</font></b>', normal_style),
            Paragraph('<b><font color="white">Vlr Total</font></b>', normal_style)
        ]
    ]
    
    # Itens com formatação corrigida
    for i, item in enumerate(pedido.itens.all(), 1):
        # Formatação brasileira dos números
        quantidade_fmt = f"{item.quantidade:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        valor_unit_fmt = f"R$ {item.valor_unitario:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        valor_total_fmt = f"R$ {item.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        # Limitar descrição se muito longa e usar style com quebra
        descricao = item.produto.nome
        if len(descricao) > 45:
            descricao = descricao[:42] + "..."
        
        itens_data.append([
            Paragraph(str(i), normal_style),
            Paragraph(item.produto.codigo, normal_style),
            Paragraph(descricao, descricao_style),
            Paragraph(quantidade_fmt, numero_style),
            Paragraph(item.unidade, normal_style),
            Paragraph(valor_unit_fmt, numero_style),
            Paragraph(valor_total_fmt, numero_style)
        ])
    
    # Tabela com larguras corrigidas
    itens_table = Table(
        itens_data, 
        colWidths=[1*cm, 2.2*cm, 7.5*cm, 1.8*cm, 1.2*cm, 2.2*cm, 2.3*cm],
        repeatRows=1
    )
    
    # Calcular altura das linhas dinamicamente (reduzidas)
    row_heights = [None]  # Cabeçalho com altura automática
    for i in range(1, len(itens_data)):
        descricao_length = len(itens_data[i][2].text if hasattr(itens_data[i][2], 'text') else str(itens_data[i][2]))
        if descricao_length > 30:
            row_heights.append(1.0*cm)
        else:
            row_heights.append(0.7*cm)
    
    itens_table._argH = row_heights
    
    itens_table.setStyle(TableStyle([
        # Cabeçalho - CORRIGIDO para garantir visibilidade
        ('BACKGROUND', (0, 0), (-1, 0), COR_PRIMARIA),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Força a cor branca no cabeçalho (fix para problema de renderização)
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),  # Item
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),  # Código
        ('TEXTCOLOR', (2, 0), (2, 0), colors.white),  # Descrição
        ('TEXTCOLOR', (3, 0), (3, 0), colors.white),  # Qtd
        ('TEXTCOLOR', (4, 0), (4, 0), colors.white),  # Un
        ('TEXTCOLOR', (5, 0), (5, 0), colors.white),  # Vlr Unit
        ('TEXTCOLOR', (6, 0), (6, 0), colors.white),  # Vlr Total
        
        # Dados - alinhamentos corrigidos
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Item - centro
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Código - esquerda
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Descrição - esquerda
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Quantidade - DIREITA
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Unidade - centro
        ('ALIGN', (5, 1), (5, -1), 'RIGHT'),   # Valor Unit - DIREITA
        ('ALIGN', (6, 1), (6, -1), 'RIGHT'),   # Valor Total - DIREITA
        
        # Alinhamento vertical
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Bordas e cores
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        
        # Zebra stripes
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COR_BACKGROUND]),
        
        # Padding otimizado reduzido
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        
        # Padding especial para descrição
        ('LEFTPADDING', (2, 1), (2, -1), 4),
        ('RIGHTPADDING', (2, 1), (2, -1), 4),
        
        # Linha de separação no cabeçalho
        ('LINEBELOW', (0, 0), (-1, 0), 2, COR_ACCENT),
    ]))
    
    elementos.append(itens_table)
    elementos.append(Spacer(1, 15))
    
    # =============================================================================
    # TOTAIS
    # =============================================================================
    
    totais_data = []
    
    # Subtotal
    subtotal_fmt = f"R$ {pedido.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    totais_data.append([Paragraph("<b>Subtotal dos Itens:</b>", normal_style), Paragraph(subtotal_fmt, numero_style)])
    
    # Desconto
    if pedido.desconto_percentual > 0:
        desconto_fmt = f"- R$ {pedido.desconto_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        totais_data.append([
            Paragraph(f"<b>Desconto ({pedido.desconto_percentual}%):</b>", normal_style),
            Paragraph(desconto_fmt, numero_style)
        ])
    
    # Frete
    if pedido.valor_frete > 0:
        frete_fmt = f"R$ {pedido.valor_frete:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        totais_data.append([
            Paragraph("<b>Frete:</b>", normal_style),
            Paragraph(frete_fmt, numero_style)
        ])
    
    # Total final destacado
    total_fmt = f"R$ {pedido.valor_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Estilo especial para total com alinhamento à direita
    total_numero_style = ParagraphStyle(
        'TotalNumeroStyle',
        parent=numero_style,
        fontSize=12,
        textColor=colors.white,
        alignment=TA_RIGHT
    )
    
    totais_data.append([
        Paragraph("<b>TOTAL GERAL:</b>", ParagraphStyle('TotalLabel', parent=normal_style, fontSize=11, textColor=colors.white)),
        Paragraph(f"<b>{total_fmt}</b>", total_numero_style)
    ])
    
    totais_table = Table(totais_data, colWidths=[13*cm, 5*cm])
    totais_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -2), 9),
        ('FONTSIZE', (-2, -1), (-1, -1), 11),
        
        # Linha do total com destaque
        ('BACKGROUND', (-2, -1), (-1, -1), COR_PRIMARIA),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elementos.append(totais_table)
    elementos.append(Spacer(1, 18))
    
    # =============================================================================
    # CONDIÇÕES E OBSERVAÇÕES
    # =============================================================================
    
    if pedido.condicao_pagamento or pedido.observacoes:
        condicoes_data = []
        
        if pedido.condicao_pagamento:
            condicoes_data.append([
                Paragraph("<b>Condição de Pagamento:</b>", normal_style), 
                Paragraph(pedido.condicao_pagamento, normal_style)
            ])
        
        if pedido.prazo_entrega:
            condicoes_data.append([
                Paragraph("<b>Prazo de Entrega:</b>", normal_style), 
                Paragraph(f"{pedido.prazo_entrega} dias úteis", normal_style)
            ])
        
        if condicoes_data:
            condicoes_table = Table(condicoes_data, colWidths=[4.5*cm, 13.5*cm])
            condicoes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), COR_BACKGROUND),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elementos.append(condicoes_table)
            elementos.append(Spacer(1, 12))
        
        if pedido.observacoes:
            elementos.append(Paragraph("<b>Observações:</b>", normal_style))
            elementos.append(Spacer(1, 6))
            elementos.append(Paragraph(pedido.observacoes, normal_style))
            elementos.append(Spacer(1, 18))
    
    
    # =============================================================================
    # RODAPÉ COM DADOS DO COMPRADOR
    # =============================================================================
    
    elementos.append(Spacer(1, 20))
    
    # INFORMAÇÕES DO COMPRADOR DOS PARÂMETROS
    if parametros and (parametros.comprador_responsavel or parametros.contato_compras):
        rodape_comprador = []
        
        if parametros.comprador_responsavel:
            rodape_comprador.append(f"Comprador: {parametros.comprador_responsavel}")
        
        if parametros.contato_compras:
            rodape_comprador.append(f"Contato: {parametros.contato_compras}")
        
        if rodape_comprador:
            rodape_comprador_text = " | ".join(rodape_comprador)
            
            rodape_comprador_style = ParagraphStyle(
                'RodapeComprador',
                parent=normal_style,
                fontSize=8,
                alignment=TA_CENTER,
                textColor=COR_PRIMARIA,
                fontName='Helvetica-Bold'
            )
            
            elementos.append(Paragraph(rodape_comprador_text, rodape_comprador_style))
            elementos.append(Spacer(1, 10))
    
    # Informações de geração
    usuario_nome = pedido.criado_por.get_full_name() or pedido.criado_por.username
    rodape_text = f"Pedido gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {usuario_nome}"
    
    rodape_style = ParagraphStyle(
        'RodapeCustom',
        parent=normal_style,
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#718096')
    )
    
    elementos.append(Paragraph(rodape_text, rodape_style))
    
    # Construir PDF
    doc.build(elementos)

    # Resetar buffer
    buffer.seek(0)

    return buffer


def gerar_pdf_vistoria(vistoria):
    """
    Gera PDF do relatório de vistoria com fotos e assinatura digital
    """
    buffer = BytesIO()

    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f'Relatório de Vistoria - Proposta {vistoria.proposta.numero}'
    )

    # Buscar parâmetros da empresa
    try:
        parametros = ParametrosGerais.objects.first()
    except:
        parametros = None

    # Estilos
    styles = getSampleStyleSheet()

    # Cores da identidade visual
    COR_PRIMARIA = colors.HexColor('#1a365d')
    COR_SECUNDARIA = colors.HexColor('#2c5282')
    COR_ACCENT = colors.HexColor('#3182ce')
    COR_TEXTO = colors.HexColor('#2d3748')
    COR_BACKGROUND = colors.HexColor('#f7fafc')

    titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=10,
        alignment=TA_CENTER,
        textColor=COR_PRIMARIA,
        fontName='Helvetica-Bold'
    )

    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
        textColor=COR_SECUNDARIA,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'NormalMelhorado',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=COR_TEXTO,
        alignment=TA_LEFT
    )

    empresa_style = ParagraphStyle(
        'EmpresaStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=COR_TEXTO,
        spaceAfter=0
    )

    elementos = []

    # =============================================================================
    # CABEÇALHO DA EMPRESA
    # =============================================================================

    if parametros:
        elementos.append(Paragraph(f"<b>{parametros.razao_social}</b>", titulo_principal))
        elementos.append(Spacer(1, 2))

        if parametros.nome_fantasia:
            elementos.append(Paragraph(parametros.nome_fantasia, empresa_style))

        # Informações da empresa
        empresa_info = []

        # Endereço
        endereco_parts = []
        if parametros.endereco:
            endereco_parts.append(parametros.endereco)
            if parametros.numero:
                endereco_parts[-1] += f", {parametros.numero}"
        if parametros.bairro:
            endereco_parts.append(parametros.bairro)
        if parametros.cidade and parametros.estado:
            endereco_parts.append(f"{parametros.cidade} - {parametros.estado}")
        if parametros.cep:
            endereco_parts.append(f"CEP: {parametros.cep}")

        if endereco_parts:
            empresa_info.append([Paragraph(" • ".join(endereco_parts), empresa_style)])

        # Contatos
        contatos = []
        if parametros.telefone:
            contatos.append(f"Tel: {parametros.telefone}")
        if parametros.email:
            contatos.append(f"Email: {parametros.email}")
        if parametros.cnpj:
            contatos.append(f"CNPJ: {parametros.cnpj}")

        if contatos:
            empresa_info.append([Paragraph(" • ".join(contatos), empresa_style)])

        if empresa_info:
            empresa_table = Table(empresa_info, colWidths=[18*cm])
            empresa_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            elementos.append(empresa_table)

    elementos.append(Spacer(1, 10))

    # =============================================================================
    # TÍTULO DO DOCUMENTO
    # =============================================================================

    elementos.append(Paragraph("RELATÓRIO DE VISTORIA", titulo_principal))
    elementos.append(Spacer(1, 10))

    # =============================================================================
    # DADOS DA PROPOSTA
    # =============================================================================

    proposta = vistoria.proposta

    proposta_data = [
        [
            Paragraph("<b>Proposta:</b>", normal_style),
            Paragraph(proposta.numero, normal_style),
            Paragraph("<b>Cliente:</b>", normal_style),
            Paragraph(proposta.cliente.nome_fantasia or proposta.cliente.razao_social, normal_style)
        ],
        [
            Paragraph("<b>Data da Vistoria:</b>", normal_style),
            Paragraph(vistoria.data_vistoria.strftime('%d/%m/%Y às %H:%M'), normal_style),
            Paragraph("<b>Obra:</b>", normal_style),
            Paragraph(proposta.obra or "N/I", normal_style)
        ]
    ]

    if proposta.endereco_obra:
        proposta_data.append([
            Paragraph("<b>Endereço da Obra:</b>", normal_style),
            Paragraph(proposta.endereco_obra, normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style)
        ])

    proposta_table = Table(proposta_data, colWidths=[3.5*cm, 5.5*cm, 3*cm, 6*cm])
    proposta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, -1), COR_BACKGROUND),
        ('BACKGROUND', (2, 0), (3, -1), COR_BACKGROUND),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 2, COR_ACCENT),
    ]))

    elementos.append(proposta_table)
    elementos.append(Spacer(1, 15))

    # =============================================================================
    # OBSERVAÇÕES
    # =============================================================================

    if vistoria.observacoes:
        elementos.append(Paragraph("<b>Observações:</b>", subtitulo_style))
        elementos.append(Spacer(1, 5))

        obs_style = ParagraphStyle(
            'ObsStyle',
            parent=normal_style,
            fontSize=10,
            leading=16,
            alignment=TA_JUSTIFY
        )

        elementos.append(Paragraph(vistoria.observacoes, obs_style))
        elementos.append(Spacer(1, 15))

    # =============================================================================
    # FOTOS DA VISTORIA
    # =============================================================================

    fotos = vistoria.fotos.all()

    if fotos:
        elementos.append(Paragraph("<b>Registro Fotográfico:</b>", subtitulo_style))
        elementos.append(Spacer(1, 10))

        # Processar fotos em grades de 2 colunas
        foto_rows = []
        foto_row_atual = []

        for i, foto in enumerate(fotos):
            try:
                # Baixar imagem da URL assinada
                response = requests.get(foto.foto_url, timeout=10)
                if response.status_code == 200:
                    img_buffer = BytesIO(response.content)

                    # Abrir com PIL para redimensionar
                    pil_img = PILImage.open(img_buffer)

                    # Redimensionar mantendo proporção (largura máxima 8cm)
                    max_width = 8 * cm
                    max_height = 6 * cm

                    aspect = pil_img.width / pil_img.height
                    if pil_img.width > max_width or pil_img.height > max_height:
                        if aspect > 1:  # Landscape
                            new_width = max_width
                            new_height = max_width / aspect
                        else:  # Portrait
                            new_height = max_height
                            new_width = max_height * aspect
                    else:
                        new_width = pil_img.width
                        new_height = pil_img.height

                    # Salvar imagem redimensionada em buffer
                    img_resized_buffer = BytesIO()
                    pil_img.save(img_resized_buffer, format='JPEG', quality=85)
                    img_resized_buffer.seek(0)

                    # Criar Image do ReportLab
                    img_reportlab = Image(img_resized_buffer, width=new_width, height=new_height)

                    # Adicionar legenda se existir
                    if foto.legenda:
                        legenda_style = ParagraphStyle(
                            'LegendaStyle',
                            parent=normal_style,
                            fontSize=8,
                            alignment=TA_CENTER,
                            textColor=colors.HexColor('#718096')
                        )
                        legenda_para = Paragraph(foto.legenda, legenda_style)
                        foto_com_legenda = [img_reportlab, Spacer(1, 3), legenda_para]
                    else:
                        foto_com_legenda = [img_reportlab]

                    foto_row_atual.append(foto_com_legenda)

                    # Se completou 2 fotos, adiciona a linha
                    if len(foto_row_atual) == 2:
                        foto_rows.append(foto_row_atual)
                        foto_row_atual = []

            except Exception as e:
                print(f"Erro ao processar foto {foto.id}: {str(e)}")
                continue

        # Adicionar última linha se tiver foto sozinha
        if foto_row_atual:
            # Preencher com célula vazia se necessário
            if len(foto_row_atual) == 1:
                foto_row_atual.append("")
            foto_rows.append(foto_row_atual)

        # Criar tabela de fotos
        if foto_rows:
            for row in foto_rows:
                foto_table = Table([row], colWidths=[9*cm, 9*cm])
                foto_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                elementos.append(foto_table)

            elementos.append(Spacer(1, 10))

    # =============================================================================
    # ASSINATURA DIGITAL
    # =============================================================================

    if vistoria.assinatura_url:
        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph("<b>Assinatura Digital:</b>", subtitulo_style))
        elementos.append(Spacer(1, 10))

        try:
            # Baixar assinatura
            response = requests.get(vistoria.assinatura_url, timeout=10)
            if response.status_code == 200:
                assinatura_buffer = BytesIO(response.content)

                # Criar imagem da assinatura (tamanho fixo)
                assinatura_img = Image(assinatura_buffer, width=6*cm, height=3*cm)

                # Dados da assinatura
                assinatura_info = [
                    [assinatura_img,
                     Paragraph(f"<b>Assinado por:</b><br/>{vistoria.assinatura_nome}<br/><br/>"
                              f"<b>Data:</b> {vistoria.data_vistoria.strftime('%d/%m/%Y às %H:%M')}",
                              normal_style)]
                ]

                assinatura_table = Table(assinatura_info, colWidths=[8*cm, 10*cm])
                assinatura_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('BACKGROUND', (0, 0), (-1, -1), COR_BACKGROUND),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))

                elementos.append(assinatura_table)

        except Exception as e:
            print(f"Erro ao processar assinatura: {str(e)}")

    # =============================================================================
    # RODAPÉ
    # =============================================================================

    elementos.append(Spacer(1, 30))

    rodape_text = f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    if vistoria.usuario:
        usuario_nome = vistoria.usuario.get_full_name() or vistoria.usuario.username
        rodape_text += f" por {usuario_nome}"

    rodape_style = ParagraphStyle(
        'RodapeCustom',
        parent=normal_style,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#718096')
    )

    elementos.append(Paragraph(rodape_text, rodape_style))

    # Construir PDF
    doc.build(elementos)

    # Resetar buffer
    buffer.seek(0)

    return buffer