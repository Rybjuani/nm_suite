#!/usr/bin/env python3
"""Atomic visual closure tool for one handoff key."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = "VISUAL_REPAIR_HANDOFF.md"
EVIDENCE_SCHEMA = "nm_suite.evidence_record.v1"
EVIDENCE_DIR = Path("docs") / "closure_evidence"
CANONICAL_DIR = Path("qa") / "_mockup_canonical"
DEFAULT_CAPTURE_DIR = Path("qa") / "_captures_v8"
DEFAULT_REPORT_DIR = Path("reports") / "qa" / "visual_closure_replay"
MODAL_AUDIT_TOOL = Path("tools") / "qa" / "audit_modal_backdrop_blur.py"
SCOPED_STATUS_PATHS = (
    "app",
    "hub",
    "shared",
    "qa",
    "tools/qa",
    HANDOFF,
    ".github/workflows",
)
KEY_RE = re.compile(r"(?P<app>suite|hub):(?P<view>[^@\s`\"'\]\)]+)@(?P<theme>light|dark)")
CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)-\s*\[(?P<state>[xX ])\]\s*(?P<body>.*)$")
NOTE_INDENT = "  "
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
}


class ClosureError(Exception):
    exit_code = 1


class PreflightError(ClosureError):
    exit_code = 2


class GateError(ClosureError):
    exit_code = 1


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
    match = KEY_RE.fullmatch(key.strip())
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_record_sha256(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, child in value.items():
            if key in VOLATILE_JSON_KEYS:
                continue
            clean[key] = _sanitize_json(child)
        return clean
    if isinstance(value, list):
        return [_sanitize_json(child) for child in value]
    return value


def stable_json_file_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return hashlib.sha256(canonical_json_bytes(_sanitize_json(payload))).hexdigest()


def _repo_arg_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def git_rev_parse(repo_root: Path, revision: str = "HEAD") -> str:
    proc = _run(["git", "rev-parse", "--verify", f"{revision}^{{commit}}"], cwd=repo_root)
    if proc.returncode != 0:
        raise PreflightError(f"invalid_git_revision: {revision}")
    return proc.stdout.strip()


def ensure_clean_for_closure(repo_root: Path) -> None:
    args = ["git", "status", "--porcelain", "--", *SCOPED_STATUS_PATHS]
    proc = _run(args, cwd=repo_root)
    if proc.returncode != 0:
        raise PreflightError("git_status_failed")
    if proc.stdout.strip():
        raise PreflightError("dirty_working_tree")


def _anti_fraud_mode_all_unsupported(proc: subprocess.CompletedProcess[str]) -> bool:
    text = f"{proc.stdout}\n{proc.stderr}".lower()
    return proc.returncode == 2 and ("invalid choice" in text or "unrecognized arguments" in text)


def run_anti_fraud(repo_root: Path) -> None:
    mode_all = _run([sys.executable, "qa/anti_fraud_scan.py", "--mode", "all"], cwd=repo_root)
    if mode_all.returncode == 0:
        return
    if not _anti_fraud_mode_all_unsupported(mode_all):
        _print_process_failure("anti_fraud --mode all", mode_all)
        raise GateError("anti_fraud_failed")

    for label, args in (
        ("anti_fraud runtime", [sys.executable, "qa/anti_fraud_scan.py"]),
        ("anti_fraud qa-harness", [sys.executable, "qa/anti_fraud_scan.py", "--mode", "qa-harness"]),
    ):
        proc = _run(args, cwd=repo_root)
        if proc.returncode != 0:
            _print_process_failure(label, proc)
            raise GateError("anti_fraud_failed")


def _key_from_capture_result(result: dict[str, Any]) -> str:
    for field in ("surface_key", "key"):
        value = result.get(field)
        if isinstance(value, str) and value:
            return value
    app = result.get("app")
    view = result.get("view")
    theme = result.get("theme")
    if all(isinstance(part, str) and part for part in (app, view, theme)):
        return f"{app}:{view}@{theme}"
    return ""


def _capture_sidecar_path(capture_dir: Path, result: dict[str, Any]) -> Path:
    provenance = result.get("provenance")
    if isinstance(provenance, dict):
        sidecar = provenance.get("introspection_sidecar")
        if isinstance(sidecar, str) and sidecar.strip():
            candidate = Path(sidecar)
            if candidate.is_absolute():
                return candidate
            return capture_dir.parent / "_visual_auditor_spec" / candidate.name
    return capture_dir.parent / "_visual_auditor_spec" / "introspection.json"


def locate_capture_artifacts(capture_dir: Path, key: str) -> tuple[Path, Path, Path]:
    manifest_path = capture_dir / "CAPTURE_MANIFEST.json"
    if not manifest_path.exists():
        raise GateError("missing_capture_manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateError(f"invalid_capture_manifest: {exc}") from exc

    for result in manifest.get("results", []):
        if not isinstance(result, dict) or _key_from_capture_result(result) != key:
            continue
        filename = result.get("file")
        png_path = capture_dir / str(filename) if filename else None
        provenance = result.get("provenance")
        if isinstance(provenance, dict) and isinstance(provenance.get("capture_path"), str):
            candidate = Path(provenance["capture_path"])
            if candidate.exists():
                png_path = candidate
        if png_path is None or not png_path.exists():
            raise GateError("missing_capture_png")
        sidecar_path = _capture_sidecar_path(capture_dir, result)
        if not sidecar_path.exists():
            raise GateError("missing_vas_sidecar")
        return manifest_path, png_path, sidecar_path
    raise GateError("capture_manifest_missing_key")


def load_canonical_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CANONICAL_DIR / "MANIFEST.json"
    if not path.exists():
        raise GateError("missing_canonical_manifest")
    return json.loads(path.read_text(encoding="utf-8"))


def _capture_file_to_key(filename: str) -> str:
    match = re.match(r"^(suite|hub)-(.+)-(light|dark)-\d+x\d+(?:-scale\d+)?\.png$", filename)
    if match:
        return f"{match.group(1)}:{match.group(2)}@{match.group(3)}"
    return ""


def is_modal_key(repo_root: Path, key: str) -> bool:
    """Return True when the canonical manifest marks this key as a modal."""
    manifest = load_canonical_manifest(repo_root)
    for capture in manifest.get("captures", []):
        if not isinstance(capture, dict):
            continue
        file_key = _capture_file_to_key(str(capture.get("file", "")))
        if file_key != key:
            continue
        if capture.get("is_modal") is True:
            return True
        if str(capture.get("surface", "")).lower() in {"modal", "window_modal"}:
            return True
    return False


def _modal_back_screen_key(repo_root: Path, key: str) -> str | None:
    manifest = load_canonical_manifest(repo_root)
    for capture in manifest.get("captures", []):
        if not isinstance(capture, dict):
            continue
        file_key = _capture_file_to_key(str(capture.get("file", "")))
        if file_key != key:
            continue
        back_key = capture.get("back_screen_key")
        if isinstance(back_key, str) and back_key:
            return back_key
    return None


def run_modal_audit(
    repo_root: Path,
    parsed: ParsedKey,
    capture_dir: Path,
    report_dir: Path,
) -> Path:
    """Run the modal backdrop/blur audit for a modal key.

    Requires the back-screen capture to be present in ``capture_dir``.
    The audit report is written under ``report_dir`` and its stable hash is
    stored in the evidence record.
    """
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
    if proc.returncode != 0:
        _print_process_failure("modal_backdrop_blur_audit", proc)
        raise GateError("modal_audit_failed")
    report_path = audit_report_dir / "AUDIT.json"
    if not report_path.exists():
        raise GateError("missing_modal_audit_report")
    audit = json.loads(report_path.read_text(encoding="utf-8"))
    if audit.get("summary", {}).get("test_blur_pass") is not True:
        raise GateError("modal_audit_blur_not_pass")
    return report_path


def _report_result(report: dict[str, Any], key: str) -> dict[str, Any]:
    if report.get("report_evidence_valid") is not True:
        raise GateError("report_evidence_invalid")
    matches = [
        result
        for result in report.get("results", [])
        if isinstance(result, dict) and result.get("key") == key
    ]
    if not matches:
        raise GateError("report_missing_key")
    result = matches[0]
    if result.get("status") != "PASS":
        raise GateError("comparator_not_pass")
    if result.get("suspicious_perfect_match") is not False:
        raise GateError("suspicious_perfect_match")
    if result.get("near_perfect_match") is not False:
        raise GateError("near_perfect_match")
    return result


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
    parsed = parse_key(key)
    run_capture(repo_root, parsed, capture_dir)


def _ensure_modal_backdrop_capture(
    repo_root: Path,
    parsed: ParsedKey,
    capture_dir: Path,
) -> None:
    back_key = _modal_back_screen_key(repo_root, parsed.key)
    if not back_key:
        raise GateError("modal_missing_back_screen_key")
    run_capture_for_key(repo_root, back_key, capture_dir)

def run_comparator(repo_root: Path, parsed: ParsedKey, capture_dir: Path, report_dir: Path) -> Path:
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
    if proc.returncode != 0:
        _print_process_failure("layered_visual_compare", proc)
        raise GateError("comparator_failed")
    report_path = report_dir / "LAYERED_VISUAL_REPORT.json"
    if not report_path.exists():
        raise GateError("missing_layered_report")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    _report_result(report, parsed.key)
    return report_path


def run_vas(repo_root: Path, key: str, sidecar_path: Path) -> None:
    proc = _run(
        [sys.executable, "qa/vas_gate.py", "--sidecar", str(sidecar_path), "--key", key],
        cwd=repo_root,
        timeout=120,
    )
    if proc.returncode != 0:
        _print_process_failure("vas_gate", proc)
        raise GateError("vas_failed")


def _metric_float(metrics: dict[str, Any], name: str) -> float:
    value = metrics.get(name)
    if value is None:
        raise GateError(f"missing_metric_{name}")
    return float(value)


def _metric_bbox(layout: dict[str, Any]) -> int | None:
    value = layout.get("max_bbox_delta_px")
    if value in ("", None):
        return None
    return int(value)


def build_evidence_record(
    *,
    repo_root: Path,
    parsed: ParsedKey,
    commit_head: str,
    manifest_path: Path,
    png_path: Path,
    report_path: Path,
    sidecar_path: Path,
    modal_audit_path: Path | None = None,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    result = _report_result(report, parsed.key)
    metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
    layout = result.get("layout") if isinstance(result.get("layout"), dict) else {}

    modal_audit_sha256 = (
        stable_json_file_sha256(modal_audit_path) if modal_audit_path else None
    )

    return {
        "schema": EVIDENCE_SCHEMA,
        "key": parsed.key,
        "commit_head": commit_head,
        "anti_fraud_sha256": sha256_file(repo_root / "qa" / "anti_fraud_scan.py"),
        "capture_v8_sha256": sha256_file(repo_root / "qa" / "capture_v8.py"),
        "layered_compare_sha256": sha256_file(repo_root / "qa" / "layered_visual_compare.py"),
        "vas_gate_sha256": sha256_file(repo_root / "qa" / "vas_gate.py"),
        "capture_png_sha256": sha256_file(png_path),
        "manifest_sha256": stable_json_file_sha256(manifest_path),
        "report_sha256": stable_json_file_sha256(report_path),
        "sidecar_sha256": stable_json_file_sha256(sidecar_path),
        "modal_audit_sha256": modal_audit_sha256,
        "result": "PASS",
        "metrics": {
            "changed_pixel_ratio": _metric_float(metrics, "changed_pixel_ratio"),
            "mean_abs_diff": _metric_float(metrics, "mean_abs_diff"),
            "windowed_ssim": _metric_float(metrics, "windowed_ssim"),
            "max_bbox_delta_px": _metric_bbox(layout),
        },
        "command_spec": {
            "capture": {
                "tool": "qa/capture_v8.py",
                "app": parsed.app,
                "view": parsed.view,
                "theme": parsed.theme,
                "vas_introspect": True,
            },
            "compare": {
                "tool": "qa/layered_visual_compare.py",
                "canonical": "qa/_mockup_canonical",
                "scope": parsed.key,
            },
        },
    }


def regenerate_record_for_key(
    *,
    repo_root: Path,
    key: str,
    commit_head: str,
    capture_dir: Path | None = None,
    report_dir: Path | None = None,
) -> EvidenceBuild:
    parsed = parse_key(key)
    capture_dir = capture_dir or (repo_root / DEFAULT_CAPTURE_DIR)
    report_dir = report_dir or (repo_root / DEFAULT_REPORT_DIR)
    run_anti_fraud(repo_root)
    run_capture(repo_root, parsed, capture_dir)
    if is_modal_key(repo_root, parsed.key):
        _ensure_modal_backdrop_capture(repo_root, parsed, capture_dir)
    manifest_path, png_path, sidecar_path = locate_capture_artifacts(capture_dir, parsed.key)
    report_path = run_comparator(repo_root, parsed, capture_dir, report_dir)
    run_vas(repo_root, parsed.key, sidecar_path)
    modal_audit_path: Path | None = None
    if is_modal_key(repo_root, parsed.key):
        modal_audit_path = run_modal_audit(repo_root, parsed, capture_dir, report_dir)
    record = build_evidence_record(
        repo_root=repo_root,
        parsed=parsed,
        commit_head=commit_head,
        manifest_path=manifest_path,
        png_path=png_path,
        report_path=report_path,
        sidecar_path=sidecar_path,
        modal_audit_path=modal_audit_path,
    )
    record_path = EVIDENCE_DIR / f"{key_safe(parsed.key)}.json"
    return EvidenceBuild(
        record=record,
        record_sha256=canonical_record_sha256(record),
        record_path=record_path,
    )


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
            if remove.returncode != 0 and worktree.exists():
                resolved = worktree.resolve()
                if temp_root in resolved.parents:
                    shutil.rmtree(resolved, ignore_errors=True)


def _checkbox_state_for_key(handoff_text: str, key: str) -> tuple[str, int | None]:
    closed_line: int | None = None
    for idx, line in enumerate(handoff_text.splitlines(), start=1):
        match = CHECKBOX_RE.match(line)
        if not match or key not in line:
            continue
        keys = [m.group(0) for m in KEY_RE.finditer(line)]
        if key not in keys:
            continue
        state = match.group("state").lower()
        if state == " ":
            return "open", idx
        closed_line = idx
    if closed_line is not None:
        return "closed", closed_line
    return "missing", None


def assert_handoff_key_open(repo_root: Path, key: str) -> None:
    handoff_path = repo_root / HANDOFF
    state, _line = _checkbox_state_for_key(handoff_path.read_text(encoding="utf-8"), key)
    if state == "open":
        return
    if state == "closed":
        raise PreflightError("key_already_closed")
    raise PreflightError("unknown_key")


def _line_ending(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def update_handoff_closure(
    *,
    handoff_path: Path,
    key: str,
    record_sha256: str,
    record_path: Path,
    commit_head: str,
) -> None:
    original = handoff_path.read_text(encoding="utf-8")
    newline = _line_ending(original)
    lines = original.splitlines()
    out: list[str] = []
    changed = False
    for line in lines:
        if not changed:
            match = CHECKBOX_RE.match(line)
            if match and match.group("state") == " " and key in [m.group(0) for m in KEY_RE.finditer(line)]:
                line = line[: match.start("state")] + "x" + line[match.end("state") :]
                out.append(line)
                out.extend(
                    [
                        f"{NOTE_INDENT}- evidence: {record_sha256}",
                        f"{NOTE_INDENT}- evidence-record: {record_path.as_posix()}",
                        f"{NOTE_INDENT}- commit: {commit_head}",
                        f"{NOTE_INDENT}- closed-by: close_visual_key.py",
                    ]
                )
                changed = True
                continue
        out.append(line)
    if not changed:
        raise PreflightError("open_key_not_found")

    new_text = newline.join(out) + (newline if original.endswith(("\n", "\r\n")) else "")
    tmp_path = handoff_path.with_name(f".{handoff_path.name}.tmp")
    tmp_path.write_text(new_text, encoding="utf-8")
    tmp_path.replace(handoff_path)


def write_record(repo_root: Path, build: EvidenceBuild) -> Path:
    record_path = repo_root / build.record_path
    record_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = record_path.with_name(f".{record_path.name}.tmp")
    tmp_path.write_text(
        json.dumps(build.record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(record_path)
    return record_path


def run_preflight(
    *,
    repo_root: Path,
    key: str,
    capture_dir: Path | None = None,
    report_dir: Path | None = None,
) -> None:
    """Early-exit guard: full pipeline over the CURRENT working tree.

    Sin dirs explícitos captura y reporta en un directorio temporal fuera del
    repo: capturar en ``qa/_captures_v8`` ensuciaba rutas scoped y el propio
    ``ensure_clean_for_closure`` posterior abortaba con ``dirty_working_tree``
    (bug observado 2026-07-03). El sidecar VAS se resuelve relativo al padre
    del capture dir (contrato de ``capture_v8``), así que también queda en el
    directorio temporal.
    """
    parsed_pf = parse_key(key)
    if capture_dir is not None or report_dir is not None:
        cap_pf = capture_dir or (repo_root / DEFAULT_CAPTURE_DIR)
        rep_pf = report_dir or (repo_root / DEFAULT_REPORT_DIR)
        rep_pf.mkdir(parents=True, exist_ok=True)
        run_anti_fraud(repo_root)
        run_capture(repo_root, parsed_pf, cap_pf)
        _, _, sidecar_pf = locate_capture_artifacts(cap_pf, parsed_pf.key)
        run_comparator(repo_root, parsed_pf, cap_pf, rep_pf)
        run_vas(repo_root, parsed_pf.key, sidecar_pf)
        return
    with tempfile.TemporaryDirectory(prefix="nm_closure_preflight_") as tmp:
        cap_pf = Path(tmp) / "captures"
        rep_pf = Path(tmp) / "report"
        rep_pf.mkdir(parents=True, exist_ok=True)
        run_anti_fraud(repo_root)
        run_capture(repo_root, parsed_pf, cap_pf)
        _, _, sidecar_pf = locate_capture_artifacts(cap_pf, parsed_pf.key)
        run_comparator(repo_root, parsed_pf, cap_pf, rep_pf)
        run_vas(repo_root, parsed_pf.key, sidecar_pf)


def close_visual_key(
    *,
    key: str,
    repo_root: Path = ROOT,
    dry_run: bool = False,
    capture_dir: Path | None = None,
    report_dir: Path | None = None,
    preflight: bool = False,
) -> EvidenceBuild:
    repo_root = repo_root.resolve()

    if preflight:
        # Run the pipeline in the working tree BEFORE setting up the worktree.
        # Aborts early on any failure, saving ~30-60s of worktree setup +
        # capture on broken code. The worktree closure below re-runs the
        # same pipeline; preflight is a cheap early-exit guard, NOT evidence.
        # Evidence is always built inside the worktree.
        #
        # Any GateError raised here propagates to main(), which catches it as
        # ClosureError and returns the right exit code. We deliberately do NOT
        # try/except here: close_visual_key() must return EvidenceBuild on
        # success or raise ClosureError on failure — never int.
        run_preflight(
            repo_root=repo_root,
            key=key,
            capture_dir=capture_dir,
            report_dir=report_dir,
        )
        print("preflight: PASS - proceeding to worktree closure", file=sys.stderr)
    parsed = parse_key(key)
    ensure_clean_for_closure(repo_root)
    commit_head = git_rev_parse(repo_root, "HEAD")
    assert_handoff_key_open(repo_root, parsed.key)

    if capture_dir is None and report_dir is None:
        with temporary_worktree(repo_root, commit_head) as worktree:
            build = regenerate_record_for_key(
                repo_root=worktree,
                key=parsed.key,
                commit_head=commit_head,
            )
    else:
        build = regenerate_record_for_key(
            repo_root=repo_root,
            key=parsed.key,
            commit_head=commit_head,
            capture_dir=capture_dir,
            report_dir=report_dir,
        )

    if dry_run:
        return build

    write_record(repo_root, build)
    update_handoff_closure(
        handoff_path=repo_root / HANDOFF,
        key=parsed.key,
        record_sha256=build.record_sha256,
        record_path=build.record_path,
        commit_head=commit_head,
    )
    return build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Close one visual handoff key with replayable evidence.")
    parser.add_argument("--key", required=True, help="Exact visual key, e.g. suite:home@light")
    parser.add_argument("--dry-run", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--capture-dir", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--report-dir", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run capture+compare+vas in the working tree before worktree setup; "
             "abort early on failure (saves ~30-60s per broken attempt). "
             "Evidence is still built inside the worktree.",
    )
    args = parser.parse_args(argv)

    try:
        build = close_visual_key(
            key=args.key,
            dry_run=args.dry_run,
            capture_dir=args.capture_dir,
            report_dir=args.report_dir,
            preflight=args.preflight,
        )
    except ClosureError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    print(f"closed: {args.key}")
    print(f"evidence: {build.record_sha256}")
    print(f"evidence-record: {build.record_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
