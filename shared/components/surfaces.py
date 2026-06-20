"""Surface primitives shared by Suite and Hub."""

from __future__ import annotations

import os

from PyQt6 import sip
from PyQt6.QtCore import QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QEnterEvent,
    QFontMetrics,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    C,
    ThemeAwareWidgetMixin,
    V3_RD,
    V3_SP,
    eyebrow_font,
    nm_icon,
    norm_modo,
    pill_radius,
    qcolor_to_rgba_css,
    qfont,
    qfont_mono,
    v3_font,
    v3c,
)


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


class NMDivider(QWidget):
    """Separador token-driven. orient='h' o 'v', opacity 0-255.

    Uso:
        layout.addWidget(NMDivider())                  # horizontal sutil
        row.addWidget(NMDivider(orient="v", alpha=80)) # vertical
    """

    def __init__(
        self, orient: str = "h", alpha: int = 60, inset: int = 0, modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._orient = "v" if orient == "v" else "h"
        self._alpha = max(0, min(255, int(alpha)))
        self._inset = max(0, int(inset))
        if self._orient == "h":
            self.setFixedHeight(1)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedWidth(1)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        _tm().theme_changed.connect(self._apply_theme)

    def paintEvent(self, event):
        p = QPainter(self)
        col = v3c("border", self._modo)
        col.setAlpha(self._alpha)
        p.setPen(QPen(col, 1.0))
        if self._orient == "h":
            y = self.height() // 2
            p.drawLine(self._inset, y, self.width() - self._inset, y)
        else:
            x = self.width() // 2
            p.drawLine(x, self._inset, x, self.height() - self._inset)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


_BADGE_TONE_TO_KEY = {
    "neutral": "text2",  # ink-2: borde y texto
    "brand": "primary",
    "info": "primary",
    "accent": "accent",
    "gold": "gold",
    "rose": "rose",
    "positive": "success",
    "completed": "success",  # variante literal de la lámina de componentes
    "patient": "teal",  # identificación de paciente sin inventar semántica clínica
    "warn": "warning",
    "warning": "warning",  # alias
    "danger": "danger",
    "critical": "danger",
}

_BADGE_TONE_TO_SOFT_KEY = {
    "brand": "primary_soft",
    "info": "primary_soft",
    "accent": "accentSoft",
    "gold": "goldSoft",
    "rose": "roseSoft",
    "positive": "successSoft",
    "completed": "successSoft",
    "patient": "tealSoft",
    "warn": "warningSoft",
    "warning": "warningSoft",
    "danger": "dangerSoft",
    "critical": "dangerSoft",
}


class NMChip(QFrame):
    """NMChip F1 Polish V2."""

    def __init__(
        self,
        text: str,
        variant: str = "default",
        size: str = "default",
        icon_name: str = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = variant
        self._size = size
        self._icon_name = icon_name
        self.setObjectName("NMChip")

        lay = QHBoxLayout(self)
        h_margin = 8 if size == "sm" else 12
        v_margin = 2 if size == "sm" else 4
        lay.setContentsMargins(h_margin, v_margin, h_margin, v_margin)
        lay.setSpacing(4)

        if icon_name:
            self._icon = QLabel()
            self._icon.setFixedSize(14, 14)
            lay.addWidget(self._icon)
        else:
            self._icon = None

        self._label = QLabel()
        font_sz = "size_caption_xs" if size == "sm" else "size_caption"
        font = v3_font(font_sz, weight=TYPOGRAPHY["weight_semibold"])
        self._label.setFont(font)

        fm = QFontMetrics(font)
        max_w = 150
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, max_w)
        self._label.setText(elided)
        if elided != text:
            self.setToolTip(text)

        lay.addWidget(self._label)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        if self._variant in ("default", "tint"):
            color_hex = C("ink_primary", self._modo)
            bg_key = "surface2"
        elif self._variant in ("solid", "info"):
            color_hex = C("primary", self._modo)
            bg_key = "surface"
        elif self._variant in ("success", "warning", "danger", "amber"):
            color_hex = C(self._variant if self._variant != "amber" else "warning", self._modo)
            bg_key = self._variant if self._variant != "amber" else "warning"
        else:
            color_hex = C("ink_primary", self._modo)
            bg_key = "surface2"

        if self._variant in ("success", "warning", "danger", "amber", "info", "tint"):
            bg_base = QColor(color_hex)
            bg_base.setAlpha(36)
            bg_css = f"rgba({bg_base.red()},{bg_base.green()},{bg_base.blue()},{bg_base.alpha()})"
            bd_css = f"rgba({bg_base.red()},{bg_base.green()},{bg_base.blue()},60)"
        else:
            bg_css = C(bg_key, self._modo)
            bd_css = C("border", self._modo)

        self._pill_r_applied = pill_radius(self, fallback=20 if self._size == "sm" else 24)
        self.setStyleSheet(f"""
            QFrame#NMChip {{
                background-color: {bg_css};
                border: 1px solid {bd_css};
                border-radius: {self._pill_r_applied}px;
            }}
            QLabel {{
                color: {color_hex};
                background: transparent;
                border: none;
            }}
        """)

        if self._icon and self._icon_name:
            self._icon.setPixmap(nm_icon(self._icon_name, color_hex, size=14).pixmap(14, 14))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self) != getattr(self, "_pill_r_applied", None):
            self._apply_style()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


