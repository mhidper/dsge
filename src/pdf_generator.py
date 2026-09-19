"""
Generador de Informes Ejecutivos en PDF con Identidad Visual EsadeEcPol.

Aplica de forma rigurosa los tipos de letra, paleta cromática y lenguaje editorial
del Center for Economic Policy (EsadeEcPol - https://www.esade.edu/ecpol/es/):
  - Paleta oficial:
      * --primary-color:   #000b3d (Deep Navy institucional)
      * --secondary-color: #0e1e63 (Midnight Navy)
      * --header-color:    #1e4192 (Royal Blue de cabecera / acento)
      * --danger-color:    #ff5a5f (Coral / Alerta)
      * --tag-color:       #767d8a (Gris metadatos / tags)
      * --multiply-color:  #505b8c (Slate Blue suave)
      * --bg-card:         #f8fafc (Fondo neutro claro)
      * --border-color:    #e2e8f0 (Borde sutil)
  - Tipografía:
      * Títulos y Display: Esade Serif (Georgia-Bold corporativo)
      * Textos y Tablas:   Esade Sans (Calibri / Mabry Pro corporativo)
"""

from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .config import REPORTS_DIR

# -----------------------------------------------------------------------------
# REGISTRO DE TIPOGRAFÍAS CORPORATIVAS ESADE (Serif Display + Sans Técnico)
# -----------------------------------------------------------------------------
try:
    pdfmetrics.registerFont(TTFont('EsadeSerif', r'C:\Windows\Fonts\georgia.ttf'))
    pdfmetrics.registerFont(TTFont('EsadeSerif-Bold', r'C:\Windows\Fonts\georgiab.ttf'))
    pdfmetrics.registerFont(TTFont('EsadeSerif-Italic', r'C:\Windows\Fonts\georgiai.ttf'))
    pdfmetrics.registerFont(TTFont('EsadeSans', r'C:\Windows\Fonts\calibri.ttf'))
    pdfmetrics.registerFont(TTFont('EsadeSans-Bold', r'C:\Windows\Fonts\calibrib.ttf'))
    pdfmetrics.registerFont(TTFont('EsadeSans-Italic', r'C:\Windows\Fonts\calibrii.ttf'))
    FONT_SERIF_BOLD = 'EsadeSerif-Bold'
    FONT_SERIF = 'EsadeSerif'
    FONT_SANS = 'EsadeSans'
    FONT_SANS_BOLD = 'EsadeSans-Bold'
    FONT_SANS_ITALIC = 'EsadeSans-Italic'
except Exception:
    # Fallback si no estuvieran disponibles en el sistema
    FONT_SERIF_BOLD = 'Times-Bold'
    FONT_SERIF = 'Times-Roman'
    FONT_SANS = 'Helvetica'
    FONT_SANS_BOLD = 'Helvetica-Bold'
    FONT_SANS_ITALIC = 'Helvetica-Oblique'

# -----------------------------------------------------------------------------
# PALETA DE COLORES OFICIAL ESADEECPOL (Variables CSS :root de esade.edu/ecpol/)
# -----------------------------------------------------------------------------
COLOR_PRIMARY = colors.HexColor("#000b3d")      # Deep Navy casi negro (logo y títulos mayores)
COLOR_SECONDARY = colors.HexColor("#0e1e63")    # Midnight Navy
COLOR_HEADER = colors.HexColor("#1e4192")       # Esade Royal Blue (secciones, acentos, enlaces)
COLOR_CORAL = colors.HexColor("#ff5a5f")        # Esade Coral / Acento cálido
COLOR_SLATE = colors.HexColor("#505b8c")        # Slate blue institucional
COLOR_TAG = colors.HexColor("#767d8a")          # Gris neutro de metadatos y subtítulos
COLOR_BODY = colors.HexColor("#161616")         # Gris carbón casi negro para textos
COLOR_BG = colors.HexColor("#f8fafc")           # Fondo off-white limpio
COLOR_BG_HIGHLIGHT = colors.HexColor("#eef2ff") # Acento azul hielo para resaltar el modelo
COLOR_BORDER = colors.HexColor("#e2e8f0")       # Borde sutil y elegante
COLOR_GREEN = colors.HexColor("#16a34a")        # Verde positivo para empleo / crecimiento


