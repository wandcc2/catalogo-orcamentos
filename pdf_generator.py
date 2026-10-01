import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_cliente(carrinho, caminho_saida="orcamento_cliente.pdf", nome_cliente="Cliente"):
    """
    Gera o PDF do orçamento para envio ao cliente (sem exibições de custo).
    """
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloCustom',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12
    )
    
    normal_style = styles['Normal']
    header_table_style = ParagraphStyle('HeaderTable', parent=normal_style, fontName='Helvetica-Bold', textColor=colors.whitesmoke)
    
    elements = []
    
    elements.append(Paragraph("ORÇAMENTO DE PRODUTOS", titulo_style))
    elements.append(Paragraph(f"<b>Cliente:</b> {nome_cliente}", normal_style))
    elements.append(Spacer(1, 15))
    
    table_data = [
        [
            Paragraph("Imagem", header_table_style),
            Paragraph("Item / Descrição", header_table_style),
            Paragraph("Qtd", header_table_style),
            Paragraph("Preço Un.", header_table_style),
            Paragraph("Total", header_table_style)
        ]
    ]
    
    total_geral = 0.0
    
    for item in carrinho:
        subtotal = item['preco_venda'] * item['quantidade']
        total_geral += subtotal
        
        img_element = "Sem foto"
        if item.get('imagem_path') and os.path.exists(item['imagem_path']):
            try:
                img_element = RLImage(item['imagem_path'], width=50, height=50)
            except Exception:
                img_element = "Sem foto"
            
        descricao_p = Paragraph(f"<b>{item['nome']}</b><br/><font size=8 color='#555555'>{item.get('descricao', '')}</font>", normal_style)
        
        table_data.append([
            img_element,
            descricao_p,
            str(item['quantidade']),
            f"R$ {item['preco_venda']:.2f}",
            f"R$ {subtotal:.2f}"
        ])
    
    table_data.append([
        "", "", "",
        Paragraph("<b>Total Geral:</b>", normal_style),
        Paragraph(f"<b>R$ {total_geral:.2f}</b>", normal_style)
    ])
    
    col_widths = [60, 240, 40, 90, 90]
    
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#CBD5E1")),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor("#1E3A8A")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return caminho_saida


def gerar_pdf_interno(carrinho, caminho_saida="relatorio_custos.pdf"):
    """
    Gera o relatório interno com detalhamento de custos, vendas e margem.
    """
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloInterno',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#B91C1C"),
        spaceAfter=12
    )
    
    normal_style = styles['Normal']
    header_style = ParagraphStyle('HeaderTable', parent=normal_style, fontName='Helvetica-Bold', textColor=colors.whitesmoke)
    
    elements = []
    
    elements.append(Paragraph("RELATÓRIO INTERNO DE CUSTOS E MARGEM", titulo_style))
    elements.append(Spacer(1, 10))
    
    table_data = [
        [
            Paragraph("Item", header_style),
            Paragraph("Qtd", header_style),
            Paragraph("Custo Un.", header_style),
            Paragraph("Venda Un.", header_style),
            Paragraph("Custo Total", header_style),
            Paragraph("Venda Total", header_style),
            Paragraph("Lucro Bruto", header_style)
        ]
    ]
    
    total_custo = 0.0
    total_venda = 0.0
    
    for item in carrinho:
        sub_custo = item['preco_custo'] * item['quantidade']
        sub_venda = item['preco_venda'] * item['quantidade']
        lucro_item = sub_venda - sub_custo
        
        total_custo += sub_custo
        total_venda += sub_venda
        
        table_data.append([
            Paragraph(f"<b>{item['nome']}</b>", normal_style),
            str(item['quantidade']),
            f"R$ {item['preco_custo']:.2f}",
            f"R$ {item['preco_venda']:.2f}",
            f"R$ {sub_custo:.2f}",
            f"R$ {sub_venda:.2f}",
            f"R$ {lucro_item:.2f}"
        ])
    
    lucro_total = total_venda - total_custo
    
    table_data.append([
        Paragraph("<b>TOTAL</b>", normal_style),
        "", "", "",
        Paragraph(f"<b>R$ {total_custo:.2f}</b>", normal_style),
        Paragraph(f"<b>R$ {total_venda:.2f}</b>", normal_style),
        Paragraph(f"<b>R$ {lucro_total:.2f}</b>", normal_style)
    ])
    
    col_widths = [150, 35, 70, 70, 70, 70, 75]
    
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#991B1B")),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#FECACA")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEE2E2")),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return caminho_saida