from __future__ import annotations


def test_animo_slider_card_matches_mockup_initial_and_touched_states(qtbot) -> None:
    from app.modules.animo_qt import ModuloAnimo

    module = ModuloAnimo(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._slider_score.text() == "— / 10"
    assert module._btn_reg.text() == "Guardar registro"
    assert not module._btn_reg.isEnabled()
    assert module._chart_range_days == 7

    module._v3_slider.set_level(6)

    assert module._slider_score.text() == "6 / 10"
    assert module._btn_reg.isEnabled()

    module._on_chart_range_changed("30 días")
    assert module._chart_range_days == 30


def test_animo_save_toast_copy_matches_mockup() -> None:
    import inspect
    from app.modules import animo_qt

    source = inspect.getsource(animo_qt.ModuloAnimo._registrar)
    assert "Registro guardado · {puntaje_wellbeing}/10" in source
    assert "Tu ánimo de hoy" not in source
