"""
app/modules/dbt_qt.py — Módulo Habilidades DBT (PyQt6)
Práctica guiada de habilidades DBT con tres vistas principales: Ahora, Biblioteca e Historial.
"""

import os
import sys
import datetime
import uuid
import logging

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
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
        NMButtonOutline,
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
        TYPOGRAPHY,
        LAYOUT,
        stylesheet_scrollarea,
    )
    from shared.components.layout import FlowLayout
    from shared.db import conexion
except ImportError:
    # Fallback paths
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButton,
        NMButtonOutline,
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
        TYPOGRAPHY,
        LAYOUT,
        stylesheet_scrollarea,
    )
    from shared.components.layout import FlowLayout
    from shared.db import conexion

_log = logging.getLogger(__name__)

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
                "title": "S - Detenete (Stop)",
                "body": "¡No reacciones inmediatamente! Tus emociones pueden empujarte a actuar sin pensar. Mantenete quieto por un instante."
            },
            {
                "title": "T - Tomá distancia (Take a step back)",
                "body": "Alejate físicamente o mentalmente de la situación. Respirá profundamente y recordá que es una emoción pasajera."
            },
            {
                "title": "O - Observá (Observe)",
                "body": "Observá qué pasa dentro de vos y a tu alrededor. ¿Qué estás sintiendo, pensando y qué dicen los demás?"
            },
            {
                "title": "P - Procedé con conciencia (Proceed mindfully)",
                "body": "Preguntate: ¿Qué acción mejorará la situación en lugar de empeorarla? Actúa de forma deliberada y constructiva."
            }
        ],
        "safety_note": "Esta habilidad es un apoyo inmediato. Si sentís un malestar extremo o peligro inminente, recurrí a asistencia profesional."
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
        "summary": "Actuar de forma contraria al impulso de la emoción cuando esta no coincide con los hechos.",
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
        "summary": "Estructura para expresar asertivamente una petición o límite.",
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
        "summary": "Checklist para cuidar la relación y mantener el autorrespeto en tus interacciones.",
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
        super().__init__(parent=parent, modo=modo, clickable=True, glow=True)
        self._family = family
        self._icon_name = icon_name
        self._title = title
        self._subtitle = subtitle
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        
        header = QHBoxLayout()
        self.icon_label = QLabel()
        header.addWidget(self.icon_label)
        header.addStretch()
        
        family_title = {
            "mindfulness": "Mindfulness",
            "distress_tolerance": "Tolerancia",
            "emotion_regulation": "Regulación",
            "interpersonal_effectiveness": "Efectividad"
        }.get(family, "")
        
        self.chip_label = QLabel(family_title)
        self.chip_label.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.chip_label.setContentsMargins(8, 2, 8, 2)
        self.chip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.chip_label)
        lay.addLayout(header)
        
        self.title_label = QLabel(title)
        self.title_label.setFont(v3_font("size_h4", weight=TYPOGRAPHY["weight_bold"], serif=True))
        self.title_label.setWordWrap(True)
        lay.addWidget(self.title_label)
        
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setFont(qfont("size_small"))
        self.subtitle_label.setWordWrap(True)
        lay.addWidget(self.subtitle_label)
        
        self._apply_theme(self._modo)
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        super()._apply_theme(self._modo)
        
        from shared.icons_svg import nm_svg_pixmap
        
        family_color_key = {
            "mindfulness": "teal",
            "distress_tolerance": "danger",
            "emotion_regulation": "amber",
            "interpersonal_effectiveness": "primary"
        }.get(self._family, "text")
        
        icon_color = v3c(family_color_key, self._modo).name()
        self.icon_label.setPixmap(nm_svg_pixmap(self._icon_name, color=icon_color, size=24))
        
        soft_color_key = {
            "primary": "primary_soft",
            "teal": "tealSoft",
            "danger": "dangerSoft",
            "amber": "amberSoft"
        }.get(family_color_key, "borderSoft")
        
        chip_bg = v3c(soft_color_key, self._modo).name()
        self.chip_label.setStyleSheet(
            f"color: {icon_color}; "
            f"background: {chip_bg}; "
            "border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);"
        )
        self.title_label.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.subtitle_label.setStyleSheet(f"color: {v3c('textMuted', self._modo).name()};")


