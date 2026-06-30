#!/usr/bin/env python3
"""VAS Gate — validates the VAS introspection sidecar for closure approval.

Usage:
    python qa/vas_gate.py [--key KEY] [--sidecar PATH]

Exit codes:
    0  PASS — the sidecar is valid and the key (or all entries) meet closure bar.
    1  FAIL — sidecar missing, key missing, fail_count > 0, or critical divergences.

Closure bar (all must hold):
    1. Sidecar file exists and is valid JSON.
    2. If --key is given, that surface_key must be present.
    3. fail_count == 0 for the validated entry(ies).
    4. Zero divergences of severity "high" or "medium".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_SIDECAR = Path("qa/_visual_auditor_spec/introspection.json")

BLOCKING_SEVERITIES = {"high", "medium"}


def _load_sidecar(path: Path) -> list[dict]:
    """Load and validate the sidecar is a JSON list of entries."""
    if not path.exists():
        print(f"VAS GATE FAIL: sidecar not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"VAS GATE FAIL: sidecar is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print(
            f"VAS GATE FAIL: sidecar root is {type(data).__name__}, expected a JSON array",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(data) == 0:
        print("VAS GATE FAIL: sidecar is empty (no VAS entries)", file=sys.stderr)
        sys.exit(1)
    return data


def _check_entry(entry: dict, key: str | None) -> list[str]:
    """Return a list of failure reasons for a single entry. Empty = pass."""
    reasons: list[str] = []
    surface = entry.get("surface_key", "<missing surface_key>")

    if key is not None and entry.get("surface_key") != key:
        return []  # Not the key we're checking; skip silently.

    # fail_count
    fail_count = entry.get("fail_count")
    if fail_count is None:
        reasons.append(f"[{surface}] missing key 'fail_count'")
    elif not isinstance(fail_count, int):
        reasons.append(f"[{surface}] 'fail_count' is {type(fail_count).__name__}, expected int")
    elif fail_count != 0:
        reasons.append(f"[{surface}] fail_count={fail_count} (must be 0)")

    # divergences — blocking severities
    divergences = entry.get("divergences", [])
    if not isinstance(divergences, list):
        divergences = []
    blocking = [
        d for d in divergences
        if isinstance(d, dict) and d.get("severity", "").lower() in BLOCKING_SEVERITIES
    ]
    if blocking:
        kinds = ", ".join(
            f"{d.get('kind', '?')}({d.get('severity', '?')})" for d in blocking
        )
        reasons.append(
            f"[{surface}] {len(blocking)} blocking divergence(s): {kinds}"
        )

    return reasons


def validate(path: Path, key: str | None) -> bool:
    """Run the gate. Returns True on PASS, exits non-zero on FAIL."""
    entries = _load_sidecar(path)

    if key is not None:
        matching = [e for e in entries if e.get("surface_key") == key]
        if not matching:
            print(
                f"VAS GATE FAIL: key '{key}' not found in sidecar "
                f"(has {len(entries)} entries: "
                f"{[e.get('surface_key', '?') for e in entries[:5]]}...)",
                file=sys.stderr,
            )
            return False
        to_check = matching
    else:
        to_check = entries

    all_reasons: list[str] = []
    for entry in to_check:
        if not isinstance(entry, dict):
            all_reasons.append(f"Non-dict entry in sidecar: {entry!r}")
            continue
        all_reasons.extend(_check_entry(entry, None))  # check all filtered entries

    if all_reasons:
        print("VAS GATE FAIL:", file=sys.stderr)
        for r in all_reasons:
            print(f"  - {r}", file=sys.stderr)
        return False

    if key is not None:
        print(f"VAS GATE PASS: key '{key}' — fail_count=0, zero high/medium divergences.")
    else:
        print(f"VAS GATE PASS: all {len(to_check)} entries — fail_count=0, zero high/medium divergences.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate VAS sidecar for closure approval."
    )
    parser.add_argument(
        "--key",
        default=None,
        help="Exact surface_key to validate (e.g. 'suite:recuperar-acceso@light'). "
        "If omitted, validates all entries.",
    )
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=DEFAULT_SIDECAR,
        help=f"Path to introspection.json (default: {DEFAULT_SIDECAR})",
    )
    args = parser.parse_args()

    ok = validate(args.sidecar, args.key)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
