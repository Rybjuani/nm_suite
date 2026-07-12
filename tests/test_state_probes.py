from __future__ import annotations

from qa.state_probes import (
    STATE_ASSERTION_SCHEMA,
    evaluate_state_probe,
    state_assertion_required,
    state_assertion_sha256,
)


class _Button:
    def __init__(self, *, icon: str = "", text: str = ""):
        self._icon = icon
        self._text = text

    def icon_name(self) -> str:
        return self._icon

    def accessibleName(self) -> str:
        return self._text


class _ActiveTimer:
    def __init__(self, active: bool):
        self._active = active

    def isActive(self) -> bool:
        return self._active


class _TimerRing:
    def __init__(self, state: str):
        self._state_text = state


class _BreathingRing:
    def __init__(self, active: bool):
        self._render_timer = _ActiveTimer(active)


class _TimerModule:
    def __init__(self, *, paused: bool):
        self._running = True
        self._paused = paused
        self._btn_play = _Button(icon="play" if paused else "pause")
        self._canvas = _TimerRing("pausado" if paused else "en curso")


class _BreathingModule:
    def __init__(self, *, paused: bool, ring_active: bool):
        self._running = True
        self._paused = paused
        self._btn_play = _Button(text="Reanudar" if paused else "Pausar")
        self._circle = _BreathingRing(ring_active)


def test_timer_running_and_paused_live_states_pass():
    running = evaluate_state_probe(_TimerModule(paused=False), "suite:timer-running@light")
    paused = evaluate_state_probe(_TimerModule(paused=True), "suite:timer-paused@dark")

    assert running["schema"] == STATE_ASSERTION_SCHEMA
    assert running["pass"] is True
    assert running["observed"]["toggle_icon"] == "pause"
    assert running["observed"]["ring_state"] == "en curso"
    assert paused["pass"] is True
    assert paused["observed"]["toggle_icon"] == "play"
    assert paused["observed"]["ring_state"] == "pausado"


def test_breathing_paused_probe_exposes_still_animated_ring_as_failure():
    assertion = evaluate_state_probe(
        _BreathingModule(paused=True, ring_active=True),
        "suite:respiracion-paused@light",
    )

    assert assertion["pass"] is False
    assert assertion["checks"]["ring_render_active"] is False
    assert assertion["observed"]["toggle_text"] == "Reanudar"


def test_breathing_running_probe_requires_active_ring():
    assertion = evaluate_state_probe(
        _BreathingModule(paused=False, ring_active=True),
        "suite:respiracion-running@dark",
    )

    assert assertion["pass"] is True
    assert assertion["observed"]["toggle_text"] == "Pausar"


def test_non_ambiguous_surface_has_no_state_assertion():
    assert evaluate_state_probe(object(), "suite:home@light") is None
    assert state_assertion_required("suite:home@light") is False


def test_state_assertion_hash_is_canonical_and_sensitive_to_observation():
    assertion = evaluate_state_probe(_TimerModule(paused=False), "suite:timer-running@light")
    same = {key: assertion[key] for key in reversed(assertion)}
    changed = {**assertion, "pass": False}

    assert state_assertion_sha256(assertion) == state_assertion_sha256(same)
    assert state_assertion_sha256(assertion) != state_assertion_sha256(changed)
