"""Feedback components shared by Suite and Hub."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QTextOption,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget

from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    ANIM,
    C,
    RADIUS_SMALL,
    blend_color,
    colors,
    interpolate_color,
    nm_icon,
    norm_modo,
    qfont,
    v3c,
)


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


class NMSkeleton(QWidget):
    """
    Rectangulo de carga animado con gradiente deslizante.
    Uso: skeleton = NMSkeleton(parent, width=200, height=16, radius=8)
    """

    def __init__(self, parent=None, width=200, height=16, radius=8, modo=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._radius = radius
        self._pos = 0.0
        self.setFixedSize(width, height)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        _tm().theme_changed.connect(self._apply_theme)

    def _tick(self):
        self._pos = (self._pos + 0.012) % 1.4
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = QRectF(self.rect())

        p.setBrush(QColor(c["bg_elevated"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, self._radius, self._radius)

        sx = (self._pos - 0.3) * self.width()
        sw = self.width() * 0.4
        sg = QLinearGradient(sx, 0, sx + sw, 0)
        sg.setColorAt(0.0, QColor(255, 255, 255, 0))
        sg.setColorAt(0.5, QColor(255, 255, 255, 18))
        sg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sg))
        p.drawRoundedRect(r, self._radius, self._radius)
        p.end()

    def _apply_theme(self, modo):
        self._modo = norm_modo(modo)
        self.update()


class NMProgressBar(QWidget):
    """
    Barra de progreso custom con fill gradiente teal→violet.
    Propiedad animable: value (0.0–1.0).
    """

    def __init__(self, parent=None, height: int = 6, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._value = 0.0
        self._bar_h = height
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _tm().theme_changed.connect(self._apply_theme)

    # value como pyqtProperty para QPropertyAnimation
    def _get_value(self) -> float:
        return self._value

    def _set_value(self, v: float):
        self._value = max(0.0, min(1.0, v))
        self.update()

    value = pyqtProperty(float, _get_value, _set_value)

    def animate_to(self, target: float, duration: int = 400):
        a = QPropertyAnimation(self, b"value", self)
        a.setDuration(duration)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.setEndValue(target)
        a.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def set_progress(self, frac: float) -> None:
        """API compatible con NMProgressLine para reemplazos drop-in."""
        self._set_value(frac)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = self._bar_h // 2
        w = self.width()
        h = self.height()
        rect = QRectF(0, 0, w, h)

        # Track
        p.setBrush(QBrush(QColor(c["progress_track"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Fill — barra sólida continua con caps redondeados (runtime).
        # El dithering de puntitos anterior se leía "técnico/punteado" — el
        # user feedback lo marcó como random design en el informe v1.0 final.
        # F5 runtime: fill `primary` SÓLIDO sobre track neutro (lo lineal
        # va plano; el gradiente firma queda solo en lo circular/identitario).
        # (El shimmer fue eliminado en F2.)
        fill_w = w * self._value
        if fill_w > 0:
            fill_rect = QRectF(0, 0, fill_w, h)
            p.setBrush(QBrush(v3c("primary", self._modo)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(fill_rect, r, r)

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMProgressLine(QWidget):
    """Línea de progreso ultra-fina (2 px, full-width) con gradiente teal→violet.

    Uso: colocar en borde superior del área de contenido de módulos y Hub.
    """

    def __init__(self, total: int = 1, current: int = 0, modo: str = None, parent=None):
        super().__init__(parent)
        self._total = max(1, total)
        self._current = current
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedHeight(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_progress(self, current: int, total: int = None):
        if total is not None:
            self._total = max(1, total)
        self._current = current
        self.update()

    @property
    def pct(self) -> float:
        return min(1.0, max(0.0, self._current / self._total))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        fill_w = int(w * self.pct)
        # Track: V3 border token — warm stone (light) / dark navy (dark)
        track = v3c("border", self._modo)
        track.setAlpha(80)
        p.fillRect(0, 0, w, h, track)
        if fill_w > 0:
            # F5 runtime: fill `primary` sólido (lo lineal va plano).
            p.fillRect(0, 0, fill_w, h, v3c("primary", self._modo))
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMRingPulse(QWidget):
    """Anillo único que se expande desde el centro y se desvanece — 500 ms, 1 pulso.

    Uso:
        self._ring_pulse = NMRingPulse(self._content, modo=self._modo)
        # Al finalizar sesión:
        self._ring_pulse.launch()

    El anillo cubre todo el widget padre (overlay transparente a eventos).
    Dos capas concéntricas: teal principal + violet secundario al 88 % del radio.
    """

    def __init__(self, parent: QWidget, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._t = 0.0          # 0→1: controla radio + alpha simultáneamente
        self._max_r = 1.0      # se calcula en launch() según tamaño del padre
        self._anim: QPropertyAnimation | None = None
        self.hide()
        parent.installEventFilter(self)

    # ── resize tracking ───────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type().name in ("Resize", "Move"):
            self.setGeometry(self.parent().rect())
        return super().eventFilter(obj, event)

    # ── pyqtProperty animable ─────────────────────────────────────────────────

    def _get_t(self) -> float:
        return self._t

    def _set_t(self, v: float) -> None:
        self._t = max(0.0, min(1.0, v))
        self.update()

    pulse_t = pyqtProperty(float, _get_t, _set_t)

    # ── API ───────────────────────────────────────────────────────────────────

    def launch(self) -> None:
        """Dispara el pulso. Idempotente: cancela pulso previo si existía."""
        par = self.parent()
        if par is None:
            return
        self.setGeometry(par.rect())
        w, h = float(par.width()), float(par.height())
        self._max_r = (w ** 2 + h ** 2) ** 0.5 / 2.0
        self._t = 0.0
        self.raise_()
        self.show()

        if self._anim:
            try:
                self._anim.stop()
            except RuntimeError:
                pass
        self._anim = QPropertyAnimation(self, b"pulse_t", self)
        self._anim.setDuration(ANIM["ring"])
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    # ── render ────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        if self._t <= 0 or self._max_r <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        center = QPointF(cx, cy)

        is_dark = "dark" in self._modo
        r = self._t * self._max_r
        # Alpha máximo y grosor de trazo difieren por tema:
        # dark → más dramático sobre bg oscuro; light → más sutil sobre bg claro
        a_max = 210 if is_dark else 155
        a = int(a_max * (1.0 - self._t) ** 1.5)
        stroke_main = 2.5 if is_dark else 2.0
        stroke_sec  = 1.5 if is_dark else 1.0

        # Anillo principal — teal
        teal = QColor(v3c("teal", self._modo))
        teal.setAlpha(a)
        p.setPen(QPen(teal, stroke_main))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(center, r, r)

        # Anillo secundario — violet, al 88 % del radio
        violet = QColor(v3c("violet", self._modo))
        sec_mult = 0.55 if is_dark else 0.45
        violet.setAlpha(int(a * sec_mult))
        p.setPen(QPen(violet, stroke_sec))
        p.drawEllipse(center, r * 0.88, r * 0.88)

        p.end()


class NMTypingDots(QWidget):
    """Indicador animado de 'IA escribiendo...' (3 puntos secuenciales).

    Llamar a start()/stop() para controlar la animación.
    """

    # Spec README v3: "3 dots con animación translateY(-4px) escalonada
    # (delay 0/0.15/0.3s)" — implementado con phase continuous + sin wave.
    _PERIOD_MS = 1200  # ciclo completo
    _STAGGER_MS = 150  # 0.15s entre dots
    _BOUNCE_PX = 4  # translateY -4px en el pico

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._t_ms = 0
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps (suave para anim continua)
        self._timer.timeout.connect(self._tick)
        self._running = False
        self.setFixedSize(48, 24)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def start(self):
        self._running = True
        self._t_ms = 0
        self._timer.start()

    def stop(self):
        self._running = False
        self._timer.stop()
        self.update()

    def _tick(self):
        if sip.isdeleted(self):
            self._timer.stop()
            return
        self._t_ms = (self._t_ms + 33) % self._PERIOD_MS
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        import math

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        dot_r = 4
        gap = 12
        y_c = self.height() / 2
        x_start = dot_r + 2
        base_c = QColor(C("teal", self._modo))
        for i in range(3):
            # Phase shift por dot — 0.15s stagger
            if self._running:
                phase = ((self._t_ms - i * self._STAGGER_MS) % self._PERIOD_MS) / self._PERIOD_MS
                # bounce: pico arriba en phase 0.5, queda abajo en 0/1
                # Usamos curva senoidal solo en la primera mitad del ciclo
                if 0 <= phase < 0.5:
                    bounce = math.sin(phase * math.pi)  # 0→1→0
                else:
                    bounce = 0.0
                offset_y = -self._BOUNCE_PX * bounce
                alpha = 0.4 + 0.6 * bounce  # 0.4 idle, 1.0 peak
            else:
                offset_y = 0.0
                alpha = 0.3
            dc = QColor(base_c)
            dc.setAlphaF(alpha)
            p.setBrush(QBrush(dc))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x_start + i * gap, y_c + offset_y), dot_r, dot_r)
        p.restore()
        p.end()


_NM_TOAST_DEFAULT_DURATION = 2200
_NM_TOAST_MAX_WIDTH = 360
_NM_TOAST_MIN_WIDTH = 220
_NM_TOAST_ICON_SIZE = 16
_NM_TOAST_GAP = 9
_NM_TOAST_PAD_X = 20
_NM_TOAST_PAD_Y = 12
_NM_TOAST_BOTTOM_MARGIN = 24
_NM_TOAST_SLIDE_PX = 20
_NM_TOAST_SHADOW_PAD = 4


class NMToast(QWidget):
    """
    Notificación inline en la esquina inferior derecha de la VENTANA.
    Variantes: 'success', 'error', 'info', 'warning'.

    Es un child overlay con parent real, SIN window flags: nunca crea una
    ventana top-level. (Antes era una ventana Qt.ToolTip|StaysOnTop y el
    lector de pantalla la resaltaba como "mini ventana titilante" fuera de
    la app — informe user feedback, frente 2.) El fade usa painter.setOpacity,
    no QGraphicsOpacityEffect: ahora vive bajo ancestros que pueden tener
    drop-shadows y Qt no soporta efectos anidados.
    """

    _VARIANT_KEYS = {
        "success": "success",
        "error": "danger",
        "info": "accent",
        "warning": "warning",
    }

    # Un toast activo por ventana: el nuevo reemplaza al anterior (antes se
    # apilaban superpuestos en la misma esquina).
    _active_by_host: dict = {}

    def __init__(
        self,
        parent_window: QWidget,
        message: str,
        variant: str = "info",
        duration_ms: int = _NM_TOAST_DEFAULT_DURATION,
    ):
        host = parent_window.window() if parent_window is not None else None
        super().__init__(host)
        self._host = host
        self._variant = variant
        self._message = message
        self._duration = duration_ms
        self._opacity = 0.0
        self._slide_offset = float(_NM_TOAST_SLIDE_PX)
        self._modo = norm_modo(ThemeManager.instance().modo)
        key = self._VARIANT_KEYS.get(variant, self._VARIANT_KEYS["info"])
        self._color = v3c(key, self._modo).name()
        self.setObjectName(f"NMToast_{variant}")
        self.setAccessibleName(f"NMToast {variant}: {message}")
        self.setAccessibleDescription("NeuroMood toast notification")
        # No roba foco ni clicks: el navegador de accesibilidad no debe
        # saltar al toast.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._setup_ui()

    def _setup_ui(self):
        # Texto auto-pintado en paintEvent (sin QLabel hijo): el fade por
        # painter.setOpacity debe afectar carta y texto por igual.
        self._font = qfont(13, weight=500)
        self._text_color = v3c("surface", self._modo)
        self._bg_color = v3c("ink", self._modo)
        self._icon_pix = nm_icon("check", v3c("primary", self._modo), size=_NM_TOAST_ICON_SIZE).pixmap(
            _NM_TOAST_ICON_SIZE, _NM_TOAST_ICON_SIZE
        )
        self._margins = (
            _NM_TOAST_PAD_X,
            _NM_TOAST_PAD_Y,
            _NM_TOAST_PAD_X,
            _NM_TOAST_PAD_Y,
        )
        ml, mt, mr, mb = self._margins
        fm = QFontMetrics(self._font)
        avail = _NM_TOAST_MAX_WIDTH - ml - mr - _NM_TOAST_ICON_SIZE - _NM_TOAST_GAP
        text_rect = fm.boundingRect(
            QRect(0, 0, avail, 1000), int(Qt.TextFlag.TextWordWrap), self._message
        )
        w = max(
            _NM_TOAST_MIN_WIDTH,
            min(
                _NM_TOAST_MAX_WIDTH,
                text_rect.width() + _NM_TOAST_ICON_SIZE + _NM_TOAST_GAP + ml + mr,
            ),
        )
        h = max(_NM_TOAST_ICON_SIZE, text_rect.height()) + mt + mb + _NM_TOAST_SHADOW_PAD
        self.setFixedSize(w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setOpacity(self._opacity)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        content_h = h - _NM_TOAST_SHADOW_PAD
        r = content_h / 2

        p.setPen(Qt.PenStyle.NoPen)
        shadow = QColor(0, 0, 0, 52 if "dark" in self._modo else 34)
        p.setBrush(QBrush(shadow))
        p.drawRoundedRect(QRectF(4, 3, w - 8, content_h), r, r)

        p.setBrush(QBrush(self._bg_color))
        p.drawRoundedRect(QRectF(0, 0, w, content_h), r, r)

        # Texto (auto-pintado para que el fade lo incluya)
        ml, mt, mr, mb = self._margins
        icon_y = (content_h - _NM_TOAST_ICON_SIZE) / 2
        p.drawPixmap(ml, int(icon_y), self._icon_pix)

        p.setFont(self._font)
        p.setPen(QPen(self._text_color))
        opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        text_x = ml + _NM_TOAST_ICON_SIZE + _NM_TOAST_GAP
        p.drawText(
            QRectF(text_x, mt, w - text_x - mr, content_h - mt - mb),
            self._message,
            opt,
        )
        p.end()

    def _set_progress(self, value):
        progress = max(0.0, min(1.0, float(value)))
        self._opacity = progress
        self._slide_offset = (1.0 - progress) * _NM_TOAST_SLIDE_PX
        self._reposition()
        self.update()

    def show_toast(self):
        if self._host is None:
            return
        self._replace_previous()
        self._host.installEventFilter(self)
        self._reposition()
        super().show()  # QWidget.show() — evita recursión con classmethod show()
        self.raise_()
        self._announce()

        # Fade + slide in (painter opacity — sin QGraphicsOpacityEffect)
        anim_in = QVariantAnimation(self)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.valueChanged.connect(self._set_progress)
        anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        # Auto-dismiss
        QTimer.singleShot(
            self._duration,
            lambda: self._dismiss() if not sip.isdeleted(self) else None,
        )

    def eventFilter(self, obj, event):
        if obj is self._host and event.type() == QEvent.Type.Resize:
            self._reposition()
        return False

    def _replace_previous(self):
        prev = NMToast._active_by_host.get(id(self._host))
        if prev is not None and prev is not self and not sip.isdeleted(prev):
            prev._cleanup()
        NMToast._active_by_host[id(self._host)] = self

    def _announce(self):
        # Al no ser ya una ventana, el lector de pantalla no lo anuncia solo:
        # anuncio explícito (Qt >= 6.8; silencioso si no está disponible).
        try:
            from PyQt6.QtGui import QAccessible, QAccessibleAnnouncementEvent

            QAccessible.updateAccessibility(QAccessibleAnnouncementEvent(self, self._message))
        except Exception:
            pass

    def _dismiss(self):
        anim_out = QVariantAnimation(self)
        anim_out.setDuration(200)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        anim_out.valueChanged.connect(self._set_progress)
        anim_out.finished.connect(self._cleanup)
        anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _cleanup(self):
        if sip.isdeleted(self):
            return
        if self._host is not None and not sip.isdeleted(self._host):
            self._host.removeEventFilter(self)
            if NMToast._active_by_host.get(id(self._host)) is self:
                NMToast._active_by_host.pop(id(self._host), None)
        self.hide()
        self.deleteLater()

    def _reposition(self):
        if self._host is None or sip.isdeleted(self._host):
            return
        margin = _NM_TOAST_BOTTOM_MARGIN
        self.adjustSize()
        x = (self._host.width() - self.width()) // 2
        y = self._host.height() - self.height() - margin + int(self._slide_offset)
        self.move(max(0, x), max(0, y))

    @classmethod
    def display(
        cls,
        parent_window: QWidget,
        message: str,
        variant: str = "info",
        duration_ms: int = _NM_TOAST_DEFAULT_DURATION,
    ):
        """Factory: crea y muestra un toast de una línea. None-safe: sin
        ventana host no se muestra nada (nunca un top-level)."""
        if parent_window is None:
            return None
        toast = cls(parent_window, message, variant, duration_ms)
        toast.show_toast()
        return toast


class NMWaveChart(QWidget):
    """Gráfico de área dual-serie para el módulo Ánimo.

    Serie teal = principal. Serie secundaria configurable por token
    (`secondary_color_key`, default violet p/ "semana anterior"; el módulo
    Ánimo la usa en danger para la serie NEGATIVA, en paralelo a la positiva).
    `series_labels=(lbl1, lbl2)` pinta una leyenda discreta arriba a la derecha.
    Emite week_changed(int) con offset de semana (0=actual, -1=anterior…).
    """

    week_changed = pyqtSignal(int)

    def __init__(
        self,
        modo: str = None,
        parent=None,
        secondary_color_key: str = "violet",
        series_labels: tuple[str, str] | None = None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._data_current: list[float | None] = [None] * 7
        self._data_previous: list[float | None] = [None] * 7
        self._secondary_color_key = secondary_color_key
        self._series_labels = series_labels
        self._week_offset = 0
        self._hover_idx = -1
        self._labels = ["L", "M", "M", "J", "V", "S", "D"]

        self.setMinimumHeight(140)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_data(self, current: list, previous: list):
        self._data_current = list(current[:7])
        self._data_previous = list(previous[:7])
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        n = len(self._data_current)
        if n < 2:
            return
        ml, mr = 32, 16
        step = (self.width() - ml - mr) / max(1, n - 1)
        idx = round((event.pos().x() - ml) / step)
        idx = max(0, min(n - 1, idx))
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        colors(self._modo)
        ml, mr = 32, 16
        # mt ampliado: la leyenda (●Positivo ●Negativo) y el label "10" del eje
        # vivían pegados al borde superior (y≈1) y se cortaban. Con una banda
        # propia arriba del gridline ya no se recortan. Aplica a todos los usos
        # del chart (pos/neg en Ánimo, semana previa, etc.).
        mt, mb = 34, 28
        cw = w - ml - mr
        ch = h - mt - mb

        teal_hex = C("teal", self._modo)
        violet_hex = C(self._secondary_color_key, self._modo)

        # Faint grid — incluye la línea de base 0 (feedback user feedback: sin ella la
        # escala quedaba asimétrica respecto de 5 y 10).
        for row in range(0, 5):
            y_grid = mt + ch - (ch * row / 4)
            gc = QColor(v3c("border", self._modo).name())
            gc.setAlpha(35)
            p.setPen(QPen(gc, 1, Qt.PenStyle.DotLine))
            p.drawLine(ml, int(y_grid), w - mr, int(y_grid))

        def _pts(data):
            result = []
            n = len(data)
            for i, v in enumerate(data):
                if v is None:
                    continue
                x = ml + (i / max(1, n - 1)) * cw
                y = mt + ch - (v / 10.0) * ch
                result.append(QPointF(x, y))
            return result

        def _draw_area(pts, color_hex, alpha_fill=50, alpha_line=190):
            if len(pts) < 2:
                return
            bottom_y = mt + ch
            poly_pts = [QPointF(pts[0].x(), bottom_y)]
            poly_pts += pts
            poly_pts.append(QPointF(pts[-1].x(), bottom_y))
            poly = QPolygonF(poly_pts)
            path = QPainterPath()
            path.addPolygon(poly)
            fill_grad = QLinearGradient(0, mt, 0, mt + ch)
            fc = QColor(color_hex)
            fc.setAlpha(alpha_fill)
            ec = QColor(color_hex)
            ec.setAlpha(0)
            fill_grad.setColorAt(0.0, fc)
            fill_grad.setColorAt(1.0, ec)
            p.fillPath(path, QBrush(fill_grad))
            lc = QColor(color_hex)
            lc.setAlpha(alpha_line)
            p.setPen(QPen(lc, 2.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            line_path = QPainterPath()
            line_path.moveTo(pts[0])
            for pt in pts[1:]:
                line_path.lineTo(pt)
            p.drawPath(line_path)

        is_dark = "dark" in self._modo
        # Con leyenda (modo pos/neg) la serie secundaria se dibuja con más
        # presencia: es un dato en paralelo, no un eco de la semana anterior.
        sec_alpha_line = 170 if self._series_labels else 90
        sec_alpha_fill = (38 if is_dark else 30) if self._series_labels else (31 if is_dark else 26)
        prev_pts = _pts(self._data_previous)
        _draw_area(prev_pts, violet_hex, alpha_fill=sec_alpha_fill, alpha_line=sec_alpha_line)

        curr_pts = _pts(self._data_current)
        _draw_area(curr_pts, teal_hex, alpha_fill=64 if is_dark else 46, alpha_line=210)

        # Dots — ambas series cuando hay leyenda (pos/neg en paralelo)
        if self._series_labels:
            p.setBrush(QBrush(QColor(violet_hex)))
            p.setPen(Qt.PenStyle.NoPen)
            for pt in prev_pts:
                p.drawEllipse(pt, 3, 3)
        p.setBrush(QBrush(QColor(teal_hex)))
        p.setPen(Qt.PenStyle.NoPen)
        for i, pt in enumerate(curr_pts):
            r = 5 if i == self._hover_idx else 3
            p.drawEllipse(pt, r, r)

        # Leyenda discreta arriba a la derecha: ● lbl1  ● lbl2
        if self._series_labels:
            p.setFont(qfont("size_caption_xs"))
            fm = p.fontMetrics()
            lbl1, lbl2 = self._series_labels
            seg_gap, dot_r = 10, 3
            x_cursor = w - mr
            for text, hexc in ((lbl2, violet_hex), (lbl1, teal_hex)):
                tw_lbl = fm.horizontalAdvance(text)
                x_cursor -= tw_lbl
                p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
                p.drawText(
                    QRectF(x_cursor, 6, tw_lbl, 14),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    text,
                )
                x_cursor -= dot_r * 2 + 4
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(hexc)))
                p.drawEllipse(QPointF(x_cursor + dot_r, 13), dot_r, dot_r)
                x_cursor -= seg_gap

        # Hover tooltip
        if 0 <= self._hover_idx < len(self._data_current):
            val = self._data_current[self._hover_idx]
            if val is not None:
                n_cur = len(self._data_current)
                pt = QPointF(
                    ml + (self._hover_idx / max(1, n_cur - 1)) * cw,
                    mt + ch - (val / 10.0) * ch,
                )
                is_today = self._hover_idx == len(self._data_current) - 1
                tip_text = f"Hoy: {val:.0f}" if is_today else f"{val:.0f}/10"
                tw, th = 60, 22
                tx = min(pt.x() - tw / 2, w - mr - tw)
                ty = max(float(mt), pt.y() - th - 8)
                tip_bg = QColor(v3c("elevated", self._modo).name())
                tip_bg.setAlpha(220)
                tip_r = QRectF(tx, ty, tw, th)
                tip_path = QPainterPath()
                tip_path.addRoundedRect(tip_r, RADIUS_SMALL, RADIUS_SMALL)
                p.fillPath(tip_path, tip_bg)
                p.setPen(QColor(v3c("text", self._modo).name()))
                p.setFont(qfont("size_small"))
                p.drawText(tip_r, Qt.AlignmentFlag.AlignCenter, tip_text)

        # Y-axis labels — escala completa 10/5/0 (feedback user feedback: sin el
        # 0 la escala quedaba coja en todos los diagramas).
        p.setFont(qfont("size_caption_xs"))
        p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
        for y_val in (10, 5, 0):
            y_pos = mt + ch - (y_val / 10.0) * ch
            p.drawText(
                QRectF(0, y_pos - 7, ml - 4, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(y_val),
            )

        # Day labels
        p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
        p.setFont(qfont("size_caption"))
        n = len(self._labels)
        for i, lbl in enumerate(self._labels):
            x = ml + (i / max(1, n - 1)) * cw
            p.drawText(QRectF(x - 12, h - mb + 4, 24, 14), Qt.AlignmentFlag.AlignCenter, lbl)

        p.restore()
        p.end()


_NM_STEPPER_MAX_WIDTH = 620
_NM_STEPPER_LINE_INSET = 0.08
_NM_STEPPER_LINE_Y = 9.0
_NM_STEPPER_LINE_HEIGHT = 2.0
_NM_STEPPER_DOT_SIZE = 18
_NM_STEPPER_DOT_RADIUS = _NM_STEPPER_DOT_SIZE / 2
_NM_STEPPER_LABEL_GAP = 8


class NMStepper(QWidget):
    """Stepper horizontal del mockup: línea brand, dots de 18px y labels de 12px."""

    def __init__(self, steps: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._steps = steps
        self._current = 0
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_step(self, idx: int):
        if not self._steps:
            self._current = 0
            self.update()
            return
        self._current = max(0, min(len(self._steps) - 1, idx))
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        n = len(self._steps)
        if n == 0:
            p.restore()
            p.end()
            return

        w = float(self.width())
        inner_w = min(w, float(_NM_STEPPER_MAX_WIDTH))
        inner_left = (w - inner_w) / 2
        line_left = inner_left + inner_w * _NM_STEPPER_LINE_INSET
        line_right = inner_left + inner_w * (1 - _NM_STEPPER_LINE_INSET)
        cy = _NM_STEPPER_LINE_Y

        if n > 1 and line_right > line_left:
            track_pen = QPen(v3c("line", self._modo), _NM_STEPPER_LINE_HEIGHT)
            track_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(track_pen)
            p.drawLine(QPointF(line_left, cy), QPointF(line_right, cy))

            fill_t = self._current / max(1, n - 1)
            fill_right = line_left + (line_right - line_left) * fill_t
            fill_pen = QPen(v3c("primary", self._modo), _NM_STEPPER_LINE_HEIGHT)
            fill_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(fill_pen)
            p.drawLine(QPointF(line_left, cy), QPointF(fill_right, cy))

        step_w = inner_w / n

        for i, label in enumerate(self._steps):
            if n == 1:
                cx = inner_left + inner_w / 2
            else:
                cx = line_left + (i / (n - 1)) * (line_right - line_left)

            # Circle / Dot
            if i <= self._current:
                p.setBrush(QBrush(v3c("primary", self._modo)))
                p.setPen(QPen(v3c("primary", self._modo), 2))
            else:
                p.setBrush(QBrush(v3c("surface3", self._modo)))
                p.setPen(QPen(v3c("line", self._modo), 2))
            dot_rect = QRectF(
                cx - _NM_STEPPER_DOT_RADIUS,
                cy - _NM_STEPPER_DOT_RADIUS,
                _NM_STEPPER_DOT_SIZE,
                _NM_STEPPER_DOT_SIZE,
            )
            p.drawEllipse(dot_rect)

            # Label below dot — elidido a su columna: un paso largo (texto
            # configurable desde el Hub) colisionaba con los vecinos.
            col_txt = (
                v3c("text", self._modo) if i == self._current else v3c("text3", self._modo)
            )
            p.setPen(col_txt)
            _f = qfont("size_caption", weight=600 if i == self._current else 500)
            p.setFont(_f)
            _fm = QFontMetrics(_f)
            _elided = _fm.elidedText(label, Qt.TextElideMode.ElideRight, int(step_w - 8))
            label_x = max(inner_left, cx - step_w / 2)
            if label_x + step_w > inner_left + inner_w:
                label_x = inner_left + inner_w - step_w
            p.drawText(
                QRectF(
                    label_x + 4,
                    cy + _NM_STEPPER_DOT_RADIUS + _NM_STEPPER_LABEL_GAP,
                    step_w - 8,
                    20,
                ),
                Qt.AlignmentFlag.AlignCenter,
                _elided,
            )

        p.restore()
        p.end()


class NMHeatBar(QWidget):
    """Barra de intensidad con gradiente dinámico frío→tibio→caliente.

    Arrastrar o hacer click mueve el indicador.
    Emite value_changed(int) con valor 0-100.
    """

    value_changed = pyqtSignal(int)

    def __init__(self, value: int = 50, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._value = max(0, min(100, value))
        self._dragging = False
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    @property
    def value(self) -> int:
        return self._value

    def set_value(self, v: int):
        self._value = max(0, min(100, v))
        self.update()

    def _ramp(self) -> tuple[str, str, str]:
        """Rampa frío→tibio→caliente desde TOKENS por modo (runtime: los hex
        web genéricos #3b82f6/#8b5cf6/#ef4444 estaban fuera de la paleta)."""
        cold = C("tcc_heat_cold", self._modo)
        hot = C("tcc_heat_hot", self._modo)
        return cold, blend_color(cold, hot, 0.5), hot

    def _color_at(self, t: float) -> QColor:
        cold, mid, hot = self._ramp()
        if t <= 0.5:
            return QColor(interpolate_color(cold, mid, t * 2))
        return QColor(interpolate_color(mid, hot, (t - 0.5) * 2))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._update_from_x(event.pos().x())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self._update_from_x(event.pos().x())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        super().mouseReleaseEvent(event)

    def _update_from_x(self, x: int):
        margin = 16
        usable = self.width() - margin * 2
        t = max(0.0, min(1.0, (x - margin) / usable))
        new_v = int(t * 100)
        if new_v != self._value:
            self._value = new_v
            self.update()
            self.value_changed.emit(self._value)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        margin = 16
        gh = 8
        gy = (h - gh) // 2
        gw = w - margin * 2

        groove_rect = QRectF(margin, gy, gw, gh)
        cold, mid, hot = self._ramp()
        grad = QLinearGradient(margin, 0, margin + gw, 0)
        grad.setColorAt(0.0, QColor(cold))
        grad.setColorAt(0.5, QColor(mid))
        grad.setColorAt(1.0, QColor(hot))
        path = QPainterPath()
        path.addRoundedRect(groove_rect, gh / 2, gh / 2)
        p.fillPath(path, grad)

        t = self._value / 100.0
        hx = margin + t * gw
        hc = self._color_at(t)
        p.setPen(QPen(QColor(C("text_on_accent", self._modo)), 2))
        p.setBrush(QBrush(hc))
        p.drawEllipse(QPointF(hx, gy + gh / 2), 10, 10)

        # El valor vive en el QLabel "Intensidad: N/10" (accesible al lector de
        # pantalla y en la misma escala /10). El antiguo caption "N%" pintado acá
        # era texto no accesible y en otra escala → contradicción de la auditoría.

        p.restore()
        p.end()
