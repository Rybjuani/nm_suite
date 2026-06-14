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
    # ── Linen + Sage ─────────────────────────────────────────────────────────
    # Backgrounds
    "bg": "#F4EFE5",  # canvas linen
    "bgAlt": "#ECE5D4",  # sidebar
    "bgSoft": "#ECE5D4",
    "bgSidebar": "#ECE5D4",
    "surface": "#FBF8F1",  # card surface
    "surface2": "#ECE5D4",  # inputs bg
    "surface_hover": "rgba(48, 90, 72, 0.04)",
    "elevated": "#FBF8F1",
    "surfaceElevated": "#FBF8F1",
    "surfaceGlass": "rgba(251, 248, 241, 0.85)",
    # Borders — 6.1: borderStrong subido 0.15→0.22 para que las separaciones
    # se lean sin gritar. Mantiene el tono ink #1C2218.
    "border": "rgba(28, 34, 24, 0.10)",
    "borderSoft": "rgba(28, 34, 24, 0.07)",
    "borderStrong": "rgba(28, 34, 24, 0.22)",
    "borderSolid": "#D8D3C5",
    # Text
    "text": "#1C2218",  # ink
    "textMuted": "#76796B",  # mute
    "text2": "#3F4636",  # ink-2
    "text3": "#76796B",
    "text4": "#8B8979",
    # Primary / Sage
    "primary": "#305A48",  # sage
    "primary_soft": "rgba(48, 90, 72, 0.08)",
    "primary_ink": "#FBF8F1",
    # Accent / Terracotta
    "accent": "#B8633B",  # terracotta accent (sage is primary)
    "accentSoft": "rgba(184, 99, 59, 0.08)",
    "accentSoftSolid": "#EADCD2",
    "gradFrom": "#305A48",
    "gradMid": "#7B7140",
    "gradTo": "#C68A2E",
    # Mood
    "moodGradFrom": "#305A48",
    "moodGradMid": "#7B7140",
    "moodGradTo": "#B8633B",  # terracotta
    # Tonos
    "teal": "#2F7E73",
    "tealSoft": "rgba(47, 126, 115, 0.08)",
    "tealSoftSolid": "#D8DFD5",
    "violet": "#B8633B",  # terracotta
    "violetSoft": "rgba(184, 99, 59, 0.08)",
    "violetSoftSolid": "#EDDED1",
    "cyan": "#2F7E73",
    "cyanSoft": "rgba(47, 126, 115, 0.08)",
    "amber": "#C68A2E",
    "amberSoft": "rgba(198, 138, 46, 0.08)",
    "amberSoftSolid": "#EBE1CB",
    # Semánticos
    "success": "#4D7A52",
    "successSoft": "rgba(77, 122, 82, 0.08)",
    "successSoftSolid": "#DDDFD0",
    "warning": "#C68A2E",
    "warningSoft": "rgba(198, 138, 46, 0.08)",
    "warningSoftSolid": "#EEE1CB",
    "danger": "#B14B3B",
    "dangerSoft": "rgba(177, 75, 59, 0.08)",
    "dangerSoftSolid": "#EDDFD4",
    "streak": "#B8633B",
    "streakSoft": "rgba(184, 99, 59, 0.08)",
    "warm": "#B8633B",
    "warmSoft": "rgba(184, 99, 59, 0.08)",
    # V5 design-system specification tokens & aliases
    "bg-0": "#F4EFE5",
    "bg-1": "#ECE5D4",
    "surface-2": "#ECE5D4",
    "canvas": "#F4EFE5",
    "sidebar": "#ECE5D4",
    "card": "#FBF8F1",
    "ink": "#1C2218",
    "sage": "#305A48",
    "terracotta": "#B8633B",
    # Semantic Helpers V5 mapping
    "background": "#F4EFE5",
    "primarySoft": "rgba(61, 90, 72, 0.08)",
    # Alias snake_case
    "bg_0": "#F4EFE5",
    "bg_1": "#ECE5D4",
    "surface_card": "#FBF8F1",
    "surface_2": "#ECE5D4",
    "surface_elev": "#FBF8F1",
    "line": "rgba(28, 34, 24, 0.08)",
    "line_strong": "rgba(28, 34, 24, 0.15)",
    "ink_2": "#3F4636",
    "mute": "#76796B",
    "faint": "#8B8979",
    "terracotta_soft": "rgba(184, 99, 59, 0.08)",
    "aqua": "#2F7E73",
    "aqua_soft": "rgba(47, 126, 115, 0.08)",
}

