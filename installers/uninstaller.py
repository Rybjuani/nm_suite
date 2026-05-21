"""uninstaller.py — Desinstalador Suite (PyQt6)"""
import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QCheckBox, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, BG_ELEVATED, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, TEXT_ON_ACCENT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, TEAL, VIOLET, GRAD_FROM, GRAD_MID, GRAD_TO,
        DANGER_FROM, DANGER_TO, DANGER_SOFT, _rgba,
        recurso, aplicar_captionbar_installer, stylesheet_installer,
        InstallerShell,
    )
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, BG_ELEVATED, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, TEXT_ON_ACCENT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, TEAL, VIOLET, GRAD_FROM, GRAD_MID, GRAD_TO,
        DANGER_FROM, DANGER_TO, DANGER_SOFT, _rgba,
        recurso, aplicar_captionbar_installer, stylesheet_installer,
        InstallerShell,
    )

NM_PROCESOS  = ["NeuroMood Suite.exe"]
APPS_NOMBRES = ["NeuroMood Suite"]

_SS = stylesheet_installer()   # design system premium unificado

try:
    from shared.components_qt import NMDataPreserveCard, NMInstallProgress
    _HAS_PRESERVE_CARD = True
except ImportError:
    try:
        _root2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root2 not in sys.path:
            sys.path.insert(0, _root2)
        from shared.components_qt import NMDataPreserveCard, NMInstallProgress
        _HAS_PRESERVE_CARD = True
    except ImportError:
        _HAS_PRESERVE_CARD = False

# ── Lógica de negocio (preservada exacta) ─────────────────────────────────────

def _es_ruta_protegida(ruta: str) -> bool:
    ruta_norm = os.path.normpath(ruta).lower()
    protegidas = [
        os.path.normpath(os.environ.get("PROGRAMFILES", r"C:\Program Files")).lower(),
        os.path.normpath(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")).lower(),
        os.path.normpath(os.environ.get("WINDIR", r"C:\Windows")).lower(),
        os.path.normpath(r"C:\ProgramData").lower(),
    ]
    return any(ruta_norm.startswith(p) for p in protegidas)

def _es_ruta_neuromood(ruta: str, marcadores=None) -> bool:
    if marcadores is None:
        marcadores = [
            "NeuroMood Suite.exe",
            "Desinstalador Suite.exe",
            "install_path.txt",
            "_nm_install_manifest.json",
            ".neuromood_install_manifest.json",
        ]
    p = Path(ruta)
    if not p.exists() or not p.is_dir():
        return False
    return any((p / m).exists() for m in marcadores)


def _es_appdata_neuromood(ruta: str) -> bool:
    p = Path(ruta)
    if not p.exists() or not p.is_dir():
        return False
    appdata = Path(os.environ.get("APPDATA", "")).resolve()
    try:
        p.resolve().relative_to(appdata)
    except Exception:
        return False
    if p.name != "NeuroMood":
        return False
    return any((p / marker).exists() for marker in ("nm_data.db", ".env", "legal_consent.json", "logs"))

def detectar_install_dir() -> str:
    if "--install-dir" in sys.argv:
        idx = sys.argv.index("--install-dir")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodSuite",
        ) as k:
            val, _ = winreg.QueryValueEx(k, "InstallLocation")
            if val:
                return val
    except Exception:
        pass
    self_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    txt = self_dir / "install_path.txt"
    if txt.exists():
        return txt.read_text(encoding="utf-8").strip()
    return str(self_dir)


def matar_procesos_neuromood(install_dir: str):
    current_pid = os.getpid()
    for proc_name in NM_PROCESOS:
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
    import winreg
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodSuite"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            winreg.DeleteKey(hive, key_path)
        except Exception:
            pass


def eliminar_accesos():
    escritorio = Path(os.path.expanduser("~")) / "Desktop"
    start_menu = (Path(os.environ.get("APPDATA", "")) /
                  "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood")
    for nombre in APPS_NOMBRES:
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
            if "NeuroMood" in target or "neuromood" in target.lower():
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


