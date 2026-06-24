"""Arc and ring progress components with shared v3 gradient helpers."""

from __future__ import annotations

import math

from PyQt6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, QTimer, pyqtProperty
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget

from shared.fonts import FONT_SANS
from shared.theme import TYPOGRAPHY, V3_GRADIENTS, v3_mode
from shared.theme_manager import ThemeManager
from shared.theme_qt import ANIM, interpolate_color, norm_modo, qfont_mono, v3c


def _tm() -> ThemeManager:
    return ThemeManager.instance()


# ── Private helpers shared by all ring components ─────────────────────────────


def _ring_stroke(size: int) -> int:
    """Stroke proporcional al tamaño (README v3).

    ≤ 40       → 3-4
    41-60      → 6      (mockup `.ring` 54×54 / tk 6)
    61-100     → 6-8
    ≥ 100      → 10-14   (340 → 14)
    """
    if size <= 40:
        return max(3, round(size * 0.085))
    if size <= 60:
        return 6
    if size <= 80:
        return 6
    if size <= 100:
        return 8
    if size <= 140:
        return 10
    if size <= 200:
        return 12
    return 14


def _clamp_optional_pct(pct: float | None) -> float | None:
    if pct is None:
        return None
    try:
        value = float(pct)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return max(0.0, min(1.0, value))


def _color_at_t(stops, t: float) -> QColor:
    """Interpola entre stops ``[(hex, t_pos), …]`` ordenados por t_pos."""
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        h0, t0 = stops[i]
        h1, t1 = stops[i + 1]
        if t0 <= t <= t1:
            local = (t - t0) / max(1e-9, t1 - t0)
            return QColor(interpolate_color(h0, h1, local))
    return QColor(stops[-1][0])


