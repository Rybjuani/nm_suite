from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from qa.layered_visual_compare import (
    LayeredThresholds,
    compare_pair,
    compare_sources,
    parse_capture_name,
)


def _png(path: Path, color=(245, 240, 230), size=(120, 80)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def test_parse_capture_name():
    parsed = parse_capture_name(Path("suite-home-light-960x600.png"))

    assert parsed is not None
    assert parsed.key == "suite:home@light"
    assert parsed.resolution == "960x600"


def test_identical_pair_passes(tmp_path):
    canonical = tmp_path / "c" / "suite-home-light-120x80.png"
    actual = tmp_path / "a" / "suite-home-light-120x80.png"
    _png(canonical)
    _png(actual)

    result = compare_pair(
        "suite:home@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.status == "PASS"
    assert result.real_divergence is False


def test_size_mismatch_is_pairing_fix(tmp_path):
    canonical = tmp_path / "c" / "hub-detalle-resumen-ia-0-light-120x80.png"
    actual = tmp_path / "a" / "hub-detalle-resumen-ia-0-light-100x90.png"
    _png(canonical, size=(120, 80))
    _png(actual, size=(100, 90))

    result = compare_pair(
        "hub:detalle-resumen-ia-0@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.status == "SIZE_MISMATCH"
    assert result.repair_bucket == "PAIRING_FIX"
    assert "size_mismatch" in result.findings


def test_state_sensitive_delta_is_classified_as_state_or_recipe(tmp_path):
    canonical = tmp_path / "c" / "suite-timer-running-light-120x80.png"
    actual = tmp_path / "a" / "suite-timer-running-light-120x80.png"
    _png(canonical)
    _png(actual)
    image = Image.open(actual).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((35, 18, 95, 62), fill=(40, 80, 160))
    image.save(actual)

    result = compare_pair(
        "suite:timer-running@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(max_changed_pixel_ratio=0.01, max_mean_abs_diff=0.001),
        use_odiff=False,
    )

    assert result.status == "FAIL"
    assert result.repair_bucket == "STATE_RECIPE_OR_PRODUCT_FIX"
    assert "state_or_recipe_suspect" in result.findings


def test_compare_sources_writes_reports(tmp_path):
    canonical_dir = tmp_path / "canonical"
    actual_dir = tmp_path / "actual"
    _png(canonical_dir / "suite-home-light-120x80.png")
    _png(actual_dir / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        canonical_dir,
        actual_dir,
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=False,
        write_panels=False,
    )

    assert len(results) == 1
    assert Path(reports["json"]).exists()
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["summary"]["pass"] == 1
    assert payload["authority"] == "LAYERED_VISUAL_COMPARE"
    assert payload["handoff_closure_allowed"] is False
    assert "Zip inputs are archive/forensics only" in payload["source_policy"]


def test_closure_false_with_non_default_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(min_ssim=0.5),
        use_odiff=True,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["handoff_closure_allowed"] is False
    assert "non_default_thresholds" in payload["handoff_closure_reason"]


def test_closure_false_with_odiff_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=False,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["handoff_closure_allowed"] is False
    assert "odiff_disabled" in payload["handoff_closure_reason"]


def test_closure_false_with_panels_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=True,
        write_panels=False,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["handoff_closure_allowed"] is False
    assert "panels_disabled" in payload["handoff_closure_reason"]


def test_evidence_valid_true_with_one_pass_one_fail(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    # PASS pair
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")
    # FAIL pair
    _png(tmp_path / "c" / "suite-timer-running-light-120x80.png")
    _png(tmp_path / "a" / "suite-timer-running-light-120x80.png", color=(40, 80, 160))

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=True,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["report_evidence_valid"] is True
    assert payload["report_evidence_reason"] is None
    assert payload["handoff_closure_allowed"] is False
    assert "real_divergence_present" in payload["handoff_closure_reason"]
    assert payload["summary"]["pass"] == 1
    assert payload["summary"]["real_divergence"] == 1


def test_evidence_valid_false_with_non_default_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(min_ssim=0.5),
        use_odiff=True,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["report_evidence_valid"] is False
    assert "non_default_thresholds" in payload["report_evidence_reason"]
    assert payload["handoff_closure_allowed"] is False


def test_evidence_valid_false_with_odiff_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=False,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["report_evidence_valid"] is False
    assert "odiff_disabled" in payload["report_evidence_reason"]
    assert payload["handoff_closure_allowed"] is False


def test_evidence_valid_false_with_panels_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=True,
        write_panels=False,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["report_evidence_valid"] is False
    assert "panels_disabled" in payload["report_evidence_reason"]
    assert payload["handoff_closure_allowed"] is False


def test_evidence_valid_and_closure_true_with_all_pass(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _png(tmp_path / "c" / "suite-home-light-120x80.png")
    _png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=True,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["report_evidence_valid"] is True
    assert payload["report_evidence_reason"] is None
    assert payload["handoff_closure_allowed"] is True
    assert payload["handoff_closure_reason"] is None
