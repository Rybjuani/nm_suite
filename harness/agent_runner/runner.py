#!/usr/bin/env python3
"""harness/agent_runner/runner.py — dispatches controlled prompts to agents.

The agent runner is the ONLY entry point for dispatching work to agents.
Prompts are controlled: the runner assembles context, declares the target set,
fixes the VisualParity profile, and delivers a path to the latest bundle.

The agent never writes to the checklist. When the agent requests closure, it
calls back into the harness, which runs the full gate (anti-fraud + replay +
semantic lint + family scope + CI gate) and decides.

This is a STUB for Fase 5. The real implementation will:
  1. Read target_scope_v2.py output.
  2. For each key, render a prompt template.
  3. Dispatch to the agent runtime (Claude, GPT, local LLM).
  4. Wait for the agent to either:
     a. Request closure → call harness/ci_gate/gate.py
     b. Request more iterations → loop with fresh VisualParity compare
     c. Report blocker → log + stop
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
TARGET_SCOPE = PROJ / "harness" / "agent_runner" / "target_scope_v2.py"
CI_GATE = PROJ / "harness" / "ci_gate" / "gate.py"

PROMPT_TEMPLATE = """You are working on nm_suite visual parity for surface_key: {key}

Target set declared by owner: {target_set}
VisualParity profile: strict (DO NOT change)
Evidence bundle: {bundle_path}

Rules (NON-NEGOTIABLE):
1. You may invoke `visualparity compare` as many times as you want to measure
   progress. None of those invocations closes anything.
2. You may NOT edit VISUAL_REPAIR_HANDOFF.md. The harness owns the checklist.
3. You may NOT edit any file under harness/policy/, harness/anti_fraud/,
   harness/replay/, or harness/semantic_lint/. Those are governance.
4. You may NOT use --no-odiff, --no-panels, --raw-changed-threshold or any
   exploratory VisualParity flag. The bundle will be marked exploratory and
   the harness will reject it.
5. When you believe the surface is ready, request closure by running:
     python harness/ci_gate/gate.py --bundle {bundle_path} --target-set {target_set}
   If exit=0, closure is granted. If exit=1, read the blocking reasons and
   iterate. If exit=2, report the error to the owner.
6. If the surface is in harness/policy/closure_policy.yaml under
   known_non_deterministic_surfaces, you MUST first achieve two consecutive
   PASS regenerations with --determinism-check before requesting closure.
7. If the surface is part of a state_ambiguous_pairs entry, you MUST verify
   capture_state_assertion matches the declared surface_key state before
   requesting closure.

Current surface: {key}
"""


def resolve_target_set(mode: str, seed_key: str | None = None, n: int | None = None) -> list[str]:
    cmd = ["python3", str(TARGET_SCOPE), "--mode", mode]
    if seed_key:
        cmd += ["--seed-key", seed_key]
    if n is not None:
        cmd += ["--n", str(n)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines()
            if line.strip() and not line.startswith("#")]


def render_prompt(key: str, target_set_path: str, bundle_path: str) -> str:
    return PROMPT_TEMPLATE.format(
        key=key,
        target_set=target_set_path,
        bundle_path=bundle_path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="next-key",
                        choices=["next-key", "all-open-keys", "family", "first-n"])
    parser.add_argument("--seed-key", default=None)
    parser.add_argument("--n", type=int, default=None)
    parser.add_argument("--bundle", required=True, help="Path to current evidence bundle")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts without dispatching")
    args = parser.parse_args()

    keys = resolve_target_set(args.mode, args.seed_key, args.n)
    if not keys:
        print("# no open keys in target set")
        return 0

    target_set_path = PROJ / "harness" / "agent_runner" / "current_target_set.txt"
    target_set_path.write_text("\n".join(keys) + "\n", encoding="utf-8")

    for key in keys:
        prompt = render_prompt(key, str(target_set_path), args.bundle)
        if args.dry_run:
            print(f"=== PROMPT for {key} ===")
            print(prompt)
            print()
        else:
            # STUB: real dispatch goes here. For now, just print the prompt.
            print(f"[stub] would dispatch prompt for {key}")
            print(prompt)

    return 0


if __name__ == "__main__":
    sys.exit(main())
