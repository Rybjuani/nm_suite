"""sync.py — Sincronización con Supabase (exportación paciente + importación asignaciones)."""
import threading
from datetime import datetime, timedelta

try:
    from supabase import create_client as _sb_create
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False

from shared.db import obtener_conexion, guardar_config, leer_config
from shared.identidad import obtener_patient_id, obtener_nombre_paciente, obtener_password_hash
from shared.config import supabase_url, supabase_key

_DAYS_BETWEEN_SYNC = 7


def _get_client():
    if not _SUPABASE_OK:
        return None
    url = supabase_url()
    key = supabase_key()
    if not url or not key:
        return None
    try:
        return _sb_create(url, key)
    except Exception:
        return None


# ── Registro de paciente ──────────────────────────────────────────────────────

def registrar_paciente_en_nube(patient_id: str, nombre: str, pwd: str = "") -> bool:
    sb = _get_client()
    if not sb:
        return False
    try:
        sb.table("patients").upsert({
            "patient_id": patient_id,
            "patient_name": nombre,
            "pwd": pwd,
        }).execute()
        return True
    except Exception:
        return False


# ── Exportación (paciente → nube) ─────────────────────────────────────────────

def _exportar_animo(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, puntaje, nota FROM termometro WHERE fecha >= ? ORDER BY fecha, hora",
        (desde,)
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {"patient_id": patient_id, "fecha": r["fecha"], "hora": r["hora"],
         "puntaje": r["puntaje"], "nota": r["nota"] or ""}
        for r in rows
    ]
    sb.table("mood_records").upsert(payload, on_conflict="patient_id,fecha,hora").execute()


def _exportar_respiracion(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, tecnica, duracion_minutos, ciclos FROM respiracion WHERE fecha >= ?",
        (desde,)
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {"patient_id": patient_id, "fecha": r["fecha"], "hora": r["hora"],
         "tecnica": r["tecnica"], "duracion_minutos": r["duracion_minutos"],
         "ciclos": r["ciclos"]}
        for r in rows
    ]
    sb.table("breathing_sessions").upsert(payload, on_conflict="patient_id,fecha,hora").execute()


def _exportar_pensamientos(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, situacion, emocion, intensidad, pensamiento, "
        "respuesta_alternativa, distorsiones, reflexion_ia "
        "FROM pensamientos WHERE fecha >= ?",
        (desde,)
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {"patient_id": patient_id, "fecha": r["fecha"], "hora": r["hora"],
         "situacion": r["situacion"], "emocion": r["emocion"],
         "intensidad": r["intensidad"], "pensamiento": r["pensamiento"],
         "respuesta_alternativa": r["respuesta_alternativa"] or "",
         "distorsiones": r["distorsiones"] or "",
         "reflexion_ia": r["reflexion_ia"] or ""}
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
        (desde,)
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {"patient_id": patient_id, "fecha": r["fecha"],
         "descripcion": r["descripcion"], "categoria": r["categoria"],
         "origen": r["origen"]}
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
        (desde,)
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {"patient_id": patient_id, "fecha": r["fecha"], "hora": r["hora"],
         "nombre": r["nombre"] or "", "categoria": r["categoria"] or "",
         "duracion_config": r["duracion_config"], "duracion_real": r["duracion_real"],
         "notas": r["notas"] or ""}
        for r in rows
    ]
    sb.table("timer_sessions").upsert(
        payload, on_conflict="patient_id,fecha,hora,nombre"
    ).execute()


def _exportar_recordatorios_log(sb, patient_id: str, desde: str):
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT fecha, hora, mensaje, cerrado "
        "FROM recordatorios_log WHERE fecha >= ? ORDER BY fecha, hora",
        (desde,)
    ).fetchall()
    conn.close()
    if not rows:
        return
    payload = [
        {"patient_id": patient_id, "fecha": r["fecha"], "hora": r["hora"],
         "mensaje": r["mensaje"] or "", "cerrado": r["cerrado"]}
        for r in rows
    ]
    sb.table("reminder_logs").upsert(
        payload, on_conflict="patient_id,fecha,hora,mensaje"
    ).execute()


# ── Importación (nube → paciente) ─────────────────────────────────────────────

def _importar_tareas_asignadas(sb, patient_id: str):
    """Descarga tareas asignadas por el profesional y las agrega al checklist local."""
    try:
        res = sb.table("assigned_tasks").select("*").eq("patient_id", patient_id).eq("activa", True).execute()
    except Exception:
        return
    tareas = res.data or []
    if not tareas:
        return
    conn = obtener_conexion()
    existentes = {r[0] for r in conn.execute("SELECT descripcion FROM checklist_tareas").fetchall()}
    for t in tareas:
        desc = t.get("descripcion", "")
        if desc in existentes:
            continue
        seccion = t.get("seccion", "tarde")
        if seccion not in ("manana", "tarde", "noche"):
            seccion = "tarde"
        max_orden = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) as m FROM checklist_tareas WHERE seccion = ?",
            (seccion,)
        ).fetchone()[0]
        try:
            conn.execute(
                "INSERT INTO checklist_tareas "
                "(seccion, descripcion, orden, categoria, dificultad, animo_rango, origen) "
                "VALUES (?, ?, ?, ?, ?, ?, 'profesional')",
                (seccion, desc, max_orden + 1,
                 t.get("categoria", "Logro"), t.get("dificultad", 1),
                 t.get("animo_rango"))
            )
        except Exception:
            pass
    conn.commit()
    conn.close()


