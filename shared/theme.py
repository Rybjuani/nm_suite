"""Runtime visual token catalog for NeuroMood.

This module owns the token data used by the PyQt runtime.  Compatibility
surfaces such as ``COLORS`` and ``shared.design_tokens`` are derived from these
runtime dictionaries so older import paths keep working without a second
palette.
"""

# ============================================================
# Runtime palettes
# ============================================================

V3_LIGHT = {
    # Mockup canonical light: cream / forest / terracotta.
    "bg": "#E9E3D6",
    "bgGradA": "#EEE9DD",
    "bgGradB": "#E3DCCB",
    "bg-grad-a": "#EEE9DD",
    "bg-grad-b": "#E3DCCB",
    "bgAlt": "#E3DCCB",
    "bgSoft": "#F3EFE4",
    "bgSidebar": "#F3EFE4",
    "surface": "#FBF8F1",
    "surface2": "#F3EFE4",
    "surface3": "#ECE6D8",
    "surface_hover": "rgba(46,93,67,0.06)",
    "elevated": "#FBF8F1",
    "surfaceElevated": "#FBF8F1",
    "surfaceGlass": "rgba(251,248,241,0.85)",
    "border": "rgba(49,45,39,0.10)",
    "borderSoft": "rgba(49,45,39,0.06)",
    "borderStrong": "rgba(49,45,39,0.18)",
    "borderSolid": "#D8D0C0",
    "line": "rgba(49,45,39,0.10)",
    "line2": "rgba(49,45,39,0.06)",
    "line-2": "rgba(49,45,39,0.06)",
    "line_strong": "rgba(49,45,39,0.18)",
    "text": "#312D27",
    "textMuted": "#6B6457",
    "text2": "#6B6457",
    "text3": "#9A9382",
    "text4": "#9A9382",
    "ink": "#312D27",
    "ink_2": "#6B6457",
    "ink-2": "#6B6457",
    "ink-3": "#9A9382",
    "mute": "#6B6457",
    "faint": "#9A9382",
    "primary": "#2E5D43",
    "primary_soft": "rgba(46,93,67,0.13)",
    "primary_ink": "#F7F3EA",
    "primarySoft": "rgba(46,93,67,0.13)",
    "successChipBg": "#E0E4DA",
    "successChipIcon": "#BCC8BB",
    "primarySoftSolid": "#DADED3",
    "primaryCheck": "#B7C5B7",
    "brand": "#2E5D43",
    "brandStrong": "#244C37",
    "brand-strong": "#244C37",
    "brandInk": "#F7F3EA",
    "brand-ink": "#F7F3EA",
    "brandSoft": "rgba(46,93,67,0.13)",
    "brand-soft": "rgba(46,93,67,0.13)",
    "brandLine": "rgba(46,93,67,0.28)",
    "brand-line": "rgba(46,93,67,0.28)",
    "accent": "#B0683B",
    "accentSoft": "rgba(176,104,59,0.15)",
    "accentSoftSolid": "#E9DCCE",
    "accent-soft": "rgba(176,104,59,0.15)",
    "gold": "#C2912F",
    "goldSoft": "rgba(194,145,47,0.16)",
    "goldSoftSolid": "#E9DEC3",
    "gold-soft": "rgba(194,145,47,0.16)",
    "rose": "#B24E3D",
    "roseSoft": "rgba(178,78,61,0.14)",
    "roseSoftSolid": "#EAD8D0",
    "rose-soft": "rgba(178,78,61,0.14)",
    "mind": "#3C8A6B",
    "toler": "#C25A45",
    "regul": "#CC8F2C",
    "efect": "#2E5D43",
    "teal": "#3C8A6B",
    "tealSoft": "rgba(60,138,107,0.13)",
    "tealSoftSolid": "#D8E4D8",
    "violet": "#B0683B",
    "violetSoft": "rgba(176,104,59,0.15)",
    "violetSoftSolid": "#E9DCCE",
    "cyan": "#3C8A6B",
    "cyanSoft": "rgba(60,138,107,0.13)",
    "amber": "#C2912F",
    "amberSoft": "rgba(194,145,47,0.16)",
    "amberSoftSolid": "#E9DEC3",
    "success": "#3C8A6B",
    "successSoft": "rgba(60,138,107,0.13)",
    "successSoftSolid": "#D8E4D8",
    "warning": "#C2912F",
    "warningSoft": "rgba(194,145,47,0.16)",
    "warningSoftSolid": "#E9DEC3",
    "danger": "#B24E3D",
    "dangerSoft": "rgba(178,78,61,0.14)",
    "dangerSoftSolid": "#EAD8D0",
    "streak": "#B0683B",
    "streakSoft": "rgba(176,104,59,0.15)",
    "warm": "#B0683B",
    "warmSoft": "rgba(176,104,59,0.15)",
    "ringTrack": "rgba(49,45,39,0.10)",
    "ring-track": "rgba(49,45,39,0.10)",
    "focus": "rgba(46,93,67,0.45)",
    "chrome": "#E5DED0",
    "chromeLine": "rgba(49,45,39,0.10)",
    "chrome-line": "rgba(49,45,39,0.10)",
    "gradFrom": "#2E5D43",
    "gradMid": "#3C8A6B",
    "gradTo": "#C2912F",
    "moodGradFrom": "#7B8A99",
    "moodGradMid": "#5FAA86",
    "moodGradTo": "#B24E3D",
    "bg-0": "#E9E3D6",
    "bg-1": "#F3EFE4",
    "surface-2": "#F3EFE4",
    "surface-3": "#ECE6D8",
    "canvas": "#E9E3D6",
    "sidebar": "#F3EFE4",
    "card": "#FBF8F1",
    "sage": "#2E5D43",
    "terracotta": "#B0683B",
    "terracotta_soft": "rgba(176,104,59,0.15)",
    "aqua": "#3C8A6B",
    "aqua_soft": "rgba(60,138,107,0.13)",
    "background": "#E9E3D6",
    "bg_0": "#E9E3D6",
    "bg_1": "#F3EFE4",
    "surface_card": "#FBF8F1",
    "surface_2": "#F3EFE4",
    "surface_3": "#ECE6D8",
    "surface_elev": "#FBF8F1",
}

