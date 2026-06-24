# LOOP_LOG_5.md — Reducción de MISSING_REFERENCE en Sentinel audit-mockup

## SHA inicial
785dbccdc0db62254f76f77572f85e8f6cfeace1

## Estado inicial (2026-06-24)
- V8_CAPTURES_LATEST: 86
- MATCHED: 86
- MISSING_CAPTURE: 0
- MISSING_REFERENCE: 26 (P0)
- REGRESSIONS: 69 (P1)
- NEW_UNREVIEWED: 26
- P0: 27, P1: 69, P2: 0, P3: 4

## Diagnóstico inicial
El run de `capture_v8.py --all` se colgó en `hub:detalle` (timeout 120s) y rotó las capturas previas a `_scratch_trash/`. Se restauraron 86 capturas desde el trash a `qa/_captures_v8/iter1/`.

Root cause de MISSING_REFERENCE: 13 aliases faltantes en `_STATE_VIEW_ALIASES` de `visual_sentinel.py`. Los view_ids de V8 no siguen la convención `{screen_id}-{state_id}` para ciertos estados, causando que:
1. Los mockup items caigan en fallback `screen_id` solo (matched con captura incorrecta).
2. Las capturas específicas queden como MISSING_REFERENCE.
3. Los phash distances sean altos (REGRESSION) porque se comparan mockup vs captura incorrecta.

Aliases necesarios:
- `("rutina", "add")` → `rutina-add-task`
- `("rutina", "done")` → `rutina-all-completed`
- `("actividades", "marked")` → `actividades-marked-hice`
- `("avisos", "active")` → `avisos-filter-activos`
- `("registro", "s1")` → `registro-step1-emotion`
- `("registro", "s1otro")` → `registro-step1-emotion-otro`
- `("registro", "s2")` → `registro-step2-distortions`
- `("registro", "s3")` → `registro-step3-filled`
- `("registro", "ok")` → `registro-success`
- `("detalle", "hub-tab-timer")` → `detalle-plan-timer`
- `("detalle", "hub-tab-rutina")` → `detalle-plan-rutina`
- `("detalle", "hub-tab-activacion")` → `detalle-plan-activacion`
- `("detalle", "modal-resumen-ia")` → `detalle-resumen-ia-0`

## Iteraciones

### Iteración 1 — 13 aliases V8→mockup

- **SHA antes:** 785dbccdc0db62254f76f77572f85e8f6cfeace1
- **SHA después:** a81eec6 (fix) + f925722 (gitignore cleanup)
- **Blocker original:** MISSING_REFERENCE=26 (P0) — capturas V8 sin referencia mockup
- **Clasificación:** D) bug real del registry Sentinel — `_candidate_views` no mapeaba view_ids de V8 que no siguen `{screen_id}-{state_id}`
- **Cambio aplicado:**
  - Agregados 13 aliases en `_STATE_VIEW_ALIASES`:
    - rutina:add → rutina-add-task
    - rutina:done → rutina-all-completed
    - actividades:marked → actividades-marked-hice
    - avisos:active → avisos-filter-activos
    - registro:s1 → registro-step1-emotion
    - registro:s1otro → registro-step1-emotion-otro
    - registro:s2 → registro-step2-distortions
    - registro:s3 → registro-step3-filled
    - registro:ok → registro-success
    - detalle:hub-tab-timer → detalle-plan-timer
    - detalle:hub-tab-rutina → detalle-plan-rutina
    - detalle:hub-tab-activacion → detalle-plan-activacion
    - detalle:modal-resumen-ia → detalle-resumen-ia-0
  - Movidos `_SCREEN_TO_VIEW` y `_STATE_VIEW_ALIASES` a nivel de módulo para testabilidad.
  - Agregado test `test_build_mockup_registry_maps_all_v8_aliases`.
  - Agregados `qa/_inspect/` y `qa/_mockup_targets/` a `.gitignore`.
- **Validación:**
  - ruff: PASS
  - pytest tests/test_visual_sentinel.py: 61 passed
  - sentinel audit-mockup: MISSING_REFERENCE 26→0, P0 27→0, REGRESSIONS 69→68
- **Nuevo conteo:** MISSING_REFERENCE=0 / P0=0 / P1=68 / P3=4

## Estado final
- SHA inicial: 785dbccdc0db62254f76f77572f85e8f6cfeace1
- SHA final: f925722
- Commits: a81eec6, f925722
- MISSING_REFERENCE inicial: 26
- MISSING_REFERENCE final: 0
- Casos corregidos: 13 aliases (26 instancias light+dark)
- Casos clasificados como no-fix: N/A (todos fueron fixables)

## Confirmación
**NO es PASS visual global.** Quedan 68 REGRESSIONS (P1) por diferencias visuales entre mockup HTML y capturas Qt offscreen. El registry está completo (MISSING_REFERENCE=0, MISSING_CAPTURE=0, REGISTRY_COMPLETE=YES) pero las divergencias visuales requieren iteración separada del loop de fidelidad visual.

