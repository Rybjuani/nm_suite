"""RB-3: telemetría de avisos invisible en el Hub.

El handoff reportaba que la Suite exporta ``recordatorios_log`` a
``reminder_logs`` (vía ``shared/sync._exportar_recordatorios_log``) pero
el Hub nunca consultaba esa tabla — solo leía ``assigned_reminders``
(la programación del profesional, no los avisos efectivamente disparados
al paciente).

RB-3 agrega el fetch de ``reminder_logs`` en
``hub/pacientes_qt._fetch_patient_data`` bajo una key nueva y explícita
(``avisos_disparados``), seleccionando solo columnas reales del schema
Supabase (``db/supabase_schema.sql:82-90``):

    reminder_logs (
        id          BIGSERIAL PRIMARY KEY,
        patient_id  TEXT NOT NULL REFERENCES patients(patient_id),
        fecha       TEXT NOT NULL,
        hora        TEXT NOT NULL,
        mensaje     TEXT NOT NULL,
        cerrado     BOOLEAN DEFAULT FALSE
    )

Columnas seleccionadas para el Hub: ``fecha, hora, mensaje, cerrado`` (las
4 telemétricamente útiles — ``id`` y ``patient_id`` son redundantes en el
dict). Limit 50, orden ``fecha DESC`` (más recientes primero).

Estos tests son de ejecución: capturan la cadena Supabase real mediante
un mock que registra select/eq/order/limit por tabla. Reutilizan el patrón
de ``test_rc3_limit_assigned_reminders.py``.
"""
from __future__ import annotations


# ─── Mock de Supabase que captura args reales de la cadena fluida ────────────


