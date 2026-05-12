"""config.py — Lectura de credenciales desde .env (nunca hardcoded en código)."""
import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

_cache: dict = {}


def _load_env():
    if _cache:
        return
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        _cache[key.strip()] = value.strip().strip("\"'")


def get(key: str, default: str = "") -> str:
    _load_env()
    return os.environ.get(key) or _cache.get(key) or default


def supabase_url() -> str:
    return get("SUPABASE_URL")


def supabase_key() -> str:
    return get("SUPABASE_KEY")
