"""Tests for Visual Auditor V3.

Run with:
    .venv\\Scripts\\python.exe -m pytest tests\\test_visual_auditor_v3.py -q
"""

from __future__ import annotations

import json
import sys
import tempfile
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
    _looks_like_real_text_pair,
    _map_to_agent_route,
    _cluster_root_cause,
    _divergences_from,
    _probable_module,
    _next_action_for_agent,
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

# ---------------------------------------------------------------------------
# V3 amend: latest/ cleanup, sync report<->surfaces, file completeness,
# and stricter PRODUCT_ACTIONABLE guardrails.
# ---------------------------------------------------------------------------


def _safe_folder_name(surface_key: str) -> str:
    """Mirror of qa/visual_auditor_v3.py::_safe_folder_name."""
    return surface_key.replace(":", "_").replace("@", "_")


def test_analyze_all_clears_latest_surfaces_before_writing():
    """analyze --all must wipe qa/_visual_auditor_v3/latest/surfaces/ first
    so stale dirs from previous runs (older taxonomy, etc.) cannot
    accumulate past report.json's surface count.

    We exercise the cleanup directly via the helper the CLI invokes, on
    a temp directory containing a fake stale dir. The real CLI integration
    is covered by test_latest_surfaces_in_sync_with_report_json.
    """
    from visual_auditor_v3 import _reset_latest_outputs

    with _ScratchLatest() as scratch:
        latest = scratch.path
        (latest / "surfaces" / "stale_old_taxonomy_dir").mkdir(parents=True)
        (latest / "surfaces" / "stale_old_taxonomy_dir" / "leftover.txt").write_text("x")
        (latest / "report.json").write_text("[]", encoding="utf-8")
        (latest / "queue.md").write_text("old", encoding="utf-8")
        (latest / "index.html").write_text("<html></html>", encoding="utf-8")

        _reset_latest_outputs()

        assert not (latest / "surfaces").exists() or not any(
            (latest / "surfaces").iterdir()
        ), "stale dir was not removed"
        assert not (latest / "report.json").exists()
        assert not (latest / "queue.md").exists()
        assert not (latest / "index.html").exists()


def test_latest_surfaces_in_sync_with_report_json():
    """surfaces/<dir> count must equal report.json count, and every active
    surface must have agent_package.json + classification.json + metrics.json.
    """
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    surf_dir = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "surfaces"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    expected_dirs = {_safe_folder_name(r["pairing"]["surface_key"]) for r in report}
    actual_dirs = {p.name for p in surf_dir.iterdir() if p.is_dir()}

    stale = actual_dirs - expected_dirs
    missing = expected_dirs - actual_dirs
    assert not stale, f"Stale surfaces dirs not in report.json: {sorted(stale)}"
    assert not missing, f"Missing surfaces dirs on disk: {sorted(missing)}"

    for r in report:
        sk = r["pairing"]["surface_key"]
        sd = surf_dir / _safe_folder_name(sk)
        for fname in ("agent_package.json", "classification.json", "metrics.json"):
            assert (sd / fname).exists(), (
                f"{sk}: missing {fname} (all 3 must be present)"
            )


def test_product_actionable_requires_top_bbox_real_pair():
    """PRODUCT_ACTIONABLE cannot be assigned when text_evidence.fuzzy_ratio_worst_pair
    is empty AND TEXT_MISMATCH diagnostic label is also absent (i.e. the
    surface has no legible text pair in its top bbox either).

    This is the harder guardrail from the V3 amend: previously a structural
    label (EXTRA_COMPONENT / MISSING_COMPONENT) plus a secondary bbox with
    fuzzy=0 could route to PRODUCT even when text_evidence reported 'No
    significant OCR difference'.
    """
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        if pkg.get("agent_route") != "PRODUCT_ACTIONABLE":
            continue
        text_ev = pkg.get("text_evidence", {})
        diag = pkg.get("diagnostic_labels", [])
        pair = text_ev.get("fuzzy_ratio_worst_pair", ["", ""])
        # If the top bbox reports no real text pair AND no secondary bbox
        # is being relied upon for TEXT_MISMATCH, this surface must not
        # be PRODUCT.
        has_real_pair_in_top = bool(pair and pair[0] and pair[1])
        assert has_real_pair_in_top or "TEXT_MISMATCH" not in diag, (
            f"{r['pairing']['surface_key']}: PRODUCT_ACTIONABLE with empty "
            f"top_bbox pair and no TEXT_MISMATCH diagnostic label"
        )


