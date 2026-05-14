"""
shared/components_qt.py
Biblioteca de componentes UI PyQt6 para NeuroMood V3.

Cada componente implementa apply_theme(modo) y se conecta
automáticamente al singleton ThemeManager al instanciarse.

NO importa CustomTkinter. Compatible con contexto frozen.
"""

import sys
import os

from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QRectF,
    QPointF, QSize, pyqtSignal, pyqtProperty, QObject, QRect,
    QParallelAnimationGroup, QSequentialAnimationGroup,
    QVariantAnimation, QAbstractAnimation,
)
from PyQt6 import sip
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QPainterPath,
    QFontMetrics, QPixmap, QPaintEvent, QMouseEvent,
    QResizeEvent, QEnterEvent,
)
from PyQt6.QtWidgets import (
    QWidget, QFrame, QPushButton, QLineEdit, QLabel,
    QHBoxLayout, QVBoxLayout, QStackedWidget, QAbstractButton,
    QSizePolicy, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QApplication,
)

try:
    from shared.theme_qt import (
        qcolor, qfont, shadow_effect, linear_gradient, rich_gradient,
        linear_gradient_vertical, radial_glow, noise_overlay, gradient_colors,
        C, colors, norm_modo, interpolate_color, label_style,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_INPUT, RADIUS_PILL,
        PAD_CONTAINER, PAD_CARD, GAP_CARDS, GAP_ELEMENTS, HEADER_H,
        stylesheet_lineedit, aplicar_captionbar_qt,
        obtener_ruta_recurso, recolorear_logo_light,
    )
    from shared.theme import TYPOGRAPHY, LAYOUT, CATEGORY_COLORS, get_gradient
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme_qt import (
        qcolor, qfont, shadow_effect, linear_gradient, rich_gradient,
        linear_gradient_vertical, radial_glow, noise_overlay, gradient_colors,
        C, colors, norm_modo, interpolate_color, label_style,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_INPUT, RADIUS_PILL,
        PAD_CONTAINER, PAD_CARD, GAP_CARDS, GAP_ELEMENTS, HEADER_H,
        stylesheet_lineedit, aplicar_captionbar_qt,
        obtener_ruta_recurso, recolorear_logo_light,
    )
    from theme import TYPOGRAPHY, LAYOUT, CATEGORY_COLORS, get_gradient


# ── ThemeManager singleton ────────────────────────────────────────────────────

class ThemeManager(QObject):
    """
    Singleton que propaga cambios de tema a todos los componentes registrados.

    Uso:
        ThemeManager.instance().switch_mode("light_hybrid")
        # En cualquier widget:
        ThemeManager.instance().theme_changed.connect(self._apply_theme)
    """
    theme_changed = pyqtSignal(str)   # emite el nuevo modo

    _inst = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"

    @property
    def modo(self) -> str:
        return self._modo

    def switch_mode(self, new_modo: str):
        new_modo = norm_modo(new_modo)
        if new_modo == self._modo:
            return
        self._modo = new_modo
        for widget in QApplication.topLevelWidgets():
            widget.update()
        QTimer.singleShot(100, lambda m=new_modo: self.theme_changed.emit(m))


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


# ── NMCard ────────────────────────────────────────────────────────────────────

