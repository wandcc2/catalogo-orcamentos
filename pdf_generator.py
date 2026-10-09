import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def obter_logo_cabecalho():
    """Verifica se existe uma imagem de logo na raiz do projeto e a retorna formatada."""
    caminhos_possiveis = ["logo.png", "logo.jpg", "logo.jpeg"]
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            try:
                return Image(caminho, width=120, height=50)
            except Exception:
                return None
    return None

def gerar_pdf_cliente(carrinho, output_path="orcamento_cliente.pdf", nome_cliente="Cliente"):
    """
    Gera o PDF do orçamento para o cliente com logo, descontos por quantidade 
    e condições de pagamento.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1A2B4C'),
        spaceAfter=6
    )

    # -------------------------------------------------------------------
    # CABEÇALHO (LOGO + TÍTULO / CLIENTE)
    # -------------------------------------------------------------------
    img_logo = obter_logo_cabecalho()
    p_titulo = Paragraph(f"<b>ORÇAMENTO DE VENDA</b><br/><font size=11 color='#555555'>Cliente: {nome_cliente}</font>", title_style)

    if img_logo:
        header_table = Table([[img_logo, p_titulo]], colWidths=[140, 400])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(header_table)
    else:
        story.append(p_titulo)

    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------
    # TABELA DE PRODUTOS
    # -------------------------------------------------------------------
    data = [["Imagem", "Produto", "Qtd", "Preço Tab.", "Desc.", "Preço Un.", "Subtotal (R$)"]]
    total = 0.0

    for item in carrinho:
        img = "Sem Imagem"
        if item.get("imagem_path") and os.path.exists(item["imagem_path"]):
            try:
                img = Image(item["imagem_path"], width=40, height=40)
            except Exception:
                img = "Sem Imagem"

        qtd = item["quantidade"]
        venda_unitario = item["preco_venda"]
        venda_original = item.get("preco_venda_original", venda_unitario)
        desconto_str = item.get("desconto_aplicado", "0%")

        subtotal = qtd * venda_unitario
        total += subtotal

        data.append([
            img,
            Paragraph(item["nome"], styles['Normal']),
            str(qtd),
            f"R$ {venda_original:.2f}",
            desconto_str,
            f"R$ {venda_unitario:.2f}",
            f"R$ {subtotal:.2f}"
        ])

    # LINHA DO TOTAL (FORMATADA COM PARAGRAPH CORRETAMENTE)
    data.append([
        "", "", "", "", "", 
        Paragraph("<b>Total:</b>", styles['Normal']), 
        Paragraph(f"<b>R$ {total:.2f}</b>", styles['Normal'])
    ])

    col_widths = [50, 180, 35, 75, 45, 75, 80]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A2B4C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-
