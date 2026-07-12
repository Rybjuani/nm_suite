from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from qa import replay_visual_closure as replay
from qa.closure_policy import (
    ANTIFRAUD_SUMMARY_SCHEMA,
    DETERMINISM_SCHEMA,
    REPORT_SCHEMA,
    VAS_SUMMARY_SCHEMA,
)
from qa.hash_utils import sha256_canonical_json
from qa.layered_visual_compare import LayeredThresholds


KEY = "suite:home@light"
COMMIT = "a" * 40
HASH = "b" * 64


def _valid_report(key: str = KEY, *, report_sha: str = HASH) -> dict:
    return {
        "schema": REPORT_SCHEMA,
        "report_evidence_valid": True,
        "report_scope": "PARTIAL",
        "report_sha256": report_sha,
        "thresholds": LayeredThresholds().to_dict(),
        "modal_audit_required": False,
        "modal_audit": None,
        "results": [
            {
                "key": key,
                "status": "PASS",
                "real_divergence": False,
                "suspicious_perfect_match": False,
                "near_perfect_match": False,
                "state_assertion_required": False,
                "findings": [],
                "metrics": {"changed_pixel_ratio": 0.01},
                "layout": {},
                "odiff": {"available": True, "diff_percentage": 1.0},
            }
        ],
    }


def _valid_vas(key: str = KEY) -> dict:
    return {
        "schema": VAS_SUMMARY_SCHEMA,
        "key": key,
        "pass": True,
        "fail_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "capture_valid": True,
    }


def _valid_antifraud() -> dict:
    return {
        "schema": ANTIFRAUD_SUMMARY_SCHEMA,
        "mode": "all",
        "scope": "default_full",
        "clean": True,
        "count": 0,
        "violations": [],
    }


def _valid_determinism(key: str = KEY) -> dict:
    return {
        "schema": DETERMINISM_SCHEMA,
        "key": key,
        "pass": True,
        "changed_ratio": 0.0,
        "first_run_id": "run-a",
        "second_run_id": "run-b",
        "first_git_head": COMMIT,
        "second_git_head": COMMIT,
    }


def _valid_record(key: str = KEY) -> dict:
    return {
        "schema": replay.EVIDENCE_SCHEMA,
        "key": key,
        "commit_head": COMMIT,
        "result": "PASS",
        "canonical_png_sha256": "1" * 64,
        "capture_png_sha256": "2" * 64,
        "manifest_sha256": "3" * 64,
        "capture_manifest_sha256": "4" * 64,
        "tool_hashes": {"qa/tool.py": "5" * 64},
        "thresholds_sha256": "6" * 64,
        "source_scope": {"schema": "nm_suite.source_scope.v1", "key": key},
        "report_sha256": HASH,
        "sidecar_sha256": "7" * 64,
        "modal_audit_sha256": None,
        "report": _valid_report(key),
        "vas_summary": _valid_vas(key),
        "antifraud": _valid_antifraud(),
        "determinism": _valid_determinism(key),
        "state_assertion": None,
        "modal_audit": None,
        "target_set": [key],
        "human_review": {"approval_url": None, "comment_id": None, "author": None},
        "policy": {"allow": True, "reasons": []},
        "operation": {"kind": "close"},
    }


def _measurement(record: dict) -> dict:
    return {
        "report": copy.deepcopy(record["report"]),
        "vas_summary": copy.deepcopy(record["vas_summary"]),
        "antifraud": copy.deepcopy(record["antifraud"]),
        "determinism": copy.deepcopy(record["determinism"]),
        "state_assertion": record["state_assertion"],
        "modal_audit": record["modal_audit"],
    }


def _universe() -> tuple[str, ...]:
    return tuple(f"suite:test-{index:03d}@light" for index in range(116))


