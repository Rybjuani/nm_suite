"""
app/modules/timer_qt.py — Módulo Timer (PyQt6)

LÓGICA PRESERVADA EXACTA de timer.py:
  PRESETS, _tick() a 16ms (60fps), _save_session(), get_card_status()
  _start(), _pause(), _stop(), _finish()

NUEVAS CAPACIDADES:
  Tick a 16ms (60fps) para arco fluido
  Círculo pulsante sutil (±4px a 0.8Hz) mientras corre
  Texto MM:SS solo en el centro del arco (sin label externo)
  Finish screen: arco success + "¡Tiempo! ✓" con scale bounce en 500ms OutBack
  Vibración visual últimos 10s: alpha 100%→70%→100% cada 500ms
"""

import os
import sys
import math
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    pyqtProperty, QAbstractAnimation, QSequentialAnimationGroup,
    QVariantAnimation,
)
from PyQt6 import sip
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath,
    QConicalGradient, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSizePolicy, QGraphicsOpacityEffect,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMInput, NMToast, ThemeManager,
        NMEmptyState, NMPresetChip, NMFocusArc, NMSessionHistory,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        get_gradient, gradient_colors, stylesheet_lineedit,
        PAD_CONTAINER, GAP_ELEMENTS, RADIUS_BUTTON, RADIUS_PILL,
        ThemeAwareWidgetMixin, sp,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMInput, NMToast, ThemeManager,
        NMEmptyState, NMPresetChip, NMFocusArc, NMSessionHistory,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        get_gradient, gradient_colors, stylesheet_lineedit,
        PAD_CONTAINER, GAP_ELEMENTS, RADIUS_BUTTON, RADIUS_PILL,
        ThemeAwareWidgetMixin, sp,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual

PRESETS = [
    ("5 min",  5 * 60),
    ("10 min", 10 * 60),
    ("25 min", 25 * 60),
    ("45 min", 45 * 60),
]

_CANVAS = 280
_R_BASE = 110       # radio base del arco
_ARC_W  = 10        # grosor del arco


def _rich_color_at(modo: str, t: float) -> str:
    palette = gradient_colors(modo)
    if len(palette) < 3:
        return interpolate_color(palette[0], palette[-1], t)
    if t <= 0.45:
        return interpolate_color(palette[0], palette[1], t / 0.45)
    return interpolate_color(palette[1], palette[2], (t - 0.45) / 0.55)


# ── TimerCanvas ───────────────────────────────────────────────────────────────

