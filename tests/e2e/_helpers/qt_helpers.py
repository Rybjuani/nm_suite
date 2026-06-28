from __future__ import annotations

from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QDialog,
    QLabel,
    QLineEdit,
    QTextEdit,
    QWidget,
)


def _is_alive(widget) -> bool:
    return widget is not None and not sip.isdeleted(widget)


def _text_of(widget) -> str:
    if hasattr(widget, "text"):
        try:
            return str(widget.text())
        except TypeError:
            pass
    if hasattr(widget, "toPlainText"):
        return str(widget.toPlainText())
    return ""


def _matches(value: str, text: str | None = None, contains: str | None = None) -> bool:
    value = value or ""
    if text is not None and value != text:
        return False
    if contains is not None and contains.lower() not in value.lower():
        return False
    return True


def drain(qapp, cycles: int = 8):
    app = qapp or QApplication.instance()
    for _ in range(cycles):
        if app is not None:
            app.processEvents()
        QTest.qWait(1)


def find_buttons(parent, text: str | None = None, contains: str | None = None):
    buttons = []
    for btn in parent.findChildren(QAbstractButton):
        if not _is_alive(btn):
            continue
        label = _text_of(btn) or btn.accessibleName() or btn.toolTip()
        if _matches(label, text=text, contains=contains):
            buttons.append(btn)
    return buttons


def find_button(parent, text: str | None = None, contains: str | None = None):
    buttons = find_buttons(parent, text=text, contains=contains)
    if not buttons:
        raise AssertionError(f"Button not found text={text!r} contains={contains!r}")
    return buttons[0]


def find_input(parent, placeholder: str | None = None, contains: str | None = None):
    widgets = parent.findChildren(QLineEdit) + parent.findChildren(QTextEdit)
    for widget in widgets:
        if not _is_alive(widget):
            continue
        values = [
            getattr(widget, "placeholderText", lambda: "")(),
            widget.accessibleName(),
            _text_of(widget),
        ]
        if any(_matches(value, text=placeholder, contains=contains) for value in values):
            return widget
    raise AssertionError(f"Input not found placeholder={placeholder!r} contains={contains!r}")


def find_widgets_by_class(parent, class_name: str):
    return [
        widget
        for widget in parent.findChildren(QWidget)
        if _is_alive(widget) and widget.__class__.__name__ == class_name
    ]


def find_widget_by_class(parent, class_name: str, nth: int = 0):
    widgets = find_widgets_by_class(parent, class_name)
    if nth >= len(widgets):
        raise AssertionError(f"Widget class {class_name!r} nth={nth} not found; count={len(widgets)}")
    return widgets[nth]


def find_label(parent, text: str | None = None, contains: str | None = None):
    for label in parent.findChildren(QLabel):
        if not _is_alive(label):
            continue
        if _matches(label.text(), text=text, contains=contains):
            return label
    raise AssertionError(f"Label not found text={text!r} contains={contains!r}")


def _toast_widgets(parent_window):
    return [
        widget
        for widget in parent_window.findChildren(QWidget)
        if _is_alive(widget) and widget.__class__.__name__ == "NMToast"
    ]


def latest_toast(parent_window):
    toasts = _toast_widgets(parent_window)
    if not toasts:
        return ""
    return toasts[-1].accessibleName()


def latest_toast_variant(parent_window):
    toast = latest_toast(parent_window)
    if not toast.startswith("NMToast "):
        return ""
    return toast.split(":", 1)[0].replace("NMToast ", "").strip()


def open_dialog(parent_window):
    dialogs = [
        widget
        for widget in QApplication.topLevelWidgets()
        if _is_alive(widget)
        and widget is not parent_window
        and (isinstance(widget, QDialog) or widget.__class__.__name__.startswith("NMDialog"))
        and widget.isVisible()
    ]
    if not dialogs:
        dialogs = [
            widget
            for widget in parent_window.findChildren(QWidget)
            if _is_alive(widget) and widget.__class__.__name__.startswith("NMDialog") and widget.isVisible()
        ]
    if not dialogs:
        raise AssertionError("No open dialog found")
    return dialogs[-1]


def click_button_by_text(parent, qapp, text: str | None = None, contains: str | None = None, cycles: int = 6):
    button = find_button(parent, text=text, contains=contains)
    button.click()
    drain(qapp, cycles=cycles)
    return button


def set_input_text(widget, text: str, qapp, cycles: int = 4):
    if isinstance(widget, QTextEdit):
        widget.setPlainText(text)
    else:
        widget.clear()
        widget.setText(text)
    drain(qapp, cycles=cycles)
    return widget


def dialog_footer_buttons(dialog):
    buttons = dialog.findChildren(QAbstractButton)
    if not buttons:
        return []
    bottom = max(btn.geometry().center().y() for btn in buttons if _is_alive(btn))
    return [btn for btn in buttons if _is_alive(btn) and btn.geometry().center().y() >= bottom - 48]


def grab_screenshot(widget, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pixmap = widget.grab()
    if not pixmap.save(str(target), "PNG"):
        raise AssertionError(f"Could not save screenshot to {target}")
    return target