def test_replay_has_no_import_or_orchestration_dependency_on_closer():
    source = Path(replay.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert not any(name.endswith("close_visual_key") for name in imported)
    assert "regenerate_record_for_key" not in source


@pytest.mark.parametrize("flag", ["--no-regen", "--skip-legacy"])
def test_removed_replay_flags_are_rejected(flag):
    with pytest.raises(SystemExit) as raised:
        replay.main(["--structural-precheck", "--base", "HEAD", flag])
    assert raised.value.code == 2


def test_threshold_hash_is_rederived_from_source_without_importing_runtime():
    source = Path("qa/layered_visual_compare.py").read_text(encoding="utf-8")

    assert replay.thresholds_sha_from_source(source) == sha256_canonical_json(
        LayeredThresholds().to_dict()
    )


def test_record_sanity_accepts_complete_v2_and_rejects_tampering():
    record = _valid_record()
    assert replay._record_sanity_reasons(record, KEY) == []

    record["target_set"] = []
    record["report"]["report_sha256"] = "f" * 64
    reasons = replay._record_sanity_reasons(record, KEY)
    assert "target_set_invalid" in reasons
    assert "report_identity_mismatch" in reasons


def test_active_record_filename_is_authority_for_key(tmp_path):
    active = tmp_path / replay.ACTIVE_DIR
    active.mkdir(parents=True)
    wrong = _valid_record("suite:home@dark")
    (active / "suite_home-light.json").write_text(json.dumps(wrong), encoding="utf-8")

    records, failures = replay._read_active_records(tmp_path)

    assert records == {}
    assert failures == [replay.ReplayFailure(KEY, "record_filename_key_mismatch")]


def test_closed_handoff_parser_detects_duplicates():
    text = f"- [x] `{KEY}`\n- [x] `{KEY}`\n- [ ] `suite:home@dark`\n"
    closed, duplicates = replay._closed_handoff_keys(text)
    assert closed == {KEY}
    assert duplicates == [KEY]


def test_structural_precheck_passes_truthfully_with_zero_active_records(
    monkeypatch, tmp_path
):
    handoff = "# generated\n"
    (tmp_path / replay.HANDOFF).write_text(handoff, encoding="utf-8")
    monkeypatch.setattr(replay, "manifest_keys", lambda _root: _universe())
    monkeypatch.setattr(replay, "_read_active_records", lambda _root: ({}, []))
    monkeypatch.setattr(replay, "git_rev_parse", lambda _root, _base: COMMIT)
    monkeypatch.setattr(replay, "git_changed_paths", lambda _root, _base: [])

    result = replay.audit_structure(
        repo_root=tmp_path,
        base="pre-branch",
        render_func=lambda _root: handoff,
    )

    assert result.passed is True
    assert result.active_records == 0
    assert result.checked_keys == 0
    assert result.replayed_keys == 0


def test_structural_precheck_blocks_handoff_drift(monkeypatch, tmp_path):
    (tmp_path / replay.HANDOFF).write_text("manual edit\n", encoding="utf-8")
    monkeypatch.setattr(replay, "manifest_keys", lambda _root: _universe())
    monkeypatch.setattr(replay, "_read_active_records", lambda _root: ({}, []))

    result = replay.audit_structure(
        repo_root=tmp_path,
        render_func=lambda _root: "generated\n",
    )

    assert result.passed is False
    assert replay.ReplayFailure("<handoff>", "handoff_render_drift") in result.failures


def test_structural_precheck_blocks_unmapped_source_and_kernel_plus_closure(
    monkeypatch, tmp_path
):
    handoff = "generated\n"
    (tmp_path / replay.HANDOFF).write_text(handoff, encoding="utf-8")
    monkeypatch.setattr(replay, "manifest_keys", lambda _root: _universe())
    monkeypatch.setattr(replay, "_read_active_records", lambda _root: ({}, []))
    monkeypatch.setattr(replay, "git_rev_parse", lambda _root, _base: COMMIT)
    monkeypatch.setattr(
        replay,
        "git_changed_paths",
        lambda _root, _base: [
            "app/new_visual.py",
            "qa/closure_policy.py",
            "docs/closure_evidence/active/suite_home-light.json",
        ],
    )

    result = replay.audit_structure(
        repo_root=tmp_path,
        base="pre-branch",
        render_func=lambda _root: handoff,
    )
    reasons = {(failure.key, failure.reason) for failure in result.failures}
    assert ("app/new_visual.py", "unmapped_visual_source") in reasons
    assert (KEY, "kernel_changed_with_visual_closure") in reasons


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


def test_class_a_reproduces_historical_bytes_and_detects_current_canonical_edit(
    monkeypatch, tmp_path
):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    canonical_rel = "qa/_mockup_canonical/suite-home-light-4x4.png"
    (repo / canonical_rel).parent.mkdir(parents=True)
    canonical_bytes = b"\x89PNG\r\nIDAT\x00\r\n"
    (repo / canonical_rel).write_bytes(canonical_bytes)
    manifest = {
        "captures": [
            {
                "view": "suite-home",
                "theme": "light",
                "file": Path(canonical_rel).name,
            }
        ]
    }
    manifest_path = repo / replay.CANONICAL_MANIFEST
    manifest_path.write_text(json.dumps(manifest) + "\r\n", encoding="utf-8", newline="")
    tool = repo / "qa" / "tool.py"
    tool.write_text("first\r\nsecond\r\n", encoding="utf-8", newline="")
    comparator = repo / "qa" / "layered_visual_compare.py"
    comparator.write_text(
        "class LayeredThresholds:\n"
        "    min_ssim: float = 0.92\n"
        "    max_changed_pixel_ratio: float = 0.08\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")
    record = {
        "key": KEY,
        "commit_head": commit,
        "canonical_png_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "manifest_sha256": replay._sha256_text_bytes(manifest_path.read_bytes()),
        "tool_hashes": {"qa/tool.py": replay._sha256_text_bytes(tool.read_bytes())},
        "thresholds_sha256": replay.thresholds_sha_from_source(
            comparator.read_text(encoding="utf-8")
        ),
        "source_scope": {},
    }
    monkeypatch.setattr(replay, "source_scope_matches_revision", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(replay, "is_source_scope_stale", lambda *_args, **_kwargs: False)

    assert replay._class_a_reasons(record, repo) == []

    (repo / canonical_rel).write_bytes(canonical_bytes + b"tamper")
    assert "canonical_png_sha256_mismatch" in replay._class_a_reasons(record, repo)


def test_external_approval_is_reverified_against_original_report():
    record = _valid_record()
    record["report"]["results"][0]["findings"] = ["near_threshold:changed_pixel_ratio"]
    record["human_review"] = {
        "approval_url": "https://github.com/Rybjuani/nm_suite/issues/1#issuecomment-2",
        "comment_id": 2,
        "author": "Rybjuani",
    }
    calls = []

    def checker(review, **kwargs):
        calls.append((review, kwargs))
        return {
            "verified": True,
            "key": kwargs["key"],
            "report_sha256": kwargs["report_sha256"],
            **review,
        }

    approval, reasons = replay._verified_approval(record, Path.cwd(), checker)

    assert reasons == []
    assert approval["verified"] is True
    assert calls[0][1]["report_sha256"] == HASH


def test_full_replay_accepts_new_metrics_when_new_measurement_allows(monkeypatch, tmp_path):
    record = _valid_record()
    measurement = _measurement(record)
    measurement["report"]["results"][0]["metrics"] = {"changed_pixel_ratio": 0.02}
    structural = replay.ReplayResult("structural", 1, 1, 0, ())
    monkeypatch.setattr(replay, "audit_structure", lambda **_kwargs: structural)
    monkeypatch.setattr(replay, "_read_active_records", lambda _root: ({KEY: record}, []))

    result = replay.replay_full(
        repo_root=tmp_path,
        all_closed=True,
        measurement_runner=lambda _root, _key, _commit: measurement,
    )

    assert result.passed is True
    assert result.replayed_keys == 1


def test_full_replay_blocks_fresh_measurement_that_fails_policy(monkeypatch, tmp_path):
    record = _valid_record()
    measurement = _measurement(record)
    measurement["report"]["results"][0]["status"] = "FAIL"
    measurement["report"]["results"][0]["real_divergence"] = True
    structural = replay.ReplayResult("structural", 1, 1, 0, ())
    monkeypatch.setattr(replay, "audit_structure", lambda **_kwargs: structural)
    monkeypatch.setattr(replay, "_read_active_records", lambda _root: ({KEY: record}, []))

    result = replay.replay_full(
        repo_root=tmp_path,
        all_closed=True,
        measurement_runner=lambda _root, _key, _commit: measurement,
    )

    assert result.passed is False
    assert any("regenerated_policy_blocked" in failure.reason for failure in result.failures)


def test_v1_records_are_quarantined_and_active_authority_starts_empty():
    root = Path("docs/closure_evidence")
    invalidated = list((root / "invalidated_v1").glob("*.json"))
    revoked = list((root / "invalidated_v1" / "revoked").glob("*.json"))

    assert len(invalidated) == 116
    assert len(revoked) == 2
    assert list((root / "active").glob("*.json")) == []
    assert all(json.loads(path.read_text())["schema"] == "nm_suite.evidence_record.v1" for path in invalidated)
    assert "forensic-pre-v3.1" in (root / "invalidated_v1" / "README.md").read_text()
