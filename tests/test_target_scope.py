from __future__ import annotations

import pytest

from qa import target_scope as ts


def _handoff(*sections: str) -> str:
    """Build a synthetic handoff with a `## Checklist` + `### section` items."""
    return "## Checklist\n\n" + "\n".join(sections) + "\n"


SECTION_A = """### Family A (2)

- [x] `suite:closed-a@light` - severity=high; changed=0.5
- [ ] `suite:open-a1@light` - severity=high; changed=0.30
- [ ] `suite:open-a2@light` - severity=medium; changed=0.15
- [ ] `suite:open-a3@light` - severity=medium; changed=0.05
"""

SECTION_B = """### Family B (2)

- [ ] `hub:open-b1@dark` - severity=high; changed=0.40
- [ ] `hub:open-b2@dark` - severity=medium; changed=0.08
"""

HANDOFF_TEXT = _handoff(SECTION_A, SECTION_B)


# ─── parse_open_keys ────────────────────────────────────────────────────────


def test_parse_open_keys_skips_closed_and_assigns_section_and_tier():
    open_keys = ts.parse_open_keys(HANDOFF_TEXT)
    keys = [ok.key for ok in open_keys]
    assert "suite:closed-a@light" not in keys
    assert keys == [
        "suite:open-a1@light",
        "suite:open-a2@light",
        "suite:open-a3@light",
        "hub:open-b1@dark",
        "hub:open-b2@dark",
    ]
    by_key = {ok.key: ok for ok in open_keys}
    assert by_key["suite:open-a1@light"].tier == "HIGH"
    assert by_key["suite:open-a1@light"].section == "Family A (2)"
    assert by_key["suite:open-a2@light"].tier == "MED"
    assert by_key["suite:open-a3@light"].tier == "LOW"
    assert by_key["hub:open-b1@dark"].section == "Family B (2)"


def test_parse_open_keys_deduplicates_first_occurrence_across_sections():
    text = _handoff(
        "### First\n\n- [ ] `suite:duplicate@light`\n",
        "### Second\n\n- [ ] `suite:duplicate@light`\n- [ ] `suite:unique@dark`\n",
    )

    open_keys = ts.parse_open_keys(text)

    assert [item.key for item in open_keys] == [
        "suite:duplicate@light",
        "suite:unique@dark",
    ]
    assert open_keys[0].section == "First"


def test_parse_open_keys_does_not_reopen_a_duplicate_closed_or_blocked_key():
    text = _handoff(
        "### Authority\n\n"
        "- [x] `suite:closed@light`\n"
        "- [~] `suite:blocked@dark`\n"
        "- [ ] `suite:closed@light`\n"
        "- [ ] `suite:blocked@dark`\n"
    )

    assert ts.parse_open_keys(text) == []


# ─── next-key ───────────────────────────────────────────────────────────────


def test_next_key_resolves_first_open_key_in_document_order():
    assert ts.resolve_target_scope("next-key", HANDOFF_TEXT) == ["suite:open-a1@light"]


def test_next_key_raises_when_no_open_keys():
    text = _handoff("### All closed (1)\n\n- [x] `suite:done@light` - severity=high; changed=0.1\n")
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("next-key", text)


# ─── first-n ────────────────────────────────────────────────────────────────


def test_first_n_resolves_exactly_n_keys_in_handoff_order():
    result = ts.resolve_target_scope("first-n", HANDOFF_TEXT, n=3)
    assert result == ["suite:open-a1@light", "suite:open-a2@light", "suite:open-a3@light"]


def test_first_n_clamped_by_available_open_keys_not_padded():
    result = ts.resolve_target_scope("first-n", HANDOFF_TEXT, n=100)
    assert len(result) == 5  # total open keys across both sections
    assert result[-1] == "hub:open-b2@dark"


def test_first_n_rejects_invalid_count():
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("first-n", HANDOFF_TEXT, n=0)


# ─── batch (same selection as first-n, different execution semantics) ──────


def test_batch_selects_same_keys_as_first_n():
    assert ts.resolve_target_scope("batch", HANDOFF_TEXT, n=4) == ts.resolve_target_scope(
        "first-n", HANDOFF_TEXT, n=4
    )


def test_batch_does_not_enable_false_pass():
    """Batch selection is purely a key list; resolving a batch target set
    must not itself claim any PASS/closure outcome -- it returns keys only."""
    result = ts.resolve_target_scope("batch", HANDOFF_TEXT, n=2)
    assert result == ["suite:open-a1@light", "suite:open-a2@light"]
    assert all(isinstance(k, str) for k in result)


