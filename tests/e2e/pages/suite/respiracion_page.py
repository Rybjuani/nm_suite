from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class RespiracionPage(BasePage):
    def open(self):
        from app.modules.respiracion_qt import ModuloRespiracion

        self.window = ModuloRespiracion(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def select_preset(self, minutes: int):
        self.window._select_preset(minutes)
        self.drain()
        return self

    def play(self):
        self.window._btn_play.click()
        self.drain()
        return self

    def stop(self):
        self.window._btn_stop.click()
        self.drain()
        return self

    def expect_duration(self, minutes: int):
        assert self.window._duration_min == minutes
        return self
