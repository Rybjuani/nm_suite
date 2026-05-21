import sqlite3
import os
from pathlib import Path


def obtener_ruta_db() -> Path:
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    carpeta = Path(appdata) / "NeuroMood"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / "nm_data.db"


def obtener_conexion() -> sqlite3.Connection:
    ruta = obtener_ruta_db()
    conn = sqlite3.connect(str(ruta), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _migrar_puntaje_min_1(conn):
    try:
        conn.execute("UPDATE termometro SET puntaje = 1 WHERE puntaje < 1")
        conn.commit()
    except Exception:
        pass


def _migrar_pensamientos_0_10(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='pensamientos'"
    ).fetchone()
    if row and "BETWEEN 1 AND 10" in row["sql"]:
        conn.executescript("""
            ALTER TABLE pensamientos RENAME TO pensamientos_old;
            CREATE TABLE pensamientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                situacion TEXT NOT NULL,
                emocion TEXT NOT NULL,
                intensidad INTEGER NOT NULL CHECK(intensidad BETWEEN 0 AND 10),
                pensamiento TEXT NOT NULL,
                respuesta_alternativa TEXT DEFAULT '',
                distorsiones TEXT DEFAULT ''
            );
            INSERT INTO pensamientos SELECT * FROM pensamientos_old;
            DROP TABLE pensamientos_old;
        """)


def _migrar_checklist_sin_cascade(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='checklist_completadas'"
    ).fetchone()
    if row and "FOREIGN KEY" in row["sql"]:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS checklist_completadas_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarea_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                UNIQUE(tarea_id, fecha)
            );
            INSERT OR IGNORE INTO checklist_completadas_v2 SELECT * FROM checklist_completadas;
            DROP TABLE checklist_completadas;
            ALTER TABLE checklist_completadas_v2 RENAME TO checklist_completadas;
        """)


def _migrar_activacion_0_10(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='activacion'"
    ).fetchone()
    if row and "BETWEEN 1 AND 10" in row["sql"]:
        conn.executescript("""
            ALTER TABLE activacion RENAME TO activacion_old;
            CREATE TABLE activacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                energia INTEGER NOT NULL CHECK(energia BETWEEN 0 AND 10),
                animo INTEGER NOT NULL CHECK(animo BETWEEN 0 AND 10),
                actividad TEXT NOT NULL,
                resultado TEXT NOT NULL CHECK(resultado IN ('hecha', 'intentada', 'no_pude'))
            );
            INSERT INTO activacion SELECT * FROM activacion_old;
            DROP TABLE activacion_old;
        """)


def inicializar_tablas():
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS termometro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            puntaje INTEGER NOT NULL CHECK(puntaje BETWEEN 1 AND 10),
            nota TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS recordatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hora TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            dias TEXT NOT NULL DEFAULT '1,2,3,4,5,6,7',
            activo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS actividades_temporizador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            nombre TEXT NOT NULL,
            categoria TEXT DEFAULT '',
            duracion_config INTEGER NOT NULL,
            duracion_real INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pensamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            situacion TEXT NOT NULL,
            emocion TEXT NOT NULL,
            intensidad INTEGER NOT NULL CHECK(intensidad BETWEEN 0 AND 10),
            pensamiento TEXT NOT NULL,
            respuesta_alternativa TEXT DEFAULT '',
            distorsiones TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS respiracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            tecnica TEXT NOT NULL,
            duracion_minutos REAL NOT NULL,
            ciclos INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS checklist_tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seccion TEXT NOT NULL CHECK(seccion IN ('manana', 'tarde', 'noche')),
            descripcion TEXT NOT NULL,
            orden INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS checklist_completadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarea_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (tarea_id) REFERENCES checklist_tareas(id) ON DELETE CASCADE,
            UNIQUE(tarea_id, fecha)
        );

        CREATE TABLE IF NOT EXISTS activacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            energia INTEGER NOT NULL CHECK(energia BETWEEN 0 AND 10),
            animo INTEGER NOT NULL CHECK(animo BETWEEN 0 AND 10),
            actividad TEXT NOT NULL,
            resultado TEXT NOT NULL CHECK(resultado IN ('hecha', 'intentada', 'no_pude'))
        );

        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS checklist_snapshot (
            fecha TEXT PRIMARY KEY,
            total_tareas INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recordatorios_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            rec_id INTEGER,
            cerrado INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS mensajes_biblioteca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            mensaje TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activacion_actividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT 'Autocuidado',
            dificultad INTEGER NOT NULL DEFAULT 1 CHECK(dificultad BETWEEN 1 AND 3),
            duracion_min INTEGER NOT NULL DEFAULT 10,
            beneficio TEXT DEFAULT '',
            animo_min INTEGER NOT NULL DEFAULT 0,
            animo_max INTEGER NOT NULL DEFAULT 10,
            activa INTEGER NOT NULL DEFAULT 1,
            es_custom INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS activacion_config (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activacion_perfil (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS timer_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            categoria TEXT DEFAULT '',
            duracion_seg INTEGER NOT NULL DEFAULT 300,
            orden INTEGER NOT NULL DEFAULT 0,
            es_custom INTEGER NOT NULL DEFAULT 0,
            animo_rango TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS checklist_plantillas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            seccion TEXT NOT NULL CHECK(seccion IN ('manana', 'tarde', 'noche')),
            categoria TEXT DEFAULT 'Logro',
            dificultad INTEGER DEFAULT 1,
            orden INTEGER NOT NULL DEFAULT 0,
            es_custom INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS checklist_notas_dia (
            fecha TEXT PRIMARY KEY,
            nota TEXT NOT NULL DEFAULT ''
        );

        -- Cache local de hub_config remoto (F2.0.B).
        -- Llenada por shared.remote_config.refresh_from_supabase() y por
        -- shared.sync._importar_hub_config(). Consumida por la util t().
        CREATE TABLE IF NOT EXISTS remote_config_cache (
            scope      TEXT NOT NULL,
            key        TEXT NOT NULL,
            value      TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (scope, key)
        );

        CREATE TABLE IF NOT EXISTS tcc_templates_cache (
            id INTEGER PRIMARY KEY,
            scope TEXT NOT NULL,
            name TEXT NOT NULL,
            payload TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            fetched_at TEXT NOT NULL,
            UNIQUE (scope, name)
        );

        CREATE TABLE IF NOT EXISTS routine_templates_cache (
            id INTEGER PRIMARY KEY,
            scope TEXT NOT NULL,
            payload TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS breathing_presets_cache (
            id INTEGER PRIMARY KEY,
            scope TEXT NOT NULL,
            name TEXT NOT NULL,
            payload TEXT NOT NULL,
            UNIQUE (scope, name)
        );

        CREATE TABLE IF NOT EXISTS timer_presets_cache (
            id INTEGER PRIMARY KEY,
            scope TEXT NOT NULL,
            name TEXT NOT NULL,
            payload TEXT NOT NULL,
            UNIQUE (scope, name)
        );

        CREATE TABLE IF NOT EXISTS support_messages_cache (
            id INTEGER PRIMARY KEY,
            scope TEXT NOT NULL,
            categoria TEXT NOT NULL,
            mensaje TEXT NOT NULL
        );
    """)

    conn.commit()
    _migrar_puntaje_min_1(conn)
    _migrar_pensamientos_0_10(conn)
    _migrar_activacion_0_10(conn)
    _migrar_checklist_sin_cascade(conn)
    _migrar_pensamientos_campos_tcc(conn)
    conn.commit()
    try:
        conn.execute("ALTER TABLE actividades_temporizador ADD COLUMN notas TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE checklist_tareas ADD COLUMN categoria TEXT DEFAULT 'Logro'")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE checklist_tareas ADD COLUMN dificultad INTEGER DEFAULT 1")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE checklist_tareas ADD COLUMN origen TEXT DEFAULT 'manual'")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE checklist_tareas ADD COLUMN animo_rango TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    _migrar_activacion_actividades_animo(conn)
    try:
        conn.execute("ALTER TABLE timer_presets ADD COLUMN animo_rango TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    conn.close()


def _migrar_pensamientos_campos_tcc(conn):
    nuevas = [
        ("evidencia_favor",    "TEXT DEFAULT ''"),
        ("evidencia_contra",   "TEXT DEFAULT ''"),
        ("creencia_antes",     "INTEGER DEFAULT 50"),
        ("creencia_despues",   "INTEGER DEFAULT 50"),
        ("emocion_resultante", "TEXT DEFAULT ''"),
        ("reflexion_ia",       "TEXT DEFAULT ''"),
    ]
    for col, typedef in nuevas:
        try:
            conn.execute(f"ALTER TABLE pensamientos ADD COLUMN {col} {typedef}")
            conn.commit()
        except Exception:
            pass


def _migrar_activacion_actividades_animo(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='activacion_actividades'"
    ).fetchone()
    if not row:
        return
    sql = row["sql"]
    if "energia_min" in sql:
        try:
            conn.execute("ALTER TABLE activacion_actividades RENAME COLUMN energia_min TO animo_min")
            conn.commit()
        except Exception:
            pass
    if "energia_max" in sql:
        try:
            conn.execute("ALTER TABLE activacion_actividades RENAME COLUMN energia_max TO animo_max")
            conn.commit()
        except Exception:
            pass


def guardar_config(clave: str, valor: str):
    conn = obtener_conexion()
    conn.execute(
        "INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)",
        (clave, valor)
    )
    conn.commit()
    conn.close()


def leer_config(clave: str, default: str = "") -> str:
    conn = obtener_conexion()
    row = conn.execute(
        "SELECT valor FROM config WHERE clave = ?", (clave,)
    ).fetchone()
    conn.close()
    return row["valor"] if row else default