class NMCard(QFrame):
    """
    Card con sombra real, hover animado, borde izquierdo de color accent
    y efecto de escala al hacer click.
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None, accent_color: str = None,
                 clickable: bool = True, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._accent = accent_color or C("accent", self._modo)
        self._clickable = clickable
        self._hover = False

        self.setObjectName("NMCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._setup_shadow()
        self.setCursor(Qt.CursorShape.PointingHandCursor if clickable
                       else Qt.CursorShape.ArrowCursor)

        _tm().theme_changed.connect(self._apply_theme)

    def _setup_shadow(self):
        self._shadow = shadow_effect("card", self._modo, self)
        self.setGraphicsEffect(self._shadow)

    # ── hover ─────────────────────────────────────────────────────────────────

    def enterEvent(self, event: QEnterEvent):
        self._hover = True
        self._anim_shadow(blur=42, offset=14)
        if self._shadow:
            col = QColor(self._accent)
            col.setAlpha(35)
            self._shadow.setColor(col)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._anim_shadow(blur=28, offset=8)
        if self._shadow:
            self._shadow.setColor(QColor(0, 0, 0, 115))
        super().leaveEvent(event)

    def _anim_shadow(self, blur: float, offset: float):
        if not self._shadow:
            return
        # blur
        a1 = QPropertyAnimation(self._shadow, b"blurRadius", self)
        a1.setDuration(200)
        a1.setEasingCurve(QEasingCurve.Type.OutCubic)
        a1.setEndValue(blur)
        a1.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        # offset Y
        a2 = QPropertyAnimation(self._shadow, b"yOffset", self)
        a2.setDuration(200)
        a2.setEasingCurve(QEasingCurve.Type.OutCubic)
        a2.setEndValue(offset)
        a2.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── click scale ───────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self._scale_anim(0.97)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self._scale_anim(1.0)
            if self.rect().contains(event.pos()):
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _scale_anim(self, target: float):
        if target < 1.0:
            self._orig_geom = self.geometry()
            shrink = 3
            end_geom = self._orig_geom.adjusted(shrink, shrink, -shrink, -shrink)
        else:
            end_geom = getattr(self, "_orig_geom", self.geometry())
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(100)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setEndValue(end_geom)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── paintEvent: barra izquierda de color ──────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = RADIUS_CARD
        bar_w = 5

        # Fondo
        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), r, r)
        p.fillPath(bg_path, QBrush(QColor(c["bg_surface"])))

        bar_rect = QRectF(0, 0, bar_w, self.height())
        bar_grad = linear_gradient_vertical(
            bar_rect,
            QColor(self._accent),
            QColor(C("violet", self._modo)),
        )

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, bar_w, self.height()), r // 2, r // 2)
        p.fillPath(path, QBrush(bar_grad))

        c = colors(self._modo)
        border_col = QColor(c.get("border_card", c["border"]))
        border_col.setAlpha(60)
        p.setPen(QPen(border_col, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), r, r)

        noise_overlay(
            p,
            QRectF(bar_w, 0, self.width() - bar_w, self.height()),
            opacity=0.025,
            modo=self._modo,
        )

        if not self.isEnabled():
            p.setOpacity(0.4)
            pen = QPen(QColor(255, 255, 255, 15), 1)
            p.setPen(pen)
            for i in range(0, self.width() + self.height(), 8):
                p.drawLine(i, 0, 0, i)
            p.setOpacity(1.0)
        p.end()

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        if not self._accent or self._accent == C("accent", "dark_hybrid"):
            self._accent = C("accent", self._modo)
        old = self._shadow
        if old is not None:
            old.deleteLater()
        self._shadow = shadow_effect("card", self._modo, self)
        self.setGraphicsEffect(self._shadow)
        self.update()

    def set_accent(self, hex_color: str):
        self._accent = hex_color
        self.update()


# ── NMButton ──────────────────────────────────────────────────────────────────

class NMButton(QPushButton):
    """
    Botón con gradiente lineal teal→violet pintado en paintEvent.
    Hover: gradiente más brillante. Press: ligera escala visual.
    """

    def __init__(self, text: str = "", parent=None, modo: str = None,
                 width: int = 180, height: int = 44):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._hover = False
        self._pressed = False
        self._opacity = 1.0
        self._ripples = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.setInterval(16)
        self._ripple_timer.timeout.connect(self._tick_ripples)

        self.setFixedHeight(height)
        if width:
            self.setMinimumWidth(width)
        self.setFont(qfont("size_body", bold=True))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        # Sin stylesheet en el botón — todo en paintEvent
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        _tm().theme_changed.connect(self._apply_theme)

    def _tick_ripples(self):
        alive = []
        for rip in self._ripples:
            rip["r"] += 8
            rip["a"] = max(0, rip["a"] - 12)
            if rip["a"] > 0:
                alive.append(rip)
        self._ripples = alive
        if not alive:
            self._ripple_timer.stop()
        self.update()

    # ── paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = RADIUS_BUTTON
        rect = QRectF(self.rect())

        # Gradiente
        grad = rich_gradient(rect, self._modo)
        if self._hover and not self._pressed:
            for color_hex, pos in get_gradient(self._modo):
                c = QColor(color_hex)
                c.setAlpha(220)
                grad.setColorAt(pos, c)
        if self._pressed:
            for color_hex, pos in get_gradient(self._modo):
                dark = interpolate_color(color_hex, "#000000", 0.15)
                grad.setColorAt(pos, QColor(dark))

        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        if not self.isEnabled():
            p.setOpacity(0.4)

        p.fillPath(path, QBrush(grad))

        # Texto
        c = colors(self._modo)
        text_color = QColor(c["text_on_accent"])
        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, self.text())

        for rip in self._ripples:
            rip_col = QColor(255, 255, 255, rip["a"])
            p.setBrush(QBrush(rip_col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(rip["center"], rip["r"], rip["r"])
        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position() if hasattr(event, "position") else QPointF(event.pos())
            self._ripples.append({"center": pos, "r": 0, "a": 80})
            self._ripple_timer.start()
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMButtonOutline ───────────────────────────────────────────────────────────

class NMButtonOutline(QPushButton):
    """Botón con borde 2px accent, fondo transparente. Hover: fill 15% accent."""

    def __init__(self, text: str = "", parent=None, modo: str = None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._hover = False
        self._active = False   # para pills toggleables (días de semana, etc.)

        self.setFont(qfont("size_small", bold=False))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setMinimumHeight(34)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        _tm().theme_changed.connect(self._apply_theme)

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def is_active(self) -> bool:
        return self._active

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = colors(self._modo)
        accent = QColor(C("accent", self._modo))
        r = RADIUS_BUTTON
        rect = QRectF(self.rect())

        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(1, 1, -1, -1), r, r)

        if self._active:
            # Fondo accent sólido
            p.fillPath(path, QBrush(accent))
            text_color = QColor(c["text_on_accent"])
            pen_color = accent
        elif self._hover:
            # Fill 15%
            fill = QColor(accent)
            fill.setAlpha(38)   # 15% de 255
            p.fillPath(path, QBrush(fill))
            text_color = QColor(c["text_primary"])
            pen_color = accent
        else:
            p.fillPath(path, QBrush(QColor(0, 0, 0, 0)))
            text_color = QColor(c["text_secondary"])
            pen_color = accent

        # Borde
        if not self._active:
            pen = QPen(pen_color, 2)
            p.setPen(pen)
            p.drawPath(path)

        # Texto
        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = not self._active
            self.update()
        super().mousePressEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMInput ───────────────────────────────────────────────────────────────────

class NMInput(QLineEdit):
    """
    QLineEdit estilizado. Focus anima el color del borde border→border_focus en 200ms.
    """

    def __init__(self, placeholder: str = "", parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setPlaceholderText(placeholder)
        self.setFont(qfont("size_body"))
        self.setMinimumHeight(LAYOUT["min_touch_target"])
        self._apply_base_style()

        _tm().theme_changed.connect(self._apply_theme)

    def _apply_base_style(self):
        c = colors(self._modo)
        r = RADIUS_INPUT
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c.get('border_card', c['border'])};
                border-radius: {r}px;
                padding: 0 12px;
                font-size: {TYPOGRAPHY['size_body']}pt;
                selection-background-color: {c['accent']};
                selection-color: {c['text_on_accent']};
            }}
            QLineEdit:focus {{
                border: 2px solid {c['border_focus']};
            }}
        """)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_base_style()


