"""ia_asistente.py — Asistente IA multi-proveedor para el terapeuta.

Soporta: Groq, Gemini, OpenCode (OpenAI-compatible), Ollama Cloud.
Selecciona automaticamente el mejor modelo disponible para tareas clinicas.
Si un modelo falla o se depreca, pasa al siguiente automaticamente.
Si ningun proveedor funciona, deshabilita IA con mensaje amigable.
"""
import threading
import time
from datetime import date

# ── Registro de proveedores ─────────────────────────────────────────────────────

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
        "name": "OpenCode",
        "env_key": "OPENCODE_API_KEY",
        "client_type": "openai",
        "base_url_env": "OPENCODE_BASE_URL",
        "base_url_default": "https://api.opencode.ai/v1",
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
_lock = threading.Lock()
_IDIOMA = "Respondé siempre en español rioplatense, sin emojis, de forma concisa."


def _cfg():
    from shared.config import get
    return get


def is_available() -> bool:
    """True si al menos un proveedor IA esta funcionando."""
    with _lock:
        if _all_dead:
            return False
        if _active_pidx < 0:
            return False
        return True


def status_msg() -> str:
    """Mensaje legible sobre el estado actual de la IA."""
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
    if ct == "groq":
        r = client.chat.completions.create(
            model=model, messages=msgs,
            temperature=0.4, max_tokens=512, timeout=15)
        if not r.choices or not r.choices[0].message or not r.choices[0].message.content:
            raise ValueError(f"Groq returned empty response for model {model}")
        return r.choices[0].message.content.strip()
    elif ct == "gemini":
        _, genai_mod = client
        system = "; ".join(m["content"] for m in msgs if m["role"] == "system")
        user = msgs[-1]["content"] if msgs and msgs[-1]["role"] == "user" else ""
        prompt = f"{system}\n\n{user}" if system else user
        gm = genai_mod.GenerativeModel(model)
        r = gm.generate_content(
            prompt,
            generation_config={"temperature": 0.4, "max_output_tokens": 512})
        return r.text.strip()
    elif ct == "openai":
        r = client.chat.completions.create(
            model=model, messages=msgs,
            temperature=0.4, max_tokens=512, timeout=15)
        if not r.choices or not r.choices[0].message or not r.choices[0].message.content:
            raise ValueError(f"OpenAI-compatible returned empty response for model {model}")
        return r.choices[0].message.content.strip()
    raise RuntimeError(f"Tipo desconocido: {ct}")


def _pick_best() -> None:
    """Busca el mejor proveedor/modelo disponible. Modifica estado global."""
    global _active_pidx, _active_model, _active_client_type, _all_dead, _last_check

    _last_check = time.time()

    scored = []
    for pi, p in enumerate(_PROVIDERS):
        for mi, (mid, score) in enumerate(p["models"]):
            if (p["name"], mid) in _failed:
                continue
            scored.append((score, pi, mi, mid, p["client_type"]))
    scored.sort(key=lambda x: -x[0])

    for score, pi, mi, mid, ct in scored:
        if (_PROVIDERS[pi]["name"], mid) in _failed:
            continue
        client, err = _make_client(pi)
        if client and not err:
            _active_pidx = pi
            _active_model = mid
            _active_client_type = ct
            _all_dead = False
            return
        else:
            # Solo marcar como fallido si NO es error de credenciales
            if err and ("sin API key" not in str(err) and "libreria" not in str(err)):
                _failed.add((_PROVIDERS[pi]["name"], mid))
            else:
                # Error de auth/key: no blacklistear, reintentar luego
                if _active_pidx < 0:
                    _last_check = 0  # Forzar reintento rapido
            continue

    _active_pidx = -1
    _active_model = ""
    _active_client_type = ""
    _all_dead = True


