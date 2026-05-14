"""
_test_responsive.py — Test de responsive, scrollbars, light mode y multitamaño.
Resizea la app a múltiples tamaños, captura módulos clave, testea scrollbars,
y verifica ambos temas sin DWM (vía ThemeManager directo, no toggle).
Ejecutar: python _test_responsive.py
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
    path = os.path.join(OUT, f"resp_{name}.png")
    app.grab().save(path)
    _cap_count += 1
    print(f"  [{_cap_count}] {name}.png", flush=True)


def _resize(app, w, h):
    app.resize(QSize(w, h))
    QApplication.processEvents()
    QApplication.processEvents()


def _nav(app, module_id):
    app._navigate_to(module_id)
    QApplication.processEvents()


def _go_home(app):
    app._go_home()
    QApplication.processEvents()


def _set_theme(app, modo):
    try:
        from shared.components_qt import ThemeManager
        from shared.theme_qt import app_palette, stylesheet_base, C
        QApplication.instance().setPalette(app_palette(modo))
        app.setStyleSheet(
            stylesheet_base(modo)
            + f"QMainWindow {{ background-color: {C('bg_primary', modo)}; }}"
        )
        ThemeManager.instance().switch_mode(modo)
        app._modo = modo
    except Exception as e:
        print(f"       (theme switch: {e})", flush=True)
    QApplication.processEvents()


# ── Test sizes ────────────────────────────────────────────────────────────────

SIZES = [
    ("min",    600, 520),   # minimum
    ("sm",     720, 580),   # small laptop
    ("md",     860, 640),   # default
    ("lg",    1024, 720),   # large
    ("wide",  1200, 640),   # ultrawide
]

print("=" * 50, flush=True)
print("NeuroMood Responsive + Light Mode Test", flush=True)
print("=" * 50, flush=True)

app = QApplication.instance() or QApplication(sys.argv)
app.setApplicationName("NeuroMood_RespTest")

from app.main_qt import NeuroMoodApp
patient = NeuroMoodApp()
patient.show()

steps = []

# ── Dark mode: home at all sizes ──────────────────────────────────────────────

for label, w, h in SIZES:
    def _make_home_step(lbl, width, height):
        def _step(app):
            _resize(app, width, height)
            _go_home(app)
            _cap(app, f"dark_home_{lbl}_{width}x{height}")
        return _step
    steps.append((0, _make_home_step(label, w, h), f"dark_home_{label}"))

# ── Dark mode: módulo denso (rutina) a tamaño min y default ──────────────────
def _s_rutina_min(app):
    _resize(app, 600, 520)
    _nav(app, "rutina")
    _cap(app, "dark_rutina_min")

def _s_rutina_md(app):
    _resize(app, 860, 640)
    _nav(app, "rutina")
    _cap(app, "dark_rutina_md")

def _s_avisos_min(app):
    _resize(app, 600, 520)
    _nav(app, "avisos")
    _cap(app, "dark_avisos_min")

def _s_avisos_md(app):
    _resize(app, 860, 640)
    _nav(app, "avisos")
    _cap(app, "dark_avisos_md")

def _s_actividades_min(app):
    _resize(app, 600, 520)
    _nav(app, "actividades")
    _cap(app, "dark_actividades_min")

steps += [
    (0, _s_rutina_min, "dark_rutina_min"),
    (0, _s_rutina_md, "dark_rutina_md"),
    (0, _s_avisos_min, "dark_avisos_min"),
    (0, _s_avisos_md, "dark_avisos_md"),
    (0, _s_actividades_min, "dark_actividades_min"),
]

# ── Light mode ────────────────────────────────────────────────────────────────

def _s_light_home(app):
    _resize(app, 860, 640)
    _go_home(app)
    _set_theme(app, "light_hybrid")
    _cap(app, "light_home")

def _s_light_rutina(app):
    _nav(app, "rutina")
    _cap(app, "light_rutina")

def _s_light_avisos(app):
    _nav(app, "avisos")
    _cap(app, "light_avisos")

def _s_light_animo(app):
    _nav(app, "animo")
    _cap(app, "light_animo")

def _s_light_home_final(app):
    _go_home(app)
    _cap(app, "light_home_final")

def _s_dark_restore(app):
    _set_theme(app, "dark_hybrid")
    _go_home(app)
    _cap(app, "dark_restored")

steps += [
    (200, _s_light_home,       "light_home"),
    (200, _s_light_rutina,     "light_rutina"),
    (200, _s_light_avisos,     "light_avisos"),
    (200, _s_light_animo,      "light_animo"),
    (200, _s_light_home_final, "light_home_final"),
    (200, _s_dark_restore,     "dark_restored"),
]

# ── Scrollbar check: módulo con mucho contenido a tamaño mínimo ───────────────

def _s_scroll_check(app):
    _resize(app, 620, 480)
    _set_theme(app, "dark_hybrid")
    _nav(app, "actividades")
    _cap(app, "dark_scrollbar_actividades")

def _s_scroll_check2(app):
    _nav(app, "rutina")
    _cap(app, "dark_scrollbar_rutina")

steps += [
    (200, _s_scroll_check,  "dark_scrollbar_actividades"),
    (200, _s_scroll_check2, "dark_scrollbar_rutina"),
]


# ── Runner ────────────────────────────────────────────────────────────────────

def _run(i):
    if i >= len(steps):
        print(f"\n=== {len(steps)} capturas completadas ===")
        print(f"  {OUT}")
        QTimer.singleShot(200, patient.close)
        return
    delay, fn, label = steps[i]
    delay = max(delay, 350)
    print(f"  [{i+1}/{len(steps)}] {label}", flush=True)
    QTimer.singleShot(delay, lambda idx=i: _do_step(idx))


def _do_step(i):
    _, fn, _ = steps[i]
    fn(patient)
    _run(i + 1)


QTimer.singleShot(2000, lambda: _run(0))
sys.exit(app.exec())
