# Visual Auditor V2

## Purpose

Convert mockup↔capture comparisons into structured, navigable, prioritized visual
evidence. Reuses existing stack (`capture_v8.py`, `diff_fidelity.py`,
`mockup_reference_static/manifest.json`). Replaces heuristic classification with
VLM-driven analysis.

## Architecture

```
qa/mockup_reference_static/manifest.json ← canónico, no se toca
     ↓
qa/capture_v8.py --all ← existe, no se toca
     ↓
qa/_captures_v8/CAPTURE_MANIFEST.json
     ↓
qa/diff_fidelity.py ← existe, no se toca
     ↓
qa/_fidelity_current/FIDELITY_REPORT.json
     ↓
qa/visual_auditor_v2.py analyze --all ← NUEVO
```

### Pipeline steps

1. **Pairing** — reads `manifest.json` and matches each item to a capture file
   via `(app, screen_id, state_id, theme)` → filename convention.
2. **Diff + BBoxes** — `scipy.ndimage.label` extracts connected diff regions,
   produces `diff.png` (side-by-side) and `overlay.png` (bboxes drawn).
3. **Crops** — per-bbox crops of mockup, real, and diff for close inspection.
4. **Classification** — VLM (GLM-4V or configurable backend) receives the bundle
   (mockup + real + diff + overlay + metrics context) and returns structured JSON.
5. **Cache** — per `(mockup_sha256, capture_sha256)` to avoid reclassifying
   unchanged images.
6. **Outputs** — `index.html`, `report.json`, `queue.md`, per-surface
   `metrics.json` + `classification.json` + `agent_package.json`.

## Commands

```powershell
# Analyze all surfaces
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all

# Analyze one surface
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --surface suite:rutina-empty:default@light

# Offline mode (no VLM, everything NEEDS_HUMAN_REVIEW)
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py analyze --all --no-vlm

# Export prioritized queue
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py queue

# Clear classification cache
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py clear-cache

# Validate environment
.\.venv\Scripts\python.exe qa\visual_auditor_v2.py doctor
```

## Environment

- `NM_VLM_BACKEND` — if set, enables VLM calls. If unset, classification
  degrades gracefully to `NEEDS_HUMAN_REVIEW`.
- The VLM client attempts to import `z_ai_web_dev_sdk` (GLM-4V). Other backends
  can be wired in by patching `_call_vlm`.

## Output structure

```
qa/_visual_auditor_v2/latest/
  index.html
  report.json
  queue.md
  surfaces/
    <surface_key>/
      mockup.png
      real.png
      diff.png
      overlay.png
      metrics.json
      classification.json
      agent_package.json
      crops/
        bbox_0/
          mockup.png
          real.png
          diff.png
        bbox_1/ ...
```

## Taxonomy

### Labels (closed set)

- `LAYOUT_SHIFT`
- `SIZE_MISMATCH`
- `SPACING_MISMATCH`
- `COLOR_MISMATCH`
- `TEXT_MISMATCH`
- `MISSING_COMPONENT`
- `EXTRA_COMPONENT`
- `CHROME_MISMATCH`
- `RENDER_NOISE`
- `PAIRING_OR_CAPTURE_MISMATCH`
- `NEEDS_HUMAN_REVIEW`

### Recommendations (closed set)

- `PRODUCT_FIX_CANDIDATE`
- `FIXTURE_FIX_CANDIDATE`
- `PAIRING_OR_CAPTURE_FIX_CANDIDATE`
- `LIKELY_RENDER_NOISE`
- `NEEDS_HUMAN_REVIEW`

## Agent package (`agent_package.json`)

Designed for agents without vision. Contains:

- `decision` — `FIX_PRODUCT`, `FIX_FIXTURE`, `FIX_PAIRING`, `SKIP_RENDER_NOISE`, `NEEDS_HUMAN_REVIEW`
- `suspected_module` — file path guess from VLM
- `evidence_summary` — textual description of what changed
- `confidence` — `high`, `medium`, `low`
- `what_to_check_first` — next step suggestion
- `do_not_touch_if` — guardrail rule

## Guardrails

- If `confidence == 'low'`, `decision` is forced to `NEEDS_HUMAN_REVIEW`.
- pHash distance is reported as auxiliary metric but **never** used as sole
  severity criterion.
- No heuristic numpy classification (no edge density, text density, color delta).
- `--no-vlm` produces `NEEDS_HUMAN_REVIEW` for all surfaces; no invented labels.

## Limitations

- VLM accuracy is not perfect. Some classifications will be wrong. Confidence is
  reported explicitly and the low-confidence rule is enforced.
- VLM cannot validate states that require real persisted data or network
  interaction. Those still need manual validation.
- Cache can theoretically go stale if images change but SHA-256 collisions occur
  (extremely rare). `clear-cache` resolves this.

## Git hygiene

`qa/_visual_auditor_v2/` is in `.gitignore`. Do not commit generated outputs.
Commit only `qa/visual_auditor_v2.py`, `tests/test_visual_auditor_v2.py`, and
`docs/VISUAL_AUDITOR_V2.md`.

## What V2 does NOT do (lessons from Sentinel)

- No hardcoded semantic regions (header/sidebar/content/cards/modal/CTA/bottom/right/form).
- No heuristics of "text density delta" / "edge density delta" / "color delta global".
- No 7-dimension heuristic scoring queue.
- No crawler (reuses `capture_v8.py`).
- No global diff (reuses `diff_fidelity.py`).
- No manifest reconstruction (reads canonical `manifest.json`).
- No auto-approval. If VLM is unavailable, everything is `NEEDS_HUMAN_REVIEW`.
- No blind microfixes. Low confidence means no fix recommendation.
