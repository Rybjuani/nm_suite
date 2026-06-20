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
