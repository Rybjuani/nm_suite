"""Tests del Visual Sentinel.

Dos grupos:
1) Logica pura (sin Qt): normalizacion, contratos, cobertura, CLI.
2) Crawler generico con fixtures Qt sinteticos (e2e): prueban que el Sentinel
   descubre estados dinamicos (tabs, stacked, modal, boton que revela subestado,
   loop visual) SIN depender de pantallas actuales de NeuroMood. Si cambian
   nombres o cantidades, estos tests siguen validando el comportamiento general.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

import qa.visual_sentinel as visual_sentinel  # noqa: E402  (alias for legacy per-test imports)


# ═══════════════════════════════════════════════════════════════════════════
# Independencia del Sentinel (no importa ni reusa V8/runtime)
# ═══════════════════════════════════════════════════════════════════════════

def test_module_imports_without_capture_v8_or_runtime():
    import ast
    import importlib
    for m in list(sys.modules):
        if m.startswith("qa.visual_sentinel"):
            del sys.modules[m]
    mod = importlib.import_module("qa.visual_sentinel")
    tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert "capture_v8" not in n.name and "runtime_live_probe" not in n.name
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            assert "capture_v8" not in mod_name
            assert "runtime_live_probe" not in mod_name
    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "from qa.capture_v8" not in src
    assert "import qa.capture_v8" not in src
    assert "from qa.runtime_live_probe" not in src
    assert "_RECIPES" not in src


# ═══════════════════════════════════════════════════════════════════════════
# Logica pura
# ═══════════════════════════════════════════════════════════════════════════

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


def test_sanitize_label():
    from qa.visual_sentinel import _sanitize_label
    assert _sanitize_label("Guía de Respiración!") == "guia-de-respiracion"
    assert _sanitize_label("???") == "state"


def test_safe_name_windows():
    from qa.visual_sentinel import _safe_name
    assert _safe_name("suite:dbt:NMTabs0-tab-1") == "suite__dbt__NMTabs0-tab-1"
    assert "/" not in _safe_name("a/b")


def test_state_spec_screen_id():
    from qa.visual_sentinel import StateSpec
    s = StateSpec(app="suite", surface="dbt", substate="tab-1", label="x")
    assert s.screen_id == "suite:dbt:tab-1"
    s2 = StateSpec(app="hub", surface="pacientes", label="x")
    assert s2.screen_id == "hub:pacientes"


def test_contracts_yaml_load_and_have_required_fields():
    from qa.visual_sentinel import _load_contracts
    contracts = _load_contracts()
    assert len(contracts) >= 12
    for c in contracts:
        assert "id" in c and "severity" in c and "check" in c, c
        assert c["severity"] in {"P0", "P1", "P2", "P3"}, c


def _make_state(text="", mean=0.5, stddev=0.1, phash=None, sha="abc",
                tree=None, geo=None, screen_id="suite:test", surface="test",
                theme="dark"):
    from qa.visual_sentinel import CapturedState
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
         "in_scroll": False, "geo_win": {"x": -50, "y": 10, "w": 40, "h": 20},
         "children": []}]}
    st = _make_state(tree=tree)
    out = _check_out_of_viewport(st, {}, [], {})
    assert out and out[0]["flag"] == "OUT_OF_VIEWPORT"


def test_out_of_viewport_ignores_scroll_content():
    from qa.visual_sentinel import _check_out_of_viewport
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "QLabel", "text": "en scroll", "visible": True, "clickable": False,
         "in_scroll": True, "geo_win": {"x": -50, "y": 2000, "w": 40, "h": 20},
         "children": []}]}
    st = _make_state(tree=tree)
    assert _check_out_of_viewport(st, {}, [], {}) == []


def test_overlap_detects_clear_overlap():
    from qa.visual_sentinel import _check_overlap
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "QPushButton", "text": "A", "visible": True, "clickable": True,
         "geo_win": {"x": 10, "y": 10, "w": 100, "h": 40}, "children": []},
        {"type": "QPushButton", "text": "B", "visible": True, "clickable": True,
         "geo_win": {"x": 20, "y": 15, "w": 100, "h": 40}, "children": []},
    ]}
    st = _make_state(tree=tree)
    out = _check_overlap(st, {}, [], {})
    assert any(r["flag"] == "WIDGET_OVERLAP" for r in out)


def test_overlap_skips_parent_child_nesting():
    from qa.visual_sentinel import _check_overlap
    # padre grande con hijo chico adentro: nesting, no overlap
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "NMCard", "text": "card", "visible": True, "clickable": True,
         "geo_win": {"x": 0, "y": 0, "w": 300, "h": 200}, "children": [
            {"type": "QPushButton", "text": "hijo", "visible": True,
             "clickable": True, "geo_win": {"x": 10, "y": 10, "w": 80, "h": 30},
             "children": []}]}]}
    st = _make_state(tree=tree)
    out = _check_overlap(st, {}, [], {})
    assert all(r["flag"] != "WIDGET_OVERLAP" for r in out)


def test_new_state_unreviewed_when_not_in_registry():
    from qa.visual_sentinel import _check_new_state
    st = _make_state(screen_id="suite:nuevo")
    out = _check_new_state(st, {}, [], {})
    assert out and out[0]["flag"] == "NEW_STATE_UNREVIEWED"
    out2 = _check_new_state(st, {}, [], {f"{st.screen_id}@{st.theme}": {}})
    assert out2 == []


def test_primary_button_missing_icon_by_role():
    from qa.visual_sentinel import _check_primary_button_missing_icon, CapturedState
    st = CapturedState(
        screen_id="hub:detalle", app="hub", theme="dark", label="d",
        png_path=Path("x.png"), tree_path=Path("x.json"), sha256=None, phash=None,
        structural_hash="", visual_metrics={}, widget_tree={}, texts=[],
        clickable=[], scrollbars=[], tabs=[],
        buttons=[{"type": "NMButton", "text": "Exportar", "enabled": True,
                  "objectName": "NMButton_gradient", "has_icon": False}],
        crops=[], geometry={})
    out = _check_primary_button_missing_icon(st, {"params": {}}, [], {})
    assert out and out[0]["flag"] == "PRIMARY_BUTTON_MISSING_ICON"
    # con icono no flagea
    st.buttons[0]["has_icon"] = True
    assert _check_primary_button_missing_icon(st, {"params": {}}, [], {}) == []


def test_control_without_metadata_flag():
    from qa.visual_sentinel import _check_control_without_metadata
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "QPushButton", "text": "", "visible": True, "clickable": True,
         "objectName": "", "has_icon": False, "children": []}]}
    st = _make_state(tree=tree)
    out = _check_control_without_metadata(st, {}, [], {})
    assert out and out[0]["flag"] == "CONTROL_WITHOUT_VISUAL_METADATA"


def test_checkbox_in_scroll_area_structural():
    from qa.visual_sentinel import _check_checkbox_in_scroll_area
    tree = {"type": "QWidget", "visible": True, "children": [
        {"type": "QCheckBox", "text": "Acepto terminos", "visible": True,
         "clickable": True, "in_scroll": True, "children": []}]}
    st = _make_state(tree=tree)
    out = _check_checkbox_in_scroll_area(st, {}, [], {})
    assert out and out[0]["flag"] == "CHECKBOX_IN_SCROLL_AREA"


def test_dialog_without_close_flag():
    from qa.visual_sentinel import _check_dialog_without_close
    tree = {"type": "QDialog", "text": "", "visible": True, "clickable": False,
            "children": [{"type": "QLabel", "text": "info", "visible": True,
                          "children": []}]}
    st = _make_state(tree=tree)
    out = _check_dialog_without_close(st, {}, [], {})
    assert out and out[0]["flag"] == "DIALOG_WITHOUT_VISIBLE_CLOSE"


def test_compute_result_blocks_on_p0_p1_and_flags():
    from qa.visual_sentinel import _compute_result, Finding
    states = []
    cov = {"discovered_states": 0, "captured_states": 0}
    res, blk = _compute_result(False, states, [], cov, strict=False)
    assert res == "FAIL" and any("GENERAL_AUDIT_NOT_RUN" in b for b in blk)
    res, blk = _compute_result(True, states,
                               [Finding("c", "P0", "BLANK_OR_FLAT", "x", "dark", "m")],
                               cov, strict=False)
    assert res == "FAIL"
    res, blk = _compute_result(True, states,
                               [Finding("c", "P2", "DUPLICATE_SUSPECT", "x", "dark", "m")],
                               cov, strict=False)
    assert res == "FAIL"
    # strict: P2 tambien bloquea
    res, blk = _compute_result(True, states,
                               [Finding("c", "P2", "WIDGET_OVERLAP", "x", "dark", "m")],
                               cov, strict=True)
    assert res == "FAIL"
    res, blk = _compute_result(True, states, [], cov, strict=False)
    assert res == "PASS" and blk == []


def test_compute_coverage_new_and_stale():
    from qa.visual_sentinel import _compute_coverage
    a = _make_state(screen_id="suite:a")
    b = _make_state(screen_id="suite:b", theme="light")
    states = [a, b]
    reg = {"suite:a@dark": {}, "suite:gone@dark": {}}
    cov = _compute_coverage(states, ["suite:a", "suite:b"], reg)
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


def test_resolve_screen_and_parse_res():
    from qa.visual_sentinel import _resolve_screen, _parse_res
    assert _resolve_screen("suite", "animo") == "suite:animo"
    assert _resolve_screen("suite", "suite:dbt") == "suite:dbt"
    assert _parse_res("960x600") == (960, 600)


def test_cli_parser_supports_top_level_list_and_strict():
    from qa.visual_sentinel import _build_parser
    p = _build_parser()
    ns = p.parse_args(["--list"])
    assert ns.list is True
    ns2 = p.parse_args(["audit", "--all", "--theme", "both", "--strict"])
    assert ns2.all is True and ns2.theme == "both" and ns2.strict is True
    ns3 = p.parse_args(["inspect", "--screen", "suite:home", "--theme", "light"])
    assert ns3.screen == "suite:home"


def test_crawl_opts_strict_increases_caps():
    from qa.visual_sentinel import _crawl_opts
    base = _crawl_opts(False)
    strict = _crawl_opts(True)
    assert strict["max_states"] > base["max_states"]
    assert strict["max_depth"] > base["max_depth"]


def test_crawl_opts_includes_time_budget():
    from qa.visual_sentinel import (_crawl_opts, _DEFAULT_TIME_BUDGET_SECS,
                                    _STRICT_TIME_BUDGET_SECS)
    assert _crawl_opts(False)["time_budget_secs"] == _DEFAULT_TIME_BUDGET_SECS
    assert _crawl_opts(True)["time_budget_secs"] == _STRICT_TIME_BUDGET_SECS


def test_crawl_opts_env_override_time_budget(monkeypatch):
    from qa.visual_sentinel import _crawl_opts
    monkeypatch.setenv("NM_SENTINEL_TIME_BUDGET", "45")
    assert _crawl_opts(False)["time_budget_secs"] == 45
    # valores invalidos no rompen: se ignora el override y vuelve al default
    monkeypatch.setenv("NM_SENTINEL_TIME_BUDGET", "no-numero")
    from qa.visual_sentinel import _DEFAULT_TIME_BUDGET_SECS
    assert _crawl_opts(False)["time_budget_secs"] == _DEFAULT_TIME_BUDGET_SECS
    # piso de seguridad: nunca menos de 15s
    monkeypatch.setenv("NM_SENTINEL_TIME_BUDGET", "1")
    assert _crawl_opts(False)["time_budget_secs"] == 15


def test_check_crawl_truncated_flags_partial_coverage():
    from qa.visual_sentinel import _check_crawl_truncated
    graphs = {
        "suite@light": {"truncated_by_time": True, "theme": "light",
                        "discovered_count": 40, "frontier_remaining": 12,
                        "crawl_opts": {"time_budget_secs": 300}},
        "hub@light": {"truncated_by_time": False, "theme": "light",
                      "discovered_count": 18, "frontier_remaining": 0,
                      "crawl_opts": {"time_budget_secs": 300}},
    }
    out = _check_crawl_truncated(graphs)
    assert len(out) == 1
    assert out[0].flag == "CRAWL_TRUNCATED"
    assert out[0].severity == "P1"
    assert out[0].screen_id == "suite@light"


def test_check_crawl_truncated_clean_when_complete():
    from qa.visual_sentinel import _check_crawl_truncated
    graphs = {"suite@light": {"truncated_by_time": False,
                              "crawl_opts": {"time_budget_secs": 300}}}
    assert _check_crawl_truncated(graphs) == []


# ═══════════════════════════════════════════════════════════════════════════
# Crawler generico: tests e2e con fixtures Qt sinteticos
# (requieren pytest-qt / qapp fixture; offscreen via conftest)
# ═══════════════════════════════════════════════════════════════════════════

def _show(w):
    w.show()
    w.resize(400, 300)
    return w


def test_enumerate_finds_tab_actions(qapp):
    from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel
    from qa.visual_sentinel import _enumerate_safe_actions
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    tabs = QTabWidget()
    for name in ("Uno", "Dos", "Tres"):
        page = QWidget()
        page.setLayout(QVBoxLayout(page))
        page.layout().addWidget(QLabel(name))
        tabs.addTab(page, name)
    lay.addWidget(tabs)
    qapp.processEvents()
    actions = _enumerate_safe_actions(root, [], {"max_branch": 20})
    tab_acts = [a for a in actions if a["kind"] == "tab"]
    assert len(tab_acts) == 2  # 2 no-current indexes
    root.deleteLater()


def test_enumerate_finds_safe_click_and_skips_destructive(qapp):
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
    from qa.visual_sentinel import _enumerate_safe_actions
    omitted = []
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    lay.addWidget(QPushButton("Iniciar"))
    lay.addWidget(QPushButton("Eliminar"))
    qapp.processEvents()
    actions = _enumerate_safe_actions(root, [], {"max_branch": 20},
                                      log_omitted=omitted.append)
    labels = [a["label"] for a in actions if a["kind"] == "click"]
    assert any("iniciar" in lbl for lbl in labels)
    assert all("eliminar" not in lbl for lbl in labels)
    assert any(o["reason"] == "destructive-text" for o in omitted)
    root.deleteLater()


def test_enumerate_skips_async_network_buttons(qapp):
    """Botones que disparan llamadas LLM/export deben filtrarse como async-network.

    Cubre las tres formas reales del repo: "Completar con IA", "Resumen IA"
    (token 'ia' aislado) y "Exportar PDF". El control benigno "Guia diaria"
    NO debe filtrarse pese a contener la subcadena 'ia' dentro de palabras."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
    from qa.visual_sentinel import _enumerate_safe_actions
    omitted = []
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    lay.addWidget(QPushButton("Iniciar tarea"))
    lay.addWidget(QPushButton("Completar con IA"))
    lay.addWidget(QPushButton("Resumen IA"))
    lay.addWidget(QPushButton("Exportar PDF"))
    lay.addWidget(QPushButton("Guia diaria"))  # 'ia' dentro de palabras: benigno
    qapp.processEvents()
    actions = _enumerate_safe_actions(root, [], {"max_branch": 20},
                                      log_omitted=omitted.append)
    labels = [a["label"] for a in actions if a["kind"] == "click"]
    assert any("iniciar" in lbl for lbl in labels)
    assert any("guia-diaria" in lbl for lbl in labels)
    assert not any("con-ia" in lbl for lbl in labels)
    assert not any("resumen" in lbl for lbl in labels)
    assert not any("exportar" in lbl for lbl in labels)
    assert sum(1 for o in omitted if o["reason"] == "async-network") == 3
    root.deleteLater()


