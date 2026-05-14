"""
app/modules/respiracion_qt.py — Módulo Respiración (PyQt6)

LÓGICA DE NEGOCIO PRESERVADA EXACTA de respiracion.py:
  TECNICA, FASES, PRESETS, CICLO_TOTAL
  _tick() con intervalo 100ms, _save_session(), get_card_status()
  _start(), _pause(), _stop(), _finish()

NUEVAS CAPACIDADES UI:
  Círculo que respira físicamente:
    - QPropertyAnimation sobre circle_radius (95→130→95) en sync con fases
    - Easing InOutSine igual que la respiración natural
  Glow pulsante:
    - QPropertyAnimation sobre glow_alpha (40→120→40) en sync
    - Pintado con QRadialGradient
  Arco gradiente:
    - QPainter + QConicalGradient teal→violet
    - Arco exterior delgado (2px) para progreso total de sesión
  Texto central animado:
    - QGraphicsOpacityEffect fade 300ms al cambiar de fase
  60fps via QTimer(16ms)
"""

import os
import sys
import math
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    pyqtProperty, QAbstractAnimation, QSequentialAnimationGroup,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPainterPath,
    QConicalGradient, QRadialGradient, QLinearGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QGraphicsOpacityEffect, QFrame,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, ThemeManager,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        radial_glow, radial_glow_double, conical_arc_gradient, get_gradient, gradient_colors,
        RADIUS_CARD, RADIUS_PILL, PAD_CONTAINER, GAP_ELEMENTS,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import NMModule, NMButton, NMButtonOutline, ThemeManager
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        radial_glow, radial_glow_double, conical_arc_gradient, get_gradient, gradient_colors,
        RADIUS_CARD, RADIUS_PILL, PAD_CONTAINER, GAP_ELEMENTS,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual

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

# Radios del círculo animado
_R_MIN   = 88    # radio en reposo / exhala final
_R_MAX   = 128   # radio máximo en inhala
_R_TRACK = 140   # radio del track ring (fijo)
_CANVAS  = 300   # tamaño del widget circular


def _rich_color_at(modo: str, t: float) -> str:
    palette = gradient_colors(modo)
    if len(palette) < 3:
        return interpolate_color(palette[0], palette[-1], t)
    if t <= 0.45:
        return interpolate_color(palette[0], palette[1], t / 0.45)
    return interpolate_color(palette[1], palette[2], (t - 0.45) / 0.55)


# ── CircleWidget — el corazón visual ─────────────────────────────────────────

