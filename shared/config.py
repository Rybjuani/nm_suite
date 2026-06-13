"""config.py - Lectura de credenciales desde entorno o .env externo.

Prioridad efectiva:
  1. Variables de entorno del sistema.
  2. APPDATA/NeuroMood/.env    (instalacion paciente).
  3. APPDATA/NeuroMoodHub/.env (instalacion Hub).
  4. Raiz del proyecto / cwd   (solo modo desarrollo no congelado).

No se leen .env embebidos en bundles PyInstaller para evitar distribuir
secretos privados dentro de ejecutables o instaladores.
"""

import os
import sys
from pathlib import Path


_cache: dict = {}


def _env_candidates() -> list:
    """Devuelve las rutas candidatas para .env en orden de prioridad."""
    candidates = []
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")

    # Detectar dinámicamente si el script o ejecutable en ejecución pertenece al Hub
    is_hub = False
    if sys.argv and sys.argv[0]:
        entry_lower = sys.argv[0].lower()
        path_parts = Path(entry_lower).parts
        if "hub" in path_parts or any(
            "hub" in part for part in path_parts if part.endswith((".py", ".exe"))
        ):
            is_hub = True

    if is_hub:
        # 1. %APPDATA%\NeuroMoodHub\.env — instalacion del Hub
        candidates.append(Path(appdata) / "NeuroMoodHub" / ".env")
    else:
        # 1. %APPDATA%\NeuroMood\.env  — instalacion del paciente
        candidates.append(Path(appdata) / "NeuroMood" / ".env")

    # 3. Desarrollo local. En produccion frozen, .env debe vivir en AppData
    # o venir de variables de entorno del sistema, no junto al ejecutable.
    if not getattr(sys, "frozen", False):
        candidates.append(Path(__file__).resolve().parent.parent / ".env")
        candidates.append(Path(os.getcwd()) / ".env")

    seen = set()
    unique = []
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _load_env():
    if _cache:
        return
    for env_path in _env_candidates():
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key and key not in _cache:
                        _cache[key] = value
            except Exception:
                pass


def get(key: str, default: str = "") -> str:
    _load_env()
    # Variables de entorno del sistema tienen prioridad sobre .env
    return os.environ.get(key) or _cache.get(key) or default


def supabase_url() -> str:
    return get("SUPABASE_URL")


def supabase_key() -> str:
    # Preferir aliases publicos en desarrollo para evitar usar service_role
    # cuando ambos valores existen en el entorno local.
    return get("SUPABASE_ANON_KEY") or get("SUPABASE_PUBLIC_KEY") or get("SUPABASE_KEY")


def supabase_hub_key() -> str:
    """Clave Supabase para el Hub profesional.

    El Hub entra libre, pero con RLS endurecido necesita una
    clave operativa propia para leer/escribir datos del panel. La Suite sigue
    usando supabase_key(), que prioriza anon/public y nunca mira estos aliases.
    """
    return (
        get("SUPABASE_HUB_KEY")
        or get("SUPABASE_SERVICE_ROLE_KEY")
        or get("SUPABASE_SERVICE_KEY")
        or supabase_key()
    )
