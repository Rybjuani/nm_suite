"""Window chrome components: _ChromeWinBtn, NMWindowChrome."""

from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    QRectF,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    nm_icon,
    norm_modo,
    qcolor_to_rgba_css,
    qfont,
    qfont_mono,
    v3c,
)
from shared.components.navigation import _ChromeLogoMark
from shared.components.status import NMStatusDot


def _tm() -> ThemeManager:
    return ThemeManager.instance()


_NM_CHROME_PAD_X = 16
_NM_CHROME_HEIGHT = 49  # mockup .titlebar{padding:11px 16px} + items 26px + border ≈ 49px
_NM_CHROME_GAP = 10
_NM_CHROME_TITLE_GAP = 8
_NM_CHROME_STATUS_GAP = 14
_NM_CHROME_BACK_SIZE = 26
_NM_CHROME_BACK_RADIUS = 8
_NM_CHROME_ICON_SIZE = 18
# Theme toggle = `.tb-theme` canónico del titlebar del mockup (línea 195):
# botón glifo 24×24 r7, solo sol/luna 16px, color ink-3 (hover ink + surface-3).
# NO es la `.themetoggle` de la cáscara web (label + píldora) — esa no se replica.
_NM_CHROME_THEME_TOGGLE_W = 24
_NM_CHROME_THEME_TOGGLE_H = 24
_NM_CHROME_THEME_TOGGLE_RADIUS = 7
_NM_CHROME_THEME_ICON_SIZE = 16
_NM_CHROME_WIN_DOT_SIZE = 13
_NM_CHROME_WIN_DOT_GAP = 8
_NM_CHROME_WIN_DOT_OPACITY = 0.55
# Orden visual del mockup `.tb-dots` (línea 194): verde, amarillo, rojo de
# izquierda a derecha. Los botones se añaden en orden min(izq) → max → close(der),
# así que min=verde, max=amarillo, close=rojo para replicar el semáforo del mockup.
_NM_CHROME_WIN_DOT_COLORS = {
    "min": "#56B27A",
    "max": "#E0B23E",
    "close": "#E0695A",
}


def _css_color(color: QColor) -> str:
    return color.name() if color.alpha() == 255 else qcolor_to_rgba_css(color)


class _ChromeWinBtn(QPushButton):
    """Botón de control de ventana (min / max / close) para NMWindowChrome."""

    def __init__(self, kind: str, modo: str, height: int = 38, parent=None):
        super().__init__(parent)
        self._kind = kind  # "min" | "max" | "close"
        self._modo = norm_modo(modo)
        self.setFixedSize(_NM_CHROME_WIN_DOT_SIZE, max(_NM_CHROME_BACK_SIZE, int(height)))
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)

    def paintEvent(self, event):
        p = QPainter(self)
        hovered = self.underMouse()
        pressed = self.isDown()
        color = QColor(_NM_CHROME_WIN_DOT_COLORS.get(self._kind, "#9A9382"))
        color.setAlphaF(1.0 if (hovered or pressed) else _NM_CHROME_WIN_DOT_OPACITY)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        x = (self.width() - _NM_CHROME_WIN_DOT_SIZE) / 2
        y = (self.height() - _NM_CHROME_WIN_DOT_SIZE) / 2
        p.drawEllipse(
            int(round(x)),
            int(round(y)),
            _NM_CHROME_WIN_DOT_SIZE,
            _NM_CHROME_WIN_DOT_SIZE,
        )
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


