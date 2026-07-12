#!/usr/bin/env python3
"""Verify external GitHub approvals for near-threshold visual evidence.

The verifier is deliberately fail-closed.  It accepts only a comment URL for
one configured repository and issue, fetches that comment through GitHub's
API, and returns a normalized mapping suitable for ``closure_policy.decide``.
It performs no writes and depends only on the Python standard library.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
GITHUB_WEB_HOST = "github.com"
GITHUB_API_HOST = "api.github.com"
GITHUB_API_VERSION = "2022-11-28"
REPOSITORY_ENV = "NM_VISUAL_APPROVAL_REPO"
OWNER_ENV = "NM_VISUAL_APPROVAL_OWNER"
ISSUE_ENV = "NM_VISUAL_APPROVAL_ISSUE"
TOKEN_ENVS = ("GH_TOKEN", "GITHUB_TOKEN")
MAX_RESPONSE_BYTES = 1024 * 1024

_REPOSITORY_PART_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_KEY_RE = re.compile(r"^(?:suite|hub):[^@\s]+@(?:light|dark)$")

Fetcher = Callable[[str, Mapping[str, str], float], object]


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        parsed = int(value)
        return parsed if parsed > 0 else None
    return None


def _repository_slug(value: object) -> tuple[str, str] | None:
    text = _text(value).strip("/")
    parts = text.split("/")
    if (
        len(parts) != 2
        or not all(_REPOSITORY_PART_RE.fullmatch(part) for part in parts)
        or parts[1].endswith(".git")
    ):
        return None
    return parts[0], parts[1]


def _repository_from_remote_url(remote_url: str) -> tuple[str, str] | None:
    """Parse a GitHub HTTPS/SSH origin without accepting lookalike hosts."""

    value = remote_url.strip()
    scp_match = re.fullmatch(
        r"(?:[^@/:]+@)?github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?",
        value,
        flags=re.IGNORECASE,
    )
    if scp_match:
        return _repository_slug(f"{scp_match.group('owner')}/{scp_match.group('repo')}")

    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() not in {"https", "ssh"}
        or (parsed.hostname or "").casefold() != GITHUB_WEB_HOST
        or port not in {None, 22, 443}
        or parsed.query
        or parsed.fragment
    ):
        return None
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return _repository_slug(path)


def _git_origin_url(git_cwd: Path) -> str | None:
    try:
        process = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(git_cwd),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if process.returncode != 0:
        return None
    return process.stdout.strip() or None


def _resolve_repository(
    repository: str | None,
    configured_owner: str | None,
    git_cwd: Path,
) -> tuple[str, str] | None:
    configured = repository if repository is not None else os.getenv(REPOSITORY_ENV)
    if configured is not None:
        slug = _repository_slug(configured)
        if slug is not None:
            return slug
        repo_name = _text(configured)
        repo_owner = _text(configured_owner)
        if (
            "/" not in repo_name
            and _REPOSITORY_PART_RE.fullmatch(repo_name)
            and not repo_name.endswith(".git")
            and _REPOSITORY_PART_RE.fullmatch(repo_owner)
        ):
            return repo_owner, repo_name
        return None
    remote_url = _git_origin_url(git_cwd)
    return _repository_from_remote_url(remote_url) if remote_url else None


def _safe_split_url(value: str):
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if parsed.username is not None or parsed.password is not None or port is not None:
        return None
    return parsed


def _web_comment_url_matches(
    value: str,
    repository: tuple[str, str],
    issue_number: int,
    comment_id: int,
) -> bool:
    parsed = _safe_split_url(value)
    if parsed is None:
        return False
    owner, repo = repository
    expected_path = f"/{owner}/{repo}/issues/{issue_number}"
    return (
        parsed.scheme.lower() == "https"
        and (parsed.hostname or "").casefold() == GITHUB_WEB_HOST
        and parsed.path.casefold() == expected_path.casefold()
        and not parsed.query
        and parsed.fragment == f"issuecomment-{comment_id}"
    )


def _api_issue_url_matches(
    value: object,
    repository: tuple[str, str],
    issue_number: int,
) -> bool:
    parsed = _safe_split_url(_text(value))
    if parsed is None:
        return False
    owner, repo = repository
    expected_path = f"/repos/{owner}/{repo}/issues/{issue_number}"
    return (
        parsed.scheme.lower() == "https"
        and (parsed.hostname or "").casefold() == GITHUB_API_HOST
        and parsed.path.casefold() == expected_path.casefold()
        and not parsed.query
        and not parsed.fragment
    )


def _default_fetcher(url: str, headers: Mapping[str, str], timeout: float) -> object:
    request = Request(url, headers=dict(headers), method="GET")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed GitHub API host
        status = getattr(response, "status", None)
        if status != 200:
            raise OSError("unexpected_http_status")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("response_too_large")
    return json.loads(raw.decode("utf-8"))


def _as_payload(value: object) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, bytes):
        if len(value) > MAX_RESPONSE_BYTES:
            return None
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_RESPONSE_BYTES:
            return None
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError):
            return None
        return decoded if isinstance(decoded, Mapping) else None
    return None


def _normalized_result(
    *,
    verified: bool,
    reason: str,
    key: object,
    report_sha256: object,
    approval_url: object,
    comment_id: object,
    author: object,
    repository: tuple[str, str] | None,
    issue_number: int | None,
) -> dict[str, object]:
    return {
        "verified": verified,
        "key": _text(key),
        "report_sha256": _text(report_sha256),
        "approval_url": _text(approval_url),
        "comment_id": comment_id if isinstance(comment_id, int) and not isinstance(comment_id, bool) else None,
        "author": _text(author),
        "repository": "/".join(repository) if repository else "",
        "issue_number": issue_number,
        "reason": reason,
    }


def verify_approval(
    human_review: object,
    *,
    key: str,
    report_sha256: str,
    issue_number: int | str | None = None,
    repository: str | None = None,
    owner: str | None = None,
    token: str | None = None,
    fetcher: Fetcher | None = None,
    git_cwd: str | Path | None = None,
    timeout: float = 10.0,
) -> dict[str, object]:
    """Verify and normalize one external GitHub issue-comment approval.

    ``repository`` may be configured as ``owner/name``.  When omitted, the
    verifier uses ``NM_VISUAL_APPROVAL_REPO`` and then the repository's Git
    ``origin``.  The approval author defaults to ``NM_VISUAL_APPROVAL_OWNER``
    and then to the repository owner.  ``issue_number`` defaults only to
    ``NM_VISUAL_APPROVAL_ISSUE``; it is never inferred from an untrusted URL.

    A token is always required, including with an injected fetcher.  Tests can
    pass a dummy token while using ``fetcher`` to guarantee that no network is
    accessed.
    """

    review = human_review if isinstance(human_review, Mapping) else {}
    approval_url = review.get("approval_url")
    comment_id_value = review.get("comment_id")
    review_author = review.get("author")
    configured_owner = owner if owner is not None else os.getenv(OWNER_ENV)
    resolved_repository = _resolve_repository(
        repository,
        configured_owner,
        Path(git_cwd or ROOT),
    )
    configured_issue = issue_number if issue_number is not None else os.getenv(ISSUE_ENV)
    resolved_issue = _positive_int(configured_issue)

    def result(verified: bool, reason: str, *, author_value: object = review_author):
        return _normalized_result(
            verified=verified,
            reason=reason,
            key=key,
            report_sha256=report_sha256,
            approval_url=approval_url,
            comment_id=comment_id_value,
            author=author_value,
            repository=resolved_repository,
            issue_number=resolved_issue,
        )

    if not isinstance(human_review, Mapping):
        return result(False, "approval_missing_or_invalid")
    if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
        return result(False, "approval_key_invalid")
    if not isinstance(report_sha256, str) or not _SHA256_RE.fullmatch(report_sha256):
        return result(False, "approval_report_sha256_invalid")
    if resolved_repository is None:
        return result(False, "approval_repository_unconfigured")
    if resolved_issue is None:
        return result(False, "approval_issue_unconfigured")

    expected_owner = _text(configured_owner) or resolved_repository[0]
    if not _REPOSITORY_PART_RE.fullmatch(expected_owner):
        return result(False, "approval_owner_invalid")

    comment_id = (
        comment_id_value
        if isinstance(comment_id_value, int)
        and not isinstance(comment_id_value, bool)
        and comment_id_value > 0
        else None
    )
    if comment_id is None:
        return result(False, "approval_comment_id_invalid")
    if not _text(approval_url) or not _web_comment_url_matches(
        _text(approval_url), resolved_repository, resolved_issue, comment_id
    ):
        return result(False, "approval_url_invalid")
    if not _text(review_author) or _text(review_author).casefold() != expected_owner.casefold():
        return result(False, "approval_author_mismatch")

    effective_token = token
    if effective_token is None:
        effective_token = next((os.getenv(name) for name in TOKEN_ENVS if os.getenv(name)), None)
    if not _text(effective_token):
        return result(False, "approval_token_missing")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        return result(False, "approval_timeout_invalid")

    repo_owner, repo_name = resolved_repository
    api_url = (
        f"https://{GITHUB_API_HOST}/repos/{repo_owner}/{repo_name}"
        f"/issues/comments/{comment_id}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_text(effective_token)}",
        "User-Agent": "nm-suite-approval-verifier",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    try:
        payload = _as_payload((fetcher or _default_fetcher)(api_url, headers, float(timeout)))
    except Exception:  # network and injected fetchers are both fail-closed
        return result(False, "approval_fetch_failed")
    if payload is None:
        return result(False, "approval_response_invalid")
    payload_id = payload.get("id")
    if isinstance(payload_id, bool) or payload_id != comment_id:
        return result(False, "approval_response_comment_id_mismatch")

    api_html_url = _text(payload.get("html_url"))
    if (
        api_html_url != _text(approval_url)
        or not _web_comment_url_matches(
            api_html_url, resolved_repository, resolved_issue, comment_id
        )
        or not _api_issue_url_matches(
            payload.get("issue_url"), resolved_repository, resolved_issue
        )
    ):
        return result(False, "approval_response_url_mismatch")

    user = payload.get("user")
    api_author = _text(user.get("login")) if isinstance(user, Mapping) else ""
    if (
        not api_author
        or api_author.casefold() != expected_owner.casefold()
        or api_author.casefold() != _text(review_author).casefold()
    ):
        return result(False, "approval_response_author_mismatch")

    body = payload.get("body")
    report_prefix = report_sha256[:12]
    if not isinstance(body, str) or key not in body or report_prefix not in body:
        return result(False, "approval_response_body_mismatch")

    return result(True, "verified", author_value=api_author)


__all__ = ["verify_approval"]
