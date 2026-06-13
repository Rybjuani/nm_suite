-- ============================================================================
-- db/patients_dedupe.sql — Diagnóstico y merge de pacientes duplicados (v1.0)
--
-- POR QUÉ EXISTEN DUPLICADOS ("dos juan cruz con IDs distintos"):
--   * Filas LEGACY: versiones viejas de la Suite derivaban el patient_id como
--     sha256(nombre:password:install_code)[:24]. El install_code se perdía al
--     desinstalar => cada reinstalación creaba un id NUEVO con el mismo nombre.
--     Esa ruta fue ELIMINADA del código (v1.0); el alta canónica es Supabase
--     Auth: patient_id = auth.user.id (UUID 36 chars) — reinstalar + iniciar
--     sesión con la misma cuenta reutiliza el MISMO id (alta idempotente).
--   * Cuentas nuevas: si el paciente crea OTRA cuenta (otro email) al
--     reinstalar, Auth emite otro UUID. Eso no es bug: son dos cuentas; el
--     merge de abajo permite consolidarlas si corresponde.
--
-- CÓMO SE USA (manual, owner — nada se borra sin tu revisión):
--   1) Correr el BLOQUE 1 (solo SELECT) y revisar el reporte.
--   2) Por cada par a consolidar, completar :dup_id y :canon_id en el
--      BLOQUE 2 y correrlo. Canónica = la fila formato 'auth-uuid' (36 chars);
--      si ambas son legacy, la de mayor actividad.
--
-- ⚠️ ADVERTENCIA: si la instalación legacy sigue VIVA y sincronizando, su
--    sync re-creará la fila legacy en el próximo ciclo (shared/sync.py
--    _upsert_paciente usa el patient_id guardado localmente). El merge es
--    definitivo solo si esa instalación se re-onboardea con cuenta (Auth)
--    o se da de baja.
-- ============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- BLOQUE 0 · ALINEAR ESQUEMA (idempotente, correr SIEMPRE primero)
-- El Hub v1.0 lee patients.email / unlinked / last_sync_date. Si la DB se creó
-- con un esquema anterior, estas columnas faltan y tanto este reporte como la
-- lista de pacientes del Hub fallan. Seguro correrlo más de una vez.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE public.patients ADD COLUMN IF NOT EXISTS last_sync_date TIMESTAMPTZ;
ALTER TABLE public.patients ADD COLUMN IF NOT EXISTS email    TEXT    DEFAULT '';
ALTER TABLE public.patients ADD COLUMN IF NOT EXISTS unlinked BOOLEAN DEFAULT FALSE;


-- ─────────────────────────────────────────────────────────────────────────────
-- BLOQUE 1 · REPORTE (solo lectura)
-- Duplicados por nombre, formato de id y cantidad de datos hijos por tabla.
-- ─────────────────────────────────────────────────────────────────────────────

