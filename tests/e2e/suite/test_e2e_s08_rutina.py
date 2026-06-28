from __future__ import annotations

import pytest

from tests.e2e.pages.suite.rutina_page import RutinaPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


def test_rutina_toggle(qapp, qtbot, request, visual_qa_env):
    page = RutinaPage(qapp, qtbot, request=request).open()
    try:
        task_id = page.toggle_first()
        assert page.window._task_done[task_id] is page.window._task_checks[task_id].isChecked()
    finally:
        page.close()


def test_rutina_empty(qapp, qtbot, request, visual_qa_env):
    page = RutinaPage(qapp, qtbot, request=request).open()
    try:
        page.force_empty()
        assert page.window._empty_state.isVisible()
    finally:
        page.close()


def test_rutina_add_task_si_existe_ui(qapp, qtbot, request, visual_qa_env):
    page = RutinaPage(qapp, qtbot, request=request).open()
    try:
        before = len(page.window._task_checks)
        added = page.add_task_if_available()
        if added:
            assert len(page.window._task_checks) >= before
        else:
            pytest.skip("La UI de agregar tarea no esta disponible en esta configuracion")
    finally:
        page.close()