class _TimerCanvas(ThemeAwareWidgetMixin, QWidget):
    """
    Canvas del timer. Propiedades animables:
      arc_alpha:     float 0–1  (parpadeo en últimos 10s)
      pulse_offset:  float      (oscilación radio ±4px)
      finish_scale:  float 0–1  (scale bounce del texto ¡Tiempo! ✓)
    """

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._progress = 0.0        # 0.0 = lleno, 1.0 = vacío
        self._time_text = "00:00"
        self._finished = False
        self._arc_alpha = 1.0
        self._pulse_offset = 0.0
        self._finish_scale = 0.0

        # Timer de 60fps
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self.update)

        # Animación de pulso (radio ±4px a 0.8Hz = 1250ms)
        self._pulse_anim: QPropertyAnimation | None = None

        self._connect_theme()

    # ── pyqtProperties ───────────────────────────────────────────────────────

    def _get_arc_alpha(self) -> float: return self._arc_alpha
    def _set_arc_alpha(self, v: float): self._arc_alpha = v

    arc_alpha = pyqtProperty(float, _get_arc_alpha, _set_arc_alpha)

    def _get_pulse_offset(self) -> float: return self._pulse_offset
    def _set_pulse_offset(self, v: float): self._pulse_offset = v

    pulse_offset = pyqtProperty(float, _get_pulse_offset, _set_pulse_offset)

    def _get_finish_scale(self) -> float: return self._finish_scale
    def _set_finish_scale(self, v: float): self._finish_scale = v

    finish_scale = pyqtProperty(float, _get_finish_scale, _set_finish_scale)

    # ── API ───────────────────────────────────────────────────────────────────

    def update_data(self, progress: float, time_text: str):
        self._progress = progress
        self._time_text = time_text
        self.update()

    def _start_rendering(self):
        if self.isVisible() and not self._fps_timer.isActive():
            self._fps_timer.start(16)

    def _stop_rendering(self):
        if self._fps_timer.isActive():
            self._fps_timer.stop()

    def start_pulse(self):
        self._start_rendering()
        if self._pulse_anim:
            self._pulse_anim.stop()
        self._pulse_anim = QPropertyAnimation(self, b"pulse_offset", self)
        self._pulse_anim.setDuration(1250)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setKeyValueAt(0.5, 4.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)  # loop infinito
        self._pulse_anim.start()

    def stop_pulse(self):
        if self._pulse_anim:
            self._pulse_anim.stop()
            self._pulse_anim = None
        self._pulse_offset = 0.0
        if not getattr(self, "_blink_anim", None):
            self._stop_rendering()

    def start_blink(self):
        """Parpadeo de los últimos 10s."""
        self._start_rendering()
        a = QPropertyAnimation(self, b"arc_alpha", self)
        a.setDuration(500)
        a.setStartValue(1.0)
        a.setKeyValueAt(0.5, 0.65)
        a.setEndValue(1.0)
        a.setLoopCount(-1)
        a.start()
        self._blink_anim = a

    def stop_blink(self):
        if hasattr(self, "_blink_anim"):
            self._blink_anim.stop()
            self._blink_anim = None
        self._arc_alpha = 1.0
        if not self._pulse_anim:
            self._stop_rendering()

    def show_finish(self):
        """Arco success + texto bounce."""
        self._finished = True
        self._start_rendering()
        self.stop_pulse()
        self.stop_blink()
        self._start_rendering()
        a = QPropertyAnimation(self, b"finish_scale", self)
        a.setDuration(500)
        a.setStartValue(0.0)
        a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.Type.OutBack)
        a.finished.connect(self._stop_rendering)
        a.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def reset(self):
        self.stop_pulse()
        self.stop_blink()
        self._finished = False
        self._finish_scale = 0.0
        self._arc_alpha = 1.0
        self._progress = 0.0
        self._time_text = "00:00"
        self._stop_rendering()

    def showEvent(self, event):
        super().showEvent(event)
        if self._pulse_anim or getattr(self, "_blink_anim", None) or self._finished:
            self._start_rendering()

    def hideEvent(self, event):
        self._stop_rendering()
        super().hideEvent(event)

    # ── paintEvent ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        cx = cy = self.width() / 2
        sc = min(self.width(), self.height()) / _CANVAS
        r = (_R_BASE + self._pulse_offset) * sc
        arc_w = _ARC_W * sc

        # Track ring
        track_pen = QPen(QColor(c["progress_track"]), arc_w)
        p.setPen(track_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        if self._finished:
            # Arco success completo
            arc_pen = QPen(QColor(C("success", self._modo)), arc_w)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            p.drawArc(rect, 90 * 16, -360 * 16)

            # Texto "¡Tiempo! ✓" con scale bounce
            if self._finish_scale > 0:
                p.save()
                scale = self._finish_scale
                p.translate(cx, cy)
                p.scale(scale, scale)
                p.translate(-cx, -cy)
                font = qfont("size_h2", bold=True)
                p.setFont(font)
                p.setPen(QPen(QColor(C("success", self._modo))))
                p.drawText(QRectF(0, cy - 28, self.width(), 56),
                       Qt.AlignmentFlag.AlignCenter, "¡Tiempo! ✓")
                p.restore()
        else:
            # Arco de progreso con gradiente 3-stop
            p.setOpacity(self._arc_alpha)
            extent = max(self._progress * 360, 2)
            rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            arc_pen = QPen(QColor(gradient_colors(self._modo)[0]), arc_w)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            segs = 36
            seg_ext = extent / segs
            for i in range(segs):
                t = i / max(segs - 1, 1)
                col = _rich_color_at(self._modo, t)
                pen = QPen(QColor(col), arc_w)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                angle = 90 - i * seg_ext
                p.drawArc(rect, int(angle * 16), int(-seg_ext * 16))

            # Texto MM:SS central
            p.setOpacity(1.0)
            font_big = qfont("size_h1", bold=True)
            font_big.setPointSize(32)
            p.setFont(font_big)
            p.setPen(QPen(QColor(c["text_primary"])))
            p.drawText(QRectF(0, cy - 28, self.width(), 56),
                       Qt.AlignmentFlag.AlignCenter, self._time_text)

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)


# ── ModuloTimer ───────────────────────────────────────────────────────────────

