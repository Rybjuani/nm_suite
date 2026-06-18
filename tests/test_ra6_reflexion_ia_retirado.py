"""RA-6: retirar reflexion_ia del contrato activo (sync + Hub SELECT).

El módulo TCC actual NO captura `reflexion_ia` (no hay widget en
registro_tcc_qt._guardar que la escriba). Antes de RA-6, el plumbing
completo la transportaba como dato real siempre vacío:
  - shared/sync.py:_exportar_pensamientos la SELECTaba y la enviaba a
    Supabase thought_records.reflexion_ia (siempre "").
  - hub/pacientes_qt._fetch_patient_data la pedía a Supabase.

RA-6 la retira de ambos. La columna física se conserva en SQLite (ALTER
en shared/db.py) y en Supabase (CREATE TABLE en db/supabase_schema.sql)
por compatibilidad con datos históricos — no se hace rollback SQL.
"""
from __future__ import annotations

import re
from unittest.mock import MagicMock


# ─── Test del Hub: captura en ejecución del .select(columns) real ────────


def test_fetch_patient_data_no_pide_reflexion_ia(qapp, isolated_db):
    """RA-6: _fetch_patient_data (hub/pacientes_qt.py) no debe pedir
    reflexion_ia a thought_records.

    Captura en ejecución el argumento real que se le pasa a .select(columns)
    cuando se llama a _fetch("tcc", "thought_records", ...). No usa regex
    sobre el código fuente — usa un mock que registra el call real.
    """
    from hub.pacientes_qt import DetallePacienteView

    # Mock del cliente Supabase que registra cada .select(columns)
    sb = _RecordingSB()
    # thought_records debe devolver al menos 1 fila para que el fetch no
    # sea no-op (aunque el test solo mira el argumento de select, igual)
    sb.set_rows("thought_records", [{"fecha": "2026-06-18", "hora": "12:00"}])

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = sb
    view._pid = "test-pid-123"
    view._nombre = "Test"

    view._fetch_patient_data()

    # Buscar la llamada a .select() para thought_records
    tcc_select = sb.select_calls.get("thought_records")
    assert tcc_select is not None, (
        "No se capturó ninguna llamada a .select() para thought_records. "
        "¿Se rompió el S0-1?"
    )
    assert "reflexion_ia" not in tcc_select, (
        f"_fetch_patient_data pasó {tcc_select!r} a .select() para "
        f"thought_records — todavía incluye reflexion_ia. "
        "RA-6 requiere retirarla."
    )


# ─── Test de _exportar_pensamientos con SQLite temporal + Supabase falso ──


def test_exportar_pensamientos_no_envia_reflexion_ia(qapp, isolated_db):
    """RA-6: _exportar_pensamientos (shared/sync.py) no debe incluir
    reflexion_ia en el payload que envía a Supabase.

    Puebla `pensamientos` en SQLite temporal con un registro real (que
    incluye reflexion_ia='' porque la columna existe en el schema), llama
    a _exportar_pensamientos con un Supabase falso que captura el payload
    del .upsert(), y verifica que el payload no contiene la key
    reflexion_ia.
    """
    from shared.db import conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.sync import _exportar_pensamientos

    # Poblar pensamientos con un registro real (la columna reflexion_ia
    # existe en el schema SQLite vía ALTER, pero el módulo TCC nunca la
    # escribe — queda con el default '')
    with conexion() as conn:
        conn.execute(
            "INSERT INTO pensamientos "
            "(fecha, hora, situacion, emocion, intensidad, pensamiento, "
            "respuesta_alternativa, distorsiones) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fecha_hoy(), hora_actual(), "test situacion", "Ansiedad",
             7, "test pensamiento", "test respuesta", "catastrofizacion"),
        )

    # Supabase falso que captura el payload del upsert a thought_records
    sb = _RecordingSB()

    _exportar_pensamientos(sb, patient_id="test-pid-123", desde="2020-01-01")

    # Verificar que se llamó upsert sobre thought_records
    upsert_calls = sb.upsert_calls.get("thought_records", [])
    assert len(upsert_calls) == 1, (
        f"Esperado 1 upsert a thought_records, got {len(upsert_calls)}. "
        "¿_exportar_pensamientos no encontró registros en pensamientos?"
    )
    payload, on_conflict = upsert_calls[0]
    assert len(payload) == 1, (
        f"Esperado 1 item en payload, got {len(payload)}"
    )
    item = payload[0]
    assert "reflexion_ia" not in item, (
        f"Payload a Supabase incluye reflexion_ia: {item!r}. "
        "RA-6 requiere retirarla del contrato activo."
    )
    # Verificar que los campos reales sí están
    for expected_key in ("patient_id", "fecha", "hora", "situacion",
                          "emocion", "intensidad", "pensamiento",
                          "respuesta_alternativa", "distorsiones"):
        assert expected_key in item, (
            f"Payload no incluye {expected_key!r}: {item!r}"
        )