def vaciar_carpeta(carpeta: str, permitir_appdata: bool = False):
    path = Path(carpeta)
    if not path.exists():
        return
    if _es_ruta_protegida(carpeta):
        raise RuntimeError(f"Ruta protegida: {carpeta}")
    segura = _es_ruta_neuromood(carpeta) or (permitir_appdata and _es_appdata_neuromood(carpeta))
    if not segura:
        raise RuntimeError(f"Ruta no reconocida como NeuroMood: {carpeta}")
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def _validar_ruta_cleanup(install_dir: str):
    path = Path(install_dir)
    if _es_ruta_protegida(install_dir):
        raise RuntimeError(f"Ruta protegida: {install_dir}")
    if path.exists() and not _es_ruta_neuromood(install_dir):
        raise RuntimeError(f"Ruta no reconocida como NeuroMood: {install_dir}")


def lanzar_bat_limpieza(install_dir: str, appdata_dir: str, eliminar_appdata: bool = True):
    _validar_ruta_cleanup(install_dir)

    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
    temp_exe = str(Path(temp_dir) / "_nm_desinstalar.exe")
    bat = Path(temp_dir) / "_nm_cleanup.bat"
    
    install_dir_clean = install_dir.rstrip("\\/")
    appdata_dir_clean = appdata_dir.rstrip("\\/")

    self_exe = Path(sys.executable)
    temp_root_to_delete = None
    if str(self_exe).startswith(temp_dir) and "_nm_desinstalar_" in str(self_exe):
        parts = self_exe.parts
        for i, part in enumerate(parts):
            if part.startswith("_nm_desinstalar_"):
                temp_root_to_delete = str(Path(*parts[:i+1])).rstrip("\\/")
                break

    lines = [
        "@echo off",
        f'cd /d "{temp_dir}"',
        "ping 127.0.0.1 -n 5 > nul",
        f'rd /s /q "{install_dir_clean}" 2>nul',
    ]
    if eliminar_appdata:
        lines.append(f'rd /s /q "{appdata_dir_clean}" 2>nul')
    if temp_root_to_delete:
        lines.append(f'rd /s /q "{temp_root_to_delete}" 2>nul')
    lines += [f'del /f /q "{temp_exe}" 2>nul', 'del /f /q "%~f0"']
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
        temp_root = Path(temp_dir) / f"_nm_desinstalar_{os.getpid()}"
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
    temp_exe = str(Path(temp_dir) / "_nm_desinstalar.exe")
    if os.path.normcase(str(self_exe)) == os.path.normcase(temp_exe):
        return False
    try:
        shutil.copy2(str(self_exe), temp_exe)
        subprocess.Popen([temp_exe, "--install-dir", install_dir, "--from-temp"])
        return True
    except Exception:
        return False


# ── Worker ────────────────────────────────────────────────────────────────────

class _UninstWorker(QThread):
    progress_signal = pyqtSignal(float, str)
    done_signal     = pyqtSignal()
    error_signal    = pyqtSignal(str)

    def __init__(self, install_dir: str, conservar: bool, parent=None):
        super().__init__(parent)
        self._install_dir = install_dir
        self._conservar = conservar

    def run(self):
        try:
            self.progress_signal.emit(0.10, "Cerrando aplicaciones...")
            matar_procesos_neuromood(self._install_dir)
            time.sleep(1.5)
            self.progress_signal.emit(0.25, "Eliminando accesos directos...")
            eliminar_accesos()
            self.progress_signal.emit(0.45, "Limpiando registro de Windows...")
            eliminar_registro_windows()
            self.progress_signal.emit(0.60, "Cerrando Explorer...")
            cerrar_explorer_en(self._install_dir)
            time.sleep(0.5)
            appdata_nm = str(Path(os.environ.get("APPDATA", "")) / "NeuroMood")
            self.progress_signal.emit(0.75, "Eliminando archivos de instalacion...")
            vaciar_carpeta(self._install_dir)
            if not self._conservar:
                self.progress_signal.emit(0.85, "Eliminando datos de usuario...")
                vaciar_carpeta(appdata_nm, permitir_appdata=True)
            self.progress_signal.emit(0.90, "Finalizando...")
            lanzar_bat_limpieza(self._install_dir, appdata_nm, eliminar_appdata=not self._conservar)
            self.progress_signal.emit(1.0, "¡Desinstalacion completada!")
            self.done_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))


# ── DesinstaladorNeuroMood ────────────────────────────────────────────────────

