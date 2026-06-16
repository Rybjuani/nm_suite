from __future__ import annotations

import sys

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
