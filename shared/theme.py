"""
NeuroMood Hybrid Unified Design System
Versión: 2.0 — Mayo 2026
Paleta fusionada premium (Dark + Light Híbrido)
Basado en el análisis del sitio + previews unificados
"""

COLORS = {
    # ============================================================
    # DARK HYBRID (Principal - Recomendado para sesiones largas)
    # ============================================================
    "dark_hybrid": {
        # Backgrounds — profundo como en refs (tXtGS, jTJrs, u8YFC)
        "bg_primary":       "#0d1117",   # era #050911 — ligeramente más claro, menos plano
        "bg_secondary":     "#0f1623",
        "bg_surface":       "#161d2e",   # era #0e1421 — más visible sobre bg_primary
        "bg_elevated":      "#1e2740",   # era #141c2e — cards elevadas más distinguibles
        "bg_overlay":       "#263354",
        "bg_glass":         "#161d2ebb", # con alpha para glassmorphism simulado
        "bg_input":         "#1a2235",

        # Acentos — exactamente como en refs (teal #00d4c8, violeta #7c5bf2)
        "accent":           "#00d4c8",
        "accent_hover":     "#00bfb5",
        "accent_glow":      "#003d3b",   # para simular glow en card borders
        "violet":           "#7c5bf2",
        "violet_hover":     "#6a4de0",
        "violet_glow":      "#2d1f5e",

        # Texto — alto contraste como en refs
        "text_primary":     "#f0f6ff",
        "text_secondary":   "#9aa5b8",
        "text_tertiary":    "#566175",
        "text_on_accent":   "#0d1117",

        # Bordes — sutiles pero presentes
        "border":           "#252e42",   # era #1E2229 — más visible
        "border_accent":    "#0d5259",
        "border_focus":     "#00d4c8",
        "border_card":      "#1e2d44",   # borde específico para cards

        # Estados semánticos
        "success":          "#10b981",
        "warning":          "#f59e0b",
        "error":            "#ef4444",
        "info":             "#3b82f6",

        # Progress
        "progress_track":   "#1a2d48",
        "progress_fill":    "#00d4c8",
    },

    # ============================================================
    # LIGHT HYBRID (Premium - Diurno / Preferencia usuario)
    # ============================================================
    "light_hybrid": {
        # Backgrounds — como en refs (wKY26, LdbzV, ZVpLC)
        "bg_primary":       "#f4f7fb",   # era #f8fafc — ligeramente más cálido
        "bg_secondary":     "#edf2f8",
        "bg_surface":       "#ffffff",
        "bg_elevated":      "#e8eef7",
        "bg_overlay":       "#dbe5f2",
        "bg_glass":         "#ffffffcc",
        "bg_input":         "#ffffff",

        # Acentos — teal más vibrante como en refs (#0891b2)
        "accent":           "#0891b2",
        "accent_hover":     "#0e7490",
        "accent_glow":      "#daf0f5",
        "violet":           "#7c3aed",
        "violet_hover":     "#6d28d9",
        "violet_glow":      "#ede9fe",

        # Texto
        "text_primary":     "#0f172a",
        "text_secondary":   "#334155",
        "text_tertiary":    "#64748b",
        "text_on_accent":   "#ffffff",

        # Bordes
        "border":           "#dde3ed",
        "border_accent":    "#a5d4e0",
        "border_focus":     "#0891b2",
        "border_card":      "#e4eaf4",

        # Estados
        "success":          "#059669",
        "warning":          "#d97706",
        "error":            "#dc2626",
        "info":             "#2563eb",

        # Progress
        "progress_track":   "#e2e8f0",
        "progress_fill":    "#0891b2",
    }
}

# ============================================================
# TOKENS ADICIONALES (compartidos)
# ============================================================
TYPOGRAPHY = {
    "font_family":      "Segoe UI",
    "font_fallback":    "Arial",
    "size_h1":          28,
    "size_h2":          22,
    "size_h3":          17,
    "size_body":        14,
    "size_small":       12,
    "size_caption":     11,
    "size_emoji":       64,   # emoji grande en módulos (ánimo, home icon grande)
    "size_emoji_sm":    22,   # emoji pequeño en cards del home
    "weight_regular":   "normal",
    "weight_medium":    "bold",
}

LAYOUT = {
    "padding_container":    24,
    "padding_card":         20,
    "padding_button_x":     24,
    "padding_button_y":     10,
    "gap_cards":            16,
    "gap_elements":         12,
    "radius_button":        10,   # era 8 — botones más redondeados como en refs
    "radius_card":          16,   # era 12 — cards más redondeadas como en refs
    "radius_modal":         20,
    "radius_input":         10,   # era 8
    "radius_badge":         20,
    "radius_pill":          24,   # para pills/chips de presets
    "border_width":         1,
    "border_card_width":    2,
    "border_accent_width":  2,
    "border_button_width":  2,
    "header_height":        56,   # era 68 — header más compacto como en refs
    "min_touch_target":     44,
}

# Gradientes (usar en canvas o como referencia para botones)
GRADIENTS = {
    "accent_teal_violet_dark":  ("#00d4c8", "#7c5bf2"),
    "accent_teal_violet_light": ("#0891b2", "#7c3aed"),
}

# Sombras recomendadas (para simular en CTkFrame)
SHADOWS = {
    "dark": {
        "card":         "0 12px 28px rgba(0,0,0,0.45)",
        "card_hover":   "0 20px 40px rgba(0,0,0,0.55), 0 0 1px rgba(0,212,200,0.10)",
        "glow_teal":    "0 0 24px rgba(0,212,200,0.30), 0 0 48px rgba(0,212,200,0.10)",
    },
    "light": {
        "card":         "0 4px 12px rgba(15,23,42,0.08), 0 8px 24px rgba(15,23,42,0.06)",
        "card_hover":   "0 8px 24px rgba(15,23,42,0.10), 0 16px 48px rgba(15,23,42,0.08)",
        "glow_teal":    "0 6px 20px rgba(8,145,178,0.25), 0 2px 8px rgba(8,145,178,0.15)",
    }
}

TRANSITIONS = {
    "fast":   150,
    "normal": 250,
    "slow":   350,
}


# Alias de compatibilidad
for _m in ("dark_hybrid", "light_hybrid"):
    COLORS[_m]["bg_hover"]      = COLORS[_m]["bg_overlay"]
    COLORS[_m]["bg_list_item"]  = COLORS[_m]["bg_elevated"]
    COLORS[_m]["accent_subtle"] = COLORS[_m]["bg_surface"]
    # border_card puede no existir en modos sin ella
    if "border_card" not in COLORS[_m]:
        COLORS[_m]["border_card"] = COLORS[_m]["border"]

# Aliases de compatibilidad (apps existentes usan "dark"/"light")
COLORS["dark"] = COLORS["dark_hybrid"]
COLORS["light"] = COLORS["light_hybrid"]


def get_colors(modo: str = "dark_hybrid"):
    """Devuelve el diccionario de colores según el modo."""
    if modo not in COLORS:
        modo = "dark_hybrid"
    return COLORS[modo]


def get_gradient(modo: str = "dark_hybrid"):
    if "dark" in modo:
        return GRADIENTS["accent_teal_violet_dark"]
    return GRADIENTS["accent_teal_violet_light"]


# Colores canónicos de categorías de activación conductual
CATEGORY_COLORS = {
    "Autocuidado": "#00d4c8",
    "Física":      "#22D47E",
    "Cognitiva":   "#9B8FE8",
    "Placer":      "#F0A500",
    "Social":      "#E8505B",
    "Maestría":    "#4A9EE8",
}