from __future__ import annotations

from pathlib import Path


# Vistas que existen en la app pero NO en el mockup: extras deliberados que el
# plan manda conservar (más completos que el mockup) y por eso no tienen target
# de fidelidad. Mantener esta lista explícita evita que un recipe huérfano pase
# inadvertido, sin exigir un target inexistente.
#   - ('suite', 'dbt-history'): tab Historial de DBT — "Conservar tab Historial
#     (extra app)" (PLAN_MIGRACION_UI.md, sección de huecos/diferencias).
_APP_EXTRA_RECIPES_WITHOUT_MOCKUP = {
    ("suite", "dbt-history"),
}


def test_mockup_targets_cover_capture_v8_recipes() -> None:
    from qa.capture_mockup import MOCKUP_TARGETS
    from qa.capture_v8 import _RECIPES

    all_recipes = {
        (app, view)
        for app, recipes in _RECIPES.items()
        for view in recipes
    }
    # Los extras de la app deben seguir existiendo como recipes (la lista no se
    # vuelve stale), pero se excluyen de la cobertura de targets del mockup.
    assert _APP_EXTRA_RECIPES_WITHOUT_MOCKUP <= all_recipes
    expected = all_recipes - _APP_EXTRA_RECIPES_WITHOUT_MOCKUP
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
