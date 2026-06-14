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


class NMIconButton(QToolButton):
    """NMIconButton F1 Polish V2."""

    def __init__(
        self,
        icon_name: str,
        size: str = "default",
        variant: str = "default",
        tooltip: str = "",
        checkable: bool = False,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._icon_name = icon_name
        self._variant = variant
        self._size_str = size

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(checkable)
        if tooltip:
            self.setToolTip(tooltip)

        if size == "sm":
            wh = 28
            self._isize = 16
        else:
            wh = 36
            self._isize = 20

        self.setFixedSize(wh, wh)
        self.setIconSize(QSize(self._isize, self._isize))
        self.setObjectName("NMIconButton")

        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        ic_color = C("ink_primary", self._modo)
        if self._icon_name:
            self.setIcon(nm_icon(self._icon_name, ic_color, size=self._isize))

        if self._variant == "ghost":
            bg = "transparent"
            hov_bg = C("surface2", self._modo)
            bd = "transparent"
        elif self._variant == "tint":
            bg = C("surface2", self._modo)
            hov_bg = C("surface", self._modo)
            bd = C("border", self._modo)
        else:  # default
            bg = C("surface", self._modo)
            hov_bg = C("surface2", self._modo)
            bd = C("border", self._modo)

        r = self.width() // 2
        prim = C("primary", self._modo)

        self.setStyleSheet(f"""
            QToolButton#NMIconButton {{
                background-color: {bg};
                border: 1px solid {bd};
                border-radius: {r}px;
            }}
            QToolButton#NMIconButton:hover {{
                background-color: {hov_bg};
            }}
            QToolButton#NMIconButton:checked {{
                background-color: {prim};
                border: 1px solid {prim};
            }}
        """)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()




# ── NMSidebar ─────────────────────────────────────────────────────────────────


class _SidebarItem(QWidget):
    """Ítem individual del sidebar."""

    clicked = pyqtSignal(str)

    def __init__(
        self, item_id: str, icon: str | QIcon, label: str, parent=None, modo: str = "dark_hybrid"
    ):
        super().__init__(parent)
        self._id = item_id
        self._icon = icon
        self._icon_pixmap = icon.pixmap(20, 20) if isinstance(icon, QIcon) else None
        self._label = label
        self._modo = norm_modo(modo)
        self._active = False
        self._hover = False
        self._hover_alpha = 0.0
        self._bar_anim_val = 0.0  # 0.0→1.0 para la barra izquierda

        self.setFixedHeight(_NM_CONTROL_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._bar_anim = QPropertyAnimation(self, b"bar_val", self)
        self._bar_anim.setDuration(150)
        self._bar_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim = QPropertyAnimation(self, b"hover_alpha", self)
        self._hover_anim.setDuration(120)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_bar_val(self) -> float:
        return self._bar_anim_val

    def _set_bar_val(self, v: float):
        self._bar_anim_val = v
        self.update()

    bar_val = pyqtProperty(float, _get_bar_val, _set_bar_val)

    def _get_hover_alpha(self) -> float:
        return self._hover_alpha

    def _set_hover_alpha(self, v: float):
        self._hover_alpha = max(0.0, min(1.0, v))
        self.update()

    hover_alpha = pyqtProperty(float, _get_hover_alpha, _set_hover_alpha)

    def set_active(self, active: bool):
        self._active = active
        target = 1.0 if active else 0.0
        self._bar_anim.stop()
        self._bar_anim.setStartValue(self._bar_anim_val)
        self._bar_anim.setEndValue(target)
        self._bar_anim.start()

    def enterEvent(self, event):
        self._hover = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_alpha)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_alpha)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._id)
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        is_dark = "dark" in self._modo
        r = V3_RD["md"]  # 10px — softer pill than RADIUS_BUTTON

        # ── Active background ──────────────────────────────────────────
        if self._active:
            bg = v3c("primary", self._modo)
            # Light: 12% primary tint on warm cream; Dark: 14% primary tint on navy
            bg.setAlpha(31 if is_dark else 28)
            path = QPainterPath()
            path.addRoundedRect(QRectF(6, 2, w - 12, h - 4), r, r)
            p.fillPath(path, QBrush(bg))

        # ── Hover background ─────────────────────────────────────────
        elif self._hover_alpha > 0:
            # Use border token fill — readable in both light and dark
            hover_bg = v3c("borderSoft", self._modo)
            hover_bg.setAlpha(
                int(hover_bg.alpha() * self._hover_alpha)
                if hover_bg.alpha() > 0
                else int(28 * self._hover_alpha)
            )
            if is_dark:
                # Dark: explicit alpha since borderSoft is rgba
                hover_fill = v3c("border", self._modo)
                hover_fill.setAlpha(int(40 * self._hover_alpha))
            else:
                # Light: warm stone tint, alpha-driven by hover_alpha
                hover_fill = v3c("border", self._modo)
                hover_fill.setAlpha(int(55 * self._hover_alpha))
            path = QPainterPath()
            path.addRoundedRect(QRectF(6, 2, w - 12, h - 4), r, r)
            p.fillPath(path, QBrush(hover_fill))

        # ── Focus ring ──────────────────────────────────────────────
        if self.hasFocus():
            focus_c = v3c("accent", self._modo)
            p.setPen(QPen(focus_c, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(7, 3, w - 14, h - 6), r, r)

        # ── Left active bar (3px, animated) ─────────────────────────────
        if self._bar_anim_val > 0:
            bar_h = int((h - 10) * self._bar_anim_val)
            bar_y = (h - bar_h) // 2
            bar_c = v3c("primary", self._modo)
            bar_path = QPainterPath()
            bar_path.addRoundedRect(QRectF(0, bar_y, 3, bar_h), 1.5, 1.5)
            p.fillPath(bar_path, QBrush(bar_c))

        # ── Icon ────────────────────────────────────────────────────
        # Active: primary color; hover: text; rest: textMuted
        if self._active:
            text_color = v3c("primary", self._modo)
        elif self._hover:
            text_color = v3c("text", self._modo)
        else:
            text_color = v3c("textMuted", self._modo)
        p.setPen(QPen(text_color))

        # Icon zone: x=16, width=28 — nudged 2px right from old x=14
        icon_rect = QRect(16, 0, 28, h)
        if self._icon_pixmap is not None:
            x = icon_rect.x() + (icon_rect.width() - self._icon_pixmap.width()) // 2
            y = icon_rect.y() + (icon_rect.height() - self._icon_pixmap.height()) // 2
            p.drawPixmap(x, y, self._icon_pixmap)
        else:
            font_icon = qfont("size_body")
            font_icon.setFamily("Segoe UI Emoji")
            p.setFont(font_icon)
            p.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, self._icon)

        # ── Label ───────────────────────────────────────────────────
        # Active: text (full contrast); hover: text; rest: textMuted
        if self._active:
            label_color = v3c("text", self._modo)
        elif self._hover:
            label_color = v3c("text", self._modo)
        else:
            label_color = v3c("textMuted", self._modo)
        p.setPen(QPen(label_color))

        # weight_semibold for active, weight_normal for rest (no bold jump)
        weight = TYPOGRAPHY["weight_semibold"] if self._active else TYPOGRAPHY["weight_normal"]
        p.setFont(qfont("size_small", weight=weight))
        # Label starts at x=46 (was 44) to match nudged icon zone
        label_rect = QRect(46, 0, w - 50, h)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignVCenter, self._label)

        p.end()

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMSidebar(QWidget):
    """
    Sidebar de navegación de 200px. Emite nav_changed(str) al hacer click en un ítem.
    """

    nav_changed = pyqtSignal(str)

    def __init__(self, parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._items: dict[str, _SidebarItem] = {}
        self._active_id: str = ""
        self._theme_labels: list[tuple[QLabel, str]] = []
        self._logo_shadow: QGraphicsDropShadowEffect | None = None
        self._logo_lbl: QLabel | None = None

        self.setFixedWidth(200)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        is_dark = "dark" in self._modo
        # Use V3 sidebar bg token with alpha for glassmorphism
        if is_dark:
            bg = v3c("bgSidebar", self._modo)
            bg.setAlpha(180)
        else:
            bg = QColor(0xF2, 0xED, 0xE2, 210)  # Glassy warm cream
        p.fillRect(self.rect(), QBrush(bg))
        # Subtle glowing glass border on the right
        border_c = v3c("border", self._modo)
        border_c.setAlpha(90 if is_dark else 140)
        p.setPen(QPen(border_c, 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.end()
        super().paintEvent(event)

    def add_header(self, title: str, subtitle: str = ""):
        """Añade sección de título/logo al tope del sidebar."""
        colors(self._modo)
        w = QWidget()
        w.setObjectName("SidebarHeader")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 6)
        vl.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setFont(qfont("size_small", bold=True))
        lbl_title.setStyleSheet(label_style(self._modo, "accent"))
        self._theme_labels.append((lbl_title, "accent"))
        vl.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setFont(qfont("size_caption"))
            lbl_sub.setStyleSheet(label_style(self._modo, "text_tertiary"))
            self._theme_labels.append((lbl_sub, "text_tertiary"))
            vl.addWidget(lbl_sub)

        self._layout.addWidget(w)
        self._add_separator()

    def add_logo(self, logo_path: str = ""):
        """Inserta logo UI con sombra al tope del sidebar.
        Usa logos-icon-{light,dark}.png segun tema."""
        from PyQt6.QtGui import QPixmap

        w = QWidget()
        w.setObjectName("SidebarLogo")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 4)

        logo_lbl = QLabel()
        try:
            if logo_path:
                path = logo_path
            else:
                icon_name = (
                    "logos-icon-light.png" if "light" in self._modo else "logos-icon-dark.png"
                )
                path = obtener_ruta_recurso(icon_name)
                if not os.path.exists(path):
                    path = obtener_ruta_recurso("LOGO.png")
            if os.path.exists(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    pm = pm.scaled(
                        144,
                        32,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    logo_lbl.setPixmap(pm)
                else:
                    raise FileNotFoundError
            else:
                raise FileNotFoundError
        except Exception:
            logo_lbl.setText("NeuroMood")
            logo_lbl.setStyleSheet(label_style(self._modo, "accent"))
            logo_lbl.setFont(qfont("size_h3", bold=True))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        is_dark = "dark" in self._modo
        shadow = QGraphicsDropShadowEffect(logo_lbl)
        shadow.setBlurRadius(8 if is_dark else 4)
        shadow.setOffset(0, 2)
        if is_dark:
            col = QColor(C("accent", self._modo))
            col.setAlpha(115)
        else:
            col = QColor(15, 23, 42, 26)  # rgba(15,23,42,.10) — spec light logo shadow
        shadow.setColor(col)
        logo_lbl.setGraphicsEffect(shadow)
        self._logo_shadow = shadow
        self._logo_lbl = logo_lbl

        vl.addWidget(logo_lbl)
        self._layout.insertWidget(0, w)

    def add_item(self, item_id: str, icon: str | QIcon, label: str):
        item = _SidebarItem(item_id, icon, label, self, self._modo)
        item.clicked.connect(self._on_item_clicked)
        self._items[item_id] = item
        self._layout.addWidget(item)

    def add_separator(self):
        self._add_separator()

    def _add_separator(self):
        sep = QWidget()
        sep.setFixedHeight(1)
        # Use V3 border token — warm stone in light, violet-tinted in dark
        border_c = v3c("border", self._modo)
        sep.setStyleSheet(
            f"background-color: rgba({border_c.red()},{border_c.green()},{border_c.blue()},90);"
        )
        self._layout.addWidget(sep)

    def add_spacer(self):

        self._layout.addStretch()

    def add_label(self, text: str):
        colors(self._modo)
        lbl = QLabel(text)
        lbl.setFont(qfont("size_caption"))
        lbl.setWordWrap(True)
        lbl.setContentsMargins(14, 4, 14, 4)
        lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._theme_labels.append((lbl, "text_tertiary"))
        self._layout.addWidget(lbl)
        self._status_label = lbl

    def set_active(self, item_id: str):
        for iid, item in self._items.items():
            item.set_active(iid == item_id)
        self._active_id = item_id

    def _on_item_clicked(self, item_id: str):
        self.set_active(item_id)
        self.nav_changed.emit(item_id)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        for item in self._items.values():
            item.apply_theme(modo)
        colors(self._modo)
        # Actualizar labels temáticos y limpiar referencias muertas
        alive = []
        for lbl, color_key in self._theme_labels:
            if not sip.isdeleted(lbl):
                lbl.setStyleSheet(label_style(self._modo, color_key))
                alive.append((lbl, color_key))
        self._theme_labels = alive
        # Actualizar sombra del logo
        if self._logo_shadow is not None:
            if "dark" in self._modo:
                col = QColor(C("accent", self._modo))
                col.setAlpha(115)
            else:
                col = QColor(15, 23, 42, 26)
            self._logo_shadow.setBlurRadius(8 if "dark" in self._modo else 4)
            self._logo_shadow.setColor(col)
        # Recolorear logo en light mode o cargar logos runtime directos
        if self._logo_lbl is not None:
            try:
                from shared.assets import obtener_ruta_asset, LOGO_LIGHT, LOGO_DARK

                logo_name = LOGO_LIGHT if "light" in self._modo else LOGO_DARK
                path = obtener_ruta_asset(logo_name)
                pm = None
                if os.path.exists(path):
                    pm = QPixmap(path)
                else:
                    path = obtener_ruta_recurso("LOGO.png")
                    if os.path.exists(path):
                        pm = QPixmap(path)
                        if "light" in self._modo:
                            from PIL import Image as PILImage

                            img = PILImage.open(path).convert("RGBA")
                            img = recolorear_logo_light(img)
                            data = img.tobytes("raw", "RGBA")
                            qimg = QImage(
                                data, img.width, img.height, QImage.Format.Format_RGBA8888
                            )
                            pm = QPixmap.fromImage(qimg)
                if pm and not pm.isNull():
                    self._logo_lbl.setPixmap(
                        pm.scaled(
                            144,
                            32,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
            except Exception:
                pass
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and w.minimumHeight() == 1 and w.maximumHeight() == 1:
                border_c = v3c("border", self._modo)
                w.setStyleSheet(
                    f"background-color: rgba({border_c.red()},{border_c.green()},"
                    f"{border_c.blue()},90);"
                )


# ── NMHeader ──────────────────────────────────────────────────────────────────


class NMHeader(QWidget):
    """
    Header de 56px con contexto, nombre de usuario y control dark/light compacto.
    Emite theme_toggle() al hacer click en el control.

    Modos:
      - Normal (default): contexto + username + theme button
      - show_back=True: boton volver + icono + titulo de modulo
      - home_mode=True: greeting + subtitle + streak badge + theme toggle
    """

    theme_toggle = pyqtSignal()

    def __init__(
        self,
        parent=None,
        modo: str = None,
        username: str = "",
        show_back: bool = False,
        module_title: str = "",
        module_icon: str = "",
        home_mode: bool = False,
        greeting: str = "",
        subtitle: str = "",
        streak: int = 0,
        hide_selector: bool = False,
        is_suite: bool = False,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._username = username
        self._show_back = show_back
        self._module_title = module_title
        self._module_icon = module_icon
        self._home_mode = home_mode
        self._greeting = greeting
        self._subtitle_text = subtitle
        self._streak = streak
        self._hide_selector = hide_selector
        self._is_suite = is_suite

        self.setFixedHeight(HEADER_H)
        self._setup_ui()
        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(20)

        colors(self._modo)

        if self._show_back:
            # Módulo: botón back estilo pill (mockup: .back-btn)
            self._btn_back = QPushButton("← Volver")
            self._btn_back.setFont(qfont("size_caption", bold=True))
            self._btn_back.setFixedHeight(30)
            self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
            self._apply_back_btn_style()
            layout.addWidget(self._btn_back)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("background: transparent;")
            self._module_icon_lbl = icon_lbl
            self._apply_module_icon()
            layout.addWidget(icon_lbl)

            title_lbl = QLabel(self._module_title)
            title_lbl.setFont(qfont("size_h3", bold=True))
            title_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
            self._module_title_lbl = title_lbl
            layout.addWidget(title_lbl)
        else:
            if self._home_mode:
                # Home mode: greeting + subtitle + streak
                left_col = QVBoxLayout()
                left_col.setSpacing(2)
                greet_lbl = QLabel(self._greeting)
                greet_lbl.setFont(qfont("size_h1", bold=True))
                greet_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
                self._greet_lbl = greet_lbl
                left_col.addWidget(greet_lbl)
                sub_lbl = QLabel(self._subtitle_text)
                sub_lbl.setFont(qfont("size_small"))
                sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
                self._sub_lbl = sub_lbl
                left_col.addWidget(sub_lbl)
                layout.addLayout(left_col, stretch=1)
                layout.addSpacing(sp("md"))

                if self._streak > 0:
                    self._streak_badge = NMStreakBadge(self._streak, self._modo)
                    layout.addWidget(self._streak_badge)
            else:
                self._logo_widget = None

                product_is_suite = bool(self._username)

                if not self._is_suite:
                    brand = QWidget(self)
                    brand.setStyleSheet("background: transparent;")
                    brand_l = QHBoxLayout(brand)
                    brand_l.setContentsMargins(0, 0, 0, 0)
                    brand_l.setSpacing(10)
                    self._hud_mark = _ChromeLogoMark(self._modo, brand)
                    self._hud_mark.setFixedSize(24, 24)
                    brand_l.addWidget(self._hud_mark, 0, Qt.AlignmentFlag.AlignVCenter)

                    brand_txt = QVBoxLayout()
                    brand_txt.setSpacing(0)
                    self._brand_name_lbl = QLabel("NeuroMood")
                    self._brand_name_lbl.setFont(
                        qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    self._brand_mode_lbl = QLabel(
                        "Suite" if product_is_suite else "Hub"
                    )
                    self._brand_mode_lbl.setFont(
                        qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    brand_txt.addWidget(self._brand_name_lbl)
                    brand_txt.addWidget(self._brand_mode_lbl)
                    brand_l.addLayout(brand_txt)
                    layout.addWidget(brand, 0, Qt.AlignmentFlag.AlignVCenter)

                    layout.addStretch(1)

                    self._mode_selector = QWidget(self)
                    self._mode_selector.setObjectName("NMModeSelector")
                    selector_l = QHBoxLayout(self._mode_selector)
                    selector_l.setContentsMargins(2, 2, 2, 2)
                    selector_l.setSpacing(0)
                    self._suite_tab_lbl = QLabel("Suite")
                    self._hub_tab_lbl = QLabel("Hub")
                    for tab in (self._suite_tab_lbl, self._hub_tab_lbl):
                        tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        tab.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
                        tab.setMinimumHeight(24)
                        tab.setContentsMargins(12, 3, 12, 3)
                        selector_l.addWidget(tab)
                    self._suite_tab_active = product_is_suite
                    layout.addWidget(self._mode_selector, 0, Qt.AlignmentFlag.AlignCenter)
                    if self._hide_selector:
                        self._mode_selector.hide()

                    layout.addStretch(1)

                    identity = QWidget(self)
                    identity.setStyleSheet("background: transparent;")
                    identity_l = QHBoxLayout(identity)
                    identity_l.setContentsMargins(0, 0, 0, 0)
                    identity_l.setSpacing(10)
                    meta_l = QVBoxLayout()
                    meta_l.setSpacing(0)
                    display_name = self._username or "Dra. Garcia"
                    self._identity_name_lbl = QLabel(display_name)
                    self._identity_name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                    self._identity_name_lbl.setFont(
                        qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    self._identity_role_lbl = QLabel(
                        "Programa Activo" if product_is_suite else "Panel Profesional"
                    )
                    self._identity_role_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                    self._identity_role_lbl.setFont(
                        qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    meta_l.addWidget(self._identity_name_lbl)
                    meta_l.addWidget(self._identity_role_lbl)
                    identity_l.addLayout(meta_l)
                    initials = (
                        "".join(part[:1] for part in display_name.split()[:2]).upper() or "NM"
                    )
                    self._identity_avatar_lbl = QLabel(initials)
                    self._identity_avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._identity_avatar_lbl.setFixedSize(28, 28)
                    self._identity_avatar_lbl.setFont(
                        qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    identity_l.addWidget(self._identity_avatar_lbl)
                    layout.addWidget(identity, 0, Qt.AlignmentFlag.AlignVCenter)

        if self._show_back or self._home_mode or self._is_suite:
            layout.addStretch()

        self._theme_lbl = QLabel(self._theme_label_text())
        self._theme_lbl.setFont(qfont("size_caption"))
        self._theme_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))
        layout.addWidget(self._theme_lbl)
        self._theme_lbl.hide()  # compact R3: toggle comunica el estado sin label

        # Compact theme button: sidebar/window chrome already carry the brand.
        self._toggle = QPushButton(self)
        self._toggle.setCheckable(True)
        self._toggle.setFixedSize(28, 28)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.setAccessibleName("Cambiar tema")
        self._toggle.setChecked("light" in self._modo)
        self._toggle.toggled.connect(lambda _: self.theme_toggle.emit())
        self._apply_theme_button_style()
        layout.addWidget(self._toggle)
        # En Suite el toggle ya vive en NMWindowChrome — ocultarlo aquí evita duplicado
        if self._is_suite:
            self._toggle.hide()
        self._apply_hud_styles()

    def _ensure_context_widgets(self):
        if hasattr(self, "_context_title_lbl"):
            return
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        title_lbl = QLabel("")
        title_lbl.setFont(qfont("size_h3", bold=True))
        title_lbl.setStyleSheet(label_style(self._modo, "text_primary"))

        self._context_icon_lbl = icon_lbl
        self._context_title_lbl = title_lbl
        self._module_icon_lbl = icon_lbl
        self._module_title_lbl = title_lbl

        layout = self.layout()
        if layout:
            insert_at = 1 if hasattr(self, "_btn_back") else 0
            layout.insertWidget(insert_at, icon_lbl)
            layout.insertWidget(insert_at + 1, title_lbl)
        icon_lbl.hide()
        title_lbl.hide()

    def set_context_title(self, title: str = "", icon: str = ""):
        """Activa el header contextual compacto usado por pantallas internas."""
        title = (title or "").strip()
        self._module_title = title
        self._module_icon = icon or ""

        if title:
            self._ensure_context_widgets()
            if hasattr(self, "_logo_widget") and self._logo_widget is not None:
                self._logo_widget.hide()
            if hasattr(self, "_user_lbl") and self._user_lbl is not None:
                self._user_lbl.hide()
            if hasattr(self, "_greet_lbl") and self._greet_lbl is not None:
                self._greet_lbl.hide()
            if hasattr(self, "_sub_lbl") and self._sub_lbl is not None:
                self._sub_lbl.hide()
            if hasattr(self, "_streak_badge") and self._streak_badge is not None:
                self._streak_badge.hide()
            if hasattr(self, "_mode_selector"):
                self._mode_selector.hide()
            self._context_title_lbl.setText(title)
            self._context_title_lbl.show()
            self._context_icon_lbl.setVisible(bool(icon))
            self._apply_module_icon()
            return

        if hasattr(self, "_context_title_lbl"):
            self._context_title_lbl.hide()
        if hasattr(self, "_context_icon_lbl"):
            self._context_icon_lbl.hide()
        if hasattr(self, "_logo_widget") and self._logo_widget is not None:
            self._logo_widget.show()
        if hasattr(self, "_user_lbl") and self._user_lbl is not None:
            self._user_lbl.show()
        if hasattr(self, "_greet_lbl") and self._greet_lbl is not None:
            self._greet_lbl.show()
        if hasattr(self, "_sub_lbl") and self._sub_lbl is not None:
            self._sub_lbl.show()
        if hasattr(self, "_streak_badge") and self._streak_badge is not None:
            self._streak_badge.show()
        if hasattr(self, "_mode_selector") and not self._hide_selector:
            self._mode_selector.show()
        if hasattr(self, "_context_badge_lbl"):
            self._context_badge_lbl.hide()

    def set_context_badge(self, text: str = "", color_key: str = "teal"):
        if getattr(self, "_is_suite", False):
            return
        text = (text or "").strip()
        if not hasattr(self, "_context_badge_lbl"):
            self._context_badge_lbl = QLabel("")
            self._context_badge_lbl.setFont(qfont("size_caption", bold=True))
            self._context_badge_lbl.setContentsMargins(8, 2, 8, 2)
            layout = self.layout()
            if layout:
                layout.insertWidget(max(0, layout.count() - 3), self._context_badge_lbl)
        self._context_badge_key = color_key or "teal"
        self._context_badge_lbl.setText(text)
        self._context_badge_lbl.setVisible(bool(text))
        self._apply_context_badge_style()

    def _apply_context_badge_style(self):
        if not hasattr(self, "_context_badge_lbl"):
            return
        key = getattr(self, "_context_badge_key", "teal")
        fg = C(key, self._modo) if key in colors(self._modo) else C("teal", self._modo)
        bg = _rgba(fg, 0.14)
        self._context_badge_lbl.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; "
            f"border-radius: {RADIUS_PILL}px; padding: 2px 8px; }}"
        )

    def _theme_label_text(self) -> str:
        return "Claro" if "light" in self._modo else "Oscuro"

    def _apply_theme_button_style(self) -> None:
        if not hasattr(self, "_toggle"):
            return
        c = colors(self._modo)
        icon_key = "moon" if "light" in self._modo else "sun"
        self._toggle.setIcon(nm_icon(icon_key, C("text_secondary", self._modo), size=15))
        self._toggle.setIconSize(QSize(15, 15))
        self._toggle.setToolTip(
            "Cambiar a modo oscuro" if "light" in self._modo else "Cambiar a modo claro"
        )
        self._toggle.setStyleSheet(
            f"QPushButton {{"
            f" background: {c.get('bg_elevated', c['bg_surface'])};"
            f" border: 1px solid {c.get('border_card', c['border'])};"
            f" border-radius: 8px;"
            f" padding: 0px;"
            f"}}"
            f"QPushButton:hover {{"
            f" background: {c.get('bg_hover', c.get('bg_secondary', c['bg_surface']))};"
            f" border-color: {c.get('border_strong', c.get('border', '#ffffff'))};"
            f"}}"
            f"QPushButton:focus {{"
            f" border: 1px solid {C('accent', self._modo)};"
            f"}}"
        )

    def _apply_module_icon(self):
        if not hasattr(self, "_module_icon_lbl"):
            return
        icon_key = self._module_icon or ""
        if not icon_key:
            self._module_icon_lbl.clear()
            return
        try:
            pm = nm_icon(icon_key, C("accent", self._modo), size=22).pixmap(22, 22)
            if not pm.isNull():
                self._module_icon_lbl.setPixmap(pm)
                self._module_icon_lbl.setText("")
                return
        except Exception:
            pass
        self._module_icon_lbl.setText(icon_key)
        self._module_icon_lbl.setFont(qfont("size_body"))

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        # Runtime spec: top command hud uses bg_canvas background
        p.fillRect(self.rect(), v3c("bg", self._modo))
        # Subtle glass border at bottom
        p.setPen(QPen(v3c("border", self._modo), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()
        super().paintEvent(event)

    def _apply_hud_styles(self):
        if not hasattr(self, "_brand_name_lbl"):
            return
        primary = v3c("primary", self._modo).name()
        primary_ink = v3c("primary_ink", self._modo).name()
        surface2 = v3c("surface_2", self._modo).name()
        text = v3c("text", self._modo).name()
        text2 = v3c("text2", self._modo).name()
        mute = v3c("mute", self._modo).name()
        border = C("border", self._modo)
        self._hud_mark._apply_theme(self._modo)
        self._brand_name_lbl.setStyleSheet(f"color: {text}; background: transparent;")
        self._brand_mode_lbl.setStyleSheet(
            f"color: {mute}; background: transparent; text-transform: uppercase; font-size: 8.5px;"
        )

        selector = self.findChild(QWidget, "NMModeSelector")
        if selector:
            # More subtle selector (pill secondary surface)
            selector.setStyleSheet(
                f"QWidget#NMModeSelector {{ background: {surface2}; "
                f"border: 1px solid {border}; border-radius: 14px; }}"
            )

        suite_active = getattr(self, "_suite_tab_active", False)
        for label, active in (
            (getattr(self, "_suite_tab_lbl", None), suite_active),
            (getattr(self, "_hub_tab_lbl", None), not suite_active),
        ):
            if label is None:
                continue
            # Pill active style
            label.setStyleSheet(
                f"QLabel {{ background: {primary if active else 'transparent'}; "
                f"color: {primary_ink if active else text2}; "
                f"border-radius: 10px; padding: 4px 14px; "
                f"font-size: 11px; font-weight: 500; }}"
            )

        self._identity_name_lbl.setStyleSheet(
            f"color: {text}; background: transparent; font-size: 12px; font-weight: 500;"
        )
        self._identity_role_lbl.setStyleSheet(
            f"color: {mute}; background: transparent; font-size: 9px; text-transform: uppercase;"
        )

        # Identity avatar (ML-like circle)
        self._identity_avatar_lbl.setStyleSheet(
            f"QLabel {{ background: {qcolor_to_rgba_css(v3c('primary_soft', self._modo))}; "
            f"color: {primary}; border: 1px solid {border}; border-radius: 14px; "
            f"font-size: 11.5px; font-weight: 500; }}"
        )

    def _apply_back_btn_style(self):
        """Aplica estilo pill del botón Volver según mockup."""
        if not hasattr(self, "_btn_back"):
            return
        c = colors(self._modo)
        is_dark = "dark" in self._modo
        if is_dark:
            bg = "rgba(255,255,255,0.04)"
            border = "rgba(255,255,255,0.08)"
        else:
            bg = c["bg_elevated"]
            border = c["border"]
        self._btn_back.setStyleSheet(
            f"QPushButton {{ "
            f"color: {C('text_tertiary', self._modo)}; "
            f"background-color: {bg}; "
            f"border: 1px solid {border}; "
            f"border-radius: {RADIUS_SMALL}px; "
            f"padding: 3px 10px; "
            f"font-size: 11px; "
            f"font-weight: 500; "
            f"}} "
            f"QPushButton:hover {{ "
            f"background-color: {c['bg_elevated']}; "
            f"color: {C('text_secondary', self._modo)}; "
            f"}}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        if hasattr(self, "_logo_widget") and self._logo_widget is not None:
            self._logo_widget.set_modo(modo)
        if hasattr(self, "_user_lbl"):
            self._user_lbl.setStyleSheet(label_style(modo, "text_tertiary"))
        if hasattr(self, "_btn_back"):
            self._apply_back_btn_style()
        if hasattr(self, "_module_title_lbl"):
            self._module_title_lbl.setStyleSheet(label_style(modo, "text_primary"))
        self._apply_module_icon()
        self._apply_hud_styles()
        if hasattr(self, "_theme_lbl"):
            self._theme_lbl.setText(self._theme_label_text())
            self._theme_lbl.setStyleSheet(label_style(modo, "text_secondary"))
        self._apply_context_badge_style()
        was_blocked = self._toggle.blockSignals(True)
        self._toggle.setChecked("light" in modo)
        self._toggle.blockSignals(was_blocked)
        self._apply_theme_button_style()

    def _ensure_back_button(self):
        if hasattr(self, "_btn_back"):
            return self._btn_back
        btn = QPushButton("← Volver", self)
        btn.setFont(qfont("size_caption", bold=True))
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = self.layout()
        if layout:
            layout.insertWidget(0, btn)
        self._btn_back = btn
        self._back_btn = btn
        self._apply_back_btn_style()
        return btn

    def set_home_greeting(self, greeting: str = "", subtitle: str = "", streak: int = 0):
        """Actualiza los textos del header en modo home."""
        if hasattr(self, "_greet_lbl") and self._greet_lbl is not None:
            self._greet_lbl.setText(greeting or f"Hola, {self._username}")
        if hasattr(self, "_sub_lbl") and self._sub_lbl is not None:
            self._sub_lbl.setText(subtitle)
        if hasattr(self, "_streak_badge") and self._streak_badge is not None:
            if streak > 0:
                self._streak_badge.show()
            else:
                self._streak_badge.hide()

    def set_back_action(self, callback=None):
        btn = self._ensure_back_button() if callback else getattr(self, "_btn_back", None)
        if not btn:
            return
        try:
            btn.clicked.disconnect()
        except TypeError:
            pass
        if callback:
            btn.clicked.connect(callback)
            btn.show()
        else:
            btn.hide()

    def set_back_callback(self, callback):
        self.set_back_action(callback)

    def set_title_info(self, title: str = "", icon: str = ""):
        self.set_context_title(title, icon)


class _LogoLabel(QWidget):
    """Logo NeuroMood desde assets/LOGO.png con glow animado + sombra UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "dark_hybrid"
        self._glow_alpha_value = 0
        self.setFixedHeight(32)
        self._pixmap = None
        self._load_logo()

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(28)
        self._shadow.setOffset(0, 0)
        col = QColor(C("accent", self._modo))
        col.setAlpha(30)
        self._shadow.setColor(col)
        self.setGraphicsEffect(self._shadow)

        self._breath_anim = QPropertyAnimation(self, b"glow_alpha", self)
        self._breath_anim.setDuration(3000)
        self._breath_anim.setStartValue(0)
        self._breath_anim.setEndValue(60)
        self._breath_anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._breath_anim.setLoopCount(-1)
        self._breath_anim.start()

    def _load_logo(self):
        try:
            from shared.assets import obtener_ruta_asset, LOGO_LIGHT, LOGO_DARK

            logo_name = LOGO_LIGHT if "light" in self._modo else LOGO_DARK
            logo_path = obtener_ruta_asset(logo_name)
            if not os.path.exists(logo_path):
                logo_key = "logos-light.png" if "light" in self._modo else "logos-dark.png"
                logo_path = obtener_ruta_recurso(logo_key)
                if not os.path.exists(logo_path):
                    logo_path = obtener_ruta_recurso("LOGO.png")
            if os.path.exists(logo_path):
                self._pixmap = QPixmap(logo_path)
                self._pixmap_light = None
        except Exception:
            self._pixmap = None
            self._pixmap_light = None

    def _get_pixmap(self):
        if self._pixmap is None:
            return None
        return self._pixmap

    def _get_glow_alpha(self) -> int:
        return self._glow_alpha_value

    def _set_glow_alpha(self, value: int):
        self._glow_alpha_value = max(0, min(255, int(value)))
        self.update()

    glow_alpha = pyqtProperty(int, _get_glow_alpha, _set_glow_alpha)

    def set_modo(self, modo: str):
        old_modo = self._modo
        self._modo = norm_modo(modo)
        if old_modo != self._modo:
            self._load_logo()
        is_dark = "dark" in self._modo
        if is_dark:
            col = QColor(C("accent", self._modo))
            col.setAlpha(30)
            self._shadow.setBlurRadius(8)
        else:
            col = QColor(15, 23, 42, 26)  # rgba(15,23,42,.10) — spec light logo shadow
            self._shadow.setBlurRadius(4)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(col)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(140, 32)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Double glow in dark mode: violet radial halo behind logo
        if "dark" in self._modo and self._glow_alpha_value > 0:
            violet_alpha = int(self._glow_alpha_value * 0.6)
            vglow = radial_glow(
                QPointF(self.width() / 2, self.height() / 2),
                max(self.width(), self.height()) * 0.6,
                C("violet", self._modo),
                alpha=violet_alpha,
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(vglow))
            p.drawEllipse(
                QPointF(self.width() / 2, self.height() / 2),
                self.width() * 0.5,
                self.height() * 0.8,
            )

        draw_text_fallback = True
        pm = self._get_pixmap()
        if pm and not pm.isNull():
            pm_scaled = pm.scaled(
                140,
                28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            if pm_scaled and not pm_scaled.isNull():
                x = (self.width() - pm_scaled.width()) // 2
                y = (self.height() - pm_scaled.height()) // 2
                p.drawPixmap(x, y, pm_scaled)
                draw_text_fallback = False

        if draw_text_fallback:
            c = colors(self._modo)
            font_bold = qfont("size_body", bold=True)
            p.setFont(font_bold)
            fm = QFontMetrics(font_bold)
            p.setPen(QColor(c["text_primary"]))
            p.drawText(0, fm.ascent() + 4, "Neuro")
            w1 = fm.horizontalAdvance("Neuro")
            p.setPen(QColor(C("accent", self._modo)))
            p.drawText(w1, fm.ascent() + 4, "Mood")

        if self._glow_alpha_value > 0:
            glow = radial_glow(
                QPointF(self.width() / 2, self.height() / 2),
                max(self.width(), self.height()) * 0.7,
                C("accent", self._modo),
                alpha=self._glow_alpha_value,
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(
                QPointF(self.width() / 2, self.height() / 2),
                self.width() * 0.45,
                self.height() * 0.7,
            )
        p.end()


# ── NMModule (base class Qt) ──────────────────────────────────────────────────


class NMModule(ThemeAwareWidgetMixin, QWidget):
    """
    Clase base para módulos de la plataforma paciente en PyQt6.
    Preserva exactamente el mismo contrato que la versión CTk:
      - MODULE_TITLE, MODULE_ICON
      - build_ui() → raise NotImplementedError
      - get_card_status() → str
      - on_enter(), on_leave() — hooks
    """

    MODULE_TITLE: str = ""
    MODULE_ICON: str = ""

    # Señal que los módulos emiten cuando quieren volver al home
    back_requested = pyqtSignal()

    def __init__(self, parent=None, modo: str = None, show_header: bool = True):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._show_header = show_header
        self._session = SessionColor.instance()

        # Layout vertical: header + contenido
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        if self._show_header:
            self._header = NMHeader(
                self,
                modo=self._modo,
                show_back=True,
                module_title=self.MODULE_TITLE,
                module_icon=self.MODULE_ICON,
            )
            self._header.set_back_callback(self.back_requested.emit)
            self._root_layout.addWidget(self._header)

        # Contenido del modulo (build_ui lo llena) con centrado UI
        self._content = QWidget()
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Runtime spec §2: opaque background para que el stacked widget no
        # muestre contenido anterior a través del módulo activo.
        self._content.setAutoFillBackground(True)
        _surf = v3c("surface", self._modo)
        _pal = QPalette()
        _pal.setColor(QPalette.ColorRole.Window, _surf)
        self._content.setPalette(_pal)
        self._apply_content_bg()

        # Wrapper centrado para pantallas anchas (>1100px el contenido se centra)
        self._content_wrapper = QHBoxLayout()
        self._content_wrapper.setContentsMargins(0, 0, 0, 0)
        self._content_wrapper.addWidget(self._content)
        self._root_layout.addLayout(self._content_wrapper)

        self._connect_theme()
        self.build_ui()

    def _apply_content_bg(self):
        self._content.update()

    def paintEvent(self, event):
        """Aura radial dinámica de fondo."""
        super().paintEvent(event)

    @property
    def modo(self) -> str:
        return self._modo

    def build_ui(self):
        raise NotImplementedError(f"{self.__class__.__name__} debe implementar build_ui()")

    def get_card_status(self) -> str:
        """Estado resumido del módulo para mostrar en la card del home."""
        return ""

    def on_enter(self):
        """Llamado cuando el módulo se hace visible (recargar datos frescos)."""
        pass

    def on_leave(self):
        """Llamado antes de que el módulo sea ocultado (detener timers, etc.)."""
        pass

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_content_bg()

    def _apply_theme(self, modo: str):
        self._on_theme(modo)








# ── NMMoodEmoji ───────────────────────────────────────────────────────────────

try:
    from shared.icons_svg import nm_mood_pixmap as _nm_mood_pixmap
except ImportError:
    try:
        from icons_svg import nm_mood_pixmap as _nm_mood_pixmap  # type: ignore
    except ImportError:
        _nm_mood_pixmap = None


class NMMoodEmoji(QLabel):
    """Emoji de mood v3 — 10 niveles, SVG line-style.

    Spec del README (sección "Mood emoji system"):
      - Círculo de línea del color ``palette[lv]['to']``, sin relleno.
      - Ojos (2 círculos), boca curva (path varía con nivel).
      - Cejas inclinadas en niveles 1-3 y 9-10.
      - Lágrimas en 1-2, blush en 7-10, sparkles en 9-10 (+ corona en 10).
      - Halo radial opcional detrás (más fuerte en dark: 0.22 vs 0.15).

    El emoji es **100% SVG inline** — no usa Apple Color Emoji ni Unicode,
    coherente con el lenguaje visual del resto de iconos v3.

    Args:
        level: 1-10 (se clampa).
        size:  lado en px.
        glow:  halo radial detrás (default True).
        modo:  override de tema; afecta intensidad del halo.
    """

    def __init__(
        self, level: int = 5, size: int = 64, glow: bool = True, modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._size = size
        self._glow = bool(glow)
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._render()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API ──────────────────────────────────────────────────────────────────

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level:
            self._level = lv
            self._render()

    def level(self) -> int:
        return self._level

    def set_size(self, size: int):
        if size != self._size:
            self._size = size
            self.setFixedSize(size, size)
            self._render()

    def set_glow(self, glow: bool):
        if bool(glow) != self._glow:
            self._glow = bool(glow)
            self._render()

    # ── render ───────────────────────────────────────────────────────────────

    def _render(self):
        if _nm_mood_pixmap is None:
            return
        is_dark = "dark" in self._modo
        pix = _nm_mood_pixmap(self._level, self._size, glow=self._glow, is_dark=is_dark)
        if pix is not None and not pix.isNull():
            self.setPixmap(pix)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._render()



# ── NMEmojiPicker ─────────────────────────────────────────────────────────────


class NMEmojiPicker(QWidget):
    """5 botones circulares de emoji para selección de estado de ánimo (1-10).

    Emite picked(int) con el puntaje seleccionado. Las etiquetas aparecen
    debajo de la fila de botones, no sobre ellos.
    """

    picked = pyqtSignal(int)

    _CHIPS = [
        ("\U0001f61e", "Muy bajo", 1),
        ("\U0001f615", "Bajo", 3),
        ("\U0001f610", "Neutro", 5),
        ("\U0001f642", "Bien", 7),
        ("\U0001f604", "Excelente", 9),
    ]

    _BTN_SIZE = 48

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected: int | None = None
        self._btns: list[QPushButton] = []
        self._labels: list[QLabel] = []
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(sp("sm"))

        for i, (emoji, label, score) in enumerate(self._CHIPS):
            btn = QPushButton(emoji)
            btn.setFixedSize(self._BTN_SIZE, self._BTN_SIZE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, idx=i, sc=score: self._select(idx, sc))
            btn_row.addWidget(btn)
            self._btns.append(btn)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        lbl_row = QHBoxLayout()
        lbl_row.setContentsMargins(0, 0, 0, 0)
        lbl_row.setSpacing(sp("sm"))

        for _, label, _ in self._CHIPS:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(self._BTN_SIZE)
            lbl_row.addWidget(lbl)
            self._labels.append(lbl)

        lbl_row.addStretch()
        outer.addLayout(lbl_row)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _select(self, idx: int, score: int):
        self._selected = idx
        self._apply_theme(self._modo)
        self.picked.emit(score)

    def selected_score(self) -> int | None:
        return self._CHIPS[self._selected][2] if self._selected is not None else None

    def set_score(self, score: int):
        for i, (_, _, sc) in enumerate(self._CHIPS):
            if score <= sc + 1:
                self._selected = i
                break
        self._apply_theme(self._modo)

    def reset(self):
        self._selected = None
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        teal = C("teal", self._modo)
        border = C("border", self._modo)
        bg_el = C("bg_elevated", self._modo)
        bg_ov = C("bg_overlay", self._modo)
        txt_s = C("text_secondary", self._modo)
        r = self._BTN_SIZE // 2

        for i, (btn, lbl) in enumerate(zip(self._btns, self._labels)):
            is_sel = i == self._selected
            if is_sel:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: 2px solid {teal};
                        border-radius: {r}px;
                        font-size: 18px;
                    }}
                    QPushButton:hover {{ background: {bg_ov}; }}
                """)
                lbl.setStyleSheet(
                    f"color: {teal}; font-weight: 500; font-size: {TYPOGRAPHY['size_caption']}px;"
                )
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg_el};
                        border: 1px solid {border};
                        border-radius: {r}px;
                        font-size: 17px;
                    }}
                    QPushButton:hover {{
                        background: {bg_ov};
                        border-color: {teal};
                    }}
                """)
                lbl.setStyleSheet(f"color: {txt_s}; font-size: {TYPOGRAPHY['size_caption']}px;")














# ── NMFeaturedCard ────────────────────────────────────────────────────────────

_PATIENT_AVATAR_PAIRS = [
    ("accent", "teal"),
    ("teal", "violet"),
    ("violet", "accent"),
    ("accent", "violet"),
]


class NMPatientRow(QFrame):
    """Fila de paciente del Hub con avatar e indicador de adherencia."""

    clicked = pyqtSignal()

    def __init__(
        self,
        name: str,
        subtitle: str = "",
        initials: str = "",
        pct: float = 0.0,
        selected: bool = False,
        tags: list[str] | None = None,
        last_activity: str = "",
        next_session: str = "",
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = selected
        self._tags = tags or []
        self._last_activity = last_activity
        self._next_session = next_session
        self._name_hash = sum(ord(c) for c in (name or "?")) % len(_PATIENT_AVATAR_PAIRS)
        self.setObjectName("NMPatientRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(74)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        self._avatar = QLabel(initials or "".join(part[:1] for part in name.split()[:2]).upper())
        self._avatar.setFixedSize(38, 38)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._avatar)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self._name = QLabel(name)
        self._name.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle = QLabel(subtitle)
        self._subtitle.setFont(qfont("size_caption"))
        text_col.addWidget(self._name)
        text_col.addWidget(self._subtitle)
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)
        self._tag_labels: list[QLabel] = []
        for tag in self._tags[:3]:
            lbl = QLabel(tag)
            lbl.setFont(qfont("size_caption"))
            lbl.setContentsMargins(7, 2, 7, 2)
            self._tag_labels.append(lbl)
            meta_row.addWidget(lbl)
        self._last_lbl = QLabel(self._last_activity)
        self._last_lbl.setFont(qfont("size_caption"))
        self._next_lbl = QLabel(self._next_session)
        self._next_lbl.setFont(qfont("size_caption"))
        if self._last_activity:
            meta_row.addWidget(self._last_lbl)
        if self._next_session:
            meta_row.addWidget(self._next_lbl)
        meta_row.addStretch()
        text_col.addLayout(meta_row)
        lay.addLayout(text_col, stretch=1)
        # Ring 40px: tamaño suficiente para mostrar "85%" sin recorte
        self._ring = NMModuleRing(size=46, pct=pct, modo=self._modo)
        lay.addWidget(self._ring)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_theme(self._modo)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        if self._selected:
            bg = _rgba(v3c("accent", self._modo).name(), 0.05)
            border = _rgba(v3c("accent", self._modo).name(), 0.30)
        else:
            bg = v3c("elevated", self._modo).name()
            border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        self.setStyleSheet(
            f"QFrame#NMPatientRow {{ background: {bg}; border: 1px solid {border}; "
            f"border-radius: 14px; }}"
        )
        k1, k2 = _PATIENT_AVATAR_PAIRS[self._name_hash]
        self._avatar.setStyleSheet(
            f"QLabel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {C(k1, self._modo)}, stop:1 {C(k2, self._modo)}); "
            f"color: white; border-radius: 19px; "
            f"border: 1px solid {_rgba('#ffffff', 0.18 if 'dark' in self._modo else 0.35)}; }}"
        )
        self._name.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        meta_col = v3c("ink_secondary", self._modo).name()
        for lbl in (self._last_lbl, self._next_lbl):
            lbl.setStyleSheet(f"color: {meta_col}; background: transparent;")
        accent = v3c("accent", self._modo)
        tag_bg = f"rgba({accent.red()},{accent.green()},{accent.blue()},34)"
        for lbl in self._tag_labels:
            lbl.setStyleSheet(
                f"color: {v3c('accent', self._modo).name()}; "
                f"background: {tag_bg}; border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                "border-radius: 8px;"
            )


class NMSparkline(QWidget):
    """Inline sparkline — polyline for up to N data points (mood 7d, etc.).

    • Fixed size (default 90×28).
    • None / 0 values treated as gaps (segment breaks).
    • Color auto-selects `danger` token when last value drops ≥2 vs first
      (descending trend), otherwise uses `primary` token.
    """

    def __init__(
        self,
        data: list | None = None,
        color: str | None = None,
        w: int = 90,
        h: int = 28,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._data: list = list(data) if data else []
        self._color = color
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(w, h)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        _tm().theme_changed.connect(self._on_theme)

    def set_data(self, data: list, color: str | None = None):
        self._data = list(data)
        if color is not None:
            self._color = color
        self.update()

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event: QPaintEvent):  # noqa: N802
        valid = [(i, float(v)) for i, v in enumerate(self._data) if v is not None and float(v) > 0]
        if len(valid) < 2:
            return

        vals = [v for _, v in valid]
        trend_down = len(vals) >= 2 and (vals[-1] - vals[0]) <= -2
        if self._color:
            stroke = QColor(self._color)
        elif trend_down:
            stroke = v3c("danger", self._modo)
        else:
            stroke = v3c("primary", self._modo)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pw, ph = self.width(), self.height()
        pad = 3
        eff_w = pw - pad * 2
        eff_h = ph - pad * 2
        n_total = max(len(self._data), 1)
        mn, mx = min(vals), max(vals)
        span = (mx - mn) if mx > mn else 1.0

        def _xy(idx: int, val: float) -> tuple:
            x = pad + idx * eff_w / max(n_total - 1, 1)
            y = pad + eff_h - (val - mn) / span * eff_h
            return x, y

        pen = QPen(stroke)
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        first = True
        for idx, val in valid:
            x, y = _xy(idx, val)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
        painter.drawPath(path)

        last_x, last_y = _xy(valid[-1][0], valid[-1][1])
        dot = QColor(stroke)
        dot.setAlpha(200)
        painter.setBrush(dot)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(last_x, last_y), 2.5, 2.5)
        painter.end()


class NMAreaSparkline(QWidget):
    """Area sparkline grande para la card de animo del Hub Dashboard (capture 03).

    A diferencia de :class:`NMSparkline` (polyline inline 90x28), este pinta:
      - area rellena con gradiente teal que se desvanece hacia abajo;
      - linea con marcadores circulares en cada punto;
      - area suave sin guias tecnicas punteadas;
      - etiquetas de eje X (dias) debajo del grafico.

    Ancho expansible, alto compacto para no romper la politica fit-first.
    """

    def __init__(
        self,
        data: list | None = None,
        labels: list[str] | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._data: list[float] = [float(v) for v in (data or [])]
        self._labels: list[str] = list(labels) if labels else []
        self._modo = norm_modo(modo or _tm().modo)
        self.setMinimumHeight(74)
        self.setMaximumHeight(82)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        _tm().theme_changed.connect(self._on_theme)

    def set_series(self, data: list, labels: list[str] | None = None):
        self._data = [float(v) for v in (data or [])]
        if labels is not None:
            self._labels = list(labels)
        self.update()

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event: QPaintEvent):  # noqa: N802
        if len(self._data) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        stroke = v3c("teal", self._modo)
        axis_c = v3c("mute", self._modo)
        pw, ph = self.width(), self.height()

        axis_h = 16 if self._labels else 0
        pad_x = 4
        top_pad = 6
        plot_h = ph - axis_h - top_pad
        eff_w = pw - pad_x * 2

        vals = self._data
        n = len(vals)
        mn, mx = min(vals), max(vals)
        # Margen vertical para que picos/valles no toquen los bordes.
        span = (mx - mn) if mx > mn else 1.0
        lo = mn - span * 0.25
        hi = mx + span * 0.25
        vspan = hi - lo

        def _xy(idx: int, val: float) -> tuple[float, float]:
            x = pad_x + idx * eff_w / max(n - 1, 1)
            y = top_pad + plot_h - (val - lo) / vspan * plot_h
            return x, y

        pts = [_xy(i, v) for i, v in enumerate(vals)]

        # Area rellena con gradiente que se desvanece hacia la baseline.
        area = QPainterPath()
        area.moveTo(pts[0][0], top_pad + plot_h)
        for x, y in pts:
            area.lineTo(x, y)
        area.lineTo(pts[-1][0], top_pad + plot_h)
        area.closeSubpath()
        grad = QLinearGradient(0, top_pad, 0, top_pad + plot_h)
        top_c = QColor(stroke)
        top_c.setAlpha(70)
        bot_c = QColor(stroke)
        bot_c.setAlpha(0)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawPath(area)

        # Linea principal.
        line = QPainterPath()
        line.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            line.lineTo(x, y)
        line_pen = QPen(QColor(stroke))
        line_pen.setWidthF(2.0)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line)

        # Marcadores circulares (relleno = surface, borde = stroke).
        surface_c = QColor(colors(self._modo)["bg_surface"])
        for x, y in pts:
            painter.setPen(QPen(QColor(stroke), 1.6))
            painter.setBrush(surface_c)
            painter.drawEllipse(QPointF(x, y), 3.0, 3.0)

        # Etiquetas de eje X (dias).
        if self._labels:
            painter.setPen(QColor(axis_c))
            f = qfont("size_caption_xs")
            painter.setFont(f)
            label_y = ph - axis_h
            n_lab = len(self._labels)
            for i, lab in enumerate(self._labels):
                cx = pad_x + i * eff_w / max(n_lab - 1, 1)
                painter.drawText(
                    QRectF(cx - 14, label_y, 28, axis_h),
                    Qt.AlignmentFlag.AlignCenter,
                    lab,
                )
        painter.end()


class NMPatientRowPremium(QFrame):
    """Dense Hub patient row with avatar, metadata, chips, sync and ring."""

    clicked = pyqtSignal()

    _SYNC_TO_KEY = {
        "ok": "success",
        "syncing": "warning",
        "stale": "warning",
        "error": "error",
    }

    def __init__(
        self,
        name: str,
        patient_id: str = "",
        subtitle: str = "",
        last_activity: str = "",
        next_session: str = "",
        tags: list[str] | None = None,
        sync_state: str = "ok",
        pct: float = 0.0,
        mood_data: list | None = None,
        selected: bool = False,
        modo: str = None,
        on_unlink=None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = selected
        self._sync_state = sync_state if sync_state in self._SYNC_TO_KEY else "ok"
        self._full_name = name or "-"
        self._full_last_activity = last_activity or patient_id or "Sin registros recientes"
        self._full_subtitle = subtitle or "Sin programa vinculado"
        self._full_next_session = next_session or self._sync_copy()
        self._name_hash = sum(ord(c) for c in (name or "?")) % len(_PATIENT_AVATAR_PAIRS)
        self.setObjectName("NMPatientRowPremium")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(58)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 7, 14, 7)
        lay.setSpacing(12)

        # Status dot
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(10, 10)
        self._status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        # Avatar circular initials (28x28 px)
        initials = "".join(part[:1] for part in (name or "?").split()[:2]).upper()
        self._avatar = QLabel(initials or "P")
        self._avatar.setFixedSize(28, 28)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        # Patient identity column
        patient_col = QVBoxLayout()
        patient_col.setContentsMargins(0, 0, 0, 0)
        patient_col.setSpacing(1)
        self._name = QLabel(self._full_name)
        self._name.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._name.setToolTip(self._full_name)
        self._name.setMinimumWidth(150)
        patient_col.addWidget(self._name)

        self._activity_lbl = QLabel(self._full_last_activity)
        self._activity_lbl.setFont(qfont("size_caption_xs"))
        self._activity_lbl.setToolTip(self._full_last_activity)
        patient_col.addWidget(self._activity_lbl)
        lay.addLayout(patient_col, stretch=3)

        # Program / context column
        program_col = QVBoxLayout()
        program_col.setContentsMargins(0, 0, 0, 0)
        program_col.setSpacing(1)
        self._subtitle_lbl = QLabel(self._full_subtitle)
        self._subtitle_lbl.setFont(qfont("size_caption_xs"))
        self._subtitle_lbl.setToolTip(self._full_subtitle)
        program_col.addWidget(self._subtitle_lbl)

        self._context_lbl = QLabel(self._full_next_session)
        self._context_lbl.setFont(qfont("size_caption_xs"))
        self._context_lbl.setToolTip(self._full_next_session)
        program_col.addWidget(self._context_lbl)
        lay.addLayout(program_col, stretch=2)

        # Sparkline
        self._sparkline = None
        if mood_data:
            self._sparkline = NMSparkline(data=mood_data, modo=self._modo)
            self._sparkline.setFixedSize(64, 22)
            lay.addWidget(self._sparkline, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            lay.addSpacing(64)

        # Adherence ring — en columna fija de 56px para alinear con el header
        # "USO" y dejar aire respecto del borde derecho. 30px: con 26 el
        # porcentaje interior quedaba comprimido contra el anillo.
        self._ring = NMModuleRing(size=30, pct=pct, modo=self._modo)
        _ring_wrap = QWidget()
        _ring_wrap.setFixedWidth(56)
        _ring_wl = QHBoxLayout(_ring_wrap)
        _ring_wl.setContentsMargins(0, 0, 0, 0)
        _ring_wl.addWidget(self._ring, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(_ring_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        # X discreta para quitar al paciente del Hub (decisión user feedback:
        # pacientes que dejan el tratamiento no deben acumularse en la lista).
        # Botón hijo: consume su propio click, no dispara el clicked de la fila.
        self._btn_unlink = None
        if on_unlink is not None:
            self._btn_unlink = QToolButton()
            self._btn_unlink.setObjectName("NMRowUnlink")
            self._btn_unlink.setFixedSize(26, 26)
            self._btn_unlink.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_unlink.setToolTip("Quitar paciente del Hub")
            self._btn_unlink.setAccessibleName(f"Quitar a {self._full_name} del Hub")
            self._btn_unlink.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._btn_unlink.clicked.connect(on_unlink)
            lay.addWidget(self._btn_unlink, 0, Qt.AlignmentFlag.AlignVCenter)

        # Compatibility widgets created but hidden to avoid crashes
        self._pid = QLabel(patient_id)
        self._subtitle = QLabel(subtitle)
        self._sync = QLabel("Sync")

        self._apply_theme(self._modo)
        QTimer.singleShot(0, self._refresh_name_text)
        QTimer.singleShot(0, self._refresh_activity_text)
        QTimer.singleShot(0, self._refresh_subtitle_text)
        QTimer.singleShot(0, self._refresh_context_text)
        _tm().theme_changed.connect(self._apply_theme)

    def _sync_copy(self) -> str:
        return {
            "ok": "Sincronización reciente",
            "syncing": "Sincronizando",
            "stale": "Sin sincronización reciente",
            "error": "Error de sincronización",
        }.get(self._sync_state, "Sincronización reciente")

    def _chip(self, text: str, tone_key: str) -> QLabel:
        chip = QLabel(text)
        chip.setProperty("tone_key", tone_key)
        chip.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setMinimumHeight(18)
        chip.setContentsMargins(6, 1, 6, 1)
        return chip

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_theme(self._modo)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_name_text()
        self._refresh_activity_text()
        self._refresh_subtitle_text()
        self._refresh_context_text()

    def _fit_label(self, label: QLabel, text: str, minimum: int = 72):
        width = max(minimum, label.width() - 4)
        metrics = QFontMetrics(label.font())
        label.setText(metrics.elidedText(text, Qt.TextElideMode.ElideRight, width))

    def _refresh_subtitle_text(self):
        if hasattr(self, "_subtitle_lbl"):
            self._fit_label(self._subtitle_lbl, self._full_subtitle, minimum=88)

    def _refresh_name_text(self):
        if hasattr(self, "_name"):
            self._fit_label(self._name, self._full_name, minimum=96)

    def _refresh_activity_text(self):
        if hasattr(self, "_activity_lbl"):
            self._fit_label(self._activity_lbl, self._full_last_activity, minimum=110)

    def _refresh_context_text(self):
        if hasattr(self, "_context_lbl"):
            self._fit_label(self._context_lbl, self._full_next_session, minimum=94)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg_key = "surfaceSolid" if is_dark else "surface"
        bg = (
            _rgba(v3c("accent", self._modo).name(), 0.08)
            if self._selected
            else v3c(bg_key, self._modo).name()
        )
        border = (
            _rgba(C("accent", self._modo), 0.38)
            if self._selected
            else qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        )
        hover_bg = _rgba(C("teal", self._modo), 0.07 if is_dark else 0.05)
        self.setStyleSheet(
            f"QFrame#NMPatientRowPremium {{ background: {bg}; border: 1px solid {border}; "
            f"border-left: 3px solid {C('accent', self._modo) if self._selected else border}; "
            f"border-radius: 12px; }}"
            f"QFrame#NMPatientRowPremium:hover {{ background: {hover_bg}; "
            f"border-color: {_rgba(C('teal', self._modo), 0.42)}; }}"
        )
        k1, k2 = _PATIENT_AVATAR_PAIRS[self._name_hash]
        self._avatar.setStyleSheet(
            f"QLabel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {C(k1, self._modo)}, stop:1 {C(k2, self._modo)}); "
            f"color: white; border-radius: 12px; "
            f"border: 1px solid {_rgba('#ffffff', 0.22 if is_dark else 0.42)}; }}"
        )
        self._name.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._activity_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._subtitle_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._context_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._pid.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )
        if self._sparkline is not None:
            self._sparkline._on_theme(self._modo)

        if self._btn_unlink is not None:
            _ink = v3c("ink_secondary", self._modo).name()
            self._btn_unlink.setIcon(nm_icon("close", _ink, size=13))
            self._btn_unlink.setIconSize(QSize(13, 13))
            self._btn_unlink.setStyleSheet(
                "QToolButton#NMRowUnlink { background: transparent; border: none; "
                "border-radius: 13px; }"
                f"QToolButton#NMRowUnlink:hover {{ "
                f"background: {_rgba(C('danger', self._modo), 0.14)}; }}"
            )

        # Status dot color based on sync state
        dot_color = v3c(self._SYNC_TO_KEY.get(self._sync_state, "ok"), self._modo).name()
        self._status_dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 5px;"
        )

        for chip in self.findChildren(QLabel):
            tone_key = chip.property("tone_key")
            if not tone_key:
                continue
            col = QColor(C(str(tone_key), self._modo))
            bgc = QColor(col)
            bgc.setAlpha(34 if is_dark else 26)
            brd = QColor(col)
            brd.setAlpha(68 if is_dark else 48)
            chip.setStyleSheet(
                f"color: {col.name()}; background: rgba({bgc.red()},{bgc.green()},{bgc.blue()},{bgc.alpha()}); "
                f"border: 1px solid rgba({brd.red()},{brd.green()},{brd.blue()},{brd.alpha()}); "
                f"border-radius: 10px; padding: 3px 8px;"
            )


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


class NMMoodSlider(QFrame):
    """Slider de estado de ánimo 1-10 con empty state inicial (F1.6).

    Estado INICIAL (null):
    - Track neutral (sin fill de color)
    - Thumb oculto / transparente
    - Display "-- /10"
    - Label "Sin registro"
    - Helper "¿Cómo te sientes hoy?"

    PRIMERA INTERACCIÓN:
    - Revela thumb con opacity 1
    - Track fill usa MOOD_PALETTE según valor seleccionado
    - Display muestra valor numérico (ej: "7 /10")

    Signals:
        value_changed(int): emitido cuando se selecciona valor 1-10
        cleared():          emitido cuando se limpia el slider al estado null
    """

    value_changed = pyqtSignal(int)
    cleared = pyqtSignal()

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._has_value = False  # null state por defecto
        self.setObjectName("NMMoodSlider")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── Layout principal ──
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["sm"])

        # ── Label de estado ──
        self._state_label = QLabel("Sin registro")
        self._state_label.setFont(v3_font("size_caption", weight=TYPOGRAPHY["weight_medium"]))
        lay.addWidget(self._state_label)

        # ── Slider row ──
        slider_row = QHBoxLayout()
        slider_row.setSpacing(V3_SP["md"])
        slider_row.setContentsMargins(0, 0, 0, 0)

        # QSlider: range 1-10, sin setValue() al inicio → null state
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 10)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(1)
        self._slider.setObjectName("MoodSliderInternal")
        self._slider.valueChanged.connect(self._on_value_changed)
        self._slider.sliderPressed.connect(self._on_first_interaction)
        slider_row.addWidget(self._slider, stretch=1)

        # Display numérico
        self._display = QLabel("-- /10")
        self._display.setFont(v3_font("size_heading_m", weight=TYPOGRAPHY["weight_semibold"]))
        self._display.setMinimumWidth(60)
        self._display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_row.addWidget(self._display)

        lay.addLayout(slider_row)

        # ── Helper text ──
        self._helper = QLabel("¿Cómo te sientes hoy?")
        self._helper.setFont(v3_font("size_caption_xs", weight=TYPOGRAPHY["weight_regular"]))
        lay.addWidget(self._helper)

        # Opacity effect para transición suave del thumb
        self._opacity_effect = QGraphicsOpacityEffect(self._slider)
        self._opacity_effect.setOpacity(0.0)  # thumb oculto en estado null
        self._slider.setGraphicsEffect(self._opacity_effect)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _on_first_interaction(self):
        """Primera interacción con el slider: revela thumb progresivamente."""
        if not self._has_value:
            self._has_value = True
            self._animate_thumb_reveal()

    def _animate_thumb_reveal(self):
        """Transición suave de opacity 0 → 1 para el thumb."""
        self._thumb_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._thumb_anim.setDuration(180)
        self._thumb_anim.setStartValue(0.0)
        self._thumb_anim.setEndValue(1.0)
        self._thumb_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._thumb_anim.start()
        self._thumb_anim.finished.connect(self._update_stylesheet)

    def _on_value_changed(self, value: int):
        """Handler interno de valueChanged del QSlider."""
        if self._slider.hasMouse():
            self._apply_theme(self._modo)
        self.value_changed.emit(value)

    def _update_stylesheet(self):
        """Refresca el QSS del slider tras animación."""
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)

        # Colores del tema
        text_primary = v3c("text", self._modo)
        text_secondary = v3c("text2", self._modo)
        surface = v3c("surface", self._modo)
        surface2 = v3c("surface2", self._modo)
        v3c("line", self._modo)

        # Track neutral (sin fill cuando null)
        track_inactive = QColor(surface2)
        track_inactive.setAlpha(100)

        if self._has_value and self._slider.value() > 0:
            # Track fill con color del mood palette
            mood = get_mood(self._slider.value())
            track_fill = QColor(mood["from"])
            track_fill.setAlpha(180)
            thumb_color = mood["from"]
        else:
            # Estado null: sin fill
            track_fill = QColor(surface2)
            track_fill.setAlpha(0)
            thumb_color = QColor(text_secondary).name()

        # Slider QSS
        self._slider.setStyleSheet(f"""
            QSlider#MoodSliderInternal {{
                background: transparent;
            }}
            QSlider#MoodSliderInternal::groove:horizontal {{
                border: none;
                height: 6px;
                background: rgba({track_inactive.red()},{track_inactive.green()},{track_inactive.blue()},{track_inactive.alpha()});
                border-radius: 3px;
                margin: 10px 0;
            }}
            QSlider#MoodSliderInternal::groove:horizontal::sub-page {{
                background: rgba({track_fill.red()},{track_fill.green()},{track_fill.blue()},{track_fill.alpha()});
                border-radius: 3px;
            }}
            QSlider#MoodSliderInternal::handle:horizontal {{
                background: {thumb_color};
                border: 2px solid {surface};
                width: 20px;
                height: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }}
        """)

        # Label de estado
        self._state_label.setStyleSheet(f"color: {text_secondary.name()}; background: transparent;")
        self._display.setStyleSheet(f"color: {text_primary.name()}; background: transparent;")
        self._helper.setStyleSheet(
            f"color: {text_secondary.name()}; background: transparent; opacity: 0.7;"
        )

    def set_value(self, value: int | None):
        """Establece el valor del slider (1-10) o None para estado vacío."""
        if value is None:
            self._has_value = False
            self._slider.setValue(1)  # reset al mínimo internamente
            self._opacity_effect.setOpacity(0.0)
            self._display.setText("-- /10")
            self._state_label.setText("Sin registro")
            self._apply_theme(self._modo)
        else:
            clamped = max(1, min(10, int(value)))
            self._slider.setValue(clamped)
            if not self._has_value:
                self._has_value = True
                self._opacity_effect.setOpacity(1.0)
            self._display.setText(f"{clamped} /10")
            self._state_label.setText(get_mood(clamped)["name"])
            self._apply_theme(self._modo)

    def get_value(self) -> int | None:
        """Devuelve el valor actual (1-10) o None si está vacío."""
        return self._slider.value() if self._has_value else None

    def clear(self):
        """Limpia el slider al estado null inicial."""
        self._has_value = False
        self._slider.setValue(1)
        self._opacity_effect.setOpacity(0.0)
        self._display.setText("-- /10")
        self._state_label.setText("Sin registro")
        self._apply_theme(self._modo)
        self.cleared.emit()


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
# V3MoodSlider + NMPlayButton — componentes nuevos v3 (aditivos)
# ══════════════════════════════════════════════════════════════════════════════

# ── helpers privados para clicks tipados ──────────────────────────────────────


class _MoodPickWidget(QWidget):
    """Widget interno que emite ``picked(int)`` al hacer click izquierdo."""

    picked = pyqtSignal(int)

    def __init__(self, value: int, parent=None):
        super().__init__(parent)
        self._value = value
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._value)
        super().mousePressEvent(event)


class _MoodPickLabel(QLabel):
    """QLabel que emite ``picked(int)`` al hacer click izquierdo."""

    picked = pyqtSignal(int)

    def __init__(self, text: str, value: int, parent=None):
        super().__init__(text, parent)
        self._value = value
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._value)
        super().mousePressEvent(event)


# ── _MoodTrackBar (subcomponente del V3MoodSlider) ───────────────────────────


class _MoodNumRow(QWidget):
    """Fila de números 0-10 posicionados EXACTAMENTE bajo los slots del track.

    Usa la misma fórmula que ``_MoodTrackBar._slot_positions`` (margen 16 +
    i/10 del ancho útil). Con el layout anterior de stretches, el centro de
    cada número quedaba ~10px corrido del dot real del slider (informe user feedback
    v1.0, módulo Ánimo).
    """

    def __init__(self, labels: list[QLabel], parent=None):
        super().__init__(parent)
        self._labels = labels
        self.setFixedHeight(20)
        for lbl in labels:
            lbl.setParent(self)
            lbl.setFixedSize(24, 20)

    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        margin = 16
        span = max(0, self.width() - 2 * margin)
        for i, lbl in enumerate(self._labels):
            x = margin + (i / 10) * span
            lbl.move(int(x - lbl.width() / 2), 0)


class _MoodTrackBar(QWidget):
    """Track horizontal con gradient arcoíris emocional + 10 dots clickeables.

    El gradient NO varía con el theme (paleta emocional fija, ver README v3).
    El dot activo: 16x16 blanco con border 3px del color del nivel + halo.
    Dots inactivos: 6x6 semi-transparentes.
    """

    level_clicked = pyqtSignal(int)

    # 7-stop rainbow emocional (literal del README v3)
    _RAINBOW_STOPS = (
        ("#5b6cb8", 0.00),
        ("#7ba8e6", 0.22),
        ("#f5d76a", 0.50),
        ("#5dd6a3", 0.70),
        ("#36cfb8", 0.80),
        ("#a78bfa", 0.95),
        ("#ec4899", 1.00),
    )

    def __init__(self, level: int = 5, parent=None, unset: bool = False):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        # Muesca 0 (feedback user feedback): el thumb arranca ESTACIONADO en un
        # 0 visual que NO es un valor registrable — al primer click/drag se
        # mueve a 1-10 y deja de estar unset. El 0 no responde a clicks.
        self._unset = bool(unset)
        self.setFixedHeight(56)
        self.setMinimumWidth(280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level or self._unset:
            self._level = lv
            self._unset = False
            self.update()

    def level(self) -> int:
        return self._level

    def set_unset(self, unset: bool = True):
        self._unset = bool(unset)
        self.update()

    def is_unset(self) -> bool:
        return self._unset

    def _slot_positions(self) -> list[float]:
        """11 slots equiespaciados: índice 0 = muesca de estacionamiento,
        índices 1-10 = niveles registrables."""
        margin_x = 16
        w = self.width() - 2 * margin_x
        return [margin_x + (i / 10) * w for i in range(11)]

    def _dot_positions(self) -> list[float]:
        return self._slot_positions()[1:]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        bar_y = h // 2 - 4
        bar_h = 8
        margin_x = 16
        bar_w = self.width() - 2 * margin_x
        bar_rect = QRectF(margin_x, bar_y, bar_w, bar_h)

        # Track con gradient rainbow (opacity .85 según JSX)
        grad = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
        for hex_c, pos in self._RAINBOW_STOPS:
            grad.setColorAt(pos, QColor(hex_c))
        path = QPainterPath()
        path.addRoundedRect(bar_rect, bar_h / 2, bar_h / 2)
        p.setOpacity(0.85)
        p.fillPath(path, QBrush(grad))
        p.setOpacity(1.0)

        # Muesca 0 (estacionamiento): anillo neutro sutil; el thumb descansa
        # acá mientras el paciente no eligió valor. Theme-aware: en light el
        # anillo blanco-sobre-card-clara era INVISIBLE (informe user feedback) —
        # se delinea con slate oscuro.
        _is_dark = "dark" in norm_modo(_tm().modo)
        slot0_x = self._slot_positions()[0]
        center_y = h / 2
        if self._unset:
            if _is_dark:
                ring = QColor(255, 255, 255, 120)
                halo = QColor(255, 255, 255, 18)
            else:
                ring = QColor(71, 85, 105, 150)
                halo = QColor(71, 85, 105, 18)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(halo))
            p.drawEllipse(QPointF(slot0_x, center_y), 9, 9)
            p.setBrush(QBrush(QColor("#ffffff")))
            p.setPen(QPen(ring, 2))
            p.drawEllipse(QPointF(slot0_x, center_y), 5.5, 5.5)
        else:
            _parked = (
                QColor(255, 255, 255, 110) if _is_dark else QColor(71, 85, 105, 110)
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_parked))
            p.drawEllipse(QPointF(slot0_x, center_y), 2.5, 2.5)

        # Dots (10)
        positions = self._dot_positions()
        for i, x in enumerate(positions):
            n = i + 1
            lv_color = get_mood(n)["to"]
            if n == self._level and not self._unset:
                # Halo exterior
                halo = QColor(lv_color)
                halo.setAlpha(64)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(halo))
                p.drawEllipse(QPointF(x, center_y), 14, 14)
                # Halo intermedio
                halo2 = QColor(lv_color)
                halo2.setAlpha(110)
                p.setBrush(QBrush(halo2))
                p.drawEllipse(QPointF(x, center_y), 10, 10)
                # Dot blanco con borde
                p.setBrush(QBrush(QColor("#ffffff")))
                p.setPen(QPen(QColor(lv_color), 3))
                p.drawEllipse(QPointF(x, center_y), 8, 8)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 180)))
                p.drawEllipse(QPointF(x, center_y), 3, 3)
        p.end()

    def _level_at_x(self, x: float) -> int:
        # Solo niveles 1-10: la muesca 0 es inerte (no registrable).
        positions = self._dot_positions()
        return min(range(10), key=lambda i: abs(positions[i] - x)) + 1

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x() if hasattr(event, "position") else float(event.pos().x())
            n = self._level_at_x(x)
            if n != self._level or self._unset:
                self.set_level(n)
            self.level_clicked.emit(n)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            x = event.position().x() if hasattr(event, "position") else float(event.pos().x())
            n = self._level_at_x(x)
            if n != self._level or self._unset:
                self.set_level(n)
                self.level_clicked.emit(n)
        super().mouseMoveEvent(event)


# ── V3MoodSlider ─────────────────────────────────────────────────────────────


class V3MoodSlider(QWidget):
    """Slider de mood 1-10 v3 (Suite > Mood Tracker > Slashbar 1-10).

    Composición:
      • Header: título + subtítulo + cluster derecho (eyebrow "HOY", nombre del
        nivel grande en color, "n/10" mono, emoji 104px con glow).
      • Slashbar gradient arcoíris emocional con 10 dots clickeables.
      • Fila de números 1-10 (mono); el activo coloreado del nivel.
      • Range descriptors (3 columnas: izq/centro/der).
      • Panel inferior con 10 mini emojis preview; el activo escala 1.18 + glow.

    Signal:
        level_changed(int)  emitido cada vez que cambia el nivel.
    """

    level_changed = pyqtSignal(int)

    def __init__(
        self,
        level: int = 5,
        title: str = "¿Cómo te sientes hoy?",
        subtitle: str = "Deslizá para encontrar el número que mejor describe tu estado.",
        modo: str = None,
        parent=None,
        compact: bool = False,
        unset: bool = False,
    ):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self._unset = bool(unset)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(V3_SP["xs"] if compact else V3_SP["lg"])

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(V3_SP["lg"])

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle_lbl = QLabel(subtitle)
        self._subtitle_lbl.setFont(qfont("size_small"))
        self._subtitle_lbl.setWordWrap(True)
        title_col.addWidget(self._title_lbl)
        title_col.addWidget(self._subtitle_lbl)
        title_col.addStretch()
        header.addLayout(title_col, stretch=1)

        right = QHBoxLayout()
        right.setSpacing(V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._eyebrow_lbl = QLabel("Hoy")
        self._eyebrow_lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._eyebrow_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl = QLabel("—" if self._unset else get_mood(self._level)["name"])
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl.setFont(qfont("size_display", weight=TYPOGRAPHY["weight_semibold"]))
        self._numeric_lbl = QLabel("—/10" if self._unset else f"{self._level}/10")
        self._numeric_lbl.setFont(qfont_mono(12, bold=False))
        self._numeric_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_col.addWidget(self._eyebrow_lbl)
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._numeric_lbl)
        text_col.addStretch()
        right.addLayout(text_col)

        self._emoji_big = NMMoodEmoji(level=self._level, size=104, glow=True, modo=self._modo)
        right.addWidget(self._emoji_big, alignment=Qt.AlignmentFlag.AlignVCenter)

        header.addLayout(right)
        root.addLayout(header)

        # ── Slashbar ──────────────────────────────────────────────────────────
        self._track = _MoodTrackBar(level=self._level, unset=self._unset)
        self._track.level_clicked.connect(self._on_level_clicked)
        root.addWidget(self._track)

        # ── Fila de números 0-10 (el 0 es la muesca de estacionamiento; no
        # registra valor — feedback user feedback). _MoodNumRow los posiciona
        # con la MISMA fórmula del track: cada número queda centrado bajo su
        # dot real (antes el layout de stretches los corría ~10px).
        self._num_labels: list[_MoodPickLabel] = []
        self._zero_lbl = QLabel("0")
        self._zero_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zero_lbl.setFont(qfont_mono(10))
        for n in range(1, 11):
            lbl = _MoodPickLabel(str(n), n)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.picked.connect(self._on_level_clicked)
            self._num_labels.append(lbl)
        num_row = _MoodNumRow([self._zero_lbl, *self._num_labels])
        root.addWidget(num_row)

        # ── Range descriptors ─────────────────────────────────────────────────
        desc_row = QHBoxLayout()
        desc_row.setContentsMargins(0, V3_SP["sm"], 0, 0)
        d_left = QLabel("Necesito apoyo")
        d_mid = QLabel("En el medio")
        d_mid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_right = QLabel("Me siento pleno")
        d_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        for d in (d_left, d_mid, d_right):
            d.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        desc_row.addWidget(d_left, 1)
        desc_row.addWidget(d_mid, 1)
        desc_row.addWidget(d_right, 1)
        self._desc_labels = (d_left, d_mid, d_right)
        root.addLayout(desc_row)

        # ── Panel inferior con 10 mini emojis ─────────────────────────────────
        self._preview_panel = QFrame()
        self._preview_panel.setObjectName("MoodPreviewPanel")
        prow = QHBoxLayout(self._preview_panel)
        prow.setContentsMargins(14, 16, 14, 16)
        prow.setSpacing(0)
        self._preview_cells: list[tuple[_MoodPickWidget, NMMoodEmoji, QLabel, int]] = []
        for n in range(1, 11):
            cell = _MoodPickWidget(n)
            cell.setFixedWidth(40)
            col = QVBoxLayout(cell)
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(2)
            col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            is_active = n == self._level and not self._unset
            emoji = NMMoodEmoji(
                level=n, size=(38 if is_active else 32), glow=is_active, modo=self._modo
            )
            num_lbl = QLabel(str(n))
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setFont(qfont_mono(9, bold=is_active))
            col.addWidget(emoji, alignment=Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(num_lbl)
            cell.picked.connect(self._on_level_clicked)
            self._preview_cells.append((cell, emoji, num_lbl, n))
            prow.addWidget(cell)
            if n < 10:
                prow.addStretch()
        root.addWidget(self._preview_panel)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

        if compact:
            self._subtitle_lbl.hide()
            self._emoji_big.hide()
            d_left.hide()
            d_mid.hide()
            d_right.hide()
            self._preview_panel.hide()
            self._title_lbl.hide()
            self._eyebrow_lbl.hide()
            self._name_lbl.hide()
            self._numeric_lbl.hide()

    # ── API pública ──────────────────────────────────────────────────────────

    def level(self) -> int:
        return self._level

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv == self._level and not self._unset:
            return
        self._level = lv
        self._unset = False
        self._track.set_level(lv)
        self._emoji_big.set_level(lv)
        self._name_lbl.setText(get_mood(lv)["name"])
        self._numeric_lbl.setText(f"{lv}/10")
        for cell, emoji, lbl, n in self._preview_cells:
            active = n == lv
            emoji.set_size(38 if active else 32)
            emoji.set_glow(active)
        self._refresh_styles()
        self.level_changed.emit(lv)

    def set_subtitle(self, text: str) -> None:
        """Actualiza el subtítulo (mensaje de cuidado dinámico por nivel)."""
        if hasattr(self, "_subtitle_lbl"):
            self._subtitle_lbl.setText(text)

    # ── internals ────────────────────────────────────────────────────────────

    def _on_level_clicked(self, n: int):
        self.set_level(int(n))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._refresh_styles()

    def _refresh_styles(self):
        is_dark = "dark" in self._modo
        c_text = v3c("text", self._modo).name()
        c_text2 = v3c("text2", self._modo).name()
        c_ink_secondary = v3c("ink_secondary", self._modo).name()
        c_text4 = v3c("text4", self._modo).name()
        elev_key = "elevatedSolid" if is_dark else "elevated"
        c_elev = v3c(elev_key, self._modo).name()
        c_border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        lv_color = get_mood(self._level)["to"]

        self._title_lbl.setStyleSheet(f"color: {c_text}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {c_text2}; background: transparent;")
        self._eyebrow_lbl.setStyleSheet(f"color: {c_ink_secondary}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {lv_color}; background: transparent;")
        self._numeric_lbl.setStyleSheet(f"color: {c_text2}; background: transparent;")
        for d in self._desc_labels:
            d.setStyleSheet(f"color: {c_ink_secondary}; background: transparent;")
        if hasattr(self, "_zero_lbl"):
            self._zero_lbl.setStyleSheet(f"color: {c_text4}; background: transparent;")
        for lbl in self._num_labels:
            active = lbl._value == self._level and not self._unset
            col = get_mood(lbl._value)["to"] if active else c_ink_secondary
            lbl.setFont(qfont_mono(11, bold=active))
            lbl.setStyleSheet(f"color: {col}; background: transparent;")
        for cell, emoji, num_lbl, n in self._preview_cells:
            active = n == self._level and not self._unset
            col = get_mood(n)["to"] if active else c_text4
            num_lbl.setFont(qfont_mono(9, bold=active))
            num_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._preview_panel.setStyleSheet(
            f"#MoodPreviewPanel {{ background: {c_elev}; "
            f"border: 1px solid {c_border}; border-radius: {V3_RD['lg']}px; }}"
        )



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







# ── NMDialog / NMModal ───────────────────────────────────────────────────────


class NMDialog(QWidget):
    """Modal/Dialog overlay con header, body y footer estandarizados.

    Implementado como overlay sobre la ventana padre (no QDialog nativo) para
    mantener consistencia visual con el shell. Soporta close por click en
    backdrop o tecla Escape.

    Uso:
        dlg = NMDialog(title="Confirmar acción", parent=self)
        dlg.set_body_widget(QLabel("¿Estás seguro?"))
        dlg.add_footer_button("Cancelar", role="secondary",
                              callback=dlg.close)
        dlg.add_footer_button("Eliminar", role="danger",
                              callback=self._do_delete)
        dlg.show_centered()
    """

    closed = pyqtSignal()

    def __init__(self, title: str = "", modo: str = None, width: int = 480, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._dialog_width = width
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # Overlay full-cover sobre el padre
        if parent is not None:
            self.setGeometry(parent.rect())

        # Container central
        self._panel = QFrame(self)
        self._panel.setFixedWidth(width)
        self._panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["lg"])
        panel_lay.setSpacing(V3_SP["md"])

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(V3_SP["sm"])
        self._title = QLabel(title or "")
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title.setWordWrap(True)
        header_row.addWidget(self._title, stretch=1)
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setFlat(True)
        self._close_btn.clicked.connect(self.close)
        header_row.addWidget(self._close_btn)
        panel_lay.addLayout(header_row)

        # Body container
        self._body_holder = QVBoxLayout()
        self._body_holder.setSpacing(V3_SP["md"])
        panel_lay.addLayout(self._body_holder, stretch=1)

        # Footer
        self._footer_row = QHBoxLayout()
        self._footer_row.setSpacing(V3_SP["sm"])
        self._footer_row.addStretch()
        panel_lay.addLayout(self._footer_row)
        self._footer_buttons: list[QPushButton] = []

        # Layout root para centrar el panel
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()
        center_row = QHBoxLayout()
        center_row.addStretch()
        center_row.addWidget(self._panel)
        center_row.addStretch()
        root.addLayout(center_row)
        root.addStretch()

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)
        self.hide()

    # ── API ──────────────────────────────────────────────────────────────────

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_body_widget(self, widget: QWidget):
        # Limpiar body actual
        while self._body_holder.count():
            item = self._body_holder.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._body_holder.addWidget(widget)

    def add_footer_button(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        """role: 'primary' | 'secondary' | 'danger' | 'ghost'."""
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(96)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_row.addWidget(btn)
        self._footer_buttons.append(btn)
        self._style_footer()
        return btn

    def show_centered(self):
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.setFocus(Qt.FocusReason.PopupFocusReason)

    # ── Eventos ──────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Click fuera del panel cierra
        if not self._panel.geometry().contains(event.pos()):
            self.close()
            return
        super().mousePressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    # ── Paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Backdrop semitransparente, theme-aware: en light un scrim negro duro se
        # ve roto (feedback). En dark mantenemos negro; en light usamos la tinta
        # profunda del tema a baja alpha para atenuar sin ennegrecer.
        if "dark" in self._modo:
            scrim = QColor(0, 0, 0, 150)
        else:
            ink = v3c("text", self._modo)
            scrim = QColor(ink.red(), ink.green(), ink.blue(), 90)
        p.fillRect(self.rect(), scrim)
        # El panel se pinta como QFrame con su stylesheet
        p.end()

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = C("border", self._modo)
        self._panel.setStyleSheet(
            f"QFrame {{ background-color: {bg}; "
            f"border: 1px solid {border}; border-radius: {V3_RD['xl']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        c_ink_secondary = v3c("ink_secondary", self._modo).name()
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c_ink_secondary}; "
            f"border: none; border-radius: 12px; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; "
            f"color: {v3c('text', self._modo).name()}; }}"
        )
        self._style_footer()

    def _style_footer(self):
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_on_acc = v3c("primary_ink", self._modo).name()
        text = v3c("text", self._modo).name()
        text_muted = v3c("text2", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._footer_buttons:
            role = btn.property("nm_role") or "secondary"
            btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
            if role == "primary":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; }}"
                )
            elif role == "danger":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('warm', self._modo).name()}; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_muted}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:  # secondary
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )


# Alias semántico
NMModal = NMDialog


def nm_confirm(
    parent: QWidget,
    titulo: str,
    mensaje: str,
    on_confirm,
    confirm_text: str = "Restablecer",
    modo: str = None,
) -> NMDialog:
    """Confirmación estándar sobre NMDialog (patrón único del producto).

    La usan todos los "Restablecer por defecto" de los configurables del Hub:
    overlay child de la ventana (sin ventana top-level), Cancelar ghost +
    acción danger. `on_confirm` corre solo si el profesional confirma.
    """
    win = parent.window() if parent is not None else None
    dlg = NMDialog(title=titulo, modo=modo, parent=win)
    body = QLabel(mensaje)
    body.setWordWrap(True)
    body.setFont(qfont("size_small"))
    body.setStyleSheet(
        f"color: {v3c('text2', norm_modo(modo or _tm().modo)).name()}; background: transparent;"
    )
    dlg.set_body_widget(body)
    dlg.add_footer_button("Cancelar", role="ghost", callback=dlg.close)

    def _go():
        dlg.close()
        on_confirm()

    dlg.add_footer_button(confirm_text, role="danger", callback=_go)
    dlg.show_centered()
    return dlg


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


# ── NMWindowChrome ────────────────────────────────────────────────────────────
# Runtime spec §3 / components.jsx `WindowChrome`:
#   Barra de título custom de 36 px que reemplaza el título nativo del SO.
#   Background bg-1, border-bottom 1px line.
#   Izquierda: logo mark 16×16 (gradiente primary→accent→amber) + título
#   (Manrope 12/600, ink-2) + subtítulo opcional (mute, separado con "—").
#   Derecha: status dot + label opcionales + botones min/max/close (40×28 c/u).
#   Drag: mousePressEvent/mouseMoveEvent mueven la ventana padre.
# ─────────────────────────────────────────────────────────────────────────────


class _ChromeWinBtn(QPushButton):
    """Botón de control de ventana (min / max / close) para NMWindowChrome."""

    def __init__(self, kind: str, modo: str, parent=None):
        super().__init__(parent)
        self._kind = kind  # "min" | "max" | "close"
        self._modo = norm_modo(modo)
        self.setFixedSize(46, 38)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._apply_style()

    def _apply_style(self):
        is_dark = "dark" in self._modo
        hover_bg = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.05)"
        pressed_bg = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.1)"
        if self._kind == "close":
            danger = v3c("danger", self._modo)
            pressed = QColor(
                blend_color(
                    v3c("primary_ink", self._modo).name(),
                    danger.name(),
                    0.18 if is_dark else 0.12,
                )
            )
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                }}
                QPushButton:hover {{
                    background: {danger.name()};
                }}
                QPushButton:pressed {{
                    background: {pressed.name()};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                }}
                QPushButton:hover {{
                    background: {hover_bg};
                }}
                QPushButton:pressed {{
                    background: {pressed_bg};
                }}
            """)

    def paintEvent(self, event):
        p = QPainter(self)
        is_dark = "dark" in self._modo
        hovered = self.underMouse()
        pressed = self.isDown()
        # Fondo hover/pressed pintado ACÁ: este paintEvent custom reemplaza el
        # render por defecto del QPushButton, por lo que el `background` del
        # stylesheet nunca llegaba a dibujarse. En light eso dejaba la X en
        # primary_ink (casi blanco) sobre la superficie clara del chrome → la X
        # "desaparecía" al hover (bug user feedback). Pintar el fondo restaura el patrón
        # Windows (rojo en close, sutil en min/max) y devuelve el contraste.
        if hovered or pressed:
            if self._kind == "close":
                if pressed:
                    bg = QColor(
                        blend_color(
                            v3c("primary_ink", self._modo).name(),
                            v3c("danger", self._modo).name(),
                            0.18 if is_dark else 0.12,
                        )
                    )
                else:
                    bg = QColor(v3c("danger", self._modo))
            else:
                base = QColor(255, 255, 255) if is_dark else QColor(0, 0, 0)
                if is_dark:
                    base.setAlphaF(0.15 if pressed else 0.10)
                else:
                    base.setAlphaF(0.10 if pressed else 0.05)
                bg = base
            p.fillRect(self.rect(), bg)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        if self._kind == "close" and hovered:
            color = QColor(v3c("primary_ink", self._modo))
        else:
            color = QColor(v3c("text", self._modo))
        pen = QPen(color, 1)
        p.setPen(pen)
        cx = self.width() // 2
        cy = self.height() // 2
        if self._kind == "min":
            p.drawLine(cx - 5, cy, cx + 5, cy)
        elif self._kind == "max":
            p.drawRect(cx - 5, cy - 5, 10, 10)
        elif self._kind == "close":
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.drawLine(cx - 5, cy - 5, cx + 5, cy + 5)
            p.drawLine(cx + 5, cy - 5, cx - 5, cy + 5)
        p.end()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()
        self.update()


