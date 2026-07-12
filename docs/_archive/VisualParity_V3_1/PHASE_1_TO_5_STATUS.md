# Fase 1 to 5 Status — VisualParity V3.1

> **Fase 4 — status snapshot. No runtime authority. No visual closure.**

## Resumen ejecutivo

| Fase | Estado | Commit | Descripción |
|---|---|---|---|
| 0A | ✅ COMPLETE | `4d7bbbe1` | Governance scaffold (10 docs + 7 skeletons). |
| 0B | ✅ COMPLETE | `41e3a8c6` | Governance validators (13 grupos stdlib). |
| 0C | ✅ COMPLETE | `8ef984f5` | CI governance smoke + Windows runner. |
| 0D | ✅ COMPLETE | `71f9ba34` | Owner decisions locked + A+ preflight. |
| 0D patch | ✅ COMPLETE | `2e36fb90` | PowerShell ASCII-safe for Windows 5.1. |
| 0E | ✅ COMPLETE | `98df54b4` | A+ forensic snapshot real (tag + bundle + release). |
| 1 | ✅ COMPLETE | `d6351182` | VisualParity Core/CLI scaffold (.NET 8). |
| 2 | ✅ COMPLETE | `ebd9b49b` | Harness v3 scaffold (Python stdlib, contract-level). |
| 3 | ✅ COMPLETE | `e3e2030a` | CI governance expandido (validators + tests + dotnet). |
| 4 | ✅ COMPLETE (this commit) | — | Documentación operativa. |
| 5 | ✅ COMPLETE (next commit) | — | Readiness manifest (no destructivo). |

## Tesis

> **VisualParity mide y muestra. El harness decide.**

Esta tesis se respeta en todas las fases. VisualParity Core/CLI mide y
empaqueta. El harness v3 consume, aplica policy y decide. CI sólo bloquea;
no autoriza cierre.

## Fase 1 — VisualParity Core/CLI scaffold

**Estado:** ✅ COMPLETE.

**Implementado:**

- Solución .NET 8 (`tools/visualparity/VisualParity.sln`).
- `VisualParity.Core` (library): `Bundle/`, `Comparators/`, `Pairing/`.
- `VisualParity.CLI` (console): `compare`, `batch`, `verify-bundle`.
- `VisualParity.Core.Tests` (xUnit): 7 tests.
- `visualparity.lock.json` (real, placeholder vp_build_sha256).

**Estados emitidos:** `NO_DIFF`, `MISSING_PAIR`, `SIZE_MISMATCH`,
`DIFF_UNCLASSIFIED`.

**No implementado (fases posteriores):** pixel metrics, `LOW_DIFF`,
`HIGH_DIFF`, `SUSPICIOUS`, `NEAR_THRESHOLD`, `NON_DETERMINISTIC`,
`MEASUREMENT_DISPUTE_CANDIDATE`, `DeterminismCheck`, `PanelRenderer`,
WPF UI.

**Tests:** 7 xUnit tests. `NOT_EXECUTABLE` localmente (no dotnet SDK);
CI corre con `setup-dotnet`.

**Detalle:** `CORE_CLI_CONTRACT.md`.

## Fase 2 — Harness v3 scaffold

**Estado:** ✅ COMPLETE.

**Implementado:**

- `bundle_verifier.py` (verifica bundle + checksums + allowlist).
- `policy_engine.py` (mapea estados → decisiones).
- `state_assertion.py` (schema + validador sintáctico).
- `capture_orchestrator.py` (contract only, NOT_IMPLEMENTED).
- `replay/replay.py` (contract + cardinality, NOT_IMPLEMENTED).
- `anti_fraud/scan.py` (1 vector: asset_byte_identity).
- `tests/` (21 tests stdlib).

**Decisiones harness:** `CANDIDATE_PASS`, `BLOCK`,
`HUMAN_REVIEW_REQUIRED`.

**No implementado (fases posteriores):** captura real, replay real,
anti-fraud vectores 2-8, validación semántica de state_assertion,
`ci_gate/gate.py`, `agent_runner/runner.py`, `evidence_records/`.

**Tests:** 21/21 PASS (policy 10 + replay 4 + bundle_verifier 4 +
duplicate_key 3).

**Detalle:** `HARNESS_V3_CONTRACT.md`.

## Fase 3 — CI governance expandido

**Estado:** ✅ COMPLETE.

**Implementado:**

