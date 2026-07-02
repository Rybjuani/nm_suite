#!/usr/bin/env python3
"""Audit modal backdrop, centering, and back-screen dependency.

This audit is a visual anti-fraud companion for modal surfaces. It does not
replace capture_v8.py, layered_visual_compare.py, qa/anti_fraud_scan.py, or VAS.
It only checks whether available modal captures preserve the canonical HTML
modal/backdrop contract instead of hiding a back-screen divergence behind an
invented blur, dim, opacity, or crop.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL_DIR = ROOT / "qa" / "_mockup_canonical"
DEFAULT_ACTUAL_DIR = ROOT / "qa" / "_captures_v8"
DEFAULT_OUT_ROOT = ROOT / "reports" / "qa" / "modal_backdrop_blur"

CAPTURE_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+)x(\d+)\.png$")
SCRIM_RGB = np.asarray([20.0, 18.0, 14.0], dtype=np.float32)
SCRIM_ALPHA = 0.5

MODAL_SURFACES = {"modal", "window_modal"}
BACK_SCREEN_VIEWS = {
    "hub:detalle-resumen-ia-0": "hub:detalle",
}

CODE_CANONICAL_MODAL_MISSING = "CANONICAL_MODAL_MISSING"
CODE_RUNTIME_MODAL_MISSING = "RUNTIME_MODAL_MISSING"
CODE_BACKDROP_CAPTURE_MISSING = "BACKDROP_CAPTURE_MISSING"
CODE_BACKDROP_BLUR_FAIL = "BACKDROP_BLUR_FAIL"
CODE_MODAL_CENTER_FAIL = "MODAL_CENTER_FAIL"
CODE_MODAL_BBOX_FAIL = "MODAL_BBOX_FAIL"
CODE_PARENT_SCREEN_DEPENDENCY = "PARENT_SCREEN_DEPENDENCY"


@dataclass(frozen=True)
class CaptureId:
    file: str
    app: str
    view: str
    theme: str
    width: int
    height: int
    surface: str = ""
    is_modal: bool = False
    modal_capture_scope: str | None = None
    backdrop_observable: bool = False
    back_screen_key: str | None = None

    @property
    def key(self) -> str:
        return f"{self.app}:{self.view}@{self.theme}"

    @property
    def view_key(self) -> str:
        return f"{self.app}:{self.view}"

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass
class ModalAuditRow:
    key: str
    verdict: str
    codes: list[str] = field(default_factory=list)
    canonical_file: str = ""
    actual_file: str = ""
    back_screen_key: str = ""
    canonical_surface: str = ""
    actual_surface: str = ""
    canonical_resolution: str = ""
    actual_resolution: str = ""
    centered: str = "not_evaluated"
    bbox_size: str = "not_evaluated"
    backdrop_region: str = "not_evaluated"
    blur_dim_equivalence: str = "not_evaluated"
    back_screen_dependency: str = "not_evaluated"
    metrics: dict[str, Any] = field(default_factory=dict)

    def fail(self, code: str) -> None:
        if code not in self.codes:
            self.codes.append(code)
        self.verdict = "FAIL"


def parse_capture_name(
    file_name: str,
    surface: str = "",
    *,
    is_modal: bool = False,
    modal_capture_scope: str | None = None,
    backdrop_observable: bool = False,
    back_screen_key: str | None = None,
) -> CaptureId | None:
    match = CAPTURE_RE.match(file_name)
    if not match:
        return None
    app, view, theme, width, height = match.groups()
    return CaptureId(
        file=file_name,
        app=app,
        view=view,
        theme=theme,
        width=int(width),
        height=int(height),
        surface=surface,
        is_modal=is_modal,
        modal_capture_scope=modal_capture_scope,
        backdrop_observable=backdrop_observable,
        back_screen_key=back_screen_key,
    )


def _capture_from_record(record: dict[str, Any], *, require_explicit_modal_metadata: bool = False) -> CaptureId | None:
    file_name = str(record.get("file") or "")
    surface = str(record.get("surface") or "")
    is_modal = bool(record.get("is_modal") or surface in MODAL_SURFACES or record.get("is_dialog_or_auxiliary"))
    modal_capture_scope = record.get("modal_capture_scope")
    if is_modal and not modal_capture_scope and not require_explicit_modal_metadata:
        modal_capture_scope = "panel_crop" if surface == "modal" or record.get("is_dialog_or_auxiliary") else "window_overlay"
    if require_explicit_modal_metadata:
        backdrop_observable = bool(record.get("backdrop_observable"))
    else:
        backdrop_observable = bool(record.get("backdrop_observable") or modal_capture_scope == "window_overlay")
    back_screen_key = record.get("back_screen_key")
    parsed = parse_capture_name(
        file_name,
        surface,
        is_modal=is_modal,
        modal_capture_scope=str(modal_capture_scope) if modal_capture_scope else None,
        backdrop_observable=backdrop_observable,
        back_screen_key=str(back_screen_key) if back_screen_key else None,
    )
    if parsed is not None:
        return parsed
    app = str(record.get("app") or "")
    view = str(record.get("view") or "")
    theme = str(record.get("theme") or "")
    resolution = str(
        record.get("actual_resolution")
        or record.get("captured_pixel_resolution")
        or record.get("resolution")
        or ""
    )
    if not app or not view or not theme or "x" not in resolution:
        return None
    try:
        width, height = (int(part) for part in resolution.split("x", 1))
    except ValueError:
        return None
    if not surface and record.get("is_dialog_or_auxiliary"):
        surface = "modal"
    is_modal = bool(record.get("is_modal") or surface in MODAL_SURFACES or record.get("is_dialog_or_auxiliary"))
    modal_capture_scope = record.get("modal_capture_scope")
    if is_modal and not modal_capture_scope and not require_explicit_modal_metadata:
        modal_capture_scope = "panel_crop" if surface == "modal" or record.get("is_dialog_or_auxiliary") else "window_overlay"
    back_screen_key = record.get("back_screen_key")
    if require_explicit_modal_metadata:
        backdrop_observable = bool(record.get("backdrop_observable"))
    else:
        backdrop_observable = bool(record.get("backdrop_observable") or modal_capture_scope == "window_overlay")
    return CaptureId(
        file_name,
        app,
        view,
        theme,
        width,
        height,
        surface,
        is_modal=is_modal,
        modal_capture_scope=str(modal_capture_scope) if modal_capture_scope else None,
        backdrop_observable=backdrop_observable,
        back_screen_key=str(back_screen_key) if back_screen_key else None,
    )


def load_captures(capture_dir: Path, *, canonical: bool) -> dict[str, CaptureId]:
    captures: dict[str, CaptureId] = {}
    manifest_name = "MANIFEST.json" if canonical else "CAPTURE_MANIFEST.json"
    manifest_path = capture_dir / manifest_name
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("captures") if canonical else manifest.get("results")
        for record in records or []:
            parsed = _capture_from_record(record, require_explicit_modal_metadata=not canonical)
            if parsed is not None:
                captures[parsed.key] = parsed

    for path in sorted(capture_dir.glob("*.png")):
        parsed = parse_capture_name(path.name)
        if parsed is None:
            continue
        existing = captures.get(parsed.key)
        if existing is None:
            captures[parsed.key] = parsed
        elif not existing.file:
            captures[parsed.key] = CaptureId(
                file=path.name,
                app=existing.app,
                view=existing.view,
                theme=existing.theme,
                width=existing.width,
                height=existing.height,
                surface=existing.surface,
                is_modal=existing.is_modal,
                modal_capture_scope=existing.modal_capture_scope,
                backdrop_observable=existing.backdrop_observable,
                back_screen_key=existing.back_screen_key,
            )
    return captures


def canonical_modal_keys(captures: dict[str, CaptureId]) -> list[str]:
    return sorted(
        key
        for key, capture in captures.items()
        if capture.is_modal or capture.surface in MODAL_SURFACES
    )


def load_image(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32)


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def mean_abs_delta(a: np.ndarray, b: np.ndarray, mask: np.ndarray | None = None) -> float:
    if a.shape != b.shape:
        return float("inf")
    delta = np.abs(a - b)
    if mask is not None:
        if not mask.any():
            return 0.0
        delta = delta[mask]
    return float(delta.mean())


def _luma(image: np.ndarray) -> np.ndarray:
    return image[..., 0] * 0.2126 + image[..., 1] * 0.7152 + image[..., 2] * 0.0722


def edge_energy(image: np.ndarray, mask: np.ndarray | None = None) -> float:
    gray = _luma(image)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    energy = np.zeros_like(gray)
    energy[:, 1:] += gx
    energy[1:, :] += gy
    if mask is not None:
        if not mask.any():
            return 0.0
        energy = energy[mask]
    return float(energy.mean())


def synthetic_backdrop(parent: np.ndarray, blur_radius: float = 3.0) -> np.ndarray:
    source = Image.fromarray(np.clip(parent, 0, 255).astype(np.uint8), "RGB")
    blurred = np.asarray(source.filter(ImageFilter.GaussianBlur(radius=blur_radius)), dtype=np.float32)
    return blurred * (1.0 - SCRIM_ALPHA) + SCRIM_RGB * SCRIM_ALPHA


def _component_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    try:
        from scipy import ndimage

        labels, count = ndimage.label(mask)
        if count <= 0:
            return None
        objects = ndimage.find_objects(labels)
        best_area = 0
        best_bbox: tuple[int, int, int, int] | None = None
        for idx, slices in enumerate(objects, start=1):
            if slices is None:
                continue
            ys, xs = slices
            area = int((labels[slices] == idx).sum())
            if area > best_area:
                best_area = area
                best_bbox = (xs.start, ys.start, xs.stop - xs.start, ys.stop - ys.start)
        return best_bbox
    except Exception:
        ys, xs = np.where(mask)
        if len(xs) == 0:
            return None
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        return (x0, y0, x1 - x0, y1 - y0)


def _refine_bbox_to_dense_core(
    diff: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    threshold: float,
    density_kernel: int = 20,
    density_threshold: float = 0.45,
    margin: int = 20,
) -> tuple[int, int, int, int] | None:
    """Refine a raw bbox to the dense core of the modal panel.

    The raw ``binary_closing(9x9)`` detector can bridge backdrop residual
    noise (Qt ``QGraphicsBlurEffect`` vs PIL ``GaussianBlur``) to the modal
    panel, inflating the detected bbox laterally. This refinement computes a
    local density map (fraction of pixels exceeding ``threshold`` in a
    ``density_kernel`` neighbourhood) inside the raw bbox and trims to the
    bounding box of the dense core (``density > density_threshold``), then
    re-inflates by a fixed ``margin`` to include the panel shadow.

    The dense core corresponds to the panel body (title, body, buttons), which
    has a high concentration of diff pixels. Backdrop noise is sparse and does
    not reach the density threshold, so it is trimmed away. This makes the
    detector robust to renderer-specific blur residual without relaxing the
    centering/size tolerances or permitting overblur.
    """
    x0, y0, bw, bh = bbox
    region = diff[y0 : y0 + bh, x0 : x0 + bw]
    binary = (region > threshold).astype(np.float32)
    try:
        from scipy import ndimage

        density = ndimage.uniform_filter(binary, size=density_kernel)
    except Exception:
        # Fallback: simple block average via cumulative sum.
        cum = np.cumsum(np.cumsum(binary, axis=0), axis=1)
        density = np.zeros_like(binary)
        k = density_kernel
        for y in range(bh):
            for x in range(bw):
                y0a = max(0, y - k // 2)
                y1a = min(bh, y + k // 2 + 1)
                x0a = max(0, x - k // 2)
                x1a = min(bw, x + k // 2 + 1)
                area = (y1a - y0a) * (x1a - x0a)
                s = cum[y1a - 1, x1a - 1]
                if y0a > 0:
                    s -= cum[y0a - 1, x1a - 1]
                if x0a > 0:
                    s -= cum[y1a - 1, x0a - 1]
                if y0a > 0 and x0a > 0:
                    s += cum[y0a - 1, x0a - 1]
                density[y, x] = s / max(area, 1)
    dense_mask = density > density_threshold
    if not dense_mask.any():
        return None
    dys, dxs = np.where(dense_mask)
    h, w = diff.shape
    rx0 = max(0, x0 + int(dxs.min()) - margin)
    ry0 = max(0, y0 + int(dys.min()) - margin)
    rx1 = min(w, x0 + int(dxs.max()) + margin + 1)
    ry1 = min(h, y0 + int(dys.max()) + margin + 1)
    return (rx0, ry0, rx1 - rx0, ry1 - ry0)


def modal_bbox_candidates(parent: np.ndarray, modal_capture: np.ndarray) -> list[tuple[int, int, int, int]]:
    if parent.shape != modal_capture.shape:
        return []
    backdrop = synthetic_backdrop(parent)
    diff = np.abs(modal_capture - backdrop).mean(axis=2)
    h, w = diff.shape
    candidates: list[tuple[int, tuple[int, int, int, int]]] = []
    for threshold in (10.0, 12.0, 15.0, 18.0, 22.0, 28.0, 35.0, 45.0, 60.0):
        mask = diff > threshold
        try:
            from scipy import ndimage

            mask = ndimage.binary_closing(mask, structure=np.ones((9, 9), dtype=bool))
            mask = ndimage.binary_fill_holes(mask)
        except Exception:
            pass
        border = max(3, min(h, w) // 100)
        mask[:border, :] = False
        mask[-border:, :] = False
        mask[:, :border] = False
        mask[:, -border:] = False

        try:
            from scipy import ndimage

            labels, count = ndimage.label(mask)
            objects = ndimage.find_objects(labels)
            for idx, slices in enumerate(objects, start=1):
                if slices is None:
                    continue
                ys, xs = slices
                area = int((labels[slices] == idx).sum())
                bbox = (xs.start, ys.start, xs.stop - xs.start, ys.stop - ys.start)
                bw, bh = bbox[2], bbox[3]
                if area < 5000 or not (0.35 * w <= bw <= 0.82 * w) or not (0.25 * h <= bh <= 0.82 * h):
                    continue
                # Refine to the dense core to avoid backdrop residual noise
                # (Qt-vs-PIL blur difference) inflating the bbox laterally.
                # See _refine_bbox_to_dense_core for the full rationale.
                refined = _refine_bbox_to_dense_core(diff, bbox, threshold=threshold)
                if refined is not None:
                    rbw, rbh = refined[2], refined[3]
                    if rbw * rbh < 1500 or not (0.30 * w <= rbw <= 0.85 * w) or not (0.20 * h <= rbh <= 0.85 * h):
                        # If the refined bbox falls outside sensible bounds,
                        # fall back to the raw bbox rather than discarding.
                        refined = bbox
                    bbox = refined
                candidates.append((area, bbox))
        except Exception:
            bbox = _component_bbox(mask)
            if bbox is not None:
                candidates.append((0, bbox))

    unique: dict[tuple[int, int, int, int], int] = {}
    for area, bbox in candidates:
        unique[bbox] = max(area, unique.get(bbox, 0))
    return [bbox for _, bbox in sorted(((-area, bbox) for bbox, area in unique.items()))]


def estimate_modal_bbox(parent: np.ndarray, modal_capture: np.ndarray) -> tuple[int, int, int, int] | None:
    candidates = modal_bbox_candidates(parent, modal_capture)
    bbox = candidates[0] if candidates else None
    if bbox is None:
        return None
    x, y, bw, bh = bbox
    if bw * bh < 1500:
        return None
    return bbox


def choose_bbox_pair(
    canonical_candidates: list[tuple[int, int, int, int]],
    actual_candidates: list[tuple[int, int, int, int]],
) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]] | tuple[None, None]:
    best: tuple[float, tuple[int, int, int, int], tuple[int, int, int, int]] | None = None
    for canonical_bbox in canonical_candidates:
        c_center = (
            canonical_bbox[0] + canonical_bbox[2] / 2.0,
            canonical_bbox[1] + canonical_bbox[3] / 2.0,
        )
        for actual_bbox in actual_candidates:
            a_center = (
                actual_bbox[0] + actual_bbox[2] / 2.0,
                actual_bbox[1] + actual_bbox[3] / 2.0,
            )
            center_delta = abs(c_center[0] - a_center[0]) + abs(c_center[1] - a_center[1])
            size_delta = abs(canonical_bbox[2] - actual_bbox[2]) + abs(canonical_bbox[3] - actual_bbox[3])
            score = center_delta + size_delta * 2.0
            if best is None or score < best[0]:
                best = (score, canonical_bbox, actual_bbox)
    if best is None:
        return None, None
    return best[1], best[2]


def inflate_bbox(
    bbox: tuple[int, int, int, int],
    margin: int,
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x, y, w, h = bbox
    x0 = max(0, x - margin)
    y0 = max(0, y - margin)
    x1 = min(width, x + w + margin)
    y1 = min(height, y + h + margin)
    return (x0, y0, x1 - x0, y1 - y0)


def outside_bboxes_mask(
    shape: tuple[int, int],
    bboxes: list[tuple[int, int, int, int]],
    margin: int = 10,
) -> np.ndarray:
    height, width = shape
    mask = np.ones((height, width), dtype=bool)
    for bbox in bboxes:
        x, y, w, h = inflate_bbox(bbox, margin, width, height)
        mask[y : y + h, x : x + w] = False
    return mask


def back_screen_key_for(capture: CaptureId) -> str:
    if capture.back_screen_key:
        return capture.back_screen_key
    if capture.view_key.startswith("suite:dbt-practice-"):
        return f"suite:dbt-library@{capture.theme}"
    back_screen_view = BACK_SCREEN_VIEWS.get(capture.view_key, "")
    return f"{back_screen_view}@{capture.theme}" if back_screen_view else ""


def _status_from_bool(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def audit_modal_key(
    key: str,
    *,
    canonical_dir: Path,
    actual_dir: Path,
    canonical_captures: dict[str, CaptureId],
    actual_captures: dict[str, CaptureId],
    center_tolerance_px: int,
    bbox_tolerance_px: int,
    backdrop_mean_tolerance: float,
    blur_ratio_tolerance: float,
    parent_mean_tolerance: float,
) -> ModalAuditRow:
    canonical = canonical_captures.get(key)
    actual = actual_captures.get(key)
    row = ModalAuditRow(
        key=key,
        verdict="PASS",
        back_screen_key=back_screen_key_for(canonical) if canonical else "",
    )

    if canonical is None:
        row.fail(CODE_CANONICAL_MODAL_MISSING)
        return row
    row.canonical_file = canonical.file
    row.canonical_surface = canonical.surface
    row.canonical_resolution = canonical.resolution

    if actual is None:
        row.fail(CODE_RUNTIME_MODAL_MISSING)
        return row
    row.actual_file = actual.file
    row.actual_surface = actual.surface
    row.actual_resolution = actual.resolution

    canonical_path = canonical_dir / canonical.file
    actual_path = actual_dir / actual.file
    if not canonical_path.exists():
        row.fail(CODE_CANONICAL_MODAL_MISSING)
        return row
    if not actual_path.exists():
        row.fail(CODE_RUNTIME_MODAL_MISSING)
        return row

    cw, ch = image_size(canonical_path)
    aw, ah = image_size(actual_path)
    row.metrics["canonical_image_size"] = f"{cw}x{ch}"
    row.metrics["actual_image_size"] = f"{aw}x{ah}"
    size_ok = abs(cw - aw) <= bbox_tolerance_px and abs(ch - ah) <= bbox_tolerance_px
    row.bbox_size = _status_from_bool(size_ok)
    if not size_ok:
        row.fail(CODE_MODAL_BBOX_FAIL)

    canonical_image = load_image(canonical_path)
    actual_image = load_image(actual_path)

    back_screen_key = back_screen_key_for(canonical)
    row.back_screen_key = back_screen_key
    canonical_parent = canonical_captures.get(back_screen_key) if back_screen_key else None
    actual_parent = actual_captures.get(back_screen_key) if back_screen_key else None

    if canonical.modal_capture_scope != "window_overlay" or not canonical.backdrop_observable:
        row.centered = "not_observable_modal_crop"
        row.backdrop_region = "not_observable_modal_crop"
        row.blur_dim_equivalence = "not_observable_modal_crop"
        row.fail(CODE_BACKDROP_CAPTURE_MISSING)
        if canonical_parent is not None and actual_parent is not None:
            parent_delta = _parent_delta(
                canonical_dir / canonical_parent.file,
                actual_dir / actual_parent.file,
            )
            row.metrics["back_screen_mean_abs_delta"] = round(parent_delta, 4)
            row.back_screen_dependency = _status_from_bool(parent_delta <= parent_mean_tolerance)
            if parent_delta > parent_mean_tolerance:
                row.fail(CODE_PARENT_SCREEN_DEPENDENCY)
        else:
            row.back_screen_dependency = "not_observable_back_screen_missing"
            row.fail(CODE_PARENT_SCREEN_DEPENDENCY)
        return row

    if actual.modal_capture_scope != "window_overlay" or not actual.backdrop_observable:
        row.centered = "not_observable_modal_crop"
        row.backdrop_region = "not_observable_modal_crop"
        row.blur_dim_equivalence = "not_observable_modal_crop"
        row.fail(CODE_BACKDROP_CAPTURE_MISSING)
        if canonical_parent is not None and actual_parent is not None:
            parent_delta = _parent_delta(
                canonical_dir / canonical_parent.file,
                actual_dir / actual_parent.file,
            )
            row.metrics["back_screen_mean_abs_delta"] = round(parent_delta, 4)
            row.back_screen_dependency = _status_from_bool(parent_delta <= parent_mean_tolerance)
            if parent_delta > parent_mean_tolerance:
                row.fail(CODE_PARENT_SCREEN_DEPENDENCY)
        else:
            row.back_screen_dependency = "not_observable_back_screen_missing"
            row.fail(CODE_PARENT_SCREEN_DEPENDENCY)
        return row

    if canonical_parent is None or actual_parent is None:
        row.back_screen_dependency = "FAIL"
        row.fail(CODE_PARENT_SCREEN_DEPENDENCY)
        return row

    canonical_parent_path = canonical_dir / canonical_parent.file
    actual_parent_path = actual_dir / actual_parent.file
    if not canonical_parent_path.exists() or not actual_parent_path.exists():
        row.back_screen_dependency = "FAIL"
        row.fail(CODE_PARENT_SCREEN_DEPENDENCY)
        return row

    canonical_parent_image = load_image(canonical_parent_path)
    actual_parent_image = load_image(actual_parent_path)
    parent_delta = mean_abs_delta(canonical_parent_image, actual_parent_image)
    row.metrics["back_screen_mean_abs_delta"] = round(parent_delta, 4)
    row.back_screen_dependency = _status_from_bool(parent_delta <= parent_mean_tolerance)
    if parent_delta > parent_mean_tolerance:
        row.fail(CODE_PARENT_SCREEN_DEPENDENCY)

    if canonical_image.shape != actual_image.shape or canonical_parent_image.shape != actual_parent_image.shape:
        row.backdrop_region = "FAIL"
        row.blur_dim_equivalence = "FAIL"
        row.fail(CODE_BACKDROP_BLUR_FAIL)
        return row

    canonical_bbox, actual_bbox = choose_bbox_pair(
        modal_bbox_candidates(canonical_parent_image, canonical_image),
        modal_bbox_candidates(actual_parent_image, actual_image),
    )
    row.metrics["canonical_modal_bbox"] = canonical_bbox
    row.metrics["actual_modal_bbox"] = actual_bbox
    if canonical_bbox is None or actual_bbox is None:
        row.centered = "FAIL"
        row.bbox_size = "FAIL"
        row.fail(CODE_MODAL_BBOX_FAIL)
        return row

    c_center = (canonical_bbox[0] + canonical_bbox[2] / 2.0, canonical_bbox[1] + canonical_bbox[3] / 2.0)
    a_center = (actual_bbox[0] + actual_bbox[2] / 2.0, actual_bbox[1] + actual_bbox[3] / 2.0)
    center_delta = (abs(c_center[0] - a_center[0]), abs(c_center[1] - a_center[1]))
    row.metrics["center_delta_px"] = [round(center_delta[0], 3), round(center_delta[1], 3)]
    center_ok = center_delta[0] <= center_tolerance_px and center_delta[1] <= center_tolerance_px
    row.centered = _status_from_bool(center_ok)
    if not center_ok:
        row.fail(CODE_MODAL_CENTER_FAIL)

    bbox_delta = (
        abs(canonical_bbox[2] - actual_bbox[2]),
        abs(canonical_bbox[3] - actual_bbox[3]),
    )
    row.metrics["bbox_size_delta_px"] = [bbox_delta[0], bbox_delta[1]]
    bbox_ok = bbox_delta[0] <= bbox_tolerance_px and bbox_delta[1] <= bbox_tolerance_px
    row.bbox_size = _status_from_bool(bbox_ok)
    if not bbox_ok:
        row.fail(CODE_MODAL_BBOX_FAIL)

    mask = outside_bboxes_mask(canonical_image.shape[:2], [canonical_bbox, actual_bbox])
    backdrop_delta = mean_abs_delta(canonical_image, actual_image, mask)
    row.metrics["backdrop_mean_abs_delta"] = round(backdrop_delta, 4)
    backdrop_ok = backdrop_delta <= backdrop_mean_tolerance
    row.backdrop_region = _status_from_bool(backdrop_ok)

    canonical_parent_edge = edge_energy(canonical_parent_image, mask)
    canonical_modal_edge = edge_energy(canonical_image, mask)
    actual_parent_edge = edge_energy(actual_parent_image, mask)
    actual_modal_edge = edge_energy(actual_image, mask)
    canonical_blur_ratio = canonical_modal_edge / max(canonical_parent_edge, 1e-6)
    actual_blur_ratio = actual_modal_edge / max(actual_parent_edge, 1e-6)
    blur_ratio_delta = abs(canonical_blur_ratio - actual_blur_ratio)
    row.metrics["canonical_blur_ratio"] = round(canonical_blur_ratio, 6)
    row.metrics["actual_blur_ratio"] = round(actual_blur_ratio, 6)
    row.metrics["blur_ratio_delta"] = round(blur_ratio_delta, 6)
    blur_ok = blur_ratio_delta <= blur_ratio_tolerance
    row.blur_dim_equivalence = _status_from_bool(backdrop_ok and blur_ok)
    if not backdrop_ok or not blur_ok:
        row.fail(CODE_BACKDROP_BLUR_FAIL)

    return row


def _parent_delta(canonical_path: Path, actual_path: Path) -> float:
    if not canonical_path.exists() or not actual_path.exists():
        return float("inf")
    canonical = load_image(canonical_path)
    actual = load_image(actual_path)
    return mean_abs_delta(canonical, actual)


def write_reports(rows: list[ModalAuditRow], out_dir: Path, payload: dict[str, Any]) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "AUDIT.json"
    csv_path = out_dir / "AUDIT.csv"
    txt_path = out_dir / "AUDIT.txt"

    payload = dict(payload)
    payload["results"] = [asdict(row) for row in rows]
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = [
        "key",
        "verdict",
        "codes",
        "canonical_file",
        "actual_file",
        "back_screen_key",
        "canonical_surface",
        "actual_surface",
        "canonical_resolution",
        "actual_resolution",
        "centered",
        "bbox_size",
        "backdrop_region",
        "blur_dim_equivalence",
        "back_screen_dependency",
        "metrics",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            data["codes"] = "|".join(row.codes)
            data["metrics"] = json.dumps(row.metrics, ensure_ascii=False, sort_keys=True)
            writer.writerow(data)

    lines = [
        "Modal backdrop/blur anti-fraud audit",
        f"Generated: {payload['generated_at']}",
        f"Canonical: {payload['inputs']['canonical_dir']}",
        f"Actual: {payload['inputs']['actual_dir']}",
        f"Summary: {payload['summary']}",
        "Safety: does not replace layered_visual_compare, qa/anti_fraud_scan.py, or VAS.",
        "",
    ]
    for row in rows:
        code_text = ",".join(row.codes) if row.codes else "test-blur-pass"
        lines.append(f"{row.verdict} {row.key} {code_text}")
        lines.append(f"  centered={row.centered} bbox={row.bbox_size} backdrop={row.backdrop_region} blur_dim={row.blur_dim_equivalence} back_screen={row.back_screen_dependency}")
        if row.metrics:
            lines.append(f"  metrics={json.dumps(row.metrics, ensure_ascii=False, sort_keys=True)}")
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "txt": txt_path}


def default_out_dir() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_ROOT / stamp


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit modal backdrop/blur fidelity against canonical HTML captures.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--key", help="Exact key, e.g. suite:dbt-practice-stop@light")
    group.add_argument("--all", action="store_true", help="Audit all canonical modal/window_modal keys.")
    parser.add_argument("--canonical", default=str(DEFAULT_CANONICAL_DIR), help="Canonical capture directory.")
    parser.add_argument("--actual", default=str(DEFAULT_ACTUAL_DIR), help="Runtime capture directory.")
    parser.add_argument("--out-dir", default=None, help="Report output directory.")
    parser.add_argument("--center-tolerance-px", type=int, default=18)
    parser.add_argument("--bbox-tolerance-px", type=int, default=32)
    parser.add_argument("--backdrop-mean-tolerance", type=float, default=22.0)
    parser.add_argument("--blur-ratio-tolerance", type=float, default=0.2)
    parser.add_argument("--parent-mean-tolerance", "--back-screen-mean-tolerance", dest="parent_mean_tolerance", type=float, default=35.0)
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> tuple[list[ModalAuditRow], dict[str, Any], dict[str, Path]]:
    canonical_dir = Path(args.canonical).resolve()
    actual_dir = Path(args.actual).resolve()
    canonical_captures = load_captures(canonical_dir, canonical=True)
    actual_captures = load_captures(actual_dir, canonical=False)

    if args.all:
        modal_keys = canonical_modal_keys(canonical_captures)
        keys = modal_keys
    else:
        modal_keys = [args.key]
        keys = [args.key]
    if not keys:
        raise SystemExit("No canonical modal keys found in MANIFEST.")

    rows = [
        audit_modal_key(
            key,
            canonical_dir=canonical_dir,
            actual_dir=actual_dir,
            canonical_captures=canonical_captures,
            actual_captures=actual_captures,
            center_tolerance_px=args.center_tolerance_px,
            bbox_tolerance_px=args.bbox_tolerance_px,
            backdrop_mean_tolerance=args.backdrop_mean_tolerance,
            blur_ratio_tolerance=args.blur_ratio_tolerance,
            parent_mean_tolerance=args.parent_mean_tolerance,
        )
        for key in keys
    ]
    pass_count = sum(1 for row in rows if row.verdict == "PASS")
    fail_count = sum(1 for row in rows if row.verdict != "PASS")
    total_canonical = len(modal_keys) if args.all else len(rows)
    skipped_unavailable_runtime: list[str] = []
    test_blur_pass = (
        len(rows) == total_canonical
        and pass_count == total_canonical
        and fail_count == 0
        and not skipped_unavailable_runtime
    )
    summary = {
        "total": len(rows),
        "pass": pass_count,
        "fail": fail_count,
        "test_blur_pass": test_blur_pass,
        "codes": sorted({code for row in rows for code in row.codes}),
        "skipped_unavailable_runtime": skipped_unavailable_runtime,
    }
    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "authority": "MODAL_BACKDROP_BLUR_ANTI_FRAUD",
        "inputs": {
            "canonical_dir": str(canonical_dir),
            "actual_dir": str(actual_dir),
            "keys": keys,
            "canonical_modal_keys": modal_keys,
        },
        "tolerances": {
            "center_tolerance_px": args.center_tolerance_px,
            "bbox_tolerance_px": args.bbox_tolerance_px,
            "backdrop_mean_tolerance": args.backdrop_mean_tolerance,
            "blur_ratio_tolerance": args.blur_ratio_tolerance,
            "back_screen_mean_tolerance": args.parent_mean_tolerance,
            "note": "Tolerances cover renderer noise and Qt-vs-Chromium rasterization; they do not permit invented dim/blur/backdrop.",
        },
        "coexists_with": [
            "qa/capture_v8.py",
            "qa/layered_visual_compare.py",
            "qa/anti_fraud_scan.py",
            "qa/vas_gate.py",
        ],
        "summary": summary,
    }
    out_dir = Path(args.out_dir).resolve() if args.out_dir else default_out_dir()
    paths = write_reports(rows, out_dir, payload)
    return rows, payload, paths


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    rows, payload, paths = run(args)
    print(f"JSON={paths['json']}")
    print(f"CSV={paths['csv']}")
    print(f"AUDIT={paths['txt']}")
    if payload["summary"]["test_blur_pass"]:
        print("test-blur-pass")
        return 0
    for row in rows:
        if row.verdict != "PASS":
            print(f"{row.key}: {','.join(row.codes)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
