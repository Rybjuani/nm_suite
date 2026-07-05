#!/usr/bin/env python3
"""PoC — canonical-copy injection false-PASS in the visual gate.

Self-contained reproduction (no external report needed): reads real canonicals
from ``qa/_mockup_canonical`` and drives the ACTUAL comparator
(``compare_pair``, default thresholds). It demonstrates two confirmed
false-PASS vectors on HEAD-before-hardening:

  V1  ``-empty`` unconditional trivial exemption: a content-rich ``*-empty``
      canonical copied verbatim as the "runtime capture" is NOT flagged
      suspicious and PASSes.
  V2  Noised canonical copy: a canonical copied with graded uniform noise lands
      in ``status=PASS`` on non-``-empty`` surfaces while GLOBAL ssim stays far
      above the honest corpus ceiling — evading both ``suspicious_perfect_match``
      (needs changed==0) and ``near_perfect_match`` (needs changed<0.005).

Run::

    .\\.venv\\Scripts\\python.exe reports/qa/governance_hardening/poc/poc_canonical_injection.py

Before hardening: several rows print ``PASS`` (false pass).
After hardening:  the same rows print ``SUSPICIOUS_PERFECT_MATCH`` /
                  ``NEAR_PERFECT_MATCH`` (blocked).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from qa.layered_visual_compare import (  # noqa: E402
    LayeredThresholds,
    compare_pair,
    parse_capture_name,
)

CANON = ROOT / "qa" / "_mockup_canonical"

# key -> noise fractions to probe. 0.0 = verbatim copy.
CASES = {
    "suite:timer-empty@light": [0.0, 0.01, 0.03],      # V1: -empty exemption
    "hub:pacientes-empty@light": [0.0, 0.01],          # V1: -empty exemption
    "suite:home@light": [0.0, 0.03, 0.06, 0.10],       # V2: dense injection band
    "suite:recuperar-acceso@light": [0.0, 0.03, 0.10],  # V2: text-dense form
}


def find_canonical(key: str) -> Path | None:
    app, rest = key.split(":", 1)
    view, theme = rest.split("@", 1)
    for p in CANON.glob(f"{app}-{view}-{theme}-*.png"):
        return p
    return None


def add_noise(arr: np.ndarray, frac: float, amp: int, rng) -> np.ndarray:
    if frac <= 0:
        return arr
    out = arr.astype(np.int16).copy()
    h, w, _ = out.shape
    n = int(h * w * frac)
    ys = rng.integers(0, h, n)
    xs = rng.integers(0, w, n)
    delta = rng.choice([-amp, amp], size=(n, 3))
    out[ys, xs] = np.clip(out[ys, xs] + delta, 0, 255)
    return out.astype(np.uint8)


def main() -> int:
    rng = np.random.default_rng(1234)
    th = LayeredThresholds()
    false_pass = 0
    print(
        f"{'key':40s} {'noise':>6s} {'changed':>8s} {'gssim':>7s} "
        f"{'wssim':>7s} {'susp':>5s} {'near':>5s} {'STATUS':>24s}"
    )
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "c").mkdir()
        (tmp / "a").mkdir()
        for key, fracs in CASES.items():
            cpath = find_canonical(key)
            if not cpath:
                print(f"  MISSING canonical for {key}")
                continue
            base = np.asarray(Image.open(cpath).convert("RGB"))
            for frac in fracs:
                actual = add_noise(base, frac, amp=40, rng=rng)
                Image.fromarray(base).save(tmp / "c" / cpath.name)
                Image.fromarray(actual).save(tmp / "a" / cpath.name)
                res = compare_pair(
                    key,
                    parse_capture_name(tmp / "c" / cpath.name),
                    parse_capture_name(tmp / "a" / cpath.name),
                    thresholds=th,
                    use_odiff=False,
                )
                m = res.metrics
                flag = " <== FALSE PASS" if res.status == "PASS" else ""
                if res.status == "PASS":
                    false_pass += 1
                print(
                    f"{key:40s} {frac:6.2f} {m['changed_pixel_ratio']:8.4f} "
                    f"{m['ssim']:7.4f} {m['windowed_ssim']:7.4f} "
                    f"{str(res.suspicious_perfect_match):>5s} "
                    f"{str(res.near_perfect_match):>5s} {res.status:>24s}{flag}"
                )
    print(f"\nfalse_pass_rows: {false_pass}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
