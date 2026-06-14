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


class NMAIDisclaimer(QFrame):
    """Disclaimer clínico permanente para todo output de IA (HANDOFF §6).

    Caja warning/amber con icono de escudo + texto fijo. Siempre visible: la IA
    solo genera borradores que requieren validación profesional y no constituyen
    diagnóstico. Componente reutilizable (panel IA del detalle, asistente global).
    """

    _TEXT = (
        "Borrador generado por IA · requiere validación de un profesional. "
        "No constituye diagnóstico."
    )

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMAIDisclaimer")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["sm"], V3_SP["xs"], V3_SP["sm"], V3_SP["xs"])
        lay.setSpacing(V3_SP["sm"])

        self._icon = QLabel()
        self._icon.setFixedSize(16, 16)
        self._icon.setScaledContents(True)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignTop)

        self._lbl = QLabel(self._TEXT)
        self._lbl.setWordWrap(True)
        self._lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._lbl, stretch=1)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg_color = C("warning_bg", self._modo)
        warning_color = v3c("warning", self._modo)
        warning_color.setAlpha(130 if "dark" in self._modo else 110)
        border_color = qcolor_to_rgba_css(warning_color)
        icon_color = v3c("warning", self._modo).name()
        ink_color = C("warning_ink", self._modo)
        self.setStyleSheet(
            f"QFrame#NMAIDisclaimer {{ "
            f"background-color: {bg_color}; "
            f"border: 1px solid {border_color}; "
            f"border-radius: {V3_RD['lg']}px; }}"
        )
        try:
            self._icon.setPixmap(nm_icon("shield", icon_color, size=16).pixmap(16, 16))
        except Exception:
            self._icon.setText("!")
            self._icon.setStyleSheet(f"color: {icon_color}; background: transparent;")
        self._lbl.setStyleSheet(f"color: {ink_color}; background: transparent;")


class NMAIPanel(QFrame):
    """Panel IA (F1.5) con disclaimer obligatorio en todos los estados (idle/generando/borrador).
    Background warning-bg, Border 1px primary-line (primary).
    """

    def __init__(self, state="idle", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._state = state
        self.setObjectName("NMAIPanel")

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        # Disclaimer - siempre visible
        self._disclaimer = NMAIDisclaimer(modo=self._modo, parent=self)
        lay.addWidget(self._disclaimer)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_state(self, state: str):
        self._state = state
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg_color = C("warning_bg", self._modo)
        primary_color = C("primary", self._modo)
        self.setStyleSheet(
            f"QFrame#NMAIPanel {{ "
            f"background-color: {bg_color}; "
            f"border: 1px solid {primary_color}; "
            f"border-radius: {V3_RD['xl']}px; }}"
        )
# ── Surfaces: _GradientTextLabel, NMHubSidebar (moved to shared.components.surfaces) ──
from shared.components.surfaces import (
    _GradientTextLabel,
    NMHubSidebar,
)


from shared.components.layout import FlowLayout

from shared.components.cards import NMFeaturedCard


class NMChatBubble(QWidget):
    """Burbuja de chat v3 (Hub IA).

      - ``side="left"``  → IA       (surface + borderSoft, texto principal).
      - ``side="right"`` → usuario  (gradient firma teal→violet, texto on-accent).

    Soporta ``typing=True``: muestra ``...`` que se actualiza cíclicamente cada
    400ms (placeholder ligero; para una animación con `NMTypingDots` pleno,
    instanciar éste como hijo).
    """

    def __init__(
        self,
        text: str = "",
        side: str = "left",
        modo: str = None,
        typing: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._side = side
        self._typing = bool(typing)
        self._typing_dots_state = 1
        self._original_text = text
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(0)

        if side == "right":
            outer.addStretch()

        self._bubble = QLabel(text)
        self._bubble.setFont(qfont("size_body"))
        self._bubble.setWordWrap(True)
        self._bubble.setMaximumWidth(480)
        # H-08: ensure minimum height for 2-3 lines of text
        self._bubble.setMinimumHeight(52)
        self._bubble.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        self._bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(self._bubble)

        if side == "left":
            outer.addStretch()

        # Timer interno para typing dots
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(400)
        self._typing_timer.timeout.connect(self._tick_typing)
        if self._typing:
            self._typing_timer.start()
            self._refresh_typing_text()

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_text(self, text: str):
        self._original_text = text
        self._typing = False
        if self._typing_timer.isActive():
            self._typing_timer.stop()
        self._bubble.setText(text)

    def set_typing(self, typing: bool):
        """Activa/desactiva el indicador de 'IA escribiendo' (3 dots cíclicos)."""
        self._typing = bool(typing)
        if self._typing:
            self._typing_timer.start()
            self._refresh_typing_text()
        else:
            self._typing_timer.stop()
            self._bubble.setText(self._original_text)

    def _tick_typing(self):
        self._typing_dots_state = (self._typing_dots_state % 3) + 1
        self._refresh_typing_text()

    def _refresh_typing_text(self):
        self._bubble.setText("●" * self._typing_dots_state + "○" * (3 - self._typing_dots_state))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        r = V3_RD["lg"]  # radius 14
        pad = f"padding: {V3_SP['sm']}px {V3_SP['md']}px;"
        fsize = f"font-size: {TYPOGRAPHY['size_body']}px;"
        if self._side == "left":
            # IA — superficie clara con borderSoft, cola en top-left
            surf_key = "surfaceSolid" if is_dark else "surface"
            bg = v3c(surf_key, self._modo).name()
            col = v3c("text", self._modo).name()
            border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
            radii = (
                f"border-top-left-radius: 3px; "
                f"border-top-right-radius: {r}px; "
                f"border-bottom-left-radius: {r}px; "
                f"border-bottom-right-radius: {r}px;"
            )
            self._bubble.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {col}; "
                f"border: 1px solid {border}; {radii} {pad} {fsize} }}"
            )
        else:
            # Usuario — low-opacity primary tint + solid primary border, cola en top-right
            bg_color = v3c("primarySoft", self._modo)
            bg_css = qcolor_to_rgba_css(bg_color)
            border_color = v3c("primary", self._modo).name()
            text_col = v3c("text", self._modo).name()
            radii = (
                f"border-top-left-radius: {r}px; "
                f"border-top-right-radius: 3px; "
                f"border-bottom-left-radius: {r}px; "
                f"border-bottom-right-radius: {r}px;"
            )
            self._bubble.setStyleSheet(
                f"QLabel {{ background: {bg_css}; color: {text_col}; "
                f"border: 1px solid {border_color}; {radii} {pad} {fsize} }}"
            )


# ── NMSyncOrb ─────────────────────────────────────────────────────────────────


class NMProviderChip(QWidget):
    """Chip compacto para proveedor/modelo IA activo."""

    def __init__(
        self, text: str = "IA verificando", state: str = "syncing", modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._state = state
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)
        self._dot = NMSyncOrb(state=state, size=7, modo=self._modo, parent=self)
        lay.addWidget(self._dot)
        self._label = QLabel(text)
        self._label.setFont(qfont("size_caption"))
        lay.addWidget(self._label)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_status(self, text: str, state: str = "ok"):
        self._state = state
        self._dot.set_state(state)
        self._label.setText(text)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        border = C("teal", self._modo) if self._state == "ok" else c.get("border_card", c["border"])
        bg = _rgba(C("teal", self._modo), 0.10 if self._state == "ok" else 0.04)
        self.setStyleSheet(
            f"QWidget {{ background: {bg}; border: 1px solid {_rgba(border, 0.35)}; "
            f"border-radius: {RADIUS_PILL}px; }}"
        )
        self._label.setStyleSheet(label_style(self._modo, "text_secondary"))


class NMQuickAction(QPushButton):
    """Boton de sugerencia rapida del panel IA."""

    def __init__(self, text: str, modo: str = None, parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(30)
        self.setFont(qfont("size_caption"))
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c['text_secondary']}; "
            f"border: 1px solid {c.get('border_card', c['border'])}; "
            f"border-radius: {RADIUS_BUTTON}px; padding: 6px 10px; text-align: left; }}"
            f"QPushButton:hover {{ color: {C('teal', self._modo)}; "
            f"border-color: {_rgba(C('teal', self._modo), 0.35)}; "
            f"background: {_rgba(C('teal', self._modo), 0.06)}; }}"
        )


