"""ia_asistente.py — Asistente IA multi-proveedor para el terapeuta.

Soporta: Groq, Gemini, OpenAI, Ollama Cloud.
Selecciona automaticamente el mejor modelo disponible para tareas profesionales.
Si un modelo falla o se depreca, pasa al siguiente automaticamente.
Si ningun proveedor funciona, deshabilita IA con mensaje amigable.
"""

import threading
import time
import logging
import os
import queue
from shared.crash_log import redact
from datetime import date

# Configurar logger para que salga en hub.log via shared.crash_log
logger = logging.getLogger(__name__)

try:
    from shared.config import get as _config_get, supabase_hub_key as _supabase_hub_key
except ImportError:
    def _config_get(k, d=""):
        return os.environ.get(k, d)

    def _supabase_hub_key():
        return (
            os.environ.get("SUPABASE_HUB_KEY")
            or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_KEY", "")
        )

try:
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    def visual_qa_enabled():
        return False

try:
    from supabase import create_client
except ImportError:
    create_client = None

# ── Registro de proveedores ─────────────────────────────────────────────────────
# ... (rest of _PROVIDERS unchanged)
_PROVIDERS = [
    {
        "name": "Groq",
        "env_key": "GROQ_API_KEY",
        "client_type": "groq",
        "models": [
            ("llama-3.3-70b-versatile", 95),
            ("deepseek-r1-distill-llama-70b", 90),
            ("llama-3.1-70b-versatile", 85),
            ("llama3-70b-8192", 75),
            ("mixtral-8x7b-32768", 70),
        ],
    },
    {
        "name": "Gemini",
        "env_key": "GEMINI_API_KEY",
        "client_type": "gemini",
        "models": [
            ("gemini-2.0-flash", 85),
            ("gemini-1.5-pro", 80),
            ("gemini-1.5-flash", 75),
        ],
    },
    {
        "name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "client_type": "openai",
        "base_url_env": "",
        "base_url_default": None,
        "models": [
            ("gpt-4o", 90),
            ("gpt-4o-mini", 80),
        ],
    },
    {
        "name": "OllamaCloud",
        "env_key": "OLLAMA_API_KEY",
        "client_type": "openai",
        "base_url_env": "OLLAMA_CLOUD_URL",
        "base_url_default": None,
        "models": [
            ("llama3.1:70b", 85),
            ("mistral:7b", 70),
        ],
    },
]

# ── Estado global ───────────────────────────────────────────────────────────────

_active_pidx: int = -1
_active_model: str = ""
_active_client_type: str = ""
_failed: set = set()
_all_dead: bool = False
_last_check: float = 0
_RETRY_SECS: float = 30
_LLM_TIMEOUT_SECS: int = 15
_ATTEMPT_DEADLINE_SECS: int = 22
# RLock (reentrante): _llamar() llama _pick_best() desde dentro de `with _lock`,
# y _pick_best() vuelve a adquirir _lock. Con un Lock normal eso es un DEADLOCK
# que congela el hilo de IA y deja la UI colgada en "GENERANDO" para siempre.
_lock = threading.RLock()
_IDIOMA = "Respondé siempre en español rioplatense, sin emojis, de forma concisa."
_MAX_RECORDS_PER_MODULE = 5
_MAX_FIELD_CHARS = 180
_MAX_PROMPT_CHARS = 8000

_RESUMEN_MODULE_FIELDS = {
    "animo": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("puntaje", "puntaje"),
        ("nota", "nota"),
    ),
    "respiracion": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("tecnica", "tecnica"),
        ("duracion_minutos", "duracion_min"),
        ("ciclos", "ciclos"),
    ),
    "tcc": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("situacion", "situacion"),
        ("emocion", "emocion"),
        ("intensidad", "intensidad"),
        ("pensamiento", "pensamiento"),
        ("respuesta_alternativa", "respuesta_alternativa"),
        ("distorsiones", "distorsiones"),
    ),
    "checklist": (
        ("fecha", "fecha"),
        ("descripcion", "descripcion"),
        ("categoria", "categoria"),
        ("origen", "origen"),
    ),
    "actividades": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("animo", "animo"),
        ("actividad", "actividad"),
        ("resultado", "resultado"),
    ),
    "timer": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("nombre", "nombre"),
        ("categoria", "categoria"),
        ("duracion_config", "duracion_config"),
        ("duracion_real", "duracion_real"),
        ("notas", "notas"),
    ),
    "recordatorios": (
        ("hora", "hora"),
        ("mensaje", "mensaje"),
        ("activa", "activa"),
    ),
    "dbt": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("skill_id", "skill"),
        ("skill_version", "version"),
        ("familia", "familia"),
        ("necesidad", "necesidad"),
        ("malestar_antes", "malestar_antes"),
        ("malestar_despues", "malestar_despues"),
        ("resultado", "resultado"),
        ("duracion_seg", "duracion_seg"),
        ("nota", "nota"),
    ),
    "avisos_disparados": (
        ("fecha", "fecha"),
        ("hora", "hora"),
        ("mensaje", "mensaje"),
        ("cerrado", "cerrado"),
    ),
}

