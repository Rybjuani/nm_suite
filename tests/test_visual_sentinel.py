"""Tests minimos del Visual Sentinel.

Cubren la logica pura (no requieren levantar Qt): parseo de CLI, normalizacion,
carga de contratos, y los checks visuales sobre estructuras sinteticas. La
validacion end-to-end (audit --all) corre por separado via el CLI documentado en
qa/README_VISUAL_SENTINEL.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))


def test_module_imports_without_capture_v8_or_runtime():
    """El Sentinel debe ser independiente: no importa ni reusa capture_v8/
    runtime_live_probe. La docstring puede mencionarlos conceptualmente, pero
    el codigo no debe importarlos ni referenciar su API/_RECIPES."""
    import ast
    import importlib
    for m in list(sys.modules):
        if m.startswith("qa.visual_sentinel"):
            del sys.modules[m]
    mod = importlib.import_module("qa.visual_sentinel")
    # Ningun import debe tirar de capture_v8 ni runtime_live_probe
    tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert "capture_v8" not in n.name and "runtime_live_probe" not in n.name
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            assert "capture_v8" not in mod_name
            assert "runtime_live_probe" not in mod_name
    # Tampoco reusa la lista de recetas manual de V8 (su simbolo caracteristico)
    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "from qa.capture_v8" not in src
    assert "import qa.capture_v8" not in src
    assert "from qa.runtime_live_probe" not in src
    assert "_RECIPES" not in src


def test_short_theme_and_theme_map():
    from qa.visual_sentinel import _short_theme, _theme_map
    assert _short_theme("light_hybrid") == "light"
    assert _short_theme("dark_hybrid") == "dark"
    assert _theme_map("both") == ["light_hybrid", "dark_hybrid"]
    assert _theme_map("light") == ["light_hybrid"]
    assert _theme_map("dark") == ["dark_hybrid"]
    with pytest.raises(SystemExit):
        _theme_map("nope")


def test_norm_text_strips_accents_and_case():
    from qa.visual_sentinel import _norm_text
    assert _norm_text("Resumen IA") == "resumen ia"
    assert _norm_text("  Exportar  PDF ") == "exportar pdf"
    assert _norm_text("Completar con IA") == "completar con ia"


def test_state_spec_screen_id():
    from qa.visual_sentinel import StateSpec
    s = StateSpec(app="suite", surface="dbt", substate="NMTabs0-tab-1", label="x")
    assert s.screen_id == "suite:dbt:NMTabs0-tab-1"
    s2 = StateSpec(app="hub", surface="pacientes", label="x")
    assert s2.screen_id == "hub:pacientes"


def test_contracts_yaml_load_and_have_required_fields():
    from qa.visual_sentinel import _load_contracts
    contracts = _load_contracts()
    assert len(contracts) >= 10, "debe cargar contratos globales + de componentes"
    for c in contracts:
        assert "id" in c and "severity" in c and "check" in c, c
        assert c["severity"] in {"P0", "P1", "P2", "P3"}, c


def _make_state(text="", mean=0.5, stddev=0.1, phash=None, sha="abc",
                tree=None, geo=None, screen_id="suite:test", surface="test",
                theme="dark"):
    from qa.visual_sentinel import CapturedState
    from pathlib import Path
    if tree is None:
        tree = {"type": "QWidget", "text": "", "visible": True, "children": []}
    if geo is None:
        geo = {"x": 0, "y": 0, "w": 960, "h": 600}
    return CapturedState(
        screen_id=screen_id, app="suite", theme=theme, label="t",
        png_path=Path("x.png"), tree_path=Path("x.json"), sha256=sha, phash=phash,
        structural_hash="dead", visual_metrics={"gray_mean": mean, "gray_stddev": stddev},
        widget_tree=tree, texts=[text] if text else [], clickable=[],
        scrollbars=[], tabs=[], buttons=[], crops=[], geometry=geo,
    )


def test_blank_or_flat_flags_blank_white():
    from qa.visual_sentinel import _check_blank_or_flat
    st = _make_state(mean=0.999, stddev=0.001)
    out = _check_blank_or_flat(st, {}, [], {})
    assert out and out[0]["flag"] == "BLANK_OR_FLAT"


def test_blank_or_flat_passes_normal():
    from qa.visual_sentinel import _check_blank_or_flat
    st = _make_state(mean=0.5, stddev=0.2)
    assert _check_blank_or_flat(st, {}, [], {}) == []


def test_blank_or_flat_missing_evidence():
    from qa.visual_sentinel import _check_blank_or_flat
    st = _make_state()
    st.error = "grab failed"
    out = _check_blank_or_flat(st, {}, [], {})
    assert out and out[0]["flag"] == "MISSING_EVIDENCE"


def test_duplicate_suspect_by_phash():
    from qa.visual_sentinel import _check_duplicate
    a = _make_state(phash="0000000000000000", screen_id="suite:a")
    b = _make_state(phash="0000000000000000", screen_id="suite:b")
    out = _check_duplicate(a, {"params": {"max_distance": 5}}, [a, b], {})
    assert any(r["flag"] == "DUPLICATE_SUSPECT" for r in out)


def test_duplicate_suspect_by_sha256():
    from qa.visual_sentinel import _check_duplicate
    a = _make_state(sha="samehash", phash="1111111111111111", screen_id="suite:a")
    b = _make_state(sha="samehash", phash="2222222222222222", screen_id="suite:b")
    out = _check_duplicate(a, {"params": {"max_distance": 1}}, [a, b], {})
    assert any(r["flag"] == "DUPLICATE_SUSPECT" for r in out)


def test_out_of_viewport_detects_offscreen_widget():
    from qa.visual_sentinel import _check_out_of_viewport
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "QLabel", "text": "fuera", "visible": True, "clickable": False,
         "geometry": {"x": -50, "y": 10, "w": 40, "h": 20}, "children": []},
    ]}
    st = _make_state(tree=tree)
    out = _check_out_of_viewport(st, {}, [], {})
    assert out and out[0]["flag"] == "OUT_OF_VIEWPORT"


def test_overlap_detects_clear_overlap():
    from qa.visual_sentinel import _check_overlap
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "QPushButton", "text": "A", "visible": True, "clickable": True,
         "geometry": {"x": 10, "y": 10, "w": 100, "h": 40}, "children": []},
        {"type": "QPushButton", "text": "B", "visible": True, "clickable": True,
         "geometry": {"x": 20, "y": 15, "w": 100, "h": 40}, "children": []},
    ]}
    st = _make_state(tree=tree)
    out = _check_overlap(st, {}, [], {})
    assert any(r["flag"] == "WIDGET_OVERLAP" for r in out)


def test_new_state_unreviewed_when_not_in_registry():
    from qa.visual_sentinel import _check_new_state
    st = _make_state(screen_id="suite:nuevo")
    out = _check_new_state(st, {}, [], {})
    assert out and out[0]["flag"] == "NEW_STATE_UNREVIEWED"
    out2 = _check_new_state(st, {}, [], {f"{st.screen_id}@{st.theme}": {}})
    assert out2 == []


def test_compute_result_blocks_on_p0_p1_and_flags():
    from qa.visual_sentinel import _compute_result, Finding
    states = []
    cov = {"discovered_states": 0, "captured_states": 0}
    # general no corrio
    res, blk = _compute_result(False, states, [], cov)
    assert res == "FAIL" and any("GENERAL_AUDIT_NOT_RUN" in b for b in blk)
    # P0 bloquea
    res, blk = _compute_result(True, states, [Finding("c", "P0", "BLANK_OR_FLAT", "x", "dark", "m")], cov)
    assert res == "FAIL"
    # bloqueante por flag (DUPLICATE_SUSPECT aunque sea P2)
    res, blk = _compute_result(True, states, [Finding("c", "P2", "DUPLICATE_SUSPECT", "x", "dark", "m")], cov)
    assert res == "FAIL"
    # PASS solo si todo limpio y general corrio
    res, blk = _compute_result(True, states, [], cov)
    assert res == "PASS" and blk == []


def test_compute_coverage_new_and_stale():
    from qa.visual_sentinel import _compute_coverage
    a = _make_state(screen_id="suite:a")
    b = _make_state(screen_id="suite:b", theme="light")
    states = [a, b]
    reg = {"suite:a@dark": {}, "suite:gone@dark": {}}
    cov = _compute_coverage(states, ["suite:a", "suite:b"], reg)
    # suite:a@dark aprobado -> no nuevo; suite:b@light nuevo; suite:gone@dark stale
    assert cov["new_count"] == 1
    assert "suite:b@light" in cov["new_state_unreviewed"]
    assert "suite:gone@dark" in cov["stale_states"]
    assert cov["stale_count"] == 1


def test_check_stale_flags_missing_approved():
    from qa.visual_sentinel import _check_stale
    reg = {"suite:gone@dark": {"screen_id": "suite:gone", "theme": "dark"}}
    out = _check_stale([], reg)
    assert out and out[0].flag == "STALE_STATE"


def test_check_obsolete_recipe_refs():
    from qa.visual_sentinel import _check_obsolete_recipe_refs
    reg = {"suite:x@dark": {"screen_id": "suite:x", "theme": "dark",
                            "note": "viene de capture_v8"}}
    out = _check_obsolete_recipe_refs(reg)
    assert out and out[0].flag == "OBSOLETE_RECIPE_REFERENCE"


def test_cta_missing_icon_for_semantic_buttons():
    from qa.visual_sentinel import _check_cta_missing_icon
    from qa.visual_sentinel import CapturedState
    from pathlib import Path
    st = CapturedState(
        screen_id="hub:detalle", app="hub", theme="dark", label="d",
        png_path=Path("x.png"), tree_path=Path("x.json"), sha256=None, phash=None,
        structural_hash="", visual_metrics={}, widget_tree={}, texts=[],
        clickable=[], scrollbars=[], tabs=[],
        buttons=[{"type": "NMButton", "text": "Exportar PDF", "enabled": True, "hasIcon": False}],
        crops=[], geometry={},
    )
    out = _check_cta_missing_icon(st, {}, [], {})
    assert out and out[0]["flag"] == "CTA_SEMANTIC_MISSING_ICON"


def test_resolve_screen_and_parse_res():
    from qa.visual_sentinel import _resolve_screen, _parse_res
    assert _resolve_screen("suite", "animo") == "suite:animo"
    assert _resolve_screen("suite", "suite:dbt") == "suite:dbt"
    assert _parse_res("960x600") == (960, 600)


def test_cli_parser_supports_top_level_list():
    from qa.visual_sentinel import _build_parser
    p = _build_parser()
    ns = p.parse_args(["--list"])
    assert ns.list is True
    ns2 = p.parse_args(["audit", "--all", "--theme", "both"])
    assert ns2.all is True and ns2.theme == "both"
    ns3 = p.parse_args(["inspect", "--screen", "suite:home", "--theme", "light"])
    assert ns3.screen == "suite:home"
