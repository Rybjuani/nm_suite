# Episode: E0_probe_baseline

## Identificación

- **ID episodio:** 20260621_175946_E0_probe_baseline
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `e95bc2b`)
- **Perfil usado:** nm_suite_visual_qa (read-only audit)
- **Agente/Modelo:** Claude Code (Opus 4.8)

## Objetivo

Baseline de gates para `PLAN_MIGRACION_UI_V2.md` (E0-PROBE-BASELINE): correr el runtime
probe + la suite pytest y escribir el primer `DEFECT_LEDGER.md`. Read-only.

## No objetivos

- No corregir nada (audit). No tocar código de producto ni tests.
- No declarar fidelidad. No perseguir SSIM.

## Presupuesto

- **Presupuesto máximo:** 1 corrida de probe + 1 corrida de pytest + diagnóstico mínimo.

## Scope

### Archivos permitidos

- Solo lectura del repo. Escritura limitada a esta carpeta de episodio
  (`EPISODE.md`, `DEFECT_LEDGER.md`).

### Archivos prohibidos

- Todo `app/`, `hub/`, `shared/`, `qa/`, `tests/` (read-only). DB/sync/build/installers.

## Estado inicial

- **Baseline antes:** `git status` limpio salvo `PLAN_MIGRACION_UI.md` (nota superseded) +
  `PLAN_MIGRACION_UI_V2.md` (nuevo). HEAD `e95bc2b`, `main` == `origin/main`.

## Plan

1. `runtime_live_probe.py --all --theme both`.
2. `pytest tests/`.
3. Si hay fallo, diagnóstico mínimo (aislado vs suite, causa).
4. Escribir `DEFECT_LEDGER.md` + handoff.

## Ejecución

- **Cambios realizados:** ninguno en código (audit). Generados: `EPISODE.md`,
  `DEFECT_LEDGER.md` (este episodio) + artefactos efímeros en `qa/_runtime_probe/`.

## Validación

- **Runtime probe:** OK=22 / DEFECTS=0 / FAILED=0 (suite+hub × light/dark, 960×600).
- **Pytest full:** 289 passed / 1 failed (456s).
- **Pytest aislado del fallo:** passed (1.25s) → order-dependiente.

## Evidencia

- **Antes:** N/A (baseline).
- **Después:** `qa/_runtime_probe/PROBE_MANIFEST.json`; `DEFECT_LEDGER.md` (D001).

## Resultado

- **Diff stat:** sin diff de código.
- **Archivos tocados:** ninguno de producto.
- **Commit:** N/A (audit; el ledger no requiere commit).
- **Deuda restante:** **D001** — `NMPlayButton` se deforma a 46×56 bajo `stylesheet_base`
  global (controles `.ctl` de Respiración/Timer ovalados en runtime real). Abrir
  **E1-PLAYBUTTON-GUARD**.

## Decisión final

- [ ] Commit
- [ ] Rollback
- [x] Pedir revisión  (handoff a E1-PLAYBUTTON-GUARD)
- [ ] Descartar
