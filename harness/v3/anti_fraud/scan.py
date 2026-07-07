#!/usr/bin/env python3
"""harness/v3/anti_fraud/scan.py - Anti-fraud scanner (Fase 2 initial).

Known-vector initial coverage. NOT 100%. NOT total immunity.

Vectors in Fase 2:
  - asset_byte_identity: scan product dirs (app/, hub/, shared/) for PNGs
    whose raw-bytes SHA256 matches a canonical PNG hash. NO EOL
    normalization on PNGs (V2 bug fixed).

Vectors deferred to later fases:
  - string_tokens, pixmap_with_reference, modal_backdrop_constants,
    ast_scan, canonical_png_in_record, capture_v8_integrity,
    sidecar_provenance.

Usage:
    python harness/v3/anti_fraud/scan.py [--json <path>]

Exit codes:
    0  CLEAN
    1  DIRTY (violations found)
    2  ERROR
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CANON_DIR = REPO_ROOT / "qa" / "_mockup_canonical"
PRODUCT_ROOTS = [REPO_ROOT / "app", REPO_ROOT / "hub", REPO_ROOT / "shared"]


def sha256_file_raw(path: Path) -> str:
    """SHA256 over raw bytes. NO EOL normalization. PNGs are binary."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_canonical_hashes() -> dict[str, str]:
    """Returns {filename: sha256} for every canonical PNG."""
    hashes: dict[str, str] = {}
    if not CANON_DIR.exists():
        return hashes
    for png in CANON_DIR.glob("*.png"):
        try:
            hashes[png.name] = sha256_file_raw(png)
        except OSError:
            continue
    return hashes


def scan_product_dirs(canonical_hashes: dict[str, str]) -> list[dict]:
    """Find PNGs in product dirs whose raw SHA256 matches a canonical hash."""
    violations: list[dict] = []
    for root in PRODUCT_ROOTS:
        if not root.exists():
            continue
        for png in root.rglob("*.png"):
            try:
                h = sha256_file_raw(png)
            except OSError:
                continue
            for canon_name, canon_h in canonical_hashes.items():
                if h == canon_h:
                    violations.append({
                        "kind": "asset_canonical_identity",
                        "file": str(png.relative_to(REPO_ROOT)),
                        "matched_canonical": canon_name,
                        "sha256": h,
                    })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None,
                        help="Also write JSON report to this path.")
    args = parser.parse_args()

    canonical_hashes = load_canonical_hashes()
    if not canonical_hashes:
        print("ERROR: no canonical PNGs found in qa/_mockup_canonical/",
              file=sys.stderr)
        return 2

    violations = scan_product_dirs(canonical_hashes)
    report = {
        "scan": "anti_fraud_v3_fase2",
        "coverage": "known_vector_initial_coverage_NOT_100_percent",
        "vectors_implemented": ["asset_byte_identity"],
        "vectors_deferred": [
            "string_tokens", "pixmap_with_reference",
            "modal_backdrop_constants", "ast_scan",
            "canonical_png_in_record", "capture_v8_integrity",
            "sidecar_provenance",
        ],
        "canonical_hashes_count": len(canonical_hashes),
        "violations_count": len(violations),
        "violations": violations,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if violations:
        print("DIRTY: anti_fraud_v3_fase2", file=sys.stderr)
        print(f"  count: {len(violations)}", file=sys.stderr)
        for v in violations:
            print(f"  - {v['kind']}: {v['file']} matches canonical {v['matched_canonical']}",
                  file=sys.stderr)
        return 1
    print("CLEAN: anti_fraud_v3_fase2 (known-vector initial coverage)")
    print(f"  canonical_hashes_scanned: {len(canonical_hashes)}")
    print(f"  product_dirs_scanned: {[r.name for r in PRODUCT_ROOTS if r.exists()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