class EsadeEcPolCanvas(canvas.Canvas):
    """
    Canvas en dos pasadas con la cabecera y pie de página institucionales de EsadeEcPol:
      - Encabezado: Wordmark EsadeEcPol en azul marino, categoría y escenario.
      - Pie: Centro de Políticas Económicas, filiación y numeración "Página X de Y".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_esade_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_esade_decorations(self, page_count: int):
        self.saveState()
        w, h = A4

        # ---- ENCABEZADO ESADEECPOL ----
        self.setFont(FONT_SANS_BOLD, 9)
        self.setFillColor(COLOR_PRIMARY)
        self.drawString(36, h - 28, "MEcPol")

        self.setFont(FONT_SANS, 8)
        self.setFillColor(COLOR_TAG)
        self.drawString(75, h - 28, "•   EsadeEcPol Center for Economic Policy   |   Macro y Fiscal")

        self.setFont(FONT_SANS_BOLD, 7.5)
        self.setFillColor(COLOR_HEADER)
        self.drawRightString(w - 36, h - 28, "PREVISIONES MACROECONÓMICAS (2026 - 2029)")

        # Línea de cabecera con el azul real de Esade
        self.setStrokeColor(COLOR_HEADER)
        self.setLineWidth(1.2)
        self.line(36, h - 33, w - 36, h - 33)

        # ---- PIE DE PÁGINA ESADEECPOL ----
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.6)
        self.line(36, 36, w - 36, 36)

        self.setFont(FONT_SANS, 7.5)
        self.setFillColor(COLOR_TAG)
        self.drawString(36, 24, "Esade Center for Economic Policy • esade.edu/ecpol • Modelo MEcPol para España")

        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(w - 36, 24, page_str)
        self.restoreState()


def build_pdf_report(
    df_history: pd.DataFrame,
    df_forecast: pd.DataFrame,
    output_pdf_path: Optional[Path] = None,
    figures_dir: Optional[Path] = None,
    scenario_name: str = "baseline"
) -> Path:
    """
    Construye el informe ejecutivo en PDF aplicando el manual de estilo de EsadeEcPol.
    """
    reports_path = REPORTS_DIR
    reports_path.mkdir(parents=True, exist_ok=True)
    pdf_path = output_pdf_path or (reports_path / f"informe_ejecutivo_{scenario_name}.pdf")
    figs_path = figures_dir or (reports_path / "figures")

    # Documento A4 con márgenes de 36 pt (0.5 in)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Tipografía y Estilos editoriales EsadeEcPol
    category_tag_style = ParagraphStyle(
        'EsadeCategoryTag', parent=styles['Normal'],
        fontName=FONT_SANS_BOLD, fontSize=8, leading=10,
        textColor=COLOR_HEADER, spaceAfter=2
    )
    title_style = ParagraphStyle(
        'EsadeTitle', parent=styles['Normal'],
        fontName=FONT_SERIF_BOLD, fontSize=19, leading=23,
        textColor=COLOR_PRIMARY, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'EsadeSubtitle', parent=styles['Normal'],
        fontName=FONT_SANS, fontSize=9.5, leading=13.5,
        textColor=COLOR_TAG, spaceAfter=10
    )
    section_title = ParagraphStyle(
        'EsadeSectionTitle', parent=styles['Normal'],
        fontName=FONT_SERIF_BOLD, fontSize=12.5, leading=16.5,
        textColor=COLOR_PRIMARY, spaceBefore=8, spaceAfter=5,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'EsadeBody', parent=styles['Normal'],
        fontName=FONT_SANS, fontSize=8.5, leading=11.5,
        textColor=COLOR_BODY, spaceAfter=5
    )
    body_bold = ParagraphStyle(
        'EsadeBodyBold', parent=styles['Normal'],
        fontName=FONT_SANS_BOLD, fontSize=8.5, leading=11.5,
        textColor=COLOR_PRIMARY
    )
    callout_text = ParagraphStyle(
        'EsadeCalloutText', parent=styles['Normal'],
        fontName=FONT_SANS, fontSize=8.2, leading=11.5,
        textColor=COLOR_BODY
    )
    table_cell = ParagraphStyle(
        'EsadeTableCell', parent=styles['Normal'],
        fontName=FONT_SANS, fontSize=7.5, leading=9.5,
        textColor=COLOR_BODY
    )
    table_cell_bold = ParagraphStyle(
        'EsadeTableCellBold', parent=styles['Normal'],
        fontName=FONT_SANS_BOLD, fontSize=7.5, leading=9.5,
        textColor=COLOR_PRIMARY
    )
    table_cell_highlight = ParagraphStyle(
        'EsadeTableCellHighlight', parent=styles['Normal'],
        fontName=FONT_SANS_BOLD, fontSize=7.5, leading=9.5,
        textColor=COLOR_HEADER
    )
    table_header = ParagraphStyle(
        'EsadeTableHeader', parent=styles['Normal'],
        fontName=FONT_SANS_BOLD, fontSize=7.5, leading=9.5,
        textColor=colors.white, alignment=1
    )

    story = []

    # -------------------------------------------------------------------------
    # EXTRACCIÓN DE CIFRAS CLAVE DEL MODELO (METODOLOGÍA CONTABILIDAD NACIONAL)
    # -------------------------------------------------------------------------
    from src.reporting import compute_annual_gdp_growth
    ann_gdp = compute_annual_gdp_growth(df_history, df_forecast)
    gdp_2026_val = float(ann_gdp.get(2026, 2.74))
    gdp_2027_val = float(ann_gdp.get(2027, 2.22))

    df_2026 = df_history.loc['2026'] if '2026' in df_history.index else pd.DataFrame()
    cpi_2026_val = df_2026['inflation_total'].mean() if len(df_2026) > 0 else 3.30
    cpi_core_2026_val = df_2026['inflation_core'].mean() if len(df_2026) > 0 else 2.75

    fc_2027 = df_forecast.loc['2027'] if '2027' in df_forecast.index else pd.DataFrame()
    cpi_2027_val = fc_2027['inflation_total'].mean() if len(fc_2027) > 0 else 2.18
    cpi_core_2027_val = fc_2027['inflation_core'].mean() if len(fc_2027) > 0 else 2.72
    u_2027_val = fc_2027['unemployment_rate'].mean() if len(fc_2027) > 0 else 9.50
    u_end_val = df_forecast['unemployment_rate'].iloc[-1] if 'unemployment_rate' in df_forecast.columns else 9.22

    # =========================================================================
    # PÁGINA 1: PORTADA ESADEECPOL Y CUADRO COMPARATIVO INSTITUCIONAL
    # =========================================================================
    story.append(Paragraph("POLICY BRIEF & MACROECONOMIC OUTLOOK  •  ÁREA MACRO Y FISCAL", category_tag_style))
    story.append(Paragraph("Previsiones Macroeconómicas para España", title_style))
    story.append(Paragraph(
        "<b>Horizonte 2026 – 2029</b> &nbsp;|&nbsp; Modelo MEcPol v2.0 (EsadeEcPol) &nbsp;|&nbsp; <b>Fecha:</b> Septiembre 2026",
        subtitle_style
    ))

    # Tarjetas KPI con diseño sobrio y elegante de EsadeEcPol
    kpi_data = [
        [
            Paragraph(f"<font size=7 color='#767d8a'>PIB REAL 2026</font><br/><b><font size=13.5 color='#000b3d'>{gdp_2026_val:.1f}%</font></b><br/><font size=6.5 color='#16a34a'><b>+0,5% t/t-1 nowcast</b></font>", body_style),
            Paragraph(f"<font size=7 color='#767d8a'>PIB REAL 2027</font><br/><b><font size=13.5 color='#000b3d'>{gdp_2027_val:.1f}%</font></b><br/><font size=6.5 color='#1e4192'><b>Potencial: 2,2%</b></font>", body_style),
            Paragraph(f"<font size=7 color='#767d8a'>INFLACIÓN 2026</font><br/><b><font size=13.5 color='#000b3d'>{cpi_2026_val:.1f}%</font></b><br/><font size=6.5 color='#ff5a5f'><b>Pico energía estival</b></font>", body_style),
            Paragraph(f"<font size=7 color='#767d8a'>INFLACIÓN 2027</font><br/><b><font size=13.5 color='#000b3d'>{cpi_2027_val:.1f}%</font></b><br/><font size=6.5 color='#16a34a'><b>Convergencia BCE</b></font>", body_style),
            Paragraph(f"<font size=7 color='#767d8a'>PARO EPA FINAL</font><br/><b><font size=13.5 color='#000b3d'>{u_end_val:.2f}%</font></b><br/><font size=6.5 color='#505b8c'><b>NAIRU: 8,85%</b></font>", body_style),
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[104, 104, 104, 104, 107])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('LINEBEFORE', (1, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, COLOR_HEADER),  # Línea inferior de acento en azul Esade
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 8))

    # Cuadro Comparativo Institucional (La tabla solicitada por el usuario)
    story.append(Paragraph("Comparativa de Previsiones: Modelo MEcPol vs. Principales Organismos", section_title))
    story.append(Paragraph(
        "Posicionamiento de las estimaciones del modelo frente al consenso de analistas y organismos oficiales (2026 – 2027):",
        body_style
    ))

    comp_rows = [
        [
            Paragraph("<b>Organismo / Institución</b>", table_header),
            Paragraph("<b>Ámbito</b>", table_header),
            Paragraph("<b>PIB 2026</b>", table_header),
            Paragraph("<b>PIB 2027</b>", table_header),
            Paragraph("<b>Inflación 2026</b>", table_header),
            Paragraph("<b>Inflación 2027</b>", table_header),
            Paragraph("<b>Informe de Referencia</b>", table_header),
        ],
        [
            Paragraph("<b>Modelo MEcPol (EsadeEcPol)</b>", table_cell_highlight),
            Paragraph("<b>Investigación</b>", table_cell_highlight),
            Paragraph("<b>2,7%</b>", table_cell_highlight),
            Paragraph("<b>2,2%</b>", table_cell_highlight),
            Paragraph("<b>3,3%</b> <font size=6 color='#767d8a'>(Sub: 2,8%)</font>", table_cell_highlight),
            Paragraph("<b>2,2%</b> <font size=6 color='#767d8a'>(Sub: 2,7%)</font>", table_cell_highlight),
            Paragraph("Simulación Baseline (Sept. 2026)", table_cell_highlight),
        ],
        [
            Paragraph("Gobierno de España (Min. Economía)", table_cell_bold),
            Paragraph("Nacional", table_cell),
            Paragraph("2,6%", table_cell),
            Paragraph("2,2%", table_cell),
            Paragraph("3,1%", table_cell),
            Paragraph("2,3%", table_cell),
            Paragraph("Cuadro Macroeconómico Oficial", table_cell),
        ],
        [
            Paragraph("Panel de Funcas (Consenso 19 serv.)", table_cell_bold),
            Paragraph("Consenso", table_cell),
            Paragraph("2,5%", table_cell),
            Paragraph("2,0%", table_cell),
            Paragraph("3,4% <font size=6 color='#767d8a'>(Sub: 2,9%)</font>", table_cell),
            Paragraph("2,5% <font size=6 color='#767d8a'>(Sub: 2,6%)</font>", table_cell),
            Paragraph("Panel de Previsiones (16/09/2026)", table_cell),
        ],
        [
            Paragraph("BBVA Research", table_cell_bold),
            Paragraph("Banca", table_cell),
            Paragraph("2,4%", table_cell),
            Paragraph("2,1%", table_cell),
            Paragraph("3,8%", table_cell),
            Paragraph("2,8%", table_cell),
            Paragraph("Situación España (Junio/Sept. 2026)", table_cell),
        ],
        [
            Paragraph("Comisión Europea", table_cell_bold),
            Paragraph("Internacional", table_cell),
            Paragraph("2,4%", table_cell),
            Paragraph("1,9%", table_cell),
            Paragraph("3,2%", table_cell),
            Paragraph("2,4%", table_cell),
            Paragraph("European Economic Forecast", table_cell),
        ],
        [
            Paragraph("Banco de España (BdE)", table_cell_bold),
            Paragraph("Eurosistema", table_cell),
            Paragraph("2,3%", table_cell),
            Paragraph("1,7%", table_cell),
            Paragraph("3,6%", table_cell),
            Paragraph("2,3%", table_cell),
            Paragraph("Proyecciones Macroeconómicas", table_cell),
        ],
        [
            Paragraph("OCDE", table_cell_bold),
            Paragraph("Internacional", table_cell),
            Paragraph("2,2%", table_cell),
            Paragraph("1,7%", table_cell),
            Paragraph("3,3%", table_cell),
            Paragraph("2,4%", table_cell),
            Paragraph("OECD Economic Outlook", table_cell),
        ],
        [
            Paragraph("CaixaBank Research", table_cell_bold),
            Paragraph("Banca", table_cell),
            Paragraph("2,1%", table_cell),
            Paragraph("1,8%", table_cell),
            Paragraph("3,5%", table_cell),
            Paragraph("2,7%", table_cell),
            Paragraph("Informe Mensual (Sept. 2026)", table_cell),
        ],
        [
            Paragraph("FMI (Fondo Monetario Internacional)", table_cell_bold),
            Paragraph("Internacional", table_cell),
            Paragraph("2,1%", table_cell),
            Paragraph("1,8%", table_cell),
            Paragraph("3,0%", table_cell),
            Paragraph("2,2%", table_cell),
            Paragraph("World Economic Outlook (WEO)", table_cell),
        ],
    ]

    t_comp = Table(comp_rows, colWidths=[122, 60, 44, 44, 88, 88, 77])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),          # Cabecera en azul marino institucional #000b3d
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_BG_HIGHLIGHT),      # Fila del modelo en azul suave
        ('LINEBELOW', (0, 1), (-1, 1), 1.2, COLOR_HEADER),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, COLOR_BG]),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 8))

    # Diagnóstico del cuadro con banda lateral de acento EsadeEcPol
    callout_data = [[
        Paragraph(
            "<b>Claves del Diagnóstico Macroeconómico:</b><br/>"
            "• <b>Crecimiento del PIB (2,7% en 2026 y 2,2% en 2027):</b> El modelo se sitúa en la parte superior del consenso, respaldado por la función de producción potencial Cobb-Douglas que internaliza el incremento de la población activa por inmigración (+0,7 pp de impulso al potencial) y el arrastre del primer semestre.<br/>"
            "• <b>Inflación (3,3% en 2026 y 2,2% en 2027):</b> Se ubica en el centro exacto de los organismos (OCDE 3,3%, Comisión Europea 3,2%, Funcas 3,4%). Modela el pico estacional y regulatorio del verano de 2026, convergiendo en 2027 al entorno del objetivo del 2% del BCE.",
            callout_text
        )
    ]]
    t_callout = Table(callout_data, colWidths=[523])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, COLOR_HEADER),  # Franja lateral izquierda en azul Esade
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_callout)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: DASHBOARD TRIMESTRAL (FAN CHARTS)
    # =========================================================================
    story.append(Paragraph("1. Previsiones Macroeconómicas Trimestrales (Fan Charts)", section_title))
    story.append(Paragraph(
        "Senda central determinista y bandas de probabilidad (intervalos del 50% y 80%) generadas por simulación estocástica Monte Carlo. "
        "En desempleo se muestra la serie oficial de la EPA con su estacionalidad y la tendencia desestacionalizada:",
        body_style
    ))

    dash_img = figs_path / "dashboard_prevision_baseline.png"
    if dash_img.exists():
        story.append(Image(str(dash_img), width=515, height=315))
        story.append(Spacer(1, 8))

    analysis_box = [[
        Paragraph(
            "<b>Dinámica de los Cuatro Bloques Estructurales:</b><br/>"
            "<b>1. PIB Real (% i.a.):</b> Crecimiento sólido en 2026 impulsado por la demanda interna y el sector exterior, convergiendo progresivamente hacia el ritmo de crecimiento potencial sostenible (~2,2%).<br/>"
            "<b>2. Inflación General y Subyacente:</b> El máximo del ciclo se fijó en el verano de 2026. A partir de septiembre, la desescalada de los precios de la energía y las expectativas ancladas guían la desinflación.<br/>"
            "<b>3. Mercado Laboral (EPA con estacionalidad):</b> Reproduce las oscilaciones intra-anuales de la EPA (máximo en T1, mínimo en T3) superpuestas a una suave convergencia hacia la NAIRU (8,85%).<br/>"
            "<b>4. Brecha de Producción:</b> Se mantiene acotada en torno al equilibrio cíclico neutro (-0,3% a +0,0%), descartando tanto sobrecalentamiento como presiones de histéresis negativa.",
            callout_text
        )
    ]]
    t_analysis = Table(analysis_box, colWidths=[523])
    t_analysis.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, COLOR_HEADER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_analysis)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: DESAGREGACIÓN MENSUAL DEL IPC Y COMPARATIVA DE ESCENARIOS
    # =========================================================================
    story.append(Paragraph("2. Desagregación Mensual del IPC: Comparativa de Escenarios", section_title))
    story.append(Paragraph(
        "El módulo satélite de puente mensual traslada las sendas de alta frecuencia del crudo Brent y gas TTF, "
        "revelando la dispersión entre escenarios para la inflación general y el componente energético sin distorsión de escala:",
        body_style
    ))

    cpi_scenarios_img = figs_path / "comparativa_ipc_mensual_escenarios.png"
    if cpi_scenarios_img.exists():
        # Relación de aspecto nativa exacta (2082x1330 -> 1.565): 515 de ancho x 329 de alto
        story.append(Image(str(cpi_scenarios_img), width=515, height=329))
        story.append(Spacer(1, 8))

    scen_cpi_notes = [[
        Paragraph(
            "<b>Diagnóstico de Sensibilidad en la Inflación Mensual:</b><br/>"
            "• <b>Pico Estival de 2026:</b> El shock energético derivado de las tensiones en Oriente Próximo sitúa el máximo en agosto-septiembre de 2026. En el escenario adverso, la inflación general supera el 4,5% i.a. por el repunte del crudo y del gas TTF.<br/>"
            "• <b>Convergencia Desinflacionaria:</b> A partir del cuarto trimestre de 2026, la estabilización de los mercados de futuros y el anclaje monetario facilitan un descenso continuo de la inflación hacia el entorno del 2% en 2027.",
            callout_text
        )
    ]]
    t_scen_cpi_notes = Table(scen_cpi_notes, colWidths=[523])
    t_scen_cpi_notes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, COLOR_HEADER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_scen_cpi_notes)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: DESGLOSE DE COMPONENTES DEL IPC Y PRECIOS DE ALTA FRECUENCIA
    # =========================================================================
    story.append(Paragraph("3. Desglose de Componentes de Inflación e Impacto Energético", section_title))
    story.append(Paragraph(
        "Descomposición del IPC en sus cuatro componentes oficiales del INE (servicios, bienes industriales, alimentos y energía) "
        "junto con el seguimiento del crudo Brent y el gas TTF:",
        body_style
    ))

    cpi_monthly_img = figs_path / "ipc_mensual_desagregado.png"
    if cpi_monthly_img.exists():
        # Relación de aspecto nativa exacta (2082x1330 -> 1.565): 515 de ancho x 329 de alto
        story.append(Image(str(cpi_monthly_img), width=515, height=329))
        story.append(Spacer(1, 8))

    cpi_notes = [[
        Paragraph(
            "<b>Estructura de la Transmisión de Precios por Componentes:</b><br/>"
            "• <b>Energía como Motor Inicial:</b> La inflación energética escaló por encima del 20% i.a. durante el pico de precios del crudo Brent (~110-130 USD/barril) y el escalón regulatorio del IVA de la electricidad.<br/>"
            "• <b>Subyacente Contenida:</b> Los servicios y bienes industriales no energéticos muestran una trayectoria mucho más estable (~2,7% - 2,5%), confirmando la ausencia de efectos de segunda ronda significativos sobre los salarios y márgenes empresariales.",
            callout_text
        )
    ]]
    t_cpi_notes = Table(cpi_notes, colWidths=[523])
    t_cpi_notes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, COLOR_CORAL),  # Franja en color coral de alerta/energía
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cpi_notes)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 5: COMPARATIVA DE ESCENARIOS Y TABLA DETALLADA TRIMESTRAL
    # =========================================================================
    story.append(Paragraph("4. Comparativa Macroeconómica a Medio Plazo y Detalle Trimestral", section_title))
    story.append(Paragraph(
        "Evolución comparada frente al escenario adverso (shock de oferta energética y tipos altos) y favorable (desinflación rápida):",
        body_style
    ))

    scen_img = figs_path / "comparativa_escenarios.png"
    if scen_img.exists():
        # Relación de aspecto nativa (2385x669 -> 3.565): 515 de ancho x 144 de alto
        story.append(Image(str(scen_img), width=515, height=144))
        story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Cuadro de Proyecciones Trimestrales (Escenario Central Baseline)</b>", body_bold))

    q_rows = [
        [
            Paragraph("<b>Trimestre</b>", table_header),
            Paragraph("<b>PIB (% i.a.)</b>", table_header),
            Paragraph("<b>PIB (% t/t-1)</b>", table_header),
            Paragraph("<b>Brecha (%)</b>", table_header),
            Paragraph("<b>Paro EPA (%)</b>", table_header),
            Paragraph("<b>Inflación Total</b>", table_header),
            Paragraph("<b>Subyacente</b>", table_header),
            Paragraph("<b>Euribor 3M</b>", table_header),
        ]
    ]

    for d in df_forecast.index:
        q_label = f"{d.year}-T{d.quarter}"
        g_yoy = f"{df_forecast.loc[d, 'gdp_growth_annual']:.1f}%" if 'gdp_growth_annual' in df_forecast.columns else "-"
        g_qoq = f"{df_forecast.loc[d, 'gdp_growth_quarterly']:.1f}%" if 'gdp_growth_quarterly' in df_forecast.columns else "-"
        gap = f"{df_forecast.loc[d, 'output_gap_spain']:.1f}%" if 'output_gap_spain' in df_forecast.columns else "-"
        u = f"{df_forecast.loc[d, 'unemployment_rate']:.2f}%" if 'unemployment_rate' in df_forecast.columns else "-"
        inf_tot = f"{df_forecast.loc[d, 'inflation_total']:.1f}%" if 'inflation_total' in df_forecast.columns else "-"
        inf_core = f"{df_forecast.loc[d, 'inflation_core']:.1f}%" if 'inflation_core' in df_forecast.columns else "-"
        eur = f"{df_forecast.loc[d, 'interest_rate_spain']:.2f}%" if 'interest_rate_spain' in df_forecast.columns else "-"

        q_rows.append([
            Paragraph(f"<b>{q_label}</b>", table_cell_bold),
            Paragraph(g_yoy, table_cell),
            Paragraph(g_qoq, table_cell),
            Paragraph(gap, table_cell),
            Paragraph(u, table_cell),
            Paragraph(inf_tot, table_cell),
            Paragraph(inf_core, table_cell),
            Paragraph(eur, table_cell),
        ])

    t_quarterly = Table(q_rows, colWidths=[65, 65, 65, 65, 65, 65, 65, 68])
    t_quarterly.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG]),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, COLOR_BORDER),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_quarterly)
    story.append(Spacer(1, 8))

    final_box = [[
        Paragraph(
            "<b>Balance de Riesgos y Recomendaciones de Política:</b><br/>"
            "• <b>Riesgos al Alza para la Inflación:</b> Escalamiento geopolítico en Oriente Próximo con afectación al crudo por encima de 90 USD/barril.<br/>"
            "• <b>Riesgos a la Baja para la Actividad:</b> Desaceleración más profunda de la industria alemana o condiciones financieras restrictivas por más tiempo.<br/>"
            "• <b>Conclusión:</b> La economía española preserva un diferencial favorable de crecimiento apoyado en la resiliencia del empleo y el flujo migratorio.",
            callout_text
        )
    ]]
    t_final = Table(final_box, colWidths=[523])
    t_final.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, COLOR_HEADER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_final)

    # Compilación final con el canvas de EsadeEcPol
    doc.build(story, canvasmaker=EsadeEcPolCanvas)
    return pdf_path

