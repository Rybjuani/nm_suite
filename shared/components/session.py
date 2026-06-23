"""Session/activity UI components: checklists, activity cards, preset chips, history."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shared.theme_manager import ThemeManager
from shared.theme import CATEGORY_COLORS, TYPOGRAPHY
from shared.theme_qt import (
    ANIM,
    C,
    RADIUS_CARD,
    RADIUS_INPUT,
    RADIUS_BUTTON,
    RADIUS_PILL,
    V3_RD,
    V3_SP,
    colors,
    label_style,
    nm_icon,
    norm_modo,
    pill_radius,
    qcolor_to_rgba_css,
    qfont,
    sp,
    v3c,
)
from shared.components.buttons import NMButton, _NM_CONTROL_HEIGHT
from shared.components.surfaces import NMSyncOrb


def _tm() -> ThemeManager:
    return ThemeManager.instance()


def _rgba(hex_color: str, alpha: float) -> str:
    c = QColor(hex_color)
    a = max(0, min(255, int(alpha * 255)))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a})"


# ═══════════════════════════════════════════════════════════════════════════════
# NMCustomCheck / NMActivityCard / Timer helpers

_NM_RT_CHECK_SIZE = 22
_NM_RT_CHECK_RADIUS = 7
_NM_RT_CHECK_BORDER = 2.0


class _NMAnimCheckBox(QWidget):
    """Caja 22×22 con checkmark que se dibuja progresivamente (220ms OutCubic).

    Uso interno de NMCustomCheck. No usar directamente.
    """

    # Geometría del checkmark del mockup `.rt-cb` (path M5 12l4 4 10-10).
    _P0 = (5.0, 12.0)   # inicio (izquierda)
    _P1 = (9.0, 16.0)   # vértice inferior (punto de quiebre)
    _P2 = (19.0, 6.0)   # final (derecha arriba)

    import math as _math
    _SEG1 = _math.sqrt((_P1[0]-_P0[0])**2 + (_P1[1]-_P0[1])**2)  # ≈ 5.66
    _SEG2 = _math.sqrt((_P2[0]-_P1[0])**2 + (_P2[1]-_P1[1])**2)  # ≈ 12.81
    _TOTAL = _SEG1 + _SEG2
    _T1 = _SEG1 / _TOTAL   # ≈ 0.306 — fracción donde termina el primer trazo

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._checked = False
        self._draw_t = 0.0
        self._anim: QPropertyAnimation | None = None
        self.setFixedSize(_NM_RT_CHECK_SIZE, _NM_RT_CHECK_SIZE)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    # ── pyqtProperty animable ─────────────────────────────────────────────────

    def _get_draw_t(self) -> float:
        return self._draw_t

    def _set_draw_t(self, v: float) -> None:
        self._draw_t = max(0.0, min(1.0, v))
        self.update()

    draw_t = pyqtProperty(float, _get_draw_t, _set_draw_t)

    # ── API ───────────────────────────────────────────────────────────────────

    def set_checked_animated(self, checked: bool) -> None:
        """Marcar con animación (uso en interacción del usuario)."""
        self._checked = checked
        if checked:
            self._draw_t = 0.0
            if self._anim:
                try:
                    self._anim.stop()
                except RuntimeError:
                    pass
            a = QPropertyAnimation(self, b"draw_t", self)
            a.setDuration(ANIM["medium"])
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.Type.OutCubic)
            a.finished.connect(lambda: setattr(self, "_anim", None))
            self._anim = a
            a.start()
        else:
            if self._anim:
                try:
                    self._anim.stop()
                except RuntimeError:
                    pass
                self._anim = None
            self._draw_t = 0.0
            self.update()

    def set_checked_instant(self, checked: bool) -> None:
        """Establecer estado sin animación (inicialización programática)."""
        if self._anim:
            try:
                self._anim.stop()
            except RuntimeError:
                pass
            self._anim = None
        self._checked = checked
        self._draw_t = 1.0 if checked else 0.0
        self.update()

    def set_modo(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self.update()

    # ── render ────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        border_col = v3c("primary" if self._checked else "line", self._modo)
        bg_col = v3c("primary" if self._checked else "surface", self._modo)

        p.setPen(QPen(border_col, _NM_RT_CHECK_BORDER))
        p.setBrush(QBrush(bg_col))
        box_rect = QRectF(
            _NM_RT_CHECK_BORDER / 2,
            _NM_RT_CHECK_BORDER / 2,
            _NM_RT_CHECK_SIZE - _NM_RT_CHECK_BORDER,
            _NM_RT_CHECK_SIZE - _NM_RT_CHECK_BORDER,
        )
        p.drawRoundedRect(box_rect, _NM_RT_CHECK_RADIUS, _NM_RT_CHECK_RADIUS)

        if self._checked and self._draw_t > 0.001:
            ink = v3c("primary_ink", self._modo)
            ck_width = 2.2
            pen = QPen(ink, ck_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)

            t = self._draw_t
            x0, y0 = self._P0
            x1, y1 = self._P1
            x2, y2 = self._P2

            if t <= self._T1:
                prog = t / max(1e-9, self._T1)
                p.drawLine(QPointF(x0, y0), QPointF(x0 + (x1-x0)*prog, y0 + (y1-y0)*prog))
            else:
                p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
                prog = (t - self._T1) / max(1e-9, 1.0 - self._T1)
                p.drawLine(QPointF(x1, y1), QPointF(x1 + (x2-x1)*prog, y1 + (y2-y1)*prog))

        p.end()


class NMCustomCheck(QWidget):
    """Checklist row matching the HTML `.check-item` / `.cbox` pattern."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        text: str,
        checked: bool = False,
        modo: str = None,
        parent=None,
        strike_on_check: bool = True,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._checked = checked
        self._strike_on_check = strike_on_check
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(_NM_CONTROL_HEIGHT)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, V3_SP["sm"], 0, V3_SP["sm"])
        lay.setSpacing(V3_SP["md"])
        # Checkbox a la IZQUIERDA del texto, como el mockup canónico (antes el box
        # iba a la derecha). El label ocupa el resto del ancho con stretch.
        self._box = _NMAnimCheckBox(self._modo)
        lay.addWidget(self._box)
        self._label = QLabel(text)
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        lay.addWidget(self._label, stretch=1)
        self.setAccessibleName(text)
        if checked:
            self._box.set_checked_instant(True)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_checked(self, checked: bool):
        self._checked = checked
        self._box.set_checked_instant(checked)
        self._apply_theme(self._modo)

    def is_checked(self) -> bool:
        return self._checked

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self.set_checked(checked)

    def setText(self, text: str):
        self._label.setText(text)

    def text(self) -> str:
        return self._label.text()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._checked = not self._checked
            self._box.set_checked_animated(self._checked)
            self._apply_theme(self._modo)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        try:
            from shared.theme_qt import v3c
            text_col = (
                v3c("ink_secondary", self._modo).name()
                if self._checked
                else v3c("text2", self._modo).name()
            )
        except ImportError:
            text_col = C("text_secondary", self._modo)

        self._box.set_modo(self._modo)
        decoration = "line-through" if self._checked and self._strike_on_check else "none"
        self._label.setStyleSheet(
            f"color: {text_col}; background: transparent; text-decoration: {decoration};"
        )


