"""RB-5: _register_result dispara sync_inmediato_background tras el INSERT.

Antes de RB-5, el módulo Actividades era el único de los 8 que NO llamaba
sync_inmediato_background al guardar. La activación conductual del paciente
quedaba pendiente hasta el próximo sync. RB-5 agrega el mismo patrón que
usan timer_qt._save_session y animo_qt._registrar.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def actividades_module_with_temp_db(qapp, isolated_db):
    from app.modules.actividades_qt import ModuloActividades
    from shared.db import conexion
    from shared.utils import fecha_hoy, hora_actual

    with conexion() as conn:
        conn.execute(
            "INSERT INTO termometro (fecha, hora, puntaje, nota) VALUES (?, ?, ?, ?)",
            (fecha_hoy(), hora_actual(), 7, ""),
        )

    mod = ModuloActividades(modo="dark_hybrid", show_header=False)
    mod.resize(960, 600)
    mod.show()
    for _ in range(5):
        qapp.processEvents()

    yield mod

    mod.close()
    mod.deleteLater()
    qapp.processEvents()


def test_register_result_dispara_sync_inmediato(actividades_module_with_temp_db):
    """RB-5: _register_result debe llamar sync_inmediato_background después
    del INSERT. Verificado con mock que captura la llamada real."""
    mod = actividades_module_with_temp_db

    class _MockCard:
        def setVisible(self, v): pass
        def deleteLater(self): pass
        def set_accent(self, c): pass
        def play_success(self): pass
        def set_completed(self, v): pass

    with patch("shared.sync.sync_inmediato_background") as sync_mock:
        mod._register_result("Caminar", "hecha", _MockCard(), None)

    assert sync_mock.call_count == 1, (
        f"sync_inmediato_background debe llamarse 1 vez, got {sync_mock.call_count}. "
        "Antes de RB-5, _register_result no llamaba sync — la activación quedaba "
        "pendiente hasta el próximo sync."
    )


def test_register_result_persiste_y_sincroniza(actividades_module_with_temp_db):
    """RB-5: tras _register_result, el registro está en SQLite Y se disparó
    sync_inmediato_background. Verifica que el fix no rompe la persistencia."""
    from shared.db import obtener_conexion

    mod = actividades_module_with_temp_db

    class _MockCard:
        def setVisible(self, v): pass
        def deleteLater(self): pass
        def set_accent(self, c): pass
        def play_success(self): pass
        def set_completed(self, v): pass

    with patch("shared.sync.sync_inmediato_background") as sync_mock:
        mod._register_result("Meditar", "intentada", _MockCard(), None)

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT actividad, resultado FROM activacion ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["actividad"] == "Meditar"
    assert row["resultado"] == "intentada"
    assert sync_mock.call_count == 1


def test_sync_no_bloquea_si_falla(actividades_module_with_temp_db):
    """RB-5: si sync_inmediato_background lanza excepción, _register_result
    no debe propagarla — el registro ya está guardado en SQLite."""
    from shared.db import obtener_conexion

    mod = actividades_module_with_temp_db

    class _MockCard:
        def setVisible(self, v): pass
        def deleteLater(self): pass
        def set_accent(self, c): pass
        def play_success(self): pass
        def set_completed(self, v): pass

    with patch("shared.sync.sync_inmediato_background", side_effect=RuntimeError("network error")):
        mod._register_result("Yoga", "hecha", _MockCard(), None)

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT actividad FROM activacion ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["actividad"] == "Yoga"
