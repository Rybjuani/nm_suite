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
    # ── Sage Linen — paleta light renovada (2026) ─────────────────────────────
    # Eje sage clinical + warm terracotta. Las CLAVES legacy se preservan; los
    # valores se re-mapean (p. ej. "violet" → terracotta cálida, "cyan" → sage
    # profundo) para no romper los consumidores históricos del bridge.

    # Backgrounds
    "bg":              "#f6f3ec",  # Warm linen — fondo principal
    "bgAlt":           "#ece8dc",  # Soft sand
    "bgSoft":          "#ece8dc",
    "bgSidebar":       "#fbf9f3",  # Sidebar diferenciado del card
    "surface":         "#ffffff",  # Card surface — blanco puro
    "elevated":        "#fafaf6",  # Elevated subtle warm white
    "surfaceElevated": "#fafaf6",
    "surfaceGlass":    "rgba(255, 255, 255, 0.78)",

    # Borders
    "border":          "#dcd6c6",  # Visible warm stone
    "borderSoft":      "#e8e2d2",
    "borderStrong":    "#c7bea8",

    # Text
    "text":            "#1c241f",  # Deep forest
    "textMuted":       "#566159",  # Muted forest
    "text2":           "#566159",
    "text3":           "#8a958e",
    "text4":           "#c5cfc9",

    # Accent — Sage clinical (primario) + Terracotta (cálido secundario)
    "accent":          "#2f6e62",  # Sage clinical
    "accentSoft":      "#dcebe6",  # Sage soft tint
    "gradFrom":        "#2f6e62",  # Sage → Soft pine (monocromático)
    "gradMid":         "#3f8278",
    "gradTo":          "#4a8a7e",

    # Slashbar emocional (no varía con theme)
    "moodGradFrom":    "#2f6e62",
    "moodGradMid":     "#5f9ea0",
    "moodGradTo":      "#b86844",

    # Tonos (claves legacy re-mapeadas a la nueva paleta)
    "teal":            "#2f6e62",  # = accent (sage)
    "tealSoft":        "#dcebe6",
    "violet":          "#b86844",  # Terracotta (warm secondary, antes copper)
    "violetSoft":      "#f3e0d6",  # Terracotta soft
    "cyan":            "#1e5a52",  # Deeper sage
    "cyanSoft":        "#cee0d9",

    # Semánticos
    "success":         "#3a8060",  # Clinical green
    "successSoft":     "#d1eadd",
    "warning":         "#c47e2b",  # Muted amber
    "warningSoft":     "#f3e6d5",
    "danger":          "#b8423e",  # Brick muted
    "dangerSoft":      "#f4d7d6",

    # Streak (re-mapeado a terracotta para coherencia con warm secondary)
    "streak":          "#b86844",
    "streakSoft":      "#f3e0d6",

    # Warm secondary (alias explícito del eje cálido)
    "warm":            "#b86844",
    "warmSoft":        "#f3e0d6",
}

