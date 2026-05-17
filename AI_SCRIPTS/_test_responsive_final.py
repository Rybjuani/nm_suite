"""
_test_responsive_final.py — Test definitivo de responsive, maximizado, light mode.
Abre app paciente y Hub, maximiza, navega, captura en dark y light.
Ejecutar: python _test_responsive_final.py
"""
import sys, os

_proj = os.path.dirname(os.path.abspath(__file__))
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

OUT = os.path.join(_proj, "_test_screens")
os.makedirs(OUT, exist_ok=True)

_cap_count = 0


def _cap(app, name):
    global _cap_count
    QApplication.processEvents()
    path = os.path.join(OUT, f"rf_{name}.png")
    app.grab().save(path)
    _cap_count += 1
    print(f"  [{_cap_count}] {name}.png", flush=True)


def _resize(app, w, h):
    app.resize(QSize(w, h))
    QApplication.processEvents()
    QApplication.processEvents()


def _maximize(app):
    app.showMaximized()
    QApplication.processEvents()
    QApplication.processEvents()


def _restore(app):
    app.showNormal()
    QApplication.processEvents()


# ── Patient App ───────────────────────────────────────────────────────────────

print("=" * 60, flush=True)
print("NeuroMood Responsive Final Test", flush=True)
print("=" * 60, flush=True)

app = QApplication(sys.argv)
app.setApplicationName("NeuroMood_RespFinal")

from app.main_qt import NeuroMoodApp
patient = NeuroMoodApp()
patient.show()

steps = []


def _make_patient_steps():
    # 1. Home default
    steps.append((500, lambda: _cap(patient, "p1_home_default"), "p1_home_default"))
    # 2. Home maximized
    steps.append((500, lambda: _maximize(patient), "p2_home_max"))
    steps.append((500, lambda: _cap(patient, "p2_home_max"), "p2_home_max"))
    # 3. Navigate to modules while maximized
    steps.append((500, lambda: patient._navigate_to("animo"), "p3_animo_max"))
    steps.append((500, lambda: _cap(patient, "p3_animo_max"), "p3_animo_max"))
    steps.append((500, lambda: patient._navigate_to("respiracion"), "p4_respiracion_max"))
    steps.append((500, lambda: _cap(patient, "p4_respiracion_max"), "p4_respiracion_max"))
    steps.append((500, lambda: patient._navigate_to("rutina"), "p5_rutina_max"))
    steps.append((500, lambda: _cap(patient, "p5_rutina_max"), "p5_rutina_max"))
    steps.append((500, lambda: patient._navigate_to("actividades"), "p6_actividades_max"))
    steps.append((500, lambda: _cap(patient, "p6_actividades_max"), "p6_actividades_max"))
    steps.append((500, lambda: patient._navigate_to("avisos"), "p7_avisos_max"))
    steps.append((500, lambda: _cap(patient, "p7_avisos_max"), "p7_avisos_max"))
    # 4. Go home, restore, toggle light
    steps.append((500, lambda: patient._go_home(), "p8_go_home"))
    steps.append((500, lambda: _restore(patient), "p8_restore"))
    steps.append((500, lambda: _resize(patient, 860, 640), "p8_resize"))
    steps.append((500, lambda: _cap(patient, "p8_home_restored"), "p8_home_restored"))
    # 5. Light mode
    steps.append((500, lambda: patient._toggle_theme(), "p9_light_toggle"))
    steps.append((500, lambda: _cap(patient, "p9_light_home"), "p9_light_home"))
    steps.append((500, lambda: _maximize(patient), "p10_light_max"))
    steps.append((500, lambda: _cap(patient, "p10_light_max"), "p10_light_max"))
    steps.append((500, lambda: patient._navigate_to("registro"), "p11_registro_light"))
    steps.append((500, lambda: _cap(patient, "p11_registro_light"), "p11_registro_light"))
    # 6. Dark restore
    steps.append((500, lambda: patient._go_home(), "p12_go_home"))
    steps.append((500, lambda: patient._toggle_theme(), "p12_dark_restore"))
    steps.append((500, lambda: _cap(patient, "p12_dark_final"), "p12_dark_final"))


def _run_patient(i):
    if i >= len(steps):
        print(f"\n=== Patient app: {len(steps)} capturas ===", flush=True)
        QTimer.singleShot(500, lambda: _start_hub())
        return
    delay, fn, label = steps[i]
    print(f"  [{i+1}/{len(steps)}] {label}", flush=True)
    QTimer.singleShot(delay, lambda idx=i: _do_step(idx))


def _do_step(i):
    _, fn, _ = steps[i]
    fn()
    _run_patient(i + 1)


_make_patient_steps()

# ── Hub ───────────────────────────────────────────────────────────────────────

def _start_hub():
    from hub.main_qt import NeuroMoodHub
    hub = NeuroMoodHub()
    hub.show()

    hub_steps = []

    def _make_hub_steps():
        hub_steps.append((500, lambda: _cap(hub, "h1_hub_default"), "h1_hub_default"))
        hub_steps.append((500, lambda: _maximize(hub), "h2_hub_max"))
        hub_steps.append((500, lambda: _cap(hub, "h2_hub_max"), "h2_hub_max"))
        hub_steps.append((500, lambda: hub._toggle_theme(), "h3_hub_light"))
        hub_steps.append((500, lambda: _cap(hub, "h3_hub_light"), "h3_hub_light"))
        hub_steps.append((500, lambda: _restore(hub), "h4_hub_restore"))
        hub_steps.append((500, lambda: _resize(hub, 1100, 680), "h4_resize"))
        hub_steps.append((500, lambda: _cap(hub, "h4_hub_restored"), "h4_hub_restored"))
        hub_steps.append((500, lambda: hub._toggle_theme(), "h5_hub_dark"))
        hub_steps.append((500, lambda: _cap(hub, "h5_hub_dark"), "h5_hub_dark_final"))

    def _run_hub(i):
        if i >= len(hub_steps):
            print(f"\n=== Hub: {len(hub_steps)} capturas ===", flush=True)
            print(f"\n=== TOTAL: {_cap_count} capturas ===", flush=True)
            print(f"  {OUT}", flush=True)
            QTimer.singleShot(300, patient.close)
            QTimer.singleShot(500, lambda: hub.close())
            QTimer.singleShot(800, app.quit)
            return
        delay, fn, label = hub_steps[i]
        print(f"  [{i+1}/{len(hub_steps)}] {label}", flush=True)
        QTimer.singleShot(delay, lambda idx=i: _do_hub_step(idx, hub_steps))

    def _do_hub_step(i, hs):
        _, fn, _ = hs[i]
        fn()
        _run_hub(i + 1)

    _make_hub_steps()
    _run_hub(0)


QTimer.singleShot(2000, lambda: _run_patient(0))
sys.exit(app.exec())
