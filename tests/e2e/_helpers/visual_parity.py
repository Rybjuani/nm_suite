from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CANONICAL_ROOT = _PROJECT_ROOT / "qa" / "_mockup_canonical"
_DEFAULT_OUT_DIR = _PROJECT_ROOT / "reports" / "e2e" / "visual_parity"
_NAME_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+)x(\d+)\.png$")


@dataclass(frozen=True)
class VisualParityThresholds:
    min_ssim: float = 0.92
    max_mean_abs_diff: float = 0.035
    max_changed_pixel_ratio: float = 0.08
    changed_pixel_floor: int = 12
    render_noise_max_mean_abs_diff: float = 0.004
    render_noise_max_changed_pixel_ratio: float = 0.003
    render_noise_max_region_area_ratio: float = 0.001
    strong_fail_changed_pixel_ratio: float = 0.18
    strong_fail_region_area_ratio: float = 0.08
    strong_fail_mean_abs_diff: float = 0.08
    max_regions: int = 8

    def to_dict(self) -> dict[str, float | int]:
        return {
            "min_ssim": self.min_ssim,
            "max_mean_abs_diff": self.max_mean_abs_diff,
            "max_changed_pixel_ratio": self.max_changed_pixel_ratio,
            "changed_pixel_floor": self.changed_pixel_floor,
            "render_noise_max_mean_abs_diff": self.render_noise_max_mean_abs_diff,
            "render_noise_max_changed_pixel_ratio": self.render_noise_max_changed_pixel_ratio,
            "render_noise_max_region_area_ratio": self.render_noise_max_region_area_ratio,
            "strong_fail_changed_pixel_ratio": self.strong_fail_changed_pixel_ratio,
            "strong_fail_region_area_ratio": self.strong_fail_region_area_ratio,
            "strong_fail_mean_abs_diff": self.strong_fail_mean_abs_diff,
            "max_regions": self.max_regions,
        }


@dataclass(frozen=True)
class CanonicalSurface:
    app: str
    view: str
    theme: str
    width: int
    height: int
    path: Path
    file: str
    screen: str = ""
    state: str = ""
    surface: str = ""
    capture_selector: str = ""
    dom_w: int | None = None
    dom_h: int | None = None
    dom_size_match: bool | None = None
    mockup_sha256: str = ""

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def surface_key(self) -> str:
        return f"{self.app}:{self.view}@{self.theme}"

    @property
    def filename(self) -> str:
        return f"{self.app}-{self.view}-{self.theme}-{self.resolution}.png"

    @property
    def stem(self) -> str:
        return Path(self.filename).stem

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_key": self.surface_key,
            "app": self.app,
            "view": self.view,
            "theme": self.theme,
            "resolution": self.resolution,
            "file": self.file,
            "path": str(self.path),
            "screen": self.screen,
            "state": self.state,
            "surface": self.surface,
            "capture_selector": self.capture_selector,
            "dom_w": self.dom_w,
            "dom_h": self.dom_h,
            "dom_size_match": self.dom_size_match,
            "mockup_sha256": self.mockup_sha256,
        }


@dataclass(frozen=True)
class VisualDiffRegion:
    x: int
    y: int
    w: int
    h: int
    area: int
    area_ratio: float
    hint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "area": self.area,
            "area_ratio": round(self.area_ratio, 6),
            "hint": self.hint,
        }


@dataclass
class VisualParityResult:
    surface_key: str
    status: str
    repair_decision: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    regions: list[VisualDiffRegion] = field(default_factory=list)
    canonical: CanonicalSurface | None = None
    actual_path: Path | None = None
    diff_path: Path | None = None
    report_path: Path | None = None
    agent_package: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_key": self.surface_key,
            "status": self.status,
            "repair_decision": self.repair_decision,
            "passed": self.passed,
            "failures": self.failures,
            "metrics": self.metrics,
            "regions": [region.to_dict() for region in self.regions],
            "canonical": self.canonical.to_dict() if self.canonical else None,
            "actual_path": str(self.actual_path) if self.actual_path else "",
            "diff_path": str(self.diff_path) if self.diff_path else "",
            "report_path": str(self.report_path) if self.report_path else "",
            "agent_package": self.agent_package,
        }

    def failure_message(self) -> str:
        changed = self.metrics.get("changed_pixel_ratio", "")
        mad = self.metrics.get("mean_abs_diff", "")
        ssim = self.metrics.get("ssim", "")
        return (
            f"Visual parity {self.status} for {self.surface_key}; "
            f"decision={self.repair_decision}; failures={self.failures}; "
            f"ssim={ssim} mad={mad} changed={changed}; diff={self.diff_path}"
        )

    def assert_ok(self) -> "VisualParityResult":
        if not self.passed:
            raise AssertionError(self.failure_message())
        return self


