"""RA-5: skill_version se persiste desde DBT_SKILLS, no hardcodeado.

DBT_SKILLS declara `version` en cada skill (todas en 1 hoy, pero el campo
existe como contrato). Antes de RA-5, _on_practice_saved hardcodeaba `1`
en el INSERT a dbt_practicas, ignorando skill["version"]. Si una skill se
revisa a version=2, el registro quedaba inconsistente.

RA-5 cachea `skill.get("version", 1)` en start_practice y lo usa en el INSERT.
"""
from __future__ import annotations

import inspect

import pytest

# Nota: pytest_plugins y QT_QPA_PLATFORM ya están en tests/conftest.py (S0-9).
# No duplicar acá.


def test_start_practice_cachea_skill_version():
    """RA-5: start_practice debe asignar self._current_skill_version desde
    skill.get("version", 1)."""
    from app.modules import dbt_qt

    src = inspect.getsource(dbt_qt.ModuloDBT.start_practice)
    assert 'skill.get("version"' in src, (
        "start_practice no llama skill.get('version', 1). "
        "RA-5 requiere cachear la version canónica desde DBT_SKILLS."
    )
    assert "self._current_skill_version" in src


def test_insert_usa_current_skill_version_no_hardcodea_1():
    """RA-5: el INSERT en _on_practice_saved usa self._current_skill_version,
    no el literal 1 entre skill_id y family."""
    from app.modules import dbt_qt

    src = inspect.getsource(dbt_qt.ModuloDBT._on_practice_saved)
    assert "self._current_skill_id, 1," not in src, (
        "INSERT sigue hardcodeando 1 para skill_version. "
        "RA-5 requiere usar self._current_skill_version."
    )
    assert "self._current_skill_version" in src


def test_dbt_skills_todas_tienen_version():
    """RA-5 (verificación de fuente canónica): todas las skills en DBT_SKILLS
    declaran `version` entera >= 1."""
    from app.modules.dbt_qt import DBT_SKILLS

    assert len(DBT_SKILLS) > 0
    for skill_id, skill in DBT_SKILLS.items():
        assert "version" in skill, (
            f"Skill {skill_id!r} no declara version. "
            "RA-5 usa skill.get('version', 1); si falta, persistiría 1 silenciosamente."
        )
        assert isinstance(skill["version"], int)
        assert skill["version"] >= 1


@pytest.fixture
def dbt_module_with_temp_db(qapp, isolated_db):
    """Construye ModuloDBT sin tocar nm_data.db real."""
    from unittest.mock import patch
    from app.modules.dbt_qt import ModuloDBT

    sync_mock = patch("shared.sync.sync_inmediato_background", autospec=True)
    sync_mock.start()

    mod = ModuloDBT(modo="dark_hybrid", show_header=False)
    mod.resize(960, 600)
    mod.show()
    for _ in range(5):
        qapp.processEvents()

    yield mod

    mod.close()
    mod.deleteLater()
    qapp.processEvents()
    sync_mock.stop()


def test_skill_version_2_se_persiste_real(dbt_module_with_temp_db):
    """RA-5 (test clave): inyectar una skill hipotética con version=2 y
    demostrar que SQLite persiste 2 (no 1 hardcodeado).

    Este test es el que valida que el fix realmente transporta el valor
    canónico hasta la DB. Si el INSERT sigue hardcodeando 1, este test
    falla con skill_version=1 en vez de 2.
    """
    from shared.db import obtener_conexion
    from app.modules.dbt_qt import DBT_SKILLS

    mod = dbt_module_with_temp_db

    # Tomar una skill real del catálogo y forzar version=2 (simula
    # una revisión clínica futura de la skill)
    skill = dict(DBT_SKILLS["observe_describe"])  # copia para no mutar el catálogo
    skill["version"] = 2  # inyección hipotética

    mod.start_practice(skill)
    assert mod._current_skill_version == 2, (
        f"start_practice no cacheó version=2, got {mod._current_skill_version!r}"
    )

    mod._on_practice_saved(antes=7, despues=4, resultado="ayudo", nota="")

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT skill_id, skill_version FROM dbt_practicas "
        "ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None, "No se persistió la práctica"
    assert row["skill_id"] == "observe_describe"
    assert row["skill_version"] == 2, (
        f"SQLite persistió skill_version={row['skill_version']!r}, esperado 2. "
        "Si el INSERT sigue hardcodeando 1, el fix RA-5 no aplicó."
    )


def test_skill_version_1_se_persiste_para_skills_reales(dbt_module_with_temp_db):
    """RA-5 (regresión): las skills reales de DBT_SKILLS (todas version=1)
    siguen persistiéndose con skill_version=1. Confirma que el fix no rompe
    el caso normal."""
    from shared.db import obtener_conexion
    from app.modules.dbt_qt import DBT_SKILLS

    mod = dbt_module_with_temp_db

    skill = DBT_SKILLS["stop"]  # version=1
    mod.start_practice(skill)
    mod._on_practice_saved(7, 4, "ayudo", "")

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT skill_version FROM dbt_practicas "
        "ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row["skill_version"] == 1


def test_skill_version_se_actualiza_al_cambiar_skill(dbt_module_with_temp_db):
    """RA-5: si el usuario practica skill A (version=1) y luego skill B
    (version=2 hipotética), cada práctica queda con su version correcta."""
    from shared.db import obtener_conexion
    from app.modules.dbt_qt import DBT_SKILLS

    mod = dbt_module_with_temp_db

    # Skill A: real, version=1
    skill_a = DBT_SKILLS["observe_describe"]
    mod.start_practice(skill_a)
    mod._on_practice_saved(7, 4, "ayudo", "")

    # Skill B: misma skill forzada a version=2
    skill_b = dict(DBT_SKILLS["observe_describe"])
    skill_b["version"] = 2
    mod.start_practice(skill_b)
    mod._on_practice_saved(6, 5, "parcial", "")

    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT skill_version FROM dbt_practicas "
        "ORDER BY created_at DESC LIMIT 2"
    ).fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0]["skill_version"] == 2  # la más nueva primero
    assert rows[1]["skill_version"] == 1
