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

1. Regenerate runtime captures before a broad visual decision:

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
- `HANDOFF_CLOSURE_ALLOWED: NO` by itself does **not** invalidate a report for closing an individual checkbox. It only means the global handoff is not yet complete because other keys still have divergences. Individual closure requires `REPORT_EVIDENCE_VALID: YES` and the exact key status `PASS`.
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

The only valid comparator command for closure evidence is the fixed command documented in the Required Flow section. Any report generated with the following overrides is **exploratory only** and **not valid** as closure evidence:

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

## Item Closure Evidence

An item can be changed from `[ ]` to `[x]` only when the note includes:

- Fix commit hash.
- Fresh `qa/_captures_v8` capture command used for that exact surface or family.
- Fresh `qa/layered_visual_compare.py` report path.
- The report must show `REPORT_EVIDENCE_VALID: YES`.
- The exact key status is `PASS` only.
- `HANDOFF_CLOSURE_ALLOWED: NO` is acceptable for individual closure if the only reason is that other keys remain `FAIL`; the deciding factor is the exact key `PASS` in a valid report.
- The comparator may exit non-zero while other items remain `FAIL`; for individual closure, read the exact key status in the JSON/MD report, not the global exit code.
- One short manual side-by-side confirmation.

If any evidence is missing, leave the checkbox open and add a note.

## Collateral PASS Handling

- If a real product/UI fix applied for the current item makes other pending checkboxes pass, that is allowed and expected.
- You may not jump to work another item before the current item passes.
- After closing the current item, continue reading the checklist in order.
- When you reach a later item that is already `PASS` from the same commit/official report, you may mark it closed with the same evidence, citing the commit and the exact key `PASS`.
- If a shared fix worsens any previously closed key, that is a regression and must be fixed before proceeding.
