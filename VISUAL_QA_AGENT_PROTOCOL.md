# Visual QA Agent Protocol

This file is the active protocol for visual parity work. Read it before editing
`VISUAL_REPAIR_HANDOFF.md`.

## Active Sources

- Canonical source of truth: `qa/_mockup_canonical/`.
- Runtime source of truth: fresh full captures in `qa/_captures_v8/`.
- Canonical HTML source: `qa/pack canonico/neuromood-mockup_reparado.html`.
- Operational comparator: `qa/layered_visual_compare.py`.
- Canonical HTML/mockup parity auditor:
  `tools/qa/audit_mockup_parity_baseline.py`.

DBT canonical v2 is the active baseline: the official mockup set has 116
captures (58 views x 2 themes), and DBT has 16 formal practice modal surfaces.
The earlier STOP-only DBT closure is historical evidence only. No previous
`suite:dbt-practice-stop` PASS can close DBT as a full family after this baseline
promotion.

Never use any HTML under `reports/` as canonical input. Files such as
`reports/.../sources/original_HEAD.html` are forensic snapshots produced by
auditors to compare `HEAD` against the working tree. They are
`DO_NOT_USE_AS_CANON`; the only allowed HTML source for official canonical PNGs
is `qa/pack canonico/neuromood-mockup_reparado.html`.

Desktop zip files are archival evidence only. Do not use
`C:\Users\nosom\Desktop\_mockup_canonical.zip` or
`C:\Users\nosom\Desktop\captures_v8_2026-06-28_031100.zip` to close current
handoff items.

## Bridge Pre-Flight (mandatory)

Before touching any UI/runtime code for a visual key, the agent **must** run the
Design-System Translation Bridge pre-flight. This is not optional and precedes
the capture/compare flow below. Skipping it (a "blind pixel fix") is a protocol
violation.

For the current visual key, in order:

1. Read `docs/BRIDGE_USAGE_FOR_AGENTS.md` (how to resolve a check via the bridge).
2. Consult the equivalence matrix `docs/CSS_TO_PYQT_EQUIVALENCE_MATRIX.md`
   (canonical selector/pattern → token/helper/widget → affected keys).
3. Consult the component catalog `docs/VISUAL_COMPONENT_CATALOG.md` (which `NM*`/
   `V3*` component and `shared.theme` token to reuse — never invent QSS).
4. Review `docs/QT_HTML_KNOWN_MISMATCHES.md` to classify the divergence as
   IRREDUCIBLE (Qt ceiling — not closable by changing that aspect), WORKAROUND
   (use the correct painter/helper), or DECISIÓN-OWNER (do not "correct").
5. Use Graphify if available to navigate the chain end to end:

   ```text
   canonical selector/pattern
   → bridge entry (matrix)
   → PyQt component actual/propuesto (catalog)
   → shared.theme tokens
   → runtime file/screen (app/ | hub/)
   → tests/probes (qa/)
   → visual key (handoff)
   ```

   ```powershell
   & "$env:USERPROFILE\.local\bin\graphify.exe" update .
   & "$env:USERPROFILE\.local\bin\graphify.exe" explain "<screen or component>"
   ```

   If Graphify is **not** available, report that explicitly and continue with the
   bridge docs. Never fabricate graph output.

### The bridge does NOT change the closure bar

- The bridge **does not replace** the comparator (`qa/layered_visual_compare.py`).
- The bridge **does not** allow threshold-only closure (the Comparator Command
  Lock still applies; no `--min-ssim`, `--no-odiff`, etc. as closure evidence).
- The bridge **does not** allow skipping any anti-fraud control.
- The bridge **does not** authorize overlays, blits, or loading any canonical /
  reference / mockup artifact into product/runtime, nor any comparison hack.
- Closure still requires the exact key `PASS`, real product/UI evidence, and a
  clean anti-fraud scan, per the rest of this protocol.

## Required Flow

0. Run Graphify before manual code exploration in every active visual repair flow:

   ```powershell
   graphify . --update
   ```

   If the shell environment exposes Graphify as a slash command instead, use:

   ```text
   /graphify . --update
   ```

   Consult the generated graph before opening product code by hand.

1. Regenerate runtime captures before a broad visual decision or final regression:

   ```powershell
   .\.venv\Scripts\python.exe qa\capture_v8.py --all --clean --out-dir qa\_captures_v8
   ```

