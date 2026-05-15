"""
smoke_test_runner.py — Automated visual QA smoke testing for NeuroMood.
Auto-discovers apps, navigates modules, captures screenshots, logs exceptions.
Uses REAL Windows rendering (not offscreen) for accurate visual testing.
Usage: python smoke_test_runner.py [--quick] [--full] [--app patient|hub|all]
"""
import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime

_proj = str(Path(__file__).resolve().parent)
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import Qt, QTimer, QPointF, QEvent, QRect
from PyQt6.QtGui import QEnterEvent, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QTabWidget, QStackedWidget

OUT_DIR = os.path.join(_proj, "_test_screens", "smoke")
os.makedirs(OUT_DIR, exist_ok=True)

REPORT = {
    "timestamp": datetime.now().isoformat(),
    "app": "",
    "passed": 0,
    "failed": 0,
    "steps": [],
    "crashes": [],
    "screenshots": [],
}


def _log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:12]
    print(f"  [{ts}] [{level}] {msg}", flush=True)


def _capture(widget, name):
    path = os.path.join(OUT_DIR, f"{name}.png")
    QApplication.processEvents()
    pix = widget.grab() if hasattr(widget, "grab") else None
    if pix:
        pix.save(path)
        REPORT["screenshots"].append(path)
        return path
    return None


