"""analisis.py — Estadísticas clínicas para Activación Conductual (BA)."""
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


def calcular_stats(n_dias: int = 30) -> dict:
    """
    Devuelve un dict con estadísticas de los últimos n_dias días.
    Retorna {} si no hay registros.
    """
    desde = (datetime.now() - timedelta(days=n_dias)).strftime("%Y-%m-%d")
    conn = obtener_conexion()
    registros = conn.execute(
        "SELECT fecha, animo, actividad, resultado "
        "FROM activacion WHERE fecha >= ? ORDER BY fecha ASC",
        (desde,),
    ).fetchall()
    act_cats = {
        r["nombre"]: r["categoria"]
        for r in conn.execute(
            "SELECT nombre, categoria FROM activacion_actividades"
        ).fetchall()
    }
    conn.close()

    if not registros:
        return {}

    # Ánimo promedio por día
    ap: dict[str, list] = {}
    for r in registros:
        ap.setdefault(r["fecha"], []).append(r["animo"])
    animos_promedio = {f: round(sum(v) / len(v), 1) for f, v in sorted(ap.items())}

    # Tasa global
    total = len(registros)
    hechas = sum(1 for r in registros if r["resultado"] == "hecha")

    # Cumplimiento por categoría (ordenado por frecuencia desc)
    por_cat: dict[str, dict] = {}
    for r in registros:
        cat = act_cats.get(r["actividad"], "Otra")
        por_cat.setdefault(cat, {"t": 0, "h": 0})
        por_cat[cat]["t"] += 1
        if r["resultado"] == "hecha":
            por_cat[cat]["h"] += 1
    tasa_por_cat = {
        c: round(v["h"] / v["t"] * 100) if v["t"] else 0
        for c, v in sorted(por_cat.items(), key=lambda x: -x[1]["t"])
    }

    # Correlación ánimo declarado vs. tasa de éxito
    por_a: dict[int, dict] = {}
    for r in registros:
        a = r["animo"]
        por_a.setdefault(a, {"t": 0, "h": 0})
        por_a[a]["t"] += 1
        if r["resultado"] == "hecha":
            por_a[a]["h"] += 1
    animo_vs_tasa = {
        a: round(v["h"] / v["t"] * 100) if v["t"] else 0
        for a, v in sorted(por_a.items())
    }

    return {
        "animos_promedio": animos_promedio,
        "tasa_global": round(hechas / total * 100),
        "tasa_por_cat": tasa_por_cat,
        "animo_vs_tasa": animo_vs_tasa,
        "total": total,
        "n_dias": n_dias,
    }


def generar_resumen_semanal() -> str:
    """Resumen clínico estructurado de la última semana."""
    stats = calcular_stats(7)
    if not stats or stats.get("total", 0) == 0:
        return "Sin datos suficientes para el resumen."

    total = stats["total"]
    tasa = stats["tasa_global"]
    vals = list(stats["animos_promedio"].values())
    prom_a = round(sum(vals) / len(vals), 1) if vals else 0

    if len(vals) >= 2:
        delta = vals[-1] - vals[0]
        tend = "ascendente" if delta > 0.8 else ("descendente" if delta < -0.8 else "estable")
    else:
        tend = "en evaluación"

    lineas = [
        f"Actividades registradas: {total}",
        f"Tasa de cumplimiento: {tasa}%",
        f"Ánimo promedio: {prom_a}/10  ·  Tendencia: {tend}",
    ]
    if stats["tasa_por_cat"]:
        mejor = max(stats["tasa_por_cat"], key=stats["tasa_por_cat"].get)
        lineas.append(f"Mejor respuesta: {mejor} ({stats['tasa_por_cat'][mejor]}%)")

    return "\n".join(lineas)
