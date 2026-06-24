# SENTINEL_REMOVAL.md — Retiro de Visual Sentinel (2026-06-24)

## Por qué se elimina
- Sentinel (qa/visual_sentinel.py, `audit-mockup` mode) no cumplió el objetivo
  de visión autónoma: el modo blind (sin herramienta `vision`) sólo podía
  clasificar P1s con evidencia cuantitativa (phash, diff PIL, edge density),
  insuficiente para reducir P1s de UI sin acceso visual humano.
- El sistema producía muchos falsos positivos por chrome de la Suite window
  (sidebar/bottom_nav) que el mockup canónico no incluye.
- El "P1 gate" consumía tiempo de iteración y tokens sin bajar P1 de manera
  medible: 15 microfixes intentados en LOOP_LOG_8 → 0 mejoras, 0 commits de
  producto revertidos.
- Próximo sistema futuro: **Visual Auditor V2** (no implementado en esta
  tarea, ver placeholder `qa/_visual_auditor_v2/` en .gitignore).

## Qué se eliminó

### Archivos de herramienta
- `qa/visual_sentinel.py` (3926 líneas, motor principal)
- `qa/visual_sentinel_contracts/` (10 archivos YAML de contratos por componente)
  - `global.yaml`, `components/{buttons,cards,dialogs,empty_states,forms,
    onboarding_legal,progress,scrollbars,tabs}.yaml`
- `qa/README_VISUAL_SENTINEL.md` (doc del sistema)
- `tests/test_visual_sentinel.py`

### Outputs regenerables (ya estaban gitignored, borrados del disco)
- `qa/_visual_sentinel/` (~42 MB: `latest/`, `runs/*`, `widget_trees/`, etc.)
- `qa/__pycache__/visual_sentinel.cpython-312.pyc`
- `tests/__pycache__/test_visual_sentinel.cpython-312-pytest-9.0.3.pyc`

## Qué se conserva

| Componente | Estado |
|------------|--------|
| `qa/capture_v8.py` (harness de capturas reales) | **Conservado** |
| `qa/capture_mockup.py` (snapshot estático del mockup HTML) | **Conservado** |
| `qa/mockup_reference_static/` (86 PNGs canónicos) | **Conservado** |
| `qa/diff_fidelity.py` | **Conservado** (no depende de Sentinel) |
| `qa/runtime_live_probe.py` | **Conservado** (no depende de Sentinel) |
| Tests visual-contract existentes (dbt, registro_tcc, rutina, hub, etc.) | **Conservados** |
| `neuromood-mockup.html` | **Conservado** |
| Código de producto (`app/`, `hub/`, `shared/`) | **Intacto** |

## Qué NO se conserva (eliminado)

- ❌ pHash P1 gate (basado en `imagehash.phash()`)
- ❌ `audit-mockup` mode
- ❌ Registry Sentinel (`MISSING_CAPTURE` / `MISSING_REFERENCE` / `PER_SURFACE_REGRESSION`)
- ❌ Reportes HTML de Sentinel (`index_mockup.html` con 3 columnas mockup|real|diff)
- ❌ `taxonomy_coverage` y `classification.json` (P0/P1/P2/P3 buckets)
- ❌ `_STATE_VIEW_ALIASES` registry (de Sentinel)
- ❌ `visual_sentinel_baselines/{proposed,approved}/`

## Revert de commit visual ciego no validado

- **Commit revertido**: `b0e65f6 fix(dbt): reduce Práctica STOP CTA size to sm (blind attempt, unverified)`
- **Revert commit**: `36bdd40 Revert "fix(dbt): reduce Práctica STOP CTA size to sm (blind attempt, unvalidated)"`
- **Estado en HEAD actual**: el fix de `b0e65f6` NO está aplicado.
  `app/modules/dbt_qt.py` está en su estado pre-fix (size="md" en btn_next).
- **Por qué se revirtió**: cambio visual ciego sin validación, no bajó P1,
  no debe quedar en main. El revert `36bdd40` ya estaba en `main` antes de
  esta tarea (lo aplicó el owner manualmente).

## Validación ejecutada
- `ruff check app hub shared qa tests`: **All checks passed**
- `pytest tests/test_dbt_visual_contract.py tests/test_registro_tcc_visual_contract.py
  tests/test_rutina_visual_contract.py tests/test_hub_visual_contract.py`:
  **24/24 passed**
- `pytest tests --collect-only`: **0 tests con "sentinel"** (verificado)
- `python -c "from qa import capture_v8"`: V8 import OK sin Sentinel
- `git diff --check`: clean
- `git grep visual_sentinel`: 0 referencias activas en `app/`, `hub/`,
  `shared/`, `qa/`, `tests/`, `pyproject.toml`, `requirements*.txt`

## Referencias históricas conservadas (no son comandos ni dependencias activas)

Los siguientes archivos contienen menciones textuales a Sentinel o phash
porque son **documentación de sesiones/auditorías previas**. NO son comandos
ejecutables ni dependencias activas. Se conservan como registro histórico.

- `qa/LOOP_LOG_5.md` — log del ciclo de fix de MISSING_REFERENCE en Sentinel
- `qa/LOOP_LOG_6.md` — log de clasificación heurística de P1s
- `qa/LOOP_LOG_7.md` — log de diagnóstico de surface_key mapping
- `qa/LOOP_LOG_8.md` — log del intento de loop iterativo de reducción P1
- `qa/DISCREPANCIAS_SENTINEL_VS_MOCKUP.md` — análisis previo de discrepancias
- `qa/PERFORMANCE_AUDIT.md` — auditoría de performance (menciona Sentinel)
- `qa/PLAN_CORRECCION_DISCREPANCIAS.md` — plan de correcciones (linkea a
  `DISCREPANCIAS_SENTINEL_VS_MOCKUP.md`)
- `docs/CLEANUP_AUDIT.md` — auditoría de cleanup previa

Si en una tarea futura se decide también purgar menciones textuales, estos
archivos pueden actualizarse; pero NO se borran en esta tarea porque
preservan contexto histórico de decisiones de arquitectura visual.

## Commits de esta limpieza
- `chore(qa): remove Visual Sentinel tooling and revert blind CTA change` (este)

## Aclaración
**NO es PASS visual global.** Esta tarea sólo elimina Sentinel y revierte
cambios visuales no validados. La auditoría visual autónoma será reemplazada
por Visual Auditor V2 en una tarea futura. Hasta entonces, el repo queda
con V8 (qa/capture_v8.py) como harness de capturas, mockup canónico en
`qa/mockup_reference_static/` como referencia visual, y los visual-contract
tests existentes como contrato de regresión.
