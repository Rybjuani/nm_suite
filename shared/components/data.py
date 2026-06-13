"""Data display primitives shared by Suite and Hub."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QLabel


class NMElidedLabel(QLabel):
    """QLabel de una línea que elide con "…" en vez de empujar el layout.

    Para textos informativos en filas/heros con ancho disputado: no impone
    mínimo horizontal (Ignored) y pinta el texto elidido a su ancho real,
    con tooltip del texto completo cuando recorta. Evita el patrón "el label
    no entra → Qt fuerza geometrías bajo el mínimo → widgets superpuestos".
    """

    def __init__(self, text: str = "", parent=None):
        self._full_text = text
        super().__init__(text, parent)

    # NO usar sizePolicy Ignored: QBoxLayout le asigna slot de ancho 0 al
    # item (aun con minimumWidth explícito) y el widget "salta" a su mínimo
    # pintándose ENCIMA del vecino. Con policy normal + minimumSizeHint chico
    # el layout puede comprimir sin superponer.
    def sizeHint(self):  # noqa: N802 — override de QLabel
        fm = QFontMetrics(self.font())
        base = super().sizeHint()
        return QSize(fm.horizontalAdvance(self._full_text) + 4, base.height())

    def minimumSizeHint(self):  # noqa: N802
        base = super().minimumSizeHint()
        return QSize(24, base.height())

    def setText(self, text: str):  # noqa: N802 — override de QLabel
        self._full_text = text
        super().setText(text)
        self.updateGeometry()
        self._elide()

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        self._elide()

    def _elide(self):
        fm = QFontMetrics(self.font())
        avail = max(0, self.width() - 2)
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, avail)
        if super().text() != elided:
            super().setText(elided)
        self.setToolTip(self._full_text if elided != self._full_text else "")
