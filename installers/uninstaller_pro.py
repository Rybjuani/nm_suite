"""uninstaller_pro.py — Desinstalador Hub Profesional NeuroMood (PyQt6)"""
import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, aplicar_captionbar_installer, stylesheet_installer,
    )
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, aplicar_captionbar_installer, stylesheet_installer,
    )

REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodPro"

_SS = stylesheet_installer()   # design system premium unificado

# ── Lógica de negocio (preservada exacta) ─────────────────────────────────────

def detectar_install_dir() -> str:
    if "--install-dir" in sys.argv:
        idx = sys.argv.index("--install-dir")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY) as k:
            val, _ = winreg.QueryValueEx(k, "InstallLocation")
            if val:
                return val
    except Exception:
        pass
    self_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    return str(self_dir)


def matar_procesos_pro(install_dir: str):
    for proc_name in ["NeuroMood Hub Profesional.exe", "HubProfesional.exe"]:
        try:
            subprocess.run(["taskkill", "/F", "/IM", proc_name],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        except Exception:
            pass
    try:
        escaped = install_dir.replace("\\", "\\\\")
        result = subprocess.run(
            ["wmic", "process", "where", f"ExecutablePath like '{escaped}%'", "get", "ProcessId"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
        )
        for line in result.stdout.splitlines():
            pid = line.strip()
            if pid.isdigit():
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
    except Exception:
        pass


def eliminar_registro_windows():
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY)
    except Exception:
        pass


def eliminar_accesos_pro():
    escritorio = Path(os.path.expanduser("~")) / "Desktop"
    start_menu = (Path(os.environ.get("APPDATA", "")) /
                  "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood")
    for nombre in ["NeuroMood Hub Profesional"]:
        try:
            (escritorio / f"{nombre}.lnk").unlink(missing_ok=True)
        except Exception:
            pass
    try:
        for lnk in escritorio.glob("*.lnk"):
            target = ""
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                target = shell.CreateShortcut(str(lnk)).TargetPath
            except Exception:
                pass
            if "Hub Profesional" in target or "HubProfesional" in target:
                lnk.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        shutil.rmtree(str(start_menu), ignore_errors=True)
    except Exception:
        pass


def cerrar_explorer_en(carpeta: str):
    try:
        ps_cmd = (
            '(New-Object -ComObject Shell.Application).Windows() | '
            'Where-Object { $_.LocationURL -match "' +
            carpeta.replace("\\", "/").replace(" ", "%20") +
            '" } | ForEach-Object { $_.Quit() }'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd],
                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
    except Exception:
        pass


def vaciar_carpeta(carpeta: str):
    if not Path(carpeta).exists():
        return
    subprocess.run(f'del /f /s /q "{carpeta}\\*"', shell=True, capture_output=True, timeout=30)
    subprocess.run(f'for /d %x in ("{carpeta}\\*") do @rd /s /q "%x"',
                   shell=True, capture_output=True, timeout=30)
    try:
        Path(carpeta).rmdir()
    except OSError:
        pass


def lanzar_bat_limpieza(install_dir: str):
    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
    temp_exe = str(Path(temp_dir) / "_nm_pro_desinstalar.exe")
    bat = Path(temp_dir) / "_nm_pro_cleanup.bat"
    lines = [
        "@echo off",
        f'cd /d "{temp_dir}"',
        "ping 127.0.0.1 -n 5 > nul",
        f'rd /s /q "{install_dir}" 2>nul',
        f'del /f /q "{temp_exe}" 2>nul',
        'del /f /q "%~f0"',
    ]
    try:
        bat.write_text("\r\n".join(lines), encoding="ascii")
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(None, "open", "cmd.exe", f'/c "{bat}"', temp_dir, 0)
    except Exception:
        pass


def relanzar_desde_temp() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    if "--from-temp" in sys.argv:
        return False
    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
    self_exe = sys.executable
    temp_exe = str(Path(temp_dir) / "_nm_pro_desinstalar.exe")
    if os.path.normcase(self_exe) == os.path.normcase(temp_exe):
        return False
    install_dir = detectar_install_dir()
    try:
        shutil.copy2(self_exe, temp_exe)
        subprocess.Popen([temp_exe, "--install-dir", install_dir, "--from-temp"])
        return True
    except Exception:
        return False


# ── Worker ────────────────────────────────────────────────────────────────────

class _ProUninstWorker(QThread):
    progress_signal = pyqtSignal(float, str)
    done_signal     = pyqtSignal()
    error_signal    = pyqtSignal(str)

    def __init__(self, install_dir: str, parent=None):
        super().__init__(parent)
        self._install_dir = install_dir

    def run(self):
        try:
            self.progress_signal.emit(0.10, "Cerrando Hub Profesional...")
            matar_procesos_pro(self._install_dir)
            time.sleep(1.5)
            self.progress_signal.emit(0.25, "Eliminando accesos directos...")
            eliminar_accesos_pro()
            self.progress_signal.emit(0.45, "Limpiando registro de Windows...")
            eliminar_registro_windows()
            self.progress_signal.emit(0.60, "Cerrando Explorer...")
            cerrar_explorer_en(self._install_dir)
            time.sleep(0.5)
            self.progress_signal.emit(0.80, "Eliminando archivos...")
            vaciar_carpeta(self._install_dir)
            self.progress_signal.emit(0.85, "Eliminando datos de configuracion...")
            appdata_pro = str(Path(os.environ.get("APPDATA", "")) / "NeuroMoodPro")
            vaciar_carpeta(appdata_pro)
            self.progress_signal.emit(0.90, "Finalizando...")
            lanzar_bat_limpieza(self._install_dir)
            self.progress_signal.emit(1.0, "¡Desinstalacion completada!")
            self.done_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))


