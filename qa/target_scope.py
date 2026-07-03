#!/usr/bin/env python3
"""Owner-directed visual QA target scope resolution.

Pure, dependency-free functions over ``VISUAL_REPAIR_HANDOFF.md`` text: given
an OWNER_TARGET_MODE declaration (see ``WORKER_VISUAL_QA_FLOW.md``), resolve
it to a concrete, ordered list of open visual keys. No git/network/subprocess
side effects here — this module never writes, never closes a key, never
reads or renders any canonical artifact. It is a read-only scope resolver,
so it carries no closure authority and is intentionally NOT part of R0.

Modes:
    next-key        -> [first open key]
    first-n         -> first N open keys, handoff document order
    batch           -> same selection as first-n; "batch" differs only in
                        execution/commit granularity, which is a caller
                        concern (see WORKER_VISUAL_QA_FLOW.md "Current Item
                        Definition"), not a scope-resolution concern
    family          -> open keys sharing the seed key's "###" section
                        (default seed: NEXT_KEY / first open key)
    all-open-keys   -> every open key, document order
    explicit-list   -> exactly the requested keys, de-duplicated,
                        every key must already be open (else TargetScopeError)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "VISUAL_REPAIR_HANDOFF.md"

CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)-\s*\[(?P<state>[xX ])\]\s*(?P<body>.*)$")
SECTION_RE = re.compile(r"^###\s+(.*)$")
KEY_RE = re.compile(r"(?P<app>suite|hub):(?P<view>[^@\s`\"'\)\]]+)@(?P<theme>light|dark)")
SEV_RE = re.compile(r"severity=(\w+)")
CHG_RE = re.compile(r"changed=([\d.]+)")

# Matches LayeredThresholds.text_dense_max_changed_pixel_ratio in
# qa/layered_visual_compare.py: keys already at/under the dense-surface gate
# threshold are the closest to PASS (LOW complexity to close).
LOW_TIER_MAX_CHANGED = 0.10

TARGET_MODES = (
    "next-key",
    "first-n",
    "batch",
    "family",
    "all-open-keys",
    "explicit-list",
)


class TargetScopeError(Exception):
    pass


@dataclass(frozen=True)
class OpenKey:
    key: str
    section: str | None
    tier: str  # "HIGH" | "MED" | "LOW"
    changed_pixel_ratio: float | None
    line_no: int


@dataclass(frozen=True)
class ParsedKey:
    key: str
    app: str
    view: str
    theme: str


def parse_key(key: str) -> ParsedKey:
    match = KEY_RE.fullmatch(key.strip())
    if not match:
        raise TargetScopeError(f"invalid_key: {key}")
    return ParsedKey(
        key=key.strip(),
        app=match.group("app"),
        view=match.group("view"),
        theme=match.group("theme"),
    )


def _tier_of(body: str) -> str:
    sev = SEV_RE.search(body)
    chg = CHG_RE.search(body)
    sev_val = sev.group(1) if sev else ""
    chg_val = float(chg.group(1)) if chg else None
    if sev_val == "high":
        return "HIGH"
    if chg_val is not None and chg_val <= LOW_TIER_MAX_CHANGED:
        return "LOW"
    return "MED"


def parse_open_keys(handoff_text: str) -> list[OpenKey]:
    """All ``- [ ]`` keys in document order, with family (### section) and
    complexity tier. Only scans checkbox lines with a resolvable key; a
    checkbox line with no key (malformed) is skipped, not raised."""
    result: list[OpenKey] = []
    current_section: str | None = None
    for line_no, line in enumerate(handoff_text.splitlines(), start=1):
        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            continue
        match = CHECKBOX_RE.match(line)
        if not match or match.group("state") != " ":
            continue
        key_match = KEY_RE.search(line)
        if not key_match:
            continue
        chg = CHG_RE.search(line)
        result.append(
            OpenKey(
                key=key_match.group(0),
                section=current_section,
                tier=_tier_of(line),
                changed_pixel_ratio=float(chg.group(1)) if chg else None,
                line_no=line_no,
            )
        )
    return result


def resolve_next_key(handoff_text: str) -> list[str]:
    open_keys = parse_open_keys(handoff_text)
    if not open_keys:
        raise TargetScopeError("no_open_keys")
    return [open_keys[0].key]


def resolve_first_n(handoff_text: str, n: int) -> list[str]:
    if n < 1:
        raise TargetScopeError("invalid_count")
    open_keys = parse_open_keys(handoff_text)
    if not open_keys:
        raise TargetScopeError("no_open_keys")
    return [ok.key for ok in open_keys[:n]]


def resolve_batch(handoff_text: str, n: int) -> list[str]:
    """Selection is identical to first-n; batch vs first-n differs only in
    how the caller groups commits/execution, not in which keys are chosen."""
    return resolve_first_n(handoff_text, n)


def resolve_family(handoff_text: str, seed_key: str | None = None) -> list[str]:
    open_keys = parse_open_keys(handoff_text)
    if not open_keys:
        raise TargetScopeError("no_open_keys")
    if seed_key is None:
        seed = open_keys[0]
    else:
        seed = next((ok for ok in open_keys if ok.key == seed_key), None)
        if seed is None:
            raise TargetScopeError(f"seed_key_not_open: {seed_key}")
    return [ok.key for ok in open_keys if ok.section == seed.section]


def resolve_all_open(handoff_text: str) -> list[str]:
    return [ok.key for ok in parse_open_keys(handoff_text)]


def resolve_explicit_list(handoff_text: str, requested: list[str]) -> list[str]:
    if not requested:
        raise TargetScopeError("empty_explicit_list")
    open_keys = {ok.key for ok in parse_open_keys(handoff_text)}
    missing = [k for k in requested if k not in open_keys]
    if missing:
        raise TargetScopeError(f"keys_not_open_or_unknown: {missing}")
    seen: set[str] = set()
    result: list[str] = []
    for k in requested:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def resolve_target_scope(
    mode: str,
    handoff_text: str,
    *,
    n: int | None = None,
    seed_key: str | None = None,
    explicit_keys: list[str] | None = None,
) -> list[str]:
    """Single entry point: resolve any OWNER_TARGET_MODE to an ordered key list."""
    if mode == "next-key":
        return resolve_next_key(handoff_text)
    if mode == "first-n":
        if n is None:
            raise TargetScopeError("first-n requires n")
        return resolve_first_n(handoff_text, n)
    if mode == "batch":
        if n is None:
            raise TargetScopeError("batch requires n")
        return resolve_batch(handoff_text, n)
    if mode == "family":
        return resolve_family(handoff_text, seed_key)
    if mode == "all-open-keys":
        return resolve_all_open(handoff_text)
    if mode == "explicit-list":
        if not explicit_keys:
            raise TargetScopeError("explicit-list requires explicit_keys")
        return resolve_explicit_list(handoff_text, explicit_keys)
    raise TargetScopeError(f"unknown_target_mode: {mode} (expected one of {TARGET_MODES})")


def to_plan_rows(keys: list[str]) -> list[str]:
    """Format resolved keys as `app,view,theme,key` rows for
    `qa/run_visual_family.ps1 -PlanFile`."""
    rows = []
    for key in keys:
        parsed = parse_key(key)
        rows.append(f"{parsed.app},{parsed.view},{parsed.theme},{parsed.key}")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve an OWNER_TARGET_MODE to a concrete ordered key list."
    )
    parser.add_argument("--mode", required=True, choices=TARGET_MODES)
    parser.add_argument("--n", type=int, default=None, help="Required for first-n/batch.")
    parser.add_argument("--seed-key", default=None, help="Optional seed for family (default: NEXT_KEY).")
    parser.add_argument(
        "--keys", default=None, help="Comma-separated keys, required for explicit-list."
    )
    parser.add_argument(
        "--handoff", type=Path, default=HANDOFF, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--plan", action="store_true", help="Print `app,view,theme,key` rows instead of bare keys."
    )
    args = parser.parse_args(argv)

    explicit_keys = [k.strip() for k in args.keys.split(",")] if args.keys else None

    try:
        handoff_text = args.handoff.read_text(encoding="utf-8")
        keys = resolve_target_scope(
            args.mode,
            handoff_text,
            n=args.n,
            seed_key=args.seed_key,
            explicit_keys=explicit_keys,
        )
    except TargetScopeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.plan:
        for row in to_plan_rows(keys):
            print(row)
    else:
        for key in keys:
            print(key)
    print(f"# target_set_size={len(keys)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
