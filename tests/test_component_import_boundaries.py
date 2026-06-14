"""Import boundary checks for the shared component package."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_LEAF_DIR = ROOT / "shared" / "components"
INTERNAL_IMPORT_ROOTS = (ROOT / "app", ROOT / "hub", ROOT / "qa", ROOT / "shared")


def _imports_for(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    return imported_modules


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def test_component_leaf_modules_do_not_import_public_or_compat_facades():
    offenders: list[tuple[str, str]] = []
    forbidden = {"shared.components", "shared.components_qt"}

    for path in _python_files(COMPONENT_LEAF_DIR):
        if path.name == "__init__.py":
            continue
        for module in _imports_for(path):
            if module in forbidden or module.startswith("shared.components_qt."):
                offenders.append((str(path.relative_to(ROOT)), module))

    assert offenders == []


def test_internal_code_does_not_import_compat_components_qt_facade():
    offenders: list[tuple[str, str]] = []
    allowed = {
        ROOT / "shared" / "components_qt.py",
    }

    for root in INTERNAL_IMPORT_ROOTS:
        for path in _python_files(root):
            if path in allowed:
                continue
            for module in _imports_for(path):
                if module == "shared.components_qt" or module.startswith("shared.components_qt."):
                    offenders.append((str(path.relative_to(ROOT)), module))

    assert offenders == []