# ── NMProgressBar ─────────────────────────────────────────────────────────────

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
        self._shimmer_pos = 0.0
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(16)
        self._shimmer_timer.timeout.connect(self._tick_shimmer)
        self._shimmer_timer.start()
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _tm().theme_changed.connect(self._apply_theme)

    def _tick_shimmer(self):
        self._shimmer_pos = (self._shimmer_pos + 0.015) % 1.2
        self.update()

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

        # Fill gradiente
        fill_w = w * self._value
        if fill_w > 0:
            fill_rect = QRectF(0, 0, fill_w, h)
            grad = linear_gradient(fill_rect, self._modo, angle=0)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(fill_rect, r, r)

            if fill_w > 4:
                shimmer_x = (self._shimmer_pos - 0.2) * fill_w
                shimmer_w = fill_w * 0.3
                sh_grad = QLinearGradient(shimmer_x, 0, shimmer_x + shimmer_w, 0)
                sh_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
                sh_grad.setColorAt(0.5, QColor(255, 255, 255, 45))
                sh_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.setBrush(QBrush(sh_grad))
                p.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(fill_rect, r, r)
                p.setClipPath(clip_path)
                p.drawRoundedRect(QRectF(max(0, shimmer_x), 0, shimmer_w, h), r, r)
                p.restore()

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMToggle ──────────────────────────────────────────────────────────────────

