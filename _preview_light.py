"""
_preview_light.py — Preview light theme · Notion visual identity completa
Lanzar: python _preview_light.py
No modifica ningún archivo del proyecto.
"""
import sys, os
_base = os.path.dirname(os.path.abspath(__file__))
if _base not in sys.path:
    sys.path.insert(0, _base)

# ══════════════════════════════════════════════════════════════════════════════
# PALETA COMPLETA — Notion light mode
#
# Fondos/superficies:
#   body       → #E3E2DE  (Notion Cream — beige cálido)
#   cards      → #F7F7F5  (Notion Light Gray)
#   header     → #FFFFFF  (blanco — elevado)
#   inputs     → #FFFFFF
#   hover      → #EEEEEC
#
# Texto:
#   primario   → #191919  (Notion Text Default)
#   secundario → #4A4A4A
#   terciario  → #6B6B6B  (Notion Dark Gray)
#
# Bordes:
#   estándar   → #CBCAC7  @ 2px  (Notion Mid Gray — VISIBLE)
#
# Interactivos (Notion usa negro como color de acción, no teal):
#   accent     → #191919  (botones primarios, slider fill, switch activo)
#   hover      → #000000
#   subtle     → #19191910
#
# Estados funcionales: paleta Notion (red/orange/green)
# ══════════════════════════════════════════════════════════════════════════════
import shared.theme as _theme

_BODY_BG = "#E3E2DE"

_NOTION_LIGHT = {
    "bg_primary":    "#FFFFFF",
    "bg_secondary":  "#F7F7F5",
    "bg_surface":    "#F7F7F5",
    "bg_input":      "#FFFFFF",
    "bg_hover":      "#EEEEEC",
    "bg_list_item":  "#FFFFFF",

    # Interactivos: negro Notion — reemplaza el teal en todos los elementos
    "accent":        "#191919",
    "accent_hover":  "#000000",
    "accent_subtle": "#19191910",

    "text_primary":  "#191919",
    "text_secondary":"#4A4A4A",
    "text_tertiary": "#6B6B6B",
    "text_on_accent":"#FFFFFF",

    "border":        "#CBCAC7",
    "border_accent": "#191919",
    "border_focus":  "#191919",

    # Estados funcionales — colores Notion de contenido
    "success":       "#0F7B6C",
    "warning":       "#D9730D",
    "error":         "#E03E3E",
    "info":          "#0B6E99",

    "progress_track":"#CBCAC7",
    "progress_fill": "#191919",
}

_theme.COLORS["light"] = _NOTION_LIGHT

# Bordes 2px → claramente visibles en cards
_theme.LAYOUT["border_width"] = 2

# ══════════════════════════════════════════════════════════════════════════════
# LANZAR APP — sin cambios en captionbar (title bar oscura original)
# ══════════════════════════════════════════════════════════════════════════════
import customtkinter as ctk
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

from shared.db import inicializar_tablas
inicializar_tablas()

from apps.termometro.main import TermometroApp


class PreviewLightApp(TermometroApp):
    def __init__(self):
        super().__init__()
        self.after(60, self._activar_light)

    def _activar_light(self):
        self._toggle_modo()
        self.title("PREVIEW · Light Theme — Notion Interactive")
        self.after(40, lambda: self.configure(fg_color=_BODY_BG))


if __name__ == "__main__":
    app = PreviewLightApp()
    app.mainloop()
