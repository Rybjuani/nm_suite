#!/usr/bin/env python3
"""harness/semantic_lint/doc_keyword_lint.py — VQA-DOC-001.

Scans all active docs (excluding docs/_archive/) for the forbidden keyword
`DECISIÓN-OWNER` and fails if any occurrence is found. The replacement keyword
is `OWNER_EXCEPTION_ACTIVE`.

This lint runs on every CI push. A PR that introduces a new `DECISIÓN-OWNER`
occurrence cannot merge.

Exit codes:
    0  PASS — no forbidden keyword found in active docs.
    1  FAIL — at least one occurrence found.
    2  ERROR — could not scan.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]

FORBIDDEN_KEYWORD = "DECISIÓN-OWNER"
REQUIRED_KEYWORD = "OWNER_EXCEPTION_ACTIVE"

SCAN_GLOBS = [
    "docs/**/*.md",
    "VISUAL_REPAIR_HANDOFF.md",
    "harness/**/*.md",
    "harness/**/*.yaml",
    "harness/**/*.py",
]

EXCLUDE_GLOBS = [
    "docs/_archive/**",
    "harness/docs/FORENSIC_FINDINGS_V2.md",  # documents the keyword for context
]


def fnmatch_any(path: Path, patterns: list[str]) -> bool:
    """Minimal glob matcher (handles ** and exact segments)."""
    from fnmatch import fnmatch
    rel = str(path.relative_to(PROJ)).replace("\\", "/")
    for pat in patterns:
        if fnmatch(rel, pat):
            return True
        # Handle ** patterns by checking suffix
        if "**" in pat:
            prefix = pat.split("**")[0]
            if prefix and rel.startswith(prefix):
                suffix = pat.split("**")[1].lstrip("/")
                if not suffix or rel.endswith(suffix):
                    return True
    return False


def scan() -> int:
    if not PROJ.exists():
        print(f"ERROR: project root not found: {PROJ}", file=sys.stderr)
        return 2

    violations: list[tuple[Path, int, str]] = []

    for path in PROJ.rglob("*"):
        if not path.is_file():
            continue
        if not any(path.suffix == ext for ext in (".md", ".yaml", ".py")):
            continue

        rel = path.relative_to(PROJ)
        rel_str = str(rel).replace("\\", "/")

        # Exclude paths
        excluded = False
        for ex in EXCLUDE_GLOBS:
            if rel_str == ex.replace("**/", "") or rel_str.startswith(ex.split("**")[0]):
                excluded = True
                break
            if ex.endswith(rel_str) or rel_str in ex:
                excluded = True
                break
        if excluded:
            continue
        if rel_str.startswith("docs/_archive"):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for i, line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN_KEYWORD in line:
                violations.append((path, i, line.strip()))

    if violations:
        print(f"FAIL: forbidden_keyword_found", file=sys.stderr)
        print(f"  keyword: {FORBIDDEN_KEYWORD}", file=sys.stderr)
        print(f"  replacement: {REQUIRED_KEYWORD}", file=sys.stderr)
        print(f"  occurrences:", file=sys.stderr)
        for path, line_no, line in violations:
            rel = path.relative_to(PROJ)
            print(f"    - {rel}:{line_no}: {line[:120]}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  remediation: replace all occurrences with {REQUIRED_KEYWORD}",
              file=sys.stderr)
        print(f"  and add an explicit reason + reviewer field.", file=sys.stderr)
        return 1

    print(f"PASS: no_forbidden_keyword_in_active_docs")
    print(f"  keyword_scanned: {FORBIDDEN_KEYWORD}")
    print(f"  active_docs_scanned: yes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    return scan()


if __name__ == "__main__":
    sys.exit(main())
