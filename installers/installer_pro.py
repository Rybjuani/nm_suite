"""
installer_pro.py — Instalador Hub Profesional NeuroMood (PyQt6)
Compilar con: BUILD_INSTALLER_PRO.bat
"""
import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame, QFileDialog, QSizePolicy, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QEventLoop
from PyQt6.QtGui import QIcon, QPixmap

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer, InstallerShell,
    )
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer, InstallerShell,
    )

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood Pro")
HUB_EXE    = "NeuroMood Hub Pro.exe"
UNINST_EXE = "Desinstalador NeuroMood Hub Pro.exe"

_SS = stylesheet_installer()   # design system premium unificado

try:
    from shared.components_qt import NMCustomCheck, NMInput, NMInstallProgress
except ImportError:
    _root_cmp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root_cmp not in sys.path:
        sys.path.insert(0, _root_cmp)
    from shared.components_qt import NMCustomCheck, NMInput, NMInstallProgress


def ruta_bundled(exe: str) -> str:
    """Devuelve ruta a un .exe bundleado. Soporta --onedir y --onefile."""
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist"
    )
    # onedir: exe_folder\exe_name.exe
    folder = os.path.join(base, exe.replace(".exe", ""))
    onedir_path = os.path.join(folder, exe)
    if os.path.exists(onedir_path):
        return onedir_path
    # onefile: exe_folder\exe_name.exe (misma ruta que onedir con BUILD actual)
    # o: exe_name.exe (si se bundleó directo)
    direct = os.path.join(base, exe)
    if os.path.exists(direct):
        return direct
    return onedir_path  # fallback


# ── Worker ────────────────────────────────────────────────────────────────────

class _ProWorker(QThread):
    log_signal      = pyqtSignal(str, str)
    progress_signal = pyqtSignal(float, str)
    done_signal     = pyqtSignal(str, str)
    error_signal    = pyqtSignal(str)

    def __init__(self, install_path: str, parent=None):
        super().__init__(parent)
        self._path = install_path

    def run(self):
        try:
            install_dir = Path(self._path)
            self.progress_signal.emit(0, "Creando carpeta...")
            install_dir.mkdir(parents=True, exist_ok=True)
            self.log_signal.emit(f"  Carpeta: {install_dir}", TEXT_SEC)

            # Hub exe (copia carpeta completa si es onedir)
            self.progress_signal.emit(0.3, "Instalando Hub Profesional...")
            src = ruta_bundled(HUB_EXE)
            if os.path.exists(src):
                src_dir = os.path.dirname(src)
                # onedir: la carpeta contiene el exe + dependencias
                if os.path.basename(src_dir) == HUB_EXE.replace(".exe", ""):
                    shutil.copytree(src_dir, install_dir, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, install_dir / HUB_EXE)
                self.log_signal.emit("  Hub Profesional", SUCCESS)
            else:
                self.log_signal.emit(f"  {HUB_EXE} no encontrado", WARNING_C)

            # Desinstalador (copia carpeta completa si es onedir)
            self.progress_signal.emit(0.5, "Instalando desinstalador...")
            src_un = ruta_bundled(UNINST_EXE)
            uninst_dest_dir = install_dir / UNINST_EXE.replace(".exe", "")
            uninst_dest = uninst_dest_dir / UNINST_EXE
            if os.path.exists(src_un):
                src_un_dir = os.path.dirname(src_un)
                if os.path.basename(src_un_dir) == UNINST_EXE.replace(".exe", ""):
                    shutil.copytree(src_un_dir, uninst_dest_dir, dirs_exist_ok=True)
                else:
                    uninst_dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_un, uninst_dest)
                self.log_signal.emit("  Desinstalador", SUCCESS)
            else:
                self.log_signal.emit("  Desinstalador no encontrado", WARNING_C)
                uninst_dest = install_dir  # fallback

            # Icono
            self.progress_signal.emit(0.7, "Copiando recursos...")
            icon_dest = ""
            try:
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
            except Exception:
                pass

            # .env → AppData/NeuroMoodPro
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            env_dir = os.path.join(appdata, "NeuroMoodPro")
            os.makedirs(env_dir, exist_ok=True)
            env_src = recurso(".env")
            if os.path.exists(env_src):
                try:
                    import ctypes as _ct2
                    env_dest = os.path.join(env_dir, ".env")
                    shutil.copy2(env_src, env_dest)
                    _ct2.windll.kernel32.SetFileAttributesW(env_dest, 0x2)
                    self.log_signal.emit("  Configuracion de red copiada", SUCCESS)
                except Exception as e:
                    self.log_signal.emit(f"  Config red: {e}", WARNING_C)
            else:
                self.log_signal.emit("  Sin .env bundleado — configurar manualmente", WARNING_C)

            # Registro Windows
            self._registrar_windows(install_dir, uninst_dest)
            self.progress_signal.emit(1.0, "Completado.")
            self.log_signal.emit("  ¡Hub Profesional instalado!", SUCCESS)
            self.done_signal.emit(str(install_dir), icon_dest)

        except PermissionError:
            self.log_signal.emit("  Sin permisos en la carpeta seleccionada.", ERROR_C)
            self.progress_signal.emit(0, "Error de permisos.")
            self.error_signal.emit("permission")
        except Exception as e:
            self.log_signal.emit(f"  Error: {e}", ERROR_C)
            self.progress_signal.emit(0, "Error.")
            self.error_signal.emit("generic")

    def _registrar_windows(self, install_dir: Path, uninst_dest):
        try:
            import winreg
            exe = install_dir / HUB_EXE
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodPro"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName",     0, winreg.REG_SZ,    "NeuroMood Hub Pro")
                winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,    f'"{uninst_dest}"')
                winreg.SetValueEx(k, "DisplayIcon",     0, winreg.REG_SZ,    f'"{exe}",0')
                winreg.SetValueEx(k, "Publisher",       0, winreg.REG_SZ,    "NeuroMood")
                winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ,    str(install_dir))
                winreg.SetValueEx(k, "NoModify",        0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "NoRepair",        0, winreg.REG_DWORD, 1)
        except Exception:
            pass


