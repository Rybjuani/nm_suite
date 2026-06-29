"""Integrity contract for the Design-System Translation Bridge docs.

These are *documentation* contracts, not a visual gate. They keep the bridge
honest so the next visual checks can rely on it:

- every ``NM*``/``V3*`` component the bridge names must really exist in
  ``shared/`` (no stale/renamed/divergent component references);
- every file path the bridge cites must exist (no equivalence without a real
  source);
- every ``MISMATCH#n`` referenced must be defined in the mismatches doc (no
  dangling non-equivalence references);
- the canonical key set the bridge summarises must match the canonical index
  (86 keys) and the canonical sources must exist.

This does NOT duplicate the visual harness (``qa/layered_visual_compare.py``,
per-module ``*_visual_contract`` tests) nor the token-parity tests. It only
validates that the bridge documents point at things that are real.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

BRIDGE_DOCS = {
    "overview": DOCS / "DESIGN_SYSTEM_TRANSLATION_BRIDGE.md",
    "matrix": DOCS / "CSS_TO_PYQT_EQUIVALENCE_MATRIX.md",
    "catalog": DOCS / "VISUAL_COMPONENT_CATALOG.md",
    "mismatches": DOCS / "QT_HTML_KNOWN_MISMATCHES.md",
    "usage": DOCS / "BRIDGE_USAGE_FOR_AGENTS.md",
}

# Sources the bridge maps onto.
_SYMBOL_SOURCES = [
    ROOT / "shared" / "theme.py",
    ROOT / "shared" / "theme_qt.py",
    *sorted((ROOT / "shared" / "components").glob("*.py")),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _defined_symbols() -> set[str]:
    """All class/function/assignment names defined across the bridge sources."""
    names: set[str] = set()
    for path in _SYMBOL_SOURCES:
        tree = ast.parse(_read(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        names.add(tgt.id)
    return names


# ---------------------------------------------------------------------------


def test_all_five_bridge_docs_exist() -> None:
    missing = [name for name, path in BRIDGE_DOCS.items() if not path.exists()]
    assert not missing, f"missing bridge docs: {missing}"


def test_bridge_components_exist_in_source() -> None:
    """Every NM*/V3* component named by the matrix/catalog must be real."""
    defined = _defined_symbols()
    referenced: set[str] = set()
    for key in ("matrix", "catalog", "overview"):
        text = _read(BRIDGE_DOCS[key])
        referenced |= set(re.findall(r"\b(?:NM|V3)[A-Z][A-Za-z0-9_]*\b", text))
    assert referenced, "no components extracted — regex/doc drift"
    unknown = sorted(n for n in referenced if n not in defined)
    assert not unknown, f"bridge references undefined components: {unknown}"


def test_bridge_helpers_exist_in_source() -> None:
    """Token/helper functions the bridge leans on must exist."""
    defined = _defined_symbols()
    required = {
        "C", "v3c", "colors", "qfont", "v3_font", "nm_font",
        "shadow_effect", "v3_shadow", "paint_card_lift",
        "conical_arc_gradient", "radial_glow", "mood_gradient",
        "focus_ring_stylesheet", "stylesheet_lineedit", "stylesheet_textedit",
        "stylesheet_combobox", "label_style",
        "V3_LIGHT", "V3_DARK", "V3_RADIUS", "V3_SHADOWS", "TYPOGRAPHY",
        "MOOD_PALETTE", "LAYOUT", "V3_LIFT",
    }
    missing = sorted(required - defined)
    assert not missing, f"bridge cites helpers/tokens not in source: {missing}"


def test_referenced_mismatches_are_defined() -> None:
    """Every MISMATCH#n used in matrix/catalog is defined in the mismatches doc."""
    defined = set(
        re.findall(r"^##\s*MISMATCH#(\d+)\b", _read(BRIDGE_DOCS["mismatches"]),
                   flags=re.MULTILINE)
    )
    assert defined, "no MISMATCH#n headings found"
    used: set[str] = set()
    for key in ("matrix", "catalog"):
        used |= set(re.findall(r"MISMATCH#(\d+)\b", _read(BRIDGE_DOCS[key])))
    dangling = sorted(used - defined, key=int)
    assert not dangling, f"matrix/catalog reference undefined MISMATCH#: {dangling}"


def test_cited_file_paths_exist() -> None:
    """Every (space-free, non-glob) path cited by the bridge must resolve.

    Docs cite both full paths (``shared/components/cards.py``) and intentional
    shorthand (``cards.py`` inside a section already scoped to a family, or doc
    names relative to ``docs/``). A citation is valid if it resolves under any
    sensible base dir; this still catches typos / renamed files.
    """
    bases = [
        ROOT,
        ROOT / "docs",
        ROOT / "shared",
        ROOT / "shared" / "components",
        ROOT / "tests",
        ROOT / "qa",
        ROOT / "qa" / "_mockup_canonical",
        ROOT / "app",
        ROOT / "app" / "modules",
        ROOT / "hub",
    ]
    pattern = re.compile(r"`([A-Za-z0-9_][\w./-]*\.(?:py|md|csv|html))(?::\d+)?`")
    missing: set[str] = set()
    for key in ("overview", "matrix", "catalog", "mismatches", "usage"):
        for rel in pattern.findall(_read(BRIDGE_DOCS[key])):
            if "*" in rel or "…" in rel:
                continue
            if not any((base / rel).exists() for base in bases):
                missing.add(rel)
    assert not missing, f"bridge cites unresolvable paths: {sorted(missing)}"


def test_canonical_sources_exist_and_have_86_keys() -> None:
    canonical_html = ROOT / "qa" / "pack canonico" / "neuromood-mockup_reparado.html"
    index_csv = ROOT / "qa" / "_mockup_canonical" / "INDICE_CAPTURAS.csv"
    assert canonical_html.exists(), "canonical HTML source missing"
    assert index_csv.exists(), "canonical index CSV missing"

    rows = [r for r in _read(index_csv).splitlines() if r.strip()]
    data_rows = rows[1:]  # drop header
    assert len(data_rows) == 86, f"expected 86 canonical keys, got {len(data_rows)}"

    # The overview doc claims 86 keys; keep the claim in sync with the index.
    assert "= 86" in _read(BRIDGE_DOCS["overview"])


def test_matrix_covers_all_fifteen_families() -> None:
    text = _read(BRIDGE_DOCS["matrix"])
    missing = [f"F{i}" for i in range(1, 16) if f"## F{i} ·" not in text]
    assert not missing, f"matrix missing family sections: {missing}"
