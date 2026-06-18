"""sync.py — Sincronización con Supabase (exportación paciente + importación asignaciones)."""

import threading
import base64
import json
import logging
from datetime import datetime, timedelta

_log = logging.getLogger("NeuroMood.Sync")

try:
    from supabase import create_client as _sb_create

    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False

from shared.db import obtener_conexion, conexion, guardar_config, leer_config
from shared.identidad import obtener_patient_id, obtener_nombre_paciente, obtener_password_hash
from shared.config import supabase_url, supabase_key

_DAYS_BETWEEN_SYNC = 7


def _jwt_expired(token: str, leeway_seconds: int = 60) -> bool:
    """True si el JWT local ya venció; no valida firma ni imprime contenido."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return False
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
        exp = data.get("exp")
        if not isinstance(exp, (int, float)):
            return False
        return exp <= datetime.now().timestamp() + leeway_seconds
    except Exception:
        return False


def _has_expired_local_session() -> bool:
    token = leer_config("auth_access_token", "").strip()
    return bool(token and token.lower() != "offline" and _jwt_expired(token))


def _get_client(*, allow_expired_anon: bool = True):
    if not _SUPABASE_OK:
        return None
    url = supabase_url()
    key = supabase_key()
    if not url or not key:
        return None
    try:
        client = _sb_create(url, key)
        access_token = leer_config("auth_access_token", "")
        refresh_token = leer_config("auth_refresh_token", "")
        token = access_token.strip()
        if not token or token.lower() == "offline":
            return client  # sin sesión: cliente anon (solo lecturas globales)

        # Intentar establecer la sesión autenticada del PACIENTE. ``set_session``
        # REFRESCA automáticamente cuando el access token venció pero el refresh
        # token sigue vivo → mantiene la sesión del paciente (su id de usuario =
        # patient_id) para que el RLS deje leer las asignaciones del profesional
        # (assigned_tasks, support_messages, patient_activities, etc.). BUG
        # ANTERIOR: con el access token vencido se caía DIRECTO a cliente anon
        # (sesión nula) y el sync del Plan terapéutico quedaba en blanco en los 4
        # módulos; como los JWT duran ~1h, el sync se rompía al poco de abrir la
        # app. Persistimos los tokens refrescados para no re-pedir contraseña.
        if refresh_token:
            try:
                res = client.auth.set_session(token, refresh_token)
                sess = getattr(res, "session", None)
                if sess is not None:
                    new_at = getattr(sess, "access_token", None)
                    new_rt = getattr(sess, "refresh_token", None)
                    if new_at and new_at != token:
                        guardar_config("auth_access_token", new_at)
                    if new_rt and new_rt != refresh_token:
                        guardar_config("auth_refresh_token", new_rt)
                return client
            except Exception as e:
                _log.debug("set_session/refresh de sesión Supabase falló: %s", e)

        # Sin refresh token (o refresh falló): usar el access token directo si
        # sigue vigente; si venció, caer a anon solo cuando se permita.
        if not _jwt_expired(token):
            try:
                client.postgrest.auth(token)
                return client
            except Exception as e_pg:
                _log.warning("Fallo fallback postgrest auth: %s", e_pg)
        if allow_expired_anon:
            _log.info(
                "Sesión Supabase no autenticada; cliente anon solo para importaciones globales."
            )
            return client
        _log.warning("Sesión Supabase no autenticada; no se exporta/escribe con cliente anon.")
        return None
    except Exception as e:
        _log.error("Fallo al crear cliente Supabase o configurar sesion: %s", e)
        return None


# ── Desvinculación por el profesional ─────────────────────────────────────────


def _paciente_desvinculado(sb, patient_id: str) -> bool:
    """True si el profesional quitó a este paciente del Hub (patients.unlinked).

    Decisión owner v1.0: el paciente desvinculado sigue usando la Suite
    OFFLINE (sin sync, sin Supabase); si quiere retomar el tratamiento crea
    una cuenta nueva (identidad nueva => fila nueva, no se re-vincula).

    El resultado se cachea en config local ("sync_unlinked"): los próximos
    sync ni siquiera tocan la red. Fail-safe: si la columna no existe aún en
    el schema remoto o hay error de red, NO se bloquea el sync.
    """
    try:
        if leer_config("sync_unlinked", "") == "1":
            return True
    except Exception:
        pass
    if sb is None or not patient_id:
        return False
    try:
        res = (
            sb.table("patients")
            .select("unlinked")
            .eq("patient_id", patient_id)
            .maybe_single()
            .execute()
        )
        data = getattr(res, "data", None) or {}
        if data.get("unlinked"):
            guardar_config("sync_unlinked", "1")
            _log.info("Paciente desvinculado por el profesional: sync deshabilitado (offline).")
            return True
    except Exception:
        # Columna ausente (schema viejo) o red caída: comportamiento normal.
        pass
    return False


# ── Registro de paciente ──────────────────────────────────────────────────────


def registrar_paciente_en_nube(patient_id: str, nombre: str, pwd: str = "") -> bool:
    sb = _get_client(allow_expired_anon=False)
    if not sb:
        _log.warning("No se pudo obtener cliente Supabase para registrar paciente")
        return False
    try:
        sb.table("patients").upsert(
            {
                "patient_id": patient_id,
                "patient_name": nombre,
                "pwd": pwd,
                "perm_checklist_activacion": True,
                "perm_checklist_manual": True,
                "perm_temporizador_manual": True,
                "perm_recordatorios_manual": True,
            }
        ).execute()
        return True
    except Exception as e:
        _log.warning("Fallo registro completo de paciente, intentando insercion minima: %s", e)
        try:
            sb.table("patients").upsert(
                {
                    "patient_id": patient_id,
                    "patient_name": nombre,
                    "pwd": pwd,
                }
            ).execute()
            return True
        except Exception as e_min:
            _log.error("Fallo registro minimo de paciente en nube: %s", e_min)
            return False


# ── Exportación (paciente → nube) ─────────────────────────────────────────────


def _exportar_animo(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, puntaje, nota "
        "FROM termometro WHERE fecha >= ? ORDER BY fecha, hora",
        (desde,),
    ).fetchall()
    conn.close()
    if not rows:
        return
    # Exportar únicamente los campos que el módulo Ánimo captura.
    payload = [
        {
            "patient_id": patient_id,
            "fecha": r["fecha"],
            "hora": r["hora"],
            "puntaje": r["puntaje"],
            "nota": r["nota"] or "",
        }
        for r in rows
    ]
    sb.table("mood_records").upsert(payload, on_conflict="patient_id,fecha,hora").execute()


def _exportar_respiracion(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, tecnica, duracion_minutos, ciclos FROM respiracion WHERE fecha >= ?",
        (desde,),
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {
            "patient_id": patient_id,
            "fecha": r["fecha"],
            "hora": r["hora"],
            "tecnica": r["tecnica"],
            "duracion_minutos": r["duracion_minutos"],
            "ciclos": r["ciclos"],
        }
        for r in rows
    ]
    sb.table("breathing_sessions").upsert(payload, on_conflict="patient_id,fecha,hora").execute()


def _exportar_pensamientos(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, situacion, emocion, intensidad, pensamiento, "
        "respuesta_alternativa, distorsiones, reflexion_ia "
        "FROM pensamientos WHERE fecha >= ?",
        (desde,),
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {
            "patient_id": patient_id,
            "fecha": r["fecha"],
            "hora": r["hora"],
            "situacion": r["situacion"],
            "emocion": r["emocion"],
            "intensidad": r["intensidad"],
            "pensamiento": r["pensamiento"],
            "respuesta_alternativa": r["respuesta_alternativa"] or "",
            "distorsiones": r["distorsiones"] or "",
            "reflexion_ia": r["reflexion_ia"] or "",
        }
        for r in rows
    ]
    sb.table("thought_records").upsert(payload, on_conflict="patient_id,fecha,hora").execute()


def _exportar_checklist(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT cc.fecha, ct.descripcion, "
        "COALESCE(ct.categoria, 'Logro') as categoria, "
        "COALESCE(ct.origen, '') as origen "
        "FROM checklist_completadas cc "
        "JOIN checklist_tareas ct ON cc.tarea_id = ct.id "
        "WHERE cc.fecha >= ?",
        (desde,),
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {
            "patient_id": patient_id,
            "fecha": r["fecha"],
            "descripcion": r["descripcion"],
            "categoria": r["categoria"],
            "origen": r["origen"],
        }
        for r in rows
    ]
    sb.table("checklist_completions").upsert(
        payload, on_conflict="patient_id,fecha,descripcion"
    ).execute()


def _exportar_temporizador(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, nombre, categoria, duracion_config, duracion_real, notas "
        "FROM actividades_temporizador WHERE fecha >= ? ORDER BY fecha, hora",
        (desde,),
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {
            "patient_id": patient_id,
            "fecha": r["fecha"],
            "hora": r["hora"],
            "nombre": r["nombre"] or "",
            "categoria": r["categoria"] or "",
            "duracion_config": r["duracion_config"],
            "duracion_real": r["duracion_real"],
            "notas": r["notas"] or "",
        }
        for r in rows
    ]
    sb.table("timer_sessions").upsert(payload, on_conflict="patient_id,fecha,hora,nombre").execute()


def _exportar_recordatorios_log(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, mensaje, cerrado "
        "FROM recordatorios_log WHERE fecha >= ? ORDER BY fecha, hora",
        (desde,),
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {
            "patient_id": patient_id,
            "fecha": r["fecha"],
            "hora": r["hora"],
            "mensaje": r["mensaje"] or "",
            "cerrado": r["cerrado"],
        }
        for r in rows
    ]
    sb.table("reminder_logs").upsert(payload, on_conflict="patient_id,fecha,hora,mensaje").execute()


def _exportar_activacion(sb, patient_id: str, desde: str):
    """[M1 Fase 0.3] Exporta resultados de Activación Conductual para que el
    profesional los monitoree en el Hub (detalle del paciente · Registros).

    Fail-safe: si la tabla remota `activation_results` aún no existe (el owner
    debe crearla en Supabase), captura el error y NO rompe el resto del sync.

    RA-1 (reauditoría UI-first): NO se envía `energia` al Hub. El módulo
    Actividades actual no la captura; antes, _register_result copiaba `animo`
    como `energia` y ese valor llegaba al Hub como autoinforme real. La
    columna física se conserva en SQLite y Supabase por compatibilidad con
    datos históricos; los registros nuevos llegan sin el campo (Supabase
    aplica el default del schema: energia=NULL).
    """
    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT fecha, hora, animo, actividad, resultado "
            "FROM activacion WHERE fecha >= ? ORDER BY fecha, hora",
            (desde,),
        ).fetchall()
        conn.close()
        if not rows:
            return
        payload = [
            {
                "patient_id": patient_id,
                "fecha": r["fecha"],
                "hora": r["hora"],
                "animo": r["animo"],
                "actividad": r["actividad"] or "",
                "resultado": r["resultado"] or "",
            }
            for r in rows
        ]
        sb.table("activation_results").upsert(
            payload, on_conflict="patient_id,fecha,hora,actividad"
        ).execute()
    except Exception:
        _log.debug("_exportar_activacion: tabla remota ausente o error (pendiente de crear)")


def _exportar_dbt_practicas(sb, patient_id: str, desde: str):
    """Exporta los registros locales de dbt_practicas a la tabla remota dbt_practice_records.
    No bloquea todo el sync si la tabla remota todavía no fue desplegada, pero registra
    el error de forma visible en los logs.
    """
    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT record_id, fecha, hora, skill_id, skill_version, familia, necesidad, "
            "malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at "
            "FROM dbt_practicas WHERE created_at >= ? ORDER BY created_at",
            (desde,),
        ).fetchall()
        conn.close()
        if not rows:
            return
        payload = [
            {
                "record_id": r["record_id"],
                "patient_id": patient_id,
                "fecha": r["fecha"],
                "hora": r["hora"],
                "skill_id": r["skill_id"],
                "skill_version": r["skill_version"],
                "familia": r["familia"],
                "necesidad": r["necesidad"] or "",
                "malestar_antes": r["malestar_antes"],
                "malestar_despues": r["malestar_despues"],
                "resultado": r["resultado"],
                "duracion_seg": r["duracion_seg"],
                "nota": r["nota"] or "",
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        sb.table("dbt_practice_records").upsert(payload, on_conflict="record_id").execute()
    except Exception as e:
        _log.error("Fallo la exportacion de dbt_practicas a la tabla remota dbt_practice_records: %s", e)


# ── Importación (nube → paciente) ─────────────────────────────────────────────


def _importar_tareas_asignadas(sb, patient_id: str):
    """Descarga tareas asignadas por el profesional y reconcilia el checklist local."""
    try:
        res = (
            sb.table("assigned_tasks")
            .select("*")
            .eq("patient_id", patient_id)
            .eq("activa", True)
            .execute()
        )
    except Exception:
        return
    tareas = res.data or []
    with conexion() as conn:
        remote_descs = {
            str(t.get("descripcion") or "").strip()
            for t in tareas
            if str(t.get("descripcion") or "").strip()
        }
        managed_origins = ("profesional", "profesional_asignacion")
        if remote_descs:
            placeholders = ",".join("?" for _ in remote_descs)
            conn.execute(
                "DELETE FROM checklist_tareas "
                "WHERE origen IN (?, ?) "
                f"AND descripcion NOT IN ({placeholders})",
                (*managed_origins, *remote_descs),
            )
        else:
            conn.execute(
                "DELETE FROM checklist_tareas WHERE origen IN (?, ?)",
                managed_origins,
            )
            return

        existentes = {
            r[0] for r in conn.execute("SELECT descripcion FROM checklist_tareas").fetchall()
        }
        for t in tareas:
            desc = t.get("descripcion", "")
            if desc in existentes:
                conn.execute(
                    "UPDATE checklist_tareas SET origen = 'profesional_asignacion' "
                    "WHERE descripcion = ? AND origen IN (?, ?)",
                    (desc, *managed_origins),
                )
                continue
            seccion = t.get("seccion", "tarde")
            if seccion not in ("manana", "tarde", "noche"):
                seccion = "tarde"
            max_orden = conn.execute(
                "SELECT COALESCE(MAX(orden), 0) as m FROM checklist_tareas WHERE seccion = ?",
                (seccion,),
            ).fetchone()[0]
            try:
                conn.execute(
                    "INSERT INTO checklist_tareas "
                    "(seccion, descripcion, orden, categoria, dificultad, animo_rango, origen) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'profesional_asignacion')",
                    (
                        seccion,
                        desc,
                        max_orden + 1,
                        t.get("categoria", "Logro"),
                        t.get("dificultad", 1),
                        t.get("animo_rango"),
                    ),
                )
            except Exception:
                pass


def _importar_rutina_modo(sb, patient_id: str):
    """Descarga patients.rutina_modo y lo guarda en config local."""
    try:
        res = (
            sb.table("patients")
            .select("rutina_modo")
            .eq("patient_id", patient_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        return
    data = res.data or {}
    modo = data.get("rutina_modo") or "mixto"
    if modo not in ("solo_profesional", "mixto", "solo_paciente"):
        modo = "mixto"
    try:
        guardar_config("rutina_modo", modo)
    except Exception:
        pass


def _template_tasks_from_sections(sections):
    if sections is None:
        return []
    if isinstance(sections, str):
        try:
            sections = json.loads(sections)
        except Exception:
            return []
    if isinstance(sections, list):
        tasks = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_key = section.get("key") or section.get("seccion") or "tarde"
            for item in section.get("items") or []:
                if isinstance(item, dict):
                    tasks.append({**item, "seccion": item.get("seccion") or section_key})
                elif isinstance(item, str):
                    tasks.append({"descripcion": item, "seccion": section_key})
        return tasks
    if isinstance(sections, dict):
        items = []
        for seccion in ("manana", "tarde", "noche"):
            section_items = sections.get(seccion) or []
            for item in section_items:
                if isinstance(item, dict):
                    item = {**item, "seccion": item.get("seccion") or seccion}
                items.append(item)
        return items
    return []


def _template_tasks_from_legacy_payload(payload):
    if payload is None:
        return []
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            return []
    if isinstance(payload, dict):
        if isinstance(payload.get("tasks"), list):
            return payload["tasks"]
        if isinstance(payload.get("tareas"), list):
            return payload["tareas"]
    if isinstance(payload, list):
        return payload
    return []


def _normalizar_tarea_template(item, fallback_section="tarde"):
    if isinstance(item, str):
        return {
            "descripcion": item,
            "seccion": fallback_section,
            "categoria": "Logro",
            "dificultad": 1,
        }
    if not isinstance(item, dict):
        return None
    desc = (
        item.get("descripcion")
        or item.get("description")
        or item.get("text")
        or item.get("nombre")
        or ""
    ).strip()
    if not desc:
        return None
    seccion = item.get("seccion") or item.get("section") or fallback_section
    if seccion not in ("manana", "tarde", "noche"):
        seccion = fallback_section
    return {
        "descripcion": desc,
        "seccion": seccion,
        "categoria": item.get("categoria") or item.get("category") or "Logro",
        "dificultad": item.get("dificultad") or item.get("difficulty") or 1,
    }


def _importar_routine_template(sb, patient_id: str):
    """Importa la plantilla de rutina asignada como tareas profesionales."""
    try:
        res = (
            sb.table("patient_routine_template")
            .select("template_id,routine_templates(*)")
            .eq("patient_id", patient_id)
            .execute()
        )
        assignments = res.data or []
    except Exception:
        try:
            res = (
                sb.table("patient_routine_template")
                .select("template_id")
                .eq("patient_id", patient_id)
                .execute()
            )
            assignments = res.data or []
        except Exception:
            return
    if not assignments:
        return

    templates = []
    for row in assignments:
        tmpl = row.get("routine_templates") or row.get("routine_template")
        if isinstance(tmpl, list):
            templates.extend(tmpl)
        elif isinstance(tmpl, dict):
            templates.append(tmpl)
        else:
            template_id = row.get("template_id")
            if not template_id:
                continue
            try:
                t_res = (
                    sb.table("routine_templates")
                    .select("*")
                    .eq("id", template_id)
                    .maybe_single()
                    .execute()
                )
                if t_res.data:
                    templates.append(t_res.data)
            except Exception:
                pass
    if not templates:
        return

    conn = obtener_conexion()
    try:
        existentes = {
            r[0]
            for r in conn.execute(
                "SELECT descripcion FROM checklist_tareas WHERE origen = 'profesional'"
            ).fetchall()
        }
        for tmpl in templates:
            tasks = _template_tasks_from_sections(tmpl.get("sections"))
            if not tasks:
                tasks = _template_tasks_from_legacy_payload(tmpl.get("payload"))
            for index, raw in enumerate(tasks):
                task = _normalizar_tarea_template(raw)
                if not task or task["descripcion"] in existentes:
                    continue
                max_orden = conn.execute(
                    "SELECT COALESCE(MAX(orden), 0) FROM checklist_tareas WHERE seccion = ?",
                    (task["seccion"],),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO checklist_tareas "
                    "(seccion, descripcion, orden, categoria, dificultad, origen) "
                    "VALUES (?, ?, ?, ?, ?, 'profesional_template')",
                    (
                        task["seccion"],
                        task["descripcion"],
                        max_orden + 1 + index,
                        task["categoria"],
                        task["dificultad"],
                    ),
                )
                existentes.add(task["descripcion"])
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _importar_tcc_templates(sb, patient_id: str):
    """Cachea plantillas TCC remotas para uso offline en la Suite."""
    if not patient_id:
        return
    scopes = ("global", f"patient:{patient_id}")
    try:
        res = (
            sb.table("tcc_templates")
            .select("id,scope,name,steps,emotions,distortions,tip_text,version")
            .in_("scope", scopes)
            .execute()
        )
    except Exception:
        return
    rows = res.data or []
    if not rows:
        return
    conn = obtener_conexion()
    fetched_at = datetime.now().isoformat()
    try:
        for row in rows:
            conn.execute(
                "INSERT OR REPLACE INTO tcc_templates_cache "
                "(id, scope, name, steps, emotions, distortions, tip_text, version, fetched_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row.get("id"),
                    row.get("scope") or "global",
                    row.get("name") or "TCC base",
                    json.dumps(row.get("steps") or [], ensure_ascii=False),
                    json.dumps(row.get("emotions") or [], ensure_ascii=False),
                    json.dumps(row.get("distortions") or [], ensure_ascii=False),
                    row.get("tip_text") or "",
                    row.get("version") or 1,
                    fetched_at,
                ),
            )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _sync_scopes(patient_id: str) -> tuple[str, ...]:
    return ("global", f"patient:{patient_id}") if patient_id else ("global",)


def _importar_timer_presets(sb, patient_id: str):
    """Cachea presets remotos de Timer con scope global y patient."""
    scopes = _sync_scopes(patient_id)
    try:
        res = (
            sb.table("timer_presets_remote")
            .select("id,scope,name,duracion_seg,categoria,activo,orden")
            .in_("scope", scopes)
            .order("orden")
            .execute()
        )
    except Exception:
        return
    rows = res.data or []
    conn = obtener_conexion()
    try:
        for scope in scopes:
            conn.execute("DELETE FROM timer_presets_cache WHERE scope = ?", (scope,))
        for row in rows:
            if row.get("activo") is False:
                continue
            payload = {
                "name": row.get("name") or "",
                "duracion_seg": row.get("duracion_seg") or 0,
                "categoria": row.get("categoria") or "",
                "activo": True,
                "orden": row.get("orden") or 0,
            }
            conn.execute(
                "INSERT OR REPLACE INTO timer_presets_cache "
                "(id, scope, name, payload) VALUES (?, ?, ?, ?)",
                (
                    row.get("id"),
                    row.get("scope") or "global",
                    row.get("name") or "",
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _importar_breathing_presets(sb, patient_id: str):
    """[DORMANTE — M1 Fase 2.3] Cachea presets remotos de respiración.

    El módulo #5 (Guía de Respiración Animada) es SOLO SEGUIMIENTO: el patrón
    4-7-8 es fijo y no hay editor de breathing presets en el Hub que popule
    `breathing_presets_remote`. Por lo tanto este import no trae datos hoy
    (la query devuelve 0 filas) y es un no-op efectivo. Se conserva el path
    —fail-safe, sin romper sync— para una eventual reactivación con editor.
    """
    scopes = _sync_scopes(patient_id)
    try:
        res = (
            sb.table("breathing_presets_remote")
            .select(
                "id,scope,name,fase_in,fase_hold,fase_out,fase_hold_after,duracion_min_default,activa,orden"
            )
            .in_("scope", scopes)
            .order("orden")
            .execute()
        )
    except Exception:
        return
    rows = res.data or []
    conn = obtener_conexion()
    try:
        for scope in scopes:
            conn.execute("DELETE FROM breathing_presets_cache WHERE scope = ?", (scope,))
        for row in rows:
            if row.get("activa") is False:
                continue
            payload = {
                "name": row.get("name") or "",
                "fases": {
                    "in": row.get("fase_in") or 0,
                    "hold": row.get("fase_hold") or 0,
                    "out": row.get("fase_out") or 0,
                    "hold_after": row.get("fase_hold_after") or 0,
                },
                "duracion_min_default": row.get("duracion_min_default") or 5,
                "activa": True,
                "orden": row.get("orden") or 0,
            }
            conn.execute(
                "INSERT OR REPLACE INTO breathing_presets_cache "
                "(id, scope, name, payload) VALUES (?, ?, ?, ?)",
                (
                    row.get("id"),
                    row.get("scope") or "global",
                    row.get("name") or "",
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _importar_support_messages(sb, patient_id: str):
    """Cachea biblioteca remota de mensajes de apoyo para Avisos."""
    scopes = _sync_scopes(patient_id)
    try:
        res = (
            sb.table("support_messages")
            .select("id,scope,categoria,mensaje,activa")
            .in_("scope", scopes)
            .execute()
        )
    except Exception:
        return
    rows = res.data or []
    conn = obtener_conexion()
    try:
        for scope in scopes:
            conn.execute("DELETE FROM support_messages_cache WHERE scope = ?", (scope,))
        for row in rows:
            if row.get("activa") is False:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO support_messages_cache "
                "(id, scope, categoria, mensaje) VALUES (?, ?, ?, ?)",
                (
                    row.get("id"),
                    row.get("scope") or "global",
                    row.get("categoria") or "Recordatorio",
                    row.get("mensaje") or "",
                ),
            )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _importar_recordatorios_asignados(sb, patient_id: str):
    """Descarga recordatorios asignados por el profesional y reconcilia el cache local."""
    try:
        res = (
            sb.table("assigned_reminders")
            .select("*")
            .eq("patient_id", patient_id)
            .eq("activa", True)
            .execute()
        )
    except Exception:
        return
    recs = res.data or []
    with conexion() as conn:
        remote_pairs = {
            (str(r.get("hora") or "").strip(), str(r.get("mensaje") or "").strip())
            for r in recs
            if str(r.get("hora") or "").strip() and str(r.get("mensaje") or "").strip()
        }
        if remote_pairs:
            keep = " OR ".join("(hora = ? AND mensaje = ?)" for _ in remote_pairs)
            params = [value for pair in remote_pairs for value in pair]
            conn.execute(f"DELETE FROM recordatorios WHERE NOT ({keep})", params)
        else:
            conn.execute("DELETE FROM recordatorios")
            return

        existentes = {
            (r[0], r[1])
            for r in conn.execute("SELECT hora, mensaje FROM recordatorios").fetchall()
        }
        for r in recs:
            hora = r.get("hora", "")
            msg = r.get("mensaje", "")
            if not hora or not msg:
                continue
            if (hora, msg) in existentes:
                continue
            dias = r.get("dias", "1,2,3,4,5,6,7")
            try:
                conn.execute(
                    "INSERT INTO recordatorios (hora, mensaje, dias, activo) VALUES (?, ?, ?, 1)",
                    (hora, msg, dias),
                )
            except Exception:
                pass


# ── Helpers ──────────────────────────────────────────────────────────────────


def _upsert_paciente(sb, pid: str, nombre: str, pwd: str, install_code: str):
    """Registra/actualiza al paciente en Supabase.

    Intenta primero con todos los campos opcionales.
    Si Supabase rechaza columnas que aun no existen (schema viejo),
    reintenta con solo los campos basicos garantizados.
    """
    payload_full = {
        "patient_id": pid,
        "patient_name": nombre,
        "pwd": pwd,
        "install_code": install_code,
        "perm_checklist_activacion": True,
        "perm_checklist_manual": True,
        "perm_temporizador_manual": True,
        "perm_recordatorios_manual": True,
    }
    # Email declarado en el alta: el Hub lo muestra para distinguir pacientes
    # homónimos (decisión owner v1.0). Solo en payload_full — si la columna no
    # existe aún en el schema remoto, el fallback mínimo sigue funcionando.
    _email = leer_config("patient_email", "")
    if _email:
        payload_full["email"] = _email
    payload_min = {
        "patient_id": pid,
        "patient_name": nombre,
        "pwd": pwd,
    }
    try:
        sb.table("patients").upsert(payload_full).execute()
        return
    except Exception as e:
        err = str(e)
        # Column not found — schema incompleto, reintentar sin columna
        if "install_code" in err or "email" in err or "PGRST204" in err:
            try:
                sb.table("patients").upsert(payload_min).execute()
                return
            except Exception:
                pass
        # RLS activo — el schema SQL no se ejecuto completo
        if "42501" in err or "row-level security" in err:
            raise RuntimeError(
                "RLS activo en tabla 'patients'. "
                "Ejecutar supabase_schema.sql en el dashboard de Supabase."
            )
        raise


# ── Sync completo ─────────────────────────────────────────────────────────────


def sync_completo(patient_id: str = None, nombre: str = None) -> bool:
    """Exporta datos locales a Supabase e importa asignaciones del profesional."""
    sb = _get_client(allow_expired_anon=False)
    if not sb:
        _log.warning("No se pudo iniciar cliente Supabase para sync completo")
        return False
    pid = patient_id or obtener_patient_id()
    nombre = nombre or obtener_nombre_paciente()
    if not pid:
        _log.warning("Paciente ID no configurado para sync completo")
        return False
    if _paciente_desvinculado(sb, pid):
        return False
    try:
        install_code = leer_config("install_code", "")
        pwd = obtener_password_hash(install_code)
        _upsert_paciente(sb, pid, nombre, pwd, install_code)
        desde = "1900-01-01"
        _exportar_animo(sb, pid, desde)
        _exportar_respiracion(sb, pid, desde)
        _exportar_pensamientos(sb, pid, desde)
        _exportar_checklist(sb, pid, desde)
        _exportar_temporizador(sb, pid, desde)
        _exportar_recordatorios_log(sb, pid, desde)
        _exportar_activacion(sb, pid, desde)
        _exportar_dbt_practicas(sb, pid, desde)
        _importar_rutina_modo(sb, pid)
        _importar_routine_template(sb, pid)
        _importar_tcc_templates(sb, pid)
        _importar_timer_presets(sb, pid)
        _importar_breathing_presets(sb, pid)
        _importar_support_messages(sb, pid)
        _importar_tareas_asignadas(sb, pid)
        _importar_recordatorios_asignados(sb, pid)
        _importar_permisos(sb, pid)
        _importar_actividades(sb, pid)
        _importar_hub_config(sb, pid)
        try:
            sb.table("patients").update({"last_sync_date": datetime.now().isoformat()}).eq(
                "patient_id", pid
            ).execute()
        except Exception as e_date:
            _log.warning("No se pudo actualizar last_sync_date en la nube: %s", e_date)
        guardar_config("last_sync_date", datetime.now().strftime("%Y-%m-%d"))
        return True
    except Exception as e:
        _log.exception("Error critico durante la sincronizacion completa: %s", e)
        return False


def _importar_permisos(sb, patient_id: str):
    """Descarga permisos del profesional y los guarda en config local."""
    try:
        res = (
            sb.table("patients")
            .select(
                "perm_checklist_activacion,perm_checklist_manual,perm_temporizador_manual,perm_recordatorios_manual"
            )
            .eq("patient_id", patient_id)
            .maybe_single()
            .execute()
        )
        if not res.data:
            return
        d = res.data
        guardar_config(
            "perm_checklist_activacion", "1" if d.get("perm_checklist_activacion", True) else "0"
        )
        guardar_config(
            "perm_checklist_manual", "1" if d.get("perm_checklist_manual", True) else "0"
        )
        guardar_config(
            "perm_temporizador_manual", "1" if d.get("perm_temporizador_manual", True) else "0"
        )
        guardar_config(
            "perm_recordatorios_manual", "1" if d.get("perm_recordatorios_manual", True) else "0"
        )
    except Exception:
        pass


def _importar_actividades(sb, patient_id: str):
    """Descarga actividades del banco general/paciente y reconcilia el cache local."""
    globales, personales = [], []
    try:
        res = sb.table("activity_bank").select("*").eq("activa", True).execute()
        globales = res.data or []
    except Exception:
        pass
    try:
        res = (
            sb.table("patient_activities")
            .select("*")
            .eq("patient_id", patient_id)
            .eq("activa", True)
            .execute()
        )
        personales = res.data or []
    except Exception:
        pass
    todas = globales + personales
    with conexion() as conn:
        remote_names = {
            str(act.get("nombre") or "").strip()
            for act in todas
            if str(act.get("nombre") or "").strip()
        }
        if remote_names:
            placeholders = ",".join("?" for _ in remote_names)
            conn.execute(
                "DELETE FROM activacion_actividades "
                "WHERE es_custom = 1 AND nombre NOT IN "
                f"({placeholders})",
                tuple(remote_names),
            )
        else:
            conn.execute("DELETE FROM activacion_actividades WHERE es_custom = 1")
            return

        existentes = {
            r[0] for r in conn.execute("SELECT nombre FROM activacion_actividades").fetchall()
        }
        for act in todas:
            nombre = act.get("nombre", "")
            if not nombre or nombre in existentes:
                continue
            try:
                conn.execute(
                    "INSERT INTO activacion_actividades "
                    "(nombre, descripcion, categoria, dificultad, duracion_min, beneficio, "
                    "animo_min, animo_max, activa, es_custom) "
                    "VALUES (?,?,?,?,?,?,?,?,1,1)",
                    (
                        nombre,
                        act.get("descripcion", ""),
                        act.get("categoria", "Autocuidado"),
                        act.get("dificultad", 1),
                        act.get("duracion_min", 10),
                        act.get("beneficio", ""),
                        act.get("animo_min", 0),
                        act.get("animo_max", 10),
                    ),
                )
                existentes.add(nombre)
            except Exception:
                pass


def _importar_hub_config(sb, patient_id: str):
    """Descarga `hub_config` scope='global' + scope='patient:<id>' y cachea local.

    F2.0.C — alimenta la tabla local `remote_config_cache` que consume
    `shared.remote_config.t()` para resolver la jerarquía
    patient:<id> -> global -> default hardcoded.

    Sigue el patrón silencioso del resto de `_importar_*`: cualquier excepción
    de red, parse JSON o IO queda contenida. No propaga errores al pipeline
    de sync.
    """
    scopes = ("global", f"patient:{patient_id}") if patient_id else ("global",)
    try:
        res = sb.table("hub_config").select("scope, key, value").in_("scope", list(scopes)).execute()
    except Exception:
        return
    rows = res.data or []
    try:
        from shared.remote_config import replace_scopes

        # replace_scopes (no cache_rows): reconcilia el cache local con el
        # remoto borrando los overrides que el profesional eliminó. Antes, con
        # rows vacío se retornaba sin limpiar y los textos "restablecidos"
        # seguían cacheados → la Suite nunca volvía al valor por defecto.
        replace_scopes(scopes, rows)
    except Exception as e:
        _log.error("Fallo al cachear remote config: %s", e)


def verificar_asignaciones(patient_id: str = None):
    """Importa tareas, recordatorios y permisos asignados por el profesional.
    Llamar en cada apertura de app, sin restricción de intervalo."""
    expired_local_session = _has_expired_local_session()
    sb = _get_client(allow_expired_anon=True)
    if not sb:
        return
    pid = patient_id or obtener_patient_id()
    if not pid:
        return
    if _paciente_desvinculado(sb, pid):
        return
    try:
        _importar_rutina_modo(sb, pid)
        _importar_routine_template(sb, pid)
        _importar_tcc_templates(sb, pid)
        _importar_timer_presets(sb, pid)
        _importar_breathing_presets(sb, pid)
        _importar_support_messages(sb, pid)
        _importar_tareas_asignadas(sb, pid)
        _importar_recordatorios_asignados(sb, pid)
        _importar_permisos(sb, pid)
        _importar_actividades(sb, pid)
        _importar_hub_config(sb, pid)
        if not expired_local_session:
            _reenviar_consent_pendiente(sb)
        else:
            _log.info("Consentimiento pendiente no reenviado: sesion local expirada.")
    except Exception as e:
        _log.error("Fallo al ejecutar verificar_asignaciones: %s", e)


def verificar_asignaciones_background(patient_id: str = None):
    """Lanza verificar_asignaciones en hilo daemon."""
    t = threading.Thread(target=verificar_asignaciones, args=(patient_id,), daemon=True)
    t.start()


def sync_al_abrir():
    """Llamar al inicio de cada app paciente.
    Verifica asignaciones siempre; exporta datos si pasaron 7 días."""
    pid = obtener_patient_id()
    if not pid:
        return
    verificar_asignaciones_background(pid)
    if necesita_sync():
        sync_en_background()


def sync_inmediato():
    """Exporta registros de las últimas 48h a Supabase.
    Llamar tras cada guardado de datos en cualquier app paciente."""
    sb = _get_client(allow_expired_anon=False)
    if not sb:
        return
    pid = obtener_patient_id()
    nombre = obtener_nombre_paciente()
    if not pid:
        return
    if _paciente_desvinculado(sb, pid):
        return
    desde = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        install_code = leer_config("install_code", "")
        pwd = obtener_password_hash(install_code)
        _upsert_paciente(sb, pid, nombre, pwd, install_code)
        _exportar_animo(sb, pid, desde)
        _exportar_respiracion(sb, pid, desde)
        _exportar_pensamientos(sb, pid, desde)
        _exportar_checklist(sb, pid, desde)
        _exportar_temporizador(sb, pid, desde)
        _exportar_recordatorios_log(sb, pid, desde)
        _exportar_activacion(sb, pid, desde)
        _exportar_dbt_practicas(sb, pid, desde)
    except Exception as e:
        _log.error("Fallo al ejecutar sync_inmediato: %s", e)


_last_sync_time = 0
_SYNC_DEBOUNCE_SECS = 15


def sync_inmediato_background():
    """Lanza sync_inmediato en hilo daemon con debounce de 15s."""
    global _last_sync_time
    now = __import__("time").time()
    if now - _last_sync_time < _SYNC_DEBOUNCE_SECS:
        return
    _last_sync_time = now
    t = threading.Thread(target=sync_inmediato, daemon=True)
    t.start()


def sync_en_background(callback=None):
    """Lanza sync completo en hilo daemon. Llama callback(success: bool) al terminar."""

    def _run():
        ok = sync_completo()
        if callback:
            callback(ok)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def necesita_sync() -> bool:
    """True si han pasado más de _DAYS_BETWEEN_SYNC días desde el último sync."""
    ultima = leer_config("last_sync_date", "")
    if not ultima:
        return True
    try:
        diff = datetime.now() - datetime.strptime(ultima, "%Y-%m-%d")
        return diff.days >= _DAYS_BETWEEN_SYNC
    except Exception:
        return True


def _reenviar_consent_pendiente(sb):
    """F6.B: Intenta reenviar el consentimiento offline pendiente y lo borra si tiene éxito."""
    try:
        import os
        from pathlib import Path

        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        pending_path = Path(appdata) / "NeuroMood" / "pending_consent.json"
        if not pending_path.exists():
            return

        import json

        payload = json.loads(pending_path.read_text(encoding="utf-8"))
        user_id = (
            payload.get("user_id")
            or leer_config("auth_user_id", "")
            or leer_config("patient_id", "")
        )
        if not user_id:
            return
        payload["user_id"] = user_id
        payload["patient_id"] = payload.get("patient_id") or user_id
        existing = (
            sb.table("legal_consents")
            .select("id")
            .eq("user_id", user_id)
            .eq("disclaimer_version", payload.get("disclaimer_version", ""))
            .eq("privacy_version", payload.get("privacy_version", ""))
            .eq("disclaimer_text_hash", payload.get("disclaimer_text_hash", ""))
            .limit(1)
            .execute()
        )
        if getattr(existing, "data", None):
            pending_path.unlink()
            return
        sb.table("legal_consents").insert(payload).execute()

        pending_path.unlink()
    except Exception as e:
        _log.error("Error al reenviar consentimiento pendiente: %s", e)
