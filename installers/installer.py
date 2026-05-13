"""
installer.py — NeuroMood Installer (PyQt6)
Compilar con: BUILD_INSTALLER.bat
"""
import sys
import os
import shutil
import subprocess
import threading
import time
import hashlib
import sqlite3
import secrets
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QButtonGroup,
    QSizePolicy, QStackedWidget, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QAbstractAnimation, QEventLoop
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, TEXT_ON_ACCENT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer,
    )
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, TEXT_ON_ACCENT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer,
    )

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood")
APP_EXE    = "NeuroMood.exe"
APP_NOMBRE = "NeuroMood"

# ── Paleta del instalador aplicada globalmente ────────────────────────────────
_SS = stylesheet_installer()   # design system premium unificado

try:
    from shared.components_qt import NMInput, NMProgressBar
    _COMPONENTS_OK = True
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    try:
        from shared.components_qt import NMInput, NMProgressBar
        _COMPONENTS_OK = True
    except ImportError:
        _COMPONENTS_OK = False


def ruta_app_bundled(exe: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist"
    )
    return os.path.join(base, exe)


# ── Hilo de instalación ───────────────────────────────────────────────────────

class _InstalWorker(QThread):
    """Ejecuta _instalar() en un hilo separado para no bloquear la UI."""
    log_signal     = pyqtSignal(str, str)   # (texto, color_hex)
    progress_signal = pyqtSignal(float, str)
    done_signal    = pyqtSignal(str, str)   # (install_dir, icon_dest)
    error_signal   = pyqtSignal(str)

    def __init__(self, install_path: str, nombre: str, pwd: str,
                 codigo: str, parent=None):
        super().__init__(parent)
        self._path = install_path
        self._nombre = nombre
        self._pwd = pwd
        self._codigo = codigo

    def run(self):
        try:
            install_dir = Path(self._path)
            total = 4
            paso = 0

            self.progress_signal.emit(0, "Creando carpeta de instalacion...")
            install_dir.mkdir(parents=True, exist_ok=True)
            paso += 1
            self.progress_signal.emit(paso / total, "Carpeta lista.")
            self.log_signal.emit(f"  Carpeta: {install_dir}", TEXT_SEC)

            # NeuroMood.exe
            self.progress_signal.emit(paso / total, "Copiando NeuroMood...")
            src = ruta_app_bundled(APP_EXE)
            if not os.path.exists(src):
                self.log_signal.emit(f"  No encontrado: {APP_EXE}", ERROR_C)
            else:
                shutil.copy2(src, install_dir / APP_EXE)
                self.log_signal.emit(f"  {APP_NOMBRE}", SUCCESS)
            paso += 1
            self.progress_signal.emit(paso / total, "NeuroMood copiado.")
            time.sleep(0.05)

            # Icono (oculto)
            icon_dest = ""
            try:
                import ctypes as _ct
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
                _ct.windll.kernel32.SetFileAttributesW(str(icon_path), 0x2)
            except Exception:
                pass

            # Desinstalador
            self.progress_signal.emit(paso / total, "Copiando desinstalador...")
            uninst_dest = install_dir / "Desinstalar NeuroMood.exe"
            try:
                shutil.copy2(ruta_app_bundled("Desinstalar NeuroMood.exe"), uninst_dest)
                self.log_signal.emit("  Desinstalador copiado", SUCCESS)
            except Exception as e:
                self.log_signal.emit(f"  Desinstalador no disponible: {e}", WARNING_C)
            paso += 1

            # install_path.txt (oculto)
            try:
                import ctypes as _ct
                path_txt = install_dir / "install_path.txt"
                path_txt.write_text(str(install_dir), encoding="utf-8")
                _ct.windll.kernel32.SetFileAttributesW(str(path_txt), 0x2)
            except Exception:
                pass

            # Registro Windows
            self._registrar_windows(install_dir, uninst_dest)

            paso += 1
            self.progress_signal.emit(1.0, "Completado.")
            self.log_signal.emit("", TEXT_SEC)
            self.log_signal.emit("  ¡NeuroMood instalado correctamente!", SUCCESS)

            # Identidad del paciente
            self._registrar_identidad(install_dir)

            self.done_signal.emit(str(install_dir), icon_dest)

        except PermissionError:
            self.log_signal.emit("  Sin permisos en la carpeta seleccionada.", ERROR_C)
            self.log_signal.emit("  Elegi otra ubicacion.", TEXT_TERT)
            self.progress_signal.emit(0, "Error de permisos.")
            self.error_signal.emit("permission")
        except Exception as e:
            self.log_signal.emit(f"  Error inesperado: {e}", ERROR_C)
            self.progress_signal.emit(0, "Error durante la instalacion.")
            self.error_signal.emit("generic")

    def _registrar_windows(self, install_dir: Path, uninst_path: Path):
        try:
            import winreg
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMood"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName",      0, winreg.REG_SZ,    "NeuroMood")
                winreg.SetValueEx(k, "UninstallString",  0, winreg.REG_SZ,    f'"{uninst_path}"')
                winreg.SetValueEx(k, "DisplayIcon",      0, winreg.REG_SZ,    f'"{uninst_path}",0')
                winreg.SetValueEx(k, "Publisher",        0, winreg.REG_SZ,    "NeuroMood")
                winreg.SetValueEx(k, "URLInfoAbout",     0, winreg.REG_SZ,    "https://neuromood.com.ar")
                winreg.SetValueEx(k, "InstallLocation",  0, winreg.REG_SZ,    str(install_dir))
                winreg.SetValueEx(k, "NoModify",         0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "NoRepair",         0, winreg.REG_DWORD, 1)
        except Exception:
            pass

    def _registrar_identidad(self, install_dir: Path):
        from shared.identidad import generar_patient_id
        pid = generar_patient_id(self._nombre, self._pwd, self._codigo)

        db_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NeuroMood")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "nm_data.db")

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
            for clave, valor in [
                ("patient_name", self._nombre),
                ("patient_id",   pid),
                ("patient_pwd",  self._pwd),
                ("install_code", self._codigo),
            ]:
                conn.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)",
                             (clave, valor))
            conn.commit()
            conn.close()
            self.log_signal.emit("  Identidad guardada", SUCCESS)
        except Exception as e:
            self.log_signal.emit(f"  Advertencia: identidad ({e})", WARNING_C)

        # .env → AppData
        env_src = recurso(".env")
        if os.path.exists(env_src):
            try:
                env_dest = os.path.join(db_dir, ".env")
                shutil.copy2(env_src, env_dest)
                try:
                    import ctypes as _ct
                    _ct.windll.kernel32.SetFileAttributesW(env_dest, 0x2)
                except Exception:
                    pass
                self.log_signal.emit("  Configuracion de red copiada", SUCCESS)
            except Exception as e:
                self.log_signal.emit(f"  Config red: {e}", WARNING_C)

        # Supabase
        try:
            import importlib, sys as _sys
            if "shared.config" in _sys.modules:
                importlib.reload(_sys.modules["shared.config"])
            from shared.config import supabase_url, supabase_key
            from supabase import create_client
            url, key = supabase_url(), supabase_key()
            if url and key:
                sb = create_client(url, key)
                sb.table("patients").upsert({
                    "patient_id": pid, "patient_name": self._nombre,
                    "pwd": self._pwd, "install_code": self._codigo,
                }).execute()
                self.log_signal.emit("  Paciente registrado en la nube", SUCCESS)
        except Exception as e:
            self.log_signal.emit(f"  Registro en nube omitido ({str(e)[:50]})", WARNING_C)


