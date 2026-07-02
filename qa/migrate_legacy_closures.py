#!/usr/bin/env python3
"""Mark historical checked visual closures as legacy."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)-\s*\[(?P<state>[xX ])\]\s*(?P<body>.*)$")
NOTE_RE = re.compile(r"^\s*-\s*(?P<name>[A-Za-z0-9_-]+):\s*(?P<value>.*)$")
LEGACY_NOTES = (
    "  - legacy: true",
    "  - legacy-reason: pre_replay_era",
    "  - legacy-migrated-by: migrate_legacy_closures.py",
)


@dataclass(frozen=True)
class MigrationResult:
    changed: bool
    migrated_count: int
    text: str


def _line_ending(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _note_names(block: list[str]) -> set[str]:
    names: set[str] = set()
    for line in block:
        match = NOTE_RE.match(line)
        if match:
            names.add(match.group("name"))
    return names


def _split_checkbox_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    starts: list[int] = []
    for idx, line in enumerate(lines):
        if CHECKBOX_RE.match(line):
            starts.append(idx)
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        blocks.append((start, end))
    return blocks


def migrate_text(text: str) -> MigrationResult:
    newline = _line_ending(text)
    lines = text.splitlines()
    inserts: dict[int, list[str]] = {}
    migrated = 0

    for start, end in _split_checkbox_blocks(lines):
        match = CHECKBOX_RE.match(lines[start])
        if not match or match.group("state").lower() != "x":
            continue
        notes = lines[start + 1 : end]
        names = _note_names(notes)
        if "evidence" in names or "legacy" in names:
            continue
        inserts[start + 1] = list(LEGACY_NOTES)
        migrated += 1

    if not inserts:
        return MigrationResult(False, 0, text)

    out: list[str] = []
    for idx, line in enumerate(lines):
        out.append(line)
        if idx + 1 in inserts:
            out.extend(inserts[idx + 1])
    new_text = newline.join(out) + (newline if text.endswith(("\n", "\r\n")) else "")
    return MigrationResult(True, migrated, new_text)


def migrate_file(path: Path, *, dry_run: bool = False) -> MigrationResult:
    original = path.read_text(encoding="utf-8")
    result = migrate_text(original)
    if result.changed and not dry_run:
        tmp_path = path.with_name(f".{path.name}.tmp")
        tmp_path.write_text(result.text, encoding="utf-8")
        tmp_path.replace(path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mark pre-replay checked visual closures as legacy.")
    parser.add_argument("--handoff", type=Path, default=Path("VISUAL_REPAIR_HANDOFF.md"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = migrate_file(args.handoff, dry_run=args.dry_run)
    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"LEGACY MIGRATION {mode}")
    print(f"migrated_count: {result.migrated_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
