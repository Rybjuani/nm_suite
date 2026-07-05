from __future__ import annotations

import pytest

from tests.e2e._helpers.qt_helpers import drain, latest_toast_variant


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


TEXT_KEY = "text.home.module.timer.card_title"


def _make_view(qapp, sb):
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=sb)
    view.resize(960, 600)
    view.show()
    drain(qapp)
    return view


def test_h01_textos_globales_renderiza_sin_crash(qapp, sb):
    view = _make_view(qapp, sb)

    assert view._rows
    assert TEXT_KEY in view._rows_by_key
    assert view._save.isEnabled() is False

    view.close()


def test_h01_editar_texto_global_persiste_override(qapp, sb):
    view = _make_view(qapp, sb)
    row = view._rows_by_key[TEXT_KEY]

    row.set_value("Timer terapeutico")
    drain(qapp)
    assert view.has_pending_changes()
    assert view._save.isEnabled()

    view._save_changes()
    drain(qapp)

    rows = sb.table("hub_config").select("*").eq("scope", "global").eq("key", TEXT_KEY).execute().data
    assert rows == [{"scope": "global", "key": TEXT_KEY, "value": "Timer terapeutico", "id": 1}]
    assert latest_toast_variant(view.window()) == "success"
    assert view._save.isEnabled() is False

    view.close()


def test_h01_sin_cambios_pendientes_boton_guardar_deshabilitado(qapp, sb):
    view = _make_view(qapp, sb)

    assert not view.has_pending_changes()
    # `.tg-foot` canónico: el status es un QLabel de texto plano (no pill).
    assert view._pending_status.text() == "Sin cambios"
    assert view._save.isEnabled() is False

    view.close()


def test_h01_guardar_sin_supabase_muestra_error(qapp):
    view = _make_view(qapp, None)
    view._rows_by_key[TEXT_KEY].set_value("Cambio sin conexion")
    drain(qapp)

    view._save_changes()
    drain(qapp)

    assert latest_toast_variant(view.window()) == "error"
    assert view._save.isEnabled()

    view.close()
