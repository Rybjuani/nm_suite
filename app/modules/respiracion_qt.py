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
  _start(), _pause(), _stop(), _finish() (incluido NMRingPulse al finalizar)
"""

import os
import sys
from shared.crash_log import redact
import math
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRectF,
    QPointF,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QFrame,
    QScrollArea,
)

try:
    from shared.components_qt import (
        NMModule,
        NMButton,
        NMButtonOutline,
        ThemeManager,
        NMCard,
        NMIcon,
        NMPlayButton,
        NMPhaseChip,
        NMCycleRing,
        NMCalmBadge,
        NMModuleRing,
        NMProgressLine,
        NMProgressBar,
        NMRingPulse,
        NMChip,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        interpolate_color,
        radial_glow_double,
        gradient_colors,
        v3c,
        v3_mode,
        V3_SP,
        V3_RD,
        ThemeAwareWidgetMixin,
        stylesheet_scrollarea,
        PAD_CONTAINER,
        eyebrow_font,
        nm_icon,
    )
    from shared.theme import TYPOGRAPHY, V3_GRADIENTS
    from shared.db import obtener_conexion, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule,
        NMButton,
        NMButtonOutline,
        NMCard,
        NMCalmBadge,
        NMModuleRing,
        NMProgressBar,
        NMRingPulse,
        NMChip,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        qfont_mono,
        interpolate_color,
        v3c,
        v3_mode,
        V3_SP,
        ThemeAwareWidgetMixin,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY, V3_GRADIENTS
    from shared.db import obtener_conexion, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled

from shared.remote_config import t


# ── Constantes de negocio ─────────────────────────────────────────────────────

TECNICA = "4-7-8"
FASES = [
    ("Inhala", 4),
    ("Mantiene", 7),
    ("Exhala", 8),
]
CICLO_TOTAL = sum(f[1] for f in FASES)

PRESETS = [
    ("3 min", 3),
    ("5 min", 5),
    ("10 min", 10),
]

# Big ring v6: Breathing orb — canvas con margen de seguridad: la extensión
# máxima real es R_MAX + ondulación (4.5) + partículas en órbita (3 + 2.5)
# ≈ 119px de radio; con canvas 220 (radio 110) la animación se recortaba en
# los 4 lados al expandir (feedback owner v1.0).
_CANVAS_V3 = 248
_RING_STROKE = 2
_R_MIN = 78   # radio en reposo / exhala final
_R_MAX = 109  # radio máximo en inhala

# ── Breathing Aurora — constantes de efectos visuales ────────────────────────
_N_PARTICLES        = 8      # puntos en órbita
_PARTICLE_SIZE      = 2.5    # radio de cada punto (px)
_PARTICLE_ORBIT_OFF = 3.0    # px más allá del borde del círculo
_UNDULATION_LOBES   = 3      # lóbulos de la onda orgánica
_UNDULATION_AMP_MAX = 4.5    # amplitud máxima del borde ondulado (px)
_ORBIT_DEG_TICK     = 0.3    # °/tick → 18°/s → 1 vuelta cada 20 s
_UNDULATION_RAD_TICK= 0.008  # rad/tick → ~0.5°/tick → 1 rotación cada 12 s


def _v3_arc_lerp(
    p: QPainter,
    rect: QRectF,
    start_deg: float,
    span_deg: float,
    pen_w: int,
    modo: str,
    segments: int = 48,
):
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
        pen = QPen(color_at(mid_t), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
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
        self._glow_alpha = 76
        self._text_opacity = 1.0
        self._phase_progress = 0.0
        self._session_progress = 0.0
        self._center_text = ""
        self._phase_text = ""

        # Animaciones
        self._anim_radius: QPropertyAnimation | None = None
        self._anim_glow: QPropertyAnimation | None = None
        self._anim_text_fade: QPropertyAnimation | None = None
        self._anim_undulation: QPropertyAnimation | None = None

        # Breathing Aurora — estado continuo
        self._orbit_angle = 0.0          # °, avanza en cada tick
        self._undulation_phase = 0.0     # rad, rota continuamente
        self._undulation_amp = 0.0       # px, animado con la fase
        self._orbit_speed_mult = 1.0     # 1.0 normal, 1.2 inhala, 0.8 exhala

        # Render timer 60 fps
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(self._on_render_tick)

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

    def _get_undulation_amp(self) -> float:
        return self._undulation_amp

    def _set_undulation_amp(self, v: float):
        self._undulation_amp = max(0.0, min(_UNDULATION_AMP_MAX + 0.5, v))

    undulation_amp = pyqtProperty(float, _get_undulation_amp, _set_undulation_amp)

    # ── API ───────────────────────────────────────────────────────────────────

    def update_data(
        self,
        phase_progress: float,
        session_progress: float,
        center_text: str,
        phase_text: str,
        phase_idx: int,
    ):
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
            self._glow_alpha = 76
        if expanding is not None:
            self._anim_glow.finished.connect(lambda: setattr(self, "_anim_glow", None))
            self._anim_glow.start()

        # Animar ondulación orgánica + velocidad de órbita
        if self._anim_undulation:
            try:
                self._anim_undulation.stop()
            except RuntimeError:
                pass
        self._anim_undulation = QPropertyAnimation(self, b"undulation_amp", self)
        self._anim_undulation.setDuration(dur)
        self._anim_undulation.setEasingCurve(QEasingCurve.Type.InOutSine)
        if expanding is True:
            self._anim_undulation.setStartValue(0.0)
            self._anim_undulation.setEndValue(_UNDULATION_AMP_MAX)
            self._orbit_speed_mult = 1.2
        elif expanding is False:
            self._anim_undulation.setStartValue(_UNDULATION_AMP_MAX)
            self._anim_undulation.setEndValue(0.4)
            self._orbit_speed_mult = 0.8
        else:  # hold
            self._undulation_amp = _UNDULATION_AMP_MAX * 0.5
            self._orbit_speed_mult = 1.0
        if expanding is not None:
            self._anim_undulation.finished.connect(lambda: setattr(self, "_anim_undulation", None))
            self._anim_undulation.start()

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
        if self._anim_undulation:
            try:
                self._anim_undulation.stop()
            except RuntimeError:
                pass
            self._anim_undulation = None
        self._stop_rendering()
        self._circle_radius = float(_R_MIN)
        self._glow_alpha = 76
        self._text_opacity = 1.0
        self._phase_progress = 0.0
        self._session_progress = 0.0
        self._center_text = ""
        self._phase_text = ""
        self._undulation_amp = 0.0
        self._orbit_speed_mult = 1.0
        self.update()

    def _on_render_tick(self) -> None:
        self._orbit_angle = (self._orbit_angle + _ORBIT_DEG_TICK * self._orbit_speed_mult) % 360.0
        self._undulation_phase = (self._undulation_phase + _UNDULATION_RAD_TICK) % (2.0 * math.pi)
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

    # ── paintEvent — Breathing Aurora ─────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        cx = cy = self.width() / 2.0
        r = self._circle_radius
        active = bool(self._phase_text or self._center_text)

        # 1. Aurora bloom — 3 capas de gradiente radial
        self._draw_aurora_bloom(p, cx, cy, r)

        # 2. Borde orgánico — ondulado en movimiento, perfecto en reposo
        self._draw_organic_border(p, cx, cy, r)

        # 3. Partículas en órbita — solo cuando la sesión está activa
        if active:
            self._draw_particles(p, cx, cy, r)

        # 4. Textos (igual que antes)
        text_alpha = max(0, min(255, int(255 * self._text_opacity)))
        text_color = v3c("text", self._modo)
        text_color.setAlpha(text_alpha)
        phase_color = v3c("primary", self._modo)
        phase_color.setAlpha(text_alpha)

        try:
            from shared.theme_qt import v3_font as _v3_font
            p.setFont(_v3_font(44, weight=TYPOGRAPHY["weight_medium"], serif=True))
        except ImportError:
            p.setFont(qfont_mono(36, bold=False))
        p.setPen(QPen(text_color))
        p.drawText(QRectF(0, cy - 45, self.width(), 50),
                   Qt.AlignmentFlag.AlignCenter, self._center_text)

        if self._phase_text:
            p.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            p.setPen(QPen(phase_color))
            p.drawText(QRectF(0, cy + 15, self.width(), 20),
                       Qt.AlignmentFlag.AlignCenter, self._phase_text)
        p.end()

    # ── Breathing Aurora — helpers de render ──────────────────────────────────

    def _draw_aurora_bloom(self, p: QPainter, cx: float, cy: float, r: float) -> None:
        """3 capas de gradiente radial: teal core · violet mid · primary halo."""
        if r <= 0:
            return
        mult = self._glow_alpha / 120.0
        is_dark = "dark" in self._modo
        center = QPointF(cx, cy)
        p.setPen(Qt.PenStyle.NoPen)

        # Alphas base difieren por tema: dark → glow dramático; light → más sutil
        # porque el bg claro compite visualmente con el glow
        l1 = 130 if is_dark else 72
        l2 = 75  if is_dark else 40
        l3 = 30  if is_dark else 14

        # Layer 1 — núcleo teal (inner 65 % del radio)
        teal = QColor(v3c("teal", self._modo))
        g1 = QRadialGradient(center, r * 0.65)
        c_in = QColor(teal)
        c_in.setAlpha(int(l1 * mult))
        c_out = QColor(teal.red(), teal.green(), teal.blue(), 0)
        g1.setColorAt(0.0, c_in)
        g1.setColorAt(1.0, c_out)
        p.setBrush(QBrush(g1))
        p.drawEllipse(center, r, r)

        # Layer 2 — anillo violet, centro desplazado 8 % hacia arriba (efecto llama)
        violet = QColor(v3c("violet", self._modo))
        off = QPointF(cx, cy - r * 0.08)
        g2 = QRadialGradient(off, r)
        v0 = QColor(violet.red(), violet.green(), violet.blue(), 0)
        v1 = QColor(violet)
        v1.setAlpha(int(l2 * mult))
        g2.setColorAt(0.0, v0)
        g2.setColorAt(0.5, v1)
        g2.setColorAt(1.0, v0)
        p.setBrush(QBrush(g2))
        p.drawEllipse(center, r, r)

        # Layer 3 — halo primary (llega hasta el borde del canvas)
        primary = QColor(v3c("primary", self._modo))
        halo_r = min(r * 1.15, cx)
        g3 = QRadialGradient(center, halo_r)
        p0 = QColor(primary.red(), primary.green(), primary.blue(), 0)
        p1 = QColor(primary)
        p1.setAlpha(int(l3 * mult))
        g3.setColorAt(0.0, p0)
        g3.setColorAt(0.72, p1)
        g3.setColorAt(1.0, p0)
        p.setBrush(QBrush(g3))
        p.drawEllipse(center, halo_r, halo_r)

    def _draw_organic_border(self, p: QPainter, cx: float, cy: float, r: float) -> None:
        """Borde con ondulación senoidal: 3 lóbulos que rotan continuamente."""
        border_color = v3c("border", self._modo)
        pen = QPen(border_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        if self._undulation_amp < 0.3:
            p.drawEllipse(QPointF(cx, cy), r, r)
            return

        n = 120
        path = QPainterPath()
        for i in range(n + 1):
            a = 2.0 * math.pi * i / n
            cr = r + self._undulation_amp * math.sin(
                _UNDULATION_LOBES * a + self._undulation_phase
            )
            x = cx + cr * math.cos(a)
            y = cy - cr * math.sin(a)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        p.drawPath(path)

    def _draw_particles(self, p: QPainter, cx: float, cy: float, r: float) -> None:
        """8 puntos que orbitan el borde del círculo, colores teal/violet alternados."""
        teal = QColor(v3c("teal", self._modo))
        violet = QColor(v3c("violet", self._modo))
        orbit_r = r + _PARTICLE_ORBIT_OFF
        p.setPen(Qt.PenStyle.NoPen)
        step = 360.0 / _N_PARTICLES
        # Más opacos en dark (alto contraste sobre bg oscuro),
        # más sutiles en light (bg claro hace que 160 parezca demasiado llamativo)
        particle_alpha = 160 if "dark" in self._modo else 115
        for i in range(_N_PARTICLES):
            a = math.radians(self._orbit_angle + i * step)
            px = cx + orbit_r * math.cos(a)
            py = cy - orbit_r * math.sin(a)
            color = QColor(teal if i % 2 == 0 else violet)
            color.setAlpha(particle_alpha)
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(px, py), _PARTICLE_SIZE, _PARTICLE_SIZE)

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
        vl.setContentsMargins(
            V3_SP["sm"], V3_SP["xs"], V3_SP["sm"], V3_SP["xs"]
        )  # compact R5A: era md/md
        vl.setSpacing(2)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl = QLabel(self._label_text)
        self._lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
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
        color_main = (
            v3c("teal", self._modo).name() if self._active else v3c("text2", self._modo).name()
        )
        color_sec = (
            v3c("teal", self._modo).name()
            if self._active
            else v3c("ink_secondary", self._modo).name()
        )
        self._lbl.setStyleSheet(f"color: {color_main}; background: transparent;")
        self._secs_lbl.setStyleSheet(f"color: {color_sec}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_step_styles()


# ── _HistorialCard ──────────────────────────────────────────────────────────


class _HistorialMiniCard(NMCard):
    """Card mini de sesión pasada: fecha + duración + ring de ciclos."""

    def __init__(
        self, fecha: str, hora: str, duracion: float, ciclos: int, modo: str = None, parent=None
    ):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._fecha = fecha
        self._hora = hora
        self._duracion = duracion
        self._ciclos = ciclos
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(
            V3_SP["sm"], V3_SP["xs"], V3_SP["sm"], V3_SP["xs"]
        )  # compact R5A: era md/md
        lay.setSpacing(V3_SP["sm"])

        # Ring chico con % ciclos vs target (15 ciclos = full). Sin label "NN%":
        # a 32px el texto no entra y se montaba sobre el arco (doc del propio
        # NMModuleRing); el progreso lo comunica el arco y los ciclos el texto.
        ring_pct = min(self._ciclos / 15.0, 1.0)
        self._ring = NMModuleRing(
            size=32, pct=ring_pct, modo=self._modo, show_label=False
        )
        lay.addWidget(self._ring)

        col = QVBoxLayout()
        col.setSpacing(0)
        self._date_lbl = QLabel(self._format_date())
        self._date_lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
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
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._dur_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )

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

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        outer.addWidget(body)

        # QHBoxLayout as top-level body layout: left is main content, right is collapsible history drawer
        main_page_layout = QHBoxLayout(body)
        main_page_layout.setContentsMargins(0, 0, 0, 0)
        main_page_layout.setSpacing(0)

        main_panel = QWidget()
        main_panel.setStyleSheet("background: transparent;")
        main_page_layout.addWidget(main_panel, stretch=1)

        lay = QVBoxLayout(main_panel)
        # Aire inferior md: con sm las stat cards (PATRÓN/CRONO/BPM) quedaban
        # pegadas al borde de la ventana ("no respira").
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        # Eyebrow del módulo vive en la titlebar (BL-07): se conserva el label
        # oculto por compatibilidad con el resto del módulo.
        self._range_lbl = QLabel("Respiración 4-7-8")
        self._range_lbl.setFont(eyebrow_font())
        self._range_lbl.hide()

        # 1+2. Bio-guía principal en card. Los presets 3/5/10 min viven DENTRO
        # de la card (arriba a la derecha, posición conservada) en vez de flotar
        # fuera; la card se expande para ocupar el espacio disponible.
        practice_card = NMCard(modo=self._modo, clickable=False, glow=False)
        practice_lay = QVBoxLayout(practice_card)
        practice_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        practice_lay.setSpacing(V3_SP["sm"])

        header_l = QHBoxLayout()
        header_l.setSpacing(V3_SP["sm"])
        self._bio_guide_lbl = QLabel(t("text.module.respiracion.guide_title", "Bio-guía"))
        self._bio_guide_lbl.setFont(eyebrow_font())
        header_l.addWidget(self._bio_guide_lbl)
        header_l.addStretch()

        # Pills de preset integradas en el header de la card.
        self._pill_btns: list[tuple[NMButtonOutline, int]] = []
        for label, mins in PRESETS:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=False, size="sm")
            btn.setFixedSize(76, 28)
            btn.clicked.connect(lambda _, m=mins: self._select_preset(m))
            header_l.addWidget(btn)
            self._pill_btns.append((btn, mins))

        practice_lay.addLayout(header_l)
        self._highlight_preset(5)

        circle_container = QVBoxLayout()
        circle_container.setSpacing(V3_SP["md"])
        # Grupo anclado ARRIBA con respiración 1:2 (no centrado): el orb
        # quedaba muy abajo en la card (feedback owner v1.0).
        circle_container.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        circle_container.addStretch(1)

        self._circle = _BreathCircle(self._content, self._modo)
        circle_container.addWidget(self._circle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Phase Chips (using NMChip directly)
        self._chips_layout = QHBoxLayout()
        self._chips_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chips_layout.setSpacing(6)

        self._chip_inhala = NMChip(
            "Inhala 4s", variant="default", size="sm", modo=self._modo, parent=self
        )
        self._chip_manten = NMChip(
            "Mantiene 7s", variant="default", size="sm", modo=self._modo, parent=self
        )
        self._chip_exhala = NMChip(
            "Exhala 8s", variant="default", size="sm", modo=self._modo, parent=self
        )

        self._chips_layout.addWidget(self._chip_inhala)
        self._chips_layout.addWidget(self._chip_manten)
        self._chips_layout.addWidget(self._chip_exhala)
        circle_container.addLayout(self._chips_layout)

        # Controles Play/Pause/Stop (using NMButton)
        ctrl_row = QHBoxLayout()
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_row.setSpacing(V3_SP["md"])

        self._btn_reset = NMButton(
            "Reiniciar", variant="secondary", size="md", parent=self, width=100
        )
        self._btn_reset.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_reset)

        # P2.E: botón Iniciar/Pausar a escala del producto (md, no lg) — antes se
        # veía gigante y rompía la jerarquía visual junto al orb.
        self._btn_play = NMButton("Iniciar", variant="gradient", size="md", parent=self, width=120)
        self._btn_play.clicked.connect(self._toggle_play_pause)
        ctrl_row.addWidget(self._btn_play)

        self._btn_stop = NMButton("Detener", variant="secondary", size="md", parent=self, width=100)
        self._btn_stop.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_stop)

        circle_container.addLayout(ctrl_row)
        circle_container.addStretch(2)
        practice_lay.addLayout(circle_container, stretch=1)
        self._practice_card = practice_card
        # stretch=1: la card del respirador ocupa el espacio disponible entre el
        # tope y las stat cards (PATRÓN/CRONO/BPM) inferiores.
        lay.addWidget(practice_card, stretch=1)

        # 3. 4 stats cards at bottom in a horizontal layout
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(V3_SP["sm"])

        try:
            from shared.theme_qt import v3_font as _v3_font

            val_font = _v3_font(20, weight=TYPOGRAPHY["weight_semibold"], serif=True)
        except ImportError:
            val_font = qfont("size_large", bold=True)

        self._pattern_card = NMCard(modo=self._modo, clickable=False)
        self._pattern_card.setFixedHeight(72)
        pat_lay = QVBoxLayout(self._pattern_card)
        pat_lay.setContentsMargins(14, 12, 14, 12)
        pat_lay.setSpacing(2)
        self._pattern_eyebrow = QLabel("Patrón")
        self._pattern_eyebrow.setFont(eyebrow_font())
        self._pattern_title = QLabel("4-7-8")
        self._pattern_title.setFont(val_font)
        pat_lay.addWidget(self._pattern_eyebrow)
        pat_lay.addWidget(self._pattern_title)
        stats_layout.addWidget(self._pattern_card, stretch=1)

        self._chrono_card = NMCard(modo=self._modo, clickable=False)
        self._chrono_card.setFixedHeight(72)
        chr_lay = QVBoxLayout(self._chrono_card)
        chr_lay.setContentsMargins(14, 12, 14, 12)
        chr_lay.setSpacing(2)
        self._chrono_eyebrow = QLabel("Crono")
        self._chrono_eyebrow.setFont(eyebrow_font())
        self._session_lbl = QLabel("00:00")
        self._session_lbl.setFont(val_font)
        chr_lay.addWidget(self._chrono_eyebrow)
        chr_lay.addWidget(self._session_lbl)
        stats_layout.addWidget(self._chrono_card, stretch=1)

        self._bpm_card = NMCard(modo=self._modo, clickable=False)
        self._bpm_card.setFixedHeight(72)
        bpm_lay = QVBoxLayout(self._bpm_card)
        bpm_lay.setContentsMargins(14, 12, 14, 12)
        bpm_lay.setSpacing(2)
        self._bpm_eyebrow = QLabel("BPM")
        self._bpm_eyebrow.setFont(eyebrow_font())
        self._bpm_value_lbl = QLabel("—")
        self._bpm_value_lbl.setFont(val_font)
        bpm_lay.addWidget(self._bpm_eyebrow)
        bpm_lay.addWidget(self._bpm_value_lbl)
        stats_layout.addWidget(self._bpm_card, stretch=1)
        # Keep NMCalmBadge dormant for theme-compat; hidden, not shown.
        self._calm_badge = NMCalmBadge(bpm=60, modo=self._modo, parent=self._bpm_card)
        self._calm_badge.setVisible(False)

        # P2.E: card "Calma" removida — duplicaba info de BPM/calma que ya muestra
        # el NMCalmBadge. Mantengo compat con el resto del código (no-op silencioso).
        self._calm_card: NMCard | None = None
        self._calm_eyebrow = QLabel("Calma")
        self._calm_eyebrow.setFont(eyebrow_font())
        self._calm_eyebrow.hide()
        self._calm_pct_lbl = QLabel("—")
        self._calm_pct_lbl.setFont(val_font)
        self._calm_pct_lbl.hide()
        self._calm_bar = NMProgressBar(height=4, modo=self._modo, parent=self)
        self._calm_bar.set_progress(0.45)
        self._calm_bar.setVisible(False)

        lay.addLayout(stats_layout)

        # Dummy hidden label to preserve compatibility with existing status update methods
        self._chrono_meta = QLabel()

        # Card de historial ESTÁTICA (decisión owner #3): reemplaza el drawer
        # colapsable feo. Siempre visible a la derecha; aprovecha el espacio libre
        # del módulo. El scroll interno acota la lista para que no rompa el layout.
        # Bordes rectos (feedback owner v1.0): el panel lateral redondeado
        # leía desprolijo contra el borde de la ventana.
        self._history_card = NMCard(modo=self._modo, clickable=False, glow=False, radius=0)
        self._history_card.setFixedWidth(236)
        _hist_outer = QVBoxLayout(self._history_card)
        _hist_outer.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        _hist_outer.setSpacing(V3_SP["sm"])
        self._hist_eyebrow = QLabel("Historial reciente")
        self._hist_eyebrow.setFont(eyebrow_font())
        _hist_outer.addWidget(self._hist_eyebrow)
        main_page_layout.addSpacing(V3_SP["md"])
        main_page_layout.addWidget(self._history_card)

        self._hist_scroll = QScrollArea()
        self._hist_scroll.setWidgetResizable(True)
        self._hist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._hist_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._hist_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._hist_container = QWidget()
        self._hist_container.setStyleSheet("background: transparent;")
        self._hist_row = QVBoxLayout(self._hist_container)
        self._hist_row.setSpacing(V3_SP["sm"])
        self._hist_row.setContentsMargins(0, 0, 0, 0)
        self._hist_scroll.setWidget(self._hist_container)
        _hist_outer.addWidget(self._hist_scroll, stretch=1)

        self._cargar_historial()
        self._apply_text_styles()

        # Ring pulse — overlay de finalización de sesión
        self._ring_pulse = NMRingPulse(self._content, modo=self._modo)

    def _relayout_main_grid(self):
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _toggle_history(self):
        # No-op: el historial ahora es una card estática siempre visible
        # (decisión owner #3). Se conserva el método por compatibilidad.
        return

    def _apply_text_styles(self):
        c = v3c("ink_secondary", self._modo).name()
        for lbl in (
            self._range_lbl,
            self._chrono_eyebrow,
            self._bpm_eyebrow,
            self._calm_eyebrow,
            self._pattern_eyebrow,
            self._bio_guide_lbl,
        ):
            if hasattr(self, lbl.objectName()) or True:
                lbl.setStyleSheet(f"color: {c}; background: transparent;")
        self._pattern_title.setStyleSheet(
            f"color: {v3c('ink_primary', self._modo).name()}; background: transparent;"
        )
        self._session_lbl.setStyleSheet(
            f"color: {v3c('ink_primary', self._modo).name()}; background: transparent;"
        )
        if hasattr(self, "_hist_eyebrow"):
            self._hist_eyebrow.setStyleSheet(
                f"color: {c}; background: transparent;"
            )
        if hasattr(self, "_hist_scroll"):
            self._hist_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

    # ── theme ────────────────────────────────────────────────────────────────

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_circle"):
            self._circle._apply_theme(self._modo)
        if hasattr(self, "_chip_inhala"):
            self._chip_inhala._modo = self._modo
            self._chip_inhala._apply_style()
        if hasattr(self, "_chip_manten"):
            self._chip_manten._modo = self._modo
            self._chip_manten._apply_style()
        if hasattr(self, "_chip_exhala"):
            self._chip_exhala._modo = self._modo
            self._chip_exhala._apply_style()
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
        """Toggle único entre play / pause / resume."""
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
        self._btn_play.setText("Pausar")
        self._chrono_meta.setText("En curso")
        self._tick()

    def _pause(self):
        if not self._running:
            return
        if self._paused:
            self._paused = False
            self._btn_play.setText("Pausar")
            self._chrono_meta.setText("En curso")
            self._circle._start_rendering()
            self._tick()
        else:
            self._paused = True
            self._btn_play.setText("Reanudar")
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
        self._btn_play.setText("Iniciar")
        self._circle.reset_idle()
        self._session_lbl.setText("00:00")
        self._chrono_meta.setText("Listo para comenzar")
        if hasattr(self, "_bpm_value_lbl"):
            self._bpm_value_lbl.setText("—")
        if hasattr(self, "_calm_pct_lbl"):
            self._calm_pct_lbl.setText("—")
        self._update_phase_chips(None)
        self._cargar_historial()

    def _update_phase_chips(self, phase_idx: int | None):
        if not hasattr(self, "_chip_inhala"):
            return
        self._chip_inhala._variant = "default"
        self._chip_manten._variant = "default"
        self._chip_exhala._variant = "default"

        if phase_idx == 0:
            self._chip_inhala._variant = "tint"
        elif phase_idx == 1:
            self._chip_manten._variant = "info"
        elif phase_idx == 2:
            self._chip_exhala._variant = "amber"

        self._chip_inhala._apply_style()
        self._chip_manten._apply_style()
        self._chip_exhala._apply_style()

    # ── tick (lógica preservada con actualizaciones) ──────────────────────────

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
                self._update_phase_chips(self._phase_idx)

            secs_left = max(0, phase_dur - int(self._phase_ms / 1000))
            session_progress = self._elapsed_ms / total_ms
            self._circle.update_data(
                phase_progress=phase_progress,
                session_progress=session_progress,
                center_text=str(secs_left),
                phase_text=phase_name,
                phase_idx=self._phase_idx,
            )

            if hasattr(self, "_calm_bar"):
                calm_target = 0.45 + session_progress * 0.5
                self._calm_bar.set_progress(min(calm_target, 0.95))
            if hasattr(self, "_calm_pct_lbl"):
                calm_target = 0.45 + session_progress * 0.5
                self._calm_pct_lbl.setText(f"{int(min(calm_target, 0.95) * 100)}%")
            if hasattr(self, "_bpm_value_lbl"):
                # Simular arritmia sinusal respiratoria (RSA) de forma orgánica:
                # El ritmo sube al inhalar y baja al exhalar/mantener, relajándose con el tiempo.
                import random
                base = 68.0 - (session_progress * 6.0)
                phase_progress_f = self._phase_ms / (phase_dur * 1000.0)
                if phase_name == "Inhala":
                    val = (base - 3.0) + (11.0 * phase_progress_f)
                elif phase_name == "Mantiene":
                    val = (base + 8.0) - (5.0 * phase_progress_f)
                else:  # "Exhala"
                    val = (base + 3.0) - (11.0 * phase_progress_f)
                val += random.uniform(-0.6, 0.6)
                self._bpm_value_lbl.setText(str(int(round(val))))

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
            _log.error(redact(f"Error in _tick: {e}"))
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
        if hasattr(self, "_ring_pulse"):
            self._ring_pulse.launch()
        self._circle.reset_idle()
        self._update_phase_chips(None)
        self._session_lbl.setText("00:00")
        self._chrono_meta.setText(f"Completo · {self._ciclos} ciclos")
        self._btn_play.setText("Iniciar")
        self._cargar_historial()

    # ── DB (preservado exacto) ───────────────────────────────────────────────

    def _save_session(self):
        try:
            with conexion() as conn:
                conn.execute(
                    "INSERT INTO respiracion "
                    "(fecha, hora, tecnica, duracion_minutos, ciclos) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        fecha_hoy(),
                        hora_actual(),
                        TECNICA,
                        round(self._elapsed_ms / 60000, 1),
                        self._ciclos,
                    ),
                )
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
                "ORDER BY fecha DESC, hora DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            out = []
            for r in rows:
                if hasattr(r, "keys"):
                    out.append(
                        (
                            r["fecha"],
                            r["hora"],
                            float(r["duracion_minutos"] or 0),
                            int(r["ciclos"] or 0),
                        )
                    )
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
        sessions = self._load_recent_sessions(10)
        if not sessions:
            empty = QLabel(t("text.module.respiracion.empty_state", "Sin sesiones."))
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
            self._hist_row.addWidget(empty)
            self._hist_row.addStretch()
            return
        for fecha, hora, dur, ciclos in sessions:
            card = _HistorialMiniCard(fecha, hora, dur, ciclos, modo=self._modo)
            self._hist_row.addWidget(card)
        self._hist_row.addStretch()

    # ── hooks NMModule ───────────────────────────────────────────────────────

    def on_enter(self):
        pass

    def on_leave(self):
        self._stop()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM respiracion WHERE fecha=?", (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} sesión{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