V3_DARK = {
    # ── Indigo Mist — paleta dark renovada (2026) ─────────────────────────────
    # Eje aqua mist + warm amber. Superficies SÓLIDAS (sin rgba translúcido en
    # surface) para evitar artefactos de rasterización Qt. Las claves legacy se
    # preservan; "violet" se re-mapea a amber, "cyan" a un aqua intermedio.

    # Backgrounds
    "bg":              "#0e1322",  # Indigo profundo
    "bgAlt":           "#141a2d",  # Capa intermedia
    "bgSoft":          "#141a2d",
    "bgSidebar":       "#0b1020",  # Sidebar más profundo
    "surface":         "#161d33",  # Sólido (antes rgba translúcido)
    "surfaceSolid":    "#161d33",
    "elevated":        "#1c2540",
    "surfaceElevated": "#1c2540",
    "elevatedSolid":   "#1c2540",
    "surfaceGlass":    "rgba(22, 29, 51, 0.85)",

    # Borders
    "border":          "rgba(106, 215, 196, 0.14)",  # Aqua undertone sutil
    "borderSoft":      "rgba(255, 255, 255, 0.06)",
    "borderStrong":    "rgba(106, 215, 196, 0.30)",
    "borderSolid":     "#20294a",

    # Text
    "text":            "#e8ecf2",  # Warm white
    "textMuted":       "#9aa3b3",
    "text2":           "#9aa3b3",
    "text3":           "#6c7585",
    "text4":           "#4a5263",

    # Accent — Aqua mist (primario) + Amber light (cálido secundario)
    "accent":          "#6ad7c4",  # Aqua mist
    "accentSoft":      "rgba(106, 215, 196, 0.18)",
    "gradFrom":        "#6ad7c4",  # Aqua → Mint (monocromático)
    "gradMid":         "#82e0d0",
    "gradTo":          "#95e6d7",

    "moodGradFrom":    "#6ad7c4",
    "moodGradMid":     "#5f9ea0",
    "moodGradTo":      "#f5b873",

    # Tonos (claves legacy re-mapeadas a la nueva paleta)
    "teal":            "#6ad7c4",  # = accent (aqua mist)
    "tealSoft":        "rgba(106, 215, 196, 0.18)",
    "tealSoftSolid":   "#1d3a3c",
    "violet":          "#f5b873",  # Amber light (warm secondary, antes magenta)
    "violetSoft":      "rgba(245, 184, 115, 0.18)",
    "violetSoftSolid": "#3a2f1f",
    "cyan":            "#82e0d0",  # Aqua intermedio
    "cyanSoft":        "rgba(130, 224, 208, 0.18)",
    "cyanSoftSolid":   "#1d3a3c",

    # Semánticos
    "success":         "#5cbf8d",
    "successSoft":     "rgba(92, 191, 141, 0.18)",
    "warning":         "#f5b873",
    "warningSoft":     "rgba(245, 184, 115, 0.18)",
    "danger":          "#e07b6e",  # Brick suave
    "dangerSoft":      "rgba(224, 123, 110, 0.18)",

    # Streak (re-mapeado a amber para coherencia con warm secondary)
    "streak":          "#f5b873",
    "streakSoft":      "rgba(245, 184, 115, 0.18)",

    # Warm secondary (alias explícito del eje cálido)
    "warm":            "#f5b873",
    "warmSoft":        "rgba(245, 184, 115, 0.18)",
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
        "sm":   {"blur":  4, "offset": (0, 1),  "color": (28, 36, 31, 10)},
        "md":   {"blur": 18, "offset": (0, 6),  "color": (28, 36, 31, 18)},
        "card": {"blur": 14, "offset": (0, 4),  "color": (28, 36, 31, 14)},
        "lg":   {"blur": 28, "offset": (0, 10), "color": (28, 36, 31, 22)},
        "ring": {"blur": 20, "offset": (0, 4),  "color": (47, 110, 98, 76)},   # sage glow
    },
    "dark": {
        "sm":   {"blur":  8, "offset": (0, 2),  "color": (0, 0, 0, 102)},
        "md":   {"blur": 24, "offset": (0, 8),  "color": (0, 0, 0, 127)},
        "card": {"blur": 30, "offset": (0, 10), "color": (0, 0, 0, 130)},
        "lg":   {"blur": 44, "offset": (0, 14), "color": (0, 0, 0, 150)},
        "glow": {"blur": 40, "offset": (0, 0),  "color": (106, 215, 196, 56)}, # aqua mist glow
    },
}

