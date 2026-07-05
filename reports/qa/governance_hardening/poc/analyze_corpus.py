#!/usr/bin/env python3
"""Empirical calibration analysis over the real 116-key corpus.

Reads the full layered compare report + canonical PNGs to answer:
  1. Which `-empty` canonicals are content-rich (std >= 2.0)? -> the name-based
     trivial exemption exempts these from perfect/near-perfect fraud detection.
  2. What is the max honest GLOBAL ssim across all PASS keys? -> calibrates a
     global-ssim fraud floor that sits above every honest render but below a
     canonical-copy injection (~1.0).
  3. Distribution of global ssim per key, to prove a fraud floor won't false
     positive honest renders.
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[4]
# Point at any full layered_visual_compare report (regenerate with:
#   python qa/layered_visual_compare.py --canonical qa/_mockup_canonical \
#     --actual qa/_captures_v8 --out-dir reports/qa/governance_baseline_compare)
REPORT = ROOT / "reports" / "qa" / "governance_baseline_compare" / "LAYERED_VISUAL_REPORT.json"
CANON = ROOT / "qa" / "_mockup_canonical"

report = json.loads(REPORT.read_text(encoding="utf-8"))
results = report["results"]
print(f"REPORT keys: {len(results)}  evidence_valid={report['report_evidence_valid']}")

def canon_std(path: Path) -> float:
    arr = np.asarray(Image.open(path).convert("L"), dtype=np.float64)
    return float(arr.std())

# 1. -empty canonical std
print("\n=== -empty canonical grayscale std (name-exemption targets) ===")
empty_rows = []
for r in results:
    if r["view"].endswith("-empty"):
        cf = r.get("canonical_file")
        std = canon_std(Path(cf)) if cf and Path(cf).exists() else None
        empty_rows.append((r["key"], std, r["metrics"].get("ssim"), r["status"]))
for key, std, ssim, status in sorted(empty_rows):
    flag = "CONTENT-RICH (exempt but shouldn't be)" if (std or 0) >= 2.0 else "flat(<2.0)"
    print(f"  {key:42s} std={std:8.3f} honest_global_ssim={ssim}  status={status}  {flag}")

# 2. max honest global ssim across all keys
print("\n=== GLOBAL ssim distribution across all keys ===")
ssims = []
for r in results:
    s = r["metrics"].get("ssim")
    if s is not None:
        ssims.append((float(s), r["key"], r["status"], r["metrics"].get("canonical_gray_std")))
ssims.sort(reverse=True)
print(f"count={len(ssims)}  max={ssims[0][0]:.5f}  min={ssims[-1][0]:.5f}")
print("Top 12 highest honest global ssim (candidate false-fraud-positives if floor too low):")
for s, key, status, cstd in ssims[:12]:
    print(f"  {s:.5f}  {key:42s} status={status} canon_std={cstd}")
print("... quantiles:")
vals = np.array([s for s, *_ in ssims])
for q in (0.5, 0.9, 0.95, 0.99, 1.0):
    print(f"  q{int(q*100):3d} = {np.quantile(vals, q):.5f}")

# 3. windowed ssim distribution (text-dense uses this)
print("\n=== WINDOWED ssim distribution ===")
w = sorted((float(r['metrics'].get('windowed_ssim', 0)), r['key']) for r in results)
warr = np.array([x for x, _ in w])
print(f"max windowed={w[-1][0]:.5f} at {w[-1][1]}")
for q in (0.9, 0.95, 0.99, 1.0):
    print(f"  q{int(q*100):3d} = {np.quantile(warr, q):.5f}")
print("Top 8 windowed:")
for x, k in w[::-1][:8]:
    print(f"  {x:.5f}  {k}")