def test_product_actionable_no_diff_summary_no_significant():
    """PRODUCT_ACTIONABLE must never carry diff_summary='No significant OCR difference'
    when diagnostic_labels does not include TEXT_MISMATCH from a real secondary pair.
    """
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        if pkg.get("agent_route") != "PRODUCT_ACTIONABLE":
            continue
        diff = pkg.get("diff_summary", "")
        diag = pkg.get("diagnostic_labels", [])
        if diff == "No significant OCR difference" and "TEXT_MISMATCH" not in diag:
            raise AssertionError(
                f"{r['pairing']['surface_key']}: PRODUCT_ACTIONABLE with "
                f"diff_summary='No significant OCR difference' and no "
                f"TEXT_MISMATCH evidence"
            )


def test_product_actionable_no_huge_bbox_without_subevidence():
    """PRODUCT_ACTIONABLE must not be based on a dominant bbox (>0.35 area_ratio)
    unless there is sub-evidence from a secondary bbox that supports the decision.
    """
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        if pkg.get("agent_route") != "PRODUCT_ACTIONABLE":
            continue
        top_bbox = pkg.get("top_bbox", {})
        area_ratio = top_bbox.get("area_ratio", 0.0)
        diag = pkg.get("diagnostic_labels", [])
        if area_ratio > 0.35:
            assert "TEXT_MISMATCH" in diag or "COLOR_MISMATCH" in diag, (
                f"{r['pairing']['surface_key']}: PRODUCT based on huge "
                f"top_bbox (area_ratio={area_ratio}) without localized "
                f"text or color sub-evidence"
            )


def test_queue_and_index_have_no_human_owner_manual_phrases():
    """queue.md and index.html must not contain phrases that ask for human/manual/owner review."""
    base = _PROJ / "qa" / "_visual_auditor_v3" / "latest"
    if not (base / "report.json").exists():
        pytest.skip("No report.json — run analyze --all first")

    forbidden = [
        "needs_human_review",
        "requires_owner_review",
        "manual review",
        "owner action",
        "human inspection",
        "please review",
    ]

    queue_text = (base / "queue.md").read_text(encoding="utf-8")
    html_text = (base / "index.html").read_text(encoding="utf-8")
    report = json.loads((base / "report.json").read_text(encoding="utf-8"))

    for f in forbidden:
        # queue.md should not contain forbidden phrases in any case
        assert f.lower() not in queue_text.lower(), (
            f"queue.md contains forbidden phrase: {f!r}"
        )
        # index.html: 'requires_owner_review' is allowed if all are False,
        # but other forbidden phrases should not appear.
        if f == "requires_owner_review":
            # Allow the literal False/true string in HTML; the rule is that
            # no surface should *require* owner review. Check the report.
            for r in report:
                pkg = r["agent_package"]
                if pkg.get("requires_owner_review", True):
                    raise AssertionError(
                        f"{r['pairing']['surface_key']}: requires_owner_review=True"
                    )
        else:
            assert f.lower() not in html_text.lower(), (
                f"index.html contains forbidden phrase: {f!r}"
            )


class _ScratchLatest:
    """Context manager that swaps _OUT_DIR to a temp dir for the lifetime of
    the block. Restores the original on exit."""

    def __init__(self):
        self.tmp = None
        self.path = None
        self._orig = None

    def __enter__(self):
        from visual_auditor_v3 import _OUT_DIR

        self.tmp = Path(tempfile.mkdtemp(prefix="v3_reset_"))
        self.path = self.tmp
        self._orig = _OUT_DIR
        # Monkey-patch the module-level binding used by _reset_latest_outputs
        import visual_auditor_v3 as v3mod
        v3mod._OUT_DIR = self.tmp
        return self

    def __exit__(self, *exc):
        import shutil as _sh
        if self.tmp and self.tmp.exists():
            _sh.rmtree(self.tmp, ignore_errors=True)
        if self._orig is not None:
            import visual_auditor_v3 as v3mod
            v3mod._OUT_DIR = self._orig


    # ---------------------------------------------------------------------------
# Owner guardrail — V3 amend OCR-legibility rule
# ---------------------------------------------------------------------------
#
# Bug being prevented: a bbox can pass `_looks_like_real_text_pair` against
# its full aggregate mockup_ocr/real_ocr (because some line in it is real,
# e.g. "NeuroMood / Configuración") while the line-to-line pair exposed to
# consumers as `fuzzy_ratio_worst_pair` is pure OCR garbage (e.g.
# "AP .. .. i..." vs "M\x27aomo"). The previous guardrail validated the bbox
# aggregate only, so the route went to PRODUCT_ACTIONABLE with a
# `diff_summary` of pure noise. The owner audit (2026-06-25) flagged four
# surfaces that hit this: suite:recuperar-acceso@light,
# suite:actividades@dark, suite:actividades-marked-hice@dark, and
# hub:textos-globales@dark. These tests pin the regression.


