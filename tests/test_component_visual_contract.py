from __future__ import annotations


def test_button_primitive_uses_mockup_control_height() -> None:
    from shared.components.buttons import _NM_CONTROL_COMPACT_HEIGHT, _NM_CONTROL_HEIGHT

    assert _NM_CONTROL_HEIGHT == 42
    assert _NM_CONTROL_COMPACT_HEIGHT == 34


def test_button_primitive_supports_mockup_soft_variant(qtbot) -> None:
    import inspect

    from shared.components.buttons import NMButton

    btn = NMButton("Hice", variant="soft", modo="light_hybrid", size="sm")
    qtbot.addWidget(btn)

    assert btn.variant() == "soft"
    source = inspect.getsource(NMButton.paintEvent)
    assert 'self._variant == "soft"' in source
    assert 'v3c("brandSoft", self._modo)' in source
    assert 'v3c("brandLine", self._modo)' in source
    assert 'v3c("brand", self._modo)' in source


def test_button_press_animation_does_not_mutate_layout_geometry(qtbot) -> None:
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QHBoxLayout, QWidget

    from shared.components.buttons import NMButton

    host = QWidget()
    lay = QHBoxLayout(host)
    btn = NMButton("Siguiente", variant="gradient", modo="dark_hybrid", width=160)
    lay.addWidget(btn)
    qtbot.addWidget(host)
    host.resize(240, 80)
    host.show()
    qtbot.wait(50)

    before = btn.geometry()
    QTest.mousePress(btn, Qt.MouseButton.LeftButton)
    qtbot.wait(140)
    assert btn.geometry() == before

    QTest.mouseRelease(btn, Qt.MouseButton.LeftButton)
    qtbot.wait(140)
    assert btn.geometry() == before


def test_button_keeps_contract_height_under_global_pushbutton_qss(qtbot, qapp) -> None:
    from PyQt6.QtWidgets import QHBoxLayout, QWidget

    from shared.components.buttons import NMButton, _NM_CONTROL_HEIGHT

    old_qss = qapp.styleSheet()
    try:
        qapp.setStyleSheet("QPushButton { padding: 11px 20px; min-height: 32px; }")
        host = QWidget()
        lay = QHBoxLayout(host)
        btn = NMButton("Guardar registro", variant="gradient", modo="dark_hybrid", width=160)
        lay.addWidget(btn)
        qtbot.addWidget(host)
        host.resize(240, 80)
        host.show()
        qtbot.wait(50)

        assert btn.height() == _NM_CONTROL_HEIGHT
        assert btn.minimumHeight() == _NM_CONTROL_HEIGHT
        assert btn.maximumHeight() == _NM_CONTROL_HEIGHT
    finally:
        qapp.setStyleSheet(old_qss)


def test_tabs_pill_paints_mockup_container_and_brand_selection(qtbot) -> None:
    import inspect

    from shared.components.buttons import (
        NMTabs,
        _NM_TAB_CONTAINER_GAP,
        _NM_TAB_CONTAINER_PAD,
        _NM_TAB_PILL_BUTTON_HEIGHT,
    )

    tabs = NMTabs(["Todas", "Mindfulness", "Tolerancia"], variant="pill", modo="light_hybrid")
    qtbot.addWidget(tabs)
    tabs.set_current(1)

    margins = tabs.layout().contentsMargins()
    assert margins.left() == _NM_TAB_CONTAINER_PAD == 5
    assert margins.top() == 5
    assert tabs.layout().spacing() == _NM_TAB_CONTAINER_GAP == 4
    assert all(btn.height() == _NM_TAB_PILL_BUTTON_HEIGHT == 30 for btn in tabs._btns)

    selected_qss = tabs._btns[1].styleSheet()
    rest_qss = tabs._btns[0].styleSheet()
    assert tabs._PAINTED_CONTAINER_VARIANTS == ("pill", "seg")
    assert "background: #2e5d43" in selected_qss
    assert "color: #f7f3ea" in selected_qss
    assert "background: transparent" in rest_qss

    source = inspect.getsource(NMTabs.paintEvent)
    assert "self._PAINTED_CONTAINER_VARIANTS" in source
    assert '"surface_2" if self._variant == "pill" else "surface3"' in source


