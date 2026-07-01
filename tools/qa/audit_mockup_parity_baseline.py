#!/usr/bin/env python3
"""Audit HTML mockup parity with a dynamic renderer-noise baseline.

The audit renders the official full capture recipe three times:

1. original A
2. original B
3. modified

Original A/B measures natural renderer noise. Original A/modified measures the
real visual delta. A capture passes when the modified delta fits inside the
dynamic allowance derived from the A/B baseline:

    mod_mean <= max(baseline_mean * 1.5 + 1.0, 5.0)
    mod_max  <= max(baseline_max  * 1.5 + 10,  50)

If a capture would fail, the audit can escalate once to a statistical baseline:
5 original-A runs x 5 original-B runs, plus 5 modified runs for the real delta.
This script does not modify the layered comparator, canonical PNGs, or VAS.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
PACK_DIR = ROOT / "qa" / "pack canonico"
DEFAULT_GENERATOR = PACK_DIR / "generate_captures.js"
DEFAULT_HTML = PACK_DIR / "neuromood-mockup_reparado.html"
DEFAULT_OUT_ROOT = ROOT / "reports" / "qa" / "mockup_parity_baseline"
CAPTURE_RE = re.compile(r"^(suite|hub)-(.+)-(light|dark)-(\d+)x(\d+)\.png$")

MEAN_MULTIPLIER = 1.5
MEAN_ADDEND = 1.0
MEAN_FLOOR = 5.0
MAX_MULTIPLIER = 1.5
MAX_ADDEND = 10.0
MAX_FLOOR = 50.0
EPSILON = 1e-9

EXPECTED_DELTA_ALLOWLIST: dict[str, dict[str, str]] = {
    "hub:detalle-resumen-ia-0@light": {
        "old_resolution": "720x462",
        "new_resolution": "960x600",
        "reason": "canonical AI summary modal window_overlay redesign",
    },
    "hub:detalle-resumen-ia-0@dark": {
        "old_resolution": "720x462",
        "new_resolution": "960x600",
        "reason": "canonical AI summary modal window_overlay redesign",
    },
}


@dataclass(frozen=True)
class CaptureName:
    file: str
    app: str
    view: str
    theme: str
    width: int
    height: int

    @property
    def key(self) -> str:
        return f"{self.app}:{self.view}@{self.theme}"

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass(frozen=True)
class DeltaMetrics:
    mean: float
    max: float
    changed_pixel_ratio: float

    def to_dict(self) -> dict[str, float]:
        return {
            "mean": round(self.mean, 6),
            "max": round(self.max, 6),
            "changed_pixel_ratio": round(self.changed_pixel_ratio, 6),
        }


def parse_capture_name(file_name: str) -> CaptureName | None:
    match = CAPTURE_RE.match(file_name)
    if not match:
        return None
    app, view, theme, width, height = match.groups()
    return CaptureName(
        file=file_name,
        app=app,
        view=view,
        theme=theme,
        width=int(width),
        height=int(height),
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_eol(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def eol_counts(text: str) -> dict[str, int]:
    crlf = text.count("\r\n")
    without_crlf = text.replace("\r\n", "")
    return {
        "crlf": crlf,
        "lf": without_crlf.count("\n"),
        "cr": without_crlf.count("\r"),
    }


def text_delta(original: Path, modified: Path, out_dir: Path) -> dict[str, Any]:
    original_bytes = original.read_bytes()
    modified_bytes = modified.read_bytes()
    original_text = original_bytes.decode("utf-8", errors="replace")
    modified_text = modified_bytes.decode("utf-8", errors="replace")
    original_normalized = normalize_eol(original_text)
    modified_normalized = normalize_eol(modified_text)

    raw_changed = original_bytes != modified_bytes
    normalized_changed = original_normalized != modified_normalized
    eol_only = raw_changed and not normalized_changed

    diff_lines: list[str] = []
    diff_path = out_dir / "TEXT_DIFF_NORMALIZED.patch"
    if normalized_changed:
        diff_lines = list(
            difflib.unified_diff(
                original_normalized.splitlines(),
                modified_normalized.splitlines(),
                fromfile=str(original),
                tofile=str(modified),
                lineterm="",
            )
        )
        diff_path.write_text("\n".join(diff_lines) + "\n", encoding="utf-8")
    else:
        diff_path.write_text(
            "No textual delta after CRLF/LF normalization.\n",
            encoding="utf-8",
        )

    eol_report = out_dir / "EOL_DELTA.txt"
    eol_report.write_text(
        "\n".join(
            [
                f"raw_changed={raw_changed}",
                f"eol_only_delta={eol_only}",
                f"normalized_changed={normalized_changed}",
                f"original_eol={eol_counts(original_text)}",
                f"modified_eol={eol_counts(modified_text)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "raw_changed": raw_changed,
        "normalized_changed": normalized_changed,
        "eol_only_delta": eol_only,
        "original_raw_sha256": sha256_bytes(original_bytes),
        "modified_raw_sha256": sha256_bytes(modified_bytes),
        "original_normalized_sha256": sha256_bytes(original_normalized.encode("utf-8")),
        "modified_normalized_sha256": sha256_bytes(modified_normalized.encode("utf-8")),
        "original_eol": eol_counts(original_text),
        "modified_eol": eol_counts(modified_text),
        "normalized_diff_line_count": len(diff_lines),
        "normalized_diff_path": str(diff_path),
        "eol_report_path": str(eol_report),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(np.asarray(values, dtype=np.float64), pct))


def mean_limit(baseline_mean: float) -> float:
    return max(baseline_mean * MEAN_MULTIPLIER + MEAN_ADDEND, MEAN_FLOOR)


def max_limit(baseline_max: float) -> float:
    return max(baseline_max * MAX_MULTIPLIER + MAX_ADDEND, MAX_FLOOR)


def load_rgb(path: Path, cache: dict[Path, Image.Image]) -> Image.Image:
    resolved = path.resolve()
    cached = cache.get(resolved)
    if cached is not None:
        return cached
    image = Image.open(resolved).convert("RGB")
    cache[resolved] = image
    return image


def image_delta(a_path: Path, b_path: Path, cache: dict[Path, Image.Image]) -> DeltaMetrics:
    a = load_rgb(a_path, cache)
    b = load_rgb(b_path, cache)
    if a.size != b.size:
        raise ValueError(f"size mismatch: {a_path.name} {a.size} vs {b_path.name} {b.size}")

    diff = np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16))
    max_per_pixel = diff.max(axis=2)
    return DeltaMetrics(
        mean=float(diff.mean()),
        max=float(diff.max()),
        changed_pixel_ratio=float((max_per_pixel > 0).mean()),
    )


def _chrome_candidates() -> list[Path]:
    env_path = os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path("/usr/bin/chromium"),
            Path("/usr/bin/chromium-browser"),
            Path("/usr/bin/google-chrome"),
        ]
    )
    for name in ("chrome", "chrome.exe", "chromium", "chromium-browser", "google-chrome"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    return candidates


def find_chromium(explicit: str | None) -> str | None:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise SystemExit(f"Chromium path does not exist: {path}")
        return str(path)
    for candidate in _chrome_candidates():
        if candidate.exists():
            return str(candidate)
    return None


def run_recipe(
    *,
    html_path: Path,
    out_dir: Path,
    generator: Path,
    chromium: str | None,
    timeout: int,
    label: str,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if chromium:
        env["PUPPETEER_EXECUTABLE_PATH"] = chromium
    node_modules = PACK_DIR / "node_modules"
    if node_modules.exists():
        existing_node_path = env.get("NODE_PATH")
        env["NODE_PATH"] = (
            str(node_modules)
            if not existing_node_path
            else os.pathsep.join([str(node_modules), existing_node_path])
        )

    cmd = ["node", str(generator), str(html_path), str(out_dir)]
    proc = subprocess.run(
        cmd,
        cwd=generator.parent,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    (out_dir / "_render_stdout.log").write_text(proc.stdout, encoding="utf-8", errors="replace")
    (out_dir / "_render_stderr.log").write_text(proc.stderr, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(
            f"capture recipe failed for {label} with exit {proc.returncode}; "
            f"see {out_dir / '_render_stderr.log'}"
        )

    manifest_path = out_dir / "MANIFEST.json"
    if not manifest_path.exists():
        raise RuntimeError(f"capture recipe did not write MANIFEST.json for {label}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "label": label,
        "out_dir": str(out_dir),
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "stdout": str(out_dir / "_render_stdout.log"),
        "stderr": str(out_dir / "_render_stderr.log"),
    }


def load_manifest_index(capture_dir: Path) -> dict[str, dict[str, Any]]:
    manifest_path = capture_dir / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    indexed: dict[str, dict[str, Any]] = {}
    for record in manifest.get("captures", []):
        file_name = str(record.get("file") or "")
        if file_name:
            indexed[file_name] = record
    return indexed


def classify_delta(
    *,
    status: str,
    baseline: DeltaMetrics,
    modified: DeltaMetrics,
    expected_delta_allowed: bool,
) -> str:
    visual_exceeds_noise = (
        modified.mean > baseline.mean + EPSILON
        or modified.max > baseline.max + EPSILON
    )
    if expected_delta_allowed and visual_exceeds_noise:
        return "EXPECTED_DELTA"
    if status == "FAIL":
        return "UNEXPECTED_DELTA"
    return "NO_DELTA"


def build_row(
    *,
    capture: CaptureName,
    record: dict[str, Any],
    original_a_dir: Path,
    original_b_dir: Path,
    modified_dir: Path,
    modified_by_key: dict[str, tuple[CaptureName, dict[str, Any]]],
    text_info: dict[str, Any],
    cache: dict[Path, Image.Image],
    baseline_mode: str = "single_1x1",
    pair_counts: tuple[int, int] = (1, 1),
) -> dict[str, Any]:
    original_a_file = original_a_dir / capture.file
    original_b_file = original_b_dir / capture.file
    modified_capture, _ = modified_by_key.get(capture.key, (capture, {}))
    modified_file = modified_dir / modified_capture.file
    allow = EXPECTED_DELTA_ALLOWLIST.get(capture.key)
    expected_delta_allowed = allow is not None

    row: dict[str, Any] = {
        "file": capture.file,
        "modified_file_name": modified_capture.file,
        "key": capture.key,
        "view": capture.view,
        "theme": capture.theme,
        "surface": record.get("surface", ""),
        "resolution": capture.resolution,
        "modified_resolution": modified_capture.resolution,
        "status": "FAIL",
        "delta_class": "UNEXPECTED_DELTA",
        "expected_delta_allowed": expected_delta_allowed,
        "expected_delta_reason": allow.get("reason", "") if allow else "",
        "allowlist_old_resolution": allow.get("old_resolution", "") if allow else "",
        "allowlist_new_resolution": allow.get("new_resolution", "") if allow else "",
        "baseline_mode": baseline_mode,
        "baseline_pair_count": pair_counts[0],
        "mod_pair_count": pair_counts[1],
        "escalated": False,
        "text_eol_only_delta": text_info["eol_only_delta"],
        "text_normalized_delta": text_info["normalized_changed"],
        "failure_reason": "",
        "original_a_file": str(original_a_file),
        "original_b_file": str(original_b_file),
        "modified_file": str(modified_file),
    }

    missing = [
        str(path)
        for path in (original_a_file, original_b_file, modified_file)
        if not path.exists()
    ]
    if missing:
        row["failure_reason"] = "missing_png:" + ";".join(missing)
        return row

    if capture.file != modified_capture.file or capture.resolution != modified_capture.resolution:
        if not expected_delta_allowed:
            row["failure_reason"] = (
                "unexpected_size_or_filename_delta:"
                f"old={capture.file} new={modified_capture.file}"
            )
            return row
        if (
            capture.resolution != allow["old_resolution"]
            or modified_capture.resolution != allow["new_resolution"]
        ):
            row["failure_reason"] = (
                "expected_delta_size_contract_mismatch:"
                f"old={capture.resolution} allow_old={allow['old_resolution']} "
                f"new={modified_capture.resolution} allow_new={allow['new_resolution']}"
            )
            return row
        row.update(
            {
                "status": "PASS",
                "delta_class": "EXPECTED_DELTA",
                "failure_reason": "",
                "baseline_mean": "",
                "baseline_max": "",
                "baseline_changed_pixel_ratio": "",
                "mod_mean": "",
                "mod_max": "",
                "mod_changed_pixel_ratio": "",
                "mean_limit": "",
                "max_limit": "",
            }
        )
        return row

    try:
        baseline = image_delta(original_a_file, original_b_file, cache)
        modified = image_delta(original_a_file, modified_file, cache)
    except ValueError as exc:
        row["failure_reason"] = str(exc)
        return row

    limit_mean = mean_limit(baseline.mean)
    limit_max = max_limit(baseline.max)
    passed = modified.mean <= limit_mean + EPSILON and modified.max <= limit_max + EPSILON

    row.update(
        {
            "status": "PASS" if passed else "FAIL",
            "baseline_mean": round(baseline.mean, 6),
            "baseline_max": round(baseline.max, 6),
            "baseline_changed_pixel_ratio": round(baseline.changed_pixel_ratio, 6),
            "mod_mean": round(modified.mean, 6),
            "mod_max": round(modified.max, 6),
            "mod_changed_pixel_ratio": round(modified.changed_pixel_ratio, 6),
            "mean_limit": round(limit_mean, 6),
            "max_limit": round(limit_max, 6),
            "failure_reason": ""
            if passed
            else "dynamic_baseline_exceeded",
        }
    )
    row["delta_class"] = classify_delta(
        status=row["status"],
        baseline=baseline,
        modified=modified,
        expected_delta_allowed=expected_delta_allowed,
    )
    return row


def _pair_metrics(
    left_dirs: list[Path],
    right_dirs: list[Path],
    file_name: str,
    cache: dict[Path, Image.Image],
) -> list[DeltaMetrics]:
    metrics: list[DeltaMetrics] = []
    for left_dir in left_dirs:
        for right_dir in right_dirs:
            left = left_dir / file_name
            right = right_dir / file_name
            if left.exists() and right.exists():
                metrics.append(image_delta(left, right, cache))
    return metrics


def apply_statistical_baseline(
    *,
    row: dict[str, Any],
    original_a_runs: list[Path],
    original_b_runs: list[Path],
    modified_runs: list[Path],
    text_info: dict[str, Any],
    cache: dict[Path, Image.Image],
) -> dict[str, Any]:
    baseline_pairs = _pair_metrics(original_a_runs, original_b_runs, row["file"], cache)
    modified_pairs = _pair_metrics(original_a_runs, modified_runs, row["file"], cache)
    if not baseline_pairs or not modified_pairs:
        row = dict(row)
        row["escalated"] = True
        row["baseline_mode"] = "statistical_5x5_incomplete"
        row["failure_reason"] = "statistical_baseline_incomplete"
        return row

    baseline_mean = percentile([metric.mean for metric in baseline_pairs], 95)
    baseline_max = percentile([metric.max for metric in baseline_pairs], 95)
    mod_mean = percentile([metric.mean for metric in modified_pairs], 50)
    mod_max = percentile([metric.max for metric in modified_pairs], 50)
    mod_changed = percentile([metric.changed_pixel_ratio for metric in modified_pairs], 50)
    baseline_changed = percentile([metric.changed_pixel_ratio for metric in baseline_pairs], 95)

    baseline = DeltaMetrics(baseline_mean, baseline_max, baseline_changed)
    modified = DeltaMetrics(mod_mean, mod_max, mod_changed)
    limit_mean = mean_limit(baseline_mean)
    limit_max = max_limit(baseline_max)
    passed = mod_mean <= limit_mean + EPSILON and mod_max <= limit_max + EPSILON

    updated = dict(row)
    baseline_mode = f"statistical_{len(original_a_runs)}x{len(original_b_runs)}_p95"
    updated.update(
        {
            "status": "PASS" if passed else "FAIL",
            "delta_class": classify_delta(
                status="PASS" if passed else "FAIL",
                baseline=baseline,
                modified=modified,
                expected_delta_allowed=bool(EXPECTED_DELTA_ALLOWLIST.get(row["key"])),
            ),
            "baseline_mode": baseline_mode,
            "baseline_pair_count": len(baseline_pairs),
            "mod_pair_count": len(modified_pairs),
            "escalated": True,
            "baseline_mean": round(baseline_mean, 6),
            "baseline_max": round(baseline_max, 6),
            "baseline_changed_pixel_ratio": round(baseline_changed, 6),
            "mod_mean": round(mod_mean, 6),
            "mod_max": round(mod_max, 6),
            "mod_changed_pixel_ratio": round(mod_changed, 6),
            "mean_limit": round(limit_mean, 6),
            "max_limit": round(limit_max, 6),
            "baseline_mean_p50": round(percentile([m.mean for m in baseline_pairs], 50), 6),
            "baseline_max_p50": round(percentile([m.max for m in baseline_pairs], 50), 6),
            "baseline_mean_p95": round(baseline_mean, 6),
            "baseline_max_p95": round(baseline_max, 6),
            "mod_mean_p95": round(percentile([m.mean for m in modified_pairs], 95), 6),
            "mod_max_p95": round(percentile([m.max for m in modified_pairs], 95), 6),
            "failure_reason": ""
            if passed
            else "dynamic_baseline_exceeded_after_statistical_escalation",
        }
    )
    return updated


def git_original_to_file(rev: str, html_path: Path, out_path: Path) -> tuple[Path | None, str | None]:
    try:
        rel = html_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None, f"{html_path} is outside repo root"

    proc = subprocess.run(
        ["git", "show", f"{rev}:{rel}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return None, proc.stderr.decode("utf-8", errors="replace").strip()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(proc.stdout)
    return out_path, None


def git_file_to_path(rev: str, repo_path: Path, out_path: Path) -> tuple[Path | None, str | None]:
    try:
        rel = repo_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None, f"{repo_path} is outside repo root"

    proc = subprocess.run(
        ["git", "show", f"{rev}:{rel}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return None, proc.stderr.decode("utf-8", errors="replace").strip()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(proc.stdout)
    return out_path, None


def prepare_sources(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    modified = Path(args.modified).resolve()
    if not modified.exists():
        raise SystemExit(f"Modified HTML does not exist: {modified}")

    source_info: dict[str, Any] = {
        "modified_html": str(modified),
        "modified_source": "filesystem",
    }

    if args.original:
        original = Path(args.original).resolve()
        if not original.exists():
            raise SystemExit(f"Original HTML does not exist: {original}")
        source_info["original_html"] = str(original)
        source_info["original_source"] = "filesystem"
        source_info["original_generator"] = str(Path(args.generator).resolve())
        source_info["original_generator_source"] = "filesystem"
        return source_info

    git_copy = out_dir / "sources" / f"original_{args.original_rev}.html"
    original, error = git_original_to_file(args.original_rev, DEFAULT_HTML, git_copy)
    if original is None:
        original = DEFAULT_HTML.resolve()
        source_info["original_source"] = "filesystem_fallback"
        source_info["original_git_error"] = error
    else:
        source_info["original_source"] = f"git:{args.original_rev}"
    source_info["original_html"] = str(original)

    generator_copy = out_dir / "sources" / f"generator_{args.original_rev}.js"
    original_generator, generator_error = git_file_to_path(args.original_rev, Path(args.generator), generator_copy)
    if original_generator is None:
        original_generator = Path(args.generator).resolve()
        source_info["original_generator_source"] = "filesystem_fallback"
        source_info["original_generator_git_error"] = generator_error
    else:
        source_info["original_generator_source"] = f"git:{args.original_rev}"
    source_info["original_generator"] = str(original_generator)
    return source_info


def capture_records(original_a_dir: Path) -> tuple[list[CaptureName], dict[str, dict[str, Any]], dict[str, Any]]:
    manifest = json.loads((original_a_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    records_by_file: dict[str, dict[str, Any]] = {}
    captures: list[CaptureName] = []
    for record in manifest.get("captures", []):
        file_name = str(record.get("file") or "")
        parsed = parse_capture_name(file_name)
        if parsed is None:
            continue
        records_by_file[file_name] = record
        captures.append(parsed)
    return captures, records_by_file, manifest


def capture_records_by_key(capture_dir: Path) -> dict[str, tuple[CaptureName, dict[str, Any]]]:
    manifest = json.loads((capture_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    records_by_key: dict[str, tuple[CaptureName, dict[str, Any]]] = {}
    for record in manifest.get("captures", []):
        file_name = str(record.get("file") or "")
        parsed = parse_capture_name(file_name)
        if parsed is not None:
            records_by_key[parsed.key] = (parsed, record)
    return records_by_key


def summary_from_rows(
    rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    text_info: dict[str, Any],
) -> dict[str, Any]:
    return {
        "total": len(rows),
        "pass": sum(1 for row in rows if row.get("status") == "PASS"),
        "fail": sum(1 for row in rows if row.get("status") != "PASS"),
        "expected_delta": sum(1 for row in rows if row.get("delta_class") == "EXPECTED_DELTA"),
        "eol_only_delta": text_info["eol_only_delta"],
        "unexpected_delta": sum(1 for row in rows if row.get("delta_class") == "UNEXPECTED_DELTA"),
        "expected_delta_allowlist": EXPECTED_DELTA_ALLOWLIST,
        "statistical_escalations": sum(1 for row in rows if row.get("escalated") is True),
        "expected_captures": manifest.get("expected_captures"),
        "all_captures_present": len(rows) == manifest.get("expected_captures"),
        "surfaces": manifest.get("surfaces", {}),
        "modal_capture_count": sum(
            1
            for row in rows
            if row.get("surface") in {"modal", "window_modal"}
        ),
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "file",
        "key",
        "view",
        "theme",
        "surface",
        "resolution",
        "modified_file_name",
        "modified_resolution",
        "status",
        "delta_class",
        "expected_delta_allowed",
        "expected_delta_reason",
        "allowlist_old_resolution",
        "allowlist_new_resolution",
        "baseline_mode",
        "escalated",
        "baseline_pair_count",
        "mod_pair_count",
        "text_eol_only_delta",
        "text_normalized_delta",
        "baseline_mean",
        "baseline_max",
        "mod_mean",
        "mod_max",
        "mean_limit",
        "max_limit",
        "baseline_changed_pixel_ratio",
        "mod_changed_pixel_ratio",
        "failure_reason",
        "original_a_file",
        "original_b_file",
        "modified_file",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(
    *,
    path: Path,
    payload: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    summary = payload["summary"]
    text_info = payload["text_delta"]
    lines = [
        "# Mockup HTML parity baseline audit",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Original HTML: `{payload['inputs']['original_html']}`",
        f"- Modified HTML: `{payload['inputs']['modified_html']}`",
        f"- Original source: `{payload['inputs']['original_source']}`",
        f"- Formula: `mod_mean <= max(baseline_mean * 1.5 + 1.0, 5.0)`",
        f"- Formula: `mod_max <= max(baseline_max * 1.5 + 10, 50)`",
        "- Scope: full canonical recipe from `qa/pack canonico/generate_captures.js`",
        "- Safety: comparator thresholds, canonical PNGs, and VAS are not modified.",
        "",
        "## Text delta",
        "",
        f"- Raw changed: {'YES' if text_info['raw_changed'] else 'NO'}",
        f"- EOL-only delta: {'YES' if text_info['eol_only_delta'] else 'NO'}",
        f"- Normalized textual delta: {'YES' if text_info['normalized_changed'] else 'NO'}",
        f"- Normalized diff lines: {text_info['normalized_diff_line_count']}",
        f"- Normalized diff: `{text_info['normalized_diff_path']}`",
        f"- EOL report: `{text_info['eol_report_path']}`",
        "",
        "## Summary",
        "",
        f"- Total captures: {summary['total']} / expected {summary['expected_captures']}",
        f"- PASS: {summary['pass']}",
        f"- FAIL: {summary['fail']}",
        f"- EXPECTED_DELTA: {summary['expected_delta']}",
        f"- EXPECTED_DELTA allowlist: `{summary['expected_delta_allowlist']}`",
        f"- EOL-only delta: {'YES' if summary['eol_only_delta'] else 'NO'}",
        f"- Statistical escalations: {summary['statistical_escalations']}",
        f"- Modal/actioned captures: {summary['modal_capture_count']}",
        f"- Surfaces: `{summary['surfaces']}`",
        "",
        "## Results",
        "",
        "| Status | Delta | Key | Base mean | Mod mean | Mean limit | Base max | Mod max | Max limit | Mode |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    ordered = sorted(
        rows,
        key=lambda row: (
            0 if row.get("status") != "PASS" else 1,
            0 if row.get("delta_class") == "EXPECTED_DELTA" else 1,
            str(row.get("key", "")),
        ),
    )
    for row in ordered:
        lines.append(
            "| {status} | {delta} | `{key}` | {bm} | {mm} | {ml} | {bx} | {mx} | {xl} | {mode} |".format(
                status=row.get("status", ""),
                delta=row.get("delta_class", ""),
                key=row.get("key", ""),
                bm=row.get("baseline_mean", ""),
                mm=row.get("mod_mean", ""),
                ml=row.get("mean_limit", ""),
                bx=row.get("baseline_max", ""),
                mx=row.get("mod_max", ""),
                xl=row.get("max_limit", ""),
                mode=row.get("baseline_mode", ""),
            )
        )

    failures = [row for row in rows if row.get("status") != "PASS"]
    if failures:
        lines.extend(["", "## FAIL Details", ""])
        for row in failures:
            lines.append(
                f"- `{row['key']}`: {row.get('failure_reason') or 'FAIL'} "
                f"(mode `{row.get('baseline_mode')}`)"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def default_out_dir() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_ROOT / stamp


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit HTML/mockup parity with dynamic original A/B baseline"
    )
    parser.add_argument("--original", help="Original HTML path. Defaults to --original-rev from git.")
    parser.add_argument(
        "--modified",
        default=str(DEFAULT_HTML),
        help="Modified HTML path. Defaults to the working-tree canonical HTML.",
    )
    parser.add_argument("--original-rev", default="HEAD", help="Git rev used when --original is omitted.")
    parser.add_argument("--generator", default=str(DEFAULT_GENERATOR), help="Canonical capture recipe JS.")
    parser.add_argument("--out-dir", default=None, help="Audit output directory.")
    parser.add_argument("--chromium", default=None, help="Chromium/Chrome executable override.")
    parser.add_argument("--render-timeout", type=int, default=600, help="Seconds per full render run.")
    parser.add_argument("--stat-runs", type=int, default=5, help="Runs per side for statistical escalation.")
    parser.add_argument(
        "--no-statistical-escalation",
        action="store_true",
        help="Do not run 5x5 statistical baseline before failing.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    generator = Path(args.generator).resolve()
    if not generator.exists():
        raise SystemExit(f"Capture generator does not exist: {generator}")
    if args.stat_runs < 2:
        raise SystemExit("--stat-runs must be >= 2")

    out_dir = Path(args.out_dir).resolve() if args.out_dir else default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    renders_dir = out_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)

    source_info = prepare_sources(args, out_dir)
    original_html = Path(source_info["original_html"])
    modified_html = Path(source_info["modified_html"])
    original_generator = Path(source_info["original_generator"])
    chromium = find_chromium(args.chromium)

    text_info = text_delta(original_html, modified_html, out_dir)

    print(f"OUT_DIR={out_dir}")
    print(f"ORIGINAL={original_html}")
    print(f"MODIFIED={modified_html}")
    print(f"CHROMIUM={chromium or '(generator default)'}")
    print("Rendering original A...")
    original_a = run_recipe(
        html_path=original_html,
        out_dir=renders_dir / "original_A",
        generator=original_generator,
        chromium=chromium,
        timeout=args.render_timeout,
        label="original_A",
    )
    print("Rendering original B...")
    original_b = run_recipe(
        html_path=original_html,
        out_dir=renders_dir / "original_B",
        generator=original_generator,
        chromium=chromium,
        timeout=args.render_timeout,
        label="original_B",
    )
    print("Rendering modified...")
    modified = run_recipe(
        html_path=modified_html,
        out_dir=renders_dir / "modified",
        generator=generator,
        chromium=chromium,
        timeout=args.render_timeout,
        label="modified",
    )

    captures, records_by_file, manifest = capture_records(Path(original_a["out_dir"]))
    modified_by_key = capture_records_by_key(Path(modified["out_dir"]))
    cache: dict[Path, Image.Image] = {}
    rows = [
        build_row(
            capture=capture,
            record=records_by_file[capture.file],
            original_a_dir=Path(original_a["out_dir"]),
            original_b_dir=Path(original_b["out_dir"]),
            modified_dir=Path(modified["out_dir"]),
            modified_by_key=modified_by_key,
            text_info=text_info,
            cache=cache,
        )
        for capture in captures
    ]

    failing_metric_rows = [
        row
        for row in rows
        if row.get("status") != "PASS"
        and row.get("failure_reason") == "dynamic_baseline_exceeded"
    ]
    statistical_runs: dict[str, list[str]] = {
        "original_A": [str(Path(original_a["out_dir"]))],
        "original_B": [str(Path(original_b["out_dir"]))],
        "modified": [str(Path(modified["out_dir"]))],
    }

    if failing_metric_rows and not args.no_statistical_escalation:
        print(
            "Initial dynamic baseline has "
            f"{len(failing_metric_rows)} candidate FAIL rows; escalating to "
            f"{args.stat_runs}x{args.stat_runs} statistical baseline..."
        )
        original_a_runs = [Path(original_a["out_dir"])]
        original_b_runs = [Path(original_b["out_dir"])]
        modified_runs = [Path(modified["out_dir"])]
        for idx in range(2, args.stat_runs + 1):
            label = f"original_A_{idx:02d}"
            print(f"Rendering {label}...")
            run = run_recipe(
                html_path=original_html,
                out_dir=renders_dir / label,
                generator=generator,
                chromium=chromium,
                timeout=args.render_timeout,
                label=label,
            )
            original_a_runs.append(Path(run["out_dir"]))
            statistical_runs["original_A"].append(str(Path(run["out_dir"])))

            label = f"original_B_{idx:02d}"
            print(f"Rendering {label}...")
            run = run_recipe(
                html_path=original_html,
                out_dir=renders_dir / label,
                generator=generator,
                chromium=chromium,
                timeout=args.render_timeout,
                label=label,
            )
            original_b_runs.append(Path(run["out_dir"]))
            statistical_runs["original_B"].append(str(Path(run["out_dir"])))

            label = f"modified_{idx:02d}"
            print(f"Rendering {label}...")
            run = run_recipe(
                html_path=modified_html,
                out_dir=renders_dir / label,
                generator=generator,
                chromium=chromium,
                timeout=args.render_timeout,
                label=label,
            )
            modified_runs.append(Path(run["out_dir"]))
            statistical_runs["modified"].append(str(Path(run["out_dir"])))

        rows_by_file = {row["file"]: row for row in rows}
        for row in failing_metric_rows:
            rows_by_file[row["file"]] = apply_statistical_baseline(
                row=row,
                original_a_runs=original_a_runs,
                original_b_runs=original_b_runs,
                modified_runs=modified_runs,
                text_info=text_info,
                cache=cache,
            )
        rows = [rows_by_file[capture.file] for capture in captures]

    summary = summary_from_rows(rows, manifest, text_info)
    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "authority": "MOCKUP_HTML_PARITY_DYNAMIC_BASELINE",
        "formula": {
            "mean": "mod_mean <= max(baseline_mean * 1.5 + 1.0, 5.0)",
            "max": "mod_max <= max(baseline_max * 1.5 + 10, 50)",
            "mean_multiplier": MEAN_MULTIPLIER,
            "mean_addend": MEAN_ADDEND,
            "mean_floor": MEAN_FLOOR,
            "max_multiplier": MAX_MULTIPLIER,
            "max_addend": MAX_ADDEND,
            "max_floor": MAX_FLOOR,
            "metric_scale": "raw RGB absolute delta, 0..255",
        },
        "inputs": {
            **source_info,
            "generator": str(generator),
            "original_generator": str(original_generator),
            "chromium": chromium,
            "original_html_sha256": sha256_file(original_html),
            "modified_html_sha256": sha256_file(modified_html),
        },
        "text_delta": text_info,
        "render_runs": {
            "initial": {
                "original_A": original_a,
                "original_B": original_b,
                "modified": modified,
            },
            "statistical": statistical_runs,
        },
        "coverage": {
            "recipe": str(generator),
            "expected_captures": manifest.get("expected_captures"),
            "captured_from_original_A": len(captures),
            "all_captured": manifest.get("all_captured"),
            "all_sizes_match": manifest.get("all_sizes_match"),
            "all_dom_sizes_match": manifest.get("all_dom_sizes_match"),
            "surfaces": manifest.get("surfaces"),
        },
        "summary": summary,
        "results": rows,
    }

    json_path = out_dir / "AUDIT.json"
    csv_path = out_dir / "AUDIT.csv"
    md_path = out_dir / "AUDIT.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(rows, csv_path)
    write_markdown(path=md_path, payload=payload, rows=rows)

    print(f"JSON={json_path}")
    print(f"CSV={csv_path}")
    print(f"AUDIT={md_path}")
    print(f"PASS={summary['pass']} FAIL={summary['fail']} EXPECTED_DELTA={summary['expected_delta']}")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
