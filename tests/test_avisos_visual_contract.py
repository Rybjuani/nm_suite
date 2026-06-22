from __future__ import annotations


def _use_default_texts(monkeypatch) -> None:
    from app.modules import avisos_qt

    monkeypatch.setattr(
        avisos_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def test_avisos_row_badge_and_complete_button_match_mockup(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.avisos_qt import _ReminderCardV3

    row = {"id": 1, "hora": "09:00", "mensaje": "Tomar agua", "dias": "", "activo": 1}
    card = _ReminderCardV3(row, modo="light_hybrid")
    qtbot.addWidget(card)

    assert card._meta_lbl.text() == "Hidratación · 09:00"
    assert card._freq_lbl.text() == "Todos los días"
    assert card._status_lbl.text() == "Hoy"
    assert card._btn_done.text() == "Completar"
    assert card._btn_done.isVisibleTo(card) or not card._btn_done.isHidden()

    completed = {
        "id": 2,
        "hora": "21:00",
        "mensaje": "Respirar",
        "dias": "",
        "activo": 0,
        "done": True,
    }
    done_card = _ReminderCardV3(completed, modo="light_hybrid")
    qtbot.addWidget(done_card)

    assert done_card._status_lbl.text() == "Completado"
    assert done_card._btn_done.isHidden()
    assert done_card._btn_done.sizePolicy().retainSizeWhenHidden()


def test_avisos_filters_and_search_are_visible_and_drive_state(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules import avisos_qt
    from app.modules.avisos_qt import _AVISOS_FILTER_PILL_HEIGHT, _AVISOS_FILTER_PILL_RADIUS

    monkeypatch.setattr(avisos_qt, "visual_qa_enabled", lambda: True)
    monkeypatch.setattr(
        avisos_qt,
        "reminder_rows",
        lambda: [
            {"id": 1, "hora": "09:00", "mensaje": "Tomar agua", "dias": "", "activo": 1},
            {"id": 2, "hora": "22:00", "mensaje": "Dormir", "dias": "1,2,3,4,5", "activo": 0},
        ],
    )

    module = avisos_qt.ModuloAvisos(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert list(module._filter_pills.keys()) == ["todos", "activos", "hoy"]
    assert module._filter_pills["todos"].text() == "Todos"
    assert module._filter_pills["activos"].text() == "Activos"
    assert module._filter_pills["hoy"].text() == "Hoy"
    active_qss = module._filter_pills["todos"].styleSheet()
    assert module._filter_pills["todos"].height() == _AVISOS_FILTER_PILL_HEIGHT == 32
    assert "background: #fbf8f1" in active_qss.lower()
    assert "border: 1px solid rgba(46, 93, 67, 71)" in active_qss
    assert f"border-radius: {_AVISOS_FILTER_PILL_RADIUS}px" in active_qss
    assert "background: #2e5d43" not in active_qss.lower()
    assert module._search_input.text() == ""
    assert module._search_input._edit.placeholderText() == "Buscar recordatorio…"
    assert module._search_edit is module._search_input._edit

    module._search_input.set_text("agua")

    assert module._search_query == "agua"