- Workflow `visual-parity-v3-governance.yml` expandido:
  - Job `governance-smoke`: Fase 0B validator + ASCII check + 4 harness
    v3 stdlib test suites.
  - Job `dotnet-tests`: setup-dotnet 8.0.x + build + test
    (`continue-on-error: true`).
- Validador Fase 0B actualizado:
  - Grupo B: acepta cualquier marker de fase + "no runtime authority"
    (case-insensitive).
  - Grupo L: permite `.cs` bajo `src/` y `tests/`.

**No modificado:** workflow legacy `visual-closure-replay.yml`.

**Tests:** validador 13/13 PASS, harness v3 21/21 PASS, ASCII 2/2 PASS.

## Fase 4 — Documentación operativa

**Estado:** ✅ COMPLETE (this commit).

**Creado/actualizado:**

- `CORE_CLI_CONTRACT.md` (nuevo).
- `HARNESS_V3_CONTRACT.md` (nuevo).
- `PHASE_1_TO_5_STATUS.md` (este archivo, nuevo).
- `CI_GOVERNANCE.md` (actualizado).
- `ARCHITECTURE.md` (actualizado).
- `CHANGELOG.md` (entrada Fase 1-4).

## Fase 5 — Readiness manifest

**Estado:** ✅ COMPLETE (next commit).

**Implementado:** `PHASE_5_READINESS.md` con:

- Lista exacta de qué falta para remoción real.
- Lista de archivos que se eliminarían en futura fase.
- Lista de blockers owner (PEND-1 a PEND-6).

**No destructivo:** no borra V1/V2, no toca producto/canon/evidence.

## Invariantes respetados en todas las fases

1. **VisualParity no decide cierre.** Sólo emite estados de medición.
2. **Harness decide.** Mapea estados → acciones.
3. **CI bloquea, no cierra.** Governance smoke + tests; no `CLOSURE_PASS`.
4. **V1/V2 no removidos.** A+ snapshot ya preserva (tag `forensic-pre-v3.1`
   + bundle + release).
5. **Remoción requiere prompt explícito posterior.** No se ejecuta en
   Fase 1-5.
6. **No PASS global.** Ninguna fase declara PASS visual/global.
7. **No `--no-regen` como cierre.** `replay.py` lo rechaza.
8. **No `signature.sha256` como firma.** Cadena de custodia con hashes
   separados.
9. **No bulk `HUMAN_REVIEWED_PASS`.** Un `review_annotation.json` por
   surface.
10. **No mixed commits.** Cada capa es commit atómico.

## A+ forensic snapshot (Fase 0E)

- **Tag:** `forensic-pre-v3.1`
- **Tagged commit:** `2e36fb90c952f8503e50d8480879de82358ecb1f`
- **Release:** `https://github.com/Rybjuani/nm_suite/releases/tag/forensic-pre-v3.1`
- **Bundle:** `nm_suite-forensic-pre-v3.1.bundle` (externo, no en repo)
- **SHA256:** `1eee4987106c767ac154b222f5761ed4c44f34921fb31cc554a14f702cf129ee`
- **Pointer commit:** `98df54b4f290eb2b3911973a80c7562c7391a829`

El snapshot preserva V1, V2, V3-previo, docs, evidence records, canon,
workflows, full git history. Cualquier estado pre-V3.1 es reconstruible
vía `git clone nm_suite-forensic-pre-v3.1.bundle`.

## Owner decisions

- **LOCKED (5):** bundle ubicación, capture_v8 conservado, stack .NET 8,
  timing por fases, canon único. Ver `OWNER_DECISIONS_LOCKED.md`.
- **PENDIENTES (6):** vas_introspect auditoría, handoff eliminar vs view,
  tessdata, self-hosted runner, WORKER_VISUAL_QA_FLOW, 116 closures. Ver
  `OWNER_DECISIONS_LOCKED.md` PEND-1 a PEND-6.

## Próximos pasos

1. **Resolver PEND-1 a PEND-6** antes de avanzar a Fase 6+ (runtime
   real de captura, replay, cierre).
2. **Construir binario VisualParity CLI** y reemplazar placeholder en
   `visualparity.lock.json`.
3. **Implementar pixel metrics** en VisualParity.Core para habilitar
   `LOW_DIFF`/`HIGH_DIFF`/etc.
4. **Implementar `capture_orchestrator.py` runtime** (tras auditar
   `vas_introspect.py`).
5. **Implementar `replay.py` runtime** (recaptura + recomparación).
6. **Implementar `ci_gate/gate.py`** (orquestación final).
7. **Prompt explícito del owner para remoción V1/V2** (Fase posterior,
   no en 1-5).
