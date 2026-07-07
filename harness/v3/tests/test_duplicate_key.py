#!/usr/bin/env python3
"""harness/v3/tests/test_duplicate_key.py - Duplicate-key parser invariant test.

Tests that the harness refuses to operate when the same surface_key
appears more than once. In V3.1 this is a parser invariant, not a
separate lint.

This test uses an inline synthetic handoff text (does NOT read the
real VISUAL_REPAIR_HANDOFF.md, which is V1 and not touched).

Run with: python harness/v3/tests/test_duplicate_key.py
"""
from __future__ import annotations

import re
import sys


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


KEY_RE = re.compile(
    r"`(?P<key>(?:suite|hub):[^@\s`\"'\]\)]+@(?:light|dark))`"
)


def detect_duplicates(handoff_text: str) -> list[str]:
    """Return list of surface_keys that appear more than once."""
    seen: dict[str, int] = {}
    for m in KEY_RE.finditer(handoff_text):
        k = m.group("key")
        seen[k] = seen.get(k, 0) + 1
    return sorted([k for k, c in seen.items() if c > 1])


def test_no_duplicates_passes() -> None:
    text = """
- [ ] `suite:timer@light`
- [ ] `suite:timer@dark`
- [ ] `suite:animo@light`
"""
    dups = detect_duplicates(text)
    _assert(dups == [], f"expected no duplicates, got {dups}")


def test_duplicates_detected() -> None:
    text = """
- [ ] `suite:onboarding@light`
- [ ] `suite:onboarding@dark`
- [ ] `suite:onboarding@light`
"""
    dups = detect_duplicates(text)
    _assert(dups == ["suite:onboarding@light"],
            f"expected suite:onboarding@light, got {dups}")


def test_multiple_duplicates_detected() -> None:
    text = """
- [ ] `suite:onboarding@light`
- [ ] `suite:onboarding@dark`
- [ ] `suite:onboarding@light`
- [ ] `suite:onboarding@dark`
- [ ] `hub:pacientes@light`
"""
    dups = detect_duplicates(text)
    _assert(set(dups) == {"suite:onboarding@light", "suite:onboarding@dark"},
            f"expected 2 dups, got {dups}")


def main() -> int:
    tests = [test_no_duplicates_passes, test_duplicates_detected,
             test_multiple_duplicates_detected]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}", file=sys.stderr)
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