# ─── Tests de no-regresión: columna física se conserva ──────────────────


def test_columna_fisica_se_conserva_en_sqlite():
    """RA-6 (no-regresión): la columna reflexion_ia se conserva en el schema
    SQLite (ALTER en shared/db.py) por compatibilidad con datos históricos.
    No se hace rollback SQL."""
    with open("shared/db.py", encoding="utf-8") as f:
        src = f.read()
    # El ALTER TABLE que agrega reflexion_ia debe seguir presente
    assert '("reflexion_ia", "TEXT DEFAULT \'\'")' in src, (
        "El ALTER TABLE que agrega reflexion_ia fue eliminado de shared/db.py. "
        "RA-6 requiere conservar la columna física por compatibilidad."
    )


def test_columna_fisica_se_conserva_en_supabase():
    """RA-6 (no-regresión): la columna reflexion_ia se conserva en el schema
    Supabase (db/supabase_schema.sql) por compatibilidad. No se hace
    rollback SQL — decisión owner."""
    with open("db/supabase_schema.sql", encoding="utf-8") as f:
        src = f.read()
    # La columna en thought_records debe seguir presente
    assert re.search(r'reflexion_ia\s+TEXT', src), (
        "La columna reflexion_ia fue eliminada de db/supabase_schema.sql. "
        "RA-6 requiere conservarla (no rollback SQL)."
    )


# ─── Helpers: mock de cliente Supabase que registra calls reales ────────


class _RecordingSB:
    """Mock mínimo de cliente Supabase que registra:
    - .table(name).select(columns) → guarda columns en select_calls[name]
    - .table(name).upsert(payload, on_conflict=...) → guarda (payload, on_conflict)
      en upsert_calls[name]

    Soporta la cadena fluida .table().select().eq().order().limit().execute()
    y .table().upsert().execute() que usa shared/sync.py y hub/pacientes_qt.py.
    """

    def __init__(self):
        self.select_calls: dict[str, str] = {}
        self.upsert_calls: dict[str, list[tuple[list, str | None]]] = {}
        self._rows: dict[str, list[dict]] = {}

    def set_rows(self, table: str, rows: list[dict]) -> None:
        """Define qué datos devolver cuando se hace select().execute() sobre table."""
        self._rows[table] = rows

    def table(self, name: str) -> "_RecordingQuery":
        return _RecordingQuery(self, name)


class _RecordingQuery:
    def __init__(self, parent: "_RecordingSB", table: str):
        self._parent = parent
        self._table = table
        self._columns: str | None = None

    def select(self, columns: str) -> "_RecordingQuery":
        self._columns = columns
        self._parent.select_calls[self._table] = columns
        return self

    def eq(self, *_args, **_kwargs) -> "_RecordingQuery":
        return self

    def order(self, *_args, **_kwargs) -> "_RecordingQuery":
        return self

    def limit(self, *_args, **_kwargs) -> "_RecordingQuery":
        return self

    def execute(self):
        # Devolver un objeto con .data (lo que espera el código real)
        result = MagicMock()
        result.data = self._parent._rows.get(self._table, [])
        return result

    def upsert(self, payload: list, on_conflict: str | None = None) -> "_RecordingQuery":
        self._parent.upsert_calls.setdefault(self._table, []).append(
            (payload, on_conflict)
        )
        return self
