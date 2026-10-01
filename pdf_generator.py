import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_cliente(carrinho, output_path="orcamento_cliente.pdf", nome_cliente="Cliente"):
    """Gera o PDF de orçamento voltado para o cliente (com preço de venda e condições de pagamento)."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1A2B4C'),
        spaceAfter=12
    )

    story.append(Paragraph(f"<b>Orçamento para:</b> {nome_cliente}", title_style))
    story.append(Spacer(1, 12))

    # Tabela com as colunas do cliente
    data = [["Imagem", "Produto", "Qtd", "Preço Unit. (R$)", "Subtotal (R$)"]]
    
    total = 0.0

    for item in carrinho:
        img = "Sem Imagem"
        if item.get("imagem_path") and os.path.exists(item["imagem_path"]):
            try:
                img = Image(item["imagem_path"], width=50, height=50)
            except Exception:
                img = "Erro Img"

        qtd = item["quantidade"]
        venda = item["preco_venda"]
        subtotal = qtd * venda
        total += subtotal

        data.append([
            img,
            Paragraph(item["nome"], styles['Normal']),
            str(qtd),
            f"{venda:.2f}",
            f"{subtotal:.2f}"
        ])

    # Linha com o Total
    data.append(["", "", "", Paragraph("<b>Total:</b>", styles['Normal']), f"R$ {total:.2f}"])

    t = Table(data, colWidths=[60, 200, 40, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A2B4C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ]))

    story.append(t)
    story.append(Spacer(1, 20))

    # -------------------------------------------------------------------
    # CONDIÇÕES DE PAGAMENTO (DESCONTO À VISTA E FATOR PARCELADO)
    # -------------------------------------------------------------------
    desconto_avista = total * 0.10
    total_avista = total - desconto_avista
    entrada_50 = total / 2.0

    condicoes_html = f"""
    <b>CONDIÇÕES DE PAGAMENTO:</b><br/><br/>
    • <b>À Vista (10% de Desconto):</b> R$ {total_avista:.2f} (Economia de R$ {desconto_avista:.2f})<br/>
    • <b>Parcelado (50% / 50%):</b> 1ª Entrada de R$ {entrada_50:.2f} no ato do pedido + 2ª Parcela de R$ {entrada_50:.2f} no ato da entrega.
    """

    style_box = ParagraphStyle(
        'CondicoesStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1A2B4C')
    )

    p_condicoes = Paragraph(condicoes_html, style_box)

    # Tabela estilizada para envelopar as condições de pagamento
    t_condicoes = Table([[p_condicoes]], colWidths=[500])
    t_condicoes.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F2F4F8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1A2B4C')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))

    story.append(t_condicoes)

    doc.build(story)
    return output_path


def gerar_pdf_interno(carrinho, output_path="relatorio_custos_interno.pdf"):
    """Gera o PDF de relatório interno com custos, margem e lucros previstos."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#8B0000'),
        spaceAfter=12
    )

    story.append(Paragraph("Relatório Interno de Custos e Margens", title_style))
    story.append(Spacer(1, 12))

    data = [["Produto", "Qtd", "Custo (R$)", "Venda (R$)", "Subtotal Custo", "Subtotal Venda", "Lucro (R$)"]]
    
    total_custo = 0.0
    total_venda = 0.0

    for item in carrinho:
        qtd = item["quantidade"]
        custo = item["preco_custo"]
        venda = item["preco_venda"]
        
        sub_custo = qtd * custo
        sub_venda = qtd * venda
        lucro_item = sub_venda - sub_custo

        total_custo += sub_custo
        total_venda += sub_venda

        data.append([
            Paragraph(item["nome"], styles['Normal']),
            str(qtd),
            f"{custo:.2f}",
            f"{venda:.2f}",
            f"{sub_custo:.2f}",
            f"{sub_venda:.2f}",
            f"{lucro_item:.2f}"
        ])

    lucro_total = total_venda - total_custo

    data.append(["Total Geral", "", "", "", f"{total_custo:.2f}", f"{total_venda:.2f}", f"{lucro_total:.2f}"])

    t = Table(data, colWidths=[120, 35, 65, 65, 75, 75, 65])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F0F0F0')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))

    story.append(t)
    doc.build(story)
    return output_path
