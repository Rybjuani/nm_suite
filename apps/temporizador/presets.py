"""presets.py — Presets terapéuticos para el Temporizador de Actividades."""
import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

from shared.db import obtener_conexion

# (nombre, descripcion, categoria, duracion_seg)
_SEMILLA = []


def sembrar_presets_si_vacio() -> None:
    conn = obtener_conexion()
    try:
        count = conn.execute("SELECT COUNT(*) FROM timer_presets").fetchone()[0]
    except Exception:
        conn.close()
        return
    if count == 0:
        conn.executemany(
            "INSERT INTO timer_presets (nombre, descripcion, categoria, duracion_seg, orden, es_custom) "
            "VALUES (?,?,?,?,?,0)",
            [(n, d, c, s, i) for i, (n, d, c, s) in enumerate(_SEMILLA)],
        )
        conn.commit()
    conn.close()


def obtener_presets() -> list:
    conn = obtener_conexion()
    try:
        rows = conn.execute(
            "SELECT * FROM timer_presets ORDER BY orden ASC, id ASC"
        ).fetchall()
    except Exception:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def guardar_preset(datos: dict) -> int:
    conn = obtener_conexion()
    if datos.get("id"):
        conn.execute(
            "UPDATE timer_presets SET nombre=?, descripcion=?, categoria=?, duracion_seg=? WHERE id=?",
            (datos["nombre"], datos["descripcion"], datos["categoria"], datos["duracion_seg"], datos["id"])
        )
        pid = datos["id"]
    else:
        max_orden = conn.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM timer_presets").fetchone()[0]
        cur = conn.execute(
            "INSERT INTO timer_presets (nombre, descripcion, categoria, duracion_seg, orden, es_custom) "
            "VALUES (?,?,?,?,?,1)",
            (datos["nombre"], datos["descripcion"], datos["categoria"], datos["duracion_seg"], max_orden)
        )
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def eliminar_preset(preset_id: int) -> None:
    conn = obtener_conexion()
    conn.execute("DELETE FROM timer_presets WHERE id=?", (preset_id,))
    conn.commit()
    conn.close()
