from __future__ import annotations

from PyQt6.QtWidgets import QTextEdit

from tests.e2e._helpers.qt_helpers import set_input_text
from tests.e2e.pages.base_page import BasePage


class PlanTerapeuticoPage(BasePage):
    def open(self, sb, pid: str = "patient-e2e", nombre: str = "Ana Paciente"):
        from hub.plan_terapeutico import PlanTerapeuticoTab

        self.window = PlanTerapeuticoTab("light_hybrid", sb, pid, nombre)
        self.qtbot.addWidget(self.window)
        self.window.resize(960, 600)
        self.window.show()
        self.drain()
        return self

    @property
    def recordatorios_tab(self):
        return self.window._tabs.widget(0)

    @property
    def timer_tab(self):
        return self.window._tabs.widget(1)

    @property
    def rutina_tab(self):
        return self.window._tabs.widget(2)

    @property
    def activacion_tab(self):
        return self.window._tabs.widget(3)

    def add_timer(self, name: str = "Lectura", minutes: str = "25", category: str = "Foco"):
        tab = self.timer_tab
        set_input_text(tab._ent_name, name, self.qapp)
        set_input_text(tab._ent_secs, minutes, self.qapp)
        set_input_text(tab._ent_cat, category, self.qapp)
        tab._save_btn.click()
        self.drain()
        return self

    def add_recordatorio(self, hora: str = "09:30", mensaje: str = "Tomar agua"):
        tab = self.recordatorios_tab
        set_input_text(tab._ent_hora, hora, self.qapp)
        set_input_text(tab._ent_msg, mensaje, self.qapp)
        tab._save_btn.click()
        self.drain()
        return self

    def add_rutina(self, tarea: str = "Respirar 3 minutos"):
        tab = self.rutina_tab
        set_input_text(tab._ent_task, tarea, self.qapp)
        tab._save_btn.click()
        self.drain()
        return self

    def add_activacion(self, name: str = "Caminata", desc: str = "15 min afuera"):
        tab = self.activacion_tab
        set_input_text(tab._ent_name, name, self.qapp)
        set_input_text(tab._ent_desc, desc, self.qapp)
        tab._save_btn.click()
        self.drain()
        return self

    def timer_ia(self):
        self.timer_tab._ia_btn.click()
        self.drain(20)
        return self