# ── InstaladorNeuroMood ───────────────────────────────────────────────────────

class InstaladorNeuroMood(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instalador — NeuroMood")
        self.setFixedSize(740, 540)
        self.setStyleSheet(_SS)

        try:
            self.setWindowIcon(QIcon(recurso("installer_icon.ico")))
        except Exception:
            pass

        # Centrar
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - 740) // 2, (screen.height() - 540) // 2)

        QTimer.singleShot(150, lambda: aplicar_captionbar_installer(self))

        self._pagina = 0
        self._install_dir: str = ""
        self._icon_dest: str = ""
        self._es_login = False
        self._codigo_instalacion = ""
        self._worker: _InstalWorker | None = None

        self._build_ui()
        self._ir_a(0)

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"background: {BG_SECONDARY};")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # Logo
        logo_lbl = QLabel()
        try:
            from PIL import Image as PILImage
            img = PILImage.open(recurso("LOGO.png")).convert("RGBA")
            img.thumbnail((160, 68), PILImage.LANCZOS)
            data = img.tobytes("raw", "RGBA")
            from PyQt6.QtGui import QImage
            qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
            logo_lbl.setPixmap(QPixmap.fromImage(qimg))
        except Exception:
            logo_lbl.setText("NeuroMood")
            logo_lbl.setStyleSheet(
                f"color: {ACCENT}; font-size: 16px; font-weight: bold;"
                f"background: transparent; padding: 8px;"
            )
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setContentsMargins(0, 20, 0, 12)
        sl.addWidget(logo_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        sl.addWidget(sep)

        self._pasos_widgets: list[tuple[QLabel, QLabel]] = []
        pasos = ["Bienvenida", "Registro", "Instalacion", "Finalizar"]
        sl.addSpacing(14)
        for i, nombre in enumerate(pasos):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 3, 14, 3)
            circle = QLabel(str(i + 1))
            circle.setFixedSize(26, 26)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setStyleSheet(
                f"background: {BORDER}; color: {TEXT_TERT};"
                f"border-radius: 13px; font-weight: bold; font-size: 11px;"
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

        # ── Contenido ─────────────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background: {BG_PRIMARY};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        root.addWidget(right)

        # Stack de páginas
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {BG_PRIMARY};")
        rl.addWidget(self._stack, stretch=1)

        # Páginas
        self._pages: list[QWidget] = []
        for builder in [self._build_p0, self._build_p1, self._build_p2, self._build_p3]:
            page = QWidget()
            page.setStyleSheet(f"background: {BG_PRIMARY};")
            builder(page)
            self._stack.addWidget(page)
            self._pages.append(page)

        # Nav bar
        nav = QWidget()
        nav.setFixedHeight(58)
        nav.setStyleSheet(f"background: {BG_SECONDARY};")
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(16, 0, 16, 0)
        self.btn_ant = QPushButton("← Anterior")
        self.btn_ant.setObjectName("outline")
        self.btn_ant.setFixedSize(120, 36)
        self.btn_ant.clicked.connect(self._anterior)
        nl.addWidget(self.btn_ant)
        nl.addStretch()
        self.btn_sig = QPushButton("Siguiente →")
        self.btn_sig.setFixedSize(140, 36)
        self.btn_sig.clicked.connect(self._siguiente)
        nl.addWidget(self.btn_sig)
        rl.addWidget(nav)

    def _page_layout(self, page: QWidget) -> QVBoxLayout:
        """Retorna un layout con márgenes estándar para una página."""
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 8)
        lay.setSpacing(0)
        return lay

    # ── Página 0: Bienvenida ──────────────────────────────────────────────────

    def _build_p0(self, page: QWidget):
        lay = self._page_layout(page)
        sub = QLabel("Bienvenido a")
        sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 14px;")
        lay.addWidget(sub)
        title = QLabel("NeuroMood")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: bold;")
        lay.addWidget(title)
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(f"background: {ACCENT};")
        lay.addSpacing(6)
        lay.addWidget(line)
        lay.addSpacing(20)
        desc = QLabel(
            "Este instalador configurará en tu computadora\n"
            "NeuroMood, diseñada para acompañar tu bienestar\n"
            "emocional y mental.\n\n"
            "En los siguientes pasos crearás tu perfil y\n"
            "la app quedará lista para usar."
        )
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        lay.addWidget(desc)
        lay.addSpacing(24)
        card = QFrame()
        card.setStyleSheet(
            f"background: {BG_SURFACE}; border-radius: 10px;"
            f"border: 1px solid {BORDER};"
        )
        cl = QHBoxLayout(card)
        cl.setContentsMargins(14, 8, 14, 8)
        info = QLabel("ℹ  Compatible con Windows 10 y Windows 11.")
        info.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px; background: transparent; border: none;")
        cl.addWidget(info)
        lay.addWidget(card)
        lay.addStretch()

    # ── Página 1: Registro ────────────────────────────────────────────────────

    def _build_p1(self, page: QWidget):
        lay = self._page_layout(page)

        self._lbl_reg_titulo = QLabel("Crear cuenta nueva")
        self._lbl_reg_titulo.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;"
        )
        lay.addWidget(self._lbl_reg_titulo)

        self._lbl_reg_sub = QLabel("Configurá tu perfil para empezar")
        self._lbl_reg_sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(self._lbl_reg_sub)
        lay.addSpacing(10)

        # Segmented: Primera vez | Ya tengo cuenta
        seg_row = QHBoxLayout()
        seg_row.setSpacing(1)
        self._btn_primera = QPushButton("Primera vez")
        self._btn_ya = QPushButton("Ya tengo cuenta")
        self._seg_btns = []

        def _apply_seg(active_btn):
            for btn in [self._btn_primera, self._btn_ya]:
                is_active = btn is active_btn
                btn.setStyleSheet(
                    f"QPushButton {{background: {ACCENT if is_active else BG_SURFACE};"
                    f"color: {TEXT_ON_ACCENT if is_active else TEXT_SEC};"
                    f"border-radius: {2 if isinstance(btn, QPushButton) else 0}px; border: none;"
                    f"font-size: 12px; padding: 8px 18px;}}"
                    f"QPushButton:hover {{background: {ACCENT_HOVER}; color: {TEXT_ON_ACCENT};}}"
                )

        self._btn_primera.clicked.connect(lambda: (_apply_seg(self._btn_primera), self._cambiar_modo(False)))
        self._btn_ya.clicked.connect(lambda: (_apply_seg(self._btn_ya), self._cambiar_modo(True)))

        for btn in [self._btn_primera, self._btn_ya]:
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            seg_row.addWidget(btn)
        _apply_seg(self._btn_primera)
        lay.addLayout(seg_row)
        lay.addSpacing(10)

        # Card de inputs
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{background: {BG_SURFACE}; border-radius: 10px; border: 1px solid {BORDER};}}"
            f"QLabel {{background: transparent; border: none; font-size: 12px; color: {TEXT_SEC};}}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(4)

        cl.addWidget(QLabel("Nombre completo"))
        self._ent_nombre = NMInput("Tu nombre y apellido") if _COMPONENTS_OK else QLineEdit()
        if not _COMPONENTS_OK:
            self._ent_nombre.setPlaceholderText("Tu nombre y apellido")
        cl.addWidget(self._ent_nombre)

        cl.addSpacing(4)
        cl.addWidget(QLabel("Contraseña"))
        self._ent_pwd = NMInput("Mínimo 6 caracteres") if _COMPONENTS_OK else QLineEdit()
        if not _COMPONENTS_OK:
            self._ent_pwd.setPlaceholderText("Mínimo 6 caracteres")
        self._ent_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        cl.addWidget(self._ent_pwd)

        # Confirmar (visible en modo "Primera vez")
        self._frame_confirm = QWidget()
        self._frame_confirm.setStyleSheet("background: transparent;")
        fcl = QVBoxLayout(self._frame_confirm)
        fcl.setContentsMargins(0, 4, 0, 0)
        fcl.setSpacing(4)
        lbl_conf = QLabel("Confirmar contraseña")
        lbl_conf.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
        fcl.addWidget(lbl_conf)
        self._ent_confirm = NMInput() if _COMPONENTS_OK else QLineEdit()
        self._ent_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        fcl.addWidget(self._ent_confirm)
        cl.addWidget(self._frame_confirm)

        # Código (visible en modo "Ya tengo cuenta")
        self._frame_codigo = QWidget()
        self._frame_codigo.setStyleSheet("background: transparent;")
        self._frame_codigo.hide()
        fkl = QVBoxLayout(self._frame_codigo)
        fkl.setContentsMargins(0, 4, 0, 0)
        fkl.setSpacing(2)
        lbl_cod = QLabel("Código de instalación")
        lbl_cod.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
        fkl.addWidget(lbl_cod)
        self._ent_codigo = NMInput("XXXXXX") if _COMPONENTS_OK else QLineEdit()
        if not _COMPONENTS_OK:
            self._ent_codigo.setPlaceholderText("XXXXXX")
        fkl.addWidget(self._ent_codigo)
        lbl_hint = QLabel(
            "El código lo encontrás en tu primera instalación\n"
            "o lo provee tu terapeuta."
        )
        lbl_hint.setStyleSheet(f"color: {TEXT_TERT}; font-size: 10px; background: transparent;")
        fkl.addWidget(lbl_hint)
        cl.addWidget(self._frame_codigo)
        lay.addWidget(card)
        lay.addSpacing(8)

        # Info card (verde)
        info_card = QFrame()
        info_card.setObjectName("InfoCard")
        info_card.setStyleSheet(
            f"QFrame#InfoCard {{background: #091E10; border-radius: 8px; border: 1px solid {SUCCESS};}}"
        )
        icl = QVBoxLayout(info_card)
        icl.setContentsMargins(12, 7, 12, 7)
        self._lbl_info_reg = QLabel(
            "ℹ  Tu contraseña es tu clave de acceso única.\n"
            "   El profesional puede recuperarla desde el Hub si la olvidás."
        )
        self._lbl_info_reg.setStyleSheet(
            f"color: {SUCCESS}; font-size: 11px; background: transparent; border: none;"
        )
        icl.addWidget(self._lbl_info_reg)
        lay.addWidget(info_card)
        lay.addSpacing(4)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet(
            f"color: {ERROR_C}; font-size: 12px; background: transparent;"
        )
        lay.addWidget(self._lbl_error)
        lay.addStretch()

    def _cambiar_modo(self, es_login: bool):
        self._es_login = es_login
        self._btn_primera.setChecked(not es_login)
        self._btn_ya.setChecked(es_login)
        if es_login:
            self._lbl_reg_titulo.setText("Iniciar sesión")
            self._lbl_reg_sub.setText("Recuperá tu progreso con tus credenciales")
            self._frame_confirm.hide()
            self._frame_codigo.show()
            self._lbl_info_reg.setText(
                "ℹ  Usá el mismo nombre y contraseña exactos de tu cuenta.\n"
                "   Tus datos en la nube se sincronizarán al abrir la app."
            )
        else:
            self._lbl_reg_titulo.setText("Crear cuenta nueva")
            self._lbl_reg_sub.setText("Configurá tu perfil para empezar")
            self._frame_confirm.show()
            self._frame_codigo.hide()
            self._lbl_info_reg.setText(
                "ℹ  Tu contraseña es tu clave de acceso única.\n"
                "   El profesional puede recuperarla desde el Hub si la olvidás."
            )
        self._lbl_error.setText("")

    # ── Página 2: Instalación ─────────────────────────────────────────────────

    def _build_p2(self, page: QWidget):
        lay = self._page_layout(page)
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
        self._ent_path = NMInput() if _COMPONENTS_OK else QLineEdit(DEFAULT_INSTALL)
        self._ent_path.setText(DEFAULT_INSTALL)
        pr.addWidget(self._ent_path, stretch=1)
        btn_browse = QPushButton("Examinar")
        btn_browse.setObjectName("outline")
        btn_browse.setFixedSize(90, 36)
        btn_browse.clicked.connect(self._browse)
        pr.addWidget(btn_browse)
        lay.addWidget(path_row)
        lay.addSpacing(12)

        if _COMPONENTS_OK:
            self._progress_bar = NMProgressBar(height=8)
        else:
            self._progress_bar = QProgressBar()
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
        lay.addWidget(self._progress_bar)
        lay.addSpacing(6)

        self._progress_lbl = QLabel("Presiona 'Instalar' para continuar.")
        self._progress_lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(self._progress_lbl)
        lay.addSpacing(8)

        # Log
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {BG_SURFACE}; border-radius: 8px; border: none; }}"
        )
        self._log_container = QWidget()
        self._log_container.setStyleSheet(f"background: {BG_SURFACE};")
        self._log_layout = QVBoxLayout(self._log_container)
        self._log_layout.setContentsMargins(8, 8, 8, 8)
        self._log_layout.setSpacing(1)
        self._log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._log_container)
        self._log_scroll = scroll
        lay.addWidget(scroll)
        lay.addStretch()

    # ── Página 3: Finalizar ───────────────────────────────────────────────────

    def _build_p3(self, page: QWidget):
        lay = self._page_layout(page)
        ok = QLabel("¡Instalacion completada!")
        ok.setStyleSheet(f"color: {SUCCESS}; font-size: 20px; font-weight: bold;")
        lay.addWidget(ok)
        lay.addSpacing(6)

        desc = QLabel(
            "NeuroMood se instalo correctamente.\n"
            "Abri la app e ingresa con tu nombre de usuario para comenzar."
        )
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        lay.addWidget(desc)
        lay.addSpacing(12)

        btn_abrir = QPushButton("Abrir NeuroMood ahora →")
        btn_abrir.setFixedSize(230, 40)
        btn_abrir.clicked.connect(self._abrir_app)
        lay.addWidget(btn_abrir)
        lay.addSpacing(16)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        lay.addWidget(sep)
        lay.addSpacing(12)

        self._chk_escritorio = QCheckBox("Crear acceso directo en el Escritorio")
        self._chk_escritorio.setChecked(True)
        lay.addWidget(self._chk_escritorio)
        lay.addSpacing(10)

        self._chk_menu = QCheckBox("Crear acceso directo en el Menu de Inicio")
        self._chk_menu.setChecked(False)
        lay.addWidget(self._chk_menu)
        lay.addSpacing(12)

        btn_carpeta = QPushButton("Abrir carpeta de instalacion")
        btn_carpeta.setObjectName("outline")
        btn_carpeta.setFixedSize(230, 32)
        btn_carpeta.clicked.connect(self._abrir_carpeta)
        lay.addWidget(btn_carpeta)
        lay.addStretch()

    # ── Navegación ────────────────────────────────────────────────────────────

    def _ir_a(self, n: int):
        if n == self._pagina:
            return
        self._pagina = n
        self._fade_to(n)

    def _fade_to(self, n: int):
        """Cross-fade de 150ms entre paginas del QStackedWidget."""
        current = self._stack.currentWidget()
        if current is None:
            self._stack.setCurrentIndex(n)
            return
        target = self._stack.widget(n)
        if target is None:
            return
        # Capturar snapshot de la pagina actual
        snap = current.grab()
        overlay = QLabel(self._stack)
        overlay.setPixmap(snap)
        overlay.setGeometry(0, 0, self._stack.width(), self._stack.height())
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.show()
        overlay.raise_()
        eff = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(150)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._stack.setCurrentIndex(n)
        anim.finished.connect(overlay.deleteLater)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        for i, (circle, lbl) in enumerate(self._pasos_widgets):
            if i == n:
                circle.setStyleSheet(
                    f"background: {ACCENT}; color: white; border-radius: 13px;"
                    f"font-weight: bold; font-size: 11px;"
                )
                lbl.setStyleSheet(
                    f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold;"
                    f"background: transparent;"
                )
            elif i < n:
                circle.setStyleSheet(
                    f"background: {SUCCESS}; color: white; border-radius: 13px;"
                    f"font-weight: bold; font-size: 11px;"
                )
                lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
            else:
                circle.setStyleSheet(
                    f"background: {BORDER}; color: {TEXT_TERT}; border-radius: 13px;"
                    f"font-weight: bold; font-size: 11px;"
                )
                lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px; background: transparent;")

        self.btn_ant.setEnabled(n == 1)
        if n == 3:
            self.btn_sig.setText("Finalizar")
            self.btn_sig.setEnabled(True)
        elif n == 2:
            self.btn_sig.setText("Instalar")
            self.btn_sig.setEnabled(True)
        else:
            self.btn_sig.setText("Siguiente →")
            self.btn_sig.setEnabled(True)

    def _anterior(self):
        if self._pagina == 1:
            self._ir_a(0)

    def _siguiente(self):
        if self._pagina == 0:
            self._ir_a(1)

        elif self._pagina == 1:
            nombre = self._ent_nombre.text().strip()
            pwd = self._ent_pwd.text()
            if not nombre:
                self._lbl_error.setText("  El nombre no puede estar vacío.")
                return
            if len(pwd) < 6:
                self._lbl_error.setText("  La contraseña debe tener al menos 6 caracteres.")
                return
            if not self._es_login:
                if pwd != self._ent_confirm.text():
                    self._lbl_error.setText("  Las contraseñas no coinciden.")
                    return
                self._codigo_instalacion = secrets.token_hex(3).upper()
            else:
                codigo = self._ent_codigo.text().strip().upper()
                if not codigo:
                    self._lbl_error.setText("  Ingresá tu código de instalación.")
                    return
                self._codigo_instalacion = codigo
            self._lbl_error.setText("")
            self._ir_a(2)

        elif self._pagina == 2:
            path = self._ent_path.text().strip()
            if self._es_ruta_protegida(path):
                resp = QMessageBox.question(
                    self, "Carpeta con restricciones",
                    f"Esa carpeta requiere permisos de administrador.\n"
                    f"¿Instalar en la carpeta recomendada?\n{DEFAULT_INSTALL}",
                )
                if resp == QMessageBox.StandardButton.Yes:
                    self._ent_path.setText(DEFAULT_INSTALL)
                    path = DEFAULT_INSTALL
                else:
                    return
            self.btn_sig.setEnabled(False)
            self.btn_sig.setText("Instalando...")
            self._iniciar_instalacion(path)

        elif self._pagina == 3:
            self._finalizar()
            self.close()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Elegí carpeta de instalación", self._ent_path.text()
        )
        if folder:
            self._ent_path.setText(folder)

    def _es_ruta_protegida(self, ruta: str) -> bool:
        ruta_norm = os.path.normpath(ruta).lower()
        protegidas = [
            os.path.normpath(os.environ.get("PROGRAMFILES", r"C:\Program Files")).lower(),
            os.path.normpath(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")).lower(),
            os.path.normpath(os.environ.get("WINDIR", r"C:\Windows")).lower(),
            os.path.normpath(r"C:\ProgramData").lower(),
        ]
        return any(ruta_norm.startswith(p) for p in protegidas)

    # ── Instalación ───────────────────────────────────────────────────────────

    def _log(self, texto: str, color: str = TEXT_SEC):
        lbl = QLabel(texto)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent; padding: 1px 2px;"
        )
        self._log_layout.addWidget(lbl)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        sb = self._log_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _set_progress(self, v: float, t: str):
        if _COMPONENTS_OK:
            self._progress_bar.animate_to(v, duration=200)
        else:
            self._progress_bar.setValue(int(v * 100))
        self._progress_lbl.setText(t)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def _iniciar_instalacion(self, path: str):
        nombre = self._ent_nombre.text().strip()
        pwd = self._ent_pwd.text()

        self._worker = _InstalWorker(path, nombre, pwd, self._codigo_instalacion, self)
        self._worker.log_signal.connect(self._log)
        self._worker.progress_signal.connect(self._set_progress)
        self._worker.done_signal.connect(self._on_install_done)
        self._worker.error_signal.connect(self._on_install_error)
        self._worker.start()

    def _on_install_done(self, install_dir: str, icon_dest: str):
        self._install_dir = install_dir
        self._icon_dest = icon_dest
        QTimer.singleShot(900, lambda: self._ir_a(3))

    def _on_install_error(self, tipo: str):
        if tipo == "permission":
            self._ir_a(2)
        self.btn_sig.setEnabled(True)
        self.btn_sig.setText("Instalar")

    # ── Finalizar ─────────────────────────────────────────────────────────────

    def _finalizar(self):
        if not self._install_dir:
            return
        exe_path = str(Path(self._install_dir) / APP_EXE)
        icono = self._icon_dest or exe_path
        if self._chk_escritorio.isChecked():
            try:
                escritorio = Path(os.path.expanduser("~")) / "Desktop"
                crear_acceso_directo(exe_path, str(escritorio / f"{APP_NOMBRE}.lnk"), icono)
            except Exception:
                pass
        if self._chk_menu.isChecked():
            try:
                start_nm = (
                    Path(os.environ.get("APPDATA", ""))
                    / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood"
                )
                start_nm.mkdir(parents=True, exist_ok=True)
                crear_acceso_directo(exe_path, str(start_nm / f"{APP_NOMBRE}.lnk"), icono)
            except Exception:
                pass

    def _abrir_app(self):
        if self._install_dir:
            exe = Path(self._install_dir) / APP_EXE
            if exe.exists():
                try:
                    subprocess.Popen([str(exe)])
                except Exception:
                    pass

    def _abrir_carpeta(self):
        if self._install_dir and Path(self._install_dir).exists():
            subprocess.Popen(["explorer", self._install_dir])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = InstaladorNeuroMood()
    win.show()
    sys.exit(app.exec())
