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

    # Mockup canónico l.1388: class="badge brand". El código actual usa
    # tone="info" (alias interno que rinde al mismo color: ambos mapean a
    # _BADGE_TONE_TO_KEY["primary"]/["primary_soft"]). Visualmente idéntico,
    # pero el spec declara explícitamente `brand`; el alias `info` es
    # desviación semántica. Migración desde UI anterior que pineaba
    # `info` por consistencia con otros badges; el spec del mockup es
    # la verdad.
    assert view._results_badge.tone() == "brand"


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


def test_hub_activacion_empty_state_is_calm_text_only(qtbot) -> None:
    """El empty de Activación es CALMO: solo texto, SIN chip de ícono.

    Decisión deliberada (commit 8b9d5f7 'simplificado: solo texto calmo' vía
    _empty_hint_label). Antes había una card de ícono compacta; este test
    bloquea esa regresión inversa y verifica el contrato vigente.
    """
    from PyQt6.QtWidgets import QFrame, QLabel
    from hub.plan_terapeutico import _PresetActivacionTab

    tab = _PresetActivacionTab(
        sb=_fake_sb(),
        pid="test-001",
        modo="light_hybrid",
    )
    qtbot.addWidget(tab)

    # Sin presets asignados → se muestra el texto calmo del empty state.
    labels = [
        lbl for lbl in tab.findChildren(QLabel)
        if lbl.text() == "Sin actividades personalizadas aún."
    ]
    assert labels, "el empty state de Activación debe mostrar el texto calmo"

    # Solo texto: no debe existir el chip de ícono (decisión de diseño vigente).
    assert tab.findChild(QFrame, "ActivationEmptyIconChip") is None


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


# ── E4-H-MODALES: Resumen IA / PDF ────────────────────────────────────────


def test_hub_resumen_ia_uses_nm_dialog_overlay(qtbot, monkeypatch) -> None:
    """E4-H-MODALES: Resumen IA usa el modal canonico con scrim/scale, no QDialog nativo."""
    from PyQt6.QtWidgets import QLabel, QTabWidget, QWidget
    import hub.plan_terapeutico as plan_module
    from hub.pacientes_qt import DetallePacienteView
    from shared.components.dialogs import NMDialog, _NM_MODAL_SCALE_FROM

    class _FakePlan(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self._tabs = QTabWidget(self)
            self._tabs.addTab(QWidget(), "Plan")

    monkeypatch.setattr(plan_module, "PlanTerapeuticoTab", _FakePlan)

    view = DetallePacienteView(
        modo="light_hybrid",
        sb=_fake_sb(),
        paciente_id="test-001",
        paciente_nombre="Ana Martínez",
    )
    view.resize(960, 600)
    qtbot.addWidget(view)
    view.show()

    view._btn_resumen_ia.setEnabled(False)
    view._btn_resumen_ia.setText("Generando...")
    view._show_resumen_dialog("Texto de prueba IA")

    dialog = view._resumen_dialog
    assert isinstance(dialog, NMDialog)
    assert dialog.parent() is view.window()
    assert dialog.isVisible()
    assert dialog._dialog_width == 720
    assert dialog._panel.height() == 462
    assert dialog._panel_scale == _NM_MODAL_SCALE_FROM
    assert view._btn_resumen_ia.isEnabled()
    assert view._btn_resumen_ia.text() == "Resumen IA"

    body_labels = [
        w.text()
        for w in dialog.findChildren(QLabel)
        if w.objectName() == "ResumenIALabel"
    ]
    assert len(body_labels) == 4
    assert body_labels[0] == "Texto de prueba IA"
    assert "Cumplimiento del 71%" in body_labels[1]
    assert "catastrofización" in body_labels[2]
    assert "Verificar los hechos" in body_labels[3]

    dialog.close()
    qtbot.wait(20)
    assert view._resumen_dialog is None
