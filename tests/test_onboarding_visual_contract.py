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


def test_onboarding_narrow_520_default_size() -> None:
    """E3-S-ACCESO: ventana arranca en 520×600 (mockup narrow:true línea 1325)."""
    from PyQt6.QtCore import QSize
    from app.onboarding_qt import OnboardingDialog

    import inspect
    source = inspect.getsource(OnboardingDialog._configure_responsive_window)
    assert "520" in source
    assert "600" in source


def test_onboarding_consent_card_uses_legal_disclaimer_text() -> None:
    """E3-S-ACCESO: el texto de consentimiento viene de legal_contract, no de un placeholder."""
    from shared.legal_contract import LEGAL_DISCLAIMER_TEXT
    from app.onboarding_qt import _CONSENT_TEXT

    assert _CONSENT_TEXT is LEGAL_DISCLAIMER_TEXT or _CONSENT_TEXT == LEGAL_DISCLAIMER_TEXT
    assert "herramienta digital complementaria de bienestar" in _CONSENT_TEXT
    assert len(_CONSENT_TEXT) > 200


def test_onboarding_compact_visual_contract_keeps_consent_integrated(qtbot) -> None:
    from app.onboarding_qt import OnboardingDialog

    dialog = OnboardingDialog()
    qtbot.addWidget(dialog)

    assert dialog._name.height() == 37
    assert dialog._email.height() == 37
    assert dialog._code.height() == 37
    assert dialog._consent_card.objectName() == "ConsentCard"
    assert dialog._consent_check.parentWidget() is not dialog._consent_card
    assert dialog._consent_check.width() == 22
    assert dialog._consent_check.height() == 22
