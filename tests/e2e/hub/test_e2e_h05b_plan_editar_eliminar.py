from __future__ import annotations

import pytest

from tests.e2e.pages.hub.plan_terapeutico_page import PlanTerapeuticoPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


PID = "patient-h05b"


def test_timer_editar_preset_existente(qapp, qtbot, request, sb):
    sb.seed(
        "timer_presets_remote",
        [{"id": 10, "scope": f"patient:{PID}", "name": "Viejo", "duracion_seg": 600, "categoria": "Foco"}],
    )
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.timer_tab._edit(sb.all_rows("timer_presets_remote")[0])
        page.add_timer("Nuevo", "20", "Estudio")
        row = sb.table("timer_presets_remote").select("*").eq("id", 10).single().execute().data
        assert row["name"] == "Nuevo"
        assert row["duracion_seg"] == 1200
    finally:
        page.close()


def test_timer_eliminar_preset_existente(qapp, qtbot, request, sb):
    sb.seed(
        "timer_presets_remote",
        [{"id": 11, "scope": f"patient:{PID}", "name": "Borrar", "duracion_seg": 600, "categoria": "Foco"}],
    )
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.timer_tab._delete(11)
        assert sb.table("timer_presets_remote").select("*").eq("id", 11).execute().data == []
    finally:
        page.close()


def test_timer_cancelar_edicion(qapp, qtbot, request, sb):
    sb.seed(
        "timer_presets_remote",
        [{"id": 12, "scope": f"patient:{PID}", "name": "Editar", "duracion_seg": 900, "categoria": "Foco"}],
    )
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.timer_tab._edit(sb.all_rows("timer_presets_remote")[0])
        assert page.timer_tab._editing_id == 12
        page.timer_tab._cancel_edit()
        assert page.timer_tab._editing_id is None
        assert page.timer_tab._ent_name.text() == ""
    finally:
        page.close()


def test_recordatorios_eliminar(qapp, qtbot, request, sb):
    sb.seed("assigned_reminders", [{"id": 21, "patient_id": PID, "hora": "08:00", "mensaje": "Agua"}])
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.recordatorios_tab._delete_recordatorio(21)
        assert sb.table("assigned_reminders").select("*").eq("id", 21).execute().data == []
    finally:
        page.close()


def test_rutina_eliminar_tarea(qapp, qtbot, request, sb):
    sb.seed("assigned_tasks", [{"id": 31, "patient_id": PID, "descripcion": "Respirar", "seccion": "manana"}])
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.rutina_tab._delete_task(31)
        assert sb.table("assigned_tasks").select("*").eq("id", 31).execute().data == []
    finally:
        page.close()


def test_activacion_eliminar(qapp, qtbot, request, sb):
    sb.seed("patient_activities", [{"id": 41, "patient_id": PID, "nombre": "Caminar", "animo_min": 1, "animo_max": 10}])
    page = PlanTerapeuticoPage(qapp, qtbot, request=request).open(sb, pid=PID)
    try:
        page.activacion_tab._delete_activity(41)
        assert sb.table("patient_activities").select("*").eq("id", 41).execute().data == []
    finally:
        page.close()
