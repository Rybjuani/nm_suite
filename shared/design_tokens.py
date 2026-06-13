"""
shared/design_tokens.py
========================
Design tokens canonicales para NeuroMood — la UNICA fuente de verdad para colores,
tipografía, espaciado y componentes. NO leer PNG ni inventar valores.

Los agentes DEBEN usar los tokens de este archivo para cualquier decisión visual.
Para código PyQt6, usar los helpers de shared.theme_qt (C, qcolor, qfont, etc.)

===
LIGHT THEME — Linen + Sage
========================
"""

from __future__ import annotations

# ── Paleta Light ───────────────────────────────────────────────────────────────
LIGHT = {
    # ── Backgrounds ──────────────────────────────────────────────────────────
    "bg_canvas": "#F4EFE5",  # Lienzo principal (linen cálido)
    "bg_sidebar": "#ECE5D4",  # Sidebar / bandas estructurales
    "bg_surface": "#FBF8F1",  # Cards, paneles, contenedores
    "bg_surface2": "#ECE5D4",  # Inputs, superficies anidadas
    "bg_input": "#ECE5D4",  # Campos de texto
    "bg_hover": "rgba(48, 90, 72, 0.04)",  # Hover state
    # ── Text ───────────────────────────────────────────────────────────────
    "ink_primary": "#1C2218",  # Texto principal (forest green oscuro)
    "ink_secondary": "#6B7770",  # Labels, texto secundario
    "ink_placeholder": "#9A9A90",  # Placeholder
    "ink_disabled": "#A8A697",  # Estados deshabilitados
    # ── Primary & Accent ────────────────────────────────────────────────────
    "primary": "#305A48",  # Sage — CTA, estados activos
    "primary_soft": "rgba(48, 90, 72, 0.08)",  # Hover/selected bg
    "accent": "#B8633B",  # Terracotta — secundario
    "accent_soft": "rgba(184, 99, 59, 0.08)",  # Hover secundario
    # ── Status Colors ───────────────────────────────────────────────────────
    "teal": "#2F7E73",  # Teal — estados positivos, éxito
    "amber": "#C68A2E",  # Oro — progreso, energía
    "violet": "#B8633B",  # Terracotta — categorías (same as accent)
    "lavender": "#B8633B",  # Alias para compatibilidad
    # ── Semantic ───────────────────────────────────────────────────────────
    "success_bg": "#E8F0EA",
    "success_ink": "#4B7F52",
    "warning_bg": "#F9F2E3",
    "warning_ink": "#B08C4A",
    "danger_bg": "#F5E8E8",
    "danger_ink": "#A94442",
    "info_bg": "#E6F0F2",
    "info_ink": "#50858B",
    # ── Borders ─────────────────────────────────────────────────────────────
    "border": "rgba(28, 34, 24, 0.08)",
    "border_strong": "rgba(28, 34, 24, 0.15)",
    "border_solid": "#DFDBCF",
    "border_focus": "#305A48",  # Sage
    # ── Shadows ─────────────────────────────────────────────────────────────
    "shadow_color": "rgba(28, 34, 24, 0.08)",
    # ── Category Colors (Activación Conductual) ───────────────────────────
    "cat_autocuidado": "#4D7A52",  # Verde — salud
    "cat_fisica": "#2F7E73",  # Teal — movimiento
    "cat_cognitiva": "#305A48",  # Sage — mente
    "cat_placer": "#B8633B",  # Terracotta — disfrute
    "cat_social": "#C68A2E",  # Oro — conexión
    "cat_maestria": "#A99CFF",  # Lavender — logro (dark primary)
    # ── Alias canónicos ─────────────────────────────────────────────────────
    "bg_0": "#F4EFE5",
    "bg_1": "#ECE5D4",
    "surface": "#FBF8F1",
    "surface_2": "#ECE5D4",
    "canvas": "#F4EFE5",
    "card": "#FBF8F1",
    "sidebar": "#ECE5D4",
    "ink": "#1C2218",
    "sage": "#305A48",
    "terracotta": "#B8633B",
    "aqua": "#2F7E73",
    "line": "rgba(28, 34, 24, 0.08)",
    "line_strong": "rgba(28, 34, 24, 0.15)",
}


