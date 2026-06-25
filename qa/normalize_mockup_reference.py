"""qa/normalize_mockup_reference.py — Normalize mockup reference PNGs to canonical sizes.

Reads qa/mockup_reference_static/ (86 PNGs, variable sizes) and produces
qa/mockup_reference_normalized/ with per-surface normalization using one of
7 documented methods. Generates manifest.json with metadata per surface.

USAGE:
    .venv\\Scripts\\python.exe qa\\normalize_mockup_reference.py
    .venv\\Scripts\\python.exe qa\\normalize_mockup_reference.py doctor
    .venv\\Scripts\\python.exe qa\\normalize_mockup_reference.py audit
    .venv\\Scripts\\python.exe qa\\normalize_mockup_reference.py regenerate --surface KEY --method METHOD --reason REASON
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from PIL import Image

_PROJ = Path(__file__).resolve().parent.parent
_STATIC_DIR = _PROJ / "qa" / "mockup_reference_static"
_NORM_DIR = _PROJ / "qa" / "mockup_reference_normalized"
_MANIFEST_PATH = _NORM_DIR / "manifest.json"

# Mapping from manifest (screen_id, state_id) -> capture_v8 view name
_MANIFEST_TO_VIEW: dict[tuple[str, str], str] = {
    ("home", "score"): "home",
    ("home", "noscore"): "home-no-score",
    ("onboarding", "normal"): "onboarding",
    ("onboarding", "error"): "onboarding-error",
    ("recuperar", "default"): "recuperar-acceso",
    ("animo", "default"): "animo",
    ("respiracion", "idle"): "respiracion",
    ("respiracion", "running"): "respiracion-running",
    ("respiracion", "paused"): "respiracion-paused",
    ("timer", "idle"): "timer",
    ("timer", "running"): "timer-running",
    ("timer", "paused"): "timer-paused",
    ("timer", "empty"): "timer-empty",
    ("rutina", "default"): "rutina",
    ("rutina", "add"): "rutina-add-task",
    ("rutina", "done"): "rutina-all-completed",
    ("rutina", "empty"): "rutina-empty",
    ("actividades", "default"): "actividades",
    ("actividades", "filtered"): "actividades-filtered",
    ("actividades", "marked"): "actividades-marked-hice",
    ("actividades", "empty"): "actividades-empty",
    ("avisos", "all"): "avisos",
    ("avisos", "active"): "avisos-filter-activos",
    ("avisos", "today"): "avisos-today",
    ("avisos", "search"): "avisos-search",
    ("avisos", "empty"): "avisos-empty",
    ("dbtnow", "default"): "dbt-now",
    ("dbtlib", "default"): "dbt-library",
    ("dbt-practice-stop", "stop-step-1"): "dbt-practice-stop",
    ("registro", "s0"): "registro",
    ("registro", "s1"): "registro-step1-emotion",
    ("registro", "s1otro"): "registro-step1-emotion-otro",
    ("registro", "s2"): "registro-step2-distortions",
    ("registro", "s3"): "registro-step3-filled",
    ("registro", "ok"): "registro-success",
    ("pacientes", "list"): "pacientes",
    ("pacientes", "empty"): "pacientes-empty",
    ("detalle", "default"): "detalle",
    ("detalle", "hub-tab-timer"): "detalle-plan-timer",
    ("detalle", "hub-tab-rutina"): "detalle-plan-rutina",
    ("detalle", "hub-tab-activacion"): "detalle-plan-activacion",
    ("textos", "default"): "textos-globales",
    ("detalle", "modal-resumen-ia"): "detalle-resumen-ia",
}

# Canonical target sizes per view (from capture_mockup.py / capture_v8.py)
_VIEW_TO_SIZE: dict[str, tuple[int, int]] = {
    "onboarding": (520, 600),
    "onboarding-error": (520, 600),
    "recuperar-acceso": (520, 600),
    "detalle-resumen-ia": (480, 325),
    "dbt-practice-stop": (520, 600),
}

Method = Literal[
    "identity",
    "resize_only",
    "resize+crop_center",
    "resize+crop_top",
    "resize+crop_bottom",
    "resize+pad_bottom_surface",
    "manual_override",
]


@dataclass
class NormEntry:
    surface_key: str
    theme: str
    view: str
    src_file: str
    src_width: int
    src_height: int
    target_width: int
    target_height: int
    method: Method
    method_params: dict | None
    lost_pixels_top: int
    lost_pixels_bottom: int
    pad_pixels: int
    lost_pct: float
    pad_pct: float
    review_required: bool
    review_reason: str | None
    regenerate_reason: str | None


def _target_size(view: str) -> tuple[int, int]:
    return _VIEW_TO_SIZE.get(view, (960, 600))


def _surface_key(view: str, theme: str) -> str:
    app = "hub" if view in (
        "pacientes", "pacientes-empty", "detalle", "detalle-plan-timer",
        "detalle-plan-rutina", "detalle-plan-activacion", "textos-globales",
        "detalle-resumen-ia",
    ) else "suite"
    return f"{app}:{view}@{theme}"


def _select_method(src_w: int, src_h: int, tgt_w: int, tgt_h: int) -> tuple[Method, dict, int, int, int, float]:
    """Select normalization method based on size delta.

    Returns: (method, method_params, lost_top, lost_bottom, pad_pixels, lost_pct)
    """
    if src_w == tgt_w and src_h == tgt_h:
        return "identity", {}, 0, 0, 0, 0.0

    # Resize width first, then handle height
    h_after_resize = int(src_h * (tgt_w / src_w))
    delta = h_after_resize - tgt_h

    if delta == 0:
        return "resize_only", {}, 0, 0, 0, 0.0

    if delta > 0:
        # Too tall, need to crop
        lost_pct = delta / h_after_resize * 100 if h_after_resize > 0 else 0.0
        if lost_pct < 5:
            crop_each = delta // 2
            return (
                "resize+crop_center",
                {},
                crop_each,
                delta - crop_each,
                0,
                lost_pct,
            )
        return (
            "manual_override",
            {"default": "resize+crop_center"},
            delta // 2,
            delta - delta // 2,
            0,
            lost_pct,
        )

    # Too short, need to pad
    pad = -delta
    if pad < 50:
        return "resize+pad_bottom_surface", {}, 0, 0, pad, 0.0

    return (
        "manual_override",
        {"default": "resize+crop_center"},
        0,
        0,
        pad,
        0.0,
    )


def _surface_color(image: Image.Image, theme: str) -> tuple[int, int, int]:
    """Extract surface color from top-left pixel (most reliable for mockup)."""
    px = image.getpixel((0, 0))
    if isinstance(px, (tuple, list)):
        return (int(px[0]), int(px[1]), int(px[2]))
    return (int(px), int(px), int(px))


def _normalize_image(
    src: Image.Image,
    method: Method,
    tgt_w: int,
    tgt_h: int,
    theme: str,
    lost_top: int,
    lost_bottom: int,
    pad_pixels: int,
) -> Image.Image:
    """Apply normalization method to produce target-sized image."""
    src_w, src_h = src.size

    if method == "identity":
        return src.copy().resize((tgt_w, tgt_h), Image.Resampling.LANCZOS) if (src_w, src_h) != (tgt_w, tgt_h) else src.copy()

    if method == "resize_only":
        return src.resize((tgt_w, tgt_h), Image.Resampling.LANCZOS)

    if method == "resize+crop_center":
        resized = src.resize((tgt_w, int(src_h * (tgt_w / src_w))), Image.Resampling.LANCZOS)
        rw, rh = resized.size
        top = lost_top
        bottom = rh - lost_bottom
        return resized.crop((0, top, rw, bottom))

    if method == "resize+crop_top":
        resized = src.resize((tgt_w, int(src_h * (tgt_w / src_w))), Image.Resampling.LANCZOS)
        rw, rh = resized.size
        return resized.crop((0, lost_top, rw, lost_top + tgt_h))

    if method == "resize+crop_bottom":
        resized = src.resize((tgt_w, int(src_h * (tgt_w / src_w))), Image.Resampling.LANCZOS)
        rw, rh = resized.size
        return resized.crop((0, 0, rw, tgt_h))

    if method == "resize+pad_bottom_surface":
        resized = src.resize((tgt_w, int(src_h * (tgt_w / src_w))), Image.Resampling.LANCZOS)
        rw, rh = resized.size
        result = Image.new("RGB", (tgt_w, tgt_h), _surface_color(src, theme))
        result.paste(resized, (0, 0))
        return result

    if method == "manual_override":
        # Default candidate generation: resize, then crop if too tall, or pad if too short
        resized = src.resize((tgt_w, int(src_h * (tgt_w / src_w))), Image.Resampling.LANCZOS)
        rw, rh = resized.size
        if rh > tgt_h:
            # Too tall: crop center
            top = lost_top
            bottom = rh - lost_bottom
            return resized.crop((0, top, rw, bottom))
        else:
            # Too short: pad bottom with surface color
            result = Image.new("RGB", (tgt_w, tgt_h), _surface_color(src, theme))
            result.paste(resized, (0, 0))
            return result

    raise ValueError(f"Unknown method: {method}")


def _build_entries() -> list[NormEntry]:
    """Build normalization entries from static manifest."""
    static_manifest = json.loads((_STATIC_DIR / "manifest.json").read_text(encoding="utf-8"))
    entries: list[NormEntry] = []

    for item in static_manifest["items"]:
        screen_id = item["screen_id"]
        state_id = item["state_id"]
        theme = item["theme"]
        src_path = _STATIC_DIR / item["relative_path"]

        view = _MANIFEST_TO_VIEW.get((screen_id, state_id))
        if not view:
            print(f"[WARN] No view mapping for ({screen_id}, {state_id})", file=sys.stderr)
            continue

        tgt_w, tgt_h = _target_size(view)

        with Image.open(src_path) as img:
            src_w, src_h = img.size

        method, method_params, lost_top, lost_bottom, pad_pixels, lost_pct = _select_method(
            src_w, src_h, tgt_w, tgt_h
        )

        review_required = lost_pct >= 5.0 or pad_pixels >= 50
        review_reason = None
        if review_required:
            if lost_pct >= 5.0:
                review_reason = f"lost_pct={lost_pct:.1f}% >= 5%"
            elif pad_pixels >= 50:
                review_reason = f"pad_pixels={pad_pixels} >= 50"

        entries.append(
            NormEntry(
                surface_key=_surface_key(view, theme),
                theme=theme,
                view=view,
                src_file=str(src_path.relative_to(_PROJ)),
                src_width=src_w,
                src_height=src_h,
                target_width=tgt_w,
                target_height=tgt_h,
                method=method,
                method_params=method_params,
                lost_pixels_top=lost_top,
                lost_pixels_bottom=lost_bottom,
                pad_pixels=pad_pixels,
                lost_pct=lost_pct,
                pad_pct=(pad_pixels / tgt_h * 100) if tgt_h > 0 else 0.0,
                review_required=review_required,
                review_reason=review_reason,
                regenerate_reason=None,
            )
        )

    return entries


def _write_normalized(entries: list[NormEntry]) -> None:
    """Write normalized PNGs and manifest."""
    _NORM_DIR.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        (_NORM_DIR / theme).mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []

    for entry in entries:
        src_path = _PROJ / entry.src_file
        with Image.open(src_path) as img:
            normalized = _normalize_image(
                img,
                entry.method,
                entry.target_width,
                entry.target_height,
                entry.theme,
                entry.lost_pixels_top,
                entry.lost_pixels_bottom,
                entry.pad_pixels,
            )

        out_path = _NORM_DIR / entry.theme / f"{entry.view}.png"
        normalized.save(out_path)

        manifest.append(asdict(entry))

    _MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {len(entries)} normalized PNGs + manifest.json")


def _cmd_normalize() -> int:
    entries = _build_entries()
    _write_normalized(entries)
    return 0


def _cmd_doctor() -> int:
    """Validate all normalized PNGs have canonical sizes."""
    if not _MANIFEST_PATH.exists():
        print("[FAIL] manifest.json not found. Run normalize first.")
        return 1

    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    canonical_sizes = {(960, 600), (520, 600), (480, 325)}
    errors = 0

    for entry in manifest:
        theme = entry["theme"]
        view = entry["view"]
        path = _NORM_DIR / theme / f"{view}.png"
        if not path.exists():
            print(f"[FAIL] Missing PNG: {path}")
            errors += 1
            continue

        with Image.open(path) as img:
            w, h = img.size

        if (w, h) not in canonical_sizes:
            print(f"[FAIL] Non-canonical size {w}x{h} for {entry['surface_key']}")
            errors += 1
        elif (w, h) != (entry["target_width"], entry["target_height"]):
            print(
                f"[FAIL] Size mismatch: {w}x{h} vs expected "
                f"{entry['target_width']}x{entry['target_height']} for {entry['surface_key']}"
            )
            errors += 1

    total = len(manifest)
    print(f"[OK] {total - errors}/{total} canonical sizes correct")
    if errors:
        print(f"[FAIL] {errors} size errors")
    return 0 if errors == 0 else 1


def _cmd_audit() -> int:
    """Audit normalization — report review_required surfaces."""
    if not _MANIFEST_PATH.exists():
        print("[FAIL] manifest.json not found. Run normalize first.")
        return 1

    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    total = len(manifest)
    size_mismatch = 0
    review_required = 0

    for entry in manifest:
        theme = entry["theme"]
        view = entry["view"]
        path = _NORM_DIR / theme / f"{view}.png"
        if not path.exists():
            size_mismatch += 1
            continue
        with Image.open(path) as img:
            w, h = img.size
        if (w, h) != (entry["target_width"], entry["target_height"]):
            size_mismatch += 1

        if entry["review_required"]:
            review_required += 1
            print(
                f"[REVIEW_REQUIRED] {entry['surface_key']}: "
                f"method={entry['method']}, {entry['review_reason']}"
            )

    print("\n[SUMMARY]")
    print(f"  Total surfaces: {total}")
    print(f"  Canonical sizes: {total - size_mismatch}/{total}")
    print(f"  Size mismatch: {size_mismatch}")
    print(f"  review_required (informative): {review_required}")
    return 0


def _cmd_regenerate(surface_key: str, method: str, reason: str) -> int:
    """Re-generate one surface with a different method."""
    if not _MANIFEST_PATH.exists():
        print("[FAIL] manifest.json not found. Run normalize first.")
        return 1

    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    found = False
    for entry in manifest:
        if entry["surface_key"] == surface_key:
            found = True
            view = entry["view"]
            theme = entry["theme"]
            src_path = _PROJ / entry["src_file"]

            tgt_w = entry["target_width"]
            tgt_h = entry["target_height"]

            with Image.open(src_path) as img:
                src_w, src_h = img.size

            # Recompute lost/pad for the new method
            if method == "identity":
                lost_top = lost_bottom = pad_pixels = 0
            elif method == "resize_only":
                lost_top = lost_bottom = pad_pixels = 0
            elif method == "resize+crop_center":
                h_after = int(src_h * (tgt_w / src_w))
                delta = h_after - tgt_h
                lost_top = delta // 2 if delta > 0 else 0
                lost_bottom = delta - lost_top if delta > 0 else 0
                pad_pixels = 0
            elif method == "resize+crop_top":
                h_after = int(src_h * (tgt_w / src_w))
                delta = h_after - tgt_h
                lost_top = delta if delta > 0 else 0
                lost_bottom = 0
                pad_pixels = 0
            elif method == "resize+crop_bottom":
                h_after = int(src_h * (tgt_w / src_w))
                delta = h_after - tgt_h
                lost_top = 0
                lost_bottom = delta if delta > 0 else 0
                pad_pixels = 0
            elif method == "resize+pad_bottom_surface":
                h_after = int(src_h * (tgt_w / src_w))
                delta = h_after - tgt_h
                lost_top = lost_bottom = 0
                pad_pixels = -delta if delta < 0 else 0
            else:
                print(f"[FAIL] Unknown method: {method}")
                return 1

            with Image.open(src_path) as img:
                normalized = _normalize_image(
                    img, method, tgt_w, tgt_h, theme, lost_top, lost_bottom, pad_pixels
                )

            out_path = _NORM_DIR / theme / f"{view}.png"
            normalized.save(out_path)

            entry["method"] = method
            entry["method_params"] = None
            entry["lost_pixels_top"] = lost_top
            entry["lost_pixels_bottom"] = lost_bottom
            entry["pad_pixels"] = pad_pixels
            entry["lost_pct"] = (lost_top + lost_bottom) / (src_h * (tgt_w / src_w)) * 100 if src_h > 0 else 0.0
            entry["pad_pct"] = (pad_pixels / tgt_h * 100) if tgt_h > 0 else 0.0
            entry["review_required"] = entry["lost_pct"] >= 5.0 or pad_pixels >= 50
            entry["review_reason"] = None
            if entry["review_required"]:
                if entry["lost_pct"] >= 5.0:
                    entry["review_reason"] = f"lost_pct={entry['lost_pct']:.1f}% >= 5%"
                elif pad_pixels >= 50:
                    entry["review_reason"] = f"pad_pixels={pad_pixels} >= 50"
            entry["regenerate_reason"] = reason

            print(f"[OK] Regenerated {surface_key} with method={method}")
            break

    if not found:
        print(f"[FAIL] Surface key not found: {surface_key}")
        return 1

    _MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize mockup reference PNGs")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("normalize", help="Generate normalized reference (default)")
    subparsers.add_parser("doctor", help="Validate canonical sizes")
    subparsers.add_parser("audit", help="Audit normalization quality")

    reg = subparsers.add_parser("regenerate", help="Re-generate one surface with different method")
    reg.add_argument("--surface", required=True)
    reg.add_argument("--method", required=True)
    reg.add_argument("--reason", required=True)

    args = parser.parse_args()

    if args.command is None or args.command == "normalize":
        return _cmd_normalize()
    if args.command == "doctor":
        return _cmd_doctor()
    if args.command == "audit":
        return _cmd_audit()
    if args.command == "regenerate":
        return _cmd_regenerate(args.surface, args.method, args.reason)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
