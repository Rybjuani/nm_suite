#!/usr/bin/env python3
"""Compare direct-entry runtime states against internally navigated states.

This auxiliary gate compares already captured images plus optional state
metadata. It is intentionally not a product harness: if a future DBT navigation
probe needs deeper runtime hooks, add them without weakening this offline check.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image


DEFAULT_OUT_DIR = Path("reports/qa/runtime_internal_nav_parity")
PASS = "PASS"
REVIEW = "REVIEW"
FAIL = "FAIL"
METADATA_FIELDS = ("state", "tab", "stack", "scroll", "viewport", "transform_scale")


@dataclass
class NavCase:
    key: str
    direct_image: Path
    nav_image: Path
    direct_metadata: Path | None = None
    nav_metadata: Path | None = None


@dataclass
class DiffBBox:
    left: int
    top: int
    right: int
    bottom: int


@dataclass
class NavRow:
    key: str
    status: str
    size_direct: tuple[int, int] | None
    size_nav: tuple[int, int] | None
    root_bbox_direct: list[int] | None
    root_bbox_nav: list[int] | None
    diff_px_high: int
    diff_pct_high: float
    max_rgb: int
    diff_bbox: DiffBBox | None
    codes: list[str]
    metadata_delta: dict[str, dict[str, object]]


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def _load_meta(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _bbox(mask: np.ndarray) -> DiffBBox | None:
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return DiffBBox(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def _root_bbox(meta: dict) -> list[int] | None:
    value = meta.get("root_bbox")
    if isinstance(value, list) and len(value) == 4:
        return [int(item) for item in value]
    if isinstance(value, tuple) and len(value) == 4:
        return [int(item) for item in value]
    return None


def _metadata_delta(direct: dict, nav: dict) -> dict[str, dict[str, object]]:
    delta: dict[str, dict[str, object]] = {}
    for field in METADATA_FIELDS:
        if field in direct or field in nav:
            if direct.get(field) != nav.get(field):
                delta[field] = {"direct": direct.get(field), "nav": nav.get(field)}
    return delta


def compare_case(
    case: NavCase,
    *,
    rgb_high_threshold: int = 20,
    isolated_review_px: int = 8,
) -> NavRow:
    codes: list[str] = []
    metadata_delta: dict[str, dict[str, object]] = {}

    try:
        direct = _load_rgb(case.direct_image)
        nav = _load_rgb(case.nav_image)
    except FileNotFoundError as exc:
        return NavRow(
            case.key,
            FAIL,
            None,
            None,
            None,
            None,
            0,
            0.0,
            0,
            None,
            [f"MISSING_IMAGE:{exc.filename}"],
            {},
        )

    size_direct = (int(direct.shape[1]), int(direct.shape[0]))
    size_nav = (int(nav.shape[1]), int(nav.shape[0]))
    direct_meta = _load_meta(case.direct_metadata)
    nav_meta = _load_meta(case.nav_metadata)
    root_direct = _root_bbox(direct_meta)
    root_nav = _root_bbox(nav_meta)

    if direct.shape != nav.shape:
        codes.append("SHAPE_MISMATCH")
        return NavRow(
            case.key,
            FAIL,
            size_direct,
            size_nav,
            root_direct,
            root_nav,
            0,
            0.0,
            0,
            None,
            codes,
            {},
        )

    if root_direct != root_nav:
        codes.append("ROOT_BBOX_MISMATCH")

    metadata_delta = _metadata_delta(direct_meta, nav_meta)
    if metadata_delta:
        codes.append("METADATA_MISMATCH")

    channel_max = np.abs(direct - nav).max(axis=2)
    high = channel_max > rgb_high_threshold
    diff_px_high = int(high.sum())
    total_px = int(channel_max.size)
    diff_bbox = _bbox(high)
    max_rgb = int(channel_max.max()) if total_px else 0
    diff_pct_high = round(float(diff_px_high / total_px), 8) if total_px else 0.0

    if diff_px_high == 0 and not codes:
        status = PASS
    elif codes:
        status = FAIL
    elif diff_px_high <= isolated_review_px:
        status = REVIEW
        codes.append("ISOLATED_PIXEL_DELTA")
    else:
        status = FAIL
        codes.append("VISUAL_DELTA")

    return NavRow(
        key=case.key,
        status=status,
        size_direct=size_direct,
        size_nav=size_nav,
        root_bbox_direct=root_direct,
        root_bbox_nav=root_nav,
        diff_px_high=diff_px_high,
        diff_pct_high=diff_pct_high,
        max_rgb=max_rgb,
        diff_bbox=diff_bbox,
        codes=codes,
        metadata_delta=metadata_delta,
    )


def evaluate_cases(
    cases: Sequence[NavCase],
    *,
    rgb_high_threshold: int = 20,
    isolated_review_px: int = 8,
) -> dict:
    rows = [
        compare_case(
            case,
            rgb_high_threshold=rgb_high_threshold,
            isolated_review_px=isolated_review_px,
        )
        for case in cases
    ]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return {
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "summary": {
            "total": len(rows),
            "by_status": counts,
            "pass_count": counts.get(PASS, 0),
            "review_count": counts.get(REVIEW, 0),
            "fail_count": counts.get(FAIL, 0),
            "advisory_only": True,
            "runtime_probe_implemented": False,
            "runtime_probe_todo": (
                "Add real PyQt route probes only if capture_v8 exposes internal "
                "navigation hooks without touching product code."
            ),
        },
        "rows": [asdict(row) for row in rows],
    }


def _case_from_dict(item: dict, base_dir: Path) -> NavCase:
    def path_or_none(value: str | None) -> Path | None:
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else base_dir / path

    return NavCase(
        key=str(item["key"]),
        direct_image=path_or_none(item["direct_image"]) or Path(),
        nav_image=path_or_none(item["nav_image"]) or Path(),
        direct_metadata=path_or_none(item.get("direct_metadata")),
        nav_metadata=path_or_none(item.get("nav_metadata")),
    )


def load_cases(path: Path) -> list[NavCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = raw.get("cases", raw)
    if not isinstance(cases, list):
        raise ValueError("case file must be a list or an object with a 'cases' list")
    return [_case_from_dict(item, path.parent) for item in cases]


def write_reports(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "RUNTIME_INTERNAL_NAV_PARITY_REPORT.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "RUNTIME_INTERNAL_NAV_PARITY_REPORT.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        columns = [
            "key",
            "status",
            "size_direct",
            "size_nav",
            "root_bbox_direct",
            "root_bbox_nav",
            "diff_px_high",
            "diff_pct_high",
            "max_rgb",
            "diff_bbox",
            "codes",
        ]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({**{key: row.get(key) for key in columns}, "codes": ";".join(row["codes"])})

    lines = [
        "# Runtime Internal Navigation Parity Report",
        "",
        f"Advisory only: `{payload['summary']['advisory_only']}`",
        f"Runtime probe implemented: `{payload['summary']['runtime_probe_implemented']}`",
        "",
        "## Rows",
    ]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['key']}`: {row['status']} "
            f"diff_px_high={row['diff_px_high']} codes={','.join(row['codes']) or 'none'}"
        )
    (out_dir / "RUNTIME_INTERNAL_NAV_PARITY_REPORT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare direct-entry captures with internally navigated captures."
    )
    parser.add_argument("--case-file", type=Path, default=None)
    parser.add_argument("--key", default="runtime:internal-nav@unknown")
    parser.add_argument("--direct-image", type=Path, default=None)
    parser.add_argument("--nav-image", type=Path, default=None)
    parser.add_argument("--direct-metadata", type=Path, default=None)
    parser.add_argument("--nav-metadata", type=Path, default=None)
    parser.add_argument("--rgb-high-threshold", type=int, default=20)
    parser.add_argument("--isolated-review-px", type=int, default=8)
    parser.add_argument("--strict-review", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.case_file:
        cases = load_cases(args.case_file)
    else:
        if args.direct_image is None or args.nav_image is None:
            parser.error("pass --case-file or both --direct-image and --nav-image")
        cases = [
            NavCase(
                args.key,
                args.direct_image,
                args.nav_image,
                args.direct_metadata,
                args.nav_metadata,
            )
        ]
    payload = evaluate_cases(
        cases,
        rgb_high_threshold=args.rgb_high_threshold,
        isolated_review_px=args.isolated_review_px,
    )
    write_reports(payload, args.out_dir)
    print(
        "RUNTIME INTERNAL NAV PARITY "
        f"fail_count={payload['summary']['fail_count']} "
        f"review_count={payload['summary']['review_count']}"
    )
    if payload["summary"]["fail_count"]:
        return 1
    if args.strict_review and payload["summary"]["review_count"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
