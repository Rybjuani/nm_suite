#!/usr/bin/env python3
"""harness/v3/tests/test_bundle_verifier.py - Bundle verifier tests (stdlib).

Tests:
  - Verify PASS on a valid bundle (built ad-hoc)
  - Verify FAIL when bundle.json is tampered
  - Verify FAIL when checksums.json missing
  - Verify FAIL when vp_build_sha256 not in allowlist

Run with: python harness/v3/tests/test_bundle_verifier.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFIER = REPO_ROOT / "harness" / "v3" / "bundle_verifier.py"


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        capture_output=True, text=True, timeout=30,
    )
    return (proc.returncode, proc.stdout, proc.stderr)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _make_bundle(bundle_dir: Path, vp_build_sha: str = "unbuilt-fase-1-scaffold") -> str:
    """Build a minimal valid bundle and return its sha256.

    The trick: bundle_sha256 must equal the hash of the final bundle.json
    bytes. But bundle.json contains bundle_sha256 inside it. We solve this
    by writing the file first with a placeholder, hashing it, then checking
    that the verifier reads the actual file hash (not the field value).
    The verifier compares the field in checksums.json against the actual
    file hash. So we:
      1. Write bundle.json WITHOUT checksums field (or with placeholder).
      2. Hash the actual file bytes.
      3. Write checksums.json with that hash.
    The bundle.json's own checksums field is informational; the verifier
    trusts checksums.json as the source of truth.
    """
    import hashlib
    bundle = {
        "schema": "visualparity.bundle.v1",
        "eol": "lf",
        "generated_at_utc": "2026-01-01T00:00:00Z",
        "git_head": "deadbeef",
        "vp_build_sha256": vp_build_sha,
        "surfaces": [
            {
                "surface_key": "suite:test@light",
                "status": "NO_DIFF",
                "canonical_png_sha256": "abc",
                "actual_png_sha256": "abc",
                "canonical_bytes": 100,
                "actual_bytes": 100,
            }
        ],
    }
    integrity_dir = bundle_dir / "integrity"
    integrity_dir.mkdir(parents=True, exist_ok=True)
    # Write bundle.json (LF normalized)
    bundle_json = json.dumps(bundle, indent=2).replace("\r\n", "\n")
    bundle_path = bundle_dir / "bundle.json"
    bundle_path.write_text(bundle_json, encoding="utf-8")
    # Hash the actual file bytes
    bundle_sha = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    # Write checksums.json referencing that hash
    checksums = {
        "schema": "visualparity.checksums.v1",
        "bundle_sha256": bundle_sha,
        "bundle_json_sha256": bundle_sha,
        "files": [{"path": "bundle.json", "sha256": bundle_sha,
                   "bytes": len(bundle_json.encode("utf-8"))}],
    }
    (integrity_dir / "checksums.json").write_text(
        json.dumps(checksums, indent=2), encoding="utf-8"
    )
    return bundle_sha


def test_verify_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bd = Path(tmp) / "bundle"
        bd.mkdir()
        _make_bundle(bd)
        rc, out, err = _run(["--bundle", str(bd)])
        _assert(rc == 0, f"valid bundle should VERIFY_PASS (exit 0), got {rc}: {err}")


def test_tamper_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bd = Path(tmp) / "bundle"
        bd.mkdir()
        _make_bundle(bd)
        # Tamper bundle.json
        bp = bd / "bundle.json"
        content = bp.read_text(encoding="utf-8")
        tampered = content.replace("suite:test@light", "suite:tampered@light")
        bp.write_text(tampered, encoding="utf-8")
        rc, _, err = _run(["--bundle", str(bd)])
        _assert(rc == 1, f"tampered bundle should VERIFY_FAIL (exit 1), got {rc}")
        _assert("bundle_sha256_mismatch" in err,
                f"err should mention mismatch: {err}")


def test_missing_checksums_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bd = Path(tmp) / "bundle"
        bd.mkdir()
        _make_bundle(bd)
        (bd / "integrity" / "checksums.json").unlink()
        rc, _, err = _run(["--bundle", str(bd)])
        _assert(rc == 1, f"missing checksums should VERIFY_FAIL (exit 1), got {rc}")
        _assert("checksums_json_missing" in err,
                f"err should mention checksums missing: {err}")


def test_vp_build_sha_not_in_allowlist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bd = Path(tmp) / "bundle"
        bd.mkdir()
        _make_bundle(bd, vp_build_sha="not-in-allowlist")
        # Use a fake lockfile with empty allowlist
        lockfile = Path(tmp) / "lock.json"
        lockfile.write_text(json.dumps({"allowlist": []}), encoding="utf-8")
        rc, _, err = _run(["--bundle", str(bd), "--lockfile", str(lockfile)])
        _assert(rc == 1, f"vp_build_sha not in allowlist should FAIL (exit 1), got {rc}")
        _assert("vp_build_sha256_not_in_allowlist" in err,
                f"err should mention allowlist: {err}")


def main() -> int:
    tests = [
        test_verify_pass,
        test_tamper_fails,
        test_missing_checksums_fails,
        test_vp_build_sha_not_in_allowlist,
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