WITH dup AS (
    SELECT lower(trim(patient_name)) AS nombre_norm
    FROM patients
    GROUP BY lower(trim(patient_name))
    HAVING count(*) > 1
)
SELECT
    p.patient_name,
    p.patient_id,
    CASE
        WHEN length(p.patient_id) = 24 AND p.patient_id ~ '^[0-9a-f]+$'
            THEN 'legacy-sha'
        WHEN length(p.patient_id) = 36
            THEN 'auth-uuid (canónica)'
        ELSE 'otro'
    END AS formato,
    p.created_at,
    p.last_sync_date,
    p.email,
    p.unlinked,
    (SELECT count(*) FROM mood_records          m WHERE m.patient_id = p.patient_id) AS animo,
    (SELECT count(*) FROM breathing_sessions    b WHERE b.patient_id = p.patient_id) AS respiracion,
    (SELECT count(*) FROM thought_records       t WHERE t.patient_id = p.patient_id) AS tcc,
    (SELECT count(*) FROM checklist_completions c WHERE c.patient_id = p.patient_id) AS checklist,
    (SELECT count(*) FROM timer_sessions        s WHERE s.patient_id = p.patient_id) AS timer,
    (SELECT count(*) FROM reminder_logs         r WHERE r.patient_id = p.patient_id) AS avisos,
    -- activation_results NO va acá: es una tabla opcional y si no existe el
    -- SELECT entero falla al parsear. El BLOQUE 2 sí la migra (condicional).
    (SELECT count(*) FROM legal_consents        l WHERE l.patient_id = p.patient_id) AS consents,
    (SELECT count(*) FROM assigned_tasks        x WHERE x.patient_id = p.patient_id) AS tareas,
    (SELECT count(*) FROM assigned_reminders    y WHERE y.patient_id = p.patient_id) AS alertas,
    (SELECT count(*) FROM patient_activities    z WHERE z.patient_id = p.patient_id) AS actividades,
    (SELECT count(*) FROM hub_config            h WHERE h.scope = 'patient:' || p.patient_id) AS textos,
    (SELECT count(*) FROM support_messages      q WHERE q.scope = 'patient:' || p.patient_id) AS mensajes,
    (SELECT count(*) FROM timer_presets_remote  w WHERE w.scope = 'patient:' || p.patient_id) AS presets_timer
FROM patients p
JOIN dup d ON lower(trim(p.patient_name)) = d.nombre_norm
ORDER BY lower(trim(p.patient_name)), p.created_at;


-- ─────────────────────────────────────────────────────────────────────────────
-- BLOQUE 2 · MERGE de UN par (correr una vez POR CADA duplicado, con los ids
-- del reporte). Reemplazar los dos valores de la CTE `par`:
--   dup_id   = id que se ABSORBE y elimina (normalmente la fila legacy-sha)
--   canon_id = id que QUEDA (normalmente la fila auth-uuid)
--
-- Las tablas clínicas tienen UNIQUE(patient_id, fecha, …): se usa
-- INSERT … ON CONFLICT DO NOTHING + DELETE (un UPDATE directo chocaría con
-- la unique si ambos perfiles registraron el mismo día/hora). Las tablas de
-- scope-string se migran con UPDATE. Al final se borra la fila duplicada
-- (los restos caen por ON DELETE CASCADE).
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- >>>>> EDITAR ESTOS DOS VALORES ANTES DE CORRER <<<<<
CREATE TEMP TABLE par AS
SELECT 'PEGAR_DUP_ID_ACA'::text   AS dup_id,
       'PEGAR_CANON_ID_ACA'::text AS canon_id;

-- Guard: con los placeholders SIN completar, el bloque entero se OMITE en
-- silencio (todas las sentencias de abajo no matchean ninguna fila) — así se
-- puede correr el archivo completo para ver solo el reporte. Con ids reales,
-- valida que existan y sean distintos (si algo falla acá, ROLLBACK).
DO $$
DECLARE d text; c text;
BEGIN
    SELECT dup_id, canon_id INTO d, c FROM par;
    IF d = 'PEGAR_DUP_ID_ACA' OR c = 'PEGAR_CANON_ID_ACA' THEN
        RAISE NOTICE 'BLOQUE 2 omitido: completá dup_id/canon_id para mergear un par.';
        RETURN;
    END IF;
    IF d = c THEN RAISE EXCEPTION 'dup_id y canon_id son iguales'; END IF;
    IF NOT EXISTS (SELECT 1 FROM patients WHERE patient_id = d) THEN
        RAISE EXCEPTION 'dup_id % no existe en patients', d;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM patients WHERE patient_id = c) THEN
        RAISE EXCEPTION 'canon_id % no existe en patients', c;
    END IF;
END $$;

