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


def _verify_pwd(password: str, stored_hash: str, salt: str = "") -> bool:
    """Verifica password contra hash almacenado (comparación en tiempo constante).

    Compatible con _hash_pwd: usa el mismo salt determinista.
    """
    import hmac as _hmac

    candidate = _hash_pwd(password, salt)
    return _hmac.compare_digest(candidate, stored_hash)


def _is_hashed(stored: str) -> bool:
    """Detecta si un valor ya fue hasheado (64 chars hex)."""
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored)


# NOTA v1.0 (reestructura, frente duplicados): la derivación legacy de
# patient_id (sha256(nombre:password:install_code)[:24]) fue ELIMINADA.
# Generaba un id NUEVO en cada reinstalación (install_code se perdía con el
# uninstall) => pacientes duplicados en Supabase. El alta canónica es
# app/onboarding_qt._save: patient_id = auth.user.id (Supabase Auth) —
# idempotente por cuenta: reinstalar + iniciar sesión = mismo id.
# Las filas legacy existentes se migran con db/patients_dedupe.sql (manual).


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


def obtener_patient_id() -> str:
    return leer_config("patient_id", "")


def obtener_nombre_paciente() -> str:
    return leer_config("patient_name", "")


def paciente_registrado() -> bool:
    return bool(obtener_patient_id())
