#!/usr/bin/env python3
"""harness/v3/tests/test_replay.py - Replay policy tests (stdlib).

Tests:
  - --no-regen is BLOCKED (forbidden for closure)
  - replayed_keys=0 with expected>0 is BLOCKED (VQA-REPLAY-001)
  - --all-closed required (range audit alone insufficient)
  - --min-keys required

Run with: python harness/v3/tests/test_replay.py
Or: pytest harness/v3/tests/test_replay.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAY = REPO_ROOT / "harness" / "v3" / "replay" / "replay.py"


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(REPLAY), *args],
        capture_output=True, text=True, timeout=30,
    )
    return (proc.returncode, proc.stdout, proc.stderr)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_no_regen_blocked() -> None:
    rc, _, err = _run(["--no-regen", "--all-closed", "--min-keys", "1"])
    _assert(rc == 1, f"--no-regen should BLOCK (exit 1), got {rc}")
    _assert("forbidden" in err.lower(), f"err should mention forbidden: {err}")


def test_replayed_keys_zero_blocks() -> None:
    # harness/v3/evidence_records/active/ does not exist in Fase 2, so
    # list_closed_keys() returns []. --all-closed --min-keys 1 should BLOCK
    # on cardinality BEFORE hitting NOT_IMPLEMENTED.
    rc, _, err = _run(["--all-closed", "--min-keys", "1"])
    _assert(rc == 1, f"0 keys should BLOCK (exit 1), got {rc}")
    out = err.lower()
    _assert("below_minimum" in out or "not_implemented" in out,
            f"err should mention cardinality or not_implemented: {err}")


def test_all_closed_required() -> None:
    rc, _, err = _run(["--min-keys", "1"])
    _assert(rc == 1, f"missing --all-closed should BLOCK (exit 1), got {rc}")
    _assert("--all-closed" in err or "keys-file" in err,
            f"err should mention --all-closed: {err}")


def test_contract_print() -> None:
    rc, out, _ = _run(["--contract-print"])
    _assert(rc == 0, f"contract-print should exit 0, got {rc}")
    _assert("no_regen_forbidden_for_closure" in out,
            "contract should mention no_regen forbidden")


def main() -> int:
    tests = [
        test_no_regen_blocked,
        test_replayed_keys_zero_blocks,
        test_all_closed_required,
        test_contract_print,
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