class _RecordingQuery:
    """Registra los argumentos de cada paso de la cadena fluida para una tabla.

    Soporta .select(columns).eq(col, val).gte(col, val).order(col, desc=)
    .limit(n).execute(), que es la forma usada por _fetch_patient_data.
    """

    def __init__(self, parent: "_RecordingSB", table: str):
        self._parent = parent
        self._table = table

    def select(self, columns: str) -> "_RecordingQuery":
        self._parent.select_calls[self._table] = columns
        return self

    def eq(self, column: str, value) -> "_RecordingQuery":
        self._parent.eq_calls.setdefault(self._table, []).append((column, value))
        return self

    def gte(self, column: str, value) -> "_RecordingQuery":
        self._parent.gte_calls.setdefault(self._table, []).append((column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "_RecordingQuery":
        self._parent.order_calls[self._table] = (column, desc)
        return self

    def limit(self, n: int) -> "_RecordingQuery":
        self._parent.limit_calls[self._table] = n
        return self

    def execute(self):
        class _Result:
            pass

        r = _Result()
        r.data = self._parent._rows.get(self._table, [])
        return r


class _RecordingSB:
    """Mock mínimo de cliente Supabase que captura args por tabla."""

    def __init__(self):
        self.select_calls: dict[str, str] = {}
        self.eq_calls: dict[str, list[tuple[str, object]]] = {}
        self.gte_calls: dict[str, list[tuple[str, object]]] = {}
        self.order_calls: dict[str, tuple[str, bool]] = {}
        self.limit_calls: dict[str, int] = {}
        self._rows: dict[str, list[dict]] = {
            "reminder_logs": [
                {"fecha": "2026-06-18", "hora": "09:00",
                 "mensaje": "Tomar medicina", "cerrado": True},
            ],
        }

    def table(self, name: str) -> _RecordingQuery:
        return _RecordingQuery(self, name)


def _make_view(sb):
    """Construye DetallePacienteView sin llamar __init__ (evita Qt pesado)."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = sb
    view._pid = "test-pid-123"
    view._nombre = "Test"
    return view


# ─── Tests RB-3 ──────────────────────────────────────────────────────────────


def test_fetch_patient_data_consulta_reminder_logs(qapp):
    """RB-3: _fetch_patient_data consulta la tabla reminder_logs.

    Antes de RB-3 solo consultaba assigned_reminders; los avisos
    efectivamente disparados al paciente no llegaban al Hub.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    assert "reminder_logs" in sb.select_calls, (
        "No se consultó reminder_logs. RB-3 exige que el Hub traiga la "
        "telemetría de avisos disparados al paciente."
    )


def test_fetch_patient_data_avisos_disparados_selecciona_columnas_reales(qapp):
    """RB-3: el select de reminder_logs pide solo columnas reales del schema.

    Schema (db/supabase_schema.sql:82-90): id, patient_id, fecha, hora,
    mensaje, cerrado. El Hub solo necesita las 4 telemétricas — id y
    patient_id son redundantes en el dict (ya se conoce el pid).
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    columns = sb.select_calls.get("reminder_logs", "")
    assert columns == "fecha,hora,mensaje,cerrado", (
        f"Select de reminder_logs con columnas inesperadas: {columns!r}. "
        "RB-3 exige 'fecha,hora,mensaje,cerrado' (verificadas en schema)."
    )
    # Garantía negativa: no pedir columnas que no existen en el schema
    for forbidden in ("rec_id", "timestamp", "created_at", "notas", "user_id"):
        assert forbidden not in columns, (
            f"Select de reminder_logs pide columna inexistente {forbidden!r}: "
            f"{columns!r}. Verificar schema Supabase."
        )


def test_fetch_patient_data_avisos_disparados_filtra_por_patient_id(qapp):
    """RB-3: el fetch de reminder_logs filtra por patient_id del paciente
    actual — no trae avisos disparados a otros pacientes.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    eq = sb.eq_calls.get("reminder_logs", [])
    assert ("patient_id", "test-pid-123") in eq, (
        f"reminder_logs no se filtra por patient_id correctamente: {eq!r}"
    )


def test_fetch_patient_data_avisos_disparados_tiene_limite_50(qapp):
    """RB-3: el fetch de reminder_logs aplica .limit(50) — consistente
    con assigned_reminders (RC-3). Sin límite, PostgREST devolvería todo
    el histórico de avisos del paciente.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    assert "reminder_logs" in sb.limit_calls, (
        "El fetch de reminder_logs no aplica .limit(). "
        "RB-3 exige un límite explícito."
    )
    assert sb.limit_calls["reminder_logs"] == 50, (
        f"Límite de reminder_logs alterado: esperado 50, "
        f"obtenido {sb.limit_calls['reminder_logs']!r}."
    )


def test_fetch_patient_data_no_confunde_reminder_logs_con_assigned_reminders(qapp):
    """RB-3: la telemetría (reminder_logs) y la programación
    (assigned_reminders) son conceptos distintos y deben viajar en keys
    distintas del dict:

      - datos["recordatorios"]    ← assigned_reminders (programación profesional)
      - datos["avisos_disparados"] ← reminder_logs (telemetría real)

    Ambas tablas deben consultarse, no reemplazarse mutuamente.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    datos = view._fetch_patient_data()

    # Ambas tablas deben consultarse
    assert "reminder_logs" in sb.select_calls, "Falta fetch de reminder_logs"
    assert "assigned_reminders" in sb.select_calls, (
        "RB-3 no debe reemplazar el fetch de assigned_reminders — son "
        "conceptos complementarios (programación vs telemetría)."
    )
    # Keys distintas en el dict
    assert "avisos_disparados" in datos, (
        "Falta la key 'avisos_disparados' en el dict de _fetch_patient_data"
    )
    assert "recordatorios" in datos, (
        "RB-3 no debe eliminar la key existente 'recordatorios'."
    )
    assert datos["avisos_disparados"] is not datos["recordatorios"], (
        "Las keys 'avisos_disparados' y 'recordatorios' referencian la misma "
        "lista — deben ser listas independientes."
    )


def test_fetch_patient_data_devuelve_key_avisos_disparados_poblada(qapp):
    """RB-3 (smoke): cuando reminder_logs tiene datos, el dict los expone
    bajo la key 'avisos_disparados' con la estructura esperada.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    datos = view._fetch_patient_data()

    assert isinstance(datos.get("avisos_disparados"), list), (
        f"avisos_disparados debe ser una lista, got "
        f"{type(datos.get('avisos_disparados'))!r}"
    )
    assert len(datos["avisos_disparados"]) == 1, (
        "Se esperaba 1 fila de telemetría (poblada por el mock). "
        f"Got {len(datos['avisos_disparados'])}"
    )
    row = datos["avisos_disparados"][0]
    for expected_key in ("fecha", "hora", "mensaje", "cerrado"):
        assert expected_key in row, (
            f"Fila de telemetría no incluye {expected_key!r}: {row!r}"
        )