def test_badge_primitive_supports_mockup_tones(qtbot) -> None:
    from shared.components.surfaces import NMBadge

    badge = NMBadge("Estado", tone="gold", modo="light_hybrid")
    qtbot.addWidget(badge)

    qss = badge.styleSheet()
    assert "color: #C2912F" in qss
    assert "background-color: rgba(194,145,47,0.16)" in qss
    # Mockup línea 265: .badge { border-radius: var(--r-pill) } = 999px (r-pill)
    assert "border-radius: 999px" in qss
    assert "padding: 4px 11px" in qss
    # Mockup línea 266: font-size: 11.5px
    assert "font-size: 11.5px" in qss


def test_input_focus_uses_mockup_brand_line_and_soft_halo(qtbot) -> None:
    import inspect

    from shared.components.buttons import NMInput, NMTextArea

    line = NMInput("Buscar", modo="light_hybrid")
    area = NMTextArea("Mensaje", modo="light_hybrid")
    qtbot.addWidget(line)
    qtbot.addWidget(area)

    assert "QLineEdit:focus" in line.styleSheet()
    assert "rgba(46, 93, 67, 71)" in line.styleSheet()
    assert "QTextEdit:focus" in area.styleSheet()
    assert "rgba(46, 93, 67, 71)" in area.styleSheet()

    assert 'v3c("brandSoft", self._modo)' in inspect.getsource(NMInput.focusInEvent)
    assert 'v3c("brandSoft", self._modo)' in inspect.getsource(NMTextArea.focusInEvent)


def test_card_hover_border_uses_brand_line() -> None:
    source = __import__("inspect").getsource(
        __import__("shared.components.cards", fromlist=["NMCard"]).NMCard.paintEvent
    )

    assert 'v3c("brandLine", self._modo)' in source


def test_mood_slider_internal_uses_shared_mockup_slider_qss(qtbot) -> None:
    from shared.components.mood import NMMoodSlider

    slider = NMMoodSlider(modo="light_hybrid")
    qtbot.addWidget(slider)

    qss = slider._slider.styleSheet()
    assert "height: 8px" in qss
    assert "stop:0 #7b8a99" in qss
    assert "stop:1 #b24e3d" in qss
    assert "width: 22px" in qss
    assert "border: 3px solid #2E5D43" in qss


def test_v3_mood_slider_thumb_uses_mockup_brand_contract() -> None:
    import inspect

    from shared.components.mood import _MoodTrackBar

    source = inspect.getsource(_MoodTrackBar.paintEvent)
    assert 'v3c("brand", _tm().modo)' in source
    assert 'v3c("brandSoft", _tm().modo)' in source
    assert "p.drawEllipse(QPointF(x, center_y), 11, 11)" in source
    assert "QPen(QColor(lv_color), 3)" not in source


def test_routine_checkbox_matches_mockup_rt_cb_contract(qtbot) -> None:
    from shared.components.session import (
        NMCustomCheck,
        _NM_RT_CHECK_RADIUS,
        _NM_RT_CHECK_SIZE,
        _NMAnimCheckBox,
    )

    check = NMCustomCheck("Tarea", checked=True, modo="light_hybrid")
    qtbot.addWidget(check)

    assert _NM_RT_CHECK_SIZE == 22
    assert _NM_RT_CHECK_RADIUS == 7
    assert check._box.width() == 22
    assert check._box.height() == 22

    source = __import__("inspect").getsource(_NMAnimCheckBox.paintEvent)
    assert 'v3c("primary" if self._checked else "line", self._modo)' in source
    assert 'v3c("primary" if self._checked else "surface", self._modo)' in source
    assert 'v3c("primary_ink", self._modo)' in source


