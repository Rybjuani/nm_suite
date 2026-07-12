# Forensic Findings V2 — Red-Team Validation

> **Status:** Validated locally against the live nm_suite repo (no commit/push yet).
> **Method:** Red-team + bug bounty techniques applied by the owner.
> **Date:** 2026-07-07.
> **Scope:** 38 hypotheses confirmed after the V1 forensic audit documented in
> `VisualParity_Workbench_Diseno_Tecnico.pdf`.

This document integrates the 38 red-team findings into the VisualParity + harness
design. Each finding is mapped to (a) the design gap it reveals, (b) the
mitigation in VisualParity Workbench, and (c) the mitigation in the consumer
harness. Findings that the V1 design already covered are marked `[covered-v1]`;
findings that required new design work are marked `[new-v2]`.

---

## A. Cross-platform hash reproducibility (findings #1, #2, #3)

### #1 — CRLF/LF bug affects all 116 active evidence records

Validated: 116/116 active records store SHA-256 hashes of `anti_fraud_scan.py`,
`capture_v8.py`, `layered_visual_compare.py` and `vas_gate.py` computed over
**CRLF bytes from the Windows checkout**, not over LF blobs from Git.

### #2 — Hashes were not random: they were checkout-dependent

Validated: 116/116 hashes match CRLF bytes, 0/116 match LF blobs. This separates
"hash invented" from "hash non-canonical by line endings". The cause is technical
(closed), but the evidence is forensically weak.

### #3 — Evidence byte-perfect is not reliable even when comparator gives PASS

Validated: a capture/report/evidence can fail to reproduce hashes even when the
comparator gives PASS. `PASS_visual`, `PASS_structural` and `evidence_byte_reproducible`
are three distinct properties.

**Design gap `[new-v2]`:** V1 design computed SHA-256 over raw file bytes. Two
checkouts of the same logical content (Windows CRLF vs Linux LF) would produce
different hashes, breaking CI reproducibility.

**Mitigation in VisualParity:**
- `Bundle/EolNormalizer.cs` normalizes CRLF/CR → LF before hashing.
- All hashes in `bundle.json` use `EolNormalizer.Sha256Normalized()`.
- The bundle records `"eol": "lf"` so the harness can verify the same mode was used.
- PNG files are binary (no EOL) — normalization is a no-op for them — but text
  artifacts (manifests, sidecars, evidence records, `bundle.json` itself) get
  reproducible hashes.

**Mitigation in harness:**
- The harness validates `bundle.eol == "lf"` before consuming.
- The replay script reads files with LF normalization when re-computing hashes.
- The closure policy adds `evidence_byte_reproducible` as a **fourth required
  property** alongside `tests_pass`, `anti_fraud_clean`, `replay_pass`.

---

## B. Capture non-determinism (findings #4, #13)

### #4 — Concrete sources of non-determinism identified

Validated:
- `actividades` has capture variance.
- `respiracion` has variance from animated ring/counter.
- `suite:rutina-add-task@dark` shows report volatility without capture change.
- `suite:actividades@light` confirmed non-deterministic by red-team: two PASS
  regenerations produced different `record_sha256`, PNG, manifest, report and sidecar.

### #13 — Cause split: capture instability vs report volatility

Validated: 9/11 replay-full failures are capture-instability; 2/11 are
report-hash volatility (`actividades-filtered@dark` and `rutina-add-task@dark`).

**Design gap `[new-v2]`:** V1 design assumed the actual PNG was stable. If the
actual side is non-deterministic, no closure can be valid regardless of how the
canon comparison goes — but V1 had no way to detect this.

**Mitigation in VisualParity:**
- `Comparators/DeterminismCheck.cs` compares two actual captures against each other.
- If `changed_ratio >= 0.005` between two actuals, the surface is flagged
  `non_deterministic_capture` and the harness MUST refuse closure.
- The CLI gets a new flag `--determinism-check <actual2_dir>` that runs this
  comparison before the canon comparison.

