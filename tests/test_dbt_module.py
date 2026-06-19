import sys
import sqlite3
import datetime
import uuid
import pytest
from PyQt6.QtWidgets import QApplication

from shared.db import conexion, inicializar_tablas
from app.modules.dbt_qt import ModuloDBT, DBT_SKILLS, _PracticeClosure

_qapp = None
def get_qapp():
    global _qapp
    if not _qapp:
        _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


def test_dbt_table_idempotent():
    # Calling inicializar_tablas multiple times should succeed without error
    try:
        inicializar_tablas()
        inicializar_tablas()
        assert True
    except Exception as e:
        pytest.fail(f"inicializar_tablas failed with error: {e}")


def test_dbt_table_idempotence_preserves_data():
    inicializar_tablas()
    # Clean up and insert test record
    rec_id = str(uuid.uuid4())
    try:
        with conexion() as conn:
            conn.execute("DELETE FROM dbt_practicas")
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (rec_id, "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
            )
        
        # Call inicializar_tablas() again
        inicializar_tablas()
        
        # Check that the record is still there
        with conexion() as conn:
            row = conn.execute("SELECT COUNT(*) FROM dbt_practicas WHERE record_id = ?", (rec_id,)).fetchone()[0]
            assert row == 1
    finally:
        # Clean up
        with conexion() as conn:
            conn.execute("DELETE FROM dbt_practicas WHERE record_id = ?", (rec_id,))


def test_dbt_constraints():
    inicializar_tablas()
    
    # Test invalid family constraint
    with conexion() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "2026-06-14", "10:00:00", "mind_wise", 1, "invalid_family", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
            )
            
    # Test invalid malestar_antes constraint (>10)
    with conexion() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 12, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
            )
            
    # Test invalid malestar_despues constraint (<0)
    with conexion() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, -1, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
            )

    # Test invalid result constraint
    with conexion() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "invalid_result", 60, "test", "2026-06-14T10:00:00Z")
            )

    # Test invalid duration constraint (negative duration)
    with conexion() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", -30, "test", "2026-06-14T10:00:00Z")
            )


def test_dbt_valid_constraints():
    inicializar_tablas()
    try:
        with conexion() as conn:
            for family in ['mindfulness', 'distress_tolerance', 'emotion_regulation', 'interpersonal_effectiveness']:
                conn.execute(
                    "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), "2026-06-14", "10:00:00", "mind_wise", 1, family, "Volver al presente", 0, 10, "ayudo", 0, "test", "2026-06-14T10:00:00Z")
                )
        assert True
    except Exception as e:
        pytest.fail(f"Valid values insertion failed: {e}")


def test_dbt_null_scales():
    inicializar_tablas()
    
    # Verify we can save NULLs for malestar ratings
    rec_id = str(uuid.uuid4())
    try:
        with conexion() as conn:
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (rec_id, "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", None, None, "sin_evaluar", 60, "", "2026-06-14T10:00:00Z")
            )
        
        with conexion() as conn:
            row = conn.execute("SELECT malestar_antes, malestar_despues FROM dbt_practicas WHERE record_id = ?", (rec_id,)).fetchone()
            assert row["malestar_antes"] is None
            assert row["malestar_despues"] is None
    finally:
        with conexion() as conn:
            conn.execute("DELETE FROM dbt_practicas WHERE record_id = ?", (rec_id,))


def test_dbt_save_null_flow():
    get_qapp()
    module = ModuloDBT(show_header=False)
    module._current_skill_id = "mind_observe"
    module._current_family = "mindfulness"
    module._started_at = datetime.datetime.now() - datetime.timedelta(seconds=120)
    
    # Clear records first
    with conexion() as conn:
        conn.execute("DELETE FROM dbt_practicas")
        
    # Trigger _on_practice_saved with None (NULL) malestar ratings
    module._on_practice_saved(antes=None, despues=None, resultado="sin_evaluar", nota="test null save")
    
    # Retrieve the inserted record
    with conexion() as conn:
        rows = conn.execute("SELECT * FROM dbt_practicas").fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["malestar_antes"] is None
        assert row["malestar_despues"] is None
        assert row["resultado"] == "sin_evaluar"
        assert row["nota"] == "test null save"
        assert row["duracion_seg"] >= 120
        assert row["duracion_seg"] < 125


