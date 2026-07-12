from __future__ import annotations

import copy

import pytest

from qa import approval_verifier as av


KEY = "hub:detalle-resumen-ia-0@light"
REPORT_SHA = "a1b2c3d4e5f6" + "0" * 52
REPOSITORY = "Rybjuani/nm_suite"
OWNER = "Rybjuani"
ISSUE = 41
COMMENT_ID = 987654321
APPROVAL_URL = (
    f"https://github.com/{REPOSITORY}/issues/{ISSUE}#issuecomment-{COMMENT_ID}"
)


def _review(**changes) -> dict:
    value = {
        "approval_url": APPROVAL_URL,
        "comment_id": COMMENT_ID,
        "author": OWNER,
    }
    value.update(changes)
    return value


def _payload(**changes) -> dict:
    value = {
        "id": COMMENT_ID,
        "html_url": APPROVAL_URL,
        "issue_url": f"https://api.github.com/repos/{REPOSITORY}/issues/{ISSUE}",
        "user": {"login": OWNER},
        "body": f"Approved {KEY} for report {REPORT_SHA[:12]}",
    }
    value.update(changes)
    return value


def _verify(review=None, fetcher=None, **changes) -> dict[str, object]:
    arguments = {
        "key": KEY,
        "report_sha256": REPORT_SHA,
        "issue_number": ISSUE,
        "repository": REPOSITORY,
        "owner": OWNER,
        "token": "read-only-token",
        "fetcher": fetcher or (lambda _url, _headers, _timeout: _payload()),
    }
    arguments.update(changes)
    return av.verify_approval(review if review is not None else _review(), **arguments)


def test_valid_comment_is_fetched_and_normalized_for_closure_policy():
    calls = []

    def fetcher(url, headers, timeout):
        calls.append((url, headers, timeout))
        return _payload()

    review = _review()
    original = copy.deepcopy(review)
    result = _verify(review, fetcher)

    assert result == {
        "verified": True,
        "key": KEY,
        "report_sha256": REPORT_SHA,
        "approval_url": APPROVAL_URL,
        "comment_id": COMMENT_ID,
        "author": OWNER,
        "repository": REPOSITORY,
        "issue_number": ISSUE,
        "reason": "verified",
    }
    assert review == original
    assert calls[0][0] == (
        f"https://api.github.com/repos/{REPOSITORY}/issues/comments/{COMMENT_ID}"
    )
    assert calls[0][1]["Authorization"] == "Bearer read-only-token"
    assert calls[0][2] == 10.0


@pytest.mark.parametrize(
    "approval_url",
    [
        f"http://github.com/{REPOSITORY}/issues/{ISSUE}#issuecomment-{COMMENT_ID}",
        f"https://github.com.evil.invalid/{REPOSITORY}/issues/{ISSUE}#issuecomment-{COMMENT_ID}",
        f"https://github.com/other/nm_suite/issues/{ISSUE}#issuecomment-{COMMENT_ID}",
        f"https://github.com/{REPOSITORY}/issues/42#issuecomment-{COMMENT_ID}",
        f"https://github.com/{REPOSITORY}/issues/{ISSUE}#issuecomment-12",
        f"https://github.com/{REPOSITORY}/issues/{ISSUE}?x=1#issuecomment-{COMMENT_ID}",
    ],
)
def test_untrusted_or_wrong_scope_comment_url_is_rejected_before_fetch(approval_url):
    called = False

    def fetcher(_url, _headers, _timeout):
        nonlocal called
        called = True
        return _payload()

    result = _verify(_review(approval_url=approval_url), fetcher)

    assert result["verified"] is False
    assert result["reason"] == "approval_url_invalid"
    assert called is False


@pytest.mark.parametrize(
    ("payload_changes", "reason"),
    [
        ({"id": COMMENT_ID + 1}, "approval_response_comment_id_mismatch"),
        (
            {"html_url": APPROVAL_URL.replace("/issues/41", "/issues/42")},
            "approval_response_url_mismatch",
        ),
        (
            {"issue_url": "https://api.github.com/repos/Rybjuani/nm_suite/issues/42"},
            "approval_response_url_mismatch",
        ),
        ({"user": {"login": "intruder"}}, "approval_response_author_mismatch"),
        ({"body": f"Approved another:key@light {REPORT_SHA[:12]}"}, "approval_response_body_mismatch"),
        ({"body": f"Approved {KEY} for a different report"}, "approval_response_body_mismatch"),
    ],
)
def test_api_comment_must_confirm_id_scope_author_key_and_report(payload_changes, reason):
    result = _verify(fetcher=lambda _url, _headers, _timeout: _payload(**payload_changes))

    assert result["verified"] is False
    assert result["reason"] == reason


