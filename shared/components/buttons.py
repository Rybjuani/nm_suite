"""Button, input and tab control components shared by Suite and Hub."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QWidget,
)

from shared.theme_manager import ThemeManager
from shared.theme import LAYOUT, TYPOGRAPHY
from shared.theme_qt import (
    ANIM,
    C,
    EASE_OUT,
    V3_SP,
    blend_color,
    focus_ring_stylesheet,
    norm_modo,
    qcolor_to_rgba_css,
    qfont,
    v3c,
)


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


# Controles runtime: compacto/sobrio, sin variante grande por defecto.
_NM_CONTROL_HEIGHT = 42
_NM_CONTROL_COMPACT_HEIGHT = 34
_NM_CONTROL_RADIUS = LAYOUT["radius_input"]
_NM_CONTROL_PILL_RADIUS = _NM_CONTROL_HEIGHT // 2
_NM_CONTROL_FONT = "size_body"
# Texto de botones en negrita (semibold 600, el peso "fuerte" runtime del
# de-negritado): el user feedback pidió confirmar que TODOS los botones se lean en
# negrita; a 500 (medium) quedaban demasiado livianos.
_NM_CONTROL_WEIGHT = TYPOGRAPHY["weight_semibold"]
_NM_TAB_HEIGHT = 38
_NM_TAB_RADIUS = 19
_NM_TAB_FONT = "size_caption"
_NM_BUTTON_HEIGHT = {
    "sm": _NM_CONTROL_COMPACT_HEIGHT,
    "md": _NM_CONTROL_HEIGHT,
    "lg": _NM_CONTROL_HEIGHT,
}
_NM_BUTTON_FONT = {"sm": "size_caption", "md": _NM_CONTROL_FONT, "lg": _NM_CONTROL_FONT}
_NM_BUTTON_VARIANT_ALIASES = {
    "primary": "gradient",
    "filled": "gradient",
    "outline": "secondary",
    "destructive": "danger",
}


class NMButton(QPushButton):
    """
    Botón v3 — pill, 3 variantes (``gradient`` / ``secondary`` / ``ghost``),
    con ``lg`` normalizado a la escala media runtime para evitar gigantismo.

    Comportamiento:
      - Press: scale 0.97 por 100 ms (spec README v3 para botones).
      - Hover: variante ``gradient`` añade glow exterior teal; las otras
        cambian color de fondo y/o border.
      - Ripple blanco al click solo en variante ``gradient``.

    Args:
        text:    label
        parent:  QWidget parent
        modo:    override de tema; ``None`` = sigue ThemeManager
        width:   minWidth (compatibility, default 180)
        height:  fixedHeight; ``None`` = derivado de ``size``
        variant: ``"gradient"`` (primary teal→violet) | ``"secondary"``
                 (surface + border) | ``"ghost"`` (transparente)
        size:    ``"sm"`` / ``"md"`` / ``"lg"``
    """

    def __init__(
        self,
        text: str = "",
        parent=None,
        modo: str = None,
        width: int = 180,
        height: int | None = None,
        variant: str = "gradient",
        size: str = "md",
    ):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = _NM_BUTTON_VARIANT_ALIASES.get(variant, variant)
        if self._variant not in ("gradient", "secondary", "ghost", "danger"):
            self._variant = "gradient"
        self._size = size if size in ("sm", "md", "lg") else "md"
        self._hover = False
        self._pressed = False
        self._success_anim: QSequentialAnimationGroup | None = None
        self._scale_anim: QPropertyAnimation | None = None
        self._base_geom = None
        self._btn_shadow: QGraphicsDropShadowEffect | None = None

        self.setObjectName(f"NMButton_{self._variant}")
        eff_height = height if height is not None else _NM_BUTTON_HEIGHT[self._size]
        self.setFixedHeight(eff_height)
        if width:
            self.setMinimumWidth(width)
        self.setFont(qfont(_NM_BUTTON_FONT[self._size], weight=_NM_CONTROL_WEIGHT))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAccessibleName(text)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        self._apply_btn_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API v3 ────────────────────────────────────────────────────────────────

    def set_variant(self, variant: str):
        canonical = _NM_BUTTON_VARIANT_ALIASES.get(variant, variant)
        if canonical in ("gradient", "secondary", "ghost", "danger"):
            self._variant = canonical
            self.setObjectName(f"NMButton_{self._variant}")
            self._apply_btn_shadow()
            self.update()

    def variant(self) -> str:
        return self._variant

    def set_size(self, size: str):
        if size in ("sm", "md", "lg") and size != self._size:
            self._size = size
            self.setFixedHeight(_NM_BUTTON_HEIGHT[size])
            self.setFont(qfont(_NM_BUTTON_FONT[size], weight=_NM_CONTROL_WEIGHT))
            self.update()

    # ── paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        r = min(LAYOUT["radius_button"], h // 2)
        w = self.width()
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        is_dark = "dark" in self._modo

        if not self.isEnabled():
            p.setOpacity(0.4)

        if self._variant == "gradient":
            primary = v3c("primary", self._modo)
            p.fillPath(path, QBrush(primary))

            # Pressed: tinte plano (runtime — el ripple radial fue eliminado;
            # alpha 45 compensa el feedback que aportaba la onda).
            if self._pressed and self.isEnabled():
                p.fillPath(path, QBrush(QColor(0, 0, 0, 45)))

            # Hover: soft inner highlight ring (no heavy outer glow)
            if self._hover and not self._pressed and self.isEnabled():
                ring_c = QColor(255, 255, 255, 55 if is_dark else 70)
                p.setPen(QPen(ring_c, 1.5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                inset = 1.25
                p.drawRoundedRect(rect.adjusted(inset, inset, -inset, -inset), r, r)

            text_color = v3c("primary_ink", self._modo)

        elif self._variant == "secondary":
            surf_key = "surfaceSolid" if is_dark else "surface"
            elev_key = "elevatedSolid" if is_dark else "elevated"

            if self._pressed and self.isEnabled():
                # Press: one step deeper than hover
                bg_col = v3c(elev_key, self._modo)
                bg_col.setAlpha(230 if is_dark else 255)
                p.fillPath(path, QBrush(bg_col))
            elif self._hover and self.isEnabled():
                p.fillPath(path, QBrush(v3c(elev_key, self._modo)))
            else:
                p.fillPath(path, QBrush(v3c(surf_key, self._modo)))

            border_key = "borderStrong" if (self._hover or self._pressed) else "border"
            border_col = v3c(border_key, self._modo)
            p.setPen(QPen(border_col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

            text_color = v3c("text", self._modo)

        elif self._variant in ("danger", "destructive"):
            bg_col = v3c("dangerSoftSolid", self._modo)
            if self._pressed and self.isEnabled():
                bg_col = QColor(blend_color(v3c("danger", self._modo).name(), bg_col.name(), 0.20))
            elif self._hover and self.isEnabled():
                bg_col = QColor(blend_color(v3c("danger", self._modo).name(), bg_col.name(), 0.10))
            p.fillPath(path, QBrush(bg_col))

            border_key = "danger" if (self._hover or self._pressed) else "dangerSoft"
            border_col = v3c(border_key, self._modo)
            p.setPen(QPen(border_col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

            text_color = v3c("danger", self._modo)

        else:  # ghost
            if self._pressed and self.isEnabled():
                # Press: slightly deeper tint than hover
                bg_c = v3c("border", self._modo)
                bg_c.setAlpha(90 if is_dark else 100)
                p.fillPath(path, QBrush(bg_c))
            elif self._hover and self.isEnabled():
                bg_col = v3c("borderSoft", self._modo)
                p.fillPath(path, QBrush(bg_col))
            # Text: lift to `text` on hover/press for clear feedback
            text_color = (
                v3c("text", self._modo)
                if (self._hover or self._pressed) and self.isEnabled()
                else v3c("text2", self._modo)
            )

        # Label
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
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._pressed = True
            self._animate_press_scale(0.97)
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._pressed:
            self._pressed = False
            self._animate_press_scale(1.0)
            self.update()
        super().mouseReleaseEvent(event)

    def _animate_press_scale(self, scale: float):
        """Scale 0.97 ↔ 1.0 (100ms) — spec README v3 para botones."""
        if scale < 1.0:
            self._base_geom = self.geometry()
        base = self._base_geom or self.geometry()
        if not base or base.isNull():
            return
        if scale >= 1.0:
            target = base
        else:
            dw = int(base.width() * (1.0 - scale) / 2)
            dh = int(base.height() * (1.0 - scale) / 2)
            target = base.adjusted(dw, dh, -dw, -dh)
        if self._scale_anim:
            try:
                if not sip.isdeleted(self._scale_anim):
                    self._scale_anim.stop()
            except RuntimeError:
                pass
            self._scale_anim = None
        anim = QPropertyAnimation(self, b"geometry", self)
        self._scale_anim = anim
        anim.setDuration(100)
        anim.setStartValue(self.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(EASE_OUT)
        anim.finished.connect(
            lambda a=anim: setattr(self, "_scale_anim", None)
            if self._scale_anim is a else None
        )
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        if scale >= 1.0:
            self._base_geom = None

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self._apply_btn_shadow()
        self.update()

    def _apply_btn_shadow(self):
        if not self.isEnabled():
            self.setGraphicsEffect(None)
            self._btn_shadow = None
            return
        is_dark = "dark" in self._modo
        if self._btn_shadow is None:
            self._btn_shadow = QGraphicsDropShadowEffect(self)
            self.setGraphicsEffect(self._btn_shadow)
        shadow = self._btn_shadow
        if self._variant == "gradient":
            # Primary CTA: lift discreto. runtime §7.3: en dark la elevación es por
            # contraste sutil — sombra neutra, nunca halo tintado con el acento.
            if is_dark:
                shadow.setBlurRadius(12)
                shadow.setOffset(0, 3)
                sc = QColor(0, 0, 0, 86)
            else:
                shadow.setBlurRadius(10)
                shadow.setOffset(0, 2)
                sc = QColor(0x44, 0x2A, 0x0A, 22)  # warm stone tint — no cold teal on ivory
        elif self._variant == "secondary":
            # Sombra neutra sutil (lift discreto)
            shadow.setBlurRadius(8 if is_dark else 6)
            shadow.setOffset(0, 2 if is_dark else 1)
            sc = QColor(0, 0, 0, 54 if is_dark else 10)
        elif self._variant == "danger":
            # Subtle danger soft shadow
            shadow.setBlurRadius(8 if is_dark else 5)
            shadow.setOffset(0, 2 if is_dark else 1)
            sc = v3c("danger", self._modo)
            sc.setAlpha(40 if is_dark else 15)
        else:  # ghost
            self.setGraphicsEffect(None)
            self._btn_shadow = None
            return
        shadow.setColor(sc)

    def play_success(self):
        """Pulso de escala."""
        base = self.geometry()
        if base.isNull():
            return
        target = base.adjusted(-2, -2, 2, 2)
        if self._success_anim:
            try:
                if not sip.isdeleted(self._success_anim):
                    self._success_anim.stop()
            except RuntimeError:
                pass
            self._success_anim = None
        group = QSequentialAnimationGroup(self)
        self._success_anim = group
        grow = QPropertyAnimation(self, b"geometry", self)
        grow.setDuration(ANIM["fast"])
        grow.setStartValue(base)
        grow.setEndValue(target)
        grow.setEasingCurve(QEasingCurve.Type.OutElastic)
        shrink = QPropertyAnimation(self, b"geometry", self)
        shrink.setDuration(ANIM["fast"])
        shrink.setStartValue(target)
        shrink.setEndValue(base)
        shrink.setEasingCurve(QEasingCurve.Type.OutElastic)
        group.addAnimation(grow)
        group.addAnimation(shrink)
        group.finished.connect(
            lambda g=group: setattr(self, "_success_anim", None)
            if self._success_anim is g else None
        )
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMButtonOutline ───────────────────────────────────────────────────────────


class NMButtonOutline(QPushButton):
    """Botón pill toggleable v3 — variant ``secondary`` cuando inactivo,
    fill gradient teal→violet cuando activo.

    Si ``toggleable=True`` alterna ``active`` en cada click. Estilo coherente
    con :class:`NMButton` (mismo radius pill, misma tipografía sm).
    """

    def __init__(
        self,
        text: str = "",
        parent=None,
        modo: str = None,
        toggleable: bool = False,
        size: str = "md",
    ):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._hover = False
        self._active = False
        self._toggleable = toggleable
        self._size = size if size in ("sm", "md", "lg") else "md"
        self._success_anim: QSequentialAnimationGroup | None = None

        self.setFont(qfont(_NM_BUTTON_FONT[self._size], weight=_NM_CONTROL_WEIGHT))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setMinimumHeight(_NM_BUTTON_HEIGHT[self._size])
        self.setAccessibleName(text)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        _tm().theme_changed.connect(self._apply_theme)

    def setText(self, text: str):
        super().setText(text)
        self.setAccessibleName(text)
        self.update()

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def is_active(self) -> bool:
        return self._active

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        r = min(LAYOUT["radius_button"], h // 2)
        w = self.width()
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        is_dark = "dark" in self._modo

        if not self.isEnabled():
            p.setOpacity(0.4)

        if self._active:
            # Active: primary SÓLIDO + tinta token (F5 runtime — antes
            # gradiente firma 135° con texto #ffffff duro y ring interno).
            p.fillPath(path, QBrush(v3c("primary", self._modo)))
            text_color = v3c("primary_ink", self._modo)

        elif self._hover:
            # Hover: elevated surface + strong border
            elev_key = "elevatedSolid" if is_dark else "elevated"
            p.fillPath(path, QBrush(v3c(elev_key, self._modo)))
            p.setPen(QPen(v3c("borderStrong", self._modo), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)
            # Hover: lift text from text2 → text
            text_color = v3c("text", self._modo)

        else:
            # Rest: surface + border
            surf_key = "surfaceSolid" if is_dark else "surface"
            p.fillPath(path, QBrush(v3c(surf_key, self._modo)))
            p.setPen(QPen(v3c("border", self._modo), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)
            text_color = v3c("text2", self._modo)

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
        if event.button() == Qt.MouseButton.LeftButton and self._toggleable:
            self._active = not self._active
            self.update()
        super().mousePressEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self.update()

    def play_success(self):
        base = self.geometry()
        if base.isNull():
            return
        target = base.adjusted(-2, -2, 2, 2)
        if self._success_anim:
            try:
                if not sip.isdeleted(self._success_anim):
                    self._success_anim.stop()
            except RuntimeError:
                pass
            self._success_anim = None
        group = QSequentialAnimationGroup(self)
        self._success_anim = group
        grow = QPropertyAnimation(self, b"geometry", self)
        grow.setDuration(ANIM["fast"])
        grow.setStartValue(base)
        grow.setEndValue(target)
        grow.setEasingCurve(QEasingCurve.Type.OutElastic)
        shrink = QPropertyAnimation(self, b"geometry", self)
        shrink.setDuration(ANIM["fast"])
        shrink.setStartValue(target)
        shrink.setEndValue(base)
        shrink.setEasingCurve(QEasingCurve.Type.OutElastic)
        group.addAnimation(grow)
        group.addAnimation(shrink)
        group.finished.connect(
            lambda g=group: setattr(self, "_success_anim", None)
            if self._success_anim is g else None
        )
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMInput ───────────────────────────────────────────────────────────────────


class NMInput(QLineEdit):
    """
    QLineEdit estilizado. Focus anima el color del borde border→border_focus en 200ms.
    """

    def __init__(self, placeholder: str = "", parent=None, modo: str = None, max_length: int | None = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._focus_glow: QGraphicsDropShadowEffect | None = None
        self._error_message = ""
        self.setObjectName("NMInput")
        self.setPlaceholderText(placeholder)
        self.setAccessibleName(placeholder)
        # Límite físico opcional (auditoría v1.0): textos sin tope rompen el
        # responsive de la Suite al sincronizar (el Hub inyecta estos textos).
        if max_length is not None:
            self.setMaxLength(int(max_length))
        self.setFont(qfont(_NM_CONTROL_FONT))
        self.setMinimumHeight(_NM_CONTROL_HEIGHT)
        self.setMaximumHeight(_NM_CONTROL_HEIGHT)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._apply_base_style()

        _tm().theme_changed.connect(self._apply_theme)

    def _apply_base_style(self):
        bg_c = v3c("surface_2", self._modo)
        text_c = v3c("text", self._modo)
        faint_c = v3c("faint", self._modo)
        border_c = v3c("border", self._modo)
        # Foco suave: accent con alpha (no a plena intensidad) — borde fino
        # y calmo, alineado al patrón de Recordatorios (user feedback).
        focus_c = v3c("accent", self._modo)  # teal (light) / purple (dark)
        focus_c.setAlpha(160)
        acc_c = v3c("accent", self._modo)
        if self._error_message:
            border_c = v3c("danger", self._modo)
            focus_c = border_c
        r = _NM_CONTROL_RADIUS
        sel_text_c = v3c("primary_ink", self._modo)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_c.name()};
                color: {text_c.name()};
                border: 1px solid {qcolor_to_rgba_css(border_c)};
                border-radius: {r}px;
                padding: 0 12px;
                font-size: {TYPOGRAPHY["size_body"]}px;
                selection-background-color: {acc_c.name()};
                selection-color: {sel_text_c.name()};
            }}
            QLineEdit::placeholder {{
                color: {faint_c.name()};
            }}
            QLineEdit:focus {{
                border: 1px solid {qcolor_to_rgba_css(focus_c)};
                background-color: {bg_c.name()};
            }}
            {focus_ring_stylesheet(self._modo)}
        """)

    def focusInEvent(self, event):
        """Enciende glow suave alrededor del input en el color del accent."""
        super().focusInEvent(event)
        is_dark = "dark" in self._modo
        if self._focus_glow is None:
            self._focus_glow = QGraphicsDropShadowEffect(self)
        self._focus_glow.setBlurRadius(12 if is_dark else 10)
        self._focus_glow.setOffset(0, 0)
        gc = v3c("accent", self._modo)
        # Glow contenido en ambos temas (user feedback: el resplandor fuerte se
        # leía duro, no UI).
        gc.setAlpha(70 if is_dark else 50)
        self._focus_glow.setColor(gc)
        self.setGraphicsEffect(self._focus_glow)

    def focusOutEvent(self, event):
        """Apaga glow al perder foco."""
        super().focusOutEvent(event)
        self.setGraphicsEffect(None)
        self._focus_glow = None

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_base_style()

    def set_error(self, message: str = ""):
        """Marca el input en estado error real sin inventar QSS por pantalla."""
        self._error_message = message or "Error"
        self.setToolTip(self._error_message)
        self._apply_base_style()

    def clear_error(self):
        self._error_message = ""
        self.setToolTip("")
        self._apply_base_style()