class NMActivityCard(QFrame):
    """Tarjeta de actividad recomendada con barra de acento lateral.

    Señales:
        completed(): el usuario marcó la actividad como completada.
        skipped():   el usuario descartó la sugerencia.
    """

    completed = pyqtSignal()
    skipped = pyqtSignal()

    def __init__(
        self,
        title: str,
        description: str = "",
        category: str = "other",
        completed: bool = False,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._category = category
        self._completed = completed
        self._accent = CATEGORY_COLORS.get(category, C("accent", self._modo))
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 12, 12)
        lay.setSpacing(5)
        self._name_lbl = QLabel(title)
        self._name_lbl.setFont(qfont("size_small", bold=True))
        lay.addWidget(self._name_lbl)
        self._desc_lbl = QLabel(description)
        self._desc_lbl.setFont(qfont("size_caption"))
        self._desc_lbl.setWordWrap(True)
        lay.addWidget(self._desc_lbl)
        row = QHBoxLayout()
        row.setContentsMargins(0, 3, 0, 0)
        row.setSpacing(6)
        self._yes_btn = QPushButton()
        self._yes_btn.setFixedHeight(24)
        self._yes_btn.clicked.connect(self._complete)
        row.addWidget(self._yes_btn)
        self._no_btn = QPushButton("× No es para mi")
        self._no_btn.setFixedHeight(24)
        self._no_btn.clicked.connect(lambda _=False: self.skipped.emit())
        row.addWidget(self._no_btn)
        row.addStretch()
        lay.addLayout(row)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _complete(self):
        self.set_completed(True)
        self.completed.emit()
        # Flash del botón: dim → bright (feedback táctil sin overlay)
        fx = QGraphicsOpacityEffect(self._yes_btn)
        self._yes_btn.setGraphicsEffect(fx)
        a = QPropertyAnimation(fx, b"opacity", self._yes_btn)
        a.setDuration(ANIM["fast"])
        a.setKeyValueAt(0.0, 1.0)
        a.setKeyValueAt(0.35, 0.35)
        a.setKeyValueAt(1.0, 1.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.finished.connect(lambda: self._yes_btn.setGraphicsEffect(None)
                           if not sip.isdeleted(self._yes_btn) else None)
        a.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def set_completed(self, completed: bool):
        self._completed = completed
        self._apply_theme(self._modo)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS_CARD, RADIUS_CARD)
        p.fillPath(path, QColor(c["bg_surface"]))
        p.setPen(QPen(QColor(c.get("border_card", c["border"])), 1))
        p.drawPath(path)
        bar = QPainterPath()
        bar.addRoundedRect(QRectF(0, 0, 3, self.height()), 3, 3)
        p.fillPath(bar, QColor(self._accent))
        if self._completed:
            p.fillPath(path, QColor(0, 0, 0, 80 if "dark" in self._modo else 20))
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self._name_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
        self._desc_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._yes_btn.setText("✓ Completado" if self._completed else "✓ Hice esto")
        self._yes_btn.setStyleSheet(
            f"QPushButton {{ background: {_rgba(self._accent, 0.14)}; color: {self._accent}; "
            f"border: none; border-radius: 8px; padding: 4px 12px; "
            f"font-size: {TYPOGRAPHY['size_caption']}px; font-weight: 500; }}"
        )
        self._no_btn.setVisible(not self._completed)
        self._no_btn.setStyleSheet(
            f"QPushButton {{ background: {c['bg_elevated']}; color: {c['text_tertiary']}; "
            f"border: none; border-radius: 8px; padding: 4px 12px; "
            f"font-size: {TYPOGRAPHY['size_caption']}px; font-weight: 500; }}"
        )
        self.update()