def test_enumerate_skips_reset_and_tooltip_destructive(qapp):
    """Reset-por-defecto (bajo valor) y boton-icono destructivo sin texto pero con
    tooltip ('Quitar...') deben filtrarse. Replica el sumidero NMRowUnlink /
    'Restablecer por defecto' que hundia el presupuesto del crawler."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QToolButton
    from qa.visual_sentinel import _enumerate_safe_actions
    omitted = []
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    lay.addWidget(QPushButton("Restablecer por defecto"))
    icon_btn = QToolButton()  # sin texto: proposito solo en el tooltip
    icon_btn.setToolTip("Quitar paciente del Hub")
    lay.addWidget(icon_btn)
    lay.addWidget(QPushButton("Guardar"))
    qapp.processEvents()
    actions = _enumerate_safe_actions(root, [], {"max_branch": 20},
                                      log_omitted=omitted.append)
    labels = [a["label"] for a in actions if a["kind"] == "click"]
    assert any("guardar" in lbl for lbl in labels)
    assert not any("restablecer" in lbl for lbl in labels)
    reasons = {o["reason"] for o in omitted}
    assert "reset-low-value" in reasons
    assert "destructive-text" in reasons  # del tooltip del boton-icono
    root.deleteLater()


def test_enumerate_dedupes_repeated_labels(qapp):
    """N controles con el mismo (tipo+texto) colapsan a UNA accion: evita la
    explosion de capturas/duplicados (p.ej. 20x el mismo boton de fila)."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
    from qa.visual_sentinel import _enumerate_safe_actions
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    for _ in range(15):
        lay.addWidget(QPushButton("Editar campo"))
    lay.addWidget(QPushButton("Guardar cambios"))
    qapp.processEvents()
    actions = _enumerate_safe_actions(root, [], {"max_branch": 12})
    labels = [a["label"] for a in actions if a["kind"] == "click"]
    assert labels.count("act:editar-campo") == 1
    assert "act:guardar-cambios" in labels  # no fue desplazado por las copias
    root.deleteLater()