class _ChromeThemeToggle(QPushButton):
    """Botón glifo sol/luna del titlebar canónico (`.tb-theme`, mockup línea 195).

    24×24 r7, solo el glifo (16px): luna en claro, sol en oscuro. Hover: color
    ink + fondo surface-3. Sin label ni píldora (eso era la `.themetoggle` de la
    cáscara web, que el plan dice NO replicar).
    """

    def __init__(self, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setFixedSize(_NM_CHROME_THEME_TOGGLE_W, _NM_CHROME_THEME_TOGGLE_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        self._apply_theme(self._modo)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        hovered = self.underMouse()
        is_dark = "dark" in self._modo

        # Fondo solo en hover (surface-3), radio 7 — `.tb-theme:hover`.
        if hovered:
            rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(v3c("surface3", self._modo))
            p.drawRoundedRect(
                rect, _NM_CHROME_THEME_TOGGLE_RADIUS, _NM_CHROME_THEME_TOGGLE_RADIUS
            )

        # Glifo: luna en claro, sol en oscuro (mockup: dark→sun, light→moon).
        icon_name = "sun" if is_dark else "moon"
        icon_color = v3c("ink" if hovered else "faint", self._modo)
        icon = nm_icon(icon_name, icon_color, size=_NM_CHROME_THEME_ICON_SIZE)
        ix = (self.width() - _NM_CHROME_THEME_ICON_SIZE) // 2
        iy = (self.height() - _NM_CHROME_THEME_ICON_SIZE) // 2
        p.drawPixmap(ix, iy, icon.pixmap(_NM_CHROME_THEME_ICON_SIZE, _NM_CHROME_THEME_ICON_SIZE))
        p.end()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setToolTip(
            "Cambiar a modo claro" if "dark" in self._modo else "Cambiar a modo oscuro"
        )
        self.update()


class NMWindowChrome(QWidget):
    """Barra de título custom (runtime spec WindowChrome). Altura canónica 44 px.

    - Drag a mover: mantiene lógica mousePressEvent/mouseMoveEvent.
    - Doble clic → maximizar/restaurar.
    - Botones min/max/close llaman a window().showMinimized() etc.
    - ThemeManager conectado vía _tm().theme_changed.
    """

    theme_toggle = pyqtSignal()

    def __init__(
        self,
        title: str = "NeuroMood",
        subtitle: str = None,
        status: str = None,
        status_label: str = None,
        show_theme_toggle: bool = False,
        show_maximize: bool = True,
        show_amber_dot: bool | None = None,
        modo: str = "dark_hybrid",
        height: int = _NM_CHROME_HEIGHT,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._title = title
        self._subtitle = subtitle
        self._status = status  # "ok" | "warn" | "danger" | None
        self._status_label = status_label
        self._show_theme_toggle = show_theme_toggle
        # Ventanas de tamaño fijo (onboarding, diálogos) no deben maximizar:
        # solo "—" minimizar y "✕" cerrar. Maximizar rompería el layout
        # fit-first y no aporta en una card centrada.
        self._show_maximize = show_maximize
        # El semáforo canónico (`.tb-dots`, mockup línea 526) SIEMPRE muestra 3
        # puntos (verde/ámbar/rojo). En ventanas de tamaño fijo no maximizamos,
        # pero el punto ámbar debe seguir visible como decorativo para igualar el
        # canónico. Default: sigue a show_maximize (back-compat).
        self._show_amber_dot = show_maximize if show_amber_dot is None else show_amber_dot
        self._chrome_height = max(28, int(height))
        self._drag_pos = None

        self.setFixedHeight(self._chrome_height)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._build_ui()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(_NM_CHROME_PAD_X, 0, _NM_CHROME_PAD_X, 0)
        lay.setSpacing(_NM_CHROME_GAP)

        title_wrap = QWidget(self)
        title_wrap.setStyleSheet("background: transparent;")
        title_l = QHBoxLayout(title_wrap)
        title_l.setContentsMargins(0, 0, 0, 0)
        title_l.setSpacing(_NM_CHROME_TITLE_GAP)
        mark_icon = "brain" if "hub" in (self._title or "").lower() else "home"
        self._mark = _ChromeLogoMark(self._modo, mark_icon, self)
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
        ctx_l.setSpacing(_NM_CHROME_GAP)
        self._ctx_back = QPushButton("←", ctx_wrap)
        self._ctx_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ctx_back.setMinimumSize(0, 0)
        self._ctx_back.setFixedSize(_NM_CHROME_BACK_SIZE, _NM_CHROME_BACK_SIZE)
        self._ctx_back.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._ctx_back.setAccessibleName("Volver")
        self._ctx_back.setToolTip("Volver al inicio")
        self._ctx_back.clicked.connect(self._on_ctx_back)
        ctx_l.addWidget(self._ctx_back, 0, Qt.AlignmentFlag.AlignVCenter)
        self._ctx_icon = QLabel(ctx_wrap)
        self._ctx_icon.setFixedSize(_NM_CHROME_ICON_SIZE, _NM_CHROME_ICON_SIZE)
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
            lay.addSpacing(_NM_CHROME_STATUS_GAP)

        if self._show_theme_toggle:
            self._btn_theme = _ChromeThemeToggle(self._modo, self)
            self._btn_theme.clicked.connect(self.theme_toggle.emit)
            lay.addWidget(self._btn_theme, 0, Qt.AlignmentFlag.AlignVCenter)

        # Window controls: semaforo dots from the mockup titlebar.
        win_controls = QWidget(self)
        # Transparente como title_wrap/content: sin esto el wrapper hereda el
        # `QWidget { background-color: bg_primary }` global y pinta una caja más
        # oscura sobre el `surface` del chrome (costura tras min/max/close en dark).
        win_controls.setStyleSheet("background: transparent;")
        win_controls_l = QHBoxLayout(win_controls)
        win_controls_l.setContentsMargins(0, 0, 0, 0)
        win_controls_l.setSpacing(_NM_CHROME_WIN_DOT_GAP)

        self._btn_min = _ChromeWinBtn("min", self._modo, self._chrome_height, self)
        # El punto ámbar (max) se crea si se maximiza O si se pidió decorativo.
        self._btn_max = (
            _ChromeWinBtn("max", self._modo, self._chrome_height, self)
            if (self._show_maximize or self._show_amber_dot)
            else None
        )
        self._btn_close = _ChromeWinBtn("close", self._modo, self._chrome_height, self)

        self._btn_min.clicked.connect(lambda: self.window().showMinimized())
        if self._btn_max is not None:
            if self._show_maximize:
                self._btn_max.clicked.connect(self._toggle_maximize)
            else:
                # Decorativo: sin maximizar (rompería el layout fit-first de la
                # ventana fija). Transparente al mouse → solo igual visual.
                self._btn_max.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
                )
                self._btn_max.setCursor(Qt.CursorShape.ArrowCursor)
        self._btn_close.clicked.connect(self.window().close)

        win_controls_l.addWidget(self._btn_min)
        if self._btn_max is not None:
            win_controls_l.addWidget(self._btn_max)
        win_controls_l.addWidget(self._btn_close)
        self._win_controls = win_controls
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
        p.fillRect(self.rect(), v3c("chrome", self._modo))
        border_c = v3c("chromeLine", self._modo)
        p.setPen(QPen(border_c, 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c_ink = v3c("ink", self._modo)
        c_ink3 = v3c("text3", self._modo)
        c_faint = v3c("faint", self._modo)

        title_f = qfont(14, weight=600)
        self._lbl_title.setFont(title_f)
        self._lbl_title.setStyleSheet(f"color: {_css_color(c_ink)}; background: transparent;")

        # El logo se actualiza internamente en _ChromeLogoMark al aplicar tema
        if hasattr(self, "_mark") and isinstance(self._mark, _ChromeLogoMark):
            self._mark._apply_theme(self._modo)

        if hasattr(self, "_lbl_sep"):
            sep_f = qfont(13)
            self._lbl_sep.setFont(sep_f)
            self._lbl_sep.setStyleSheet(f"color: {_css_color(c_faint)}; background: transparent;")
        if hasattr(self, "_lbl_sub"):
            sub_f = qfont(13)
            self._lbl_sub.setFont(sub_f)
            self._lbl_sub.setStyleSheet(f"color: {_css_color(c_ink3)}; background: transparent;")
        if hasattr(self, "_lbl_status_txt"):
            self._lbl_status_txt.setFont(qfont_mono(8))
            self._lbl_status_txt.setStyleSheet(f"color: {_css_color(c_ink3)}; background: transparent;")
        if hasattr(self, "_status_dot"):
            self._status_dot._apply_theme(modo)

        self._btn_min._apply_theme(modo)
        if self._btn_max is not None:
            self._btn_max._apply_theme(modo)
        self._btn_close._apply_theme(modo)
        self._mark._apply_theme(modo)

        if hasattr(self, "_btn_theme"):
            self._btn_theme._apply_theme(self._modo)

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
            pm = nm_icon(key, v3c("accent", self._modo), size=_NM_CHROME_ICON_SIZE).pixmap(
                _NM_CHROME_ICON_SIZE,
                _NM_CHROME_ICON_SIZE,
            )
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
        c_ink = v3c("ink", self._modo)
        c_ink2 = v3c("ink_2", self._modo)
        self._ctx_title.setFont(qfont(14, weight=600))
        self._ctx_title.setStyleSheet(f"color: {_css_color(c_ink)}; background: transparent;")
        self._ctx_back.setStyleSheet(
            "QPushButton { background: transparent; "
            f"border: none; border-radius: {_NM_CHROME_BACK_RADIUS}px; "
            f"color: {_css_color(c_ink2)}; padding: 0px; }} "
            f"QPushButton:hover {{ background: {_css_color(v3c('surface3', self._modo))}; }}"
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

