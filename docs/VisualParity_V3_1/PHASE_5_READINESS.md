# Fase 5 Readiness Manifest — VisualParity V3.1

> **Fase 5 — readiness only. NOT destructive. No runtime authority. No visual closure.**
>
> Este documento lista exactamente qué falta para la remoción real de V1/V2.
> **Fase 5 no ejecuta remoción.** Fase 5 = readiness manifest. La remoción
> requiere prompt explícito posterior del owner.

## Tesis

Fase 1-4 implementaron el scaffold V3.1 (Core/CLI + harness v3 contract +
CI + docs). Fase 5 = readiness: declarar qué falta, qué se eliminaría, y
qué blockers owner impiden avanzar. **No se borra nada en Fase 5.**

## Qué falta para remoción real de V1/V2

### Bloqueantes (owner decisions pendientes)

| # | Decisión | Bloquea | Estado |
|---|---|---|---|
| PEND-1 | `vas_introspect.py` auditoría profunda | Habilitación de `--introspect` en `capture_orchestrator.py` | Pendiente |
| PEND-2 | Handoff eliminar vs view read-only | Diseño de `evidence_records/` y flujo de cierre | Pendiente |
| PEND-3 | `qa/tessdata/` conservar vs eliminar | Dependencia de OCR en `state_assertion.py` | Pendiente |
| PEND-4 | Self-hosted runner | Flujo de cierre post-CI en Fase 6+ | Pendiente |
| PEND-5 | `WORKER_VISUAL_QA_FLOW.md` reescribir vs archivar | Protocolo operativo para agentes | Pendiente |
| PEND-6 | 116 closures V1: reabrir vs `INVALIDATED_PRE_V3.1` | Estado de closures post-migración | Pendiente |

Ver `OWNER_DECISIONS_LOCKED.md` para detalle.

### Bloqueantes (implementación pendiente)

| Item | Bloquea | Fase |
|---|---|---|
| Construir binario VisualParity CLI | Reemplazar placeholder `vp_build_sha256` en `visualparity.lock.json` | Fase posterior |
| Pixel metrics en VisualParity.Core | Habilitar `LOW_DIFF`/`HIGH_DIFF`/`SUSPICIOUS`/`NEAR_THRESHOLD`/`NON_DETERMINISTIC`/`MEASUREMENT_DISPUTE_CANDIDATE` | Fase posterior |
| `capture_orchestrator.py` runtime real | Captura real de surfaces | Fase posterior (tras PEND-1) |
| `replay/replay.py` runtime real | Replay con recaptura + recomparación | Fase posterior |
| Anti-fraud vectores 2-8 | Cobertura anti-fraud completa | Fase posterior |
| `state_assertion.py` validación semántica | Verificar assertion vs surface_key declarado | Fase posterior |
| `ci_gate/gate.py` | Orquestación final (anti-fraud + replay + policy + lint) | Fase posterior |
| `agent_runner/runner.py` runtime | Despacho con denylist real | Fase posterior |
| `evidence_records/active/` | Persistencia de closures V3.1 | Fase posterior |

### No bloqueantes (mejoras)

- WPF UI (sólo `review_annotation.json`) — fase futura.
- Ed25519 signatures — fase futura.
- `DeterminismCheck` en Core — fase posterior.

## Archivos que se eliminarían en futura fase de remoción

**Sólo tras prompt explícito del owner.** Preservados vía A+ snapshot tag
`forensic-pre-v3.1` + bundle externo + GitHub Release.

### V1 scripts (`qa/`)

- `qa/close_visual_key.py` (1124 LOC)
- `qa/layered_visual_compare.py` (1463 LOC)
- `qa/replay_visual_closure.py` (677 LOC)
- `qa/target_scope.py` (271 LOC)
- `qa/anti_fraud_scan.py` (809 LOC)
- `qa/vas_gate.py` (289 LOC)
- `qa/vas_engine.py` (436 LOC)
- `qa/odiff_runner.py`
- `qa/spec_generator.py`
- `qa/visual_gate_calibration.py`
- `qa/visual_auditor_spec.py`
- `qa/runtime_live_probe.py`
- `qa/run_visual.ps1`
- `qa/specs/` (directorio)

### V2 harness (`harness/` raíz, NO `harness/v3/`)

