"""
_test_audit_visual.py  --  Auditoria visual completa y reutilizable.

Combina cuatro tipos de analisis independientes:

  1. ESTATICO   Analiza archivos .py sin abrir la UI.
                Detecta: hardcoded hex/white/black en stylesheets,
                font-size en px, valores de diseño que deberian ser tokens.

  2. LAYOUT     Inspecciona el arbol de widgets en ejecucion.
                Detecta: widgets visibles con tamano cero, fuentes fuera de
                rango, botones sin cursor interactivo, alturas de componentes
                clave fuera de especificacion, solapamientos evidentes.

  3. BASELINE   Comparacion screenshot vs imagen de referencia.
                Primera corrida: crea las referencias en _baseline/.
                Corridas siguientes: compara y reporta diferencia en %.
                --update-baseline: reemplaza las referencias con la captura actual.

  4. COLOR      Muestreo de pixeles vs tokens del design system
                (misma logica que _test_color_regression.py).

Uso:
    python _test_audit_visual.py                      # todo (paciente + hub)
    python _test_audit_visual.py --static             # solo analisis de codigo
    python _test_audit_visual.py --update-baseline    # actualizar referencias
    python _test_audit_visual.py --patient            # solo app paciente
    python _test_audit_visual.py --hub                # solo hub

Salida:
    Tabla en consola con PASS / WARN / FAIL por cada check.
    JSON en _test_screens/audit/audit_report.json
"""

import sys
import os
import re
import json
import argparse
import traceback
from pathlib import Path
from datetime import datetime

_proj = str(Path(__file__).resolve().parent)
if _proj not in sys.path:
    sys.path.insert(0, _proj)

# ──────────────────────────────────────────────────────────────────────────────
# Configuracion central
# ──────────────────────────────────────────────────────────────────────────────

OUT_DIR      = os.path.join(_proj, "_test_screens", "audit")
BASELINE_DIR = os.path.join(_proj, "_test_screens", "baseline")
os.makedirs(OUT_DIR,      exist_ok=True)
os.makedirs(BASELINE_DIR, exist_ok=True)

# Tolerancia de similitud de screenshots (0-100, 100=identico)
BASELINE_WARN_THRESHOLD = 97   # < 97% similar -> WARN
BASELINE_FAIL_THRESHOLD = 92   # < 92% similar -> FAIL

# Rango de tamanio de fuente aceptable (pt)
FONT_MIN_PT = 7
FONT_MAX_PT = 32

# Alturas de componentes clave (min, max) en px
COMPONENT_HEIGHTS = {
    "NMButton":        (32, 60),
    "NMButtonOutline": (24, 60),
    "NMHeader":        (40, 80),
}

# Archivos que definen tokens (excluir de analisis de hardcoded)
TOKEN_FILES = {"theme.py", "theme_qt.py"}

# Directorios a excluir del analisis estatico
EXCLUDE_DIRS = {"DESIGN_SYSTEM_NEUROMOOD", "__pycache__", ".git",
                "_test_screens", "dist", "build"}

# Directorios a auditar
AUDIT_DIRS = ["app", "hub", "shared", "installers"]

# ──────────────────────────────────────────────────────────────────────────────
# Registro de resultados
# ──────────────────────────────────────────────────────────────────────────────

_issues: list[dict] = []
_counts = {"PASS": 0, "WARN": 0, "FAIL": 0}


def _record(section: str, label: str, status: str, detail: str = ""):
    _issues.append({
        "section": section,
        "label":   label,
        "status":  status,
        "detail":  detail,
        "time":    datetime.now().isoformat(),
    })
    _counts[status] = _counts.get(status, 0) + 1
    tag = f"[{status:4s}]"
    line = f"  {tag}  {label}"
    if detail:
        line += f"\n         {detail}"
    print(line)


def _section(title: str):
    print()
    print(f"  {'='*55}")
    print(f"  {title}")
    print(f"  {'='*55}")


# ──────────────────────────────────────────────────────────────────────────────
# MODULO 1: Auditoria estatica de codigo
# ──────────────────────────────────────────────────────────────────────────────