def test_dbt_cancel_does_not_insert():
    get_qapp()
    module = ModuloDBT(show_header=False)
    module.start_practice(DBT_SKILLS["mind_observe"])
    
    # Clear records first
    with conexion() as conn:
        conn.execute("DELETE FROM dbt_practicas")
        
    # Simulate clicking cancel on practice view
    module._on_practice_cancelled()
    
    with conexion() as conn:
        count = conn.execute("SELECT COUNT(*) FROM dbt_practicas").fetchone()[0]
        assert count == 0


def test_dbt_double_save_prevention():
    get_qapp()
    
    closure = _PracticeClosure("Observar y describir", modo=None)
    
    # Connect its saved signal to a custom function that records how many times it was emitted
    emitted_payloads = []
    closure.saved.connect(lambda antes, despues, res, nota: emitted_payloads.append((antes, despues, res, nota)))
    
    # Simulate saving twice
    closure._save_practice()
    closure._save_practice()
    
    # It should only emit once
    assert len(emitted_payloads) == 1


def test_dbt_get_card_status():
    get_qapp()
    inicializar_tablas()
    
    # Clean up first
    with conexion() as conn:
        conn.execute("DELETE FROM dbt_practicas")
        
    module = ModuloDBT(show_header=False)
    
    # Check initially empty status
    assert module.get_card_status() == "Sin prácticas"
    
    # Insert one practice for today
    today_str = datetime.date.today().isoformat()
    rec_id1 = str(uuid.uuid4())
    with conexion() as conn:
        conn.execute(
            "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (rec_id1, today_str, "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
        )
        
    assert module.get_card_status() == "1 práctica hoy"
    
    # Insert another practice
    rec_id2 = str(uuid.uuid4())
    with conexion() as conn:
        conn.execute(
            "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (rec_id2, today_str, "11:00:00", "mind_observe", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T11:00:00Z")
        )
        
    assert module.get_card_status() == "2 prácticas hoy"
    
    # Clean up
    with conexion() as conn:
        conn.execute("DELETE FROM dbt_practicas WHERE record_id IN (?, ?)", (rec_id1, rec_id2))


def test_dbt_get_card_status_weekly():
    get_qapp()
    module = ModuloDBT(show_header=False)
    
    # Clear
    with conexion() as conn:
        conn.execute("DELETE FROM dbt_practicas")
        
    assert module.get_card_status() == "Sin prácticas"
    
    # Insert practice from 3 days ago
    three_days_ago = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
    with conexion() as conn:
        conn.execute(
            "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), three_days_ago, "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
        )
        
    assert module.get_card_status() == "1 práctica esta semana"
    
    # Insert another practice from 5 days ago
    five_days_ago = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
    with conexion() as conn:
        conn.execute(
            "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), five_days_ago, "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
        )
        
    assert module.get_card_status() == "2 prácticas esta semana"


def test_dbt_reopen_module_retains_records():
    get_qapp()
    
    # Clear and insert a record
    today_str = datetime.date.today().isoformat()
    with conexion() as conn:
        conn.execute("DELETE FROM dbt_practicas")
        conn.execute(
            "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("rec_reopen_test", today_str, "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test", "2026-06-14T10:00:00Z")
        )
        
    # Instantiate two modules and verify both see the persisted DB state.
    module1 = ModuloDBT(show_header=False)
    assert module1.get_card_status() == "1 práctica hoy"
    
    # Close/destroy module1
    module1.deleteLater()
    del module1
    
    # Instantiate a second module, check card status and history
    module2 = ModuloDBT(show_header=False)
    assert module2.get_card_status() == "1 práctica hoy"


class MockSupabaseTable:
    def __init__(self, table_name):
        self.table_name = table_name
        self.upsert_payloads = []
        
    def upsert(self, payload, on_conflict=None):
        self.upsert_payloads.append(payload)
        return self
        
    def execute(self):
        return self


class MockSupabaseClient:
    def __init__(self):
        self.tables = {}
        
    def table(self, name):
        if name not in self.tables:
            self.tables[name] = MockSupabaseTable(name)
        return self.tables[name]


