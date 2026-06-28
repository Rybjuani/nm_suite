from __future__ import annotations

from tests.e2e._helpers.qt_helpers import set_input_text
from tests.e2e.pages.base_page import BasePage


class AvisosPage(BasePage):
    def open(self):
        from app.modules.avisos_qt import ModuloAvisos

        self.window = ModuloAvisos(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def filter_active(self):
        self.window._on_filter_changed("activos")
        self.drain()
        return self

    def search(self, text: str):
        set_input_text(self.window._search_edit, text, self.qapp)
        return self
