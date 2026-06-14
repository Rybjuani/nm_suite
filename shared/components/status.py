"""Status/badge widgets: chips, dots, banners, phase chips, calm badge."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QPointF,
    QRectF,
    Qt,
    QTimer,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from shared.theme_manager import ThemeManager
from shared.theme import TYPOGRAPHY, V3_DARK, V3_LIGHT
from shared.theme_qt import (
    C,
    RADIUS_BUTTON,
    RADIUS_CARD,
    SIZE_TIME_LARGE,
    V3_RD,
    V3_SP,
    norm_modo,
    pill_radius,
    qcolor_to_rgba_css,
    qfont,
    qfont_mono,
    sp,
    v3c,
)
from shared.components.surfaces import NMBadge
from shared.components.session import _rgba


def _tm() -> ThemeManager:
    return ThemeManager.instance()


# ── NMStatusDot ──────────────────────────────────────────────────────────────
# Runtime spec §3 / tokens.css `.nm-status-dot`: punto de estado 8 px con halo
# suave (positive/warn/danger). Sirve para footer de sidebar y barras de
# estado interno. Cubre los tres tonos del runtime spec usando los keys semánticos
# del tema existente — NO introduce paleta nueva.

_STATUS_DOT_TONE_TO_KEY = {
    "ok": "success",
    "positive": "success",
    "warn": "warning",
    "warning": "warning",
    "danger": "danger",
    "error": "danger",
}


class NMStatusDot(QWidget):
    """Punto de estado con halo suave (runtime spec §3 + tokens `.nm-status-dot`).

    El punto sólido es de 8 px; el widget total es 16 px para hospedar el
    halo radial al estilo del CSS original. Tonos soportados:
    ``"ok" | "warn" | "danger"`` (alias: ``positive | warning | error``).
    """

    def __init__(self, tone: str = "ok", modo: str | None = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone if tone in _STATUS_DOT_TONE_TO_KEY else "ok"
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        _tm().theme_changed.connect(self._apply_theme)

    def set_tone(self, tone: str):
        if tone in _STATUS_DOT_TONE_TO_KEY:
            self._tone = tone
            self.update()

    def tone(self) -> str:
        return self._tone

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, _ev):  # noqa: N802 (Qt API)
        key = _STATUS_DOT_TONE_TO_KEY[self._tone]
        color = QColor(C(key, self._modo))
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        # Halo radial (alpha decreciente) de 14 px
        halo = QRadialGradient(QPointF(cx, cy), 7.0)
        halo_c = QColor(color)
        halo_c.setAlpha(70)
        halo.setColorAt(0.0, halo_c)
        edge = QColor(color)
        edge.setAlpha(0)
        halo.setColorAt(1.0, edge)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(cx, cy), 7.0, 7.0)
        # Punto sólido 8 px
        p.setBrush(QBrush(color))
        p.drawEllipse(QPointF(cx, cy), 4.0, 4.0)
        p.end()


class NMStatusChip(QLabel):
    """Pill pequeña con color semántico y texto. Usa tokens del tema."""

    def __init__(
        self, text: str = "", color_key: str = "success", modo: str = "dark_hybrid", parent=None
    ):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._color_key = color_key
        self.setFont(qfont("size_caption"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(22)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        color_hex = C(self._color_key, self._modo)
        is_dark = "dark" in self._modo
        # Soft semantic bg: use the Soft variant of the color key if available
        soft_key = self._color_key + "Soft"
        soft_c = (
            v3c(soft_key, self._modo) if soft_key in (V3_DARK if is_dark else V3_LIGHT) else None
        )
        if soft_c is not None:
            bg_css = f"rgba({soft_c.red()},{soft_c.green()},{soft_c.blue()},{soft_c.alpha()})"
        else:
            # Fallback: 10% of the semantic color
            fc = QColor(color_hex)
            fc.setAlpha(26)  # ~10%
            bg_css = f"rgba({fc.red()},{fc.green()},{fc.blue()},26)"
        self._pill_r_applied = pill_radius(self, fallback=22)
        self.setStyleSheet(f"""
            NMStatusChip {{
                color: {color_hex};
                background-color: {bg_css};
                border: 1px solid {color_hex};
                border-radius: {self._pill_r_applied}px;
                padding: 2px 10px;
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=22) != getattr(self, "_pill_r_applied", None):
            self._apply_style()

    def set_color(self, color_key: str):
        self._color_key = color_key
        self._apply_style()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


class NMStatusBanner(QFrame):
    """Banner sereno de estado operativo para pantallas de configuracion."""

    _TONES = {
        "ok": ("positive", "Conectado"),
        "syncing": ("patient", "Verificando"),
        "idle": ("neutral", "Pendiente"),
        "error": ("danger", "Revisar conexion"),
    }

    def __init__(
        self,
        title: str,
        detail: str = "",
        tone: str = "idle",
        action: QWidget | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone
        self.setObjectName("NMStatusBanner")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["md"])

        self._dot = NMStatusDot(tone="ok", modo=self._modo, parent=self)
        lay.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(2)
        self._title = QLabel(title)
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._detail = QLabel(detail)
        self._detail.setWordWrap(True)
        self._detail.setFont(qfont("size_caption"))
        text.addWidget(self._title)
        text.addWidget(self._detail)
        lay.addLayout(text, stretch=1)

        self._badge = NMBadge("", tone="patient", modo=self._modo)
        lay.addWidget(self._badge, alignment=Qt.AlignmentFlag.AlignTop)
        if action is not None:
            lay.addWidget(action, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.set_tone(tone)
        _tm().theme_changed.connect(self._apply_theme)

    def set_status(self, title: str, detail: str, tone: str):
        self._title.setText(title)
        self._detail.setText(detail)
        self.set_tone(tone)

    def set_tone(self, tone: str):
        self._tone = tone if tone in self._TONES else "idle"
        dot_tone = (
            "danger" if self._tone == "error" else ("warn" if self._tone == "syncing" else "ok")
        )
        self._dot.set_tone(dot_tone)
        badge_variant, badge_text = self._TONES[self._tone]
        self._badge.setText(badge_text)
        self._badge.set_tone(badge_variant)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg_key = "surface2" if is_dark else "surface2"
        bg = v3c(bg_key, self._modo)
        border = v3c("border", self._modo)
        if self._tone == "error":
            border = v3c("danger", self._modo)
            border.setAlpha(130)
        else:
            border.setAlpha(150)
        self.setStyleSheet(
            f"QFrame#NMStatusBanner {{ background: {bg.name()}; "
            f"border: 1px solid rgba({border.red()},{border.green()},{border.blue()},{border.alpha()}); "
            f"border-radius: {V3_RD['xl']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._detail.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )


class NMPhaseChip(QWidget):
    """Fila de 3 chips de fase para la respiración: Inhala / Mantén / Exhala.

    El chip activo se ilumina con fondo teal. Llama a set_phase(key).
    keys: 'inhala' | 'manten' | 'exhala' | None
    """

    _PHASES = [
        ("Inhala ↑ 4s", "inhala"),
        ("Mantén 7s", "manten"),
        ("Exhala ↓ 8s", "exhala"),
    ]

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active: str | None = None
        self._chips: dict[str, QLabel] = {}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(sp("sm"))

        for label, key in self._PHASES:
            chip = QLabel(label)
            chip.setFont(qfont("size_small"))
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setFixedHeight(32)
            chip.setMinimumWidth(90)
            chip.setContentsMargins(12, 0, 12, 0)
            self._chips[key] = chip
            lay.addWidget(chip)

        lay.addStretch()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_phase(self, phase: str | None):
        self._active = phase
        self._apply_theme(self._modo)

    _PHASE_COLOR_KEY = {
        "inhala": "teal",
        "manten": "accent",
        "exhala": "violet",
    }

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for key, chip in self._chips.items():
            active = key == self._active
            phase_color = C(self._PHASE_COLOR_KEY.get(key, "teal"), self._modo)
            if active:
                bg = phase_color
                col = v3c("textOnSolid", self._modo).name()
                border = phase_color
            else:
                # Estado preview: tint suave del color de fase + texto del color
                bg = _rgba(phase_color, 0.12)
                col = phase_color
                border = _rgba(phase_color, 0.25)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {bg};
                    color: {col};
                    border: 1px solid {border};
                    border-radius: {RADIUS_BUTTON}px;
                    font-size: {TYPOGRAPHY["size_small"]}px;
                    font-weight: {"500" if active else "400"};
                }}
            """)


class NMCalmBadge(QWidget):
    """Badge decorativo 'Calm ♥ / N BPM' para la columna derecha de Respiración."""

    def __init__(self, bpm: int = 60, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._bpm = bpm
        self._blink_alpha = 255
        self._blink_dir = -1
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(80)
        self._blink_timer.timeout.connect(self._on_blink)
        self._blink_timer.start()
        self.setObjectName("NMCalmBadge")
        # WA_StyledBackground=True para que el QSS bg/border aplique al widget
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(100)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("sm"), sp("md"), sp("sm"), sp("md"))
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._calm_lbl = QLabel("Calm ♥")
        self._calm_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._calm_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._calm_lbl)

        self._bpm_lbl = QLabel(str(bpm))
        self._bpm_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bpm_lbl.setFont(qfont_mono(SIZE_TIME_LARGE, bold=True))
        lay.addWidget(self._bpm_lbl)

        self._unit_lbl = QLabel("BPM")
        self._unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unit_lbl.setFont(qfont("size_caption"))
        lay.addWidget(self._unit_lbl)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_bpm(self, bpm: int):
        self._bpm = bpm
        self._bpm_lbl.setText(str(bpm))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        violet = C("violet", self._modo)
        # Selector específico #NMCalmBadge para evitar herencia del border a hijos
        # (sin esto, cada QLabel hijo se renderizaba con su propio border = chips
        # fragmentados visualmente)
        self.setStyleSheet(
            f"QWidget#NMCalmBadge {{ background: {v3c('elevated', self._modo).name()}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; }}"
            f"QWidget#NMCalmBadge QLabel {{ background: transparent; border: none; }}"
        )
        self._calm_lbl.setStyleSheet(f"color: {violet};")
        self._bpm_lbl.setStyleSheet(f"color: {violet};")
        self._unit_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )

    def _on_blink(self):
        if sip.isdeleted(self):
            self._blink_timer.stop()
            return
        self._blink_alpha += self._blink_dir * 12
        if self._blink_alpha <= 80:
            self._blink_dir = 1
            self._blink_alpha = 80
        elif self._blink_alpha >= 255:
            self._blink_dir = -1
            self._blink_alpha = 255
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(C("violet", self._modo))
        c.setAlpha(self._blink_alpha)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(self.width() - 14, 8, 6, 6))
        p.end()
