"""
shared/components/registry.py
==============================
Central registry of all NeuroMood UI components.

``COMPONENT_REGISTRY``  —  dict mapping class name → metadata dict.
``list_components()``   —  return sorted list of available names.
``get_component(name)`` —  import and return the class.

Usage::

    from shared.components.registry import list_components, get_component

    print(list_components())      # ['NMActivityCard', 'NMAvisoCard', ...]
    CardClass = get_component('NMCard')
"""

COMPONENT_REGISTRY: dict[str, dict] = {
    # ── Core ────────────────────────────────────────────────────────────────
    "ThemeManager": {
        "class": "ThemeManager",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Singleton that propagates theme changes to all registered components. "
            "Emits theme_changed(str) on mode switch."
        ),
    },
    # ── Cards & Surfaces ────────────────────────────────────────────────────
    "NMCard": {
        "class": "NMCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Card v3 — rounded surface with border, optional glow halo. "
            "Spec-compliant: no scale on press, borderStrong on hover."
        ),
    },
    "NMCardSecondary": {
        "class": "NMCardSecondary",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Secondary card variant with muted styling.",
    },
    "NMEmptyState": {
        "class": "NMEmptyState",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Empty state widget — icon chip + title + subtitle + optional CTAs. "
            "Handoff §2.11 compliant."
        ),
    },
    "NMSectionCard": {
        "class": "NMSectionCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Section container card with header slot.",
    },
    "NMActivityCard": {
        "class": "NMActivityCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Activity item card for the dashboard grid.",
    },
    "NMFeaturedCard": {
        "class": "NMFeaturedCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Featured / highlighted card variant.",
    },
    "NMStatCard": {
        "class": "NMStatCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Stat display card — number + label + optional delta.",
    },
    "NMErrorState": {
        "class": "NMErrorState",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Error display card with icon and retry CTA.",
    },
    "NMDataPreserveCard": {
        "class": "NMDataPreserveCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Data preservation info card for uninstall flow.",
    },
    # ── Buttons ──────────────────────────────────────────────────────────────
    "NMButton": {
        "class": "NMButton",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Button v3 — pill, gradient/secondary/ghost/danger variants, "
            "sm/md/lg sizes. Press scale 0.97, ripple on gradient."
        ),
    },
    "NMIconButton": {
        "class": "NMIconButton",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Icon button with variants (default/ghost/tint) and sizes (sm/default).",
    },
    "NMButtonOutline": {
        "class": "NMButtonOutline",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Toggleable pill button. Variant secondary when inactive, "
            "fill gradient teal→violet when active."
        ),
    },
    "NMPlayButton": {
        "class": "NMPlayButton",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Play/pause icon button for media controls.",
    },
    "NMQuickAction": {
        "class": "NMQuickAction",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Quick action button — icon + label for toolbar.",
    },
    "NMDivider": {
        "class": "NMDivider",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Horizontal rule / divider.",
    },
    "NMSectionHeader": {
        "class": "NMSectionHeader",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Section heading with optional action slot.",
    },
    # ── Inputs ───────────────────────────────────────────────────────────────
    "NMInput": {
        "class": "NMInput",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Stylized QLineEdit. Focus glow border, error state, "
            "placeholder styling. Border animates border→border_focus on focus."
        ),
    },
    "NMSearchInput": {
        "class": "NMSearchInput",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Search input with magnifier icon.",
    },
    "NMTextArea": {
        "class": "NMTextArea",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Multi-line text input widget.",
    },
    "NMSelect": {
        "class": "NMSelect",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Dropdown select widget.",
    },
    "NMFormField": {
        "class": "NMFormField",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Form field — label + input + error hint layout.",
    },
    "NMFormRow": {
        "class": "NMFormRow",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Horizontal form row — label + field pair.",
    },
    "NMToggle": {
        "class": "NMToggle",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Toggle switch widget.",
    },
    "NMCustomCheck": {
        "class": "NMCustomCheck",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Custom checkbox with animated check.",
    },
    "NMSegmentedChoice": {
        "class": "NMSegmentedChoice",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Segmented control — pill toggle group.",
    },
    # ── Navigation ───────────────────────────────────────────────────────────
    "NMSidebar": {
        "class": "NMSidebar",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Left navigation sidebar. Connects to ThemeManager. Handoff §2.4 compliant."
        ),
    },
    "NMHeader": {
        "class": "NMHeader",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Top header bar with title and action buttons.",
    },
    "NMTabs": {
        "class": "NMTabs",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Tab bar widget for panel navigation.",
    },
    "NMWindowChrome": {
        "class": "NMWindowChrome",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Custom window chrome with drag region and controls.",
    },
    "NMRow": {
        "class": "NMRow",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Generic horizontal layout row.",
    },
    # ── Feedback ────────────────────────────────────────────────────────────
    "NMToast": {
        "class": "NMToast",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Toast notification — slides in from top-right, auto-dismiss. Handoff §2.9 compliant."
        ),
    },
    "NMTooltip": {
        "class": "NMTooltip",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Tooltip overlay widget.",
    },
    "NMChip": {
        "class": "NMChip",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Small pill with optional icon. Variants: default/tint/solid/success/warning/danger/info/amber.",
    },
    "NMBadge": {
        "class": "NMBadge",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Small label badge — count or status indicator.",
    },
    "NMStatusDot": {
        "class": "NMStatusDot",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Colored status dot indicator.",
    },
    "NMStatusBanner": {
        "class": "NMStatusBanner",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Full-width status message banner.",
    },
    "NMStatusChip": {
        "class": "NMStatusChip",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Status chip — pill with icon and label.",
    },
    "NMWelcomeBar": {
        "class": "NMWelcomeBar",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Welcome banner for the dashboard.",
    },
    # ── Data / Charts ────────────────────────────────────────────────────────
    "NMSparkline": {
        "class": "NMSparkline",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Compact sparkline chart for inline trend display.",
    },
    "NMWaveChart": {
        "class": "NMWaveChart",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Wave / area chart for mood history.",
    },
    "NMProgressBar": {
        "class": "NMProgressBar",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Custom progress bar with teal→violet gradient fill and shimmer animation."
        ),
    },
    "NMProgressLine": {
        "class": "NMProgressLine",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Linear progress line widget.",
    },
    "NMFocusArc": {
        "class": "NMFocusArc",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Circular focus ring with animated arc.",
    },
    "NMHeatBar": {
        "class": "NMHeatBar",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Heat map bar — one week of activity.",
    },
    "NMCycleRing": {
        "class": "NMCycleRing",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Circular cycle indicator ring.",
    },
    "NMStreakBadge": {
        "class": "NMStreakBadge",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Streak / consecutive-day badge.",
    },
    "NMRoutineSection": {
        "class": "NMRoutineSection",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Routine section with timeline for the day.",
    },
    "NMDayNote": {
        "class": "NMDayNote",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Daily note entry widget.",
    },
    "NMModuleRing": {
        "class": "NMModuleRing",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Module completion ring indicator.",
    },
    # ── Mood ─────────────────────────────────────────────────────────────────
    "NMMoodEmoji": {
        "class": "NMMoodEmoji",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Mood emoji display with tooltip.",
    },
    "V3MoodSlider": {
        "class": "V3MoodSlider",
        "file": "components_qt.py",
        "status": "stable",
        "description": (
            "Mood slider v3 — 10-point scale with gradient track "
            "and animated thumb. Handoff §2.6 compliant."
        ),
    },
    "NMEmojiPicker": {
        "class": "NMEmojiPicker",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Emoji picker grid for mood selection.",
    },
    "NMCalmBadge": {
        "class": "NMCalmBadge",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Calm session badge.",
    },
    "NMPhaseChip": {
        "class": "NMPhaseChip",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Phase indicator chip.",
    },
    "NMTCCStepper": {
        "class": "NMTCCStepper",
        "file": "components_qt.py",
        "status": "stable",
        "description": "TCC (Terapia Cognitivo-Conductual) stepper widget.",
    },
    "NMStepper": {
        "class": "NMStepper",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Horizontal stepper with 10px dots and 2px line.",
    },
    "NMMoodContextHeader": {
        "class": "NMMoodContextHeader",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Mood context header with emoji and timestamp.",
    },
    "NMCategoryFilter": {
        "class": "NMCategoryFilter",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Category filter chips row.",
    },
    "_MoodPickWidget": {
        "class": "_MoodPickWidget",
        "file": "components_qt.py",
        "status": "legacy",
        "description": "Internal mood picker widget (private).",
    },
    "_MoodPickLabel": {
        "class": "_MoodPickLabel",
        "file": "components_qt.py",
        "status": "legacy",
        "description": "Internal mood pick label (private).",
    },
    "_MoodTrackBar": {
        "class": "_MoodTrackBar",
        "file": "components_qt.py",
        "status": "legacy",
        "description": "Internal mood track bar (private).",
    },
    # ── Session ──────────────────────────────────────────────────────────────
    "NMSessionHistory": {
        "class": "NMSessionHistory",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Session history list widget.",
    },
    "NMSkeleton": {
        "class": "NMSkeleton",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Loading skeleton placeholder widget.",
    },
    "NMFadeWidget": {
        "class": "NMFadeWidget",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Widget with fade-in animation on show.",
    },
    "NMModule": {
        "class": "NMModule",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Module card for the home screen.",
    },
    "NMSyncOrb": {
        "class": "NMSyncOrb",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Sync status orb indicator.",
    },
    "NMInstallStepper": {
        "class": "NMInstallStepper",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Install stepper for onboarding flow.",
    },
    # ── Misc / Utility ──────────────────────────────────────────────────────
    "NMIcon": {
        "class": "NMIcon",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Icon widget wrapper around nm_icon.",
    },
    "NMAvatar": {
        "class": "NMAvatar",
        "file": "components_qt.py",
        "status": "stable",
        "description": "User avatar image widget.",
    },
    "NMPresetChip": {
        "class": "NMPresetChip",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Preset selection chip.",
    },
    "NMProviderChip": {
        "class": "NMProviderChip",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Provider / professional chip.",
    },
    "NMHubSidebar": {
        "class": "NMHubSidebar",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Hub navigation sidebar variant.",
    },
    "NMAvisoCard": {
        "class": "NMAvisoCard",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Aviso / notice card widget.",
    },
    "NMPatientRow": {
        "class": "NMPatientRow",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Patient list row item.",
    },
    "NMPatientRowPremium": {
        "class": "NMPatientRowPremium",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Premium patient row variant.",
    },
    "NMPatientContext": {
        "class": "NMPatientContext",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Patient context header widget.",
    },
    "NMSettingsSection": {
        "class": "NMSettingsSection",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Settings section panel.",
    },
    "NMPanel": {
        "class": "NMPanel",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Generic panel container widget.",
    },
    "NMChatBubble": {
        "class": "NMChatBubble",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Chat message bubble widget.",
    },
    "NMTypingDots": {
        "class": "NMTypingDots",
        "file": "components_qt.py",
        "status": "stable",
        "description": "Animated typing dots indicator.",
    },
}


def list_components(status: str | None = None) -> list[str]:
    """Return sorted list of available component names.

    Args:
        status: Filter by ``"stable"`` or ``"legacy"``.  Pass ``None``
                (default) to include all.

    Returns:
        Sorted list of component class names.
    """
    if status is None:
        return sorted(COMPONENT_REGISTRY.keys())
    return sorted(name for name, meta in COMPONENT_REGISTRY.items() if meta.get("status") == status)


def get_component(name: str) -> type:
    """Import and return the component class by name.

    Args:
        name: Class name, e.g. ``"NMCard"``.

    Returns:
        The class object.

    Raises:
        ImportError: If the name is not in the registry or cannot be imported.
        AttributeError: If the class does not exist in ``components_qt``.
    """
    if name not in COMPONENT_REGISTRY:
        raise ImportError(
            f"'{name}' is not in the component registry. "
            f"Available: {sorted(COMPONENT_REGISTRY.keys())}"
        )

    # Import from components_qt at runtime
    from shared import components_qt

    cls = getattr(components_qt, name, None)
    if cls is None:
        raise AttributeError(f"'{name}' is in registry but not found in components_qt")
    return cls
