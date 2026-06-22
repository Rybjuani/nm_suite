"""Capture canonical screenshots from neuromood-mockup.html.

The mockup is the visual source of truth for the migration. This tool drives it
with Playwright, captures only the device window (not the web navigation shell),
and writes targets named like capture_v8.py outputs:

    suite-home-light-960x600.png
    hub-detalle-resumen-ia-0-dark-480x325.png
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


_PROJ = Path(__file__).resolve().parent.parent
_MOCKUP = _PROJ / "neuromood-mockup.html"
_DEFAULT_OUT = _PROJ / "qa" / "_mockup_targets"
_STANDARD_RES = "960x600"
_NARROW_RES = "520x600"
_DIALOG_RES = "480x325"

CaptureMode = Literal["window", "viewport", "modal"]


@dataclass(frozen=True)
class MockupTarget:
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


def _t(
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
) -> MockupTarget:
    return MockupTarget(
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


MOCKUP_TARGETS: tuple[MockupTarget, ...] = (
    # Suite - Home and access
    _t("suite", "home", "home", "score"),
    _t("suite", "home-no-score", "home", "noscore"),
    _t("suite", "onboarding", "onboarding", "normal", resolution=_NARROW_RES),
    _t("suite", "onboarding-error", "onboarding", "error", resolution=_NARROW_RES),
    _t("suite", "recuperar-acceso", "recuperar", resolution=_NARROW_RES),
    # Suite - Mood
    _t("suite", "animo", "animo"),
    # Suite - Breathing
    _t("suite", "respiracion", "respiracion", "idle"),
    _t(
        "suite",
        "respiracion-preset-3min",
        "respiracion",
        "idle",
        clicks=("#brPreset [data-m='3']",),
    ),
    _t(
        "suite",
        "respiracion-preset-10min",
        "respiracion",
        "idle",
        clicks=("#brPreset [data-m='10']",),
    ),
    _t("suite", "respiracion-running", "respiracion", "running"),
    _t("suite", "respiracion-paused", "respiracion", "paused"),
    # Suite - CBT thought record
    _t("suite", "registro", "registro", "s0"),
    _t("suite", "registro-step1-emotion", "registro", "s1"),
    _t("suite", "registro-step1-emotion-otro", "registro", "s1otro"),
    _t("suite", "registro-step2-distortions", "registro", "s2"),
    _t("suite", "registro-step3-filled", "registro", "s3"),
    _t("suite", "registro-success", "registro", "ok"),
    # Suite - Routine
    _t("suite", "rutina", "rutina", "default"),
    _t("suite", "rutina-add-task", "rutina", "add"),
    _t("suite", "rutina-all-completed", "rutina", "done"),
    _t("suite", "rutina-empty", "rutina", "empty"),
    # Suite - Behavioral activation
    _t("suite", "actividades", "actividades", "default"),
    _t("suite", "actividades-filtered", "actividades", "filtered"),
    _t("suite", "actividades-marked-hice", "actividades", "marked"),
    _t("suite", "actividades-empty", "actividades", "empty"),
    # Suite - Reminders
    _t("suite", "avisos", "avisos", "all"),
    _t("suite", "avisos-filter-activos", "avisos", "active"),
    _t("suite", "avisos-search", "avisos", "search"),
    _t("suite", "avisos-empty", "avisos", "empty"),
    _t("suite", "avisos-completed", "avisos", "all", clicks=(".av-do",)),
    # Suite - Timer
    _t("suite", "timer", "timer", "idle"),
    _t("suite", "timer-running", "timer", "running"),
    _t("suite", "timer-paused", "timer", "paused"),
    _t("suite", "timer-empty", "timer", "empty"),
    _t("suite", "timer-preset-5min", "timer", "idle", clicks=("[data-min='5']",)),
    _t("suite", "timer-preset-45min", "timer", "idle", clicks=("[data-min='45']",)),
    # Suite - DBT
    _t("suite", "dbt-now", "dbtnow"),
    _t("suite", "dbt-library", "dbtlib"),
    _t(
        "suite",
        "dbt-practice-stop",
        "dbtlib",
        capture="viewport",
        eval_after=("openDBTPractice('Tolerancia')",),
        clicks=("#dbtNext",),
        wait_ms=260,
    ),
    # dbt-practice-closure removido (C4-05): pantalla eliminada del producto
    # Hub - Patients
    _t("hub", "pacientes", "pacientes", "list"),
    _t("hub", "pacientes-empty", "pacientes", "empty"),
    # Hub - Detail
    _t("hub", "detalle", "detalle", eval_after=("HUB_TAB='recordatorios'; render()",)),
    _t("hub", "detalle-plan-timer", "detalle", eval_after=("HUB_TAB='timer'; render()",)),
    _t("hub", "detalle-plan-rutina", "detalle", eval_after=("HUB_TAB='rutina'; render()",)),
    _t(
        "hub",
        "detalle-plan-activacion",
        "detalle",
        eval_after=("HUB_TAB='activacion'; render()",),
    ),
    _t(
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
    _t("hub", "textos-globales", "textos"),
)


def _parse_res(res: str) -> tuple[int, int]:
    try:
        w, h = res.lower().split("x", 1)
        width, height = int(w), int(h)
    except Exception as exc:
        raise argparse.ArgumentTypeError(f"Resolution must be WIDTHxHEIGHT, got {res!r}") from exc
    if width < 100 or height < 100:
        raise argparse.ArgumentTypeError(f"Resolution is too small: {res!r}")
    return width, height


def _themes(label: str) -> list[str]:
    return ["light", "dark"] if label == "both" else [label]


def _git_metadata() -> dict[str, str | None]:
    def run(args: list[str]) -> str | None:
        try:
            return subprocess.check_output(args, cwd=_PROJ, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return None

    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "branch": run(["git", "branch", "--show-current"]),
    }


def _clean_output(out_dir: Path) -> int:
    if not out_dir.exists():
        return 0
    count = sum(1 for p in out_dir.rglob("*") if p.is_file())
    if not count:
        return 0
    trash_root = _PROJ / "_scratch_trash"
    timestamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    trash_dir = trash_root / f"mockup_targets_{timestamp}"
    trash_dir.mkdir(parents=True, exist_ok=True)
    for item in out_dir.iterdir():
        shutil.move(str(item), str(trash_dir / item.name))
    print(f"[OUTPUT_ROTATED] {count} old files moved to {trash_dir}")
    return count


def _select_targets(
    *,
    all_targets: bool,
    app: str | None,
    view: str,
) -> list[MockupTarget]:
    targets = list(MOCKUP_TARGETS)
    if app:
        targets = [t for t in targets if t.app == app]
    if all_targets:
        return targets
    if not view:
        return []

    normalized = view
    if app == "suite" and normalized.startswith("suite-"):
        normalized = normalized[6:]
    if app == "hub" and normalized.startswith("hub-"):
        normalized = normalized[4:]

    return [t for t in targets if t.view == normalized or t.output_view == normalized]


def _list_targets() -> None:
    for app in ("suite", "hub"):
        rows = [t for t in MOCKUP_TARGETS if t.app == app]
        print(f"\n=== {app.upper()} ({len(rows)} targets) ===")
        for target in rows:
            state = target.state or "-"
            print(
                f"  {target.view:32s} screen={target.screen:14s} "
                f"state={state:10s} res={target.resolution:8s} capture={target.capture}"
            )
    print(f"\nTOTAL: {len(MOCKUP_TARGETS)} targets x 2 themes = {len(MOCKUP_TARGETS) * 2} captures")


def _page_url() -> str:
    return _MOCKUP.resolve().as_uri()


def _device_css(width: int, height: int, capture: CaptureMode) -> str:
    # Keep screenshots deterministic and remove the surrounding mockup browser UI.
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


def _reset_and_render(page, target: MockupTarget, theme: str) -> None:
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
            "product": target.product,
            "screen": target.screen,
            "state": target.state,
        },
    )
    for js in target.eval_after:
        page.evaluate(js)
    for selector in target.clicks:
        page.locator(selector).first.click(timeout=5000)
    page.wait_for_timeout(target.wait_ms)


def _capture_one(page, target: MockupTarget, theme: str, out_dir: Path) -> dict:
    width, height = _parse_res(target.resolution)
    viewport_w = width if target.capture == "viewport" else max(width + 80, 960)
    viewport_h = height if target.capture == "viewport" else max(height + 80, 680)
    page.set_viewport_size({"width": viewport_w, "height": viewport_h})
    page.goto(_page_url(), wait_until="load")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        # The Google Fonts request can keep the page busy depending on network state.
        pass
    try:
        page.evaluate("document.fonts && document.fonts.ready")
    except Exception:
        pass
    page.add_style_tag(content=_device_css(width, height, target.capture))
    _reset_and_render(page, target, theme)

    name = f"{target.app}-{target.output_view}-{theme}-{target.resolution}.png"
    path = out_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)

    if target.capture == "window":
        page.locator(".window").screenshot(path=str(path), animations="disabled")
    elif target.capture == "modal":
        page.locator(".modal-bg.show .modal").screenshot(path=str(path), animations="disabled")
    else:
        page.screenshot(path=str(path), full_page=False, animations="disabled")
    _force_image_size(path, width, height)

    return {
        "file": str(path.relative_to(_PROJ)),
        "app": target.app,
        "view": target.view,
        "file_view": target.output_view,
        "screen": target.screen,
        "state": target.state,
        "theme": theme,
        "resolution": target.resolution,
        "capture": target.capture,
        "success": True,
    }


def _force_image_size(path: Path, width: int, height: int) -> None:
    from PIL import Image

    with Image.open(path).convert("RGB") as image:
        if image.size == (width, height):
            return
        fixed = Image.new("RGB", (width, height), image.getpixel((0, 0)))
        fixed.paste(image.crop((0, 0, min(width, image.width), min(height, image.height))), (0, 0))
        fixed.save(path)


def _write_matrix(results: list[dict], out_dir: Path) -> dict[str, str]:
    csv_path = out_dir / "MOCKUP_TARGET_MATRIX.csv"
    md_path = out_dir / "MOCKUP_TARGET_MATRIX.md"
    fields = ["app", "view", "file_view", "screen", "state", "theme", "resolution", "capture", "file"]

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key, "") for key in fields})

    lines = [
        "# Mockup target matrix",
        "",
        f"Generated: {_dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "| App | View | Screen | State | Theme | Res | Capture | File |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in results:
        rel = row.get("file", "")
        lines.append(
            "| {app} | {view} | {screen} | {state} | {theme} | {resolution} | {capture} | {file} |".format(
                app=row.get("app", ""),
                view=row.get("file_view") or row.get("view", ""),
                screen=row.get("screen", ""),
                state=row.get("state") or "",
                theme=row.get("theme", ""),
                resolution=row.get("resolution", ""),
                capture=row.get("capture", ""),
                file=rel,
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": str(csv_path), "markdown": str(md_path)}


def capture_targets(targets: list[MockupTarget], themes: list[str], out_dir: Path) -> list[dict]:
    from playwright.sync_api import sync_playwright

    results: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        for theme in themes:
            print(f"\n--- {theme.upper()} ---")
            for target in targets:
                label = f"{target.app}-{target.output_view}-{theme}-{target.resolution}"
                print(f"  [{label}] ", end="", flush=True)
                try:
                    result = _capture_one(page, target, theme, out_dir)
                    results.append(result)
                    print("CAPTURED")
                except Exception as exc:
                    results.append(
                        {
                            **asdict(target),
                            "theme": theme,
                            "file_view": target.output_view,
                            "success": False,
                            "error": f"{exc.__class__.__name__}: {exc}",
                        }
                    )
                    print(f"FAIL ({exc.__class__.__name__}: {str(exc)[:120]})")
        browser.close()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture canonical UI targets from neuromood-mockup.html")
    parser.add_argument("--all", action="store_true", help="Capture every target mapped to capture_v8 recipes")
    parser.add_argument("--app", choices=["suite", "hub"])
    parser.add_argument("--view", default="", help="Capture one view id, with or without app prefix")
    parser.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    parser.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--no-clean", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        _list_targets()
        return 0

    if not _MOCKUP.exists():
        print(f"[ERROR] Mockup not found: {_MOCKUP}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)

    if args.clean and not args.no_clean:
        _clean_output(out_dir)
        if not args.all and not args.view:
            return 0

    targets = _select_targets(all_targets=args.all, app=args.app, view=args.view)
    if not targets:
        parser.print_help()
        print("\n[ERROR] No targets selected. Use --all, or --view plus optional --app.", file=sys.stderr)
        return 1

    if not args.no_clean and not args.clean:
        _clean_output(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    themes = _themes(args.theme)
    print("=" * 60)
    print("MOCKUP CAPTURE")
    print(f"Targets: {len(targets)} | Themes: {len(themes)} | Output: {out_dir}")
    print("=" * 60)
    start = time.time()
    results = capture_targets(targets, themes, out_dir)
    elapsed = time.time() - start
    success = sum(1 for row in results if row.get("success"))
    failed = len(results) - success
    matrix_paths = _write_matrix(results, out_dir)

    manifest = {
        "harness": "capture_mockup.py",
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "git": _git_metadata(),
        "mockup": str(_MOCKUP.relative_to(_PROJ)),
        "command": sys.argv,
        "output_dir": str(out_dir),
        "targets": len(targets),
        "themes": themes,
        "success": success,
        "failed": failed,
        "elapsed_seconds": round(elapsed, 1),
        "matrix_paths": matrix_paths,
        "results": results,
    }
    manifest_path = out_dir / "MOCKUP_TARGET_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 60)
    print("RESULTS")
    print(f"  Saved targets:  {success}")
    print(f"  Failed targets: {failed}")
    print(f"  Time:           {elapsed:.1f}s")
    print(f"  Manifest:       {manifest_path}")
    print(f"  Matrix:         {matrix_paths['markdown']}")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
