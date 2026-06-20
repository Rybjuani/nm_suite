from __future__ import annotations


def test_button_primitive_uses_mockup_control_height() -> None:
    from shared.components.buttons import _NM_CONTROL_COMPACT_HEIGHT, _NM_CONTROL_HEIGHT

    assert _NM_CONTROL_HEIGHT == 42
    assert _NM_CONTROL_COMPACT_HEIGHT == 34


def test_badge_primitive_supports_mockup_tones(qtbot) -> None:
    from shared.components.surfaces import NMBadge

    badge = NMBadge("Estado", tone="gold", modo="light_hybrid")
    qtbot.addWidget(badge)

    qss = badge.styleSheet()
    assert "color: #C2912F" in qss
    assert "background-color: rgba(194,145,47,0.16)" in qss
    assert "border-radius: 11px" in qss
    assert "padding: 4px 11px" in qss


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


def test_patient_row_premium_matches_mockup_prow_contract(qtbot) -> None:
    from shared.components.patient import (
        NMPatientRowPremium,
        NMSparkline,
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
