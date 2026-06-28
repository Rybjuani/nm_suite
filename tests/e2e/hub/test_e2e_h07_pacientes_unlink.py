from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


def test_x_quitar_paciente_desvincula_y_oculta_fila(qapp, qtbot, monkeypatch, sb):
    import hub.main_qt as main_qt

    pid = "patient-unlink-e2e"
    paciente = {
        "patient_id": pid,
        "patient_name": "Paciente Fachada",
        "email": "fachada@example.com",
        "last_sync_date": "2026-06-28",
        "adherence": 0.8,
        "mood_data_7d": [5, 6, 6, 7, 7, 8, 8],
    }
    sb.seed("patients", [paciente])
    locally_unlinked: list[str] = []
    refreshes: list[bool] = []

    monkeypatch.setattr(main_qt, "visual_qa_enabled", lambda: False)
    monkeypatch.setattr(main_qt, "_add_local_unlinked", lambda value: locally_unlinked.append(value))
    monkeypatch.setattr(
        main_qt.QDialog,
        "exec",
        lambda _dialog: QDialog.DialogCode.Accepted,
    )
    monkeypatch.setattr(main_qt.NMToast, "display", lambda *_args, **_kwargs: None)

    view = main_qt.PacientesView(
        modo="light_hybrid",
        pacientes=[paciente.copy()],
        on_select=lambda *_args: None,
        on_refresh=lambda: refreshes.append(True),
        sb=sb,
    )
    qtbot.addWidget(view)
    view.resize(960, 600)
    view.show()
    for _ in range(8):
        qapp.processEvents()

    assert len(view._patient_row_widgets) == 1
    row = view._patient_row_widgets[0]
    assert row._btn_unlink is not None
    assert row._btn_unlink.isVisible()

    qtbot.mouseClick(row._btn_unlink, Qt.MouseButton.LeftButton)
    for _ in range(8):
        qapp.processEvents()

    assert view._patient_row_widgets == []
    assert locally_unlinked == [pid]
    assert refreshes == [True]
    assert sb.table("patients").select("*").eq("patient_id", pid).single().execute().data[
        "unlinked"
    ] is True