2. Compare active folders:

   ```powershell
   .\.venv\Scripts\python.exe qa\layered_visual_compare.py `
     --canonical qa\_mockup_canonical `
     --actual qa\_captures_v8 `
     --out-dir reports\qa\layered_visual_compare_fresh
   ```

3. Inspect the side-by-side panel for each item before editing or closing it.

## Canonical HTML / Mockup Parity Harness

Use this harness whenever a change touches the canonical HTML, the canonical
capture recipe, generated canonical PNGs, or the checklist seed/baseline that is
used to decide which surfaces are `PASS` or `FAIL`. It coexists with the runtime
visual gates below; it does not replace `capture_v8.py`, `layered_visual_compare.py`,
anti-fraud, or VAS.

Canonical command:

```powershell
.\.venv\Scripts\python.exe tools\qa\audit_mockup_parity_baseline.py
```

Outputs are written under `reports\qa\mockup_parity_baseline\<timestamp>\`:

- `AUDIT.json`
- `AUDIT.csv`
- `AUDIT.md`
- `TEXT_DIFF_NORMALIZED.patch`
- `EOL_DELTA.txt`

PASS means all of the following are true:

- The full official recipe produced every expected capture, including modal and
  actioned-modal captures.
- `AUDIT.json` has `summary.fail == 0`.
- The report shows explicit `PASS` / `FAIL` / `EXPECTED_DELTA` rows.
- CRLF/LF-only changes are reported as `EOL-only delta` and are not confused
  with normalized textual deltas.

FAIL means any row exceeds the dynamic baseline after automatic statistical
escalation, the recipe does not produce the complete capture set, or the script
exits non-zero. A FAIL blocks canonical baseline/checklist refresh until fixed
and rerun. If a visual change is expected, it must appear as `EXPECTED_DELTA`
inside an audit that still exits PASS.

The auditor measures renderer noise by rendering original A/B, then measures
the real delta by rendering original/modified. If a capture has high renderer,
SVG, ring, or modal variance, it automatically escalates to a statistical
baseline before failing. This is a baseline/mockup integrity gate only: do not
use it to close a runtime visual item without the required runtime evidence.

## Runtime Scope / Noise Envelope Hardening

These gates are complementary no-regression hardening only. They do not replace
`qa/layered_visual_compare.py`, `qa/capture_v8.py`,
`tools/qa/audit_modal_backdrop_blur.py`, `qa/vas_gate.py`,
`qa/anti_fraud_scan.py`, or exact-key closure evidence. They never close the
handoff checklist by themselves.

Use them to keep scope disciplined, detect renderer-noise instability, catch
unexpected runtime deltas outside an allowlist, and compare direct-entry states
against internally navigated states.

Available auxiliary commands:

```powershell
.\.venv\Scripts\python.exe tools\qa\audit_diff_confinement.py `
  --base HEAD~1 `
  --allow-path qa `
  --allow-path tools\qa `
  --allow-path tests `
  --allow-path VISUAL_QA_AGENT_PROTOCOL.md `
  --allow-path VISUAL_REPAIR_HANDOFF.md

.\.venv\Scripts\python.exe qa\runtime_noise_envelope.py `
  --baseline-dir reports\qa\runtime_baseline_a `
  --baseline-dir reports\qa\runtime_baseline_b `
  --modified-dir reports\qa\runtime_current `
  --expected-delta-key "suite:dbt-practice-wise-mind@light"

.\.venv\Scripts\python.exe qa\runtime_internal_nav_parity.py `
  --case-file reports\qa\nav_parity_cases.json

.\qa\run_visual_scope_regression.ps1 -PlanFile .\reports\qa\visual_family_keys.csv
```

Runtime noise rule:

- `delta_best` is diagnostic only and never closes runtime.
- Strong pass requires `delta_median <= noise_worst + margen minimo`.
- If only `delta_best` fits the envelope, the result is `REVIEW_NOISE`, not PASS.
- `REVIEW_NOISE` and `NOISE_WARNING` are not strong PASS states.
- Shape mismatch is a hard fail unless the exact key is explicitly allowlisted
  as `EXPECTED_DELTA`.
- Keys outside the expected-delta allowlist that exceed the envelope are FAIL.

Internal navigation parity currently compares captured images and metadata
without touching product code. If real PyQt route probes need deeper hooks, add
them in QA harness code only; do not fake PASS and do not modify `app/`, `hub/`,
or `shared/` to satisfy this auxiliary gate.

Any modal, VAS, anti-fraud, layout, capture-validity, or active comparator FAIL
still blocks closure. If the canonical HTML, capture recipe, canonical PNGs, or
checklist seed/baseline changes, `tools/qa/audit_mockup_parity_baseline.py`
remains mandatory. DBT v2 canon means 116 captures with 16 formal DBT practice
modal surfaces; hardening must respect that baseline. Snapshots under
`reports/qa/mockup_parity_baseline/.../sources/` are not canonical sources.

