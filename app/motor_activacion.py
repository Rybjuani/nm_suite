"""motor_activacion.py — Motor de sugerencias de Activación Conductual."""
from shared.db import obtener_conexion
from shared.theme import CATEGORY_COLORS

CATEGORIAS = list(CATEGORY_COLORS.keys())
CATEGORIA_COLOR = CATEGORY_COLORS

ACTIVIDADES_DEFAULT = [
    {"nombre": "Caminar 15 minutos", "categoria": "Física", "animo_min": 1, "animo_max": 5},
    {"nombre": "Escuchar música que te guste", "categoria": "Placer", "animo_min": 1, "animo_max": 6},
    {"nombre": "Ordenar un espacio pequeño", "categoria": "Maestría", "animo_min": 3, "animo_max": 7},
    {"nombre": "Llamar a alguien cercano", "categoria": "Social", "animo_min": 4, "animo_max": 8},
    {"nombre": "Respiración profunda 5 min", "categoria": "Autocuidado", "animo_min": 1, "animo_max": 4},
    {"nombre": "Leer 10 páginas", "categoria": "Cognitiva", "animo_min": 5, "animo_max": 10},
    {"nombre": "Ducharse con atención plena", "categoria": "Autocuidado", "animo_min": 2, "animo_max": 6},
    {"nombre": "Escribir 3 cosas positivas del día", "categoria": "Cognitiva", "animo_min": 3, "animo_max": 8},
    {"nombre": "Estiramientos suaves", "categoria": "Física", "animo_min": 1, "animo_max": 5},
    {"nombre": "Cocinar algo simple", "categoria": "Placer", "animo_min": 4, "animo_max": 9},
]


def sugerir_actividades(animo: int, max_results: int = 3) -> list:
    conn = obtener_conexion()
    try:
        candidatos = [
            dict(r) for r in conn.execute(
                "SELECT * FROM activacion_actividades "
                "WHERE activa=1 AND animo_min<=? AND animo_max>=? "
                "ORDER BY RANDOM() LIMIT ?",
                (animo, animo, max_results * 2),
            ).fetchall()
        ]
    except Exception:
        candidatos = []
    conn.close()

    if not candidatos:
        candidatos = [a for a in ACTIVIDADES_DEFAULT if a["animo_min"] <= animo <= a["animo_max"]]

    recientes = _obtener_recientes()
    frescos = [a for a in candidatos if a["nombre"] not in recientes]
    pool = frescos if len(frescos) >= max_results else candidatos

    return pool[:max_results]


def _obtener_recientes() -> set:
    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT actividad FROM activacion ORDER BY fecha DESC, hora DESC LIMIT 12"
        ).fetchall()
        conn.close()
        return {r[0] if isinstance(r, tuple) else r["actividad"] for r in rows}
    except Exception:
        return set()


def registrar_resultado(nombre: str, resultado: str, animo: int):
    from shared.utils import fecha_hoy, hora_actual
    conn = obtener_conexion()
    try:
        conn.execute(
            "INSERT INTO activacion (fecha, hora, actividad, resultado, animo) VALUES (?, ?, ?, ?, ?)",
            (fecha_hoy(), hora_actual(), nombre, resultado, animo),
        )
        conn.commit()
    except Exception:
        pass
    conn.close()


def obtener_ultimo_animo() -> int | None:
    from shared.utils import fecha_hoy
    conn = obtener_conexion()
    try:
        row = conn.execute(
            "SELECT puntaje FROM termometro WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
            (fecha_hoy(),)
        ).fetchone()
        conn.close()
        if row:
            return row[0] if isinstance(row, tuple) else row["puntaje"]
    except Exception:
        pass
    return None
