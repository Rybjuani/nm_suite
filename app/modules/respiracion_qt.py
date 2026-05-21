"""
app/modules/respiracion_qt.py — Módulo Respiración 4-7-8 v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Respiración):

  Header        eyebrow + pills de preset (3 / 5 / 10 min)
  2-col main    LEFT: BIG breath circle (340, stroke 14) + phase chips
                      + 3 controles NMPlayButton (play/stop/refresh)
                RIGHT rail: cronómetro mono / BPM (NMCalmBadge) / calm bar
  3 step cards  Inhala 4s / Mantén 7s / Exhala 8s
  Historial     4 mini cards con fecha + duración + ring de ciclos

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  TECNICA, FASES, PRESETS, CICLO_TOTAL
  _tick() con intervalo 100ms, _save_session(), get_card_status()
  _start(), _pause(), _stop(), _finish() (incluido winsound.Beep al finalizar)
"""

import os
import sys
import math
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QRadialGradient, QLinearGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QFrame,
    QScrollArea, QGridLayout,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, ThemeManager,
        NMCard, NMIcon, NMPlayButton, NMPhaseChip,
        NMCycleRing, NMCalmBadge, NMModuleRing, NMProgressLine,
        responsive_columns,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        interpolate_color, radial_glow_double,
        gradient_colors, v3c, v3_mode, V3_SP, V3_RD,
        ThemeAwareWidgetMixin, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY, V3_GRADIENTS
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, ThemeManager,
        NMCard, NMIcon, NMPlayButton, NMPhaseChip,
        NMCycleRing, NMCalmBadge, NMModuleRing, NMProgressLine,
        responsive_columns,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        interpolate_color, radial_glow_double,
        gradient_colors, v3c, v3_mode, V3_SP, V3_RD,
        ThemeAwareWidgetMixin, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY, V3_GRADIENTS
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled


# ── Constantes de negocio (preservadas exactas) ───────────────────────────────

TECNICA = "4-7-8"
FASES = [
    ("Inhala ↑", 4),
    ("Mantén",   7),
    ("Exhala ↓", 8),
]
CICLO_TOTAL = sum(f[1] for f in FASES)

PRESETS = [
    ("3 min",  3),
    ("5 min",  5),
    ("10 min", 10),
]

# Big ring v3: README "Big ring (size 340, stroke 14)"
_CANVAS_V3 = 340
_RING_STROKE = 14
_R_MIN = 110   # radio en reposo / exhala final
_R_MAX = 154   # radio máximo en inhala


def _v3_arc_lerp(p: QPainter, rect: QRectF, start_deg: float, span_deg: float,
                 pen_w: int, modo: str, segments: int = 48):
    """Pinta un arco con gradient firma v3 segmento-a-segmento.

    Versión local del helper (no importamos el privado de components_qt).
    """
    if abs(span_deg) < 0.1:
        return
    stops = V3_GRADIENTS[v3_mode(modo)]
    direction = 1 if span_deg > 0 else -1
    abs_span = abs(span_deg)

    def color_at(t):
        t = max(0.0, min(1.0, t))
        for i in range(len(stops) - 1):
            h0, t0 = stops[i]
            h1, t1 = stops[i + 1]
            if t0 <= t <= t1:
                local = (t - t0) / max(1e-9, t1 - t0)
                return QColor(interpolate_color(h0, h1, local))
        return QColor(stops[-1][0])

    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(segments):
        t0 = i / segments
        t1 = (i + 1) / segments
        mid_t = (t0 + t1) / 2
        pen = QPen(color_at(mid_t), pen_w, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        a0 = start_deg + direction * abs_span * t0
        a1 = start_deg + direction * abs_span * t1
        p.drawArc(rect, int(a0 * 16), int((a1 - a0) * 16))

    # Round caps manuales en los extremos
    cx, cy = rect.center().x(), rect.center().y()
    rx, ry = rect.width() / 2, rect.height() / 2
    cap_r = pen_w / 2
    for endpoint_t in (0.0, 1.0):
        ang = math.radians(start_deg + direction * abs_span * endpoint_t)
        px = cx + rx * math.cos(ang)
        py = cy - ry * math.sin(ang)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color_at(endpoint_t)))
        p.drawEllipse(QPointF(px, py), cap_r, cap_r)


