from __future__ import annotations

import types


def _fake_sb():
    """Minimal Supabase stub that returns empty data for all calls."""
    sb = types.SimpleNamespace()

    def _noop(*_a, **_kw):
        return sb

    sb.table = _noop
    sb.select = _noop
    sb.eq = _noop
    sb.neq = _noop
    sb.execute = lambda: types.SimpleNamespace(data=[], count=0)
    return sb


# ── E4-H-PAC: Pacientes list ───────────────────────────────────────────────


def test_hub_pacientes_list_title_is_serif(qtbot) -> None:
    """E4-H-PAC: 'Lista activa' usa h-serif 20px (mockup línea 1387, size_h1 auto-serif)."""
    import shared.fonts as _fonts_mod
    from hub.main_qt import PacientesView

    view = PacientesView(
        modo="light_hybrid",
        pacientes=[],
        on_select=lambda _: None,
        on_refresh=lambda: None,
        sb=None,
    )
    qtbot.addWidget(view)

    font_serif = _fonts_mod.FONT_SERIF
    font = view._table_title.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"_table_title debe ser serif ({font_serif}), got {font.family()!r}"


def test_hub_pacientes_badge_tone_is_info(qtbot) -> None:
    """E4-H-PAC: results badge usa tone='info' (mockup línea 1388: class='badge brand')."""
    from hub.main_qt import PacientesView

    view = PacientesView(
        modo="light_hybrid",
        pacientes=[],
        on_select=lambda _: None,
        on_refresh=lambda: None,
        sb=None,
    )
    qtbot.addWidget(view)

    assert view._results_badge.tone() == "info"


# ── E4-H-PAC: Detalle hero ────────────────────────────────────────────────


def test_hub_detalle_patient_name_is_serif(qtbot) -> None:
    """E4-H-PAC: nombre del paciente en el hero usa h-serif (mockup línea 1513)."""
    import shared.fonts as _fonts_mod
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView(
        modo="light_hybrid",
        sb=_fake_sb(),
        paciente_id="test-001",
        paciente_nombre="Ana Martínez",
    )
    qtbot.addWidget(view)

    font_serif = _fonts_mod.FONT_SERIF
    font = view._lbl_name.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"_lbl_name debe ser serif ({font_serif}), got {font.family()!r}"


def test_hub_detalle_avatar_is_52px_r15(qtbot) -> None:
    """E4-H-PAC: avatar 52×52 border-radius 15 (mockup línea 1510)."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView(
        modo="light_hybrid",
        sb=_fake_sb(),
        paciente_id="test-001",
        paciente_nombre="Ana Martínez",
    )
    qtbot.addWidget(view)

    assert view._avatar.width() == 52
    assert view._avatar.height() == 52
    assert view._avatar._radius == 15


def test_hub_detalle_plan_tabs_match_mockup(qtbot) -> None:
    """E4-H-PAC: 4 tabs del plan terapéutico = labels exactos del mockup (línea 1444-1449)."""
    from hub.plan_terapeutico import PlanTerapeuticoTab

    tab = PlanTerapeuticoTab(
        modo="light_hybrid",
        sb=_fake_sb(),
        pid="test-001",
        nombre="Ana Martínez",
    )
    qtbot.addWidget(tab)

    expected = [
        "Recordatorios de Bienestar",
        "Temporizador de Actividades",
        "Checklist de Rutina Diaria",
        "Asistente de Activación Conductual",
    ]
    assert tab._tabs.count() == 4
    actual = [tab._tabs.tabText(i) for i in range(tab._tabs.count())]
    assert actual == expected


# ── E4-H-CONFIG: Textos globales ──────────────────────────────────────────


def test_hub_config_textos_title_is_serif(qtbot) -> None:
    """E4-H-CONFIG: 'Textos globales' usa h-serif ~19-20px (mockup línea 1602)."""
    import shared.fonts as _fonts_mod
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=None)
    qtbot.addWidget(view)

    font_serif = _fonts_mod.FONT_SERIF
    font = view._title_lbl.font()
    assert (
        font_serif.lower() in font.family().lower()
        or font.family().lower() in font_serif.lower()
    ), f"_title_lbl debe ser serif ({font_serif}), got {font.family()!r}"


def test_hub_config_textos_save_starts_disabled(qtbot) -> None:
    """E4-H-CONFIG: 'Guardar cambios' arranca deshabilitado (mockup línea 1617: disabled)."""
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=None)
    qtbot.addWidget(view)

    assert not view._save.isEnabled()


def test_hub_config_textos_has_search_and_filter(qtbot) -> None:
    """E4-H-CONFIG: vista tiene NMSearchInput + filtro de módulos (mockup líneas 1603-1609)."""
    from hub.config_global_texts import TextosGlobalesSuiteView

    view = TextosGlobalesSuiteView(modo="light_hybrid", sb=None)
    qtbot.addWidget(view)

    assert hasattr(view, "_search")
    assert hasattr(view, "_section_filter")
    assert view._section_filter.count() > 1