**Mitigation in harness:**
- The closure policy adds `determinism_pass` as a required property.
- The agent runner captures the same surface twice before requesting closure.
- The 11 known non-deterministic surfaces are listed in `policy/known_issues.yaml`
  with `status: blocked_until_capture_stabilized`.

---

## C. State confusion and comparator tolerance (findings #15, #16, #17)

### #15 — False visual PASS confirmed

Validated by red-team: `suite:rutina-add-task@dark` shows material divergences
incompatible with parity. Additionally, `suite:timer-running@light` compared
against a real capture of `suite:timer-paused@light` gives PASS in
`layered_visual_compare.py` despite being an incorrect visible state.

### #16 — State confusion: timer-paused passes as timer-running

Red-team `VQA-STATE-001`: capture of `timer-paused@light` compared as
`timer-running@light` gave `PASS`, with `changed=0.04265` and `bbox=14`.

### #17 — Visible mutations can pass comparator

Red-team `VQA-MUT-001`: visible mutations in `suite:home@light` and
`suite:timer-running@light` passed. `suite:rutina-add-task@dark` failed.

**Design gap `[partial-v1]`:** V1 design paired by surface_key filename, which
prevents the literal name-swap attack. But V1 did not verify that the capture
command actually produced the named state — an agent could capture
`timer-paused` and rename the file to `timer-running`.

**Mitigation in VisualParity:**
- `ProvenanceRecord` gets a new field `capture_state_assertion` that the harness
  fills with the state the capture command claims to have produced.
- The comparator can optionally run a state-difference check between
  `timer-running` and `timer-paused` canonicals: if their inter-canonical
  distance is small (similar states), the comparator adds a `state_ambiguity`
  finding requiring extra verification.

**Mitigation in harness:**
- The V8 capture script emits a state fingerprint (window title, button labels,
  visible timer value) alongside the PNG. The harness verifies the fingerprint
  matches the declared state before accepting the capture.
- The closure policy refuses `state_ambiguity` surfaces without
  `HUMAN_REVIEWED_PASS`.

---

## D. Replay semantic weaknesses (findings #7, #8, #12, #20)

### #7 — Replay does not revalidate all closed history

Validated: replay audits the range `base..HEAD`; keys closed before `base` and
not modified are excluded. A bounded replay can pass without touching prior closures.

### #8 — Structural replay can pass while full replay fails

Validated: in mass emulation, structural replay `--no-regen` gave PASS for 116
keys, but full replay with regeneration gave FAIL. Structural check ≠ reproducible
closure.

### #12 — The 11 replay-full FAIL keys passed `run_visual` twice

Validated: the failure was evidence/hash reproducibility, not direct comparator
FAIL detected by `run_visual`.

### #20 — Replay can return empty PASS

Red-team `VQA-REPLAY-001`: `replay_visual_closure.py --base HEAD --no-regen`
returned `REPLAY PASS` with `replayed_keys: 0`. Dangerous if an agent does not
validate expected cardinality.

**Design gap `[partial-v1]`:** V1 design required `replay_pass` in the closure
policy but did not specify cardinality or full-regen requirements.

**Mitigation in harness:**
- The replay script in the harness REQUIRES `--min-keys <N>` and fails if
  `replayed_keys < N`.
- The closure policy distinguishes `replay_structural_pass` (weak, diagnostic)
  from `replay_full_regen_pass` (strong, required for closure).
- The policy explicitly forbids `--no-regen` for closure validation; structural
  replay is allowed only as a fast pre-check.

---

## E. Closer semantic bypass (findings #6, #10, #18, #19)

### #6 — Closer refuses to close an already-closed key

Validated: the normal flow requires the key to be open. Already-closed keys are
shielded from the ordinary close/revalidate flow. `[control-positive]`

### #10 — Reversible emulation closed 116/116 by script

