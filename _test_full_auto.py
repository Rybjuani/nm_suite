"""
_test_full_auto.py — Test de integración completo.
Abre la app paciente real, navega por los 7 módulos, captura cada uno,
cambia a light mode, captura el dashboard del Hub.
Auto-cierra al terminar.
Ejecutar: python _test_full_auto.py
"""
import sys, os

_proj = os.path.dirname(os.path.abspath(__file__))
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import Qt, QTimer, QPointF, QEvent
from PyQt6.QtGui import QEnterEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication

OUT = os.path.join(_proj, "_test_screens")
os.makedirs(OUT, exist_ok=True)


def _cap(app, name):
    QApplication.processEvents()
    path = os.path.join(OUT, f"{name}.png")
    app.grab().save(path)
    print(f"  {name}.png", flush=True)


def _click(w):
    from PyQt6.QtCore import QPointF as _QPF
    rc = w.rect()
    c = _QPF(rc.center())
    g = _QPF(w.mapTo(w.window(), rc.center()))
    QApplication.sendEvent(w, QMouseEvent(
        QEvent.Type.MouseButtonPress, c, g,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier))
    QApplication.processEvents()
    QApplication.sendEvent(w, QMouseEvent(
        QEvent.Type.MouseButtonRelease, c, g,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier))
    QApplication.processEvents()


def _run_step(i, steps, app):
    if i >= len(steps):
        print(f"\n=== {len(steps)} capturas completadas ===")
        print(f"  {OUT}")
        QTimer.singleShot(200, app.close)
        return
    delay, fn, label = steps[i]
    print(f"  [{i+1}/{len(steps)}] {label}...", flush=True)
    QTimer.singleShot(delay, lambda idx=i: _do_step(idx, steps, app))


def _do_step(i, steps, app):
    _, fn, _ = steps[i]
    fn(app)
    _run_step(i + 1, steps, app)


# ── Patient App Tests ─────────────────────────────────────────────────────────

_MODULES = ["animo", "respiracion", "registro", "rutina", "actividades", "timer", "avisos"]

print("=" * 50, flush=True)
print("NeuroMood Full Integration Test", flush=True)
print("=" * 50, flush=True)

app_patient = QApplication.instance() or QApplication(sys.argv)
app_patient.setApplicationName("NeuroMood_FullTest")

from app.main_qt import NeuroMoodApp
patient = NeuroMoodApp()
patient.show()


def _nav_to(module_id):
    patient._navigate_to(module_id)


def _go_home():
    patient._go_home()


def _toggle_theme():
    patient._toggle_theme()


def _s00(app):
    _cap(app, "full_01_home")


def _s01(app):
    _nav_to("animo")
    _cap(app, "full_02_animo")


def _s02(app):
    _go_home()
    _cap(app, "full_03_home_after_animo")


def _s03(app):
    _nav_to("respiracion")
    _cap(app, "full_04_respiracion")


def _s04(app):
    _nav_to("registro")
    _cap(app, "full_05_registro_tcc")


def _s05(app):
    _nav_to("rutina")
    _cap(app, "full_06_rutina")


def _s06(app):
    _nav_to("actividades")
    _cap(app, "full_07_actividades")


def _s07(app):
    _nav_to("timer")
    _cap(app, "full_08_timer")


def _s08(app):
    _nav_to("avisos")
    _cap(app, "full_09_avisos")


def _s09(app):
    _go_home()
    _cap(app, "full_10_home_final")


def _s10(app):
    _toggle_theme()
    _cap(app, "full_11_light_mode")


def _s11(app):
    _toggle_theme()
    _cap(app, "full_12_dark_restored")


def _s_fin(app):
    pass


def _start_patient():
    steps = [
        (800,  _s00, "01_home"),
        (500,  _s01, "02_animo"),
        (600,  _s02, "03_home_after_animo"),
        (500,  _s03, "04_respiracion"),
        (500,  _s04, "05_registro_tcc"),
        (500,  _s05, "06_rutina"),
        (500,  _s06, "07_actividades"),
        (500,  _s07, "08_timer"),
        (500,  _s08, "09_avisos"),
        (600,  _s09, "10_home_final"),
        (400,  _s10, "11_light_mode"),
        (400,  _s11, "12_dark_restored"),
        (200,  _s_fin, "fin"),
    ]
    _run_step(0, steps, patient)


QTimer.singleShot(2000, _start_patient)
sys.exit(app_patient.exec())
