from __future__ import annotations

import pytest

from tests.e2e.fakes.ia_fake import patch_ia
from tests.e2e.pages.hub.plan_terapeutico_page import PlanTerapeuticoPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


PID = "patient-h05"


def test_timer_agregar(qapp, qtbot, request, sb):
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.add_timer("Lectura", "25", "Foco")
        rows = sb.table("timer_presets_remote").select("*").eq("scope", f"patient:{PID}").execute().data
        assert rows[0]["name"] == "Lectura"
        assert rows[0]["duracion_seg"] == 1500
    finally:
        page.close()


def test_recordatorio_agregar(qapp, qtbot, request, sb):
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.add_recordatorio("08:30", "Tomar agua")
        rows = sb.table("assigned_reminders").select("*").eq("patient_id", PID).execute().data
        assert rows[0]["hora"] == "08:30"
        assert rows[0]["mensaje"] == "Tomar agua"
    finally:
        page.close()


def test_rutina_agregar(qapp, qtbot, request, sb):
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.add_rutina("Respirar 3 minutos")
        rows = sb.table("assigned_tasks").select("*").eq("patient_id", PID).execute().data
        assert rows[0]["descripcion"] == "Respirar 3 minutos"
    finally:
        page.close()


def test_activacion_agregar(qapp, qtbot, request, sb):
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.add_activacion("Caminata corta", "15 min afuera")
        rows = sb.table("patient_activities").select("*").eq("patient_id", PID).execute().data
        assert rows[0]["nombre"] == "Caminata corta"
        assert "animo_min" in rows[0]
        assert "animo_max" in rows[0]
    finally:
        page.close()


def test_timer_completar_con_ia(qapp, qtbot, request, sb, ia_responder, monkeypatch):
    ia_responder.queue_asignacion("Nombre: Escritura\nMinutos: 15\nCategoria: Foco")
    patch_ia(monkeypatch, ia_responder)
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.timer_ia()
        assert page.timer_tab._ent_name.text() == "Escritura"
        assert page.timer_tab._ent_secs.text() == "15"
        assert page.timer_tab._ent_cat.text() == "Foco"
        assert ia_responder.calls_asignacion[0]["modulo"] == "timer"
    finally:
        page.close()