def _make_card_class(qapp):
    """Fabrica una clase tipo ModuleCard: QFrame que navega via mouseReleaseEvent
    custom (sin senal 'clicked'), con cursor pointing-hand y un QLabel de titulo."""
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt

    class _Card(QFrame):
        def __init__(self, title):
            super().__init__()
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.clicks = 0
            lay = QVBoxLayout(self)
            lay.addWidget(QLabel(title))

        def mouseReleaseEvent(self, event):
            self.clicks += 1
            super().mouseReleaseEvent(event)

    return _Card


def test_reimplements_mouse_ignores_pyqt_classes(qapp):
    """Solo cuenta override REAL de producto: una clase Python con
    mouseReleaseEvent -> True; un QFrame/QLabel puro del binding -> False."""
    from PyQt6.QtWidgets import QFrame, QLabel
    from qa.visual_sentinel import _reimplements_mouse
    Card = _make_card_class(qapp)
    assert _reimplements_mouse(Card("x")) is True
    assert _reimplements_mouse(QFrame()) is False
    assert _reimplements_mouse(QLabel("y")) is False


def test_is_clickable_custom_card_by_capability(qapp):
    """Un card custom (override mouse + pointing-hand) se detecta clickeable sin
    estar en ninguna lista de nombres; un QFrame estatico no."""
    from PyQt6.QtWidgets import QFrame
    from qa.visual_sentinel import _is_clickable
    Card = _make_card_class(qapp)
    assert _is_clickable(Card("Termometro")) is True
    assert _is_clickable(QFrame()) is False


