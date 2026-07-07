#!/usr/bin/env python3
"""harness/v3/tests/test_policy_engine.py - Policy engine tests (stdlib).

Tests:
  - HIGH_DIFF -> BLOCK (no override)
  - LOW_DIFF -> HUMAN_REVIEW_REQUIRED (no auto-close)
  - DIFF_UNCLASSIFIED -> BLOCK
  - MISSING_PAIR -> BLOCK
  - SIZE_MISMATCH -> BLOCK
  - NO_DIFF -> CANDIDATE_PASS (with required properties missing listed)
  - HUMAN_REVIEWED_PASS -> CANDIDATE_PASS
  - HUMAN_REVIEWED_FAIL -> BLOCK
  - Unknown state -> BLOCK

Run with: python harness/v3/tests/test_policy_engine.py
Or: pytest harness/v3/tests/test_policy_engine.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "harness" / "v3"))

from policy_engine import evaluate, REQUIRED_PROPERTIES  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_high_diff_blocks() -> None:
    r = evaluate("HIGH_DIFF")
    _assert(r["decision"] == "BLOCK", f"HIGH_DIFF should BLOCK, got {r['decision']}")


def test_low_diff_no_auto_close() -> None:
    r = evaluate("LOW_DIFF")
    _assert(r["decision"] == "HUMAN_REVIEW_REQUIRED",
            f"LOW_DIFF should HUMAN_REVIEW_REQUIRED, got {r['decision']}")


def test_diff_unclassified_blocks() -> None:
    r = evaluate("DIFF_UNCLASSIFIED")
    _assert(r["decision"] == "BLOCK", f"DIFF_UNCLASSIFIED should BLOCK, got {r['decision']}")


def test_missing_pair_blocks() -> None:
    r = evaluate("MISSING_PAIR")
    _assert(r["decision"] == "BLOCK", f"MISSING_PAIR should BLOCK, got {r['decision']}")


def test_size_mismatch_blocks() -> None:
    r = evaluate("SIZE_MISMATCH")
    _assert(r["decision"] == "BLOCK", f"SIZE_MISMATCH should BLOCK, got {r['decision']}")


def test_no_diff_candidate_pass() -> None:
    r = evaluate("NO_DIFF")
    _assert(r["decision"] == "CANDIDATE_PASS",
            f"NO_DIFF should CANDIDATE_PASS, got {r['decision']}")
    _assert(r["required_properties_checked"] is True,
            "NO_DIFF should check required properties")
    # Without properties, all required should be listed as missing
    _assert(len(r["missing_required_properties"]) == len(REQUIRED_PROPERTIES),
            "All required properties should be missing when none provided")


def test_no_diff_with_all_properties() -> None:
    props = {p: True for p in REQUIRED_PROPERTIES}
    r = evaluate("NO_DIFF", props)
    _assert(r["decision"] == "CANDIDATE_PASS",
            f"NO_DIFF should CANDIDATE_PASS, got {r['decision']}")
    _assert(r["missing_required_properties"] == [],
            "No missing properties when all provided")


def test_human_reviewed_pass() -> None:
    r = evaluate("HUMAN_REVIEWED_PASS")
    _assert(r["decision"] == "CANDIDATE_PASS",
            f"HUMAN_REVIEWED_PASS should CANDIDATE_PASS, got {r['decision']}")


def test_human_reviewed_fail_blocks() -> None:
    r = evaluate("HUMAN_REVIEWED_FAIL")
    _assert(r["decision"] == "BLOCK",
            f"HUMAN_REVIEWED_FAIL should BLOCK, got {r['decision']}")


def test_unknown_state_blocks() -> None:
    r = evaluate("BOGUS_STATE")
    _assert(r["decision"] == "BLOCK", f"Unknown state should BLOCK, got {r['decision']}")
    _assert("unknown_state" in r["reason"], "Reason should mention unknown_state")


def main() -> int:
    tests = [
        test_high_diff_blocks,
        test_low_diff_no_auto_close,
        test_diff_unclassified_blocks,
        test_missing_pair_blocks,
        test_size_mismatch_blocks,
        test_no_diff_candidate_pass,
        test_no_diff_with_all_properties,
        test_human_reviewed_pass,
        test_human_reviewed_fail_blocks,
        test_unknown_state_blocks,
    ]
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
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e!r}", file=sys.stderr)
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
