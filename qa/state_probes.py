#!/usr/bin/env python3
"""Lightweight registry for surfaces whose visual state is ambiguous."""

from __future__ import annotations

from typing import Any

try:
    from qa.hash_utils import sha256_canonical_json
except ModuleNotFoundError:
    from hash_utils import sha256_canonical_json


# Family keys are theme-independent. Capture-time evaluators are added by the
# state-probe layer; policy only needs this declarative registry.
STATE_ASSERTION_SCHEMA = "nm_suite.state_assertion.v1"

STATE_PROBES: dict[str, dict[str, Any]] = {
    "suite:respiracion-paused": {
        "component": "respiracion",
        "expected_state": "paused",
        "expected": {
            "running": True,
            "paused": True,
            "toggle_text": "Reanudar",
            "ring_render_active": False,
        },
    },
    "suite:respiracion-running": {
        "component": "respiracion",
        "expected_state": "running",
        "expected": {
            "running": True,
            "paused": False,
            "toggle_text": "Pausar",
            "ring_render_active": True,
        },
    },
    "suite:timer-paused": {
        "component": "timer",
        "expected_state": "paused",
        "expected": {
            "running": True,
            "paused": True,
            "toggle_icon": "play",
            "ring_state": "pausado",
        },
    },
    "suite:timer-running": {
        "component": "timer",
        "expected_state": "running",
        "expected": {
            "running": True,
            "paused": False,
            "toggle_icon": "pause",
            "ring_state": "en curso",
        },
    },
}


def family_key(key: str) -> str:
    """Return ``app:view`` for an exact ``app:view@theme`` key."""

    return key.split("@", 1)[0]


def state_assertion_required(key: str) -> bool:
    return family_key(key) in STATE_PROBES


def state_probe_for(key: str) -> dict[str, Any] | None:
    probe = STATE_PROBES.get(family_key(key))
    if probe is None:
        return None
    return {
        **probe,
        "expected": dict(probe["expected"]),
    }


def _safe_call(value: object, method: str) -> Any:
    candidate = getattr(value, method, None)
    if not callable(candidate):
        return None
    try:
        return candidate()
    except Exception:
        return None


def _observe_timer(target: object) -> dict[str, Any]:
    button = getattr(target, "_btn_play", None)
    ring = getattr(target, "_canvas", None)
    return {
        "running": getattr(target, "_running", None),
        "paused": getattr(target, "_paused", None),
        "toggle_icon": _safe_call(button, "icon_name"),
        "ring_state": getattr(ring, "_state_text", None),
    }


def _observe_respiration(target: object) -> dict[str, Any]:
    button = getattr(target, "_btn_play", None)
    ring = getattr(target, "_circle", None)
    render_timer = getattr(ring, "_render_timer", None)
    return {
        "running": getattr(target, "_running", None),
        "paused": getattr(target, "_paused", None),
        "toggle_text": _safe_call(button, "accessibleName"),
        "ring_render_active": _safe_call(render_timer, "isActive"),
    }


def evaluate_state_probe(target: object, key: str) -> dict[str, Any] | None:
    """Evaluate one declarative probe against the settled live widget tree."""

    probe = state_probe_for(key)
    if probe is None:
        return None
    component = probe["component"]
    if component == "timer":
        observed = _observe_timer(target)
    elif component == "respiracion":
        observed = _observe_respiration(target)
    else:
        observed = {}
    expected = probe["expected"]
    checks = {name: observed.get(name) == value for name, value in expected.items()}
    return {
        "schema": STATE_ASSERTION_SCHEMA,
        "key": key,
        "probe_id": family_key(key),
        "component": component,
        "expected_state": probe["expected_state"],
        "expected": expected,
        "observed": observed,
        "checks": checks,
        "pass": bool(checks) and all(checks.values()),
    }


def state_assertion_sha256(assertion: object) -> str | None:
    if not isinstance(assertion, dict):
        return None
    return sha256_canonical_json(assertion)