def _click(widget):
    """Simulate click on widget center."""
    from PyQt6.QtCore import QPointF as _QPF
    try:
        rc = widget.rect()
        c = _QPF(rc.center())
        g = _QPF(widget.mapTo(widget.window(), rc.center()))
        QApplication.sendEvent(widget, QMouseEvent(
            QEvent.Type.MouseButtonPress, c, g,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()
        QApplication.sendEvent(widget, QMouseEvent(
            QEvent.Type.MouseButtonRelease, c, g,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()
        return True
    except Exception as e:
        _log(f"Click failed: {e}", "ERROR")
        return False


def _find_buttons(widget, texts: list = None) -> list:
    """Find all clickable buttons in widget tree."""
    buttons = []
    try:
        for child in widget.findChildren(QPushButton):
            if child.isVisible() and child.isEnabled():
                txt = child.text().strip()
                if texts is None or any(t.lower() in txt.lower() for t in texts):
                    buttons.append(child)
    except Exception:
        pass
    return buttons


def _find_by_objectname(widget, name: str):
    """Find widget by objectName."""
    try:
        return widget.findChild(type(QWidget), name)
    except Exception:
        return None


def _navigate_homeview(app, module_id: str) -> bool:
    """Navigate to a module from HomeView."""
    try:
        app._navigate_to(module_id)
        QApplication.processEvents()
        QApplication.processEvents()
        _log(f"Navigated to: {module_id}")
        return True
    except Exception as e:
        REPORT["crashes"].append(f"Navigate {module_id}: {e}")
        _log(f"Navigation failed: {module_id} - {e}", "ERROR")
        return False


def _go_home(app) -> bool:
    """Navigate back to HomeView."""
    try:
        app._go_home()
        QApplication.processEvents()
        _log("Returned to home")
        return True
    except Exception as e:
        _log(f"Go home failed: {e}", "ERROR")
        return False


def _toggle_theme(app) -> bool:
    """Toggle dark/light theme."""
    try:
        app._toggle_theme()
        QApplication.processEvents()
        _log("Toggled theme")
        return True
    except Exception as e:
        REPORT["crashes"].append(f"Theme toggle: {e}")
        _log(f"Theme toggle failed: {e}", "ERROR")
        return False


MODULE_IDS = ["animo", "respiracion", "registro", "rutina", "actividades", "timer", "avisos"]


def smoke_test_patient(quick: bool = False) -> dict:
    """Run smoke test on patient app."""
    _log("=== Patient App Smoke Test ===")
    REPORT["app"] = "patient"

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood_SmokeTest")

    from app.main_qt import NeuroMoodApp
    patient = NeuroMoodApp()
    patient.show()
    QApplication.processEvents()
    QApplication.processEvents()

    def _step(name, fn, *args):
        REPORT["steps"].append({"name": name, "status": "running"})
        try:
            result = fn(*args)
            status = "passed" if result is not False else "failed"
            REPORT["steps"][-1]["status"] = status
            if status == "passed":
                REPORT["passed"] += 1
            else:
                REPORT["failed"] += 1
            _log(f"{'OK' if status == 'passed' else 'FAIL'}: {name}")
            return result
        except Exception as e:
            REPORT["steps"][-1]["status"] = "crashed"
            REPORT["failed"] += 1
            REPORT["crashes"].append(f"{name}: {e}\n{traceback.format_exc()}")
            _log(f"CRASH: {name} - {e}", "ERROR")
            return False

    steps = [
        ("Home capture", lambda: _capture(patient, "s01_home")),
    ]

    if not quick:
        steps += [
            ("Theme toggle light", lambda: _toggle_theme(patient)),
            ("Light home capture", lambda: _capture(patient, "s02_light_home")),
            ("Theme toggle dark", lambda: _toggle_theme(patient)),
        ]

    mods = MODULE_IDS[:3] if quick else MODULE_IDS
    for mid in mods:
        steps.append((f"Navigate to {mid}", lambda m=mid: _navigate_homeview(patient, m)))
        steps.append((f"Capture {mid}", lambda m=mid: _capture(patient, f"s_mod_{mid}")))
        steps.append(("Go home", lambda: _go_home(patient)))

    # Resize test
    for w, h in [(800, 600), (1280, 720), (1366, 768)]:
        steps.append((f"Resize {w}x{h}", lambda ww=w, hh=h: patient.resize(ww, hh)))
        steps.append((f"Capture {w}x{h}", lambda ww=w, hh=h: _capture(patient, f"s_resize_{ww}x{hh}")))

    # Run steps
    def _run_test():
        nonlocal steps
        i = [0]

        # Safety timeout
        QTimer.singleShot(45000, lambda: (_log("TIMEOUT", "ERROR"),
                                           _save_report(), patient.close(), app.quit()))

        def _next():
            if i[0] >= len(steps):
                _log(f"=== Smoke complete: {REPORT['passed']} passed, {REPORT['failed']} failed ===")
                _save_report()
                QTimer.singleShot(500, lambda: patient.close())
                QTimer.singleShot(800, app.quit)
                return
            _, fn = steps[i[0]]
            name = steps[i[0]][0]
            ok = _step(name, fn)
            if ok is False:
                _log(f"Step failed, continuing...", "WARN")
            i[0] += 1
            QTimer.singleShot(50, _next)

        _next()

    QTimer.singleShot(2000, _run_test)
    app.exec()
    return REPORT


def smoke_test_hub(quick: bool = False) -> dict:
    """Run smoke test on Hub."""
    _log("=== Hub Smoke Test ===")
    REPORT["app"] = "hub_profesional"

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood_HubSmoke")

    from hub.main_qt import HubProfesional
    hub = HubProfesional()
    hub.show()
    QApplication.processEvents()
    QApplication.processEvents()

    def _step(name, fn):
        REPORT["steps"].append({"name": name, "status": "running"})
        try:
            result = fn()
            status = "passed" if result is not False else "failed"
            REPORT["steps"][-1]["status"] = status
            REPORT["passed" if status == "passed" else "failed"] += 1
            _log(f"{'OK' if status == 'passed' else 'FAIL'}: {name}")
            return result
        except Exception as e:
            REPORT["steps"][-1]["status"] = "crashed"
            REPORT["failed"] += 1
            REPORT["crashes"].append(f"{name}: {e}\n{traceback.format_exc()}")
            _log(f"CRASH: {name} - {e}", "ERROR")
            return False

    def _open_ia_detalle():
        """Instancia DetallePacienteView con datos mock para cubrir la vista IA."""
        try:
            from hub.pacientes_qt import DetallePacienteView
            detalle = DetallePacienteView(
                modo=hub._modo, sb=None,
                paciente_id="smoke_test_id",
                paciente_nombre="Paciente Test",
            )
            hub._stack.addWidget(detalle)
            hub._stack.setCurrentWidget(detalle)
            QApplication.processEvents()
            # Cambiar a tab IA (último tab del detalle)
            tabs = detalle.findChildren(QTabWidget)
            if tabs:
                tabs[0].setCurrentIndex(tabs[0].count() - 1)
                QApplication.processEvents()
            return True
        except Exception as e:
            _log(f"IA detalle mock: {e}", "WARN")
            return False

    steps = [
        ("Hub default", lambda: _capture(hub, "h01_default")),
        ("Navigate pacientes", lambda: hub._on_nav("pacientes")),
        ("Capture pacientes", lambda: _capture(hub, "h02_pacientes")),
        ("Navigate dashboard", lambda: hub._on_nav("dashboard")),
        ("Capture dashboard", lambda: _capture(hub, "h03_dashboard")),
        ("Navigate config", lambda: hub._on_nav("config")),
        ("Capture config", lambda: _capture(hub, "h04_config")),
        ("Open IA detalle (mock)", _open_ia_detalle),
        ("Capture IA detalle", lambda: _capture(hub, "h05_ia_detalle")),
        ("Navigate dashboard (restore)", lambda: hub._on_nav("dashboard")),
        ("Theme toggle light", lambda: _toggle_theme(hub)),
        ("Capture light", lambda: _capture(hub, "h06_light")),
        ("Theme toggle dark", lambda: _toggle_theme(hub)),
    ]

    # Sizes
    for w, h in [(1024, 720), (1366, 768), (1920, 1080)]:
        steps.append((f"Resize {w}x{h}", lambda ww=w, hh=h: hub.resize(ww, hh)))
        steps.append((f"Capture {w}x{h}", lambda ww=w, hh=h: _capture(hub, f"h_resize_{ww}x{hh}")))

    def _run_test():
        i = [0]

        def _next():
            if i[0] >= len(steps):
                _log(f"=== Hub Smoke complete: {REPORT['passed']} passed, {REPORT['failed']} failed ===")
                REPORT["app"] += "|hub_profesional"
                _save_report()
                QTimer.singleShot(500, lambda: hub.close())
                QTimer.singleShot(800, app.quit)
                return
            _, fn = steps[i[0]]
            name = steps[i[0]][0]
            _step(name, fn)
            i[0] += 1
            QTimer.singleShot(100, _next)

        _next()

    QTimer.singleShot(2500, _run_test)
    app.exec()
    return REPORT


def _save_report():
    path = os.path.join(OUT_DIR, "report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Report saved: {path}", flush=True)
    print(f"  Passed: {REPORT['passed']}  Failed: {REPORT['failed']}", flush=True)
    if REPORT["crashes"]:
        print(f"  Crashes: {len(REPORT['crashes'])}", flush=True)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="NeuroMood Smoke Test Runner")
    p.add_argument("--quick", action="store_true", help="Quick mode (3 modules only)")
    p.add_argument("--full", action="store_true", help="Full test (all modules)")
    p.add_argument("--app", default="all", help="App to test: patient/hub/all")
    args = p.parse_args()

    quick = args.quick and not args.full

    if args.app == "patient":
        smoke_test_patient(quick)
    elif args.app == "hub":
        smoke_test_hub(quick)
    else:
        smoke_test_patient(quick)
        # Hub runs after patient closes
