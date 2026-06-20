from __future__ import annotations

from pathlib import Path


def test_mockup_targets_cover_capture_v8_recipes() -> None:
    from qa.capture_mockup import MOCKUP_TARGETS
    from qa.capture_v8 import _RECIPES

    expected = {
        (app, view)
        for app, recipes in _RECIPES.items()
        for view in recipes
    }
    actual = {(target.app, target.view) for target in MOCKUP_TARGETS}

    assert actual == expected


def test_modal_target_uses_child_capture_filename() -> None:
    from qa.capture_mockup import MOCKUP_TARGETS

    target = next(t for t in MOCKUP_TARGETS if t.view == "detalle-resumen-ia")

    assert target.output_view == "detalle-resumen-ia-0"
    assert target.resolution == "480x325"
    assert target.capture == "modal"


def test_parse_capture_name_with_greedy_view() -> None:
    from qa.diff_fidelity import parse_capture_name

    parsed = parse_capture_name(Path("hub-detalle-resumen-ia-0-dark-480x325.png"))

    assert parsed is not None
    assert parsed.app == "hub"
    assert parsed.view == "detalle-resumen-ia-0"
    assert parsed.theme == "dark"
    assert parsed.resolution == "480x325"
