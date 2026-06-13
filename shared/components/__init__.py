"""
shared/components/__init__.py
=============================
Import point for NeuroMood PyQt6 UI components.

Re-exports all public components from ``shared.components_qt`` for
backwards compatibility.  Code can import from this package::

    from shared.components import NMCard, NMButton, NMInput

The direct runtime module remains available::

    from shared.components_qt import NMCard, NMButton

"""

from shared.components_qt import (
    # ── Core ──────────────────────────────────────────────────────────────
    ThemeManager,
    # ── Cards & Surfaces ──────────────────────────────────────────────────
    NMCard,
    NMCardSecondary,
    NMEmptyState,
    NMSectionCard,
    NMActivityCard,
    NMFeaturedCard,
    NMStatCard,
    NMErrorState,
    NMRingPulse,
    NMDataPreserveCard,
    # ── Buttons ────────────────────────────────────────────────────────────
    NMButton,
    NMIconButton,
    NMButtonOutline,
    NMPlayButton,
    NMQuickAction,
    NMDivider,
    NMSectionHeader,
    # ── Inputs ─────────────────────────────────────────────────────────────
    NMInput,
    NMSearchInput,
    NMTextArea,
    NMSelect,
    NMFormField,
    NMFormRow,
    NMToggle,
    NMCustomCheck,
    NMSegmentedChoice,
    # ── Navigation ─────────────────────────────────────────────────────────
    NMSidebar,
    NMHeader,
    NMTabs,
    NMWindowChrome,
    NMRow,
    # ── Feedback ───────────────────────────────────────────────────────────
    NMToast,
    NMTooltip,
    NMChip,
    NMBadge,
    NMStatusDot,
    NMStatusBanner,
    NMStatusChip,
    NMWelcomeBar,
    # ── Data / Charts ──────────────────────────────────────────────────────
    NMSparkline,
    NMWaveChart,
    NMProgressBar,
    NMProgressLine,
    NMFocusArc,
    NMHeatBar,
    NMCycleRing,
    NMStreakBadge,
    NMRoutineSection,
    NMDayNote,
    NMModuleRing,
    # ── Mood ───────────────────────────────────────────────────────────────
    NMMoodEmoji,
    V3MoodSlider,
    NMEmojiPicker,
    NMCalmBadge,
    NMPhaseChip,
    NMTCCStepper,
    NMStepper,
    NMMoodContextHeader,
    NMCategoryFilter,
    _MoodPickWidget,
    _MoodPickLabel,
    _MoodTrackBar,
    # ── Session ────────────────────────────────────────────────────────────
    NMSessionHistory,
    NMSkeleton,
    NMFadeWidget,
    NMModule,
    NMSyncOrb,
    NMInstallStepper,
    # ── Misc / Utility ─────────────────────────────────────────────────────
    NMIcon,
    NMAvatar,
    NMPresetChip,
    NMProviderChip,
    NMHubSidebar,
    NMAvisoCard,
    NMPatientRow,
    NMPatientRowPremium,
    NMPatientContext,
    NMSettingsSection,
    NMPanel,
    NMChatBubble,
    NMTypingDots,
)

__all__ = [
    # Core
    "ThemeManager",
    # Cards & Surfaces
    "NMCard",
    "NMCardSecondary",
    "NMEmptyState",
    "NMSectionCard",
    "NMActivityCard",
    "NMFeaturedCard",
    "NMStatCard",
    "NMErrorState",
    "NMRingPulse",
    "NMDataPreserveCard",
    # Buttons
    "NMButton",
    "NMIconButton",
    "NMButtonOutline",
    "NMPlayButton",
    "NMQuickAction",
    "NMDivider",
    "NMSectionHeader",
    # Inputs
    "NMInput",
    "NMSearchInput",
    "NMTextArea",
    "NMSelect",
    "NMFormField",
    "NMFormRow",
    "NMToggle",
    "NMCustomCheck",
    "NMSegmentedChoice",
    # Navigation
    "NMSidebar",
    "NMHeader",
    "NMTabs",
    "NMWindowChrome",
    "NMRow",
    # Feedback
    "NMToast",
    "NMTooltip",
    "NMChip",
    "NMBadge",
    "NMStatusDot",
    "NMStatusBanner",
    "NMStatusChip",
    "NMWelcomeBar",
    # Data / Charts
    "NMSparkline",
    "NMWaveChart",
    "NMProgressBar",
    "NMProgressLine",
    "NMFocusArc",
    "NMHeatBar",
    "NMCycleRing",
    "NMStreakBadge",
    "NMRoutineSection",
    "NMDayNote",
    "NMModuleRing",
    # Mood
    "NMMoodEmoji",
    "V3MoodSlider",
    "NMEmojiPicker",
    "NMCalmBadge",
    "NMPhaseChip",
    "NMTCCStepper",
    "NMStepper",
    "NMMoodContextHeader",
    "NMCategoryFilter",
    "_MoodPickWidget",
    "_MoodPickLabel",
    "_MoodTrackBar",
    # Session
    "NMSessionHistory",
    "NMSkeleton",
    "NMFadeWidget",
    "NMModule",
    "NMSyncOrb",
    "NMInstallStepper",
    # Misc / Utility
    "NMIcon",
    "NMAvatar",
    "NMPresetChip",
    "NMProviderChip",
    "NMHubSidebar",
    "NMAvisoCard",
    "NMPatientRow",
    "NMPatientRowPremium",
    "NMPatientContext",
    "NMSettingsSection",
    "NMPanel",
    "NMChatBubble",
    "NMTypingDots",
]
