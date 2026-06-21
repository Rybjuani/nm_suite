from __future__ import annotations


def test_home_hero_empty_state_matches_mockup_cta(qtbot) -> None:
    from app.home_qt import _HeroBienestar

    opened: list[str] = []
    hero = _HeroBienestar(
        "light_hybrid",
        lambda _mid: "",
        username="Alex",
        on_module_open=opened.append,
    )
    qtbot.addWidget(hero)

    assert hero._stack.currentIndex() == 0
    assert hero._msg.text() == "Aún no registraste tu ánimo hoy."
    assert hero._empty_cta.text() == "Registrar ánimo"

    hero._empty_cta.click()
    assert opened == ["animo"]


def test_home_hero_filled_state_matches_mockup_score_and_delta(qtbot, monkeypatch) -> None:
    from app.home_qt import _HeroBienestar

    monkeypatch.setenv("NM_VISUAL_QA", "1")
    hero = _HeroBienestar(
        "light_hybrid",
        lambda mid: "4/10" if mid == "animo" else "",
        username="Alex",
    )
    qtbot.addWidget(hero)
    hero.refresh()

    assert hero._stack.currentIndex() == 1
    # Mockup muestra el score sin ceros sobrantes ("10", "4"; "8.5" conserva decimal).
    assert hero._score.text() == "4"
    assert hero._score_unit.text() == "/ 10"
    assert hero._delta_lbl.text() == "▲ 0.8 vs semana"
    assert "border-radius: 10px" in hero._delta_lbl.styleSheet()
    assert hero._progress_bar.height() == 8


def test_home_view_vertical_rhythm_matches_mockup(qtbot, monkeypatch) -> None:
    from app.home_qt import HomeView

    monkeypatch.setenv("NM_VISUAL_QA", "1")
    view = HomeView(modo="light_hybrid", username="Alex")
    qtbot.addWidget(view)

    content = view.layout().itemAt(0).widget()
    content_lay = content.layout()
    margins = content_lay.contentsMargins()

    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        24,
        24,
        24,
        12,
    )
    assert view._hero.maximumHeight() == 178
    assert content_lay.itemAt(1).spacerItem().sizeHint().height() == 18
    assert content_lay.count() == 3
    assert content_lay.itemAt(2).layout() is view._grid


def test_home_module_card_matches_mockup_badge_contract(qtbot) -> None:
    from app.home_qt import ModuleCard, module_configs

    cfg = next(item for item in module_configs() if item["id"] == "rutina")
    card = ModuleCard(
        cfg,
        3,
        "light_hybrid",
        on_click=lambda _mid: None,
        get_status_fn=lambda _mid: "60% hoy",
    )
    qtbot.addWidget(card)

    assert card.minimumHeight() == 148
    assert card.maximumHeight() == 190
    assert card._icon_box.size().width() == 32
    assert card._icon_box.size().height() == 32
    assert card._badge.text() == "60% hoy"
    assert card._badge_wrap.height() == 23
    assert card._badge_dot.size().width() == 6
    assert card._badge_dot.size().height() == 6
    assert "border-radius: 11px" in card._badge_wrap.styleSheet()
    assert "padding: 4px 11px" in card._chip.styleSheet()


def test_visual_qa_home_statuses_match_mockup() -> None:
    from shared.visual_qa import module_status

    assert module_status("animo") == "10/10"
    assert module_status("respiracion") == "Activo"
    assert module_status("registro") == "En progreso"
    assert module_status("rutina") == "60% hoy"
    assert module_status("actividades") == "3 sugeridas"
    assert module_status("timer") == "45 min hoy"
    assert module_status("avisos") == "2 / 5 listos"
    assert module_status("dbt") == "4 familias"
