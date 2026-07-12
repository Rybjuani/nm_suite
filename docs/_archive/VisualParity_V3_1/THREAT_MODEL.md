# Threat Model V3.1 — Matriz VQA-RT-001

> **Fase 0A skeleton — no runtime authority.** Este documento resume la
> matriz de amenazas derivada de las hipótesis VQA-RT-001 owner-validadas.
> Los estados de control son diagnósticos; ningún control está implementado
> en Fase 0A.

## Convención de estados

| Estado | Significado |
|---|---|
| `VERIFIED_IN_REPO` | Evidencia directa en HEAD `c645405e` (código, CI, evidence record, handoff). |
| `OWNER_VALIDATED_NOT_REPRODUCED` | Owner validó la hipótesis vía red-team; no reproducida en sandbox sin toolchain (PyQt6 + odiff + display). |
| `DOCUMENTED_IN_V2_BUT_NOT_ENFORCED` | V2 declara mitigación en docs/policy pero no la implementa en código. |
| `NOT_VERIFIED` | No se pudo verificar en auditoría; no implica ausencia. |
| `PENDING_IMPLEMENTATION` | Control requerido por V3.1; no existe en V1/V2; pendiente de implementar en Fases posteriores. |

## Matriz de amenazas

| # | Amenaza | Hipótesis VQA-RT-001 | Evidencia actual | Estado control V3.1 |
|---|---|---|---|---|
| T1 | CRLF/LF afecta evidence records activos | A.1 | Evidence records V1 (`docs/closure_evidence/*.json`) tienen hashes CRLF-era no reproducibles en checkout Linux. MANIFEST canónico con paths Windows hardcoded. | `VERIFIED_IN_REPO` |
| T2 | PASS visual ≠ PASS estructural ≠ evidence byte-reproducible son propiedades distintas | A.3 | V1 `_report_result` chequea 4 propiedades distintas (status, suspicious_perfect_match, near_perfect_match, report_evidence_valid) + `record_sha256` (5ta). | `VERIFIED_IN_REPO` |
| T3 | No determinismo en Actividades, Respiración y report volátil | A.2 / B | `closure_policy.yaml:170-181` (V2) lista 11 surfaces. No verificable en sandbox sin PyQt6. | `OWNER_VALIDATED_NOT_REPRODUCED` |
| T4 | Replay estructural puede pasar mientras replay full falla | A.2 | CI workflow línea 109 ejecuta `replay_visual_closure.py --no-regen` por diseño. V2 `replay.py:57` es stub PASS. | `VERIFIED_IN_REPO` |
| T5 | `target_scope` excluye keys cerradas | B.1 | `qa/target_scope.py:113-114` sólo matchea `[ ]`. | `VERIFIED_IN_REPO` |
| T6 | `close_visual_key` no re-cierra keys cerradas salvo reapertura | B.2 | `qa/close_visual_key.py:707-714` `assert_handoff_key_open` raise `key_already_closed`. | `VERIFIED_IN_REPO` |
| T7 | Replay por `base..HEAD` no revalida todo | B.3 | `qa/replay_visual_closure.py:549` `audited_commits = git_rev_list(repo_root, base_commit, "HEAD")` — sólo `(base, HEAD]`. | `VERIFIED_IN_REPO` |
| T8 | Replay puede devolver PASS vacío | B.4 | `qa/replay_visual_closure.py` loop `for key in sorted(validate_keys)` no ejecuta si `validate_keys` vacío. `result.ok = not failures = True`. | `VERIFIED_IN_REPO` |
| T9 | Duplicate-key spoofing posible | B.5 | Handoff actual tiene 6 duplicate keys (`onboarding`, `onboarding-error`, `recuperar-acceso` × light/dark). V2 `target_scope_v2.py` detecta pero aborta todo. V1 `target_scope.py` no detecta. | `VERIFIED_IN_REPO` |
| T10 | Family/scope policy no estaba realmente enforced | B.6 | `closure_policy.yaml:142-149` (V2) declara `block_if_family_member_failing: true` pero `target_scope_v2.py:family_of` sólo lista, no bloquea. V1 `close_visual_key.py` no toma `--target-set` ni `--family`. | `DOCUMENTED_IN_V2_BUT_NOT_ENFORCED` |
| T11 | Comparator tolerante: timer-paused puede pasar como timer-running | C.1 | V1 `layered_visual_compare.py` thresholds: `min_ssim: 0.92`, `max_changed_pixel_ratio: 0.08`, `max_mean_abs_diff: 0.035`. `compare_pair` añade `state_or_recipe_suspect` pero `_report_result` no lo chequea. Red-team VQA-STATE-001: `timer-paused@light` comparado como `timer-running@light` dio PASS con `changed=0.04265`. | `OWNER_VALIDATED_NOT_REPRODUCED` |
| T12 | Mutaciones visibles pueden quedar PASS | C.2 | Subproducto de T11. Thresholds permiten mutaciones visibles pequeñas. | `VERIFIED_IN_REPO` |
| T13 | Near-threshold PASS existen | C.3 | `home-no-score@light` 0.09977/0.10, `detalle-resumen-ia-0@light` 0.07933/0.08. V1 no tiene `near_threshold` flag. V2 declara `margin_fraction: 0.05` pero el flag vive en VisualParity (no existe). | `VERIFIED_IN_REPO` |
| T14 | `rutina-add-task@dark` muestra divergencias materiales | C.4 | FORENSIC_FINDINGS_V2 #15: red-team confirmó divergencia material incompatible con parity. Aún marcado PASS en `docs/closure_evidence/`. | `OWNER_VALIDATED_NOT_REPRODUCED` |
| T15 | Closer puede cerrar key con texto activo FAIL/deuda/risk | D.1 | `qa/close_visual_key.py:assert_handoff_key_open` sólo chequea checkbox `[ ]`. No parsea texto. Red-team VQA-SEM-001: cerró `suite:timer@light` con `status=FAIL`, `OPEN debt`, `risk`, `needs owner decision`. | `VERIFIED_IN_REPO` |
| T16 | Handoff puede quedar `[x]` con semántica FAIL | D.2 | `update_handoff_closure` reescribe checkbox a `[x]` + 4 sub-notes; no toca resto del texto. `status=FAIL` persiste. | `VERIFIED_IN_REPO` |
| T17 | `DECISIÓN-OWNER` fue salida explotable | D.3 | 11 archivos en docs activos + harness contienen `DECISIÓN-OWNER`. `QT_HTML_KNOWN_MISMATCHES.md` lo define como clasificación operativa. | `VERIFIED_IN_REPO` |
| T18 | `OWNER_EXCEPTION_ACTIVE` no debe recrear bypass | D.4 | `OWNER_EXCEPTION_ACTIVE` aparece en 5 archivos como string, no mecanismo. Si se implementa como flag, reproduce el patrón explotable. | `DOCUMENTED_IN_V2_BUT_NOT_ENFORCED` |
| T19 | 116/116 no es homogéneo ni retroactivamente confiable | D.5 | Métricas heterogéneas en evidence records (sample: `timer-running@light` changed_pixel_ratio 0.04214). 16 marcados `[~]` blocked en handoff V2 pero bloqueo es documentario. | `VERIFIED_IN_REPO` |
| T20 | Anti-fraud puede abortar y dejar reporte PASS stale | E.1 | V1 `run_visual.ps1:90-94` corre anti-fraud y `exit 1` on failure, pero `New-Item -ItemType Directory -Force $OutDir` (l.105) no limpia. `LAYERED_VISUAL_REPORT.json` previo queda. V2 `anti_fraud/scan.py` docstring miente sobre `stale_bundle_in_outdir` (no implementado). | `VERIFIED_IN_REPO` |
| T21 | No aceptar archivos por path sin run_id/hash/mtime/log actual | E.2 | V1 evidence records no tienen `run_id`. V2 no mejora. | `VERIFIED_IN_REPO` |
| T22 | Canonical smuggling obvio, inactive source, wrong sidecar, tamper básico son controles positivos, no inmunidad total | E.3 | V1 `anti_fraud_scan.py` tenía 6 categorías; V2 redujo a 1 (regresión). Smuggle en `tests/fixtures/`, `docs/`, `tools/qa/` no detectado por V2. | `VERIFIED_IN_REPO` |
| T23 | Stub PASS (replay V2) | — | `harness/replay/replay.py:57` retorna `(True, "stub_pass")` siempre. V2 reproduce el pecado V1 (#8). | `VERIFIED_IN_REPO` |
| T24 | Gate V2 no aplica policy | — | `harness/ci_gate/gate.py:70` vs `:143`: `evaluate_surface(surface, policy)` recibe `bundle`. `required_properties` nunca se verifican. | `VERIFIED_IN_REPO` |
| T25 | VisualParity no existe | — | `harness/README.md:26` referencia `github.com/Rybjuani/visualparity — to be created`. V2 es consumidor de productor inexistente. | `VERIFIED_IN_REPO` |
| T26 | V2 se auto-rechaza | — | `target_scope_v2.py` FAIL con 6 duplicate keys. `doc_keyword_lint.py` FAIL con 16+ ocurrencias `DECISIÓN-OWNER` (incl. sus propios archivos). `replay.py` FAIL con 0 keys. | `VERIFIED_IN_REPO` |
| T27 | CI no corre tests | — | `.github/workflows/visual-closure-replay.yml` sólo corre anti-fraud V1 + replay `--no-regen`. No pytest. `tests/conftest.py` fuerza `pytestqt` (no instalable en sandbox). | `VERIFIED_IN_REPO` |
| T28 | `reopen_legacy_all` existe | — | `qa/close_visual_key.py:1002-1058`. Masa de reopen sin per-key reason/reviewer. | `VERIFIED_IN_REPO` |
| T29 | Comparator thresholds CLI-overridable | — | `qa/layered_visual_compare.py:1383-1387` permite `--min-ssim`, `--raw-changed-threshold`, etc. | `VERIFIED_IN_REPO` |
| T30 | Evidence record sin canonical PNG hash | — | `docs/closure_evidence/suite_timer-running-light.json` no tiene `canonical_png_sha256`. | `VERIFIED_IN_REPO` |
| T31 | Bulk human pass posible | — | No hay mecanismo bulk en V1/V2, pero no hay defensa explícita. `reopen_legacy_all` es masa análoga. | `NOT_VERIFIED` |
| T32 | Mixed commits posible | — | No hay test de mixed commit en V1/V2. | `NOT_VERIFIED` |
| T33 | VisualParity invoca capture_v8 o agentes | — | V2 no implementado. V3-previo no especifica. | `PENDING_IMPLEMENTATION` |
| T34 | `--no-regen` como cierre | — | CI workflow línea 109. V2 lo prohibe pero es stub. | `VERIFIED_IN_REPO` |

## Controles V3.1 requeridos (PENDING_IMPLEMENTATION)

Cada amenaza mapea a un control V3.1 a implementar en Fases posteriores:

| Amenaza | Control V3.1 |
|---|---|
| T1 | `EolNormalizer` sólo para texto; PNGs raw bytes. Hashes LF-normalized para `.json/.yaml/.md/.py`. |
| T2 | Evidence record con `bundle_sha256`, `vp_build_sha256`, `policy_sha256`, `closure_decision_sha256` separados. |
| T3 | `DeterminismCheck` (dos actuals, `changed_ratio < 0.005`). |
| T4 | `--no-regen` no existe. Replay = recaptura + recomparación + cardinalidad exacta. |
| T7 | Replay con `--all-closed` por defecto; range audit no suficiente. |
| T8 | `replayed_keys == expected_keys`; `replayed_keys=0` con `expected_keys>0` = BLOCK. |
| T9 | Duplicate-key como invariant del parser de records, no lint aparte. |
| T10 | Family enforcement real en gate: verifica otros keys del target set antes de ALLOW_CLOSURE. |
| T11 | `capture_state_assertion` generado por harness; validado antes de aceptar capture. |
| T12 | Thresholds constantes del comparator (no CLI-overridable). Calibrados con corpus. |
| T13 | `NearThresholdFlag` en VisualParity; harness requiere `HUMAN_REVIEWED_PASS`. |
| T14 | Recalibración con corpus `rutina-add-task@dark`. |
| T15-T16 | `semantic_lint` parsea handoff line; forbidden phrases bloquean (no substring matching). |
| T17-T18 | `DECISIÓN-OWNER` prohibido en docs activos. `OWNER_EXCEPTION_ACTIVE` sólo como registro firmado, no flag. |
| T19 | No treat-as-homogeneous; cada closure se valida individualmente. |
| T20 | `BundleWriter` wipa OutDir antes de escribir. Harness verifica `bundle.generated_at` > latest commit. |
| T21 | Evidence record con `capture_provenance.json` (run_id, git_head, mtime, capture_v8_sha256). |
| T22 | Anti-fraud 8 vectores (cobertura inicial de vectores conocidos, no cobertura total). |
| T23 | No stubs. Si no implementado, `raise NotImplementedError` y gate BLOCK. |
| T24 | Gate aplica policy real vía `policy_engine.py`; verifica `required_properties`. |
| T25 | VisualParity Core/CLI implementado en `tools/visualparity/`. |
| T26 | V2 descartado; V3.1 no hereda stubs. |
| T27 | Tests spliteados: unitarios (no-Qt) en CI Ubuntu; Qt/e2e en self-hosted runner. |
| T28 | `reopen_legacy_all` no existe en V3.1. |
| T29 | Thresholds son constantes. |
| T30 | Evidence record incluye `canonical_png_sha256`. |
| T31 | Un `review_annotation.json` por surface; harness rechaza N annotations idénticas. |
| T32 | Test de mixed commit en pre-commit hook + CI. |
| T33 | Separación: VisualParity no puede invocar `capture_v8.py` ni agentes. |
| T34 | `--no-regen` no existe. |

## Cobertura anti-fraud (redline)

Anti-fraud V3.1 implementa **8 vectores como cobertura inicial de vectores
conocidos**. No es cobertura total ni inmunidad. Denylist real pero no
única defensa. Vectores nuevos requieren adición versionada + re-validación
de corpus.

Los 8 vectores:

1. Asset byte identity (PNG en product code)
2. String tokens (referencias a canonical en código)
3. Pixmap-with-reference (`QPixmap("qa/_mockup_canonical/...")`)
4. Modal backdrop constants (modificación de `_NM_MODAL_BLUR_RADIUS_*`)
5. AST scan (obfuscación con `chr()` + `eval()`, `importlib.import_module`)
6. Canonical PNG hash in record (verifica canonical al commit de cierre)
7. Capture_v8 integrity (verifica `capture_v8.py` no modificado entre capture y replay)
8. Sidecar provenance (sidecar VAS generado por `vas_introspect.py` al commit)
