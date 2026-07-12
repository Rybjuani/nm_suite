# Harness v3 Contract — VisualParity V3.1

> **Fase 2 — contract-level. No runtime authority. No visual closure.**

## Tesis

> **VisualParity mide y muestra. El harness decide.**

El harness v3 consume bundles de VisualParity, aplica la política de
cierre y decide. Es la **única** autoridad de cierre. El handoff (si
sobrevive) es view read-only.

## Módulos (Fase 2)

| Módulo | Estado Fase 2 | Responsabilidad |
|---|---|---|
| `bundle_verifier.py` | Implementado | Verifica bundle.json + integrity/checksums.json + vp_build_sha256 allowlist. |
| `policy_engine.py` | Implementado | Mapea estados VisualParity → decisiones harness. |
| `state_assertion.py` | Implementado (syntactic) | Schema + validador sintáctico de capture_state_assertion.json. |
| `capture_orchestrator.py` | Contract only | Declara contrato; NOT_IMPLEMENTED para captura real. |
| `replay/replay.py` | Contract + cardinality | Rechaza `--no-regen`; cardinality check; NOT_IMPLEMENTED para replay real. |
| `anti_fraud/scan.py` | Initial coverage | asset_byte_identity (1 vector); 6 vectores diferidos. |
| `tests/` | Implementado | 21 tests stdlib (policy, replay, bundle_verifier, duplicate_key). |

## Estados que el harness emite

`CANDIDATE_PASS`, `BLOCK`, `HUMAN_REVIEW_REQUIRED`.

`CLOSURE_ALLOWED` y `HUMAN_REVIEWED_PASS`/`HUMAN_REVIEWED_FAIL` son
decisiones de cierre que se emiten en operaciones separadas (no en
`policy_engine.evaluate` directamente).

## Mapeo estado VisualParity → acción harness

| Estado VisualParity | Acción harness v3 | Nota |
|---|---|---|
| `NO_DIFF` | `CANDIDATE_PASS` | Requiere todos los required properties para upgrade a `CLOSURE_ALLOWED`. |
| `MISSING_PAIR` | `BLOCK` | |
| `SIZE_MISMATCH` | `BLOCK` | |
| `DIFF_UNCLASSIFIED` | `BLOCK` | Pixel metrics en fase posterior. |
| `LOW_DIFF` | `HUMAN_REVIEW_REQUIRED` | Nunca auto-close. |
| `HIGH_DIFF` | `BLOCK` | No override. Path: `MEASUREMENT_DISPUTE`. |
| `SUSPICIOUS` | `BLOCK` | |
| `NEAR_THRESHOLD` | `HUMAN_REVIEW_REQUIRED` | |
| `NON_DETERMINISTIC` | `BLOCK` | |
| `MEASUREMENT_DISPUTE_CANDIDATE` | `HUMAN_REVIEW_REQUIRED` | Recalibración + regeneración. |
| `HUMAN_REVIEWED_PASS` | `CANDIDATE_PASS` | Requiere reviewer, timestamp, reason. |
| `HUMAN_REVIEWED_FAIL` | `BLOCK` | |

## Required properties para `CLOSURE_ALLOWED`

- `tests_pass`
- `anti_fraud_clean`
- `replay_full_regen_pass`
- `evidence_byte_reproducible`
- `determinism_pass`
- `state_assertion_valid`
- `canonical_png_hash_in_record`
- `vp_build_sha256_in_allowlist`

`policy_engine.evaluate` emite `CANDIDATE_PASS` y lista
`missing_required_properties`. El upgrade a `CLOSURE_ALLOWED` es una
operación separada del harness (no en `policy_engine`).

## bundle_verifier.py

Verifica:

1. `bundle.json` existe y es JSON válido.
2. `integrity/checksums.json` existe y es JSON válido.
3. `schema == "visualparity.bundle.v1"`.
4. `eol == "lf"`.
5. `vp_build_sha256` presente y en allowlist (`visualparity.lock.json`).
6. `bundle_sha256` en `checksums.json` == SHA256 real de `bundle.json`.

Exit codes: `0` VERIFY_PASS, `1` VERIFY_FAIL, `2` ERROR.

## policy_engine.py

```bash
python harness/v3/policy_engine.py --state NO_DIFF --properties '{"tests_pass": true, ...}'
```

Exit codes: `0` decision emitida, `1` estado inválido, `2` ERROR.

## state_assertion.py

Validador sintáctico de `capture_state_assertion.json`:

- `surface_key` (str, formato `suite:...@light|dark` o `hub:...@light|dark`)
- `window_title` (str, no vacío)
- `button_labels` (list)
- `state_fingerprint` (str, no vacío)
- `captured_at` (str, ISO8601 con `T`)
- `capture_v8_sha256` (str, 64 hex chars)
- `timer_value` (opcional)

