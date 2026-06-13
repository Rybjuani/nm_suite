"""qa/runtime_live_probe.py — BL-00R: reliable read-only runtime evidence probe.

Distinta de `qa/capture_v8.py` (matriz offscreen in-process). Esta sonda LANZA la
ventana de la app en un SUBPROCESO CONTROLADO (PID real, ciclo de vida real),
opcionalmente sobre una superficie de window-manager REAL (`--mode onscreen`) para
exponer defectos de runtime que un grab offscreen in-process NO puede ver:
ventanas top-level fantasma, ventanas que no cierran, procesos huérfanos y
(onscreen) flicker real del WM.

NO reemplaza a `capture_v8.py`. Sirve para destrabar BL-04 (runtime real).

SEGURO / READ-ONLY:
  - Corre bajo NM_VISUAL_QA=1 (datos demo, sb=None): sin Supabase, sin DB real,
    sin auth, sin onboarding/privacy gate, sin escribir .env en AppData, sin sync.
  - Nunca limpia AppData. Nunca toca .env / installers / build / qa/e2e /
    qa/capture_v8.py / qa/_captures_v8.
  - Cierra SOLO los subprocesos que ella lanzó. Nunca mata procesos preexistentes.
  - NO aprueba calidad visual (AGENTS.md §10.0).

USO (parent):
    .venv\\Scripts\\python.exe qa\\runtime_live_probe.py --all
    .venv\\Scripts\\python.exe qa\\runtime_live_probe.py --app hub --view dashboard --theme both
    .venv\\Scripts\\python.exe qa\\runtime_live_probe.py --all --mode onscreen   # intrusivo, BL-04
    .venv\\Scripts\\python.exe qa\\runtime_live_probe.py --list

SALIDA: qa/_runtime_probe/{app}-{view}-{theme}-960x600.png + PROBE_MANIFEST.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

_DEFAULT_OUT = _PROJ / "qa" / "_runtime_probe"
# Contrato base 960x600; override por env para pasadas responsive (los hijos
# heredan el entorno del parent, así un solo export cubre toda la corrida).
_RES = os.environ.get("NM_PROBE_RES", "960x600")
_THEME_MAP = {"light": "light_hybrid", "dark": "dark_hybrid"}

# Vistas runtime-críticas (la matriz exhaustiva es trabajo de capture_v8.py).
# Hub post-reestructura v1.0: nav canónica de 4 lugares (Inicio/Pacientes/
# Personalización global/Ajustes) + detalle con tabs Plan terapéutico e IA
# (las ex-vistas top-level presets/textos/ia ya no existen).
_VIEWS = {
    "suite": ["home", "animo", "respiracion", "timer", "avisos",
              "registro", "rutina", "actividades", "evolucion"],
    "hub": ["dashboard", "pacientes", "detalle", "detalle_plan", "detalle_ia",
            "personalizacion", "config"],
}
_SPEC = {
    "suite": ("app.main_qt", "NeuroMoodApp", "Suite"),
    "hub": ("hub.main_qt", "NeuroMoodHub", "Hub"),
}

_CHILD_TIMEOUT = 90  # s por subproceso; si excede => no cerró / colgado


# ═══════════════════════════════════════════════════════════════════════════
# CHILD: corre dentro de un subproceso, lanza la ventana real, captura, cierra
# ═══════════════════════════════════════════════════════════════════════════

def _run_child(app_key: str, view: str, modo: str, mode: str, out_dir: Path) -> int:
    # Plataforma: offscreen (seguro, headless) u onscreen (WM real, intrusivo).
    if mode == "onscreen":
        os.environ.pop("QT_QPA_PLATFORM", None)
    else:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["NM_VISUAL_QA"] = "1"  # demo, sb=None: sin auth/sync/Supabase/AppData

    sidecar = out_dir / f"{app_key}-{view}-{_short(modo)}.sidecar.json"
    result: dict = {"app": app_key, "view": view, "theme": _short(modo),
                    "mode": mode, "ok": False, "reasons": []}
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QSettings, QSize
        from shared.fonts import load_fonts
        from shared.theme_qt import stylesheet_base
        import importlib

        qapp = QApplication.instance() or QApplication(sys.argv)
        load_fonts()
        qapp.setStyleSheet(stylesheet_base(modo))

        module_name, class_name, settings_name = _SPEC[app_key]
        QSettings("NeuroMood", settings_name).setValue("ui/theme", modo)
        WindowClass = getattr(importlib.import_module(module_name), class_name)

        w, h = (int(x) for x in _RES.split("x"))
        win = WindowClass()
        win.show()
        _drain(qapp, 10)
        try:
            win.setMinimumSize(QSize(0, 0))
            win.setMaximumSize(QSize(16777215, 16777215))
            win.setFixedSize(QSize(w, h))
            lay = win.layout()
            if lay:
                lay.activate()
        except Exception:
            pass
        _drain(qapp, 6)

        # Navegación real
        navd = _navigate(win, app_key, view, qapp)
        _drain(qapp, 8)
        result["navigated"] = navd

        # Firma de vista (landmark) + enumeración top-level (fantasma)
        result["current_signature"] = _view_signature(win, app_key)
        result["toplevels_visible"] = _toplevel_titles(qapp, win)

        # Captura de la ventana real
        if not win.isVisible():
            win.show()
        _drain(qapp, 4)
        pm = win.grab()
        out_path = out_dir / f"{app_key}-{view}-{_short(modo)}-{w}x{h}.png"
        ok = pm.save(str(out_path))
        result["png"] = out_path.name if ok else None
        result["actual_w"], result["actual_h"] = pm.width(), pm.height()
        if not ok:
            result["reasons"].append("grab_save_failed")
        if (pm.width(), pm.height()) != (w, h):
            result["reasons"].append(f"size_mismatch_{pm.width()}x{pm.height()}")

        # Lifecycle: cerrar y verificar que NO queden top-levels visibles de la app
        win.close()
        win.deleteLater()
        _drain(qapp, 8)
        residual = _toplevel_titles(qapp, None)
        result["toplevels_after_close"] = residual
        if residual:
            result["reasons"].append(f"did_not_close_clean({len(residual)})")

        result["ok"] = not result["reasons"]
    except Exception as exc:  # noqa: BLE001
        import traceback
        result["reasons"].append(f"exception:{exc.__class__.__name__}:{str(exc)[:80]}")
        result["traceback"] = traceback.format_exc()[:1500]

    sidecar.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 2


def _navigate(win, app_key: str, view: str, qapp) -> bool:
    try:
        if app_key == "suite":
            if view == "home":
                if hasattr(win, "_go_home"):
                    win._go_home()
            elif hasattr(win, "_open_module"):
                win._open_module(view)
            _drain(qapp, 4)
            return True
        # hub
        if view.startswith("detalle"):
            if hasattr(win, "_on_nav"):
                win._on_nav("pacientes")
            _drain(qapp, 4)
            pacientes = list(getattr(win, "_pacientes", None) or [])
            if not pacientes:
                try:
                    from shared.visual_qa import hub_patients
                    pacientes = hub_patients()
                except Exception:
                    pacientes = []
            if pacientes and hasattr(win, "_select_patient"):
                p = pacientes[0]
                win._select_patient(p.get("patient_id", ""), p.get("patient_name", ""))
            # Sub-vistas del detalle: Plan terapéutico (tab 2) e IA (tab 3).
            if view in ("detalle_plan", "detalle_ia"):
                _drain(qapp, 4)
                stack = getattr(win, "_stack", None)
                det = stack.currentWidget() if stack is not None else None
                tabs = getattr(det, "_tabs", None)
                if tabs is not None:
                    tabs.setCurrentIndex(2 if view == "detalle_plan" else 3)
            return True
        if hasattr(win, "_on_nav"):
            win._on_nav(view)
        _drain(qapp, 4)
        return True
    except Exception:
        return False


def _view_signature(win, app_key: str) -> str:
    try:
        if app_key == "suite":
            cm = getattr(win, "_current_module", None)
            return "home" if cm is None else type(cm).__name__
        stack = getattr(win, "_stack", None)
        if stack is not None and hasattr(stack, "currentWidget"):
            cw = stack.currentWidget()
            return type(cw).__name__ if cw is not None else "<none>"
    except Exception:
        pass
    return "<unknown>"


def _toplevel_titles(qapp, exclude) -> list[str]:
    from PyQt6.QtWidgets import QApplication
    out = []
    for tl in QApplication.topLevelWidgets():
        if tl is exclude or not tl.isVisible():
            continue
        out.append(f"{type(tl).__name__}:{(tl.windowTitle() or '')[:30]}")
    return out


# ═══════════════════════════════════════════════════════════════════════════
# PARENT: orquesta subprocesos, controla PIDs, arma manifest
# ═══════════════════════════════════════════════════════════════════════════

def _probe_one(app_key: str, view: str, modo: str, mode: str, out_dir: Path) -> dict:
    rec: dict = {"app": app_key, "view": view, "theme": _short(modo),
                 "mode": mode, "resolution": _RES}
    sidecar = out_dir / f"{app_key}-{view}-{_short(modo)}.sidecar.json"
    if sidecar.exists():
        sidecar.unlink()

    cmd = [sys.executable, str(Path(__file__).resolve()), "--_child",
           "--app", app_key, "--view", view, "--theme", _short(modo),
           "--mode", mode, "--out-dir", str(out_dir)]
    rec["command"] = " ".join(cmd)
    t0 = time.time()
    try:
        proc = subprocess.Popen(cmd, cwd=str(_PROJ))
        rec["pid"] = proc.pid
        try:
            exit_code = proc.wait(timeout=_CHILD_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()  # mata SOLO el subproceso que lanzamos
            proc.wait(timeout=10)
            rec["exit_code"] = None
            rec["duration_s"] = round(time.time() - t0, 1)
            rec["result"] = "DEFECTS_FOUND"
            rec["reasons"] = ["hang_no_exit_within_timeout (ventana no cerró / proceso colgado)"]
            return rec
        rec["exit_code"] = exit_code
    except Exception as exc:  # noqa: BLE001
        rec["result"] = "FAILED"
        rec["reasons"] = [f"spawn_error:{exc.__class__.__name__}:{str(exc)[:80]}"]
        rec["duration_s"] = round(time.time() - t0, 1)
        return rec
    rec["duration_s"] = round(time.time() - t0, 1)

    # Leer sidecar del child
    if not sidecar.exists():
        rec["result"] = "FAILED"
        rec["reasons"] = ["no_sidecar (child no reportó)"]
        return rec
    child = json.loads(sidecar.read_text(encoding="utf-8"))
    rec["current_signature"] = child.get("current_signature")
    rec["toplevels_visible"] = child.get("toplevels_visible")
    rec["toplevels_after_close"] = child.get("toplevels_after_close")
    rec["actual_resolution"] = f"{child.get('actual_w')}x{child.get('actual_h')}"
    rec["navigated"] = child.get("navigated")
    reasons = list(child.get("reasons", []))

    # Hash de la imagen (para detección de duplicados sospechosos en el parent)
    png = child.get("png")
    if png:
        p = out_dir / png
        if p.exists():
            rec["png"] = png
            rec["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        else:
            reasons.append("png_missing_on_disk")
    else:
        reasons.append("no_png")

    rec["reasons"] = reasons
    rec["result"] = "DEFECTS_FOUND" if reasons else "OK"
    return rec


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_PROJ),
            text=True, timeout=10).strip()
    except Exception:
        return "<unknown>"


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _short(modo: str) -> str:
    return "light" if "light" in modo else "dark"


def _drain(app, cycles: int = 8, pause: float = 0.04) -> None:
    for _ in range(cycles):
        app.processEvents()
        time.sleep(pause)
        app.processEvents()


def _targets(args) -> list[tuple[str, str]]:
    out = []
    if args.all:
        # --all rinde ambas apps; --app X --all restringe a esa app (p.ej. solo Suite).
        apps = (args.app,) if args.app else ("suite", "hub")
        for ak in apps:
            for v in _VIEWS[ak]:
                out.append((ak, v))
    elif args.view:
        ak = args.app or "suite"
        out.append((ak, args.view))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="BL-00R runtime live probe (read-only)")
    p.add_argument("--app", choices=["suite", "hub"])
    p.add_argument("--view", default="")
    p.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    p.add_argument("--mode", choices=["offscreen", "onscreen"], default="offscreen")
    p.add_argument("--all", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    # internas (subproceso child)
    p.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.list:
        for ak in ("suite", "hub"):
            print(f"{ak}: {', '.join(_VIEWS[ak])}")
        return 0

    # Modo child
    if args._child:
        modo = _THEME_MAP[args.theme] if args.theme in _THEME_MAP else "dark_hybrid"
        return _run_child(args.app, args.view, modo, args.mode, out_dir)

    # Modo parent
    targets = _targets(args)
    if not targets:
        p.print_help()
        return 1
    themes = ["light_hybrid", "dark_hybrid"] if args.theme == "both" else [_THEME_MAP[args.theme]]

    print("=" * 60)
    print("BL-00R RUNTIME LIVE PROBE (read-only)")
    print(f"mode={args.mode} | targets={len(targets)} | themes={len(themes)} | out={out_dir}")
    print("=" * 60)

    results: list[dict] = []
    for ak, view in targets:
        for modo in themes:
            print(f"  [{ak}/{view}/{_short(modo)}] ", end="", flush=True)
            rec = _probe_one(ak, view, modo, args.mode, out_dir)
            results.append(rec)
            tail = "" if rec["result"] == "OK" else f" :: {rec.get('reasons')}"
            print(f"{rec['result']} pid={rec.get('pid')} {rec.get('duration_s')}s{tail}")

    # Detección de hashes duplicados entre vistas distintas
    seen: dict[str, str] = {}
    for r in results:
        h = r.get("sha256")
        if not h:
            continue
        key = f"{r['app']}-{r['view']}-{r['theme']}"
        if h in seen and seen[h] != key:
            r.setdefault("reasons", []).append(f"duplicate_hash_with:{seen[h]}")
            if r["result"] == "OK":
                r["result"] = "DEFECTS_FOUND"
        else:
            seen.setdefault(h, key)

    n_ok = sum(1 for r in results if r["result"] == "OK")
    n_def = sum(1 for r in results if r["result"] == "DEFECTS_FOUND")
    n_fail = sum(1 for r in results if r["result"] == "FAILED")

    manifest = {
        "tool": "qa/runtime_live_probe.py",
        "purpose": "BL-00R runtime evidence (read-only). NO aprueba calidad visual.",
        "commit_head": _git_head(),
        "generated_at": datetime.datetime.now().isoformat(),
        "mode": args.mode,
        "resolution": _RES,
        "themes": [_short(t) for t in themes],
        "nm_visual_qa": "1 (demo, sb=None: sin Supabase/DB/auth/AppData/sync)",
        "summary": {"ok": n_ok, "defects": n_def, "failed": n_fail, "total": len(results)},
        "results": results,
        "limitations": [
            "Datos demo (NM_VISUAL_QA=1): no valida datos reales ni sync.",
            "mode=offscreen no observa flicker real del window-manager; usar --mode onscreen para eso.",
            "No aprueba calidad visual: requiere inspección semántica capture-by-capture.",
        ],
    }
    (out_dir / "PROBE_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"OK={n_ok}  DEFECTS_FOUND={n_def}  FAILED={n_fail}  TOTAL={len(results)}")
    print(f"Manifest: {out_dir / 'PROBE_MANIFEST.json'}")
    # Resultado de gobernanza permitido por el anti-checklist (NO PASS/APPROVED)
    if n_fail or n_def:
        print("Runtime tooling: DEFECTS_FOUND")
    else:
        print("Runtime tooling: READY_FOR_TARGETED_PROBES")
    print("Semantic visual review: NOT_RUN")
    print("Visual review outcome: REVIEW_INCOMPLETE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