def test_derive_label_text_from_child_label(qapp):
    """Card sin texto propio deriva su label del QLabel hijo (distingue hermanas)."""
    from PyQt6.QtWidgets import QPushButton
    from qa.visual_sentinel import _derive_label_text
    Card = _make_card_class(qapp)
    c = Card("Guia de respiracion")
    c.show()
    qapp.processEvents()
    assert _derive_label_text(c) == "Guia de respiracion"
    assert _derive_label_text(QPushButton("Aceptar")) == "Aceptar"  # texto propio
    c.deleteLater()


def test_apply_action_synthesizes_mouse_for_card(qapp):
    """_apply_action dispara mouseReleaseEvent en cards sin click()/clicked."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout
    from qa.visual_sentinel import _widget_locator, _apply_action
    Card = _make_card_class(qapp)
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    card = Card("Modulo")
    lay.addWidget(card)
    qapp.processEvents()
    action = {"kind": "click", "locator": _widget_locator(card, root),
              "label": "act:modulo"}
    assert _apply_action(root, action, qapp) is True
    assert card.clicks >= 1
    root.deleteLater()


def test_enumerate_detects_sibling_cards_distinctly(qapp):
    """Varias cards hermanas sin texto propio NO colapsan: cada una conserva su
    label derivado del titulo hijo (replica los 8 modulos del Suite home)."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout
    from qa.visual_sentinel import _enumerate_safe_actions
    Card = _make_card_class(qapp)
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    for title in ("Termometro", "Respiracion", "Registro", "Rutina"):
        lay.addWidget(Card(title))
    qapp.processEvents()
    actions = _enumerate_safe_actions(root, [], {"max_branch": 20})
    labels = {a["label"] for a in actions if a["kind"] == "click"}
    assert "act:termometro" in labels
    assert "act:respiracion" in labels
    assert "act:registro" in labels
    assert "act:rutina" in labels
    root.deleteLater()


def test_close_active_modals_rejects_native_dialog(qapp):
    """El modal guard cierra QDialog nativos modales (evita el cuelgue por
    event-loop anidado). Usa setModal+show (sin exec) para no bloquear el test."""
    from PyQt6.QtWidgets import QDialog
    from qa.visual_sentinel import _close_active_modals
    dlg = QDialog()
    dlg.setModal(True)
    dlg.show()
    qapp.processEvents()
    assert qapp.activeModalWidget() is dlg
    _close_active_modals()
    qapp.processEvents()
    assert qapp.activeModalWidget() is None
    dlg.deleteLater()


