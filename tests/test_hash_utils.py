from __future__ import annotations

import hashlib

from qa.hash_utils import sha256_binary, sha256_canonical_json, sha256_text


def test_sha256_binary_preserves_crlf_bytes_inside_png(tmp_path):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x08IDAT\x00\r\n\xff\x10\r\n"
    png = tmp_path / "capture.png"
    png.write_bytes(png_bytes)

    assert sha256_binary(png) == hashlib.sha256(png_bytes).hexdigest()
    assert sha256_binary(png) != hashlib.sha256(png_bytes.replace(b"\r\n", b"\n")).hexdigest()


def test_sha256_text_is_cross_platform_lf_stable(tmp_path):
    crlf = tmp_path / "crlf.py"
    lf = tmp_path / "lf.py"
    crlf.write_bytes(b"first\r\nsecond\rthird\n")
    lf.write_bytes(b"first\nsecond\nthird\n")

    assert sha256_text(crlf) == sha256_text(lf)


def test_sha256_canonical_json_ignores_mapping_order_and_spacing():
    left = {"z": [3, 2, 1], "text": "á", "nested": {"b": True, "a": None}}
    right = {"nested": {"a": None, "b": True}, "text": "á", "z": [3, 2, 1]}

    expected = hashlib.sha256(
        '{"nested":{"a":null,"b":true},"text":"á","z":[3,2,1]}'.encode("utf-8")
    ).hexdigest()
    assert sha256_canonical_json(left) == expected
    assert sha256_canonical_json(right) == expected
