"""
NeuroMood Design System — v3 (Mayo 2026)

Fuente canónica: design_handoff_neuromood_v3/README.md

Esta versión expone DOS superficies en paralelo:

  • v3 (canónica, nueva)
        V3_LIGHT / V3_DARK ........... paletas con gradiente firma teal → violet
        MOOD_PALETTE ................. 10 niveles emocionales (NMMoodEmoji, V3MoodSlider)
        V3_SPACE / V3_RADIUS ......... escala estructural
        V3_SHADOWS ................... params para QGraphicsDropShadowEffect
        V3_GRADIENTS ................. paradas para QLinearGradient
        get_v3_palette() / get_mood() / v3_mode() / icon_stroke_width()

  • Legacy (compat — no tocar aún)
        COLORS["dark_hybrid"|"light_hybrid"|"dark"|"light"]   re-mapeada a v3
        TYPOGRAPHY / LAYOUT / GRADIENTS / SHADOWS / CATEGORY_COLORS
        norm_modo() / get_colors() / get_gradient()

Los 16 consumidores actuales (theme_qt.py, components_qt.py, pantallas) siguen
funcionando contra los nombres legacy; obtienen los valores v3 sin refactor.
"""

# ============================================================
# V3 · Paletas canónicas
# ============================================================

V3_LIGHT = {
    # Backgrounds
    "bg":              "#eef2f8",
    "bgAlt":           "#e6ecf5",
    "bgSidebar":       "#ffffff",
    "surface":         "#ffffff",
    "elevated":        "#f5f7fb",

    # Borders
    "border":          "#e3e9f1",
    "borderSoft":      "#eef1f6",
    "borderStrong":    "#cdd5e2",

    # Text
    "text":            "#0f172a",
    "text2":           "#475569",
    "text3":           "#94a3b8",
    "text4":           "#cbd5e1",

    # Gradiente firma teal → violet
    "gradFrom":        "#2dd4bf",
    "gradMid":         "#5eead4",
    "gradTo":          "#a855f7",

    # Slashbar emocional (no varía con theme)
    "moodGradFrom":    "#2dd4bf",
    "moodGradMid":     "#5eead4",
    "moodGradTo":      "#a855f7",

    # Tonos
    "teal":            "#14b8a6",
    "tealSoft":        "#d3f5ef",
    "violet":          "#a855f7",
    "violetSoft":      "#ede5fc",
    "cyan":            "#06b6d4",
    "cyanSoft":        "#cef3f9",

    # Semánticos
    "success":         "#10b981",
    "successSoft":     "#d1fae5",
    "warning":         "#f59e0b",
    "warningSoft":     "#fef3c7",
    "danger":          "#ef4444",
    "dangerSoft":      "#fee2e2",

    # Streak
    "streak":          "#f97316",
    "streakSoft":      "#ffedd5",
}

V3_DARK = {
    # Backgrounds
    "bg":              "#060912",
    "bgAlt":           "#0a0f1f",
    "bgSidebar":       "#0a0f1f",
    # Translúcidos (Qt no soporta rgba en todos los QSS): se ofrece la
    # variante *Solid como fallback para stylesheets.
    "surface":         "rgba(18, 25, 45, 0.7)",
    "surfaceSolid":    "#121c2d",
    "elevated":        "rgba(30, 41, 65, 0.6)",
    "elevatedSolid":   "#1e2941",

    "border":          "rgba(94, 234, 212, 0.10)",
    "borderSoft":      "rgba(255, 255, 255, 0.06)",
    "borderStrong":    "rgba(94, 234, 212, 0.25)",
    "borderSolid":     "#23314a",

    "text":            "#f1f5f9",
    "text2":           "#94a3b8",
    "text3":           "#64748b",
    "text4":           "#475569",

    "gradFrom":        "#22d3ee",
    "gradMid":         "#5eead4",
    "gradTo":          "#c084fc",

    "moodGradFrom":    "#22d3ee",
    "moodGradMid":     "#5eead4",
    "moodGradTo":      "#c084fc",

    "teal":            "#5eead4",
    "tealSoft":        "rgba(20, 184, 166, 0.18)",
    "tealSoftSolid":   "#103631",
    "violet":          "#c084fc",
    "violetSoft":      "rgba(168, 85, 247, 0.20)",
    "violetSoftSolid": "#2a1843",
    "cyan":            "#22d3ee",
    "cyanSoft":        "rgba(6, 182, 212, 0.18)",
    "cyanSoftSolid":   "#0f2e36",

    "success":         "#34d399",
    "successSoft":     "rgba(16, 185, 129, 0.20)",
    "warning":         "#fbbf24",
    "warningSoft":     "rgba(245, 158, 11, 0.20)",
    "danger":          "#f87171",
    "dangerSoft":      "rgba(239, 68, 68, 0.20)",

    "streak":          "#fb923c",
    "streakSoft":      "rgba(249, 115, 22, 0.18)",
}


