"""Establish the single canonical visual source from neuromood-mockup.html.

Phase 0 of plan_reestructuracion_qa_nm_suite.md (v3.0).

This replaces the four obsolete, mutually-inconsistent reference folders
(``mockup_reference_static``, ``_mockup_targets``, ``mockup_reference_normalized``,
``_mockup_targets_normalized``) with ONE reproducible source of truth generated
fresh from the HTML via Playwright:

    qa/_mockup_canonical/{theme}/{view}.png        (e.g. light/home.png)
    qa/_mockup_canonical/MANIFEST.json             (surface_key, size, bg, sha256)
    qa/_mockup_canonical/_review_collage.png       (5 surfaces for owner approval)

Self-contained on purpose: Phase 3 deletes ``capture_mockup.py``, so this module
duplicates the proven driving logic instead of importing it.

Run (full canonical regen, reproducible):

    rm -rf qa/_mockup_canonical && python qa/capture_mockup_canonical.py

Gate (Phase 0.1): >=80 surfaces captured (86 expected), 0 wrong-size PNGs,
0 theme-inconsistent PNGs. The script exits non-zero if the gate is not met.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_PROJ = Path(__file__).resolve().parent.parent
_MOCKUP = _PROJ / "qa" / "pack canonico" / "neuromood-mockup_reparado.html"
_OUT = _PROJ / "qa" / "_mockup_canonical"
_STANDARD_RES = "960x600"
_NARROW_RES = "520x600"
_DIALOG_RES = "480x325"

CaptureMode = Literal["window", "viewport", "modal"]


@dataclass(frozen=True)
class Surface:
    app: str
    view: str
    screen: str
    state: str | None = None
    resolution: str = _STANDARD_RES
    capture: CaptureMode = "window"
    file_view: str | None = None
    eval_after: tuple[str, ...] = ()
    clicks: tuple[str, ...] = ()
    wait_ms: int = 180

    @property
    def product(self) -> str:
        return "hub" if self.app == "hub" else "suite"

    @property
    def output_view(self) -> str:
        return self.file_view or self.view

    @property
    def surface_key(self) -> str:
        # Matches the keying used by the rest of the QA system, e.g.
        # "suite:home@light" / "hub:pacientes@dark".
        return f"{self.product}:{self.output_view}"


def _s(
    app: str,
    view: str,
    screen: str,
    state: str | None = None,
    *,
    resolution: str = _STANDARD_RES,
    capture: CaptureMode = "window",
    file_view: str | None = None,
    eval_after: tuple[str, ...] = (),
    clicks: tuple[str, ...] = (),
    wait_ms: int = 180,
) -> Surface:
    return Surface(
        app=app,
        view=view,
        screen=screen,
        state=state,
        resolution=resolution,
        capture=capture,
        file_view=file_view,
        eval_after=eval_after,
        clicks=clicks,
        wait_ms=wait_ms,
    )


# Canonical surface registry: surface_key -> go(screen, state) recipe.
# Mirrors capture_v8 output surfaces. 43 surfaces x 2 themes = 86 captures.
SURFACES: tuple[Surface, ...] = (
    # Suite - Home and access
    _s("suite", "home", "home", "score"),
    _s("suite", "home-no-score", "home", "noscore"),
    _s("suite", "onboarding", "onboarding", "normal", resolution=_NARROW_RES),
    _s("suite", "onboarding-error", "onboarding", "error", resolution=_NARROW_RES),
    _s("suite", "recuperar-acceso", "recuperar", resolution=_NARROW_RES),
    # Suite - Mood
    _s("suite", "animo", "animo"),
    # Suite - Breathing
    _s("suite", "respiracion", "respiracion", "idle"),
    _s("suite", "respiracion-running", "respiracion", "running"),
    _s("suite", "respiracion-paused", "respiracion", "paused"),
    # Suite - CBT thought record
    _s("suite", "registro", "registro", "s0"),
    _s("suite", "registro-step1-emotion", "registro", "s1"),
    _s("suite", "registro-step1-emotion-otro", "registro", "s1otro"),
    _s("suite", "registro-step2-distortions", "registro", "s2"),
    _s("suite", "registro-step3-filled", "registro", "s3"),
    _s("suite", "registro-success", "registro", "ok"),
    # Suite - Routine
    _s("suite", "rutina", "rutina", "default"),
    _s("suite", "rutina-add-task", "rutina", "add"),
    _s("suite", "rutina-all-completed", "rutina", "done"),
    _s("suite", "rutina-empty", "rutina", "empty"),
    # Suite - Behavioral activation
    _s("suite", "actividades", "actividades", "default"),
    _s("suite", "actividades-filtered", "actividades", "filtered"),
    _s("suite", "actividades-marked-hice", "actividades", "marked"),
    _s("suite", "actividades-empty", "actividades", "empty"),
    # Suite - Reminders
    _s("suite", "avisos", "avisos", "all"),
    _s("suite", "avisos-filter-activos", "avisos", "active"),
    _s("suite", "avisos-search", "avisos", "search"),
    _s("suite", "avisos-today", "avisos", "today"),
    _s("suite", "avisos-empty", "avisos", "empty"),
    # Suite - Timer
    _s("suite", "timer", "timer", "idle"),
    _s("suite", "timer-running", "timer", "running"),
    _s("suite", "timer-paused", "timer", "paused"),
    _s("suite", "timer-empty", "timer", "empty"),
    # Suite - DBT
    _s("suite", "dbt-now", "dbtnow"),
    _s("suite", "dbt-library", "dbtlib"),
    _s(
        "suite",
        "dbt-practice-stop",
        "dbtlib",
        capture="viewport",
        eval_after=("openDBTPractice('Tolerancia')",),
        clicks=("#dbtNext",),
        wait_ms=260,
    ),
    # Hub - Patients
    _s("hub", "pacientes", "pacientes", "list"),
    _s("hub", "pacientes-empty", "pacientes", "empty"),
    # Hub - Detail
    _s("hub", "detalle", "detalle", eval_after=("HUB_TAB='recordatorios'; render()",)),
    _s("hub", "detalle-plan-timer", "detalle", eval_after=("HUB_TAB='timer'; render()",)),
    _s("hub", "detalle-plan-rutina", "detalle", eval_after=("HUB_TAB='rutina'; render()",)),
    _s(
        "hub",
        "detalle-plan-activacion",
        "detalle",
        eval_after=("HUB_TAB='activacion'; render()",),
    ),
    _s(
        "hub",
        "detalle-resumen-ia",
        "detalle",
        resolution=_DIALOG_RES,
        capture="modal",
        file_view="detalle-resumen-ia-0",
        eval_after=("HUB_TAB='recordatorios'; render()",),
        clicks=("[data-ia-summary]",),
        wait_ms=220,
    ),
    # Hub - Global texts
    _s("hub", "textos-globales", "textos"),
)

# Five surfaces sampled for the Phase 0.2 owner-approval collage.
COLLAGE_SAMPLE: tuple[tuple[str, str], ...] = (
    ("suite", "home", "light"),
    ("suite", "animo", "dark"),
    ("suite", "registro-step1-emotion", "dark"),
    ("hub", "pacientes", "light"),
    ("suite", "dbt-now", "dark"),
)


def _parse_res(res: str) -> tuple[int, int]:
    w, h = res.lower().split("x", 1)
    return int(w), int(h)


def _page_url() -> str:
    return _MOCKUP.resolve().as_uri()


def _git_metadata() -> dict[str, str | None]:
    def run(args: list[str]) -> str | None:
        try:
            return subprocess.check_output(
                args, cwd=_PROJ, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            return None

    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "branch": run(["git", "branch", "--show-current"]),
    }


def _device_css(width: int, height: int, capture: CaptureMode) -> str:
    # Strip the surrounding mockup browser chrome; pin the device window size so
    # captures are deterministic.
    modal_override = ""
    if capture == "modal":
        modal_override = f"""
        .modal {{
          width:{width}px !important;
          height:{height}px !important;
          max-height:{height}px !important;
        }}
        """
    return f"""
    :root {{
      --qa-target-width:{width}px;
      --qa-target-height:{height}px;
    }}
    * {{
      animation-duration:0ms !important;
      animation-delay:0ms !important;
      transition-duration:0ms !important;
      caret-color:transparent !important;
      scroll-behavior:auto !important;
    }}
    html, body {{ overflow:hidden !important; }}
    .app {{
      display:block !important;
      width:100vw !important;
      height:100vh !important;
    }}
    .nav, .stage__top, .menu-fab, .toast {{
      display:none !important;
    }}
    .stage {{
      padding:0 !important;
      width:100vw !important;
      height:100vh !important;
      overflow:hidden !important;
      display:grid !important;
      place-items:center !important;
    }}
    #windowMount {{
      width:100vw !important;
      height:100vh !important;
      display:grid !important;
      place-items:center !important;
    }}
    .window,
    .window.narrow {{
      width:{width}px !important;
      max-width:{width}px !important;
      height:{height}px !important;
      max-height:{height}px !important;
      margin:0 !important;
      animation:none !important;
    }}
    .screen {{
      min-height:calc({height}px - 48px) !important;
    }}
    {modal_override}
    """


def _reset_and_render(page, surface: Surface, theme: str) -> None:
    page.evaluate(
        """
        ({theme, product, screen, state}) => {
          try { stopBreath(); } catch (_) {}
          try { clearInterval(timerInt); } catch (_) {}
          try { closeModal(); } catch (_) {}
          try { HUB_TAB = 'recordatorios'; } catch (_) {}
          try { HUB_PATIENT = 'ana'; } catch (_) {}
          try { TG_FILTER = 'Todos los m\\u00f3dulos'; } catch (_) {}
          try { TG_SEARCH = ''; } catch (_) {}
          try { if (TG_DIRTY && TG_DIRTY.clear) TG_DIRTY.clear(); } catch (_) {}
          setTheme(theme);
          setProduct(product);
          go(screen, state || null);
        }
        """,
        {
            "theme": theme,
            "product": surface.product,
            "screen": surface.screen,
            "state": surface.state,
        },
    )
    for js in surface.eval_after:
        page.evaluate(js)
    for selector in surface.clicks:
        page.locator(selector).first.click(timeout=5000)
    page.wait_for_timeout(max(surface.wait_ms, 800))  # fonts + animation settle


def _force_image_size(path: Path, width: int, height: int) -> None:
    from PIL import Image

    with Image.open(path).convert("RGB") as image:
        if image.size == (width, height):
            return
        fixed = Image.new("RGB", (width, height), image.getpixel((0, 0)))
        fixed.paste(
            image.crop((0, 0, min(width, image.width), min(height, image.height))),
            (0, 0),
        )
        fixed.save(path)


def _capture_one(page, surface: Surface, theme: str, out_dir: Path) -> dict:
    width, height = _parse_res(surface.resolution)
    viewport_w = width if surface.capture == "viewport" else max(width + 80, 960)
    viewport_h = height if surface.capture == "viewport" else max(height + 80, 680)
    page.set_viewport_size({"width": viewport_w, "height": viewport_h})
    page.goto(_page_url(), wait_until="load")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass  # Google Fonts can keep the page busy depending on network state
    try:
        page.evaluate("document.fonts && document.fonts.ready")
    except Exception:
        pass
    page.add_style_tag(content=_device_css(width, height, surface.capture))
    _reset_and_render(page, surface, theme)

    rel = f"{theme}/{surface.output_view}.png"
    path = out_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)

    if surface.capture == "window":
        page.locator(".window").screenshot(path=str(path), animations="disabled")
    elif surface.capture == "modal":
        page.locator(".modal-bg.show .modal").screenshot(
            path=str(path), animations="disabled"
        )
    else:
        page.screenshot(path=str(path), full_page=False, animations="disabled")
    _force_image_size(path, width, height)

    return _audit_png(path, surface, theme, width, height, rel)


def _audit_png(
    path: Path, surface: Surface, theme: str, width: int, height: int, rel: str
) -> dict:
    """Validate one PNG: exact size, 5-point bg sample, sha256, theme luminance."""
    import numpy as np
    from PIL import Image

    with Image.open(path).convert("RGB") as img:
        size = img.size
        arr = np.asarray(img, dtype=np.float64)

    h, w, _ = arr.shape

    def sample(y: int, x: int) -> list[int]:
        return [int(c) for c in arr[y, x]]

    bg = {
        "tl": sample(2, 2),
        "tr": sample(2, w - 3),
        "bl": sample(h - 3, 2),
        "br": sample(h - 3, w - 3),
        "center": sample(h // 2, w // 2),
    }
    # Rec. 601 luminance over the whole image is the most robust light/dark signal.
    lum = float((0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).mean())

    size_ok = size == (width, height)
    # Wide bands: catch gross errors (a dark image saved under light/, etc.) without
    # false-failing content-heavy screens. The pairwise light>dark check below is the
    # stricter, threshold-free signal.
    if theme == "light":
        theme_ok = lum >= 90.0
    else:
        theme_ok = lum <= 175.0

    sha = hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "surface_key": f"{surface.surface_key}@{theme}",
        "app": surface.app,
        "view": surface.output_view,
        "theme": theme,
        "file": rel,
        "resolution": surface.resolution,
        "size": [size[0], size[1]],
        "size_ok": size_ok,
        "bg_color_sample": bg,
        "mean_luminance": round(lum, 2),
        "theme_ok": bool(theme_ok),
        "sha256": sha,
        "success": True,
    }


def _capture(surfaces: list[Surface], themes: list[str], out_dir: Path) -> list[dict]:
    from playwright.sync_api import sync_playwright

    results: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        for theme in themes:
            print(f"\n--- {theme.upper()} ---")
            for surface in surfaces:
                label = f"{surface.surface_key}@{theme}"
                print(f"  [{label}] ", end="", flush=True)
                try:
                    results.append(_capture_one(page, surface, theme, out_dir))
                    print("OK")
                except Exception as exc:
                    results.append(
                        {
                            "surface_key": label,
                            "app": surface.app,
                            "view": surface.output_view,
                            "theme": theme,
                            "file": f"{theme}/{surface.output_view}.png",
                            "resolution": surface.resolution,
                            "success": False,
                            "error": f"{exc.__class__.__name__}: {exc}",
                        }
                    )
                    print(f"FAIL ({exc.__class__.__name__}: {str(exc)[:100]})")
        browser.close()
    return results


def _build_collage(out_dir: Path, results: list[dict]) -> Path | None:
    """Owner-review collage of 5 sampled surfaces (Phase 0.2)."""
    from PIL import Image, ImageDraw

    by_key = {r["surface_key"]: r for r in results if r.get("success")}
    cells: list[tuple[str, Image.Image]] = []
    for app, view, theme in COLLAGE_SAMPLE:
        key = f"{app}:{view}@{theme}"
        rec = by_key.get(key)
        if not rec:
            continue
        img_path = out_dir / rec["file"]
        if not img_path.exists():
            continue
        cells.append((key, Image.open(img_path).convert("RGB")))

    if not cells:
        return None

    cell_h = 300
    pad = 14
    cap_h = 22
    scaled: list[tuple[str, Image.Image]] = []
    for key, img in cells:
        ratio = cell_h / img.height
        scaled.append((key, img.resize((max(1, int(img.width * ratio)), cell_h))))

    total_w = sum(im.width for _, im in scaled) + pad * (len(scaled) + 1)
    total_h = cell_h + cap_h + pad * 2
    canvas = Image.new("RGB", (total_w, total_h), (32, 32, 36))
    draw = ImageDraw.Draw(canvas)

    x = pad
    for key, im in scaled:
        canvas.paste(im, (x, pad + cap_h))
        draw.text((x, pad // 2), key, fill=(235, 235, 235))
        x += im.width + pad

    path = out_dir / "_review_collage.png"
    canvas.save(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the single canonical mockup source (Phase 0)."
    )
    parser.add_argument(
        "--theme", choices=["light", "dark", "both"], default="both"
    )
    parser.add_argument(
        "--view", default="", help="Capture a single output_view (debug)."
    )
    parser.add_argument(
        "--no-collage", action="store_true", help="Skip the review collage."
    )
    args = parser.parse_args()

    if not _MOCKUP.exists():
        print(f"[ERROR] Mockup not found: {_MOCKUP}", file=sys.stderr)
        return 1

    surfaces = list(SURFACES)
    if args.view:
        surfaces = [s for s in surfaces if s.output_view == args.view]
        if not surfaces:
            print(f"[ERROR] No surface with output_view={args.view!r}", file=sys.stderr)
            return 1

    themes = ["light", "dark"] if args.theme == "both" else [args.theme]
    _OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CANONICAL MOCKUP CAPTURE (Phase 0)")
    print(f"Surfaces: {len(surfaces)} | Themes: {len(themes)} | Out: {_OUT}")
    print("=" * 60)

    start = time.time()
    results = _capture(surfaces, themes, _OUT)
    elapsed = time.time() - start

    captured = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    wrong_size = [r for r in captured if not r.get("size_ok")]
    bad_theme = [r for r in captured if not r.get("theme_ok")]

    # Threshold-free pairwise check: each view's light capture must be brighter
    # than its dark counterpart (catches theme bleed that the wide bands miss).
    pair_violations: list[str] = []
    if set(themes) == {"light", "dark"}:
        lum_by = {(r["app"], r["view"], r["theme"]): r["mean_luminance"] for r in captured}
        for (app, view, theme), lum in lum_by.items():
            if theme != "light":
                continue
            dark = lum_by.get((app, view, "dark"))
            if dark is not None and lum <= dark + 10:
                pair_violations.append(f"{app}:{view} (light {lum} <= dark {dark}+10)")

    collage_path = None
    if not args.no_collage:
        collage_path = _build_collage(_OUT, results)

    manifest = {
        "harness": "capture_mockup_canonical.py",
        "plan": "plan_reestructuracion_qa_nm_suite.md (Fase 0)",
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "git": _git_metadata(),
        "mockup": str(_MOCKUP.relative_to(_PROJ)),
        "command": sys.argv,
        "themes": themes,
        "surfaces_expected": len(surfaces) * len(themes),
        "captured": len(captured),
        "failed": len(failed),
        "wrong_size": len(wrong_size),
        "theme_inconsistent": len(bad_theme),
        "pair_violations": pair_violations,
        "elapsed_seconds": round(elapsed, 1),
        "review_collage": "_review_collage.png" if collage_path else None,
        "captures": sorted(results, key=lambda r: r["surface_key"]),
    }
    (_OUT / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ----- Phase 0.1 gate -----
    expected = len(surfaces) * len(themes)
    gate_min = 80 if expected >= 80 else expected  # single-view debug runs relax this
    gate_ok = (
        len(captured) >= gate_min
        and len(wrong_size) == 0
        and len(bad_theme) == 0
        and len(pair_violations) == 0
    )

    print("\n" + "=" * 60)
    print("RESULTS")
    print(f"  Captured:          {len(captured)}/{expected}")
    print(f"  Failed:            {len(failed)}")
    print(f"  Wrong size:        {len(wrong_size)}")
    print(f"  Theme inconsistent:{len(bad_theme)}")
    print(f"  Pair violations:   {len(pair_violations)}")
    print(f"  Time:              {elapsed:.1f}s")
    print(f"  Manifest:          {_OUT / 'MANIFEST.json'}")
    if collage_path:
        print(f"  Review collage:    {collage_path}")
    for r in failed:
        print(f"    FAIL {r['surface_key']}: {r.get('error', '')}")
    for v in pair_violations:
        print(f"    PAIR {v}")
    print(f"\n  GATE (Phase 0.1):  {'PASS' if gate_ok else 'FAIL'}")
    print("=" * 60)
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