class NMToggle(QAbstractButton):
    """
    Toggle switch custom: píldora redondeada con círculo deslizante.
    QPropertyAnimation sobre posición X del círculo en 200ms OutCubic.
    """

    def __init__(self, parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._track_w = 48
        self._track_h = 26
        self._thumb_r = 10
        self._thumb_x = float(self._thumb_r + 3)  # posición X animada

        self.setCheckable(True)
        self.setFixedSize(self._track_w, self._track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"thumb_x", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.toggled.connect(self._on_toggle)
        _tm().theme_changed.connect(self._apply_theme)

    # thumb_x como pyqtProperty
    def _get_thumb_x(self) -> float:
        return self._thumb_x

    def _set_thumb_x(self, x: float):
        self._thumb_x = x
        self.update()

    thumb_x = pyqtProperty(float, _get_thumb_x, _set_thumb_x)

    def _on_toggle(self, checked: bool):
        target = (self._track_w - self._thumb_r - 3) if checked else (self._thumb_r + 3)
        self._anim.stop()
        self._anim.setStartValue(self._thumb_x)
        self._anim.setEndValue(float(target))
        self._anim.start()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)

        r = self._track_h // 2
        track_rect = QRectF(0, 0, self._track_w, self._track_h)

        # Track
        track_color = QColor(C("accent", self._modo)) if self.isChecked() \
            else QColor(c["bg_elevated"])
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(track_rect, r, r)

        # Thumb
        ty = self._track_h / 2
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(QPointF(self._thumb_x, ty), self._thumb_r, self._thumb_r)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMToast ───────────────────────────────────────────────────────────────────

class NMToast(QWidget):
    """
    Notificación flotante en esquina inferior derecha. Slide + fade in/out.
    Variantes: 'success', 'error', 'info', 'warning'.
    Se muestra sobre todos los demás widgets (Qt.WindowType.ToolTip).
    """

    _VARIANT_COLORS = {
        "success": "#10b981",
        "error":   "#ef4444",
        "info":    "#6366f1",
        "warning": "#f59e0b",
    }

    def __init__(self, parent_window: QWidget, message: str,
                 variant: str = "info", duration_ms: int = 2500):
        super().__init__(parent_window, Qt.WindowType.ToolTip)
        self._parent_win = parent_window
        self._variant = variant
        self._message = message
        self._duration = duration_ms
        self._color = self._VARIANT_COLORS.get(variant, self._VARIANT_COLORS["info"])

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._setup_ui()
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Indicador de color
        dot = QWidget()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background: {self._color}; border-radius: 4px;"
        )
        layout.addWidget(dot)

        lbl = QLabel(self._message)
        lbl.setFont(qfont("size_body"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: white; background: transparent;")
        layout.addWidget(lbl)

        self.setStyleSheet(f"""
            NMToast {{
                background-color: rgba(30, 39, 64, 230);
                border-radius: 12px;
                border: 1px solid {self._color};
            }}
        """)
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)
        self.adjustSize()

    def show_toast(self):
        if not self._parent_win:
            return
        self._reposition()
        super().show()   # QWidget.show() — evita recursión con classmethod show()
        self.raise_()

        # Fade in
        anim_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        # Auto-dismiss
        QTimer.singleShot(self._duration, self._dismiss)

    def _dismiss(self):
        anim_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim_out.setDuration(200)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        anim_out.finished.connect(self.close)
        anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _reposition(self):
        pw = self._parent_win
        margin = 20
        x = pw.x() + pw.width() - self.width() - margin
        y = pw.y() + pw.height() - self.height() - margin - 60
        self.move(x, y)

    @classmethod
    def show(cls, parent_window: QWidget, message: str,
             variant: str = "info", duration_ms: int = 2500):
        """Factory: crea y muestra un toast de una línea."""
        toast = cls(parent_window, message, variant, duration_ms)
        toast.show_toast()
        return toast

    # Evitar que el método show() herede de QWidget (ya está en el classmethod)
    def _show_widget(self):
        super().show()


# ── NMSidebar ─────────────────────────────────────────────────────────────────

class _SidebarItem(QWidget):
    """Ítem individual del sidebar."""
    clicked = pyqtSignal(str)

    def __init__(self, item_id: str, icon: str, label: str,
                 parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._id = item_id
        self._icon = icon
        self._label = label
        self._modo = norm_modo(modo)
        self._active = False
        self._hover = False
        self._hover_alpha = 0.0
        self._bar_anim_val = 0.0   # 0.0→1.0 para la barra izquierda

        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._bar_anim = QPropertyAnimation(self, b"bar_val", self)
        self._bar_anim.setDuration(150)
        self._bar_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim = QPropertyAnimation(self, b"hover_alpha", self)
        self._hover_anim.setDuration(120)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_bar_val(self) -> float:
        return self._bar_anim_val

    def _set_bar_val(self, v: float):
        self._bar_anim_val = v
        self.update()

    bar_val = pyqtProperty(float, _get_bar_val, _set_bar_val)

    def _get_hover_alpha(self) -> float:
        return self._hover_alpha

    def _set_hover_alpha(self, v: float):
        self._hover_alpha = max(0.0, min(1.0, v))
        self.update()

    hover_alpha = pyqtProperty(float, _get_hover_alpha, _set_hover_alpha)

    def set_active(self, active: bool):
        self._active = active
        target = 1.0 if active else 0.0
        self._bar_anim.stop()
        self._bar_anim.setStartValue(self._bar_anim_val)
        self._bar_anim.setEndValue(target)
        self._bar_anim.start()

    def enterEvent(self, event):
        self._hover = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_alpha)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_alpha)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._id)
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        w, h = self.width(), self.height()
        r = RADIUS_BUTTON

        # Fondo hover/active
        if self._active:
            bg = QColor(c["bg_elevated"])
        elif self._hover:
            bg = QColor(c["bg_elevated"])
            bg.setAlpha(int(120 * self._hover_alpha))
        else:
            bg = QColor(0, 0, 0, 0)

        if bg.alpha() > 0:
            path = QPainterPath()
            path.addRoundedRect(QRectF(4, 2, w - 8, h - 4), r, r)
            p.fillPath(path, QBrush(bg))

        # Barra izquierda animada (3px)
        if self._bar_anim_val > 0:
            bar_h = int((h - 8) * self._bar_anim_val)
            bar_y = (h - bar_h) // 2
            bar_path = QPainterPath()
            bar_path.addRoundedRect(QRectF(0, bar_y, 3, bar_h), 2, 2)
            p.fillPath(bar_path, QBrush(QColor(C("accent", self._modo))))

        # Icono + texto
        text_color = QColor(c["text_primary"] if (self._active or self._hover)
                            else c["text_secondary"])
        p.setPen(QPen(text_color))

        font_icon = qfont("size_body")
        font_icon.setFamily("Segoe UI Emoji")
        p.setFont(font_icon)
        icon_rect = QRect(14, 0, 28, h)
        p.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, self._icon)

        font_label = qfont("size_small", bold=self._active)
        p.setFont(font_label)
        label_rect = QRect(44, 0, w - 48, h)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignVCenter, self._label)

        p.end()

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMSidebar(QWidget):
    """
    Sidebar de navegación de 200px. Emite nav_changed(str) al hacer click en un ítem.
    """
    nav_changed = pyqtSignal(str)

    def __init__(self, parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._items: dict[str, _SidebarItem] = {}
        self._active_id: str = ""
        self._theme_labels: list[tuple[QLabel, str]] = []
        self._logo_shadow: QGraphicsDropShadowEffect | None = None
        self._logo_lbl: QLabel | None = None

        self.setFixedWidth(200)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        c = colors(self._modo)
        p.fillRect(self.rect(), QColor(c["bg_secondary"]))
        p.end()
        super().paintEvent(event)

    def add_header(self, title: str, subtitle: str = ""):
        """Añade sección de título/logo al tope del sidebar."""
        c = colors(self._modo)
        w = QWidget()
        w.setObjectName("SidebarHeader")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 16, 16, 8)
        vl.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setFont(qfont("size_small", bold=True))
        lbl_title.setStyleSheet(label_style(self._modo, 'accent'))
        self._theme_labels.append((lbl_title, "accent"))
        vl.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setFont(qfont("size_caption"))
            lbl_sub.setStyleSheet(label_style(self._modo, 'text_tertiary'))
            self._theme_labels.append((lbl_sub, "text_tertiary"))
            vl.addWidget(lbl_sub)

        self._layout.addWidget(w)
        self._add_separator()

    def add_logo(self, logo_path: str = ""):
        """Inserta LOGO.png con sombra premium al tope del sidebar."""
        from PyQt6.QtGui import QPixmap

        w = QWidget()
        w.setObjectName("SidebarLogo")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 4)

        logo_lbl = QLabel()
        try:
            path = logo_path or obtener_ruta_recurso("LOGO.png")
            if os.path.exists(path):
                pm = QPixmap(path).scaled(
                    168, 36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                logo_lbl.setPixmap(pm)
            else:
                raise FileNotFoundError
        except Exception:
            logo_lbl.setText("NeuroMood")
            logo_lbl.setStyleSheet(label_style(self._modo, "accent"))
            logo_lbl.setFont(qfont("size_h3", bold=True))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        shadow = QGraphicsDropShadowEffect(logo_lbl)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 0)
        col = QColor(C("accent", self._modo))
        col.setAlpha(45)
        shadow.setColor(col)
        logo_lbl.setGraphicsEffect(shadow)
        self._logo_shadow = shadow
        self._logo_lbl = logo_lbl

        vl.addWidget(logo_lbl)
        self._layout.insertWidget(0, w)

    def add_item(self, item_id: str, icon: str, label: str):
        item = _SidebarItem(item_id, icon, label, self, self._modo)
        item.clicked.connect(self._on_item_clicked)
        self._items[item_id] = item
        self._layout.addWidget(item)

    def add_separator(self):
        self._add_separator()

    def _add_separator(self):
        sep = QWidget()
        sep.setFixedHeight(1)
        c = colors(self._modo)
        sep.setStyleSheet(f"background: {c.get('border_card', c['border'])};")
        self._layout.addWidget(sep)

    def add_spacer(self):
        from PyQt6.QtWidgets import QSpacerItem
        self._layout.addStretch()

    def add_label(self, text: str):
        c = colors(self._modo)
        lbl = QLabel(text)
        lbl.setFont(qfont("size_caption"))
        lbl.setWordWrap(True)
        lbl.setContentsMargins(14, 4, 14, 4)
        lbl.setStyleSheet(label_style(self._modo, 'text_tertiary'))
        self._theme_labels.append((lbl, "text_tertiary"))
        self._layout.addWidget(lbl)
        self._status_label = lbl

    def set_active(self, item_id: str):
        for iid, item in self._items.items():
            item.set_active(iid == item_id)
        self._active_id = item_id

    def _on_item_clicked(self, item_id: str):
        self.set_active(item_id)
        self.nav_changed.emit(item_id)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        for item in self._items.values():
            item.apply_theme(modo)
        c = colors(self._modo)
        # Actualizar labels temáticos y limpiar referencias muertas
        alive = []
        for lbl, color_key in self._theme_labels:
            if not sip.isdeleted(lbl):
                lbl.setStyleSheet(label_style(self._modo, color_key))
                alive.append((lbl, color_key))
        self._theme_labels = alive
        # Actualizar sombra del logo
        if self._logo_shadow is not None:
            col = QColor(C("accent", self._modo))
            col.setAlpha(45)
            self._logo_shadow.setColor(col)
        # Recolorear logo en light mode
        if self._logo_lbl is not None:
            try:
                path = obtener_ruta_recurso("LOGO.png")
                if os.path.exists(path):
                    pm = QPixmap(path)
                    if "light" in self._modo:
                        from PIL import Image as PILImage
                        img = PILImage.open(path).convert("RGBA")
                        img = recolorear_logo_light(img)
                        data = img.tobytes("raw", "RGBA")
                        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                        pm = QPixmap.fromImage(qimg)
                    self._logo_lbl.setPixmap(pm.scaled(
                        168, 36,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
            except Exception:
                pass
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and w.fixedHeight() == 1:
                w.setStyleSheet(f"background: {c.get('border_card', c['border'])};")


# ── NMHeader ──────────────────────────────────────────────────────────────────

class NMHeader(QWidget):
    """
    Header de 56px con logo NeuroMood (N teal + M violet), nombre de usuario
    y toggle dark/light. Emite theme_toggle() al hacer click en el toggle.
    """
    theme_toggle = pyqtSignal()

    def __init__(self, parent=None, modo: str = None,
                 username: str = "", show_back: bool = False,
                 module_title: str = "", module_icon: str = ""):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._username = username
        self._show_back = show_back
        self._module_title = module_title
        self._module_icon = module_icon

        self.setFixedHeight(HEADER_H)
        self._setup_ui()
        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        c = colors(self._modo)

        if self._show_back:
            # Módulo: botón back + icono + título
            self._btn_back = QPushButton("←")
            self._btn_back.setFont(qfont("size_h2"))
            self._btn_back.setFixedSize(40, 36)
            self._btn_back.setFlat(True)
            self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_back.setStyleSheet(
                f"color: {C('text_primary', self._modo)};"
                f"background: transparent;"
                f"border-radius: {RADIUS_BUTTON}px;"
            )
            layout.addWidget(self._btn_back)

            icon_lbl = QLabel(self._module_icon)
            icon_lbl.setFont(qfont("size_body"))
            self._module_icon_lbl = icon_lbl
            layout.addWidget(icon_lbl)

            title_lbl = QLabel(self._module_title)
            title_lbl.setFont(qfont("size_h3", bold=True))
            title_lbl.setStyleSheet(label_style(self._modo, 'text_primary'))
            self._module_title_lbl = title_lbl
            layout.addWidget(title_lbl)
        else:
            # Home: logo NeuroMood
            self._logo_widget = _LogoLabel(self)
            self._logo_widget.set_modo(self._modo)
            layout.addWidget(self._logo_widget)

            if self._username:
                user_lbl = QLabel(f"Hola, {self._username}")
                user_lbl.setFont(qfont("size_small"))
                user_lbl.setStyleSheet(label_style(self._modo, 'text_tertiary'))
                self._user_lbl = user_lbl
                layout.addWidget(user_lbl)

        layout.addStretch()

        # Toggle dark/light
        self._toggle = NMToggle(self, self._modo)
        self._toggle.setChecked("light" in self._modo)
        self._toggle.toggled.connect(lambda _: self.theme_toggle.emit())
        layout.addWidget(self._toggle)

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        c = colors(self._modo)
        p.fillRect(self.rect(), QColor(c["bg_secondary"]))
        p.setPen(QPen(QColor(c.get("border_card", c["border"])), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()
        super().paintEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        if hasattr(self, "_logo_widget"):
            self._logo_widget.set_modo(modo)
        if hasattr(self, "_user_lbl"):
            self._user_lbl.setStyleSheet(label_style(modo, 'text_tertiary'))
        if hasattr(self, "_btn_back"):
            self._btn_back.setStyleSheet(
                f"color: {C('text_primary', modo)};"
                f"background: transparent;"
                f"border-radius: {RADIUS_BUTTON}px;"
            )
        if hasattr(self, "_module_title_lbl"):
            self._module_title_lbl.setStyleSheet(label_style(modo, 'text_primary'))
        self._toggle._apply_theme(modo)
        self._toggle.setChecked("light" in modo)

    def _ensure_back_button(self):
        if hasattr(self, "_btn_back"):
            return self._btn_back
        btn = QPushButton("←", self)
        btn.setFont(qfont("size_h2"))
        btn.setFixedSize(40, 36)
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"color: {C('text_primary', self._modo)};"
            f"background: transparent;"
            f"border-radius: {RADIUS_BUTTON}px;"
        )
        layout = self.layout()
        if layout:
            layout.insertWidget(0, btn)
        self._btn_back = btn
        self._back_btn = btn
        return btn

    def set_back_action(self, callback=None):
        btn = self._ensure_back_button() if callback else getattr(self, "_btn_back", None)
        if not btn:
            return
        try:
            btn.clicked.disconnect()
        except TypeError:
            pass
        if callback:
            btn.clicked.connect(callback)
            btn.show()
        else:
            btn.hide()

    def set_back_callback(self, callback):
        self.set_back_action(callback)

    def set_title_info(self, title: str = "", icon: str = ""):
        if hasattr(self, "_module_title_lbl"):
            self._module_title_lbl.setText(title)
        if hasattr(self, "_module_icon_lbl"):
            self._module_icon_lbl.setText(icon)


class _LogoLabel(QWidget):
    """Logo NeuroMood desde assets/LOGO.png con glow animado + sombra premium."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "dark_hybrid"
        self._glow_alpha_value = 0
        self.setFixedHeight(32)
        self._pixmap = None
        self._load_logo()

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(14)
        self._shadow.setOffset(0, 0)
        col = QColor(C("accent", self._modo))
        col.setAlpha(50)
        self._shadow.setColor(col)
        self.setGraphicsEffect(self._shadow)

        self._breath_anim = QPropertyAnimation(self, b"glow_alpha", self)
        self._breath_anim.setDuration(3000)
        self._breath_anim.setStartValue(0)
        self._breath_anim.setEndValue(60)
        self._breath_anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._breath_anim.setLoopCount(-1)
        self._breath_anim.start()

    def _load_logo(self):
        try:
            logo_path = obtener_ruta_recurso("LOGO.png")
            if os.path.exists(logo_path):
                self._pixmap = QPixmap(logo_path)
                self._pixmap_light = None
        except Exception:
            self._pixmap = None
            self._pixmap_light = None

    def _get_pixmap(self):
        if self._pixmap is None:
            return None
        if "light" in self._modo:
            if self._pixmap_light is None:
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(obtener_ruta_recurso("LOGO.png")).convert("RGBA")
                    img = recolorear_logo_light(img)
                    data = img.tobytes("raw", "RGBA")
                    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                    self._pixmap_light = QPixmap.fromImage(qimg)
                except Exception:
                    return self._pixmap
            return self._pixmap_light
        return self._pixmap

    def _get_glow_alpha(self) -> int:
        return self._glow_alpha_value

    def _set_glow_alpha(self, value: int):
        self._glow_alpha_value = max(0, min(255, int(value)))
        self.update()

    glow_alpha = pyqtProperty(int, _get_glow_alpha, _set_glow_alpha)

    def set_modo(self, modo: str):
        self._modo = norm_modo(modo)
        col = QColor(C("accent", self._modo))
        col.setAlpha(50)
        self._shadow.setColor(col)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(140, 32)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self._pixmap and not self._pixmap.isNull():
            pm = self._get_pixmap()
            if pm and not pm.isNull():
                pm = pm.scaled(
                140, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - pm.width()) // 2
            y = (self.height() - pm.height()) // 2
            p.drawPixmap(x, y, pm)
        else:
            c = colors(self._modo)
            font_bold = qfont("size_body", bold=True)
            p.setFont(font_bold)
            fm = QFontMetrics(font_bold)
            p.setPen(QColor(c["text_primary"]))
            p.drawText(0, fm.ascent() + 4, "Neuro")
            w1 = fm.horizontalAdvance("Neuro")
            p.setPen(QColor(C("accent", self._modo)))
            p.drawText(w1, fm.ascent() + 4, "Mood")

        if self._glow_alpha_value > 0:
            glow = radial_glow(
                QPointF(self.width() / 2, self.height() / 2),
                max(self.width(), self.height()) * 0.7,
                C("accent", self._modo),
                alpha=self._glow_alpha_value,
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(
                QPointF(self.width() / 2, self.height() / 2),
                self.width() * 0.45,
                self.height() * 0.7,
            )
        p.end()


# ── NMFadeWidget ──────────────────────────────────────────────────────────────

class NMFadeWidget(QStackedWidget):
    """
    QStackedWidget con transición fade entre páginas.
    setCurrentWidget() override: fade-out/in en 200ms OutCubic.
    """

    def __init__(self, parent=None, duration: int = 200):
        super().__init__(parent)
        self._duration = duration
        self._animating = False
        self._snapshot: QLabel | None = None

    def setCurrentWidget(self, widget: QWidget):
        if widget is self.currentWidget():
            return
        if self._animating:
            return
        self._fade_to(widget)

    def _fade_to(self, target: QWidget):
        self._animating = True
        current = self.currentWidget()

        # Captura snapshot del widget actual
        if current:
            px = current.grab()
            snap = QLabel(self)
            snap.setPixmap(px)
            snap.setGeometry(0, 0, self.width(), self.height())
            snap.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            snap.show()
            snap.raise_()
            self._snapshot = snap

            # Fade out snapshot
            eff = QGraphicsOpacityEffect(snap)
            snap.setGraphicsEffect(eff)

            fade_out = QPropertyAnimation(eff, b"opacity", self)
            fade_out.setDuration(self._duration)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _on_out_done():
                snap.deleteLater()
                self._snapshot = None
                self._animating = False

            fade_out.finished.connect(_on_out_done)

            # Mostrar target mientras sale el snapshot
            super().setCurrentWidget(target)
            fade_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        else:
            super().setCurrentWidget(target)
            self._animating = False

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._snapshot:
            self._snapshot.setGeometry(0, 0, self.width(), self.height())


# ── NMModule (base class Qt) ──────────────────────────────────────────────────

class NMSkeleton(QWidget):
    """
    Rectangulo de carga animado con gradiente deslizante.
    Uso: skeleton = NMSkeleton(parent, width=200, height=16, radius=8)
    """

    def __init__(self, parent=None, width=200, height=16,
                 radius=8, modo=None):
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


class NMModule(QWidget):
    """
    Clase base para módulos de la plataforma paciente en PyQt6.
    Preserva exactamente el mismo contrato que la versión CTk:
      - MODULE_TITLE, MODULE_ICON
      - build_ui() → raise NotImplementedError
      - get_card_status() → str
      - on_enter(), on_leave() — hooks
    """
    MODULE_TITLE: str = ""
    MODULE_ICON: str = ""

    # Señal que los módulos emiten cuando quieren volver al home
    back_requested = pyqtSignal()

    def __init__(self, parent=None, modo: str = None, show_header: bool = True):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._show_header = show_header

        # Layout vertical: header + contenido
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        if self._show_header:
            self._header = NMHeader(
                self, modo=self._modo,
                show_back=True,
                module_title=self.MODULE_TITLE,
                module_icon=self.MODULE_ICON,
            )
            self._header.set_back_callback(self.back_requested.emit)
            self._root_layout.addWidget(self._header)

        # Contenido del modulo (build_ui lo llena) con centrado premium
        self._content = QWidget()
        self._content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._apply_content_bg()

        # Wrapper centrado para pantallas anchas (>1100px el contenido se centra)
        self._content_wrapper = QHBoxLayout()
        self._content_wrapper.setContentsMargins(0, 0, 0, 0)
        self._content_wrapper.addWidget(self._content)
        self._root_layout.addLayout(self._content_wrapper)

        _tm().theme_changed.connect(self._on_theme)
        self.build_ui()

    def _apply_content_bg(self):
        self._content.update()

    @property
    def modo(self) -> str:
        return self._modo

    def build_ui(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} debe implementar build_ui()"
        )

    def get_card_status(self) -> str:
        """Estado resumido del módulo para mostrar en la card del home."""
        return ""

    def on_enter(self):
        """Llamado cuando el módulo se hace visible (recargar datos frescos)."""
        pass

    def on_leave(self):
        """Llamado antes de que el módulo sea ocultado (detener timers, etc.)."""
        pass

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_content_bg()


def h_spacer() -> QWidget:
    """Spacer horizontal expandible."""
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return w