# ── _BreathCircle v3 ─────────────────────────────────────────────────────────

class _BreathCircle(ThemeAwareWidgetMixin, QWidget):
    """Círculo de respiración v3 — 340px, stroke 14, gradient teal→violet.

    Animaciones (pyqtProperty):
      circle_radius: float  → radio del círculo relleno (pulsing breath)
      glow_alpha:    int    → intensidad del halo radial (0-255)
      text_opacity:  float  → fade del texto al cambiar de fase (0-1)
    """

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setFixedSize(_CANVAS_V3, _CANVAS_V3)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Estado visual
        self._circle_radius = float(_R_MIN)
        self._glow_alpha = 40
        self._text_opacity = 1.0
        self._phase_progress = 0.0
        self._session_progress = 0.0
        self._center_text = ""
        self._phase_text = ""

        # Animaciones
        self._anim_radius: QPropertyAnimation | None = None
        self._anim_glow: QPropertyAnimation | None = None
        self._anim_text_fade: QPropertyAnimation | None = None

        # Render timer 60 fps
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(self.update)

        self.setStyleSheet("background: transparent;")
        self._connect_theme()

    # ── pyqtProperties animables ──────────────────────────────────────────────

    def _get_circle_radius(self) -> float:
        return self._circle_radius

    def _set_circle_radius(self, v: float):
        self._circle_radius = v

    circle_radius = pyqtProperty(float, _get_circle_radius, _set_circle_radius)

    def _get_glow_alpha(self) -> int:
        return self._glow_alpha

    def _set_glow_alpha(self, v: int):
        self._glow_alpha = max(0, min(255, v))

    glow_alpha = pyqtProperty(int, _get_glow_alpha, _set_glow_alpha)

    def _get_text_opacity(self) -> float:
        return self._text_opacity

    def _set_text_opacity(self, v: float):
        self._text_opacity = v

    text_opacity = pyqtProperty(float, _get_text_opacity, _set_text_opacity)

    # ── API ───────────────────────────────────────────────────────────────────

    def update_data(self, phase_progress: float, session_progress: float,
                    center_text: str, phase_text: str, phase_idx: int):
        self._phase_progress = phase_progress
        self._session_progress = session_progress
        self._center_text = center_text
        self._phase_text = phase_text

    def animate_phase(self, phase_idx: int, phase_dur_s: int, expanding):
        self._start_rendering()
        dur = phase_dur_s * 1000

        # Animar radio
        if self._anim_radius:
            try:
                self._anim_radius.stop()
            except RuntimeError:
                pass
        self._anim_radius = QPropertyAnimation(self, b"circle_radius", self)
        self._anim_radius.setDuration(dur)
        self._anim_radius.setEasingCurve(QEasingCurve.Type.InOutSine)
        if expanding is True:
            self._anim_radius.setStartValue(float(_R_MIN))
            self._anim_radius.setEndValue(float(_R_MAX))
        elif expanding is False:
            self._anim_radius.setStartValue(float(_R_MAX))
            self._anim_radius.setEndValue(float(_R_MIN))
        else:
            self._circle_radius = float(_R_MAX)
        if expanding is not None:
            self._anim_radius.finished.connect(lambda: setattr(self, "_anim_radius", None))
            self._anim_radius.start()

        # Animar glow
        if self._anim_glow:
            try:
                self._anim_glow.stop()
            except RuntimeError:
                pass
        self._anim_glow = QPropertyAnimation(self, b"glow_alpha", self)
        self._anim_glow.setDuration(dur)
        self._anim_glow.setEasingCurve(QEasingCurve.Type.InOutSine)
        if expanding is True:
            self._anim_glow.setStartValue(40)
            self._anim_glow.setEndValue(120)
        elif expanding is False:
            self._anim_glow.setStartValue(120)
            self._anim_glow.setEndValue(40)
        else:
            self._glow_alpha = 100
        if expanding is not None:
            self._anim_glow.finished.connect(lambda: setattr(self, "_anim_glow", None))
            self._anim_glow.start()

    def animate_text_change(self):
        if self._anim_text_fade:
            try:
                self._anim_text_fade.stop()
            except RuntimeError:
                pass
        self._anim_text_fade = QPropertyAnimation(self, b"text_opacity", self)
        self._anim_text_fade.setDuration(300)
        self._anim_text_fade.setKeyValueAt(0.0, 1.0)
        self._anim_text_fade.setKeyValueAt(0.4, 0.0)
        self._anim_text_fade.setKeyValueAt(1.0, 1.0)
        self._anim_text_fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim_text_fade.finished.connect(lambda: setattr(self, "_anim_text_fade", None))
        self._anim_text_fade.start()

    def reset_idle(self):
        if self._anim_radius:
            try:
                self._anim_radius.stop()
            except RuntimeError:
                pass
            self._anim_radius = None
        if self._anim_glow:
            try:
                self._anim_glow.stop()
            except RuntimeError:
                pass
            self._anim_glow = None
        if self._anim_text_fade:
            try:
                self._anim_text_fade.stop()
            except RuntimeError:
                pass
            self._anim_text_fade = None
        self._stop_rendering()
        self._circle_radius = float(_R_MIN)
        self._glow_alpha = 40
        self._text_opacity = 1.0
        self._phase_progress = 0.0
        self._session_progress = 0.0
        self._center_text = ""
        self._phase_text = ""
        self.update()

    def _start_rendering(self):
        if self.isVisible() and not self._render_timer.isActive():
            self._render_timer.start(16)

    def _stop_rendering(self):
        if self._render_timer.isActive():
            self._render_timer.stop()

    def showEvent(self, event):
        super().showEvent(event)
        if self._phase_text or self._center_text:
            self._start_rendering()

    def hideEvent(self, event):
        self._stop_rendering()
        super().hideEvent(event)

    # ── paintEvent v3 ─────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        is_dark = "dark" in self._modo
        cx = cy = self.width() / 2

        # 1. Halo radial (color teal del tema, intensidad animada)
        halo_color = v3c("teal", self._modo)
        halo_r = self._circle_radius + 40
        glow = QRadialGradient(QPointF(cx, cy), halo_r)
        inner = QColor(halo_color); inner.setAlpha(self._glow_alpha)
        outer = QColor(halo_color); outer.setAlpha(0)
        glow.setColorAt(0.0, inner)
        glow.setColorAt(1.0, outer)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), halo_r, halo_r)

        # 4. Círculo relleno que respira (fill suave)
        r = self._circle_radius
        fill_grad = QRadialGradient(QPointF(cx, cy), r)
        base = v3c("teal", self._modo); base.setAlpha(48)
        rim = v3c("violet", self._modo); rim.setAlpha(22)
        fill_grad.setColorAt(0.0, base)
        fill_grad.setColorAt(1.0, rim)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill_grad))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Borde del círculo respirando (tono teal del tema)
        border_pen = QPen(v3c("teal", self._modo), 2)
        border_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(border_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # 6. Texto central con alpha precalculado por color.
        text_alpha = max(0, min(255, int(255 * self._text_opacity)))
        text_color = v3c("text", self._modo)
        text_color.setAlpha(text_alpha)
        phase_color = v3c("teal", self._modo)
        phase_color.setAlpha(text_alpha)

        # Número grande (segundos) — tipografía mono v3, escalada a tamaño
        p.setFont(qfont_mono(48, bold=False))
        p.setPen(QPen(text_color))
        text_rect_top = QRectF(0, cy - 50, self.width(), 60)
        p.drawText(text_rect_top, Qt.AlignmentFlag.AlignCenter,
                   self._center_text)

        # Nombre de fase
        if self._phase_text:
            p.setFont(qfont("size_small",
                            weight=TYPOGRAPHY["weight_semibold"]))
            p.setPen(QPen(phase_color))
            text_rect_bot = QRectF(0, cy + 16, self.width(), 24)
            p.drawText(text_rect_bot, Qt.AlignmentFlag.AlignCenter,
                       self._phase_text)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── StepCard v3 ──────────────────────────────────────────────────────────────

class _StepCard(NMCard):
    """Card de fase: ICONO/LABEL + segundos. Activa = glow + accent."""

    def __init__(self, label: str, secs: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._label_text = label
        self._secs_text = secs
        self._active = False
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setContentsMargins(V3_SP["md"], V3_SP["md"],
                              V3_SP["md"], V3_SP["md"])
        vl.setSpacing(2)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl = QLabel(self._label_text)
        self._lbl.setFont(qfont("size_small",
                                weight=TYPOGRAPHY["weight_semibold"]))
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self._lbl)
        self._secs_lbl = QLabel(self._secs_text)
        self._secs_lbl.setFont(qfont_mono(11, bold=False))
        self._secs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self._secs_lbl)
        self._apply_step_styles()

    def set_active(self, active: bool):
        if active != self._active:
            self._active = active
            self.set_glow(active)
            self._apply_step_styles()

    def _apply_step_styles(self):
        color_main = (v3c("teal", self._modo).name() if self._active
                      else v3c("text2", self._modo).name())
        color_sec = (v3c("teal", self._modo).name() if self._active
                     else v3c("text3", self._modo).name())
        self._lbl.setStyleSheet(
            f"color: {color_main}; background: transparent;")
        self._secs_lbl.setStyleSheet(
            f"color: {color_sec}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_step_styles()


# ── _HistorialCard ──────────────────────────────────────────────────────────

class _HistorialMiniCard(NMCard):
    """Card mini de sesión pasada: fecha + duración + ring de ciclos."""

    def __init__(self, fecha: str, hora: str, duracion: float, ciclos: int,
                 modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._fecha = fecha
        self._hora = hora
        self._duracion = duracion
        self._ciclos = ciclos
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["md"],
                                V3_SP["md"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        # Ring chico con % ciclos vs target (15 ciclos = full)
        ring_pct = min(self._ciclos / 15.0, 1.0)
        self._ring = NMModuleRing(size=40, pct=ring_pct, modo=self._modo)
        lay.addWidget(self._ring)

        col = QVBoxLayout()
        col.setSpacing(0)
        self._date_lbl = QLabel(self._format_date())
        self._date_lbl.setFont(qfont("size_caption",
                                      weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._date_lbl)
        self._dur_lbl = QLabel(self._format_duration())
        self._dur_lbl.setFont(qfont("size_caption_xs"))
        col.addWidget(self._dur_lbl)
        lay.addLayout(col, stretch=1)
        self._apply_hist_styles()

    def _format_date(self) -> str:
        try:
            import datetime as dt
            d = dt.datetime.strptime(self._fecha, "%Y-%m-%d").date()
            today = dt.date.today()
            if d == today:
                return f"Hoy · {self._hora[:5]}"
            if d == today - dt.timedelta(days=1):
                return f"Ayer · {self._hora[:5]}"
            return f"{d.strftime('%d/%m')} · {self._hora[:5]}"
        except Exception:
            return f"{self._fecha} {self._hora[:5]}"

    def _format_duration(self) -> str:
        return f"{self._duracion:g} min · {self._ciclos} ciclos"

    def _apply_hist_styles(self):
        self._date_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self._dur_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_hist_styles()


# ── ModuloRespiracion v3 ─────────────────────────────────────────────────────

class ModuloRespiracion(NMModule):
    MODULE_TITLE = "Respiración"
    MODULE_ICON = "respiracion"

    # ── build ────────────────────────────────────────────────────────────────

    def build_ui(self):
        # Estado preservado exacto
        self._running = False
        self._paused = False
        self._elapsed_ms = 0
        self._session_ms = 0
        self._duration_min = 5
        self._ciclos = 0
        self._timer_id: QTimer | None = None
        self._phase_idx = 0
        self._phase_ms = 0
        self._last_phase_idx = -1

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(scroll)
        self._scroll = scroll

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        scroll.setWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["lg"])

        # 1. Eyebrow + pills de preset
        header_row = QHBoxLayout()
        self._range_lbl = QLabel("RESPIRACIÓN 4-7-8")
        self._range_lbl.setFont(
            qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        header_row.addWidget(self._range_lbl)
        header_row.addStretch()
        # Pills
        self._pill_btns: list[tuple[NMButtonOutline, int]] = []
        for label, mins in PRESETS:
            btn = NMButtonOutline(label, modo=self._modo,
                                   toggleable=False, size="sm")
            btn.setFixedSize(80, 32)
            btn.clicked.connect(lambda _, m=mins: self._select_preset(m))
            header_row.addWidget(btn)
            self._pill_btns.append((btn, mins))
        lay.addLayout(header_row)
        self._highlight_preset(5)

        # 2. Main responsive grid: breath circle + metrics rail
        self._main_grid = QGridLayout()
        self._main_grid.setContentsMargins(0, 0, 0, 0)
        self._main_grid.setHorizontalSpacing(V3_SP["xl"])
        self._main_grid.setVerticalSpacing(V3_SP["lg"])

        # ── LEFT col ─────────────────────────────────────────────────────────
        self._breath_left_panel = QWidget()
        self._breath_left_panel.setStyleSheet("background: transparent;")
        left_col = QVBoxLayout(self._breath_left_panel)
        left_col.setSpacing(V3_SP["lg"])
        left_col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._circle = _BreathCircle(self._content, self._modo)
        left_col.addWidget(self._circle,
                           alignment=Qt.AlignmentFlag.AlignHCenter)

        # Phase chips
        self._phase_chip = NMPhaseChip(self._modo)
        left_col.addWidget(self._phase_chip,
                           alignment=Qt.AlignmentFlag.AlignHCenter)

        # Controles NMPlayButton: refresh / play|pause / stop
        ctrl_row = QHBoxLayout()
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ctrl_row.setSpacing(V3_SP["md"])

        self._btn_reset = NMPlayButton(icon_name="refresh", size="md",
                                        modo=self._modo)
        self._btn_reset.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_reset)

        self._btn_play = NMPlayButton(icon_name="play", size="lg",
                                       modo=self._modo)
        self._btn_play.clicked.connect(self._toggle_play_pause)
        ctrl_row.addWidget(self._btn_play)

        self._btn_stop = NMPlayButton(icon_name="stop", size="md",
                                       modo=self._modo)
        self._btn_stop.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_stop)

        left_col.addLayout(ctrl_row)
        self._main_grid.addWidget(self._breath_left_panel, 0, 0)

        # ── RIGHT rail ───────────────────────────────────────────────────────
        self._breath_right_panel = QWidget()
        self._breath_right_panel.setStyleSheet("background: transparent;")
        right_rail = QVBoxLayout(self._breath_right_panel)
        right_rail.setSpacing(V3_SP["md"])
        right_rail.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Cronómetro card (mono grande)
        chrono_card = NMCard(modo=self._modo, clickable=False)
        chrono_lay = QVBoxLayout(chrono_card)
        chrono_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                       V3_SP["lg"], V3_SP["lg"])
        chrono_lay.setSpacing(2)
        chrono_eyebrow = QLabel("CRONÓMETRO")
        chrono_eyebrow.setFont(qfont("size_caption_xs",
                                      weight=TYPOGRAPHY["weight_semibold"]))
        chrono_lay.addWidget(chrono_eyebrow)
        self._session_lbl = QLabel("00:00")
        self._session_lbl.setFont(qfont_mono(28, bold=False))
        chrono_lay.addWidget(self._session_lbl)
        self._chrono_meta = QLabel("Listo para comenzar")
        self._chrono_meta.setFont(qfont("size_caption"))
        chrono_lay.addWidget(self._chrono_meta)
        right_rail.addWidget(chrono_card)
        self._chrono_card = chrono_card
        self._chrono_eyebrow = chrono_eyebrow

        # BPM card (NMCalmBadge envuelto en NMCard mini)
        bpm_card = NMCard(modo=self._modo, clickable=False)
        bpm_lay = QVBoxLayout(bpm_card)
        bpm_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                    V3_SP["lg"], V3_SP["lg"])
        bpm_lay.setSpacing(V3_SP["sm"])
        bpm_eyebrow = QLabel("RITMO CARDÍACO")
        bpm_eyebrow.setFont(qfont("size_caption_xs",
                                   weight=TYPOGRAPHY["weight_semibold"]))
        bpm_lay.addWidget(bpm_eyebrow)
        self._calm_badge = NMCalmBadge(bpm=60, modo=self._modo)
        bpm_lay.addWidget(self._calm_badge,
                          alignment=Qt.AlignmentFlag.AlignLeft)
        right_rail.addWidget(bpm_card)
        self._bpm_card = bpm_card
        self._bpm_eyebrow = bpm_eyebrow

        # Calma card (barra de progreso v3)
        calm_card = NMCard(modo=self._modo, clickable=False)
        calm_lay = QVBoxLayout(calm_card)
        calm_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                     V3_SP["lg"], V3_SP["lg"])
        calm_lay.setSpacing(V3_SP["sm"])
        calm_eyebrow = QLabel("ESTADO DE CALMA")
        calm_eyebrow.setFont(qfont("size_caption_xs",
                                    weight=TYPOGRAPHY["weight_semibold"]))
        calm_lay.addWidget(calm_eyebrow)
        self._calm_bar = NMProgressLine(modo=self._modo)
        self._calm_bar.set_progress(0.45)
        calm_lay.addWidget(self._calm_bar)
        right_rail.addWidget(calm_card)
        self._calm_card = calm_card
        self._calm_eyebrow = calm_eyebrow

        right_rail.addStretch()

        self._main_grid.addWidget(self._breath_right_panel, 0, 1)
        lay.addLayout(self._main_grid)
        self._relayout_main_grid()

        # 3. 3 step cards (Inhala / Mantén / Exhala)
        step_row = QHBoxLayout()
        step_row.setSpacing(V3_SP["md"])
        self._step_cards: list[_StepCard] = []
        for label, secs in FASES:
            sc = _StepCard(label, f"{secs}s", modo=self._modo)
            step_row.addWidget(sc, stretch=1)
            self._step_cards.append(sc)
        lay.addLayout(step_row)

        # 4. Historial card (4 mini cards horizontal)
        hist_section_lbl = QLabel("ÚLTIMAS SESIONES")
        hist_section_lbl.setFont(qfont("size_caption_xs",
                                        weight=TYPOGRAPHY["weight_semibold"]))
        hist_section_lbl.setContentsMargins(0, V3_SP["sm"], 0, 0)
        lay.addWidget(hist_section_lbl)
        self._hist_section_lbl = hist_section_lbl

        self._hist_row_widget = QWidget()
        self._hist_row = QHBoxLayout(self._hist_row_widget)
        self._hist_row.setSpacing(V3_SP["md"])
        self._hist_row.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._hist_row_widget)

        self._cargar_historial()
        self._apply_text_styles()

    def _relayout_main_grid(self):
        if not hasattr(self, "_main_grid"):
            return
        self._main_grid.removeWidget(self._breath_left_panel)
        self._main_grid.removeWidget(self._breath_right_panel)
        width = max(
            360,
            self._scroll.viewport().width() if hasattr(self, "_scroll") else self.width(),
        )
        cols = responsive_columns(width, min_card_width=420, max_columns=2)
        if cols >= 2:
            self._main_grid.addWidget(self._breath_left_panel, 0, 0)
            self._main_grid.addWidget(self._breath_right_panel, 0, 1)
            self._main_grid.setColumnStretch(0, 2)
            self._main_grid.setColumnStretch(1, 1)
        else:
            self._main_grid.addWidget(self._breath_left_panel, 0, 0)
            self._main_grid.addWidget(self._breath_right_panel, 1, 0)
            self._main_grid.setColumnStretch(0, 1)
            self._main_grid.setColumnStretch(1, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_main_grid()

    def _apply_text_styles(self):
        c = v3c("text3", self._modo).name()
        for lbl in (self._range_lbl, self._chrono_eyebrow, self._bpm_eyebrow,
                     self._calm_eyebrow, self._hist_section_lbl):
            lbl.setStyleSheet(f"color: {c}; background: transparent;")
        self._session_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self._chrono_meta.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;")

    # ── theme ────────────────────────────────────────────────────────────────

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_circle"):
            self._circle._apply_theme(self._modo)
        if hasattr(self, "_phase_chip"):
            self._phase_chip._apply_theme(self._modo)
        if hasattr(self, "_calm_badge"):
            self._calm_badge._apply_theme(self._modo)
        if hasattr(self, "_calm_bar"):
            self._calm_bar._modo = self._modo
            self._calm_bar.update()
        if hasattr(self, "_range_lbl"):
            self._apply_text_styles()
        self.update()

    # ── presets ──────────────────────────────────────────────────────────────

    def _select_preset(self, mins: int):
        if self._running:
            return
        self._duration_min = mins
        self._highlight_preset(mins)

    def _highlight_preset(self, selected: int):
        for btn, mins in self._pill_btns:
            btn.set_active(mins == selected)

    # ── controles ────────────────────────────────────────────────────────────

    def _toggle_play_pause(self):
        """Toggle único entre play / pause / resume (NMPlayButton spec v3)."""
        if not self._running:
            self._start()
        else:
            self._pause()

    def _start(self):
        if self._running:
            return
        self._running = True
        self._paused = False
        self._elapsed_ms = 0
        self._session_ms = 0
        self._ciclos = 0
        self._phase_idx = 0
        self._phase_ms = 0
        self._last_phase_idx = -1
        self._btn_play.set_icon("pause")
        self._chrono_meta.setText("En curso")
        self._tick()

    def _pause(self):
        if not self._running:
            return
        if self._paused:
            self._paused = False
            self._btn_play.set_icon("pause")
            self._chrono_meta.setText("En curso")
            self._circle._start_rendering()
            self._tick()
        else:
            self._paused = True
            self._btn_play.set_icon("play")
            self._chrono_meta.setText("Pausado")
            if self._timer_id:
                self._timer_id.stop()
                self._timer_id = None

    def _stop(self):
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        if self._running and self._ciclos > 0:
            self._save_session()
        self._running = False
        self._paused = False
        self._btn_play.set_icon("play")
        self._circle.reset_idle()
        self._session_lbl.setText("00:00")
        self._chrono_meta.setText("Listo para comenzar")
        if hasattr(self, "_phase_chip"):
            self._phase_chip.set_phase(None)
        for sc in getattr(self, "_step_cards", []):
            sc.set_active(False)
        self._cargar_historial()

    # ── tick (lógica preservada) ─────────────────────────────────────────────

    def _tick(self):
        try:
            if not self._running or self._paused:
                return

            total_ms = self._duration_min * 60 * 1000
            interval = 100

            if self._elapsed_ms >= total_ms:
                self._finish()
                return

            phase_name, phase_dur = FASES[self._phase_idx]
            phase_dur_ms = phase_dur * 1000
            phase_progress = self._phase_ms / phase_dur_ms

            if self._phase_idx != self._last_phase_idx:
                self._last_phase_idx = self._phase_idx
                self._on_phase_change(self._phase_idx, phase_dur)
                self._circle.animate_text_change()
                for i, sc in enumerate(self._step_cards):
                    sc.set_active(i == self._phase_idx)

            secs_left = max(0, phase_dur - int(self._phase_ms / 1000))
            session_progress = self._elapsed_ms / total_ms
            self._circle.update_data(
                phase_progress=phase_progress,
                session_progress=session_progress,
                center_text=str(secs_left),
                phase_text=phase_name,
                phase_idx=self._phase_idx,
            )

            _PHASE_KEYS = ["inhala", "manten", "exhala"]
            if hasattr(self, "_phase_chip"):
                self._phase_chip.set_phase(_PHASE_KEYS[self._phase_idx])

            if hasattr(self, "_calm_bar"):
                calm_target = 0.45 + session_progress * 0.5
                self._calm_bar.set_progress(min(calm_target, 0.95))

            self._session_ms += interval
            s_total = self._session_ms // 1000
            self._session_lbl.setText(f"{s_total // 60:02d}:{s_total % 60:02d}")

            self._phase_ms += interval
            self._elapsed_ms += interval

            if self._phase_ms >= phase_dur_ms:
                self._phase_ms = 0
                self._phase_idx += 1
                if self._phase_idx >= len(FASES):
                    self._phase_idx = 0
                    self._ciclos += 1

            if self._timer_id is None:
                self._timer_id = QTimer(self)
                self._timer_id.timeout.connect(self._tick)
            self._timer_id.start(interval)
        except Exception as e:
            _log.error(f"Error in _tick: {e}")
            import traceback
            traceback.print_exc()
            self._running = False

    def _on_phase_change(self, phase_idx: int, phase_dur: int):
        if phase_idx == 0:
            self._circle.animate_phase(phase_idx, phase_dur, expanding=True)
        elif phase_idx == 1:
            self._circle.animate_phase(phase_idx, phase_dur, expanding=None)
        elif phase_idx == 2:
            self._circle.animate_phase(phase_idx, phase_dur, expanding=False)

    def _finish(self):
        self._running = False
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        self._save_session()
        self._circle.reset_idle()
        if hasattr(self, "_phase_chip"):
            self._phase_chip.set_phase(None)
        for sc in self._step_cards:
            sc.set_active(False)
        self._session_lbl.setText("00:00")
        self._chrono_meta.setText(f"Completo · {self._ciclos} ciclos")
        self._btn_play.set_icon("play")
        try:
            import winsound
            winsound.Beep(800, 300)
        except Exception:
            _log.exception("Operation failed")
        self._cargar_historial()

    # ── DB (preservado exacto) ───────────────────────────────────────────────

    def _save_session(self):
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO respiracion "
                "(fecha, hora, tecnica, duracion_minutos, ciclos) "
                "VALUES (?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), TECNICA,
                 round(self._elapsed_ms / 60000, 1), self._ciclos),
            )
            conn.commit()
            conn.close()
            try:
                from shared.sync import sync_inmediato_background
                sync_inmediato_background()
            except Exception:
                pass
        except Exception:
            _log.exception("Operation failed")

    # ── historial ────────────────────────────────────────────────────────────

    def _load_recent_sessions(self, limit: int = 4):
        if visual_qa_enabled():
            return [
                ("2026-05-17", "08:30", 5.0, 6),
                ("2026-05-16", "21:15", 10.0, 12),
                ("2026-05-16", "07:00", 3.5, 4),
                ("2026-05-15", "12:00", 5.0, 6),
            ]
        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT fecha, hora, duracion_minutos, ciclos FROM respiracion "
                "ORDER BY fecha DESC, hora DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            out = []
            for r in rows:
                if hasattr(r, "keys"):
                    out.append((r["fecha"], r["hora"],
                                float(r["duracion_minutos"] or 0),
                                int(r["ciclos"] or 0)))
                else:
                    out.append((r[0], r[1], float(r[2] or 0), int(r[3] or 0)))
            return out
        except Exception:
            _log.exception("Error cargando historial respiración")
            return []

    def _cargar_historial(self):
        # Clear
        while self._hist_row.count():
            item = self._hist_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        sessions = self._load_recent_sessions(4)
        if not sessions:
            empty = QLabel("Aún no hay sesiones registradas.")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            self._hist_row.addWidget(empty)
            self._hist_row.addStretch()
            return
        for fecha, hora, dur, ciclos in sessions:
            card = _HistorialMiniCard(fecha, hora, dur, ciclos,
                                        modo=self._modo)
            self._hist_row.addWidget(card, stretch=1)
        # Si hay menos de 4, rellenar con stretch
        if len(sessions) < 4:
            for _ in range(4 - len(sessions)):
                self._hist_row.addStretch()

    # ── hooks NMModule ───────────────────────────────────────────────────────

    def on_leave(self):
        self._stop()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM respiracion WHERE fecha=?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} sesión{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
