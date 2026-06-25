"""Visual Auditor V3 — OCR-driven visual diff classification (no VLM).

Replaces VLM dependency with local Tesseract OCR + heuristic per-bbox
classification. Built on top of normalized reference (Fase 1).

Commands:
    python qa/visual_auditor_v3.py doctor
    python qa/visual_auditor_v3.py analyze --all
    python qa/visual_auditor_v3.py analyze --surface suite:avisos-search@light
    python qa/visual_auditor_v3.py queue
    python qa/visual_auditor_v3.py clear-cache

Surface key canonical form: 'app:view@theme' (e.g. 'suite:avisos@light',
    'hub:pacientes@dark'). The 'app:view:theme' alias (e.g.
    'suite:avisos-search:light') is also accepted by --surface and
    normalized automatically.
"""

from __future__ import annotations

import argparse
from datetime import datetime
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
import shutil
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
    ssim_method: str = "skimage_unavailable_fallback_mean"
    mean_abs_diff: float = 0.0
    max_abs_diff: int = 0
    changed_pixel_ratio: float = 0.0
    size_mismatch: bool = False
    phash_distance: int = -1
    phash_method: str = "not_computed"  # pHash intentionally not used (no DCT dep);
    # see _compute_metrics docstring for the honest audit note.
    bbox_count: int = 0
    bbox_total_area_ratio: float = 0.0
    bbox_largest_area_ratio: float = 0.0
    bbox_largest_geometry: list[int] = field(default_factory=list)
    notes: str = ""


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
class ActionableEvidence:
    """Per-surface actionable payload emitted on every surface (no matter the
    route). Consumed by agents — never by humans. Independent of
    agent_route: a NO_ACTION_NEEDED surface still gets this so consumers
    can audit why V3 concluded stability.
    """
    divergences: list[str] = field(default_factory=list)
    probable_module: str = ""
    probable_root_cause: str = ""  # render_noise | real_text_mismatch | ocr_garbage | color_theme_bleed | structural_component | unknown
    real_visual_signals: list[str] = field(default_factory=list)
    next_action: str = ""
    evidence_strength: str = "weak"  # strong | medium | weak


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


# Agent route taxonomy — replaces NEEDS_HUMAN_REVIEW as the operational output.
# Every surface must land in one of these; none may require_owner_review.
AGENT_ROUTES: set[str] = {
    "PRODUCT_ACTIONABLE",
    "QA_TOOLING_ACTIONABLE",
    "CAPTURE_OR_PAIRING_ACTIONABLE",
    "AUDITOR_IMPROVEMENT_ACTIONABLE",
    "RENDER_NOISE_AUTO_IGNORED",
    "NO_ACTION_NEEDED_WITH_EVIDENCE",
}


@dataclass
class AgentPackage:
    surface_key: str
    decision: str = "NEEDS_HUMAN_REVIEW"  # kept for internal compat; not shown to owner
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
    fidelity_available: bool = True  # owner audit rule A — False when
    # FIDELITY_REPORT.json is missing/empty/has 0 comparisons.
    # --- V3 reorientation: agent-facing output ---
    diff_summary: str = ""  # top-level mirror of text_evidence.diff_summary
    # so consumers do not need to dig into text_evidence to see what OCR
    # conclusion drove the routing decision.
    agent_route: str = "AUDITOR_IMPROVEMENT_ACTIONABLE"
    agent_next_action: str = ""
    requires_owner_review: bool = False
    why_not_owner_review: str = ""
    evidence_quality: str = "weak"  # strong | medium | weak | none
    diagnostic_labels: list[str] = field(default_factory=list)
    product_action_allowed: bool = False
    qa_action_allowed: bool = False
    capture_action_allowed: bool = False
    actionable_evidence: ActionableEvidence = field(default_factory=ActionableEvidence)


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


