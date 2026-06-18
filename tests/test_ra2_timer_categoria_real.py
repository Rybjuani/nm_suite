"""RA-2 smoke test: el módulo Timer persiste la categoria real del preset seleccionado.

Verifica que después del fix RA-2 (reauditoría UI-first):
1. `_preset_from_row` separa `categoria` de `description` (devuelve 4-tuple).
2. `_load_presets` devuelve `list[tuple[str, int, str, str]]` (name, secs, description, categoria).
3. `_select_preset` cachea la categoria en `self._current_categoria`.
4. La inicialización del módulo setea `self._current_categoria` con la categoria
   del preset inicial.
5. `_save_session` persiste `self._current_categoria` (no hardcodea "Timer").
6. `_preset_from_row` ya NO usa `payload.get("categoria")` como fallback de description.

## Contexto

El Hub envía `categoria` como campo separado en el payload de timer_presets_remote
(ver shared/sync.py:_importar_timer_presets). Antes de RA-2, `_preset_from_row`
mezclaba `categoria` dentro de `description` (línea 128: `or payload.get("categoria")`),
y `_save_session` hardcodeaba `"Timer"` en el INSERT — la categoria real se perdía.

RA-2 separa ambos campos y transporta la categoria explícitamente:
  payload → _preset_from_row → _load_presets → _select_preset →
  self._current_categoria → _save_session → actividades_temporizador.categoria

El profesional ahora verá las sesiones del paciente con la categoria real
(Foco, Descanso, etc.) en vez de "Timer" para todas.
"""
from __future__ import annotations

import os
import json
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest_plugins = ["pytestqt"]


# ─── Tests de _preset_from_row (separación de categoria y description) ────


def test_preset_from_row_devuelve_4_tuple_con_categoria_separada():
    """RA-2: _preset_from_row devuelve (name, secs, description, categoria).
    La categoria ya NO se mezcla con description."""
    from app.modules.timer_qt import _preset_from_row

    payload = {
        "name": "Lectura",
        "duracion_seg": 1500,
        "categoria": "Foco",
        "description": "Leer un libro 25 min",
        "activo": True,
    }
    row = type("R", (), {"__getitem__": lambda self, k: {"name": "Lectura", "payload": json.dumps(payload)}[k],
                          "keys": lambda self: ["name", "payload"]})()

    result = _preset_from_row(row)
    assert result is not None, "_preset_from_row devolvió None para un payload válido"
    assert len(result) == 4, (
        f"_preset_from_row debe devolver 4-tuple, got {len(result)}-tuple: {result!r}. "
        "RA-2 requiere separar categoria de description."
    )
    name, secs, description, categoria = result
    assert name == "Lectura"
    assert secs == 1500
    assert description == "Leer un libro 25 min"
    assert categoria == "Foco", (
        f"categoria debe ser 'Foco', got {categoria!r}. "
        "RA-2 requiere que categoria se lea de payload.get('categoria')."
    )


def test_preset_from_row_no_usa_categoria_como_fallback_de_description():
    """RA-2: si el payload tiene categoria pero NO description, description
    debe quedar vacía (no heredar categoria)."""
    from app.modules.timer_qt import _preset_from_row

    payload = {
        "name": "Pausa",
        "duracion_seg": 300,
        "categoria": "Descanso",
        "activo": True,
    }
    row = type("R", (), {"__getitem__": lambda self, k: {"name": "Pausa", "payload": json.dumps(payload)}[k],
                          "keys": lambda self: ["name", "payload"]})()

    result = _preset_from_row(row)
    assert result is not None
    name, secs, description, categoria = result
    assert description == "", (
        f"description debe ser '' cuando el payload no la tiene, got {description!r}. "
        "Antes de RA-2, _preset_from_row usaba payload.get('categoria') como "
        "fallback de description — eso disfrazaba la categoria de descripcion."
    )
    assert categoria == "Descanso"


def test_preset_from_row_categoria_vacia_si_no_esta_en_payload():
    """RA-2: si el payload no tiene categoria, se devuelve cadena vacía."""
    from app.modules.timer_qt import _preset_from_row

    payload = {
        "name": "Sin cat",
        "duracion_seg": 600,
        "description": "Solo descripcion",
        "activo": True,
    }
    row = type("R", (), {"__getitem__": lambda self, k: {"name": "Sin cat", "payload": json.dumps(payload)}[k],
                          "keys": lambda self: ["name", "payload"]})()

    result = _preset_from_row(row)
    assert result is not None
    name, secs, description, categoria = result
    assert categoria == ""
    assert description == "Solo descripcion"