def test_stepper_matches_mockup_line_and_dot_contract(qtbot) -> None:
    from shared.components.feedback import (
        NMStepper,
        _NM_STEPPER_DOT_SIZE,
        _NM_STEPPER_LINE_INSET,
        _NM_STEPPER_LINE_Y,
        _NM_STEPPER_MAX_WIDTH,
    )

    stepper = NMStepper(["Situación", "Emoción", "Pensamiento", "Respuesta"], modo="dark_hybrid")
    qtbot.addWidget(stepper)
    stepper.set_step(2)

    assert _NM_STEPPER_MAX_WIDTH == 620
    assert _NM_STEPPER_LINE_INSET == 0.08
    assert _NM_STEPPER_LINE_Y == 9.0
    assert _NM_STEPPER_DOT_SIZE == 18
    assert stepper.height() == 56

    source = __import__("inspect").getsource(NMStepper.paintEvent)
    assert 'v3c("line", self._modo)' in source
    assert 'v3c("primary", self._modo)' in source
    assert 'v3c("surface3", self._modo)' in source
    assert "weight=600 if i == self._current else 500" in source


def test_empty_state_matches_mockup_icon_and_title_contract(qtbot) -> None:
    from shared.components.overlays import (
        NMEmptyState,
        _NM_EMPTY_ICON_CHIP_RADIUS,
        _NM_EMPTY_ICON_CHIP_SIZE,
        _NM_EMPTY_ICON_SIZE,
        _NM_EMPTY_TITLE_SIZE,
    )

    empty = NMEmptyState("timer", "Sin actividades", "Tu terapeuta enviara actividades pronto.")
    qtbot.addWidget(empty)

    assert _NM_EMPTY_ICON_CHIP_SIZE == 64
    assert _NM_EMPTY_ICON_CHIP_RADIUS == 18
    assert _NM_EMPTY_ICON_SIZE == 30
    assert _NM_EMPTY_TITLE_SIZE == 20
    assert empty._icon_chip.width() == 64
    assert empty._icon_chip.height() == 64
    assert empty._icon_lbl.width() == 30
    assert empty._icon_lbl.height() == 30
    assert empty._title_lbl.font().pixelSize() == 20
    assert empty._title_lbl.font().weight() >= 600
    assert "border-radius: 18px" in empty._icon_chip.styleSheet()


def test_toast_matches_mockup_pill_contract(qtbot) -> None:
    from PyQt6.QtWidgets import QWidget
    from shared.components.feedback import (
        NMToast,
        _NM_TOAST_BOTTOM_MARGIN,
        _NM_TOAST_DEFAULT_DURATION,
        _NM_TOAST_GAP,
        _NM_TOAST_ICON_SIZE,
        _NM_TOAST_PAD_X,
        _NM_TOAST_PAD_Y,
        _NM_TOAST_SLIDE_PX,
    )

    host = QWidget()
    host.resize(520, 320)
    qtbot.addWidget(host)
    toast = NMToast(host, "Registro guardado")

    assert toast._duration == _NM_TOAST_DEFAULT_DURATION == 2200
    assert toast._margins == (_NM_TOAST_PAD_X, _NM_TOAST_PAD_Y, _NM_TOAST_PAD_X, _NM_TOAST_PAD_Y)
    assert _NM_TOAST_ICON_SIZE == 16
    assert _NM_TOAST_GAP == 9
    assert toast._font.pixelSize() == 13
    assert toast._font.weight() >= 500

    toast._slide_offset = 0
    toast._reposition()
    assert toast.x() == (host.width() - toast.width()) // 2
    assert toast.y() == host.height() - toast.height() - _NM_TOAST_BOTTOM_MARGIN

    source = __import__("inspect").getsource(NMToast.paintEvent)
    assert "drawPixmap" in source
    assert "_NM_TOAST_SHADOW_PAD" in source
    assert "drawRect(QRectF(0, 0, 4" not in source
    assert _NM_TOAST_SLIDE_PX == 20


