# Visual QA — Governance Hardening Audit (Fase 1)

Base SHA: `5ffcca1a3b4abb1d3fd161d24c3cd2fd39f26ec2` (main, clean).
Measured against a fresh full capture (116/116 PNG, `NM_VAS_INTROSPECT=1`) +
full `layered_visual_compare` (`REPORT_EVIDENCE_VALID: YES`, 75 PASS / 41
divergence).

This report is committed (force-added past the `reports/` gitignore) so the
audit trail is versioned. The reproducible PoC lives in
[`poc/poc_canonical_injection.py`](poc/poc_canonical_injection.py); the
corpus-calibration helper is [`poc/analyze_corpus.py`](poc/analyze_corpus.py).

---

## 1. System of record (verified against live repo, not docs)

| Concern | Source of truth | Notes |
|---|---|---|
| Worker flow | `WORKER_VISUAL_QA_FLOW.md` | 6 owner trigger modes, resolved by `qa/target_scope.py`. |
| Scope resolution | `qa/target_scope.py` | Pure read-only over the `## Checklist` of the handoff. NOT R0. |
| Capture | `qa/capture_v8.py` (R0) | Per-key subprocess; writes PNG + `CAPTURE_MANIFEST.json` + VAS sidecar + provenance. |
| Compare | `qa/layered_visual_compare.py` (R0) | Only active closure comparator: odiff + raw pixel + windowed/global SSIM + layout bbox + region + perfect/near-perfect fraud flags. |
| VAS gate | `qa/vas_gate.py` (R0) + `qa/vas_introspect.py` (R0) | Validates sidecar provenance chain (PNG sha, script sha, manifest cross-check, entry id) + `fail_count==0` + no high/medium divergences. |
| Modal audit | `tools/qa/audit_modal_backdrop_blur.py` (R0) | Back-screen dependency + centering + bbox + backdrop + blur-ratio; static scrim/blur constants pinned in anti-fraud. |
| Anti-fraud | `qa/anti_fraud_scan.py` (R0) | Static AST scan of `app/hub/shared` (+ qa-harness mode): forbids canonical/reference/report artifact reads, overlay identifiers, pixmap-with-artifact, obfuscation sinks, modal scrim/blur constant drift. |
| Close | `qa/close_visual_key.py` (R0) | Re-runs full gate in an isolated worktree at HEAD, writes deterministic evidence record, flips checkbox. |
| Replay | `qa/replay_visual_closure.py` (R0) | Audits `base..HEAD`: closed-checkbox + note tamper + orphan records + R0-touched-with-closure; `--regen` regenerates pixels, `--no-regen` (CI) is structural (hash/paths/R0/schema only). |
| Runner | `qa/run_visual.ps1` | Single validation runner (`-Key`/`-PlanFile`/`-All`); reparation loop, not closure evidence. |

Runner-vs-closure boundary, R0 list, and the six trigger modes are consistent
between code and docs. All six modes resolve mechanically and correctly
(next-key → `hub:textos-globales@light`; explicit-list rejects a closed key;
`--plan` emits valid `app,view,theme,key` rows).

## 2. Checklist / PASS-viejo matrix (116 keys)

| Class | Count | Verdict |
|---|---|---|
| Open `[ ]` | 52 | Working set. |
| Closed — legacy (no evidence record) | 60 | Pre-replay-era; **not trustworthy as closures**. → In the owner-audit correction round these 60 were **reopened** (`--reopen-legacy-all`): the honest end-state is 112 open / 4 closed (see `FINAL_VALIDATION.md`). |
| Closed — evidence-backed | 4 | `suite:dbt-library@{light,dark}`, `hub:detalle-resumen-ia-0@{light,dark}`. Record hash matches handoff note, schema v1, `result: PASS`. **Still PASS under a fresh gate; still PASS under the hardened gate** (global ssim 0.61–0.94, none `-empty`). LEGITIMATE. |
| Revoked records | 2 | `docs/closure_evidence/revoked/hub_detalle-resumen-ia-0-*.json` — well-formed, sanctioned-reopen shape. |

