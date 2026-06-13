


from shared.fonts import (
    FONT_MONO,
    FONT_SANS,
    FONT_SERIF,
    _fonts_dirs,
    available_families,
    font_summary,
    load_fonts,
)


class TestConstantesFonts:
    def test_fallbacks_definidos(self):
        assert isinstance(FONT_SERIF, str)
        assert isinstance(FONT_SANS, str)
        assert isinstance(FONT_MONO, str)
        assert len(FONT_SERIF) > 0
        assert len(FONT_SANS) > 0
        assert len(FONT_MONO) > 0


class TestLoadFonts:
    def test_no_explota_sin_qapplication(self):
        result = load_fonts()
        assert isinstance(result, dict)
        assert "serif" in result
        assert "sans" in result
        assert "mono" in result

    def test_idempotente(self):
        r1 = load_fonts()
        r2 = load_fonts()
        assert r1 == r2


class TestFontSummary:
    def test_devuelve_string_no_vacio(self):
        result = font_summary()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contiene_nombres_familias(self):
        result = font_summary()
        assert "sans" in result.lower() or "serif" in result.lower()


class TestAvailableFamilies:
    def test_devuelve_lista(self):
        result = available_families()
        assert isinstance(result, list)

    def test_no_explota(self):
        available_families()


class TestFontsDirs:
    def test_devuelve_lista_no_vacia(self):
        dirs = _fonts_dirs()
        assert isinstance(dirs, list)
        assert len(dirs) > 0

    def test_todas_son_strings(self):
        dirs = _fonts_dirs()
        for d in dirs:
            assert isinstance(d, str)
