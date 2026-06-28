from __future__ import annotations

import sys
from types import ModuleType

from PyQt6.QtWidgets import QDialog

from tests.e2e._helpers.qt_helpers import set_input_text
from tests.e2e.pages.base_page import BasePage


def patch_supabase(sb, monkeypatch):
    import app.onboarding_qt as onboarding_qt

    module = sys.modules.get("supabase")
    if module is None:
        module = ModuleType("supabase")
        sys.modules["supabase"] = module
    monkeypatch.setattr(module, "create_client", lambda *_args, **_kwargs: sb, raising=False)
    monkeypatch.setattr(onboarding_qt, "supabase_url", lambda: "https://fake.supabase.local")
    monkeypatch.setattr(onboarding_qt, "supabase_key", lambda: "fake-key")
    return sb


class OnboardingPage(BasePage):
    def open(self):
        from app.onboarding_qt import OnboardingDialog

        self.window = OnboardingDialog()
        self.qtbot.addWidget(self.window)
        self.window.show()
        self.drain()
        return self

    @property
    def accepted(self) -> bool:
        return self.window.result() == QDialog.DialogCode.Accepted

    def fill_name(self, value: str):
        set_input_text(self.window._name, value, self.qapp)
        return self

    def fill_email(self, value: str):
        set_input_text(self.window._email, value, self.qapp)
        return self

    def fill_password(self, value: str):
        set_input_text(self.window._code, value, self.qapp)
        return self

    def accept_consent(self, checked: bool = True):
        self.window._consent_check.setChecked(checked)
        self.drain()
        return self

    def click_signup(self):
        self.window._btn_signup.click()
        self.drain()
        return self

    def click_login(self):
        self.window._btn_ok.click()
        self.drain()
        return self

    def click_recover(self):
        self.window._on_forgot_password()
        self.drain()
        return self

    def expect_error_label_contains(self, text: str):
        assert text.lower() in self.window._error_lbl.text().lower()
        return self

    def expect_name_error(self):
        assert getattr(self.window._name, "_error_message", "")
        return self

    def expect_email_error(self):
        assert getattr(self.window._email, "_error_message", "")
        return self

    def expect_signup_button_enabled(self, enabled: bool = True):
        assert self.window._btn_signup.isEnabled() is enabled
        return self

    def expect_login_button_enabled(self, enabled: bool = True):
        assert self.window._btn_ok.isEnabled() is enabled
        return self

    def expect_accepted(self):
        assert self.accepted
        return self


def user_count(sb) -> int:
    return len(sb.auth._users_by_email)
