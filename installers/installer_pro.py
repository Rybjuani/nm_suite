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
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QScrollArea, QFrame, QFileDialog, QSizePolicy, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QEventLoop
from PyQt6.QtGui import QIcon, QPixmap

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer,
    )
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer,
    )

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood Pro")
HUB_EXE    = "NeuroMood Hub Profesional.exe"
UNINST_EXE = "Desinstalar NeuroMood Pro.exe"

_SS = stylesheet_installer()   # design system premium unificado


def ruta_bundled(exe: str) -> str:
    """Devuelve ruta a un .exe bundleado. Soporta --onedir y --onefile."""
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist"
    )
    # onedir: HubProfesional\HubProfesional.exe
    folder = os.path.join(base, "pro", exe.replace(".exe", ""))
    onedir_path = os.path.join(folder, exe)
    if os.path.exists(onedir_path):
        return onedir_path
    # onefile: pro\HubProfesional.exe
    return os.path.join(base, "pro", exe)


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
            src = ruta_bundled("HubProfesional.exe")
            if os.path.exists(src):
                src_dir = os.path.dirname(src)
                if os.path.isdir(src_dir):
                    shutil.copytree(src_dir, install_dir, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, install_dir / HUB_EXE)
                self.log_signal.emit("  Hub Profesional", SUCCESS)
            else:
                self.log_signal.emit("  HubProfesional.exe no encontrado", WARNING_C)

            # Desinstalador (copia carpeta completa si es onedir)
            self.progress_signal.emit(0.5, "Instalando desinstalador...")
            src_un = ruta_bundled(UNINST_EXE)
            uninst_dest_dir = install_dir / UNINST_EXE.replace(".exe", "")
            uninst_dest = uninst_dest_dir / UNINST_EXE
            if os.path.exists(src_un):
                src_un_dir = os.path.dirname(src_un)
                if os.path.isdir(src_un_dir):
                    shutil.copytree(src_un_dir, uninst_dest_dir, dirs_exist_ok=True)
                else:
                    uninst_dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_un, uninst_dest)
                self.log_signal.emit("  Desinstalador", SUCCESS)
            else:
                self.log_signal.emit("  Desinstalador no encontrado", WARNING_C)
                uninst_dest = install_dir  # fallback

            # Icono (oculto)
            self.progress_signal.emit(0.7, "Copiando recursos...")
            icon_dest = ""
            try:
                import ctypes as _ct
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
                _ct.windll.kernel32.SetFileAttributesW(str(icon_path), 0x2)
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
                winreg.SetValueEx(k, "DisplayName",     0, winreg.REG_SZ,    "NeuroMood Hub Profesional")
                winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,    f'"{uninst_dest}"')
                winreg.SetValueEx(k, "DisplayIcon",     0, winreg.REG_SZ,    f'"{exe}",0')
                winreg.SetValueEx(k, "Publisher",       0, winreg.REG_SZ,    "NeuroMood")
                winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ,    str(install_dir))
                winreg.SetValueEx(k, "NoModify",        0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "NoRepair",        0, winreg.REG_DWORD, 1)
        except Exception:
            pass


# ── InstaladorPro ─────────────────────────────────────────────────────────────

