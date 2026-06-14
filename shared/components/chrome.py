"""Window chrome components: _ChromeWinBtn, NMWindowChrome."""

from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    QSize,
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
    C,
    blend_color,
    nm_icon,
    norm_modo,
    qfont,
    qfont_mono,
    v3c,
)
from shared.components.navigation import _ChromeLogoMark
from shared.components.status import NMStatusDot


def _tm() -> ThemeManager:
    return ThemeManager.instance()


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