class _BreathCircle(QWidget):
    """
    Círculo de respiración con animaciones Qt nativas.

    Propiedades animables (pyqtProperty):
      circle_radius: float — radio del círculo relleno
      glow_alpha:    int   — intensidad del glow radial (0–255)
      text_opacity:  float — opacidad del texto central (0.0–1.0)

    Datos que se actualizan en cada tick:
      phase_progress: float 0–1 (progreso dentro de la fase actual)
      session_progress: float 0–1 (progreso total de la sesión)
      center_text: str — segundos restantes
      phase_text: str — nombre de la fase
      phase_color: str — color hex de la fase
    """

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setFixedSize(_CANVAS, _CANVAS)

        # Estado visual
        self._circle_radius = float(_R_MIN)
        self._glow_alpha = 40
        self._text_opacity = 1.0
        self._phase_progress = 0.0
        self._session_progress = 0.0
        self._center_text = ""
        self._phase_text = ""
        self._phase_color = C("accent", self._modo)

        # Animaciones de entrada (se crean una vez, se reinician en cada fase)
        self._anim_radius: QPropertyAnimation | None = None
        self._anim_glow: QPropertyAnimation | None = None
        self._anim_text_fade: QPropertyAnimation | None = None

        # Timer de 60fps para redibujado
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(self.update)
        self._render_timer.start(16)

        self.setStyleSheet("background: transparent;")
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

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

    # ── API para el módulo ────────────────────────────────────────────────────

    def update_data(self, phase_progress: float, session_progress: float,
                    center_text: str, phase_text: str, phase_idx: int):
        """Actualizar datos del frame actual. Llamar en cada tick."""
        self._phase_progress = phase_progress
        self._session_progress = session_progress
        self._center_text = center_text
        self._phase_text = phase_text
        if phase_idx == 0:
            self._phase_color = C("teal", self._modo)
        elif phase_idx == 2:
            self._phase_color = C("violet", self._modo)
        else:
            self._phase_color = C("accent", self._modo)

    def animate_phase(self, phase_idx: int, phase_dur_s: int, expanding: bool):
        """
        Iniciar animaciones de la fase:
          Inhala (expanding=True):  radius MIN→MAX, glow 40→120
          Mantén (expanding=None):  radio fijo, solo glow pulsante
          Exhala (expanding=False): radius MAX→MIN, glow 120→40
        """
        self._render_timer.start(16)
        dur = phase_dur_s * 1000

        # Animar radio
        if self._anim_radius:
            self._anim_radius.stop()
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
            # Mantén: radio fijo, sin animación de tamaño
            self._circle_radius = float(_R_MAX)
        if expanding is not None:
            self._anim_radius.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        # Animar glow
        if self._anim_glow:
            self._anim_glow.stop()
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
            # Mantén: glow constante alto
            self._glow_alpha = 100
        if expanding is not None:
            self._anim_glow.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def animate_text_change(self):
        """Fade out→in del texto al cambiar de fase (300ms)."""
        if self._anim_text_fade:
            self._anim_text_fade.stop()
        self._anim_text_fade = QPropertyAnimation(self, b"text_opacity", self)
        self._anim_text_fade.setDuration(300)
        # out → in
        self._anim_text_fade.setKeyValueAt(0.0, 1.0)
        self._anim_text_fade.setKeyValueAt(0.4, 0.0)
        self._anim_text_fade.setKeyValueAt(1.0, 1.0)
        self._anim_text_fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim_text_fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def reset_idle(self):
        if self._anim_radius:
            self._anim_radius.stop()
        if self._anim_glow:
            self._anim_glow.stop()
        self._render_timer.stop()
        self._circle_radius = float(_R_MIN)
        self._glow_alpha = 40
        self._text_opacity = 1.0
        self._phase_progress = 0.0
        self._session_progress = 0.0
        self._center_text = ""
        self._phase_text = ""
        self.update()

    # ── paintEvent ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.save()

        c = colors(self._modo)
        cx = cy = _CANVAS / 2

        # ── 1. Glow radial (usando radial_glow_double premium) ─────────────────
        glow_r = self._circle_radius + 32
        glow_center = QPointF(cx, cy)
        glow_grad = radial_glow_double(glow_center, glow_r, self._phase_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow_grad))
        p.drawEllipse(glow_center, glow_r, glow_r)

        # ── 2. Track ring exterior (arco total de sesión) ─────────────────────
        track_pen = QPen(QColor(c["progress_track"]), 2)
        p.setPen(track_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), _R_TRACK, _R_TRACK)

        # Arco de sesión (progreso total, delgado, gris suave)
        if self._session_progress > 0:
            session_pen = QPen(QColor(c["text_tertiary"]), 2)
            session_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(session_pen)
            rect_track = QRectF(
                cx - _R_TRACK, cy - _R_TRACK,
                _R_TRACK * 2, _R_TRACK * 2
            )
            span_deg = int(-self._session_progress * 360 * 16)
            p.drawArc(rect_track, 90 * 16, span_deg)

        # ── 3. Círculo relleno que respira ────────────────────────────────────
        r = self._circle_radius
        # Gradiente radial: centro ligeramente más brillante
        fill_grad = QRadialGradient(QPointF(cx, cy), r)
        base_c = QColor(self._phase_color)
        base_c.setAlpha(40)
        rim_c = QColor(self._phase_color)
        rim_c.setAlpha(20)
        fill_grad.setColorAt(0.0, base_c)
        fill_grad.setColorAt(1.0, rim_c)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill_grad))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Borde del círculo
        border_pen = QPen(QColor(self._phase_color), 2)
        border_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(border_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # ── 4. Arco de fase con QConicalGradient ──────────────────────────────
        if self._phase_progress > 0:
            arc_r = r - 8
            rect_arc = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)

            # Arco de progreso de la fase
            extent = max(self._phase_progress * 360, 2)
            segs = max(4, int(36 * self._phase_progress))
            seg_ext = extent / segs
            for i in range(segs):
                t = i / max(segs - 1, 1)
                col = _rich_color_at(self._modo, t)
                arc_pen = QPen(QColor(col), 6)
                arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(arc_pen)
                angle = 90 - i * seg_ext
                p.drawArc(rect_arc, int(angle * 16), int(-seg_ext * 16))

        # ── 5. Texto central ──────────────────────────────────────────────────
        p.setOpacity(self._text_opacity)

        # Número grande (segundos)
        font_big = qfont("size_h1", bold=True)
        font_big.setPointSize(38)
        p.setFont(font_big)
        p.setPen(QPen(QColor(c["text_primary"])))
        text_rect_top = QRectF(0, cy - 44, _CANVAS, 52)
        p.drawText(text_rect_top, Qt.AlignmentFlag.AlignCenter, self._center_text)

        # Nombre de fase debajo
        if self._phase_text:
            font_small = qfont("size_caption")
            p.setFont(font_small)
            p.setPen(QPen(QColor(self._phase_color)))
            text_rect_bot = QRectF(0, cy + 12, _CANVAS, 28)
            p.drawText(text_rect_bot, Qt.AlignmentFlag.AlignCenter, self._phase_text)

        p.restore()
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── StepCard ──────────────────────────────────────────────────────────────────

