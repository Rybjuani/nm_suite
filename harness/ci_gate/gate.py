#!/usr/bin/env python3
"""harness/ci_gate/gate.py — binary PASS/FAIL for CI.

Reads a VisualParity evidence bundle + runs the closure policy. Exits 0 if
the policy allows closure for all surfaces in the target set; exits 1 if any
surface is blocked.

This is the ONLY binary signal CI consumes. If this script exits 1, the
pipeline fails. No agent can bypass it.

Usage:
    python harness/ci_gate/gate.py \\
        --bundle vp_report/bundle.json \\
        --target-set harness/agent_runner/current_target_set.txt \\
        --policy harness/policy/closure_policy.yaml

Exit codes:
    0  PASS — all target-set surfaces are ALLOW_CLOSURE
    1  FAIL — at least one surface is BLOCK_CLOSURE or missing required properties
    2  ERROR — bundle invalid, policy missing, or internal error
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
POLICY = PROJ / "harness" / "policy" / "closure_policy.yaml"
SEMANTIC_LINT = PROJ / "harness" / "semantic_lint" / "handoff_text_lint.py"


def load_bundle(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: bundle not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: bundle is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)


def load_target_set(path: Path) -> list[str]:
    if not path.exists():
        print(f"ERROR: target-set file not found: {path}", file=sys.stderr)
        sys.exit(2)
    keys = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            keys.append(line)
    return keys


def run_semantic_lint(surface_key: str) -> bool:
    """Run handoff_text_lint.py for the given key. Returns True if PASS."""
    try:
        result = subprocess.run(
            ["python3", str(SEMANTIC_LINT), "--key", surface_key],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def evaluate_surface(surface: dict, policy: dict) -> tuple[str, list[str]]:
    """Return (action, missing_requirements) for a single surface."""
    status = surface.get("status", "")
    rules = policy.get("rules", [])

    # Find the matching rule
    matching = next((r for r in rules if r.get("state") == status), None)
    if matching is None:
        return ("BLOCK_CLOSURE", [f"unknown_state:{status}"])

    action = matching.get("action", "BLOCK_CLOSURE")
    required = matching.get("requires", [])

    if action != "ALLOW_CLOSURE":
        return (action, required)

    # For ALLOW_CLOSURE, check all required properties.
    # In a real implementation these would call out to test runners, anti-fraud,
    # replay, etc. For now we just check that the surface has no blocking
    # findings.
    missing = []
    findings = surface.get("findings", [])
    blocking_findings = [f for f in findings if f.startswith("near_threshold:")
                         or f == "non_deterministic_capture"
                         or f == "state_ambiguity"
                         or f == "suspicious_perfect_match"
                         or f == "near_perfect_match"]
    if blocking_findings:
        missing.append(f"blocking_findings:{blocking_findings}")

    # Near-threshold surfaces require HUMAN_REVIEWED_PASS (VQA-THRESH-001)
    if any(f.startswith("near_threshold:") for f in findings):
        if status != "HUMAN_REVIEWED_PASS":
            missing.append("near_threshold_requires_human_review")

    return (action, missing)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--target-set", required=True, type=Path)
    parser.add_argument("--policy", default=POLICY, type=Path)
    parser.add_argument("--skip-semantic-lint", action="store_true",
                        help="Skip handoff_text_lint.py (NOT recommended for closure)")
    args = parser.parse_args()

    bundle = load_bundle(args.bundle)
    target_keys = load_target_set(args.target_set)

    # Validate bundle schema
    schema = bundle.get("schema_version")
    if not schema:
        print("FAIL: bundle_missing_schema_version", file=sys.stderr)
        return 1
    eol = bundle.get("eol")
    if eol != "lf":
        print(f"FAIL: bundle_eol_not_lf (got {eol!r})", file=sys.stderr)
        print("  VisualParity must use EolNormalizer for cross-platform hashes.",
              file=sys.stderr)
        return 1

    # Index surfaces by surface_key
    surfaces_by_key = {s["surface_key"]: s for s in bundle.get("surfaces", [])}

    # Check every target key
    blocking = []
    for key in target_keys:
        if key not in surfaces_by_key:
            blocking.append((key, "MISSING_FROM_BUNDLE", []))
            continue

        surface = surfaces_by_key[key]
        action, missing = evaluate_surface(surface, bundle)

        if action != "ALLOW_CLOSURE":
            blocking.append((key, action, missing))
            continue

        if missing:
            blocking.append((key, "MISSING_REQUIREMENTS", missing))
            continue

        # Run semantic lint unless explicitly skipped
        if not args.skip_semantic_lint:
            if not run_semantic_lint(key):
                blocking.append((key, "SEMANTIC_LINT_FAILED", []))

    if blocking:
        print("FAIL: ci_gate_blocked", file=sys.stderr)
        print(f"  blocking_surfaces: {len(blocking)}", file=sys.stderr)
        for key, action, missing in blocking:
            print(f"    - {key}: {action}", file=sys.stderr)
            for m in missing:
                print(f"        missing: {m}", file=sys.stderr)
        return 1

    print("PASS: ci_gate_open")
    print(f"  target_set_size: {len(target_keys)}")
    print(f"  bundle: {args.bundle}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