V3_DARK = {
    # Mockup canonical dark: ink / mint.
    "bg": "#0E121C",
    "bgGradA": "#121726",
    "bgGradB": "#0B0E18",
    "bg-grad-a": "#121726",
    "bg-grad-b": "#0B0E18",
    "bgAlt": "#121726",
    "bgSoft": "#212838",
    "bgSidebar": "#141A28",
    "surface": "#191F2E",
    "surfaceSolid": "#191F2E",
    "surface2": "#212838",
    "surface3": "#283047",
    "elevated": "#191F2E",
    "surfaceElevated": "#191F2E",
    "elevatedSolid": "#191F2E",
    "surfaceGlass": "rgba(25,31,46,0.85)",
    "surface_hover": "rgba(86,217,166,0.07)",
    "border": "rgba(255,255,255,0.09)",
    "borderSoft": "rgba(255,255,255,0.05)",
    "borderStrong": "rgba(255,255,255,0.16)",
    "borderSolid": "#30384B",
    "line": "rgba(255,255,255,0.09)",
    "line2": "rgba(255,255,255,0.05)",
    "line-2": "rgba(255,255,255,0.05)",
    "line_strong": "rgba(255,255,255,0.16)",
    "text": "#E8EAF1",
    "textMuted": "#A7AEC1",
    "text2": "#A7AEC1",
    "text3": "#727A90",
    "text4": "#727A90",
    "ink": "#E8EAF1",
    "ink_2": "#A7AEC1",
    "ink-2": "#A7AEC1",
    "ink-3": "#727A90",
    "mute": "#A7AEC1",
    "faint": "#727A90",
    "primary": "#56D9A6",
    "primary_soft": "rgba(86,217,166,0.14)",
    "primary_ink": "#06140D",
    "primarySoft": "rgba(86,217,166,0.14)",
    "successChipBg": "#1F343B",
    "successChipIcon": "#2B5852",
    "primarySoftSolid": "#233C41",
    "primaryCheck": "#56D9A6",
    "brand": "#56D9A6",
    "brandStrong": "#3FC592",
    "brand-strong": "#3FC592",
    "brandInk": "#06140D",
    "brand-ink": "#06140D",
    "brandSoft": "rgba(86,217,166,0.14)",
    "brand-soft": "rgba(86,217,166,0.14)",
    "brandLine": "rgba(86,217,166,0.34)",
    "brand-line": "rgba(86,217,166,0.34)",
    "accent": "#E0996A",
    "accentSoft": "rgba(224,153,106,0.16)",
    "accentSoftSolid": "#382C27",
    "accent-soft": "rgba(224,153,106,0.16)",
    "gold": "#E3B765",
    "goldSoft": "rgba(227,183,101,0.16)",
    "goldSoftSolid": "#383125",
    "gold-soft": "rgba(227,183,101,0.16)",
    "rose": "#F09182",
    "roseSoft": "rgba(240,145,130,0.16)",
    "roseSoftSolid": "#3D282B",
    "rose-soft": "rgba(240,145,130,0.16)",
    "mind": "#5FE0B2",
    "toler": "#FF9082",
    "regul": "#E9BC66",
    "efect": "#7CC6F0",
    "teal": "#5FE0B2",
    "tealSoft": "rgba(95,224,178,0.14)",
    "tealSoftSolid": "#1A3931",
    "violet": "#7CC6F0",
    "violetSoft": "rgba(124,198,240,0.16)",
    "violetSoftSolid": "#243747",
    "cyan": "#7CC6F0",
    "cyanSoft": "rgba(124,198,240,0.16)",
    "cyanSoftSolid": "#243747",
    "green": "#56D9A6",
    "amber": "#E3B765",
    "amberSoft": "rgba(227,183,101,0.16)",
    "amberSoftSolid": "#383125",
    "success": "#5FE0B2",
    "successSoft": "rgba(95,224,178,0.14)",
    "successSoftSolid": "#1A3931",
    "warning": "#E3B765",
    "warningSoft": "rgba(227,183,101,0.16)",
    "warningSoftSolid": "#383125",
    "danger": "#F09182",
    "dangerSoft": "rgba(240,145,130,0.16)",
    "dangerSoftSolid": "#3D282B",
    "streak": "#E0996A",
    "streakSoft": "rgba(224,153,106,0.16)",
    "warm": "#E0996A",
    "warmSoft": "rgba(224,153,106,0.16)",
    "ringTrack": "rgba(255,255,255,0.10)",
    "ring-track": "rgba(255,255,255,0.10)",
    "focus": "rgba(86,217,166,0.50)",
    "chrome": "#141A28",
    "chromeLine": "rgba(255,255,255,0.07)",
    "chrome-line": "rgba(255,255,255,0.07)",
    "gradFrom": "#56D9A6",
    "gradMid": "#5FE0B2",
    "gradTo": "#7CC6F0",
    "moodGradFrom": "#7B8A99",
    "moodGradMid": "#5FAA86",
    "moodGradTo": "#F09182",
    "bg-0": "#0E121C",
    "bg-1": "#121726",
    "surface-2": "#212838",
    "surface-3": "#283047",
    "deep": "#0E121C",
    "sidebar": "#141A28",
    "card": "#191F2E",
    "lavender": "#56D9A6",
    "aqua": "#56D9A6",
    "aqua_soft": "rgba(86,217,166,0.14)",
    "sage": "#56D9A6",
    "terracotta": "#E0996A",
    "terracotta_soft": "rgba(224,153,106,0.16)",
    "background": "#0E121C",
    "bg_0": "#0E121C",
    "bg_1": "#121726",
    "surface_card": "#191F2E",
    "surface_2": "#212838",
    "surface_3": "#283047",
    "surface_elev": "#191F2E",
}