# ============================================================
# MOOD_PALETTE · 10 niveles emocionales
# Consumido por NMMoodEmoji y V3MoodSlider (componentes nuevos)
# ============================================================

MOOD_PALETTE = {
    1:  {"from": "#5b6cb8", "to": "#3a4585", "glow": "#5b6cb8", "name": "Devastada"},
    2:  {"from": "#6c84d6", "to": "#445a9e", "glow": "#6c84d6", "name": "Muy triste"},
    3:  {"from": "#7ba8e6", "to": "#4c7cc4", "glow": "#7ba8e6", "name": "Triste"},
    4:  {"from": "#9eb4d8", "to": "#6a87b6", "glow": "#9eb4d8", "name": "Decaída"},
    5:  {"from": "#f5d76a", "to": "#daa520", "glow": "#f5d76a", "name": "Neutral"},
    6:  {"from": "#aee279", "to": "#7eb83a", "glow": "#aee279", "name": "Bien"},
    7:  {"from": "#5dd6a3", "to": "#1da678", "glow": "#5dd6a3", "name": "Contenta"},
    8:  {"from": "#36cfb8", "to": "#0d8f7f", "glow": "#36cfb8", "name": "Feliz"},
    9:  {"from": "#34cfd1", "to": "#7a72d8", "glow": "#7a72d8", "name": "Muy feliz"},
    10: {"from": "#a78bfa", "to": "#ec4899", "glow": "#c084fc", "name": "Eufórica"},
}


# ============================================================
# Tokens estructurales v3
# ============================================================

V3_SPACE  = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32, "xxxl": 48}
V3_RADIUS = {"sm": 6, "md": 10, "lg": 14, "xl": 18, "xxl": 22, "pill": 999}

# Shadows en formato consumible por QGraphicsDropShadowEffect:
#   blur (px), offset (dx, dy), color (r, g, b, a 0-255)
V3_SHADOWS = {
    "light": {
        "sm":   {"blur":  4, "offset": (0, 1),  "color": (15, 23, 42, 10)},
        "md":   {"blur": 16, "offset": (0, 4),  "color": (15, 23, 42, 15)},
        "card": {"blur": 12, "offset": (0, 4),  "color": (15, 23, 42, 13)},
        "ring": {"blur": 20, "offset": (0, 4),  "color": (20, 184, 166, 76)},
    },
    "dark": {
        "sm":   {"blur":  8, "offset": (0, 2),  "color": (0, 0, 0, 102)},
        "md":   {"blur": 24, "offset": (0, 8),  "color": (0, 0, 0, 127)},
        "card": {"blur": 30, "offset": (0, 10), "color": (0, 0, 0, 115)},
        "glow": {"blur": 40, "offset": (0, 0),  "color": (94, 234, 212, 46)},
    },
}

# Paradas para QLinearGradient (firma teal → violet)
V3_GRADIENTS = {
    "light": [("#2dd4bf", 0.0), ("#5eead4", 0.5), ("#a855f7", 1.0)],
    "dark":  [("#22d3ee", 0.0), ("#5eead4", 0.5), ("#c084fc", 1.0)],
}


# ============================================================
# Tipografía v3 (expandida; compatible con keys v2)
# ============================================================