def _paint_v3_arc(
    p: QPainter,
    rect: QRectF,
    start_angle_deg: float,
    span_deg: float,
    pen_width: int,
    modo: str,
    segments: int = 64,
):
    """Pinta un arco con el gradient firma v3 fluyendo a lo largo del arco.

    Implementación segmento-a-segmento con FlatCap (sin spokes intermedios) y
    círculos sólidos en los extremos para simular RoundCap. Funciona en
    cualquier dirección (CW o CCW) sin los líos de QConicalGradient.
    """
    import math

    if abs(span_deg) < 0.1:
        return
    stops = V3_GRADIENTS[v3_mode(modo)]
    direction = 1 if span_deg > 0 else -1
    abs_span = abs(span_deg)

    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(segments):
        t0 = i / segments
        t1 = (i + 1) / segments
        mid_t = (t0 + t1) / 2
        col = _color_at_t(stops, mid_t)
        pen = QPen(col, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        a0 = start_angle_deg + direction * abs_span * t0
        a1 = start_angle_deg + direction * abs_span * t1
        p.drawArc(rect, int(a0 * 16), int((a1 - a0) * 16))

    # Round caps manuales en los extremos del arco
    cx, cy = rect.center().x(), rect.center().y()
    rx, ry = rect.width() / 2, rect.height() / 2
    cap_r = pen_width / 2
    for endpoint_t, color_t in ((0.0, 0.0), (1.0, 1.0)):
        angle = math.radians(start_angle_deg + direction * abs_span * endpoint_t)
        # Qt: y aumenta hacia abajo, ángulo positivo es CCW desde +x
        px = cx + rx * math.cos(angle)
        py = cy - ry * math.sin(angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(_color_at_t(stops, color_t)))
        p.drawEllipse(QPointF(px, py), cap_r, cap_r)


class NMFocusArc(QWidget):
    """Arco circular de foco con aura, texto central, pulse y blink.

    Implementa la primitiva ``.bigring`` del mockup canónico
    (neuromood-mockup.html líneas 207-219):
      - contenedor 230×230 con radial-gradient brand-soft
      - inner core 200×200 con radial-gradient surface→surface-2,
        border 1px line, inset shadow + shadow-2
      - número central: 52px font-display weight 500 por defecto (mockup
        línea 213 .bigring .num), pero configurable via ``num_size``:
          · Timer (mockup línea 861): overridea a 46px con style inline
            → pasar ``num_size=46``
          · Respiración: usa el default 52px (.bigring .num del CSS base)
      - arco de progreso brand + glow (extensión runtime sobre el mockup)
      - pulse/blink animados (extensión runtime)
    """

    def __init__(
        self,
        size: int = 230,
        modo: str = None,
        num_size: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._pct = 0.0
        self._time_text = "25:00"
        self._state_text = "listo"
        # num_size: None = default 52px (mockup .bigring .num línea 213),
        # int = override (Timer pasa 46px según mockup línea 861).
        self._num_size_override = num_size
        # Efectos animados
        self._pulse_intensity = 0.0   # 0..1 — modula aura y glow mientras corre
        self._blink_on = True          # False = frame apagado en los últimos 10s
        self._anim_pulse: QPropertyAnimation | None = None
        self._blink_timer: QTimer | None = None
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    # ── pyqtProperty animable ─────────────────────────────────────────────────

    def _get_pulse_intensity(self) -> float:
        return self._pulse_intensity

    def _set_pulse_intensity(self, v: float) -> None:
        self._pulse_intensity = max(0.0, min(1.0, v))
        self.update()

    pulse_intensity = pyqtProperty(float, _get_pulse_intensity, _set_pulse_intensity)

    # ── API de datos ──────────────────────────────────────────────────────────

    def set_data(self, pct: float, time_text: str, state_text: str | None = None):
        self._pct = max(0.0, min(1.0, pct))
        self._time_text = time_text
        self.update()

    def update_data(self, progress: float, time_text: str):
        self.set_data(progress, time_text, self._state_text)

    # ── Animaciones de estado ─────────────────────────────────────────────────

    def start_pulse(self):
        """Aura que respira lentamente mientras el timer corre (loop infinito)."""
        self._state_text = "en curso"
        self._blink_on = True
        if self._anim_pulse is not None:
            return
        a = QPropertyAnimation(self, b"pulse_intensity", self)
        a.setDuration(ANIM["pulse"])
        a.setLoopCount(-1)
        a.setKeyValueAt(0.0, 0.15)
        a.setKeyValueAt(0.5, 1.0)
        a.setKeyValueAt(1.0, 0.15)
        a.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim_pulse = a
        a.start()

    def stop_pulse(self):
        """Pausa el timer — congela el pulso en base."""
        self._state_text = "pausado"
        self._stop_pulse_anim()
        self.update()

    def start_blink(self):
        """Parpadeo urgente para los últimos 10 s (coexiste con el pulse)."""
        if self._blink_timer is not None:
            return
        t = QTimer(self)
        t.setInterval(ANIM["blink"])
        t.timeout.connect(self._on_blink_tick)
        self._blink_timer = t
        t.start()

    def stop_blink(self):
        if self._blink_timer is not None:
            self._blink_timer.stop()
            self._blink_timer = None
        self._blink_on = True
        self.update()

    def _on_blink_tick(self) -> None:
        self._blink_on = not self._blink_on
        self.update()

    def show_finish(self):
        self._stop_all_anims()
        self.set_data(1.0, "00:00", "terminado")

    def reset(self):
        self._stop_all_anims()
        self.set_data(0.0, self._time_text, "listo")

    def _stop_pulse_anim(self) -> None:
        if self._anim_pulse is not None:
            try:
                self._anim_pulse.stop()
            except RuntimeError:
                pass
            self._anim_pulse = None
        self._pulse_intensity = 0.0

    def _stop_all_anims(self) -> None:
        self._stop_pulse_anim()
        self.stop_blink()

    # ── paintEvent ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        cx = cy = w / 2
        is_dark = "dark" in self._modo

        # ── Sección arc+aura: opacidad en blink-off (más alto en light para visibilidad)
        p.setOpacity(0.22 if not self._blink_on else 1.0)

        # Aura radial — radio y alpha adaptativos al tema (mockup .bigring bg)
        base_alpha = 0.18 if is_dark else 0.11
        pulse_boost = 0.10 if is_dark else 0.07   # boost más sutil en light
        aura_alpha = min(1.0, base_alpha + self._pulse_intensity * pulse_boost)
        aura_r = w * (0.42 + self._pulse_intensity * 0.03)
        aura = QRadialGradient(QPointF(cx, cy), aura_r)
        ac = QColor(v3c("teal", self._modo))
        ac.setAlphaF(aura_alpha)
        aura.setColorAt(0.0, ac)
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(aura)
        p.drawEllipse(QPointF(cx, cy), aura_r, aura_r)

        # Track sutil
        pen_w = _ring_stroke(w)
        r = w / 2 - pen_w - 1
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        track_col = v3c("borderSoft", self._modo)
        p.setPen(QPen(track_col, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Arco progreso con glow — glow se intensifica con pulse
        if self._pct > 0.001:
            glow_w = pen_w + 6
            glow_rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            base_glow = 40 if is_dark else 22
            pulse_glow = 40 if is_dark else 22   # amplitud del pulso también más sutil en light
            glow_col = QColor(v3c("teal", self._modo))
            glow_col.setAlpha(int(base_glow + self._pulse_intensity * pulse_glow))
            p.setPen(QPen(glow_col, glow_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            p.drawArc(glow_rect, int(90 * 16), int(-360.0 * self._pct * 16))
            if is_dark:
                glow_col2 = QColor(v3c("violet", self._modo))
                glow_col2.setAlpha(int(25 + self._pulse_intensity * 25))
                p.setPen(QPen(glow_col2, glow_w - 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.drawArc(glow_rect, int(90 * 16), int(-360.0 * self._pct * 16))
            _paint_v3_arc(p, rect, 90.0, -360.0 * self._pct, pen_w, self._modo)

        # ── Inner core 200×200 (mockup .bigring .core líneas 209-212) ────────
        # radial-gradient surface→surface-2 + border 1px line + inset shadow
        # + shadow-2. Escalado proporcional al tamaño del widget (200/230).
        core_d = w * (200.0 / 230.0)
        core_r = core_d / 2
        # Sombra exterior (shadow-2 approximation: 0 4px 12px rgba(0,0,0,.18))
        shadow_col = QColor(0, 0, 0, 46)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow_col))
        p.drawEllipse(QPointF(cx, cy + 2), core_r + 2, core_r + 2)
        # Core con radial-gradient surface → surface-2 (mockup: circle at 50% 38%,
        # surface 0% → surface-2 70%).
        core_grad = QRadialGradient(QPointF(cx, cy - core_r * 0.12), core_r)
        core_grad.setColorAt(0.0, QColor(v3c("surface", self._modo)))
        core_grad.setColorAt(0.70, QColor(v3c("surface2", self._modo)))
        core_grad.setColorAt(1.0, QColor(v3c("surface2", self._modo)))
        p.setBrush(QBrush(core_grad))
        p.setPen(QPen(QColor(v3c("line", self._modo)), 1))
        p.drawEllipse(QPointF(cx, cy), core_r, core_r)
        # Inset shadow sutil (mockup línea 211: inset 0 2px 10px rgba(0,0,0,.04))
        # Aproximación: arco superior interior con gradiente negro alpha 10/255.
        inset_pen = QPen(QColor(0, 0, 0, 10), 2)
        p.setPen(inset_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(
            QRectF(cx - core_r + 1, cy - core_r + 1, (core_r - 1) * 2, (core_r - 1) * 2),
            int(20 * 16),
            int(140 * 16),
        )

        # ── Tiempo central: siempre 100% opacidad para ser legible ───────────
        # Mockup línea 213: font-display 52px weight 500 (.bigring .num default).
        # Timer overridea a 46px (mockup línea 861 style="font-size:46px").
        # Si _num_size_override es None, usar 52px escalado proporcionalmente
        # al tamaño del widget. Si es int, usar ese valor absoluto.
        p.setOpacity(1.0)
        if self._num_size_override is not None:
            time_pt = int(self._num_size_override)
        else:
            time_pt = max(20, int(w * (52.0 / 230.0)))
        p.setPen(v3c("text", self._modo))
        try:
            from shared.theme_qt import v3_font as _v3_font
            p.setFont(_v3_font(time_pt, weight=TYPOGRAPHY["weight_medium"], serif=True))
        except ImportError:
            p.setFont(qfont_mono(time_pt, bold=True))
        p.drawText(QRectF(0, 0, w, w), Qt.AlignmentFlag.AlignCenter, self._time_text)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMCycleRing(QWidget):
    """Anillo de trazo pequeño con contador de ciclos de respiración.

    Columna izquierda del módulo Respiración.
    """

    def __init__(self, size: int = 56, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._cycles = 0
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_cycles(self, n: int):
        self._cycles = n
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        s = self._size
        cx, cy = s / 2, s / 2
        pen_w = _ring_stroke(s)
        r_out = s / 2 - pen_w - 1
        rect = QRectF(cx - r_out, cy - r_out, r_out * 2, r_out * 2)

        # Contorno completo con gradient firma v3 (no es progreso — siempre 360°)
        _paint_v3_arc(p, rect, 90.0, -359.99, pen_w, self._modo, segments=80)

        p.setPen(v3c("text", self._modo))
        p.setFont(qfont_mono(max(10, int(s * 0.22)), bold=False))
        # Peso semibold sin usar bold flag: usar v3_font sería ideal pero qfont_mono no
        # acepta weight; pintamos directo con la familia mono y dejamos bold=False
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, str(self._cycles))
        p.restore()
        p.end()


class NMModuleRing(QWidget):
    """Ring de progreso de módulo, equivalente al CSS `.ring` del mockup.

    ``show_label``: si True (default), pinta "NN%" centrado. En tamaños pequeños
    (<32px) el label es ilegible — usar show_label=False y delegar el % a una
    chip/badge externa.
    """

    DEFAULT_SIZE = 54

    def __init__(
        self,
        size: int = DEFAULT_SIZE,
        pct: float | None = 0.0,
        modo: str = None,
        show_label: bool = True,
        color_key: str = "primary",
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._pct = _clamp_optional_pct(pct)
        self._size = size
        self._show_label = bool(show_label)
        self._color_key = color_key or "primary"
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_pct(self, pct: float | None):
        self._pct = _clamp_optional_pct(pct)
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        s = self._size
        cx, cy = s / 2, s / 2
        pen_w = _ring_stroke(s)
        r_arc = s / 2 - pen_w / 2 - 0.5
        arc_rect = QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2)

        # (F2 runtime: el glow radial teal detrás del arco fue eliminado —
        # el anillo se sostiene solo con track + arco firma, sin halo.)

        # Track exacto del mockup: var(--ring-track).
        track_c = v3c("ringTrack", self._modo)
        p.setPen(QPen(track_c, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r_arc, r_arc)

        # Arco progreso con brand sólido, equivalente a conic-gradient(var(--brand)).
        if self._pct is not None and self._pct > 0.001:
            p.setPen(
                QPen(
                    v3c(self._color_key, self._modo),
                    pen_w,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.FlatCap,
                )
            )
            p.drawArc(arc_rect, int(90.0 * 16), int(-360.0 * self._pct * 16))

        # Centro superficie, como `.ring::before`.
        inner_r = max(0.0, s / 2 - pen_w)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(v3c("surface", self._modo)))
        p.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # Texto centrado (solo si show_label=True; tamaños chicos no lo pintan)
        if self._show_label:
            p.setPen(v3c(self._color_key, self._modo))
            # Mockup usa sans (Inter) para los anillos, NO monospace. El 60% del
            # real se renderizaba en Consolas mono (qfont_mono) y no matcheaba.
            _label_px = 12 if s >= 50 else max(9, int(s * 0.20))
            _f = QFont(FONT_SANS, _label_px)
            _f.setWeight(QFont.Weight.Bold)
            _f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
            p.setFont(_f)
            label = "—" if self._pct is None else f"{int(self._pct * 100)}%"
            p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, label)

        p.restore()
        p.end()
