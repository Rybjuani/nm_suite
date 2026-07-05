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


def _write_capture_manifest(capture_dir: Path, results: list[dict]) -> None:
    capture_dir.mkdir(parents=True, exist_ok=True)
    (capture_dir / "CAPTURE_MANIFEST.json").write_text(
        json.dumps({"results": results}, ensure_ascii=False), encoding="utf-8"
    )


def test_ensure_modal_backdrop_capture_preserves_modal_manifest_entry(monkeypatch, tmp_path):
    """Regression: capture_v8.py fully overwrites CAPTURE_MANIFEST.json on every
    invocation instead of appending to it. Capturing the modal's back-screen key
    straight into the modal's own capture_dir used to erase the modal key's
    manifest entry, breaking locate_capture_artifacts with
    capture_manifest_missing_key (reproduced against `hub:detalle-resumen-ia-0@light`).
    """
    modal_key = "hub:detalle-resumen-ia-0@light"
    back_key = "hub:detalle@light"
    capture_dir = tmp_path / "captures"

    modal_png = "hub-detalle-resumen-ia-0-light-960x600.png"
    back_png = "hub-detalle-light-960x600.png"

    _write_capture_manifest(
        capture_dir,
        [
            {
                "key": modal_key,
                "file": modal_png,
                "app": "hub",
                "view": "detalle-resumen-ia-0",
                "theme": "light",
            }
        ],
    )
    (capture_dir / modal_png).write_bytes(b"modal-png")

    sidecar_dir = capture_dir.parent / "_visual_auditor_spec"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    (sidecar_dir / "introspection.json").write_text("{}", encoding="utf-8")

    def fake_run_capture_for_key(_repo_root, key, out_dir):
        assert key == back_key
        # Simulate capture_v8.py: a fresh out-dir gets its own, unrelated manifest
        # with no knowledge of anything captured previously elsewhere.
        _write_capture_manifest(
            out_dir,
            [
                {
                    "key": back_key,
                    "file": back_png,
                    "app": "hub",
                    "view": "detalle",
                    "theme": "light",
                }
            ],
        )
        (out_dir / back_png).write_bytes(b"back-png")

    monkeypatch.setattr(close, "run_capture_for_key", fake_run_capture_for_key)
    monkeypatch.setattr(close, "_modal_back_screen_key", lambda repo_root, key: back_key)

    parsed = close.parse_key(modal_key)
    close._ensure_modal_backdrop_capture(tmp_path, parsed, capture_dir)

    # The modal key must still be resolvable after merging the back-screen capture.
    manifest_path, png_path, _sidecar = close.locate_capture_artifacts(capture_dir, modal_key)
    assert manifest_path == capture_dir / "CAPTURE_MANIFEST.json"
    assert png_path == capture_dir / modal_png

    # The back-screen PNG must land alongside it for the modal backdrop audit.
    assert (capture_dir / back_png).exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    keys = {r.get("key") for r in manifest["results"]}
    assert keys == {modal_key, back_key}


def test_stable_json_file_sha256_ignores_modal_audit_worktree_paths(tmp_path):
    """Regression: audit_modal_backdrop_blur.py's AUDIT.json embeds the resolved
    absolute path of the capture dirs (inputs.actual_dir / inputs.canonical_dir).
    Every closure/replay run resolves these inside a freshly created, randomly
    named temp worktree, so two independent runs over identical code/pixels
    produced two different modal_audit_sha256 values (and thus two different
    whole-record hashes) purely from path noise, breaking replay --regen for
    every modal key."""
    run1 = {
        "inputs": {
            "actual_dir": r"C:\Users\x\AppData\Local\Temp\nm_visual_worktree_aaaaaaaa\worktree\qa\_captures_v8",
            "canonical_dir": r"C:\Users\x\AppData\Local\Temp\nm_visual_worktree_aaaaaaaa\worktree\qa\_mockup_canonical",
            "keys": ["hub:detalle-resumen-ia-0@dark"],
        },
        "summary": {"test_blur_pass": True},
    }
    run2 = {
        "inputs": {
            "actual_dir": r"C:\Users\x\AppData\Local\Temp\nm_visual_worktree_bbbbbbbb\worktree\qa\_captures_v8",
            "canonical_dir": r"C:\Users\x\AppData\Local\Temp\nm_visual_worktree_bbbbbbbb\worktree\qa\_mockup_canonical",
            "keys": ["hub:detalle-resumen-ia-0@dark"],
        },
        "summary": {"test_blur_pass": True},
    }
    path1 = tmp_path / "audit1.json"
    path2 = tmp_path / "audit2.json"
    path1.write_text(json.dumps(run1), encoding="utf-8")
    path2.write_text(json.dumps(run2), encoding="utf-8")

    assert close.stable_json_file_sha256(path1) == close.stable_json_file_sha256(path2)


def test_record_hash_is_deterministic_for_same_logical_inputs():
    left = {"b": [2, 1], "a": {"z": "same", "n": 1}}
    right = {"a": {"n": 1, "z": "same"}, "b": [2, 1]}

    assert close.canonical_record_sha256(left) == close.canonical_record_sha256(right)


# ─── reopen (sanctioned revocation) ─────────────────────────────────────────


