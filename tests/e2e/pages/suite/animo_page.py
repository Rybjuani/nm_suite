from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class AnimoPage(BasePage):
    def open(self):
        from app.modules.animo_qt import ModuloAnimo

        self.window = ModuloAnimo(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def set_level(self, level: int):
        self.window._v3_slider.set_level(level)
        self.drain()
        return self

    def save(self):
        self.window._btn_reg.click()
        self.drain()
        return self

    def expect_save_enabled(self, enabled: bool = True):
        assert self.window._btn_reg.isEnabled() is enabled
        return self
