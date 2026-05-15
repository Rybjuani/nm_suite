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
        # Backgrounds — alineados con mockup V3 (--bg:#0f172a, --surface:#1e293b)
        "bg_primary":       "#0f172a",
        "bg_secondary":     "#12192a",
        "bg_surface":       "#1e293b",
        "bg_elevated":      "#334155",
        "bg_overlay":       "#3d4f68",
        "bg_glass":         "#1e293bbb",
        "bg_input":         "#1e293b",

        # Acentos — indigo + teal + violet
        "accent":           "#6366f1",
        "accent_hover":     "#4f52d4",
        "accent_glow":      "#1e1f5e",
        "violet":           "#a855f7",
        "violet_hover":     "#9333ea",
        "violet_glow":      "#2d1060",
        "teal":             "#14b8a6",
        "teal_hover":       "#0d9488",
        "cyan":             "#22d3ee",

        # Texto — --tp:#f1f5f9, --ts:#94a3b8, --tm:#64748b
        "text_primary":     "#f1f5f9",
        "text_secondary":   "#94a3b8",
        "text_tertiary":    "#64748b",
        "text_on_accent":   "#ffffff",

        # Bordes — equivalentes opacos del mockup rgba(255,255,255,.09/.15)
        "border":           "#334155",
        "border_accent":    "#3d4f68",
        "border_focus":     "#6366f1",
        "border_card":      "#334155",

        # Estados semánticos
        "success":          "#22c55e",
        "warning":          "#f59e0b",
        "error":            "#ef4444",
        "info":             "#3b82f6",

        # Progress
        "progress_track":   "#1e293b",
        "progress_fill":    "#6366f1",

        # ── Tokens nuevos (Design System v3 — Mayo 2026) ──────────────────────
        # Hub sidebar
        "sidebar_bg":             "#12192a",
        # Streak badge (🔥)
        "streak_color":           "#fb923c",
        "streak_bg":              "#2a1a0a",
        # TCC heat bar
        "tcc_heat_cold":          "#3b82f6",
        "tcc_heat_hot":           "#ef4444",
        # Routine section tints — usar al 6-8% de opacidad en stylesheets
        "routine_morning_tint":   "#fbbf24",
        "routine_afternoon_tint": "#f97316",
        "routine_night_tint":     "#6366f1",
        # Actividades
        "cat_autocuidado_color":  "#22c55e",
        "cat_social_color":       "#f59e0b",
        # Hub dashboard blobs
        "hub_blob_teal":          "#14b8a6",
        "hub_blob_violet":        "#a855f7",
        # Estado de sincronización
        "sync_orb_green":         "#22c55e",
        # Instaladores
        "uninstall_danger":       "#ef4444",
        "installer_terminal_bg":  "#060d1a",
    },

    # ============================================================
    # LIGHT HYBRID (Premium - Diurno / Preferencia usuario)
    # ============================================================
    "light_hybrid": {
        # Backgrounds — alineados con mockup V3 (--bg:#f8fafc, --surface:#fff)
        "bg_primary":       "#f8fafc",
        "bg_secondary":     "#f1f5f9",
        "bg_surface":       "#ffffff",
        "bg_elevated":      "#f1f5f9",
        "bg_overlay":       "#e2e8f0",
        "bg_glass":         "#ffffffcc",
        "bg_input":         "#f8fafc",

        # Acentos — indigo oscuro para modo claro
        "accent":           "#4f46e5",
        "accent_hover":     "#4338ca",
        "accent_glow":      "#daf0f5",
        "violet":           "#7c3aed",
        "violet_hover":     "#6d28d9",
        "violet_glow":      "#ede9fe",
        "teal":             "#0d9488",
        "teal_hover":       "#0f766e",
        "cyan":             "#06b6d4",

        # Texto — --tp:#0f172a, --ts:#475569, --tm:#94a3b8
        "text_primary":     "#0f172a",
        "text_secondary":   "#475569",
        "text_tertiary":    "#94a3b8",
        "text_on_accent":   "#ffffff",

        # Bordes — rgba(0,0,0,.08) sobre #f8fafc ≈ #e4e9ef
        "border":           "#e2e8f0",
        "border_accent":    "#cbd5e1",
        "border_focus":     "#4f46e5",
        "border_card":      "#e2e8f0",

        # Estados
        "success":          "#16a34a",
        "warning":          "#d97706",
        "error":            "#dc2626",
        "info":             "#2563eb",

        # Progress
        "progress_track":   "#e2e8f0",
        "progress_fill":    "#4f46e5",

        # ── Tokens nuevos (Design System v3 — Mayo 2026) ──────────────────────
        # Hub sidebar
        "sidebar_bg":             "#f1f5f9",
        # Streak badge (🔥)
        "streak_color":           "#ea580c",
        "streak_bg":              "#fff7ed",
        # TCC heat bar
        "tcc_heat_cold":          "#3b82f6",
        "tcc_heat_hot":           "#ef4444",
        # Routine section tints — usar al 6-8% de opacidad en stylesheets
        "routine_morning_tint":   "#fbbf24",
        "routine_afternoon_tint": "#f97316",
        "routine_night_tint":     "#4f46e5",
        # Actividades
        "cat_autocuidado_color":  "#16a34a",
        "cat_social_color":       "#d97706",
        # Hub dashboard blobs
        "hub_blob_teal":          "#0d9488",
        "hub_blob_violet":        "#7c3aed",
        # Estado de sincronización
        "sync_orb_green":         "#16a34a",
        # Instaladores (siempre dark — no aplica, valores de fallback)
        "uninstall_danger":       "#dc2626",
        "installer_terminal_bg":  "#060d1a",
    }
}

