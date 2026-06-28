from __future__ import annotations

import pytest

from tests.e2e.pages.suite.respiracion_page import RespiracionPage


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


def test_respiracion_presets_3_5_10(qapp, qtbot, request, visual_qa_env):
    page = RespiracionPage(qapp, qtbot, request=request).open()
    try:
        for minutes in (3, 5, 10):
            page.select_preset(minutes).expect_duration(minutes)
    finally:
        page.close()
