"""
_test_color_regression.py — Regresión visual de colores del design system V3.

Muestrea píxeles en posiciones conocidas de cada pantalla y compara contra
los tokens actuales de shared/theme.py. Detecta automáticamente:
  - Token no propagado a un paintEvent (color hardcodeado)
  - Light mode roto (colores idénticos en ambos modos)
  - Header / sidebar usando token incorrecto
  - Regresión al reemplazar un token de tema

Límites de tolerancia (L1 rgb):
  SOLID = 20  → widget con fill sólido: header, sidebar
  AURA  = 35  → área con aura gradient (bg_primary con superposición)
  LIGHT = 80  → transición dark→light (debe diferir mucho)

Uso:
    python _test_color_regression.py
    python _test_color_regression.py --patient
    python _test_color_regression.py --hub
"""

import sys
import os
import argparse

_proj = os.path.dirname(os.path.abspath(__file__))
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor

from shared.theme import COLORS

# ── Tolerancias ────────────────────────────────────────────────────────────────
TOL_SOLID = 20   # fill sólido (header, sidebar)
TOL_AURA  = 35   # zona con aura radial superpuesta
TOL_LIGHT = 80   # diferencia mínima esperada entre dark y light

DARK  = COLORS["dark_hybrid"]
LIGHT = COLORS["light_hybrid"]

# ── Resultados globales ────────────────────────────────────────────────────────
_results: list[dict] = []
_passed = 0
_failed = 0


# ── Helpers de color ──────────────────────────────────────────────────────────

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _sample_pixel(pixmap, x: int, y: int) -> tuple[int, int, int]:
    """Devuelve el RGB del píxel (x, y) en el pixmap."""
    img = pixmap.toImage()
    c = img.pixelColor(
        max(0, min(x, pixmap.width() - 1)),
        max(0, min(y, pixmap.height() - 1)),
    )
    return (c.red(), c.green(), c.blue())


def _l1_delta(actual: tuple, expected_hex: str) -> int:
    exp = _hex_to_rgb(expected_hex)
    return sum(abs(a - e) for a, e in zip(actual, exp))


def _assert_color(label: str, pixmap, x: int, y: int,
                  expected_hex: str, tolerance: int) -> bool:
    global _passed, _failed
    actual = _sample_pixel(pixmap, x, y)
    delta = _l1_delta(actual, expected_hex)
    ok = delta <= tolerance
    status = "PASS" if ok else "FAIL"
    exp_rgb = _hex_to_rgb(expected_hex)
    record = {
        "label":    label,
        "status":   status,
        "actual":   f"rgb{actual}",
        "expected": f"{expected_hex} rgb{exp_rgb}",
        "delta":    delta,
        "tol":      tolerance,
        "pos":      (x, y),
    }
    _results.append(record)
    if ok:
        _passed += 1
        print(f"  PASS  {label}")
    else:
        _failed += 1
        print(f"  FAIL  {label}")
        print(f"        actual  = rgb{actual}")
        print(f"        expected= {expected_hex} rgb{exp_rgb}  (delta={delta}, tol={tolerance})")
    return ok


def _assert_contrast(label: str, pix_a, xa, ya, pix_b, xb, yb,
                     min_delta: int = TOL_LIGHT) -> bool:
    """Verifica que dos píxeles difieran suficientemente (test dark!=light)."""
    global _passed, _failed
    a = _sample_pixel(pix_a, xa, ya)
    b = _sample_pixel(pix_b, xb, yb)
    delta = sum(abs(x - y) for x, y in zip(a, b))
    ok = delta >= min_delta
    status = "PASS" if ok else "FAIL"
    _results.append({
        "label":   label,
        "status":  status,
        "dark_px": f"rgb{a}",
        "light_px": f"rgb{b}",
        "delta":   delta,
        "min_delta": min_delta,
    })
    if ok:
        _passed += 1
        print(f"  PASS  {label}  (delta={delta})")
    else:
        _failed += 1
        print(f"  FAIL  {label}  -- dark/light indistinguibles (delta={delta} < {min_delta})")
    return ok


# ── Tests de pantalla paciente ─────────────────────────────────────────────────