def test_dialog_matches_mockup_modal_contract(qtbot) -> None:
    from PyQt6.QtWidgets import QWidget
    from shared.components.dialogs import (
        NMDialog,
        _NM_MODAL_ANIM_MS,
        _NM_MODAL_MAX_WIDTH,
        _NM_MODAL_SCALE_FROM,
        _NM_MODAL_SCRIM_RGBA,
        _NM_MODAL_WIDTH_RATIO,
    )

    host = QWidget()
    host.resize(520, 360)
    qtbot.addWidget(host)
    dialog = NMDialog("Confirmar", modo="light_hybrid", parent=host)
    qtbot.addWidget(dialog)

    assert _NM_MODAL_MAX_WIDTH == 560
    assert _NM_MODAL_WIDTH_RATIO == 0.92
    assert _NM_MODAL_SCRIM_RGBA == (20, 18, 14, 128)
    assert _NM_MODAL_SCALE_FROM == 0.96
    assert _NM_MODAL_ANIM_MS == 240
    assert dialog._dialog_width == 560
    assert dialog._effective_panel_width() == int(host.width() * 0.92)

    dialog._set_panel_scale(1.0)
    assert dialog._panel.width() == int(host.width() * 0.92)
    assert dialog._panel.graphicsEffect() is not None
    assert "border-radius: 28px" in dialog._panel.styleSheet()

    primary = dialog.add_footer_button("Guardar", role="primary")
    assert "background: #2e5d43" in primary.styleSheet()
    assert "color: #f7f3ea" in primary.styleSheet()

    source = __import__("inspect").getsource(NMDialog.paintEvent)
    assert "QColor(*_NM_MODAL_SCRIM_RGBA)" in source


def test_card_hover_lift_matches_mockup(qtbot) -> None:
    # Mockup `.card.hov:hover` (línea 260): translateY(-3px) + shadow-2 +
    # brand-line. Solo en hover real; el reposo (lo que captura el harness QA)
    # queda idéntico.
    from PyQt6.QtCore import QEvent, QPointF
    from PyQt6.QtGui import QEnterEvent
    from shared.components.cards import NMCard, _NM_CARD_HOVER_LIFT_PX
    from shared.theme import V3_SHADOWS

    rest_blur = V3_SHADOWS["light"]["shadow_1"]["blur"]
    hover_blur = V3_SHADOWS["light"]["shadow_2"]["blur"]
    assert _NM_CARD_HOVER_LIFT_PX == 3
    assert hover_blur > rest_blur  # shadow-2 más prominente que shadow-1

    card = NMCard(clickable=True, modo="light_hybrid")
    qtbot.addWidget(card)

    # Reposo: shadow-1, sin lift.
    assert card._hover is False
    assert card._lift_base_y is None
    assert card._card_shadow.blurRadius() == rest_blur

    base_y = card.pos().y()
    pt = QPointF(5.0, 5.0)
    card.enterEvent(QEnterEvent(pt, pt, pt))

    # Hover: lift -3px + shadow-2.
    assert card._hover is True
    assert card._card_shadow.blurRadius() == hover_blur
    assert card._lift_anim is not None
    assert card._lift_anim.endValue().y() == base_y - _NM_CARD_HOVER_LIFT_PX

    card.leaveEvent(QEvent(QEvent.Type.Leave))

    # Al salir: vuelve a reposo (shadow-1).
    assert card._hover is False
    assert card._card_shadow.blurRadius() == rest_blur


def test_card_non_clickable_does_not_lift(qtbot) -> None:
    # `.card` sin `.hov` (info estática) no se levanta en hover.
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QEnterEvent
    from shared.components.cards import NMCard
    from shared.theme import V3_SHADOWS

    rest_blur = V3_SHADOWS["light"]["shadow_1"]["blur"]
    card = NMCard(clickable=False, modo="light_hybrid")
    qtbot.addWidget(card)

    pt = QPointF(5.0, 5.0)
    card.enterEvent(QEnterEvent(pt, pt, pt))

    assert card._lift_base_y is None
    assert card._card_shadow.blurRadius() == rest_blur


def test_module_ring_matches_mockup_conic_contract(qtbot) -> None:
    from shared.components.rings import NMModuleRing, _ring_stroke

    ring = NMModuleRing(modo="light_hybrid")
    qtbot.addWidget(ring)

    assert NMModuleRing.DEFAULT_SIZE == 54
    assert ring.width() == 54
    assert ring.height() == 54
    assert ring._color_key == "primary"
    assert _ring_stroke(54) == 6

    source = __import__("inspect").getsource(NMModuleRing.paintEvent)
    assert 'v3c("ringTrack", self._modo)' in source
    assert "v3c(self._color_key, self._modo)" in source
    assert 'v3c("surface", self._modo)' in source
    assert "_paint_v3_arc" not in source