def _write_closed_fixture(root: Path, key: str = KEY) -> close.EvidenceBuild:
    """A closed key with real record file + matching evidence note."""
    build = _build(key)
    record_path = root / build.record_path
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(
        json.dumps(build.record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_handoff(
        root,
        f"- [x] `{key}` done\n"
        f"  - evidence: {build.record_sha256}\n"
        f"  - evidence-record: {build.record_path.as_posix()}\n"
        f"  - commit: {FIX_COMMIT}\n"
        "  - closed-by: close_visual_key.py\n",
    )
    return build


def test_reopen_moves_record_and_rewrites_checkbox(monkeypatch, tmp_path):
    build = _write_closed_fixture(tmp_path)
    _patch_clean_git(monkeypatch)

    result = close.reopen_visual_key(key=KEY, reason="cierre con gaming", repo_root=tmp_path)

    assert result.revoked_evidence == build.record_sha256
    assert not (tmp_path / build.record_path).exists()
    revoked = tmp_path / "docs" / "closure_evidence" / "revoked" / f"{close.key_safe(KEY)}.json"
    assert revoked.exists()
    assert json.loads(revoked.read_text(encoding="utf-8")) == build.record

    handoff = (tmp_path / "VISUAL_REPAIR_HANDOFF.md").read_text(encoding="utf-8")
    assert f"- [ ] `{KEY}` done" in handoff
    assert "  - reopened: cierre con gaming" in handoff
    assert f"  - revoked-evidence: {build.record_sha256}" in handoff
    assert f"  - revoked-record: docs/closure_evidence/revoked/{close.key_safe(KEY)}.json" in handoff
    assert "  - evidence: " not in handoff
    assert "  - evidence-record: " not in handoff
    assert "  - closed-by:" not in handoff


def test_reopen_requires_reason(monkeypatch, tmp_path):
    _write_closed_fixture(tmp_path)
    _patch_clean_git(monkeypatch)

    with pytest.raises(close.PreflightError, match="missing_reopen_reason"):
        close.reopen_visual_key(key=KEY, reason="  ", repo_root=tmp_path)


def test_reopen_rejects_open_key(monkeypatch, tmp_path):
    _write_handoff(tmp_path, f"- [ ] `{KEY}` pending\n")
    _patch_clean_git(monkeypatch)

    with pytest.raises(close.PreflightError, match="key_not_closed"):
        close.reopen_visual_key(key=KEY, reason="x", repo_root=tmp_path)


def test_reopen_rejects_legacy_closure(monkeypatch, tmp_path):
    _write_handoff(
        tmp_path,
        f"- [x] `{KEY}` old\n"
        "  - legacy: true\n"
        "  - legacy-reason: pre_replay_era\n",
    )
    _patch_clean_git(monkeypatch)

    with pytest.raises(close.PreflightError, match="legacy_key_reopen_unsupported"):
        close.reopen_visual_key(key=KEY, reason="x", repo_root=tmp_path)


def test_reopen_rejects_tampered_record(monkeypatch, tmp_path):
    build = _write_closed_fixture(tmp_path)
    record_path = tmp_path / build.record_path
    tampered = dict(build.record)
    tampered["metrics"] = dict(tampered["metrics"], changed_pixel_ratio=0.0)
    record_path.write_text(json.dumps(tampered, sort_keys=True), encoding="utf-8")
    _patch_clean_git(monkeypatch)

    with pytest.raises(close.PreflightError, match="evidence_integrity_mismatch"):
        close.reopen_visual_key(key=KEY, reason="x", repo_root=tmp_path)

    # Nothing moved, nothing rewritten.
    assert record_path.exists()
    assert "- [x]" in (tmp_path / "VISUAL_REPAIR_HANDOFF.md").read_text(encoding="utf-8")


# ─── reopen_legacy_all (governance bulk reset) ──────────────────────────────


def test_reopen_legacy_all_flips_only_legacy_and_strips_notes(tmp_path):
    handoff = (
        "## Checklist\n"
        "\n"
        "### Fam\n"
        "- [x] `suite:legacy-a@light` - severity=high; changed=0.20\n"
        "  - legacy: true\n"
        "  - legacy-reason: pre_replay_era\n"
        "  - Closure evidence (2026): manual panel review, no overlay.\n"
        "- [x] `suite:evidence-b@light` - severity=high; changed=0.05\n"
        "  - evidence: " + "d" * 64 + "\n"
        "  - evidence-record: docs/closure_evidence/suite_evidence-b-light.json\n"
        "  - commit: " + "a" * 40 + "\n"
        "- [ ] `suite:open-c@light` - severity=medium; changed=0.09\n"
        "- [x] `suite:legacy-d@dark` - severity=medium; changed=0.10\n"
        "  - legacy: true\n"
    )
    path = _write_handoff(tmp_path, handoff)

    reopened = close.reopen_legacy_all(repo_root=tmp_path)

    assert reopened == ["suite:legacy-a@light", "suite:legacy-d@dark"]
    text = path.read_text(encoding="utf-8")
    # legacy items are now open, with notes stripped
    assert "- [ ] `suite:legacy-a@light`" in text
    assert "- [ ] `suite:legacy-d@dark`" in text
    assert "legacy: true" not in text
    assert "manual panel review" not in text
    # evidence-backed closure untouched
    assert "- [x] `suite:evidence-b@light`" in text
    assert "evidence: " + "d" * 64 in text
    # already-open item untouched
    assert "- [ ] `suite:open-c@light`" in text
    # inline metadata preserved on reopened line (target_scope tiers on it)
    assert "severity=high; changed=0.20" in text


def test_reopen_legacy_all_is_idempotent(tmp_path):
    handoff = (
        "## Checklist\n"
        "- [x] `suite:legacy-a@light` - severity=high\n"
        "  - legacy: true\n"
    )
    _write_handoff(tmp_path, handoff)
    assert close.reopen_legacy_all(repo_root=tmp_path) == ["suite:legacy-a@light"]
    # second run finds nothing
    assert close.reopen_legacy_all(repo_root=tmp_path) == []
