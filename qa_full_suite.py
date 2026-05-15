"""
qa_full_suite.py — Suite completa de QA automatizado para NeuroMood V3.

Cubre:
  1. COMPILE   python -m compileall en app/ hub/ shared/ installers/
  2. PATIENT   Abre Suite, navega 7 módulos, toggle tema, resize 3 resoluciones
  3. HUB       Abre Hub, navega 4 vistas, sidebar toggle, tema, resize 3 resoluciones
  4. INSTALLER Instancia UI de los 4 installers/uninstallers, navega páginas seguras
  5. REPORT    Genera QA_REPORT.md con resultados, bugs y screenshots

Detección automática de:
  - Crashes / excepciones con traceback completo
  - Widgets visibles con tamaño cero (rotos)
  - Widgets recortados fuera de su padre (overflow)
  - Errores de tema (dark == light sin diferencia)
  - Errores de layout en resize

Uso:
    python qa_full_suite.py               # todo
    python qa_full_suite.py --patient     # solo Suite
    python qa_full_suite.py --hub         # solo Hub
    python qa_full_suite.py --installers  # solo installers UI
    python qa_full_suite.py --compile     # solo sintaxis
"""

import sys, os, re, json, time, shutil, traceback, subprocess, argparse
from pathlib import Path
from datetime import datetime

# Forzar UTF-8 en stdout para evitar UnicodeEncodeError en Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_proj = str(Path(__file__).resolve().parent)
if _proj not in sys.path:
    sys.path.insert(0, _proj)

# ── Directorios de salida ──────────────────────────────────────────────────────
SCREENS_DIR = os.path.join(_proj, "_test_screens", "qa")
os.makedirs(SCREENS_DIR, exist_ok=True)

# ── Registro central ──────────────────────────────────────────────────────────

class QAReport:
    def __init__(self):
        self.ts   = datetime.now()
        self.bugs:    list[dict] = []   # crashes + logic bugs
        self.warns:   list[dict] = []   # widgets zero-size, clipping leve
        self.passes:  list[dict] = []
        self.screenshots: list[str] = []

    def bug(self, section, label, detail="", screenshot=None):
        entry = {"section": section, "label": label, "detail": detail}
        if screenshot:
            entry["screenshot"] = screenshot
        self.bugs.append(entry)
        print(f"  [BUG ] {label}")
        if detail:
            for line in detail.strip().splitlines()[:6]:
                print(f"         {line}")

    def warn(self, section, label, detail=""):
        self.warns.append({"section": section, "label": label, "detail": detail})
        print(f"  [WARN] {label}")
        if detail:
            print(f"         {detail[:120]}")

    def ok(self, section, label):
        self.passes.append({"section": section, "label": label})
        print(f"  [PASS] {label}")

    def step(self, label):
        print(f"\n  -- {label}")

    def section(self, title):
        print()
        print(f"  {'='*60}")
        print(f"  {title}")
        print(f"  {'='*60}")

    # ── Generar QA_REPORT.md ──────────────────────────────────────────────────
    def save_markdown(self):
        ts_str = self.ts.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENS_DIR, f"qa_report_{ts_str}.md")
        lines = []
        lines += [
            f"# QA Report — NeuroMood V3",
            f"",
            f"**Fecha**: {self.ts.strftime('%Y-%m-%d %H:%M')}  ",
            f"**Bugs críticos**: {len(self.bugs)}  ",
            f"**Advertencias**: {len(self.warns)}  ",
            f"**Checks OK**: {len(self.passes)}  ",
            f"",
            f"---",
            f"",
        ]

        if self.bugs:
            lines += ["## Bugs (crashes / lógica)", ""]
            for i, b in enumerate(self.bugs, 1):
                lines += [
                    f"### BUG {i:02d} — {b['label']}",
                    f"",
                    f"**Sección**: {b['section']}  ",
                ]
                if b.get("screenshot"):
                    rel = os.path.relpath(b["screenshot"], _proj).replace("\\", "/")
                    lines.append(f"**Screenshot**: [{rel}]({rel})  ")
                if b.get("detail"):
                    lines += ["", "```", b["detail"][:800], "```", ""]
                else:
                    lines.append("")
        else:
            lines += ["## Bugs\n\nNingún crash ni bug de lógica detectado.\n"]

        if self.warns:
            lines += ["## Advertencias", ""]
            for w in self.warns:
                lines += [
                    f"- **[{w['section']}]** {w['label']}",
                ]
                if w.get("detail"):
                    lines.append(f"  > {w['detail'][:200]}")
            lines.append("")

        lines += [
            "## Checks OK", "",
            f"Total: {len(self.passes)} checks pasaron sin incidentes.",
            "",
            "---",
            "",
            "## Screenshots", "",
        ]
        for s in self.screenshots:
            rel = os.path.relpath(s, _proj).replace("\\", "/")
            lines.append(f"- [{os.path.basename(s)}]({rel})")

        lines += [
            "",
            "---",
            "",
            "## Archivos modificados",
            "",
            "_Completar manualmente después de aplicar fixes._",
            "",
            "## Pendiente",
            "",
            "_Completar manualmente._",
        ]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n  Reporte guardado en: {path}")
        return path


