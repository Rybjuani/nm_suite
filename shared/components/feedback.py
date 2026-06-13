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
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QLinearGradient,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
    QTextOption,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget

from shared.theme_manager import ThemeManager
from shared.theme_qt import ANIM, C, colors, norm_modo, qfont, v3c


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
        self, parent_window: QWidget, message: str, variant: str = "info", duration_ms: int = 2500
    ):
        host = parent_window.window() if parent_window is not None else None
        super().__init__(host)
        self._host = host
        self._variant = variant
        self._message = message
        self._duration = duration_ms
        self._opacity = 0.0
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
        self._font = qfont("size_body")
        self._text_color = v3c("text", self._modo)
        # Margen izquierdo ampliado para no solapar la barra de acento (4 px)
        self._margins = (18, 12, 16, 12)
        ml, mt, mr, mb = self._margins
        fm = QFontMetrics(self._font)
        avail = 360 - ml - mr
        text_rect = fm.boundingRect(
            QRect(0, 0, avail, 1000), int(Qt.TextFlag.TextWordWrap), self._message
        )
        w = max(260, min(360, text_rect.width() + ml + mr))
        h = text_rect.height() + mt + mb
        self.setFixedSize(w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setOpacity(self._opacity)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        r = 12.0
        accent = QColor(self._color)

        # Fondo y wash adaptativos al tema. Superficie 100% OPACA en ambos
        # temas (feedback user feedback: cualquier traslucidez se lee "barata" y
        # el aviso se confunde con el fondo); el color queda en la barra de
        # acento + wash mínimo.
        is_dark = "dark" in self._modo
        wash = QColor(accent)
        wash.setAlpha(12 if is_dark else 18)
        if is_dark:
            base_bg = QColor(v3c("surfaceSolid", self._modo))
        else:
            base_bg = QColor(v3c("surface", self._modo))
        base_bg.setAlpha(255)
        # El wash va ENCIMA del fondo opaco, nunca en su lugar: si el gradiente
        # arranca en el wash solo (alpha ~12), el borde izquierdo del toast
        # queda translúcido y se ve el contenido de atrás (feedback user feedback).
        wash_grad = QLinearGradient(0, 0, w, 0)
        wash_grad.setColorAt(0.0, wash)
        wash_transparent = QColor(wash)
        wash_transparent.setAlpha(0)
        wash_grad.setColorAt(0.40, wash_transparent)

        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setClipPath(clip)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(base_bg))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setBrush(QBrush(wash_grad))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # Barra de acento izquierda — 4 px, color sólido
        p.setBrush(QBrush(accent))
        p.drawRect(QRectF(0, 0, 4, h))

        p.setClipping(False)

        # Borde perimetral sutil en ambos temas (paridad dark/light) — apenas
        # más firme que el de las cards para que el aviso se distinga del
        # fondo sin recurrir a sombras.
        border_c = QColor(accent)
        border_c.setAlpha(95)
        p.setPen(QPen(border_c, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), r, r)

        # Texto (auto-pintado para que el fade lo incluya)
        ml, mt, mr, mb = self._margins
        p.setFont(self._font)
        p.setPen(QPen(self._text_color))
        opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        p.drawText(QRectF(ml, mt, w - ml - mr, h - mt - mb), self._message, opt)
        p.end()

    def _set_opacity(self, value):
        self._opacity = float(value)
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

        # Fade in (painter opacity — sin QGraphicsOpacityEffect)
        anim_in = QVariantAnimation(self)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.valueChanged.connect(self._set_opacity)
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
        anim_out.valueChanged.connect(self._set_opacity)
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
        margin = 20
        self.adjustSize()
        x = self._host.width() - self.width() - margin
        y = self._host.height() - self.height() - margin
        self.move(max(0, x), max(0, y))

    @classmethod
    def display(
        cls, parent_window: QWidget, message: str, variant: str = "info", duration_ms: int = 2500
    ):
        """Factory: crea y muestra un toast de una línea. None-safe: sin
        ventana host no se muestra nada (nunca un top-level)."""
        if parent_window is None:
            return None
        toast = cls(parent_window, message, variant, duration_ms)
        toast.show_toast()
        return toast
