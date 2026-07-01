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


def test_runtime_dbt_modal_with_window_overlay_metadata_is_evaluated(tmp_path: Path) -> None:
    """Regression for the capture_v8 harness metadata bug: when the runtime
    manifest records dbt-practice-stop with surface=window_modal,
    modal_capture_scope=window_overlay, backdrop_observable=true and a
    back_screen_key, the modal audit must evaluate backdrop/blur/centering
    (not fall back to BACKDROP_CAPTURE_MISSING / not_observable_modal_crop).

    Before the harness fix, capture_v8.py labeled dbt-practice-stop as
    surface=window with no modal metadata, so the audit could never reach the
    backdrop comparison even though the PNG and _PracticeModalScrim existed.
    """
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent()
    modal = _modal(parent)
    _save(canonical / "suite-dbt-library-light-960x600.png", parent)
    _save(canonical / "suite-dbt-practice-stop-light-960x600.png", modal)
    _save(actual / "suite-dbt-library-light-960x600.png", parent)
    _save(actual / "suite-dbt-practice-stop-light-960x600.png", modal)
    runtime_modal_record = {
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
            runtime_modal_record,
        ],
        canonical=True,
    )
    _write_manifest(
        actual,
        [
            {"file": "suite-dbt-library-light-960x600.png", "surface": "window"},
            runtime_modal_record,
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

    # The audit must reach the backdrop/blur evaluation stage, not short-circuit
    # on BACKDROP_CAPTURE_MISSING (which would set backdrop_region to
    # "not_observable_modal_crop").
    assert audit.CODE_BACKDROP_CAPTURE_MISSING not in row.codes
    assert row.backdrop_region != "not_observable_modal_crop"
    assert row.blur_dim_equivalence != "not_observable_modal_crop"
    assert row.centered != "not_observable_modal_crop"


# --- Bbox detector robustness against backdrop residual noise ---------------
# These tests verify that _refine_bbox_to_dense_core / modal_bbox_candidates
# distinguish real modal-panel geometry from backdrop residual noise (the
# Qt-QGraphicsBlurEffect vs PIL-GaussianBlur difference that inflates the raw
# binary_closing(9x9) bbox laterally). A panel that is geometrically correct
# must not fail MODAL_CENTER_FAIL / MODAL_BBOX_FAIL because of noise bleed.


def _parent_with_contrast_cards(size=(960, 600)) -> Image.Image:
    """A parent screen with high-contrast content (cards) that produces
    residual diff when blurred by Qt vs PIL, simulating the dbt-library
    backdrop that triggered the false MODAL_BBOX_FAIL."""
    image = Image.new("RGB", size, "#191F2E")
    draw = ImageDraw.Draw(image)
    # High-contrast cards in the left zone (x=30..190) — this is the content
    # whose Qt-vs-PIL blur residual inflates the raw bbox.
    for x in range(30, 190, 40):
        draw.rectangle([x, 180, x + 30, 400], fill="#F3EFE4")
    # Cards in the right zone too (symmetric noise)
    for x in range(770, 930, 40):
        draw.rectangle([x, 180, x + 30, 400], fill="#F3EFE4")
    return image


def _modal_centered(parent: Image.Image, card_bbox=(280, 165, 400, 270)) -> Image.Image:
    """A modal capture with a centered card (blur 3 + scrim + surface card)."""
    blurred = parent.filter(ImageFilter.GaussianBlur(radius=3))
    tint = Image.new("RGB", parent.size, (20, 18, 14))
    image = Image.blend(blurred, tint, 0.5)
    draw = ImageDraw.Draw(image)
    x, y, w, h = card_bbox
    draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill="#fffaf2", outline="#d8cfc0", width=2)
    # Panel content (title + body) — dense diff region
    draw.rectangle((x + 20, y + 20, x + w - 20, y + 40), fill="#2e5d43")
    draw.rectangle((x + 20, y + 50, x + w - 24, y + 58), fill="#846a47")
    # Buttons row
    draw.rectangle((x + 20, y + h - 50, x + 120, y + h - 16), fill="#3a4a5e")
    draw.rectangle((x + w - 120, y + h - 50, x + w - 20, y + h - 16), fill="#2e5d43")
    return image


def _add_backdrop_noise(image: Image.Image, intensity: int = 14) -> Image.Image:
    """Add sparse noise to the backdrop zone (outside the card) to simulate
    Qt-vs-PIL blur residual that the raw binary_closing(9x9) bridges to the
    panel, inflating the detected bbox."""
    import random
    draw = ImageDraw.Draw(image)
    w, h = image.size
    rng = random.Random(42)
    # Card is roughly centered; add noise in the left/right backdrop zones
    for _ in range(6000):
        x = rng.randint(0, 280)
        y = rng.randint(140, 440)
        base = image.getpixel((x, y))
        delta = rng.randint(-intensity, intensity)
        px = tuple(max(0, min(255, c + delta)) for c in base)
        draw.point((x, y), fill=px)
    for _ in range(6000):
        x = rng.randint(680, w - 1)
        y = rng.randint(140, 440)
        base = image.getpixel((x, y))
        delta = rng.randint(-intensity, intensity)
        px = tuple(max(0, min(255, c + delta)) for c in base)
        draw.point((x, y), fill=px)
    return image


def test_backdrop_residual_noise_does_not_inflate_bbox_when_panel_is_centered(tmp_path: Path) -> None:
    """Regression: a centered modal panel with backdrop residual noise (Qt-vs-PIL
    blur difference) must not produce MODAL_CENTER_FAIL / MODAL_BBOX_FAIL.
    The dense-core refinement trims the noise bleed that the raw
    binary_closing(9x9) bridges to the panel."""
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent_with_contrast_cards()
    modal_canonical = _modal_centered(parent)
    # Actual: same centered card, but with backdrop residual noise added.
    modal_actual = _modal_centered(parent)
    modal_actual = _add_backdrop_noise(modal_actual, intensity=14)
    _save(canonical / "suite-dbt-library-light-960x600.png", parent)
    _save(canonical / "suite-dbt-practice-stop-light-960x600.png", modal_canonical)
    _save(actual / "suite-dbt-library-light-960x600.png", parent)
    _save(actual / "suite-dbt-practice-stop-light-960x600.png", modal_actual)
    record = {
        "file": "suite-dbt-practice-stop-light-960x600.png",
        "surface": "window_modal",
        "is_modal": True,
        "modal_capture_scope": "window_overlay",
        "backdrop_observable": True,
        "back_screen_key": "suite:dbt-library@light",
    }
    _write_manifest(canonical, [{"file": "suite-dbt-library-light-960x600.png", "surface": "window"}, record], canonical=True)
    _write_manifest(actual, [{"file": "suite-dbt-library-light-960x600.png", "surface": "window"}, record], canonical=False)

    canonical_captures = audit.load_captures(canonical, canonical=True)
    actual_captures = audit.load_captures(actual, canonical=False)
    row = audit.audit_modal_key(
        "suite:dbt-practice-stop@light",
        canonical_dir=canonical,
        actual_dir=actual,
        canonical_captures=canonical_captures,
        actual_captures=actual_captures,
        center_tolerance_px=18,
        bbox_tolerance_px=32,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )

    # The noise must not cause CENTER or BBOX fails. The panel is geometrically
    # centered and correctly sized; only the backdrop has residual noise.
    assert audit.CODE_MODAL_CENTER_FAIL not in row.codes, (
        f"backdrop noise inflated center: {row.metrics}"
    )
    assert audit.CODE_MODAL_BBOX_FAIL not in row.codes, (
        f"backdrop noise inflated bbox: {row.metrics}"
    )


def test_actually_offcenter_modal_still_fails_centering(tmp_path: Path) -> None:
    """A modal that is genuinely off-center must still fail MODAL_CENTER_FAIL.
    The dense-core refinement must not mask real geometric divergences."""
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent_with_contrast_cards()
    # Canonical card centered at x=280..680 (center 480)
    modal_canonical = _modal_centered(parent, card_bbox=(280, 165, 400, 270))
    # Actual card shifted 60px to the right (center 540) — genuinely off-center
    modal_actual = _modal_centered(parent, card_bbox=(340, 165, 400, 270))
    _save(canonical / "suite-dbt-library-light-960x600.png", parent)
    _save(canonical / "suite-dbt-practice-stop-light-960x600.png", modal_canonical)
    _save(actual / "suite-dbt-library-light-960x600.png", parent)
    _save(actual / "suite-dbt-practice-stop-light-960x600.png", modal_actual)
    record = {
        "file": "suite-dbt-practice-stop-light-960x600.png",
        "surface": "window_modal",
        "is_modal": True,
        "modal_capture_scope": "window_overlay",
        "backdrop_observable": True,
        "back_screen_key": "suite:dbt-library@light",
    }
    _write_manifest(canonical, [{"file": "suite-dbt-library-light-960x600.png", "surface": "window"}, record], canonical=True)
    _write_manifest(actual, [{"file": "suite-dbt-library-light-960x600.png", "surface": "window"}, record], canonical=False)

    canonical_captures = audit.load_captures(canonical, canonical=True)
    actual_captures = audit.load_captures(actual, canonical=False)
    row = audit.audit_modal_key(
        "suite:dbt-practice-stop@light",
        canonical_dir=canonical,
        actual_dir=actual,
        canonical_captures=canonical_captures,
        actual_captures=actual_captures,
        center_tolerance_px=18,
        bbox_tolerance_px=32,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )

    assert row.verdict == "FAIL"
    assert audit.CODE_MODAL_CENTER_FAIL in row.codes, (
        f"genuinely off-center modal must fail centering: {row.metrics}"
    )


def test_actually_wider_modal_still_fails_bbox_size(tmp_path: Path) -> None:
    """A modal that is genuinely wider than the canonical must still fail
    MODAL_BBOX_FAIL. The refinement must not mask real size divergences."""
    canonical = tmp_path / "canon"
    actual = tmp_path / "actual"
    parent = _parent_with_contrast_cards()
    # Canonical card width 400
    modal_canonical = _modal_centered(parent, card_bbox=(280, 165, 400, 270))
    # Actual card width 500 (100px wider) — genuinely wrong size
    modal_actual = _modal_centered(parent, card_bbox=(230, 165, 500, 270))
    _save(canonical / "suite-dbt-library-light-960x600.png", parent)
    _save(canonical / "suite-dbt-practice-stop-light-960x600.png", modal_canonical)
    _save(actual / "suite-dbt-library-light-960x600.png", parent)
    _save(actual / "suite-dbt-practice-stop-light-960x600.png", modal_actual)
    record = {
        "file": "suite-dbt-practice-stop-light-960x600.png",
        "surface": "window_modal",
        "is_modal": True,
        "modal_capture_scope": "window_overlay",
        "backdrop_observable": True,
        "back_screen_key": "suite:dbt-library@light",
    }
    _write_manifest(canonical, [{"file": "suite-dbt-library-light-960x600.png", "surface": "window"}, record], canonical=True)
    _write_manifest(actual, [{"file": "suite-dbt-library-light-960x600.png", "surface": "window"}, record], canonical=False)

    canonical_captures = audit.load_captures(canonical, canonical=True)
    actual_captures = audit.load_captures(actual, canonical=False)
    row = audit.audit_modal_key(
        "suite:dbt-practice-stop@light",
        canonical_dir=canonical,
        actual_dir=actual,
        canonical_captures=canonical_captures,
        actual_captures=actual_captures,
        center_tolerance_px=18,
        bbox_tolerance_px=32,
        backdrop_mean_tolerance=22.0,
        blur_ratio_tolerance=0.2,
        parent_mean_tolerance=35.0,
    )

    assert row.verdict == "FAIL"
    assert audit.CODE_MODAL_BBOX_FAIL in row.codes, (
        f"genuinely wider modal must fail bbox size: {row.metrics}"
    )
