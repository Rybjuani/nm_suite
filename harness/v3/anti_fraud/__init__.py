#!/usr/bin/env python3
"""harness/v3/anti_fraud/__init__.py - Anti-fraud multi-vector scanner.

Fase 2: initial coverage of known vectors. NOT 100% coverage. NOT total
immunity. Denylist real but not the only defense.

Each vector is a separate module. The scanner aggregates results.

Vectors implemented in Fase 2 (structural only):
  - asset_byte_identity: scan product dirs for PNGs whose SHA256 matches
    a canonical PNG hash. (Inherited from V2 scan.py but fixed: no EOL
    normalization on PNGs - they are binary.)

Vectors deferred to later fases:
  - string_tokens
  - pixmap_with_reference
  - modal_backdrop_constants
  - ast_scan
  - canonical_png_in_record
  - capture_v8_integrity
  - sidecar_provenance
"""
