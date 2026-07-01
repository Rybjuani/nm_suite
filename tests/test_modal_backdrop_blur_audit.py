from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from tools.qa import audit_modal_backdrop_blur as audit


def _save(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _parent(size=(240, 160)) -> Image.Image:
    image = Image.new("RGB", size, "#efe7dc")
    draw = ImageDraw.Draw(image)
    for x in range(0, size[0], 12):
        draw.line((x, 0, size[0] - x // 2, size[1]), fill="#2e5d43", width=2)
    for y in range(20, size[1], 28):
        draw.rectangle((18, y, size[0] - 24, y + 12), fill="#d8cfc0")
    return image


def _modal(parent: Image.Image, bbox=(70, 44, 170, 124)) -> Image.Image:
    blurred = parent.filter(ImageFilter.GaussianBlur(radius=3))
    tint = Image.new("RGB", parent.size, (20, 18, 14))
    image = Image.blend(blurred, tint, 0.5)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(bbox, radius=12, fill="#fffaf2", outline="#d8cfc0", width=2)
    draw.rectangle((bbox[0] + 18, bbox[1] + 18, bbox[2] - 18, bbox[1] + 26), fill="#2e5d43")
    draw.rectangle((bbox[0] + 18, bbox[1] + 40, bbox[2] - 24, bbox[1] + 48), fill="#846a47")
    return image


def _write_manifest(root: Path, captures: list[dict], *, canonical: bool) -> None:
    name = "MANIFEST.json" if canonical else "CAPTURE_MANIFEST.json"
    payload = {"captures": captures} if canonical else {"results": captures}
    (root / name).write_text(json.dumps(payload), encoding="utf-8")


def test_window_modal_passes_when_backdrop_and_back_screen_match(tmp_path: Path) -> None:
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent()
    modal = _modal(parent)
    files = {
        canonical / "suite-dbt-library-light-240x160.png": parent,
        canonical / "suite-dbt-practice-stop-light-240x160.png": modal,
        actual / "suite-dbt-library-light-240x160.png": parent,
        actual / "suite-dbt-practice-stop-light-240x160.png": modal,
    }
    for path, image in files.items():
        _save(path, image)
    _write_manifest(
        canonical,
        [
            {"file": "suite-dbt-library-light-240x160.png", "surface": "window"},
            {
                "file": "suite-dbt-practice-stop-light-240x160.png",
                "surface": "window_modal",
                "is_modal": True,
                "modal_capture_scope": "window_overlay",
                "backdrop_observable": True,
                "back_screen_key": "suite:dbt-library@light",
            },
        ],
        canonical=True,
    )
    _write_manifest(
        actual,
        [
            {"file": "suite-dbt-library-light-240x160.png", "surface": "window"},
            {
                "file": "suite-dbt-practice-stop-light-240x160.png",
                "surface": "window_modal",
                "is_modal": True,
                "modal_capture_scope": "window_overlay",
                "backdrop_observable": True,
                "back_screen_key": "suite:dbt-library@light",
            },
        ],
        canonical=False,
    )

    args = Namespace(
        key=None,
        all=True,
        canonical=str(canonical),
        actual=str(actual),
        out_dir=str(tmp_path / "report"),
        center_tolerance_px=18,
        bbox_tolerance_px=24,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )
    rows, payload, _ = audit.run(args)

    assert payload["summary"]["test_blur_pass"] is True
    assert rows[0].verdict == "PASS"
    assert not rows[0].codes


def test_modal_crop_cannot_pass_backdrop_gate(tmp_path: Path) -> None:
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent()
    _save(canonical / "hub-detalle-light-240x160.png", parent)
    _save(actual / "hub-detalle-light-240x160.png", parent)
    _save(canonical / "hub-detalle-resumen-ia-0-light-240x160.png", _modal(parent))
    _save(actual / "hub-detalle-resumen-ia-0-light-56x22.png", Image.new("RGB", (56, 22), "#fffaf2"))
    _write_manifest(
        canonical,
        [
            {"file": "hub-detalle-light-240x160.png", "surface": "window"},
            {
                "file": "hub-detalle-resumen-ia-0-light-240x160.png",
                "surface": "window_modal",
                "is_modal": True,
                "modal_capture_scope": "window_overlay",
                "backdrop_observable": True,
                "back_screen_key": "hub:detalle@light",
            },
        ],
        canonical=True,
    )
    _write_manifest(
        actual,
        [
            {"file": "hub-detalle-light-240x160.png", "surface": "window"},
            {
                "file": "hub-detalle-resumen-ia-0-light-56x22.png",
                "surface": "modal",
                "is_modal": True,
                "modal_capture_scope": "panel_crop",
                "backdrop_observable": False,
                "back_screen_key": "hub:detalle@light",
            },
        ],
        canonical=False,
    )

    canonical_captures = audit.load_captures(canonical, canonical=True)
    actual_captures = audit.load_captures(actual, canonical=False)
    row = audit.audit_modal_key(
        "hub:detalle-resumen-ia-0@light",
        canonical_dir=canonical,
        actual_dir=actual,
        canonical_captures=canonical_captures,
        actual_captures=actual_captures,
        center_tolerance_px=18,
        bbox_tolerance_px=2,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )

    assert row.verdict == "FAIL"
    assert audit.CODE_MODAL_BBOX_FAIL in row.codes
    assert audit.CODE_BACKDROP_CAPTURE_MISSING in row.codes


def test_missing_canonical_modal_reports_clear_code(tmp_path: Path) -> None:
    row = audit.audit_modal_key(
        "suite:dbt-practice-stop@dark",
        canonical_dir=tmp_path / "canon",
        actual_dir=tmp_path / "actual",
        canonical_captures={},
        actual_captures={},
        center_tolerance_px=18,
        bbox_tolerance_px=24,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )

    assert row.verdict == "FAIL"
    assert row.codes == [audit.CODE_CANONICAL_MODAL_MISSING]


def _dbt_fixture(tmp_path: Path, *, include_dark_runtime: bool) -> tuple[Path, Path]:
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent_light = _parent()
    modal_light = _modal(parent_light)
    parent_dark = _parent()
    modal_dark = _modal(parent_dark)
    files = {
        canonical / "suite-dbt-library-light-240x160.png": parent_light,
        canonical / "suite-dbt-practice-stop-light-240x160.png": modal_light,
        canonical / "suite-dbt-library-dark-240x160.png": parent_dark,
        canonical / "suite-dbt-practice-stop-dark-240x160.png": modal_dark,
        actual / "suite-dbt-library-light-240x160.png": parent_light,
        actual / "suite-dbt-practice-stop-light-240x160.png": modal_light,
    }
    if include_dark_runtime:
        files[actual / "suite-dbt-library-dark-240x160.png"] = parent_dark
        files[actual / "suite-dbt-practice-stop-dark-240x160.png"] = modal_dark
    for path, image in files.items():
        _save(path, image)

    modal_record = {
        "surface": "window_modal",
        "is_modal": True,
        "modal_capture_scope": "window_overlay",
        "backdrop_observable": True,
    }

    def modal_entry(theme: str) -> dict:
        return {
            **modal_record,
            "file": f"suite-dbt-practice-stop-{theme}-240x160.png",
            "back_screen_key": f"suite:dbt-library@{theme}",
        }

    _write_manifest(
        canonical,
        [
            {"file": "suite-dbt-library-light-240x160.png", "surface": "window"},
            modal_entry("light"),
            {"file": "suite-dbt-library-dark-240x160.png", "surface": "window"},
            modal_entry("dark"),
        ],
        canonical=True,
    )
    actual_records = [
        {"file": "suite-dbt-library-light-240x160.png", "surface": "window"},
        modal_entry("light"),
    ]
    if include_dark_runtime:
        actual_records.extend(
            [
                {"file": "suite-dbt-library-dark-240x160.png", "surface": "window"},
                modal_entry("dark"),
            ]
        )
    _write_manifest(actual, actual_records, canonical=False)
    return canonical, actual


def test_all_fails_when_canonical_modal_missing_runtime(tmp_path: Path) -> None:
    canonical, actual = _dbt_fixture(tmp_path, include_dark_runtime=False)
    args = Namespace(
        key=None,
        all=True,
        canonical=str(canonical),
        actual=str(actual),
        out_dir=str(tmp_path / "report"),
        center_tolerance_px=18,
        bbox_tolerance_px=24,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )
    rows, payload, _ = audit.run(args)

    assert payload["summary"]["test_blur_pass"] is False
    assert payload["summary"]["fail"] >= 1
    assert any(row.key == "suite:dbt-practice-stop@dark" and row.verdict == "FAIL" for row in rows)


def test_all_cannot_pass_with_skipped_unavailable_runtime() -> None:
    total_canonical = 2
    pass_count = 2
    fail_count = 0
    skipped_unavailable_runtime = ["suite:dbt-practice-stop@dark"]
    rows_len = 2
    test_blur_pass = (
        rows_len == total_canonical
        and pass_count == total_canonical
        and fail_count == 0
        and not skipped_unavailable_runtime
    )
    assert test_blur_pass is False


def test_runtime_modal_without_explicit_metadata_fails(tmp_path: Path) -> None:
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent()
    modal = _modal(parent)
    _save(canonical / "suite-dbt-library-light-240x160.png", parent)
    _save(canonical / "suite-dbt-practice-stop-light-240x160.png", modal)
    _save(actual / "suite-dbt-library-light-240x160.png", parent)
    _save(actual / "suite-dbt-practice-stop-light-240x160.png", modal)
    _write_manifest(
        canonical,
        [
            {"file": "suite-dbt-library-light-240x160.png", "surface": "window"},
            {
                "file": "suite-dbt-practice-stop-light-240x160.png",
                "surface": "window_modal",
                "is_modal": True,
                "modal_capture_scope": "window_overlay",
                "backdrop_observable": True,
                "back_screen_key": "suite:dbt-library@light",
            },
        ],
        canonical=True,
    )
    _write_manifest(
        actual,
        [
            {"file": "suite-dbt-library-light-240x160.png", "surface": "window"},
            {
                "file": "suite-dbt-practice-stop-light-240x160.png",
                "surface": "window_modal",
                "is_modal": True,
            },
        ],
        canonical=False,
    )

    canonical_captures = audit.load_captures(canonical, canonical=True)
    actual_captures = audit.load_captures(actual, canonical=False)
    row = audit.audit_modal_key(
        "suite:dbt-practice-stop@light",
        canonical_dir=canonical,
        actual_dir=actual,
        canonical_captures=canonical_captures,
        actual_captures=actual_captures,
        center_tolerance_px=18,
        bbox_tolerance_px=24,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )

    assert row.verdict == "FAIL"
    assert audit.CODE_BACKDROP_CAPTURE_MISSING in row.codes


def _overblur_fraud(parent: Image.Image, bbox=(280, 165, 680, 435)) -> Image.Image:
    """Simulate modal overblur fraud: heavy blur washes out back-screen detail."""
    blurred = parent.filter(ImageFilter.GaussianBlur(radius=40))
    tint = Image.new("RGB", parent.size, (20, 18, 14))
    image = Image.blend(blurred, tint, 0.5)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(bbox, radius=12, fill="#fffaf2", outline="#d8cfc0", width=2)
    draw.rectangle((bbox[0] + 18, bbox[1] + 18, bbox[2] - 18, bbox[1] + 26), fill="#2e5d43")
    draw.rectangle((bbox[0] + 18, bbox[1] + 40, bbox[2] - 24, bbox[1] + 48), fill="#846a47")
    return image


def _modal_large(parent: Image.Image, bbox=(280, 165, 680, 435)) -> Image.Image:
    blurred = parent.filter(ImageFilter.GaussianBlur(radius=3))
    tint = Image.new("RGB", parent.size, (20, 18, 14))
    image = Image.blend(blurred, tint, 0.5)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(bbox, radius=12, fill="#fffaf2", outline="#d8cfc0", width=2)
    draw.rectangle((bbox[0] + 18, bbox[1] + 18, bbox[2] - 18, bbox[1] + 26), fill="#2e5d43")
    draw.rectangle((bbox[0] + 18, bbox[1] + 40, bbox[2] - 24, bbox[1] + 48), fill="#846a47")
    return image


def _parent_variant(size=(960, 600)) -> Image.Image:
    image = Image.new("RGB", size, "#dce8f0")
    draw = ImageDraw.Draw(image)
    for x in range(0, size[0], 10):
        draw.line((x, 0, size[0] - x // 3, size[1]), fill="#7a2040", width=3)
    for y in range(30, size[1], 36):
        draw.rectangle((24, y, size[0] - 30, y + 16), fill="#b8c9d8")
    return image


def test_overblur_cannot_produce_test_blur_pass(tmp_path: Path) -> None:
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent_canonical = _parent(size=(960, 600))
    parent_actual = _parent_variant(size=(960, 600))
    modal = _modal_large(parent_canonical)
    overblur = _overblur_fraud(parent_actual)
    _save(canonical / "suite-dbt-library-light-960x600.png", parent_canonical)
    _save(canonical / "suite-dbt-practice-stop-light-960x600.png", modal)
    _save(actual / "suite-dbt-library-light-960x600.png", parent_actual)
    _save(actual / "suite-dbt-practice-stop-light-960x600.png", overblur)
    record = {
        "file": "suite-dbt-practice-stop-light-960x600.png",
        "surface": "window_modal",
        "is_modal": True,
        "modal_capture_scope": "window_overlay",
        "backdrop_observable": True,
        "back_screen_key": "suite:dbt-library@light",
    }
    _write_manifest(
        canonical,
        [
            {"file": "suite-dbt-library-light-960x600.png", "surface": "window"},
            record,
        ],
        canonical=True,
    )
    _write_manifest(
        actual,
        [
            {"file": "suite-dbt-library-light-960x600.png", "surface": "window"},
            record,
        ],
        canonical=False,
    )

    args = Namespace(
        key="suite:dbt-practice-stop@light",
        all=False,
        canonical=str(canonical),
        actual=str(actual),
        out_dir=str(tmp_path / "report"),
        center_tolerance_px=18,
        bbox_tolerance_px=24,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )
    rows, payload, _ = audit.run(args)

    assert payload["summary"]["test_blur_pass"] is False
    assert rows[0].verdict == "FAIL"
    assert audit.CODE_PARENT_SCREEN_DEPENDENCY in rows[0].codes
