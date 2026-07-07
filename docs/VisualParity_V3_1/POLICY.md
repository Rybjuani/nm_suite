# Policy V3.1 — Reglas de cierre

> **Fase 0A skeleton — no runtime authority.** Este documento declara las
> reglas de cierre V3.1. El skeleton `harness/v3/policy/closure_policy_v3.example.yaml`
> es ejemplo no funcional. Ningún gate aplica estas reglas en Fase 0A.

## Tesis

> **VisualParity mide y muestra. El harness decide.**

VisualParity emite estados de medición. El harness `v3` mapea esos estados
a acciones de cierre vía `closure_policy_v3.yaml`. La política es la
**única** autoridad de cierre. El handoff (si sobrevive) es view read-only.

## Reglas V3.1 (no negociables)

### R1 — `LOW_DIFF` no cierra

`LOW_DIFF` se mapea a `HUMAN_REVIEW_REQUIRED`. No existe path de
auto-cierre. Requiere `HUMAN_REVIEWED_PASS` individual con `reviewer`,
`timestamp_utc`, `reason_text` (mín. 50 chars), `reviewer_screenshot_sha256`.

### R2 — `HIGH_DIFF` no tiene override

`HIGH_DIFF` se mapea a `BLOCK`. No existe `--allow-high-diff-override`,
`OWNER_EXCEPTION_ACTIVE` como flag, ni `DECISIÓN-OWNER`.

Si se sospecha falso positivo, el path es `MEASUREMENT_DISPUTE`:
- VisualParity emite `MEASUREMENT_DISPUTE_CANDIDATE`.
- Harness requiere recalibración versionada del comparator.
- Regeneración del bundle con la nueva versión.
- Re-validación contra corpus.
- No es override; es re-medición.

### R3 — No bulk human pass

Un `review_annotation.json` por surface. El harness rechaza N annotations
idénticas (mismo `reviewer` + `timestamp` ± 60s + `reason_text` idéntico).

### R4 — CI sólo bloquea; no autoriza cierre

CI corre: anti-fraud V3.1 + structural pre-check + lint + schema. Exit 0
desbloquea el target set para cierre manual en self-hosted runner. Exit 1
BLOCK. CI nunca emite `CLOSURE_PASS`.

### R5 — Replay con recaptura real

Replay válido = recaptura + recomparación + cardinalidad exacta.

- `--no-regen` no existe en V3.1.
- `replayed_keys == len(closed_keys_in_target_set)`.
- `replayed_keys=0` con `expected_keys>0` = `BLOCK`.
- Range audit (`base..HEAD`) no es suficiente; `--all-closed` por defecto.

### R6 — `DECISIÓN-OWNER` prohibido; `OWNER_EXCEPTION_ACTIVE` sólo como registro firmado

`DECISIÓN-OWNER` está prohibido en docs activos. `doc_keyword_lint` bloquea
CI si aparece.

`OWNER_EXCEPTION_ACTIVE` **no es flag ni bypass**. Es un registro firmado
con `reason`, `reviewer`, `timestamp`. No abre path de cierre alternativo.
No overridea `HIGH_DIFF` ni `LOW_DIFF`.

### R7 — `signature.sha256` prohibido como firma

Cadena de custodia con 4 hashes separados:

- `bundle_sha256 = sha256(bytes del .vpbundle)`
- `vp_build_sha256 = sha256(binario VisualParity)`
- `policy_sha256 = sha256(policy canonicalizada)`
- `closure_decision_sha256 = sha256(record canonicalizado)`

Más `integrity/checksums.json` con hashes LF-normalized de cada archivo
texto del bundle; hashes raw de cada PNG.

Ed25519 sólo como fase futura si se implementa.

### R8 — No stubs que PASS

Si un módulo no está implementado, `raise NotImplementedError` y gate
`BLOCK`. Un stub que retorna `(True, "stub_pass")` es fraude (V2 pecado).

### R9 — No mixed commits

Un commit no mezcla: (a) producto (`app/`, `hub/`, `shared/`); (b)
VisualParity Core (`tools/visualparity/`); (c) policy (`harness/v3/policy/`);
(d) closure evidence (`harness/v3/evidence_records/`); (e) canon
(`qa/_mockup_canonical/`).

Test de mixed commit en pre-commit hook + CI.

### R10 — `capture_v8.py` sólo vía `capture_orchestrator.py`

