"""Structural parity between the runtime token catalog and compatibility views."""

from shared import design_tokens as dt
from shared import theme


_PALETTE_PAIRS = {
    "bg_canvas": "bg",
    "bg_sidebar": "bgSidebar",
    "bg_surface": "surface",
    "bg_surface2": "surface2",
    "bg_input": "surface2",
    "primary": "primary",
    "primary_soft": "primary_soft",
    "accent": "accent",
    "accent_soft": "accentSoft",
    "teal": "teal",
    "amber": "amber",
    "violet": "violet",
    "ink_primary": "text",
    "ink_secondary": "textMuted",
    "border": "border",
    "border_strong": "borderStrong",
    "border_solid": "borderSolid",
    "border_focus": "primary",
    "bg_0": "bg_0",
    "bg_1": "bg_1",
    "surface": "surface",
    "surface_2": "surface_2",
    "card": "card",
    "sidebar": "sidebar",
    "ink": "ink",
    "terracotta": "terracotta",
    "aqua": "aqua",
    "line": "line",
    "line_strong": "line_strong",
}


def _assert_palette_adapter(adapter: dict[str, str], source: dict[str, str]) -> None:
    for adapter_key, source_key in _PALETTE_PAIRS.items():
        assert adapter[adapter_key] == source[source_key]


def test_design_tokens_palette_adapters_follow_runtime_tokens():
    _assert_palette_adapter(dt.LIGHT, theme.V3_LIGHT)
    _assert_palette_adapter(dt.DARK, theme.V3_DARK)
    assert dt.LIGHT["sage"] == theme.V3_LIGHT["sage"]
    assert dt.LIGHT["canvas"] == theme.V3_LIGHT["canvas"]
    assert dt.DARK["sage"] == theme.V3_DARK["lavender"]
    assert dt.DARK["canvas"] == theme.V3_DARK["bg"]
    assert dt.DARK["green"] == theme.V3_DARK["green"]
    assert dt.DARK["deep"] == theme.V3_DARK["deep"]


def test_design_tokens_structural_scales_reuse_runtime_tokens():
    assert dt.SPACING is theme.V3_SPACE
    assert dt.RADIUS is theme.V3_RADIUS
    assert dt.SHADOWS is theme.V3_SHADOWS
    assert dt.MOOD_PALETTE is theme.MOOD_PALETTE
    assert dt.TYPOGRAPHY is theme.TYPOGRAPHY


def test_design_tokens_layout_aliases_follow_runtime_layout():
    assert dt.LAYOUT["card_gap"] == theme.LAYOUT["gap_cards"]
    assert dt.LAYOUT["card_padding"] == theme.LAYOUT["padding_card"]
    assert dt.LAYOUT["container_padding"] == theme.LAYOUT["padding_container"]
    for key, value in theme.LAYOUT.items():
        assert dt.LAYOUT[key] == value


def test_theme_qt_reexports_runtime_token_objects():
    from shared import theme_qt

    assert theme_qt.COLORS is theme.COLORS
    assert theme_qt.TYPOGRAPHY is theme.TYPOGRAPHY
    assert theme_qt.LAYOUT is theme.LAYOUT
    assert theme_qt.V3_LIGHT is theme.V3_LIGHT
    assert theme_qt.V3_DARK is theme.V3_DARK
    assert theme_qt.V3_SHADOWS is theme.V3_SHADOWS
    assert theme_qt.V3_GRADIENTS is theme.V3_GRADIENTS


def test_spacing_roles_derive_from_v3_space():
    """V3_SPACE_ROLES son aliases de V3_SPACE sin redefinir valores."""
    assert dt.SPACING_ROLES is theme.V3_SPACE_ROLES
    space_values = set(theme.V3_SPACE.values())
    for role, value in theme.V3_SPACE_ROLES.items():
        assert value in space_values, f"V3_SPACE_ROLES[{role!r}] = {value} no existe en V3_SPACE"


def test_scrollbar_deprecated_alias_returns_clinical_style():
    """stylesheet_hidden_scrollbar redirige al estilo clínico (no oculta las barras)."""
    from shared.theme_qt import stylesheet_hidden_scrollbar

    for modo in ("dark_hybrid", "light_hybrid"):
        qss = stylesheet_hidden_scrollbar(modo)
        assert "width: 10px" in qss, f"track vertical debe ser 10px en {modo!r}"
        assert "height: 10px" in qss, f"track horizontal debe ser 10px en {modo!r}"
