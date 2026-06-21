from __future__ import annotations


def test_animo_slider_score_is_serif_in_both_states(qtbot) -> None:
    """E3-S-BIENESTAR: slider score '— / 10' usa h-serif (Fraunces) igual que el mockup línea 704."""
    import shared.fonts as _fonts_mod
    from app.modules.animo_qt import ModuloAnimo

    module = ModuloAnimo(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    # import after widget construction so load_fonts() has run
    font_serif = _fonts_mod.FONT_SERIF

    # untouched state
    font_initial = module._slider_score.font()
    assert (
        font_serif.lower() in font_initial.family().lower()
        or font_initial.family().lower() in font_serif.lower()
    ), f"untouched: esperaba serif ({font_serif}), got {font_initial.family()!r}"

    # touched state
    module._v3_slider.set_level(7)
    font_touched = module._slider_score.font()
    assert (
        font_serif.lower() in font_touched.family().lower()
        or font_touched.family().lower() in font_serif.lower()
    ), f"touched: esperaba serif ({font_serif}), got {font_touched.family()!r}"


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
