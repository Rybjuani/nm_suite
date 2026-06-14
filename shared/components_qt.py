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
class _GradientTextLabel(QWidget):
    """Label que pinta texto con gradiente horizontal izquierda→derecha."""

    def __init__(
        self,
        text: str,
        font,
        color_left: str,
        color_right: str,
        height: int = 28,
        margins=(10, 6, 10, 10),
        parent=None,
    ):
        super().__init__(parent)
        self._text = text
        self._font = font
        self._c1 = QColor(color_left)
        self._c2 = QColor(color_right)
        self.setFixedHeight(height)
        self.setContentsMargins(*margins)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_colors(self, color_left: str, color_right: str):
        self._c1 = QColor(color_left)
        self._c2 = QColor(color_right)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self._font)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, self._c1)
        grad.setColorAt(1.0, self._c2)
        p.setPen(QPen(QBrush(grad), 1))
        r = self.contentsRect()
        p.drawText(r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._text)
        p.end()


class NMHubSidebar(QWidget):
    """Sidebar del Hub con nav vertical y pill activo."""

    nav_clicked = pyqtSignal(str)

    def __init__(
        self,
        items: list[tuple[str, str, str]],
        active: str = "",
        modo: str = None,
        parent=None,
        product: str = "Hub",
        sidebar_width: int = 200,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active = active or (items[0][0] if items else "")
        self._items_tuple = items
        self._product = product.lower()
        self._collapsed = False
        self._buttons: dict[str, QPushButton] = {}
        self._expanded_width = sidebar_width
        self._collapsed_width = 60
        self.setFixedWidth(sidebar_width)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        self._layout = lay
        lay.setContentsMargins(8, 10, 8, 10)
        lay.setSpacing(4)
        self._logo_icon = QLabel()
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._logo_icon.setContentsMargins(12, 10, 12, 10)
        self._logo_icon.setStyleSheet("background: transparent;")
        self._section_title = QLabel(
            "Herramientas" if product.lower() == "suite" else "Panel Profesional"
        )
        self._section_title.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._section_title.setContentsMargins(12, 0, 12, 10)
        self._section_title.setStyleSheet("background: transparent;")
        if self._product == "suite":
            self._logo_icon.hide()
            lay.addWidget(self._section_title)
            self._logo_text = self._section_title
        else:
            self._section_title.hide()
            lay.addWidget(self._logo_icon)
            self._logo_text = self._logo_icon
        for key, icon, label in items:
            btn = QPushButton(f"  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            try:
                qicon = nm_icon(icon, C("ink_secondary", self._modo), size=16)
                if qicon and not qicon.isNull():
                    btn.setIcon(qicon)
                    btn.setIconSize(QSize(18, 18))
            except Exception:
                pass
            btn.clicked.connect(lambda checked=False, k=key: self._select(k))
            lay.addWidget(btn)
            self._buttons[key] = btn
        lay.addStretch()
        # M3 F4: saludo del profesional en serif (Newsreader) para calidez emocional
        # — el Suite usa serif en los saludos del Home; el Hub debe resonar.
        self._footer = QLabel()
        try:
            self._footer.setFont(v3_font("size_caption", "weight_semibold", serif=True))
        except Exception:
            self._footer.setFont(qfont("size_caption"))
        self._footer.setContentsMargins(10, 10, 10, 4)
        self._footer.setWordWrap(True)
        lay.addWidget(self._footer)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_footer(self, text: str):
        text = (text or "").strip()
        self._footer.setText(text)
        self._footer.setVisible(bool(text) and not self._collapsed)

    def set_collapsed(self, collapsed: bool):
        """Colapsa la sidebar a solo iconos y conserva el isotipo de marca."""
        self._collapsed = bool(collapsed)
        self.setFixedWidth(self._collapsed_width if collapsed else self._expanded_width)
        if self._logo_text is self._logo_icon:
            self._logo_icon.setVisible(True)
        else:
            self._logo_text.setVisible(not collapsed)
        self._footer.setVisible(bool(self._footer.text().strip()) and not collapsed)
        _labels = {item[0]: item[2] for item in self._items_tuple}
        for key, btn in self._buttons.items():
            btn.setText("" if collapsed else f"  {_labels.get(key, '')}")
            btn.setToolTip(_labels.get(key, "") if collapsed else "")
        self._apply_theme(self._modo)

    def set_active(self, key: str):
        self._active = key
        self._apply_theme(self._modo)

    def _select(self, key: str):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo

        if hasattr(self, "_logo_icon") and self._logo_icon.parent() is not None:
            if self._logo_text is self._logo_icon:
                if self._collapsed:
                    from shared.assets import nm_logo_pixmap

                    self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._logo_icon.setContentsMargins(0, 10, 0, 10)
                    self._logo_icon.setFixedHeight(48)
                    self._logo_icon.setPixmap(
                        nm_logo_pixmap(self._modo, tipo="icon", width=30, height=30)
                    )
                    self._logo_icon.show()
                    self._section_title.hide()
                else:
                    from shared.assets import obtener_ruta_asset

                    logo_filename = "logo_dark.png" if is_dark else "logo_light.png"
                    logo_path = obtener_ruta_asset(logo_filename)
                    self._logo_icon.setAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                    self._logo_icon.setContentsMargins(12, 10, 12, 10)
                    self._logo_icon.setFixedHeight(56)
                    if os.path.exists(logo_path):
                        pm = QPixmap(logo_path)
                        self._logo_icon.setPixmap(
                            pm.scaledToWidth(130, Qt.TransformationMode.SmoothTransformation)
                        )
                        self._logo_icon.show()
                        self._section_title.hide()
                    else:
                        self._section_title.setText("NeuroMood Hub")
                        self._section_title.show()
                        self._logo_icon.hide()
            else:
                self._section_title.show()
                self._logo_icon.hide()

        # Sidebar sólida del mockup: bg-sidebar + borde line, sin glass.
        # Separación visual explícita (Rule 7, 8, 9): usamos bg_sidebar para contraste con el fondo
        bg = v3c("bg_sidebar", self._modo)
        bg_css = bg.name()
        border_c = v3c("border", self._modo)
        # Runtime: divisor vertical más sutil (antes 180/140 = duro). El
        # contraste bg_sidebar vs fondo ya separa; el borde solo lo acompaña.
        border_alpha = 110 if is_dark else 85
        border_rgba = f"rgba({border_c.red()},{border_c.green()},{border_c.blue()},{border_alpha})"
        self.setStyleSheet(
            f"NMHubSidebar {{ background-color: {bg_css}; border-right: 1px solid {border_rgba}; }}"
        )

        if hasattr(self, "_section_title"):
            self._section_title.setStyleSheet(
                f"color: {v3c('mute', self._modo).name()}; "
                "background: transparent;"
            )

        # ── Footer ───────────────────────────────────────────────────
        ink_secondary_hex = v3c("ink_secondary", self._modo).name()
        self._footer.setStyleSheet(
            f"color: {ink_secondary_hex}; background: transparent; border: none;"
        )

        # ── Nav buttons ────────────────────────────────────────────────
        primary_col = v3c("primary", self._modo)
        primary_hex = primary_col.name()
        text_hex = v3c("text", self._modo).name()
        text2_hex = v3c("text2", self._modo).name()
        active_bg = (
            f"rgba({primary_col.red()},{primary_col.green()},"
            f"{primary_col.blue()},{58 if is_dark else 34})"
        )
        primary_soft = (
            f"rgba({primary_col.red()},{primary_col.green()},"
            f"{primary_col.blue()}, {25 if is_dark else 22})"
        )
        font_pt = TYPOGRAPHY["size_small"]

        for key, btn in self._buttons.items():
            active = key == self._active
            btn.setFixedHeight(38)
            align = "center" if self._collapsed else "left"
            padding = "8px 0px" if self._collapsed else "8px 10px"
            radius = 12 if self._collapsed else 8
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  text-align: {align};"
                f"  background: {active_bg if active else 'transparent'};"
                f"  color: {primary_hex if active else text2_hex};"
                f"  border: none;"
                f"  border-left: {3 if active and not self._collapsed else 0}px solid {primary_hex};"
                f"  border-radius: {radius}px;"
                # 10px: con la sidebar angosta (172) el padding 12 cortaba
                # "Personalización" (el label más largo).
                f"  padding: {padding};"
                f"  font-size: {font_pt}px;"
                f"  font-weight: 500;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background: {active_bg if active else primary_soft};"
                f"  color: {primary_hex if active else text_hex};"
                f"}}"
            )
            # Icon: primary_ink when active, text2 at rest
            icon_color = primary_hex if active else text2_hex
            for item in self._items_tuple:
                if item[0] == key:
                    try:
                        qicon = nm_icon(item[1], icon_color, size=16)
                        if qicon and not qicon.isNull():
                            btn.setIcon(qicon)
                            icon_px = 20 if self._collapsed else 18
                            btn.setIconSize(QSize(icon_px, icon_px))
                    except Exception:
                        pass
                    break


class FlowLayout(QLayout):
    """Layout que acomoda los items en filas y los envuelve a la línea siguiente
    cuando no entran en el ancho disponible (patrón estándar de Qt).

    Pensado para grupos de chips/badges que no deben desbordar ni recortarse a
    anchos chicos (regla anti-solape del HANDOFF §3). Implementa
    ``heightForWidth`` para que el contenedor reserve el alto correcto al envolver.
    """

    def __init__(self, parent=None, margin: int = 0, spacing: int = 6):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._items = []

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only: bool):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        right = rect.right() - m.right()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            w, h = hint.width(), hint.height()
            next_x = x + w
            if next_x > right and line_height > 0:
                x = rect.x() + m.left()
                y = y + line_height + self._spacing
                next_x = x + w
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x + self._spacing
            line_height = max(line_height, h)
        return y + line_height - rect.y() + m.bottom()