class InstaladorPro(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instalador — NeuroMood Hub Profesional")
        self.setFixedSize(680, 480)
        self.setStyleSheet(_SS)
        try:
            self.setWindowIcon(QIcon(recurso("installer_icon.ico")))
        except Exception:
            pass
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - 680) // 2, (screen.height() - 480) // 2)
        aplicar_captionbar_installer(self)

        self._pagina = 0
        self._install_dir = ""
        self._icon_dest = ""
        self._worker: _ProWorker | None = None

        self._build_ui()
        self._ir_a(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet(f"background: {BG_SECONDARY};")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)

        logo_lbl = QLabel()
        try:
            from PIL import Image as PILImage
            img = PILImage.open(recurso("LOGO.png")).convert("RGBA")
            img.thumbnail((158, 64), PILImage.LANCZOS)
            from PyQt6.QtGui import QImage
            qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height,
                          QImage.Format.Format_RGBA8888)
            logo_lbl.setPixmap(QPixmap.fromImage(qimg))
        except Exception:
            logo_lbl.setText("NeuroMood")
            logo_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 15px; font-weight: bold; background: transparent;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setContentsMargins(0, 18, 0, 10)
        sl.addWidget(logo_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        sl.addWidget(sep)

        self._pasos_widgets: list[tuple[QLabel, QLabel]] = []
        sl.addSpacing(14)
        for i, nombre in enumerate(["Bienvenida", "Instalacion", "Finalizar"]):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 3, 14, 3)
            circle = QLabel(str(i + 1))
            circle.setFixedSize(24, 24)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setStyleSheet(
                f"background: {BORDER}; color: {TEXT_TERT}; border-radius: 12px;"
                f"font-weight: bold; font-size: 11px;"
            )
            lbl = QLabel(nombre)
            lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px; background: transparent;")
            rl.addWidget(circle)
            rl.addWidget(lbl, stretch=1)
            sl.addWidget(row)
            self._pasos_widgets.append((circle, lbl))

        sl.addStretch()
        web = QLabel("neuromood.com.ar")
        web.setAlignment(Qt.AlignmentFlag.AlignCenter)
        web.setStyleSheet(f"color: {TEXT_TERT}; font-size: 10px; background: transparent;")
        web.setContentsMargins(0, 0, 0, 14)
        sl.addWidget(web)
        root.addWidget(sidebar)

        # Contenido
        right = QWidget()
        right.setStyleSheet(f"background: {BG_PRIMARY};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        root.addWidget(right)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {BG_PRIMARY};")
        rl.addWidget(self._stack, stretch=1)

        for builder in [self._build_p0, self._build_p1, self._build_p2]:
            page = QWidget()
            page.setStyleSheet(f"background: {BG_PRIMARY};")
            builder(page)
            self._stack.addWidget(page)

        nav = QWidget()
        nav.setFixedHeight(54)
        nav.setStyleSheet(f"background: {BG_SECONDARY};")
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(14, 0, 14, 0)
        self.btn_ant = QPushButton("← Anterior")
        self.btn_ant.setObjectName("outline")
        self.btn_ant.setFixedSize(110, 34)
        self.btn_ant.clicked.connect(self._anterior)
        self.btn_ant.setVisible(False)
        nl.addWidget(self.btn_ant)
        nl.addStretch()
        self.btn_sig = QPushButton("Siguiente →")
        self.btn_sig.setFixedSize(130, 34)
        self.btn_sig.clicked.connect(self._siguiente)
        nl.addWidget(self.btn_sig)
        rl.addWidget(nav)

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
        info = QLabel("ℹ  Requiere conexion a internet para funciones remotas.")
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
        lay.addSpacing(20)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100); self._progress_bar.setValue(0)
        lay.addWidget(self._progress_bar)
        lay.addSpacing(6)
        self._progress_lbl = QLabel("Listo para instalar.")
        self._progress_lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(self._progress_lbl)
        lay.addSpacing(8)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumHeight(120)
        scroll.setStyleSheet(f"QScrollArea {{background: {BG_SURFACE}; border-radius: 8px; border: none;}}")
        self._log_container = QWidget()
        self._log_container.setStyleSheet(f"background: {BG_SURFACE};")
        self._log_layout = QVBoxLayout(self._log_container)
        self._log_layout.setContentsMargins(8, 8, 8, 8); self._log_layout.setSpacing(1)
        self._log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._log_container)
        self._log_scroll = scroll
        lay.addWidget(scroll)
        lay.addStretch()

    def _build_p2(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(26, 22, 26, 8)
        lay.setSpacing(0)
        ok = QLabel("¡Instalacion completada!")
        ok.setStyleSheet(f"color: {SUCCESS}; font-size: 20px; font-weight: bold;")
        lay.addWidget(ok)
        lay.addSpacing(8)
        desc = QLabel("El Hub Profesional NeuroMood esta listo.")
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        lay.addWidget(desc)
        lay.addSpacing(18)
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        lay.addWidget(sep); lay.addSpacing(16)
        self._chk_escritorio = QCheckBox("Crear acceso directo en el Escritorio")
        self._chk_escritorio.setChecked(True); lay.addWidget(self._chk_escritorio)
        lay.addSpacing(12)
        self._chk_menu = QCheckBox("Crear acceso directo en el Menu de Inicio")
        self._chk_menu.setChecked(False); lay.addWidget(self._chk_menu)
        lay.addSpacing(16)
        btn_carpeta = QPushButton("Abrir carpeta de instalacion")
        btn_carpeta.setObjectName("outline"); btn_carpeta.setFixedSize(220, 36)
        btn_carpeta.clicked.connect(self._abrir_carpeta); lay.addWidget(btn_carpeta)
        lay.addStretch()

    def _ir_a(self, n: int):
        self._pagina = n
        self._stack.setCurrentIndex(n)
        for i, (circle, lbl) in enumerate(self._pasos_widgets):
            if i == n:
                circle.setStyleSheet(f"background: {ACCENT}; color: white; border-radius: 12px; font-weight: bold; font-size: 11px;")
                lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; background: transparent;")
            elif i < n:
                circle.setStyleSheet(f"background: {SUCCESS}; color: white; border-radius: 12px; font-weight: bold; font-size: 11px;")
                lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
            else:
                circle.setStyleSheet(f"background: {BORDER}; color: {TEXT_TERT}; border-radius: 12px; font-weight: bold; font-size: 11px;")
                lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px; background: transparent;")
        self.btn_ant.setVisible(n > 0)
        self.btn_sig.setText("Finalizar" if n == 2 else "Siguiente →")
        self.btn_sig.setEnabled(True)

    def _anterior(self):
        if self._pagina == 1:
            self._ir_a(0)

    def _siguiente(self):
        if self._pagina == 0:
            self._ir_a(1)
        elif self._pagina == 1:
            if self._install_dir:
                self._ir_a(2)
                return
            self.btn_sig.setEnabled(False); self.btn_sig.setText("Instalando...")
            self.btn_ant.setEnabled(False)
            self._worker = _ProWorker(self._ent_path.text().strip(), self)
            self._worker.log_signal.connect(self._log)
            self._worker.progress_signal.connect(self._set_progress)
            self._worker.done_signal.connect(self._on_done)
            self._worker.error_signal.connect(self._on_error)
            self._worker.start()
        elif self._pagina == 2:
            self._finalizar(); self.close()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Elegí carpeta", self._ent_path.text())
        if folder:
            self._ent_path.setText(folder)

    def _log(self, texto: str, color: str):
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; padding: 1px 2px;")
        self._log_layout.addWidget(lbl)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        self._log_scroll.verticalScrollBar().setValue(self._log_scroll.verticalScrollBar().maximum())

    def _set_progress(self, v: float, t: str):
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
