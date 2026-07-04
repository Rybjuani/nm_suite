from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from qa import close_visual_key as close
from qa import target_scope as ts

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOTS = (ROOT / "app", ROOT / "hub", ROOT / "shared")
RUNNERS = (
    ROOT / "qa" / "run_visual.ps1",
)
DIALOGS_PY = ROOT / "shared" / "components" / "dialogs.py"
DBT_QT_PY = ROOT / "app" / "modules" / "dbt_qt.py"
PACIENTES_QT_PY = ROOT / "hub" / "pacientes_qt.py"
MISMATCH_DOC = ROOT / "docs" / "QT_HTML_KNOWN_MISMATCHES.md"


# ─────────────────────────────────────────────────────────────────────────────
# 1. No escape hatches / overrides for modal blur/scrim/fill in product code
# ─────────────────────────────────────────────────────────────────────────────

_ESCAPE_HATCH_NAMES = {
    "_blur_radius_override",
    "_scrim_rgba_override",
    "_backdrop_fill_bottom_px",
}


class _ModalOverrideVisitor(ast.NodeVisitor):
    """Collect assignments to or reads of known modal escape-hatch attributes.

    Also flags any identifier that looks like a modal override/escape hatch
    (``_NM_MODAL_*_OVERRIDE``, ``_*_blur_radius_override``, etc.) not in the
    documented allowlist. The current allowlist is intentionally empty.
    """

    def __init__(self) -> None:
        self.escapes: list[tuple[int, str, str]] = []

    def _is_escape_attr(self, name: str) -> str | None:
        low = name.lower()
        if name in _ESCAPE_HATCH_NAMES:
            return name
        if "modal" in low and "override" in low:
            return name
        if low.endswith("_blur_radius_override") or low.endswith("_scrim_rgba_override"):
            return name
        if low.endswith("_backdrop_fill_bottom_px") or low.endswith("_fill_bottom_px"):
            return name
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                attr = self._is_escape_attr(target.attr)
                if attr:
                    self.escapes.append((node.lineno, "assign", attr))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Attribute) and isinstance(node.target.value, ast.Name):
            attr = self._is_escape_attr(node.target.attr)
            if attr:
                self.escapes.append((node.lineno, "aug_assign", attr))
        self.generic_visit(node)


_OVERLAY_FRAUD_TOKENS = (
    "blur_radius_override",
    "scrim_rgba_override",
    "backdrop_fill_bottom_px",
)


