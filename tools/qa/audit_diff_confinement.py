#!/usr/bin/env python3
"""Audit that the current git diff stays inside an explicit scope.

This is an auxiliary QA hardening gate. It does not replace visual comparison,
capture, VAS, modal audit, or anti-fraud checks. It only answers: "did this
change touch files and hunks that were allowed for this task?"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_OUT_DIR = Path("reports/qa/diff_confinement")
HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass(frozen=True)
class BlockSpec:
    path: str
    start_marker: str
    end_marker: str


@dataclass(frozen=True)
class LineRange:
    start: int
    end: int

    def contains(self, other: "LineRange") -> bool:
        return self.start <= other.start and other.end <= self.end


@dataclass
class HunkAudit:
    file: str
    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    allowed_by_block: bool
    block_required: bool
    reason: str


@dataclass
class FileAudit:
    path: str
    allowed_by_path: bool
    has_block_markers: bool
    status: str
    hunks: list[HunkAudit]


def normalize_repo_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip("/")


def is_path_allowed(path: str, allow_paths: Sequence[str]) -> bool:
    normalized = normalize_repo_path(path)
    for allowed in allow_paths:
        candidate = normalize_repo_path(allowed)
        if not candidate:
            continue
        if normalized == candidate or normalized.startswith(candidate.rstrip("/") + "/"):
            return True
    return False


def _git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _require_git(repo: Path, args: Sequence[str]) -> str:
    result = _git(repo, args)
    if result.returncode != 0:
        raise RuntimeError(
            "git command failed: "
            + " ".join(["git", "-C", str(repo), *args])
            + f"\n{result.stderr.strip()}"
        )
    return result.stdout


def touched_files(repo: Path, base: str) -> list[str]:
    raw = _require_git(repo, ["diff", "--name-only", "-z", base, "--"])
    if not raw:
        return []
    return [normalize_repo_path(part) for part in raw.split("\0") if part]


def current_diff(repo: Path, base: str) -> str:
    return _require_git(
        repo,
        [
            "diff",
            "--no-ext-diff",
            "--find-renames",
            "--find-copies",
            "--unified=0",
            base,
            "--",
        ],
    )


def _path_from_diff_git(line: str) -> str | None:
    # Covers normal unquoted paths. Tests and QA paths avoid special quoting.
    if not line.startswith("diff --git "):
        return None
    parts = line.split(" ")
    if len(parts) < 4:
        return None
    right = parts[3]
    if right.startswith("b/"):
        return normalize_repo_path(right[2:])
    return normalize_repo_path(right)


def _path_from_file_header(line: str) -> str | None:
    if line.startswith("+++ b/"):
        return normalize_repo_path(line[6:])
    if line.startswith("--- a/"):
        return normalize_repo_path(line[6:])
    return None


def parse_hunks(diff_text: str) -> dict[str, list[tuple[str, int, int, int, int]]]:
    hunks: dict[str, list[tuple[str, int, int, int, int]]] = {}
    current_file: str | None = None
    for line in diff_text.splitlines():
        diff_path = _path_from_diff_git(line)
        if diff_path is not None:
            current_file = diff_path
            hunks.setdefault(current_file, [])
            continue
        header_path = _path_from_file_header(line)
        if header_path is not None and header_path != "/dev/null":
            current_file = header_path
            hunks.setdefault(current_file, [])
            continue
        match = HUNK_RE.match(line)
        if match and current_file:
            old_count = int(match.group("old_count") or "1")
            new_count = int(match.group("new_count") or "1")
            hunks.setdefault(current_file, []).append(
                (
                    line,
                    int(match.group("old_start")),
                    old_count,
                    int(match.group("new_start")),
                    new_count,
                )
            )
    return hunks


def _line_ranges_for_block(repo: Path, spec: BlockSpec) -> list[LineRange]:
    path = repo / spec.path
    if not path.exists() or not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    ranges: list[LineRange] = []
    start_line: int | None = None
    for index, line in enumerate(lines, start=1):
        if start_line is None and spec.start_marker in line:
            start_line = index
            continue
        if start_line is not None and spec.end_marker in line:
            ranges.append(LineRange(start_line, index))
            start_line = None
    return ranges


def block_ranges(repo: Path, specs: Sequence[BlockSpec]) -> dict[str, list[LineRange]]:
    ranges: dict[str, list[LineRange]] = {}
    for spec in specs:
        ranges.setdefault(spec.path, []).extend(_line_ranges_for_block(repo, spec))
    return ranges


def _new_line_range(new_start: int, new_count: int) -> LineRange:
    if new_count <= 0:
        return LineRange(new_start, new_start)
    return LineRange(new_start, new_start + new_count - 1)


def audit_diff(
    repo: Path,
    base: str,
    allow_paths: Sequence[str],
    block_specs: Sequence[BlockSpec],
) -> dict:
    normalized_allow = [normalize_repo_path(path) for path in allow_paths]
    normalized_specs = [
        BlockSpec(normalize_repo_path(spec.path), spec.start_marker, spec.end_marker)
        for spec in block_specs
    ]
    touched = touched_files(repo, base)
    hunks_by_file = parse_hunks(current_diff(repo, base))
    ranges_by_file = block_ranges(repo, normalized_specs)
    block_paths = {spec.path for spec in normalized_specs}

    files: list[FileAudit] = []
    outside: list[dict] = []
    prohibited: list[str] = []

    for path in sorted(set(touched) | set(hunks_by_file)):
        allowed_by_path = is_path_allowed(path, normalized_allow)
        has_blocks = path in block_paths
        hunk_rows: list[HunkAudit] = []
        for header, old_start, old_count, new_start, new_count in hunks_by_file.get(path, []):
            allowed_by_block = True
            reason = "no_block_marker_required"
            if has_blocks:
                candidate = _new_line_range(new_start, new_count)
                allowed_by_block = any(
                    allowed_range.contains(candidate)
                    for allowed_range in ranges_by_file.get(path, [])
                )
                reason = "inside_allowed_block" if allowed_by_block else "outside_allowed_block"
            row = HunkAudit(
                file=path,
                header=header,
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
                allowed_by_block=allowed_by_block,
                block_required=has_blocks,
                reason=reason,
            )
            hunk_rows.append(row)
            if has_blocks and not allowed_by_block:
                outside.append(asdict(row))
        status = "PERMITTED" if allowed_by_path else "PROHIBITED"
        if not allowed_by_path:
            prohibited.append(path)
        files.append(FileAudit(path, allowed_by_path, has_blocks, status, hunk_rows))

    diff_confined = not prohibited and not outside
    payload = {
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "repo": str(repo.resolve()),
        "base": base,
        "allow_paths": normalized_allow,
        "allow_blocks": [asdict(spec) for spec in normalized_specs],
        "summary": {
            "verdict": "PASS" if diff_confined else "FAIL",
            "diff_confined": diff_confined,
            "touched_count": len(touched),
            "permitted_count": sum(1 for item in files if item.allowed_by_path),
            "prohibited_count": len(prohibited),
            "hunks_outside_block_count": len(outside),
        },
        "touched_files": touched,
        "prohibited_files": prohibited,
        "hunks_outside_block": outside,
        "files": [
            {
                **asdict(item),
                "hunks": [asdict(hunk) for hunk in item.hunks],
            }
            for item in files
        ],
    }
    return payload


def write_reports(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "DIFF_CONFINEMENT_REPORT.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Diff Confinement Report",
        "",
        f"Verdict: {payload['summary']['verdict']}",
        f"Base: `{payload['base']}`",
        f"Touched files: {payload['summary']['touched_count']}",
        f"Prohibited files: {payload['summary']['prohibited_count']}",
        f"Hunks outside block: {payload['summary']['hunks_outside_block_count']}",
        "",
        "## Files",
    ]
    for item in payload["files"]:
        lines.append(f"- {item['status']}: `{item['path']}`")
        for hunk in item["hunks"]:
            marker = "ok" if hunk["allowed_by_block"] else "outside-block"
            lines.append(f"  - {marker}: `{hunk['header']}`")
    (out_dir / "DIFF_CONFINEMENT_REPORT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    txt = [
        f"verdict={payload['summary']['verdict']}",
        f"diff_confined={payload['summary']['diff_confined']}",
        f"touched_count={payload['summary']['touched_count']}",
        f"prohibited_count={payload['summary']['prohibited_count']}",
        f"hunks_outside_block_count={payload['summary']['hunks_outside_block_count']}",
    ]
    (out_dir / "DIFF_CONFINEMENT_REPORT.txt").write_text(
        "\n".join(txt) + "\n",
        encoding="utf-8",
    )


def _parse_block_specs(entries: Sequence[Sequence[str]] | None) -> list[BlockSpec]:
    specs: list[BlockSpec] = []
    for entry in entries or []:
        path, start_marker, end_marker = entry
        specs.append(BlockSpec(normalize_repo_path(path), start_marker, end_marker))
    return specs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check that git diff files and optional hunks are confined to an allowlist."
    )
    parser.add_argument("--repo", type=Path, default=Path("."), help="Git repo root.")
    parser.add_argument("--base", default="HEAD", help="Base revision for git diff.")
    parser.add_argument(
        "--allow-path",
        action="append",
        default=[],
        help="Allowed file or directory path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--allow-block",
        action="append",
        nargs=3,
        metavar=("PATH", "START_MARKER", "END_MARKER"),
        help="Restrict hunks in PATH to lines between START_MARKER and END_MARKER.",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = audit_diff(
            args.repo,
            args.base,
            args.allow_path,
            _parse_block_specs(args.allow_block),
        )
        write_reports(payload, args.out_dir)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        print(f"DIFF CONFINEMENT ERROR: {exc}", file=sys.stderr)
        return 2

    verdict = payload["summary"]["verdict"]
    print(
        "DIFF CONFINEMENT "
        f"{verdict}: touched={payload['summary']['touched_count']} "
        f"prohibited={payload['summary']['prohibited_count']} "
        f"outside_block={payload['summary']['hunks_outside_block_count']}"
    )
    return 0 if payload["summary"]["diff_confined"] else 1


if __name__ == "__main__":
    sys.exit(main())
