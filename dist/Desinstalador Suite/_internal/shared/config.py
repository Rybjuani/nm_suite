"""config.py - Lectura de credenciales desde .env

Busca el .env en este orden de prioridad:
  1. APPDATA/NeuroMood/.env    (produccion paciente - copiado por instalador)
  2. APPDATA/NeuroMoodHub/.env (produccion Hub - copiado por instalador pro)
  3. Bundle PyInstaller        (_MEIPASS / _internal)
  4. Carpeta del ejecutable    (produccion alternativa)
  5. Raiz del proyecto         (modo desarrollo)
  6. Variables de entorno del sistema (siempre disponibles)
"""
import os
import sys
from pathlib import Path


_cache: dict = {}


def _env_candidates() -> list:
    """Devuelve las rutas candidatas para .env en orden de prioridad."""
    candidates = []
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")

    # 1. %APPDATA%\NeuroMood\.env  — instalacion del paciente
    candidates.append(Path(appdata) / "NeuroMood" / ".env")

    # 2. %APPDATA%\NeuroMoodHub\.env — instalacion del Hub
    candidates.append(Path(appdata) / "NeuroMoodHub" / ".env")

    # 3. Bundle PyInstaller. En --onedir los add-data suelen quedar en _internal,
    # y en --onefile en sys._MEIPASS. El instalador necesita este fallback antes
    # de copiar .env a AppData.
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", ""))
        if str(meipass):
            candidates.append(meipass / ".env")
        exe_dir = Path(sys.executable).parent
        candidates.append(exe_dir / "_internal" / ".env")

    # 4. Carpeta del ejecutable (frozen) o raiz del proyecto (dev)
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / ".env")
    else:
        candidates.append(Path(__file__).resolve().parent.parent / ".env")

    # 5. Directorio de trabajo actual
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
    return get("SUPABASE_KEY")