def test_play_button_matches_mockup_ctl_contract(qtbot) -> None:
    from shared.components.inputs import NMPlayButton

    neutral = NMPlayButton(icon_name="refresh", size="md", modo="light_hybrid")
    main = NMPlayButton(icon_name="play", size="lg", modo="light_hybrid")
    qtbot.addWidget(neutral)
    qtbot.addWidget(main)

    assert NMPlayButton._SIZE_MAP["md"] == 46
    assert NMPlayButton._SIZE_MAP["lg"] == 58
    assert neutral.width() == 46
    assert neutral.height() == 46
    assert main.width() == 58
    assert main.height() == 58
    assert neutral.graphicsEffect() is not None
    assert main.graphicsEffect() is not None

    source = __import__("inspect").getsource(NMPlayButton.paintEvent)
    assert 'self._size_key == "lg"' in source
    assert 'v3c("brandStrong" if self._hover else "primary", self._modo)' in source
    assert 'v3c("brandLine" if self._hover else "line", self._modo)' in source
    assert '"primary_ink" if is_main' in source


def test_window_chrome_matches_mockup_titlebar_contract(qtbot) -> None:
    from shared.components.chrome import (
        _ChromeThemeToggle,
        NMWindowChrome,
        _ChromeWinBtn,
        _NM_CHROME_BACK_RADIUS,
        _NM_CHROME_BACK_SIZE,
        _NM_CHROME_GAP,
        _NM_CHROME_HEIGHT,
        _NM_CHROME_ICON_SIZE,
        _NM_CHROME_PAD_X,
        _NM_CHROME_THEME_ICON_SIZE,
        _NM_CHROME_THEME_TOGGLE_H,
        _NM_CHROME_THEME_TOGGLE_RADIUS,
        _NM_CHROME_THEME_TOGGLE_W,
        _NM_CHROME_WIN_DOT_COLORS,
        _NM_CHROME_WIN_DOT_GAP,
        _NM_CHROME_WIN_DOT_OPACITY,
        _NM_CHROME_WIN_DOT_SIZE,
    )

    chrome = NMWindowChrome(
        title="NeuroMood",
        subtitle="Pacientes",
        show_theme_toggle=True,
        modo="light_hybrid",
    )
    qtbot.addWidget(chrome)
    chrome.set_module_context("Respiracion", "breath")
    assert chrome.height() == _NM_CHROME_HEIGHT == 44

    margins = chrome.layout().contentsMargins()
    assert margins.left() == _NM_CHROME_PAD_X == 16
    assert margins.right() == 16
    assert chrome.layout().spacing() == _NM_CHROME_GAP == 10
    assert chrome._mark._icon_name == "home"
    assert chrome._mark.width() == 18
    assert chrome._mark.height() == 18

    hub_chrome = NMWindowChrome(title="NeuroMood Hub", modo="light_hybrid")
    qtbot.addWidget(hub_chrome)
    assert hub_chrome._mark._icon_name == "brain"

    assert chrome._ctx_back.width() == _NM_CHROME_BACK_SIZE == 26
    assert chrome._ctx_back.height() == 26
    assert _NM_CHROME_BACK_RADIUS == 8
    assert chrome._ctx_icon.width() == _NM_CHROME_ICON_SIZE == 18
    # Theme toggle = `.tb-theme` canónico del titlebar (mockup línea 195):
    # botón glifo 24×24 r7, solo sol/luna 16px — NO la píldora label+dot de la
    # `.themetoggle` de la cáscara web (que el plan dice no replicar).
    assert chrome._btn_theme.width() == _NM_CHROME_THEME_TOGGLE_W == 24
    assert chrome._btn_theme.height() == _NM_CHROME_THEME_TOGGLE_H == 24
    assert _NM_CHROME_THEME_TOGGLE_RADIUS == 7
    assert _NM_CHROME_THEME_ICON_SIZE == 16

    assert chrome._win_controls.layout().spacing() == _NM_CHROME_WIN_DOT_GAP == 8
    assert chrome._btn_min.width() == _NM_CHROME_WIN_DOT_SIZE == 13
    assert chrome._btn_max.width() == 13
    assert chrome._btn_close.width() == 13
    assert _NM_CHROME_WIN_DOT_OPACITY == 0.55
    # Semáforo del mockup `.tb-dots`: verde, amarillo, rojo (izq→der). Los dots se
    # añaden en orden min→max→close, así que min=verde, max=amarillo, close=rojo.
    assert _NM_CHROME_WIN_DOT_COLORS == {
        "min": "#56B27A",
        "max": "#E0B23E",
        "close": "#E0695A",
    }

    chrome_source = __import__("inspect").getsource(NMWindowChrome.paintEvent)
    assert 'v3c("chrome", self._modo)' in chrome_source
    assert 'v3c("chromeLine", self._modo)' in chrome_source

    btn_source = __import__("inspect").getsource(_ChromeWinBtn.paintEvent)
    assert "_NM_CHROME_WIN_DOT_COLORS" in btn_source
    assert "_NM_CHROME_WIN_DOT_OPACITY" in btn_source

    toggle_source = __import__("inspect").getsource(_ChromeThemeToggle.paintEvent)
    # Glifo solo: fondo surface-3 únicamente en hover, icono faint→ink; sin
    # píldora (dot/knob). Mockup `.tb-theme` / `.tb-theme:hover`.
    assert 'v3c("surface3", self._modo)' in toggle_source
    assert 'icon_name = "sun" if is_dark else "moon"' in toggle_source
    assert 'v3c("ink" if hovered else "faint", self._modo)' in toggle_source
    assert "knob_x" not in toggle_source


