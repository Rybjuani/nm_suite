#!/usr/bin/env python3
"""Visual Auditor Spec (VAS) — canonical QA by declarative specifications.

Replaces V2/V3 paradigm of pixel-diff-between-engines with:
  - Human-written specs per surface (colors, layout, components, text, icons, shadows)
  - Capture verification via PIL/numpy + vas_engine (color clustering, shape analysis)
  - Actionable, no-render-noise reports

Usage:
    .venv\\Scripts\\python.exe qa\\visual_auditor_spec.py verify \
        --capture qa\\_captures_v8\\suite-home-light-960x600.png \
        --surface suite:home@light

    .venv\\Scripts\\python.exe qa\\visual_auditor_spec.py verify-all \
        --captures-dir qa\\_captures_v8 \
        --manifest qa\\_captures_v8\\CAPTURE_MANIFEST.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

import vas_engine


SPECS_PATH = Path(__file__).parent / "specs" / "specs.json"
TOLERANCE_COLOR = 12
TOLERANCE_POS_PCT = 5.0
TOLERANCE_SIZE_PCT = 10.0
# Presence thresholds, calibrated empirically against the 86-capture set with
# the border-artifact fix in vas_engine (a flat/blank region reads ~0). For the
# real captures the lowest valid text region read 0.011 and the lowest valid
# card-group signal read 0.039, while every blanked region read 0.000 — so these
# thresholds give clean separation (0 false positives, 0 missed blanks).
TEXT_PRESENCE_MIN = 0.005
CARD_STRUCTURE_MIN = 0.02
# Presence checks are skipped on regions thinner than this (degenerate spec
# artifacts, e.g. a header_text region that collapsed to a 7px sliver, cannot be
# measured reliably and would false-positive).
MIN_PRESENCE_REGION_PX = 10
# A card_group of count<2 is a single element (often an empty-state illustration)
# rather than a true group; structural banding is meaningless there, so the
# count check only runs for genuine groups. Single elements are still covered by
# the color check.
MIN_CARD_GROUP_COUNT = 2
# Layout: tolerance (in % of canvas height) for where content begins. The
# content top margin agreed mockup-vs-capture within 0.014 (max 0.033) across
# the 86 captures, so a 5% band flags a real vertical shift with no false
# positives. See vas_engine.content_top_margin.
LAYOUT_TOP_TOL_PCT = 5.0


@dataclass
class ColorSpec:
    hex: str

    def to_rgb(self) -> tuple[int, int, int]:
        h = self.lstrip_hash()
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def lstrip_hash(self) -> str:
        return self.hex.lstrip("#")


@dataclass
class RegionSpec:
    x_pct: float
    y_pct: float
    w_pct: float
    h_pct: float

    def to_pixels(self, w: int, h: int) -> tuple[int, int, int, int]:
        x = int(self.x_pct / 100.0 * w)
        y = int(self.y_pct / 100.0 * h)
        rw = int(self.w_pct / 100.0 * w)
        rh = int(self.h_pct / 100.0 * h)
        return x, y, rw, rh


@dataclass
class Divergence:
    component_id: str
    kind: str
    message: str
    severity: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    surface_key: str
    capture_path: str
    pass_count: int
    fail_count: int
    divergences: list[Divergence]
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_key": self.surface_key,
            "capture_path": self.capture_path,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "divergences": [
                {
                    "component_id": d.component_id,
                    "kind": d.kind,
                    "message": d.message,
                    "severity": d.severity,
                    "evidence": d.evidence,
                }
                for d in self.divergences
            ],
            "summary": self.summary,
            "canonical": self.fail_count == 0,
        }


class SpecVerifier:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.color_tol = spec.get("verification_engine", {}).get("color_tolerance", TOLERANCE_COLOR)
        self.pos_tol = spec.get("verification_engine", {}).get("position_tolerance_pct", TOLERANCE_POS_PCT)
        self.size_tol = spec.get("verification_engine", {}).get("size_tolerance_pct", TOLERANCE_SIZE_PCT)

    def verify(self, capture_path: Path, surface_key: str) -> VerificationResult:
        img = Image.open(capture_path).convert("RGB")
        arr = np.array(img)
        w, h = img.size

        surface_spec = self.spec.get("surfaces", {}).get(surface_key)
        if not surface_spec:
            return VerificationResult(
                surface_key=surface_key,
                capture_path=str(capture_path),
                pass_count=0,
                fail_count=1,
                divergences=[
                    Divergence(
                        component_id="_meta",
                        kind="MISSING_SPEC",
                        message=f"No spec defined for {surface_key}",
                        severity="high",
                    )
                ],
            )

        divergences: list[Divergence] = []
        pass_count = 0
        fail_count = 0

        # 1. Canvas background color
        canvas = surface_spec.get("canvas", {})
        expected_bg = canvas.get("background_color")
        if expected_bg:
            ok, ev = self._check_canvas_bg(arr, w, h, expected_bg)
            if ok:
                pass_count += 1
            else:
                fail_count += 1
                divergences.append(ev)

        # 2. Canvas size
        expected_w = canvas.get("width")
        expected_h = canvas.get("height")
        if expected_w and expected_h:
            if abs(w - expected_w) > 2 or abs(h - expected_h) > 2:
                fail_count += 1
                divergences.append(
                    Divergence(
                        component_id="canvas",
                        kind="SIZE_MISMATCH",
                        message=f"Canvas size {w}x{h} vs expected {expected_w}x{expected_h}",
                        severity="medium",
                        evidence={"actual": [w, h], "expected": [expected_w, expected_h]},
                    )
                )
            else:
                pass_count += 1

        # 3. Shadow / elevation. Coverage is limited (only a handful of surfaces
        # declare a shadow in the spec, because the mockup reference is mostly
        # flat) and detection is approximate (Qt renders box-shadow differently
        # from Chromium, and detect_shadows rides on color-based component
        # detection). But where the mockup declares a shadow and the capture is
        # flat, that is real elevation debt, so it is reported as a fail.
        effects = surface_spec.get("effects", {})
        if effects.get("shadow") is True:
            shadow_evidence = vas_engine.detect_shadows(arr, w, h, vas_engine.detect_components(arr, w, h))
            has_shadow = any(s["has_shadow"] for s in shadow_evidence)
            if not has_shadow:
                fail_count += 1
                divergences.append(
                    Divergence(
                        component_id="effects",
                        kind="SHADOW_MISMATCH",
                        message="Mockup declares a shadow but capture renders flat (no elevation detected)",
                        severity="medium",
                    )
                )
            else:
                pass_count += 1

        # 4. Layout — vertical start of content. Exact sub-component layout
        # (padding, gaps, grid alignment) is not robust across renderers, but the
        # row where content begins is (0/86 outside a 5% band). This catches a UI
        # that shifted vertically or gained/lost top padding.
        content_top_pct = canvas.get("content_top_pct")
        if content_top_pct is not None and expected_bg:
            bg_rgb = ColorSpec(expected_bg).to_rgb()
            actual_top = vas_engine.content_top_margin(arr, bg_rgb) * 100.0
            if abs(actual_top - content_top_pct) > LAYOUT_TOP_TOL_PCT:
                fail_count += 1
                divergences.append(
                    Divergence(
                        component_id="layout",
                        kind="LAYOUT_SHIFT",
                        message=f"Content starts at {actual_top:.1f}% of height vs expected {content_top_pct:.1f}% (>{LAYOUT_TOP_TOL_PCT}% shift)",
                        severity="medium",
                        evidence={"actual_top_pct": round(actual_top, 1), "expected_top_pct": content_top_pct},
                    )
                )
            else:
                pass_count += 1

        # 5. Components
        for comp in surface_spec.get("components", []):
            passed, comp_divs = self._check_component(img, arr, w, h, comp)
            pass_count += passed
            fail_count += len(comp_divs)
            divergences.extend(comp_divs)

        summary = (
            f"{surface_key}: {pass_count} pass, {fail_count} fail — "
            + ("CANONICAL" if fail_count == 0 else "NEEDS_FIX")
        )
        return VerificationResult(
            surface_key=surface_key,
            capture_path=str(capture_path),
            pass_count=pass_count,
            fail_count=fail_count,
            divergences=divergences,
            summary=summary,
        )

    def _check_canvas_bg(self, arr: np.ndarray, w: int, h: int, expected_hex: str) -> tuple[bool, Divergence | None]:
        expected = ColorSpec(expected_hex).to_rgb()
        corners = [
            arr[5, 5], arr[5, w - 5], arr[h - 5, 5], arr[h - 5, w - 5],
        ]
        med = np.median(corners, axis=0)
        delta = float(np.mean(np.abs(med - np.array(expected))))
        if delta <= 25:
            return True, None
        return False, Divergence(
            component_id="canvas",
            kind="COLOR_MISMATCH",
            message=f"Canvas background delta={delta:.1f} (expected {expected_hex}, got ~{self._rgb_to_hex(med)})",
            severity="high",
            evidence={"expected": expected_hex, "actual_approx": self._rgb_to_hex(med), "delta": delta},
        )

    def _check_component(
        self, img: Image.Image, arr: np.ndarray, w: int, h: int, comp: dict[str, Any]
    ) -> tuple[int, list[Divergence]]:
        """Run every applicable check for one component.

        Returns (checks_passed, divergences). A component may contribute several
        independent assertions (e.g. card_group is checked for both interior
        color and card-structure presence), so this returns a count + list
        rather than a single boolean.
        """
        comp_id = comp["id"]
        region = comp.get("region")
        if not region:
            return 0, []

        rs = RegionSpec(**region)
        x, y, rw, rh = rs.to_pixels(w, h)
        if x + rw > w:
            rw = w - x
        if y + rh > h:
            rh = h - y
        if rw <= 0 or rh <= 0:
            return 0, [
                Divergence(
                    component_id=comp_id,
                    kind="REGION_OUT_OF_BOUNDS",
                    message=f"Region {x},{y},{rw},{rh} exceeds canvas {w}x{h}",
                    severity="medium",
                )
            ]

        crop_arr = arr[y : y + rh, x : x + rw]
        passed = 0
        divs: list[Divergence] = []

        # Color hint check
        color_hint = comp.get("color_hint")
        if color_hint:
            expected = ColorSpec(color_hint).to_rgb()
            if crop_arr.shape[0] > 4 and crop_arr.shape[1] > 4:
                interior = crop_arr[2:-2, 2:-2]
            else:
                interior = crop_arr
            avg = np.mean(interior.reshape(-1, 3), axis=0)
            delta = float(np.mean(np.abs(avg - np.array(expected))))
            if delta > self.color_tol:
                divs.append(
                    Divergence(
                        component_id=comp_id,
                        kind="COLOR_MISMATCH",
                        message=f"Component {comp_id} color delta={delta:.1f} (expected {color_hint}, got ~{self._rgb_to_hex(avg)})",
                        severity="high",
                        evidence={"region": [x, y, rw, rh], "expected": color_hint, "actual": self._rgb_to_hex(avg), "delta": delta},
                    )
                )
            else:
                passed += 1

        # Text PRESENCE check (re-enabled). For regions the spec marks as
        # text_required, verify rendered glyphs exist via edge density. This is
        # the robust half of "text checks": presence flags a region that renders
        # blank (a real regression) without false positives. Text COLOR is NOT
        # checked — the auto-generated text_color_hint samples non-text elements
        # and diverges from the capture on 72% of regions, so it is unreliable
        # without OCR and intentionally omitted. Degenerate (very thin) spec
        # regions cannot be measured and are skipped rather than flagged.
        if (
            comp.get("type") == "text"
            and comp.get("text_required")
            and rh >= MIN_PRESENCE_REGION_PX
            and rw >= MIN_PRESENCE_REGION_PX
        ):
            density = vas_engine.region_text_presence(arr, x, y, rw, rh)
            if density < TEXT_PRESENCE_MIN:
                divs.append(
                    Divergence(
                        component_id=comp_id,
                        kind="TEXT_MISSING",
                        message=f"Required text region {comp_id} appears blank (edge density {density:.4f} < {TEXT_PRESENCE_MIN})",
                        severity="high",
                        evidence={"region": [x, y, rw, rh], "edge_density": round(density, 4), "min": TEXT_PRESENCE_MIN},
                    )
                )
            else:
                passed += 1

        # COUNT check (re-enabled as presence). Exact card counts are not robust
        # across renderers (>30% divergence on ~35% of surfaces), so instead of
        # asserting the stored count we verify a genuine card_group (count>=2)
        # actually contains card structure: at least one horizontal content band
        # with measurable edge signal. This catches a card group that failed to
        # render while staying false-positive-free on valid captures.
        if comp.get("type") == "card_group" and comp.get("count", 0) >= MIN_CARD_GROUP_COUNT:
            bands, sig = vas_engine.region_card_structure(arr, x, y, rw, rh)
            if bands < 1 or sig < CARD_STRUCTURE_MIN:
                divs.append(
                    Divergence(
                        component_id=comp_id,
                        kind="CARD_GROUP_EMPTY",
                        message=f"card_group {comp_id} shows no card structure (bands={bands}, signal={sig:.3f}); expected ~{comp.get('count')} cards",
                        severity="high",
                        evidence={"region": [x, y, rw, rh], "bands": bands, "signal": round(sig, 3), "expected_count": comp.get("count")},
                    )
                )
            else:
                passed += 1

        # ----------------------------------------------------------------------
        # Dimensions measured against the 86-capture set and INTENTIONALLY
        # DISABLED — each fails the "robust between HTML mockup and Qt capture"
        # bar (>15% divergence) or only works on a generic region that does not
        # map to the component-specific debt it would claim to check. The common
        # root cause is the same as text-color: these properties live in
        # individual elements (avatars, checkboxes, icons, charts, buttons) that
        # cannot be isolated reliably across two renderers without OCR/segmentation.
        #
        #   SHAPE (corner roundedness)  — 25% disagree mockup-vs-capture on the
        #       card_group bbox corners (max diff 1.0). Per-element shape (square
        #       vs round avatar/checkbox) needs element isolation; not robust.
        #   PROPORTION (content area frac) — 14% disagree, but the failures are
        #       dark-theme dialogs where content barely differs from background,
        #       i.e. detector noise that would false-positive, not real debt.
        #   GRADIENT — stable (~10%) only on the generic card_group region, which
        #       is not where the real gradient debt lives (chart fill, radial
        #       breathing circle). Those are unlabeled in the spec; not shippable
        #       without per-component regions that don't detect robustly.
        #   TYPOGRAPHY (line count) — 40% diverge >30% relative. Line/band counts
        #       are render-dependent, same instability as exact card counts.
        #   CONTRAST (WCAG text vs bg) — 62% false positives. Needs glyph
        #       isolation; real text already measures ~1.0-1.9 like "invisible".
        #   ICON (presence/count) — 16% false positives; exact counts are noise
        #       (mockup "icon" counts reach 200+). Needs OCR/template matching.
        #   BORDER (outline) — region-perimeter edge density is renderer-stable
        #       but only measures the card_group bbox edge, not per-card outlines,
        #       and overlaps the card-structure check; omitted to avoid a
        #       misleadingly-named assertion.
        # ----------------------------------------------------------------------

        return passed, divs

    def _rgb_to_hex(self, rgb: np.ndarray | tuple[float, float, float]) -> str:
        r, g, b = rgb
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _load_specs() -> dict[str, Any]:
    with open(SPECS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_verify(args: argparse.Namespace) -> int:
    specs = _load_specs()
    verifier = SpecVerifier(specs)
    result = verifier.verify(Path(args.capture), args.surface)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.fail_count == 0 else 1


def cmd_verify_all(args: argparse.Namespace) -> int:
    specs = _load_specs()
    verifier = SpecVerifier(specs)
    capture_dir = Path(args.captures_dir)
    manifest_path = Path(args.manifest) if args.manifest else None

    surfaces_to_check = list(specs.get("surfaces", {}).keys())
    if manifest_path and manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        captures = {}
        for entry in manifest.get("results", manifest):
            if isinstance(entry, dict) and "app" in entry and "view" in entry and "theme" in entry:
                sk = f"{entry['app']}:{entry['view']}@{entry['theme']}"
                captures[sk] = str(capture_dir / entry.get("file", ""))
    else:
        captures = {}
        for sk in surfaces_to_check:
            parts = sk.replace("@", "-").replace(":", "-")
            for f in capture_dir.glob("*.png"):
                if parts in f.name:
                    captures[sk] = str(f)
                    break

    results: list[dict[str, Any]] = []
    any_fail = False
    for sk in surfaces_to_check:
        cap_path = captures.get(sk)
        if not cap_path or not Path(cap_path).exists():
            print(f"SKIP {sk}: capture not found")
            continue
        result = verifier.verify(Path(cap_path), sk)
        results.append(result.to_dict())
        if result.fail_count > 0:
            any_fail = True
        print(f"{result.summary}")

    report_path = capture_dir.parent / "_visual_auditor_spec" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport: {report_path}")
    return 1 if any_fail else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Visual Auditor Spec — canonical QA by specifications")
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser("verify", help="Verify one capture against one surface spec")
    p_verify.add_argument("--capture", required=True, help="Path to capture PNG")
    p_verify.add_argument("--surface", required=True, help="Surface key (e.g. suite:home@light)")
    p_verify.set_defaults(func=cmd_verify)

    p_all = sub.add_parser("verify-all", help="Verify all captures in directory against all specs")
    p_all.add_argument("--captures-dir", required=True, help="Directory with capture PNGs")
    p_all.add_argument("--manifest", help="Optional CAPTURE_MANIFEST.json")
    p_all.set_defaults(func=cmd_verify_all)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