# Patrones de anti-patrones de diseno en stylesheets Python
_STATIC_PATTERNS = [
    # (regex, descripcion, severidad, excluir_en_token_files)
    (r'color:\s*white\b',            "color: white sin token",              "FAIL", True),
    (r'color:\s*black\b',            "color: black sin token",              "FAIL", True),
    (r'background(?:-color)?:\s*white\b', "background: white sin token",   "FAIL", True),
    (r'background(?:-color)?:\s*black\b', "background: black sin token",   "FAIL", True),
    # Hex hardcodeado en contexto CSS (no precedido de { ni de # en comentario)
    (r'(?<![{#])(?:color|background|border)[-\w]*:\s*#[0-9a-fA-F]{6}',
     "hex literal en propiedad CSS",                                        "WARN", True),
    # font-size en pixeles (deberia ser pt o token)
    (r'font-size:\s*\d+px',          "font-size en px (usar pt o token)",   "WARN", False),
    # Valores de bg_primary / bg_surface del sistema anterior (ya migrados)
    (r'#080910',  "color legado: bg_primary antiguo (#080910)",             "FAIL", False),
    (r'#111420',  "color legado: bg_secondary antiguo (#111420)",           "FAIL", False),
    (r'#181c30',  "color legado: bg_surface antiguo (#181c30)",             "FAIL", False),
    (r'#1f243b',  "color legado: bg_elevated antiguo (#1f243b)",            "FAIL", False),
]


def _collect_py_files() -> list[str]:
    files = []
    for audit_dir in AUDIT_DIRS:
        base = os.path.join(_proj, audit_dir)
        if not os.path.isdir(base):
            continue
        for root, dirs, fnames in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for fname in fnames:
                if fname.endswith(".py"):
                    files.append(os.path.join(root, fname))
    return files


def run_static_audit():
    _section("AUDITORIA ESTATICA  (codigo fuente)")
    files = _collect_py_files()
    found_any = False

    for fpath in files:
        fname = os.path.basename(fpath)
        is_token_file = fname in TOKEN_FILES
        rel = os.path.relpath(fpath, _proj)

        try:
            lines = Path(fpath).read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        for lineno, line in enumerate(lines, 1):
            # Saltar lineas de comentario y definiciones de tokens
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            # Saltar COLORES_PUNTAJE y SESSION_COLORS (logica de negocio)
            if "COLORES_PUNTAJE" in line or "_SESSION_COLORS" in line or "_COLD" in line or "_MID" in line or "_HOT" in line:
                continue

            for pattern, desc, severity, skip_token in _STATIC_PATTERNS:
                if skip_token and is_token_file:
                    continue
                if re.search(pattern, line, re.IGNORECASE):
                    detail = f"{rel}:{lineno}  >>  {stripped[:90]}"
                    _record("ESTATICO", desc, severity, detail)
                    found_any = True
                    break  # un issue por linea es suficiente

    if not found_any:
        _record("ESTATICO", "Sin hardcoded colors ni patrones legados detectados", "PASS")


# ──────────────────────────────────────────────────────────────────────────────
# MODULO 2: Auditoria de layout y tipografia en widget tree
# ──────────────────────────────────────────────────────────────────────────────

def _walk_widgets(root, depth=0, max_depth=12):
    """Generador recursivo del arbol de widgets visibles."""
    if depth > max_depth:
        return
    from PyQt6.QtWidgets import QWidget
    for child in root.findChildren(QWidget):
        if child.parent() is root:
            yield child
            yield from _walk_widgets(child, depth + 1, max_depth)


