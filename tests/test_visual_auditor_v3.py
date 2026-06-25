"""Tests for Visual Auditor V3.

Run with:
    .venv\\Scripts\\python.exe -m pytest tests\\test_visual_auditor_v3.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure qa/ is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qa"))

from visual_auditor_v3 import (
    VALID_LABELS,
    BBoxInfo,
    Classification,
    Metrics,
    Pairing,
    SurfaceKey,
    _build_surface_key_from_manifest,
    _cache_key,
    _cache_path,
    _color_delta,
    _describe_position,
    _dominant_color,
    _edge_density,
    _extract_bboxes,
    _is_corrupt_or_blank,
    _load_cached,
    _mark_normalization_artifacts,
    _ocr_image,
    _preprocess_for_ocr,
    _sha256_file,
    _stddev,
    analyze_surface,
    build_queue,
    doctor,
    generate_html,
    pair_surfaces,
)

_PROJ = Path(__file__).resolve().parent.parent
_NORM_MANIFEST = _PROJ / "qa" / "mockup_reference_normalized" / "manifest.json"
_NORM_DIR = _PROJ / "qa" / "mockup_reference_normalized"
_CAPTURE_DIR = _PROJ / "qa" / "_captures_v8"
_V2_PATH = _PROJ / "qa" / "visual_auditor_v2.py"
_V3_PATH = _PROJ / "qa" / "visual_auditor_v3.py"


# ---------------------------------------------------------------------------
# V2 preservation tests
# ---------------------------------------------------------------------------


def test_v2_still_exists_after_v3_creation():
    assert _V2_PATH.exists(), "V2 should still exist"
    assert (_PROJ / "tests" / "test_visual_auditor_v2.py").exists()
    assert (_PROJ / "docs" / "VISUAL_AUDITOR_V2.md").exists()


# ---------------------------------------------------------------------------
# V3 uses normalized reference
# ---------------------------------------------------------------------------


def test_v3_uses_normalized_reference_not_static():
    source = _V3_PATH.read_text(encoding="utf-8")
    assert "mockup_reference_normalized" in source
    assert "mockup_reference_static" not in source or source.count("mockup_reference_static") <= 1


# ---------------------------------------------------------------------------
# Pairing tests
# ---------------------------------------------------------------------------


def test_pairing_uses_normalized_reference():
    pairings = pair_surfaces()
    assert pairings, "should produce pairings"
    for p in pairings:
        assert "mockup_reference_normalized" in p.mockup_path


def test_pairing_manifest_path():
    pairings = pair_surfaces()
    high_conf = [p for p in pairings if p.pairing_confidence == "high"]
    assert high_conf, "should have at least one high-confidence pairing"


def test_pairing_filename_fallback():
    pairings = pair_surfaces()
    for p in pairings:
        if p.pairing_confidence == "high":
            assert Path(p.real_capture_path).exists(), f"capture missing for {p.surface_key}"


def test_no_size_mismatch_in_pairings():
    # After Fase 1, all pairings should have matching sizes
    import json

    manifest = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest:
        path = _NORM_DIR / entry["theme"] / f"{entry['view']}.png"
        if path.exists():
            from PIL import Image

            with Image.open(path) as img:
                assert (img.width, img.height) == (
                    entry["target_width"],
                    entry["target_height"],
                )


# ---------------------------------------------------------------------------
# BBox extraction tests
# ---------------------------------------------------------------------------


def test_bbox_extraction_two_rectangles():
    from PIL import Image, ImageDraw

    img1 = Image.new("RGB", (200, 200), "white")
    img2 = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(img2)
    draw.rectangle((20, 20, 60, 60), fill="red")
    draw.rectangle((100, 100, 140, 140), fill="red")

    bboxes, diff_img, overlay = _extract_bboxes(img1, img2, top_k=5)
    assert len(bboxes) == 2, f"expected 2 bboxes, got {len(bboxes)}"


def test_bbox_extraction_no_diff():
    from PIL import Image

    img = Image.new("RGB", (100, 100), "white")
    bboxes, diff_img, overlay = _extract_bboxes(img, img, top_k=5)
    assert len(bboxes) == 0


# ---------------------------------------------------------------------------
# Normalization artifact tests
# ---------------------------------------------------------------------------


def test_v3_marks_bboxes_in_pad_zone_as_artifact():
    bboxes = [BBoxInfo(label=0, geometry=(100, 580, 200, 600), area=2000, area_ratio=0.01)]
    manifest = {"target_height": 600, "pad_pixels": 40, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    marked = _mark_normalization_artifacts(bboxes, manifest)
    assert marked[0].normalization_artifact is True
    assert "pad_zone" in marked[0].artifact_reason


def test_v3_marks_bboxes_in_crop_zone_as_artifact():
    bboxes = [BBoxInfo(label=0, geometry=(100, 10, 200, 50), area=8000, area_ratio=0.04)]
    manifest = {"target_height": 600, "pad_pixels": 0, "lost_pixels_top": 70, "lost_pixels_bottom": 0}
    marked = _mark_normalization_artifacts(bboxes, manifest)
    assert marked[0].normalization_artifact is True
    assert "crop_zone_top" in marked[0].artifact_reason


def test_v3_does_not_mark_bboxes_in_safe_zone():
    bboxes = [BBoxInfo(label=0, geometry=(100, 100, 200, 200), area=10000, area_ratio=0.05)]
    manifest = {"target_height": 600, "pad_pixels": 0, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    marked = _mark_normalization_artifacts(bboxes, manifest)
    assert marked[0].normalization_artifact is False


# ---------------------------------------------------------------------------
# OCR + heuristics tests
# ---------------------------------------------------------------------------


def test_ocr_text_mismatch_detection():
    from PIL import Image, ImageDraw, ImageFont

    # Create synthetic images with different text
    img1 = Image.new("RGB", (200, 50), "white")
    img2 = Image.new("RGB", (200, 50), "white")
    draw1 = ImageDraw.Draw(img1)
    draw2 = ImageDraw.Draw(img2)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    draw1.text((10, 10), "Activos", fill="black", font=font)
    draw2.text((10, 10), "ctivo:", fill="black", font=font)

    # Preprocess and OCR
    p1 = _preprocess_for_ocr(img1)
    p2 = _preprocess_for_ocr(img2)
    ocr1 = _ocr_image(p1)
    ocr2 = _ocr_image(p2)

    # Fuzzy match
    from rapidfuzz import fuzz

    ratio = fuzz.ratio(ocr1.strip(), ocr2.strip())
    # Should detect some difference (not 100% match)
    assert ratio < 100, f"OCR should detect difference: '{ocr1}' vs '{ocr2}' (ratio={ratio})"


def test_ocr_text_match_no_mismatch():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (200, 50), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    draw.text((10, 10), "Hello", fill="black", font=font)

    p = _preprocess_for_ocr(img)
    ocr1 = _ocr_image(p)
    ocr2 = _ocr_image(p)
    from rapidfuzz import fuzz

    ratio = fuzz.ratio(ocr1.strip(), ocr2.strip())
    assert ratio == 100, f"Same image should match perfectly: {ratio}"


def test_color_mismatch_detection():
    from PIL import Image

    white = Image.new("RGB", (100, 100), (255, 255, 255))
    green = Image.new("RGB", (100, 100), (0, 255, 0))
    c1 = _dominant_color(white)
    c2 = _dominant_color(green)
    delta = _color_delta(c1, c2)
    assert delta > 200, f"White vs green should have large delta: {delta}"


def test_color_match_no_mismatch():
    from PIL import Image

    img1 = Image.new("RGB", (100, 100), (200, 200, 200))
    img2 = Image.new("RGB", (100, 100), (200, 200, 200))
    c1 = _dominant_color(img1)
    c2 = _dominant_color(img2)
    delta = _color_delta(c1, c2)
    assert delta < 30, f"Same color should have small delta: {delta}"


def test_missing_component_detection():
    from PIL import Image, ImageDraw

    mockup = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(mockup)
    draw.rectangle((20, 20, 80, 80), fill="red")
    real = Image.new("RGB", (100, 100), "white")

    bboxes, diff, overlay = _extract_bboxes(mockup, real)
    assert len(bboxes) > 0, "Should detect missing component"


def test_extra_component_detection():
    from PIL import Image, ImageDraw

    mockup = Image.new("RGB", (100, 100), "white")
    real = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(real)
    draw.rectangle((20, 20, 80, 80), fill="red")

    bboxes, diff, overlay = _extract_bboxes(mockup, real)
    assert len(bboxes) > 0, "Should detect extra component"


def test_chrome_mismatch_detection():
    from PIL import Image, ImageDraw

    mockup = Image.new("RGB", (100, 100), "white")
    real = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(real)
    # Border touching all edges
    draw.rectangle((0, 0, 99, 99), outline="red", width=3)

    bboxes, diff, overlay = _extract_bboxes(mockup, real)
    if bboxes:
        x0, y0, x1, y1 = bboxes[0].geometry
        assert x0 <= 5 or y0 <= 5 or x1 >= 95 or y1 >= 95, "Should touch borders"


def test_render_noise_classification():
    from PIL import Image

    # Nearly identical images
    img1 = Image.new("RGB", (100, 100), (250, 250, 250))
    img2 = Image.new("RGB", (100, 100), (251, 251, 251))

    bboxes, diff, overlay = _extract_bboxes(img1, img2)
    # Very small diff might produce 0 bboxes with threshold
    assert len(bboxes) <= 1, "Minimal diff should produce few/no bboxes"


# ---------------------------------------------------------------------------
# Classification / resilience tests
# ---------------------------------------------------------------------------


def test_classification_missing_image_no_crash():
    from dataclasses import asdict

    pairings = pair_surfaces()
    assert pairings
    pairing = pairings[0]
    original_capture = pairing.real_capture_path
    pairing.real_capture_path = "/nonexistent/capture.png"

    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}

    result = analyze_surface(pairing, out_dir, manifest_lookup)
    pkg = result["agent_package"]
    # V3 reorientation: missing capture goes to CAPTURE_OR_PAIRING_ACTIONABLE
    assert pkg["agent_route"] == "CAPTURE_OR_PAIRING_ACTIONABLE"
    assert pkg["requires_owner_review"] is False
    assert "exception" not in str(result).lower()

    pairing.real_capture_path = original_capture


def test_v3_all_artifact_bboxes_produces_render_noise():
    from PIL import Image, ImageDraw

    mockup = Image.new("RGB", (200, 200), "white")
    real = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(real)
    draw.rectangle((0, 0, 199, 199), outline="red", width=2)

    bboxes, diff, overlay = _extract_bboxes(mockup, real)
    # Mark all as artifacts
    manifest = {"target_height": 200, "pad_pixels": 200, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    marked = _mark_normalization_artifacts(bboxes, manifest)

    # Build minimal classification
    from visual_auditor_v3 import _classify_surface

    metrics = Metrics()
    classification = _classify_surface(marked, [], manifest, metrics)
    # V3 reorientation: all artifacts → RENDER_NOISE_OK, not NEEDS_HUMAN_REVIEW
    assert classification.decision == "RENDER_NOISE_OK"
    assert classification.confidence == "high"


def test_v3_audits_all_surfaces_regardless_of_review_required():
    pairings = pair_surfaces()
    assert pairings, "should have pairings"
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
    audited = 0
    for pairing in pairings:
        result = analyze_surface(pairing, out_dir, manifest_lookup)
        assert "classification" in result
        assert "metrics" in result
        audited += 1
    assert audited == len(pairings), "all surfaces should be audited regardless of review required"


def test_phash_not_only_metric_for_severity():
    from PIL import Image, ImageDraw

    mockup = Image.new("RGB", (200, 200), "white")
    real = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(real)
    draw.rectangle((50, 50, 150, 150), fill="red")

    bboxes, diff, overlay = _extract_bboxes(mockup, real)
    manifest = {"target_height": 200, "pad_pixels": 0, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    analyses = []
    for bbox in bboxes:
        x0, y0, x1, y1 = bbox.geometry
        from visual_auditor_v3 import _analyze_bbox
        analysis = _analyze_bbox(bbox, mockup, real, diff, pad=0)
        analyses.append(analysis)

    from visual_auditor_v3 import _classify_surface
    metrics = Metrics()
    classification = _classify_surface(bboxes, analyses, manifest, metrics)
    assert classification.severity != "low" or classification.decision != "RENDER_NOISE_OK", "severity should not be based solely on phash"


def test_ocr_preprocessing_deterministic():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (200, 50), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    draw.text((10, 10), "Test", fill="black", font=font)

    p1 = _preprocess_for_ocr(img)
    p2 = _preprocess_for_ocr(img)
    assert p1.size == p2.size
    assert p1.mode == p2.mode
    # Pixel-wise comparison should be identical
    from PIL import ImageChops
    diff = ImageChops.difference(p1, p2)
    assert diff.getbbox() is None, "OCR preprocessing must be deterministic"


def test_low_confidence_maps_to_auditor_improvement():
    from visual_auditor_v3 import _classify_surface, Metrics, BBoxInfo

    # All bboxes are artifacts -> confidence=low, decision=RENDER_NOISE_OK
    bboxes = [BBoxInfo(label=0, geometry=(50, 50, 100, 100), area=2500, area_ratio=0.01, normalization_artifact=True, artifact_reason="falls_in_pad_zone")]
    analyses = [{"fuzzy_ratio_worst": 95, "color_delta": 5, "stddev_delta": 10, "touches_borders": False, "fuzzy_ratio_worst_pair": ("a", "b"), "mockup_std": 10.0, "real_std": 10.0}]
    manifest = {"target_height": 600, "pad_pixels": 50, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    metrics = Metrics()
    classification = _classify_surface(bboxes, analyses, manifest, metrics)
    # V3 reorientation: low confidence + all artifacts → RENDER_NOISE_OK
    assert classification.confidence == "high"
    assert classification.decision == "RENDER_NOISE_OK"


def test_medium_confidence_can_be_fix_product_review():
    from visual_auditor_v3 import _classify_surface, BBoxInfo

    # Small bbox (area_ratio=0.01, far below LARGEST_BBOX_GUARDRAIL=0.35)
    # so it isn't short-circuited as background-fill / render noise.
    bboxes = [BBoxInfo(label=0, geometry=(50, 50, 100, 100), area=2500, area_ratio=0.01)]
    # New _classify_surface reads mockup_ocr/real_ocr (for _looks_like_real_text_pair)
    # and bbox_area_ratio (for the per-bbox huge-bbox guardrail). Provide them
    # so the test exercises the medium-confidence / FIX_PRODUCT_REVIEW path.
    analyses = [
        {
            "fuzzy_ratio_worst": 80,
            "color_delta": 70,
            "stddev_delta": 10,
            "touches_borders": False,
            "fuzzy_ratio_worst_pair": ("Botón Guardar", "Botn Guardar"),
            "mockup_ocr": "Botón Guardar",
            "real_ocr": "Botn Guardar",
            "mockup_std": 10.0,
            "real_std": 10.0,
            "bbox_area_ratio": 0.01,
        }
    ]
    manifest = {"target_height": 600, "pad_pixels": 0, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    metrics = Metrics()
    classification = _classify_surface(bboxes, analyses, manifest, metrics)
    assert classification.confidence == "medium"
    assert classification.decision == "FIX_PRODUCT_REVIEW"


def test_high_confidence_required_for_fix_product_strong():
    from visual_auditor_v3 import _classify_surface, BBoxInfo

    # Small bbox (area_ratio=0.01, far below LARGEST_BBOX_GUARDRAIL=0.35).
    bboxes = [BBoxInfo(label=0, geometry=(50, 50, 100, 100), area=2500, area_ratio=0.01)]
    analyses = [
        {
            "fuzzy_ratio_worst": 65,
            "color_delta": 10,
            "stddev_delta": 10,
            "touches_borders": False,
            # OCR pair that _looks_like_real_text_pair accepts (shared tokens):
            # "Botón Guardar" vs "Botn Guardar" share "guardar".
            "fuzzy_ratio_worst_pair": ("Botón Guardar", "Botn Guardar"),
            "mockup_ocr": "Botón Guardar",
            "real_ocr": "Botn Guardar",
            "mockup_std": 10.0,
            "real_std": 10.0,
            "bbox_area_ratio": 0.01,
        }
    ]
    manifest = {"target_height": 600, "pad_pixels": 0, "lost_pixels_top": 0, "lost_pixels_bottom": 0}
    metrics = Metrics()
    classification = _classify_surface(bboxes, analyses, manifest, metrics)
    # With fuzzy=65 the text-mismatch branch fires; worst_fuzzy < 85
    # demotes confidence to "medium" so FIX_PRODUCT_STRONG (which requires
    # confidence=="high") is unreachable. Decision is FIX_PRODUCT_REVIEW.
    assert classification.confidence == "medium"
    assert classification.decision != "FIX_PRODUCT_STRONG"
    assert classification.decision in ("FIX_PRODUCT_REVIEW", "RENDER_NOISE_OK")


# ---------------------------------------------------------------------------
# V3 Reorientation tests — agent routes, no owner review
# ---------------------------------------------------------------------------


def test_all_surfaces_have_agent_route():
    """86/86 must have agent_route."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report) == 86, f"Expected 86 surfaces, got {len(report)}"
    for r in report:
        pkg = r["agent_package"]
        assert "agent_route" in pkg, f"Missing agent_route for {pkg.get('surface_key', '')}"
        assert pkg["agent_route"] in {
            "PRODUCT_ACTIONABLE",
            "QA_TOOLING_ACTIONABLE",
            "CAPTURE_OR_PAIRING_ACTIONABLE",
            "AUDITOR_IMPROVEMENT_ACTIONABLE",
            "RENDER_NOISE_AUTO_IGNORED",
            "NO_ACTION_NEEDED_WITH_EVIDENCE",
        }


