import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_dieta(df_resultados, costo_total, cms_req, ecm, raza, estado_prod, dr_nombre="Dr. Alejandro Castañeda Correa"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#054A29'),
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        spaceAfter=18
    )
    
    # Encabezado
    story.append(Paragraph("<b>LECHER-IA Pro — Reporte de Formulación Nutricional</b>", title_style))
    story.append(Paragraph(f"<b>Diseñado por:</b> {dr_nombre} | <b>Perfil:</b> {raza} ({estado_prod})", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Resumen Metabólico
    summary_text = f"<b>Consumo Objetvo (CMS):</b> {cms_req} kg MS/día &nbsp;&nbsp;|&nbsp;&nbsp; <b>ECM (Leche Corregida):</b> {ecm:.2f} kg/día &nbsp;&nbsp;|&nbsp;&nbsp; <b>Costo Diario:</b> ${costo_total:.2f} MXN"
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Tabla de Dieta
    table_data = [["Ingrediente", "Inclusión (kg MS)", "% Dieta (MS)", "Costo (MXN)"]]
    for _, row in df_resultados.iterrows():
        table_data.append([
            str(row["Ingrediente"]),
            f"{row['Inclusión (kg MS)']:.2f}",
            f"{row['% en la Dieta (MS)']:.2f}%",
            f"${row['Costo Parcial (MXN)']:.2f}"
        ])
        
    t = Table(table_data, colWidths=[180, 110, 110, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#137547')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<font size=8 color='#888888'>Documento generado automáticamente por Lecher-IA Pro. Válido para mezclado en carro mezclador TMR.</font>", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
