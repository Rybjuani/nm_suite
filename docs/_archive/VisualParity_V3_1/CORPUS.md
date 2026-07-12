# Corpus mínimo V3.1

> **Fase 0A skeleton — no runtime authority.** Este documento declara el
> corpus mínimo de pruebas para calibrar VisualParity Core/CLI. El corpus
> físico se crea en Fase 0B/1A bajo `tools/visualparity/tests/corpus/`.

## Tesis

El comparator V3.1 se calibra con corpus, no por intuición. Cada fixture
del corpus tiene un `expected.json` con el estado que VisualParity debe
emitir. Si VisualParity emite otro estado, el test falla.

## Corpus mínimo (15 fixtures)

| # | Fixture | Entrada | Estado esperado | Hipótesis VQA-RT-001 |
|---|---|---|---|---|
| 01 | `no_diff_real` | `canon.png` + `actual.png` idénticos | `NO_DIFF` | — |
| 02 | `low_diff_aa_shadow` | `canon.png` + `actual.png` con diferencia AA/sombra | `LOW_DIFF` | — |
| 03 | `false_pass_known` | `canon.png` + `actual.png` con mutación visible < threshold V1 | `HIGH_DIFF` (V3.1 recalibrado) | C.2 |
| 04 | `high_diff_obvious` | `canon.png` + `actual.png` con mutación obvia | `HIGH_DIFF` | — |
| 05 | `wrong_state_timer` | `canon_timer_running.png` + `actual_timer_paused.png` | `HIGH_DIFF` + `state_ambiguity` finding | C.1 |
| 06 | `visible_mutation_suite_home` | `canon.png` + `actual.png` con mutación `suite:home` | `HIGH_DIFF` | C.2 |
| 07 | `duplicate_key` | handoff con duplicate | `duplicate_surface_key` BLOCK (parser invariant) | B.5 |
| 08 | `stale_report` | `bundle.json` con `generated_at` < latest commit | `stale_bundle` BLOCK | E.1 |
| 09 | `crlf_lf_fixture` | evidence record con hash CRLF vs LF | `eol_mismatch` BLOCK | A.1 |
| 10 | `nondeterminism_actividades_respiracion` | `actual1.png` + `actual2.png` con diferencia > 0.005 | `NON_DETERMINISTIC` | A.2 |
| 11 | `near_threshold` | `canon.png` + `actual.png` con `changed_pixel_ratio` = 0.099 vs threshold 0.10 | `NEAR_THRESHOLD` | C.3 |
| 12 | `canonical_smuggling_blocked` | product code con `QPixmap("qa/_mockup_canonical/foo.png")` | anti_fraud `DIRTY` | E.3 |
| 13 | `inactive_source` | bundle con `canonical_source != default` | `REPORT_EVIDENCE_VALID:NO` | E.3 |
| 14 | `rutina_add_task_dark_material_divergence` | `canon.png` + `actual.png` | `HIGH_DIFF` | C.4 |
| 15 | `measurement_dispute_candidate` | `canon.png` + `actual.png` (HIGH_DIFF pero plausible falso positivo) | `MEASUREMENT_DISPUTE_CANDIDATE` | — |

## Estructura de cada fixture

```
tools/visualparity/tests/corpus/<NN>_<name>/
├── canon.png              # o canon_<state>.png si aplica
├── actual.png             # o actual1.png + actual2.png si es determinism
├── meta.json              # descripción, hipótesis VQA-RT-001 referenciada
├── expected.json          # estado esperado de VisualParity
└── (opcional) handoff.md  # si el fixture es de parser (duplicate_key)
```

### `expected.json` schema (ejemplo)

```json
{
  "fixture": "05_wrong_state_timer",
  "expected_state": "HIGH_DIFF",
  "expected_findings": ["state_ambiguity"],
  "expected_metrics_range": {
    "changed_pixel_ratio": {"min": 0.0, "max": 1.0},
    "mean_abs_diff": {"min": 0.0, "max": 1.0}
  },
  "notes": "canon_timer_running.png vs actual_timer_paused.png. VQA-STATE-001."
}
```

## Calibración de thresholds

Los thresholds del comparator V3.1 se calibran con este corpus:

- `min_ssim`, `max_changed_pixel_ratio`, `text_dense_max_changed_pixel_ratio`, `max_mean_abs_diff` se ajustan hasta que todos los fixtures produzcan su `expected_state`.
- `near_threshold` margin (5%) se valida con fixture 11.
- `determinism` threshold (0.005) se valida con fixture 10.

Los thresholds son **constantes del comparator** (no CLI-overridable).
Cambios requieren bump de versión + re-validación de todos los fixtures.

## Estado actual (Fase 0A)

- **Implementado:** sólo este documento.
- **No implementado:** fixtures físicos, `tools/visualparity/tests/corpus/`
  no existe, tests de corpus inventory no implementados.

## Próximas fases

- **Fase 0B:** crear `tools/visualparity/tests/corpus/` con los 15 fixtures.
  Tests de corpus inventory (`test_corpus_inventory.py`) validan que cada
  directorio tenga `canon.png` + `actual.png` + `expected.json`.
- **Fase 1A:** calibrar thresholds del comparator contra el corpus.
  Tests de bundle determinism (`test_bundle_determinism.py`).