# ============================================================
# MOOD_PALETTE · 10 niveles emocionales
# Consumido por NMMoodEmoji y V3MoodSlider (componentes nuevos)
# ============================================================

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


# ============================================================
# Tokens estructurales v3
# ============================================================

V3_SPACE = {
    "xs": 4,
    "sm": 6,
    "md": 10,
    "lg": 14,
    "xl": 16,
    "2xl": 20,
    "3xl": 24,
    "4xl": 32,
    "xxl": 20,
    "xxxl": 24,
}
V3_RADIUS = {
    "xs": 8,
    "sm": 12,
    "md": 16,
    "lg": 22,
    "xl": 28,
    "xxl": 28,
    "pill": 999,
    "card": 22,
    "input": 16,
}

# Shadows en formato consumible por QGraphicsDropShadowEffect:
#   blur (px), offset (dx, dy), color (r, g, b, a 0-255)
V3_SHADOWS = {
    # Approximation of mockup multi-layer shadows for QGraphicsDropShadowEffect.
    "light": {
        "sm": {"blur": 6, "offset": (0, 2), "color": (49, 45, 39, 10)},
        "md": {"blur": 28, "offset": (0, 10), "color": (49, 45, 39, 18)},
        "card": {"blur": 28, "offset": (0, 10), "color": (49, 45, 39, 18)},
        "lg": {"blur": 60, "offset": (0, 30), "color": (49, 45, 39, 31)},
        "ring": {"blur": 20, "offset": (0, 4), "color": (46, 93, 67, 72)},
        "shadow_1": {"blur": 6, "offset": (0, 2), "color": (49, 45, 39, 10)},
        "shadow_2": {"blur": 28, "offset": (0, 10), "color": (49, 45, 39, 18)},
        "shadow_3": {"blur": 60, "offset": (0, 30), "color": (49, 45, 39, 31)},
    },
    "dark": {
        "sm": {"blur": 2, "offset": (0, 1), "color": (0, 0, 0, 102)},
        "md": {"blur": 32, "offset": (0, 12), "color": (0, 0, 0, 89)},
        "card": {"blur": 32, "offset": (0, 12), "color": (0, 0, 0, 89)},
        "lg": {"blur": 70, "offset": (0, 30), "color": (0, 0, 0, 140)},
        "glow": {"blur": 24, "offset": (0, 0), "color": (86, 217, 166, 28)},
        "ring": {"blur": 20, "offset": (0, 4), "color": (86, 217, 166, 46)},
        "shadow_1": {"blur": 2, "offset": (0, 1), "color": (0, 0, 0, 102)},
        "shadow_2": {"blur": 32, "offset": (0, 12), "color": (0, 0, 0, 89)},
        "shadow_3": {"blur": 24, "offset": (0, 8), "color": (0, 0, 0, 140)},
    },
}

