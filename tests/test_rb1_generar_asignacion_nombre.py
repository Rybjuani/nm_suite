"""RB-1: generar_asignacion recibe self._nombre, no "".

Antes de RB-1, los 3 botones "Completar con IA" del Plan Terapéutico
(timer/avisos/rutina) pasaban nombre="" a generar_asignacion porque
los subtabs no recibían `nombre` en su constructor. El guard
_contexto_clinico_valido rechazaba la llamada y mostraba "Seleccioná un
paciente antes de generar." aunque el paciente ya estaba seleccionado.

RB-1 pasa `nombre` desde PlanTerapeuticoTab a los constructores de los
3 subtabs como argumento obligatorio, lo guarda como self._nombre, y lo
usa en generar_asignacion.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock


def _make_subtab(tab_class, qapp, nombre):
    """Construye un subtab con nombre real, sin tocar Supabase."""
    sb = MagicMock()
    query = sb.table.return_value
    query.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    query.select.return_value.eq.return_value.execute.return_value.data = []
    query.upsert.return_value.execute.return_value.data = []

    tab = tab_class(sb, "test-pid-123", "dark_hybrid", nombre, None)
    tab.show()
    for _ in range(5):
        qapp.processEvents()
    return tab


def test_timer_tab_autofill_pasa_nombre_real(qapp):
    """RB-1: _PresetTimerTab._autofill_with_ia pasa self._nombre (no "")
    como 3er argumento a generar_asignacion."""
    from hub.plan_terapeutico import _PresetTimerTab

    tab = _make_subtab(_PresetTimerTab, qapp, nombre="Juan Cruz")

    with patch("hub.ia_asistente.generar_asignacion") as mock_ia:
        tab._autofill_with_ia()

    assert mock_ia.call_count == 1
    args = mock_ia.call_args
    nombre_arg = args[0][2]
    assert nombre_arg == "Juan Cruz", (
        f"generar_asignacion recibió nombre={nombre_arg!r}, esperado 'Juan Cruz'. "
        "RB-1 requiere que self._nombre se transporte hasta generar_asignacion."
    )

    tab.close()
    tab.deleteLater()


def test_recordatorios_tab_autofill_pasa_nombre_real(qapp):
    """RB-1: _PresetRecordatoriosTab._autofill_with_ia pasa self._nombre."""
    from hub.plan_terapeutico import _PresetRecordatoriosTab

    tab = _make_subtab(_PresetRecordatoriosTab, qapp, nombre="María López")

    with patch("hub.ia_asistente.generar_asignacion") as mock_ia:
        tab._autofill_with_ia()

    assert mock_ia.call_count == 1
    args = mock_ia.call_args
    nombre_arg = args[0][2]
    assert nombre_arg == "María López", (
        f"generar_asignacion recibió nombre={nombre_arg!r}, esperado 'María López'."
    )

    tab.close()
    tab.deleteLater()


def test_rutina_tab_autofill_pasa_nombre_real(qapp):
    """RB-1: _PresetRutinaTab._autofill_with_ia pasa self._nombre."""
    from hub.plan_terapeutico import _PresetRutinaTab

    tab = _make_subtab(_PresetRutinaTab, qapp, nombre="Pedro Gómez")

    with patch("hub.ia_asistente.generar_asignacion") as mock_ia:
        tab._autofill_with_ia()

    assert mock_ia.call_count == 1
    args = mock_ia.call_args
    nombre_arg = args[0][2]
    assert nombre_arg == "Pedro Gómez", (
        f"generar_asignacion recibió nombre={nombre_arg!r}, esperado 'Pedro Gómez'."
    )

    tab.close()
    tab.deleteLater()
