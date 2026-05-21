"""
_generar_pdfs.py — Genera los 2 PDFs oficiales de NeuroMood V3:
  1. Manual_Usuario_Profesional_NeuroMood.pdf
  2. Manual_Tecnico_Descriptivo_NeuroMood.pdf

Usa reportlab + capturas del mockup HTML.
"""

import os, sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, Frame, PageTemplate, BaseDocTemplate,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

PROJ = Path(__file__).resolve().parent
SCREENS_DIR = PROJ / "_qa_output" / "mockup_screens"

# ══ COLORS ══
BG      = HexColor("#0f172a")
SURFACE = HexColor("#1e293b")
ELEVATED = HexColor("#334155")
ACCENT  = HexColor("#6366f1")
TEAL    = HexColor("#14b8a6")
VIOLET  = HexColor("#a855f7")
TP      = HexColor("#f1f5f9")   # text primary
TS      = HexColor("#94a3b8")   # text secondary
TM      = HexColor("#64748b")   # text muted
BORDER  = HexColor("#2a3a5c")
AMBER   = HexColor("#f59e0b")
GREEN   = HexColor("#22c55e")
RED     = HexColor("#ef4444")

PAGE_W, PAGE_H = A4  # 595.27 x 841.89

# ══ STYLES ══
styles = getSampleStyleSheet()

body_style = ParagraphStyle("nm_body", fontName="Helvetica", fontSize=10,
                            textColor=TS, leading=15, alignment=TA_JUSTIFY)

heading1 = ParagraphStyle("nm_h1", fontName="Helvetica-Bold", fontSize=20,
                          textColor=TP, spaceAfter=8, spaceBefore=12)

heading2 = ParagraphStyle("nm_h2", fontName="Helvetica-Bold", fontSize=14,
                          textColor=TEAL, spaceAfter=6, spaceBefore=14)

heading3 = ParagraphStyle("nm_h3", fontName="Helvetica-Bold", fontSize=11,
                          textColor=ACCENT, spaceAfter=4, spaceBefore=10)

caption_style = ParagraphStyle("nm_caption", fontName="Helvetica", fontSize=8,
                               textColor=TM, alignment=TA_CENTER, spaceAfter=4)

disclaimer_style = ParagraphStyle("nm_disclaimer", fontName="Helvetica-Oblique",
                                  fontSize=8, textColor=TM, alignment=TA_CENTER)

small_style = ParagraphStyle("nm_small", fontName="Helvetica", fontSize=8,
                             textColor=TM, leading=11)

accent_label = ParagraphStyle("nm_label", fontName="Helvetica-Bold", fontSize=8,
                              textColor=TEAL)

# ══ PAGE TEMPLATE (dark background) ══
class DarkBackground(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

def dark_page_template():
    """Returns a PageTemplate that draws the dark background and header/footer."""
    frame = Frame(20*mm, 18*mm, PAGE_W - 40*mm, PAGE_H - 36*mm, id="main")
    
    def on_page(canvas_obj, doc):
        # Background
        canvas_obj.setFillColor(BG)
        canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        
        # Top accent line
        canvas_obj.setFillColor(TEAL)
        canvas_obj.rect(0, PAGE_H - 3, PAGE_W, 3, fill=1, stroke=0)
        
        # Logo area
        canvas_obj.setFillColor(TEAL)
        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.drawString(20*mm, PAGE_H - 13*mm, "NeuroMood")
        
        # Version tag
        canvas_obj.setFillColor(TM)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawRightString(PAGE_W - 20*mm, PAGE_H - 13*mm, "v3.0")
        
        # Page number
        canvas_obj.setFillColor(TM)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawCentredString(PAGE_W/2, 10*mm, str(doc.page))
        
        # Disclaimer bar at bottom of every page for Usuario PDF
        if getattr(doc, "is_usuario", False):
            canvas_obj.setFillColor(HexColor("#1a2332"))
            canvas_obj.rect(0, 0, PAGE_W, 8*mm, fill=1, stroke=0)
            canvas_obj.setFillColor(TM)
            canvas_obj.setFont("Helvetica-Oblique", 6.5)
            canvas_obj.drawCentredString(
                PAGE_W/2, 2.8*mm,
                "Documento descriptivo orientativo. Las imagenes son simulaciones del mockup y no representan el producto final."
            )
    
    return PageTemplate(id="dark", frames=[frame], onPage=on_page)


def _img_or_fallback(screen_id, max_width, max_height=None):
    """Returns an Image flowable or a placeholder text if image missing."""
    img_path = SCREENS_DIR / f"{screen_id}.png"
    if img_path.exists():
        img = Image(str(img_path), width=max_width, height=max_height)
        return img
    # Fallback
    return Paragraph(
        f'<font color="#475569">[Imagen orientativa {screen_id} — pendiente de captura]</font>',
        caption_style
    )


def _section(title, body, level=2):
    """Shorthand for heading + body paragraph."""
    return [
        Paragraph(title, heading2 if level == 2 else heading3),
        Paragraph(body, body_style),
        Spacer(1, 4*mm),
    ]


def _card(items):
    """Renders a list of (label, value) pairs as a dark surface card."""
    rows = []
    for label, value in items:
        rows.append([
            Paragraph(f'<font color="{TM}">{label}</font>', small_style),
            Paragraph(f'<font color="{TS}">{value}</font>', small_style),
        ])
    t = Table(rows, colWidths=[120, 280])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), SURFACE),
        ("TEXTCOLOR", (0,0), (-1,-1), TS),
        ("ALIGN", (0,0), (0,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("LINEAFTER", (0,0), (0,-1), 0.5, HexColor("#334155")),
        ("LINEBELOW", (0,0), (-1,-1), 0.5, SURFACE),
    ]))
    return [t, Spacer(1, 3*mm)]