Emulated virgin checklist run (owner trigger *"todas las keys abiertas"*):
`target_scope --mode all-open-keys` → 52 keys, ordered, no duplicates.
`REPORT_EVIDENCE_VALID: YES`, `HANDOFF_CLOSURE_ALLOWED: NO`
(`real_divergence_present`) — correct for a partial working set.

## 3. Findings

### F1 — `-empty` unconditional trivial exemption → canonical-copy false PASS  ·  REPRODUCED

`qa/layered_visual_compare.py::_is_trivial_surface` exempts any view whose name
ends `-empty` from **both** `suspicious_perfect_match` and `near_perfect_match`,
unconditionally. Corpus reality: all 10 `-empty` canonicals carry chrome /
sidebar / empty-state art — grayscale std **13.3–16.0** (far above the 2.0
trivial epsilon), honest global ssim **0.31–0.49**. So a perfect match on them
is exactly as implausible as on any other surface, yet it is waved through.

PoC (verbatim copy as the "runtime capture"):

```
suite:timer-empty@light    noise 0.00  changed 0.0000  gssim 1.0000  susp False  ->  PASS  (false)
hub:pacientes-empty@light  noise 0.00  changed 0.0000  gssim 1.0000  susp False  ->  PASS  (false)
```

Impact: 10 currently-open `-empty` keys (timer/avisos/actividades/rutina/
pacientes ×2). The existing test `test_empty_state_view_is_exempt` *encodes*
this wrong behavior (it draws a content-rich image and asserts PASS).

### F2 — Noised canonical copy evades both fraud flags → false PASS  ·  REPRODUCED

`suspicious_perfect_match` requires `changed==0`; `near_perfect_match` requires
`changed<0.005 AND ssim>0.995`. The band between `changed 0.005` and the pass
bar (`0.08` sparse / `0.10` dense) is unguarded. A canonical copy with graded
noise lands there while GLOBAL ssim stays far above the honest ceiling:

```
suite:home@light            noise 0.03  changed 0.0279  gssim 0.9884  ->  PASS (false)
suite:home@light            noise 0.10  changed 0.0897  gssim 0.9637  ->  PASS (false)
suite:recuperar-acceso@light noise 0.03 changed 0.0286  gssim 0.9831  ->  PASS (false)
```

The structural layers do not help: a copy has bbox delta ≈ 0, largest-region ≈
0, odiff ≈ noise-only. (`suite:dbt-practice-stop` copy happens to FAIL, but only
via an *accidental* content-bbox perturbation — `bbox_dh=109` from noise near
the corner samples — not a designed defense; interior-only noise avoids it.)

**Calibration (real 116-key corpus).** Honest GLOBAL ssim never approaches a
copy's:

| density class | canon std | honest global-ssim max | injection ceiling | margin |
|---|---|---|---|---|
| text-dense / content | `< 35` | **0.743** (`hub:detalle-plan-rutina@light`) | **0.90** | 0.157 |
| sparse / high-contrast | `>= 35` | **0.966** (`suite:dbt-practice-check-facts@light`) | **0.985** | 0.019 |

Overall honest global-ssim max = **0.966**. A copy sits at 0.95–1.0. A
density-aware GLOBAL-ssim ceiling is therefore a clean discriminator with
provably zero honest-render regressions on the current corpus, tightest exactly
where fraud is most tempting (dense surfaces, where honest ssim is only
0.4–0.74). The static anti-fraud scan does not stop this because the canonical
can be smuggled as a product **asset** PNG (non-forbidden path), so no string
token trips.

### F3 — Structural (`--no-regen`) replay cannot detect a fabricated record  ·  PLAUSIBLE (by design), HARDENED