# ============================================================
# TOKENS ADICIONALES (compartidos)
# ============================================================
TYPOGRAPHY = {
    "font_family":      "DM Sans",
    "font_fallback":    "Arial",
    "font_mono":        "JetBrains Mono",   # timers, contadores, terminal del installer
    "size_h1":          22,
    "size_h2":          18,
    "size_h3":          15,
    "size_body":        13,
    "size_small":       12,
    "size_caption":     11,
    "size_emoji":       64,   # emoji grande en módulos (ánimo, home icon grande)
    "size_emoji_sm":    22,   # emoji pequeño en cards del home
    "size_time_large":  20,   # hora en NMAvisoCard y countdown de respiración (pt)
    "size_time_timer":  18,   # MM:SS en NMFocusArc del timer (pt)
    "weight_regular":   "normal",
    "weight_medium":    "bold",
}

LAYOUT = {
    "padding_container":    18,
    "padding_card":         14,
    "padding_button_x":     20,
    "padding_button_y":     8,
    "gap_cards":            10,
    "gap_elements":         12,
    "radius_button":        10,
    "radius_card":          12,
    "radius_modal":         20,
    "radius_input":         10,
    "radius_badge":         20,
    "radius_pill":          20,   # para pills/chips de presets
    "radius_small":         6,    # row items, badges pequeños, separadores
    "checkbox_size":        18,   # indicador de QCheckBox
    "border_width":         1,
    "border_card_width":    2,
    "border_accent_width":  2,
    "border_button_width":  2,
    "header_height":        56,   # era 68 — header más compacto como en refs
    "min_touch_target":     44,
    # ── Tokens de opacidad (Design System v3 — Mayo 2026) ─────────────────
    "aura_opacity_dark":    0.18,  # SessionColor aura radial en dark mode
    "aura_opacity_light":   0.10,  # SessionColor aura radial en light mode
    "blob_opacity_dark":    0.22,  # Blob gradient en Hub Featured Card (dark)
    "blob_opacity_light":   0.18,  # Blob gradient en Hub Featured Card (light)
    # ── Umbrales para progress rings ──────────────────────────────────────
    "ring_good_threshold":  80,    # ≥80% → teal (buen progreso)
    "ring_mid_threshold":   50,    # 50-79% → accent, <50% → violet
}

# Gradientes (usar en canvas o como referencia para botones)
GRADIENTS = {
    "dark_hybrid": [
        ("#6366f1", 0.0),
        ("#14b8a6", 0.45),
        ("#a855f7", 1.0),
    ],
    "light_hybrid": [
        ("#4f46e5", 0.0),
        ("#0d9488", 0.45),
        ("#9333ea", 1.0),
    ],
    "accent_teal_violet_dark":  ("#6366f1", "#a855f7"),
    "accent_teal_violet_light": ("#4f46e5", "#9333ea"),
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


def norm_modo(modo: str = "dark_hybrid") -> str:
    """Normaliza alias legacy de modo."""
    if modo == "dark":
        return "dark_hybrid"
    if modo == "light":
        return "light_hybrid"
    return modo if modo in ("dark_hybrid", "light_hybrid") else "dark_hybrid"


def get_colors(modo: str = "dark_hybrid"):
    """Devuelve el diccionario de colores según el modo."""
    return COLORS[norm_modo(modo)]


def get_gradient(modo: str = "dark_hybrid") -> list:
    return GRADIENTS.get(norm_modo(modo), GRADIENTS["dark_hybrid"])


# Colores canónicos de categorías de activación conductual (v3 — Mayo 2026)
CATEGORY_COLORS = {
    "Autocuidado": "#22c55e",  # green  — salud, autocuidado
    "Física":      "#14b8a6",  # teal   — movimiento, energía
    "Cognitiva":   "#22d3ee",  # cyan   — mente, claridad
    "Placer":      "#a855f7",  # violet — disfrute, creatividad
    "Social":      "#f59e0b",  # amber  — calidez, conexión
    "Maestría":    "#6366f1",  # indigo — logro, habilidades
}