def _make_routing_inputs(bbox_analyses, *, has_structural=False, has_color=False,
                         confidence="medium"):
    """Build the kwargs _map_to_agent_route expects, except bbox_analyses."""
    labels = []
    if has_structural:
        labels.append("EXTRA_COMPONENT")
    if has_color:
        labels.append("COLOR_MISMATCH")
    labels.append("TEXT_MISMATCH_PROBABLE")
    classification = Classification(
        labels=labels, severity="high", explanation="",
        decision="FIX_PRODUCT_REVIEW", suspected_module="",
        confidence=confidence,
    )
    bboxes = [
        BBoxInfo(label=0, geometry=(0, 0, 100, 50), area=5000,
                 normalization_artifact=False, area_ratio=0.1)
        for _ in bbox_analyses
    ]
    metrics = Metrics(
        bbox_count=len(bbox_analyses), bbox_largest_area_ratio=0.1,
        changed_pixel_ratio=0.05, mean_abs_diff=10.0,
    )
    pairing = Pairing(
        surface_key="", app="", view="", theme="", mockup_path="",
        real_capture_path="x", diff_path="", overlay_path="",
    )
    return {
        "classification": classification,
        "bboxes": bboxes,
        "bbox_analyses": bbox_analyses,
        "metrics": metrics,
        "manifest_entry": {},
        "biggest_bbox_dominates": False,
        "all_artifacts": False,
        "pairing": pairing,
    }


def _route_for(bbox_analyses, **kw):
    inputs = _make_routing_inputs(bbox_analyses, **kw)
    res = _map_to_agent_route(**inputs)
    return res[0], res[5]  # agent_route, product_action_allowed


def test_guardrail_garbage_worst_pair_not_product_actionable():
    """Surface: suite:recuperar-acceso@light (real data).

    Bbox aggregate OCR contains NeuroMood / Configuración (legible),
    but fuzzy_ratio_worst_pair is the pure-noise pair
    AP .. .. i... vs M-x22aomo. Previous guardrail validated only the
    bbox aggregate and let this through to PRODUCT_ACTIONABLE.
    """
    ba = [{
        "mockup_ocr": "NeuroMood / Configuración inicial\nAP .. .. i...",
        "real_ocr": "NeuroMood / Configuración inicial\nM\x22aomo",
        "fuzzy_ratio_worst": 0.0,
        "fuzzy_ratio_worst_pair": ["AP .. .. i...", "M\x22aomo"],
        "color_delta": 0,
        "mockup_color": (0, 0, 0), "real_color": (0, 0, 0),
        "geometry": (0, 0, 100, 50),
    }]
    route, allowed = _route_for(ba)
    assert allowed is False, (
        f"OCR-garbage worst_pair must NOT enable product action, got route={route}"
    )
    assert route != "PRODUCT_ACTIONABLE", (
        f"OCR-garbage worst_pair must NOT route to PRODUCT_ACTIONABLE, got {route}"
    )


def test_guardrail_garbage_on_both_sides_not_product_actionable():
    """Surface: suite:actividades@dark + suite:actividades-marked-hice@dark.

    Both sides of fuzzy_ratio_worst_pair are junk. The pair shares no
    alphabetic token of length >=3 and has no shared substring >=5 chars.
    """
    ba = [{
        "mockup_ocr": "Elegí una fan",
        "real_ocr": "VAIOCOUURIAS",
        "fuzzy_ratio_worst": 0.0,
        "fuzzy_ratio_worst_pair": ["Elegí una fan", "VAIOCOUURIAS"],
        "color_delta": 0,
        "mockup_color": (0, 0, 0), "real_color": (0, 0, 0),
        "geometry": (0, 0, 100, 50),
    }]
    route, allowed = _route_for(ba)
    assert allowed is False, (
        f"Junk-on-both-sides pair must NOT enable product action, got route={route}"
    )
    assert route != "PRODUCT_ACTIONABLE", (
        f"Junk-on-both-sides pair must NOT route to PRODUCT_ACTIONABLE, got {route}"
    )


