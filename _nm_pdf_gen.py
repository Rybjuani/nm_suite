"""
_nm_pdf_gen.py  —  NeuroMood Suite · PDF Documentation Generator
Uso: python _nm_pdf_gen.py
Requiere: capturas en ./_doc_screenshots/
Salida: NeuroMood_Suite_Manual.pdf
"""
import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Image, Table, TableStyle,
    Flowable, KeepTogether, NextPageTemplate, PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE   = os.path.dirname(os.path.abspath(__file__))
SS_DIR = os.path.join(BASE, "_doc_screenshots")
OUTPUT = os.path.join(BASE, "NeuroMood_Suite_Manual.pdf")
LOGO   = os.path.join(BASE, "LOGO.png")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 55, 55, 70, 55
CW = PAGE_W - ML - MR
CH = PAGE_H - MT - MB

NAVY      = HexColor('#0B1928')
NAVY_SEC  = HexColor('#0D2137')
TEAL      = HexColor('#1EC8D4')
TEAL_D    = HexColor('#0BA8B5')
WHITE     = HexColor('#FFFFFF')
DARK_TEXT = HexColor('#12253A')
MED_TEXT  = HexColor('#3A5570')
LIGHT     = HexColor('#8BA4BE')
BORDER_C  = HexColor('#1A3050')
ROW_BG    = HexColor('#F2F6FA')
SEP       = HexColor('#DDE8F2')

F = {"r": "Helvetica", "b": "Helvetica-Bold", "i": "Helvetica-Oblique"}


def _reg_fonts():
    fd = "C:/Windows/Fonts"
    try:
        pdfmetrics.registerFont(TTFont("SUI",  os.path.join(fd, "segoeui.ttf")))
        pdfmetrics.registerFont(TTFont("SUIB", os.path.join(fd, "segoeuib.ttf")))
        pdfmetrics.registerFont(TTFont("SUII", os.path.join(fd, "segoeuii.ttf")))
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily("SUI", normal="SUI", bold="SUIB", italic="SUII")
        F["r"] = "SUI"; F["b"] = "SUIB"; F["i"] = "SUII"
    except Exception:
        pass


S = {}


def _build_styles():
    S["body"]   = ParagraphStyle("body",   fontName=F["r"], fontSize=10.5, textColor=DARK_TEXT, leading=16, spaceAfter=4)
    S["bold"]   = ParagraphStyle("bold",   fontName=F["b"], fontSize=10.5, textColor=DARK_TEXT, leading=16)
    S["head"]   = ParagraphStyle("head",   fontName=F["b"], fontSize=12,   textColor=TEAL_D,    spaceBefore=10, spaceAfter=4)
    S["cap"]    = ParagraphStyle("cap",    fontName=F["i"], fontSize=9,    textColor=LIGHT,     alignment=TA_CENTER, spaceAfter=4)
    S["step_n"] = ParagraphStyle("step_n", fontName=F["b"], fontSize=10.5, textColor=TEAL_D)
    S["step_t"] = ParagraphStyle("step_t", fontName=F["r"], fontSize=10.5, textColor=DARK_TEXT, leading=16)
    S["req_l"]  = ParagraphStyle("req_l",  fontName=F["b"], fontSize=10,   textColor=MED_TEXT)
    S["req_v"]  = ParagraphStyle("req_v",  fontName=F["r"], fontSize=10,   textColor=DARK_TEXT, leading=14)
    S["note"]   = ParagraphStyle("note",   fontName=F["i"], fontSize=9.5,  textColor=MED_TEXT,  leading=14)


# ── Page callbacks ─────────────────────────────────────────────────────────