Validated: by temporarily reopening all 116 keys in a disposable worktree,
`close_visual_key.py` could close all of them. `target_scope.py --mode
all-open-keys` ended at 0 open. This proves the closer can produce records and
flip checkboxes for the full set.

### #18 — Closer can close a key with active FAIL/debt semantics

Red-team `VQA-SEM-001`: `close_visual_key.py` closed `suite:timer@light` even
though the active line contained `status=FAIL`, `severity=high`, `OPEN debt`,
`needs owner decision`, `risk`, `not worth touching`. Then
`replay_visual_closure.py --no-regen` gave PASS with `replayed_keys: 1`.

### #19 — Closer can leave semantic contradictions in the handoff

Validated with `suite:dbt-library@light/dark` and reinforced by red-team: a key
can be `[x]` with `evidence`/`record`/`closed-by` while the visible text retains
`status=FAIL`, `OPEN debt`, `keep open`, `risk` or equivalent. The JSON can say
PASS but the human-readable record stays contradictory.

**Design gap `[new-v2]`:** V1 design treated the JSON evidence record as
authoritative and ignored the visible handoff text. Red-team proved this is
exploitable: an agent can keep contradictory text in the handoff while the JSON
says PASS, and the closer will accept it.

**Mitigation in harness:**
- `semantic_lint/handoff_text_lint.py` parses the visible handoff line at
  closure time. If the line contains any of:
  `status=FAIL`, `OPEN debt`, `keep open`, `risk`, `not worth touching`,
  `needs owner decision`, `requires decision`, `near threshold` — closure is
  REFUSED with `reason: handoff_text_contradicts_evidence`.
- The lint runs BEFORE the closure commit and is non-bypassable.
- The list of forbidden phrases lives in `policy/forbidden_handoff_phrases.yaml`
  and is versioned with the policy.

---

## F. Parser duplicate-key spoofing (finding #21)

### #21 — Duplicate key spoofing

Red-team `VQA-DUP-001`: if a key appears closed in its real location and open
duplicated at the end, `target_scope.py` and closer helpers can treat it as
open. Risk: a key can have ambiguous state `[x]` and `[ ]`.

**Design gap `[new-v2]`:** V1 design did not consider duplicate surface_keys in
the handoff.

**Mitigation in harness:**
- `target_scope.py` is replaced by `harness/agent_runner/target_scope_v2.py`
  which deduplicates surface_keys and refuses to operate if any key appears more
  than once in the handoff.
- The check is `len(set(keys)) == len(keys)`. If unequal, the harness aborts with
  `reason: duplicate_surface_key_in_handoff` and lists the duplicates.
- The CI gate runs this check on every push.

---

## G. Stale report post-abort (finding #22)

### #22 — Anti-fraud aborts but leaves stale PASS report

Red-team `VQA-AF-STALE-001`: with an anti-fraud violation, the runner aborts
correctly, but the old `LAYERED_VISUAL_REPORT.json` remains intact in OutDir.
Risk: an agent could cite a stale report if it only looks at the file and not
the log/mtime/hash.

**Design gap `[new-v2]`:** V1 design wrote the bundle to a directory without
cleaning it first.

**Mitigation in VisualParity:**
- `BundleWriter.WriteAsync` deletes the entire output directory before writing.
  This guarantees the only bundle present is the one just written.
- If VisualParity aborts mid-write (anti-fraud, OOM, crash), the output dir is
  either empty or contains a partial bundle that fails schema validation —
  never a stale valid bundle from a previous run.

**Mitigation in harness:**
- The harness verifies `bundle.generated_at` is more recent than the latest
  commit in the audited range. A bundle older than the latest commit is rejected
  as stale.

---

## H. Document/classification ambiguity (findings #30, #31, #32, #33, #34)

### #30 — `DECISIÓN-OWNER` was the correct keyword

Validated: appears in active/remote docs and was consumed by Bridge/README/Known
Mismatches as an operative classification.

