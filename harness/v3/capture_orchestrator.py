#!/usr/bin/env python3
"""harness/v3/capture_orchestrator.py - Capture orchestration contract.

Fase 2: contract only. Does NOT invoke qa/capture_v8.py yet. Defines the
interface that the future runtime capture_orchestrator will implement.

The capture_orchestrator is the ONLY module permitted to invoke
qa/capture_v8.py. VisualParity Core/CLI never invokes it. Agents never
invoke it. CI never invokes it.

NO runtime authority in Fase 2. This file declares the contract and
emits NOT_IMPLEMENTED for any actual capture attempt.

Usage:
    python harness/v3/capture_orchestrator.py --contract-print
    python harness/v3/capture_orchestrator.py --key <surface_key> --theme <light|dark>

Exit codes:
    0  contract printed or preflight check passed
    1  NOT_IMPLEMENTED (actual capture attempted)
    2  ERROR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONTRACT = {
    "module": "harness/v3/capture_orchestrator.py",
    "fase": "2-contract-only",
    "authority": "ONLY module permitted to invoke qa/capture_v8.py",
    "forbidden_for": [
        "VisualParity Core/CLI",
        "agents",
        "CI workflows",
        "V1/V2 legacy scripts",
    ],
    "captures_v8_limits": {
        "only_invoker": "harness/v3/capture_orchestrator.py",
        "introspect_flag": "disabled_until_vas_introspect_audited",
        "captures_v8_path": "qa/capture_v8.py",
    },
    "captures_v8_invocation_contract": {
        "command": "python qa/capture_v8.py --key <surface_key> --theme <theme> --out-dir <dir>",
        "introspect": "NOT passed by default",
        "output": "qa/_captures_v8/<key>.png + CAPTURE_MANIFEST.json",
        "provenance": "capture_provenance.json (run_id, git_head, mtime, capture_v8_sha256)",
    },
    "state_assertion": "harness/v3/state_assertion.py generates capture_state_assertion.json",
    "future_fase": "actual capture invocation deferred to fase where capture_v8 audit is complete",
}


def print_contract() -> int:
    print(json.dumps(CONTRACT, indent=2))
    return 0


def attempt_capture(surface_key: str, theme: str) -> int:
    """Fase 2: NOT_IMPLEMENTED. Actual capture is deferred."""
    print("NOT_IMPLEMENTED: capture_orchestrator is contract-only in Fase 2.",
          file=sys.stderr)
    print(f"  requested: surface_key={surface_key} theme={theme}", file=sys.stderr)
    print("  To enable, implement actual invocation in a later fase after",
          file=sys.stderr)
    print("  vas_introspect.py audit (OWNER_DECISION PEND-1).", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-print", action="store_true",
                        help="Print the capture contract and exit.")
    parser.add_argument("--key", default=None,
                        help="Surface key to capture (will emit NOT_IMPLEMENTED in Fase 2).")
    parser.add_argument("--theme", default=None, choices=["light", "dark"])
    args = parser.parse_args()
    if args.contract_print:
        return print_contract()
    if args.key and args.theme:
        return attempt_capture(args.key, args.theme)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
