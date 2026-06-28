from __future__ import annotations

import pytest

from tests.e2e.pages.suite.actividades_page import ActividadesPage
from tests.e2e.pages.suite.animo_page import AnimoPage
from tests.e2e.pages.suite.avisos_page import AvisosPage
from tests.e2e.pages.suite.dbt_page import DBTPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


def test_modulo_animo_registra_estado(qapp, qtbot, request, visual_qa_env):
    page = AnimoPage(qapp, qtbot, request=request).open()
    try:
        page.set_level(8).expect_save_enabled(True).save()
        assert page.window._slider_touched is True
    finally:
        page.close()


def test_modulo_avisos_filtra_y_busca(qapp, qtbot, request, visual_qa_env):
    page = AvisosPage(qapp, qtbot, request=request).open()
    try:
        assert page.window._all_rows
        page.filter_active().search("Respir")
        assert page.window._current_filter == "activos"
        assert page.window._search_query == "respir"
    finally:
        page.close()


def test_modulo_actividades_filtra_y_marca(qapp, qtbot, request, visual_qa_env):
    page = ActividadesPage(qapp, qtbot, request=request).open()
    try:
        assert page.window._suggested_cards
        page.filter_category(1)
        assert page.window._current_filter
        if not page.window._suggested_cards:
            page.filter_category(0)
        completed = page.complete_first()
        assert completed
    finally:
        page.close()


def test_modulo_dbt_biblioteca_y_practica(qapp, qtbot, request, visual_qa_env):
    page = DBTPage(qapp, qtbot, request=request).open()
    try:
        page.open_library()
        assert page.window._view_stack.currentIndex() == 1
        page.start_first_skill()
        assert page.window._practice_view is not None
    finally:
        page.close()
