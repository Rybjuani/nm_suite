from __future__ import annotations


def _use_default_texts(monkeypatch) -> None:
    from app.modules import actividades_qt

    monkeypatch.setattr(
        actividades_qt,
        "t",
        lambda _key, default, patient_id=None: default,
    )


def test_actividad_card_actions_and_done_badge_match_mockup(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules.actividades_qt import _SuggestedCard

    card = _SuggestedCard(
        {
            "nombre": "Caminar diez minutos",
            "descripcion": "Salir a caminar por una zona tranquila.",
            "categoria": "Física",
        },
        modo="light_hybrid",
    )
    qtbot.addWidget(card)

    assert card._btn_no.text() == "No pude"
    assert card._btn_yes.text() == "Hice"
    assert card._btn_no.variant() == "secondary"
    assert card._btn_yes.variant() == "secondary"
    # NMBadge ahora renderiza dot 6px prefijo en tono brand → el texto bare
    # se preserva en `_bare_text`; `.text()` devuelve rich text.
    assert card._done_badge._bare_text == "Hecho"
    assert card._done_badge.tone() == "brand"
    assert card._done_badge.isHidden()

    card.set_completed(True)

    assert card._btn_no.isHidden()
    assert card._btn_yes.isHidden()
    assert not card._done_badge.isHidden()
    assert card._done_badge._bare_text == "Hecho"


def test_actividades_filters_are_mockup_fchips_and_count_is_visible(qtbot, monkeypatch) -> None:
    _use_default_texts(monkeypatch)

    from app.modules import actividades_qt

    monkeypatch.setattr(actividades_qt.ModuloActividades, "_get_last_mood", lambda self: 7)
    monkeypatch.setattr(
        actividades_qt.ModuloActividades,
        "_get_activities",
        lambda self, _animo: [
            {
                "nombre": "Respirar al aire libre",
                "descripcion": "Hacer una pausa corta en un lugar abierto.",
                "categoria": "Autocuidado",
            },
            {
                "nombre": "Caminar diez minutos",
                "descripcion": "Movimiento suave.",
                "categoria": "Física",
            },
        ],
    )

    module = actividades_qt.ModuloActividades(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    assert module._category_tabs._variant == "filter"
    assert module._category_tabs._labels == [
        "Todas",
        "Autocuidado",
        "Física",
        "Cognitiva",
        "Placer",
        "Social",
        "Maestría",
    ]
    assert module._footer_lbl.text() == "2 actividades sugeridas"

    module._on_category_tab_changed(2, "Física")

    assert module._current_filter == "Física"
    assert module._footer_lbl.text() == "1 actividad sugerida"
