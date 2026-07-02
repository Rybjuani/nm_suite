from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from qa import runtime_internal_nav_parity as nav


def _save(path: Path, *, size: tuple[int, int] = (20, 20), shift_y: int = 0, dot: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, "#f4efe6")
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 5 + shift_y, 15, 12 + shift_y), fill="#264b3a")
    if dot:
        draw.point((1, 1), fill="#ffffff")
    image.save(path)


def _meta(path: Path, **overrides: object) -> Path:
    payload = {
        "root_bbox": [0, 0, 20, 20],
        "state": "dbt-library",
        "tab": "library",
        "stack": "dbt",
        "scroll": 0,
        "viewport": [0, 0, 20, 20],
        "transform_scale": 1.0,
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _case(tmp_path: Path, *, nav_shift: int = 0, nav_dot: bool = False) -> nav.NavCase:
    direct = tmp_path / "direct.png"
    reached = tmp_path / "nav.png"
    _save(direct)
    _save(reached, shift_y=nav_shift, dot=nav_dot)
    direct_meta = _meta(tmp_path / "direct.json")
    nav_meta = _meta(tmp_path / "nav.json")
    return nav.NavCase("suite:dbt-library@light", direct, reached, direct_meta, nav_meta)


def test_identical_comparison_passes(tmp_path: Path) -> None:
    row = nav.compare_case(_case(tmp_path))

    assert row.status == nav.PASS
    assert row.diff_px_high == 0


def test_vertical_displacement_is_fail(tmp_path: Path) -> None:
    row = nav.compare_case(_case(tmp_path, nav_shift=3))

    assert row.status == nav.FAIL
    assert "VISUAL_DELTA" in row.codes


def test_few_isolated_pixels_are_review_not_pass(tmp_path: Path) -> None:
    row = nav.compare_case(_case(tmp_path, nav_dot=True), isolated_review_px=2)

    assert row.status == nav.REVIEW
    assert "ISOLATED_PIXEL_DELTA" in row.codes


def test_metadata_inconsistency_fails(tmp_path: Path) -> None:
    case = _case(tmp_path)
    case.nav_metadata = _meta(tmp_path / "nav.json", state="dbt-now")

    row = nav.compare_case(case)

    assert row.status == nav.FAIL
    assert "METADATA_MISMATCH" in row.codes
    assert row.metadata_delta["state"]["nav"] == "dbt-now"


def test_shape_mismatch_fails(tmp_path: Path) -> None:
    direct = tmp_path / "direct.png"
    reached = tmp_path / "nav.png"
    _save(direct, size=(20, 20))
    _save(reached, size=(21, 20))

    row = nav.compare_case(nav.NavCase("suite:dbt-library@light", direct, reached))

    assert row.status == nav.FAIL
    assert "SHAPE_MISMATCH" in row.codes


def test_root_bbox_mismatch_fails(tmp_path: Path) -> None:
    case = _case(tmp_path)
    case.nav_metadata = _meta(tmp_path / "nav.json", root_bbox=[1, 0, 20, 20])

    row = nav.compare_case(case)

    assert row.status == nav.FAIL
    assert "ROOT_BBOX_MISMATCH" in row.codes


def test_tab_state_mismatch_fails(tmp_path: Path) -> None:
    case = _case(tmp_path)
    case.nav_metadata = _meta(tmp_path / "nav.json", tab="now")

    row = nav.compare_case(case)

    assert row.status == nav.FAIL
    assert row.metadata_delta["tab"]["nav"] == "now"


def test_cli_writes_reports(tmp_path: Path) -> None:
    case = _case(tmp_path)
    out_dir = tmp_path / "report"

    rc = nav.main(
        [
            "--key",
            case.key,
            "--direct-image",
            str(case.direct_image),
            "--nav-image",
            str(case.nav_image),
            "--direct-metadata",
            str(case.direct_metadata),
            "--nav-metadata",
            str(case.nav_metadata),
            "--out-dir",
            str(out_dir),
        ]
    )

    assert rc == 0
    assert (out_dir / "RUNTIME_INTERNAL_NAV_PARITY_REPORT.json").exists()
    assert (out_dir / "RUNTIME_INTERNAL_NAV_PARITY_REPORT.csv").exists()
    assert (out_dir / "RUNTIME_INTERNAL_NAV_PARITY_REPORT.md").exists()