def _on_cover(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, PAGE_H - 5, PAGE_W, 5, fill=1, stroke=0)

    if os.path.exists(LOGO):
        try:
            pil = PILImage.open(LOGO)
            lw = 210
            lh = lw * pil.height / pil.width
            c.drawImage(LOGO, (PAGE_W - lw) / 2, PAGE_H / 2 + 85,
                        width=lw, height=lh, preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    c.setFont(F["b"], 36)
    c.setFillColor(WHITE)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 32, "Manual de Usuario")

    c.setStrokeColor(TEAL)
    c.setLineWidth(2.5)
    c.line(90, PAGE_H / 2 + 14, PAGE_W - 90, PAGE_H / 2 + 14)

    c.setFont(F["r"], 16)
    c.setFillColor(TEAL)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 8, "Suite de Herramientas Terapéuticas")

    c.setFont(F["r"], 11)
    c.setFillColor(LIGHT)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 32,
                        "Documentación de uso para pacientes y profesionales")

    c.setFont(F["r"], 10)
    c.setFillColor(HexColor('#3A5570'))
    c.drawCentredString(PAGE_W / 2, 52, "neuromood.com.ar  ·  Dra. Lucía Fazzito  ·  2026")

    c.setFillColor(TEAL)
    c.rect(0, 0, PAGE_W, 4, fill=1, stroke=0)
    c.restoreState()


def _on_content(c, doc):
    c.saveState()
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.5)
    c.line(ML, PAGE_H - 46, PAGE_W - MR, PAGE_H - 46)
    c.setFont(F["r"], 8.5)
    c.setFillColor(LIGHT)
    c.drawString(ML, PAGE_H - 38, "NeuroMood Suite  —  Manual de Usuario")
    c.drawRightString(PAGE_W - MR, PAGE_H - 38, "neuromood.com.ar")
    c.setStrokeColor(HexColor('#DDE8F2'))
    c.setLineWidth(1)
    c.line(ML, 38, PAGE_W - MR, 38)
    c.setFont(F["r"], 8.5)
    c.setFillColor(LIGHT)
    c.drawCentredString(PAGE_W / 2, 27, str(doc.page - 1))
    c.restoreState()


# ── SectionHeader flowable ─────────────────────────────────────────────────

class SectionHeader(Flowable):
    H = 54

    def __init__(self, title, subtitle=""):
        super().__init__()
        self.title    = title
        self.subtitle = subtitle
        self.width    = CW
        self.height   = self.H

    def wrap(self, aW, aH):
        return (self.width, self.height)

    def split(self, aW, aH):
        return []

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY_SEC)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        c.setFont(F["b"], 16)
        c.setFillColor(WHITE)
        c.drawString(18, self.height - 24, self.title)
        if self.subtitle:
            c.setFont(F["r"], 10)
            c.setFillColor(TEAL)
            c.drawString(18, 11, self.subtitle)


# ── Helpers ────────────────────────────────────────────────────────────────

def _bordered_img(path, dw, dh):
    img = Image(path, width=dw, height=dh)
    return Table(
        [[img]],
        colWidths=[dw + 2], rowHeights=[dh + 2],
        style=TableStyle([
            ("BOX",           (0, 0), (-1, -1), 1, BORDER_C),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]),
    )


def _centered_img(path, max_w=None, caption=None):
    if max_w is None:
        max_w = CW
    flowables = []
    if not os.path.exists(path):
        flowables.append(Paragraph("[Captura no disponible]", S["cap"]))
        return flowables
    pil = PILImage.open(path)
    dw = min(float(max_w), float(pil.width))
    dh = dw * pil.height / pil.width
    bordered = _bordered_img(path, dw, dh)
    outer = Table(
        [[bordered]],
        colWidths=[CW],
        style=TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]),
    )
    flowables.append(outer)
    if caption:
        flowables.append(Spacer(1, 4))
        flowables.append(Paragraph(caption, S["cap"]))
    return flowables


