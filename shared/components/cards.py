"""Card surfaces: NMCard hierarchy and standalone themed cards."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
    QEnterEvent,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from shared.components.buttons import (
    _NM_CONTROL_FONT,
    _NM_CONTROL_HEIGHT,
    _NM_CONTROL_PILL_RADIUS,
    _NM_CONTROL_WEIGHT,
)
from shared.components.layout import FlowLayout
from shared.components.patient import NMAreaSparkline
from shared.components.session import _rgba
from shared.theme import TYPOGRAPHY, V3_DARK, V3_LIGHT, V3_SHADOWS
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    ANIM,
    C,
    EASE_OUT,
    PAD_CARD,
    RADIUS_CARD,
    SIZE_TIME_LARGE,
    V3_RD,
    V3_SP,
    colors,
    eyebrow_font,
    focus_ring_stylesheet,
    label_style,
    norm_modo,
    qfont,
    qfont_mono,
    sp,
    v3c,
)


def _tm() -> ThemeManager:
    return ThemeManager.instance()


# ── NMCard ────────────────────────────────────────────────────────────────────


class NMCard(QFrame):
    """
    Card v3 — superficie limpia con border ``borderSoft`` y radius 18.

    Spec del README v3:
      - Surface ``v3c("surface")`` (o ``surfaceSolid`` en dark para QSS).
      - Border 1px ``borderSoft`` → cambia a ``borderStrong`` en hover.
      - Sin scale ni desplazamiento horizontal en press (eso es de botones).
      - ``glow=True``: halo teal concéntrico alrededor + (solo dark)
        overlay gradient teal→violet al 10% de opacidad.

    Args:
        accent_color: Hex que tiñe el halo si ``glow=True`` (default = teal).
        clickable:    Cursor pointer + emite ``clicked`` al soltar.
        modo:         Override de tema; ``None`` = sigue ThemeManager.
        disabled:     Opacity 0.45 + cursor forbidden + tooltip reason.
        glow:         Halo + (en dark) overlay gradient translúcido.
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        parent=None,
        accent_color: str = None,
        clickable: bool = True,
        modo: str = None,
        disabled: bool = False,
        disabled_reason: str = "",
        glow: bool = False,
        active: bool = False,
        radius: int | None = None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        # Radio override por instancia (None = V3_RD["card"]). Permite cards
        # de borde recto donde el redondeo lee desprolijo (p.ej. paneles
        # laterales pegados al borde de la ventana).
        self._radius_override = radius
        self._accent = accent_color
        self._base_accent = accent_color
        self._clickable = clickable
        self._glow = glow
        self._active = active
        self._hover = False
        self._disabled = False
        self._disabled_effect: QGraphicsOpacityEffect | None = None
        self._disabled_reason = ""
        self._success_anim: QSequentialAnimationGroup | None = None
        self._scale_anim: QPropertyAnimation | None = None
        self._card_shadow: QGraphicsDropShadowEffect | None = None

        self.setObjectName("NMCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if clickable else Qt.CursorShape.ArrowCursor
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self.set_disabled(disabled, disabled_reason)
        # Aplicar sombra al construir (v3 spec) — antes solo se aplicaba
        # al cambiar tema, dejando la primera render sin sombra (cards planas
        # en light).
        if not disabled:
            self._apply_card_shadow()

        _tm().theme_changed.connect(self._apply_theme)

    # ── sombra v3 (extraída para reutilizar desde init / theme / glow) ──────

    def _apply_card_shadow(self):
        """Crea o refresca QGraphicsDropShadowEffect según modo + glow.

        Spec V3_SHADOWS (shared/theme.py):
          light card:  blur 12, offset (0,4), rgba(15,23,42,13)
          dark  card:  blur 30, offset (0,10), rgba(0,0,0,115)
          light ring:  blur 20, offset (0,4), teal alpha 96  (glow=True)
          dark  glow:  blur 40, offset (0,0),  accent alpha 120 (glow=True)
        """
        if self._disabled:
            return
        if self._card_shadow is None:
            self._card_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if self._glow:
            # Halo accent — reads from V3_SHADOWS ring/glow bucket
            if is_dark:
                s = V3_SHADOWS["dark"]["glow"]
                self._card_shadow.setBlurRadius(s["blur"])
                self._card_shadow.setOffset(*s["offset"])
                sc = v3c("accent", self._modo)
                sc.setAlpha(s["color"][3])  # 46 from token
            else:
                s = V3_SHADOWS["light"]["ring"]
                self._card_shadow.setBlurRadius(s["blur"])
                self._card_shadow.setOffset(*s["offset"])
                sc = v3c("teal", self._modo)
                sc.setAlpha(s["color"][3])  # 76 from token
        else:
            # Standard card shadow — reads from V3_SHADOWS card bucket
            if is_dark:
                s = V3_SHADOWS["dark"]["card"]
                self._card_shadow.setBlurRadius(s["blur"])  # 30
                self._card_shadow.setOffset(*s["offset"])  # (0, 10)
                sc = QColor(*s["color"])  # rgba(0,0,0,115)
            else:
                s = V3_SHADOWS["light"]["card"]
                self._card_shadow.setBlurRadius(s["blur"])  # 12
                self._card_shadow.setOffset(*s["offset"])  # (0, 4)
                sc = QColor(*s["color"])  # rgba(15,23,42,13)
        self._card_shadow.setColor(sc)
        self.setGraphicsEffect(self._card_shadow)

    # ── hover (solo cambia el color del border, sin escalado) ─────────────────

    def enterEvent(self, event: QEnterEvent):
        # F2 runtime: hover NO agranda la sombra (la card no "se levanta");
        # el feedback es el borde (border → borderStrong en paintEvent).
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ── click (v3 no aplica scale a cards en press; solo se emite clicked) ────

    def mouseReleaseEvent(self, event: QMouseEvent):
        if (
            self._clickable
            and not self._disabled
            and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.pos())
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _animate_press_scale(self, scale: float):
        """Pulso de escala — usado por ``play_success`` (no por hover/click)."""
        base = self.geometry()
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
        anim.setDuration(ANIM["fast"])
        anim.setStartValue(self.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(EASE_OUT)
        anim.finished.connect(
            lambda a=anim: setattr(self, "_scale_anim", None)
            if self._scale_anim is a else None
        )
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── paintEvent v3 ─────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = "dark" in self._modo
        r = (
            self._radius_override
            if getattr(self, "_radius_override", None) is not None
            else V3_RD["card"]  # 18px — UI Hub card radius
        )
        w, h = self.width(), self.height()
        rect = QRectF(0, 0, w, h)

        # Superficie sólida del cockpit: card limpia, sin glass ni highlights.
        if not self._disabled and self.isEnabled():
            surf_col = v3c("surfaceSolid" if is_dark else "surface", self._modo)
            p.setBrush(QBrush(surf_col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)
        else:
            # Disabled: solid surface for legibility
            surface_key = "surfaceSolid" if is_dark else "surface"
            p.setBrush(QBrush(v3c(surface_key, self._modo)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)

        if self._glow and not self._disabled and self.isEnabled():
            accent = QColor(self._accent or v3c("primary", self._modo).name())
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(accent))
            p.drawRoundedRect(QRectF(0, 12, 3, max(18, h - 24)), 1.5, 1.5)

        # Border: 'primary' if active, 'borderStrong' on hover, else 'border'
        if self._active:
            border_c = v3c("primary", self._modo)
            pen = QPen(border_c, 2)
        elif self._hover and self.isEnabled() and not self._disabled:
            border_c = v3c("borderStrong", self._modo)
            pen = QPen(border_c, 1)
        else:
            border_c = v3c("border", self._modo)
            pen = QPen(border_c, 1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.end()

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self._apply_card_shadow()
        self.update()

    def set_active(self, active: bool):
        self._active = bool(active)
        self.update()

    def set_accent(self, hex_color: str | None):
        """En v3 solo afecta el color del halo cuando ``glow=True``."""
        self._accent = hex_color
        self._base_accent = hex_color
        self.update()

    def set_glow(self, enabled: bool):
        self._glow = bool(enabled)
        # Re-aplicar shadow con preset distinto (card → ring/glow)
        self._apply_card_shadow()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        if state:
            if self._disabled_effect is None:
                self._disabled_effect = QGraphicsOpacityEffect(self)
                self.setGraphicsEffect(self._disabled_effect)
            self._disabled_effect.setOpacity(0.45)
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            if self._disabled_effect is not None:
                self._disabled_effect.deleteLater()
                self._disabled_effect = None
            self.setCursor(
                Qt.CursorShape.PointingHandCursor if self._clickable else Qt.CursorShape.ArrowCursor
            )
            # Restaurar sombra (reemplaza el QGraphicsOpacityEffect anterior)
            self._apply_card_shadow()
        self.update()

    def play_success(self):
        """Pulso de escala + flash del halo en success."""
        if self._disabled:
            return
        base = self.geometry()
        if base.isNull():
            return
        prev_accent = self._accent
        prev_glow = self._glow
        self._accent = C("success", self._modo)
        self._glow = True
        self.update()

        target = base.adjusted(
            -int(base.width() * 0.02),
            -int(base.height() * 0.02),
            int(base.width() * 0.02),
            int(base.height() * 0.02),
        )
        if self._success_anim:
            try:
                if not sip.isdeleted(self._success_anim):
                    self._success_anim.stop()
            except RuntimeError:
                pass
            self._success_anim = None
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

        group = QSequentialAnimationGroup(self)
        self._success_anim = group
        group.addAnimation(grow)
        group.addAnimation(shrink)

        def _restore():
            self._accent = prev_accent
            self._glow = prev_glow
            self.update()

        group.finished.connect(_restore)
        group.finished.connect(
            lambda g=group: setattr(self, "_success_anim", None)
            if self._success_anim is g else None
        )
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

# ── NMSectionCard ─────────────────────────────────────────────────────────────


class NMSectionCard(QFrame):
    """Card con título decorativo. content_widget() devuelve el área para widgets."""

    def __init__(self, title: str = "", icon: str = "", modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._title = title
        self._icon = icon
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._build()
        _tm().theme_changed.connect(self._apply_theme)

    def _build(self):
        c = colors(self._modo)
        self.setStyleSheet(f"""
            NMSectionCard {{
                background-color: {c["bg_surface"]};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get("border_card", c["border"])};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        if self._icon:
            icon_lbl = QLabel(self._icon)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title_lbl = QLabel(self._title)
        title_lbl.setFont(qfont("size_body", bold=True))
        title_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(4)
        layout.addWidget(self._content)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(f"""
            NMSectionCard {{
                background-color: {c["bg_surface"]};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get("border_card", c["border"])};
            }}
        """)

# ── NMAvisoCard ───────────────────────────────────────────────────────────────


class NMAvisoCard(QFrame):
    """Card de recordatorio con hora grande, mensaje y status pill.

    status: 'activo' | 'disparado' | 'expirado'
    """

    STATUS_ACTIVE = "activo"
    STATUS_FIRED = "disparado"
    STATUS_EXPIRED = "expirado"

    def __init__(
        self, time_str: str, message: str, status: str = "activo", modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._status = status
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # Quitamos border en setStyleSheet; lo dibujamos manualmente para tener accent bar
        self.setAutoFillBackground(False)

        outer = QHBoxLayout(self)
        # Margen izquierdo extra para dejar espacio al accent bar de 3px
        outer.setContentsMargins(sp("md") + 6, sp("sm"), sp("md"), sp("sm"))
        outer.setSpacing(sp("md"))

        # Left: big monospaced time
        self._time_lbl = QLabel(time_str)
        self._time_lbl.setFont(qfont_mono(SIZE_TIME_LARGE, bold=True))
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_lbl.setFixedWidth(88)
        self._time_lbl.setStyleSheet("background: transparent;")
        outer.addWidget(self._time_lbl)

        # Right: message + status pill
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(0, 0, 0, 0)

        self._msg_lbl = QLabel(message)
        self._msg_lbl.setFont(qfont("size_body"))
        self._msg_lbl.setWordWrap(True)
        self._msg_lbl.setStyleSheet("background: transparent;")
        right.addWidget(self._msg_lbl)

        pill_row = QHBoxLayout()
        pill_row.setSpacing(sp("sm"))
        self._pill = QLabel()
        self._pill.setFixedHeight(20)
        self._pill.setContentsMargins(10, 0, 10, 0)
        self._pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pill.setFont(qfont("size_caption", bold=True))
        pill_row.addWidget(self._pill)
        pill_row.addStretch()
        right.addLayout(pill_row)

        outer.addLayout(right, stretch=1)

        self.set_status(status)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_status(self, status: str):
        self._status = status
        self._update_pill()
        self._apply_theme(self._modo)

    def _update_pill(self):
        labels = {
            self.STATUS_ACTIVE: "● Activo",
            self.STATUS_FIRED: "✓ Disparado",
            self.STATUS_EXPIRED: "○ Expirado",
        }
        self._pill.setText(labels.get(self._status, self._status))

    def _status_pill_colors(self) -> tuple[str, str]:
        if self._status == self.STATUS_ACTIVE:
            return C("teal", self._modo), C("text_on_accent", self._modo)
        if self._status == self.STATUS_FIRED:
            return C("violet", self._modo), C("text_on_accent", self._modo)
        return C("bg_elevated", self._modo), C("text_tertiary", self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        # No usamos border/background en setStyleSheet — los pintamos en paintEvent
        # para tener accent bar gradient teal→violet a la izquierda.
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        time_key = "text_primary" if self._status != self.STATUS_EXPIRED else "text_tertiary"
        self._time_lbl.setStyleSheet(f"color: {C(time_key, self._modo)}; background: transparent;")
        msg_key = "text_primary" if self._status != self.STATUS_EXPIRED else "text_tertiary"
        self._msg_lbl.setStyleSheet(label_style(self._modo, msg_key))
        pill_bg, pill_col = self._status_pill_colors()
        self._pill.setStyleSheet(
            f"QLabel {{ background: {pill_bg}; color: {pill_col}; "
            f"border-radius: 10px; font-size: {TYPOGRAPHY['size_caption']}px; "
            f"font-weight: 500; }}"
        )
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        w, h = self.width(), self.height()
        r = RADIUS_CARD
        c = colors(self._modo)

        # Card background + border
        bg = QColor(c["bg_surface"])
        if self._status == self.STATUS_EXPIRED:
            bg.setAlphaF(0.5)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, bg)

        # Accent bar lateral 3px con gradient teal→violet (gris si expirado)
        if self._status == self.STATUS_EXPIRED:
            bar_top = QColor(c.get("border_card", c["border"]))
            bar_bot = QColor(bar_top)
        else:
            bar_top = QColor(C("teal", self._modo))
            bar_bot = QColor(C("violet", self._modo))
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(0, 0, 3, h), 1.5, 1.5)
        bar_grad = QLinearGradient(0, 0, 0, h)
        bar_grad.setColorAt(0.0, bar_top)
        bar_grad.setColorAt(1.0, bar_bot)
        p.fillPath(bar_path, bar_grad)

        # Border sutil
        border_c = QColor(c.get("border_card", c["border"]))
        p.setPen(QPen(border_c, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.restore()
        p.end()

# ── NMStatCard ───────────────────────────────────────────────────────────────


class NMStatCard(QWidget):
    """Card de métrica: label arriba (eyebrow), valor grande, delta opcional.

    Uso:
        c = NMStatCard("PROMEDIO 7 DÍAS", "7.3/10")
        c.set_delta("+0.4", positive=True)
    """

    def __init__(self, label: str = "", value: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(84)
        self.setMinimumWidth(168)  # minmax(168px, 1fr) per F3.3

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["xs"], V3_SP["md"], V3_SP["xs"])
        lay.setSpacing(0)

        self._label = QLabel(label or "")
        self._label.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._label)

        value_row = QHBoxLayout()
        value_row.setSpacing(V3_SP["xs"])
        self._value = QLabel(value or "—")
        try:
            from shared.theme_qt import v3_font as _v3_font

            self._value.setFont(
                _v3_font("size_h2", weight=TYPOGRAPHY["weight_semibold"], serif=True)
            )
        except ImportError:
            self._value.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        value_row.addWidget(self._value)
        self._delta = QLabel("")
        self._delta.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))

        self._delta.setContentsMargins(6, 2, 6, 2)
        self._delta.setVisible(False)
        value_row.addWidget(self._delta)
        value_row.addStretch()
        lay.addLayout(value_row)
        lay.addStretch()

        _tm().theme_changed.connect(self._apply_theme)
        self._tone_key = None
        self._stat_shadow: QGraphicsDropShadowEffect | None = None
        self._apply_theme(self._modo)
        self._apply_stat_shadow()

    def _apply_stat_shadow(self):
        if self._stat_shadow is None:
            self._stat_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if is_dark:
            self._stat_shadow.setBlurRadius(18)
            self._stat_shadow.setOffset(0, 5)
            self._stat_shadow.setColor(QColor(0, 0, 0, 80))
        else:
            self._stat_shadow.setBlurRadius(10)
            self._stat_shadow.setOffset(0, 3)
            self._stat_shadow.setColor(QColor(28, 34, 24, 14))
        self.setGraphicsEffect(self._stat_shadow)

    def set_value(self, value: str):
        self._value.setText(value or "—")

    def set_label(self, label: str):
        self._label.setText(label or "")

    def set_tone(self, tone_key: str | None):
        """Define un color semántico (primary, accent, danger, etc) para el valor."""
        self._tone_key = tone_key
        self._apply_value_style()

    def set_delta(self, text: str, positive: bool | None = None):
        if not text:
            self._delta.setVisible(False)
            return
        self._delta.setText(text)
        self._delta.setVisible(True)
        self._delta_positive = positive
        self._style_delta()

    def _apply_value_style(self):
        if self._tone_key:
            col = v3c(self._tone_key, self._modo)
        else:
            col = v3c("text", self._modo)
        self._value.setStyleSheet(f"color: {col.name()}; background: transparent;")

    def _style_delta(self):
        pos = getattr(self, "_delta_positive", None)
        if pos is True:
            col = v3c("success", self._modo)
        elif pos is False:
            col = v3c("danger", self._modo)
        else:
            col = v3c("text2", self._modo)
        bg_alpha = 36
        bg = f"rgba({col.red()},{col.green()},{col.blue()},{bg_alpha})"
        self._delta.setStyleSheet(
            f"color: {col.name()}; background: {bg}; border-radius: 6px; padding: 2px 6px;"
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(V3_RD["card"])  # UI Hub radius 18px
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        is_dark = "dark" in self._modo
        surf = v3c("surfaceSolid" if is_dark else "surface", self._modo)
        p.setBrush(QBrush(surf))
        p.setPen(QPen(v3c("border", self._modo), 1.0))
        p.drawRoundedRect(rect, r, r)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._label.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;"
        )
        self._value.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._style_delta()
        self._apply_value_style()
        if hasattr(self, "_stat_shadow") and self._stat_shadow is not None:
            self._apply_stat_shadow()
        self.update()

# ── NMCardSecondary ──────────────────────────────────────────────────────────
# Runtime spec §4.2: variante "nm-card-2" — surface-2, sin sombra, radius 14.
# Se usa para cards anidadas o secundarias (insets dentro de cards primarias).


class NMCardSecondary(NMCard):
    """Card secundaria del runtime spec §4.2 (``nm-card-2``).

    Apaga la sombra de la card primaria y conmuta el background a
    ``surface-2`` con radius 14. Mantiene la API de NMCard.
    """

    def __init__(self, parent=None, modo: str | None = None, clickable: bool = False):
        super().__init__(parent=parent, modo=modo, clickable=clickable, glow=False)
        # Apagar sombra heredada (runtime spec §4.2: "sin sombra")
        try:
            self.setGraphicsEffect(None)
        except Exception:
            pass
        self._card_shadow = None
        self._apply_secondary_style()
        _tm().theme_changed.connect(self._reapply_secondary)

    def _apply_secondary_style(self):
        surf2 = (
            v3c("surface_2", self._modo).name()
            if "surface_2" in (V3_DARK if "dark" in self._modo else V3_LIGHT)
            else C("bg_input", self._modo)
        )
        border = v3c("line", self._modo)
        border_css = f"rgba({border.red()},{border.green()},{border.blue()},{border.alpha()})"
        # Override del stylesheet base de NMCard sin perder focus ring.
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#NMCard {{
                background-color: {surf2};
                border: 1px solid {border_css};
                border-radius: {V3_RD["lg"]}px;
            }}
        """
        )

    def _reapply_secondary(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_secondary_style()

# ── NMChartPanel ──────────────────────────────────────────────────────────────


class NMChartPanel(NMCard):
    """Panel de gráfico con zonas reservadas: eyebrow, métrica, canvas, leyenda.

    Garantiza que datos/líneas no invadan chips, labels o tabs.

    Zonas verticales (de arriba a abajo):
      - header: eyebrow (izq) + métrica inline (der)
      - subtitle: texto pequeño opcional
      - canvas: widget chart con stretch=1 (zona reservada, nunca invadida)
      - legend: labels de eje X (opcional, altura fija 16px)

    Uso::
        panel = NMChartPanel("ULTIMOS 7 DIAS", modo=modo)
        panel.set_metric("7.3/10", "Promedio")
        panel.set_chart(NMWaveChart(modo=modo))
    """

    def __init__(self, eyebrow: str = "", subtitle: str = "", modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._modo = norm_modo(modo or _tm().modo)
        self._chart_widget = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["xs"])
        self._lay = lay

        hdr = QHBoxLayout()
        hdr.setSpacing(V3_SP["sm"])
        hdr.setContentsMargins(0, 0, 0, 0)

        # Parent + visibilidad post-addWidget: setVisible(True) en un widget
        # sin padre lo muestra un instante como top-level (mini ventana).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())
        hdr.addWidget(self._eyebrow_lbl)
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        hdr.addStretch()

        self._header_tabs_row: list[QPushButton] = []
        self._header_tabs_group = QButtonGroup(self)
        self._header_tabs_group.setExclusive(True)

        self._metric_val = QLabel()
        self._metric_val.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._metric_val.setVisible(False)
        hdr.addWidget(self._metric_val)

        self._metric_label = QLabel()
        self._metric_label.setFont(qfont("size_caption_xs"))
        self._metric_label.setVisible(False)
        hdr.addWidget(self._metric_label)

        self._hdr = hdr
        lay.addLayout(hdr)

        self._subtitle_lbl = QLabel(subtitle or "", self)
        self._subtitle_lbl.setFont(qfont("size_caption_xs"))
        lay.addWidget(self._subtitle_lbl)
        self._subtitle_lbl.setVisible(bool(subtitle))

        # Optional h2 serif title (for charts with a display title below the eyebrow)
        self._title_lbl = QLabel()
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title_lbl.setVisible(False)
        lay.addWidget(self._title_lbl)

        self._canvas_slot = QWidget()
        self._canvas_slot.setStyleSheet("background: transparent;")
        self._canvas_lay = QVBoxLayout(self._canvas_slot)
        self._canvas_lay.setContentsMargins(0, 0, 0, 0)
        self._canvas_lay.setSpacing(0)
        lay.addWidget(self._canvas_slot, stretch=1)

        self._legend_row = QHBoxLayout()
        self._legend_row.setContentsMargins(0, 0, 0, 0)
        self._legend_row.setSpacing(0)
        self._legend_widget = QWidget()
        self._legend_widget.setStyleSheet("background: transparent;")
        self._legend_widget.setLayout(self._legend_row)
        self._legend_widget.setFixedHeight(16)
        self._legend_widget.setVisible(False)
        lay.addWidget(self._legend_widget)

        self._apply_chart_theme(self._modo)
        _tm().theme_changed.connect(self._apply_chart_theme)

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_title(self, text: str) -> None:
        """Título display h2 serif (para charts con título visible debajo del eyebrow)."""
        self._title_lbl.setText(text or "")
        self._title_lbl.setVisible(bool(text))

    def set_metric(self, value: str, label: str = "") -> None:
        self._metric_val.setText(value or "")
        self._metric_val.setVisible(bool(value))
        self._metric_label.setText(f"· {label}" if label else "")
        self._metric_label.setVisible(bool(label))

    def set_header_tabs(self, labels: list[str], on_select=None) -> None:
        """Añade tabs de selección de período en el header (reemplaza tabs previos).

        Args:
            labels:    Lista de etiquetas ("7D", "30D", "ALL"…).
            on_select: Callable(label: str) invocado al seleccionar.
        """
        for btn in self._header_tabs_row:
            btn.setParent(None)
        self._header_tabs_row.clear()
        for lbl in labels:
            btn = QPushButton(lbl)
            btn.setCheckable(True)
            btn.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if on_select is not None:
                btn.clicked.connect(lambda _=False, lb=lbl: on_select(lb))
            self._header_tabs_group.addButton(btn)
            self._hdr.addWidget(btn)
            self._header_tabs_row.append(btn)
        if self._header_tabs_row:
            self._header_tabs_row[0].setChecked(True)
        self._apply_chart_theme(self._modo)

    def set_chart(self, widget: QWidget) -> None:
        while self._canvas_lay.count():
            item = self._canvas_lay.takeAt(0)
            if item.widget() and item.widget() is not widget:
                item.widget().setParent(None)
        self._chart_widget = widget
        widget.setParent(self._canvas_slot)
        self._canvas_lay.addWidget(widget)

    def set_legend(self, labels: list) -> None:
        while self._legend_row.count():
            item = self._legend_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not labels:
            self._legend_widget.setVisible(False)
            return
        ink2 = v3c("ink_secondary", self._modo).name()
        for lbl in labels:
            lbl_w = QLabel(str(lbl))
            lbl_w.setFont(qfont("size_caption_xs"))
            lbl_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_w.setStyleSheet(f"color: {ink2}; background: transparent;")
            self._legend_row.addWidget(lbl_w, stretch=1)
        self._legend_widget.setVisible(True)

    def _apply_chart_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink2 = v3c("ink_secondary", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        primary = v3c("primary", self._modo).name()
        soft = v3c("bgAlt", self._modo).name()
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._metric_val.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._metric_label.setStyleSheet(f"color: {ink2}; background: transparent;")
        for i in range(self._legend_row.count()):
            item = self._legend_row.itemAt(i)
            if item and item.widget():
                item.widget().setStyleSheet(f"color: {ink2}; background: transparent;")
        for btn in self._header_tabs_row:
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {ink2}; "
                f"border: none; border-radius: 10px; padding: 2px 7px; }}"
                f"QPushButton:checked {{ background: {soft}; color: {primary}; }}"
                f"QPushButton:hover {{ color: {ink1}; }}"
            )

# ── NMMetricCard ──────────────────────────────────────────────────────────────


class NMMetricCard(NMCard):
    """Stat card unificada: eyebrow + valor grande + badge/chip opcional.

    Consolida NMStatCard (Dashboard) y las custom stat cards de Respiración
    en un componente con jerarquía y densidad consistentes.
    Altura fija FIXED_H px para grid de métricas uniforme.

    Uso::
        card = NMMetricCard("PACIENTES", "5", modo=modo)
        card.set_badge("· 3 nuevos", "primary")
        card.set_tone("primary")
    """

    # M3 UI: altura para que entren eyebrow + número serif (size_display_m=26)
    # + badge SIN cortarse, con aire interno (lectura calma, no "admin denso").
    FIXED_H = 96

    def __init__(self, label: str = "", value: str = "—", modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = None
        self.setFixedHeight(self.FIXED_H)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(3)

        self._label_lbl = QLabel(label or "")
        self._label_lbl.setFont(eyebrow_font())

        self._value_lbl = QLabel(value or "—")
        try:
            from shared.theme_qt import v3_font as _v3f
            self._value_lbl.setFont(_v3f("size_display_m", weight=TYPOGRAPHY["weight_semibold"], serif=True))
        except Exception:
            self._value_lbl.setFont(qfont("size_h1", weight=TYPOGRAPHY["weight_semibold"]))

        self._badge_row = QHBoxLayout()
        self._badge_row.setContentsMargins(0, 0, 0, 0)
        self._badge_row.setSpacing(V3_SP["xs"])
        self._badge_lbl = QLabel()
        self._badge_lbl.setFont(qfont("size_caption"))
        self._badge_lbl.setVisible(False)
        self._badge_row.addWidget(self._badge_lbl)
        self._badge_row.addStretch()

        lay.addWidget(self._label_lbl)
        lay.addWidget(self._value_lbl)
        lay.addLayout(self._badge_row)

        _tm().theme_changed.connect(self._apply_metric_theme)
        self._apply_metric_theme(self._modo)

    def set_label(self, text: str) -> None:
        self._label_lbl.setText(text or "")

    def set_value(self, text: str) -> None:
        self._value_lbl.setText(text or "—")

    def set_badge(self, text: str, variant: str = "default") -> None:
        if not text:
            self._badge_lbl.setVisible(False)
            return
        self._badge_lbl.setText(text)
        self._badge_lbl.setVisible(True)
        _tone_map = {
            "accent": "accent", "primary": "primary", "success": "success",
            "danger": "danger", "teal": "teal", "amber": "warning",
            "default": "ink_secondary",
        }
        color_key = _tone_map.get(variant, "ink_secondary")
        try:
            color = v3c(color_key, self._modo).name()
        except Exception:
            color = v3c("ink_secondary", self._modo).name()
        surf = v3c("surface2", self._modo).name()
        self._badge_lbl.setStyleSheet(
            f"color: {color}; background: {surf}; border-radius: 6px; padding: 2px 8px;"
        )

    def set_tone(self, token: str) -> None:
        self._tone = token
        self._apply_metric_theme(self._modo)

    def _apply_metric_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink2 = v3c("ink_secondary", self._modo).name()
        self._label_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        if self._tone:
            try:
                val_color = v3c(self._tone, self._modo).name()
            except Exception:
                val_color = v3c("ink_primary", self._modo).name()
        else:
            val_color = v3c("ink_primary", self._modo).name()
        self._value_lbl.setStyleSheet(f"color: {val_color}; background: transparent;")

# ── NMFormPanel ───────────────────────────────────────────────────────────────


class NMFormPanel(NMCard):
    """Formulario inline compacto con cuerpo de campos y footer de acciones fijo.

    Estructura: eyebrow/título → body (campos) → footer con botones.
    El footer siempre queda pegado al borde inferior de la card.

    Uso::
        form = NMFormPanel("Nuevo aviso", modo=modo)
        form.body_layout().addWidget(campo_widget)
        form.add_action("Cancelar", role="ghost", callback=form.hide)
        form.add_action("Guardar", role="primary", callback=on_save)
    """

    def __init__(self, title: str = "", eyebrow: str = "", modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._modo = norm_modo(modo or _tm().modo)
        self._action_buttons: list[QPushButton] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        self._eyebrow_lbl = QLabel(eyebrow or "")
        self._eyebrow_lbl.setFont(eyebrow_font())
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        lay.addWidget(self._eyebrow_lbl)

        self._title_lbl = QLabel(title or "")
        self._title_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        self._title_lbl.setVisible(bool(title))
        lay.addWidget(self._title_lbl)

        self._body_lay = QVBoxLayout()
        self._body_lay.setSpacing(V3_SP["sm"])
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._body_lay, stretch=1)

        self._sep = QWidget()
        self._sep.setFixedHeight(1)
        lay.addWidget(self._sep)

        self._footer_row = QHBoxLayout()
        self._footer_row.setSpacing(V3_SP["sm"])
        self._footer_row.setContentsMargins(0, V3_SP["xs"], 0, 0)
        self._footer_row.addStretch()
        lay.addLayout(self._footer_row)

        _tm().theme_changed.connect(self._apply_form_theme)
        self._apply_form_theme(self._modo)

    def body_layout(self) -> QVBoxLayout:
        return self._body_lay

    def footer_layout(self) -> QHBoxLayout:
        """Layout del footer — permite añadir widgets custom (p.ej. NMButton)."""
        return self._footer_row

    def add_action(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        """Agrega botón al footer. role: 'primary'|'secondary'|'ghost'|'danger'."""
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(80)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_row.addWidget(btn)
        self._action_buttons.append(btn)
        self._style_actions()
        return btn

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")
        self._title_lbl.setVisible(bool(text))

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def _style_actions(self) -> None:
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_on_acc = v3c("primary_ink", self._modo).name()
        text_m = v3c("text2", self._modo).name()
        text = v3c("text", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._action_buttons:
            role = btn.property("nm_role") or "secondary"
            if role == "primary":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; }}"
                )
            elif role == "danger":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_m}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )

    def _apply_form_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        sep_c = v3c("border", self._modo)
        sep_c.setAlpha(60)
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._sep.setStyleSheet(
            f"background: rgba({sep_c.red()},{sep_c.green()},{sep_c.blue()},60);"
        )
        self._style_actions()


class NMFeaturedCard(QFrame):
    """Card principal del Hub Dashboard con blob gradient de fondo.

    Muestra ánimo promedio como número grande + emoji + subtítulo.
    API: set_score(float, str), set_delta(float|None), set_meta(str), set_tags(list[tuple[str,str]])
    """

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(140)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("lg"), sp("md"), sp("lg"), sp("md"))
        lay.setSpacing(sp("xs") if hasattr(sp, "__call__") else 4)

        # Sub-label superior teal uppercase (ej. "Ánimo promedio · semana")
        self._title_lbl = QLabel("Ánimo promedio · semana")
        self._title_lbl.setFont(qfont("size_caption", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._title_lbl)

        # Fila: score grande + "/10" + emoji + delta pill
        score_row = QHBoxLayout()
        score_row.setSpacing(sp("sm"))
        self._score_lbl = QLabel("—")
        self._score_lbl.setFont(qfont("size_h1", bold=True))
        self._score_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._score_lbl)

        self._slash_lbl = QLabel("/ 10")
        self._slash_lbl.setFont(qfont("size_small"))
        self._slash_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._slash_lbl)

        self._emoji_lbl = QLabel("\U0001f610")
        self._emoji_lbl.setFont(qfont("size_h2"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._emoji_lbl)

        self._delta_lbl = QLabel()
        self._delta_lbl.setFont(qfont("size_caption", bold=True))
        self._delta_lbl.setVisible(False)
        score_row.addWidget(self._delta_lbl)

        score_row.addStretch()
        lay.addLayout(score_row)

        # Meta line: "N semanas en programa · Última sesión: hace X días"
        self._sub_lbl = QLabel()
        self._sub_lbl.setFont(qfont("size_small"))
        self._sub_lbl.setStyleSheet("background: transparent;")
        self._sub_lbl.setVisible(False)
        lay.addWidget(self._sub_lbl)

        # Tags row (pills) — FlowLayout: los chips envuelven en vez de desbordar.
        self._tags_widget = QWidget()
        self._tags_widget.setStyleSheet("background: transparent;")
        _tags_pol = self._tags_widget.sizePolicy()
        _tags_pol.setHeightForWidth(True)
        self._tags_widget.setSizePolicy(_tags_pol)
        self._tags_layout = FlowLayout(
            self._tags_widget, margin=0, spacing=sp("sm") if hasattr(sp, "__call__") else 8
        )  # 8px gap per F3.3
        self._tags_widget.setVisible(False)
        lay.addWidget(self._tags_widget)

        # Sparkline de área (tendencia semanal de ánimo). Va debajo de las
        # métricas para que la línea nunca cruce chips ni labels.
        self._spark = NMAreaSparkline(modo=self._modo)
        self._spark.setVisible(False)
        lay.addWidget(self._spark)

        lay.addStretch()

        self._last_delta = None  # cache para re-aplicar en cambio de tema

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_score(self, score: float, emoji: str = "\U0001f610"):
        self._score_lbl.setText(f"{score:.1f}")
        self._emoji_lbl.setText(emoji)
        self.update()

    def set_delta(self, delta):
        """Muestra pill con delta vs semana anterior. None oculta el pill."""
        self._last_delta = delta
        if delta is None:
            self._delta_lbl.setVisible(False)
            return
        sign = "↑" if delta >= 0 else "↓"
        text = f"{sign} {abs(delta):.1f} vs semana anterior"
        self._delta_lbl.setText(text)
        teal = C("teal", self._modo)
        amber = C("warning", self._modo)
        bg_color = _rgba(teal, 0.14) if delta >= 0 else _rgba(amber, 0.14)
        fg_color = teal if delta >= 0 else amber
        self._delta_lbl.setStyleSheet(
            f"QLabel {{ background: {bg_color}; color: {fg_color}; "
            f"border-radius: 10px; padding: 2px 8px; }}"
        )
        self._delta_lbl.setVisible(True)

    def set_series(self, data, labels=None):
        """Serie semanal de ánimo para el sparkline de área. Lista vacía la oculta."""
        if not data:
            self._spark.setVisible(False)
            return
        self._spark.set_series(data, labels)
        self._spark.setVisible(True)

    def set_meta(self, text: str):
        """Muestra línea gris con meta info (semanas, última sesión)."""
        if not text:
            self._sub_lbl.setVisible(False)
            return
        self._sub_lbl.setText(text)
        self._sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._sub_lbl.setVisible(True)

    def set_tags(self, tags):
        """tags: list[tuple[str, str]] donde str2 es 'teal'|'violet'|'accent'."""
        # Limpiar tags anteriores
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item is not None and item.widget():
                item.widget().deleteLater()
        if not tags:
            self._tags_widget.setVisible(False)
            return
        color_map = {
            "teal": ("teal", 0.14),
            "violet": ("violet", 0.14),
            "accent": ("accent", 0.14),
        }
        for label_text, color_key in tags[:3]:
            key, alpha = color_map.get(color_key, ("teal", 0.14))
            fg = C(key, self._modo)
            bg = _rgba(fg, alpha)
            chip = QLabel(label_text)
            chip.setFont(qfont("size_caption", bold=True))
            chip.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {fg}; "
                f"border-radius: 10px; padding: 2px 9px; }}"
            )
            self._tags_layout.addWidget(chip)
        self._tags_widget.setVisible(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        r = RADIUS_CARD
        is_dark = "dark" in self._modo
        surf_col = v3c("surfaceSolid" if is_dark else "surface", self._modo)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, surf_col)

        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.restore()
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        teal = C("teal", self._modo)
        self._title_lbl.setStyleSheet(
            f"color: {teal}; background: transparent;"
        )
        self._score_lbl.setStyleSheet(
            f"color: {C('text_primary', self._modo)}; background: transparent;"
        )
        self._slash_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        if self._sub_lbl.isVisible():
            self._sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        # Re-aplicar delta con los nuevos colores de tema
        if hasattr(self, "_last_delta"):
            self.set_delta(self._last_delta)
        self.update()

