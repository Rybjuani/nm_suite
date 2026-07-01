#!/usr/bin/env python3
"""Static anti-fraud scan for runtime/product code.

Forbids product/runtime code (``app/``, ``hub/``, ``shared/``) from reading,
loading, rendering, copying, mounting or overlaying canonical / reference /
mockup / QA-report artifacts in order to pass — or appear to pass — a visual
comparison. This is the static guard for the anti-fraud rule documented in
``VISUAL_QA_AGENT_PROTOCOL.md`` and ``VISUAL_REPAIR_HANDOFF.md`` (the rule that
was violated by the recovery reference overlay).

What it flags (in app/hub/shared only):
  - String literals pointing at QA/canonical/reference artifacts
    (``qa/_mockup_canonical``, ``qa/mockup_reference_static``, ``reports/qa``,
    ``LAYERED_VISUAL_REPORT``, ``mockup_reparado``, ``pack canonico``,
    ``_captures_v8`` …).
  - Reference-overlay identifiers (``*reference_overlay*``, the
    ``RecoverReferenceOverlay`` class family).
  - ``QPixmap`` / ``QImage`` / ``QIcon`` / ``setPixmap`` / ``setIcon`` calls whose
    arguments reference a QA/canonical/reference artifact.

What it does NOT do:
  - It does NOT forbid ``QPixmap`` globally — only its use with QA/reference
    artifacts. Loading product assets (``assets/...``) is fine.

Usage::

    python qa/anti_fraud_scan.py                 # scan app/ hub/ shared/, exit 1 on violation
    python qa/anti_fraud_scan.py --roots app     # scan a subset
    python qa/anti_fraud_scan.py --json out.json # also write a JSON report

If this scan fails, NO visual report may be used as valid closure evidence,
even if the comparator reports PASS.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = ("app", "hub", "shared")

# Substrings (matched case-insensitively) that must never appear in a product
# string literal. These point at canonical/reference/mockup/QA-report artifacts.
FORBIDDEN_STRING_TOKENS = (
    "_mockup_canonical",
    "mockup_reference",
    "mockup_reference_static",
    "mockup_reparado",
    "pack canonico",
    "layered_visual_report",
    "reports/qa",
    "reports\\qa",
    "_captures_v8",
)

# Substrings (case-insensitive) forbidden in product identifiers: reference
# overlay machinery that paints a canonical/reference artifact over real UI.
FORBIDDEN_NAME_TOKENS = (
    "reference_overlay",
    "referenceoverlay",
    "mockup_overlay",
    "canonical_overlay",
)

# Image-loading calls that must not be fed a QA/reference artifact.
PIXMAP_FUNCS = {"QPixmap", "QImage", "QIcon"}
PIXMAP_METHODS = {"setPixmap", "setIcon", "addPixmap", "setImage"}
# Broader proximity tokens for the pixmap-with-reference check.
PIXMAP_REFERENCE_TOKENS = (
    "canonical",
    "mockup",
    "reference",
    "reports/qa",
    "reports\\qa",
    "_captures",
    "/qa/",
    "\\qa\\",
)

# Canonical modal backdrop contract (HTML mockup). Product code must match exactly.
_CANONICAL_MODAL_BLUR_RADIUS = 3
_CANONICAL_MODAL_SCRIM_RGBA = (20, 18, 14, 128)
_MODAL_BLUR_CONSTANTS = {
    # NMDialog (shared/components/dialogs.py)
    "_NM_MODAL_BLUR_RADIUS_LIGHT": _CANONICAL_MODAL_BLUR_RADIUS,
    "_NM_MODAL_BLUR_RADIUS_DARK": _CANONICAL_MODAL_BLUR_RADIUS,
    # _PracticeModalScrim (app/modules/dbt_qt.py) — same canonical contract.
    "_SCRIM_BLUR_RADIUS_LIGHT": _CANONICAL_MODAL_BLUR_RADIUS,
    "_SCRIM_BLUR_RADIUS_DARK": _CANONICAL_MODAL_BLUR_RADIUS,
}
# Scrim RGBA constants that must match the canonical (20, 18, 14, 128).
# Both NMDialog and _PracticeModalScrim use the same canonical scrim.
_MODAL_SCRIM_CONSTANTS = {
    "_NM_MODAL_SCRIM_RGBA",
    "_SCRIM_RGBA",
}
_MODAL_BACKDROP_FRAUD_MESSAGE = (
    "fixea primero la pantalla de atras y despues seguis con el modal"
)


@dataclass
class Violation:
    file: str
    line: int
    kind: str
    pattern: str
    snippet: str

    def to_dict(self) -> dict:
        return asdict(self)


def _iter_py_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".py":
            files.append(root)
            continue
        files.extend(sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts))
    return files


def _string_constants(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node


def _call_string_args(node: ast.Call):
    """Yield string-literal values appearing anywhere inside a call's args."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            yield sub.value


