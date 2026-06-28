"""
app/modules/dbt_qt.py — Módulo Habilidades DBT (PyQt6)
Práctica guiada de habilidades DBT con vistas Ahora y Biblioteca.
"""

import os
import sys
import datetime
import uuid
import logging

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QEvent
from PyQt6.QtGui import QPainter, QBrush, QColor
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
_DBT_SKILL_BAR_TOP_W = 54
_DBT_SKILL_BAR_TOP_H = 5
_DBT_LIBRARY_CARD_MIN_H = 116
_DBT_LIBRARY_CARD_MAX_H = 122
_DBT_NEED_BORDER_W = 3  # mockup l.232: .need-card{border-left:3px solid var(--brand); ...}
_DBT_NEED_BORDER_Y = 14
_DBT_NEED_BORDER_RADIUS = 2.5


def _dbt_family_color_key(family: str) -> str:
    return _DBT_FAMILY_COLOR_KEYS.get(family, "text")


def _dbt_family_soft_css(family: str, modo: str, alpha: float = 0.14) -> str:
    c = QColor(v3c(_dbt_family_color_key(family), modo))
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return qcolor_to_rgba_css(c)


# Catálogo MVP: 8 habilidades divididas en 4 familias
DBT_SKILLS = {
    "mind_observe": {
        "id": "mind_observe",
        "version": 1,
        "family": "mindfulness",
        "title": "Observar y describir",
        "summary": "Notar sensaciones, pensamientos y entorno sin intentar corregirlos.",
        "duration_min": 2,
        "steps": [
            {
                "title": "Paso 1: Enfocá tu atención",
                "body": "Elegí un único objeto de atención (tu respiración, un sonido de tu entorno o una sensación física en tu cuerpo)."
            },
            {
                "title": "Paso 2: Observá sin juzgar",
                "body": "Limitá tu mente a registrar lo que percibe. Si surge un pensamiento como 'este ruido es molesto', reformulalo mentalmente a 'percibo un ruido fuerte'."
            },
            {
                "title": "Paso 3: Describí internamente",
                "body": "Ponele palabras sencillas a tu experiencia. Por ejemplo: 'Siento el aire frío al entrar por la nariz' o 'Noto tensión en los hombros'."
            }
        ],
        "safety_note": ""
    },
    "mind_wise": {
        "id": "mind_wise",
        "version": 1,
        "family": "mindfulness",
        "title": "Mente sabia",
        "summary": "Pausa guiada para integrar emoción, hechos y objetivo del momento.",
        "duration_min": 2,
        "steps": [
            {
                "title": "Paso 1: Mente emocional",
                "body": "¿Qué estás sintiendo ahora? Reconocé tus emociones sin juzgarlas. Date permiso para sentir lo que sentís."
            },
            {
                "title": "Paso 2: Mente racional",
                "body": "¿Cuáles son los hechos fríos? ¿Qué es objetivamente real en esta situación, dejando de lado las interpretaciones?"
            },
            {
                "title": "Paso 3: Integración",
                "body": "Respirá hondo. Buscá el punto de equilibrio en tu interior donde la razón y la emoción se encuentran. ¿Qué es lo más sabio que podés hacer ahora?"
            }
        ],
        "safety_note": ""
    },
    "distress_stop": {
        "id": "distress_stop",
        "version": 1,
        "family": "distress_tolerance",
        "title": "STOP",
        "summary": "Hacé una pausa antes de actuar impulsivamente.",
        "duration_min": 2,
        "steps": [
            {
                "title": "S — Stop (Frená)",  # mockup: em-dash
                # 2026-06-24: mockup l.1171 — copy alineado al mockup.
                # Antes era genérico; ahora es específico al paso S de STOP.
                "body": "Detené lo que estás haciendo. No actúes todavía. Quedate quieto por un momento."
            },
            {
                "title": "T — Tomá distancia (Take a step back)",  # mockup: em-dash
                # 2026-06-24: mockup l.1162 — "física" en lugar de "físicamente"
                "body": "Alejate física o mentalmente de la situación. Respirá profundamente y recordá que es una emoción pasajera."
            },
            {
                "title": "O — Observá (Observe)",  # mockup: em-dash
                # 2026-06-24: mockup l.1163 — copy alineado al mockup
                "body": "Notá qué está pasando dentro y fuera: pensamientos, sensaciones, el contexto, sin juzgarlos."
            },
            {
                # 2026-06-24: mockup l.1164 — title sin "(Proceed mindfully)" en
                # paréntesis (no está en el mockup).
                "title": "P — Procedé con conciencia",  # mockup: em-dash
                # 2026-06-24: mockup l.1164 — body alineado al mockup
                "body": "Elegí una respuesta alineada con tus objetivos y valores, no con el impulso del momento."
            }
        ],
        "safety_note": "Esta habilidad es un apoyo inmediato. Si sentís malestar extremo o peligro inminente, recurrí a asistencia profesional.",
    },
    "distress_senses": {
        "id": "distress_senses",
        "version": 1,
        "family": "distress_tolerance",
        "title": "Autocalma con los sentidos",
        "summary": "Elegí estímulos seguros de tu vista, oído, tacto, olfato o gusto.",
        "duration_min": 3,
        "steps": [
            {
                "title": "Vista",
                "body": "Buscá a tu alrededor algo agradable a la vista: una planta, el cielo, una foto querida o simplemente prestá atención a los colores de la habitación."
            },
            {
                "title": "Oído",
                "body": "Escuchá con atención. Puede ser música suave, el sonido del viento, el canto de un pájaro o el murmullo de fondo."
            },
            {
                "title": "Tacto",
                "body": "Tocá una textura reconfortante: la suavidad de una prenda, una taza de té tibia o acariciá a tu mascota."
            },
            {
                "title": "Olfato y Gusto",
                "body": "Percibí un aroma agradable (café, perfume, una flor) o saboreá algo despacio, sintiendo la textura y el sabor real."
            }
        ],
        "safety_note": ""
    },
    "emotion_facts": {
        "id": "emotion_facts",
        "version": 1,
        "family": "emotion_regulation",
        "title": "Verificar los hechos",
        "summary": "Separar hechos observables, interpretación y emoción.",
        "duration_min": 2,
        "steps": [
            {
                "title": "Paso 1: ¿Cuál es el evento detonante?",
                "body": "Describí la situación externa sin adjetivos subjetivos. ¿Quién hizo qué? ¿Qué pasó exactamente?"
            },
            {
                "title": "Paso 2: ¿Qué interpretaciones estás sumando?",
                "body": "¿Qué pensamientos o suposiciones estás haciendo sobre lo que pasó? Separalos de los hechos observables."
            },
            {
                "title": "Paso 3: ¿La emoción coincide con los hechos?",
                "body": "Preguntate: ¿La intensidad de mi emoción es proporcional a lo que realmente ocurrió, o está basada en mis interpretaciones y temores?"
            }
        ],
        "safety_note": ""
    },
    "emotion_opposite": {
        "id": "emotion_opposite",
        "version": 1,
        "family": "emotion_regulation",
        "title": "Acción opuesta",
        "summary": "Actuar de forma contraria al impulso cuando no coincide con los hechos.",
        "duration_min": 3,
        "steps": [
            {
                "title": "Paso 1: Identificá la emoción y el impulso",
                "body": "Por ejemplo: Si sentís miedo, el impulso es huir; si sentís enojo, el impulso es atacar; si sentís tristeza, el impulso es aislarte."
            },
            {
                "title": "Paso 2: Evaluá si el impulso ayuda",
                "body": "¿El impulso de acción es efectivo para resolver la situación o sólo sirve para intensificar la emoción?"
            },
            {
                "title": "Paso 3: Actúa de forma contraria",
                "body": "Hacé lo opuesto de manera total y comprometida. Si es miedo injustificado, enfrentalo; si es tristeza, actívate; si es enojo inútil, alejate amablemente."
            }
        ],
        "safety_note": ""
    },
    "interpersonal_dearman": {
        "id": "interpersonal_dearman",
        "version": 1,
        "family": "interpersonal_effectiveness",
        "title": "DEAR MAN",
        "summary": "Estructura para expresar asertivamente una necesidad o pedido.",
        "duration_min": 3,
        "steps": [
            {
                "title": "D - Describir & E - Expresar",
                "body": "Describí la situación objetivamente ('Llegaste tarde las últimas tres veces'). Expresá tus sentimientos claramente ('Me siento frustrado cuando espero')."
            },
            {
                "title": "A - Aseverar & R - Reforzar",
                "body": "Aseverá tu pedido o límite de forma clara y directa ('Te pido que me avises si vas a demorarte'). Reforzá explicando el beneficio mutuo ('Así nos organizamos mejor y evitamos discusiones')."
            },
            {
                "title": "M - Mantenerse consciente & A - Aparentar seguridad",
                "body": "Mantenete enfocado en tu objetivo sin desviarte. Hablá con calma, manteniendo contacto visual y un tono de voz firme."
            },
            {
                "title": "N - Negociar",
                "body": "Buscá soluciones alternativas si la otra persona no acepta tu propuesta original. Mantenete abierto a un acuerdo razonable."
            }
        ],
        "safety_note": ""
    },
    "interpersonal_givefast": {
        "id": "interpersonal_givefast",
        "version": 1,
        "family": "interpersonal_effectiveness",
        "title": "GIVE / FAST",
        "summary": "Checklist para cuidar la relación y mantener el autorrespeto.",
        "duration_min": 2,
        "steps": [
            {
                "title": "GIVE - Cuidar la relación",
                "body": "G - Gentil (sin juzgar), I - Interés (escuchar activamente), V - Validar (respetar los sentimientos del otro), E - Estilo fácil (con humor o calidez)."
            },
            {
                "title": "FAST - Mantener el autorrespeto",
                "body": "F - Firmeza ética (ser justo), A - Apologías mínimas (no disculparse por existir o tener necesidades), S - Sinceridad (no mentir ni exagerar), T - Tener valores (mantener tus principios)."
            }
        ],
        "safety_note": ""
    }
}


