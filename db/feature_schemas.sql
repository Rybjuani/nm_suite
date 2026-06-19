-- NeuroMood Hub — Schemas para entidades complejas (F2.1.A)
-- Ejecutar en: Supabase Dashboard → SQL Editor.
--
-- Estas tablas existen aparte de `hub_config` porque tienen lifecycle
-- propio, FKs, o estructura compleja que no encaja en un key/value
-- (ver §15.6 de AI_PROJECT_CONTEXT.md sobre el scope de hub_config).
--
-- Cubren las features:
--   - F2.4.A Editor de plantillas TCC
--   - F2.3.A/B/C Rutina con sistema 3 estados (opción C, decisión 2026-05-21)
--   - F2.2.A/B Timer profesional
--   - F2.2.C/D Avisos plantillas equipo
--   - F4.B Audit log IA
--
-- RLS habilitado por defecto. No usar anon key para datos clinicos,
-- patient-scoped ni logs IA.

-- ── Plantillas TCC ───────────────────────────────────────────────────────────
-- 4 steps + 8 emotions + N distortions + tip terapéutico, todo editable
-- desde Hub. F2.4.A.
CREATE TABLE IF NOT EXISTS public.tcc_templates (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    scope       TEXT NOT NULL DEFAULT 'global', -- 'global' o 'patient:<id>'
    steps       JSONB NOT NULL,  -- [{order, title, prompt, hint, required}]
    emotions    JSONB NOT NULL,  -- [{label, icon, color_token}]
    distortions JSONB NOT NULL,  -- [{label, keywords, category, icon}]
    tip_text    TEXT,
    version     INT DEFAULT 1,
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- ── Plantillas de rutina diaria ──────────────────────────────────────────────
-- Estructura por secciones (Mañana/Tarde/Noche o custom) con items.
-- F2.3.C — el profesional crea plantillas reutilizables.
CREATE TABLE IF NOT EXISTS public.routine_templates (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    scope      TEXT NOT NULL DEFAULT 'global',
    sections   JSONB NOT NULL,
    -- ejemplo:
    -- [{"key":"manana", "label":"Mañana",
    --   "items":[{"descripcion":"...", "categoria":"...", "dificultad":1}]},
    --  ...]
    version    INT DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Asignación plantilla rutina → paciente ───────────────────────────────────
-- 1 plantilla activa por paciente (PK paciente). F2.3.C.
CREATE TABLE IF NOT EXISTS public.patient_routine_template (
    patient_id  TEXT REFERENCES public.patients(patient_id) ON DELETE CASCADE,
    template_id BIGINT REFERENCES public.routine_templates(id),
    assigned_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (patient_id)
);

-- ── Presets remotos de timer ─────────────────────────────────────────────────
-- Reemplaza PRESETS hardcoded de app/modules/timer_qt.py (5/10/25/45).
-- Interpretación Propuesta Base item 3: el profesional delimita actividades
-- terapéuticas, no el paciente. F2.2.A/B.
CREATE TABLE IF NOT EXISTS public.timer_presets_remote (
    id           BIGSERIAL PRIMARY KEY,
    scope        TEXT NOT NULL DEFAULT 'global',
    name         TEXT NOT NULL,
    duracion_seg INT NOT NULL,
    categoria    TEXT DEFAULT '',
    activo       BOOLEAN DEFAULT TRUE,
    orden        INT DEFAULT 0,
    UNIQUE (scope, name)
);

-- ── Biblioteca de mensajes de apoyo ──────────────────────────────────────────
-- Mensajes que el equipo determina (Propuesta Base ítem 2). Reemplaza la
-- categorización inferida hardcoded de app/modules/avisos_qt.py. F2.2.C/D.
CREATE TABLE IF NOT EXISTS public.support_messages (
    id        BIGSERIAL PRIMARY KEY,
    scope     TEXT NOT NULL DEFAULT 'global',
    categoria TEXT NOT NULL,
    -- ej: "medicacion", "hidratacion", "calma", "actividad",
    --     "comida", "trabajo", "descanso", "terapia", "recordatorio".
    mensaje   TEXT NOT NULL,
    activa    BOOLEAN DEFAULT TRUE
);

-- ── Audit log IA ─────────────────────────────────────────────────────────────
-- F4.B — Trazabilidad clínica/legal de cada llamada al asistente IA del Hub.
-- Append-only: nunca se hace UPDATE, solo INSERT.
CREATE TABLE IF NOT EXISTS public.ia_audit_log (
    id            BIGSERIAL PRIMARY KEY,
    patient_id    TEXT,
    called_at     TIMESTAMPTZ DEFAULT now(),
    provider      TEXT,   -- "Groq", "Gemini", "OpenAI", "OllamaCloud"
    model         TEXT,   -- ej "llama-3.3-70b-versatile"
    fn_name       TEXT,   -- "generar_resumen_paciente", "generar_asignacion_*", etc.
    prompt_user   TEXT,
    prompt_system TEXT,
    output        TEXT,
    error         TEXT
);

-- ── RLS seguro por defecto ───────────────────────────────────────────────────
ALTER TABLE public.tcc_templates             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.routine_templates         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_routine_template  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timer_presets_remote      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.support_messages          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ia_audit_log              ENABLE ROW LEVEL SECURITY;

-- ── ALTER patients: campo `rutina_modo` (opción C, decisión 2026-05-21) ──────
-- Sistema híbrido 3 estados: solo el profesional / mixto / solo el paciente.
-- F2.3.A — la Suite respeta este modo al renderizar el módulo Rutina.
ALTER TABLE public.patients
    ADD COLUMN IF NOT EXISTS rutina_modo TEXT DEFAULT 'mixto'
    CHECK (rutina_modo IN ('solo_profesional', 'mixto', 'solo_paciente'));

-- ── ALTER patients: campos Hub F4.A ──────────────────────────────────────────
-- F4.A — Gestión real de pacientes desde Hub.
ALTER TABLE public.patients
    ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS creado_por TEXT,
    ADD COLUMN IF NOT EXISTS notas_profesional TEXT;
