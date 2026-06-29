"""Tests for the density-aware SSIM gate in qa/layered_visual_compare.py.

Text-dense / low-contrast canonicals (520x600 forms) cannot reach the global
single-window SSIM bar (hard ~0.55 floor from Qt-vs-Chromium text rasterisation),
so for those surfaces the SSIM layer uses windowed SSIM. All other layers
(mean_abs_diff, changed_pixel_ratio, ...) and the anti-fraud controls stay at
full strength for every surface.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from qa.layered_visual_compare import (
    LayeredThresholds,
    _raw_fail,
    _windowed_ssim,
    compare_pair,
    parse_capture_name,
)

T = LayeredThresholds()


def _m(**kw):
    base = dict(
        ssim=1.0,
        windowed_ssim=1.0,
        canonical_gray_std=50.0,
        mean_abs_diff=0.0,
        changed_pixel_ratio=0.0,
    )
    base.update(kw)
    return base


def test_dense_surface_uses_windowed_and_passes_low_global_ssim():
    # Global SSIM far below 0.92, but windowed above the floor on a text-dense
    # surface, with other layers clean -> not a raw fail.
    assert _raw_fail(
        _m(ssim=0.52, windowed_ssim=0.70, canonical_gray_std=22.0,
           mean_abs_diff=0.03, changed_pixel_ratio=0.05),
        T,
    ) is False


def test_dense_surface_windowed_below_floor_fails():
    assert _raw_fail(_m(ssim=0.52, windowed_ssim=0.60, canonical_gray_std=22.0), T) is True


def test_sparse_surface_is_unaffected_and_uses_global_ssim():
    # Sparse: windowed is ignored; strict global SSIM applies.
    assert _raw_fail(_m(ssim=0.95, windowed_ssim=0.40, canonical_gray_std=57.0), T) is False
    assert _raw_fail(_m(ssim=0.80, windowed_ssim=0.99, canonical_gray_std=57.0), T) is True


def test_dense_changed_ratio_layer_stays_strict():
    # Passes windowed but changed_ratio over limit -> still fails (divergence kept).
    assert _raw_fail(
        _m(windowed_ssim=0.90, canonical_gray_std=22.0, changed_pixel_ratio=0.12), T
    ) is True


def test_dense_mean_abs_diff_layer_stays_strict():
    assert _raw_fail(
        _m(windowed_ssim=0.90, canonical_gray_std=22.0, mean_abs_diff=0.05), T
    ) is True


def test_windowed_ssim_identical_is_one():
    a = np.random.RandomState(0).randint(0, 255, (40, 40)).astype(float)
    assert _windowed_ssim(a, a.copy()) > 0.999


def test_windowed_ssim_drops_for_unrelated():
    rng = np.random.RandomState(1)
    a = rng.randint(0, 255, (40, 40)).astype(float)
    b = rng.randint(0, 255, (40, 40)).astype(float)
    assert _windowed_ssim(a, b) < 0.5


def test_thresholds_serialized():
    d = LayeredThresholds().to_dict()
    assert d["text_dense_canonical_std"] == 35.0
    assert d["text_dense_min_windowed_ssim"] == 0.65


def test_compare_pair_emits_density_metrics_and_classifies_dense(tmp_path):
    can = tmp_path / "c" / "suite-recuperar-acceso-light-200x200.png"
    act = tmp_path / "a" / "suite-recuperar-acceso-light-200x200.png"
    for p in (can, act):
        p.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (200, 200), (245, 240, 232))
        d = ImageDraw.Draw(img)
        for y in range(20, 180, 16):
            d.line((16, y, 184, y), fill=(90, 90, 90))
        img.save(p)

    r = compare_pair(
        "suite:recuperar-acceso@light",
        parse_capture_name(can),
        parse_capture_name(act),
        thresholds=LayeredThresholds(),
        use_odiff=False,
    )
    assert "windowed_ssim" in r.metrics
    assert "canonical_gray_std" in r.metrics
    assert r.metrics["canonical_gray_std"] < 35.0  # classified text-dense