class _ChromeLogoMark(QLabel):
    """Logo icon mark que usa el asset real de la marca mediante nm_logo_pixmap."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(20, 20)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        from shared.assets import nm_logo_pixmap

        pm = nm_logo_pixmap(self._modo, tipo="icon", width=20, height=20)
        self.setPixmap(pm)
        self.update()


class NMWindowChrome(QWidget):
    """Barra de título custom 36 px (runtime spec WindowChrome).

    - Drag a mover: mantiene lógica mousePressEvent/mouseMoveEvent.
    - Doble clic → maximizar/restaurar.
    - Botones min/max/close llaman a window().showMinimized() etc.
    - ThemeManager conectado vía _tm().theme_changed.
    """

    theme_toggle = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(
        self,
        title: str = "NeuroMood",
        subtitle: str = None,
        status: str = None,
        status_label: str = None,
        show_theme_toggle: bool = False,
        show_settings_btn: bool = False,
        show_maximize: bool = True,
        modo: str = "dark_hybrid",
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._title = title
        self._subtitle = subtitle
        self._status = status  # "ok" | "warn" | "danger" | None
        self._status_label = status_label
        self._show_theme_toggle = show_theme_toggle
        self._show_settings_btn = show_settings_btn
        # Ventanas de tamaño fijo (onboarding, diálogos) no deben maximizar:
        # solo "—" minimizar y "✕" cerrar. Maximizar rompería el layout
        # fit-first y no aporta en una card centrada.
        self._show_maximize = show_maximize
        self._drag_pos = None

        self.setFixedHeight(38)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._build_ui()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 0, 0)
        lay.setSpacing(0)

        title_wrap = QWidget(self)
        title_wrap.setStyleSheet("background: transparent;")
        title_l = QHBoxLayout(title_wrap)
        title_l.setContentsMargins(0, 0, 0, 0)
        title_l.setSpacing(7)
        self._mark = _ChromeLogoMark(self._modo, self)
        title_l.addWidget(self._mark, 0, Qt.AlignmentFlag.AlignVCenter)
        self._lbl_title = QLabel(self._title)
        title_l.addWidget(self._lbl_title, 0, Qt.AlignmentFlag.AlignVCenter)
        if self._subtitle:
            self._lbl_sep = QLabel("/")
            title_l.addWidget(self._lbl_sep, 0, Qt.AlignmentFlag.AlignVCenter)
            self._lbl_sub = QLabel(self._subtitle)
            title_l.addWidget(self._lbl_sub, 0, Qt.AlignmentFlag.AlignVCenter)
        self._title_wrap = title_wrap
        lay.addWidget(title_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        # ── Contexto de módulo (Suite, Runtime) ────────────────────────────────
        # Cuando hay un módulo abierto, el back + icono + título viven aquí, en la
        # titlebar, en vez de una banda de 56px aparte. Oculto hasta abrir módulo.
        ctx_wrap = QWidget(self)
        ctx_wrap.setStyleSheet("background: transparent;")
        ctx_l = QHBoxLayout(ctx_wrap)
        ctx_l.setContentsMargins(0, 0, 0, 0)
        ctx_l.setSpacing(8)
        self._ctx_back = QPushButton("←", ctx_wrap)
        self._ctx_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ctx_back.setFixedSize(30, 30)
        self._ctx_back.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._ctx_back.setAccessibleName("Volver")
        self._ctx_back.setToolTip("Volver al inicio")
        self._ctx_back.clicked.connect(self._on_ctx_back)
        ctx_l.addWidget(self._ctx_back, 0, Qt.AlignmentFlag.AlignVCenter)
        self._ctx_icon = QLabel(ctx_wrap)
        self._ctx_icon.setFixedSize(18, 18)
        self._ctx_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ctx_icon.setStyleSheet("background: transparent;")
        ctx_l.addWidget(self._ctx_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self._ctx_title = QLabel("", ctx_wrap)
        ctx_l.addWidget(self._ctx_title, 0, Qt.AlignmentFlag.AlignVCenter)
        ctx_wrap.hide()
        self._ctx_wrap = ctx_wrap
        lay.addWidget(ctx_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        lay.addStretch(1)

        # Optional status dot + label (JetBrains Mono 11)
        if self._status is not None:
            self._status_dot = NMStatusDot(tone=self._status, modo=self._modo, parent=self)
            lay.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(6)
            self._lbl_status_txt = QLabel(self._status_label or "")
            lay.addWidget(self._lbl_status_txt, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(12)

        if self._show_settings_btn:
            self._btn_settings = QPushButton(self)
            self._btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_settings.setStyleSheet(
                f"QPushButton {{ border: none; "
                "background: transparent; border-radius: 12px; padding: 0px; } "
                f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
            )
            self._btn_settings.setFixedSize(30, 30)
            self._btn_settings.setToolTip("Ajustes")
            self._btn_settings.setAccessibleName("Ajustes")
            # P2.C: usar el engranaje "cog" en vez de "settings" para que no se
            # confunda con el icono de tema (sun/moon) en la titlebar.
            self._btn_settings.setIcon(nm_icon("cog", C("ink_secondary", self._modo), size=14))
            self._btn_settings.setIconSize(QSize(14, 14))
            self._btn_settings.clicked.connect(self.settings_clicked.emit)
            lay.addWidget(self._btn_settings, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(6)

        if self._show_theme_toggle:
            self._btn_theme = QPushButton(self)
            self._btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_theme.setStyleSheet(
                f"QPushButton {{ border: none; "
                "background: transparent; border-radius: 12px; padding: 0px; } "
                f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
            )
            self._btn_theme.setFixedSize(30, 30)
            is_dark = "dark" in self._modo
            icon_name = "sun" if is_dark else "moon"
            self._btn_theme.setIcon(nm_icon(icon_name, C("ink_secondary", self._modo), size=14))
            self._btn_theme.setIconSize(QSize(14, 14))
            self._btn_theme.clicked.connect(self.theme_toggle.emit)
            lay.addWidget(self._btn_theme, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(8)

        # Window controls: min / max / close (standard Windows design)
        win_controls = QWidget(self)
        # Transparente como title_wrap/content: sin esto el wrapper hereda el
        # `QWidget { background-color: bg_primary }` global y pinta una caja más
        # oscura sobre el `surface` del chrome (costura tras min/max/close en dark).
        win_controls.setStyleSheet("background: transparent;")
        win_controls_l = QHBoxLayout(win_controls)
        win_controls_l.setContentsMargins(0, 0, 0, 0)
        win_controls_l.setSpacing(0)

        self._btn_min = _ChromeWinBtn("min", self._modo, self)
        self._btn_max = _ChromeWinBtn("max", self._modo, self) if self._show_maximize else None
        self._btn_close = _ChromeWinBtn("close", self._modo, self)

        self._btn_min.clicked.connect(lambda: self.window().showMinimized())
        if self._btn_max is not None:
            self._btn_max.clicked.connect(self._toggle_maximize)
        self._btn_close.clicked.connect(self.window().close)

        win_controls_l.addWidget(self._btn_min)
        if self._btn_max is not None:
            win_controls_l.addWidget(self._btn_max)
        win_controls_l.addWidget(self._btn_close)
        lay.addWidget(win_controls)

    # ── Drag / maximize ───────────────────────────────────────────────────────

    def _toggle_maximize(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and self._drag_pos is not None
            and not self.window().isMaximized()
        ):
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._show_maximize:
            self._toggle_maximize()
        else:
            super().mouseDoubleClickEvent(event)

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        # Background: surface, como la barra de ventana del mockup.
        p.fillRect(self.rect(), v3c("surface", self._modo))
        # Border bottom: 1px line
        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c_ink2 = v3c("ink_2", self._modo)
        c_mute = v3c("mute", self._modo)
        c_faint = v3c("faint", self._modo)

        title_f = qfont("size_caption", weight=600)
        self._lbl_title.setFont(title_f)
        self._lbl_title.setStyleSheet(f"color: {c_ink2.name()}; background: transparent;")

        # El logo se actualiza internamente en _ChromeLogoMark al aplicar tema
        if hasattr(self, "_mark") and isinstance(self._mark, _ChromeLogoMark):
            self._mark._apply_theme(self._modo)

        if hasattr(self, "_lbl_sep"):
            sep_f = qfont("size_caption")
            self._lbl_sep.setFont(sep_f)
            self._lbl_sep.setStyleSheet(f"color: {c_faint.name()}; background: transparent;")
        if hasattr(self, "_lbl_sub"):
            sub_f = qfont("size_caption")
            self._lbl_sub.setFont(sub_f)
            self._lbl_sub.setStyleSheet(f"color: {c_mute.name()}; background: transparent;")
        if hasattr(self, "_lbl_status_txt"):
            self._lbl_status_txt.setFont(qfont_mono(8))
            self._lbl_status_txt.setStyleSheet(f"color: {c_mute.name()}; background: transparent;")
        if hasattr(self, "_status_dot"):
            self._status_dot._apply_theme(modo)

        self._btn_min._apply_theme(modo)
        if self._btn_max is not None:
            self._btn_max._apply_theme(modo)
        self._btn_close._apply_theme(modo)
        self._mark._apply_theme(modo)

        # Sin borde en los botones de la titlebar (Volver/Ajustes/Tema): el
        # feedback es solo el hover, según pedido del user feedback. Aplica en todos los
        # módulos, Home, Hub, ventanas y subventanas que usan NMWindowChrome.
        tool_btn_style = (
            f"QPushButton {{ border: none; "
            "background: transparent; border-radius: 12px; padding: 0px; } "
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
        )

        if hasattr(self, "_btn_settings"):
            self._btn_settings.setStyleSheet(tool_btn_style)
            self._btn_settings.setIcon(
                nm_icon("cog", v3c("ink_secondary", self._modo), size=14)
            )

        if hasattr(self, "_btn_theme"):
            self._btn_theme.setStyleSheet(tool_btn_style)
            is_dark = "dark" in self._modo
            icon_name = "sun" if is_dark else "moon"
            self._btn_theme.setIcon(nm_icon(icon_name, v3c("ink_secondary", self._modo), size=14))

        if hasattr(self, "_ctx_title"):
            self._apply_ctx_theme()

        self.update()

    # ── Contexto de módulo (Suite, Runtime) ──────────────────────────────────────

    def _on_ctx_back(self):
        cb = getattr(self, "_ctx_back_cb", None)
        if callable(cb):
            cb()

    def _apply_ctx_icon(self):
        if not hasattr(self, "_ctx_icon"):
            return
        key = getattr(self, "_ctx_icon_key", "") or ""
        if not key:
            self._ctx_icon.clear()
            self._ctx_icon.hide()
            return
        try:
            pm = nm_icon(key, v3c("accent", self._modo), size=18).pixmap(18, 18)
            if not pm.isNull():
                self._ctx_icon.setPixmap(pm)
                self._ctx_icon.show()
                return
        except Exception:
            pass
        self._ctx_icon.hide()

    def _apply_ctx_theme(self):
        if not hasattr(self, "_ctx_title"):
            return
        c_ink2 = v3c("ink_2", self._modo)
        self._ctx_title.setFont(qfont("size_caption", weight=600))
        self._ctx_title.setStyleSheet(f"color: {c_ink2.name()}; background: transparent;")
        self._ctx_back.setStyleSheet(
            "QPushButton { background: transparent; "
            "border: none; border-radius: 12px; "
            f"color: {c_ink2.name()}; padding: 0px; }} "
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
        )
        self._apply_ctx_icon()

    def set_module_context(self, title: str = "", icon: str = "", back_callback=None):
        """Suite: muestra back + icono + título de módulo en la titlebar y oculta el brand."""
        self._ctx_back_cb = back_callback
        self._ctx_icon_key = icon or ""
        self._ctx_title.setText((title or "").strip())
        if hasattr(self, "_title_wrap"):
            self._title_wrap.hide()
        self._ctx_wrap.show()
        self._apply_ctx_theme()

    def clear_module_context(self):
        """Suite: vuelve al brand normal de la titlebar (Home)."""
        self._ctx_back_cb = None
        if hasattr(self, "_ctx_wrap"):
            self._ctx_wrap.hide()
        if hasattr(self, "_title_wrap"):
            self._title_wrap.show()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_subtitle(self, text: str | None):
        if hasattr(self, "_lbl_sub"):
            self._lbl_sub.setText(text or "")

    def set_status(self, tone: str | None, label: str = ""):
        if hasattr(self, "_status_dot"):
            self._status_dot.set_tone(tone or "ok")
        if hasattr(self, "_lbl_status_txt"):
            self._lbl_status_txt.setText(label)










# ── NMDialogScaffold ──────────────────────────────────────────────────────────


class NMDialogScaffold(QWidget):
    """Ventana auxiliar standalone con header, cuerpo y footer de acciones.

    Para editores y ventanas secundarias (no overlay). Incluye:
      - Header fijo: eyebrow opcional + título + botón cerrar
      - Cuerpo: widget principal (flexible, con stretch)
      - Footer fijo: action bar con botones alineados a la derecha

    Uso::
        win = NMDialogScaffold("Editor de textos", modo=modo)
        win.set_body(editor_widget)
        win.add_action("Cancelar", role="ghost", callback=win.close)
        win.add_action("Guardar", role="primary", callback=on_save)
        win.show()
    """

    def __init__(
        self,
        title: str = "",
        eyebrow: str = "",
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._action_buttons: list[QPushButton] = []
        # Flags de ventana SOLO standalone. Con parent (embebido en un QDialog
        # via addWidget) el flag Window NO se limpia porque el parent ya
        # coincide y addChildWidget saltea el setParent → el scaffold quedaba
        # como top-level invisible y el diálogo medía 360×0 (la "mini ventana"
        # de Olvidé mi PIN / Quitar paciente / Exportar informe).
        if parent is None:
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
            )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        root.setSpacing(0)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(V3_SP["sm"])
        hdr.setContentsMargins(0, 0, 0, V3_SP["sm"])

        vtext = QVBoxLayout()
        vtext.setSpacing(2)
        # Parent explícito pre-addWidget: setVisible(True) sobre un QLabel
        # huérfano lo muestra como top-level fugaz (AGENTS §10.9).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        vtext.addWidget(self._eyebrow_lbl)

        self._title_lbl = QLabel(title or "")
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        vtext.addWidget(self._title_lbl)
        hdr.addLayout(vtext, stretch=1)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._close_btn.setFlat(True)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.close)
        hdr.addWidget(self._close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(hdr)

        # Body slot
        self._body_slot = QVBoxLayout()
        self._body_slot.setContentsMargins(0, 0, 0, 0)
        self._body_slot.setSpacing(0)
        root.addLayout(self._body_slot, stretch=1)

        # Footer
        self._footer_sep = QWidget()
        self._footer_sep.setFixedHeight(1)
        root.addWidget(self._footer_sep)

        footer = QHBoxLayout()
        footer.setSpacing(V3_SP["sm"])
        footer.setContentsMargins(0, V3_SP["sm"], 0, 0)
        footer.addStretch()
        root.addLayout(footer)
        self._footer_lay = footer

        _tm().theme_changed.connect(self._apply_scaffold_theme)
        self._apply_scaffold_theme(self._modo)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_body(self, widget: QWidget) -> None:
        while self._body_slot.count():
            item = self._body_slot.takeAt(0)
            if item.widget() and item.widget() is not widget:
                item.widget().setParent(None)
        self._body_slot.addWidget(widget)

    def add_action(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        variant = {
            "primary": "primary",
            "secondary": "secondary",
            "ghost": "ghost",
            "danger": "danger",
        }.get(role, "secondary")
        btn = NMButton(label, variant=variant, size="md", modo=self._modo, width=90)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(90)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_lay.addWidget(btn)
        self._action_buttons.append(btn)
        self._style_scaffold_actions()
        return btn

    def _style_scaffold_actions(self) -> None:
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_m = v3c("text2", self._modo).name()
        text = v3c("text", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._action_buttons:
            role = btn.property("nm_role") or "secondary"
            btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
            if isinstance(btn, NMButton):
                btn.set_variant(
                    "primary"
                    if role == "primary"
                    else "danger"
                    if role == "danger"
                    else "ghost"
                    if role == "ghost"
                    else "secondary"
                )
                btn._apply_theme(self._modo)
                continue
            if role == "primary":
                text_on_acc = v3c("text_on_accent", self._modo).name()
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; color: {text_on_acc}; }}"
                )
            elif role == "danger":
                text_on_danger = v3c("primary_ink", self._modo).name()
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_danger}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_m}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )

    def _apply_scaffold_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self.setStyleSheet(f"QWidget {{ background: {bg}; }}")
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {ink2}; "
            f"border: none; border-radius: 12px; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; color: {ink1}; }}"
        )
        sep_c = v3c("border", self._modo)
        self._footer_sep.setStyleSheet(
            f"background: rgba({sep_c.red()},{sep_c.green()},{sep_c.blue()},60);"
        )
        self._style_scaffold_actions()


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