class _StepCard(QFrame):
    def __init__(self, label: str, secs: str, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._active = False
        self._accent = C("accent", self._modo)

        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(8, 8, 8, 8)
        vl.setSpacing(2)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl = QLabel(label)
        self._lbl.setFont(qfont("size_small", bold=True))
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self._lbl)

        self._secs_lbl = QLabel(secs)
        self._secs_lbl.setFont(qfont("size_caption"))
        self._secs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self._secs_lbl)

        self._update_style()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def set_active(self, active: bool, accent: str = None):
        self._active = active
        if accent:
            self._accent = accent
        self._update_style()

    def _update_style(self):
        c = colors(self._modo)
        if self._active:
            self.setStyleSheet(f"""
                _StepCard {{
                    background: {c['bg_elevated']};
                    border: 2px solid {self._accent};
                    border-radius: {RADIUS_CARD}px;
                }}
            """)
            self._lbl.setStyleSheet(f"color: {self._accent}; background: transparent;")
            self._secs_lbl.setStyleSheet(f"color: {self._accent}; background: transparent;")
        else:
            self.setStyleSheet(f"""
                _StepCard {{
                    background: {c['bg_surface']};
                    border: 1px solid {c.get('border_card', c['border'])};
                    border-radius: {RADIUS_CARD}px;
                }}
            """)
            self._lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
            self._secs_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._update_style()


# ── ModuloRespiracion ─────────────────────────────────────────────────────────