# ─── family ─────────────────────────────────────────────────────────────────


def test_family_resolves_keys_sharing_next_key_section_by_default():
    result = ts.resolve_target_scope("family", HANDOFF_TEXT)
    assert result == ["suite:open-a1@light", "suite:open-a2@light", "suite:open-a3@light"]


def test_family_resolves_relative_to_explicit_seed_key():
    result = ts.resolve_target_scope("family", HANDOFF_TEXT, seed_key="hub:open-b1@dark")
    assert result == ["hub:open-b1@dark", "hub:open-b2@dark"]


def test_family_excludes_non_familiar_keys():
    result = ts.resolve_target_scope("family", HANDOFF_TEXT, seed_key="hub:open-b1@dark")
    assert "suite:open-a1@light" not in result
    assert "suite:open-a2@light" not in result


def test_family_raises_for_seed_key_not_open():
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("family", HANDOFF_TEXT, seed_key="suite:closed-a@light")
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("family", HANDOFF_TEXT, seed_key="suite:does-not-exist@light")


# ─── all-open-keys ──────────────────────────────────────────────────────────


def test_all_open_keys_resolves_every_open_key_in_document_order():
    result = ts.resolve_target_scope("all-open-keys", HANDOFF_TEXT)
    assert result == [
        "suite:open-a1@light",
        "suite:open-a2@light",
        "suite:open-a3@light",
        "hub:open-b1@dark",
        "hub:open-b2@dark",
    ]


# ─── explicit-list ──────────────────────────────────────────────────────────


def test_explicit_list_respects_exact_requested_order():
    result = ts.resolve_target_scope(
        "explicit-list",
        HANDOFF_TEXT,
        explicit_keys=["hub:open-b2@dark", "suite:open-a1@light"],
    )
    assert result == ["hub:open-b2@dark", "suite:open-a1@light"]


def test_explicit_list_dedupes_while_preserving_first_occurrence_order():
    result = ts.resolve_target_scope(
        "explicit-list",
        HANDOFF_TEXT,
        explicit_keys=["suite:open-a1@light", "hub:open-b1@dark", "suite:open-a1@light"],
    )
    assert result == ["suite:open-a1@light", "hub:open-b1@dark"]


def test_explicit_list_rejects_closed_or_unknown_keys():
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("explicit-list", HANDOFF_TEXT, explicit_keys=["suite:closed-a@light"])
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("explicit-list", HANDOFF_TEXT, explicit_keys=["suite:nope@light"])


def test_explicit_list_rejects_empty_list():
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("explicit-list", HANDOFF_TEXT, explicit_keys=[])


# ─── unknown mode / plan formatting ─────────────────────────────────────────


def test_unknown_mode_raises():
    with pytest.raises(ts.TargetScopeError):
        ts.resolve_target_scope("some-other-mode", HANDOFF_TEXT)


def test_to_plan_rows_formats_app_view_theme_key():
    rows = ts.to_plan_rows(["suite:dbt-library@light", "hub:pacientes@dark"])
    assert rows == [
        "suite,dbt-library,light,suite:dbt-library@light",
        "hub,pacientes,dark,hub:pacientes@dark",
    ]


def test_parse_key_rejects_malformed_key():
    with pytest.raises(ts.TargetScopeError):
        ts.parse_key("not-a-valid-key")


# ─── real handoff smoke test ────────────────────────────────────────────────


def test_resolves_against_the_real_handoff_without_error():
    """Every mode must resolve cleanly against the live repo handoff, so a
    trigger phrase never dead-ends on an unhandled exception."""
    text = ts.HANDOFF.read_text(encoding="utf-8")
    next_key = ts.resolve_target_scope("next-key", text)
    assert len(next_key) == 1
    assert ts.resolve_target_scope("first-n", text, n=5) == ts.resolve_target_scope(
        "first-n", text, n=5
    )
    family = ts.resolve_target_scope("family", text)
    assert next_key[0] in family
    all_open = ts.resolve_target_scope("all-open-keys", text)
    assert next_key[0] in all_open
    assert set(family) <= set(all_open)
    explicit = ts.resolve_target_scope("explicit-list", text, explicit_keys=[next_key[0]])
    assert explicit == next_key
