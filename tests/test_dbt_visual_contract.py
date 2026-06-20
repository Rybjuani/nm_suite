from __future__ import annotations


def _use_default_texts(monkeypatch) -> None:
    from app.modules import dbt_qt

    monkeypatch.setattr(
        dbt_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def test_dbt_tabs_preserve_history_extra_and_stack(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.dbt_qt import ModuloDBT

    module = ModuloDBT(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._tabs._labels == ["Ahora", "Biblioteca", "Historial"]
    assert module._view_stack.count() == 3

    module._tabs.set_current(2)

    assert module._view_stack.currentIndex() == 2
    assert hasattr(module, "_history_lay")
    assert module._history_lay.count() > 0


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
    assert practice.title_lbl.text() == "STOP · TOLERANCIA"
    assert practice.progress_lbl.text() == "Paso 1 de 4"
    assert practice.step_card.maximumHeight() == 190
    assert practice.safety_lbl is not None
    assert practice.safety_lbl.alignment() & Qt.AlignmentFlag.AlignHCenter

    practice._next_step()

    assert practice.progress_lbl.text() == "Paso 2 de 4"
