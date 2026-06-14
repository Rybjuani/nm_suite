"""Session/activity UI components: checklists, activity cards, preset chips, history."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
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
    V3_SP,
    colors,
    label_style,
    norm_modo,
    pill_radius,
    qfont,
    sp,
    v3c,
)
from shared.components.buttons import _NM_CONTROL_HEIGHT


def _tm() -> ThemeManager:
    return ThemeManager.instance()


def _rgba(hex_color: str, alpha: float) -> str:
    c = QColor(hex_color)
    a = max(0, min(255, int(alpha * 255)))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a})"


# ═══════════════════════════════════════════════════════════════════════════════
# NMCustomCheck / NMActivityCard / Timer helpers


class _NMAnimCheckBox(QWidget):
    """Caja 20×20 con checkmark que se dibuja progresivamente (220ms OutCubic).

    Uso interno de NMCustomCheck. No usar directamente.
    """

    # Geometría del checkmark en espacio 20×20
    _P0 = (4.0, 11.0)   # inicio (izquierda)
    _P1 = (8.0, 15.0)   # vértice inferior (punto de quiebre)
    _P2 = (16.0, 5.0)   # final (derecha arriba)

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
        self.setFixedSize(20, 20)
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

        border_col = v3c("teal" if self._checked else "borderStrong", self._modo)
        bg_col = QColor(v3c("teal", self._modo)) if self._checked else QColor(0, 0, 0, 0)

        p.setPen(QPen(border_col, 2.0))
        p.setBrush(QBrush(bg_col))
        p.drawRoundedRect(QRectF(1, 1, 18, 18), 5, 5)

        if self._checked and self._draw_t > 0.001:
            ink = v3c("bg", self._modo)
            # Trazo más grueso en light: el bg del botón es más claro, necesita más peso
            ck_width = 2.0 if "dark" in self._modo else 2.5
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
        self._label = QLabel(text)
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        lay.addWidget(self._label, stretch=1)
        self._box = _NMAnimCheckBox(self._modo)
        lay.addWidget(self._box)
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
