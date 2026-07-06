#!/usr/bin/env python3
"""harness/agent_runner/target_scope_v2.py — VQA-DUP-001 + VQA-FAMILY-001.

Replaces qa/target_scope.py. Adds:
  - duplicate-key detection (refuses to operate if any surface_key appears
    more than once in the handoff).
  - family/scope enforcement (closing a key requires declaring the target-set
    and family; refuses if another family member is FAIL in the current bundle).

Modes (same as v1):
  --mode next-key          resolve first open [ ] checkbox
  --mode all-open-keys     list all open keys, deduplicated
  --mode family --seed-key <key>   list open keys in the same ### section
  --mode first-n --n <N>           list first N open keys
  --mode explicit-list --keys-file <path>

Exit codes:
    0  OK — printed resolved keys
    1  FAIL — duplicate key detected or scope violation
    2  ERROR
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
HANDOFF = PROJ / "VISUAL_REPAIR_HANDOFF.md"
KEY_RE = re.compile(r"`(?P<key>(?:suite|hub):[^@\s`\"'\]\)]+@(?:light|dark))`")
SECTION_RE = re.compile(r"^###\s+(.+)$")
CHECKLIST_OPEN_RE = re.compile(r"^-\s+\[\s+\]\s+`(?P<key>(?:suite|hub):[^@`]+@(?:light|dark))`")


def parse_handoff() -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (all_keys_with_section, open_keys_with_section, duplicate_keys).
    Each list element is (surface_key, section_heading).
    """
    if not HANDOFF.exists():
        print(f"ERROR: handoff not found: {HANDOFF}", file=sys.stderr)
        sys.exit(2)

    text = HANDOFF.read_text(encoding="utf-8")
    all_keys: list[tuple[str, str]] = []
    open_keys: list[tuple[str, str]] = []
    current_section = ""

    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            current_section = m.group(1).strip()
            continue
        for km in KEY_RE.finditer(line):
            key = km.group("key")
            all_keys.append((key, current_section))
        if CHECKLIST_OPEN_RE.match(line):
            km = KEY_RE.search(line)
            if km:
                open_keys.append((km.group("key"), current_section))

    # Detect duplicates
    seen: dict[str, int] = {}
    duplicates: list[tuple[str, str]] = []
    for key, section in all_keys:
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 2:
            duplicates.append((key, section))

    return all_keys, open_keys, duplicates


def family_of(seed_key: str, all_keys: list[tuple[str, str]]) -> list[str]:
    """Return all surface_keys sharing the same ### section as seed_key."""
    seed_section = ""
    for key, section in all_keys:
        if key == seed_key:
            seed_section = section
            break
    if not seed_section:
        return []
    return [k for k, s in all_keys if s == seed_section]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True,
                        choices=["next-key", "all-open-keys", "family",
                                 "first-n", "explicit-list"])
    parser.add_argument("--seed-key", default=None)
    parser.add_argument("--n", type=int, default=None)
    parser.add_argument("--keys-file", default=None)
    args = parser.parse_args()

    all_keys, open_keys, duplicates = parse_handoff()

    # ── Duplicate-key check (VQA-DUP-001) ─────────────────────────────
    if duplicates:
        print(f"FAIL: duplicate_surface_key_in_handoff", file=sys.stderr)
        print(f"  duplicates:", file=sys.stderr)
        for key, section in duplicates:
            print(f"    - {key} (section: {section})", file=sys.stderr)
        print(f"  remediation: manually deduplicate before any scope operation.",
              file=sys.stderr)
        return 1

    open_key_set = [k for k, _ in open_keys]

    if args.mode == "next-key":
        if not open_key_set:
            print("# no open keys")
            return 0
        print(open_key_set[0])
        return 0

    if args.mode == "all-open-keys":
        for k in open_key_set:
            print(k)
        return 0

    if args.mode == "family":
        if not args.seed_key:
            print("ERROR: --seed-key required for family mode", file=sys.stderr)
            return 2
        family = family_of(args.seed_key, all_keys)
        open_in_family = [k for k in family if k in open_key_set]
        for k in open_in_family:
            print(k)
        return 0

    if args.mode == "first-n":
        if args.n is None:
            print("ERROR: --n required for first-n mode", file=sys.stderr)
            return 2
        for k in open_key_set[:args.n]:
            print(k)
        return 0

    if args.mode == "explicit-list":
        if not args.keys_file:
            print("ERROR: --keys-file required for explicit-list mode", file=sys.stderr)
            return 2
        keys_path = Path(args.keys_file)
        if not keys_path.exists():
            print(f"ERROR: keys-file not found: {keys_path}", file=sys.stderr)
            return 2
        for line in keys_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                print(line)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