`qa/capture_v8.py` es generador transitorio. Sólo
`harness/v3/capture_orchestrator.py` puede invocarlo. VisualParity Core/CLI
no puede invocarlo. Agentes no pueden invocarlo. CI no puede invocarlo.

`--introspect` deshabilitado por defecto hasta auditar `vas_introspect.py`.

### R11 — `reopen_legacy_all` no existe

Sólo `--reopen --key <key> --reason <text> --reviewer <id>`. Legacy
closures se tratan como OPEN (no requieren reopen; simplemente están
abiertos).

### R12 — Comparator thresholds son constantes

No CLI-overridable. Si necesitan cambiarse: bump de versión del
comparator + re-validación de todos los closures previos. Calibrados con
corpus, no por intuición.

### R13 — `near_threshold` como flag de medición

VisualParity emite `near_threshold: <metric>` finding. Harness requiere
`HUMAN_REVIEWED_PASS`. La lista de surfaces no se hardcodea en policy.

### R14 — Determinism check antes de cierre

Dos captures del mismo surface, sin commit de por medio. Si
`changed_ratio >= 0.005` entre los dos captures, refuse closure
(`NON_DETERMINISTIC`).

### R15 — State verification en capture time

`capture_state_assertion` (window title, button labels, timer value,
state fingerprint) generado por harness al capturar. Validado antes de
aceptar capture. VisualParity no lo genera ni valida.

### R16 — Family enforcement real en gate

Gate recibe `--target-set`. Antes de `ALLOW_CLOSURE` para un key, verifica
que todos los otros keys del target set están `ALLOW_CLOSURE` o ya
`CLOSED`. Si uno está `BLOCK`, refuse. No hay `--allow-family-partial-close`;
el owner debe cambiar el target set explícitamente.

### R17 — UI sólo produce `review_annotation.json`

UI (WPF, fase futura) sólo produce `review_annotation.json` por surface.
El harness emite `HUMAN_REVIEWED_PASS/FAIL` leyendo la annotation +
verificando `reviewer`, `timestamp`, `reason_text_min_50_chars`,
screenshot. WinUI fuera de V3.1.

### R18 — Anti-fraud: cobertura inicial de vectores conocidos

8 vectores (ver `THREAT_MODEL.md`). No cobertura total. Denylist real pero
no única defensa. Vectores nuevos requieren adición versionada +
re-validación de corpus.

## Mapeo estado → acción (resumen)

| Estado VisualParity | Acción harness |
|---|---|
| `NO_DIFF` | `CLOSURE_ALLOWED` (si todos los required properties pass) |
| `LOW_DIFF` | `HUMAN_REVIEW_REQUIRED` |
| `SUSPICIOUS` | `BLOCK` |
| `HIGH_DIFF` | `BLOCK` (path: `MEASUREMENT_DISPUTE`) |
| `MISSING_PAIR` | `BLOCK` |
| `SIZE_MISMATCH` | `BLOCK` |
| `NEAR_THRESHOLD` | `HUMAN_REVIEW_REQUIRED` |
| `NON_DETERMINISTIC` | `BLOCK` |
| `MEASUREMENT_DISPUTE_CANDIDATE` | `HUMAN_REVIEW_REQUIRED` (recalibración + regeneración) |
| `HUMAN_REVIEWED_PASS` (harness) | `CLOSURE_ALLOWED` |
| `HUMAN_REVIEWED_FAIL` (harness) | `BLOCK` |

## Required properties para `CLOSURE_ALLOWED`

- `tests_pass` (referencia CI artifact URL + run_id)
- `anti_fraud_clean` (8 vectores CLEAN)
- `replay_full_regen_pass` (recaptura + recomparación + cardinalidad exacta)
- `evidence_byte_reproducible` (`bundle_sha256` reproduce on re-read)
- `determinism_pass` (dos actuals, `changed_ratio < 0.005`)
- `state_assertion_valid` (`capture_state_assertion` matches `surface_key`)
- `canonical_png_hash_in_record` (record incluye `canonical_png_sha256`)
- `vp_build_sha256_in_allowlist` (vs `visualparity.lock.json`)

## Skeletons no funcionales

- `harness/v3/policy/closure_policy_v3.example.yaml` — ejemplo de policy
  declarativa. No runtime authority.
- `harness/v3/policy/measurement_config_v3.example.yaml` — ejemplo de
  parámetros de medición separados de la policy. No runtime authority.

Estos skeletons **no reemplazan** la policy V1/V2, **no son leídos** por
ningún gate, y **no cierran keys**.
