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
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = ("app", "hub", "shared")

# Asset-vs-canonical identity scan. A canonical PNG smuggled into the product as
# a plain asset (a path with no forbidden token) defeats the string/AST scan, so
# the runtime could render it and pass the visual compare by injection. This
# byte-identity check closes the verbatim-copy path at the source; the noised
# variant is closed at compare time by the density-aware injection ceiling in
# qa/layered_visual_compare.py. Stdlib-only (hashlib) so it runs in CI.
CANONICAL_PNG_DIRS = ("qa/_mockup_canonical", "qa/pack canonico")
ASSET_IDENTITY_ROOTS = ("assets", "app", "hub", "shared")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_png_hashes(base: Path) -> dict[str, str]:
    """sha256 -> canonical filename, for every canonical PNG."""
    hashes: dict[str, str] = {}
    for rel in CANONICAL_PNG_DIRS:
        root = base / rel
        if not root.exists():
            continue
        for png in root.rglob("*.png"):
            hashes[_sha256_path(png)] = png.name
    return hashes


def scan_asset_canonical_identity(base: Path | None = None) -> list["Violation"]:
    """Flag any product PNG byte-identical to a canonical PNG (smuggled asset)."""
    base = base or _PROJ
    canon = _canonical_png_hashes(base)
    if not canon:
        return []
    violations: list[Violation] = []
    for rel in ASSET_IDENTITY_ROOTS:
        root = base / rel
        if not root.exists():
            continue
        for png in sorted(root.rglob("*.png")):
            if "__pycache__" in png.parts:
                continue
            digest = _sha256_path(png)
            name = canon.get(digest)
            if name is not None:
                violations.append(
                    Violation(
                        str(png.relative_to(base)),
                        0,
                        "asset_canonical_identity",
                        name,
                        f"product PNG is byte-identical to canonical '{name}'",
                    )
                )
    return violations
QA_HARNESS_ROOTS = (
    "qa/capture_v8.py",
    "qa/layered_visual_compare.py",
    "qa/odiff_runner.py",
    "qa/vas_gate.py",
    "qa/vas_engine.py",
    "qa/vas_introspect.py",
    "qa/spec_generator.py",
    "qa/close_visual_key.py",
    "qa/replay_visual_closure.py",
    "tools/qa",
)

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