def _llamar(prompt: str, sistema: str, on_result, on_error):
    def _run():
        global _all_dead, _last_check, _failed

        msgs = [
            {"role": "system", "content": sistema + " " + _IDIOMA},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(2):
            with _lock:
                now = time.time()
                if _all_dead and (now - _last_check) > _RETRY_SECS:
                    _failed.clear()
                    _pick_best()

                if _active_pidx < 0:
                    _pick_best()

                if _all_dead or _active_pidx < 0:
                    on_error("IA no disponible momentaneamente")
                    return

                pname = _PROVIDERS[_active_pidx]["name"]
                model = _active_model
                ct = _active_client_type
                client, err = _make_client(_active_pidx)
                if not client:
                    _failed.add((pname, model))
                    _pick_best()
                    if _all_dead:
                        on_error("IA no disponible momentaneamente")
                        return
                    continue

            try:
                result = _do_chat(client, ct, model, msgs)
                on_result(result)
                return
            except Exception as e:
                with _lock:
                    _failed.add((pname, model))
                    _pick_best()
                if attempt == 1 or _all_dead:
                    on_error("IA no disponible momentaneamente")
                    return

        on_error("IA no disponible momentaneamente")

    threading.Thread(target=_run, daemon=True).start()


# ── API publica ──────────────────────────────────────────────────────────────────

def resumir_evolucion(datos: dict, nombre: str, on_result, on_error):
    """Genera un resumen narrativo de la evolucion del paciente."""
    animo = datos.get("animo", [])
    resp = datos.get("resp", [])
    pens = datos.get("pens", [])
    check = datos.get("checklist", [])

    puntajes = [r.get("puntaje") for r in animo if r.get("puntaje")]
    prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else None

    contexto = (
        f"Fecha actual: {date.today()}\n"
        f"Paciente: {nombre}.\n"
        f"Registros de animo ({len(animo)}): promedio {prom}/10.\n"
        f"Sesiones de respiracion: {len(resp)}.\n"
        f"Registros TCC: {len(pens)}.\n"
        f"Checklist completadas: {len(check)} items.\n"
    )
    if pens:
        emociones = [r.get("emocion", "") for r in pens[:5] if r.get("emocion")]
        if emociones:
            contexto += f"Ultimas emociones registradas: {', '.join(emociones)}.\n"

    prompt = (
        f"{contexto}\n"
        "Escribi un parrafo breve (3-4 oraciones) que resuma la evolucion clinica "
        "de este paciente para el terapeuta. Destaca tendencias, areas de progreso "
        "y posibles areas de atencion."
    )
    sistema = (
        "Sos un asistente clinico para terapeutas de salud mental. "
        "Analizas datos de apps de bienestar para dar contexto al terapeuta. "
        "Nunca haces diagnosticos ni recomendas medicacion."
    )
    _llamar(prompt, sistema, on_result, on_error)


def sugerir_acciones(datos: dict, nombre: str, on_result, on_error):
    """Devuelve lista de sugerencias de accion para el terapeuta."""
    animo = datos.get("animo", [])
    check = datos.get("checklist", [])

    puntajes = [r.get("puntaje") for r in animo if r.get("puntaje")]
    prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else None
    tendencia = ""
    if len(puntajes) >= 3:
        if puntajes[0] < puntajes[-1]:
            tendencia = "El animo esta mejorando en los ultimos registros."
        elif puntajes[0] > puntajes[-1]:
            tendencia = "El animo esta bajando en los ultimos registros."

    totales = len(check)

    prompt = (
        f"Fecha actual: {date.today()}\n"
        f"Paciente: {nombre}. Animo promedio: {prom}/10. {tendencia} "
        f"Checklist completadas en total: {totales}.\n\n"
        "Genera exactamente 3 sugerencias de accion concretas para el terapeuta "
        "(asignar tarea, ajustar actividad, enviar recordatorio, etc.). "
        "Formato: una sugerencia por linea, empezando con '•'."
    )
    sistema = (
        "Sos un asistente clinico para terapeutas. "
        "Sugeris acciones terapeuticas concretas basadas en datos de comportamiento. "
        "Nunca haces diagnosticos."
    )
    _llamar(prompt, sistema, on_result, on_error)


def generar_tarea(contexto_paciente: str, on_result, on_error):
    """Genera un borrador de tarea de rutina personalizada."""
    prompt = (
        f"Fecha actual: {date.today()}\n"
        f"Contexto del paciente: {contexto_paciente}\n\n"
        "Genera una tarea de rutina terapeutica concreta y personalizada "
        "(maximo 15 palabras, accionable, en segunda persona). "
        "Solo la tarea, sin explicacion."
    )
    sistema = "Sos un asistente clinico para terapeutas. Generas tareas terapeuticas breves."
    _llamar(prompt, sistema, on_result, on_error)


def autocompletar_actividad(nombre_parcial: str, on_result, on_error):
    """Sugiere una descripcion corta para una actividad conductual."""
    prompt = (
        f"Fecha actual: {date.today()}\n"
        f"Nombre de la actividad: '{nombre_parcial}'.\n"
        "Escribi una descripcion terapeutica breve (maximo 20 palabras) "
        "para incluir en un banco de actividades conductuales. "
        "Solo la descripcion, sin comillas."
    )
    sistema = "Sos un asistente para terapeutas que completa descripciones de actividades conductuales."
    _llamar(prompt, sistema, on_result, on_error)


# Probe inicial en background — se ejecuta al importar el módulo
threading.Thread(target=_pick_best, daemon=True).start()
