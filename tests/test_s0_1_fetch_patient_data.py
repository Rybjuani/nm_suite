"""S0-1 smoke test: _fetch_patient_data trae datos de las 9 tablas reales.

Verifica que después del fix S0-1 (+ RB-3 que agrega reminder_logs):
1. Las 4 tablas inexistentes (animo_registros, tcc_registros, activacion_registros,
   dbt_registros) NO se consultan.
2. Las 9 tablas reales (mood_records, breathing_sessions, thought_records,
   checklist_completions, activation_results, timer_sessions, assigned_reminders,
   dbt_practice_records, reminder_logs) SÍ se consultan y devuelven datos.
3. Los campos textuales de cada módulo viajan en el dict (no solo id+fecha).

Marcado como skip si PyQt6 no está disponible (corre en CI con PyQt6 instalado).
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest_plugins = ["pytestqt"]


class _FakeQuery:
    def __init__(self, data, table):
        self._data = data
        self._table = table

    def select(self, *_args, **_kw): return self
    def eq(self, *_args, **_kw): return self
    def order(self, *_args, **_kw): return self
    def limit(self, *_args, **_kw): return self

    def execute(self):
        class _R: pass
        r = _R()
        r.data = self._data
        return r


class _FakeSB:
    """Mock de cliente Supabase que devuelve datos reales para las 8 tablas correctas.
    Lanza Exception si se consulta una tabla inexistente — esto es lo que
    pasaba en producción y que el fix S0-1 debe prevenir."""

    def __init__(self):
        self.calls: list[str] = []
        self._mock_data = {
            "mood_records": [{"fecha": "2026-06-18", "hora": "10:00", "puntaje": 7,
                              "nota": "ok", "emocion": "Calma",
                              "valencia": "positiva", "intensidad": 7}],
            "breathing_sessions": [{"fecha": "2026-06-18", "hora": "11:00",
                                    "tecnica": "4-7-8", "duracion_minutos": 5.0,
                                    "ciclos": 8}],
            "thought_records": [{"fecha": "2026-06-18", "hora": "12:00",
                                 "situacion": "test", "emocion": "Ansiedad",
                                 "intensidad": 6, "pensamiento": "p",
                                 "respuesta_alternativa": "r",
                                 "distorsiones": "d", "reflexion_ia": ""}],
            "checklist_completions": [{"fecha": "2026-06-18",
                                       "descripcion": "Tomar agua",
                                       "categoria": "Logro", "origen": "manual"}],
            "activation_results": [{"fecha": "2026-06-18", "hora": "13:00",
                                    "animo": 7,
                                    "actividad": "Caminar", "resultado": "hecha"}],
            "timer_sessions": [{"fecha": "2026-06-18", "hora": "14:00",
                                "nombre": "Pomodoro", "categoria": "Foco",
                                "duracion_config": 1500, "duracion_real": 1480,
                                "notas": ""}],
            "assigned_reminders": [{"id": 1, "hora": "09:00",
                                    "mensaje": "Tomar medicina", "activa": True}],
            "reminder_logs": [{"fecha": "2026-06-18", "hora": "09:00",
                               "mensaje": "Tomar medicina", "cerrado": True}],
            "dbt_practice_records": [{"fecha": "2026-06-18", "hora": "15:00",
                                      "skill_id": "wise_mind", "skill_version": 1,
                                      "familia": "mindfulness", "necesidad": "",
                                      "malestar_antes": 7, "malestar_despues": 4,
                                      "resultado": "ayudo", "duracion_seg": 300,
                                      "nota": ""}],
        }

    def table(self, name):
        self.calls.append(name)
        if name not in self._mock_data:
            raise Exception(f"Tabla inexistente consultada: {name}")
        return _FakeQuery(self._mock_data[name], name)


def test_fetch_patient_data_uses_real_table_names(qapp):
    """S0-1: el fetch solo consulta tablas reales de Supabase."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = _FakeSB()
    view._pid = "test-pid-123"
    view._nombre = "Test"

    datos = view._fetch_patient_data()

    # Las 4 tablas inexistentes NO deben aparecer en calls
    bad = {"animo_registros", "tcc_registros",
           "activacion_registros", "dbt_registros"}
    consultadas = set(view._sb.calls)
    assert not (bad & consultadas), (
        f"S0-1 regredió: se consultaron tablas inexistentes: {bad & consultadas}"
    )

    # Las 9 tablas reales SÍ deben consultarse (RB-3 agrega reminder_logs)
    good = {"mood_records", "breathing_sessions", "thought_records",
            "checklist_completions", "activation_results", "timer_sessions",
            "assigned_reminders", "dbt_practice_records", "reminder_logs"}
    assert good.issubset(consultadas), (
        f"Faltan tablas reales por consultar: {good - consultadas}"
    )


