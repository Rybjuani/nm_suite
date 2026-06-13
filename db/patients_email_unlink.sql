-- ============================================================================
-- db/patients_email_unlink.sql — Email visible + desvinculación de pacientes
-- Ejecutar en: Supabase Dashboard → SQL Editor (una sola vez, owner)
--
-- QUÉ AGREGA (decisión owner v1.0 final):
--   1. patients.email     — el email declarado en el alta. El Hub lo muestra
--      en la lista para DISTINGUIR pacientes con el mismo nombre (caso real:
--      dos "Juan Cruz" con cuentas distintas).
--   2. patients.unlinked  — el profesional puede quitar un paciente del Hub
--      con la X de su fila. El paciente desvinculado:
--        * desaparece de la lista del Hub (sus datos NO se borran);
--        * su Suite deja de sincronizar (queda offline-only);
--        * si quiere retomar el tratamiento, crea una cuenta nueva.
--
-- Es seguro correrlo más de una vez (IF NOT EXISTS / idempotente).
-- ============================================================================

begin;

alter table public.patients add column if not exists email    text    default '';
alter table public.patients add column if not exists unlinked boolean default false;

-- Backfill: copiar el email real de la cuenta Supabase Auth a las filas
-- existentes (las altas nuevas lo escriben solas desde la Suite).
update public.patients p
set email = u.email
from auth.users u
where u.id::text = p.patient_id
  and (p.email is null or p.email = '');

commit;

-- Verificación rápida (debería listar email y unlinked=false):
--   select patient_id, patient_name, email, unlinked from public.patients;
