# Changelog VisualParity V3.1

> **Fase 4 — operational docs. No runtime authority. No visual closure.**
> Este changelog registra cambios de V3.1 (documentación + skeletons +
> validadores + CI smoke + migration planning + Core/CLI + harness v3 +
> operational docs). No registra cambios de V1/V2.

## Convención

Formato: `Keep a Changelog`. Versionado: `MAJOR.MINOR.PATCH` donde MAJOR
es la fase (0, 1, 2, ...), MINOR es sub-fase, PATCH es corrección.

## [1.0.0] — 2026-07-07 — Fase 1-4 (Core/CLI + harness v3 + CI + docs)

### Fase 1 — feat(visual-parity-v3.1): add core cli scaffold (`d6351182`)

- `tools/visualparity/VisualParity.sln` (.NET 8 solution).
- `src/VisualParity.Core/`: Bundle (SurfaceStatus, BundleWriter),
  Comparators (PixelDiff byte-equality), Pairing (Pairer).
- `src/VisualParity.CLI/`: Program.cs (compare, batch, verify-bundle;
  manual arg parser, no external NuGet).
- `tests/VisualParity.Core.Tests/`: PixelDiffTests.cs (7 xUnit tests).
- `visualparity.lock.json`: real lockfile (placeholder vp_build_sha256).
- Estados: NO_DIFF, MISSING_PAIR, SIZE_MISMATCH, DIFF_UNCLASSIFIED.
- dotnet build/test: NOT_EXECUTABLE localmente; CI usa setup-dotnet.

### Fase 2 — feat(visual-parity-v3.1): add harness v3 scaffold (`ebd9b49b`)

- `harness/v3/bundle_verifier.py`: verifica bundle + checksums + allowlist.
- `harness/v3/policy_engine.py`: mapea estados → decisiones.
- `harness/v3/state_assertion.py`: schema + validador sintáctico.
- `harness/v3/capture_orchestrator.py`: contract only (NOT_IMPLEMENTED).
- `harness/v3/replay/replay.py`: contract + cardinality + --no-regen rejection.
- `harness/v3/anti_fraud/scan.py`: asset_byte_identity (1 vector, known-vector
  initial coverage).
- `harness/v3/tests/`: 4 test suites, 21 tests stdlib (all PASS).
- HIGH_DIFF → BLOCK (no override). LOW_DIFF → HUMAN_REVIEW_REQUIRED (no
  auto-close). --no-regen → BLOCK. replayed_keys=0 con expected>0 → BLOCK.

### Fase 3 — ci(visual-parity-v3.1): expand governance checks (`e3e2030a`)

- Workflow `visual-parity-v3-governance.yml` expandido:
  - Job `governance-smoke` (hard gate): Fase 0B validator (13 grupos) +
    ASCII check (2 archivos) + 4 harness v3 test suites (21 tests).
  - Job `dotnet-tests` (soft gate, continue-on-error): setup-dotnet 8.0.x
    + build + test.
- Validador Fase 0B actualizado:
  - Grupo B: acepta cualquier marker de fase + "no runtime authority"
    (case-insensitive).
  - Grupo L: permite .cs bajo src/ y tests/; prohibe en phase0b/, phase0d/.
- Workflow legacy `visual-closure-replay.yml` NO tocado.

### Fase 4 — docs(visual-parity-v3.1): document phase 1 to 5 contracts (this commit)

- `CORE_CLI_CONTRACT.md` (nuevo): contrato VisualParity Core/CLI.
- `HARNESS_V3_CONTRACT.md` (nuevo): contrato harness v3.
- `PHASE_1_TO_5_STATUS.md` (nuevo): status por fase.
- `CI_GOVERNANCE.md` (actualizado): jobs governance-smoke + dotnet-tests.
- `ARCHITECTURE.md` (actualizado): estado Fase 4.
- `CHANGELOG.md` (este archivo).

### Not Modified (confirmado)

- V1/V2 no removidos (preservados vía A+ snapshot tag `forensic-pre-v3.1`).
- Producto, canon, evidence records, handoff: sin cambios.
- Workflow legacy `visual-closure-replay.yml`: sin cambios.
- `VISUAL_REPAIR_HANDOFF.md`: sin cambios.

### Riesgos residuales

- V1/V2 siguen en path activo y wired al CI legacy. Riesgo activo hasta
  remoción (prompt explícito posterior, Fase 5+).
- 6 owner decisions pendientes (PEND-1 a PEND-6) bloquean fases
  posteriores específicas.