_RESUMEN_MODULE_TITLES = {
    "animo": "Animo",
    "respiracion": "Respiracion",
    "tcc": "TCC",
    "checklist": "Rutina",
    "actividades": "Actividades conductuales",
    "timer": "Temporizador",
    "recordatorios": "Recordatorios asignados",
    "dbt": "DBT",
    "avisos_disparados": "Avisos disparados",
}

_picked = False
_picked_lock = threading.Lock()


def _ensure_provider():
    global _picked
    with _picked_lock:
        if _picked:
            return
        _picked = True
    threading.Thread(target=_pick_best, daemon=True).start()


def _cfg():
    return _config_get


def _compact_text(value, max_chars: int = _MAX_FIELD_CHARS) -> str:
    text = " ".join(str(value).split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _format_clinical_record(row: dict, fields: tuple[tuple[str, str], ...]) -> str:
    parts: list[str] = []
    for key, label in fields:
        value = row.get(key)
        if value is None or value == "":
            continue
        parts.append(f"{label}: {_compact_text(value)}")
    return "; ".join(parts)


def _truncate_block(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    suffix = "\n[Contexto truncado para mantener el tamaño del prompt.]"
    cut = text[: max(0, max_chars - len(suffix))]
    if "\n" in cut:
        cut = cut.rsplit("\n", 1)[0]
    return cut.rstrip() + suffix


def _resumen_registros_recientes(modulos: dict[str, list]) -> str:
    sections: list[str] = []
    for key, rows in modulos.items():
        if not rows:
            continue
        fields = _RESUMEN_MODULE_FIELDS[key]
        lines: list[str] = []
        for row in rows[:_MAX_RECORDS_PER_MODULE]:
            if not isinstance(row, dict):
                continue
            formatted = _format_clinical_record(row, fields)
            if formatted:
                lines.append(f"  - {formatted}")
        if lines:
            title = _RESUMEN_MODULE_TITLES[key]
            sections.append(f"{title} (hasta 5 recientes):\n" + "\n".join(lines))
    if not sections:
        return ""
    return "Registros recientes con contenido clinico:\n" + "\n".join(sections)


def _prompt_con_presupuesto(contexto: str, instrucciones: str) -> str:
    budget_contexto = max(1200, _MAX_PROMPT_CHARS - len(instrucciones) - 2)
    contexto = _truncate_block(contexto, budget_contexto)
    return f"{contexto}\n\n{instrucciones}"




def is_available() -> bool:
    """True si al menos un proveedor IA esta funcionando."""
    _ensure_provider()
    with _lock:
        if _all_dead:
            return False
        if _active_pidx < 0:
            return False
        return True


def status_msg() -> str:
    """Mensaje legible sobre el estado actual de la IA."""
    _ensure_provider()
    with _lock:
        if _all_dead:
            return "IA no disponible momentaneamente"
        if _active_pidx >= 0:
            pname = _PROVIDERS[_active_pidx]["name"]
            return f"IA disponible via {pname}"
        return "IA: verificando disponibilidad..."


def _make_client(pidx: int):
    """Crea el cliente para un proveedor. Retorna (client, error_msg)."""
    p = _PROVIDERS[pidx]
    key = _cfg()(p["env_key"])
    if not key:
        return None, f"{p['name']}: sin API key"

    ct = p["client_type"]
    try:
        if ct == "groq":
            from groq import Groq

            return Groq(api_key=key), None
        elif ct == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=key)
            return ("gemini", genai), None
        elif ct == "openai":
            from openai import OpenAI

            base_url = _cfg()(p.get("base_url_env", "")) or p.get("base_url_default")
            kwargs = {"api_key": key}
            if base_url:
                kwargs["base_url"] = base_url
            return OpenAI(**kwargs), None
    except ImportError:
        return None, f"{p['name']}: libreria no instalada"
    except Exception as e:
        return None, f"{p['name']}: {str(e)[:80]}"
    return None, "tipo desconocido"


def _do_chat(client, ct: str, model: str, msgs: list) -> str:
    """Ejecuta chat de acuerdo al tipo de cliente."""
    timeout = _LLM_TIMEOUT_SECS
    try:
        if ct == "groq":
            r = client.chat.completions.create(
                model=model, messages=msgs, temperature=0.4, max_tokens=512, timeout=timeout
            )
            if not r.choices or not r.choices[0].message or not r.choices[0].message.content:
                raise ValueError(f"Groq returned empty response for model {model}")
            return r.choices[0].message.content.strip()
        elif ct == "gemini":
            _, genai_mod = client
            system = "; ".join(m["content"] for m in msgs if m["role"] == "system")
            user = msgs[-1]["content"] if msgs and msgs[-1]["role"] == "user" else ""
            prompt = f"{system}\n\n{user}" if system else user
            gm = genai_mod.GenerativeModel(model)
            # Gemini no tiene parametro timeout directo en generate_content en algunas versiones,
            # pero request_options lo soporta en las versiones actuales. Si Gemini
            # queda colgado, el caller tambien tiene un deadline defensivo por intento.
            r = gm.generate_content(
                prompt,
                generation_config={"temperature": 0.4, "max_output_tokens": 512},
                request_options={"timeout": timeout},
            )
            if not r.text:
                raise ValueError(f"Gemini returned empty response for model {model}")
            return r.text.strip()
        elif ct == "openai":
            r = client.chat.completions.create(
                model=model, messages=msgs, temperature=0.4, max_tokens=512, timeout=timeout
            )
            if not r.choices or not r.choices[0].message or not r.choices[0].message.content:
                raise ValueError(f"OpenAI-compatible returned empty response for model {model}")
            return r.choices[0].message.content.strip()
    except Exception as e:
        logger.error(redact(f"Error en _do_chat ({ct}/{model}): {str(e)}"))
        raise e
    raise RuntimeError(f"Tipo desconocido: {ct}")


def _do_chat_with_deadline(client, ct: str, model: str, msgs: list) -> str:
    """Envuelve cada proveedor/modelo con deadline duro sin bloquear el hilo de UI.

    Algunos SDKs pueden ignorar timeouts o colgarse en red. No podemos matar
    una llamada externa ya iniciada, pero si podemos abandonarla en un hilo
    daemon y continuar el fallback a otros modelos/proveedores.
    """
    out: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=1)

    def _target():
        try:
            out.put(("ok", _do_chat(client, ct, model, msgs)))
        except Exception as exc:
            out.put(("err", exc))

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(_ATTEMPT_DEADLINE_SECS)
    if t.is_alive():
        raise TimeoutError(
            f"Timeout IA {ct}/{model} tras {_ATTEMPT_DEADLINE_SECS}s"
        )
    status, payload = out.get_nowait()
    if status == "err":
        raise payload
    return str(payload)


