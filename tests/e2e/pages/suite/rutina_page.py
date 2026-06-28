from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class RutinaPage(BasePage):
    def open(self):
        from app.modules.rutina_qt import ModuloRutina

        self.window = ModuloRutina(show_header=False, modo="light_hybrid")
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    def toggle_first(self):
        task_id, check = next(iter(self.window._task_checks.items()))
        check.setChecked(not check.isChecked())
        check.toggled.emit(check.isChecked())
        self.drain()
        return task_id

    def force_empty(self):
        self.window._task_checks.clear()
        self.window._task_done.clear()
        self.window._task_section.clear()
        self.window._hero_card.setVisible(False)
        self.window._set_empty_visible(True)
        self.drain()
        return self

    def add_task_if_available(self, section: str = "manana", text: str = "Tarea E2E"):
        if section not in self.window._section_cards:
            return False
        self.window._add_task(section, text, None)
        self.drain()
        return True
