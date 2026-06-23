"""Patient row components for the Hub: NMPatientRow, NMSparkline, NMAreaSparkline, NMPatientRowPremium."""

from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    QPointF,
    QRectF,
    QSize,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    C,
    norm_modo,
    qfont,
    qcolor_to_rgba_css,
    v3c,
)
from shared.components.rings import NMModuleRing
from shared.components.session import _rgba


def _tm() -> ThemeManager:
    return ThemeManager.instance()


_PATIENT_AVATAR_PAIRS = [
    ("accent", "teal"),
    ("teal", "violet"),
    ("violet", "accent"),
    ("accent", "violet"),
]

_NM_PATIENT_ROW_HEIGHT = 70
_NM_PATIENT_ROW_PAD_X = 16
_NM_PATIENT_ROW_PAD_Y = 14
_NM_PATIENT_ROW_GAP = 14
_NM_PATIENT_AVATAR_SIZE = 40
_NM_PATIENT_AVATAR_RADIUS = 12
_NM_PATIENT_SPARKLINE_W = 78
_NM_PATIENT_SPARKLINE_H = 30
_NM_PATIENT_TREND_COL_W = 90
_NM_PATIENT_RING_SIZE = 36
_NM_PATIENT_RING_COL_W = 60
_NM_PATIENT_UNLINK_SIZE = 30
_NM_PATIENT_UNLINK_RADIUS = 9
_NM_AREA_SPARK_MIN_H = 74
_NM_AREA_SPARK_MAX_H = 82
_NM_AREA_SPARK_GRID_VALUES = (0, 5, 10)
_NM_AREA_SPARK_PAD_L = 24
_NM_AREA_SPARK_PAD_R = 6
_NM_AREA_SPARK_TOP_PAD = 8
_NM_AREA_SPARK_LABEL_H = 16
_NM_AREA_SPARK_STROKE_W = 2.0
_NM_AREA_SPARK_DOT_RADIUS = 3.0
_NM_AREA_SPARK_DOT_MAX_POINTS = 7


