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
    assert card._btn_no.variant() == "ghost"
    assert card._btn_yes.variant() == "soft"
    # NMBadge ahora renderiza dot 6px prefijo en tono brand → el texto bare
    # se preserva en `_bare_text`; `.text()` devuelve rich text.
    assert card._done_badge._bare_text == "Hecho"
    assert card._done_badge.tone() == "brand"
    assert card._done_badge.isHidden()
    chip_qss = card._chip.styleSheet()
    assert "border-radius: 10px" in chip_qss
    assert "padding: 2px 8px" in chip_qss
    assert "min-height: 20px" in chip_qss

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


def test_actividades_card_title_is_serif(qtbot, monkeypatch) -> None:
    """E3-S-ACT: _SuggestedCard título usa h-serif 16px (mockup línea 1000)."""
    _use_default_texts(monkeypatch)
    import shared.fonts as _fonts_mod

    from app.modules.actividades_qt import _SuggestedCard

    card = _SuggestedCard(
        {"nombre": "Caminar", "descripcion": "Movimiento suave.", "categoria": "Física"},
        modo="light_hybrid",
    )
    qtbot.addWidget(card)

    font_serif = _fonts_mod.FONT_SERIF
    font = card._title_lbl.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"_title_lbl debe ser serif ({font_serif}), got {font.family()!r}"


def test_actividades_filter_header_title_is_serif(qtbot, monkeypatch) -> None:
    """E3-S-ACT: sección 'Elegí una familia' usa h-serif (mockup línea 1013, qfont size_h2 auto-serif)."""
    _use_default_texts(monkeypatch)
    import shared.fonts as _fonts_mod

    from app.modules import actividades_qt

    monkeypatch.setattr(actividades_qt.ModuloActividades, "_get_last_mood", lambda self: 7)
    monkeypatch.setattr(
        actividades_qt.ModuloActividades,
        "_get_activities",
        lambda self, _a: [
            {"nombre": "Caminar", "descripcion": "Suave.", "categoria": "Física"},
        ],
    )

    module = actividades_qt.ModuloActividades(show_header=False, modo="light_hybrid")
    qtbot.addWidget(module)

    font_serif = _fonts_mod.FONT_SERIF
    font = module._filter_header._title.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"filter header title debe ser serif ({font_serif}), got {font.family()!r}"