### #31 — The `DECISIÓN-OWNER` semantic gap was real

Before hardening, a divergence could be classified as `DECISIÓN-OWNER` and the
bridge said "do not correct towards mockup". It was a documented escape hatch to
stop iterating a difficult key.

### #32 — Local canon-first hardening corrects the gap but does not retroact

Validated: PNG/HTML canonical rules over bridge/reference docs; historical
decisions, old comments, `_archive`, bridge-era deviations and old
`DECISIÓN-OWNER` do not block closure unless revalidated as active exceptions.

### #33 — New protocol forbids risk/cost/"requires decision" as operational excuse

Validated: a FAIL key can only stop under closed conditions with a minimum
package. Comments, `_archive`, old logs, old feedback and transversal risk do
not count.

### #34 — Active inconsistency remains in `DECISIÓN-OWNER`

Red-team `VQA-DOC-001`: the new policy requires `OWNER_EXCEPTION_ACTIVE`, but
`QT_HTML_KNOWN_MISMATCHES.md` still maintains `DECISIÓN-OWNER` language/table.
Risk: an opportunistic agent can exploit this documentary ambiguity.

**Design gap `[new-v2]`:** V1 design used `OWNER_EXCEPTION_ACTIVE` in the policy
file but did not lint existing docs for the legacy `DECISIÓN-OWNER` keyword.

**Mitigation in harness:**
- `semantic_lint/doc_keyword_lint.py` scans all active docs (not `_archive/`) for
  the string `DECISIÓN-OWNER` and fails CI if any occurrence is found.
- The lint suggests the migration: `DECISIÓN-OWNER` → `OWNER_EXCEPTION_ACTIVE`
  with an explicit `reason:` and `reviewer:` field.
- The CI gate refuses to merge any PR that introduces a new `DECISIÓN-OWNER`
  occurrence in active docs.

---

## I. Family/scope enforcement gap (finding #37)

### #37 — Family/scope policy vs closer enforcement gap

Red-team `VQA-FAMILY-001`: docs prohibit closing an individual key if another
key in the same family is FAIL under family scope, but `close_visual_key.py`
only takes `--key` and does not know target-set/family. Documentary-script gap.

**Design gap `[new-v2]`:** V1 design had `target_scope.py` but did not enforce
family-level constraints at closure time.

**Mitigation in harness:**
- The harness closure API requires `--target-set <path>` and `--family <name>`
  in addition to `--key`. The closer refuses to operate without them.
- Before closing a key, the harness checks all other keys in the same family
  against the current bundle. If any is `HIGH_DIFF` or `SUSPICIOUS`, closure is
  refused with `reason: family_member_still_failing`.
- The check is bypassable only with `--allow-family-partial-close` plus a
  signed `OWNER_EXCEPTION_ACTIVE` record — and that exception itself is linted.

---

## J. Near-threshold PASS (finding #36)

### #36 — Near-miss PASS very close to threshold

Red-team `VQA-THRESH-001`: `suite:home-no-score@light` appears with
`changed=0.09977/0.10`, and `hub:detalle-resumen-ia-0@light` with
`changed=0.07933/0.08`. Not proof of false PASS alone, but marks priority
surfaces for human audit.

**Design gap `[new-v2]`:** V1 design only emitted PASS/FAIL; no warning zone.

**Mitigation in VisualParity:**
- `Ranking/NearThresholdFlag.cs` flags surfaces whose metrics are within 5% of
  the closing threshold, even when the surface is technically PASS.
- The flag appears in `bundle.json` as `findings: ["near_threshold:changed_pixel_ratio"]`.
- The harness treats `near_threshold` surfaces as audit-priority: they require
  `HUMAN_REVIEWED_PASS` even if the metric is technically under the limit.

---

## K. `reopen_legacy_all` dangerous surface (finding #28)

### #28 — `reopen_legacy_all` exists and is a dangerous governance surface

