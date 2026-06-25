"""Visual Auditor V3 — OCR-driven visual diff classification (no VLM).

Replaces VLM dependency with local Tesseract OCR + heuristic per-bbox
classification. Built on top of normalized reference (Fase 1).

Commands:
    python qa/visual_auditor_v3.py doctor
    python qa/visual_auditor_v3.py analyze --all
    python qa/visual_auditor_v3.py analyze --surface suite:avisos-search:light
    python qa/visual_auditor_v3.py queue
    python qa/visual_auditor_v3.py clear-cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import textwrap
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter
from rapidfuzz import fuzz

# Tesseract path auto-detection for Windows
_tesseract_path = os.environ.get("TESSDATA_PREFIX")
if not _tesseract_path:
    for p in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.exists(p):
            os.environ["PATH"] = os.pathsep.join(
                [os.path.dirname(p), os.environ.get("PATH", "")]
            )
            break

import pytesseract

warnings.filterwarnings("ignore", category=UserWarning)

_PROJ = Path(__file__).resolve().parent.parent
_NORM_MANIFEST = _PROJ / "qa" / "mockup_reference_normalized" / "manifest.json"
_NORM_DIR = _PROJ / "qa" / "mockup_reference_normalized"
_CAPTURE_DIR = _PROJ / "qa" / "_captures_v8"
_CAPTURE_MANIFEST = _CAPTURE_DIR / "CAPTURE_MANIFEST.json"
_FIDELITY_REPORT = _PROJ / "qa" / "_fidelity_current" / "FIDELITY_REPORT.json"
_OUT_DIR = _PROJ / "qa" / "_visual_auditor_v3" / "latest"
_CACHE_DIR = _PROJ / "qa" / "_visual_auditor_v3" / "cache"

# Use local tessdata if available (contains spa+eng)
_local_tessdata = str(_PROJ / "qa" / "tessdata")
if os.path.exists(_local_tessdata):
    os.environ["TESSDATA_PREFIX"] = _local_tessdata

_NAME_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+x\d+)\.png$")

VALID_LABELS: set[str] = {
    "LAYOUT_SHIFT",
    "SIZE_MISMATCH",
    "SPACING_MISMATCH",
    "COLOR_MISMATCH",
    "TEXT_MISMATCH_PROBABLE",
    "MISSING_COMPONENT",
    "EXTRA_COMPONENT",
    "CHROME_MISMATCH",
    "RENDER_NOISE",
    "PAIRING_OR_CAPTURE_MISMATCH",
    "NEEDS_HUMAN_REVIEW",
}

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "needs_review": 3}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}
DECISION_ORDER = {
    "FIX_PRODUCT_STRONG": 0,
    "FIX_PRODUCT_REVIEW": 1,
    "NEEDS_HUMAN_REVIEW": 2,
    "RENDER_NOISE_OK": 3,
    "PAIRING_FIX": 4,
}


@dataclass(frozen=True)
class SurfaceKey:
    app: str
    screen_id: str
    state_id: str
    theme: str

    @property
    def full(self) -> str:
        return f"{self.app}:{self.screen_id}-{self.state_id}:{self.theme}"


@dataclass
class Pairing:
    surface_key: str
    app: str
    view: str
    theme: str
    mockup_path: str
    real_capture_path: str
    diff_path: str
    overlay_path: str
    crop_paths: list[str] = field(default_factory=list)
    pairing_source: str = ""
    pairing_method: str = ""
    pairing_confidence: str = ""


@dataclass
class BBoxInfo:
    label: int
    geometry: tuple[int, int, int, int]
    area: int
    area_ratio: float
    normalization_artifact: bool = False
    artifact_reason: str = ""


@dataclass
class Metrics:
    ssim: float = 0.0
    ssim_method: str = ""
    mean_abs_diff: float = 0.0
    max_abs_diff: float = 0.0
    changed_pixel_ratio: float = 0.0
    size_mismatch: bool = False
    phash_distance: int = -1
    phash_method: str = "imagehash.phash"
    bbox_count: int = 0
    bbox_total_area_ratio: float = 0.0
    bbox_largest_area_ratio: float = 0.0
    bbox_largest_geometry: list[int] = field(default_factory=list)


@dataclass
class TextEvidence:
    mockup_ocr_top_lines: list[str] = field(default_factory=list)
    real_ocr_top_lines: list[str] = field(default_factory=list)
    diff_summary: str = ""
    fuzzy_ratio_worst: int = 100
    fuzzy_ratio_worst_pair: list[str] = field(default_factory=list)


@dataclass
class ColorEvidence:
    mockup_dominant_color_hex: str = ""
    mockup_dominant_color_name: str = ""
    real_dominant_color_hex: str = ""
    real_dominant_color_name: str = ""
    delta_rgb: int = 0
    interpretation: str = ""


@dataclass
class Classification:
    labels: list[str] = field(default_factory=list)
    severity: str = "needs_review"
    explanation: str = ""
    decision: str = "NEEDS_HUMAN_REVIEW"
    suspected_module: str = ""
    confidence: str = "low"
    confidence_reason: str = ""
    ocr_preprocessing_version: str = "v1"


@dataclass
class AgentPackage:
    surface_key: str
    decision: str = "NEEDS_HUMAN_REVIEW"
    decision_reason: str = ""
    top_bbox: dict[str, Any] = field(default_factory=dict)
    text_evidence: TextEvidence = field(default_factory=TextEvidence)
    color_evidence: ColorEvidence = field(default_factory=ColorEvidence)
    labels: list[str] = field(default_factory=list)
    severity: str = "needs_review"
    confidence: str = "low"
    suspected_module: str = ""
    suspected_lines_hint: str = ""
    what_to_check_first: str = ""
    do_not_touch_if: str = ""
    normalization_warning: str | None = None
    pairing_concerns: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _parse_capture_name(path: Path) -> tuple[str, str, str, str] | None:
    match = _NAME_RE.match(path.name)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3), match.group(4)


def _build_surface_key_from_manifest(item: dict) -> SurfaceKey:
    app = "suite" if "Suite" in item.get("product", "") else "hub"
    return SurfaceKey(
        app=app,
        screen_id=item["screen_id"],
        state_id=item.get("state_id", "default"),
        theme=item["theme"],
    )


def _build_capture_view(screen_id: str, state_id: str) -> str:
    primary_states = {"default", "score", "list", "normal", ""}
    if state_id in primary_states:
        return screen_id
    return f"{screen_id}-{state_id}"


def _surface_key_to_capture_filename(key: SurfaceKey) -> str:
    view = _build_capture_view(key.screen_id, key.state_id)
    return f"{key.app}-{view}-{key.theme}"


def _load_norm_manifest() -> list[dict]:
    if not _NORM_MANIFEST.exists():
        return []
    return json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))


def _load_capture_manifest() -> dict:
    if not _CAPTURE_MANIFEST.exists():
        return {}
    return json.loads(_CAPTURE_MANIFEST.read_text(encoding="utf-8"))


def _load_fidelity_report() -> dict:
    if not _FIDELITY_REPORT.exists():
        return {}
    return json.loads(_FIDELITY_REPORT.read_text(encoding="utf-8"))


def _load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _gray_mean(path: Path) -> float:
    try:
        img = _load_rgb(path).convert("L")
        arr = np.array(img)
        return float(arr.mean() / 255.0)
    except Exception:
        return 0.0


def _is_corrupt_or_blank(path: Path) -> bool:
    try:
        img = _load_rgb(path)
        arr = np.array(img.convert("L"))
        return float(arr.mean() / 255.0) > 0.985
    except Exception:
        return True


# ---------------------------------------------------------------------------
# Pairing
# ---------------------------------------------------------------------------


def pair_surfaces() -> list[Pairing]:
    norm_items = _load_norm_manifest()
    capture_manifest = _load_capture_manifest()
    capture_results = capture_manifest.get("results", [])

    # Index captures by (app, view, theme)
    capture_index: dict[tuple[str, str, str], dict] = {}
    for result in capture_results:
        fname = result.get("file", "")
        parsed = _parse_capture_name(Path(str(fname)))
        if parsed:
            app, view, theme, _ = parsed
            capture_index[(app, view, theme)] = result

    pairings: list[Pairing] = []
    for item in norm_items:
        app = item.get("app", "suite")
        view = item.get("view", "")
        theme = item.get("theme", "light")
        surface_key = f"{app}:{view}@{theme}"

        mockup_path = _NORM_DIR / theme / f"{view}.png"

        # Try capture index
        capture_key = (app, view, theme)
        capture_result = capture_index.get(capture_key)
        capture_path = None
        pairing_method = "manifest"
        pairing_confidence = "high"

        if capture_result:
            capture_path = _CAPTURE_DIR / capture_result["file"]
            if not capture_path.exists():
                capture_path = None
                pairing_confidence = "low"
        else:
            # Fallback: filename convention
            capture_fname = f"{app}-{view}-{theme}-960x600.png"
            capture_path = _CAPTURE_DIR / capture_fname
            if not capture_path.exists():
                # Try other resolutions
                for res in ["520x600", "480x325"]:
                    capture_path = _CAPTURE_DIR / f"{app}-{view}-{theme}-{res}.png"
                    if capture_path.exists():
                        break
                else:
                    capture_path = None
            pairing_method = "filename_fallback"
            pairing_confidence = "medium" if capture_path else "low"

        pairings.append(
            Pairing(
                surface_key=surface_key,
                app=app,
                view=view,
                theme=theme,
                mockup_path=str(mockup_path),
                real_capture_path=str(capture_path) if capture_path else "",
                diff_path="",
                overlay_path="",
                pairing_source="capture_manifest" if capture_result else "filename",
                pairing_method=pairing_method,
                pairing_confidence=pairing_confidence,
            )
        )

    return pairings


# ---------------------------------------------------------------------------
# Diff + BBoxes
# ---------------------------------------------------------------------------


def _extract_bboxes(
    mockup: Image.Image, real: Image.Image, top_k: int = 5
) -> tuple[list[BBoxInfo], Image.Image, Image.Image]:
    """Extract connected diff regions using scipy.ndimage.label."""
    try:
        from scipy import ndimage
    except ImportError:
        # Fallback: simple threshold without scipy
        diff = ImageChops.difference(mockup, real)
        diff_arr = np.array(diff.convert("L"))
        mask = diff_arr > 20
        # Simple bounding box of all non-zero
        ys, xs = np.where(mask)
        if len(xs) == 0:
            return [], diff, mockup.copy()
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        info = BBoxInfo(
            label=0,
            geometry=bbox,
            area=(bbox[2] - bbox[0]) * (bbox[3] - bbox[1]),
            area_ratio=(bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) / (mockup.width * mockup.height),
        )
        overlay = real.copy()
        draw = ImageDraw.Draw(overlay)
        draw.rectangle(bbox, outline="red", width=2)
        return [info], diff, overlay

    diff = ImageChops.difference(mockup, real)
    diff_arr = np.array(diff.convert("L"))
    mask = diff_arr > 20

    labeled, num_features = ndimage.label(mask)
    if num_features == 0:
        return [], diff, mockup.copy()

    bboxes: list[BBoxInfo] = []
    for i in range(1, num_features + 1):
        ys, xs = np.where(labeled == i)
        if len(xs) == 0:
            continue
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        area = (x1 - x0) * (y1 - y0)
        bboxes.append(
            BBoxInfo(
                label=i - 1,
                geometry=(x0, y0, x1, y1),
                area=area,
                area_ratio=area / (mockup.width * mockup.height),
            )
        )

    bboxes.sort(key=lambda b: b.area, reverse=True)
    bboxes = bboxes[:top_k]

    overlay = real.copy()
    draw = ImageDraw.Draw(overlay)
    for bbox in bboxes:
        draw.rectangle(bbox.geometry, outline="red", width=2)

    return bboxes, diff, overlay


def _mark_normalization_artifacts(
    bboxes: list[BBoxInfo], manifest_entry: dict
) -> list[BBoxInfo]:
    """Mark bboxes that fall in pad/crop zones as normalization artifacts."""
    lost_top = manifest_entry.get("lost_pixels_top", 0)
    lost_bottom = manifest_entry.get("lost_pixels_bottom", 0)
    pad_pixels = manifest_entry.get("pad_pixels", 0)
    target_h = manifest_entry.get("target_height", 600)

    for bbox in bboxes:
        _, y0, _, y1 = bbox.geometry
        # Falls in pad zone (bottom padding)
        if pad_pixels > 0 and y0 >= (target_h - pad_pixels - 5):
            bbox.normalization_artifact = True
            bbox.artifact_reason = "falls_in_pad_zone"
        # Falls in crop zone top
        elif lost_top > 0 and y1 <= (lost_top + 5):
            bbox.normalization_artifact = True
            bbox.artifact_reason = "falls_in_crop_zone_top"
        # Falls in crop zone bottom
        elif lost_bottom > 0 and y0 >= (target_h - lost_bottom - 5):
            bbox.normalization_artifact = True
            bbox.artifact_reason = "falls_in_crop_zone_bottom"

    return bboxes


# ---------------------------------------------------------------------------
# OCR + Heuristics per BBox
# ---------------------------------------------------------------------------


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """Upscale 2x, enhance contrast 1.5x, mild sharpen."""
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def _ocr_image(img: Image.Image) -> str:
    """Run Tesseract OCR with spa+eng, psm=6."""
    try:
        preprocessed = _preprocess_for_ocr(img)
        text = pytesseract.image_to_string(
            preprocessed, lang="spa+eng", config="--psm 6"
        )
        return text.strip()
    except Exception as e:
        return f"[OCR_ERROR: {e}]"


def _dominant_color(img: Image.Image) -> tuple[int, int, int]:
    """Get dominant color via PIL getcolors."""
    try:
        small = img.resize((50, 50), Image.Resampling.NEAREST)
        colors = small.getcolors(maxcolors=2500)
        if colors:
            c = max(colors, key=lambda x: x[0])[1]
            if isinstance(c, tuple):
                rgb = tuple(int(v) for v in c[:3])
                if len(rgb) == 3:
                    return rgb
                return (rgb[0], rgb[1], rgb[2]) if len(rgb) >= 3 else (0, 0, 0)
            return (int(c), int(c), int(c))
    except Exception:
        pass
    arr = np.array(img)
    return tuple(int(np.median(arr[:, :, i])) for i in range(3))


def _color_delta(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> int:
    return sum(abs(a - b) for a, b in zip(c1, c2))


def _edge_density(img: Image.Image) -> float:
    """Sobel edge density via numpy."""
    try:
        from scipy import ndimage
        arr = np.array(img.convert("L"))
        sx = ndimage.sobel(arr, axis=1)
        sy = ndimage.sobel(arr, axis=0)
        sobel = np.hypot(sx, sy)
        return float(np.mean(sobel > 20))
    except Exception:
        return 0.0


def _stddev(img: Image.Image) -> float:
    arr = np.array(img.convert("L"))
    return float(np.std(arr))


def _analyze_bbox(
    bbox: BBoxInfo,
    mockup_img: Image.Image,
    real_img: Image.Image,
    diff_img: Image.Image,
    pad: int = 20,
) -> dict[str, Any]:
    """Analyze a single bbox: OCR, color, edge, stddev."""
    x0, y0, x1, y1 = bbox.geometry
    w, h = mockup_img.size

    # Clamp with padding
    x0p = max(0, x0 - pad)
    y0p = max(0, y0 - pad)
    x1p = min(w, x1 + pad)
    y1p = min(h, y1 + pad)

    mockup_crop = mockup_img.crop((x0p, y0p, x1p, y1p))
    real_crop = real_img.crop((x0p, y0p, x1p, y1p))
    _ = diff_img.crop((x0p, y0p, x1p, y1p))  # unused, kept for symmetry

    # OCR
    mockup_ocr = _ocr_image(mockup_crop)
    real_ocr = _ocr_image(real_crop)

    # Fuzzy match line by line
    mockup_lines = [line.strip() for line in mockup_ocr.split("\n") if line.strip()]
    real_lines = [line.strip() for line in real_ocr.split("\n") if line.strip()]
    worst_ratio = 100
    worst_pair = ["", ""]
    for ml, rl in zip(mockup_lines, real_lines):
        if len(ml) > 2 or len(rl) > 2:
            ratio = fuzz.ratio(ml, rl)
            if ratio < worst_ratio:
                worst_ratio = ratio
                worst_pair = [ml, rl]

    # Color
    mockup_color = _dominant_color(mockup_crop)
    real_color = _dominant_color(real_crop)
    color_delta = _color_delta(mockup_color, real_color)

    # Edge density
    mockup_edge = _edge_density(mockup_crop)
    real_edge = _edge_density(real_crop)
    edge_delta = abs(mockup_edge - real_edge)

    # Stddev
    mockup_std = _stddev(mockup_crop)
    real_std = _stddev(real_crop)
    stddev_delta = abs(mockup_std - real_std)

    # Position relative to borders
    touches_left = x0 <= 5
    touches_right = x1 >= w - 5
    touches_top = y0 <= 5
    touches_bottom = y1 >= h - 5
    touches_borders = touches_left or touches_right or touches_top or touches_bottom

    return {
        "mockup_ocr": mockup_ocr,
        "real_ocr": real_ocr,
        "fuzzy_ratio_worst": worst_ratio,
        "fuzzy_ratio_worst_pair": worst_pair,
        "mockup_color": mockup_color,
        "real_color": real_color,
        "color_delta": color_delta,
        "mockup_edge": mockup_edge,
        "real_edge": real_edge,
        "edge_delta": edge_delta,
        "mockup_std": mockup_std,
        "real_std": real_std,
        "stddev_delta": stddev_delta,
        "touches_borders": touches_borders,
        "touches_left": touches_left,
        "touches_right": touches_right,
        "touches_top": touches_top,
        "touches_bottom": touches_bottom,
    }


# ---------------------------------------------------------------------------
# Classification Heuristics
# ---------------------------------------------------------------------------


def _classify_surface(
    bboxes: list[BBoxInfo],
    bbox_analyses: list[dict],
    manifest_entry: dict,
    metrics: Metrics,
    unreliable: bool = False,
    unreliable_reason: str = "",
) -> Classification:
    """Classify surface based on OCR + heuristics per bbox."""
    labels: list[str] = []
    severity = "low"
    confidence = "low"
    confidence_reason = ""
    decision = "NEEDS_HUMAN_REVIEW"

    if unreliable:
        labels.append("NEEDS_HUMAN_REVIEW")
        return Classification(
            labels=labels,
            severity="needs_review",
            explanation=f"unreliable=true: {unreliable_reason}",
            decision="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason=f"unreliable: {unreliable_reason}",
        )

    if not bboxes:
        labels.append("RENDER_NOISE")
        return Classification(
            labels=labels,
            severity="low",
            explanation="No diff bboxes detected",
            decision="RENDER_NOISE_OK",
            confidence="high",
            confidence_reason="No differences detected",
        )

    # Check if all bboxes are normalization artifacts
    all_artifacts = all(b.normalization_artifact for b in bboxes)
    if all_artifacts:
        labels.append("NEEDS_HUMAN_REVIEW")
        return Classification(
            labels=labels,
            severity="needs_review",
            explanation="All bboxes are normalization artifacts",
            decision="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason="all_bboxes_are_normalization_artifacts",
        )

    # Analyze non-artifact bboxes
    non_artifact_analyses = [
        a for b, a in zip(bboxes, bbox_analyses) if not b.normalization_artifact
    ]

    text_mismatch = False
    color_mismatch = False
    missing_component = False
    extra_component = False
    chrome_mismatch = False
    render_noise = True

    worst_fuzzy = 100
    worst_color_delta = 0
    worst_stddev_delta = 0

    for analysis in non_artifact_analyses:
        if analysis["fuzzy_ratio_worst"] < 85 and analysis["fuzzy_ratio_worst_pair"][0]:
            text_mismatch = True
            worst_fuzzy = min(worst_fuzzy, analysis["fuzzy_ratio_worst"])
        if analysis["color_delta"] > 30:
            color_mismatch = True
            worst_color_delta = max(worst_color_delta, analysis["color_delta"])
        if analysis["stddev_delta"] > 40:
            if analysis["mockup_std"] > analysis["real_std"]:
                missing_component = True
            else:
                extra_component = True
            worst_stddev_delta = max(worst_stddev_delta, analysis["stddev_delta"])
        if analysis["touches_borders"]:
            chrome_mismatch = True
        if analysis["fuzzy_ratio_worst"] < 100 or analysis["color_delta"] > 10:
            render_noise = False

    if text_mismatch:
        labels.append("TEXT_MISMATCH_PROBABLE")
    if color_mismatch:
        labels.append("COLOR_MISMATCH")
    if missing_component:
        labels.append("MISSING_COMPONENT")
    if extra_component:
        labels.append("EXTRA_COMPONENT")
    if chrome_mismatch:
        labels.append("CHROME_MISMATCH")
    if render_noise and not any([text_mismatch, color_mismatch, missing_component, extra_component]):
        labels.append("RENDER_NOISE")

    # Determine confidence
    if worst_fuzzy > 90 and not color_mismatch and not missing_component and not extra_component:
        confidence = "high"
        confidence_reason = "OCR matches well, no structural differences"
    elif text_mismatch and worst_fuzzy < 85:
        confidence = "medium"
        confidence_reason = f"OCR detected text mismatch (fuzzy={worst_fuzzy})"
    elif color_mismatch and worst_color_delta > 60:
        confidence = "medium"
        confidence_reason = f"Color mismatch detected (delta={worst_color_delta})"
    elif worst_fuzzy > 90:
        confidence = "high"
        confidence_reason = "OCR matches well, no structural differences"
    else:
        confidence = "low"
        confidence_reason = "No strong textual or color evidence"

    # Determine severity
    if text_mismatch or missing_component or extra_component:
        severity = "high"
    elif color_mismatch:
        severity = "medium"
    else:
        severity = "low"

    # Determine decision
    if confidence == "high" and (text_mismatch and worst_fuzzy < 70 or missing_component or extra_component):
        decision = "FIX_PRODUCT_STRONG"
    elif confidence == "medium" and (text_mismatch and worst_fuzzy < 85 or color_mismatch and worst_color_delta > 60):
        decision = "FIX_PRODUCT_REVIEW"
    elif render_noise and not any([text_mismatch, color_mismatch, missing_component, extra_component]):
        decision = "RENDER_NOISE_OK"
    else:
        decision = "NEEDS_HUMAN_REVIEW"

    return Classification(
        labels=labels,
        severity=severity,
        explanation=f"text_mismatch={text_mismatch}, color_mismatch={color_mismatch}, "
        f"missing={missing_component}, extra={extra_component}, "
        f"chrome={chrome_mismatch}, render_noise={render_noise}",
        decision=decision,
        confidence=confidence,
        confidence_reason=confidence_reason,
    )


# ---------------------------------------------------------------------------
# Agent Package
# ---------------------------------------------------------------------------


def _build_agent_package(
    surface_key: str,
    classification: Classification,
    bboxes: list[BBoxInfo],
    bbox_analyses: list[dict],
    manifest_entry: dict,
) -> AgentPackage:
    """Build agent_package.json with text + color evidence."""
    pkg = AgentPackage(
        surface_key=surface_key,
        decision=classification.decision,
        decision_reason=classification.confidence_reason,
        labels=classification.labels,
        severity=classification.severity,
        confidence=classification.confidence,
    )

    # Top bbox (first non-artifact, or first if all artifact)
    non_artifact = [b for b in bboxes if not b.normalization_artifact]
    top_bbox = non_artifact[0] if non_artifact else (bboxes[0] if bboxes else None)

    if top_bbox:
        analysis = next(
            (a for b, a in zip(bboxes, bbox_analyses) if b.label == top_bbox.label),
            {},
        )
        pkg.top_bbox = {
            "index": top_bbox.label,
            "geometry": list(top_bbox.geometry),
            "size_px": f"{top_bbox.geometry[2] - top_bbox.geometry[0]}x{top_bbox.geometry[3] - top_bbox.geometry[1]}",
            "position_relative": _describe_position(top_bbox.geometry, manifest_entry),
            "area_ratio": round(top_bbox.area_ratio, 4),
        }

        if analysis:
            pkg.text_evidence = TextEvidence(
                mockup_ocr_top_lines=[
                    line.strip()
                    for line in analysis.get("mockup_ocr", "").split("\n")
                    if line.strip()
                ][:5],
                real_ocr_top_lines=[
                    line.strip()
                    for line in analysis.get("real_ocr", "").split("\n")
                    if line.strip()
                ][:5],
                diff_summary=_ocr_diff_summary(analysis),
                fuzzy_ratio_worst=analysis.get("fuzzy_ratio_worst", 100),
                fuzzy_ratio_worst_pair=analysis.get("fuzzy_ratio_worst_pair", ["", ""]),
            )
            pkg.color_evidence = ColorEvidence(
                mockup_dominant_color_hex=_rgb_to_hex(analysis.get("mockup_color", (0, 0, 0))),
                mockup_dominant_color_name=_color_name(analysis.get("mockup_color", (0, 0, 0))),
                real_dominant_color_hex=_rgb_to_hex(analysis.get("real_color", (0, 0, 0))),
                real_dominant_color_name=_color_name(analysis.get("real_color", (0, 0, 0))),
                delta_rgb=analysis.get("color_delta", 0),
                interpretation=_color_interpretation(analysis),
            )

    pkg.suspected_module = _guess_module(surface_key)
    pkg.suspected_lines_hint = _guess_lines_hint(surface_key, classification.labels)
    pkg.what_to_check_first = _what_to_check(classification, bbox_analyses)
    pkg.do_not_touch_if = "confidence == 'low' OR no TEXT_MISMATCH detected"

    if manifest_entry.get("review_required"):
        pkg.normalization_warning = (
            f"review_required=true: {manifest_entry.get('review_reason', '')}"
        )

    return pkg


def _describe_position(geometry: tuple[int, int, int, int], manifest_entry: dict) -> str:
    x0, y0, x1, y1 = geometry
    w = manifest_entry.get("target_width", 960)
    h = manifest_entry.get("target_height", 600)
    cx, cy = (x0 + x1) / 2 / w, (y0 + y1) / 2 / h

    vert = "top" if cy < 0.33 else "center" if cy < 0.66 else "bottom"
    horiz = "left" if cx < 0.33 else "center" if cx < 0.66 else "right"
    band = "header" if y1 < h * 0.15 else "footer" if y0 > h * 0.85 else "content"

    return f"{band} band, {vert}-{horiz} quadrant"


def _ocr_diff_summary(analysis: dict) -> str:
    pair = analysis.get("fuzzy_ratio_worst_pair", ["", ""])
    if pair[0] and pair[1] and pair[0] != pair[1]:
        return f"'{pair[0]}' vs '{pair[1]}' (fuzzy={analysis.get('fuzzy_ratio_worst', 0)})"
    return "No significant OCR difference"


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _color_name(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    if r > 200 and g > 200 and b > 200:
        return "near-white"
    if r < 50 and g < 50 and b < 50:
        return "near-black"
    if g > r and g > b:
        return "green-ish"
    if r > g and r > b:
        return "red-ish"
    if b > r and b > g:
        return "blue-ish"
    if r > 150 and g > 150:
        return "yellow-ish"
    return "mixed"


def _color_interpretation(analysis: dict) -> str:
    delta = analysis.get("color_delta", 0)
    if delta > 100:
        return "Strong color difference — likely different UI state or theme mismatch"
    elif delta > 30:
        return "Moderate color difference — possible component styling change"
    return "Minor color variation — likely render noise"


def _guess_module(surface_key: str) -> str:
    """Guess suspected module from surface key."""
    if "avisos" in surface_key:
        return "app/modules/avisos_qt.py"
    if "actividades" in surface_key:
        return "app/modules/actividades_qt.py"
    if "rutina" in surface_key:
        return "app/modules/rutina_qt.py"
    if "timer" in surface_key or "respiracion" in surface_key:
        return "app/modules/timer_qt.py"
    if "dbt" in surface_key:
        return "app/modules/dbt_qt.py"
    if "registro" in surface_key:
        return "app/modules/registro_qt.py"
    if "onboarding" in surface_key:
        return "app/modules/onboarding_qt.py"
    if "home" in surface_key:
        return "app/modules/home_qt.py"
    if "hub" in surface_key:
        return "hub/screens.py"
    if "pacientes" in surface_key:
        return "hub/pacientes.py"
    return "app/modules/unknown.py"


def _guess_lines_hint(surface_key: str, labels: list[str]) -> str:
    if "TEXT_MISMATCH_PROBABLE" in labels:
        return "Check setMinimumWidth, padding, or font metrics for truncated text"
    if "COLOR_MISMATCH" in labels:
        return "Check QSS stylesheets or palette definitions for color differences"
    if "MISSING_COMPONENT" in labels:
        return "Check widget visibility or conditional rendering logic"
    if "EXTRA_COMPONENT" in labels:
        return "Check for duplicate widgets or unexpected overlays"
    return "General visual inspection needed"


def _what_to_check(classification: Classification, bbox_analyses: list[dict]) -> str:
    if classification.decision == "FIX_PRODUCT_STRONG":
        return "Apply fix with high confidence — OCR and structural evidence are strong"
    elif classification.decision == "FIX_PRODUCT_REVIEW":
        return "Review OCR diff and color evidence before applying fix"
    elif classification.decision == "RENDER_NOISE_OK":
        return "No action needed — differences are render noise"
    return "Insufficient evidence — needs human review or better capture"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _cache_key(
    mockup_sha: str, capture_sha: str, bbox_geometry: tuple, ocr_version: str = "v1"
) -> str:
    geom_str = "_".join(str(x) for x in bbox_geometry)
    return hashlib.sha256(
        f"{mockup_sha}:{capture_sha}:{geom_str}:{ocr_version}".encode()
    ).hexdigest()


def _cache_path(key: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{key}.json"


def _load_cached(key: str) -> dict | None:
    path = _cache_path(key)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cached(key: str, data: dict) -> None:
    _cache_path(key).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Analyze Surface
# ---------------------------------------------------------------------------


def analyze_surface(
    pairing: Pairing,
    out_dir: Path,
    manifest_lookup: dict[str, dict],
) -> dict[str, Any]:
    """Analyze one surface and produce all outputs."""
    surface_key = pairing.surface_key
    # Sanitize surface_key for filesystem (Windows forbids colons)
    safe_surface_key = surface_key.replace(":", "_").replace("@", "_")
    surface_out = out_dir / "surfaces" / safe_surface_key
    surface_out.mkdir(parents=True, exist_ok=True)

    # Load images
    mockup_path = Path(pairing.mockup_path)
    capture_path = Path(pairing.real_capture_path) if pairing.real_capture_path else None

    # Hard technical conditions for unreliable
    unreliable = False
    unreliable_reason = ""

    if not mockup_path.exists() or not capture_path or not capture_path.exists():
        unreliable = True
        unreliable_reason = "missing_file"
    elif _is_corrupt_or_blank(mockup_path) or (capture_path and _is_corrupt_or_blank(capture_path)):
        unreliable = True
        unreliable_reason = "corrupt_image"
    else:
        try:
            mockup_img = _load_rgb(mockup_path)
            real_img = _load_rgb(capture_path) if capture_path else None
            if mockup_img.size == (0, 0) or (real_img and real_img.size == (0, 0)):
                unreliable = True
                unreliable_reason = "impossible_size"
            elif max(mockup_img.size) > 10000 or (real_img and max(real_img.size) > 10000):
                unreliable = True
                unreliable_reason = "impossible_size"
        except Exception:
            unreliable = True
            unreliable_reason = "corrupt_image"

    if unreliable:
        classification = Classification(
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            explanation=f"unreliable=true: {unreliable_reason}",
            decision="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason=f"unreliable: {unreliable_reason}",
        )
        agent_pkg = AgentPackage(
            surface_key=surface_key,
            decision="NEEDS_HUMAN_REVIEW",
            decision_reason=f"unreliable=true: {unreliable_reason}",
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            confidence="low",
        )
        result = {
            "pairing": asdict(pairing),
            "metrics": asdict(Metrics()),
            "classification": asdict(classification),
            "agent_package": asdict(agent_pkg),
        }
        (surface_out / "agent_package.json").write_text(
            json.dumps(asdict(agent_pkg), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return result

    # Load images for real analysis
    mockup_img = _load_rgb(mockup_path)
    real_img = _load_rgb(capture_path)

    # Ensure same size
    if mockup_img.size != real_img.size:
        real_img = real_img.resize(mockup_img.size, Image.Resampling.LANCZOS)

    # Diff + bboxes
    bboxes, diff_img, overlay = _extract_bboxes(mockup_img, real_img, top_k=5)

    # Mark normalization artifacts
    manifest_entry = manifest_lookup.get(surface_key, {})
    bboxes = _mark_normalization_artifacts(bboxes, manifest_entry)

    # Save images
    mockup_img.save(surface_out / "mockup.png")
    real_img.save(surface_out / "real.png")
    diff_img.save(surface_out / "diff.png")
    overlay.save(surface_out / "overlay.png")

    # Analyze bboxes
    bbox_analyses: list[dict] = []
    crops_dir = surface_out / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)

    for bbox in bboxes:
        x0, y0, x1, y1 = bbox.geometry
        pad = 20
        w, h = mockup_img.size
        x0p = max(0, x0 - pad)
        y0p = max(0, y0 - pad)
        x1p = min(w, x1 + pad)
        y1p = min(h, y1 + pad)

        mockup_crop = mockup_img.crop((x0p, y0p, x1p, y1p))
        real_crop = real_img.crop((x0p, y0p, x1p, y1p))
        diff_crop = diff_img.crop((x0p, y0p, x1p, y1p))

        bbox_dir = crops_dir / f"bbox_{bbox.label}"
        bbox_dir.mkdir(parents=True, exist_ok=True)
        mockup_crop.save(bbox_dir / "mockup.png")
        real_crop.save(bbox_dir / "real.png")
        diff_crop.save(bbox_dir / "diff.png")

        # Cache key
        mockup_sha = _sha256_file(mockup_path)
        capture_sha = _sha256_file(capture_path)
        cache_key = _cache_key(mockup_sha, capture_sha, bbox.geometry, "v1")
        cached = _load_cached(cache_key)

        if cached:
            analysis = cached
        else:
            analysis = _analyze_bbox(bbox, mockup_img, real_img, diff_img)
            # Save OCR text
            (bbox_dir / "ocr_mockup.txt").write_text(analysis["mockup_ocr"], encoding="utf-8")
            (bbox_dir / "ocr_real.txt").write_text(analysis["real_ocr"], encoding="utf-8")
            _save_cached(cache_key, analysis)

        bbox_analyses.append(analysis)

    # Metrics
    metrics = Metrics(
        bbox_count=len(bboxes),
        bbox_total_area_ratio=sum(b.area_ratio for b in bboxes),
        bbox_largest_area_ratio=bboxes[0].area_ratio if bboxes else 0.0,
        bbox_largest_geometry=list(bboxes[0].geometry) if bboxes else [],
    )

    # Classification
    classification = _classify_surface(
        bboxes, bbox_analyses, manifest_entry, metrics, unreliable, unreliable_reason
    )

    # Agent package
    agent_pkg = _build_agent_package(surface_key, classification, bboxes, bbox_analyses, manifest_entry)

    # Save outputs
    (surface_out / "metrics.json").write_text(
        json.dumps(asdict(metrics), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (surface_out / "classification.json").write_text(
        json.dumps(asdict(classification), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (surface_out / "agent_package.json").write_text(
        json.dumps(asdict(agent_pkg), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "pairing": asdict(pairing),
        "metrics": asdict(metrics),
        "classification": asdict(classification),
        "agent_package": asdict(agent_pkg),
    }


# ---------------------------------------------------------------------------
# HTML Report
# ---------------------------------------------------------------------------


def generate_html(results: list[dict], out_path: Path) -> None:
    """Generate navigable HTML report."""
    rows = []
    for r in results:
        pkg = r.get("agent_package", {})
        cls = r.get("classification", {})
        severity = cls.get("severity", "low")
        decision = cls.get("decision", "NEEDS_HUMAN_REVIEW")
        confidence = cls.get("confidence", "low")
        labels = ", ".join(cls.get("labels", []))
        surface_key = pkg.get("surface_key", "")
        rows.append(
            f"""
        <tr class="severity-{severity}">
            <td>{surface_key}</td>
            <td>{severity}</td>
            <td>{confidence}</td>
            <td>{decision}</td>
            <td>{labels}</td>
            <td><a href="surfaces/{surface_key}/agent_package.json">agent_package</a></td>
        </tr>"""
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Visual Auditor V3 Report</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f0f0f0; }}
        .severity-high {{ background: #ffcccc; }}
        .severity-medium {{ background: #ffffcc; }}
        .severity-low {{ background: #ccffcc; }}
        .severity-needs_review {{ background: #ccccff; }}
    </style>
</head>
<body>
    <h1>Visual Auditor V3 Report</h1>
    <p>Total surfaces: {len(results)}</p>
    <table>
        <tr><th>Surface</th><th>Severity</th><th>Confidence</th><th>Decision</th><th>Labels</th><th>Link</th></tr>
        {''.join(rows)}
    </table>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


def build_queue(results: list[dict]) -> str:
    """Build prioritized queue markdown."""
    # Sort by severity, then confidence, then decision
    def sort_key(r: dict) -> tuple[int, int, int]:
        cls = r.get("classification", {})
        sev = SEVERITY_ORDER.get(cls.get("severity", "low"), 2)
        conf = CONFIDENCE_ORDER.get(cls.get("confidence", "low"), 2)
        dec = DECISION_ORDER.get(cls.get("decision", "NEEDS_HUMAN_REVIEW"), 2)
        return (sev, conf, dec)

    sorted_results = sorted(results, key=sort_key)

    lines = ["# Visual Auditor V3 — Prioritized Queue\n"]
    for r in sorted_results:
        pkg = r.get("agent_package", {})
        cls = r.get("classification", {})
        lines.append(
            f"- **{pkg.get('surface_key', '')}** | "
            f"severity={cls.get('severity', 'low')} | "
            f"confidence={cls.get('confidence', 'low')} | "
            f"decision={cls.get('decision', 'NEEDS_HUMAN_REVIEW')} | "
            f"labels={', '.join(cls.get('labels', []))}"
        )
        if pkg.get("decision_reason"):
            lines.append(f"  - {pkg['decision_reason']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------


def doctor() -> bool:
    """Validate environment for V3."""
    ok = True

    # 1. Normalized manifest
    if not _NORM_MANIFEST.exists():
        print("[MISSING] qa/mockup_reference_normalized/manifest.json — run Fase 1 first")
        ok = False
    else:
        print("[OK] Normalized manifest exists")

    # 2. Capture manifest
    if not _CAPTURE_MANIFEST.exists():
        print("[MISSING] qa/_captures_v8/CAPTURE_MANIFEST.json")
        ok = False
    else:
        print("[OK] Capture manifest exists")

    # 3. Fidelity report (optional, warn only)
    if not _FIDELITY_REPORT.exists():
        print("[WARN] qa/_fidelity_current/FIDELITY_REPORT.json — run diff_fidelity.py")
    else:
        print("[OK] Fidelity report exists")

    # 4. Dependencies
    import importlib
    deps = [("PIL", "Pillow"), ("numpy", "numpy"), ("scipy", "scipy"), ("pytesseract", "pytesseract"), ("rapidfuzz", "rapidfuzz")]
    for import_name, pip_name in deps:
        try:
            importlib.import_module(import_name)
            print(f"[OK] {pip_name} available")
        except ImportError:
            print(f"[MISSING] {pip_name} — pip install {pip_name}")
            ok = False

    # 5. Tesseract binary
    try:
        ver = pytesseract.get_tesseract_version()
        print(f"[OK] Tesseract binary: {ver}")
    except Exception as e:
        print(f"[MISSING] Tesseract binary not found: {e}")
        ok = False

    # 6. Tesseract languages
    try:
        langs = pytesseract.get_languages()
        if "spa" in langs and "eng" in langs:
            print("[OK] Tesseract languages: spa+eng")
        else:
            print(f"[WARN] Tesseract languages: {langs} — need spa+eng")
    except Exception as e:
        print(f"[WARN] Could not check Tesseract languages: {e}")

    # 7. V2 still exists
    v2_path = _PROJ / "qa" / "visual_auditor_v2.py"
    if v2_path.exists():
        print("[OK] V2 still present (expected)")
    else:
        print("[WARN] V2 missing — should be preserved until Fase 3")

    # 8. Output dir gitignored
    gitignore = _PROJ / ".gitignore"
    if gitignore.exists() and "qa/_visual_auditor_v3/" in gitignore.read_text():
        print("[OK] qa/_visual_auditor_v3/ is gitignored")
    else:
        print("[WARN] qa/_visual_auditor_v3/ should be in .gitignore")

    # 9. No writes to static/normalized
    print("[OK] V3 does not write to mockup_reference_static/ or mockup_reference_normalized/")

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual Auditor V3")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Validate environment")

    analyze_parser = sub.add_parser("analyze", help="Analyze surfaces")
    analyze_parser.add_argument("--all", action="store_true", help="Analyze all surfaces")
    analyze_parser.add_argument("--surface", type=str, help="Analyze one surface")

    sub.add_parser("queue", help="Generate prioritized queue")
    sub.add_parser("clear-cache", help="Clear OCR cache")

    args = parser.parse_args()

    if args.command == "doctor":
        return 0 if doctor() else 1

    if args.command == "clear-cache":
        if _CACHE_DIR.exists():
            for f in _CACHE_DIR.glob("*.json"):
                f.unlink()
        print("[OK] Cache cleared")
        return 0

    if args.command == "analyze":
        if not args.all and not args.surface:
            print("Usage: analyze --all | --surface <key>")
            return 1

        # Load manifest lookup
        manifest_items = _load_norm_manifest()
        manifest_lookup: dict[str, dict] = {}
        for item in manifest_items:
            key = f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}"
            manifest_lookup[key] = item

        pairings = pair_surfaces()
        if args.surface:
            pairings = [p for p in pairings if p.surface_key == args.surface]
            if not pairings:
                print(f"Surface not found: {args.surface}")
                return 1

        _OUT_DIR.mkdir(parents=True, exist_ok=True)
        results: list[dict] = []

        for pairing in pairings:
            print(f"Analyzing {pairing.surface_key}...")
            result = analyze_surface(pairing, _OUT_DIR, manifest_lookup)
            results.append(result)

        # Save report
        report_path = _OUT_DIR / "report.json"
        report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Report saved to {report_path}")

        # Generate HTML
        html_path = _OUT_DIR / "index.html"
        generate_html(results, html_path)
        print(f"[OK] HTML report saved to {html_path}")

        # Generate queue
        queue_path = _OUT_DIR / "queue.md"
        queue_path.write_text(build_queue(results), encoding="utf-8")
        print(f"[OK] Queue saved to {queue_path}")

        return 0

    if args.command == "queue":
        report_path = _OUT_DIR / "report.json"
        if not report_path.exists():
            print("[ERROR] No report.json — run analyze first")
            return 1
        results = json.loads(report_path.read_text(encoding="utf-8"))
        queue_path = _OUT_DIR / "queue.md"
        queue_path.write_text(build_queue(results), encoding="utf-8")
        print(f"[OK] Queue saved to {queue_path}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
