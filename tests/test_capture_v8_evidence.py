from __future__ import annotations

import sys
import json
from pathlib import Path

from qa import capture_v8


def _make_result(fname: str) -> dict:
    return {
        "success": True,
        "file": fname,
        "technical_capture_valid": True,
        "evidence_flags": [],
        "evidence_notes": [],
    }


def test_blank_png_invalidated(tmp_path):
    from PIL import Image

    blank = tmp_path / "suite-home-dark-960x600.png"
    Image.new("RGB", (960, 600), "#FFFFFF").save(blank)

    result = _make_result(blank.name)
    capture_v8._apply_content_validation([result], tmp_path)

    assert result["technical_capture_valid"] is False
    assert capture_v8._STATUS_BLANK_OR_FLAT in result["evidence_flags"]
    assert result["content_metrics"]["gray_mean"] > 0.985


def test_flat_png_invalidated(tmp_path):
    from PIL import Image

    flat = tmp_path / "suite-home-dark-960x600.png"
    Image.new("RGB", (960, 600), "#141A38").save(flat)

    result = _make_result(flat.name)
    capture_v8._apply_content_validation([result], tmp_path)

    assert result["technical_capture_valid"] is False
    assert capture_v8._STATUS_BLANK_OR_FLAT in result["evidence_flags"]


def test_corrupt_png_invalidated(tmp_path):
    bad = tmp_path / "suite-home-dark-960x600.png"
    bad.write_bytes(b"not a png at all")

    result = _make_result(bad.name)
    capture_v8._apply_content_validation([result], tmp_path)

    assert result["technical_capture_valid"] is False
    assert "error" in result["content_metrics"]


def test_content_rich_png_stays_valid(tmp_path):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (960, 600), "#141A38")
    draw = ImageDraw.Draw(img)
    for i in range(0, 960, 40):
        draw.rectangle([i, 0, i + 20, 600], fill="#A99CFF")
        draw.rectangle([i, 200, i + 30, 400], fill="#ECECFB")
    path = tmp_path / "suite-home-dark-960x600.png"
    img.save(path)

    result = _make_result(path.name)
    capture_v8._apply_content_validation([result], tmp_path)

    assert result["technical_capture_valid"] is True
    assert capture_v8._STATUS_BLANK_OR_FLAT not in result["evidence_flags"]


def test_capture_provenance_links_key_png_manifest_and_introspection(tmp_path):
    png = tmp_path / "suite-home-light-960x600.png"
    png.write_bytes(b"runtime capture bytes")

    provenance = capture_v8._capture_provenance(
        app_key="suite",
        view_id="home",
        theme="light",
        png_path=png,
        out_dir=tmp_path,
    )

    assert provenance["schema"] == "capture_v8.provenance.v2"
    assert provenance["key"] == "suite:home@light"
    assert provenance["capture_file"] == png.name
    assert provenance["png_sha256"] == capture_v8._sha256_file(png)
    assert provenance["command_args"]
    assert provenance["capture_script_sha256"] == capture_v8._sha256_file(Path(capture_v8.__file__).resolve())
    assert provenance["capture_manifest"].endswith("CAPTURE_MANIFEST.json")
    assert provenance["introspection_sidecar"].endswith("introspection.json")
    assert len(provenance["introspection_entry_id"]) == 64
    assert provenance["state_assertion_sha256"] is None


def test_capture_provenance_signs_state_assertion(tmp_path):
    png = tmp_path / "suite-timer-running-light-960x600.png"
    png.write_bytes(b"runtime capture bytes")
    assertion = {
        "schema": "nm_suite.state_assertion.v1",
        "key": "suite:timer-running@light",
        "pass": True,
        "observed": {"toggle_icon": "pause", "ring_state": "en curso"},
    }

    provenance = capture_v8._capture_provenance(
        app_key="suite",
        view_id="timer-running",
        theme="light",
        png_path=png,
        out_dir=tmp_path,
        state_assertion=assertion,
    )

    from qa.state_probes import state_assertion_sha256

    assert provenance["state_assertion_sha256"] == state_assertion_sha256(assertion)


def test_state_probe_is_evaluated_immediately_before_grab():
    source = Path(capture_v8.__file__).read_text(encoding="utf-8")
    function = source[source.index("def _grab_save(") : source.index("def _scan_and_capture_children(")]

    assert function.index("evaluate_state_probe") < function.index("win.grab()")


def test_capture_v8_clean_only_without_targets(monkeypatch, tmp_path):
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(sys, "argv", ["capture_v8.py", "--clean", "--out-dir", str(tmp_path)])
    monkeypatch.setattr(capture_v8, "_clean_output", lambda out_dir: calls.append(("clean", str(out_dir))) or 0)
    monkeypatch.setattr(
        capture_v8,
        "_capture_matrix_in_subprocesses",
        lambda *args, **kwargs: calls.append(("capture", "")) or [],
    )

    assert capture_v8.main() == 0
    assert calls == [("clean", str(tmp_path))]