# Highlight superior interno de las superficies ("lift") — dirección del mockup
# aprobado: un degradado blanco translúcido que cae sobre el ~42% superior de la
# card y le da material/elevación sin sombra dura. Valores = alpha 0-255 del
# blanco en el tope (cae a 0). En dark es casi imperceptible (solo "sella" el
# borde superior); en light es el principal aportante de profundidad.
V3_LIFT = {"light": 140, "dark": 16}


V3_GRADIENTS = {
    "light": [("#2E5D43", 0.0), ("#3C8A6B", 1.0)],
    "dark": [("#56D9A6", 0.0), ("#5FE0B2", 1.0)],
}


# ============================================================
# Tipografía v3 (expandida; compatible con keys v2)
# ============================================================

TYPOGRAPHY = {
    # Canonical mockup typography: Inter body + Fraunces display.
    "font_family": "Inter, Segoe UI, system-ui, sans-serif",
    "font_family_fallback_chain": [
        "Inter",
        "Segoe UI",
        "Plus Jakarta Sans",
        "DM Sans",
        "Arial",
    ],
    "font_fallback": "Segoe UI",
    "font_mono": "JetBrains Mono",
    "font_serif": "Fraunces, Georgia, Times New Roman, serif",
    "font_serif_fallback_chain": [
        "Fraunces",
        "Source Serif Pro",
        "Georgia",
        "serif",
    ],
    # Escala tipográfica del runtime spec §3 — píxeles convertidos a puntos donde
    # corresponde. Las claves compatibility (size_h1/h2/h3) se preservan; las
    # display-xl/display-l/display-m/heading-l/heading-m/eyebrow son nuevas.
    "size_display": 28,  # compatibility — no cambiar (compat con consumidores históricos)
    "size_display_xl": 40,  # hero onboarding contenido (runtime, era 56)
    "size_display_l": 30,  # saludo/score del Home contenidos (era 38)
    "size_display_m": 26,  # compact desktop: card headings (era 26)
    "size_h1": 20,  # compact: alineado a heading_l
    "size_h2": 16,  # compact: alineado a heading_m
    "size_h3": 14,  # compact: alineado a body
    "size_heading_l": 20,  # compact desktop: sección (era 20)
    "size_heading_m": 16,  # compact desktop: subtítulo card (era 16)
    "size_body": 14,  # compact desktop: body text (era 14)
    "size_small": 12,
    "size_caption": 12,  # mantener
    "size_caption_xs": 11,
    "size_eyebrow": 11,  # compact: eyebrow uppercase (era 11)
    "size_mono": 12,  # compact: mono timestamps (era 12)
    # V5 Typography Scale camelCase and short aliases
    "displayXL": 56,
    "displayL": 38,
    "displayM": 26,
    "headingL": 20,
    "headingM": 16,
    "body": 14,
    "caption": 12,
    "eyebrow": 11,
    "mono": 12,
    # Tamaños heredados (mantenidos por compat)
    "size_emoji": 64,
    "size_emoji_sm": 22,
    "size_time_large": 20,
    "size_time_timer": 18,
    # Pesos numéricos (runtime spec §3)
    "weight_regular": 400,
    "weight_medium": 500,
    "weight_semibold": 600,
    "weight_bold": 700,
    # Letter spacing (runtime spec §3 — eyebrow .14em uppercase)
    "tracking_tight": "0",
    "tracking_normal": "0",
    "tracking_eyebrow": ".14em",
}