def _pick_best() -> None:
    """Busca el mejor proveedor/modelo disponible. Modifica estado global."""
    global _active_pidx, _active_model, _active_client_type, _all_dead, _last_check

    # 1. Preparar lista de candidatos fuera del lock
    scored = []
    with _lock:
        _last_check = time.time()
        for pi, p in enumerate(_PROVIDERS):
            for mi, (mid, score) in enumerate(p["models"]):
                if (p["name"], mid) in _failed:
                    continue
                scored.append((score, pi, mi, mid, p["client_type"]))

    scored.sort(key=lambda x: -x[0])

    # 2. Probar candidatos uno a uno (lento, fuera del lock)
    for score, pi, mi, mid, ct in scored:
        client, err = _make_client(pi)
        if client and not err:
            with _lock:
                _active_pidx = pi
                _active_model = mid
                _active_client_type = ct
                _all_dead = False
                logger.info(f"IA seleccionada: {_PROVIDERS[pi]['name']} / {mid}")
            return
        else:
            if err and ("sin API key" not in str(err) and "libreria" not in str(err)):
                with _lock:
                    _failed.add((_PROVIDERS[pi]["name"], mid))
            continue

    # 3. Si llegamos aca, ninguno funciono
    with _lock:
        _active_pidx = -1
        _active_model = ""
        _active_client_type = ""
        _all_dead = True
        logger.warning("No se encontro ningun proveedor IA funcional")


