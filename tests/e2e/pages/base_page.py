from __future__ import annotations

from pathlib import Path

from tests.e2e._helpers.qt_helpers import (
    click_button_by_text,
    drain,
    find_button,
    find_input,
    find_label,
    find_widget_by_class,
    grab_screenshot,
    latest_toast,
    latest_toast_variant,
)


class BasePage:
    def __init__(self, qapp, qtbot, request=None):
        self.qapp = qapp
        self.qtbot = qtbot
        self.request = request
        self.window = None
        self._screenshots: list[Path] = []

    def close(self):
        if self.window is not None:
            self.window.close()
            self.drain()

    def drain(self, cycles: int = 8):
        drain(self.qapp, cycles=cycles)

    def find_button(self, text=None, contains=None, parent=None):
        return find_button(parent or self.window, text=text, contains=contains)

    def find_input(self, placeholder=None, contains=None, parent=None):
        return find_input(parent or self.window, placeholder=placeholder, contains=contains)

    def find_label(self, text=None, contains=None, parent=None):
        return find_label(parent or self.window, text=text, contains=contains)

    def find_widget(self, class_name, nth: int = 0, parent=None):
        return find_widget_by_class(parent or self.window, class_name, nth=nth)

    def latest_toast(self):
        return latest_toast(self.window)

    def latest_toast_variant(self):
        return latest_toast_variant(self.window)

    def click_button(self, text=None, contains=None, cycles: int = 6):
        return click_button_by_text(self.window, self.qapp, text=text, contains=contains, cycles=cycles)

    def grab_screenshot(self, name: str | None = None):
        if self.request is not None:
            base = Path("reports/e2e/screenshots") / self.request.node.name
        else:
            base = Path("reports/e2e/screenshots/manual")
        path = base / (name or "screenshot.png")
        saved = grab_screenshot(self.window, path)
        self._register_screenshot(saved)
        return saved

    def _register_screenshot(self, path):
        path = Path(path)
        self._screenshots.append(path)
        if self.request is not None:
            existing = getattr(self.request.node, "_e2e_screenshots", [])
            existing.append(path)
            setattr(self.request.node, "_e2e_screenshots", existing)
        return path
