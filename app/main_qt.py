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
    QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QGraphicsOpacityEffect, QMessageBox,
)
from PyQt6.QtCore import QTimer, QSize, QRectF, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtGui import QIcon, QPainter
from PyQt6 import sip

from shared.theme_qt import (
    obtener_ruta_recurso, aplicar_captionbar_qt,
    ANIM, EASE_IN, EASE_OUT, ThemeAwareWidgetMixin,
    paint_shell_background,
    app_palette, stylesheet_base,
    norm_modo,
)
from shared.components_qt import (
    ThemeManager, NMHeader, NMFadeWidget, NMToast,
)
from shared.db import inicializar_tablas
from shared.identidad import obtener_nombre_paciente
from app import avisos_daemon
from shared.visual_qa import visual_qa_enabled, qa_patient_name, module_status as qa_module_status

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

_MODULE_UI_META = {
    "animo":       ("Ánimo", "animo"),
    "respiracion": ("Respiración", "respiracion"),
    "registro":    ("Registro TCC", "registro_tcc"),
    "rutina":      ("Rutina del día", "rutina"),
    "actividades": ("Actividades", "actividades"),
    "timer":       ("Timer de enfoque", "timer"),
    "avisos":      ("Avisos", "avisos"),
}

_MODULE_UI_BADGES = {
    "animo": ("🔥 5 días", "warning"),
    "respiracion": ("3 ciclos", "teal"),
    "registro": ("Paso 1/4", "accent"),
    "rutina": ("8/10 · 80%", "teal"),
    "actividades": ("3 completadas hoy", "text_tertiary"),
    "avisos": ("2/5", "teal"),
}

# Metadata de módulos para títulos e íconos.
class _ShellWidget(QWidget):
    """Central widget con fondo shell v3: gradiente + blobs."""
    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = modo

    def set_shell_modo(self, modo: str):
        self._modo = modo
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        paint_shell_background(p, QRectF(self.rect()), self._modo)
        p.end()


