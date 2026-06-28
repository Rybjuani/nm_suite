from __future__ import annotations

from tests.e2e.pages.base_page import BasePage


class DetallePacientePage(BasePage):
    def open(self, sb, pid: str = "patient-e2e", nombre: str = "Ana Paciente"):
        from hub.pacientes_qt import DetallePacienteView

        self.window = DetallePacienteView("light_hybrid", sb, pid, nombre)
        self.qtbot.addWidget(self.window)
        self.window.resize(960, 600)
        self.window.show()
        self.drain()
        return self

    def generar_resumen(self):
        self.window._btn_resumen_ia.click()
        self.drain(20)
        return self

    def expect_resumen_dialog(self):
        assert hasattr(self.window, "_resumen_dialog")
        assert self.window._resumen_dialog.isVisible()
        return self

    def expect_resumen_button_ready(self):
        assert self.window._btn_resumen_ia.isEnabled()
        assert self.window._btn_resumen_ia.text() == "Resumen IA"
        return self
