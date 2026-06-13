"""Local-only visual QA fixtures for mockup fidelity screenshots.

This module is deliberately opt-in through environment variables. It gives the
Qt UI stable data for screenshots without touching DB, sync, auth, config, or
Supabase state.
"""

from __future__ import annotations

import os


_TRUE_VALUES = {"1", "true", "yes", "on", "visual", "demo", "qa"}


def visual_qa_enabled() -> bool:
    """Return True only for explicit local visual QA/demo runs."""
    for key in ("NM_VISUAL_QA", "NM_DEMO_VISUAL", "NM_QA_VISUAL", "NM_VISUAL_QA_DEMO"):
        if os.environ.get(key, "").strip().lower() in _TRUE_VALUES:
            return True
    return False


def qa_patient_name() -> str:
    return os.environ.get("NM_VISUAL_QA_NAME", "juan cruz").strip() or "juan cruz"


def module_status(module_id: str) -> str:
    return {
        "animo": "10/10",  # score del día (mismo formato real "N/10"): ejercita el hero filled
        "respiracion": "Activo",
        "registro": "En progreso",
        "rutina": "Completo",
        "actividades": "3 hoy",
        "timer": "45 min hoy",
        "avisos": "2/5 listos",
    }.get(module_id, "")


def last_mood() -> int:
    return 6


def activity_suggestions() -> list[dict]:
    return [
        {
            "nombre": "Caminata 20 min",
            "descripcion": "Salir a caminar activa el sistema nervioso y mejora el estado de ánimo de manera significativa.",
            "categoria": "Fisica",
        },
        {
            "nombre": "Escuchar música",
            "descripcion": "Arma una playlist de canciones que te gusten. El placer musical activa circuitos de recompensa.",
            "categoria": "Placer",
        },
        {
            "nombre": "Llamar a alguien",
            "descripcion": "El contacto social, aunque breve, reduce el aislamiento percibido.",
            "categoria": "Social",
            "done": True,
        },
        {
            "nombre": "Diario de 5 min",
            "descripcion": "Escribe 3 cosas que funcionaron hoy, aunque sean pequeñas.",
            "categoria": "Maestria",
        },
    ]


def routine_sections() -> dict[str, list[dict]]:
    return {
        "manana": [
            {"id": 9101, "descripcion": "Meditación 10 min", "done": True},
            {"id": 9102, "descripcion": "Desayuno saludable", "done": True},
            {"id": 9103, "descripcion": "Revisión de agenda", "done": True},
        ],
        "tarde": [
            {"id": 9201, "descripcion": "Almuerzo", "done": True},
            {"id": 9202, "descripcion": "Respiración 5 min", "done": True},
            {"id": 9203, "descripcion": "Caminata", "done": True},
            {"id": 9204, "descripcion": "Registro de ánimo", "done": False},
            {"id": 9205, "descripcion": "Lectura 15 min", "done": False, "origen": "manual"},
        ],
        "noche": [
            {"id": 9301, "descripcion": "Bajar luces y pantallas", "done": False},
            {"id": 9302, "descripcion": "Preparar descanso", "done": False, "origen": "manual"},
        ],
    }


def reminder_rows() -> list[dict]:
    return [
        {
            "id": 8101,
            "hora": "08:00",
            "mensaje": "Medicación matutina",
            "dias": "1,2,3,4,5",
            "activo": 1,
            "done": True,
        },
        {
            "id": 8102,
            "hora": "10:30",
            "mensaje": "Respiración 5 min",
            "dias": "1,2,3,4,5,6,7",
            "activo": 1,
            "done": True,
        },
        {
            "id": 8103,
            "hora": "14:00",
            "mensaje": "Registro de ánimo",
            "dias": "1,2,3,4,5,6,7",
            "activo": 1,
            "done": False,
        },
        {
            "id": 8104,
            "hora": "18:00",
            "mensaje": "Rutina de tarde",
            "dias": "1,2,3,4,5",
            "activo": 1,
            "done": False,
        },
        {
            "id": 8105,
            "hora": "21:00",
            "mensaje": "Técnica de relajación",
            "dias": "1,2,3,4,5,6,7",
            "activo": 1,
            "done": False,
        },
    ]


def timer_sessions() -> list[str]:
    return [
        "Lectura - 25 min",
        "Emails - 10 min",
        "Código - 45 min",
    ]


def hub_patients() -> list[dict]:
    return [
        {
            "patient_id": "qa-am-001",
            "email": "ana.martinez@ejemplo.com",
            "patient_name": "Ana Martínez",
            "last_mood": 7.2,
            "adherence": 0.75,
            "last_session": "hace 2 días",
        },
        {
            "patient_id": "qa-jr-002",
            "email": "juanr@ejemplo.com",
            "patient_name": "Juan Rodríguez",
            "last_mood": 5.8,
            "adherence": 0.50,
            "last_session": "hace 5 días",
        },
        {
            "patient_id": "qa-cl-003",
            "email": "carmen.lopez@ejemplo.com",
            "patient_name": "Carmen López",
            "last_mood": 8.1,
            "adherence": 0.88,
            "last_session": "ayer",
        },
        {
            "patient_id": "qa-ps-004",
            "email": "pedrosanchez@ejemplo.com",
            "patient_name": "Pedro Sánchez",
            "last_mood": 6.5,
            "adherence": 0.62,
            "last_session": "hace 3 días",
        },
        {
            "patient_id": "qa-lg-005",
            "email": "lauragomez@ejemplo.com",
            "patient_name": "Laura Gómez",
            "last_mood": 8.8,
            "adherence": 0.94,
            "last_session": "hoy",
        },
    ]


def hub_module_metrics() -> list[tuple[str, float]]:
    return [
        ("Guía de Respiración Animada", 0.73),
        ("Termómetro Emocional", 0.86),
        ("Registro de Pensamientos (TCC)", 0.50),
        ("Checklist de Rutina Diaria", 0.64),
        ("Asistente de Activación Conductual", 0.58),
        ("Temporizador de Actividades", 0.42),
        ("Recordatorios de Bienestar", 0.69),
    ]