class ModuloRespiracion(NMModule):
    MODULE_TITLE = "Respiración"
    MODULE_ICON = "🌬️"

    def build_ui(self):
        # ── Estado de negocio (preservado exacto) ─────────────────────────────
        self._running = False
        self._paused = False
        self._elapsed_ms = 0
        self._session_ms = 0
        self._duration_min = 5
        self._ciclos = 0
        self._timer_id: QTimer | None = None
        self._phase_idx = 0
        self._phase_ms = 0
        self._last_phase_idx = -1   # para detectar cambio de fase

        # ── Layout principal ───────────────────────────────────────────────────
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(GAP_ELEMENTS)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        c = colors(self._modo)

        # ── Pills de preset ────────────────────────────────────────────────────
        pills_row = QHBoxLayout()
        pills_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pills_row.setSpacing(8)
        self._pill_btns: list[tuple[NMButtonOutline, int]] = []
        for label, mins in PRESETS:
            btn = NMButtonOutline(label, modo=self._modo)
            btn.setFixedSize(80, 34)
            btn.clicked.connect(lambda _, m=mins: self._select_preset(m))
            pills_row.addWidget(btn)
            self._pill_btns.append((btn, mins))
        layout.addLayout(pills_row)
        self._highlight_preset(5)

        # ── Círculo animado ────────────────────────────────────────────────────
        self._circle = _BreathCircle(self._content, self._modo)
        layout.addWidget(self._circle, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Cronómetro ─────────────────────────────────────────────────────────
        self._session_lbl = QLabel("")
        self._session_lbl.setFont(qfont("size_small"))
        self._session_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._session_lbl.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent;"
        )
        layout.addWidget(self._session_lbl)

        # ── Step cards ─────────────────────────────────────────────────────────
        steps_row = QHBoxLayout()
        steps_row.setSpacing(8)
        step_data = [("Inhala ↑ durante", "4 segundos"), ("Mantén durante", "7 segundos"), ("Exhala ↓ durante", "8 segundos")]
        self._step_cards: list[_StepCard] = []
        for label, secs in step_data:
            sc = _StepCard(label, secs, self._content, self._modo)
            steps_row.addWidget(sc)
            self._step_cards.append(sc)
        layout.addLayout(steps_row)

        # ── Controles ──────────────────────────────────────────────────────────
        ctrl_row = QHBoxLayout()
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_row.setSpacing(8)

        self._btn_start = NMButton("Iniciar", modo=self._modo, width=110, height=42)
        self._btn_start.clicked.connect(self._start)
        ctrl_row.addWidget(self._btn_start)

        self._btn_pause = NMButtonOutline("Pausa", modo=self._modo)
        self._btn_pause.setFixedSize(110, 42)
        self._btn_pause.clicked.connect(self._pause)
        ctrl_row.addWidget(self._btn_pause)

        self._btn_stop = NMButtonOutline("Detener", modo=self._modo)
        self._btn_stop.setFixedSize(110, 42)
        self._btn_stop.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_stop)

        layout.addLayout(ctrl_row)

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_circle"):
            self._circle._apply_theme(self._modo)
        self.update()

    # ── Lógica de preset (preservada) ─────────────────────────────────────────

    def _select_preset(self, mins: int):
        if self._running:
            return
        self._duration_min = mins
        self._highlight_preset(mins)

    def _highlight_preset(self, selected: int):
        for btn, mins in self._pill_btns:
            btn.set_active(mins == selected)

    # ── Controles (lógica preservada, adaptada a QTimer) ──────────────────────

    def _start(self):
        if self._running and self._paused:
            self._paused = False
            self._btn_start.setText("Reanudar")
            self._circle._render_timer.start(16)
            self._tick()
            return
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
        self._btn_start.setText("Reanudar")
        self._tick()

    def _pause(self):
        if not self._running:
            return
        self._paused = True
        self._btn_pause.setText("Pausado")
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
        self._btn_start.setText("Iniciar")
        self._btn_pause.setText("Pausa")
        self._circle.reset_idle()
        self._session_lbl.setText("")
        for sc in self._step_cards:
            sc.set_active(False)

    # ── Tick loop (lógica preservada, 100ms) ──────────────────────────────────

    def _tick(self):
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

        # Detectar cambio de fase para animar
        if self._phase_idx != self._last_phase_idx:
            self._last_phase_idx = self._phase_idx
            self._on_phase_change(self._phase_idx, phase_dur)
            self._circle.animate_text_change()

        # Actualizar datos del círculo
        secs_left = max(0, phase_dur - int(self._phase_ms / 1000))
        session_progress = self._elapsed_ms / total_ms
        self._circle.update_data(
            phase_progress=phase_progress,
            session_progress=session_progress,
            center_text=str(secs_left),
            phase_text=phase_name,
            phase_idx=self._phase_idx,
        )

        # Resaltar step card activa
        t = self._phase_idx / max(len(FASES) - 1, 1)
        phase_color = _rich_color_at(self._modo, t)
        for i, sc in enumerate(self._step_cards):
            sc.set_active(i == self._phase_idx, phase_color)

        # Cronómetro
        self._session_ms += interval
        s_total = self._session_ms // 1000
        self._session_lbl.setText(
            f"Sesión  {s_total // 60:02d}:{s_total % 60:02d}"
            f"   ·   Ciclos: {self._ciclos}"
        )

        # Avanzar tiempo
        self._phase_ms += interval
        self._elapsed_ms += interval

        if self._phase_ms >= phase_dur_ms:
            self._phase_ms = 0
            self._phase_idx += 1
            if self._phase_idx >= len(FASES):
                self._phase_idx = 0
                self._ciclos += 1

        # Siguiente tick
        if self._timer_id is None:
            self._timer_id = QTimer(self)
            self._timer_id.timeout.connect(self._tick)
        self._timer_id.start(interval)

    def _on_phase_change(self, phase_idx: int, phase_dur: int):
        """Iniciar animación de círculo apropiada para la nueva fase."""
        # 0=Inhala, 1=Mantén, 2=Exhala
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
        for sc in self._step_cards:
            sc.set_active(False)
        self._session_lbl.setText(f"✓ Sesión completa · {self._ciclos} ciclos")
        self._btn_start.setText("Iniciar")
        try:
            import winsound
            winsound.Beep(800, 300)
        except Exception:
            _log.exception("Operation failed")

    # ── DB (preservado exacto) ────────────────────────────────────────────────

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
        except Exception:
            _log.exception("Operation failed")

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
                return f"{n} sesión{'es' if n > 1 else ''} ✔"
        except Exception:
            _log.exception("Operation failed")
        return ""
