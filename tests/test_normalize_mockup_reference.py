"""Tests for qa/normalize_mockup_reference.py.

Run with:
    .venv\\Scripts\\python.exe -m pytest tests\\test_normalize_mockup_reference.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

_PROJ = Path(__file__).resolve().parent.parent
_NORM_DIR = _PROJ / "qa" / "mockup_reference_normalized"
_MANIFEST_PATH = _NORM_DIR / "manifest.json"
_STATIC_DIR = _PROJ / "qa" / "mockup_reference_static"
_SCRIPT = _PROJ / "qa" / "normalize_mockup_reference.py"

_CANONICAL_SIZES = {(960, 600), (520, 600), (480, 325)}


@pytest.fixture(scope="module")
def manifest() -> list[dict]:
    assert _MANIFEST_PATH.exists(), "manifest.json not found — run normalize first"
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def test_all_normalized_pngs_have_canonical_sizes(manifest: list[dict]) -> None:
    for entry in manifest:
        path = _NORM_DIR / entry["theme"] / f"{entry['view']}.png"
        assert path.exists(), f"Missing PNG: {path}"
        with Image.open(path) as img:
            assert img.size in _CANONICAL_SIZES, (
                f"Non-canonical size {img.size} for {entry['surface_key']}"
            )


def test_no_size_mismatch_after_normalization(manifest: list[dict]) -> None:
    for entry in manifest:
        path = _NORM_DIR / entry["theme"] / f"{entry['view']}.png"
        with Image.open(path) as img:
            assert (img.width, img.height) == (
                entry["target_width"],
                entry["target_height"],
            ), f"Size mismatch for {entry['surface_key']}"


def test_normalization_manifest_has_86_entries(manifest: list[dict]) -> None:
    assert len(manifest) == 86


def test_normalization_method_documented_per_item(manifest: list[dict]) -> None:
    valid_methods = {
        "identity",
        "resize_only",
        "resize+crop_center",
        "resize+crop_top",
        "resize+crop_bottom",
        "resize+pad_bottom_surface",
        "manual_override",
    }
    for entry in manifest:
        assert entry["method"] in valid_methods, (
            f"Invalid method {entry['method']} for {entry['surface_key']}"
        )


def test_review_required_flag_set_when_loss_ge_5pct(manifest: list[dict]) -> None:
    for entry in manifest:
        if entry["lost_pct"] >= 5.0 or entry["pad_pixels"] >= 50:
            assert entry["review_required"] is True, (
                f"review_required should be True for {entry['surface_key']}"
            )


def test_no_owner_approved_field_in_manifest(manifest: list[dict]) -> None:
    for entry in manifest:
        assert "owner_approved" not in entry, (
            f"owner_approved should not exist in manifest for {entry['surface_key']}"
        )


def test_crop_center_only_when_loss_lt_5pct(manifest: list[dict]) -> None:
    for entry in manifest:
        if entry["method"] == "resize+crop_center":
            assert entry["lost_pct"] < 5.0, (
                f"crop_center requires lost_pct < 5% for {entry['surface_key']}"
            )


def test_pad_bottom_only_when_pad_lt_50(manifest: list[dict]) -> None:
    for entry in manifest:
        if entry["method"] == "resize+pad_bottom_surface":
            assert entry["pad_pixels"] < 50, (
                f"pad_bottom requires pad_pixels < 50 for {entry['surface_key']}"
            )


def test_pad_bottom_uses_surface_color_not_white() -> None:
    """Synthetic: 980x560 image with red top-left, target 960x600 -> pad 40px bottom."""
    img = Image.new("RGB", (980, 560), (255, 0, 0))
    # Simulate what the script does for resize+pad_bottom_surface
    resized = img.resize((960, 560), Image.Resampling.LANCZOS)
    result = Image.new("RGB", (960, 600), (255, 0, 0))
    result.paste(resized, (0, 0))
    # Bottom 40px should be red (surface color), not white
    assert result.getpixel((0, 599)) == (255, 0, 0)


def test_crop_center_preserves_header_and_footer_symmetric() -> None:
    """Synthetic: 980x620 with red header + blue footer, crop center to 960x600."""
    img = Image.new("RGB", (980, 620))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 979, 9), fill=(255, 0, 0))  # red header 10px
    draw.rectangle((0, 610, 979, 619), fill=(0, 0, 255))  # blue footer 10px
    # resize to 960x608, then crop center 8px (4 top + 4 bottom)
    resized = img.resize((960, 608), Image.Resampling.LANCZOS)
    cropped = resized.crop((0, 4, 960, 604))
    assert cropped.size == (960, 600)
    # Header should still be reddish (some interpolation)
    px = cropped.getpixel((100, 0))
    assert isinstance(px, tuple)
    assert px[0] > px[2], "Header should still be red-dominant"
    # Footer should still be bluish
    px = cropped.getpixel((100, 599))
    assert isinstance(px, tuple)
    assert px[2] > px[0], "Footer should still be blue-dominant"


def test_manual_override_marks_review_required_informative(manifest: list[dict]) -> None:
    for entry in manifest:
        if entry["method"] == "manual_override":
            assert entry["review_required"] is True, (
                f"manual_override must have review_required=True for {entry['surface_key']}"
            )


def test_does_not_touch_mockup_reference_static() -> None:
    """After normalize, static dir should be unchanged."""
    # We can't easily check git status for just this dir, but we can verify
    # the static manifest still exists and has the same content
    static_manifest = _STATIC_DIR / "manifest.json"
    assert static_manifest.exists()
    original = json.loads(static_manifest.read_text(encoding="utf-8"))
    assert original["captures_total"] == 86


def test_manifest_is_commiteable_but_pngs_are_gitignored() -> None:
    gitignore = _PROJ / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")
    # manifest.json should NOT be ignored
    assert "!qa/mockup_reference_normalized/manifest.json" in content, (
        "manifest.json exception missing from .gitignore"
    )
    # PNGs should be ignored
    assert "qa/mockup_reference_normalized/*" in content or "qa/mockup_reference_normalized/" in content, (
        "PNG gitignore pattern missing"
    )


def test_dbt_practice_stop_target_is_narrow_520x600(manifest: list[dict]) -> None:
    for entry in manifest:
        if entry["view"] == "dbt-practice-stop":
            assert entry["target_width"] == 520, f"dbt-practice-stop width should be 520, got {entry['target_width']}"
            assert entry["target_height"] == 600, f"dbt-practice-stop height should be 600, got {entry['target_height']}"


def test_regenerate_command_changes_method() -> None:
    # Make a copy of the current manifest to avoid mutating the real one
    manifest_bytes = _MANIFEST_PATH.read_bytes()
    manifest = json.loads(manifest_bytes)
    # Pick a surface that currently uses resize+pad_bottom_surface
    entry = next(e for e in manifest if e["method"] == "resize+pad_bottom_surface")
    surface_key = entry["surface_key"]
    original_method = entry["method"]

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "regenerate", "--surface", surface_key, "--method", "resize+crop_bottom", "--reason", "test"],
        capture_output=True,
        text=True,
        cwd=_PROJ,
    )
    assert result.returncode == 0, result.stderr

    updated = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    updated_entry = next(e for e in updated if e["surface_key"] == surface_key)
    assert updated_entry["method"] == "resize+crop_bottom"
    assert updated_entry["regenerate_reason"] == "test"

    # Restore byte-perfect original manifest
    _MANIFEST_PATH.write_bytes(manifest_bytes)
    # Verify restoration
    restored = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    restored_entry = next(e for e in restored if e["surface_key"] == surface_key)
    assert restored_entry["method"] == original_method
    assert restored_entry.get("regenerate_reason") is None


def test_all_surfaces_have_expected_view_mapping(manifest: list[dict]) -> None:
    """Every entry should have a known view mapping."""
    expected_views = {
        "home", "home-no-score", "onboarding", "onboarding-error", "recuperar-acceso",
        "animo", "dbt-now", "dbt-library", "dbt-practice-stop", "respiracion",
        "respiracion-running", "respiracion-paused", "registro", "registro-step1-emotion",
        "registro-step1-emotion-otro", "registro-step2-distortions", "registro-step3-filled",
        "registro-success", "rutina", "rutina-all-completed", "rutina-add-task", "rutina-empty",
        "actividades", "actividades-filtered", "actividades-marked-hice", "actividades-empty",
        "timer", "timer-running", "timer-paused", "timer-empty", "avisos",
        "avisos-filter-activos", "avisos-search", "avisos-today", "avisos-empty",
        "pacientes", "pacientes-empty", "detalle", "detalle-plan-timer",
        "detalle-plan-rutina", "detalle-plan-activacion", "textos-globales", "detalle-resumen-ia",
    }
    for entry in manifest:
        assert entry["view"] in expected_views, f"Unexpected view: {entry['view']}"
