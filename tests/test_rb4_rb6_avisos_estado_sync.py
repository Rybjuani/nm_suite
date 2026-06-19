from __future__ import annotations

import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch


def _insert_recordatorio(hora="09:00", mensaje="Tomar agua", activo=1, completado_en=None):
    from shared.db import conexion

    with conexion() as conn:
        cur = conn.execute(
            "INSERT INTO recordatorios (hora, mensaje, dias, activo, completado_en) "
            "VALUES (?, ?, ?, ?, ?)",
            (hora, mensaje, "1,2,3,4,5,6,7", activo, completado_en),
        )
        return cur.lastrowid


def _latest_recordatorio(hora="09:00", mensaje="Tomar agua"):
    from shared.db import obtener_conexion

    conn = obtener_conexion()
    try:
        return conn.execute(
            "SELECT hora, mensaje, activo, completado_en FROM recordatorios "
            "WHERE hora = ? AND mensaje = ?",
            (hora, mensaje),
        ).fetchone()
    finally:
        conn.close()


class _FakeUpdateQuery:
    def __init__(self, sink):
        self._sink = sink
        self._payload = None
        self._filters = []

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def execute(self):
        self._sink.append({"payload": self._payload, "filters": list(self._filters)})
        return SimpleNamespace(data=[])


class _FakeUpdateSupabase:
    def __init__(self):
        self.updates = []

    def table(self, name):
        assert name == "assigned_reminders"
        return _FakeUpdateQuery(self.updates)


class _FakeSelectQuery:
    def __init__(self, data):
        self._data = data
        self.select_arg = None
        self.eq_calls = []

    def select(self, columns):
        self.select_arg = columns
        return self

    def eq(self, column, value):
        self.eq_calls.append((column, value))
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


class _FakeSelectSupabase:
    def __init__(self, data):
        self.query = _FakeSelectQuery(data)

    def table(self, name):
        assert name == "assigned_reminders"
        return self.query


def _now_local_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def test_completar_aviso_persiste_inactivo_y_timestamp(isolated_db, monkeypatch):
    from app.modules import avisos_qt
    from app.modules.avisos_qt import ModuloAvisos

    rec_id = _insert_recordatorio()
    mod = object()
    monkeypatch.setattr(avisos_qt, "visual_qa_enabled", lambda: False)

    assert ModuloAvisos._toggle_active(mod, rec_id, False) is True

    row = _latest_recordatorio()
    assert row["activo"] == 0
    assert row["completado_en"]


def test_on_completar_dispara_sync_inmediato_si_guardo(monkeypatch):
    from app.modules.avisos_qt import ModuloAvisos, NMToast

    class _DummyModulo:
        pass

    mod = _DummyModulo()
    mod._toggle_active = Mock(return_value=True)
    mod._load_reminders = Mock()
    mod._sync_inmediato_background = lambda: ModuloAvisos._sync_inmediato_background(mod)
    mod.window = Mock(return_value=None)

    with (
        patch("shared.sync.sync_inmediato_background") as sync_mock,
        patch.object(NMToast, "display"),
    ):
        ModuloAvisos._on_completar(mod, 123)

    mod._toggle_active.assert_called_once_with(123, False)
    mod._load_reminders.assert_called_once()
    sync_mock.assert_called_once()


def test_on_completar_no_propaga_error_de_sync(monkeypatch):
    from app.modules.avisos_qt import ModuloAvisos, NMToast

    class _DummyModulo:
        pass

    mod = _DummyModulo()
    mod._toggle_active = Mock(return_value=True)
    mod._load_reminders = Mock()
    mod._sync_inmediato_background = lambda: ModuloAvisos._sync_inmediato_background(mod)
    mod.window = Mock(return_value=None)

    with (
        patch("shared.sync.sync_inmediato_background", side_effect=RuntimeError("red")),
        patch.object(NMToast, "display"),
    ):
        ModuloAvisos._on_completar(mod, 123)


def test_exportar_recordatorios_estado_actualiza_completado_en_sin_upsert(isolated_db):
    import shared.sync as sync_module

    completed_at = _now_local_iso()
    _insert_recordatorio(hora="08:00", mensaje="Activo", activo=1, completado_en=completed_at)
    _insert_recordatorio(hora="09:00", mensaje="Completo", activo=0, completado_en=completed_at)
    sb = _FakeUpdateSupabase()

    sync_module._exportar_recordatorios_estado(sb, "patient-1", "2026-01-01")

    assert sb.updates == [
        {
            "payload": {"completado_en": None},
            "filters": [
                ("patient_id", "patient-1"),
                ("hora", "08:00"),
                ("mensaje", "Activo"),
            ],
        },
        {
            "payload": {"completado_en": completed_at},
            "filters": [
                ("patient_id", "patient-1"),
                ("hora", "09:00"),
                ("mensaje", "Completo"),
            ],
        },
    ]


def test_importar_recordatorios_asignados_respeta_completado_hoy(isolated_db):
    import shared.sync as sync_module

    completed_at = _now_local_iso()
    sb = _FakeSelectSupabase(
        [
            {
                "hora": "09:00",
                "mensaje": "Tomar agua",
                "dias": "1,2,3",
                "completado_en": completed_at,
            }
        ]
    )

    sync_module._importar_recordatorios_asignados(sb, "patient-1")

    row = _latest_recordatorio()
    assert row["activo"] == 0
    assert row["completado_en"] == completed_at
    assert ("patient_id", "patient-1") in sb.query.eq_calls
    assert ("activa", True) in sb.query.eq_calls


def test_importar_recordatorios_asignados_reactiva_completado_viejo(isolated_db):
    import shared.sync as sync_module

    completed_at = (
        datetime.datetime.now().astimezone() - datetime.timedelta(days=1)
    ).isoformat(timespec="seconds")
    sb = _FakeSelectSupabase(
        [
            {
                "hora": "09:00",
                "mensaje": "Tomar agua",
                "dias": "1,2,3",
                "completado_en": completed_at,
            }
        ]
    )

    sync_module._importar_recordatorios_asignados(sb, "patient-1")

    row = _latest_recordatorio()
    assert row["activo"] == 1
    assert row["completado_en"] is None


def test_importar_recordatorios_asignados_preserva_completado_local_pendiente(isolated_db):
    import shared.sync as sync_module

    local_completed_at = _now_local_iso()
    _insert_recordatorio(
        hora="09:00",
        mensaje="Tomar agua",
        activo=0,
        completado_en=local_completed_at,
    )
    sb = _FakeSelectSupabase(
        [
            {
                "hora": "09:00",
                "mensaje": "Tomar agua",
                "dias": "1,2,3",
                "completado_en": None,
            }
        ]
    )

    sync_module._importar_recordatorios_asignados(sb, "patient-1")

    row = _latest_recordatorio()
    assert row["activo"] == 0
    assert row["completado_en"] == local_completed_at
