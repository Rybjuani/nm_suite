"""
shared/components_qt.py
Biblioteca de componentes UI PyQt6 para NeuroMood V3.

Cada componente implementa apply_theme(modo) y se conecta
automáticamente al singleton ThemeManager al instanciarse.

NO importa CustomTkinter. Compatible con contexto frozen.
"""

import sys
import os

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QPoint,
    QRectF,
    QPointF,
    QSize,
    pyqtSignal,
    pyqtProperty,
    QObject,
    QRect,
    QSequentialAnimationGroup,
    QAbstractAnimation,
    QVariantAnimation,
)
from PyQt6 import sip
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPalette,
    QLinearGradient,
    QRadialGradient,
    QPainterPath,
    QFontMetrics,
    QPixmap,
    QPaintEvent,
    QMouseEvent,
    QResizeEvent,
    QEnterEvent,
    QIcon,
    QPolygonF,
    QImage,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QPushButton,
    QLineEdit,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QAbstractButton,
    QToolButton,
    QSizePolicy,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
    QApplication,
    QScrollArea,
    QTextEdit,
    QLayout,
    QSlider,
    QButtonGroup,
)

from shared.components.buttons import (
    NMButton,
    NMButtonOutline,
    NMInput,
    NMSearchInput,
    NMSegmentedChoice,
    NMTabs,
    NMTextArea,
    _NM_BUTTON_FONT,
    _NM_BUTTON_HEIGHT,
    _NM_CONTROL_COMPACT_HEIGHT,
    _NM_CONTROL_FONT,
    _NM_CONTROL_HEIGHT,
    _NM_CONTROL_PILL_RADIUS,
    _NM_CONTROL_RADIUS,
    _NM_CONTROL_WEIGHT,
    _NM_TAB_FONT,
    _NM_TAB_HEIGHT,
    _NM_TAB_RADIUS,
)
from shared.components.overlays import NMEmptyState, NMTooltip, NMErrorState
from shared.components.status import (
    NMStatusChip,
    NMStatusDot,
    NMStatusBanner,
    NMPhaseChip,
    NMCalmBadge,
    _STATUS_DOT_TONE_TO_KEY,
)
from shared.components.session import (
    _NMAnimCheckBox,
    NMCategoryFilter,
    NMCustomCheck,
    NMActivityCard,
    NMDayNote,
    NMFormField,
    NMMoodContextHeader,
    NMPresetChip,
    NMRoutineSection,
    NMSessionHistory,
    NMStreakBadge,
    NMTCCStepper,
    NMWelcomeBar,
    _rgba,
)
from shared.components.core import NMFadeWidget
from shared.components.layout import h_spacer, responsive_breakpoint, responsive_columns
from shared.components.data import NMElidedLabel
from shared.components.feedback import (
    NMHeatBar,
    NMProgressBar,
    NMProgressLine,
    NMRingPulse,
    NMSkeleton,
    NMStepper,
    NMToast,
    NMTypingDots,
    NMWaveChart,
)
from shared.components.icons import NMAvatar, NMIcon, NMSectionHeader
from shared.components.inputs import NMPlayButton, NMToggle
from shared.components.rings import NMCycleRing, NMFocusArc, NMModuleRing
from shared.components.surfaces import (
    NMBadge,
    NMChip,
    NMDivider,
    NMFormRow,
    NMListRow,
    NMPageHeader,
    NMPanel,
    NMRow,
    NMSettingsSection,
    NMSyncOrb,
)
from shared.theme_manager import ThemeManager
from shared.components.onboarding import NMDataPreserveCard, NMInstallStepper
from shared.components.cards import (
    NMAvisoCard,
    NMCard,
    NMCardSecondary,
    NMChartPanel,
    NMFormPanel,
    NMMetricCard,
    NMSectionCard,
    NMStatCard,
)

