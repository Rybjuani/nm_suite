"""
app/main_qt.py — NeuroMood Plataforma Paciente (PyQt6 entry point)

Layout:
    QMainWindow
    ├── NMWindowChrome (titlebar 48px; lleva back + título de módulo, BL-07)
    └── NMFadeWidget (contenido principal)
        ├── HomeView
        └── módulos cargados dinámicamente

Toda la lógica de negocio está preservada exactamente del main.py CTk:
    _sync_background(), _on_close() con bandeja, _get_module_status()
"""

import sys
import os
import pathlib
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
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QRectF,
    QSettings,
    pyqtSignal,
)
from PyQt6.QtGui import QIcon, QPainter
from PyQt6 import sip


# ── QSettings · persistencia del tema (handoff Mayo 2026) ────────────────────
# El usuario elige light/dark desde el header; la elección persiste entre
# sesiones via QSettings. La org/app se setea en main() — QSettings sin args
# usa los nombres ya registrados allí.


def _saved_theme(default: str = "dark_hybrid") -> str:
    """Devuelve el modo guardado o `default`. Normaliza alias legacy."""
    try:
        raw = QSettings("NeuroMood", "Suite").value("ui/theme", default, type=str)
    except Exception:
        raw = default
    return norm_modo(raw or default)


def _persist_theme(modo: str) -> None:
    """Guarda el modo (best-effort; nunca lanza)."""
    try:
        QSettings("NeuroMood", "Suite").setValue("ui/theme", norm_modo(modo))
    except Exception:
        _log.debug("No se pudo persistir el tema (QSettings unavailable)")


from shared.theme_qt import (
    obtener_ruta_recurso,
    ThemeAwareWidgetMixin,
    paint_shell_background,
    app_palette,
    stylesheet_base,
    norm_modo,
    v3c,
)
from shared.adaptive_layout_qt import configure_adaptive_window, install_transient_qt_window_guard
from shared.components import (
    ThemeManager,
    NMFadeWidget,
    NMToast,
    NMWindowChrome,
)
from shared.db import inicializar_tablas
from shared.identidad import obtener_nombre_paciente
from app import avisos_daemon
from shared.visual_qa import visual_qa_enabled, qa_patient_name, module_status as qa_module_status
from shared.remote_config import t

_MODULE_MAP = {
    "animo": ("app.modules.animo_qt", "ModuloAnimo"),
    "respiracion": ("app.modules.respiracion_qt", "ModuloRespiracion"),
    "registro": ("app.modules.registro_tcc_qt", "ModuloRegistroTCC"),
    "rutina": ("app.modules.rutina_qt", "ModuloRutina"),
    "actividades": ("app.modules.actividades_qt", "ModuloActividades"),
    "timer": ("app.modules.timer_qt", "ModuloTimer"),
    "avisos": ("app.modules.avisos_qt", "ModuloAvisos"),
    "dbt": ("app.modules.dbt_qt", "ModuloDBT"),
}

