"""
app/main_qt.py — NeuroMood Plataforma Paciente (PyQt6 entry point)

Layout:
    QMainWindow
    ├── NMHeader (56px, ancho completo)
    └── NMFadeWidget (contenido principal)
        ├── HomeView
        └── módulos cargados dinámicamente

Toda la lógica de negocio está preservada exactamente del main.py CTk:
    _sync_background(), _on_close() con bandeja, _get_module_status()
"""

import sys
import os
import importlib
import threading
import logging

_log = logging.getLogger("NeuroMood")

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
)
from PyQt6.QtCore import QTimer, QSize
from PyQt6.QtGui import QIcon

from shared.theme_qt import (
    C, colors, norm_modo, app_palette, stylesheet_base,
    obtener_ruta_recurso, aplicar_captionbar_qt,
)
from shared.components_qt import (
    ThemeManager, NMHeader, NMFadeWidget, NMToast,
)
from shared.db import inicializar_tablas
from shared.identidad import obtener_nombre_paciente
from app import avisos_daemon

# Módulos disponibles: id → (módulo Python, clase Qt)
# Se migrarán a Qt de a uno; mientras tanto se carga versión CTk si la Qt no existe
_MODULE_MAP = {
    "animo":       ("app.modules.animo_qt",        "ModuloAnimo"),
    "respiracion": ("app.modules.respiracion_qt",  "ModuloRespiracion"),
    "registro":    ("app.modules.registro_tcc_qt", "ModuloRegistroTCC"),
    "rutina":      ("app.modules.rutina_qt",       "ModuloRutina"),
    "actividades": ("app.modules.actividades_qt",  "ModuloActividades"),
    "timer":       ("app.modules.timer_qt",        "ModuloTimer"),
    "avisos":      ("app.modules.avisos_qt",       "ModuloAvisos"),
}

# Metadata de módulos para títulos e íconos.
_NAV_ITEMS = [
    ("animo",       "🎭", "Ánimo"),
    ("respiracion", "🌬️", "Respirar"),
    ("registro",    "📝", "Registro TCC"),
    ("rutina",      "✅", "Rutina"),
    ("actividades", "⚡", "Actividades"),
    ("timer",       "⏱️", "Timer"),
    ("avisos",      "🔔", "Avisos"),
]


class NeuroMoodApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        self._current_module: QWidget | None = None
        self._module_cache: dict[str, QWidget] = {}  # caché de módulos instanciados

        # ── Init DB y nombre ───────────────────────────────────────────────────
        inicializar_tablas()
        self._nombre = obtener_nombre_paciente() or "Paciente"

        # ── ThemeManager ───────────────────────────────────────────────────────
        self._tm = ThemeManager.instance()
        self._tm.switch_mode(self._modo)   # establece modo inicial

        # ── Ventana ────────────────────────────────────────────────────────────
        self.setWindowTitle(f"NeuroMood — Hola, {self._nombre}")
        self.setMinimumSize(QSize(720, 520))
        self.resize(QSize(860, 640))
        self._center_window()
        self._apply_icon()
        self._apply_initial_style()

        # ── UI ─────────────────────────────────────────────────────────────────
        self._build_ui()

        # ── Caption bar DWM ────────────────────────────────────────────────────
        QTimer.singleShot(120, lambda: aplicar_captionbar_qt(self, self._modo))

        # ── Daemon de avisos ───────────────────────────────────────────────────
        self._avisos_stop = avisos_daemon.iniciar(on_abrir_app=self._restaurar_ventana)

        # ── Sync background ────────────────────────────────────────────────────
        QTimer.singleShot(600, self._sync_background)

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header full-width
        self._header = NMHeader(central, modo=self._modo, username=self._nombre)
        self._header.theme_toggle.connect(self._toggle_theme)
        main_layout.addWidget(self._header)

        # Stack con fade
        self._stack = NMFadeWidget(central)
        main_layout.addWidget(self._stack)

        # Home
        from app.home_qt import HomeView
        self._home = HomeView(
            modo=self._modo,
            on_module_open=self._navigate_to,
            get_status_fn=self._get_module_status,
        )
        self._stack.addWidget(self._home)
        self._stack.setCurrentWidget(self._home)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _navigate_to(self, module_id: str):
        if module_id not in _MODULE_MAP:
            return

        # Si ya fue instanciado, reusar con fade
        if module_id in self._module_cache:
            mod = self._module_cache[module_id]
            if self._current_module and self._current_module is not mod:
                if hasattr(self._current_module, "on_leave"):
                    self._current_module.on_leave()
            self._current_module = mod
            self._stack.setCurrentWidget(mod)
            if hasattr(mod, "on_enter"):
                mod.on_enter()
            self._header.set_back_action(self._go_home)
            return

        mod_path, cls_name = _MODULE_MAP[module_id]
        try:
            module = importlib.import_module(mod_path)
            cls = getattr(module, cls_name)
        except (ImportError, AttributeError) as e:
            NMToast.show(self,
                         f"Módulo '{module_id}' no disponible aún.\n{e}",
                         variant="error")
            return

        # Instanciar y conectar señal back
        instance = cls(modo=self._modo, show_header=False)
        instance.back_requested.connect(self._go_home)
        self._module_cache[module_id] = instance
        self._stack.addWidget(instance)

        self._current_module = instance
        self._stack.setCurrentWidget(instance)
        if hasattr(instance, "on_enter"):
            instance.on_enter()
        self._header.set_back_action(self._go_home)

    def _go_home(self):
        if self._current_module:
            if hasattr(self._current_module, "on_leave"):
                self._current_module.on_leave()
            self._current_module = None

        self._stack.setCurrentWidget(self._home)
        self._home.refresh_statuses()
        self._header.set_back_action(None)

    def _back_to_home(self):
        self._go_home()

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        if "dark" in self._modo:
            self._modo = "light_hybrid"
        else:
            self._modo = "dark_hybrid"
        self._apply_global_style()
        self._tm.switch_mode(self._modo)
        QTimer.singleShot(50, lambda: aplicar_captionbar_qt(self, self._modo))

    def _apply_global_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    def _apply_initial_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    # ── Ventana ────────────────────────────────────────────────────────────────

    def _center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        target_w = min(900, int(screen.width() * 0.65))
        target_h = min(680, int(screen.height() * 0.78))
        if target_w < self.minimumWidth():
            target_w = self.minimumWidth()
        if target_h < self.minimumHeight():
            target_h = self.minimumHeight()
        self.resize(QSize(target_w, target_h))
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def _apply_icon(self):
        ico_path = obtener_ruta_recurso("NM_icon.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

    def closeEvent(self, event):
        self._on_close(event)

    def _on_close(self, event=None):
        """Minimiza a bandeja si hay avisos activos, si no cierra."""
        try:
            from shared.db import obtener_conexion
            conn = obtener_conexion()
            n = conn.execute(
                "SELECT COUNT(*) FROM recordatorios WHERE activo=1"
            ).fetchone()[0]
            conn.close()
        except Exception:
            n = 0

        if n > 0 and avisos_daemon._PYSTRAY_OK:
            if event:
                event.ignore()
            self.hide()   # Minimizar a bandeja, no cerrar
        else:
            avisos_daemon.detener()
            if event:
                event.accept()

    def _restaurar_ventana(self):
        """Llamado por el ícono de bandeja para traer la ventana al frente."""
        self.show()
        self.raise_()
        self.activateWindow()

    # ── Sync ──────────────────────────────────────────────────────────────────

    def _sync_background(self):
        try:
            from shared.sync import sync_al_abrir
            threading.Thread(target=sync_al_abrir, daemon=True).start()
        except Exception:
            _log.debug("Sync background skipped (module not available)")

    # ── Status de módulos (lógica preservada exacta del main.py CTk) ──────────

    def _get_module_status(self, module_id: str) -> str:
        try:
            from shared.db import obtener_conexion
            from shared.utils import fecha_hoy
            conn = obtener_conexion()
            hoy = fecha_hoy()
            result = ""
            if module_id == "animo":
                row = conn.execute(
                    "SELECT puntaje FROM termometro "
                    "WHERE fecha=? ORDER BY hora DESC LIMIT 1", (hoy,)
                ).fetchone()
                result = f"{row[0]}/10 ✔" if row else ""
            elif module_id == "respiracion":
                n = conn.execute(
                    "SELECT COUNT(*) FROM respiracion WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} sesión{'es' if n > 1 else ''} ✔" if n else ""
            elif module_id == "registro":
                n = conn.execute(
                    "SELECT COUNT(*) FROM pensamientos WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} registro{'s' if n > 1 else ''} ✔" if n else ""
            elif module_id == "rutina":
                total = conn.execute(
                    "SELECT COUNT(*) FROM checklist_tareas"
                ).fetchone()[0]
                done = conn.execute(
                    "SELECT COUNT(*) FROM checklist_completadas WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{done}/{total} ✔" if total else ""
            elif module_id == "actividades":
                n = conn.execute(
                    "SELECT COUNT(*) FROM activacion WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} actividad{'es' if n > 1 else ''} ✔" if n else ""
            elif module_id == "timer":
                n = conn.execute(
                    "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} sesión{'es' if n > 1 else ''} ✔" if n else ""
            elif module_id == "avisos":
                n = conn.execute(
                    "SELECT COUNT(*) FROM recordatorios WHERE activo=1"
                ).fetchone()[0]
                result = f"{n} activo{'s' if n > 1 else ''}" if n else ""
            conn.close()
            return result
        except Exception:
            _log.debug("Could not get module status for %s", module_id)
        return ""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood")
    app.setOrganizationName("NeuroMood")
    # AA_UseHighDpiPixmaps fue eliminado en PyQt6 6.x — DPI se maneja automáticamente

    window = NeuroMoodApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