TYPOGRAPHY = {
    "font_family":   "Plus Jakarta Sans, DM Sans, system-ui, sans-serif",
    "font_family_fallback_chain": [
        "Plus Jakarta Sans", "DM Sans", "Segoe UI", "Arial",
    ],
    "font_fallback": "DM Sans",
    "font_mono":     "JetBrains Mono",

    # Escala v3 (px)
    "size_display":    28,
    "size_h1":         24,
    "size_h2":         18,
    "size_h3":         15,
    "size_body":       13,
    "size_small":      12,
    "size_caption":    11,
    "size_caption_xs": 10,

    # Tamaños heredados (mantenidos por compat)
    "size_emoji":      64,
    "size_emoji_sm":   22,
    "size_time_large": 20,
    "size_time_timer": 18,

    # Pesos numéricos v3
    "weight_regular":  400,
    "weight_medium":   500,
    "weight_semibold": 600,
    "weight_bold":     700,

    # Letter spacing
    "tracking_tight":   "-.02em",
    "tracking_normal":  "0",
    "tracking_eyebrow": ".15em",
}


# ============================================================
# Layout · keys históricos preservados, valores actualizados a v3
# ============================================================

LAYOUT = {
    "padding_container":   24,    # v3 xl
    "padding_card":        20,
    "padding_button_x":    20,
    "padding_button_y":    10,
    "gap_cards":           12,
    "gap_elements":        12,

    # Botones pill (v3) — antes 10
    "radius_button":       999,
    "radius_card":         14,    # v3 lg
    "radius_modal":        22,    # v3 xxl
    "radius_input":        10,    # v3 md
    "radius_badge":        999,
    "radius_pill":         999,
    "radius_small":        6,

    "checkbox_size":       18,
    "border_width":        1,
    "border_card_width":   1,
    "border_accent_width": 2,
    "border_button_width": 1,

    "header_height":       56,    # v3 — antes 44
    "min_touch_target":    44,

    # Opacidades heredadas
    "aura_opacity_dark":   0.18,
    "aura_opacity_light":  0.10,
    "blob_opacity_dark":   0.22,
    "blob_opacity_light":  0.18,

    # Umbrales rings
    "ring_good_threshold": 80,
    "ring_mid_threshold":  50,

    # v3 extras
    "sidebar_width":       240,
}


def icon_stroke_width(size: int) -> float:
    """Grosor de stroke para NMIcon SVG según tamaño (README v3)."""
    if size <= 14: return 1.4
    if size <= 18: return 1.5
    if size <= 24: return 1.6
    if size <= 32: return 1.7
    if size <= 48: return 1.8
    return 2.0


# ============================================================
# COLORS · bridge legacy → v3
# Cada modo expone las claves v3 + las claves v2 históricas re-mapeadas.
# Para QSS (que no soporta rgba en todos los properties), las claves
# legacy apuntan a las variantes …Solid donde existe.
# ============================================================

