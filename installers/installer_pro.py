"""
installer_pro.py — Instalador Hub (PyQt6)
Compilar con: BUILD_NEUROMOOD.bat
"""
import sys
import os
import shutil
import subprocess
import time
import json
from datetime import datetime, timezone
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

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood Hub")
HUB_EXE    = "NeuroMood Hub.exe"
UNINST_EXE = "Desinstalador Hub.exe"

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


INSTALL_MANIFEST_NAME = ".neuromood_hub_install_manifest.json"
INSTALL_BUILD_ID = "clean-reinstall-2026-05-17"


def _safe_join(base: Path, rel: str) -> Path | None:
    try:
        target = (base / rel).resolve()
        target.relative_to(base.resolve())
        return target
    except Exception:
        return None


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _collect_relative_files(path: Path, base: Path) -> list[str]:
    files: list[str] = []
    if not path.exists():
        return files
    if path.is_file():
        try:
            files.append(path.relative_to(base).as_posix())
        except Exception:
            pass
        return files
    for child in path.rglob("*"):
        if child.is_file():
            try:
                files.append(child.relative_to(base).as_posix())
            except Exception:
                pass
    return files


def _dangerous_install_dir(path: Path) -> bool:
    try:
        resolved = path.expanduser().resolve()
        home = Path.home().resolve()
        anchors = {Path(resolved.anchor).resolve()} if resolved.anchor else set()
        blocked = {home, home.parent, Path(os.environ.get("APPDATA", str(home))).resolve()}
        return resolved in blocked or resolved in anchors
    except Exception:
        return False


def _clean_previous_payload(install_dir: Path, known_items: list[str]) -> list[str]:
    removed: list[str] = []
    if _dangerous_install_dir(install_dir):
        raise RuntimeError(f"Ruta de instalación insegura para reemplazar: {install_dir}")
    manifest = install_dir / INSTALL_MANIFEST_NAME
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            for rel in data.get("files", []):
                target = _safe_join(install_dir, str(rel))
                if target and target.exists():
                    _remove_path(target)
                    removed.append(str(rel))
            for rel in sorted(data.get("dirs", []), key=lambda x: len(str(x)), reverse=True):
                target = _safe_join(install_dir, str(rel))
                if target and target.exists() and target.is_dir():
                    try:
                        target.rmdir()
                    except OSError:
                        pass
        except Exception:
            pass
    for name in known_items:
        target = install_dir / name
        if target.exists():
            _remove_path(target)
            removed.append(name)
    return removed


