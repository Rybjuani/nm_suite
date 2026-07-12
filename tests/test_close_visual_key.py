from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import pytest
from PIL import Image

from qa import close_visual_key as close


KEY = "suite:home@light"
COMMIT = "a" * 40


def _record(key: str = KEY, *, commit: str = COMMIT) -> dict:
    return {
        "schema": close.EVIDENCE_SCHEMA,
        "key": key,
        "commit_head": commit,
        "result": "PASS",
        "source_scope": {"schema": "nm_suite.source_scope.v1", "key": key},
        "report_sha256": "b" * 64,
    }


def _build(key: str = KEY, *, commit: str = COMMIT) -> close.EvidenceBuild:
    record = _record(key, commit=commit)
    return close.EvidenceBuild(
        record=record,
        record_sha256=close.canonical_record_sha256(record),
        record_path=close.active_record_path(key),
    )


def _patch_repo_guards(monkeypatch, *, target_set=(KEY,)) -> None:
    monkeypatch.setattr(close, "ensure_clean_for_closure", lambda _root: None)
    monkeypatch.setattr(close, "git_rev_parse", lambda _root, revision="HEAD": COMMIT)
    monkeypatch.setattr(close, "resolve_target_set", lambda _root, explicit=None: set(target_set))


def _write_active(root: Path, record: dict) -> Path:
    path = root / close.active_record_path(record["key"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def test_schema_and_scoped_clean_check_cover_new_authority():
    assert close.EVIDENCE_SCHEMA == "nm_suite.evidence_record.v2"
    assert "assets" in close.SCOPED_STATUS_PATHS
    assert "docs/closure_evidence" in close.SCOPED_STATUS_PATHS
    assert close.ACTIVE_DIR == Path("docs/closure_evidence/active")


def test_record_hash_is_canonical_and_key_parser_is_strict():
    left = {"b": [2, 1], "a": {"z": "same", "n": 1}}
    right = {"a": {"n": 1, "z": "same"}, "b": [2, 1]}

    assert close.canonical_record_sha256(left) == close.canonical_record_sha256(right)
    assert close.parse_key(KEY).view == "home"
    with pytest.raises(close.PreflightError, match="invalid_key"):
        close.parse_key("suite:home@sepia")


def test_explicit_target_set_rejects_duplicates_and_unknown_manifest_keys(monkeypatch, tmp_path):
    monkeypatch.setattr(close, "manifest_keys", lambda _root: (KEY,))

    with pytest.raises(close.PreflightError, match="duplicate_target_key"):
        close.resolve_target_set(tmp_path, [KEY, KEY])
    with pytest.raises(close.PreflightError, match="target_key_not_in_manifest"):
        close.resolve_target_set(tmp_path, ["suite:missing@light"])


def test_vas_summary_requires_capture_contract_and_zero_blocking_findings(tmp_path):
    sidecar = tmp_path / "introspection.json"
    sidecar.write_text(
        json.dumps(
            [
                {
                    "surface_key": KEY,
                    "fail_count": 0,
                    "divergences": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    capture = {
        "success": True,
        "technical_capture_valid": True,
        "state_evidence_valid": True,
        "capture_status": "CAPTURED_VALID",
    }

    summary, assertion = close.build_vas_summary(KEY, sidecar, capture, True)

    assert summary == {
        "schema": "nm_suite.vas_summary.v1",
        "key": KEY,
        "pass": True,
        "fail_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "capture_valid": True,
    }
    assert assertion is None
    capture["capture_status"] = "REQUIRES_DATA_STATE"
    summary, _ = close.build_vas_summary(KEY, sidecar, capture, True)
    assert summary["pass"] is False
    assert summary["capture_valid"] is False


def _write_capture(capture_dir: Path, key: str, run_id: str, *, commit: str = COMMIT) -> None:
    capture_dir.mkdir(parents=True, exist_ok=True)
    png_name = "suite-home-light-4x4.png"
    Image.new("RGB", (4, 4), (10, 20, 30)).save(capture_dir / png_name)
    sidecar = capture_dir.parent / "_visual_auditor_spec" / "introspection.json"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(
        json.dumps([{"surface_key": key, "fail_count": 0, "divergences": []}]),
        encoding="utf-8",
    )
    (capture_dir / "CAPTURE_MANIFEST.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "key": key,
                        "file": png_name,
                        "success": True,
                        "technical_capture_valid": True,
                        "state_evidence_valid": True,
                        "capture_status": "CAPTURED_VALID",
                        "provenance": {
                            "capture_path": str(capture_dir / png_name),
                            "introspection_sidecar": str(sidecar),
                            "introspection_entry_id": run_id,
                            "git_head": commit,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _valid_report(path: Path, key: str = KEY) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "nm_suite.layered_report.v2",
                "report_evidence_valid": True,
                "report_scope": "PARTIAL",
                "thresholds": {"min_ssim": 0.92},
                "results": [
                    {
                        "key": key,
                        "status": "PASS",
                        "real_divergence": False,
                        "suspicious_perfect_match": False,
                        "near_perfect_match": False,
                        "state_assertion_required": False,
                        "findings": [],
                        "metrics": {},
                        "layout": {},
                        "odiff": {"available": True, "diff_percentage": 1.0},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_regenerate_builds_complete_v2_record_from_two_independent_captures(
    monkeypatch, tmp_path
):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / close.CANONICAL_MANIFEST).parent.mkdir(parents=True)
    (repo / close.CANONICAL_MANIFEST).write_text("{}\n", encoding="utf-8")
    canonical = repo / "canonical.png"
    Image.new("RGB", (4, 4), (10, 20, 30)).save(canonical)
    capture_dirs: list[Path] = []

    def fake_capture(_repo, _parsed, capture_dir):
        capture_dirs.append(Path(capture_dir))
        _write_capture(Path(capture_dir), KEY, f"run-{len(capture_dirs)}")

    def fake_comparator(_repo, _parsed, _capture_dir, report_dir):
        path = Path(report_dir) / "LAYERED_VISUAL_REPORT.json"
        _valid_report(path)
        return path

    antifraud = {
        "schema": "nm_suite.antifraud_summary.v1",
        "mode": "all",
        "scope": "default_full",
        "clean": True,
        "count": 0,
        "violations": [],
    }
    monkeypatch.setattr(
        close,
        "manifest_keys",
        lambda _root: (KEY, "suite:home@dark"),
    )
    monkeypatch.setattr(close, "run_anti_fraud", lambda _root, _path: antifraud)
    monkeypatch.setattr(close, "run_capture", fake_capture)
    monkeypatch.setattr(close, "is_modal_key", lambda _root, _key: False)
    monkeypatch.setattr(close, "run_comparator", fake_comparator)
    monkeypatch.setattr(close, "run_vas", lambda _root, _key, _sidecar: True)
    monkeypatch.setattr(close, "canonical_png_path", lambda _root, _key: canonical)
    monkeypatch.setattr(close, "measurement_tool_hashes", lambda _root: {"qa/tool.py": "c" * 64})
    monkeypatch.setattr(close, "thresholds_sha256", lambda: "d" * 64)
    monkeypatch.setattr(
        close,
        "build_source_scope",
        lambda key, **_kwargs: {"schema": "nm_suite.source_scope.v1", "key": key},
    )

    build = close.regenerate_record_for_key(
        repo_root=repo,
        key=KEY,
        commit_head=COMMIT,
        target_set={KEY, "suite:home@dark"},
        capture_dir=repo / "qa" / "_captures_v8",
        report_dir=repo / "reports",
    )

    assert len(capture_dirs) == 2
    assert capture_dirs[0].parent != capture_dirs[1].parent
    record = build.record
    assert record["schema"] == close.EVIDENCE_SCHEMA
    assert record["result"] == "PASS"
    assert record["commit_head"] == COMMIT
    assert record["canonical_png_sha256"] == close.sha256_binary(canonical)
    assert record["capture_png_sha256"] == close.sha256_binary(
        capture_dirs[0] / "suite-home-light-4x4.png"
    )
    assert record["manifest_sha256"] == close.sha256_text(repo / close.CANONICAL_MANIFEST)
    assert record["tool_hashes"] == {"qa/tool.py": "c" * 64}
    assert record["thresholds_sha256"] == "d" * 64
    assert record["determinism"]["pass"] is True
    assert record["determinism"]["first_run_id"] != record["determinism"]["second_run_id"]
    assert record["target_set"] == ["suite:home@dark", KEY]
    assert record["policy"] == {"allow": True, "reasons": []}
    assert build.record_path == close.active_record_path(KEY)


def test_close_policy_failure_never_publishes_active_record(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    handoff = tmp_path / close.HANDOFF
    handoff.write_text("original\n", encoding="utf-8")
    candidate = _build()
    monkeypatch.setattr(
        close,
        "regenerate_record_for_key",
        lambda **_kwargs: (_ for _ in ()).throw(
            close.PolicyError(["comparator_not_pass"], candidate)
        ),
    )

    with pytest.raises(close.PolicyError, match="comparator_not_pass"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            target_set={KEY},
            capture_dir=tmp_path / "capture-a",
            second_capture_dir=tmp_path / "capture-b",
            report_dir=tmp_path / "reports",
        )

    assert not (tmp_path / close.active_record_path(KEY)).exists()
    assert handoff.read_text(encoding="utf-8") == "original\n"


def test_close_publishes_record_and_generated_handoff_atomically(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    (tmp_path / close.HANDOFF).write_text("original\n", encoding="utf-8")
    build = _build()
    monkeypatch.setattr(close, "regenerate_record_for_key", lambda **_kwargs: build)
    monkeypatch.setattr(close, "load_active_records", lambda _root: {})
    monkeypatch.setattr(
        close,
        "render_handoff",
        lambda _root, active_records: f"generated:{','.join(sorted(active_records))}\n",
    )

    result = close.close_visual_key(
        key=KEY,
        repo_root=tmp_path,
        target_set={KEY},
        capture_dir=tmp_path / "capture-a",
        second_capture_dir=tmp_path / "capture-b",
        report_dir=tmp_path / "reports",
    )

    assert result == build
    assert json.loads((tmp_path / build.record_path).read_text(encoding="utf-8")) == build.record
    assert (tmp_path / close.HANDOFF).read_text(encoding="utf-8") == f"generated:{KEY}\n"


def test_renderer_failure_rolls_back_record_and_handoff(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    handoff = tmp_path / close.HANDOFF
    handoff.write_text("original\n", encoding="utf-8")
    monkeypatch.setattr(close, "regenerate_record_for_key", lambda **_kwargs: _build())
    monkeypatch.setattr(close, "load_active_records", lambda _root: {})
    monkeypatch.setattr(
        close,
        "render_handoff",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("renderer failed")),
    )

    with pytest.raises(ValueError, match="renderer failed"):
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            target_set={KEY},
            capture_dir=tmp_path / "capture-a",
            second_capture_dir=tmp_path / "capture-b",
            report_dir=tmp_path / "reports",
        )

    assert not (tmp_path / close.active_record_path(KEY)).exists()
    assert handoff.read_text(encoding="utf-8") == "original\n"


def test_near_threshold_creates_pending_candidate_without_closing(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    handoff = tmp_path / close.HANDOFF
    handoff.write_text("original\n", encoding="utf-8")
    candidate = _build()
    candidate.record["report_sha256"] = "e" * 64
    monkeypatch.setattr(
        close,
        "regenerate_record_for_key",
        lambda **_kwargs: (_ for _ in ()).throw(
            close.PolicyError(["near_threshold_requires_verified_approval"], candidate)
        ),
    )

    with pytest.raises(close.ApprovalRequired) as raised:
        close.close_visual_key(
            key=KEY,
            repo_root=tmp_path,
            target_set={KEY},
            capture_dir=tmp_path / "capture-a",
            second_capture_dir=tmp_path / "capture-b",
            report_dir=tmp_path / "reports",
        )

    pending = raised.value.pending_path
    assert pending.exists()
    payload = json.loads(pending.read_text(encoding="utf-8"))
    assert payload["candidate_sha256"] == close.canonical_record_sha256(payload["candidate"])
    assert not (tmp_path / close.active_record_path(KEY)).exists()
    assert handoff.read_text(encoding="utf-8") == "original\n"


def test_resume_pending_uses_same_measurement_without_recapture(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    candidate = _record()
    candidate.update(
        {
            "result": "BLOCKED",
            "report": {"report_sha256": "b" * 64},
            "vas_summary": {},
            "antifraud": {},
            "determinism": {},
            "state_assertion": None,
            "target_set": [KEY],
            "human_review": {"approval_url": None, "comment_id": None, "author": None},
            "policy": {"allow": False, "reasons": ["near_threshold_requires_verified_approval"]},
        }
    )
    pending = tmp_path / "pending.json"
    pending.write_text(
        json.dumps(
            {
                "schema": close.PENDING_SCHEMA,
                "candidate_sha256": close.canonical_record_sha256(candidate),
                "candidate": candidate,
            }
        ),
        encoding="utf-8",
    )
    approval = {
        "verified": True,
        "key": KEY,
        "report_sha256": "b" * 64,
        "approval_url": "https://github.com/Rybjuani/nm_suite/issues/1#issuecomment-2",
        "comment_id": 2,
        "author": "Rybjuani",
    }
    monkeypatch.setattr(close, "is_source_scope_stale", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(close, "_pending_provenance_is_current", lambda *_args: True)
    monkeypatch.setattr(close, "decide", lambda *_args: (True, []))
    monkeypatch.setattr(close, "load_active_records", lambda _root: {})
    monkeypatch.setattr(close, "render_handoff", lambda *_args, **_kwargs: "closed\n")
    monkeypatch.setattr(
        close,
        "run_capture",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("recaptured")),
    )

    build = close.resume_pending_closure(
        pending_path=pending,
        approval=approval,
        repo_root=tmp_path,
    )

    assert build.record["result"] == "PASS"
    assert build.record["human_review"]["comment_id"] == 2
    assert json.loads((tmp_path / build.record_path).read_text())["policy"]["allow"] is True


def test_resume_pending_rejects_tampered_candidate(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    candidate = _record()
    pending = tmp_path / "pending.json"
    pending.write_text(
        json.dumps(
            {
                "schema": close.PENDING_SCHEMA,
                "candidate_sha256": "0" * 64,
                "candidate": candidate,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(close.PreflightError, match="pending_closure_integrity_mismatch"):
        close.resume_pending_closure(pending_path=pending, approval={}, repo_root=tmp_path)


def test_reopen_moves_immutable_record_into_hashed_revocation_receipt(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    record = _record()
    active = _write_active(tmp_path, record)
    (tmp_path / close.HANDOFF).write_text("closed\n", encoding="utf-8")
    monkeypatch.setattr(close, "render_handoff", lambda *_args, **_kwargs: "open\n")

    result = close.reopen_visual_key(key=KEY, reason="stale_fail", repo_root=tmp_path)

    assert not active.exists()
    receipt_path = tmp_path / result.revoked_record_path
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema"] == close.REVOCATION_SCHEMA
    assert receipt["reason"] == "stale_fail"
    assert receipt["revoked_record"] == record
    assert receipt["revoked_record_sha256"] == close.canonical_record_sha256(record)
    assert (tmp_path / close.HANDOFF).read_text(encoding="utf-8") == "open\n"


def test_reopen_requires_reason_and_active_record(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    with pytest.raises(close.PreflightError, match="missing_reopen_reason"):
        close.reopen_visual_key(key=KEY, reason=" ", repo_root=tmp_path)
    with pytest.raises(close.PreflightError, match="key_not_closed"):
        close.reopen_visual_key(key=KEY, reason="invalid", repo_root=tmp_path)


def test_refresh_replaces_pass_and_reopens_policy_fail_only(monkeypatch, tmp_path):
    dark = "suite:home@dark"
    _patch_repo_guards(monkeypatch, target_set=(KEY, dark))
    first = _record(KEY, commit="1" * 40)
    second = _record(dark, commit="2" * 40)
    _write_active(tmp_path, first)
    _write_active(tmp_path, second)
    (tmp_path / close.HANDOFF).write_text("closed\n", encoding="utf-8")

    @contextmanager
    def fake_worktree(_root, _commit):
        yield tmp_path

    refreshed = _build(KEY, commit=COMMIT)

    def regenerate(**kwargs):
        if kwargs["key"] == KEY:
            return refreshed
        raise close.PolicyError(["comparator_not_pass"], _build(dark))

    monkeypatch.setattr(close, "temporary_worktree", fake_worktree)
    monkeypatch.setattr(close, "regenerate_record_for_key", regenerate)
    monkeypatch.setattr(close, "render_handoff", lambda *_args, **_kwargs: "mixed\n")

    result = close.refresh_evidence(keys=[KEY, dark], repo_root=tmp_path)

    assert result == close.RefreshResult((KEY,), (dark,))
    assert json.loads((tmp_path / close.active_record_path(KEY)).read_text())["commit_head"] == COMMIT
    assert not (tmp_path / close.active_record_path(dark)).exists()
    receipts = list((tmp_path / close.REVOKED_DIR).glob("*.json"))
    assert len(receipts) == 1
    assert json.loads(receipts[0].read_text())["reason"].startswith("stale_fail:")


def test_refresh_near_threshold_writes_pending_and_keeps_active_record(monkeypatch, tmp_path):
    _patch_repo_guards(monkeypatch)
    old = _record()
    _write_active(tmp_path, old)
    (tmp_path / close.HANDOFF).write_text("closed\n", encoding="utf-8")

    @contextmanager
    def fake_worktree(_root, _commit):
        yield tmp_path

    candidate = _build()
    candidate.record["report_sha256"] = "e" * 64
    captured: dict = {}

    def regenerate(**kwargs):
        captured.update(kwargs)
        raise close.PolicyError(["near_threshold_requires_verified_approval"], candidate)

    monkeypatch.setattr(close, "temporary_worktree", fake_worktree)
    monkeypatch.setattr(close, "regenerate_record_for_key", regenerate)
    monkeypatch.setattr(close, "render_handoff", lambda *_args, **_kwargs: "closed\n")

    result = close.refresh_evidence(keys=[KEY], repo_root=tmp_path)

    assert result.refreshed == () and result.reopened == ()
    assert len(result.pending) == 1
    payload = json.loads(result.pending[0].read_text(encoding="utf-8"))
    assert payload["candidate_sha256"] == close.canonical_record_sha256(payload["candidate"])
    # La key NO se reabre: el record viejo sigue activo y no hay revocación.
    assert json.loads((tmp_path / close.active_record_path(KEY)).read_text()) == old
    assert not list((tmp_path / close.REVOKED_DIR).glob("*.json"))
    # La operación de refresh ancla la evidencia de origen para el resume.
    assert captured["operation"]["refreshed_from_evidence"] == close.canonical_record_sha256(old)


def _refresh_pending(tmp_path: Path, old: dict, *, source_evidence: str) -> Path:
    candidate = _record()
    candidate.update(
        {
            "result": "BLOCKED",
            "report": {"report_sha256": "b" * 64},
            "vas_summary": {},
            "antifraud": {},
            "determinism": {},
            "state_assertion": None,
            "target_set": [KEY],
            "human_review": {"approval_url": None, "comment_id": None, "author": None},
            "policy": {"allow": False, "reasons": ["near_threshold_requires_verified_approval"]},
            "operation": {
                "kind": "refresh",
                "refreshed_from_commit": old["commit_head"],
                "refreshed_from_evidence": source_evidence,
            },
        }
    )
    pending = tmp_path / f"pending-{source_evidence[:8]}.json"
    pending.write_text(
        json.dumps(
            {
                "schema": close.PENDING_SCHEMA,
                "candidate_sha256": close.canonical_record_sha256(candidate),
                "candidate": candidate,
            }
        ),
        encoding="utf-8",
    )
    return pending


def test_resume_pending_refresh_replaces_active_record_only_when_source_matches(
    monkeypatch, tmp_path
):
    _patch_repo_guards(monkeypatch)
    old = _record(commit="1" * 40)
    _write_active(tmp_path, old)
    approval = {
        "verified": True,
        "key": KEY,
        "report_sha256": "b" * 64,
        "approval_url": "https://github.com/Rybjuani/nm_suite/issues/1#issuecomment-2",
        "comment_id": 2,
        "author": "Rybjuani",
    }
    monkeypatch.setattr(close, "is_source_scope_stale", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(close, "_pending_provenance_is_current", lambda *_args: True)
    monkeypatch.setattr(close, "decide", lambda *_args: (True, []))
    monkeypatch.setattr(close, "render_handoff", lambda *_args, **_kwargs: "closed\n")

    # Origen equivocado (el record activo cambió desde el refresh): rechaza.
    stale_pending = _refresh_pending(tmp_path, old, source_evidence="0" * 64)
    with pytest.raises(close.PreflightError, match="pending_refresh_source_mismatch"):
        close.resume_pending_closure(pending_path=stale_pending, approval=approval, repo_root=tmp_path)

    # Origen correcto: reemplaza el record activo con el candidato aprobado.
    pending = _refresh_pending(
        tmp_path, old, source_evidence=close.canonical_record_sha256(old)
    )
    build = close.resume_pending_closure(pending_path=pending, approval=approval, repo_root=tmp_path)

    stored = json.loads((tmp_path / build.record_path).read_text(encoding="utf-8"))
    assert stored["result"] == "PASS"
    assert stored["operation"]["kind"] == "refresh"
    assert stored["human_review"]["comment_id"] == 2

    # Sin record activo no hay refresh que reanudar.
    (tmp_path / close.active_record_path(KEY)).unlink()
    orphan_pending = _refresh_pending(
        tmp_path, old, source_evidence=close.canonical_record_sha256(old)
    )
    with pytest.raises(close.PreflightError, match="pending_refresh_key_not_closed"):
        close.resume_pending_closure(pending_path=orphan_pending, approval=approval, repo_root=tmp_path)


def test_refresh_cli_forwards_approval_resolver_and_reports_pending(monkeypatch, capsys):
    seen: dict = {}

    def fake_refresh(**kwargs):
        seen.update(kwargs)
        return close.RefreshResult((), (), (Path("reports/qa/visual_closure_pending/x.json"),))

    monkeypatch.setattr(close, "refresh_evidence", fake_refresh)

    rc = close.main(
        [
            "--refresh-evidence",
            "--keys",
            KEY,
            "--approval-url",
            "https://github.com/Rybjuani/nm_suite/issues/1#issuecomment-2",
        ]
    )

    assert rc == close.ApprovalRequired.exit_code
    assert callable(seen["approval_resolver"])
    assert "pending-approval:" in capsys.readouterr().err

    def fake_refresh_no_pending(**kwargs):
        seen.update(kwargs)
        return close.RefreshResult((), ())

    monkeypatch.setattr(close, "refresh_evidence", fake_refresh_no_pending)
    rc = close.main(["--refresh-evidence", "--keys", KEY])

    assert rc == 0
    assert seen["approval_resolver"] is None


def test_modal_back_screen_merge_preserves_both_manifest_entries(monkeypatch, tmp_path):
    modal_key = "hub:detalle-resumen-ia-0@light"
    back_key = "hub:detalle@light"
    capture_dir = tmp_path / "captures"
    _write_capture(capture_dir, modal_key, "modal")

    def fake_back_capture(_root, key, out_dir):
        assert key == back_key
        _write_capture(out_dir, back_key, "back")

    monkeypatch.setattr(close, "_modal_back_screen_key", lambda _root, _key: back_key)
    monkeypatch.setattr(close, "run_capture_for_key", fake_back_capture)
    close._ensure_modal_backdrop_capture(tmp_path, close.parse_key(modal_key), capture_dir)

    manifest = json.loads((capture_dir / "CAPTURE_MANIFEST.json").read_text())
    assert {_key.get("key") for _key in manifest["results"]} == {modal_key, back_key}


def test_stable_json_hash_ignores_random_worktree_paths(tmp_path):
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(json.dumps({"actual_dir": "C:/temp/a", "summary": {"pass": True}}))
    right.write_text(json.dumps({"actual_dir": "C:/temp/b", "summary": {"pass": True}}))

    assert close.stable_json_file_sha256(left) == close.stable_json_file_sha256(right)


def test_legacy_bulk_reopen_api_and_cli_are_removed():
    assert not hasattr(close, "reopen_legacy_all")
    with pytest.raises(SystemExit) as raised:
        close.main(["--reopen-legacy-all"])
    assert raised.value.code == 2
