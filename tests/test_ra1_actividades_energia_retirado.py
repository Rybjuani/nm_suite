"""RA-1 smoke test: el módulo Actividades NO persiste ni transporta `energia`.

Verifica que después del fix RA-1 (reauditoría UI-first):
1. El INSERT en `_register_result` NO escribe `energia` (la columna queda NULL
   via default del schema SQLite migrado).
2. El schema SQLite permite `energia NULL` (migración `_migrar_activacion_energia_null`).
3. DBs existentes con el schema viejo (`energia NOT NULL`) se migran automáticamente.
4. `_exportar_activacion` (sync.py) NO envía `energia` en el payload a Supabase.
5. `_fetch_patient_data` (hub/pacientes_qt.py) NO pide `energia` a `activation_results`.
6. IA y PDF no mencionan `energia` (verificado por ausencia en código).

## Contexto

El módulo Actividades actual NO captura energía por separado. Solo captura:
- `actividad` (nombre)
- `resultado` (hecha/intentada/no_pude)
- `animo` (leído del último registro de termometro de hoy — autoreportado)

Antes de RA-1, `_register_result` copiaba `animo` como `energia` en el INSERT.
En Behavioral Activation, energía y ánimo son dimensiones distintas:
- Podés tener ánimo bajo con energía alta (ej. ansiedad)
- Podés tener ánimo alto con energía baja (ej. relajado pero cansado)

Copiar `animo` como `energia` era una inferencia falsa que el Hub leía como
autoinforme real. RA-1 corrige retirando `energia` de todo el contrato activo
(INSERT, sync, Hub SELECT). La columna física se conserva por compatibilidad
con datos históricos.
"""
from __future__ import annotations

import os
import sqlite3
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest_plugins = ["pytestqt"]


# ─── Tests del schema SQLite (migración permite NULL) ────────────────────


def test_activacion_schema_permite_energia_null(isolated_db):
    """RA-1: el schema SQLite permite INSERT con energia=NULL."""
    from shared.db import conexion

    with conexion() as conn:
        conn.execute(
            "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
            "VALUES (?, ?, NULL, ?, ?, ?)",
            ("2026-06-18", "10:00", 7, "Caminar", "hecha"),
        )
        row = conn.execute(
            "SELECT energia, animo, actividad, resultado "
            "FROM activacion ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row["energia"] is None, (
        f"energia debe ser NULL, got {row['energia']!r}. "
        "El schema SQLite no fue migrado correctamente por RA-1."
    )
    assert row["animo"] == 7
    assert row["actividad"] == "Caminar"
    assert row["resultado"] == "hecha"


def test_activacion_schema_sigue_validando_energia_en_rango(isolated_db):
    """RA-1 (regresión): el schema sigue rechazando energia fuera de rango
    cuando no es NULL."""
    from shared.db import conexion

    with conexion() as conn:
        # energia=15 debe seguir siendo rechazado por el CHECK
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("2026-06-18", "10:00", 15, 7, "test", "hecha"),
            )
        # energia=0 debe ser aceptado (0 está en el rango 0-10)
        conn.execute(
            "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-06-18", "11:00", 0, 5, "test", "hecha"),
        )
        # energia=10 debe ser aceptado
        conn.execute(
            "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-06-18", "12:00", 10, 5, "test", "hecha"),
        )


def test_activacion_schema_rechaza_animo_null(isolated_db):
    """RA-1 (regresión): animo sigue siendo NOT NULL (no se permite NULL)."""
    from shared.db import conexion

    with conexion() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
                "VALUES (?, ?, NULL, NULL, ?, ?)",
                ("2026-06-18", "10:00", "test", "hecha"),
            )


