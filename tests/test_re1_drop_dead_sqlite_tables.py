from __future__ import annotations


RE1_DEAD_TABLES = {
    "checklist_snapshot",
    "mensajes_biblioteca",
    "activacion_config",
    "activacion_perfil",
    "timer_presets",
    "checklist_plantillas",
    "checklist_notas_dia",
}


def _existing_tables() -> set[str]:
    from shared.db import obtener_conexion

    conn = obtener_conexion()
    try:
        return {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        conn.close()


def test_re1_dead_tables_no_se_crean_en_db_nueva(isolated_db):
    assert not (RE1_DEAD_TABLES & _existing_tables())


def test_re1_dead_tables_se_eliminan_de_db_existente(isolated_db):
    from shared.db import conexion, inicializar_tablas

    with conexion() as conn:
        for table in RE1_DEAD_TABLES:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER)")

    assert RE1_DEAD_TABLES <= _existing_tables()

    inicializar_tablas()

    assert not (RE1_DEAD_TABLES & _existing_tables())