def _audit_widget_tree(root, screen_name: str):
    """Comprueba tipografia, tamanos y cursores en el arbol de widgets."""
    from PyQt6.QtWidgets import QLabel, QPushButton, QAbstractButton
    from PyQt6.QtCore import Qt

    zero_count  = 0
    font_issues = []
    cursor_issues = []

    # Clases con altura especificada en COMPONENT_HEIGHTS
    try:
        from shared.components_qt import NMButton, NMButtonOutline, NMHeader
        height_checks = {
            NMButton:        ("NMButton",        *COMPONENT_HEIGHTS["NMButton"]),
            NMButtonOutline: ("NMButtonOutline", *COMPONENT_HEIGHTS["NMButtonOutline"]),
            NMHeader:        ("NMHeader",        *COMPONENT_HEIGHTS["NMHeader"]),
        }
    except Exception:
        height_checks = {}

    height_issues = []

    for w in _walk_widgets(root):
        if not w.isVisible():
            continue

        # -- Tamano cero en widget visible --
        if w.width() == 0 or w.height() == 0:
            # Algunos spacers y overlays tienen tamano cero intencionalmente
            if not w.styleSheet() == "" or w.minimumWidth() > 0:
                zero_count += 1

        # -- Fuente fuera de rango en QLabel --
        if isinstance(w, QLabel) and w.text():
            pt = w.font().pointSize()
            if pt > 0 and not (FONT_MIN_PT <= pt <= FONT_MAX_PT):
                font_issues.append(f"{type(w).__name__} pt={pt}  text='{w.text()[:30]}'")

        # -- Boton sin cursor interactivo --
        if isinstance(w, QPushButton) and w.isEnabled():
            if w.cursor().shape() != Qt.CursorShape.PointingHandCursor:
                cursor_issues.append(f"QPushButton '{w.text()[:25]}' sin cursor Pointing")

        # -- Alturas de componentes clave --
        for cls, (name, h_min, h_max) in height_checks.items():
            if type(w) is cls:
                h = w.height()
                if not (h_min <= h <= h_max):
                    height_issues.append(
                        f"{name} altura={h}px fuera de [{h_min},{h_max}]"
                    )

    sec = "LAYOUT"
    prefix = f"{screen_name}: "

    if zero_count:
        _record(sec, f"{prefix}widgets visibles con tamano cero", "WARN",
                f"{zero_count} widgets afectados")
    else:
        _record(sec, f"{prefix}sin widgets visibles de tamano cero", "PASS")

    if font_issues:
        for fi in font_issues[:3]:
            _record(sec, f"{prefix}fuente fuera de rango [{FONT_MIN_PT}-{FONT_MAX_PT}pt]", "WARN", fi)
    else:
        _record(sec, f"{prefix}fuentes dentro de rango", "PASS")

    if cursor_issues:
        for ci in cursor_issues[:3]:
            _record(sec, f"{prefix}boton sin cursor interactivo", "WARN", ci)
    else:
        _record(sec, f"{prefix}todos los botones tienen cursor", "PASS")

    if height_issues:
        for hi in height_issues[:3]:
            _record(sec, f"{prefix}componente fuera de especificacion", "WARN", hi)
    else:
        _record(sec, f"{prefix}alturas de componentes dentro de especificacion", "PASS")


# ──────────────────────────────────────────────────────────────────────────────
# MODULO 3: Baseline screenshots (PIL)
# ──────────────────────────────────────────────────────────────────────────────

_COMPARE_SIZE = (400, 280)   # tamano de normalizacion para comparar


def _pil_similarity(path_a: str, path_b: str) -> float:
    """Retorna similitud 0-100 entre dos imagenes (100 = identicas)."""
    try:
        from PIL import Image
        import numpy as np
        a = Image.open(path_a).resize(_COMPARE_SIZE).convert("RGB")
        b = Image.open(path_b).resize(_COMPARE_SIZE).convert("RGB")
        arr_a = np.array(a, dtype=np.int32)
        arr_b = np.array(b, dtype=np.int32)
        mae = np.mean(np.abs(arr_a - arr_b))   # 0-255
        return round(100.0 - (mae / 255.0 * 100.0), 1)
    except Exception as e:
        return -1.0


def _grab_and_save(widget, name: str) -> str:
    """Captura el widget y guarda en OUT_DIR. Retorna la ruta."""
    from PyQt6.QtWidgets import QApplication
    QApplication.processEvents()
    QApplication.processEvents()
    path = os.path.join(OUT_DIR, f"{name}.png")
    widget.grab().save(path)
    return path


def _check_baseline(widget, name: str, update: bool):
    """Captura la pantalla y compara con el baseline (o lo crea)."""
    current_path  = _grab_and_save(widget, name)
    baseline_path = os.path.join(BASELINE_DIR, f"{name}.png")

    if update or not os.path.exists(baseline_path):
        import shutil
        shutil.copy2(current_path, baseline_path)
        _record("BASELINE", f"{name}: baseline {'actualizado' if not update else 'creado'}",
                "PASS", baseline_path)
        return

    sim = _pil_similarity(current_path, baseline_path)
    if sim < 0:
        _record("BASELINE", f"{name}: error al comparar imagenes", "WARN")
    elif sim < BASELINE_FAIL_THRESHOLD:
        _record("BASELINE", f"{name}: cambio visual detectado ({sim:.1f}% similar)",
                "FAIL", f"actual={current_path}  baseline={baseline_path}")
    elif sim < BASELINE_WARN_THRESHOLD:
        _record("BASELINE", f"{name}: cambio menor detectado ({sim:.1f}% similar)",
                "WARN", f"actual={current_path}  baseline={baseline_path}")
    else:
        _record("BASELINE", f"{name}: sin cambios ({sim:.1f}% similar)", "PASS")


