-- NeuroMood Hub — Schema de configurabilidad remota (F2.0.A)
-- Ejecutar en: Supabase Dashboard → SQL Editor.
--
-- Implementa el patrón general "hub_config 2 niveles" documentado en
-- AUDITORIA_NEUROMOOD.md subsección 9.4.A y en AI_PROJECT_CONTEXT.md §15.6.
--
-- Una sola tabla para TODA configuración del Hub que aplique al render de
-- la UI de la Suite. Dos niveles via columna `scope`:
--   - 'global'              → vale para todos los pacientes del equipo
--   - 'patient:<patient_id>' → override individual sobre el global
--
-- La util `shared/remote_config.py` (a crear en F2.0.B) resuelve la
-- jerarquía: patient:<id> → global → default hardcoded.
--
-- Esta tabla NO almacena:
--   - registros clínicos (mood_records, breathing_sessions, etc.)
--   - consentimientos legales (legal_consents — versionado por código)
--   - banco de actividades (activity_bank — tabla propia con FK)
--   - prompts IA del sistema (versionados en hub/ia_asistente.py)
--   - audit log IA (ia_audit_log — tabla propia, append-only)
--   - entidades con lifecycle propio o estructura compleja
--     (tcc_templates, routine_templates → schemas separados en F2.1.A)
-- Ver §15.6 de AI_PROJECT_CONTEXT.md para el scope completo.

-- ── Tabla principal ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.hub_config (
    id           BIGSERIAL PRIMARY KEY,
    scope        TEXT NOT NULL,
    key          TEXT NOT NULL,
    value        JSONB NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   UUID,
    version      INT NOT NULL DEFAULT 1,
    UNIQUE (scope, key)
);

-- ── Índice de lookup (scope, key) ────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_hub_config_scope_key
    ON public.hub_config (scope, key);

-- ── RLS seguro por defecto ───────────────────────────────────────────────────
-- No usar anon key para overrides patient:<id>. Las policies completas se
-- centralizan en db/secure_rls_hardening.sql.
ALTER TABLE public.hub_config ENABLE ROW LEVEL SECURITY;