# ── DesinstaladorPro ──────────────────────────────────────────────────────────

class DesinstaladorPro(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Desinstalar — NeuroMood Hub Profesional")
        self.setFixedSize(480, 300)
        self.setStyleSheet(_SS)
        try:
            self.setWindowIcon(QIcon(recurso("no_symbol.ico")))
        except Exception:
            pass
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - 480) // 2, (screen.height() - 300) // 2)
        aplicar_captionbar_installer(self)

        self._install_dir = detectar_install_dir()
        self._worker: _ProUninstWorker | None = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background: {BG_SECONDARY};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        logo_lbl = QLabel()
        try:
            from PIL import Image as PILImage
            img = PILImage.open(recurso("LOGO.png")).convert("RGBA")
            img.thumbnail((120, 40), PILImage.LANCZOS)
            from PyQt6.QtGui import QImage
            qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height,
                          QImage.Format.Format_RGBA8888)
            logo_lbl.setPixmap(QPixmap.fromImage(qimg))
        except Exception:
            logo_lbl.setText("NeuroMood Hub")
            logo_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 14px; font-weight: bold;")
        hl.addWidget(logo_lbl)
        hl.addStretch()
        layout.addWidget(header)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(sep)

        self._stack = QWidget()
        self._stack_layout = QVBoxLayout(self._stack)
        self._stack_layout.setContentsMargins(28, 16, 28, 16)
        layout.addWidget(self._stack, stretch=1)

        self._show_confirm()

    def _clear_stack(self):
        while self._stack_layout.count():
            item = self._stack_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_confirm(self):
        self._clear_stack()

        title = QLabel("Desinstalar Hub Profesional")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        self._stack_layout.addWidget(title)
        self._stack_layout.addSpacing(8)

        desc = QLabel(
            f"Se eliminaran los archivos de instalacion del Hub Profesional\n"
            f"de tu computadora.\n\nCarpeta: {self._install_dir}"
        )
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        self._stack_layout.addWidget(desc)
        self._stack_layout.addStretch()

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("outline")
        btn_cancel.setFixedSize(110, 34)
        btn_cancel.clicked.connect(self.close)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_uninst = QPushButton("Desinstalar")
        btn_uninst.setFixedSize(130, 34)
        btn_uninst.clicked.connect(self._iniciar)
        btn_row.addWidget(btn_uninst)
        self._stack_layout.addLayout(btn_row)

    def _iniciar(self):
        self._clear_stack()

        title = QLabel("Desinstalando Hub Profesional...")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        self._stack_layout.addWidget(title)
        self._stack_layout.addSpacing(12)

        self._pbar = QProgressBar()
        self._pbar.setRange(0, 100); self._pbar.setValue(0)
        self._stack_layout.addWidget(self._pbar)
        self._stack_layout.addSpacing(6)

        self._status_lbl = QLabel("Preparando...")
        self._status_lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 11px;")
        self._stack_layout.addWidget(self._status_lbl)
        self._stack_layout.addStretch()

        self._worker = _ProUninstWorker(self._install_dir, self)
        self._worker.progress_signal.connect(self._set_progress)
        self._worker.done_signal.connect(self._on_done)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _set_progress(self, v: float, t: str):
        self._pbar.setValue(int(v * 100))
        self._status_lbl.setText(t)

    def _on_done(self):
        self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 16px; font-weight: bold;")
        self._status_lbl.setText("Desinstalacion completada. Cerrando...")
        QApplication.instance().processEvents()
        QTimer.singleShot(1500, self.close)
        QTimer.singleShot(2000, QApplication.instance().quit)

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"Error: {msg}")
        self._status_lbl.setStyleSheet(f"color: {ERROR_C}; font-size: 11px;")


if __name__ == "__main__":
    if relanzar_desde_temp():
        sys.exit(0)
    app = QApplication(sys.argv)
    win = DesinstaladorPro()
    win.show()
    sys.exit(app.exec())
