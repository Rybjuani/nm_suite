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


def test_registro_tcc_response_cta_stays_inside_card_after_mouse_navigation(
    qtbot, monkeypatch
) -> None:
    _use_mockup_defaults(monkeypatch)
    monkeypatch.setenv("NM_VISUAL_QA", "1")
    monkeypatch.setenv("NM_TEST_FORCE_CLOSE", "1")

    from PyQt6.QtCore import QPoint, QRect, Qt
    from PyQt6.QtTest import QTest

    from app.main_qt import NeuroMoodApp

    window = NeuroMoodApp()
    qtbot.addWidget(window)
    window.resize(960, 600)
    window.show()
    window._apply_theme("dark_hybrid")
    window._open_module("registro")
    qtbot.wait(80)
    module = window._current_module

    module._txt_situacion.setPlainText("Discusión breve por tiempos de entrega.")
    QTest.mouseClick(module._btn_next, Qt.MouseButton.LeftButton)
    qtbot.wait(120)

    module._emotion_tiles[0].clicked.emit()
    QTest.mouseClick(module._btn_next, Qt.MouseButton.LeftButton)
    qtbot.wait(120)

    module._txt_pensamiento.setPlainText(
        "Nunca voy a poder resolver esto y todo va a salir mal."
    )
    QTest.mouseClick(module._btn_next, Qt.MouseButton.LeftButton)
    qtbot.wait(160)

    assert module._step == 3
    assert module._btn_next.text() == "Guardar registro"

    viewport = QRect(QPoint(0, 0), window.size())
    button_rect = QRect(module._btn_next.mapTo(window, QPoint(0, 0)), module._btn_next.size())
    effective_clip = QRect(viewport)
    parent = module._btn_next.parentWidget()
    while parent is not None:
        parent_rect = QRect(parent.mapTo(window, QPoint(0, 0)), parent.size())
        effective_clip = effective_clip.intersected(parent_rect)
        parent = parent.parentWidget()

    assert viewport.contains(button_rect.topLeft())
    assert viewport.contains(button_rect.bottomRight())
    assert viewport.contains(button_rect.center())
    assert effective_clip.contains(button_rect.topLeft())
    assert effective_clip.contains(button_rect.bottomRight())
    assert effective_clip.contains(button_rect.center())


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


def test_registro_tcc_stepper_widget_has_4_steps_and_titles_match(qtbot, monkeypatch) -> None:
    """E3-S-TCC: NMStepper cargado con 4 pasos y títulos del template (mockup línea 1210)."""
    _use_mockup_defaults(monkeypatch)

    from app.modules.registro_tcc_qt import ModuloRegistroTCC

    module = ModuloRegistroTCC(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert len(module._stepper._steps) == 4
    assert module._stepper._steps == ["Situación", "Emoción", "Pensamiento", "Respuesta"]
    assert module._stepper._current == 0


def test_registro_tcc_step_title_uses_serif_source() -> None:
    """E3-S-TCC: _make_title usa v3_font serif para los h-serif 17px del mockup (líneas 1222,1229,1241,1261)."""
    import inspect
    from app.modules import registro_tcc_qt

    source = inspect.getsource(registro_tcc_qt.ModuloRegistroTCC._make_title)
    assert "serif=True" in source
