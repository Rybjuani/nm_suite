"""Integracion Hub -> hub_config -> sync -> Suite real para textos globales."""

from __future__ import annotations

import os

import pytest

from tests.e2e.fakes.supabase_fake import FakeSupabase as _FakeSupabase

# Movido a tests/conftest.py (se aplica a todos los tests antes de
# cualquier import de PyQt6, no solo a los que lo seteaban individualmente).


def _sync_fake_hub_config(sb: _FakeSupabase) -> None:
    from shared.sync import _importar_hub_config

    _importar_hub_config(sb, "patient-fase5")


def _drain_events(qapp, cycles: int = 6) -> None:
    for _ in range(cycles):
        qapp.processEvents()


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
    row = (
        sb.table("hub_config")
        .select("value")
        .eq("scope", "global")
        .eq("key", key)
        .single()
        .execute()
        .data
    )
    assert row == {"value": value}


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
    assert (
        sb.table("hub_config")
        .select("*")
        .eq("scope", "global")
        .eq("key", key)
        .execute()
        .data
        == []
    )
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


def test_global_texts_dirty_row_matches_mockup_visual_state(qapp):
    import inspect

    from hub.config_global_texts import TextosGlobalesSuiteView, _TextEntryRow

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=_FakeSupabase())
    qapp.processEvents()

    row = view._rows_by_key["text.home.module.timer.card_title"]
    assert not row._dirty

    row.set_value("Timer editable")
    view._update_pending_state()
    qapp.processEvents()

    assert row._dirty
    assert row._radius_override == 16
    source = inspect.getsource(_TextEntryRow.paintEvent)
    assert 'v3c("brandLine", self._modo)' in source
    assert 'v3c("brandSoft", self._modo)' in inspect.getsource(_TextEntryRow._apply_dirty_shadow)


def test_global_texts_offscreen_rows_do_not_expose_controls(qapp):
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=_FakeSupabase())
    view.resize(960, 600)
    view.show()
    _drain_events(qapp)

    first_row = view._rows[0]
    offscreen_row = next(
        row for row in view._rows if row.geometry().top() > view._scroll.viewport().height()
    )

    assert first_row.editor.isVisible()
    assert first_row._restore_btn.isVisible()
    # El editor permanece visible siempre: ahora porta el VALOR del texto (como el
    # mockup canonico, sin un label de default aparte). Ocultarlo esconderia el
    # contenido. Solo el boton Restaurar se oculta fuera del viewport.
    assert offscreen_row.editor.isVisible()
    assert not offscreen_row._restore_btn.isVisible()

    view._scroll.verticalScrollBar().setValue(offscreen_row.geometry().top())
    _drain_events(qapp)

    assert offscreen_row.editor.isVisible()
    assert offscreen_row._restore_btn.isVisible()
    view.close()


@pytest.mark.parametrize(
    ("label", "key", "replacement", "reader"),
    [
        ("Home", "text.home.module.timer.card_title", "Timer Fase 5", _home_timer_title),
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