# ============================================================
# Layout · keys históricos preservados, valores actualizados a v3
# ============================================================

LAYOUT = {
    "padding_container": 24,  # v3 xxxl
    "padding_card": 20,
    "padding_button_x": 20,
    "padding_button_y": 10,
    "gap_cards": 14,
    "gap_elements": 10,
    # Botones pill (v3) — pill buttons
    "radius_button": 999,
    "radius_card": 22,
    "radius_modal": 28,
    "radius_input": 16,
    "radius_badge": 999,
    "radius_pill": 999,
    "radius_small": 8,
    "checkbox_size": 18,
    "border_width": 1,
    "border_card_width": 1,
    "border_accent_width": 2,
    "border_button_width": 1,
    "header_height": 56,  # v3 cockpit (matching top-command-hud)
    "min_touch_target": 44,
    # Opacidades heredadas
    "aura_opacity_dark": 0.18,
    "aura_opacity_light": 0.10,
    "blob_opacity_dark": 0.22,
    "blob_opacity_light": 0.18,
    # Umbrales rings
    "ring_good_threshold": 80,
    "ring_mid_threshold": 50,
    # v3 extras
    "sidebar_width": 200,  # compact R3 (era 240)
}


# ============================================================
# Densidades visuales por producto
# ============================================================

VISUAL_DENSITIES = {
    "suite_comfortable": {
        "id": "suite_comfortable",
        "product": "suite",
        "control_height": 36,
        "control_compact_height": 32,
        "button_height": 36,
        "button_compact_height": 32,
        "input_height": 36,
        "textarea_min_height": 96,
        "tab_height": 32,
        "subtab_height": 32,
        "filter_height": 32,
        "badge_height": 22,
        "chip_height": 24,
        "scrollbar_width": 8,
        "row_padding_y": 6,
        "focus_border_width": 1,
        "disabled_opacity": 0.45,
        "pad_x": 12,
        "pad_y": 5,
        "tab_pad_x": 14,
        "badge_pad_x": 10,
    },
    "hub_professional_compact": {
        "id": "hub_professional_compact",
        "product": "hub",
        "control_height": 32,
        "control_compact_height": 28,
        "button_height": 32,
        "button_compact_height": 28,
        "input_height": 32,
        "textarea_min_height": 72,
        "tab_height": 28,
        "subtab_height": 28,
        "filter_height": 28,
        "badge_height": 20,
        "chip_height": 22,
        "scrollbar_width": 6,
        "row_padding_y": 5,
        "focus_border_width": 1,
        "disabled_opacity": 0.45,
        "pad_x": 10,
        "pad_y": 4,
        "tab_pad_x": 10,
        "badge_pad_x": 8,
    },
}


def icon_stroke_width(size: int) -> float:
    """Grosor de stroke para NMIcon SVG según tamaño (README v3)."""
    if size <= 14:
        return 1.4
    if size <= 18:
        return 1.5
    if size <= 24:
        return 1.6
    if size <= 32:
        return 1.7
    if size <= 48:
        return 1.8
    return 2.0


# ============================================================
# COLORS · bridge compatibility → v3
# Cada modo expone las claves v3 + las claves v2 históricas re-mapeadas.
# Para QSS (que no soporta rgba en todos los properties), las claves
# compatibility apuntan a las variantes …Solid donde existe.
# ============================================================


