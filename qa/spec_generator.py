#!/usr/bin/env python3
"""Spec Generator — auto-generate visual specs from mockup reference images.

Usage:
    .venv\\Scripts\\python.exe qa\\spec_generator.py \
        --mockup-dir qa\\mockup_reference_normalized \
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


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def sample_bg_color(arr: np.ndarray, w: int, h: int) -> str:
    """Sample corners + center to infer background color."""
    samples = [
        arr[5, 5],
        arr[5, w - 5],
        arr[h - 5, 5],
        arr[h - 5, w - 5],
        arr[h // 2, w // 2],
    ]
    avg = np.mean(samples, axis=0).astype(int)
    return rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2]))


def detect_components_grid(arr: np.ndarray, w: int, h: int, bg_color: str) -> list[dict[str, Any]]:
    """Fast component detection using a coarse grid (cell-based)."""
    bg_rgb = np.array([int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)])
    # Grid size: 24x24 cells for 960x600 -> 40x25 cells
    cols = 40
    rows = 25
    cell_w = w // cols
    cell_h = h // rows
    if cell_w < 4 or cell_h < 4:
        cols = max(4, w // 20)
        rows = max(4, h // 20)
        cell_w = w // cols
        cell_h = h // rows

    # Compute mean color per cell
    cell_colors = np.zeros((rows, cols, 3), dtype=np.float32)
    cell_active = np.zeros((rows, cols), dtype=bool)
    for r in range(rows):
        y0 = r * cell_h
        y1 = (r + 1) * cell_h if r < rows - 1 else h
        for c in range(cols):
            x0 = c * cell_w
            x1 = (c + 1) * cell_w if c < cols - 1 else w
            crop = arr[y0:y1, x0:x1]
            mean = np.mean(crop.reshape(-1, 3), axis=0)
            cell_colors[r, c] = mean
            diff = np.mean(np.abs(mean - bg_rgb))
            cell_active[r, c] = diff > 18

    # Find connected active cells
    labels = np.zeros((rows, cols), dtype=np.int32)
    label = 0
    for r in range(rows):
        for c in range(cols):
            if cell_active[r, c] and labels[r, c] == 0:
                label += 1
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
                        continue
                    if labels[cr, cc] != 0 or not cell_active[cr, cc]:
                        continue
                    labels[cr, cc] = label
                    stack.extend([(cr-1, cc), (cr+1, cc), (cr, cc-1), (cr, cc+1)])

    # Convert labels to pixel regions
    regions = []
    min_cells = 4  # At least 4 cells (~2% of image)
    for i in range(1, label + 1):
        cells = np.argwhere(labels == i)
        if len(cells) < min_cells:
            continue
        r_min, c_min = cells.min(axis=0)
        r_max, c_max = cells.max(axis=0)
        x0 = c_min * cell_w
        y0 = r_min * cell_h
        x1 = min((c_max + 1) * cell_w, w)
        y1 = min((r_max + 1) * cell_h, h)
        rw = x1 - x0
        rh = y1 - y0
        aspect = rw / max(rh, 1)
        if aspect < 0.25 or aspect > 4.0:
            continue
        if rw < 30 or rh < 30:
            continue
        # Interior color
        crop = arr[y0:y1, x0:x1]
        interior = crop[2:-2, 2:-2] if crop.shape[0] > 4 and crop.shape[1] > 4 else crop
        avg = np.mean(interior.reshape(-1, 3), axis=0).astype(int)
        regions.append({
            "x": int(x0), "y": int(y0), "w": int(rw), "h": int(rh),
            "color": rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2])),
            "cells": int(len(cells)),
        })
    return regions


def infer_layout(cards: list[dict[str, Any]], w: int, h: int) -> dict[str, Any]:
    if not cards:
        return {"type": "free"}
    cards_sorted = sorted(cards, key=lambda c: (c["y"], c["x"]))
    y_positions = sorted(set(c["y"] for c in cards_sorted))
    x_positions = sorted(set(c["x"] for c in cards_sorted))
    rows = len(y_positions)
    cols = len(x_positions)
    margin_top = y_positions[0] if y_positions else 0
    margin_bottom = h - (y_positions[-1] + cards_sorted[-1]["h"]) if y_positions else 0
    margin_left = x_positions[0] if x_positions else 0
    gap_x = 0
    if len(x_positions) > 1:
        gaps = [x_positions[i+1] - (x_positions[i] + cards_sorted[i]["w"]) for i in range(len(x_positions)-1)]
        gap_x = int(np.median(gaps)) if gaps else 0
    return {
        "type": "grid" if rows > 1 or cols > 1 else "free",
        "columns": max(cols, 1),
        "rows": max(rows, 1),
        "margin_top_px": margin_top,
        "margin_bottom_px": margin_bottom,
        "margin_sides_px": margin_left,
        "gap_px": gap_x,
    }


def resolve_mockup_path(mockup_dir: Path, view: str, theme: str) -> Path | None:
    candidates = [
        mockup_dir / theme / f"{view}.png",
        mockup_dir / theme / f"{view.rsplit('-', 1)[0]}.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def generate_spec_for_mockup(mockup_path: Path, surface_key: str) -> dict[str, Any]:
    img = Image.open(mockup_path).convert("RGB")
    arr = np.array(img)
    w, h = img.size

    bg_color = sample_bg_color(arr, w, h)
    cards = detect_components_grid(arr, w, h, bg_color)
    layout = infer_layout(cards, w, h)

    components = []
    components.append({
        "id": "header_band",
        "type": "header",
        "region": {"x_pct": 0, "y_pct": 0, "w_pct": 100, "h_pct": 18},
        "color_hint": bg_color,
    })
    components.append({
        "id": "score_widget",
        "type": "card",
        "region": {"x_pct": 0, "y_pct": 10, "w_pct": 100, "h_pct": 15},
        "color_hint": bg_color,
    })
    if cards:
        min_x = min(c["x"] for c in cards)
        min_y = min(c["y"] for c in cards)
        max_x = max(c["x"] + c["w"] for c in cards)
        max_y = max(c["y"] + c["h"] for c in cards)
        colors = [c["color"] for c in cards]
        # Most common interior color (filter out background-like)
        from collections import Counter
        filtered = [c for c in colors if c != bg_color]
        card_color = max(set(filtered), key=filtered.count) if filtered else colors[0]
        components.append({
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

    return {
        "canvas": {
            "background_color": bg_color,
            "width": w,
            "height": h,
        },
        "layout": layout,
        "components": components,
        "_meta": {
            "generated_from": str(mockup_path),
            "surface_key": surface_key,
            "card_count": len(cards),
        },
    }


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
        mockup_path = resolve_mockup_path(mockup_dir, view, theme)
        if not mockup_path:
            print(f"SKIP {surface_key}: mockup not found")
            continue
        print(f"Generating spec for {surface_key} ...")
        spec = generate_spec_for_mockup(mockup_path, surface_key)
        surfaces[surface_key] = spec

    out = {
        "schema_version": "1.0.0",
        "description": "Auto-generated visual specs from mockup reference. Human review recommended.",
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