V3_DARK = {
    # ── Indigo Profundo ──────────────────────────────────────────────────────
    # Backgrounds
    "bg": "#07091A",  # canvas indigo profundo (bg-0)
    "bgAlt": "#0E132B",  # sidebar (bg-1)
    "bgSoft": "#0E132B",
    "bgSidebar": "#0E132B",
    "surface": "#141A38",  # card surface
    "surfaceSolid": "#141A38",
    "surface2": "#0E132B",  # campos/anidados: tono sidebar, no canvas (campos negros = rechazo user feedback)
    "elevated": "#141A38",
    "surfaceElevated": "#141A38",
    "elevatedSolid": "#141A38",
    "surfaceGlass": "rgba(20, 26, 56, 0.85)",
    # Borders
    "border": "rgba(255,255,255,0.06)",
    "borderSoft": "rgba(255,255,255,0.04)",
    "borderStrong": "rgba(255,255,255,0.12)",
    "borderSolid": "#232740",
    # Text
    "text": "#ECECFB",  # ink
    "textMuted": "#8285A8",  # mute
    "text2": "#C7C9E5",  # ink-2
    "text3": "#8285A8",  # mute
    "text4": "#6A6F93",  # faint
    # Accent: primary = lavender, accent = aqua
    "primary": "#A99CFF",  # lavender primary
    "primary_soft": "rgba(169,156,255,0.10)",
    "primary_ink": "#0E132B",
    "accent": "#5EE0C7",  # aqua accent (lavender is primary)
    "accentSoft": "rgba(94,224,199,0.14)",
    "accentSoftSolid": "#123336",
    "gradFrom": "#A99CFF",  # primary → amber
    "gradMid": "#C8A89B",
    "gradTo": "#E8B86A",
    "moodGradFrom": "#A99CFF",
    "moodGradMid": "#C8A89B",
    "moodGradTo": "#5EE0C7",
    # Tonos (claves compatibility re-mapeadas al runtime spec)
    "teal": "#5EE0C7",  # aqua
    "tealSoft": "rgba(94,224,199,0.14)",
    "tealSoftSolid": "#123336",
    "violet": "#5EE0C7",  # aqua
    "violetSoft": "rgba(94,224,199,0.14)",
    "violetSoftSolid": "#123336",
    "cyan": "#5EE0C7",  # alias del aqua
    "cyanSoft": "rgba(94,224,199,0.14)",
    "cyanSoftSolid": "#123336",
    "green": "#60B89A",
    # Amber (runtime spec — progreso, energía)
    "amber": "#E8B86A",
    "amberSoft": "rgba(232,184,106,0.16)",
    "amberSoftSolid": "#2F2722",
    # Semánticos runtime spec
    "success": "#60B89A",
    "successSoft": "rgba(96,184,154,0.16)",
    "successSoftSolid": "#18261A",
    "warning": "#E8B86A",
    "warningSoft": "rgba(232,184,106,0.16)",
    "warningSoftSolid": "#2F2722",
    "danger": "#FF8A7A",
    "dangerSoft": "rgba(255,138,122,0.14)",
    "dangerSoftSolid": "#2E1D22",
    # Streak (re-mapeado a amber)
    "streak": "#E8B86A",
    "streakSoft": "rgba(232,184,106,0.16)",
    # Warm secondary
    "warm": "#E8B86A",
    "warmSoft": "rgba(232,184,106,0.16)",
    # V5 design-system specification tokens & aliases
    "bg-0": "#07091A",
    "bg-1": "#0E132B",
    "surface-2": "#07091A",
    "deep": "#07091A",
    "sidebar": "#0E132B",
    "card": "#141A38",
    "ink": "#ECECFB",
    "lavender": "#A99CFF",
    "aqua": "#5EE0C7",
    # Semantic Helpers V5 mapping
    "background": "#07091A",
    "primarySoft": "rgba(169,156,255,0.10)",
    # ── Alias runtime spec con nombres CSS directos (snake_case) ───────────────────
    "bg_0": "#07091A",
    "bg_1": "#0E132B",
    "surface_card": "#141A38",
    "surface_2": "#0E132B",
    "surface_elev": "#141A38",
    "line": "rgba(255,255,255,0.06)",
    "line_strong": "rgba(255,255,255,0.12)",
    "ink_2": "#C7C9E5",
    "mute": "#8285A8",
    "faint": "#6A6F93",
    "terracotta": "#5EE0C7",  # en dark el "accent" runtime es aqua
    "terracotta_soft": "rgba(94,224,199,0.14)",
    "aqua_soft": "rgba(94,224,199,0.14)",
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

# Roles semánticos de spacing — apuntan a claves V3_SPACE sin redefinir valores.
# Presupuestos canónicos: 16 px (gaps/card-padding-compact),
# 24 px (content-padding/main-gaps), 32 px (section separation).
# Consúmelos en lugar de literales cuando el rol sea claro.
V3_SPACE_ROLES = {
    "content_padding": V3_SPACE["3xl"],     # 24 — padding de áreas de contenido
    "card_padding": V3_SPACE["2xl"],        # 20 — padding interior de card
    "gap_cards": V3_SPACE["xl"],            # 16 — separación entre cards
    "section_spacing": V3_SPACE["4xl"],     # 32 — separación entre secciones mayores
    "gap_elements": V3_SPACE["md"],         # 10 — gap entre elementos inline
    "gap_dense": V3_SPACE["sm"],            # 6  — gap denso (Hub compact)
}

V3_RADIUS = {"sm": 8, "md": 12, "lg": 16, "xl": 16, "xxl": 22, "pill": 999, "card": 16, "input": 12}

# Shadows en formato consumible por QGraphicsDropShadowEffect:
#   blur (px), offset (dx, dy), color (r, g, b, a 0-255)
V3_SHADOWS = {
    # Light sombras del runtime spec (§2.3): tono ink (28,34,24) con opacidades muy
    # bajas para mantener el "nada brilla, la calma es el default".
    # 6.1: opacidades levemente subidas para que el light se lea con el mismo
    # "peso" que dark — antes las cards en light parecían planas.
    "light": {
        # sm: 0 1px 0 rgba(28,34,24,.04), 0 4px 12px rgba(28,34,24,.04)
        "sm": {"blur": 12, "offset": (0, 4), "color": (28, 34, 24, 14)},
        # md: 0 2px 4px rgba(28,34,24,.04), 0 12px 32px rgba(28,34,24,.07)
        "md": {"blur": 32, "offset": (0, 12), "color": (28, 34, 24, 24)},
        # card alias de md (cards primarios)
        "card": {"blur": 32, "offset": (0, 12), "color": (28, 34, 24, 24)},
        # lg: 0 4px 8px rgba(28,34,24,.05), 0 24px 64px rgba(28,34,24,.10)
        "lg": {"blur": 64, "offset": (0, 24), "color": (28, 34, 24, 34)},
        # ring glow sage (NMRing, anillos)
        "ring": {"blur": 20, "offset": (0, 4), "color": (61, 90, 72, 80)},
        # compact §2.5 — desktop compact shadows (más sutiles que sm/md/lg)
        "shadow_1": {"blur": 2, "offset": (0, 1), "color": (28, 34, 24, 12)},
        "shadow_2": {"blur": 12, "offset": (0, 4), "color": (28, 34, 24, 20)},
        "shadow_3": {"blur": 24, "offset": (0, 8), "color": (28, 34, 24, 32)},
    },
    # Dark: opacidades 0.25–0.45 según runtime spec §2.3.
    "dark": {
        "sm": {"blur": 12, "offset": (0, 4), "color": (0, 0, 0, 76)},
        "md": {"blur": 40, "offset": (0, 16), "color": (0, 0, 0, 102)},
        "card": {"blur": 30, "offset": (0, 10), "color": (0, 0, 0, 90)},
        "lg": {"blur": 80, "offset": (0, 32), "color": (0, 0, 0, 130)},
        # glow lavender (anillos en dark) — F2 runtime: calmado (antes
        # blur 40/alpha 56 y alpha 64: halos que "brillaban" contra la regla
        # "nada brilla, la calma es el default").
        "glow": {"blur": 24, "offset": (0, 0), "color": (169, 156, 255, 24)},
        "ring": {"blur": 20, "offset": (0, 4), "color": (169, 156, 255, 32)},
        # compact §2.5 — desktop compact shadows
        "shadow_1": {"blur": 2, "offset": (0, 1), "color": (0, 0, 0, 89)},
        "shadow_2": {"blur": 4, "offset": (0, 2), "color": (0, 0, 0, 115)},
        "shadow_3": {"blur": 24, "offset": (0, 8), "color": (0, 0, 0, 140)},
    },
}

# Paradas para QLinearGradient — gradiente firma del runtime spec.
# Runtime spec §4.7: progress fill = linear primary → amber.
#   Light: sage (#305A48) → amber (#C68A2E)
#   Dark:  lavender (#A99CFF) → amber (#E8B86A)
V3_GRADIENTS = {
    "light": [("#305A48", 0.0), ("#7B7140", 0.5), ("#C68A2E", 1.0)],
    "dark": [("#A99CFF", 0.0), ("#C8A89B", 0.5), ("#E8B86A", 1.0)],
}


# ============================================================
# Tipografía v3 (expandida; compatible con keys v2)
# ============================================================

TYPOGRAPHY = {
    # Familias runtime del runtime spec (§3): Newsreader serif (display), Manrope
    # sans (UI), JetBrains Mono (timestamps). Fallbacks de sistema para
    # entornos donde los .ttf de assets/fonts/ no estén disponibles.
    "font_family": "Manrope, Manrope ExtraLight, Segoe UI, system-ui, sans-serif",
    "font_family_fallback_chain": [
        "Manrope",
        "Manrope ExtraLight",
        "Plus Jakarta Sans",
        "DM Sans",
        "Segoe UI",
        "Arial",
    ],
    "font_fallback": "Segoe UI",
    "font_mono": "JetBrains Mono",
    "font_serif": "Newsreader, Newsreader 16pt 16pt, Source Serif Pro, Georgia, serif",
    "font_serif_fallback_chain": [
        "Newsreader",
        "Newsreader 16pt 16pt",
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
    "tracking_tight": "-.02em",
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
    "radius_card": 16,
    "radius_modal": 22,
    "radius_input": 12,
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
            "bg_input": V3_DARK["surface2"],  # inputs sobre surface-2 (runtime spec §4.3)
            # Acentos compatibility (mapeo al runtime spec: primary lavender, accent aqua)
            "accent": "#A99CFF",  # lavender primary for compatibility compatibility
            "accent_hover": "#BFB4FF",  # lavender brighter
            "accent_glow": V3_DARK["accentSoftSolid"],
            "violet_hover": "#7CE6D0",  # aqua hover
            "violet_glow": V3_DARK["violetSoftSolid"],
            "teal_hover": "#7CE6D0",
            # Texto compatibility
            "text_primary": V3_DARK["text"],
            "text_secondary": V3_DARK["text2"],
            "text_tertiary": V3_DARK["text3"],
            "text_on_accent": V3_DARK["primary_ink"],  # bg-1 — texto oscuro sobre lavender
            # Bordes compatibility (sólidos para QSS)
            "border": V3_DARK["borderSolid"],
            "border_accent": "#2A2F58",  # lavender undertone solid
            "border_focus": "#A99CFF",  # lavender
            "border_card": V3_DARK["borderSolid"],
            # Semánticos compatibility
            "error": V3_DARK["danger"],
            "info": "#7FA8E8",  # cool blue muted
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
            "routine_night_tint": V3_DARK["aqua"],
            "cat_autocuidado_color": V3_DARK["success"],
            "cat_social_color": V3_DARK["amber"],
            "hub_blob_teal": V3_DARK["aqua"],
            "hub_blob_violet": V3_DARK["accent"],  # lavender primary
            "sync_orb_green": V3_DARK["success"],
            "uninstall_danger": V3_DARK["danger"],
            "installer_terminal_bg": V3_DARK["bg"],  # indigo profundo runtime spec
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
            "bg_overlay": V3_LIGHT["bgAlt"],  # bg-1 runtime spec
            "bg_glass": "#FBF8F1d9",  # surface translúcido
            "bg_input": V3_LIGHT["surface2"],  # inputs sobre surface-2 (runtime spec §4.3)
            # Acentos compatibility alineados al runtime spec: primary sage, accent terracotta
            "accent": "#305A48",  # sage primary for compatibility compatibility
            "accent_hover": "#345040",  # sage deeper
            "accent_glow": V3_LIGHT["accentSoftSolid"],
            "violet_hover": "#9C5530",  # terracotta deeper
            "violet_glow": V3_LIGHT["violetSoftSolid"],
            "teal_hover": "#27695F",
            "text_primary": V3_LIGHT["text"],
            "text_secondary": V3_LIGHT["text2"],
            "text_tertiary": V3_LIGHT["text3"],
            "text_on_accent": V3_LIGHT["primary_ink"],  # surface — texto claro sobre sage
            "border": V3_LIGHT["borderSolid"],
            "border_accent": "#C8C0AD",  # line-strong sólido
            "border_focus": "#305A48",  # sage focus
            "border_card": V3_LIGHT["borderSolid"],
            # Semánticos light alineados al runtime spec
            "success": V3_LIGHT["success"],
            "warning": V3_LIGHT["warning"],
            "error": V3_LIGHT["danger"],
            "info": "#3A6EA0",  # cool blue muted
            "progress_track": V3_LIGHT["surface2"],
            "progress_fill": "#305A48",
            "sidebar_bg": V3_LIGHT["bgSidebar"],
            "streak_color": V3_LIGHT["streak"],  # terracotta
            "streak_bg": V3_LIGHT["violetSoftSolid"],
            "tcc_heat_cold": "#3A6EA0",
            "tcc_heat_hot": V3_LIGHT["danger"],
            "routine_morning_tint": V3_LIGHT["amber"],
            "routine_afternoon_tint": V3_LIGHT["violet"],  # terracotta
            "routine_night_tint": "#305A48",  # sage
            "cat_autocuidado_color": V3_LIGHT["success"],
            "cat_social_color": V3_LIGHT["warning"],
            "hub_blob_teal": V3_LIGHT["teal"],
            "hub_blob_violet": V3_LIGHT["violet"],
            "sync_orb_green": V3_LIGHT["success"],
            "uninstall_danger": V3_LIGHT["danger"],
            "installer_terminal_bg": V3_DARK["bg"],  # indigo profundo runtime spec dark
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
    # Gradiente firma del runtime spec — primary → amber en cada tema.
    "dark_hybrid": [
        ("#A99CFF", 0.0),
        ("#C8A89B", 0.5),
        ("#E8B86A", 1.0),
    ],
    "light_hybrid": [
        ("#305A48", 0.0),
        ("#7B7140", 0.5),
        ("#C68A2E", 1.0),
    ],
    # Pares (start, end) — claves compatibility preservadas (re-mapeadas al runtime spec)
    "accent_teal_violet_dark": ("#A99CFF", "#E8B86A"),
    "accent_teal_violet_light": ("#305A48", "#C68A2E"),
}


# ============================================================
# SHADOWS · strings CSS-like preservados (consumidores existentes)
# ============================================================

SHADOWS = {
    # Strings CSS-like preservados (consumidores compatibility). Valores re-mapeados al
    # runtime spec §2.3: tono ink en light, negro en dark con opacidades 0.25–0.45.
    "dark": {
        "card": "0 10px 30px rgba(0,0,0,0.35)",
        "card_hover": "0 18px 44px rgba(0,0,0,0.45), 0 0 1px rgba(169,156,255,0.22)",
        "glow_teal": "0 0 40px rgba(169,156,255,0.22), 0 0 16px rgba(169,156,255,0.12)",
    },
    "light": {
        "card": "0 4px 12px rgba(28,34,24,0.04), 0 1px 0 rgba(28,34,24,0.04)",
        "card_hover": "0 12px 32px rgba(28,34,24,0.07), 0 2px 4px rgba(28,34,24,0.04)",
        "glow_teal": "0 4px 20px rgba(48,90,72,0.20)",
    },
}


TRANSITIONS = {
    "fast": 150,
    "normal": 250,
    "slow": 350,
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
    # Categorías de activación conductual — alineadas a la paleta del runtime spec
    # (linen+sage / indigo profundo) sin perder distinción semántica.
    "Autocuidado": "#4D7A52",  # runtime spec success  — salud, autocuidado
    "Física": "#2F7E73",  # runtime spec teal     — movimiento, energía
    "Cognitiva": "#305A48",  # primary — mente, claridad
    "Placer": "#B8633B",  # runtime spec accent   — disfrute, creatividad
    "Social": "#C68A2E",  # runtime spec warning  — calidez, conexión
    "Maestría": "#A99CFF",  # dark primary — logro, habilidades
}
