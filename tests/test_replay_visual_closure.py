from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa import close_visual_key as close
from qa import replay_visual_closure as replay


KEY = "suite:home@light"
BASE = "b" * 40
FIX = "a" * 40
HEAD = "c" * 40


def _record(key: str = KEY, commit: str = FIX) -> dict:
    return {
        "schema": close.EVIDENCE_SCHEMA,
        "key": key,
        "commit_head": commit,
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


def _write_record(root: Path, record: dict) -> tuple[Path, str]:
    rel = Path("docs/closure_evidence") / f"{close.key_safe(record['key'])}.json"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return rel, close.canonical_record_sha256(record)


def _patch_git(
    monkeypatch: pytest.MonkeyPatch,
    *,
    base_text: str,
    diff_text: str,
    audited: set[str] | None = None,
    changed_files: list[str] | None = None,
) -> None:
    def rev_parse(_root: Path, revision: str) -> str:
        if revision in {"base", BASE}:
            return BASE
        if revision in {"HEAD", HEAD}:
            return HEAD
        if revision in {"fix", FIX}:
            return FIX
        raise RuntimeError(f"invalid git revision: {revision}")

    monkeypatch.setattr(replay, "git_rev_parse", rev_parse)
    monkeypatch.setattr(
        replay,
        "git_rev_list",
        lambda _root, _base, _head="HEAD": {FIX} if audited is None else audited,
    )
    monkeypatch.setattr(replay, "git_handoff_diff", lambda _root, _base, _handoff: diff_text)
    monkeypatch.setattr(replay, "git_show_text", lambda _root, _revision, _path: base_text)
    monkeypatch.setattr(replay, "git_changed_files", lambda _root, _base, _head="HEAD": changed_files or [])


def _closure_diff(key: str = KEY) -> str:
    return f"""
@@ -1 +1,5 @@
- - [ ] `{key}` pending
+ - [x] `{key}` pending
+   - evidence: placeholder
+   - evidence-record: docs/closure_evidence/{close.key_safe(key)}.json
+   - commit: {FIX}
+   - closed-by: close_visual_key.py
"""


def _handoff_closed(key: str, evidence: str, record_path: Path, commit: str = FIX) -> str:
    return (
        f"- [x] `{key}` pending\n"
        f"  - evidence: {evidence}\n"
        f"  - evidence-record: {record_path.as_posix()}\n"
        f"  - commit: {commit}\n"
        "  - closed-by: close_visual_key.py\n"
    )


def test_replay_passes_when_evidence_matches(monkeypatch, tmp_path):
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, evidence, record_rel), encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=f"- [ ] `{KEY}` pending\n",
        diff_text=_closure_diff(),
        changed_files=["VISUAL_REPAIR_HANDOFF.md", record_rel.as_posix()],
    )
    monkeypatch.setattr(
        replay,
        "regenerate_record_at_commit",
        lambda _root, _key, _commit: close.EvidenceBuild(record, evidence, record_rel),
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is True
    assert result.replayed_keys == 1
    assert result.failed_keys == []


def test_replay_fails_with_evidence_hash_mismatch(monkeypatch, tmp_path):
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, evidence, record_rel), encoding="utf-8")
    _patch_git(monkeypatch, base_text=f"- [ ] `{KEY}` pending\n", diff_text=_closure_diff())
    monkeypatch.setattr(
        replay,
        "regenerate_record_at_commit",
        lambda _root, _key, _commit: close.EvidenceBuild(record, "0" * 64, record_rel),
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "evidence_hash_mismatch"


@pytest.mark.parametrize(
    ("notes", "reason"),
    [
        ("  - evidence-record: docs/closure_evidence/suite_home-light.json\n  - commit: " + FIX + "\n", "missing_evidence"),
        ("  - evidence: " + "d" * 64 + "\n  - evidence-record: docs/closure_evidence/suite_home-light.json\n", "missing_commit"),
    ],
)
def test_replay_fails_if_evidence_or_commit_is_missing(monkeypatch, tmp_path, notes, reason):
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(f"- [x] `{KEY}` pending\n{notes}", encoding="utf-8")
    _patch_git(monkeypatch, base_text=f"- [ ] `{KEY}` pending\n", diff_text=_closure_diff())

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == reason


def test_replay_fails_if_commit_is_outside_range(monkeypatch, tmp_path):
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, evidence, record_rel), encoding="utf-8")
    _patch_git(monkeypatch, base_text=f"- [ ] `{KEY}` pending\n", diff_text=_closure_diff(), audited=set())

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "commit_outside_range"


