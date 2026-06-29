#!/usr/bin/env python3
"""Layered visual comparison for canonical mockups vs runtime captures.

This comparator is intentionally stricter than qa/diff_fidelity.py. It keeps
odiff as one layer, but it also records raw pixel deltas, rough layout drift,
size/pairing mismatches, and state-sensitive surfaces. A surface can therefore
be flagged even when odiff considers it acceptable.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont


_PROJ = Path(__file__).resolve().parent.parent
_NAME_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+)x(\d+)\.png$")
_DEFAULT_CANONICAL = _PROJ / "qa" / "_mockup_canonical"
_DEFAULT_ACTUAL = _PROJ / "qa" / "_captures_v8"
_DEFAULT_OUT = _PROJ / "reports" / "qa" / "layered_visual_compare"
_HANDOFF_AUTHORITY = "LAYERED_VISUAL_COMPARE"
_ACTIVE_SOURCE_POLICY = (
    "Use qa/_mockup_canonical plus a fresh complete qa/_captures_v8 run for "
    "operational handoff decisions. Zip inputs are archive/forensics only and "
    "must not close VISUAL_REPAIR_HANDOFF.md items."
)

_STATE_SENSITIVE_EXACT = {
    "suite:actividades-filtered",
    "suite:actividades-marked-hice",
    "suite:avisos-filter-activos",
    "suite:avisos-search",
    "suite:avisos-today",
    "suite:dbt-practice-stop",
    "suite:recuperar-acceso",
    "suite:respiracion-paused",
    "suite:respiracion-running",
    "suite:timer-paused",
    "suite:timer-running",
    "hub:detalle-resumen-ia-0",
}
_STATE_SENSITIVE_PREFIXES = (
    "suite:onboarding",
    "suite:registro",
)

# SUSPICIOUS_PERFECT_MATCH detection.
# A runtime Qt capture that is pixel-identical to a Chromium-rendered canonical
# (ssim=1.0 / mad=0.0 / changed=0) on a NON-trivial surface is not physically
# plausible and is the signature of a reference-artifact injection (see the
# recovery overlay fraud). Such a result is flagged and blocks closure pending
# audit. Trivial surfaces are exempt by an explicit, tested rule:
#   - empty-state views (name ends with ``-empty``), and
#   - flat / near-constant canonicals (grayscale std below the epsilon, e.g.
#     solid test fixtures) where a perfect match carries no information.
_TRIVIAL_SURFACE_STD = 2.0
_TRIVIAL_EMPTY_VIEW_SUFFIX = "-empty"


@dataclass(frozen=True)
class CaptureRef:
    app: str
    view: str
    theme: str
    width: int
    height: int
    path: Path

    @property
    def key(self) -> str:
        return f"{self.app}:{self.view}@{self.theme}"

    @property
    def family_key(self) -> str:
        return f"{self.app}:{self.view}"

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def filename(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class LayeredThresholds:
    min_ssim: float = 0.92
    # Density-aware SSIM gate (calibration-derived, see reports/qa/
    # visual_gate_calibration and the handoff "Gate Hardening" section).
    # Global single-window SSIM has a hard ~0.55 floor on text-dense, low-contrast
    # surfaces (520x600 forms) set by Qt-vs-Chromium text rasterisation — it is
    # unreachable by any honest render. For such surfaces (canonical grayscale std
    # below ``text_dense_canonical_std``) the SSIM layer uses the standard
    # *windowed* SSIM with ``text_dense_min_windowed_ssim`` instead. This only
    # changes the SSIM layer; mean_abs_diff, changed_pixel_ratio, bbox/layout,
    # region and odiff layers stay at full strength for every surface, and the
    # anti-fraud controls (static scan + SUSPICIOUS_PERFECT_MATCH) are unchanged.
    text_dense_canonical_std: float = 35.0
    text_dense_min_windowed_ssim: float = 0.65
    max_mean_abs_diff: float = 0.035
    max_changed_pixel_ratio: float = 0.08
    changed_pixel_floor: int = 12
    max_odiff_diff_pct: float = 8.0
    odiff_threshold: float = 0.3
    max_bbox_shift_px: int = 18
    max_bbox_size_delta_px: int = 36
    max_largest_region_ratio: float = 0.08
    strong_changed_pixel_ratio: float = 0.18
    strong_mean_abs_diff: float = 0.08
    strong_largest_region_ratio: float = 0.18

    def to_dict(self) -> dict[str, float | int]:
        return {
            "min_ssim": self.min_ssim,
            "text_dense_canonical_std": self.text_dense_canonical_std,
            "text_dense_min_windowed_ssim": self.text_dense_min_windowed_ssim,
            "max_mean_abs_diff": self.max_mean_abs_diff,
            "max_changed_pixel_ratio": self.max_changed_pixel_ratio,
            "changed_pixel_floor": self.changed_pixel_floor,
            "max_odiff_diff_pct": self.max_odiff_diff_pct,
            "odiff_threshold": self.odiff_threshold,
            "max_bbox_shift_px": self.max_bbox_shift_px,
            "max_bbox_size_delta_px": self.max_bbox_size_delta_px,
            "max_largest_region_ratio": self.max_largest_region_ratio,
            "strong_changed_pixel_ratio": self.strong_changed_pixel_ratio,
            "strong_mean_abs_diff": self.strong_mean_abs_diff,
            "strong_largest_region_ratio": self.strong_largest_region_ratio,
        }


@dataclass
class DiffRegion:
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
class LayeredResult:
    key: str
    app: str
    view: str
    theme: str
    status: str
    severity: str
    repair_bucket: str
    real_divergence: bool
    findings: list[str] = field(default_factory=list)
    suspicious_perfect_match: bool = False
    canonical_file: str = ""
    actual_file: str = ""
    canonical_size: str = ""
    actual_size: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    layout: dict[str, Any] = field(default_factory=dict)
    odiff: dict[str, Any] = field(default_factory=dict)
    regions: list[DiffRegion] = field(default_factory=list)
    panel_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "app": self.app,
            "view": self.view,
            "theme": self.theme,
            "status": self.status,
            "severity": self.severity,
            "repair_bucket": self.repair_bucket,
            "real_divergence": self.real_divergence,
            "suspicious_perfect_match": self.suspicious_perfect_match,
            "findings": self.findings,
            "canonical_file": self.canonical_file,
            "actual_file": self.actual_file,
            "canonical_size": self.canonical_size,
            "actual_size": self.actual_size,
            "metrics": self.metrics,
            "layout": self.layout,
            "odiff": self.odiff,
            "regions": [region.to_dict() for region in self.regions],
            "panel_path": self.panel_path,
        }

    def csv_row(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "status": self.status,
            "severity": self.severity,
            "repair_bucket": self.repair_bucket,
            "real_divergence": self.real_divergence,
            "suspicious_perfect_match": self.suspicious_perfect_match,
            "findings": ",".join(self.findings),
            "raw_changed_ratio": self.metrics.get("changed_pixel_ratio", ""),
            "mean_abs_diff": self.metrics.get("mean_abs_diff", ""),
            "ssim": self.metrics.get("ssim", ""),
            "odiff_pct": self.odiff.get("diff_percentage", ""),
            "max_bbox_delta_px": self.layout.get("max_bbox_delta_px", ""),
            "largest_region_ratio": self.metrics.get("largest_region_ratio", ""),
            "canonical_file": self.canonical_file,
            "actual_file": self.actual_file,
            "panel_path": self.panel_path,
        }


@dataclass(frozen=True)
class ReportFilters:
    app: str | None = None
    view: str | None = None
    theme: str | None = None
    key: str | None = None
    keys_file: str | None = None
    keys_file_keys: tuple[str, ...] = ()

    @property
    def active(self) -> bool:
        return any((self.app, self.view, self.theme, self.key, self.keys_file))

    @property
    def scope(self) -> str:
        return "PARTIAL" if self.active else "FULL"

    @property
    def exact_keys(self) -> set[str]:
        keys = set(self.keys_file_keys)
        if self.key:
            keys.add(self.key)
        return keys

    def to_dict(self) -> dict[str, Any]:
        return {
            "app": self.app,
            "view": self.view,
            "theme": self.theme,
            "key": self.key,
            "keys_file": self.keys_file,
            "keys_file_keys": list(self.keys_file_keys),
        }


def parse_capture_name(path: Path) -> CaptureRef | None:
    match = _NAME_RE.match(path.name)
    if not match:
        return None
    app, view, theme, width, height = match.groups()
    return CaptureRef(
        app=app,
        view=view,
        theme=theme,
        width=int(width),
        height=int(height),
        path=path,
    )


def compare_sources(
    canonical_source: Path,
    actual_source: Path,
    out_dir: Path,
    *,
    thresholds: LayeredThresholds | None = None,
    use_odiff: bool = True,
    write_panels: bool = True,
    filters: ReportFilters | None = None,
) -> tuple[list[LayeredResult], dict[str, str]]:
    thresholds = thresholds or LayeredThresholds()
    filters = filters or ReportFilters()
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical_root = _resolve_source(canonical_source, out_dir / "_sources" / "canonical")
    actual_root = _resolve_source(actual_source, out_dir / "_sources" / "actual")

    canonical = _index_images(canonical_root)
    actual = _index_images(actual_root)
    keys = _filter_keys(sorted(set(canonical) | set(actual)), filters)
    results: list[LayeredResult] = []
    panel_dir = out_dir / "panels"
    if write_panels:
        panel_dir.mkdir(parents=True, exist_ok=True)

    odiff_dir = out_dir / "odiff"
    if use_odiff:
        odiff_dir.mkdir(parents=True, exist_ok=True)

    for key in keys:
        target = canonical.get(key)
        runtime = actual.get(key)
        result = compare_pair(
            key,
            target,
            runtime,
            thresholds=thresholds,
            use_odiff=use_odiff,
            odiff_dir=odiff_dir,
            panel_dir=panel_dir if write_panels else None,
        )
        results.append(result)

    reports = write_reports(
        results,
        out_dir,
        thresholds,
        canonical_source=canonical_source,
        actual_source=actual_source,
        canonical_root=canonical_root,
        actual_root=actual_root,
        use_odiff=use_odiff,
        write_panels=write_panels,
        filters=filters,
    )
    return results, reports


def compare_pair(
    key: str,
    canonical: CaptureRef | None,
    actual: CaptureRef | None,
    *,
    thresholds: LayeredThresholds | None = None,
    use_odiff: bool = False,
    odiff_dir: Path | None = None,
    panel_dir: Path | None = None,
) -> LayeredResult:
    thresholds = thresholds or LayeredThresholds()
    app, view, theme = _split_key(key, canonical, actual)

    if canonical is None:
        return LayeredResult(
            key=key,
            app=app,
            view=view,
            theme=theme,
            status="EXTRA_ACTUAL",
            severity="medium",
            repair_bucket="PAIRING_FIX",
            real_divergence=True,
            findings=["extra_actual"],
            actual_file=str(actual.path) if actual else "",
            actual_size=actual.resolution if actual else "",
        )
    if actual is None:
        return LayeredResult(
            key=key,
            app=app,
            view=view,
            theme=theme,
            status="MISSING_ACTUAL",
            severity="high",
            repair_bucket="PAIRING_FIX",
            real_divergence=True,
            findings=["missing_actual"],
            canonical_file=str(canonical.path),
            canonical_size=canonical.resolution,
        )

    target_img = _load_rgb(canonical.path)
    actual_img = _load_rgb(actual.path)
    size_mismatch = target_img.size != actual_img.size
    findings: list[str] = []
    odiff_result: dict[str, Any] = {}

    metrics, changed_mask = _image_metrics(target_img, actual_img, thresholds.changed_pixel_floor)
    regions = _diff_regions(changed_mask, target_img.size)
    largest_region_ratio = regions[0].area_ratio if regions else 0.0
    metrics["largest_region_ratio"] = round(float(largest_region_ratio), 6)
    layout = _layout_metrics(target_img, actual_img)

    if size_mismatch:
        findings.append("size_mismatch")
    raw_fail = _raw_fail(metrics, thresholds)
    if raw_fail:
        findings.append("raw_pixel_delta")

    layout_fail = _layout_fail(layout, largest_region_ratio, thresholds)
    if layout_fail:
        findings.append("layout_drift")

    state_sensitive = _is_state_sensitive(canonical.app, canonical.view)
    if state_sensitive and (raw_fail or layout_fail or size_mismatch):
        findings.append("state_or_recipe_suspect")

    if use_odiff and not size_mismatch:
        odiff_result = _run_odiff_layer(canonical.path, actual.path, odiff_dir, thresholds)
        if odiff_result.get("available") is False:
            findings.append("odiff_unavailable")
        elif float(odiff_result.get("diff_percentage", 0.0)) > thresholds.max_odiff_diff_pct:
            findings.append("odiff_delta")
        elif raw_fail or layout_fail:
            findings.append("qa_missed_raw_or_layout")

    repair_bucket = _repair_bucket(findings, metrics, layout, thresholds)
    severity = _severity(findings, metrics, layout, thresholds)
    real_divergence = bool(findings) and findings != ["odiff_unavailable"]
    status = "FAIL" if real_divergence else "PASS"
    if size_mismatch:
        status = "SIZE_MISMATCH"

    # SUSPICIOUS_PERFECT_MATCH: a pixel-identical capture on a non-trivial
    # surface is the signature of reference-artifact injection. Flag it and
    # block closure pending audit (overrides an otherwise-PASS verdict).
    suspicious_perfect_match = not size_mismatch and _is_suspicious_perfect_match(
        metrics, target_img, canonical.view
    )
    if suspicious_perfect_match:
        if "suspicious_perfect_match" not in findings:
            findings.append("suspicious_perfect_match")
        real_divergence = True
        status = "SUSPICIOUS_PERFECT_MATCH"
        severity = "high"
        repair_bucket = "AUDIT_REQUIRED"

    panel_path = ""
    if panel_dir is not None:
        panel_path = str(_write_panel(canonical, actual, target_img, actual_img, panel_dir, regions))

    return LayeredResult(
        key=key,
        app=canonical.app,
        view=canonical.view,
        theme=canonical.theme,
        status=status,
        severity=severity,
        repair_bucket=repair_bucket,
        real_divergence=real_divergence,
        suspicious_perfect_match=suspicious_perfect_match,
        findings=findings,
        canonical_file=str(canonical.path),
        actual_file=str(actual.path),
        canonical_size=f"{target_img.width}x{target_img.height}",
        actual_size=f"{actual_img.width}x{actual_img.height}",
        metrics=metrics,
        layout=layout,
        odiff=odiff_result,
        regions=regions,
        panel_path=panel_path,
    )


def write_reports(
    results: list[LayeredResult],
    out_dir: Path,
    thresholds: LayeredThresholds,
    *,
    canonical_source: Path | None = None,
    actual_source: Path | None = None,
    canonical_root: Path | None = None,
    actual_root: Path | None = None,
    use_odiff: bool = True,
    write_panels: bool = True,
    filters: ReportFilters | None = None,
) -> dict[str, str]:
    filters = filters or ReportFilters()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "LAYERED_VISUAL_REPORT.json"
    csv_path = out_dir / "LAYERED_VISUAL_REPORT.csv"
    md_path = out_dir / "LAYERED_VISUAL_REPORT.md"

    closure = _report_closure_allowed(
        results,
        canonical_source,
        actual_source,
        thresholds,
        use_odiff,
        write_panels,
        filters,
    )
    evidence = _report_evidence_valid(
        results,
        canonical_source,
        actual_source,
        thresholds,
        use_odiff,
        write_panels,
    )
    payload = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "authority": _HANDOFF_AUTHORITY,
        "source_policy": _ACTIVE_SOURCE_POLICY,
        "report_scope": filters.scope,
        "report_filters": filters.to_dict(),
        "report_evidence_valid": evidence["valid"],
        "report_evidence_reason": evidence["reason"],
        "handoff_closure_allowed": closure["allowed"],
        "handoff_closure_reason": closure["reason"],
        "sources": _source_metadata(
            canonical_source,
            actual_source,
            canonical_root,
            actual_root,
        ),
        "thresholds": thresholds.to_dict(),
        "summary": _summary(results),
        "results": [result.to_dict() for result in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = list(results[0].csv_row()) if results else []
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(result.csv_row())

    md_path.write_text(
        _markdown_report(
            results,
            thresholds,
            canonical_source=canonical_source,
            actual_source=actual_source,
            use_odiff=use_odiff,
            write_panels=write_panels,
            filters=filters,
        ),
        encoding="utf-8",
    )
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def _resolve_source(source: Path, extract_dir: Path) -> Path:
    source = Path(source)
    if source.is_dir():
        return source
    if source.is_file() and source.suffix.lower() == ".zip":
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)
        _safe_extract_zip(source, extract_dir)
        return extract_dir
    raise FileNotFoundError(f"Unsupported visual source: {source}")


def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            target = (destination / info.filename).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"Unsafe zip member path: {info.filename}")
        zf.extractall(destination)


def _index_images(root: Path) -> dict[str, CaptureRef]:
    indexed: dict[str, CaptureRef] = {}
    for path in sorted(root.rglob("*.png")):
        parsed = parse_capture_name(path)
        if parsed:
            indexed[parsed.key] = parsed
    return indexed


def _filter_keys(keys: list[str], filters: ReportFilters) -> list[str]:
    exact_keys = filters.exact_keys
    filtered: list[str] = []
    for key in keys:
        app, view, theme = _split_key(key, None, None)
        if exact_keys and key not in exact_keys:
            continue
        if filters.app and app != filters.app:
            continue
        if filters.view and view != filters.view:
            continue
        if filters.theme and filters.theme != "both" and theme != filters.theme:
            continue
        filtered.append(key)
    return filtered


def load_keys_file(path: Path) -> tuple[str, ...]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        keys.append(value)
    return tuple(keys)


def _split_key(
    key: str,
    canonical: CaptureRef | None,
    actual: CaptureRef | None,
) -> tuple[str, str, str]:
    ref = canonical or actual
    if ref:
        return ref.app, ref.view, ref.theme
    app, rest = key.split(":", 1)
    view, theme = rest.split("@", 1)
    return app, view, theme


def _load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _image_metrics(
    target: Image.Image,
    actual: Image.Image,
    changed_pixel_floor: int,
) -> tuple[dict[str, Any], np.ndarray]:
    actual_for_metrics = actual
    if target.size != actual.size:
        actual_for_metrics = actual.resize(target.size, Image.Resampling.LANCZOS)

    t = np.asarray(target)
    a = np.asarray(actual_for_metrics)
    diff = np.abs(t.astype(np.int16) - a.astype(np.int16))
    changed_mask = diff.max(axis=2) > changed_pixel_floor
    total_pixels = int(changed_mask.size)
    changed_pixels = int(changed_mask.sum())

    return (
        {
            "ssim": round(float(_global_ssim(t, a)), 5),
            "windowed_ssim": round(float(_windowed_ssim(t, a)), 5),
            "canonical_gray_std": round(float(_to_gray(t).std()), 3),
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


def _to_gray(arr: np.ndarray) -> np.ndarray:
    x = arr.astype(np.float64)
    if x.ndim == 3:
        x = 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    return x


def _box_mean(img: np.ndarray, win: int) -> np.ndarray:
    """Mean over every win x win window (stride 1, valid region) via integral image."""
    ii = np.cumsum(np.cumsum(img, axis=0), axis=1)
    ii = np.pad(ii, ((1, 0), (1, 0)))
    s = ii[win:, win:] - ii[:-win, win:] - ii[win:, :-win] + ii[:-win, :-win]
    return s / float(win * win)


def _windowed_ssim(a: np.ndarray, b: np.ndarray, win: int = 7) -> float:
    """Standard Wang et al. windowed SSIM (mean of the local SSIM map).

    Robust on low-variance / text-dense surfaces where the single-window
    ``_global_ssim`` is pathologically dominated by global covariance.
    """
    x = _to_gray(a) / 255.0
    y = _to_gray(b) / 255.0
    if min(x.shape) < win:
        return _global_ssim(a, b)
    mux = _box_mean(x, win)
    muy = _box_mean(y, win)
    vx = _box_mean(x * x, win) - mux * mux
    vy = _box_mean(y * y, win) - muy * muy
    cov = _box_mean(x * y, win) - mux * muy
    c1 = 0.01 ** 2
    c2 = 0.03 ** 2
    smap = ((2 * mux * muy + c1) * (2 * cov + c2)) / ((mux * mux + muy * muy + c1) * (vx + vy + c2))
    return float(np.clip(smap, -1.0, 1.0).mean())


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


def _diff_regions(mask: np.ndarray, image_size: tuple[int, int], limit: int = 8) -> list[DiffRegion]:
    changed = int(mask.sum())
    if changed == 0:
        return []
    image_w, image_h = image_size
    if changed > 120_000:
        ys, xs = np.where(mask)
        return [_make_region(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), changed, image_w, image_h)]

    height, width = mask.shape
    visited = np.zeros(mask.shape, dtype=bool)
    regions: list[DiffRegion] = []
    ys, xs = np.where(mask)
    for start_y, start_x in zip(ys.tolist(), xs.tolist()):
        if visited[start_y, start_x]:
            continue
        stack = [(start_y, start_x)]
        visited[start_y, start_x] = True
        min_x = max_x = start_x
        min_y = max_y = start_y
        area = 0
        while stack:
            y, x = stack.pop()
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
                stack.append((ny, nx))
        regions.append(_make_region(min_x, min_y, max_x, max_y, area, image_w, image_h))
    return sorted(regions, key=lambda r: r.area, reverse=True)[:limit]


def _make_region(
    min_x: int,
    min_y: int,
    max_x: int,
    max_y: int,
    area: int,
    image_w: int,
    image_h: int,
) -> DiffRegion:
    w = max_x - min_x + 1
    h = max_y - min_y + 1
    ratio = area / float(max(1, image_w * image_h))
    if ratio > 0.25:
        hint = "global_state_or_layout"
    elif w > image_w * 0.65 or h > image_h * 0.65:
        hint = "layout_shift_or_spacing"
    elif area < 800:
        hint = "text_icon_or_antialiasing"
    else:
        hint = "component_region"
    return DiffRegion(x=min_x, y=min_y, w=w, h=h, area=area, area_ratio=ratio, hint=hint)


def _layout_metrics(target: Image.Image, actual: Image.Image) -> dict[str, Any]:
    actual_for_metrics = actual
    if target.size != actual.size:
        actual_for_metrics = actual.resize(target.size, Image.Resampling.LANCZOS)
    target_bbox = _content_bbox(target)
    actual_bbox = _content_bbox(actual_for_metrics)
    if not target_bbox or not actual_bbox:
        return {
            "target_content_bbox": target_bbox,
            "actual_content_bbox": actual_bbox,
            "max_bbox_delta_px": None,
            "bbox_area_delta_ratio": None,
        }
    deltas = [abs(a - b) for a, b in zip(target_bbox, actual_bbox)]
    t_area = max(1, target_bbox[2] * target_bbox[3])
    a_area = max(1, actual_bbox[2] * actual_bbox[3])
    return {
        "target_content_bbox": target_bbox,
        "actual_content_bbox": actual_bbox,
        "bbox_dx": actual_bbox[0] - target_bbox[0],
        "bbox_dy": actual_bbox[1] - target_bbox[1],
        "bbox_dw": actual_bbox[2] - target_bbox[2],
        "bbox_dh": actual_bbox[3] - target_bbox[3],
        "max_bbox_delta_px": max(deltas),
        "bbox_area_delta_ratio": round(abs(a_area - t_area) / float(t_area), 5),
    }


def _content_bbox(image: Image.Image) -> list[int] | None:
    arr = np.asarray(image)
    h, w = arr.shape[:2]
    corner = min(24, h // 4, w // 4)
    if corner <= 0:
        return None
    samples = np.concatenate(
        [
            arr[:corner, :corner].reshape(-1, 3),
            arr[:corner, -corner:].reshape(-1, 3),
            arr[-corner:, :corner].reshape(-1, 3),
            arr[-corner:, -corner:].reshape(-1, 3),
        ],
        axis=0,
    )
    bg = np.median(samples, axis=0)
    bg_delta = np.abs(arr.astype(np.int16) - bg.astype(np.int16)).max(axis=2)
    luma = (
        0.2126 * arr[..., 0].astype(np.float32)
        + 0.7152 * arr[..., 1].astype(np.float32)
        + 0.0722 * arr[..., 2].astype(np.float32)
    )
    gx = np.zeros_like(luma)
    gy = np.zeros_like(luma)
    gx[:, 1:] = np.abs(luma[:, 1:] - luma[:, :-1])
    gy[1:, :] = np.abs(luma[1:, :] - luma[:-1, :])
    mask = (bg_delta > 16) | (gx > 7) | (gy > 7)
    if float(mask.mean()) > 0.92:
        mask = (gx > 10) | (gy > 10)
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    x0 = int(xs.min())
    y0 = int(ys.min())
    x1 = int(xs.max())
    y1 = int(ys.max())
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def _run_odiff_layer(
    target: Path,
    actual: Path,
    out_dir: Path | None,
    thresholds: LayeredThresholds,
) -> dict[str, Any]:
    try:
        try:
            from qa.odiff_runner import compare_with_odiff
        except ModuleNotFoundError:
            from odiff_runner import compare_with_odiff

        diff_path = None
        if out_dir:
            diff_path = out_dir / f"{target.stem}-odiff.png"
        result = compare_with_odiff(
            target,
            actual,
            diff_path,
            threshold=thresholds.odiff_threshold,
            antialiasing=True,
        )
        result["available"] = True
        result["accepted"] = float(result["diff_percentage"]) <= thresholds.max_odiff_diff_pct
        return result
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _raw_fail(metrics: dict[str, Any], thresholds: LayeredThresholds) -> bool:
    # Density-aware SSIM layer (see LayeredThresholds). Text-dense / low-contrast
    # canonicals use windowed SSIM; everything else keeps the strict global SSIM.
    # All other layers are unchanged for every surface.
    canon_std = float(metrics.get("canonical_gray_std", thresholds.text_dense_canonical_std + 1.0))
    if canon_std < thresholds.text_dense_canonical_std:
        ssim_fail = float(metrics.get("windowed_ssim", 1.0)) < thresholds.text_dense_min_windowed_ssim
    else:
        ssim_fail = float(metrics.get("ssim", 1.0)) < thresholds.min_ssim
    return (
        ssim_fail
        or float(metrics.get("mean_abs_diff", 0.0)) > thresholds.max_mean_abs_diff
        or float(metrics.get("changed_pixel_ratio", 0.0)) > thresholds.max_changed_pixel_ratio
    )


def _layout_fail(
    layout: dict[str, Any],
    largest_region_ratio: float,
    thresholds: LayeredThresholds,
) -> bool:
    max_delta = layout.get("max_bbox_delta_px")
    size_delta = max(abs(int(layout.get("bbox_dw") or 0)), abs(int(layout.get("bbox_dh") or 0)))
    return (
        (max_delta is not None and int(max_delta) > thresholds.max_bbox_shift_px)
        or size_delta > thresholds.max_bbox_size_delta_px
        or largest_region_ratio > thresholds.max_largest_region_ratio
    )


def _is_trivial_surface(canonical_img: Image.Image, view: str) -> bool:
    """A surface where a perfect pixel match carries no fraud signal.

    Explicit, tested exception for SUSPICIOUS_PERFECT_MATCH:
      - empty-state views (name ends with ``-empty``);
      - flat / near-constant canonicals (grayscale std below the epsilon),
        e.g. solid colour test fixtures.
    """
    if view.endswith(_TRIVIAL_EMPTY_VIEW_SUFFIX):
        return True
    arr = np.asarray(canonical_img.convert("L"), dtype=np.float64)
    return float(arr.std()) < _TRIVIAL_SURFACE_STD


def _is_suspicious_perfect_match(metrics: dict[str, Any], canonical_img: Image.Image, view: str) -> bool:
    perfect = (
        int(metrics.get("changed_pixels", -1)) == 0
        and float(metrics.get("mean_abs_diff", 1.0)) == 0.0
        and float(metrics.get("ssim", 0.0)) >= 1.0
    )
    return perfect and not _is_trivial_surface(canonical_img, view)


def _is_state_sensitive(app: str, view: str) -> bool:
    family_key = f"{app}:{view}"
    return family_key in _STATE_SENSITIVE_EXACT or any(
        family_key.startswith(prefix) for prefix in _STATE_SENSITIVE_PREFIXES
    )


def _repair_bucket(
    findings: list[str],
    metrics: dict[str, Any],
    layout: dict[str, Any],
    thresholds: LayeredThresholds,
) -> str:
    if any(f in findings for f in ("missing_actual", "extra_actual", "size_mismatch")):
        return "PAIRING_FIX"
    if "state_or_recipe_suspect" in findings:
        return "STATE_RECIPE_OR_PRODUCT_FIX"
    if "layout_drift" in findings:
        return "LAYOUT_FIX"
    if "raw_pixel_delta" in findings or "odiff_delta" in findings:
        return "VISUAL_STYLE_REVIEW"
    return "NONE"


def _severity(
    findings: list[str],
    metrics: dict[str, Any],
    layout: dict[str, Any],
    thresholds: LayeredThresholds,
) -> str:
    if any(f in findings for f in ("missing_actual", "size_mismatch", "odiff_delta")):
        return "high"
    if (
        float(metrics.get("changed_pixel_ratio", 0.0)) >= thresholds.strong_changed_pixel_ratio
        or float(metrics.get("mean_abs_diff", 0.0)) >= thresholds.strong_mean_abs_diff
        or float(metrics.get("largest_region_ratio", 0.0)) >= thresholds.strong_largest_region_ratio
    ):
        return "high"
    if findings:
        return "medium"
    return "none"


def _write_panel(
    canonical: CaptureRef,
    actual: CaptureRef,
    target: Image.Image,
    actual_img: Image.Image,
    out_dir: Path,
    regions: list[DiffRegion],
) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", canonical.key)
    out_path = out_dir / f"{safe}.png"
    target_fit = _fit(target)
    actual_fit = _fit(actual_img)
    heat_source = actual_img
    if target.size != actual_img.size:
        heat_source = actual_img.resize(target.size, Image.Resampling.LANCZOS)
    heat = _heatmap(target, heat_source)
    heat_fit = _fit(heat)
    panels = [
        _label_panel(target_fit, "CANONICAL", f"{canonical.filename} {target.width}x{target.height}"),
        _label_panel(actual_fit, "ACTUAL", f"{actual.filename} {actual_img.width}x{actual_img.height}"),
        _label_panel(heat_fit, "DIFF", "absolute RGB x4"),
    ]
    gap = 12
    width = sum(panel.width for panel in panels) + gap * (len(panels) - 1)
    height = max(panel.height for panel in panels)
    canvas = Image.new("RGB", (width, height), (235, 235, 235))
    x = 0
    for panel in panels:
        canvas.paste(panel, (x, 0))
        x += panel.width + gap
    draw = ImageDraw.Draw(canvas)
    target_x = panels[0].width + gap
    heat_x = panels[0].width + panels[1].width + gap * 2
    sx = actual_fit.width / max(1, target.width)
    sy = actual_fit.height / max(1, target.height)
    for region in regions[:4]:
        rect = (
            target_x + int(region.x * sx),
            48 + int(region.y * sy),
            target_x + int((region.x + region.w) * sx),
            48 + int((region.y + region.h) * sy),
        )
        draw.rectangle(rect, outline=(255, 208, 64), width=2)
        rect_heat = (
            heat_x + int(region.x * sx),
            48 + int(region.y * sy),
            heat_x + int((region.x + region.w) * sx),
            48 + int((region.y + region.h) * sy),
        )
        draw.rectangle(rect_heat, outline=(255, 208, 64), width=2)
    canvas.save(out_path)
    return out_path


def _fit(image: Image.Image, max_w: int = 420, max_h: int = 290) -> Image.Image:
    ratio = min(max_w / image.width, max_h / image.height, 1.0)
    return image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)


def _heatmap(target: Image.Image, actual: Image.Image) -> Image.Image:
    diff = ImageChops.difference(target, actual).convert("L")
    return Image.merge(
        "RGB",
        (
            diff.point(lambda p: min(255, p * 4)),
            diff.point(lambda _: 0),
            diff.point(lambda _: 0),
        ),
    )


def _label_panel(image: Image.Image, title: str, subtitle: str) -> Image.Image:
    label_h = 48
    canvas = Image.new("RGB", (image.width, image.height + label_h), (250, 250, 250))
    canvas.paste(image, (0, label_h))
    draw = ImageDraw.Draw(canvas)
    font = _font(14)
    small = _font(11)
    draw.text((6, 5), title, fill=(20, 20, 20), font=font)
    draw.text((6, 26), subtitle, fill=(80, 80, 80), font=small)
    return canvas


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _summary(results: list[LayeredResult]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total": len(results),
        "pass": 0,
        "real_divergence": 0,
        "by_status": {},
        "by_severity": {},
        "by_repair_bucket": {},
        "qa_missed_raw_or_layout": 0,
        "state_or_recipe_suspect": 0,
        "suspicious_perfect_match": 0,
    }
    for result in results:
        if result.status == "PASS":
            summary["pass"] += 1
        if result.suspicious_perfect_match:
            summary["suspicious_perfect_match"] += 1
        if result.real_divergence:
            summary["real_divergence"] += 1
        summary["by_status"][result.status] = summary["by_status"].get(result.status, 0) + 1
        summary["by_severity"][result.severity] = summary["by_severity"].get(result.severity, 0) + 1
        summary["by_repair_bucket"][result.repair_bucket] = (
            summary["by_repair_bucket"].get(result.repair_bucket, 0) + 1
        )
        if "qa_missed_raw_or_layout" in result.findings:
            summary["qa_missed_raw_or_layout"] += 1
        if "state_or_recipe_suspect" in result.findings:
            summary["state_or_recipe_suspect"] += 1
    return summary


def _source_metadata(
    canonical_source: Path | None,
    actual_source: Path | None,
    canonical_root: Path | None,
    actual_root: Path | None,
) -> dict[str, Any]:
    return {
        "canonical_source": str(canonical_source) if canonical_source else "",
        "actual_source": str(actual_source) if actual_source else "",
        "canonical_root": str(canonical_root) if canonical_root else "",
        "actual_root": str(actual_root) if actual_root else "",
        "canonical_source_kind": _source_kind(canonical_source),
        "actual_source_kind": _source_kind(actual_source),
        "active_repo_pair": _is_active_source_pair(canonical_source, actual_source),
    }


def _source_kind(source: Path | None) -> str:
    if source is None:
        return "unknown"
    source = Path(source)
    if source.suffix.lower() == ".zip":
        return "zip_archive"
    if source.is_dir():
        return "directory"
    return "unknown"


def _is_active_source_pair(canonical_source: Path | None, actual_source: Path | None) -> bool:
    if canonical_source is None or actual_source is None:
        return False
    try:
        return (
            Path(canonical_source).resolve() == _DEFAULT_CANONICAL.resolve()
            and Path(actual_source).resolve() == _DEFAULT_ACTUAL.resolve()
        )
    except OSError:
        return False


def _report_evidence_valid(
    results: list[LayeredResult],
    canonical_source: Path | None,
    actual_source: Path | None,
    thresholds: LayeredThresholds,
    use_odiff: bool,
    write_panels: bool,
) -> dict[str, Any]:
    reasons: list[str] = []
    if not _is_active_source_pair(canonical_source, actual_source):
        reasons.append("non_active_sources")
    if not results:
        reasons.append("empty_results")
    if thresholds != LayeredThresholds():
        reasons.append("non_default_thresholds")
    if not use_odiff:
        reasons.append("odiff_disabled")
    if not write_panels:
        reasons.append("panels_disabled")
    if reasons:
        return {"valid": False, "reason": "; ".join(reasons)}
    return {"valid": True, "reason": None}


def _report_closure_allowed(
    results: list[LayeredResult],
    canonical_source: Path | None,
    actual_source: Path | None,
    thresholds: LayeredThresholds,
    use_odiff: bool,
    write_panels: bool,
    filters: ReportFilters | None = None,
) -> dict[str, Any]:
    filters = filters or ReportFilters()
    evidence = _report_evidence_valid(
        results, canonical_source, actual_source, thresholds, use_odiff, write_panels
    )
    if not evidence["valid"]:
        return {"allowed": False, "reason": evidence["reason"]}
    reasons: list[str] = []
    if filters.scope == "PARTIAL":
        reasons.append("partial_scope")
    if any(result.status in {"MISSING_ACTUAL", "EXTRA_ACTUAL", "SIZE_MISMATCH"} for result in results):
        reasons.append("pairing_or_size_mismatch")
    if any(result.real_divergence for result in results):
        reasons.append("real_divergence_present")
    if reasons:
        return {"allowed": False, "reason": "; ".join(reasons)}
    return {"allowed": True, "reason": None}


def _markdown_report(
    results: list[LayeredResult],
    thresholds: LayeredThresholds,
    *,
    canonical_source: Path | None = None,
    actual_source: Path | None = None,
    use_odiff: bool = True,
    write_panels: bool = True,
    filters: ReportFilters | None = None,
) -> str:
    filters = filters or ReportFilters()
    summary = _summary(results)
    evidence = _report_evidence_valid(results, canonical_source, actual_source, thresholds, use_odiff, write_panels)
    closure = _report_closure_allowed(
        results, canonical_source, actual_source, thresholds, use_odiff, write_panels, filters
    )
    lines = [
        "# Layered visual comparison report",
        "",
        f"Generated: {_dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "Handoff policy:",
        f"- Authority: {_HANDOFF_AUTHORITY}",
        f"- {_ACTIVE_SOURCE_POLICY}",
        f"- Canonical source: `{canonical_source or _DEFAULT_CANONICAL}`",
        f"- Actual source: `{actual_source or _DEFAULT_ACTUAL}`",
        f"- REPORT_SCOPE: {filters.scope}",
        f"- REPORT_FILTERS: {filters.to_dict()}",
        f"- REPORT_EVIDENCE_VALID: {'YES' if evidence['valid'] else 'NO'}",
    ]
    if evidence["reason"]:
        lines.append(f"- REPORT_EVIDENCE_REASON: {evidence['reason']}")
    lines.append(f"- HANDOFF_CLOSURE_ALLOWED: {'YES' if closure['allowed'] else 'NO'}")
    if closure["reason"]:
        lines.append(f"- HANDOFF_CLOSURE_REASON: {closure['reason']}")
    lines.extend([
        "",
        "Thresholds:",
        f"- raw SSIM >= {thresholds.min_ssim:g}",
        f"- raw mean_abs_diff <= {thresholds.max_mean_abs_diff:g}",
        f"- raw changed_pixel_ratio <= {thresholds.max_changed_pixel_ratio:g}",
        f"- odiff diff_percentage <= {thresholds.max_odiff_diff_pct:g}",
        f"- content bbox shift <= {thresholds.max_bbox_shift_px}px",
        "",
        "Summary:",
        f"- Total: {summary['total']}",
        f"- Pass: {summary['pass']}",
        f"- Real divergences/review items: {summary['real_divergence']}",
        f"- QA missed raw/layout: {summary['qa_missed_raw_or_layout']}",
        f"- State or recipe suspects: {summary['state_or_recipe_suspect']}",
        f"- By repair bucket: {summary['by_repair_bucket']}",
        "",
        "| Severity | Status | Bucket | Key | Findings | Raw changed | ODiff % | BBox delta | Panel |",
        "|---|---|---|---|---|---:|---:|---:|---|",
    ])
    ordered = sorted(
        results,
        key=lambda r: (
            0 if r.severity == "high" else 1 if r.severity == "medium" else 2,
            -float(r.metrics.get("changed_pixel_ratio", 0.0) or 0.0),
            r.key,
        ),
    )
    for result in ordered:
        if result.status == "PASS":
            continue
        lines.append(
            "| {severity} | {status} | {bucket} | {key} | {findings} | {changed} | {odiff} | {bbox} | {panel} |".format(
                severity=result.severity,
                status=result.status,
                bucket=result.repair_bucket,
                key=result.key,
                findings=",".join(result.findings),
                changed=result.metrics.get("changed_pixel_ratio", ""),
                odiff=result.odiff.get("diff_percentage", ""),
                bbox=result.layout.get("max_bbox_delta_px", ""),
                panel=result.panel_path,
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Layered visual comparator for mockup canonical vs runtime captures")
    parser.add_argument("--canonical", default=str(_DEFAULT_CANONICAL))
    parser.add_argument("--actual", default=str(_DEFAULT_ACTUAL))
    parser.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    parser.add_argument("--app", choices=("suite", "hub"), help="Filter report to one app")
    parser.add_argument("--view", help="Filter report to one view id")
    parser.add_argument("--theme", choices=("light", "dark", "both"), help="Filter report to one theme")
    parser.add_argument("--key", help='Filter report to one exact key, e.g. "suite:dbt-practice-stop@light"')
    parser.add_argument("--keys-file", help="Filter report to exact keys listed one per line")
    parser.add_argument("--no-odiff", action="store_true", help="Disable odiff layer")
    parser.add_argument("--no-panels", action="store_true", help="Do not write side-by-side panels")
    parser.add_argument("--raw-changed-threshold", type=float, default=LayeredThresholds.max_changed_pixel_ratio)
    parser.add_argument("--raw-mad-threshold", type=float, default=LayeredThresholds.max_mean_abs_diff)
    parser.add_argument("--min-ssim", type=float, default=LayeredThresholds.min_ssim)
    parser.add_argument("--max-odiff-diff-pct", type=float, default=LayeredThresholds.max_odiff_diff_pct)
    parser.add_argument("--max-bbox-shift-px", type=int, default=LayeredThresholds.max_bbox_shift_px)
    args = parser.parse_args()

    thresholds = LayeredThresholds(
        min_ssim=args.min_ssim,
        max_mean_abs_diff=args.raw_mad_threshold,
        max_changed_pixel_ratio=args.raw_changed_threshold,
        max_odiff_diff_pct=args.max_odiff_diff_pct,
        max_bbox_shift_px=args.max_bbox_shift_px,
    )
    filters = ReportFilters(
        app=args.app,
        view=args.view,
        theme=args.theme,
        key=args.key,
        keys_file=args.keys_file,
        keys_file_keys=load_keys_file(Path(args.keys_file)) if args.keys_file else (),
    )
    results, reports = compare_sources(
        Path(args.canonical),
        Path(args.actual),
        Path(args.out_dir),
        thresholds=thresholds,
        use_odiff=not args.no_odiff,
        write_panels=not args.no_panels,
        filters=filters,
    )
    summary = _summary(results)
    print("=" * 60)
    print("LAYERED VISUAL COMPARE")
    print(f"Authority:             {_HANDOFF_AUTHORITY}")
    print(f"Canonical source:      {Path(args.canonical)}")
    print(f"Actual source:         {Path(args.actual)}")
    print(f"Report scope:          {filters.scope}")
    print(f"Report filters:        {filters.to_dict()}")
    evidence = _report_evidence_valid(
        results,
        Path(args.canonical),
        Path(args.actual),
        thresholds,
        not args.no_odiff,
        not args.no_panels,
    )
    closure = _report_closure_allowed(
        results,
        Path(args.canonical),
        Path(args.actual),
        thresholds,
        not args.no_odiff,
        not args.no_panels,
        filters,
    )
    print(
        "Report evidence valid: "
        f"{'YES' if evidence['valid'] else 'NO'}"
    )
    if evidence["reason"]:
        print(f"Evidence reason:       {evidence['reason']}")
    print(
        "Handoff closure:      "
        f"{'YES' if closure['allowed'] else 'NO'}"
    )
    if closure["reason"]:
        print(f"Closure reason:       {closure['reason']}")
    print(f"Source policy:         {_ACTIVE_SOURCE_POLICY}")
    print(f"Total:                 {summary['total']}")
    print(f"Pass:                  {summary['pass']}")
    print(f"Review/divergence:     {summary['real_divergence']}")
    print(f"QA missed raw/layout:  {summary['qa_missed_raw_or_layout']}")
    print(f"State/recipe suspects: {summary['state_or_recipe_suspect']}")
    print(f"Report:                {reports['markdown']}")
    print("=" * 60)
    return 1 if summary["real_divergence"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