class NMPresetChip(QPushButton):
    """Chip de preset del timer."""

    def __init__(self, text: str, active: bool = False, modo: str = None, parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active = active
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_small"))
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_active(self, active: bool):
        self._active = active
        self._apply_theme(self._modo)

    def is_active(self) -> bool:
        return self._active

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        accent_hex = C("accent", self._modo)
        if self._active:
            bg = _rgba(accent_hex, 0.13 if is_dark else 0.10)
            border = _rgba(accent_hex, 0.32 if is_dark else 0.28)
            col = accent_hex
        else:
            bg = "transparent"
            bdr_c = v3c("border", self._modo)
            border = f"rgba({bdr_c.red()},{bdr_c.green()},{bdr_c.blue()},180)"
            col = v3c("text2", self._modo).name()  # was text_tertiary — too dim
        # Hover: elevated surface + full text contrast
        elev_c = v3c("elevated" if not is_dark else "elevatedSolid", self._modo)
        hover_bg = (
            f"rgba({elev_c.red()},{elev_c.green()},{elev_c.blue()},200)"
            if not is_dark
            else elev_c.name()
        )
        text_hex = v3c("text", self._modo).name()
        self._pill_r_applied = pill_radius(self, fallback=30)
        self.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {col}; border: 1px solid {border}; "
            f"border-radius: {self._pill_r_applied}px; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {hover_bg}; color: {text_hex}; }}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=30) != getattr(self, "_pill_r_applied", None):
            self._apply_theme(self._modo)


class NMSessionHistory(QWidget):
    """Footer de chips de sesiones de hoy."""

    def __init__(self, title: str = "Sesiones de hoy", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(7)
        self._label = QLabel(title)
        self._label.setFont(qfont("size_caption"))
        lay.addWidget(self._label)
        self._row = QHBoxLayout()
        self._row.setSpacing(6)
        self._row.addStretch()
        lay.addLayout(self._row)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_sessions(self, sessions: list[str]):
        while self._row.count() > 1:
            item = self._row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for text in sessions:
            chip = QLabel(text)
            chip.setFont(qfont("size_caption"))
            chip.setContentsMargins(11, 4, 11, 4)
            chip.setStyleSheet(self._chip_style())
            self._row.insertWidget(self._row.count() - 1, chip)

    def _chip_style(self) -> str:
        c = colors(self._modo)
        return (
            f"QLabel {{ background: {c['bg_elevated']}; color: {c['text_tertiary']}; "
            f"border: 1px solid {c.get('border_card', c['border'])}; "
            f"border-radius: 10px; padding: 4px 11px; }}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(f"border-top: 1px solid {C('border', self._modo)};")
        self._label.setStyleSheet(label_style(self._modo, "text_tertiary"))
        for chip in self.findChildren(QLabel):
            if chip is not self._label:
                chip.setStyleSheet(self._chip_style())


# COMPONENTES V3 — Design System Mayo 2026
# ═══════════════════════════════════════════════════════════════════════════════

# ── NMStreakBadge ─────────────────────────────────────────────────────────────


class NMStreakBadge(QLabel):
    """Pill badge de racha diaria — paleta brand teal, sin emoji.

    Muestra '● N días' con color teal y fondo accent_soft.
    Se oculta automáticamente si days <= 0.
    """

    def __init__(self, days: int = 0, modo: str = None, parent=None):
        super().__init__(parent)
        self._days = days
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(10, 0, 10, 0)
        self._update_text()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_days(self, days: int):
        self._days = days
        self._update_text()
        self._apply_theme(self._modo)

    def _update_text(self):
        if self._days <= 0:
            self.setText("")
            self.hide()
        else:
            suffix = "s" if self._days != 1 else ""
            self.setText(f"●  {self._days} día{suffix}")
            self.show()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        teal = v3c("teal", self._modo)
        bg = v3c("accent_soft", self._modo)
        border_c = QColor(teal)
        border_c.setAlpha(70)
        self._pill_r_applied = pill_radius(self, fallback=22)
        self.setStyleSheet(f"""
            QLabel {{
                color: {teal.name()};
                background-color: {bg.name()};
                border-radius: {self._pill_r_applied}px;
                border: 1px solid rgba({border_c.red()},{border_c.green()},{border_c.blue()},70);
                padding: 1px 10px;
                font-size: {TYPOGRAPHY["size_small"]}px;
                font-weight: 500;
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=22) != getattr(self, "_pill_r_applied", None):
            self._apply_theme(self._modo)


# ── NMWelcomeBar ──────────────────────────────────────────────────────────────


class NMWelcomeBar(QWidget):
    """Tarjeta de bienvenida accent: '✨ Bienvenida de vuelta / ¿Empezamos?'.

    Se usa debajo del saludo en HomeView.
    """

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(sp("md"), sp("sm"), sp("md"), sp("sm"))
        lay.setSpacing(sp("sm"))

        icon_lbl = QLabel("✨")
        icon_lbl.setFont(qfont("size_h3"))
        icon_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = QLabel("Bienvenida de vuelta")
        self._title_lbl.setFont(qfont("size_small", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        text_col.addWidget(self._title_lbl)

        self._sub_lbl = QLabel("Tu última sesión fue ayer. ¿Empezamos?")
        self._sub_lbl.setFont(qfont("size_caption"))
        self._sub_lbl.setStyleSheet("background: transparent;")
        text_col.addWidget(self._sub_lbl)

        lay.addLayout(text_col, stretch=1)

        self._action_lbl = QLabel("Comenzar →")
        self._action_lbl.setFont(qfont("size_caption", bold=True))
        self._action_lbl.setStyleSheet("background: transparent;")
        self._action_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self._action_lbl)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def refresh(self):
        pass

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        accent = C("accent", self._modo)
        c = QColor(accent)
        bg_r, bg_g, bg_b = c.red(), c.green(), c.blue()
        self.setStyleSheet(f"""
            NMWelcomeBar {{
                background-color: rgba({bg_r},{bg_g},{bg_b},20);
                border: 1px solid rgba({bg_r},{bg_g},{bg_b},51);
                border-radius: {RADIUS_INPUT}px;
            }}
        """)
        self._title_lbl.setStyleSheet(f"color: {accent}; background: transparent;")
        self._sub_lbl.setStyleSheet(
            f"color: {C('text_tertiary', self._modo)}; background: transparent;"
        )
        self._action_lbl.setStyleSheet(f"color: {accent}; background: transparent;")


# ── NMFormField ────────────────────────────────────────────────────────────────


class NMFormField(QWidget):
    """Label + input en fila horizontal, con espaciado consistente."""

    def __init__(
        self, label: str = "", widget: QWidget = None, modo: str = "dark_hybrid", parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setFont(qfont("size_body"))
        self._label.setStyleSheet(label_style(self._modo, "text_secondary"))
        self._label.setMinimumWidth(55)
        layout.addWidget(self._label)

        if widget:
            layout.addWidget(widget, stretch=1)
        layout.addStretch()
        _tm().theme_changed.connect(self._apply_theme)

    def label(self) -> QLabel:
        return self._label

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._label.setStyleSheet(label_style(self._modo, "text_secondary"))

# ── NMTCCStepper ──────────────────────────────────────────────────────────────


class NMTCCStepper(QWidget):
    """Stepper horizontal de N pasos para el asistente TCC (y cualquier wizard).

    Estado por paso: pasado=verde+check, activo=accent, futuro=gris.
    """

    def __init__(self, steps: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._steps = steps
        self._current = 0
        self.setFixedHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_step(self, idx: int):
        self._current = max(0, min(len(self._steps) - 1, idx))
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
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
        circle_r = 14
        cy = 22
        step_w = w / n

        for i, label in enumerate(self._steps):
            cx = int(step_w * i + step_w / 2)

            # Connector line — F3+F5 runtime: tramo completado en `primary`
            # SÓLIDO vía token (el gradiente lavanda→ámbar anterior tenía los
            # 6 hex duros acá y "lo lineal va plano"; gradiente queda solo en
            # lo circular/identitario).
            if i > 0:
                prev_cx = int(step_w * (i - 1) + step_w / 2)
                if i <= self._current:
                    p.setPen(QPen(QColor(v3c("primary", self._modo)), 2))
                else:
                    p.setPen(QPen(QColor(v3c("borderSoft", self._modo)), 2))
                p.drawLine(prev_cx + circle_r, cy, cx - circle_r, cy)

            # Circle
            circ_rect = QRectF(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
            if i < self._current:
                p.setBrush(QBrush(QColor(v3c("teal", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QPen(QColor(v3c("textOnSolid", self._modo)), 2))
                p.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, "✓")
            elif i == self._current:
                p.setBrush(QBrush(QColor(v3c("accent", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(v3c("textOnSolid", self._modo)))
                p.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(v3c("borderSoft", self._modo)), 2))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(v3c("ink_secondary", self._modo)))
                p.setFont(qfont("size_small"))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            # Label below circle — elidido a su columna: un paso largo (texto
            # configurable desde el Hub) colisionaba con los vecinos.
            col_txt = (
                v3c("text", self._modo) if i == self._current else v3c("ink_secondary", self._modo)
            )
            p.setPen(QColor(col_txt))
            _f = qfont("size_caption")
            p.setFont(_f)
            _fm = QFontMetrics(_f)
            _elided = _fm.elidedText(label, Qt.TextElideMode.ElideRight, int(step_w - 8))
            p.drawText(
                QRectF(cx - step_w / 2 + 4, cy + circle_r + 4, step_w - 8, 16),
                Qt.AlignmentFlag.AlignCenter,
                _elided,
            )

        p.restore()
        p.end()

# ── NMRoutineSection ──────────────────────────────────────────────────────────


class NMRoutineSection(QWidget):
    """Sección colapsable de rutina con cabecera tintada de color semántico.

    section_type: 'morning' | 'afternoon' | 'night'
    Añadir ítems con content_layout().addWidget(…).
    """

    _TINTS = {
        "morning": ("routine_morning_tint", "☀️"),
        "afternoon": ("routine_afternoon_tint", "\U0001f324"),
        "night": ("routine_night_tint", "\U0001f319"),
    }

    def __init__(self, section_type: str, title: str, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._section_type = section_type
        self._collapsed = False
        self.setObjectName("NMRoutineSection")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._main_lay = QVBoxLayout(self)
        self._main_lay.setContentsMargins(0, 0, 0, 0)
        self._main_lay.setSpacing(0)

        # Header
        self._header = QWidget()
        self._header.setFixedHeight(_NM_CONTROL_HEIGHT)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = lambda e: self._toggle()

        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(sp("md"), 0, sp("md"), 0)
        h_lay.setSpacing(sp("sm"))

        _, icon = self._TINTS.get(section_type, ("routine_morning_tint", "•"))
        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setFont(qfont("size_body"))
        self._icon_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(self._icon_lbl)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_body", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(self._title_lbl, stretch=1)

        # Mini progress bar inline (60×3px) + label "N/N"
        self._mini_prog = QWidget()
        self._mini_prog.setFixedSize(60, 3)
        self._mini_prog_pct = 0.0
        self._mini_prog.paintEvent = self._paint_mini_prog
        self._mini_prog.setVisible(False)
        h_lay.addWidget(self._mini_prog)

        self._prog_lbl = QLabel("")
        self._prog_lbl.setFont(qfont("size_caption", bold=True))
        self._prog_lbl.setStyleSheet("background: transparent;")
        self._prog_lbl.setVisible(False)
        h_lay.addWidget(self._prog_lbl)

        self._toggle_lbl = QLabel("▼")
        self._toggle_lbl.setFont(qfont("size_caption"))
        self._toggle_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(self._toggle_lbl)
        self._main_lay.addWidget(self._header)

        # Content
        self._content = QWidget()
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(sp("md"), sp("sm"), sp("md"), sp("sm"))
        self._content_lay.setSpacing(sp("sm"))
        self._main_lay.addWidget(self._content)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def content_layout(self) -> QVBoxLayout:
        return self._content_lay

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._toggle_lbl.setText("▶" if self._collapsed else "▼")

    def set_progress(self, done: int, total: int):
        """Muestra mini-bar inline + label 'N/N' (o 'N/N ✓' si completo) en el header."""
        if total <= 0:
            self._mini_prog.setVisible(False)
            self._prog_lbl.setVisible(False)
            return
        self._mini_prog_pct = max(0.0, min(1.0, done / total))
        complete = done >= total
        self._prog_lbl.setText(f"{done}/{total} ✓" if complete else f"{done}/{total}")
        c = colors(self._modo)
        if complete:
            col = C("success", self._modo) if "success" in c else C("teal", self._modo)
        elif self._mini_prog_pct >= 0.5:
            col = C("warning", self._modo)
        else:
            col = C("text_tertiary", self._modo)
        self._prog_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._mini_prog.setVisible(True)
        self._prog_lbl.setVisible(True)
        self._mini_prog.update()

    def _paint_mini_prog(self, _event):
        p = QPainter(self._mini_prog)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        w, h = self._mini_prog.width(), self._mini_prog.height()
        c = colors(self._modo)
        # Track
        track_c = QColor(c.get("border_card", c["border"]))
        track_path = QPainterPath()
        track_path.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        p.fillPath(track_path, track_c)
        # Fill
        if self._mini_prog_pct > 0:
            complete = self._mini_prog_pct >= 1.0
            if complete:
                fill_c = QColor(
                    C("success", self._modo) if "success" in c else C("teal", self._modo)
                )
            elif self._mini_prog_pct >= 0.5:
                fill_c = QColor(C("warning", self._modo))
            else:
                fill_c = QColor(C("teal", self._modo))
            fill_path = QPainterPath()
            fw = w * self._mini_prog_pct
            fill_path.addRoundedRect(QRectF(0, 0, fw, h), h / 2, h / 2)
            p.fillPath(fill_path, fill_c)
        p.restore()
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        tint_key, _ = self._TINTS.get(self._section_type, ("routine_morning_tint", ""))
        tint_hex = C(tint_key, self._modo)
        self.setStyleSheet(
            f"QWidget#NMRoutineSection {{ background: {c['bg_surface']}; "
            f"border: 1px solid {c.get('border_card', c['border'])}; "
            f"border-radius: {RADIUS_CARD}px; }}"
        )
        self._header.setStyleSheet(
            f"QWidget {{ background: {_rgba(tint_hex, 0.08 if 'light' in self._modo else 0.06)}; "
            f"border: none; border-radius: {RADIUS_CARD}px; }}"
        )
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._toggle_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._content.setStyleSheet(
            f"background: {_rgba('#000000', 0.01 if 'light' in self._modo else 0.02)};"
        )

# ── NMDayNote ─────────────────────────────────────────────────────────────────


class NMDayNote(QWidget):
    """Card de nota del día con estado bloqueado/desbloqueado.

    Bloqueada: ícono de candado + razón de bloqueo.
    Desbloqueada: QTextEdit expandible.
    Emite note_changed(str).
    """

    note_changed = pyqtSignal(str)

    def __init__(self, locked: bool = True, lock_reason: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._locked = locked
        self._last_emitted_text = ""
        self.setObjectName("NMDayNote")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("md"), sp("sm"), sp("md"), sp("sm"))
        lay.setSpacing(sp("sm"))

        # Header
        row = QHBoxLayout()
        row.setSpacing(sp("sm"))
        self._icon_lbl = QLabel()
        self._icon_lbl.setFont(qfont("size_body"))
        self._icon_lbl.setStyleSheet("background: transparent;")
        row.addWidget(self._icon_lbl)
        title_lbl = QLabel("Nota del día")
        title_lbl.setFont(qfont("size_body", bold=True))
        title_lbl.setStyleSheet("background: transparent;")
        row.addWidget(title_lbl, stretch=1)
        self._save_btn = NMButton("Guardar", variant="gradient", size="sm", modo=self._modo, width=88)
        self._save_btn.clicked.connect(self._emit_note_changed)
        row.addWidget(self._save_btn)
        lay.addLayout(row)

        self._locked_lbl = QLabel()
        self._locked_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._locked_lbl.setFont(qfont("size_small"))
        self._locked_lbl.setWordWrap(True)
        lay.addWidget(self._locked_lbl)

        self._textarea = QTextEdit()
        self._textarea.setPlaceholderText("Escribe tu reflexión del día...")
        self._textarea.setFixedHeight(90)
        # note_changed se emite al TERMINAR de editar (focus out), NO por
        # tecla: emitir en textChanged hacía que el consumidor guardara y
        # bloqueara la nota con el PRIMER caracter (feedback user feedback).
        self._textarea.installEventFilter(self)
        lay.addWidget(self._textarea)

        self.set_locked(locked, lock_reason)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "_textarea", None) and not self._textarea.isReadOnly():
            if ev.type() == QEvent.Type.FocusOut:
                self._emit_note_changed()
            elif ev.type() == QEvent.Type.KeyPress and ev.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                # Enter CONFIRMA la nota (cierra la edición → FocusOut →
                # guardado); Shift+Enter inserta salto de línea. Antes Enter
                # dejaba la nota en modo edición permanente (informe user feedback).
                if not (ev.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._textarea.clearFocus()
                    return True
        return super().eventFilter(obj, ev)

    def _emit_note_changed(self):
        text = self._textarea.toPlainText()
        if self._locked or self._textarea.isReadOnly():
            return
        if text == self._last_emitted_text:
            return
        self._last_emitted_text = text
        self.note_changed.emit(text)

    def set_locked(self, locked: bool, reason: str = ""):
        self._locked = locked
        self._locked_lbl.setVisible(locked)
        self._textarea.setVisible(not locked)
        self._textarea.setReadOnly(False)
        self._save_btn.setVisible(not locked)
        self._save_btn.setEnabled(not locked)
        self._icon_lbl.setText("\U0001f512" if locked else "\U0001f4dd")
        if locked:
            self._locked_lbl.setText(reason or "Completa tu rutina del día para desbloquear")

    def set_saved_today(self, text: str):
        """Estado 'nota del día guardada': lectura hasta mañana.

        La nota del día no es un block de notas eterno (decisión user feedback):
        al guardarse queda visible pero cerrada; al día siguiente el módulo
        la reabre vacía (la nota se persiste por fecha).
        """
        self._locked = True
        self.set_note(text)
        self._textarea.setVisible(True)
        self._textarea.setReadOnly(True)
        self._icon_lbl.setText("✓")
        self._locked_lbl.clear()
        self._locked_lbl.setVisible(False)
        self._save_btn.setVisible(False)
        self._save_btn.setEnabled(False)

    def is_saved_today(self) -> bool:
        return self._textarea.isReadOnly()

    def set_note(self, text: str):
        self._textarea.blockSignals(True)
        self._textarea.setPlainText(text)
        self._textarea.blockSignals(False)
        self._last_emitted_text = text

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        border = _rgba(C("accent", self._modo), 0.20 if "light" in self._modo else 0.25)
        bg = _rgba(C("accent", self._modo), 0.04 if "light" in self._modo else 0.06)
        self.setStyleSheet(
            f"QWidget#NMDayNote {{ background: {bg}; border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {border}; }}"
            "QWidget#NMDayNote QLabel { background: transparent; border: none; }"
        )
        self._locked_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._save_btn._apply_theme(self._modo)
        self._textarea.setStyleSheet(
            f"QTextEdit {{ background: {c['bg_input']}; color: {c['text_primary']}; "
            f"border: 1px solid {c['border']}; border-radius: {RADIUS_INPUT}px; "
            f"padding: 6px 10px; font-size: {TYPOGRAPHY['size_body']}px; }}"
        )

# ── NMMoodContextHeader ────────────────────────────────────────────────────────


class NMMoodContextHeader(QWidget):
    """Banner contextual: 'Basado en tu ánimo de hoy (N/10) EMOJI'.

    Se usa en la cabecera del módulo Actividades.
    """

    _SCORE_MAP = [
        (3, "\U0001f61e"),  # <=2  muy bajo
        (5, "\U0001f615"),  # 3-4  bajo
        (7, "\U0001f610"),  # 5-6  neutro
        (9, "\U0001f642"),  # 7-8  bien
        (11, "\U0001f604"),  # 9-10 excelente
    ]

    def __init__(self, score: int = 5, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._score = score
        self.setFixedHeight(_NM_CONTROL_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(sp("md"), 0, sp("md"), 0)
        lay.setSpacing(sp("sm"))

        self._emoji_lbl = QLabel()
        self._emoji_lbl.setFont(qfont("size_h3"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._emoji_lbl)

        self._text_lbl = QLabel()
        self._text_lbl.setFont(qfont("size_small"))
        self._text_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._text_lbl, stretch=1)

        self.set_score(score)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _emoji_for(self, score: int) -> str:
        for limit, emoji in self._SCORE_MAP:
            if score < limit:
                return emoji
        return "\U0001f610"

    def set_score(self, score: int):
        self._score = score
        self._emoji_lbl.setText(self._emoji_for(score))
        self._text_lbl.setText(f"Basado en tu ánimo de hoy ({score}/10)")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg = _rgba(C("teal", self._modo), 0.06 if "light" in self._modo else 0.07)
        border = _rgba(C("teal", self._modo), 0.12 if "light" in self._modo else 0.15)
        self.setStyleSheet(
            f"background: {bg}; border-radius: {RADIUS_CARD}px; border: 1px solid {border};"
        )
        self._text_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))

# ── NMCategoryFilter ──────────────────────────────────────────────────────────


class NMCategoryFilter(QWidget):
    """Fila horizontal scrollable de chips de filtro por categoría.

    Emite filter_changed(str): nombre de categoría o "" para "Todas".
    """

    filter_changed = pyqtSignal(str)

    def __init__(self, categories: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected: str | None = None
        self._btns: dict[str, QPushButton] = {}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(40)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(sp("sm"))

        all_btn = QPushButton("Todas")
        all_btn.setFixedHeight(28)
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.clicked.connect(lambda: self._select(""))
        row.addWidget(all_btn)
        self._btns[""] = all_btn

        for cat in categories:
            btn = QPushButton(cat)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, c=cat: self._select(c))
            row.addWidget(btn)
            self._btns[cat] = btn

        row.addStretch()
        scroll.setWidget(container)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _select(self, cat: str):
        self._selected = cat if cat else None
        self._apply_theme(self._modo)
        self.filter_changed.emit(cat)

    def selected(self) -> str:
        return self._selected or ""

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for cat, btn in self._btns.items():
            is_sel = (self._selected == cat) or (cat == "" and self._selected is None)
            cat_color = (
                CATEGORY_COLORS.get(cat, C("accent", self._modo))
                if cat
                else C("accent", self._modo)
            )
            bg = _rgba(cat_color, 0.20 if is_sel else 0.14)
            border = _rgba(cat_color, 0.25)
            col = cat_color if cat else C("text_secondary", self._modo)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: {col};
                    border: 1px solid {border};
                    border-radius: {RADIUS_PILL}px;
                    padding: 3px 12px;
                    font-size: {TYPOGRAPHY["size_caption"]}px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    border-color: {cat_color};
                    background: {_rgba(cat_color, 0.20)};
                }}
            """)


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
        # Aviso NEUTRAL (Fase 6): antes era una caja amber/warning dominante que
        # competía con el contenido. Ahora superficie+borde calmos y texto/icono
        # secundarios — sigue presente y legible, pero como nota, no alarma.
        bg_color = v3c("surface2", self._modo).name()
        border_color = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        icon_color = v3c("ink_secondary", self._modo).name()
        ink_color = v3c("ink_secondary", self._modo).name()
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

