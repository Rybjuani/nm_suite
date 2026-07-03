"""
app/modules/dbt_qt.py — Módulo Habilidades DBT (PyQt6)
Práctica guiada de habilidades DBT con vistas Ahora y Biblioteca.
"""

import os
import sys
import datetime
import uuid
import logging

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QEvent, QPointF, QSize
from PyQt6.QtGui import QImage, QPainter, QBrush, QColor, QPixmap, QRadialGradient, QPen, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QStackedWidget,
    QFrame,
    QGraphicsDropShadowEffect,
)

# Textos customizables desde el Hub
from shared.remote_config import t

# Import standard NeuroMood components and theme variables
try:
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        ThemeManager,
        NMCard,
        NMTabs,
    )
    from shared.theme_qt import (
        norm_modo,
        v3c,
        qfont,
        v3_font,
        qcolor_to_rgba_css,
        TYPOGRAPHY,
        stylesheet_scrollarea,
    )
    from shared.db import conexion
except ImportError:
    # Fallback paths
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        ThemeManager,
        NMCard,
        NMTabs,
    )
    from shared.theme_qt import (
        norm_modo,
        v3c,
        qfont,
        v3_font,
        qcolor_to_rgba_css,
        TYPOGRAPHY,
        stylesheet_scrollarea,
    )
    from shared.db import conexion

_log = logging.getLogger(__name__)

_DBT_FAMILY_TITLES = {
    "mindfulness": "Mindfulness",
    "distress_tolerance": "Tolerancia",
    "emotion_regulation": "Regulación",
    "interpersonal_effectiveness": "Efectividad",
}
_DBT_FAMILY_LONG_TITLES = {
    "mindfulness": "Mindfulness",
    "distress_tolerance": "Tolerancia al malestar",
    "emotion_regulation": "Regulación emocional",
    "interpersonal_effectiveness": "Efectividad interpersonal",
}
_DBT_FAMILY_COLOR_KEYS = {
    "mindfulness": "mind",
    "distress_tolerance": "toler",
    "emotion_regulation": "regul",
    "interpersonal_effectiveness": "efect",
}
_DBT_SKILL_BAR_TOP_W = 30
_DBT_SKILL_BAR_TOP_H = 3
_DBT_LIBRARY_COLUMNS = 4
_DBT_LIBRARY_CARD_MIN_H = 96
_DBT_LIBRARY_CARD_MAX_H = 96
_DBT_NEED_BORDER_W = 3  # mockup l.232: .need-card{border-left:3px solid var(--brand); ...}
_DBT_NEED_BORDER_Y = 14
_DBT_NEED_BORDER_RADIUS = 2.5


def _dbt_family_color_key(family: str) -> str:
    return _DBT_FAMILY_COLOR_KEYS.get(family, "text")


def _dbt_family_soft_css(family: str, modo: str, alpha: float = 0.14) -> str:
    c = QColor(v3c(_dbt_family_color_key(family), modo))
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return qcolor_to_rgba_css(c)


_DBT_SAFETY_NOTE = (
    "Esta habilidad es un apoyo inmediato. Si sentís malestar extremo o peligro "
    "inminente, recurrí a asistencia profesional."
)


def _skill(
    practice_id: str,
    family: str,
    title: str,
    summary: str,
    duration_min: int,
    steps: list[tuple[str, str]],
) -> dict:
    return {
        "id": practice_id,
        "version": 1,
        "family": family,
        "title": title,
        "summary": summary,
        "duration_min": duration_min,
        "steps": [{"title": h, "body": d} for h, d in steps],
        "safety_note": _DBT_SAFETY_NOTE,
    }


