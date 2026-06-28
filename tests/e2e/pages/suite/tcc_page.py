from __future__ import annotations

from tests.e2e._helpers.qt_helpers import set_input_text
from tests.e2e.pages.base_page import BasePage


class TCCPage(BasePage):
    def open(self):
        from app.modules.registro_tcc_qt import ModuloRegistroTCC

        self.window = ModuloRegistroTCC(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def close(self):
        if self.window is not None and hasattr(self.window, "_distortions_timer"):
            self.window._distortions_timer.stop()
        super().close()

    def fill_situacion(self, text: str):
        set_input_text(self.window._txt_situacion, text, self.qapp)
        return self

    def next(self):
        self.window._btn_next.click()
        self.drain()
        return self

    def choose_emotion(self, label: str, custom: str | None = None):
        self.window._on_emotion_picked(label)
        if custom is not None:
            set_input_text(self.window._custom_emotion_input, custom, self.qapp)
        self.drain()
        return self

    def set_intensity(self, value: int):
        self.window._on_intensidad(value)
        self.drain()
        return self

    def fill_pensamiento(self, text: str):
        set_input_text(self.window._txt_pensamiento, text, self.qapp)
        return self

    def fill_respuesta(self, text: str):
        set_input_text(self.window._txt_respuesta, text, self.qapp)
        return self

    def expect_step(self, step: int):
        assert self.window._step == step
        return self

    def expect_next_enabled(self, enabled: bool = True):
        assert self.window._btn_next.isEnabled() is enabled
        return self
