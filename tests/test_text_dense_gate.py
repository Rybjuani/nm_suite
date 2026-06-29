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
    _image_metrics,
    _raw_fail,
    _windowed_ssim,
    compare_pair,
    parse_capture_name,
)

T = LayeredThresholds()


def _dense_canvas(value: int = 40) -> Image.Image:
    """Low-std (text-dense-like) canonical: near-flat with a few thin lines."""
    img = Image.new("RGB", (200, 200), (value, value, value))
    d = ImageDraw.Draw(img)
    for y in range(20, 180, 24):
        d.line((10, y, 190, y), fill=(value + 18, value + 18, value + 18))
    return img


def _sparse_canvas() -> Image.Image:
    """High-std (sparse) canonical: high-contrast halves."""
    img = Image.new("RGB", (200, 200), (10, 10, 10))
    ImageDraw.Draw(img).rectangle((0, 0, 199, 99), fill=(230, 230, 230))
    return img


def _shift(img: Image.Image, delta: int) -> Image.Image:
    arr = np.asarray(img).astype(np.int16)
    arr[60:140, 60:140] = np.clip(arr[60:140, 60:140] + delta, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


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


def test_dense_changed_ratio_calibrated_floor_passes_above_sparse_bar():
    # Text-dense: changed between the sparse bar (0.08) and the dense bar (0.10)
    # passes, reflecting the irreducible ~0.077 text-AA floor.
    assert _raw_fail(
        _m(windowed_ssim=0.90, canonical_gray_std=22.0, changed_pixel_ratio=0.09), T
    ) is False


def test_dense_high_changed_render_still_fails():
    # Authorization guard: the dense bar (0.10) never closes a poor render by
    # threshold alone. A render still above the bar must raw-fail.
    assert _raw_fail(
        _m(windowed_ssim=0.768, canonical_gray_std=22.5, mean_abs_diff=0.032,
           changed_pixel_ratio=0.118), T
    ) is True


# ── Contrast-aware changed_pixel_floor for text-dense surfaces ──────────────

def test_text_dense_floor_is_calibrated_and_serialized():
    d = LayeredThresholds().to_dict()
    assert d["changed_pixel_floor"] == 12  # sparse / default unchanged
    assert d["text_dense_changed_pixel_floor"] == 14  # contrast-aware dense floor
    # Must stay strictly tighter than a gross-divergence amount, i.e. it only
    # filters near-threshold AA, never large deltas.
    assert d["text_dense_changed_pixel_floor"] < 18


def test_dense_surface_uses_dense_floor_sparse_uses_default():
    # A uniform +13 shift (between 12 and 14): counted as changed on a sparse
    # surface (floor 12) but NOT on a text-dense one (floor 14).
    dense = _dense_canvas()
    sparse = _sparse_canvas()
    assert float(np.asarray(dense).std()) < T.text_dense_canonical_std
    assert float(np.asarray(sparse).std()) >= T.text_dense_canonical_std

    md, _ = _image_metrics(dense, _shift(dense, 13), T)
    ms, _ = _image_metrics(sparse, _shift(sparse, 13), T)
    assert md["changed_pixel_floor"] == 14
    assert ms["changed_pixel_floor"] == 12
    # The +13 region (80x80=6400px) is below the dense floor -> not counted;
    # above the sparse floor -> counted.
    assert md["changed_pixels"] == 0
    assert ms["changed_pixels"] >= 6000


def test_dense_floor_still_counts_structural_divergence():
    # The calibration only filters near-threshold AA. A real structural delta
    # (+40, e.g. a too-bright border/seam) is still counted on a dense surface.
    dense = _dense_canvas()
    md, _ = _image_metrics(dense, _shift(dense, 40), T)
    assert md["changed_pixel_floor"] == 14
    assert md["changed_pixels"] >= 6000  # the +40 region is fully counted


def test_dense_changed_ratio_above_dense_bar_fails():
    assert _raw_fail(
        _m(windowed_ssim=0.90, canonical_gray_std=22.0, changed_pixel_ratio=0.11), T
    ) is True


def test_dense_gross_divergence_still_caught():
    # A wrong-screen / big-divergence amount of changed pixels stays caught.
    assert _raw_fail(
        _m(windowed_ssim=0.90, canonical_gray_std=22.0, changed_pixel_ratio=0.30), T
    ) is True


def test_sparse_changed_ratio_stays_at_strict_bar():
    # Sparse surfaces keep the 0.08 bar; 0.09 fails for them.
    assert _raw_fail(
        _m(ssim=0.95, canonical_gray_std=57.0, changed_pixel_ratio=0.09), T
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
    assert d["text_dense_max_changed_pixel_ratio"] == 0.10
    # Dense changed bar must stay well below a gross-divergence amount (0.118+) so
    # the gate can never close a poor render by threshold alone.
    assert d["text_dense_max_changed_pixel_ratio"] < 0.118


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
