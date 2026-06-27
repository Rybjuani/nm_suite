#!/usr/bin/env python3
"""Spec Generator — auto-generate visual specs from mockup reference images.

Uses vas_engine for robust component detection (color clustering + shape
analysis) instead of grid-based thresholding.

Usage:
    .venv\\Scripts\\python.exe qa\\spec_generator.py \\
        --mockup-dir qa\\_mockup_canonical \\
        --manifest qa\\_captures_v8\\CAPTURE_MANIFEST.json \
        --out qa\\specs\\specs.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

import vas_engine


def resolve_mockup_path(mockup_dir: Path, view: str, theme: str, app: str = "") -> Path | None:
    # Canonical source is flat: {app}-{view}-{theme}-{WxH}.png
    # (single owner-approved source; no nested {theme}/{view}.png layout).
    patterns = []
    if app:
        patterns.append(f"{app}-{view}-{theme}-*.png")
    patterns.append(f"*-{view}-{theme}-*.png")
    for pat in patterns:
        matches = sorted(mockup_dir.glob(pat))
        if matches:
            return matches[0]
    return None


def generate_spec_for_mockup(mockup_path: Path, surface_key: str) -> dict[str, Any]:
    img = Image.open(mockup_path).convert("RGB")
    arr = np.array(img)
    w, h = img.size

    bg_color = vas_engine.sample_bg_color(arr, w, h)
    bg_rgb = tuple(int(bg_color[i:i + 2], 16) for i in (1, 3, 5))
    content_top_pct = round(vas_engine.content_top_margin(arr, bg_rgb) * 100, 2)

    # VAS canvas check samples only the 4 corners (offset 5px). Use the same
    # corner-only average for background_color so spec and VAS measure the same
    # thing. Omit the check entirely when:
    #   - corners are non-uniform (std_dev > 15): mixed content / gradients
    #   - canonical is not full-screen (< 900×550): modal/dialog, different size
    corner_px = np.array([
        arr[5, 5], arr[5, w - 5], arr[h - 5, 5], arr[h - 5, w - 5],
    ], dtype=float)
    _canon_corner_std = float(np.std(corner_px))
    _corner_avg = np.mean(corner_px, axis=0).astype(int)
    _bg_color_corners = "#{:02x}{:02x}{:02x}".format(
        int(_corner_avg[0]), int(_corner_avg[1]), int(_corner_avg[2])
    )
    # Also skip canvas check when center content color differs strongly from
    # corners (e.g. modal overlay: dark corners, lighter dialog center).
    _center_px = arr[h // 2, w // 2].astype(float)
    _corner_vs_center = float(np.mean(np.abs(_corner_avg - _center_px)))
    _bg_color_stable = _canon_corner_std <= 15 and w >= 900 and h >= 550 and _corner_vs_center < 30
    components = vas_engine.detect_components(arr, w, h)

    # Filter to card-like components (exclude very large panels)
    cards = [c for c in components if (c["w"] * c["h"]) / (w * h) < 0.6 and 0.5 <= c["w"] / max(c["h"], 1) <= 2.5]

    # Layout inference from card positions
    layout = {"type": "free"}
    if cards:
        y_positions = sorted(set(c["y"] for c in cards))
        x_positions = sorted(set(c["x"] for c in cards))
        rows = len(y_positions)
        cols = len(x_positions)
        if rows > 1 or cols > 1:
            layout = {
                "type": "grid",
                "columns": cols,
                "rows": rows,
                "margin_top_px": y_positions[0] if y_positions else 0,
                "margin_bottom_px": h - (y_positions[-1] + cards[-1]["h"]) if y_positions else 0,
                "margin_sides_px": x_positions[0] if x_positions else 0,
                "gap_px": _compute_gap(cards, x_positions, y_positions),
            }

    spec_components = []

    # Card group (all cards detected)
    # Exclude only degenerate single-pixel artifacts (< 0.1% of canvas = ~576px²).
    # Even a 24×24 checkbox represents a real visual element and should be included.
    _MIN_CARD_GROUP_PCT = 0.1
    if cards:
        min_x = min(c["x"] for c in cards)
        min_y = min(c["y"] for c in cards)
        max_x = max(c["x"] + c["w"] for c in cards)
        max_y = max(c["y"] + c["h"] for c in cards)
        bbox_pct = (max_x - min_x) * (max_y - min_y) / (w * h) * 100
        if bbox_pct >= _MIN_CARD_GROUP_PCT:
            # color_hint = regional average of the canonical bbox (same metric VAS will measure)
            card_color = _region_avg_hex(arr, min_x, min_y, max_x, max_y)
            spec_components.append({
                "id": "card_group",
                "type": "card_group",
                "count": len(cards),
                "region": {
                    "x_pct": round(min_x / w * 100, 1),
                    "y_pct": round(min_y / h * 100, 1),
                    "w_pct": round((max_x - min_x) / w * 100, 1),
                    "h_pct": round((max_y - min_y) / h * 100, 1),
                },
                "color_hint": card_color,
            })

    # Detect text regions
    text_regions = vas_engine.detect_text_regions(arr, w, h)
    if text_regions:
        # Group by approximate y-position (header vs content)
        header_text = [t for t in text_regions if t["y"] < h * 0.15]
        body_text = [t for t in text_regions if t["y"] >= h * 0.15]
        if header_text:
            avg_color = _dominant_text_color(header_text, arr)
            spec_components.append({
                "id": "header_text",
                "type": "text",
                "region": _merge_regions_pct(header_text, w, h),
                "text_color_hint": avg_color,
                "text_required": False,
            })
        if body_text:
            avg_color = _dominant_text_color(body_text, arr)
            spec_components.append({
                "id": "body_text",
                "type": "text",
                "region": _merge_regions_pct(body_text, w, h),
                "text_color_hint": avg_color,
                "text_required": False,
            })

    # Detect shadows — only mark shadow=True in spec when canonical clearly shows
    # elevation (light mode: shadow visible against light bg; dark mode: shadow too
    # subtle to be reliable, so disabled to avoid systematic SHADOW_MISMATCH FPs).
    is_dark_image = _is_dark_image(bg_color)
    if is_dark_image:
        has_shadow = False
    else:
        shadow_evidence = vas_engine.detect_shadows(arr, w, h, cards)
        has_shadow = any(s["has_shadow"] for s in shadow_evidence)

    # Detect icons — color_hint = regional bbox average (same metric VAS measures)
    # Exclude degenerate strips (width or height < 15px): thin horizontal/vertical
    # artifacts from text baselines or chart axes that aren't real icon areas.
    icons = vas_engine.detect_icons(arr, w, h, cards)
    if icons:
        icon_region = _merge_regions_pct(icons, w, h)
        ix = int(icon_region["x_pct"] / 100 * w)
        iy = int(icon_region["y_pct"] / 100 * h)
        iw = int(icon_region["w_pct"] / 100 * w)
        ih = int(icon_region["h_pct"] / 100 * h)
        if iw >= 10 and ih >= 10:
            icon_color = _region_avg_hex(arr, ix, iy, ix + iw, iy + ih)
            spec_components.append({
                "id": "icons",
                "type": "icon_group",
                "count": len(icons),
                "region": icon_region,
                "color_hint": icon_color,
            })

    return {
        "canvas": {
            "background_color": _bg_color_corners if _bg_color_stable else None,
            "width": w,
            "height": h,
            "content_top_pct": content_top_pct,
        },
        "layout": layout,
        "components": spec_components,
        "effects": {
            "shadow": has_shadow,
        },
        "_meta": {
            "generated_from": str(mockup_path),
            "surface_key": surface_key,
            "card_count": len(cards),
            "text_block_count": len(text_regions),
            "icon_count": len(icons),
        },
    }


def _region_avg_hex(arr: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> str:
    """Average pixel color of arr[y0:y1, x0:x1] as a hex string."""
    h_a, w_a = arr.shape[:2]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w_a, x1), min(h_a, y1)
    if x1 <= x0 or y1 <= y0:
        return "#808080"
    crop = arr[y0:y1, x0:x1]
    avg = np.mean(crop.reshape(-1, 3), axis=0)
    return "#{:02x}{:02x}{:02x}".format(int(avg[0]), int(avg[1]), int(avg[2]))


def _is_dark_image(bg_hex: str) -> bool:
    """Return True if background hex color is a dark color (luminance < 0.25)."""
    try:
        r = int(bg_hex[1:3], 16) / 255
        g = int(bg_hex[3:5], 16) / 255
        b = int(bg_hex[5:7], 16) / 255
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return lum < 0.25
    except Exception:
        return False


def _compute_gap(cards: list[dict], x_positions: list[int], y_positions: list[int]) -> int:
    if len(x_positions) > 1:
        gaps = []
        for i in range(len(x_positions) - 1):
            card_w = next(c["w"] for c in cards if c["x"] == x_positions[i])
            gaps.append(x_positions[i + 1] - (x_positions[i] + card_w))
        if gaps:
            return int(sorted(gaps)[len(gaps) // 2])
    return 0


def _merge_regions_pct(regions: list[dict], w: int, h: int) -> dict[str, float]:
    if not regions:
        return {"x_pct": 0, "y_pct": 0, "w_pct": 0, "h_pct": 0}
    min_x = min(r["x"] for r in regions)
    min_y = min(r["y"] for r in regions)
    max_x = max(r["x"] + r.get("w", 10) for r in regions)
    max_y = max(r["y"] + r.get("h", 10) for r in regions)
    return {
        "x_pct": round(min_x / w * 100, 1),
        "y_pct": round(min_y / h * 100, 1),
        "w_pct": round((max_x - min_x) / w * 100, 1),
        "h_pct": round((max_y - min_y) / h * 100, 1),
    }


def _dominant_text_color(text_regions: list[dict], arr: np.ndarray) -> str:
    colors = []
    for t in text_regions[:5]:
        x, y, w, h = t["x"], t["y"], t.get("w", 10), t.get("h", 10)
        crop = arr[y:y+h, x:x+w]
        if crop.size == 0:
            continue
        gray = np.mean(crop, axis=2)
        dark = crop[gray < np.mean(gray)]
        if len(dark) > 0:
            avg = np.mean(dark, axis=0).astype(int)
            colors.append(vas_engine.rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2])))
    from collections import Counter
    if colors:
        return Counter(colors).most_common(1)[0][0]
    return "#333333"


def _dominant_icon_color(icons: list[dict]) -> str:
    from collections import Counter
    colors = [i["color"] for i in icons]
    if colors:
        return Counter(colors).most_common(1)[0][0]
    return "#666666"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mockup-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    mockup_dir = Path(args.mockup_dir)
    manifest_path = Path(args.manifest)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    surfaces: dict[str, Any] = {}
    for entry in manifest.get("results", manifest):
        app = entry.get("app", "")
        view = entry.get("view", "")
        theme = entry.get("theme", "")
        surface_key = f"{app}:{view}@{theme}"
        mockup_path = resolve_mockup_path(mockup_dir, view, theme, app)
        if not mockup_path:
            print(f"SKIP {surface_key}: mockup not found")
            continue
        print(f"Generating spec for {surface_key} ...")
        spec = generate_spec_for_mockup(mockup_path, surface_key)
        surfaces[surface_key] = spec

    out = {
        "schema_version": "1.1.0",
        "description": "Auto-generated visual specs from mockup reference (vas_engine). Human review recommended.",
        "verification_engine": {
            "color_tolerance": 12,
            "position_tolerance_pct": 5,
            "size_tolerance_pct": 10,
        },
        "surfaces": surfaces,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSpecs written to {out_path} ({len(surfaces)} surfaces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