def test_replay_fails_with_kernel_changed_when_new_closure_in_same_range(monkeypatch, tmp_path):
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, evidence, record_rel), encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=f"- [ ] `{KEY}` pending\n",
        diff_text=_closure_diff(),
        changed_files=["qa/capture_v8.py", "VISUAL_REPAIR_HANDOFF.md"],
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "kernel_changed_with_visual_closure"
    assert result.replayed_keys == 0


def test_replay_skips_legacy_with_skip_legacy(monkeypatch, tmp_path):
    base_text = f"- [x] `{KEY}` old closure\n"
    current = (
        f"- [x] `{KEY}` old closure\n"
        "  - legacy: true\n"
        "  - legacy-reason: pre_replay_era\n"
        "  - legacy-migrated-by: migrate_legacy_closures.py\n"
    )
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(current, encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=base_text,
        diff_text="""
@@ -1,0 +2,3 @@
+   - legacy: true
+   - legacy-reason: pre_replay_era
+   - legacy-migrated-by: migrate_legacy_closures.py
""",
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is True
    assert result.replayed_keys == 0
    assert result.skipped_legacy == 1


def test_manual_bypass_with_fake_record_fails(monkeypatch, tmp_path):
    fake_hash = "deadbeef" * 8
    fake_record = Path("docs/closure_evidence/fake.json")
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, fake_hash, fake_record), encoding="utf-8")
    _patch_git(monkeypatch, base_text=f"- [ ] `{KEY}` pending\n", diff_text=_closure_diff())

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason in {"missing_evidence_record", "evidence_hash_mismatch"}


def test_replay_without_skip_legacy_fails_legacy_closures(monkeypatch, tmp_path):
    base_text = f"- [x] `{KEY}` old closure\n"
    current = (
        f"- [x] `{KEY}` old closure\n"
        "  - legacy: true\n"
        "  - legacy-reason: pre_replay_era\n"
        "  - legacy-migrated-by: migrate_legacy_closures.py\n"
    )
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(current, encoding="utf-8")
    _patch_git(monkeypatch, base_text=base_text, diff_text="")

    result = replay.replay(base="base", handoff=handoff, skip_legacy=False, repo_root=tmp_path)

    assert result.ok is False
    assert result.skipped_legacy == 0
    assert result.failed_keys[0].reason == "legacy_closure_without_evidence"


def test_replay_fails_closed_item_with_neither_evidence_nor_legacy_marker(monkeypatch, tmp_path):
    base_text = f"- [x] `{KEY}` old closure\n"
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(base_text, encoding="utf-8")
    _patch_git(monkeypatch, base_text=base_text, diff_text="")

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "unmigrated_closure"


def test_replay_validates_evidence_tampered_without_checkbox_transition(monkeypatch, tmp_path):
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    base_text = _handoff_closed(KEY, evidence, record_rel)
    tampered = _handoff_closed(KEY, "0" * 64, record_rel)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(tampered, encoding="utf-8")
    # Diff shows only the edited note line: no `[ ] -> [x]` transition.
    _patch_git(
        monkeypatch,
        base_text=base_text,
        diff_text=f"""
@@ -2 +2 @@
-   - evidence: {evidence}
+   - evidence: {'0' * 64}
""",
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "evidence_hash_mismatch"


def test_replay_rejects_record_path_outside_evidence_dir(monkeypatch, tmp_path):
    record = _record()
    record_rel = Path("reports/qa/evil.json")
    path = tmp_path / record_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    evidence = close.canonical_record_sha256(record)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, evidence, record_rel), encoding="utf-8")
    _patch_git(monkeypatch, base_text=f"- [ ] `{KEY}` pending\n", diff_text=_closure_diff())

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "invalid_evidence_record_path"