QA_CAPTURE_SOURCE_FORBIDDEN_TOKENS = (
    "_mockup_canonical",
    "mockup_reference",
    "mockup_reference_static",
    "mockup_reparado",
    "neuromood-mockup_reparado",
    "pack canonico",
    "reports/qa",
    "reports\\qa",
)
QA_CAPTURE_READ_FUNCS = {
    "open",
    "read_text",
    "read_bytes",
    "Image.open",
    "QImage",
    "QPixmap",
    "copy",
    "copy2",
    "copyfile",
    "move",
}
QA_ENV_ROUTE_TOKENS = ("CANON", "CANONICAL", "MOCKUP", "REFERENCE", "REPORT", "IMAGE", "PNG")
QA_CANONICAL_SOURCE_ALLOWED = (
    "qa/layered_visual_compare.py",
    "qa/visual_gate_calibration.py",
    "qa/spec_generator.py",
    "qa/visual_auditor_spec.py",
    # Orquestadores de cierre/replay: construyen la ruta canónica sólo para
    # pasarla como --canonical al comparador; no leen pixeles.
    "qa/close_visual_key.py",
    "qa/replay_visual_closure.py",
    "tools/qa/",
)
QA_OBFUSCATION_PRIMITIVES = {"chr", "eval", "exec"}
QA_COMMAND_SINKS = {
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
}
QA_ALLOWED_DYNAMIC_IMPORT_PREFIXES = (
    "app.",
    "hub.",
    "shared.",
    "qa.",
    "tools.qa.",
    "PyQt6",
    "PySide6",
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


def _eval_static_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                return None
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _eval_static_string(node.left)
        right = _eval_static_string(node.right)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _eval_static_string(node.left)
        right = _eval_static_string(node.right)
        if left is not None and right is not None:
            return f"{left}/{right}"
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "Path" and node.args:
            return _eval_static_string(node.args[0])
        if isinstance(func, ast.Attribute) and func.attr == "Path" and node.args:
            return _eval_static_string(node.args[0])
    return None


def _static_strings_in_call(node: ast.Call) -> list[str]:
    values: list[str] = []
    for arg in [*node.args, *[kw.value for kw in node.keywords]]:
        value = _eval_static_string(arg)
        if value is not None:
            values.append(value)
    return values


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parent = ""
        if isinstance(func.value, ast.Name):
            parent = func.value.id
        elif isinstance(func.value, ast.Attribute):
            parent = func.value.attr
        return f"{parent}.{func.attr}" if parent else func.attr
    return ""


def _has_forbidden_token(value: str, tokens: tuple[str, ...]) -> str | None:
    low = value.lower().replace("\\", "/")
    for token in tokens:
        normalized = token.lower().replace("\\", "/")
        if normalized in low:
            return token
    return None


def _qa_allows_canonical_source(file_label: str) -> bool:
    normalized = file_label.replace("\\", "/")
    return any(
        normalized == allowed.rstrip("/")
        or normalized.startswith(allowed)
        for allowed in QA_CANONICAL_SOURCE_ALLOWED
    )


def _is_literal_bytes_decode_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "decode":
        return False
    receiver = func.value
    if isinstance(receiver, ast.Constant) and isinstance(receiver.value, (bytes, bytearray)):
        return True
    if isinstance(receiver, ast.Call):
        return _call_name(receiver) in {"bytes", "bytearray"}
    return False


def _is_suspicious_getattr_os_call(node: ast.Call) -> bool:
    if _call_name(node) != "getattr" or len(node.args) < 2:
        return False
    target = node.args[0]
    target_name = ""
    if isinstance(target, ast.Name):
        target_name = target.id
    elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
        target_name = f"{target.value.id}.{target.attr}"
    if target_name not in {"os", "subprocess"}:
        return False
    attr_name = _eval_static_string(node.args[1]) or ""
    return attr_name in {"system", "popen", "run", "call", "check_call", "check_output"}


def _is_suspicious_import_module_call(node: ast.Call) -> bool:
    call_name = _call_name(node)
    if call_name not in {"importlib.import_module", "import_module"} and not call_name.endswith(".import_module"):
        return False
    if not node.args:
        return False
    module_name = _eval_static_string(node.args[0]) or ""
    if not module_name:
        return False
    normalized = module_name.replace("\\", "/")
    if _has_forbidden_token(normalized, QA_CAPTURE_SOURCE_FORBIDDEN_TOKENS):
        return True
    return not normalized.startswith(QA_ALLOWED_DYNAMIC_IMPORT_PREFIXES)


def _call_contains_obfuscation_sink(node: ast.Call) -> bool:
    call_name = _call_name(node)
    if call_name not in QA_COMMAND_SINKS:
        return False
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            sub_name = _call_name(sub)
            if sub_name.split(".")[-1] in QA_OBFUSCATION_PRIMITIVES:
                return True
            if _is_literal_bytes_decode_call(sub):
                return True
            if _is_suspicious_getattr_os_call(sub):
                return True
            if _is_suspicious_import_module_call(sub):
                return True
    return False


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


def scan_qa_harness_source(source: str, file_label: str) -> list[Violation]:
    violations: list[Violation] = []
    lines = source.splitlines()
    normalized_label = file_label.replace("\\", "/")
    is_capture_runtime = normalized_label.endswith("qa/capture_v8.py")
    allows_canonical = _qa_allows_canonical_source(normalized_label)

    def snippet(lineno: int) -> str:
        idx = lineno - 1
        if 0 <= idx < len(lines):
            return lines[idx].strip()[:200]
        return ""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        for i, line in enumerate(lines, start=1):
            token = _has_forbidden_token(line, QA_CAPTURE_SOURCE_FORBIDDEN_TOKENS)
            if token:
                violations.append(Violation(file_label, i, "qa_unparsed_artifact_token", token, line.strip()[:200]))
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = _call_name(node)
            short_name = call_name.split(".")[-1]
            if short_name in QA_OBFUSCATION_PRIMITIVES:
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_obfuscation_primitive",
                        call_name,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

            if _is_literal_bytes_decode_call(node):
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_literal_bytes_decode",
                        call_name,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

            if _is_suspicious_getattr_os_call(node):
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_getattr_os_command",
                        call_name,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

            if _is_suspicious_import_module_call(node):
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_suspicious_importlib",
                        call_name,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

            if _call_contains_obfuscation_sink(node):
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_obfuscated_command_sink",
                        call_name,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

            if call_name.endswith("b64decode") or short_name == "b64decode":
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_suspicious_base64_decode",
                        call_name,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

            if is_capture_runtime and short_name in QA_CAPTURE_READ_FUNCS:
                for value in _static_strings_in_call(node):
                    token = _has_forbidden_token(value, QA_CAPTURE_SOURCE_FORBIDDEN_TOKENS)
                    if token:
                        violations.append(
                            Violation(
                                file_label,
                                getattr(node, "lineno", 0),
                                "qa_capture_reads_reference_artifact",
                                token,
                                snippet(getattr(node, "lineno", 0)),
                            )
                        )

            if call_name in {"os.environ.get", "environ.get"} and node.args:
                env_name = _eval_static_string(node.args[0]) or ""
                if any(token in env_name.upper() for token in QA_ENV_ROUTE_TOKENS):
                    violations.append(
                        Violation(
                            file_label,
                            getattr(node, "lineno", 0),
                            "qa_env_artifact_route",
                            env_name,
                            snippet(getattr(node, "lineno", 0)),
                        )
                    )

        if isinstance(node, ast.Subscript):
            target = node.value
            target_name = ""
            if isinstance(target, ast.Attribute):
                target_name = f"{getattr(target.value, 'id', '')}.{target.attr}"
            elif isinstance(target, ast.Name):
                target_name = target.id
            if target_name in {"os.environ", "environ"}:
                env_name = _eval_static_string(node.slice) or ""
                if any(token in env_name.upper() for token in QA_ENV_ROUTE_TOKENS):
                    violations.append(
                        Violation(
                            file_label,
                            getattr(node, "lineno", 0),
                            "qa_env_artifact_route",
                            env_name,
                            snippet(getattr(node, "lineno", 0)),
                        )
                    )

        if isinstance(node, (ast.BinOp, ast.JoinedStr, ast.Call)):
            value = _eval_static_string(node)
            if value is None:
                continue
            token = _has_forbidden_token(value, QA_CAPTURE_SOURCE_FORBIDDEN_TOKENS)
            if not token:
                continue
            if allows_canonical:
                continue
            if is_capture_runtime or isinstance(node, (ast.BinOp, ast.JoinedStr)):
                violations.append(
                    Violation(
                        file_label,
                        getattr(node, "lineno", 0),
                        "qa_dynamic_artifact_path_construction",
                        token,
                        snippet(getattr(node, "lineno", 0)),
                    )
                )

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


def scan_qa_harness_file(path: Path, *, base: Path | None = None) -> list[Violation]:
    label = str(path.relative_to(base)) if base else str(path)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return scan_qa_harness_source(source, label)


def scan_paths(roots, *, base: Path | None = None) -> list[Violation]:
    base = base or _PROJ
    root_paths = [(base / r) if not Path(r).is_absolute() else Path(r) for r in roots]
    violations: list[Violation] = []
    for path in _iter_py_files(root_paths):
        violations.extend(scan_file(path, base=base))
    return violations


def scan_qa_harness_paths(roots, *, base: Path | None = None) -> list[Violation]:
    base = base or _PROJ
    root_paths = [(base / r) if not Path(r).is_absolute() else Path(r) for r in roots]
    violations: list[Violation] = []
    for path in _iter_py_files(root_paths):
        violations.extend(scan_qa_harness_file(path, base=base))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static anti-fraud scan for runtime/product and QA harness code.")
    parser.add_argument(
        "--mode",
        choices=("runtime", "qa-harness", "all"),
        default="runtime",
        help="Scan mode: runtime product code, QA harness code, or both.",
    )
    parser.add_argument("--roots", nargs="*", default=None, help="Roots to scan (mode-specific defaults if omitted).")
    parser.add_argument("--json", default=None, help="Optional path to write a JSON report.")
    args = parser.parse_args(argv)

    runtime_roots = args.roots if args.roots is not None else list(DEFAULT_ROOTS)
    qa_roots = args.roots if args.roots is not None else list(QA_HARNESS_ROOTS)
    violations: list[Violation] = []
    if args.mode in {"runtime", "all"}:
        violations.extend(scan_paths(runtime_roots))
        # Byte-identity of a canonical PNG smuggled as a product asset is a
        # runtime injection the AST scan can't see. Only run with default roots
        # (a custom --roots is a scoped AST scan, not a full asset audit).
        if args.roots is None:
            violations.extend(scan_asset_canonical_identity())
    if args.mode in {"qa-harness", "all"}:
        violations.extend(scan_qa_harness_paths(qa_roots))

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
    print(f"ANTI-FRAUD STATIC SCAN ({args.mode})")
    if args.mode == "runtime":
        roots_display = runtime_roots
    elif args.mode == "qa-harness":
        roots_display = qa_roots
    else:
        roots_display = [*runtime_roots, *qa_roots]
    print(f"Roots: {', '.join(roots_display)}")
    if not violations:
        print("Result: CLEAN - no canonical/reference/mockup artifact usage found.")
        print("=" * 60)
        return 0
    print(f"Result: FAIL - {len(violations)} violation(s).")
    print("Runtime/product and capture harnesses must never inject canonical/reference artifacts.")
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