- VisualParity CLI binary no construido; `vp_build_sha256` es placeholder.
- Pixel metrics no implementadas; cualquier diff es `DIFF_UNCLASSIFIED`.
- `capture_orchestrator.py` y `replay/replay.py` son contract-only
  (NOT_IMPLEMENTED para runtime real).

## [0.5.0] — 2026-07-07 — Fase 0E (A+ forensic snapshot executed)

- Tag `forensic-pre-v3.1` creado apuntando a `2e36fb90`.
- Bundle externo `nm_suite-forensic-pre-v3.1.bundle` creado.
- SHA256: `1eee4987106c767ac154b222f5761ed4c44f34921fb31cc554a14f702cf129ee`.
- GitHub Release `forensic-pre-v3.1` publicado.
- Pointer commit `98df54b4`.

## [0.4.1] — 2026-07-07 — Fase 0D patch (PowerShell ASCII-safe)

### Fixed

- `tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1` —
  reemplazados caracteres non-ASCII (em dash `—` U+2014, box drawing `─`
  U+2500) por hyphen ASCII `-`. El script fallaba en Windows PowerShell
  5.1 con `ParserError: Token ')' inesperado` porque 5.1 interpreta mal
  UTF-8 sin BOM. Sin cambios lógicos: sigue siendo dry-run, no crea
  tag/bundle/SHA/release, no escribe archivos, no hace push, exit 0 si
  clean + HEAD == origin/main, exit 1 si divergencia.
- `tools/visualparity/phase0b/run_phase0b.ps1` — mismo reemplazo de
  caracteres non-ASCII por ASCII. Sin cambios lógicos.

### Added

- `tools/visualparity/phase0d/check_ascii.py` — script Python stdlib que
  verifica que ambos `.ps1` sean ASCII-only. Exit 0 si PASS, exit 1 si
  FAIL. No runtime authority. No invoca V1/V2. No invoca capture_v8.

### Not Modified (confirmado)

- Lógica de los scripts PowerShell: sin cambios.
- Producto, canon, evidence, V1/V2, handoff, workflows: sin cambios.
- No tag real, no bundle real, no release real.

### Commit

- `fix(visual-parity-v3.1): make PowerShell dry-run ASCII-safe` (HEAD
  sobre `71f9ba34`).

### Riesgos residuales

- El fix no fue probado en Windows PowerShell 5.1 real en este entorno
  (Linux sandbox). El ASCII check stdlib confirma 0 non-ASCII chars, lo
  que elimina la causa raíz del ParserError reportado. Se recomienda
  re-ejecutar `preflight_snapshot_dry_run.ps1` en Windows 5.1 para
  confirmar el fix end-to-end.
- El archivo sigue siendo UTF-8 sin BOM. Windows PowerShell 5.1 maneja
  ASCII-only UTF-8 sin BOM correctamente; si en el futuro se agregan
  caracteres non-ASCII, se requerirá BOM o re-aplicar ASCII-safe.

## [0.4.0] — 2026-07-07 — Fase 0D

### Added

- `docs/VisualParity_V3_1/OWNER_DECISIONS_LOCKED.md` — 5 decisiones owner
  cerradas como `LOCKED_FOR_V3_1` (LOCK-1 bundle ubicación, LOCK-2
  capture_v8, LOCK-3 stack .NET 8, LOCK-4 timing por fases, LOCK-5 canon
  único). 6 decisiones pendientes como `STILL_OWNER_DECISION_REQUIRED`
  (PEND-1 vas_introspect, PEND-2 handoff, PEND-3 tessdata, PEND-4
  self-hosted runner, PEND-5 WORKER_VISUAL_QA_FLOW, PEND-6 116 closures).
  5 decisiones como `NOT_DECIDED_IN_THIS_PHASE`.
- `docs/VisualParity_V3_1/FORENSIC_SNAPSHOT_PREFLIGHT.md` — preflight A+
  detallado. Comandos futuros (Paso F1 a F5) marcados `FUTURE_PHASE_ONLY`.
  Prohibiciones explícitas: no tag/bundle/release en Fase 0D, no Git
  Bash/WSL, no commit de `.bundle`/`.zip`/`.tar.gz`/evidence V1/scripts
  V1/V2 a `main`.
- `docs/VisualParity_V3_1/MIGRATION_A_PLUS_EXECUTION_PLAN.md` — plan de
  ejecución de 8 pasos (snapshot → manifest pointer → archive docs →
  remove V1/V2 → preserve capture_v8 → reconcile canon → replace workflow
  → implement Core/CLI). Cada paso con objetivo, files allowed, files
  forbidden, validation, rollback strategy. Comandos destructivos marcados
  `FUTURE_PHASE_ONLY`.
