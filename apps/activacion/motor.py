"""motor.py — Motor de sugerencias de Activación Conductual (BA)."""
import sys
import os
from datetime import datetime, timedelta

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

from shared.db import obtener_conexion

# (nombre, descripción, categoría, dificultad 1-3, duracion_min, beneficio, animo_min, animo_max)
_SEMILLA = []

ACTIVIDADES_SEMILLA = [
    {
        "nombre": n, "descripcion": d, "categoria": c,
        "dificultad": f, "duracion_min": dm, "beneficio": b,
        "animo_min": em, "animo_max": ex,
    }
    for n, d, c, f, dm, b, em, ex in _SEMILLA
]

CATEGORIAS = ["Autocuidado", "Cognitiva", "Física", "Placer", "Rutina", "Social", "Maestría"]

DIFICULTAD_LABEL = {1: "Baja", 2: "Media", 3: "Alta"}
CATEGORIA_COLOR_DARK = {
    "Autocuidado": "#1EC8D4",
    "Cognitiva":   "#9B8FE8",
    "Física":      "#22D47E",
    "Placer":      "#F0A500",
    "Rutina":      "#8BA4BE",
    "Social":      "#E8505B",
    "Maestría":    "#4A9EE8",
}
CATEGORIA_COLOR_LIGHT = {
    "Autocuidado": "#4A7EA5",
    "Cognitiva":   "#7B6FC8",
    "Física":      "#5A9E82",
    "Placer":      "#C87C40",
    "Rutina":      "#6B6B6B",
    "Social":      "#D46868",
    "Maestría":    "#3A7EA0",
}


def sembrar_actividades_si_vacio() -> None:
    conn = obtener_conexion()
    try:
        count = conn.execute("SELECT COUNT(*) FROM activacion_actividades").fetchone()[0]
    except Exception:
        conn.close()
        return
    if count == 0:
        conn.executemany(
            "INSERT INTO activacion_actividades "
            "(nombre, descripcion, categoria, dificultad, duracion_min, beneficio, animo_min, animo_max, activa, es_custom) "
            "VALUES (?,?,?,?,?,?,?,?,1,0)",
            [(a["nombre"], a["descripcion"], a["categoria"], a["dificultad"],
              a["duracion_min"], a["beneficio"], a["animo_min"], a["animo_max"])
             for a in ACTIVIDADES_SEMILLA],
        )
        conn.commit()
    conn.close()


def sugerir_actividades(animo: int, perfil: dict = None) -> list:
    """
    Devuelve hasta 6 dicts de actividades filtradas por rango de ánimo,
    ordenadas de menor a mayor dificultad, evitando repetición reciente.
    Si se pasa perfil, las categorías preferidas se priorizan.
    """
    conn = obtener_conexion()
    recientes_rows = conn.execute(
        "SELECT actividad FROM activacion ORDER BY fecha DESC, hora DESC LIMIT 18"
    ).fetchall()
    recientes = {r["actividad"] for r in recientes_rows}

    candidatos = [
        dict(r) for r in conn.execute(
            "SELECT * FROM activacion_actividades "
            "WHERE activa=1 AND animo_min<=? AND animo_max>=? "
            "ORDER BY dificultad ASC",
            (animo, animo),
        ).fetchall()
    ]
    conn.close()

    frescos = [a for a in candidatos if a["nombre"] not in recientes]
    pool = frescos if len(frescos) >= 4 else candidatos

    if perfil:
        cats_pref = {c.strip() for c in perfil.get("cat_preferidas", "").split(",") if c.strip()}
        if cats_pref:
            pref  = [a for a in pool if a.get("categoria") in cats_pref]
            otros = [a for a in pool if a.get("categoria") not in cats_pref]
            pool  = pref + otros

    return pool[:6]


_CAT_CHECKLIST = {
    "Autocuidado": "Autocuidado",
    "Placer":      "Placer",
    "Social":      "Social",
    "Cognitiva":   "Logro",
    "Física":      "Logro",
    "Rutina":      "Logro",
    "Maestría":    "Logro",
}


def agregar_a_checklist(animo: int, max_total: int = 3) -> int:
    """
    Sugiere actividades según el ánimo registrado en el termómetro
    y las agrega automáticamente a checklist_tareas con origen='activacion'.
    Evita duplicar actividades ya presentes. Retorna la cantidad agregada.
    """
    candidatos = sugerir_actividades(animo)
    if not candidatos:
        return 0

    conn = obtener_conexion()
    existentes = {
        r[0] for r in conn.execute("SELECT descripcion FROM checklist_tareas").fetchall()
    }

    secciones = ["manana", "tarde", "noche"]
    agregadas = 0

    for i, act in enumerate(candidatos[:max_total]):
        desc = act["nombre"]
        if desc in existentes:
            continue
        seccion = secciones[i % len(secciones)]
        max_orden = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) as m FROM checklist_tareas WHERE seccion = ?",
            (seccion,)
        ).fetchone()[0]
        cat = _CAT_CHECKLIST.get(act.get("categoria", ""), "Logro")
        try:
            conn.execute(
                "INSERT INTO checklist_tareas "
                "(seccion, descripcion, orden, categoria, dificultad, origen) "
                "VALUES (?, ?, ?, ?, ?, 'activacion')",
                (seccion, desc, max_orden + 1, cat, act["dificultad"])
            )
            agregadas += 1
        except Exception:
            pass

    conn.commit()
    conn.close()
    return agregadas


def generar_insight(animo_actual: int) -> str | None:
    """
    Devuelve un insight contextual breve si hay ≥3 registros en los últimos 7 días.
    Retorna None cuando no hay suficiente historial.
    """
    desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    conn = obtener_conexion()
    registros = conn.execute(
        "SELECT animo, resultado FROM activacion WHERE fecha >= ? ORDER BY fecha DESC",
        (desde,),
    ).fetchall()
    conn.close()

    if len(registros) < 3:
        return None

    animos = [r["animo"] for r in registros]
    prom = round(sum(animos) / len(animos), 1)
    total = len(registros)
    hechas = sum(1 for r in registros if r["resultado"] == "hecha")
    tasa = round(hechas / total * 100)

    dif = animo_actual - prom
    if dif > 1.5:
        estado = f"por encima de tu promedio de {prom}"
    elif dif < -1.5:
        estado = f"por debajo de tu promedio de {prom}"
    else:
        estado = f"en línea con tu promedio de {prom}"

    if tasa >= 65:
        tasa_txt = f"Cumplimiento: {tasa}%."
    elif tasa >= 35:
        tasa_txt = f"Cumplimiento: {tasa}%. Hay margen para crecer."
    else:
        tasa_txt = f"Cumplimiento: {tasa}%. Hoy priorizamos opciones de bajo costo."

    return f"Ánimo promedio (7 días): {prom}. Hoy estás {estado}. {tasa_txt}"
