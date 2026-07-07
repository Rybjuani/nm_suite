#!/usr/bin/env python3
"""harness/v3/bundle_verifier.py - VisualParity bundle verifier.

Verifies that a VisualParity bundle directory contains the required files
and that the recorded bundle_sha256 matches the actual bytes of bundle.json.
Also verifies that vp_build_sha256 is in the allowlist (visualparity.lock.json).

NO runtime authority. Does NOT close keys. Does NOT invoke V1/V2. Does NOT
invoke capture_v8. Does NOT decide closure - only emits VERIFY_PASS or
VERIFY_FAIL with reasons.

Usage:
    python harness/v3/bundle_verifier.py --bundle <dir> [--lockfile <path>]

Exit codes:
    0  VERIFY_PASS
    1  VERIFY_FAIL (reasons printed to stderr)
    2  ERROR (internal)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCKFILE = REPO_ROOT / "tools/visualparity/visualparity.lock.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_bundle(bundle_dir: Path, lockfile: Path) -> tuple[bool, list[str]]:
    """Return (ok, reasons). ok=True means VERIFY_PASS."""
    reasons: list[str] = []

    bundle_json = bundle_dir / "bundle.json"
    checksums_json = bundle_dir / "integrity" / "checksums.json"

    if not bundle_json.exists():
        reasons.append("bundle_json_missing")
        return (False, reasons)
    if not checksums_json.exists():
        reasons.append("checksums_json_missing")
        return (False, reasons)

    try:
        bundle_data = json.loads(bundle_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        reasons.append(f"bundle_json_invalid:{e}")
        return (False, reasons)
    try:
        checksums_data = json.loads(checksums_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        reasons.append(f"checksums_json_invalid:{e}")
        return (False, reasons)

    # Schema check
    schema = bundle_data.get("schema")
    if schema != "visualparity.bundle.v1":
        reasons.append(f"unexpected_schema:{schema}")
    eol = bundle_data.get("eol")
    if eol != "lf":
        reasons.append(f"eol_not_lf:{eol}")
    vp_build_sha = bundle_data.get("vp_build_sha256")
    if not vp_build_sha:
        reasons.append("vp_build_sha256_missing")

    # bundle_sha256 verification
    expected_bundle_sha = checksums_data.get("bundle_sha256")
    actual_bundle_sha = sha256_file(bundle_json)
    if expected_bundle_sha != actual_bundle_sha:
        reasons.append(
            f"bundle_sha256_mismatch:expected={expected_bundle_sha},"
            f"actual={actual_bundle_sha}"
        )

    # vp_build_sha256 allowlist check
    if vp_build_sha and lockfile.exists():
        try:
            lock_data = json.loads(lockfile.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            reasons.append("lockfile_invalid_json")
            lock_data = {}
        allowlist = lock_data.get("allowlist", [])
        allowed_shas = {
            entry.get("vp_build_sha256")
            for entry in allowlist
            if isinstance(entry, dict)
        }
        if vp_build_sha not in allowed_shas:
            reasons.append(
                f"vp_build_sha256_not_in_allowlist:{vp_build_sha}"
            )
    elif vp_build_sha and not lockfile.exists():
        reasons.append(f"lockfile_missing:{lockfile}")

    return (len(reasons) == 0, reasons)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--lockfile", default=DEFAULT_LOCKFILE, type=Path)
    args = parser.parse_args()

    if not args.bundle.exists():
        print(f"ERROR: bundle dir not found: {args.bundle}", file=sys.stderr)
        return 2

    ok, reasons = verify_bundle(args.bundle, args.lockfile)
    if ok:
        print("VERIFY_PASS: bundle_verifier_v3")
        print(f"  bundle: {args.bundle}")
        return 0
    print("VERIFY_FAIL: bundle_verifier_v3", file=sys.stderr)
    print(f"  bundle: {args.bundle}", file=sys.stderr)
    for r in reasons:
        print(f"  - {r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
