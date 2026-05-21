"""
AI_SCRIPTS/_capture_v3_screens.py — Captura visual robusta de pantallas v3.

Spawnea un subprocess por pantalla — un crash no afecta a los demás.
Genera PNGs en _qa_output/v3_capture/ con cada pantalla del Suite + Hub
en dark y light. Útil para diff visual contra el mockup HTML del bundle.

Ejecutar:
    python AI_SCRIPTS/_capture_v3_screens.py
o:
    python AI_SCRIPTS/_capture_v3_screens.py --worker SLUG MODE OUTFILE
"""
import os
import sys
import subprocess
import traceback

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

OUT_DIR = os.path.join(_root, "_qa_output", "v3_capture")


# ── Lista de pantallas: (slug, builder_path, ctor_args) ────────────────────
# builder_path es "module:function|class" — el worker importa y llama.

# (slug, screen_kind, size)
SCREENS = [
    ("suite_01_inicio",      "home",        (1320, 860)),
    ("suite_02_animo",       "animo",       (1320, 860)),
    ("suite_03_respiracion", "respiracion", (1320, 860)),
    ("suite_04_tcc",         "tcc",         (1320, 860)),
    ("suite_05_rutina",      "rutina",      (1320, 860)),
    ("suite_06_actividades", "actividades", (1320, 860)),
    ("suite_07_timer",       "timer",       (1320, 860)),
    ("suite_08_avisos",      "avisos",      (1320, 860)),
    ("hub_01_pacientes",     "pacientes",   (1360, 920)),
    ("hub_02_ia",            "ia",          (1360, 920)),
    ("hub_03_config",        "config",      (1360, 920)),
]


def _worker_build(kind: str, modo: str):
    """Construye la pantalla solicitada y devuelve el widget."""
    if kind == "home":
        from app.home_qt import HomeView
        return HomeView(
            modo=modo,
            on_module_open=lambda x: None,
            get_status_fn=lambda mid: {
                "animo": "En progreso", "respiracion": "Completo",
                "registro": "Activo", "rutina": "2/5 hoy",
                "actividades": "3 hoy", "timer": "45 min", "avisos": ""
            }.get(mid, ""),
            username="Ana")
    if kind == "animo":
        from app.modules.animo_qt import ModuloAnimo
        return ModuloAnimo(modo=modo)
    if kind == "respiracion":
        from app.modules.respiracion_qt import ModuloRespiracion
        return ModuloRespiracion(modo=modo)
    if kind == "tcc":
        from app.modules.registro_tcc_qt import ModuloRegistroTCC
        return ModuloRegistroTCC(modo=modo)
    if kind == "rutina":
        from app.modules.rutina_qt import ModuloRutina
        return ModuloRutina(modo=modo)
    if kind == "actividades":
        from app.modules.actividades_qt import ModuloActividades
        return ModuloActividades(modo=modo)
    if kind == "timer":
        from app.modules.timer_qt import ModuloTimer
        return ModuloTimer(modo=modo)
    if kind == "avisos":
        from app.modules.avisos_qt import ModuloAvisos
        return ModuloAvisos(modo=modo)
    if kind == "pacientes":
        from hub.main_qt import PacientesView
        pacientes_mock = [
            {"patient_name": "Ana Martínez", "patient_id": "abc123def456",
             "adherence": 0.85, "last_session": "hace 1 día"},
            {"patient_name": "Carlos López", "patient_id": "xyz789",
             "adherence": 0.35, "last_session": "hace 5 días"},
            {"patient_name": "María Rodríguez", "patient_id": "mno456",
             "adherence": 0.92, "last_session": "hoy"},
            {"patient_name": "Juan Pérez", "patient_id": "qwe111",
             "adherence": 0.55, "last_session": "ayer"},
        ]
        return PacientesView(modo, pacientes_mock,
                              on_select=lambda *a: None,
                              on_refresh=lambda: None)
    if kind == "ia":
        from hub.main_qt import IAAssistantView
        return IAAssistantView(modo, "Ana Martínez")
    if kind == "config":
        from hub.main_qt import ConfigView
        return ConfigView(modo,
                           on_toggle_theme=lambda: None,
                           on_reconnect=lambda: None)
    raise ValueError(f"Unknown screen kind: {kind}")


