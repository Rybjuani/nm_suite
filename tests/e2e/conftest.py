from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from tests.e2e.fakes.ia_fake import FakeIAResponder
from tests.e2e.fakes.supabase_fake import FakeSupabase


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end UX test (real Qt UI, mocked external services)")
    config.addinivalue_line("markers", "e2e_suite: end-to-end test of the Suite (patient) app")
    config.addinivalue_line("markers", "e2e_hub: end-to-end test of the Hub (professional) app")
    config.addinivalue_line("markers", "e2e_visual: visual parity check against qa/_mockup_canonical")
    config.addinivalue_line("markers", "smoke: smoke test (subprocess, validates app boots)")


@pytest.fixture
def visual_qa_env(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    monkeypatch.setenv("NM_VISUAL_QA", "1")
    monkeypatch.setenv("NM_TEST_FORCE_CLOSE", "1")
    yield


@pytest.fixture
def clean_env(monkeypatch):
    for key in (
        "NM_VISUAL_QA",
        "NM_DEMO_VISUAL",
        "NM_QA_VISUAL",
        "NM_VISUAL_QA_DEMO",
        "NM_VISUAL_QA_NAME",
        "NM_VISUAL_QA_HUB_VIEW",
        "NM_QA_SMOKE",
        "NM_TEST_FORCE_CLOSE",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    yield


@pytest.fixture
def sb():
    return FakeSupabase()


@pytest.fixture
def ia_responder():
    return FakeIAResponder()


@pytest.fixture
def e2e_screenshot(request):
    def register(widget):
        setattr(request.node, "_e2e_screenshot_widget", widget)
        return widget

    return register


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    expected_xfail = bool(getattr(report, "wasxfail", None) and call.excinfo is not None)
    if report.when != "call" or not (report.failed or expected_xfail):
        return

    path = Path(str(getattr(item, "path", ""))).as_posix()
    if "tests/e2e/" not in path and not path.endswith("tests/e2e"):
        return

    try:
        from PyQt6 import sip
        from PyQt6.QtWidgets import QApplication

        widget = getattr(item, "_e2e_screenshot_widget", None)
        if widget is None:
            widget = QApplication.activeWindow()
        if widget is None or sip.isdeleted(widget):
            return

        out_dir = Path("reports/e2e/screenshots")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.nodeid)
        out_path = out_dir / f"{safe_name}.png"
        widget.grab().save(str(out_path), "PNG")
        existing = getattr(item, "_e2e_screenshots", [])
        existing.append(out_path)
        setattr(item, "_e2e_screenshots", existing)
    except Exception:
        return
