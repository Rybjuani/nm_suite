"""Layout helpers shared by Suite and Hub components."""

from __future__ import annotations

from PyQt6.QtWidgets import QSizePolicy, QWidget

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