-- mood_records (UNIQUE patient_id, fecha, hora)
INSERT INTO mood_records (patient_id, fecha, hora, puntaje, nota, emocion, valencia, intensidad)
SELECT (SELECT canon_id FROM par), fecha, hora, puntaje, nota, emocion, valencia, intensidad
FROM mood_records WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, fecha, hora) DO NOTHING;
DELETE FROM mood_records WHERE patient_id = (SELECT dup_id FROM par);

-- breathing_sessions (UNIQUE patient_id, fecha, hora)
INSERT INTO breathing_sessions (patient_id, fecha, hora, tecnica, duracion_minutos, ciclos)
SELECT (SELECT canon_id FROM par), fecha, hora, tecnica, duracion_minutos, ciclos
FROM breathing_sessions WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, fecha, hora) DO NOTHING;
DELETE FROM breathing_sessions WHERE patient_id = (SELECT dup_id FROM par);

-- thought_records (UNIQUE patient_id, fecha, hora)
INSERT INTO thought_records (patient_id, fecha, hora, situacion, emocion, intensidad,
                             pensamiento, respuesta_alternativa, distorsiones, reflexion_ia)
SELECT (SELECT canon_id FROM par), fecha, hora, situacion, emocion, intensidad,
       pensamiento, respuesta_alternativa, distorsiones, reflexion_ia
FROM thought_records WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, fecha, hora) DO NOTHING;
DELETE FROM thought_records WHERE patient_id = (SELECT dup_id FROM par);

-- checklist_completions (UNIQUE patient_id, fecha, descripcion)
INSERT INTO checklist_completions (patient_id, fecha, descripcion, categoria, origen)
SELECT (SELECT canon_id FROM par), fecha, descripcion, categoria, origen
FROM checklist_completions WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, fecha, descripcion) DO NOTHING;
DELETE FROM checklist_completions WHERE patient_id = (SELECT dup_id FROM par);

-- timer_sessions (UNIQUE patient_id, fecha, hora, nombre)
INSERT INTO timer_sessions (patient_id, fecha, hora, nombre, categoria,
                            duracion_config, duracion_real, notas)
SELECT (SELECT canon_id FROM par), fecha, hora, nombre, categoria,
       duracion_config, duracion_real, notas
FROM timer_sessions WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, fecha, hora, nombre) DO NOTHING;
DELETE FROM timer_sessions WHERE patient_id = (SELECT dup_id FROM par);

-- reminder_logs (UNIQUE patient_id, fecha, hora, mensaje)
INSERT INTO reminder_logs (patient_id, fecha, hora, mensaje, cerrado)
SELECT (SELECT canon_id FROM par), fecha, hora, mensaje, cerrado
FROM reminder_logs WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, fecha, hora, mensaje) DO NOTHING;
DELETE FROM reminder_logs WHERE patient_id = (SELECT dup_id FROM par);

-- assigned_tasks (UNIQUE patient_id, descripcion)
INSERT INTO assigned_tasks (patient_id, descripcion, seccion, categoria,
                            dificultad, animo_rango, activa)
SELECT (SELECT canon_id FROM par), descripcion, seccion, categoria,
       dificultad, animo_rango, activa
FROM assigned_tasks WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, descripcion) DO NOTHING;
DELETE FROM assigned_tasks WHERE patient_id = (SELECT dup_id FROM par);

-- assigned_reminders (UNIQUE patient_id, hora, mensaje)
INSERT INTO assigned_reminders (patient_id, hora, mensaje, dias, activa)
SELECT (SELECT canon_id FROM par), hora, mensaje, dias, activa
FROM assigned_reminders WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, hora, mensaje) DO NOTHING;
DELETE FROM assigned_reminders WHERE patient_id = (SELECT dup_id FROM par);

-- patient_activities (UNIQUE patient_id, nombre)
INSERT INTO patient_activities (patient_id, nombre, descripcion, categoria,
                                animo_min, animo_max, activa)
SELECT (SELECT canon_id FROM par), nombre, descripcion, categoria,
       animo_min, animo_max, activa
