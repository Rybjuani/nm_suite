"""
app/modules/animo_qt.py — Módulo Mood Tracker v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Mood Tracker):

  Header        eyebrow "ÚLTIMOS 7 DÍAS"
  Wave card     NMWaveChart altura 280 (current + previous week)
  Slider card   V3MoodSlider 1-10 (slashbar emocional + NMMoodEmoji 104px)
  Nota card     textarea con contador X/500 + NMButton "Guardar registro"
  Insights row  3 cards (Promedio / Racha / Progreso semanal) con NMModuleRing

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  COLORES_PUNTAJE (chips legacy + celebration), _registrar() (DB write +
  sync_inmediato_background), _load_streak(), get_card_status(), on_enter/leave,
  MoodCelebration overlay (≥7 puntos).
"""

import os
import sys
import random
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPointF,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QFont,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QBoxLayout,
    QSizePolicy,
)

try:
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        ThemeManager,
        NMCard,
        NMWaveChart,
        NMModuleRing,
        V3MoodSlider,
        NMTextArea,
        NMDivider,
        responsive_columns,
        NMChartPanel,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        V3_RD,
        stylesheet_textedit,
        stylesheet_scrollarea,
        PAD_CONTAINER,
        eyebrow_font,
        v3_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButton,
        NMCard,
        NMToast,
        NMWaveChart,
        NMModuleRing,
        V3MoodSlider,
        NMTextArea,
        NMChartPanel,
    )
    from shared.theme_qt import (
        C,
        norm_modo,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        eyebrow_font,
        v3_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled


from shared.design_tokens import MOOD_PALETTE
from shared.remote_config import t


EMOCIONES_POSITIVAS = {"Calma", "Energía", "Gratitud"}
EMOCIONES_NEGATIVAS = {"Tensión", "Tristeza", "Cansancio"}
EMOCIONES_VALIDAS = EMOCIONES_POSITIVAS | EMOCIONES_NEGATIVAS


def valencia_de_emocion(emocion: str) -> str:
    """'positiva' | 'negativa' | 'neutral' según la emoción elegida."""
    if emocion in EMOCIONES_POSITIVAS:
        return "positiva"
    if emocion in EMOCIONES_NEGATIVAS:
        return "negativa"
    return "neutral"


def bienestar_desde_emocion(emocion: str, intensidad: int) -> int:
    """Mapea emoción+intensidad (1-10) → bienestar (1-10) coherente con Hub/Activación.

    Positivas (Calma/Energía/Gratitud): bienestar = intensidad.
    Negativas (Tensión/Tristeza/Cansancio): bienestar = 11 - intensidad.
    Sin emoción: bienestar = intensidad (compatibilidad hacia atrás).
    """
    intensidad = max(1, min(10, int(intensidad)))
    if emocion in EMOCIONES_POSITIVAS:
        return intensidad
    if emocion in EMOCIONES_NEGATIVAS:
        return 11 - intensidad
    return intensidad


def _colores_puntaje() -> dict:
    """Retorna dict nivel->hex usando MOOD_PALETTE V5 para que los agentes
    usen tokens y no colores hardcodeados. Mantiene compatibilidad con la
    interfaz existente (level int 1-10 → hex str)."""
    return {lv: MOOD_PALETTE[lv]["from"] for lv in range(1, 11)}


def _mood_care(level: int) -> tuple[str, str]:
    level = max(1, min(10, int(level)))
    if level <= 3:
        return (
            "Necesitas cuidado",
            "Ve despacio. Una pausa breve puede ayudarte a volver al cuerpo.",
        )
    if level <= 6:
        return (
            "Estado medio",
            "Observa qué necesitas hoy. Un registro breve alcanza.",
        )
    return (
        "Buen sostén",
        "Aprovecha esta energía para cuidar un hábito simple.",
    )


def _mood_color_for_level(level: int) -> str:
    """Hex color del extremo 'from' del MOOD_PALETTE para el nivel dado."""
    return MOOD_PALETTE[max(1, min(10, int(level)))]["from"]


class _AnimoHeroCard(NMCard):
    """Hero V5 local: copy cálido, badge de estado y score con mensaje."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self.setMinimumHeight(88)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(16)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(3)
        self._eyebrow = QLabel("Tu ánimo")
        self._eyebrow.setFont(eyebrow_font())
        self._eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        text_col.addWidget(self._eyebrow)
        self._title = QLabel("Registra cómo estás hoy")
        self._title.setFont(
            v3_font("size_display_m", weight=TYPOGRAPHY["weight_medium"], serif=True)
        )
        text_col.addWidget(self._title)
        # Sin consejo clínico ("una nota corta ayuda a..."): los desarrolladores
        # no dan tips terapéuticos (decisión owner v1.0). Descriptor neutro.
        self._body = QLabel("Tu registro diario, en tus palabras.")
        self._body.setFont(qfont("size_small"))
        self._body.setWordWrap(True)
        text_col.addWidget(self._body)
        lay.addLayout(text_col, 1)

        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.setSpacing(4)
        status_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._status = QLabel("Sin registro")
        self._status.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_col.addWidget(self._status, 0, Qt.AlignmentFlag.AlignRight)

        self._status_hint = QLabel("Tu check-in de hoy aparece aquí.")
        self._status_hint.setFont(qfont("size_caption_xs"))
        self._status_hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._status_hint.setWordWrap(True)
        status_col.addWidget(self._status_hint, 0, Qt.AlignmentFlag.AlignRight)

        score_row = QHBoxLayout()
        score_row.setSpacing(4)
        score_row.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self._score = QLabel("—")
        self._score.setFont(
            v3_font("size_display_m", weight=TYPOGRAPHY["weight_medium"], serif=True)
        )
        score_row.addWidget(self._score)
        self._unit = QLabel("/ 10")
        self._unit.setFont(qfont("size_small"))
        score_row.addWidget(self._unit, alignment=Qt.AlignmentFlag.AlignBottom)
        status_col.addLayout(score_row)
        lay.addLayout(status_col)
        self._apply_theme(self._modo)

    def set_level(self, level: int):
        label, message = _mood_care(level)
        self._score.setText(str(int(level)))
        self._status.setText(label)
        self._status_hint.setText(message)

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent; "
        )
        self._eyebrow.setFont(eyebrow_font())
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._body.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )
        primary = v3c("primary", self._modo)
        primary_soft = C("primary_soft", self._modo)
        self._status.setStyleSheet(
            f"color: {primary.name()}; background: {primary_soft}; "
            "border-radius: 7px; padding: 4px 10px;"
        )
        self._status_hint.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )
        self._score.setStyleSheet(f"color: {primary.name()}; background: transparent;")
        self._unit.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )


class _CareStatCard(NMCard):
    """Métrica compacta con mensaje de cuidado; nunca muestra un valor solo."""

    def __init__(self, label: str, value: str, message: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self.setMinimumHeight(66)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(1)
        self._label = QLabel(label)
        self._label.setFont(eyebrow_font())
        lay.addWidget(self._label)

        row = QHBoxLayout()
        row.setSpacing(6)
        self._value = QLabel(value)
        self._value.setFont(v3_font("size_h3", weight=TYPOGRAPHY["weight_semibold"], serif=True))
        row.addWidget(self._value)
        self._delta = QLabel("")
        self._delta.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._delta.setVisible(False)
        row.addWidget(self._delta)
        row.addStretch()
        lay.addLayout(row)

        self._message = QLabel(message)
        self._message.setFont(qfont("size_caption_xs"))
        self._message.setWordWrap(True)
        lay.addWidget(self._message)
        self._tone_key = None
        self._apply_theme(self._modo)

    def set_value(self, value: str):
        self._value.setText(value or "—")

    def set_message(self, message: str):
        self._message.setText(message or "")

    def set_tone(self, tone_key: str | None):
        self._tone_key = tone_key
        self._apply_value_style()

    def set_delta(self, text: str, positive: bool | None = None):
        if not text:
            self._delta.setVisible(False)
            return
        self._delta.setText(text)
        self._delta.setVisible(True)
        col_key = "teal" if positive is True else "danger" if positive is False else "text2"
        col = v3c(col_key, self._modo)
        bg = f"rgba({col.red()},{col.green()},{col.blue()},0.13)"
        self._delta.setStyleSheet(
            f"color: {col.name()}; background: {bg}; border-radius: 6px; padding: 2px 6px;"
        )

    def _apply_value_style(self):
        col = v3c(self._tone_key or "text", self._modo)
        self._value.setStyleSheet(f"color: {col.name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._label.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent; "
        )
        self._label.setFont(eyebrow_font())
        self._message.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )
        self._apply_value_style()


# ── MoodCelebration: partículas cuando se registra mood ≥ 7 ──────────────────


class _MoodParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -2)
        # Alpha inicial 200 (feedback owner: subir un poco la intensidad;
        # el original era 255 — sigue suavizado).
        self.alpha = 200
        self.radius = random.uniform(3, 6)
        self.color = QColor(color)


class MoodCelebration(QWidget):
    """Overlay de partículas (~600ms) cuando el usuario registra un ánimo alto."""

    def __init__(self, parent, modo="dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._particles: list[_MoodParticle] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.hide()
        parent.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.parent() and ev.type().name in ("Resize", "Move"):
            self.setGeometry(self.parent().rect())
        return super().eventFilter(obj, ev)

    def launch(self, x: float, y: float, score: int = 7):
        if not self.parent():
            return
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()

        # Paleta alineada con el dithering: violet/teal/primary (sin amber).
        # violet ≈ indigo/lavanda del _bar(); teal = teal; primary = azul medio.
        palette = [
            v3c("violet", self._modo).name(),
            v3c("teal", self._modo).name(),
            v3c("primary", self._modo).name(),
        ]

        # 3 niveles definidos por el owner: 7-8 leve, 9 media, 10 mayor.
        # Densidad/tamaño crecen por tier, manteniendo el tope calmo (lejos de
        # los 22/8.0 originales).
        score = max(7, min(10, int(score)))
        if score <= 8:
            count, (r_min, r_max) = 9, (2.0, 4.5)    # leve  (7-8)
        elif score == 9:
            count, (r_min, r_max) = 13, (2.5, 6.0)   # media (9)
        else:
            count, (r_min, r_max) = 18, (3.0, 7.0)   # mayor (10)

        for _ in range(count):
            p = _MoodParticle(x, y, random.choice(palette))
            p.radius = random.uniform(r_min, r_max)
            self._particles.append(p)
        self._timer.start(16)

    def stop(self):
        self._timer.stop()
        self._particles.clear()
        self.hide()

    def _tick(self):
        alive = []
        for p in self._particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.35
            # Decay -8 con alpha inicial 200: la celebración dura ~400ms.
            p.alpha = max(0, p.alpha - 8)
            if p.alpha > 0:
                alive.append(p)
        self._particles = alive
        self.update()
        if not alive:
            self._timer.stop()
            self.hide()

    def paintEvent(self, event):
        if not self._particles:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for part in self._particles:
            col = QColor(part.color)
            col.setAlpha(part.alpha)
            p.setBrush(QBrush(col))
            p.drawEllipse(QPointF(part.x, part.y), part.radius, part.radius)
        p.end()


# ── _InsightCard ─────────────────────────────────────────────────────────────


class _InsightCard(NMCard):
    """Tarjeta de insight v3: NMModuleRing + eyebrow + valor grande."""

    def __init__(self, label: str, value: str, pct: float, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._label_text = label
        self._value_text = value
        self._pct = max(0.0, min(1.0, pct))
        self._build()

    def _build(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        h.setSpacing(V3_SP["md"])

        self._ring = NMModuleRing(size=56, pct=self._pct, modo=self._modo)
        h.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._label_lbl = QLabel(self._label_text)
        self._label_lbl.setFont(eyebrow_font())
        col.addWidget(self._label_lbl)
        self._value_lbl = QLabel(self._value_text)
        self._value_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._value_lbl)
        h.addLayout(col, stretch=1)
        self._apply_insight_styles()

    def set_value(self, value: str, pct: float):
        self._value_text = value
        self._pct = max(0.0, min(1.0, pct))
        self._value_lbl.setText(value)
        self._ring.set_pct(self._pct)

    def _apply_insight_styles(self):
        self._label_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._value_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_insight_styles()


# ── ModuloAnimo v3 ──────────────────────────────────────────────────────────


class ModuloAnimo(NMModule):
    MODULE_TITLE = "Ánimo"
    MODULE_ICON = "animo"

    # ── build ────────────────────────────────────────────────────────────────

    def build_ui(self):
        # 4.1: el slider arranca SIN selección visible. El thumb se queda en el
        # centro (level=5) internamente, pero el score label muestra "—/10" y el
        # botón "Guardar registro" está deshabilitado hasta el primer movimiento.
        # Antes mostraba "5/10" con puntaje=5 ya seteado — el paciente creía tener
        # un valor elegido sin haber tocado nada (semántica clínica rota).
        self.puntaje = None
        self._slider_touched = False

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        outer.addWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(10)

        self._hero = _AnimoHeroCard(self._modo, parent=body)
        lay.addWidget(self._hero)

        self._main_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._main_row.setSpacing(12)
        left_col = QWidget()
        left_col.setStyleSheet("background: transparent;")
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(8)
        right_col = QWidget()
        right_col.setStyleSheet("background: transparent;")
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)

        # 1. NMChartPanel con wave chart — zona reservada (Plan 2 NMChartPanel)
        self._hist_card = NMChartPanel("Últimos 7 días", modo=self._modo)
        self._hist_card.setMinimumHeight(182)
        self._range_lbl = None  # ya manejado internamente por NMChartPanel

        # Serie positiva (teal) y negativa (danger) en paralelo, con leyenda:
        # "tristeza 10" se ve como negativo fuerte, no como positivo.
        self._wave_chart = NMWaveChart(
            modo=self._modo,
            secondary_color_key="danger",
            series_labels=("Positivo", "Negativo"),
        )
        self._wave_chart.setMinimumHeight(110)
        self._wave_chart.setMaximumHeight(140)
        self._hist_card.set_chart(self._wave_chart)
        right_lay.addWidget(self._hist_card)

        # Registro pos/neg separado (v1.0): un lado NO descuenta al otro.
        # Lenguaje descriptivo, sin consejo clínico (criterio owner).
        self._stat_avg = _CareStatCard(
            "Positivo · 7 días",
            "—",
            "Promedio de tus registros positivos.",
            modo=self._modo,
        )
        self._stat_prog = _CareStatCard(
            "Negativo · 7 días",
            "—",
            "Promedio de tus registros negativos.",
            modo=self._modo,
        )
        self._stat_streak = _CareStatCard(
            "Progreso",
            "0 días",
            "Días seguidos con registro.",
            modo=self._modo,
        )
        self._stat_cards = [self._stat_avg, self._stat_prog, self._stat_streak]
        for card in self._stat_cards:
            right_lay.addWidget(card)

        # 2. Registro del ánimo: escala sobria + mensaje de cuidado.
        slider_card = NMCard(modo=self._modo, clickable=False, glow=False)
        slider_lay = QVBoxLayout(slider_card)
        slider_lay.setContentsMargins(18, 12, 18, 12)
        slider_lay.setSpacing(6)

        slider_head = QHBoxLayout()
        slider_head.setSpacing(V3_SP["sm"])
        self._slider_eyebrow = QLabel("Escala emocional")
        self._slider_eyebrow.setFont(eyebrow_font())
        slider_head.addWidget(self._slider_eyebrow)
        slider_head.addStretch()
        # 4.1: arranca en "—/10" (muted) hasta el primer movimiento del slider.
        self._slider_score = QLabel("—/10")
        self._slider_score.setFont(qfont_mono(11, bold=True))
        slider_head.addWidget(self._slider_score)
        slider_lay.addLayout(slider_head)

        # unset=True: el thumb arranca ESTACIONADO en la muesca 0 (el 0 no es
        # un valor registrable — feedback owner v1.0); al primer click/drag se
        # mueve a 1-10 y se habilita guardar.
        self._v3_slider = V3MoodSlider(
            level=5,
            title="¿Cómo te sientes hoy?",
            subtitle="Desliza para indicar tu estado.",
            modo=self._modo,
            compact=True,
            unset=True,
        )
        self._v3_slider.level_changed.connect(self._on_level_changed)
        slider_lay.addWidget(self._v3_slider)

        chips = QGridLayout()
        chips.setHorizontalSpacing(V3_SP["sm"])
        chips.setVerticalSpacing(V3_SP["sm"])
        self._emotion_chips: list[QPushButton] = []
        self._emocion_por_chip: dict[QPushButton, str] = {}
        self._emocion_actual: str | None = None
        for text in ("Calma", "Tensión", "Tristeza", "Energía", "Cansancio", "Gratitud"):
            chip = QPushButton(text)
            chip.setFont(qfont("size_caption"))
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            # Pastilla compacta: el QPushButton global impone min-height 36 y los
            # chips quedaban altos/estirados. Fijamos 30px (la QSS del chip
            # también la cap­ea) para reducirlos sin perder legibilidad.
            chip.setFixedHeight(30)
            chip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            chip.setCheckable(True)
            chip.clicked.connect(lambda _checked=False, c=chip: self._on_emotion_chip_clicked(c))
            self._emotion_chips.append(chip)
            self._emocion_por_chip[chip] = text
            idx = len(self._emotion_chips) - 1
            chips.addWidget(chip, idx // 3, idx % 3)
        slider_lay.addLayout(chips)
        left_lay.addWidget(slider_card)
        self._slider_card = slider_card

        # 4. Nota del día card
        note_card = NMCard(modo=self._modo, clickable=False, glow=False)
        note_card.setMinimumHeight(176)
        note_lay = QVBoxLayout(note_card)
        note_lay.setContentsMargins(18, 12, 18, 14)
        note_lay.setSpacing(6)

        note_header = QHBoxLayout()
        self._note_eyebrow = QLabel("Nota del día")
        self._note_eyebrow.setFont(eyebrow_font())
        note_header.addWidget(self._note_eyebrow)
        note_header.addStretch()
        self._note_counter = QLabel("0/500")
        self._note_counter.setFont(qfont_mono(10, bold=False))
        note_header.addWidget(self._note_counter)
        note_lay.addLayout(note_header)

        self._txt_nota = NMTextArea(
            t("text.module.animo.note_placeholder", "¿Qué influyó en tu estado hoy?"),
            modo=self._modo,
            min_height=72,
        )
        # Min 64 + Expanding: en ventanas grandes el espacio extra del card lo
        # absorbe el ÁREA DE ESCRITURA (útil), no los labels (que centraban su
        # texto y dejaban un hueco muerto arriba de "Nota del día" a 1920px).
        self._txt_nota.setMinimumHeight(64)
        self._txt_nota.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._txt_nota.setPlaceholderText(t("text.module.animo.note_placeholder", "¿Qué influyó en tu estado hoy?"))
        self._txt_nota.textChanged.connect(self._on_note_changed)
        note_lay.addWidget(self._txt_nota)

        footer = QVBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        # (Hint "Una frase alcanza..." eliminado — feedback owner v1.0: era
        # recomendación clínica; no la hacemos nosotros como desarrolladores.)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(V3_SP["sm"])
        btn_row.addStretch()
        self._btn_reg = NMButton(
            t("text.module.animo.save_btn", "Guardar registro"), modo=self._modo, variant="gradient", size="md", width=180
        )
        self._btn_reg.setFixedHeight(34)
        # 4.1: deshabilitado hasta que el paciente toque el slider. La razón se
        # explica en el score label "—/10" — coherente.
        self._btn_reg.setEnabled(False)
        self._btn_reg.clicked.connect(self._registrar)
        btn_row.addWidget(self._btn_reg)
        footer.addLayout(btn_row)
        note_lay.addLayout(footer)
        left_lay.addWidget(note_card)
        self._note_card = note_card

        left_lay.addStretch()
        right_lay.addStretch()
        self._main_row.addWidget(left_col, 1)
        self._main_row.addWidget(right_col, 1)
        lay.addLayout(self._main_row)

        # Datos iniciales
        self._cargar_grafico()
        self._refresh_insights()
        self._apply_text_styles()

        # Celebration overlay (partículas mood ≥ 7)
        self._celebration = MoodCelebration(self._content, self._modo)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        if hasattr(self, "_main_row"):
            if w < 900:
                self._main_row.setDirection(QBoxLayout.Direction.TopToBottom)
            else:
                self._main_row.setDirection(QBoxLayout.Direction.LeftToRight)

    def _relayout_stats(self):
        pass  # stats en columna fija 1/3 — sin responsive grid

    # ── styles helper ────────────────────────────────────────────────────────

    def _apply_text_styles(self):
        C("ink_primary", self._modo)
        text2 = C("ink_secondary", self._modo)
        C("ink_placeholder", self._modo)
        C("primary", self._modo)
        C("border", self._modo)
        surface_2 = C("bg_surface2", self._modo)
        border_solid = C("border_solid", self._modo)

        for lbl in (
            getattr(self, "_range_lbl", None),
            getattr(self, "_note_eyebrow", None),
            getattr(self, "_note_counter", None),
            getattr(self, "_slider_eyebrow", None),
        ):
            if lbl is not None:
                lbl.setStyleSheet(f"color: {text2}; background: transparent;")

        if hasattr(self, "_slider_score"):
            # 4.1: si el slider no fue tocado, mostrar "—/10" muted; si fue
            # tocado, mostrar el puntaje real en color accent.
            if not getattr(self, "_slider_touched", False):
                self._slider_score.setText("—/10")
                self._slider_score.setStyleSheet(
                    f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
                )
            else:
                score = self.puntaje
                if score is None and hasattr(self, "_v3_slider"):
                    score = self._v3_slider.level()
                self._slider_score.setText(f"{score}/10")
                self._slider_score.setStyleSheet(
                    f"color: {v3c('accent', self._modo).name()}; background: transparent;"
                )
        if hasattr(self, "_v3_slider"):
            self._v3_slider._apply_theme(self._modo)
        if hasattr(self, "_emotion_chips"):
            accent = C("accent", self._modo)
            bg_active = C("accent_soft", self._modo)
            for chip in self._emotion_chips:
                chip.setStyleSheet(
                    f"QPushButton {{ color: {text2}; "
                    f"background: {surface_2}; "
                    f"border: 1px solid {border_solid}; "
                    "border-radius: 15px; padding: 3px 12px; "
                    "min-height: 20px; max-height: 20px; "
                    f"font-size: {TYPOGRAPHY['size_caption']}px; }}"
                    f"QPushButton:hover {{ color: {accent}; "
                    f"background: {bg_active}; border-color: {accent}; }}"
                    f"QPushButton:checked {{ color: {accent}; "
                    f"background: {bg_active}; border-color: {accent}; }}"
                )

    # ── theme switch ─────────────────────────────────────────────────────────

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_txt_nota"):
            if hasattr(self._txt_nota, "_apply_theme"):
                self._txt_nota._apply_theme(self._modo)
        if hasattr(self, "_wave_chart"):
            self._wave_chart._apply_theme(self._modo)
        if hasattr(self, "_hero"):
            self._hero._apply_theme(self._modo)
        if hasattr(self, "_hist_card"):
            self._hist_card._apply_theme(self._modo)
        if hasattr(self, "_slider_card"):
            self._slider_card._apply_theme(self._modo)
        if hasattr(self, "_note_card"):
            self._note_card._apply_theme(self._modo)
        if hasattr(self, "_stat_cards"):
            for card in self._stat_cards:
                card._apply_theme(self._modo)
        if hasattr(self, "_celebration"):
            self._celebration._modo = self._modo
        self._apply_text_styles()
        self.update()

    def _check_and_sync_window_theme(self):
        win = self.window()
        if win and hasattr(win, "_modo"):
            win_modo = getattr(win, "_modo")
            if win_modo and win_modo != self._modo:
                self._on_theme(win_modo)

    def paintEvent(self, event):
        self._check_and_sync_window_theme()
        super().paintEvent(event)

    # ── slider callbacks ─────────────────────────────────────────────────────

    def _on_level_changed(self, level: int):
        """Actualiza puntaje interno cuando la escala cambia."""
        # 4.1: primer movimiento del slider → puntaje real + botón habilitado.
        # Antes el slider arrancaba con level=5 ya seteado y "5/10" hardcodeado;
        # el paciente veía un valor sin haber elegido nada.
        if not getattr(self, "_slider_touched", False):
            self._slider_touched = True
        self.puntaje = int(level)
        _, message = _mood_care(self.puntaje)
        if hasattr(self, "_v3_slider"):
            self._v3_slider.set_subtitle(message)
        if hasattr(self, "_slider_score"):
            self._slider_score.setText(f"{self.puntaje}/10")
            self._slider_score.setStyleSheet(
                f"color: {v3c('accent', self._modo).name()}; background: transparent;"
            )
        if hasattr(self, "_hero"):
            self._hero.set_level(self.puntaje)
        if hasattr(self, "_btn_reg"):
            self._btn_reg.setEnabled(True)
        self._apply_text_styles()

    def _on_emotion_chip_clicked(self, chip: QPushButton):
        """Selección exclusiva del chip de emoción. Click en chip activo lo deselecciona."""
        if not hasattr(self, "_emocion_por_chip"):
            return
        if chip.isChecked():
            for other in self._emocion_por_chip:
                if other is not chip and other.isChecked():
                    other.blockSignals(True)
                    other.setChecked(False)
                    other.blockSignals(False)
            self._emocion_actual = self._emocion_por_chip.get(chip)
        else:
            if self._emocion_por_chip.get(chip) == self._emocion_actual:
                self._emocion_actual = None

    def _on_note_changed(self):
        text = self._txt_nota.toPlainText()
        n = len(text)
        if n > 500:
            self._txt_nota.blockSignals(True)
            cursor = self._txt_nota.textCursor()
            cursor_pos = cursor.position()
            self._txt_nota.setPlainText(text[:500])
            cursor = self._txt_nota.textCursor()
            cursor.setPosition(min(cursor_pos, 500))
            self._txt_nota.setTextCursor(cursor)
            self._txt_nota.blockSignals(False)
            n = 500
        # Color del contador: si > 450 → warning, sino ink_secondary
        if n > 450:
            color = v3c("warning", self._modo).name()
        else:
            color = v3c("ink_secondary", self._modo).name()
        self._note_counter.setText(f"{n}/500")
        self._note_counter.setStyleSheet(f"color: {color}; background: transparent;")

    # ── streak (lógica preservada) ────────────────────────────────────────────

    def _load_streak(self) -> int:
        """Días consecutivos con registro de ánimo (tabla termometro)."""
        if visual_qa_enabled():
            return 7
        try:
            import datetime as dt

            con = obtener_conexion()
            rows = [
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT date(fecha) FROM termometro ORDER BY date(fecha) DESC LIMIT 30"
                ).fetchall()
            ]
            today = dt.date.today()
            streak = 0
            for i, d_str in enumerate(rows):
                if str(today - dt.timedelta(days=i)) == d_str:
                    streak += 1
                else:
                    break
            return streak
        except Exception:
            _log.exception("Error calculando streak")
            return 0

    # ── data fetchers (lectura) ──────────────────────────────────────────────

    def _get_valence_series(self) -> tuple[list, list]:
        """(positiva, negativa) — intensidad cruda promedio por día, 7+7."""
        from shared.utils import get_weekly_valence_series

        return get_weekly_valence_series()

    def _cargar_grafico(self):
        """Carga datos en el NMWaveChart: línea principal = registros positivos,
        línea secundaria = registros negativos (intensidad cruda por día)."""
        if not hasattr(self, "_wave_chart"):
            return
        positiva, negativa = self._get_valence_series()
        self._wave_chart.set_data(positiva, negativa)

    def _refresh_insights(self):
        """Actualiza los 3 stats: positivo 7d / negativo 7d / progreso."""
        positiva, negativa = self._get_valence_series()

        p_valid = [v for v in positiva if v is not None]
        if hasattr(self, "_stat_avg"):
            self._stat_avg.set_value(
                f"{sum(p_valid) / len(p_valid):.1f}/10" if p_valid else "—"
            )
            self._stat_avg.set_message("Promedio de tus registros positivos.")
            self._stat_avg.set_tone("primary" if p_valid else None)

        n_valid = [v for v in negativa if v is not None]
        if hasattr(self, "_stat_prog"):
            self._stat_prog.set_value(
                f"{sum(n_valid) / len(n_valid):.1f}/10" if n_valid else "—"
            )
            self._stat_prog.set_message("Promedio de tus registros negativos.")
            self._stat_prog.set_tone("danger" if n_valid else None)
            self._stat_prog.set_delta("", positive=None)

        streak = self._load_streak()
        if hasattr(self, "_stat_streak"):
            self._stat_streak.set_value("1 día" if streak == 1 else f"{streak} días")
            self._stat_streak.set_message("Días seguidos con registro.")
            self._stat_streak.set_tone("primary" if streak else None)

    # ── registrar (lógica preservada exacta) ─────────────────────────────────

    def _registrar(self):
        if getattr(self, "puntaje", None) is None:
            NMToast.display(
                self.window(),
                "Desliza para indicar cómo te sientes antes de guardar.",
                variant="warning",
            )
            return
        # Emoción OBLIGATORIA: sin una de las 6 opciones no hay valencia y el
        # registro caía del lado positivo aunque fuera tristeza (feedback owner).
        if not self._emocion_actual:
            NMToast.display(
                self.window(),
                "Selecciona una emoción (Calma, Tensión, Tristeza, Energía, "
                "Cansancio o Gratitud) antes de guardar.",
                variant="warning",
            )
            return

        emocion = self._emocion_actual or ""
        intensidad = int(self.puntaje)
        puntaje_wellbeing = bienestar_desde_emocion(emocion, intensidad)
        # Registro pos/neg separado: la valencia y la intensidad CRUDA se
        # guardan explícitas. "Tristeza 10" es un registro NEGATIVO fuerte,
        # no "ánimo 1" — el bienestar combinado se conserva para continuidad,
        # pero las métricas separan ambos lados.
        valencia = valencia_de_emocion(emocion)
        nota = self._txt_nota.toPlainText().strip()[:500]
        if visual_qa_enabled():
            self._txt_nota.clear()
            self._cargar_grafico()
            self._refresh_insights()
            if hasattr(self._btn_reg, "play_success"):
                self._btn_reg.play_success()
            NMToast.display(
                self.window(),
                f"Registro guardado. Tu ánimo de hoy: {puntaje_wellbeing}/10.",
                variant="success",
                duration_ms=1800,
            )
            self._trigger_celebration_if_needed(emocion, intensidad)
            return
        try:
            with conexion() as conn:
                conn.execute(
                    "INSERT INTO termometro "
                    "(fecha, hora, puntaje, emocion, nota, valencia, intensidad) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        fecha_hoy(),
                        hora_actual(),
                        puntaje_wellbeing,
                        emocion,
                        nota,
                        valencia,
                        intensidad,
                    ),
                )
            self._txt_nota.clear()
            try:
                from shared.sync import sync_inmediato_background

                sync_inmediato_background()
            except Exception:
                pass
            self._cargar_grafico()
            self._refresh_insights()
            if hasattr(self._btn_reg, "play_success"):
                self._btn_reg.play_success()
            NMToast.display(
                self.window(),
                f"Registro guardado. Tu ánimo de hoy: {puntaje_wellbeing}/10.",
                variant="success",
            )
            self._trigger_celebration_if_needed(emocion, intensidad)
        except Exception:
            _log.exception("Operation failed")

    def _trigger_celebration_if_needed(self, emocion: str, intensidad: int | None = None):
        """El confeti es refuerzo POSITIVO: solo se dispara con emociones
        positivas (Calma, Energía, Gratitud) en intensidad CRUDA 7-10.

        Una emoción negativa nunca lo dispara aunque su bienestar invertido sea
        alto (p. ej. Cansancio nivel 1 → bienestar 10): ese era el bug — se
        gatillaba sobre el bienestar, no sobre la valencia/intensidad reales.
        Tiers: 7-8 leve, 9 media, 10 mayor (definición owner).
        """
        if valencia_de_emocion(emocion) != "positiva":
            return
        if intensidad is None or int(intensidad) < 7:
            return
        if not hasattr(self, "_celebration"):
            return
        origin = self._btn_reg.mapTo(self._content, self._btn_reg.rect().center())
        self._celebration.launch(origin.x(), origin.y(), score=int(intensidad))

    # ── hooks NMModule ───────────────────────────────────────────────────────

    def on_enter(self):
        self._cargar_grafico()
        self._refresh_insights()

    def on_leave(self):
        if hasattr(self, "_celebration"):
            self._celebration.stop()

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "9/10"
        try:
            conn = obtener_conexion()
            # Promedio REAL del día (no el último registro) — coherente con el
            # hero del Home (feedback owner v1.0).
            row = conn.execute(
                "SELECT AVG(puntaje) FROM termometro WHERE fecha=?",
                (fecha_hoy(),),
            ).fetchone()
            conn.close()
            if row and row[0] is not None:
                avg = float(row[0])
                return f"{int(avg)}/10" if avg == int(avg) else f"{avg:.1f}/10"
        except Exception:
            _log.exception("Operation failed")
        return ""