def test_patient_row_premium_matches_mockup_prow_contract(qtbot) -> None:
    from shared.components.patient import (
        NMAreaSparkline,
        NMPatientRowPremium,
        NMSparkline,
        _NM_AREA_SPARK_DOT_MAX_POINTS,
        _NM_AREA_SPARK_DOT_RADIUS,
        _NM_AREA_SPARK_GRID_VALUES,
        _NM_AREA_SPARK_MAX_H,
        _NM_AREA_SPARK_MIN_H,
        _NM_AREA_SPARK_STROKE_W,
        _NM_PATIENT_AVATAR_RADIUS,
        _NM_PATIENT_AVATAR_SIZE,
        _NM_PATIENT_RING_COL_W,
        _NM_PATIENT_RING_SIZE,
        _NM_PATIENT_ROW_GAP,
        _NM_PATIENT_ROW_HEIGHT,
        _NM_PATIENT_SPARKLINE_H,
        _NM_PATIENT_SPARKLINE_W,
        _NM_PATIENT_TREND_COL_W,
        _NM_PATIENT_UNLINK_SIZE,
    )

    spark = NMSparkline([5, 6, 7], modo="light_hybrid")
    qtbot.addWidget(spark)
    assert spark.width() == _NM_PATIENT_SPARKLINE_W == 78
    assert spark.height() == _NM_PATIENT_SPARKLINE_H == 30

    area = NMAreaSparkline(
        [2, 4, 5, 7, 6, 8, 9],
        labels=["L", "M", "M", "J", "V", "S", "D"],
        modo="light_hybrid",
    )
    qtbot.addWidget(area)
    assert area.minimumHeight() == _NM_AREA_SPARK_MIN_H == 74
    assert area.maximumHeight() == _NM_AREA_SPARK_MAX_H == 82
    assert _NM_AREA_SPARK_GRID_VALUES == (0, 5, 10)
    assert _NM_AREA_SPARK_STROKE_W == 2.0
    assert _NM_AREA_SPARK_DOT_RADIUS == 3.0
    assert _NM_AREA_SPARK_DOT_MAX_POINTS == 7

    row = NMPatientRowPremium(
        "Ana Martinez",
        subtitle="ana@example.com",
        mood_data=[5, 6, 6, 7, 8, 7, 9],
        pct=0.75,
        modo="light_hybrid",
        on_unlink=lambda: None,
    )
    qtbot.addWidget(row)

    assert row.height() == _NM_PATIENT_ROW_HEIGHT == 70
    assert row.layout().spacing() == _NM_PATIENT_ROW_GAP == 14
    assert row._avatar.width() == _NM_PATIENT_AVATAR_SIZE == 40
    assert row._avatar.height() == _NM_PATIENT_AVATAR_SIZE
    assert f"border-radius: {_NM_PATIENT_AVATAR_RADIUS}px" in row._avatar.styleSheet()
    assert row._sparkline.width() == 78
    assert row._sparkline.height() == 30
    assert row._ring.width() == _NM_PATIENT_RING_SIZE == 46
    assert row._ring._color_key == "gold"
    assert row._btn_unlink.width() == _NM_PATIENT_UNLINK_SIZE == 30
    assert _NM_PATIENT_TREND_COL_W == 90
    assert _NM_PATIENT_RING_COL_W == 60

    source = __import__("inspect").getsource(NMPatientRowPremium._apply_theme)
    assert 'v3c("surface2", self._modo).name()' in source

    area_source = __import__("inspect").getsource(NMAreaSparkline.paintEvent)
    assert "for value in _NM_AREA_SPARK_GRID_VALUES" in area_source
    assert "min(10.0, max(0.0, float(v)))" in area_source
    assert 'v3c("moodGradFrom", self._modo)' in area_source
    assert 'v3c("moodGradMid", self._modo)' in area_source
    assert 'v3c("moodGradTo", self._modo)' in area_source
    assert "draw_dots = n <= _NM_AREA_SPARK_DOT_MAX_POINTS" in area_source


