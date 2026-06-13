"""Public component API contract based on real Suite/Hub/QA/build consumers."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSUMER_ROOTS = (ROOT / "app", ROOT / "hub", ROOT / "qa", ROOT / "build_neuromood.py")
COMPONENT_MODULES = {"shared.components", "shared.components_qt"}

EXPECTED_PUBLIC_COMPONENT_SYMBOLS = {
    "NMAIDisclaimer",
    "NMAvatar",
    "NMBadge",
    "NMButton",
    "NMButtonOutline",
    "NMCalmBadge",
    "NMCard",
    "NMChartPanel",
    "NMChip",
    "NMCustomCheck",
    "NMCycleRing",
    "NMDayNote",
    "NMDialogScaffold",
    "NMDivider",
    "NMElidedLabel",
    "NMEmptyState",
    "NMFadeWidget",
    "NMFeaturedCard",
    "NMFocusArc",
    "NMFormPanel",
    "NMFormRow",
    "NMHeatBar",
    "NMHubSidebar",
    "NMIcon",
    "NMInput",
    "NMListRow",
    "NMMetricCard",
    "NMModule",
    "NMModuleRing",
    "NMPageHeader",
    "NMPanel",
    "NMPatientRowPremium",
    "NMPhaseChip",
    "NMPlayButton",
    "NMProgressBar",
    "NMProgressLine",
    "NMRingPulse",
    "NMSearchInput",
    "NMSectionHeader",
    "NMSegmentedChoice",
    "NMSettingsSection",
    "NMSkeleton",
    "NMStepper",
    "NMSyncOrb",
    "NMTabs",
    "NMTextArea",
    "NMToast",
    "NMToggle",
    "NMTypingDots",
    "NMWaveChart",
    "NMWindowChrome",
    "ThemeManager",
    "V3MoodSlider",
    "h_spacer",
    "nm_confirm",
    "responsive_columns",
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

    assert len(EXPECTED_PUBLIC_COMPONENT_SYMBOLS) == 56
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


def test_layout_helpers_are_leaf_exports_with_compatible_identity():
    components = importlib.import_module("shared.components")
    facade = importlib.import_module("shared.components_qt")
    layout = importlib.import_module("shared.components.layout")

    assert facade.h_spacer is layout.h_spacer
    assert components.h_spacer is layout.h_spacer
    assert facade.responsive_columns is layout.responsive_columns
    assert components.responsive_columns is layout.responsive_columns
    assert facade.responsive_breakpoint is layout.responsive_breakpoint


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


def test_data_module_does_not_import_component_facades_theme_or_upper_layers():
    path = ROOT / "shared" / "components" / "data.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden_prefixes = (
        "app",
        "hub",
        "qa",
        "shared.components",
        "shared.components_qt",
        "shared.theme",
        "shared.theme_manager",
        "shared.theme_qt",
    )
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    assert not any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported_modules
        for prefix in forbidden_prefixes
    )
