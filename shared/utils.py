import os
import sys
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


def color_por_puntaje(puntaje: int, modo: str = "dark") -> str:
    colores = COLORS[modo]
    if puntaje <= 3:
        return colores["error"]
    elif puntaje <= 6:
        return colores["warning"]
    else:
        return colores["accent"]


def obtener_ruta_recurso(nombre: str) -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


def configurar_matplotlib_nm(modo: str = "dark"):
    import matplotlib.pyplot as plt
    colores = COLORS[modo]
    plt.rcParams.update({
        "figure.facecolor": colores["bg_primary"],
        "axes.facecolor": colores["bg_surface"],
        "axes.edgecolor": colores["border"],
        "axes.labelcolor": colores["text_secondary"],
        "xtick.color": colores["text_tertiary"],
        "ytick.color": colores["text_tertiary"],
        "text.color": colores["text_primary"],
        "grid.color": colores["border"],
        "grid.alpha": 0.5,
        "lines.linewidth": 2,
        "font.family": ["Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
        "font.size": 10,
    })


def exportar_csv(filas: list, encabezados: list, ruta_archivo: str):
    import csv
    with open(ruta_archivo, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(encabezados)
        writer.writerows(filas)
