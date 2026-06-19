-- secure_rls_hardening.sql
-- NeuroMood emergency RLS hardening.
--
-- Ejecutar en Supabase Dashboard -> SQL Editor con permisos de owner.
-- Objetivo: bloquear lectura/escritura anon sobre datos clinicos y consentimientos.
--
-- Importante:
-- - Esto corrige la exposicion con anon key.
-- - El Hub profesional accede libremente sin login utilizando las credenciales base de Supabase.
-- - La Suite paciente puede operar con authenticated si patient_id = auth.uid().

begin;

-- Quitar policies anon amplias conocidas.
drop policy if exists "legal_consents_select_anon_hub" on public.legal_consents;

-- Asegurar RLS en tablas clinicas/sensibles.
alter table public.patients              enable row level security;
alter table public.mood_records          enable row level security;
alter table public.breathing_sessions    enable row level security;
alter table public.thought_records       enable row level security;
alter table public.checklist_completions enable row level security;
alter table public.timer_sessions        enable row level security;
alter table public.reminder_logs         enable row level security;
alter table public.activation_results    enable row level security;
alter table public.assigned_tasks        enable row level security;
alter table public.assigned_reminders    enable row level security;
alter table public.patient_activities    enable row level security;
alter table public.legal_consents        enable row level security;
alter table public.ia_audit_log          enable row level security;
alter table public.hub_config            enable row level security;
alter table public.patient_routine_template enable row level security;

-- Defense-in-depth: anon no debe tener privilegios directos sobre datos clinicos.
revoke all on table public.patients              from anon;
revoke all on table public.mood_records          from anon;
revoke all on table public.breathing_sessions    from anon;
revoke all on table public.thought_records       from anon;
revoke all on table public.checklist_completions from anon;
revoke all on table public.timer_sessions        from anon;
revoke all on table public.reminder_logs         from anon;
revoke all on table public.activation_results    from anon;
revoke all on table public.assigned_tasks        from anon;
revoke all on table public.assigned_reminders    from anon;
revoke all on table public.patient_activities    from anon;
revoke all on table public.legal_consents        from anon;
revoke all on table public.ia_audit_log          from anon;
revoke all on table public.hub_config            from anon;
revoke all on table public.patient_routine_template from anon;

-- Permisos base para usuarios autenticados. RLS sigue filtrando filas.
grant select, insert, update on table public.patients              to authenticated;
grant select, insert, update, delete on table public.mood_records          to authenticated;
grant select, insert, update, delete on table public.breathing_sessions    to authenticated;
grant select, insert, update, delete on table public.thought_records       to authenticated;
grant select, insert, update, delete on table public.checklist_completions to authenticated;
grant select, insert, update, delete on table public.timer_sessions        to authenticated;
grant select, insert, update, delete on table public.reminder_logs         to authenticated;
grant select, insert, update, delete on table public.activation_results    to authenticated;
grant select, insert, update, delete on table public.patient_activities    to authenticated;
grant select on table public.assigned_tasks        to authenticated;
grant select on table public.assigned_reminders    to authenticated;
grant update (completado_en) on table public.assigned_reminders to authenticated;
grant select, insert on table public.legal_consents to authenticated;
grant select, insert on table public.ia_audit_log   to authenticated;
grant select on table public.hub_config to authenticated;
grant select on table public.patient_routine_template to authenticated;

-- Patients: el instalador actual usa auth.uid() como patient_id para usuarios nuevos.
drop policy if exists "patients_select_own" on public.patients;
create policy "patients_select_own"
on public.patients
for select
to authenticated
using (patient_id = auth.uid()::text);

drop policy if exists "patients_insert_own" on public.patients;
create policy "patients_insert_own"
on public.patients
for insert
to authenticated
with check (patient_id = auth.uid()::text);

drop policy if exists "patients_update_own" on public.patients;
create policy "patients_update_own"
on public.patients
for update
to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