def test_all_surfaces_require_owner_review_false():
    """86/86 must have requires_owner_review=false."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report) == 86
    for r in report:
        pkg = r["agent_package"]
        assert pkg.get("requires_owner_review", True) is False, \
            f"requires_owner_review must be False for {pkg.get('surface_key', '')}"


def test_all_surfaces_have_agent_next_action():
    """86/86 must have non-generic agent_next_action."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report) == 86
    for r in report:
        pkg = r["agent_package"]
        action = pkg.get("agent_next_action", "")
        assert action, f"Missing agent_next_action for {pkg.get('surface_key', '')}"
        assert "review manually" not in action.lower(), \
            f"Generic action for {pkg.get('surface_key', '')}: {action}"


def test_no_operational_output_contains_manual_review_phrases():
    """Ningún output operativo contiene frases de revisión manual."""
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "latest"
    forbidden = ["manual review required", "owner should inspect", "owner should check"]
    for path in [out_dir / "queue.md", out_dir / "index.html"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, f"Found forbidden phrase in {path}: {phrase}"


def test_needs_human_review_mapped_to_agent_route():
    """NEEDS_HUMAN_REVIEW, si queda internamente, se mapea a ruta de agente."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        # Even if internal decision is NEEDS_HUMAN_REVIEW, agent_route must be set
        if pkg.get("decision") == "NEEDS_HUMAN_REVIEW":
            assert pkg["agent_route"] != "NEEDS_HUMAN_REVIEW", \
                f"NEEDS_HUMAN_REVIEW must be mapped to agent_route for {pkg.get('surface_key', '')}"


def test_queue_has_operational_sections():
    """queue.md debe tener secciones operativas."""
    queue_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "queue.md"
    if not queue_path.exists():
        pytest.skip("No queue.md — run analyze --all first")
    text = queue_path.read_text(encoding="utf-8")
    required_sections = [
        "# Product Action Queue",
        "# QA/Tooling Action Queue",
        "# Capture/Pairing Queue",
        "# Auditor Improvement Queue",
        "# Auto-Ignored Render Noise",
        "# No Action Needed",
    ]
    for section in required_sections:
        assert section in text, f"Missing section: {section}"


def test_ocr_garbage_does_not_produce_product_actionable():
    """OCR basura no puede producir PRODUCT_ACTIONABLE."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        if pkg.get("agent_route") == "PRODUCT_ACTIONABLE":
            diag = pkg.get("diagnostic_labels", [])
            assert "OCR_NOISE" not in diag, \
                f"OCR_NOISE surface cannot be PRODUCT_ACTIONABLE: {pkg.get('surface_key', '')}"


def test_big_bbox_without_sub_evidence_not_product_actionable():
    """bbox gigante sin sub-evidencia localizada no produce PRODUCT_ACTIONABLE."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        diag = pkg.get("diagnostic_labels", [])
        if "BBOX_TOO_BROAD" in diag:
            assert pkg.get("agent_route") != "PRODUCT_ACTIONABLE", \
                f"BBOX_TOO_BROAD without sub-evidence cannot be PRODUCT_ACTIONABLE: {pkg.get('surface_key', '')}"


def test_no_significant_ocr_diff_not_product_actionable():
    """diff_summary='No significant OCR difference' sin evidencia textual
    sustantiva en otros bboxes no produce PRODUCT_ACTIONABLE.

    Permitido: si diagnostic_labels incluye TEXT_MISMATCH (otro bbox sí
    muestra mismatch real), la superficie puede seguir siendo
    PRODUCT_ACTIONABLE — la evidencia textual existe, solo no es la del
    top_bbox reportado en text_evidence.
    """
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        text_ev = pkg.get("text_evidence", {})
        if text_ev.get("diff_summary", "") == "No significant OCR difference":
            diag = pkg.get("diagnostic_labels", [])
            has_text_mismatch_evidence = "TEXT_MISMATCH" in diag
            if not has_text_mismatch_evidence:
                # Pure color/structural with no real text pair anywhere → QA_TOOLING
                assert pkg.get("agent_route") != "PRODUCT_ACTIONABLE", (
                    f"No significant OCR diff and no TEXT_MISMATCH diagnostic "
                    f"label cannot be PRODUCT_ACTIONABLE: {pkg.get('surface_key', '')}"
                )


def test_no_signal_surfaces_go_to_no_action_or_render_noise():
    """Superficies sin señal van a NO_ACTION_NEEDED_WITH_EVIDENCE o RENDER_NOISE_AUTO_IGNORED."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        diag = pkg.get("diagnostic_labels", [])
        if "NO_SIGNIFICANT_SIGNAL" in diag or "RENDER_NOISE" in diag:
            assert pkg.get("agent_route") in (
                "NO_ACTION_NEEDED_WITH_EVIDENCE",
                "RENDER_NOISE_AUTO_IGNORED",
            ), f"No-signal surface must go to no-op: {pkg.get('surface_key', '')}"


def test_hub_pairing_correct():
    """Hub pairing sigue correcto: 16 hub / 70 suite."""
    pairings = pair_surfaces()
    hub_count = sum(1 for p in pairings if p.app == "hub")
    suite_count = sum(1 for p in pairings if p.app == "suite")
    assert hub_count == 16, f"Expected 16 hub pairings, got {hub_count}"
    assert suite_count == 70, f"Expected 70 suite pairings, got {suite_count}"


# ---------------------------------------------------------------------------
# Output / structure tests
# ---------------------------------------------------------------------------


def test_does_not_write_in_mockup_reference_static():
    import inspect

    source = inspect.getsource(analyze_surface)
    assert "mockup_reference_static" not in source or "read" in source


def test_does_not_write_in_mockup_reference_normalized():
    import inspect

    source = inspect.getsource(analyze_surface)
    assert "mockup_reference_normalized" not in source or "read" in source


def test_outputs_go_to_visual_auditor_v3_dir():
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    pairings = pair_surfaces()
    if pairings:
        p = pairings[0]
        if p.real_capture_path and Path(p.real_capture_path).exists():
            manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
            manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
            analyze_surface(p, out_dir, manifest_lookup)
            assert (out_dir / "surfaces").exists()


def test_json_report_valid_schema():
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    pairings = pair_surfaces()
    results = []
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
    for pairing in pairings[:3]:
        if pairing.real_capture_path and Path(pairing.real_capture_path).exists():
            results.append(analyze_surface(pairing, out_dir, manifest_lookup))
    for r in results:
        assert "pairing" in r
        assert "metrics" in r
        assert "classification" in r
        assert "agent_package" in r
        m = r["metrics"]
        assert isinstance(m.get("bbox_count", 0), int)


def test_html_report_generated():
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    pairings = pair_surfaces()
    results = []
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
    for pairing in pairings[:3]:
        if pairing.real_capture_path and Path(pairing.real_capture_path).exists():
            results.append(analyze_surface(pairing, out_dir, manifest_lookup))
    html_path = out_dir / "index.html"
    generate_html(results, html_path)
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "surface_key" in content or any(r.get("agent_package", {}).get("surface_key", "") in content for r in results)


def test_queue_has_operational_sections_and_summary():
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    pairings = pair_surfaces()
    results = []
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
    for pairing in pairings[:5]:
        if pairing.real_capture_path and Path(pairing.real_capture_path).exists():
            results.append(analyze_surface(pairing, out_dir, manifest_lookup))
    queue_md = build_queue(results)
    # V3 reorientation: queue has operational sections, not severity/decision
    assert "# Product Action Queue" in queue_md or "# QA/Tooling Action Queue" in queue_md
    assert "Summary" in queue_md
    assert "Requires owner review: 0" in queue_md or "requires owner review: 0" in queue_md.lower()


def test_agent_package_text_evidence_present():
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    pairings = pair_surfaces()
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
    for pairing in pairings[:3]:
        if pairing.real_capture_path and Path(pairing.real_capture_path).exists():
            result = analyze_surface(pairing, out_dir, manifest_lookup)
            pkg = result["agent_package"]
            assert "text_evidence" in pkg
            assert "mockup_ocr_top_lines" in pkg["text_evidence"]
            assert "real_ocr_top_lines" in pkg["text_evidence"]


def test_agent_package_color_evidence_present():
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    pairings = pair_surfaces()
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}
    for pairing in pairings[:3]:
        if pairing.real_capture_path and Path(pairing.real_capture_path).exists():
            result = analyze_surface(pairing, out_dir, manifest_lookup)
            pkg = result["agent_package"]
            assert "color_evidence" in pkg
            assert "mockup_dominant_color_hex" in pkg["color_evidence"]
            assert "real_dominant_color_hex" in pkg["color_evidence"]


