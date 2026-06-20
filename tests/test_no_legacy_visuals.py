"""Current visual-layer contracts with no historical value locks."""

from __future__ import annotations

from pathlib import Path

from shared import design_tokens, theme

ROOT = Path(__file__).resolve().parent.parent


def test_design_token_helpers_read_the_runtime_catalog():
    for mode, palette in (("light", theme.V3_LIGHT), ("dark", theme.V3_DARK)):
        assert design_tokens.primary(mode) == palette["primary"]
        assert design_tokens.accent(mode) == palette["accent"]
        assert design_tokens.bg_canvas(mode) == palette["bg"]
        assert design_tokens.bg_surface(mode) == palette["surface"]
        assert design_tokens.ink_primary(mode) == palette["text"]
        assert design_tokens.ink_secondary(mode) == palette["textMuted"]


def test_runtime_visual_tokens_do_not_lock_old_adn_values():
    legacy_values = {
        "#F4EFE5",
        "#305A48",
        "#07091A",
        "#A99CFF",
        "Manrope",
        "Newsreader",
    }
    runtime_values = []
    for source in (theme.V3_LIGHT, theme.V3_DARK, theme.TYPOGRAPHY):
        for value in source.values():
            if isinstance(value, str):
                runtime_values.append(value)
            elif isinstance(value, list):
                runtime_values.extend(str(item) for item in value)

    joined = "\n".join(runtime_values)
    for legacy in legacy_values:
        assert legacy not in joined


def test_removed_component_metadata_modules_are_not_importable():
    assert not (ROOT / "shared" / "components" / "registry.py").exists()
    assert not (ROOT / "shared" / "components" / "base.py").exists()