class _SkillCard(NMCard):
    """Tarjeta de presentación de habilidad en la Biblioteca."""
    
    def __init__(self, skill: dict, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=True, glow=True)
        self._skill = skill
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        
        family_title = {
            "mindfulness": "Mindfulness",
            "distress_tolerance": "Tolerancia al malestar",
            "emotion_regulation": "Regulación emocional",
            "interpersonal_effectiveness": "Efectividad interpersonal"
        }.get(skill["family"], "")
        
        self.family_lbl = QLabel(family_title.upper())
        self.family_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.family_lbl.setContentsMargins(6, 2, 6, 2)
        self.family_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.family_lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        lay.addWidget(self.family_lbl)
        
        self.title_lbl = QLabel(skill["title"])
        self.title_lbl.setFont(v3_font("size_h4", weight=TYPOGRAPHY["weight_bold"], serif=True))
        self.title_lbl.setWordWrap(True)
        lay.addWidget(self.title_lbl)
        
        self.summary_lbl = QLabel(skill["summary"])
        self.summary_lbl.setFont(qfont("size_small"))
        self.summary_lbl.setWordWrap(True)
        lay.addWidget(self.summary_lbl)
        
        info_lay = QHBoxLayout()
        info_lay.setSpacing(12)
        
        self.dur_lbl = QLabel(f"⏱ {skill['duration_min']} min")
        self.dur_lbl.setFont(qfont("size_caption"))
        info_lay.addWidget(self.dur_lbl)
        
        self.guide_lbl = QLabel("✓ Práctica guiada")
        self.guide_lbl.setFont(qfont("size_caption"))
        info_lay.addWidget(self.guide_lbl)
        
        info_lay.addStretch()
        lay.addLayout(info_lay)
        
        self._apply_theme(self._modo)
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        super()._apply_theme(self._modo)
        
        family_color_key = {
            "mindfulness": "teal",
            "distress_tolerance": "danger",
            "emotion_regulation": "amber",
            "interpersonal_effectiveness": "primary"
        }.get(self._skill["family"], "text")
        
        color_val = v3c(family_color_key, self._modo).name()
        soft_color_key = {
            "primary": "primary_soft",
            "teal": "tealSoft",
            "danger": "dangerSoft",
            "amber": "amberSoft"
        }.get(family_color_key, "borderSoft")
        
        chip_bg = v3c(soft_color_key, self._modo).name()
        
        self.family_lbl.setStyleSheet(
            f"color: {color_val}; "
            f"background: {chip_bg}; "
            "border-radius: 4px; border: 1px solid rgba(255,255,255,0.05);"
        )
        self.title_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.summary_lbl.setStyleSheet(f"color: {v3c('textMuted', self._modo).name()};")
        self.dur_lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
        self.guide_lbl.setStyleSheet(f"color: {v3c('teal', self._modo).name()};")


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
        
        family_color_key = {
            "mindfulness": "teal",
            "distress_tolerance": "danger",
            "emotion_regulation": "warning",
            "interpersonal_effectiveness": "primary"
        }.get(self._family, "text")
        
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