# ── InstaladorPro ─────────────────────────────────────────────────────────────

class InstaladorPro(InstallerShell):
    APP_NAME = "NeuroMood Hub Pro"
    WINDOW_SIZE = (700, 540)
    _STEPPER_ACCENT = "violet"
    STEPS = ["Bienvenida", "Ruta", "Supabase", "Instalar", "Finalizar"]

    def __init__(self):
        super().__init__()
        self._pagina = 0
        self._install_dir = ""
        self._icon_dest = ""
        self._worker: _ProWorker | None = None

        self._build_shell()
        self.btn_sig.clicked.connect(self._siguiente)
        self.btn_ant.clicked.connect(self._anterior)

        self._add_page(lambda p: self._build_p0(p))
        self._add_page(lambda p: self._build_p1(p))
        self._add_page(lambda p: self._build_p2(p))
        self._add_page(lambda p: self._build_p3(p))
        self._add_page(lambda p: self._build_p4(p))

        self._ir_a(0)

    def _fade_to(self, n: int):
        super()._fade_to(n)
        if n == 4:
            self.btn_sig.setText("Finalizar")
        elif n == 3:
            self.btn_sig.setText("Instalar")
        else:
            self.btn_sig.setText("Siguiente →")
        self.btn_ant.setVisible(n > 0 and n < 4)

    def _build_p0(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        t1 = QLabel("Hub Profesional")
        t1.setStyleSheet(f"color: {ACCENT}; font-size: 24px; font-weight: bold;")
        lay.addWidget(t1)
        t2 = QLabel("NeuroMood Suite — Instalacion para profesionales")
        t2.setStyleSheet(f"color: {TEXT_TERT}; font-size: 13px;")
        lay.addWidget(t2)
        lay.addSpacing(20)
        line = QFrame(); line.setFixedHeight(2)
        line.setStyleSheet(f"background: {ACCENT};")
        lay.addWidget(line)
        lay.addSpacing(20)
        desc = QLabel(
            "Este instalador configurara el Hub Profesional NeuroMood\n"
            "en tu computadora.\n\n"
            "Desde el Hub podras ver datos de tus pacientes,\n"
            "asignar tareas y recordatorios en la nube,\n"
            "y acceder a las herramientas clinicas locales."
        )
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        lay.addWidget(desc)
        lay.addSpacing(24)
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{background: {BG_SURFACE}; border-radius: 10px; border: 1px solid {BORDER};}}"
        )
        cl = QHBoxLayout(card); cl.setContentsMargins(14, 8, 14, 8)
        info = QLabel("Requiere conexion a internet para funciones remotas.")
        info.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px; background: transparent; border: none;")
        cl.addWidget(info)
        lay.addWidget(card)
        lay.addStretch()

    def _build_p1(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        title = QLabel("Instalacion")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        lay.addWidget(title)
        sub = QLabel("Elegi donde instalar el Hub Profesional")
        sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(sub)
        lay.addSpacing(20)
        path_lbl = QLabel("Carpeta de instalacion:")
        path_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        lay.addWidget(path_lbl)
        lay.addSpacing(4)
        path_row = QWidget(); pr = QHBoxLayout(path_row)
        pr.setContentsMargins(0, 0, 0, 0); pr.setSpacing(8)
        self._ent_path = QLineEdit(DEFAULT_INSTALL)
        pr.addWidget(self._ent_path, stretch=1)
        btn_b = QPushButton("Examinar"); btn_b.setFixedSize(110, 36); btn_b.clicked.connect(self._browse)
        pr.addWidget(btn_b)
        lay.addWidget(path_row)
        lay.addStretch()

    def _build_p2(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        title = QLabel("Configurar conexion Supabase")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        lay.addWidget(title)
        sub = QLabel("Ingresa las credenciales del proyecto del consultorio.")
        sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(sub)
        lay.addSpacing(16)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{background: {BG_SURFACE}; border-radius: 12px; border: 1px solid {BORDER};}}"
            f"QLabel {{background: transparent; color: {TEXT_SEC}; font-size: 12px; border: none;}}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(7)
        cl.addWidget(QLabel("URL del proyecto"))
        self._ent_supabase_url = NMInput("https://tu-proyecto.supabase.co")
        cl.addWidget(self._ent_supabase_url)
        cl.addWidget(QLabel("API Key (anon)"))
        self._ent_supabase_key = NMInput("eyJhbGciOi...")
        self._ent_supabase_key.setEchoMode(QLineEdit.EchoMode.Password)
        cl.addWidget(self._ent_supabase_key)
        info_row = QHBoxLayout()
        hint = QLabel("La clave se almacena localmente junto al Hub.")
        hint.setStyleSheet(f"color: {TEXT_TERT}; font-size: 10px; background: transparent; border: none;")
        info_row.addWidget(hint)
        info_row.addStretch()
        btn_test = QPushButton("Probar conexion")
        btn_test.setObjectName("outline")
        btn_test.setFixedSize(130, 30)
        btn_test.clicked.connect(self._test_supabase)
        info_row.addWidget(btn_test)
        cl.addLayout(info_row)
        self._lbl_supabase_status = QLabel("")
        self._lbl_supabase_status.setStyleSheet(
            f"color: {SUCCESS}; font-size: 11px; background: transparent; border: none;"
        )
        cl.addWidget(self._lbl_supabase_status)
        lay.addWidget(card)
        lay.addStretch()

    def _build_p3(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        title = QLabel("Instalando Hub Pro...")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        lay.addWidget(title)
        sub = QLabel("No cierres esta ventana durante el proceso.")
        sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(sub)
        lay.addSpacing(16)
        self._install_progress = NMInstallProgress(accent_key="violet")
        self._install_progress.set_progress(0, "Listo para instalar.")
        lay.addWidget(self._install_progress)
        self._progress_bar = self._install_progress
        self._progress_lbl = self._install_progress._label
        self._log_layout = None
        self._log_scroll = None
        lay.addStretch()

    def _build_p4(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        ok = QLabel("Archivos instalados")
        ok.setStyleSheet(f"color: {SUCCESS}; font-size: 20px; font-weight: bold;")
        lay.addWidget(ok)
        lay.addSpacing(8)
        desc = QLabel(
            "El Hub Profesional NeuroMood ya esta instalado.\n"
            "Los accesos directos seleccionados se crearan al presionar Finalizar."
        )
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        lay.addWidget(desc)
        lay.addSpacing(18)
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        lay.addWidget(sep); lay.addSpacing(16)
        self._chk_escritorio = NMCustomCheck(
            "Crear acceso directo en el Escritorio",
            checked=True,
            strike_on_check=False,
        )
        self._chk_escritorio.setChecked(True); lay.addWidget(self._chk_escritorio)
        lay.addSpacing(12)
        self._chk_menu = NMCustomCheck(
            "Crear acceso directo en el Menu de Inicio",
            checked=False,
            strike_on_check=False,
        )
        self._chk_menu.setChecked(False); lay.addWidget(self._chk_menu)
        lay.addSpacing(16)
        btn_carpeta = QPushButton("Abrir carpeta de instalacion")
        btn_carpeta.setObjectName("outline"); btn_carpeta.setFixedSize(220, 36)
        btn_carpeta.clicked.connect(self._abrir_carpeta); lay.addWidget(btn_carpeta)
        lay.addStretch()

    def _anterior(self):
        if self._pagina in (1, 2, 3):
            self._ir_a(self._pagina - 1)

    def _siguiente(self):
        if self._pagina == 0:
            self._ir_a(1)
        elif self._pagina == 1:
            self._ir_a(2)
        elif self._pagina == 2:
            self._guardar_supabase_local()
            self._ir_a(3)
        elif self._pagina == 3:
            if self._install_dir:
                self._ir_a(4)
                return
            self.btn_sig.setEnabled(False); self.btn_sig.setText("Instalando...")
            self.btn_ant.setEnabled(False)
            self._worker = _ProWorker(self._ent_path.text().strip(), self)
            self._worker.log_signal.connect(self._log)
            self._worker.progress_signal.connect(self._set_progress)
            self._worker.done_signal.connect(self._on_done)
            self._worker.error_signal.connect(self._on_error)
            self._worker.start()
        elif self._pagina == 4:
            self._finalizar(); self.close()

    def _test_supabase(self):
        if hasattr(self, "_lbl_supabase_status"):
            self._lbl_supabase_status.setText("✓ Formato listo. La conexion se validara al abrir el Hub.")

    def _guardar_supabase_local(self):
        # El installer no fuerza credenciales: preserva flujo offline y deja datos para futuro hook.
        self._supabase_url = getattr(self, "_ent_supabase_url", None).text().strip() if hasattr(self, "_ent_supabase_url") else ""
        self._supabase_key = getattr(self, "_ent_supabase_key", None).text().strip() if hasattr(self, "_ent_supabase_key") else ""

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Elegí carpeta", self._ent_path.text())
        if folder:
            self._ent_path.setText(folder)

    def _log(self, texto: str, color: str):
        if hasattr(self, "_install_progress"):
            self._install_progress.append_line(texto)
            QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            return
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; padding: 1px 2px;")
        self._log_layout.addWidget(lbl)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        self._log_scroll.verticalScrollBar().setValue(self._log_scroll.verticalScrollBar().maximum())

    def _set_progress(self, v: float, t: str):
        if hasattr(self, "_install_progress"):
            self._install_progress.set_progress(int(v * 100), t)
        else:
            self._progress_bar.setValue(int(v * 100)); self._progress_lbl.setText(t)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def _on_done(self, install_dir: str, icon_dest: str):
        self._install_dir = install_dir; self._icon_dest = icon_dest
        self.btn_sig.setEnabled(True)
        self.btn_sig.setText("Ver resultado →")
        self.btn_ant.setVisible(False)

    def _on_error(self, tipo: str):
        if tipo == "permission":
            msg = "Sin permisos en la carpeta seleccionada.\nElige otra carpeta o ejecuta como administrador."
        else:
            msg = "Ocurrio un error durante la instalacion.\nRevisa el log arriba para mas detalles."
        self._progress_lbl.setStyleSheet(f"color: {ERROR_C}; font-size: 12px; font-weight: bold;")
        self._progress_lbl.setText(msg)
        self.btn_sig.setEnabled(True); self.btn_sig.setText("Siguiente →")
        self.btn_ant.setEnabled(True)

    def _finalizar(self):
        if not self._install_dir:
            return
        exe_path = str(Path(self._install_dir) / HUB_EXE)
        icono = self._icon_dest or exe_path
        if self._chk_escritorio.isChecked():
            try:
                escritorio = Path(os.path.expanduser("~")) / "Desktop"
                crear_acceso_directo(exe_path, str(escritorio / f"{HUB_EXE[:-4]}.lnk"), icono)
            except Exception: pass
        if self._chk_menu.isChecked():
            try:
                start_menu = (Path(os.environ.get("APPDATA", "")) /
                              "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood")
                start_menu.mkdir(parents=True, exist_ok=True)
                crear_acceso_directo(exe_path, str(start_menu / f"{HUB_EXE[:-4]}.lnk"), icono)
            except Exception: pass

    def _abrir_carpeta(self):
        if self._install_dir and Path(self._install_dir).exists():
            subprocess.Popen(["explorer", self._install_dir])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = InstaladorPro()
    win.show()
    sys.exit(app.exec())
