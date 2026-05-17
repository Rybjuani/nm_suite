from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets" / "LOGO.png"

USER_PDF = ROOT / "Manual_Usuario_Profesional_NeuroMood.pdf"
TECH_PDF = ROOT / "Manual_Tecnico_Descriptivo_NeuroMood.pdf"
OLD_OUTPUTS = [
    ROOT / "Manual_Usuario_Final_NeuroMood_V3.pdf",
    ROOT / "Manual_Tecnico_Descriptivo_NeuroMood_V3.pdf",
    ROOT / "Manual_Usuario_Final_NeuroMood_V3.md",
    ROOT / "Manual_Tecnico_NeuroMood_V3.md",
]

PAGE_W, PAGE_H = A4

INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
SOFT = colors.HexColor("#f8fafc")
SURFACE = colors.HexColor("#ffffff")
BORDER = colors.HexColor("#dbe5ef")
TEAL = colors.HexColor("#14b8a6")
TEAL_DARK = colors.HexColor("#0f766e")
VIOLET = colors.HexColor("#8b5cf6")
INDIGO = colors.HexColor("#6366f1")
DARK = colors.HexColor("#07111f")
DARK_2 = colors.HexColor("#0f1b2d")
SLATE = colors.HexColor("#1e293b")
WARN = colors.HexColor("#f59e0b")
GOOD = colors.HexColor("#22c55e")
RED = colors.HexColor("#ef4444")


@dataclass
class DocTheme:
    title: str
    subtitle: str
    eyebrow: str
    accent: colors.Color = TEAL
    secondary: colors.Color = VIOLET


