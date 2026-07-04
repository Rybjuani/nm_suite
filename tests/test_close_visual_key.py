from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa import close_visual_key as close


FIX_COMMIT = "a" * 40
KEY = "suite:home@light"


def _write_handoff(root: Path, body: str) -> Path:
    path = root / "VISUAL_REPAIR_HANDOFF.md"
    path.write_text(body, encoding="utf-8")
    return path


def _record(key: str = KEY) -> dict:
    return {
        "schema": close.EVIDENCE_SCHEMA,
        "key": key,
        "commit_head": FIX_COMMIT,
        "anti_fraud_sha256": "1" * 64,
        "capture_v8_sha256": "2" * 64,
        "layered_compare_sha256": "3" * 64,
        "vas_gate_sha256": "4" * 64,
        "capture_png_sha256": "5" * 64,
        "manifest_sha256": "6" * 64,
        "report_sha256": "7" * 64,
        "sidecar_sha256": "8" * 64,
        "modal_audit_sha256": None,
        "result": "PASS",
        "metrics": {
            "changed_pixel_ratio": 0.01,
            "mean_abs_diff": 0.02,
            "windowed_ssim": 0.99,
            "max_bbox_delta_px": None,
        },
        "command_spec": {
            "capture": {
                "tool": "qa/capture_v8.py",
                "app": "suite",
                "view": "home",
                "theme": "light",
                "vas_introspect": True,
            },
            "compare": {
                "tool": "qa/layered_visual_compare.py",
                "canonical": "qa/_mockup_canonical",
                "scope": key,
            },
        },
    }


def _build(key: str = KEY) -> close.EvidenceBuild:
    record = _record(key)
    return close.EvidenceBuild(
        record=record,
        record_sha256=close.canonical_record_sha256(record),
        record_path=Path("docs/closure_evidence") / f"{close.key_safe(key)}.json",
    )


def _patch_clean_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(close, "ensure_clean_for_closure", lambda repo_root: None)
    monkeypatch.setattr(close, "git_rev_parse", lambda repo_root, revision="HEAD": FIX_COMMIT)


def test_close_tool_rejects_dirty_working_tree(monkeypatch, tmp_path):
    handoff = _write_handoff(tmp_path, f"- [ ] `{KEY}` pending\n")

    def dirty(_repo_root):
        raise close.PreflightError("dirty_working_tree")

    monkeypatch.setattr(close, "ensure_clean_for_closure", dirty)

    with pytest.raises(close.PreflightError, match="dirty_working_tree"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            capture_dir=tmp_path / "captures",
            report_dir=tmp_path / "reports",
        )

    assert handoff.read_text(encoding="utf-8") == f"- [ ] `{KEY}` pending\n"


def test_close_tool_rejects_unknown_key(monkeypatch, tmp_path):
    _write_handoff(tmp_path, "- [ ] `suite:other@light` pending\n")
    _patch_clean_git(monkeypatch)

    with pytest.raises(close.PreflightError, match="unknown_key"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            capture_dir=tmp_path / "captures",
            report_dir=tmp_path / "reports",
        )


def test_close_tool_rejects_already_closed_key(monkeypatch, tmp_path):
    _write_handoff(tmp_path, f"- [x] `{KEY}` done\n")
    _patch_clean_git(monkeypatch)

    with pytest.raises(close.PreflightError, match="key_already_closed"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            capture_dir=tmp_path / "captures",
            report_dir=tmp_path / "reports",
        )


def test_close_tool_aborts_if_capture_fails_without_touching_handoff(monkeypatch, tmp_path):
    handoff = _write_handoff(tmp_path, f"- [ ] `{KEY}` pending\n")
    _patch_clean_git(monkeypatch)

    def fail(**_kwargs):
        raise close.GateError("capture_failed")

    monkeypatch.setattr(close, "regenerate_record_for_key", fail)

    with pytest.raises(close.GateError, match="capture_failed"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            capture_dir=tmp_path / "captures",
            report_dir=tmp_path / "reports",
        )

    assert handoff.read_text(encoding="utf-8") == f"- [ ] `{KEY}` pending\n"


def test_close_tool_aborts_if_comparator_fails_without_touching_handoff(monkeypatch, tmp_path):
    handoff = _write_handoff(tmp_path, f"- [ ] `{KEY}` pending\n")
    _patch_clean_git(monkeypatch)

    def fail(**_kwargs):
        raise close.GateError("comparator_not_pass")

    monkeypatch.setattr(close, "regenerate_record_for_key", fail)

    with pytest.raises(close.GateError, match="comparator_not_pass"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            capture_dir=tmp_path / "captures",
            report_dir=tmp_path / "reports",
        )

    assert handoff.read_text(encoding="utf-8") == f"- [ ] `{KEY}` pending\n"