def _check_fidelity_available() -> bool:
    """Owner audit rule A: True iff FIDELITY_REPORT.json exists, parses,
    and has at least 1 comparison. False means diff_fidelity was not
    run or produced 0 targets — the metric numbers in the report should
    not be treated as real signal.
    """
    if not _FIDELITY_REPORT.exists():
        return False
    try:
        data = json.loads(_FIDELITY_REPORT.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return False
    if isinstance(data, list):
        return len(data) > 0
    if isinstance(data, dict):
        comparisons = data.get("comparisons", [])
        return len(comparisons) > 0
    return False


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


def _parse_surface_key(surface_key: str) -> tuple[str, str, str] | None:
    """Parse a canonical surface_key 'app:view@theme' into (app, view, theme).

    Returns None if the format doesn't match. This is the canonical form
    defined by mockup_reference_normalized/manifest.json (e.g.
    'suite:avisos@light' or 'hub:pacientes@light').
    """
    if not surface_key:
        return None
    # Format: {app}:{view}@{theme}  (e.g. suite:avisos-filter-activos@light)
    m = re.match(r"^(suite|hub):(.+)@(light|dark)$", surface_key)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def _normalize_surface_alias(surface_key: str) -> str:
    """Normalize surface_key aliases to the canonical form 'app:view@theme'.

    Accepts:
        - canonical:         'suite:avisos@light'
        - colon-theme alias: 'suite:avisos-search:light' -> 'suite:avisos-search@light'
    Returns the input unchanged if it doesn't match either pattern (caller
    will surface 'Surface not found' as before).
    """
    if not surface_key:
        return surface_key
    if _parse_surface_key(surface_key):
        return surface_key
    # Try alias: app:view:theme
    m = re.match(r"^(suite|hub):(.+):(light|dark)$", surface_key)
    if m:
        return f"{m.group(1)}:{m.group(2)}@{m.group(3)}"
    return surface_key


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
        # Manifest entries have no separate 'app' field — derive it from
        # surface_key ('suite:view@theme' or 'hub:view@theme'). This is the
        # fix for the Hub pairing being broken (previously defaulted to 'suite').
        raw_surface_key = item.get("surface_key", "")
        parsed_key = _parse_surface_key(raw_surface_key)
        if parsed_key:
            app, view, theme = parsed_key
        else:
            # Fallback: trust explicit fields if surface_key is malformed
            app = item.get("app") or "suite"
            view = item.get("view", "")
            theme = item.get("theme", "light")
            raw_surface_key = f"{app}:{view}@{theme}"
        surface_key = raw_surface_key

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


# Threshold above which a single bbox's area ratio is considered to
# dominate the image. When a bbox is this large we can't trust OCR-driven
# text/colour decisions — the evidence almost certainly comes from a big
# background region (render noise, theme fill, scroll artifact, etc.).
LARGEST_BBOX_GUARDRAIL = 0.35

# Threshold above which a fuzzy ratio means "OCR matches well" — i.e. we
# must NOT emit TEXT_MISMATCH_PROBABLE or a FIX_PRODUCT_* decision driven
# by text. Owner audit rule: if fuzzy >= 95, no text-based decision.
FUZZY_MATCH_THRESHOLD = 95

# Threshold below which fuzzy ratio means "OCR noise / garbage". When
# fuzzy < 30 and we don't have a real-text pair, we treat the result as
# not-actionable evidence.
FUZZY_NOISE_THRESHOLD = 30

# Generic phrases that are forbidden in what_to_check_first / decision_reason
# when the decision is FIX_PRODUCT_STRONG or FIX_PRODUCT_REVIEW. If we can
# only produce one of these phrases, the decision must be downgraded to
# NEEDS_HUMAN_REVIEW (owner audit rule E).
FORBIDDEN_GENERIC_PHRASES = (
    "Review OCR diff and color evidence before applying fix",
    "Check visual difference",
    "Review manually",
    "No significant OCR difference",
    "Insufficient evidence",
    "Apply fix with high confidence",
    "General visual inspection needed",
)


def _is_generic_phrase(text: str) -> bool:
    """True if text contains any of the forbidden generic phrases."""
    if not text:
        return True
    t = text.strip()
    if not t:
        return True
    for phrase in FORBIDDEN_GENERIC_PHRASES:
        if phrase.lower() in t.lower():
            return True
    return False


def _real_fuzzy_in_evidence(bbox_analyses: list[dict]) -> int:
    """Worst fuzzy ratio across all bboxes (unfiltered, no min-via-mismatch
    trick). Used to detect contradictions between decision_reason and
    text_evidence (owner audit rule C)."""
    worst = 100
    for a in bbox_analyses:
        r = int(a.get("fuzzy_ratio_worst", 100))
        if r < worst:
            worst = r
    return worst


def _has_real_text_pair(bbox_analyses: list[dict]) -> bool:
    """True if at least one bbox has a real (non-noise) OCR pair."""
    for a in bbox_analyses:
        if _looks_like_real_text_pair(a.get("mockup_ocr", ""), a.get("real_ocr", "")):
            return True
    return False


# ---------------------------------------------------------------------------
# Agent Route Mapping — V3 reorientation: no surface goes to owner
# ---------------------------------------------------------------------------


def _map_to_agent_route(
    classification: Classification,
    bboxes: list[BBoxInfo],
    bbox_analyses: list[dict],
    metrics: Metrics,
    manifest_entry: dict,
    biggest_bbox_dominates: bool,
    all_artifacts: bool,
    pairing: Pairing,
) -> tuple[str, str, str, str, list[str], bool, bool, bool]:
    """Map a classification + evidence to an agent route.

    Returns:
        (agent_route, agent_next_action, evidence_quality, why_not_owner_review,
         diagnostic_labels, product_action_allowed, qa_action_allowed,
         capture_action_allowed)

    Hard rule: requires_owner_review is ALWAYS False. If we can't decide,
    we send to AUDITOR_IMPROVEMENT_ACTIONABLE with a concrete next step.
    """
    decision = classification.decision
    labels = list(classification.labels)
    confidence = classification.confidence

    # --- Compute evidence quality ---
    worst_fuzzy_real = _real_fuzzy_in_evidence(bbox_analyses)
    has_real_text = _has_real_text_pair(bbox_analyses)
    has_color = any(a.get("color_delta", 0) > 30 for a in bbox_analyses)
    has_structural = "MISSING_COMPONENT" in labels or "EXTRA_COMPONENT" in labels

    if has_structural and confidence == "high":
        evidence_quality = "strong"
    elif has_real_text and worst_fuzzy_real < 70 and confidence in ("high", "medium"):
        evidence_quality = "strong"
    elif has_real_text and worst_fuzzy_real < 85 and confidence == "medium":
        evidence_quality = "medium"
    elif has_color and confidence == "medium":
        evidence_quality = "medium"
    elif has_real_text or has_color or has_structural:
        evidence_quality = "weak"
    else:
        evidence_quality = "none"

    # --- Diagnostic labels (technical, not operational) ---
    diagnostic_labels = []
    if has_real_text:
        diagnostic_labels.append("TEXT_MISMATCH")
    if has_color:
        diagnostic_labels.append("COLOR_MISMATCH")
    if has_structural:
        diagnostic_labels.append("STRUCTURAL_SIGNAL")
    if biggest_bbox_dominates:
        diagnostic_labels.append("BBOX_TOO_BROAD")
    if worst_fuzzy_real < 30 and not has_real_text:
        diagnostic_labels.append("OCR_NOISE")
    elif worst_fuzzy_real < 95 and not has_real_text:
        diagnostic_labels.append("OCR_WEAK")
    if "CHROME_MISMATCH" in labels:
        diagnostic_labels.append("CHROME_MISMATCH")
    if metrics.changed_pixel_ratio < 0.01 and metrics.mean_abs_diff < 5:
        diagnostic_labels.append("RENDER_NOISE")
    if not diagnostic_labels:
        diagnostic_labels.append("NO_SIGNIFICANT_SIGNAL")

    # --- Determine route ---
    product_action_allowed = False
    qa_action_allowed = False
    capture_action_allowed = False

    # Case 0: Auditor internal decision is RENDER_NOISE_OK and nothing contradicts.
    # SSIM near 1.0 IS the actionable evidence: visual content matches, pixel-level
    # diffs are theme/chrome/scrollbar noise. changed_pixel_ratio is NOT used as
    # a hard gate because a 25% diff at SSIM 0.9999 is still render noise.
    if (
        classification.decision == "RENDER_NOISE_OK"
        and metrics.ssim >= 0.95
        and "MISSING_COMPONENT" not in labels
        and "EXTRA_COMPONENT" not in labels
    ):
        agent_route = "NO_ACTION_NEEDED_WITH_EVIDENCE"
        agent_next_action = (
            f"V3 verified visual stability. SSIM={metrics.ssim:.3f}, "
            f"changed_pixel_ratio={metrics.changed_pixel_ratio:.4f}, "
            f"largest_bbox_area_ratio={metrics.bbox_largest_area_ratio:.3f} "
            f"(theme/chrome variance, not a bug)."
        )
        why_not_owner_review = (
            "Auditor internal decision is RENDER_NOISE_OK with high SSIM and "
            "no structural labels. No actionable product change."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 1: No bboxes at all → no signal
    if metrics.bbox_count == 0:
        agent_route = "NO_ACTION_NEEDED_WITH_EVIDENCE"
        agent_next_action = (
            "No action. V3 found no diff bboxes after pixel-level comparison. "
            "Surface is visually stable."
        )
        why_not_owner_review = (
            "No pixel differences detected; nothing to review or fix."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 1b: All bboxes are normalization artifacts → pad/crop noise
    if all_artifacts:
        agent_route = "RENDER_NOISE_AUTO_IGNORED"
        agent_next_action = (
            "All detected differences are in normalization artifacts (pad/crop zones). "
            "No product action needed."
        )
        why_not_owner_review = (
            "Pad/crop artifacts are expected from Fase 1 normalization, not product bugs."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 2: Biggest bbox dominates (>35%) without localized sub-evidence
    if biggest_bbox_dominates:
        if has_real_text and worst_fuzzy_real < 70:
            # Even with big bbox, there IS localized text evidence — send to QA
            # to split into bands and re-run
            agent_route = "QA_TOOLING_ACTIONABLE"
            agent_next_action = (
                f"BBox extraction is dominated by a full-screen region "
                f"(area_ratio={metrics.bbox_largest_area_ratio:.3f}). "
                f"However, OCR detected real text mismatch (worst_fuzzy={worst_fuzzy_real}). "
                f"Split the diff into horizontal bands and rerun OCR on "
                f"tab/header areas before product changes."
            )
            qa_action_allowed = True
        else:
            # No localized evidence — auto-ignore as render noise
            agent_route = "RENDER_NOISE_AUTO_IGNORED"
            agent_next_action = (
                f"No product action. Differences are dominated by a single "
                f"large region (area_ratio={metrics.bbox_largest_area_ratio:.3f}) "
                f"without localized text or color evidence. Likely background fill, "
                f"theme bleed, or scroll artifact."
            )
        why_not_owner_review = (
            "Large bbox without localized sub-evidence is not actionable for a human. "
            "Either improve bbox extraction (QA) or auto-ignore (render noise)."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 3: Strong structural or text evidence → PRODUCT_ACTIONABLE
    # Guardrail: if diff_summary says "No significant OCR difference" and
    # there is no real text pair, do NOT route to PRODUCT_ACTIONABLE even
    # if color/structural signals exist. Send to QA for verification.

    # Find the top_bbox analysis (same logic as _build_agent_package)
    top_bbox_analysis = None
    if bbox_analyses:
        for b, a in zip(bboxes, bbox_analyses):
            if not b.normalization_artifact:
                top_bbox_analysis = a
                break
        if top_bbox_analysis is None and bbox_analyses:
            top_bbox_analysis = bbox_analyses[0]

    # Find the bbox with the WORST real-text fuzzy ratio. Routing uses
    # `worst_fuzzy_real` across all bboxes, so ocr_contradicts_product must
    # be evaluated against that same bbox — otherwise a strong mismatch in
    # a secondary bbox is silenced by an innocuous top_bbox.
    worst_analysis = None
    if bbox_analyses:
        for a in bbox_analyses:
            if not a:
                continue
            if worst_analysis is None:
                worst_analysis = a
                continue
            if a.get("fuzzy_ratio_worst", 100) < worst_analysis.get("fuzzy_ratio_worst", 100):
                worst_analysis = a

    # has_real_text_pair is used inside _map_to_agent_route via the
    # _has_real_text_pair(bbox_analyses) call where needed; the local
    # variable was retained for symmetry with the original logic.
    _ = _has_real_text_pair(bbox_analyses)

    # ocr_contradicts_product: True when the evidence the routing would rely
    # on (worst real-text pair) is absent — i.e. neither top_bbox nor any
    # other bbox shows a real text mismatch. In that case, even if the
    # bbox-level worst_fuzzy is low due to OCR noise, the structural/color
    # signal is not backed by legible text and the surface should go to
    # QA_TOOLING, not PRODUCT.
    #
    # Owner guardrail (V3 amend — OCR-legibility rule): the pair we expose
    # to consumers is fuzzy_ratio_worst_pair, the worst line-to-line pair
    # inside a bbox. Validating only the bbox's full mockup_ocr/real_ocr
    # (which may aggregate multiple lines, some legible, some noise) is
    # insufficient: a bbox can contain 'NeuroMood / Configuración' on one
    # side and 'NeuroMood / Configuración' on the other (legible, pass)
    # while its fuzzy_ratio_worst_pair is OCR garbage (would fail). The
    # consumer reads the pair, not the full OCR; routing must mirror that.
    worst_pair = (worst_analysis or {}).get('fuzzy_ratio_worst_pair', ['', ''])
    worst_mockup_ocr = (worst_analysis or {}).get('mockup_ocr', '')
    worst_real_ocr = (worst_analysis or {}).get('real_ocr', '')
    # Pass condition: BOTH the bbox's aggregate OCR AND the reported
    # worst_pair must look like real text. If only one passes, the
    # evidence is mixed and the consumer cannot act on it.
    worst_bbox_legible = _looks_like_real_text_pair(worst_mockup_ocr, worst_real_ocr)
    worst_pair_legible = _looks_like_real_text_pair(
        (worst_pair or ['', ''])[0], (worst_pair or ['', ''])[1]
    )
    worst_has_real_pair = bool(
        worst_pair
        and worst_pair[0]
        and worst_pair[1]
        and worst_pair[0] != worst_pair[1]
        and worst_bbox_legible
        and worst_pair_legible
    )
    ocr_contradicts_product = not worst_has_real_pair

    # Case 3a guard: structural labels are surface-wide but the OCR
    # evidence we expose to consumers comes from the top_bbox only. To avoid
    # the case where labels=[EXTRA_COMPONENT] (surface) routes to PRODUCT
    # while text_evidence.diff_summary='No significant OCR difference' (top
    # bbox), we additionally require the top_bbox to carry some legible text
    # pair of its own. If the top_bbox has no real text pair, the structural
    # signal falls into the OCR-contradicts branch below.
    #
    # Same owner guardrail: validate the reported worst_pair directly. A
    # bbox with aggregate legible OCR but a worst_pair of pure noise
    # must NOT route to product.
    top_pair = (top_bbox_analysis or {}).get('fuzzy_ratio_worst_pair', ['', ''])
    top_bbox_legible = _looks_like_real_text_pair(
        (top_bbox_analysis or {}).get('mockup_ocr', ''),
        (top_bbox_analysis or {}).get('real_ocr', ''),
    )
    top_pair_legible = _looks_like_real_text_pair(
        (top_pair or ['', ''])[0], (top_pair or ['', ''])[1]
    )
    top_has_real_pair = bool(
        top_pair
        and top_pair[0]
        and top_pair[1]
        and top_pair[0] != top_pair[1]
        and top_bbox_legible
        and top_pair_legible
    )
    if (
        has_structural
        and confidence in ('high', 'medium')
        and not ocr_contradicts_product
        and top_has_real_pair
    ):
        agent_route = "PRODUCT_ACTIONABLE"
        agent_next_action = _build_product_action(
            classification, bbox_analyses, bboxes, metrics, manifest_entry
        )
        product_action_allowed = True
        why_not_owner_review = (
            "Structural evidence (missing/extra component) with sufficient confidence "
            "is actionable by an agent investigating the suspected module."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    if (
        has_real_text
        and worst_fuzzy_real < 70
        and confidence in ("high", "medium")
        and not ocr_contradicts_product
        and top_has_real_pair
    ):
        agent_route = "PRODUCT_ACTIONABLE"
        agent_next_action = _build_product_action(
            classification, bbox_analyses, bboxes, metrics, manifest_entry
        )
        product_action_allowed = True
        why_not_owner_review = (
            "Clear text mismatch with real OCR pair and sufficient confidence "
            "is actionable by an agent investigating font metrics, padding, or truncation."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 3b: Structural/color evidence but OCR contradicts → QA for verification
    if (has_structural or has_color) and confidence in ("high", "medium") and ocr_contradicts_product:
        agent_route = "QA_TOOLING_ACTIONABLE"
        agent_next_action = (
            f"Structural or color evidence detected (diagnostic_labels={diagnostic_labels}) "
            f"but OCR diff_summary='No significant OCR difference'. "
            f"Verify with tooling before claiming product action. "
            f"Investigate bbox extraction and crop quality."
        )
        qa_action_allowed = True
        why_not_owner_review = (
            "Structural/color evidence exists but OCR contradicts it. "
            "QA tooling should verify before product changes."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 3c: Auditor saw a real signal but the OCR pair is partial/imprecise.
    # The verdict is FIX_PRODUCT_REVIEW — there IS something to investigate.
    # Routing it to AUDITOR is inoperancia; send to QA_TOOLING with a concrete
    # next step: improve OCR preprocessing for this surface and rerun V3.
    has_aggregate_real_pair = _has_real_text_pair(bbox_analyses) if bbox_analyses else False
    if (
        classification.decision == "FIX_PRODUCT_REVIEW"
        and confidence in ("high", "medium")
        and (has_real_text or has_color or has_structural or has_aggregate_real_pair)
    ):
        agent_route = "QA_TOOLING_ACTIONABLE"
        diag_desc = (
            ",".join(diagnostic_labels[:3])
            if diagnostic_labels
            else (classification.labels[0] if classification.labels else "unknown")
        )
        agent_next_action = (
            f"Auditor flagged FIX_PRODUCT_REVIEW ({diag_desc}) with partial OCR evidence. "
            f"Improve OCR preprocessing (upscale, contrast, sharpen crops) for this surface "
            f"and rerun V3. If OCR still illegible after preprocessing, escalate to VLM."
        )
        qa_action_allowed = True
        product_action_allowed = False
        why_not_owner_review = (
            "Auditor saw a real signal but OCR evidence is partial. QA tooling "
            "should improve preprocessing and rerun before any product action."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 4: Weak text/color evidence → QA_TOOLING_ACTIONABLE
    if has_real_text and worst_fuzzy_real < 85 and confidence == "low":
        agent_route = "QA_TOOLING_ACTIONABLE"
        agent_next_action = (
            f"OCR detected possible text mismatch (worst_fuzzy={worst_fuzzy_real}) "
            f"but confidence is low. Improve OCR preprocessing (upscale, contrast, "
            f"sharpen) or split bboxes into smaller crops before claiming product action. "
            f"Current OCR may be noisy or partial."
        )
        qa_action_allowed = True
        why_not_owner_review = (
            "Weak text evidence should be strengthened by tooling improvements, "
            "not thrown to a human for visual inspection."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    if has_color and confidence == "low":
        agent_route = "QA_TOOLING_ACTIONABLE"
        agent_next_action = (
            "Color difference detected but confidence is low. "
            "Verify that the dominant-color crop is not a background fill region. "
            "If confirmed as component color, investigate QSS/palette."
        )
        qa_action_allowed = True
        why_not_owner_review = (
            "Low-confidence color signal needs tooling verification before product action."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 5: Chrome mismatch only → RENDER_NOISE_AUTO_IGNORED
    if "CHROME_MISMATCH" in labels and not any([
        has_real_text, has_color, has_structural
    ]):
        agent_route = "RENDER_NOISE_AUTO_IGNORED"
        agent_next_action = (
            "Differences are limited to window chrome, scrollbar, or titlebar areas. "
            "No product action needed."
        )
        why_not_owner_review = (
            "Chrome differences are expected capture variance, not product bugs."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 6: Pairing/capture issues
    if decision == "PAIRING_FIX" or not pairing.real_capture_path:
        agent_route = "CAPTURE_OR_PAIRING_ACTIONABLE"
        agent_next_action = (
            "Check capture pairing and normalized target path for this surface. "
            "Evidence suggests no meaningful product diff but capture structure "
            "may be misaligned."
        )
        capture_action_allowed = True
        why_not_owner_review = (
            "Capture/pairing issues are resolved by re-running capture pipeline, "
            "not by manual visual review."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 7: Render noise / no signal
    if metrics.changed_pixel_ratio < 0.05 and not has_real_text and not has_color and not has_structural:
        agent_route = "RENDER_NOISE_AUTO_IGNORED"
        agent_next_action = (
            "No product action. Differences are below threshold or limited to render noise."
        )
        why_not_owner_review = (
            "Pixel changes are minimal and no structural/text/color signal detected. "
            "Auto-ignore is safe."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 8: Real fallback — only when nothing else decided and the auditor
    # itself has no opinion. Legacy NEEDS_HUMAN_REVIEW with no signals means
    # the auditor's heuristic chain ended without a verdict; that IS an
    # auditor improvement task, not a product bug.
    if (
        classification.decision == "NEEDS_HUMAN_REVIEW"
        and not has_real_text
        and not has_color
        and not has_structural
        and not classification.suspected_module
        and metrics.changed_pixel_ratio >= 0.05
    ):
        agent_route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
        agent_next_action = (
            f"V3 could not classify this surface into a confident route. "
            f"Evidence: diagnostic_labels={diagnostic_labels}, "
            f"confidence={confidence}, worst_fuzzy={worst_fuzzy_real}. "
            f"Improve bbox extraction, OCR preprocessing, or add heuristic rules "
            f"for this surface pattern."
        )
        qa_action_allowed = True
        why_not_owner_review = (
            "Unclear signal is an auditor limitation, not a human task. "
            "The agent should improve V3 heuristics or tooling for this surface type."
        )
        return (
            agent_route, agent_next_action, evidence_quality, why_not_owner_review,
            diagnostic_labels, product_action_allowed, qa_action_allowed,
            capture_action_allowed,
        )

    # Case 9: Fallback when verdict was decided but routing missed all
    # branches. Should be rare. Points the agent at the routing gap.
    agent_route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
    agent_next_action = (
        f"V3 routed a {classification.decision} surface but matched no branch. "
        f"diagnostic_labels={diagnostic_labels}, has_real_text={has_real_text}, "
        f"has_color={has_color}, has_structural={has_structural}. "
        f"Add a routing rule for this pattern or improve the upstream classifier."
    )
    qa_action_allowed = True
    why_not_owner_review = "Routing gap. Improve V3 routing rules."
    return (
        agent_route, agent_next_action, evidence_quality, why_not_owner_review,
        diagnostic_labels, product_action_allowed, qa_action_allowed,
        capture_action_allowed,
    )


def _build_product_action(
    classification: Classification,
    bbox_analyses: list[dict],
    bboxes: list | None,
    metrics: Metrics,
    manifest_entry: dict,
) -> str:
    """Build a concrete, actionable next step for PRODUCT_ACTIONABLE.

    Uses the SAME bbox as agent_package.text_evidence (the top_bbox: first
    non-artifact, or first if all artifact). This keeps the action consistent
    with the evidence reported in the package — a downstream consumer should
    never see an action citing OCR/text from one bbox while text_evidence
    shows another.
    """
    parts: list[str] = []

    # Find the top_bbox analysis — same logic as _build_agent_package.
    top_bbox_analysis = None
    if bboxes and bbox_analyses:
        for b, a in zip(bboxes, bbox_analyses):
            if not b.normalization_artifact:
                top_bbox_analysis = a
                break
        if top_bbox_analysis is None and bbox_analyses:
            top_bbox_analysis = bbox_analyses[0]
    elif bbox_analyses:
        # No bbox metadata — fall back to first analysis
        top_bbox_analysis = bbox_analyses[0]

    best = top_bbox_analysis

    if best:
        pair = best.get("fuzzy_ratio_worst_pair", ["", ""])
        if pair and pair[0] and pair[1] and pair[0] != pair[1]:
            parts.append(
                f"OCR mismatch: '{pair[0]}' vs '{pair[1]}' "
                f"(fuzzy={best.get('fuzzy_ratio_worst', 0):.0f})"
            )
        color = best.get("color_delta", 0)
        if color > 30:
            m_rgb = best.get("mockup_color", (0, 0, 0))
            r_rgb = best.get("real_color", (0, 0, 0))
            parts.append(
                f"color delta={color} (mockup={_rgb_to_hex(m_rgb)} vs real={_rgb_to_hex(r_rgb)})"
            )
        pos = _describe_position(best.get("geometry", (0, 0, 0, 0)), manifest_entry)
        parts.append(f"position: {pos}")

    if classification.suspected_module:
        parts.append(f"suspected_module={classification.suspected_module}")

    if parts:
        return (
            f"Investigate the suspected module. Evidence suggests: "
            f"{'; '.join(parts)}. Confirm locally before changing product."
        )
    return (
        "Investigate the suspected module. Evidence suggests visual differences "
        "in the captured region. Confirm locally before changing product."
    )


def _cluster_root_cause(classification: Classification, bbox_analyses: list[dict], metrics: Metrics) -> str:
    """Cluster visual evidence into a small fixed vocabulary of root causes.
    Independent of agent_route.
    """
    labels = classification.labels or []
    explanation = classification.explanation or ""
    has_text_signal = "TEXT_MISMATCH" in labels or "text_mismatch=True" in explanation
    has_color_signal = "COLOR_MISMATCH" in labels or "color_mismatch=True" in explanation
    has_structural = (
        "MISSING_COMPONENT" in labels
        or "EXTRA_COMPONENT" in labels
        or "missing=True" in explanation
        or "extra=True" in explanation
    )
    real_text = _has_real_text_pair(bbox_analyses) if bbox_analyses else False

    if classification.decision == "RENDER_NOISE_OK" and metrics.changed_pixel_ratio < 0.05:
        return "render_noise"
    if has_text_signal and real_text:
        return "real_text_mismatch"
    if has_text_signal and not real_text:
        return "ocr_garbage"
    if has_color_signal and not has_text_signal:
        return "color_theme_bleed"
    if has_structural:
        return "structural_component"
    return "unknown"


def _divergences_from(bbox_analyses: list[dict], limit: int = 3) -> list[str]:
    """Top divergences from bbox analyses, sorted by worst fuzzy."""
    if not bbox_analyses:
        return []
    sorted_bas = sorted(bbox_analyses, key=lambda a: a.get("fuzzy_ratio_worst", 100) if a else 100)
    out: list[str] = []
    for a in sorted_bas[:limit]:
        if not a:
            continue
        pair = a.get("fuzzy_ratio_worst_pair") or ["", ""]
        if pair and len(pair) == 2 and pair[0] and pair[1] and pair[0] != pair[1]:
            out.append(f"text: '{pair[0]}' vs '{pair[1]}' (fuzzy={a.get('fuzzy_ratio_worst', 0):.0f})")
        color_delta = a.get("color_delta", 0) or 0
        if color_delta > 30:
            geom = a.get("geometry", (0, 0, 0, 0))
            out.append(f"color delta={color_delta:.0f} at bbox {geom}")
    return out


def _probable_module(surface_key: str) -> str:
    """Heuristic: derive probable module from surface_key.

    Examples:
        'suite:recuperar-acceso@light' -> 'suite.recuperar_acceso'
        'hub:detalle-plan-activacion@dark' -> 'hub.detalle_plan_activacion'
    """
    if not surface_key or ":" not in surface_key:
        return surface_key or "unknown"
    app = surface_key.split(":")[0]
    rest = surface_key.split(":", 1)[1]
    view = rest.split("@")[0]
    return f"{app}.{view.replace('-', '_')}"


def _next_action_for_agent(route: str, root_cause: str, divergences: list[str], module: str) -> str:
    """Concrete agent-facing next action for the given cluster."""
    if route == "NO_ACTION_NEEDED_WITH_EVIDENCE" or root_cause == "render_noise":
        return "No action. V3 verified visual stability (theme/chrome variance only)."
    if root_cause == "real_text_mismatch":
        first = divergences[0] if divergences else "text mismatch"
        return (
            f"Investigate {module}. Evidence: {first}. "
            "Likely font metrics, padding, or truncation. Confirm locally before changing product."
        )
    if root_cause == "ocr_garbage":
        return (
            f"Improve OCR preprocessing for {module} (upscale, contrast, sharpen crops). "
            "Current OCR is illegible; rerun V3 after fix or escalate to VLM."
        )
    if root_cause == "color_theme_bleed":
        return f"Inspect QSS/palette for {module}. Verify theme switching does not leak between surfaces."
    if root_cause == "structural_component":
        return f"Inspect {module} for missing/extra component. Compare against mockup reference."
    return "V3 could not classify this surface. Improve bbox extraction or add a heuristic rule for this surface pattern."


def _is_ocr_noise(text: str) -> bool:
    """Heuristic: OCR output is junk (symbols / no real words).

    Used to suppress TEXT_MISMATCH_PROBABLE on background-region bboxes
    that produce garbage OCR. A non-empty string with no letters or
    only very short non-alphanumeric tokens is considered noise.
    """
    if not text or not text.strip():
        return True
    # Strip out the OCR_ERROR sentinel
    if text.strip().startswith("[OCR_ERROR"):
        return True
    # Count alpha letters
    letters = sum(1 for ch in text if ch.isalpha())
    if letters < 3:
        return True
    # Ratio of non-alphanumeric to total length
    non_alnum = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
    if len(text) > 0 and non_alnum / max(len(text), 1) > 0.55:
        return True
    return False


def _looks_like_real_text_pair(mockup_ocr: str, real_ocr: str) -> bool:
    """Both OCR lines look like real text (not garbage) AND the pair is
    semantically comparable (shared language / script / shape).

    Used to decide if a low fuzzy_ratio is meaningful evidence or just OCR
    noise. Returns False when either side is noise, or when the two
    strings are too short / one-sided to support a TEXT_MISMATCH claim.
    """
    if _is_ocr_noise(mockup_ocr) or _is_ocr_noise(real_ocr):
        return False
    m = mockup_ocr.strip()
    r = real_ocr.strip()
    if not m or not r:
        return False
    # Both need at least one alphabetic word of length >= 3
    m_words = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}", m)]
    r_words = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}", r)]
    if not m_words or not r_words:
        return False
    # Avoid penalising pairs that are obviously different content (a digit
    # vs a word, a code vs a phrase, etc.) — require minimum overlap via
    # token-set Jaccard. If they share no tokens at all and the fuzzy
    # match is the only signal, treat as non-semantic.
    m_set = {w.lower() for w in m_words}
    r_set = {w.lower() for w in r_words}
    if not m_set or not r_set:
        return False
    overlap = len(m_set & r_set)
    if overlap == 0:
        # No shared tokens: maybe still legitimate (full sentence
        # replacement) but the audit flagged this as a source of false
        # positives. Require at least one shared short token OR a long
        # matching substring.
        common_substr = any(
            sub in r.lower()
            for token in m_set
            for sub in [token[:5]]
            if len(token) >= 5
        )
        if not common_substr:
            return False
    return True


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


def _ssim_fallback(a: np.ndarray, b: np.ndarray) -> float:
    """Lightweight SSIM proxy using luminance mean/stddev (numpy only).

    We avoid a hard dependency on scikit-image / scipy.signal. This is NOT
    the original Wang et al. SSIM (no windowed covariance, no SSIM map) —
    it's a single-number approximation: 1 - normalized absolute mean +
    stddev divergence. It is documented honestly in Metrics.ssim_method.
    Result is in [-1, 1]; we clamp to [0, 1].
    """
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    mu_a = float(a.mean())
    mu_b = float(b.mean())
    var_a = float(((a - mu_a) ** 2).mean())
    var_b = float(((b - mu_b) ** 2).mean())
    # Luminance + contrast/structure term, simplified
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    lum = (2.0 * mu_a * mu_b + c1) / (mu_a * mu_a + mu_b * mu_b + c1)
    cs = (2.0 * (var_a * var_b) ** 0.5 + c2) / (var_a + var_b + c2)
    ssim = float(lum * cs)
    return max(0.0, min(1.0, ssim))


def _compute_metrics(
    mockup_img: Image.Image,
    real_img: Image.Image,
    bboxes: list[BBoxInfo],
) -> Metrics:
    """Compute honest pixel-level metrics for a surface.

    Metrics policy (post-audit):
      * SSIM is computed using a luminance+contrast numpy fallback so the
        metric is never silently 0.0. The fallback is documented in
        Metrics.ssim_method.
      * mean_abs_diff, max_abs_diff, changed_pixel_ratio are computed
        from the actual pixel diff.
      * pHash is intentionally NOT computed — we don't depend on
        scipy.fftpack / imagehash and we don't want to ship a hand-rolled
        DCT that produces misleading "distance=0" claims. The
        phash_method field is set to "not_computed" and the value is
        -1. This is the audit fix #9 — we never present zeros as valid
        metrics, and we tell the consumer explicitly that pHash was
        skipped.
    """
    notes_parts: list[str] = []
    if mockup_img.size != real_img.size:
        # Resize for comparison only; do not save the resized image.
        real_for_diff = real_img.resize(
            mockup_img.size, Image.Resampling.LANCZOS
        )
        size_mismatch = True
        notes_parts.append("real capture resized to mockup size for diff")
    else:
        real_for_diff = real_img
        size_mismatch = False

    a = np.array(mockup_img.convert("L"), dtype=np.int16)
    b = np.array(real_for_diff.convert("L"), dtype=np.int16)
    abs_diff = np.abs(a - b)

    mean_abs = float(abs_diff.mean())
    max_abs = int(abs_diff.max())
    changed_ratio = float((abs_diff > 20).mean())

    ssim_val = _ssim_fallback(a.astype(np.float32), b.astype(np.float32))

    if bboxes:
        largest = bboxes[0]
        largest_area = largest.area_ratio
        largest_geom = list(largest.geometry)
    else:
        largest_area = 0.0
        largest_geom = []

    notes = "; ".join(notes_parts) if notes_parts else ""
    if size_mismatch:
        notes = (notes + "; " if notes else "") + "size_mismatch=true"

    return Metrics(
        ssim=round(ssim_val, 4),
        ssim_method="numpy_fallback_lum_cs",
        mean_abs_diff=round(mean_abs, 4),
        max_abs_diff=max_abs,
        changed_pixel_ratio=round(changed_ratio, 4),
        size_mismatch=size_mismatch,
        phash_distance=-1,
        phash_method="not_computed",
        bbox_count=len(bboxes),
        bbox_total_area_ratio=round(
            sum(b.area_ratio for b in bboxes), 4
        ),
        bbox_largest_area_ratio=round(largest_area, 4),
        bbox_largest_geometry=largest_geom,
        notes=notes,
    )


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
        "bbox_area_ratio": bbox.area_ratio,
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
    """Classify surface based on OCR + heuristics per bbox.

    Guardrails (post-audit):
      * if the largest bbox area_ratio > LARGEST_BBOX_GUARDRAIL without
        clear localized text evidence, classification becomes
        NEEDS_HUMAN_REVIEW with low confidence (fix #5). This avoids
        emitting FIX_PRODUCT_REVIEW from garbage OCR on huge background
        bboxes.
      * TEXT_MISMATCH_PROBABLE is suppressed when OCR lines are noise or
        the mockup/real pair is non-semantic (fix #6).
      * CHROME_MISMATCH coming from border-touching bboxes is downgraded
        to evidence-only — it does not push FIX_PRODUCT_REVIEW (fix #7).
      * COLOR_MISMATCH now requires the crop to be smaller than the
        whole-image bbox, otherwise it is treated as a background fill
        change and not flagged actionable (fix #8).
    """
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
        labels.append("RENDER_NOISE")
        return Classification(
            labels=labels,
            severity="low",
            explanation="All bboxes are normalization artifacts (pad/crop zones)",
            decision="RENDER_NOISE_OK",
            confidence="high",
            confidence_reason="all_bboxes_are_normalization_artifacts",
        )

    # Analyze non-artifact bboxes
    non_artifact_analyses = [
        a for b, a in zip(bboxes, bbox_analyses) if not b.normalization_artifact
    ]

    # Owner audit rule C: compute the REAL worst fuzzy across all non-artifact
    # bboxes (unfiltered). Used to verify decision_reason / confidence claims
    # against the actual text_evidence. This is independent of the
    # text_mismatch threshold (85) used to label TEXT_MISMATCH_PROBABLE.
    worst_fuzzy_real = _real_fuzzy_in_evidence(non_artifact_analyses)

    text_mismatch = False
    color_mismatch = False
    missing_component = False
    extra_component = False
    chrome_mismatch = False
    render_noise = True

    worst_fuzzy = 100
    worst_color_delta = 0
    worst_stddev_delta = 0
    largest_bbox_area = max((b.area_ratio for b in bboxes), default=0.0)
    biggest_bbox_dominates = largest_bbox_area > LARGEST_BBOX_GUARDRAIL

    # Count actionable evidence with guardrails applied per-bbox
    for analysis in non_artifact_analyses:
        area = analysis.get("bbox_area_ratio", 0.0)
        # Per-bbox: a single huge bbox can't drive text/colour decisions.
        # We treat it as render noise regardless of fuzzy ratio, unless
        # there's still clean localized text in BOTH crops.
        bbox_is_huge = area > LARGEST_BBOX_GUARDRAIL

        # ---- TEXT evidence (fix #5 + #6) ----
        if analysis["fuzzy_ratio_worst"] < 85 and analysis["fuzzy_ratio_worst_pair"][0]:
            if bbox_is_huge:
                # Huge bboxes (>35% of image) are almost always background fill.
                # If fuzzy is extremely low (<30) the OCR is garbage — skip entirely.
                # Only accept text mismatch from a huge bbox when the OCR pair
                # is clearly real text in both crops AND the fuzzy isn't noise-floor.
                if analysis["fuzzy_ratio_worst"] < 30:
                    # Garbage OCR on background — do not count as evidence
                    pass
                elif _looks_like_real_text_pair(
                    analysis["mockup_ocr"], analysis["real_ocr"]
                ):
                    text_mismatch = True
                    worst_fuzzy = min(worst_fuzzy, analysis["fuzzy_ratio_worst"])
            else:
                # Smaller bbox: still require the pair to look real
                if _looks_like_real_text_pair(
                    analysis["mockup_ocr"], analysis["real_ocr"]
                ):
                    text_mismatch = True
                    worst_fuzzy = min(worst_fuzzy, analysis["fuzzy_ratio_worst"])

        # ---- COLOR evidence (fix #8) ----
        if analysis["color_delta"] > 30:
            # Color from a giant bbox is just background fill or theme
            # bleed — not actionable. Require the crop to be small enough
            # to be a real component.
            if not bbox_is_huge:
                color_mismatch = True
                worst_color_delta = max(worst_color_delta, analysis["color_delta"])
            # else: ignore, it's a background fill change

        # ---- MISSING / EXTRA component ----
        if analysis["stddev_delta"] > 40:
            if not bbox_is_huge:
                if analysis["mockup_std"] > analysis["real_std"]:
                    missing_component = True
                else:
                    extra_component = True
                worst_stddev_delta = max(worst_stddev_delta, analysis["stddev_delta"])
            # else: huge bbox stddev delta is just background — ignore

        # ---- CHROME evidence (fix #7) ----
        if analysis["touches_borders"]:
            # Border-touching bboxes describe window chrome / scrollbar /
            # titlebar — they should be reported as evidence but never
            # push FIX_PRODUCT_REVIEW. We mark the label so downstream
            # agents can still see it, but the decision logic below
            # ignores chrome_mismatch when picking a decision.
            chrome_mismatch = True

        if analysis["fuzzy_ratio_worst"] < 100 or analysis["color_delta"] > 10:
            render_noise = False

    # Owner audit rule B (coherence): if the worst fuzzy across all
    # non-artifact bboxes is >= FUZZY_MATCH_THRESHOLD (95), there is no
    # text-based actionable evidence. Strip TEXT_MISMATCH_PROBABLE and
    # clear text_mismatch so the downstream decision logic doesn't claim
    # text-driven fixes.
    if worst_fuzzy_real >= FUZZY_MATCH_THRESHOLD:
        text_mismatch = False
        # Don't touch worst_fuzzy; let the confidence block reflect the
        # real evidence. But strip the label and disable text decisions.

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

    # Determine confidence — owner audit rule C: confidence_reason must
    # be consistent with the REAL worst fuzzy across all non-artifact
    # bboxes. The previous version said "OCR matches well" whenever
    # worst_fuzzy (the min-via-text_mismatch filter) was > 90, even when
    # other bboxes had fuzzy < 70. We now require worst_fuzzy_real >= 95
    # to claim "OCR matches well".
    if worst_fuzzy_real >= FUZZY_MATCH_THRESHOLD and not color_mismatch and not missing_component and not extra_component:
        confidence = "high"
        confidence_reason = (
            f"OCR matches well (worst_fuzzy_real={worst_fuzzy_real} "
            f">={FUZZY_MATCH_THRESHOLD}); no structural differences"
        )
    elif text_mismatch and worst_fuzzy < 85:
        confidence = "medium"
        confidence_reason = (
            f"OCR detected text mismatch (worst_fuzzy={worst_fuzzy}, "
            f"worst_fuzzy_real={worst_fuzzy_real})"
        )
    elif color_mismatch and worst_color_delta > 60:
        confidence = "medium"
        confidence_reason = f"Color mismatch detected (delta={worst_color_delta})"
    elif worst_fuzzy_real >= FUZZY_MATCH_THRESHOLD:
        confidence = "high"
        confidence_reason = (
            f"OCR matches well (worst_fuzzy_real={worst_fuzzy_real} "
            f">={FUZZY_MATCH_THRESHOLD}); no structural differences"
        )
    else:
        confidence = "low"
        confidence_reason = (
            f"No strong textual or color evidence "
            f"(worst_fuzzy_real={worst_fuzzy_real}, worst_fuzzy={worst_fuzzy})"
        )

    # Determine severity
    if text_mismatch or missing_component or extra_component:
        severity = "high"
    elif color_mismatch:
        severity = "medium"
    else:
        severity = "low"

    # Guardrail #5: largest bbox dominates — this is almost certainly a background
    # fill / theme bleed / scroll artifact. The OCR on a >35% bbox is unreliable.
    # Force low confidence + human review regardless of other bboxes.
    if biggest_bbox_dominates:
        confidence = "low"
        confidence_reason = (
            f"largest_bbox_area_ratio={largest_bbox_area:.3f} "
            f">{LARGEST_BBOX_GUARDRAIL}; background-dominated image — "
            "OCR unreliable on oversized region"
        )
        # Owner audit rule C: also strip TEXT_MISMATCH_PROBABLE and
        # COLOR_MISMATCH from labels when bbox dominates — those came
        # from noisy background diffs, not from a real component diff.
        labels = [
            lbl for lbl in labels
            if lbl not in ("TEXT_MISMATCH_PROBABLE", "COLOR_MISMATCH")
        ]
        # Avoid producing FIX_PRODUCT_STRONG/REVIEW from this signal.
        # Return a neutral decision; _map_to_agent_route will route based on
        # biggest_bbox_dominates + evidence quality.
        decision = "RENDER_NOISE_OK"
        return Classification(
            labels=labels,
            severity="low",
            explanation=(
                f"largest_bbox_dominates={biggest_bbox_dominates}; "
                "insufficient localized evidence for product action"
            ),
            decision=decision,
            confidence=confidence,
            confidence_reason=confidence_reason,
        )

    # Determine decision (chrome_mismatch is intentionally excluded — fix #7)
    actionable_structural = missing_component or extra_component
    actionable_text = text_mismatch and worst_fuzzy < 70
    actionable_text_review = text_mismatch and worst_fuzzy < 85
    actionable_color_review = color_mismatch and worst_color_delta > 60

    if confidence == "high" and (actionable_structural or actionable_text):
        decision = "FIX_PRODUCT_STRONG"
    elif confidence == "medium" and (actionable_text_review or actionable_color_review):
        decision = "FIX_PRODUCT_REVIEW"
    elif render_noise and not any([text_mismatch, color_mismatch, missing_component, extra_component]):
        decision = "RENDER_NOISE_OK"
    else:
        # V3 reorientation: no NEEDS_HUMAN_REVIEW. Use a neutral decision
        # that _map_to_agent_route will interpret based on evidence.
        decision = "RENDER_NOISE_OK"

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
    metrics: Metrics,
    pairing: Pairing,
) -> AgentPackage:
    """Build agent_package.json with text + color evidence + agent route."""
    # Compute agent route before constructing the package
    biggest_bbox_dominates = metrics.bbox_largest_area_ratio > LARGEST_BBOX_GUARDRAIL
    all_artifacts = all(b.normalization_artifact for b in bboxes) if bboxes else False
    (
        agent_route,
        agent_next_action,
        evidence_quality,
        why_not_owner_review,
        diagnostic_labels,
        product_action_allowed,
        qa_action_allowed,
        capture_action_allowed,
    ) = _map_to_agent_route(
        classification, bboxes, bbox_analyses, metrics, manifest_entry,
        biggest_bbox_dominates, all_artifacts, pairing,
    )

    pkg = AgentPackage(
        surface_key=surface_key,
        decision=classification.decision,
        decision_reason=classification.confidence_reason,
        labels=classification.labels,
        severity=classification.severity,
        confidence=classification.confidence,
        agent_route=agent_route,
        agent_next_action=agent_next_action,
        requires_owner_review=False,
        why_not_owner_review=why_not_owner_review,
        evidence_quality=evidence_quality,
        diagnostic_labels=diagnostic_labels,
        product_action_allowed=product_action_allowed,
        qa_action_allowed=qa_action_allowed,
        capture_action_allowed=capture_action_allowed,
    )
    # diff_summary is computed later when text_evidence is built; placeholder
    # for now (filled after the top_bbox block).

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
            # Mirror top_bbox diff_summary at package top level so consumers
            # of agent_package.json can see what OCR conclusion drove the
            # routing without diving into text_evidence.
            pkg.diff_summary = pkg.text_evidence.diff_summary

    pkg.suspected_module = _guess_module(surface_key)
    pkg.suspected_lines_hint = _guess_lines_hint(surface_key, classification.labels)
    pkg.what_to_check_first = _what_to_check(classification, bbox_analyses)
    pkg.do_not_touch_if = "confidence == 'low' OR no TEXT_MISMATCH detected"

    if manifest_entry.get("review_required"):
        pkg.normalization_warning = (
            f"review_required=true: {manifest_entry.get('review_reason', '')}"
        )

    # Actionable evidence — concrete per-surface payload for downstream agents.
    root_cause = _cluster_root_cause(classification, bbox_analyses, metrics)
    divergences = _divergences_from(bbox_analyses)
    module = _probable_module(surface_key)
    base_action = _next_action_for_agent(agent_route, root_cause, divergences, module)
    if agent_route == "QA_TOOLING_ACTIONABLE" and root_cause == "real_text_mismatch":
        next_act = (
            f"Tooling step: improve OCR preprocessing for {module} "
            "(upscale, contrast, sharpen crops) and rerun V3 before any "
            f"product investigation. If OCR still illegible, escalate to VLM. "
            f"Underlying signal: {base_action}"
        )
    else:
        next_act = base_action
    real_signals: list[str] = []
    for ba in bbox_analyses[:3]:
        if not ba:
            continue
        geom = ba.get("geometry", (0, 0, 0, 0))
        real_signals.append(
            f"bbox@{geom} fuzzy={ba.get('fuzzy_ratio_worst', 100):.0f} "
            f"color_delta={ba.get('color_delta', 0):.0f}"
        )
    pkg.actionable_evidence = ActionableEvidence(
        divergences=divergences,
        probable_module=module,
        probable_root_cause=root_cause,
        real_visual_signals=real_signals,
        next_action=next_act,
        evidence_strength=evidence_quality,
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
    """Build a concrete, actionable hint for the agent.

    Owner audit rule E: what_to_check_first MUST NOT be generic. If we
    can only produce a generic phrase for a FIX_PRODUCT_* decision, the
    decision must be downgraded to NEEDS_HUMAN_REVIEW by the caller.
    """
    # Pick the best (most informative) bbox analysis. Strategy:
    # 1. For FIX_PRODUCT_* on COLOR_MISMATCH, prefer the bbox with
    #    highest color_delta (that's the one driving the decision).
    # 2. For other cases, prefer the bbox with the lowest fuzzy_ratio_worst
    #    (most interesting text evidence).
    best = None
    if "COLOR_MISMATCH" in classification.labels and classification.decision in (
        "FIX_PRODUCT_STRONG", "FIX_PRODUCT_REVIEW"
    ):
        for a in bbox_analyses:
            if not a:
                continue
            if best is None:
                best = a
                continue
            if a.get("color_delta", 0) > best.get("color_delta", 0):
                best = a
    else:
        for a in bbox_analyses:
            if not a:
                continue
            if best is None:
                best = a
                continue
            if a.get("fuzzy_ratio_worst", 100) < best.get("fuzzy_ratio_worst", 100):
                best = a

    if classification.decision == "RENDER_NOISE_OK":
        return "No action needed — differences are render noise"

    if classification.decision in ("FIX_PRODUCT_STRONG", "FIX_PRODUCT_REVIEW"):
        parts: list[str] = []
        if best:
            pair = best.get("fuzzy_ratio_worst_pair", ["", ""])
            if pair and pair[0] and pair[1] and pair[0] != pair[1]:
                parts.append(
                    f"OCR mismatch: '{pair[0]}' vs '{pair[1]}' "
                    f"(fuzzy={best.get('fuzzy_ratio_worst', 0):.0f})"
                )
            elif pair and pair[0]:
                parts.append(
                    f"OCR matched line: '{pair[0]}' "
                    f"(fuzzy={best.get('fuzzy_ratio_worst', 0):.0f})"
                )
            color = best.get("color_delta", 0)
            if color > 30:
                m_rgb = best.get("mockup_color", (0, 0, 0))
                r_rgb = best.get("real_color", (0, 0, 0))
                m_hex = _rgb_to_hex(m_rgb)
                r_hex = _rgb_to_hex(r_rgb)
                parts.append(
                    f"color delta={color} (mockup={m_hex} vs real={r_hex})"
                )
            if best.get("touches_borders"):
                parts.append("bbox touches window border (chrome)")
            area = best.get("bbox_area_ratio", 0.0)
            if area > 0:
                parts.append(f"top_bbox area_ratio={area:.3f}")
        if classification.labels:
            parts.append("labels=" + ",".join(classification.labels))
        if classification.suspected_module:
            parts.append(f"suspected={classification.suspected_module}")
        if parts:
            return "; ".join(parts)
        # Fallback: still actionable, includes labels + confidence
        return (
            f"Inspect: decision={classification.decision}, "
            f"confidence={classification.confidence}, "
            f"labels={','.join(classification.labels)}"
        )

    # NEEDS_HUMAN_REVIEW or PAIRING_FIX — must be concrete about WHY
    # review is needed, not generic.
    parts_nhr: list[str] = []
    if best:
        worst_fuzzy = int(best.get("fuzzy_ratio_worst", 100))
        if worst_fuzzy < FUZZY_NOISE_THRESHOLD:
            parts_nhr.append(
                f"OCR noise on this surface (worst_fuzzy={worst_fuzzy}); "
                "capture diff likely too small for clean OCR"
            )
        elif worst_fuzzy < FUZZY_MATCH_THRESHOLD:
            pair = best.get("fuzzy_ratio_worst_pair", ["", ""])
            if pair and pair[0] and pair[1] and pair[0] != pair[1]:
                parts_nhr.append(
                    f"OCR diff between '{pair[0]}' and '{pair[1]}' but no "
                    "real-text pair confirmed (different content/units); "
                    "human review needed to disambiguate"
                )
        area = best.get("bbox_area_ratio", 0.0)
        if area > LARGEST_BBOX_GUARDRAIL:
            parts_nhr.append(
                f"bbox too broad (area_ratio={area:.3f} "
                f">{LARGEST_BBOX_GUARDRAIL}); no localized actionable "
                "evidence"
            )
    if not parts_nhr:
        parts_nhr.append(
            f"Insufficient localized evidence (confidence="
            f"{classification.confidence}, labels="
            f"{','.join(classification.labels)})"
        )
    return "; ".join(parts_nhr)


def _enforce_decision_guardrails(
    surface_key: str,
    classification: Classification,
    agent_pkg: AgentPackage,
    bbox_analyses: list[dict],
    fidelity_available: bool,
) -> tuple[Classification, AgentPackage]:
    """Final coherence guardrails (owner audit rules A-F) + agent-route guarantee.

    Called at the end of agent_package construction. Mutates and
    returns both objects with consistent fields. Key change for V3
    reorientation: we NEVER downgrade to NEEDS_HUMAN_REVIEW. Instead,
    we map to AUDITOR_IMPROVEMENT_ACTIONABLE when evidence is weak.
    requires_owner_review is ALWAYS False.
    """
    cls = classification
    pkg = agent_pkg
    diff_summary = pkg.text_evidence.diff_summary if pkg.text_evidence else ""
    fuzzy_worst = (
        int(pkg.text_evidence.fuzzy_ratio_worst)
        if pkg.text_evidence else 100
    )

    # Guarantee: requires_owner_review is always False
    pkg.requires_owner_review = False  # type: ignore[attr-defined]

    # Rule 7: fidelity_available flag (informational; not a downgrade)
    pkg.fidelity_available = fidelity_available  # type: ignore[attr-defined]

    # Rule 1 (reoriented): confidence == low => map to AUDITOR_IMPROVEMENT_ACTIONABLE
    # instead of NEEDS_HUMAN_REVIEW. The agent_route already handles this,
    # but we enforce it here as a hard guardrail.
    if cls.confidence == "low":
        if pkg.agent_route not in (
            "RENDER_NOISE_AUTO_IGNORED",
            "NO_ACTION_NEEDED_WITH_EVIDENCE",
            "CAPTURE_OR_PAIRING_ACTIONABLE",
        ):
            pkg.agent_route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
            pkg.agent_next_action = (
                f"Confidence is low ({cls.confidence}). V3 heuristics are "
                f"insufficient for this surface. Improve bbox extraction, "
                f"OCR preprocessing, or add surface-specific rules. "
                f"diagnostic_labels={pkg.diagnostic_labels}"
            )
            pkg.qa_action_allowed = True
            pkg.product_action_allowed = False

    # Rule 2: fuzzy_ratio_worst >= 95 forbids TEXT_MISMATCH and text-decisions
    if fuzzy_worst >= FUZZY_MATCH_THRESHOLD:
        if "TEXT_MISMATCH_PROBABLE" in cls.labels:
            cls.labels = [lbl for lbl in cls.labels if lbl != "TEXT_MISMATCH_PROBABLE"]
        # If agent_route is PRODUCT_ACTIONABLE driven by text, downgrade to QA
        if pkg.agent_route == "PRODUCT_ACTIONABLE" and not any(
            lbl in cls.labels for lbl in ("MISSING_COMPONENT", "EXTRA_COMPONENT", "COLOR_MISMATCH")
        ):
            pkg.agent_route = "QA_TOOLING_ACTIONABLE"
            pkg.agent_next_action = (
                "OCR fuzzy ratio >= 95 indicates text matches well. "
                "Product action driven by text is not justified. "
                "Verify with tooling or investigate structural evidence."
            )
            pkg.product_action_allowed = False
            pkg.qa_action_allowed = True

    # Rule 3: diff_summary == "No significant OCR difference"
    if diff_summary.strip() == "No significant OCR difference":
        if "TEXT_MISMATCH_PROBABLE" in cls.labels:
            cls.labels = [lbl for lbl in cls.labels if lbl != "TEXT_MISMATCH_PROBABLE"]
        # If agent_route is PRODUCT_ACTIONABLE and only text evidence, downgrade
        if pkg.agent_route == "PRODUCT_ACTIONABLE" and not any(
            lbl in cls.labels for lbl in ("MISSING_COMPONENT", "EXTRA_COMPONENT", "COLOR_MISMATCH")
        ):
            pkg.agent_route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
            pkg.agent_next_action = (
                "diff_summary='No significant OCR difference' contradicts "
                "PRODUCT_ACTIONABLE. No text evidence to support product change. "
                "Improve heuristics or verify with structural/color evidence."
            )
            pkg.product_action_allowed = False
            pkg.qa_action_allowed = True

    # Rule 4: decision_reason "OCR matches well" while fuzzy < 85 somewhere
    if pkg.decision_reason and "OCR matches well" in pkg.decision_reason:
        worst_real = _real_fuzzy_in_evidence(bbox_analyses)
        if worst_real < FUZZY_MATCH_THRESHOLD:
            pkg.decision_reason = (
                f"confidence_reason inconsistent with text_evidence "
                f"(worst_fuzzy_real={worst_real}); see text_evidence"
            )
            cls.confidence_reason = pkg.decision_reason

    # Rule 5: FIX_PRODUCT_STRONG requires confidence == high
    # (kept for internal compat; agent_route is the operational output)
    if cls.decision == "FIX_PRODUCT_STRONG" and cls.confidence != "high":
        if cls.confidence == "medium":
            cls.decision = "FIX_PRODUCT_REVIEW"
        else:
            cls.decision = "NEEDS_HUMAN_REVIEW"
            cls.severity = "needs_review"

    # Rule 6: FIX_PRODUCT_* with generic what_to_check_first => downgrade
    if cls.decision in ("FIX_PRODUCT_STRONG", "FIX_PRODUCT_REVIEW"):
        if _is_generic_phrase(pkg.what_to_check_first):
            cls.decision = "NEEDS_HUMAN_REVIEW"
            cls.severity = "needs_review"
            cls.explanation = (
                (cls.explanation or "")
                + "; downgraded by guardrail: generic what_to_check_first "
                "forbids FIX_PRODUCT_*"
            ).strip("; ")

    # Mirror decision back into agent package (decision_reason kept as
    # set in rule 4 or original from classification).
    pkg.decision = cls.decision
    pkg.severity = cls.severity
    pkg.labels = list(cls.labels)

    # Final guarantee: if agent_route is still somehow NEEDS_HUMAN_REVIEW
    # (should never happen), force it to AUDITOR_IMPROVEMENT_ACTIONABLE
    if pkg.agent_route not in AGENT_ROUTES:
        pkg.agent_route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
        pkg.agent_next_action = (
            "V3 produced an unrecognized agent_route. Fallback to "
            "AUDITOR_IMPROVEMENT_ACTIONABLE. Improve heuristics for this surface."
        )
        pkg.qa_action_allowed = True
        pkg.product_action_allowed = False

    return cls, pkg


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
    safe_surface_key = _safe_folder_name(surface_key)
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
            labels=["PAIRING_OR_CAPTURE_MISMATCH"],
            severity="low",
            explanation=f"unreliable=true: {unreliable_reason}",
            decision="PAIRING_FIX",
            confidence="low",
            confidence_reason=f"unreliable: {unreliable_reason}",
        )
        agent_pkg = AgentPackage(
            surface_key=surface_key,
            decision="PAIRING_FIX",
            decision_reason=f"unreliable=true: {unreliable_reason}",
            labels=["PAIRING_OR_CAPTURE_MISMATCH"],
            severity="low",
            confidence="low",
            agent_route="CAPTURE_OR_PAIRING_ACTIONABLE",
            agent_next_action=(
                f"Capture or pairing issue: {unreliable_reason}. "
                f"Check that the capture exists and is not blank/corrupt. "
                f"Re-run capture pipeline if needed."
            ),
            requires_owner_review=False,
            why_not_owner_review=(
                "Missing/corrupt capture is a pipeline issue, not a human review task."
            ),
            evidence_quality="none",
            diagnostic_labels=["PAIRING_OR_CAPTURE_ISSUE"],
            capture_action_allowed=True,
        )
        # Unreliable paths also get classification.json + metrics.json so
        # every per-surface dir on disk contains the same 3 canonical files
        # (agent_package, classification, metrics). Metrics is a placeholder
        # because we never computed it.
        placeholder_metrics = Metrics()
        result = {
            "pairing": asdict(pairing),
            "metrics": asdict(placeholder_metrics),
            "classification": asdict(classification),
            "agent_package": asdict(agent_pkg),
        }
        (surface_out / "metrics.json").write_text(
            json.dumps(asdict(placeholder_metrics), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (surface_out / "classification.json").write_text(
            json.dumps(asdict(classification), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
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

    # Metrics — computed honestly from the actual pixels + bbox list.
    # pHash is intentionally not computed; SSIM uses a documented
    # numpy fallback. See _compute_metrics docstring for the audit note.
    metrics = _compute_metrics(mockup_img, real_img, bboxes)

    # Classification
    classification = _classify_surface(
        bboxes, bbox_analyses, manifest_entry, metrics, unreliable, unreliable_reason
    )

    # Agent package
    agent_pkg = _build_agent_package(
        surface_key, classification, bboxes, bbox_analyses, manifest_entry, metrics, pairing
    )

    # Owner audit rule A+F: enforce decision coherence and stamp
    # fidelity_available. Fidelity must be computed BEFORE this call.
    fidelity_available = _check_fidelity_available()
    classification, agent_pkg = _enforce_decision_guardrails(
        surface_key, classification, agent_pkg, bbox_analyses, fidelity_available
    )

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


def _reset_latest_outputs() -> None:
    """Wipe per-surface outputs and stale top-level artifacts so a fresh
    `analyze --all` run starts from a known-clean state.

    Removes:
      * qa/_visual_auditor_v3/latest/surfaces/  (every per-surface dir)
      * qa/_visual_auditor_v3/latest/report.json (rebuilt by analyze)
      * qa/_visual_auditor_v3/latest/queue.md    (rebuilt by build_queue)
      * qa/_visual_auditor_v3/latest/index.html  (rebuilt by generate_html)

    The cache directory is left untouched — it is governed by
    `clear-cache` and by per-surface staleness rules, not by this reset.
    Historical snapshots should be stored outside `latest/`.
    """
    surfaces_dir = _OUT_DIR / "surfaces"
    if surfaces_dir.exists():
        for child in surfaces_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink(missing_ok=True)
    for top in ("report.json", "queue.md", "index.html"):
        target = _OUT_DIR / top
        if target.exists():
            target.unlink()


def _safe_folder_name(surface_key: str) -> str:
    """Sanitize a surface_key into a safe filesystem/URL folder name.

    Mirrors the same transform used by analyze_surface() when it creates
    the per-surface output directory. Used by the HTML report so links
    resolve on Windows (colons in 'C:' would break file:// URLs).
    """
    return surface_key.replace(":", "_").replace("@", "_")


def generate_html(results: list[dict], out_path: Path) -> None:
    """Generate navigable HTML report with agent-facing output."""
    rows = []
    for r in results:
        pkg = r.get("agent_package", {})
        agent_route = pkg.get("agent_route", "AUDITOR_IMPROVEMENT_ACTIONABLE")
        evidence_quality = pkg.get("evidence_quality", "weak")
        requires_owner_review = pkg.get("requires_owner_review", False)
        diagnostic_labels = ", ".join(pkg.get("diagnostic_labels", []))
        surface_key = pkg.get("surface_key", "")
        safe_folder = _safe_folder_name(surface_key)
        # Color-code by agent_route
        route_class = agent_route.lower().replace("_", "-")
        rows.append(
            f"""
        <tr class="route-{route_class}">
            <td>{surface_key}</td>
            <td>{agent_route}</td>
            <td>{evidence_quality}</td>
            <td>{'YES' if requires_owner_review else 'NO'}</td>
            <td>{diagnostic_labels}</td>
            <td>{pkg.get('agent_next_action', '')}</td>
            <td><a href="surfaces/{safe_folder}/agent_package.json">agent_package</a></td>
        </tr>"""
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Visual Auditor V3 Report</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
        th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; vertical-align: top; }}
        th {{ background: #f0f0f0; }}
        .route-product-actionable {{ background: #ffcccc; }}
        .route-qa-tooling-actionable {{ background: #ffffcc; }}
        .route-capture-or-pairing-actionable {{ background: #ccffff; }}
        .route-auditor-improvement-actionable {{ background: #ffccff; }}
        .route-render-noise-auto-ignored {{ background: #ccffcc; }}
        .route-no-action-needed-with-evidence {{ background: #e0e0e0; }}
        td:nth-child(6) {{ max-width: 400px; word-wrap: break-word; }}
    </style>
</head>
<body>
    <h1>Visual Auditor V3 Report</h1>
    <p>Total surfaces: {len(results)}</p>
    <p><strong>No surface requires owner review.</strong></p>
    <table>
        <tr><th>Surface</th><th>Agent Route</th><th>Evidence Quality</th><th>Owner Review?</th><th>Diagnostic Labels</th><th>Next Action</th><th>Link</th></tr>
        {''.join(rows)}
    </table>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


def build_queue(results: list[dict]) -> str:
    """Build operational queue markdown grouped by agent_route.

    V3 reorientation: queue is no longer a prioritized list of
    'things to review'. It is a set of actionable sections for agents.
    """
    # Group by agent_route
    groups: dict[str, list[dict]] = {
        "PRODUCT_ACTIONABLE": [],
        "QA_TOOLING_ACTIONABLE": [],
        "CAPTURE_OR_PAIRING_ACTIONABLE": [],
        "AUDITOR_IMPROVEMENT_ACTIONABLE": [],
        "RENDER_NOISE_AUTO_IGNORED": [],
        "NO_ACTION_NEEDED_WITH_EVIDENCE": [],
    }
    for r in results:
        pkg = r.get("agent_package", {})
        route = pkg.get("agent_route", "AUDITOR_IMPROVEMENT_ACTIONABLE")
        if route not in groups:
            route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
        groups[route].append(r)

    lines: list[str] = ["# Visual Auditor V3 — Operational Queue\n"]
    lines.append("> Every surface below has an actionable route for agents. ")
    lines.append("> No surface requires owner review.\n"
    )

    section_titles = {
        "PRODUCT_ACTIONABLE": "# Product Action Queue",
        "QA_TOOLING_ACTIONABLE": "# QA/Tooling Action Queue",
        "CAPTURE_OR_PAIRING_ACTIONABLE": "# Capture/Pairing Queue",
        "AUDITOR_IMPROVEMENT_ACTIONABLE": "# Auditor Improvement Queue",
        "RENDER_NOISE_AUTO_IGNORED": "# Auto-Ignored Render Noise",
        "NO_ACTION_NEEDED_WITH_EVIDENCE": "# No Action Needed",
    }

    for route in [
        "PRODUCT_ACTIONABLE",
        "QA_TOOLING_ACTIONABLE",
        "CAPTURE_OR_PAIRING_ACTIONABLE",
        "AUDITOR_IMPROVEMENT_ACTIONABLE",
        "RENDER_NOISE_AUTO_IGNORED",
        "NO_ACTION_NEEDED_WITH_EVIDENCE",
    ]:
        items = groups[route]
        lines.append(section_titles[route])
        lines.append(f"Count: {len(items)}\n")
        if not items:
            lines.append("_No surfaces in this category._\n")
            continue
        for r in items:
            pkg = r.get("agent_package", {})
            cls = r.get("classification", {})
            lines.append(
                f"- **{pkg.get('surface_key', '')}** | "
                f"evidence_quality={pkg.get('evidence_quality', 'weak')} | "
                f"confidence={cls.get('confidence', 'low')}"
            )
            if pkg.get("diagnostic_labels"):
                lines.append(
                    f"  - diagnostic_labels={', '.join(pkg['diagnostic_labels'])}"
                )
            if pkg.get("agent_next_action"):
                lines.append(f"  - agent_next_action: {pkg['agent_next_action']}")
            if pkg.get("requires_owner_review"):
                lines.append(
                    "  - **WARNING: requires_owner_review=True** "
                    "(this should never happen)"
                )
        lines.append("")

    # Summary stats
    total = len(results)
    owner_review_count = sum(
        1 for r in results if r.get("agent_package", {}).get("requires_owner_review", False)
    )
    lines.append("## Summary")
    lines.append(f"- Total surfaces: {total}")
    lines.append(f"- Requires owner review: {owner_review_count}")
    for route, items in groups.items():
        lines.append(f"- {route}: {len(items)}")
    lines.append("")

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

    # 3. Fidelity report (optional, warn only) — validate it has real comparisons,
    # not an empty shell. Windows-safe read with errors='replace'.
    if not _FIDELITY_REPORT.exists():
        print("[WARN] qa/_fidelity_current/FIDELITY_REPORT.json — run diff_fidelity.py")
    else:
        try:
            fidelity_text = _FIDELITY_REPORT.read_text(encoding="utf-8", errors="replace")
            fidelity_data = json.loads(fidelity_text)
            # Handle both dict-shaped and list-shaped reports
            if isinstance(fidelity_data, list):
                comparisons = fidelity_data
            elif isinstance(fidelity_data, dict):
                comparisons = fidelity_data.get("comparisons", [])
            else:
                comparisons = []
            if not comparisons:
                print(
                    "[WARN] FIDELITY_REPORT.json exists but has no comparisons "
                    "— regenerate via diff_fidelity.py"
                )
            else:
                print(
                    f"[OK] Fidelity report exists ({len(comparisons)} comparisons)"
                )
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] FIDELITY_REPORT.json could not be parsed: {e}")

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

    # 8. Output dir gitignored (Windows-safe read: explicit utf-8 with replace)
    gitignore = _PROJ / ".gitignore"
    try:
        gitignore_text = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""
    except OSError:
        gitignore_text = ""
    if gitignore.exists() and "qa/_visual_auditor_v3/" in gitignore_text:
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
    analyze_parser.add_argument("--quiet", action="store_true", help="Suppress per-surface stdout; only summary at end.")
    analyze_parser.add_argument("--resume", action="store_true", help="Skip surfaces already in .hermes/qa_progress.json.")
    analyze_parser.add_argument("--log-file", type=Path, default=None, help="Append per-surface status to this file.")

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

        # Load manifest lookup. Derive app from surface_key (no separate
        # 'app' field on entries). Index by both canonical surface_key and
        # the colon-theme alias for tolerant --surface lookups.
        manifest_items = _load_norm_manifest()
        manifest_lookup: dict[str, dict] = {}
        for item in manifest_items:
            sk = item.get("surface_key", "")
            if sk:
                manifest_lookup[sk] = item
                manifest_lookup[_normalize_surface_alias(sk)] = item

        pairings = pair_surfaces()
        if args.surface:
            # Accept both canonical ('suite:avisos@light') and the
            # colon-theme alias ('suite:avisos-search:light') forms.
            requested = _normalize_surface_alias(args.surface)
            pairings = [p for p in pairings if p.surface_key == requested]
            if not pairings:
                print(
                    f"Surface not found: {args.surface} "
                    f"(normalized: {requested}). Use canonical 'app:view@theme'."
                )
                return 1

        _OUT_DIR.mkdir(parents=True, exist_ok=True)

        # Clean stale per-surface outputs so report.json, surfaces/ and
        # queue.md/index.html stay in sync. Without this, dirs from a
        # previous run (e.g. an older taxonomy) leak through and inflate
        # the surface count beyond what report.json contains. Only run
        # the cleanup when --all is requested; --surface is incremental.
        if args.all:
            _reset_latest_outputs()

        results: list[dict] = []

        # --- Batch mode setup: progress + log + quiet ---
        progress_path = Path(".hermes") / "qa_progress.json"
        done: set[str] = set()
        if args.resume and progress_path.exists():
            try:
                done = set(json.loads(progress_path.read_text(encoding="utf-8")).get("done", []))
            except Exception:
                done = set()

        log_fp = None
        if args.log_file:
            args.log_file.parent.mkdir(parents=True, exist_ok=True)
            log_fp = open(args.log_file, "a", encoding="utf-8")

        if log_fp:
            log_fp.write(
                f"[{datetime.now().isoformat()}] === analyze started (quiet={args.quiet}, resume={args.resume}) ===\n"
            )
            log_fp.flush()

        def _emit(msg: str) -> None:
            if not args.quiet:
                print(msg)
            if log_fp:
                log_fp.write(f"[{datetime.now().isoformat()}] {msg}\n")
                log_fp.flush()

        surfaces_to_analyze = [p.surface_key for p in pairings]

        try:
            for pairing in pairings:
                surface_key = pairing.surface_key
                if args.resume and surface_key in done:
                    _emit(f"[skip] {surface_key} (already done)")
                    continue
                _emit(f"Analyzing {surface_key}...")
                try:
                    result = analyze_surface(pairing, _OUT_DIR, manifest_lookup)
                    results.append(result)
                    if args.resume:
                        done.add(surface_key)
                        progress_path.parent.mkdir(parents=True, exist_ok=True)
                        progress_path.write_text(
                            json.dumps({"done": sorted(done), "updated_at": datetime.now().isoformat() + "Z"}, indent=2),
                            encoding="utf-8",
                        )
                    _emit(f"[OK] {surface_key}")
                except Exception as e:
                    _emit(f"[FAIL] {surface_key}: {e}")
                    if not args.resume:
                        raise
                    continue
        finally:
            if log_fp:
                log_fp.write(
                    f"[{datetime.now().isoformat()}] === analyze finished ({len(results)}/{len(surfaces_to_analyze)} completed) ===\n"
                )
                log_fp.flush()
                log_fp.close()

        print(f"=== analyze --all done: {len(results)}/{len(surfaces_to_analyze)} surfaces processed ===")

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