def test_exportar_dbt_practicas():
    from shared.sync import _exportar_dbt_practicas
    inicializar_tablas()
    
    # Clean up and insert test record
    rec_id = str(uuid.uuid4())
    try:
        with conexion() as conn:
            conn.execute("DELETE FROM dbt_practicas")
            conn.execute(
                "INSERT INTO dbt_practicas (record_id, fecha, hora, skill_id, skill_version, familia, necesidad, malestar_antes, malestar_despues, resultado, duracion_seg, nota, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (rec_id, "2026-06-14", "10:00:00", "mind_wise", 1, "mindfulness", "Volver al presente", 5, 3, "ayudo", 60, "test sync note", "2026-06-14T10:00:00Z")
            )
        
        # Test synchronization
        sb = MockSupabaseClient()
        _exportar_dbt_practicas(sb, "test_patient", "2026-06-14T00:00:00Z")
        
        # Verify the client received the payload
        dbt_table = sb.table("dbt_practice_records")
        assert len(dbt_table.upsert_payloads) == 1
        payload = dbt_table.upsert_payloads[0]
        assert len(payload) == 1
        record = payload[0]
        assert record["record_id"] == rec_id
        assert record["patient_id"] == "test_patient"
        assert record["skill_id"] == "mind_wise"
        assert record["nota"] == "test sync note"
        assert record["malestar_antes"] == 5
        assert record["malestar_despues"] == 3
        assert record["resultado"] == "ayudo"
    finally:
        with conexion() as conn:
            conn.execute("DELETE FROM dbt_practicas WHERE record_id = ?", (rec_id,))


def test_hub_exportar_pdf_integration():
    from hub.exportar import _normalizar_secciones
    secciones = _normalizar_secciones(None)
    assert "dbt" in secciones
    
    from hub.exportar import _generar
    
    test_datos = {
        "animo": [],
        "respiracion": [],
        "tcc": [],
        "checklist": [],
        "actividades": [],
        "timer": [],
        "recordatorios": [],
        "avisos_disparados": [],
        "dbt": [
            {
                "record_id": "test_id",
                "fecha": "2026-06-14",
                "hora": "10:00:00",
                "skill_id": "mind_wise",
                "familia": "mindfulness",
                "resultado": "ayudo",
                "malestar_antes": 6,
                "malestar_despues": 3,
                "nota": "test pdf notes"
            }
        ]
    }
    
    try:
        import os
        path = _generar(
            nombre="Paciente Test",
            pid="test_patient_123",
            datos=test_datos,
            secciones=["dbt"],
            fecha_desde="",
            fecha_hasta="",
            nombre_archivo="test_dbt_export.pdf"
        )
        assert os.path.exists(path)
        os.remove(path)
    except Exception as e:
        pytest.fail(f"PDF generation with DBT records crashed: {e}")


def test_dbt_module_apply_theme_scroll_bars():
    get_qapp()
    module = ModuloDBT(show_header=False)
    
    module._apply_theme("dark")
    assert "dark" in module._modo
    
    from shared.theme_qt import stylesheet_scrollarea
    expected_style = stylesheet_scrollarea(module._modo)
    assert module._biblioteca_scroll.styleSheet() == expected_style


def test_dbt_custom_widgets_behaviors():
    get_qapp()
    from app.modules.dbt_qt import _DistressRatingButton, _ServiceOptionButton, _StepProgressIndicator
    
    # Test Distress Rating Button
    btn_low = _DistressRatingButton(2, modo="dark")
    assert btn_low.text() == "2"
    assert not btn_low.is_active()
    btn_low.set_active(True)
    assert btn_low.is_active()
    
    btn_mid = _DistressRatingButton(5, modo="light")
    btn_mid.set_active(True)
    
    btn_high = _DistressRatingButton(9, modo="dark")
    btn_high.set_active(True)
    
    # Test Service Option Button
    btn_opt = _ServiceOptionButton("ayudo", "Me ayudó", modo="dark")
    assert btn_opt.text() == "Me ayudó"
    btn_opt.set_active(True)
    assert btn_opt.is_active()
    
    # Test Step Progress Indicator
    indicator = _StepProgressIndicator(num_steps=3, family="mindfulness", modo="dark")
    assert indicator._current_step == 0
    indicator.set_current_step(1)
    assert indicator._current_step == 1
    
    # Ensure they can paint without crashing
    btn_low.repaint()
    btn_opt.repaint()
    indicator.repaint()