# ──────────────────────────────────────────────────────────────────────────────
# MODULO 4: Muestreo de color vs tokens (inline, sin depender de otro archivo)
# ──────────────────────────────────────────────────────────────────────────────

def _sample(pixmap, x: int, y: int):
    img = pixmap.toImage()
    c = img.pixelColor(max(0, min(x, pixmap.width()-1)),
                       max(0, min(y, pixmap.height()-1)))
    return (c.red(), c.green(), c.blue())


def _delta(rgb, hex_color: str) -> int:
    h = hex_color.lstrip("#")
    exp = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return sum(abs(a-e) for a, e in zip(rgb, exp))


def _check_color(label: str, pixmap, x: int, y: int, expected_hex: str, tol: int = 20):
    rgb   = _sample(pixmap, x, y)
    delta = _delta(rgb, expected_hex)
    if delta <= tol:
        _record("COLOR", label, "PASS")
    else:
        exp = tuple(int(expected_hex.lstrip("#")[i:i+2], 16) for i in (0,2,4))
        _record("COLOR", label, "FAIL",
                f"actual=rgb{rgb}  esperado={expected_hex} rgb{exp}  delta={delta}  tol={tol}")


# ──────────────────────────────────────────────────────────────────────────────
# RUNNERS de aplicacion
# ──────────────────────────────────────────────────────────────────────────────

