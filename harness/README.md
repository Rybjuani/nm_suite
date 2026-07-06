# nm_suite/harness/ — VisualParity Consumer Harness

> **Frase rectora:** VisualParity mide y muestra. El harness decide.

This folder contains the project-specific protocol that consumes VisualParity
evidence bundles and decides whether a visual surface can close.

## What lives here

| Folder | Responsibility |
|---|---|
| `policy/` | Declarative closure policy (YAML). The ONLY authority for closure. |
| `anti_fraud/` | Static scan for canonical/reference artifact injection. Migrated from `qa/anti_fraud_scan.py` with LF-normalized hashes. |
| `replay/` | Replay of past closures with `--regen` mandate and `--min-keys` cardinality. Migrated from `qa/replay_visual_closure.py`. |
| `agent_runner/` | Controlled prompt dispatch to agents. Includes `target_scope_v2.py` with duplicate-key detection. |
| `ci_gate/` | Binary PASS/FAIL for CI. Reads bundle + runs policy + runs semantic lint. |
| `semantic_lint/` | Handoff text lint (forbidden phrases) + doc keyword lint (`DECISIÓN-OWNER` → `OWNER_EXCEPTION_ACTIVE`). |
| `checklists/` | (Reserved) Minimal checklist view. The active checklist lives at `VISUAL_REPAIR_HANDOFF.md` in the repo root. |
| `evidence_records/active/` | One JSON record per closed surface, bundle-backed. |
| `evidence_records/revoked/` | Records moved here when a closure is reopened. |
| `docs/` | `FORENSIC_FINDINGS_V2.md` and other harness docs. |

## What does NOT live here

- The VisualParity tool itself. It lives in a separate repo
  (`github.com/Rybjuani/visualparity` — to be created).
- The canonical PNGs and HTML. They stay at `qa/_mockup_canonical/` and
  `qa/pack canonico/`.
- The V8 capture script. It stays at `qa/capture_v8.py`.
- The product code. It stays at `app/`, `hub/`, `shared/`.

## Quick start

```bash
# 1. Capture surfaces (V8 stays where it is)
python qa/capture_v8.py --all --clean --out-dir qa/_captures_v8

# 2. Run VisualParity compare (external tool)
visualparity compare \
  --canon qa/_mockup_canonical \
  --actual qa/_captures_v8 \
  --out vp_report \
  --profile strict \
  --git-head $(git rev-parse HEAD)

# 3. Run the CI gate
python harness/ci_gate/gate.py \
  --bundle vp_report/bundle.json \
  --target-set harness/agent_runner/current_target_set.txt

# 4. Run anti-fraud scan
python harness/anti_fraud/scan.py

# 5. Run replay (full regen, all closed)
python harness/replay/replay.py --all-closed --min-keys 1

# 6. Run semantic lints
python harness/semantic_lint/handoff_text_lint.py --key suite:timer@light
python harness/semantic_lint/doc_keyword_lint.py
```

## V2 changes vs the V1 system

See `docs/FORENSIC_FINDINGS_V2.md` for the full red-team findings. Summary:

1. **EOL normalization** — all hashes are LF-normalized for cross-platform reproducibility.
2. **Determinism check** — two actual captures must be compared before closure.
3. **Semantic lint** — handoff line is parsed; forbidden phrases block closure.
4. **Duplicate-key check** — `target_scope_v2.py` refuses ambiguous state.
5. **Family/scope enforcement** — closer requires `--target-set` + `--family`.
6. **Replay cardinality** — `--min-keys` mandatory; `--no-regen` forbidden for closure.
7. **`DECISIÓN-OWNER` deprecation** — replaced by `OWNER_EXCEPTION_ACTIVE`.
8. **Stale report prevention** — VisualParity wipes OutDir before writing.
9. **`reopen_legacy_all` removed** — only individual `--reopen` with reason+reviewer.
10. **Near-threshold audit** — surfaces within 5% of threshold require human review.

## Status

This is a scaffold. The Python files are functional stubs that compile and run
but delegate the heavy lifting (actual capture, actual VisualParity invocation,
actual replay regen) to future Fase 4 work. The closure policy is complete and
authoritative; the gate enforces it.
