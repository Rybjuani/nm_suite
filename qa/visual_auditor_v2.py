"""Visual Auditor V2 — structural diff + VLM classification.

Converts mockup↔capture comparisons into structured, navigable, prioritized
evidence. Reuses existing stack (capture_v8.py, diff_fidelity.py,
mockup_reference_static/manifest.json). Replaces heuristic classification
with VLM-driven analysis.

Commands:
    python qa/visual_auditor_v2.py analyze --all
    python qa/visual_auditor_v2.py analyze --surface suite:rutina-empty:default@light
    python qa/visual_auditor_v2.py analyze --all --no-vlm
    python qa/visual_auditor_v2.py queue
    python qa/visual_auditor_v2.py clear-cache
    python qa/visual_auditor_v2.py doctor
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import textwrap
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

warnings.filterwarnings("ignore", category=UserWarning)

_PROJ = Path(__file__).resolve().parent.parent
_MOCKUP_MANIFEST = _PROJ / "qa" / "mockup_reference_static" / "manifest.json"
_MOCKUP_DIR = _PROJ / "qa" / "mockup_reference_static"
_CAPTURE_DIR = _PROJ / "qa" / "_captures_v8"
_CAPTURE_MANIFEST = _CAPTURE_DIR / "CAPTURE_MANIFEST.json"
_FIDELITY_REPORT = _PROJ / "qa" / "_fidelity_current" / "FIDELITY_REPORT.json"
_OUT_DIR = _PROJ / "qa" / "_visual_auditor_v2" / "latest"
_CACHE_DIR = _PROJ / "qa" / "_visual_auditor_v2" / "cache"

_NAME_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+x\d+)\.png$")

VALID_LABELS: set[str] = {
    "LAYOUT_SHIFT",
    "SIZE_MISMATCH",
    "SPACING_MISMATCH",
    "COLOR_MISMATCH",
    "TEXT_MISMATCH",
    "MISSING_COMPONENT",
    "EXTRA_COMPONENT",
    "CHROME_MISMATCH",
    "RENDER_NOISE",
    "PAIRING_OR_CAPTURE_MISMATCH",
    "NEEDS_HUMAN_REVIEW",
}

VALID_RECOMMENDATIONS: set[str] = {
    "PRODUCT_FIX_CANDIDATE",
    "FIXTURE_FIX_CANDIDATE",
    "PAIRING_OR_CAPTURE_FIX_CANDIDATE",
    "LIKELY_RENDER_NOISE",
    "NEEDS_HUMAN_REVIEW",
}

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "needs_review": 3}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}
RECOMMENDATION_ORDER = {
    "PRODUCT_FIX_CANDIDATE": 0,
    "FIXTURE_FIX_CANDIDATE": 1,
    "PAIRING_OR_CAPTURE_FIX_CANDIDATE": 2,
    "LIKELY_RENDER_NOISE": 3,
    "NEEDS_HUMAN_REVIEW": 4,
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
class Classification:
    labels: list[str] = field(default_factory=list)
    severity: str = "needs_review"
    explanation: str = ""
    recommendation: str = "NEEDS_HUMAN_REVIEW"
    suspected_module: str = ""
    confidence: str = "low"
    confidence_reason: str = ""
    vlm_model: str = ""
    vlm_tokens_used: int = 0
    vlm_cost_estimate_usd: float = 0.0


@dataclass
class SurfaceReport:
    surface_key: str
    decision: str = "NEEDS_HUMAN_REVIEW"
    suspected_module: str = ""
    suspected_lines: str = ""
    evidence_summary: str = ""
    confidence: str = "low"
    what_to_check_first: str = ""
    do_not_touch_if: str = ""
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
    # Some screens have a "primary" state that is omitted from the filename.
    # Known primary states that are omitted: default, score (for home), list (for pacientes)
    primary_states = {"default", "score", "list", "normal", ""}
    if state_id in primary_states:
        return screen_id
    return f"{screen_id}-{state_id}"


def _surface_key_to_capture_filename(surface_key: SurfaceKey) -> str:
    view = _build_capture_view(surface_key.screen_id, surface_key.state_id)
    return f"{surface_key.app}-{view}-{surface_key.theme}-960x600.png"


def _capture_filename_variants(surface_key: SurfaceKey) -> list[str]:
    """Return possible capture filenames for a surface key."""
    variants = []
    # With state_id
    view_with_state = f"{surface_key.screen_id}-{surface_key.state_id}"
    variants.append(f"{surface_key.app}-{view_with_state}-{surface_key.theme}-960x600.png")
    # Without state_id (primary/default)
    variants.append(f"{surface_key.app}-{surface_key.screen_id}-{surface_key.theme}-960x600.png")
    # Kebab-case state_id
    kebab_state = surface_key.state_id.replace("_", "-")
    if kebab_state != surface_key.state_id:
        variants.append(f"{surface_key.app}-{surface_key.screen_id}-{kebab_state}-{surface_key.theme}-960x600.png")
    return variants


def _sanitize_dir_name(surface_key: str) -> str:
    return surface_key.replace(":", "_")


# ---------------------------------------------------------------------------
# Pairing
# ---------------------------------------------------------------------------

def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("items", [])


def load_capture_manifest(path: Path) -> dict[tuple[str, str, str, str], dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    indexed: dict[tuple[str, str, str, str], dict] = {}
    for result in data.get("results", []):
        fname = result.get("file", "")
        parsed = _parse_capture_name(Path(fname))
        if parsed:
            indexed[parsed] = result
    return indexed


def pair_surfaces(
    manifest_items: list[dict],
    capture_dir: Path,
) -> list[Pairing]:
    capture_files = {p.name: p for p in capture_dir.rglob("*.png")}
    pairings: list[Pairing] = []

    for item in manifest_items:
        sk = _build_surface_key_from_manifest(item)
        variants = _capture_filename_variants(sk)
        capture_path = None
        for variant in variants:
            if variant in capture_files:
                capture_path = capture_files[variant]
                break

        mockup_abs = _MOCKUP_DIR / item["relative_path"]

        if capture_path and mockup_abs.exists():
            pairings.append(
                Pairing(
                    surface_key=sk.full,
                    app=sk.app,
                    view=_build_capture_view(sk.screen_id, sk.state_id),
                    theme=sk.theme,
                    mockup_path=str(mockup_abs),
                    real_capture_path=str(capture_path),
                    diff_path="",
                    overlay_path="",
                    pairing_source="manifest",
                    pairing_method=(
                        "manifest.json item matched by (theme, product, screen_id, state_id)"
                    ),
                    pairing_confidence="high",
                )
            )
        else:
            # Fallback: try filename convention without manifest
            pairings.append(
                Pairing(
                    surface_key=sk.full,
                    app=sk.app,
                    view=_build_capture_view(sk.screen_id, sk.state_id),
                    theme=sk.theme,
                    mockup_path=str(mockup_abs) if mockup_abs.exists() else "",
                    real_capture_path=str(capture_path) if capture_path else "",
                    diff_path="",
                    overlay_path="",
                    pairing_source="fallback" if capture_path else "unpaired",
                    pairing_method=(
                        "filename convention fallback"
                        if capture_path
                        else "no capture file found for expected filename"
                    ),
                    pairing_confidence="medium" if capture_path else "low",
                )
            )

    return pairings


# ---------------------------------------------------------------------------
# Diff + BBoxes
# ---------------------------------------------------------------------------

def _load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _compute_phash_distance(path_a: Path, path_b: Path) -> tuple[int, str]:
    try:
        import imagehash

        a = Image.open(path_a)
        b = Image.open(path_b)
        ha = imagehash.phash(a)
        hb = imagehash.phash(b)
        return ha - hb, "imagehash.phash"
    except Exception:
        return -1, "unavailable"


def _compute_metrics(
    mockup_path: Path, capture_path: Path
) -> tuple[Metrics, Image.Image, Image.Image]:
    target = _load_rgb(mockup_path)
    actual = _load_rgb(capture_path)

    size_mismatch = target.size != actual.size
    if size_mismatch:
        actual = actual.resize(target.size, Image.Resampling.LANCZOS)

    t = np.asarray(target)
    a = np.asarray(actual)
    diff = np.abs(t.astype(np.int16) - a.astype(np.int16))

    # SSIM
    ssim_val, method = _ssim(t, a)

    phash_dist, phash_method = _compute_phash_distance(mockup_path, capture_path)

    metrics = Metrics(
        ssim=round(float(ssim_val), 5),
        ssim_method=method,
        mean_abs_diff=round(float(diff.mean() / 255.0), 5),
        max_abs_diff=round(float(diff.max() / 255.0), 5),
        changed_pixel_ratio=round(float((diff.max(axis=2) > 12).mean()), 5),
        size_mismatch=size_mismatch,
        phash_distance=phash_dist,
        phash_method=phash_method,
    )

    return metrics, target, actual


def _ssim(a: np.ndarray, b: np.ndarray) -> tuple[float, str]:
    try:
        from skimage.metrics import structural_similarity

        value = structural_similarity(a, b, channel_axis=2, data_range=255)
        return float(value), "skimage"
    except Exception:
        return _global_ssim(a, b), "global"


def _global_ssim(a: np.ndarray, b: np.ndarray) -> float:
    x = a.astype(np.float64) / 255.0
    y = b.astype(np.float64) / 255.0
    if x.ndim == 3:
        x = 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
        y = 0.2126 * y[..., 0] + 0.7152 * y[..., 1] + 0.0722 * y[..., 2]
    c1 = 0.01**2
    c2 = 0.03**2
    mux = float(x.mean())
    muy = float(y.mean())
    vx = float(x.var())
    vy = float(y.var())
    cov = float(((x - mux) * (y - muy)).mean())
    denom = (mux * mux + muy * muy + c1) * (vx + vy + c2)
    if denom == 0:
        return 1.0 if np.array_equal(a, b) else 0.0
    return ((2 * mux * muy + c1) * (2 * cov + c2)) / denom


def _extract_bboxes(
    target: Image.Image, actual: Image.Image, top_k: int = 5
) -> tuple[list[BBoxInfo], Image.Image, Image.Image]:
    """Return connected-component bboxes from diff, plus diff image and overlay."""
    t = np.asarray(target)
    a = np.asarray(actual)
    if t.shape != a.shape:
        a = np.array(actual.resize(target.size, Image.Resampling.LANCZOS))

    diff = np.abs(t.astype(np.int16) - a.astype(np.int16))
    diff_gray = diff.max(axis=2)
    threshold = 15
    binary = diff_gray > threshold

    try:
        from scipy import ndimage

        labeled, num_features = ndimage.label(binary)
        if num_features == 0:
            return [], _make_diff_image(target, actual), _make_overlay(target, [])

        slices = ndimage.find_objects(labeled)
        bboxes: list[BBoxInfo] = []
        for i, slc in enumerate(slices, start=1):
            if slc is None:
                continue
            y_slice, x_slice = slc
            y0, y1 = y_slice.start or 0, y_slice.stop or binary.shape[0]
            x0, x1 = x_slice.start or 0, x_slice.stop or binary.shape[1]
            area = int((labeled[y0:y1, x0:x1] == i).sum())
            area_ratio = area / (binary.shape[0] * binary.shape[1])
            bboxes.append(
                BBoxInfo(
                    label=i,
                    geometry=(x0, y0, x1, y1),
                    area=area,
                    area_ratio=round(area_ratio, 5),
                )
            )

        bboxes.sort(key=lambda b: b.area, reverse=True)
        top_bboxes = bboxes[:top_k]

        diff_img = _make_diff_image(target, actual)
        overlay = _make_overlay(target, top_bboxes)
        return top_bboxes, diff_img, overlay
    except Exception:
        # scipy not available fallback
        return [], _make_diff_image(target, actual), _make_overlay(target, [])


def _make_diff_image(target: Image.Image, actual: Image.Image) -> Image.Image:
    if target.size != actual.size:
        actual = actual.resize(target.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(target, actual).convert("L")
    heat = Image.merge(
        "RGB",
        (
            diff.point(lambda p: min(255, p * 4)),
            diff.point(lambda _: 0),
            diff.point(lambda _: 0),
        ),
    )
    w, h = target.size
    canvas = Image.new("RGB", (w * 3, h), "white")
    canvas.paste(target, (0, 0))
    canvas.paste(actual, (w, 0))
    canvas.paste(heat, (w * 2, 0))
    draw = ImageDraw.Draw(canvas)
    _draw_label(draw, 0, "mockup target")
    _draw_label(draw, w, "qt capture")
    _draw_label(draw, w * 2, "abs diff x4")
    return canvas


def _draw_label(draw: ImageDraw.ImageDraw, x: int, text: str) -> None:
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle((x, 0, x + 220, 22), fill=(0, 0, 0))
    draw.text((x + 6, 6), text, fill=(255, 255, 255), font=font)


def _make_overlay(target: Image.Image, bboxes: list[BBoxInfo]) -> Image.Image:
    overlay = target.copy()
    draw = ImageDraw.Draw(overlay)
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    for i, bbox in enumerate(bboxes):
        color = colors[i % len(colors)]
        draw.rectangle(bbox.geometry, outline=color, width=3)
        draw.text((bbox.geometry[0] + 2, bbox.geometry[1] - 12), f"bbox{i}", fill=color)
    return overlay


# ---------------------------------------------------------------------------
# VLM classification
# ---------------------------------------------------------------------------

def _image_to_b64(path: Path) -> str:
    with path.open("rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _build_vlm_prompt(metrics: Metrics, surface_key: str) -> str:
    return (
        f"You are a visual UI auditor. Compare the mockup reference (left) "
        f"against the actual Qt capture (center) and the absolute difference "
        f"heatmap (right). The overlay shows bounding boxes of connected "
        f"diff regions.\n\n"
        f"Surface: {surface_key}\n"
        f"Metrics: SSIM={metrics.ssim}, MAD={metrics.mean_abs_diff}, "
        f"changed_pixel_ratio={metrics.changed_pixel_ratio}, "
        f"bbox_count={metrics.bbox_count}\n\n"
        f"Classify the difference using ONLY these labels: "
        f"{', '.join(sorted(VALID_LABELS))}.\n"
        f"Severity must be one of: high, medium, low.\n"
        f"Recommendation must be one of: "
        f"{', '.join(sorted(VALID_RECOMMENDATIONS))}.\n\n"
        f"Respond ONLY with a JSON object having these exact keys:\n"
        f'{{"labels": [...], "severity": "...", "explanation": "...", '
        f'"recommendation": "...", "suspected_module": "...", '
        f'"confidence": "high|medium|low", "confidence_reason": "..."}}'
    )


def _call_vlm_kimi(
    mockup_path: Path,
    capture_path: Path,
    diff_path: Path,
    overlay_path: Path,
    metrics: Metrics,
    surface_key: str,
) -> Classification:
    """Kimi OAuth backend (k2p6 multimodal) via OpenAI-compatible endpoint.

    Reads api_key and base_url from the active Kimi Code config.toml
    (~/.kimi-code/config.toml on Unix, %APPDATA%/kimi-desktop/.../config.toml on Windows).
    Falls back to NM_KIMI_API_KEY / NM_KIMI_BASE_URL env overrides.
    """
    import re as _re
    import urllib.request as _ur
    import urllib.error as _ue

    cfg_candidates = [
        Path(os.environ.get("KIMI_CONFIG", "")),
        Path.home() / ".kimi" / "config.toml",
        Path.home() / ".kimi-code" / "config.toml",
        Path(os.environ.get("APPDATA", "")) / "kimi-desktop" / "daimon-share" / "config.toml",
    ]
    api_key = os.environ.get("NM_KIMI_API_KEY", "")
    base_url = os.environ.get("NM_KIMI_BASE_URL", "")
    for cp in cfg_candidates:
        if not api_key and cp.exists():
            try:
                t = cp.read_text(encoding="utf-8")
                mk = _re.search(r'api_key\s*=\s*"([^"]+)"', t)
                mb = _re.search(r'base_url\s*=\s*"([^"]+)"', t)
                if mk:
                    api_key = mk.group(1)
                if mb:
                    base_url = mb.group(1)
                if api_key and base_url:
                    break
            except OSError:
                continue

    if not api_key or not base_url:
        return Classification(
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            explanation="Kimi backend selected but api_key/base_url not found in config.",
            recommendation="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason="Kimi credentials missing.",
        )

    try:
        prompt = _build_vlm_prompt(metrics, surface_key)
        b64_mockup = _image_to_b64(mockup_path)
        b64_capture = _image_to_b64(capture_path)
        b64_diff = _image_to_b64(diff_path)
        b64_overlay = _image_to_b64(overlay_path)

        content: list[dict] = [{"type": "text", "text": prompt}]
        for b64 in (b64_mockup, b64_capture, b64_diff, b64_overlay):
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            )

        payload = {
            "model": os.environ.get("NM_KIMI_MODEL", "k2p6"),
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 16000,
            "temperature": 1,
        }
        req = _ur.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with _ur.urlopen(req, timeout=180) as resp:
            body_text = resp.read().decode("utf-8")
        parsed_resp = json.loads(body_text)
        raw = parsed_resp["choices"][0]["message"]["content"]
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.split("\n", 1)[-1].rsplit("\n", 1)[0]
        if raw_clean.endswith("```"):
            raw_clean = raw_clean[:-3].strip()
        parsed = json.loads(raw_clean)
        labels = [lbl for lbl in parsed.get("labels", []) if lbl in VALID_LABELS]
        if not labels:
            labels = ["NEEDS_HUMAN_REVIEW"]
        rec = parsed.get("recommendation", "NEEDS_HUMAN_REVIEW")
        if rec not in VALID_RECOMMENDATIONS:
            rec = "NEEDS_HUMAN_REVIEW"
        usage = parsed_resp.get("usage", {}) or {}
        return Classification(
            labels=labels,
            severity=parsed.get("severity", "needs_review"),
            explanation=parsed.get("explanation", ""),
            recommendation=rec,
            suspected_module=parsed.get("suspected_module", ""),
            confidence=parsed.get("confidence", "low"),
            confidence_reason=parsed.get("confidence_reason", ""),
            vlm_model=f"kimi/{os.environ.get('NM_KIMI_MODEL', 'k2p6')}",
            vlm_tokens_used=usage.get("total_tokens", 0),
            vlm_cost_estimate_usd=0.0,
        )
    except Exception as exc:
        return Classification(
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            explanation=f"Kimi VLM call failed: {exc}",
            recommendation="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason=f"Kimi exception: {type(exc).__name__}",
        )


def _call_vlm(
    mockup_path: Path,
    capture_path: Path,
    diff_path: Path,
    overlay_path: Path,
    metrics: Metrics,
    surface_key: str,
) -> Classification:
    backend = os.environ.get("NM_VLM_BACKEND", "").lower()
    if not backend:
        return Classification(
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            explanation="VLM backend not configured (NM_VLM_BACKEND not set).",
            recommendation="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason="No VLM available.",
        )
    if backend == "kimi":
        return _call_vlm_kimi(
            mockup_path, capture_path, diff_path, overlay_path, metrics, surface_key
        )

    # Try GLM-4V via z-ai-web-dev-sdk if available

    # Try GLM-4V via z-ai-web-dev-sdk if available
    try:
        from z_ai_web_dev_sdk import VisionClient

        client = VisionClient()
        prompt = _build_vlm_prompt(metrics, surface_key)
        b64_mockup = _image_to_b64(mockup_path)
        b64_capture = _image_to_b64(capture_path)
        b64_diff = _image_to_b64(diff_path)
        b64_overlay = _image_to_b64(overlay_path)

        # Construct a multi-image prompt; SDK specifics vary — this is a best-effort
        # generic shape that many vision APIs accept.
        response = client.chat.completions.create(
            model="glm-4v",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_mockup}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_capture}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_diff}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_overlay}"}},
                    ],
                }
            ],
        )
        raw = response.choices[0].message.content
        # Extract JSON from markdown code block if present
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.split("\n", 1)[-1].rsplit("\n", 1)[0]
        if raw_clean.endswith("```"):
            raw_clean = raw_clean[:-3].strip()
        parsed = json.loads(raw_clean)
        labels = [lbl for lbl in parsed.get("labels", []) if lbl in VALID_LABELS]
        if not labels:
            labels = ["NEEDS_HUMAN_REVIEW"]
        rec = parsed.get("recommendation", "NEEDS_HUMAN_REVIEW")
        if rec not in VALID_RECOMMENDATIONS:
            rec = "NEEDS_HUMAN_REVIEW"
        return Classification(
            labels=labels,
            severity=parsed.get("severity", "needs_review"),
            explanation=parsed.get("explanation", ""),
            recommendation=rec,
            suspected_module=parsed.get("suspected_module", ""),
            confidence=parsed.get("confidence", "low"),
            confidence_reason=parsed.get("confidence_reason", ""),
            vlm_model="glm-4v",
            vlm_tokens_used=response.usage.total_tokens if hasattr(response, "usage") else 0,
            vlm_cost_estimate_usd=0.012,
        )
    except Exception as exc:
        return Classification(
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            explanation=f"VLM call failed: {exc}",
            recommendation="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason=f"VLM exception: {type(exc).__name__}",
        )


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_key(mockup_path: Path, capture_path: Path) -> str:
    m = _sha256_file(mockup_path)
    c = _sha256_file(capture_path)
    return hashlib.sha256(f"{m}:{c}".encode()).hexdigest()


def _cache_path(cache_key: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{cache_key}.json"


def _load_cached(cache_key: str) -> Classification | None:
    cp = _cache_path(cache_key)
    if cp.exists():
        data = json.loads(cp.read_text(encoding="utf-8"))
        return Classification(**data)
    return None


def _save_cached(cache_key: str, classification: Classification) -> None:
    cp = _cache_path(cache_key)
    cp.write_text(json.dumps(asdict(classification), indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------

def analyze_surface(
    pairing: Pairing,
    out_dir: Path,
    use_vlm: bool = True,
) -> dict[str, Any]:
    surface_dir = out_dir / "surfaces" / _sanitize_dir_name(pairing.surface_key)
    surface_dir.mkdir(parents=True, exist_ok=True)
    crops_dir = surface_dir / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)

    mockup_path = Path(pairing.mockup_path)
    capture_path = Path(pairing.real_capture_path)

    # Copy / symlink mockup and real
    mockup_dst = surface_dir / "mockup.png"
    real_dst = surface_dir / "real.png"
    if mockup_path.exists():
        mockup_dst.write_bytes(mockup_path.read_bytes())
    if capture_path.exists():
        real_dst.write_bytes(capture_path.read_bytes())

    # Compute metrics + bboxes
    if mockup_path.exists() and capture_path.exists():
        metrics, target_img, actual_img = _compute_metrics(mockup_path, capture_path)
        bboxes, diff_img, overlay = _extract_bboxes(target_img, actual_img, top_k=5)
    else:
        metrics = Metrics()
        bboxes = []
        diff_img = Image.new("RGB", (100, 100), color=(200, 200, 200))
        overlay = diff_img.copy()

    metrics.bbox_count = len(bboxes)
    if bboxes:
        metrics.bbox_total_area_ratio = round(sum(b.area_ratio for b in bboxes), 5)
        metrics.bbox_largest_area_ratio = round(bboxes[0].area_ratio, 5)
        metrics.bbox_largest_geometry = list(bboxes[0].geometry)

    diff_path = surface_dir / "diff.png"
    overlay_path = surface_dir / "overlay.png"
    diff_img.save(diff_path)
    overlay.save(overlay_path)

    pairing.diff_path = str(diff_path)
    pairing.overlay_path = str(overlay_path)

    # Crops
    crop_paths: list[str] = []
    for i, bbox in enumerate(bboxes):
        bbox_dir = crops_dir / f"bbox_{i}"
        bbox_dir.mkdir(parents=True, exist_ok=True)
        x0, y0, x1, y1 = bbox.geometry
        if mockup_path.exists():
            m_crop = _load_rgb(mockup_path).crop((x0, y0, x1, y1))
            m_crop.save(bbox_dir / "mockup.png")
        if capture_path.exists():
            r_crop = _load_rgb(capture_path).crop((x0, y0, x1, y1))
            r_crop.save(bbox_dir / "real.png")
        # diff crop from diff_img (which is 3x width)
        dw, dh = diff_img.size
        w = dw // 3
        diff_crop = diff_img.crop((x0 + w * 2, y0, x1 + w * 2, y1))
        diff_crop.save(bbox_dir / "diff.png")
        crop_paths.append(str(bbox_dir))

    pairing.crop_paths = crop_paths

    # Classification
    cache_key = _cache_key(mockup_path, capture_path) if mockup_path.exists() and capture_path.exists() else ""
    classification: Classification
    if not use_vlm or not cache_key:
        classification = Classification(
            labels=["NEEDS_HUMAN_REVIEW"],
            severity="needs_review",
            explanation="VLM disabled or images missing. Manual review required.",
            recommendation="NEEDS_HUMAN_REVIEW",
            confidence="low",
            confidence_reason="--no-vlm flag or missing image.",
        )
    else:
        cached = _load_cached(cache_key)
        if cached:
            classification = cached
        else:
            classification = _call_vlm(
                mockup_path,
                capture_path,
                diff_path,
                overlay_path,
                metrics,
                pairing.surface_key,
            )
            _save_cached(cache_key, classification)

    # Ensure low confidence forces NEEDS_HUMAN_REVIEW
    if classification.confidence == "low":
        classification.recommendation = "NEEDS_HUMAN_REVIEW"
        if "NEEDS_HUMAN_REVIEW" not in classification.labels:
            classification.labels.append("NEEDS_HUMAN_REVIEW")

    # Build agent package
    agent_report = SurfaceReport(
        surface_key=pairing.surface_key,
        decision=(
            "FIX_PRODUCT"
            if classification.recommendation == "PRODUCT_FIX_CANDIDATE"
            else (
                "FIX_FIXTURE"
                if classification.recommendation == "FIXTURE_FIX_CANDIDATE"
                else (
                    "FIX_PAIRING"
                    if classification.recommendation == "PAIRING_OR_CAPTURE_FIX_CANDIDATE"
                    else (
                        "SKIP_RENDER_NOISE"
                        if classification.recommendation == "LIKELY_RENDER_NOISE"
                        else "NEEDS_HUMAN_REVIEW"
                    )
                )
            )
        ),
        suspected_module=classification.suspected_module,
        suspected_lines="",
        evidence_summary=(
            f"{classification.explanation} "
            f"SSIM={metrics.ssim}, MAD={metrics.mean_abs_diff}, "
            f"changed={metrics.changed_pixel_ratio}, bbox_count={metrics.bbox_count}."
        ),
        confidence=classification.confidence,
        what_to_check_first=(
            "Review suspected_module and compare with related surfaces."
        ),
        do_not_touch_if="confidence == 'low' or diff is RENDER_NOISE",
        pairing_concerns=None if pairing.pairing_confidence == "high" else pairing.pairing_method,
    )

    if classification.confidence == "low":
        agent_report.decision = "NEEDS_HUMAN_REVIEW"

    # Write per-surface files
    metrics_dict = asdict(metrics)
    # Convert numpy types to native Python for JSON serialization
    for key, val in metrics_dict.items():
        if hasattr(val, "item"):
            metrics_dict[key] = val.item()
        elif isinstance(val, list):
            metrics_dict[key] = [
                v.item() if hasattr(v, "item") else v for v in val
            ]

    metrics_path = surface_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                **metrics_dict,
                "surface_key": pairing.surface_key,
                "mockup_path": str(mockup_path),
                "real_capture_path": str(capture_path),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    classification_path = surface_dir / "classification.json"
    classification_path.write_text(
        json.dumps(asdict(classification), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    agent_path = surface_dir / "agent_package.json"
    agent_path.write_text(
        json.dumps(asdict(agent_report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "pairing": asdict(pairing),
        "metrics": asdict(metrics),
        "classification": asdict(classification),
        "agent_package": asdict(agent_report),
    }


# ---------------------------------------------------------------------------
# Queue + HTML report
# ---------------------------------------------------------------------------

def _queue_sort_key(item: dict) -> tuple[int, int, int, bool, bool]:
    cls = item.get("classification", {})
    sev = SEVERITY_ORDER.get(cls.get("severity", "needs_review"), 3)
    conf = CONFIDENCE_ORDER.get(cls.get("confidence", "low"), 2)
    rec = RECOMMENDATION_ORDER.get(cls.get("recommendation", "NEEDS_HUMAN_REVIEW"), 4)
    # cross_theme / cross_state are computed outside and injected
    cross_theme = item.get("cross_theme", False)
    cross_state = item.get("cross_state", False)
    return (sev, conf, rec, cross_theme, cross_state)


def build_queue(results: list[dict]) -> list[dict]:
    # Compute cross_theme and cross_state
    screen_state_map: dict[str, set[str]] = {}
    screen_theme_map: dict[str, set[str]] = {}
    for r in results:
        sk = r.get("pairing", {}).get("surface_key", "")
        parts = sk.split(":")
        if len(parts) != 3:
            continue
        app_screen = parts[0] + ":" + parts[1].split("-")[0]
        theme = parts[2]
        state = parts[1]
        screen_theme_map.setdefault(app_screen, set()).add(theme)
        screen_state_map.setdefault(app_screen, set()).add(state)

    for r in results:
        sk = r.get("pairing", {}).get("surface_key", "")
        parts = sk.split(":")
        if len(parts) == 3:
            app_screen = parts[0] + ":" + parts[1].split("-")[0]
            r["cross_theme"] = len(screen_theme_map.get(app_screen, set())) > 1
            r["cross_state"] = len(screen_state_map.get(app_screen, set())) > 1
        else:
            r["cross_theme"] = False
            r["cross_state"] = False

    return sorted(results, key=_queue_sort_key)


def _severity_badge(severity: str) -> str:
    colors = {
        "high": "#dc2626",
        "medium": "#ea580c",
        "low": "#16a34a",
        "needs_review": "#6b7280",
    }
    return f'<span style="background:{colors.get(severity, "#6b7280")};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{severity.upper()}</span>'


def _confidence_badge(confidence: str) -> str:
    colors = {
        "high": "#16a34a",
        "medium": "#ca8a04",
        "low": "#dc2626",
    }
    return f'<span style="background:{colors.get(confidence, "#6b7280")};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{confidence.upper()}</span>'


def _rec_badge(rec: str) -> str:
    labels = {
        "PRODUCT_FIX_CANDIDATE": "PRODUCT FIX",
        "FIXTURE_FIX_CANDIDATE": "FIXTURE FIX",
        "PAIRING_OR_CAPTURE_FIX_CANDIDATE": "PAIRING FIX",
        "LIKELY_RENDER_NOISE": "RENDER NOISE",
        "NEEDS_HUMAN_REVIEW": "HUMAN REVIEW",
    }
    return f'<span style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{labels.get(rec, rec)}</span>'


def generate_html(report_data: list[dict], out_path: Path) -> None:
    total = len(report_data)
    pass_count = sum(
        1
        for r in report_data
        if r.get("classification", {}).get("severity", "") == "low"
        and r.get("classification", {}).get("confidence", "") == "high"
    )
    needs_human = sum(
        1
        for r in report_data
        if r.get("classification", {}).get("recommendation", "") == "NEEDS_HUMAN_REVIEW"
    )
    pass_pct = round((pass_count / total * 100), 1) if total else 0.0
    human_pct = round((needs_human / total * 100), 1) if total else 0.0

    top10 = build_queue(report_data)[:10]

    rows_html = []
    for r in report_data:
        p = r.get("pairing", {})
        c = r.get("classification", {})
        m = r.get("metrics", {})
        sk = p.get("surface_key", "")
        dir_name = _sanitize_dir_name(sk)
        labels_html = " ".join(
            f'<span style="background:#374151;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px">{lbl}</span>'
            for lbl in c.get("labels", [])
        )
        rows_html.append(
            f"""
        <tr data-app="{p.get('app','')}" data-theme="{p.get('theme','')}" data-severity="{c.get('severity','')}" data-rec="{c.get('recommendation','')}" data-labels="{' '.join(c.get('labels',[]))}">
          <td style="padding:8px;border-bottom:1px solid #374151">{sk}</td>
          <td style="padding:8px;border-bottom:1px solid #374151"><img src="surfaces/{dir_name}/mockup.png" style="max-width:180px;cursor:pointer" onclick="window.open(this.src)"></td>
          <td style="padding:8px;border-bottom:1px solid #374151"><img src="surfaces/{dir_name}/real.png" style="max-width:180px;cursor:pointer" onclick="window.open(this.src)"></td>
          <td style="padding:8px;border-bottom:1px solid #374151"><img src="surfaces/{dir_name}/diff.png" style="max-width:180px;cursor:pointer" onclick="window.open(this.src)"></td>
          <td style="padding:8px;border-bottom:1px solid #374151"><img src="surfaces/{dir_name}/overlay.png" style="max-width:180px;cursor:pointer" onclick="window.open(this.src)"></td>
          <td style="padding:8px;border-bottom:1px solid #374151;font-size:12px">
            SSIM: {m.get('ssim','')}<br>
            MAD: {m.get('mean_abs_diff','')}<br>
            Changed%: {m.get('changed_pixel_ratio','')}<br>
            bbox: {m.get('bbox_count','')}<br>
            phash: {m.get('phash_distance','')}
          </td>
          <td style="padding:8px;border-bottom:1px solid #374151;font-size:12px">
            {labels_html}<br><br>
            {_severity_badge(c.get('severity','needs_review'))}<br><br>
            {_confidence_badge(c.get('confidence','low'))}<br><br>
            {_rec_badge(c.get('recommendation','NEEDS_HUMAN_REVIEW'))}
          </td>
          <td style="padding:8px;border-bottom:1px solid #374151;font-size:12px;max-width:300px">
            {c.get('explanation','')}
          </td>
          <td style="padding:8px;border-bottom:1px solid #374151;font-size:12px">
            {c.get('suspected_module','')}
          </td>
          <td style="padding:8px;border-bottom:1px solid #374151;font-size:12px">
            <a href="surfaces/{dir_name}/metrics.json">metrics</a><br>
            <a href="surfaces/{dir_name}/classification.json">classification</a><br>
            <a href="surfaces/{dir_name}/agent_package.json">agent</a>
          </td>
        </tr>
        """
        )

    top10_html = ""
    for i, r in enumerate(top10, 1):
        c = r.get("classification", {})
        p = r.get("pairing", {})
        top10_html += f"""
        <li style="margin-bottom:6px">
          <strong>{i}. {p.get('surface_key','')}</strong> —
          {_severity_badge(c.get('severity',''))} {_rec_badge(c.get('recommendation',''))}<br>
          labels: {', '.join(c.get('labels',[]))} | module: {c.get('suspected_module','')} | confidence: {c.get('confidence','')}
        </li>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Visual Auditor V2 Report</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:20px; }}
  h1,h2 {{ color:#f8fafc; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th {{ background:#1e293b; padding:10px; text-align:left; border-bottom:2px solid #334155; }}
  td {{ vertical-align: top; }}
  .filters {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }}
  .filters select, .filters input {{ background:#1e293b; color:#e2e8f0; border:1px solid #334155; padding:6px 10px; border-radius:4px; }}
  .summary {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(140px,1fr)); gap:12px; margin-bottom:20px; }}
  .card {{ background:#1e293b; padding:16px; border-radius:8px; text-align:center; }}
  .card big {{ display:block; font-size:28px; font-weight:bold; color:#38bdf8; }}
  a {{ color:#38bdf8; }}
</style>
</head>
<body>
<h1>Visual Auditor V2</h1>
<div class="summary">
  <div class="card"><big>{total}</big> surfaces</div>
  <div class="card"><big>{pass_pct}%</big> PASS</div>
  <div class="card"><big>{human_pct}%</big> NEEDS_HUMAN_REVIEW</div>
  <div class="card"><big>{len(top10)}</big> top severity</div>
</div>

<h2>Top 10 by Severity</h2>
<ol>{top10_html}</ol>

<h2>Filters</h2>
<div class="filters">
  <select id="filter-app" onchange="applyFilters()">
    <option value="">all apps</option>
    <option value="suite">suite</option>
    <option value="hub">hub</option>
  </select>
  <select id="filter-theme" onchange="applyFilters()">
    <option value="">all themes</option>
    <option value="light">light</option>
    <option value="dark">dark</option>
  </select>
  <select id="filter-severity" onchange="applyFilters()">
    <option value="">all severities</option>
    <option value="high">high</option>
    <option value="medium">medium</option>
    <option value="low">low</option>
    <option value="needs_review">needs_review</option>
  </select>
  <select id="filter-rec" onchange="applyFilters()">
    <option value="">all recommendations</option>
    <option value="PRODUCT_FIX_CANDIDATE">PRODUCT_FIX</option>
    <option value="FIXTURE_FIX_CANDIDATE">FIXTURE_FIX</option>
    <option value="PAIRING_OR_CAPTURE_FIX_CANDIDATE">PAIRING_FIX</option>
    <option value="LIKELY_RENDER_NOISE">RENDER_NOISE</option>
    <option value="NEEDS_HUMAN_REVIEW">HUMAN_REVIEW</option>
  </select>
  <input id="filter-search" type="text" placeholder="search surface_key..." oninput="applyFilters()">
</div>

<table id="report-table">
<thead>
<tr>
  <th>surface_key</th>
  <th>mockup</th>
  <th>real</th>
  <th>diff</th>
  <th>overlay</th>
  <th>metrics</th>
  <th>classification</th>
  <th>explanation</th>
  <th>module</th>
  <th>links</th>
</tr>
</thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>

<script>
function applyFilters() {{
  const app = document.getElementById('filter-app').value;
  const theme = document.getElementById('filter-theme').value;
  const severity = document.getElementById('filter-severity').value;
  const rec = document.getElementById('filter-rec').value;
  const search = document.getElementById('filter-search').value.toLowerCase();
  document.querySelectorAll('#report-table tbody tr').forEach(row => {{
    let ok = true;
    if (app && row.dataset.app !== app) ok = false;
    if (theme && row.dataset.theme !== theme) ok = false;
    if (severity && row.dataset.severity !== severity) ok = false;
    if (rec && row.dataset.rec !== rec) ok = false;
    if (search && !row.cells[0].textContent.toLowerCase().includes(search)) ok = false;
    row.style.display = ok ? '' : 'none';
  }});
}}
</script>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def generate_queue_md(queue: list[dict], out_path: Path) -> None:
    lines = ["# Visual Auditor V2 — Prioritized Queue", ""]
    for i, item in enumerate(queue, 1):
        p = item.get("pairing", {})
        c = item.get("classification", {})
        lines.append(f"## {i}. {p.get('surface_key', '')}")
        lines.append(f"- severity: {c.get('severity', '')}")
        lines.append(f"- confidence: {c.get('confidence', '')}")
        lines.append(f"- recommendation: {c.get('recommendation', '')}")
        lines.append(f"- labels: {', '.join(c.get('labels', []))}")
        lines.append(f"- suspected_module: {c.get('suspected_module', '')}")
        lines.append(f"- explanation: {c.get('explanation', '')}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------

def doctor() -> int:
    issues: list[str] = []

    # 1. manifest
    if not _MOCKUP_MANIFEST.exists():
        issues.append("MISSING: qa/mockup_reference_static/manifest.json")
    else:
        try:
            json.loads(_MOCKUP_MANIFEST.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"BAD JSON: manifest.json — {exc}")

    # 2. captures
    if not _CAPTURE_DIR.exists():
        issues.append("MISSING: qa/_captures_v8/")
    if not _CAPTURE_MANIFEST.exists():
        issues.append("MISSING: qa/_captures_v8/CAPTURE_MANIFEST.json")

    # 3. fidelity report
    if not _FIDELITY_REPORT.exists():
        issues.append("MISSING: qa/_fidelity_current/FIDELITY_REPORT.json (run diff_fidelity.py)")

    # 4. deps
    deps = ["PIL", "numpy", "scipy", "imagehash", "skimage"]
    for dep in deps:
        try:
            __import__(dep)
        except Exception:
            issues.append(f"MISSING DEP: {dep}")

    # 5. VLM sanity
    backend = os.environ.get("NM_VLM_BACKEND", "")
    if not backend:
        issues.append("INFO: NM_VLM_BACKEND not set — VLM classification will degrade to NEEDS_HUMAN_REVIEW")
    else:
        try:
            from z_ai_web_dev_sdk import VisionClient

            _ = VisionClient()
            issues.append("OK: VLM client (z-ai-web-dev-sdk) importable")
        except Exception as exc:
            issues.append(f"VLM import issue: {exc}")

    # 6. gitignore
    gitignore = _PROJ / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if "qa/_visual_auditor_v2/" not in content:
            issues.append("GITIGNORE: qa/_visual_auditor_v2/ not in .gitignore")
        else:
            issues.append("OK: qa/_visual_auditor_v2/ is gitignored")
    else:
        issues.append("MISSING: .gitignore")

    # 7. no outputs in mockup_reference_static (except canonical manifest.json)
    if _MOCKUP_DIR.exists():
        generated = [
            p for p in (list(_MOCKUP_DIR.rglob("*.json")) + list(_MOCKUP_DIR.rglob("diff.png")))
            if p.name != "manifest.json"
        ]
        if generated:
            issues.append(f"WARN: {len(generated)} generated files in qa/mockup_reference_static/")

    print("=" * 60)
    print("VISUAL AUDITOR V2 — DOCTOR")
    print("=" * 60)
    for issue in issues:
        print(f"  {'[OK]' if issue.startswith('OK') else ('[INFO]' if issue.startswith('INFO') else '[ISSUE]')} {issue}")
    print("=" * 60)
    return 0 if not any(i.startswith("[ISSUE]") for i in issues) else 1


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Visual Auditor V2")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="Run analysis")
    analyze_p.add_argument("--all", action="store_true", help="Analyze all paired surfaces")
    analyze_p.add_argument("--surface", type=str, default="", help="Specific surface_key")
    analyze_p.add_argument("--no-vlm", action="store_true", help="Offline mode")

    sub.add_parser("queue", help="Export prioritized queue")
    sub.add_parser("clear-cache", help="Clear VLM classification cache")
    sub.add_parser("doctor", help="Validate inputs and environment")

    args = parser.parse_args()

    if args.command == "doctor":
        return doctor()

    if args.command == "clear-cache":
        if _CACHE_DIR.exists():
            for f in _CACHE_DIR.iterdir():
                f.unlink()
        print("Cache cleared.")
        return 0

    if args.command == "queue":
        report_path = _OUT_DIR / "report.json"
        if not report_path.exists():
            print("[ERROR] No report.json found. Run 'analyze --all' first.", file=sys.stderr)
            return 1
        data = json.loads(report_path.read_text(encoding="utf-8"))
        queue = build_queue(data)
        generate_queue_md(queue, _OUT_DIR / "queue.md")
        print(f"Queue written to {_OUT_DIR / 'queue.md'}")
        return 0

    if args.command == "analyze":
        manifest_items = load_manifest(_MOCKUP_MANIFEST)
        if not manifest_items:
            print("[ERROR] manifest.json empty or missing.", file=sys.stderr)
            return 1

        pairings = pair_surfaces(manifest_items, _CAPTURE_DIR)
        if args.surface:
            pairings = [p for p in pairings if p.surface_key == args.surface]
            if not pairings:
                print(f"[ERROR] Surface '{args.surface}' not found.", file=sys.stderr)
                return 1

        _OUT_DIR.mkdir(parents=True, exist_ok=True)
        results: list[dict] = []
        for pairing in pairings:
            if not pairing.real_capture_path or not pairing.mockup_path:
                # Unpaired — still emit a minimal record
                results.append(
                    {
                        "pairing": asdict(pairing),
                        "metrics": asdict(Metrics()),
                        "classification": asdict(
                            Classification(
                                labels=["PAIRING_OR_CAPTURE_MISMATCH"],
                                severity="needs_review",
                                explanation="Missing mockup or capture. Pairing failed.",
                                recommendation="PAIRING_OR_CAPTURE_FIX_CANDIDATE",
                                confidence="low",
                                confidence_reason="Missing image file.",
                            )
                        ),
                        "agent_package": asdict(
                            SurfaceReport(
                                surface_key=pairing.surface_key,
                                decision="FIX_PAIRING",
                                evidence_summary="Pairing failed — missing mockup or capture.",
                                confidence="low",
                            )
                        ),
                    }
                )
                continue
            result = analyze_surface(pairing, _OUT_DIR, use_vlm=not args.no_vlm)
            results.append(result)

        # Write report.json
        report_path = _OUT_DIR / "report.json"
        # Sanitize numpy types from full results list
        def _sanitize(obj):
            if isinstance(obj, dict):
                return {k: _sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize(v) for v in obj]
            if hasattr(obj, "item"):
                return obj.item()
            return obj

        report_path.write_text(json.dumps(_sanitize(results), indent=2, ensure_ascii=False), encoding="utf-8")

        # Write HTML
        generate_html(results, _OUT_DIR / "index.html")

        # Write queue.md
        queue = build_queue(results)
        generate_queue_md(queue, _OUT_DIR / "queue.md")

        print("=" * 60)
        print("VISUAL AUDITOR V2 — ANALYSIS COMPLETE")
        print(f"Surfaces analyzed: {len(results)}")
        print(f"Report JSON:       {report_path}")
        print(f"Report HTML:       {_OUT_DIR / 'index.html'}")
        print(f"Queue MD:          {_OUT_DIR / 'queue.md'}")
        print("=" * 60)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