def test_capture_v8_clean_with_all_still_captures(monkeypatch, tmp_path):
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        ["capture_v8.py", "--all", "--clean", "--out-dir", str(tmp_path)],
    )
    monkeypatch.setattr(capture_v8, "_RECIPES", {"suite": {"home": {}}, "hub": {}})
    monkeypatch.setattr(capture_v8, "_clean_output", lambda out_dir: calls.append(("clean", str(out_dir))) or 0)
    monkeypatch.setattr(
        capture_v8,
        "_capture_matrix_in_subprocesses",
        lambda *args, **kwargs: calls.append(("capture", "")) or [
            {"success": True, "app": "suite", "view": "home", "theme": "light"}
        ],
    )
    monkeypatch.setattr(
        capture_v8,
        "_finalize_evidence",
        lambda results, out_dir: {
            "state_valid_capture_count": 1,
            "technical_valid_capture_count": 1,
            "technical_960_capture_count": 1,
        },
    )
    monkeypatch.setattr(capture_v8, "_git_metadata", lambda: {})

    assert capture_v8.main() == 0
    assert calls == [("clean", str(tmp_path)), ("capture", "")]


def test_phase0_required_recipes_are_registered():
    suite = capture_v8._RECIPES["suite"]
    for view_id in (
        "actividades-empty",
        "avisos-empty",
        "recuperar-acceso",
        "dbt-now",
        "registro-success",
    ):
        assert view_id in suite
        assert any(action.get("action") == "capture" for action in suite[view_id]["actions"])


def test_canonical_manifest_mockup_path_is_not_a_reports_snapshot():
    for manifest_path in (
        Path("qa/_mockup_canonical/MANIFEST.json"),
        Path("qa/pack canonico/capturas_test/MANIFEST.json"),
    ):
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        mockup_path = str(manifest.get("mockup_path", "")).replace("\\", "/").lower()
        assert "/reports/" not in mockup_path
        assert not mockup_path.endswith("/original_head.html")
        assert mockup_path.endswith("qa/pack canonico/neuromood-mockup_reparado.html")


def test_dbt_v2_practice_recipes_declare_modal_window_overlay_metadata():
    """DBT v2 promotes all 16 practice modals as formal capture surfaces."""
    suite = capture_v8._RECIPES["suite"]
    expected = [
        f"dbt-practice-{practice_id.replace('_', '-')}"
        for practice_id, _label in capture_v8._DBT_CANONICAL_PRACTICES
    ]

    assert len(expected) == 16
    assert all(view_id in suite for view_id in expected)
    all_calls = [
        action
        for view_id in expected
        for action in suite[view_id]["actions"]
        if action.get("action") == "call"
    ]
    assert not any(action.get("func") == "_dbt_start_stop_practice" for action in all_calls)

    for practice_id, _label in capture_v8._DBT_CANONICAL_PRACTICES:
        view_id = f"dbt-practice-{practice_id.replace('_', '-')}"
        actions = suite[view_id]["actions"]
        start_actions = [
            a for a in actions
            if a.get("action") == "call" and a.get("func") == "_dbt_start_practice"
        ]
        assert start_actions
        assert start_actions[-1]["practice_id"] == practice_id

        capture_actions = [a for a in actions if a.get("action") == "capture"]
        assert capture_actions, f"{view_id} recipe must have a capture action"
        capture = capture_actions[-1]
        assert capture["view"] == view_id
        assert capture["surface"] == "window_modal"
        assert capture["modal_capture_scope"] == "window_overlay"
        assert capture["back_screen_key"] == "suite:dbt-library"


def test_capture_matrix_rows_include_phase0_columns():
    result = {
        "success": True,
        "app": "suite",
        "view": "actividades-empty",
        "theme": "dark",
        "requested_resolution": "960x600",
        "capture_status": capture_v8._STATUS_CAPTURED_VALID,
        "file": "suite-actividades-empty-dark-960x600.png",
        "evidence_flags": [],
        "evidence_notes": [],
    }

    rows = capture_v8._matrix_rows([result])

    assert rows == [{
        "producto": "suite",
        "vista": "actividades-empty",
        "estado": "Actividades empty state deterministico",
        "tema": "dark",
        "resolucion": "960x600",
        "receta": "navigate:actividades > call:_actividades_force_empty > drain:6 > capture:actividades-empty",
        "captura": "suite-actividades-empty-dark-960x600.png",
        "inspeccion_manual": "pendiente",
        "resultado": "pendiente",
        "deuda_pendiente": "requiere inspeccion manual",
    }]
