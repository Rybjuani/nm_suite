#!/usr/bin/env python3
"""Measure, close, refresh, or revoke one visual surface.

The active v2 evidence record is the only closure authority. This module is
the only writer of active records and always asks ``closure_policy.decide``
before publishing a closure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    from qa.closure_policy import (
        DETERMINISM_CHANGED_RATIO_LIMIT,
        DETERMINISM_SCHEMA,
        STATE_ASSERTION_SCHEMA,
        VAS_SUMMARY_SCHEMA,
        decide,
    )
    from qa.hash_utils import sha256_binary, sha256_canonical_json, sha256_text
    from qa.render_handoff import load_active_records, render_handoff
    from qa.surface_scope import (
        CANONICAL_MANIFEST,
        ROOT,
        build_source_scope,
        is_source_scope_stale,
        manifest_key,
        manifest_keys,
    )
except ModuleNotFoundError:  # direct ``python qa/close_visual_key.py`` execution
    from closure_policy import (  # type: ignore[no-redef]
        DETERMINISM_CHANGED_RATIO_LIMIT,
        DETERMINISM_SCHEMA,
        STATE_ASSERTION_SCHEMA,
        VAS_SUMMARY_SCHEMA,
        decide,
    )
    from hash_utils import sha256_binary, sha256_canonical_json, sha256_text  # type: ignore[no-redef]
    from render_handoff import load_active_records, render_handoff  # type: ignore[no-redef]
    from surface_scope import (  # type: ignore[no-redef]
        CANONICAL_MANIFEST,
        ROOT,
        build_source_scope,
        is_source_scope_stale,
        manifest_key,
        manifest_keys,
    )


HANDOFF = Path("VISUAL_REPAIR_HANDOFF.md")
EVIDENCE_SCHEMA = "nm_suite.evidence_record.v2"
EVIDENCE_DIR = Path("docs") / "closure_evidence"
ACTIVE_DIR = EVIDENCE_DIR / "active"
REVOKED_DIR = ACTIVE_DIR / "revoked"
PENDING_DIR = Path("reports") / "qa" / "visual_closure_pending"
PENDING_SCHEMA = "nm_suite.pending_closure.v1"
REVOCATION_SCHEMA = "nm_suite.revocation.v1"
CANONICAL_DIR = Path("qa") / "_mockup_canonical"
DEFAULT_CAPTURE_DIR = Path("qa") / "_captures_v8"
DEFAULT_REPORT_DIR = Path("reports") / "qa" / "visual_closure"
MODAL_AUDIT_TOOL = Path("tools") / "qa" / "audit_modal_backdrop_blur.py"
SCOPED_STATUS_PATHS = (
    "app",
    "hub",
    "shared",
    "assets",
    "qa",
    "tools/qa",
    EVIDENCE_DIR.as_posix(),
    HANDOFF.as_posix(),
    ".github/workflows",
    ".github/CODEOWNERS",
)
MEASUREMENT_TOOL_PATHS = (
    "qa/approval_verifier.py",
    "qa/anti_fraud_scan.py",
    "qa/capture_v8.py",
    "qa/closure_policy.py",
    "qa/hash_utils.py",
    "qa/layered_visual_compare.py",
    "qa/odiff_runner.py",
    "qa/state_probes.py",
    "qa/surface_scope.py",
    "qa/vas_engine.py",
    "qa/vas_gate.py",
    "qa/vas_introspect.py",
    "tools/qa/audit_modal_backdrop_blur.py",
)
KEY_RE = re.compile(r"(?P<app>suite|hub):(?P<view>[^@\s`\"'\]\)]+)@(?P<theme>light|dark)")
VOLATILE_JSON_KEYS = {
    "generated_at",
    "captured_at",
    "elapsed_seconds",
    "elapsed_ms",
    "duration",
    "duration_seconds",
    "time",
    "cwd",
    "output_dir",
    "command",
    "command_args",
    "argv",
    "capture_path",
    "capture_script",
    "capture_manifest",
    "introspection_sidecar",
    "introspection_entry_id",
    "matrix_paths",
    "git_branch",
    "git_tracked_dirty",
    "tracked_dirty",
    "tracked_status",
    "actual_dir",
    "canonical_dir",
}


class ClosureError(Exception):
    exit_code = 1


class PreflightError(ClosureError):
    exit_code = 2


class GateError(ClosureError):
    exit_code = 1


class PolicyError(GateError):
    def __init__(self, reasons: Iterable[str], candidate: "EvidenceBuild | None" = None):
        self.reasons = list(reasons)
        self.candidate = candidate
        super().__init__("closure_policy_blocked: " + ", ".join(self.reasons))


class ApprovalRequired(PolicyError):
    exit_code = 3

    def __init__(self, reasons: Iterable[str], candidate: "EvidenceBuild", pending_path: Path):
        self.pending_path = pending_path
        super().__init__(reasons, candidate)


@dataclass(frozen=True)
class ParsedKey:
    key: str
    app: str
    view: str
    theme: str


@dataclass(frozen=True)
class EvidenceBuild:
    record: dict[str, Any]
    record_sha256: str
    record_path: Path


@dataclass(frozen=True)
class ReopenResult:
    key: str
    revoked_evidence: str
    revoked_record_path: Path


@dataclass(frozen=True)
class RefreshResult:
    refreshed: tuple[str, ...]
    reopened: tuple[str, ...]
    pending: tuple[Path, ...] = ()


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _print_process_failure(label: str, proc: subprocess.CompletedProcess[str]) -> None:
    print(f"{label} failed with exit {proc.returncode}", file=sys.stderr)
    if proc.stdout:
        print(proc.stdout.strip(), file=sys.stderr)
    if proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)


def parse_key(key: str) -> ParsedKey:
    match = KEY_RE.fullmatch((key or "").strip())
    if not match:
        raise PreflightError(f"invalid_key: {key}")
    return ParsedKey(
        key=key.strip(),
        app=match.group("app"),
        view=match.group("view"),
        theme=match.group("theme"),
    )


def key_safe(key: str) -> str:
    return key.replace(":", "_").replace("@", "-")


def canonical_record_sha256(record: Mapping[str, Any]) -> str:
    return sha256_canonical_json(dict(record))


def sha256_file(path: Path) -> str:
    """Compatibility alias for byte-exact evidence hashing."""

    return sha256_binary(path)


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_json(child)
            for key, child in value.items()
            if key not in VOLATILE_JSON_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_json(child) for child in value]
    return value


def stable_json_file_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return sha256_canonical_json(_sanitize_json(payload))


def _repo_arg_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def git_rev_parse(repo_root: Path, revision: str = "HEAD") -> str:
    proc = _run(["git", "rev-parse", "--verify", f"{revision}^{{commit}}"], cwd=repo_root)
    if proc.returncode != 0:
        raise PreflightError(f"invalid_git_revision: {revision}")
    return proc.stdout.strip()


def ensure_clean_for_closure(repo_root: Path) -> None:
    proc = _run(["git", "status", "--porcelain", "--", *SCOPED_STATUS_PATHS], cwd=repo_root)
    if proc.returncode != 0:
        raise PreflightError("git_status_failed")
    if proc.stdout.strip():
        raise PreflightError("dirty_working_tree")


def active_record_path(key: str) -> Path:
    return ACTIVE_DIR / f"{key_safe(key)}.json"


def resolve_target_set(
    repo_root: Path,
    explicit: Iterable[str] | None = None,
) -> set[str]:
    if explicit is not None:
        values = [parse_key(key).key for key in explicit]
        if len(values) != len(set(values)):
            raise PreflightError("duplicate_target_key")
        target = set(values)
        if not target:
            raise PreflightError("empty_target_set")
        unknown = target - set(manifest_keys(repo_root))
        if unknown:
            raise PreflightError(f"target_key_not_in_manifest: {', '.join(sorted(unknown))}")
        return target
    try:
        from qa.target_scope import resolve_all_open
    except ModuleNotFoundError:
        from target_scope import resolve_all_open
    handoff_path = repo_root / HANDOFF
    if not handoff_path.exists():
        raise PreflightError("missing_handoff")
    target = set(resolve_all_open(handoff_path.read_text(encoding="utf-8")))
    if not target:
        raise PreflightError("empty_target_set")
    unknown = target - set(manifest_keys(repo_root))
    if unknown:
        raise PreflightError(f"target_key_not_in_manifest: {', '.join(sorted(unknown))}")
    return target


def _key_from_capture_result(result: Mapping[str, Any]) -> str:
    for field in ("surface_key", "key"):
        value = result.get(field)
        if isinstance(value, str) and value:
            return value
    app, view, theme = result.get("app"), result.get("view"), result.get("theme")
    if all(isinstance(part, str) and part for part in (app, view, theme)):
        return f"{app}:{view}@{theme}"
    return ""


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid_{label}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"invalid_{label}_root")
    return value


def _capture_result(manifest_path: Path, key: str) -> dict[str, Any]:
    manifest = _load_json_object(manifest_path, "capture_manifest")
    matches = [
        result
        for result in manifest.get("results", [])
        if isinstance(result, dict) and _key_from_capture_result(result) == key
    ]
    if len(matches) != 1:
        raise GateError("capture_manifest_missing_or_duplicate_key")
    return matches[0]


def _capture_sidecar_path(capture_dir: Path, result: Mapping[str, Any]) -> Path:
    provenance = result.get("provenance")
    if isinstance(provenance, Mapping):
        value = provenance.get("introspection_sidecar")
        if isinstance(value, str) and value.strip():
            candidate = Path(value)
            if candidate.is_absolute():
                return candidate
            return capture_dir.parent / "_visual_auditor_spec" / candidate.name
    return capture_dir.parent / "_visual_auditor_spec" / "introspection.json"


def locate_capture_artifacts(capture_dir: Path, key: str) -> tuple[Path, Path, Path]:
    manifest_path = capture_dir / "CAPTURE_MANIFEST.json"
    if not manifest_path.exists():
        raise GateError("missing_capture_manifest")
    result = _capture_result(manifest_path, key)
    filename = result.get("file")
    png_path = capture_dir / str(filename) if filename else None
    provenance = result.get("provenance")
    if isinstance(provenance, Mapping) and isinstance(provenance.get("capture_path"), str):
        candidate = Path(str(provenance["capture_path"]))
        if candidate.exists():
            png_path = candidate
    if png_path is None or not png_path.exists():
        raise GateError("missing_capture_png")
    sidecar_path = _capture_sidecar_path(capture_dir, result)
    if not sidecar_path.exists():
        raise GateError("missing_vas_sidecar")
    return manifest_path, png_path, sidecar_path


def load_canonical_manifest(repo_root: Path) -> dict[str, Any]:
    return _load_json_object(repo_root / CANONICAL_MANIFEST, "canonical_manifest")


def _canonical_capture(repo_root: Path, key: str) -> dict[str, Any]:
    matches = [
        capture
        for capture in load_canonical_manifest(repo_root).get("captures", [])
        if isinstance(capture, dict) and manifest_key(capture) == key
    ]
    if len(matches) != 1:
        raise PreflightError("key_not_in_canonical_manifest")
    return matches[0]


def canonical_png_path(repo_root: Path, key: str) -> Path:
    capture = _canonical_capture(repo_root, key)
    path = repo_root / CANONICAL_DIR / str(capture.get("file", ""))
    if not path.is_file():
        raise GateError("missing_canonical_png")
    return path


def is_modal_key(repo_root: Path, key: str) -> bool:
    capture = _canonical_capture(repo_root, key)
    return capture.get("is_modal") is True or str(capture.get("surface", "")).lower() in {
        "modal",
        "window_modal",
    }


def _modal_back_screen_key(repo_root: Path, key: str) -> str | None:
    value = _canonical_capture(repo_root, key).get("back_screen_key")
    return value if isinstance(value, str) and value else None


def run_anti_fraud(repo_root: Path, output_path: Path | None = None) -> dict[str, Any]:
    if output_path is None:
        with tempfile.TemporaryDirectory(prefix="nm_antifraud_") as temp:
            return run_anti_fraud(repo_root, Path(temp) / "ANTIFRAUD.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proc = _run(
        [
            sys.executable,
            "qa/anti_fraud_scan.py",
            "--mode",
            "all",
            "--json",
            str(output_path),
        ],
        cwd=repo_root,
        timeout=180,
    )
    if not output_path.exists():
        _print_process_failure("anti_fraud --mode all", proc)
        raise GateError("missing_antifraud_summary")
    return _load_json_object(output_path, "antifraud_summary")


def run_capture(repo_root: Path, parsed: ParsedKey, capture_dir: Path) -> None:
    env = os.environ.copy()
    env["NM_VAS_INTROSPECT"] = "1"
    proc = _run(
        [
            sys.executable,
            "qa/capture_v8.py",
            "--app",
            parsed.app,
            "--view",
            parsed.view,
            "--theme",
            parsed.theme,
            "--out-dir",
            _repo_arg_path(repo_root, capture_dir),
            "--no-clean",
        ],
        cwd=repo_root,
        env=env,
        timeout=300,
    )
    if proc.returncode != 0:
        _print_process_failure("capture_v8", proc)
        raise GateError("capture_failed")


def run_capture_for_key(repo_root: Path, key: str, capture_dir: Path) -> None:
    run_capture(repo_root, parse_key(key), capture_dir)


def _merge_back_screen_capture(capture_dir: Path, back_capture_dir: Path) -> None:
    back_manifest_path = back_capture_dir / "CAPTURE_MANIFEST.json"
    back_manifest = _load_json_object(back_manifest_path, "back_capture_manifest")
    back_results = [result for result in back_manifest.get("results", []) if isinstance(result, dict)]
    for result in back_results:
        filename = result.get("file")
        if filename and (back_capture_dir / str(filename)).exists():
            shutil.copy2(back_capture_dir / str(filename), capture_dir / str(filename))

    manifest_path = capture_dir / "CAPTURE_MANIFEST.json"
    manifest = _load_json_object(manifest_path, "capture_manifest")
    results = manifest.setdefault("results", [])
    if not isinstance(results, list):
        raise GateError("invalid_capture_manifest_results")
    existing = {_key_from_capture_result(result) for result in results if isinstance(result, dict)}
    for result in back_results:
        if _key_from_capture_result(result) not in existing:
            results.append(result)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _ensure_modal_backdrop_capture(repo_root: Path, parsed: ParsedKey, capture_dir: Path) -> None:
    back_key = _modal_back_screen_key(repo_root, parsed.key)
    if not back_key:
        raise GateError("modal_missing_back_screen_key")
    with tempfile.TemporaryDirectory(prefix="nm_modal_back_screen_") as temp:
        back_capture_dir = Path(temp) / "captures"
        run_capture_for_key(repo_root, back_key, back_capture_dir)
        _merge_back_screen_capture(capture_dir, back_capture_dir)


def run_comparator(
    repo_root: Path,
    parsed: ParsedKey,
    capture_dir: Path,
    report_dir: Path,
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    proc = _run(
        [
            sys.executable,
            "qa/layered_visual_compare.py",
            "--canonical",
            str(CANONICAL_DIR),
            "--actual",
            _repo_arg_path(repo_root, capture_dir),
            "--out-dir",
            _repo_arg_path(repo_root, report_dir),
            "--key",
            parsed.key,
        ],
        cwd=repo_root,
        timeout=300,
    )
    report_path = report_dir / "LAYERED_VISUAL_REPORT.json"
    if not report_path.exists():
        _print_process_failure("layered_visual_compare", proc)
        raise GateError("missing_layered_report")
    return report_path


def run_vas(repo_root: Path, key: str, sidecar_path: Path) -> bool:
    proc = _run(
        [sys.executable, "qa/vas_gate.py", "--sidecar", str(sidecar_path), "--key", key],
        cwd=repo_root,
        timeout=120,
    )
    return proc.returncode == 0


def run_preflight(
    *,
    repo_root: Path,
    key: str,
    capture_dir: Path | None = None,
    report_dir: Path | None = None,
) -> None:
    """Compatibility guard that measures outside scoped paths by default.

    It never creates closure evidence and is intentionally absent from the v2
    public CLI. The authoritative close still performs both fresh captures in
    its detached worktree.
    """

    parsed = parse_key(key)

    def measure(cap: Path, report: Path) -> None:
        report.mkdir(parents=True, exist_ok=True)
        run_anti_fraud(repo_root)
        run_capture(repo_root, parsed, cap)
        _manifest, _png, sidecar = locate_capture_artifacts(cap, parsed.key)
        run_comparator(repo_root, parsed, cap, report)
        run_vas(repo_root, parsed.key, sidecar)

    if capture_dir is not None or report_dir is not None:
        measure(capture_dir or (repo_root / DEFAULT_CAPTURE_DIR), report_dir or (repo_root / DEFAULT_REPORT_DIR))
        return
    with tempfile.TemporaryDirectory(prefix="nm_closure_preflight_") as temp:
        measure(Path(temp) / "captures", Path(temp) / "report")


def _sidecar_entry(sidecar_path: Path, key: str) -> dict[str, Any]:
    try:
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid_vas_sidecar: {exc}") from exc
    if not isinstance(payload, list):
        raise GateError("invalid_vas_sidecar_root")
    matches = [entry for entry in payload if isinstance(entry, dict) and entry.get("surface_key") == key]
    if len(matches) != 1:
        raise GateError("vas_sidecar_missing_or_duplicate_key")
    return matches[0]


def build_vas_summary(
    key: str,
    sidecar_path: Path,
    capture_result: Mapping[str, Any],
    gate_pass: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    entry = _sidecar_entry(sidecar_path, key)
    divergences = entry.get("divergences")
    if not isinstance(divergences, list):
        divergences = []
    high_count = sum(
        1 for item in divergences if isinstance(item, Mapping) and item.get("severity") == "high"
    )
    medium_count = sum(
        1
        for item in divergences
        if isinstance(item, Mapping) and item.get("severity") == "medium"
    )
    fail_count = entry.get("fail_count") if isinstance(entry.get("fail_count"), int) else -1
    capture_valid = (
        capture_result.get("success") is True
        and capture_result.get("technical_capture_valid") is True
        and capture_result.get("state_evidence_valid") is True
        and capture_result.get("capture_status") == "CAPTURED_VALID"
    )
    summary = {
        "schema": VAS_SUMMARY_SCHEMA,
        "key": key,
        "pass": bool(
            gate_pass
            and fail_count == 0
            and high_count == 0
            and medium_count == 0
            and capture_valid
        ),
        "fail_count": fail_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "capture_valid": capture_valid,
    }
    state_assertion = entry.get("state_assertion")
    if state_assertion is not None and not isinstance(state_assertion, dict):
        state_assertion = {
            "schema": STATE_ASSERTION_SCHEMA,
            "key": key,
            "pass": False,
            "error": "invalid_state_assertion",
        }
    return summary, state_assertion


def run_modal_audit(
    repo_root: Path,
    parsed: ParsedKey,
    capture_dir: Path,
    report_dir: Path,
) -> Path:
    audit_report_dir = report_dir / f"modal_audit_{key_safe(parsed.key)}"
    audit_report_dir.mkdir(parents=True, exist_ok=True)
    proc = _run(
        [
            sys.executable,
            str(MODAL_AUDIT_TOOL),
            "--key",
            parsed.key,
            "--canonical",
            str(CANONICAL_DIR),
            "--actual",
            _repo_arg_path(repo_root, capture_dir),
            "--out-dir",
            _repo_arg_path(repo_root, audit_report_dir),
        ],
        cwd=repo_root,
        timeout=120,
    )
    report_path = audit_report_dir / "AUDIT.json"
    if not report_path.exists():
        _print_process_failure("modal_backdrop_blur_audit", proc)
        raise GateError("missing_modal_audit_report")
    return report_path


def _modal_summary(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _load_json_object(path, "modal_audit")
    return {
        "pass": payload.get("summary", {}).get("test_blur_pass") is True,
        "summary": payload.get("summary", {}),
    }


def measurement_tool_hashes(repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in MEASUREMENT_TOOL_PATHS:
        source = repo_root / path
        if not source.is_file():
            raise GateError(f"missing_measurement_tool: {path}")
        hashes[path] = sha256_text(source)
    return hashes


def thresholds_sha256() -> str:
    try:
        from qa.layered_visual_compare import LayeredThresholds
    except ModuleNotFoundError:
        from layered_visual_compare import LayeredThresholds
    return sha256_canonical_json(LayeredThresholds().to_dict())


def _determinism_summary(
    key: str,
    first_manifest: Path,
    second_manifest: Path,
    first_png: Path,
    second_png: Path,
) -> dict[str, Any]:
    try:
        from qa.layered_visual_compare import determinism_changed_ratio
    except ModuleNotFoundError:
        from layered_visual_compare import determinism_changed_ratio
    first = _capture_result(first_manifest, key).get("provenance")
    second = _capture_result(second_manifest, key).get("provenance")
    first = first if isinstance(first, Mapping) else {}
    second = second if isinstance(second, Mapping) else {}
    ratio = determinism_changed_ratio(first_png, second_png)
    return {
        "schema": DETERMINISM_SCHEMA,
        "key": key,
        "pass": ratio < DETERMINISM_CHANGED_RATIO_LIMIT,
        "changed_ratio": ratio,
        "limit": DETERMINISM_CHANGED_RATIO_LIMIT,
        "first_run_id": first.get("introspection_entry_id"),
        "second_run_id": second.get("introspection_entry_id"),
        "first_git_head": first.get("git_head"),
        "second_git_head": second.get("git_head"),
    }


def _human_review(approval: object) -> dict[str, Any]:
    source = approval if isinstance(approval, Mapping) else {}
    return {
        "approval_url": source.get("approval_url"),
        "comment_id": source.get("comment_id"),
        "author": source.get("author"),
    }


def _build_record(
    *,
    repo_root: Path,
    parsed: ParsedKey,
    commit_head: str,
    capture_manifest: Path,
    capture_png: Path,
    report_path: Path,
    sidecar_path: Path,
    modal_audit_path: Path | None,
    policy_report: dict[str, Any],
    vas_summary: dict[str, Any],
    antifraud: dict[str, Any],
    determinism: dict[str, Any],
    state_assertion: dict[str, Any] | None,
    modal_audit: dict[str, Any] | None,
    approval: object,
    target_set: set[str],
    operation: Mapping[str, Any],
    allow: bool,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "schema": EVIDENCE_SCHEMA,
        "key": parsed.key,
        "commit_head": commit_head,
        "result": "PASS" if allow else "BLOCKED",
        "canonical_png_sha256": sha256_binary(canonical_png_path(repo_root, parsed.key)),
        "capture_png_sha256": sha256_binary(capture_png),
        "manifest_sha256": sha256_text(repo_root / CANONICAL_MANIFEST),
        "capture_manifest_sha256": stable_json_file_sha256(capture_manifest),
        "tool_hashes": measurement_tool_hashes(repo_root),
        "thresholds_sha256": thresholds_sha256(),
        "source_scope": build_source_scope(parsed.key, repo_root=repo_root, revision=commit_head),
        "report_sha256": policy_report["report_sha256"],
        "sidecar_sha256": stable_json_file_sha256(sidecar_path),
        "modal_audit_sha256": (
            stable_json_file_sha256(modal_audit_path) if modal_audit_path is not None else None
        ),
        "report": policy_report,
        "vas_summary": vas_summary,
        "antifraud": antifraud,
        "determinism": determinism,
        "state_assertion": state_assertion,
        "modal_audit": modal_audit,
        "human_review": _human_review(approval),
        "target_set": sorted(target_set),
        "policy": {"allow": allow, "reasons": list(reasons)},
        "operation": dict(operation),
        "command_spec": {
            "capture": {
                "tool": "qa/capture_v8.py",
                "app": parsed.app,
                "view": parsed.view,
                "theme": parsed.theme,
                "vas_introspect": True,
                "runs": 2,
            },
            "compare": {
                "tool": "qa/layered_visual_compare.py",
                "canonical": CANONICAL_DIR.as_posix(),
                "scope": parsed.key,
            },
        },
    }


def regenerate_record_for_key(
    *,
    repo_root: Path,
    key: str,
    commit_head: str,
    target_set: Iterable[str],
    approval: object = None,
    approval_resolver: Callable[[str, str], object] | None = None,
    capture_dir: Path | None = None,
    second_capture_dir: Path | None = None,
    report_dir: Path | None = None,
    operation: Mapping[str, Any] | None = None,
) -> EvidenceBuild:
    parsed = parse_key(key)
    if parsed.key not in set(manifest_keys(repo_root)):
        raise PreflightError("key_not_in_canonical_manifest")
    target_values = [parse_key(value).key for value in target_set]
    if len(target_values) != len(set(target_values)):
        raise PreflightError("duplicate_target_key")
    targets = set(target_values)
    unknown_targets = targets - set(manifest_keys(repo_root))
    if unknown_targets:
        raise PreflightError(
            f"target_key_not_in_manifest: {', '.join(sorted(unknown_targets))}"
        )
    if parsed.key not in targets:
        raise PreflightError("key_outside_target_set")

    capture_dir = capture_dir or (repo_root / DEFAULT_CAPTURE_DIR)
    report_dir = report_dir or (repo_root / DEFAULT_REPORT_DIR / key_safe(parsed.key))
    report_dir.mkdir(parents=True, exist_ok=True)
    temp_second: tempfile.TemporaryDirectory[str] | None = None
    if second_capture_dir is None:
        temp_second = tempfile.TemporaryDirectory(prefix="nm_determinism_second_")
        second_capture_dir = Path(temp_second.name) / "captures"
    try:
        antifraud = run_anti_fraud(repo_root, report_dir / "ANTIFRAUD.json")
        run_capture(repo_root, parsed, capture_dir)
        modal_required = is_modal_key(repo_root, parsed.key)
        if modal_required:
            _ensure_modal_backdrop_capture(repo_root, parsed, capture_dir)
        first_manifest, first_png, first_sidecar = locate_capture_artifacts(
            capture_dir, parsed.key
        )
        first_result = _capture_result(first_manifest, parsed.key)

        run_capture(repo_root, parsed, second_capture_dir)
        second_manifest, second_png, _second_sidecar = locate_capture_artifacts(
            second_capture_dir, parsed.key
        )
        determinism = _determinism_summary(
            parsed.key, first_manifest, second_manifest, first_png, second_png
        )

        report_path = run_comparator(repo_root, parsed, capture_dir, report_dir)
        gate_pass = run_vas(repo_root, parsed.key, first_sidecar)
        vas_summary, state_assertion = build_vas_summary(
            parsed.key, first_sidecar, first_result, gate_pass
        )
        modal_audit_path = (
            run_modal_audit(repo_root, parsed, capture_dir, report_dir)
            if modal_required
            else None
        )
        modal_audit = _modal_summary(modal_audit_path)

        report = _load_json_object(report_path, "layered_report")
        report_sha = stable_json_file_sha256(report_path)
        policy_report = dict(report)
        policy_report["report_sha256"] = report_sha
        policy_report["modal_audit_required"] = modal_required
        policy_report["modal_audit"] = modal_audit
        if approval_resolver is not None:
            approval = approval_resolver(parsed.key, report_sha)

        allow, reasons = decide(
            policy_report,
            vas_summary,
            antifraud,
            determinism,
            state_assertion,
            approval,
            targets,
        )
        record = _build_record(
            repo_root=repo_root,
            parsed=parsed,
            commit_head=commit_head,
            capture_manifest=first_manifest,
            capture_png=first_png,
            report_path=report_path,
            sidecar_path=first_sidecar,
            modal_audit_path=modal_audit_path,
            policy_report=policy_report,
            vas_summary=vas_summary,
            antifraud=antifraud,
            determinism=determinism,
            state_assertion=state_assertion,
            modal_audit=modal_audit,
            approval=approval,
            target_set=targets,
            operation=operation or {"kind": "close"},
            allow=allow,
            reasons=reasons,
        )
        build = EvidenceBuild(
            record=record,
            record_sha256=canonical_record_sha256(record),
            record_path=active_record_path(parsed.key),
        )
        if not allow:
            raise PolicyError(reasons, build)
        return build
    finally:
        if temp_second is not None:
            temp_second.cleanup()


@contextmanager
def temporary_worktree(repo_root: Path, commit: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="nm_visual_worktree_") as temp:
        temp_root = Path(temp).resolve()
        worktree = temp_root / "worktree"
        proc = _run(["git", "worktree", "add", "--detach", str(worktree), commit], cwd=repo_root)
        if proc.returncode != 0:
            _print_process_failure("git worktree add", proc)
            raise GateError("worktree_add_failed")
        try:
            yield worktree
        finally:
            remove = _run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root)
            if remove.returncode != 0 and worktree.exists() and temp_root in worktree.resolve().parents:
                shutil.rmtree(worktree, ignore_errors=True)


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(
        json.dumps(dict(payload), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    tmp.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _revocation(record: Mapping[str, Any], reason: str) -> tuple[Path, dict[str, Any]]:
    record_sha = canonical_record_sha256(record)
    key = str(record.get("key", ""))
    commit = str(record.get("commit_head", "unknown"))
    path = REVOKED_DIR / f"{key_safe(key)}-{commit[:12]}-{record_sha[:12]}.json"
    return path, {
        "schema": REVOCATION_SCHEMA,
        "key": key,
        "reason": reason,
        "revoked_record_sha256": record_sha,
        "revoked_record": dict(record),
    }


def _publish_desired_state(
    repo_root: Path,
    desired_records: Mapping[str, Mapping[str, Any]],
    revocations: Iterable[tuple[Mapping[str, Any], str]] = (),
) -> list[Path]:
    rendered = render_handoff(repo_root, active_records=desired_records)
    current = load_active_records(repo_root)
    active_paths = {
        repo_root / active_record_path(key) for key in set(current) | set(desired_records)
    }
    revocation_payloads = [_revocation(record, reason) for record, reason in revocations]
    changed_paths = [*active_paths, *(repo_root / path for path, _ in revocation_payloads), repo_root / HANDOFF]
    snapshots = {path: path.read_bytes() if path.exists() else None for path in changed_paths}
    written_revocations: list[Path] = []
    try:
        for key in set(current) - set(desired_records):
            path = repo_root / active_record_path(key)
            if path.exists():
                path.unlink()
        for key, record in desired_records.items():
            _write_json_atomic(repo_root / active_record_path(key), record)
        for rel_path, payload in revocation_payloads:
            path = repo_root / rel_path
            if path.exists():
                raise PreflightError(f"revocation_already_exists: {rel_path.as_posix()}")
            _write_json_atomic(path, payload)
            written_revocations.append(rel_path)
        _write_text_atomic(repo_root / HANDOFF, rendered)
    except Exception:
        for path, content in snapshots.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        raise
    return written_revocations


def _write_pending(repo_root: Path, build: EvidenceBuild) -> Path:
    candidate = dict(build.record)
    payload = {
        "schema": PENDING_SCHEMA,
        "candidate_sha256": canonical_record_sha256(candidate),
        "candidate": candidate,
    }
    path = (
        repo_root
        / PENDING_DIR
        / key_safe(str(candidate["key"]))
        / f"{candidate['report_sha256']}.json"
    )
    _write_json_atomic(path, payload)
    return path


def _approval_only(reasons: Iterable[str]) -> bool:
    values = list(reasons)
    approval_reasons = {
        "near_threshold_requires_verified_approval",
        "approval_evidence_mismatch",
        "approval_approval_url_invalid",
        "approval_comment_id_invalid",
        "approval_author_invalid",
    }
    return bool(values) and all(reason in approval_reasons for reason in values)


def close_visual_key(
    *,
    key: str,
    repo_root: Path = ROOT,
    dry_run: bool = False,
    capture_dir: Path | None = None,
    second_capture_dir: Path | None = None,
    report_dir: Path | None = None,
    target_set: Iterable[str] | None = None,
    approval: object = None,
    approval_resolver: Callable[[str, str], object] | None = None,
) -> EvidenceBuild:
    repo_root = repo_root.resolve()
    parsed = parse_key(key)
    ensure_clean_for_closure(repo_root)
    if (repo_root / active_record_path(parsed.key)).exists():
        raise PreflightError("key_already_closed")
    targets = resolve_target_set(repo_root, target_set)
    if parsed.key not in targets:
        raise PreflightError("key_outside_target_set")
    commit_head = git_rev_parse(repo_root)

    try:
        if capture_dir is None and report_dir is None and second_capture_dir is None:
            with temporary_worktree(repo_root, commit_head) as worktree:
                build = regenerate_record_for_key(
                    repo_root=worktree,
                    key=parsed.key,
                    commit_head=commit_head,
                    target_set=targets,
                    approval=approval,
                    approval_resolver=approval_resolver,
                )
        else:
            build = regenerate_record_for_key(
                repo_root=repo_root,
                key=parsed.key,
                commit_head=commit_head,
                target_set=targets,
                approval=approval,
                approval_resolver=approval_resolver,
                capture_dir=capture_dir,
                second_capture_dir=second_capture_dir,
                report_dir=report_dir,
            )
    except PolicyError as exc:
        if exc.candidate is not None and _approval_only(exc.reasons):
            pending = _write_pending(repo_root, exc.candidate)
            raise ApprovalRequired(exc.reasons, exc.candidate, pending) from exc
        raise

    if dry_run:
        return build
    desired = load_active_records(repo_root)
    desired[parsed.key] = build.record
    _publish_desired_state(repo_root, desired)
    return build


def reopen_visual_key(
    *,
    key: str,
    reason: str,
    repo_root: Path = ROOT,
) -> ReopenResult:
    repo_root = repo_root.resolve()
    parsed = parse_key(key)
    reason = (reason or "").strip()
    if not reason:
        raise PreflightError("missing_reopen_reason")
    ensure_clean_for_closure(repo_root)
    records = load_active_records(repo_root)
    record = records.get(parsed.key)
    if record is None:
        raise PreflightError("key_not_closed")
    if record.get("schema") != EVIDENCE_SCHEMA or record.get("key") != parsed.key:
        raise PreflightError("invalid_active_record")
    evidence = canonical_record_sha256(record)
    del records[parsed.key]
    paths = _publish_desired_state(repo_root, records, [(record, reason)])
    return ReopenResult(parsed.key, evidence, paths[0])


def refresh_evidence(
    *,
    keys: Iterable[str],
    repo_root: Path = ROOT,
    approval: object = None,
    approval_resolver: Callable[[str, str], object] | None = None,
) -> RefreshResult:
    repo_root = repo_root.resolve()
    selected = tuple(dict.fromkeys(parse_key(key).key for key in keys))
    if not selected:
        raise PreflightError("empty_refresh_set")
    ensure_clean_for_closure(repo_root)
    records = load_active_records(repo_root)
    missing = [key for key in selected if key not in records]
    if missing:
        raise PreflightError(f"refresh_key_not_closed: {', '.join(missing)}")
    commit_head = git_rev_parse(repo_root)
    refreshed: list[str] = []
    reopened: list[str] = []
    pending: list[Path] = []
    revocations: list[tuple[Mapping[str, Any], str]] = []
    with temporary_worktree(repo_root, commit_head) as worktree:
        for key in selected:
            try:
                build = regenerate_record_for_key(
                    repo_root=worktree,
                    key=key,
                    commit_head=commit_head,
                    target_set=selected,
                    approval=approval,
                    approval_resolver=approval_resolver,
                    operation={
                        "kind": "refresh",
                        "refreshed_from_commit": records[key].get("commit_head"),
                        "refreshed_from_evidence": canonical_record_sha256(records[key]),
                    },
                )
            except PolicyError as exc:
                if _approval_only(exc.reasons):
                    # Aprobación externa es el ÚNICO bloqueo: la key no se
                    # reabre. Queda el record viejo activo (sigue stale) y un
                    # candidato inmutable esperando el resume con approval.
                    if exc.candidate is None:
                        raise
                    pending.append(_write_pending(repo_root, exc.candidate))
                    continue
                old = records.pop(key)
                reason = "stale_fail:" + ",".join(exc.reasons)
                revocations.append((old, reason))
                reopened.append(key)
            else:
                records[key] = build.record
                refreshed.append(key)
    _publish_desired_state(repo_root, records, revocations)
    return RefreshResult(tuple(refreshed), tuple(reopened), tuple(pending))


def stale_active_keys(repo_root: Path = ROOT) -> tuple[str, ...]:
    records = load_active_records(repo_root)
    return tuple(
        sorted(
            key
            for key, record in records.items()
            if is_source_scope_stale(record.get("source_scope"), key, repo_root=repo_root)
        )
    )


def _pending_provenance_is_current(candidate: Mapping[str, Any], repo_root: Path) -> bool:
    key = str(candidate.get("key", ""))
    try:
        expected = {
            "canonical_png_sha256": sha256_binary(canonical_png_path(repo_root, key)),
            "manifest_sha256": sha256_text(repo_root / CANONICAL_MANIFEST),
            "tool_hashes": measurement_tool_hashes(repo_root),
            "thresholds_sha256": thresholds_sha256(),
        }
    except (ClosureError, OSError, ValueError):
        return False
    if any(candidate.get(field) != value for field, value in expected.items()):
        return False
    report = candidate.get("report")
    if not isinstance(report, Mapping):
        return False
    return report.get("report_sha256") == candidate.get("report_sha256")


def resume_pending_closure(
    *,
    pending_path: Path,
    approval: object,
    repo_root: Path = ROOT,
) -> EvidenceBuild:
    repo_root = repo_root.resolve()
    ensure_clean_for_closure(repo_root)
    payload = _load_json_object(pending_path, "pending_closure")
    candidate = payload.get("candidate")
    if payload.get("schema") != PENDING_SCHEMA or not isinstance(candidate, dict):
        raise PreflightError("invalid_pending_closure")
    if canonical_record_sha256(candidate) != payload.get("candidate_sha256"):
        raise PreflightError("pending_closure_integrity_mismatch")
    key = parse_key(str(candidate.get("key", ""))).key
    if candidate.get("commit_head") != git_rev_parse(repo_root):
        raise PreflightError("pending_closure_commit_mismatch")
    if is_source_scope_stale(candidate.get("source_scope"), key, repo_root=repo_root):
        raise PreflightError("pending_closure_stale")
    if not _pending_provenance_is_current(candidate, repo_root):
        raise PreflightError("pending_closure_provenance_mismatch")
    targets = candidate.get("target_set")
    allow, reasons = decide(
        candidate.get("report"),
        candidate.get("vas_summary"),
        candidate.get("antifraud"),
        candidate.get("determinism"),
        candidate.get("state_assertion"),
        approval,
        targets,
    )
    if not allow:
        raise PolicyError(reasons)
    candidate["result"] = "PASS"
    candidate["human_review"] = _human_review(approval)
    candidate["policy"] = {"allow": True, "reasons": []}
    build = EvidenceBuild(
        record=candidate,
        record_sha256=canonical_record_sha256(candidate),
        record_path=active_record_path(key),
    )
    desired = load_active_records(repo_root)
    operation = candidate.get("operation")
    op_kind = operation.get("kind") if isinstance(operation, Mapping) else "close"
    if op_kind == "refresh":
        existing = desired.get(key)
        if existing is None:
            raise PreflightError("pending_refresh_key_not_closed")
        if canonical_record_sha256(existing) != operation.get("refreshed_from_evidence"):
            raise PreflightError("pending_refresh_source_mismatch")
    elif key in desired:
        raise PreflightError("key_already_closed")
    desired[key] = candidate
    _publish_desired_state(repo_root, desired)
    return build


def _keys_from_file(path: Path) -> tuple[str, ...]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            key = parse_key(value).key
            if key in keys:
                raise PreflightError(f"duplicate_target_key: {key}")
            keys.append(key)
    if not keys:
        raise PreflightError("empty_target_set")
    return tuple(keys)


def _approval_resolver_from_url(url: str | None, repo_root: Path) -> Callable[[str, str], object] | None:
    if not url:
        return None

    def resolve(key: str, report_sha256: str) -> object:
        try:
            from qa.approval_verifier import verify_approval
        except ModuleNotFoundError:
            from approval_verifier import verify_approval
        comment_match = re.search(r"#issuecomment-(\d+)$", url)
        owner_match = re.match(r"https://github\.com/([^/]+)/", url, flags=re.IGNORECASE)
        review = {
            "approval_url": url,
            "comment_id": int(comment_match.group(1)) if comment_match else None,
            "author": os.getenv("NM_VISUAL_APPROVAL_OWNER")
            or (owner_match.group(1) if owner_match else ""),
        }
        return verify_approval(
            review,
            key=key,
            report_sha256=report_sha256,
            git_cwd=repo_root,
        )

    return resolve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage v2 visual closure evidence.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--reopen", action="store_true")
    actions.add_argument("--refresh-evidence", action="store_true")
    actions.add_argument("--resume-pending", type=Path)
    parser.add_argument("--key")
    parser.add_argument("--reason")
    parser.add_argument("--stale", action="store_true")
    parser.add_argument("--keys", nargs="+")
    parser.add_argument("--target-set-file", type=Path)
    parser.add_argument("--approval-url")
    parser.add_argument("--dry-run", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    try:
        if args.reopen:
            if not args.key:
                parser.error("--reopen requires --key")
            result = reopen_visual_key(key=args.key, reason=args.reason or "")
            print(f"reopened: {result.key}")
            print(f"revoked-evidence: {result.revoked_evidence}")
            print(f"revoked-record: {result.revoked_record_path.as_posix()}")
            return 0
        if args.refresh_evidence:
            if args.stale == bool(args.keys):
                parser.error("--refresh-evidence requires exactly one of --stale or --keys")
            keys = stale_active_keys() if args.stale else tuple(args.keys or ())
            result = refresh_evidence(
                keys=keys,
                approval_resolver=_approval_resolver_from_url(args.approval_url, ROOT),
            )
            print(f"refreshed: {len(result.refreshed)}")
            print(f"reopened-stale-fail: {len(result.reopened)}")
            for pending_path in result.pending:
                print(f"pending-approval: {pending_path.as_posix()}", file=sys.stderr)
            return ApprovalRequired.exit_code if result.pending else 0
        if args.resume_pending:
            if not args.approval_url:
                parser.error("--resume-pending requires --approval-url")
            pending = _load_json_object(args.resume_pending, "pending_closure")
            candidate = pending.get("candidate", {})
            key = str(candidate.get("key", "")) if isinstance(candidate, Mapping) else ""
            report_sha = str(candidate.get("report_sha256", "")) if isinstance(candidate, Mapping) else ""
            resolver = _approval_resolver_from_url(args.approval_url, ROOT)
            assert resolver is not None
            build = resume_pending_closure(
                pending_path=args.resume_pending,
                approval=resolver(key, report_sha),
            )
        else:
            if not args.key:
                parser.error("closure requires --key")
            targets = _keys_from_file(args.target_set_file) if args.target_set_file else None
            build = close_visual_key(
                key=args.key,
                dry_run=args.dry_run,
                target_set=targets,
                approval_resolver=_approval_resolver_from_url(args.approval_url, ROOT),
            )
    except ApprovalRequired as exc:
        print(str(exc), file=sys.stderr)
        print(f"pending-approval: {exc.pending_path}", file=sys.stderr)
        return exc.exit_code
    except ClosureError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    print(f"closed: {build.record['key']}")
    print(f"evidence: {build.record_sha256}")
    print(f"evidence-record: {build.record_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