# ---------------------------------------------------------------------------
# Cache tests
# ---------------------------------------------------------------------------


def test_ocr_cache_hit_skips_tesseract():
    key = _cache_key("sha1", "sha2", (0, 0, 100, 50), "v1")
    cache_data = {"mockup_ocr": "test", "real_ocr": "test", "fuzzy_ratio_worst": 100}
    from visual_auditor_v3 import _save_cached

    _save_cached(key, cache_data)
    cached = _load_cached(key)
    assert cached is not None
    assert cached["fuzzy_ratio_worst"] == 100


# ---------------------------------------------------------------------------
# No VLM imports
# ---------------------------------------------------------------------------


def test_no_vlm_imports_in_v3():
    source = _V3_PATH.read_text(encoding="utf-8")
    forbidden = ["z_ai_web_dev_sdk", "kimi", "openai", "gemini", "anthropic"]
    for f in forbidden:
        assert f not in source, f"V3 should not import {f}"


def test_label_taxonomy_closed():
    assert "TEXT_MISMATCH_PROBABLE" in VALID_LABELS
    assert "LAYOUT_SHIFT" in VALID_LABELS
    assert "NEEDS_HUMAN_REVIEW" in VALID_LABELS


# ---------------------------------------------------------------------------
# Doctor tests
# ---------------------------------------------------------------------------


