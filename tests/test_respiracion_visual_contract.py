from __future__ import annotations


def _use_default_texts(monkeypatch) -> None:
    from app.modules import respiracion_qt

    monkeypatch.setattr(
        respiracion_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def _chip_text(chip) -> str:
    return chip._label.text()


def test_respiracion_matches_mockup_idle_contract(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.respiracion_qt import ModuloRespiracion

    module = ModuloRespiracion(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert [btn.text() for btn, _mins in module._pill_btns] == ["3 min", "5 min", "10 min"]
    assert [mins for _btn, mins in module._pill_btns] == [3, 5, 10]
    assert [btn.is_active() for btn, _mins in module._pill_btns] == [False, True, False]
    assert module._duration_min == 5

    module._select_preset(10)

    assert module._duration_min == 10
    assert [btn.is_active() for btn, _mins in module._pill_btns] == [False, False, True]

    assert _chip_text(module._chip_inhala) == "Inhalá 4s"
    assert _chip_text(module._chip_manten) == "Mantené 7s"
    assert _chip_text(module._chip_exhala) == "Exhalá 8s"

    assert module._pattern_eyebrow.text() == "Patrón"
    assert module._pattern_title.text() == "4·7·8"
    assert module._chrono_eyebrow.text() == "Crono"
    assert module._session_lbl.text() == "00:00"
    assert module._ciclos_eyebrow.text() == "Ciclos"
    assert module._ciclos_value_lbl.text() == "—"

    assert module._btn_reset.icon_name() == "refresh"
    assert module._btn_reset.width() == 46
    assert module._btn_reset.height() == 46
    assert module._btn_play.icon_name() == "play"
    assert module._btn_play.text() == ""
    assert module._btn_play.width() == 58
    assert module._btn_play.height() == 58
    assert module._btn_stop.icon_name() == "stop"
    assert module._btn_stop.width() == 46
    assert module._btn_stop.height() == 46


def test_respiracion_breath_circle_is_248px(qtbot, monkeypatch) -> None:
    """E3-S-BIENESTAR: orb de respiración fijado en 248×248 (canvas v3, bigring idle fix)."""
    _use_default_texts(monkeypatch)

    from app.modules.respiracion_qt import ModuloRespiracion

    module = ModuloRespiracion(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._circle.width() == 248
    assert module._circle.height() == 248


def test_respiracion_play_control_icons_follow_runtime_state(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.respiracion_qt import ModuloRespiracion

    module = ModuloRespiracion(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    module._start()
    try:
        assert module._btn_play.icon_name() == "pause"
        assert module._btn_play.toolTip() == "Pausar"
        assert module._btn_play.text() == ""

        module._pause()

        assert module._btn_play.icon_name() == "play"
        assert module._btn_play.toolTip() == "Reanudar"
        assert module._btn_play.text() == ""

        module._pause()

        assert module._btn_play.icon_name() == "pause"
        assert module._btn_play.toolTip() == "Pausar"
    finally:
        module._stop()

    assert module._btn_play.icon_name() == "play"
    assert module._btn_play.toolTip() == "Iniciar"
    assert module._btn_play.text() == ""
