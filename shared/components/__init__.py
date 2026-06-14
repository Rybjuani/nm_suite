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
    "NMCalmBadge": "shared.components.status",
    "NMPhaseChip": "shared.components.status",
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
    "NMDivider": "shared.components.surfaces",
    "NMHeatBar": "shared.components.feedback",
    "NMProgressBar": "shared.components.feedback",
    "NMProgressLine": "shared.components.feedback",
    "NMRingPulse": "shared.components.feedback",
    "NMSkeleton": "shared.components.feedback",
    "NMStepper": "shared.components.feedback",
    "NMToast": "shared.components.feedback",
    "NMTypingDots": "shared.components.feedback",
    "NMWaveChart": "shared.components.feedback",
    "NMToggle": "shared.components.inputs",
    "NMPlayButton": "shared.components.inputs",
    "NMIcon": "shared.components.icons",
    "NMSectionHeader": "shared.components.icons",
    "NMAvatar": "shared.components.icons",
    "NMBadge": "shared.components.surfaces",
    "NMChip": "shared.components.surfaces",
    "NMFormRow": "shared.components.surfaces",
    "NMListRow": "shared.components.surfaces",
    "NMPageHeader": "shared.components.surfaces",
    "NMPanel": "shared.components.surfaces",
    "NMSettingsSection": "shared.components.surfaces",
    "NMSyncOrb": "shared.components.surfaces",
    "NMFocusArc": "shared.components.rings",
    "NMCycleRing": "shared.components.rings",
    "NMModuleRing": "shared.components.rings",
    "NMCard": "shared.components.cards",
    "NMChartPanel": "shared.components.cards",
    "NMFormPanel": "shared.components.cards",
    "NMMetricCard": "shared.components.cards",
    "V3MoodSlider": "shared.components.mood",
    "NMPatientRowPremium": "shared.components.patient",
    "NMModule": "shared.components.navigation",
    "NMWindowChrome": "shared.components.chrome",
    "NMDialogScaffold": "shared.components.dialogs",
    "nm_confirm": "shared.components.dialogs",
    "NMHubSidebar": "shared.components.surfaces",
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
