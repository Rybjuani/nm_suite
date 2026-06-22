from __future__ import annotations

from pathlib import Path


_APP_EXTRA_RECIPES_WITHOUT_MOCKUP: set[tuple[str, str]] = set()


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


def test_fidelity_gate_rejects_high_ssim_with_large_pixel_delta() -> None:
    from qa.diff_fidelity import FidelityThresholds, _acceptance_status

    metrics = {
        "ssim": 0.93078,
        "mean_abs_diff": 0.04478,
        "changed_pixel_ratio": 0.10997,
        "size_mismatch": False,
    }

    status, failures = _acceptance_status(metrics, FidelityThresholds(), None)

    assert status == "FAIL"
    assert "mad>0.035" in failures
    assert "changed>0.08" in failures


def test_fidelity_gate_uses_capture_manifest_state_evidence(tmp_path) -> None:
    from PIL import Image
    from qa.diff_fidelity import FidelityThresholds, compare

    target_dir = tmp_path / "targets"
    actual_dir = tmp_path / "actuals"
    out_dir = tmp_path / "report"
    target_dir.mkdir()
    actual_dir.mkdir()
    fname = "suite-home-no-score-light-960x600.png"
    Image.new("RGB", (24, 24), "#E9E3D6").save(target_dir / fname)
    Image.new("RGB", (24, 24), "#E9E3D6").save(actual_dir / fname)
    (actual_dir / "CAPTURE_MANIFEST.json").write_text(
        """
        {
          "results": [{
            "file": "suite-home-no-score-light-960x600.png",
            "capture_status": "REQUIRES_DATA_STATE",
            "technical_capture_valid": true,
            "state_evidence_valid": false,
            "evidence_flags": ["REQUIRES_DATA_STATE"]
          }]
        }
        """,
        encoding="utf-8",
    )

    failures, rows, _ = compare(
        target_dir,
        actual_dir,
        out_dir,
        app=None,
        view="",
        theme="both",
        thresholds=FidelityThresholds(),
        write_images=False,
    )

    assert failures == 1
    assert rows[0]["status"] == "PARTIAL_CAPTURE_EVIDENCE"
    assert rows[0]["capture_status"] == "REQUIRES_DATA_STATE"
    assert rows[0]["acceptance_failures"] == "capture_state_not_product_evidence"
