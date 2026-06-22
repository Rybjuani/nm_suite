from __future__ import annotations


def _use_default_texts(monkeypatch) -> None:
    from app.modules import timer_qt

    monkeypatch.setattr(
        timer_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def _assigned_presets() -> list[tuple[str, int, str, str]]:
    return [
        ("Lectura", 25 * 60, "Leer con foco", "Foco"),
        ("Pausa activa", 5 * 60, "Mover el cuerpo", "Descanso"),
        ("Trabajo profundo", 45 * 60, "Concentración", "Foco"),
    ]


def test_timer_idle_chips_and_status_badge_match_mockup(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules import timer_qt
    from app.modules.timer_qt import ModuloTimer

    monkeypatch.setattr(timer_qt, "_load_presets", _assigned_presets)

    module = ModuloTimer(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._state_chip.text() == "Lista para empezar"
    assert "border-radius: 10px" in module._state_chip.styleSheet()
    assert module._input_container.isHidden()

    assert [btn.text() for btn, _secs in module._duration_chip_btns] == [
        "5 min",
        "25 min",
        "45 min",
    ]
    assert [btn.text() for btn, _secs in module._chip_btns] == [
        "Lectura",
        "Pausa activa",
        "Trabajo profundo",
    ]
    assert {btn.__class__.__name__ for btn, _secs in module._duration_chip_btns} == {"_TimerChip"}
    assert {btn.__class__.__name__ for btn, _secs in module._chip_btns} == {"_TimerChip"}

    duration_active = {btn.text(): btn.is_active() for btn, _secs in module._duration_chip_btns}
    mode_active = {btn.text(): btn.is_active() for btn, _secs in module._chip_btns}

    assert duration_active == {"5 min": False, "25 min": True, "45 min": False}
    assert mode_active == {"Lectura": True, "Pausa activa": False, "Trabajo profundo": False}


def test_timer_focus_arc_size_and_num_match_mockup(qtbot, monkeypatch) -> None:
    """Timer ring 180×180 — propuesta visual aprobada owner (V2-P1-040 resuelto).
    Ring reducido de 230px a 180px para que no domine el viewport."""
    _use_default_texts(monkeypatch)

    from app.modules import timer_qt
    from app.modules.timer_qt import ModuloTimer

    monkeypatch.setattr(timer_qt, "_load_presets", _assigned_presets)

    module = ModuloTimer(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._canvas.width() == 180
    assert module._canvas.height() == 180
    assert module._canvas._num_size_override == 40
    assert module._canvas._time_text == "25:00"


def test_timer_duration_mode_and_pause_state_stay_in_sync(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules import timer_qt
    from app.modules.timer_qt import ModuloTimer

    monkeypatch.setattr(timer_qt, "_load_presets", _assigned_presets)

    module = ModuloTimer(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    module._select_duration(5 * 60)

    assert module._ent_actividad.text() == "Pausa activa"
    assert module._current_categoria == "Descanso"
    assert {
        btn.text(): btn.is_active() for btn, _secs in module._duration_chip_btns
    } == {"5 min": True, "25 min": False, "45 min": False}
    assert {
        btn.text(): btn.is_active() for btn, _secs in module._chip_btns
    } == {"Lectura": False, "Pausa activa": True, "Trabajo profundo": False}

    module._start()
    assert module._state_chip.text() == "Sesión en curso"

    module._pause()
    assert module._state_chip.text() == "En pausa"
