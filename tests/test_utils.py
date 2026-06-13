
import re

from shared.utils import (
    color_por_puntaje,
    color_por_puntaje_exacto,
    fecha_hoy,
    fecha_legible,
    get_weekly_series,
    hora_actual,
)


class TestFechaHoy:
    def test_formato_iso(self):
        result = fecha_hoy()
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result), f"Formato inesperado: {result}"

    def test_no_explota(self):
        result = fecha_hoy()
        assert isinstance(result, str)
        assert len(result) == 10


class TestHoraActual:
    def test_formato_hora(self):
        result = hora_actual()
        assert re.match(r"^\d{2}:\d{2}:\d{2}$", result), f"Formato inesperado: {result}"

    def test_no_explota(self):
        result = hora_actual()
        assert isinstance(result, str)
        assert 8 <= len(result) <= 8


class TestFechaLegible:
    def test_fecha_valida(self):
        result = fecha_legible("2026-05-27")
        assert isinstance(result, str)
        assert "27" in result
        assert any(m in result for m in ("mayo", "Mayo")) or len(result) > 0

    def test_fecha_invalida(self):
        result = fecha_legible("no-es-fecha")
        assert result == "no-es-fecha"

    def test_fecha_vacia(self):
        result = fecha_legible("")
        assert result == ""


class TestColorPorPuntajeExacto:
    def test_rango_valido_0_10(self):
        for p in range(11):
            color = color_por_puntaje_exacto(p)
            assert color.startswith("#"), f"Puntaje {p} devolvio {color}"

    def test_clamp_bajo(self):
        assert color_por_puntaje_exacto(-1) == color_por_puntaje_exacto(0)

    def test_clamp_alto(self):
        assert color_por_puntaje_exacto(11) == color_por_puntaje_exacto(10)

    def test_puntaje_1_no_es_igual_a_10(self):
        assert color_por_puntaje_exacto(1) != color_por_puntaje_exacto(10)


class TestColorPorPuntaje:
    def test_delega_en_exacto_dark(self):
        assert color_por_puntaje(5, "dark") == color_por_puntaje_exacto(5)

    def test_delega_en_exacto_light(self):
        assert color_por_puntaje(5, "light") == color_por_puntaje_exacto(5)

    def test_default_mode(self):
        assert color_por_puntaje(5) == color_por_puntaje_exacto(5)


class TestGetWeeklySeries:
    def test_devuelve_tuplas_de_7(self):
        current, previous = get_weekly_series()
        assert len(current) == 7
        assert len(previous) == 7

    def test_elementos_son_float_o_none(self):
        current, previous = get_weekly_series()
        for v in current:
            assert v is None or isinstance(v, float)
        for v in previous:
            assert v is None or isinstance(v, float)
