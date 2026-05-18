"""
installer.py — Instalador Suite (PyQt6)
Compilar con: BUILD_NEUROMOOD.bat
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
import json
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QCheckBox,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QButtonGroup, QInputDialog,
    QSizePolicy, QStackedWidget, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QAbstractAnimation, QEventLoop
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette
from PyQt6 import sip

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, BG_ELEVATED, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, TEXT_ON_ACCENT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        SUCCESS_BG, FONT_FAMILY, TEAL, VIOLET, GRAD_FROM, GRAD_MID, GRAD_TO,
        recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer, InstallerShell, GradientTextLabel,
    )
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, BG_ELEVATED, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, TEXT_ON_ACCENT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        SUCCESS_BG, FONT_FAMILY, TEAL, VIOLET, GRAD_FROM, GRAD_MID, GRAD_TO,
        recurso, crear_acceso_directo, aplicar_captionbar_installer,
        stylesheet_installer, InstallerShell, GradientTextLabel,
    )

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood")
APP_EXE    = "NeuroMood Suite.exe"
APP_NOMBRE = "NeuroMood Suite"
NEUROMOOD_SUITE_VERSION = "1.0.0"
INSTALADOR_SUITE_VERSION = "1.0.0"
DISCLAIMER_VERSION = "legal-2026-05-16"
PRIVACY_VERSION = "privacy-2026-05-16"
CONSENT_SCOPE = (
    "db_local,sync_autorizado,revision_profesional,visualizacion_neuromood_hub,"
    "ia_asistida_profesional,constancia_legal_remota"
)
LEGAL_DISCLAIMER_TEXT = """NeuroMood Suite es una herramienta digital complementaria de bienestar, registro emocional, organización de hábitos y apoyo personal. Su finalidad es facilitar el registro de estados de ánimo, rutinas, pensamientos, actividades, recordatorios y ejercicios de autorregulación.

NeuroMood Suite no realiza diagnósticos médicos, psicológicos ni psiquiátricos; no indica tratamientos; no reemplaza la evaluación, seguimiento, criterio ni intervención de profesionales de la salud habilitados; y no debe utilizarse como único medio para tomar decisiones sobre la salud física o mental.

NeuroMood Suite puede utilizarse como apoyo complementario dentro de un proceso acompañado por profesionales habilitados. El seguimiento, interpretación clínica, evaluación de riesgo, indicación terapéutica, derivación o toma de decisiones corresponden exclusivamente al profesional tratante.

Los contenidos, registros, gráficos, sugerencias, recordatorios o actividades incluidos en NeuroMood Suite tienen carácter orientativo, educativo y de apoyo complementario. Su interpretación y uso quedan bajo responsabilidad del paciente y, cuando corresponda, del profesional tratante.

NeuroMood Suite no es un servicio de emergencias. En caso de crisis emocional intensa, riesgo de autolesión, ideación suicida, emergencia médica, empeoramiento significativo del estado de salud o cualquier situación de peligro, el paciente debe comunicarse inmediatamente con un servicio de emergencias, guardia médica, línea local de asistencia, familiar responsable o profesional de confianza.

NeuroMood Suite puede tratar datos personales y datos sensibles vinculados al bienestar emocional, hábitos, registros de ánimo, pensamientos, actividades, recordatorios y uso de módulos. El paciente acepta que NeuroMood Suite pueda almacenar estos datos localmente y sincronizarlos, cuando corresponda, para el funcionamiento de NeuroMood Suite, continuidad de uso, visualización de evolución y, si existe vinculación profesional, revisión desde NeuroMood Hub por parte del profesional o equipo autorizado.

Cuando exista vinculación con un profesional, los registros sincronizados podrán ser utilizados en NeuroMood Hub para organizar información, preparar preguntas, generar borradores o sintetizar contexto mediante funciones asistidas por inteligencia artificial. La IA no realiza diagnósticos, evaluaciones clínicas, detección de riesgo, indicaciones terapéuticas, prescripciones, decisiones clínicas ni seguimiento autónomo del paciente. Todo contenido generado por IA debe ser revisado, validado y corregido por el profesional antes de utilizarse.

El paciente acepta que NeuroMood Suite registre una constancia técnica de esta aceptación, localmente y en un registro remoto seguro, incluyendo fecha, cuenta asociada, versión de NeuroMood Suite, versión del Instalador Suite, versión del aviso legal, versión de privacidad y hash del texto aceptado. Esta constancia podrá ser consultada por el profesional o equipo autorizado desde NeuroMood Hub únicamente para verificar el estado del consentimiento.

Estos datos se utilizarán exclusivamente para el funcionamiento de NeuroMood Suite, la continuidad de uso, la sincronización autorizada, la visualización profesional cuando corresponda, la constancia legal de consentimiento y el acompañamiento complementario dentro del entorno correspondiente. Su tratamiento deberá realizarse conforme a la política de privacidad aplicable, con medidas razonables de seguridad, confidencialidad y control de acceso.

La autenticación puede requerir email y contraseña mediante el sistema de cuenta de NeuroMood Suite. La contraseña no debe guardarse localmente en texto plano. El paciente se compromete a no compartir su cuenta, contraseña ni equipo con terceros no autorizados.

Al continuar, el paciente declara haber leído, comprendido y aceptado este aviso legal, el consentimiento de uso, el tratamiento de datos personales y sensibles, la sincronización autorizada cuando corresponda, la visualización profesional desde NeuroMood Hub y la generación de una constancia auditable de consentimiento."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _legal_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


DISCLAIMER_TEXT_HASH = _legal_hash(LEGAL_DISCLAIMER_TEXT)
PRIVACY_TEXT_HASH = _legal_hash(
    f"{PRIVACY_VERSION}|{CONSENT_SCOPE}|{DISCLAIMER_TEXT_HASH}"
)


def _patient_id_from_auth(email: str, auth_user_id: str) -> str:
    return auth_user_id.strip() or hashlib.sha256(email.strip().lower().encode()).hexdigest()[:24]


def _consent_file_path() -> Path:
    base = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "NeuroMood"
    return base / "legal_consent.json"


def _load_local_consent(email: str, auth_user_id: str) -> dict | None:
    path = _consent_file_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if data.get("email", "").strip().lower() != email.strip().lower():
        return None
    if data.get("user_id", "") != auth_user_id.strip():
        return None
    if data.get("disclaimer_version") != DISCLAIMER_VERSION:
        return None
    if data.get("privacy_version") != PRIVACY_VERSION:
        return None
    if data.get("disclaimer_text_hash") != DISCLAIMER_TEXT_HASH:
        return None
    if data.get("status") != "vigente":
        return None
    return data


def _save_local_consent(payload: dict) -> None:
    path = _consent_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

# ── Paleta del instalador aplicada globalmente ────────────────────────────────
_SS = stylesheet_installer()   # design system premium unificado

try:
    from shared.components_qt import NMInput, NMProgressBar, NMInstallProgress, NMCustomCheck
    _COMPONENTS_OK = True
except ImportError:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    try:
        from shared.components_qt import NMInput, NMProgressBar, NMInstallProgress, NMCustomCheck
        _COMPONENTS_OK = True
    except ImportError:
        _COMPONENTS_OK = False