-- Helper repetido para tablas con patient_id.
drop policy if exists "mood_records_own" on public.mood_records;
create policy "mood_records_own" on public.mood_records
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "breathing_sessions_own" on public.breathing_sessions;
create policy "breathing_sessions_own" on public.breathing_sessions
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "thought_records_own" on public.thought_records;
create policy "thought_records_own" on public.thought_records
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "checklist_completions_own" on public.checklist_completions;
create policy "checklist_completions_own" on public.checklist_completions
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "timer_sessions_own" on public.timer_sessions;
create policy "timer_sessions_own" on public.timer_sessions
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "reminder_logs_own" on public.reminder_logs;
create policy "reminder_logs_own" on public.reminder_logs
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "activation_results_own" on public.activation_results;
create policy "activation_results_own" on public.activation_results
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "patient_activities_own" on public.patient_activities;
create policy "patient_activities_own" on public.patient_activities
for all to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

-- Asignaciones: el paciente autenticado solo lee lo propio.
drop policy if exists "assigned_tasks_select_own" on public.assigned_tasks;
create policy "assigned_tasks_select_own" on public.assigned_tasks
for select to authenticated
using (patient_id = auth.uid()::text);

drop policy if exists "assigned_reminders_select_own" on public.assigned_reminders;
create policy "assigned_reminders_select_own" on public.assigned_reminders
for select to authenticated
using (patient_id = auth.uid()::text);

drop policy if exists "assigned_reminders_update_completion_own" on public.assigned_reminders;
create policy "assigned_reminders_update_completion_own" on public.assigned_reminders
for update to authenticated
using (patient_id = auth.uid()::text)
with check (patient_id = auth.uid()::text);

drop policy if exists "patient_routine_template_select_own" on public.patient_routine_template;
create policy "patient_routine_template_select_own" on public.patient_routine_template
for select to authenticated
using (patient_id = auth.uid()::text);

drop policy if exists "hub_config_select_global_or_own" on public.hub_config;
create policy "hub_config_select_global_or_own" on public.hub_config
for select to authenticated
using (scope = 'global' or scope = ('patient:' || auth.uid()::text));

-- Consentimientos: mantener atado a auth.uid().
drop policy if exists "legal_consents_insert_own" on public.legal_consents;
create policy "legal_consents_insert_own"
on public.legal_consents
for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "legal_consents_select_own" on public.legal_consents;
create policy "legal_consents_select_own"
on public.legal_consents
for select
to authenticated
using (auth.uid() = user_id);

-- IA: el paciente autenticado solo ve/escribe su propio historial si hay patient_id.
drop policy if exists "ia_audit_log_patient_own" on public.ia_audit_log;
create policy "ia_audit_log_patient_own" on public.ia_audit_log
for select to authenticated
using (patient_id is null or patient_id = auth.uid()::text);

-- ── Tablas de config global — acceso authenticated ───────────────────────────
-- Sin estas policies, tras habilitar RLS en feature_schemas.sql, el sync de
-- la Suite no puede importar presets/mensajes/plantillas (queda en blanco).
-- El Hub tampoco puede leer los editores de config. Writes del Hub a estas
-- tablas globales requieren service_role o auth profesional (PENDIENTE).

grant select on table public.timer_presets_remote     to authenticated;
grant select on table public.support_messages         to authenticated;
grant select on table public.tcc_templates            to authenticated;
grant select on table public.routine_templates        to authenticated;
grant select on table public.activity_bank            to authenticated;

drop policy if exists "timer_presets_select_authenticated" on public.timer_presets_remote;
create policy "timer_presets_select_authenticated" on public.timer_presets_remote
for select to authenticated
using (scope = 'global' or scope = ('patient:' || auth.uid()::text));

drop policy if exists "support_messages_select_authenticated" on public.support_messages;
create policy "support_messages_select_authenticated" on public.support_messages
for select to authenticated
using (scope = 'global' or scope = ('patient:' || auth.uid()::text));

drop policy if exists "tcc_templates_select_authenticated" on public.tcc_templates;
create policy "tcc_templates_select_authenticated" on public.tcc_templates
for select to authenticated
using (scope = 'global' or scope = ('patient:' || auth.uid()::text));

drop policy if exists "routine_templates_select_authenticated" on public.routine_templates;
create policy "routine_templates_select_authenticated" on public.routine_templates
for select to authenticated
using (true);

drop policy if exists "activity_bank_select_authenticated" on public.activity_bank;
create policy "activity_bank_select_authenticated" on public.activity_bank
for select to authenticated
using (true);

commit;
