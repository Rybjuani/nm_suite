-- Tabla separada de auditoria legal para consentimientos de NeuroMood Suite.
-- No mezclar con tablas clinicas, registros de modulos ni sync funcional.

create table if not exists public.legal_consents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null,
    patient_id text,
    email text not null,
    accepted_at_utc timestamptz not null,
    product_name text not null,
    neuromood_suite_version text not null,
    instalador_suite_version text not null,
    disclaimer_version text not null,
    privacy_version text not null,
    disclaimer_text_hash text not null,
    privacy_text_hash text not null,
    consent_scope text not null,
    professional_team_id text,
    status text not null default 'vigente'
        check (status in ('vigente', 'pendiente', 'revocado', 'desactualizado')),
    created_at timestamptz not null default now()
);

create index if not exists legal_consents_patient_idx
    on public.legal_consents (patient_id, accepted_at_utc desc);

create index if not exists legal_consents_user_idx
    on public.legal_consents (user_id, accepted_at_utc desc);

create index if not exists legal_consents_status_idx
    on public.legal_consents (status);

alter table public.legal_consents enable row level security;

-- Politicas sugeridas:
-- 1) Usuarios autenticados pueden insertar su propio consentimiento.
-- 2) Usuarios autenticados pueden leer su propio consentimiento.
-- 3) El Hub debe leer consentimientos solo de pacientes vinculados mediante
--    la politica/rol que ya use el proyecto para visualizacion profesional.

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
          and tablename = 'legal_consents'
          and policyname = 'legal_consents_insert_own'
    ) then
        create policy "legal_consents_insert_own"
        on public.legal_consents
        for insert
        to authenticated
        with check (auth.uid() = user_id);
    end if;
end $$;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
          and tablename = 'legal_consents'
          and policyname = 'legal_consents_select_own'
    ) then
        create policy "legal_consents_select_own"
        on public.legal_consents
        for select
        to authenticated
        using (auth.uid() = user_id);
    end if;
end $$;

-- No habilitar SELECT anon amplio sobre consentimientos.
-- La version previa incluia `legal_consents_select_anon_hub using (true)`,
-- lo que exponia todas las constancias a cualquiera con la anon key. El Hub
-- debe consultar consentimientos mediante una ruta autenticada/RLS profesional
-- antes de uso clinico real; mientras tanto, si no hay sesion autorizada,
-- debe tratar el consentimiento como pendiente.
do $$
begin
    if exists (
        select 1 from pg_policies
        where schemaname = 'public'
          and tablename = 'legal_consents'
          and policyname = 'legal_consents_select_anon_hub'
    ) then
        drop policy "legal_consents_select_anon_hub" on public.legal_consents;
    end if;
end $$;
