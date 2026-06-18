"""Integracion Hub -> hub_config -> sync -> Suite real para textos globales."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class _FakeHubConfigQuery:
    def __init__(self, client: "_FakeSupabase"):
        self._client = client
        self._operation = "select"
        self._payload = None
        self._filters: list[tuple[str, str, object]] = []

    def select(self, *_args, **_kwargs):
        self._operation = "select"
        return self

    def eq(self, field: str, value):
        self._filters.append(("eq", field, value))
        return self

    def like(self, field: str, pattern: str):
        self._filters.append(("like", field, pattern))
        return self

    def in_(self, field: str, values):
        self._filters.append(("in", field, set(values)))
        return self

    def delete(self):
        self._operation = "delete"
        return self

    def upsert(self, payload, on_conflict=None):
        self._operation = "upsert"
        self._payload = payload if isinstance(payload, list) else [payload]
        self._on_conflict = on_conflict
        return self

    def execute(self):
        if self._operation == "upsert":
            payload = self._payload or []
            for row in payload:
                scope = str(row["scope"])
                key = str(row["key"])
                self._client.rows[(scope, key)] = row["value"]
            return SimpleNamespace(data=payload)

        if self._operation == "delete":
            for scope, key, _value in list(self._iter_matching_rows()):
                self._client.rows.pop((scope, key), None)
            return SimpleNamespace(data=[])

        data = [
            {"scope": scope, "key": key, "value": value}
            for scope, key, value in self._iter_matching_rows()
        ]
        return SimpleNamespace(data=data)

    def _iter_matching_rows(self):
        for (scope, key), value in sorted(self._client.rows.items()):
            row = {"scope": scope, "key": key, "value": value}
            if self._matches(row):
                yield scope, key, value

    def _matches(self, row: dict) -> bool:
        for op, field, expected in self._filters:
            value = row[field]
            if op == "eq" and value != expected:
                return False
            if op == "in" and value not in expected:
                return False
            if op == "like":
                pattern = str(expected)
                if pattern.endswith("%"):
                    if not str(value).startswith(pattern[:-1]):
                        return False
                elif value != pattern:
                    return False
        return True


class _FakeSupabase:
    def __init__(self):
        self.rows: dict[tuple[str, str], object] = {}

    def table(self, table_name: str):
        assert table_name == "hub_config"
        return _FakeHubConfigQuery(self)


def _sync_fake_hub_config(sb: _FakeSupabase) -> None:
    from shared.sync import _importar_hub_config

    _importar_hub_config(sb, "patient-fase5")


def _count_sensitive_tables() -> dict[str, int]:
    from shared.db import obtener_conexion

    tables = (
        "checklist_tareas",
        "checklist_completadas",
        "checklist_completadas_v2",
        "pensamientos",
        "termometro",
        "activacion",
        "activacion_actividades",
        "recordatorios",
        "recordatorios_log",
        "actividades_temporizador",
        "respiracion",
        "dbt_practicas",
        "timer_presets",
        "checklist_plantillas",
        "checklist_notas_dia",
        "config",
    )
    conn = obtener_conexion()
    try:
        counts = {}
        existing = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        for table in tables:
            if table not in existing:
                counts[table] = None
                continue
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return counts
    finally:
        conn.close()


def _assert_remote_value(sb: _FakeSupabase, key: str, value: str) -> None:
    assert sb.rows[("global", key)] == value


def _edit_and_sync(key: str, value: str, qapp, sb: _FakeSupabase):
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="dark_hybrid", sb=sb)
    qapp.processEvents()
    view._rows_by_key[key].set_value(value)
    view._save_changes()
    qapp.processEvents()
    _assert_remote_value(sb, key, value)
    _sync_fake_hub_config(sb)
    return view


def _restore_and_sync(view, key: str, qapp, sb: _FakeSupabase) -> None:
    view._rows_by_key[key].restore()
    view._save_changes()
    qapp.processEvents()
    assert ("global", key) not in sb.rows
    _sync_fake_hub_config(sb)


def _home_timer_title(qapp) -> str:
    from app.home_qt import HomeView

    view = HomeView(modo="dark_hybrid", username="Alex")
    qapp.processEvents()
    return view._cards["timer"]._title_lbl.text()


def _onboarding_name_placeholder(qapp) -> str:
    from app.onboarding_qt import OnboardingDialog

    dialog = OnboardingDialog()
    qapp.processEvents()
    return dialog._name.placeholderText()


def _timer_empty_title(qapp) -> str:
    from app.modules.timer_qt import ModuloTimer

    module = ModuloTimer(show_header=False, modo="dark_hybrid")
    qapp.processEvents()
    return module._state_chip.text()


def _rutina_empty_title(qapp) -> str:
    from app.modules.rutina_qt import ModuloRutina

    module = ModuloRutina(show_header=False, modo="dark_hybrid")
    qapp.processEvents()
    return module._empty_state._title_lbl.text()


def _tcc_next_button(qapp) -> str:
    from app.modules.registro_tcc_qt import ModuloRegistroTCC

    module = ModuloRegistroTCC(show_header=False, modo="dark_hybrid")
    qapp.processEvents()
    return module._btn_next.text()


@pytest.mark.parametrize(
    ("label", "key", "replacement", "reader"),
    [
        ("Home", "text.home.module.timer.title", "Timer Fase 5", _home_timer_title),
        (
            "Onboarding",
            "text.onboarding.name_placeholder",
            "Nombre visible F5",
            _onboarding_name_placeholder,
        ),
        ("Temporizador", "text.module.timer.empty_title", "Timer sin asignacion F5", _timer_empty_title),
        ("Rutina", "text.module.rutina.empty_title", "Rutina sin asignacion F5", _rutina_empty_title),
        ("TCC", "text.module.registro.next_btn", "Continuar F5", _tcc_next_button),
    ],
)
def test_global_texts_hub_sync_suite_real_screens(qapp, label, key, replacement, reader):
    from shared.suite_text_catalog import suite_text_by_key

    sb = _FakeSupabase()
    sensitive_before = _count_sensitive_tables()

    view = _edit_and_sync(key, replacement, qapp, sb)
    assert reader(qapp) == replacement, label

    _restore_and_sync(view, key, qapp, sb)
    assert reader(qapp) == suite_text_by_key()[key].default, label

    assert _count_sensitive_tables() == sensitive_before
