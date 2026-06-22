# Episode: C0_GATE_HARNESS

## Identificacion

- **ID episodio:** 20260621_235455_C0_GATE_HARNESS
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `634348b`)
- **Perfil usado:** nm_suite_visual_qa
- **Agente/Modelo:** Codex

## Objetivo

Ejecutar C0-GATE-HARNESS: invalidar E5 como cierre visual, conservar `c0c692e` como cierre
tecnico no rollback y crear el formato de checklist visual trazado que reemplaza el cierre
por tests/capturas verdes.

## No objetivos

- No tocar UI/producto/tests/QA ejecutable.
- No generar ZIP.
- No regenerar capturas.
- No ejecutar C1 dentro de este episodio.

## Presupuesto

- **Presupuesto maximo:** docs/harness + validacion textual.

## Scope

### Archivos permitidos

- `agent_harness/HARNESS_CONTRACT.md`
- `agent_harness/EVIDENCE_PACKAGE_TEMPLATE.md`
- `agent_harness/VISUAL_REVIEW_CHECKLIST_TEMPLATE.md`
- `agent_harness/episodes/20260621_235455_C0_GATE_HARNESS/EPISODE.md`

### Archivos prohibidos

- Producto/tests/QA ejecutable/DB/sync/build/dist/installers.
- `PLAN_MIGRACION_UI_V2.md`.
- `qa/_captures_v8/`, `qa/_mockup_targets/`, `qa/_fidelity_*`.

## Estado inicial

- **Baseline antes:** `git status --short --branch` -> `## main...origin/main`.
- C0 defects abiertos en `E6_OWNER_VISUAL_AUDIT/DEFECT_LEDGER.md`: V2-P0-006,
  V2-P0-007, V2-P0-008.

## Plan

- **Plan corto:**
  1. Actualizar contrato para separar evidencia tecnica de aprobacion visual.
  2. Agregar template central de checklist visual.
  3. Actualizar template de evidencia para exigir checklist en UI visual.
  4. Validar textual y diff acotado.
  5. Cerrar episodio C0.

## Ejecucion

- **Cambios realizados:**
  - `HARNESS_CONTRACT.md` ahora prohibe cerrar UI visual con tests/probe/capturas como
    unica evidencia.
  - `VISUAL_REVIEW_CHECKLIST_TEMPLATE.md` define campos por pantalla/estado/tema,
    before/after, defectos y decision.
  - `EVIDENCE_PACKAGE_TEMPLATE.md` exige checklist visual para episodios UI.
  - `c0c692e` queda registrado como cierre tecnico exitoso pero visualmente fallido.

## Validacion

- **Validacion ejecutada:**
  - `rg -n "capturas generadas|aprobacion visual|Cierre visual trazado|c0c692e|VISUAL_REVIEW_CHECKLIST_TEMPLATE|tests verdes|before/after|P0/P1" ...`
    -> reglas C0 presentes en contrato, template de evidencia, checklist y episodio.
  - `git diff --name-only` -> solo archivos permitidos de harness/episodio.
  - `git status --short --branch` -> cambios limitados a C0.

## Evidencia

- **Antes:** harness permitia que la evidencia tecnica se leyera como cierre visual.
- **Despues:** cierre visual requiere checklist trazado; C0 no tiene superficie UI, por lo
  que before/after es documental.

## Resultado

- **Diff stat:** harness contract + evidence template + checklist template + episodio C0.
- **Archivos tocados:**
  - `agent_harness/HARNESS_CONTRACT.md`
  - `agent_harness/EVIDENCE_PACKAGE_TEMPLATE.md`
  - `agent_harness/VISUAL_REVIEW_CHECKLIST_TEMPLATE.md`
  - `agent_harness/episodes/20260621_235455_C0_GATE_HARNESS/EPISODE.md`
- **Commit:** este commit (`docs(ui): enforce traced visual gate`)
- **Deuda restante:** C1-C6 siguen pendientes; C0 baja V2-P0-006, V2-P0-007 y V2-P0-008.

## Decision final

- [x] Commit
- [ ] Rollback
- [ ] Pedir revision
- [ ] Descartar