def _importar_recordatorios_asignados(sb, patient_id: str):
    """Descarga recordatorios asignados por el profesional y los agrega localmente."""
    try:
        res = sb.table("assigned_reminders").select("*").eq("patient_id", patient_id).eq("activa", True).execute()
    except Exception:
        return
    recs = res.data or []
    if not recs:
        return
    conn = obtener_conexion()
    existentes = {(r[0], r[1]) for r in conn.execute(
        "SELECT hora, mensaje FROM recordatorios"
    ).fetchall()}
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
                (hora, msg, dias)
            )
        except Exception:
            pass
    conn.commit()
    conn.close()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _upsert_paciente(sb, pid: str, nombre: str, pwd: str, install_code: str):
    """Registra/actualiza al paciente en Supabase.

    Intenta primero con todos los campos opcionales.
    Si Supabase rechaza columnas que aun no existen (schema viejo),
    reintenta con solo los campos basicos garantizados.
    """
    payload_full = {
        "patient_id":   pid,
        "patient_name": nombre,
        "pwd":          pwd,
        "install_code": install_code,
    }
    payload_min = {
        "patient_id":   pid,
        "patient_name": nombre,
        "pwd":          pwd,
    }
    try:
        sb.table("patients").upsert(payload_full).execute()
        return
    except Exception as e:
        err = str(e)
        # Column not found — schema incompleto, reintentar sin columna
        if "install_code" in err or "PGRST204" in err:
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
    sb = _get_client()
    if not sb:
        return False
    pid = patient_id or obtener_patient_id()
    nombre = nombre or obtener_nombre_paciente()
    if not pid:
        return False
    try:
        install_code = leer_config("install_code", "")
        pwd = obtener_password_hash(install_code)
        _upsert_paciente(sb, pid, nombre, pwd, install_code)

    except Exception:
        return False


def _importar_permisos(sb, patient_id: str):
    """Descarga permisos del profesional y los guarda en config local."""
    try:
        res = (sb.table("patients")
               .select("perm_checklist_activacion,perm_checklist_manual,perm_temporizador_manual,perm_recordatorios_manual")
               .eq("patient_id", patient_id)
               .maybe_single()
               .execute())
        if not res.data:
            return
        d = res.data
        guardar_config("perm_checklist_activacion", "1" if d.get("perm_checklist_activacion", True) else "0")
        guardar_config("perm_checklist_manual",     "1" if d.get("perm_checklist_manual", False) else "0")
        guardar_config("perm_temporizador_manual",  "1" if d.get("perm_temporizador_manual", False) else "0")
        guardar_config("perm_recordatorios_manual", "1" if d.get("perm_recordatorios_manual", False) else "0")
    except Exception:
        pass


def _importar_actividades(sb, patient_id: str):
    """Descarga actividades del banco general y del banco del paciente e inserta en local."""
    globales, personales = [], []
    try:
        res = sb.table("activity_bank").select("*").eq("activa", True).execute()
        globales = res.data or []
    except Exception:
        pass
    try:
        res = (sb.table("patient_activities").select("*")
               .eq("patient_id", patient_id).eq("activa", True).execute())
        personales = res.data or []
    except Exception:
        pass
    todas = globales + personales
    if not todas:
        return
    conn = obtener_conexion()
    existentes = {r[0] for r in conn.execute("SELECT nombre FROM activacion_actividades").fetchall()}
    for act in todas:
        nombre = act.get("nombre", "")
        if not nombre or nombre in existentes:
            continue
        try:
            conn.execute(
                "INSERT INTO activacion_actividades "
                "(nombre, descripcion, categoria, dificultad, duracion_min, beneficio, "
                "animo_min, animo_max, activa, es_custom) "
                "VALUES (?,?,?,?,?,?,?,?,1,0)",
                (nombre, act.get("descripcion", ""), act.get("categoria", "Autocuidado"),
                 act.get("dificultad", 1), act.get("duracion_min", 10),
                 act.get("beneficio", ""), act.get("animo_min", 0), act.get("animo_max", 10))
            )
            existentes.add(nombre)
        except Exception:
            pass
    conn.commit()
    conn.close()


def verificar_asignaciones(patient_id: str = None):
    """Importa tareas, recordatorios y permisos asignados por el profesional.
    Llamar en cada apertura de app, sin restricción de intervalo."""
    sb = _get_client()
    if not sb:
        return
    pid = patient_id or obtener_patient_id()
    if not pid:
        return
    try:
        _importar_tareas_asignadas(sb, pid)
        _importar_recordatorios_asignados(sb, pid)
        _importar_permisos(sb, pid)
        _importar_actividades(sb, pid)
    except Exception:
        pass


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
    sb = _get_client()
    if not sb:
        return
    pid = obtener_patient_id()
    nombre = obtener_nombre_paciente()
    if not pid:
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
    except Exception:
        pass


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