# Paradas para QLinearGradient — gradiente firma monocromático en ambos temas
# Light: sage (#2f6e62) → soft pine (#4a8a7e)
# Dark:  aqua mist (#6ad7c4) → mint (#95e6d7)
V3_GRADIENTS = {
    "light": [("#2f6e62", 0.0), ("#3f8278", 0.5), ("#4a8a7e", 1.0)],
    "dark":  [("#6ad7c4", 0.0), ("#82e0d0", 0.5), ("#95e6d7", 1.0)],
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

    # Escala v3 renovada (px) — body sube a 14 para accesibilidad clínica;
    # h1 baja a 22 para una jerarquía más elegante (display sigue siendo 28).
    "size_display":    28,
    "size_h1":         22,
    "size_h2":         18,
    "size_h3":         15,
    "size_body":       14,
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
        "bg_overlay":   "#222b46",        # ajustado al nuevo undertone indigo
        "bg_glass":     V3_DARK["surfaceSolid"] + "d9",
        "bg_input":     V3_DARK["surfaceSolid"],

        # Acentos legacy (mapeo a la nueva firma aqua + amber)
        "accent":       V3_DARK["teal"],          # aqua mist
        "accent_hover": V3_DARK["cyan"],          # aqua intermedio
        "accent_glow":  V3_DARK["tealSoftSolid"],
        "violet_hover": "#f8c989",                # amber hover (alineado al warm secondary)
        "violet_glow":  V3_DARK["violetSoftSolid"],
        "teal_hover":   V3_DARK["cyan"],          # = #82e0d0

        # Texto legacy
        "text_primary":   V3_DARK["text"],
        "text_secondary": V3_DARK["text2"],
        "text_tertiary":  V3_DARK["text3"],
        "text_on_accent": "#0e1322",     # bg color — texto oscuro sobre aqua

        # Bordes legacy (sólidos para QSS)
        "border":        V3_DARK["borderSolid"],
        "border_accent": "#2d4458",      # aqua undertone solid
        "border_focus":  V3_DARK["teal"],
        "border_card":   V3_DARK["borderSolid"],

        # Semánticos legacy
        "error": V3_DARK["danger"],
        "info":  "#7db0ff",              # cool blue muted

        "progress_track": V3_DARK["surfaceSolid"],
        "progress_fill":  V3_DARK["teal"],

        # Tokens v2/v3 ya existentes en el codebase
        "sidebar_bg":             V3_DARK["bgSidebar"],
        "streak_color":           V3_DARK["streak"],        # amber
        "streak_bg":              "#2a1f0e",                # amber undertone deep
        "tcc_heat_cold":          "#5d8acd",                # slate blue muted
        "tcc_heat_hot":           V3_DARK["danger"],        # brick suave
        "routine_morning_tint":   "#f5b873",                # amber morning
        "routine_afternoon_tint": "#e07b6e",                # brick afternoon
        "routine_night_tint":     "#6ad7c4",                # aqua night
        "cat_autocuidado_color":  "#5cbf8d",
        "cat_social_color":       "#f5b873",
        "hub_blob_teal":          V3_DARK["teal"],
        "hub_blob_violet":        V3_DARK["violet"],        # amber re-mapeado
        "sync_orb_green":         "#5cbf8d",
        "uninstall_danger":       V3_DARK["danger"],
        "installer_terminal_bg":  "#070b18",
    })
    return v