def _bridge_dark():
    v = dict(V3_DARK)
    v.update(
        {
            # Backgrounds compatibility
            "bg_primary": V3_DARK["bg"],
            "bg_secondary": V3_DARK["bgAlt"],
            "bg_surface": V3_DARK["surfaceSolid"],
            "bg_elevated": V3_DARK["elevatedSolid"],
            "bg_overlay": V3_DARK["surface2"],  # surface-2 runtime spec
            "bg_glass": V3_DARK["surfaceSolid"] + "d9",
            "bg_input": V3_DARK["surface2"],
            "accent": V3_DARK["primary"],
            "accent_hover": V3_DARK["brandStrong"],
            "accent_glow": V3_DARK["accentSoftSolid"],
            "violet_hover": V3_DARK["efect"],
            "violet_glow": V3_DARK["violetSoftSolid"],
            "teal_hover": V3_DARK["brandStrong"],
            # Texto compatibility
            "text_primary": V3_DARK["text"],
            "text_secondary": V3_DARK["text2"],
            "text_tertiary": V3_DARK["text3"],
            "text_on_accent": V3_DARK["primary_ink"],
            # Bordes compatibility (sólidos para QSS)
            "border": V3_DARK["borderSolid"],
            "border_accent": "#315947",
            "border_focus": V3_DARK["primary"],
            "border_card": V3_DARK["borderSolid"],
            # Semánticos compatibility
            "error": V3_DARK["danger"],
            "info": V3_DARK["efect"],
            "progress_track": V3_DARK["surface2"],
            "progress_fill": V3_DARK["primary"],
            # Tokens v2/v3 ya existentes en el codebase (re-mapeados al runtime spec dark)
            "sidebar_bg": V3_DARK["bgSidebar"],
            "streak_color": V3_DARK["amber"],
            "streak_bg": V3_DARK["amberSoftSolid"],
            "tcc_heat_cold": "#7FA8E8",  # slate blue cool
            "tcc_heat_hot": V3_DARK["danger"],
            "routine_morning_tint": V3_DARK["amber"],
            "routine_afternoon_tint": V3_DARK["danger"],
            "routine_night_tint": V3_DARK["primary"],
            "cat_autocuidado_color": V3_DARK["success"],
            "cat_social_color": V3_DARK["amber"],
            "hub_blob_teal": V3_DARK["primary"],
            "hub_blob_violet": V3_DARK["efect"],
            "sync_orb_green": V3_DARK["success"],
            "uninstall_danger": V3_DARK["danger"],
            "installer_terminal_bg": V3_DARK["bg"],
        }
    )
    return v


def _bridge_light():
    v = dict(V3_LIGHT)
    v.update(
        {
            "bg_primary": V3_LIGHT["bg"],
            "bg_secondary": V3_LIGHT["bgAlt"],
            "bg_surface": V3_LIGHT["surface"],
            "bg_elevated": V3_LIGHT["elevated"],
            "bg_overlay": V3_LIGHT["bgAlt"],
            "bg_glass": "#FBF8F1d9",  # surface translúcido
            "bg_input": V3_LIGHT["surface2"],
            "accent": V3_LIGHT["primary"],
            "accent_hover": V3_LIGHT["brandStrong"],
            "accent_glow": V3_LIGHT["accentSoftSolid"],
            "violet_hover": V3_LIGHT["accent"],
            "violet_glow": V3_LIGHT["violetSoftSolid"],
            "teal_hover": V3_LIGHT["mind"],
            "text_primary": V3_LIGHT["text"],
            "text_secondary": V3_LIGHT["text2"],
            "text_tertiary": V3_LIGHT["text3"],
            "text_on_accent": V3_LIGHT["primary_ink"],  # surface — texto claro sobre sage
            "border": V3_LIGHT["borderSolid"],
            "border_accent": "#C8BDA9",
            "border_focus": V3_LIGHT["primary"],
            "border_card": V3_LIGHT["borderSolid"],
            # Semánticos light alineados al runtime spec
            "success": V3_LIGHT["success"],
            "warning": V3_LIGHT["warning"],
            "error": V3_LIGHT["danger"],
            "info": V3_LIGHT["mind"],
            "progress_track": V3_LIGHT["surface2"],
            "progress_fill": V3_LIGHT["primary"],
            "sidebar_bg": V3_LIGHT["bgSidebar"],
            "streak_color": V3_LIGHT["streak"],  # terracotta
            "streak_bg": V3_LIGHT["violetSoftSolid"],
            "tcc_heat_cold": V3_LIGHT["mind"],
            "tcc_heat_hot": V3_LIGHT["danger"],
            "routine_morning_tint": V3_LIGHT["amber"],
            "routine_afternoon_tint": V3_LIGHT["violet"],
            "routine_night_tint": V3_LIGHT["primary"],
            "cat_autocuidado_color": V3_LIGHT["success"],
            "cat_social_color": V3_LIGHT["warning"],
            "hub_blob_teal": V3_LIGHT["teal"],
            "hub_blob_violet": V3_LIGHT["violet"],
            "sync_orb_green": V3_LIGHT["success"],
            "uninstall_danger": V3_LIGHT["danger"],
            "installer_terminal_bg": V3_DARK["bg"],
        }
    )
    return v


