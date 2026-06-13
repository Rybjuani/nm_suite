from datetime import datetime

# Vocabulario compartido Suite↔Hub: categorías de mensajes de apoyo.
# Vive en shared/ porque lo consumen ambas apps (Avisos del Suite y el editor
# de Presets del Hub) y los bundles PyInstaller NO incluyen app/ dentro del Hub.
SUPPORT_CATEGORIES = [
    "Salud",
    "Hidratación",
    "Calma",
    "Actividad",
    "Comida",
    "Trabajo",
    "Descanso",
    "Terapia",
    "Recordatorio",
]


def fecha_hoy() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def hora_actual() -> str:
    return datetime.now().strftime("%H:%M:%S")


def fecha_legible(fecha_iso: str) -> str:
    try:
        dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
        meses = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]
        return f"{dt.day} de {meses[dt.month - 1]}"
    except ValueError:
        return fecha_iso


_GRAD_PUNTAJE = [
    "#E74C3C",
    "#E96134",
    "#EC762C",
    "#EF8C24",
    "#F0A500",
    "#EAB800",
    "#C0C030",
    "#7CBD50",
    "#3AAE70",
    "#2BBF7A",
    "#22D47E",
]


def color_por_puntaje_exacto(puntaje: int) -> str:
    return _GRAD_PUNTAJE[max(0, min(10, puntaje))]


def color_por_puntaje(
    puntaje: int, modo: str = "dark"
) -> str:  # modo ignorado — se mantiene por compatibilidad
    return color_por_puntaje_exacto(puntaje)


def get_weekly_series() -> tuple[list, list]:
    """(current_week, previous_week) — 7 floats/None cada uno."""
    from shared.visual_qa import visual_qa_enabled
    import logging

    _log = logging.getLogger(__name__)

    if visual_qa_enabled():
        return ([5, 6, 7, 8, 7, 9, 9], [4, 5, 6, 6, 7, 7, 8])
    try:
        import datetime as dt
        from shared.db import obtener_conexion

        con = obtener_conexion()
        today = dt.date.today()
        current, previous = [], []
        for offset in range(6, -1, -1):
            day = today - dt.timedelta(days=offset)
            row = con.execute(
                "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?", (str(day),)
            ).fetchone()
            current.append(float(row[0]) if row and row[0] is not None else None)
            day_prev = day - dt.timedelta(days=7)
            row2 = con.execute(
                "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?", (str(day_prev),)
            ).fetchone()
            previous.append(float(row2[0]) if row2 and row2[0] is not None else None)
        return current, previous
    except Exception:
        _log.exception("Error cargando series de ánimo")
        return [None] * 7, [None] * 7


def get_valence_series(days: int = 7) -> tuple[list, list]:
    """(positiva, negativa) — promedio diario de intensidad CRUDA por valencia.

    `days` valores/None cada una (hoy-(days-1) .. hoy). Registro pos/neg
    separado (v1.0): "tristeza 10" cuenta como registro NEGATIVO de
    intensidad 10, no como bienestar 1 — los dos lados se miden por separado.
    Los registros sin emoción (valencia neutral/'') cuentan del lado positivo:
    son un check-in de ánimo a secas (legacy: hoy la emoción es obligatoria).
    """
    from shared.visual_qa import visual_qa_enabled
    import logging

    _log = logging.getLogger(__name__)

    if visual_qa_enabled():
        base_p = [6, 7, None, 8, 7, 9, 8]
        base_n = [3, None, 5, 2, 4, None, 3]
        reps = (days + 6) // 7
        return (base_p * reps)[:days], (base_n * reps)[:days]
    try:
        import datetime as dt
        from shared.db import obtener_conexion

        con = obtener_conexion()
        today = dt.date.today()
        positiva, negativa = [], []
        for offset in range(days - 1, -1, -1):
            day = str(today - dt.timedelta(days=offset))
            row_p = con.execute(
                "SELECT AVG(COALESCE(intensidad, puntaje)) FROM termometro "
                "WHERE date(fecha)=? AND (valencia IS NULL OR valencia != 'negativa')",
                (day,),
            ).fetchone()
            positiva.append(float(row_p[0]) if row_p and row_p[0] is not None else None)
            row_n = con.execute(
                "SELECT AVG(COALESCE(intensidad, 11 - puntaje)) FROM termometro "
                "WHERE date(fecha)=? AND valencia = 'negativa'",
                (day,),
            ).fetchone()
            negativa.append(float(row_n[0]) if row_n and row_n[0] is not None else None)
        return positiva, negativa
    except Exception:
        _log.exception("Error cargando series de valencia")
        return [None] * days, [None] * days


def get_weekly_valence_series() -> tuple[list, list]:
    """(positiva, negativa) de los últimos 7 días — ver get_valence_series."""
    return get_valence_series(7)