_report = QAReport()


# ── Helpers PyQt6 ────────────────────────────────────────────────────────────

def _cap(widget, name: str) -> str:
    """Captura el widget y guarda PNG. Devuelve la ruta."""
    try:
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        QApplication.processEvents()
        path = os.path.join(SCREENS_DIR, f"{name}.png")
        widget.grab().save(path)
        _report.screenshots.append(path)
        return path
    except Exception:
        return ""


def _proc():
    try:
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        QApplication.processEvents()
    except Exception:
        pass


def _click(w):
    try:
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication
        rc = w.rect()
        c = QPointF(rc.center())
        g = QPointF(w.mapTo(w.window(), rc.center()))
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
        return True
    except Exception as e:
        return False


def _in_scrollarea(widget) -> bool:
    """Devuelve True si el widget está dentro de un QScrollArea (contenido scrolleable)."""
    from PyQt6.QtWidgets import QScrollArea, QAbstractScrollArea
    p = widget.parent()
    while p is not None:
        if isinstance(p, (QScrollArea, QAbstractScrollArea)):
            return True
        p = p.parent()
    return False


def _detect_issues(root, section: str):
    """Detecta widgets visibles con tamaño 0 o desbordando su padre."""
    try:
        from PyQt6.QtWidgets import QWidget, QApplication
        QApplication.processEvents()
        zero, clipped = [], []
        for w in root.findChildren(QWidget):
            if not w.isVisible():
                continue
            if w.width() == 0 or w.height() == 0:
                zero.append(type(w).__name__)
            # Clipping: ¿el widget sale fuera de la ventana principal?
            # Excluir widgets dentro de QScrollArea (contenido scrolleable es normal)
            if _in_scrollarea(w):
                continue
            gr = w.mapTo(root, w.rect().topLeft())
            if (gr.x() + w.width() < 0 or gr.y() + w.height() < 0 or
                    gr.x() > root.width() or gr.y() > root.height()):
                clipped.append(type(w).__name__)
        if zero:
            _report.warn(section, f"Widgets visibles con tamaño 0: {len(zero)}",
                         ", ".join(zero[:8]))
        else:
            _report.ok(section, "Sin widgets de tamaño cero")
        if clipped:
            _report.warn(section, f"Widgets recortados fuera de ventana: {len(clipped)}",
                         ", ".join(clipped[:8]))
        else:
            _report.ok(section, "Sin desbordamiento de widgets")
    except Exception as e:
        _report.warn(section, f"No se pudo analizar widget tree: {e}")


# ── FASE 1: compileall ────────────────────────────────────────────────────────

def run_compile_check():
    _report.section("FASE 1 — Verificación de sintaxis (compileall)")
    targets = ["app", "hub", "shared", "installers"]
    errors = []
    for tgt in targets:
        path = os.path.join(_proj, tgt)
        if not os.path.isdir(path):
            continue
        result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", path],
            capture_output=True, text=True, cwd=_proj
        )
        if result.returncode != 0:
            errors.append(f"{tgt}/: {result.stderr.strip()[:400]}")
            _report.bug("COMPILE", f"Errores de sintaxis en {tgt}/",
                        result.stderr.strip()[:400])
        else:
            _report.ok("COMPILE", f"Sintaxis OK: {tgt}/")
    if not errors:
        _report.ok("COMPILE", "Todos los archivos compilan sin errores")


# ── FASE 2: App paciente ──────────────────────────────────────────────────────

MODULE_IDS = ["animo", "respiracion", "registro", "rutina", "actividades", "timer", "avisos"]

