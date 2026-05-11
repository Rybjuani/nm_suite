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
        # Backgrounds (del sitio dark premium)
        "bg_primary":       "#050911",
        "bg_secondary":     "#080c14",
        "bg_surface":       "#0e1421",
        "bg_elevated":      "#141c2e",
        "bg_overlay":       "#1a2340",
        "bg_glass":         "rgba(14,20,33,0.72)",
        "bg_input":         "#112740",

        # Acentos (teal vibrante + violeta neuro)
        "accent":           "#00d4c8",
        "accent_hover":     "#00b8ad",
        "accent_glow":      "rgba(0,212,200,0.25)",
        "violet":           "#7c5bf2",
        "violet_hover":     "#6245d6",
        "violet_glow":      "rgba(124,91,242,0.25)",

        # Texto
        "text_primary":     "#f0f4ff",
        "text_secondary":   "rgba(240,244,255,0.72)",
        "text_tertiary":    "rgba(240,244,255,0.45)",
        "text_on_accent":   "#050911",

        # Bordes y estados
        "border":           "rgba(255,255,255,0.10)",
        "border_accent":    "rgba(0,212,200,0.35)",
        "border_focus":     "#00d4c8",
        "success":          "#10b981",
        "warning":          "#f59e0b",
        "error":            "#ef4444",
        "info":             "#3b82f6",

        # Progress
        "progress_track":   "#1a3050",
        "progress_fill":    "#00d4c8",
    },

    # ============================================================
    # LIGHT HYBRID (Premium - Diurno / Preferencia usuario)
    # ============================================================
    "light_hybrid": {
        # Backgrounds (cream premium del white theme)
        "bg_primary":       "#f8fafc",
        "bg_secondary":     "#f1f5f9",
        "bg_surface":       "#ffffff",
        "bg_elevated":      "#e8eef6",
        "bg_overlay":       "#dde6f0",
        "bg_glass":         "rgba(255,255,255,0.75)",
        "bg_input":         "#ffffff",

        # Acentos (teal más profundo + violeta suave)
        "accent":           "#0891b2",
        "accent_hover":     "#0e7490",
        "accent_glow":      "rgba(8,145,178,0.20)",
        "violet":           "#7c3aed",
        "violet_hover":     "#6d28d9",
        "violet_glow":      "rgba(124,58,237,0.15)",

        # Texto (excelente contraste)
        "text_primary":     "#0f172a",
        "text_secondary":   "#334155",
        "text_tertiary":    "#64748b",
        "text_on_accent":   "#ffffff",

        # Bordes y estados
        "border":           "rgba(15,23,42,0.10)",
        "border_accent":    "rgba(8,145,178,0.40)",
        "border_focus":     "#0891b2",
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
    "radius_button":        8,
    "radius_card":          12,
    "radius_modal":         16,
    "radius_input":         8,
    "radius_badge":         20,
    "border_width":         1,
    "border_card_width":    2,
    "border_accent_width":  2,
    "border_button_width":  2,
    "header_height":        68,
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


def get_colors(modo: str = "dark_hybrid"):
    """Devuelve el diccionario de colores según el modo."""
    if modo not in COLORS:
        modo = "dark_hybrid"
    return COLORS[modo]


def get_gradient(modo: str = "dark_hybrid"):
    if "dark" in modo:
        return GRADIENTS["accent_teal_violet_dark"]
    return GRADIENTS["accent_teal_violet_light"]