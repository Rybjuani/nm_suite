from __future__ import annotations

import datetime as dt
from types import SimpleNamespace


TABLES_WITH_FECHA = {
    "mood_records",
    "breathing_sessions",
    "thought_records",
    "checklist_completions",
    "activation_results",
    "timer_sessions",
    "dbt_practice_records",
    "reminder_logs",
}


class _RecordingQuery:
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
        return SimpleNamespace(data=self._parent.rows.get(self._table, []))


class _RecordingSB:
    def __init__(self):
        self.select_calls: dict[str, str] = {}
        self.eq_calls: dict[str, list[tuple[str, object]]] = {}
        self.gte_calls: dict[str, list[tuple[str, object]]] = {}
        self.order_calls: dict[str, tuple[str, bool]] = {}
        self.limit_calls: dict[str, int] = {}
        self.rows = {
            table: [{"fecha": "2026-06-18"}] for table in TABLES_WITH_FECHA
        }
        self.rows["assigned_reminders"] = [
            {"id": 1, "hora": "09:00", "mensaje": "Tomar agua", "activa": True}
        ]

    def table(self, name: str) -> _RecordingQuery:
        return _RecordingQuery(self, name)


class _FrozenDateTime:
    @classmethod
    def now(cls):
        return dt.datetime(2026, 6, 19, 12, 0, 0)


def _make_view(sb):
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = sb
    view._pid = "patient-1"
    view._nombre = "Paciente"
    return view


def test_fetch_patient_data_aplica_gte_fecha_30_dias(qapp, monkeypatch):
    import hub.pacientes_qt as pacientes_qt

    sb = _RecordingSB()
    monkeypatch.setattr(pacientes_qt, "datetime", _FrozenDateTime)

    _make_view(sb)._fetch_patient_data()

    assert set(sb.gte_calls) == TABLES_WITH_FECHA
    assert all(calls == [("fecha", "2026-05-20")] for calls in sb.gte_calls.values())


def test_fetch_patient_data_no_aplica_gte_a_assigned_reminders(qapp, monkeypatch):
    import hub.pacientes_qt as pacientes_qt

    sb = _RecordingSB()
    monkeypatch.setattr(pacientes_qt, "datetime", _FrozenDateTime)

    _make_view(sb)._fetch_patient_data()

    assert "assigned_reminders" not in sb.gte_calls
    assert sb.order_calls["assigned_reminders"] == ("hora", False)
    assert sb.limit_calls["assigned_reminders"] == 50