class ModuloTimer(NMModule):
    MODULE_TITLE = "Temporizador"
    MODULE_ICON = "timer"

    def build_ui(self):
        # Estado de negocio (preservado exacto)
        self._running = False
        self._paused = False
        self._total_sec = 25 * 60
        self._remaining_sec = 25 * 60
        self._timer_id: QTimer | None = None
        self._custom_mode = False
        self._last_10s_blink = False

        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(GAP_ELEMENTS)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        c = colors(self._modo)

        # ── Actividad ──────────────────────────────────────────────────────────
        self._empty_state = NMEmptyState(
            "fa5s.hourglass-half",
            "Timer listo",
            "Configurá el tiempo y empezá.",
            self._content,
        )
        layout.addWidget(self._empty_state)

        self._ent_actividad = NMInput("Nombre de la actividad (opcional)", modo=self._modo)
        layout.addWidget(self._ent_actividad)

        # ── Chips de preset ───────────────────────────────────────────────────
        chips_row = QHBoxLayout()
        chips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chips_row.setSpacing(6)
        self._chip_btns: list[tuple[NMPresetChip, int]] = []
        for label, secs in PRESETS:
            btn = NMPresetChip(label, modo=self._modo)
            btn.setFixedSize(76, 32)
            btn.clicked.connect(lambda _, s=secs: self._select_preset(s))
            chips_row.addWidget(btn)
            self._chip_btns.append((btn, secs))

        # Chip "Otro"
        self._btn_custom = NMButtonOutline("Otro", modo=self._modo)
        self._btn_custom.setFixedSize(56, 32)
        self._btn_custom.clicked.connect(self._show_custom_input)
        chips_row.addWidget(self._btn_custom)
        layout.addLayout(chips_row)
        self._highlight_preset(25 * 60)

        # Input custom (oculto por defecto)
        self._custom_widget = QWidget()
        self._custom_widget.setVisible(False)
        cw_row = QHBoxLayout(self._custom_widget)
        cw_row.setContentsMargins(0, 0, 0, 0)
        cw_row.setSpacing(6)
        self._entry_custom = QLineEdit()
        self._entry_custom.setPlaceholderText("min")
        self._entry_custom.setFixedSize(80, 34)
        self._entry_custom.setStyleSheet(stylesheet_lineedit(self._modo))
        cw_row.addWidget(self._entry_custom)
        btn_ok = NMButtonOutline("OK", modo=self._modo)
        btn_ok.setFixedSize(42, 34)
        btn_ok.clicked.connect(self._apply_custom)
        cw_row.addWidget(btn_ok)
        layout.addWidget(self._custom_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Canvas ────────────────────────────────────────────────────────────
        self._canvas = NMFocusArc(size=160, modo=self._modo)
        self._canvas.update_data(0.0, "25:00")
        layout.addWidget(self._canvas, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Controles ─────────────────────────────────────────────────────────
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

        # ── Activity name label (shown during session) ────────────────────────
        self._lbl_active_name = QLabel("")
        self._lbl_active_name.setFont(qfont("size_caption"))
        self._lbl_active_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_active_name.setStyleSheet(
            f"color: {c['text_secondary']}; background: transparent;"
        )
        self._lbl_active_name.hide()
        layout.addWidget(self._lbl_active_name)

        # ── Quick history footer (last 3 sessions today) ──────────────────────
        self._session_history = NMSessionHistory(modo=self._modo)
        layout.addWidget(self._session_history)

        self._load_quick_history()

    # ── Presets ───────────────────────────────────────────────────────────────

    def _select_preset(self, secs: int):
        if self._running:
            return
        self._total_sec = secs
        self._remaining_sec = secs
        self._custom_mode = False
        self._custom_widget.setVisible(False)
        self._highlight_preset(secs)
        self._update_canvas()

    def _highlight_preset(self, selected: int):
        for btn, secs in self._chip_btns:
            btn.set_active(secs == selected and not self._custom_mode)
        self._btn_custom.set_active(self._custom_mode)

    def _show_custom_input(self):
        if self._running:
            return
        self._custom_mode = True
        self._custom_widget.setVisible(True)
        self._highlight_preset(-1)
        self._entry_custom.setFocus()

    def _apply_custom(self):
        try:
            mins = int(self._entry_custom.text().strip())
            mins = max(1, min(120, mins))
            self._total_sec = mins * 60
            self._remaining_sec = self._total_sec
            self._update_canvas()
        except ValueError:
            pass
        self._custom_widget.setVisible(False)

    # ── Display ───────────────────────────────────────────────────────────────

    def _format_time(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def _update_canvas(self):
        progress = (self._remaining_sec / self._total_sec) if self._total_sec > 0 else 1.0
        self._canvas.update_data(progress, self._format_time(self._remaining_sec))

    # ── Controles (preservados) ───────────────────────────────────────────────

    def _start(self):
        if self._running and self._paused:
            self._paused = False
            self._btn_pause.setText("Pausa")
            self._canvas.start_pulse()
            self._tick()
            return
        if self._running:
            return
        if hasattr(self, "_empty_state"):
            self._empty_state.hide()
        self._running = True
        self._paused = False
        self._remaining_sec = self._total_sec
        self._last_10s_blink = False
        self._btn_start.setText("Reanudar")
        self._canvas.reset()
        self._canvas.start_pulse()
        # Show activity name below canvas during session
        nombre = self._ent_actividad.text().strip()
        if hasattr(self, "_lbl_active_name"):
            if nombre:
                self._lbl_active_name.setText(nombre)
                self._lbl_active_name.show()
            else:
                self._lbl_active_name.hide()
        self._tick()

    def _pause(self):
        if not self._running:
            return
        self._paused = True
        self._btn_pause.setText("Pausado")
        self._canvas.stop_pulse()
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None

    def _stop(self):
        was_running = self._running
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        self._canvas.stop_pulse()
        self._canvas.stop_blink()
        elapsed = self._total_sec - self._remaining_sec
        if was_running and elapsed >= 30:
            self._save_session(elapsed)
        self._running = False
        self._paused = False
        self._remaining_sec = self._total_sec
        self._btn_start.setText("Iniciar")
        self._btn_pause.setText("Pausa")
        if hasattr(self, "_empty_state"):
            self._empty_state.show()
        if hasattr(self, "_lbl_active_name"):
            self._lbl_active_name.hide()
        self._canvas.reset()
        self._update_canvas()
        self._load_quick_history()

    # ── Tick (16ms = 60fps, pero lógica de segundos preservada) ──────────────

    def _tick(self):
        if not self._running or self._paused:
            return
        if self._remaining_sec <= 0:
            self._finish()
            return

        self._remaining_sec -= 1
        self._update_canvas()

        # Activar parpadeo en últimos 10 segundos
        if self._remaining_sec <= 10 and not self._last_10s_blink:
            self._last_10s_blink = True
            self._canvas.start_blink()

        if self._timer_id is None:
            self._timer_id = QTimer(self)
            self._timer_id.timeout.connect(self._tick)
        self._timer_id.start(1000)

    def _finish(self):
        self._running = False
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        self._save_session(self._total_sec)
        self._btn_start.setText("Iniciar")
        self._btn_pause.setText("Pausa")
        self._canvas.show_finish()
        try:
            import winsound
            winsound.Beep(1000, 400)
            QTimer.singleShot(500, lambda: winsound.Beep(1000, 400))
        except Exception:
            _log.exception("Operation failed")

        # Auto-restaurar ventana y mostrar toast
        nombre = self._ent_actividad.text().strip() or "Sin nombre"
        top = self.window()
        if top and top.isMinimized():
            top.showNormal()
        if top:
            top.raise_()
            top.activateWindow()
        NMToast.display(top, f"Tiempo para \"{nombre}\" finalizado ✓", variant="success", duration_ms=4000)

        # Reset después de 4 segundos
        QTimer.singleShot(4000, lambda: self._reset_after_finish() if not sip.isdeleted(self) else None)

    def _reset_after_finish(self):
        self._canvas.reset()
        self._remaining_sec = self._total_sec
        self._update_canvas()
        if hasattr(self, "_lbl_active_name"):
            self._lbl_active_name.hide()
        self._load_quick_history()

    # ── DB (preservado exacto) ────────────────────────────────────────────────

    def _save_session(self, duracion: int):
        nombre = self._format_time(self._total_sec) + " timer"
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO actividades_temporizador "
                "(fecha, hora, nombre, categoria, duracion_config, duracion_real) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), nombre, "Timer",
                 self._total_sec, duracion),
            )
            conn.commit()
            conn.close()
            if hasattr(self._btn_start, "play_success"):
                self._btn_start.play_success()
        except Exception:
            _log.exception("Operation failed")

    def _load_quick_history(self):
        """Populate the quick history footer with last 3 sessions today."""
        sessions = []
        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT nombre, duracion_real FROM actividades_temporizador "
                "WHERE fecha = ? ORDER BY rowid DESC LIMIT 3",
                (fecha_hoy(),)
            ).fetchall()
            conn.close()
            for row in rows:
                dr = row["duracion_real"] if isinstance(row, dict) or hasattr(row, "keys") else row[1]
                mins = dr // 60
                secs = dr % 60
                name = row["nombre"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
                sessions.append(f"{name} · {mins:02d}:{secs:02d}")
            if hasattr(self, "_session_history"):
                self._session_history.set_sessions(sessions)
        except Exception:
            _log.exception("Operation failed")

    def on_leave(self):
        if self._running:
            elapsed = self._total_sec - self._remaining_sec
            self._stop()
            msg = "Sesión guardada" if elapsed >= 30 else "Timer detenido — menos de 30 s, no se guardó"
            NMToast.display(self.window(), msg, variant="warning")

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha=?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} sesión{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