_MODULE_UI_META = {
    "animo": ("Termómetro emocional", "animo"),
    "respiracion": ("Guía de respiración animada", "respiracion"),
    "registro": ("Registro de pensamientos (TCC)", "registro_tcc"),
    "rutina": ("Checklist de rutina diaria", "rutina"),
    "actividades": ("Asistente de activación conductual", "actividades"),
    "timer": ("Temporizador de actividades", "timer"),
    "avisos": ("Recordatorios de bienestar", "avisos"),
    "dbt": ("Habilidades DBT", "spark"),
}


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
    # Emite (label, tone) desde el hilo de sync; queued → seguro cross-thread.
    _sync_status_sig = pyqtSignal(str, str)
    # Emitido desde el hilo de la bandeja (pystray) cuando el usuario toca
    # "Salir"; queued → el cierre real corre en el hilo de UI. Sin esto el
    # proceso Qt queda vivo con la ventana oculta y sin ícono (proceso "invisible").
    _quit_requested = pyqtSignal()
    # Ídem para "Abrir NeuroMood": el callback de pystray corre en su hilo;
    # mostrar la ventana (y el diálogo de PIN) debe pasar por el hilo de UI.
    _restore_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Restaurar tema persistido (handoff Mayo 2026 — QSettings).
        self._modo = _saved_theme("dark_hybrid")
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
        self._tm.switch_mode(self._modo)  # establece modo inicial

        # ── Ventana frameless (handoff WindowChrome) ───────────────────────────
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowTitle(f"NeuroMood Suite — Hola, {self._nombre}")
        self._center_window()
        self._apply_icon()
        self._apply_initial_style()

        # ── UI ─────────────────────────────────────────────────────────────────
        self._build_ui()

        # ── Sombra DWM (frameless necesita restaurar sombra nativa) ───────────
        QTimer.singleShot(
            120,
            lambda: self._apply_dwm_shadow() if not sip.isdeleted(self) else None,
        )

        # ── Daemon de avisos ───────────────────────────────────────────────────
        self._really_quit = False
        self._quit_requested.connect(self._force_quit)
        self._restore_requested.connect(self._restaurar_ventana)
        self._avisos_stop = None
        # Performance (qa/PERFORMANCE_AUDIT.md Fix #3): diferir iniciar() al
        # primer ciclo de eventos tras show(). Antes corría síncrono en
        # __init__, agregando al critical path: import pystray (~30ms en
        # Windows), PIL.open(.ico).resize((64,64)) (~27ms medido), creación
        # de pystray.Icon + start de hilo bandeja (~20ms). Total ~50-80ms
        # en Windows real que NO necesitan bloquear el primer paint.
        # QTimer.singleShot(0, ...) encola en el event loop y corre
        # inmediatamente después de que Qt termine el primer paint de la
        # ventana, sin que el usuario lo perciba.
        if not self._visual_qa:
            def _start_avisos_daemon():
                if sip.isdeleted(self):
                    return
                self._avisos_stop = avisos_daemon.iniciar(
                    on_abrir_app=self._restore_requested.emit,
                    on_salir=self._quit_requested.emit,
                )
            QTimer.singleShot(0, _start_avisos_daemon)

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

        # ── Chrome (36 px, full-width, reemplaza barra nativa) ────────────────
        # El nombre de la app (barra de título) también es un texto global
        # configurable desde el Hub.
        _brand = t("text.chrome.app_title", "NeuroMood Suite")
        self._chrome = NMWindowChrome(
            title=_brand,
            modo=self._modo,
            show_theme_toggle=True,
            parent=central,
        )
        self._chrome.theme_toggle.connect(self._toggle_theme)
        main_layout.addWidget(self._chrome)

        # ── Fila de contenido: área derecha toma todo el ancho ─────────────────
        # Mockup canónico: `.window { background: var(--surface) }` — todo el
        # área debajo del titlebar es surface (no bg). Antes `content` era
        # transparente, lo que dejaba ver el gradiente bg del shell en los
        # márgenes/padding donde el módulo no cubría. Esto generaba el patrón
        # sistemático "light theme changed_pixel_ratio 3-5x mayor que dark"
        # porque en light bg vs surface difieren ~22/canal (>12 threshold) y
        # en dark solo ~11/canal (<12 threshold).
        content = QWidget(central)
        content.setObjectName("NMShellContent")
        content.setStyleSheet(self._shell_content_qss(self._modo))
        self._content_widget = content
        content_lay = QHBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        # Área derecha: header de contexto + stack con fade
        right = QWidget(content)
        right.setStyleSheet("background: transparent;")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        # BL-07: el back + título de módulo viven en NMWindowChrome (titlebar),
        # no en una banda de 56px aparte. Ver _open_module/_go_home.
        self._stack = NMFadeWidget(right)
        right_lay.addWidget(self._stack, 1)

        content_lay.addWidget(right, 1)
        main_layout.addWidget(content, 1)

        # ── Home ──────────────────────────────────────────────────────────────
        from app.home_qt import HomeView

        self._home = HomeView(
            modo=self._modo,
            on_module_open=self._open_module,
            get_status_fn=self._get_module_status,
            username=self._nombre,
        )
        self._home._theme_switch_requested.connect(self._toggle_theme)
        # Estado de sync del footer: el hilo emite el signal, el slot corre en UI.
        self._sync_status_sig.connect(self._home.set_sync_status)
        self._stack.addWidget(self._home)
        self._navigate_to(self._home)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _navigate_to(self, widget: QWidget):
        """Navega a un widget (Home o módulo) con transición fade v3."""
        if isinstance(widget, str):
            self._open_module(widget)
            return
        if widget is self._stack.currentWidget():
            return
        self._stack.setCurrentWidget(widget)

    def _open_module(self, module_id: str):
        if module_id == "tcc":
            module_id = "registro"
        if module_id == "mas":
            NMToast.display(self, "Más herramientas próximamente.", variant="info")
            return
        if module_id not in _MODULE_MAP:
            return

        title_default, icon = _MODULE_UI_META.get(module_id, ("", ""))
        title = t(f"text.home.module.{module_id}.title", title_default)

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
            self._chrome.set_module_context(title, icon, self._go_home)
            return

        mod_path, cls_name = _MODULE_MAP[module_id]
        try:
            module = importlib.import_module(mod_path)
            cls = getattr(module, cls_name)
        except (ImportError, AttributeError) as e:
            NMToast.display(self, f"Módulo '{module_id}' no disponible aún.\n{e}", variant="error")
            return

        # Instanciar y conectar señal back. Pasamos parent=self._stack para
        # que el módulo NUNCA quede como widget top-level momentáneo (mini-ventana
        # negra al abrir/rethemear). El mismo patrón está en hub/main_qt.py.
        instance = cls(modo=self._modo, show_header=False, parent=self._stack)
        instance.back_requested.connect(self._go_home)
        self._module_cache[module_id] = instance
        self._stack.addWidget(instance)

        self._current_module = instance
        self._navigate_to(instance)
        if hasattr(instance, "on_enter"):
            instance.on_enter()
        self._chrome.set_module_context(title, icon, self._go_home)

    def _go_home(self):
        if self._current_module:
            if hasattr(self._current_module, "on_leave"):
                self._current_module.on_leave()
            self._current_module = None

        self._navigate_to(self._home)
        self._home.refresh_statuses()
        # BL-07: limpiar el contexto de módulo en la titlebar al volver a Home.
        self._chrome.clear_module_context()

    def _back_to_home(self):
        self._go_home()

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _toggle_theme(self, checked: bool | None = None):
        if isinstance(checked, bool):
            new_modo = "light_hybrid" if checked else "dark_hybrid"
        else:
            new_modo = "light_hybrid" if "dark" in self._modo else "dark_hybrid"
        new_modo = norm_modo(new_modo)
        if new_modo == self._modo:
            _persist_theme(new_modo)
            return
        self._apply_global_style(new_modo)
        self._tm.switch_mode(new_modo)
        self._modo = new_modo
        _persist_theme(new_modo)
        # NMWindowChrome recibe el tema vía ThemeManager.theme_changed (ya conectado).

    def _apply_global_style(self, modo: str | None = None):
        modo = modo or self._modo
        QApplication.instance().setPalette(app_palette(modo))
        QApplication.instance().setStyleSheet(stylesheet_base(modo))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_global_style(self._modo)
        self._tm.switch_mode(self._modo)
        cw = self.centralWidget()
        if isinstance(cw, _ShellWidget):
            cw.set_shell_modo(self._modo)
        if hasattr(self, "_chrome"):
            self._chrome._apply_theme(self._modo)
        # Re-aplicar QSS del content widget con el surface del modo actual
        # (el QSS incluye el hex literal, hay que refrescarlo en cada switch).
        if hasattr(self, "_content_widget"):
            self._content_widget.setStyleSheet(self._shell_content_qss(self._modo))
        if hasattr(self, "_home"):
            self._home._apply_theme(self._modo)
            self._home.refresh_statuses()
        if self._current_module is not None:
            if hasattr(self._current_module, "_on_theme"):
                self._current_module._on_theme(self._modo)

    @staticmethod
    def _shell_content_qss(modo: str) -> str:
        """QSS para el content widget: pinta surface (mockup .window bg)."""
        surf_hex = v3c("surface", modo).name()
        return f"QWidget#NMShellContent {{ background-color: {surf_hex}; }}"

    def _apply_initial_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    # ── Ventana ────────────────────────────────────────────────────────────────

    def _center_window(self):
        configure_adaptive_window(self)

    def _apply_icon(self):
        try:
            from shared.assets import obtener_ruta_asset, APP_ICON

            ico_path = obtener_ruta_asset(APP_ICON)
        except ImportError:
            ico_path = obtener_ruta_recurso("NM_icon.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

    def closeEvent(self, event):
        self._on_close(event)

    def _on_close(self, event=None):
        """Cierra la app. Cerrar la ventana cierra la app de verdad: no queda
        ningún proceso oculto en segundo plano (autostart/bandeja removido)."""
        if (
            getattr(self, "_really_quit", False)
            or os.environ.get("NM_TEST_FORCE_CLOSE") == "1"
            or getattr(self, "_visual_qa", False)
        ):
            avisos_daemon.detener()
            if event:
                event.accept()
            QApplication.instance().quit()
            return

        # Cierre real. Si hay un timer corriendo, avisar antes para no detenerlo
        # sin querer.
        timer_active = False
        if self._current_module and hasattr(self._current_module, "_running"):
            timer_active = getattr(self._current_module, "_running", False)
        if timer_active:
            resp = QMessageBox.question(
                self,
                "Timer activo",
                "Hay un timer en curso. Si cerrás NeuroMood, se detendrá.\n"
                "¿Querés cerrar igual?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                if event:
                    event.ignore()
                return

        self._really_quit = True
        avisos_daemon.detener()
        if event:
            event.accept()
        QApplication.instance().quit()

    def _restaurar_ventana(self):
        """Trae la ventana al frente (bandeja / segunda instancia)."""
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def _force_quit(self):
        """Cierre real solicitado desde la bandeja ('Salir').

        Marca el flag, detiene el daemon y cierra la app de verdad. Sin esto,
        ``_salir`` solo quitaba el ícono de bandeja y el proceso Qt quedaba vivo
        con la ventana oculta → proceso "invisible" que solo se cerraba por el
        Administrador de tareas.
        """
        self._really_quit = True
        try:
            avisos_daemon.detener()
        except Exception:
            _log.debug("force_quit: detener() del daemon falló")
        self.close()
        QApplication.instance().quit()

    # ── DWM shadow + resize handles (frameless) ───────────────────────────────

    def _apply_dwm_shadow(self):
        pass

    def nativeEvent_disabled(self, event_type, message):
        """Maneja WM_NCHITTEST para resize handles en ventana frameless."""
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            try:
                import ctypes
                import ctypes.wintypes

                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == 0x0084:  # WM_NCHITTEST
                    BORDER = 8
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    geo = self.geometry()
                    lx, ly = geo.x(), geo.y()
                    rx, ry = geo.right(), geo.bottom()
                    on_l = x < lx + BORDER
                    on_r = x > rx - BORDER
                    on_t = y < ly + BORDER
                    on_b = y > ry - BORDER
                    if on_t and on_l:
                        return True, 13  # HTTOPLEFT
                    if on_t and on_r:
                        return True, 14  # HTTOPRIGHT
                    if on_b and on_l:
                        return True, 16  # HTBOTTOMLEFT
                    if on_b and on_r:
                        return True, 17  # HTBOTTOMRIGHT
                    if on_t:
                        return True, 12  # HTTOP
                    if on_b:
                        return True, 15  # HTBOTTOM
                    if on_l:
                        return True, 10  # HTLEFT
                    if on_r:
                        return True, 11  # HTRIGHT
            except Exception:
                pass
        return super().nativeEvent(event_type, message)

    # ── Sync ──────────────────────────────────────────────────────────────────

    def _sync_background(self):
        try:
            from shared.sync import sync_al_abrir, _get_client

            self._sync_status_sig.emit("Sincronizando…", "warn")

            def _run_sync():
                try:
                    sync_al_abrir()
                    online = _get_client() is not None
                except Exception:
                    online = False
                if online:
                    self._sync_status_sig.emit("Sincronizado", "ok")
                else:
                    self._sync_status_sig.emit("Sin conexión", "danger")

            threading.Thread(target=_run_sync, daemon=True).start()

            # F6.B: Check pending consent 7 days warning
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            pending_path = pathlib.Path(appdata) / "NeuroMood" / "pending_consent.json"
            if pending_path.exists():
                mtime = pending_path.stat().st_mtime
                import time

                if (time.time() - mtime) > 7 * 24 * 3600:
                    from shared.theme_qt import WARNING_C

                    NMToast.display(
                        self,
                        "Aún no se pudo registrar tu consentimiento en la nube. Verificá tu conexión.",
                        color=WARNING_C,
                        duration=5000,
                    )
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
                # Promedio REAL del día (no el último registro): con varios
                # registros, mostrar solo el último ocultaba los negativos y el
                # hero decía "10 / Estado positivo" con datos mixtos (feedback
                # owner v1.0). El estado del badge sale de este promedio.
                row = conn.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE fecha=?",
                    (hoy,),
                ).fetchone()
                if row and row[0] is not None:
                    avg = float(row[0])
                    result = (
                        f"{int(avg)}/10" if avg == int(avg) else f"{avg:.1f}/10"
                    )
                else:
                    result = ""
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
                total = conn.execute("SELECT COUNT(*) FROM checklist_tareas").fetchone()[0]
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
                n = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE activo=1").fetchone()[0]
                result = f"{n} activo{'s' if n > 1 else ''}" if n else ""
            conn.close()
            return result
        except Exception:
            _log.debug("Could not get module status for %s", module_id)
        return ""


# ── Onboarding gate ───────────────────────────────────────────────────────────


def _is_onboarded() -> bool:
    """True si identidad Auth real, token y legal_consent.json existen."""
    try:
        from shared.db import leer_config

        patient_id = leer_config("patient_id")
        auth_user_id = leer_config("auth_user_id")
        access_token = leer_config("auth_access_token")
        if not patient_id or not auth_user_id or not access_token:
            return False
        if patient_id != auth_user_id:
            return False
        if access_token.strip().lower() == "offline":
            return False
    except Exception:
        return False

    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    consent = pathlib.Path(appdata) / "NeuroMood" / "legal_consent.json"
    return consent.exists()


def _show_onboarding_required():
    """Muestra un diálogo bloqueante cuando falta onboarding y termina la app."""
    from PyQt6.QtWidgets import QMessageBox

    dlg = QMessageBox()
    dlg.setWindowTitle("Configuración inicial requerida")
    dlg.setIcon(QMessageBox.Icon.Warning)
    dlg.setText(
        "NeuroMood Suite requiere completar la configuracion inicial\n"
        "antes de poder usarse.\n\n"
        "Ejecuta el instalador de NeuroMood Suite y completa\n"
        "el proceso de registro: cuenta, identidad y consentimiento legal.\n\n"
        "Si ya lo completaste y el problema persiste,\n"
        "contacta al soporte de NeuroMood."
    )
    dlg.setStandardButtons(QMessageBox.StandardButton.Close)
    dlg.exec()
    sys.exit(0)


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    from shared.crash_log import setup as _crash_setup

    _crash_setup("suite")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Suite")
    app.setOrganizationName("NeuroMood")
    install_transient_qt_window_guard(app.applicationName())
    # AA_UseHighDpiPixmaps fue eliminado en PyQt6 6.x — DPI se maneja automáticamente

    # ── Instancia única ────────────────────────────────────────────────────
    # Con la app minimizada en bandeja, relanzarla abría OTRO proceso (no hay
    # guard) → procesos acumulados/invisibles. Si ya hay una instancia, le
    # pedimos que se muestre y salimos. Se omite en QA/smoke (corren en paralelo).
    _single_server = None
    from shared.visual_qa import visual_qa_enabled as _vqa

    if not (
        _vqa()
        or os.environ.get("NM_QA_SMOKE") == "1"
        or os.environ.get("NM_TEST_FORCE_CLOSE") == "1"
    ):
        try:
            from PyQt6.QtNetwork import QLocalServer, QLocalSocket

            _SINGLETON = "NeuroMoodSuite_singleton"
            _probe = QLocalSocket()
            _probe.connectToServer(_SINGLETON)
            if _probe.waitForConnected(300):
                _probe.write(b"activate")
                _probe.flush()
                _probe.waitForBytesWritten(300)
                _probe.disconnectFromServer()
                _log.info("NeuroMood Suite ya está corriendo — activando esa instancia.")
                sys.exit(0)
            _probe.abort()
            QLocalServer.removeServer(_SINGLETON)  # limpia un named-pipe stale
            _single_server = QLocalServer()
            if not _single_server.listen(_SINGLETON):
                _single_server = None
        except Exception:
            _log.debug("Single-instance guard no disponible — continuando")
            _single_server = None

    # Cargar fuentes del handoff (Newsreader, Manrope, JetBrains Mono) antes
    # de construir widgets. Si los .ttf no están en assets/fonts/, fonts.py
    # cae a fallback de sistema sin crashear.
    try:
        from shared.fonts import load_fonts

        load_fonts()
    except Exception:
        _log.debug("load_fonts() falló — continuando con fallback de sistema")

    # ── Garantizar AppData Suite con credenciales base ────────────────────
    # Fallback de autogestión: si el installer no desplegó el .env (versión
    # vieja del installer), lo crea leyendo las credenciales de shared.config.
    try:
        import os as _os
        import pathlib as _pl
        from shared.config import supabase_url as _su_url, supabase_key as _su_key
        _nm_dir = _pl.Path(_os.environ.get("APPDATA", str(_pl.Path.home() / "AppData" / "Roaming"))) / "NeuroMood"
        _nm_dir.mkdir(parents=True, exist_ok=True)
        _env_path = _nm_dir / ".env"
        _existing: dict = {}
        if _env_path.exists():
            for _ln in _env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                _ln = _ln.strip()
                if not _ln or _ln.startswith("#") or "=" not in _ln:
                    continue
                _k, _, _v = _ln.partition("=")
                _existing[_k.strip()] = _v.strip()
        _changed = False
        _url, _key = _su_url(), _su_key()
        if _url and "SUPABASE_URL" not in _existing:
            _existing["SUPABASE_URL"] = _url
            _changed = True
        if _key and "SUPABASE_KEY" not in _existing:
            _existing["SUPABASE_KEY"] = _key
            _changed = True
        if _changed or not _env_path.exists():
            _env_path.write_text(
                "\n".join(f"{k}={v}" for k, v in _existing.items() if v) + "\n",
                encoding="utf-8",
            )
            from shared import config as _cfg_mod
            _cfg_mod._cache.clear()
    except Exception:
        pass

    # ── Inicializar DB antes del lock (leer config) ────────────────────────
    from shared.visual_qa import visual_qa_enabled

    if not visual_qa_enabled():
        inicializar_tablas()

    # ── Gate de onboarding (Fase 4 — SUITE_ONBOARDING_PLAN.md) ───────────
    # Muestra la pantalla de primer arranque si falta identidad Auth real,
    # auth_access_token o legal_consent.json. Se omite en modo QA.
    if not visual_qa_enabled() and not _is_onboarded():
        from app.onboarding_qt import run_onboarding

        if not run_onboarding():
            sys.exit(0)
        if not _is_onboarded():
            _show_onboarding_required()

    window = NeuroMoodApp()
    window.show()
    # Esquinas redondeadas nativas (Win11; no-op Win10) — flags ya definitivos.
    from shared.adaptive_layout_qt import apply_native_rounded_corners

    apply_native_rounded_corners(window)

    # Si somos la instancia primaria, atender pedidos de "mostrate" de
    # instancias nuevas (en vez de dejarlas abrir otro proceso).
    if _single_server is not None:
        def _on_second_instance():
            sock = _single_server.nextPendingConnection()
            if sock is not None:
                sock.readAll()
                sock.disconnectFromServer()
            window._restaurar_ventana()

        _single_server.newConnection.connect(_on_second_instance)
        window._single_server = _single_server  # mantener viva la referencia

    # ── Hook de QA Smoke (Fase 2) ──────────────────────────────────────────
    if os.environ.get("NM_QA_SMOKE") == "1":
        print("QA Smoke Test: programando cierre automático en 3 segundos.")
        QTimer.singleShot(3000, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