def _pill(text, color=None):
    """Colored pill badge text."""
    c = color or TEAL
    return f'<font color="{c}">●</font> <b>{text}</b>'


# ═══════════════════════════════════════════════════════════════════════════════════
#  PDF 1: USUARIO / PROFESIONAL
# ═══════════════════════════════════════════════════════════════════════════════════

def build_usuario_pdf():
    out = PROJ / "Manual_Usuario_Profesional_NeuroMood.pdf"
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=20*mm,
                          rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
    doc.is_usuario = True
    doc.addPageTemplates([dark_page_template()])

    story = []

    # ── COVER PAGE ──
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("NeuroMood", ParagraphStyle("cover_logo",
                        fontName="Helvetica-Bold", fontSize=36,
                        textColor=TEAL, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph("Manual para Pacientes y Profesionales",
                        ParagraphStyle("cover_sub", fontName="Helvetica", fontSize=14,
                                       textColor=TS, alignment=TA_CENTER, spaceAfter=12)))
    story.append(HRFlowable(width="40%", thickness=1, color=TEAL, spaceAfter=12))
    story.append(Paragraph(
        "Guia descriptiva de NeuroMood Suite para pacientes y "
        "NeuroMood Hub para profesionales. Incluye instalacion, "
        "modulos, uso clinico, privacidad y aviso legal.",
        ParagraphStyle("cover_desc", fontName="Helvetica", fontSize=10,
                       textColor=TM, alignment=TA_CENTER, leading=16)))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        '<font color="#ef4444">⚠</font> <i>Este documento es descriptivo y orientativo. '
        'Las imagenes son simulaciones del mockup y no representan el producto final.</i>',
        disclaimer_style))
    story.append(PageBreak())

    # ── PAGE 2: PACIENTES — NeuroMood Suite ──
    story.append(Paragraph("NeuroMood Suite para pacientes", heading1))
    story.append(Paragraph(
        "NeuroMood Suite reune herramientas breves, visuales y repetibles. "
        "Su objetivo no es exigir mas carga al paciente, sino transformar momentos "
        "cotidianos en registros utiles para el acompanamiento terapeutico. "
        "La aplicacion funciona principalmente sin conexion a internet (offline-first) "
        "y sincroniza datos cuando hay conectividad disponible.",
        body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("7 Modulos de acompanamiento",
        "Cada modulo aborda un aspecto concreto del autocuidado y la terapia: "
        "registro emocional, respiracion guiada, reestructuracion cognitiva (TCC), "
        "rutina diaria, activacion conductual, temporizador de enfoque y recordatorios.")

    # Module grid cards
    modulos = [
        ("animo", "Animo", "Registro emocional diario con escala visual, "
         "nota breve y grafico semanal de tendencias."),
        ("respiracion", "Respirar", "Guia de respiracion animada con tecnicas 4-7-8, "
         "Box 4x4 y Coherente. Incluye indicador de calma y BPM."),
        ("registro", "Registro TCC", "Registro de pensamientos en 4 pasos: "
         "situacion, pensamiento automatico, intensidad emocional y respuesta alternativa. "
         "Con deteccion automatica de distorsiones cognitivas."),
        ("rutina", "Rutina", "Checklist diario organizado por momentos del dia "
         "(Manana, Tarde, Noche) con indicadores de progreso y nota diaria."),
        ("actividades", "Actividades", "Sugerencias de activacion conductual basadas "
         "en el animo actual, filtradas por categoria y con acciones de completar/omitir."),
        ("timer", "Timer", "Temporizador de sesiones de enfoque con presets de duracion, "
         "historial diario y arco de progreso visual."),
        ("avisos", "Avisos", "Recordatorios configurables con busqueda, "
         "indicador de completados y persistencia en background."),
    ]

    for mid, mtitle, mdesc in modulos:
        story.append(Paragraph(
            f'<font color="{TEAL}">▸</font> <b>{mtitle}</b><br/>'
            f'<font color="{TM}" size="9">{mdesc}</font>',
            ParagraphStyle("mod_item", fontName="Helvetica", fontSize=10,
                           textColor=TS, leading=14, spaceAfter=6)))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("2 temas visuales: Dark Hybrid y Light Hybrid, "
        "disenados para minimizar la fatiga visual y adaptarse a la preferencia del usuario.",
        body_style))

    # ── HOME SCREEN ──
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Pantalla principal (Home)", heading3))
    story.append(_img_or_fallback("s1", 440, 280))
    story.append(Paragraph("Vista del Home con grid de modulos, saludo contextual, "
        "racha de actividad y toggle de tema oscuro/claro. Imagen orientativa del mockup.",
        caption_style))
    story.append(PageBreak())

    # ── PAGE 3+4: MODULOS EN DETALLE ──
    story.append(Paragraph("Modulos en detalle", heading2))
    story.append(Paragraph(
        "A continuacion se muestran las pantallas principales de cada modulo "
        "con su proposito clinico. Todas las imagenes son orientativas y provienen "
        "del mockup de diseno.", body_style))
    story.append(Spacer(1, 4*mm))

    # Pairs of screens with descriptions
    screens_detail = [
        ("s2", "Termometro Emocional",
         "Registro diario del estado de animo con selector visual de 5 niveles, "
         "nota contextual opcional y grafico semanal de tendencias. "
         "Permite al paciente expresar como esta en menos de 30 segundos."),
        ("s3", "Guia de Respiracion Animada",
         "Ejercicios de respiracion con ritmo visual, arco de progreso y fases "
         "claras (Inhala 4s, Manten 7s, Exhala 8s). Util para bajar activacion "
         "fisiologica antes o despues de una intervencion."),
        ("s4", "Registro de Pensamientos (TCC)",
         "Formulario guiado en 4 pasos con stepper visual, barra de intensidad "
         "emocional y deteccion automatica de distorsiones cognitivas "
         "(catastrofizacion, todo-o-nada, minimizacion, etc.)."),
        ("s5", "Checklist de Rutina Diaria",
         "Tareas organizadas por momento del dia con checkboxes, barras de progreso "
         "y nota diaria bloqueable. Refuerza adherencia y estructura sin rigidez."),
        ("s6", "Asistente de Activacion Conductual",
         "Sugerencias de actividades basadas en el animo del dia, filtradas por "
         "categoria (Fisica, Placer, Maestria, Autocuidado, Social) con acciones "
         "de completar u omitir."),
        ("s7", "Temporizador de Enfoque",
         "Sesiones cronometradas con nombre de tarea, presets de duracion "
         "y arco circular de progreso. Incluye historial de sesiones del dia."),
        ("s8", "Recordatorios (Avisos)",
         "Sistema de avisos con busqueda, indicador de progreso diario y "
         "persistencia en background. Los avisos completados se atenuan visualmente."),
    ]

    for sid, title, desc in screens_detail:
        story.append(Paragraph(title, heading3))
        story.append(_img_or_fallback(sid, 440, 270))
        story.append(Paragraph(desc, caption_style))
        story.append(Spacer(1, 3*mm))

    story.append(PageBreak())

    # ── PAGE 5: USO CLINICO ──
    story.append(Paragraph("Uso clinico", heading2))
    story.append(Paragraph(
        "NeuroMood no reemplaza el criterio profesional. Su aporte es ordenar "
        "senales entre encuentros, facilitar adherencia y dejar una huella de "
        "trabajo terapeutico mas legible.", body_style))
    story.append(Spacer(1, 3*mm))

    story += _section("Antes de la sesion",
        "El paciente registra animo, rutinas y eventos relevantes. "
        "El profesional llega a la consulta con una vista mas clara del periodo "
        "entre sesiones, reduciendo la dependencia del relato retrospectivo.")
    story += _section("Durante la sesion",
        "Los registros permiten revisar ejemplos concretos, detectar barreras, "
        "ajustar indicaciones y acordar tareas mas realistas basadas en datos "
        "semanales visibles desde NeuroMood Hub.")
    story += _section("Despues de la sesion",
        "Recordatorios, checklist y temporizadores ayudan a sostener la intervencion "
        "en el contexto cotidiano del paciente, reforzando lo trabajado en consulta.")
    story += _section("Seguimiento profesional",
        "NeuroMood Hub permite observar evolucion, revisar patrones y mantener "
        "una lectura organizada del proceso. El profesional puede habilitar o "
        "bloquear modulos segun el plan terapeutico.")

    # ── PAGE 6: NEUROMOOD HUB ──
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("NeuroMood Hub para profesionales", heading1))
    story.append(Paragraph(
        "NeuroMood Hub centraliza la supervision de pacientes, la lectura de "
        "evolucion clinica, la asistencia contextual con IA y la configuracion "
        "del sistema. Esta disenado para equipos que necesitan informacion clara "
        "sin pantallas sobrecargadas.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("Pacientes",
        "Lista con busqueda, filtros por actividad, estado de sincronizacion y "
        "acceso rapido al detalle clinico de cada persona. Incluye indicadores "
        "de adherencia con anillos de progreso.")
    story.append(_img_or_fallback("s9", 440, 260))
    story.append(Paragraph("Lista de pacientes en NeuroMood Hub. Imagen orientativa.", caption_style))

    story += _section("Dashboard",
        "Lectura visual por paciente con puntaje de animo promedio, tendencia "
        "semanal, modulos activos con progreso, actividad reciente en linea de "
        "tiempo y etiquetas clinicas configuradas por el profesional.")
    story.append(_img_or_fallback("s10", 440, 280))
    story.append(Paragraph("Dashboard de paciente con metricas clave. Imagen orientativa.", caption_style))

    story += _section("IA Asistente",
        "Apoyo para ordenar informacion clinica, preparar preguntas para la sesion "
        "o sintetizar contexto del paciente. Utiliza el modelo Llama 3 mediante "
        "Groq. No reemplaza el juicio profesional; es una herramienta de consulta.")
    story += _section("Configuracion",
        "Panel con estado de conexion Supabase, configuracion de tema visual, "
        "selector de proveedor IA y log de sincronizacion en tiempo real.")

    story.append(PageBreak())

    # ── PAGE 7: INSTALADORES ──
    story.append(Paragraph("Instaladores", heading1))
    story.append(Paragraph(
        "La instalacion se presenta como un flujo guiado con pasos visibles, "
        "validacion de cuenta, consentimiento legal y mensajes claros. "
        "El objetivo es que el paciente entienda que instala, que acepta y "
        "como retirarlo.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("Instalador Suite",
        "Instala NeuroMood Suite con Wizard de 5 pasos: Bienvenida, "
        "Cuenta (Supabase Auth), Consentimiento legal, Instalacion y "
        "Finalizacion. Incluye acceso directo en escritorio y menu inicio.")
    story.append(_img_or_fallback("s13", 440, 270))
    story.append(Paragraph("Instalador Suite con Wizard de 5 pasos. Imagen orientativa.", caption_style))

    story += _section("Instalador Hub Pro",
        "Instala NeuroMood Hub con Wizard de 6 pasos que incluye configuracion "
        "de credenciales Supabase del consultorio. Validacion de conexion en "
        "tiempo real antes de instalar.")

    story += _section("Desinstalador Suite",
        "Wizard de 3 pasos que permite retirar la aplicacion de forma limpia. "
        "Ofrece la opcion de conservar los datos clinicos en una ubicacion segura "
        "antes de eliminar los archivos (recomendado si se planea reinstalar).")
    story.append(_img_or_fallback("s15", 440, 260))
    story.append(Paragraph("Desinstalador con opcion de conservar datos. Imagen orientativa.", caption_style))

    story.append(PageBreak())

    # ── PAGE 8: PRIVACIDAD + DISCLAIMER LEGAL ──
    story.append(Paragraph("Privacidad y seguridad", heading1))
    story.append(Paragraph(
        "La informacion de salud requiere un trato cuidadoso. NeuroMood esta "
        "disenado para registrar lo necesario, sincronizar con control y evitar "
        "exponer datos tecnicos al usuario final.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("Cuenta y autenticacion",
        "El acceso se realiza mediante email y contrasena a traves de Supabase Auth. "
        "Las contrasenas se protegen con PBKDF2-SHA256 (100,000 iteraciones) y "
        "nunca se almacenan en texto plano. Cada instalacion utiliza una sal "
        "criptografica unica basada en el codigo de instalacion.")
    story += _section("Datos locales",
        "NeuroMood Suite almacena datos en el equipo del paciente (SQLite en "
        "AppData) para funcionar sin conexion. La informacion permanece privada "
        "y solo se sincroniza con Supabase cuando el paciente tiene conectividad.")
    story += _section("Sincronizacion",
        "La sincronizacion con Supabase es incremental (ultimas 48 horas) y "
        "completa cada 7 dias. Los datos se transmiten cifrados. El profesional "
        "accede solo a la informacion de sus pacientes asignados mediante "
        "Row Level Security (RLS).")
    story += _section("Permisos de modulos",
        "NeuroMood Hub permite al profesional habilitar o bloquear modulos "
        "especificos segun el plan terapeutico. La configuracion inicial "
        "mantiene todos los modulos desbloqueados por defecto.")

    # LEGAL DISCLAIMER
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Aviso Legal y Consentimiento", heading2))
    story.append(Paragraph(
        '<font color="#f59e0b">⚠ Importante:</font> NeuroMood Suite es una '
        'herramienta complementaria de bienestar y acompanamiento terapeutico. '
        '<b>No es un dispositivo medico ni sustituye el diagnostico, tratamiento '
        'o criterio de un profesional de la salud.</b>',
        body_style))
    story.append(Spacer(1, 3*mm))

    legal_items = [
        ("Naturaleza de la aplicacion",
         "NeuroMood Suite es una herramienta de apoyo al bienestar emocional. "
         "No diagnostica, trata ni previene enfermedades. Ante cualquier urgencia "
         "o crisis, el usuario debe contactar a su profesional tratante o a los "
         "servicios de emergencia correspondientes."),
        ("Consentimiento informado",
         "Durante la instalacion, el paciente acepta explicitamente un aviso legal "
         "completo (marcando una casilla obligatoria). Este consentimiento queda "
         "registrado localmente y en Supabase con firma de version, timestamp UTC "
         "y alcance detallado de los permisos otorgados."),
        ("Alcance del consentimiento",
         "Base de datos local, sincronizacion autorizada, revision profesional "
         "desde NeuroMood Hub, visualizacion de datos por el profesional asignado "
         "y asistencia IA para el profesional. Cada alcance es auditable."),
        ("Versionado del consentimiento",
         "Cada aceptacion queda vinculada a una version especifica del documento "
         "legal. Si el aviso legal se actualiza, el sistema solicitara una nueva "
         "aceptacion al paciente en la siguiente apertura de la aplicacion."),
        ("Derechos del usuario",
         "El paciente puede solicitar la eliminacion de sus datos en cualquier "
         "momento. El desinstalador permite conservar o eliminar los registros "
         "locales. Los datos en Supabase se eliminan segun la politica de "
         "privacidad del consultorio."),
        ("Uso responsable",
         "Los registros son apoyo para la conversacion clinica. No deben usarse "
         "como unico criterio de decision terapeutica. Ante senales de riesgo, "
         "el profesional debe activar los protocolos asistenciales habituales."),
    ]

    for title, desc in legal_items:
        story.append(Paragraph(
            f'<font color="{TEAL}">▸</font> <b>{title}</b><br/>'
            f'<font color="{TM}" size="9">{desc}</font>',
            ParagraphStyle("legal_item", fontName="Helvetica", fontSize=10,
                           textColor=TS, leading=14, spaceAfter=7)))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        '<i>Version del aviso legal: legal-2026-05-16. Version de privacidad: privacy-2026-05-16. '
        'Consulte a su profesional para mas informacion sobre el tratamiento de sus datos.</i>',
        disclaimer_style))

    # Build
    doc.build(story)
    print(f"  PDF Usuario/Profesional: {out} ({os.path.getsize(out)//1024} KB)")


# ═══════════════════════════════════════════════════════════════════════════════════
#  PDF 2: TECNICO
# ═══════════════════════════════════════════════════════════════════════════════════

def build_tecnico_pdf():
    out = PROJ / "Manual_Tecnico_Descriptivo_NeuroMood.pdf"
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=20*mm,
                          rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
    doc.is_usuario = False
    doc.addPageTemplates([dark_page_template()])

    story = []

    # ── COVER ──
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("NeuroMood", ParagraphStyle("cov_logo2",
                        fontName="Helvetica-Bold", fontSize=36,
                        textColor=TEAL, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph("Manual Tecnico Descriptivo",
                        ParagraphStyle("cov_sub2", fontName="Helvetica", fontSize=14,
                                       textColor=TS, alignment=TA_CENTER, spaceAfter=12)))
    story.append(HRFlowable(width="40%", thickness=1, color=TEAL, spaceAfter=12))
    story.append(Paragraph(
        "Arquitectura, diseno, seguridad, autenticacion, sincronizacion, "
        "componentes, build, QA y distribucion de NeuroMood V3.",
        ParagraphStyle("cov_desc2", fontName="Helvetica", fontSize=10,
                       textColor=TM, alignment=TA_CENTER, leading=16)))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Documento orientado a desarrolladores, equipo tecnico y responsables de operacion. "
        "Centraliza criterios de arquitectura, seguridad, build y QA para mantener "
        "una entrega reproducible y segura.",
        disclaimer_style))
    story.append(PageBreak())

    # ── ARQUITECTURA ──
    story.append(Paragraph("Arquitectura del proyecto", heading1))
    story.append(Paragraph(
        "NeuroMood V3 se organiza como dos aplicaciones PyQt6 de escritorio, "
        "componentes compartidos, instaladores propios y scripts de automatizacion.", body_style))
    story.append(Spacer(1, 4*mm))

    arch_items = [
        ("app/", "Suite del paciente. Entry point: app/main_qt.py. "
         "Carga Home y siete modulos funcionales con sus vistas."),
        ("hub/", "NeuroMood Hub para profesionales. Entry point: hub/main_qt.py. "
         "Incluye pacientes, dashboard, IA asistente y configuracion."),
        ("shared/", "Design system, componentes Qt (54 widgets), config, DB local, "
         "sincronizacion, identidad (PBKDF2), helpers y fixtures visuales de QA."),
        ("installers/", "Instaladores y desinstaladores PyQt6 con wizard visual, "
         "auth Supabase y limpieza de instalacion. Clase base: InstallerShell."),
        ("AI_SCRIPTS/", "Build oficial, QA automatizado, capturas de pantalla, "
         "auditorias visuales y utilidades para agentes IA."),
        ("dist/", "Salida de EXEs oficiales compilados con PyInstaller. "
         "Se conserva; build/ y specs/ son temporales y se eliminan tras compilar."),
    ]

    for folder, desc in arch_items:
        story.append(Paragraph(
            f'<font color="{ACCENT}"><b>{folder}</b></font>  '
            f'<font color="{TM}" size="9">{desc}</font>',
            ParagraphStyle("arch", fontName="Helvetica", fontSize=10,
                           textColor=TS, leading=15, spaceAfter=5)))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Documentacion centralizada en AI_PROJECT_CONTEXT.md. Este archivo es la "
        "fuente unica de contexto para agentes IA y desarrolladores.", body_style))
    story.append(PageBreak())

    # ── DESIGN SYSTEM ──
    story.append(Paragraph("Design System y Componentes", heading1))
    story.append(Paragraph(
        "El sistema de diseno utiliza tokens centralizados en shared/theme_qt.py "
        "y 54 componentes reutilizables en shared/components_qt.py. Ambos temas "
        "(dark_hybrid y light_hybrid) comparten los mismos tokens con valores "
        "adaptados por modo.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("Tokens de diseno",
        "Colores (C(key, modo)), tipografia (qfont, nm_font), espaciado (sp), "
        "radios (RADIUS_CARD, RADIUS_BUTTON, etc.), sombras (shadow_effect), "
        "gradientes (linear_gradient, rich_gradient) y paleta (app_palette). "
        "Todos los valores estan tokenizados: no se usan colores hardcodeados "
        "en la UI.")

    story += _section("Tipografia",
        "DM Sans como fuente principal, JetBrains Mono para datos tecnicos y tiempos. "
        "Escala tipografica: display (28pt), h1 (22pt), h2 (18pt), h3 (15pt), "
        "body (13pt), small (12pt), caption (11pt).")

    story += _section("Componentes principales (54 widgets)",
        "NMButton, NMButtonOutline, NMCard, NMInput, NMToggle, NMToast, "
        "NMSidebar, NMHeader, NMFadeWidget, NMModule (base), NMSkeleton, "
        "NMProgressBar, NMEmptyState, NMStatusChip, NMSectionCard, NMFormField, "
        "NMSegmentedChoice, NMCustomCheck, NMHubSidebar, NMPatientRow, "
        "NMModuleRing, NMFeaturedCard, NMChatBubble, NMTypingDots, "
        "NMProviderChip, NMQuickAction, NMPatientContext, NMSyncOrb, "
        "NMSettingsSection, NMInstallStepper, NMInstallProgress, "
        "NMDataPreserveCard, entre otros.")

    story += _section("Temas visuales",
        "Dark Hybrid (#0f172a de fondo principal) como experiencia primaria. "
        "Light Hybrid (#f8fafc) como alternativa funcional. El cambio de tema "
        "es instantaneo mediante ThemeManager (singleton con senal theme_changed).")

    story += _section("Sistema de iconos",
        "Los iconos usan QtAwesome (FontAwesome 5 Solid) mediante la funcion "
        "nm_icon(). MODULE_ICONS mapea cada modulo a su icono vectorial. "
        "No se usan emojis como iconos principales en la interfaz.")
    story.append(PageBreak())

    # ── SEGURIDAD ──
    story.append(Paragraph("Seguridad y Autenticacion", heading1))
    story.append(Paragraph(
        "La seguridad se implementa en multiples capas: hashing de contrasenas, "
        "cifrado en transito, Row Level Security en Supabase y consentimiento "
        "legal versionado.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("PBKDF2-SHA256",
        "Las contrasenas se protegen con PBKDF2-SHA256 (100,000 iteraciones, "
        "32 bytes de clave). La sal criptografica es el codigo de instalacion "
        "(install_code), unico por instalacion. Esto hace que cada hash sea "
        "diferente incluso para la misma contrasena en distintos equipos. "
        "Las contrasenas en texto plano existentes se migran automaticamente "
        "al primer acceso (_is_hashed + auto-migracion).")

    story += _section("Supabase Auth",
        "La autenticacion de pacientes usa Supabase Auth con email y contrasena. "
        "El instalador incluye flujo completo de sign_in, sign_up y "
        "reset_password_for_email. No se usa service_role en builds distribuidos. "
        "El archivo .env solo contiene la clave anonima publica.")

    story += _section("Row Level Security (RLS)",
        "Supabase aplica RLS en las tablas clinicas principales. El profesional "
        "solo accede a datos de pacientes que le pertenecen. La tabla "
        "legal_consents permite insert autenticado y select anonimo para "
        "verificacion desde NeuroMood Hub.")

    story += _section("Consentimiento legal versionado",
        "El consentimiento legal se almacena con hash de version "
        "(legal-2026-05-16, privacy-2026-05-16). Si las versiones cambian, "
        "el sistema solicita re-aceptacion. Los consentimientos se registran "
        "localmente (legal_consent.json) y remotamente (tabla legal_consents "
        "con user_id, accepted_at_utc, version hashes y consent_scope).")

    story += _section("Zonas sensibles (no modificar sin revision)",
        "shared/db.py, shared/sync.py, shared/config.py, shared/identidad.py. "
        "Estos archivos contienen logica de base de datos, sincronizacion, "
        "configuracion y autenticacion. Cualquier cambio debe validarse con "
        "pruebas reales y revision de manejo de errores.")
    story.append(PageBreak())

    # ── DATOS Y SYNC ──
    story.append(Paragraph("Datos, Sincronizacion y Permisos", heading1))
    story.append(Paragraph(
        "El modelo de datos combina almacenamiento local SQLite, sincronizacion "
        "incremental con Supabase y control profesional de modulos. "
        "El sistema funciona offline-first y sincroniza cuando hay conectividad.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("SQLite local",
        "shared/db.py gestiona la base de datos local en %APPDATA%/NeuroMood/nm_data.db. "
        "Almacena registros de animo, sesiones de respiracion, pensamientos TCC, "
        "checklist, timer, avisos, configuracion y datos de identidad del paciente.")

    story += _section("Sincronizacion incremental",
        "Exporta datos de las ultimas 48 horas en cada guardado (sync_inmediato). "
        "Sincronizacion completa cada 7 dias (sync_al_abrir). Importa tareas "
        "asignadas, recordatorios, permisos y actividades desde Supabase. "
        "Usa upsert con claves compuestas para evitar duplicados.")

    story += _section("Permisos de modulos",
        "La instalacion parte con todos los modulos desbloqueados. "
        "NeuroMood Hub puede bloquear modulos especificos mediante la tabla "
        "de permisos. Los permisos desde la nube tienen prioridad sobre los locales "
        "cuando estan explicitamente en False.")

    story += _section("Manejo de errores de red",
        "Auth y sync fallan con mensajes elegantes (NMToast), sin crash de la "
        "aplicacion y con opcion de reintento. La aplicacion es plenamente "
        "funcional sin conexion. El cliente Supabase se inicializa con lazy loading "
        "y retorna None si no hay conectividad, sin lanzar excepciones.")

    # ── BUILD ──
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Build y Distribucion", heading1))
    story.append(Paragraph(
        "La compilacion se centraliza en un unico script BAT que delega a un "
        "script Python mantenible. El proceso es reproducible y genera 6 EXEs.", body_style))

    story += _section("Comando oficial",
        "BUILD_NEUROMOOD.bat compila Suite, NeuroMood Hub, desinstaladores "
        "e instaladores. Soporta flags: --dry-run (validacion sin compilar), "
        "--clean (cache limpio de PyInstaller).")

    story += _section("Artefactos generados (dist/)",
        "NeuroMood Suite.exe, NeuroMood Hub Pro.exe, "
        "Instalador NeuroMood Suite.exe, Desinstalador NeuroMood.exe, "
        "Instalador NeuroMood Hub Pro.exe, Desinstalador NeuroMood Hub Pro.exe. "
        "Compilacion onedir por defecto para arranque rapido.")

    story += _section("Script interno",
        "AI_SCRIPTS/build_neuromood.py contiene targets, hidden imports "
        "(matplotlib, etc.), add-data, preflight y limpieza post-build. "
        "Usa --log-level WARN para PyInstaller. Sin supresion de output (>nul).")

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("QA y Operacion", heading1))
    story.append(Paragraph(
        "El sistema de QA incluye compilacion, smoke tests, auditorias visuales, "
        "verificacion de EXEs y capturas automatizadas. Todos los scripts viven "
        "en AI_SCRIPTS/ y la raiz del proyecto.", body_style))
    story.append(Spacer(1, 4*mm))

    story += _section("Compile Check",
        "python -m compileall . sobre app/, hub/, shared/, installers/. "
        "Debe pasar sin errores antes de cualquier commit o build.")

    story += _section("Smoke Tests (smoke_test_runner.py)",
        "Recorre todos los modulos de la Suite (31 tests) y del Hub (16 tests), "
        "capturando pantallas en dark y light. Usa QTest para navegacion "
        "automatizada sin interaccion manual.")

    story += _section("QA Full Suite (qa_full_suite.py)",
        "Suite completa con 9 etapas: Compile, Patient Smoke, Hub Smoke, "
        "Visual Components, Home View, Responsive, Resize, Color Regression, "
        "Visual Audit y EXE Verification. Genera reporte JSON en _qa_output/.")

    story += _section("Auditorias visuales",
        "Scripts _test_visual_auto.py, _test_home_auto.py, "
        "_test_responsive_final.py, _test_color_regression.py y resize_test.py "
        "cubren componentes, layout, responsive y regresion de color.")

    story += _section("Capturas de mockup",
        "_capture_mockup.py genera 15 screenshots del mockup HTML oficial "
        "usando Chrome headless. Las imagenes se usan en la documentacion "
        "como referencia visual orientativa.")

    story += _section("Checklist pre-distribucion",
        "1. Compilar con BUILD_NEUROMOOD.bat. "
        "2. Verificar los 6 EXEs en dist/. "
        "3. Ejecutar smoke_test_runner.py --app patient y --app hub. "
        "4. Probar dark/light en ambas apps. "
        "5. Ejecutar instalador y desinstalador Suite. "
        "6. Confirmar que no quedan procesos abiertos ni carpetas temporales.")

    # ── COMPONENTES DE INSTALADORES ──
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Arquitectura de Instaladores", heading2))
    story.append(Paragraph(
        "Los 4 instaladores comparten la clase base InstallerShell "
        "(shared/installer_common.py) que proporciona header, footer, "
        "stepper de pasos, transiciones fade y manejo de errores unificado. "
        "Cada instalador personaliza pasos, colores de marca y logica especifica.", body_style))
    story.append(Spacer(1, 3*mm))

    installer_table = [
        ("Instalador Suite", "5 pasos, tema teal, auth Supabase obligatorio, "
         "consentimiento legal versionado, atajos de escritorio."),
        ("Instalador Hub Pro", "6 pasos, tema violeta, configuracion de "
         "credenciales Supabase del consultorio, verificacion de conexion."),
        ("Desinstalador Suite", "3 pasos, tema sobrio con alerta roja, "
         "opcion de conservar datos clinicos (NMDataPreserveCard)."),
        ("Desinstalador Hub Pro", "3 pasos, tema violeta, preservacion de "
         "configuracion y datos del profesional."),
    ]
    for inst, desc in installer_table:
        story.append(Paragraph(
            f'<font color="{TEAL}">▸</font> <b>{inst}</b>: {desc}',
            ParagraphStyle("inst_item", fontName="Helvetica", fontSize=9,
                           textColor=TS, leading=13, spaceAfter=5)))

    story.append(PageBreak())

    # ── STACK TECNOLOGICO ──
    story.append(Paragraph("Stack Tecnologico", heading1))
    
    stack = [
        ("Lenguaje", "Python 3.12"),
        ("Framework UI", "PyQt6 (Qt 6.x)"),
        ("Base de datos local", "SQLite (via sqlite3)"),
        ("Backend cloud", "Supabase (PostgreSQL + Auth + RLS)"),
        ("Hashing", "PBKDF2-SHA256 (hashlib, 100k iteraciones)"),
        ("Iconos", "QtAwesome (FontAwesome 5 Solid)"),
        ("Compilacion", "PyInstaller (onedir)"),
        ("QA automatizado", "QTest + Pillow + Chrome headless"),
        ("Tipografia UI", "DM Sans (principal), JetBrains Mono (datos), Segoe UI (fallback)"),
        ("IA en Hub", "Groq API (modelo Llama 3 70B)"),
        ("Build system", "BAT + Python (AI_SCRIPTS/build_neuromood.py)"),
        ("ReportLab", "Generacion de PDFs de documentacion"),
    ]

    for label, value in stack:
        story.append(Paragraph(
            f'<font color="{ACCENT}"><b>{label}</b></font>: '
            f'<font color="{TS}">{value}</font>',
            ParagraphStyle("stack", fontName="Helvetica", fontSize=10,
                           textColor=TS, leading=15, spaceAfter=4)))

    story.append(Spacer(1, 8*mm))

    # ── REGLAS DE SEGURIDAD FINALES ──
    story.append(Paragraph("Reglas de seguridad operativa", heading2))
    rules = [
        "No hardcodear colores, paddings, fuentes, secretos, IDs, rutas clinicas o claves.",
        "No incluir service_role de Supabase en builds distribuidos.",
        "No mostrar URL/API key reales en la interfaz del Hub ni en logs visibles.",
        "No modificar shared/db.py, shared/sync.py, shared/config.py, shared/identidad.py sin revision.",
        "No duplicar documentacion; actualizar AI_PROJECT_CONTEXT.md.",
        "Mantener los EXEs de Suite y NeuroMood Hub como unicas apps del ecosistema.",
        "No empaquetar .env con contenido real en builds publicos (solo plantilla).",
    ]
    for r in rules:
        story.append(Paragraph(
            f'<font color="{RED}">▸</font> {r}',
            ParagraphStyle("rule", fontName="Helvetica", fontSize=9,
                           textColor=TS, leading=14, spaceAfter=3)))

    # Build
    doc.build(story)
    print(f"  PDF Tecnico: {out} ({os.path.getsize(out)//1024} KB)")


# ═══════════════════════════════════════════════════════════════════════════════════

def main():
    print("Generando PDFs de NeuroMood V3...")
    build_usuario_pdf()
    build_tecnico_pdf()
    print("Listo. Ambos PDFs actualizados en la raiz del proyecto.")

if __name__ == "__main__":
    main()