CI runs `replay --no-regen`. In that mode `_validate_one_closure` checks only:
note present, commit in range, record path valid, `record_sha256 == evidence`.
It never re-derives pixels (impossible on the stdlib-only runner) **and never
even asserts `result=="PASS"` or that metrics are within the gate bars**. The
project's own test `test_replay_no_regen_validates_structurally_without_regeneration`
builds a hand-written `_record()` with fabricated metrics and asserts a
structural pass. So a lazy fabricator who writes an internally-consistent record
(correct canonical hash) passes CI; only the closing machine's local `--regen`
is the real pixel gate, and nothing proves it ran.

This is partly by design (pixel truth is platform-bound to the closing
machine). Hardening keeps that boundary but closes the lazy path: add a cheap
**structural record-sanity** check (runs in both modes) — `result=="PASS"`,
schema v1, and the uniform upper bounds every real PASS satisfies
(`changed_pixel_ratio<=0.10`, `mean_abs_diff<=0.035`, `max_bbox_delta_px<=18`).
All 4 existing evidence records satisfy these. The residual (a careful in-bounds
fabrication) still requires local `--regen` — documented explicitly as the only
pixel gate.

### F4 — Stale human-facing scope guidance in the handoff  ·  DEUDA DOCUMENTAL, CURED

`## NEXT_KEY` snapshot names `hub:detalle-resumen-ia-0@light` (now CLOSED);
`## OPEN KEYS` convenience view still lists the 2 resumen-ia keys as open and
headers "54 keys abiertas" (real open count = **52**). The mechanical resolver
(`target_scope.py`) is correct — but the stale snapshot/view is exactly the
ambiguous guidance the governance goal forbids. Cured in Fase 2.

## 4. Not reproduced / adequately gated (no change)

- **Threshold overrides**: `report_evidence_valid` requires default thresholds;
  any `--min-ssim`/`--raw-*`/`--no-odiff`/`--no-panels` sets `evidence_valid:
  NO`. Closure needs `YES`. Solid.
- **Modal backdrop/blur**: back-screen dependency + centering/bbox + backdrop
  mean + blur-ratio, plus static pinning of scrim `(20,18,14,128)` and blur
  radius `3`. The prior blur/alpha gaming path is closed. No new control needed.
- **Duplicate captures / sidecar / manifest / provenance**: capture flags
  duplicate PNG hashes; VAS validates the full provenance chain (PNG sha,
  script sha, manifest cross-check, entry id, sidecar link). Strong.
- **R0 kernel + closure in same range**: replay fails
  `kernel_changed_with_visual_closure`. Verified in code + tests.
- **Reopen / revoked records**: sanctioned-reopen shape is the only record
  change replay accepts without a closed item; anything else is
  `orphan_evidence_record`. Solid.
- **Anti-fraud env/obfuscation**: env-route tokens, `getattr(os,...)`,
  `importlib`, base64/decode, command sinks all covered in qa-harness mode.

## 5. Saneamiento proposed (implemented in Fase 2 / Commit 2)

1. **Remove the `-empty` name exemption** in `_is_trivial_surface`; keep only
   the std `< 2.0` flat-canonical exemption. Update the one test that encoded
   the old behavior; add a flat-`-empty`-stays-exempt test. (Closes F1.)
2. **Density-aware canonical-injection ceiling** in the near-perfect predicate:
   flag non-trivial surfaces whose global ssim `>= 0.90` (dense) / `>= 0.985`
   (sparse) as `NEAR_PERFECT_MATCH` (blocked, `AUDIT_REQUIRED`). Corpus-
   calibrated, zero honest regressions. Add negative tests. (Closes F2's easy
   band; documents the residual heavy-noise needle + its layered complements.)
3. **Structural record-sanity** in `replay._validate_one_closure` (both modes):
   `result==PASS` + uniform metric upper bounds. New reason
   `record_metrics_out_of_bounds`. (Hardens F3 for CI.)
4. **Cure the handoff**: fix `## NEXT_KEY` snapshot + `## OPEN KEYS` view +
   counts; add concise Gate-Hardening subsections for #1–#3. (Closes F4.)

All four are R0-file edits made in a closure-free range (0 checkboxes flipped),
so the R0 rule permits them; existing evidence-backed closures remain valid and
still PASS under the hardened gate.