def _run_patient_checks(patient, step_fn):
    """Checks sobre la app paciente (dark + light + módulos)."""

    def _grab_full():
        QApplication.processEvents()
        QApplication.processEvents()
        return patient.grab()

    w = patient.width()
    h = patient.height()
    hdr_h = patient._header.height()

    # Posiciones seguras respecto de la geometría
    # top-right del contenido (sin aura, sin widgets encima)
    cx = w - 20
    cy = hdr_h + 15

    # Header center-derecho (evita logo izquierda y botón toggle derecha ~45px)
    hx = w - 70
    hy = hdr_h // 2

    # ── Home — dark mode ──────────────────────────────────────────────────────
    step_fn("Home dark – captura")
    pix_home_dark = _grab_full()

    _assert_color(
        "Home dark: header bg_surface",
        patient._header.grab(),
        patient._header.width() - 70,
        patient._header.height() // 2,
        DARK["bg_surface"], TOL_SOLID,
    )
    _assert_color(
        "Home dark: contenido bg_primary (top-right)",
        pix_home_dark, cx, cy,
        DARK["bg_primary"], TOL_AURA,
    )

    # ── Módulo Ánimo — dark mode ──────────────────────────────────────────────
    step_fn("Ánimo dark – navegar + captura")
    patient._navigate_to("animo")
    QApplication.processEvents()
    QApplication.processEvents()
    pix_animo_dark = _grab_full()

    _assert_color(
        "Ánimo dark: header bg_surface",
        patient._header.grab(),
        patient._header.width() - 70,
        patient._header.height() // 2,
        DARK["bg_surface"], TOL_SOLID,
    )
    _assert_color(
        "Ánimo dark: contenido bg_primary (top-right)",
        pix_animo_dark, cx, cy,
        DARK["bg_primary"], TOL_AURA,
    )
    patient._go_home()
    QApplication.processEvents()

    # ── Módulo Respiración — dark mode ────────────────────────────────────────
    step_fn("Respiración dark – navegar + captura")
    patient._navigate_to("respiracion")
    QApplication.processEvents()
    QApplication.processEvents()
    pix_resp_dark = _grab_full()

    _assert_color(
        "Respiración dark: header bg_surface",
        patient._header.grab(),
        patient._header.width() - 70,
        patient._header.height() // 2,
        DARK["bg_surface"], TOL_SOLID,
    )
    _assert_color(
        "Respiración dark: contenido bg_primary (top-right)",
        pix_resp_dark, cx, cy,
        DARK["bg_primary"], TOL_AURA,
    )
    patient._go_home()
    QApplication.processEvents()

    # ── Capturar dark ANTES de toggle (para comparar después) ────────────────
    hdr_x = patient._header.width() - 70
    hdr_y = patient._header.height() // 2
    pix_header_dark = patient._header.grab()

    # ── Light mode ────────────────────────────────────────────────────────────
    step_fn("Toggle a light mode")
    patient._toggle_theme()
    QApplication.processEvents()
    QApplication.processEvents()
    pix_home_light = _grab_full()
    pix_header_light = patient._header.grab()

    _assert_color(
        "Home light: header bg_surface",
        pix_header_light, hdr_x, hdr_y,
        LIGHT["bg_surface"], TOL_SOLID,
    )
    _assert_color(
        "Home light: contenido bg_primary (top-right)",
        pix_home_light, cx, cy,
        LIGHT["bg_primary"], TOL_AURA,
    )

    # ── Contraste dark != light ───────────────────────────────────────────────
    _assert_contrast(
        "Header: dark (#1e293b) != light (bg_surface)",
        pix_header_dark, hdr_x, hdr_y,
        pix_header_light, hdr_x, hdr_y,
        min_delta=TOL_LIGHT,
    )

    # Restaurar dark
    patient._toggle_theme()
    QApplication.processEvents()

    step_fn("Módulos restantes dark – capturas rápidas")
    for mid in ["registro", "rutina", "actividades", "timer", "avisos"]:
        patient._navigate_to(mid)
        QApplication.processEvents()
        QApplication.processEvents()
        pix = _grab_full()
        _assert_color(
            f"{mid} dark: header bg_surface",
            patient._header.grab(),
            patient._header.width() - 70,
            patient._header.height() // 2,
            DARK["bg_surface"], TOL_SOLID,
        )
        _assert_color(
            f"{mid} dark: contenido bg_primary",
            pix, cx, cy,
            DARK["bg_primary"], TOL_AURA,
        )
        patient._go_home()
        QApplication.processEvents()


# ── Tests del Hub ──────────────────────────────────────────────────────────────