def run_patient_qa():
    _report.section("FASE 2 — App Paciente (NeuroMood Suite)")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    # ── Abrir ────────────────────────────────────────────────────────────────
    _report.step("Inicializar NeuroMoodApp")
    try:
        from app.main_qt import NeuroMoodApp
        patient = NeuroMoodApp()
        patient.show()
        _proc()
        _proc()
        _report.ok("PATIENT", "NeuroMoodApp abrió sin crash")
    except Exception:
        tb = traceback.format_exc()
        _report.bug("PATIENT", "NeuroMoodApp no pudo abrirse", tb)
        return

    scr = _cap(patient, "p00_home_dark")

    # ── Verificar dimensiones ─────────────────────────────────────────────────
    if patient.width() < 100 or patient.height() < 100:
        _report.bug("PATIENT", f"Ventana con dimensiones anómalas: {patient.width()}x{patient.height()}")
    else:
        _report.ok("PATIENT", f"Dimensiones OK: {patient.width()}x{patient.height()}")

    _detect_issues(patient, "PATIENT Home dark")

    # ── Navegar cada módulo ───────────────────────────────────────────────────
    _report.step("Navegar 7 módulos en dark mode")
    for mid in MODULE_IDS:
        try:
            patient._navigate_to(mid)
            _proc()
            _proc()
            scr = _cap(patient, f"p01_{mid}_dark")
            _report.ok("PATIENT", f"Módulo '{mid}' abrió sin crash")
            _detect_issues(patient, f"PATIENT {mid} dark")
            patient._go_home()
            _proc()
        except Exception:
            tb = traceback.format_exc()
            scr = _cap(patient, f"p01_{mid}_crash")
            _report.bug("PATIENT", f"Crash en módulo '{mid}'", tb, scr)

    # ── Toggle tema ───────────────────────────────────────────────────────────
    _report.step("Toggle dark → light → dark")
    try:
        patient._toggle_theme()
        _proc(); _proc()
        scr = _cap(patient, "p02_home_light")
        _report.ok("PATIENT", "Toggle light mode sin crash")
        _detect_issues(patient, "PATIENT Home light")

        # Verificar contraste header dark≠light
        try:
            hdr = patient._header
            pix_l = hdr.grab()
            from PyQt6.QtWidgets import QApplication as _QA
            _QA.processEvents()

            # Volver a dark y capturar header
            patient._toggle_theme()
            _proc()
            pix_d = hdr.grab()
            img_l = pix_l.toImage()
            img_d = pix_d.toImage()
            # Comparar píxel central
            cx = hdr.width() - 70
            cy = hdr.height() // 2
            cl = img_l.pixelColor(cx, cy)
            cd = img_d.pixelColor(cx, cy)
            delta = (abs(cl.red()-cd.red()) + abs(cl.green()-cd.green()) +
                     abs(cl.blue()-cd.blue()))
            if delta < 60:
                _report.bug("PATIENT", f"Header dark/light indistinguibles (delta={delta})",
                            f"dark=rgb({cd.red()},{cd.green()},{cd.blue()}) "
                            f"light=rgb({cl.red()},{cl.green()},{cl.blue()})")
            else:
                _report.ok("PATIENT", f"Header dark≠light (delta={delta})")
        except Exception:
            _report.warn("PATIENT", f"No se pudo verificar contraste: {traceback.format_exc()[-200:]}")
    except Exception:
        tb = traceback.format_exc()
        scr = _cap(patient, "p02_light_crash")
        _report.bug("PATIENT", "Crash al toggle light mode", tb, scr)
        try:
            patient._toggle_theme()  # intentar volver a dark
            _proc()
        except Exception:
            pass

    # ── Navegar módulos en light ──────────────────────────────────────────────
    _report.step("Navegar módulos en light mode")
    try:
        patient._toggle_theme()
        _proc()
        for mid in MODULE_IDS[:3]:  # muestra de los primeros 3
            try:
                patient._navigate_to(mid)
                _proc(); _proc()
                _cap(patient, f"p03_{mid}_light")
                _report.ok("PATIENT", f"Módulo '{mid}' en light sin crash")
                patient._go_home()
                _proc()
            except Exception:
                tb = traceback.format_exc()
                _report.bug("PATIENT", f"Crash en '{mid}' light mode", tb)
        patient._toggle_theme()  # restaurar dark
        _proc()
    except Exception:
        pass

    # ── Resize ────────────────────────────────────────────────────────────────
    _report.step("Test responsive resize")
    for rw, rh in [(800, 600), (1024, 768), (1366, 768), (1280, 720)]:
        try:
            patient.resize(rw, rh)
            _proc(); _proc()
            scr = _cap(patient, f"p04_resize_{rw}x{rh}")
            _detect_issues(patient, f"PATIENT {rw}x{rh}")
            _report.ok("PATIENT", f"Resize {rw}x{rh} sin crash")
        except Exception:
            tb = traceback.format_exc()
            _report.bug("PATIENT", f"Crash en resize {rw}x{rh}", tb)

    # ── Navegación rápida completa en tamaño grande ────────────────────────────
    patient.resize(1280, 720)
    _proc()
    _report.step("Navegación completa con resize 1280x720")
    for mid in MODULE_IDS:
        try:
            patient._navigate_to(mid)
            _proc()
            _detect_issues(patient, f"PATIENT {mid} 1280x720")
            patient._go_home()
            _proc()
        except Exception:
            tb = traceback.format_exc()
            _report.bug("PATIENT", f"Crash en '{mid}' a 1280x720", tb)

    patient.close()
    _proc()
    _report.ok("PATIENT", "App paciente cerró limpiamente")


