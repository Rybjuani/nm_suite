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


def get_mood_series(days: int = 7) -> list:
    """Serie diaria de ánimo: promedio de ``puntaje`` por día (UN punto por día),
    últimos ``days`` días (hoy-(days-1) .. hoy). ``None`` donde no hubo registro.

    Fuente y fórmula ÚNICAS del ánimo (sin separar valencia positiva/negativa):
    el mismo ``AVG(puntaje)`` por día que usan el score del Home
    (``_get_module_status``) y el módulo Ánimo. Garantiza que un mismo día dé el
    mismo valor en Suite Home, módulo Ánimo y Hub.
    """
    from shared.visual_qa import visual_qa_enabled
    import logging

    _log = logging.getLogger(__name__)

    if visual_qa_enabled():
        base = [6, 7, 5, 8, 7, 9, 8]
        reps = (days + 6) // 7
        return (base * reps)[:days]
    try:
        import datetime as dt
        from shared.db import obtener_conexion

        con = obtener_conexion()
        today = dt.date.today()
        serie: list = []
        for offset in range(days - 1, -1, -1):
            day = str(today - dt.timedelta(days=offset))
            row = con.execute(
                "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?", (day,)
            ).fetchone()
            serie.append(float(row[0]) if row and row[0] is not None else None)
        con.close()
        return serie
    except Exception:
        _log.exception("Error cargando serie de ánimo")
        return [None] * days
