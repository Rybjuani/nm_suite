# Changelog VisualParity V3.1

> **Fase 0C — governance smoke. No runtime authority. No visual closure.**
> Este changelog registra cambios de V3.1 (documentación + skeletons +
> validadores + CI smoke). No registra cambios de V1/V2.

## Convención

Formato: `Keep a Changelog`. Versionado: `MAJOR.MINOR.PATCH` donde MAJOR
es la fase (0, 1, 2, ...), MINOR es sub-fase, PATCH es corrección.

## [0.3.0] — 2026-07-07 — Fase 0C

### Added

- `tools/visualparity/phase0b/run_phase0b.ps1` — runner PowerShell nativo
  para Windows. Localiza repo root, busca Python (`.venv\Scripts\python.exe`
  → `python` → `py -3`), ejecuta `validate_phase0b.py`, propaga exit code.
  No invoca V1/V2. No invoca `capture_v8.py`. No toca archivos.
- `.github/workflows/visual-parity-v3-governance.yml` — workflow CI nuevo
  `VisualParity V3.1 Governance Smoke`. Trigger `pull_request` + `push` sobre
  `docs/VisualParity_V3_1/**`, `tools/visualparity/**`, `harness/v3/**`, y el
  propio workflow. Runner `ubuntu-latest`, Python 3.12. Ejecuta
  `python tools/visualparity/phase0b/validate_phase0b.py`. Governance smoke
  only. No runtime authority. No visual closure. No pytest. No PyQt6. No
  V1/V2. No `capture_v8.py`. No reemplaza el workflow legacy.
- `docs/VisualParity_V3_1/CI_GOVERNANCE.md` — documentación del workflow
  nuevo: qué corre, qué NO corre, qué protege, relación con workflow legacy.

### Changed

- `tools/visualparity/phase0b/README.md` — corregida frase imprecisa sobre
  referencias V1/V2 en el validador. Texto nuevo: "el validador no importa,
  ejecuta ni invoca V1/V2; las referencias textuales a nombres V1/V2 son
  esperadas porque se usan para validar prohibiciones y denylist." Sección
  "Estado" actualizada para reflejar Fase 0C (runner PowerShell + CI smoke).

### Not Modified (confirmado)

- Producto: `app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/` —
  sin cambios.
- Canon: `qa/_mockup_canonical/`, `qa/pack canonico/` — sin cambios.
- Evidence records: `docs/closure_evidence/` — sin cambios.
- V1: `qa/` scripts — sin cambios.
- V2: `harness/` (raíz) — sin cambios.
- V3-previo: `docs/VisualParity_V3/` — sin cambios.
- Workflow legacy: `.github/workflows/visual-closure-replay.yml` — sin
  cambios, no reemplazado, no editado.
- Handoff: `VISUAL_REPAIR_HANDOFF.md` — sin cambios.
- `tools/visualparity/phase0b/validate_phase0b.py` — sin cambios (Fase 0B
  intacta).
- Fase 0A docs (`docs/VisualParity_V3_1/*.md` salvo CHANGELOG y
  CI_GOVERNANCE nuevo) — sin cambios.

### Commit

- `ci(visual-parity-v3.1): add governance smoke workflow` (HEAD sobre
  `41e3a8c6`).

### Riesgos residuales

- El workflow nuevo corre sólo en `ubuntu-latest`. No valida captura en
  Windows (será workflow separado en Fase posterior si se requiere).
- El workflow no verifica el árbol git completo (no-toque de producto/canon/
  evidence). Esa verificación se hace manualmente vía `git status --short`
  en review de PR.
