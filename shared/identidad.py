"""identidad.py — Gestión de identidad del paciente (patient_id único)."""
import hashlib
from shared.db import guardar_config, leer_config


def generar_patient_id(nombre: str, password: str, install_code: str = "") -> str:
    """Genera patient_id determinista. install_code asegura unicidad entre instalaciones."""
    clave = f"{nombre.strip().lower()}:{password}:{install_code.lower()}"
    return hashlib.sha256(clave.encode()).hexdigest()[:24]


def registrar_paciente(nombre: str, password: str, install_code: str = "") -> str:
    pid = generar_patient_id(nombre, password, install_code)
    guardar_config("patient_id", pid)
    guardar_config("patient_name", nombre.strip())
    guardar_config("install_code", install_code)
    return pid


def obtener_patient_id() -> str:
    return leer_config("patient_id", "")


def obtener_nombre_paciente() -> str:
    return leer_config("patient_name", "")


def paciente_registrado() -> bool:
    return bool(obtener_patient_id())
