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
