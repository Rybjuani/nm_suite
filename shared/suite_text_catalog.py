"""Catalogo contractual de textos globales configurables de la Suite.

Este modulo es la fuente semantica unica para el editor del Hub y para la
Suite real. No contiene widgets, layouts, fixtures visuales ni datos clinicos.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable


@dataclass(frozen=True, slots=True)
class SuiteTextEntry:
    key: str
    section: str
    field: str
    default: str
    max_chars: int
    multiline: bool
    order: int


def _entry(
    key: str,
    section: str,
    field: str,
    default: str,
    max_chars: int,
    multiline: bool = False,
) -> SuiteTextEntry:
    return SuiteTextEntry(
        key=key,
        section=section,
        field=field,
        default=default,
        max_chars=max_chars,
        multiline=multiline,
        order=len(_ENTRIES),
    )


_ENTRIES: list[SuiteTextEntry] = []


def _add(
    key: str,
    section: str,
    field: str,
    default: str,
    max_chars: int,
    multiline: bool = False,
) -> None:
    _ENTRIES.append(_entry(key, section, field, default, max_chars, multiline))


# Chrome
_add("text.chrome.app_title", "Chrome", "Nombre de la app", "NeuroMood Suite", 40)

# Home
_add("text.home.hero_eyebrow", "Home", "Rótulo de bienvenida", "Bienvenida", 32)
_add("text.home.greeting_morning", "Home", "Saludo de mañana", "Buenos días,", 32)
_add("text.home.greeting_afternoon", "Home", "Saludo de tarde", "Buenas tardes,", 32)
_add("text.home.greeting_evening", "Home", "Saludo de noche", "Buenas noches,", 32)
_add(
    "text.home.subtitle",
    "Home",
    "Subtítulo de módulos",
    "Elegí un módulo para registrar cómo venís y sostener tu rutina.",
    96,
)
_add(
    "text.home.empty_message",
    "Home",
    "Mensaje de bienvenida sin registros",
    "Aquí tienes tu espacio personal. Arriba están tus módulos recomendados.",
    120,
    True,
)
_add("text.home.next_session_eyebrow", "Home", "Rótulo próxima sesión", "Próxima sesión", 36)
_add(
    "text.home.next_session_empty",
    "Home",
    "Texto sin sesión programada",
    "Sin sesión programada",
    56,
)

_HOME_MODULES = [
    ("animo", "Termómetro Emocional", "Registro emocional diario", "Bienestar"),
    ("respiracion", "Guía de Respiración Animada", "Técnicas de calma 4-7-8", "Calma"),
    ("registro", "Registro de Pensamientos (TCC)", "Pensamientos automáticos", "Cognitivo"),
    ("rutina", "Checklist de Rutina Diaria", "Checklist del día", "Hábitos"),
    (
        "actividades",
        "Asistente de Activación Conductual",
        "Activación conductual",
        "Acción",
    ),
    ("timer", "Temporizador de Actividades", "Sesiones de enfoque", "Focus"),
    ("avisos", "Recordatorios de Bienestar", "Recordatorios del día", "Diario"),
    ("dbt", "Habilidades DBT", "Práctica guiada breve", "Habilidades"),
]

for _module_id, _title, _desc, _chip in _HOME_MODULES:
    _section = f"Home - {_title}"
    _add(f"text.home.module.{_module_id}.title", _section, "Título de tarjeta", _title, 60)
    _add(f"text.home.module.{_module_id}.desc", _section, "Descripción de tarjeta", _desc, 80)
    _add(f"text.home.module.{_module_id}.chip", _section, "Chip de tarjeta", _chip, 28)

# Onboarding
_add(
    "text.onboarding.title_main",
    "Onboarding",
    "Título principal",
    "NeuroMood",
    48,
)
_add("text.onboarding.title_suffix", "Onboarding", "Sufijo de título", "Suite", 18)
_add(
    "text.onboarding.subtitle",
    "Onboarding",
    "Subtítulo",
    "Vinculá tu cuenta de NeuroMood. Tus datos se mantienen cifrados y bajo tu control.",
    140,
    True,
)
_add("text.onboarding.name_label", "Onboarding", "Etiqueta nombre", "Nombre *", 32)
_add("text.onboarding.name_placeholder", "Onboarding", "Placeholder nombre", "Tu nombre", 40)
_add(
    "text.onboarding.email_label",
    "Onboarding",
    "Etiqueta correo",
    "Correo electrónico *",
    40,
)
_add(
    "text.onboarding.email_placeholder",
    "Onboarding",
    "Placeholder correo",
    "correo@ejemplo.com",
    48,
)
_add(
    "text.onboarding.password_label",
    "Onboarding",
    "Etiqueta contraseña",
    "Contraseña * (mín. 6 caracteres)",
    56,
)
_add(
    "text.onboarding.password_placeholder",
    "Onboarding",
    "Placeholder contraseña",
    "Contraseña de tu cuenta NeuroMood",
    60,
)
_add(
    "text.onboarding.forgot_password",
    "Onboarding",
    "Enlace recuperar contraseña",
    "¿Olvidaste tu contraseña?",
    48,
)
_add("text.onboarding.signup_btn", "Onboarding", "Botón crear cuenta", "Crear cuenta", 32)
_add("text.onboarding.login_btn", "Onboarding", "Botón iniciar sesión", "Iniciar sesión", 32)
_add("text.onboarding.connecting_btn", "Onboarding", "Botón conectando", "Conectando...", 32)
_add(
    "text.onboarding.error_name_required",
    "Onboarding",
    "Error nombre obligatorio",
    "Completá tu nombre para crear la cuenta.",
    80,
)
_add(
    "text.onboarding.error_invalid_email",
    "Onboarding",
    "Error email inválido",
    "Ingresá un email válido.",
    80,
)
_add(
    "text.onboarding.error_short_password",
    "Onboarding",
    "Error contraseña corta",
    "La contraseña debe tener al menos 6 caracteres.",
    96,
)
_add(
    "text.onboarding.error_terms_required",
    "Onboarding",
    "Error términos no aceptados",
    "Debés aceptar los términos para continuar.",
    96,
)

# Animo
_add("text.module.animo.slider_eyebrow", "Ánimo", "Rótulo escala", "Escala emocional", 40)
_add(
    "text.module.animo.slider_title",
    "Ánimo",
    "Título escala",
    "¿Cómo te sientes hoy?",
    60,
)
_add(
    "text.module.animo.slider_subtitle",
    "Ánimo",
    "Ayuda escala",
    "Desliza para indicar tu estado.",
    80,
)
_add("text.module.animo.save_btn", "Ánimo", "Botón guardar", "Guardar registro", 32)

# Respiracion
_add(
    "text.module.respiracion.eyebrow",
    "Respiración",
    "Título del módulo oculto",
    "Respiración 4-7-8",
    44,
)
_add("text.module.respiracion.phase_inhale", "Respiración", "Chip inhalar", "Inhalá 4s", 24)
_add("text.module.respiracion.phase_hold", "Respiración", "Chip mantener", "Mantené 7s", 24)
_add("text.module.respiracion.phase_exhale", "Respiración", "Chip exhalar", "Exhalá 8s", 24)
_add("text.module.respiracion.reset_btn", "Respiración", "Botón reiniciar", "Reiniciar", 28)
_add("text.module.respiracion.start_btn", "Respiración", "Botón iniciar", "Iniciar", 28)
_add("text.module.respiracion.pause_btn", "Respiración", "Botón pausar", "Pausar", 28)
_add("text.module.respiracion.resume_btn", "Respiración", "Botón reanudar", "Reanudar", 28)
_add("text.module.respiracion.stop_btn", "Respiración", "Botón detener", "Detener", 28)
_add("text.module.respiracion.pattern_label", "Respiración", "Métrica patrón", "Patrón", 24)
_add("text.module.respiracion.chrono_label", "Respiración", "Métrica cronómetro", "Crono", 24)
_add("text.module.respiracion.cycles_label", "Respiración", "Métrica ciclos", "Ciclos", 24)
_add(
    "text.module.respiracion.ready_state",
    "Respiración",
    "Estado inicial",
    "Listo para comenzar",
    40,
)
_add("text.module.respiracion.running_state", "Respiración", "Estado en curso", "En curso", 32)
_add("text.module.respiracion.paused_state", "Respiración", "Estado pausado", "Pausado", 32)

# TCC
_add("text.module.registro.eyebrow", "TCC", "Título del módulo oculto", "Registro TCC", 40)
_add("text.module.registro.prev_btn", "TCC", "Botón anterior", "Anterior", 32)
_add("text.module.registro.next_btn", "TCC", "Botón siguiente", "Siguiente", 32)
_add("text.module.registro.save_btn", "TCC", "Botón guardar", "Guardar registro", 40)
_add("text.module.registro.situation_placeholder", "TCC", "Placeholder situación", "Escribí lo que pasó…", 80)
_add("text.module.registro.other_emotion_placeholder", "TCC", "Placeholder otra emoción", "Nombrá tu emoción…", 48)
_add(
    "text.module.registro.thought_placeholder",
    "TCC",
    "Placeholder pensamiento",
    "Escribi el pensamiento automatico",
    80,
)
_add(
    "text.module.registro.response_placeholder",
    "TCC",
    "Placeholder respuesta",
    "Escribi una respuesta alternativa",
    80,
)
_add(
    "text.module.registro.distortions_eyebrow",
    "TCC",
    "Rótulo distorsiones",
    "Posibles distorsiones detectadas",
    60,
)
_add(
    "text.module.registro.no_distortions",
    "TCC",
    "Texto sin distorsiones",
    "Ninguna detectada aún",
    48,
)
_add("text.module.registro.success_title", "TCC", "Título éxito", "Registro guardado", 48)
_add(
    "text.module.registro.success_subtitle",
    "TCC",
    "Subtítulo éxito",
    "Buen trabajo al identificar y cuestionar el pensamiento.",
    100,
)
_add("text.module.registro.tip_eyebrow", "TCC", "Rótulo tip", "Tip terapéutico", 40)

# Rutina
_add("text.module.rutina.eyebrow", "Rutina", "Rótulo progreso", "Progreso del día", 40)
_add("text.module.rutina.no_tasks_title", "Rutina", "Título sin tareas", "Sin tareas configuradas", 56)
_add(
    "text.module.rutina.no_tasks_desc",
    "Rutina",
    "Descripción sin tareas",
    "Tu rutina se va construyendo paso a paso.",
    96,
)
_add(
    "text.module.rutina.empty_title",
    "Rutina",
    "Título estado vacío",
    "Sin tareas asignadas",
    56,
)
_add(
    "text.module.rutina.empty_desc",
    "Rutina",
    "Descripción estado vacío",
    "Cuando tu terapeuta asigne una rutina, tus tareas del día aparecerán organizadas por franja.",
    128,
)
_add("text.module.rutina.section_morning", "Rutina", "Sección mañana", "Mañana", 24)
_add("text.module.rutina.section_afternoon", "Rutina", "Sección tarde", "Tarde", 24)
_add("text.module.rutina.section_night", "Rutina", "Sección noche", "Noche", 24)
_add("text.module.rutina.add_task_btn", "Rutina", "Botón agregar tarea", "+ Agregar tarea", 36)
_add("text.module.rutina.new_task_placeholder", "Rutina", "Placeholder nueva tarea", "Nueva tarea…", 48)

# Activacion
_add(
    "text.module.actividades.categories_eyebrow",
    "Activación",
    "Rótulo categorías",
    "Categorías",
    32,
)
_add(
    "text.module.actividades.categories_help",
    "Activación",
    "Ayuda categorías",
    "Elegí una familia de actividades",
    80,
)
_add("text.module.actividades.filter_all", "Activación", "Filtro todas", "Todas", 24)
_add("text.module.actividades.category_autocuidado", "Activación", "Categoría autocuidado", "Autocuidado", 32)
_add("text.module.actividades.category_fisica", "Activación", "Categoría física", "Física", 32)
_add("text.module.actividades.category_cognitiva", "Activación", "Categoría cognitiva", "Cognitiva", 32)
_add("text.module.actividades.category_placer", "Activación", "Categoría placer", "Placer", 32)
_add("text.module.actividades.category_social", "Activación", "Categoría social", "Social", 32)
_add("text.module.actividades.category_maestria", "Activación", "Categoría maestría", "Maestría", 32)
_add("text.module.actividades.empty_no_mood_title", "Activación", "Título sin ánimo", "Sin sugerencias", 48)
_add(
    "text.module.actividades.empty_no_mood_desc",
    "Activación",
    "Descripción sin ánimo",
    "Registrá tu ánimo primero para recibir sugerencias.",
    96,
)
_add(
    "text.module.actividades.empty_no_activities_desc",
    "Activación",
    "Descripción sin actividades",
    "Tu terapeuta aún no ha cargado actividades para este ánimo.",
    110,
)
_add("text.module.actividades.btn_done", "Activación", "Botón hice", "Hice", 24)
_add("text.module.actividades.btn_not_done", "Activación", "Botón no pude", "No pude", 28)
_add("text.module.actividades.btn_done_state", "Activación", "Estado hecho", "Hecho", 24)

# Timer
_add("text.module.timer.eyebrow", "Temporizador", "Título del módulo oculto", "Timer de enfoque", 40)
_add("text.module.timer.ready_state", "Temporizador", "Estado listo", "Lista para empezar", 44)
_add("text.module.timer.running_state", "Temporizador", "Estado en curso", "Sesión en curso", 40)
_add("text.module.timer.paused_state", "Temporizador", "Estado pausado", "En pausa", 24)
_add(
    "text.module.timer.empty_title",
    "Temporizador",
    "Título estado vacío",
    "Sin actividades asignadas",
    56,
)
_add(
    "text.module.timer.empty_desc",
    "Temporizador",
    "Descripción estado vacío",
    "Pedile a tu profesional que te asigne una actividad temporizada para poder empezar.",
    120,
    True,
)
_add(
    "text.module.timer.activity_placeholder",
    "Temporizador",
    "Placeholder actividad",
    "Pedile a tu profesional que te asigne una actividad",
    90,
)

# Recordatorios
_add("text.module.avisos.eyebrow", "Recordatorios", "Título del módulo oculto", "Recordatorios", 40)
_add("text.module.avisos.filter_all", "Recordatorios", "Filtro todos", "Todos", 24)
_add("text.module.avisos.filter_active", "Recordatorios", "Filtro activos", "Activos", 24)
_add("text.module.avisos.filter_today", "Recordatorios", "Filtro hoy", "Hoy", 20)
_add(
    "text.module.avisos.search_placeholder",
    "Recordatorios",
    "Placeholder búsqueda",
    "Buscar recordatorio…",
    56,
)
_add(
    "text.module.avisos.empty_title",
    "Recordatorios",
    "Título sin recordatorios",
    "Sin recordatorios asignados",
    56,
)
_add(
    "text.module.avisos.empty_desc",
    "Recordatorios",
    "Descripción sin recordatorios",
    "Tu profesional configura tus recordatorios de bienestar desde el Hub.",
    120,
    True,
)
_add(
    "text.module.avisos.empty_filter_title",
    "Recordatorios",
    "Título sin resultados",
    "Sin resultados con esos filtros",
    64,
)
_add(
    "text.module.avisos.empty_filter_desc",
    "Recordatorios",
    "Descripción sin resultados",
    "Probá cambiar los filtros.",
    80,
)
_add("text.module.avisos.complete_btn", "Recordatorios", "Botón completar", "Completar", 32)
_add("text.module.avisos.silence_eyebrow", "Recordatorios", "Rótulo silencio", "Silencio", 32)
_add("text.module.avisos.silence_label", "Recordatorios", "Etiqueta silencio", "Horario de silencio", 48)
_add("text.module.avisos.apply_btn", "Recordatorios", "Botón aplicar", "Aplicar", 28)

# DBT
_add("text.module.dbt.tab_now", "DBT", "Tab ahora", "Ahora", 24)
_add("text.module.dbt.tab_library", "DBT", "Tab biblioteca", "Biblioteca", 32)
_add("text.module.dbt.tab_history", "DBT", "Tab historial", "Historial", 32)
_add("text.module.dbt.now_prompt", "DBT", "Pregunta de entrada", "¿Qué necesitás en este momento?", 80)
_add("text.module.dbt.family_all", "DBT", "Filtro todas", "Todas", 24)
_add("text.module.dbt.family_mindfulness", "DBT", "Filtro mindfulness", "Mindfulness", 32)
_add("text.module.dbt.family_tolerance", "DBT", "Filtro tolerancia", "Tolerancia", 32)
_add("text.module.dbt.family_regulation", "DBT", "Filtro regulación", "Regulación", 32)
_add("text.module.dbt.family_effectiveness", "DBT", "Filtro efectividad", "Efectividad", 32)
_add("text.module.dbt.cancel_btn", "DBT", "Botón salir", "Salir", 24)
_add("text.module.dbt.prev_btn", "DBT", "Botón anterior", "Anterior", 32)
_add("text.module.dbt.next_btn", "DBT", "Botón siguiente", "Siguiente", 32)
_add("text.module.dbt.finish_btn", "DBT", "Botón terminar", "Terminar", 32)
_add("text.module.dbt.closure_antes", "DBT", "Pregunta malestar antes", "¿Cómo estaba tu nivel de malestar ANTES? (Opcional)", 96)
_add("text.module.dbt.closure_despues", "DBT", "Pregunta malestar ahora", "¿Cómo está tu nivel de malestar AHORA? (Opcional)", 96)
_add("text.module.dbt.closure_result", "DBT", "Pregunta utilidad", "¿Te sirvió la práctica?", 64)
_add("text.module.dbt.result_helped", "DBT", "Resultado ayudó", "Me ayudó", 32)
_add("text.module.dbt.result_partial", "DBT", "Resultado parcial", "Un poco", 32)
_add("text.module.dbt.result_no", "DBT", "Resultado no", "No esta vez", 32)
_add("text.module.dbt.result_skip", "DBT", "Resultado sin evaluar", "Prefiero no evaluar", 48)
_add("text.module.dbt.save_practice_btn", "DBT", "Botón guardar práctica", "Guardar práctica", 40)
_add("text.module.dbt.history_empty_title", "DBT", "Historial vacío título", "Sin prácticas guardadas", 48)
_add(
    "text.module.dbt.history_empty_desc",
    "DBT",
    "Historial vacío descripción",
    "Cuando completes una habilidad, va a aparecer acá.",
    80,
)


def suite_text_entries() -> tuple[SuiteTextEntry, ...]:
    return tuple(_ENTRIES)


@lru_cache(maxsize=1)
def suite_text_by_key() -> dict[str, SuiteTextEntry]:
    return {entry.key: entry for entry in suite_text_entries()}


def suite_text_sections() -> tuple[str, ...]:
    seen: list[str] = []
    for entry in suite_text_entries():
        if entry.section not in seen:
            seen.append(entry.section)
    return tuple(seen)


def iter_suite_text_entries(section: str | None = None) -> Iterable[SuiteTextEntry]:
    for entry in suite_text_entries():
        if section is None or entry.section == section:
            yield entry

