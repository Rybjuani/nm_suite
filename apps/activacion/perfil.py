"""perfil.py — Perfil del paciente para personalización de sugerencias."""
import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

from shared.db import obtener_conexion

_DEFAULTS = {
    "metas":            "",
    "restricciones":    "",
    "horario":          "flexible",
    "cat_preferidas":   "",
    "notas_terapeuta":  "",
}


def cargar_perfil() -> dict:
    conn = obtener_conexion()
    try:
        rows = conn.execute("SELECT clave, valor FROM activacion_perfil").fetchall()
    except Exception:
        rows = []
    conn.close()
    perfil = dict(_DEFAULTS)
    for r in rows:
        if r["clave"] in perfil:
            perfil[r["clave"]] = r["valor"]
    return perfil


def guardar_perfil(datos: dict) -> None:
    conn = obtener_conexion()
    for clave, valor in datos.items():
        conn.execute(
            "INSERT OR REPLACE INTO activacion_perfil (clave, valor) VALUES (?,?)",
            (clave, str(valor))
        )
    conn.commit()
    conn.close()