class NeuroMoodApp(ThemeAwareWidgetMixin, QMainWindow):

    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        self._current_module: QWidget | None = None
        self._module_cache: dict[str, QWidget] = {}  # caché de módulos instanciados

        # ── Init DB y nombre ───────────────────────────────────────────────────
        self._visual_qa = visual_qa_enabled()
        if self._visual_qa:
            self._nombre = qa_patient_name()
        else:
            inicializar_tablas()
            self._nombre = obtener_nombre_paciente() or "Paciente"

        # ── ThemeManager ───────────────────────────────────────────────────────
        self._tm = ThemeManager.instance()
        self._tm.switch_mode(self._modo)   # establece modo inicial

        # ── Ventana ────────────────────────────────────────────────────────────
        self.setWindowTitle(f"NeuroMood Suite — Hola, {self._nombre}")
        self.setMinimumSize(QSize(1100, 720))
        self.resize(QSize(1320, 860))
        self._center_window()
        self._apply_icon()
        self._apply_initial_style()

        # ── UI ─────────────────────────────────────────────────────────────────
        self._build_ui()

        # ── Caption bar DWM ────────────────────────────────────────────────────
        QTimer.singleShot(
            120,
            lambda: aplicar_captionbar_qt(self, self._modo)
            if not sip.isdeleted(self) else None,
        )

        # ── Daemon de avisos ───────────────────────────────────────────────────
        self._avisos_stop = None
        if not self._visual_qa:
            self._avisos_stop = avisos_daemon.iniciar(on_abrir_app=self._restaurar_ventana)

        # ── Sync background ────────────────────────────────────────────────────
        if not self._visual_qa:
            QTimer.singleShot(600, self._sync_background)
        self._connect_theme()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self):
        central = _ShellWidget(modo=self._modo)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header full-width — modo normal (logo NM + nombre sutil + theme toggle).
        # El saludo grande va SOLO en la _SidePanel de HomeView; el header queda
        # limpio para que la sidebar tenga el protagonismo en home.
        self._header = NMHeader(central, modo=self._modo, home_mode=False,
                                username=self._nombre)
        self._header.theme_toggle.connect(self._toggle_theme)
        main_layout.addWidget(self._header)

        # Stack con fade
        self._stack = NMFadeWidget(central)
        main_layout.addWidget(self._stack)

        # Home
        from app.home_qt import HomeView
        self._home = HomeView(
            modo=self._modo,
            on_module_open=self._open_module,
            get_status_fn=self._get_module_status,
            username=self._nombre,
        )
        self._home._theme_switch_requested.connect(self._toggle_theme)
        self._stack.addWidget(self._home)
        self._navigate_to(self._home)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _navigate_to(self, widget: QWidget):
        """Fade out -> swap -> fade in en 200ms total."""
        if isinstance(widget, str):
            self._open_module(widget)
            return
        current = self._stack.currentWidget()
        if widget is current:
            return
        if current is None:
            QStackedWidget.setCurrentWidget(self._stack, widget)
            return

        current_eff = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(current_eff)

        fade_out = QPropertyAnimation(current_eff, b"opacity", self)
        fade_out.setDuration(ANIM["fast"] - 50)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(EASE_IN)

        def _swap():
            current.setGraphicsEffect(None)
            QStackedWidget.setCurrentWidget(self._stack, widget)
            target_eff = QGraphicsOpacityEffect(widget)
            target_eff.setOpacity(0.0)
            widget.setGraphicsEffect(target_eff)
            fade_in = QPropertyAnimation(target_eff, b"opacity", self)
            fade_in.setDuration(ANIM["fast"] - 50)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(EASE_OUT)

            def _finish_in():
                widget.setGraphicsEffect(None)

            fade_in.finished.connect(_finish_in)
            self._nav_fade_in = fade_in
            fade_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        fade_out.finished.connect(_swap)
        self._nav_fade_out = fade_out
        fade_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _open_module(self, module_id: str):
        if module_id not in _MODULE_MAP:
            return

        # Si ya fue instanciado, reusar con fade
        if module_id in self._module_cache:
            mod = self._module_cache[module_id]
            if self._current_module and self._current_module is not mod:
                if hasattr(self._current_module, "on_leave"):
                    self._current_module.on_leave()
            self._current_module = mod
            self._navigate_to(mod)
            if hasattr(mod, "on_enter"):
                mod.on_enter()
            self._header.set_back_action(self._go_home)
            title, icon = _MODULE_UI_META.get(module_id, ("", ""))
            self._header.set_context_title(title, icon)
            badge, color = _MODULE_UI_BADGES.get(module_id, ("", "teal"))
            self._header.set_context_badge(badge, color)
            return

        mod_path, cls_name = _MODULE_MAP[module_id]
        try:
            module = importlib.import_module(mod_path)
            cls = getattr(module, cls_name)
        except (ImportError, AttributeError) as e:
            NMToast.display(self,
                         f"Módulo '{module_id}' no disponible aún.\n{e}",
                         variant="error")
            return

        # Instanciar y conectar señal back
        instance = cls(modo=self._modo, show_header=False)
        instance.back_requested.connect(self._go_home)
        self._module_cache[module_id] = instance
        self._stack.addWidget(instance)

        self._current_module = instance
        self._navigate_to(instance)
        if hasattr(instance, "on_enter"):
            instance.on_enter()
        self._header.set_back_action(self._go_home)
        title, icon = _MODULE_UI_META.get(module_id, ("", ""))
        self._header.set_context_title(title, icon)
        badge, color = _MODULE_UI_BADGES.get(module_id, ("", "teal"))
        self._header.set_context_badge(badge, color)

    def _go_home(self):
        if self._current_module:
            if hasattr(self._current_module, "on_leave"):
                self._current_module.on_leave()
            self._current_module = None

        self._navigate_to(self._home)
        self._home.refresh_statuses()
        self._header.set_back_action(None)
        self._header.set_context_title("")
        self._header.set_context_badge("")
        # El saludo vive ya en _SidePanel; el header queda en su modo normal
        # (logo + username + toggle) tras limpiar el context title.

    def _back_to_home(self):
        self._go_home()

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        new_modo = "light_hybrid" if "dark" in self._modo else "dark_hybrid"
        self._apply_global_style(new_modo)
        self._tm.switch_mode(new_modo)
        self._modo = new_modo
        QTimer.singleShot(
            50,
            lambda m=new_modo: aplicar_captionbar_qt(self, m)
            if not sip.isdeleted(self) else None,
        )

    def _apply_global_style(self, modo: str | None = None):
        modo = modo or self._modo
        QApplication.instance().setPalette(app_palette(modo))
        QApplication.instance().setStyleSheet(stylesheet_base(modo))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_global_style(self._modo)
        cw = self.centralWidget()
        if isinstance(cw, _ShellWidget):
            cw.set_shell_modo(self._modo)
        if hasattr(self, "_header"):
            self._header._apply_theme(self._modo)
        if hasattr(self, "_home"):
            self._home._apply_theme(self._modo)
            self._home.refresh_statuses()

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
        """Minimiza a bandeja si hay avisos activos o timer corriendo, si no cierra."""
        if os.environ.get("NM_TEST_FORCE_CLOSE") == "1" or getattr(self, "_visual_qa", False):
            avisos_daemon.detener()
            if event:
                event.accept()
            QApplication.instance().quit()
            return
        try:
            from shared.db import obtener_conexion
            conn = obtener_conexion()
            n = conn.execute(
                "SELECT COUNT(*) FROM recordatorios WHERE activo=1"
            ).fetchone()[0]
            conn.close()
        except Exception:
            n = 0

        # Verificar si el timer está corriendo en el módulo actual
        timer_active = False
        if self._current_module and hasattr(self._current_module, '_running'):
            timer_active = getattr(self._current_module, '_running', False)

        if (n > 0 or timer_active) and avisos_daemon._PYSTRAY_OK:
            if event:
                event.ignore()
            self.hide()
        else:
            if timer_active and not avisos_daemon._PYSTRAY_OK:
                resp = QMessageBox.question(
                    self,
                    "Timer activo",
                    "Hay un timer en curso y la bandeja del sistema no esta disponible.\n"
                    "Si cerras NeuroMood, el timer se detendra. Queres cerrar igual?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if resp != QMessageBox.StandardButton.Yes:
                    if event:
                        event.ignore()
                    return
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
        if getattr(self, "_visual_qa", False):
            return qa_module_status(module_id)
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
                result = f"{row[0]}/10" if row else ""
            elif module_id == "respiracion":
                n = conn.execute(
                    "SELECT COUNT(*) FROM respiracion WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = "Activo" if n else ""
            elif module_id == "registro":
                n = conn.execute(
                    "SELECT COUNT(*) FROM pensamientos WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} registro{'s' if n > 1 else ''}" if n else ""
            elif module_id == "rutina":
                total = conn.execute(
                    "SELECT COUNT(*) FROM checklist_tareas"
                ).fetchone()[0]
                done = conn.execute(
                    "SELECT COUNT(*) FROM checklist_completadas WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                if total:
                    result = f"✓ {done}/{total}" if done == total else f"{done}/{total}"
                else:
                    result = ""
            elif module_id == "actividades":
                n = conn.execute(
                    "SELECT COUNT(*) FROM activacion WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} hoy" if n else ""
            elif module_id == "timer":
                n = conn.execute(
                    "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} sesión{'es' if n > 1 else ''}" if n else ""
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
    from shared.crash_log import setup as _crash_setup
    _crash_setup("suite")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood Suite")
    app.setOrganizationName("NeuroMood Suite")
    # AA_UseHighDpiPixmaps fue eliminado en PyQt6 6.x — DPI se maneja automáticamente

    window = NeuroMoodApp()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
