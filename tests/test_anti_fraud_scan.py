"""Tests for qa/anti_fraud_scan.py — the static runtime/product anti-fraud guard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from PIL import Image

from qa.anti_fraud_scan import (
    QA_HARNESS_ROOTS,
    scan_asset_canonical_identity,
    scan_source,
    scan_paths,
    scan_qa_harness_source,
    scan_qa_harness_paths,
    main,
)


def _kinds(violations):
    return {v.kind for v in violations}


def _make_png(path: Path, color=(10, 20, 30)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color).save(path)


def test_asset_identity_clean_when_no_collision(tmp_path):
    _make_png(tmp_path / "qa" / "_mockup_canonical" / "hub-detalle-dark-960x600.png", (1, 2, 3))
    _make_png(tmp_path / "assets" / "brand.png", (200, 100, 50))  # different content
    assert scan_asset_canonical_identity(base=tmp_path) == []


def test_asset_identity_flags_smuggled_canonical(tmp_path):
    canon = tmp_path / "qa" / "_mockup_canonical" / "hub-detalle-dark-960x600.png"
    _make_png(canon, (7, 7, 7))
    smuggled = tmp_path / "assets" / "sneaky.png"
    smuggled.parent.mkdir(parents=True, exist_ok=True)
    smuggled.write_bytes(canon.read_bytes())  # byte-identical copy
    violations = scan_asset_canonical_identity(base=tmp_path)
    assert len(violations) == 1
    assert violations[0].kind == "asset_canonical_identity"
    assert violations[0].pattern == "hub-detalle-dark-960x600.png"


def test_asset_identity_detects_copy_under_product_dirs(tmp_path):
    canon = tmp_path / "qa" / "_mockup_canonical" / "suite-home-light-960x600.png"
    _make_png(canon, (9, 9, 9))
    for root in ("app", "hub", "shared"):
        dst = tmp_path / root / "x.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(canon.read_bytes())
    violations = scan_asset_canonical_identity(base=tmp_path)
    assert len(violations) == 3


def test_clean_source_has_no_violations():
    src = (
        "from PyQt6.QtGui import QPixmap\n"
        "def build():\n"
        "    pix = QPixmap('assets/logos/brand.png')\n"
        "    return pix\n"
    )
    assert scan_source(src, "app/clean.py") == []


def test_flags_canonical_path_literal():
    src = "REF = 'qa/_mockup_canonical/suite-recuperar-acceso-light-520x600.png'\n"
    v = scan_source(src, "app/x.py")
    assert any(k == "artifact_path_literal" for k in _kinds(v))


def test_flags_reports_qa_and_layered_report():
    src = (
        "A = 'reports/qa/layered_visual_compare_item'\n"
        "B = 'LAYERED_VISUAL_REPORT.json'\n"
    )
    v = scan_source(src, "app/x.py")
    patterns = {x.pattern for x in v}
    assert "reports/qa" in patterns
    assert "layered_visual_report" in patterns


def test_flags_setpixmap_with_reference_artifact():
    src = (
        "from PyQt6.QtGui import QPixmap\n"
        "def show(self):\n"
        "    self._overlay.setPixmap(QPixmap('qa/_mockup_canonical/x.png'))\n"
    )
    v = scan_source(src, "app/x.py")
    # Caught both as an artifact literal and as a pixmap-reference call.
    assert "pixmap_reference_artifact" in _kinds(v)
    assert "artifact_path_literal" in _kinds(v)


def test_flags_reference_overlay_identifier_and_class():
    src = (
        "class RecoverReferenceOverlay:\n"
        "    pass\n"
        "def _show_recover_reference_overlay(self):\n"
        "    self._reference_overlay = None\n"
    )
    v = scan_source(src, "app/x.py")
    assert "reference_overlay_identifier" in _kinds(v)


def test_does_not_ban_qpixmap_globally():
    src = (
        "from PyQt6.QtGui import QPixmap, QImage\n"
        "p = QPixmap('assets/icons/shield.png')\n"
        "i = QImage('assets/bg/forest.png')\n"
    )
    assert scan_source(src, "shared/x.py") == []


def test_captures_dir_is_flagged():
    src = "path = 'qa/_captures_v8/suite-home-light-960x600.png'\n"
    v = scan_source(src, "app/x.py")
    assert "_captures_v8" in {x.pattern for x in v}


def test_syntax_error_falls_back_to_line_scan():
    src = "def broken(:\n    x = 'qa/_mockup_canonical/y.png'\n"
    v = scan_source(src, "app/broken.py")
    assert any(x.kind == "unparsed_token" for x in v)


def test_real_product_tree_is_clean():
    """Regression guard: app/ hub/ shared/ must stay free of reference artifacts."""
    violations = scan_paths(["app", "hub", "shared"])
    assert violations == [], f"anti-fraud violations in product code: {[v.to_dict() for v in violations]}"


def test_main_returns_zero_on_clean_subset(capsys):
    rc = main(["--roots", "shared"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "CLEAN" in captured.out


_MODAL_FRAUD_MSG = "fixea primero la pantalla de atras y despues seguis con el modal"


def _modal_violation_patterns(violations):
    return {v.pattern for v in violations}


def test_modal_blur_light_40_fails():
    src = "_NM_MODAL_BLUR_RADIUS_LIGHT = 40\n"
    v = scan_source(src, "shared/components/dialogs.py")
    assert any(x.kind == "modal_backdrop_constant" for x in v)
    assert any(_MODAL_FRAUD_MSG in x.pattern for x in v)


def test_modal_blur_dark_4_fails():
    src = "_NM_MODAL_BLUR_RADIUS_DARK = 4\n"
    v = scan_source(src, "shared/components/dialogs.py")
    assert any(x.kind == "modal_backdrop_constant" for x in v)
    assert any(_MODAL_FRAUD_MSG in x.pattern for x in v)


def test_modal_scrim_wrong_fails():
    src = "_NM_MODAL_SCRIM_RGBA = (0, 0, 0, 128)\n"
    v = scan_source(src, "shared/components/dialogs.py")
    assert any(x.kind == "modal_backdrop_constant" for x in v)
    assert any(_MODAL_FRAUD_MSG in x.pattern for x in v)


def test_modal_constants_canonical_pass():
    src = (
        "_NM_MODAL_BLUR_RADIUS_LIGHT = 3\n"
        "_NM_MODAL_BLUR_RADIUS_DARK = 3\n"
        "_NM_MODAL_SCRIM_RGBA = (20, 18, 14, 128)\n"
    )
    v = scan_source(src, "shared/components/dialogs.py")
    assert v == []


def test_real_dialogs_modal_constants_pass():
    dialogs = Path(__file__).resolve().parents[1] / "shared" / "components" / "dialogs.py"
    v = scan_source(dialogs.read_text(encoding="utf-8"), "shared/components/dialogs.py")
    modal_v = [x for x in v if x.kind == "modal_backdrop_constant"]
    assert modal_v == []


# --- DBT _PracticeModalScrim modal backdrop contract ----------------------
# _PracticeModalScrim (app/modules/dbt_qt.py) is a canonical modal surface
# (suite:dbt-practice-stop) and must obey the same canonical contract as
# NMDialog: blur 3/3, scrim (20, 18, 14, 128). A larger blur (e.g. 40 in light
# mode) hides back-screen divergence and is treated as visual fraud.


def test_dbt_scrim_blur_light_40_fails():
    src = "_SCRIM_BLUR_RADIUS_LIGHT = 40\n"
    v = scan_source(src, "app/modules/dbt_qt.py")
    assert any(x.kind == "modal_backdrop_constant" for x in v)
    assert any(_MODAL_FRAUD_MSG in x.pattern for x in v)


def test_dbt_scrim_blur_dark_4_fails():
    src = "_SCRIM_BLUR_RADIUS_DARK = 4\n"
    v = scan_source(src, "app/modules/dbt_qt.py")
    assert any(x.kind == "modal_backdrop_constant" for x in v)
    assert any(_MODAL_FRAUD_MSG in x.pattern for x in v)


def test_dbt_scrim_rgba_alpha_127_fails():
    src = "_SCRIM_RGBA = (20, 18, 14, 127)\n"
    v = scan_source(src, "app/modules/dbt_qt.py")
    assert any(x.kind == "modal_backdrop_constant" for x in v)
    assert any(_MODAL_FRAUD_MSG in x.pattern for x in v)


def test_dbt_scrim_constants_canonical_pass():
    src = (
        "_SCRIM_BLUR_RADIUS_LIGHT = 3\n"
        "_SCRIM_BLUR_RADIUS_DARK = 3\n"
        "_SCRIM_RGBA = (20, 18, 14, 128)\n"
    )
    v = scan_source(src, "app/modules/dbt_qt.py")
    assert v == []


def test_real_dbt_qt_modal_constants_pass():
    dbt = Path(__file__).resolve().parents[1] / "app" / "modules" / "dbt_qt.py"
    v = scan_source(dbt.read_text(encoding="utf-8"), "app/modules/dbt_qt.py")
    modal_v = [x for x in v if x.kind == "modal_backdrop_constant"]
    assert modal_v == []


def test_qa_harness_capture_cannot_read_canonical_artifact():
    src = (
        "from pathlib import Path\n"
        "from PIL import Image\n"
        "def capture():\n"
        "    return Image.open(Path('qa/_mockup_canonical/suite-home-light-960x600.png'))\n"
    )
    v = scan_qa_harness_source(src, "qa/capture_v8.py")
    assert "qa_capture_reads_reference_artifact" in _kinds(v)


def test_qa_harness_detects_dynamic_split_mockup_canonical_path():
    src = (
        "from pathlib import Path\n"
        "p = Path('qa') / ('_mockup' + '_canonical') / 'suite-home-light-960x600.png'\n"
    )
    v = scan_qa_harness_source(src, "qa/capture_v8.py")
    assert "qa_dynamic_artifact_path_construction" in _kinds(v)


def test_qa_harness_detects_env_artifact_route():
    src = "import os\np = os.environ.get('NM_CANONICAL_IMAGE_PATH')\n"
    v = scan_qa_harness_source(src, "qa/capture_v8.py")
    assert "qa_env_artifact_route" in _kinds(v)


def test_qa_harness_detects_base64_decode():
    src = "import base64\npayload = base64.b64decode('AAAA')\n"
    v = scan_qa_harness_source(src, "tools/qa/audit_x.py")
    assert "qa_suspicious_base64_decode" in _kinds(v)


@pytest.mark.parametrize(
    "src, expected_kinds",
    [
        (
            "p = ''.join(chr(c) for c in [113,97,47,95,109])\n",
            {"qa_obfuscation_primitive"},
        ),
        (
            "payload = bytes([113, 97, 47, 95]).decode()\n",
            {"qa_literal_bytes_decode"},
        ),
        (
            "import subprocess\nsubprocess.run([chr(99)+chr(112), 'src', 'dst'])\n",
            {"qa_obfuscation_primitive", "qa_obfuscated_command_sink"},
        ),
        (
            "import os\ngetattr(os, 'system')('cp src dst')\n",
            {"qa_getattr_os_command"},
        ),
        (
            "import importlib\nimportlib.import_module('os')\n",
            {"qa_suspicious_importlib"},
        ),
    ],
)
def test_qa_harness_obfuscation_patterns_are_flagged(src, expected_kinds):
    v = scan_qa_harness_source(src, "tools/qa/audit_x.py")
    assert expected_kinds <= _kinds(v)


def test_qa_harness_allows_comparator_declared_canonical_source():
    src = "from pathlib import Path\n_DEFAULT_CANONICAL = Path('qa') / '_mockup_canonical'\n"
    v = scan_qa_harness_source(src, "qa/layered_visual_compare.py")
    assert v == []


def test_real_qa_harness_scan_is_clean():
    violations = scan_qa_harness_paths(list(QA_HARNESS_ROOTS))
    assert violations == [], f"anti-fraud QA harness violations: {[v.to_dict() for v in violations]}"


def test_main_qa_harness_mode_returns_zero(capsys):
    rc = main(["--mode", "qa-harness"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "qa-harness" in captured.out
    assert "CLEAN" in captured.out


def test_json_summary_identifies_full_default_scan(tmp_path, monkeypatch):
    monkeypatch.setattr("qa.anti_fraud_scan.scan_paths", lambda roots: [])
    monkeypatch.setattr("qa.anti_fraud_scan.scan_asset_canonical_identity", lambda: [])
    monkeypatch.setattr("qa.anti_fraud_scan.scan_qa_harness_paths", lambda roots: [])
    output = tmp_path / "antifraud.json"

    assert main(["--mode", "all", "--json", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "nm_suite.antifraud_summary.v1"
    assert payload["mode"] == "all"
    assert payload["scope"] == "default_full"
    assert payload["clean"] is True
    assert payload["count"] == 0
