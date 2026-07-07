# tools/visualparity/phase0b/ — Fase 0B Governance Validators

> **Fase 0B — no runtime authority.**
>
> Este directorio contiene validadores standalone de gobernanza para
> comprobar que el scaffold V3.1 creado en Fase 0A no se degrade. Los
> validadores **no cierran keys**, **no invocan V1/V2**, **no invocan
> `capture_v8.py`**, **no usan pytest**, y **no tienen autoridad de
> runtime**.

## Qué valida

`validate_phase0b.py` verifica 13 grupos de invariantes del scaffold V3.1:

| Grupo | Validación |
|---|---|
| A | Existencia de los 17 archivos Fase 0A (10 docs + 7 skeletons). |
| B | Cada skeleton declara `Fase 0A skeleton` y `no runtime authority`. |
| C | Declaraciones no-go en docs canónicos (no repo `Rybjuani/visualparity`, V3.1 en `nm_suite`, `.NET 8` primero, `WPF` después, `WinUI` fuera, `LOW_DIFF` no cierra, `HIGH_DIFF` no override, UI sólo `review_annotation.json`, bulk `HUMAN_REVIEWED_PASS` prohibido, CI sólo bloquea, replay con recaptura, `--no-regen` prohibido, no `signature.sha256`, anti-fraud = cobertura inicial de vectores conocidos). |
| D | Separación de estados: VisualParity sólo emite los 9 estados permitidos; los 5 estados de cierre están marcados como prohibidos para VisualParity. |
| E | `closure_policy_v3.example.yaml`: `LOW_DIFF → HUMAN_REVIEW_REQUIRED`, `HIGH_DIFF → BLOCK`, no `LOW_DIFF: ALLOW_CLOSURE`, no override de `HIGH_DIFF`, bulk human pass prohibido, `--no-regen` sólo como prohibición, skeleton authority markers. |
| F | `measurement_config_v3.example.yaml`: contiene `near_threshold`, `determinism`, `bbox`/`diff` thresholds; NO contiene reglas de cierre (`ALLOW_CLOSURE` / `action: BLOCK`). |
| G | `denylist.example.yaml`: prohíbe invocar V1 closers/comparators/replay, V2 legacy, `--no-regen`, bulk human pass, editar evidence records, editar canon. |
| H | `MIGRATION_A_PLUS.md`: tag `forensic-pre-v3.1`, git bundle externo/release asset, SHA256, MANIFEST puntero, no V1/V2 ejecutable en `main`, `docs/_archive/` sólo documentación no ejecutable. |
| I | `CAPTURE_V8_TRANSITION.md`: sólo `capture_orchestrator.py` invoca `capture_v8.py`, VisualParity no lo invoca, `--introspect` deshabilitado hasta auditar `vas_introspect.py`. |
| J | `CANON_RECONCILIATION_PLAN.md`: no eliminar `pack canonico/` en 0A/0B, reconciliar contra `_mockup_canonical/`, canon único con paths relativos, comparar sha256 raw bytes, migrar assets únicos antes de eliminar. |
| K | `PHASE_0A_DECISIONS.md`: contiene las 11 owner decisions requeridas. |
| L | No runtime leakage: el validador es el único `.py` en `phase0b/`, no hay `.cs` bajo `tools/visualparity/`, no hay workflows nuevos, el validador no importa pytest/pytestqt/PyQt ni importa/ejecuta/invoca V1/V2. Las referencias textuales a nombres V1/V2 son esperadas porque se usan para validar prohibiciones y denylist. |
| M | Fase 0D docs y scripts: existencia de `OWNER_DECISIONS_LOCKED.md`, `FORENSIC_SNAPSHOT_PREFLIGHT.md`, `MIGRATION_A_PLUS_EXECUTION_PLAN.md`, `PHASE_0D_CHECKLIST.md`, `preflight_snapshot_dry_run.ps1`, `phase0d/README.md`. Valida que `OWNER_DECISIONS_LOCKED.md` contiene LOCK-1 a LOCK-5 y secciones `LOCKED_FOR_V3_1` / `STILL_OWNER_DECISION_REQUIRED`. Valida que preflight y plan marcan comandos `FUTURE_PHASE_ONLY`. Valida que el plan tiene los 8 pasos. |