class PdfManual:
    def __init__(self, path: Path, theme: DocTheme):
        self.path = path
        self.theme = theme
        self.c = canvas.Canvas(str(path), pagesize=A4, pageCompression=0)
        self.c.setTitle(theme.title)
        self.c.setAuthor("NeuroMood")
        self.page = 0
        self._logo_reader = ImageReader(str(LOGO)) if LOGO.exists() else None

    def save(self) -> None:
        self.c.save()

    def new_page(self, *, dark: bool = False) -> None:
        if self.page:
            self.c.showPage()
        self.page += 1
        self.c.setFillColor(DARK if dark else SOFT)
        self.c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        if not dark:
            self._draw_page_chrome()

    def _draw_page_chrome(self) -> None:
        self.c.setFillColor(SURFACE)
        self.c.roundRect(28, 28, PAGE_W - 56, PAGE_H - 56, 18, stroke=0, fill=1)
        self.c.setStrokeColor(colors.Color(0.86, 0.90, 0.95, alpha=0.75))
        self.c.roundRect(28, 28, PAGE_W - 56, PAGE_H - 56, 18, stroke=1, fill=0)
        self.c.setFillColor(MUTED)
        self.c.setFont("Helvetica", 8)
        self.c.drawString(54, 42, "NeuroMood")
        self.c.drawRightString(PAGE_W - 54, 42, str(self.page))

    def cover(self, bullets: list[str]) -> None:
        self.new_page(dark=True)
        for i in range(44):
            ratio = i / 44
            r = 0.03 + ratio * 0.03
            g = 0.07 + ratio * 0.03
            b = 0.13 + ratio * 0.10
            self.c.setFillColor(colors.Color(r, g, b))
            self.c.rect(0, i * PAGE_H / 44, PAGE_W, PAGE_H / 44 + 1, stroke=0, fill=1)
        self.c.setFillColor(colors.Color(0.08, 0.72, 0.65, alpha=0.12))
        self.c.circle(PAGE_W - 100, PAGE_H - 120, 160, stroke=0, fill=1)
        self.c.setFillColor(colors.Color(0.55, 0.36, 0.96, alpha=0.14))
        self.c.circle(86, 110, 180, stroke=0, fill=1)
        if self._logo_reader:
            self.c.drawImage(self._logo_reader, 54, PAGE_H - 114, width=176, height=37, mask="auto")
        self.pill(54, PAGE_H - 160, self.theme.eyebrow.upper(), self.theme.accent, dark=True)
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 34)
        y = PAGE_H - 230
        for line in wrap(self.theme.title, 24):
            self.c.drawString(54, y, line)
            y -= 40
        self.c.setFillColor(colors.HexColor("#cbd5e1"))
        self.c.setFont("Helvetica", 13)
        y -= 8
        for line in wrap(self.theme.subtitle, 58):
            self.c.drawString(56, y, line)
            y -= 18
        self.c.setFillColor(colors.Color(1, 1, 1, alpha=0.08))
        self.c.roundRect(54, 100, PAGE_W - 108, 190, 18, stroke=0, fill=1)
        self.c.setStrokeColor(colors.Color(1, 1, 1, alpha=0.12))
        self.c.roundRect(54, 100, PAGE_W - 108, 190, 18, stroke=1, fill=0)
        y = 254
        for bullet in bullets:
            self.c.setFillColor(self.theme.accent)
            self.c.circle(78, y + 4, 3, stroke=0, fill=1)
            self.c.setFillColor(colors.HexColor("#e2e8f0"))
            self.c.setFont("Helvetica", 10.5)
            self.draw_text(bullet, 92, y, PAGE_W - 170, 13.5, color=colors.HexColor("#e2e8f0"))
            y -= 42
        self.c.setFillColor(colors.HexColor("#94a3b8"))
        self.c.setFont("Helvetica", 9)
        self.c.drawString(54, 54, "Documentación de producto")

    def section(self, title: str, intro: str, *, accent: colors.Color | None = None) -> float:
        accent = accent or self.theme.accent
        self.new_page()
        x, y = 54, PAGE_H - 92
        self.c.setFillColor(accent)
        self.c.roundRect(x, y + 8, 44, 6, 3, stroke=0, fill=1)
        self.c.setFillColor(INK)
        self.c.setFont("Helvetica-Bold", 24)
        self.c.drawString(x, y - 22, title)
        self.draw_text(intro, x, y - 52, PAGE_W - 108, 14, font="Helvetica", size=10.5, color=MUTED)
        return y - 94

    def h2(self, text: str, x: float, y: float, *, color: colors.Color = INK) -> float:
        self.c.setFillColor(color)
        self.c.setFont("Helvetica-Bold", 14)
        self.c.drawString(x, y, text)
        return y - 20

    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        width: float,
        leading: float = 13,
        *,
        font: str = "Helvetica",
        size: float = 9.5,
        color: colors.Color = INK,
    ) -> float:
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        max_chars = max(28, int(width / (size * 0.48)))
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                y -= leading
                continue
            for line in wrap(paragraph, max_chars):
                self.c.drawString(x, y, line)
                y -= leading
        return y

    def pill(self, x: float, y: float, text: str, fill: colors.Color, *, dark: bool = False) -> None:
        self.c.setFont("Helvetica-Bold", 8)
        w = self.c.stringWidth(text, "Helvetica-Bold", 8) + 22
        self.c.setFillColor(fill)
        self.c.roundRect(x, y, w, 20, 10, stroke=0, fill=1)
        self.c.setFillColor(colors.white if dark else colors.white)
        self.c.drawCentredString(x + w / 2, y + 6, text)

    def card(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        body: str,
        *,
        accent: colors.Color | None = None,
        tag: str | None = None,
    ) -> None:
        accent = accent or self.theme.accent
        self.c.setFillColor(SURFACE)
        self.c.roundRect(x, y - h, w, h, 14, stroke=0, fill=1)
        self.c.setStrokeColor(BORDER)
        self.c.roundRect(x, y - h, w, h, 14, stroke=1, fill=0)
        self.c.setFillColor(colors.Color(accent.red, accent.green, accent.blue, alpha=0.12))
        self.c.roundRect(x + 14, y - 30, 34, 20, 10, stroke=0, fill=1)
        self.c.setFillColor(accent)
        self.c.circle(x + 31, y - 20, 4, stroke=0, fill=1)
        self.c.setFillColor(INK)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(x + 58, y - 24, title)
        if tag:
            self.pill(x + w - 82, y - 31, tag, accent)
        self.draw_text(body, x + 16, y - 52, w - 32, 12.2, size=8.8, color=MUTED)

    def metric_row(self, x: float, y: float, items: list[tuple[str, str]], *, accent: colors.Color | None = None) -> float:
        accent = accent or self.theme.accent
        gap = 12
        w = (PAGE_W - 108 - gap * (len(items) - 1)) / len(items)
        for idx, (value, label) in enumerate(items):
            xx = x + idx * (w + gap)
            self.c.setFillColor(colors.Color(accent.red, accent.green, accent.blue, alpha=0.08))
            self.c.roundRect(xx, y - 66, w, 66, 14, stroke=0, fill=1)
            self.c.setStrokeColor(colors.Color(accent.red, accent.green, accent.blue, alpha=0.28))
            self.c.roundRect(xx, y - 66, w, 66, 14, stroke=1, fill=0)
            self.c.setFillColor(INK)
            self.c.setFont("Helvetica-Bold", 17)
            self.c.drawString(xx + 16, y - 28, value)
            self.c.setFillColor(MUTED)
            self.c.setFont("Helvetica", 8.5)
            self.c.drawString(xx + 16, y - 47, label)
        return y - 86

    def mockup_panel(self, x: float, y: float, w: float, h: float, title: str, kind: str) -> None:
        self.c.setFillColor(DARK_2)
        self.c.roundRect(x, y - h, w, h, 18, stroke=0, fill=1)
        self.c.setStrokeColor(colors.Color(1, 1, 1, alpha=0.10))
        self.c.roundRect(x, y - h, w, h, 18, stroke=1, fill=0)
        self.c.setFillColor(colors.HexColor("#e2e8f0"))
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(x + 18, y - 26, title)
        self.c.setFillColor(colors.HexColor("#94a3b8"))
        self.c.setFont("Helvetica", 7.5)
        self.c.drawRightString(x + w - 18, y - 25, "mockup")
        if kind == "suite":
            cols, rows = 3, 2
            cw = (w - 54) / cols
            ch = 46
            labels = ["Ánimo", "Respirar", "TCC", "Rutina", "Actividad", "Avisos"]
            accents = [TEAL, INDIGO, VIOLET, GOOD, WARN, RED]
            for i, label in enumerate(labels):
                cx = x + 18 + (i % cols) * (cw + 9)
                cy = y - 54 - (i // cols) * (ch + 10)
                self.c.setFillColor(colors.Color(1, 1, 1, alpha=0.06))
                self.c.roundRect(cx, cy - ch, cw, ch, 9, stroke=0, fill=1)
                self.c.setFillColor(accents[i])
                self.c.circle(cx + 16, cy - 19, 5, stroke=0, fill=1)
                self.c.setFillColor(colors.HexColor("#e2e8f0"))
                self.c.setFont("Helvetica-Bold", 7.2)
                self.c.drawString(cx + 28, cy - 22, label)
                self.c.setFillColor(colors.Color(accents[i].red, accents[i].green, accents[i].blue, alpha=0.35))
                self.c.roundRect(cx + 28, cy - 36, cw - 42, 6, 3, stroke=0, fill=1)
        elif kind == "hub":
            self.c.setFillColor(colors.Color(1, 1, 1, alpha=0.06))
            self.c.roundRect(x + 18, y - h + 18, 72, h - 54, 12, stroke=0, fill=1)
            for i, label in enumerate(["Pacientes", "Dashboard", "IA", "Config"]):
                yy = y - 58 - i * 24
                self.c.setFillColor(TEAL if i == 0 else colors.HexColor("#94a3b8"))
                self.c.circle(x + 34, yy, 3, stroke=0, fill=1)
                self.c.setFillColor(colors.HexColor("#cbd5e1"))
                self.c.setFont("Helvetica", 6.8)
                self.c.drawString(x + 44, yy - 3, label)
            for i, name in enumerate(["Ana Martínez", "Juan Rodríguez", "Carmen López"]):
                yy = y - 62 - i * 42
                self.c.setFillColor(colors.Color(1, 1, 1, alpha=0.07))
                self.c.roundRect(x + 104, yy - 22, w - 126, 32, 9, stroke=0, fill=1)
                self.c.setFillColor(TEAL if i == 0 else INDIGO)
                self.c.circle(x + 120, yy - 6, 6, stroke=0, fill=1)
                self.c.setFillColor(colors.HexColor("#e2e8f0"))
                self.c.setFont("Helvetica-Bold", 7.2)
                self.c.drawString(x + 134, yy - 3, name)
        else:
            steps = ["Cuenta", "Ruta", "Instalar", "Final"]
            for i, step in enumerate(steps):
                cx = x + 34 + i * ((w - 68) / 3)
                self.c.setFillColor(TEAL if i < 2 else colors.HexColor("#334155"))
                self.c.circle(cx, y - 74, 10, stroke=0, fill=1)
                self.c.setFillColor(colors.HexColor("#e2e8f0"))
                self.c.setFont("Helvetica-Bold", 6.5)
                self.c.drawCentredString(cx, y - 101, step)
            self.c.setFillColor(colors.HexColor("#060d1a"))
            self.c.roundRect(x + 30, y - h + 28, w - 60, 42, 8, stroke=0, fill=1)
            self.c.setFillColor(TEAL)
            self.c.setFont("Courier", 7)
            self.c.drawString(x + 42, y - h + 52, "> preparando instalación segura")
            self.c.drawString(x + 42, y - h + 38, "> validando componentes")

    def table(self, x: float, y: float, rows: list[tuple[str, str]], *, w: float = PAGE_W - 108) -> float:
        row_h = 46
        self.c.setStrokeColor(BORDER)
        for i, (left, right) in enumerate(rows):
            yy = y - i * row_h
            self.c.setFillColor(colors.HexColor("#f8fafc") if i % 2 == 0 else colors.white)
            self.c.roundRect(x, yy - row_h, w, row_h, 8 if i in (0, len(rows) - 1) else 0, stroke=0, fill=1)
            self.c.setFillColor(INK)
            self.c.setFont("Helvetica-Bold", 8.8)
            self.c.drawString(x + 14, yy - 18, left)
            self.draw_text(right, x + 160, yy - 14, w - 174, 11, size=8.2, color=MUTED)
        self.c.setStrokeColor(BORDER)
        self.c.roundRect(x, y - row_h * len(rows), w, row_h * len(rows), 10, stroke=1, fill=0)
        return y - row_h * len(rows) - 24


def cleanup_old_outputs() -> None:
    for path in OLD_OUTPUTS:
        if path.exists():
            path.unlink()


def build_user_manual() -> None:
    doc = PdfManual(
        USER_PDF,
        DocTheme(
            title="Manual para Pacientes y Profesionales",
            subtitle="Guía clara para pacientes, equipos clínicos, NeuroMood Hub, instalación, desinstalación, privacidad y uso cotidiano.",
            eyebrow="NeuroMood",
            accent=TEAL,
            secondary=VIOLET,
        ),
    )
    doc.cover(
        [
            "Acompaña el registro emocional, la activación conductual, la rutina diaria y la comunicación clínica sin invadir la experiencia del paciente.",
            "Ordena la información relevante para que el profesional observe evolución, adherencia y señales de seguimiento desde NeuroMood Hub.",
            "Incluye una instalación guiada, desinstalación clara y criterios de privacidad pensados para un entorno terapéutico real.",
        ]
    )

    y = doc.section(
        "Pacientes",
        "NeuroMood Suite para pacientes reune herramientas breves, visuales y repetibles. Su valor no esta en exigir mas carga al paciente, sino en transformar momentos cotidianos en registros utiles para el acompanamiento.",
    )
    doc.mockup_panel(54, y, PAGE_W - 108, 160, "Suite del paciente · referencia visual", "suite")
    y -= 190
    doc.metric_row(54, y, [("7", "módulos de acompañamiento"), ("2", "temas visuales"), ("1", "experiencia integrada")])
    y -= 84
    doc.h2("Qué aporta en el uso diario", 54, y)
    y -= 24
    doc.draw_text(
        "La aplicación ayuda a que el paciente registre cómo está, sostenga acciones pequeñas y llegue a la sesión con información menos fragmentada. Cada módulo usa una tarea concreta: elegir una emoción, completar una rutina, practicar respiración, escribir un pensamiento o activar una conducta posible.",
        54,
        y,
        PAGE_W - 108,
        14,
        color=MUTED,
    )

    y = doc.section("Módulos de la Suite", "Cada herramienta tiene un rol específico dentro del acompañamiento clínico. Los nombres visibles vigentes son los siguientes.")
    modules = [
        ("Termómetro Emocional", "Permite registrar el estado emocional con una escala simple, emojis grandes y una nota breve. Favorece continuidad entre sesiones y ayuda a detectar patrones sin convertir el registro en una encuesta extensa.", TEAL),
        ("Guía de Respiración Animada", "Propone pausas respiratorias con ritmo visual, ciclos y fases claras. Es útil para bajar activación fisiológica, iniciar una transición o cerrar una intervención breve.", INDIGO),
        ("Registro de Pensamientos (TCC)", "Ordena situación, emoción, pensamiento automático y respuesta alternativa. El diseño por pasos reduce fricción y hace más fácil revisar material terapéutico luego.", VIOLET),
        ("Checklist de Rutina Diaria", "Agrupa acciones por momentos del día y muestra avance. Refuerza adherencia, higiene de hábitos y sensación de estructura sin imponer un formato rígido.", GOOD),
        ("Asistente de Activación Conductual", "Sugiere actividades acordes al contexto anímico. Ayuda a pasar de la observación del estado interno a una acción posible, concreta y medible.", WARN),
        ("Temporizador de Actividades", "Acompaña bloques de foco, tareas terapéuticas o actividades graduadas. Los presets y el historial facilitan sostener pequeñas sesiones de acción.", INDIGO),
        ("Recordatorios de Bienestar", "Organiza avisos de medicación, hábitos, pausas y tareas indicadas. Su función es sostener continuidad sin saturar al paciente.", RED),
    ]
    x1, x2 = 54, 309
    for i, (title, body, accent) in enumerate(modules):
        x = x1 if i % 2 == 0 else x2
        if i and i % 2 == 0:
            y -= 118
        doc.card(x, y, 230, 104, title, body, accent=accent)
    y -= 128
    doc.draw_text(
        "Los nombres anteriores quedan solo como referencia técnica: animo, respiracion, TCC, rutina, actividades, Timer y avisos.",
        54,
        y,
        PAGE_W - 108,
        12,
        color=MUTED,
    )

    y = doc.section(
        "Uso clínico",
        "NeuroMood no reemplaza el criterio profesional. Su aporte es ordenar señales entre encuentros, facilitar adherencia y dejar una huella de trabajo terapéutico más legible.",
    )
    rows = [
        ("Antes de la sesión", "El paciente puede registrar ánimo, rutinas y eventos relevantes. El profesional llega con una vista más clara del período entre consultas."),
        ("Durante la sesión", "Los registros permiten revisar ejemplos concretos, detectar barreras, ajustar indicaciones y acordar tareas más realistas."),
        ("Después de la sesión", "Recordatorios, checklist y temporizadores ayudan a sostener la intervención en el contexto cotidiano."),
        ("Seguimiento", "El NeuroMood Hub permite observar evolución, revisar patrones y mantener una lectura organizada del proceso sin depender solo del relato retrospectivo."),
    ]
    y = doc.table(54, y, rows)
    doc.card(
        54,
        y,
        PAGE_W - 108,
        98,
        "Criterio de uso recomendado",
        "Empezar con pocos módulos, acordar objetivos simples y revisar los datos con el paciente. La experiencia mejora cuando la app se usa como apoyo conversacional y no como obligación administrativa.",
        accent=TEAL,
        tag="práctico",
    )

    y = doc.section(
        "NeuroMood Hub",
        "NeuroMood Hub centraliza pacientes, lectura de evolución, asistencia contextual y configuración. Está pensado para equipos que necesitan mirar información clínica sin perder tiempo en pantallas cargadas.",
        accent=VIOLET,
    )
    doc.mockup_panel(54, y, PAGE_W - 108, 156, "NeuroMood Hub · lista y seguimiento", "hub")
    y -= 184
    hub_rows = [
        ("Pacientes", "Lista con búsqueda, estado, sincronización y acceso rápido al detalle clínico."),
        ("Dashboard", "Lectura visual de módulos, actividad reciente, tendencias y resumen de una persona seleccionada."),
        ("IA Asistente", "Apoyo para ordenar información, preparar preguntas o sintetizar contexto. No reemplaza el juicio profesional."),
        ("Configuración", "Preferencias de tema, sincronización, estado de conexión y controles operativos."),
    ]
    doc.table(54, y, hub_rows)

    y = doc.section(
        "Instaladores y Desinstaladores",
        "La instalacion se presenta como un flujo guiado, con pasos visibles, validacion, consentimiento legal y mensajes claros. El objetivo es que el paciente entienda que se instala, que acepta y como puede retirarlo.",
    )
    doc.mockup_panel(54, y, PAGE_W - 108, 152, "Instalación guiada · referencia visual", "installer")
    y -= 182
    install_rows = [
        ("Instalador Suite", "Incluye cuenta obligatoria con Supabase Auth, consentimiento legal auditable, ruta de instalacion, progreso y cierre final."),
        ("Instalador Hub", "Instala NeuroMood Hub con configuración segura por defecto, sin pedir credenciales manuales al paciente."),
        ("Desinstaladores", "Permiten retirar la aplicación y decidir si se conservan o eliminan los datos locales según corresponda."),
        ("Reinstalación", "Puede realizarse desde los instaladores oficiales. La conservación de datos depende de la opción elegida al desinstalar."),
    ]
    y = doc.table(54, y, install_rows)
    doc.card(
        54,
        y,
        PAGE_W - 108,
        92,
        "Que debe verificar el paciente",
        "Usar instaladores oficiales, mantener conexion a internet durante autenticacion y consentimiento, y consultar al profesional ante dudas sobre modulos, recordatorios o interpretacion de registros.",
        accent=TEAL,
    )

    y = doc.section(
        "Privacidad y uso",
        "La información de salud requiere un trato cuidadoso. NeuroMood está diseñado para registrar lo necesario, sincronizar con control y evitar exponer datos técnicos innecesarios.",
    )
    privacy_rows = [
        ("Cuenta", "La autenticación se realiza con email y contraseña mediante Supabase Auth. La contraseña no se guarda localmente."),
        ("Datos locales", "La Suite puede guardar información en el equipo para operar y conservar continuidad de uso."),
        ("Sincronización", "Cuando corresponde, los datos se sincronizan para que el profesional pueda revisar evolución y asignaciones."),
        ("Permisos", "El Hub puede habilitar o bloquear módulos. La configuración inicial prioriza acceso funcional y luego permite control profesional."),
        ("Uso responsable", "Los registros son apoyo para la conversación clínica. Ante urgencias o crisis, se deben usar los canales asistenciales indicados por el equipo tratante."),
    ]
    y = doc.table(54, y, privacy_rows)
    doc.draw_text(
        "Buenas prácticas: registrar con honestidad, usar notas breves, revisar la información en consulta y no compartir el equipo o la cuenta con terceros.",
        54,
        y,
        PAGE_W - 108,
        13,
        color=MUTED,
    )
    doc.save()


def build_technical_manual() -> None:
    doc = PdfManual(
        TECH_PDF,
        DocTheme(
            title="Manual Técnico Descriptivo",
            subtitle="Arquitectura, configuración, autenticación, sincronización, permisos, build, QA, instaladores, seguridad y distribución.",
            eyebrow="NeuroMood",
            accent=VIOLET,
            secondary=TEAL,
        ),
    )
    doc.cover(
        [
            "Documento orientado a desarrolladores, profesionales técnicos y responsables de operación.",
            "Resume la estructura vigente del proyecto y las zonas sensibles que no deben modificarse sin revisión.",
            "Centraliza criterios de build, QA, seguridad y distribución para mantener una entrega reproducible.",
        ]
    )

    y = doc.section(
        "Arquitectura",
        "El producto se organiza como dos aplicaciones PyQt6 de escritorio, componentes compartidos, instaladores propios y scripts de automatización concentrados.",
        accent=VIOLET,
    )
    arch_rows = [
        ("app/", "Suite del paciente. Entry point: app/main_qt.py. Carga home y siete módulos funcionales."),
        ("hub/", "NeuroMood Hub para profesionales. Entry point: hub/main_qt.py. Incluye pacientes, dashboard, IA y configuración."),
        ("shared/", "Design system, componentes Qt, config, DB, sync, identidad, helpers y fixtures visuales QA."),
        ("installers/", "Instaladores y desinstaladores PyQt6. Mantienen wizard visual, auth y limpieza de instalación."),
        ("AI_SCRIPTS/", "Build oficial, QA, capturas, auditorías visuales y utilidades para agentes."),
        ("dist/", "Salida de EXEs oficiales. Se conserva; build/ y specs son temporales."),
    ]
    y = doc.table(54, y, arch_rows)
    doc.card(
        54,
        y,
        PAGE_W - 108,
        82,
        "Archivo de contexto obligatorio",
        "AI_PROJECT_CONTEXT.md es la fuente de documentación para agentes IA. Cualquier nota técnica nueva debe consolidarse ahí y no en archivos sueltos.",
        accent=VIOLET,
        tag="IA",
    )

    y = doc.section(
        "Configuración y Supabase",
        "La configuración sensible se concentra en puertas de acceso específicas. El objetivo es evitar secretos duplicados, pantallas manuales innecesarias y exposición accidental.",
    )
    config_rows = [
        (".env", "Debe contener variables públicas necesarias como SUPABASE_URL y SUPABASE_KEY anon. No distribuir service_role."),
        ("shared/config.py", "Punto de lectura para configuración. No duplicar lectura de secretos en módulos de UI."),
        ("Supabase Auth", "Suite installer usa email y contraseña con sign_in, sign_up y reset_password_for_email."),
        ("NeuroMood Hub", "La configuración Supabase queda preparada por defecto. No se solicita carga manual al paciente o profesional."),
        ("Sin SMTP custom", "El flujo actual usa email default de Supabase. Cambios de remitente se hacen luego en consola Supabase, no en código."),
    ]
    y = doc.table(54, y, config_rows)
    doc.card(
        54,
        y,
        PAGE_W - 108,
        92,
        "Regla de seguridad",
        "No tocar shared/db.py, shared/sync.py, shared/config.py ni shared/identidad.py en cambios visuales. Si se modifica auth, sync o permisos, validar con pruebas reales y revisar manejo de errores offline.",
        accent=RED,
    )

    y = doc.section(
        "Datos, sync y permisos",
        "El modelo combina almacenamiento local, sincronización con Supabase y control profesional de módulos. El comportamiento productivo debe mantenerse estable.",
        accent=TEAL,
    )
    sync_rows = [
        ("SQLite local", "shared/db.py gestiona la base local en AppData. Mantener migraciones y acceso estructurado."),
        ("Sync", "shared/sync.py exporta datos, importa permisos y actualiza estado de paciente con lazy loading."),
        ("Permisos", "La instalacion parte de modulos desbloqueados. NeuroMood Hub puede bloquear o desbloquear modulos posteriormente."),
        ("Fixtures QA", "shared/visual_qa.py habilita datos visuales solo con flags explícitos de QA/demo."),
        ("Errores de red", "Auth y sync deben fallar con mensajes elegantes, sin crash y con opción de reintento cuando aplique."),
    ]
    y = doc.table(54, y, sync_rows)
    doc.metric_row(54, y, [("local", "continuidad de uso"), ("sync", "seguimiento profesional"), ("QA", "fixtures aislados")], accent=TEAL)

    y = doc.section(
        "Interfaz y design system",
        "La referencia visual principal es el mockup HTML de la raíz. Los cambios UI deben usar tokens y componentes compartidos antes que estilos crudos.",
    )
    ui_rows = [
        ("Tokens", "Usar C(), qfont(), nm_font(), sp(), RADIUS_*, PAD_* y GAP_* donde correspondan."),
        ("Componentes", "Priorizar NMWelcomeBar, NMEmojiPicker, NMActivityCard, NMHubSidebar, NMInstallStepper y componentes compartidos existentes."),
        ("Temas", "Mantener dark/light donde aplique, sin scrollbars inesperadas en tamaños objetivo."),
        ("Instaladores", "Suite usa teal; NeuroMood Hub usa violet. Terminal, stepper y botones deben conservar medidas del mockup."),
        ("Sitio visual", "La identidad debe sentirse clínica, clara, tecnológica y sobria: blanco limpio, fondos oscuros controlados y acentos teal/violeta."),
    ]
    y = doc.table(54, y, ui_rows)
    doc.mockup_panel(54, y, PAGE_W - 108, 142, "Patrones visuales principales", "suite")

    y = doc.section(
        "Build y distribución",
        "La compilación se centraliza en un único BAT y un script Python mantenible. El objetivo es reducir basura en la raíz y hacer el proceso reproducible.",
        accent=VIOLET,
    )
    build_rows = [
        ("Comando oficial", "BUILD_NEUROMOOD.bat compila Suite, NeuroMood Hub, desinstaladores e instaladores."),
        ("Script interno", "AI_SCRIPTS/build_neuromood.py contiene targets, hidden imports, add-data, preflight y limpieza."),
        ("Validación rápida", "BUILD_NEUROMOOD.bat --dry-run valida rutas y secuencia sin compilar."),
        ("Build limpio", "BUILD_NEUROMOOD.bat --clean fuerza cache limpio de PyInstaller cuando hay fallos persistentes."),
        ("Limpieza", "Al terminar se eliminan specs y build/. dist/ queda como salida oficial."),
    ]
    y = doc.table(54, y, build_rows)
    doc.card(
        54,
        y,
        PAGE_W - 108,
        82,
        "Artefactos esperados",
        "dist/NeuroMood Suite, dist/NeuroMood Hub, dist/Instalador Suite, dist/Instalador Hub y sus desinstaladores.",
        accent=VIOLET,
    )

    y = doc.section(
        "QA y operación",
        "El QA visual debe ejecutarse sobre EXEs reales cuando el objetivo sea fidelidad final. Los scripts de utilidad viven en AI_SCRIPTS.",
    )
    qa_rows = [
        ("Capturas EXE", "AI_SCRIPTS/qa_exe_capture.py recorre instaladores, apps y desinstaladores para generar evidencia visual."),
        ("Smoke tests", "AI_SCRIPTS/smoke_test_runner.py concentra validaciones rápidas de arranque y módulos."),
        ("Auditorías visuales", "Scripts _audit_* y _test_* ayudan a revisar mockup, color, responsive y navegación."),
        ("Procesos", "Al finalizar QA no deben quedar procesos abiertos ni carpetas temporales innecesarias."),
        ("Modo demo", "Usar flags QA explícitos. No mezclar fixtures con producción."),
    ]
    y = doc.table(54, y, qa_rows)
    doc.card(
        54,
        y,
        PAGE_W - 108,
        92,
        "Checklist antes de distribuir",
        "Compilar con el BAT oficial, instalar Suite y NeuroMood Hub, recorrer pantallas principales, probar dark/light, ejecutar desinstaladores y confirmar que no quedan residuos salvo datos preservados por eleccion del paciente.",
        accent=TEAL,
    )

    y = doc.section(
        "Zonas sensibles",
        "Estas reglas reducen riesgo operativo. Para cambios visuales, mantenerse fuera de lógica clínica, sincronización, configuración y seguridad.",
        accent=RED,
    )
    sensitive_rows = [
        ("No tocar sin revisión", "shared/db.py, shared/sync.py, shared/config.py, shared/identidad.py."),
        ("No hardcodear", "Colores, paddings, fuentes, secretos, IDs, rutas clínicas o claves."),
        ("No duplicar docs", "Actualizar AI_PROJECT_CONTEXT.md. Evitar README paralelos, docs/ o planes sueltos."),
        ("No romper producto", "Mantener un EXE paciente y un NeuroMood Hub. No recrear apps separadas."),
        ("No exponer secretos", "No mostrar URL/API key reales en Hub ni logs visibles. No empaquetar service_role."),
    ]
    doc.table(54, y, sensitive_rows)
    doc.save()


def main() -> None:
    cleanup_old_outputs()
    build_user_manual()
    build_technical_manual()
    print(USER_PDF)
    print(TECH_PDF)


if __name__ == "__main__":
    main()
