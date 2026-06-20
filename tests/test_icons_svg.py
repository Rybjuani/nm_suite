from __future__ import annotations


def test_mockup_icon_set_is_available_and_exact() -> None:
    from shared.icons_svg import ICON_BODIES, MOCKUP_ICON_BODIES

    required = {
        "home",
        "mood",
        "breath",
        "brain",
        "activity",
        "bell",
        "check",
        "timer",
        "spark",
        "users",
        "user",
        "text",
        "key",
        "shield",
        "smile",
        "flower",
        "doc",
        "sun",
        "moon",
        "arrow",
    }

    assert required == set(MOCKUP_ICON_BODIES)
    for name in required:
        assert ICON_BODIES[name] == MOCKUP_ICON_BODIES[name]


def test_mockup_icons_render_to_pixmap(qtbot) -> None:
    from shared.icons_svg import MOCKUP_ICON_BODIES, nm_svg_pixmap

    for name in MOCKUP_ICON_BODIES:
        pixmap = nm_svg_pixmap(name, color="#2E5D43", size=24)
        assert pixmap is not None
        assert not pixmap.isNull()
