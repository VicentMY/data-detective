import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def exportar_df_a_pdf(df: pd.DataFrame, path: str, titulo: str = "", chunk_size: int = 6):
    """
    Exporta un DataFrame de Pandas a un archivo PDF.

    Args:
        df (pd.DataFrame): DataFrame con los datos a exportar.
        path (str): Ruta donde se guardará el archivo PDF.
        titulo (str, opcional): Título del documento PDF.
        chunk_size (int): Número máximo de columnas por tabla.
    """
    # Usamos A4 en horizontal (landscape) para que las tablas quepan mejor
    page_width, page_height = landscape(A4)
    
    doc = SimpleDocTemplate(path, pagesize=(page_width, page_height))
    elements = []
    
    styles = getSampleStyleSheet()
    
    if titulo:
        elements.append(Paragraph(titulo, styles['Title']))
        elements.append(Spacer(1, 20)) # Añadir algo de espacio
        
    num_cols = len(df.columns)
    
    # Dividir el DataFrame en trozos de 'chunk_size' columnas
    for i in range(0, num_cols, chunk_size):
        df_chunk = df.iloc[:, i:i+chunk_size]
        
        # Mostrar un subtítulo para cada parte si se ha dividido la tabla
        if num_cols > chunk_size:
            part_title = f"Parte {i//chunk_size + 1} (Columnas {i+1} a {min(i+chunk_size, num_cols)})"
            elements.append(Paragraph(part_title, styles['Heading3']))
            elements.append(Spacer(1, 10))

        # Convertir todos los datos a string para evitar errores con ReportLab
        data = [df_chunk.columns.astype(str).tolist()] + df_chunk.astype(str).values.tolist()
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)), # Cabecera
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.95, 0.95, 0.95)), # Filas
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 25)) # Espacio entre tablas si hay varias o antes del final
        
    doc.build(elements)