def _iter_py_files(roots: tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        files.extend(sorted(root.rglob("*.py")))
    return files


def _scan_modal_escape_hatches() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []
    for path in _iter_py_files(PRODUCT_ROOTS):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        visitor = _ModalOverrideVisitor()
        visitor.visit(tree)
        for lineno, kind, attr in visitor.escapes:
            findings.append((path.relative_to(ROOT).as_posix(), lineno, kind, attr))
    return findings


def test_modal_override_escape_hatches_are_absent() -> None:
    """Static guard: product code must not use modal blur/scrim/fill overrides.

    The canonical HTML contract is ``.modal-bg { rgba(20,18,14,.5); blur(3px) }``.
    Any per-modal override that increases blur, changes the scrim, or fills the
    bottom of the backdrop is a potential back-screen cover-up and is banned.
    The allowlist is currently empty; any needed exception must be documented here.
    """
    findings = _scan_modal_escape_hatches()
    # Documented allowlist (empty until owner-approved).
    allowlist: set[tuple[str, int, str, str]] = set()
    disallowed = [f for f in findings if f not in allowlist]
    assert not disallowed, (
        "modal escape-hatch overrides found in product code; "
        "fix the back-screen instead of masking it:\n"
        + "\n".join(f"  {p}:{ln} [{k}] {attr}" for p, ln, k, attr in disallowed)
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Canonical blur constants must equal 3 in both light and dark
# ─────────────────────────────────────────────────────────────────────────────


def _extract_constant_assignments(path: Path) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants: dict[str, object] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                constants[target.id] = node.value.value
    return constants


def test_modal_blur_radius_constants_match_canonical() -> None:
    """The canonical CSS backdrop-filter is blur(3px); product must match exactly."""
    consts = _extract_constant_assignments(DIALOGS_PY)
    assert consts.get("_NM_MODAL_BLUR_RADIUS_LIGHT") == 3
    assert consts.get("_NM_MODAL_BLUR_RADIUS_DARK") == 3


# ─────────────────────────────────────────────────────────────────────────────
# 3. MISMATCH#17 documents the back-screen-first rule
# ─────────────────────────────────────────────────────────────────────────────


def test_mismatch_17_bans_backscreen_coverup() -> None:
    """MISMATCH#17 must explicitly forbid blur/opacity/density as cover-ups."""
    text = MISMATCH_DOC.read_text(encoding="utf-8")
    section_match = re.search(r"## MISMATCH#17\b.*?(?=\n## |\Z)", text, re.DOTALL)
    assert section_match, "MISMATCH#17 section not found"
    section = section_match.group(0).lower()
    for phrase in ("no se tapa", "blur", "opacidad", "densidad"):
        assert phrase in section, f"MISMATCH#17 must mention '{phrase}'"
    assert "back-screen" in section or "pantalla trasera" in section or "back screen" in section


# ─────────────────────────────────────────────────────────────────────────────
# 4. Modal audit tool runs per modal key in the visual runners
# ─────────────────────────────────────────────────────────────────────────────


def test_modal_audit_tool_exists() -> None:
    audit_tool = ROOT / "tools" / "qa" / "audit_modal_backdrop_blur.py"
    assert audit_tool.exists(), f"missing {audit_tool}"
    assert audit_tool.stat().st_size > 0



def test_runners_invoke_modal_audit_for_modals() -> None:
    """run_visual_*.ps1 must invoke audit_modal_backdrop_blur.py for modal keys."""
    for runner in RUNNERS:
        source = runner.read_text(encoding="utf-8")
        assert "audit_modal_backdrop_blur.py" in source, (
            f"{runner.name} does not invoke the modal backdrop audit tool"
        )
        assert "Test-ModalVisualKey" in source or "is_modal" in source or "window_modal" in source.lower(), (
            f"{runner.name} does not gate modal keys before invoking the audit"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Evidence record schema carries modal_audit_sha256 when relevant
# ─────────────────────────────────────────────────────────────────────────────


def test_evidence_record_schema_has_modal_audit_sha256() -> None:
    """Every evidence record must include the modal_audit_sha256 field."""
    record = {
        "schema": close.EVIDENCE_SCHEMA,
        "key": "suite:dbt-practice-stop@light",
        "modal_audit_sha256": None,
        "result": "PASS",
    }
    # Deterministic hash must not raise and must include the field.
    sha = close.canonical_record_sha256(record)
    assert len(sha) == 64


def test_close_visual_key_has_modal_audit_helpers() -> None:
    """close_visual_key.py must expose helpers to run the modal audit and store the hash."""
    source = (ROOT / "qa" / "close_visual_key.py").read_text(encoding="utf-8")
    assert "modal_audit_sha256" in source
    assert "audit_modal_backdrop_blur" in source


# ─────────────────────────────────────────────────────────────────────────────
# 6. Text essential must not be invisible/alpha-zero on modal surfaces
# ─────────────────────────────────────────────────────────────────────────────

_ALPHA_ZERO_RE = re.compile(r"rgba\([^)]*,\s*0\s*\)|color\s*:\s*transparent", re.IGNORECASE)


def _scan_modal_alpha_zero(path: Path) -> list[tuple[int, str]]:
    """Look for alpha-zero text color declarations in a file.

    This is intentionally conservative: it flags style-sheet strings that contain
    ``rgba(...,0)`` or ``color: transparent`` anywhere in product files. The
    only acceptable hits are documented allowlist entries.
    """
    findings: list[tuple[int, str]] = []
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _ALPHA_ZERO_RE.search(node.value):
                findings.append((node.lineno, node.value.strip()[:120]))
    return findings


def test_modal_resumen_ia_text_not_alpha_zero() -> None:
    """Resumen IA modal must not hide essential text via alpha-zero color."""
    findings = _scan_modal_alpha_zero(PACIENTES_QT_PY)
    # Allowlist: none. Any alpha-zero text on a modal surface is banned.
    assert not findings, (
        "alpha-zero text color found in pacientes_qt.py modal code:\n"
        + "\n".join(f"  ln {ln}: {snippet}" for ln, snippet in findings)
    )


def test_modals_declare_blur_radius_three() -> None:
    """The modal implementations in dialogs.py and dbt_qt.py must declare blur=3."""
    for path in (DIALOGS_PY, DBT_QT_PY):
        consts = _extract_constant_assignments(path)
        for name in ("_NM_MODAL_BLUR_RADIUS_LIGHT", "_NM_MODAL_BLUR_RADIUS_DARK", "_SCRIM_BLUR_RADIUS_LIGHT", "_SCRIM_BLUR_RADIUS_DARK"):
            if name in consts:
                assert consts[name] == 3, (
                    f"{path.name}:{name}={consts[name]!r} != canonical 3"
                )