def _bridge_dark():
    v = dict(V3_DARK)
    v.update({
        # Backgrounds legacy
        "bg_primary":   V3_DARK["bg"],
        "bg_secondary": V3_DARK["bgAlt"],
        "bg_surface":   V3_DARK["surfaceSolid"],
        "bg_elevated":  V3_DARK["elevatedSolid"],
        "bg_overlay":   "#2a3554",
        "bg_glass":     V3_DARK["surfaceSolid"] + "bb",
        "bg_input":     V3_DARK["surfaceSolid"],

        # Acentos legacy (mapeo al tono dominante v3)
        "accent":       V3_DARK["teal"],
        "accent_hover": V3_DARK["cyan"],
        "accent_glow":  V3_DARK["tealSoftSolid"],
        "violet_hover": "#a855f7",
        "violet_glow":  V3_DARK["violetSoftSolid"],
        "teal_hover":   "#22d3ee",

        # Texto legacy
        "text_primary":   V3_DARK["text"],
        "text_secondary": V3_DARK["text2"],
        "text_tertiary":  V3_DARK["text3"],
        "text_on_accent": "#0b1220",   # texto oscuro sobre gradient claro

        # Bordes legacy (sólidos para QSS)
        "border":        V3_DARK["borderSolid"],
        "border_accent": "#2f4767",
        "border_focus":  V3_DARK["teal"],
        "border_card":   V3_DARK["borderSolid"],

        # Semánticos legacy
        "error": V3_DARK["danger"],
        "info":  "#5fa1ff",

        "progress_track": V3_DARK["surfaceSolid"],
        "progress_fill":  V3_DARK["teal"],

        # Tokens v2/v3 ya existentes en el codebase
        "sidebar_bg":             V3_DARK["bgSidebar"],
        "streak_color":           V3_DARK["streak"],
        "streak_bg":              "#2a1a0a",
        "tcc_heat_cold":          "#3b82f6",
        "tcc_heat_hot":           "#ef4444",
        "routine_morning_tint":   "#fbbf24",
        "routine_afternoon_tint": "#f97316",
        "routine_night_tint":     "#6366f1",
        "cat_autocuidado_color":  "#22c55e",
        "cat_social_color":       "#f59e0b",
        "hub_blob_teal":          V3_DARK["teal"],
        "hub_blob_violet":        V3_DARK["violet"],
        "sync_orb_green":         "#22c55e",
        "uninstall_danger":       V3_DARK["danger"],
        "installer_terminal_bg":  "#060d1a",
    })
    return v


def _bridge_light():
    v = dict(V3_LIGHT)
    v.update({
        "bg_primary":   V3_LIGHT["bg"],
        "bg_secondary": V3_LIGHT["bgAlt"],
        "bg_surface":   V3_LIGHT["surface"],
        "bg_elevated":  V3_LIGHT["elevated"],
        "bg_overlay":   "#dde4ee",
        "bg_glass":     "#ffffffcc",
        "bg_input":     V3_LIGHT["surface"],

        "accent":       V3_LIGHT["teal"],
        "accent_hover": "#0d9488",
        "accent_glow":  V3_LIGHT["tealSoft"],
        "violet_hover": "#9333ea",
        "violet_glow":  V3_LIGHT["violetSoft"],
        "teal_hover":   "#0d9488",

        "text_primary":   V3_LIGHT["text"],
        "text_secondary": V3_LIGHT["text2"],
        "text_tertiary":  V3_LIGHT["text3"],
        "text_on_accent": "#ffffff",

        "border":        V3_LIGHT["border"],
        "border_accent": V3_LIGHT["borderStrong"],
        "border_focus":  V3_LIGHT["teal"],
        "border_card":   V3_LIGHT["border"],

        # Light usa semánticos algo más oscuros para contraste sobre #ffffff
        "success": "#16a34a",
        "warning": "#d97706",
        "error":   "#dc2626",
        "info":    "#2563eb",

        "progress_track": V3_LIGHT["border"],
        "progress_fill":  V3_LIGHT["teal"],

        "sidebar_bg":             V3_LIGHT["bgSidebar"],
        "streak_color":           V3_LIGHT["streak"],
        "streak_bg":              V3_LIGHT["streakSoft"],
        "tcc_heat_cold":          "#3b82f6",
        "tcc_heat_hot":           "#ef4444",
        "routine_morning_tint":   "#fbbf24",
        "routine_afternoon_tint": "#f97316",
        "routine_night_tint":     "#4f46e5",
        "cat_autocuidado_color":  "#16a34a",
        "cat_social_color":       "#d97706",
        "hub_blob_teal":          V3_LIGHT["teal"],
        "hub_blob_violet":        V3_LIGHT["violet"],
        "sync_orb_green":         "#16a34a",
        "uninstall_danger":       "#dc2626",
        "installer_terminal_bg":  "#060d1a",
    })
    return v


COLORS = {
    "dark_hybrid":  _bridge_dark(),
    "light_hybrid": _bridge_light(),
}

# Alias cortos
COLORS["dark"]  = COLORS["dark_hybrid"]
COLORS["light"] = COLORS["light_hybrid"]

