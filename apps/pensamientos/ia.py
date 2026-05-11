"""
ia.py — Integración Groq para Registro de Pensamientos.
System prompt fijo y estricto bajo el modelo TCC de Beck.
"""
import json
import urllib.request
import urllib.error

SYSTEM_PROMPT = (
    "Eres un asistente psicoeducativo especializado en Terapia Cognitivo-Conductual (TCC). "
    "Tu rol es acompañar al paciente en la revisión de sus registros de pensamientos, "
    "sin reemplazar al terapeuta. Debes:\n"
    "1. Reconocer la emoción y validar la experiencia sin juzgar.\n"
    "2. Señalar brevemente si hay patrones de distorsión cognitiva presentes, nombrándolos "
    "por su nombre técnico pero explicándolos con lenguaje accesible.\n"
    "3. Reforzar positivamente el esfuerzo del paciente por cuestionar el pensamiento automático.\n"
    "4. Si la respuesta alternativa escrita por el paciente es coherente y equilibrada, "
    "validarla y enriquecerla levemente.\n"
    "5. Si la respuesta alternativa es aún sesgada, ofrecer una perspectiva más equilibrada "
    "sin invalidar al paciente.\n"
    "6. Cerrar con una pregunta de reflexión breve que invite a profundizar.\n"
    "Tono: cálido, profesional, sin clichés vacíos, sin frases genéricas como "
    "'recuerda que tienes fortalezas'. Máximo 200 palabras."
)


def obtener_feedback_ia(datos: dict, api_key: str, historial_reciente: list = None) -> str:
    """
    Envía el registro a Groq (llama3-70b-8192) y devuelve la reflexión TCC.
    Lanza excepción si el request falla — el caller maneja el error.
    """
    partes = []
    if datos.get("situacion"):
        partes.append(f"Situación: {datos['situacion']}")
    if datos.get("emocion"):
        partes.append(f"Emoción: {datos['emocion']} (intensidad {datos.get('intensidad', 5)}/10)")
    if datos.get("pensamiento"):
        partes.append(f"Pensamiento automático: {datos['pensamiento']}")
    if datos.get("creencia_antes") is not None:
        partes.append(f"Creencia inicial en el pensamiento: {datos['creencia_antes']}%")
    if datos.get("distorsiones_list"):
        partes.append(f"Distorsiones identificadas: {', '.join(datos['distorsiones_list'])}")
    if datos.get("evidencia_favor"):
        partes.append(f"Evidencia a favor del pensamiento: {datos['evidencia_favor']}")
    if datos.get("evidencia_contra"):
        partes.append(f"Evidencia en contra: {datos['evidencia_contra']}")
    if datos.get("respuesta"):
        partes.append(f"Respuesta alternativa: {datos['respuesta']}")
    if datos.get("creencia_despues") is not None:
        partes.append(f"Creencia después de analizar: {datos['creencia_despues']}%")
    if datos.get("emocion_resultante"):
        partes.append(f"Emoción resultante: {datos['emocion_resultante']}")

    if historial_reciente:
        partes.append("\n--- Últimos registros del paciente (contexto) ---")
        for h in historial_reciente[:3]:
            partes.append(
                f"- {h.get('fecha', '')}: {h.get('emocion', '')} "
                f"({h.get('intensidad', 0)}/10) — {str(h.get('situacion', ''))[:70]}"
            )

    payload = json.dumps({
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": "\n".join(partes)},
        ],
        "max_tokens": 350,
        "temperature": 0.65,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


_PREGUNTAS_PROMPT = (
    "Eres un asistente TCC. Genera exactamente 6 preguntas guía breves (máx 12 palabras c/u) "
    "para acompañar al paciente en un registro de pensamientos según el modelo de Beck. "
    "Una pregunta por cada paso: 1=Situación, 2=Emoción, 3=Pensamiento automático, "
    "4=Análisis/distorsiones, 5=Respuesta alternativa, 6=Cierre/reflexión. "
    "Respondé ÚNICAMENTE con un JSON válido: {\"1\":\"...\",\"2\":\"...\",\"3\":\"...\","
    "\"4\":\"...\",\"5\":\"...\",\"6\":\"...\"}. Sin texto adicional."
)

_PREGUNTAS_FALLBACK = {
    "1": "Describí el contexto: dónde estabas, qué hacías, con quién.",
    "2": "Identificar la emoción con precisión — las emociones son señales, no el problema.",
    "3": "El pensamiento automático aparece rápido e involuntario. Registralo sin juzgarlo.",
    "4": "Identificá distorsiones y buscá evidencia real — el corazón del trabajo cognitivo.",
    "5": "¿Cuál sería una mirada más realista y compasiva de la situación?",
    "6": "Resumen clínico del registro — basado en el modelo de Beck.",
}


def obtener_preguntas_sesion(api_key: str) -> dict:
    """Llama a Groq una sola vez al inicio de sesión para generar preguntas guía por paso."""
    try:
        payload = json.dumps({
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": _PREGUNTAS_PROMPT},
                {"role": "user",   "content": "Genera las 6 preguntas ahora."},
            ],
            "max_tokens": 200,
            "temperature": 0.8,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        raw = data["choices"][0]["message"]["content"].strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(raw[start:end])
            if all(str(i) in parsed for i in range(1, 7)):
                return {str(k): str(v) for k, v in parsed.items()}
    except Exception:
        pass
    return _PREGUNTAS_FALLBACK.copy()