def _bridge_light():
    v = dict(V3_LIGHT)
    v.update({
        "bg_primary":   V3_LIGHT["bg"],
        "bg_secondary": V3_LIGHT["bgAlt"],
        "bg_surface":   V3_LIGHT["surface"],
        "bg_elevated":  V3_LIGHT["elevated"],
        "bg_overlay":   "#e3dfd3",         # warm linen overlay
        "bg_glass":     "#ffffffd9",
        "bg_input":     V3_LIGHT["surface"],

        # Acentos legacy alineados al eje sage + terracotta
        "accent":       V3_LIGHT["teal"],         # sage
        "accent_hover": "#26615a",                # sage deeper
        "accent_glow":  V3_LIGHT["tealSoft"],
        "violet_hover": "#9c5638",                # terracotta deeper
        "violet_glow":  V3_LIGHT["violetSoft"],
        "teal_hover":   "#26615a",

        "text_primary":   V3_LIGHT["text"],
        "text_secondary": V3_LIGHT["text2"],
        "text_tertiary":  V3_LIGHT["text3"],
        "text_on_accent": "#ffffff",

        "border":        V3_LIGHT["border"],
        "border_accent": V3_LIGHT["borderStrong"],
        "border_focus":  V3_LIGHT["teal"],
        "border_card":   V3_LIGHT["border"],

        # Semánticos light alineados a la nueva paleta
        "success": V3_LIGHT["success"],
        "warning": V3_LIGHT["warning"],
        "error":   V3_LIGHT["danger"],
        "info":    "#3a6ea0",            # cool blue muted

        "progress_track": V3_LIGHT["border"],
        "progress_fill":  V3_LIGHT["teal"],

        "sidebar_bg":             V3_LIGHT["bgSidebar"],
        "streak_color":           V3_LIGHT["streak"],       # terracotta
        "streak_bg":              V3_LIGHT["streakSoft"],
        "tcc_heat_cold":          "#3a6ea0",                # slate blue
        "tcc_heat_hot":           V3_LIGHT["danger"],
        "routine_morning_tint":   "#c4862b",                # amber morning
        "routine_afternoon_tint": "#b86844",                # terracotta afternoon
        "routine_night_tint":     "#2f6e62",                # sage night
        "cat_autocuidado_color":  V3_LIGHT["success"],
        "cat_social_color":       V3_LIGHT["warning"],
        "hub_blob_teal":          V3_LIGHT["teal"],
        "hub_blob_violet":        V3_LIGHT["violet"],       # terracotta re-mapeado
        "sync_orb_green":         V3_LIGHT["success"],
        "uninstall_danger":       V3_LIGHT["danger"],
        "installer_terminal_bg":  "#070b18",
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
    # Gradiente firma renovado — monocromático en cada tema.
    # Dark: aqua mist → mint. Light: sage → soft pine.
    "dark_hybrid": [
        ("#6ad7c4", 0.0),
        ("#82e0d0", 0.5),
        ("#95e6d7", 1.0),
    ],
    "light_hybrid": [
        ("#2f6e62", 0.0),
        ("#3f8278", 0.5),
        ("#4a8a7e", 1.0),
    ],
    # Pares (start, end) — claves legacy preservadas (re-mapeadas a la firma nueva)
    "accent_teal_violet_dark":  ("#6ad7c4", "#95e6d7"),
    "accent_teal_violet_light": ("#2f6e62", "#4a8a7e"),
}


# ============================================================
# SHADOWS · strings CSS-like preservados (consumidores existentes)
# ============================================================

SHADOWS = {
    "dark": {
        "card":       "0 10px 30px rgba(0,0,0,0.50)",
        "card_hover": "0 18px 44px rgba(0,0,0,0.60), 0 0 1px rgba(106,215,196,0.22)",
        "glow_teal":  "0 0 40px rgba(106,215,196,0.22), 0 0 16px rgba(106,215,196,0.12)",
    },
    "light": {
        "card":       "0 4px 12px rgba(28,36,31,0.06), 0 1px 2px rgba(28,36,31,0.04)",
        "card_hover": "0 14px 32px rgba(28,36,31,0.09), 0 4px 12px rgba(28,36,31,0.05)",
        "glow_teal":  "0 4px 20px rgba(47,110,98,0.30)",
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
    # Categorías de activación conductual — refrescadas para alinear con
    # la paleta sage/terracotta sin perder distinción semántica.
    "Autocuidado": "#3a8060",  # sage clinical    — salud, autocuidado
    "Física":      "#2f9d95",  # teal cool        — movimiento, energía
    "Cognitiva":   "#4d8acd",  # slate blue       — mente, claridad
    "Placer":      "#b86844",  # terracotta       — disfrute, creatividad
    "Social":      "#c4862b",  # amber muted      — calidez, conexión
    "Maestría":    "#7b6cc4",  # lavender muted   — logro, habilidades
}
