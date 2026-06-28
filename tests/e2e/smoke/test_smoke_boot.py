from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.smoke]


ROOT = Path(__file__).resolve().parents[3]


def _smoke(path: str):
    env = os.environ.copy()
    env.update(
        {
            "NM_QA_SMOKE": "1",
            "NM_VISUAL_QA": "1",
            "NM_TEST_FORCE_CLOSE": "1",
            "QT_QPA_PLATFORM": "offscreen",
        }
    )
    proc = subprocess.run(
        [sys.executable, path],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr


def test_smoke_01_suite_arranca():
    _smoke("app/main_qt.py")


def test_smoke_02_hub_arranca():
    _smoke("hub/main_qt.py")
