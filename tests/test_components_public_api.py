"""Public component API contract based on real Suite/Hub/QA/build consumers."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSUMER_ROOTS = (ROOT / "app", ROOT / "hub", ROOT / "qa", ROOT / "build_neuromood.py")
COMPONENT_MODULES = {"shared.components", "shared.components_qt"}
MOVED_COMPONENT_MODULES = {
    "NMIcon": "shared.components.icons",
    "NMSectionHeader": "shared.components.icons",
    "NMAvatar": "shared.components.icons",
    "NMBadge": "shared.components.surfaces",
    "NMButton": "shared.components.buttons",
    "NMButtonOutline": "shared.components.buttons",
    "NMCard": "shared.components.cards",
    "NMChartPanel": "shared.components.cards",
    "NMChip": "shared.components.surfaces",
    "NMCustomCheck": "shared.components.session",
    "NMDialogScaffold": "shared.components.dialogs",
    "NMElidedLabel": "shared.components.data",
    "NMEmptyState": "shared.components.overlays",
    "NMFadeWidget": "shared.components.core",
    "NMFocusArc": "shared.components.rings",
    "NMHeatBar": "shared.components.feedback",
    "NMInput": "shared.components.buttons",
    "NMModule": "shared.components.navigation",
    "NMModuleRing": "shared.components.rings",
    "NMPageHeader": "shared.components.surfaces",
    "NMPatientRowPremium": "shared.components.patient",
    "NMPlayButton": "shared.components.inputs",
    "NMProgressBar": "shared.components.feedback",
    "NMRingPulse": "shared.components.feedback",
    "NMSearchInput": "shared.components.buttons",
    "NMSegmentedChoice": "shared.components.buttons",
    "NMStepper": "shared.components.feedback",
    "NMTabs": "shared.components.buttons",
    "NMTextArea": "shared.components.buttons",
    "NMToast": "shared.components.feedback",
    "NMWaveChart": "shared.components.feedback",
    "NMWindowChrome": "shared.components.chrome",
    "ThemeManager": "shared.theme_manager",
    "V3MoodSlider": "shared.components.mood",
    "nm_confirm": "shared.components.dialogs",
}

EXPECTED_PUBLIC_COMPONENT_SYMBOLS = {
    "NMAvatar",
    "NMBadge",
    "NMButton",
    "NMButtonOutline",
    "NMCard",
    "NMChartPanel",
    "NMChip",
    "NMCustomCheck",
    "NMDialogScaffold",
    "NMElidedLabel",
    "NMEmptyState",
    "NMFadeWidget",
    "NMFocusArc",
    "NMHeatBar",
    "NMIcon",
    "NMInput",
    "NMModule",
    "NMModuleRing",
    "NMPageHeader",
    "NMPatientRowPremium",
    "NMPlayButton",
    "NMProgressBar",
    "NMRingPulse",
    "NMSearchInput",
    "NMSectionHeader",
    "NMSegmentedChoice",
    "NMStepper",
    "NMTabs",
    "NMTextArea",
    "NMToast",
    "NMWaveChart",
    "NMWindowChrome",
    "ThemeManager",
    "V3MoodSlider",
    "nm_confirm",
}


def _consumer_files() -> list[Path]:
    files: list[Path] = []
    for root in CONSUMER_ROOTS:
        if root.is_file():
            files.append(root)
        else:
            files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(files)


def _component_imports_used_by_consumers() -> set[str]:
    used: set[str] = set()
    for path in _consumer_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in COMPONENT_MODULES:
                used.update(alias.name for alias in node.names)
    return used


def test_public_component_contract_matches_real_consumers():
    assert not any(name.startswith("_") for name in EXPECTED_PUBLIC_COMPONENT_SYMBOLS)
    assert _component_imports_used_by_consumers() == EXPECTED_PUBLIC_COMPONENT_SYMBOLS


def test_public_component_symbols_are_reexported_from_both_paths():
    components = importlib.import_module("shared.components")
    facade = importlib.import_module("shared.components_qt")

    assert len(EXPECTED_PUBLIC_COMPONENT_SYMBOLS) == 35
    assert set(facade.__all__) == EXPECTED_PUBLIC_COMPONENT_SYMBOLS
    assert set(components.__all__) == EXPECTED_PUBLIC_COMPONENT_SYMBOLS
    assert EXPECTED_PUBLIC_COMPONENT_SYMBOLS <= set(components.__all__)
    for name in EXPECTED_PUBLIC_COMPONENT_SYMBOLS:
        assert getattr(components, name) is getattr(facade, name)


def test_theme_manager_reexports_keep_singleton_identity():
    components = importlib.import_module("shared.components")
    facade = importlib.import_module("shared.components_qt")
    theme_manager = importlib.import_module("shared.theme_manager")

    assert facade.ThemeManager is theme_manager.ThemeManager
    assert components.ThemeManager is theme_manager.ThemeManager
    assert facade.ThemeManager.instance() is theme_manager.ThemeManager.instance()


def test_theme_manager_has_no_component_or_qt_adapter_dependencies():
    path = ROOT / "shared" / "theme_manager.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = {"shared.theme_qt", "shared.components", "shared.components_qt"}
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    assert not (imported_modules & forbidden)


def test_layout_module_does_not_import_component_facades_or_theme_adapters():
    path = ROOT / "shared" / "components" / "layout.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = {
        "shared.components",
        "shared.components_qt",
        "shared.theme_qt",
        "shared.theme_manager",
    }
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    assert not (imported_modules & forbidden)


def test_elided_label_leaf_export_keeps_identity_from_all_paths():
    components = importlib.import_module("shared.components")
    facade = importlib.import_module("shared.components_qt")
    data = importlib.import_module("shared.components.data")

    assert facade.NMElidedLabel is data.NMElidedLabel
    assert components.NMElidedLabel is data.NMElidedLabel
    assert components.NMElidedLabel is facade.NMElidedLabel


def test_moved_component_exports_keep_identity_from_all_paths():
    components = importlib.import_module("shared.components")
    facade = importlib.import_module("shared.components_qt")

    assert set(MOVED_COMPONENT_MODULES) == EXPECTED_PUBLIC_COMPONENT_SYMBOLS
    for name, module_name in MOVED_COMPONENT_MODULES.items():
        module = importlib.import_module(module_name)
        assert getattr(facade, name) is getattr(module, name)
        assert getattr(components, name) is getattr(module, name)
        assert getattr(components, name) is getattr(facade, name)