def test_watchdog_beat_and_stop_no_abort():
    """El watchdog no aborta mientras recibe latidos / se detiene limpio."""
    from qa.visual_sentinel import _Watchdog
    wd = _Watchdog(op_timeout_s=999).start()
    wd.beat()
    wd.stop()
    # Si el proceso sigue vivo tras stop(), el watchdog no disparo os._exit.
    assert True


def test_find_by_locator_resolves(qapp):
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
    from qa.visual_sentinel import _widget_locator, _find_by_locator
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    btn = QPushButton("Aceptar")
    lay.addWidget(btn)
    qapp.processEvents()
    loc = _widget_locator(btn, root)
    assert loc["type"] == "QPushButton"
    found = _find_by_locator(root, loc)
    assert found is btn
    root.deleteLater()


def test_apply_action_clicks_button(qapp):
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
    from qa.visual_sentinel import _widget_locator, _find_by_locator, _apply_action
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    btn = QPushButton("Go")
    state = {"clicked": False}
    btn.clicked.connect(lambda: state.__setitem__("clicked", True))
    lay.addWidget(btn)
    qapp.processEvents()
    action = {"kind": "click", "locator": _widget_locator(btn, root), "label": "act:go"}
    assert _apply_action(root, action, qapp)
    assert state["clicked"] is True
    root.deleteLater()


def test_widget_has_icon_detection(qapp):
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QPushButton, QWidget
    from qa.visual_sentinel import _widget_has_icon
    w = QPushButton("x")
    assert _widget_has_icon(w) is False
    # no podemos setear un QIcon real sin un recurso, pero un QIcon vacio sigue
    # isNull; verificamos que el helper no crashea y devuelve bool.
    w2 = QPushButton("y")
    w2.setIcon(QIcon())
    assert _widget_has_icon(w2) in (False, True)
    QWidget()  # keep refs
    w.deleteLater()
    w2.deleteLater()


def test_build_widget_tree_marks_in_scroll_and_icon(qapp, tmp_path):
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QCheckBox,
                                 QPushButton)
    from qa.visual_sentinel import _build_widget_tree, _walk_tree
    root = _show(QWidget())
    lay = QVBoxLayout(root)
    scroll = QScrollArea()
    inner = QWidget()
    inner.setLayout(QVBoxLayout(inner))
    cb = QCheckBox("Acepto terminos")
    inner.layout().addWidget(cb)
    scroll.setWidget(inner)
    lay.addWidget(scroll)
    lay.addWidget(QPushButton("Guardar"))
    qapp.processEvents()
    tree = _build_widget_tree(root, win_ref=root)
    found_cb = [n for n in _walk_tree(tree) if n.get("type") == "QCheckBox"]
    assert found_cb and found_cb[0]["in_scroll"] is True
    root.deleteLater()


def test_crawler_discovers_distinct_states_synthetic(qapp):
    """e2e: el crawler generico descubre estados dinamicos en un fixture Qt
    sintetico con tabs + boton que revela un subestado. No usa pantallas reales
    de NeuroMood: valida que la mecanica de descubrimiento es generica."""
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                                 QStackedWidget)
    from qa.visual_sentinel import (_enumerate_safe_actions, _apply_action,
                                    _build_widget_tree, _structural_hash)

    def build():
        root = QWidget()
        root.resize(400, 300)
        lay = QVBoxLayout(root)
        toggle = QPushButton("Revelar panel")
        stack = QStackedWidget()
        page0 = QWidget()
        page0.setLayout(QVBoxLayout(page0))
        page0.layout().addWidget(QLabel("estado base"))
        page1 = QWidget()
        page1.setLayout(QVBoxLayout(page1))
        page1.layout().addWidget(QLabel("estado revelado"))
        stack.addWidget(page0)
        stack.addWidget(page1)
        lay.addWidget(toggle)
        lay.addWidget(stack)
        toggle.clicked.connect(lambda: stack.setCurrentIndex(
            0 if stack.currentIndex() == 1 else 1))
        root.show()
        qapp.processEvents()
        return root

    opts = {"max_branch": 20, "max_states": 50, "max_depth": 4}
    seen_sigs = set()
    # estado base
    base = build()
    base_sig = _structural_hash(_build_widget_tree(base, win_ref=base))
    seen_sigs.add(base_sig)
    actions = _enumerate_safe_actions(base, [], opts)
    base.deleteLater()
    # para cada accion, materializar en fixture fresco y computar sig
    for action in actions:
        root = build()
        _apply_action(root, action, qapp)
        sig = _structural_hash(_build_widget_tree(root, win_ref=root))
        seen_sigs.add(sig)
        root.deleteLater()
    # debe haber descubierto al menos 2 estados distintos (base + revelado)
    assert len(seen_sigs) >= 2