Validated: allows mass legacy reopen, deletes notes, and does not have the same
strong trail as `--reopen`. Not proven to hide a current visual FAIL, but the
escape surface is confirmed.

**Design gap `[partial-v1]`:** V1 design mentioned legacy closures but did not
explicitly deprecate `reopen_legacy_all`.

**Mitigation in harness:**
- `reopen_legacy_all` is removed from the harness. There is no mass-reopen path.
- All reopens go through `--reopen --key <key> --reason "<text>" --reviewer <id>`.
- The migration of any remaining legacy closures is a one-time documented event
  with a signed record per key, not a script.

---

## L. Other validated findings (already covered or control-positive)

- **#5** `target_scope.py` protects/excludes closed keys — `[control-positive]`,
  V1 design preserved this behavior.
- **#9** 11 keys fail replay full — `[covered-v1]`, V1 design requires
  `replay_full_regen_pass` for closure.
- **#11** Reversible emulation did not produce 116/116 reproducible closure —
  `[covered-v1]`, V1 design treats this as proof that the V1 system was broken.
- **#14** "Gate did not show hidden visual FAIL in 116" is REFUTED — `[covered-v1]`,
  V1 forensic audit already established this.
- **#23** Canonical/reference smuggling blocked — `[control-positive]`,
  VisualParity inherits `SUSPICIOUS_PERFECT_MATCH` + `canonical-injection ceiling`.
- **#24** Non-active sources produce `REPORT_EVIDENCE_VALID:NO` — `[control-positive]`,
  V1 design's provenance chain enforces this.
- **#25** VAS rejects sidecar from wrong key — `[control-positive]`, preserved.
- **#26** Modal/backdrop alteration failed comparator and modal audit —
  `[control-positive]`, V1 design moves modal audit to the harness.
- **#27** Basic evidence tampering detected — `[control-positive]`, V1 design's
  self-hash + per-file hashes cover this.
- **#29** Gate tests are partially stale — `[covered-v1]`, harness CI gate
  requires 100% test pass.
- **#35** Closures with visible high-divergence metadata despite evidence —
  `[covered-v1]`, V1 design replaces the handoff as authority.
- **#38** The 116/116 closure cannot be treated as homogeneous — `[covered-v1]`,
  this is the central thesis of the V1 forensic audit.

---

## Summary of new V2 design work

| Vector | Findings | New V2 artifact |
|---|---|---|
| EOL/hash cross-platform | #1-3 | `VisualParity.Core/Bundle/EolNormalizer.cs` |
| Capture non-determinism | #4, #13 | `VisualParity.Core/Comparators/DeterminismCheck.cs` |
| State confusion | #15-17 | `ProvenanceRecord.capture_state_assertion` field + harness state fingerprint |
| Replay semantic weak | #7, 8, 12, 20 | `replay_pass` → split into `replay_structural_pass` + `replay_full_regen_pass` + `--min-keys` cardinality |
| Closer semantic bypass | #18, 19 | `harness/semantic_lint/handoff_text_lint.py` |
| Duplicate-key spoofing | #21 | `harness/agent_runner/target_scope_v2.py` with dedup |
| Stale report post-abort | #22 | `BundleWriter` wipes output dir before write |
| DECISIÓN-OWNER ambiguity | #34 | `harness/semantic_lint/doc_keyword_lint.py` |
| Family/scope enforcement | #37 | Closure API requires `--target-set` + `--family` |
| Near-threshold PASS | #36 | `VisualParity.Core/Ranking/NearThresholdFlag.cs` |
| `reopen_legacy_all` | #28 | Removed from harness; individual `--reopen` only |

The V2 design is backward-compatible with the V1 evidence bundle schema: all new
fields are optional, and a V1 bundle can be consumed by a V2 harness (with
warnings). A V2 bundle cannot be consumed by a V1 harness (the V1 harness will
reject unknown fields like `eol`, `capture_state_assertion`, `near_threshold:*`).