class NMPatientRow(QFrame):
    """Fila de paciente del Hub con avatar e indicador de adherencia."""

    clicked = pyqtSignal()

    def __init__(
        self,
        name: str,
        subtitle: str = "",
        initials: str = "",
        pct: float | None = 0.0,
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

    • Fixed size (default 78×30, matching Hub `.pcol-trend`).
    • None / 0 values treated as gaps (segment breaks).
    • Color auto-selects `danger` token when last value drops ≥2 vs first
      (descending trend), otherwise uses `primary` token.
    """

    def __init__(
        self,
        data: list | None = None,
        color: str | None = None,
        w: int = _NM_PATIENT_SPARKLINE_W,
        h: int = _NM_PATIENT_SPARKLINE_H,
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
        pen.setWidthF(2.0)
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

    A diferencia de :class:`NMSparkline` (polyline inline 78x30), este pinta:
      - area rellena con gradiente brand que se desvanece hacia abajo;
      - linea con gradiente de animo;
      - guias 0/5/10 como el chart del mockup;
      - marcadores circulares en series semanales;
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
        self.setMinimumHeight(_NM_AREA_SPARK_MIN_H)
        self.setMaximumHeight(_NM_AREA_SPARK_MAX_H)
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

        pw, ph = self.width(), self.height()

        axis_h = _NM_AREA_SPARK_LABEL_H if self._labels else 4
        plot_left = _NM_AREA_SPARK_PAD_L
        plot_right = pw - _NM_AREA_SPARK_PAD_R
        top_pad = _NM_AREA_SPARK_TOP_PAD
        plot_h = max(1, ph - axis_h - top_pad - 2)
        eff_w = max(1, plot_right - plot_left)

        vals = [min(10.0, max(0.0, float(v))) for v in self._data]
        n = len(vals)

        def _xy(idx: int, val: float) -> tuple[float, float]:
            x = plot_left + idx * eff_w / max(n - 1, 1)
            y = top_pad + plot_h - (val / 10.0) * plot_h
            return x, y

        pts = [_xy(i, v) for i, v in enumerate(vals)]
        baseline_y = top_pad + plot_h

        grid_c = v3c("line", self._modo)
        grid_c.setAlpha(70 if "dark" in self._modo else 92)
        label_c = v3c("text3", self._modo)
        painter.setFont(qfont("size_caption_xs", weight=500))
        for value in _NM_AREA_SPARK_GRID_VALUES:
            y_grid = top_pad + plot_h - (value / 10.0) * plot_h
            painter.setPen(QPen(grid_c, 1))
            painter.drawLine(plot_left, int(round(y_grid)), plot_right, int(round(y_grid)))
            painter.setPen(label_c)
            painter.drawText(
                QRectF(0, y_grid - 8, plot_left - 5, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(value),
            )

        # Area rellena con gradiente que se desvanece hacia la baseline.
        area = QPainterPath()
        area.moveTo(pts[0][0], baseline_y)
        for x, y in pts:
            area.lineTo(x, y)
        area.lineTo(pts[-1][0], baseline_y)
        area.closeSubpath()
        grad = QLinearGradient(0, top_pad, 0, baseline_y)
        top_c = v3c("brand", self._modo)
        top_c.setAlpha(62 if "dark" in self._modo else 48)
        bot_c = v3c("brand", self._modo)
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
        line_grad = QLinearGradient(plot_left, 0, plot_right, 0)
        line_grad.setColorAt(0.0, v3c("moodGradFrom", self._modo))
        line_grad.setColorAt(0.50, v3c("moodGradMid", self._modo))
        line_grad.setColorAt(1.0, v3c("moodGradTo", self._modo))
        line_pen = QPen(QBrush(line_grad), _NM_AREA_SPARK_STROKE_W)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line)

        draw_dots = n <= _NM_AREA_SPARK_DOT_MAX_POINTS
        if draw_dots:
            dot_border = v3c("brand", self._modo)
            dot_fill = v3c("surface", self._modo)
            for x, y in pts:
                painter.setPen(QPen(dot_border, 1.6))
                painter.setBrush(dot_fill)
                painter.drawEllipse(QPointF(x, y), _NM_AREA_SPARK_DOT_RADIUS, _NM_AREA_SPARK_DOT_RADIUS)

        # Etiquetas de eje X (dias).
        if self._labels:
            painter.setPen(label_c)
            f = qfont("size_caption_xs")
            painter.setFont(f)
            label_y = ph - axis_h
            n_lab = len(self._labels)
            for i, lab in enumerate(self._labels):
                cx = plot_left + i * eff_w / max(n_lab - 1, 1)
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
        pct: float | None = 0.0,
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
        self.setFixedHeight(_NM_PATIENT_ROW_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._action_controls_visible = True

        lay = QHBoxLayout(self)
        lay.setContentsMargins(
            _NM_PATIENT_ROW_PAD_X,
            _NM_PATIENT_ROW_PAD_Y,
            _NM_PATIENT_ROW_PAD_X,
            _NM_PATIENT_ROW_PAD_Y,
        )
        lay.setSpacing(_NM_PATIENT_ROW_GAP)

        # Status dot
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(10, 10)
        self._status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        # Avatar rounded initials (40x40, r12) — Hub `.avatar`.
        initials = "".join(part[:1] for part in (name or "?").split()[:2]).upper()
        self._avatar = QLabel(initials or "P")
        self._avatar.setFixedSize(_NM_PATIENT_AVATAR_SIZE, _NM_PATIENT_AVATAR_SIZE)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_bold"]))
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
            lay.addWidget(self._sparkline, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            lay.addSpacing(_NM_PATIENT_TREND_COL_W)

        self._ring = NMModuleRing(
            size=_NM_PATIENT_RING_SIZE, pct=pct, modo=self._modo, color_key="gold"
        )
        _ring_wrap = QWidget()
        _ring_wrap.setFixedWidth(_NM_PATIENT_RING_COL_W)
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
            self._btn_unlink.setFixedSize(_NM_PATIENT_UNLINK_SIZE, _NM_PATIENT_UNLINK_SIZE)
            self._btn_unlink.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_unlink.setToolTip("Quitar paciente del Hub")
            self._btn_unlink.setAccessibleName(f"Quitar a {self._full_name} del Hub")
            self._btn_unlink.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            # La X se oculta en filas no completamente visibles (optimización de
            # scroll). Debe CONSERVAR su espacio al ocultarse: si no, el layout
            # recupera el hueco y corre sparkline+ring a la derecha, desalineando
            # la última fila respecto de las demás.
            _sp = self._btn_unlink.sizePolicy()
            _sp.setRetainSizeWhenHidden(True)
            self._btn_unlink.setSizePolicy(_sp)
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

    def set_action_controls_visible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._action_controls_visible:
            return
        self._action_controls_visible = visible
        if self._btn_unlink is not None:
            self._btn_unlink.setVisible(visible)
            if not visible and self._btn_unlink.hasFocus():
                self._btn_unlink.clearFocus()

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
            else "transparent"
        )
        hover_bg = v3c("surface2", self._modo).name()
        self.setStyleSheet(
            f"QFrame#NMPatientRowPremium {{ background: {bg}; border: 1px solid {border}; "
            f"border-left: 3px solid {C('accent', self._modo) if self._selected else border}; "
            f"border-radius: 12px; }}"
            f"QFrame#NMPatientRowPremium:hover {{ background: {hover_bg}; "
            f"border-color: {qcolor_to_rgba_css(v3c('line', self._modo))}; }}"
        )
        k1, k2 = _PATIENT_AVATAR_PAIRS[self._name_hash]
        self._avatar.setStyleSheet(
            f"QLabel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {C(k1, self._modo)}, stop:1 {C(k2, self._modo)}); "
            f"color: white; border-radius: {_NM_PATIENT_AVATAR_RADIUS}px; "
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
            from shared.theme_qt import nm_icon
            # Acción destructiva legible: el icono lleva el tono danger en reposo
            # (no un gris neutro que se leía como "cerrar") y el hover refuerza
            # con un fondo danger translúcido. Quitar un paciente es irreversible
            # → debe verse como tal sin gritar (alpha bajo en el fondo).
            _danger = v3c("danger", self._modo).name()
            self._btn_unlink.setIcon(nm_icon("close", _danger, size=13))
            self._btn_unlink.setIconSize(QSize(13, 13))
            self._btn_unlink.setStyleSheet(
                "QToolButton#NMRowUnlink { background: transparent; border: none; "
                f"border-radius: {_NM_PATIENT_UNLINK_RADIUS}px; }}"
                f"QToolButton#NMRowUnlink:hover {{ "
                f"background: {_rgba(C('danger', self._modo), 0.18)}; }}"
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
