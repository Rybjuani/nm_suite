"""Compatibility view over the runtime visual tokens.

The visual data lives in :mod:`shared.theme`.  This module keeps the older
``shared.design_tokens`` import path working for callers that expect simple
Python dictionaries such as ``LIGHT``, ``DARK`` and ``MOOD_PALETTE``.
"""

from __future__ import annotations

from shared import theme as _theme

V3_LIGHT = _theme.V3_LIGHT
V3_DARK = _theme.V3_DARK
V3_SPACE = _theme.V3_SPACE
V3_RADIUS = _theme.V3_RADIUS
V3_SHADOWS = _theme.V3_SHADOWS
V3_GRADIENTS = _theme.V3_GRADIENTS

MOOD_PALETTE = _theme.MOOD_PALETTE
TYPOGRAPHY = _theme.TYPOGRAPHY
SPACING = V3_SPACE
RADIUS = V3_RADIUS
SHADOWS = V3_SHADOWS


def _compat_palette(palette: dict[str, str], *, dark: bool) -> dict[str, str]:
    category = _theme.CATEGORY_COLORS
    bg_hover = "rgba(255, 255, 255, 0.06)" if dark else palette["surface_hover"]
    result = {
        "bg_canvas": palette["bg"],
        "bg_sidebar": palette["bgSidebar"],
        "bg_surface": palette["surface"],
        "bg_surface2": palette["surface2"],
        "bg_input": palette["surface2"],
        "bg_hover": bg_hover,
        "ink_primary": palette["text"],
        "ink_secondary": palette["textMuted"],
        "ink_placeholder": palette.get("text4", palette["textMuted"]),
        "ink_disabled": palette.get("text4", palette["textMuted"]),
        "primary": palette["primary"],
        "primary_soft": palette["primary_soft"],
        "accent": palette["accent"],
        "accent_soft": palette["accentSoft"],
        "teal": palette["teal"],
        "amber": palette["amber"],
        "violet": palette["violet"],
        "lavender": palette.get("lavender", palette["primary"]),
        "success_bg": palette["successSoftSolid"],
        "success_ink": palette["success"],
        "warning_bg": palette["warningSoftSolid"],
        "warning_ink": palette["warning"],
        "danger_bg": palette["dangerSoftSolid"],
        "danger_ink": palette["danger"],
        "info_bg": palette.get("tealSoftSolid", palette["surface2"]),
        "info_ink": palette["teal"],
        "border": palette["border"],
        "border_strong": palette["borderStrong"],
        "border_solid": palette["borderSolid"],
        "border_focus": palette["primary"],
        "shadow_color": "rgba(0, 0, 0, 0.30)" if dark else "rgba(28, 34, 24, 0.08)",
        "cat_autocuidado": category["Autocuidado"],
        "cat_fisica": category["Física"],
        "cat_cognitiva": category["Cognitiva"],
        "cat_placer": category["Placer"],
        "cat_social": category["Social"],
        "cat_maestria": category["Maestría"],
        "bg_0": palette["bg_0"],
        "bg_1": palette["bg_1"],
        "surface": palette["surface"],
        "surface_2": palette["surface_2"],
        "canvas": palette.get("canvas", palette["bg"]),
        "card": palette["card"],
        "sidebar": palette["sidebar"],
        "ink": palette["ink"],
        "sage": palette["sage"] if not dark else palette["lavender"],
        "terracotta": palette["terracotta"],
        "aqua": palette["aqua"],
        "line": palette["line"],
        "line_strong": palette["line_strong"],
    }
    if dark:
        result["green"] = palette["green"]
        result["deep"] = palette["deep"]
    return result


LIGHT = _compat_palette(V3_LIGHT, dark=False)
DARK = _compat_palette(V3_DARK, dark=True)

LAYOUT = {
    **_theme.LAYOUT,
    "card_gap": _theme.LAYOUT["gap_cards"],
    "card_padding": _theme.LAYOUT["padding_card"],
    "container_padding": _theme.LAYOUT["padding_container"],
}


def get_token(key: str, theme: str = "dark") -> str:
    """Return a token value from the compatibility palette."""
    palette = LIGHT if theme == "light" else DARK
    return palette.get(key, "#888888")


def get_mood(level: int) -> dict:
    """Return the mood descriptor for a clamped 1-10 level."""
    return _theme.get_mood(level)


def primary(theme: str = "dark") -> str:
    return get_token("primary", theme)


def accent(theme: str = "dark") -> str:
    return get_token("accent", theme)


def bg_canvas(theme: str = "dark") -> str:
    return get_token("bg_canvas", theme)


def bg_surface(theme: str = "dark") -> str:
    return get_token("bg_surface", theme)


def ink_primary(theme: str = "dark") -> str:
    return get_token("ink_primary", theme)


def ink_secondary(theme: str = "dark") -> str:
    return get_token("ink_secondary", theme)