class CanonicalIndex:
    def __init__(
        self,
        root: Path,
        surfaces: list[CanonicalSurface],
        manifest: dict[str, Any] | None = None,
    ):
        self.root = root
        self.surfaces = surfaces
        self.manifest = manifest or {}
        self._by_key: dict[str, CanonicalSurface] = {}
        for surface in surfaces:
            for key in _surface_lookup_keys(surface):
                self._by_key[key] = surface

    def resolve(self, surface_key: str) -> CanonicalSurface | None:
        for key in _candidate_surface_keys(surface_key):
            found = self._by_key.get(key)
            if found:
                return found
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "total_surfaces": len(self.surfaces),
            "mockup_sha256": self.manifest.get("mockup_sha256", ""),
            "all_captured": self.manifest.get("all_captured"),
            "all_sizes_match": self.manifest.get("all_sizes_match"),
            "all_dom_sizes_match": self.manifest.get("all_dom_sizes_match"),
        }


def load_canonical_index(root: Path | str = _DEFAULT_CANONICAL_ROOT) -> CanonicalIndex:
    root = Path(root)
    manifest = _read_json(root / "MANIFEST.json")
    manifest_captures = manifest.get("captures") if isinstance(manifest, dict) else None
    surfaces: list[CanonicalSurface] = []

    if isinstance(manifest_captures, list):
        for entry in manifest_captures:
            if not isinstance(entry, dict):
                continue
            file_name = str(entry.get("file") or "")
            parsed = _parse_capture_filename(file_name)
            if not parsed:
                continue
            app, view, theme, width, height = parsed
            surfaces.append(
                CanonicalSurface(
                    app=app,
                    view=view,
                    theme=theme,
                    width=width,
                    height=height,
                    path=root / file_name,
                    file=file_name,
                    screen=str(entry.get("screen") or ""),
                    state=str(entry.get("state") or ""),
                    surface=str(entry.get("surface") or ""),
                    capture_selector=str(entry.get("capture_selector") or ""),
                    dom_w=_optional_int(entry.get("dom_w")),
                    dom_h=_optional_int(entry.get("dom_h")),
                    dom_size_match=_optional_bool(entry.get("dom_size_match")),
                    mockup_sha256=str(manifest.get("mockup_sha256") or ""),
                )
            )
    else:
        for path in sorted(root.glob("*.png")):
            parsed = _parse_capture_filename(path.name)
            if not parsed:
                continue
            app, view, theme, width, height = parsed
            surfaces.append(
                CanonicalSurface(
                    app=app,
                    view=view,
                    theme=theme,
                    width=width,
                    height=height,
                    path=path,
                    file=path.name,
                )
            )

    return CanonicalIndex(root=root, surfaces=surfaces, manifest=manifest)