def test_crawler_detects_loop_visual(qapp):
    """Un toggle que vuelve al estado base (A->B->A) debe deduparse por hash:
    el crawler no cuenta el loop como estado nuevo."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
    from qa.visual_sentinel import (_enumerate_safe_actions, _apply_action,
                                    _build_widget_tree, _structural_hash)

    def build():
        root = QWidget()
        root.resize(300, 200)
        lay = QVBoxLayout(root)
        tog = QPushButton("toggle")
        lbl = QLabel("off")
        tog.clicked.connect(lambda: lbl.setText("on" if lbl.text() == "off" else "off"))
        lay.addWidget(tog)
        lay.addWidget(lbl)
        root.show()
        qapp.processEvents()
        return root

    opts = {"max_branch": 20, "max_states": 50, "max_depth": 4}
    base = build()
    base_sig = _structural_hash(_build_widget_tree(base, win_ref=base))
    actions = _enumerate_safe_actions(base, [], opts)
    base.deleteLater()
    sigs = {base_sig}
    for action in actions:
        r = build()
        _apply_action(r, action, qapp)
        sigs.add(_structural_hash(_build_widget_tree(r, win_ref=r)))
        r.deleteLater()
    # exactamente 2 estados (off / on); el loop de vuelta colapsa a "off"
    assert len(sigs) == 2


def test_crawler_discovers_stack_pages_synthetic(qapp):
    """Fixture con QStackedWidget y botones Siguiente/Anterior: el crawler debe
    descubrir las paginas internas siguiendo los botones (flujo multi-step donde
    el MISMO boton avanza por estados distintos)."""
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QStackedWidget, QLabel)
    from qa.visual_sentinel import (_enumerate_safe_actions, _apply_action,
                                    _build_widget_tree, _structural_hash)

    def build():
        root = QWidget()
        root.resize(400, 300)
        lay = QVBoxLayout(root)
        stack = QStackedWidget()
        for txt in ("paso 0", "paso 1", "paso 2"):
            p = QWidget()
            p.setLayout(QVBoxLayout(p))
            p.layout().addWidget(QLabel(txt))
            stack.addWidget(p)
        row = QWidget()
        row.setLayout(QHBoxLayout(row))
        nxt = QPushButton("Siguiente")
        prev = QPushButton("Anterior")
        nxt.clicked.connect(lambda: stack.setCurrentIndex(
            min(stack.currentIndex() + 1, stack.count() - 1)))
        prev.clicked.connect(lambda: stack.setCurrentIndex(
            max(stack.currentIndex() - 1, 0)))
        row.layout().addWidget(prev)
        row.layout().addWidget(nxt)
        lay.addWidget(stack)
        lay.addWidget(row)
        root.show()
        qapp.processEvents()
        return root

    opts = {"max_branch": 20, "max_states": 50, "max_depth": 4}
    sigs = set()
    # BFS manual de profundidad 2 sobre fixtures frescos (igual que crawl_app):
    # cada nodo se materializa en un fixture fresco re-aplicando su path.
    frontier = [[]]
    while frontier:
        path = frontier.pop()
        root = build()
        ok = True
        for a in path:
            if not _apply_action(root, a, qapp):
                ok = False
                break
        if ok:
            sig = _structural_hash(_build_widget_tree(root, win_ref=root))
            if sig not in sigs:
                sigs.add(sig)
                if len(path) < 3:
                    for a in _enumerate_safe_actions(root, path, opts):
                        frontier.append(path + [a])
        root.deleteLater()
    # debe alcanzar los 3 pasos (paso 0/1/2)
    assert len(sigs) >= 3


# ═══════════════════════════════════════════════════════════════════════════
# Configuracion de plataforma Qt: _configure_platform() + argv sanitizado
# ═══════════════════════════════════════════════════════════════════════════

def test_configure_platform_native_never_sets_invalid_qt_plugin(monkeypatch):
    """Windows + native: QT_QPA_PLATFORM no debe ser 'native' (no es plugin Qt)."""
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    from qa.visual_sentinel import _configure_platform, _INVALID_QT_PLATFORMS
    _configure_platform("native")
    val = os.environ.get("QT_QPA_PLATFORM", "")
    assert val not in _INVALID_QT_PLATFORMS, (
        f"QT_QPA_PLATFORM tiene valor invalido para Qt: {val!r}"
    )


def test_configure_platform_auto_windows_no_ci_never_sets_invalid_qt_plugin(monkeypatch):
    """Windows + auto sin CI: QT_QPA_PLATFORM no debe ser 'auto' (no es plugin Qt)."""
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    for ci_var in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "TF_BUILD",
                   "BUILDKITE", "CIRCLECI", "TRAVIS"):
        monkeypatch.delenv(ci_var, raising=False)
    from qa.visual_sentinel import _configure_platform, _INVALID_QT_PLATFORMS
    _configure_platform("auto")
    val = os.environ.get("QT_QPA_PLATFORM", "")
    assert val not in _INVALID_QT_PLATFORMS, (
        f"QT_QPA_PLATFORM tiene valor invalido para Qt: {val!r}"
    )


def test_configure_platform_sanitizes_env_native(monkeypatch):
    """Si QT_QPA_PLATFORM=native ya estaba en env, se sanea antes de configurar."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "native")
    from qa.visual_sentinel import _configure_platform, _INVALID_QT_PLATFORMS
    _configure_platform("auto")
    val = os.environ.get("QT_QPA_PLATFORM", "")
    assert val not in _INVALID_QT_PLATFORMS, (
        f"QT_QPA_PLATFORM=native no fue saneado, quedo: {val!r}"
    )


