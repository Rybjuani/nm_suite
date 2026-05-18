"""identidad.py — Gestión de identidad del paciente (patient_id único)."""
import hashlib
from shared.db import guardar_config, leer_config

_PWD_ITERATIONS = 100_000
_PWD_KEY_LEN = 32


def _hash_pwd(password: str, salt: str = "") -> str:
    """Hash PBKDF2-SHA256 con salt determinista. Misma (password, salt) → mismo hash."""
    s = salt.encode() if salt else b"NeuromoodV3"
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), s, _PWD_ITERATIONS, dklen=_PWD_KEY_LEN)
    return dk.hex()


def _is_hashed(stored: str) -> bool:
    """Detecta si un valor ya fue hasheado (64 chars hex)."""
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored)


def generar_patient_id(nombre: str, password: str, install_code: str = "") -> str:
    """Genera patient_id determinista. install_code asegura unicidad entre instalaciones."""
    clave = f"{nombre.strip().lower()}:{password}:{install_code.lower()}"
    return hashlib.sha256(clave.encode()).hexdigest()[:24]


def guardar_password(password: str, install_code: str = ""):
    """Almacena hash PBKDF2-SHA256. Salt = install_code (único por instalación)."""
    h = _hash_pwd(password, install_code)
    guardar_config("patient_pwd", h)


def obtener_password_hash(install_code: str = "") -> str:
    """Devuelve hash almacenado. Si detecta texto plano, lo migra automáticamente a PBKDF2."""
    stored = leer_config("patient_pwd", "")
    if not stored:
        return ""
    if not _is_hashed(stored):
        h = _hash_pwd(stored, install_code)
        guardar_config("patient_pwd", h)
        return h
    return stored


def registrar_paciente(nombre: str, password: str, install_code: str = "") -> str:
    pid = generar_patient_id(nombre, password, install_code)
    guardar_config("patient_id", pid)
    guardar_config("patient_name", nombre.strip())
    guardar_config("install_code", install_code)
    guardar_password(password, install_code)
    return pid


def obtener_patient_id() -> str:
    return leer_config("patient_id", "")


def obtener_nombre_paciente() -> str:
    return leer_config("patient_name", "")


def paciente_registrado() -> bool:
    return bool(obtener_patient_id())
