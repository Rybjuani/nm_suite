from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from tests.e2e._helpers.visual_parity import (
    VisualParityThresholds,
    assert_visual_parity,
    compare_visual_parity,
    load_canonical_index,
    write_visual_parity_report,
)


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_visual]


def _write_png(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (32, 24)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def _canonical_root(tmp_path: Path) -> Path:
    root = tmp_path / "canonical"
    _write_png(root / "suite-home-light-32x24.png", (245, 240, 230))
    manifest = {
        "mockup_sha256": "test-sha",
        "all_captured": True,
        "all_sizes_match": True,
        "all_dom_sizes_match": True,
        "captures": [
            {
                "file": "suite-home-light-32x24.png",
                "view": "suite-home",
                "screen": "home",
                "state": "score",
                "surface": "window",
                "theme": "light",
                "real_w": 32,
                "real_h": 24,
                "expected_w": 32,
                "expected_h": 24,
                "size_match": True,
                "dom_w": 32,
                "dom_h": 24,
                "dom_size_match": True,
                "capture_selector": ".window",
            }
        ],
    }
    (root / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_load_canonical_index_resolves_surface_key(tmp_path):
    root = _canonical_root(tmp_path)

    index = load_canonical_index(root)

    surface = index.resolve("suite:home@light")
    assert surface is not None
    assert surface.path.name == "suite-home-light-32x24.png"
    assert index.resolve("suite-home-light-32x24.png") == surface


def test_compare_visual_parity_passes_identical_image(tmp_path):
    root = _canonical_root(tmp_path)
    actual = tmp_path / "actual.png"
    _write_png(actual, (245, 240, 230))

    result = assert_visual_parity(
        actual,
        "suite:home@light",
        canonical_root=root,
        out_dir=tmp_path / "out",
    )

    assert result.status == "PASS"
    assert result.repair_decision == "NONE"
    assert result.diff_path and result.diff_path.exists()
    assert result.report_path and result.report_path.exists()


def test_compare_visual_parity_builds_repair_package_for_visual_delta(tmp_path):
    root = _canonical_root(tmp_path)
    actual = tmp_path / "actual.png"
    _write_png(actual, (245, 240, 230))
    image = Image.open(actual).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 6, 18, 13), fill=(40, 80, 160))
    image.save(actual)

    result = compare_visual_parity(
        actual,
        "suite:home@light",
        canonical_root=root,
        out_dir=tmp_path / "out",
        thresholds=VisualParityThresholds(
            min_ssim=0.0,
            max_mean_abs_diff=0.001,
            max_changed_pixel_ratio=0.01,
            strong_fail_changed_pixel_ratio=0.5,
            strong_fail_region_area_ratio=0.5,
        ),
    )

    assert result.status == "FAIL"
    assert result.repair_decision == "FIX_PRODUCT_REVIEW"
    assert result.regions
    assert result.agent_package["largest_regions"][0]["hint"] == "text_icon_or_antialiasing"
    assert result.diff_path and result.diff_path.exists()


def test_compare_visual_parity_classifies_size_mismatch_as_pairing_fix(tmp_path):
    root = _canonical_root(tmp_path)
    actual = tmp_path / "actual.png"
    _write_png(actual, (245, 240, 230), size=(20, 20))

    result = compare_visual_parity(
        actual,
        "suite:home@light",
        canonical_root=root,
        out_dir=tmp_path / "out",
    )

    assert result.status == "SIZE_MISMATCH"
    assert result.repair_decision == "PAIRING_FIX"
    assert "size_mismatch" in result.failures


def test_write_visual_parity_report(tmp_path):
    root = _canonical_root(tmp_path)
    actual = tmp_path / "actual.png"
    _write_png(actual, (245, 240, 230))
    result = compare_visual_parity(
        actual,
        "suite:home@light",
        canonical_root=root,
        out_dir=tmp_path / "surface-out",
    )

    paths = write_visual_parity_report([result], tmp_path / "report")

    assert Path(paths["json"]).exists()
    assert Path(paths["markdown"]).read_text(encoding="utf-8").startswith(
        "# E2E visual parity repair queue"
    )