## Resource-Safe Validation

Microfix de una pantalla:

- Nunca usar `capture_v8.py --all --clean` por defecto.
- Usar `capture_v8.py --app ... --view ... --theme ... --out-dir qa\_captures_v8 --no-clean`.
- Luego correr `layered_visual_compare.py` con filtro de key/app/view/theme para validar solo la superficie relevante.
- El reporte puede ser `REPORT_SCOPE: PARTIAL` y sirve como evidencia individual si `REPORT_EVIDENCE_VALID: YES` y la exact key esta en `PASS`.

Familia chica:

- Capturar solo las vistas/temas afectados, repitiendo comandos puntuales con `--no-clean`.
- Usar comparator filtrado por `--keys-file` o filtros equivalentes.
- No correr `--all` salvo que la familia toque una base compartida amplia.

Cambio transversal grande:

- Si toca `theme`, `chrome`, `NMCard`, layout shell, tokens, navegacion base, helpers de captura compartidos o componentes globales, ahi si corresponde una regresion amplia con `capture_v8.py --all --clean`.

Regresion final:

- Solo para cierre global o verificacion amplia.
- Usar `capture_v8.py --all --clean` + comparator full.
- If the regression also changes the canonical HTML, capture recipe, canonical
  PNGs, or checklist seed/baseline, run the canonical HTML/mockup parity harness
  above and record its `AUDIT.md` path.

Disciplina de recursos:

- No correr varios harnesses pesados en simultaneo.
- No correr `capture_v8 --all`, `runtime_live_probe --all`, E2E completo y comparator full al mismo tiempo.
- En agentes baratos/Hermes Desktop, usar una sola validacion pesada por vez.
- Para microfix, preferir validacion puntual, no matriz completa.
- `REPORT_SCOPE: PARTIAL` nunca puede habilitar `HANDOFF_CLOSURE_ALLOWED: YES`.
- `REPORT_SCOPE: PARTIAL` si puede servir para cerrar un checkbox individual si la exact key esta en `PASS` y `REPORT_EVIDENCE_VALID: YES`.
- `REPORT_SCOPE: FULL` es requerido para cierre global del handoff.

Ejemplos seguros:

Microfix pantalla exacta:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py `
  --app suite `
  --view dbt-practice-wise-mind `
  --theme light `
  --out-dir qa\_captures_v8 `
  --no-clean

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_item `
  --key "suite:dbt-practice-wise-mind@light"
```

Familia chica:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view timer-running --theme light --out-dir qa\_captures_v8 --no-clean
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view timer-paused  --theme light --out-dir qa\_captures_v8 --no-clean

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_family `
  --keys-file reports\qa\visual_family_keys.txt
```

Runtime probe puntual:

```powershell
.\.venv\Scripts\python.exe qa\runtime_live_probe.py `
  --app suite `
  --view timer `
  --theme light `
  --mode offscreen
```

E2E puntual:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\e2e\suite\test_e2e_s07_timer.py -q
```

E2E smoke:

```powershell
.\scripts\e2e\run-e2e-smoke.ps1
```

