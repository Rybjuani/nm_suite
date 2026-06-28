from __future__ import annotations

import pytest

from tests.e2e.pages.suite.tcc_page import TCCPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


@pytest.fixture
def page(qapp, qtbot, request, visual_qa_env):
    p = TCCPage(qapp, qtbot, request=request).open()
    try:
        yield p
    finally:
        p.close()


def test_tcc_flujo_completo(page):
    (
        page.fill_situacion("Discusion breve en el trabajo")
        .next()
        .choose_emotion("Ansiedad")
        .set_intensity(7)
        .next()
        .fill_pensamiento("Seguro hice todo mal")
        .next()
        .fill_respuesta("Puedo revisar los hechos antes de concluir")
        .next()
    )

    assert page.window._success_page is not None
    assert page.window._stack.currentWidget() is page.window._success_page


def test_tcc_vacio_no_avanza(page):
    page.next()

    page.expect_step(0)
    page.expect_next_enabled(False)


def test_tcc_emocion_otro(page):
    (
        page.fill_situacion("Situacion con emocion no listada")
        .next()
        .choose_emotion("Otro", custom="Calma rara")
    )

    assert page.window._data["emocion"] == "Calma rara"
    page.expect_next_enabled(True)