def _llamar(prompt: str, sistema: str, fn_name: str, patient_id, on_result, on_error):
    def _run():
        global _all_dead, _last_check, _failed

        audit_id = None
        sb = None
        try:
            if not visual_qa_enabled() and create_client:
                cfg = _cfg()
                url = cfg("SUPABASE_URL")
                key = _supabase_hub_key()
                if url and key:
                    sb = create_client(url, key)
                    payload = {
                        "provider": "Pending",
                        "model": "Pending",
                        "fn_name": fn_name,
                        "prompt_user": prompt,
                        "prompt_system": sistema + " " + _IDIOMA,
                    }
                    if patient_id:
                        payload["patient_id"] = patient_id
                    r = sb.table("ia_audit_log").insert(payload).execute()
                    if r.data:
                        audit_id = r.data[0].get("id")
        except Exception as e:
            logger.error(redact(f"Error en ia_audit_log insert: {e}"))

        try:
            msgs = [
                {"role": "system", "content": sistema + " " + _IDIOMA},
                {"role": "user", "content": prompt},
            ]

            # Presupuesto de intentos: cubre todos los modelos de todos los
            # proveedores + 1. Así, si los primeros proveedores fallan (key
            # inválida, cuota agotada), el fallback recorre el resto hasta dar
            # con uno funcional, en vez de rendirse tras 2 intentos.
            max_attempts = sum(len(p["models"]) for p in _PROVIDERS) + 1

            def _is_auth_error(msg: str) -> bool:
                # Solo señales de autenticación reales → matar el proveedor entero.
                # NO incluir "invalid_request_error" (un model-not-found también lo
                # usa) ni "permission denied" (eso es RLS de Supabase, no del LLM).
                m = msg.lower()
                return any(s in m for s in (
                    "401", "invalid api key", "invalid_api_key", "incorrect api key",
                    "unauthorized", "no api key", "api key not valid",
                ))

            def _fail_provider(pname: str, pidx: int) -> None:
                """Marca TODOS los modelos del proveedor como fallidos (key muerta)."""
                for _m, _ in _PROVIDERS[pidx]["models"]:
                    _failed.add((pname, _m))

            for attempt in range(max_attempts):
                with _lock:
                    now = time.time()
                    if _all_dead and (now - _last_check) > _RETRY_SECS:
                        _failed.clear()
                        _pick_best()

                    if _active_pidx < 0:
                        _pick_best()

                    if _all_dead or _active_pidx < 0:
                        if audit_id and sb:
                            try:
                                sb.table("ia_audit_log").update(
                                    {"error": "IA no disponible momentaneamente"}
                                ).eq("id", audit_id).execute()
                            except Exception:
                                pass
                        on_error("IA no disponible momentaneamente")
                        return

                    pidx = _active_pidx
                    pname = _PROVIDERS[pidx]["name"]
                    model = _active_model
                    ct = _active_client_type

                # Crear cliente fuera del lock
                client, err = _make_client(pidx)

                if not client:
                    with _lock:
                        # Sin cliente (sin key / sin librería): proveedor muerto.
                        _fail_provider(pname, pidx)
                        _pick_best()
                    continue

                try:
                    result = _do_chat_with_deadline(client, ct, model, msgs)
                    if audit_id and sb:
                        try:
                            sb.table("ia_audit_log").update(
                                {"provider": pname, "model": model, "output": result}
                            ).eq("id", audit_id).execute()
                        except Exception as e:
                            logger.error(redact(f"Error en ia_audit_log update: {e}"))
                    on_result(result)
                    return
                except Exception as e:
                    err_str = str(e)
                    logger.error(
                        redact(f"Fallo intento {attempt + 1} con {pname}/{model}: {err_str}")
                    )
                    with _lock:
                        if _is_auth_error(err_str):
                            # Key inválida/sin permiso → todo el proveedor muerto,
                            # no tiene sentido probar sus otros modelos.
                            _fail_provider(pname, pidx)
                        else:
                            # Error puntual del modelo (cuota, modelo inexistente,
                            # timeout): descarta solo este modelo y prueba el siguiente.
                            _failed.add((pname, model))
                        _pick_best()
                    if _all_dead:
                        if audit_id and sb:
                            try:
                                sb.table("ia_audit_log").update(
                                    {"error": "IA no disponible momentaneamente"}
                                ).eq("id", audit_id).execute()
                            except Exception:
                                pass
                        on_error("IA no disponible momentaneamente")
                        return
                    # Quedan proveedores/modelos: continuar el fallback.

            # Presupuesto agotado sin éxito.
            if audit_id and sb:
                try:
                    sb.table("ia_audit_log").update(
                        {"error": "IA no disponible momentaneamente"}
                    ).eq("id", audit_id).execute()
                except Exception:
                    pass
            on_error("IA no disponible momentaneamente")
        except Exception as e:
            logger.error(redact(f"Error critico en hilo IA: {str(e)}"))
            if audit_id and sb:
                try:
                    sb.table("ia_audit_log").update({"error": f"Error interno: {str(e)[:80]}"}).eq(
                        "id", audit_id
                    ).execute()
                except Exception:
                    pass
            on_error("Error interno en el modulo de IA")

    threading.Thread(target=_run, daemon=True).start()


