#!/usr/bin/env python3
"""harness/v3/replay/replay.py - Replay with cardinality + full-regen mandate.

Replaces V1 qa/replay_visual_closure.py. Key V3.1 rules:
  - --no-regen is FORBIDDEN for closure validation. The flag does not
    exist as a closure mode; if passed, BLOCK.
  - --min-keys <N> is required. If replayed_keys < N, BLOCK.
  - --all-closed is required for closure audit, not just --base <ref>.

Fase 2: contract-level only. Does NOT actually recapture or recompare.
Returns NOT_IMPLEMENTED for any actual replay attempt. The cardinality
and --no-regen rejections ARE implemented (they are policy, not runtime).

NO stub-pass. V2 peca al permitir stubs que PASS; V3.1 no.

Usage:
    python harness/v3/replay/replay.py --contract-print
    python harness/v3/replay/replay.py --all-closed --min-keys 1
    python harness/v3/replay/replay.py --no-regen   # BLOCK

Exit codes:
    0  contract printed or preflight cardinality check passed (no replay run)
    1  BLOCK (--no-regen, cardinality fail, NOT_IMPLEMENTED actual replay)
    2  ERROR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "harness" / "v3" / "evidence_records" / "active"

CONTRACT = {
    "module": "harness/v3/replay/replay.py",
    "fase": "2-contract-only",
    "rules": {
        "no_regen_forbidden_for_closure": True,
        "min_keys_required": True,
        "all_closed_required_for_closure_audit": True,
        "cardinality_exact": True,
        "replayed_keys_zero_with_expected_positive": "BLOCK",
        "stub_pass": "FORBIDDEN - V3.1 does not allow stubs that return PASS",
    },
    "not_implemented": [
        "actual recapture",
        "actual recompare via VisualParity",
        "actual hash verification vs stored evidence records",
    ],
}


def list_closed_keys() -> list[str]:
    """List surface_keys from harness/v3/evidence_records/active/*.json.
    Fase 2: the directory does not exist yet; returns empty list."""
    if not EVIDENCE_DIR.exists():
        return []
    keys: list[str] = []
    for record in EVIDENCE_DIR.glob("*.json"):
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
            key = data.get("surface_key") or data.get("key")
            if key:
                keys.append(key)
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(keys)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-print", action="store_true")
    parser.add_argument("--base", default=None,
                        help="Git base ref for range audit (optional, pre-check only).")
    parser.add_argument("--all-closed", action="store_true",
                        help="Replay ALL closed keys (required for closure audit).")
    parser.add_argument("--min-keys", type=int, default=1)
    parser.add_argument("--no-regen", action="store_true",
                        help="FORBIDDEN for closure. Will BLOCK.")
    parser.add_argument("--keys-file", default=None)
    args = parser.parse_args()

    if args.contract_print:
        print(json.dumps(CONTRACT, indent=2))
        return 0

    # Rule: --no-regen is forbidden for closure.
    if args.no_regen:
        print("BLOCK: --no-regen is forbidden for closure validation.",
              file=sys.stderr)
        print("  Structural replay is diagnostic only. Use --regen (default).",
              file=sys.stderr)
        return 1

    # Rule: --all-closed or --keys-file required for closure audit.
    if not args.all_closed and not args.keys_file:
        print("BLOCK: --all-closed or --keys-file required for closure audit.",
              file=sys.stderr)
        return 1

    # Determine keys.
    if args.keys_file:
        keys_path = Path(args.keys_file)
        if not keys_path.exists():
            print(f"ERROR: keys-file not found: {keys_path}", file=sys.stderr)
            return 2
        keys = [
            line.strip() for line in keys_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
    else:
        keys = list_closed_keys()

    # Rule: cardinality check.
    if len(keys) < args.min_keys:
        print("BLOCK: replayed_keys_below_minimum", file=sys.stderr)
        print(f"  replayed_keys: {len(keys)}", file=sys.stderr)
        print(f"  minimum_required: {args.min_keys}", file=sys.stderr)
        print("  Empty replay PASS is dangerous (VQA-REPLAY-001).", file=sys.stderr)
        return 1

    # Fase 2: actual replay is NOT_IMPLEMENTED.
    print("NOT_IMPLEMENTED: actual replay (recapture + recompare) is deferred.",
          file=sys.stderr)
    print(f"  resolved_keys: {len(keys)}", file=sys.stderr)
    print(f"  min_keys: {args.min_keys}", file=sys.stderr)
    print("  Cardinality check PASSED. Actual replay requires fase with",
          file=sys.stderr)
    print("  VisualParity CLI built and capture_orchestrator implemented.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