def test_record_author_must_be_the_configured_owner_without_fetching():
    called = False

    def fetcher(_url, _headers, _timeout):
        nonlocal called
        called = True
        return _payload()

    result = _verify(_review(author="intruder"), fetcher)

    assert result["verified"] is False
    assert result["reason"] == "approval_author_mismatch"
    assert called is False


def test_record_comment_id_must_be_a_positive_json_integer():
    result = _verify(_review(comment_id=str(COMMENT_ID)))

    assert result["verified"] is False
    assert result["reason"] == "approval_comment_id_invalid"


def test_issue_is_fixed_by_environment_and_repository_is_derived_from_git_remote(monkeypatch):
    monkeypatch.setenv(av.ISSUE_ENV, str(ISSUE))
    monkeypatch.delenv(av.REPOSITORY_ENV, raising=False)
    monkeypatch.delenv(av.OWNER_ENV, raising=False)
    monkeypatch.setattr(
        av,
        "_git_origin_url",
        lambda _cwd: "git@github.com:Rybjuani/nm_suite.git",
    )

    result = av.verify_approval(
        _review(),
        key=KEY,
        report_sha256=REPORT_SHA,
        token="read-only-token",
        fetcher=lambda _url, _headers, _timeout: _payload(),
    )

    assert result["verified"] is True
    assert result["repository"] == REPOSITORY
    assert result["issue_number"] == ISSUE


def test_explicit_repository_and_owner_configuration_override_environment(monkeypatch):
    monkeypatch.setenv(av.REPOSITORY_ENV, "attacker/wrong")
    monkeypatch.setenv(av.OWNER_ENV, "attacker")

    assert _verify()["verified"] is True


def test_repository_name_can_be_configured_separately_from_owner():
    result = _verify(repository="nm_suite", owner="Rybjuani")

    assert result["verified"] is True
    assert result["repository"] == REPOSITORY


@pytest.mark.parametrize(
    ("remote_url", "expected"),
    [
        ("https://github.com/Rybjuani/nm_suite.git", ("Rybjuani", "nm_suite")),
        ("git@github.com:Rybjuani/nm_suite.git", ("Rybjuani", "nm_suite")),
        ("ssh://git@github.com/Rybjuani/nm_suite.git", ("Rybjuani", "nm_suite")),
        ("https://github.com.evil.invalid/Rybjuani/nm_suite.git", None),
        ("https://gitlab.com/Rybjuani/nm_suite.git", None),
    ],
)
def test_git_remote_parser_accepts_only_github_repository_urls(remote_url, expected):
    assert av._repository_from_remote_url(remote_url) == expected


def test_missing_token_fails_closed_and_does_not_call_injected_fetcher(monkeypatch):
    for name in av.TOKEN_ENVS:
        monkeypatch.delenv(name, raising=False)
    called = False

    def fetcher(_url, _headers, _timeout):
        nonlocal called
        called = True
        return _payload()

    result = _verify(fetcher=fetcher, token=None)

    assert result["verified"] is False
    assert result["reason"] == "approval_token_missing"
    assert called is False


@pytest.mark.parametrize(
    ("fetcher", "reason"),
    [
        (lambda _url, _headers, _timeout: (_ for _ in ()).throw(OSError("offline")), "approval_fetch_failed"),
        (lambda _url, _headers, _timeout: b"not-json", "approval_response_invalid"),
        (lambda _url, _headers, _timeout: [], "approval_response_invalid"),
    ],
)
def test_network_and_response_failures_are_normalized(fetcher, reason):
    result = _verify(fetcher=fetcher)

    assert result["verified"] is False
    assert result["reason"] == reason
    assert result["key"] == KEY
    assert result["report_sha256"] == REPORT_SHA


def test_missing_fixed_issue_never_trusts_issue_number_from_comment_url(monkeypatch):
    monkeypatch.delenv(av.ISSUE_ENV, raising=False)

    result = _verify(issue_number=None)

    assert result["verified"] is False
    assert result["reason"] == "approval_issue_unconfigured"


def test_invalid_review_returns_policy_shaped_unverified_result():
    result = _verify(review={})

    assert result["verified"] is False
    assert result["approval_url"] == ""
    assert result["comment_id"] is None
    assert result["author"] == ""
