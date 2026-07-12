#!/usr/bin/env python3
"""Deterministic SHA-256 helpers for visual-closure provenance."""

from __future__ import annotations

import hashlib
import json
from os import PathLike
from pathlib import Path
from typing import Any


Pathish = str | PathLike[str]


def sha256_binary(path: Pathish) -> str:
    """Hash a file byte-for-byte without newline or encoding conversion."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(path: Pathish) -> str:
    """Hash text after normalizing CRLF and lone CR newlines to LF.

    Normalization is performed on bytes so the helper never rewrites a source
    file or depends on the platform's universal-newline behavior.
    """

    content = Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def sha256_canonical_json(value: Any) -> str:
    """Hash a JSON value using one stable, whitespace-free representation."""

    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
