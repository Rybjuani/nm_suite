#!/usr/bin/env python3
"""tools/visualparity/phase0d/check_ascii.py - ASCII check for PowerShell scripts.

Standalone stdlib-only checker. Verifies that the V3.1 PowerShell scripts
contain no non-ASCII characters, which would break Windows PowerShell 5.1
parsing when the file is UTF-8 without BOM.

NO runtime authority. Does NOT close keys, does NOT invoke V1/V2, does NOT
invoke capture_v8, does NOT use pytest.

Usage:
    python tools/visualparity/phase0d/check_ascii.py

Exit codes:
    0  PASS - all checked files are ASCII-only
    1  FAIL - at least one file contains non-ASCII characters
    2  ERROR - internal error (file not found, etc.)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Files to check (relative to repo root)
TARGETS = [
    "tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1",
    "tools/visualparity/phase0b/run_phase0b.ps1",
]


def check_file(rel: str) -> list[tuple[int, int, str]]:
    """Return list of (line, col, char) for each non-ASCII char found."""
    path = REPO_ROOT / rel
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    content = path.read_text(encoding="utf-8")
    findings: list[tuple[int, int, str]] = []
    for li, line in enumerate(content.splitlines(), 1):
        for ci, ch in enumerate(line, 1):
            if ord(ch) > 127:
                findings.append((li, ci, ch))
    return findings


def main() -> int:
    print("=" * 72)
    print("ASCII check for V3.1 PowerShell scripts")
    print("=" * 72)
    total_failures = 0
    for rel in TARGETS:
        findings = check_file(rel)
        if not findings:
            print(f"  PASS  {rel}  (0 non-ASCII chars)")
            continue
        total_failures += len(findings)
        print(f"  FAIL  {rel}  ({len(findings)} non-ASCII chars)")
        # Show first 10 unique chars
        seen: set[str] = set()
        for li, ci, ch in findings[:50]:
            if ch not in seen:
                seen.add(ch)
                print(f"        L{li}:C{ci} char={ch!r} U+{ord(ch):04X}")
    print("-" * 72)
    if total_failures == 0:
        print(f"Result: PASS (all {len(TARGETS)} files are ASCII-only)")
        print("=" * 72)
        return 0
    print(f"Result: FAIL ({total_failures} non-ASCII chars across {len(TARGETS)} files)")
    print("=" * 72)
    return 1


if __name__ == "__main__":
    sys.exit(main())