def test_replay_fails_on_orphan_changed_evidence_record(monkeypatch, tmp_path):
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(f"- [ ] `{KEY}` pending\n", encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=f"- [ ] `{KEY}` pending\n",
        diff_text="",
        changed_files=["docs/closure_evidence/suite_home-light.json"],
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys[0].reason == "orphan_evidence_record"


def test_replay_no_regen_validates_structurally_without_regeneration(monkeypatch, tmp_path):
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_handoff_closed(KEY, evidence, record_rel), encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=f"- [ ] `{KEY}` pending\n",
        diff_text=_closure_diff(),
        changed_files=["VISUAL_REPAIR_HANDOFF.md", record_rel.as_posix()],
    )

    def explode(_root, _key, _commit):
        raise AssertionError("regeneration must not run with regenerate=False")

    monkeypatch.setattr(replay, "regenerate_record_at_commit", explode)

    result = replay.replay(
        base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path, regenerate=False
    )

    assert result.ok is True
    assert result.replayed_keys == 1
    assert result.regenerated is False


# ─── evidence_changed_keys legacy-note hardening ────────────────────────────
#
# Legacy [x] closures carry freeform narrative notes ("CLOSURE INVALIDATED
# (...)", "Partial fidelity repair (...)") that never match the `name: value`
# shape NOTE_RE parses, and most never carry evidence/evidence-record/commit
# notes at all. The original evidence_changed_keys() only compared those 3
# canonical note values, so editing anything else under a legacy [x] entry
# (or a legacy item with no canonical notes at all) went undetected — no
# checkbox transition, no tracked note-value change, no failure.

_LEGACY_BASE = (
    f"- [x] `{KEY}` old closure\n"
    "  - legacy: true\n"
    "  - legacy-reason: pre_replay_era\n"
    "  - legacy-migrated-by: migrate_legacy_closures.py\n"
    "  - Closure evidence (2026-06-29): manual panel review confirms alignment.\n"
)


