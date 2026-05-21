"""remote_config.py — util de configuración remota 2 niveles (F2.0.B).

Implementa el patrón general documentado en:
    - AUDITORIA_NEUROMOOD.md §9.4.A
    - AI_PROJECT_CONTEXT.md §15.6
    - db/hub_config_schema.sql

Jerarquía de lookup en `t(key, default, patient_id=None)`:

    1. scope = "patient:<patient_id>"   (override individual, si se pidió)
    2. scope = "global"                  (configuración del equipo)
    3. default hardcoded                 (último recurso, siempre presente)

La función `t()` siempre lee del cache local SQLite `remote_config_cache`.
Nunca golpea Supabase de forma síncrona durante el render. La actualización
del cache pasa por:

    - `refresh_from_supabase(patient_id)` (standalone, este módulo)
    - `shared.sync._importar_hub_config(sb, patient_id)` (F2.0.C, integrado
      en el pipeline de sync_completo / verificar_asignaciones).

Diseño:
    - Sin dependencia de PyQt6 — librería pura. Suite y Hub la consumen.
    - Cero panics: cualquier excepción de DB/red/parse cae al `default`.
    - Valores en disco: JSON string. El `value` de Supabase es JSONB
      (Python lo recibe ya deserializado), pero acá lo guardamos como
      texto para no atar el cache a un tipo Python específico.

Ejemplos:
    >>> from shared.remote_config import t
    >>> t("home.greeting", "Hola")
    'Hola'   # devuelve default mientras el cache esté vacío
    >>> t("home.greeting", "Hola", patient_id="abc-123")
    'Hola'
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Iterable, Optional

from shared.db import obtener_conexion

_log = logging.getLogger(__name__)


# ── Lectura: t() ─────────────────────────────────────────────────────────────


def t(key: str, default: Any, patient_id: Optional[str] = None) -> Any:
    """Devuelve el valor configurable para `key`, con jerarquía 2 niveles.

    Orden de lookup:
        1. scope='patient:<patient_id>' (si patient_id no es None y no vacío)
        2. scope='global'
        3. default hardcoded

    Cualquier error (DB inaccesible, JSON inválido, etc.) devuelve `default`.

    Args:
        key: la clave de configuración (ej. "home.greeting", "timer.presets").
        default: valor a devolver si no hay override en cache.
        patient_id: id del paciente para override individual. None salta al global.

    Returns:
        El valor deserializado (dict, list, str, int, etc.) o `default`.
    """
    if not key:
        return default

    try:
        conn = obtener_conexion()
    except Exception:
        return default

    try:
        if patient_id:
            row = conn.execute(
                "SELECT value FROM remote_config_cache WHERE scope=? AND key=?",
                (f"patient:{patient_id}", key),
            ).fetchone()
            if row is not None:
                parsed = _safe_loads(row["value"])
                if parsed is not _SENTINEL:
                    return parsed

        row = conn.execute(
            "SELECT value FROM remote_config_cache WHERE scope=? AND key=?",
            ("global", key),
        ).fetchone()
        if row is not None:
            parsed = _safe_loads(row["value"])
            if parsed is not _SENTINEL:
                return parsed
    except Exception as exc:
        _log.debug("t(%r): error leyendo cache (%s); usando default", key, exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return default


# ── Escritura: helpers internos para llenar el cache ─────────────────────────


_SENTINEL = object()


def _safe_loads(raw: Any) -> Any:
    """json.loads tolerante. Devuelve _SENTINEL si no se puede deserializar."""
    if raw is None:
        return _SENTINEL
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return _SENTINEL


def cache_rows(rows: Iterable[dict]) -> int:
    """Persiste una lista de filas `hub_config` en el cache local.

    Helper público que también usa `shared.sync._importar_hub_config` (F2.0.C)
    para no duplicar lógica. Cada `row` debe tener `scope`, `key`, `value`.

    El `value` puede venir como objeto Python (lo que devuelve Supabase para
    columnas JSONB) o como string JSON (lo que devuelve un select crudo).
    En ambos casos se serializa a JSON string antes de guardar.

    Returns:
        Cantidad de filas escritas con éxito (puede ser menor que `len(rows)`
        si alguna fue inválida).
    """
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = obtener_conexion()
    except Exception as exc:
        _log.warning("cache_rows: no se pudo abrir DB: %s", exc)
        return 0

    written = 0
    try:
        for row in rows:
            if not isinstance(row, dict):
                continue
            scope = row.get("scope")
            key = row.get("key")
            value = row.get("value")
            if not scope or not key or value is None:
                continue

            if isinstance(value, (dict, list, tuple, bool, int, float)):
                try:
                    value_str = json.dumps(value, ensure_ascii=False)
                except (TypeError, ValueError):
                    continue
            elif isinstance(value, str):
                # Puede ser ya un JSON string o un texto plano. Probamos
                # parsearlo: si es JSON válido, lo dejamos tal cual (porque
                # eso es lo que t() va a deserializar). Si no, lo envolvemos
                # como string JSON.
                try:
                    json.loads(value)
                    value_str = value
                except (TypeError, ValueError):
                    value_str = json.dumps(value, ensure_ascii=False)
            else:
                continue

            try:
                conn.execute(
                    "INSERT OR REPLACE INTO remote_config_cache "
                    "(scope, key, value, fetched_at) VALUES (?, ?, ?, ?)",
                    (str(scope), str(key), value_str, fetched_at),
                )
                written += 1
            except Exception as exc:
                _log.debug("cache_rows: skip %s/%s (%s)", scope, key, exc)
        conn.commit()
    except Exception as exc:
        _log.warning("cache_rows: error guardando filas: %s", exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return written


# ── refresh standalone (sin sync) ────────────────────────────────────────────


def refresh_from_supabase(patient_id: Optional[str] = None) -> bool:
    """Descarga `hub_config` desde Supabase y refresca el cache local.

    Standalone: arma su propio cliente Supabase. No depende de `shared.sync`,
    útil para invocar manualmente desde el Hub o un script de QA.

    Args:
        patient_id: si se pasa, también descarga scope='patient:<id>'.

    Returns:
        True si el refresh terminó OK (incluso si trajo 0 filas).
        False si Supabase no está disponible o la query falló.
    """
    try:
        from shared.config import supabase_url, supabase_key
    except Exception as exc:
        _log.warning("refresh_from_supabase: shared.config no disponible (%s)", exc)
        return False

    url = supabase_url()
    key = supabase_key()
    if not url or not key:
        _log.info("refresh_from_supabase: credenciales Supabase ausentes")
        return False

    try:
        from supabase import create_client
    except ImportError:
        _log.warning("refresh_from_supabase: paquete 'supabase' no instalado")
        return False

    try:
        sb = create_client(url, key)
    except Exception as exc:
        _log.warning("refresh_from_supabase: create_client falló (%s)", exc)
        return False

    scopes = ["global"]
    if patient_id:
        scopes.append(f"patient:{patient_id}")

    try:
        res = (sb.table("hub_config")
                 .select("scope, key, value")
                 .in_("scope", scopes)
                 .execute())
    except Exception as exc:
        _log.warning("refresh_from_supabase: SELECT hub_config falló (%s)", exc)
        return False

    rows = res.data or []
    cache_rows(rows)
    return True
