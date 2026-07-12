# CI Governance — VisualParity V3.1 Governance Smoke

> **Fase 3 — Governance smoke + tests. No runtime authority. No visual closure.**

## Tesis

El workflow `.github/workflows/visual-parity-v3-governance.yml` es un **smoke
test de gobernanza** que protege el scaffold V3.1 (docs + skeletons + Core/CLI
+ harness v3) contra degradación. No es CI de cierre visual. No autoriza
cierre. No reemplaza el workflow legacy.

## Qué corre el workflow (Fase 3)

- **Trigger:** `pull_request` y `push` sobre los paths:
  - `docs/VisualParity_V3_1/**`
  - `tools/visualparity/**`
  - `harness/v3/**`
  - `.github/workflows/visual-parity-v3-governance.yml`
- **Runner:** `ubuntu-latest`.

### Job `governance-smoke` (hard gate)

1. `checkout` (fetch-depth 1).
2. `setup-python` 3.12.
3. `python tools/visualparity/phase0b/validate_phase0b.py` (13 grupos).
4. `python tools/visualparity/phase0d/check_ascii.py` (2 archivos .ps1).
5. `python harness/v3/tests/test_policy_engine.py` (10 tests).
6. `python harness/v3/tests/test_replay.py` (4 tests).
7. `python harness/v3/tests/test_bundle_verifier.py` (4 tests).
8. `python harness/v3/tests/test_duplicate_key.py` (3 tests).

Si cualquiera falla, el PR/push es rechazado.

### Job `dotnet-tests` (soft gate, `continue-on-error: true`)

1. `checkout` (fetch-depth 1).
2. `setup-dotnet` 8.0.x.
3. `dotnet build VisualParity.sln --configuration Release`.
4. `dotnet test VisualParity.sln --configuration Release --no-build`.

Marcado `continue-on-error: true` para que el job `governance-smoke` siga
siendo el hard gate. Si `dotnet-tests` falla, el PR no se bloquea pero se
genera una advertencia visible.

## Qué NO corre el workflow nuevo

- ❌ No corre pytest.
- ❌ No corre PyQt6.
- ❌ No corre .NET.
- ❌ No corre Node.
- ❌ No corre Playwright.
- ❌ No corre V1/V2 scripts (`close_visual_key.py`, `layered_visual_compare.py`,
  `replay_visual_closure.py`, `target_scope.py`, `anti_fraud_scan.py`,
  `vas_gate.py`, ni `harness/*` legacy).
- ❌ No corre `qa/capture_v8.py`.
- ❌ No corre `--no-regen`.
- ❌ No autoriza cierre visual.
- ❌ No emite `CLOSURE_PASS` ni `HUMAN_REVIEWED_PASS/FAIL`.
- ❌ No reemplaza ni edita el workflow legacy
  `.github/workflows/visual-closure-replay.yml`.

## Qué protege

El validador Fase 0B (`tools/visualparity/phase0b/validate_phase0b.py`)
verifica 12 grupos de invariantes:

| Grupo | Invariante |
|---|---|
| A | Existencia de los 17 archivos Fase 0A (10 docs + 7 skeletons). |
| B | Cada skeleton declara `Fase 0A skeleton` y `no runtime authority`. |
| C | Declaraciones no-go en docs canónicos (16 invariants). |
| D | Separación de estados VisualParity (9 permitidos, 5 prohibidos). |
| E | `closure_policy_v3.example.yaml`: reglas de cierre correctas. |
| F | `measurement_config_v3.example.yaml`: parámetros separados de policy. |
| G | `denylist.example.yaml`: prohibiciones V1/V2/--no-regen/bulk/evidence/canon. |
| H | `MIGRATION_A_PLUS.md`: tag, bundle, SHA256, MANIFEST, no V1/V2 en main. |
| I | `CAPTURE_V8_TRANSITION.md`: límites de capture_v8. |
| J | `CANON_RECONCILIATION_PLAN.md`: plan de reconciliación canónica. |
| K | `PHASE_0A_DECISIONS.md`: 11 owner decisions. |
| L | No runtime leakage (sólo `validate_phase0b.py` en `phase0b/`, sin `.cs`,
     sin workflows nuevos, sin imports prohibidos). |

Detalle completo en `tools/visualparity/phase0b/README.md`.

## Workflow legacy (sin cambios)

`.github/workflows/visual-closure-replay.yml` sigue existiendo y ejecutando
`anti_fraud_scan.py --mode all` + `replay_visual_closure.py --no-regen` sobre
Ubuntu. **No se modifica, no se reemplaza, no se elimina en Fase 0C.**

El workflow legacy será reemplazado en la migración A+ (Fase posterior, sujeta
a owner decision #1 y #9 en `PHASE_0A_DECISIONS.md`). Hasta entonces, ambos
workflows coexisten:

- `visual-closure-replay.yml` (legacy): CI de cierre visual V1. Sigue wired a
  V1 scripts. No tocado.
- `visual-parity-v3-governance.yml` (nuevo): smoke de gobernanza V3.1. No
  autoriza cierre. Protege scaffold V3.1.

## Cómo correr localmente

### Linux / macOS

```bash
python tools/visualparity/phase0b/validate_phase0b.py
```

### Windows (PowerShell nativo)

```powershell
.\tools\visualparity\phase0b\run_phase0b.ps1
```

El runner PowerShell localiza el repo root, busca Python (`.venv\Scripts\
python.exe` → `python` → `py -3`), ejecuta el validador y propaga el exit
code. No invoca V1/V2. No invoca `capture_v8.py`. No toca archivos.

## Limitaciones

- El workflow corre sólo en `ubuntu-latest`. No corre en Windows ni macOS
  porque el validador es stdlib-only y no requiere PyQt6. Si en el futuro se
  requiere validar captura en Windows, será un workflow separado (Fase
  posterior).
- El workflow no verifica el árbol git completo (no-toque de producto/canon/
  evidence). Esa verificación se hace manualmente vía `git status --short` en
  review de PR.
- El workflow no reemplaza la revisión humana de PRs. Es un smoke test; la
  revisión de fondo sigue siendo necesaria.

## Estado

- **Implementado (Fase 0C):** workflow
  `.github/workflows/visual-parity-v3-governance.yml` + runner PowerShell
  `tools/visualparity/phase0b/run_phase0b.ps1` + este documento.
- **No implementado:** workflow de cierre visual V3.1 (Fase 1B+), workflow de
  self-hosted runner con toolchain completa (Fase posterior, sujeto a owner
  decision #6).

## Documentación relacionada

- `tools/visualparity/phase0b/README.md` — detalle del validador.
- `docs/VisualParity_V3_1/README.md` — tesis, alcance, no-go absolutos.
- `docs/VisualParity_V3_1/PHASE_0A_DECISIONS.md` — owner decisions pendientes.
- `docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` — plan de migración forense.
