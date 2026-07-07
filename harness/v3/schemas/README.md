# harness/v3/schemas/ — JSON Schemas (futuro)

> **Fase 0A skeleton — no runtime authority.**
>
> Este directorio es un placeholder. No contiene schemas `.schema.json`
> funcionales. Los schemas se crean en Fase 0B/1A.

## Tesis

Cada artefacto V3.1 tiene un JSON Schema (Draft 2020-12) que valida su
estructura. El harness v3 (futuro) valida cada artefacto contra su schema
antes de consumirlo. Si la validación falla, BLOCK.

## Schemas futuros

| Schema | Valida |
|---|---|
| `bundle.schema.json` | Output de VisualParity CLI (`bundle.json`). `schema_version`, `eol: "lf"`, `generated_at`, `git_head`, `vp_build_sha256`, `surfaces[]` con `surface_key`, `status`, `metrics`, `findings[]`, `canonical_png_sha256`, `actual_png_sha256`, `capture_state_assertion_sha256`, `integrity/checksums.json` reference. |
| `closure_decision.schema.json` | Evidence record. `surface_key`, `decision` (BLOCK/CLOSURE_ALLOWED/HUMAN_REVIEWED_PASS/HUMAN_REVIEWED_FAIL), `bundle_sha256`, `vp_build_sha256`, `policy_sha256`, `closure_decision_sha256`, `capture_provenance_sha256`, `state_assertion_sha256`, `anti_fraud_report_sha256`, `replay_result_sha256`, `reviewer` (si HUMAN_REVIEWED), `timestamp_utc`, `reason_text` (min 50 chars si HUMAN_REVIEWED). |
| `capture_state_assertion.schema.json` | `surface_key`, `window_title`, `button_labels[]`, `timer_value` (si aplica), `state_fingerprint`, `captured_at`, `capture_v8_sha256`. |
| `review_annotation.schema.json` | Output de UI (WPF, fase futura). `surface_key`, `reviewer`, `timestamp_utc`, `reason_text` (min 50 chars), `screenshot_sha256`, `decision` (PASS/FAIL). |
| `capture_provenance.schema.json` | `run_id`, `git_head`, `mtime`, `capture_v8_sha256`, `vp_build_sha256_expected`, `invocation_args[]`. |
| `replay_result.schema.json` | `replayed_keys[]`, `expected_keys[]`, `replayed_count`, `expected_count`, `cardinality_match: bool`, `per_key_results[]`. |

## Estado actual (Fase 0A)

- **Implementado:** sólo este `README.md`.
- **No implementado:** `*.schema.json` (futuro, Fase 0B).

## Reglas de schema (futuro)

- Draft 2020-12.
- `additionalProperties: false` (rechazar campos desconocidos).
- `required` explícito para cada campo obligatorio.
- Validación en runtime (harness v3) y en CI (pre-commit hook).

## Documentación relacionada

- `docs/VisualParity_V3_1/ARCHITECTURE.md` — separación de capas.
- `docs/VisualParity_V3_1/POLICY.md` — reglas de cierre.
