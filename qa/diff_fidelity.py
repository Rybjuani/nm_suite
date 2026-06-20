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
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont


_PROJ = Path(__file__).resolve().parent.parent
_DEFAULT_TARGETS = _PROJ / "qa" / "_mockup_targets"
_DEFAULT_ACTUALS = _PROJ / "qa" / "_captures_v8"
_DEFAULT_OUT = _PROJ / "qa" / "_fidelity_diff"
_NAME_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+x\d+)\.png$")


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


def _write_reports(rows: list[dict], out_dir: Path) -> dict[str, str]:
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


def compare(
    target_dir: Path,
    actual_dir: Path,
    out_dir: Path,
    *,
    app: str | None,
    view: str,
    theme: str,
    fail_under: float,
    write_images: bool,
) -> tuple[int, list[dict], dict[str, str]]:
    targets = _index_images(target_dir)
    actuals = _index_images(actual_dir)
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
        row.update(_metrics(target_img, actual_img))
        row["status"] = "PASS" if float(row["ssim"]) >= fail_under else "FAIL"
        if write_images:
            diff_path = out_dir / f"{target.app}-{target.view}-{target.theme}-{target.resolution}-diff.png"
            _write_diff_image(target_img, actual_img, diff_path)
            row["diff_file"] = str(diff_path)
        rows.append(row)

    report_paths = _write_reports(rows, out_dir)
    failures = sum(1 for row in rows if row.get("status") != "PASS")
    return failures, rows, report_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff mockup targets against PyQt captures")
    parser.add_argument("--target-dir", default=str(_DEFAULT_TARGETS))
    parser.add_argument("--actual-dir", default=str(_DEFAULT_ACTUALS))
    parser.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    parser.add_argument("--app", choices=["suite", "hub"])
    parser.add_argument("--view", default="")
    parser.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    parser.add_argument("--fail-under", type=float, default=0.92)
    parser.add_argument("--no-images", action="store_true", help="Skip side-by-side diff images")
    args = parser.parse_args()

    failures, rows, report_paths = compare(
        Path(args.target_dir),
        Path(args.actual_dir),
        Path(args.out_dir),
        app=args.app,
        view=args.view,
        theme=args.theme,
        fail_under=args.fail_under,
        write_images=not args.no_images,
    )

    compared = sum(1 for row in rows if row.get("status") in {"PASS", "FAIL"})
    missing = sum(1 for row in rows if row.get("status") == "MISSING_ACTUAL")
    passed = sum(1 for row in rows if row.get("status") == "PASS")

    print("=" * 60)
    print("FIDELITY DIFF")
    print(f"Targets considered: {len(rows)}")
    print(f"Compared:           {compared}")
    print(f"Passed:             {passed}")
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