- El workflow legacy sigue wired a V1 scripts y ejecutando `--no-regen`.
  Riesgo activo hasta migración A+ (owner decision #1 y #9).
- El runner PowerShell no fue ejecutado en este entorno (Linux sin pwsh);
  marcado `NOT_EXECUTABLE`. Debe probarse en Windows real en primera
  oportunidad.

## [0.2.0] — 2026-07-07 — Fase 0B

### Added

- `tools/visualparity/phase0b/validate_phase0b.py` — validador standalone
  stdlib con 12 grupos (A-L) de invariantes del scaffold V3.1.
- `tools/visualparity/phase0b/README.md` — documentación del validador.

### Changed

- `harness/v3/policy/closure_policy_v3.example.yaml` — agregada sección
  `bulk_human_pass_policy` (requerida por validador grupo E).

### Commit

- `test(visual-parity-v3.1): add phase 0B governance validators` (`41e3a8c6`).

## [0.1.0] — 2026-07-07 — Fase 0A

### Added

- `docs/VisualParity_V3_1/` (directorio nuevo).
- `docs/VisualParity_V3_1/README.md` — tesis, alcance V3.1, rutas
  oficiales, no-go absolutos (14 items).
- `docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` — plan de archivo forense
  A+ pre-V3.1: tag `forensic-pre-v3.1` + git bundle externo + SHA256 +
  MANIFEST puntero. Prohibición de archivar V1/V2 ejecutable en `main`.
- `docs/VisualParity_V3_1/ARCHITECTURE.md` — separación de capas
  (medición / política / aplicación / persistencia), módulos VisualParity
  Core/CLI y harness v3, estados permitidos/prohibidos, flujo end-to-end.
- `docs/VisualParity_V3_1/THREAT_MODEL.md` — matriz VQA-RT-001 con 34
  amenazas (T1-T34), estados de control `VERIFIED_IN_REPO`,
  `OWNER_VALIDATED_NOT_REPRODUCED`, `DOCUMENTED_IN_V2_BUT_NOT_ENFORCED`,
  `NOT_VERIFIED`, `PENDING_IMPLEMENTATION`. Controles V3.1 requeridos por
  amenaza. Cobertura anti-fraud: 8 vectores como cobertura inicial de
  vectores conocidos (no cobertura total).
- `docs/VisualParity_V3_1/POLICY.md` — 18 reglas de cierre V3.1
  (R1-R18): `LOW_DIFF` no cierra, `HIGH_DIFF` no override, no bulk human
  pass, CI sólo bloquea, replay con recaptura real, `DECISIÓN-OWNER`
  prohibido, `OWNER_EXCEPTION_ACTIVE` sólo como registro firmado,
  `signature.sha256` prohibido, no stubs que PASS, no mixed commits,
  `capture_v8.py` sólo vía `capture_orchestrator.py`, `--introspect`
  deshabilitado, `reopen_legacy_all` no existe, thresholds constantes,
  `near_threshold` como flag de medición, determinism check, state
  verification en capture time, family enforcement real, UI sólo produce
  `review_annotation.json`, anti-fraud cobertura inicial de vectores
  conocidos.
- `docs/VisualParity_V3_1/CORPUS.md` — corpus mínimo 15 fixtures
  (NO_DIFF real, LOW_DIFF AA/sombra, false PASS conocidos, HIGH_DIFF
  obvio, wrong-state timer, visible mutation suite:home, duplicate key,
  stale report, CRLF/LF, nondeterminism actividades/respiración,
  near-threshold, canonical smuggling blocked, inactive source,
  rutina-add-task@dark material divergence, measurement dispute
  candidate).
- `docs/VisualParity_V3_1/PHASE_0A_DECISIONS.md` — 11 owner decisions
  pendientes con recomendación clara (bundle forense ubicación,
  `capture_v8.py` conservado, `vas_introspect.py` auditoría, handoff
  eliminar, `tessdata/` conservar, self-hosted runner, stack VisualParity,
  `WORKER_VISUAL_QA_FLOW.md` reescribir, timing migración, 116 closures V1,
  canon reconciliación).
- `docs/VisualParity_V3_1/CANON_RECONCILIATION_PLAN.md` — plan 8 pasos
  para reconciliar `qa/pack canonico/` vs `qa/_mockup_canonical/`.
  No elimina nada en Fase 0A.
- `docs/VisualParity_V3_1/CAPTURE_V8_TRANSITION.md` — límites de
  `capture_v8.py` como generador transitorio (L1 sólo
  `capture_orchestrator.py` lo invoca, L2 VisualParity no lo invoca, L3
  `--introspect` deshabilitado hasta auditar `vas_introspect.py`).
  Dependency audit resumido.
- `docs/VisualParity_V3_1/CHANGELOG.md` — este archivo.
- `tools/visualparity/README.md` — skeleton no funcional. Declara "Fase
  0A skeleton — no runtime authority".
- `tools/visualparity/visualparity.lock.example.json` — skeleton no
  funcional del lockfile (`vp_build_sha256` allowlist).
- `harness/v3/README.md` — skeleton no funcional. Declara "Fase 0A
  skeleton — no runtime authority".
- `harness/v3/policy/closure_policy_v3.example.yaml` — skeleton no
  funcional de policy declarativa. Sólo política, sin datos de medición.
- `harness/v3/policy/measurement_config_v3.example.yaml` — skeleton no
  funcional de parámetros de medición separados de la policy.
- `harness/v3/schemas/README.md` — skeleton no funcional. Lista schemas
  futuros (bundle, closure_decision, capture_state_assertion,
  review_annotation, capture_provenance, replay_result).
- `harness/v3/agent_runner/denylist.example.yaml` — skeleton no funcional
  de denylist.

### Not Modified (confirmado)

- Producto: `app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/` —
  sin cambios.
- Canon: `qa/_mockup_canonical/`, `qa/pack canonico/` — sin cambios.
- Evidence records: `docs/closure_evidence/` (116 records + 2 revoked) —
  sin cambios.
- V1: `qa/` scripts (close_visual_key, layered_visual_compare,
  replay_visual_closure, target_scope, anti_fraud_scan, vas_gate,
  vas_engine, vas_introspect, capture_v8, odiff_runner, spec_generator,
  visual_gate_calibration, visual_auditor_spec, runtime_live_probe,
  run_visual.ps1) — sin cambios.
- V2: `harness/` (ci_gate, replay, anti_fraud, agent_runner,
  semantic_lint, policy, docs) — sin cambios.
- V3-previo: `docs/VisualParity_V3/` — sin cambios (se tratará como
  forense en Fase posterior).
- CI: `.github/workflows/visual-closure-replay.yml` — sin cambios.
- Handoff: `VISUAL_REPAIR_HANDOFF.md` — sin cambios.
- Protocolo: `WORKER_VISUAL_QA_FLOW.md` — sin cambios.

### Commit

- `docs(visual-parity-v3.1): add phase 0A governance scaffold` (HEAD
  sobre `c645405e`). No push.

### Riesgos residuales

- V1/V2 siguen en path activo y wired al CI. Riesgo activo hasta
  migración A+ (owner decision #9).
- `--introspect` sigue habilitado en `capture_v8.py` binario; el límite
  se aplica a nivel de `capture_orchestrator.py` (futuro).
- `MANIFEST.json` canónico sigue con paths Windows hardcoded; la
  re-canonicalización es Fase posterior.
- 6 duplicate keys en handoff actual persisten; se resuelven al
  eliminar handoff como autoridad (owner decision #4) o al reescribirlo.

### Owner decisions pendientes

11 decisiones en `PHASE_0A_DECISIONS.md`. Bloqueantes para Fase 1A: #2
(`capture_v8.py` conservado), #7 (stack VisualParity). Bloqueante para
migración A+: #1 (bundle forense ubicación). Riesgo activo si se
posterga: #9 (timing migración).
