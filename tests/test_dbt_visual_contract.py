from __future__ import annotations

from app.modules.dbt_qt import _PracticeModalScrim


DBT_V2_PRACTICES = [
    "observe_describe",
    "wise_mind",
    "participate",
    "non_judgmental",
    "stop",
    "tipp",
    "self_soothe",
    "radical_acceptance",
    "check_facts",
    "opposite_action",
    "problem_solving",
    "please",
    "dear_man",
    "give",
    "fast",
    "validation_limits",
]


def test_practice_modal_scrim_constants_match_canonical_contract() -> None:
    """Static contract: DBT modal backdrop stays canonical."""
    assert _PracticeModalScrim._SCRIM_BLUR_RADIUS_LIGHT == 3
    assert _PracticeModalScrim._SCRIM_BLUR_RADIUS_DARK == 3
    assert _PracticeModalScrim._SCRIM_RGBA == (20, 18, 14, 128)


def _use_default_texts(monkeypatch) -> None:
    from app.modules import dbt_qt

    monkeypatch.setattr(
        dbt_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def test_dbt_tabs_remove_history_from_ui_v2(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.dbt_qt import ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._tabs._labels == ["Ahora", "Biblioteca"]
    assert module._view_stack.count() == 2
    assert not hasattr(module, "_view_historial")
    assert not hasattr(module, "_history_lay")

    module._tabs.set_current(1)

    assert module._view_stack.currentIndex() == 1


def test_dbt_library_has_16_formal_practices(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.dbt_qt import DBT_SKILLS, ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)
    module._tabs.set_current(1)

    assert list(DBT_SKILLS) == DBT_V2_PRACTICES
    assert module._library_grid.count() == 16


def test_dbt_now_cards_open_canonical_practices(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.dbt_qt import DBT_NEED_PRACTICE_IDS, ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    expected = {
        "mindfulness": "wise_mind",
        "distress_tolerance": "stop",
        "emotion_regulation": "check_facts",
        "interpersonal_effectiveness": "dear_man",
    }
    assert DBT_NEED_PRACTICE_IDS == expected

    for family, practice_id in expected.items():
        assert module.start_practice_by_id(practice_id) is True
        assert module._current_skill_id == practice_id
        module._cleanup_practice_flow()
        module._on_need_clicked(family)
        assert module._current_skill_id == practice_id
        module._cleanup_practice_flow()


def test_each_dbt_practice_opens_own_title_and_step_counter(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.dbt_qt import DBT_SKILLS, ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    for practice_id in DBT_V2_PRACTICES:
        skill = DBT_SKILLS[practice_id]
        assert module.start_practice(skill) is True
        practice = module._practice_view
        assert practice.title_lbl.text().startswith(f"{skill['title']} · ")
        assert practice.progress_lbl.text() == f"Paso 1 de {len(skill['steps'])}"
        assert practice.safety_lbl is not None
        module._cleanup_practice_flow()


def test_stop_is_not_universal_fallback_and_unknown_practice_is_blocked(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.dbt_qt import ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module.start_practice_by_id("check_facts") is True
    assert module._current_skill_id == "check_facts"
    assert module._practice_view.title_lbl.text().startswith("Verificar los hechos · ")
    module._cleanup_practice_flow()

    assert module.start_practice_by_id("does_not_exist") is False
    assert module._practice_view is None


def test_dbt_stop_practice_uses_modal_stepper_contract(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from PyQt6.QtCore import Qt

    from app.modules.dbt_qt import DBT_SKILLS, ModuloDBT, _SkillCard

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    card = _SkillCard(DBT_SKILLS["stop"], modo="light_hybrid")
    qtbot.addWidget(card)
    assert card.family_lbl.isHidden()

    module.start_practice(DBT_SKILLS["stop"])

    practice = module._practice_view
    assert practice.maximumWidth() == 560
    assert practice.title_lbl.text() == "STOP · Tolerancia"
    assert practice.progress_lbl.text() == "Paso 1 de 4"
    assert practice.step_card.maximumHeight() == 190
    assert practice.step_body_lbl.alignment() & Qt.AlignmentFlag.AlignHCenter
    assert practice.safety_lbl is not None
    assert practice.safety_lbl.alignment() & Qt.AlignmentFlag.AlignHCenter

    practice._next_step()

    assert practice.progress_lbl.text() == "Paso 2 de 4"


def test_dbt_step_title_uses_serif_font(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)
    from shared.fonts import FONT_SERIF
    from app.modules.dbt_qt import DBT_SKILLS, ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    module.start_practice(DBT_SKILLS["stop"])
    practice = module._practice_view

    font = practice.step_title_lbl.font()
    assert FONT_SERIF.lower() in font.family().lower() or font.family().lower() in FONT_SERIF.lower(), (
        f"step_title_lbl debe usar familia serif ({FONT_SERIF}), got {font.family()!r}"
    )


def test_dbt_need_card_title_uses_serif_font(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)
    import shared.fonts as _fonts_mod
    from app.modules.dbt_qt import _NeedCard

    card = _NeedCard(
        "Volver al presente",
        "Mindfulness: pausar y notar el presente.",
        "mindfulness",
        "mind",
        modo="light_hybrid",
    )
    qtbot.addWidget(card)

    font_serif = _fonts_mod.FONT_SERIF
    font = card.title_label.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"NeedCard title debe ser serif ({font_serif}), got {font.family()!r}"


def test_dbt_skill_card_title_uses_serif_font(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)
    import shared.fonts as _fonts_mod
    from app.modules.dbt_qt import DBT_SKILLS, _SkillCard

    card = _SkillCard(DBT_SKILLS["stop"], modo="light_hybrid")
    qtbot.addWidget(card)

    assert card.minimumHeight() == 128
    assert card.maximumHeight() == 128

    font_serif = _fonts_mod.FONT_SERIF
    font = card.title_lbl.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"SkillCard title debe ser serif ({font_serif}), got {font.family()!r}"
