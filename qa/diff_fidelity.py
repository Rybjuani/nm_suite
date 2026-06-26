"""Compare mockup targets against PyQt captures.

The report is intentionally file-name driven. Both capture_mockup.py and
capture_v8.py use names shaped as:

    {app}-{view}-{theme}-{width}x{height}.png
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import sys
import tempfile as _tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont


_PROJ = Path(__file__).resolve().parent.parent
_DEFAULT_TARGETS = _PROJ / "qa" / "_mockup_canonical"
_DEFAULT_ACTUALS = _PROJ / "qa" / "_captures_v8"
_DEFAULT_OUT = _PROJ / "qa" / "_fidelity_diff"
_NAME_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+x\d+)\.png$")
_DEFAULT_MIN_SSIM = 0.92
_DEFAULT_MAX_MEAN_ABS_DIFF = 0.035
_DEFAULT_MAX_CHANGED_PIXEL_RATIO = 0.08


@dataclass(frozen=True)
class CaptureName:
    app: str
    view: str
    theme: str
    resolution: str
    path: Path

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.app, self.view, self.theme, self.resolution)


@dataclass(frozen=True)
class FidelityThresholds:
    min_ssim: float = _DEFAULT_MIN_SSIM
    max_mean_abs_diff: float = _DEFAULT_MAX_MEAN_ABS_DIFF
    max_changed_pixel_ratio: float = _DEFAULT_MAX_CHANGED_PIXEL_RATIO


def parse_capture_name(path: Path) -> CaptureName | None:
    match = _NAME_RE.match(path.name)
    if not match:
        return None
    app, view, theme, resolution = match.groups()
    return CaptureName(app=app, view=view, theme=theme, resolution=resolution, path=path)


def _index_images(root: Path) -> dict[tuple[str, str, str, str], CaptureName]:
    indexed: dict[tuple[str, str, str, str], CaptureName] = {}
    if not root.exists():
        return indexed
    for path in root.rglob("*.png"):
        parsed = parse_capture_name(path)
        if parsed:
            indexed[parsed.key] = parsed
    return indexed


def _load_capture_manifest(actual_dir: Path) -> dict[tuple[str, str, str, str], dict]:
    manifest_path = actual_dir / "CAPTURE_MANIFEST.json"
    if not manifest_path.exists():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    indexed: dict[tuple[str, str, str, str], dict] = {}
    for result in manifest.get("results", []):
        fname = result.get("file")
        if not fname:
            continue
        parsed = parse_capture_name(Path(str(fname)))
        if parsed:
            indexed[parsed.key] = result
    return indexed


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


def _ssim(a: np.ndarray, b: np.ndarray) -> tuple[float, str]:
    try:
        from skimage.metrics import structural_similarity

        value = structural_similarity(a, b, channel_axis=2, data_range=255)
        return float(value), "skimage"
    except Exception:
        return _global_ssim(a, b), "global"


def _metrics(target: Image.Image, actual: Image.Image) -> dict[str, float | str | bool]:
    size_mismatch = target.size != actual.size
    if size_mismatch:
        actual = actual.resize(target.size, Image.Resampling.LANCZOS)

    t = np.asarray(target)
    a = np.asarray(actual)
    diff = np.abs(t.astype(np.int16) - a.astype(np.int16))
    ssim_value, method = _ssim(t, a)
    return {
        "ssim": round(float(ssim_value), 5),
        "ssim_method": method,
        "mean_abs_diff": round(float(diff.mean() / 255.0), 5),
        "max_abs_diff": round(float(diff.max() / 255.0), 5),
        "changed_pixel_ratio": round(float((diff.max(axis=2) > 12).mean()), 5),
        "size_mismatch": size_mismatch,
    }


def _threshold_failures(
    metrics: dict[str, float | str | bool],
    thresholds: FidelityThresholds,
) -> list[str]:
    failures: list[str] = []
    if metrics.get("size_mismatch"):
        failures.append("size_mismatch")
    if float(metrics.get("ssim", 0.0)) < thresholds.min_ssim:
        failures.append(f"ssim<{thresholds.min_ssim:g}")
    if float(metrics.get("mean_abs_diff", 1.0)) > thresholds.max_mean_abs_diff:
        failures.append(f"mad>{thresholds.max_mean_abs_diff:g}")
    if float(metrics.get("changed_pixel_ratio", 1.0)) > thresholds.max_changed_pixel_ratio:
        failures.append(f"changed>{thresholds.max_changed_pixel_ratio:g}")
    return failures


def _capture_evidence_failures(manifest_result: dict | None) -> list[str]:
    if not manifest_result:
        return []
    failures: list[str] = []
    if manifest_result.get("technical_capture_valid") is False:
        failures.append("capture_technical_invalid")
    if manifest_result.get("state_evidence_valid") is False:
        failures.append("capture_state_not_product_evidence")
    return failures


def _acceptance_status(
    metrics: dict[str, float | str | bool],
    thresholds: FidelityThresholds,
    manifest_result: dict | None,
) -> tuple[str, list[str]]:
    metric_failures = _threshold_failures(metrics, thresholds)
    evidence_failures = _capture_evidence_failures(manifest_result)
    failures = metric_failures + evidence_failures
    if metric_failures:
        return "FAIL", failures
    if evidence_failures:
        return "PARTIAL_CAPTURE_EVIDENCE", failures
    return "PASS", failures


def _label(draw: ImageDraw.ImageDraw, x: int, text: str) -> None:
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle((x, 0, x + 220, 22), fill=(0, 0, 0))
    draw.text((x + 6, 6), text, fill=(255, 255, 255), font=font)


def _write_diff_image(target: Image.Image, actual: Image.Image, out_path: Path) -> None:
    if target.size != actual.size:
        actual = actual.resize(target.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(target, actual).convert("L")
    heat = Image.merge("RGB", (diff.point(lambda p: min(255, p * 4)), diff.point(lambda _: 0), diff.point(lambda _: 0)))
    w, h = target.size
    canvas = Image.new("RGB", (w * 3, h), "white")
    canvas.paste(target, (0, 0))
    canvas.paste(actual, (w, 0))
    canvas.paste(heat, (w * 2, 0))
    draw = ImageDraw.Draw(canvas)
    _label(draw, 0, "mockup target")
    _label(draw, w, "qt capture")
    _label(draw, w * 2, "abs diff x4")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _matches_filters(parsed: CaptureName, app: str | None, view: str, theme: str) -> bool:
    if app and parsed.app != app:
        return False
    if view and parsed.view != view:
        normalized = view
        if parsed.app == "suite" and normalized.startswith("suite-"):
            normalized = normalized[6:]
        if parsed.app == "hub" and normalized.startswith("hub-"):
            normalized = normalized[4:]
        if parsed.view != normalized:
            return False
    if theme != "both" and parsed.theme != theme:
        return False
    return True


def _write_reports(rows: list[dict], out_dir: Path, thresholds: FidelityThresholds) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "FIDELITY_REPORT.csv"
    md_path = out_dir / "FIDELITY_REPORT.md"
    json_path = out_dir / "FIDELITY_REPORT.json"

    fields = [
        "app",
        "view",
        "theme",
        "resolution",
        "status",
        "ssim",
        "ssim_method",
        "mean_abs_diff",
        "max_abs_diff",
        "changed_pixel_ratio",
        "size_mismatch",
        "acceptance_failures",
        "capture_status",
        "capture_technical_valid",
        "capture_state_valid",
        "capture_evidence_flags",
        "target_file",
        "actual_file",
        "diff_file",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    lines = [
        "# Fidelity diff report",
        "",
        f"Generated: {_dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "Acceptance gate:",
        f"- SSIM >= {thresholds.min_ssim:g}",
        f"- mean_abs_diff <= {thresholds.max_mean_abs_diff:g}",
        f"- changed_pixel_ratio <= {thresholds.max_changed_pixel_ratio:g}",
        "- capture manifest evidence, when present, must be technically valid and state-valid",
        "",
        "| Status | App | View | Theme | Res | SSIM | MAD | Changed | Diff |",
        "|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        diff_file = row.get("diff_file") or ""
        lines.append(
            "| {status} | {app} | {view} | {theme} | {resolution} | {ssim} | {mad} | {changed} | {diff} |".format(
                status=row.get("status", ""),
                app=row.get("app", ""),
                view=row.get("view", ""),
                theme=row.get("theme", ""),
                resolution=row.get("resolution", ""),
                ssim=row.get("ssim", ""),
                mad=row.get("mean_abs_diff", ""),
                changed=row.get("changed_pixel_ratio", ""),
                diff=diff_file,
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"csv": str(csv_path), "markdown": str(md_path), "json": str(json_path)}


def compare_legacy(
    target_dir: Path,
    actual_dir: Path,
    out_dir: Path,
    *,
    app: str | None,
    view: str,
    theme: str,
    thresholds: FidelityThresholds,
    write_images: bool,
    use_capture_manifest: bool = True,
) -> tuple[int, list[dict], dict[str, str]]:
    targets = _index_images(target_dir)
    actuals = _index_images(actual_dir)
    manifest = _load_capture_manifest(actual_dir) if use_capture_manifest else {}
    rows: list[dict] = []

    for key in sorted(targets):
        target = targets[key]
        if not _matches_filters(target, app, view, theme):
            continue
        actual = actuals.get(key)
        row: dict = {
            "app": target.app,
            "view": target.view,
            "theme": target.theme,
            "resolution": target.resolution,
            "target_file": str(target.path),
            "actual_file": str(actual.path) if actual else "",
        }
        if actual is None:
            row["status"] = "MISSING_ACTUAL"
            rows.append(row)
            continue

        target_img = _load_rgb(target.path)
        actual_img = _load_rgb(actual.path)
        metrics = _metrics(target_img, actual_img)
        row.update(metrics)
        manifest_result = manifest.get(key)
        if manifest_result:
            row["capture_status"] = manifest_result.get("capture_status", "")
            row["capture_technical_valid"] = manifest_result.get("technical_capture_valid", "")
            row["capture_state_valid"] = manifest_result.get("state_evidence_valid", "")
            row["capture_evidence_flags"] = ",".join(manifest_result.get("evidence_flags") or [])
        status, acceptance_failures = _acceptance_status(metrics, thresholds, manifest_result)
        row["status"] = status
        row["acceptance_failures"] = ",".join(acceptance_failures)
        if write_images:
            diff_path = out_dir / f"{target.app}-{target.view}-{target.theme}-{target.resolution}-diff.png"
            _write_diff_image(target_img, actual_img, diff_path)
            row["diff_file"] = str(diff_path)
        rows.append(row)

    report_paths = _write_reports(rows, out_dir, thresholds)
    failures = sum(1 for row in rows if row.get("status") != "PASS")
    return failures, rows, report_paths


def compare_odiff(
    target_dir: Path,
    actual_dir: Path,
    out_dir: Path,
    *,
    app: str | None,
    view: str,
    theme: str,
    write_images: bool = True,
    threshold: float = 0.1,
    # Acceptance is aligned to the owner's existing changed-pixel tolerance
    # (FidelityThresholds.max_changed_pixel_ratio = 0.08 → 8%). odiff_pct measures
    # the same dimension (fraction of differing pixels) but antialiasing-aware, so
    # using 8% keeps odiff and the SSIM gate comparing like-for-like.
    max_diff_pct: float = 8.0,
) -> tuple[int, list[dict], dict[str, str]]:
    """Compare images using odiff with --antialiasing (preferred over SSIM legacy).

    Returns (failures, rows, report_paths) shaped like compare_legacy so the
    CLI can use either engine interchangeably.
    """
    try:
        from odiff_runner import compare_with_odiff  # run as script (qa/ on sys.path)
    except ModuleNotFoundError:
        from qa.odiff_runner import compare_with_odiff  # imported as package

    targets = _index_images(target_dir)
    actuals = _index_images(actual_dir)
    rows: list[dict] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for key in sorted(targets):
        target = targets[key]
        if not _matches_filters(target, app, view, theme):
            continue
        actual = actuals.get(key)
        row: dict = {
            "app": target.app,
            "view": target.view,
            "theme": target.theme,
            "resolution": target.resolution,
            "target_file": str(target.path),
            "actual_file": str(actual.path) if actual else "",
        }
        if actual is None:
            row["status"] = "MISSING_ACTUAL"
            rows.append(row)
            continue

        # odiff always needs an output path; when images are disabled, route it
        # to a throwaway temp file so we never write into the canonical source dir.
        diff_name = f"{target.app}-{target.view}-{target.theme}-{target.resolution}-odiff.png"
        diff_png = (out_dir / diff_name) if write_images else (Path(_tempfile.gettempdir()) / diff_name)
        try:
            result = compare_with_odiff(target.path, actual.path, diff_png, threshold=threshold)
            row["diff_pixels"] = result["diff_pixels"]
            row["diff_percentage"] = result["diff_percentage"]
            row["diff_png_path"] = result["diff_png_path"]
            if result["match"]:
                row["status"] = "PASS"
            elif float(result["diff_percentage"]) <= max_diff_pct:
                row["status"] = "PASS"
            else:
                row["status"] = "FAIL"
                row["acceptance_failures"] = f"odiff_diff_pct>{max_diff_pct:g}"
            row["diff_file"] = result["diff_png_path"]
        except Exception as exc:
            row["status"] = "FAIL"
            row["acceptance_failures"] = f"odiff_error:{exc}"
        rows.append(row)

    report_paths = _write_reports(rows, out_dir, FidelityThresholds())
    failures = sum(1 for row in rows if row.get("status") != "PASS")
    return failures, rows, report_paths


# Backwards-compat alias: compare() now dispatches to the requested engine.
def compare(
    target_dir: Path,
    actual_dir: Path,
    out_dir: Path,
    *,
    app: str | None,
    view: str,
    theme: str,
    thresholds: FidelityThresholds,
    write_images: bool,
    use_capture_manifest: bool = True,
    engine: str = "odiff",
) -> tuple[int, list[dict], dict[str, str]]:
    if engine == "odiff":
        return compare_odiff(
            target_dir, actual_dir, out_dir,
            app=app, view=view, theme=theme,
            write_images=write_images,
        )
    return compare_legacy(
        target_dir, actual_dir, out_dir,
        app=app, view=view, theme=theme,
        thresholds=thresholds, write_images=write_images,
        use_capture_manifest=use_capture_manifest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff mockup targets against PyQt captures")
    parser.add_argument("--target-dir", default=str(_DEFAULT_TARGETS))
    parser.add_argument("--actual-dir", default=str(_DEFAULT_ACTUALS))
    parser.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    parser.add_argument("--app", choices=["suite", "hub"])
    parser.add_argument("--view", default="")
    parser.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    parser.add_argument("--fail-under", type=float, default=_DEFAULT_MIN_SSIM)
    parser.add_argument("--max-mean-abs-diff", type=float, default=_DEFAULT_MAX_MEAN_ABS_DIFF)
    parser.add_argument("--max-changed-pixel-ratio", type=float, default=_DEFAULT_MAX_CHANGED_PIXEL_RATIO)
    parser.add_argument("--ignore-capture-manifest", action="store_true")
    parser.add_argument("--no-images", action="store_true", help="Skip side-by-side diff images")
    parser.add_argument("--engine", choices=["odiff", "ssim"], default="odiff",
                        help="Comparison engine: 'odiff' (default, antialiasing-aware) or 'ssim' (legacy)")
    args = parser.parse_args()
    thresholds = FidelityThresholds(
        min_ssim=args.fail_under,
        max_mean_abs_diff=args.max_mean_abs_diff,
        max_changed_pixel_ratio=args.max_changed_pixel_ratio,
    )

    failures, rows, report_paths = compare(
        Path(args.target_dir),
        Path(args.actual_dir),
        Path(args.out_dir),
        app=args.app,
        view=args.view,
        theme=args.theme,
        thresholds=thresholds,
        write_images=not args.no_images,
        use_capture_manifest=not args.ignore_capture_manifest,
        engine=args.engine,
    )

    compared = sum(1 for row in rows if row.get("status") in {"PASS", "FAIL"})
    missing = sum(1 for row in rows if row.get("status") == "MISSING_ACTUAL")
    partial = sum(1 for row in rows if row.get("status") == "PARTIAL_CAPTURE_EVIDENCE")
    passed = sum(1 for row in rows if row.get("status") == "PASS")

    print("=" * 60)
    print("FIDELITY DIFF")
    print(
        "Gate:                "
        f"SSIM>={thresholds.min_ssim:g}, "
        f"MAD<={thresholds.max_mean_abs_diff:g}, "
        f"Changed<={thresholds.max_changed_pixel_ratio:g}"
    )
    print(f"Targets considered: {len(rows)}")
    print(f"Compared:           {compared}")
    print(f"Passed:             {passed}")
    print(f"Partial evidence:   {partial}")
    print(f"Missing actuals:    {missing}")
    print(f"Failures:           {failures}")
    print(f"Report:             {report_paths['markdown']}")
    print("=" * 60)

    if not rows:
        print("[ERROR] No target images matched the selected filters.", file=sys.stderr)
        return 1
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