class DesinstaladorNeuroMood(InstallerShell):
    APP_NAME = "Desinstalador Suite"
    WINDOW_SIZE = (760, 620)
    WINDOW_ROLE = ""
    STEPS = ["Confirmar", "Eliminando", "Finalizado"]
    _STEPPER_ACCENT = "error"   # tono rojo de alerta para acción destructiva

    def __init__(self):
        super().__init__()
        self._install_dir = detectar_install_dir()
        self._worker: _UninstWorker | None = None
        self._build_shell()
        self.btn_ant.clicked.connect(self._anterior)
        self._show_confirm()
        
    def _anterior(self):
        if self._pagina == 0:
            self.close()

    def _fade_to(self, n: int):
        super()._fade_to(n)
        if n == 0:
            self.btn_ant.setVisible(True)
            self.btn_ant.setText("Cancelar")
            self.btn_sig.setText("Desinstalar")
            self.btn_sig.setStyleSheet(
                f"QPushButton {{ border: none; border-radius: 8px;"
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                f"stop:0 {DANGER_FROM}, stop:1 {DANGER_TO});"
                f"color: {TEXT_ON_ACCENT}; font-size: 12px; font-weight: 600;"
                f"padding: 8px 22px; }}"
                f"QPushButton:hover {{ background: {DANGER_FROM}; }}"
                f"QPushButton:disabled {{ background: {BORDER}; color: {TEXT_TERT}; }}"
            )
        elif n == 1:
            self.btn_ant.setVisible(False)
            self.btn_sig.setText("Desinstalando...")
        elif n == 2:
            self.btn_ant.setVisible(False)
            self.btn_sig.setText("Cerrar")
            self.btn_sig.setStyleSheet(
                f"QPushButton {{ border: none; border-radius: 8px;"
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                f"stop:0 {GRAD_FROM}, stop:0.5 {GRAD_MID}, stop:1 {GRAD_TO});"
                f"color: {TEXT_ON_ACCENT}; font-size: 12px; font-weight: 600;"
                f"padding: 8px 22px; }}"
                f"QPushButton:hover {{ background: {GRAD_MID}; }}"
                f"QPushButton:disabled {{ background: {BORDER}; color: {TEXT_TERT}; }}"
            )

    def _build_confirm(self, page, layout):
        from PyQt6.QtCore import Qt as _Qt

        # Header con icono warning v3
        hdr_row = QWidget()
        hdr_row.setStyleSheet("background: transparent;")
        hr = QHBoxLayout(hdr_row)
        hr.setContentsMargins(0, 0, 0, 0)
        hr.setSpacing(16)

        warn_badge = QFrame()
        warn_badge.setFixedSize(52, 52)
        warn_badge.setStyleSheet(
            f"QFrame {{ background: {DANGER_SOFT}; border-radius: 12px; border: none; }}"
        )
        wb_inner = QLabel("⚠", warn_badge)
        wb_inner.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        wb_inner.setGeometry(0, 0, 52, 52)
        wb_inner.setStyleSheet(f"color: {ERROR_C}; font-size: 24px; background: transparent;")
        hr.addWidget(warn_badge)

        titles_col = QVBoxLayout()
        titles_col.setSpacing(4)
        eyebrow_d = QLabel("DESINSTALACIÓN")
        eyebrow_d.setStyleSheet(
            f"color: {ERROR_C}; font-size: 11px; font-weight: 700; letter-spacing: 3px; background: transparent;"
        )
        titles_col.addWidget(eyebrow_d)
        main_title = QLabel("¿Desinstalar NeuroMood Suite?")
        main_title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent;"
        )
        titles_col.addWidget(main_title)
        sub_title = QLabel("Se eliminarán los archivos de instalación de tu computadora.")
        sub_title.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; background: transparent;")
        titles_col.addWidget(sub_title)
        hr.addLayout(titles_col, stretch=1)
        layout.addWidget(hdr_row)
        layout.addSpacing(14)

        # Card carpeta
        folder_card = QFrame()
        folder_card.setStyleSheet(
            f"QFrame {{ background: {BG_SURFACE}; border-radius: 12px; border: 1px solid {BORDER}; }}"
        )
        fc = QVBoxLayout(folder_card)
        fc.setContentsMargins(14, 10, 14, 10)
        fc.setSpacing(2)
        folder_key = QLabel("CARPETA A ELIMINAR")
        folder_key.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;"
        )
        fc.addWidget(folder_key)
        folder_val = QLabel(self._install_dir)
        folder_val.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-family: Consolas, monospace; background: transparent;"
        )
        fc.addWidget(folder_val)
        layout.addWidget(folder_card)
        layout.addSpacing(10)

        # Card "Conservar mis datos"
        if _HAS_PRESERVE_CARD:
            self._preserve_card = NMDataPreserveCard(
                "Conservar mis datos",
                "Registros, historial y configuración de la app",
                checked=True,
            )
            layout.addWidget(self._preserve_card)
        else:
            conservar_card = QFrame()
            conservar_card.setObjectName("ConservarCard")
            conservar_card.setStyleSheet(
                f"QFrame#ConservarCard {{background: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;}}"
            )
            cv = QHBoxLayout(conservar_card)
            cv.setContentsMargins(16, 14, 16, 14)
            cv.setSpacing(14)

            save_badge = QFrame()
            save_badge.setFixedSize(44, 44)
            save_badge.setStyleSheet(
                f"QFrame {{ background: {_rgba(TEAL, 0.14)}; border-radius: 12px; border: none; }}"
            )
            sb_lbl = QLabel("💾", save_badge)
            sb_lbl.setAlignment(_Qt.AlignmentFlag.AlignCenter)
            sb_lbl.setGeometry(0, 0, 44, 44)
            sb_lbl.setStyleSheet("font-size: 20px; background: transparent;")
            cv.addWidget(save_badge)

            text_col = QVBoxLayout()
            tit = QLabel("Conservar mis datos")
            tit.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent;"
            )
            text_col.addWidget(tit)
            sub = QLabel("Registros, historial y configuración local de la app")
            sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 11px; background: transparent;")
            text_col.addWidget(sub)
            cv.addLayout(text_col, stretch=1)

            self._chk_conservar = QCheckBox()
            self._chk_conservar.setChecked(True)
            self._chk_conservar.setStyleSheet(f"""
                QCheckBox {{ spacing: 0px; }}
                QCheckBox::indicator {{
                    width: 44px; height: 24px; border-radius: 12px;
                    border: none; background: {BORDER};
                }}
                QCheckBox::indicator:checked {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {GRAD_FROM}, stop:0.5 {GRAD_MID}, stop:1 {GRAD_TO}
                    );
                }}
            """)
            cv.addWidget(self._chk_conservar, alignment=_Qt.AlignmentFlag.AlignRight)
            layout.addWidget(conservar_card)

        layout.addSpacing(10)

        # Info card — qué pasará al continuar
        info_card = QFrame()
        info_card.setStyleSheet(
            f"QFrame {{ background: {BG_ELEVATED}; border-radius: 12px; border: 1px solid {BORDER}; }}"
        )
        ic = QHBoxLayout(info_card)
        ic.setContentsMargins(14, 10, 14, 10)
        ic.setSpacing(10)
        ic.addWidget(QLabel("ℹ"))
        info_txt = QLabel(
            "Al continuar se cerrarán todas las ventanas de NeuroMood Suite abiertas. "
            "Los accesos directos del escritorio y del menú inicio también serán eliminados."
        )
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
        ic.addWidget(info_txt, stretch=1)
        layout.addWidget(info_card)
        layout.addStretch()

    def _show_confirm(self):
        self._add_page(lambda page, lay: self._build_confirm(page, lay))
        self.btn_sig.setText("Desinstalar")
        self.btn_sig.clicked.connect(self._iniciar)

    def _iniciar(self):
        if hasattr(self, "_preserve_card"):
            conservar = self._preserve_card.is_checked()
        else:
            conservar = self._chk_conservar.isChecked()
        self.btn_sig.setEnabled(False)
        self.btn_sig.setText("Desinstalando...")

        self._add_page(lambda page, lay: self._build_progress(page, lay))
        self._ir_a(self._pagina + 1)

        self._worker = _UninstWorker(self._install_dir, conservar, self)
        self._worker.progress_signal.connect(self._set_progress)
        self._worker.done_signal.connect(self._on_done)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _build_progress(self, page, layout):
        title = QLabel("Desinstalando...")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(16)

        self._install_progress = NMInstallProgress(accent_key="teal")
        self._install_progress.set_progress(0, "Preparando...")
        self._install_progress.set_lines([
            "○ Preparando desinstalación",
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
        # delay = 5000 if os.environ.get("NM_VISUAL_QA") == "1" else 1500
        # QTimer.singleShot(delay, self.close)
        # QTimer.singleShot(delay + 500, QApplication.instance().quit)

    def _build_done(self, page, layout):
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor as _QColor

        conservar = self._worker._conservar if self._worker else True

        # Círculo check
        check_circle = QFrame()
        check_circle.setObjectName("UninstCheckCircle")
        check_circle.setFixedSize(88, 88)
        check_circle.setStyleSheet(
            f"QFrame#UninstCheckCircle {{"
            f"  background: {SUCCESS};"
            f"  border-radius: 44px; border: none;"
            f"}}"
        )
        
        check_lbl = QLabel("✓", check_circle)
        check_lbl.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        check_lbl.setGeometry(0, 0, 88, 88)
        check_lbl.setStyleSheet(
            "color: #ffffff; font-size: 38px; font-weight: 900; background: transparent;"
        )
        layout.addWidget(check_circle, alignment=_Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(14)

        eyebrow_ok = QLabel("LISTO")
        eyebrow_ok.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
        eyebrow_ok.setStyleSheet(
            f"color: {SUCCESS}; font-size: 11px; font-weight: 700;"
            f"letter-spacing: 4px; background: transparent;"
        )
        layout.addWidget(eyebrow_ok)
        layout.addSpacing(4)

        title = QLabel("Desinstalación completada")
        title.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700;"
            f"letter-spacing: -0.5px; background: transparent;"
        )
        layout.addWidget(title)
        layout.addSpacing(8)

        if conservar:
            desc_text = (
                "NeuroMood Suite fue eliminado de este equipo.\n"
                "Tus datos personales se conservaron según la opción seleccionada."
            )
        else:
            desc_text = (
                "NeuroMood Suite fue eliminado de este equipo.\n"
                "Tus datos personales también fueron eliminados."
            )

        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; background: transparent;")
        layout.addWidget(desc)
        layout.addSpacing(16)

        if conservar:
            # Card datos preservados con badge "preservado"
            if _HAS_PRESERVE_CARD:
                pres_outer = QFrame()
                pres_outer.setStyleSheet(
                    f"QFrame {{ background: {BG_SURFACE}; border-radius: 12px; border: 1px solid {BORDER}; }}"
                )
                po = QHBoxLayout(pres_outer)
                po.setContentsMargins(16, 14, 16, 14)
                po.setSpacing(14)

                save_badge = QFrame()
                save_badge.setFixedSize(44, 44)
                save_badge.setStyleSheet(
                    f"QFrame {{ background: {_rgba(TEAL, 0.14)}; border-radius: 12px; border: none; }}"
                )
                sb_lbl = QLabel("💾", save_badge)
                sb_lbl.setAlignment(_Qt.AlignmentFlag.AlignCenter)
                sb_lbl.setGeometry(0, 0, 44, 44)
                sb_lbl.setStyleSheet("font-size: 20px; background: transparent;")
                po.addWidget(save_badge)

                data_col = QVBoxLayout()
                data_col.setSpacing(2)
                data_title = QLabel("Datos conservados")
                data_title.setStyleSheet(
                    f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent;"
                )
                data_col.addWidget(data_title)
                appdata = os.path.join(os.environ.get("APPDATA", "~"), "NeuroMood", "nm_data.db")
                data_path = QLabel(appdata)
                data_path.setStyleSheet(
                    f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace; background: transparent;"
                )
                data_col.addWidget(data_path)
                po.addLayout(data_col, stretch=1)

                preserved_badge = QLabel("preservado")
                preserved_badge.setStyleSheet(
                    f"background: {_rgba(SUCCESS, 0.14)}; color: {SUCCESS}; font-size: 11px; font-weight: 700;"
                    f"border-radius: 999px; padding: 3px 12px; border: none;"
                )
                po.addWidget(preserved_badge, alignment=_Qt.AlignmentFlag.AlignVCenter)
                layout.addWidget(pres_outer)
            else:
                layout.addWidget(NMDataPreserveCard(
                    "Datos preservados",
                    "Registros, historial y configuración local",
                    checked=True,
                ))

            layout.addSpacing(10)
            hint = QLabel("Si en el futuro reinstalás NeuroMood Suite, podrás recuperar tu historial desde estos datos.")
            hint.setWordWrap(True)
            hint.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
            hint.setStyleSheet(f"color: {TEXT_TERT}; font-size: 11px; background: transparent;")
            layout.addWidget(hint)

        layout.addStretch()

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"Error: {msg}")
        self._status_lbl.setStyleSheet(f"color: {ERROR_C}; font-size: 11px;")


if __name__ == "__main__":
    if relanzar_desde_temp():
        sys.exit(0)
    app = QApplication(sys.argv)
    win = DesinstaladorNeuroMood()
    win.show()
    sys.exit(app.exec())
