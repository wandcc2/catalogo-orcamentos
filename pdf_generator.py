import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def gerar_pdf_cliente(carrinho, caminho_saida, nome_cliente, logo_path=None, observacoes=""):
    doc = SimpleDocTemplate(caminho_saida, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    # Estilos
    style_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1d4ed8'), spaceAfter=5)
    style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#333333'))
    style_tabela_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=10, textColor=colors.white, fontName='Helvetica-Bold')
    style_legenda = ParagraphStyle('Legenda', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#1d4ed8'))
    style_pagamento = ParagraphStyle('Pagamento', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#111827'), leading=14)
    style_obs = ParagraphStyle('Obs', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#374151'), leading=13)

    # Cabeçalho com Logo (se houver)
    if logo_path and os.path.exists(logo_path):
        try:
            img_logo = Image(logo_path, width=100, height=50)
            img_logo.hAlign = 'LEFT'
            story.append(img_logo)
            story.append(Spacer(1, 10))
        except Exception:
            pass

    story.append(Paragraph("<b>ORÇAMENTO DE PRODUTOS</b>", style_titulo))
    story.append(Paragraph(f"<b>Cliente:</b> {nome_cliente}", style_normal))
    story.append(Spacer(1, 15))

    # Tabela de Itens
    dados_tabela = [
        [
            Paragraph("Item", style_tabela_header),
            Paragraph("Qtd", style_tabela_header),
            Paragraph("Preço Tabela", style_tabela_header),
            Paragraph("Desconto", style_tabela_header),
            Paragraph("Preço Unit. c/ Desc.", style_tabela_header),
            Paragraph("Subtotal", style_tabela_header)
        ]
    ]

    total_venda = 0.0

    for item in carrinho:
        subtotal = item["preco_venda"] * item["quantidade"]
        total_venda += subtotal
        
        dados_tabela.append([
            Paragraph(item["nome"], style_normal),
            Paragraph(str(item["quantidade"]), style_normal),
            Paragraph(f"R$ {item['preco_venda_original']:.2f}", style_normal),
            Paragraph(str(item["desconto_aplicado"]), style_normal),
            Paragraph(f"R$ {item['preco_venda']:.2f}", style_normal),
            Paragraph(f"R$ {subtotal:.2f}", style_normal)
        ])

    tabela = Table(dados_tabela, colWidths=[180, 40, 80, 60, 90, 80])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    
    story.append(tabela)
    story.append(Spacer(1, 15))

    # Total
    style_total = ParagraphStyle('Total', parent=styles['Heading2'], fontSize=12, alignment=2, textColor=colors.HexColor('#111827'))
    story.append(Paragraph(f"<b>Total: R$ {total_venda:.2f}</b>", style_total))
    story.append(Spacer(1, 10))

    # Observações (Se houver preenchimento)
    if observacoes and observacoes.strip():
        texto_observacao = f"<b>OBSERVAÇÕES:</b><br/>{observacoes.replace(chr(10), '<br/>')}"
        tabela_obs = Table([[Paragraph(texto_observacao, style_obs)]], colWidths=[530])
        tabela_obs.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffbeb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#fde68a')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(tabela_obs)
        story.append(Spacer(1, 10))

    # Caixa de Condições de Pagamento
    texto_pagamento = f"""
    <b>CONDIÇÕES DE PAGAMENTO:</b><br/>
    • <b>À Vista (10% de Desconto):</b> R$ {total_venda * 0.9:.2f}<br/>
    • <b>1+1 (50% / 50%):</b> 1ª Entrada no ato do pedido (R$ {total_venda / 2:.2f}) + 2ª Parcela na entrega (R$ {total_venda / 2:.2f}).
    """

    tabela_pagamento = Table([[Paragraph(texto_pagamento, style_pagamento)]], colWidths=[530])
    tabela_pagamento.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(tabela_pagamento)
    story.append(Spacer(1, 15))

    # Caixa de Legenda do Desconto Progressivo
    texto_legenda = """
    <b>TABELA DE DESCONTO PROGRESSIVO POR QUANTIDADE DE CAMISETAS:</b><br/>
    • Até 10 un: <b>Sem Desconto</b> | • 11 a 20 un: <b>10%</b> | • 21 a 30 un: <b>15%</b><br/>
    • 31 a 40 un: <b>20%</b> | • 41 a 50 un: <b>22%</b> | • 51+ un: <b>25% de Desconto</b>
    """
    
    tabela_legenda = Table([[Paragraph(texto_legenda, style_legenda)]], colWidths=[530])
    tabela_legenda.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(tabela_legenda)
    doc.build(story)
    return caminho_saida


def gerar_pdf_interno(carrinho, caminho_saida):
    doc = SimpleDocTemplate(caminho_saida, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    style_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#dc2626'), spaceAfter=10)
    style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#333333'))
    style_tabela_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=10, textColor=colors.white, fontName='Helvetica-Bold')

    story.append(Paragraph("<b>RELATÓRIO DE CUSTO E LUCRO INTERNO</b>", style_titulo))
    story.append(Spacer(1, 15))

    dados_tabela = [
        [
            Paragraph("Item", style_tabela_header),
            Paragraph("Qtd", style_tabela_header),
            Paragraph("Custo Unit.", style_tabela_header),
            Paragraph("Venda Unit.", style_tabela_header),
            Paragraph("Subtotal Custo", style_tabela_header),
            Paragraph("Subtotal Venda", style_tabela_header)
        ]
    ]

    total_custo = 0.0
    total_venda = 0.0

    for item in carrinho:
        sub_custo = item["preco_custo"] * item["quantidade"]
        sub_venda = item["preco_venda"] * item["quantidade"]
        total_custo += sub_custo
        total_venda += sub_venda

        dados_tabela.append([
            Paragraph(item["nome"], style_normal),
            Paragraph(str(item["quantidade"]), style_normal),
            Paragraph(f"R$ {item['preco_custo']:.2f}", style_normal),
            Paragraph(f"R$ {item['preco_venda']:.2f}", style_normal),
            Paragraph(f"R$ {sub_custo:.2f}", style_normal),
            Paragraph(f"R$ {sub_venda:.2f}", style_normal)
        ])

    tabela = Table(dados_tabela, colWidths=[180, 40, 75, 75, 80, 80])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991b1b')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))

    story.append(tabela)
    story.append(Spacer(1, 15))

    lucro = total_venda - total_custo
    style_resumo = ParagraphStyle('Resumo', parent=styles['Normal'], fontSize=11, alignment=2)
    story.append(Paragraph(f"<b>Custo Total:</b> R$ {total_custo:.2f}", style_resumo))
    story.append(Paragraph(f"<b>Venda Total:</b> R$ {total_venda:.2f}", style_resumo))
    story.append(Paragraph(f"<b>Lucro Bruto Estimado:</b> R$ {lucro:.2f}", style_resumo))

    doc.build(story)
    return caminho_saida
