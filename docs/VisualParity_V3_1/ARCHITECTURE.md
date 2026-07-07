# Arquitectura V3.1

> **Fase 0A skeleton — no runtime authority.** Este documento describe la
> arquitectura objetivo. Ningún módulo está implementado en Fase 0A.

## Tesis

> **VisualParity mide y muestra. El harness decide.**

La separación entre medición y política es absoluta. VisualParity produce
métricas crudas y estados de medición. El harness `v3` consume esos bundles,
aplica la política de cierre y decide. Cualquier mezcla reproduce los
defectos de V1 (closer que mide + decide + escribe evidence + muta handoff)
y V2 (policy que contiene datos de medición; gate que no aplica policy).

## Estructura de carpetas (objetivo)

```
nm_suite/
├── tools/visualparity/                      # VisualParity Core/CLI (.NET 8, futuro)
│   ├── src/
│   │   ├── VisualParity.Core/               # Medición pura
│   │   │   ├── Bundle/                      # EolNormalizer (texto), BundleWriter
│   │   │   ├── Comparators/                 # PixelDiff, BboxCluster, DeterminismCheck
│   │   │   ├── Pairing/                     # missing/extra/duplicate detection
│   │   │   ├── Ranking/                     # NearThresholdFlag, SeverityRank
│   │   │   ├── Panel/                       # CANON/ACTUAL/DIFF rendering
│   │   │   └── Integrity/                   # checksums.json, bundle_sha256
│   │   ├── VisualParity.CLI/                # compare, batch, verify-bundle, inspect
│   │   └── VisualParity.Core.Tests/         # xUnit tests
│   ├── tests/                               # Corpus mínimo
│   ├── visualparity.lock.json               # vp_build_sha256 allowlist
│   └── README.md
│
├── harness/v3/                              # Harness consumidor (Python, futuro)
│   ├── capture_orchestrator.py              # ÚNICO invocador de qa/capture_v8.py
│   ├── state_assertion.py                   # capture_state_assertion.json
│   ├── bundle_verifier.py                   # vp_build_sha256 vs allowlist
│   ├── policy_engine.py                     # Lee closure_policy_v3.yaml
│   ├── anti_fraud/                          # 8 vectores
│   ├── replay/                              # recaptura + recomparación + cardinalidad
│   ├── ci_gate/                             # sólo bloquea
│   ├── agent_runner/                        # denylist real + per-key dispatch
│   ├── semantic_lint/
│   ├── evidence_records/
│   │   ├── active/
│   │   └── revoked/
│   ├── policy/
│   │   ├── closure_policy_v3.yaml
│   │   └── measurement_config_v3.yaml
│   ├── schemas/
│   └── README.md
│
├── docs/VisualParity_V3_1/                  # Este directorio
│
├── qa/
│   ├── capture_v8.py                        # Generador transitorio (ver limits)
│   └── _mockup_canonical/                   # Canon único tras reconciliación
│
└── .github/workflows/visual-parity-v3-gate.yml  # Workflow V3.1 (sólo bloquea)
```

## Separación de capas

| Capa | Componente | Invariante |
|---|---|---|
| **Medición** | VisualParity Core/CLI | Produce métricas crudas + estados de medición. No decide. No conoce "closure". |
| **Política** | `harness/v3/policy/closure_policy_v3.yaml` + `policy_engine.py` | Lee bundle + metadatos y decide ALLOW/BLOCK. No mide. No contiene datos de medición. |
| **Aplicación** | `harness/v3/ci_gate/gate.py` + `capture_orchestrator.py` + `replay/replay.py` + `agent_runner/runner.py` | Orquesta medición + política + anti-fraud + replay. No decide. Sólo ejecuta y reporta veredicto de la política. |
| **Persistencia** | `harness/v3/evidence_records/{active,revoked}/` | Escribe records inmutables. No orquesta. No decide. |

**V1 peca** al mezclar medición + política + aplicación + persistencia en
`close_visual_key.py` (1124 LOC).

**V2 peca** al poner datos de medición (`known_non_deterministic_surfaces`,
`state_ambiguous_pairs`, `near_threshold_policy.margin_fraction`) en la
política (`closure_policy.yaml`).

**V3.1** separa estrictamente: `closure_policy_v3.yaml` contiene sólo
reglas; `measurement_config_v3.yaml` contiene parámetros de medición
(thresholds, near_threshold margin, determinism threshold).

## Límites por capa

### VisualParity Core/CLI puede

- Emparejar CANON PNG vs ACTUAL PNG.
- Calcular métricas (changed_pixel_ratio, mean_abs_diff, bbox clusters,
  windowed_ssim).
- Generar panel CANON / ACTUAL / DIFF.
- Rankear severidad visual.
- Exportar evidence bundle (`.vpbundle`).
- Verificar estructura del bundle.
- Emitir estados de medición.

### VisualParity Core/CLI no puede

- Decidir cierre.
- Emitir `CLOSURE_PASS`.
- Emitir `HUMAN_REVIEWED_PASS/FAIL` final.
- Interpretar reglas clínicas/producto de `nm_suite`.
- Ejecutar `qa/capture_v8.py`.
- Invocar agentes.
- Modificar handoff.
- Modificar policy.
- Cerrar keys.
- Usar bulk review como atajo.

### Harness v3 puede