# ── FASE 3: Hub ───────────────────────────────────────────────────────────────

def run_hub_qa():
    _report.section("FASE 3 — Hub Profesional (NeuroMood Hub Pro)")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    _report.step("Inicializar HubProfesional")
    try:
        from hub.main_qt import HubProfesional
        hub = HubProfesional()
        hub.show()
        _proc(); _proc()
        _report.ok("HUB", "HubProfesional abrió sin crash")
    except Exception:
        tb = traceback.format_exc()
        _report.bug("HUB", "HubProfesional no pudo abrirse", tb)
        return

    _cap(hub, "h00_dashboard_dark")
    _detect_issues(hub, "HUB Dashboard dark")

    # ── Navegación ────────────────────────────────────────────────────────────
    _report.step("Navegar vistas del Hub")
    for nav_id, label in [("pacientes", "Pacientes"), ("config", "Config"),
                          ("dashboard", "Dashboard")]:
        try:
            hub._on_nav(nav_id)
            _proc(); _proc()
            _cap(hub, f"h01_{nav_id}_dark")
            _detect_issues(hub, f"HUB {label} dark")
            _report.ok("HUB", f"Vista '{label}' abrió sin crash")
        except Exception:
            tb = traceback.format_exc()
            _report.bug("HUB", f"Crash navegando a '{label}'", tb)

    # ── IA mock ───────────────────────────────────────────────────────────────
    _report.step("Vista IA (DetallePacienteView mock)")
    try:
        from PyQt6.QtWidgets import QTabWidget
        from hub.pacientes_qt import DetallePacienteView
        detalle = DetallePacienteView(
            modo=hub._modo, sb=None,
            paciente_id="qa_test_id",
            paciente_nombre="QA Test",
        )
        hub._stack.addWidget(detalle)
        hub._stack.setCurrentWidget(detalle)
        _proc(); _proc()
        _cap(hub, "h02_detalle_paciente")
        _detect_issues(hub, "HUB DetallePaciente")
        _report.ok("HUB", "DetallePacienteView abrió sin crash")

        tabs = detalle.findChildren(QTabWidget)
        if tabs:
            for i in range(tabs[0].count()):
                tabs[0].setCurrentIndex(i)
                _proc()
                _cap(hub, f"h02_detalle_tab{i}")
                _report.ok("HUB", f"Tab {i} de DetallePaciente sin crash")
        hub._on_nav("dashboard")
        _proc()
    except Exception:
        tb = traceback.format_exc()
        _report.bug("HUB", "Crash en DetallePacienteView mock", tb)

    # ── Sidebar toggle ────────────────────────────────────────────────────────
    _report.step("Toggle sidebar collapse")
    try:
        hub._toggle_sidebar()
        _proc(); _proc()
        _cap(hub, "h03_sidebar_collapsed")
        _detect_issues(hub, "HUB sidebar collapsed")
        hub._toggle_sidebar()
        _proc()
        _report.ok("HUB", "Sidebar toggle collapse/expand sin crash")
    except Exception:
        tb = traceback.format_exc()
        _report.bug("HUB", "Crash en toggle sidebar", tb)

    # ── Toggle tema ───────────────────────────────────────────────────────────
    _report.step("Toggle dark → light → dark")
    try:
        hub._toggle_theme()
        _proc(); _proc()
        _cap(hub, "h04_dashboard_light")
        _detect_issues(hub, "HUB Dashboard light")
        _report.ok("HUB", "Toggle light mode sin crash")

        # Navegación en light
        for nav_id in ["pacientes", "config", "dashboard"]:
            hub._on_nav(nav_id)
            _proc()
            _cap(hub, f"h04_{nav_id}_light")
            _report.ok("HUB", f"Vista '{nav_id}' en light sin crash")

        hub._toggle_theme()
        _proc()
        _report.ok("HUB", "Restaurar dark mode sin crash")
    except Exception:
        tb = traceback.format_exc()
        _report.bug("HUB", "Crash en toggle tema Hub", tb)
        try:
            hub._toggle_theme()
            _proc()
        except Exception:
            pass

    # ── Resize ────────────────────────────────────────────────────────────────
    _report.step("Test responsive resize Hub")
    for rw, rh in [(1024, 720), (1280, 800), (1366, 768), (1920, 1080)]:
        try:
            hub.resize(rw, rh)
            _proc(); _proc()
            _cap(hub, f"h05_resize_{rw}x{rh}")
            _detect_issues(hub, f"HUB {rw}x{rh}")
            _report.ok("HUB", f"Resize {rw}x{rh} sin crash")
        except Exception:
            tb = traceback.format_exc()
            _report.bug("HUB", f"Crash en resize {rw}x{rh}", tb)

    hub.close()
    _proc()
    _report.ok("HUB", "Hub cerró limpiamente")


