-- mood_valencia_migration.sql — Registro positivo/negativo separado (v1.0 ronda 2)
--
-- EJECUTAR UNA VEZ en el SQL Editor de Supabase (la anon key no puede hacer DDL).
-- Sin estas columnas, el sync de ánimo del Suite y los gráficos del Hub fallan
-- (decisión owner: sin fallbacks — el schema nuevo es requisito).
--
-- Qué agrega a mood_records:
--   emocion    texto de la emoción elegida ("Calma", "Tristeza", ...)
--   valencia   'positiva' | 'negativa' | 'neutral'
--   intensidad intensidad CRUDA 1-10 elegida por el paciente (sin invertir)
--
-- El puntaje existente (bienestar 1-10) se conserva como índice combinado.

alter table mood_records add column if not exists emocion text not null default '';
alter table mood_records add column if not exists valencia text not null default 'neutral';
alter table mood_records add column if not exists intensidad integer;

-- Backfill de históricos: sin emoción registrada se asume neutral con
-- intensidad = puntaje (los registros nuevos llegan completos desde el Suite).
update mood_records
   set intensidad = puntaje
 where intensidad is null;
