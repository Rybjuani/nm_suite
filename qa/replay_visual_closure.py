#!/usr/bin/env python3
"""Replay auditor for visual closure evidence records."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qa import close_visual_key

CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)-\s*\[(?P<state>[xX ])\]\s*(?P<body>.*)$")
KEY_RE = close_visual_key.KEY_RE
OPEN_RE = re.compile(r"^\s*-\s*\[\s\]")
CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]")
NOTE_RE = re.compile(r"^\s*-\s*(?P<name>[A-Za-z0-9_-]+):\s*(?P<value>.*)$")
R0_KERNEL_PATHS = (
    "qa/capture_v8.py",
    "qa/layered_visual_compare.py",
    "qa/vas_gate.py",
    "qa/vas_engine.py",
    "qa/vas_introspect.py",
    "qa/anti_fraud_scan.py",
    "qa/close_visual_key.py",
    "qa/replay_visual_closure.py",
    "qa/spec_generator.py",
    "qa/specs/specs.json",
    ".github/workflows/visual-closure-replay.yml",
    "qa/_mockup_canonical/",
    "qa/pack canonico/",
)


@dataclass(frozen=True)
class HandoffItem:
    key: str
    state: str
    line_no: int
    line: str
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReplayFailure:
    key: str
    reason: str


@dataclass(frozen=True)
class ReplayResult:
    ok: bool
    base: str
    head: str
    replayed_keys: int
    skipped_legacy: int
    failed_keys: list[ReplayFailure]
    regenerated: bool = True


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _git_path(repo_root: Path, path: Path) -> str:
    path = path if path.is_absolute() else repo_root / path
    return _normalize_path(str(path.resolve().relative_to(repo_root.resolve())))


def git_rev_parse(repo_root: Path, revision: str) -> str:
    proc = _run_git(repo_root, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    if proc.returncode != 0:
        raise RuntimeError(f"invalid git revision: {revision}")
    return proc.stdout.strip()


def git_rev_list(repo_root: Path, base: str, head: str = "HEAD") -> set[str]:
    proc = _run_git(repo_root, ["rev-list", f"{base}..{head}"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git rev-list failed")
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def git_handoff_diff(repo_root: Path, base: str, handoff: Path) -> str:
    proc = _run_git(repo_root, ["diff", "--unified=0", base, "--", _git_path(repo_root, handoff)])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff handoff failed")
    return proc.stdout


def git_show_text(repo_root: Path, revision: str, path: Path) -> str:
    proc = _run_git(repo_root, ["show", f"{revision}:{_git_path(repo_root, path)}"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git show failed: {revision}:{path}")
    return proc.stdout


def git_changed_files(repo_root: Path, base: str, head: str = "HEAD") -> list[str]:
    # --no-renames: la detección de renames (default de git) pliega un move en
    # una sola ruta nueva y esconde la desaparición de la ruta vieja — el audit
    # necesita ver ambas (p.ej. record activo movido a revoked/ en un reopen).
    proc = _run_git(repo_root, ["diff", "--name-only", "--no-renames", f"{base}..{head}"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff --name-only failed")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _keys(line: str) -> list[str]:
    return [match.group(0) for match in KEY_RE.finditer(line)]


def parse_closed_checkbox_keys(diff_text: str) -> list[str]:
    removed_open: set[str] = set()
    closed: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("@@"):
            removed_open.clear()
            continue
        body = line[1:] if line[:1] in {"-", "+"} else line
        if line.startswith("-") and OPEN_RE.search(body):
            removed_open.update(_keys(body))
        elif line.startswith("+") and CHECKED_RE.search(body):
            added = set(_keys(body))
            if removed_open:
                closed.update(added & removed_open or added)
            else:
                closed.update(added)
    return sorted(closed)


def parse_handoff_items(text: str) -> list[HandoffItem]:
    items: list[HandoffItem] = []
    current_index: int | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = CHECKBOX_RE.match(line)
        if match:
            keys = _keys(line)
            if not keys:
                current_index = None
                continue
            state = "closed" if match.group("state").lower() == "x" else "open"
            items.append(HandoffItem(keys[0], state, line_no, line, []))
            current_index = len(items) - 1
            continue
        if current_index is None:
            continue
        if not line.strip():
            items[current_index].notes.append(line)
            continue
        if line.startswith(" ") or line.startswith("\t"):
            items[current_index].notes.append(line)
            continue
        current_index = None
    return items


def first_item(items: list[HandoffItem], key: str, state: str | None = None) -> HandoffItem | None:
    for item in items:
        if item.key != key:
            continue
        if state is not None and item.state != state:
            continue
        return item
    return None


def note_values(item: HandoffItem) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in item.notes:
        match = NOTE_RE.match(line)
        if match:
            values[match.group("name")] = match.group("value").strip()
    return values


def find_legacy_migrations(base_items: list[HandoffItem], head_items: list[HandoffItem]) -> list[str]:
    skipped: list[str] = []
    for item in head_items:
        if item.state != "closed":
            continue
        base_item = first_item(base_items, item.key, state="closed")
        if base_item is None:
            continue
        notes = note_values(item)
        if notes.get("legacy") == "true" and "evidence" not in notes:
            skipped.append(item.key)
    return sorted(set(skipped))


def find_unmigrated_closures(base_items: list[HandoffItem], head_items: list[HandoffItem]) -> list[str]:
    """Closed items carried over from base with neither evidence nor a legacy marker."""
    unmigrated: list[str] = []
    for item in head_items:
        if item.state != "closed":
            continue
        if first_item(base_items, item.key, state="closed") is None:
            continue
        notes = note_values(item)
        if "evidence" not in notes and notes.get("legacy") != "true":
            unmigrated.append(item.key)
    return sorted(set(unmigrated))


EVIDENCE_NOTE_NAMES = ("evidence", "evidence-record", "commit")


def evidence_changed_keys(base_items: list[HandoffItem], head_items: list[HandoffItem]) -> set[str]:
    """Closed keys whose notes were added or edited relative to base.

    Catches in-place tampering (or legacy re-closure) that never flips the
    checkbox in the diff, so it would escape parse_closed_checkbox_keys.

    Two detection modes:
    - Legacy items (``legacy: true``): full-notes-block comparison. Legacy
      closures were migrated pre-replay-era and carry freeform narrative
      notes (e.g. "CLOSURE INVALIDATED (...)", "Partial fidelity repair
      (...)") that don't fit the ``name: value`` shape ``NOTE_RE`` parses —
      restricting the check to ``EVIDENCE_NOTE_NAMES`` let edits to that
      narrative (or a fabricated evidence claim slipped into it) go
      undetected, since most legacy items never carry
      evidence/evidence-record/commit notes at all. Any line change under a
      legacy ``[x]`` entry now forces re-validation.
    - Non-legacy items: unchanged value-level comparison of
      ``EVIDENCE_NOTE_NAMES`` only, so real evidence-based closures (real
      ``docs/closure_evidence/*.json`` records) aren't over-flagged by
      unrelated note churn.
    """
    changed: set[str] = set()
    for item in head_items:
        if item.state != "closed":
            continue
        notes = note_values(item)
        base_item = first_item(base_items, item.key, state="closed")

        if notes.get("legacy") == "true":
            if base_item is None:
                # No closed key at this position in base: either a fresh
                # checkbox flip (parse_closed_checkbox_keys already covers
                # that from the diff) or an untracked new closure — not this
                # function's concern.
                continue
            base_notes = note_values(base_item)
            if base_notes.get("legacy") != "true":
                # The migration event itself (the retired one-shot
                # migrate_legacy_closures tool stamping `legacy: true` for the
                # first time): expected, whitelisted via find_legacy_migrations
                # + skip_legacy, not tampering.
                continue
            if item.notes != base_item.notes:
                changed.add(item.key)
            continue

        if not any(name in notes for name in EVIDENCE_NOTE_NAMES):
            continue
        if base_item is None:
            changed.add(item.key)
            continue
        base_notes = note_values(base_item)
        if any(notes.get(name) != base_notes.get(name) for name in EVIDENCE_NOTE_NAMES):
            changed.add(item.key)
    return changed


EVIDENCE_RECORD_PREFIX = "docs/closure_evidence/"
REVOKED_RECORD_PREFIX = EVIDENCE_RECORD_PREFIX + "revoked/"


def _key_from_record_filename(name: str) -> str:
    """Reverse of close_visual_key.key_safe: `<app>_<view>-<theme>.json` -> key."""
    stem = name[:-5] if name.endswith(".json") else name
    app, sep, rest = stem.partition("_")
    if not sep or app not in {"suite", "hub"}:
        return ""
    view, sep, theme = rest.rpartition("-")
    if not sep or theme not in {"light", "dark"} or not view:
        return ""
    return f"{app}:{view}@{theme}"


def keys_for_changed_records(
    head_items: list[HandoffItem],
    changed_files: list[str],
) -> tuple[set[str], list[str]]:
    """Map changed evidence-record files to their closed keys; report orphans.

    Sanctioned reopens (close_visual_key.py --reopen) are the ONE allowed
    shape for a record change without a closed item: the active record
    disappears, an identical file appears under revoked/, and the head
    handoff has the key OPEN with matching `reopened:`/`revoked-record:`
    notes. Anything else is an orphan (tampering)."""
    changed_records = sorted(
        {
            _normalize_path(path)
            for path in changed_files
            if _normalize_path(path).startswith(EVIDENCE_RECORD_PREFIX)
            and _normalize_path(path).endswith(".json")
        }
    )
    revoked_changed = {p for p in changed_records if p.startswith(REVOKED_RECORD_PREFIX)}
    active_changed = [p for p in changed_records if p not in revoked_changed]
    referenced: dict[str, str] = {}
    reopened_notes: dict[str, dict[str, str]] = {}
    for item in head_items:
        notes = note_values(item)
        if item.state == "closed":
            record = notes.get("evidence-record", "")
            if record:
                referenced[_normalize_path(record)] = item.key
        elif "reopened" in notes:
            reopened_notes[item.key] = notes
    keys: set[str] = set()
    orphans: list[str] = []
    sanctioned_revoked: set[str] = set()
    for path in active_changed:
        key = referenced.get(path)
        if key:
            keys.add(key)
            continue
        filename = path[len(EVIDENCE_RECORD_PREFIX):]
        derived = _key_from_record_filename(filename)
        revoked_path = REVOKED_RECORD_PREFIX + filename
        notes = reopened_notes.get(derived, {})
        if (
            derived
            and _normalize_path(notes.get("revoked-record", "")) == revoked_path
            and notes.get("revoked-evidence")
            and revoked_path in revoked_changed
        ):
            sanctioned_revoked.add(revoked_path)
            continue
        orphans.append(path)
    for path in sorted(revoked_changed):
        if path in sanctioned_revoked:
            continue
        # A revoked/ record may only appear as the counterpart of a
        # sanctioned reopen in the same range.
        filename = path[len(REVOKED_RECORD_PREFIX):]
        derived = _key_from_record_filename(filename)
        notes = reopened_notes.get(derived, {})
        if (
            derived
            and _normalize_path(notes.get("revoked-record", "")) == path
            and notes.get("revoked-evidence")
            and (EVIDENCE_RECORD_PREFIX + filename) in changed_records
        ):
            continue
        orphans.append(path)
    return keys, orphans


def kernel_paths_touched(paths: list[str]) -> list[str]:
    touched: list[str] = []
    for raw in paths:
        path = _normalize_path(raw)
        for marker in R0_KERNEL_PATHS:
            normalized = marker.rstrip("/")
            if marker.endswith("/"):
                if path.startswith(marker):
                    touched.append(raw)
                    break
            elif path == normalized:
                touched.append(raw)
                break
    return touched


def _record_path(repo_root: Path, value: str) -> Path | None:
    """Resolve an evidence-record note; only docs/closure_evidence/*.json is authority."""
    if not value or Path(value).is_absolute():
        return None
    resolved = (repo_root / value).resolve()
    evidence_root = (repo_root / "docs" / "closure_evidence").resolve()
    if resolved.parent != evidence_root or resolved.suffix != ".json":
        return None
    return resolved


def _record_hash(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != close_visual_key.EVIDENCE_SCHEMA:
        raise ValueError(f"unexpected evidence schema: {payload.get('schema')!r}")
    return close_visual_key.canonical_record_sha256(payload)


def regenerate_record_at_commit(repo_root: Path, key: str, commit: str) -> close_visual_key.EvidenceBuild:
    with close_visual_key.temporary_worktree(repo_root, commit) as worktree:
        return close_visual_key.regenerate_record_for_key(
            repo_root=worktree,
            key=key,
            commit_head=commit,
        )


def _validate_one_closure(
    *,
    repo_root: Path,
    item: HandoffItem,
    audited_commits: set[str],
    regenerate: bool = True,
) -> ReplayFailure | None:
    notes = note_values(item)
    evidence = notes.get("evidence", "")
    record_value = notes.get("evidence-record", "")
    commit_value = notes.get("commit", "")
    if not evidence:
        return ReplayFailure(item.key, "missing_evidence")
    if not commit_value:
        return ReplayFailure(item.key, "missing_commit")
    if not record_value:
        return ReplayFailure(item.key, "missing_evidence_record")

    try:
        commit = git_rev_parse(repo_root, commit_value)
    except RuntimeError:
        return ReplayFailure(item.key, "commit_outside_range")
    if commit not in audited_commits:
        return ReplayFailure(item.key, "commit_outside_range")

    record_path = _record_path(repo_root, record_value)
    if record_path is None:
        return ReplayFailure(item.key, "invalid_evidence_record_path")
    if not record_path.exists():
        return ReplayFailure(item.key, "missing_evidence_record")
    try:
        stored_hash = _record_hash(record_path)
    except Exception:
        return ReplayFailure(item.key, "invalid_evidence_record")
    if stored_hash != evidence:
        return ReplayFailure(item.key, "evidence_hash_mismatch")

    if not regenerate:
        return None
    try:
        regenerated = regenerate_record_at_commit(repo_root, item.key, commit)
    except Exception as exc:
        return ReplayFailure(item.key, f"replay_regeneration_failed:{type(exc).__name__}")
    if regenerated.record_sha256 != evidence:
        return ReplayFailure(item.key, "evidence_hash_mismatch")
    return None


def replay(
    *,
    base: str,
    handoff: Path,
    skip_legacy: bool,
    repo_root: Path = ROOT,
    regenerate: bool = True,
) -> ReplayResult:
    repo_root = repo_root.resolve()
    handoff = handoff if handoff.is_absolute() else repo_root / handoff
    base_commit = git_rev_parse(repo_root, base)
    head = git_rev_parse(repo_root, "HEAD")
    audited_commits = git_rev_list(repo_root, base_commit, "HEAD")
    diff_text = git_handoff_diff(repo_root, base_commit, handoff)
    closed_keys = parse_closed_checkbox_keys(diff_text)
    base_text = git_show_text(repo_root, base_commit, handoff)
    head_text = handoff.read_text(encoding="utf-8")
    base_items = parse_handoff_items(base_text)
    head_items = parse_handoff_items(head_text)
    changed_files = git_changed_files(repo_root, base_commit, "HEAD")

    failures: list[ReplayFailure] = []

    legacy_keys = find_legacy_migrations(base_items, head_items)
    if skip_legacy:
        skipped_legacy = len(legacy_keys)
    else:
        skipped_legacy = 0
        failures.extend(
            ReplayFailure(key, "legacy_closure_without_evidence") for key in legacy_keys
        )

    failures.extend(
        ReplayFailure(key, "unmigrated_closure")
        for key in find_unmigrated_closures(base_items, head_items)
    )

    validate_keys = set(closed_keys)
    validate_keys |= evidence_changed_keys(base_items, head_items)
    record_keys, orphan_records = keys_for_changed_records(head_items, changed_files)
    validate_keys |= record_keys
    failures.extend(
        ReplayFailure(path, "orphan_evidence_record") for path in orphan_records
    )

    if validate_keys:
        touched = kernel_paths_touched(changed_files)
        if touched:
            failures.extend(
                ReplayFailure(key, "kernel_changed_with_visual_closure")
                for key in sorted(validate_keys)
            )
            return ReplayResult(
                False, base_commit, head, 0, skipped_legacy, failures, regenerate
            )

    replayed = 0
    for key in sorted(validate_keys):
        item = first_item(head_items, key, state="closed")
        if item is None:
            failures.append(ReplayFailure(key, "missing_closed_handoff_item"))
            continue
        failure = _validate_one_closure(
            repo_root=repo_root,
            item=item,
            audited_commits=audited_commits,
            regenerate=regenerate,
        )
        if failure is not None:
            failures.append(failure)
            continue
        replayed += 1

    return ReplayResult(
        ok=not failures,
        base=base_commit,
        head=head,
        replayed_keys=replayed,
        skipped_legacy=skipped_legacy,
        failed_keys=failures,
        regenerated=regenerate,
    )


def print_result(result: ReplayResult) -> None:
    print("REPLAY " + ("PASS" if result.ok else "FAIL"))
    print(f"base: {result.base}")
    print(f"head: {result.head}")
    print(f"regeneration: {'full' if result.regenerated else 'structural'}")
    print(f"replayed_keys: {result.replayed_keys}")
    print(f"skipped_legacy: {result.skipped_legacy}")
    print("failed_keys:")
    for failure in result.failed_keys:
        print(f"  - {failure.key}: {failure.reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay visual closure evidence records.")
    parser.add_argument("--base", required=True, help="Base commit for audited range.")
    parser.add_argument("--handoff", type=Path, default=Path(close_visual_key.HANDOFF))
    parser.add_argument("--skip-legacy", action="store_true")
    parser.add_argument(
        "--no-regen",
        action="store_true",
        help=(
            "Structural mode: validate notes, ranges, R0 and record hashes without "
            "re-running capture/compare. Pixel regeneration is platform-bound to the "
            "closing machine (Windows); CI uses this mode."
        ),
    )
    args = parser.parse_args(argv)

    try:
        result = replay(
            base=args.base,
            handoff=args.handoff,
            skip_legacy=args.skip_legacy,
            regenerate=not args.no_regen,
        )
    except RuntimeError as exc:
        head = "UNKNOWN"
        try:
            head = git_rev_parse(ROOT, "HEAD")
        except RuntimeError:
            pass
        result = ReplayResult(
            ok=False,
            base=args.base,
            head=head,
            replayed_keys=0,
            skipped_legacy=0,
            failed_keys=[ReplayFailure("<preflight>", str(exc))],
            regenerated=not args.no_regen,
        )
    print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
