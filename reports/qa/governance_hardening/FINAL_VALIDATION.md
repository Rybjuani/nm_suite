# Visual QA — Governance Hardening: Final Validation (post-hardening reaudit)

SHA base: `5ffcca1a3b4abb1d3fd161d24c3cd2fd39f26ec2` (= `origin/main`, intacto).
Branch: `qa/governance-hardening` (no push — owner decides). El SHA final es el
tip de la branch tras el commit de correcciones; no se hardcodea acá para no
quedar stale — usá `git rev-parse qa/governance-hardening`.

## Commits (ver `git log 5ffcca1a3..qa/governance-hardening`)

| # | Scope | Files |
|---|---|---|
| 1 | Fase 1 audit + PoCs (sin cambio de código) | `reports/qa/governance_hardening/{REPORT.md,poc/*}` |
| 2 | Fase 2 gate hardening + tests + doc cure | `qa/layered_visual_compare.py`, `qa/replay_visual_closure.py`, `tests/test_suspicious_perfect_match.py`, `tests/test_replay_visual_closure.py`, `VISUAL_REPAIR_HANDOFF.md` |
| 3 | Reporte de validación final | `reports/qa/governance_hardening/FINAL_VALIDATION.md` |
| 4 | Correcciones del audit del owner: reopen 60 legacy, asset-identity scan, NEXT_KEY/OPEN KEYS stale-proof, contradicciones `-empty`/manual-review/thresholds | `qa/close_visual_key.py`, `qa/anti_fraud_scan.py`, `qa/layered_visual_compare.py`, `VISUAL_REPAIR_HANDOFF.md`, `WORKER_VISUAL_QA_FLOW.md`, tests, este reporte |

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

## Keys state (116) — after the owner-audit corrections

| Class | Count | Status |
|---|---|---|
| Open `[ ]` | **112** | Working set. Now includes the 60 formerly-legacy keys (reopened). |
| Closed — evidence-backed | 4 | Integrity-valid; **still PASS under the hardened gate**. The only closed keys. |
| Closed — legacy (no evidence) | **0** | **Reopened** via `close_visual_key.py --reopen-legacy-all` (2026-07-04): they never had a record proving they passed the gate, so keeping them `[x]` misrepresented the checklist. Now `[ ]`, to revalidate with real evidence. `--skip-legacy` no longer needed. |
| Revoked records | 2 | Well-formed sanctioned-reopen shape. |

The checklist is now honest: only evidence-backed closures remain `[x]`.
No old PASS survives unverified. The 4 evidence-backed keys re-verified PASS
under the hardened gate.

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

## Residual — now closed from both ends

The canonical-injection vector is closed at both entry points:

- **Verbatim canonical shipped as a product asset**: `anti_fraud_scan.py` now
  scans `assets/`, `app/`, `hub/`, `shared/` for any PNG byte-identical to a
  canonical (`asset_canonical_identity`), stdlib-only so it runs in CI and in
  `close_visual_key`. Verified: CLEAN on the real repo (no false positive),
  FAIL when a canonical is copied into `assets/`.
- **Render implausibly close to canonical** (with or without noise): the
  density-aware injection ceiling blocks it at compare time.

Together these leave no free ride from the canonical. Beyond them, a capture
whose global ssim is genuinely below the density ceiling is, by definition, a
materially different render that must pass the honest gate (changed / windowed /
bbox / region / odiff / VAS) on its own merits — that is the gate working, not a
bypass. No known false-PASS path remains.