def ruta_app_bundled(exe: str) -> str:
    """Devuelve ruta a un .exe bundleado. Soporta --onedir y --onefile."""
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist"
    )
    # onedir: carpeta del ejecutable + dependencias
    folder = os.path.join(base, exe.replace(".exe", ""))
    onedir_path = os.path.join(folder, exe)
    if os.path.exists(onedir_path):
        return onedir_path
    # onefile: ejecutable directo
    return os.path.join(base, exe)


INSTALL_MANIFEST_NAME = ".neuromood_install_manifest.json"
INSTALL_BUILD_ID = "clean-reinstall-2026-05-17"


def _safe_join(base: Path, rel: str) -> Path | None:
    """Une rutas de manifiesto sin permitir salir de install_dir."""
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
    """Evita limpiar carpetas demasiado amplias por error de selección."""
    try:
        resolved = path.expanduser().resolve()
        home = Path.home().resolve()
        anchors = {Path(resolved.anchor).resolve()} if resolved.anchor else set()
        blocked = {home, home.parent, Path(os.environ.get("APPDATA", str(home))).resolve()}
        return resolved in blocked or resolved in anchors
    except Exception:
        return False


def _clean_previous_payload(install_dir: Path, known_items: list[str]) -> list[str]:
    """Elimina solo archivos del bundle anterior, no datos de usuario en AppData."""
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
            # limpiar directorios vacíos más comunes después del manifest
            for rel in sorted(data.get("dirs", []), key=lambda x: len(str(x)), reverse=True):
                target = _safe_join(install_dir, str(rel))
                if target and target.exists() and target.is_dir():
                    try:
                        target.rmdir()
                    except OSError:
                        pass
        except Exception:
            # Si el manifest está corrupto, seguimos con los ítems conocidos.
            pass

    for name in known_items:
        target = install_dir / name
        if target.exists():
            _remove_path(target)
            removed.append(name)
    return removed


def _copy_payload_from_bundled_exe(src_exe: str, dest_dir: Path) -> list[str]:
    """Copia un bundle PyInstaller one-dir u one-file y devuelve archivos relativos copiados."""
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
        "installed_at_utc": _utc_now_iso(),
        "files": sorted(set(files)),
        "dirs": dirs,
    }
    (install_dir / INSTALL_MANIFEST_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

# ── Hilo de instalación ───────────────────────────────────────────────────────

class _AuthWorker(QThread):
    done_signal = pyqtSignal(str, str, str, bool, str, str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, action: str, email: str, password: str = "", parent=None):
        super().__init__(parent)
        self._action = action
        self._email = email.strip().lower()
        self._password = password

    def run(self):
        try:
            from shared.config import supabase_url, supabase_key
            from supabase import create_client

            url, key = supabase_url(), supabase_key()
            if not url or not key:
                self.error_signal.emit(
                    "No encontramos la configuracion de Supabase. Revisa la conexion o la configuracion incluida."
                )
                return

            client = create_client(url, key)

            if self._action == "login":
                res = client.auth.sign_in_with_password({
                    "email": self._email,
                    "password": self._password,
                })
                user = getattr(res, "user", None)
                session = getattr(res, "session", None)
                user_id = getattr(user, "id", "") if user else ""
                if not user_id:
                    self.error_signal.emit("No pudimos iniciar sesion. Revisa email y contrasena.")
                    return
                self.done_signal.emit(
                    "login",
                    "Sesion iniciada correctamente. Ya podes continuar.",
                    user_id,
                    True,
                    self._email,
                    getattr(session, "access_token", "") or "",
                    getattr(session, "refresh_token", "") or "",
                )
                return

            if self._action == "signup":
                res = client.auth.sign_up({
                    "email": self._email,
                    "password": self._password,
                })
                user = getattr(res, "user", None)
                session = getattr(res, "session", None)
                user_id = getattr(user, "id", "") if user else ""
                if session and user_id:
                    self.done_signal.emit(
                        "signup",
                        "Cuenta creada e iniciada correctamente. Ya podes continuar.",
                        user_id,
                        True,
                        self._email,
                        getattr(session, "access_token", "") or "",
                        getattr(session, "refresh_token", "") or "",
                    )
                else:
                    self.done_signal.emit(
                        "signup",
                        "Cuenta creada. Si Supabase requiere confirmacion, revisa tu correo y luego inicia sesion.",
                        user_id,
                        False,
                        self._email,
                        "",
                        "",
                    )
                return

            if self._action == "reset":
                client.auth.reset_password_for_email(self._email)
                self.done_signal.emit(
                    "reset",
                    "Te enviamos un enlace para restablecer tu contrasena. Revisa tu correo.\n"
                    "Este correo fue enviado automaticamente. No respondas a este mail.",
                    "",
                    False,
                    self._email,
                    "",
                    "",
                )
                return

            self.error_signal.emit("Accion de autenticacion no reconocida.")
        except Exception as e:
            msg = str(e).strip() or "Error desconocido"
            low = msg.lower()
            if "invalid login" in low or "invalid credentials" in low:
                msg = "Email o contrasena incorrectos."
            elif "email not confirmed" in low:
                msg = "Tu email aun no esta confirmado. Revisa tu correo y volve a intentar."
            elif "already registered" in low or "user already" in low:
                msg = "Ese email ya tiene cuenta. Proba iniciar sesion."
            elif any(x in low for x in ("network", "connection", "timeout", "failed to establish")):
                msg = "No pudimos conectarnos con Supabase. Revisa internet y reintenta."
            self.error_signal.emit(msg)


class _ConsentWorker(QThread):
    done_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, email: str, auth_user_id: str, access_token: str = "",
                 refresh_token: str = "", parent=None):
        super().__init__(parent)
        self._email = email.strip().lower()
        self._auth_user_id = auth_user_id.strip()
        self._access_token = access_token
        self._refresh_token = refresh_token

    def run(self):
        try:
            from shared.config import supabase_url, supabase_key
            from supabase import create_client

            url, key = supabase_url(), supabase_key()
            if not url or not key:
                self.error_signal.emit("No encontramos la configuracion remota para registrar el consentimiento.")
                return

            client = create_client(url, key)
            if self._access_token:
                try:
                    client.auth.set_session(self._access_token, self._refresh_token)
                except Exception:
                    try:
                        client.postgrest.auth(self._access_token)
                    except Exception:
                        pass

            accepted_at = _utc_now_iso()
            patient_id = _patient_id_from_auth(self._email, self._auth_user_id)
            payload = {
                "user_id": self._auth_user_id,
                "patient_id": patient_id,
                "email": self._email,
                "accepted_at_utc": accepted_at,
                "product_name": "NeuroMood Suite",
                "neuromood_suite_version": NEUROMOOD_SUITE_VERSION,
                "instalador_suite_version": INSTALADOR_SUITE_VERSION,
                "disclaimer_version": DISCLAIMER_VERSION,
                "privacy_version": PRIVACY_VERSION,
                "disclaimer_text_hash": DISCLAIMER_TEXT_HASH,
                "privacy_text_hash": PRIVACY_TEXT_HASH,
                "consent_scope": CONSENT_SCOPE,
                "status": "vigente",
                "created_at": accepted_at,
            }
            # Verificar si ya existe un registro vigente con las mismas versiones
            # para no acumular duplicados en Supabase.
            existing = (
                client.table("legal_consents")
                .select("id")
                .eq("user_id", self._auth_user_id)
                .eq("disclaimer_version", DISCLAIMER_VERSION)
                .eq("privacy_version", PRIVACY_VERSION)
                .eq("status", "vigente")
                .limit(1)
                .execute()
            )
            if not (getattr(existing, "data", None) or []):
                client.table("legal_consents").insert(payload).execute()
            _save_local_consent(payload)
            self.done_signal.emit(payload)
        except Exception as e:
            msg = str(e).strip() or "Error desconocido"
            low = msg.lower()
            if "relation" in low and "legal_consents" in low:
                msg = "La tabla legal_consents no existe o no esta disponible. Creala en Supabase y reintenta."
            elif any(x in low for x in ("network", "connection", "timeout", "failed to establish")):
                msg = "No pudimos registrar el consentimiento por un problema de red. Revisa internet y reintenta."
            else:
                msg = f"No pudimos registrar el consentimiento remoto: {msg[:180]}"
            self.error_signal.emit(msg)


