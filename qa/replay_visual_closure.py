#!/usr/bin/env python3
"""Independent structural and full-regeneration visual-closure replay."""

from __future__ import annotations

import argparse
import ast
import hashlib
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
    from qa.approval_verifier import verify_approval
    from qa.closure_policy import (
        DETERMINISM_CHANGED_RATIO_LIMIT,
        DETERMINISM_SCHEMA,
        STATE_ASSERTION_SCHEMA,
        VAS_SUMMARY_SCHEMA,
        decide,
    )
    from qa.hash_utils import sha256_binary, sha256_canonical_json, sha256_text
    from qa.render_handoff import render_handoff
    from qa.surface_scope import (
        CANONICAL_MANIFEST,
        ROOT,
        is_source_scope_stale,
        manifest_key,
        manifest_keys,
        source_scope_matches_revision,
        unmapped_visual_sources,
    )
except ModuleNotFoundError:  # direct ``python qa/replay_visual_closure.py`` execution
    from approval_verifier import verify_approval  # type: ignore[no-redef]
    from closure_policy import (  # type: ignore[no-redef]
        DETERMINISM_CHANGED_RATIO_LIMIT,
        DETERMINISM_SCHEMA,
        STATE_ASSERTION_SCHEMA,
        VAS_SUMMARY_SCHEMA,
        decide,
    )
    from hash_utils import sha256_binary, sha256_canonical_json, sha256_text  # type: ignore[no-redef]
    from render_handoff import render_handoff  # type: ignore[no-redef]
    from surface_scope import (  # type: ignore[no-redef]
        CANONICAL_MANIFEST,
        ROOT,
        is_source_scope_stale,
        manifest_key,
        manifest_keys,
        source_scope_matches_revision,
        unmapped_visual_sources,
    )


EVIDENCE_SCHEMA = "nm_suite.evidence_record.v2"
ACTIVE_DIR = Path("docs") / "closure_evidence" / "active"
HANDOFF = Path("VISUAL_REPAIR_HANDOFF.md")
CANONICAL_DIR = Path("qa") / "_mockup_canonical"
MODAL_AUDIT_TOOL = Path("tools") / "qa" / "audit_modal_backdrop_blur.py"
EXPECTED_UNIVERSE_SIZE = 116
KEY_RE = re.compile(r"^(?P<app>suite|hub):(?P<view>[^@\s]+)@(?P<theme>light|dark)$")
RECORD_NAME_RE = re.compile(r"^(?P<app>suite|hub)_(?P<view>.+)-(?P<theme>light|dark)\.json$")
CHECKBOX_RE = re.compile(
    r"^\s*-\s*\[(?P<state>[xX ~])\]\s*`(?P<key>(?:suite|hub):[^`]+@(?:light|dark))`"
)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")
KERNEL_PATHS = (
    "qa/anti_fraud_scan.py",
    "qa/approval_verifier.py",
    "qa/capture_v8.py",
    "qa/close_visual_key.py",
    "qa/closure_policy.py",
    "qa/hash_utils.py",
    "qa/layered_visual_compare.py",
    "qa/odiff_runner.py",
    "qa/render_handoff.py",
    "qa/replay_visual_closure.py",
    "qa/spec_generator.py",
    "qa/specs/specs.json",
    "qa/state_probes.py",
    "qa/surface_scope.py",
    "qa/surface_notes.json",
    "qa/target_scope.py",
    "qa/vas_engine.py",
    "qa/vas_gate.py",
    "qa/vas_introspect.py",
    "qa/run_visual.ps1",
    "qa/_mockup_canonical/",
    "qa/pack canonico/",
    "tools/qa/",
    ".github/workflows/",
    ".github/CODEOWNERS",
)
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


@dataclass(frozen=True)
class ParsedKey:
    key: str
    app: str
    view: str
    theme: str


@dataclass(frozen=True)
class ReplayFailure:
    key: str
    reason: str


@dataclass(frozen=True)
class ReplayResult:
    mode: str
    active_records: int
    checked_keys: int
    replayed_keys: int
    failures: tuple[ReplayFailure, ...]

    @property
    def passed(self) -> bool:
        return not self.failures


