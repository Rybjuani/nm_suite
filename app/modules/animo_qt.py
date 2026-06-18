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
    QLabel,
    QFrame,
    QBoxLayout,
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
    from shared.utils import fecha_hoy, hora_actual, get_mood_series
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
    from shared.utils import fecha_hoy, hora_actual, get_mood_series
    from shared.visual_qa import visual_qa_enabled


from shared.design_tokens import MOOD_PALETTE
from shared.remote_config import t


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
        # 2026-06: minimumHeight 182→224 para balancear la columna derecha con la
        # izquierda (slider card ocupa ~280px) — sin esto, el chart queda
        # pequeño y las stats se "amontonan" abajo con stretch vacío entre
        # el chart y las cards.
        self._hist_card = NMChartPanel("Últimos días", modo=self._modo)
        self._hist_card.setMinimumHeight(224)
        self._range_lbl = None  # ya manejado internamente por NMChartPanel
        # Selector 7D/30D — el chart muestra el promedio DIARIO de los
        # registros (varios registros en el mismo día se promedian a un solo
        # punto). El usuario puede alternar entre la vista semanal y mensual.
        self._chart_range_days = 7
        self._hist_card.set_header_tabs(
            ["7 días", "30 días"], self._on_chart_range_changed
        )

        # Serie ÚNICA: el valor de ánimo (puntaje) promediado por día. Sin separar
        # positivo/negativo — un solo punto diario, misma fórmula que Home y Hub.
        self._wave_chart = NMWaveChart(modo=self._modo)
        self._wave_chart.setMinimumHeight(110)
        self._wave_chart.setMaximumHeight(140)
        self._hist_card.set_chart(self._wave_chart)
        right_lay.addWidget(self._hist_card)

        # 2026-06: dos tarjetas de progreso (7 y 30 días) en lugar de una
        # sola "Progreso". Se integran directamente con el bloque superior
        # (sin stretch intermedio) para eliminar el vacío central.
        # El chart ya muestra 7/30 días por separado, así que las stats
        # tienen que reflejar el mismo rango para no quedar desfasadas.
        # Mismo tamaño mínimo (66px) para que la grilla vertical lea uniforme.
        self._stat_streak_7 = _CareStatCard(
            "Progreso 7 días",
            "0 días",
            "Días seguidos con registro esta semana.",
            modo=self._modo,
        )
        self._stat_streak_30 = _CareStatCard(
            "Progreso 30 días",
            "0 días",
            "Días seguidos con registro este mes.",
            modo=self._modo,
        )
        self._stat_cards = [self._stat_streak_7, self._stat_streak_30]
        for card in self._stat_cards:
            right_lay.addWidget(card)

        # 2. Registro del ánimo: escala sobria + mensaje de cuidado.
        slider_card = NMCard(modo=self._modo, clickable=False, glow=False)
        slider_lay = QVBoxLayout(slider_card)
        slider_lay.setContentsMargins(18, 12, 18, 12)
        slider_lay.setSpacing(6)

        slider_head = QHBoxLayout()
        slider_head.setSpacing(V3_SP["sm"])
        self._slider_eyebrow = QLabel(t("text.module.animo.slider_eyebrow", "Escala emocional"))
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
        # (2026-06: show_zero=False — la escala clínica visible es 1-10 sin tick
        # 0. El thumb sigue arrancando en la muesca 0 (unset), pero el número
        # 0 no se muestra en la fila de números.)
        self._v3_slider = V3MoodSlider(
            level=5,
            title=t("text.module.animo.slider_title", "¿Cómo te sientes hoy?"),
            subtitle=t("text.module.animo.slider_subtitle", "Desliza para indicar tu estado."),
            modo=self._modo,
            compact=True,
            unset=True,
            show_zero=False,
        )
        self._v3_slider.level_changed.connect(self._on_level_changed)
        slider_lay.addWidget(self._v3_slider)

        left_lay.addWidget(slider_card)
        self._slider_card = slider_card

        # 4. Botón guardar registro
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)
        btn_row.setSpacing(V3_SP["sm"])
        btn_row.addStretch()
        self._btn_reg = NMButton(
            t("text.module.animo.save_btn", "Guardar registro"), modo=self._modo, variant="gradient", size="md", width=180
        )
        self._btn_reg.setFixedHeight(34)
        self._btn_reg.setEnabled(False)
        self._btn_reg.clicked.connect(self._registrar)
        btn_row.addWidget(self._btn_reg)
        left_lay.addLayout(btn_row)

        # 2026-06: el stretch del final de cada columna ya no es necesario
        # (el de la derecha está entre el chart y las stats; el de la
        # izquierda se removió para que el botón Guardar quede pegado al
        # final de la columna, balanceando con las stats de la derecha).
        left_lay.addStretch()
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
        text2 = C("ink_secondary", self._modo)

        for lbl in (
            getattr(self, "_range_lbl", None),
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

    # ── theme switch ─────────────────────────────────────────────────────────

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_wave_chart"):
            self._wave_chart._apply_theme(self._modo)
        if hasattr(self, "_hist_card"):
            self._hist_card._apply_theme(self._modo)
        if hasattr(self, "_slider_card"):
            self._slider_card._apply_theme(self._modo)
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
        if hasattr(self, "_btn_reg"):
            self._btn_reg.setEnabled(True)
        self._apply_text_styles()

    # ── streak (lógica preservada) ────────────────────────────────────────────

    def _load_streak(self, days: int = 30) -> int:
        """Días consecutivos con registro de ánimo (tabla termometro).

        `days` limita la ventana de búsqueda (7 para la tarjeta semanal,
        30 para la mensual). En QA devuelve 7 días para la semanal y
        12 para la mensual (representativo sin saturar la tarjeta).
        """
        if visual_qa_enabled():
            return 7 if days <= 7 else 12
        try:
            import datetime as dt

            con = obtener_conexion()
            rows = [
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT date(fecha) FROM termometro ORDER BY date(fecha) DESC LIMIT ?",
                    (max(days, 60),),
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

    def _get_mood_series(self) -> list:
        """Serie diaria de ánimo (promedio de puntaje por día).

        Respeta ``self._chart_range_days`` (7D o 30D). Cada punto es el
        PROMEDIO de los registros del día (varios registros en el mismo día →
        un solo punto). Misma fuente/fórmula que el score del Home y el Hub.
        """
        return get_mood_series(self._chart_range_days)

    def _on_chart_range_changed(self, label: str) -> None:
        """Handler de los tabs 7D/30D del header del chart."""
        days_map = {"7 días": 7, "30 días": 30}
        self._chart_range_days = days_map.get(label, 7)
        try:
            self._cargar_grafico()
        except Exception:
            _log.exception("Error actualizando rango del chart de ánimo")

    def _cargar_grafico(self):
        """Carga la serie ÚNICA de ánimo (promedio diario de puntaje) en el chart."""
        if not hasattr(self, "_wave_chart"):
            return
        serie = self._get_mood_series()
        # NMWaveChart pinta dos series (principal/comparación); acá la comparación
        # va vacía → una sola línea con el ánimo diario real.
        self._wave_chart.set_data(serie, [None] * len(serie))

    def _refresh_insights(self):
        """Actualiza stats de progreso (rachas 7 y 30 días)."""
        streak_7 = self._load_streak(days=7)
        streak_30 = self._load_streak(days=30)
        if hasattr(self, "_stat_streak_7"):
            self._stat_streak_7.set_value("1 día" if streak_7 == 1 else f"{streak_7} días")
            self._stat_streak_7.set_message("Días seguidos con registro esta semana.")
            self._stat_streak_7.set_tone("primary" if streak_7 else None)
        if hasattr(self, "_stat_streak_30"):
            self._stat_streak_30.set_value("1 día" if streak_30 == 1 else f"{streak_30} días")
            self._stat_streak_30.set_message("Días seguidos con registro este mes.")
            self._stat_streak_30.set_tone("primary" if streak_30 else None)

    # ── registrar (lógica preservada exacta) ─────────────────────────────────

    def _registrar(self):
        if getattr(self, "puntaje", None) is None:
            NMToast.display(
                self.window(),
                "Desliza para indicar cómo te sientes antes de guardar.",
                variant="warning",
            )
            return
        intensidad = int(self.puntaje)
        puntaje_wellbeing = intensidad
        if visual_qa_enabled():
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
            return
        try:
            with conexion() as conn:
                # El módulo actual solo captura un puntaje 1-10.
                # No inventar emoción, valencia ni intensidad.
                conn.execute(
                    "INSERT INTO termometro "
                    "(fecha, hora, puntaje, nota) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        fecha_hoy(),
                        hora_actual(),
                        puntaje_wellbeing,
                        "",
                    ),
                )
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
        except Exception:
            _log.exception("Operation failed")

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
