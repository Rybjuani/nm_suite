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
    assert dt.VISUAL_DENSITIES is theme.VISUAL_DENSITIES
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


def test_visual_density_contract_keeps_hub_compact_and_scoped():
    from shared import theme_qt

    suite = theme.VISUAL_DENSITIES["suite_comfortable"]
    hub = theme.VISUAL_DENSITIES["hub_professional_compact"]
    for key in (
        "button_height",
        "button_compact_height",
        "input_height",
        "textarea_min_height",
        "tab_height",
        "subtab_height",
        "filter_height",
        "badge_height",
        "chip_height",
        "scrollbar_width",
    ):
        assert hub[key] <= suite[key]

    qss = theme_qt.hub_density_qss("HubMain")
    assert "#HubMain" in qss
    assert "QApplication" not in qss
    assert f"min-height: {hub['button_height']}px" in qss
    assert f"width: {hub['scrollbar_width']}px" in qss