# ── API publica ──────────────────────────────────────────────────────────────────


def _contexto_clinico_valido(nombre: str, patient_id, on_error) -> bool:
    """Guard clinico BLOQUEANTE (informe owner v1.0): la IA nunca genera
    contenido clinico sin un paciente real en contexto. Sin esto, un nombre
    "Sin paciente" o un pid vacio producia borradores clinicos ficticios
    (y gastaba tokens + fila de audit log)."""
    nombre_norm = (nombre or "").strip().lower()
    if not nombre_norm or nombre_norm == "sin paciente" or not (patient_id or "").strip():
        try:
            on_error("Seleccioná un paciente antes de generar.")
        except Exception:
            pass
        return False
    return True


# Especificación por módulo asignable (reorganización owner v1.0): qué genera
# la IA y en qué formato clave:valor responde. El Hub parsea estas claves y
# SOLO escribe cuando el profesional aprueba explícitamente.
ASIGNACION_SPECS = {
    "avisos": (
        "UN recordatorio de bienestar (modulo Recordatorios de Bienestar)",
        "hora: <HH:MM en 24h>\nmensaje: <maximo 100 caracteres, segunda persona>",
    ),
    "timer": (
        "UN temporizador de actividad (modulo Temporizador de Actividades)",
        "nombre: <maximo 24 caracteres>\nminutos: <entero entre 1 y 180>\ncategoria: <una palabra>",
    ),
    "rutina": (
        "UNA tarea de rutina diaria (modulo Checklist de Rutina Diaria)",
        "tarea: <maximo 100 caracteres, accionable, segunda persona>\nseccion: <manana|tarde|noche>",
    ),
    "actividades": (
        "UNA actividad de activacion conductual (modulo Asistente de Activacion Conductual)",
        "nombre: <maximo 50 caracteres>\ndescripcion: <maximo 120 caracteres>\n"
        "categoria: <Autocuidado|Física|Cognitiva|Placer|Social|Maestría>",
    ),
}


def generar_asignacion(modulo: str, datos: dict, nombre: str, on_result, on_error, patient_id=None):
    """Genera UN borrador de asignación para un módulo del Plan terapéutico.

    SOLO genera texto: la escritura clínica ocurre únicamente cuando el
    profesional toca "Aprobar y asignar" en el Hub (nada automático)."""
    if modulo not in ASIGNACION_SPECS:
        try:
            on_error(f"Módulo no asignable: {modulo}")
        except Exception:
            pass
        return
    if not _contexto_clinico_valido(nombre, patient_id, on_error):
        return
    _ensure_provider()

    animo = (datos or {}).get("animo", [])
    puntajes = [r.get("puntaje") for r in animo if r.get("puntaje")]
    prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else None
    contexto = f"Paciente: {nombre}."
    if prom is not None:
        contexto += f" Animo promedio reciente: {prom}/10."

    que, formato = ASIGNACION_SPECS[modulo]
    prompt = (
        f"Fecha actual: {date.today()}\n"
        f"{contexto}\n\n"
        f"Genera {que} como BORRADOR para que el terapeuta lo revise y "
        "apruebe antes de asignarlo.\n"
        "Responde SOLO en este formato exacto, una clave por linea, sin "
        "explicaciones ni comillas:\n"
        f"{formato}"
    )
    sistema = (
        "Sos un asistente profesional para terapeutas. Generas borradores de "
        "asignaciones que requieren validacion profesional explicita. "
        "Nunca asignas nada por tu cuenta ni haces diagnosticos."
    )
    _llamar(prompt, sistema, f"generar_asignacion_{modulo}", patient_id, on_result, on_error)


