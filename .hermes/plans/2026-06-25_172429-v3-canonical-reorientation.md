# V3 Canonical Reorientation — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. Subagentes coordinan: diagnosis (1) → evidence design (1) → implementation (1-2) → batch mode + audit (1).

**Goal:** Make V3 the canonical source of visual truth for the repo. Eliminate the AUDITOR_IMPROVEMENT_ACTIONABLE mass bucket (currently 67/86, inoperancia con otro nombre) by routing each surface to a concrete, executable agent action — or to `NO_ACTION_NEEDED_WITH_EVIDENCE` when the auditor's internal decision is `RENDER_NOISE_OK` with SSIM ~1.0. Reach 86/86 actionable or explicitly no-actionable, 0 owner review, 0 generic bucket, 0 PRODUCT_ACTIONABLE on weak evidence.

**Architecture:** Decouple the auditor's internal `decision` (RENDER_NOISE_OK / FIX_PRODUCT_REVIEW / PAIRING_FIX) from the agent-route. The auditor's decision IS the actionable verdict; the route is just the dispatch. Keep the existing OCR/bbox/color/structural signals as evidence layers, but stop using them to OVERRIDE the internal decision. Add a per-surface actionable evidence package: divergence list per screen, probable module/component, probable root cause (clustered), real visual signals, next concrete action for the agent.

**Tech Stack:** Python 3.12, pyproject.toml (existing), pytest, ruff. Pure stdlib + the existing VLM/Kimi backend (already wired, ~30% timeout — used only on demand).

---

## Diagnostic findings (root cause of the 67/86 mass bucket)

Cross-tab of `decision` (auditor internal) × `agent_route` (current output):

| decision            | agent_route                      | count |
|---------------------|----------------------------------|-------|
| RENDER_NOISE_OK     | AUDITOR_IMPROVEMENT_ACTIONABLE   | 55    |
| FIX_PRODUCT_REVIEW  | QA_TOOLING_ACTIONABLE            | 16    |
| FIX_PRODUCT_REVIEW  | AUDITOR_IMPROVEMENT_ACTIONABLE   | 12    |
| PAIRING_FIX         | CAPTURE_OR_PAIRING_ACTIONABLE    | 2     |
| FIX_PRODUCT_REVIEW  | PRODUCT_ACTIONABLE               | 1     |

