from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QLabel


pytestmark = pytest.mark.e2e


@pytest.mark.xfail(strict=True, reason="verifica que el hook capture screenshots en fallos")
def test_auto_screenshot_se_captura_en_fallo(qtbot, e2e_screenshot):
    widget = QLabel("fallo esperado para screenshot")
    qtbot.addWidget(widget)
    widget.resize(240, 80)
    widget.show()
    e2e_screenshot(widget)

    assert False


def test_verifica_screenshot_capturado():
    shots = list(Path("reports/e2e/screenshots").glob("*test_auto_screenshot_se_captura_en_fallo*.png"))
    assert shots
    assert shots[-1].stat().st_size > 0