def compare_visual_parity(
    actual_path: Path | str,
    surface_key: str,
    *,
    canonical_root: Path | str = _DEFAULT_CANONICAL_ROOT,
    out_dir: Path | str = _DEFAULT_OUT_DIR,
    thresholds: VisualParityThresholds | None = None,
    write_artifacts: bool = True,
) -> VisualParityResult:
    thresholds = thresholds or VisualParityThresholds()
    actual_path = Path(actual_path)
    out_dir = Path(out_dir)
    index = load_canonical_index(canonical_root)
    canonical = index.resolve(surface_key)

    if canonical is None:
        return _finalize_result(
            VisualParityResult(
                surface_key=surface_key,
                status="MISSING_CANONICAL",
                repair_decision="PAIRING_FIX",
                passed=False,
                failures=["missing_canonical"],
                actual_path=actual_path,
            ),
            thresholds=thresholds,
            canonical_index=index,
            out_dir=out_dir,
            write_artifacts=write_artifacts,
        )

    if not actual_path.exists():
        return _finalize_result(
            VisualParityResult(
                surface_key=canonical.surface_key,
                status="MISSING_ACTUAL",
                repair_decision="PAIRING_FIX",
                passed=False,
                failures=["missing_actual"],
                canonical=canonical,
                actual_path=actual_path,
            ),
            thresholds=thresholds,
            canonical_index=index,
            out_dir=out_dir,
            write_artifacts=write_artifacts,
        )

    target_img = _load_rgb(canonical.path)
    actual_img = _load_rgb(actual_path)
    metrics, changed_mask = _metrics(target_img, actual_img, thresholds.changed_pixel_floor)
    regions = _diff_regions(changed_mask, target_img.size, thresholds.max_regions)
    failures = _threshold_failures(metrics, thresholds)
    status, repair_decision, passed = _classify(metrics, regions, failures, thresholds)

    diff_path = None
    if write_artifacts:
        diff_path = _surface_out_dir(out_dir, canonical.surface_key) / f"{canonical.stem}-diff.png"
        _write_diff_image(target_img, actual_img, diff_path, regions)

    return _finalize_result(
        VisualParityResult(
            surface_key=canonical.surface_key,
            status=status,
            repair_decision=repair_decision,
            passed=passed,
            failures=failures,
            metrics=metrics,
            regions=regions,
            canonical=canonical,
            actual_path=actual_path,
            diff_path=diff_path,
        ),
        thresholds=thresholds,
        canonical_index=index,
        out_dir=out_dir,
        write_artifacts=write_artifacts,
    )


def assert_visual_parity(
    actual_path: Path | str,
    surface_key: str,
    *,
    canonical_root: Path | str = _DEFAULT_CANONICAL_ROOT,
    out_dir: Path | str = _DEFAULT_OUT_DIR,
    thresholds: VisualParityThresholds | None = None,
) -> VisualParityResult:
    return compare_visual_parity(
        actual_path,
        surface_key,
        canonical_root=canonical_root,
        out_dir=out_dir,
        thresholds=thresholds,
    ).assert_ok()