# ─── Tests estructurales (no-regresión) ─────────────────────────────────


def test_preset_from_row_signature_es_4_tuple():
    """RA-2 (no-regresión estructural): el código fuente de _preset_from_row
    debe declarar que devuelve tuple[str, int, str, str] (4 elementos)."""
    import inspect
    from app.modules import timer_qt

    src = inspect.getsource(timer_qt._preset_from_row)
    assert "tuple[str, int, str, str]" in src, (
        "_preset_from_row no declara devolver tuple[str, int, str, str]. "
        "RA-2 requiere separar categoria de description → 4-tuple."
    )


def test_preset_from_row_no_mezcla_categoria_en_description():
    """RA-2: description no debe usar categoria como fallback."""
    import inspect
    from app.modules import timer_qt

    src = inspect.getsource(timer_qt._preset_from_row)
    start = src.find("description = (")
    end = src.find("categoria = payload.get", start)
    assert start >= 0 and end > start, (
        "No se pudo aislar el bloque description/categoria en _preset_from_row"
    )
    desc_block = src[start:end]
    assert 'payload.get("categoria")' not in desc_block, (
        "description sigue usando categoria como fallback"
    )


def test_load_presets_devuelve_4_tuple():
    """RA-2: _load_presets devuelve list[tuple[str, int, str, str]]."""
    import inspect
    from app.modules import timer_qt

    src = inspect.getsource(timer_qt._load_presets)
    assert "list[tuple[str, int, str, str]]" in src, (
        "_load_presets no declara devolver list[tuple[str, int, str, str]]."
    )


def test_select_preset_recibe_categoria():
    """RA-2: _select_preset acepta y cachea categoria explícitamente."""
    import inspect
    from app.modules import timer_qt

    fn = timer_qt.ModuloTimer._select_preset
    signature = inspect.signature(fn)
    assert "categoria" in signature.parameters
    src = inspect.getsource(fn)
    assert "self._current_categoria = categoria" in src


def test_save_session_no_hardcodea_timer():
    """RA-2: _save_session usa current_categoria y no el literal Timer."""
    import inspect
    import re
    from app.modules import timer_qt

    src = inspect.getsource(timer_qt.ModuloTimer._save_session)
    executable = re.sub(r"#.*$", "", src, flags=re.MULTILINE)
    assert '"Timer"' not in executable and "'Timer'" not in executable
    assert "self._current_categoria" in executable


# ─── Tests de integración con SQLite temporal ───────────────────────────


@pytest.fixture
def timer_module_with_temp_db(qapp, isolated_db, monkeypatch):
    """Construye ModuloTimer sin tocar el nm_data.db real.

    Pre-puebla timer_presets_cache con un preset que tiene categoria "Foco"
    para que el módulo tenga algo que cargar.
    """
    from app.modules.timer_qt import ModuloTimer
    from shared.db import conexion, guardar_config

    guardar_config("patient_id", "test-patient-123")

    payload = json.dumps({
        "name": "Lectura",
        "duracion_seg": 1500,
        "categoria": "Foco",
        "description": "Leer 25 min",
        "activo": True,
        "orden": 1,
    })
    with conexion() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO timer_presets_cache (id, scope, name, payload) "
            "VALUES (?, ?, ?, ?)",
            (1, "patient:test-patient-123", "Lectura", payload),
        )

    sync_mock = patch("shared.sync.sync_inmediato_background", autospec=True)
    sync_mock.start()

    mod = ModuloTimer(modo="dark_hybrid", show_header=False)
    mod.resize(960, 600)
    mod.show()
    for _ in range(5):
        qapp.processEvents()

    yield mod

    mod.close()
    mod.deleteLater()
    qapp.processEvents()
    sync_mock.stop()


def test_save_session_persiste_categoria_real_del_preset(timer_module_with_temp_db):
    """RA-2: tras _save_session, actividades_temporizador.categoria debe ser
    la categoria real del preset ('Foco'), no 'Timer'."""
    mod = timer_module_with_temp_db

    assert mod._current_categoria == "Foco", (
        f"self._current_categoria debería ser 'Foco' (del preset), "
        f"got {mod._current_categoria!r}"
    )

    mod._save_session(1500)

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT nombre, categoria, duracion_config, duracion_real "
        "FROM actividades_temporizador ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None, "No se persistió la sesión"
    assert row["categoria"] == "Foco", (
        f"categoria persistida debe ser 'Foco', got {row['categoria']!r}. "
        "Antes de RA-2, _save_session hardcodeaba 'Timer'."
    )
    assert row["nombre"] == "Lectura"
    assert row["duracion_config"] == 1500
    assert row["duracion_real"] == 1500