def _steps(items, bold_first=False):
    rows = []
    for i, text in enumerate(items, 1):
        body = f"<b>{text.split('—')[0]}</b>" + ("—" + "—".join(text.split("—")[1:]) if "—" in text else "") if bold_first else text
        rows.append(
            Table(
                [[Paragraph(f"{i}.", S["step_n"]),
                  Paragraph(text, S["step_t"])]],
                colWidths=[22, CW - 22],
                style=TableStyle([
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                ]),
            )
        )
    return rows


def _req_table(rows):
    data = []
    ts   = []
    for i, (label, val) in enumerate(rows):
        data.append([
            Paragraph(label, S["req_l"]),
            Paragraph(val,   S["req_v"]),
        ])
        bg = ROW_BG if i % 2 == 0 else WHITE
        ts += [
            ("BACKGROUND", (0, i), (-1, i), bg),
            ("TOPPADDING",    (0, i), (-1, i), 7),
            ("BOTTOMPADDING", (0, i), (-1, i), 7),
            ("LEFTPADDING",   (0, i), (-1, i), 10),
            ("RIGHTPADDING",  (0, i), (-1, i), 6),
            ("LINEBELOW",     (0, i), (-1, i), 0.5, SEP),
        ]
    ts += [
        ("BOX", (0, 0), (-1, -1), 1, SEP),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    return Table(data, colWidths=[CW * 0.38, CW * 0.62],
                 style=TableStyle(ts))


# ── Section builders ───────────────────────────────────────────────────────

def _build_requirements():
    fl = [
        SectionHeader("Requisitos del Sistema",
                      "Compatibilidad y especificaciones mínimas recomendadas"),
        Spacer(1, 16),
        Paragraph(
            "Especificaciones técnicas necesarias para ejecutar NeuroMood Suite "
            "correctamente en tu computadora.",
            S["body"],
        ),
        Spacer(1, 14),
        _req_table([
            ("Sistema operativo",   "Windows 10 / Windows 11 (64 bits)"),
            ("Espacio en disco",    "200 MB libres mínimo para la instalación completa"),
            ("Memoria RAM",         "4 GB o más (recomendado 8 GB)"),
            ("Resolución de pantalla", "1280 × 720 px mínimo"),
            ("Permisos",            "Cuenta de usuario estándar — no requiere administrador"),
            ("Conexión a internet", "No requerida una vez instalada la suite"),
            ("Dependencias",        "El instalador incluye todas las librerías necesarias"),
        ]),
        Spacer(1, 20),
        Paragraph("Nota de compatibilidad", S["head"]),
        Paragraph(
            "Todas las herramientas funcionan en Windows 10 y Windows 11. En Windows 11, "
            "la barra de título de cada ventana muestra el color corporativo navy de NeuroMood. "
            "En Windows 10, la barra adopta el color del tema oscuro del sistema operativo.",
            S["body"],
        ),
    ]
    return fl


def _build_installer():
    fl = [
        SectionHeader("Instalación Paso a Paso",
                      "Cómo instalar NeuroMood Suite en tu computadora"),
        Spacer(1, 14),
        Paragraph(
            "El instalador de NeuroMood Suite es un asistente guiado de 4 pasos que configura "
            "todas las herramientas seleccionadas, crea accesos directos y registra la suite "
            "en el panel de control de Windows para una desinstalación limpia.",
            S["body"],
        ),
        Spacer(1, 16),
    ]

    p0 = os.path.join(SS_DIR, "installer_p0.png")
    p1 = os.path.join(SS_DIR, "installer_p1.png")
    ss_w = (CW - 14) / 2

    cells = []
    for path, cap in [(p0, "Paso 1 — Bienvenida"), (p1, "Paso 2 — Selección de apps")]:
        if os.path.exists(path):
            pil = PILImage.open(path)
            dh  = ss_w * pil.height / pil.width
            b   = _bordered_img(path, ss_w, dh)
            cell = Table(
                [[b], [Paragraph(cap, S["cap"])]],
                colWidths=[ss_w + 2],
                style=TableStyle([
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                ]),
            )
        else:
            cell = Paragraph(f"[{cap}]", S["cap"])
        cells.append(cell)

    if len(cells) == 2:
        fl.append(
            Table(
                [cells],
                colWidths=[ss_w + 2, ss_w + 2],
                style=TableStyle([
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (0,  -1), 14),
                ]),
            )
        )
        fl.append(Spacer(1, 18))

    fl.append(Paragraph("Pasos de instalación", S["head"]))
    steps = [
        "<b>Ejecutá el instalador</b> — Hacé doble clic en NM_Installer.exe. Si Windows solicita permiso UAC, hacé clic en Sí para continuar.",
        "<b>Seleccioná las aplicaciones</b> — Elegí cuáles herramientas instalar. El Visualizador de Evolución requiere el Termómetro Emocional: seleccionar uno activa el otro automáticamente.",
        "<b>Elegí la carpeta de instalación</b> — La carpeta predeterminada es C:\\Users\\[usuario]\\NeuroMood. Podés cambiarla con el botón Examinar.",
        "<b>Completá la instalación</b> — Hacé clic en Instalar. Al finalizar, elegí si crear accesos directos en el Escritorio.",
    ]
    fl.extend(_steps(steps))
    return fl


