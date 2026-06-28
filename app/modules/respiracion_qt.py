"""
app/modules/respiracion_qt.py — Módulo Respiración 4-7-8 v3 (PyQt6)

Estructura actual (Suite > Respiración):

  Practice card  BIG breath circle + phase chips + controles
  Stats row      Patrón / Crono / Ciclos
  Historial      Card lateral con sesiones recientes

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
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)

try:
    from shared.components import (
        NMModule,
        NMButtonOutline,
        NMCard,
        NMPlayButton,
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
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButtonOutline,
        NMCard,
        NMPlayButton,
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

from shared.remote_config import t


# ── Constantes de negocio ─────────────────────────────────────────────────────

TECNICA = "4-7-8"
FASES = [
    ("Inhala", 4),
    ("Mantiene", 7),
    ("Exhala", 8),
]
# Etiquetas de fase mostradas en el ring (mockup `.bigring .ph`: "Inhalá" /
# "Mantené" / "Exhalá", acentuadas). Las claves internas (sin tilde) se conservan
# para lógica/DB; el display se acentúa para fidelidad con el mockup.
FASE_DISPLAY = {
    "Inhala": "Inhalá",
    "Mantiene": "Mantené",
    "Exhala": "Exhalá",
}
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
# Radios subidos (propagación visual): el orb en reposo (78 → 92) llenaba poco
# su canvas de 248px y se leía chico, flotando con ~46px de padding transparente
# que inflaba el vacío percibido por encima. 92/116 lo hacen presente y reducen
# el hueco sin tocar el layout ni recortar el borde orgánico (max+ondas < 124).
_R_MIN = 92   # radio en reposo / exhala final
_R_MAX = 116  # radio máximo en inhala

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
        # Sesión activa = partículas en órbita + render timer. Se separa de la
        # presencia de texto para poder mostrar el idle estático del mockup
        # (num "4" + "Inhalá") sin disparar la animación.
        self._session_active = False

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
        self._session_active = True
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
        self._session_active = False
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

    def set_idle_preview(self, center_text: str, phase_text: str) -> None:
        """Idle estático del mockup: muestra el primer paso (num + fase) dentro del
        ring SIN animar (sin partículas ni render timer).

        Delega en ``reset_idle`` para detener cualquier animación en curso (radio,
        glow, undulación) y dejar el círculo en reposo; luego fija el texto del
        primer paso. Así parar una sesión activa detiene la animación igual que antes.
        """
        self.reset_idle()
        self._center_text = center_text
        self._phase_text = phase_text
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
        if self._session_active:
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
        active = self._session_active

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
            # Mockup neuromood-mockup.html l.213: .bigring .num usa font-size:52px
            # weight:500. El real estaba en 44px — se veía más chico y ligero
            # que el mockup canónico.
            p.setFont(_v3_font(52, weight=TYPOGRAPHY["weight_medium"], serif=True))
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
        # 2026-06-24 iter 70: alpha 115→55 (light) / 160→85 (dark) — partículas
        # casi invisibles para acercarse al mockup "En curso" (sin partículas
        # visibles). Mantiene feedback animado mínimo.
        particle_alpha = 85 if "dark" in self._modo else 55
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
        # Márgenes del row a nivel body: el historial (ahora card redondeada)
        # necesita aire arriba/derecha/abajo para no pegarse al borde de la
        # ventana. El top/bottom se mueve acá desde `lay` para no duplicarlo en
        # la columna izquierda (queda visualmente idéntica).
        main_page_layout.setContentsMargins(0, V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        main_page_layout.setSpacing(0)

        main_panel = QWidget()
        main_panel.setStyleSheet("background: transparent;")
        main_page_layout.addWidget(main_panel, stretch=1)

        lay = QVBoxLayout(main_panel)
        # Top/bottom ahora los aporta main_page_layout (aire compartido con el
        # historial); acá solo el inset horizontal de la columna izquierda.
        lay.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], 0)
        lay.setSpacing(V3_SP["sm"])

        # 1+2. Área de práctica — sin card wrapper (canónico: contenido flotante sobre fondo).
        practice_card = QFrame()
        practice_card.setStyleSheet("background: transparent; border: none;")
        practice_lay = QVBoxLayout(practice_card)
        practice_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        practice_lay.setSpacing(V3_SP["sm"])

        header_l = QHBoxLayout()
        header_l.setSpacing(V3_SP["sm"])
        header_l.addStretch()

        # Pills de preset integradas en el header de la card (centradas, mockup).
        self._pill_btns: list[tuple[NMButtonOutline, int]] = []
        for label, mins in PRESETS:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=False, size="sm")
            btn.setFixedSize(76, 28)
            btn.clicked.connect(lambda _, m=mins: self._select_preset(m))
            header_l.addWidget(btn)
            self._pill_btns.append((btn, mins))
        header_l.addStretch()

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
            t("text.module.respiracion.phase_inhale", "Inhalá 4s"),
            variant="default", size="sm", modo=self._modo, parent=self
        )
        self._chip_manten = NMChip(
            t("text.module.respiracion.phase_hold", "Mantené 7s"),
            variant="default", size="sm", modo=self._modo, parent=self
        )
        self._chip_exhala = NMChip(
            t("text.module.respiracion.phase_exhale", "Exhalá 8s"),
            variant="default", size="sm", modo=self._modo, parent=self
        )

        self._chips_layout.addWidget(self._chip_inhala)
        self._chips_layout.addWidget(self._chip_manten)
        self._chips_layout.addWidget(self._chip_exhala)
        circle_container.addLayout(self._chips_layout)

        # Controles circulares del mockup: reset/play/stop sin texto visible.
        ctrl_row = QHBoxLayout()
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_row.setSpacing(V3_SP["md"])

        self._btn_reset = NMPlayButton(icon_name="refresh", size="md", modo=self._modo, parent=self)
        self._btn_reset.setToolTip(t("text.module.respiracion.reset_btn", "Reiniciar"))
        self._btn_reset.setAccessibleName(t("text.module.respiracion.reset_btn", "Reiniciar"))
        self._btn_reset.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_reset)

        self._btn_play = NMPlayButton(icon_name="play", size="lg", modo=self._modo, parent=self)
        self._set_play_control("play", t("text.module.respiracion.start_btn", "Iniciar"))
        self._btn_play.clicked.connect(self._toggle_play_pause)
        ctrl_row.addWidget(self._btn_play)

        self._btn_stop = NMPlayButton(icon_name="stop", size="md", modo=self._modo, parent=self)
        self._btn_stop.setToolTip(t("text.module.respiracion.stop_btn", "Detener"))
        self._btn_stop.setAccessibleName(t("text.module.respiracion.stop_btn", "Detener"))
        self._btn_stop.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_stop)

        circle_container.addLayout(ctrl_row)
        # Antes 1:2 (anclado arriba) dejaba un hueco asimétrico grande debajo de
        # los controles. Con el orb agrandado, centrar el grupo (1:1) reparte el
        # aire de forma pareja y elimina el vacío excesivo inferior.
        circle_container.addStretch(1)
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
        self._pattern_eyebrow = QLabel(t("text.module.respiracion.pattern_label", "Patrón"))
        self._pattern_eyebrow.setFont(eyebrow_font())
        self._pattern_title = QLabel("4·7·8")
        self._pattern_title.setFont(val_font)
        pat_lay.addWidget(self._pattern_eyebrow)
        pat_lay.addWidget(self._pattern_title)
        stats_layout.addWidget(self._pattern_card, stretch=1)

        self._chrono_card = NMCard(modo=self._modo, clickable=False)
        self._chrono_card.setFixedHeight(72)
        chr_lay = QVBoxLayout(self._chrono_card)
        chr_lay.setContentsMargins(14, 12, 14, 12)
        chr_lay.setSpacing(2)
        self._chrono_eyebrow = QLabel(t("text.module.respiracion.chrono_label", "Crono"))
        self._chrono_eyebrow.setFont(eyebrow_font())
        self._session_lbl = QLabel("00:00")
        self._session_lbl.setFont(val_font)
        chr_lay.addWidget(self._chrono_eyebrow)
        chr_lay.addWidget(self._session_lbl)
        stats_layout.addWidget(self._chrono_card, stretch=1)

        # Tercera card: "Ciclos" (conteo real de ciclos 4-7-8 completados).
        # Antes era "BPM" mostrando un pulso cardíaco SIMULADO (RSA con ruido
        # aleatorio): parecía una lectura biométrica real sin serlo (la app no
        # mide pulso). Fase 9 lo reemplaza por una métrica honesta y verificable.
        self._ciclos_card = NMCard(modo=self._modo, clickable=False)
        self._ciclos_card.setFixedHeight(72)
        ciclos_lay = QVBoxLayout(self._ciclos_card)
        ciclos_lay.setContentsMargins(14, 12, 14, 12)
        ciclos_lay.setSpacing(2)
        self._ciclos_eyebrow = QLabel(t("text.module.respiracion.cycles_label", "Ciclos"))
        self._ciclos_eyebrow.setFont(eyebrow_font())
        self._ciclos_value_lbl = QLabel("0")
        self._ciclos_value_lbl.setFont(val_font)
        ciclos_lay.addWidget(self._ciclos_eyebrow)
        ciclos_lay.addWidget(self._ciclos_value_lbl)
        stats_layout.addWidget(self._ciclos_card, stretch=1)

        lay.addLayout(stats_layout)

        self._apply_text_styles()

        # Ring pulse — overlay de finalización de sesión
        self._ring_pulse = NMRingPulse(self._content, modo=self._modo)

        # Estado de reposo del mockup: el ring abre mostrando el primer paso
        # ("4" / "Inhalá") en vez de un círculo vacío.
        self._show_idle_preview()

    def _show_idle_preview(self) -> None:
        """Reposo del mockup: el ring muestra el primer paso (num + fase) estático."""
        first_name, first_dur = FASES[0]
        self._circle.set_idle_preview(
            str(first_dur), FASE_DISPLAY.get(first_name, first_name)
        )
        self._update_phase_chips(None)

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
            self._chrono_eyebrow,
            self._ciclos_eyebrow,
            self._pattern_eyebrow,
        ):
            lbl.setStyleSheet(f"color: {c}; background: transparent;")
        self._pattern_title.setStyleSheet(
            f"color: {v3c('ink_primary', self._modo).name()}; background: transparent;"
        )
        self._session_lbl.setStyleSheet(
            f"color: {v3c('ink_primary', self._modo).name()}; background: transparent;"
        )

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

    def _set_play_control(self, icon_name: str, label: str) -> None:
        self._btn_play.set_icon(icon_name)
        self._btn_play.setToolTip(label)
        self._btn_play.setAccessibleName(label)

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
        self._set_play_control("pause", t("text.module.respiracion.pause_btn", "Pausar"))
        self._tick()

    def _pause(self):
        if not self._running:
            return
        if self._paused:
            self._paused = False
            self._set_play_control("pause", t("text.module.respiracion.pause_btn", "Pausar"))
            self._circle._start_rendering()
            self._tick()
        else:
            self._paused = True
            self._set_play_control("play", t("text.module.respiracion.resume_btn", "Reanudar"))
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
        self._set_play_control("play", t("text.module.respiracion.start_btn", "Iniciar"))
        self._show_idle_preview()
        self._session_lbl.setText("00:00")
        if hasattr(self, "_ciclos_value_lbl"):
            self._ciclos_value_lbl.setText("0")

    def _update_phase_chips(self, phase_idx: int | None):
        if not hasattr(self, "_chip_inhala"):
            return
        # Cada fase con su color base (verde / amarillo / naranja), visible también
        # en reposo como el mockup canónico. El feedback de la fase activa lo da el
        # círculo central animado; antes los chips quedaban gris "default" en reposo.
        self._chip_inhala._variant = "success"
        self._chip_manten._variant = "warning"
        self._chip_exhala._variant = "danger"

        if phase_idx == 0:
            self._chip_inhala._variant = "solid"
        elif phase_idx == 1:
            self._chip_manten._variant = "solid"
        elif phase_idx == 2:
            self._chip_exhala._variant = "solid"

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
                phase_text=FASE_DISPLAY.get(phase_name, phase_name),
                phase_idx=self._phase_idx,
            )

            if hasattr(self, "_ciclos_value_lbl"):
                # Conteo real de ciclos 4-7-8 completados en la sesión (no una
                # métrica biométrica simulada): honesto, determinista y verificable.
                self._ciclos_value_lbl.setText(str(self._ciclos))

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
        self._show_idle_preview()
        self._session_lbl.setText("00:00")
        self._set_play_control("play", t("text.module.respiracion.start_btn", "Iniciar"))

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