Fase 2: validación sintáctica only. Validación semántica (¿el assertion
corresponde al `surface_key` declarado?) en fase posterior.

## capture_orchestrator.py

**Fase 2: contract only.** `NOT_IMPLEMENTED` para captura real.

Contrato:

- Es el **único** módulo permitido para invocar `qa/capture_v8.py`.
- VisualParity Core/CLI **nunca** invoca `capture_v8.py`.
- Agentes **nunca** invocan `capture_v8.py` directamente.
- CI **nunca** invoca `capture_v8.py`.
- `--introspect` deshabilitado hasta auditar `vas_introspect.py` (PEND-1).

```bash
python harness/v3/capture_orchestrator.py --contract-print
python harness/v3/capture_orchestrator.py --key suite:timer@light --theme light
# -> NOT_IMPLEMENTED (exit 1)
```

## replay/replay.py

**Fase 2: contract + cardinality.** `NOT_IMPLEMENTED` para replay real.

Reglas implementadas:

- `--no-regen` → `BLOCK` (forbidden for closure).
- `--all-closed` o `--keys-file` requerido (range audit solo no basta).
- `replayed_keys < --min-keys` → `BLOCK` (VQA-REPLAY-001).
- No stub-pass. Si todo pasa, emite `NOT_IMPLEMENTED` (no falso PASS).

```bash
python harness/v3/replay/replay.py --contract-print
python harness/v3/replay/replay.py --all-closed --min-keys 1
# -> NOT_IMPLEMENTED (porque Fase 2 no implementa recaptura)
python harness/v3/replay/replay.py --no-regen
# -> BLOCK
```

## anti_fraud/scan.py

**Fase 2: known-vector initial coverage. NOT 100%.**

Vectores implementados:

1. `asset_byte_identity` — scan `app/`, `hub/`, `shared/` por PNGs cuyo
   SHA256 raw bytes matchea un canonical PNG hash. **Sin EOL
   normalization en PNGs** (V2 bug fixed).

Vectores diferidos:

2. `string_tokens`
3. `pixmap_with_reference`
4. `modal_backdrop_constants`
5. `ast_scan`
6. `canonical_png_in_record`
7. `capture_v8_integrity`
8. `sidecar_provenance`

```bash
python harness/v3/anti_fraud/scan.py
python harness/v3/anti_fraud/scan.py --json report.json
```

Exit codes: `0` CLEAN, `1` DIRTY, `2` ERROR.

## Tests (Fase 2)

`harness/v3/tests/`:

| Archivo | Tests | Descripción |
|---|---|---|
| `test_policy_engine.py` | 10 | HIGH_DIFF blocks, LOW_DIFF no auto-close, NO_DIFF candidate_pass, etc. |
| `test_replay.py` | 4 | --no-regen blocked, 0 keys blocked, --all-closed required, contract-print. |
| `test_bundle_verifier.py` | 4 | verify_pass, tamper_fails, missing_checksums_fails, vp_build_sha_not_in_allowlist. |
| `test_duplicate_key.py` | 3 | No-dup passes, dup detected, multi-dup detected. |

**Total: 21 tests, todos PASS.**

Run:

```bash
python harness/v3/tests/test_policy_engine.py
python harness/v3/tests/test_replay.py
python harness/v3/tests/test_bundle_verifier.py
python harness/v3/tests/test_duplicate_key.py
```

O con pytest (si disponible):

```bash
pytest harness/v3/tests/
```

## Límites (no negociables)

- Harness v3 **no puede** invocar V1/V2 scripts.
- Harness v3 **no puede** usar `--no-regen` como cierre.
- Harness v3 **no puede** usar `reopen_legacy_all`.
- Harness v3 **no puede** aceptar bulk `HUMAN_REVIEWED_PASS`.
- Harness v3 **no puede** confiar en `signature.sha256` como firma.
- Harness v3 **no puede** mezclar commits de producto / VisualParity /
  policy / canon / closure.
- `capture_orchestrator.py` es el **único** invocador de
  `qa/capture_v8.py`.

## Próximas fases (no implementadas)

- **Fase posterior:** implementar `capture_orchestrator.py` runtime real
  (invocar `capture_v8.py` con `--introspect` deshabilitado).
- **Fase posterior:** implementar `replay/replay.py` runtime real
  (recaptura + recomparación + cardinalidad exacta).
- **Fase posterior:** anti-fraud vectores 2-8.
- **Fase posterior:** `state_assertion.py` validación semántica.
- **Fase posterior:** `ci_gate/gate.py` (orquesta todo).
- **Fase posterior:** `agent_runner/runner.py` (despacho con denylist).
- **Fase posterior:** `evidence_records/active/` (persistencia).
