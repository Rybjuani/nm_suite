from __future__ import annotations


def _use_mockup_defaults(monkeypatch) -> None:
    from app.modules import registro_tcc_qt

    monkeypatch.setattr(
        registro_tcc_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )
    monkeypatch.setattr(
        registro_tcc_qt,
        "_load_tcc_template_config",
        lambda: registro_tcc_qt.DEFAULT_TCC_TEMPLATE,
    )


def test_registro_tcc_stepper_otro_and_final_cta_match_mockup(qtbot, monkeypatch) -> None:
    _use_mockup_defaults(monkeypatch)

    from app.modules.registro_tcc_qt import ModuloRegistroTCC

    module = ModuloRegistroTCC(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert [step["title"] for step in module._step_defs] == [
        "Situación",
        "Emoción",
        "Pensamiento",
        "Respuesta",
    ]
    assert module._btn_prev.text() == "Anterior"
    assert module._btn_next.text() == "Siguiente"
    assert module._custom_emotion_input.text() == ""
    assert module._custom_emotion_input.placeholderText() == "Nombrá tu emoción…"

    module._step = 3
    module._show_step()

    assert module._btn_next.text() == "Guardar registro"


def test_registro_tcc_distortion_and_tip_tones_match_mockup(qtbot, monkeypatch) -> None:
    _use_mockup_defaults(monkeypatch)

    from app.modules.registro_tcc_qt import ModuloRegistroTCC

    module = ModuloRegistroTCC(show_header=False, modo="dark_hybrid")
    qtbot.addWidget(module)

    assert module._tip_card._icon._color_key == "gold"

    module._txt_pensamiento.setPlainText("Siempre fallo y todo va a salir mal.")
    module._detect_distortions(None)

    chips = [
        item.widget()
        for item_index in range(module._distortion_layout.count())
        if (item := module._distortion_layout.itemAt(item_index)) is not None
    ]
    chips = [chip for chip in chips if chip is not None]

    assert chips
    assert all("border: none" in chip.styleSheet() for chip in chips)
    assert all("border-radius: 999px" in chip.styleSheet() for chip in chips)


def test_registro_tcc_visual_source_uses_mockup_rose_and_gold() -> None:
    import inspect
    from app.modules import registro_tcc_qt

    distortions_source = inspect.getsource(registro_tcc_qt.ModuloRegistroTCC._detect_distortions)
    tip_paint_source = inspect.getsource(registro_tcc_qt._TipCard.paintEvent)

    assert 'v3c("rose", self._modo)' in distortions_source
    assert "goldSoft" in tip_paint_source
