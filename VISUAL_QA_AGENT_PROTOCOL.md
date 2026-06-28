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
- There is no discretionary selection of the next item.
- You may not skip to a dark/light pair, family member, or related surface until the `current item` is `PASS`, unless the handoff note for that same item explicitly directs you to do so.

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

If any evidence is missing, leave the checkbox open and add a note.

## Collateral PASS Handling

- If a real product/UI fix applied for the current item makes other pending checkboxes pass, that is allowed and expected.
- You may not jump to work another item before the current item passes.
- After closing the current item, continue reading the checklist in order.
- When you reach a later item that is already `PASS` from the same commit/official report, you may mark it closed with the same evidence, citing the commit and the exact key `PASS`.
- If a shared fix worsens any previously closed key, that is a regression and must be fixed before proceeding.