try:
    from shared.theme_qt import (
        # Compatibility (intacto)
        qcolor,
        qfont,
        qfont_mono,
        linear_gradient,
        rich_gradient,
        linear_gradient_vertical,
        radial_glow,
        noise_overlay,
        gradient_colors,
        conical_arc_gradient,
        ring_color,
        aura_opacity,
        blob_opacity,
        C,
        colors,
        norm_modo,
        interpolate_color,
        blend_color,
        label_style,
        SessionColor,
        nm_icon,
        nm_font,
        sp,
        fx,
        focus_ring_stylesheet,
        ThemeAwareWidgetMixin,
        ANIM,
        EASE_OUT,
        RADIUS_CARD,
        RADIUS_BUTTON,
        RADIUS_INPUT,
        RADIUS_PILL,
        RADIUS_SMALL,
        CHECKBOX_SIZE,
        qcolor_to_rgba_css,
        qcolor_hex,
        shadow_effect,
        PAD_CONTAINER,
        PAD_CARD,
        GAP_CARDS,
        GAP_ELEMENTS,
        HEADER_H,
        FONT_MONO,
        SIZE_TIME_LARGE,
        SIZE_TIME_TIMER,
        RING_GOOD_THRESHOLD,
        RING_MID_THRESHOLD,
        stylesheet_lineedit,
        aplicar_captionbar_qt,
        obtener_ruta_recurso,
        recolorear_logo_light,
        obtener_icono_solido,
        # v3 (nuevos helpers para los sub-pasos 2-8)
        v3c,
        parse_rgba,
        v3_shadow,
        v3_linear_gradient,
        v3_conical_signature,
        v3_font,
        mood_qcolor,
        mood_gradient,
        V3_SP,
        V3_RD,
        pill_radius,
        eyebrow_font,
    )
    from shared.theme import (
        TYPOGRAPHY,
        LAYOUT,
        CATEGORY_COLORS,
        get_gradient,
        # v3
        V3_LIGHT,
        V3_DARK,
        V3_SPACE,
        V3_RADIUS,
        V3_SHADOWS,
        V3_GRADIENTS,
        MOOD_PALETTE,
        get_v3_palette,
        get_mood,
        v3_mode,
        icon_stroke_width,
    )
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme_qt import (
        qfont,
        qfont_mono,
        radial_glow,
        blob_opacity,
        C,
        colors,
        norm_modo,
        interpolate_color,
        blend_color,
        label_style,
        SessionColor,
        nm_icon,
        sp,
        focus_ring_stylesheet,
        ThemeAwareWidgetMixin,
        ANIM,
        EASE_OUT,
        RADIUS_CARD,
        RADIUS_BUTTON,
        RADIUS_INPUT,
        RADIUS_PILL,
        RADIUS_SMALL,
        qcolor_to_rgba_css,
        PAD_CARD,
        HEADER_H,
        SIZE_TIME_LARGE,
        obtener_ruta_recurso,
        recolorear_logo_light,
        v3c,
        v3_shadow,
        v3_linear_gradient,
        v3_font,
        V3_SP,
        V3_RD,
        pill_radius,
        eyebrow_font,
    )
    from theme import (
        TYPOGRAPHY,
        LAYOUT,
        CATEGORY_COLORS,
        V3_LIGHT,
        V3_DARK,
        V3_SHADOWS,
        V3_GRADIENTS,
        get_mood,
        v3_mode,
    )


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()




# ── NMIconButton ──────────────────────────────────────────────────────────────


# ── Navigation components (moved to shared.components.navigation) ──────────────
from shared.components.navigation import (
    NMIconButton,
    _SidebarItem,
    NMSidebar,
    _LogoLabel,
    NMHeader,
    NMModule,
    _ChromeLogoMark,
)
from shared.components.mood import (
    NMMoodEmoji,
    NMEmojiPicker,
    NMMoodSlider,
    _MoodPickWidget,
    _MoodPickLabel,
    _MoodNumRow,
    _MoodTrackBar,
    V3MoodSlider,
)
# ── Patient components (moved to shared.components.patient) ───────────────────
from shared.components.patient import (
    _PATIENT_AVATAR_PAIRS,
    NMPatientRow,
    NMSparkline,
    NMAreaSparkline,
    NMPatientRowPremium,
)
_PATIENT_AVATAR_PAIRS = _PATIENT_AVATAR_PAIRS  # re-export for any direct access

