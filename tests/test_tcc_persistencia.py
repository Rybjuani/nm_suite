"""Fase 11 — guardado REAL del Registro TCC (QA desactivado, SQLite temporal).

El modo QA visual salta deliberadamente el INSERT (sólo muestra la página de
éxito), así que el guardado real quedaba sin cubrir por la evidencia de capturas.
Estos tests ejercitan ``_persistir_pensamiento`` — el seam que ``_guardar`` usa
cuando QA está OFF — contra una SQLite temporal aislada vía ``APPDATA``, de modo
que NUNCA tocan el ``nm_data.db`` real. Cubren persistencia, el constraint de
intensidad y el manejo de errores (que ``_guardar`` traduce en toast).
"""

import sqlite3
import contextlib

import pytest


@pytest.fixture
def db_temporal(tmp_path, monkeypatch):
    """Aísla la base a un APPDATA temporal y crea el esquema.

    ``obtener_ruta_db`` lee ``APPDATA`` en cada llamada, así que redirigirlo a
    ``tmp_path`` garantiza que el ``nm_data.db`` real quede intacto.
    """
    appdata = tmp_path / "appdata"
    appdata.mkdir()
    monkeypatch.setenv("APPDATA", str(appdata))
    from shared import db

    db.inicializar_tablas()
    ruta = db.obtener_ruta_db()
    assert str(tmp_path) in str(ruta)  # aislamiento confirmado
    return ruta


def _registro(**over):
    base = {
        "situacion": "Discusión con un compañero sobre plazos.",
        "emocion": "Ansiedad",
        "pensamiento": "Nunca voy a cumplir; siempre fallo.",
        "respuesta": "He cumplido antes; puedo pedir ayuda.",
        "distorsiones": "Catastrofización",
    }
    base.update(over)
    return base


def test_qa_desactivado_en_tests():
    """El conftest limpia NM_VISUAL_QA → el guardado real es el camino activo."""
    from shared.visual_qa import visual_qa_enabled

    assert visual_qa_enabled() is False


def test_persistencia_real(db_temporal):
    """El guardado real inserta y commitea una fila legible en `pensamientos`."""
    from app.modules import registro_tcc_qt as tcc
    from shared import db

    tcc._persistir_pensamiento(_registro(), 7)

    conn = db.obtener_conexion()
    rows = conn.execute(
        "SELECT situacion, emocion, intensidad, pensamiento, "
        "respuesta_alternativa, distorsiones FROM pensamientos"
    ).fetchall()
    conn.close()

    assert len(rows) == 1
    r = rows[0]
    assert r["situacion"] == "Discusión con un compañero sobre plazos."
    assert r["emocion"] == "Ansiedad"
    assert r["intensidad"] == 7
    assert r["pensamiento"].startswith("Nunca voy")
    assert r["respuesta_alternativa"].startswith("He cumplido")
    assert r["distorsiones"] == "Catastrofización"


def test_intensidad_default_5_persiste(db_temporal):
    """El default de intensidad (5, cuando el usuario no movió el heatbar)
    satisface el CHECK(0..10) y persiste."""
    from app.modules import registro_tcc_qt as tcc
    from shared import db

    tcc._persistir_pensamiento(_registro(), 5)

    conn = db.obtener_conexion()
    val = conn.execute("SELECT intensidad FROM pensamientos").fetchone()["intensidad"]
    conn.close()
    assert val == 5


def test_intensidad_constraint_rollback(db_temporal):
    """intensidad fuera de 0..10 viola el CHECK → IntegrityError y rollback:
    nada queda persistido. Ejercita el manejo de errores que `_guardar` traduce
    en toast (no un crash silencioso)."""
    from app.modules import registro_tcc_qt as tcc
    from shared import db

    with pytest.raises(sqlite3.IntegrityError):
        tcc._persistir_pensamiento(_registro(), 99)

    conn = db.obtener_conexion()
    n = conn.execute("SELECT COUNT(*) AS n FROM pensamientos").fetchone()["n"]
    conn.close()
    assert n == 0


def test_error_db_propaga(db_temporal, monkeypatch):
    """Un fallo de conexión se propaga (no se traga en silencio): `_guardar` lo
    captura para mostrar el toast de error."""
    from app.modules import registro_tcc_qt as tcc

    @contextlib.contextmanager
    def _conexion_rota():
        raise sqlite3.OperationalError("disk I/O error")
        yield  # pragma: no cover

    monkeypatch.setattr(tcc, "conexion", _conexion_rota)
    with pytest.raises(sqlite3.OperationalError):
        tcc._persistir_pensamiento(_registro(), 5)


def test_nm_data_db_no_tocado(db_temporal, tmp_path):
    """El guardado real escribe SOLO en la SQLite temporal bajo tmp_path."""
    from app.modules import registro_tcc_qt as tcc

    tcc._persistir_pensamiento(_registro(), 4)
    db_file = tmp_path / "appdata" / "NeuroMood" / "nm_data.db"
    assert db_file.exists()
