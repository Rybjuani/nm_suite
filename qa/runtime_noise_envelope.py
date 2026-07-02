#!/usr/bin/env python3
"""Auxiliary runtime no-regression noise envelope for PyQt captures.

The script compares repeated runtime capture directories. Baseline-to-baseline
comparisons estimate renderer noise; baseline-to-modified comparisons estimate
the current change. It is intentionally advisory and never replaces
layered_visual_compare, VAS, modal audit, anti-fraud, or exact-key closure.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import itertools
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from PIL import Image


DEFAULT_OUT_DIR = Path("reports/qa/runtime_noise_envelope")
CAPTURE_SUFFIXES = {".png", ".PNG"}
PASS_STRICT = "PASS_STRICT"
EXPECTED_DELTA = "EXPECTED_DELTA"
REVIEW_NOISE = "REVIEW_NOISE"
FAIL = "FAIL"
NOISE_WARNING = "NOISE_WARNING"
STRICT_PASS_STATUSES = {PASS_STRICT, EXPECTED_DELTA}


@dataclass(frozen=True)
class CaptureId:
    file: str
    key: str


@dataclass
class PairMetrics:
    shape_mismatch: bool
    shape_a: tuple[int, ...] | None
    shape_b: tuple[int, ...] | None
    diff_px_low: int = 0
    diff_px_high: int = 0
    diff_pct_high: float = 0.0
    max_rgb: int = 0
    mean_rgb_high: float = 0.0
    total_px: int = 0


@dataclass
class NoiseRow:
    key: str
    status: str
    shape_mismatch: bool
    diff_px_low: int
    diff_px_high: int
    diff_pct_high: float
    max_rgb: int
    mean_rgb_high: float
    total_px: int
    noise_best: float
    noise_worst: float
    delta_best: float
    delta_median: float
    delta_worst: float
    codes: list[str]
    files: dict[str, list[str]]


def capture_key_from_name(file_name: str) -> str | None:
    stem = Path(file_name).stem
    parts = stem.split("-")
    if len(parts) < 5:
        return None
    app = parts[0]
    if app not in {"suite", "hub"}:
        return None
    theme_index = -3 if parts[-1].startswith("scale") else -2
    theme = parts[theme_index]
    if theme not in {"light", "dark"}:
        return None
    view = "-".join(parts[1:theme_index])
    if not view:
        return None
    return f"{app}:{view}@{theme}"


def collect_captures(directory: Path) -> dict[str, Path]:
    captures: dict[str, Path] = {}
    if not directory.exists():
        return captures
    for path in sorted(directory.iterdir()):
        if path.suffix not in CAPTURE_SUFFIXES or not path.is_file():
            continue
        key = capture_key_from_name(path.name)
        if key:
            captures[key] = path
    return captures


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def image_diff_metrics(path_a: Path, path_b: Path, rgb_high_threshold: int) -> PairMetrics:
    a = _load_rgb(path_a)
    b = _load_rgb(path_b)
    if a.shape != b.shape:
        return PairMetrics(True, tuple(a.shape), tuple(b.shape))

    channel_max = np.abs(a - b).max(axis=2)
    high = channel_max > rgb_high_threshold
    low = channel_max > 0
    diff_px_high = int(high.sum())
    total_px = int(channel_max.size)
    mean_high = float(channel_max[high].mean()) if diff_px_high else 0.0
    return PairMetrics(
        shape_mismatch=False,
        shape_a=tuple(a.shape),
        shape_b=tuple(b.shape),
        diff_px_low=int(low.sum()),
        diff_px_high=diff_px_high,
        diff_pct_high=float(diff_px_high / total_px) if total_px else 0.0,
        max_rgb=int(channel_max.max()) if total_px else 0,
        mean_rgb_high=mean_high,
        total_px=total_px,
    )


def _ratio_values(metrics: Iterable[PairMetrics]) -> list[float]:
    return [item.diff_pct_high for item in metrics if not item.shape_mismatch]


def _round(value: float) -> float:
    return round(float(value), 8)


def _worst(metrics: Sequence[PairMetrics]) -> PairMetrics:
    valid = [item for item in metrics if not item.shape_mismatch]
    if not valid:
        return PairMetrics(False, None, None)
    return max(valid, key=lambda item: (item.diff_pct_high, item.max_rgb, item.diff_px_low))


def _paths_for_key(maps: Sequence[dict[str, Path]], key: str) -> list[Path]:
    return [mapping[key] for mapping in maps if key in mapping]


def classify_row(
    *,
    key: str,
    baseline_paths: list[Path],
    modified_paths: list[Path],
    expected_delta_keys: set[str],
    rgb_high_threshold: int,
    min_margin: float,
    noise_warning_threshold: float,
) -> NoiseRow:
    codes: list[str] = []
    files = {
        "baseline": [str(path) for path in baseline_paths],
        "modified": [str(path) for path in modified_paths],
    }
    expected = key in expected_delta_keys

    if len(baseline_paths) < 2:
        codes.append("INSUFFICIENT_BASELINE_RUNS")
        return NoiseRow(key, FAIL, False, 0, 0, 0.0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, codes, files)
    if not modified_paths:
        codes.append("MISSING_MODIFIED_CAPTURE")
        return NoiseRow(key, FAIL, False, 0, 0, 0.0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, codes, files)

    noise_metrics = [
        image_diff_metrics(a, b, rgb_high_threshold)
        for a, b in itertools.combinations(baseline_paths, 2)
    ]
    delta_metrics = [
        image_diff_metrics(a, b, rgb_high_threshold)
        for a in baseline_paths
        for b in modified_paths
    ]
    shape_mismatch = any(item.shape_mismatch for item in noise_metrics + delta_metrics)

    if any(item.shape_mismatch for item in noise_metrics):
        codes.append("BASELINE_SHAPE_MISMATCH")
        return NoiseRow(key, FAIL, True, 0, 0, 0.0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, codes, files)

    if shape_mismatch:
        codes.append("SHAPE_MISMATCH")
        status = EXPECTED_DELTA if expected else FAIL
        return NoiseRow(key, status, True, 0, 0, 0.0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, codes, files)

    noise_values = _ratio_values(noise_metrics)
    delta_values = _ratio_values(delta_metrics)
    noise_best = min(noise_values) if noise_values else 0.0
    noise_worst = max(noise_values) if noise_values else 0.0
    delta_best = min(delta_values) if delta_values else 0.0
    delta_median = statistics.median(delta_values) if delta_values else 0.0
    delta_worst = max(delta_values) if delta_values else 0.0
    worst_delta = _worst(delta_metrics)

    if expected:
        status = EXPECTED_DELTA
        codes.append("EXPECTED_DELTA_ALLOWLIST")
    else:
        limit = noise_worst + min_margin
        if delta_median <= limit:
            if noise_worst > noise_warning_threshold:
                status = NOISE_WARNING
                codes.append("BASELINE_NOISE_HIGH")
            else:
                status = PASS_STRICT
        elif delta_best <= limit:
            status = REVIEW_NOISE
            codes.append("DELTA_BEST_ONLY")
        else:
            status = FAIL
            codes.append("DELTA_EXCEEDS_NOISE_ENVELOPE")

    return NoiseRow(
        key=key,
        status=status,
        shape_mismatch=shape_mismatch,
        diff_px_low=worst_delta.diff_px_low,
        diff_px_high=worst_delta.diff_px_high,
        diff_pct_high=_round(worst_delta.diff_pct_high),
        max_rgb=worst_delta.max_rgb,
        mean_rgb_high=_round(worst_delta.mean_rgb_high),
        total_px=worst_delta.total_px,
        noise_best=_round(noise_best),
        noise_worst=_round(noise_worst),
        delta_best=_round(delta_best),
        delta_median=_round(delta_median),
        delta_worst=_round(delta_worst),
        codes=codes,
        files=files,
    )


def evaluate(
    baseline_dirs: Sequence[Path],
    modified_dirs: Sequence[Path],
    expected_delta_keys: Iterable[str],
    *,
    rgb_high_threshold: int = 20,
    min_margin: float = 0.001,
    noise_warning_threshold: float = 0.02,
) -> dict:
    baseline_maps = [collect_captures(path) for path in baseline_dirs]
    modified_maps = [collect_captures(path) for path in modified_dirs]
    keys = sorted(set().union(*(mapping.keys() for mapping in baseline_maps + modified_maps)))
    expected = set(expected_delta_keys)

    rows = [
        classify_row(
            key=key,
            baseline_paths=_paths_for_key(baseline_maps, key),
            modified_paths=_paths_for_key(modified_maps, key),
            expected_delta_keys=expected,
            rgb_high_threshold=rgb_high_threshold,
            min_margin=min_margin,
            noise_warning_threshold=noise_warning_threshold,
        )
        for key in keys
    ]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    strict_pass = all(row.status in STRICT_PASS_STATUSES for row in rows)
    no_failures = all(row.status != FAIL for row in rows)
    return {
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "summary": {
            "total": len(rows),
            "by_status": counts,
            "strict_pass": strict_pass,
            "no_failures": no_failures,
            "advisory_only": True,
            "delta_best_closes_runtime": False,
        },
        "inputs": {
            "baseline_dirs": [str(path) for path in baseline_dirs],
            "modified_dirs": [str(path) for path in modified_dirs],
            "expected_delta_keys": sorted(expected),
            "rgb_high_threshold": rgb_high_threshold,
            "min_margin": min_margin,
            "noise_warning_threshold": noise_warning_threshold,
        },
        "rows": [asdict(row) for row in rows],
    }


def write_reports(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "RUNTIME_NOISE_ENVELOPE_REPORT.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    csv_path = out_dir / "RUNTIME_NOISE_ENVELOPE_REPORT.csv"
    columns = [
        "key",
        "status",
        "shape_mismatch",
        "diff_px_low",
        "diff_px_high",
        "diff_pct_high",
        "max_rgb",
        "mean_rgb_high",
        "total_px",
        "noise_best",
        "noise_worst",
        "delta_best",
        "delta_median",
        "delta_worst",
        "codes",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({**{key: row.get(key) for key in columns}, "codes": ";".join(row["codes"])})

    lines = [
        "# Runtime Noise Envelope Report",
        "",
        f"Strict pass: `{payload['summary']['strict_pass']}`",
        f"No failures: `{payload['summary']['no_failures']}`",
        "Advisory only: `True`",
        "delta_best closes runtime: `False`",
        "",
        "## Rows",
    ]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['key']}`: {row['status']} "
            f"delta_median={row['delta_median']} noise_worst={row['noise_worst']} "
            f"codes={','.join(row['codes']) or 'none'}"
        )
    (out_dir / "RUNTIME_NOISE_ENVELOPE_REPORT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _read_expected_delta_file(path: Path | None) -> list[str]:
    if path is None:
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare runtime capture dirs against a renderer-noise envelope."
    )
    parser.add_argument(
        "--baseline-dir",
        action="append",
        type=Path,
        required=True,
        help="Baseline capture directory. Pass at least two.",
    )
    parser.add_argument(
        "--modified-dir",
        action="append",
        type=Path,
        required=True,
        help="Modified/current capture directory. Can be passed multiple times.",
    )
    parser.add_argument("--expected-delta-key", action="append", default=[])
    parser.add_argument("--expected-delta-file", type=Path, default=None)
    parser.add_argument("--rgb-high-threshold", type=int, default=20)
    parser.add_argument("--min-margin", type=float, default=0.001)
    parser.add_argument("--noise-warning-threshold", type=float, default=0.02)
    parser.add_argument("--mode", choices=("strict", "diagnostic"), default="strict")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    expected_keys = set(args.expected_delta_key) | set(_read_expected_delta_file(args.expected_delta_file))
    if len(args.baseline_dir) < 2:
        print("RUNTIME NOISE ENVELOPE FAIL: pass at least two --baseline-dir values.", file=sys.stderr)
        return 2
    payload = evaluate(
        args.baseline_dir,
        args.modified_dir,
        expected_keys,
        rgb_high_threshold=args.rgb_high_threshold,
        min_margin=args.min_margin,
        noise_warning_threshold=args.noise_warning_threshold,
    )
    write_reports(payload, args.out_dir)
    print(
        "RUNTIME NOISE ENVELOPE "
        f"strict_pass={payload['summary']['strict_pass']} "
        f"no_failures={payload['summary']['no_failures']} "
        f"by_status={payload['summary']['by_status']}"
    )
    if args.mode == "diagnostic":
        return 0 if payload["summary"]["no_failures"] else 1
    return 0 if payload["summary"]["strict_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
