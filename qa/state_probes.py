#!/usr/bin/env python3
"""Lightweight registry for surfaces whose visual state is ambiguous."""

from __future__ import annotations

from typing import Any


# Family keys are theme-independent. Capture-time evaluators are added by the
# state-probe layer; policy only needs this declarative registry.
STATE_PROBES: dict[str, dict[str, str]] = {
    "suite:respiracion-paused": {"component": "respiracion", "expected_state": "paused"},
    "suite:respiracion-running": {"component": "respiracion", "expected_state": "running"},
    "suite:timer-paused": {"component": "timer", "expected_state": "paused"},
    "suite:timer-running": {"component": "timer", "expected_state": "running"},
}


def family_key(key: str) -> str:
    """Return ``app:view`` for an exact ``app:view@theme`` key."""

    return key.split("@", 1)[0]


def state_assertion_required(key: str) -> bool:
    return family_key(key) in STATE_PROBES


def state_probe_for(key: str) -> dict[str, Any] | None:
    probe = STATE_PROBES.get(family_key(key))
    return dict(probe) if probe is not None else None
