import os
from datetime import datetime
from shared.theme import COLORS


def fecha_hoy() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def hora_actual() -> str:
    return datetime.now().strftime("%H:%M:%S")


def fecha_legible(fecha_iso: str) -> str:
    try:
        dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"{dt.day} de {meses[dt.month - 1]}"
    except ValueError:
        return fecha_iso


_GRAD_PUNTAJE = [
    "#E74C3C", "#E96134", "#EC762C", "#EF8C24", "#F0A500",
    "#EAB800", "#C0C030", "#7CBD50", "#3AAE70", "#2BBF7A", "#22D47E",
]


def color_por_puntaje_exacto(puntaje: int) -> str:
    return _GRAD_PUNTAJE[max(0, min(10, puntaje))]


def color_por_puntaje(puntaje: int, modo: str = "dark") -> str:
    return color_por_puntaje_exacto(puntaje)