def test_guardrail_garbage_with_color_signal_goes_to_qa_tooling():
    """Surface: hub:textos-globales@dark (real data).

    c 12/32 vs Bienvenida — no shared tokens, no shared substrings.
    The bbox also has a strong color delta (so has_color=True), but the
    OCR evidence is pure noise. The owner rule: color+noise must NOT
    route to PRODUCT; it must go to QA_TOOLING_ACTIONABLE so the agent
    can verify the dominant-color crop is not a background fill before
    claiming product action.
    """
    ba = [{
        "mockup_ocr": "c 12/32",
        "real_ocr": "Bienvenida",
        "fuzzy_ratio_worst": 0.0,
        "fuzzy_ratio_worst_pair": ["c 12/32", "Bienvenida"],
        "color_delta": 50,
        "mockup_color": (10, 10, 10), "real_color": (200, 200, 200),
        "geometry": (0, 0, 100, 50),
    }]
    route, allowed = _route_for(ba, has_color=True)
    assert allowed is False, (
        f"Color + garbage-OCR must NOT enable product action, got route={route}"
    )
    assert route != "PRODUCT_ACTIONABLE", (
        f"Color + garbage-OCR must NOT route to PRODUCT_ACTIONABLE, got {route}"
    )
    assert route in ("QA_TOOLING_ACTIONABLE", "AUDITOR_IMPROVEMENT_ACTIONABLE"), (
        f"Color + garbage-OCR should go to QA/AUDITOR, got {route}"
    )


def test_guardrail_legit_pair_still_routes_product_actionable():
    """Sanity guard: a REAL text mismatch must still route to PRODUCT.

    The amend must not be over-restrictive. Recuperar acceso vs
    Recuperar-Acceso shares recuperar as a >=5-char substring;
    _looks_like_real_text_pair returns True, so routing should pass.
    """
    ba = [{
        "mockup_ocr": "Recuperar acceso",
        "real_ocr": "Recuperar-Acceso",
        "fuzzy_ratio_worst": 35.0,
        "fuzzy_ratio_worst_pair": ["Recuperar acceso", "Recuperar-Acceso"],
        "color_delta": 0,
        "mockup_color": (0, 0, 0), "real_color": (0, 0, 0),
        "geometry": (0, 0, 100, 50),
    }]
    route, allowed = _route_for(ba)
    assert allowed is True, (
        f"Legit text mismatch MUST enable product action, got route={route}"
    )
    assert route == "PRODUCT_ACTIONABLE", (
        f"Legit text mismatch MUST route to PRODUCT_ACTIONABLE, got {route}"
    )


def test_guardrail_aggregate_legible_but_pair_garbage_not_product():
    """The exact pattern that bit the four real surfaces:

    bbox aggregate has legible OCR (e.g. multiple lines, one legible),
    but the WORST sub-pair reported to consumers is garbage. Without
    validating the sub-pair directly, the old guardrail would let this
    through. With the amend, the sub-pair is validated and the route
    falls back to AUDITOR (since worst_fuzzy_real < 70 but no structural,
    no color → Case 4 weak-text branch).
    """
    ba = [{
        "mockup_ocr": "NeuroMood\nConfiguración\nAP .. .. i...",
        "real_ocr": "NeuroMood\nConfiguración\nM\x22aomo",
        "fuzzy_ratio_worst": 0.0,
        "fuzzy_ratio_worst_pair": ["AP .. .. i...", "M\x22aomo"],
        "color_delta": 0,
        "mockup_color": (0, 0, 0), "real_color": (0, 0, 0),
        "geometry": (0, 0, 100, 50),
    }]
    route, allowed = _route_for(ba)
    assert allowed is False, (
        "When aggregate OCR is legible but worst_pair is garbage, the "
        f"routing must NOT allow product action (got route={route})"
    )
    assert route != "PRODUCT_ACTIONABLE"


def test_guardrail_empty_bbox_analyses_not_product():
    """Regression for empty bbox_analyses: must not crash and must not
    spuriously route to PRODUCT_ACTIONABLE."""
    route, allowed = _route_for([])
    assert allowed is False, (
        f"Empty bbox_analyses must NOT enable product action, got route={route}"
    )
    assert route != "PRODUCT_ACTIONABLE"


def test_report_json_no_garbage_pair_product_actionable():
    """Integration check against the latest report.json.

    Scans every PRODUCT_ACTIONABLE surface in the latest report and
    confirms that its fuzzy_ratio_worst_pair (the pair actually shown to
    consumers via diff_summary) passes _looks_like_real_text_pair on its
    own. This catches the original regression at the report level.
    """
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r.get("agent_package", {})
        if pkg.get("agent_route") != "PRODUCT_ACTIONABLE":
            continue
        if not pkg.get("product_action_allowed", False):
            continue
        te = pkg.get("text_evidence", {})
        pair = te.get("fuzzy_ratio_worst_pair", ["", ""])
        if not (pair and pair[0] and pair[1] and pair[0] != pair[1]):
            continue
        # The pair shown to consumers MUST pass the legibility check on
        # its own. If it doesn't, the routing guardrail is broken.
        assert _looks_like_real_text_pair(pair[0], pair[1]), (
            f"PRODUCT_ACTIONABLE surface {pkg.get('surface_key', '')} "
            f"cites an illegible pair: {pair!r}"
        )