COLORS = {
    "dark_hybrid": _bridge_dark(),
    "light_hybrid": _bridge_light(),
}

# Alias cortos
COLORS["dark"] = COLORS["dark_hybrid"]
COLORS["light"] = COLORS["light_hybrid"]

# Compat extras heredados
for _m in ("dark_hybrid", "light_hybrid"):
    COLORS[_m]["bg_hover"] = COLORS[_m]["bg_overlay"]
    COLORS[_m]["bg_list_item"] = COLORS[_m]["bg_elevated"]
    COLORS[_m]["accent_subtle"] = COLORS[_m]["bg_surface"]
    if "border_card" not in COLORS[_m]:
        COLORS[_m]["border_card"] = COLORS[_m]["border"]


# ============================================================
# GRADIENTS · ahora con la firma v3 (teal → violet)
# ============================================================

GRADIENTS = {
    "dark_hybrid": [
        ("#56D9A6", 0.0),
        ("#5FE0B2", 1.0),
    ],
    "light_hybrid": [
        ("#2E5D43", 0.0),
        ("#3C8A6B", 1.0),
    ],
    "accent_teal_violet_dark": ("#56D9A6", "#5FE0B2"),
    "accent_teal_violet_light": ("#2E5D43", "#3C8A6B"),
}


# ============================================================
# SHADOWS · strings CSS-like preservados (consumidores existentes)
# ============================================================

SHADOWS = {
    "dark": {
        "card": "0 4px 12px rgba(0,0,0,0.40), 0 12px 32px rgba(0,0,0,0.35)",
        "card_hover": "0 10px 24px rgba(0,0,0,0.50), 0 30px 70px rgba(0,0,0,0.55)",
        "glow_teal": "0 0 32px rgba(86,217,166,0.18)",
    },
    "light": {
        "card": "0 1px 2px rgba(49,45,39,0.05), 0 2px 6px rgba(49,45,39,0.04)",
        "card_hover": "0 2px 8px rgba(49,45,39,0.06), 0 10px 28px rgba(49,45,39,0.07)",
        "glow_teal": "0 4px 20px rgba(46,93,67,0.18)",
    },
}


TRANSITIONS = {
    "fast": 140,
    "normal": 240,
    "slow": 480,
}


# ============================================================
# Helpers
# ============================================================


def norm_modo(modo: str = "dark_hybrid") -> str:
    """Normaliza alias compatibility de modo."""
    if modo == "dark":
        return "dark_hybrid"
    if modo == "light":
        return "light_hybrid"
    return modo if modo in ("dark_hybrid", "light_hybrid") else "dark_hybrid"


def v3_mode(modo: str = "dark_hybrid") -> str:
    """Devuelve 'light' o 'dark' a partir de cualquier alias."""
    return "light" if norm_modo(modo) == "light_hybrid" else "dark"


def get_colors(modo: str = "dark_hybrid"):
    """Devuelve el diccionario de colores según el modo (incluye claves v3 + compatibility)."""
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
    "Autocuidado": "#3C8A6B",
    "Física": "#3C8A6B",
    "Cognitiva": "#2E5D43",
    "Placer": "#B0683B",
    "Social": "#C2912F",
    "Maestría": "#7CC6F0",
}
