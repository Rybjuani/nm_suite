from __future__ import annotations

import pytest

from tests.e2e.fakes.ia_fake import FakeIAResponder
from tests.e2e.fakes.supabase_fake import FakeSupabase


pytestmark = pytest.mark.e2e


def test_fake_supabase_select_insert_update_delete():
    sb = FakeSupabase()
    sb.table("items").insert({"name": "uno", "kind": "a"}).execute()
    sb.table("items").insert({"name": "dos", "kind": "b"}).execute()

    assert [row["name"] for row in sb.table("items").select("*").eq("kind", "a").execute().data] == ["uno"]

    sb.table("items").update({"kind": "c"}).eq("name", "uno").execute()
    assert sb.table("items").select("kind").eq("name", "uno").single().execute().data == {"kind": "c"}

    sb.table("items").delete().neq("kind", "c").execute()
    assert [row["name"] for row in sb.all_rows("items")] == ["uno"]


def test_fake_ia_responder_queues_and_failures():
    responder = FakeIAResponder().queue_resumen("ok")
    seen = []
    responder.generar_resumen_paciente({}, "Ana", seen.append, seen.append, patient_id="p1")
    assert seen == ["ok"]
    assert responder.calls_resumen[0]["patient_id"] == "p1"

    responder.fail_next_asignacion("sin llm")
    responder.generar_asignacion("timer", {}, "Ana", seen.append, seen.append, patient_id="p1")
    assert seen[-1] == "sin llm"
