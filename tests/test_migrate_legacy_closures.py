from __future__ import annotations

from pathlib import Path

from qa import migrate_legacy_closures as migrate


def test_migrate_marks_historical_closures_as_legacy(tmp_path):
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text("- [x] `suite:home@light` old\n- [ ] `suite:home@dark` open\n", encoding="utf-8")

    result = migrate.migrate_file(handoff)

    assert result.migrated_count == 1
    text = handoff.read_text(encoding="utf-8")
    assert "  - legacy: true" in text
    assert "  - legacy-reason: pre_replay_era" in text
    assert "  - legacy-migrated-by: migrate_legacy_closures.py" in text
    assert "- [ ] `suite:home@dark` open" in text


def test_migrate_is_idempotent(tmp_path):
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text("- [x] `suite:home@light` old\n", encoding="utf-8")

    first = migrate.migrate_file(handoff)
    after_first = handoff.read_text(encoding="utf-8")
    second = migrate.migrate_file(handoff)

    assert first.migrated_count == 1
    assert second.migrated_count == 0
    assert handoff.read_text(encoding="utf-8") == after_first


def test_migrate_does_not_touch_closures_that_already_have_evidence(tmp_path):
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    handoff.write_text(
        "- [x] `suite:home@light` closed\n"
        "  - evidence: " + "a" * 64 + "\n"
        "  - evidence-record: docs/closure_evidence/suite_home-light.json\n",
        encoding="utf-8",
    )

    result = migrate.migrate_file(handoff)

    assert result.migrated_count == 0
    assert "legacy: true" not in handoff.read_text(encoding="utf-8")


def test_migrate_dry_run_does_not_write(tmp_path):
    handoff = tmp_path / "VISUAL_REPAIR_HANDOFF.md"
    original = "- [x] `suite:home@light` old\n"
    handoff.write_text(original, encoding="utf-8")

    result = migrate.migrate_file(handoff, dry_run=True)

    assert result.migrated_count == 1
    assert handoff.read_text(encoding="utf-8") == original