class _DistressRatingButton(QPushButton):
    """Circular distress rating button (0-10) with semantic color coding."""
    
    def __init__(self, value: int, parent=None, modo: str = None):
        super().__init__(str(value), parent)
        self._value = value
        self._modo = norm_modo(modo)
        self._hover = False
        self._active = False
        
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_bold"]))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
    def set_active(self, active: bool):
        self._active = active
        self.update()
        
    def is_active(self) -> bool:
        return self._active
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(self.rect())
        is_dark = "dark" in self._modo
        
        if not self.isEnabled():
            p.setOpacity(0.4)
            
        if self._active:
            if self._value <= 3:
                bg_color = v3c("teal", self._modo)
            elif self._value <= 6:
                bg_color = v3c("warning", self._modo)
            else:
                bg_color = v3c("danger", self._modo)
            text_color = QColor("#FFFFFF")
            border_color = bg_color
        elif self._hover:
            bg_color = v3c("elevatedSolid" if is_dark else "elevated", self._modo)
            border_color = v3c("borderStrong", self._modo)
            text_color = v3c("text", self._modo)
        else:
            bg_color = v3c("surfaceSolid" if is_dark else "surface", self._modo)
            border_color = v3c("border", self._modo)
            text_color = v3c("text2", self._modo)
            
        p.setBrush(QBrush(bg_color))
        p.setPen(QPen(border_color, 1.5))
        p.drawEllipse(rect.adjusted(1, 1, -1, -1))
        
        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()
        
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class _ServiceOptionButton(QPushButton):
    """Semantic option button for evaluating practice efficacy."""
    
    def __init__(self, key: str, text: str, parent=None, modo: str = None):
        super().__init__(text, parent)
        self._key = key
        self._modo = norm_modo(modo)
        self._hover = False
        self._active = False
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_bold"]))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(36)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
    def set_active(self, active: bool):
        self._active = active
        self.update()
        
    def is_active(self) -> bool:
        return self._active
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        h = self.height()
        r = min(LAYOUT["radius_button"], h // 2)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        is_dark = "dark" in self._modo
        
        if not self.isEnabled():
            p.setOpacity(0.4)
            
        color_map = {
            "ayudo": "teal",
            "parcial": "warning",
            "no_esta_vez": "danger",
            "sin_evaluar": "textMuted"
        }
        color_token = color_map.get(self._key, "text")
        
        if self._active:
            color_solid = v3c(color_token, self._modo)
            bg_color = color_solid
            border_color = color_solid
            text_color = QColor("#FFFFFF") if self._key != "sin_evaluar" else v3c("primary_ink", self._modo)
        elif self._hover:
            bg_color = v3c("elevatedSolid" if is_dark else "elevated", self._modo)
            border_color = v3c("borderStrong", self._modo)
            text_color = v3c("text", self._modo)
        else:
            bg_color = v3c("surfaceSolid" if is_dark else "surface", self._modo)
            border_color = v3c("border", self._modo)
            text_color = v3c("text2", self._modo)
            
        p.fillPath(path, QBrush(bg_color))
        p.setPen(QPen(border_color, 1.25))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)
        
        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()
        
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


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

        self.title_lbl = QLabel(self._skill["title"])
        self.title_lbl.setFont(v3_font("size_h3", weight=TYPOGRAPHY["weight_bold"], serif=True))
        lay.addWidget(self.title_lbl)

        self.progress_lbl = QLabel()
        self.progress_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.progress_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.progress_lbl)

        # Visual step indicator
        self.step_indicator = _StepProgressIndicator(len(self._skill["steps"]), self._skill["family"], parent=self, modo=self._modo)
        lay.addWidget(self.step_indicator)

        self.step_card = NMCard(parent=self, clickable=False, modo=self._modo)
        self.step_card_lay = QVBoxLayout(self.step_card)
        self.step_card_lay.setContentsMargins(20, 16, 20, 16)
        self.step_card_lay.setSpacing(8)

        self.step_title_lbl = QLabel()
        self.step_title_lbl.setFont(v3_font("size_h4", weight=TYPOGRAPHY["weight_bold"]))
        self.step_card_lay.addWidget(self.step_title_lbl)

        self.step_body_lbl = QLabel()
        self.step_body_lbl.setFont(qfont("size_body"))
        self.step_body_lbl.setWordWrap(True)
        self.step_card_lay.addWidget(self.step_body_lbl)

        # 2026-06: el step_card con stretch=1 para que se expanda y rellene
        # el alto disponible. Antes el contenido quedaba arriba con un
        # vacío grande entre el bloque y los botones de navegación.
        lay.addWidget(self.step_card, stretch=1)

        self.safety_lbl = None
        if self._skill.get("safety_note"):
            self.safety_lbl = QLabel(self._skill["safety_note"])
            self.safety_lbl.setFont(qfont("size_caption"))
            self.safety_lbl.setWordWrap(True)
            lay.addWidget(self.safety_lbl)

        # 2026-06: removido `lay.addStretch()` que generaba un vacío
        # excesivo entre el safety_note y los botones de navegación.
        # Los botones quedan pegados al bloque de contenido.

        btn_lay = QHBoxLayout()
        self.btn_cancel = NMButton(t("text.module.dbt.cancel_btn", "Salir"), parent=self, variant="ghost", size="md")
        self.btn_cancel.clicked.connect(self.cancelled.emit)
        btn_lay.addWidget(self.btn_cancel)

        btn_lay.addStretch()

        self.btn_prev = NMButton(t("text.module.dbt.prev_btn", "Anterior"), parent=self, variant="secondary", size="md")
        self.btn_prev.clicked.connect(self._prev_step)
        btn_lay.addWidget(self.btn_prev)

        self.btn_next = NMButton(t("text.module.dbt.next_btn", "Siguiente"), parent=self, variant="gradient", size="md")
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
            self.safety_lbl.setStyleSheet(f"color: {v3c('warning', self._modo).name()};")
        if hasattr(self, "step_indicator") and self.step_indicator:
            self.step_indicator._apply_theme(self._modo)
            
    def _update_step(self):
        steps = self._skill["steps"]
        step = steps[self._current_step]
        
        self.progress_lbl.setText(f"PASO {self._current_step + 1} DE {len(steps)}")
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


