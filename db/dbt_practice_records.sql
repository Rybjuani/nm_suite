-- NeuroMood Hub — Schema para Prácticas de Habilidades DBT (Fase 3)
-- Ejecutar en: Supabase Dashboard → SQL Editor.

CREATE TABLE IF NOT EXISTS public.dbt_practice_records (
    record_id        TEXT PRIMARY KEY,
    patient_id       TEXT NOT NULL REFERENCES public.patients(patient_id) ON DELETE CASCADE,
    fecha            DATE NOT NULL,
    hora             TIME NOT NULL,
    skill_id         TEXT NOT NULL,
    skill_version    INTEGER NOT NULL DEFAULT 1,
    familia          TEXT NOT NULL CHECK (
        familia IN (
            'mindfulness',
            'distress_tolerance',
            'emotion_regulation',
            'interpersonal_effectiveness'
        )
    ),
    necesidad        TEXT DEFAULT '',
    malestar_antes   INTEGER CHECK (
        malestar_antes IS NULL OR (malestar_antes BETWEEN 0 AND 10)
    ),
    malestar_despues INTEGER CHECK (
        malestar_despues IS NULL OR (malestar_despues BETWEEN 0 AND 10)
    ),
    resultado        TEXT NOT NULL DEFAULT 'sin_evaluar' CHECK (
        resultado IN ('ayudo', 'parcial', 'no_esta_vez', 'sin_evaluar')
    ),
    duracion_seg     INTEGER NOT NULL DEFAULT 0 CHECK (duracion_seg >= 0),
    nota             TEXT NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS habilitado
ALTER TABLE public.dbt_practice_records ENABLE ROW LEVEL SECURITY;

-- Revocar acceso anónimo por defecto
REVOKE ALL ON TABLE public.dbt_practice_records FROM anon;

-- Otorgar permisos de lectura/escritura a usuarios autenticados
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.dbt_practice_records TO authenticated;

-- Política para Pacientes (lectura y escritura de sus propios registros)
DROP POLICY IF EXISTS "dbt_practice_records_own" ON public.dbt_practice_records;
CREATE POLICY "dbt_practice_records_own" ON public.dbt_practice_records
    FOR ALL
    TO authenticated
    USING (patient_id = auth.uid()::text)
    WITH CHECK (patient_id = auth.uid()::text);

-- Política para Profesionales (lectura de los registros de sus pacientes asignados)
DROP POLICY IF EXISTS "dbt_practice_records_professional" ON public.dbt_practice_records;
CREATE POLICY "dbt_practice_records_professional" ON public.dbt_practice_records
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.patient_assignments pa
            WHERE pa.patient_id = dbt_practice_records.patient_id
              AND pa.professional_id = auth.uid()::text
        )
    );