def run_worker(kind: str, modo: str, w: int, h: int, out_path: str):
    """Subprocess entry point: construye dentro de un ShellWindow (que pinta
    el background v3 con gradient + blobs), renderiza, guarda, exit."""
    os.environ["NM_VISUAL_QA"] = "1"
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QPainter
    app = QApplication([])
    from shared.theme_qt import _ensure_premium_font, paint_shell_background
    _ensure_premium_font()

    class _ShellWindow(QMainWindow):
        """Replica el shell de NeuroMoodApp para que los módulos hijos hereden
        el fondo glassmorph + blobs (sin esto las cards translúcidas no
        muestran nada detrás)."""
        def __init__(self, modo):
            super().__init__()
            self._modo = modo
            self.setAttribute(__import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.WidgetAttribute.WA_StyledBackground, True)

        def paintEvent(self, ev):
            p = QPainter(self)
            paint_shell_background(p, QRectF(self.rect()), self._modo)
            p.end()

    shell = _ShellWindow(modo)
    shell.resize(w, h)
    inner = _worker_build(kind, modo)
    # Algunos widgets son top-level (QMainWindow del NMModule), no se pueden
    # poner dentro de otro QMainWindow. Detectar y ajustar.
    from PyQt6.QtWidgets import QMainWindow as _QM
    if isinstance(inner, _QM):
        # NMModule extiende QWidget, no QMainWindow. PacientesView/ConfigView/
        # IAAssistantView extienden QWidget también. HomeView extiende QWidget.
        # Si por alguna razón es QMainWindow, fallback: capturar standalone.
        inner.resize(w, h); inner.show(); app.processEvents(); inner.repaint(); app.processEvents()
        pix = inner.grab()
    else:
        shell.setCentralWidget(inner)
        shell.show()
        app.processEvents()
        shell.repaint()
        app.processEvents()
        pix = shell.grab()

    if pix.isNull():
        print(f"NULL", flush=True)
        sys.exit(2)
    ok = pix.save(out_path, "PNG")
    print(f"OK {pix.width()}x{pix.height()}" if ok else "SAVE_FAIL", flush=True)
    sys.exit(0 if ok else 3)


def main_orchestrator():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"\nOutput dir: {OUT_DIR}\n")

    ok_count = 0
    fail_count = 0
    crashed = 0
    for slug, kind, (w, h) in SCREENS:
        for modo, modo_short in (("dark_hybrid", "dark"), ("light_hybrid", "light")):
            out_path = os.path.join(OUT_DIR, f"{slug}__{modo_short}.png")
            cmd = [
                sys.executable, "-u", os.path.abspath(__file__),
                "--worker", kind, modo, str(w), str(h), out_path,
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=30, cwd=_root)
                stdout = (res.stdout or "").strip()
                if res.returncode == 0 and os.path.exists(out_path):
                    kb = os.path.getsize(out_path) / 1024
                    print(f"  OK  {slug:30s} {modo_short:6s} {stdout} ({kb:.0f} KB)")
                    ok_count += 1
                elif res.returncode < 0 or res.returncode > 100:
                    print(f"  XX  {slug:30s} {modo_short:6s} CRASH (exit {res.returncode})")
                    crashed += 1
                else:
                    err = (res.stderr or "")[-200:].strip().replace("\n", " | ")
                    print(f"  FAIL {slug:30s} {modo_short:6s} (exit {res.returncode}) {err[:120]}")
                    fail_count += 1
            except subprocess.TimeoutExpired:
                print(f"  TIMEOUT {slug:30s} {modo_short:6s}")
                fail_count += 1
            except Exception as e:
                print(f"  ERR {slug:30s} {modo_short:6s} :: {e}")
                fail_count += 1

    print(f"\nResumen: {ok_count} OK / {fail_count} FAIL / {crashed} CRASH")
    print(f"Capturas en: {OUT_DIR}")


if __name__ == "__main__":
    if len(sys.argv) >= 7 and sys.argv[1] == "--worker":
        # Worker mode: --worker KIND MODE W H OUTPATH
        try:
            run_worker(sys.argv[2], sys.argv[3],
                       int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
        except Exception:
            traceback.print_exc()
            sys.exit(1)
    else:
        main_orchestrator()
