"""Layout helpers shared by Suite and Hub components."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout, QSizePolicy, QWidget

# Breakpoints documentados (ancho de viewport)
BREAKPOINTS = {"xs": 640, "sm": 960, "md": 1280, "lg": 1600}


def h_spacer() -> QWidget:
    """Spacer horizontal expandible."""
    widget = QWidget()
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return widget


def responsive_columns(
    available_width: int, min_card_width: int = 280, max_columns: int = 3
) -> int:
    """Devuelve el número óptimo de columnas según ancho disponible.

    Breakpoints documentados:
        xs < 640   → 1 columna (móvil / ventana muy pequeña)
        sm < 960   → hasta 2 columnas
        md < 1280  → hasta 3 columnas
        lg < 1600  → hasta max_columns
        xl >= 1600 → max_columns
    """
    if available_width < BREAKPOINTS["xs"]:
        return 1
    if available_width < BREAKPOINTS["sm"]:
        return min(2, max_columns)
    cols = max(1, min(max_columns, available_width // min_card_width))
    return cols


def responsive_breakpoint(width: int) -> str:
    """Devuelve el nombre del breakpoint activo para el ancho dado."""
    if width < BREAKPOINTS["xs"]:
        return "xs"
    if width < BREAKPOINTS["sm"]:
        return "sm"
    if width < BREAKPOINTS["md"]:
        return "md"
    if width < BREAKPOINTS["lg"]:
        return "lg"
    return "xl"


class FlowLayout(QLayout):
    """Layout que acomoda los items en filas y los envuelve a la línea siguiente
    cuando no entran en el ancho disponible (patrón estándar de Qt).

    Pensado para grupos de chips/badges que no deben desbordar ni recortarse a
    anchos chicos (regla anti-solape del HANDOFF §3). Implementa
    ``heightForWidth`` para que el contenedor reserve el alto correcto al envolver.
    """

    def __init__(self, parent=None, margin: int = 0, spacing: int = 6):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._items = []

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only: bool):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        right = rect.right() - m.right()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            w, h = hint.width(), hint.height()
            next_x = x + w
            if next_x > right and line_height > 0:
                x = rect.x() + m.left()
                y = y + line_height + self._spacing
                next_x = x + w
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x + self._spacing
            line_height = max(line_height, h)
        return y + line_height - rect.y() + m.bottom()