class NMFeaturedCard(QFrame):
    """Card principal del Hub Dashboard con blob gradient de fondo.

    Muestra ánimo promedio como número grande + emoji + subtítulo.
    API: set_score(float, str), set_delta(float|None), set_meta(str), set_tags(list[tuple[str,str]])
    """

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(140)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("lg"), sp("md"), sp("lg"), sp("md"))
        lay.setSpacing(sp("xs") if hasattr(sp, "__call__") else 4)

        # Sub-label superior teal uppercase (ej. "Ánimo promedio · semana")
        self._title_lbl = QLabel("Ánimo promedio · semana")
        self._title_lbl.setFont(qfont("size_caption", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._title_lbl)

        # Fila: score grande + "/10" + emoji + delta pill
        score_row = QHBoxLayout()
        score_row.setSpacing(sp("sm"))
        self._score_lbl = QLabel("—")
        self._score_lbl.setFont(qfont("size_h1", bold=True))
        self._score_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._score_lbl)

        self._slash_lbl = QLabel("/ 10")
        self._slash_lbl.setFont(qfont("size_small"))
        self._slash_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._slash_lbl)

        self._emoji_lbl = QLabel("\U0001f610")
        self._emoji_lbl.setFont(qfont("size_h2"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._emoji_lbl)

        self._delta_lbl = QLabel()
        self._delta_lbl.setFont(qfont("size_caption", bold=True))
        self._delta_lbl.setVisible(False)
        score_row.addWidget(self._delta_lbl)

        score_row.addStretch()
        lay.addLayout(score_row)

        # Meta line: "N semanas en programa · Última sesión: hace X días"
        self._sub_lbl = QLabel()
        self._sub_lbl.setFont(qfont("size_small"))
        self._sub_lbl.setStyleSheet("background: transparent;")
        self._sub_lbl.setVisible(False)
        lay.addWidget(self._sub_lbl)

        # Tags row (pills) — FlowLayout: los chips envuelven en vez de desbordar.
        self._tags_widget = QWidget()
        self._tags_widget.setStyleSheet("background: transparent;")
        _tags_pol = self._tags_widget.sizePolicy()
        _tags_pol.setHeightForWidth(True)
        self._tags_widget.setSizePolicy(_tags_pol)
        self._tags_layout = FlowLayout(
            self._tags_widget, margin=0, spacing=sp("sm") if hasattr(sp, "__call__") else 8
        )  # 8px gap per F3.3
        self._tags_widget.setVisible(False)
        lay.addWidget(self._tags_widget)

        # Sparkline de área (tendencia semanal de ánimo). Va debajo de las
        # métricas para que la línea nunca cruce chips ni labels.
        self._spark = NMAreaSparkline(modo=self._modo)
        self._spark.setVisible(False)
        lay.addWidget(self._spark)

        lay.addStretch()

        self._last_delta = None  # cache para re-aplicar en cambio de tema

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_score(self, score: float, emoji: str = "\U0001f610"):
        self._score_lbl.setText(f"{score:.1f}")
        self._emoji_lbl.setText(emoji)
        self.update()

    def set_delta(self, delta):
        """Muestra pill con delta vs semana anterior. None oculta el pill."""
        self._last_delta = delta
        if delta is None:
            self._delta_lbl.setVisible(False)
            return
        sign = "↑" if delta >= 0 else "↓"
        text = f"{sign} {abs(delta):.1f} vs semana anterior"
        self._delta_lbl.setText(text)
        teal = C("teal", self._modo)
        amber = C("warning", self._modo)
        bg_color = _rgba(teal, 0.14) if delta >= 0 else _rgba(amber, 0.14)
        fg_color = teal if delta >= 0 else amber
        self._delta_lbl.setStyleSheet(
            f"QLabel {{ background: {bg_color}; color: {fg_color}; "
            f"border-radius: 10px; padding: 2px 8px; }}"
        )
        self._delta_lbl.setVisible(True)

    def set_series(self, data, labels=None):
        """Serie semanal de ánimo para el sparkline de área. Lista vacía la oculta."""
        if not data:
            self._spark.setVisible(False)
            return
        self._spark.set_series(data, labels)
        self._spark.setVisible(True)

    def set_meta(self, text: str):
        """Muestra línea gris con meta info (semanas, última sesión)."""
        if not text:
            self._sub_lbl.setVisible(False)
            return
        self._sub_lbl.setText(text)
        self._sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._sub_lbl.setVisible(True)

    def set_tags(self, tags):
        """tags: list[tuple[str, str]] donde str2 es 'teal'|'violet'|'accent'."""
        # Limpiar tags anteriores
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item is not None and item.widget():
                item.widget().deleteLater()
        if not tags:
            self._tags_widget.setVisible(False)
            return
        color_map = {
            "teal": ("teal", 0.14),
            "violet": ("violet", 0.14),
            "accent": ("accent", 0.14),
        }
        for label_text, color_key in tags[:3]:
            key, alpha = color_map.get(color_key, ("teal", 0.14))
            fg = C(key, self._modo)
            bg = _rgba(fg, alpha)
            chip = QLabel(label_text)
            chip.setFont(qfont("size_caption", bold=True))
            chip.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {fg}; "
                f"border-radius: 10px; padding: 2px 9px; }}"
            )
            self._tags_layout.addWidget(chip)
        self._tags_widget.setVisible(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        r = RADIUS_CARD
        is_dark = "dark" in self._modo
        surf_col = v3c("surfaceSolid" if is_dark else "surface", self._modo)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, surf_col)

        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.restore()
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        teal = C("teal", self._modo)
        self._title_lbl.setStyleSheet(
            f"color: {teal}; background: transparent;"
        )
        self._score_lbl.setStyleSheet(
            f"color: {C('text_primary', self._modo)}; background: transparent;"
        )
        self._slash_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        if self._sub_lbl.isVisible():
            self._sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        # Re-aplicar delta con los nuevos colores de tema
        if hasattr(self, "_last_delta"):
            self.set_delta(self._last_delta)
        self.update()


# ── NMChatBubble ──────────────────────────────────────────────────────────────


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
