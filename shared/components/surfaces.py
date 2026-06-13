"""Surface primitives shared by Suite and Hub."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import C, nm_icon, norm_modo, pill_radius, v3_font, v3c


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
    "info": "accent",  # primary (sage/lavender)
    "positive": "success",
    "completed": "success",  # variante literal de la lámina de componentes
    "patient": "teal",  # identificación de paciente sin inventar semántica clínica
    "warn": "warning",
    "warning": "warning",  # alias
    "danger": "danger",
    "critical": "danger",
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
    """Pill semántica del runtime spec §4.4.

    Args:
        text:   Etiqueta. Puede incluir un símbolo unicode a la izquierda.
        tone:   ``"neutral"`` / ``"info"`` / ``"completed"`` /
                ``"warning"`` / ``"critical"`` / ``"patient"``.
        modo:   Override; ``None`` = sigue ThemeManager.
        parent: parent widget.

    Para añadir ícono SVG real, usar ``NMIcon`` en un layout horizontal y
    poner el ``NMBadge`` al lado — el runtime spec acepta rich text via QLabel
    pero la composición externa es más mantenible.
    """

    def __init__(self, text: str = "", tone: str = "neutral", modo: str | None = None, parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone if tone in _BADGE_TONE_TO_KEY else "neutral"
        self.setObjectName("NMBadge")
        self.setFont(v3_font("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(24)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def set_tone(self, tone: str):
        if tone in _BADGE_TONE_TO_KEY:
            self._tone = tone
            self._apply_style()

    def tone(self) -> str:
        return self._tone

    def _apply_style(self):
        key = _BADGE_TONE_TO_KEY[self._tone]
        color_hex = C(key, self._modo)
        # Soft bg: rgba a 14% del color semántico (consistente con runtime spec §4.4).
        fc = QColor(color_hex)
        fc.setAlpha(36)  # ~14%
        bg_css = f"rgba({fc.red()},{fc.green()},{fc.blue()},{fc.alpha()})"
        border_alpha = QColor(color_hex)
        border_alpha.setAlpha(60)
        border_css = (
            f"rgba({border_alpha.red()},{border_alpha.green()},"
            f"{border_alpha.blue()},{border_alpha.alpha()})"
        )
        self._pill_r_applied = pill_radius(self, fallback=26)
        self.setStyleSheet(f"""
            NMBadge {{
                color: {color_hex};
                background-color: {bg_css};
                border: 1px solid {border_css};
                border-radius: {self._pill_r_applied}px;
                padding: 4px 12px;
                min-height: 24px;
            }}
        """)
        # Una pill nunca debe renderizar texto recortado ni pisarse con su
        # vecina. Medir con QFontMetrics y NO con sizeHint(): el sizeHint del
        # QLabel depende de que el QSS esté "polished", y cuando la pill se
        # re-estila después del primer layout (theme apply) el mínimo crecía
        # tarde — el widget se ensanchaba sin que el QHBoxLayout reposicionara
        # a los hermanos → pills superpuestas (bug real: "Sin alerta activa"
        # pisada por "Progreso 5d" en el hero del detalle del Hub).
        # 26 = padding QSS 12+12 + borde 1+1.
        self._sync_min_width()

    def _sync_min_width(self):
        fm = QFontMetrics(self.font())
        self.setMinimumWidth(fm.horizontalAdvance(self.text()) + 26)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=26) != getattr(self, "_pill_r_applied", None):
            self._apply_style()

    def setText(self, text: str):  # noqa: N802 — override de QLabel
        super().setText(text)
        self._sync_min_width()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()