def _run_text(
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


def _run_bytes(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, check=False)


def _normalize_path(path: str | Path) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def key_safe(key: str) -> str:
    return key.replace(":", "_").replace("@", "-")


def parse_key(key: str) -> ParsedKey:
    match = KEY_RE.fullmatch(key)
    if not match:
        raise ValueError(f"invalid visual key: {key!r}")
    return ParsedKey(key, match.group("app"), match.group("view"), match.group("theme"))


def _key_from_record_name(name: str) -> str:
    match = RECORD_NAME_RE.fullmatch(name)
    if not match:
        return ""
    return f"{match.group('app')}:{match.group('view')}@{match.group('theme')}"


def git_rev_parse(repo_root: Path, revision: str) -> str:
    proc = _run_text(["git", "rev-parse", "--verify", f"{revision}^{{commit}}"], cwd=repo_root)
    if proc.returncode != 0:
        raise ValueError(f"invalid git revision: {revision}")
    return proc.stdout.strip()


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    proc = _run_text(["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd=repo_root)
    return proc.returncode == 0


def git_changed_paths(repo_root: Path, base: str, head: str = "HEAD") -> list[str]:
    """Return the final tree delta, used for staleness and active-record changes."""

    proc = _run_text(
        ["git", "diff", "--name-only", "--find-renames", f"{base}..{head}"],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        raise ValueError("git changed-path query failed")
    return sorted({_normalize_path(line) for line in proc.stdout.splitlines() if line.strip()})


def git_touched_paths(repo_root: Path, base: str, head: str = "HEAD") -> list[str]:
    """Return every path touched by every commit in the audited range.

    Unlike the final delta, this retains change-then-revert history. ``-m``
    expands merge commits against each parent, and name-status parsing keeps
    both sides of renames/copies so an R0 path cannot disappear by moving it.
    Merge diffs use the first parent, avoiding unrelated base-parent changes
    in the synthetic merge ref used by pull-request CI.
    """

    proc = _run_bytes(
        [
            "git",
            "log",
            "--format=",
            "--name-status",
            "--find-renames",
            "--diff-merges=first-parent",
            "-z",
            f"{base}..{head}",
        ],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        raise ValueError("git touched-path query failed")
    tokens = proc.stdout.split(b"\0")
    paths: set[str] = set()
    index = 0
    while index < len(tokens):
        raw_status = tokens[index]
        index += 1
        if not raw_status.strip():
            continue
        status = os.fsdecode(raw_status).strip()
        if not re.fullmatch(r"[ACDMRTUXB][0-9]*", status):
            raise ValueError("git touched-path output invalid")
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(tokens):
            raise ValueError("git touched-path output truncated")
        for raw_path in tokens[index : index + path_count]:
            if not raw_path:
                raise ValueError("git touched-path output missing path")
            paths.add(_normalize_path(os.fsdecode(raw_path)))
        index += path_count
    return sorted(paths)


def kernel_paths_touched(paths: Iterable[str]) -> list[str]:
    touched: list[str] = []
    for value in paths:
        path = _normalize_path(value)
        if any(path == rule.rstrip("/") or (rule.endswith("/") and path.startswith(rule)) for rule in KERNEL_PATHS):
            touched.append(path)
    return sorted(set(touched))


def _changed_active_keys(paths: Iterable[str]) -> set[str]:
    prefix = ACTIVE_DIR.as_posix() + "/"
    keys: set[str] = set()
    for value in paths:
        path = _normalize_path(value)
        if not path.startswith(prefix) or "/revoked/" in path or not path.endswith(".json"):
            continue
        relative = path[len(prefix) :]
        if "/" not in relative:
            key = _key_from_record_name(relative)
            if key:
                keys.add(key)
    return keys


def _git_show_bytes(repo_root: Path, revision: str, path: str) -> bytes:
    proc = _run_bytes(["git", "show", f"{revision}:{path}"], cwd=repo_root)
    if proc.returncode != 0:
        raise ValueError(f"git show failed: {revision}:{path}")
    return proc.stdout


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text_bytes(value: bytes) -> str:
    normalized = value.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _thresholds_from_source(source: str) -> dict[str, int | float]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "LayeredThresholds":
            values: dict[str, int | float] = {}
            for child in node.body:
                if not isinstance(child, ast.AnnAssign) or not isinstance(child.target, ast.Name):
                    continue
                try:
                    value = ast.literal_eval(child.value)
                except (ValueError, TypeError):
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    values[child.target.id] = value
            if values:
                return values
    raise ValueError("LayeredThresholds not found")


def thresholds_sha_from_source(source: str) -> str:
    return sha256_canonical_json(_thresholds_from_source(source))


def _read_active_records(repo_root: Path) -> tuple[dict[str, dict[str, Any]], list[ReplayFailure]]:
    records: dict[str, dict[str, Any]] = {}
    failures: list[ReplayFailure] = []
    root = repo_root / ACTIVE_DIR
    if not root.exists():
        return records, failures
    for path in sorted(root.glob("*.json")):
        filename_key = _key_from_record_name(path.name)
        if not filename_key:
            failures.append(ReplayFailure(path.name, "invalid_active_record_filename"))
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failures.append(ReplayFailure(filename_key, "invalid_active_record_json"))
            continue
        if not isinstance(payload, dict):
            failures.append(ReplayFailure(filename_key, "invalid_active_record_root"))
            continue
        record_key = payload.get("key")
        if record_key != filename_key:
            failures.append(ReplayFailure(filename_key, "record_filename_key_mismatch"))
            continue
        if filename_key in records:
            failures.append(ReplayFailure(filename_key, "duplicate_active_record"))
            continue
        records[filename_key] = payload
    return records, failures


def _record_sanity_reasons(record: Mapping[str, Any], key: str) -> list[str]:
    reasons: list[str] = []
    if record.get("schema") != EVIDENCE_SCHEMA:
        reasons.append("record_schema_invalid")
    if record.get("key") != key:
        reasons.append("record_key_mismatch")
    if record.get("result") != "PASS":
        reasons.append("record_result_not_pass")
    if not isinstance(record.get("commit_head"), str) or not COMMIT_RE.fullmatch(record["commit_head"]):
        reasons.append("record_commit_invalid")
    for field in (
        "canonical_png_sha256",
        "capture_png_sha256",
        "manifest_sha256",
        "capture_manifest_sha256",
        "thresholds_sha256",
        "report_sha256",
        "sidecar_sha256",
    ):
        if not isinstance(record.get(field), str) or not HEX64_RE.fullmatch(record[field]):
            reasons.append(f"{field}_invalid")
    modal_hash = record.get("modal_audit_sha256")
    if modal_hash is not None and (not isinstance(modal_hash, str) or not HEX64_RE.fullmatch(modal_hash)):
        reasons.append("modal_audit_sha256_invalid")
    tools = record.get("tool_hashes")
    if not isinstance(tools, Mapping) or not tools:
        reasons.append("tool_hashes_invalid")
    elif any(
        not isinstance(path, str)
        or not isinstance(digest, str)
        or not HEX64_RE.fullmatch(digest)
        for path, digest in tools.items()
    ):
        reasons.append("tool_hashes_invalid")
    source_scope = record.get("source_scope")
    if not isinstance(source_scope, Mapping) or source_scope.get("key") != key:
        reasons.append("source_scope_invalid")
    report = record.get("report")
    if not isinstance(report, Mapping) or report.get("report_sha256") != record.get("report_sha256"):
        reasons.append("report_identity_mismatch")
    for field in ("vas_summary", "antifraud", "determinism"):
        if not isinstance(record.get(field), Mapping):
            reasons.append(f"{field}_invalid")
    targets = record.get("target_set")
    if (
        not isinstance(targets, list)
        or not all(isinstance(value, str) for value in targets)
        or len(targets) != len(set(targets))
        or key not in targets
    ):
        reasons.append("target_set_invalid")
    review = record.get("human_review")
    if not isinstance(review, Mapping) or not {
        "approval_url",
        "comment_id",
        "author",
    }.issubset(review):
        reasons.append("human_review_invalid")
    policy = record.get("policy")
    if not isinstance(policy, Mapping) or policy.get("allow") is not True or policy.get("reasons") != []:
        reasons.append("stored_policy_invalid")
    operation = record.get("operation")
    if not isinstance(operation, Mapping) or operation.get("kind") not in {"close", "refresh"}:
        reasons.append("operation_invalid")
    return reasons


def _report_near_threshold(record: Mapping[str, Any]) -> bool:
    report = record.get("report")
    if not isinstance(report, Mapping):
        return False
    results = report.get("results")
    if not isinstance(results, list):
        return False
    return any(
        isinstance(result, Mapping)
        and isinstance(result.get("findings"), list)
        and any(
            isinstance(finding, str) and finding.startswith("near_threshold:")
            for finding in result["findings"]
        )
        for result in results
    )


ApprovalChecker = Callable[..., dict[str, object]]


def _verified_approval(
    record: Mapping[str, Any],
    repo_root: Path,
    checker: ApprovalChecker,
) -> tuple[dict[str, object] | None, list[str]]:
    if not _report_near_threshold(record):
        return None, []
    result = checker(
        record.get("human_review"),
        key=str(record.get("key", "")),
        report_sha256=str(record.get("report_sha256", "")),
        git_cwd=repo_root,
    )
    if result.get("verified") is not True:
        return result, [f"approval_invalid:{result.get('reason', 'unknown')}"]
    return result, []


def _stored_policy_reasons(
    record: Mapping[str, Any],
    approval: object,
) -> list[str]:
    allow, reasons = decide(
        record.get("report"),
        record.get("vas_summary"),
        record.get("antifraud"),
        record.get("determinism"),
        record.get("state_assertion"),
        approval,
        record.get("target_set"),
    )
    return [] if allow else [f"stored_policy_blocked:{reason}" for reason in reasons]


def _historical_manifest_capture(
    repo_root: Path,
    commit: str,
    key: str,
) -> tuple[dict[str, Any], bytes]:
    raw = _git_show_bytes(repo_root, commit, CANONICAL_MANIFEST.as_posix())
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("historical manifest invalid") from exc
    matches = [
        item
        for item in manifest.get("captures", [])
        if isinstance(item, dict) and manifest_key(item) == key
    ]
    if len(matches) != 1:
        raise ValueError("historical manifest key mismatch")
    return matches[0], raw


def _class_a_reasons(record: Mapping[str, Any], repo_root: Path) -> list[str]:
    reasons: list[str] = []
    key = str(record.get("key", ""))
    commit = str(record.get("commit_head", ""))
    if not _is_ancestor(repo_root, commit):
        return ["commit_head_not_ancestor"]
    try:
        capture, manifest_raw = _historical_manifest_capture(repo_root, commit, key)
        canonical_rel = (CANONICAL_DIR / str(capture.get("file", ""))).as_posix()
        canonical_raw = _git_show_bytes(repo_root, commit, canonical_rel)
        if _sha256_bytes(canonical_raw) != record.get("canonical_png_sha256"):
            reasons.append("canonical_png_historical_mismatch")
        if _sha256_text_bytes(manifest_raw) != record.get("manifest_sha256"):
            reasons.append("manifest_historical_mismatch")
        tools = record.get("tool_hashes")
        if isinstance(tools, Mapping):
            for path, expected in tools.items():
                if _sha256_text_bytes(_git_show_bytes(repo_root, commit, str(path))) != expected:
                    reasons.append(f"tool_hash_mismatch:{path}")
        comparator_source = _git_show_bytes(
            repo_root, commit, "qa/layered_visual_compare.py"
        ).decode("utf-8")
        if thresholds_sha_from_source(comparator_source) != record.get("thresholds_sha256"):
            reasons.append("thresholds_sha256_mismatch")
        if not source_scope_matches_revision(
            record.get("source_scope"), repo_root=repo_root, revision=commit
        ):
            reasons.append("source_scope_historical_mismatch")
        current_canonical = repo_root / canonical_rel
        if not current_canonical.is_file() or sha256_binary(current_canonical) != record.get(
            "canonical_png_sha256"
        ):
            reasons.append("canonical_png_sha256_mismatch")
        if sha256_text(repo_root / CANONICAL_MANIFEST) != record.get("manifest_sha256"):
            reasons.append("manifest_sha256_mismatch")
    except (OSError, UnicodeDecodeError, ValueError):
        reasons.append("class_a_reproduction_failed")
    if is_source_scope_stale(record.get("source_scope"), key, repo_root=repo_root):
        reasons.append("stale_closure")
    return reasons


def _closed_handoff_keys(text: str) -> tuple[set[str], list[str]]:
    closed: set[str] = set()
    duplicates: list[str] = []
    for line in text.splitlines():
        match = CHECKBOX_RE.match(line)
        if not match or match.group("state").lower() != "x":
            continue
        key = match.group("key")
        if key in closed:
            duplicates.append(key)
        closed.add(key)
    return closed, duplicates


def audit_structure(
    *,
    repo_root: Path = ROOT,
    base: str | None = None,
    approval_checker: ApprovalChecker = verify_approval,
    render_func: Callable[[Path], str] = render_handoff,
) -> ReplayResult:
    repo_root = repo_root.resolve()
    failures: list[ReplayFailure] = []
    try:
        universe = set(manifest_keys(repo_root))
    except Exception as exc:
        return ReplayResult("structural", 0, 0, 0, (ReplayFailure("<universe>", str(exc)),))
    if len(universe) != EXPECTED_UNIVERSE_SIZE:
        failures.append(ReplayFailure("<universe>", f"manifest_universe_not_116:{len(universe)}"))
    records, record_load_failures = _read_active_records(repo_root)
    failures.extend(record_load_failures)
    unknown_records = sorted(set(records) - universe)
    failures.extend(ReplayFailure(key, "record_outside_manifest") for key in unknown_records)

    try:
        rendered = render_func(repo_root)
        actual = (repo_root / HANDOFF).read_text(encoding="utf-8")
        if actual != rendered:
            failures.append(ReplayFailure("<handoff>", "handoff_render_drift"))
        closed, duplicates = _closed_handoff_keys(actual)
        failures.extend(ReplayFailure(key, "duplicate_closed_handoff_key") for key in duplicates)
        if closed != set(records):
            failures.append(ReplayFailure("<handoff>", "handoff_active_cardinality_mismatch"))
    except Exception as exc:
        failures.append(ReplayFailure("<handoff>", f"handoff_render_failed:{exc}"))

    for key, record in sorted(records.items()):
        for reason in _record_sanity_reasons(record, key):
            failures.append(ReplayFailure(key, reason))
        for reason in _class_a_reasons(record, repo_root):
            failures.append(ReplayFailure(key, reason))
        approval, approval_reasons = _verified_approval(record, repo_root, approval_checker)
        failures.extend(ReplayFailure(key, reason) for reason in approval_reasons)
        if not approval_reasons:
            failures.extend(
                ReplayFailure(key, reason)
                for reason in _stored_policy_reasons(record, approval)
            )

    if base is not None:
        try:
            base_commit = git_rev_parse(repo_root, base)
            if not _is_ancestor(repo_root, base_commit):
                raise ValueError("base_not_ancestor")
            paths = git_changed_paths(repo_root, base_commit)
            touched_paths = git_touched_paths(repo_root, base_commit)
        except ValueError as exc:
            failures.append(ReplayFailure("<range>", str(exc)))
        else:
            for path in unmapped_visual_sources(paths):
                failures.append(ReplayFailure(path, "unmapped_visual_source"))
            active_changed = _changed_active_keys(paths)
            touched = kernel_paths_touched(touched_paths)
            for key in sorted(active_changed & set(records)):
                record_commit = records[key].get("commit_head")
                if not isinstance(record_commit, str) or not _is_ancestor(
                    repo_root, base_commit, record_commit
                ):
                    failures.append(
                        ReplayFailure(key, "record_commit_outside_audited_range")
                    )
            if active_changed and touched:
                for key in sorted(active_changed):
                    failures.append(ReplayFailure(key, "kernel_changed_with_visual_closure"))
    return ReplayResult(
        "structural",
        len(records),
        len(records),
        0,
        tuple(failures),
    )


def _repo_arg_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


@contextmanager
def _temporary_worktree(repo_root: Path, commit: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="nm_replay_worktree_") as temp:
        worktree = Path(temp) / "worktree"
        proc = _run_text(["git", "worktree", "add", "--detach", str(worktree), commit], cwd=repo_root)
        if proc.returncode != 0:
            raise RuntimeError("worktree_add_failed")
        try:
            yield worktree
        finally:
            _run_text(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root)


def _capture_result(manifest_path: Path, key: str) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    matches = [
        item
        for item in payload.get("results", [])
        if isinstance(item, dict)
        and (
            item.get("key") == key
            or item.get("surface_key") == key
            or (
                isinstance(item.get("app"), str)
                and isinstance(item.get("view"), str)
                and isinstance(item.get("theme"), str)
                and f"{item['app']}:{item['view']}@{item['theme']}" == key
            )
        )
    ]
    if len(matches) != 1:
        raise RuntimeError("capture_manifest_key_mismatch")
    return matches[0]


def _capture_artifacts(capture_dir: Path, key: str) -> tuple[Path, Path, Path]:
    manifest = capture_dir / "CAPTURE_MANIFEST.json"
    result = _capture_result(manifest, key)
    png = capture_dir / str(result.get("file", ""))
    provenance = result.get("provenance")
    if isinstance(provenance, Mapping):
        candidate = Path(str(provenance.get("capture_path", "")))
        if candidate.is_file():
            png = candidate
        sidecar_value = Path(str(provenance.get("introspection_sidecar", "")))
        sidecar = (
            sidecar_value
            if sidecar_value.is_absolute()
            else capture_dir.parent / "_visual_auditor_spec" / sidecar_value.name
        )
    else:
        sidecar = capture_dir.parent / "_visual_auditor_spec" / "introspection.json"
    if not manifest.is_file() or not png.is_file() or not sidecar.is_file():
        raise RuntimeError("capture_artifact_missing")
    return manifest, png, sidecar


def _run_capture(worktree: Path, parsed: ParsedKey, out_dir: Path) -> None:
    env = os.environ.copy()
    env["NM_VAS_INTROSPECT"] = "1"
    proc = _run_text(
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
            _repo_arg_path(worktree, out_dir),
            "--no-clean",
        ],
        cwd=worktree,
        env=env,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError("capture_failed")


def _canonical_capture(worktree: Path, key: str) -> dict[str, Any]:
    manifest = json.loads((worktree / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    matches = [
        item
        for item in manifest.get("captures", [])
        if isinstance(item, dict) and manifest_key(item) == key
    ]
    if len(matches) != 1:
        raise RuntimeError("canonical_manifest_key_mismatch")
    return matches[0]


def _merge_back_capture(primary: Path, back: Path) -> None:
    primary_manifest = json.loads((primary / "CAPTURE_MANIFEST.json").read_text(encoding="utf-8"))
    back_manifest = json.loads((back / "CAPTURE_MANIFEST.json").read_text(encoding="utf-8"))
    primary_results = primary_manifest.setdefault("results", [])
    existing = {item.get("key") for item in primary_results if isinstance(item, dict)}
    for item in back_manifest.get("results", []):
        if not isinstance(item, dict):
            continue
        filename = item.get("file")
        if filename and (back / str(filename)).is_file():
            shutil.copy2(back / str(filename), primary / str(filename))
        if item.get("key") not in existing:
            primary_results.append(item)
    (primary / "CAPTURE_MANIFEST.json").write_text(
        json.dumps(primary_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _run_antifraud(worktree: Path, report_dir: Path) -> dict[str, Any]:
    path = report_dir / "ANTIFRAUD.json"
    report_dir.mkdir(parents=True, exist_ok=True)
    _run_text(
        [sys.executable, "qa/anti_fraud_scan.py", "--mode", "all", "--json", str(path)],
        cwd=worktree,
        timeout=180,
    )
    if not path.is_file():
        raise RuntimeError("antifraud_output_missing")
    return json.loads(path.read_text(encoding="utf-8"))


def _run_comparator(worktree: Path, parsed: ParsedKey, capture_dir: Path, report_dir: Path) -> Path:
    _run_text(
        [
            sys.executable,
            "qa/layered_visual_compare.py",
            "--canonical",
            CANONICAL_DIR.as_posix(),
            "--actual",
            _repo_arg_path(worktree, capture_dir),
            "--out-dir",
            _repo_arg_path(worktree, report_dir),
            "--key",
            parsed.key,
        ],
        cwd=worktree,
        timeout=300,
    )
    path = report_dir / "LAYERED_VISUAL_REPORT.json"
    if not path.is_file():
        raise RuntimeError("comparator_output_missing")
    return path


def _sidecar_entry(path: Path, key: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    matches = [item for item in payload if isinstance(item, dict) and item.get("surface_key") == key]
    if len(matches) != 1:
        raise RuntimeError("vas_sidecar_key_mismatch")
    return matches[0]


def _vas_summary(
    worktree: Path,
    key: str,
    sidecar: Path,
    capture_result: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    proc = _run_text(
        [sys.executable, "qa/vas_gate.py", "--sidecar", str(sidecar), "--key", key],
        cwd=worktree,
        timeout=120,
    )
    entry = _sidecar_entry(sidecar, key)
    divergences = entry.get("divergences") if isinstance(entry.get("divergences"), list) else []
    high = sum(1 for item in divergences if isinstance(item, Mapping) and item.get("severity") == "high")
    medium = sum(
        1 for item in divergences if isinstance(item, Mapping) and item.get("severity") == "medium"
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
        "pass": proc.returncode == 0 and fail_count == 0 and high == 0 and medium == 0 and capture_valid,
        "fail_count": fail_count,
        "high_count": high,
        "medium_count": medium,
        "capture_valid": capture_valid,
    }
    assertion = entry.get("state_assertion")
    if assertion is not None and not isinstance(assertion, dict):
        assertion = {"schema": STATE_ASSERTION_SCHEMA, "key": key, "pass": False}
    return summary, assertion


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


def _stable_json_hash(path: Path) -> str:
    return sha256_canonical_json(_sanitize_json(json.loads(path.read_text(encoding="utf-8"))))


def _run_modal_audit(
    worktree: Path,
    parsed: ParsedKey,
    capture_dir: Path,
    report_dir: Path,
) -> dict[str, Any]:
    out = report_dir / f"modal_audit_{key_safe(parsed.key)}"
    out.mkdir(parents=True, exist_ok=True)
    _run_text(
        [
            sys.executable,
            str(MODAL_AUDIT_TOOL),
            "--key",
            parsed.key,
            "--canonical",
            CANONICAL_DIR.as_posix(),
            "--actual",
            _repo_arg_path(worktree, capture_dir),
            "--out-dir",
            _repo_arg_path(worktree, out),
        ],
        cwd=worktree,
        timeout=120,
    )
    path = out / "AUDIT.json"
    if not path.is_file():
        raise RuntimeError("modal_audit_output_missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "pass": payload.get("summary", {}).get("test_blur_pass") is True,
        "summary": payload.get("summary", {}),
    }


def _determinism(
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


def regenerate_measurement(repo_root: Path, key: str, commit: str) -> dict[str, Any]:
    parsed = parse_key(key)
    with _temporary_worktree(repo_root, commit) as worktree:
        primary = worktree / "qa" / "_captures_v8"
        report_dir = worktree / "reports" / "qa" / "closure_replay" / key_safe(key)
        antifraud = _run_antifraud(worktree, report_dir)
        _run_capture(worktree, parsed, primary)
        canonical = _canonical_capture(worktree, key)
        modal_required = canonical.get("is_modal") is True or canonical.get("surface") in {
            "modal",
            "window_modal",
        }
        if modal_required:
            back_key = canonical.get("back_screen_key")
            if not isinstance(back_key, str) or not back_key:
                raise RuntimeError("modal_back_screen_missing")
            with tempfile.TemporaryDirectory(prefix="nm_replay_back_") as temp:
                back = Path(temp) / "captures"
                _run_capture(worktree, parse_key(back_key), back)
                _merge_back_capture(primary, back)
        first_manifest, first_png, first_sidecar = _capture_artifacts(primary, key)
        first_result = _capture_result(first_manifest, key)
        with tempfile.TemporaryDirectory(prefix="nm_replay_determinism_") as temp:
            secondary = Path(temp) / "captures"
            _run_capture(worktree, parsed, secondary)
            second_manifest, second_png, _second_sidecar = _capture_artifacts(secondary, key)
            determinism = _determinism(
                key, first_manifest, second_manifest, first_png, second_png
            )
        report_path = _run_comparator(worktree, parsed, primary, report_dir)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["report_sha256"] = _stable_json_hash(report_path)
        vas, assertion = _vas_summary(worktree, key, first_sidecar, first_result)
        modal = _run_modal_audit(worktree, parsed, primary, report_dir) if modal_required else None
        report["modal_audit_required"] = modal_required
        report["modal_audit"] = modal
        return {
            "report": report,
            "vas_summary": vas,
            "antifraud": antifraud,
            "determinism": determinism,
            "state_assertion": assertion,
            "modal_audit": modal,
        }


MeasurementRunner = Callable[[Path, str, str], dict[str, Any]]


def replay_full(
    *,
    repo_root: Path = ROOT,
    base: str | None = None,
    all_closed: bool = False,
    approval_checker: ApprovalChecker = verify_approval,
    measurement_runner: MeasurementRunner = regenerate_measurement,
    render_func: Callable[[Path], str] = render_handoff,
) -> ReplayResult:
    structural = audit_structure(
        repo_root=repo_root,
        base=base,
        approval_checker=approval_checker,
        render_func=render_func,
    )
    records, load_failures = _read_active_records(repo_root)
    if structural.failures or load_failures:
        return ReplayResult(
            "full",
            len(records),
            structural.checked_keys,
            0,
            tuple([*structural.failures, *load_failures]),
        )
    if all_closed:
        candidates = set(records)
    else:
        if base is None:
            return ReplayResult(
                "full", len(records), len(records), 0, (ReplayFailure("<range>", "base_required"),)
            )
        try:
            base_commit = git_rev_parse(repo_root, base)
            if not _is_ancestor(repo_root, base_commit):
                raise ValueError("base_not_ancestor")
            candidates = _changed_active_keys(git_changed_paths(repo_root, base_commit))
        except ValueError as exc:
            return ReplayResult(
                "full", len(records), len(records), 0, (ReplayFailure("<range>", str(exc)),)
            )
        candidates &= set(records)

    failures: list[ReplayFailure] = []
    replayed = 0
    for key in sorted(candidates):
        record = records[key]
        try:
            measurement = measurement_runner(repo_root, key, str(record["commit_head"]))
        except Exception as exc:
            failures.append(ReplayFailure(key, f"regeneration_failed:{exc}"))
            continue
        approval, approval_reasons = _verified_approval(record, repo_root, approval_checker)
        failures.extend(ReplayFailure(key, reason) for reason in approval_reasons)
        if approval_reasons:
            continue
        if isinstance(approval, dict):
            approval = dict(approval)
            approval["key"] = key
            approval["report_sha256"] = measurement.get("report", {}).get("report_sha256")
        allow, reasons = decide(
            measurement.get("report"),
            measurement.get("vas_summary"),
            measurement.get("antifraud"),
            measurement.get("determinism"),
            measurement.get("state_assertion"),
            approval,
            record.get("target_set"),
        )
        if not allow:
            failures.extend(ReplayFailure(key, f"regenerated_policy_blocked:{reason}") for reason in reasons)
            continue
        replayed += 1
    if all_closed and replayed != len(records) and not failures:
        failures.append(ReplayFailure("<cardinality>", "replayed_active_cardinality_mismatch"))
    return ReplayResult("full", len(records), len(records), replayed, tuple(failures))


def print_result(result: ReplayResult) -> None:
    print("REPLAY PASS" if result.passed else "REPLAY FAIL")
    print(f"mode: {result.mode}")
    print(f"active_records: {result.active_records}")
    print(f"checked_keys: {result.checked_keys}")
    print(f"replayed_keys: {result.replayed_keys}")
    for failure in result.failures:
        print(f"- {failure.key}: {failure.reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independently replay v2 visual closures.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--structural-precheck", action="store_true")
    modes.add_argument("--all-closed", action="store_true")
    parser.add_argument("--base")
    args = parser.parse_args(argv)
    if args.structural_precheck:
        if not args.base:
            parser.error("--structural-precheck requires --base")
        result = audit_structure(base=args.base)
    else:
        if not args.all_closed and not args.base:
            parser.error("full replay requires --all-closed or --base")
        result = replay_full(base=args.base, all_closed=args.all_closed)
    print_result(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
