# Episode: E5_FIDELITY_final_visual_qa

## Identificación

- **ID episodio:** 20260621_202526_E5_FIDELITY_final_visual_qa
- **Fecha:** 2026-06-21
- **Repo objetivo:** nm_suite (`main` @ `4059a74`)
- **Perfil usado:** nm_suite_visual_qa
- **Agente/Modelo:** Codex

## Objetivo

Ejecutar cierre E5 de fidelidad: probe runtime completo, capturas finales `capture_v8`,
diff auxiliar contra mockup y revision de evidencia para declarar deuda cero o abrir un
defecto puntual verificable.

## No objetivos

- No perseguir SSIM como gate.
- No tocar DB/sync/logica clinica/auth/build/dist/installers.
- No mezclar fixes de multiples clusters.

## Presupuesto

- **Presupuesto maximo:** 1 probe completo + 1 captura completa + 1 diff completo +
  revision de reportes. Fix solo si es minimo, local y evidenciado.

## Scope

### Archivos permitidos

- `agent_harness/episodes/20260621_202526_E5_FIDELITY_final_visual_qa/EPISODE.md`
- `PLAN_MIGRACION_UI_V2.md`
- `shared/components/dialogs.py`
- `hub/pacientes_qt.py`
- `qa/capture_v8.py`
- `tests/test_component_visual_contract.py`
- `tests/test_hub_visual_contract.py`
- Artefactos efimeros ignorados por git bajo `qa/_runtime_probe/`, `qa/_captures_v8/`,
  `qa/_fidelity_diff/`.

### Archivos prohibidos

- DB/sync/logica clinica/auth/build/dist/installers.
- Producto/tests fuera de los archivos permitidos.

## Estado inicial

- **Baseline antes:** `main` == `origin/main` en `4059a74`; worktree limpio.

## Plan

- **Plan corto:**
  1. Correr `runtime_live_probe.py --all --theme both`.
  2. Correr `capture_v8.py --all --theme both`.
  3. Correr `diff_fidelity.py` como señal auxiliar.
  4. Revisar manifest/reportes por fallos tecnicos o deuda accionable.
  5. Cerrar con status, diff, validacion y deuda restante.

## Ejecución

- **Cambios realizados:**
  - `hub/pacientes_qt.py`: el modal Resumen IA queda en panel natural `480x325`
    (target mockup) con contenido scrolleable.
  - `shared/components/dialogs.py`: el borde/radio de `NMDialog` queda scopiado a
    `QFrame#NMDialogPanel`, evitando fuga visual a `QFrame` internos.
  - `qa/capture_v8.py`: `detalle-resumen-ia` captura el panel interno del `NMDialog`
    overlay en vez de buscar un `QDialog` top-level obsoleto.
  - Tests de contrato actualizados para bloquear selector scoped y alto del modal IA.

## Validación

- **Validación ejecutada:**
  - `.\.venv\Scripts\python.exe qa\runtime_live_probe.py --all --theme both`
    → OK=22, DEFECTS_FOUND=0, FAILED=0.
  - `.\.venv\Scripts\python.exe qa\capture_v8.py --all --theme both`
    → Saved captures=98, Failed captures=0, Technical evidence=98.
  - `.\.venv\Scripts\python.exe qa\diff_fidelity.py`
    → Compared=96, Missing actuals=0, Partial evidence=0, Failures=92 por umbral
    SSIM/MAD auxiliar; no es gate segun `PLAN_MIGRACION_UI_V2.md`.
  - `.\.venv\Scripts\python.exe -m pytest tests\`
    → 317 passed.
  - `.\.venv\Scripts\python.exe -m ruff check shared\components\dialogs.py hub\pacientes_qt.py qa\capture_v8.py tests\test_component_visual_contract.py tests\test_hub_visual_contract.py tests\test_mockup_qa_tools.py`
    → All checks passed.
  - Barrido visual de 4 hojas de contacto generadas desde las 98 capturas
    → sin clipping/blank/wrong-view/overlap accionable observado.

## Evidencia

- **Antes:** probe completo y tests completos verdes desde `4059a74`.
- **Después:** `qa/_runtime_probe/PROBE_MANIFEST.json`,
  `qa/_captures_v8/CAPTURE_MANIFEST.json`, `qa/_fidelity_diff/FIDELITY_REPORT.md`
  y hojas de contacto `qa/_fidelity_diff/E5_all_actuals_contact_*.png` (artefactos
  efimeros ignorados por git).

## Resultado

- **Diff stat:** fix acotado en modal/harness/tests + cierre documental.
- **Archivos tocados:**
  - `shared/components/dialogs.py`
  - `hub/pacientes_qt.py`
  - `qa/capture_v8.py`
  - `tests/test_component_visual_contract.py`
  - `tests/test_hub_visual_contract.py`
  - `PLAN_MIGRACION_UI_V2.md`
  - `agent_harness/episodes/20260621_202526_E5_FIDELITY_final_visual_qa/EPISODE.md`
- **Commit:** `c0c692e`
- **Deuda restante:** cero deuda accionable detectada. Los 92 failures de
  `diff_fidelity.py` quedan registrados como señal auxiliar no-gate por techo de render
  Qt/Chromium y diferencias aceptadas; no hay missing actuals ni captura fallida.

## Decisión final

- [x] Commit
- [ ] Rollback
- [ ] Pedir revisión
- [ ] Descartar