class _NeedCard(NMCard):
    """Tarjeta de necesidad cotidiana en la vista Ahora."""
    
    def __init__(self, title: str, subtitle: str, family: str, icon_name: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=True, glow=False)
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


class _SkillCard(NMCard):
    """Tarjeta de presentación de habilidad en la Biblioteca."""
    
    def __init__(self, skill: dict, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=True, glow=False)
        self._skill = skill
        self._family_color_key = _dbt_family_color_key(skill["family"])
        self.setProperty("dbt_family", skill["family"])
        self.setMinimumHeight(_DBT_LIBRARY_CARD_MIN_H)
        self.setMaximumHeight(_DBT_LIBRARY_CARD_MAX_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 18)
        lay.setSpacing(5)

        self.family_bar = QFrame()
        self.family_bar.setObjectName("DbtSkillFamilyBar")
        self.family_bar.setFixedSize(_DBT_SKILL_BAR_TOP_W, _DBT_SKILL_BAR_TOP_H)
        self.family_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay.addWidget(self.family_bar, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addSpacing(3)

        family_title = _DBT_FAMILY_LONG_TITLES.get(skill["family"], "")
        
        self.family_lbl = QLabel(family_title.upper())
        self.family_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.family_lbl.setContentsMargins(6, 2, 6, 2)
        self.family_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.family_lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        lay.addWidget(self.family_lbl)
        self.family_lbl.hide()
        
        self.title_lbl = QLabel(skill["title"])
        self.title_lbl.setFont(v3_font("size_h4", weight=TYPOGRAPHY["weight_bold"], serif=True))
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setMaximumHeight(34)
        lay.addWidget(self.title_lbl)
        
        self.summary_lbl = QLabel(skill["summary"])
        self.summary_lbl.setFont(qfont("size_small"))
        self.summary_lbl.setWordWrap(True)
        self.summary_lbl.setMaximumHeight(46)
        lay.addWidget(self.summary_lbl)
        
        info_lay = QHBoxLayout()
        info_lay.setSpacing(14)

        # Duración: icono calendario SVG + "N min" (mockup `.dbt-card .meta`).
        # Antes era el emoji "⏱" que no está en las fuentes cargadas → tofu (▯).
        dur_box = QHBoxLayout()
        dur_box.setSpacing(5)
        dur_box.setContentsMargins(0, 0, 0, 0)
        self.dur_icon = QLabel()
        self.dur_icon.setStyleSheet("background: transparent;")
        dur_box.addWidget(self.dur_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self.dur_lbl = QLabel(f"{skill['duration_min']} min")
        self.dur_lbl.setFont(qfont("size_caption"))
        dur_box.addWidget(self.dur_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        info_lay.addLayout(dur_box)

        self.guide_lbl = QLabel("✓ Práctica guiada")
        self.guide_lbl.setFont(qfont("size_caption"))
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
            nm_svg_pixmap("calendar", color=v3c("faint", self._modo).name(), size=14)
        )
        # Mockup `.dbt-card .meta .pl{color:var(--brand)}` — "Práctica guiada" SIEMPRE
        # en brand, no en el color de la familia (antes salía cobre/rojo por card).
        self.guide_lbl.setStyleSheet(f"color: {v3c('brand', self._modo).name()};")


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
        self.step_card_lay.setSpacing(8)

        self.step_title_lbl = QLabel()
        self.step_title_lbl.setFont(v3_font("size_h4", weight=TYPOGRAPHY["weight_bold"], serif=True))
        self.step_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # mockup: centrado
        self.step_card_lay.addWidget(self.step_title_lbl)

        self.step_body_lbl = QLabel()
        self.step_body_lbl.setFont(qfont("size_body"))
        self.step_body_lbl.setWordWrap(True)
        self.step_card_lay.addWidget(self.step_body_lbl)

        lay.addWidget(self.step_card)

        self.safety_lbl = None
        if self._skill.get("safety_note"):
            self.safety_lbl = QLabel(self._skill["safety_note"])
            self.safety_lbl.setFont(qfont("size_caption"))
            self.safety_lbl.setWordWrap(True)
            self.safety_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(self.safety_lbl)

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
        self.step_body_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        if self.safety_lbl:
            self.safety_lbl.setStyleSheet(f"color: {v3c('rose', self._modo).name()};")
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

    _SCRIM_RGBA = (20, 18, 14, 104)  # softer scrim; visual focus without hardening bg

    def __init__(self, parent: QWidget, modo: str):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._content: QWidget | None = None
        # No pinta fondo opaco: el fillRect translúcido del paintEvent oscurece
        # el contenido que quedó debajo (efecto scrim).
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

    def _apply_card_style(self):
        surf = v3c("surface", self._modo).name()
        b = v3c("line", self._modo)
        self._card.setStyleSheet(
            f"QFrame#DBTModalCard {{ background: {surf}; "
            f"border: 1px solid rgba({b.red()},{b.green()},{b.blue()},{b.alpha()}); "
            f"border-radius: 28px; }}"  # mockup `.modal` r-xl
        )

    def set_content(self, content: QWidget, max_width: int):
        if content is self._content:
            return
        if self._content is not None:
            self._card_lay.removeWidget(self._content)
            self._content.hide()
        self._content = content
        content.setParent(self._card)
        self._card.setMaximumWidth(max_width)
        self._card_lay.addWidget(content)
        content.show()

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_card_style()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
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
        
        # Main Layout inside self._content
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(24, 16, 24, 16)
        self._main_layout.setSpacing(16)
        
        # Tabs at the top
        self._tabs = NMTabs(
            [
                t("text.module.dbt.tab_now", "Ahora"),
                t("text.module.dbt.tab_library", "Biblioteca"),
            ],
            variant="seg",  # mockup `.seg`: contenedor surface-3, segmento sel = surface elevado
            modo=self._modo,
            parent=self,
        )
        self._tabs.changed.connect(self._on_tab_changed)
        # Mockup neuromood-mockup.html: el seg "Ahora / Biblioteca" arranca a
        # la izquierda del card, no centrado, y su ancho es compacto (≈200px).
        # Antes: max 640 + AlignHCenter → seg gigante centrado, no matcheaba.
        self._tabs.setMaximumWidth(220)
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
        # Open library with that family filtered
        self._tabs.set_current(1)
        family_map = {
            "mindfulness": 1,
            "distress_tolerance": 2,
            "emotion_regulation": 3,
            "interpersonal_effectiveness": 4
        }
        self._family_tabs.set_current(family_map.get(family, 0))
        
    def _build_view_biblioteca(self) -> QWidget:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        
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
            parent=widget,
        )
        self._family_tabs.changed.connect(self._filter_library)
        lay.addWidget(self._family_tabs)
        
        # Scroll Area for Skill Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._biblioteca_scroll = scroll
        
        self._library_container = QWidget()
        self._library_container.setStyleSheet("background: transparent;")
        self._library_grid = QGridLayout(self._library_container)
        self._library_grid.setContentsMargins(0, 0, 8, 0)
        self._library_grid.setHorizontalSpacing(12)
        self._library_grid.setVerticalSpacing(12)
        self._library_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for col in range(3):
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
                row, col = divmod(visible_idx, 3)
                self._library_grid.addWidget(card, row, col)
                visible_idx += 1
                
    def _show_modal(self, content, max_width: int):
        """Muestra `content` en el overlay modal (scrim + card centrada),
        dejando el fondo dimmed sin controles interactivos visibles detrás."""
        self._set_modal_background_controls_visible(False)
        if self._modal_scrim is None:
            self._modal_scrim = _PracticeModalScrim(self._content, self._modo)
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

    def start_practice(self, skill: dict):
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
        self._show_modal(self._practice_view, 560)

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
