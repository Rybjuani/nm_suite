#!/usr/bin/env python3
"""Visual gate calibration — NON-CLOSURE technical evidence only.

Measures how the layered visual gate behaves on a set of surfaces WITHOUT
changing any threshold and WITHOUT closing, reclassifying or skipping any
checklist item. It exists to characterise the gate (e.g. why text-dense
surfaces cannot reach the global-SSIM bar) so calibration decisions are made on
data, not assertion.

For each key it reports:
  - ssim, mean_abs_diff, changed_pixel_ratio (the live gate metrics);
  - bbox layout deltas;
  - best ssim achievable with a small (+/-3px) alignment shift;
  - text density (canonical ink fraction) and diff density;
  - estimated ceiling by alignment (best-shift ssim) and by colour
    (ssim if every flat/colour pixel were perfectly matched, leaving only
    strong text edges).

Output: reports/qa/visual_gate_calibration/{CALIBRATION.json,CALIBRATION.md}

This script is explicitly NOT a gate and NOT closure evidence.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qa.layered_visual_compare import (
    LayeredThresholds,
    _DEFAULT_ACTUAL,
    _DEFAULT_CANONICAL,
    _global_ssim,
    _image_metrics,
    _index_images,
    _layout_metrics,
    _load_rgb,
    _windowed_ssim,
)

_PROJ = Path(__file__).resolve().parent.parent
_DEFAULT_OUT = _PROJ / "reports" / "qa" / "visual_gate_calibration"
_DEFAULT_KEYS = (
    "suite:recuperar-acceso@light",
    "suite:onboarding-error@light",
    "suite:onboarding@light",
    "suite:dbt-practice-stop@light",  # sparse control
)
_INK_LUM = 160  # below this grayscale value counts as "ink" (text/borders)


def _gray(img: Image.Image) -> np.ndarray:
    a = np.asarray(img, dtype=np.float64)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def _best_shift_ssim(can: Image.Image, act: Image.Image, radius: int = 3):
    if can.size != act.size:
        act = act.resize(can.size, Image.Resampling.LANCZOS)
    c = _gray(can)
    a = _gray(act)
    H, W = c.shape
    best = (0, 0, _ssim_gray(c, a))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            y0, y1 = max(0, dy), min(H, H + dy)
            x0, x1 = max(0, dx), min(W, W + dx)
            cc = c[y0:y1, x0:x1]
            aa = a[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
            s = _ssim_gray(cc, aa)
            if s > best[2]:
                best = (dx, dy, s)
    return {"dx": best[0], "dy": best[1], "ssim": round(best[2], 5)}


def _ssim_gray(x: np.ndarray, y: np.ndarray) -> float:
    x = x / 255.0
    y = y / 255.0
    c1 = 0.01 ** 2
    c2 = 0.03 ** 2
    mux, muy = float(x.mean()), float(y.mean())
    vx, vy = float(x.var()), float(y.var())
    cov = float(((x - mux) * (y - muy)).mean())
    denom = (mux * mux + muy * muy + c1) * (vx + vy + c2)
    if denom == 0:
        return 1.0 if np.array_equal(x, y) else 0.0
    return ((2 * mux * muy + c1) * (2 * cov + c2)) / denom


def _color_ceiling_ssim(can: Image.Image, act: Image.Image, strong: int = 60) -> float:
    """SSIM if every flat/colour pixel (|diff|<=strong) were perfectly matched,
    leaving only strong text-edge pixels. Estimates the ceiling reachable by
    fixing colours/backgrounds alone."""
    if can.size != act.size:
        act = act.resize(can.size, Image.Resampling.LANCZOS)
    c = np.asarray(can, dtype=np.int16)
    a = np.asarray(act, dtype=np.int16)
    d = np.abs(c - a).max(axis=2)
    sim = a.copy()
    mask = d <= strong
    sim[mask] = c[mask]
    return round(float(_global_ssim(c.astype(np.uint8), sim.astype(np.uint8))), 5)


def _density(can: Image.Image, act: Image.Image) -> dict:
    cg = _gray(can)
    ink_fraction = float((cg < _INK_LUM).mean())
    if can.size != act.size:
        act = act.resize(can.size, Image.Resampling.LANCZOS)
    c = np.asarray(can, dtype=np.int16)
    a = np.asarray(act, dtype=np.int16)
    d = np.abs(c - a).max(axis=2)
    return {
        # Fraction of canonical pixels darker than the ink threshold. NOTE: this
        # conflates real text with large dark regions (e.g. a dimmed backdrop),
        # so it is a raw measurement, not a clean text-vs-chrome discriminator.
        "ink_fraction": round(ink_fraction, 5),
        # Canonical grayscale std: high std = strong large-scale structure that,
        # when it matches, dominates (lifts) global SSIM; low std = bright form
        # where thin non-overlapping text edges dominate covariance.
        "canon_gray_std": round(float(cg.std()), 3),
        "diff_density": round(float((d > 12).mean()), 5),
        "strong_edge_density": round(float((d > 60).mean()), 5),
    }


def calibrate_key(key: str, canonical_index, actual_index) -> dict:
    can_ref = canonical_index.get(key)
    act_ref = actual_index.get(key)
    if can_ref is None or act_ref is None:
        return {
            "key": key,
            "status": "missing",
            "canonical_present": can_ref is not None,
            "actual_present": act_ref is not None,
        }
    gate = LayeredThresholds()
    can = _load_rgb(can_ref.path)
    act = _load_rgb(act_ref.path)
    metrics, _mask = _image_metrics(can, act, gate)
    layout = _layout_metrics(can, act)
    best = _best_shift_ssim(can, act)
    dens = _density(can, act)
    color_ceiling = _color_ceiling_ssim(can, act)
    canon_std = dens["canon_gray_std"]
    is_dense = canon_std < gate.text_dense_canonical_std
    return {
        "key": key,
        "status": "measured",
        "resolution": can_ref.resolution,
        "ssim": metrics["ssim"],
        "windowed_ssim": metrics["windowed_ssim"],
        "gate_class": "text_dense" if is_dense else "sparse",
        "effective_ssim_gate": (
            f"windowed>={gate.text_dense_min_windowed_ssim}" if is_dense
            else f"global>={gate.min_ssim}"
        ),
        "effective_changed_gate": (
            f"changed<={gate.text_dense_max_changed_pixel_ratio}" if is_dense
            else f"changed<={gate.max_changed_pixel_ratio}"
        ),
        "mean_abs_diff": metrics["mean_abs_diff"],
        "changed_pixel_ratio": metrics["changed_pixel_ratio"],
        "bbox": {
            "bbox_dx": layout.get("bbox_dx"),
            "bbox_dy": layout.get("bbox_dy"),
            "bbox_dw": layout.get("bbox_dw"),
            "bbox_dh": layout.get("bbox_dh"),
            "max_bbox_delta_px": layout.get("max_bbox_delta_px"),
        },
        "best_small_shift": best,
        "density": dens,
        "estimated_ceiling": {
            "by_alignment_ssim": best["ssim"],
            "by_color_ssim": color_ceiling,
        },
    }


def run(keys, canonical_dir: Path, actual_dir: Path, out_dir: Path) -> dict:
    canonical_index = _index_images(canonical_dir)
    actual_index = _index_images(actual_dir)
    results = [calibrate_key(k, canonical_index, actual_index) for k in keys]
    gate = LayeredThresholds()
    payload = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "report_kind": "VISUAL_GATE_CALIBRATION",
        "is_closure_evidence": False,
        "note": (
            "NON-CLOSURE technical calibration. Does not close, reclassify or "
            "skip any item and does not modify thresholds. Live gate (unchanged): "
            f"ssim>={gate.min_ssim}, mad<={gate.max_mean_abs_diff}, "
            f"changed_ratio<={gate.max_changed_pixel_ratio}."
        ),
        "gate_thresholds": gate.to_dict(),
        "canonical_dir": str(canonical_dir),
        "actual_dir": str(actual_dir),
        "results": results,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "CALIBRATION.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "CALIBRATION.md").write_text(_markdown(payload), encoding="utf-8")
    return payload


def _markdown(payload: dict) -> str:
    g = payload["gate_thresholds"]
    lines = [
        "# Visual Gate Calibration (NON-CLOSURE)",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "**This is technical evidence only.** It does not close, reclassify or skip "
        "any checklist item and does not change any threshold.",
        "",
        f"Live gate (unchanged): `ssim>={g['min_ssim']}`, `mad<={g['max_mean_abs_diff']}`, "
        f"`changed_ratio<={g['max_changed_pixel_ratio']}`.",
        "",
        "| key | res | class | global ssim | windowed ssim | gate | mad | changed | canon std | ceiling(align) | ceiling(color) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in payload["results"]:
        if r["status"] != "measured":
            lines.append(f"| {r['key']} | MISSING (canonical={r['canonical_present']}, actual={r['actual_present']}) | | | | | | | | | |")
            continue
        d = r["density"]
        e = r["estimated_ceiling"]
        lines.append(
            f"| {r['key']} | {r['resolution']} | {r['gate_class']} | {r['ssim']} | "
            f"{r['windowed_ssim']} | {r['effective_ssim_gate']} | {r['mean_abs_diff']} | "
            f"{r['changed_pixel_ratio']} | {d['canon_gray_std']} | "
            f"{e['by_alignment_ssim']} | {e['by_color_ssim']} |"
        )
    lines += [
        "",
        "Columns: `ceiling(align)` = best SSIM under a +/-3px global shift; "
        "`ceiling(color)` = SSIM if every flat/colour pixel were perfectly matched, "
        "leaving only strong text edges. The decisive signal is the ceiling: if a "
        "surface stays far below the `min_ssim` gate even after alignment AND colour "
        "are perfected, the global-SSIM floor is set by text-edge rasterisation "
        "(Qt vs Chromium), not by layout or colour that product code could fix. "
        "`ink_fraction` conflates text with large dark regions (e.g. a dimmed "
        "backdrop) and is informational only.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Visual gate calibration (non-closure technical evidence).")
    parser.add_argument("--keys", nargs="*", default=list(_DEFAULT_KEYS))
    parser.add_argument("--canonical", default=str(_DEFAULT_CANONICAL))
    parser.add_argument("--actual", default=str(_DEFAULT_ACTUAL))
    parser.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    args = parser.parse_args(argv)
    payload = run(args.keys, Path(args.canonical), Path(args.actual), Path(args.out_dir))
    print("=" * 60)
    print("VISUAL GATE CALIBRATION (NON-CLOSURE TECHNICAL EVIDENCE)")
    print(f"Out: {args.out_dir}")
    for r in payload["results"]:
        if r["status"] != "measured":
            print(f"  {r['key']}: MISSING (canonical={r['canonical_present']}, actual={r['actual_present']})")
            continue
        e = r["estimated_ceiling"]
        print(
            f"  {r['key']} [{r['resolution']}] {r['gate_class']}: global_ssim={r['ssim']} "
            f"windowed_ssim={r['windowed_ssim']} ssim_gate={r['effective_ssim_gate']} "
            f"changed={r['changed_pixel_ratio']} changed_gate={r['effective_changed_gate']} "
            f"canon_std={r['density']['canon_gray_std']}"
        )
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
