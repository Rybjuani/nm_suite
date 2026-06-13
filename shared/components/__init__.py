"""Public import point for NeuroMood PyQt6 UI components."""

from __future__ import annotations

from importlib import import_module

from shared.components.layout import h_spacer, responsive_columns

__all__ = [
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
]

_LAYOUT_EXPORTS = {"h_spacer", "responsive_columns"}
_LEAF_EXPORT_MODULES = {
    "NMElidedLabel": "shared.components.data",
    "NMSkeleton": "shared.components.feedback",
    "NMToast": "shared.components.feedback",
    "NMToggle": "shared.components.inputs",
}


def __getattr__(name: str):
    if name in _LAYOUT_EXPORTS:
        return globals()[name]
    if name in _LEAF_EXPORT_MODULES:
        module = import_module(_LEAF_EXPORT_MODULES[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in __all__:
        from shared import components_qt

        value = getattr(components_qt, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'shared.components' has no attribute {name!r}")
