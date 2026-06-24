from __future__ import annotations


def _use_default_texts(monkeypatch) -> None:
    from app.modules import rutina_qt

    monkeypatch.setattr(
        rutina_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def test_rutina_sections_and_rings_match_mockup(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules import rutina_qt
    from app.modules.rutina_qt import ModuloRutina

    monkeypatch.setattr(rutina_qt, "visual_qa_enabled", lambda: True)
    monkeypatch.setattr(
        rutina_qt,
        "routine_sections",
        lambda: {
            "manana": [{"id": 1, "descripcion": "Levantarse", "done": True}],
            "tarde": [{"id": 2, "descripcion": "Caminar", "done": False}],
            "noche": [{"id": 3, "descripcion": "Preparar descanso", "done": False}],
        },
    )

    module = ModuloRutina(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert [section[3] for section in rutina_qt.SECCIONES] == ["sun", "smile", "moon"]
    assert module._hero_card._ring.width() == 64
    assert module._hero_card._title_lbl.text() == "1 de 3 tareas completadas"

    for card in module._section_cards.values():
        assert card._ring.width() == 40

    assert module._section_cards["manana"]._icon_name == "sun"
    assert module._section_cards["tarde"]._icon_name == "smile"
    assert module._section_cards["noche"]._icon_name == "moon"


def test_rutina_add_done_and_empty_states_match_mockup(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules import rutina_qt
    from app.modules.rutina_qt import ModuloRutina

    monkeypatch.setattr(rutina_qt, "visual_qa_enabled", lambda: True)
    monkeypatch.setattr(
        rutina_qt,
        "routine_sections",
        lambda: {
            "manana": [{"id": 10, "descripcion": "Hidratarse", "done": True}],
            "tarde": [],
            "noche": [],
        },
    )

    module = ModuloRutina(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    check = module._task_checks[10]
    assert check.isChecked()
    assert "text-decoration: line-through" in check._label.styleSheet()

    saved: list[tuple[str, str]] = []
    module._section_cards["tarde"].show_add_inline(lambda key, text, _btn: saved.append((key, text)))

    add_form = module._section_cards["tarde"].body_layout().itemAt(0).widget()
    add_input = add_form.findChild(rutina_qt.NMInput)
    # Mockup l.929: <button class="btn btn--primary" id="rtAdd" style="padding:9px 14px;">+</button>
    # Migración desde UI anterior (glyph "✓" + variant "secondary"); el design system
    # adoptó "+" como glyph canónico de "add" y "btn--primary" (alias de "gradient"
    # en NMButton) para la CTA inline. El código `app/modules/rutina_qt.py:308` ya
    # rindió al spec; el test quedó pineado al valor histórico.
    add_buttons = [btn for btn in add_form.findChildren(rutina_qt.NMButton) if btn.text() == "+"]

    assert add_input.placeholderText() == "Nueva tarea…"
    assert add_buttons
    assert add_buttons[0].variant() == "gradient"
    assert add_buttons[0].width() == 36
    assert add_buttons[0].height() == 34

    monkeypatch.setattr(
        rutina_qt,
        "routine_sections",
        lambda: {"manana": [], "tarde": [], "noche": []},
    )
    module._load_tasks()

    assert not module._empty_state.isHidden()
    assert not module._empty_host.isHidden()
    assert module._hero_card.isHidden()
    assert all(card.isHidden() for card in module._section_cards.values())
