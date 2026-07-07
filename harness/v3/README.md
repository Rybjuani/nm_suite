# harness/v3/ — VisualParity Consumer Harness v3

> **Fase 0A skeleton — no runtime authority.**
>
> Este directorio es un placeholder. No contiene código productivo. El
> harness v3 funcional se implementa en Fase 1B+. Ningún archivo aquí es
> leído por CI, ni por agentes, ni aplica policy en Fase 0A. **No
> reemplaza** el harness V2 en `harness/` (raíz); V2 sigue intacto y wired
> al CI hasta la migración A+.

## Tesis

> **VisualParity mide y muestra. El harness decide.**

El harness v3 consume bundles de VisualParity, aplica la política de
cierre y decide. Es la **única** autoridad de cierre. El handoff (si
sobrevive) es view read-only.

## Módulos (futuro)

| Módulo | Responsabilidad |
|---|---|
| `capture_orchestrator.py` | ÚNICO invocador de `qa/capture_v8.py`. Genera `capture_provenance.json`. |
| `state_assertion.py` | Genera + valida `capture_state_assertion.json`. |
| `bundle_verifier.py` | Verifica `vp_build_sha256` vs allowlist. Calcula `bundle_sha256`. |
| `policy_engine.py` | Lee `closure_policy_v3.yaml`. Evalúa reglas. |
| `anti_fraud/` | 8 vectores (cobertura inicial de vectores conocidos). |
| `replay/replay.py` | Recaptura + recomparación + cardinalidad exacta. No `--no-regen`. |
| `ci_gate/gate.py` | Sólo bloquea; no autoriza cierre. |
| `agent_runner/runner.py` | Denylist real + per-key dispatch. No bulk. |
| `semantic_lint/` | Handoff text lint (si handoff sobrevive). |
| `evidence_records/active/` | Un `closure_decision.json` por surface cerrada. |
| `evidence_records/revoked/` | Records movidos al reabrir. |
| `policy/closure_policy_v3.yaml` | Sólo política, sin datos de medición. |
| `policy/measurement_config_v3.yaml` | Parámetros de medición (thresholds, near_threshold margin). |
| `schemas/` | JSON Schemas. |

## Límites (no negociables)

- Harness v3 **no puede** invocar V1/V2 scripts.
- Harness v3 **no puede** usar `--no-regen` como cierre.
- Harness v3 **no puede** usar `reopen_legacy_all`.
- Harness v3 **no puede** aceptar bulk `HUMAN_REVIEWED_PASS`.
- Harness v3 **no puede** confiar en `signature.sha256` como firma.
- Harness v3 **no puede** mezclar commits de producto / VisualParity /
  policy / canon / closure.
- `capture_orchestrator.py` es el **único** invocador de
  `qa/capture_v8.py`. No pasa `--introspect` por defecto.

## Estados que el harness emite

`BLOCK`, `HUMAN_REVIEW_REQUIRED`, `CANDIDATE_ONLY`, `CLOSURE_ALLOWED`,
`HUMAN_REVIEWED_PASS`, `HUMAN_REVIEWED_FAIL`.

## Estados que el harness NO emite (los emite VisualParity)

`NO_DIFF`, `LOW_DIFF`, `SUSPICIOUS`, `HIGH_DIFF`, `MISSING_PAIR`,
`SIZE_MISMATCH`, `NEAR_THRESHOLD`, `NON_DETERMINISTIC`,
`MEASUREMENT_DISPUTE_CANDIDATE`.

## Skeletons no funcionales (Fase 0A)

| Archivo | Tipo |
|---|---|
| `README.md` | Este archivo. |
| `policy/closure_policy_v3.example.yaml` | Ejemplo de policy. No runtime authority. |
| `policy/measurement_config_v3.example.yaml` | Ejemplo de config de medición. No runtime authority. |
| `schemas/README.md` | Lista de schemas futuros. |
| `agent_runner/denylist.example.yaml` | Ejemplo de denylist. No runtime authority. |

## Estado actual (Fase 0A)

- **Implementado:** sólo skeletons no funcionales.
- **No implementado:** `capture_orchestrator.py`, `state_assertion.py`,
  `bundle_verifier.py`, `policy_engine.py`, `anti_fraud/`, `replay/`,
  `ci_gate/`, `agent_runner/runner.py`, `semantic_lint/`,
  `evidence_records/`, `policy/closure_policy_v3.yaml` (real),
  `policy/measurement_config_v3.yaml` (real), `schemas/*.schema.json`.

## Documentación relacionada

- `docs/VisualParity_V3_1/README.md` — tesis, alcance, rutas, no-go.
- `docs/VisualParity_V3_1/ARCHITECTURE.md` — separación de capas.
- `docs/VisualParity_V3_1/POLICY.md` — reglas de cierre.
- `docs/VisualParity_V3_1/THREAT_MODEL.md` — matriz de amenazas.
- `docs/VisualParity_V3_1/CAPTURE_V8_TRANSITION.md` — límites de
  `capture_v8.py`.