def write_visual_parity_report(
    results: list[VisualParityResult],
    out_dir: Path | str = _DEFAULT_OUT_DIR,
) -> dict[str, str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "visual_parity_report.json"
    md_path = out_dir / "repair_queue.md"
    payload = {
        "summary": _summary(results),
        "results": [result.to_dict() for result in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_repair_queue_markdown(results), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _finalize_result(
    result: VisualParityResult,
    *,
    thresholds: VisualParityThresholds,
    canonical_index: CanonicalIndex,
    out_dir: Path,
    write_artifacts: bool,
) -> VisualParityResult:
    result.agent_package = _agent_package(result, thresholds, canonical_index)
    if write_artifacts:
        target_dir = _surface_out_dir(out_dir, result.surface_key)
        target_dir.mkdir(parents=True, exist_ok=True)
        result.report_path = target_dir / "result.json"
        result.report_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return result


def _agent_package(
    result: VisualParityResult,
    thresholds: VisualParityThresholds,
    canonical_index: CanonicalIndex,
) -> dict[str, Any]:
    return {
        "surface_key": result.surface_key,
        "status": result.status,
        "repair_decision": result.repair_decision,
        "passed": result.passed,
        "failures": result.failures,
        "metrics": result.metrics,
        "thresholds": thresholds.to_dict(),
        "canonical_index": canonical_index.to_dict(),
        "canonical": result.canonical.to_dict() if result.canonical else None,
        "actual_path": str(result.actual_path) if result.actual_path else "",
        "diff_path": str(result.diff_path) if result.diff_path else "",
        "largest_regions": [region.to_dict() for region in result.regions],
        "what_to_check_first": _what_to_check_first(result),
        "do_not_touch_if": _do_not_touch_if(result),
        "repair_hints": _repair_hints(result),
    }


def _what_to_check_first(result: VisualParityResult) -> list[str]:
    if result.repair_decision == "PAIRING_FIX":
        return [
            "Verify the surface_key maps to the current canonical manifest.",
            "Verify actual capture size, modal selector, theme, and transient UI cleanup before editing product code.",
        ]
    if result.repair_decision == "FIX_PRODUCT_STRONG":
        return [
            "Inspect the largest diff regions first; this usually means layout, modal position, missing widget, or wrong state.",
            "Compare Qt widget geometry against the canonical manifest resolution and selector.",
        ]
    if result.repair_decision == "FIX_PRODUCT_REVIEW":
        return [
            "Inspect typography, spacing, color tokens, text wrap, and icon glyphs inside the listed regions.",
            "Check whether a semantic E2E assertion already proves the state before changing visuals.",
        ]
    return [
        "Keep the artifact for audit, but avoid product changes unless the same area repeats across surfaces.",
    ]


def _do_not_touch_if(result: VisualParityResult) -> list[str]:
    items = [
        "The canonical manifest has all_dom_sizes_match=false or the capture selector is stale.",
        "The actual screenshot contains an unrelated dialog, hover state, focus ring, cursor, toast, or loading state.",
    ]
    if result.canonical and result.canonical.surface in {"modal", "window_modal"}:
        items.append("The modal is being captured at a runtime size that no longer matches the repaired HTML canonical.")
    return items


def _repair_hints(result: VisualParityResult) -> list[str]:
    hints: list[str] = []
    if "size_mismatch" in result.failures:
        hints.append("Pairing fix: recapture the runtime surface or update the E2E selector before visual styling.")
    if result.regions:
        hints.append(f"Open the largest bbox first: {result.regions[0].to_dict()}.")
    if result.metrics.get("changed_pixel_ratio", 0) and result.metrics["changed_pixel_ratio"] > 0.4:
        hints.append("Very large delta: confirm the test reached the same state as the mockup.")
    if result.repair_decision.startswith("FIX_PRODUCT"):
        hints.append("After a product patch, rerun only this surface before expanding to the full visual suite.")
    return hints


def _threshold_failures(
    metrics: dict[str, Any],
    thresholds: VisualParityThresholds,
) -> list[str]:
    failures: list[str] = []
    if metrics.get("size_mismatch"):
        failures.append("size_mismatch")
        return failures
    if float(metrics.get("ssim", 0.0)) < thresholds.min_ssim:
        failures.append(f"ssim<{thresholds.min_ssim:g}")
    if float(metrics.get("mean_abs_diff", 1.0)) > thresholds.max_mean_abs_diff:
        failures.append(f"mad>{thresholds.max_mean_abs_diff:g}")
    if float(metrics.get("changed_pixel_ratio", 1.0)) > thresholds.max_changed_pixel_ratio:
        failures.append(f"changed>{thresholds.max_changed_pixel_ratio:g}")
    return failures


def _classify(
    metrics: dict[str, Any],
    regions: list[VisualDiffRegion],
    failures: list[str],
    thresholds: VisualParityThresholds,
) -> tuple[str, str, bool]:
    if "size_mismatch" in failures:
        return "SIZE_MISMATCH", "PAIRING_FIX", False
    if not failures:
        return "PASS", "NONE", True

    largest_ratio = regions[0].area_ratio if regions else 0.0
    changed = float(metrics.get("changed_pixel_ratio", 1.0))
    mad = float(metrics.get("mean_abs_diff", 1.0))
    ssim = float(metrics.get("ssim", 0.0))

    if (
        changed <= thresholds.render_noise_max_changed_pixel_ratio
        and mad <= thresholds.render_noise_max_mean_abs_diff
        and largest_ratio <= thresholds.render_noise_max_region_area_ratio
    ):
        return "RENDER_NOISE_OK", "RENDER_NOISE_OK", True

    if (
        changed >= thresholds.strong_fail_changed_pixel_ratio
        or largest_ratio >= thresholds.strong_fail_region_area_ratio
        or mad >= thresholds.strong_fail_mean_abs_diff
        or (thresholds.min_ssim > 0 and ssim < max(0.0, thresholds.min_ssim - 0.17))
    ):
        return "FAIL", "FIX_PRODUCT_STRONG", False

    return "FAIL", "FIX_PRODUCT_REVIEW", False


def _metrics(
    target: Image.Image,
    actual: Image.Image,
    changed_pixel_floor: int,
) -> tuple[dict[str, Any], np.ndarray]:
    size_mismatch = target.size != actual.size
    original_actual_size = actual.size
    actual_for_metrics = actual
    if size_mismatch:
        actual_for_metrics = actual.resize(target.size, Image.Resampling.LANCZOS)

    target_array = np.asarray(target)
    actual_array = np.asarray(actual_for_metrics)
    diff = np.abs(target_array.astype(np.int16) - actual_array.astype(np.int16))
    changed_mask = diff.max(axis=2) > changed_pixel_floor
    total_pixels = int(changed_mask.size)
    changed_pixels = int(changed_mask.sum())
    ssim = _global_ssim(target_array, actual_array)

    return (
        {
            "target_size": {"w": target.size[0], "h": target.size[1]},
            "actual_size": {"w": original_actual_size[0], "h": original_actual_size[1]},
            "size_mismatch": size_mismatch,
            "ssim": round(float(ssim), 5),
            "mean_abs_diff": round(float(diff.mean() / 255.0), 5),
            "max_abs_diff": round(float(diff.max() / 255.0), 5),
            "changed_pixel_floor": changed_pixel_floor,
            "changed_pixels": changed_pixels,
            "total_pixels": total_pixels,
            "changed_pixel_ratio": round(float(changed_pixels / total_pixels), 5)
            if total_pixels
            else 0.0,
        },
        changed_mask,
    )


def _load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


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


def _diff_regions(
    mask: np.ndarray,
    image_size: tuple[int, int],
    limit: int,
) -> list[VisualDiffRegion]:
    changed = int(mask.sum())
    if changed == 0:
        return []

    image_w, image_h = image_size
    if changed > 120_000:
        ys, xs = np.where(mask)
        return [
            _make_region(
                int(xs.min()),
                int(ys.min()),
                int(xs.max()),
                int(ys.max()),
                changed,
                image_w,
                image_h,
            )
        ]

    height, width = mask.shape
    visited = np.zeros(mask.shape, dtype=bool)
    regions: list[VisualDiffRegion] = []
    ys, xs = np.where(mask)
    for start_y, start_x in zip(ys.tolist(), xs.tolist()):
        if visited[start_y, start_x]:
            continue
        queue: deque[tuple[int, int]] = deque([(start_y, start_x)])
        visited[start_y, start_x] = True
        min_x = max_x = start_x
        min_y = max_y = start_y
        area = 0
        while queue:
            y, x = queue.popleft()
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if ny < 0 or nx < 0 or ny >= height or nx >= width:
                    continue
                if visited[ny, nx] or not mask[ny, nx]:
                    continue
                visited[ny, nx] = True
                queue.append((ny, nx))
        regions.append(_make_region(min_x, min_y, max_x, max_y, area, image_w, image_h))

    return sorted(regions, key=lambda region: region.area, reverse=True)[:limit]


def _make_region(
    min_x: int,
    min_y: int,
    max_x: int,
    max_y: int,
    area: int,
    image_w: int,
    image_h: int,
) -> VisualDiffRegion:
    w = max_x - min_x + 1
    h = max_y - min_y + 1
    area_ratio = area / float(max(1, image_w * image_h))
    if area_ratio > 0.25:
        hint = "global_state_or_layout"
    elif w > image_w * 0.65 or h > image_h * 0.65:
        hint = "layout_shift_or_spacing"
    elif area < 800:
        hint = "text_icon_or_antialiasing"
    else:
        hint = "component_region"
    return VisualDiffRegion(
        x=min_x,
        y=min_y,
        w=w,
        h=h,
        area=area,
        area_ratio=area_ratio,
        hint=hint,
    )


def _write_diff_image(
    target: Image.Image,
    actual: Image.Image,
    out_path: Path,
    regions: list[VisualDiffRegion],
) -> None:
    actual_for_diff = actual
    if target.size != actual.size:
        actual_for_diff = actual.resize(target.size, Image.Resampling.LANCZOS)

    diff = ImageChops.difference(target, actual_for_diff).convert("L")
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
    canvas.paste(actual_for_diff, (w, 0))
    canvas.paste(heat, (w * 2, 0))
    draw = ImageDraw.Draw(canvas)
    _label(draw, 0, "canonical")
    _label(draw, w, "actual")
    _label(draw, w * 2, "diff x4")
    for region in regions:
        rect_actual = (w + region.x, region.y, w + region.x + region.w, region.y + region.h)
        rect_heat = (w * 2 + region.x, region.y, w * 2 + region.x + region.w, region.y + region.h)
        draw.rectangle(rect_actual, outline=(255, 216, 77), width=2)
        draw.rectangle(rect_heat, outline=(255, 216, 77), width=2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _label(draw: ImageDraw.ImageDraw, x: int, text: str) -> None:
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle((x, 0, x + 110, 20), fill=(0, 0, 0))
    draw.text((x + 5, 5), text, fill=(255, 255, 255), font=font)


def _surface_out_dir(out_dir: Path, surface_key: str) -> Path:
    return out_dir / _safe_name(surface_key)


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "surface"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _parse_capture_filename(file_name: str) -> tuple[str, str, str, int, int] | None:
    match = _NAME_RE.match(Path(file_name).name)
    if not match:
        return None
    app, view, theme, width, height = match.groups()
    return app, view, theme, int(width), int(height)


def _strip_app_prefix(app: str, view: str) -> str:
    prefix = f"{app}-"
    return view[len(prefix) :] if view.startswith(prefix) else view


def _surface_lookup_keys(surface: CanonicalSurface) -> set[str]:
    app = surface.app
    view = surface.view
    theme = surface.theme
    full_view = f"{app}-{view}"
    return {
        surface.file.lower(),
        Path(surface.file).stem.lower(),
        surface.surface_key.lower(),
        f"{app}:{full_view}@{theme}",
        f"{app}:{view}:{theme}",
        f"{app}/{view}@{theme}",
        f"{app}-{view}-{theme}",
        f"{app}-{view}-{theme}-{surface.resolution}",
        f"{full_view}-{theme}",
        f"{full_view}-{theme}-{surface.resolution}",
    }


def _candidate_surface_keys(raw_key: str) -> list[str]:
    raw = str(raw_key).strip().replace("\\", "/").lower()
    if "/" in raw and raw.endswith(".png"):
        raw = Path(raw).name.lower()
    candidates = {raw}
    if raw.endswith(".png"):
        candidates.add(Path(raw).stem)
        parsed = _parse_capture_filename(raw)
        if parsed:
            app, view, theme, width, height = parsed
            resolution = f"{width}x{height}"
            candidates.update(
                {
                    f"{app}:{view}@{theme}",
                    f"{app}:{view}:{theme}",
                    f"{app}-{view}-{theme}",
                    f"{app}-{view}-{theme}-{resolution}",
                }
            )

    for pattern in (
        r"^(suite|hub)[:/](.+)@(light|dark)$",
        r"^(suite|hub):(.+):(light|dark)$",
        r"^(suite|hub)-(.+)-(light|dark)(?:-\d+x\d+)?$",
    ):
        match = re.match(pattern, raw)
        if not match:
            continue
        app, view, theme = match.groups()
        view = _strip_app_prefix(app, view)
        full_view = f"{app}-{view}"
        candidates.update(
            {
                f"{app}:{view}@{theme}",
                f"{app}:{full_view}@{theme}",
                f"{app}:{view}:{theme}",
                f"{app}/{view}@{theme}",
                f"{app}-{view}-{theme}",
                f"{full_view}-{theme}",
            }
        )
    return sorted(candidates)


def _summary(results: list[VisualParityResult]) -> dict[str, int]:
    summary = {
        "total": len(results),
        "passed": 0,
        "failed": 0,
        "pairing_fix": 0,
        "fix_product_strong": 0,
        "fix_product_review": 0,
        "render_noise_ok": 0,
    }
    for result in results:
        if result.passed:
            summary["passed"] += 1
        else:
            summary["failed"] += 1
        if result.repair_decision == "PAIRING_FIX":
            summary["pairing_fix"] += 1
        elif result.repair_decision == "FIX_PRODUCT_STRONG":
            summary["fix_product_strong"] += 1
        elif result.repair_decision == "FIX_PRODUCT_REVIEW":
            summary["fix_product_review"] += 1
        elif result.repair_decision == "RENDER_NOISE_OK":
            summary["render_noise_ok"] += 1
    return summary


def _repair_queue_markdown(results: list[VisualParityResult]) -> str:
    summary = _summary(results)
    lines = [
        "# E2E visual parity repair queue",
        "",
        f"Total: {summary['total']}",
        f"Passed: {summary['passed']}",
        f"Failed: {summary['failed']}",
        "",
        "| Status | Decision | Surface | Changed | MAD | Diff |",
        "|---|---|---|---:|---:|---|",
    ]
    for result in results:
        metrics = result.metrics
        lines.append(
            "| {status} | {decision} | {surface} | {changed} | {mad} | {diff} |".format(
                status=result.status,
                decision=result.repair_decision,
                surface=result.surface_key,
                changed=metrics.get("changed_pixel_ratio", ""),
                mad=metrics.get("mean_abs_diff", ""),
                diff=result.diff_path or "",
            )
        )
    lines.append("")
    return "\n".join(lines)