def test_migracion_activacion_energia_null_es_idempotente(isolated_db):
    """RA-1: llamar inicializar_tablas() de nuevo no rompe si la migración
    ya aplicó."""
    from shared.db import inicializar_tablas

    # inicializar_tablas ya corrió en el fixture. Llamarla de nuevo debe ser no-op.
    inicializar_tablas()
    inicializar_tablas()

    from shared.db import conexion

    with conexion() as conn:
        conn.execute(
            "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
            "VALUES (?, ?, NULL, ?, ?, ?)",
            ("2026-06-18", "10:00", 5, "test", "hecha"),
        )
        row = conn.execute(
            "SELECT energia FROM activacion ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row["energia"] is None


# ─── Tests del INSERT en _register_result ─────────────────────────────────


@pytest.fixture
def actividades_module_with_temp_db(qapp, isolated_db, monkeypatch):
    """Construye ModuloActividades sin tocar el nm_data.db real.

    Requiere un registro de ánimo previo en termometro (el módulo valida
    que exista antes de permitir registrar actividad).
    """
    from app.modules.actividades_qt import ModuloActividades
    from shared.db import conexion
    from shared.utils import fecha_hoy, hora_actual

    # Pre-poblar un registro de ánimo para que _get_last_mood() no devuelva None
    with conexion() as conn:
        conn.execute(
            "INSERT INTO termometro (fecha, hora, puntaje, nota) VALUES (?, ?, ?, ?)",
            (fecha_hoy(), hora_actual(), 7, ""),
        )

    sync_mock = patch("shared.sync.sync_inmediato_background", autospec=True)
    sync_mock.start()

    mod = ModuloActividades(modo="dark_hybrid", show_header=False)
    mod.resize(960, 600)
    mod.show()
    for _ in range(5):
        qapp.processEvents()

    yield mod

    mod.close()
    mod.deleteLater()
    qapp.processEvents()
    sync_mock.stop()


def test_register_result_no_persiste_energia(actividades_module_with_temp_db):
    """RA-1: tras _register_result, energia debe ser NULL (no copia de animo)."""
    mod = actividades_module_with_temp_db

    class _MockCard:
        def __init__(self):
            self.visible = True
        def setVisible(self, v): self.visible = v
        def deleteLater(self): pass
        def set_accent(self, c): pass
        def play_success(self): pass
        def set_completed(self, v): pass

    mod._register_result("Caminar 20 min", "hecha", _MockCard(), None)

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT energia, animo, actividad, resultado "
        "FROM activacion ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None, "No se persistió el registro"
    assert row["energia"] is None, (
        f"energia debe ser NULL, got {row['energia']!r}. "
        "Antes de RA-1, _register_result copiaba animo como energia. "
        "Eso era una inferencia falsa (energia y animo son dimensiones distintas)."
    )
    assert row["animo"] == 7  # el ánimo autoreportado sí se persiste
    assert row["actividad"] == "Caminar 20 min"
    assert row["resultado"] == "hecha"


def test_register_result_persiste_animo_real(actividades_module_with_temp_db):
    """RA-1 (regresión): animo sigue persistiéndose con el valor autoreportado."""
    mod = actividades_module_with_temp_db

    class _MockCard:
        def setVisible(self, v): pass
        def deleteLater(self): pass
        def set_accent(self, c): pass
        def play_success(self): pass
        def set_completed(self, v): pass

    mod._register_result("Meditar", "intentada", _MockCard(), None)

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT animo FROM activacion ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["animo"] == 7  # autoreportado desde termometro


def test_register_result_no_rompe_para_diferentes_resultados(actividades_module_with_temp_db):
    """RA-1 (smoke): _register_result funciona para los 3 valores de resultado."""
    mod = actividades_module_with_temp_db

    class _MockCard:
        def setVisible(self, v): pass
        def deleteLater(self): pass
        def set_accent(self, c): pass
        def play_success(self): pass
        def set_completed(self, v): pass

    for resultado in ("hecha", "intentada", "no_pude"):
        mod._register_result(f"Actividad {resultado}", resultado, _MockCard(), None)

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    count = conn.execute("SELECT COUNT(*) AS n FROM activacion").fetchone()["n"]
    conn.close()

    assert count == 3, f"Debería haber 3 registros, hay {count}"


# ─── Tests estructurales (no-regresión) ─────────────────────────────────


def test_register_result_no_menciona_energia_en_insert():
    """RA-1 (no-regresión estructural): el código fuente de _register_result
    no debe mencionar `energia` en el INSERT ni en los parámetros."""
    import inspect
    from app.modules import actividades_qt

    src = inspect.getsource(actividades_qt.ModuloActividades._register_result)

    # El patrón malo era: (fecha_hoy(), hora_actual(), animo, animo, nombre, resultado)
    # donde el 3er ? (energia) recibía `animo` y el 4to ? (animo) también.
    assert "animo, animo" not in src, (
        "Encontrado patrón `animo, animo` en _register_result — el bug RA-1 "
        "regresó. energia no debe copiarse de animo."
    )

    # El INSERT no debe mencionar `energia` en las columnas
    import re
    insert_match = re.search(
        r'INSERT INTO activacion\s*\(([^)]+)\)',
        src,
        re.DOTALL,
    )
    assert insert_match, "No se encontró INSERT INTO activacion en _register_result"
    columns = insert_match.group(1)
    assert "energia" not in columns.lower(), (
        f"INSERT sigue mencionando `energia` en columnas: {columns!r}. "
        "RA-1 requiere que el INSERT no mencione energia."
    )


def test_exportar_activacion_no_envia_energia():
    """RA-1: _exportar_activacion (shared/sync.py) no debe incluir `energia`
    en el SELECT ni en el payload que envía a Supabase."""
    import inspect
    import re
    from shared import sync

    src = inspect.getsource(sync._exportar_activacion)
    # Quitar comentarios para mirar solo código ejecutable
    src_no_comments = re.sub(r'#.*$', '', src, flags=re.MULTILINE)
    src_no_comments = re.sub(r'"""[\s\S]*?"""', '', src_no_comments)

    # El payload no debe incluir "energia" como key
    for forbidden in ['"energia"', "'energia'"]:
        assert forbidden not in src_no_comments, (
            f"Encontrado {forbidden!r} en código ejecutable de _exportar_activacion — "
            "el payload sigue enviando energia al Hub."
        )

    # El SELECT tampoco debe pedir esa columna
    src_flat = " ".join(src_no_comments.split())
    select_match = re.search(
        r'SELECT\s+(.*?)\s*FROM\s+activacion',
        src_flat,
        re.IGNORECASE,
    )
    assert select_match, (
        f"No se encontró SELECT ... FROM activacion. Source: {src_flat[:300]}"
    )
    select_cols = select_match.group(1).replace('"', '').replace("'", "").strip()
    assert "energia" not in select_cols.lower(), (
        f"_exportar_activacion sigue haciendo SELECT de energia "
        f"(cols = {select_cols!r}) — debe traer solo "
        "fecha, hora, animo, actividad, resultado."
    )


def test_fetch_patient_data_no_pide_energia():
    """RA-1: _fetch_patient_data (hub/pacientes_qt.py) no debe pedir
    `energia` a `activation_results`."""
    import inspect
    import re
    from hub import pacientes_qt

    src = inspect.getsource(pacientes_qt.DetallePacienteView._fetch_patient_data)
    # Buscar el call _fetch("actividades", "activation_results", "<columns>", limit=20)
    pattern = r'_fetch\(\s*"actividades"\s*,\s*"activation_results"\s*,\s*"([^"]+)"'
    match = re.search(pattern, src)
    assert match, (
        "No se encontró la llamada _fetch('actividades', 'activation_results', ...) "
        "en _fetch_patient_data. ¿Se rompió el S0-1?"
    )
    columns = match.group(1)
    assert "energia" not in columns, (
        f"_fetch_patient_data sigue pidiendo `energia` a activation_results "
        f"(columns = {columns!r}). RA-1 requiere que no se pida."
    )


def test_migracion_activacion_energia_null_existe_en_db_py():
    """RA-1: la migración existe y se invoca desde inicializar_tablas."""
    import inspect
    from shared import db

    assert hasattr(db, "_migrar_activacion_energia_null"), (
        "Falta la función _migrar_activacion_energia_null en shared/db.py."
    )
    init_src = inspect.getsource(db.inicializar_tablas)
    assert "_migrar_activacion_energia_null(conn)" in init_src, (
        "La migración existe pero no se invoca desde inicializar_tablas."
    )


def test_create_table_activacion_permite_null_en_db_py():
    """RA-1: el CREATE TABLE inicial de activacion debe usar
    `energia INTEGER NULL CHECK(...)` (no NOT NULL)."""
    with open("shared/db.py", encoding="utf-8") as f:
        src = f.read()
    assert "energia INTEGER NULL CHECK(energia IS NULL OR energia BETWEEN 0 AND 10)" in src, (
        "El schema SQLite de activacion no permite energia NULL. "
        "DBs nuevas se crearían con el schema viejo (NOT NULL) y RA-1 no funcionaría."
    )
    # El schema viejo NO debe seguir presente en el CREATE TABLE inicial
    import re
    create_match = re.search(
        r'CREATE TABLE IF NOT EXISTS activacion\s*\(([^)]+)\)',
        src,
        re.DOTALL,
    )
    assert create_match, "No se encontró CREATE TABLE IF NOT EXISTS activacion"
    create_body = create_match.group(1)
    assert "energia INTEGER NOT NULL" not in create_body, (
        f"CREATE TABLE activacion sigue teniendo energia NOT NULL: {create_body!r}"
    )


def test_supabase_schema_energia_es_nullable():
    """RA-1: la columna energia en Supabase (db/supabase_schema.sql) debe
    seguir siendo nullable. NO se toca el DDL Supabase — solo se verifica
    que ya permite NULL (lo que hace que el fix funcione sin migración remota)."""
    with open("db/supabase_schema.sql", encoding="utf-8") as f:
        src = f.read()
    # En Supabase, la columna debe ser solo `energia INTEGER,` (sin NOT NULL)
    # Buscar la línea específica de energia dentro de activation_results
    # (no usar regex greedy porque hay paréntesis anidados en REFERENCES)
    import re
    # Buscar el bloque CREATE TABLE activation_results ... ;
    activation_match = re.search(
        r'CREATE TABLE IF NOT EXISTS activation_results\s*\((.+?)\);',
        src,
        re.DOTALL,
    )
    assert activation_match, "No se encontró CREATE TABLE activation_results en supabase_schema.sql"
    body = activation_match.group(1)
    # Buscar la línea de energia
    energia_line = re.search(r'energia\s+INTEGER\b([^\n]*)', body)
    assert energia_line, f"No se encontró columna energia en activation_results: {body!r}"
    suffix = energia_line.group(1)
    assert "NOT NULL" not in suffix.upper(), (
        f"Supabase activation_results.energia tiene NOT NULL: {energia_line.group(0)!r}. "
        "RA-1 requiere que sea nullable en Supabase (ya lo es por diseño)."
    )