def test_select_preset_actualiza_current_categoria(timer_module_with_temp_db):
    """RA-2: al llamar _select_preset, self._current_categoria se actualiza."""
    mod = timer_module_with_temp_db

    mod._select_preset("Pausa activa", 300, "Descanso")

    assert mod._current_categoria == "Descanso", (
        f"self._current_categoria debería ser 'Descanso' tras _select_preset, "
        f"got {mod._current_categoria!r}"
    )

    mod._save_session(300)

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT categoria FROM actividades_temporizador ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row["categoria"] == "Descanso"


def test_save_session_categoria_vacia_si_no_hay_preset(isolated_db, qapp, monkeypatch):
    """RA-2: si no hay preset seleccionado, categoria se persiste como ''
    (no como 'Timer'). Caso edge: módulo sin asignaciones."""
    from app.modules.timer_qt import ModuloTimer
    from shared.db import guardar_config

    guardar_config("patient_id", "")

    sync_mock = patch("shared.sync.sync_inmediato_background", autospec=True)
    sync_mock.start()

    mod = ModuloTimer(modo="dark_hybrid", show_header=False)
    mod.resize(960, 600)
    mod.show()
    for _ in range(5):
        qapp.processEvents()

    try:
        assert mod._current_categoria == ""

        mod._ent_actividad.setText("Actividad manual")
        mod._save_session(60)

        from shared.db import obtener_conexion

        conn = obtener_conexion()
        row = conn.execute(
            "SELECT categoria FROM actividades_temporizador ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        if row is not None:
            assert row["categoria"] == "", (
                f"categoria debe ser '' cuando no hay preset, got {row['categoria']!r}. "
                "RA-2: no debe hardcodear 'Timer'."
            )
    finally:
        mod.close()
        mod.deleteLater()
        qapp.processEvents()
        sync_mock.stop()


def test_save_session_no_rompe_para_multiples_sesiones(timer_module_with_temp_db):
    """RA-2 (smoke): _save_session funciona para múltiples sesiones seguidas."""
    mod = timer_module_with_temp_db

    for i in range(3):
        mod._save_session(1500)

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    count = conn.execute("SELECT COUNT(*) AS n FROM actividades_temporizador").fetchone()["n"]
    conn.close()

    assert count == 3, f"Debería haber 3 sesiones, hay {count}"


# ─── Test del flujo completo payload → INSERT ──────────────────────────


def test_flujo_completo_payload_a_insert(qapp, isolated_db, monkeypatch):
    """RA-2 (integración end-to-end): un payload con categoria="Foco" del
    Hub termina persistido como categoria="Foco" en actividades_temporizador."""
    from app.modules.timer_qt import ModuloTimer, _preset_from_row
    from shared.db import conexion, guardar_config, obtener_conexion
    from unittest.mock import patch

    guardar_config("patient_id", "test-flujo-123")

    payload = json.dumps({
        "name": "Trabajo profundo",
        "duracion_seg": 2700,
        "categoria": "Foco",
        "description": "45 min de concentración",
        "activo": True,
        "orden": 1,
    })
    with conexion() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO timer_presets_cache (id, scope, name, payload) "
            "VALUES (?, ?, ?, ?)",
            (1, "patient:test-flujo-123", "Trabajo profundo", payload),
        )

    sync_mock = patch("shared.sync.sync_inmediato_background", autospec=True)
    sync_mock.start()

    try:
        mod = ModuloTimer(modo="dark_hybrid", show_header=False)
        mod.resize(960, 600)
        mod.show()
        for _ in range(5):
            qapp.processEvents()

        assert mod._current_categoria == "Foco", (
            f"Esperado 'Foco', got {mod._current_categoria!r}"
        )

        mod._save_session(2700)

        conn = obtener_conexion()
        row = conn.execute(
            "SELECT nombre, categoria FROM actividades_temporizador ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["nombre"] == "Trabajo profundo"
        assert row["categoria"] == "Foco", (
            f"categoria persistida debe ser 'Foco', got {row['categoria']!r}. "
            "El flujo completo payload → _preset_from_row → _load_presets → "
            "_select_preset → self._current_categoria → _save_session → INSERT "
            "no está transportando la categoria correctamente."
        )

        mod.close()
        mod.deleteLater()
        qapp.processEvents()
    finally:
        sync_mock.stop()