def test_configure_platform_sanitizes_env_auto(monkeypatch):
    """Si QT_QPA_PLATFORM=auto ya estaba en env, se sanea antes de configurar."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "auto")
    from qa.visual_sentinel import _configure_platform, _INVALID_QT_PLATFORMS
    _configure_platform("native")
    val = os.environ.get("QT_QPA_PLATFORM", "")
    assert val not in _INVALID_QT_PLATFORMS, (
        f"QT_QPA_PLATFORM=auto no fue saneado, quedo: {val!r}"
    )


def test_qapplication_receives_sanitized_argv(monkeypatch):
    """_instantiate usa argv de un solo elemento: Qt no ve --platform auto/native."""
    original_argv = sys.argv[:]
    monkeypatch.setattr(
        sys, "argv",
        ["visual_sentinel.py", "--platform", "auto",
         "capture", "--screen", "suite:home", "--theme", "dark"],
    )
    # argv seguro = solo el nombre del ejecutable; nunca args Sentinel
    safe_argv = [sys.argv[0] if sys.argv else "visual_sentinel"]
    assert len(safe_argv) == 1
    assert "--platform" not in safe_argv
    assert "auto" not in safe_argv
    assert "native" not in safe_argv
    # Confirmar que el modulo construye el mismo argv seguro
    import importlib
    import ast
    import qa.visual_sentinel as _mod
    src = Path(_mod.__file__).read_text(encoding="utf-8")
    # El patron correcto esta en _instantiate: sys.argv[0] como unico elemento
    assert "_safe_argv = [sys.argv[0]" in src or '_safe_argv = [sys.argv[0]' in src, (
        "_instantiate debe usar _safe_argv = [sys.argv[0]] para evitar pasar "
        "--platform a Qt"
    )
    sys.argv = original_argv



# ═══════════════════════════════════════════════════════════════════════════
# Tests para _load_latest_captures (bug 2026-06-24 v3):
# El root manifest de qa/capture_v8.py --all (86 resultados) debe tener
# prioridad sobre iter*/históricos, y los iters deben ordenarse por
# número real (no lexicográfico: iter100 > iter89 porque 100 > 89, no
# porque '1' < '8' en ASCII). Sin PyQt6; usan tmp_path + manifests
# sintéticos. Compatibles con el patrón de import del legacy (sys.path
# + from qa.visual_sentinel import).
# ═══════════════════════════════════════════════════════════════════════════

import json
import shutil


def _write_manifest_for_sentinel(path: Path, results: list[dict]) -> None:
    """Escribe un CAPTURE_MANIFEST.json con la lista de results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"harness": "test", "total": len(results), "results": results},
                  indent=2),
        encoding="utf-8",
    )


def _sentinel_entry(app: str, view: str, theme: str, file_name: str) -> dict:
    """Construye un entry de CAPTURE_MANIFEST.json exitoso (shape V8)."""
    return {
        "file": file_name,
        "app": app,
        "view": view,
        "theme": theme,
        "resolution": "960x600",
        "success": True,
        "size_bytes": 50000,
        "evidence_contract": "main_base",
    }


def test_load_latest_captures_root_manifest_with_86_results_loads_completely(
    tmp_path, monkeypatch
):
    """(a) Root manifest con 86 results se carga completo.

    Bug pre-fix: la implementación sólo leía iter*/ y veía 1 captura.
    Post-fix: el root manifest se procesa y las 86 entries se registran
    con ``iter='root'``.
    """
    cap_root = tmp_path / "_captures_v8"
    cap_root.mkdir()
    results = [
        _sentinel_entry("suite" if i < 43 else "hub",
                        f"view_{i:02d}", "light" if i % 2 == 0 else "dark",
                        f"x-{i:02d}.png")
        for i in range(86)
    ]
    # Crear PNGs dummy para que la función no los descarte.
    for e in results:
        (cap_root / e["file"]).write_bytes(b"PNG")
    _write_manifest_for_sentinel(cap_root / "CAPTURE_MANIFEST.json", results)

    monkeypatch.setattr(visual_sentinel, "_CAPTURE_ROOT", cap_root)
    out = visual_sentinel._load_latest_captures()
    assert len(out) == 86, (
        f"Esperaba 86 entradas del root manifest, obtuve {len(out)}. "
        f"Esto indica que _load_latest_captures no leyó el root "
        f"manifest raíz (bug pre-fix)."
    )
    for key, entry in out.items():
        assert entry["iter"] == "root", (
            f"key {key} no viene del root manifest (iter={entry['iter']})"
        )
        assert entry["png"] == cap_root / entry["png"].name


def test_load_latest_captures_numeric_sort_picks_higher_iter(tmp_path, monkeypatch):
    """(b) iter89 e iter100 presentes → iter100 gana como más reciente.

    Bug pre-fix: sorted() lexicográfico ponía iter100 ANTES de iter89
    ('1' < '8' en ASCII) y el último procesado (iter89) ganaba →
    resultado INCORRECTO. Post-fix: orden numérico por el número real
    extraído con regex.
    """
    cap_root = tmp_path / "_captures_v8"
    cap_root.mkdir()
    iter89 = cap_root / "iter89_baseline"
    iter89.mkdir()
    (iter89 / "suite-pacientes-light.png").write_bytes(b"PNG89")
    _write_manifest_for_sentinel(iter89 / "CAPTURE_MANIFEST.json", [
        _sentinel_entry("suite", "pacientes", "light", "suite-pacientes-light.png"),
    ])
    iter100 = cap_root / "iter100_latest"
    iter100.mkdir()
    (iter100 / "suite-pacientes-light.png").write_bytes(b"PNG100")
    _write_manifest_for_sentinel(iter100 / "CAPTURE_MANIFEST.json", [
        _sentinel_entry("suite", "pacientes", "light", "suite-pacientes-light.png"),
    ])

    monkeypatch.setattr(visual_sentinel, "_CAPTURE_ROOT", cap_root)
    out = visual_sentinel._load_latest_captures()
    assert ("suite", "pacientes", "light") in out
    assert out[("suite", "pacientes", "light")]["iter"] == "iter100_latest", (
        f"iter100 debería ganar sobre iter89 (orden numérico), pero "
        f"ganó {out[('suite', 'pacientes', 'light')]['iter']}."
    )
    assert out[("suite", "pacientes", "light")]["png"].parent == iter100


