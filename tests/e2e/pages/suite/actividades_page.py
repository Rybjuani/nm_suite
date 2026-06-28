from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class ActividadesPage(BasePage):
    def open(self):
        from app.modules.actividades_qt import ModuloActividades

        self.window = ModuloActividades(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def filter_category(self, index: int):
        self.window._category_tabs.set_current(index)
        self.drain()
        return self

    def complete_first(self):
        card = self.window._suggested_cards[0]
        card.completed.emit(card._nombre)
        self.drain()
        return card._nombre