class _InstalWorker(QThread):
    """Ejecuta _instalar() en un hilo separado para no bloquear la UI."""
    log_signal     = pyqtSignal(str, str)   # (texto, color_hex)
    progress_signal = pyqtSignal(float, str)
    done_signal    = pyqtSignal(str, str)   # (install_dir, icon_dest)
    error_signal   = pyqtSignal(str)

    def __init__(self, install_path: str, email: str, auth_user_id: str,
                 codigo: str, access_token: str = "", refresh_token: str = "",
                 parent=None):
        super().__init__(parent)
        self._path = install_path
        self._email = email.strip().lower()
        self._auth_user_id = auth_user_id.strip()
        self._nombre = self._email.split("@", 1)[0] if self._email else "Paciente"
        self._codigo = codigo
        self._access_token = access_token
        self._refresh_token = refresh_token

    def run(self):
        try:
            install_dir = Path(self._path)
            total = 5
            paso = 0
            manifest_files: list[str] = []
            uninst_dest = install_dir / "Desinstalador Suite" / "Desinstalador Suite.exe"

            self.progress_signal.emit(0, "Preparando instalación limpia...")
            install_dir.mkdir(parents=True, exist_ok=True)
            removed = _clean_previous_payload(
                install_dir,
                [
                    APP_EXE,
                    "_internal",
                    "base_library.zip",
                    "NM_icon.ico",
                    "install_path.txt",
                    "Desinstalador Suite",
                    "Desinstalador Suite.exe",
                    INSTALL_MANIFEST_NAME,
                ],
            )
            paso += 1
            self.progress_signal.emit(paso / total, "Carpeta lista y versión anterior reemplazada.")
            self.log_signal.emit(f"  Carpeta: {install_dir}", TEXT_SEC)
            if removed:
                self.log_signal.emit(f"  Limpieza previa: {len(removed)} elementos reemplazados", SUCCESS)

            # NeuroMood Suite (copia carpeta completa si es onedir)
            self.progress_signal.emit(paso / total, "Copiando NeuroMood Suite actualizado...")
            src = ruta_app_bundled(APP_EXE)
            try:
                copied = _copy_payload_from_bundled_exe(src, install_dir)
                manifest_files.extend(copied)
                if not (install_dir / APP_EXE).exists():
                    raise FileNotFoundError(f"No quedó instalado {APP_EXE}")
                self.log_signal.emit(f"  {APP_NOMBRE} actualizado", SUCCESS)
            except FileNotFoundError:
                self.log_signal.emit(f"  No encontrado: {APP_EXE}", ERROR_C)
                raise
            paso += 1
            self.progress_signal.emit(paso / total, "NeuroMood Suite copiado.")
            time.sleep(0.05)

            # Icono
            icon_dest = ""
            try:
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
                manifest_files.append("NM_icon.ico")
            except Exception:
                pass

            # Desinstalador (copia carpeta completa si es onedir)
            self.progress_signal.emit(paso / total, "Copiando desinstalador actualizado...")
            uninst_exe = "Desinstalador Suite.exe"
            uninst_src = ruta_app_bundled(uninst_exe)
            try:
                uninst_dest_dir = install_dir / "Desinstalador Suite"
                if Path(uninst_src).exists() and Path(uninst_src).parent.name == uninst_exe.replace(".exe", ""):
                    before = set(_collect_relative_files(install_dir, install_dir))
                    shutil.copytree(Path(uninst_src).parent, uninst_dest_dir, dirs_exist_ok=True)
                    after = set(_collect_relative_files(install_dir, install_dir))
                    manifest_files.extend(sorted(after - before))
                    uninst_dest = uninst_dest_dir / uninst_exe
                elif Path(uninst_src).exists():
                    uninst_dest_dir.mkdir(parents=True, exist_ok=True)
                    uninst_dest = uninst_dest_dir / uninst_exe
                    shutil.copy2(uninst_src, uninst_dest)
                    manifest_files.append(uninst_dest.relative_to(install_dir).as_posix())
                else:
                    raise FileNotFoundError(uninst_src)
                self.log_signal.emit("  Desinstalador actualizado", SUCCESS)
            except Exception as e:
                self.log_signal.emit(f"  Desinstalador no disponible: {e}", WARNING_C)
            paso += 1

            # install_path.txt (oculto)
            try:
                import ctypes as _ct
                path_txt = install_dir / "install_path.txt"
                path_txt.write_text(str(install_dir), encoding="utf-8")
                _ct.windll.kernel32.SetFileAttributesW(str(path_txt), 0x2)
                manifest_files.append("install_path.txt")
            except Exception:
                pass

            try:
                _write_install_manifest(install_dir, manifest_files, APP_NOMBRE)
            except Exception as e:
                self.log_signal.emit(f"  Manifest omitido: {e}", WARNING_C)

            # Registro Windows
            self._registrar_windows(install_dir, uninst_dest)

            paso += 1
            self.progress_signal.emit(1.0, "Completado.")
            self.log_signal.emit("", TEXT_SEC)
            self.log_signal.emit("  ¡NeuroMood Suite instalado correctamente!", SUCCESS)

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
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodSuite"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName",      0, winreg.REG_SZ,    "NeuroMood Suite")
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
        pid = self._auth_user_id or hashlib.sha256(self._email.encode()).hexdigest()[:24]

        db_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NeuroMood")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "nm_data.db")

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
            for clave, valor in [
                ("patient_name", self._nombre),
                ("patient_email", self._email),
                ("patient_id",   pid),
                ("auth_user_id",  self._auth_user_id),
                ("install_code",  self._codigo),
                ("perm_checklist_activacion", "1"),
                ("perm_checklist_manual",     "1"),
                ("perm_temporizador_manual",  "1"),
                ("perm_recordatorios_manual", "1"),
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
                if self._access_token:
                    try:
                        sb.auth.set_session(self._access_token, self._refresh_token)
                    except Exception:
                        try:
                            sb.postgrest.auth(self._access_token)
                        except Exception:
                            pass
                # Columnas que existen en la tabla patients del schema Supabase
                payload_full = {
                    "patient_id": pid, "patient_name": self._nombre,
                    "install_code": self._codigo,
                    "perm_checklist_activacion": True,
                    "perm_checklist_manual": True,
                    "perm_temporizador_manual": True,
                    "perm_recordatorios_manual": True,
                }
                try:
                    sb.table("patients").upsert(payload_full).execute()
                except Exception:
                    sb.table("patients").upsert({
                        "patient_id": pid, "patient_name": self._nombre,
                    }).execute()
                self.log_signal.emit("  Paciente registrado en la nube", SUCCESS)
        except Exception as e:
            self.log_signal.emit(f"  Registro en nube omitido ({str(e)[:50]})", WARNING_C)


# ── InstaladorNeuroMood ───────────────────────────────────────────────────────

class InstaladorNeuroMood(InstallerShell):
    APP_NAME = "Instalador Suite"
    WINDOW_ROLE = ""
    WINDOW_SIZE = (820, 660)
    STEPS = ["Bienvenida", "Cuenta", "Consentimiento", "Instalar", "Finalizar"]

    def __init__(self):
        super().__init__()
        self._pagina = 0
        self._install_dir: str = ""
        self._icon_dest: str = ""
        self._auth_ok = False
        self._auth_email = ""
        self._auth_user_id = ""
        self._auth_access_token = ""
        self._auth_refresh_token = ""
        self._consent_ok = False
        self._consent_payload: dict = {}
        self._auth_worker: _AuthWorker | None = None
        self._consent_worker: _ConsentWorker | None = None
        self._codigo_instalacion = ""
        self._worker: _InstalWorker | None = None
        self._email_needs_confirmation = False
        self._pending_auth_action = None

        self._build_shell()
        self.btn_sig.clicked.connect(self._siguiente)
        self.btn_ant.clicked.connect(self._anterior)

        # Pages
        self._add_page(lambda p: self._build_p0(p))
        self._add_page(lambda p: self._build_p1(p))
        self._add_page(lambda p: self._build_p2(p))
        self._add_page(lambda p: self._build_p3(p))
        self._add_page(lambda p: self._build_p4(p))

        self._apply_visual_qa_defaults()
        self._ir_a(0)

    def _apply_visual_qa_defaults(self):
        if os.environ.get("NM_VISUAL_QA") != "1":
            return
        qa_root = os.path.join(os.path.expanduser("~"), "NeuromoodV3_QA")
        if hasattr(self, "_ent_email"):
            self._ent_email.setText(os.environ.get("NM_QA_PATIENT_EMAIL", "visualqa@example.com"))
        if hasattr(self, "_ent_pwd"):
            self._ent_pwd.setText(os.environ.get("NM_QA_PATIENT_PASSWORD", "visualqa-pass"))
        self._ent_path.setText(
            os.environ.get(
                "NM_QA_SUITE_INSTALL_DIR",
                os.path.join(qa_root, "NeuroMood Suite"),
            )
        )

    # ── Override fade_to para textos de botón específicos ─────────────────────

    def _fade_to(self, n: int):
        super()._fade_to(n)
        if n == 4:
            self.btn_sig.setText("Finalizar")
        elif n == 3:
            self.btn_sig.setText("Instalar")
        elif n == 2:
            self.btn_sig.setText("Continuar")
        else:
            self.btn_sig.setText("Siguiente →")
        if n == 1:
            # Enable btn_sig if authenticated OR if waiting for email confirmation after signup
            self.btn_sig.setEnabled(self._auth_ok or self._email_needs_confirmation)
        elif n == 2:
            accepted = bool(getattr(self, "_chk_legal", None) and self._chk_legal.isChecked())
            self.btn_sig.setEnabled(self._consent_ok or accepted)
        else:
            self.btn_sig.setEnabled(True)
        self.btn_ant.setVisible(n > 0 and n < 4)

    # ── Página 0: Bienvenida ──────────────────────────────────────────────────

    def _build_p0(self, page: QWidget):
        from PyQt6.QtCore import Qt as _Qt
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 16, 28, 8)
        lay.setSpacing(0)

        # ── Row 2 columnas ────────────────────────────────────────────────────
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(28)

        # ── Columna izquierda ─────────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 16, 0, 0)
        ll.setSpacing(0)

        eyebrow = QLabel("BIENVENIDA")
        eyebrow.setStyleSheet(
            f"color: {VIOLET}; font-size: 11px; font-weight: 700;"
            f"letter-spacing: 3px; background: transparent;"
        )
        ll.addWidget(eyebrow)
        ll.addSpacing(8)

        title1 = QLabel("Una herramienta para")
        title1.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 30px; font-weight: 700;"
            f"letter-spacing: -1px; background: transparent;"
        )
        ll.addWidget(title1)

        try:
            t2 = GradientTextLabel("acompañarte", font_size=30)
            ll.addWidget(t2)
        except Exception:
            t2 = QLabel("acompañarte")
            t2.setStyleSheet(
                f"color: {TEAL}; font-size: 30px; font-weight: 700; background: transparent;"
            )
            ll.addWidget(t2)

        ll.addSpacing(14)

        desc = QLabel(
            "<b style='color:" + TEXT_PRIMARY + ";'>NeuroMood Suite</b> "
            "es una herramienta digital complementaria de bienestar emocional. "
            "En los próximos pasos vas a crear tu cuenta, aceptar el aviso "
            "legal y configurar la app."
        )
        desc.setWordWrap(True)
        desc.setTextFormat(_Qt.TextFormat.RichText)
        desc.setStyleSheet(
            f"color: {TEXT_SEC}; font-size: 13px; line-height: 1.6; background: transparent;"
        )
        ll.addWidget(desc)
        ll.addSpacing(20)

        for sym, col, txt in [
            ("✓", SUCCESS,    "Compatible con Windows 10 y 11"),
            ("◎", TEAL,       "Datos cifrados localmente y sincronización opcional"),
            ("⚡", WARNING_C,  "Liviano: ~280 MB de espacio en disco"),
        ]:
            feat = QFrame()
            feat.setStyleSheet(
                f"QFrame {{ background: {BG_SURFACE}; border-radius: 12px;"
                f"border: 1px solid {BORDER}; }}"
            )
            fr = QHBoxLayout(feat)
            fr.setContentsMargins(10, 8, 14, 8)
            fr.setSpacing(10)
            badge = QLabel(sym)
            badge.setFixedSize(28, 28)
            badge.setAlignment(_Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background: {col}33; color: {col}; border-radius: 8px;"
                f"font-size: 12px; font-weight: bold; border: none;"
            )
            fr.addWidget(badge)
            txt_lbl = QLabel(txt)
            txt_lbl.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 12px; background: transparent; border: none;"
            )
            fr.addWidget(txt_lbl, stretch=1)
            ll.addWidget(feat)
            ll.addSpacing(6)

        ll.addStretch()
        rl.addWidget(left, stretch=55)

        # ── Columna derecha — card con logo ───────────────────────────────────
        right = QFrame()
        right.setObjectName("WelcomeLogoCard")
        right.setStyleSheet(
            f"QFrame#WelcomeLogoCard {{"
            f"  background: {BG_SURFACE}; border-radius: 22px; border: 1px solid {BORDER};"
            f"}}"
        )
        rr = QVBoxLayout(right)
        rr.setContentsMargins(32, 40, 32, 40)
        rr.setSpacing(0)
        rr.setAlignment(_Qt.AlignmentFlag.AlignCenter)

        logo_c = QLabel()
        logo_c.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        logo_c.setStyleSheet("background: transparent; border: none;")
        try:
            from PIL import Image as PILImage
            from PyQt6.QtGui import QImage
            img = PILImage.open(recurso("logos-dark.png")).convert("RGBA")
            img.thumbnail((130, 72), PILImage.LANCZOS)
            qi = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format.Format_RGBA8888)
            logo_c.setPixmap(QPixmap.fromImage(qi))
        except Exception:
            logo_c.setText("NeuroMood")
            logo_c.setStyleSheet(
                f"color: {TEAL}; font-size: 22px; font-weight: bold; background: transparent;"
            )
        rr.addWidget(logo_c)
        rr.addSpacing(20)

        suite_lbl = QLabel("SUITE PARA PACIENTES")
        suite_lbl.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        suite_lbl.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 11px; font-weight: 700;"
            f"letter-spacing: 3px; background: transparent; border: none;"
        )
        rr.addWidget(suite_lbl)
        rr.addSpacing(6)

        ver_lbl = QLabel(f"v{self.APP_VERSION} · build {self.BUILD_DATE}")
        ver_lbl.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace;"
            f"background: transparent; border: none;"
        )
        rr.addWidget(ver_lbl)
        rl.addWidget(right, stretch=45)

        lay.addWidget(row, stretch=1)

    # ── Página 1: Registro ────────────────────────────────────────────────────

    def _build_p1(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 8)
        lay.setSpacing(8)

        title = QLabel("Cuenta NeuroMood")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        lay.addWidget(title)

        sub = QLabel("Inicia sesion o crea tu cuenta con Supabase Auth para continuar.")
        sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(sub)

        card = QFrame()
        card.setObjectName("AuthCard")
        card.setStyleSheet(
            f"QFrame#AuthCard {{background: {BG_SURFACE}; border-radius: 14px; border: 1px solid {BORDER};}}"
            f"QLabel {{background: transparent; border: none; font-size: 12px; color: {TEXT_SEC};}}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 16, 18, 14)
        cl.setSpacing(8)

        cl.addWidget(QLabel("Email"))
        self._ent_email = NMInput("tu@email.com") if _COMPONENTS_OK else QLineEdit()
        if not _COMPONENTS_OK:
            self._ent_email.setPlaceholderText("tu@email.com")
        cl.addWidget(self._ent_email)

        cl.addWidget(QLabel("Contraseña"))
        self._ent_pwd = NMInput("Minimo 6 caracteres") if _COMPONENTS_OK else QLineEdit()
        if not _COMPONENTS_OK:
            self._ent_pwd.setPlaceholderText("Minimo 6 caracteres")
        self._ent_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        cl.addWidget(self._ent_pwd)
        self._ent_email.textEdited.connect(self._invalidate_auth)
        self._ent_pwd.textEdited.connect(self._invalidate_auth)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_login = QPushButton("Iniciar sesión")
        self._btn_login.setObjectName("outline")
        self._btn_signup = QPushButton("Crear cuenta nueva")
        self._btn_signup.setObjectName("outline")
        for btn in (self._btn_login, self._btn_signup):
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_login.clicked.connect(lambda: self._start_auth("login"))
        self._btn_signup.clicked.connect(lambda: self._start_auth("signup"))
        btn_row.addWidget(self._btn_login)
        btn_row.addWidget(self._btn_signup)
        cl.addLayout(btn_row)

        self._btn_reset = QPushButton("¿Olvidaste tu contraseña?")
        self._btn_reset.setObjectName("outline")
        self._btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_reset.clicked.connect(self._reset_password)
        cl.addWidget(self._btn_reset, alignment=Qt.AlignmentFlag.AlignLeft)

        self._lbl_auth_status = QLabel("La cuenta es obligatoria para continuar.")
        self._lbl_auth_status.setWordWrap(True)
        self._lbl_auth_status.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 11px; background: transparent; border: none;"
        )
        cl.addWidget(self._lbl_auth_status)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        cl.addWidget(sep)

        lay.addWidget(card)

        # Dot "Conectado a Supabase" (spec mockup v3)
        dot_row = QWidget()
        dot_row.setStyleSheet("background: transparent;")
        dr = QHBoxLayout(dot_row)
        dr.setContentsMargins(4, 0, 0, 0)
        dr.setSpacing(8)
        self._dot_conn = QLabel()
        self._dot_conn.setFixedSize(8, 8)
        self._dot_conn.setStyleSheet(
            f"background: {TEXT_TERT}; border-radius: 4px;"
        )
        dr.addWidget(self._dot_conn)
        self._lbl_conn = QLabel("Verificando conexión con Supabase…")
        self._lbl_conn.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 11px; background: transparent;"
        )
        dr.addWidget(self._lbl_conn)
        dr.addStretch()
        lay.addWidget(dot_row)
        lay.addStretch()

    def _is_valid_email(self, email: str) -> bool:
        return "@" in email and "." in email.rsplit("@", 1)[-1]

    def _invalidate_auth(self):
        if not self._auth_ok:
            return
        self._auth_ok = False
        self._auth_email = ""
        self._auth_user_id = ""
        self._auth_access_token = ""
        self._auth_refresh_token = ""
        self._consent_ok = False
        self._consent_payload = {}
        self.btn_sig.setEnabled(False)
        self._set_auth_status("Volvé a iniciar sesión si cambiás el email o la contraseña.", WARNING_C)

    def _set_auth_status(self, text: str, color: str = TEXT_TERT):
        self._lbl_auth_status.setText(text)
        self._lbl_auth_status.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent; border: none;"
        )

    def _set_auth_loading(self, loading: bool):
        for w in (self._ent_email, self._ent_pwd, self._btn_login, self._btn_signup, self._btn_reset):
            w.setEnabled(not loading)
        if self._pagina == 1:
            self.btn_sig.setEnabled(self._auth_ok and not loading)

    def _start_auth(self, action: str):
        email = self._ent_email.text().strip().lower()
        pwd = self._ent_pwd.text()
        self._auth_ok = False
        self._consent_ok = False
        self._consent_payload = {}
        self.btn_sig.setEnabled(False)
        if not self._is_valid_email(email):
            self._set_auth_status("Ingresá un email valido.", ERROR_C)
            return
        if len(pwd) < 6:
            self._set_auth_status("La contraseña debe tener al menos 6 caracteres.", ERROR_C)
            return

        label = "Iniciando sesión..." if action == "login" else "Creando cuenta..."
        self._set_auth_status(label, TEXT_SEC)
        self._set_auth_loading(True)
        self._auth_worker = _AuthWorker(action, email, pwd, self)
        self._auth_worker.done_signal.connect(self._on_auth_done)
        self._auth_worker.error_signal.connect(self._on_auth_error)
        self._auth_worker.start()

    def _on_auth_done(self, action: str, message: str, user_id: str, can_continue: bool,
                       email: str, access_token: str, refresh_token: str):
        self._set_auth_loading(False)
        self._auth_ok = bool(can_continue and user_id)
        self._pending_auth_action = None  # Clear pending action
        
        if self._auth_ok:
            self._auth_email = email
            self._auth_user_id = user_id
            self._auth_access_token = access_token
            self._auth_refresh_token = refresh_token
            self._consent_payload = _load_local_consent(email, user_id) or {}
            self._consent_ok = bool(self._consent_payload)
            self._codigo_instalacion = secrets.token_hex(3).upper()
            self.btn_sig.setEnabled(True)
            # Actualizar dot de conexión
            if hasattr(self, "_dot_conn"):
                self._dot_conn.setStyleSheet(
                    f"background: {SUCCESS}; border-radius: 4px;"
                    f"border: none; box-shadow: 0 0 0 4px {SUCCESS}22;"
                )
            if hasattr(self, "_lbl_conn"):
                self._lbl_conn.setText(f"Conectado a Supabase · {email}")
                self._lbl_conn.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; background: transparent;")
            if self._consent_ok:
                self._set_auth_status(
                    message + "\nConsentimiento legal vigente registrado para esta versión.",
                    SUCCESS,
                )
            else:
                self._set_auth_status(message + "\nEl siguiente paso requiere aceptar el aviso legal.", SUCCESS)
        else:
            # Check if this is a signup that needs email confirmation
            if action == "signup" and not can_continue and user_id:
                # User created account but needs email confirmation
                self._email_needs_confirmation = True
                self._auth_email = email
                self._auth_user_id = user_id
                self._set_auth_status(
                    message + "\nRevisa tu correo para confirmar el email antes de continuar.", 
                    WARNING_C
                )
            else:
                self.btn_sig.setEnabled(False)
                self._set_auth_status(message, WARNING_C if action == "signup" else SUCCESS)

    def _on_auth_error(self, message: str):
        self._set_auth_loading(False)
        self._auth_ok = False
        self._consent_ok = False
        self._email_needs_confirmation = False
        self.btn_sig.setEnabled(False)
        self._set_auth_status(message, ERROR_C)

    def _reset_password(self):
        default_email = self._ent_email.text().strip().lower() if hasattr(self, "_ent_email") else ""
        email, ok = QInputDialog.getText(
            self,
            "Restablecer contraseña",
            "Email de tu cuenta:",
            QLineEdit.EchoMode.Normal,
            default_email,
        )
        email = email.strip().lower()
        if not ok:
            return
        if not self._is_valid_email(email):
            self._set_auth_status("Ingresá un email valido para restablecer la contraseña.", ERROR_C)
            return
        self._ent_email.setText(email)
        self._set_auth_status("Enviando enlace de restablecimiento...", TEXT_SEC)
        self._set_auth_loading(True)
        self._auth_worker = _AuthWorker("reset", email, "", self)
        self._auth_worker.done_signal.connect(self._on_auth_done)
        self._auth_worker.error_signal.connect(self._on_auth_error)
        self._auth_worker.start()

    def _build_p2(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 16, 28, 8)
        lay.setSpacing(8)

        title = QLabel("Aviso legal y consentimiento")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold;")
        lay.addWidget(title)

        sub = QLabel("Obligatorio para asociar la aceptación a tu cuenta antes de instalar NeuroMood Suite.")
        sub.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
        lay.addWidget(sub)

        # Card legal con header v3
        panel = QFrame()
        panel.setObjectName("LegalPanel")
        panel.setStyleSheet(
            f"QFrame#LegalPanel {{background: {BG_SURFACE}; border-radius: 14px; border: 1px solid {BORDER};}}"
        )
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        # Header de la card legal
        legal_hdr = QFrame()
        legal_hdr.setStyleSheet(
            f"QFrame {{ background: {BG_ELEVATED}; border-radius: 14px 14px 0 0;"
            f"border-bottom: 1px solid {BORDER}; border-top: none; border-left: none; border-right: none; }}"
        )
        hh = QHBoxLayout(legal_hdr)
        hh.setContentsMargins(14, 10, 14, 10)
        hh.setSpacing(8)
        legal_icon = QLabel("📋")
        legal_icon.setStyleSheet("font-size: 14px; background: transparent;")
        hh.addWidget(legal_icon)
        legal_title_lbl = QLabel("Aviso legal · Consentimiento · Tratamiento de datos")
        legal_title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 700; background: transparent;"
        )
        hh.addWidget(legal_title_lbl, stretch=1)
        ver_tag = QLabel(f"v.legal-{DISCLAIMER_VERSION.replace('legal-', '')}")
        ver_tag.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace; background: transparent;"
        )
        hh.addWidget(ver_tag)
        pl.addWidget(legal_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(180)
        scroll.setStyleSheet("QScrollArea {background: transparent; border: none;}")
        content = QLabel(LEGAL_DISCLAIMER_TEXT)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content.setStyleSheet(
            f"color: {TEXT_SEC}; font-size: 11px; line-height: 1.4; background: transparent; border: none;"
        )
        content.setContentsMargins(14, 12, 14, 8)
        scroll.setWidget(content)
        pl.addWidget(scroll)

        # Footer de la card con hash + privacidad en mono
        legal_ftr = QFrame()
        legal_ftr.setStyleSheet(
            f"QFrame {{ background: {BG_ELEVATED}; border-radius: 0 0 14px 14px;"
            f"border-top: 1px solid {BORDER}; border-bottom: none; border-left: none; border-right: none; }}"
        )
        fh = QHBoxLayout(legal_ftr)
        fh.setContentsMargins(14, 8, 14, 8)
        hash_lbl = QLabel(f"Hash: {DISCLAIMER_TEXT_HASH[:8]}...{DISCLAIMER_TEXT_HASH[-4:]}")
        hash_lbl.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace; background: transparent;"
        )
        fh.addWidget(hash_lbl)
        fh.addStretch()
        priv_lbl = QLabel(f"Privacidad: {PRIVACY_VERSION}")
        priv_lbl.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace; background: transparent;"
        )
        fh.addWidget(priv_lbl)
        pl.addWidget(legal_ftr)
        lay.addWidget(panel)

        # Card de aceptación con badges
        accept_card = QFrame()
        accept_card.setObjectName("AcceptCard")
        accept_card.setStyleSheet(
            f"QFrame#AcceptCard {{background: {BG_SURFACE}; border-radius: 12px; border: 1px solid {BORDER};}}"
        )
        ac = QHBoxLayout(accept_card)
        ac.setContentsMargins(14, 12, 14, 12)
        ac.setSpacing(12)

        self._chk_legal = QCheckBox()
        self._chk_legal.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chk_legal.setStyleSheet(
            f"QCheckBox {{spacing: 0px;}}"
            f"QCheckBox::indicator {{width: 18px; height: 18px; border-radius: 5px;"
            f"border: 1px solid {BORDER}; background: {BG_SURFACE};}}"
            f"QCheckBox::indicator:checked {{"
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {GRAD_FROM},stop:1 {GRAD_TO});"
            f"border-color: {GRAD_MID};}}"
        )
        self._chk_legal.stateChanged.connect(self._on_legal_check_changed)
        ac.addWidget(self._chk_legal, alignment=Qt.AlignmentFlag.AlignTop)

        chk_col = QVBoxLayout()
        chk_col.setSpacing(6)
        chk_title = QLabel("Leí y acepto el aviso legal, el consentimiento de uso y el tratamiento de datos personales y sensibles")
        chk_title.setWordWrap(True)
        chk_title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        chk_col.addWidget(chk_title)
        badges_row = QHBoxLayout()
        badges_row.setSpacing(14)
        for badge_txt in ["✓ Constancia local en AppData", "✓ Constancia remota auditable"]:
            bl = QLabel(badge_txt)
            bl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; background: transparent;")
            badges_row.addWidget(bl)
        badges_row.addStretch()
        chk_col.addLayout(badges_row)
        ac.addLayout(chk_col, stretch=1)
        lay.addWidget(accept_card)

        # Warning card — emergencias
        warn_card = QFrame()
        warn_card.setStyleSheet(
            f"QFrame {{ background: {WARNING_C}18; border-radius: 12px; border: 1px solid {WARNING_C}44; }}"
        )
        wc = QHBoxLayout(warn_card)
        wc.setContentsMargins(14, 11, 14, 11)
        wc.setSpacing(10)
        warn_icon = QLabel("⚠")
        warn_icon.setStyleSheet(f"color: {WARNING_C}; font-size: 16px; background: transparent;")
        wc.addWidget(warn_icon, alignment=Qt.AlignmentFlag.AlignTop)
        warn_txt = QLabel(
            "<b style='color:" + WARNING_C + ";'>NeuroMood Suite no es un servicio de emergencias.</b>"
            " En caso de crisis, comunicate con un servicio de emergencias o profesional de confianza inmediatamente."
        )
        warn_txt.setWordWrap(True)
        warn_txt.setTextFormat(Qt.TextFormat.RichText)
        warn_txt.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
        wc.addWidget(warn_txt, stretch=1)
        lay.addWidget(warn_card)

        self._lbl_legal_status = QLabel(
            "Para continuar se registrará una constancia local y remota auditable."
        )
        self._lbl_legal_status.setWordWrap(True)
        self._lbl_legal_status.setStyleSheet(f"color: {TEXT_TERT}; font-size: 11px;")
        lay.addWidget(self._lbl_legal_status)
        lay.addStretch()

        if self._consent_ok:
            self._chk_legal.setChecked(True)
            self._chk_legal.setEnabled(False)
            self._set_legal_status("Consentimiento vigente ya registrado para esta cuenta y versión.", SUCCESS)

    def _on_legal_check_changed(self):
        if self._pagina == 2 and not self._consent_ok:
            self.btn_sig.setEnabled(self._chk_legal.isChecked())

    def _set_legal_status(self, text: str, color: str = TEXT_TERT):
        if hasattr(self, "_lbl_legal_status"):
            self._lbl_legal_status.setText(text)
            self._lbl_legal_status.setStyleSheet(f"color: {color}; font-size: 11px;")

    def _set_consent_loading(self, loading: bool):
        if hasattr(self, "_chk_legal") and not self._consent_ok:
            self._chk_legal.setEnabled(not loading)
        self.btn_sig.setEnabled(False if loading else (self._consent_ok or self._chk_legal.isChecked()))
        self.btn_sig.setText("Registrando..." if loading else "Continuar")

    def _register_consent(self):
        if self._consent_ok:
            self._ir_a(3)
            return
        if not self._auth_ok:
            self._set_legal_status("Primero iniciá sesión para asociar el consentimiento a tu cuenta.", ERROR_C)
            return
        if not getattr(self, "_chk_legal", None) or not self._chk_legal.isChecked():
            self._set_legal_status("Debés aceptar el aviso legal y el tratamiento de datos para continuar.", ERROR_C)
            return
        self._set_legal_status("Registrando consentimiento remoto seguro...", TEXT_SEC)
        self._set_consent_loading(True)
        self._consent_worker = _ConsentWorker(
            self._auth_email,
            self._auth_user_id,
            self._auth_access_token,
            self._auth_refresh_token,
            self,
        )
        self._consent_worker.done_signal.connect(self._on_consent_done)
        self._consent_worker.error_signal.connect(self._on_consent_error)
        self._consent_worker.start()

    def _on_consent_done(self, payload: dict):
        self._consent_ok = True
        self._consent_payload = payload
        self._set_consent_loading(False)
        self._set_legal_status("Consentimiento registrado correctamente. Ya podés continuar.", SUCCESS)
        self._ir_a(3)

    def _on_consent_error(self, message: str):
        self._consent_ok = False
        self._set_consent_loading(False)
        self._set_legal_status(message, ERROR_C)

    def _build_p3(self, page: QWidget):
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 8)
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
        self._ent_path = NMInput() if _COMPONENTS_OK else QLineEdit(DEFAULT_INSTALL)
        self._ent_path.setText(DEFAULT_INSTALL)
        pr.addWidget(self._ent_path, stretch=1)
        btn_browse = QPushButton("Examinar")
        btn_browse.setObjectName("outline")
        btn_browse.setFixedSize(110, 36)
        btn_browse.clicked.connect(self._browse)
        pr.addWidget(btn_browse)
        lay.addWidget(path_row)
        lay.addSpacing(12)

        if _COMPONENTS_OK:
            self._install_progress = NMInstallProgress(accent_key="teal")
            self._install_progress.set_progress(0, "Presiona 'Instalar' para continuar.")
            lay.addWidget(self._install_progress)
            self._progress_bar = self._install_progress
            self._progress_lbl = self._install_progress._label
            self._log_layout = None
            self._log_scroll = None
        else:
            self._progress_bar = QProgressBar()
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
            lay.addWidget(self._progress_bar)
            self._progress_lbl = QLabel("Presiona 'Instalar' para continuar.")
            self._progress_lbl.setStyleSheet(f"color: {TEXT_TERT}; font-size: 12px;")
            lay.addWidget(self._progress_lbl)
        lay.addStretch()

    # ── Página 4: Finalizar ───────────────────────────────────────────────────

    def _build_p4(self, page: QWidget):
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import QGridLayout
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 12, 28, 8)
        lay.setSpacing(0)

        # Círculo check 88px gradient + glow ring
        circle_row = QWidget()
        circle_row.setStyleSheet("background: transparent;")
        crl = QVBoxLayout(circle_row)
        crl.setContentsMargins(0, 0, 0, 0)
        crl.setAlignment(_Qt.AlignmentFlag.AlignHCenter)

        check_circle = QFrame()
        check_circle.setObjectName("CheckCircle")
        check_circle.setFixedSize(88, 88)
        check_circle.setStyleSheet(
            f"QFrame#CheckCircle {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"    stop:0 {GRAD_FROM}, stop:1 {GRAD_TO});"
            f"  border-radius: 44px;"
            f"  border: 4px solid transparent;"
            f"}}"
        )
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor as _QColor
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(32)
        glow.setOffset(0, 8)
        glow.setColor(_QColor(94, 234, 212, 140))
        check_circle.setGraphicsEffect(glow)

        check_lbl = QLabel("✓", check_circle)
        check_lbl.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        check_lbl.setGeometry(0, 0, 88, 88)
        check_lbl.setStyleSheet(
            "color: #ffffff; font-size: 38px; font-weight: 900; background: transparent;"
        )
        crl.addWidget(check_circle, alignment=_Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(circle_row)
        lay.addSpacing(14)

        # Eyebrow LISTO + título
        eyebrow_ok = QLabel("LISTO")
        eyebrow_ok.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
        eyebrow_ok.setStyleSheet(
            f"color: {SUCCESS}; font-size: 11px; font-weight: 700;"
            f"letter-spacing: 4px; background: transparent;"
        )
        lay.addWidget(eyebrow_ok)
        lay.addSpacing(4)

        title_ok = QLabel("Instalación completada")
        title_ok.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
        title_ok.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 700;"
            f"letter-spacing: -1px; background: transparent;"
        )
        lay.addWidget(title_ok)
        lay.addSpacing(6)

        desc_ok = QLabel(
            "NeuroMood Suite quedó instalado en tu equipo.\n"
            "Tu cuenta y consentimiento legal están registrados."
        )
        desc_ok.setAlignment(_Qt.AlignmentFlag.AlignHCenter)
        desc_ok.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; background: transparent;")
        lay.addWidget(desc_ok)
        lay.addSpacing(20)

        # Grid 2×2 de info cards
        grid_w = QWidget()
        grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)

        self._info_cards_data = [
            ("💾", "CARPETA", self._install_dir or DEFAULT_INSTALL, True),
            ("👤", "CUENTA",  self._auth_email or "—", False),
            ("📌", "VERSIÓN", f"NeuroMood Suite {self.APP_VERSION}", True),
            ("✅", "CONSENTIMIENTO", f"Registrado · v.legal-{DISCLAIMER_VERSION.replace('legal-','')}", False),
        ]
        for idx, (ic, key, val, mono) in enumerate(self._info_cards_data):
            card = QFrame()
            card.setObjectName(f"InfoCard_{idx}")
            card.setStyleSheet(
                f"QFrame {{background: {BG_SURFACE}; border-radius: 12px; border: 1px solid {BORDER};}}"
            )
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.setSpacing(10)
            icon_badge = QLabel(ic)
            icon_badge.setFixedSize(36, 36)
            icon_badge.setAlignment(_Qt.AlignmentFlag.AlignCenter)
            icon_badge.setStyleSheet(
                f"background: {TEAL}22; border-radius: 10px; font-size: 16px; border: none;"
            )
            cl.addWidget(icon_badge)
            txt_col = QVBoxLayout()
            txt_col.setSpacing(2)
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(
                f"color: {TEXT_TERT}; font-size: 10px; font-weight: 700;"
                f"letter-spacing: 2px; background: transparent;"
            )
            txt_col.addWidget(key_lbl)
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 500; background: transparent;"
                + (f"font-family: Consolas, monospace;" if mono else "")
            )
            val_lbl.setWordWrap(False)
            txt_col.addWidget(val_lbl)
            if key == "CUENTA":
                self._lbl_cuenta_val = val_lbl
            elif key == "CARPETA":
                self._lbl_carpeta_val = val_lbl
            cl.addLayout(txt_col, stretch=1)
            grid.addWidget(card, idx // 2, idx % 2)
        lay.addWidget(grid_w)
        lay.addSpacing(12)

        # Info card con accesos directos
        info_card = QFrame()
        info_card.setStyleSheet(
            f"QFrame {{ background: {BG_ELEVATED}; border-radius: 12px; border: 1px solid {BORDER}; }}"
        )
        ic_lay = QHBoxLayout(info_card)
        ic_lay.setContentsMargins(14, 10, 14, 10)
        ic_lay.setSpacing(10)
        ic_lay.addWidget(QLabel("ℹ"))

        shortcuts_col = QVBoxLayout()
        shortcuts_col.setSpacing(4)
        info_txt = QLabel(
            "Se creó un acceso directo en el escritorio. "
            "Podés desinstalar desde Agregar o quitar programas."
        )
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")
        shortcuts_col.addWidget(info_txt)

        chk_row = QHBoxLayout()
        chk_row.setSpacing(16)
        self._chk_escritorio = NMCustomCheck(
            "Escritorio", checked=True, strike_on_check=False
        )
        self._chk_escritorio.setChecked(True)
        chk_row.addWidget(self._chk_escritorio)
        self._chk_menu = NMCustomCheck(
            "Menú inicio", checked=False, strike_on_check=False
        )
        self._chk_menu.setChecked(False)
        chk_row.addWidget(self._chk_menu)
        chk_row.addStretch()
        shortcuts_col.addLayout(chk_row)
        ic_lay.addLayout(shortcuts_col, stretch=1)
        lay.addWidget(info_card)
        lay.addStretch()

    # ── Navegación ────────────────────────────────────────────────────────────

    def _anterior(self):
        if self._pagina == 1:
            self._ir_a(0)
        elif self._pagina == 2:
            self._ir_a(1)
        elif self._pagina == 3:
            self._ir_a(2 if not self._consent_ok else 1)

    def _siguiente(self):
        if self._pagina == 0:
            self._ir_a(1)

        elif self._pagina == 1:
            if not self._auth_ok:
                self._set_auth_status("Primero inicia sesion o crea tu cuenta para continuar.", ERROR_C)
                return
            if self._consent_ok:
                self._ir_a(3)
            else:
                self._ir_a(2)

        elif self._pagina == 2:
            self._register_consent()

        elif self._pagina == 3:
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

        elif self._pagina == 4:
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
        if hasattr(self, "_install_progress"):
            self._install_progress.append_line(texto)
            QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            return
        lbl = QLabel(texto)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent; padding: 1px 2px;"
        )
        self._log_layout.addWidget(lbl)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        sb = self._log_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _set_progress(self, v: float, t: str):
        if hasattr(self, "_install_progress"):
            self._install_progress.set_progress(int(v * 100), t)
        elif _COMPONENTS_OK:
            self._progress_bar.animate_to(v, duration=200)
        else:
            self._progress_bar.setValue(int(v * 100))
        self._progress_lbl.setText(t)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def _iniciar_instalacion(self, path: str):
        self._worker = _InstalWorker(
            path,
            self._auth_email,
            self._auth_user_id,
            self._codigo_instalacion,
            access_token=self._auth_access_token,
            refresh_token=self._auth_refresh_token,
            parent=self,
        )
        self._worker.log_signal.connect(self._log)
        self._worker.progress_signal.connect(self._set_progress)
        self._worker.done_signal.connect(self._on_install_done)
        self._worker.error_signal.connect(self._on_install_error)
        self._worker.start()

    def _on_install_done(self, install_dir: str, icon_dest: str):
        self._install_dir = install_dir
        self._icon_dest = icon_dest
        if hasattr(self, "_lbl_cuenta_val"):
            self._lbl_cuenta_val.setText(self._auth_email or "—")
        if hasattr(self, "_lbl_carpeta_val"):
            self._lbl_carpeta_val.setText(install_dir or DEFAULT_INSTALL)
        QTimer.singleShot(
            900,
            lambda: self._ir_a(4) if not sip.isdeleted(self) else None,
        )

    def _on_install_error(self, tipo: str):
        if tipo == "permission":
            self._progress_lbl.setStyleSheet(f"color: {ERROR_C}; font-size: 12px; font-weight: bold;")
            self._progress_lbl.setText("Sin permisos. Elegi otra carpeta.")
        else:
            self._progress_lbl.setStyleSheet(f"color: {ERROR_C}; font-size: 12px; font-weight: bold;")
            self._progress_lbl.setText("Error inesperado. Revisa el log arriba.")
        self._ir_a(3)
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
    from shared.crash_log import setup as _crash_setup
    _crash_setup("installer_suite")
    app = QApplication(sys.argv)
    win = InstaladorNeuroMood()
    win.show()
    sys.exit(app.exec())