# ── FASE 4: Installers UI ─────────────────────────────────────────────────────

def _test_installer(cls_name: str, module_path: str, pages_to_visit: int = 2):
    """Instancia un installer, navega páginas seguras, detecta crashes."""
    section = "INSTALLER"
    _report.step(f"Testeando {cls_name}")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    inst = None
    try:
        mod = __import__(module_path, fromlist=[cls_name])
        cls = getattr(mod, cls_name)
        inst = cls()
        inst.show()
        _proc(); _proc()
        _cap(inst, f"ins_{cls_name.lower()}_p0")
        _report.ok(section, f"{cls_name}: abrió sin crash")
        _detect_issues(inst, f"{cls_name}")

        # Navegar páginas seguras (no la última que dispara el proceso real)
        for pi in range(1, min(pages_to_visit, len(inst._pages))):
            try:
                inst._ir_a(pi)
                _proc(); _proc()
                _cap(inst, f"ins_{cls_name.lower()}_p{pi}")
                _report.ok(section, f"{cls_name}: página {pi} sin crash")
                _detect_issues(inst, f"{cls_name} p{pi}")
            except Exception:
                tb = traceback.format_exc()
                _report.bug(section, f"{cls_name}: crash en página {pi}", tb)

        inst.close()
        _proc()
        _report.ok(section, f"{cls_name}: cerró limpiamente")

    except Exception:
        tb = traceback.format_exc()
        scr = _cap(inst, f"ins_{cls_name.lower()}_crash") if inst else ""
        _report.bug(section, f"{cls_name}: crash al instanciar", tb, scr)
        try:
            if inst:
                inst.close()
        except Exception:
            pass


def run_installer_qa():
    _report.section("FASE 4 — Installers / Uninstallers UI")

    _test_installer("InstaladorNeuroMood", "installers.installer",  pages_to_visit=2)
    _test_installer("InstaladorPro",       "installers.installer_pro", pages_to_visit=2)
    _test_installer("DesinstaladorNeuroMood", "installers.uninstaller", pages_to_visit=1)
    _test_installer("DesinstaladorPro",       "installers.uninstaller_pro", pages_to_visit=1)


# ── FASE 5: Tests de regresión rápidos ───────────────────────────────────────

