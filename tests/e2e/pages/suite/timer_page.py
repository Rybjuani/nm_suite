from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class TimerPage(BasePage):
    def open(self):
        from app.modules.timer_qt import ModuloTimer

        self.window = ModuloTimer(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def play(self):
        self.window._btn_play.click()
        self.drain()
        return self

    def pause(self):
        self.window._btn_play.click()
        self.drain()
        return self

    def stop(self):
        self.window._btn_reset.click()
        self.drain()
        return self

    def force_empty(self):
        self.window._presets = []
        self.window._has_activity = False
        self.window._btn_play.setEnabled(False)
        self.window._btn_skip.setEnabled(False)
        self.window._empty_state.show()
        self.drain()
        return self
