#!/usr/bin/env python3
"""Cross-platform visual-closure evidence audit.

This replaces the previous PowerShell-only false-pass audit. It does not repair
UI and it does not generate fresh captures. Instead it verifies that any
VISUAL_REPAIR_HANDOFF checkbox closure in the diff is backed by already
generated, provenance-linked evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KEY_RE = re.compile(r"(suite|hub):([^@\s`\"'\]\)]+)@(light|dark)")
CHECKED_RE = re.compile(r"^\s*-\s*\[x\]")
OPEN_RE = re.compile(r"^\s*-\s*\[\s\]")
CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)-\s*\[(?P<state>[xX ])\]\s*(?P<body>.*)$")
COMMIT_CITATION_RE = re.compile(
    r"\b(?:fix\s+commit|commit(?:\s+hash)?)\s+`?([^`\s;,:]+)`?",
    re.IGNORECASE,
)
BUNDLE_SCHEMA = "visual_closure_bundle.v1"
DEFAULT_BUNDLE = ROOT / "docs" / "visual_closure_bundle.json"

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
    bundle_keys: list[str] = field(default_factory=list)
    validated_commits: list[str] = field(default_factory=list)

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


def _workspace_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _git_rev_parse(revision: str) -> str | None:
    proc = _run_git(["rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}"])
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _git_show_text(revision: str, path: Path) -> str:
    resolved = _workspace_path(path)
    rel_path = _normalize_path(str(resolved.relative_to(ROOT)))
    proc = _run_git(["show", f"{revision}:{rel_path}"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git show {revision}:{rel_path} failed")
    return proc.stdout


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _keys(line: str) -> list[str]:
    return [match.group(0) for match in KEY_RE.finditer(line)]


@dataclass
class ChecklistItem:
    key: str
    state: str
    line_no: int
    line: str
    notes: list[str] = field(default_factory=list)

    @property
    def note_text(self) -> str:
        return "\n".join(self.notes)


def _parse_checklist_items(text: str) -> list[ChecklistItem]:
    items: list[ChecklistItem] = []
    current: ChecklistItem | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = CHECKBOX_RE.match(line)
        if match:
            keys = _keys(line)
            if not keys:
                current = None
                continue
            state = "closed" if match.group("state").lower() == "x" else "open"
            current = ChecklistItem(
                key=keys[0],
                state=state,
                line_no=line_no,
                line=line,
            )
            items.append(current)
            continue
        if current is None:
            continue
        stripped = line.lstrip()
        if not line.strip():
            current.notes.append("")
            continue
        if line.startswith(" ") or line.startswith("\t"):
            current.notes.append(line)
            continue
        if stripped.startswith("#") or CHECKBOX_RE.match(line):
            current = None
            continue
        current = None
    return items


def _first_checklist_item(items: list[ChecklistItem], key: str, *, state: str | None = None) -> ChecklistItem | None:
    for item in items:
        if item.key != key:
            continue
        if state is not None and item.state != state:
            continue
        return item
    return None


def _commit_citations(text: str) -> list[str]:
    commits: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        if "commit" not in line.lower():
            continue
        for match in COMMIT_CITATION_RE.finditer(line):
            token = match.group(1).strip().strip("`").strip()
            if not token:
                continue
            normalized = token.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            commits.append(token)
    return commits


def _resolve_commit_range(base: str) -> set[str]:
    proc = _run_git(["rev-list", f"{base}..HEAD"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git rev-list failed")
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


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


def _load_bundle(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"bundle root must be a JSON object: {path}")
    return payload


def _bundle_keys(bundle: dict[str, Any]) -> list[str]:
    closures = bundle.get("closures", [])
    keys: list[str] = []
    if not isinstance(closures, list):
        return keys
    for entry in closures:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        if isinstance(key, str) and key:
            keys.append(key)
    return keys


def _entry_report_summary(report: dict[str, Any], key: str) -> dict[str, Any] | None:
    if report.get("authority") != "LAYERED_VISUAL_COMPARE":
        return None
    if report.get("report_evidence_valid") is not True:
        return None
    if report.get("summary") is None:
        return None
    for result in report.get("results", []):
        if not isinstance(result, dict) or result.get("key") != key:
            continue
        if result.get("status") != "PASS":
            return None
        if result.get("suspicious_perfect_match") or result.get("near_perfect_match"):
            return None
        return {
            "authority": report.get("authority"),
            "report_evidence_valid": report.get("report_evidence_valid"),
            "report_scope": report.get("report_scope"),
            "handoff_closure_allowed": report.get("handoff_closure_allowed"),
            "summary": report.get("summary"),
            "result": {
                "key": result.get("key"),
                "status": result.get("status"),
                "suspicious_perfect_match": bool(result.get("suspicious_perfect_match")),
                "near_perfect_match": bool(result.get("near_perfect_match")),
            },
        }
    return None


def _entry_sidecar_summary(entry: dict[str, Any], key: str) -> dict[str, Any] | None:
    if not isinstance(entry.get("provenance"), dict):
        return None
    if entry.get("surface_key") != key:
        return None
    fail_count = entry.get("fail_count")
    divergences = entry.get("divergences", [])
    if not isinstance(divergences, list):
        divergences = []
    blocking = [
        d for d in divergences
        if isinstance(d, dict) and str(d.get("severity", "")).lower() in {"high", "medium"}
    ]
    return {
        "surface_key": entry.get("surface_key"),
        "fail_count": fail_count,
        "divergence_count": len(divergences),
        "blocking_divergence_count": len(blocking),
        "provenance_key": entry.get("provenance", {}).get("key"),
        "provenance_png_sha256": entry.get("provenance", {}).get("png_sha256"),
        "provenance_capture_script_sha256": entry.get("provenance", {}).get("capture_script_sha256"),
        "provenance_introspection_entry_id": entry.get("provenance", {}).get("introspection_entry_id"),
    }


def _check_commit_citations(
    *,
    citations: list[str],
    audited_commits: set[str],
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    validated: list[str] = []
    for token in citations:
        resolved = _git_rev_parse(token)
        if resolved is None:
            reasons.append(f"closure note cites commit {token!r} but it does not exist in git")
            continue
        if resolved not in audited_commits:
            reasons.append(
                f"closure note cites commit {token!r} ({resolved}) but it is outside the audited range"
            )
            continue
        validated.append(resolved)
    return reasons, validated


def _validate_bundle_entry(
    *,
    entry: dict[str, Any],
    base: str,
    handoff_items: list[ChecklistItem],
    base_items: list[ChecklistItem],
    audited_commits: set[str],
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    validated_commits: list[str] = []

    key = entry.get("key")
    if not isinstance(key, str) or not key:
        return ["bundle closure entry missing key"], []

    current_item = _first_checklist_item(handoff_items, key, state="closed")
    if current_item is None:
        reasons.append(f"{key}: bundle claims closure but handoff has no checked item")
        return reasons, validated_commits

    base_item = _first_checklist_item(base_items, key, state="open")
    if base_item is None:
        reasons.append(f"{key}: base {base!r} does not contain the open checkbox transition")

    note_citations = _commit_citations(current_item.note_text)
    bundle_citations = entry.get("closure_note_hashes", [])
    if not isinstance(bundle_citations, list):
        reasons.append(f"{key}: bundle closure_note_hashes must be a list")
        bundle_citations = []

    if not note_citations:
        reasons.append(f"{key}: closure note does not cite a fix commit hash")
    else:
        note_set = {token.lower() for token in note_citations}
        bundle_set = {str(token).lower() for token in bundle_citations if str(token).strip()}
        if not bundle_set:
            reasons.append(f"{key}: bundle closure_note_hashes must not be empty")
        elif note_set != bundle_set:
            reasons.append(f"{key}: bundle closure_note_hashes do not match the handoff note")

    commit_reasons, commit_ids = _check_commit_citations(
        citations=note_citations,
        audited_commits=audited_commits,
    )
    reasons.extend(f"{key}: {reason}" for reason in commit_reasons)
    validated_commits.extend(commit_ids)

    report = entry.get("report")
    if not isinstance(report, dict):
        reasons.append(f"{key}: bundle entry missing report manifest")
        return reasons, validated_commits

    report_path = report.get("path")
    if not isinstance(report_path, str) or not report_path:
        reasons.append(f"{key}: report path missing from bundle")
        return reasons, validated_commits
    report_file = Path(report_path)
    if not report_file.exists():
        reasons.append(f"{key}: report path does not exist: {report_path}")
        return reasons, validated_commits
    report_sha = _sha256_file(report_file)
    if report_sha != report.get("sha256"):
        reasons.append(f"{key}: report hash does not match bundle sha256")
        return reasons, validated_commits
    report_payload = _load_json(report_file)
    expected_report_summary = _entry_report_summary(report_payload, key)
    if expected_report_summary is None:
        reasons.append(f"{key}: report does not contain a valid PASS for the closure")
    elif report.get("summary") != expected_report_summary:
        reasons.append(f"{key}: report summary in bundle does not match the report payload")

    sidecar = entry.get("sidecar")
    if not isinstance(sidecar, dict):
        reasons.append(f"{key}: bundle entry missing sidecar summary")
        return reasons, validated_commits

    sidecar_path = sidecar.get("path")
    if not isinstance(sidecar_path, str) or not sidecar_path:
        reasons.append(f"{key}: sidecar path missing from bundle")
        return reasons, validated_commits
    sidecar_file = Path(sidecar_path)
    if not sidecar_file.exists():
        reasons.append(f"{key}: sidecar path does not exist: {sidecar_path}")
        return reasons, validated_commits
    sidecar_sha = _sha256_file(sidecar_file)
    if sidecar_sha != sidecar.get("sha256"):
        reasons.append(f"{key}: sidecar hash does not match bundle sha256")
        return reasons, validated_commits

    sidecar_payload = _load_json(sidecar_file)
    if not isinstance(sidecar_payload, list):
        reasons.append(f"{key}: sidecar root is not a JSON array")
        return reasons, validated_commits
    matching = [
        item for item in sidecar_payload
        if isinstance(item, dict) and item.get("surface_key") == key
    ]
    if not matching:
        reasons.append(f"{key}: sidecar does not contain the surface key")
        return reasons, validated_commits
    sidecar_entry = matching[0]
    expected_sidecar_summary = _entry_sidecar_summary(sidecar_entry, key)
    if expected_sidecar_summary is None:
        reasons.append(f"{key}: sidecar entry is not a valid PASS provenance record")
    elif sidecar.get("summary") != expected_sidecar_summary:
        reasons.append(f"{key}: sidecar summary in bundle does not match the sidecar payload")

    provenance = entry.get("provenance")
    if provenance != sidecar_entry.get("provenance"):
        reasons.append(f"{key}: bundle provenance does not match the sidecar provenance")

    if provenance and report.get("summary") and sidecar.get("summary"):
        if not isinstance(provenance, dict):
            reasons.append(f"{key}: bundle provenance is not an object")
        else:
            capture_manifest = provenance.get("capture_manifest")
            if not isinstance(capture_manifest, str) or not capture_manifest:
                reasons.append(f"{key}: bundle provenance missing capture_manifest")
            elif not Path(capture_manifest).exists():
                reasons.append(f"{key}: capture manifest does not exist: {capture_manifest}")
            else:
                manifest_sha = _sha256_file(Path(capture_manifest))
                if manifest_sha is None:
                    reasons.append(f"{key}: capture manifest is unreadable")

    return reasons, validated_commits


def audit(
    *,
    base: str,
    handoff: Path,
    bundle: Path,
    layered_reports: list[Path],
    sidecar: Path,
    objective: str,
    skip_anti_fraud: bool = False,
) -> AuditResult:
    handoff = _workspace_path(handoff)
    bundle = _workspace_path(bundle)
    sidecar = _workspace_path(sidecar)

    diff = handoff_diff(base, handoff)
    closed_keys = parse_closed_checkbox_keys(diff)
    touched = changed_files(base)
    restricted = restricted_touched(touched)
    normalized_objective = objective.strip().lower()
    hardening_objective = normalized_objective in HARDENING_OBJECTIVES
    base_commit = _git_rev_parse(base)
    head_commit = _git_rev_parse("HEAD")
    if base_commit is None:
        raise RuntimeError(f"base revision cannot be resolved: {base}")
    if head_commit is None:
        raise RuntimeError("HEAD cannot be resolved")

    current_text = handoff.read_text(encoding="utf-8")
    base_text = _git_show_text(base, handoff)
    current_items = _parse_checklist_items(current_text)
    base_items = _parse_checklist_items(base_text)

    bundle_payload = _load_bundle(bundle)
    bundle_keys: list[str] = []
    bundle_closures: list[dict[str, Any]] = []
    validated_commit_ids: list[str] = []
    if bundle_payload is not None:
        if bundle_payload.get("schema") != BUNDLE_SCHEMA:
            raise ValueError(f"unexpected bundle schema: {bundle_payload.get('schema')!r}")
        bundle_closures = [
            entry for entry in bundle_payload.get("closures", [])
            if isinstance(entry, dict)
        ]
        bundle_keys = _bundle_keys(bundle_payload)
    bundle_key_set = set(bundle_keys)
    diff_key_set = set(closed_keys)

    reasons: list[str] = []
    if restricted and not hardening_objective:
        reasons.append("restricted_qa_or_artifact_paths_touched_without_hardening_objective")
    if closed_keys and hardening_objective:
        reasons.append("hardening_objective_must_not_close_visual_checkboxes")
    if bundle_payload is None:
        if closed_keys:
            reasons.append("checkbox_closure_without_versioned_bundle")
    else:
        if bundle_key_set != diff_key_set:
            reasons.append("bundle_keys_do_not_match_handoff_diff")
        if not bundle_closures and diff_key_set:
            reasons.append("bundle_has_no_closure_entries")
        if bundle_closures or diff_key_set:
            audited_range = bundle_payload.get("audited_range")
            if not isinstance(audited_range, dict):
                reasons.append("bundle_audited_range_missing")
            elif audited_range.get("base_commit") != base_commit or audited_range.get("head_commit") != head_commit:
                reasons.append("bundle_audited_range_does_not_match_audited_git_range")
        audited_commits = _resolve_commit_range(base)
        for entry in bundle_closures:
            entry_reasons, validated_commits = _validate_bundle_entry(
                entry=entry,
                base=base,
                handoff_items=current_items,
                base_items=base_items,
                audited_commits=audited_commits,
            )
            reasons.extend(entry_reasons)
            validated_commit_ids.extend(validated_commits)
            bundle_keys.append(str(entry.get("key", "")))
        if not skip_anti_fraud and bundle_closures and not anti_fraud_clean():
            reasons.append("anti_fraud_not_clean")
    if bundle_payload is None and not skip_anti_fraud and closed_keys and not anti_fraud_clean():
        reasons.append("anti_fraud_not_clean")

    return AuditResult(
        ok=not reasons,
        reasons=reasons,
        closed_keys=closed_keys,
        touched_restricted=restricted,
        bundle_keys=sorted({key for key in bundle_keys if key}),
        validated_commits=sorted({commit for commit in validated_commit_ids if commit}),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit visual closure evidence without PowerShell.")
    parser.add_argument("--base", default="main", help="Base revision for diff inspection.")
    parser.add_argument("--handoff", type=Path, default=ROOT / "VISUAL_REPAIR_HANDOFF.md")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--layered-report", action="append", type=Path, default=[])
    parser.add_argument("--sidecar", type=Path, default=ROOT / "qa" / "_visual_auditor_spec" / "introspection.json")
    parser.add_argument("--objective", default="", help="Declared objective, e.g. 'hardening-qa'.")
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--skip-anti-fraud", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = audit(
        base=args.base,
        handoff=args.handoff,
        bundle=args.bundle,
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
    print(f"Bundle keys: {len(result.bundle_keys)}")
    if result.bundle_keys:
        for key in result.bundle_keys:
            print(f"  - {key}")
    print(f"Validated commits: {len(result.validated_commits)}")
    for commit in result.validated_commits:
        print(f"  - {commit}")
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