def test_dbt_cards_match_mockup_family_bar_contract(qtbot) -> None:
    from app.modules.dbt_qt import (
        _DBT_FAMILY_COLOR_KEYS,
        _DBT_NEED_BORDER_W,
        _DBT_SKILL_BAR_TOP_H,
        _DBT_SKILL_BAR_TOP_W,
        _NeedCard,
        _SkillCard,
        _dbt_family_soft_css,
    )

    need = _NeedCard(
        "Volver al presente",
        "Pausar, enfocar y notar el aqui y ahora.",
        "mindfulness",
        "mind",
        modo="light_hybrid",
    )
    qtbot.addWidget(need)
    assert need.layout().contentsMargins().left() == 20
    assert need._family_color_key == "mind"
    assert _DBT_NEED_BORDER_W == 5

    skill = _SkillCard(
        {
            "family": "distress_tolerance",
            "title": "STOP",
            "summary": "Pausa guiada para atravesar un momento intenso.",
            "duration_min": 2,
        },
        modo="light_hybrid",
    )
    qtbot.addWidget(skill)
    # Mockup `.dbt-card` = `.card.pad` (20px) con barra HORIZONTAL superior 64×7.
    assert skill.layout().contentsMargins().left() == 20
    assert skill._family_color_key == "toler"
    assert _DBT_SKILL_BAR_TOP_W == 64
    assert _DBT_SKILL_BAR_TOP_H == 7
    assert _DBT_FAMILY_COLOR_KEYS == {
        "mindfulness": "mind",
        "distress_tolerance": "toler",
        "emotion_regulation": "regul",
        "interpersonal_effectiveness": "efect",
    }
    assert _dbt_family_soft_css("emotion_regulation", "light_hybrid").startswith("rgba(")

    need_source = __import__("inspect").getsource(_NeedCard.paintEvent)
    assert "_DBT_NEED_BORDER_W" in need_source
    assert "v3c(self._family_color_key, self._modo)" in need_source

    skill_source = __import__("inspect").getsource(_SkillCard.paintEvent)
    assert "_DBT_SKILL_BAR_TOP_W" in skill_source
    assert "_DBT_SKILL_BAR_TOP_H" in skill_source
    assert "v3c(self._family_color_key, self._modo)" in skill_source