# ── NMSegmentedChoice ─────────────────────────────────────────────────────────


class NMSegmentedChoice(QWidget):
    """Grupo de NMButtonOutline con selección exclusiva. Emite choice_made(str)."""

    choice_made = pyqtSignal(str)

    def __init__(self, choices: list[tuple[str, str]], modo: str = "dark_hybrid", parent=None):
        """
        choices: lista de (label, value). Ej: [("Hecha", "hecha"), ("No pude", "no_pude")]
        """
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._btns: dict[str, NMButtonOutline] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)  # 4px per F2.2 — reduced from 6px
        for label, value in choices:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=True)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(72)
            btn.clicked.connect(lambda checked=False, v=value, b=btn: self._select(v, b))
            layout.addWidget(btn)
            self._btns[value] = btn
        layout.addStretch()

    def _select(self, value: str, active_btn: NMButtonOutline):
        for v, btn in self._btns.items():
            btn.set_active(btn is active_btn)
        self.choice_made.emit(value)

    def selected(self) -> str:
        for v, btn in self._btns.items():
            if btn.is_active():
                return v
        return ""

    def reset(self):
        for btn in self._btns.values():
            btn.set_active(False)


# ── NMSearchInput ────────────────────────────────────────────────────────────


class NMSearchInput(QWidget):
    """Input de búsqueda con icono de lupa y botón clear (aparece con texto).

    Uso:
        s = NMSearchInput(placeholder="Buscar paciente…")
        s.text_changed.connect(self._on_search)
        s.text() / s.set_text("foo")
    """

    text_changed = pyqtSignal(str)
    returned = pyqtSignal(str)

    def __init__(self, placeholder: str = "Buscar…", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(_NM_CONTROL_HEIGHT)
        self.setMaximumHeight(_NM_CONTROL_HEIGHT)
        self.setAccessibleName("Buscar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["sm"], 0, V3_SP["xs"], 0)
        lay.setSpacing(V3_SP["xs"])

        self._icon = QLabel()
        self._icon.setFixedSize(20, 20)
        lay.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setFrame(False)
        self._edit.setFont(qfont(_NM_CONTROL_FONT))
        # Texto centrado verticalmente: sin margen de texto propio el QLineEdit
        # frameless dejaba el placeholder/valor pegado abajo del campo. Margen 0
        # + alineación VCenter en el layout lo centran de forma estable con
        # cualquier fuente (Manrope cargada vs fallback).
        self._edit.setTextMargins(0, 0, 0, 0)
        self._edit.textChanged.connect(self._on_text_changed)
        self._edit.returnPressed.connect(lambda: self.returned.emit(self._edit.text()))
        lay.addWidget(self._edit, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._clear_btn = QPushButton("")
        self._clear_btn.setFixedSize(22, 22)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setFlat(True)
        self._clear_btn.clicked.connect(lambda: self._edit.setText(""))
        self._clear_btn.setVisible(False)
        lay.addWidget(self._clear_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def text(self) -> str:
        return self._edit.text()

    def set_text(self, value: str):
        self._edit.setText(value or "")

    def set_placeholder(self, value: str):
        self._edit.setPlaceholderText(value or "")

    def _on_text_changed(self, text: str):
        self._clear_btn.setVisible(bool(text))
        self.text_changed.emit(text)

    def _render_icons(self):
        try:
            from shared.icons_svg import nm_svg_pixmap, has_icon
        except ImportError:
            return
        text_col = v3c("ink_secondary", self._modo).name()
        if has_icon("search"):
            pix = nm_svg_pixmap("search", text_col, 18)
            if pix is not None and not pix.isNull():
                self._icon.setPixmap(pix)
        if has_icon("close"):
            pix = nm_svg_pixmap("close", text_col, 14)
            if pix is not None and not pix.isNull():
                self._clear_btn.setIcon(QIcon(pix))
                self._clear_btn.setIconSize(QSize(14, 14))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(_NM_CONTROL_RADIUS)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        bg = v3c("surface_2", self._modo)
        focused = self._edit.hasFocus()
        border = v3c("accent" if focused else "border", self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(QPen(border, 1.5 if focused else 1.0))
        p.drawRoundedRect(rect, r, r)
        p.end()

    def focusInEvent(self, event):
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.update()
        super().focusOutEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c_text = v3c("text", self._modo).name()
        c_placeholder = v3c("faint", self._modo).name()
        self._edit.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; "
            f"color: {c_text}; padding: 6px 4px; "
            f"font-size: {TYPOGRAPHY['size_body']}px; }}"
            f"QLineEdit::placeholder {{ color: {c_placeholder}; }}"
        )
        self._clear_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._render_icons()
        # Forzar repintado de border via focus event listener
        self._edit.installEventFilter(self) if not hasattr(self, "_filt") else None
        self._filt = True
        self.update()

    def eventFilter(self, obj, ev):
        if obj is self._edit and ev.type() in (ev.Type.FocusIn, ev.Type.FocusOut):
            self.update()
        return super().eventFilter(obj, ev)


# ── NMTextArea ───────────────────────────────────────────────────────────────


class NMTextArea(QTextEdit):
    """QTextEdit con tema, border focus, placeholder y altura mínima."""

    def __init__(
        self,
        placeholder: str = "",
        modo: str = None,
        min_height: int = 96,
        max_length: int | None = None,
        font_key: str = _NM_CONTROL_FONT,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._max_length = max_length
        # font_key configurable: el contenido generado por IA usa "size_small"
        # (más compacto, pedido user feedback) sin afectar el resto de los text areas.
        self._font_key = font_key if font_key in TYPOGRAPHY else _NM_CONTROL_FONT
        self.setPlaceholderText(placeholder or "")
        self.setAccessibleName(placeholder or "Text area")
        self.setMinimumHeight(min_height)
        self.setFont(qfont(self._font_key))
        self.setAcceptRichText(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        if max_length is not None:
            # QTextEdit no tiene setMaxLength: tope físico vía textChanged
            # (auditoría v1.0 — pegar texto masivo rompía el responsive de la
            # Suite al sincronizar).
            self.textChanged.connect(self._enforce_max_length)
        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def _enforce_max_length(self):
        if self._max_length is None:
            return
        text = self.toPlainText()
        if len(text) <= self._max_length:
            return
        cursor = self.textCursor()
        pos = min(cursor.position(), self._max_length)
        self.blockSignals(True)
        self.setPlainText(text[: self._max_length])
        cursor = self.textCursor()
        cursor.setPosition(pos)
        self.setTextCursor(cursor)
        self.blockSignals(False)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg = v3c("surface_2", self._modo).name()
        text_col = v3c("text", self._modo).name()
        placeholder = v3c("faint", self._modo).name()
        border = C("border", self._modo)
        focus_col = v3c("accent", self._modo).name()
        sel_text = v3c("primary_ink", self._modo).name()
        # Foco fino y suave (1px, accent con alpha) — el 1.5px a plena
        # intensidad se leía duro/grueso (informe user feedback: alinear al
        # borde verde suave de Recordatorios).
        _focus_soft = QColor(v3c("accent", self._modo))
        _focus_soft.setAlpha(150)
        # Scrollbar canónica (clínica, neutra): un QTextEdit con stylesheet
        # propio pierde el QScrollBar global y caía al nativo de Qt (las "muchas
        # scrollbars que violan el runtime" en el tab IA). La apendamos al QSS.
        from shared.theme_qt import _clinical_scrollbar_qss

        self.setStyleSheet(
            f"QTextEdit {{ background-color: {bg}; color: {text_col}; "
            f"border: 1px solid {border}; border-radius: {_NM_CONTROL_RADIUS}px; "
            f"padding: 8px 12px; font-size: {TYPOGRAPHY[self._font_key]}px; "
            f"selection-background-color: {focus_col}; selection-color: {sel_text}; }}"
            f"QTextEdit:focus {{ border: 1px solid {qcolor_to_rgba_css(_focus_soft)}; }}"
            + _clinical_scrollbar_qss(self._modo)
        )
        # Solo el placeholder en color faint (vía palette). Antes se pintaba el
        # viewport con ese color, lo que también atenuaba el TEXTO escrito y lo
        # dejaba casi ilegible en light. El texto real usa text_col del QSS.
        _pal = self.palette()
        _pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(placeholder))
        self.setPalette(_pal)


# ── NMTabs ───────────────────────────────────────────────────────────────────


class NMTabs(QWidget):
    """Tabs custom (pill o underline). API minimal independiente de QTabWidget.

    Uso:
        t = NMTabs(["Todos", "Activos", "Sin registros"])
        t.changed.connect(self._on_tab)
        t.set_current(0)
    """

    changed = pyqtSignal(int, str)  # index, label

    def __init__(
        self,
        labels: list[str] | None = None,
        variant: str = "pill",  # "pill" | "underline"
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = variant if variant in ("pill", "filter", "underline") else "pill"
        self._labels = list(labels or [])
        self._current = 0
        self._btns: list[QPushButton] = []
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(V3_SP["xs"])
        self._build_buttons()
        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def _build_buttons(self):
        # Limpiar
        for b in self._btns:
            b.setParent(None)
            b.deleteLater()
        self._btns.clear()
        # Crear
        for i, label in enumerate(self._labels):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, idx=i: self.set_current(idx))
            self._lay.addWidget(btn)
            self._btns.append(btn)
        self._lay.addStretch()

    def set_labels(self, labels: list[str]):
        self._labels = list(labels or [])
        self._current = 0
        self._build_buttons()
        self._apply_theme(self._modo)

    def set_current(self, idx: int):
        if not (0 <= idx < len(self._labels)):
            return
        self._current = idx
        for i, b in enumerate(self._btns):
            b.setChecked(i == idx)
        self._style_buttons()
        self.changed.emit(idx, self._labels[idx])

    def current(self) -> int:
        return self._current

    def _style_buttons(self):
        primary = v3c("primary", self._modo).name()
        primary_ink = v3c("primary_ink", self._modo).name()
        text = v3c("text", self._modo).name()
        text_muted = v3c("text2", self._modo).name()
        surface_2 = v3c("surface_2", self._modo).name()
        border = v3c("border", self._modo)
        border_strong = v3c("borderStrong", self._modo)
        soft_css = (
            f"rgba({border.red()},{border.green()},"
            f"{border.blue()},{max(border.alpha(), 24)})"
        )
        strong_css = (
            f"rgba({border_strong.red()},{border_strong.green()},"
            f"{border_strong.blue()},{max(border_strong.alpha(), 48)})"
        )
        for i, b in enumerate(self._btns):
            b.setMinimumHeight(_NM_TAB_HEIGHT)
            b.setFont(qfont(_NM_TAB_FONT, weight=_NM_CONTROL_WEIGHT))
            checked = i == self._current
            if self._variant == "underline":
                if checked:
                    b.setStyleSheet(
                        f"QPushButton {{ background: transparent; color: {primary}; "
                        f"border: none; border-bottom: 2px solid {primary}; "
                        "padding: 4px 10px; border-radius: 0px; }}"
                    )
                else:
                    b.setStyleSheet(
                        f"QPushButton {{ background: transparent; color: {text_muted}; "
                        "border: none; border-bottom: 2px solid transparent; "
                        "padding: 4px 10px; border-radius: 0px; }}"
                        f"QPushButton:hover {{ color: {text}; }}"
                    )
            elif checked:
                b.setStyleSheet(
                    f"QPushButton {{ background: {primary}; color: {primary_ink}; "
                    f"border: none; padding: 4px 14px; "
                    f"border-radius: {_NM_TAB_RADIUS - 3}px; }}"
                )
            else:
                bg = "transparent" if self._variant == "filter" else surface_2
                b.setStyleSheet(
                    f"QPushButton {{ background: {bg}; color: {text_muted}; "
                    f"border: 1px solid {soft_css}; padding: 4px 14px; "
                    f"border-radius: {_NM_TAB_RADIUS - 3}px; }}"
                    f"QPushButton:hover {{ color: {text}; border-color: {strong_css}; }}"
                )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._style_buttons()