"""
========================
DARK THEME — Indigo Profundo
========================
"""
DARK = {
    # ── Backgrounds ──────────────────────────────────────────────────────────
    "bg_canvas": "#07091A",  # Indigo profundo
    "bg_sidebar": "#0E132B",  # Sidebar / zonas estructurales
    "bg_surface": "#141A38",  # Cards, paneles, contenedores
    # Campos/anidados: tono sidebar (#0E132B), NO canvas puro — sobre una card
    # #141A38 el canvas se leía como bloque negro duro ("campos pesados",
    # rechazo owner). El ADN no fija color de input; esta es la lectura calma.
    "bg_surface2": "#0E132B",
    "bg_input": "#0E132B",
    "bg_hover": "rgba(255, 255, 255, 0.06)",  # Hover state
    # ── Text ───────────────────────────────────────────────────────────────
    "ink_primary": "#ECECFB",  # Lavanda claro (off-white)
    "ink_secondary": "#8285A8",  # Slate muted (= theme.V3_DARK textMuted; F4 cerró la divergencia)
    "ink_placeholder": "#4A4D60",  # Placeholder
    "ink_disabled": "#555977",  # Estados deshabilitados
    # ── Primary & Accent ────────────────────────────────────────────────────
    "primary": "#A99CFF",  # Lavanda — CTA, estados activos (dark)
    "primary_soft": "rgba(169, 156, 255, 0.10)",  # Hover/selected bg
    "accent": "#5EE0C7",  # Aqua/turquesa — secundario
    "accent_soft": "rgba(94, 224, 199, 0.14)",  # Hover secundario
    # ── Status Colors ───────────────────────────────────────────────────────
    "teal": "#5EE0C7",  # Aqua — información/acento
    "green": "#60B89A",  # Verde — éxito, estados positivos
    "amber": "#E8B86A",  # Oro cálido — progreso
    "violet": "#5EE0C7",  # Aqua (same as accent en dark)
    "lavender": "#A99CFF",  # Primary
    # ── Semantic ───────────────────────────────────────────────────────────
    "success_bg": "#0D2A26",
    "success_ink": "#60B89A",
    "warning_bg": "#2A2210",
    "warning_ink": "#E8B86A",
    "danger_bg": "#2A1015",
    "danger_ink": "#FF8A7A",
    "info_bg": "#0D2333",
    "info_ink": "#5EE0C7",
    # ── Borders ─────────────────────────────────────────────────────────────
    "border": "rgba(255, 255, 255, 0.06)",
    "border_strong": "rgba(255, 255, 255, 0.12)",
    "border_solid": "#232740",
    "border_focus": "#A99CFF",  # Lavender
    # ── Shadows ─────────────────────────────────────────────────────────────
    "shadow_color": "rgba(0, 0, 0, 0.30)",
    # ── Category Colors ───────────────────────────────────────────────────
    "cat_autocuidado": "#60B89A",  # Verde
    "cat_fisica": "#5EE0C7",  # Aqua
    "cat_cognitiva": "#A99CFF",  # Lavender
    "cat_placer": "#E8B86A",  # Oro
    "cat_social": "#E8B86A",  # Oro
    "cat_maestria": "#A99CFF",  # Lavender
    # ── Alias canónicos ─────────────────────────────────────────────────────
    "bg_0": "#07091A",
    "bg_1": "#0E132B",
    "surface": "#141A38",
    "surface_2": "#0E132B",
    "canvas": "#07091A",
    "card": "#141A38",
    "sidebar": "#0E132B",
    "ink": "#ECECFB",
    "deep": "#07091A",
    "sage": "#A99CFF",
    "terracotta": "#5EE0C7",
    "aqua": "#5EE0C7",
    "line": "rgba(255, 255, 255, 0.06)",
    "line_strong": "rgba(255, 255, 255, 0.12)",
}


"""
========================
MOOD PALETTE — 10 niveles emocionales
========================
Usar MOOD_PALETTE[nivel]['from'] y MOOD_PALETTE[nivel]['to'] para gradientes.
MOOD_PALETTE[nivel]['name'] para labels.
"""
MOOD_PALETTE = {
    1: {"from": "#5b6cb8", "to": "#3a4585", "glow": "#5b6cb8", "name": "Devastada"},
    2: {"from": "#6c84d6", "to": "#445a9e", "glow": "#6c84d6", "name": "Muy triste"},
    3: {"from": "#7ba8e6", "to": "#4c7cc4", "glow": "#7ba8e6", "name": "Triste"},
    4: {"from": "#9eb4d8", "to": "#6a87b6", "glow": "#9eb4d8", "name": "Decaída"},
    5: {"from": "#f5d76a", "to": "#daa520", "glow": "#f5d76a", "name": "Neutral"},
    6: {"from": "#aee279", "to": "#7eb83a", "glow": "#aee279", "name": "Bien"},
    7: {"from": "#5dd6a3", "to": "#1da678", "glow": "#5dd6a3", "name": "Contenta"},
    8: {"from": "#36cfb8", "to": "#0d8f7f", "glow": "#36cfb8", "name": "Feliz"},
    9: {"from": "#34cfd1", "to": "#7a72d8", "glow": "#7a72d8", "name": "Muy feliz"},
    10: {"from": "#a78bfa", "to": "#ec4899", "glow": "#c084fc", "name": "Eufórica"},
}


