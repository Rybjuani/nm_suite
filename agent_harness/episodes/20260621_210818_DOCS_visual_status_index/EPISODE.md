# Episode: DOCS_visual_status_index

## Identificación

- **ID episodio:** 20260621_210818_DOCS_visual_status_index
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `5c12ab5`)
- **Perfil usado:** generic_docs
- **Agente/Modelo:** Codex

## Objetivo

Crear un indice de vigencia en `docs/` para evitar que handoffs/planes visuales historicos
reabran deuda UI V2 ya cerrada.

## No objetivos

- No editar codigo de producto ni tests.
- No reescribir docs historicos fase por fase.
- No cambiar el resultado tecnico de E5.

## Presupuesto

- **Presupuesto maximo:** 1 doc nuevo + validacion textual.

## Scope

### Archivos permitidos

- `docs/README.md`
- `agent_harness/episodes/20260621_210818_DOCS_visual_status_index/EPISODE.md`

### Archivos prohibidos

- Producto/tests/QA ejecutable/DB/sync/build/dist/installers.
- Docs historicos fuera del indice salvo necesidad puntual.

## Estado inicial

- **Baseline antes:** `main` == `origin/main` en `5c12ab5`; worktree limpio.

## Plan

- **Plan corto:**
  1. Crear `docs/README.md` con fuente de verdad actual y lista de docs historicos.
  2. Validar que el indice no contradiga `PLAN_MIGRACION_UI_V2.md`.
  3. Cerrar con diff/stat.

## Ejecución

- **Cambios realizados:**
  - Creado `docs/README.md` como indice de vigencia para docs de UI/QA visual.
  - El indice marca `PLAN_MIGRACION_UI_V2.md` + episodio E5 como fuente vigente y deja
    `FASE*.md`/handoffs previos como historicos.

## Validación

- **Validación ejecutada:**
  - `rg -n "c0c692e|5c12ab5|runtime_live_probe|capture_v8|diff_fidelity" docs\README.md`
    -> referencias presentes.
  - `git diff --stat` -> solo `docs/README.md` + este episodio.

## Evidencia

- **Antes:** `docs/HANDOFF_CONTINUACION_LOCAL.md` y `docs/FASE*.md` contienen deuda visual
  historica anterior al cierre `c0c692e`/`5c12ab5`.
- **Después:** `docs/README.md` explica la fuente de verdad vigente y el caracter historico
  de esos docs.

## Resultado

- **Diff stat:** `docs/README.md` + este episodio.
- **Archivos tocados:**
  - `docs/README.md`
  - `agent_harness/episodes/20260621_210818_DOCS_visual_status_index/EPISODE.md`
- **Commit:** pendiente
- **Deuda restante:** sin deuda documental accionable detectada en docs de UI/QA visual;
  los docs historicos quedan explicitamente marcados como no-backlog vivo.

## Decisión final

- [x] Commit
- [ ] Rollback
- [ ] Pedir revisión
- [ ] Descartar
