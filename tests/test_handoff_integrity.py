from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from qa.render_handoff import (
    HANDOFF,
    HandoffRenderError,
    load_active_records,
    load_surface_notes,
    render_handoff,
)
from qa.surface_scope import ROOT, manifest_keys


ROW_RE = re.compile(
    r"^- \[(?P<state>[x ~])\] `(?P<key>(?:suite|hub):[^`]+@(?:light|dark))`"
)


def _rows(text: str) -> list[tuple[str, str]]:
    return [
        (match.group("state"), match.group("key"))
        for line in text.splitlines()
        if (match := ROW_RE.match(line))
    ]


def test_handoff_file_is_byte_exact_renderer_output():
    expected = render_handoff(ROOT).encode("utf-8")

    assert (ROOT / HANDOFF).read_bytes() == expected


def test_handoff_universe_matches_manifest_once_with_expected_states():
    rendered = render_handoff(ROOT)
    rows = _rows(rendered)
    keys = [key for _state, key in rows]
    universe = set(manifest_keys(ROOT))
    closed = set(load_active_records(ROOT))
    blocked = set(load_surface_notes(ROOT))
    opened = universe - closed - blocked

    assert len(rows) == 116
    assert len(keys) == len(set(keys))
    assert set(keys) == universe
    assert not closed & blocked
    assert {key for state, key in rows if state == "x"} == closed
    assert {key for state, key in rows if state == "~"} == blocked
    assert {key for state, key in rows if state == " "} == opened
    assert (
        f"Estado: {len(closed)} cerradas · {len(opened)} abiertas · "
        f"{len(blocked)} bloqueadas · {len(universe)} total."
    ) in rendered


def test_surface_notes_fail_closed_when_missing_or_invalid(tmp_path: Path):
    with pytest.raises(HandoffRenderError, match="invalid surface notes"):
        load_surface_notes(tmp_path)

    notes = tmp_path / "qa" / "surface_notes.json"
    notes.parent.mkdir()
    notes.write_text('{"schema":"wrong","surfaces":{}}', encoding="utf-8")
    with pytest.raises(HandoffRenderError, match="schema"):
        load_surface_notes(tmp_path)


@pytest.mark.parametrize("separator", ["\r", "\u2028"])
def test_surface_notes_reject_line_separator_injection(tmp_path: Path, separator: str):
    notes = tmp_path / "qa" / "surface_notes.json"
    notes.parent.mkdir()
    payload = {
        "schema": "nm_suite.surface_notes.v1",
        "surfaces": {
            "suite:home@light": {
                "status": "blocked",
                "reason": "test",
                "note": f"annotation{separator}### injected section",
            }
        },
    }
    notes.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(HandoffRenderError, match="invalid surface note text"):
        load_surface_notes(tmp_path)