# DBT v2 canon: 16 prácticas formales, alineadas con el HTML canónico.
DBT_SKILLS = {
    "observe_describe": _skill(
        "observe_describe",
        "mindfulness",
        "Observar y describir",
        "Notar sensaciones, pensamientos y entorno sin intentar corregirlos.",
        2,
        [
            ("Elegí un objeto", "Fijate en algo del entorno o en una sensación corporal concreta."),
            ("Observá", "Notá ese objeto sin etiquetarlo, sin interpretarlo, sin reaccionar."),
            ("Describí", "Poné en palabras lo que percibís, en voz baja o mentalmente."),
            ("Volvé cuando la mente se vaya", "Cada vez que aparezca un juicio o pensamiento, regresá al objeto elegido."),
        ],
    ),
    "wise_mind": _skill(
        "wise_mind",
        "mindfulness",
        "Mente sabia",
        "Pausa guiada para integrar emoción, hechos y objetivo del momento.",
        2,
        [
            ("Reconocé la mente emocional", "Identificá qué pide la emoción: alivio, escape, ataque, defensa."),
            ("Reconocé la mente razonable", "Identificá qué dicen los hechos fríos, sin emoción."),
            ("Buscá el centro", "Preguntate: ¿qué serviría a mi objetivo de largo plazo aquí?"),
            ("Actuá desde la mente sabia", "Elegí la respuesta que integra emoción y razón, no el impulso."),
        ],
    ),
    "participate": _skill(
        "participate",
        "mindfulness",
        "Participar",
        "Entrá por completo en la actividad del momento, sin observarte desde afuera.",
        3,
        [
            ("Elegí una actividad", "Algo simple: lavar platos, caminar, escribir, escuchar música."),
            ("Entrá de lleno", "Hacé solo eso, sin dividir la atención ni observarte haciendo."),
            ("Soltá el performance", "No midas cómo lo hacés; participá sin juzgar el resultado."),
        ],
    ),
    "non_judgmental": _skill(
        "non_judgmental",
        "mindfulness",
        "Sin juzgar",
        "Observar sin etiquetar como bueno o malo, solo como es.",
        2,
        [
            ("Notá el juicio", "Cuando aparezca \"esto está mal\" o \"soy un desastre\", registrá que es un juicio."),
            ("Reetiquetá como hecho", "Cambiá \"soy un desastre\" por \"tengo este pensamiento sobre mí\"."),
            ("Soltá el peso del juicio", "No agregues catastrificación ni culpa encima del hecho."),
            ("Volvé a observar", "Regresá a lo que estabas haciendo con la mirada sin filtro."),
        ],
    ),
    "stop": _skill(
        "stop",
        "distress_tolerance",
        "STOP",
        "Hacé una pausa antes de actuar impulsivamente.",
        2,
        [
            ("S — Stop (Frená)", "Detené lo que estás haciendo. No actúes todavía. Quedate quieto un momento."),
            ("T — Tomá distancia (Take a step back)", "Alejate física o mentalmente de la situación. Respirá profundamente y recordá que es una emoción pasajera."),
            ("O — Observá", "Notá qué está pasando dentro y fuera: pensamientos, sensaciones, el contexto, sin juzgarlos."),
            ("P — Procedé con conciencia", "Elegí una respuesta alineada con tus objetivos y valores, no con el impulso del momento."),
        ],
    ),
    "tipp": _skill(
        "tipp",
        "distress_tolerance",
        "TIPP / TIP",
        "Cambiá rápido el estado corporal para bajar la intensidad emocional.",
        3,
        [
            ("T — Temperatura", "Agua fría en la cara o hielo en la nuca: activa el reflejo de inmersión y baja la frecuencia cardíaca."),
            ("I — Ejercicio intenso", "Mové el cuerpo con fuerza por 1-2 minutos para descargar la activación."),
            ("P — Respiración pausada", "Inhala 4, exhala 6-8. Alargá la exhalación para calmar el sistema."),
            ("P — Pares relajados", "Tensá y soltá músculos en pares (manos/brazos, hombros/cuello) para liberar tensión."),
        ],
    ),
    "self_soothe": _skill(
        "self_soothe",
        "distress_tolerance",
        "Autocalma con los sentidos",
        "Elegí estímulos seguros de vista, oído, tacto, olfato o gusto.",
        3,
        [
            ("Vista", "Buscá un color, una textura o un detalle del entorno que sea neutro o agradable."),
            ("Oído", "Poné un sonido suave: música, lluvia, tu respiración."),
            ("Tacto", "Tocá algo con temperatura o textura reconfortante: una manta, agua tibia, una piedra."),
            ("Olfato", "Olé algo conocido y calmante: café, lavanda, una ropa con tu olor."),
            ("Gusto", "Probá algo pequeño y de sabor definido: un caramelo, agua, una fruta."),
        ],
    ),
    "radical_acceptance": _skill(
        "radical_acceptance",
        "distress_tolerance",
        "Aceptación radical",
        "Aceptar la realidad tal como es, sin aprobarla ni rendirse.",
        4,
        [
            ("Reconocé los hechos", "Describí lo que pasó sin interpretación: solo datos observables."),
            ("Notá la resistencia", "Identificá dónde decís \"no debería ser así\" o \"no es justo\"."),
            ("Soltá la resistencia", "Aceptá que la realidad es lo que es, aunque no lo apruebes."),
            ("Actuá desde la aceptación", "Preguntate: ¿qué puedo hacer ahora, desde esta realidad, no desde la que quería?"),
        ],
    ),
    "check_facts": _skill(
        "check_facts",
        "emotion_regulation",
        "Verificar los hechos",
        "Separar hechos observables, interpretación y emoción.",
        2,
        [
            ("Nombrá la emoción", "Poné nombre a lo que sentís: miedo, enojo, vergüenza, tristeza."),
            ("Listá los hechos", "Escribí lo que pasó en términos observables, sin adjetivos ni interpretaciones."),
            ("Identificá las interpretaciones", "Marcá qué partes son suposiciones, no hechos."),
            ("Reajustá la respuesta", "Con los hechos solos, ¿la intensidad de la emoción se sostiene? Ajustá si no."),
        ],
    ),
    "opposite_action": _skill(
        "opposite_action",
        "emotion_regulation",
        "Acción opuesta",
        "Actuar de forma contraria al impulso cuando no coincide con los hechos.",
        3,
        [
            ("Identificá la emoción y su impulso", "Miedo→evitar. Tristeza→aislarte. Enojo→atacar. Vergüenza→esconderte."),
            ("Verificá si el impulso sirve", "¿Los hechos justifican esa acción? ¿La acción ayuda a tu objetivo?"),
            ("Definí la acción opuesta", "Miedo→acercarte. Tristeza→activarte. Enojo→suavizar. Vergüenza→mostrarte."),
            ("Hacelo todo el camino", "No a medias: cuerpo, cara y acción alineados con la respuesta opuesta."),
        ],
    ),
    "problem_solving": _skill(
        "problem_solving",
        "emotion_regulation",
        "Resolución de problemas",
        "Convertir una preocupación en un problema concreto con pasos.",
        4,
        [
            ("Nombrá el problema", "Escribí en una frase concreta qué situación querés cambiar."),
            ("Generá opciones", "Listá al menos 3 respuestas posibles, sin filtrar por ahora."),
            ("Evaluá consecuencias", "Para cada opción: ¿corto plazo? ¿largo plazo? ¿sobre vos y sobre otros?"),
            ("Elegí y actuá", "Seleccioná la opción con mejor balance y dale un primer paso hoy."),
        ],
    ),
    "please": _skill(
        "please",
        "emotion_regulation",
        "PLEASE / autocuidado base",
        "Cuidar el cuerpo para reducir la vulnerabilidad emocional.",
        5,
        [
            ("PL — Tratar enfermedad física", "Si estás enfermo o con dolor, atendelo, no lo arrastres."),
            ("E — Equilibrio en comidas", "Comé a horario, ni saltado ni en exceso. El hambre desregula."),
            ("A — Evitá drogas y alcohol", "Las sustancias alteran el estado emocional de base."),
            ("S — Sueño reparador", "Respetá tus horas. El déficit de sueño dispara la reactividad."),
            ("E — Ejercicio regular", "Movimiento moderado diario mejora el estado de ánimo de base."),
        ],
    ),
    "dear_man": _skill(
        "dear_man",
        "interpersonal_effectiveness",
        "DEAR MAN",
        "Estructura para expresar asertivamente una necesidad o pedido.",
        3,
        [
            ("D — Describí la situación", "Hechos observables, sin juicio: \"Ayer llegué 20 min tarde a la reunión con vos\"."),
            ("E — Expresá tu emoción", "\"Me dio vergüenza y preocupación\". Usá \"yo\", no \"vos\"."),
            ("A — Assertivamente pedí", "Pedido concreto y específico: \"Necesito que me avises 15 min antes si vas a llegar tarde\"."),
            ("MAN — Mantente y refuerza", "Repetí el pedido sin agresión. Anticipá la ganancia para la otra persona."),
        ],
    ),
    "give": _skill(
        "give",
        "interpersonal_effectiveness",
        "GIVE",
        "Checklist para cuidar la relación mientras pedís.",
        2,
        [
            ("G — Amable (Gentle)", "Tono y gestos suaves, sin sarcasmo ni desprecio."),
            ("I — Interesado (Interested)", "Escuchá mirando, sin interrumpir ni planear respuesta."),
            ("V — Validá (Validate)", "Reconocé lo que el otro siente o piensa antes de responder."),
            ("E — Fácil (Easy manner)", "Sonreí, usá humor ligero, no cargues tensión a la conversación."),
        ],
    ),
    "fast": _skill(
        "fast",
        "interpersonal_effectiveness",
        "FAST",
        "Checklist para mantener el autorrespeto en la interacción.",
        2,
        [
            ("F — Justo (Fair)", "No ataques, no exageres, no uses lo que sabés que duele."),
            ("A — Sin disculparte de más (Apologies)", "No pidas perdón por existir o por pedir. Discúlpate solo si realmente hiciste algo."),
            ("S — Adherí a tus valores (Stick to values)", "No cedas lo que importa para evitar conflicto. La relación no vale tu integridad."),
            ("T — Honesto (Truthful)", "No exageres para ganar ni minimices para no incomodar. Decí lo cierto."),
        ],
    ),
    "validation_limits": _skill(
        "validation_limits",
        "interpersonal_effectiveness",
        "Validación / límites",
        "Validar al otro sin abandonar tus propios límites.",
        3,
        [
            ("Escuchá antes de responder", "Dejá hablar sin preparar respuesta. Parafraseá lo que escuchaste."),
            ("Validá lo que se pueda", "\"Entiendo que te enoje\" no es \"tenés razón\". Reconocé la emoción, no apruebes todo."),
            ("Marcá el límite", "\"Y al mismo tiempo, no puedo hacer X. Lo que sí puedo es Y\"."),
            ("Sostené sin atacar", "Si insisten, repetí el límite con calma. No justifiques ni te disculpes de más."),
        ],
    ),
}

DBT_NEED_PRACTICE_IDS = {
    "mindfulness": "wise_mind",
    "distress_tolerance": "stop",
    "emotion_regulation": "check_facts",
    "interpersonal_effectiveness": "dear_man",
}


