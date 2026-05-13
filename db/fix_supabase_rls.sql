-- fix_supabase_rls.sql
-- Ejecutar este archivo COMPLETO en:
--   Supabase Dashboard -> SQL Editor -> New query -> Paste -> Run
--
-- Deshabilita RLS en todas las tablas y agrega columnas faltantes.
-- Es seguro ejecutarlo multiples veces (IF NOT EXISTS / IF EXISTS).

-- ── 1. Deshabilitar RLS en todas las tablas ─────────────────────────────────
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

-- ── 2. Agregar columnas faltantes en patients ────────────────────────────────
ALTER TABLE patients ADD COLUMN IF NOT EXISTS install_code              TEXT    DEFAULT '';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_checklist_activacion BOOLEAN DEFAULT TRUE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_checklist_manual     BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_temporizador_manual  BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS perm_recordatorios_manual BOOLEAN DEFAULT FALSE;

-- ── 3. Columna faltante en assigned_tasks ───────────────────────────────────
ALTER TABLE assigned_tasks ADD COLUMN IF NOT EXISTS animo_rango TEXT DEFAULT NULL;
