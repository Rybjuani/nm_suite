# Visual QA Agent Protocol

This file is the active protocol for visual parity work. Read it before editing
`VISUAL_REPAIR_HANDOFF.md`.

## Active Sources

- Canonical source of truth: `qa/_mockup_canonical/`.
- Runtime source of truth: fresh full captures in `qa/_captures_v8/`.
- Canonical HTML source: `qa/pack canonico/neuromood-mockup_reparado.html`.
- Operational comparator: `qa/layered_visual_compare.py`.

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
  --view dbt-practice-stop `
  --theme light `
  --out-dir qa\_captures_v8 `
  --no-clean

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_item `
  --key "suite:dbt-practice-stop@light"
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

### VAS resource-safe capture (mandatory for every closure)

Every capture used for closure must set `NM_VAS_INTROSPECT=1`.

Before every closure capture, remove stale VAS sidecar:

```powershell
Remove-Item .\qa\_visual_auditor_spec\introspection.json -ErrorAction SilentlyContinue
```

The closure evidence must use the last VAS entry for the exact key generated by
the current run. A stale/pre-existing `introspection.json` entry is not valid
closure evidence.

Microfix exact screen:

```powershell
$env:NM_VAS_INTROSPECT=1
.\.venv\Scripts\python.exe qa\capture_v8.py `
  --app suite `
  --view dbt-practice-stop `
  --theme light `
  --out-dir qa\_captures_v8 `
  --no-clean
```

Small family:

```powershell
$env:NM_VAS_INTROSPECT=1
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view timer-running --theme light --out-dir qa\_captures_v8 --no-clean
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view timer-paused  --theme light --out-dir qa\_captures_v8 --no-clean
```

Prohibited: `capture_v8.py --all` for microfix or single-item closure. `--all`
is only allowed for final global regression or broad shared-base changes.

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

### VAS semantic gate (mandatory)

`qa/vas_introspect.py` inspects semantic contracts and geometry via Qt
introspection. Every exact-key closure requires a VAS pass in addition to the
layered comparator.

Requirements:
- Capture with `NM_VAS_INTROSPECT=1`.
- Sidecar `qa/_visual_auditor_spec/introspection.json` must exist.
- The exact key must have an entry in `introspection.json`.
- `fail_count` must be `0`.
- Zero divergences of severity `high` or `medium`.
- If VAS reports `GEOMETRY_*`, `RADIUS_MISSING`, `SHADOW_MISSING`, or any
  semantic contract failure, the key is **not closable** even if the layered
  comparator reports `PASS`.

The layered comparator remains the primary visual gate. VAS is a mandatory
additional semantic gate. `size_review` is informational unless this document
states otherwise; `divergences` blocks.

### Mandatory push

After every closed checkbox, or any anti-fraud cleanup commit, push to the
remote immediately. A local-only fraud removal or closure is not done until it
is pushed.

The closure cadence is: one exact-key `PASS` = one commit + immediate push.

## Item Closure Evidence

An item can be changed from `[ ]` to `[x]` only when the note includes:

- Fix commit hash.
- Fresh `qa/_captures_v8` capture command used for that exact surface or family.
- Fresh `qa/layered_visual_compare.py` report path.
- The report must show `REPORT_EVIDENCE_VALID: YES`.
- The exact key status is `PASS` only.
- `HANDOFF_CLOSURE_ALLOWED: NO` is acceptable for individual closure if the reason is `partial_scope` or that other keys remain `FAIL`; the deciding factor is the exact key `PASS` in a valid report.
- The comparator may exit non-zero while other items remain `FAIL`; for individual closure, read the exact key status in the JSON/MD report, not the global exit code.
- One short manual side-by-side confirmation.
- VAS sidecar `qa/_visual_auditor_spec/introspection.json` must exist, contain
  the exact key, `fail_count=0`, and zero high/medium divergences.
- The VAS entry must be from the current run; a stale/pre-existing
  `introspection.json` entry is not valid closure evidence.

If any evidence is missing, leave the checkbox open and add a note.

## Collateral PASS Handling

- If a real product/UI fix applied for the current item makes other pending checkboxes pass, that is allowed and expected.
- You may not jump to work another item before the current item passes.
- After closing the current item, continue reading the checklist in order.
- Inside an active family, you may continue after the push to the next open equivalent family member; before leaving that family, stop and report.
- When you reach a later item that is already `PASS` from the same commit/official report, you may mark it closed with the same evidence, citing the commit and the exact key `PASS`.
- If a shared fix worsens any previously closed key, that is a regression and must be fixed before proceeding.