def _copy_payload_from_bundled_exe(src_exe: str, dest_dir: Path) -> list[str]:
    src = Path(src_exe)
    if not src.exists():
        raise FileNotFoundError(str(src))
    before: set[str] = set(_collect_relative_files(dest_dir, dest_dir))
    src_dir = src.parent
    if src_dir.name == src.stem:
        for child in src_dir.iterdir():
            dest = dest_dir / child.name
            if child.is_dir():
                shutil.copytree(child, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(child, dest)
    else:
        shutil.copy2(src, dest_dir / src.name)
    after: set[str] = set(_collect_relative_files(dest_dir, dest_dir))
    return sorted(after - before)


def _write_install_manifest(install_dir: Path, files: list[str], product: str) -> None:
    dirs = sorted({str(Path(f).parent).replace("\\", "/") for f in files if str(Path(f).parent) != "."})
    payload = {
        "product": product,
        "build_id": INSTALL_BUILD_ID,
        "installed_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "files": sorted(set(files)),
        "dirs": dirs,
    }
    (install_dir / INSTALL_MANIFEST_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

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
            manifest_files: list[str] = []
            uninst_dest_dir = install_dir / UNINST_EXE.replace(".exe", "")
            uninst_dest = uninst_dest_dir / UNINST_EXE

            self.progress_signal.emit(0, "Preparando instalación limpia...")
            install_dir.mkdir(parents=True, exist_ok=True)
            removed = _clean_previous_payload(
                install_dir,
                [
                    HUB_EXE,
                    "_internal",
                    "base_library.zip",
                    "NM_icon.ico",
                    UNINST_EXE.replace(".exe", ""),
                    UNINST_EXE,
                    INSTALL_MANIFEST_NAME,
                ],
            )
            self.log_signal.emit(f"  Carpeta: {install_dir}", TEXT_SEC)
            if removed:
                self.log_signal.emit(f"  Limpieza previa: {len(removed)} elementos reemplazados", SUCCESS)

            # Hub exe (copia carpeta completa si es onedir)
            self.progress_signal.emit(0.3, "Instalando NeuroMood Hub actualizado...")
            src = ruta_bundled(HUB_EXE)
            try:
                copied = _copy_payload_from_bundled_exe(src, install_dir)
                manifest_files.extend(copied)
                if not (install_dir / HUB_EXE).exists():
                    raise FileNotFoundError(f"No quedó instalado {HUB_EXE}")
                self.log_signal.emit("  NeuroMood Hub actualizado", SUCCESS)
            except FileNotFoundError:
                self.log_signal.emit(f"  {HUB_EXE} no encontrado", ERROR_C)
                raise

            # Desinstalador (copia carpeta completa si es onedir)
            self.progress_signal.emit(0.5, "Instalando desinstalador actualizado...")
            src_un = ruta_bundled(UNINST_EXE)
            try:
                if Path(src_un).exists() and Path(src_un).parent.name == UNINST_EXE.replace(".exe", ""):
                    before = set(_collect_relative_files(install_dir, install_dir))
                    shutil.copytree(Path(src_un).parent, uninst_dest_dir, dirs_exist_ok=True)
                    after = set(_collect_relative_files(install_dir, install_dir))
                    manifest_files.extend(sorted(after - before))
                    uninst_dest = uninst_dest_dir / UNINST_EXE
                elif Path(src_un).exists():
                    uninst_dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_un, uninst_dest)
                    manifest_files.append(uninst_dest.relative_to(install_dir).as_posix())
                else:
                    raise FileNotFoundError(src_un)
                self.log_signal.emit("  Desinstalador actualizado", SUCCESS)
            except Exception as e:
                self.log_signal.emit(f"  Desinstalador no disponible: {e}", WARNING_C)
                uninst_dest = install_dir  # fallback

            # Icono
            self.progress_signal.emit(0.7, "Copiando recursos...")
            icon_dest = ""
            try:
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
                manifest_files.append("NM_icon.ico")
            except Exception:
                pass

            # .env → AppData/NeuroMoodHub
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            env_dir = os.path.join(appdata, "NeuroMoodHub")
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
                self.log_signal.emit("  Configuracion de red no incluida en el paquete", WARNING_C)

            try:
                _write_install_manifest(install_dir, manifest_files, "NeuroMood Hub")
            except Exception as e:
                self.log_signal.emit(f"  Manifest omitido: {e}", WARNING_C)

            # Registro Windows
            self._registrar_windows(install_dir, uninst_dest)
            self.progress_signal.emit(1.0, "Completado.")
            self.log_signal.emit("  ¡NeuroMood Hub instalado!", SUCCESS)
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
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodHub"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName",     0, winreg.REG_SZ,    "NeuroMood Hub")
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
    APP_NAME = "Instalador Hub"
    WINDOW_ROLE = ""
    WINDOW_SIZE = (820, 660)
    _STEPPER_ACCENT = "violet"
    STEPS = ["Bienvenida", "Instalar", "Finalizar"]

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

        self._apply_visual_qa_defaults()
        self._ir_a(0)

    def _apply_visual_qa_defaults(self):
        if os.environ.get("NM_VISUAL_QA") != "1":
            return
        qa_root = os.path.join(os.path.expanduser("~"), "NeuromoodV3_QA")
        self._ent_path.setText(
            os.environ.get(
                "NM_QA_HUB_INSTALL_DIR",
                os.path.join(qa_root, "NeuroMood Hub"),
            )
        )

    def _fade_to(self, n: int):
        super()._fade_to(n)
        if n == 2:
            self.btn_sig.setText("Finalizar")
        elif n == 1:
            self.btn_sig.setText("Instalar")
        else:
            self.btn_sig.setText("Siguiente →")
        self.btn_ant.setVisible(n > 0 and n < 2)

    def _build_p0(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        t1 = QLabel("Instalador Hub")
        t1.setStyleSheet(f"color: {ACCENT}; font-size: 24px; font-weight: bold;")
        lay.addWidget(t1)
        t2 = QLabel("Instalador Hub - instalacion para profesionales")
        t2.setStyleSheet(f"color: {TEXT_TERT}; font-size: 13px;")
        lay.addWidget(t2)
        lay.addSpacing(20)
        line = QFrame(); line.setFixedHeight(2)
        line.setStyleSheet(f"background: {ACCENT};")
        lay.addWidget(line)
        lay.addSpacing(20)
        desc = QLabel(
            "Este instalador configurara el NeuroMood Hub\n"
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
        title = QLabel("Instalando...")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        lay.addWidget(title)
        lay.addSpacing(12)

        path_lbl = QLabel("Carpeta de instalacion:")
        path_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        lay.addWidget(path_lbl)
        lay.addSpacing(3)

        path_row = QWidget()
        pr = QHBoxLayout(path_row)
        pr.setContentsMargins(0, 0, 0, 0)
        pr.setSpacing(8)
        self._ent_path = QLineEdit(DEFAULT_INSTALL)
        self._ent_path.setText(DEFAULT_INSTALL)
        pr.addWidget(self._ent_path, stretch=1)
        btn_browse = QPushButton("Examinar")
        btn_browse.setObjectName("outline")
        btn_browse.setFixedSize(110, 36)
        btn_browse.clicked.connect(self._browse)
        pr.addWidget(btn_browse)
        lay.addWidget(path_row)
        lay.addSpacing(12)

        self._install_progress = NMInstallProgress(accent_key="violet")
        self._install_progress.set_progress(0, "Presiona 'Instalar' para continuar.")
        lay.addWidget(self._install_progress)
        self._progress_bar = self._install_progress
        self._progress_lbl = self._install_progress._label
        self._log_layout = None
        self._log_scroll = None
        lay.addStretch()

    def _build_p3(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        title = QLabel("Instalando NeuroMood Hub...")
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

    def _build_p2(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        ok = QLabel("Archivos instalados")
        ok.setStyleSheet(f"color: {SUCCESS}; font-size: 20px; font-weight: bold;")
        lay.addWidget(ok)
        lay.addSpacing(8)
        desc = QLabel(
            "El NeuroMood Hub ya esta instalado.\n"
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
        if self._pagina in (1, 2):
            self._ir_a(self._pagina - 1)

    def _siguiente(self):
        if self._pagina == 0:
            self._ir_a(1)
        elif self._pagina == 1:
            self._ir_a(2)
        elif self._pagina == 2:
            if self._install_dir:
                self._ir_a(3)
                return
            self.btn_sig.setEnabled(False); self.btn_sig.setText("Instalando...")
            self.btn_ant.setEnabled(False)
            self._worker = _ProWorker(self._ent_path.text().strip(), self)
            self._worker.log_signal.connect(self._log)
            self._worker.progress_signal.connect(self._set_progress)
            self._worker.done_signal.connect(self._on_done)
            self._worker.error_signal.connect(self._on_error)
            self._worker.start()
        elif self._pagina == 3:
            self._finalizar(); self.close()

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
