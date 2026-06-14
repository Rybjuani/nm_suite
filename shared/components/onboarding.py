"""Install/uninstall flow widgets: step indicators and decision cards."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPaintEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import C, RADIUS_CARD, colors, label_style, norm_modo, qfont, sp


def _tm() -> ThemeManager:
    return ThemeManager.instance()


# ── NMInstallStepper ──────────────────────────────────────────────────────────


class NMInstallStepper(QWidget):
    """Stepper horizontal para instaladores y desinstaladores (3-5 pasos).

    Siempre usa dark mode (instaladores son siempre dark).
    Accent configurable: 'teal' para Suite, 'violet' para NeuroMood Hub.
    """

    def __init__(self, steps: list[str], current: int = 0, accent_key: str = "teal", parent=None):
        super().__init__(parent)
        self._steps = steps
        self._current = current
        self._accent_key = accent_key
        self._modo = "dark_hybrid"
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_step(self, idx: int):
        self._current = max(0, min(len(self._steps) - 1, idx))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        n = len(self._steps)
        if n == 0:
            p.restore()
            p.end()
            return

        w, _h = self.width(), self.height()
        circle_r = 12
        cy = 20
        step_w = w / n
        accent_key = {
            "error": "danger",
            "red": "danger",
            "destructive": "danger",
            "hub": "violet",
            "suite": "teal",
        }.get(self._accent_key, self._accent_key)
        accent = C(accent_key, self._modo)

        for i, label in enumerate(self._steps):
            cx = int(step_w * i + step_w / 2)

            if i > 0:
                prev_cx = int(step_w * (i - 1) + step_w / 2)
                lc = QColor(accent if i <= self._current else C("border", self._modo))
                p.setPen(QPen(lc, 2))
                p.drawLine(prev_cx + circle_r, cy, cx - circle_r, cy)

            circ_rect = QRectF(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
            if i < self._current:
                p.setBrush(QBrush(QColor(accent)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QPen(QColor(C("text_on_accent", self._modo)), 2))
                p.setFont(qfont("size_caption", bold=True))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, "✓")
            elif i == self._current:
                p.setBrush(QBrush(QColor(accent)))
                p.setPen(QPen(QColor(C("bg_primary", self._modo)), 2))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(C("text_on_accent", self._modo)))
                p.setFont(qfont("size_caption", bold=True))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(C("border", self._modo)), 1))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(C("text_tertiary", self._modo)))
                p.setFont(qfont("size_caption"))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            col = "text_primary" if i == self._current else "text_tertiary"
            p.setPen(QColor(C(col, self._modo)))
            p.setFont(qfont("size_caption"))
            p.drawText(
                QRectF(cx - step_w / 2 + 4, cy + circle_r + 4, step_w - 8, 14),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )


# ── NMDataPreserveCard ────────────────────────────────────────────────────────


class NMDataPreserveCard(QWidget):
    """Card de decisión crítica para desinstaladores.

    Muestra ícono de advertencia + título + descripción + toggle switch gradient.
    Emite toggled(bool). Siempre dark mode.
    """

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, description: str, checked: bool = True, parent=None):
        super().__init__(parent)
        self._modo = "dark_hybrid"
        self._checked = checked
        self.setObjectName("NMDataPreserveCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("lg"), sp("md"), sp("lg"), sp("md"))
        lay.setSpacing(sp("sm"))

        # Warning header
        header = QHBoxLayout()
        warn = QLabel("⚠️")
        warn.setFont(qfont("size_h3"))
        warn.setStyleSheet("background: transparent;")
        header.addWidget(warn)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_body", bold=True))
        self._title_lbl.setStyleSheet(
            f"color: {C('warning', self._modo)}; background: transparent;"
        )
        header.addWidget(self._title_lbl, stretch=1)
        lay.addLayout(header)

        self._desc_lbl = QLabel(description)
        self._desc_lbl.setFont(qfont("size_small"))
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._desc_lbl)

        # Toggle row
        toggle_row = QHBoxLayout()
        self._state_lbl = QLabel("Activado" if checked else "Desactivado")
        self._state_lbl.setFont(qfont("size_small", bold=True))
        self._state_lbl.setStyleSheet("background: transparent;")
        toggle_row.addWidget(self._state_lbl, stretch=1)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedSize(52, 28)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle)
        toggle_row.addWidget(self._toggle_btn)
        lay.addLayout(toggle_row)

        self._apply_theme(self._modo)

    def _toggle(self):
        self._checked = not self._checked
        self._state_lbl.setText("Activado" if self._checked else "Desactivado")
        self._apply_theme(self._modo)
        self.toggled.emit(self._checked)

    def is_checked(self) -> bool:
        return self._checked

    def _apply_theme(self, modo: str = None):
        c = colors(self._modo)
        self.setStyleSheet(
            f"QWidget#NMDataPreserveCard {{ "
            f"background: {c['bg_surface']}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {C('warning', self._modo)}; }}"
        )
        self._desc_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))
        if self._checked:
            self._toggle_btn.setText("✓")
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {C('teal', self._modo)}, stop:1 {C('accent', self._modo)}); "
                f"color: {C('text_on_accent', self._modo)}; font-weight: 500; "
                f"border-radius: 14px; border: none; min-height: 0px; padding: 0px; }}"
            )
            self._state_lbl.setStyleSheet(
                f"color: {C('teal', self._modo)}; background: transparent;"
            )
        else:
            self._toggle_btn.setText("")
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{ background: {c['bg_elevated']}; "
                f"border-radius: 14px; border: 1px solid {c['border']}; "
                f"min-height: 0px; padding: 0px; }}"
            )
            self._state_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