def _run_hub_checks(hub, step_fn):
    """Checks sobre el Hub Pro (sidebar, vistas, dark+light)."""

    def _grab_full():
        QApplication.processEvents()
        QApplication.processEvents()
        return hub.grab()

    step_fn("Hub dark – captura base")
    pix_dark = _grab_full()
    w = hub.width()
    h = hub.height()

    # El hub tiene su propio NMHeader — el contenido empieza debajo de él
    hdr_h = hub._header.height() if hasattr(hub, "_header") else 56

    # Sidebar: widget independiente, fill sólido con sidebar_bg
    sb = hub._sidebar
    sb_pix = sb.grab()
    sb_w = sb.width()
    sb_h = sb.height()

    _assert_color(
        "Hub dark: sidebar bg (centro-izquierda)",
        sb_pix, 10, sb_h // 2,
        DARK["sidebar_bg"], TOL_SOLID,
    )
    _assert_color(
        "Hub dark: sidebar bg (centro-derecha)",
        sb_pix, sb_w - 10, sb_h // 2,
        DARK["sidebar_bg"], TOL_SOLID,
    )

    # Contenido principal — top-right del área de stack (debajo del header)
    sidebar_actual_w = sb_w
    content_cx = sidebar_actual_w + (w - sidebar_actual_w) // 2
    content_cy = hdr_h + 15  # justo debajo del NMHeader del hub

    _assert_color(
        "Hub dark: contenido bg_primary (top-center)",
        pix_dark, content_cx, content_cy,
        DARK["bg_primary"], TOL_AURA,
    )

    # ── Vista Pacientes ───────────────────────────────────────────────────────
    step_fn("Hub: navegar a Pacientes")
    hub._on_nav("pacientes")
    QApplication.processEvents()
    QApplication.processEvents()
    pix_pac = _grab_full()
    _assert_color(
        "Hub Pacientes: sidebar bg intacto",
        hub._sidebar.grab(), 10, hub._sidebar.height() // 2,
        DARK["sidebar_bg"], TOL_SOLID,
    )

    # ── Vista Config ──────────────────────────────────────────────────────────
    step_fn("Hub: navegar a Config")
    hub._on_nav("config")
    QApplication.processEvents()
    QApplication.processEvents()

    # ── Light mode Hub ────────────────────────────────────────────────────────
    step_fn("Hub: toggle a light mode")
    hub._toggle_theme()
    QApplication.processEvents()
    QApplication.processEvents()
    pix_light = hub.grab()
    sb_light = hub._sidebar.grab()

    _assert_color(
        "Hub light: sidebar bg_surface (light)",
        sb_light, 10, hub._sidebar.height() // 2,
        LIGHT["sidebar_bg"], TOL_SOLID,
    )

    _assert_contrast(
        "Hub sidebar: dark (#12192a) != light (#f1f5f9)",
        sb_pix, 10, sb_h // 2,
        sb_light, 10, hub._sidebar.height() // 2,
        min_delta=TOL_LIGHT,
    )

    step_fn("Hub: restaurar dark")
    hub._toggle_theme()
    QApplication.processEvents()

    # ── Dashboard ─────────────────────────────────────────────────────────────
    step_fn("Hub: navegar a Dashboard")
    hub._on_nav("dashboard")
    QApplication.processEvents()
    QApplication.processEvents()
    pix_dash = _grab_full()
    _assert_color(
        "Hub Dashboard: contenido bg_primary",
        pix_dash, content_cx, content_cy,
        DARK["bg_primary"], TOL_AURA,
    )


# ── Runner principal ───────────────────────────────────────────────────────────

def _print_summary():
    print()
    print("=" * 55)
    total = _passed + _failed
    print(f"  Color Regression: {_passed}/{total} PASS  |  {_failed} FAIL")
    print("=" * 55)
    if _failed:
        print()
        print("  Checks fallidos:")
        for r in _results:
            if r["status"] == "FAIL":
                print(f"    ✗ {r['label']}")
                if "actual" in r:
                    print(f"        actual={r['actual']}  expected={r['expected']}"
                          f"  delta={r['delta']}")
    print()


def run_patient_test():
    print("=" * 55)
    print("  Color Regression — App Paciente")
    print("=" * 55)

    app = QApplication.instance() or QApplication(sys.argv)
    from app.main_qt import NeuroMoodApp
    patient = NeuroMoodApp()
    patient.show()
    QApplication.processEvents()
    QApplication.processEvents()

    steps_done = [0]
    def step(label):
        steps_done[0] += 1
        print(f"\n  [{steps_done[0]}] {label}")

    def _run():
        try:
            _run_patient_checks(patient, step)
        except Exception as e:
            import traceback
            print(f"\n  CRASH en test paciente: {e}")
            traceback.print_exc()
        finally:
            _print_summary()
            QTimer.singleShot(300, patient.close)
            QTimer.singleShot(600, app.quit)

    QTimer.singleShot(2000, _run)
    app.exec()


def run_hub_test():
    print("=" * 55)
    print("  Color Regression — Hub Pro")
    print("=" * 55)

    app = QApplication.instance() or QApplication(sys.argv)
    from hub.main_qt import HubProfesional
    hub = HubProfesional()
    hub.show()
    QApplication.processEvents()
    QApplication.processEvents()

    steps_done = [0]
    def step(label):
        steps_done[0] += 1
        print(f"\n  [{steps_done[0]}] {label}")

    def _run():
        try:
            _run_hub_checks(hub, step)
        except Exception as e:
            import traceback
            print(f"\n  CRASH en test hub: {e}")
            traceback.print_exc()
        finally:
            _print_summary()
            QTimer.singleShot(300, hub.close)
            QTimer.singleShot(600, app.quit)

    QTimer.singleShot(2500, _run)
    app.exec()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--patient", action="store_true")
    p.add_argument("--hub",     action="store_true")
    args = p.parse_args()

    run_both = not args.patient and not args.hub

    if args.patient or run_both:
        run_patient_test()
    if args.hub or run_both:
        run_hub_test()