def _build_app(app):
    fl = [
        SectionHeader(app["name"], app["tagline"]),
        Spacer(1, 12),
    ]
    fl.extend(_centered_img(os.path.join(SS_DIR, app["screenshot"])))
    fl += [
        Spacer(1, 14),
        Paragraph("Descripción", S["head"]),
        Paragraph(app["description"], S["body"]),
        Spacer(1, 8),
        Paragraph("Instrucciones de uso", S["head"]),
    ]
    fl.extend(_steps(app["instructions"]))
    return fl


def _build_uninstaller():
    fl = [
        SectionHeader("Desinstalación",
                      "Cómo eliminar NeuroMood Suite del sistema"),
        Spacer(1, 14),
        Paragraph(
            "El desinstalador elimina de forma segura todas las aplicaciones, accesos "
            "directos, archivos y entradas del registro de Windows. Ofrece la opción de "
            "conservar o eliminar los datos personales (registros, historial y configuración).",
            S["body"],
        ),
        Spacer(1, 14),
    ]
    fl.extend(_centered_img(os.path.join(SS_DIR, "uninstaller.png"), max_w=min(CW, 490)))
    fl += [
        Spacer(1, 16),
        Paragraph("Pasos para desinstalar", S["head"]),
    ]
    fl.extend(_steps([
        "Abrí el Panel de control → Programas → Desinstalar un programa, buscá <b>NeuroMood Suite</b> y hacé doble clic. También podés ejecutar NM_Uninstaller.exe directamente desde la carpeta de instalación.",
        "En la pantalla de confirmación revisá la carpeta de instalación detectada y presioná <b>Desinstalar</b>.",
        "El proceso cerrará automáticamente las apps abiertas, eliminará los archivos de instalación, los accesos directos y la entrada del registro de Windows.",
        "Al finalizar, la suite queda completamente eliminada. Los datos personales se eliminan o conservan según la opción elegida en el paso anterior.",
    ]))
    fl += [
        Spacer(1, 16),
        Paragraph(
            "Si el desinstalador no puede borrar archivos en uso, cerrá todas las "
            "aplicaciones de NeuroMood antes de ejecutarlo.",
            S["note"],
        ),
    ]
    return fl


# ── App data ───────────────────────────────────────────────────────────────

