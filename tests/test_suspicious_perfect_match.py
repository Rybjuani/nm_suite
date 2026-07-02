"""Tests for SUSPICIOUS_PERFECT_MATCH detection in qa/layered_visual_compare.py.

A pixel-identical capture on a non-trivial surface is the signature of a
reference-artifact injection (the recovery overlay fraud). It must be flagged
and must block closure, with an explicit exception for trivial empty states.
"""

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


def _content_png(path: Path, *, size=(120, 80)):
    """Draw a non-trivial image (grayscale std well above the trivial epsilon)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, (245, 240, 230))
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 60, 40), fill=(30, 60, 40))
    d.rectangle((64, 44, 112, 72), fill=(180, 90, 70))
    d.line((0, 0, size[0], size[1]), fill=(10, 10, 10), width=2)
    for x in range(0, size[0], 8):
        d.line((x, 0, x, size[1]), fill=(120, 120, 120))
    img.save(path)


def _solid_png(path: Path, color=(245, 240, 230), size=(120, 80)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def test_perfect_match_on_nontrivial_surface_is_suspicious(tmp_path):
    canonical = tmp_path / "c" / "suite-home-light-120x80.png"
    actual = tmp_path / "a" / "suite-home-light-120x80.png"
    _content_png(canonical)
    _content_png(actual)  # identical content -> perfect match

    result = compare_pair(
        "suite:home@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.suspicious_perfect_match is True
    assert result.status == "SUSPICIOUS_PERFECT_MATCH"
    assert result.real_divergence is True
    assert "suspicious_perfect_match" in result.findings
    assert result.status != "PASS"


def test_empty_state_view_is_exempt(tmp_path):
    canonical = tmp_path / "c" / "suite-timer-empty-light-120x80.png"
    actual = tmp_path / "a" / "suite-timer-empty-light-120x80.png"
    _content_png(canonical)
    _content_png(actual)

    result = compare_pair(
        "suite:timer-empty@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.suspicious_perfect_match is False
    assert result.status == "PASS"


def test_flat_surface_perfect_match_is_trivial(tmp_path):
    canonical = tmp_path / "c" / "suite-home-light-120x80.png"
    actual = tmp_path / "a" / "suite-home-light-120x80.png"
    _solid_png(canonical)
    _solid_png(actual)

    result = compare_pair(
        "suite:home@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.suspicious_perfect_match is False
    assert result.status == "PASS"


def test_nontrivial_but_different_is_not_suspicious(tmp_path):
    canonical = tmp_path / "c" / "suite-home-light-120x80.png"
    actual = tmp_path / "a" / "suite-home-light-120x80.png"
    _content_png(canonical)
    _content_png(actual)
    img = Image.open(actual).convert("RGB")
    ImageDraw.Draw(img).rectangle((20, 20, 100, 60), fill=(0, 0, 200))
    img.save(actual)

    result = compare_pair(
        "suite:home@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.suspicious_perfect_match is False
    assert result.status == "FAIL"


def test_near_perfect_match_on_nontrivial_surface_is_audit_required(tmp_path):
    canonical = tmp_path / "c" / "suite-home-light-120x80.png"
    actual = tmp_path / "a" / "suite-home-light-120x80.png"
    _content_png(canonical)
    _content_png(actual)
    img = Image.open(actual).convert("RGB")
    px = img.load()
    px[12, 12] = (255, 255, 255)
    px[13, 12] = (255, 255, 255)
    img.save(actual)

    result = compare_pair(
        "suite:home@light",
        parse_capture_name(canonical),
        parse_capture_name(actual),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )

    assert result.suspicious_perfect_match is False
    assert result.near_perfect_match is True
    assert result.status == "NEAR_PERFECT_MATCH"
    assert result.repair_bucket == "AUDIT_REQUIRED"
    assert result.real_divergence is True
    assert "near_perfect_match" in result.findings


def test_near_perfect_match_blocks_closure_in_report(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    canonical = tmp_path / "c" / "suite-home-light-120x80.png"
    actual = tmp_path / "a" / "suite-home-light-120x80.png"
    _content_png(canonical)
    _content_png(actual)
    img = Image.open(actual).convert("RGB")
    ImageDraw.Draw(img).point((12, 12), fill=(255, 255, 255))
    img.save(actual)

    _results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=True,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))

    assert payload["summary"]["near_perfect_match"] == 1
    assert payload["summary"]["pass"] == 0
    assert payload["handoff_closure_allowed"] is False
    assert payload["results"][0]["near_perfect_match"] is True
    assert payload["results"][0]["status"] == "NEAR_PERFECT_MATCH"


def test_suspicious_match_blocks_closure_in_report(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_CANONICAL", tmp_path / "c")
    monkeypatch.setattr("qa.layered_visual_compare._DEFAULT_ACTUAL", tmp_path / "a")
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _content_png(tmp_path / "c" / "suite-home-light-120x80.png")
    _content_png(tmp_path / "a" / "suite-home-light-120x80.png")

    results, reports = compare_sources(
        tmp_path / "c",
        tmp_path / "a",
        tmp_path / "out",
        thresholds=LayeredThresholds(),
        use_odiff=True,
        write_panels=True,
    )
    payload = json.loads(Path(reports["json"]).read_text(encoding="utf-8"))
    assert payload["summary"]["suspicious_perfect_match"] == 1
    assert payload["summary"]["pass"] == 0
    assert payload["handoff_closure_allowed"] is False
    assert payload["results"][0]["suspicious_perfect_match"] is True
    assert payload["results"][0]["status"] == "SUSPICIOUS_PERFECT_MATCH"