## Cómo correr

```bash
python tools/visualparity/phase0b/validate_phase0b.py
```

### Requisitos

- Python 3.9+ (usa `from __future__ import annotations`, type hints `str | None`).
- **Sólo stdlib.** No requiere pytest, pytestqt, PyQt6, .NET, Node, Playwright, ni GitHub Actions.
- Se ejecuta desde cualquier directorio; localiza el repo root automáticamente (3 niveles arriba del script).

### Salida

```
========================================================================
Fase 0B — Governance Validators
========================================================================
  PASS  A. Existence of Fase 0A files  (0 errors)
  PASS  B. Skeleton authority ...  (0 errors)
  ...
  PASS  L. No runtime leakage ...  (0 errors)
  PASS  M. Fase 0D docs and scripts existence  (0 errors)
------------------------------------------------------------------------
Groups: 13/13 passed, 0 failed, 0 total errors
========================================================================
```

### Exit codes

- `0` — PASS: todos los grupos pasaron.
- `1` — FAIL: al menos un grupo falló (errores listados).
- `2` — ERROR: error interno (repo root no encontrado, archivo canónico ausente).

## Restricciones

- **No usa pytest.** El repo raíz tiene `tests/conftest.py` que fuerza `pytestqt`, lo que rompe la colección en entornos sin PyQt6. Este validador es standalone y no depende de pytest.
- **No tiene runtime authority.** No cierra keys, no abre keys, no invoca V1/V2, no invoca `capture_v8.py`, no modifica policy/canon/evidence.
- **No reemplaza CI.** Es una herramienta de validación local; no está wired a ningún workflow.
- **No es un test unitario de producto.** No toca `app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/`.

## Cuándo correr

- Después de cualquier commit que toque `docs/VisualParity_V3_1/`, `tools/visualparity/`, o `harness/v3/`.
- Antes de avanzar a Fase 1A, como smoke test de que el scaffold sigue íntegro.
- En review de PRs que pretendan modificar el scaffold V3.1.

## Limitaciones

- El validador verifica **presencia de texto** y **estructura de archivos**, no semántica profunda. Un doc que mencione `LOW_DIFF` pero lo mapee incorrectamente en prosa no será detectado si el texto literal está presente.
- El grupo L (no runtime leakage) verifica estáticamente que el validador no importa, ejecuta ni invoca V1/V2; las referencias textuales a nombres V1/V2 son esperadas porque se usan para validar prohibiciones y denylist. El grupo L no verifica el árbol git completo. La verificación de git se hace por separado (el operador debe correr `git status --short` por separado).
- El validador no verifica que los `.example.yaml` sean YAML válidos parseables; verifica substrings. Si se requiere parseo YAML real, agregar en Fase posterior (sin introducir dependencia de `pyyaml` si no está en stdlib — usar `tomllib` o un parser minimalista propio).

## Estado

- **Implementado:** `validate_phase0b.py` + este `README.md` + `run_phase0b.ps1` (runner PowerShell nativo para Windows) + workflow CI `.github/workflows/visual-parity-v3-governance.yml` (governance smoke).
- **No implementado:** parseo YAML estricto, validación de JSON Schemas (Fase 1B+ cuando los schemas existan).

## Runner PowerShell para Windows

`run_phase0b.ps1` es un runner nativo de Windows PowerShell (no Git Bash, no WSL) que localiza el repo root, busca Python en este orden (`.\.venv\Scripts\python.exe` → `python` → `py -3`), ejecuta el validador y propaga el exit code.

```powershell
.\tools\visualparity\phase0b\run_phase0b.ps1
```

No invoca V1/V2. No invoca `capture_v8.py`. No toca archivos. No tiene runtime authority.
