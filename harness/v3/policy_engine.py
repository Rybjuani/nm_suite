#!/usr/bin/env python3
"""harness/v3/policy_engine.py - Closure policy engine.

Maps VisualParity measurement states to harness actions. The policy is
the ONLY authority for closure. VisualParity emits measurement states
(NO_DIFF, MISSING_PAIR, SIZE_MISMATCH, DIFF_UNCLASSIFIED, etc.); the
harness maps them to ALLOW/BLOCK/HUMAN_REVIEW_REQUIRED.

NO runtime authority beyond policy evaluation. Does NOT close keys directly.
Does NOT invoke V1/V2. Does NOT invoke capture_v8. Does NOT emit CLOSURE_PASS.

States mapping (Fase 2 - initial):
    NO_DIFF            -> CANDIDATE_PASS     (still requires all required_properties)
    MISSING_PAIR       -> BLOCK
    SIZE_MISMATCH      -> BLOCK
    DIFF_UNCLASSIFIED  -> BLOCK
    LOW_DIFF           -> HUMAN_REVIEW_REQUIRED (never auto-close)
    HIGH_DIFF          -> BLOCK              (no override; MEASUREMENT_DISPUTE path)
    SUSPICIOUS         -> BLOCK
    NEAR_THRESHOLD     -> HUMAN_REVIEW_REQUIRED
    NON_DETERMINISTIC  -> BLOCK
    MEASUREMENT_DISPUTE_CANDIDATE -> HUMAN_REVIEW_REQUIRED
    HUMAN_REVIEWED_PASS  -> CANDIDATE_PASS    (requires reviewer, timestamp, reason)
    HUMAN_REVIEWED_FAIL  -> BLOCK

Usage:
    python harness/v3/policy_engine.py --state <state> [--properties <json>]

Exit codes:
    0  decision emitted (BLOCK, CANDIDATE_PASS, HUMAN_REVIEW_REQUIRED)
    1  invalid state
    2  ERROR
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# VisualParity-emitted measurement states (input)
MEASUREMENT_STATES = {
    "NO_DIFF",
    "MISSING_PAIR",
    "SIZE_MISMATCH",
    "DIFF_UNCLASSIFIED",
    "LOW_DIFF",
    "HIGH_DIFF",
    "SUSPICIOUS",
    "NEAR_THRESHOLD",
    "NON_DETERMINISTIC",
    "MEASUREMENT_DISPUTE_CANDIDATE",
}

# Harness-emitted decisions (output). These are the only closure-relevant
# decisions VisualParity itself NEVER emits.
HARNESS_DECISIONS = {
    "CANDIDATE_PASS",
    "BLOCK",
    "HUMAN_REVIEW_REQUIRED",
}

# States that only the harness can emit after human review (input from
# review_annotation.json processed by the harness).
HARNESS_INPUT_STATES = {
    "HUMAN_REVIEWED_PASS",
    "HUMAN_REVIEWED_FAIL",
}

# Required properties for CANDIDATE_PASS to upgrade to CLOSURE_ALLOWED
# (closure is a separate operation; policy_engine only emits CANDIDATE_PASS).
REQUIRED_PROPERTIES = [
    "tests_pass",
    "anti_fraud_clean",
    "replay_full_regen_pass",
    "evidence_byte_reproducible",
    "determinism_pass",
    "state_assertion_valid",
    "canonical_png_hash_in_record",
    "vp_build_sha256_in_allowlist",
]

STATE_TO_ACTION: dict[str, str] = {
    "NO_DIFF": "CANDIDATE_PASS",
    "MISSING_PAIR": "BLOCK",
    "SIZE_MISMATCH": "BLOCK",
    "DIFF_UNCLASSIFIED": "BLOCK",
    "LOW_DIFF": "HUMAN_REVIEW_REQUIRED",
    "HIGH_DIFF": "BLOCK",
    "SUSPICIOUS": "BLOCK",
    "NEAR_THRESHOLD": "HUMAN_REVIEW_REQUIRED",
    "NON_DETERMINISTIC": "BLOCK",
    "MEASUREMENT_DISPUTE_CANDIDATE": "HUMAN_REVIEW_REQUIRED",
    "HUMAN_REVIEWED_PASS": "CANDIDATE_PASS",
    "HUMAN_REVIEWED_FAIL": "BLOCK",
}


def evaluate(state: str, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate a state and return a decision envelope."""
    properties = properties or {}
    state_upper = state.upper()
    if state_upper not in STATE_TO_ACTION:
        return {
            "decision": "BLOCK",
            "reason": f"unknown_state:{state}",
            "required_properties_checked": False,
        }
    action = STATE_TO_ACTION[state_upper]
    # For CANDIDATE_PASS, check required properties (informational; closure
    # is a separate step).
    missing_props: list[str] = []
    if action == "CANDIDATE_PASS":
        for prop in REQUIRED_PROPERTIES:
            if not properties.get(prop):
                missing_props.append(prop)
    return {
        "decision": action,
        "input_state": state_upper,
        "missing_required_properties": missing_props,
        "required_properties_checked": action == "CANDIDATE_PASS",
        "note": (
            "CANDIDATE_PASS requires all required_properties to upgrade to "
            "CLOSURE_ALLOWED. Closure is a separate harness operation."
            if action == "CANDIDATE_PASS"
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True)
    parser.add_argument("--properties", default=None,
                        help="JSON object of required properties")
    args = parser.parse_args()
    props: dict[str, Any] = {}
    if args.properties:
        try:
            props = json.loads(args.properties)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid --properties JSON: {e}", file=sys.stderr)
            return 2
    result = evaluate(args.state, props)
    print(json.dumps(result, indent=2))
    if result["decision"] == "BLOCK" and result.get("reason", "").startswith("unknown_state"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
