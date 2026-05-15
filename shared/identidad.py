"""identidad.py — Gestión de identidad del paciente (patient_id único)."""
import hashlib
from shared.db import guardar_config, leer_config


def _hash_pwd(password: str) -> str:
    """Hash SHA-256 determinista de contraseña. Misma password → mismo hash."""
    return hashlib.sha256(password.encode()).hexdigest()


def _is_hashed(stored: str) -> bool:
    """Detecta si un valor ya fue hasheado (64 chars hex)."""
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored)


def generar_patient_id(nombre: str, password: str, install_code: str = "") -> str:
    """Genera patient_id determinista. install_code asegura unicidad entre instalaciones."""
    clave = f"{nombre.strip().lower()}:{password}:{install_code.lower()}"
    return hashlib.sha256(clave.encode()).hexdigest()[:24]


def guardar_password(password: str):
    """Almacena hash seguro de la contraseña. SIEMPRE usar esta función."""
    guardar_config("patient_pwd", _hash_pwd(password))


def obtener_password_hash() -> str:
    """Devuelve hash almacenado. Si detecta texto plano, lo migra automáticamente."""
    stored = leer_config("patient_pwd", "")
    if not stored:
        return ""
    if not _is_hashed(stored):
        # Migrar password en texto plano a hash
        hashed = _hash_pwd(stored)
        guardar_config("patient_pwd", hashed)
        return hashed
    return stored


def registrar_paciente(nombre: str, password: str, install_code: str = "") -> str:
    pid = generar_patient_id(nombre, password, install_code)
    guardar_config("patient_id", pid)
    guardar_config("patient_name", nombre.strip())
    guardar_config("install_code", install_code)
    guardar_password(password)
    return pid


def obtener_patient_id() -> str:
    return leer_config("patient_id", "")


def obtener_nombre_paciente() -> str:
    return leer_config("patient_name", "")


def paciente_registrado() -> bool:
    return bool(obtener_patient_id())
