#!/usr/bin/env python3
"""harness/semantic_lint/handoff_text_lint.py — VQA-SEM-001 / VQA-DUP-001.

Refuses closure if the visible handoff line for a surface_key contains any
forbidden phrase from closure_policy.yaml, OR if the surface_key appears
more than once in the handoff (duplicate-key spoofing).

Exit codes:
    0  PASS — handoff line is clean and the key is unique.
    1  FAIL — forbidden phrase found or duplicate key detected.
    2  ERROR — could not parse handoff or policy.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
HANDOFF = PROJ / "VISUAL_REPAIR_HANDOFF.md"
POLICY = PROJ / "harness" / "policy" / "closure_policy.yaml"

# Minimal YAML loader — avoids the pyyaml dependency for this single-file lint.
def load_forbidden_phrases(policy_path: Path) -> list[str]:
    text = policy_path.read_text(encoding="utf-8")
    in_section = False
    phrases: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("forbidden_handoff_phrases:"):
            in_section = True
            continue
        if in_section:
            if s.startswith("- "):
                val = s[2:].strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                phrases.append(val)
            elif s and not s.startswith("#") and not s.startswith("-"):
                # Left a section
                in_section = False
    return phrases


def find_handoff_line(handoff_text: str, surface_key: str) -> tuple[int, str] | None:
    """Return (line_number, line_text) for the active handoff line of surface_key.
    Returns the FIRST occurrence; the caller checks for duplicates separately.
    """
    pattern = re.compile(rf"`{re.escape(surface_key)}`")
    for i, line in enumerate(handoff_text.splitlines(), start=1):
        if pattern.search(line):
            return (i, line)
    return None


def count_handoff_occurrences(handoff_text: str, surface_key: str) -> int:
    pattern = re.compile(rf"`{re.escape(surface_key)}`")
    return sum(1 for line in handoff_text.splitlines() if pattern.search(line))


def lint_key(surface_key: str, phrases: list[str]) -> int:
    if not HANDOFF.exists():
        print(f"ERROR: handoff not found: {HANDOFF}", file=sys.stderr)
        return 2
    handoff_text = HANDOFF.read_text(encoding="utf-8")

    # ── Duplicate-key check (VQA-DUP-001) ──────────────────────────────
    occurrences = count_handoff_occurrences(handoff_text, surface_key)
    if occurrences > 1:
        print(f"FAIL: duplicate_surface_key_in_handoff", file=sys.stderr)
        print(f"  surface_key: {surface_key}", file=sys.stderr)
        print(f"  occurrences: {occurrences} (expected 1)", file=sys.stderr)
        print(f"  remediation: manually deduplicate the handoff before closure.",
              file=sys.stderr)
        return 1

    if occurrences == 0:
        print(f"FAIL: surface_key_not_in_handoff", file=sys.stderr)
        print(f"  surface_key: {surface_key}", file=sys.stderr)
        return 1

    # ── Forbidden-phrase check (VQA-SEM-001) ───────────────────────────
    found = find_handoff_line(handoff_text, surface_key)
    if found is None:
        print(f"FAIL: could not locate handoff line", file=sys.stderr)
        return 2
    line_no, line_text = found

    violations: list[str] = []
    for phrase in phrases:
        if phrase.lower() in line_text.lower():
            violations.append(phrase)

    if violations:
        print(f"FAIL: handoff_text_contradicts_evidence", file=sys.stderr)
        print(f"  surface_key: {surface_key}", file=sys.stderr)
        print(f"  handoff_line: {line_no}", file=sys.stderr)
        print(f"  forbidden_phrases_found:", file=sys.stderr)
        for v in violations:
            print(f"    - {v}", file=sys.stderr)
        print(f"  remediation: remove or resolve the forbidden phrases in the",
              file=sys.stderr)
        print(f"  handoff line before requesting closure.", file=sys.stderr)
        return 1

    print(f"PASS: handoff_line_clean")
    print(f"  surface_key: {surface_key}")
    print(f"  handoff_line: {line_no}")
    print(f"  occurrences: {occurrences}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", required=True,
                        help="surface_key to lint (e.g. suite:timer@light)")
    args = parser.parse_args()

    if not POLICY.exists():
        print(f"ERROR: policy file not found: {POLICY}", file=sys.stderr)
        return 2

    phrases = load_forbidden_phrases(POLICY)
    if not phrases:
        print(f"ERROR: no forbidden_handoff_phrases found in {POLICY}",
              file=sys.stderr)
        return 2

    return lint_key(args.key, phrases)


if __name__ == "__main__":
    sys.exit(main())
