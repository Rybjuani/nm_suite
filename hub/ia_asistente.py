"""ia_asistente.py — Asistente IA para el terapeuta (Groq llama3-70b).

NO interactúa con el paciente. El terapeuta siempre aprueba antes de aplicar.
"""
import threading


def _get_client():
    try:
        from groq import Groq
        from shared.config import get as _cfg
        key = _cfg("GROQ_KEY") or _cfg("GROQ_API_KEY")
        if not key:
            return None, "GROQ_KEY no configurada en .env"
        return Groq(api_key=key), None
    except ImportError:
        return None, "groq no instalado (pip install groq)"
    except Exception as e:
        return None, str(e)[:80]


_MODELO = "llama3-70b-8192"
_IDIOMA = "Respondé siempre en español rioplatense, sin emojis, de forma concisa."


def _llamar(prompt: str, sistema: str, on_result, on_error):
    def _run():
        client, motivo = _get_client()
        if not client:
            on_error(motivo)
            return
        try:
            resp = client.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": sistema + " " + _IDIOMA},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.4,
                max_tokens=512,
                timeout=15,
            )
            on_result(resp.choices[0].message.content.strip())
        except Exception as e:
            on_error(str(e)[:120])

    threading.Thread(target=_run, daemon=True).start()


# ── API pública ───────────────────────────────────────────────────────────────

def resumir_evolucion(datos: dict, nombre: str, on_result, on_error):
    """Genera un resumen narrativo de la evolución del paciente."""
    animo = datos.get("animo", [])
    resp  = datos.get("resp", [])
    pens  = datos.get("pens", [])
    check = datos.get("checklist", [])

    puntajes = [r.get("puntaje") for r in animo if r.get("puntaje")]
    prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else None

    contexto = (
        f"Paciente: {nombre}.\n"
        f"Registros de ánimo ({len(animo)}): promedio {prom}/10.\n"
        f"Sesiones de respiración: {len(resp)}.\n"
        f"Registros TCC: {len(pens)}.\n"
        f"Checklist completadas: {len(check)} ítems.\n"
    )
    if pens:
        emociones = [r.get("emocion","") for r in pens[:5] if r.get("emocion")]
        if emociones:
            contexto += f"Últimas emociones registradas: {', '.join(emociones)}.\n"

    prompt = (
        f"{contexto}\n"
        "Escribí un párrafo breve (3-4 oraciones) que resuma la evolución clínica "
        "de este paciente para el terapeuta. Destacá tendencias, áreas de progreso "
        "y posibles áreas de atención."
    )
    sistema = (
        "Sos un asistente clínico para terapeutas de salud mental. "
        "Analizás datos de apps de bienestar para dar contexto al terapeuta. "
        "Nunca hacés diagnósticos ni recomendás medicación."
    )
    _llamar(prompt, sistema, on_result, on_error)


def sugerir_acciones(datos: dict, nombre: str, on_result, on_error):
    """Devuelve lista de sugerencias de acción para el terapeuta."""
    animo = datos.get("animo", [])
    check = datos.get("checklist", [])

    puntajes = [r.get("puntaje") for r in animo if r.get("puntaje")]
    prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else None
    tendencia = ""
    if len(puntajes) >= 3:
        if puntajes[0] < puntajes[-1]:
            tendencia = "El ánimo está mejorando en los últimos registros."
        elif puntajes[0] > puntajes[-1]:
            tendencia = "El ánimo está bajando en los últimos registros."

    totales = len(check)

    prompt = (
        f"Paciente: {nombre}. Ánimo promedio: {prom}/10. {tendencia} "
        f"Checklist completadas en total: {totales}.\n\n"
        "Generá exactamente 3 sugerencias de acción concretas para el terapeuta "
        "(asignar tarea, ajustar actividad, enviar recordatorio, etc.). "
        "Formato: una sugerencia por línea, empezando con '•'."
    )
    sistema = (
        "Sos un asistente clínico para terapeutas. "
        "Sugerís acciones terapéuticas concretas basadas en datos de comportamiento. "
        "Nunca hacés diagnósticos."
    )
    _llamar(prompt, sistema, on_result, on_error)


def generar_tarea(contexto_paciente: str, on_result, on_error):
    """Genera un borrador de tarea de rutina personalizada."""
    prompt = (
        f"Contexto del paciente: {contexto_paciente}\n\n"
        "Generá una tarea de rutina terapéutica concreta y personalizada "
        "(máximo 15 palabras, accionable, en segunda persona). "
        "Solo la tarea, sin explicación."
    )
    sistema = "Sos un asistente clínico para terapeutas. Generás tareas terapéuticas breves."
    _llamar(prompt, sistema, on_result, on_error)


def autocompletar_actividad(nombre_parcial: str, on_result, on_error):
    """Sugiere una descripción corta para una actividad conductual."""
    prompt = (
        f"Nombre de la actividad: '{nombre_parcial}'.\n"
        "Escribí una descripción terapéutica breve (máximo 20 palabras) "
        "para incluir en un banco de actividades conductuales. "
        "Solo la descripción, sin comillas."
    )
    sistema = "Sos un asistente para terapeutas que completa descripciones de actividades conductuales."
    _llamar(prompt, sistema, on_result, on_error)
