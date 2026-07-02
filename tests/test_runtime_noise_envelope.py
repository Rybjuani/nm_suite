from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from qa import runtime_noise_envelope as envelope


FILE_NAME = "suite-dbt-practice-stop-light-10x10.png"
KEY = "suite:dbt-practice-stop@light"


def _save(path: Path, *, size: tuple[int, int] = (10, 10), changed: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, "#000000")
    pixels = image.load()
    width, height = size
    for index in range(changed):
        pixels[index % width, index // width % height] = (255, 255, 255)
    image.save(path)


def _dirs(tmp_path: Path, *, b2_changed: int = 0, modified_changed: int = 0) -> tuple[Path, Path, Path]:
    b1 = tmp_path / "b1"
    b2 = tmp_path / "b2"
    modified = tmp_path / "modified"
    _save(b1 / FILE_NAME)
    _save(b2 / FILE_NAME, changed=b2_changed)
    _save(modified / FILE_NAME, changed=modified_changed)
    return b1, b2, modified


def _row(payload: dict) -> dict:
    assert payload["rows"]
    return payload["rows"][0]


def test_identical_images_pass_strict(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path)

    payload = envelope.evaluate([b1, b2], [modified], set())

    assert _row(payload)["status"] == envelope.PASS_STRICT
    assert payload["summary"]["strict_pass"] is True


def test_modified_inside_noise_envelope_passes_strict(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path, b2_changed=1, modified_changed=1)

    payload = envelope.evaluate([b1, b2], [modified], set())

    assert _row(payload)["status"] == envelope.PASS_STRICT
    assert _row(payload)["delta_median"] <= _row(payload)["noise_worst"] + 0.001


def test_delta_best_only_is_review_noise_not_pass(tmp_path: Path) -> None:
    b1, b2, _modified = _dirs(tmp_path)
    m1 = tmp_path / "m1"
    m2 = tmp_path / "m2"
    _save(m1 / FILE_NAME)
    _save(m2 / FILE_NAME, changed=50)

    payload = envelope.evaluate([b1, b2], [m1, m2], set())
    row = _row(payload)

    assert row["status"] == envelope.REVIEW_NOISE
    assert "DELTA_BEST_ONLY" in row["codes"]
    assert payload["summary"]["strict_pass"] is False


def test_high_delta_outside_allowlist_fails(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path, modified_changed=50)

    payload = envelope.evaluate([b1, b2], [modified], set())

    assert _row(payload)["status"] == envelope.FAIL
    assert "DELTA_EXCEEDS_NOISE_ENVELOPE" in _row(payload)["codes"]


def test_expected_delta_allowlist_classifies_expected_delta(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path, modified_changed=50)

    payload = envelope.evaluate([b1, b2], [modified], {KEY})

    assert _row(payload)["status"] == envelope.EXPECTED_DELTA
    assert payload["summary"]["strict_pass"] is True


def test_shape_mismatch_without_allowlist_fails(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path)
    _save(modified / FILE_NAME, size=(11, 10))

    payload = envelope.evaluate([b1, b2], [modified], set())

    assert _row(payload)["status"] == envelope.FAIL
    assert "SHAPE_MISMATCH" in _row(payload)["codes"]


def test_shape_mismatch_with_explicit_allowlist_is_expected_delta(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path)
    _save(modified / FILE_NAME, size=(11, 10))

    payload = envelope.evaluate([b1, b2], [modified], {KEY})

    assert _row(payload)["status"] == envelope.EXPECTED_DELTA
    assert payload["summary"]["strict_pass"] is True


def test_noise_warning_is_not_strong_pass(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path, b2_changed=20, modified_changed=20)

    payload = envelope.evaluate([b1, b2], [modified], set(), noise_warning_threshold=0.01)

    assert _row(payload)["status"] == envelope.NOISE_WARNING
    assert payload["summary"]["strict_pass"] is False


def test_output_reports_contain_minimum_metrics(tmp_path: Path) -> None:
    b1, b2, modified = _dirs(tmp_path)
    out_dir = tmp_path / "report"

    rc = envelope.main(
        [
            "--baseline-dir",
            str(b1),
            "--baseline-dir",
            str(b2),
            "--modified-dir",
            str(modified),
            "--out-dir",
            str(out_dir),
        ]
    )

    assert rc == 0
    payload = json.loads((out_dir / "RUNTIME_NOISE_ENVELOPE_REPORT.json").read_text(encoding="utf-8"))
    assert (out_dir / "RUNTIME_NOISE_ENVELOPE_REPORT.csv").exists()
    assert (out_dir / "RUNTIME_NOISE_ENVELOPE_REPORT.md").exists()
    row = _row(payload)
    for key in (
        "shape_mismatch",
        "diff_px_low",
        "diff_px_high",
        "diff_pct_high",
        "max_rgb",
        "mean_rgb_high",
        "total_px",
        "noise_best",
        "noise_worst",
        "delta_best",
        "delta_median",
        "delta_worst",
    ):
        assert key in row
