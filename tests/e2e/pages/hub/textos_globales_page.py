from __future__ import annotations

from tests.e2e._helpers.qt_helpers import set_input_text
from tests.e2e.pages.base_page import BasePage


class TextosGlobalesPage(BasePage):
    def open(self, sb):
        from hub.config_global_texts import TextosGlobalesSuiteView

        self.window = TextosGlobalesSuiteView(modo="light_hybrid", sb=sb)
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def edit(self, key: str, value: str):
        row = self.window._rows_by_key[key]
        set_input_text(row.editor, value, self.qapp)
        return self

    def save(self):
        self.window._save.click()
        self.drain()
        return self