"""
========================
TYPOGRAPHY — Escala tipográfica
========================
"""
TYPOGRAPHY = {
    # Familias (cargadas desde assets/fonts/ — ver shared/fonts.py)
    "font_serif": "Newsreader",  # Display, títulos, números bienestar
    "font_sans": "Manrope",  # UI, body, labels
    "font_mono": "JetBrains Mono",  # Timestamps, IDs técnicos
    # Tamaños (pt para QFont)
    "size_display_xl": 40,  # Bienvenida onboarding (hero contenido)
    "size_display_l": 30,  # Títulos principales contenidos
    "size_display_m": 26,  # Headers de sección
    "size_heading_l": 20,  # UI headers
    "size_heading_m": 16,  # Sub-headers
    "size_body": 14,  # Body text
    "size_caption": 12,  # Timestamps, metadata
    "size_eyebrow": 11,  # Labels compactos sin tracking forzado
    "size_mono": 12,  # Mono para datos técnicos
    # Alias históricos (mantenidos por compatibilidad)
    "displayM": 26,  # Headers de sección (serif)
    "headingL": 20,  # UI headers (sans)
    "headingM": 16,  # Sub-headers (sans)
    "body": 14,  # Body text
    "caption": 12,  # Timestamps, metadata
    "eyebrow": 11,  # Labels compactos
    "mono": 12,  # Mono para datos técnicos
    # ── Alias históricos ───────────────────────────────────────────────────────
    "h1": 20,  # alias de headingL
    "h2": 16,  # alias de headingM
    "h3": 14,  # alias de body
    "sm": 12,  # alias de caption
    "size_small": 12,  # alias de caption
    "size_display": 28,  # legacy (mantenido por compat)
    "size_caption_xs": 11,  # alias de eyebrow
    # Pesos
    "weight_regular": 400,
    "weight_medium": 500,
    "weight_semibold": 600,
    "weight_bold": 700,
}


"""
========================
SPACING — Sistema de espaciado
========================
"""
SPACING = {
    "xs": 4,  # Muy pequeño
    "sm": 6,  # Pequeño
    "md": 10,  # Medio
    "lg": 14,  # Grande
    "xl": 16,  # Extra grande
    "2xl": 20,  # 2XL ADN
    "3xl": 24,  # 3XL ADN
    "xxl": 20,  # XXL
    "xxxl": 24,  # XXXL (padding containers)
    "4xl": 32,  # Máximo estructural ADN
}


"""
========================
LAYOUT — Dimensiones clave
========================
"""
LAYOUT = {
    "sidebar_width": 200,  # px — sidebar fija
    "card_gap": 12,  # gap entre cards
    "card_padding": 20,  # padding interno cards
    "container_padding": 24,  # padding secciones principales
    "radius_card": 16,  # cards ADN
    "radius_button": 999,  # botones/chips pill
    "radius_input": 12,  # inputs
    "radius_modal": 22,  # modales
    "header_height": 56,  # altura header
    "min_touch_target": 44,  # touch target mínimo (WCAG)
}


"""
========================
RADIUS — Radios de borde
========================
"""
RADIUS = {
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 16,
    "xxl": 22,  # Modales
    "pill": 999,  # Botones/chips pill
    "card": 16,
    "modal": 22,
    "input": 12,
    "circle": 9999,
}


"""
========================
SHADOWS — Parámetros para QGraphicsDropShadowEffect
========================
"""
# Formato: {"blur": px, "offset": (dx, dy), "color": (r, g, b, a 0-255)}
SHADOWS = {
    "light": {
        "sm": {"blur": 12, "offset": (0, 4), "color": (28, 34, 24, 10)},
        "md": {"blur": 32, "offset": (0, 12), "color": (28, 34, 24, 18)},
        "lg": {"blur": 64, "offset": (0, 24), "color": (28, 34, 24, 26)},
    },
    "dark": {
        "sm": {"blur": 12, "offset": (0, 4), "color": (0, 0, 0, 76)},
        "md": {"blur": 40, "offset": (0, 16), "color": (0, 0, 0, 102)},
        "lg": {"blur": 80, "offset": (0, 32), "color": (0, 0, 0, 130)},
    },
}


"""
========================
HELPERS — Funciones de conveniencia
========================
"""


def get_token(key: str, theme: str = "dark") -> str:
    """Obtener valor de token por nombre.

    Args:
        key:   Nombre del token (ej: 'primary', 'bg_surface', 'ink')
        theme: 'light' o 'dark'
    Returns:
        Valor hex del token
    """
    pal = LIGHT if theme == "light" else DARK
    return pal.get(key, "#888888")


def get_mood(level: int) -> dict:
    """Obtener mood palette para nivel 1-10.

    Returns:
        dict con 'from', 'to', 'glow', 'name'
    """
    lv = max(1, min(10, int(level)))
    return MOOD_PALETTE[lv]


# ── Accesores rápidos para uso en código ────────────────────────────────────────
def primary(theme: str = "dark") -> str:
    return DARK["primary"] if theme == "dark" else LIGHT["primary"]


def accent(theme: str = "dark") -> str:
    return DARK["accent"] if theme == "dark" else LIGHT["accent"]


def bg_canvas(theme: str = "dark") -> str:
    return DARK["bg_canvas"] if theme == "dark" else LIGHT["bg_canvas"]


def bg_surface(theme: str = "dark") -> str:
    return DARK["bg_surface"] if theme == "dark" else LIGHT["bg_surface"]


def ink_primary(theme: str = "dark") -> str:
    return DARK["ink_primary"] if theme == "dark" else LIGHT["ink_primary"]


def ink_secondary(theme: str = "dark") -> str:
    return DARK["ink_secondary"] if theme == "dark" else LIGHT["ink_secondary"]
