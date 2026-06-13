"""Input components shared by Suite and Hub."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, pyqtProperty
from PyQt6.QtGui import QBrush, QColor, QPaintEvent, QPainter
from PyQt6.QtWidgets import QAbstractButton

from shared.theme_manager import ThemeManager
from shared.theme_qt import norm_modo, v3c


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


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