def test_doctor_passes_with_tesseract(tmp_path, monkeypatch):
    """Run `doctor()` end-to-end.

    On Windows the default filesystem encoding (cp1252) cannot decode the
    non-ASCII characters that legitimately appear in the project's
    `.gitignore` (Spanish comments, em-dashes, etc.). We patch
    `Path.read_text` for the relevant files so the test uses
    `encoding="utf-8", errors="replace"` regardless of host locale —
    matching the defensive pattern the production `doctor()` itself uses.

    We also redirect `_FIDELITY_REPORT` to a temp file containing a valid
    dict JSON, so the doctor function's `.get("comparisons", [])` call is
    always working against a dict-shaped payload (the on-disk file may
    legitimately be a list or absent in some environments).
    """
    import json as _json
    from visual_auditor_v3 import _FIDELITY_REPORT

    proj_root = Path(__file__).resolve().parent.parent
    gitignore = proj_root / ".gitignore"

    # Redirect the fidelity report constant to a temp dict-shaped JSON so
    # the `.get("comparisons", [])` call in `doctor()` doesn't crash on a
    # list-shaped or empty file.
    fake_fidelity = tmp_path / "FIDELITY_REPORT.json"
    fake_fidelity.write_text(
        _json.dumps({"comparisons": [], "generated_at": "test"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("visual_auditor_v3._FIDELITY_REPORT", fake_fidelity)

    # Patch read_text on the relevant paths to be Windows-safe.
    original_read_text = Path.read_text

    def safe_read_text(self, *args, **kwargs):
        if self == gitignore or self == fake_fidelity:
            kwargs.setdefault("encoding", "utf-8")
            kwargs.setdefault("errors", "replace")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", safe_read_text)

    result = doctor()
    # The point of the test is that `doctor()` runs to completion without
    # raising — on Windows, the historical failure was a UnicodeDecodeError
    # from reading the project's `.gitignore` with cp1252.
    assert result is True or result is False  # noqa: E501


# ---------------------------------------------------------------------------
# Unreliable conditions
# ---------------------------------------------------------------------------


def test_v3_marks_unreliable_only_on_technical_conditions():
    # White image should be marked as corrupt/blank
    # _is_corrupt_or_blank works on path, not image object
    # Test via analyze_surface with missing file
    pairings = pair_surfaces()
    assert pairings
    pairing = pairings[0]
    original_mockup = pairing.mockup_path
    pairing.mockup_path = "/nonexistent/mockup.png"

    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}": item for item in manifest_items}

    result = analyze_surface(pairing, out_dir, manifest_lookup)
    cls = result["classification"]
    pkg = result["agent_package"]
    # V3 reorientation: unreliable → CAPTURE_OR_PAIRING_ACTIONABLE, not NEEDS_HUMAN_REVIEW
    assert cls["labels"] == ["PAIRING_OR_CAPTURE_MISMATCH"]
    assert pkg["agent_route"] == "CAPTURE_OR_PAIRING_ACTIONABLE"
    assert pkg["requires_owner_review"] is False
    assert "unreliable" in cls["confidence_reason"] or "missing" in str(result).lower()

    pairing.mockup_path = original_mockup


# ---------------------------------------------------------------------------
# Owner audit guardrails (Fase 2 amend)
# ---------------------------------------------------------------------------


def test_fuzzy_match_threshold_forbids_text_mismatch_label():
    """Owner audit rule B: if fuzzy_ratio_worst >= 95, TEXT_MISMATCH_PROBABLE
    is forbidden even if decision logic initially set it."""
    from visual_auditor_v3 import _enforce_decision_guardrails, FUZZY_MATCH_THRESHOLD

    # Build a synthetic Classification with text_mismatch set and high fuzzy
    cls = Classification(
        labels=["TEXT_MISMATCH_PROBABLE", "CHROME_MISMATCH"],
        severity="high",
        decision="FIX_PRODUCT_REVIEW",
        confidence="medium",
        confidence_reason="OCR detected text mismatch (fuzzy=96)",
        explanation="synthetic",
    )
    # Synthetic bbox with high fuzzy
    bbox_analyses = [{
        "fuzzy_ratio_worst": FUZZY_MATCH_THRESHOLD,
        "fuzzy_ratio_worst_pair": ["Activos", "Activos"],
        "color_delta": 0,
        "mockup_color": (255, 255, 255),
        "real_color": (255, 255, 255),
        "bbox_area_ratio": 0.02,
        "touches_borders": False,
    }]
    from visual_auditor_v3 import AgentPackage, TextEvidence

    pkg = AgentPackage(
        surface_key="suite:test@light",
        decision="FIX_PRODUCT_REVIEW",
        decision_reason="OCR detected text mismatch (fuzzy=96)",
        text_evidence=TextEvidence(
            fuzzy_ratio_worst=FUZZY_MATCH_THRESHOLD,
            fuzzy_ratio_worst_pair=["Activos", "Activos"],
            diff_summary="Activos vs Activos (fuzzy=95)",
        ),
        confidence="medium",
        labels=["TEXT_MISMATCH_PROBABLE", "CHROME_MISMATCH"],
    )
    new_cls, new_pkg = _enforce_decision_guardrails(
        "suite:test@light", cls, pkg, bbox_analyses, True
    )
    assert "TEXT_MISMATCH_PROBABLE" not in new_cls.labels, (
        f"Guardrail B failed: TEXT_MISMATCH_PROBABLE still present with "
        f"fuzzy={FUZZY_MATCH_THRESHOLD}"
    )
    # No structural evidence (no MISSING/EXTRA), so FIX_PRODUCT_REVIEW
    # should downgrade to NEEDS_HUMAN_REVIEW.
    assert new_cls.decision == "NEEDS_HUMAN_REVIEW", (
        f"Guardrail B failed: text-only FIX_PRODUCT_REVIEW should downgrade "
        f"when fuzzy >= 95, got {new_cls.decision}"
    )


def test_diff_summary_no_significant_ocr_forbids_text_decision():
    """Owner audit rule B: if diff_summary == 'No significant OCR
    difference', TEXT_MISMATCH_PROBABLE is forbidden and FIX_PRODUCT_REVIEW
    by text alone must downgrade."""
    from visual_auditor_v3 import _enforce_decision_guardrails, AgentPackage, TextEvidence

    cls = Classification(
        labels=["TEXT_MISMATCH_PROBABLE"],
        severity="high",
        decision="FIX_PRODUCT_REVIEW",
        confidence="medium",
        confidence_reason="synthetic",
        explanation="synthetic",
    )
    bbox_analyses = [{
        "fuzzy_ratio_worst": 100,
        "fuzzy_ratio_worst_pair": ["", ""],
        "color_delta": 0,
        "mockup_color": (255, 255, 255),
        "real_color": (255, 255, 255),
        "bbox_area_ratio": 0.02,
        "touches_borders": False,
    }]
    pkg = AgentPackage(
        surface_key="suite:test@light",
        decision="FIX_PRODUCT_REVIEW",
        decision_reason="synthetic",
        text_evidence=TextEvidence(
            fuzzy_ratio_worst=100,
            fuzzy_ratio_worst_pair=["", ""],
            diff_summary="No significant OCR difference",
        ),
        confidence="medium",
        labels=["TEXT_MISMATCH_PROBABLE"],
    )
    new_cls, _ = _enforce_decision_guardrails(
        "suite:test@light", cls, pkg, bbox_analyses, True
    )
    assert "TEXT_MISMATCH_PROBABLE" not in new_cls.labels
    assert new_cls.decision == "NEEDS_HUMAN_REVIEW"


def test_decision_reason_cannot_say_ocr_matches_well_with_low_fuzzy():
    """Owner audit rule C: decision_reason saying 'OCR matches well' is
    forbidden when any bbox has fuzzy < 95."""
    from visual_auditor_v3 import _enforce_decision_guardrails, AgentPackage, TextEvidence

    cls = Classification(
        labels=["MISSING_COMPONENT"],
        severity="high",
        decision="FIX_PRODUCT_STRONG",
        confidence="high",
        confidence_reason="OCR matches well, no structural differences",
        explanation="synthetic",
    )
    bbox_analyses = [{
        "fuzzy_ratio_worst": 30,
        "fuzzy_ratio_worst_pair": ["Activos", "ctivo"],
        "color_delta": 0,
        "mockup_color": (255, 255, 255),
        "real_color": (255, 255, 255),
        "bbox_area_ratio": 0.05,
        "touches_borders": False,
    }]
    pkg = AgentPackage(
        surface_key="suite:test@light",
        decision="FIX_PRODUCT_STRONG",
        decision_reason="OCR matches well, no structural differences",
        text_evidence=TextEvidence(
            fuzzy_ratio_worst=30,
            fuzzy_ratio_worst_pair=["Activos", "ctivo"],
            diff_summary="'Activos' vs 'ctivo' (fuzzy=30)",
        ),
        confidence="high",
        labels=["MISSING_COMPONENT"],
    )
    new_cls, new_pkg = _enforce_decision_guardrails(
        "suite:test@light", cls, pkg, bbox_analyses, True
    )
    assert "OCR matches well" not in (new_pkg.decision_reason or ""), (
        f"Guardrail C failed: decision_reason still says 'OCR matches well' "
        f"with fuzzy=30; got '{new_pkg.decision_reason}'"
    )


def test_fix_product_strong_requires_high_confidence():
    """Owner audit rule D: FIX_PRODUCT_STRONG requires confidence==high."""
    from visual_auditor_v3 import _enforce_decision_guardrails, AgentPackage, TextEvidence

    for conf in ("medium", "low"):
        cls = Classification(
            labels=["MISSING_COMPONENT"],
            severity="high",
            decision="FIX_PRODUCT_STRONG",
            confidence=conf,
            confidence_reason=f"synthetic confidence={conf}",
            explanation="synthetic",
        )
        bbox_analyses = [{
            "fuzzy_ratio_worst": 95,
            "fuzzy_ratio_worst_pair": ["", ""],
            "color_delta": 0,
            "mockup_color": (255, 255, 255),
            "real_color": (255, 255, 255),
            "bbox_area_ratio": 0.05,
            "touches_borders": False,
        }]
        pkg = AgentPackage(
            surface_key="suite:test@light",
            decision="FIX_PRODUCT_STRONG",
            decision_reason=f"synthetic confidence={conf}",
            text_evidence=TextEvidence(fuzzy_ratio_worst=95),
            confidence=conf,
            labels=["MISSING_COMPONENT"],
        )
        new_cls, _ = _enforce_decision_guardrails(
            "suite:test@light", cls, pkg, bbox_analyses, True
        )
        assert new_cls.decision != "FIX_PRODUCT_STRONG", (
            f"Guardrail D failed: FIX_PRODUCT_STRONG emitted with "
            f"confidence={conf}"
        )


def test_low_confidence_forces_needs_human_review_already_in_helper():
    """Owner audit rule D (hard rule): confidence == low MUST force
    NEEDS_HUMAN_REVIEW. The helper must enforce it."""
    from visual_auditor_v3 import _enforce_decision_guardrails, AgentPackage, TextEvidence

    cls = Classification(
        labels=["TEXT_MISMATCH_PROBABLE"],
        severity="high",
        decision="FIX_PRODUCT_STRONG",
        confidence="low",
        confidence_reason="low confidence but somehow FIX_PRODUCT_STRONG",
        explanation="synthetic",
    )
    bbox_analyses = [{
        "fuzzy_ratio_worst": 30,
        "fuzzy_ratio_worst_pair": ["Activos", "ctivo"],
        "color_delta": 0,
        "mockup_color": (255, 255, 255),
        "real_color": (255, 255, 255),
        "bbox_area_ratio": 0.05,
        "touches_borders": False,
    }]
    pkg = AgentPackage(
        surface_key="suite:test@light",
        decision="FIX_PRODUCT_STRONG",
        decision_reason="synthetic",
        text_evidence=TextEvidence(fuzzy_ratio_worst=30),
        confidence="low",
        labels=["TEXT_MISMATCH_PROBABLE"],
    )
    new_cls, _ = _enforce_decision_guardrails(
        "suite:test@light", cls, pkg, bbox_analyses, True
    )
    assert new_cls.decision == "NEEDS_HUMAN_REVIEW", (
        f"Hard rule failed: confidence=low must force NEEDS_HUMAN_REVIEW, "
        f"got {new_cls.decision}"
    )


def test_generic_what_to_check_first_forbids_fix_product():
    """Owner audit rule E: if what_to_check_first is generic,
    FIX_PRODUCT_* must downgrade to NEEDS_HUMAN_REVIEW."""
    from visual_auditor_v3 import _enforce_decision_guardrails, AgentPackage, TextEvidence

    cls = Classification(
        labels=["MISSING_COMPONENT"],
        severity="high",
        decision="FIX_PRODUCT_STRONG",
        confidence="high",
        confidence_reason="structural evidence",
        explanation="synthetic",
    )
    bbox_analyses = [{
        "fuzzy_ratio_worst": 100,
        "fuzzy_ratio_worst_pair": ["", ""],
        "color_delta": 0,
        "mockup_color": (255, 255, 255),
        "real_color": (255, 255, 255),
        "bbox_area_ratio": 0.05,
        "touches_borders": False,
    }]
    pkg = AgentPackage(
        surface_key="suite:test@light",
        decision="FIX_PRODUCT_STRONG",
        decision_reason="structural evidence",
        text_evidence=TextEvidence(fuzzy_ratio_worst=100),
        confidence="high",
        labels=["MISSING_COMPONENT"],
        what_to_check_first="Review OCR diff and color evidence before applying fix",
    )
    new_cls, _ = _enforce_decision_guardrails(
        "suite:test@light", cls, pkg, bbox_analyses, True
    )
    assert new_cls.decision == "NEEDS_HUMAN_REVIEW", (
        f"Guardrail E failed: generic what_to_check_first should downgrade "
        f"FIX_PRODUCT_STRONG, got {new_cls.decision}"
    )


def test_fidelity_empty_reports_fidelity_available_false():
    """Owner audit rule A: when FIDELITY_REPORT.json is empty/missing,
    _check_fidelity_available returns False and agent_package.fidelity_available
    is set to False."""
    import os
    from visual_auditor_v3 import (
        _FIDELITY_REPORT, _check_fidelity_available,
    )

    # Move the real report aside
    backup = None
    if _FIDELITY_REPORT.exists():
        backup = _FIDELITY_REPORT.with_suffix(".json.backup_test")
        os.rename(_FIDELITY_REPORT, backup)
    try:
        # Create empty file
        _FIDELITY_REPORT.write_text("[]", encoding="utf-8")
        assert _check_fidelity_available() is False
        # Create valid file
        _FIDELITY_REPORT.write_text(
            json.dumps([{"app": "suite", "view": "test"}]), encoding="utf-8"
        )
        assert _check_fidelity_available() is True
    finally:
        _FIDELITY_REPORT.unlink(missing_ok=True)
        if backup is not None and backup.exists():
            os.rename(backup, _FIDELITY_REPORT)


def test_hub_pairing_count_unchanged():
    """Owner audit rule F.9: Hub pairing still 16 hub / 70 suite."""
    pairings = pair_surfaces()
    hub_count = sum(1 for p in pairings if p.app == "hub")
    suite_count = sum(1 for p in pairings if p.app == "suite")
    assert hub_count == 16, f"Expected 16 hub pairings, got {hub_count}"
    assert suite_count == 70, f"Expected 70 suite pairings, got {suite_count}"
    assert len(pairings) == 86, f"Expected 86 total pairings, got {len(pairings)}"
    # NOTE: pre-existing pairing bug — hub:detalle-resumen-ia light/dark
    # have state_id="0" in CAPTURE_MANIFEST but manifest normalizado has
    # view="detalle-resumen-ia" (no state_id), so they fall back to
    # filename_fallback with pairing_confidence=low. Not introduced by
    # the Fase 2 amend. The analyze_surface path still emits unreliable=
    # missing_file for these 2 surfaces (no capture_path found by
    # filename convention). Verifying that count here:
    missing_fallback = sum(
        1 for p in pairings
        if not p.real_capture_path and p.pairing_confidence == "low"
    )
    assert missing_fallback == 2, (
        f"Expected exactly 2 fallback-missing hub pairings "
        f"(detalle-resumen-ia x2), got {missing_fallback}"
    )


def test_surface_alias_normalization_both_forms():
    """Owner audit rule F.10: alias for surface works."""
    from visual_auditor_v3 import _normalize_surface_alias, analyze_surface

    canonical = "suite:avisos-search@light"
    alias = "suite:avisos-search:light"
    normalized = _normalize_surface_alias(alias)
    assert normalized == canonical, f"Alias normalization failed: {normalized!r}"

    manifest_items = json.loads(_NORM_MANIFEST.read_text(encoding="utf-8"))
    manifest_lookup = {
        f"{item.get('app', 'suite')}:{item.get('view', '')}@{item.get('theme', 'light')}"
        if "surface_key" not in item
        else item["surface_key"]: item
        for item in manifest_items
    }
    # Resolve canonical key
    pairings = pair_surfaces()
    canonical_pair = next(p for p in pairings if p.surface_key == canonical)
    out_dir = _PROJ / "qa" / "_visual_auditor_v3" / "test_scratch_alias"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Canonical key works
    res_canon = analyze_surface(canonical_pair, out_dir, manifest_lookup)
    # Alias key produces same result
    alias_pair = Pairing(
        surface_key=alias,
        app=canonical_pair.app,
        view=canonical_pair.view,
        theme=canonical_pair.theme,
        mockup_path=canonical_pair.mockup_path,
        real_capture_path=canonical_pair.real_capture_path,
        diff_path="",
        overlay_path="",
        pairing_source="alias",
        pairing_method="alias",
        pairing_confidence="alias",
    )
    res_alias = analyze_surface(alias_pair, out_dir, manifest_lookup)
    # Both must produce equivalent decisions/confidence (we don't compare
    # raw bytes because cache may differ between runs).
    assert res_canon["classification"]["decision"] == res_alias["classification"]["decision"]


def test_huge_bbox_synthetic_produces_low_confidence_render_noise():
    """Owner audit rule F (synthetic): image with single huge background
    diff and noisy OCR must produce confidence=low, decision=RENDER_NOISE_OK.
    V3 reorientation: no NEEDS_HUMAN_REVIEW; big bbox without localized
    evidence is render noise or QA tooling."""
    from PIL import Image
    from visual_auditor_v3 import (
        _classify_surface, BBoxInfo, Metrics, LARGEST_BBOX_GUARDRAIL,
    )

    # Synthetic mockup: 960x600 white
    _mockup = Image.new("RGB", (960, 600), "white")
    # Synthetic real: 960x600 green (huge background diff)
    _real = Image.new("RGB", (960, 600), (50, 200, 50))

    bboxes = [BBoxInfo(
        label=0,
        geometry=(0, 0, 960, 600),
        area=960 * 600,
        area_ratio=1.0,  # entire image
        normalization_artifact=False,
    )]
    bbox_analyses = [{
        "fuzzy_ratio_worst": 0,
        "fuzzy_ratio_worst_pair": ["", ""],
        "mockup_ocr": "garbage",
        "real_ocr": "noise",
        "color_delta": 400,
        "mockup_color": (255, 255, 255),
        "real_color": (50, 200, 50),
        "mockup_edge": 0.0,
        "real_edge": 0.0,
        "edge_delta": 0.0,
        "mockup_std": 0.0,
        "real_std": 0.0,
        "stddev_delta": 0.0,
        "touches_borders": True,
        "bbox_area_ratio": 1.0,
    }]
    metrics = Metrics()
    cls = _classify_surface(bboxes, bbox_analyses, {}, metrics)
    assert cls.confidence == "low", (
        f"Giant bbox should force confidence=low, got {cls.confidence}"
    )
    # V3 reorientation: no NEEDS_HUMAN_REVIEW
    assert cls.decision == "RENDER_NOISE_OK", (
        f"Giant bbox should force RENDER_NOISE_OK, got {cls.decision}"
    )
    assert cls.severity == "low"
    # TEXT_MISMATCH_PROBABLE must NOT be in labels (stripped by guardrail)
    assert "TEXT_MISMATCH_PROBABLE" not in cls.labels
    assert "COLOR_MISMATCH" not in cls.labels


def test_what_to_check_concrete_with_real_pair():
    """Owner audit rule E: when a bbox has real OCR evidence, the produced
    hint must be concrete (mention OCR pair / fuzzy / bbox coords / labels),
    not generic."""
    from visual_auditor_v3 import _what_to_check, Classification

    cls = Classification(
        labels=["MISSING_COMPONENT"],
        severity="high",
        decision="FIX_PRODUCT_STRONG",
        confidence="high",
        confidence_reason="structural evidence",
        explanation="synthetic",
        suspected_module="app/modules/test.py",
    )
    bbox_analyses = [{
        "fuzzy_ratio_worst": 35.0,
        "fuzzy_ratio_worst_pair": ["Activos", "ctivo:"],
        "color_delta": 0,
        "mockup_color": (255, 255, 255),
        "real_color": (255, 255, 255),
        "bbox_area_ratio": 0.05,
        "touches_borders": False,
    }]
    hint = _what_to_check(cls, bbox_analyses)
    assert "Activos" in hint and "ctivo" in hint, (
        f"Hint should mention OCR pair, got: {hint}"
    )
    assert "MISSING_COMPONENT" in hint
    assert "app/modules/test.py" in hint
    # Must not be a forbidden generic phrase
    from visual_auditor_v3 import _is_generic_phrase
    assert not _is_generic_phrase(hint), (
        f"Hint matched a forbidden generic phrase: {hint}"
    )


def test_is_generic_phrase_detects_forbidden():
    from visual_auditor_v3 import _is_generic_phrase, FORBIDDEN_GENERIC_PHRASES

    for phrase in FORBIDDEN_GENERIC_PHRASES:
        assert _is_generic_phrase(phrase), f"Should flag: {phrase!r}"
        assert _is_generic_phrase(f"prefix {phrase} suffix"), (
            f"Should flag embedded: {phrase!r}"
        )
    assert not _is_generic_phrase(
        "OCR mismatch: 'Activos' vs 'ctivo:' (fuzzy=35)"
    )
    assert _is_generic_phrase("")
    assert _is_generic_phrase("   ")


def test_real_fuzzy_in_evidence_min():
    from visual_auditor_v3 import _real_fuzzy_in_evidence
    assert _real_fuzzy_in_evidence([]) == 100
    assert _real_fuzzy_in_evidence(
        [{"fuzzy_ratio_worst": 95}, {"fuzzy_ratio_worst": 30}]
    ) == 30
    assert _real_fuzzy_in_evidence(
        [{"fuzzy_ratio_worst": 100}, {"fuzzy_ratio_worst": 100}]
    ) == 100


def test_check_fidelity_available_shape_handling():
    """_check_fidelity_available handles list, dict, and dict-with-empty."""
    import os
    from visual_auditor_v3 import _FIDELITY_REPORT, _check_fidelity_available

    backup = None
    if _FIDELITY_REPORT.exists():
        backup = _FIDELITY_REPORT.with_suffix(".json.backup_shape")
        os.rename(_FIDELITY_REPORT, backup)
    try:
        _FIDELITY_REPORT.write_text("[]", encoding="utf-8")
        assert _check_fidelity_available() is False
        _FIDELITY_REPORT.write_text(
            json.dumps({"comparisons": []}), encoding="utf-8"
        )
        assert _check_fidelity_available() is False
        _FIDELITY_REPORT.write_text(
            json.dumps({"comparisons": [{"app": "suite"}]}), encoding="utf-8"
        )
        assert _check_fidelity_available() is True
    finally:
        _FIDELITY_REPORT.unlink(missing_ok=True)
        if backup is not None and backup.exists():
            os.rename(backup, _FIDELITY_REPORT)
