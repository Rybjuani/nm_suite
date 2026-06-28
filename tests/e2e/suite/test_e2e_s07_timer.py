from __future__ import annotations

import pytest

from tests.e2e.pages.suite.timer_page import TimerPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


def test_timer_play_pause_stop(qapp, qtbot, request, visual_qa_env):
    page = TimerPage(qapp, qtbot, request=request).open()
    try:
        page.play()
        assert page.window._running is True
        assert page.window._paused is False

        page.pause()
        assert page.window._running is True
        assert page.window._paused is True

        page.stop()
        assert page.window._running is False
        assert page.window._paused is False
    finally:
        page.close()


def test_timer_empty_state(qapp, qtbot, request, visual_qa_env):
    page = TimerPage(qapp, qtbot, request=request).open()
    try:
        page.force_empty()
        assert page.window._empty_state.isVisible()
        assert not page.window._btn_play.isEnabled()
    finally:
        page.close()