class NMBadge(QLabel):
    """Pill semántica del runtime spec §4.4 + mockup canónico.

    Implementa ``.badge`` del mockup (líneas 265-271):
      - pill 4×11 padding, soft bg + colored text
      - dot 6px ``.dt`` delante del texto (currentColor) en tonos brand/accent/
        gold/rose/positive/completed/patient/warning/danger — no en neutral.

    Args:
        text:   Etiqueta. Puede incluir un símbolo unicode a la izquierda.
        tone:   ``"neutral"`` / ``"brand"`` / ``"info"`` / ``"accent"`` /
                ``"gold"`` / ``"rose"`` / ``"positive"`` / ``"completed"`` /
                ``"patient"`` / ``"warning"`` / ``"danger"`` / ``"critical"``.
        modo:   Override; ``None`` = sigue ThemeManager.
        with_dot:  Forzar dot on/off. Por defecto: on para tonos no-neutral.
        parent: parent widget.

    Para añadir ícono SVG real, usar ``NMIcon`` en un layout horizontal y
    poner el ``NMBadge`` al lado — el runtime spec acepta rich text via QLabel
    pero la composición externa es más mantenible.
    """

    # Tonos que llevan el dot 6px del mockup (todos los semánticos; no neutral).
    _TONES_WITH_DOT = frozenset({
        "brand", "info", "accent", "gold", "rose",
        "positive", "completed", "patient", "warning", "warn",
        "danger", "critical",
    })

    def __init__(
        self,
        text: str = "",
        tone: str = "neutral",
        modo: str | None = None,
        with_dot: bool | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone if tone in _BADGE_TONE_TO_KEY else "neutral"
        # with_dot: None = automático (según tone), True/False = forzado.
        self._with_dot = (
            with_dot if with_dot is not None else (self._tone in self._TONES_WITH_DOT)
        )
        self._bare_text = ""  # texto sin dot (para re-render en theme change)
        self.setObjectName("NMBadge")
        self.setFont(v3_font("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(22)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        # Seteo inicial del texto (con dot si corresponde)
        self._render_text(text)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def set_tone(self, tone: str):
        if tone in _BADGE_TONE_TO_KEY:
            self._tone = tone
            if tone not in self._TONES_WITH_DOT:
                self._with_dot = False
            elif self._with_dot is None:
                self._with_dot = True
            self._render_text(self._bare_text)
            self._apply_style()

    def set_with_dot(self, enabled: bool):
        self._with_dot = bool(enabled)
        self._render_text(self._bare_text)
        self._apply_style()

    def tone(self) -> str:
        return self._tone

    def _render_text(self, text: str):
        """Renderiza el texto del QLabel con o sin dot según _with_dot."""
        self._bare_text = text
        if self._with_dot:
            key = _BADGE_TONE_TO_KEY[self._tone]
            color_hex = C(key, self._modo)
            # Rich text con span circular inline-block (Qt soporta CSS limitado).
            # Usamos table-cell para mejor alineación vertical del dot.
            dot_html = (
                f"<span style='display:inline-block; width:6px; height:6px;"
                f" border-radius:3px; background:{color_hex};"
                f" margin-right:5px; vertical-align:middle;'></span>"
            )
            # Escapar entidades HTML del texto del usuario para evitar parse issues.
            from html import escape
            safe_text = escape(text)
            self.setTextFormat(Qt.TextFormat.RichText)
            super().setText(dot_html + safe_text)
        else:
            self.setTextFormat(Qt.TextFormat.PlainText)
            super().setText(text)

    def _apply_style(self):
        key = _BADGE_TONE_TO_KEY[self._tone]
        color_hex = C(key, self._modo)
        if self._tone == "neutral":
            bg_css = C("surface3", self._modo)
        else:
            bg_css = C(_BADGE_TONE_TO_SOFT_KEY.get(self._tone, "primary_soft"), self._modo)
        # Mockup línea 265: .badge { border-radius: var(--r-pill) = 999px; font-size: 11.5px; padding: 4px 11px }
        self._pill_r_applied = 999  # r-pill canónico (era 11)
        self.setStyleSheet(f"""
            NMBadge {{
                color: {color_hex};
                background-color: {bg_css};
                border: 1px solid transparent;
                border-radius: {self._pill_r_applied}px;
                padding: 4px 11px;
                font-size: 11.5px;
                min-height: 22px;
            }}
        """)
        self._sync_min_width()

    def _sync_min_width(self):
        fm = QFontMetrics(self.font())
        # Medir solo el texto bare (sin HTML del dot) para que el ancho sea real.
        dot_w = 11 if self._with_dot else 0  # 6px dot + 5px margin
        self.setMinimumWidth(fm.horizontalAdvance(self._bare_text) + 20 + dot_w)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def setText(self, text: str):  # noqa: N802 — override de QLabel
        self._render_text(text)
        self._sync_min_width()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        # Re-render para que el dot tome el color del nuevo tema.
        self._render_text(self._bare_text)
        self._apply_style()


class NMSettingsSection(QFrame):
    """Sección de configuración v3 (NMConfigRow del README).

    - Surface card con radius ``V3_RD["lg"]`` (14).
    - Header eyebrow (caption semibold) con separador ``borderSoft``.
    - Filas key-value separadas con line ``borderSoft``.
    - Right slot acepta QWidget arbitrario (NMToggle, NMStatusChip, valor).
    """

    def __init__(self, title: str, modo: str = None, compact: bool = False, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self.setObjectName("NMSettingsSection")
        self._sec_shadow: QGraphicsDropShadowEffect | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._header = QLabel(title)
        self._header.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        if self._compact:
            self._header.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        else:
            self._header.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.addWidget(self._header)
        self._rows = QVBoxLayout()
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(0)
        lay.addLayout(self._rows)
        self._apply_theme(self._modo)
        self._apply_section_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_section_shadow(self):
        """Sombra v3 (idem NMCard) — sin esta queda plana sobre fondo claro."""
        if self._sec_shadow is None:
            self._sec_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if is_dark:
            self._sec_shadow.setBlurRadius(32)
            self._sec_shadow.setOffset(0, 10)
            self._sec_shadow.setColor(QColor(0, 0, 0, 120))
        else:
            self._sec_shadow.setBlurRadius(32)
            self._sec_shadow.setOffset(0, 12)
            self._sec_shadow.setColor(QColor(28, 34, 24, 18))
        self.setGraphicsEffect(self._sec_shadow)

    def paintEvent(self, event):
        """La sección usa superficie sólida QSS; sin brillo decorativo."""
        super().paintEvent(event)

    def add_row(self, label: str, value):
        row = QWidget()
        row.setObjectName("NMSettingsRow")
        lay = QHBoxLayout(row)
        if getattr(self, "_compact", False):
            lay.setContentsMargins(V3_SP["md"], V3_SP["xs"] + 2, V3_SP["md"], V3_SP["xs"] + 2)
        else:
            lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"] + 2, V3_SP["lg"], V3_SP["sm"] + 2)
        left = QLabel(label)
        left.setFont(qfont("size_small"))
        lay.addWidget(left)
        lay.addStretch()
        if isinstance(value, QWidget):
            lay.addWidget(value)
        else:
            right = QLabel(str(value))
            sval = str(value)
            right.setFont(
                qfont_mono(9) if "http" in sval or "..." in sval else qfont("size_caption")
            )
            lay.addWidget(right)
        self._rows.addWidget(row)
        self._apply_theme(self._modo)
        return row

    def add_log(self, html: str):
        log = QLabel(html)
        log.setTextFormat(Qt.TextFormat.RichText)
        log.setFont(qfont_mono(9))
        log.setWordWrap(True)
        if getattr(self, "_compact", False):
            log.setContentsMargins(V3_SP["md"], V3_SP["xs"], V3_SP["md"], V3_SP["xs"])
        else:
            log.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        self._rows.addWidget(log)
        self._apply_theme(self._modo)
        return log

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        surf_key = "surfaceSolid" if is_dark else "surface"
        bg = v3c(surf_key, self._modo).name()
        border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        text_eyebrow = v3c("ink_secondary", self._modo).name()
        text_body = v3c("text2", self._modo).name()
        radius = V3_RD["lg"]
        self.setStyleSheet(
            f"QFrame#NMSettingsSection {{ background: {bg}; "
            f"border: 1px solid {border}; border-radius: {radius}px; }}"
            f"QWidget#NMSettingsRow {{ background: transparent; "
            f"border-top: 1px solid {border}; }}"
        )
        self._header.setStyleSheet(f"color: {text_eyebrow}; background: transparent; ")
        for lbl in self.findChildren(QLabel):
            if lbl is not self._header:
                lbl.setStyleSheet(f"color: {text_body}; background: transparent;")
        # Re-aplicar sombra al cambiar tema
        if getattr(self, "_sec_shadow", None) is not None:
            self._apply_section_shadow()


class NMPanel(QFrame):
    """Panel de configuracion compacto con header y superficie v3."""

    def __init__(
        self, title: str, subtitle: str = "", modo: str = None, compact: bool = False, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self.setObjectName("NMPanel")
        self._panel_shadow: QGraphicsDropShadowEffect | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget(self)
        header.setStyleSheet("background: transparent;")
        header_lay = QVBoxLayout(header)
        if self._compact:
            header_lay.setContentsMargins(12, 10, 12, 6)
        else:
            header_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["sm"])
        header_lay.setSpacing(2)

        self._title = QLabel(title)
        self._title.setFont(
            qfont("size_h3" if self._compact else "size_h2", weight=TYPOGRAPHY["weight_semibold"])
        )
        header_lay.addWidget(self._title)
        self._subtitle = QLabel(subtitle)
        self._subtitle.setWordWrap(True)
        self._subtitle.setFont(qfont("size_caption"))
        if subtitle:
            header_lay.addWidget(self._subtitle)
        root.addWidget(header)

        self._body = QVBoxLayout()
        if self._compact:
            self._body.setContentsMargins(12, 0, 12, 12)
            self._body.setSpacing(8)
        else:
            self._body.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], V3_SP["md"])
            self._body.setSpacing(V3_SP["sm"])
        root.addLayout(self._body)

        self._apply_theme(self._modo)
        self._apply_panel_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    def body_layout(self) -> QVBoxLayout:
        return self._body

    def add_widget(self, widget: QWidget):
        self._body.addWidget(widget)
        return widget

    def _apply_panel_shadow(self):
        if self._panel_shadow is None:
            self._panel_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if is_dark:
            self._panel_shadow.setBlurRadius(32)
            self._panel_shadow.setOffset(0, 10)
            self._panel_shadow.setColor(QColor(0, 0, 0, 120))
        else:
            self._panel_shadow.setBlurRadius(32)
            self._panel_shadow.setOffset(0, 12)
            self._panel_shadow.setColor(QColor(28, 34, 24, 18))
        self.setGraphicsEffect(self._panel_shadow)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        self.setStyleSheet(
            f"QFrame#NMPanel {{ background: {bg}; border: 1px solid {border}; "
            f"border-radius: {V3_RD['lg']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        if self._panel_shadow is not None:
            self._apply_panel_shadow()


class NMFormRow(QWidget):
    """Fila label/control para formularios de configuracion."""

    def __init__(
        self,
        label: str,
        value,
        hint: str = "",
        modo: str = None,
        compact: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self.setObjectName("NMFormRow")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["sm"] if self._compact else V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self._label = QLabel(label)
        self._label.setFont(
            qfont(
                "size_caption" if self._compact else "size_small",
                weight=TYPOGRAPHY["weight_semibold"],
            )
        )
        text_col.addWidget(self._label)
        self._hint = QLabel(hint)
        self._hint.setWordWrap(True)
        self._hint.setFont(qfont("size_caption"))
        if hint:
            text_col.addWidget(self._hint)
        lay.addLayout(text_col, stretch=1)

        if isinstance(value, QWidget):
            self._value = value
            lay.addWidget(
                value, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        else:
            self._value = QLabel(str(value))
            self._value.setFont(qfont_mono(9) if "http" in str(value) else qfont("size_caption"))
            self._value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lay.addWidget(self._value)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("QWidget#NMFormRow { background: transparent; }")
        self._label.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._hint.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        if isinstance(self._value, QLabel):
            self._value.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; background: transparent;"
            )


class NMSyncOrb(QWidget):
    """Orb circular de estado de sincronización con animación de pulso.

    state: 'ok' (verde) | 'error' (rojo) | 'syncing' (ámbar, pulsa).
    """

    def __init__(self, state: str = "ok", size: int = 12, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._state = state
        self._anim_alpha = 255
        self._fade_dir = -1
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._pulse)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.set_state(state)
        _tm().theme_changed.connect(self._apply_theme)

    def set_state(self, state: str):
        self._state = state
        if state == "syncing":
            self._timer.start()
        else:
            self._timer.stop()
            self._anim_alpha = 255
        self.update()

    def _pulse(self):
        if sip.isdeleted(self):
            self._timer.stop()
            return
        self._anim_alpha += self._fade_dir * 14
        if self._anim_alpha <= 70:
            self._fade_dir = 1
        elif self._anim_alpha >= 255:
            self._fade_dir = -1
        self.update()

    def _color(self) -> QColor:
        key = {"ok": "sync_orb_green", "error": "error"}.get(self._state, "warning")
        return QColor(C(key, self._modo))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        c = self._color()

        # Glow halo radial — alpha modulado por pulso (max 100)
        glow = QRadialGradient(cx, cy, cx)
        glow_c = QColor(c)
        glow_c.setAlpha(int(self._anim_alpha * 0.39))  # ~100 en estado estático
        transparent = QColor(c)
        transparent.setAlpha(0)
        glow.setColorAt(0.3, glow_c)
        glow.setColorAt(1.0, transparent)
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(0, 0, w, h))

        # Círculo sólido centrado
        c.setAlpha(self._anim_alpha)
        p.setBrush(QBrush(c))
        m = max(1, w // 4)
        p.drawEllipse(QRectF(m, m, w - m * 2, h - m * 2))

        p.restore()
        p.end()


# ── NMPageHeader ──────────────────────────────────────────────────────────────


class NMPageHeader(ThemeAwareWidgetMixin, QWidget):
    """Header estándar para vistas/páginas del Hub.

    Eyebrow (CAPS secundario) + título serif h2, con slot de acciones
    a la derecha. Consolida el patrón NMSectionHeader + v3_font + action_row.

    Uso::
        hdr = NMPageHeader("Pacientes", "5 vinculados", modo=modo)
        hdr.add_action(btn_sync)
        layout.addWidget(hdr)
    """

    def __init__(self, eyebrow: str = "", title: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMPageHeader")
        self.setStyleSheet("background: transparent;")

        self._root = QHBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(V3_SP["xs"])
        text_col.setContentsMargins(0, 0, 0, 0)

        # OJO: SIEMPRE con parent y visibilidad DESPUÉS de addWidget.
        # setVisible(True) sobre un QLabel sin padre lo muestra un instante
        # como ventana top-level — ERA la "mini ventana titilante" del user feedback
        # (se recreaba en cada _refresh_all_views del Hub).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())

        self._title_lbl = QLabel(title or "", self)
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))

        text_col.addWidget(self._eyebrow_lbl)
        text_col.addWidget(self._title_lbl)
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        self._root.addLayout(text_col, stretch=1)

        self._action_row = QHBoxLayout()
        self._action_row.setSpacing(V3_SP["sm"])
        self._action_row.setContentsMargins(0, 0, 0, 0)
        self._action_row.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._root.addLayout(self._action_row)

        self._connect_theme()
        self._apply_theme(self._modo)

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def add_action(self, widget: QWidget) -> None:
        self._action_row.addWidget(widget, alignment=Qt.AlignmentFlag.AlignVCenter)

    def clear_actions(self) -> None:
        while self._action_row.count():
            item = self._action_row.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink2 = v3c("ink_secondary", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")


# ── NMListRow ─────────────────────────────────────────────────────────────────


class NMListRow(ThemeAwareWidgetMixin, QWidget):
    """Fila UI para listas internas: icono, título, subtítulo, trailing widget.

    Hover highlight, divider inferior opcional, click signal.
    Consolida patrones de fila dispares en Avisos, Pacientes y Registro.

    Uso::
        row = NMListRow("bell", "Medicación", "Salud · 08:00", modo=modo)
        row.set_trailing(NMBadge("Completado", modo=modo))
        row.clicked.connect(callback)
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        icon: str = "",
        title: str = "",
        subtitle: str = "",
        modo: str = None,
        parent=None,
        divider: bool = True,
        clickable: bool = True,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._divider = divider
        self._clickable = clickable
        self._hover = False
        self.setFixedHeight(56)
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], 0)
        root.setSpacing(V3_SP["md"])

        # Parent explícito + visibilidad post-addWidget: setVisible(True) en
        # un widget sin padre lo muestra un instante como top-level.
        self._icon_lbl = QLabel(self)
        self._icon_lbl.setFixedSize(20, 20)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        self._icon_name = icon
        if icon:
            try:
                # nm_icon devuelve QIcon — pedir el pixmap explícito (pasarlo
                # directo a setPixmap tiraba TypeError y caía a la letra).
                self._icon_lbl.setPixmap(
                    nm_icon(icon, v3c("ink_secondary", self._modo), size=16).pixmap(16, 16)
                )
            except Exception:
                self._icon_lbl.setText(icon[:1].upper())
        root.addWidget(self._icon_lbl)
        self._icon_lbl.setVisible(bool(icon))

        txt = QVBoxLayout()
        txt.setSpacing(1)
        txt.setContentsMargins(0, 0, 0, 0)
        self._title_lbl = QLabel(title or "", self)
        self._title_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle_lbl = QLabel(subtitle or "", self)
        self._subtitle_lbl.setFont(qfont("size_caption_xs"))
        txt.addWidget(self._title_lbl)
        txt.addWidget(self._subtitle_lbl)
        self._subtitle_lbl.setVisible(bool(subtitle))
        root.addLayout(txt, stretch=1)

        self._trailing_slot = QHBoxLayout()
        self._trailing_slot.setContentsMargins(0, 0, 0, 0)
        self._trailing_slot.setSpacing(V3_SP["xs"])
        root.addLayout(self._trailing_slot)

        self._connect_theme()
        self._apply_theme(self._modo)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def set_subtitle(self, text: str) -> None:
        self._subtitle_lbl.setText(text or "")
        self._subtitle_lbl.setVisible(bool(text))

    def set_trailing(self, widget: QWidget) -> None:
        while self._trailing_slot.count():
            item = self._trailing_slot.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self._trailing_slot.addWidget(widget)

    def set_divider(self, show: bool) -> None:
        self._divider = show
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self._hover and self._clickable:
            bg = QColor(v3c("surface2", self._modo))
            bg.setAlpha(120)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRect(0, 0, w, h)
        if self._divider:
            div_c = QColor(v3c("border", self._modo))
            div_c.setAlpha(60)
            p.setPen(QPen(div_c, 1))
            p.drawLine(V3_SP["lg"], h - 1, w - V3_SP["lg"], h - 1)
        p.end()

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        if self._icon_name and self._icon_lbl.isVisible():
            try:
                self._icon_lbl.setPixmap(
                    nm_icon(self._icon_name, v3c("ink_secondary", self._modo), size=16)
                )
            except Exception:
                pass
        self.update()


# ── NMRow ─────────────────────────────────────────────────────────────────────
# Runtime spec §2.7: fila genérica de lista con hover/selected/focus-visible.
# - hover:    bg surface_2
# - selected: bg primary_soft + barra vertical 3×18 primary
# - bottom border: 1px LINE (omitida en la última fila usando hide_divider)


class NMRow(QFrame):
    """Fila genérica de lista (runtime spec §2.7).

    Señales:
        clicked           — clic sobre la fila
        selected_changed  — cambio de estado selected (bool)

    Args:
        row_height:   Altura fija en px (default 56 Suite / 48 Hub).
        selectable:   Si True, clic marca la fila como selected.
        hide_divider: Si True, no dibuja el borde inferior (útil para la última fila).
    """

    clicked = pyqtSignal()
    selected_changed = pyqtSignal(bool)

    def __init__(
        self,
        parent=None,
        modo: str | None = None,
        row_height: int = 56,
        selectable: bool = True,
        hide_divider: bool = False,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = False
        self._hover = False
        self._selectable = selectable
        self._hide_divider = hide_divider

        self.setFixedHeight(row_height)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if selectable else Qt.CursorShape.ArrowCursor
        )
        _tm().theme_changed.connect(self._apply_theme)

    # ── API pública ────────────────────────────────────────────────────────────

    @property
    def selected(self) -> bool:
        return self._selected

    def set_selected(self, value: bool):
        if self._selected != value:
            self._selected = value
            self.update()
            self.selected_changed.emit(value)

    def set_hide_divider(self, hide: bool):
        self._hide_divider = hide
        self.update()

    # ── Interacción ───────────────────────────────────────────────────────────

    def enterEvent(self, event: QEnterEvent):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
            if self._selectable:
                self.set_selected(True)
        super().mouseReleaseEvent(event)

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        if self._selected:
            bg = v3c("primary_soft", self._modo)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(bg))
            p.drawRect(rect)
            # Barra vertical 3×18 PRIMARY a la izquierda
            bar_col = v3c("primary", self._modo)
            bar_y = (h - 18.0) / 2.0
            bar = QRectF(0, bar_y, 3, 18)
            p.setBrush(QBrush(bar_col))
            p.drawRoundedRect(bar, 1.5, 1.5)
        elif self._hover:
            bg = v3c("surface_2", self._modo)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(bg))
            p.drawRect(rect)

        # Focus ring (2px PRIMARY outline)
        if self.hasFocus():
            acc = v3c("primary", self._modo)
            acc.setAlpha(180)
            p.setPen(QPen(acc, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRectF(1, 1, w - 2, h - 2))

        # Divider inferior (1px LINE)
        if not self._hide_divider:
            border_c = v3c("line", self._modo)
            p.setPen(QPen(border_c, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(0, int(h) - 1, int(w), int(h) - 1)

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


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
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)
        self._logo_icon = QLabel()
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._logo_icon.setContentsMargins(12, 6, 12, 6)
        self._logo_icon.setStyleSheet("background: transparent;")
        self._section_title = QLabel(
            "Herramientas" if product.lower() == "suite" else "Panel Profesional"
        )
        self._section_title.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._section_title.setContentsMargins(12, 0, 12, 6)
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
        self._footer.setContentsMargins(10, 6, 10, 4)
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
                    self._logo_icon.setContentsMargins(0, 6, 0, 6)
                    self._logo_icon.setFixedHeight(40)
                    self._logo_icon.setPixmap(
                        nm_logo_pixmap(self._modo, tipo="icon", width=28, height=28)
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
                    self._logo_icon.setContentsMargins(12, 6, 12, 6)
                    self._logo_icon.setFixedHeight(44)
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
            btn.setFixedHeight(34)
            align = "center" if self._collapsed else "left"
            padding = "6px 0px" if self._collapsed else "6px 10px"
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
