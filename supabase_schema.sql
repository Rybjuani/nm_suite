-- NeuroMood Suite — Schema Supabase
-- Ejecutar en: Supabase Dashboard → SQL Editor

-- ── Pacientes ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    patient_id                  TEXT PRIMARY KEY,
    patient_name                TEXT,
    pwd                         TEXT DEFAULT '',
    install_code                TEXT DEFAULT '',
    created_at                  TIMESTAMPTZ DEFAULT now(),
    perm_checklist_activacion   BOOLEAN DEFAULT TRUE,
    perm_checklist_manual       BOOLEAN DEFAULT FALSE,
    perm_temporizador_manual    BOOLEAN DEFAULT FALSE,
    perm_recordatorios_manual   BOOLEAN DEFAULT FALSE
);

-- ── Registros de ánimo (Termómetro) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mood_records (
    id         BIGSERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    fecha      TEXT NOT NULL,
    hora       TEXT NOT NULL,
    puntaje    INTEGER,
    nota       TEXT,
    UNIQUE (patient_id, fecha, hora)
);

-- ── Sesiones de respiración ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS breathing_sessions (
    id                BIGSERIAL PRIMARY KEY,
    patient_id        TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    fecha             TEXT NOT NULL,
    hora              TEXT NOT NULL,
    tecnica           TEXT,
    duracion_minutos  REAL,
    ciclos            INTEGER,
    UNIQUE (patient_id, fecha, hora)
);

-- ── Registros de pensamientos ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS thought_records (
    id                    BIGSERIAL PRIMARY KEY,
    patient_id            TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    fecha                 TEXT NOT NULL,
    hora                  TEXT NOT NULL,
    situacion             TEXT,
    emocion               TEXT,
    intensidad            INTEGER,
    pensamiento           TEXT,
    respuesta_alternativa TEXT,
    distorsiones          TEXT,
    reflexion_ia          TEXT,
    UNIQUE (patient_id, fecha, hora)
);

-- ── Checklist completadas ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS checklist_completions (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    fecha       TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    categoria   TEXT,
    origen      TEXT DEFAULT '',
    UNIQUE (patient_id, fecha, descripcion)
);

-- ── Sesiones de temporizador ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS timer_sessions (
    id               BIGSERIAL PRIMARY KEY,
    patient_id       TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    fecha            TEXT NOT NULL,
    hora             TEXT NOT NULL,
    nombre           TEXT,
    categoria        TEXT,
    duracion_config  INTEGER,
    duracion_real    INTEGER,
    notas            TEXT,
    UNIQUE (patient_id, fecha, hora, nombre)
);

-- ── Log de recordatorios disparados ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reminder_logs (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    fecha       TEXT NOT NULL,
    hora        TEXT NOT NULL,
    mensaje     TEXT NOT NULL,
    cerrado     BOOLEAN DEFAULT FALSE,
    UNIQUE (patient_id, fecha, hora, mensaje)
);

-- ── Tareas asignadas por el profesional ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS assigned_tasks (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    seccion     TEXT DEFAULT 'tarde',
    categoria   TEXT DEFAULT 'Logro',
    dificultad  INTEGER DEFAULT 1,
    animo_rango TEXT DEFAULT NULL,
    activa      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (patient_id, descripcion)
);

-- ── Recordatorios asignados por el profesional ────────────────────────────────
CREATE TABLE IF NOT EXISTS assigned_reminders (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    hora        TEXT NOT NULL,
    mensaje     TEXT NOT NULL,
    dias        TEXT DEFAULT '1,2,3,4,5,6,7',
    activa      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (patient_id, hora, mensaje)
);

-- ── Migración: agregar columnas si la tabla patients ya existe ───────────────
ALTER TABLE patients ADD COLUMN IF NOT EXISTS pwd                        TEXT    DEFAULT '';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS install_code               TEXT    DEFAULT '';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_checklist_activacion  BOOLEAN DEFAULT TRUE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_checklist_manual      BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_temporizador_manual   BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_recordatorios_manual  BOOLEAN DEFAULT FALSE;
ALTER TABLE assigned_tasks ADD COLUMN IF NOT EXISTS animo_rango TEXT DEFAULT NULL;

-- ── Banco general de actividades (compartido entre todos los pacientes) ────────
CREATE TABLE IF NOT EXISTS activity_bank (
    id          BIGSERIAL PRIMARY KEY,
    nombre      TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL DEFAULT '',
    categoria   TEXT NOT NULL DEFAULT 'Autocuidado',
    dificultad  INTEGER NOT NULL DEFAULT 1,
    duracion_min INTEGER NOT NULL DEFAULT 10,
    beneficio   TEXT NOT NULL DEFAULT '',
    animo_min   INTEGER NOT NULL DEFAULT 0,
    animo_max   INTEGER NOT NULL DEFAULT 10,
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ── Actividades personalizadas por paciente ───────────────────────────────────
CREATE TABLE IF NOT EXISTS patient_activities (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    nombre      TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    categoria   TEXT NOT NULL DEFAULT 'Autocuidado',
    dificultad  INTEGER NOT NULL DEFAULT 1,
    duracion_min INTEGER NOT NULL DEFAULT 10,
    beneficio   TEXT NOT NULL DEFAULT '',
    animo_min   INTEGER NOT NULL DEFAULT 0,
    animo_max   INTEGER NOT NULL DEFAULT 10,
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (patient_id, nombre)
);

-- ── RLS: deshabilitar para acceso con anon key (entorno clínico controlado) ───
-- Si preferís RLS activo, reemplazá con políticas permisivas por patient_id.
ALTER TABLE patients              DISABLE ROW LEVEL SECURITY;
ALTER TABLE mood_records          DISABLE ROW LEVEL SECURITY;
ALTER TABLE breathing_sessions    DISABLE ROW LEVEL SECURITY;
ALTER TABLE thought_records       DISABLE ROW LEVEL SECURITY;
ALTER TABLE checklist_completions DISABLE ROW LEVEL SECURITY;
ALTER TABLE timer_sessions        DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_logs         DISABLE ROW LEVEL SECURITY;
ALTER TABLE assigned_tasks        DISABLE ROW LEVEL SECURITY;
ALTER TABLE assigned_reminders    DISABLE ROW LEVEL SECURITY;
ALTER TABLE activity_bank         DISABLE ROW LEVEL SECURITY;
ALTER TABLE patient_activities    DISABLE ROW LEVEL SECURITY;
