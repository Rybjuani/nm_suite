#!/usr/bin/env python3
"""Select the audit objective for the visual handoff workflow."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.qa.audit_handoff_false_pass import select_objective_for_diff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print audit objective args for VISUAL_REPAIR_HANDOFF changes.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--handoff", type=Path, default=Path("VISUAL_REPAIR_HANDOFF.md"))
    args = parser.parse_args(argv)

    objective = select_objective_for_diff(base=args.base, handoff=args.handoff)
    if objective:
        print(f"--objective {objective}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
