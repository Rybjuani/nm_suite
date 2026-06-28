from __future__ import annotations

import pytest

from tests.e2e._helpers.qt_helpers import latest_toast_variant
from tests.e2e.fakes.ia_fake import patch_ia
from tests.e2e.pages.hub.detalle_paciente_page import DetallePacientePage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


def _seed_patient_data(sb, pid: str):
    sb.seed("mood_records", [{"patient_id": pid, "fecha": "2026-06-01", "puntaje": 7}])
    sb.seed("thought_records", [{"patient_id": pid, "fecha": "2026-06-01", "situacion": "Trabajo"}])
    sb.seed("assigned_reminders", [{"patient_id": pid, "hora": "09:00", "mensaje": "Agua", "activa": True}])


def test_resumen_ia_exitoso(qapp, qtbot, request, sb, ia_responder, monkeypatch):
    pid = "patient-h03-ok"
    _seed_patient_data(sb, pid)
    ia_responder.queue_resumen("Resumen clinico breve")
    patch_ia(monkeypatch, ia_responder)

    page = DetallePacientePage(qapp, qtbot, request=request).open(sb, pid=pid)
    try:
        page.generar_resumen().expect_resumen_button_ready().expect_resumen_dialog()
        assert ia_responder.calls_resumen[0]["patient_id"] == pid
    finally:
        page.close()


def test_resumen_ia_error_sin_llm(qapp, qtbot, request, sb, ia_responder, monkeypatch):
    pid = "patient-h03-error"
    _seed_patient_data(sb, pid)
    ia_responder.fail_next_resumen("sin proveedor")
    patch_ia(monkeypatch, ia_responder)

    page = DetallePacientePage(qapp, qtbot, request=request).open(sb, pid=pid)
    try:
        page.generar_resumen().expect_resumen_button_ready()
        assert latest_toast_variant(page.window) == "error"
    finally:
        page.close()
