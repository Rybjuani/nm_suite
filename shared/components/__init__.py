"""Public import point for NeuroMood PyQt6 UI components."""

from __future__ import annotations

from importlib import import_module

__all__ = [
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
    "NMFormPanel",
    "NMHeatBar",
    "NMIcon",
    "NMInput",
    "NMModule",
    "NMModuleRing",
    "NMPageHeader",
    "NMPatientRowPremium",
    "NMPlayButton",
    "NMProgressBar",
    "NMProgressLine",
    "NMRingPulse",
    "NMSearchInput",
    "NMSectionHeader",
    "NMSegmentedChoice",
    "NMSkeleton",
    "NMStepper",
    "NMTabs",
    "NMTextArea",
    "NMToast",
    "NMToggle",
    "NMWaveChart",
    "NMWindowChrome",
    "ThemeManager",
    "V3MoodSlider",
    "nm_confirm",
]

_LAYOUT_EXPORTS = set()
_LEAF_EXPORT_MODULES = {
    "NMEmptyState": "shared.components.overlays",
    "NMCustomCheck": "shared.components.session",
    "NMButton": "shared.components.buttons",
    "NMButtonOutline": "shared.components.buttons",
    "NMInput": "shared.components.buttons",
    "NMSearchInput": "shared.components.buttons",
    "NMSegmentedChoice": "shared.components.buttons",
    "NMTabs": "shared.components.buttons",
    "NMTextArea": "shared.components.buttons",
    "NMFadeWidget": "shared.components.core",
    "NMElidedLabel": "shared.components.data",
    "NMHeatBar": "shared.components.feedback",
    "NMProgressBar": "shared.components.feedback",
    "NMProgressLine": "shared.components.feedback",
    "NMRingPulse": "shared.components.feedback",
    "NMSkeleton": "shared.components.feedback",
    "NMStepper": "shared.components.feedback",
    "NMToast": "shared.components.feedback",
    "NMWaveChart": "shared.components.feedback",
    "NMToggle": "shared.components.inputs",
    "NMPlayButton": "shared.components.inputs",
    "NMIcon": "shared.components.icons",
    "NMSectionHeader": "shared.components.icons",
    "NMAvatar": "shared.components.icons",
    "NMBadge": "shared.components.surfaces",
    "NMChip": "shared.components.surfaces",
    "NMPageHeader": "shared.components.surfaces",
    "NMFocusArc": "shared.components.rings",
    "NMModuleRing": "shared.components.rings",
    "NMCard": "shared.components.cards",
    "NMChartPanel": "shared.components.cards",
    "NMFormPanel": "shared.components.cards",
    "V3MoodSlider": "shared.components.mood",
    "NMPatientRowPremium": "shared.components.patient",
    "NMModule": "shared.components.navigation",
    "NMWindowChrome": "shared.components.chrome",
    "NMDialogScaffold": "shared.components.dialogs",
    "nm_confirm": "shared.components.dialogs",
    "ThemeManager": "shared.theme_manager",
}


def __getattr__(name: str):
    if name in _LAYOUT_EXPORTS:
        return globals()[name]
    if name in _LEAF_EXPORT_MODULES:
        module = import_module(_LEAF_EXPORT_MODULES[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'shared.components' has no attribute {name!r}")