def test_replay_flags_legacy_note_edit_without_checkbox_transition(monkeypatch, tmp_path):
    """(1) Editing a legacy item's narrative note (not evidence/evidence-record/
    commit) with no checkbox transition must still force re-validation and fail,
    since legacy items have no real docs/closure_evidence/*.json record."""
    tampered = (
        f"- [x] `{KEY}` old closure\n"
        "  - legacy: true\n"
        "  - legacy-reason: pre_replay_era\n"
        "  - legacy-migrated-by: migrate_legacy_closures.py\n"
        "  - Closure evidence (2026-06-29): FABRICATED — actually never reviewed.\n"
    )
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(tampered, encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=_LEGACY_BASE,
        diff_text=(
            "@@ -5 +5 @@\n"
            "-  - Closure evidence (2026-06-29): manual panel review confirms alignment.\n"
            "+  - Closure evidence (2026-06-29): FABRICATED — actually never reviewed.\n"
        ),
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    assert result.failed_keys
    assert result.failed_keys[0].key == KEY
    assert result.failed_keys[0].reason == "missing_evidence"


def test_replay_legacy_unchanged_notes_still_skipped(monkeypatch, tmp_path):
    """(2) A legacy item whose notes are byte-for-byte unchanged relative to
    base must still be skipped (not forced into re-validation)."""
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(_LEGACY_BASE, encoding="utf-8")
    _patch_git(monkeypatch, base_text=_LEGACY_BASE, diff_text="")

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is True
    assert result.replayed_keys == 0
    assert result.skipped_legacy == 1
    assert result.failed_keys == []


def test_replay_unrelated_handoff_edit_does_not_flag_untouched_legacy_key(monkeypatch, tmp_path):
    """(3) Editing handoff content outside a legacy item's own note block (an
    unrelated open item's text) must not cause that legacy key to be flagged."""
    other_key = "suite:animo@light"
    base_text = _LEGACY_BASE + f"- [ ] `{other_key}` needs polish\n"
    head_text = _LEGACY_BASE + f"- [ ] `{other_key}` needs a different polish pass\n"
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(head_text, encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=base_text,
        diff_text=(
            "@@ -6 +6 @@\n"
            f"- - [ ] `{other_key}` needs polish\n"
            f"+ - [ ] `{other_key}` needs a different polish pass\n"
        ),
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is True
    assert result.replayed_keys == 0
    assert result.skipped_legacy == 1
    assert result.failed_keys == []


def test_replay_new_canonical_record_unaffected_by_legacy_hardening(monkeypatch, tmp_path):
    """(4) A real, non-legacy evidence-based closure with an extra freeform
    note line (not evidence/evidence-record/commit) added must not be forced
    into re-validation by the legacy-notes hardening — canonical closures
    keep working exactly as before."""
    record = _record()
    record_rel, evidence = _write_record(tmp_path, record)
    base_text = _handoff_closed(KEY, evidence, record_rel)
    head_text = base_text + "  - reviewed-by: qa-team\n"
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(head_text, encoding="utf-8")
    _patch_git(
        monkeypatch,
        base_text=base_text,
        diff_text="@@ -4,0 +5 @@\n+  - reviewed-by: qa-team\n",
        changed_files=["VISUAL_REPAIR_HANDOFF.md"],
    )

    def explode(_root, _key, _commit):
        raise AssertionError("adding an unrelated note must not force re-validation")

    monkeypatch.setattr(replay, "regenerate_record_at_commit", explode)

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is True
    assert result.replayed_keys == 0
    assert result.failed_keys == []


# ─── owner-directed batch closure: evidence stays per-key ──────────────────


def test_replay_batch_closure_requires_evidence_per_key(monkeypatch, tmp_path):
    """A batch/all-open-keys commit may close several keys together, but
    each key still needs its own real docs/closure_evidence/*.json record.
    One well-evidenced key and one key whose checkbox flipped without a real
    record (e.g. hand-edited notes, no close_visual_key.py run) in the SAME
    commit/diff: replay must fail specifically for the unevidenced key while
    still validating the properly-evidenced one on its own merits."""
    key_ok = KEY
    key_bad = "suite:animo@light"

    record = _record(key=key_ok)
    record_rel_ok, evidence_ok = _write_record(tmp_path, record)

    fake_evidence = "0" * 64
    fake_record_rel = Path(f"docs/closure_evidence/{close.key_safe(key_bad)}.json")
    # Deliberately never written to disk: simulates a checkbox flip with
    # fabricated evidence notes but no real close_visual_key.py record.

    base_text = f"- [ ] `{key_ok}` pending\n- [ ] `{key_bad}` pending\n"
    head_text = _handoff_closed(key_ok, evidence_ok, record_rel_ok) + _handoff_closed(
        key_bad, fake_evidence, fake_record_rel
    )
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(head_text, encoding="utf-8")

    diff_text = _closure_diff(key_ok) + _closure_diff(key_bad)
    _patch_git(monkeypatch, base_text=base_text, diff_text=diff_text)
    monkeypatch.setattr(
        replay,
        "regenerate_record_at_commit",
        lambda _root, _key, _commit: close.EvidenceBuild(record, evidence_ok, record_rel_ok),
    )

    result = replay.replay(base="base", handoff=handoff, skip_legacy=True, repo_root=tmp_path)

    assert result.ok is False
    failures_by_key = {f.key: f.reason for f in result.failed_keys}
    assert failures_by_key.get(key_bad) == "missing_evidence_record"
    assert key_ok not in failures_by_key
    assert result.replayed_keys == 1
