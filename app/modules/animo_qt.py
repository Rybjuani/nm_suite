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
    Qt, QTimer, QAbstractAnimation, QPointF,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QScrollArea, QSizePolicy, QFrame,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMCard, NMWaveChart, NMModuleRing, V3MoodSlider,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMCard, NMWaveChart, NMModuleRing, V3MoodSlider,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled


# ── Tokens de negocio preservados (chips historial + celebration) ────────────

COLORES_PUNTAJE = {
    1: "#ef4444", 2: "#f97316", 3: "#fb923c",
    4: "#fbbf24", 5: "#facc15", 6: "#a3e635", 7: "#4ade80",
    8: "#22d3ee", 9: "#06b6d4", 10: "#14b8a6",
}


# ── MoodCelebration: partículas cuando se registra mood ≥ 7 ──────────────────

class _MoodParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -2)
        self.alpha = 255
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

    def launch(self, x: float, y: float):
        if not self.parent():
            return
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        palette = [
            v3c("teal", self._modo).name(),
            v3c("gradFrom", self._modo).name(),
            v3c("gradMid", self._modo).name(),
            v3c("violet", self._modo).name(),
        ]
        for _ in range(36):
            self._particles.append(
                _MoodParticle(x, y, random.choice(palette))
            )
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
            p.alpha = max(0, p.alpha - 6)
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

    def __init__(self, label: str, value: str, pct: float,
                 modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._label_text = label
        self._value_text = value
        self._pct = max(0.0, min(1.0, pct))
        self._build()

    def _build(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                              V3_SP["lg"], V3_SP["lg"])
        h.setSpacing(V3_SP["md"])

        self._ring = NMModuleRing(size=56, pct=self._pct, modo=self._modo)
        h.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._label_lbl = QLabel(self._label_text)
        self._label_lbl.setFont(qfont("size_caption_xs",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._label_lbl)
        self._value_lbl = QLabel(self._value_text)
        self._value_lbl.setFont(qfont("size_h2",
                                       weight=TYPOGRAPHY["weight_bold"]))
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
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        self._value_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_insight_styles()


# ── ModuloAnimo v3 ──────────────────────────────────────────────────────────

class ModuloAnimo(NMModule):
    MODULE_TITLE = "Mood Tracker"
    MODULE_ICON = "animo"

    # ── build ────────────────────────────────────────────────────────────────

    def build_ui(self):
        self.puntaje = 5

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scroll para overflow (insights row + nota + slider + wave es alto)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(self._scroll)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        self._scroll.setWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["lg"])

        # 1. Header row con eyebrow del rango
        header_row = QHBoxLayout()
        self._range_lbl = QLabel("ÚLTIMOS 7 DÍAS")
        self._range_lbl.setFont(
            qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        header_row.addWidget(self._range_lbl)
        header_row.addStretch()
        lay.addLayout(header_row)

        # 2. Wave chart card (altura 280)
        wave_card = NMCard(modo=self._modo, clickable=False, glow=False)
        wave_lay = QVBoxLayout(wave_card)
        wave_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                     V3_SP["lg"], V3_SP["lg"])
        self._wave_chart = NMWaveChart(modo=self._modo)
        self._wave_chart.setMinimumHeight(280)
        self._wave_chart.setMaximumHeight(280)
        wave_lay.addWidget(self._wave_chart)
        lay.addWidget(wave_card)
        self._wave_card = wave_card

        # 3. V3MoodSlider card con glow
        slider_card = NMCard(modo=self._modo, clickable=False, glow=True)
        slider_lay = QVBoxLayout(slider_card)
        slider_lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                                       V3_SP["xl"], V3_SP["xl"])
        self._mood_slider = V3MoodSlider(level=5, modo=self._modo)
        self._mood_slider.level_changed.connect(self._on_level_changed)
        slider_lay.addWidget(self._mood_slider)
        lay.addWidget(slider_card)
        self._slider_card = slider_card

        # 4. Nota del día card
        note_card = NMCard(modo=self._modo, clickable=False, glow=False)
        note_lay = QVBoxLayout(note_card)
        note_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                     V3_SP["lg"], V3_SP["lg"])
        note_lay.setSpacing(V3_SP["sm"])

        note_header = QHBoxLayout()
        self._note_eyebrow = QLabel("NOTA DEL DÍA")
        self._note_eyebrow.setFont(
            qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        note_header.addWidget(self._note_eyebrow)
        note_header.addStretch()
        self._note_counter = QLabel("0/500")
        self._note_counter.setFont(qfont_mono(10, bold=False))
        note_header.addWidget(self._note_counter)
        note_lay.addLayout(note_header)

        self._txt_nota = QTextEdit()
        self._txt_nota.setMinimumHeight(96)
        self._txt_nota.setMaximumHeight(140)
        self._txt_nota.setPlaceholderText("¿Qué influyó en tu estado hoy?")
        self._txt_nota.setStyleSheet(stylesheet_textedit(self._modo))
        self._txt_nota.textChanged.connect(self._on_note_changed)
        note_lay.addWidget(self._txt_nota)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_reg = NMButton("Guardar registro", modo=self._modo,
                                  variant="gradient", size="md", width=180)
        self._btn_reg.clicked.connect(self._registrar)
        btn_row.addWidget(self._btn_reg)
        note_lay.addLayout(btn_row)
        lay.addWidget(note_card)
        self._note_card = note_card

        # 5. Insights row (Promedio / Racha / Progreso)
        insights_row = QHBoxLayout()
        insights_row.setSpacing(V3_SP["md"])
        self._insight_avg = _InsightCard(
            "PROMEDIO 7 DÍAS", "—", 0.0, modo=self._modo)
        self._insight_streak = _InsightCard(
            "RACHA ACTUAL", "0 días", 0.0, modo=self._modo)
        self._insight_progress = _InsightCard(
            "PROGRESO SEMANAL", "—", 0.0, modo=self._modo)
        for c in (self._insight_avg, self._insight_streak,
                  self._insight_progress):
            insights_row.addWidget(c, stretch=1)
        lay.addLayout(insights_row)

        # Datos iniciales
        self._cargar_grafico()
        self._refresh_insights()
        self._apply_text_styles()

        # Celebration overlay (partículas mood ≥ 7)
        self._celebration = MoodCelebration(self._content, self._modo)

    # ── styles helper ────────────────────────────────────────────────────────

    def _apply_text_styles(self):
        self._range_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        self._note_eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        self._note_counter.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")

    # ── theme switch ─────────────────────────────────────────────────────────

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_txt_nota"):
            self._txt_nota.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_wave_chart"):
            self._wave_chart._apply_theme(self._modo)
        if hasattr(self, "_mood_slider"):
            self._mood_slider._apply_theme(self._modo)
        if hasattr(self, "_celebration"):
            self._celebration._modo = self._modo
        if hasattr(self, "_range_lbl"):
            self._apply_text_styles()
        # Insights y cards heredados se auto-refrescan vía ThemeManager
        self.update()

    # ── slider callbacks ─────────────────────────────────────────────────────

    def _on_level_changed(self, level: int):
        """Actualiza puntaje interno cuando el V3MoodSlider cambia."""
        self.puntaje = int(level)

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
        # Color del contador: si > 450 → warning, sino text3
        if n > 450:
            color = v3c("warning", self._modo).name()
        else:
            color = v3c("text3", self._modo).name()
        self._note_counter.setText(f"{n}/500")
        self._note_counter.setStyleSheet(
            f"color: {color}; background: transparent;")

    # ── streak (lógica preservada) ────────────────────────────────────────────

    def _load_streak(self) -> int:
        """Días consecutivos con registro de ánimo (tabla termometro)."""
        if visual_qa_enabled():
            return 7
        try:
            import datetime as dt
            con = obtener_conexion()
            rows = [r[0] for r in con.execute(
                "SELECT DISTINCT date(fecha) FROM termometro "
                "ORDER BY date(fecha) DESC LIMIT 30"
            ).fetchall()]
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

    def _get_weekly_series(self) -> tuple[list, list]:
        """(current_week, previous_week) — 7 floats/None cada uno."""
        if visual_qa_enabled():
            return ([5, 6, 7, 8, 7, 9, 9],
                    [4, 5, 6, 6, 7, 7, 8])
        try:
            import datetime as dt
            con = obtener_conexion()
            today = dt.date.today()
            current, previous = [], []
            for offset in range(6, -1, -1):
                day = today - dt.timedelta(days=offset)
                row = con.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?",
                    (str(day),)).fetchone()
                current.append(
                    float(row[0]) if row and row[0] is not None else None)
                day_prev = day - dt.timedelta(days=7)
                row2 = con.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?",
                    (str(day_prev),)).fetchone()
                previous.append(
                    float(row2[0]) if row2 and row2[0] is not None else None)
            return current, previous
        except Exception:
            _log.exception("Error cargando series de ánimo")
            return [None] * 7, [None] * 7

    def _cargar_grafico(self):
        """Carga datos en el NMWaveChart."""
        if not hasattr(self, "_wave_chart"):
            return
        current, previous = self._get_weekly_series()
        self._wave_chart.set_data(current, previous)

    def _refresh_insights(self):
        """Actualiza los 3 insights cards a partir de los datos semanales."""
        current, previous = self._get_weekly_series()

        # Promedio (current week)
        c_valid = [v for v in current if v is not None]
        if c_valid:
            avg = sum(c_valid) / len(c_valid)
            self._insight_avg.set_value(f"{avg:.1f}/10", avg / 10.0)
        else:
            self._insight_avg.set_value("—", 0.0)

        # Racha
        streak = self._load_streak()
        days_label = "1 día" if streak == 1 else f"{streak} días"
        self._insight_streak.set_value(days_label, min(streak / 10.0, 1.0))

        # Progreso semanal (delta avg current vs previous)
        p_valid = [v for v in previous if v is not None]
        if c_valid and p_valid:
            c_avg = sum(c_valid) / len(c_valid)
            p_avg = sum(p_valid) / len(p_valid)
            delta = c_avg - p_avg
            sign = "+" if delta >= 0 else ""
            self._insight_progress.set_value(
                f"{sign}{delta:.1f}", min(abs(delta) / 5.0, 1.0))
        else:
            self._insight_progress.set_value("—", 0.0)

    # ── registrar (lógica preservada exacta) ─────────────────────────────────

    def _registrar(self):
        nota = self._txt_nota.toPlainText().strip()[:500]
        if visual_qa_enabled():
            self._txt_nota.clear()
            self._cargar_grafico()
            self._refresh_insights()
            if hasattr(self._btn_reg, "play_success"):
                self._btn_reg.play_success()
            NMToast.display(self.window(),
                            f"Ánimo {self.puntaje}/10 registrado (demo visual)",
                            variant="success", duration_ms=1800)
            self._trigger_celebration_if_needed()
            return
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO termometro (fecha, hora, puntaje, nota) "
                "VALUES (?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), self.puntaje, nota),
            )
            conn.commit()
            conn.close()
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
                f"Ánimo {self.puntaje}/10 registrado",
                variant="success")
            self._trigger_celebration_if_needed()
        except Exception:
            _log.exception("Operation failed")

    def _trigger_celebration_if_needed(self):
        if self.puntaje >= 7 and hasattr(self, "_celebration"):
            origin = self._btn_reg.mapTo(
                self._content, self._btn_reg.rect().center())
            self._celebration.launch(origin.x(), origin.y())

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
            row = conn.execute(
                "SELECT puntaje FROM termometro "
                "WHERE fecha=? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                p = row[0] if isinstance(row, tuple) else row["puntaje"]
                return f"{p}/10"
        except Exception:
            _log.exception("Operation failed")
        return ""