- `docs/VisualParity_V3_1/PHASE_0D_CHECKLIST.md` — checklist de aceptación
  Fase 0D: docs creados, no tag/bundle/release reales, no V1/V2 removidos,
  no producto/canon/evidence/handoff/workflow legacy modificados,
  validador Fase 0B PASS, runners PowerShell PASS o NOT_EXECUTABLE.
- `tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1` — script
  dry-run PowerShell nativo. Valida clean tree + HEAD == origin/main + no
  tag `forensic-pre-v3.1` existe. Imprime comandos futuros marcados
  `FUTURE_PHASE_ONLY`. No crea tag/bundle/SHA256/release. No escribe
  archivos. No hace push. No modifica repo. Exit 0 si PASS, exit 1 si
  fail.
- `tools/visualparity/phase0d/README.md` — documentación del dry-run.

### Changed

- `docs/VisualParity_V3_1/PHASE_0A_DECISIONS.md` — 5 decisiones (#1, #2,
  #7, #9, #11) marcadas como `✅ RESUELTO en Fase 0D` con referencia a
  `OWNER_DECISIONS_LOCKED.md`. Header actualizado con resumen de estado.
- `docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` — header actualizado a
  `Fase 0D`. Referencia `FORENSIC_SNAPSHOT_PREFLIGHT.md`,
  `MIGRATION_A_PLUS_EXECUTION_PLAN.md`, `OWNER_DECISIONS_LOCKED.md`,
  `PHASE_0D_CHECKLIST.md`, y el dry-run script. Aclara que Fase 0D no
  ejecuta tag/bundle.
- `tools/visualparity/phase0b/validate_phase0b.py` — grupo M agregado para
  validar existencia de docs Fase 0D (OWNER_DECISIONS_LOCKED,
  FORENSIC_SNAPSHOT_PREFLIGHT, MIGRATION_A_PLUS_EXECUTION_PLAN,
  PHASE_0D_CHECKLIST) y del dry-run script.
- `tools/visualparity/phase0b/README.md` — actualizado para reflejar
  grupo M.

### Not Modified (confirmado)

- Producto: `app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/` —
  sin cambios.
- Canon: `qa/_mockup_canonical/`, `qa/pack canonico/` — sin cambios.
- Evidence records: `docs/closure_evidence/` — sin cambios.
- V1: `qa/` scripts — sin cambios.
- V2: `harness/` (raíz) — sin cambios.
- V3-previo: `docs/VisualParity_V3/` — sin cambios.
- Workflow legacy: `.github/workflows/visual-closure-replay.yml` — sin
  cambios.
- Workflow governance: `.github/workflows/visual-parity-v3-governance.yml`
  — sin cambios.
- Handoff: `VISUAL_REPAIR_HANDOFF.md` — sin cambios.
- Tests: `tests/` — sin cambios.
- No tag real creado.
- No bundle real creado.
- No GitHub Release creado.

### Commit

- `docs(visual-parity-v3.1): lock phase 0D migration decisions` (HEAD
  sobre `8ef984f5`).

### Riesgos residuales

- Fase 0D no ejecuta migración A+; sólo prepara. Riesgo activo de V1/V2
  en path sigue hasta fase posterior con prompt explícito.
- 6 decisiones owner pendientes (PEND-1 a PEND-6) bloquean Fases
  posteriores específicas.
- Dry-run PowerShell no ejecutado en este entorno (Linux sin pwsh);
  marcado `NOT_EXECUTABLE`. Debe probarse en Windows real.
- Plan de ejecución A+ (8 pasos) es documento; cualquier desviación en
  fase futura requiere actualización de este changelog y del plan.

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

## [0.5.0] - 2026-07-07 - Fase 0E - A+ forensic snapshot executed

### Added

- Tag forensic-pre-v3.1 creado apuntando a 2e36fb90c952f8503e50d8480879de82358ecb1f.
- Bundle externo nm_suite-forensic-pre-v3.1.bundle creado en C:\Users\nosom\Desktop\forensic_release_nm_suite.
- SHA256 calculado y verificado: 1eee4987106c767ac154b222f5761ed4c44f34921fb31cc554a14f702cf129ee.
- GitHub Release forensic-pre-v3.1 publicado con bundle + sha256 como assets.
- Puntero registrado en MIGRATION_A_PLUS.md.

### Not Modified

- V1/V2 no removidos.
- Producto, canon, evidence, handoff, workflows: sin cambios.
- No bundle/sha256 commiteados al working tree.

### Commit

- docs(visual-parity-v3.1): register forensic snapshot A+