Regresion final completa:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py --all --clean --out-dir qa\_captures_v8

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_fresh
```

## Forbidden Closure Reasons

Do not mark an item complete because of:

- `STALE`.
- `fidelity PASS`.
- `diff_fidelity.py` PASS.
- `capture_v8.py` success, total, or manifest status.
- A single filtered recapture when the item belongs to a broad handoff reset.
- Any zip-based comparison.
- Any report whose manifest says `technical_capture_only`,
  `REVIEW_INCOMPLETE`, or `REPORT_EVIDENCE_VALID: NO`.
- `audit_mockup_parity_baseline.py` PASS by itself. That auditor validates
  canonical HTML/mockup parity only; runtime closure still requires the active
  comparator, anti-fraud, and VAS gates.
- `HANDOFF_CLOSURE_ALLOWED: NO` by itself does **not** invalidate a report for closing an individual checkbox. It means the global handoff is not complete because the report is partial or other keys still have divergences. Individual closure requires `REPORT_EVIDENCE_VALID: YES` and the exact key status `PASS`.
- Owner acceptance, human review, or "looks good enough".
- Acceptable residue, partial progress, or "mostly fixed".
- Blocked / too hard / won’t fix as a closure reason.
- Degrading or reclassifying the item to a lower severity to skip it.
- Any claim that the divergence is "minor", "cosmetic", or "acceptable" without a `PASS` from the comparator.

## Operational Discipline

The checklist is a sequential queue, not a global audit. Rules:

1. If the current item is still `FAIL`, the next action is to repair that same item.
2. You may not ask the owner for a decision to skip or accept the item.
3. You may not jump to the next item while the current one remains `FAIL`.
4. You may not close, downgrade, or reclassify an item because it is difficult.
5. The only way to advance the queue is a `PASS` from the active layered comparator (`qa/layered_visual_compare.py`).

## Current Item Definition

- `current item` = the first unchecked `[ ]` checkbox in this document, read strictly from top to bottom.
- If the handoff or owner explicitly pins an active visual family sprint, `current item` means the first unchecked `[ ]` checkbox inside that pinned family order.
- Family-equivalent work is allowed only when the shared repair does not complicate individual closure.
- Closure remains sequential by exact key: the active key must be `PASS` before its checkbox changes, and each exact-key `PASS` requires one closure commit followed by an immediate push.
- After that push, the agent may continue to the next open key only inside the same visual family, or an explicitly equivalent surface covered by the same mapping/evidence flow.
- Stop and report before switching to another visual family or to a non-equivalent check.

## Comparator Command Lock

Valid comparator closure evidence must use the active comparator command documented in Required Flow or Resource-Safe Validation. Full reports are required for global handoff closure; filtered `REPORT_SCOPE: PARTIAL` reports are valid only for individual checkbox evidence. Any report generated with the following overrides is **exploratory only** and **not valid** as closure evidence:

- `--raw-changed-threshold`
- `--raw-mad-threshold`
- `--min-ssim`
- `--max-odiff-diff-pct`
- `--max-bbox-shift-px`
- `--no-odiff`
- `--no-panels`

Do not use threshold overrides, disabled odiff, or disabled panels to close a checklist item.

## Anti-Fraud Rule

A `PASS` must come from real changes in the product or UI. It is strictly forbidden to modify any of the following in order to make a visual divergence pass:

- QA scripts, tests, or assertions
- Comparators, thresholds, or scoring logic
- Capture scripts, canonical images, or fixtures
- Reports, manifests, or baselines

If a divergence is fixed, the fix must be in the actual product code, styles, or assets. Any attempt to game the comparator is a protocol violation.

### No canonical/reference artifacts in product or runtime

Product or runtime code may **never** read, render, mount, copy, blit, or
overlay any canonical / reference / mockup artifact (e.g. anything under
`qa/_mockup_canonical/`, `qa/pack canonico/`, the canonical HTML, or any
reference image/fixture) in order to pass — or appear to pass — a visual
comparison. The runtime must render only its own real UI. A capture that
shows a reference artifact instead of a genuine render is fraudulent.

If any closure depends, directly or indirectly, on such canonical/reference
injection into the product or runtime, that closure is automatically
**invalid** and the affected checklist item(s) must be **reopened** and
re-validated with a real render. This applies retroactively to already-closed
items.

## Gate Hardening (mandatory)

These mechanisms harden the visual gate. They do NOT change the closure bar —
the comparator thresholds are unchanged.

### Mandatory static anti-fraud scan

`qa/anti_fraud_scan.py` statically scans `app/`, `hub/`, `shared/` and fails if
runtime/product code reads, renders, copies, mounts or overlays any
canonical / reference / mockup / QA-report artifact. It is wired into the
resource-safe wrappers (`qa/run_visual_item.ps1`, `qa/run_visual_family.ps1`,
`qa/run_visual_full.ps1`) and runs BEFORE capture/compare. If the scan fails the
run aborts and **no report it would have produced is valid closure evidence,
even if the comparator reports `PASS`**. Run standalone with
`.\.venv\Scripts\python.exe qa\anti_fraud_scan.py`. It does not ban `QPixmap`
globally — only its use with QA/reference artifacts.

### Suspicious perfect match

The comparator flags any result that is pixel-identical to the canonical
(`ssim=1.0`, `mad=0.0`, `changed=0`) on a non-trivial surface as
`status=SUSPICIOUS_PERFECT_MATCH` with `suspicious_perfect_match: true`. This is
physically implausible for genuine Qt-vs-Chromium rendering and is the signature
of reference-artifact injection. It counts as a real divergence and **blocks
closure pending audit** — it can never be closure evidence. The only exception
is trivial surfaces, by an explicit, tested rule: empty-state views (name ends
`-empty`) and flat / near-constant canonicals (grayscale std < 2.0).

### Density-aware gate (text-dense surfaces)

Two layers are density-aware. Sparse, high-contrast surfaces keep the strict bars
(`ssim >= 0.92`, `changed_pixel_ratio <= 0.08`). Text-dense, low-contrast
surfaces — canonical grayscale std `< 35.0` (e.g. the 520x600 Acceso/registro
forms) — instead use:

- **windowed SSIM `>= 0.65`** (standard Wang et al. metric) instead of global
  `ssim >= 0.92`, because global single-window SSIM has a measured ~0.55 hard
  floor on these surfaces (Qt-vs-Chromium text rasterisation). The 0.65 floor
  sits below every genuine family render measured (windowed 0.69-0.78) and above
  a wrong-screen render (~0.58).
- **`changed_pixel_ratio <= 0.10`** instead of 0.08, because ~0.077 of the
  changed pixels on these surfaces are irreducible text-edge anti-aliasing. The
  0.10 bar sits above that AA floor and BELOW the current recovery render
  (0.118), so it never closes a surface by threshold alone — the current render
  still FAILs and real flat-region fixes are still required.

This changes ONLY those two thresholds for low-std surfaces. `mean_abs_diff`,
bbox/layout, region and odiff stay at full strength for every surface; canonical
images and the anti-fraud controls (static scan + SUSPICIOUS_PERFECT_MATCH) are
unchanged. Localized/structural divergence is still caught by
`max_largest_region_ratio`, odiff, bbox/layout and changed_ratio above 0.10.

### Gate calibration is non-closure

`qa/visual_gate_calibration.py` writes technical evidence to
`reports/qa/visual_gate_calibration/` (SSIM, MAD, changed, bbox, best
small-shift SSIM, density, and the estimated ceiling by alignment/colour). It is
**not a gate**: it never closes, reclassifies or skips an item and never
modifies thresholds. Use it to characterise the gate, not to justify a closure.

### Mandatory push

After every closed checkbox, or any anti-fraud cleanup commit, push to the
remote immediately. A local-only fraud removal or closure is not done until it
is pushed.

The closure cadence is: one exact-key `PASS` = one commit + immediate push.

## Item Closure Evidence

An item can be changed from `[ ]` to `[x]` only when **all** of the following
technical gates pass. There is no subjective or manual closure path — inspection,
"looks good", or panel review are **not** evidence of closure.

### PASS requirements (all mandatory)

1. Anti-fraud scan: `CLEAN`.
2. Fresh capture with `NM_VAS_INTROSPECT=1` for that exact surface or family.
3. Fresh `qa/layered_visual_compare.py` report with `REPORT_EVIDENCE_VALID: YES`.
4. Exact key status is `PASS` only.
5. VAS Gate (`qa/vas_gate.py`) passes: sidecar
   `qa/_visual_auditor_spec/introspection.json` exists, contains the exact key,
   `fail_count=0`, and zero divergences of severity `high` or `medium`.
6. Modal keys must have `modal_capture_scope=window_overlay`,
   `backdrop_observable=true`, a `back_screen_key`, and
   `tools/qa/audit_modal_backdrop_blur.py --key "<exact-key>"` PASS. A
   `panel_crop` can validate internal layout only; it never closes modal
   backdrop/blur/centering.
7. If the item, harness, or checklist update changes canonical HTML, the
   canonical capture recipe, canonical PNGs, or the baseline/checklist seed,
   `tools/qa/audit_mockup_parity_baseline.py` must also PASS.

The closure note must record:

- Fix commit hash.
- Capture command used (must include `NM_VAS_INTROSPECT=1`).
- Comparator report path.
- `REPORT_EVIDENCE_VALID: YES` + exact key `PASS`.
- `qa/vas_gate.py` exit code `0`.
- For modal keys, modal backdrop audit report path and PASS summary.
- When applicable, mockup parity `AUDIT.md` path and PASS/FAIL summary.

`HANDOFF_CLOSURE_ALLOWED: NO` is acceptable for individual closure if the reason
is `partial_scope` or that other keys remain `FAIL`; the deciding factor is the
exact key `PASS` in a valid report plus a passing VAS Gate. The comparator may
exit non-zero while other items remain `FAIL`; for individual closure, read the
exact key status in the JSON/MD report, not the global exit code.

If any gate fails or evidence is missing, leave the checkbox open and add a note.

## Collateral PASS Handling

- If a real product/UI fix applied for the current item makes other pending checkboxes pass, that is allowed and expected.
- You may not jump to work another item before the current item passes.
- After closing the current item, continue reading the checklist in order.
- Inside an active family, you may continue after the push to the next open equivalent family member; before leaving that family, stop and report.
- When you reach a later item that is already `PASS` from the same commit/official report, you may mark it closed with the same evidence, citing the commit and the exact key `PASS`.
- If a shared fix worsens any previously closed key, that is a regression and must be fixed before proceeding.
