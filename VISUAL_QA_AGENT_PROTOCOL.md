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
  `REVIEW_INCOMPLETE`, or `HANDOFF_CLOSURE_ALLOWED: NO`.

## Item Closure Evidence

An item can be changed from `[ ]` to `[x]` only when the note includes:

- Fix commit hash.
- Fresh `qa/_captures_v8` capture command used for that exact surface or family.
- Fresh `qa/layered_visual_compare.py` report path.
- The exact key status is `PASS`, or a remaining divergence is explicitly
  accepted by the owner.
- One short manual side-by-side confirmation.

If any evidence is missing, leave the checkbox open and add a note.