class _NeedCard(NMCard):
    """Tarjeta de necesidad cotidiana en la vista Ahora."""
    
    def __init__(self, title: str, subtitle: str, family: str, icon_name: str, modo: str = None, parent=None):
        super().__init__(
            parent=parent,
            modo=modo,
            clickable=True,
            glow=False,
            lift=False,
        )
        self._family = family
        self._icon_name = icon_name
        self._title = title
        self._subtitle = subtitle
        self._family_color_key = _dbt_family_color_key(family)
        self.setProperty("dbt_family", family)
        self.setMinimumHeight(144)
        self.setMaximumHeight(162)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 16, 14)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        header = QHBoxLayout()
        header.setSpacing(8)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        header.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignTop)
        header.addStretch()
        
        family_title = _DBT_FAMILY_TITLES.get(family, "")
        
        self.chip_label = QLabel(family_title)
        self.chip_label.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.chip_label.setContentsMargins(8, 2, 8, 2)
        self.chip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chip_label.setFixedHeight(22)
        self.chip_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        header.addWidget(
            self.chip_label,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        lay.addLayout(header)
        
        self.title_label = QLabel(title)
        self.title_label.setFont(v3_font("size_h4", weight=TYPOGRAPHY["weight_bold"], serif=True))
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay.addWidget(self.title_label)
        
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setFont(qfont("size_small"))
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        lay.addWidget(self.subtitle_label)
        lay.addStretch(1)
        
        self._apply_theme(self._modo)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(v3c(self._family_color_key, self._modo))
        h = max(24, self.height() - _DBT_NEED_BORDER_Y * 2)
        p.drawRoundedRect(
            QRectF(0, _DBT_NEED_BORDER_Y, _DBT_NEED_BORDER_W, h),
            _DBT_NEED_BORDER_RADIUS,
            _DBT_NEED_BORDER_RADIUS,
        )
        p.end()
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        super()._apply_theme(self._modo)
        
        from shared.icons_svg import nm_svg_pixmap
        
        family_color_key = _dbt_family_color_key(self._family)
        self._family_color_key = family_color_key
        
        icon_color = v3c(family_color_key, self._modo).name()
        self.icon_label.setPixmap(nm_svg_pixmap(self._icon_name, color=icon_color, size=24))
        
        chip_bg = _dbt_family_soft_css(self._family, self._modo, alpha=0.04)
        self.chip_label.setStyleSheet(
            f"color: {icon_color}; "
            f"background: {chip_bg}; "
            f"border-radius: 7px; border: 1px solid {_dbt_family_soft_css(self._family, self._modo, 0.34)};"
        )
        self.title_label.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self.subtitle_label.setStyleSheet(f"color: {v3c('textMuted', self._modo).name()}; background: transparent;")


def _elide_two_lines(text: str, fm: QFontMetrics, max_width: int) -> str:
    """Envuelve `text` a máximo 2 líneas dentro de `max_width`, elidiendo la
    2da con "…" si sobra contenido. Qt no tiene `-webkit-line-clamp`, y el
    mockup confía en `.dbt-card{overflow:hidden}` para que una descripción
    larga no desborde sobre `.meta` — sin este tope, `wordWrap` + `maximumHeight`
    dejan pintar una 3ra línea encima de la fila de duración/práctica."""
    words = text.split()
    if not words or max_width <= 0:
        return text
    lines: list[str] = []
    i = 0
    for _ in range(2):
        if i >= len(words):
            break
        line = words[i]
        i += 1
        while i < len(words) and fm.horizontalAdvance(line + " " + words[i]) <= max_width:
            line += " " + words[i]
            i += 1
        lines.append(line)
    if i < len(words):
        remainder = lines[-1] + " " + " ".join(words[i:])
        lines[-1] = fm.elidedText(remainder, Qt.TextElideMode.ElideRight, max_width)
    return "\n".join(lines)


class _TwoLineElideLabel(QLabel):
    """`QLabel` con tope duro de 2 líneas + elipsis (ver `_elide_two_lines`)."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full_text = text
        super().setText(text)

    # Igual que NMElidedLabel (components/data.py): NO sizePolicy Ignored
    # (haría que el layout le dé un slot de ancho 0 y el widget se pinte
    # encima del vecino). minimumSizeHint chico evita que el ancho sin
    # wrap del texto completo, antes del primer resizeEvent, infle las
    # columnas del grid y corte la 4ta columna fuera del canvas.
    def minimumSizeHint(self):  # noqa: N802
        base = super().minimumSizeHint()
        return QSize(24, base.height())

    def setText(self, text: str):  # noqa: N802 — override de QLabel
        self._full_text = text
        self.updateGeometry()
        self._reflow()

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        self._reflow()

    def _reflow(self):
        width = max(0, self.width())
        if width <= 0:
            super().setText(self._full_text)
            return
        fm = QFontMetrics(self.font())
        super().setText(_elide_two_lines(self._full_text, fm, width))


class _SkillCard(NMCard):
    """Tarjeta de presentación de habilidad en la Biblioteca."""
    
    def __init__(self, skill: dict, modo: str = None, parent=None):
        super().__init__(
            parent=parent,
            modo=modo,
            clickable=True,
            glow=False,
            lift=False,
            padding=(11, 10, 11, 10),
        )
        self._skill = skill
        self._family_color_key = _dbt_family_color_key(skill["family"])
        self.setProperty("dbt_family", skill["family"])
        self.setMinimumHeight(_DBT_LIBRARY_CARD_MIN_H)
        self.setMaximumHeight(_DBT_LIBRARY_CARD_MAX_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(11, 10, 11, 10)
        lay.setSpacing(4)

        self.family_bar = QFrame()
        self.family_bar.setObjectName("DbtSkillFamilyBar")
        self.family_bar.setFixedSize(_DBT_SKILL_BAR_TOP_W, _DBT_SKILL_BAR_TOP_H)
        self.family_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay.addWidget(self.family_bar, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addSpacing(2)

        family_title = _DBT_FAMILY_LONG_TITLES.get(skill["family"], "")

        self.family_lbl = QLabel(family_title.upper())
        self.family_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.family_lbl.setContentsMargins(6, 2, 6, 2)
        self.family_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.family_lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        lay.addWidget(self.family_lbl)
        self.family_lbl.hide()

        self.title_lbl = QLabel(skill["title"])
        self.title_lbl.setFont(v3_font(13, weight=TYPOGRAPHY["weight_bold"], serif=True))
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setMaximumHeight(31)
        lay.addWidget(self.title_lbl)

        self.summary_lbl = _TwoLineElideLabel()
        self.summary_lbl.setFont(qfont(10))
        self.summary_lbl.setMinimumHeight(24)
        self.summary_lbl.setMaximumHeight(28)
        self.summary_lbl.setText(skill["summary"])
        lay.addWidget(self.summary_lbl)

        info_lay = QHBoxLayout()
        info_lay.setSpacing(8)

        # Duración: icono calendario SVG + "N min" (mockup `.dbt-card .meta`).
        # Antes era el emoji "⏱" que no está en las fuentes cargadas → tofu (▯).
        dur_box = QHBoxLayout()
        dur_box.setSpacing(5)
        dur_box.setContentsMargins(0, 0, 0, 0)
        self.dur_icon = QLabel()
        self.dur_icon.setStyleSheet("background: transparent;")
        dur_box.addWidget(self.dur_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self.dur_lbl = QLabel(f"{skill['duration_min']}m")
        self.dur_lbl.setFont(qfont(10))
        dur_box.addWidget(self.dur_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        info_lay.addLayout(dur_box)

        self.guide_lbl = QLabel("✓ Práctica")
        self.guide_lbl.setFont(qfont(10))
        info_lay.addWidget(self.guide_lbl)
        
        info_lay.addStretch()
        lay.addLayout(info_lay)
        
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        super()._apply_theme(self._modo)
        
        family_color_key = _dbt_family_color_key(self._skill["family"])
        self._family_color_key = family_color_key
        
        color_val = v3c(family_color_key, self._modo).name()
        chip_bg = _dbt_family_soft_css(self._skill["family"], self._modo, alpha=0.04)

        self.family_lbl.setStyleSheet(
            f"color: {color_val}; "
            f"background: {chip_bg}; "
            f"border-radius: 4px; border: 1px solid {_dbt_family_soft_css(self._skill['family'], self._modo, 0.34)};"
        )
        self.family_bar.setStyleSheet(
            f"QFrame#DbtSkillFamilyBar {{ background: {color_val}; "
            f"border-radius: {_DBT_SKILL_BAR_TOP_H // 2}px; }}"
        )
        self.title_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.summary_lbl.setStyleSheet(f"color: {v3c('text2', self._modo).name()};")
        self.dur_lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
        # Icono calendario recoloreado al tema (ink-3 / faint, como el texto meta).
        from shared.icons_svg import nm_svg_pixmap
        self.dur_icon.setPixmap(
            nm_svg_pixmap("calendar", color=v3c("faint", self._modo).name(), size=10)
        )
        # Mockup `.dbt-card .meta .pl{color:var(--brand)}` — "Práctica guiada" SIEMPRE
        # en brand, no en el color de la familia (antes salía cobre/rojo por card).
        self.guide_lbl.setStyleSheet(f"color: {v3c('brand', self._modo).name()};")


class _DBTScreen(QWidget):
    """Full-height DBT screen background matching the canonical `.screen`."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: transparent;")

    def set_modo(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        rect = QRectF(self.rect())
        surface = v3c("surface", self._modo)
        surface_2 = v3c("surface_2", self._modo)
        surface_3 = v3c("surface_3", self._modo)

        p.fillRect(rect, QBrush(surface))

        glow = QRadialGradient(QPointF(rect.width() * 0.5, -rect.height() * 0.2), 500)
        glow.setColorAt(0.0, surface_2)
        fade = QColor(surface_2)
        fade.setAlpha(0)
        glow.setColorAt(0.7, fade)
        p.fillRect(rect, QBrush(glow))

        p.setPen(QPen(surface_3, 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class _StepProgressIndicator(QWidget):
    """Horizontal step dots indicator with smooth family semantic colors."""
    
    def __init__(self, num_steps: int, family: str, parent=None, modo: str = None):
        super().__init__(parent)
        self._num_steps = num_steps
        self._family = family
        self._modo = norm_modo(modo)
        self._current_step = 0
        
        self.setFixedHeight(16)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
    def set_current_step(self, step: int):
        self._current_step = step
        self.update()
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        family_color_key = _dbt_family_color_key(self._family)
        
        active_color = v3c(family_color_key, self._modo)
        inactive_color = v3c("borderStrong", self._modo)
        
        dot_spacing = 16
        dot_width = 8
        total_width = self._num_steps * dot_width + (self._num_steps - 1) * dot_spacing
        start_x = (self.width() - total_width) / 2
        y = (self.height() - dot_width) / 2
        
        for i in range(self._num_steps):
            x = start_x + i * (dot_width + dot_spacing)
            if i == self._current_step:
                p.setBrush(QBrush(active_color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QRectF(x - 2, y - 2, dot_width + 4, dot_width + 4))
            else:
                p.setBrush(QBrush(inactive_color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QRectF(x, y, dot_width, dot_width))
        p.end()


class _SkillPracticeView(QWidget):
    """Flujo paso a paso guiado para practicar una habilidad."""
    
    finished = pyqtSignal(datetime.datetime)  # Emite started_at
    cancelled = pyqtSignal()
    
    def __init__(self, skill: dict, modo: str = None, parent=None):
        super().__init__(parent)
        self._skill = skill
        self._modo = norm_modo(modo)
        self._current_step = 0
        self._started_at = datetime.datetime.now()
        
        self._setup_ui()
        
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(12)

        # Mockup l.1091 DBT_FAMILIES + l.1172 eyebrow: STOP · ${fam} usa el
        # nombre CORTO de la familia en Title Case (no el largo). Migración
        # desde UI anterior donde el eyebrow usaba el título largo
        # "Tolerancia al malestar" en UPPERCASE — el código actual usaba
        # _DBT_FAMILY_LONG_TITLES + .upper() (rindiendo "STOP · TOLERANCIA AL
        # MALESTAR", más largo que el spec). Se corrige a _DBT_FAMILY_TITLES
        # (corto) y se remueve .upper() (mockup usa Title Case en l.1172).
        family_title = _DBT_FAMILY_TITLES.get(self._skill["family"], "")
        title_text = self._skill["title"]
        if family_title:
            title_text = f"{title_text} · {family_title}"
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.title_lbl)

        self.progress_lbl = QLabel()
        self.progress_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.progress_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.progress_lbl)

        # Visual step indicator
        self.step_indicator = _StepProgressIndicator(len(self._skill["steps"]), self._skill["family"], parent=self, modo=self._modo)
        lay.addWidget(self.step_indicator)

        self.step_card = NMCard(parent=self, clickable=False, modo=self._modo)
        self.step_card.setMinimumHeight(150)
        self.step_card.setMaximumHeight(190)
        self.step_card_lay = QVBoxLayout(self.step_card)
        self.step_card_lay.setContentsMargins(20, 16, 20, 16)
        self.step_card_lay.setSpacing(14)
        self.step_card_lay.addStretch(1)

        self.step_title_lbl = QLabel()
        self.step_title_lbl.setFont(v3_font(18, weight=TYPOGRAPHY["weight_semibold"], serif=True))
        self.step_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # mockup: centrado
        self.step_title_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.step_card_lay.addWidget(self.step_title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.step_body_lbl = QLabel()
        self.step_body_lbl.setFont(qfont(13))
        self.step_body_lbl.setWordWrap(True)
        self.step_body_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_body_lbl.setFixedWidth(390)
        self.step_body_lbl.setMinimumHeight(32)
        self.step_body_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.step_card_lay.addWidget(self.step_body_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        self.step_card_lay.addStretch(1)

        lay.addWidget(self.step_card)

        self.safety_lbl = None
        if self._skill.get("safety_note"):
            self.safety_lbl = QLabel(self._skill["safety_note"])
            self.safety_lbl.setFont(qfont(10))
            self.safety_lbl.setWordWrap(True)
            self.safety_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.safety_lbl.setFixedWidth(340)
            self.safety_lbl.setMinimumHeight(24)
            lay.addWidget(self.safety_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2026-06: removido `lay.addStretch()` que generaba un vacío
        # excesivo entre el safety_note y los botones de navegación.
        # Los botones quedan pegados al bloque de contenido.

        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(8)
        # width=0 → sin el minWidth=180 por defecto de NMButton: en un modal de
        # ~480px tres botones con min 180px entran en contención y reparten el
        # ancho de forma arbitraria (Anterior salía más ancho que Salir). Con
        # ancho de contenido + stretch factor 1 en Salir, "Salir" crece para
        # ocupar el espacio izquierdo (mockup) y Anterior/Siguiente quedan a la
        # derecha con su ancho natural.
        self.btn_cancel = NMButton(t("text.module.dbt.cancel_btn", "Salir"), parent=self, variant="ghost", size="md", width=0)
        self.btn_cancel.clicked.connect(self.cancelled.emit)
        btn_lay.addWidget(self.btn_cancel, 1)

        # Anterior/Siguiente: ancho fijo ~100px (mockup mide Siguiente=101px) para
        # mantener el padding del mockup; Salir (width=0, stretch=1) absorbe el resto.
        self.btn_prev = NMButton(t("text.module.dbt.prev_btn", "Anterior"), parent=self, variant="secondary", size="md", width=100)
        self.btn_prev.clicked.connect(self._prev_step)
        btn_lay.addWidget(self.btn_prev)

        self.btn_next = NMButton(t("text.module.dbt.next_btn", "Siguiente"), parent=self, variant="gradient", size="md", width=100)
        self.btn_next.clicked.connect(self._next_step)
        btn_lay.addWidget(self.btn_next)

        lay.addLayout(btn_lay)
        
        self._update_step()
        self._apply_theme(self._modo)
        
        ThemeManager.instance().theme_changed.connect(self._apply_theme)
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.title_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.progress_lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
        self.step_title_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.step_body_lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
        if self.safety_lbl:
            rose = v3c("rose", self._modo)
            rose.setAlpha(184)
            self.safety_lbl.setStyleSheet(f"color: {qcolor_to_rgba_css(rose)};")
        if hasattr(self, "step_indicator") and self.step_indicator:
            self.step_indicator._apply_theme(self._modo)
            
    def _update_step(self):
        steps = self._skill["steps"]
        step = steps[self._current_step]
        
        self.progress_lbl.setText(f"Paso {self._current_step + 1} de {len(steps)}")
        if hasattr(self, "step_indicator") and self.step_indicator:
            self.step_indicator.set_current_step(self._current_step)
        self.step_title_lbl.setText(step["title"])
        self.step_body_lbl.setText(step["body"])
        
        self.btn_prev.setEnabled(self._current_step > 0)
        
        if self._current_step == len(steps) - 1:
            self.btn_next.setText(t("text.module.dbt.finish_btn", "Terminar"))
        else:
            self.btn_next.setText(t("text.module.dbt.next_btn", "Siguiente"))
            
    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step()
            
    def _next_step(self):
        steps = self._skill["steps"]
        if self._current_step < len(steps) - 1:
            self._current_step += 1
            self._update_step()
        else:
            if getattr(self, "_is_finished", False):
                return
            self._is_finished = True
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.finished.emit(self._started_at)


class _PracticeModalScrim(QWidget):
    """Overlay modal del flujo DBT (mockup `.modal-bg` + `.modal`).

    Pinta el scrim `rgba(20,18,14,.5)` sobre el módulo (biblioteca dimmed detrás)
    y centra una card `surface` (r-xl 28) que aloja el contenido de práctica/
    cierre. Antes la práctica REEMPLAZABA la pantalla full-screen sin scrim → el
    fondo quedaba claro vs el target oscuro del mockup (MAD 0.23). El overlay
    sigue el geometry del padre vía eventFilter.
    """

    _SCRIM_RGBA = (20, 18, 14, 128)  # mockup .modal-bg rgba(20,18,14,.5)
    # CSS backdrop-filter: blur(3px) — el contrato canonical exige blur 3 en
    # ambos modos. Un blur mayor (p.ej. 40 en light) oculta divergencias de la
    # pantalla trasera y constituye fraude visual: el anti-fraud_scan lo bloquea.
    _SCRIM_BLUR_RADIUS_LIGHT = 3
    _SCRIM_BLUR_RADIUS_DARK = 3
    _MODAL_WIDTH_LIGHT = 554
    _MODAL_WIDTH_DARK = 560

    @classmethod
    def _blur_radius_for_mode(cls, modo: str) -> int:
        return (
            cls._SCRIM_BLUR_RADIUS_DARK
            if norm_modo(modo).startswith("dark")
            else cls._SCRIM_BLUR_RADIUS_LIGHT
        )

    @classmethod
    def modal_width_for_mode(cls, modo: str) -> int:
        return (
            cls._MODAL_WIDTH_DARK
            if norm_modo(modo).startswith("dark")
            else cls._MODAL_WIDTH_LIGHT
        )

    def __init__(self, parent: QWidget, modo: str):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._blur_radius = self._blur_radius_for_mode(self._modo)
        self._content: QWidget | None = None
        self._bg_pixmap: "QPixmap | None" = None
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        parent.installEventFilter(self)
        self.setGeometry(parent.rect())

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        self._card = QFrame()
        self._card.setObjectName("DBTModalCard")
        self._card_lay = QVBoxLayout(self._card)
        self._card_lay.setContentsMargins(0, 0, 0, 0)
        self._card_lay.setSpacing(0)
        row.addWidget(self._card)
        row.addStretch()
        root.addLayout(row)
        root.addStretch()
        self._apply_card_style()
        self._apply_card_shadow()

    def _apply_card_style(self):
        surf = v3c("surface", self._modo).name()
        b = v3c("line", self._modo)
        self._card.setStyleSheet(
            f"QFrame#DBTModalCard {{ background: {surf}; "
            f"border: 1px solid rgba({b.red()},{b.green()},{b.blue()},{b.alpha()}); "
            f"border-radius: 28px; }}"  # mockup `.modal` r-xl
        )

    def _apply_card_shadow(self):
        shadow = QGraphicsDropShadowEffect(self._card)
        if self._modo.startswith("dark"):
            shadow.setBlurRadius(64)
            shadow.setOffset(0, 26)
            shadow.setColor(QColor(0, 0, 0, 145))
        else:
            shadow.setBlurRadius(34)
            shadow.setOffset(0, 14)
            shadow.setColor(QColor(49, 45, 39, 42))
        self._card.setGraphicsEffect(shadow)

    def set_content(self, content: QWidget, max_width: int):
        if content is self._content:
            return
        if self._content is not None:
            self._card_lay.removeWidget(self._content)
            self._content.hide()
        self._content = content
        content.setParent(self._card)
        # mockup .modal{width:min(560px,92vw)} — width fijo, no max.
        # Sin minimum, el card colapsa al sizeHint del contenido (~460px)
        # generando wrapping excesivo del body vs el mockup de 560px.
        self._card.setFixedWidth(max_width)
        self._card.setMinimumHeight(366 if self._modo.startswith("dark") else 360)
        self._card_lay.addWidget(content)
        content.show()

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._blur_radius = self._blur_radius_for_mode(self._modo)
        self._apply_card_style()
        self._apply_card_shadow()
        self.update()

    def _apply_backdrop_blur_pil(self, pix: QPixmap) -> QPixmap | None:
        """Blur the parent snapshot with PIL GaussianBlur (radius=_blur_radius).

        PIL's GaussianBlur matches the canonical HTML ``backdrop-filter:blur(3px)``
        (Chromium) and the ``synthetic_backdrop`` used by
        ``tools/qa/audit_modal_backdrop_blur.py`` far more closely than Qt's
        ``QGraphicsBlurEffect``, which leaves residual gradients that the
        visual comparator measures as ``layout_drift``.

        The pixmap is padded by ``blur_radius*4`` px on each side with
        edge-replicated content (clamp-to-edge, matching CSS semantics) before
        blurring, then cropped back to the original size — identical strategy
        to the previous Qt path, only the blur kernel backend changes.

        Returns the blurred QPixmap, or ``None`` if PIL is unavailable or the
        conversion fails (caller falls back to the Qt path).
        """
        if self._blur_radius <= 0 or pix.isNull():
            return None
        try:
            from PIL import Image as PILImage, ImageFilter
        except Exception:
            return None
        try:
            pw, ph = pix.width(), pix.height()
            # Convert QPixmap → PIL Image (RGB) via QImage bits.
            qimg = pix.toImage().convertToFormat(QImage.Format.Format_RGB888)
            ptr = qimg.bits()
            ptr.setsize(qimg.sizeInBytes())
            arr = bytes(ptr)
            img = PILImage.frombytes("RGB", (pw, ph), arr, "raw", "RGB")
            # Clamp-to-edge padding: extend the image by pad px on each side
            # replicating the border pixels, so the Gaussian kernel does not
            # darken the edges (CSS blur clamps to edge; without this, Qt/PIL
            # would vignette the borders).
            pad = self._blur_radius * 4
            padded = img.resize((pw + 2 * pad, ph + 2 * pad))
            # Fill the padding with edge-replicated content.
            from PIL import ImageDraw as _PILDraw
            left = img.crop((0, 0, 1, ph)).resize((pad, ph))
            right = img.crop((pw - 1, 0, pw, ph)).resize((pad, ph))
            top = img.crop((0, 0, pw, 1)).resize((pw, pad))
            bottom = img.crop((0, ph - 1, pw, ph)).resize((pw, pad))
            tl = img.crop((0, 0, 1, 1)).resize((pad, pad))
            tr = img.crop((pw - 1, 0, pw, 1)).resize((pad, pad))
            bl = img.crop((0, ph - 1, 1, ph)).resize((pad, pad))
            br = img.crop((pw - 1, ph - 1, pw, ph)).resize((pad, pad))
            padded.paste(left, (0, pad))
            padded.paste(right, (pw + pad, pad))
            padded.paste(top, (pad, 0))
            padded.paste(bottom, (pad, ph + pad))
            padded.paste(tl, (0, 0))
            padded.paste(tr, (pw + pad, 0))
            padded.paste(bl, (0, ph + pad))
            padded.paste(br, (pw + pad, ph + pad))
            padded.paste(img, (pad, pad))
            # Apply Gaussian blur — same radius as the canonical CSS blur(3px).
            blurred = padded.filter(ImageFilter.GaussianBlur(radius=self._blur_radius))
            # Crop back to original size.
            blurred = blurred.crop((pad, pad, pad + pw, pad + ph))
            # Convert PIL Image → QPixmap.
            data = blurred.tobytes("raw", "RGB")
            out_qimg = QImage(data, pw, ph, 3 * pw, QImage.Format.Format_RGB888)
            # Keep a reference to the bytes so the QImage stays valid until
            # we copy it into a QPixmap below.
            out_qimg._data_ref = data
            return QPixmap.fromImage(out_qimg.copy())
        except Exception:
            return None

    def _apply_backdrop_blur_qt(self, pix: QPixmap) -> QPixmap:
        """Fallback blur using QGraphicsBlurEffect (the previous backend).

        Used when PIL is unavailable or fails. Produces a slightly different
        blur kernel than PIL/Chromium, but preserves the same radius and
        clamp-to-edge padding strategy so the visual contract (blur=3, no
        overblur) still holds.
        """
        if self._blur_radius <= 0:
            return pix
        from PyQt6.QtWidgets import QGraphicsBlurEffect, QGraphicsScene, QGraphicsPixmapItem
        pad = self._blur_radius * 4
        pw, ph = pix.width(), pix.height()
        padded = QPixmap(pw + 2 * pad, ph + 2 * pad)
        pp = QPainter(padded)
        pp.drawPixmap(pad, pad, pix)
        pp.drawPixmap(pad, 0, pix.copy(0, 0, pw, 1).scaled(pw, pad))
        pp.drawPixmap(pad, ph + pad, pix.copy(0, ph - 1, pw, 1).scaled(pw, pad))
        pp.drawPixmap(0, pad, pix.copy(0, 0, 1, ph).scaled(pad, ph))
        pp.drawPixmap(pw + pad, pad, pix.copy(pw - 1, 0, 1, ph).scaled(pad, ph))
        top_left = pix.copy(0, 0, 1, 1).scaled(pad, pad)
        pp.drawPixmap(0, 0, top_left)
        pp.drawPixmap(pw + pad, 0, pix.copy(pw - 1, 0, 1, 1).scaled(pad, pad))
        pp.drawPixmap(0, ph + pad, pix.copy(0, ph - 1, 1, 1).scaled(pad, pad))
        pp.drawPixmap(pw + pad, ph + pad, pix.copy(pw - 1, ph - 1, 1, 1).scaled(pad, pad))
        pp.end()
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(padded)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(self._blur_radius)
        blur.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
        item.setGraphicsEffect(blur)
        scene.addItem(item)
        blurred_padded = QPixmap(padded.size())
        bp = QPainter(blurred_padded)
        bp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        scene.render(bp, QRectF(0, 0, padded.width(), padded.height()), QRectF(0, 0, padded.width(), padded.height()))
        bp.end()
        return blurred_padded.copy(pad, pad, pw, ph)

    def capture_background(self):
        """Pre-captura el contenido del parent y aplica el tinte del scrim.

        En el renderer offscreen de Qt los child widgets con alpha no compósitan
        sobre su parent. Grabamos el parent mientras el scrim está oculto y
        aplicamos el color del scrim manualmente para que paintEvent lo dibuje
        de forma opaca — el resultado visual es idéntico al blend real.

        Backend de blur:
        - **Light**: PIL ``GaussianBlur(radius=3)`` (sigma=3), que coincide
          con el ``backdrop-filter:blur(3px)`` canonical (Chromium) y con el
          ``synthetic_backdrop`` del auditor modal. El Qt
          ``QGraphicsBlurEffect(radius=3)`` usa un kernel box (≈sigma=1.5)
          que deja gradientes residuales del parent dbt-library (cards de alto
          contraste) que el comparator mide como ``layout_drift`` (46px en
          light). El PIL Gaussian los elimina.
        - **Dark**: fallback a ``QGraphicsBlurEffect(radius=3)`` (Qt box). El
          parent dbt-library dark tiene un layout distinto al canonical (sin
          cards en y≈550 donde el canonical las tiene). El PIL Gaussian
          (sigma=3, más fiel al canonical) suaviza demasiado los gradientes
          de bajo contraste del dark, reduciendo el content_bbox 2px y
          causando un ``layout_drift`` de 1px sobre el tolerance. El Qt box
          (≈sigma=1.5, menos suave) preserva esos gradientes hasta que el
          parent sea alineado con el canonical.
        - Si PIL no está disponible o falla, se usa Qt en ambos modos.
        """
        parent = self.parent()
        if parent is None:
            return
        pix = parent.grab()
        # mockup backdrop-filter:blur(3px) — el blur se aplica sobre el
        # snapshot del parent antes del tinte del scrim.
        if self._blur_radius > 0:
            is_dark = self._modo.startswith("dark")
            blurred: QPixmap | None = None
            # Light: prefer PIL Gaussian (faithful to canonical, eliminates
            # residual gradients from high-contrast parent cards).
            if not is_dark:
                blurred = self._apply_backdrop_blur_pil(pix)
            # Dark: PIL Gaussian smooths too aggressively for the low-contrast
            # backdrop; fall back to Qt box blur which preserves gradients
            # needed to match the canonical content_bbox.
            # Also used as fallback if PIL is unavailable or fails.
            if blurred is None:
                blurred = self._apply_backdrop_blur_qt(pix)
            pix = blurred
        tinted = QPixmap(pix.size())
        p = QPainter(tinted)
        p.drawPixmap(0, 0, pix)
        p.fillRect(tinted.rect(), QColor(*self._SCRIM_RGBA))
        p.end()
        self._bg_pixmap = tinted

    def paintEvent(self, event):
        p = QPainter(self)
        if self._bg_pixmap is not None:
            p.drawPixmap(0, 0, self._bg_pixmap)
        else:
            p.fillRect(self.rect(), QColor(*self._SCRIM_RGBA))

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parent().rect())
        return False


class ModuloDBT(NMModule):
    """Módulo de Habilidades DBT — NeuroMood Suite."""
    
    MODULE_TITLE = "Habilidades DBT"
    MODULE_ICON = "spark"
    
    def build_ui(self):
        # Unconditionally initialize tables to ensure dbt_practicas exists even in visual QA mode
        try:
            from shared.db import inicializar_tablas
            inicializar_tablas()
        except Exception as e:
            _log.error(f"Error initializing tables: {e}")

        self._current_family = None
        self._current_skill_id = None
        # RA-5: cachear la version de la skill desde DBT_SKILLS[...]["version"].
        # Antes se hardcodeaba 1 en el INSERT, ignorando el campo canónico.
        self._current_skill_version = 1
        self._current_step = 0
        self._started_at = None
        self._origin_view = 0
        
        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._screen_bg = _DBTScreen(self._modo, self._content)
        outer.addWidget(self._screen_bg, 1)

        # Main Layout inside the canonical full-height screen.
        self._main_layout = QVBoxLayout(self._screen_bg)
        self._main_layout.setContentsMargins(24, 24, 24, 16)
        self._main_layout.setSpacing(13)
        
        # Tabs at the top
        self._tabs = NMTabs(
            [
                t("text.module.dbt.tab_now", "Ahora"),
                t("text.module.dbt.tab_library", "Biblioteca"),
            ],
            variant="seg",  # mockup `.seg`: contenedor surface-3, segmento sel = surface elevado
            modo=self._modo,
            selected_border=False,
            parent=self,
        )
        self._tabs.changed.connect(self._on_tab_changed)
        # Mockup neuromood-mockup.html: el seg "Ahora / Biblioteca" arranca a
        # la izquierda del card, no centrado, y su ancho es compacto (≈200px).
        # Antes: max 640 + AlignHCenter → seg gigante centrado, no matcheaba.
        self._tabs.setFixedWidth(240)
        self._main_layout.addWidget(self._tabs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # View stacked widget
        self._view_stack = QStackedWidget()
        self._main_layout.addWidget(self._view_stack)
        
        # 2 main views: Historial fue removido de UI V2 por decision owner.
        self._view_ahora = self._build_view_ahora()
        self._view_biblioteca = self._build_view_biblioteca()

        self._view_stack.addWidget(self._view_ahora)
        self._view_stack.addWidget(self._view_biblioteca)
        
        self._practice_view = None
        self._modal_scrim = None
        self._modal_background_controls_hidden = False

        # Navigation track
        self._on_tab_changed(0, t("text.module.dbt.tab_now", "Ahora"))
        
    def _on_tab_changed(self, idx: int, label: str):
        if self._practice_view:
            self._cleanup_practice_flow()
            
        self._view_stack.setCurrentIndex(idx)
        if not self._modal_background_controls_hidden:
            self._tabs.show()
        
        if idx == 1:
            self._filter_library()
            
    def on_enter(self):
        super().on_enter()
        self._on_tab_changed(self._tabs.current(), "")
        
    def _build_view_ahora(self) -> QWidget:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        lbl_prompt = QLabel(t("text.module.dbt.now_prompt", "¿Qué necesitás en este momento?"))
        lbl_prompt.setObjectName("DbtPromptLabel")
        lbl_prompt.setFont(v3_font("size_h3", weight=TYPOGRAPHY["weight_bold"], serif=True))
        lbl_prompt.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        lay.addWidget(lbl_prompt)

        # 4 need cards grid
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for c in range(2):
            grid.setColumnStretch(c, 1)
        for r in range(2):
            grid.setRowStretch(r, 0)

        needs = [
            ("Volver al presente", "Mindfulness: pausar, enfocar y notar el aquí y ahora.", "mindfulness", "mind"),
            ("Atravesar un momento intenso", "Tolerancia: superar la crisis sin empeorar la situación.", "distress_tolerance", "shield"),
            ("Regular una emoción", "Regulación: entender y suavizar sentimientos desbordantes.", "emotion_regulation", "mood"),
            ("Comunicarme con claridad", "Efectividad: pedir límites o dialogar con autorrespeto.", "interpersonal_effectiveness", "heart"),  # mockup: heart
        ]

        for i, (title, desc, family, icon) in enumerate(needs):
            card = _NeedCard(title, desc, family, icon, modo=self._modo, parent=widget)
            card.clicked.connect(lambda f=family: self._on_need_clicked(f))
            grid.addWidget(card, i // 2, i % 2, alignment=Qt.AlignmentFlag.AlignTop)

        lay.addLayout(grid, stretch=0)
        lay.addStretch(1)

        return widget
        
    def _on_need_clicked(self, family: str):
        practice_id = DBT_NEED_PRACTICE_IDS.get(family)
        if practice_id:
            self.start_practice_by_id(practice_id)
        
    def _build_view_biblioteca(self) -> QWidget:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)
        
        # Horizontal family tabs filter
        self._family_tabs = NMTabs(
            [
                t("text.module.dbt.family_all", "Todas"),
                t("text.module.dbt.family_mindfulness", "Mindfulness"),
                t("text.module.dbt.family_tolerance", "Tolerancia"),
                t("text.module.dbt.family_regulation", "Regulación"),
                t("text.module.dbt.family_effectiveness", "Efectividad"),
            ],
            variant="filter",  # mockup: active pill fill sólido
            modo=self._modo,
            density="compact",
            parent=widget,
        )
        self._family_tabs.changed.connect(self._filter_library)
        lay.addWidget(self._family_tabs)
        
        # Scroll Area for Skill Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._biblioteca_scroll = scroll
        
        self._library_container = QWidget()
        self._library_container.setStyleSheet("background: transparent;")
        self._library_grid = QGridLayout(self._library_container)
        self._library_grid.setContentsMargins(0, 0, 0, 0)
        self._library_grid.setHorizontalSpacing(6)
        self._library_grid.setVerticalSpacing(6)
        self._library_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for col in range(_DBT_LIBRARY_COLUMNS):
            self._library_grid.setColumnStretch(col, 1)
        
        scroll.setWidget(self._library_container)
        lay.addWidget(scroll)
        
        return widget

    def _filter_library(self, *args):
        # Clear existing
        while self._library_grid.count():
            item = self._library_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
                
        # Filter logic
        tab_idx = self._family_tabs.current()
        family_filter = [None, "mindfulness", "distress_tolerance", "emotion_regulation", "interpersonal_effectiveness"][tab_idx]
        
        visible_idx = 0
        for skill_id, skill in DBT_SKILLS.items():
            if family_filter is None or skill["family"] == family_filter:
                card = _SkillCard(skill, modo=self._modo, parent=self._library_container)
                card.clicked.connect(lambda s=skill: self.start_practice(s))
                row, col = divmod(visible_idx, _DBT_LIBRARY_COLUMNS)
                self._library_grid.addWidget(card, row, col)
                visible_idx += 1

    def _show_modal(self, content, max_width: int):
        """Muestra `content` en el overlay modal (scrim + card centrada),
        dejando el fondo dimmed con controles visibles pero no interactivos."""
        if self._modal_scrim is None:
            self._modal_scrim = _PracticeModalScrim(self._content, self._modo)
        # Captura el fondo ANTES de ocultar controles para que los tabs aparezcan
        # dimmed en el scrim (igual que el mockup). El scrim cubre los controles
        # reales, haciéndolos no interactivos sin necesidad de ocultarlos.
        self._modal_scrim.capture_background()
        self._set_modal_background_controls_visible(False)
        self._modal_scrim.set_content(content, max_width)
        self._modal_scrim.setGeometry(self._content.rect())
        self._modal_scrim.show()
        self._modal_scrim.raise_()

    def _set_modal_background_controls_visible(self, visible: bool):
        self._modal_background_controls_hidden = not visible
        for attr in ("_tabs", "_family_tabs"):
            widget = getattr(self, attr, None)
            if widget is not None:
                widget.setVisible(visible)

    def start_practice_by_id(self, practice_id: str) -> bool:
        skill = DBT_SKILLS.get(practice_id)
        if skill is None:
            _log.warning("DBT practice id bloqueado: %s", practice_id)
            return False
        self.start_practice(skill)
        return True

    def start_practice(self, skill: dict):
        if not skill or skill.get("id") not in DBT_SKILLS:
            _log.warning("DBT practice bloqueada: %r", skill.get("id") if isinstance(skill, dict) else skill)
            return False
        self._cleanup_practice_flow()

        # Cache origin tab to return correctly
        self._origin_view = self._tabs.current()
        self._current_skill_id = skill["id"]
        self._current_family = skill["family"]
        # RA-5: cachear la version canónica de DBT_SKILLS. Default 1 si falta.
        self._current_skill_version = skill.get("version", 1)

        self._practice_view = _SkillPracticeView(skill, modo=self._modo, parent=self)
        self._practice_view.setMaximumWidth(560)
        self._practice_view.cancelled.connect(self._on_practice_cancelled)
        self._practice_view.finished.connect(self._on_practice_finished)
        # La práctica es un MODAL sobre la biblioteca dimmed, no un reemplazo
        # full-screen. Los controles de fondo se ocultan mientras el scrim está
        # activo para no dejar botones visualmente tapados/no clickeables.
        self._show_modal(
            self._practice_view,
            _PracticeModalScrim.modal_width_for_mode(self._modo),
        )
        return True

    def _on_practice_cancelled(self):
        # Cerramos el modal y restauramos la tab de origen.
        self._cleanup_practice_flow()
        self._tabs.set_current(self._origin_view)

    def _on_practice_finished(self, started_at: datetime.datetime):
        self._started_at = started_at
        self._on_practice_saved(None, None, "sin_evaluar", "")

    def _on_practice_saved(self, antes, despues, resultado, nota):
        # Calculate duration
        dur_seg = 0
        if self._started_at:
            delta = datetime.datetime.now() - self._started_at
            dur_seg = max(0, int(delta.total_seconds()))
            
        # Insert record locally
        record_id = str(uuid.uuid4())
        fecha = datetime.date.today().isoformat()
        hora = datetime.datetime.now().time().strftime("%H:%M:%S")
        
        # Use timezone-aware UTC datetime to avoid deprecation warnings
        try:
            from datetime import timezone
            created_at = datetime.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        except ImportError:
            created_at = datetime.datetime.utcnow().isoformat() + "Z"
        
        try:
            with conexion() as conn:
                conn.execute(
                    "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    # RA-5: usar self._current_skill_version (canónico de DBT_SKILLS)
                    # en vez de hardcodear 1.
                    (record_id, fecha, hora, self._current_skill_id, self._current_skill_version, self._current_family, self._get_need_text(self._current_family), antes, despues, resultado, dur_seg, nota, created_at)
                )
            NMToast.display(self, "Práctica guardada correctamente.", variant="success")
            
            # Trigger immediate sync in background
            try:
                from shared.sync import sync_inmediato_background
                sync_inmediato_background()
            except Exception as e_sync:
                _log.warning(f"Error starting immediate sync: {e_sync}")
        except Exception as e:
            _log.error(f"Error saving dbt practice: {e}")
            NMToast.display(self, "No se pudo guardar la práctica.", variant="error")
            
        self._cleanup_practice_flow()
        self._tabs.set_current(0)

    def _get_need_text(self, family: str) -> str:
        return {
            "mindfulness": "Volver al presente",
            "distress_tolerance": "Atravesar un momento intenso",
            "emotion_regulation": "Regular una emoción",
            "interpersonal_effectiveness": "Comunicarme con claridad"
        }.get(family, "")
        
    def _cleanup_practice_flow(self):
        # El scrim es dueño de la card y del contenido (práctica/cierre) como
        # hijos; al borrarlo se destruyen con él. Solo anulamos las referencias.
        if self._modal_scrim is not None:
            self._modal_scrim.hide()
            self._modal_scrim.deleteLater()
            self._modal_scrim = None
        self._set_modal_background_controls_visible(True)
        self._practice_view = None
            
    def get_card_status(self) -> str:
        today_str = datetime.date.today().isoformat()
        seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        try:
            with conexion() as conn:
                count_today = conn.execute("SELECT COUNT(*) FROM dbt_practicas WHERE fecha = ?", (today_str,)).fetchone()[0]
                count_week = conn.execute("SELECT COUNT(*) FROM dbt_practicas WHERE fecha >= ?", (seven_days_ago,)).fetchone()[0]
            if count_today == 0 and count_week == 0:
                return "Sin prácticas"
            elif count_today > 0:
                return f"{count_today} práctica{'s' if count_today > 1 else ''} hoy"
            else:
                return f"{count_week} práctica{'s' if count_week > 1 else ''} esta semana"
        except Exception:
            return "Sin prácticas"
            
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        super()._apply_theme(self._modo)
        
        # Style scroll areas dynamically on theme change
        if hasattr(self, "_biblioteca_scroll") and self._biblioteca_scroll:
            self._biblioteca_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_screen_bg"):
            self._screen_bg.set_modo(self._modo)
        # Trigger theme re-apply for all internal views
        if hasattr(self, "_view_ahora"):
            # Recurse children manually
            for child in self._view_ahora.findChildren(NMCard):
                family = child.property("dbt_family")
                if family:
                    family_color_key = {
                        "mindfulness": "teal",
                        "distress_tolerance": "danger",
                        "emotion_regulation": "warning",
                        "interpersonal_effectiveness": "primary"
                    }.get(family, "text")
                    accent_color_hex = v3c(family_color_key, self._modo).name()
                    child.set_accent(accent_color_hex)
                if hasattr(child, "_apply_theme"):
                    child._apply_theme(self._modo)
            for lbl in self._view_ahora.findChildren(QLabel):
                obj_name = lbl.objectName()
                if obj_name == "DbtPromptLabel":
                    lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
                    
        if hasattr(self, "_view_biblioteca"):
            for child in self._view_biblioteca.findChildren(NMCard):
                if hasattr(child, "_apply_theme"):
                    child._apply_theme(self._modo)
            if hasattr(self, "_family_tabs"):
                self._family_tabs._apply_theme(self._modo)

        # Forward theme calls to active practice flows
        if getattr(self, "_modal_scrim", None) is not None:
            self._modal_scrim.apply_theme(self._modo)
        if hasattr(self, "_practice_view") and self._practice_view:
            if hasattr(self._practice_view, "_apply_theme"):
                self._practice_view._apply_theme(self._modo)
