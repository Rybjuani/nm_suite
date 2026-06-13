"""Surface primitives shared by Suite and Hub."""

from __future__ import annotations

from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from shared.theme_manager import ThemeManager
from shared.theme_qt import norm_modo, v3c


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


class NMDivider(QWidget):
    """Separador token-driven. orient='h' o 'v', opacity 0-255.

    Uso:
        layout.addWidget(NMDivider())                  # horizontal sutil
        row.addWidget(NMDivider(orient="v", alpha=80)) # vertical
    """

    def __init__(
        self, orient: str = "h", alpha: int = 60, inset: int = 0, modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._orient = "v" if orient == "v" else "h"
        self._alpha = max(0, min(255, int(alpha)))
        self._inset = max(0, int(inset))
        if self._orient == "h":
            self.setFixedHeight(1)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedWidth(1)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        _tm().theme_changed.connect(self._apply_theme)

    def paintEvent(self, event):
        p = QPainter(self)
        col = v3c("border", self._modo)
        col.setAlpha(self._alpha)
        p.setPen(QPen(col, 1.0))
        if self._orient == "h":
            y = self.height() // 2
            p.drawLine(self._inset, y, self.width() - self._inset, y)
        else:
            x = self.width() // 2
            p.drawLine(x, self._inset, x, self.height() - self._inset)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()
