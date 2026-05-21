"""Fullscreen visual capture runner for NeuroMood source apps.

Captures Suite, Hub, installers and uninstallers without rebuilding EXEs and
without running install/uninstall workers. Output goes to _qa_output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_BASE = ROOT / "_qa_output" / "fullscreen_capture"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("NM_VISUAL_QA", "1")
os.environ.setdefault("NM_TEST_FORCE_CLOSE", "1")
os.environ.setdefault("NM_VISUAL_QA_NAME", "Ana Martinez")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QWidget


CAPTURES: list[dict] = []


def log(msg: str) -> None:
    print(msg, flush=True)


def drain(app: QApplication, ms: int = 400) -> None:
    end = time.time() + (ms / 1000)
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()


def maximize(win: QWidget, app: QApplication, allow_fixed: bool = False) -> None:
    screen = QApplication.primaryScreen().availableGeometry()
    if allow_fixed:
        win.setMinimumSize(QSize(0, 0))
        win.setMaximumSize(QSize(16777215, 16777215))
    win.showMaximized()
    drain(app, 700)
    if win.width() < int(screen.width() * 0.75) or win.height() < int(screen.height() * 0.75):
        win.resize(screen.width(), screen.height())
        win.move(screen.x(), screen.y())
        drain(app, 400)


def capture(app: QApplication, win: QWidget, out: Path, label: str) -> None:
    drain(app, 500)
    win.repaint()
    drain(app, 200)
    pix = win.grab()
    if pix.isNull():
        raise RuntimeError(f"Null screenshot: {label}")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not pix.save(str(out), "PNG"):
        raise RuntimeError(f"Could not save screenshot: {out}")
    CAPTURES.append({
        "label": label,
        "path": str(out),
        "width": pix.width(),
        "height": pix.height(),
    })
    log(f"CAPTURE {label} {pix.width()}x{pix.height()} -> {out}")


def close_window(app: QApplication, win: QWidget) -> None:
    try:
        win.close()
        win.deleteLater()
    except Exception:
        pass
    drain(app, 500)


def set_app_theme(win, theme: str, app: QApplication) -> None:
    if theme == "light":
        if hasattr(win, "_toggle_theme") and "dark" in getattr(win, "_modo", "dark"):
            win._toggle_theme()
            drain(app, 700)
    elif theme == "dark":
        if hasattr(win, "_toggle_theme") and "light" in getattr(win, "_modo", ""):
            win._toggle_theme()
            drain(app, 700)


def capture_suite(app: QApplication, out_root: Path, themes: tuple[str, ...] = ("dark", "light")) -> None:
    from app.main_qt import NeuroMoodApp

    modules = [
        ("00_home", None),
        ("01_animo", "animo"),
        ("02_respiracion", "respiracion"),
        ("03_registro_tcc", "registro"),
        ("04_rutina", "rutina"),
        ("05_actividades", "actividades"),
        ("06_timer", "timer"),
        ("07_avisos", "avisos"),
    ]
    for theme in themes:
        log(f"== Suite {theme} ==")
        win = NeuroMoodApp()
        maximize(win, app)
        set_app_theme(win, theme, app)
        for slug, module_id in modules:
            if module_id is None:
                win._go_home()
            else:
                win._navigate_to(module_id)
            drain(app, 900)
            capture(app, win, out_root / "suite" / theme / f"{slug}.png", f"suite/{theme}/{slug}")
        close_window(app, win)


def _detail_demo_data() -> dict:
    return {
        "animo": [
            {"fecha": "2026-05-18", "hora": "09:00", "puntaje": 7.2, "nota": "Mejor descanso"},
            {"fecha": "2026-05-17", "hora": "20:30", "puntaje": 6.5, "nota": "Ansiedad baja"},
            {"fecha": "2026-05-16", "hora": "11:15", "puntaje": 8.0, "nota": "Actividad social"},
            {"fecha": "2026-05-15", "hora": "18:45", "puntaje": 5.9, "nota": "Dia demandante"},
        ],
        "resp": [
            {"fecha": "2026-05-18", "hora": "10:10", "tecnica": "4-7-8", "duracion_minutos": 5},
            {"fecha": "2026-05-17", "hora": "22:00", "tecnica": "coherencia", "duracion_minutos": 8},
        ],
        "pens": [
            {"fecha": "2026-05-18", "hora": "12:20", "emocion": "ansiedad", "intensidad": 6, "pensamiento": "No voy a llegar"},
            {"fecha": "2026-05-16", "hora": "19:10", "emocion": "tristeza", "intensidad": 4, "pensamiento": "Necesito pedir ayuda"},
        ],
        "checklist": [
            {"fecha": "2026-05-18", "descripcion": "Caminata 20 min", "categoria": "Fisica", "origen": "manual"},
            {"fecha": "2026-05-17", "descripcion": "Llamar a una amiga", "categoria": "Social", "origen": "hub"},
        ],
        "timer": [
            {"fecha": "2026-05-18", "hora": "15:00", "nombre": "Lectura", "categoria": "Foco", "duracion_real": 25},
        ],
        "reclog": [
            {"fecha": "2026-05-18", "hora": "08:00", "mensaje": "Medicacion", "cerrado": 1},
            {"fecha": "2026-05-18", "hora": "14:00", "mensaje": "Registro de animo", "cerrado": 0},
        ],
    }


def _prepare_hub_detail(hub, app: QApplication):
    from shared.visual_qa import hub_patients

    patient = hub_patients()[0]
    hub._select_patient(patient["patient_id"], patient["patient_name"])
    drain(app, 1000)
    detail = hub._stack.currentWidget()
    try:
        detail._set_legal_consent({
            "status": "vigente",
            "accepted_at_utc": "2026-05-18T12:00:00Z",
            "disclaimer_version": "legal-2026-05-16",
            "privacy_version": "privacy-2026-05-16",
            "neuromood_suite_version": "1.0.0",
            "disclaimer_text_hash": "demo-hash",
        }, None)
        detail._tab_reg._on_datos_loaded(_detail_demo_data())
    except Exception as exc:
        log(f"WARN could not inject detail demo data: {exc}")
    drain(app, 800)
    return detail


def capture_hub(app: QApplication, out_root: Path, themes: tuple[str, ...] = ("dark", "light")) -> None:
    from hub.main_qt import NeuroMoodHub

    views = [
        ("00_pacientes", "pacientes"),
        ("01_dashboard", "dashboard"),
        ("02_ia", "ia"),
        ("03_config", "config"),
    ]
    detail_tabs = [
        ("04_detalle_registros", 0),
        ("05_detalle_asignar", 1),
        ("06_detalle_banco", 2),
        ("07_detalle_ia", 3),
    ]
    for theme in themes:
        log(f"== Hub {theme} ==")
        hub = NeuroMoodHub()
        maximize(hub, app)
        drain(app, 900)
        hub._activate_visual_qa_hub()
        set_app_theme(hub, theme, app)
        drain(app, 800)
        for slug, view_id in views:
            hub._on_nav(view_id)
            drain(app, 800)
            capture(app, hub, out_root / "hub" / theme / f"{slug}.png", f"hub/{theme}/{slug}")
        detail = _prepare_hub_detail(hub, app)
        for slug, idx in detail_tabs:
            try:
                detail._tabs.setCurrentIndex(idx)
            except Exception:
                pass
            drain(app, 800)
            capture(app, hub, out_root / "hub" / theme / f"{slug}.png", f"hub/{theme}/{slug}")
        close_window(app, hub)


def _patch_installer_theme(theme: str) -> None:
    import shared.installer_common as ic
    from shared.theme import V3_DARK, V3_LIGHT

    palette = V3_LIGHT if theme == "light" else V3_DARK
    is_light = theme == "light"
    surface = palette["surface"] if is_light else palette["surfaceSolid"]
    elevated = palette["elevated"] if is_light else palette["elevatedSolid"]
    border = palette["border"] if is_light else palette["borderSolid"]
    success_bg = palette["successSoft"] if is_light else "#091E10"
    text_on_accent = "#0b1220"
    values = {
        "BG_PRIMARY": palette["bg"],
        "BG_SECONDARY": palette["bgAlt"],
        "BG_SURFACE": surface,
        "BG_ELEVATED": elevated,
        "ACCENT": palette["teal"],
        "ACCENT_HOVER": palette["cyan"],
        "TEXT_PRIMARY": palette["text"],
        "TEXT_SEC": palette["text2"],
        "TEXT_TERT": palette["text3"],
        "TEXT_ON_ACCENT": text_on_accent,
        "BORDER": border,
        "SUCCESS": palette["success"],
        "WARNING_C": palette["warning"],
        "ERROR_C": palette["danger"],
        "SUCCESS_BG": success_bg,
        "VIOLET": palette["violet"],
        "VIOLET_HOVER": palette["violet"],
        "TEAL": palette["teal"],
        "TEAL_HOVER": palette["cyan"],
        "GRAD_FROM": palette["gradFrom"],
        "GRAD_MID": palette["gradMid"],
        "GRAD_TO": palette["gradTo"],
        "DANGER_FROM": palette["danger"],
        "DANGER_TO": palette["warning"],
    }
    for key, val in values.items():
        setattr(ic, key, val)
    for mod_name in (
        "installers.installer",
        "installers.installer_pro",
        "installers.uninstaller",
        "installers.uninstaller_pro",
    ):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            for key, val in values.items():
                if hasattr(mod, key):
                    setattr(mod, key, val)


def _capture_installer_pages(app: QApplication, out_root: Path, theme: str) -> None:
    _patch_installer_theme(theme)
    from installers.installer import InstaladorNeuroMood
    from installers.installer_pro import InstaladorPro

    log(f"== Installers {theme} ==")

    suite = InstaladorNeuroMood()
    suite._auth_ok = True
    suite._auth_email = "ana.martinez@example.com"
    suite._auth_user_id = "qa-user-001"
    suite._consent_ok = True
    suite._install_dir = str(Path.home() / "NeuromoodV3_QA" / "NeuroMood Suite")
    maximize(suite, app, allow_fixed=True)
    for idx, slug in enumerate(("00_bienvenida", "01_cuenta", "02_consentimiento", "03_instalar", "04_finalizar")):
        suite._ir_a(idx)
        if idx == 1:
            suite._set_auth_status("Sesion iniciada para ana.martinez@example.com", suite.SUCCESS if hasattr(suite, "SUCCESS") else "#10b981")
        if idx == 2 and hasattr(suite, "_chk_legal"):
            suite._chk_legal.setChecked(True)
        if idx == 3 and hasattr(suite, "_install_progress"):
            suite._install_progress.set_progress(42, "Copiando archivos de la Suite...")
            suite._install_progress.append_line("Preparando carpeta de instalacion")
            suite._install_progress.append_line("Copiando recursos y base local")
        if idx == 4:
            if hasattr(suite, "_lbl_cuenta_val"):
                suite._lbl_cuenta_val.setText(suite._auth_email)
            if hasattr(suite, "_lbl_carpeta_val"):
                suite._lbl_carpeta_val.setText(suite._install_dir)
        drain(app, 600)
        capture(app, suite, out_root / "installers" / "suite" / theme / f"{slug}.png", f"installer_suite/{theme}/{slug}")
    close_window(app, suite)

    hub = InstaladorPro()
    hub._install_dir = str(Path.home() / "NeuromoodV3_QA" / "NeuroMood Hub")
    maximize(hub, app, allow_fixed=True)
    for idx, slug in enumerate(("00_bienvenida", "01_instalar", "02_finalizar")):
        hub._ir_a(idx)
        if idx == 1 and hasattr(hub, "_install_progress"):
            hub._install_progress.set_progress(56, "Copiando NeuroMood Hub...")
            hub._install_progress.append_line("Preparando recursos profesionales")
            hub._install_progress.append_line("Configurando accesos del Hub")
        drain(app, 600)
        capture(app, hub, out_root / "installers" / "hub" / theme / f"{slug}.png", f"installer_hub/{theme}/{slug}")
    close_window(app, hub)


class _DummyWorker:
    def __init__(self, conservar: bool = True):
        self._conservar = conservar


def _capture_uninstaller_pages(app: QApplication, out_root: Path, theme: str) -> None:
    _patch_installer_theme(theme)
    from installers.uninstaller import DesinstaladorNeuroMood
    from installers.uninstaller_pro import DesinstaladorPro

    log(f"== Uninstallers {theme} ==")

    old_argv = sys.argv[:]
    sys.argv = [old_argv[0], "--install-dir", str(Path.home() / "NeuroMood")]
    suite = DesinstaladorNeuroMood()
    sys.argv = old_argv
    maximize(suite, app, allow_fixed=True)
    capture(app, suite, out_root / "uninstallers" / "suite" / theme / "00_confirmar.png", f"uninstaller_suite/{theme}/00_confirmar")
    suite._add_page(lambda page, lay: suite._build_progress(page, lay))
    suite._ir_a(1)
    suite._set_progress(0.75, "Eliminando archivos de instalacion...")
    drain(app, 600)
    capture(app, suite, out_root / "uninstallers" / "suite" / theme / "01_eliminando.png", f"uninstaller_suite/{theme}/01_eliminando")
    suite._worker = _DummyWorker(True)
    suite._add_page(lambda page, lay: suite._build_done(page, lay))
    suite._ir_a(2)
    drain(app, 600)
    capture(app, suite, out_root / "uninstallers" / "suite" / theme / "02_finalizado.png", f"uninstaller_suite/{theme}/02_finalizado")
    close_window(app, suite)

    old_argv = sys.argv[:]
    sys.argv = [old_argv[0], "--install-dir", str(Path.home() / "NeuroMood Hub")]
    hub = DesinstaladorPro()
    sys.argv = old_argv
    maximize(hub, app, allow_fixed=True)
    capture(app, hub, out_root / "uninstallers" / "hub" / theme / "00_confirmar.png", f"uninstaller_hub/{theme}/00_confirmar")
    hub._add_page(lambda page, lay: hub._build_progress(page, lay))
    hub._ir_a(1)
    hub._set_progress(0.80, "Eliminando archivos...")
    drain(app, 600)
    capture(app, hub, out_root / "uninstallers" / "hub" / theme / "01_eliminando.png", f"uninstaller_hub/{theme}/01_eliminando")
    hub._worker = _DummyWorker(True)
    hub._add_page(lambda page, lay: hub._build_done(page, lay))
    hub._ir_a(2)
    drain(app, 600)
    capture(app, hub, out_root / "uninstallers" / "hub" / theme / "02_finalizado.png", f"uninstaller_hub/{theme}/02_finalizado")
    close_window(app, hub)


def capture_installers(app: QApplication, out_root: Path, themes: tuple[str, ...] = ("dark", "light")) -> None:
    for theme in themes:
        _capture_installer_pages(app, out_root, theme)


def capture_uninstallers(app: QApplication, out_root: Path, themes: tuple[str, ...] = ("dark", "light")) -> None:
    for theme in themes:
        _capture_uninstaller_pages(app, out_root, theme)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture all NeuroMood UI screens fullscreen.")
    parser.add_argument("--out", default="", help="Output directory. Defaults to _qa_output/fullscreen_capture/<timestamp>.")
    parser.add_argument("--skip-apps", action="store_true", help="Skip Suite and Hub app captures.")
    parser.add_argument("--skip-installers", action="store_true", help="Skip installer/uninstaller captures.")
    parser.add_argument("--only", choices=("all", "suite", "hub", "installers", "uninstallers"), default="all",
                        help="Capture only one UI family.")
    parser.add_argument("--theme", choices=("all", "dark", "light"), default="all",
                        help="Capture only one theme.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out).resolve() if args.out else OUT_BASE / stamp
    out_root.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood Fullscreen Capture QA")

    started = datetime.now().isoformat(timespec="seconds")
    themes = ("dark", "light") if args.theme == "all" else (args.theme,)
    if args.only in ("all", "suite") and not args.skip_apps:
        capture_suite(app, out_root, themes)
    if args.only in ("all", "hub") and not args.skip_apps:
        capture_hub(app, out_root, themes)
    if args.only in ("all", "installers") and not args.skip_installers:
        capture_installers(app, out_root, themes)
    if args.only in ("all", "uninstallers") and not args.skip_installers:
        capture_uninstallers(app, out_root, themes)

    manifest = {
        "started_at": started,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(out_root),
        "note": "Source capture only. No EXE rebuild. Install/uninstall workers were not executed.",
        "installer_light_theme": "forced token preview for screenshots; production installer_common is dark-only unless source theme support is added.",
        "captures": CAPTURES,
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(f"DONE {len(CAPTURES)} captures -> {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
