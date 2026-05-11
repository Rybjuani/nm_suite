"""plantillas.py — Plantillas clínicas de tareas para el Checklist de Rutina."""
import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

from shared.db import obtener_conexion

# (descripcion, seccion, categoria)
_SEMILLA = []


def sembrar_plantillas_si_vacio() -> None:
    conn = obtener_conexion()
    try:
        count = conn.execute("SELECT COUNT(*) FROM checklist_plantillas").fetchone()[0]
    except Exception:
        conn.close()
        return
    if count == 0:
        conn.executemany(
            "INSERT INTO checklist_plantillas "
            "(descripcion, seccion, categoria, orden, es_custom) "
            "VALUES (?,?,?,?,0)",
            [(d, s, c, i) for i, (d, s, c) in enumerate(_SEMILLA)],
        )
        conn.commit()
    conn.close()


def obtener_plantillas() -> list:
    conn = obtener_conexion()
    try:
        rows = conn.execute(
            "SELECT * FROM checklist_plantillas ORDER BY seccion, orden ASC, id ASC"
        ).fetchall()
    except Exception:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def guardar_plantilla(datos: dict) -> int:
    conn = obtener_conexion()
    if datos.get("id"):
        conn.execute(
            "UPDATE checklist_plantillas "
            "SET descripcion=?, seccion=?, categoria=? WHERE id=?",
            (datos["descripcion"], datos["seccion"], datos["categoria"],
             datos["id"])
        )
        pid = datos["id"]
    else:
        max_orden = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM checklist_plantillas"
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO checklist_plantillas "
            "(descripcion, seccion, categoria, orden, es_custom) "
            "VALUES (?,?,?,?,1)",
            (datos["descripcion"], datos["seccion"], datos["categoria"],
             max_orden)
        )
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def eliminar_plantilla(plantilla_id: int) -> None:
    conn = obtener_conexion()
    conn.execute("DELETE FROM checklist_plantillas WHERE id=?", (plantilla_id,))
    conn.commit()
    conn.close()
