from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from tests.e2e.pages.base_page import BasePage


class DBTPage(BasePage):
    def open(self):
        from app.modules.dbt_qt import ModuloDBT

        self.window = ModuloDBT(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def open_library(self):
        self.window._tabs.set_current(1)
        self.drain()
        return self

    def start_first_skill(self):
        skill_cards = [
            child for child in self.window._library_container.findChildren(QWidget) if child.__class__.__name__ == "_SkillCard"
        ]
        if not skill_cards:
            self.window._filter_library()
            self.drain()
            skill_cards = [
                child for child in self.window._library_container.findChildren(QWidget) if child.__class__.__name__ == "_SkillCard"
            ]
        skill_cards[0].clicked.emit()
        self.drain()
        return self