# Compat extras heredados
for _m in ("dark_hybrid", "light_hybrid"):
    COLORS[_m]["bg_hover"]      = COLORS[_m]["bg_overlay"]
    COLORS[_m]["bg_list_item"]  = COLORS[_m]["bg_elevated"]
    COLORS[_m]["accent_subtle"] = COLORS[_m]["bg_surface"]
    if "border_card" not in COLORS[_m]:
        COLORS[_m]["border_card"] = COLORS[_m]["border"]


# ============================================================
# GRADIENTS · ahora con la firma v3 (teal → violet)
# ============================================================

GRADIENTS = {
    "dark_hybrid": [
        ("#22d3ee", 0.0),
        ("#5eead4", 0.5),
        ("#c084fc", 1.0),
    ],
    "light_hybrid": [
        ("#2dd4bf", 0.0),
        ("#5eead4", 0.5),
        ("#a855f7", 1.0),
    ],
    # Pares (start, end) usados por algunos builders
    "accent_teal_violet_dark":  ("#22d3ee", "#c084fc"),
    "accent_teal_violet_light": ("#2dd4bf", "#a855f7"),
}


# ============================================================
# SHADOWS · strings CSS-like preservados (consumidores existentes)
# ============================================================

SHADOWS = {
    "dark": {
        "card":       "0 10px 30px rgba(0,0,0,0.45)",
        "card_hover": "0 16px 40px rgba(0,0,0,0.55), 0 0 1px rgba(94,234,212,0.18)",
        "glow_teal":  "0 0 40px rgba(94,234,212,0.18), 0 0 16px rgba(94,234,212,0.10)",
    },
    "light": {
        "card":       "0 4px 12px rgba(15,23,42,0.05), 0 1px 2px rgba(15,23,42,0.04)",
        "card_hover": "0 12px 28px rgba(15,23,42,0.06), 0 4px 10px rgba(15,23,42,0.04)",
        "glow_teal":  "0 4px 20px rgba(20,184,166,0.30)",
    },
}


TRANSITIONS = {
    "fast":   150,
    "normal": 250,
    "slow":   350,
}


# ============================================================
# Helpers
# ============================================================

def norm_modo(modo: str = "dark_hybrid") -> str:
    """Normaliza alias legacy de modo."""
    if modo == "dark":
        return "dark_hybrid"
    if modo == "light":
        return "light_hybrid"
    return modo if modo in ("dark_hybrid", "light_hybrid") else "dark_hybrid"


def v3_mode(modo: str = "dark_hybrid") -> str:
    """Devuelve 'light' o 'dark' a partir de cualquier alias."""
    return "light" if norm_modo(modo) == "light_hybrid" else "dark"


def get_colors(modo: str = "dark_hybrid"):
    """Devuelve el diccionario de colores según el modo (incluye claves v3 + legacy)."""
    return COLORS[norm_modo(modo)]


def get_v3_palette(modo: str = "dark"):
    """Devuelve V3_LIGHT o V3_DARK según el modo (solo claves v3 puras)."""
    return V3_LIGHT if v3_mode(modo) == "light" else V3_DARK


def get_gradient(modo: str = "dark_hybrid"):
    return GRADIENTS.get(norm_modo(modo), GRADIENTS["dark_hybrid"])


def get_mood(level: int):
    """Devuelve el descriptor MOOD_PALETTE clampeado a [1, 10]."""
    lv = max(1, min(10, int(level)))
    return MOOD_PALETTE[lv]


# ============================================================
# Categorías de activación conductual (sin cambios — tokens estables)
# ============================================================

CATEGORY_COLORS = {
    "Autocuidado": "#22c55e",  # green  — salud, autocuidado
    "Física":      "#14b8a6",  # teal   — movimiento, energía
    "Cognitiva":   "#22d3ee",  # cyan   — mente, claridad
    "Placer":      "#a855f7",  # violet — disfrute, creatividad
    "Social":      "#f59e0b",  # amber  — calidez, conexión
    "Maestría":    "#6366f1",  # indigo — logro, habilidades
}
