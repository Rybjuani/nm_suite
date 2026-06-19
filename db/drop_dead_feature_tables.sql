-- drop_dead_feature_tables.sql
-- Limpieza Fase 5: tablas remotas auditadas como no usadas.
--
-- Ejecutar en Supabase Dashboard -> SQL Editor con permisos de owner.
-- El schema base ya no las crea y el producto no las lee ni escribe.

begin;

drop table if exists public.ia_chat_history;
drop table if exists public.breathing_presets_remote;

commit;
