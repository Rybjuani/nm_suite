from __future__ import annotations


class FakeIAResponder:
    def __init__(self):
        self.resumen_queue: list[str] = []
        self.asignacion_queue: list[str] = []
        self.actividad_queue: list[str] = []
        self._fail_resumen: str | None = None
        self._fail_asignacion: str | None = None
        self._fail_actividad: str | None = None
        self.calls_resumen: list[dict] = []
        self.calls_asignacion: list[dict] = []
        self.calls_actividad: list[dict] = []

    def queue_resumen(self, text: str):
        self.resumen_queue.append(text)
        return self

    def queue_asignacion(self, text: str):
        self.asignacion_queue.append(text)
        return self

    def queue_actividad(self, text: str):
        self.actividad_queue.append(text)
        return self

    def fail_next_resumen(self, message: str = "IA no disponible"):
        self._fail_resumen = message
        return self

    def fail_next_asignacion(self, message: str = "IA no disponible"):
        self._fail_asignacion = message
        return self

    def fail_next_actividad(self, message: str = "IA no disponible"):
        self._fail_actividad = message
        return self

    def generar_resumen_paciente(self, datos, nombre, on_result, on_error, patient_id=None):
        self.calls_resumen.append({"datos": datos, "nombre": nombre, "patient_id": patient_id})
        if self._fail_resumen:
            message, self._fail_resumen = self._fail_resumen, None
            on_error(message)
            return
        on_result(self.resumen_queue.pop(0) if self.resumen_queue else "Resumen IA fake")

    def generar_asignacion(self, modulo, datos, nombre, on_result, on_error, patient_id=None):
        self.calls_asignacion.append(
            {"modulo": modulo, "datos": datos, "nombre": nombre, "patient_id": patient_id}
        )
        if self._fail_asignacion:
            message, self._fail_asignacion = self._fail_asignacion, None
            on_error(message)
            return
        default = {
            "timer": "Nombre: Lectura\nMinutos: 25\nCategoria: Foco",
            "avisos": "Hora: 09:30\nMensaje: Tomar agua",
            "rutina": "Tarea: Respiracion breve\nSeccion: manana",
        }.get(modulo, "Asignacion IA fake")
        on_result(self.asignacion_queue.pop(0) if self.asignacion_queue else default)

    def autocompletar_actividad(self, nombre_parcial, on_result, on_error, patient_id=None):
        self.calls_actividad.append({"nombre_parcial": nombre_parcial, "patient_id": patient_id})
        if self._fail_actividad:
            message, self._fail_actividad = self._fail_actividad, None
            on_error(message)
            return
        on_result(
            self.actividad_queue.pop(0)
            if self.actividad_queue
            else "Nombre: Caminata corta\nDescripcion: 15 min afuera\nCategoria: Fisica\nAnimo min: 1\nAnimo max: 10"
        )


def patch_ia(monkeypatch, responder: FakeIAResponder):
    import hub.ia_asistente as ia_asistente

    monkeypatch.setattr(ia_asistente, "generar_resumen_paciente", responder.generar_resumen_paciente)
    monkeypatch.setattr(ia_asistente, "generar_asignacion", responder.generar_asignacion)
    monkeypatch.setattr(ia_asistente, "autocompletar_actividad", responder.autocompletar_actividad)
    return responder
