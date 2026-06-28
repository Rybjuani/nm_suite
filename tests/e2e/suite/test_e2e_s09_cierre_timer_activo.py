from __future__ import annotations

from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QMessageBox


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


class _Event:
    def __init__(self):
        self.accepted = False
        self.ignored = False

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


class _App:
    def __init__(self):
        self.quit_called = False

    def processEvents(self):
        return None

    def quit(self):
        self.quit_called = True


def _stub(timer_running=False, visual_qa=False, really_quit=False):
    return SimpleNamespace(
        _current_module=SimpleNamespace(_running=timer_running),
        _visual_qa=visual_qa,
        _really_quit=really_quit,
    )


def _patch_close_deps(monkeypatch):
    import app.main_qt as main_qt

    app = _App()
    detener_calls = []
    monkeypatch.setattr(main_qt.avisos_daemon, "detener", lambda: detener_calls.append(True))
    monkeypatch.setattr(main_qt.QApplication, "instance", lambda: app)
    return main_qt, app, detener_calls


def test_usuario_dice_si_cierra(monkeypatch):
    main_qt, app, detener_calls = _patch_close_deps(monkeypatch)
    monkeypatch.setattr(main_qt.QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    event = _Event()

    main_qt.NeuroMoodApp._on_close(_stub(timer_running=True), event)

    assert event.accepted
    assert app.quit_called
    assert detener_calls


def test_usuario_dice_no_no_cierra(monkeypatch):
    main_qt, app, detener_calls = _patch_close_deps(monkeypatch)
    monkeypatch.setattr(main_qt.QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.No)
    event = _Event()

    main_qt.NeuroMoodApp._on_close(_stub(timer_running=True), event)

    assert event.ignored
    assert not event.accepted
    assert not app.quit_called
    assert detener_calls == []


def test_sin_timer_activo_cierra_sin_preguntar(monkeypatch):
    main_qt, app, detener_calls = _patch_close_deps(monkeypatch)
    asked = []
    monkeypatch.setattr(main_qt.QMessageBox, "question", lambda *args, **kwargs: asked.append(True))
    event = _Event()

    main_qt.NeuroMoodApp._on_close(_stub(timer_running=False), event)

    assert event.accepted
    assert app.quit_called
    assert asked == []
    assert detener_calls


def test_modo_visual_qa_skipea_dialogo(monkeypatch):
    main_qt, app, detener_calls = _patch_close_deps(monkeypatch)
    asked = []
    monkeypatch.setattr(main_qt.QMessageBox, "question", lambda *args, **kwargs: asked.append(True))
    event = _Event()

    main_qt.NeuroMoodApp._on_close(_stub(timer_running=True, visual_qa=True), event)

    assert event.accepted
    assert app.quit_called
    assert asked == []
    assert detener_calls


def test_force_close_env_skipea_dialogo(monkeypatch):
    main_qt, app, detener_calls = _patch_close_deps(monkeypatch)
    monkeypatch.setenv("NM_TEST_FORCE_CLOSE", "1")
    asked = []
    monkeypatch.setattr(main_qt.QMessageBox, "question", lambda *args, **kwargs: asked.append(True))
    event = _Event()

    main_qt.NeuroMoodApp._on_close(_stub(timer_running=True), event)

    assert event.accepted
    assert app.quit_called
    assert asked == []
    assert detener_calls
