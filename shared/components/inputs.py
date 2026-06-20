"""Input components shared by Suite and Hub."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, pyqtProperty
from PyQt6.QtGui import QBrush, QColor, QPaintEvent, QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton, QComboBox, QPushButton

from shared.theme_manager import ThemeManager
from shared.theme_qt import focus_ring_stylesheet, norm_modo, qfont, stylesheet_combobox, v3_shadow, v3c

try:
    from shared.icons_svg import has_icon as _has_v3_icon, nm_svg_pixmap as _nm_svg_pixmap
except ImportError:
    try:
        from icons_svg import has_icon as _has_v3_icon, nm_svg_pixmap as _nm_svg_pixmap  # type: ignore
    except ImportError:
        _nm_svg_pixmap = None
        _has_v3_icon = lambda _n: False  # noqa: E731


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


class NMSelect(QComboBox):
    """QComboBox themed según runtime spec §4.3."""

    def __init__(self, parent=None, modo: str | None = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setMinimumHeight(36)
        self.setFont(qfont("size_body"))
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(stylesheet_combobox(self._modo))


class NMToggle(QAbstractButton):
    """
    Toggle switch custom: píldora redondeada con círculo deslizante.
    QPropertyAnimation sobre posición X del círculo en 200ms OutCubic.
    """

    def __init__(self, parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        # v3: track 42×24, thumb 9px (deja 3px margin top/bot)
        self._track_w = 42
        self._track_h = 24
        self._thumb_r = 9
        self._thumb_x = float(self._thumb_r + 3)

        self.setCheckable(True)
        self.setFixedSize(self._track_w, self._track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Toggle")

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

        r = self._track_h // 2
        track_rect = QRectF(0, 0, self._track_w, self._track_h)
        is_dark = "dark" in self._modo

        # Track
        if self.isChecked():
            # F5 runtime: track `primary` SÓLIDO, sin halo (antes gradiente
            # firma + glow teal alrededor).
            p.setBrush(QBrush(v3c("primary", self._modo)))
        else:
            # Inactivo: text4 en light (#cbd5e1 — spec JSX), borderSolid en dark
            track_col = v3c("text4", self._modo) if not is_dark else v3c("borderSolid", self._modo)
            p.setBrush(QBrush(track_col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(track_rect, r, r)

        # Thumb (knob blanco) — sombra suave solo cuando activo (v3 spec)
        ty = self._track_h / 2
        if self.isChecked():
            shadow_col = QColor(0, 0, 0, 50)
            p.setBrush(QBrush(shadow_col))
            p.drawEllipse(QPointF(self._thumb_x, ty + 1), self._thumb_r, self._thumb_r)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(self._thumb_x, ty), self._thumb_r, self._thumb_r)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMPlayButton ─────────────────────────────────────────────────────────────


class NMPlayButton(QPushButton):
    """Botón circular minimal para controles de player (play/pause/stop/skip/refresh).

    Spec README v3:
      - Tamaños sm/md/lg → diámetro 40/48/56.
      - Background ``surface`` (neutro), border ``borderSoft`` sutil,
        sombra suave ``v3_shadow("sm")``.
      - **Sin gradient**, **sin texto**. Solo icono SVG centrado.
      - Hover: fondo ``elevated`` + border ``borderStrong``.

    Args:
        icon_name: nombre del icono SVG v3 ("play"/"pause"/"stop"/"skip"/"refresh").
        size:      "sm" / "md" / "lg".
        modo:      override de tema.
    """

    _SIZE_MAP = {"sm": 40, "md": 46, "lg": 58}

    def __init__(self, icon_name: str = "play", size: str = "md", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._icon_name = icon_name
        self._size_key = size if size in self._SIZE_MAP else "md"
        self._hover = False
        diameter = self._SIZE_MAP[self._size_key]
        self.setFixedSize(diameter, diameter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._disabled = False
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    # ── API ──────────────────────────────────────────────────────────────────

    def set_icon(self, name: str):
        if name != self._icon_name:
            self._icon_name = name
            self.update()

    def icon_name(self) -> str:
        return self._icon_name

    def set_size(self, size: str):
        if size in self._SIZE_MAP and size != self._size_key:
            self._size_key = size
            d = self._SIZE_MAP[size]
            self.setFixedSize(d, d)
            self.update()

    # ── eventos ──────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ── paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = "dark" in self._modo
        d = self.width()
        rect = QRectF(1, 1, d - 2, d - 2)
        is_main = self._size_key == "lg"

        # Background surface (elevated en hover)
        if is_main:
            bg = v3c("brandStrong" if self._hover else "primary", self._modo)
        else:
            surf_key = (
                "elevatedSolid"
                if (self._hover and is_dark)
                else "elevated"
                if self._hover
                else "surfaceSolid"
                if is_dark
                else "surface"
            )
            bg = v3c(surf_key, self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(rect)

        # Border sutil
        if is_main:
            border = QColor(0, 0, 0, 0)
        else:
            border = v3c("brandLine" if self._hover else "line", self._modo)
        p.setPen(QPen(border, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(0.5, 0.5, d - 1, d - 1))

        # Icono SVG centrado
        if _nm_svg_pixmap is not None and _has_v3_icon(self._icon_name):
            icon_size = 22 if is_main else 20
            color_key = "primary_ink" if is_main else ("text" if self._hover else "text2")
            color = v3c(color_key, self._modo).name()
            pix = _nm_svg_pixmap(self._icon_name, color, icon_size)
            if pix is not None and not pix.isNull():
                px = (d - icon_size) // 2
                p.drawPixmap(px, px, pix)
        p.end()

    # ── theme ────────────────────────────────────────────────────────────────

    def _apply_shadow(self):
        eff = v3_shadow("shadow_1", self._modo, parent=self)
        self.setGraphicsEffect(eff)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        if not self._disabled and self.isEnabled():
            self._apply_shadow()
        self.update()