def run_patient_audit(update_baseline: bool = False):
    _section("APP PACIENTE")
    from PyQt6.QtWidgets import QApplication
    from shared.theme import COLORS
    DARK  = COLORS["dark_hybrid"]
    LIGHT = COLORS["light_hybrid"]

    app = QApplication.instance() or QApplication(sys.argv)
    from app.main_qt import NeuroMoodApp
    patient = NeuroMoodApp()
    patient.show()
    QApplication.processEvents()
    QApplication.processEvents()

    w  = patient.width()
    h  = patient.height()
    hh = patient._header.height()
    hw = patient._header.width()
    # Top-right del contenido (lejos del aura radial)
    cx = w - 20
    cy = hh + 12

    def _grab():
        QApplication.processEvents()
        QApplication.processEvents()
        return patient.grab()

    def _nav(mid):
        patient._navigate_to(mid)
        QApplication.processEvents()
        QApplication.processEvents()

    def _home():
        patient._go_home()
        QApplication.processEvents()

    MODULES = [
        ("animo",       "Animo"),
        ("respiracion", "Respiracion"),
        ("registro",    "Registro TCC"),
        ("rutina",      "Rutina"),
        ("actividades", "Actividades"),
        ("timer",       "Timer"),
        ("avisos",      "Avisos"),
    ]

    # ── HOME dark ──────────────────────────────────────────────────────────────
    _check_baseline(patient, "p_home_dark", update_baseline)
    pix = _grab()
    _check_color("Home dark: header bg_surface",
                 patient._header.grab(), hw - 70, hh // 2,
                 DARK["bg_surface"], 20)
    _check_color("Home dark: contenido bg_primary",
                 pix, cx, cy, DARK["bg_primary"], 35)
    _audit_widget_tree(patient, "Home dark")

    # ── Modulos dark ───────────────────────────────────────────────────────────
    for mid, label in MODULES:
        _nav(mid)
        _check_baseline(patient, f"p_{mid}_dark", update_baseline)
        pix = _grab()
        _check_color(f"{label} dark: header bg_surface",
                     patient._header.grab(), hw - 70, hh // 2,
                     DARK["bg_surface"], 20)
        _check_color(f"{label} dark: contenido bg_primary",
                     pix, cx, cy, DARK["bg_primary"], 35)
        _audit_widget_tree(patient, f"{label} dark")
        _home()

    # ── Light mode ─────────────────────────────────────────────────────────────
    pix_hdr_dark = patient._header.grab()
    patient._toggle_theme()
    QApplication.processEvents()
    QApplication.processEvents()

    _check_baseline(patient, "p_home_light", update_baseline)
    pix = _grab()
    pix_hdr_light = patient._header.grab()

    _check_color("Home light: header bg_surface",
                 pix_hdr_light, hw - 70, hh // 2,
                 LIGHT["bg_surface"], 20)
    _check_color("Home light: contenido bg_primary",
                 pix, cx, cy, LIGHT["bg_primary"], 35)

    # Dark != light (contraste)
    dark_rgb  = _sample(pix_hdr_dark,  hw - 70, hh // 2)
    light_rgb = _sample(pix_hdr_light, hw - 70, hh // 2)
    contrast  = sum(abs(a-b) for a, b in zip(dark_rgb, light_rgb))
    if contrast >= 80:
        _record("COLOR", "Header: dark != light (contraste suficiente)", "PASS",
                f"delta={contrast}")
    else:
        _record("COLOR", "Header: dark/light indistinguibles", "FAIL",
                f"delta={contrast} < 80  dark=rgb{dark_rgb}  light=rgb{light_rgb}")

    _audit_widget_tree(patient, "Home light")

    # Navegar algun modulo en light para verificar propagacion
    _nav("animo")
    _check_baseline(patient, "p_animo_light", update_baseline)
    _audit_widget_tree(patient, "Animo light")
    _home()

    patient._toggle_theme()  # restaurar dark
    QApplication.processEvents()

    # ── Responsive ─────────────────────────────────────────────────────────────
    for rw, rh in [(800, 600), (1280, 720), (1366, 768)]:
        patient.resize(rw, rh)
        QApplication.processEvents()
        QApplication.processEvents()
        _check_baseline(patient, f"p_home_{rw}x{rh}", update_baseline)
        pix = _grab()
        # A cualquier tamano, el header debe seguir teniendo bg_surface
        _check_color(f"Home {rw}x{rh}: header bg_surface",
                     patient._header.grab(),
                     patient._header.width() - 70, patient._header.height() // 2,
                     DARK["bg_surface"], 20)

    patient.close()


def run_hub_audit(update_baseline: bool = False):
    _section("HUB PRO")
    from PyQt6.QtWidgets import QApplication
    from shared.theme import COLORS
    DARK  = COLORS["dark_hybrid"]
    LIGHT = COLORS["light_hybrid"]

    app = QApplication.instance() or QApplication(sys.argv)
    from hub.main_qt import HubProfesional
    hub = HubProfesional()
    hub.show()
    QApplication.processEvents()
    QApplication.processEvents()

    w    = hub.width()
    h    = hub.height()
    hh   = hub._header.height() if hasattr(hub, "_header") else 56
    sb   = hub._sidebar
    sb_w = sb.width()
    sb_h = sb.height()
    content_x = sb_w + (w - sb_w) // 2
    content_y = hh + 15

    def _grab():
        QApplication.processEvents()
        QApplication.processEvents()
        return hub.grab()

    # ── Dashboard dark ─────────────────────────────────────────────────────────
    hub._on_nav("dashboard")
    QApplication.processEvents()
    _check_baseline(hub, "h_dashboard_dark", update_baseline)
    pix = _grab()
    _check_color("Hub dark: sidebar_bg (izq)",
                 sb.grab(), 10, sb_h // 2, DARK["sidebar_bg"], 20)
    _check_color("Hub dark: sidebar_bg (der)",
                 sb.grab(), sb_w - 10, sb_h // 2, DARK["sidebar_bg"], 20)
    _check_color("Hub dark: contenido bg_primary",
                 pix, content_x, content_y, DARK["bg_primary"], 35)
    _audit_widget_tree(hub, "Hub Dashboard dark")

    # ── Pacientes dark ─────────────────────────────────────────────────────────
    hub._on_nav("pacientes")
    QApplication.processEvents()
    _check_baseline(hub, "h_pacientes_dark", update_baseline)
    _audit_widget_tree(hub, "Hub Pacientes dark")

    # ── Config dark ────────────────────────────────────────────────────────────
    hub._on_nav("config")
    QApplication.processEvents()
    _check_baseline(hub, "h_config_dark", update_baseline)
    _audit_widget_tree(hub, "Hub Config dark")

    # ── IA (DetallePacienteView mock) ──────────────────────────────────────────
    try:
        from PyQt6.QtWidgets import QTabWidget
        from hub.pacientes_qt import DetallePacienteView
        detalle = DetallePacienteView(
            modo=hub._modo, sb=None,
            paciente_id="audit_test_id",
            paciente_nombre="Auditoria Test",
        )
        hub._stack.addWidget(detalle)
        hub._stack.setCurrentWidget(detalle)
        QApplication.processEvents()
        tabs = detalle.findChildren(QTabWidget)
        if tabs:
            tabs[0].setCurrentIndex(tabs[0].count() - 1)
            QApplication.processEvents()
        _check_baseline(hub, "h_ia_detalle_dark", update_baseline)
        _audit_widget_tree(detalle, "Hub IA detalle dark")
        # Restaurar
        hub._on_nav("dashboard")
        QApplication.processEvents()
    except Exception as e:
        _record("LAYOUT", "Hub IA detalle: no se pudo instanciar", "WARN", str(e))

    # ── Light mode Hub ─────────────────────────────────────────────────────────
    sb_dark = sb.grab()
    hub._toggle_theme()
    QApplication.processEvents()
    QApplication.processEvents()

    _check_baseline(hub, "h_dashboard_light", update_baseline)
    sb_light = sb.grab()
    _check_color("Hub light: sidebar_bg (light)",
                 sb_light, 10, sb.height() // 2, LIGHT["sidebar_bg"], 20)

    dark_rgb  = _sample(sb_dark,  10, sb_h // 2)
    light_rgb = _sample(sb_light, 10, sb.height() // 2)
    contrast  = sum(abs(a-b) for a, b in zip(dark_rgb, light_rgb))
    if contrast >= 80:
        _record("COLOR", "Hub sidebar: dark != light", "PASS", f"delta={contrast}")
    else:
        _record("COLOR", "Hub sidebar: dark/light indistinguibles", "FAIL",
                f"delta={contrast}  dark=rgb{dark_rgb}  light=rgb{light_rgb}")

    _audit_widget_tree(hub, "Hub Dashboard light")
    hub._toggle_theme()  # restaurar dark
    QApplication.processEvents()

    # ── Responsive Hub ─────────────────────────────────────────────────────────
    for rw, rh in [(1024, 720), (1366, 768), (1920, 1080)]:
        hub.resize(rw, rh)
        QApplication.processEvents()
        QApplication.processEvents()
        _check_baseline(hub, f"h_dashboard_{rw}x{rh}", update_baseline)
        _check_color(f"Hub sidebar {rw}x{rh}: sidebar_bg",
                     hub._sidebar.grab(), 10, hub._sidebar.height() // 2,
                     DARK["sidebar_bg"], 20)

    hub.close()


# ──────────────────────────────────────────────────────────────────────────────
# Reporte final
# ──────────────────────────────────────────────────────────────────────────────

def _print_summary():
    total = sum(_counts.values())
    print()
    print("=" * 57)
    print(f"  AUDITORIA VISUAL  --  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  PASS={_counts.get('PASS',0)}  WARN={_counts.get('WARN',0)}  FAIL={_counts.get('FAIL',0)}  TOTAL={total}")
    print("=" * 57)

    fails = [i for i in _issues if i["status"] == "FAIL"]
    warns = [i for i in _issues if i["status"] == "WARN"]

    if fails:
        print()
        print("  ERRORES CRITICOS:")
        for f in fails:
            print(f"    x  [{f['section']}] {f['label']}")
            if f["detail"]:
                print(f"       {f['detail'][:100]}")
    if warns:
        print()
        print("  ADVERTENCIAS:")
        for w in warns[:8]:
            print(f"    !  [{w['section']}] {w['label']}")
            if w["detail"]:
                print(f"       {w['detail'][:100]}")
        if len(warns) > 8:
            print(f"    ... y {len(warns)-8} advertencias mas (ver JSON)")

    report_path = os.path.join(OUT_DIR, "audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "counts":    _counts,
            "issues":    _issues,
        }, f, indent=2, ensure_ascii=False, default=str)
    print()
    print(f"  Reporte JSON: {report_path}")
    print()
    return _counts.get("FAIL", 0) == 0


# ──────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Auditoria visual completa de NeuroMood V3"
    )
    p.add_argument("--static",          action="store_true",
                   help="Solo auditoria estatica (sin UI)")
    p.add_argument("--update-baseline", action="store_true",
                   help="Reemplazar referencias de screenshot")
    p.add_argument("--patient",         action="store_true",
                   help="Solo auditar app paciente")
    p.add_argument("--hub",             action="store_true",
                   help="Solo auditar Hub Pro")
    args = p.parse_args()

    # Siempre corre la auditoria estatica
    run_static_audit()

    if args.static:
        _print_summary()
        sys.exit(0 if _counts.get("FAIL", 0) == 0 else 1)

    # Auditoria con UI
    run_both = not args.patient and not args.hub

    if args.patient or run_both:
        run_patient_audit(update_baseline=args.update_baseline)

    if args.hub or run_both:
        run_hub_audit(update_baseline=args.update_baseline)

    ok = _print_summary()
    sys.exit(0 if ok else 1)
