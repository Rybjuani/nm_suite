"""Navigation components: NMIconButton, NMSidebar, NMHeader, NMModule, _LogoLabel, _ChromeLogoMark."""

from __future__ import annotations

import os

from PyQt6.QtCore import (
    Qt,
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QRectF,
    QPointF,
    QSize,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QIcon,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPalette,
    QPixmap,
    QImage,
)
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    C,
    HEADER_H,
    RADIUS_PILL,
    RADIUS_SMALL,
    SessionColor,
    ThemeAwareWidgetMixin,
    V3_RD,
    colors,
    label_style,
    nm_icon,
    norm_modo,
    obtener_ruta_recurso,
    qcolor_to_rgba_css,
    qfont,
    radial_glow,
    recolorear_logo_light,
    sp,
    v3c,
)
from shared.components.buttons import _NM_CONTROL_HEIGHT
from shared.components.session import NMStreakBadge, _rgba


def _tm() -> ThemeManager:
    return ThemeManager.instance()

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


class _ChromeLogoMark(QLabel):
    """Icono simple del titlebar canónico (`.tb-ic` del mockup)."""

    def __init__(self, modo: str, icon_name: str = "home", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._icon_name = icon_name or "home"
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(18, 18)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        icon = nm_icon(self._icon_name, v3c("accent", self._modo), size=18)
        self.setPixmap(icon.pixmap(18, 18))
        self.update()

