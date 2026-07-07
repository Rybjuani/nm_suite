# Fase 0D Checklist — Aceptación

> **Fase 0D — migration planning. No runtime authority. No visual closure.**
>
> Checklist de aceptación para Fase 0D. Cada item debe marcarse `[x]` antes
> de commit. Si algún item queda `[ ]`, Fase 0D no se considera completa.

## Docs creados

- [x] `docs/VisualParity_V3_1/OWNER_DECISIONS_LOCKED.md` creado con 5
  decisiones `LOCKED_FOR_V3_1`, 6 `STILL_OWNER_DECISION_REQUIRED`, 5
  `NOT_DECIDED_IN_THIS_PHASE`.
- [x] `docs/VisualParity_V3_1/FORENSIC_SNAPSHOT_PREFLIGHT.md` creado con
  preflight A+, comandos marcados `FUTURE_PHASE_ONLY`, prohibiciones
  explícitas (no tag/bundle/release en 0D, no Git Bash/WSL).
- [x] `docs/VisualParity_V3_1/MIGRATION_A_PLUS_EXECUTION_PLAN.md` creado con
  8 pasos ordenados, cada uno con objetivo/files allowed/files
  forbidden/validation/rollback, comandos destructivos marcados
  `FUTURE_PHASE_ONLY`.
- [x] `docs/VisualParity_V3_1/PHASE_0D_CHECKLIST.md` (este archivo) creado.

## Scripts creados

- [x] `tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1` creado.
  Sólo dry-run. No crea tag/bundle/release. No escribe archivos. No hace
  push. No modifica repo.
- [x] `tools/visualparity/phase0d/README.md` creado.

## Docs existentes actualizados

- [x] `docs/VisualParity_V3_1/PHASE_0A_DECISIONS.md` actualizado: 5
  decisiones cerradas marcadas como resueltas, referencian
  `OWNER_DECISIONS_LOCKED.md`. Resto pendiente.
- [x] `docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` actualizado: referencia
  `FORENSIC_SNAPSHOT_PREFLIGHT.md` y `MIGRATION_A_PLUS_EXECUTION_PLAN.md`.
  Aclara que Fase 0D no ejecuta tag/bundle.
- [x] `docs/VisualParity_V3_1/CHANGELOG.md` actualizado con entrada Fase 0D.
- [x] `tools/visualparity/phase0b/validate_phase0b.py` actualizado si
  necesario (grupo M para validar docs Fase 0D).
- [x] `tools/visualparity/phase0b/README.md` actualizado si el validador
  cambió.

## Prohibiciones (no debe haber)

- [x] No tag real creado (`git tag -l forensic-pre-v3.1` devuelve vacío).
- [x] No bundle real creado (no existe `nm_suite-forensic-pre-v3.1.bundle`
  en filesystem ni en git).
- [x] No GitHub Release creado.
- [x] No V1/V2 removidos del working tree (`qa/close_visual_key.py` etc.
  siguen presentes; `harness/ci_gate/` etc. siguen presentes).
- [x] No producto modificado (`app/`, `hub/`, `shared/`, `db/`, `assets/`,
  `installers/` sin cambios).
- [x] No canon modificado (`qa/_mockup_canonical/`, `qa/pack canonico/` sin
  cambios).
- [x] No evidence records modificados (`docs/closure_evidence/` sin
  cambios).
- [x] No handoff modificado (`VISUAL_REPAIR_HANDOFF.md` sin cambios).
- [x] No workflow legacy modificado
  (`.github/workflows/visual-closure-replay.yml` sin cambios).
- [x] No cierre de keys.
- [x] No reapertura de keys.
- [x] No `--force` usado.
- [x] No commit de `.bundle`/`.zip`/`.tar.gz`/evidence V1/scripts V1/V2 a
  `main`.

## Validaciones

- [x] Validador Fase 0B PASS (12/12 grupos o 13/13 si se agregó grupo M).
- [x] Runner PowerShell `run_phase0b.ps1` PASS o `NOT_EXECUTABLE` (Linux
  sandbox sin pwsh).
- [x] Runner PowerShell `preflight_snapshot_dry_run.ps1` PASS o
  `NOT_EXECUTABLE` (Linux sandbox sin pwsh).
- [x] Workflow governance `visual-parity-v3-governance.yml` no modificado
  salvo si estrictamente necesario (no fue necesario en Fase 0D).

## Scope

- [x] `git status --short` sólo muestra archivos en:
  - `docs/VisualParity_V3_1/**`
  - `tools/visualparity/phase0b/**` (si el validador/README cambió)
  - `tools/visualparity/phase0d/**`
- [x] `git diff --stat` no muestra archivos fuera de scope.

## Commit

- [x] Un solo commit: `docs(visual-parity-v3.1): lock phase 0D migration
  decisions`.
- [x] No push sin verificación previa.
- [x] Push sólo si todos los items anteriores están `[x]`.

## Post-push

- [x] `git fetch origin` sincroniza.
- [x] `git rev-parse HEAD` == `git rev-parse origin/main`.
- [x] `git status --short --branch` muestra `## main...origin/main` (sin
  ahead/behind).

## Notas

- Si PowerShell no está disponible en el entorno de ejecución, los runners
  se marcan `NOT_EXECUTABLE` y no fallan la fase. Deben probarse en Windows
  real en primera oportunidad.
- Si el validador Fase 0B falla, corregir docs/skeletons V3.1 o el propio
  validador, no tocar legacy/product/canon/evidence.
- Si hay divergencia inesperada o cambios fuera de scope, NO hacer push;
  reportar bloqueo.
