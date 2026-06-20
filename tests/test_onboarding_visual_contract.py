from __future__ import annotations


def test_onboarding_actions_are_disabled_until_terms_are_accepted(qtbot) -> None:
    from app.onboarding_qt import OnboardingDialog

    dialog = OnboardingDialog()
    qtbot.addWidget(dialog)

    assert not dialog._btn_signup.isEnabled()
    assert not dialog._btn_ok.isEnabled()

    dialog._consent_check.setChecked(True)
    assert dialog._btn_signup.isEnabled()
    assert dialog._btn_ok.isEnabled()

    dialog._consent_check.setChecked(False)
    assert not dialog._btn_signup.isEnabled()
    assert not dialog._btn_ok.isEnabled()


def test_onboarding_name_error_copy_matches_mockup(qtbot) -> None:
    from app.onboarding_qt import OnboardingDialog

    dialog = OnboardingDialog()
    qtbot.addWidget(dialog)
    dialog._consent_check.setChecked(True)

    dialog._on_accept("signup")

    # Mockup onboarding error línea 1315: "Completá tu nombre para crear la cuenta."
    assert dialog._error_lbl.text() == "Completá tu nombre para crear la cuenta."