FROM patient_activities WHERE patient_id = (SELECT dup_id FROM par)
ON CONFLICT (patient_id, nombre) DO NOTHING;
DELETE FROM patient_activities WHERE patient_id = (SELECT dup_id FROM par);

-- activation_results (sin unique por fila → UPDATE directo; condicional:
-- la tabla puede no existir si nunca se corrió su SQL de creación)
DO $$
BEGIN
    IF to_regclass('public.activation_results') IS NOT NULL THEN
        UPDATE activation_results SET patient_id = (SELECT canon_id FROM par)
        WHERE patient_id = (SELECT dup_id FROM par);
    END IF;
END $$;

-- legal_consents (histórico append-only → UPDATE directo, conserva constancias)
UPDATE legal_consents SET patient_id = (SELECT canon_id FROM par)
WHERE patient_id = (SELECT dup_id FROM par);

-- Tablas por scope-string ('patient:<id>')
UPDATE hub_config SET scope = 'patient:' || (SELECT canon_id FROM par)
WHERE scope = 'patient:' || (SELECT dup_id FROM par)
  AND NOT EXISTS (
      SELECT 1 FROM hub_config h2
      WHERE h2.scope = 'patient:' || (SELECT canon_id FROM par)
        AND h2.key = hub_config.key
  );
DELETE FROM hub_config WHERE scope = 'patient:' || (SELECT dup_id FROM par);

UPDATE support_messages SET scope = 'patient:' || (SELECT canon_id FROM par)
WHERE scope = 'patient:' || (SELECT dup_id FROM par);

UPDATE timer_presets_remote SET scope = 'patient:' || (SELECT canon_id FROM par)
WHERE scope = 'patient:' || (SELECT dup_id FROM par)
  AND NOT EXISTS (
      SELECT 1 FROM timer_presets_remote t2
      WHERE t2.scope = 'patient:' || (SELECT canon_id FROM par)
        AND t2.name = timer_presets_remote.name
  );
DELETE FROM timer_presets_remote WHERE scope = 'patient:' || (SELECT dup_id FROM par);

-- tcc_templates / routine_templates usan scope-string también
UPDATE tcc_templates SET scope = 'patient:' || (SELECT canon_id FROM par)
WHERE scope = 'patient:' || (SELECT dup_id FROM par);

-- patient_routine_template (PK = patient_id: solo migrar si la canónica no tiene)
UPDATE patient_routine_template SET patient_id = (SELECT canon_id FROM par)
WHERE patient_id = (SELECT dup_id FROM par)
  AND NOT EXISTS (
      SELECT 1 FROM patient_routine_template
      WHERE patient_id = (SELECT canon_id FROM par)
  );
DELETE FROM patient_routine_template WHERE patient_id = (SELECT dup_id FROM par);

-- Cierre: eliminar la fila duplicada (CASCADE limpia cualquier resto)
DELETE FROM patients WHERE patient_id = (SELECT dup_id FROM par);

-- Reporte final del par (honesto: distingue merge real de bloque omitido)
SELECT CASE
           WHEN (SELECT dup_id FROM par) = 'PEGAR_DUP_ID_ACA'
               THEN 'BLOQUE 2 omitido — completá dup_id/canon_id para mergear'
           ELSE 'merge OK — fila duplicada eliminada'
       END AS resultado,
       (SELECT canon_id FROM par) AS paciente_canonico;

DROP TABLE par;

COMMIT;
-- (Si algo falló a mitad de camino: ROLLBACK; y revisar el error.)


-- ─────────────────────────────────────────────────────────────────────────────
-- BLOQUE 3 · VERIFICACIÓN POST-MERGE (solo lectura)
-- Debe devolver 0 filas cuando no quedan duplicados por nombre.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT lower(trim(patient_name)) AS nombre, count(*) AS filas,
       array_agg(patient_id ORDER BY created_at) AS ids
FROM patients
GROUP BY lower(trim(patient_name))
HAVING count(*) > 1;
