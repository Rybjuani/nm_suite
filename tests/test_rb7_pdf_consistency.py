from __future__ import annotations

from types import SimpleNamespace


def test_pdf_sections_use_fetch_patient_data_keys():
    from hub.exportar import _normalizar_secciones

    sections = _normalizar_secciones(None)

    assert {
        "animo",
        "respiracion",
        "tcc",
        "checklist",
        "actividades",
        "timer",
        "recordatorios",
        "avisos_disparados",
        "dbt",
    } <= sections
    assert not {"resp", "pens", "reclog"} & sections


def test_generar_pdf_renderiza_secciones_reales(tmp_path, monkeypatch):
    from hub.exportar import _generar
    from pypdf import PdfReader

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / "Downloads").mkdir()

    datos = {
        "animo": [
            {"fecha": "2026-06-19", "hora": "09:00", "puntaje": 7, "nota": "animo estable"}
        ],
        "respiracion": [
            {
                "fecha": "2026-06-19",
                "hora": "09:05",
                "tecnica": "4-7-8",
                "duracion_minutos": 5,
            }
        ],
        "tcc": [
            {
                "fecha": "2026-06-19",
                "emocion": "Ansiedad",
                "intensidad": 6,
                "pensamiento": "No voy a poder",
            }
        ],
        "checklist": [
            {
                "fecha": "2026-06-19",
                "origen": "manual",
                "categoria": "Logro",
                "descripcion": "Tomar agua",
            }
        ],
        "actividades": [
            {
                "fecha": "2026-06-19",
                "hora": "10:00",
                "animo": 7,
                "actividad": "Caminar diez minutos",
                "resultado": "hecha",
            }
        ],
        "timer": [
            {
                "fecha": "2026-06-19",
                "hora": "11:00",
                "nombre": "Pomodoro",
                "duracion_real": 1500,
            }
        ],
        "recordatorios": [
            {
                "hora": "12:00",
                "mensaje": "Tomar medicacion indicada",
                "dias": "1,2,3",
                "activa": True,
            }
        ],
        "avisos_disparados": [
            {
                "fecha": "2026-06-19",
                "hora": "12:00",
                "mensaje": "Tomar medicacion indicada",
                "cerrado": True,
            }
        ],
        "dbt": [
            {
                "fecha": "2026-06-19",
                "hora": "13:00",
                "skill_id": "stop",
                "familia": "distress_tolerance",
                "resultado": "ayudo",
                "malestar_antes": 8,
                "malestar_despues": 5,
                "nota": "uso STOP",
            }
        ],
    }

    path = _generar(
        "Paciente PDF",
        "patient-1",
        datos,
        nombre_archivo="rb7_pdf_test.pdf",
    )

    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    assert "Sesiones de respiración" in text
    assert "Registros de pensamientos" in text
    assert "Actividades conductuales" in text
    assert "Recordatorios asignados" in text
    assert "Avisos disparados" in text
    assert "Prácticas de habilidades DBT" in text
    assert "Caminar diez minutos" in text
    assert "Tomar medicacion indicada" in text


def test_detalle_paciente_view_tiene_boton_exportar_pdf(qapp, qtbot, monkeypatch):
    from PyQt6.QtWidgets import QWidget
    import hub.plan_terapeutico as plan_module
    from hub.pacientes_qt import DetallePacienteView

    class _FakePlan(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()

    monkeypatch.setattr(plan_module, "PlanTerapeuticoTab", _FakePlan)

    view = DetallePacienteView(
        "dark_hybrid",
        sb=None,
        paciente_id="patient-1",
        paciente_nombre="Paciente PDF",
    )
    qtbot.addWidget(view)

    assert view._btn_exportar_pdf.text() == "Exportar PDF"
    assert view._btn_resumen_ia.text() == "Resumen IA"


def test_on_exportar_pdf_llama_exportador_con_datos_del_paciente(qapp, qtbot, monkeypatch):
    from PyQt6.QtWidgets import QWidget
    import hub.plan_terapeutico as plan_module
    import hub.pacientes_qt as pacientes_qt
    import hub.exportar as exportar_module
    from hub.pacientes_qt import DetallePacienteView

    class _FakePlan(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()

    monkeypatch.setattr(plan_module, "PlanTerapeuticoTab", _FakePlan)
    monkeypatch.setattr(pacientes_qt.NMToast, "display", lambda *args, **kwargs: None)

    captured = {}

    def _fake_exportar_pdf(nombre, pid, datos, on_done=None, on_error=None, **kwargs):
        captured.update({"nombre": nombre, "pid": pid, "datos": datos, "kwargs": kwargs})
        if on_done:
            on_done("C:/tmp/test.pdf")

    monkeypatch.setattr(exportar_module, "exportar_pdf", _fake_exportar_pdf)

    view = DetallePacienteView(
        "dark_hybrid",
        sb=None,
        paciente_id="patient-1",
        paciente_nombre="Paciente PDF",
    )
    qtbot.addWidget(view)
    view._fetch_patient_data = lambda: {"actividades": [{"actividad": "Caminar"}]}

    view._on_exportar_pdf()

    assert captured == {
        "nombre": "Paciente PDF",
        "pid": "patient-1",
        "datos": {"actividades": [{"actividad": "Caminar"}]},
        "kwargs": {},
    }
    assert view._btn_exportar_pdf.isEnabled()
    assert view._btn_exportar_pdf.text() == "Exportar PDF"


class _SelectQuery:
    def __init__(self, parent, table: str):
        self._parent = parent
        self._table = table

    def select(self, columns: str):
        self._parent.select_columns[self._table] = columns
        return self

    def eq(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=[])

    def gte(self, *args, **kwargs):
        return self


class _SelectSB:
    def __init__(self):
        self.select_columns = {}

    def table(self, name: str):
        return _SelectQuery(self, name)


def test_fetch_patient_data_recordatorios_trae_campos_pdf(qapp):
    from hub.pacientes_qt import DetallePacienteView

    sb = _SelectSB()
    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = sb
    view._pid = "patient-1"
    view._nombre = "Paciente PDF"

    view._fetch_patient_data()

    columns = sb.select_columns["assigned_reminders"]
    assert "dias" in columns
    assert "completado_en" in columns