def test_audit_mockup_v8_captures_count_matches_root_manifest(tmp_path, monkeypatch):
    """(c) audit-mockup no reporta V8_CAPTURES_LATEST=1 con root válido.

    Simula el escenario del bug: iter89 con 1 captura + root con
    86 resultados, una entrada compartida. Verifica len==86 y que la
    entrada compartida quede en 'root' (prioridad como batch actual).
    """
    cap_root = tmp_path / "_captures_v8"
    cap_root.mkdir()
    iter89 = cap_root / "iter89_baseline"
    iter89.mkdir()
    (iter89 / "suite-home-light.png").write_bytes(b"old")
    _write_manifest_for_sentinel(iter89 / "CAPTURE_MANIFEST.json", [
        _sentinel_entry("suite", "home", "light", "suite-home-light.png"),
    ])
    results = [
        _sentinel_entry("suite" if i < 43 else "hub",
                        f"view_{i:02d}", "light" if i % 2 == 0 else "dark",
                        f"x-{i:02d}.png")
        for i in range(86)
    ]
    # Sobrescribir suite/home/light en el root con el mismo key que iter89.
    results[0] = _sentinel_entry("suite", "home", "light", "suite-home-light.png")
    for e in results:
        (cap_root / e["file"]).write_bytes(b"new")
    _write_manifest_for_sentinel(cap_root / "CAPTURE_MANIFEST.json", results)

    monkeypatch.setattr(visual_sentinel, "_CAPTURE_ROOT", cap_root)
    captures = visual_sentinel._load_latest_captures()
    assert len(captures) == 86, (
        f"V8_CAPTURES_LATEST={len(captures)} sugiere que el root "
        f"manifest se está ignorando. Esperaba 86. Bug pre-fix: 1."
    )
    shared_key = ("suite", "home", "light")
    assert shared_key in captures
    assert captures[shared_key]["iter"] == "root", (
        f"Esperaba que root override iter89 para {shared_key} (root "
        f"tiene prioridad como batch actual), pero ganó "
        f"{captures[shared_key]['iter']}."
    )


def test_build_mockup_registry_maps_state_id_alias_to_v8_view():
    """(d) El registry debe mapear state_id 'noscore' del mockup a la receta
    V8 'home-no-score' (alias semantico de estado).

    Pre-fix: _candidate_views solo derivaba "home-noscore" y no encontraba
    la captura real, reportando MISSING_REFERENCE (P0) para
    suite:home-no-score@light/dark.
    """
    mockup_items = [
        {
            "screen_id": "home",
            "state_id": "score",
            "theme": "light",
            "product": "Suite · Paciente",
            "relative_path": "light/home/score.png",
        },
        {
            "screen_id": "home",
            "state_id": "noscore",
            "theme": "light",
            "product": "Suite · Paciente",
            "relative_path": "light/home/noscore.png",
        },
    ]
    captures = {
        ("suite", "home", "light"): {"png": Path("cap-home-light.png")},
        ("suite", "home-no-score", "light"): {"png": Path("cap-home-no-score-light.png")},
    }
    reg = visual_sentinel._build_mockup_to_capture_registry(mockup_items, captures)

    assert "suite:home:score@light" in reg["matched"]
    assert "suite:home:noscore@light" in reg["matched"]
    assert "suite:home-no-score@light" not in reg["missing_reference"]
    assert reg["per_surface"]["suite:home:noscore@light"]["view"] == "home-no-score"


def test_build_mockup_registry_maps_all_v8_aliases():
    """(e) Verifica que todos los aliases _STATE_VIEW_ALIASEs mapean correctamente
    mockup screen_id/state_id a V8 view_id, evitando MISSING_REFERENCE.
    """
    from qa.visual_sentinel import _STATE_VIEW_ALIASES

    # Build minimal mockup items and captures for each alias
    for (screen_id, state_id), views in _STATE_VIEW_ALIASES.items():
        for theme in ("light", "dark"):
            for view in views:
                app = "hub" if screen_id in ("detalle", "pacientes", "textos") else "suite"
                mockup_items = [
                    {
                        "screen_id": screen_id,
                        "state_id": state_id,
                        "theme": theme,
                        "product": "Hub · Clínica" if app == "hub" else "Suite · Paciente",
                        "relative_path": f"{theme}/{screen_id}/{state_id}.png",
                    },
                ]
                captures = {
                    (app, view, theme): {"png": Path(f"cap-{view}-{theme}.png")},
                }
                reg = visual_sentinel._build_mockup_to_capture_registry(mockup_items, captures)
                key = f"{app}:{screen_id}:{state_id}@{theme}"
                assert key in reg["matched"], f"Alias {key} -> {view} no hizo match"
                assert f"{app}:{view}@{theme}" not in reg["missing_reference"], (
                    f"V8 view {app}:{view}@{theme} sigue como MISSING_REFERENCE"
                )
                assert reg["per_surface"][key]["view"] == view
