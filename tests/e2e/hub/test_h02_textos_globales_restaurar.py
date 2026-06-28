from __future__ import annotations

import pytest

from tests.e2e._helpers.qt_helpers import drain


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


TEXT_KEY = "text.home.module.timer.card_title"
OTHER_KEY = "text.module.timer.empty_title"


def _make_view(qapp, sb):
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=sb)
    view.resize(960, 600)
    view.show()
    drain(qapp)
    return view


def test_h02_restaurar_texto_global_elimina_override(qapp, sb):
    sb.table("hub_config").upsert(
        {"scope": "global", "key": TEXT_KEY, "value": "Timer editado"},
        on_conflict="scope,key",
    ).execute()
    view = _make_view(qapp, sb)

    row = view._rows_by_key[TEXT_KEY]
    assert row.value() == "Timer editado"
    row.restore()
    drain(qapp)
    assert view.has_pending_changes()

    view._save_changes()
    drain(qapp)

    assert sb.table("hub_config").select("*").eq("key", TEXT_KEY).execute().data == []
    assert view._save.isEnabled() is False

    view.close()


def test_h02_restaurar_todos_los_textos_confirma_y_limpia(qapp, sb, monkeypatch):
    from hub import config_global_texts

    sb.table("hub_config").upsert(
        [
            {"scope": "global", "key": TEXT_KEY, "value": "Timer editado"},
            {"scope": "global", "key": OTHER_KEY, "value": "Sin timer editado"},
        ],
        on_conflict="scope,key",
    ).execute()
    view = _make_view(qapp, sb)

    confirmed = []

    def fake_confirm(parent, title, message, on_confirm, **kwargs):
        confirmed.append((title, message, kwargs))
        on_confirm()

    monkeypatch.setattr(config_global_texts, "nm_confirm", fake_confirm)

    view._restore_all_rows()
    drain(qapp)
    assert confirmed
    assert view.has_pending_changes()

    view._save_changes()
    drain(qapp)

    assert sb.table("hub_config").select("*").execute().data == []
    assert view._save.isEnabled() is False

    view.close()


def test_h02_restaurar_fila_sin_cambios_previos_no_genera_pending(qapp, sb):
    view = _make_view(qapp, sb)
    row = view._rows_by_key[TEXT_KEY]

    row.restore()
    drain(qapp)

    assert not view.has_pending_changes()
    assert row._dirty is False
    assert view._save.isEnabled() is False

    view.close()