def generar_resumen_paciente(datos: dict, nombre: str, on_result, on_error, patient_id=None):
    """Genera un resumen clinico completo del paciente a partir de sus 8 modulos."""
    if not _contexto_clinico_valido(nombre, patient_id, on_error):
        return
    _ensure_provider()

    animo = datos.get("animo", [])
    respiracion = datos.get("respiracion", [])
    tcc = datos.get("tcc", [])
    checklist = datos.get("checklist", [])
    actividades = datos.get("actividades", [])
    timer = datos.get("timer", [])
    recordatorios = datos.get("recordatorios", [])
    dbt = datos.get("dbt", [])
    avisos_disparados = datos.get("avisos_disparados", [])

    puntajes = [r.get("puntaje") for r in animo if r.get("puntaje")]
    prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else None

    contexto = (
        f"Fecha actual: {date.today()}\n"
        f"Paciente: {nombre}.\n"
        f"Registros disponibles:\n"
        f"- Animo: {len(animo)} registros"
        + (f", promedio {prom}/10" if prom else "") + "\n"
        f"- Respiracion: {len(respiracion)} sesiones\n"
        f"- TCC: {len(tcc)} registros\n"
        f"- Rutina: {len(checklist)} completadas\n"
        f"- Actividades conductuales: {len(actividades)} registros\n"
        f"- Temporizador: {len(timer)} sesiones\n"
        f"- Recordatorios asignados: {len(recordatorios)}\n"
        f"- DBT: {len(dbt)} registros\n"
        f"- Avisos disparados: {len(avisos_disparados)} registros\n"
    )
    if tcc:
        emociones = [r.get("emocion") for r in tcc[:5] if r.get("emocion")]
        if emociones:
            contexto += f"Emociones TCC recientes: {', '.join(emociones[:3])}.\n"
    detalles = _resumen_registros_recientes(
        {
            "animo": animo,
            "respiracion": respiracion,
            "tcc": tcc,
            "checklist": checklist,
            "actividades": actividades,
            "timer": timer,
            "recordatorios": recordatorios,
            "dbt": dbt,
            "avisos_disparados": avisos_disparados,
        }
    )
    if detalles:
        contexto += "\n" + detalles + "\n"

    instrucciones = (
        "Redacta un resumen clinico ordenado y breve para el terapeuta. "
        "Usa los registros recientes como evidencia, sin inventar datos ausentes. "
        "No incluyas identificadores tecnicos ni datos de cuenta. "
        "El texto es un borrador para revision profesional. "
        "Usa exactamente estas 4 secciones, cada una de 1-2 oraciones:\n"
        "Estado general: ...\n"
        "Adherencia y habitos: ...\n"
        "Aspectos a monitorear: ...\n"
        "Recomendacion de sesion: ...\n"
        "Sin texto adicional fuera de esas secciones."
    )
    prompt = _prompt_con_presupuesto(contexto, instrucciones)
    sistema = (
        "Sos un asistente profesional para terapeutas de salud mental. "
        "Analiza datos de apps de bienestar para dar contexto al terapeuta. "
        "Nunca haces diagnosticos ni recomiendas medicacion. "
        "Usa lenguaje profesional conciso en espanol rioplatense."
    )
    _llamar(prompt, sistema, "generar_resumen_paciente", patient_id, on_result, on_error)


def autocompletar_actividad(nombre_parcial: str, on_result, on_error, patient_id=None):
    """Sugiere una descripcion corta para una actividad conductual.

    Sin guard de paciente A PROPOSITO: completa la descripcion de una
    actividad del banco (contenido generico, no clinico-personal); la usa
    tambien el Banco de actividades global, que no tiene paciente."""
    if not (nombre_parcial or "").strip():
        try:
            on_error("Escribi el nombre de la actividad primero.")
        except Exception:
            pass
        return
    _ensure_provider()
    prompt = (
        f"Fecha actual: {date.today()}\n"
        f"Nombre de la actividad: '{nombre_parcial}'.\n"
        "Escribi una descripcion breve de apoyo conductual (maximo 20 palabras) "
        "para incluir en un banco de actividades conductuales. "
        "Solo la descripcion, sin comillas."
    )
    sistema = (
        "Sos un asistente para terapeutas que completa descripciones de actividades conductuales. "
        "No haces diagnosticos ni personalizas indicaciones clinicas."
    )
    _llamar(prompt, sistema, "autocompletar_actividad", patient_id, on_result, on_error)
