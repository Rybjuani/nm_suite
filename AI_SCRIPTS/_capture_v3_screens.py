"""
AI_SCRIPTS/_capture_v3_screens.py — Captura visual de todas las pantallas v3.

Genera PNGs en _qa_output/v3_capture/ con cada pantalla del Suite + Hub +
Installer renderizada en dark y light. Útil para diff visual contra el
mockup HTML (neuromood/project/design_handoff_neuromood_v3/NeuroMood Redesign.html).

Ejecutar:
    NM_VISUAL_QA=1 python AI_SCRIPTS/_capture_v3_screens.py
"""
import os
import sys
import traceback

# Asegurar paths
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

# Forzar visual QA + offscreen para CI / sin display
os.environ.setdefault("NM_VISUAL_QA", "1")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QSize

app = QApplication(sys.argv)

# Forzar carga de fuentes premium antes de instanciar widgets
from shared.theme_qt import _ensure_premium_font, _font_family
_ensure_premium_font()
_loaded_family = _font_family()
print(f"Premium font cargada: {_loaded_family!r}")

import shared.components_qt as cmp

OUT_DIR = os.path.join(_root, "_qa_output", "v3_capture")
os.makedirs(OUT_DIR, exist_ok=True)

# (slug, builder_fn, size) — size = (w, h) por defecto del README
SCREENS = []


def _suite_screens():
    """Suite paciente — 8 pantallas, todas tamaño 1320×860 (README v3)."""
    from app.home_qt import HomeView
    from app.modules.animo_qt import ModuloAnimo
    from app.modules.respiracion_qt import ModuloRespiracion
    from app.modules.registro_tcc_qt import ModuloRegistroTCC
    from app.modules.rutina_qt import ModuloRutina
    from app.modules.actividades_qt import ModuloActividades
    from app.modules.timer_qt import ModuloTimer
    from app.modules.avisos_qt import ModuloAvisos

    return [
        ("suite_01_inicio",
         lambda modo: HomeView(
             modo=modo,
             on_module_open=lambda mid: None,
             get_status_fn=lambda mid: {
                 "animo": "En progreso", "respiracion": "Completo",
                 "registro": "Activo", "rutina": "2/5 hoy",
                 "actividades": "3 hoy", "timer": "45 min",
                 "avisos": ""}.get(mid, ""),
             username="Ana"),
         (1320, 860)),
        ("suite_02_animo",        lambda modo: ModuloAnimo(modo=modo),       (1320, 860)),
        ("suite_03_respiracion",  lambda modo: ModuloRespiracion(modo=modo), (1320, 860)),
        ("suite_04_tcc",          lambda modo: ModuloRegistroTCC(modo=modo), (1320, 860)),
        ("suite_05_rutina",       lambda modo: ModuloRutina(modo=modo),      (1320, 860)),
        ("suite_06_actividades",  lambda modo: ModuloActividades(modo=modo), (1320, 860)),
        ("suite_07_timer",        lambda modo: ModuloTimer(modo=modo),       (1320, 860)),
        ("suite_08_avisos",       lambda modo: ModuloAvisos(modo=modo),      (1320, 860)),
    ]


def _hub_screens():
    """Hub profesional — 4 vistas, tamaño 1360×920 (README v3)."""
    from hub.main_qt import PacientesView, ConfigView, IAAssistantView

    pacientes_mock = [
        {"patient_name": "Ana Martínez", "patient_id": "abc123def456",
         "adherence": 0.85, "last_session": "hace 1 día"},
        {"patient_name": "Carlos López", "patient_id": "xyz789",
         "adherence": 0.35, "last_session": "hace 5 días"},
        {"patient_name": "María Rodríguez", "patient_id": "mno456",
         "adherence": 0.92, "last_session": "hoy"},
        {"patient_name": "Juan Pérez", "patient_id": "qwe111",
         "adherence": 0.55, "last_session": "ayer"},
        {"patient_name": "Lucía Gómez", "patient_id": "rty222",
         "adherence": 0.78, "last_session": "hace 2 días"},
    ]

    return [
        ("hub_01_pacientes",
         lambda modo: PacientesView(modo, pacientes_mock,
                                     on_select=lambda *a: None,
                                     on_refresh=lambda: None),
         (1360, 920)),
        ("hub_02_ia",
         lambda modo: IAAssistantView(modo, "Ana Martínez"),
         (1360, 920)),
        ("hub_03_config",
         lambda modo: ConfigView(modo,
                                  on_toggle_theme=lambda: None,
                                  on_reconnect=lambda: None),
         (1360, 920)),
    ]


def _installer_screens():
    """Solo verifica que installer/uninstaller arrancan; no captura pasos individuales
    porque InstallerShell maneja navegación internamente."""
    try:
        # Smoke import — no se renderiza por la complejidad de _build_shell
        import installers.installer
        import installers.uninstaller
        print("installer/uninstaller import OK (captura individual de pasos requiere flow)")
    except Exception as e:
        print(f"  installer import err: {e}")
    return []


def capture(slug: str, widget: QWidget, size: tuple[int, int], modo: str):
    w, h = size
    widget.resize(w, h)
    widget.show()
    app.processEvents()
    # Force a paint cycle
    widget.repaint()
    app.processEvents()
    pix = widget.grab()
    out_path = os.path.join(OUT_DIR, f"{slug}__{modo}.png")
    if pix.save(out_path, "PNG"):
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  OK {slug:32s} {modo:14s} {pix.width()}x{pix.height()} ({size_kb:.0f} KB)")
    else:
        print(f"  FAIL {slug}: save returned False")
    widget.hide()
    widget.deleteLater()
    app.processEvents()


def main():
    all_screens = _suite_screens() + _hub_screens()
    _installer_screens()  # solo smoke import

    total = len(all_screens) * 2   # dark + light
    print(f"\nCapturando {total} screenshots a {OUT_DIR}\n")

    for slug, builder, size in all_screens:
        for modo in ("dark_hybrid", "light_hybrid"):
            try:
                # Reset theme manager
                cmp.ThemeManager.instance().switch_mode(modo, animate=False)
                w = builder(modo)
                capture(slug, w, size, "dark" if modo == "dark_hybrid" else "light")
            except Exception:
                print(f"  ERR {slug} ({modo}):")
                traceback.print_exc()
                print()

    print(f"\nDone. Capturas en: {OUT_DIR}")
    print("Comparar contra: neuromood/project/design_handoff_neuromood_v3/NeuroMood Redesign.html")


if __name__ == "__main__":
    main()