def test_fetch_patient_data_returns_data_for_all_8_modules(qapp):
    """S0-1: las 8 secciones del dict traen datos (no listas vacías)."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = _FakeSB()
    view._pid = "test-pid-123"
    view._nombre = "Test"

    datos = view._fetch_patient_data()

    expected_keys = {"animo", "respiracion", "tcc", "checklist",
                     "actividades", "timer", "recordatorios", "dbt",
                     "avisos_disparados"}
    assert set(datos.keys()) == expected_keys, (
        f"Keys inesperadas: {set(datos.keys()) ^ expected_keys}"
    )

    for key in expected_keys:
        assert len(datos[key]) > 0, (
            f"Módulo {key} vacío tras fetch — el fix S0-1 no está funcionando "
            "para esta tabla. Revisar que el nombre de la tabla en _fetch() "
            "coincida con db/supabase_schema.sql."
        )


def test_fetch_patient_data_includes_textual_fields(qapp):
    """S0-1 (+S1-1 adelantado): los campos textuales viajan, no solo id+fecha."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = _FakeSB()
    view._pid = "test-pid-123"
    view._nombre = "Test"

    datos = view._fetch_patient_data()

    # Verificar campos clave por módulo
    assert "pensamiento" in datos["tcc"][0], "TCC sin campo 'pensamiento'"
    assert "actividad" in datos["actividades"][0], "Actividades sin 'actividad'"
    assert "nota" in datos["dbt"][0], "DBT sin campo 'nota'"
    assert "malestar_antes" in datos["dbt"][0], "DBT sin 'malestar_antes'"
    assert "tecnica" in datos["respiracion"][0], "Respiración sin 'tecnica'"
    assert "descripcion" in datos["checklist"][0], "Checklist sin 'descripcion'"
    assert "nombre" in datos["timer"][0], "Timer sin 'nombre'"
    assert "emocion" in datos["animo"][0], "Ánimo sin 'emocion' (mood_valencia_migration)"


def test_fetch_patient_data_handles_missing_supabase_gracefully(qapp):
    """S0-1: si no hay cliente Supabase, devuelve dict con listas vacías."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = None  # sin cliente
    view._pid = "test-pid-123"
    view._nombre = "Test"

    datos = view._fetch_patient_data()

    expected_keys = {"animo", "respiracion", "tcc", "checklist",
                     "actividades", "timer", "recordatorios", "dbt",
                     "avisos_disparados"}
    assert set(datos.keys()) == expected_keys
    for key in expected_keys:
        assert datos[key] == [], f"{key} debería ser [] cuando no hay sb"


def test_fetch_patient_data_logs_on_table_error(qapp, caplog):
    """S0-1: si una tabla falla, se loguea (no se silencia con except: pass)."""
    import logging
    from hub.pacientes_qt import DetallePacienteView

    class _BrokenSB:
        def table(self, name):
            raise Exception("network error simulated")

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = _BrokenSB()
    view._pid = "test-pid-123"
    view._nombre = "Test"

    with caplog.at_level(logging.WARNING, logger="NeuroMoodHub.Pacientes"):
        datos = view._fetch_patient_data()

    # El dict se devuelve con listas vacías (fail-safe)
    for key in datos:
        assert datos[key] == []

    # Y se generaron warnings en el log
    assert any("fallo fetch" in r.message for r in caplog.records), (
        "Se esperaba al menos un warning de 'fallo fetch' en el log. "
        "El fix S0-1 reemplazó except: pass por logging.warning — verificar."
    )