def run_regression_checks():
    """Checks de lógica críticos sin abrir UI."""
    _report.section("FASE 5 — Regresiones de lógica (sin UI)")

    # ── shared/db.py — importación sin error ──────────────────────────────────
    try:
        from shared.db import obtener_conexion, inicializar_tablas
        _report.ok("LOGIC", "shared/db.py importa sin errores")
    except Exception:
        _report.bug("LOGIC", "shared/db.py falla al importar", traceback.format_exc())

    # ── shared/theme.py — tokens completos ───────────────────────────────────
    try:
        from shared.theme import COLORS
        dark  = COLORS["dark_hybrid"]
        light = COLORS["light_hybrid"]
        required = ["bg_primary", "bg_surface", "bg_secondary", "accent",
                    "text_primary", "text_secondary", "sidebar_bg", "text_on_accent"]
        missing = [k for k in required if k not in dark or k not in light]
        if missing:
            _report.bug("LOGIC", f"Tokens faltantes en COLORS: {missing}")
        else:
            _report.ok("LOGIC", f"Todos los tokens requeridos presentes en dark+light")
    except Exception:
        _report.bug("LOGIC", "shared/theme.py falla al importar", traceback.format_exc())

    # ── shared/identidad.py — función de ID ──────────────────────────────────
    try:
        from shared.identidad import generar_patient_id
        pid = generar_patient_id("TestUser", "pw123", "INSTALL_CODE")
        assert isinstance(pid, str) and len(pid) > 0, "ID vacío"
        _report.ok("LOGIC", f"generar_patient_id OK: '{pid[:20]}...'")
    except Exception:
        _report.bug("LOGIC", "generar_patient_id falla", traceback.format_exc())

    # ── shared/sync.py — import sin credential leak ───────────────────────────
    try:
        import importlib
        sync_mod = importlib.import_module("shared.sync")
        # Verificar que no haya credenciales en el módulo al importar
        src = Path(os.path.join(_proj, "shared", "sync.py")).read_text(encoding="utf-8")
        if "supabase.com" in src and 'os.getenv' not in src and '.env' not in src:
            _report.bug("LOGIC", "shared/sync.py puede tener credenciales hardcodeadas")
        else:
            _report.ok("LOGIC", "shared/sync.py sin credenciales hardcodeadas aparentes")
    except Exception:
        _report.bug("LOGIC", "shared/sync.py falla al importar", traceback.format_exc())

    # ── avisos_daemon.py — import correcto ───────────────────────────────────
    try:
        import importlib
        daemon = importlib.import_module("app.avisos_daemon")
        _report.ok("LOGIC", "app/avisos_daemon.py importa sin errores")
    except Exception:
        _report.bug("LOGIC", "app/avisos_daemon.py falla al importar", traceback.format_exc())

    # ── Verificar que _MODULE_MAP usa claves correctas ───────────────────────
    try:
        src = Path(os.path.join(_proj, "app", "main_qt.py")).read_text(encoding="utf-8")
        expected_ids = {"animo", "respiracion", "registro", "rutina", "actividades", "timer", "avisos"}
        found = set(re.findall(r'"(animo|respiracion|registro|rutina|actividades|timer|avisos)"', src))
        missing = expected_ids - found
        if missing:
            _report.bug("LOGIC", f"IDs de módulo faltantes en _MODULE_MAP: {missing}")
        else:
            _report.ok("LOGIC", "Todos los IDs de módulo presentes en _MODULE_MAP")
    except Exception:
        _report.warn("LOGIC", "No se pudo verificar _MODULE_MAP")


# ── Punto de entrada ──────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="QA Full Suite — NeuroMood V3")
    p.add_argument("--compile",    action="store_true")
    p.add_argument("--patient",    action="store_true")
    p.add_argument("--hub",        action="store_true")
    p.add_argument("--installers", action="store_true")
    p.add_argument("--logic",      action="store_true")
    args = p.parse_args()

    run_all = not any([args.compile, args.patient, args.hub,
                       args.installers, args.logic])

    print(f"\n  NeuroMood V3 — QA Full Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    run_compile_check()
    run_regression_checks()

    if args.logic:
        pass  # ya corrió arriba
    elif run_all or args.patient:
        run_patient_qa()
    if run_all or args.hub:
        run_hub_qa()
    if run_all or args.installers:
        run_installer_qa()

    # Resumen
    print()
    print(f"  {'='*60}")
    print(f"  QA COMPLETADO — {_report.ts.strftime('%Y-%m-%d %H:%M')}")
    print(f"  BUGS: {len(_report.bugs)}  WARNS: {len(_report.warns)}  PASS: {len(_report.passes)}")
    print(f"  {'='*60}")

    _report.save_markdown()
    return len(_report.bugs)


if __name__ == "__main__":
    sys.exit(main())
