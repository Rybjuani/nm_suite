# Visual QA — Governance Hardening: Final Validation (post-hardening reaudit)

SHA base: `5ffcca1a3b4abb1d3fd161d24c3cd2fd39f26ec2`
SHA final: `42567e6be991c7de8d4762fb4f3217b3e9bea88d`
Branch: `qa/governance-hardening` (no push — owner decides).

## Commits

| # | SHA | Scope | Files | Δ |
|---|---|---|---|---|
| 1 | `7891c12bd` | Fase 1 audit + PoCs (no code change) | `reports/qa/governance_hardening/{REPORT.md,poc/*}` | +362 |
| 2 | `42567e6be` | Fase 2 gate hardening + tests + doc cure | `qa/layered_visual_compare.py`, `qa/replay_visual_closure.py`, `tests/test_suspicious_perfect_match.py`, `tests/test_replay_visual_closure.py`, `VISUAL_REPAIR_HANDOFF.md` | +288 / −21 |
| 3 | this | Final validation report | `reports/qa/governance_hardening/FINAL_VALIDATION.md` | — |

## Mandatory validation results

| Check | Result |
|---|---|
| Anti-fraud (`--mode all`) | **CLEAN** (runtime + qa-harness) |
| QA gate test suite (13 files) | **238 passed** (was 228 + 10 new) |
| Consumer visual-contract sweep (home/hub/dbt/registro/onboarding/no-legacy) | **42 passed** |
| ruff (changed files) | **clean** |
| PoC before hardening | **10 false-PASS rows** |
| PoC after hardening | **0 false-PASS rows** (all → SUSPICIOUS / NEAR_PERFECT) |
| Full 116-key compare, before vs after | PASS **75 → 75**, **0 keys reclassified**, suspicious/near **0** on honest corpus |
| Replay `--regen` (`base..HEAD`) | **PASS** — replayed 0, skipped_legacy 60 |
| Replay `--no-regen` (CI structural) | **PASS** — replayed 0, skipped_legacy 60 |
| 4 evidence-backed closures under hardened gate | **still PASS** (global ssim 0.61–0.94; none `-empty`) |
| Six official trigger modes | all resolve mechanically (below) |
| Git final state | **clean** (compare artifacts are gitignored) |

## Six official triggers — emulation

| Trigger | Resolver | Result |
|---|---|---|
| `## NEXT_KEY` | `target_scope --mode next-key` | `hub:textos-globales@light` |
| first-N (N=3) | `--mode first-n --n 3` | textos-globales@light, pacientes@light, textos-globales@dark |
| batch (N=3) | `--mode batch --n 3` | identical to first-N ✓ |
| family | `--mode family` | Hub Patients / Global Texts (6 keys) |
| all-open-keys | `--mode all-open-keys` | 52 keys, ordered, no dupes |
| explicit-list | `--mode explicit-list --keys …` | open keys accepted; a CLOSED key errors `keys_not_open_or_unknown` |

`--plan` emits valid `app,view,theme,key` rows for `run_visual.ps1 -PlanFile`.
A worker can drive any of the six without reading stale/contradictory docs: the
`## NEXT_KEY` snapshot and `## OPEN KEYS` view now agree with the resolver.

## Keys state (116)

| Class | Count | Status after hardening |
|---|---|---|
| Open `[ ]` | 52 | Working set (unchanged). |
| Closed — legacy (no evidence) | 60 | Skipped with `--skip-legacy`; still `invalidated-pending-revalidation`. Re-closing needs real evidence. |
| Closed — evidence-backed | 4 | Integrity-valid; **still PASS under the hardened gate**. Legitimate. |
| Revoked records | 2 | Well-formed sanctioned-reopen shape. |

No old PASS became illegitimate under the hardened gate (the 4 evidence-backed
keys re-verified PASS; the 60 legacy were already flagged non-trustworthy — the
hardening does not change their status, it only makes any *future* re-closure
harder to fake).

## What changed in the gate (net)

1. `-empty` name exemption **removed** — 10 empty keys are no longer a free
   canonical-injection lane. Only flat canonicals (std < 2.0) stay exempt.
2. **Density-aware canonical-injection ceiling** (global ssim ≥ 0.90 dense /
   ≥ 0.985 sparse on non-trivial surfaces) → `NEAR_PERFECT_MATCH` / blocked.
3. **Structural record-sanity** in replay (`result==PASS` + uniform metric
   bars) hardens the CI `--no-regen` path against lazy record fabrication.
4. Handoff cured (NEXT_KEY snapshot, OPEN KEYS view, counts) + concise docs.

No control was weakened, none added without a reproduced false-PASS path, and
every threshold is calibrated on the real 116-key corpus with a verified
zero-honest-regression margin. The six official triggers remain usable as-is.

## Residual (documented, not a known false PASS)

A determined attacker who smuggles a canonical PNG as a product asset AND adds
enough noise to drop global ssim below the density ceiling still has to clear
`changed_pixel_ratio` / windowed-SSIM (both degrade as noise rises), the VAS
introspection contract, and the static anti-fraud scan on any code path that
loads the asset. This is a narrow, quality-degrading needle, not the wide easy
band that existed before. Closing it fully would require an asset-vs-canonical
byte/perceptual identity scan over `assets/`; deferred as it needs its own
corpus calibration and is out of the reproduced-vector scope.