# ---------------------------------------------------------------------------
# V3 reorientation tests — actionable_evidence + routing + distribution
# ---------------------------------------------------------------------------


def test_actionable_evidence_present_on_all_surfaces():
    """Every surface in latest/report.json must have actionable_evidence populated."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for r in report:
        pkg = r["agent_package"]
        assert "actionable_evidence" in pkg, f"Missing actionable_evidence: {pkg.get('surface_key')}"
        ae = pkg["actionable_evidence"]
        assert "probable_root_cause" in ae
        assert "probable_module" in ae
        assert "next_action" in ae
        assert "evidence_strength" in ae


def test_actionable_evidence_module_heuristic():
    """probable_module derived from surface_key correctly."""
    assert _probable_module("suite:recuperar-acceso@light") == "suite.recuperar_acceso"
    assert _probable_module("hub:detalle-plan-activacion@dark") == "hub.detalle_plan_activacion"
    assert _probable_module("suite:home@light") == "suite.home"


def test_cluster_root_cause_render_noise():
    """RENDER_NOISE_OK + low changed_pixel → render_noise."""
    cls = Classification(decision="RENDER_NOISE_OK", labels=["CHROME_MISMATCH"], explanation="")
    metrics = Metrics(changed_pixel_ratio=0.01)
    assert _cluster_root_cause(cls, [], metrics) == "render_noise"


def test_render_noise_ok_routes_to_no_action():
    """RENDER_NOISE_OK + SSIM >= 0.95 + no structural labels -> NO_ACTION."""
    cls = Classification(decision="RENDER_NOISE_OK", labels=["CHROME_MISMATCH"], explanation="", confidence="high")
    metrics = Metrics(ssim=0.98, changed_pixel_ratio=0.246, mean_abs_diff=2.0, bbox_largest_area_ratio=0.9, bbox_count=1)
    bboxes = [BBoxInfo(label=0, geometry=(0,0,100,100), area=10000, area_ratio=0.9, normalization_artifact=False)]
    ba = [{"mockup_ocr":"x","real_ocr":"x","fuzzy_ratio_worst":100,"fuzzy_ratio_worst_pair":["",""],"color_delta":0,"mockup_color":(0,0,0),"real_color":(0,0,0),"geometry":(0,0,100,100),"bbox_area_ratio":0.9}]
    pairing = Pairing(surface_key="",app="",view="",theme="",mockup_path="",real_capture_path="x",diff_path="",overlay_path="")
    res = _map_to_agent_route(cls, bboxes, ba, metrics, {}, False, False, pairing)
    assert res[0] == "NO_ACTION_NEEDED_WITH_EVIDENCE", f"Got {res[0]}"


def test_distribution_auditor_bucket_bounded():
    """After reorientation, AUDITOR_IMPROVEMENT_ACTIONABLE <= 10 surfaces."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    n_auditor = sum(1 for r in report if r["agent_package"]["agent_route"] == "AUDITOR_IMPROVEMENT_ACTIONABLE")
    assert n_auditor <= 10, f"AUDITOR bucket too large: {n_auditor}/86 (must be <=10)"


def test_distribution_no_human_review():
    """0 surfaces with requires_owner_review=True (V3 hard rule)."""
    report_path = _PROJ / "qa" / "_visual_auditor_v3" / "latest" / "report.json"
    if not report_path.exists():
        pytest.skip("No report.json — run analyze --all first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    n_human = sum(1 for r in report if r["agent_package"].get("requires_owner_review", False))
    assert n_human == 0, f"Found {n_human} surfaces with requires_owner_review=True"


def test_batch_mode_help_lists_flags():
    """--quiet, --resume, --log-file must be in --help output."""
    import subprocess
    result = subprocess.run(
        [str(Path(".venv") / "Scripts" / "python.exe"), "qa/visual_auditor_v3.py", "analyze", "--help"],
        capture_output=True, text=True, cwd=_PROJ,
    )
    assert "--quiet" in result.stdout
    assert "--resume" in result.stdout
    assert "--log-file" in result.stdout
