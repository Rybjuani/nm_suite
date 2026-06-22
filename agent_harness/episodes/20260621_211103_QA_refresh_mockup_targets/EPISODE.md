# Episode: QA_refresh_mockup_targets

## Identificación

- **ID episodio:** 20260621_211103_QA_refresh_mockup_targets
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `a5138d4`)
- **Perfil usado:** generic_docs
- **Agente/Modelo:** Codex

## Objetivo

Eliminar deuda de artefactos QA visuales versionados: refrescar `qa/_mockup_targets/`
contra el HEAD actual y retirar/ignorar evidencia `_fidelity_fresh` historica si sigue
versionada como si fuera vigente.

## No objetivos

- No tocar UI/producto/tests funcionales.
- No cambiar thresholds ni semantica de `diff_fidelity.py`.
- No tocar build/dist/installers.

## Presupuesto

- **Presupuesto maximo:** 1 corrida `capture_mockup.py --all --theme both --clean`, una
  decision sobre `_fidelity_fresh`, validacion textual y `pytest` focal de QA tools.

## Scope

### Archivos permitidos

- `qa/_mockup_targets/**`
- `qa/_fidelity_fresh/**`
- `.gitignore`
- `docs/README.md`
- `agent_harness/episodes/20260621_211103_QA_refresh_mockup_targets/EPISODE.md`

### Archivos prohibidos

- Producto/tests no-QA/build/dist/installers/DB/sync.
- `qa/capture_v8.py`, `qa/diff_fidelity.py`, `qa/capture_mockup.py` salvo solo lectura.

## Estado inicial

- **Baseline antes:** `main` == `origin/main` en `a5138d4`; worktree limpio.
- `qa/_mockup_targets/MOCKUP_TARGET_MANIFEST.json` declara commit `51f4448`.
- `qa/_fidelity_fresh/` esta versionado con reporte historico.

## Plan

- **Plan corto:**
  1. Regenerar targets mockup con `capture_mockup.py --all --theme both --clean`.
  2. Revisar diff/manifest.
  3. Decidir si `_fidelity_fresh` se elimina o se conserva marcado como historico.
  4. Validar `tests/test_mockup_qa_tools.py`.
  5. Cerrar con evidencia y commit.

## Ejecución

- **Cambios realizados:**
  - Regenerado `qa/_mockup_targets/` con `capture_mockup.py --all --theme both --clean`.
  - Eliminado `qa/_fidelity_fresh/` del repositorio: era reporte historico de diff, no
    fuente vigente.
  - Agregado `qa/_fidelity_fresh/` a `.gitignore`.
  - Actualizado `docs/README.md` para declarar targets canonicos frescos y reports diff
    efimeros.

## Validación

- **Validación ejecutada:**
  - `.\.venv\Scripts\python.exe qa\capture_mockup.py --all --theme both --clean`
    -> Saved targets=96, Failed targets=0.
  - `.\.venv\Scripts\python.exe -m pytest tests\test_mockup_qa_tools.py tests\test_capture_v8_evidence.py -q`
    -> 13 passed.
  - `.\.venv\Scripts\python.exe qa\diff_fidelity.py --no-images`
    -> Compared=96, Missing actuals=0, Partial evidence=0, Failures=92 por umbral
    SSIM/MAD auxiliar no-gate.

## Evidencia

- **Antes:** manifest de targets apuntaba a `51f4448`; `_fidelity_fresh` tenia reports
  historicos versionados.
- **Después:** manifest de targets apunta a `a5138d4`; `_fidelity_fresh/` queda removido
  e ignorado.

## Resultado

- **Diff stat:** targets mockup regenerados + purga `_fidelity_fresh` + docs/ignore.
- **Archivos tocados:**
  - `qa/_mockup_targets/**`
  - `qa/_fidelity_fresh/**` (eliminado)
  - `.gitignore`
  - `docs/README.md`
  - `agent_harness/episodes/20260621_211103_QA_refresh_mockup_targets/EPISODE.md`
- **Commit:** este commit (`chore(qa): refresh mockup targets`)
- **Deuda restante:** cero deuda accionable. `diff_fidelity.py` conserva failures por
  SSIM/MAD auxiliar no-gate, pero sin missing actuals ni partial evidence.

## Decisión final

- [x] Commit
- [ ] Rollback
- [ ] Pedir revisión
- [ ] Descartar
