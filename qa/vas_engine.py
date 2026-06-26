#!/usr/bin/env python3
"""VAS Engine — shared detection logic for Visual Auditor Spec.

No pixel-to-pixel comparison. No OCR. Uses color clustering, shape analysis,
and contrast detection on single images (mockup or capture).

Usage:
    from vas_engine import detect_components, detect_text_regions, count_cards
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from PIL import Image, ImageFilter


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


def _find_dominant_colors(arr: np.ndarray, n: int = 4, quantize: int = 8) -> list[tuple[str, int]]:
    """Find dominant colors via histogram on quantized RGB (fast np.unique)."""
    quantized = (arr // quantize) * quantize
    h, w = quantized.shape[:2]
    step = max(1, int(math.sqrt((w * h) / 2000)))
    sample = quantized[::step, ::step].reshape(-1, 3)

    # Fast unique counting via numpy
    # View as structured array for unique on axis
    dtype = np.dtype((np.void, sample.dtype.itemsize * 3))
    view = sample.view(dtype)
    unique, counts = np.unique(view, return_counts=True)
    unique = unique.view(sample.dtype).reshape(-1, 3)
    order = np.argsort(counts)[::-1]
    return [(rgb_to_hex(int(r), int(g), int(b)), int(c)) for (r, g, b), c in zip(unique[order], counts[order])][:n]


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def detect_components(arr: np.ndarray, w: int, h: int) -> list[dict[str, Any]]:
    """Detect UI components (cards, panels) via color clustering + shape analysis.

    Returns list of component regions with:
        - x, y, w, h (in pixels)
        - color (hex of interior)
        - area
        - rect_score (0-1, how rectangular the component is)
    """
    # Step 1: find dominant colors (limit to 4 for speed/quality balance)
    dominant = _find_dominant_colors(arr, n=4, quantize=8)
    if not dominant:
        return []

    bg_hex = dominant[0][0]
    bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))

    # Step 2: for each non-background color, find connected components
    regions = []
    for color_hex, _count in dominant[1:]:
        rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
        # Create mask: pixels close to this color (within 24 RGB units)
        diff = np.linalg.norm(arr.astype(np.float32) - np.array(rgb), axis=2)
        mask = (diff < 28).astype(np.uint8) * 255

        # Clean up: small dilate to close gaps, then erode (fast PIL C impl)
        mask_img = Image.fromarray(mask.astype(np.uint8))
        mask_img = mask_img.filter(ImageFilter.MaxFilter(3))
        mask = np.array(mask_img)

        # Connected component labeling (scipy, fast C impl)
        labeled, num_labels = _label_4c(mask)
        if num_labels == 0:
            continue

        # For each component, compute bounding box and rectangularity
        for i in range(1, num_labels + 1):
            ys, xs = np.where(labeled == i)
            if len(ys) < 20:  # Too small
                continue

            x0, y0 = int(xs.min()), int(ys.min())
            x1, y1 = int(xs.max()), int(ys.max())
            rw = x1 - x0 + 1
            rh = y1 - y0 + 1
            bbox_area = rw * rh
            comp_area = len(ys)

            if bbox_area < 900:  # < 30x30 px
                continue

            aspect = rw / max(rh, 1)
            if aspect < 0.25 or aspect > 4.0:
                continue

            rect_score = comp_area / bbox_area
            if rect_score < 0.45:  # Too irregular
                continue

            # Interior color (avoid 2px border for anti-aliasing)
            crop = arr[y0:y1+1, x0:x1+1]
            interior = crop[2:-2, 2:-2] if crop.shape[0] > 4 and crop.shape[1] > 4 else crop
            avg = np.mean(interior.reshape(-1, 3), axis=0).astype(int)
            interior_hex = rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2]))

            # Skip if interior is too close to background
            if _color_distance(tuple(int(interior_hex[i:i+2], 16) for i in (1, 3, 5)), bg_rgb) < 20:
                continue

            regions.append({
                "x": x0, "y": y0, "w": rw, "h": rh,
                "color": interior_hex,
                "area": int(comp_area),
                "rect_score": round(rect_score, 3),
                "source_color": color_hex,
            })

    # Merge overlapping regions (keep largest when overlap > 50%)
    regions = _merge_overlapping(regions, overlap_threshold=0.5)
    return sorted(regions, key=lambda r: (r["y"], r["x"]))


def _label_4c(arr: np.ndarray) -> tuple[np.ndarray, int]:
    """4-connectivity connected component labeling (fast via scipy)."""
    from scipy.ndimage import label
    labeled, num = label(arr > 0)
    return labeled.astype(np.int32), int(num)


def _merge_overlapping(regions: list[dict], overlap_threshold: float = 0.5) -> list[dict]:
    """Merge regions that overlap more than threshold. Keep the larger one."""
    if not regions:
        return []

    merged = []
    used = set()

    for i, r1 in enumerate(regions):
        if i in used:
            continue
        # Find all overlapping regions
        group = [r1]
        used.add(i)
        for j, r2 in enumerate(regions[i+1:], start=i+1):
            if j in used:
                continue
            if _iou(r1, r2) > overlap_threshold:
                group.append(r2)
                used.add(j)

        # Keep the largest region in the group
        largest = max(group, key=lambda r: r["w"] * r["h"])
        merged.append(largest)

    return merged


def _iou(r1: dict, r2: dict) -> float:
    """Intersection over Union of two rectangles."""
    x1 = max(r1["x"], r2["x"])
    y1 = max(r1["y"], r2["y"])
    x2 = min(r1["x"] + r1["w"], r2["x"] + r2["w"])
    y2 = min(r1["y"] + r1["h"], r2["y"] + r2["h"])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    union = r1["w"] * r1["h"] + r2["w"] * r2["h"] - inter
    return inter / union


def count_cards(arr: np.ndarray) -> int:
    """Count cards in an image using color clustering."""
    h, w = arr.shape[:2]
    regions = detect_components(arr, w, h)
    cards = []
    for r in regions:
        area_ratio = (r["w"] * r["h"]) / (w * h)
        if area_ratio > 0.7:
            continue
        aspect = r["w"] / max(r["h"], 1)
        if 0.5 <= aspect <= 2.5:
            cards.append(r)
    return len(cards)



def detect_text_regions(arr: np.ndarray, w: int, h: int) -> list[dict[str, Any]]:
    """Detect text regions by edge detection (PIL FIND_EDGES, fast C impl).

    Text is typically dark on light background or light on dark background.
    Returns list of text region hints with approximate color and position.
    """
    # Fast edge detection via PIL
    gray = np.mean(arr, axis=2).astype(np.uint8)
    pil_gray = Image.fromarray(gray)
    edges = np.array(pil_gray.filter(ImageFilter.FIND_EDGES))

    # Threshold: text has many fine edges
    text_mask = (edges > 20).astype(np.uint8) * 255

    # Label connected components
    labeled, num = _label_4c(text_mask)
    if num == 0:
        return []

    # Fast vectorized bbox extraction via scipy.find_objects + bincount
    from scipy.ndimage import find_objects
    slices = find_objects(labeled)
    counts = np.bincount(labeled.ravel())

    max_area = w * h * 0.3
    regions = []
    for i in range(1, num + 1):
        area = int(counts[i])
        if area < 30 or area > max_area:
            continue
        sl = slices[i - 1]
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        rw = x1 - x0
        rh = y1 - y0
        if rh < 6 or rw < 15:
            continue
        if rh > 80:
            continue

        # Determine text color (dominant dark color in region)
        crop = arr[y0:y1, x0:x1]
        gray_crop = np.mean(crop, axis=2)
        dark_mask = gray_crop < np.mean(gray_crop)
        dark_pixels = crop[dark_mask]
        if len(dark_pixels) > 0:
            avg = np.mean(dark_pixels, axis=0).astype(int)
            text_color = rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2]))
        else:
            text_color = "#000000"

        regions.append({
            "x": x0, "y": y0, "w": rw, "h": rh,
            "text_color": text_color,
            "type": "text_block",
        })

    return regions


def region_text_presence(arr: np.ndarray, x: int, y: int, rw: int, rh: int) -> float:
    """Edge-density proxy for "this region contains rendered glyphs".

    Robust across renderers: measures the fraction of strong edges in the
    region, NOT an exact glyph/block count. Text produces many fine edges, so a
    region that should hold text but renders blank collapses toward 0. Across 75
    text_required regions the captured value never dropped below 0.055, so a
    small threshold (~0.02) separates "text present" from "blank" with no false
    positives — while exact text-block counts diverge >30% on 36% of surfaces
    and are not usable.
    """
    if rw <= 0 or rh <= 0:
        return 0.0
    crop = arr[y : y + rh, x : x + rw]
    if crop.size == 0:
        return 0.0
    gray = np.mean(crop, axis=2).astype(np.uint8)
    edges = np.array(Image.fromarray(gray).filter(ImageFilter.FIND_EDGES))
    # PIL leaves the 1px frame of a Kernel filter at raw values (not 0), which
    # would count as edges and put a content-independent floor under the result.
    # Strip that frame so a genuinely flat (blank) region reads ~0.
    if edges.shape[0] > 2 and edges.shape[1] > 2:
        edges = edges[1:-1, 1:-1]
    return float(np.mean(edges > 20))


def region_card_structure(arr: np.ndarray, x: int, y: int, rw: int, rh: int) -> tuple[int, float]:
    """Describe card structure in a region as (band_count, edge_signal).

    band_count = number of distinct horizontal content bands (runs of rows with
    edge activity, separated by gaps). edge_signal = mean per-row edge fraction.

    This is a presence/structure proxy, not an exact card count. Exact counts
    (color-clustering or fill-holes) diverge >30% on ~35% of surfaces and the
    fill-holes variant collapses dense UIs into one blob. By contrast, across 30
    card_group regions every capture yielded >=1 band and edge_signal >=0.046,
    so requiring (band>=1 and signal>~0.02) detects a card group that failed to
    render with no false positives.
    """
    if rw <= 0 or rh <= 0:
        return 0, 0.0
    crop = arr[y : y + rh, x : x + rw]
    if crop.size == 0:
        return 0, 0.0
    gray = np.mean(crop, axis=2).astype(np.uint8)
    edges = np.array(Image.fromarray(gray).filter(ImageFilter.FIND_EDGES))
    # Strip the PIL Kernel-filter border frame (raw values, not 0) so a flat
    # region reads ~0 instead of a perimeter-driven floor.
    if edges.shape[0] > 2 and edges.shape[1] > 2:
        edges = edges[1:-1, 1:-1]
    rowsig = np.mean(edges > 15, axis=1)
    active = rowsig > 0.05
    bands = 0
    prev = False
    for a in active:
        if a and not prev:
            bands += 1
        prev = bool(a)
    return bands, float(np.mean(rowsig))


def detect_shadows(arr: np.ndarray, w: int, h: int, regions: list[dict]) -> list[dict[str, Any]]:
    """Detect if components have shadow effects by analyzing brightness gradient
    around their edges.
    """
    gray = np.mean(arr, axis=2).astype(np.float32)
    shadow_evidence = []
    for r in regions:
        # Check 5px outside the region on all sides
        x0 = max(0, r["x"] - 5)
        y0 = max(0, r["y"] - 5)
        x1 = min(w, r["x"] + r["w"] + 5)
        y1 = min(h, r["y"] + r["h"] + 5)

        outer = gray[y0:y1, x0:x1]
        inner = gray[r["y"]:r["y"]+r["h"], r["x"]:r["x"]+r["w"]]

        if outer.size == 0 or inner.size == 0:
            continue

        outer_mean = np.mean(outer)
        inner_mean = np.mean(inner)
        # Shadow = region is darker around the component
        if outer_mean < inner_mean - 8:
            shadow_evidence.append({
                "component_id": r.get("id", "unknown"),
                "has_shadow": True,
                "brightness_drop": round(inner_mean - outer_mean, 1),
            })
        else:
            shadow_evidence.append({
                "component_id": r.get("id", "unknown"),
                "has_shadow": False,
                "brightness_drop": round(inner_mean - outer_mean, 1),
            })
    return shadow_evidence


def detect_icons(arr: np.ndarray, w: int, h: int, regions: list[dict]) -> list[dict[str, Any]]:
    """Detect icons inside components. Icons are small, colorful regions with
    high contrast against the component interior.
    """
    icons = []
    for r in regions:
        # Crop the component interior
        cx0 = r["x"] + 2
        cy0 = r["y"] + 2
        cx1 = r["x"] + r["w"] - 2
        cy1 = r["y"] + r["h"] - 2
        if cx1 - cx0 < 10 or cy1 - cy0 < 10:
            continue

        crop = arr[cy0:cy1, cx0:cx1]
        crop_gray = np.mean(crop, axis=2)
        comp_mean = np.mean(crop_gray)

        # Find small blobs of significantly different color
        diff = np.abs(crop_gray - comp_mean)
        icon_mask = (diff > 25).astype(np.uint8) * 255
        labeled, num = _label_4c(icon_mask)

        for i in range(1, num + 1):
            ys, xs = np.where(labeled == i)
            if len(ys) < 20 or len(ys) > 500:
                continue
            x0, y0 = int(xs.min()), int(ys.min())
            x1, y1 = int(xs.max()), int(ys.max())
            iw, ih = x1 - x0 + 1, y1 - y0 + 1
            if iw < 8 or ih < 8 or iw > 48 or ih > 48:
                continue
            aspect = iw / max(ih, 1)
            if aspect < 0.5 or aspect > 2.0:
                continue

            avg = np.mean(crop[y0:y1+1, x0:x1+1], axis=(0, 1)).astype(int)
            icon_color = rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2]))

            icons.append({
                "parent_component": r.get("id", "unknown"),
                "x": cx0 + x0, "y": cy0 + y0,
                "w": iw, "h": ih,
                "color": icon_color,
                "type": "icon",
            })

    return icons