class NMPatientContext(QFrame):
    """Panel lateral de contexto de paciente para IA."""

    def __init__(self, paciente: str = "Sin paciente", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._rows: dict[str, QLabel] = {}
        self.setMinimumWidth(240)
        self.setMaximumWidth(270)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)
        self._title = QLabel("Contexto")
        self._title.setFont(qfont("size_body", bold=True))
        lay.addWidget(self._title)
        for key, label, value in [
            ("paciente", "Paciente", paciente),
            ("semanas", "Semanas", "12"),
            ("animo", "Ánimo 7d", "7.2/10"),
            ("distorsiones", "Distorsiones", "3"),
            ("progreso", "Progreso", "5d"),
        ]:
            row = QWidget()
            row_l = QVBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(1)
            lbl = QLabel(label)
            lbl.setFont(qfont("size_caption"))
            v = QLabel(value)
            v.setFont(qfont("size_small", bold=True))
            row_l.addWidget(lbl)
            row_l.addWidget(v)
            lay.addWidget(row)
            self._rows[key] = v
        lay.addStretch()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_patient(self, paciente: str):
        if "paciente" in self._rows:
            self._rows["paciente"].setText(paciente or "Sin paciente")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(
            f"QFrame {{ background: {c['bg_secondary']}; "
            f"border-left: 1px solid {c.get('border_card', c['border'])}; }}"
        )
        self._title.setStyleSheet(label_style(self._modo, "text_primary"))
        for key, lbl in self._rows.items():
            color_key = (
                "teal"
                if key == "animo"
                else ("violet" if key == "distorsiones" else "text_primary")
            )
            lbl.setStyleSheet(label_style(self._modo, color_key))
        for label in self.findChildren(QLabel):
            if label is self._title or label in self._rows.values():
                continue
            label.setStyleSheet(label_style(self._modo, "text_tertiary"))


        p.restore()
        p.end()



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
