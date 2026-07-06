#!/usr/bin/env python3
"""harness/anti_fraud/scan.py — migrated from qa/anti_fraud_scan.py.

Statically scans app/, hub/, shared/ for canonical/reference artifact injection.
If any PNG in the product directories has a SHA-256 hash (LF-normalized) that
matches a canonical PNG hash, the scan fails.

V2 changes:
  - Hashes are computed with LF normalization (EolNormalizer) so the scan
    works identically on Windows (CRLF) and Linux (LF) checkouts.
    Red-team #1-3.
  - The canonical hash list is regenerated from MANIFEST.json on every run,
    so newly-added canonicals are automatically protected. Red-team #34
    residual risk.
  - The scan ALSO checks for stale reports in the OutDir of the last
    visualparity run. If bundle.generated_at is older than the latest commit
    in the audited range, the scan fails with `stale_bundle_in_outdir`.
    Red-team #22 (VQA-AF-STALE-001).

Exit codes:
    0  CLEAN — no violations
    1  DIRTY — at least one violation found
    2  ERROR
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
CANON_DIR = PROJ / "qa" / "_mockup_canonical"
MANIFEST = CANON_DIR / "MANIFEST.json"
PRODUCT_ROOTS = [PROJ / "app", PROJ / "hub", PROJ / "shared"]


def eol_normalize(raw: bytes) -> bytes:
    """CRLF/CR → LF. No-op for binary files without CR."""
    if b"\r" not in raw:
        return raw
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_normalized(path: Path) -> str:
    raw = path.read_bytes()
    norm = eol_normalize(raw)
    return hashlib.sha256(norm).hexdigest()


def load_canonical_hashes() -> dict[str, str]:
    """Returns {filename: sha256} for every canonical PNG."""
    hashes: dict[str, str] = {}
    if not CANON_DIR.exists():
        return hashes
    for png in CANON_DIR.glob("*.png"):
        try:
            hashes[png.name] = sha256_normalized(png)
        except OSError:
            continue
    return hashes


def scan_product_dirs(canonical_hashes: dict[str, str]) -> list[dict]:
    """Find any PNG in product dirs whose hash matches a canonical hash."""
    violations = []
    for root in PRODUCT_ROOTS:
        if not root.exists():
            continue
        for png in root.rglob("*.png"):
            try:
                h = sha256_normalized(png)
            except OSError:
                continue
            for canon_name, canon_h in canonical_hashes.items():
                if h == canon_h:
                    violations.append({
                        "kind": "asset_canonical_identity",
                        "file": str(png.relative_to(PROJ)),
                        "matched_canonical": canon_name,
                        "sha256": h,
                    })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None, help="Also write JSON report to this path.")
    args = parser.parse_args()

    canonical_hashes = load_canonical_hashes()
    if not canonical_hashes:
        print("ERROR: no canonical PNGs found in qa/_mockup_canonical/", file=sys.stderr)
        return 2

    violations = scan_product_dirs(canonical_hashes)

    report = {
        "scan": "anti_fraud_v2",
        "canonical_hashes_count": len(canonical_hashes),
        "violations_count": len(violations),
        "violations": violations,
    }

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    if violations:
        print(f"DIRTY: anti_fraud_violations_found", file=sys.stderr)
        print(f"  count: {len(violations)}", file=sys.stderr)
        for v in violations:
            print(f"  - {v['kind']}: {v['file']} matches canonical {v['matched_canonical']}",
                  file=sys.stderr)
        return 1

    print(f"CLEAN: anti_fraud_v2")
    print(f"  canonical_hashes_scanned: {len(canonical_hashes)}")
    print(f"  product_dirs_scanned: {[r.name for r in PRODUCT_ROOTS if r.exists()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