def _eval_static_literal(node: ast.AST) -> object | None:
    """Evaluate a simple literal (number or tuple of numbers) from an AST node."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        values = [_eval_static_literal(elt) for elt in node.elts]
        if any(v is None for v in values):
            return None
        return tuple(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _eval_static_literal(node.operand)
        if isinstance(inner, (int, float)):
            return -inner
    return None


def _scan_modal_backdrop_constants(tree: ast.AST, file_label: str, lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []

    def snippet(lineno: int) -> str:
        idx = lineno - 1
        if 0 <= idx < len(lines):
            return lines[idx].strip()[:200]
        return ""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = _eval_static_literal(node.value)
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if name in _MODAL_BLUR_CONSTANTS:
                expected = _MODAL_BLUR_CONSTANTS[name]
                if value != expected:
                    violations.append(
                        Violation(
                            file_label,
                            getattr(node, "lineno", 0),
                            "modal_backdrop_constant",
                            f"{name}={value!r} expected {expected!r}; {_MODAL_BACKDROP_FRAUD_MESSAGE}",
                            snippet(getattr(node, "lineno", 0)),
                        )
                    )
            elif name in _MODAL_SCRIM_CONSTANTS:
                if value != _CANONICAL_MODAL_SCRIM_RGBA:
                    violations.append(
                        Violation(
                            file_label,
                            getattr(node, "lineno", 0),
                            "modal_backdrop_constant",
                            f"{name}={value!r} expected {_CANONICAL_MODAL_SCRIM_RGBA!r}; {_MODAL_BACKDROP_FRAUD_MESSAGE}",
                            snippet(getattr(node, "lineno", 0)),
                        )
                    )
    return violations


def scan_source(source: str, file_label: str) -> list[Violation]:
    violations: list[Violation] = []
    lines = source.splitlines()

    def snippet(lineno: int) -> str:
        idx = lineno - 1
        if 0 <= idx < len(lines):
            return lines[idx].strip()[:200]
        return ""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fall back to a plain line scan so a syntax error can't hide a leak.
        for i, line in enumerate(lines, start=1):
            low = line.lower()
            for tok in FORBIDDEN_STRING_TOKENS + FORBIDDEN_NAME_TOKENS:
                if tok in low:
                    violations.append(Violation(file_label, i, "unparsed_token", tok, line.strip()[:200]))
        return violations

    # 1. Forbidden string literals (QA/canonical/reference artifact paths).
    for node in _string_constants(tree):
        low = node.value.lower()
        for tok in FORBIDDEN_STRING_TOKENS:
            if tok in low:
                violations.append(
                    Violation(file_label, getattr(node, "lineno", 0), "artifact_path_literal", tok, snippet(getattr(node, "lineno", 0)))
                )

    # 2. Forbidden identifiers (reference-overlay machinery).
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        for name in names:
            low = name.lower()
            for tok in FORBIDDEN_NAME_TOKENS:
                if tok in low:
                    violations.append(
                        Violation(file_label, getattr(node, "lineno", 0), "reference_overlay_identifier", name, snippet(getattr(node, "lineno", 0)))
                    )

    # 3. Pixmap/Image/Icon loads fed a QA/reference artifact (do NOT ban QPixmap
    #    itself — only its use with reference artifacts).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        target = None
        if isinstance(func, ast.Name) and func.id in PIXMAP_FUNCS:
            target = func.id
        elif isinstance(func, ast.Attribute) and func.attr in (PIXMAP_FUNCS | PIXMAP_METHODS):
            target = func.attr
        if target is None:
            continue
        for value in _call_string_args(node):
            low = value.lower()
            if any(tok in low for tok in PIXMAP_REFERENCE_TOKENS):
                violations.append(
                    Violation(file_label, getattr(node, "lineno", 0), "pixmap_reference_artifact", f"{target}(...{value[:60]}...)", snippet(getattr(node, "lineno", 0)))
                )
                break

    # 4. Modal backdrop constants must match the canonical HTML mockup contract.
    violations.extend(_scan_modal_backdrop_constants(tree, file_label, lines))

    # De-dup identical (line, kind, pattern) triples.
    seen = set()
    unique: list[Violation] = []
    for v in violations:
        sig = (v.file, v.line, v.kind, v.pattern)
        if sig not in seen:
            seen.add(sig)
            unique.append(v)
    return unique


def scan_file(path: Path, *, base: Path | None = None) -> list[Violation]:
    label = str(path.relative_to(base)) if base else str(path)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return scan_source(source, label)


def scan_paths(roots, *, base: Path | None = None) -> list[Violation]:
    base = base or _PROJ
    root_paths = [(base / r) if not Path(r).is_absolute() else Path(r) for r in roots]
    violations: list[Violation] = []
    for path in _iter_py_files(root_paths):
        violations.extend(scan_file(path, base=base))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static anti-fraud scan for runtime/product code.")
    parser.add_argument("--roots", nargs="*", default=list(DEFAULT_ROOTS), help="Roots to scan (default: app hub shared).")
    parser.add_argument("--json", default=None, help="Optional path to write a JSON report.")
    args = parser.parse_args(argv)

    violations = scan_paths(args.roots)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {"clean": not violations, "count": len(violations), "violations": [v.to_dict() for v in violations]},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    print("=" * 60)
    print("ANTI-FRAUD STATIC SCAN (runtime/product)")
    print(f"Roots: {', '.join(args.roots)}")
    if not violations:
        print("Result: CLEAN - no canonical/reference/mockup artifact usage found.")
        print("=" * 60)
        return 0
    print(f"Result: FAIL - {len(violations)} violation(s).")
    print("Runtime/product must never read/render/overlay canonical/reference artifacts.")
    print("A report produced while this scan fails is NOT valid closure evidence.")
    print("-" * 60)
    for v in violations:
        print(f"  {v.file}:{v.line}  [{v.kind}] pattern={v.pattern!r}")
        if v.snippet:
            print(f"      {v.snippet}")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
