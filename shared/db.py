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
    conn = sqlite3.connect(str(ruta))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _migrar_termometro_0_10(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='termometro'"
    ).fetchone()
    if row and "BETWEEN 1 AND 10" in row["sql"]:
        conn.executescript("""
            ALTER TABLE termometro RENAME TO termometro_old;
            CREATE TABLE termometro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                puntaje INTEGER NOT NULL CHECK(puntaje BETWEEN 0 AND 10),
                nota TEXT DEFAULT ''
            );
            INSERT INTO termometro SELECT * FROM termometro_old;
            DROP TABLE termometro_old;
        """)


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
            puntaje INTEGER NOT NULL CHECK(puntaje BETWEEN 0 AND 10),
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
    """)

    conn.commit()
    _migrar_termometro_0_10(conn)
    _migrar_pensamientos_0_10(conn)
    _migrar_activacion_0_10(conn)
    _migrar_checklist_sin_cascade(conn)
    conn.commit()
    conn.close()


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
