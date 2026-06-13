"""Paridad de tokens: shared/theme.py (fuente de verdad Qt) vs
shared/design_tokens.py (espejo canónico que leen los agentes).

Gate del plan "Índigo Calmado" (F4): el espejo divergió silenciosamente más
de una vez (p.ej. ink_secondary). Este test convierte la regla documental
"el espejo sigue a theme" en verificación automática para las claves
canónicas de paleta. Si cambiás la paleta, cambiá AMBOS archivos.
"""

from shared import design_tokens as dt
from shared import theme


# (clave en design_tokens, clave en theme.V3_*)
_CANONICAL_PAIRS = [
    ("bg_canvas", "bg"),
    ("bg_sidebar", "bgSidebar"),
    ("bg_surface2", "surface2"),
    ("primary", "primary"),
    ("accent", "accent"),
    ("teal", "teal"),
    ("amber", "amber"),
    ("ink_primary", "text"),
]

_ADN_LIGHT = {
    "bg_canvas": "#F4EFE5",
    "bg_sidebar": "#ECE5D4",
    "bg_surface": "#FBF8F1",
    "primary": "#305A48",
    "accent": "#B8633B",
    "teal": "#2F7E73",
    "amber": "#C68A2E",
    "ink_primary": "#1C2218",
}

_ADN_DARK = {
    "bg_canvas": "#07091A",
    "bg_sidebar": "#0E132B",
    "bg_surface": "#141A38",
    "primary": "#A99CFF",
    "accent": "#5EE0C7",
    "teal": "#5EE0C7",
    "green": "#60B89A",
    "amber": "#E8B86A",
    "ink_primary": "#ECECFB",
}

_ADN_SPACING = {
    "xs": 4,
    "sm": 6,
    "md": 10,
    "lg": 14,
    "xl": 16,
    "2xl": 20,
    "3xl": 24,
    "4xl": 32,
}

_ADN_RADIUS = {
    "sm": 8,
    "md": 12,
    "lg": 16,
    "card": 16,
    "xxl": 22,
    "pill": 999,
}


def test_paridad_dark():
    for dt_key, th_key in _CANONICAL_PAIRS:
        assert dt.DARK[dt_key].lower() == theme.V3_DARK[th_key].lower(), (
            f"DARK divergente: design_tokens[{dt_key!r}]={dt.DARK[dt_key]} "
            f"!= theme.V3_DARK[{th_key!r}]={theme.V3_DARK[th_key]}"
        )


def test_paridad_light():
    for dt_key, th_key in _CANONICAL_PAIRS:
        assert dt.LIGHT[dt_key].lower() == theme.V3_LIGHT[th_key].lower(), (
            f"LIGHT divergente: design_tokens[{dt_key!r}]={dt.LIGHT[dt_key]} "
            f"!= theme.V3_LIGHT[{th_key!r}]={theme.V3_LIGHT[th_key]}"
        )


def test_paridad_textmuted_dark():
    # Divergencia histórica puntual (ink_secondary vs textMuted) — cerrada en F4.
    assert dt.DARK["ink_secondary"].lower() == theme.V3_DARK["textMuted"].lower()


def test_adn_light_exact_values():
    for key, value in _ADN_LIGHT.items():
        assert dt.LIGHT[key].lower() == value.lower()


def test_adn_dark_exact_values():
    for key, value in _ADN_DARK.items():
        assert dt.DARK[key].lower() == value.lower()


def test_adn_spacing_exact_values():
    for key, value in _ADN_SPACING.items():
        assert dt.SPACING[key] == value
        assert theme.V3_SPACE[key] == value


def test_adn_radius_exact_values():
    for key, value in _ADN_RADIUS.items():
        assert dt.RADIUS[key] == value
        assert theme.V3_RADIUS[key] == value


def test_adn_layout_radius_aliases():
    assert dt.LAYOUT["radius_card"] == 16
    assert dt.LAYOUT["radius_modal"] == 22
    assert dt.LAYOUT["radius_button"] == 999
    assert theme.LAYOUT["radius_card"] == 16
    assert theme.LAYOUT["radius_modal"] == 22
    assert theme.LAYOUT["radius_button"] == 999