def test_close_tool_pass_writes_versioned_record_and_handoff_note(monkeypatch, tmp_path):
    _write_handoff(tmp_path, f"- [ ] `{KEY}` pending\n")
    _patch_clean_git(monkeypatch)
    build = _build()
    monkeypatch.setattr(close, "regenerate_record_for_key", lambda **_kwargs: build)

    result = close.close_visual_key(
        key=KEY,
        repo_root=tmp_path,
        capture_dir=tmp_path / "captures",
        report_dir=tmp_path / "reports",
    )

    assert result.record_sha256 == build.record_sha256
    record_path = tmp_path / build.record_path
    assert record_path.exists()
    assert json.loads(record_path.read_text(encoding="utf-8")) == build.record
    handoff = (tmp_path / "VISUAL_REPAIR_HANDOFF.md").read_text(encoding="utf-8")
    assert f"- [x] `{KEY}` pending" in handoff
    assert f"  - evidence: {build.record_sha256}" in handoff
    assert f"  - evidence-record: {build.record_path.as_posix()}" in handoff
    assert f"  - commit: {FIX_COMMIT}" in handoff
    assert "  - closed-by: close_visual_key.py" in handoff


def test_close_visual_key_modal_runs_modal_audit(monkeypatch, tmp_path):
    """When the canonical manifest marks a key as modal, close_visual_key must run
    the modal backdrop audit and record its hash in the evidence record."""
    modal_key = "suite:dbt-practice-stop@light"
    _write_handoff(tmp_path, f"- [ ] `{modal_key}` pending\n")
    _patch_clean_git(monkeypatch)

    # Fake modal audit report
    audit_dir = tmp_path / "reports" / "modal_audit_suite-dbt-practice-stop-light"
    audit_dir.mkdir(parents=True)
    audit_path = audit_dir / "AUDIT.json"
    audit_path.write_text(json.dumps({"summary": {"test_blur_pass": True}}, sort_keys=True), encoding="utf-8")

    # Mock everything expensive; only test the orchestration decision
    monkeypatch.setattr(close, "sha256_file", lambda path: "a" * 64)
    monkeypatch.setattr(close, "stable_json_file_sha256", lambda path: "b" * 64)
    monkeypatch.setattr(close, "run_anti_fraud", lambda repo_root: None)
    monkeypatch.setattr(close, "run_capture", lambda repo_root, parsed, capture_dir: None)
    monkeypatch.setattr(close, "_ensure_modal_backdrop_capture", lambda repo_root, parsed, capture_dir: None)
    monkeypatch.setattr(close, "run_comparator", lambda repo_root, parsed, capture_dir, report_dir: report_path)
    monkeypatch.setattr(close, "run_vas", lambda repo_root, key, sidecar_path: None)
    monkeypatch.setattr(close, "run_modal_audit", lambda repo_root, parsed, capture_dir, report_dir: audit_path)
    monkeypatch.setattr(close, "locate_capture_artifacts", lambda capture_dir, key: (Path("m.json"), Path("p.png"), Path("s.json")))
    monkeypatch.setattr(close, "is_modal_key", lambda repo_root, key: True)

    # Minimal report for build_evidence_record
    report_path = tmp_path / "LAYERED_VISUAL_REPORT.json"
    report_path.write_text(
        json.dumps(
            {
                "report_evidence_valid": True,
                "results": [
                    {
                        "key": modal_key,
                        "status": "PASS",
                        "suspicious_perfect_match": False,
                        "near_perfect_match": False,
                        "metrics": {"changed_pixel_ratio": 0, "mean_abs_diff": 0, "windowed_ssim": 1},
                        "layout": {"max_bbox_delta_px": None},
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(close, "run_comparator", lambda repo_root, parsed, capture_dir, report_dir: report_path)

    build = close.regenerate_record_for_key(
        repo_root=tmp_path,
        key=modal_key,
        commit_head=FIX_COMMIT,
        capture_dir=tmp_path / "captures",
        report_dir=tmp_path / "reports",
    )

    assert build.record["modal_audit_sha256"] is not None
    assert build.record["modal_audit_sha256"] == close.stable_json_file_sha256(audit_path)


def test_record_hash_is_deterministic_for_same_logical_inputs():
    left = {"b": [2, 1], "a": {"z": "same", "n": 1}}
    right = {"a": {"n": 1, "z": "same"}, "b": [2, 1]}

    assert close.canonical_record_sha256(left) == close.canonical_record_sha256(right)
