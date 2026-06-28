from __future__ import annotations


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


def test_dbt_stop_practice_uses_modal_stepper_contract(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from PyQt6.QtCore import Qt

    from app.modules.dbt_qt import DBT_SKILLS, ModuloDBT, _SkillCard

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    card = _SkillCard(DBT_SKILLS["distress_stop"], modo="light_hybrid")
    qtbot.addWidget(card)
    assert card.family_lbl.isHidden()

    module.start_practice(DBT_SKILLS["distress_stop"])

    practice = module._practice_view
    assert practice.maximumWidth() == 560
    # Mockup l.1091 DBT_FAMILIES + l.1172 eyebrow `STOP · ${fam}`: el eyebrow
    # usa el nombre CORTO de la familia en Title Case. Migración desde UI
    # anterior que pineaba el render UPPERCASE del título largo. El código
    # `app/modules/dbt_qt.py:579-583` ya rindió al spec usando
    # _DBT_FAMILY_TITLES (corto) sin .upper().
    assert practice.title_lbl.text() == "STOP · Tolerancia"
    assert practice.progress_lbl.text() == "Paso 1 de 4"
    assert practice.step_card.maximumHeight() == 190
    assert practice.step_body_lbl.alignment() & Qt.AlignmentFlag.AlignHCenter
    assert practice.safety_lbl is not None
    assert practice.safety_lbl.alignment() & Qt.AlignmentFlag.AlignHCenter

    practice._next_step()

    assert practice.progress_lbl.text() == "Paso 2 de 4"


def test_dbt_step_title_uses_serif_font(qtbot, monkeypatch) -> None:
    """E2-SERIF-TITLES: el headline del paso DBT usa Fraunces (h-serif mockup línea 1178)."""
    _use_default_texts(monkeypatch)
    from shared.fonts import FONT_SERIF
    from app.modules.dbt_qt import DBT_SKILLS, ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    module.start_practice(DBT_SKILLS["distress_stop"])
    practice = module._practice_view

    font = practice.step_title_lbl.font()
    assert FONT_SERIF.lower() in font.family().lower() or font.family().lower() in FONT_SERIF.lower(), (
        f"step_title_lbl debe usar familia serif ({FONT_SERIF}), got {font.family()!r}"
    )


def test_dbt_need_card_title_uses_serif_font(qtbot, monkeypatch) -> None:
    """E3-S-DBT: NeedCard título usa h-serif (mockup línea 1124, size_h4 serif)."""
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
    """E3-S-DBT: SkillCard título usa h-serif (mockup línea 1136, size_h4 serif)."""
    _use_default_texts(monkeypatch)
    import shared.fonts as _fonts_mod
    from app.modules.dbt_qt import DBT_SKILLS, _SkillCard

    card = _SkillCard(DBT_SKILLS["distress_stop"], modo="light_hybrid")
    qtbot.addWidget(card)

    assert card.minimumHeight() == 128
    assert card.maximumHeight() == 128

    font_serif = _fonts_mod.FONT_SERIF
    font = card.title_lbl.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"SkillCard title debe ser serif ({font_serif}), got {font.family()!r}"
