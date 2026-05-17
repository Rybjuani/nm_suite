"""uninstaller_pro.py — Desinstalador Hub (PyQt6)"""
import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, aplicar_captionbar_installer, stylesheet_installer,
        InstallerShell, TEAL, VIOLET,
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

REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodHub"

_SS = stylesheet_installer()   # design system premium unificado

try:
    from shared.components_qt import NMInstallProgress, NMDataPreserveCard
except ImportError:
    _root_cmp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root_cmp not in sys.path:
        sys.path.insert(0, _root_cmp)
    from shared.components_qt import NMInstallProgress, NMDataPreserveCard

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
    current_pid = os.getpid()
    for proc_name in ["NeuroMood Hub.exe"]:
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
            if pid.isdigit() and int(pid) != current_pid:
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
    for nombre in ["NeuroMood Hub"]:
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
            target_l = target.lower()
            if (
                "neuromood hub pro" in target_l
                or "hub profesional" in target_l
                or "hubprofesional" in target_l
            ):
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
    self_exe = Path(sys.executable)
    self_dir = self_exe.parent
    install_dir = detectar_install_dir()
    if (self_dir / "_internal").exists():
        temp_root = Path(temp_dir) / f"_nm_pro_desinstalar_{os.getpid()}"
        temp_bundle = temp_root / self_dir.name
        temp_exe = temp_bundle / self_exe.name
        try:
            if temp_root.exists():
                shutil.rmtree(temp_root, ignore_errors=True)
            shutil.copytree(self_dir, temp_bundle)
            subprocess.Popen([str(temp_exe), "--install-dir", install_dir, "--from-temp"])
            return True
        except Exception:
            return False
    temp_exe = str(Path(temp_dir) / "_nm_pro_desinstalar.exe")
    if os.path.normcase(str(self_exe)) == os.path.normcase(temp_exe):
        return False
    try:
        shutil.copy2(str(self_exe), temp_exe)
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
            self.progress_signal.emit(0.10, "Cerrando NeuroMood Hub...")
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
            appdata_pro = str(Path(os.environ.get("APPDATA", "")) / "NeuroMoodHub")
            vaciar_carpeta(appdata_pro)
            self.progress_signal.emit(0.90, "Finalizando...")
            lanzar_bat_limpieza(self._install_dir)
            self.progress_signal.emit(1.0, "¡Desinstalacion completada!")
            self.done_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))


# ── DesinstaladorPro ──────────────────────────────────────────────────────────

class DesinstaladorPro(InstallerShell):
    APP_NAME = "Desinstalador Hub"
    WINDOW_SIZE = (620, 420)
    WINDOW_ROLE = ""
    STEPS = ["Confirmar", "Eliminando", "Finalizado"]
    _STEPPER_ACCENT = "error"   # tono rojo de alerta para acción destructiva

    def __init__(self):
        super().__init__()
        self._install_dir = detectar_install_dir()
        self._worker: _ProUninstWorker | None = None
        self._build_shell()
        self._show_confirm()

    def _build_confirm(self, page, layout):
        title = QLabel("Desinstalador Hub")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(8)

        desc = QLabel(
            f"Se eliminaran los archivos de instalacion del NeuroMood Hub\n"
            f"de tu computadora.\n\nCarpeta: {self._install_dir}"
        )
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        layout.addWidget(desc)
        layout.addStretch()

    def _show_confirm(self):
        self._add_page(lambda page, lay: self._build_confirm(page, lay))
        self.btn_sig.setText("Desinstalar")
        self.btn_sig.clicked.connect(self._iniciar)

    def _iniciar(self):
        self.btn_sig.setEnabled(False)
        self.btn_sig.setText("Desinstalando...")
        self._add_page(lambda page, lay: self._build_progress(page, lay))
        self._ir_a(self._pagina + 1)

        self._worker = _ProUninstWorker(self._install_dir, self)
        self._worker.progress_signal.connect(self._set_progress)
        self._worker.done_signal.connect(self._on_done)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _build_progress(self, page, layout):
        title = QLabel("Desinstalando NeuroMood Hub...")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(12)
        self._install_progress = NMInstallProgress(accent_key="violet")
        self._install_progress.set_progress(0, "Preparando...")
        self._install_progress.set_lines([
            "○ Preparando desinstalación NeuroMood Hub",
            "○ Cerrando procesos",
            "○ Eliminando archivos",
        ])
        layout.addWidget(self._install_progress)
        self._pbar = self._install_progress
        self._status_lbl = self._install_progress._label
        layout.addStretch()

    def _set_progress(self, v: float, t: str):
        if hasattr(self, "_install_progress"):
            self._install_progress.set_progress(int(v * 100), t)
            self._install_progress.append_line(f"↻ {t}")
        else:
            self._pbar.setValue(int(v * 100))
            self._status_lbl.setText(t)

    def _on_done(self):
        self._install_progress.set_progress(100, "Desinstalacion completada")
        self._install_progress.append_line("✓ Desinstalacion completada")
        self._add_page(lambda page, lay: self._build_done(page, lay))
        self._ir_a(self._pagina + 1)
        self.btn_sig.setEnabled(True)
        self.btn_sig.setText("Cerrar")
        try:
            self.btn_sig.clicked.disconnect()
        except TypeError:
            pass
        self.btn_sig.clicked.connect(self.close)
        QApplication.instance().processEvents()
        delay = 5000 if os.environ.get("NM_VISUAL_QA") == "1" else 1500
        QTimer.singleShot(delay, self.close)
        QTimer.singleShot(delay + 500, QApplication.instance().quit)

    def _build_done(self, page, layout):
        title = QLabel("Desinstalacion completada")
        title.setStyleSheet(f"color: {SUCCESS}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(8)
        desc = QLabel(
            "NeuroMood Hub fue eliminado de este equipo.\n"
            "La configuracion local se preservo segun la opcion seleccionada."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        layout.addWidget(desc)
        layout.addSpacing(10)
        layout.addWidget(NMDataPreserveCard(
            "Datos preservados",
            "Credenciales locales, registros y configuracion",
            checked=True,
        ))
        layout.addStretch()

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
