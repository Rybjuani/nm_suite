#!/usr/bin/env python3
"""Cross-platform visual-closure evidence audit.

This replaces the previous PowerShell-only false-pass audit. It does not repair
UI and it does not generate fresh captures. Instead it verifies that any
VISUAL_REPAIR_HANDOFF checkbox closure in the diff is backed by already
generated, provenance-linked evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KEY_RE = re.compile(r"(suite|hub):([^@\s`\"'\]\)]+)@(light|dark)")
CHECKED_RE = re.compile(r"^\s*-\s*\[x\]")
OPEN_RE = re.compile(r"^\s*-\s*\[\s\]")

HARDENING_OBJECTIVES = {
    "hardening qa",
    "qa hardening",
    "hardening-qa",
    "visual evidence hardening",
}

RESTRICTED_CLOSURE_PATHS = (
    "qa/capture_v8.py",
    "qa/layered_visual_compare.py",
    "qa/vas_gate.py",
    "qa/anti_fraud_scan.py",
    "tools/qa/",
    "qa/_mockup_canonical/",
    "qa/pack canonico/",
    "qa/_captures_v8/",
    "qa/_visual_auditor_spec/",
    "reports/",
)


@dataclass
class AuditResult:
    ok: bool
    reasons: list[str]
    closed_keys: list[str]
    touched_restricted: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _keys(line: str) -> list[str]:
    return [match.group(0) for match in KEY_RE.finditer(line)]


def parse_closed_checkbox_keys(diff_text: str) -> list[str]:
    """Return exact keys whose checklist marker changed from open to checked."""
    removed_open: set[str] = set()
    closed: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("@@"):
            removed_open.clear()
            continue
        body = line[1:] if line[:1] in {"-", "+"} else line
        if line.startswith("-") and OPEN_RE.search(body):
            removed_open.update(_keys(body))
        elif line.startswith("+") and CHECKED_RE.search(body):
            added_keys = set(_keys(body))
            if removed_open:
                closed.update(added_keys & removed_open or added_keys)
            else:
                closed.update(added_keys)
    return sorted(closed)


def changed_files(base: str) -> list[str]:
    proc = _run_git(["diff", "--name-only", base])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff --name-only failed")
    return sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})


def handoff_diff(base: str, handoff: Path) -> str:
    proc = _run_git(["diff", "--unified=0", base, "--", str(handoff)])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff handoff failed")
    return proc.stdout


def restricted_touched(files: list[str]) -> list[str]:
    restricted: list[str] = []
    for raw in files:
        path = _normalize_path(raw)
        if any(path == marker.rstrip("/") or path.startswith(marker) for marker in RESTRICTED_CLOSURE_PATHS):
            restricted.append(raw)
    return restricted


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report_passes_for_key(report: dict[str, Any], key: str) -> bool:
    if report.get("authority") != "LAYERED_VISUAL_COMPARE":
        return False
    if report.get("report_evidence_valid") is not True:
        return False
    for result in report.get("results", []):
        if not isinstance(result, dict) or result.get("key") != key:
            continue
        if result.get("status") != "PASS":
            return False
        if result.get("suspicious_perfect_match") or result.get("near_perfect_match"):
            return False
        return True
    return False


def layered_report_valid_for_key(report_paths: list[Path], key: str) -> bool:
    for path in report_paths:
        if not path.exists():
            continue
        try:
            if _report_passes_for_key(_load_json(path), key):
                return True
        except Exception:
            continue
    return False


def vas_gate_valid(sidecar: Path, key: str) -> bool:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "qa" / "vas_gate.py"), "--sidecar", str(sidecar), "--key", key],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode == 0


def anti_fraud_clean() -> bool:
    for mode in ("runtime", "qa-harness"):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "qa" / "anti_fraud_scan.py"), "--mode", mode],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            return False
    return True


def audit(
    *,
    base: str,
    handoff: Path,
    layered_reports: list[Path],
    sidecar: Path,
    objective: str,
    skip_anti_fraud: bool = False,
) -> AuditResult:
    diff = handoff_diff(base, handoff)
    closed_keys = parse_closed_checkbox_keys(diff)
    touched = changed_files(base)
    restricted = restricted_touched(touched)
    normalized_objective = objective.strip().lower()
    hardening_objective = normalized_objective in HARDENING_OBJECTIVES

    reasons: list[str] = []
    if restricted and not hardening_objective:
        reasons.append("restricted_qa_or_artifact_paths_touched_without_hardening_objective")
    if closed_keys and hardening_objective:
        reasons.append("hardening_objective_must_not_close_visual_checkboxes")

    if closed_keys:
        if not layered_reports:
            reasons.append("checkbox_closure_without_layered_report")
        for key in closed_keys:
            if not layered_report_valid_for_key(layered_reports, key):
                reasons.append(f"{key}: missing valid layered PASS report")
            if not vas_gate_valid(sidecar, key):
                reasons.append(f"{key}: missing valid VAS/provenance")
        if not skip_anti_fraud and not anti_fraud_clean():
            reasons.append("anti_fraud_not_clean")

    return AuditResult(
        ok=not reasons,
        reasons=reasons,
        closed_keys=closed_keys,
        touched_restricted=restricted,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit visual closure evidence without PowerShell.")
    parser.add_argument("--base", default="main", help="Base revision for diff inspection.")
    parser.add_argument("--handoff", type=Path, default=ROOT / "VISUAL_REPAIR_HANDOFF.md")
    parser.add_argument("--layered-report", action="append", type=Path, default=[])
    parser.add_argument("--sidecar", type=Path, default=ROOT / "qa" / "_visual_auditor_spec" / "introspection.json")
    parser.add_argument("--objective", default="", help="Declared objective, e.g. 'hardening-qa'.")
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--skip-anti-fraud", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = audit(
        base=args.base,
        handoff=args.handoff,
        layered_reports=args.layered_report,
        sidecar=args.sidecar,
        objective=args.objective,
        skip_anti_fraud=args.skip_anti_fraud,
    )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    print("VISUAL CLOSURE EVIDENCE AUDIT " + ("PASS" if result.ok else "FAIL"))
    print(f"Closed keys: {len(result.closed_keys)}")
    if result.closed_keys:
        for key in result.closed_keys:
            print(f"  - {key}")
    print(f"Restricted touched: {len(result.touched_restricted)}")
    for path in result.touched_restricted:
        print(f"  - {path}")
    if result.reasons:
        print("Reasons:")
        for reason in result.reasons:
            print(f"  - {reason}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