# ── AI/chat components (moved to shared.components.session) ────────────────────
from shared.components.session import (
    NMAIDisclaimer,
    NMAIPanel,
    NMChatBubble,
    NMProviderChip,
    NMQuickAction,
    NMPatientContext,
)
from shared.components.surfaces import (
    _GradientTextLabel,
    NMHubSidebar,
)


from shared.components.layout import FlowLayout

from shared.components.cards import NMFeaturedCard







# ══════════════════════════════════════════════════════════════════════════════
# Componentes v3 — Redesign 2026 (Sage Linen / Indigo Mist)
# ══════════════════════════════════════════════════════════════════════════════
# Estos wrappers cubren huecos del design system identificados en la auditoría:
# NMDivider, NMSectionHeader, NMAvatar, NMStatCard, NMSearchInput, NMTextArea,
# NMTabs, NMTooltip, NMErrorState, NMDialog/NMModal.
#
# Todos siguen el patrón runtime: aceptan `modo`, registran un slot al
# ThemeManager via _tm().theme_changed, y exponen `_apply_theme(modo)`.
# ══════════════════════════════════════════════════════════════════════════════







# ── Dialog components (moved to shared.components.dialogs) ────────────────────
from shared.components.dialogs import (
    NMDialog,
    NMModal,
    nm_confirm,
    NMDialogScaffold,
)

# ════════════════════════════════════════════════════════════════════════════
# Runtime spec Full UI Pass — Mayo 2026
# Extensiones MÍNIMAS al catálogo para alinear con
# design_runtime spec_nm_suite_full_ui/. Sólo se incluyen los componentes que el
# plan declara imprescindibles para the runtime migration y que no existían como tales.
# El resto (NMRing, NMSparkline, NMMoodBars, NMModal, NMToast, NMTabs,
# NMAvatar, NMSwitch, NMProgress) ya está en el catálogo arriba y se reusan
# desde las pantallas — se repintan automáticamente al cambiar la paleta V3.
# ════════════════════════════════════════════════════════════════════════════




# ── NMSelect ─────────────────────────────────────────────────────────────────
# Runtime spec §4.3: QComboBox themed (surface-2 bg, border line, radius 14,
# focus = primary). El catálogo previo no exponía un select consistente.

try:
    from PyQt6.QtWidgets import QComboBox as _QComboBox

    class NMSelect(_QComboBox):
        """QComboBox themed según runtime spec §4.3.

        Lee tokens del tema vía ``stylesheet_combobox`` (theme_qt). Se conecta
        al ThemeManager para repintar al conmutar light/dark.
        """

        def __init__(self, parent=None, modo: str | None = None):
            super().__init__(parent)
            self._modo = norm_modo(modo or _tm().modo)
            self.setMinimumHeight(36)
            self.setFont(qfont("size_body"))
            self._apply_theme(self._modo)
            _tm().theme_changed.connect(self._apply_theme)

        def _apply_theme(self, modo: str):
            self._modo = norm_modo(modo)
            try:
                from shared.theme_qt import stylesheet_combobox
            except ImportError:
                from theme_qt import stylesheet_combobox  # type: ignore
            self.setStyleSheet(stylesheet_combobox(self._modo))
except ImportError:
    # PyQt6 sin QComboBox (no debería pasar) — degradar a alias seguro.
    NMSelect = QLineEdit  # type: ignore


# ── Chrome components (moved to shared.components.chrome) ────────────────────
from shared.components.chrome import (
    _ChromeWinBtn,
    NMWindowChrome,
)










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
