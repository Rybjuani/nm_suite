from __future__ import annotations

import pytest

from tests.e2e.pages.suite.onboarding_page import OnboardingPage, patch_supabase


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_suite]


@pytest.fixture
def onboarding_page(qapp, qtbot, monkeypatch, tmp_path, sb, request):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    patch_supabase(sb, monkeypatch)
    page = OnboardingPage(qapp, qtbot, request=request).open()
    try:
        yield page
    finally:
        page.close()


def test_signup_exitoso(onboarding_page, sb):
    (
        onboarding_page.fill_name("Ana")
        .fill_email("ana@example.com")
        .fill_password("password123")
        .accept_consent()
        .click_signup()
        .expect_accepted()
    )

    assert sb.auth.signups == [{"email": "ana@example.com", "password": "password123"}]
    assert sb.table("patients").select("*").eq("email", "ana@example.com").single().execute().data[
        "patient_name"
    ] == "Ana"


def test_login_exitoso(onboarding_page, sb):
    sb.auth.seed_user("ana@example.com", "password123", user_id="user-login")

    (
        onboarding_page.fill_name("Ana")
        .fill_email("ana@example.com")
        .fill_password("password123")
        .accept_consent()
        .click_login()
        .expect_accepted()
    )

    assert sb.auth.signins == [{"email": "ana@example.com", "password": "password123"}]
    assert sb.table("patients").select("*").eq("patient_id", "user-login").single().execute().data[
        "patient_name"
    ] == "Ana"


def test_email_duplicado_muestra_error(onboarding_page, sb):
    sb.auth.seed_user("ana@example.com", "password123")

    (
        onboarding_page.fill_name("Ana")
        .fill_email("ana@example.com")
        .fill_password("password123")
        .accept_consent()
        .click_signup()
        .expect_error_label_contains("User already registered")
    )

    assert not onboarding_page.accepted


def test_password_corta_muestra_error(onboarding_page):
    (
        onboarding_page.fill_name("Ana")
        .fill_email("ana@example.com")
        .fill_password("123")
        .accept_consent()
        .click_signup()
        .expect_error_label_contains("contrase")
    )

    assert not onboarding_page.accepted


def test_email_invalido(onboarding_page):
    (
        onboarding_page.fill_name("Ana")
        .fill_email("ana-invalid")
        .fill_password("password123")
        .accept_consent()
        .click_signup()
        .expect_email_error()
        .expect_error_label_contains("email")
    )


def test_nombre_vacio(onboarding_page):
    (
        onboarding_page.fill_name("")
        .fill_email("ana@example.com")
        .fill_password("password123")
        .accept_consent()
        .click_signup()
        .expect_name_error()
        .expect_error_label_contains("nombre")
    )


def test_sin_consent_deshabilita_boton(onboarding_page):
    onboarding_page.fill_name("Ana").fill_email("ana@example.com").fill_password("password123")

    onboarding_page.expect_signup_button_enabled(False).expect_login_button_enabled(False)


def test_recuperar_acceso_exitoso(onboarding_page, sb):
    onboarding_page.fill_email("ana@example.com").click_recover().expect_error_label_contains("enlace")

    assert sb.auth.recoveries == ["ana@example.com"]


def test_recuperar_acceso_email_vacio(onboarding_page, sb):
    onboarding_page.fill_email("").click_recover().expect_error_label_contains("email")

    assert sb.auth.recoveries == []