- Generar capturas (vía `capture_orchestrator.py` → `qa/capture_v8.py`).
- Generar `capture_provenance.json`.
- Generar y validar `state_assertion.json`.
- Invocar VisualParity.
- Calcular `bundle_sha256` al consumir.
- Verificar `vp_build_sha256` contra allowlist (`visualparity.lock.json`).
- Aplicar `closure_policy_v3.yaml`.
- Correr anti-fraud (8 vectores).
- Correr replay con recaptura real.
- Decidir `BLOCK`, `HUMAN_REVIEW_REQUIRED`, `CANDIDATE_ONLY`,
  `CLOSURE_ALLOWED`, `HUMAN_REVIEWED_PASS`, `HUMAN_REVIEWED_FAIL`.
- Escribir evidence records.

### Harness v3 no puede

- Invocar V1/V2 scripts.
- Usar `--no-regen` como cierre.
- Usar `reopen_legacy_all`.
- Aceptar bulk `HUMAN_REVIEWED_PASS`.
- Confiar en `signature.sha256` como firma.
- Mezclar commits de producto / VisualParity / policy / canon / closure.

## Estados VisualParity permitidos

VisualParity Core/CLI emite **sólo** estos estados:

- `NO_DIFF`
- `LOW_DIFF`
- `SUSPICIOUS`
- `HIGH_DIFF`
- `MISSING_PAIR`
- `SIZE_MISMATCH`
- `NEAR_THRESHOLD`
- `NON_DETERMINISTIC`
- `MEASUREMENT_DISPUTE_CANDIDATE`

## Estados prohibidos en VisualParity

VisualParity Core/CLI **nunca** emite estos estados (son del harness):

- `CLOSURE_ALLOWED`
- `BLOCK`
- `CLOSURE_PASS`
- `HUMAN_REVIEWED_PASS`
- `HUMAN_REVIEWED_FAIL`

## Mapeo estado VisualParity → acción harness

| Estado VisualParity | Acción harness v3 | Requiere |
|---|---|---|
| `NO_DIFF` | `CLOSURE_ALLOWED` | tests_pass, anti_fraud_clean, replay_full_regen_pass, evidence_byte_reproducible, determinism_pass, state_assertion_valid, canonical_png_hash_in_record, vp_build_sha256_in_allowlist |
| `LOW_DIFF` | `HUMAN_REVIEW_REQUIRED` | (nunca auto-cierre) |
| `SUSPICIOUS` | `BLOCK` | (nunca cierra) |
| `HIGH_DIFF` | `BLOCK` | (path alternativo: `MEASUREMENT_DISPUTE`, no override) |
| `MISSING_PAIR` | `BLOCK` | |
| `SIZE_MISMATCH` | `BLOCK` | |
| `NEAR_THRESHOLD` | `HUMAN_REVIEW_REQUIRED` | |
| `NON_DETERMINISTIC` | `BLOCK` | |
| `MEASUREMENT_DISPUTE_CANDIDATE` | `HUMAN_REVIEW_REQUIRED` | recalibración versionada + regeneración de bundle |
| `HUMAN_REVIEWED_PASS` (harness) | `CLOSURE_ALLOWED` | reviewer, timestamp_utc, reason_text_min_50_chars, reviewer_screenshot_sha256, + todos los required de NO_DIFF |
| `HUMAN_REVIEWED_FAIL` (harness) | `BLOCK` | |

## Flujo end-to-end (objetivo, no implementado)

```
1. Owner declara target_set en harness/v3/agent_runner/current_target_set.txt
2. capture_orchestrator.py invoca qa/capture_v8.py --key <key> --theme <theme>
   → genera qa/_captures_v8/<key>.png + CAPTURE_MANIFEST.json
   → genera capture_provenance.json
3. state_assertion.py genera capture_state_assertion.json
   → valida assertion vs surface_key declarado
   → si mismatch: BLOCK (state_ambiguity)
4. capture_orchestrator.py invoca VisualParity CLI:
   visualparity compare --canon qa/_mockup_canonical --actual qa/_captures_v8
                       --out vp_report --profile strict --git-head <HEAD>
                       --determinism-check <actual2_dir>
   → genera bundle + panel + integrity/checksums.json
5. bundle_verifier.py:
   → verifica vp_build_sha256 vs visualparity.lock.json
   → calcula bundle_sha256
   → verifica integrity/checksums.json
6. anti_fraud/ (8 vectores) corre sobre app/, hub/, shared/, qa/, tests/, docs/, tools/
7. policy_engine.py lee closure_policy_v3.yaml + bundle + assertion + anti_fraud
8. replay/replay.py (si es cierre): recaptura + recomparación + cardinalidad exacta
9. ci_gate/gate.py: exit 0 = PASS (desbloqueado para cierre), exit 1 = FAIL (BLOCK)
10. Si PASS y es cierre: harness escribe evidence_records/active/<key>.closure_decision.json
```

## Stack

- **VisualParity Core/CLI:** .NET 8. CLI primero. WPF después (fase futura,
  sólo `review_annotation.json`). WinUI fuera de V3.1.
- **Harness v3:** Python 3.12. Preserva compatibilidad con
  `qa/capture_v8.py` (PyQt6 offscreen) y `qa/_mockup_canonical/`.
- **CI:** GitHub Actions. Self-hosted runner para cierre (decisión owner #6).

## Estado actual (Fase 0A)

- **Implementado:** sólo documentación y skeletons no funcionales
  (`tools/visualparity/README.md`, `harness/v3/README.md`,
  `harness/v3/policy/*.example.yaml`, `harness/v3/schemas/README.md`,
  `harness/v3/agent_runner/denylist.example.yaml`).
- **No implementado:** VisualParity Core, harness v3 funcional, CI V3.1.
