#!/usr/bin/env python3
"""Render the human visual-repair view from canonical authority sources."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    from qa.surface_scope import ROOT, manifest_keys
except ModuleNotFoundError:
    from surface_scope import ROOT, manifest_keys


HANDOFF = Path("VISUAL_REPAIR_HANDOFF.md")
ACTIVE_DIR = Path("docs") / "closure_evidence" / "active"
EVIDENCE_SCHEMA = "nm_suite.evidence_record.v2"
_BLOCKED_RE = re.compile(
    r"^\s*-\s*\[~\]\s*`(?P<key>(?:suite|hub):[^`]+@(?:light|dark))`(?P<suffix>.*)$"
)


class HandoffRenderError(ValueError):
    pass


def load_active_records(repo_root: Path = ROOT) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    active_dir = repo_root / ACTIVE_DIR
    if not active_dir.exists():
        return records
    for path in sorted(active_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HandoffRenderError(f"invalid active record {path.name}: {exc}") from exc
        if not isinstance(record, dict):
            raise HandoffRenderError(f"invalid active record root: {path.name}")
        key = record.get("key")
        if record.get("schema") != EVIDENCE_SCHEMA or not isinstance(key, str):
            raise HandoffRenderError(f"invalid active record schema: {path.name}")
        if key in records:
            raise HandoffRenderError(f"duplicate active record: {key}")
        records[key] = record
    return records


def _legacy_blocked_notes(repo_root: Path) -> dict[str, str]:
    path = repo_root / HANDOFF
    if not path.exists():
        return {}
    notes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _BLOCKED_RE.match(line)
        if match:
            notes[match.group("key")] = match.group("suffix").strip()
    return notes


def _group(key: str) -> str:
    app, rest = key.split(":", 1)
    view = rest.split("@", 1)[0]
    if app == "hub":
        return "Hub"
    if view.startswith(("onboarding", "recuperar-acceso")):
        return "Onboarding y acceso"
    if view.startswith("registro"):
        return "Registro TCC"
    if view.startswith("dbt"):
        return "DBT"
    if view.startswith(("home", "animo")):
        return "Home y ánimo"
    if view.startswith("respiracion"):
        return "Respiración"
    if view.startswith("timer"):
        return "Timer"
    return "Rutina, actividades y avisos"


_GROUP_ORDER = (
    "Onboarding y acceso",
    "Registro TCC",
    "DBT",
    "Home y ánimo",
    "Respiración",
    "Timer",
    "Rutina, actividades y avisos",
    "Hub",
)


def render_handoff(
    repo_root: Path = ROOT,
    *,
    active_records: Mapping[str, Mapping[str, Any]] | None = None,
    blocked_notes: Mapping[str, str] | None = None,
) -> str:
    """Return the deterministic handoff view; never mutate the repository."""

    universe = manifest_keys(repo_root)
    universe_set = set(universe)
    records = dict(active_records) if active_records is not None else load_active_records(repo_root)
    notes = dict(blocked_notes) if blocked_notes is not None else _legacy_blocked_notes(repo_root)
    unknown_records = sorted(set(records) - universe_set)
    unknown_notes = sorted(set(notes) - universe_set)
    conflicts = sorted(set(records) & set(notes))
    if unknown_records:
        raise HandoffRenderError(f"active records outside manifest: {unknown_records}")
    if unknown_notes:
        raise HandoffRenderError(f"blocked notes outside manifest: {unknown_notes}")
    if conflicts:
        raise HandoffRenderError(f"active and blocked conflict: {conflicts}")

    closed = len(records)
    blocked = len(notes)
    opened = len(universe) - closed - blocked
    lines = [
        "# Visual Repair Handoff",
        "",
        "> AUTORIDAD GENERADA: no editar este archivo. El estado cerrado proviene",
        "> exclusivamente de `docs/closure_evidence/active/`; el universo proviene",
        "> de `qa/_mockup_canonical/MANIFEST.json`.",
        "",
        f"Estado: {closed} cerradas · {opened} abiertas · {blocked} bloqueadas · {len(universe)} total.",
        "",
        "## Superficies",
        "",
    ]
    by_group: dict[str, list[str]] = {group: [] for group in _GROUP_ORDER}
    for key in universe:
        by_group[_group(key)].append(key)
    for group in _GROUP_ORDER:
        keys = by_group[group]
        if not keys:
            continue
        lines.extend((f"### {group} ({len(keys)})", ""))
        for key in keys:
            if key in records:
                state, suffix = "x", ""
            elif key in notes:
                state = "~"
                suffix = f" {notes[key]}" if notes[key] else ""
            else:
                state, suffix = " ", ""
            lines.append(f"- [{state}] `{key}`{suffix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_handoff(repo_root: Path = ROOT, *, text: str | None = None) -> Path:
    path = repo_root / HANDOFF
    rendered = render_handoff(repo_root) if text is None else text
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(rendered, encoding="utf-8", newline="\n")
    tmp.replace(path)
    return path