- **55/86 (64%)** of the entire base has `decision: RENDER_NOISE_OK` (the auditor's internal verdict: SSIM ~1.0, no bug). But because `largest_bbox_dominates=True` (median 0.928, mean 0.564, 40/67 above 0.50), they get routed to AUDITOR. **The auditor says "no bug"; the route contradicts that.** Fix: when `decision=RENDER_NOISE_OK` and SSIM ≥ 0.95 and changed_pixel_ratio < 0.05, route to `NO_ACTION_NEEDED_WITH_EVIDENCE` with the metrics as evidence.
- **12 surfaces** in AUDITOR bucket have `decision=FIX_PRODUCT_REVIEW` + `text_mismatch=True`. The current guardrail rejects them because `_looks_like_real_text_pair` fails on the `fuzzy_ratio_worst_pair` (sub-bbox granularity). After the previous amend (commit ed05efa) this is correct behavior — they should NOT be `PRODUCT_ACTIONABLE`. But they ARE bugs. **Fix**: route to `QA_TOOLING_ACTIONABLE` with concrete text-evidence package, not AUDITOR.
- **56/67** surfaces in AUDITOR bucket already have a non-empty `fuzzy_ratio_worst_pair`. The evidence is there — the dispatch is wrong.

**Conclusion**: the AUDITOR bucket is over-used. RENDER_NOISE_OK verdicts need their own dispatch (no-action). FIX_PRODUCT_REVIEW verdicts need concrete text/color/structural evidence packages, even when the OCR pair is partial — they go to QA_TOOLING, not AUDITOR.

---

## Files

- Modify: `qa/visual_auditor_v3.py` (routing + evidence packaging)
- Modify: `tests/test_visual_auditor_v3.py` (guardrails + distribution)
- Create: `qa/_visual_auditor_v3/cli_batch.py` (batch mode + resume + log file)
- Modify: `qa/visual_auditor_v3.py` (CLI: --quiet --resume --log-file flags on `analyze`)
- Create: `qa/_visual_auditor_v3/progress.json` schema (under .hermes, not tracked)

---

## Step-by-step plan

### Task 1: Add per-surface actionable evidence package

**Objective:** Every surface (no matter the route) emits a structured `actionable_evidence` block with: divergences[], probable_module, probable_root_cause_cluster, real_visual_signals, next_action_for_agent. This is the audit-grade payload an agent consumes.

**Files:**
- Modify: `qa/visual_auditor_v3.py:1660-1850` (`_build_agent_package`)

**Step 1:** Add a `ActionableEvidence` dataclass after `ColorEvidence`:

```python
@dataclass
class ActionableEvidence:
    divergences: list[str] = field(default_factory=list)        # e.g. ["text: 'Recuperar' vs 'Recuperar-Acceso'"]
    probable_module: str = ""                                    # e.g. "suite.login_form" (heuristic from surface_key)
    probable_root_cause: str = ""                                 # clustered: "color_theme_bleed" | "ocr_garbage" | "real_text_mismatch" | "render_noise"
    real_visual_signals: list[str] = field(default_factory=list) # e.g. ["bbox@header (60,40,200,80)", "color Δ=50 RGB(10,10,10)→(200,200,200)"]
    next_action: str = ""                                          # concrete: "Open suite/login_form.py, check font_metrics for 'Recuperar'"
    evidence_strength: str = "weak"                                # "strong" | "medium" | "weak" — independent of route
```

**Step 2:** Add helper `_cluster_root_cause(classification, bbox_analyses, metrics) -> str`. Mapping:
- `decision=RENDER_NOISE_OK` + `changed_pixel_ratio < 0.05` → `"render_noise"` (no bug, theme/scroll/chrome variance)
- `text_mismatch=True` + `_has_real_text_pair(bbox_analyses)` → `"real_text_mismatch"`
- `text_mismatch=True` + not `_has_real_text_pair` → `"ocr_garbage"` (auditor can't read it; agent should improve OCR pipeline or check crop)
- `color_mismatch=True` + not `text_mismatch` → `"color_theme_bleed"` (palette/QSS drift, usually theme-related)
- `missing=True` or `extra=True` → `"structural_component"` (missing/extra element)
- else → `"unknown"` (forces AUDITOR — legitimate unknown, not a default)

**Step 3:** Add helper `_divergences_from(bbox_analyses) -> list[str]` that walks the worst 3 pairs and emits strings like:
- `f"text: '{pair[0]}' vs '{pair[1]}' (fuzzy={fuzzy})"`
- `f"color Δ={delta} at bbox {geometry}"`

**Step 4:** Add helper `_probable_module(surface_key) -> str` from the surface key (e.g. `suite:login@light` → `suite.login`). Heuristic, just split + map.

**Step 5:** Add helper `_next_action_for_agent(route, root_cause, divergences) -> str` returning concrete agent instructions. Examples:
- `route=NO_ACTION_NEEDED_WITH_EVIDENCE` → `"No action. V3 verified visual stability."`
- `root_cause=real_text_mismatch` → `"Investigate {module}: {divergences[0]}. Likely font metrics, padding, or truncation. Confirm locally before changing product."`
- `root_cause=ocr_garbage` → `"Improve OCR preprocessing for {module} (upscale, contrast, sharpen crops) before claiming product action. Current OCR is illegible."`
- `root_cause=color_theme_bleed` → `"Inspect QSS/palette for {module}. Verify theme switching does not leak between surfaces."`
- `root_cause=structural_component` → `"Inspect {module} for missing/extra component. Compare against mockup reference."`

**Step 6:** In `_build_agent_package`, after building the existing package, attach `ActionableEvidence` and return it in the dict.

**Step 7:** Test: existing tests must still pass; new tests verify the field is populated.

---

### Task 2: Re-route RENDER_NOISE_OK to NO_ACTION_NEEDED_WITH_EVIDENCE

**Objective:** Stop the 55/86 contradiction where the auditor says "no bug" but the router sends to AUDITOR. When the auditor's internal decision is `RENDER_NOISE_OK` AND there is no contradicting evidence (no `MISSING_COMPONENT`, no `EXTRA_COMPONENT`, no `text_mismatch` from a real pair), the surface is `NO_ACTION_NEEDED_WITH_EVIDENCE`.

**Files:**
- Modify: `qa/visual_auditor_v3.py:_map_to_agent_route` (insert before Case 1)

**Step 1:** Insert a new Case 0 just after the metrics/evidence_quality computation:

```python
# Case 0: Auditor internal decision is RENDER_NOISE_OK and nothing contradicts.
# This is the most common case (55/86 in current run) and the previous
# guardrail wrongly routed them to AUDITOR_IMPROVEMENT_ACTIONABLE because
# largest_bbox_dominates=True. The bbox dominance is expected for theme/
# chrome variance on a screen-sized capture, not a product bug.
if (
    classification.decision == "RENDER_NOISE_OK"
    and metrics.ssim >= 0.95
    and metrics.changed_pixel_ratio < 0.05
    and "MISSING_COMPONENT" not in labels
    and "EXTRA_COMPONENT" not in labels
):
    agent_route = "NO_ACTION_NEEDED_WITH_EVIDENCE"
    agent_next_action = (
        f"V3 verified visual stability. SSIM={metrics.ssim:.3f}, "
        f"changed_pixel_ratio={metrics.changed_pixel_ratio:.4f}, "
        f"largest_bbox_area_ratio={metrics.bbox_largest_area_ratio:.3f} "
        f"(theme/chrome variance, not a bug)."
    )
    why_not_owner_review = (
        "Auditor internal decision is RENDER_NOISE_OK with high SSIM "
        "and no structural labels. No actionable product change."
    )
    return (..., product_action_allowed=False, qa_action_allowed=False, capture_action_allowed=False, ...)
```

**Step 2:** Run analyze --all and confirm the 55 RENDER_NOISE_OK surfaces flip to NO_ACTION_NEEDED_WITH_EVIDENCE.

---

### Task 3: Re-route FIX_PRODUCT_REVIEW-with-evidence to QA_TOOLING with concrete package

**Objective:** The 12 surfaces currently in AUDITOR bucket that have `decision=FIX_PRODUCT_REVIEW` need a real dispatch. They are not `PRODUCT_ACTIONABLE` (OCR is partial) but they ARE potential bugs. Route to `QA_TOOLING_ACTIONABLE` with a concrete actionable_evidence package.

**Files:**
- Modify: `qa/visual_auditor_v3.py:_map_to_agent_route` (modify Case 4 weak-text branch + add a Case 3c)

**Step 1:** Insert Case 3c after Case 3b:

```python
# Case 3c: Auditor internal decision is FIX_PRODUCT_REVIEW but OCR pair is
# not fully legible. The auditor saw a real signal (text_mismatch or
# color_mismatch) but cannot cite the exact pair. Route to QA_TOOLING with
# a concrete next step: improve OCR preprocessing for this surface, then
# rerun. The actionable_evidence package carries the divergences.
if (
    classification.decision == "FIX_PRODUCT_REVIEW"
    and confidence in ("high", "medium")
    and not ocr_contradicts_product
):
    agent_route = "QA_TOOLING_ACTIONABLE"
    agent_next_action = (
        f"Auditor flagged FIX_PRODUCT_REVIEW on {classification.labels} "
        f"but the cited OCR pair is partial. Improve OCR preprocessing "
        f"(upscale, contrast, sharpen) for this surface and rerun. "
        f"VLM may be needed if preprocessing does not recover legibility."
    )
    qa_action_allowed = True
    product_action_allowed = False
    return (...)
```

**Step 2:** The existing Case 4 (weak text + low confidence) remains for cases where confidence=low even with a real pair.

---

### Task 4: Replace AUDITOR_IMPROVEMENT_ACTIONABLE's mass use with concrete evidence

**Objective:** Reserve AUDITOR_IMPROVEMENT_ACTIONABLE for genuine unknowns (no labels, no signals). Currently 67/86 hit it because it's the default fallback. The new Case 8 (default) should only fire when `classification.decision == "NEEDS_HUMAN_REVIEW"` (legacy) AND no other case matched.

**Files:**
- Modify: `qa/visual_auditor_v3.py:_map_to_agent_route` (Case 8 final fallback)

**Step 1:** Change Case 8 to require `classification.decision in ("NEEDS_HUMAN_REVIEW",)` AND no signal. Currently the case fires for any surface that didn't match earlier. Tighten:

```python
# Case 8: Real fallback — only when nothing else decided.
if (
    classification.decision == "NEEDS_HUMAN_REVIEW"
    and not any([has_real_text, has_color, has_structural, classification.suspected_module])
    and metrics.changed_pixel_ratio >= 0.05
):
    agent_route = "AUDITOR_IMPROVEMENT_ACTIONABLE"
    ...
```

**Step 2:** Add a unit test that confirms a surface with `decision=RENDER_NOISE_OK` does NOT fall into AUDITOR bucket.

---

### Task 5: Test the reorientation

**Objective:** Verify the post-run distribution matches the criterion.

**Step 1:** Add `test_distribution_no_mass_auditor_bucket`:

```python
def test_distribution_no_mass_auditor_bucket():
    report = json.loads((_PROJ / "qa/_visual_auditor_v3/latest/report.json").read_text())
    n_auditor = sum(1 for r in report if r["agent_package"]["agent_route"] == "AUDITOR_IMPROVEMENT_ACTIONABLE")
    assert n_auditor <= 10, f"AUDITOR bucket is too large ({n_auditor}/86); V3 must dispatch concretely."
```

**Step 2:** Add `test_all_surfaces_have_actionable_evidence`:

```python
def test_all_surfaces_have_actionable_evidence():
    report = json.loads((_PROJ / "qa/_visual_auditor_v3/latest/report.json").read_text())
    for r in report:
        pkg = r["agent_package"]
        assert "actionable_evidence" in pkg, f"Missing actionable_evidence on {pkg.get('surface_key')}"
        ae = pkg["actionable_evidence"]
        assert ae.get("probable_root_cause") != "unknown" or pkg["agent_route"] == "AUDITOR_IMPROVEMENT_ACTIONABLE"
```

**Step 3:** Add `test_product_actionable_requires_legit_pair` (already exists; verify it still passes).

**Step 4:** Add `test_no_action_needed_renders_decision_no_bug`:

```python
def test_no_action_needed_for_render_noise_ok():
    report = json.loads((_PROJ / "qa/_visual_auditor_v3/latest/report.json").read_text())
    for r in report:
        cls = r["classification"]
        pkg = r["agent_package"]
        if cls["decision"] == "RENDER_NOISE_OK" and "MISSING_COMPONENT" not in cls.get("labels", []) and "EXTRA_COMPONENT" not in cls.get("labels", []):
            assert pkg["agent_route"] == "NO_ACTION_NEEDED_WITH_EVIDENCE", (
                f"RENDER_NOISE_OK without structural must go to NO_ACTION: {pkg.get('surface_key')}"
            )
```

---

### Task 6: Batch mode CLI

**Objective:** Add `--quiet --resume --log-file <path>` to `analyze --all`. Reduces stdout, persists progress to `.hermes/qa_progress.json` (per-surface status), can resume from where it stopped, logs to file without freezing.

**Files:**
- Modify: `qa/visual_auditor_v3.py` (argparse + main())
- Create: `qa/_visual_auditor_v3/cli_batch.py` (helpers: load_progress, save_progress, log)

**Step 1:** argparse additions:

```python
parser.add_argument("--quiet", action="store_true", help="Suppress per-surface stdout")
parser.add_argument("--resume", action="store_true", help="Skip surfaces already analyzed in progress file")
parser.add_argument("--log-file", type=Path, default=None, help="Append progress to this file")
```

**Step 2:** In `main()`, before iterating surfaces:

```python
progress_path = Path(".hermes/qa_progress.json")
done = set()
if args.resume and progress_path.exists():
    done = set(json.loads(progress_path.read_text()).get("done", []))

log_fp = open(args.log_file, "a", encoding="utf-8") if args.log_file else None
def emit(msg):
    if not args.quiet:
        print(msg)
    if log_fp:
        log_fp.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")
        log_fp.flush()
```

**Step 3:** Per surface, after analyze_surface returns:

```python
if surface_key in done:
    emit(f"[skip] {surface_key} (already done)")
    continue
emit(f"Analyzing {surface_key}...")
try:
    pkg = analyze_surface(...)
    done.add(surface_key)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps({"done": sorted(done)}))
    emit(f"[OK] {surface_key}")
except Exception as e:
    emit(f"[FAIL] {surface_key}: {e}")
    if not args.resume:
        raise
```

**Step 4:** Wrap the loop in try/finally to close the log file.

**Step 5:** Test that the flags parse without error (no functional test needed for argparse).

---

### Task 7: Update the legacy tests that asserted specific distribution

**Objective:** Several existing tests assert that specific routes are valid (e.g. `test_product_actionable_requires_top_bbox_real_pair`). After the reorientation, these still hold but the distribution changed. Run the full test suite and fix any breakage caused by the new dispatch (not by removing tests).

**Files:**
- Modify: `tests/test_visual_auditor_v3.py` (any test that broke; do NOT remove tests)

---

### Task 8: Audit pass + commit

**Objective:** Final verification.

**Step 1:** Run ruff: `.venv/Scripts/python.exe -m ruff check qa/visual_auditor_v3.py tests/test_visual_auditor_v3.py`
**Step 2:** Run full pytest on V3 + V2 + normalize_mockup tests:
```bash
.venv/Scripts/python.exe -m pytest tests/test_visual_auditor_v3.py tests/test_visual_auditor_v2.py tests/test_normalize_mockup_reference.py -v
```
**Step 3:** Run doctor: `.venv/Scripts/python.exe qa/visual_auditor_v3.py doctor`
**Step 4:** Run analyze --all in batch mode: `.venv/Scripts/python.exe qa/visual_auditor_v3.py analyze --all --quiet --log-file .hermes/qa_batch.log`
**Step 5:** Read queue.md + index.html, confirm 86/86 surfaces present, distribution matches the criterion.
**Step 6:** git status --short, confirm no accidental edits.
**Step 7:** Commit (single commit with full description; not split — this is one logical change).

---

## Acceptance criterion (re-stated)

- 86/86 surfaces with `actionable_evidence` populated, route either `NO_ACTION_NEEDED_WITH_EVIDENCE`, `QA_TOOLING_ACTIONABLE`, `CAPTURE_OR_PAIRING_ACTIONABLE`, or `PRODUCT_ACTIONABLE` (only with legit pair).
- AUDITOR_IMPROVEMENT_ACTIONABLE ≤ 10 surfaces (only genuine unknowns).
- 0 owner review.
- 0 `PRODUCT_ACTIONABLE` with weak evidence (existing guardrail holds).
- batch mode `--quiet --resume --log-file` works.
- ruff + pytest + doctor + analyze --all + queue + git status all green.
- NO V2 deletion. NO product changes. NO push.