class _PracticeClosure(QWidget):
    """Pantalla de evaluación final antes de guardar."""

    saved = pyqtSignal(object, object, str, str)  # (antes, despues, resultado, nota)
    
    def __init__(self, skill_title: str, modo: str = None, parent=None):
        super().__init__(parent)
        self._skill_title = skill_title
        self._modo = norm_modo(modo)
        self._antes = None
        self._despues = None
        self._resultado = "sin_evaluar"
        
        self._setup_ui()
        
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(10)

        self.title_lbl = QLabel(f"Finalizar práctica: {self._skill_title}")
        self.title_lbl.setFont(v3_font("size_h3", weight=TYPOGRAPHY["weight_bold"], serif=True))
        lay.addWidget(self.title_lbl)

        # Antes
        self.lbl_antes = QLabel(
            t(
                "text.module.dbt.closure_antes",
                "¿Cómo estaba tu nivel de malestar ANTES? (Opcional)",
            )
        )
        self.lbl_antes.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self.lbl_antes)

        self.antes_buttons = []
        antes_lay = QHBoxLayout()
        antes_lay.setSpacing(4)
        for i in range(11):
            btn = _DistressRatingButton(i, parent=self, modo=self._modo)
            btn.clicked.connect(lambda checked=False, val=i: self._select_antes(val))
            antes_lay.addWidget(btn)
            self.antes_buttons.append(btn)
        lay.addLayout(antes_lay)

        # Despues
        self.lbl_despues = QLabel(
            t(
                "text.module.dbt.closure_despues",
                "¿Cómo está tu nivel de malestar AHORA? (Opcional)",
            )
        )
        self.lbl_despues.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self.lbl_despues)

        self.despues_buttons = []
        despues_lay = QHBoxLayout()
        despues_lay.setSpacing(4)
        for i in range(11):
            btn = _DistressRatingButton(i, parent=self, modo=self._modo)
            btn.clicked.connect(lambda checked=False, val=i: self._select_despues(val))
            despues_lay.addWidget(btn)
            self.despues_buttons.append(btn)
        lay.addLayout(despues_lay)

        # Resultado
        self.lbl_res = QLabel(t("text.module.dbt.closure_result", "¿Te sirvió la práctica?"))
        self.lbl_res.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self.lbl_res)

        self.res_buttons = {}
        res_lay = QHBoxLayout()
        res_lay.setSpacing(6)

        options = [
            ("ayudo", t("text.module.dbt.result_helped", "Me ayudó")),
            ("parcial", t("text.module.dbt.result_partial", "Un poco")),
            ("no_esta_vez", t("text.module.dbt.result_no", "No esta vez")),
            ("sin_evaluar", t("text.module.dbt.result_skip", "Prefiero no evaluar"))
        ]
        for val, label in options:
            btn = _ServiceOptionButton(val, label, parent=self, modo=self._modo)
            btn.clicked.connect(lambda checked=False, v=val: self._select_resultado(v))
            res_lay.addWidget(btn)
            self.res_buttons[val] = btn
        lay.addLayout(res_lay)

        # Preselect "sin_evaluar"
        self._select_resultado("sin_evaluar")

        # 2026-06: removido `lay.addStretch()` que generaba un vacío
        # excesivo entre los botones de resultado y el botón Guardar.
        # El botón ahora queda pegado al bloque de arriba.

        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        self.btn_save = NMButton(
            t("text.module.dbt.save_practice_btn", "Guardar práctica"),
            parent=self, variant="gradient", size="md"
        )
        self.btn_save.clicked.connect(self._save_practice)
        btn_lay.addWidget(self.btn_save)
        lay.addLayout(btn_lay)
        
        self._apply_theme(self._modo)
        ThemeManager.instance().theme_changed.connect(self._apply_theme)
        
    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.title_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.lbl_antes.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.lbl_despues.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        self.lbl_res.setStyleSheet(f"color: {v3c('text', self._modo).name()};")

        for btn in self.antes_buttons:
            btn._apply_theme(self._modo)
        for btn in self.despues_buttons:
            btn._apply_theme(self._modo)
        for btn in self.res_buttons.values():
            btn._apply_theme(self._modo)
            
    def _select_antes(self, val: int):
        self._antes = val
        for i, btn in enumerate(self.antes_buttons):
            btn.set_active(i == val)
            
    def _select_despues(self, val: int):
        self._despues = val
        for i, btn in enumerate(self.despues_buttons):
            btn.set_active(i == val)
            
    def _select_resultado(self, val: str):
        self._resultado = val
        for k, btn in self.res_buttons.items():
            btn.set_active(k == val)
            
    def _save_practice(self):
        if getattr(self, "_is_saved", False):
            return
        self._is_saved = True
        self.btn_save.setEnabled(False)
        self.saved.emit(self._antes, self._despues, self._resultado, "")


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
            modo=self._modo,
            parent=self,
        )
        self._tabs.changed.connect(self._on_tab_changed)
        self._main_layout.addWidget(self._tabs)
        
        # View stacked widget
        self._view_stack = QStackedWidget()
        self._main_layout.addWidget(self._view_stack)
        
        # 3 main views
        self._view_ahora = self._build_view_ahora()
        self._view_biblioteca = self._build_view_biblioteca()

        self._view_stack.addWidget(self._view_ahora)
        self._view_stack.addWidget(self._view_biblioteca)
        
        self._practice_view = None
        self._closure_view = None
        
        # Navigation track
        self._on_tab_changed(0, t("text.module.dbt.tab_now", "Ahora"))
        
    def _on_tab_changed(self, idx: int, label: str):
        if self._practice_view or self._closure_view:
            self._cleanup_practice_flow()
            
        self._view_stack.setCurrentIndex(idx)
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
        for c in range(2):
            grid.setColumnStretch(c, 1)
        for r in range(2):
            grid.setRowStretch(r, 1)

        needs = [
            ("Volver al presente", "Mindfulness: pausar, enfocar y notar el aquí y ahora.", "mindfulness", "mind"),
            ("Atravesar un momento intenso", "Tolerancia: superar crisis sin empeorar la situación.", "distress_tolerance", "shield"),
            ("Regular una emoción", "Regulación: entender y suavizar sentimientos desbordantes.", "emotion_regulation", "mood"),
            ("Comunicarme con claridad", "Efectividad: pedir límites o dialogar con autorrespeto.", "interpersonal_effectiveness", "handshake"),
        ]

        for i, (title, desc, family, icon) in enumerate(needs):
            card = _NeedCard(title, desc, family, icon, modo=self._modo, parent=widget)
            card.clicked.connect(lambda f=family: self._on_need_clicked(f))
            # Expanding vertical para que las celdas del grid rellenen el
            # alto disponible y eliminen el hueco excesivo entre el prompt
            # y las 4 cards (antes el QStackedWidget centraba el contenido
            # y quedaba un gap grande arriba).
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            grid.addWidget(card, i // 2, i % 2)

        # 2026-06: stretch=1 en la grid para que el contenido se pegue al
        # top de la vista (sin el stretch, Qt centra vertical → gap arriba
        # y vacío abajo). Con el stretch, la grid se expande para llenar
        # el alto del QStackedWidget.
        lay.addLayout(grid, stretch=1)

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
            modo=self._modo,
            parent=widget,
        )
        self._family_tabs.changed.connect(self._filter_library)
        lay.addWidget(self._family_tabs)
        
        # Scroll Area for Skill Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._biblioteca_scroll = scroll
        
        self._library_container = QWidget()
        self._library_container.setStyleSheet("background: transparent;")
        self._library_flow = FlowLayout(self._library_container, spacing=16)
        
        scroll.setWidget(self._library_container)
        lay.addWidget(scroll)
        
        return widget
        
    def _filter_library(self, *args):
        # Clear existing
        while self._library_flow.count():
            item = self._library_flow.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
                
        # Filter logic
        tab_idx = self._family_tabs.current()
        family_filter = [None, "mindfulness", "distress_tolerance", "emotion_regulation", "interpersonal_effectiveness"][tab_idx]
        
        for skill_id, skill in DBT_SKILLS.items():
            if family_filter is None or skill["family"] == family_filter:
                card = _SkillCard(skill, modo=self._modo, parent=self._library_container)
                card.clicked.connect(lambda s=skill: self.start_practice(s))
                self._library_flow.addWidget(card)
                
    def start_practice(self, skill: dict):
        self._cleanup_practice_flow()
        self._tabs.hide()
        
        # Cache origin tab to return correctly
        self._origin_view = self._tabs.current()
        self._current_skill_id = skill["id"]
        self._current_family = skill["family"]
        # RA-5: cachear la version canónica de DBT_SKILLS. Default 1 si falta.
        self._current_skill_version = skill.get("version", 1)
        
        self._practice_view = _SkillPracticeView(skill, modo=self._modo, parent=self)
        self._practice_view.cancelled.connect(self._on_practice_cancelled)
        self._practice_view.finished.connect(self._on_practice_finished)
        self._main_layout.addWidget(self._practice_view)
        
        self._view_stack.hide()
        self._practice_view.show()
        
    def _on_practice_cancelled(self):
        self._cleanup_practice_flow()
        self._tabs.show()
        self._view_stack.show()
        self._tabs.set_current(self._origin_view)
        
    def _on_practice_finished(self, started_at: datetime.datetime):
        self._started_at = started_at
        self._tabs.hide()
        
        skill = DBT_SKILLS.get(self._current_skill_id)
        skill_title = skill["title"] if skill else ""
        
        self._closure_view = _PracticeClosure(skill_title, modo=self._modo, parent=self)
        self._closure_view.saved.connect(self._on_practice_saved)
        
        self._main_layout.addWidget(self._closure_view)
        if self._practice_view:
            self._practice_view.hide()
        self._closure_view.show()
        
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
        self._tabs.show()
        self._view_stack.show()
        self._tabs.set_current(0)
        
    def _get_need_text(self, family: str) -> str:
        return {
            "mindfulness": "Volver al presente",
            "distress_tolerance": "Atravesar un momento intenso",
            "emotion_regulation": "Regular una emoción",
            "interpersonal_effectiveness": "Comunicarme con claridad"
        }.get(family, "")
        
    def _cleanup_practice_flow(self):
        if self._practice_view:
            self._practice_view.hide()
            self._main_layout.removeWidget(self._practice_view)
            self._practice_view.deleteLater()
            self._practice_view = None
        if self._closure_view:
            self._closure_view.hide()
            self._main_layout.removeWidget(self._closure_view)
            self._closure_view.deleteLater()
            self._closure_view = None
            
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
        if hasattr(self, "_practice_view") and self._practice_view:
            if hasattr(self._practice_view, "_apply_theme"):
                self._practice_view._apply_theme(self._modo)
        if hasattr(self, "_closure_view") and self._closure_view:
            if hasattr(self._closure_view, "_apply_theme"):
                self._closure_view._apply_theme(self._modo)