- `harness/ci_gate/gate.py`
- `harness/replay/replay.py`
- `harness/anti_fraud/scan.py`
- `harness/agent_runner/runner.py`
- `harness/agent_runner/target_scope_v2.py`
- `harness/semantic_lint/handoff_text_lint.py`
- `harness/semantic_lint/doc_keyword_lint.py`
- `harness/policy/closure_policy.yaml`
- `harness/docs/FORENSIC_FINDINGS_V2.md`
- `harness/README.md`

### V3-previo docs (`docs/VisualParity_V3/`)

- Mover sólo `.md`/`.pdf`/`.png` a `docs/_archive/VisualParity_V3_PRE_FORENSIC/`.
- **No** mover código ni evidence.

### Evidence records V1 (`docs/closure_evidence/`)

- 116 records activos (`*.json`)
- 2 revoked (`revoked/*.json`)
- **No** se mueven a `docs/_archive/` (redline: `docs/_archive/` sólo
  documentación no ejecutable). Preservación sólo vía bundle A+.

### Workflow legacy

- `.github/workflows/visual-closure-replay.yml` — reemplazado por
  workflow V3.1 de cierre (fase posterior, no el governance smoke actual).

### Handoff (sujeto a PEND-2)

- `VISUAL_REPAIR_HANDOFF.md` — si PEND-2 = eliminar.

### Protocolo (sujeto a PEND-5)

- `WORKER_VISUAL_QA_FLOW.md` — si PEND-5 = archivar.

## Archivos que se CONSERVAN

- `qa/capture_v8.py` (generador transitorio, LOCK-2).
- `qa/_mockup_canonical/` (canon único, LOCK-5).
- `qa/pack canonico/` (hasta reconciliación, LOCK-5).
- `qa/tessdata/` (sujeto a PEND-3; congelado).
- `tests/` no-V1 (tests de producto).
- Producto: `app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/`.
- `docs/VisualParity_V3_1/` (docs V3.1 nuevos).
- `tools/visualparity/` (scaffold V3.1).
- `harness/v3/` (scaffold V3.1).
- `.github/workflows/visual-parity-v3-governance.yml` (governance smoke).

## Orden de remoción (futura fase, FUTURE_PHASE_ONLY)

Ver `MIGRATION_A_PLUS_EXECUTION_PLAN.md` para detalle de 8 pasos. Resumen:

1. Snapshot/tag/bundle/checksum — ✅ HECHO (Fase 0E).
2. Manifest pointer — ✅ HECHO (commit `98df54b4`).
3. Archive docs no ejecutables — FUTURE.
4. Remove V1/V2 operative code — FUTURE.
5. Preserve `capture_v8.py` — FUTURE (verificación).
6. Reconcile canon — FUTURE.
7. Replace workflow legacy — FUTURE.
8. Implement VisualParity Core/CLI runtime — FUTURE (Fase 6+).

**No se ejecuta ningún paso destructivo en Fase 5.**

## Confirmación de no-destructivo

- ✅ No se borró V1/V2.
- ✅ No se movió V1/V2.
- ✅ No se modificó `qa/` (salvo lectura para auditoría).
- ✅ No se modificó canon (`qa/_mockup_canonical/`, `qa/pack canonico/`).
- ✅ No se modificó producto.
- ✅ No se modificó evidence records.
- ✅ No se modificó handoff.
- ✅ No se modificó workflow legacy.
- ✅ No se cerraron keys.
- ✅ No se reabrieron keys.
- ✅ No se usó `--force`.
- ✅ No se commitearon bundle/sha256/zip/tar/screenshots/captures/evidence nuevos.

## Próximo paso requerido

**Prompt explícito del owner** citando este documento y
`MIGRATION_A_PLUS_EXECUTION_PLAN.md` para:

1. Resolver PEND-1 a PEND-6.
2. Confirmar que el bundle A+ (`forensic-pre-v3.1` release) es
   descargable y verificable.
3. Autorizar ejecución del Paso 3 en adelante (archive + remove + reconcile
   + replace workflow).

Sin prompt explícito, V1/V2 permanecen en `main` y el riesgo activo
(V1/V2 wired al CI legacy) persiste.

## Referencias

- `OWNER_DECISIONS_LOCKED.md` — decisiones LOCKED + PEND.
- `MIGRATION_A_PLUS_EXECUTION_PLAN.md` — plan 8 pasos.
- `FORENSIC_SNAPSHOT_PREFLIGHT.md` — preflight A+.
- `PHASE_1_TO_5_STATUS.md` — status por fase.
- `CORE_CLI_CONTRACT.md` — contrato Core/CLI.
- `HARNESS_V3_CONTRACT.md` — contrato harness v3.
