from __future__ import annotations

from unittest import mock

from PyQt6.QtGui import QPainter as _RealQPainter
from PyQt6.QtWidgets import QWidget

from shared.components.rings import NMModuleRing


class _FakePainter:
    RenderHint = _RealQPainter.RenderHint
    instance: "_FakePainter | None" = None

    def __init__(self, *args, **kwargs):
        self.draw_texts = []
        self.draw_ellipses = []
        self.draw_arcs = []
        _FakePainter.instance = self

    def setRenderHint(self, *args, **kwargs):
        pass

    def save(self):
        pass

    def restore(self):
        pass

    def end(self):
        pass

    def setPen(self, *args, **kwargs):
        pass

    def setBrush(self, *args, **kwargs):
        pass

    def setFont(self, *args, **kwargs):
        pass

    def drawEllipse(self, *args, **kwargs):
        self.draw_ellipses.append((args, kwargs))

    def drawArc(self, *args, **kwargs):
        self.draw_arcs.append((args, kwargs))

    def drawText(self, *args, **kwargs):
        self.draw_texts.append((args, kwargs))


def _paint_module_ring(qtbot, pct):
    _FakePainter.instance = None
    ring = NMModuleRing(size=56, pct=pct)
    qtbot.addWidget(ring)

    with mock.patch("shared.components.rings.QPainter", _FakePainter):
        ring.paintEvent(None)

    assert _FakePainter.instance is not None
    return ring, _FakePainter.instance


def _painted_labels(painter: _FakePainter) -> list[str]:
    return [args[2] for args, _kwargs in painter.draw_texts]


def test_module_ring_stores_unknown_pct(qtbot):
    ring = NMModuleRing(size=56, pct=None)
    qtbot.addWidget(ring)

    assert ring._pct is None


def test_module_ring_set_pct_can_restore_unknown(qtbot):
    ring = NMModuleRing(size=56, pct=0.4)
    qtbot.addWidget(ring)

    ring.set_pct(None)

    assert ring._pct is None


def test_module_ring_clamps_negative_pct(qtbot):
    ring = NMModuleRing(size=56, pct=-0.25)
    qtbot.addWidget(ring)

    assert ring._pct == 0.0


def test_module_ring_clamps_above_one_pct(qtbot):
    ring = NMModuleRing(size=56, pct=1.25)
    qtbot.addWidget(ring)

    assert ring._pct == 1.0


def test_module_ring_paint_unknown_draws_dash_label(qtbot):
    _ring, painter = _paint_module_ring(qtbot, None)

    assert _painted_labels(painter) == ["—"]


def test_module_ring_paint_unknown_skips_progress_arc(qtbot):
    _ring, painter = _paint_module_ring(qtbot, None)

    assert painter.draw_arcs == []


def test_module_ring_paint_numeric_draws_percent_and_arc(qtbot):
    _ring, painter = _paint_module_ring(qtbot, 0.75)

    assert _painted_labels(painter) == ["75%"]
    assert len(painter.draw_arcs) == 1
    assert painter.draw_arcs[0][0][2] == int(-270.0 * 16)


def test_patient_row_premium_passes_unknown_pct_to_ring(qtbot):
    from shared.components import patient as patient_components
    from shared.components.patient import NMPatientRowPremium

    class _FakeRing(QWidget):
        instances = []

        def __init__(
            self, size=56, pct=0.0, modo=None, show_label=True, color_key="primary", parent=None
        ):
            super().__init__(parent)
            self.size_arg = size
            self.pct_arg = pct
            self.modo_arg = modo
            self.show_label_arg = show_label
            self.color_key_arg = color_key
            self.setFixedSize(size, size)
            _FakeRing.instances.append(self)

    with mock.patch.object(patient_components, "NMModuleRing", _FakeRing):
        row = NMPatientRowPremium("Paciente Prueba", patient_id="p-1", pct=None)
        qtbot.addWidget(row)

    assert _FakeRing.instances[-1].pct_arg is None


def test_pacientes_view_uses_real_adherence_only(qtbot, monkeypatch):
    import hub.main_qt as main_qt

    class _FakeSignal:
        def __init__(self):
            self.connected = []

        def connect(self, slot):
            self.connected.append(slot)

    class _FakeRow(QWidget):
        instances = []

        def __init__(self, name, **kwargs):
            super().__init__(kwargs.get("parent"))
            self.name_arg = name
            self.kwargs = kwargs
            self.clicked = _FakeSignal()
            _FakeRow.instances.append(self)

    monkeypatch.setattr(main_qt, "visual_qa_enabled", lambda: False)
    monkeypatch.setattr(main_qt, "NMPatientRowPremium", _FakeRow)

    view = main_qt.PacientesView(
        modo="dark_hybrid",
        pacientes=[
            {"patient_id": "p-1", "patient_name": "Sin Métrica", "email": "sin@example.com"},
            {
                "patient_id": "p-2",
                "patient_name": "Con Métrica",
                "email": "con@example.com",
                "adherence": "0.42",
            },
        ],
        on_select=lambda *_args: None,
        on_refresh=lambda: None,
    )
    qtbot.addWidget(view)

    assert [row.kwargs["pct"] for row in _FakeRow.instances] == [None, 0.42]
    assert _FakeRow.instances[0].kwargs["last_activity"] == "Sin registros"
    assert _FakeRow.instances[0].kwargs["next_session"] == ""
    assert _FakeRow.instances[0].kwargs["mood_data"] is None
