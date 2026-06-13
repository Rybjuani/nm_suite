"""Feedback components shared by Suite and Hub."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QRect,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QTextOption,
)
from PyQt6.QtWidgets import QWidget

from shared.theme_manager import ThemeManager
from shared.theme_qt import norm_modo, qfont, v3c


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