APPS_DATA = [
    {
        "name": "Termómetro Emocional",
        "tagline": "Registrá tu estado emocional del 0 al 10 con notas personales",
        "screenshot": "termometro.png",
        "description": (
            "Herramienta de autorregistro emocional que permite puntuar el estado de "
            "ánimo en una escala del 0 al 10 cada día. Admite notas personales para "
            "contextualizar el registro y muestra el historial de los últimos días con "
            "código de colores que varía del rojo (0) al verde (10)."
        ),
        "instructions": [
            "Ajustá el deslizador al valor que mejor represente tu estado emocional actual (0 = muy bajo, 10 = excelente).",
            "Escribí una nota opcional en el campo de texto para contextualizar el registro del día.",
            "Presioná <b>Guardar registro</b> para confirmar la entrada.",
            "Revisá el historial de los últimos días en el panel lateral derecho.",
        ],
    },
    {
        "name": "Visualizador de Evolución",
        "tagline": "Gráficos de tendencia emocional basados en el Termómetro",
        "screenshot": "visualizador.png",
        "description": (
            "Genera gráficos interactivos con la evolución emocional registrada en el "
            "Termómetro Emocional. Permite visualizar tendencias en períodos de 7 días, "
            "30 días, 3 meses o el historial completo, y exportar el informe a PDF. "
            "Requiere datos previos en el Termómetro Emocional para mostrar contenido."
        ),
        "instructions": [
            "Requiere registros previos en el <b>Termómetro Emocional</b>.",
            "Seleccioná el período de análisis con los botones de la barra superior (7 días, 30 días, 3 meses o Todo).",
            "Explorá el gráfico de línea para identificar tendencias y patrones emocionales.",
            "Presioná <b>Exportar PDF</b> para generar un informe descargable con los datos del período.",
        ],
    },
    {
        "name": "Temporizador de Actividades",
        "tagline": "Cronómetro con categorías para registrar sesiones terapéuticas",
        "screenshot": "temporizador.png",
        "description": (
            "Cronómetro con categorías para delimitar y registrar actividades terapéuticas "
            "en el tiempo. Admite duraciones predefinidas (5, 10, 15, 20 y 30 minutos) o "
            "personalizadas. Guarda automáticamente cada sesión completada con nombre, "
            "categoría y duración real."
        ),
        "instructions": [
            "Ingresá el nombre de la actividad en el campo de texto.",
            "Seleccioná la categoría: Relajación, Cognitiva, Física, Social o Autocuidado.",
            "Elegí la duración con los botones rápidos (5'–30') o ingresá un valor personalizado en el campo <b>min</b>.",
            "Presioná <b>Iniciar</b> para arrancar el temporizador.",
            "Usá <b>Pausar / Reanudar</b> para interrumpir la sesión. Al finalizar, el registro se guarda automáticamente.",
        ],
    },
    {
        "name": "Guía de Respiración",
        "tagline": "Técnica guiada 4-7-8 con animación y registro de sesiones",
        "screenshot": "respiracion.png",
        "description": (
            "Guía animada de la técnica de respiración 4-7-8 (inhalar 4 segundos, retener "
            "7 segundos, exhalar 8 segundos). Incluye un círculo animado sincronizado con "
            "cada fase y registra automáticamente cada sesión con ciclos completados y "
            "tiempo total."
        ),
        "instructions": [
            "Seleccioná la duración de la sesión con los botones de tiempo disponibles.",
            "Presioná <b>Iniciar</b> para comenzar la guía animada.",
            "Seguí las instrucciones del círculo animado: inhalar — retener — exhalar.",
            "Al completar la sesión, el registro se guarda automáticamente.",
        ],
    },
    {
        "name": "Checklist de Rutina",
        "tagline": "Organización de tareas por turno con seguimiento de racha diaria",
        "screenshot": "checklist.png",
        "description": (
            "Organizador de tareas cotidianas dividido en secciones de Mañana, Tarde y "
            "Noche con seguimiento de progreso diario y racha semanal. Permite agregar "
            "tareas personalizadas a cada sección y consultar el cumplimiento en un "
            "calendario semanal con vista por día."
        ),
        "instructions": [
            "Seleccioná la sección del día: Mañana, Tarde o Noche.",
            "Ingresá el nombre de una tarea y presioná el botón <b>+</b> para agregarla.",
            "Marcá cada tarea como completada tildando la casilla correspondiente.",
            "Consultá el progreso del día y la racha semanal en la parte inferior.",
        ],
    },
    {
        "name": "Recordatorios de Bienestar",
        "tagline": "Notificaciones personalizadas con horarios y días específicos",
        "screenshot": "recordatorios.png",
        "description": (
            "Sistema de recordatorios personalizados con horarios y días específicos de "
            "la semana. Funciona en segundo plano desde la bandeja del sistema y emite "
            "alertas visuales y sonoras en los horarios configurados. Soporta múltiples "
            "recordatorios independientes con estado activo/inactivo."
        ),
        "instructions": [
            "Presioná <b>+ Nuevo recordatorio</b> para crear una entrada.",
            "Ingresá el mensaje, seleccioná la hora y los días de la semana activos.",
            "Activá o desactivá el recordatorio con el interruptor correspondiente.",
            "La app continúa monitoreando los horarios aunque esté minimizada en la bandeja del sistema.",
        ],
    },
    {
        "name": "Registro de Pensamientos",
        "tagline": "Identificá y reformulá pensamientos automáticos en 4 pasos",
        "screenshot": "pensamientos.png",
        "description": (
            "Herramienta de reestructuración cognitiva para identificar, analizar y "
            "reformular pensamientos automáticos negativos. Permite registrar la situación "
            "disparadora, el pensamiento automático, la emoción asociada y un pensamiento "
            "alternativo más equilibrado. Todos los registros quedan guardados en el historial."
        ),
        "instructions": [
            "Completá el paso 1: describí la situación que desencadenó el pensamiento.",
            "Avanzá con el botón <b>Siguiente →</b> e identificá el pensamiento automático negativo.",
            "En el paso 3, registrá la emoción que generó ese pensamiento.",
            "En el paso 4, formulá un pensamiento alternativo más equilibrado y guardá el registro en el historial.",
        ],
    },
    {
        "name": "Asistente de Activación",
        "tagline": "Activación conductual adaptada al nivel de energía actual",
        "screenshot": "activacion.png",
        "description": (
            "Genera sugerencias de actividades conductuales adaptadas al nivel de energía "
            "actual. Basado en principios de activación conductual terapéutica, propone "
            "tareas de bajo, medio o alto nivel de demanda según la energía reportada y "
            "registra un historial de actividades realizadas."
        ),
        "instructions": [
            "Ajustá el deslizador de Energía (0 = agotado, 10 = máxima energía).",
            "Presioná <b>Proponé actividades</b> para recibir sugerencias adaptadas.",
            "Revisá las actividades sugeridas y elegí la que mejor se ajuste a tu estado.",
            "Usá los botones <b>Hecha</b>, <b>Intentada</b> o <b>No pude</b> para registrar el resultado en tu historial.",
        ],
    },
]


# ── Build ──────────────────────────────────────────────────────────────────

def build():
    _reg_fonts()
    _build_styles()

    doc = BaseDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT, bottomMargin=MB,
    )

    cover_frame   = Frame(ML, MB, CW, CH, id="cover",   showBoundary=0)
    content_frame = Frame(ML, MB, CW, CH, id="content", showBoundary=0)

    doc.addPageTemplates([
        PageTemplate("cover",   frames=[cover_frame],   onPage=_on_cover),
        PageTemplate("content", frames=[content_frame], onPage=_on_content),
    ])

    story = []
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    story.extend(_build_requirements())
    story.append(PageBreak())

    story.extend(_build_installer())

    for app in APPS_DATA:
        story.append(PageBreak())
        story.extend(_build_app(app))

    story.append(PageBreak())
    story.extend(_build_uninstaller())

    doc.build(story)
    print(f"PDF generado: {OUTPUT}")
    print(f"Paginas aproximadas: {len(APPS_DATA) + 4}")


if __name__ == "__main__":
    build()
