"""S0-2-bis smoke test: el módulo Ánimo NO persiste emocion/valencia/intensidad.

Verifica que después del fix S0-2-bis:
1. `_registrar()` solo escribe (fecha, hora, puntaje, nota) en `termometro`.
   No-popula emocion/valencia/intensidad porque el módulo actual (escala
   única 1-10) no los captura.
2. SQLite aplica defaults del schema: emocion='', valencia='', intensidad=NULL.
3. El payload de `_exportar_animo` (shared/sync.py) NO incluye esos campos.
4. El SELECT de `_fetch_patient_data` (hub/pacientes_qt.py) NO los pide.
5. El backfill legacy de shared/db.py fue eliminado (no vuelve a inferir
   valencia/intensidad de un set de emociones legacy que el módulo no captura).

## Contexto

El S0-2 original intentó _derivar_ valencia y emocion del puntaje usando
_mood_care() y MOOD_PALETTE — eso fue incorrecto: el paciente solo elige un
puntaje 1-10, no elige emoción ni valencia. Cualquier valor derivado sería
autoinforme falso. S0-2-bis corrige el error: dejar de persistir los campos
que el módulo no captura.

Las columnas se conservan por compatibilidad con datos históricos.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest_plugins = ["pytestqt"]


# ─── Tests del INSERT en _registrar (no persiste campos sin captura) ─────


@pytest.fixture
def animo_module_with_temp_db(qapp, isolated_db, monkeypatch):
    """Construye ModuloAnimo sin tocar el nm_data.db real."""
    from app.modules.animo_qt import ModuloAnimo

    sync_mock = patch("shared.sync.sync_inmediato_background", autospec=True)
    sync_mock.start()

    mod = ModuloAnimo(modo="dark_hybrid", show_header=False)
    mod.resize(960, 600)
    mod.show()
    for _ in range(5):
        qapp.processEvents()

    yield mod

    mod.close()
    mod.deleteLater()
    qapp.processEvents()
    sync_mock.stop()


def test_registrar_no_persiste_emocion(animo_module_with_temp_db):
    """S0-2-bis: tras registrar, emocion debe ser '' (default), no un nombre inventado."""
    mod = animo_module_with_temp_db

    mod._v3_slider.set_level(7)
    mod._btn_reg.click()

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT emocion FROM termometro ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["emocion"] == "", (
        f"emocion debe ser '' (default, sin captura), got {row['emocion']!r}. "
        "El módulo actual de Ánimo no captura emocion — persistirla con un "
        "valor derivado sería autoinforme falso."
    )


def test_registrar_no_persiste_valencia(animo_module_with_temp_db):
    """S0-2-bis: tras registrar, valencia debe ser '' (default), no 'positiva'/'neutral'/'negativa'."""
    mod = animo_module_with_temp_db

    mod._v3_slider.set_level(2)  # nivel bajo
    mod._btn_reg.click()

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT valencia FROM termometro ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["valencia"] == "", (
        f"valencia debe ser '' (default, sin captura), got {row['valencia']!r}. "
        "Antes del fix, _registrar hardcodeaba 'positiva'. Después del S0-2 "
        "original (rechazado), derivaba del puntaje. Ambos eran incorrectos: "
        "el módulo actual no captura valencia."
    )


def test_registrar_no_persiste_intensidad(animo_module_with_temp_db):
    """S0-2-bis: tras registrar, intensidad debe ser NULL, no igual al puntaje."""
    mod = animo_module_with_temp_db

    mod._v3_slider.set_level(8)
    mod._btn_reg.click()

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT intensidad FROM termometro ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["intensidad"] is None, (
        f"intensidad debe ser NULL (sin captura), got {row['intensidad']!r}. "
        "Antes del fix, _registrar persistía intensidad = puntaje. Eso "
        "convertía 'sin dato' en autoinforme real."
    )


def test_registrar_persiste_puntaje_y_nota(animo_module_with_temp_db):
    """S0-2-bis (regresión): puntaje y nota siguen persistiéndose correctamente."""
    mod = animo_module_with_temp_db

    mod._v3_slider.set_level(6)
    mod._btn_reg.click()

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    row = conn.execute(
        "SELECT puntaje, nota FROM termometro ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["puntaje"] == 6
    assert row["nota"] == ""  # nota también es '' por ahora (sin UI textarea)


def test_registrar_no_rompe_para_todos_los_niveles(animo_module_with_temp_db):
    """Smoke test: _registrar funciona para los 10 niveles sin excepción."""
    mod = animo_module_with_temp_db

    for nivel in range(1, 11):
        mod._v3_slider.set_level(nivel)
        mod._btn_reg.click()

    from shared.db import obtener_conexion

    conn = obtener_conexion()
    count = conn.execute("SELECT COUNT(*) AS n FROM termometro").fetchone()["n"]
    conn.close()

    assert count == 10, f"Debería haber 10 registros (1 por nivel), hay {count}"


# ─── Tests estructurales (no-regresión) ─────────────────────────────────


def test_registrar_insert_no_menciona_emocion_valencia_intensidad():
    """S0-2-bis (no-regresión estructural): el código fuente de _registrar
    no debe mencionar emocion/valencia/intensidad en el INSERT."""
    import inspect
    from app.modules import animo_qt

    src = inspect.getsource(animo_qt.ModuloAnimo._registrar)
    for forbidden in ['"emocion"', '"valencia"', '"intensidad"', "'emocion'",
                       "'valencia'", "'intensidad'"]:
        assert forbidden not in src, (
            f"Encontrado {forbidden!r} en _registrar — el bug S0-2 regresó. "
            "El INSERT no debe mencionar estos campos; el módulo no los captura."
        )


def test_exportar_animo_no_envia_campos_sin_captura():
    """S0-2-bis: _exportar_animo (shared/sync.py) no debe incluir
    emocion/valencia/intensidad en el payload que envía a Supabase.

    El test mira solo código ejecutable (sin comentarios ni docstrings) para
    no falsear con menciones en la documentación del fix."""
    import inspect
    import re
    from shared import sync

    src = inspect.getsource(sync._exportar_animo)
    # Qutar docstrings y comentarios para mirar solo código ejecutable
    src_no_comments = re.sub(r'#.*$', '', src, flags=re.MULTILINE)
    src_no_comments = re.sub(r'"""[\s\S]*?"""', '', src_no_comments)
    src_no_comments = re.sub(r"'''[\s\S]*?'''", '', src_no_comments)

    # El payload no debe incluir estos campos como keys
    for forbidden in ['"emocion"', '"valencia"', '"intensidad"',
                       "'emocion'", "'valencia'", "'intensidad'"]:
        assert forbidden not in src_no_comments, (
            f"Encontrado {forbidden!r} en código ejecutable de _exportar_animo — "
            "el payload sigue enviando campos sin captura al Hub."
        )
    # El SELECT tampoco debe pedir esas columnas.
    # El SQL puede estar partido en múltiples strings concatenados
    # (ej. "SELECT a, b " "FROM tbl"), así que miramos todo el código
    # ejecutable de la función.
    # Buscar la línea que contiene SELECT y la siguiente, juntas
    src_flat = " ".join(src_no_comments.split())  # colapsar whitespace
    # Extraer todo entre SELECT y FROM (sin importar comillas intermedias)
    select_match = re.search(
        r'SELECT\s+(.*?)\s*FROM\s+termometro',
        src_flat,
        re.IGNORECASE,
    )
    assert select_match, (
        f"No se encontró SELECT ... FROM termometro en _exportar_animo. "
        f"Source (flattened): {src_flat[:300]}"
    )
    select_cols = select_match.group(1)
    # Quitar comillas y espacios para comparar
    select_cols_clean = select_cols.replace('"', '').replace("'", "").strip()
    for forbidden in ["emocion", "valencia", "intensidad"]:
        assert forbidden not in select_cols_clean.lower(), (
            f"_exportar_animo sigue haciendo SELECT de {forbidden!r} "
            f"(cols = {select_cols_clean!r}) — debe traer solo "
            "fecha, hora, puntaje, nota."
        )


def test_fetch_patient_data_no_pide_campos_sin_captura():
    """S0-2-bis: _fetch_patient_data (hub/pacientes_qt.py) no debe pedir
    emocion/valencia/intensidad a mood_records.

    Mira solo la llamada _fetch() para mood_records, sin falsear con
    comentarios explicativos."""
    import inspect
    import re
    from hub import pacientes_qt

    src = inspect.getsource(pacientes_qt.DetallePacienteView._fetch_patient_data)
    # Buscar el call _fetch("animo", "mood_records", "<columns>", limit=30)
    # y extraer el string de columns
    pattern = r'_fetch\(\s*"animo"\s*,\s*"mood_records"\s*,\s*"([^"]+)"'
    match = re.search(pattern, src)
    assert match, (
        "No se encontró la llamada _fetch('animo', 'mood_records', ...) "
        "en _fetch_patient_data. ¿Se rompió el S0-1?"
    )
    columns = match.group(1)
    for forbidden in ["emocion", "valencia", "intensidad"]:
        assert forbidden not in columns, (
            f"_fetch_patient_data sigue pidiendo {forbidden!r} a mood_records "
            f"(columns = {columns!r}). Esos campos no se capturan en el "
            "módulo Ánimo actual."
        )


def test_backfill_legacy_eliminado_de_db_py():
    """S0-2-bis: el backfill legacy de shared/db.py que infería
    valencia/intensidad de emociones viejas debe estar eliminado."""
    with open("shared/db.py", encoding="utf-8") as f:
        src = f.read()

    # El UPDATE backfill no debe estar presente
    forbidden_patterns = [
        "WHEN emocion IN ('Calma','Energía','Gratitud') THEN 'positiva'",
        "WHEN emocion IN ('Tensión','Tristeza','Cansancio') THEN 'negativa'",
        "intensidad = CASE",
        "  WHEN emocion IN ('Tensión','Tristeza','Cansancio') THEN 11 - puntaje",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in src, (
            f"Backfill legacy NO eliminado: encontrado {pattern!r} en shared/db.py. "
            "Este bloque deriva valencia/intensidad de emociones que el módulo "
            "actual no captura — debe eliminarse."
        )


# ─── Test de integración: schema sigue siendo válido ────────────────────


def test_termometro_schema_permite_insert_minimo(isolated_db):
    """S0-2-bis (regresión): el schema SQLite permite INSERT solo con
    (fecha, hora, puntaje, nota) — emocion/valencia/intensidad aplican defaults."""
    from shared.db import conexion, inicializar_tablas

    # inicializar_tablas ya corrió via fixture isolated_db
    with conexion() as conn:
        conn.execute(
            "INSERT INTO termometro (fecha, hora, puntaje, nota) "
            "VALUES (?, ?, ?, ?)",
            ("2026-06-18", "10:00", 7, ""),
        )
        row = conn.execute(
            "SELECT puntaje, emocion, valencia, intensidad, nota "
            "FROM termometro ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row["puntaje"] == 7
    assert row["emocion"] == ""  # default del schema SQLite
    assert row["valencia"] == ""  # default del schema SQLite (ALTER posterior)
    assert row["intensidad"] is None  # default del schema SQLite (ALTER posterior)
    assert row["nota"] == ""
