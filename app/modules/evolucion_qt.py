"""
app/modules/evolucion_qt.py — Módulo Visualizador de Evolución Anímica (PyQt6)
Vista de progreso semanal/mensual con toggle y gráficos.
"""

import os
import sys
import datetime as dt
import logging

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QFont,
    QPen,
    QLinearGradient,
    QPolygonF,
    QPainterPath,
    QMouseEvent,
    QPalette,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QSizePolicy,
)

# Textos customizables desde el Hub (M1 Fase 2): alinea las claves del editor
# text_overrides con lo que el módulo realmente consume (antes huérfanas).
from shared.remote_config import t

# Import shared modules
try:
    from shared.components_qt import (
        NMModule,
        NMButton,
        NMToast,
        ThemeManager,
        NMCard,
        NMTabs,
        NMChartPanel,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        V3_RD,
        stylesheet_scrollarea,
        eyebrow_font,
        v3_font,
        RADIUS_SMALL,
        _tm,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule,
        NMButton,
        NMToast,
        NMCard,
        NMTabs,
        NMChartPanel,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        V3_RD,
        eyebrow_font,
        v3_font,
        RADIUS_SMALL,
        _tm,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.visual_qa import visual_qa_enabled

_log = logging.getLogger(__name__)


class EvolucionWaveChart(QWidget):
    """Gráfico de evolución dual-serie (positiva teal / negativa danger).
    Adapta NMWaveChart para soportar series semanales (7 pts) y mensuales
    (30 pts) de forma dinámica, con leyenda Positivo/Negativo.
    """

    SERIES_LABELS = ("Positivo", "Negativo")

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or "dark_hybrid")
        self._data_current: list[float | None] = []
        self._data_previous: list[float | None] = []
        self._labels: list[str] = []
        self._hover_idx = -1

        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_data(self, current: list, previous: list, labels: list[str]):
        self._data_current = list(current)
        self._data_previous = list(previous)
        self._labels = list(labels)
        self._hover_idx = -1
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        n = len(self._data_current)
        if n < 2:
            return
        ml, mr = 32, 16
        step = (self.width() - ml - mr) / max(1, n - 1)
        idx = round((event.pos().x() - ml) / step)
        idx = max(0, min(n - 1, idx))
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        ml, mr = 32, 16
        # mt ampliado para que la leyenda (●Positivo ●Negativo) tenga banda
        # propia y no se recorte contra el borde superior (mismo criterio que
        # NMWaveChart — "elevar ambas etiquetas").
        mt, mb = 34, 28
        cw = w - ml - mr
        ch = h - mt - mb

        teal_hex = C("teal", self._modo)
        danger_hex = C("danger", self._modo)

        # Faint grid lines at 10, 7.5, 5, 2.5 y 0 (línea de base incluida —
        # sin ella la escala quedaba asimétrica).
        for row in range(0, 5):
            y_grid = mt + ch - (ch * row / 4)
            gc = QColor(v3c("border", self._modo).name())
            gc.setAlpha(35)
            p.setPen(QPen(gc, 1, Qt.PenStyle.DotLine))
            p.drawLine(ml, int(y_grid), w - mr, int(y_grid))

        def _pts(data):
            result = []
            n = len(data)
            for i, v in enumerate(data):
                if v is None:
                    continue
                x = ml + (i / max(1, n - 1)) * cw
                y = mt + ch - (v / 10.0) * ch
                result.append(QPointF(x, y))
            return result

        def _draw_area(pts, color_hex, alpha_fill=50, alpha_line=190):
            if len(pts) < 2:
                return
            bottom_y = mt + ch
            poly_pts = [QPointF(pts[0].x(), bottom_y)]
            poly_pts += pts
            poly_pts.append(QPointF(pts[-1].x(), bottom_y))
            poly = QPolygonF(poly_pts)
            path = QPainterPath()
            path.addPolygon(poly)
            fill_grad = QLinearGradient(0, mt, 0, mt + ch)
            fc = QColor(color_hex)
            fc.setAlpha(alpha_fill)
            ec = QColor(color_hex)
            ec.setAlpha(0)
            fill_grad.setColorAt(0.0, fc)
            fill_grad.setColorAt(1.0, ec)
            p.fillPath(path, QBrush(fill_grad))
            lc = QColor(color_hex)
            lc.setAlpha(alpha_line)
            p.setPen(QPen(lc, 2.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            line_path = QPainterPath()
            line_path.moveTo(pts[0])
            for pt in pts[1:]:
                line_path.lineTo(pt)
            p.drawPath(line_path)

        is_dark = "dark" in self._modo
        prev_pts = _pts(self._data_previous)
        _draw_area(prev_pts, danger_hex, alpha_fill=38 if is_dark else 30, alpha_line=170)

        curr_pts = _pts(self._data_current)
        _draw_area(curr_pts, teal_hex, alpha_fill=64 if is_dark else 46, alpha_line=210)

        # Dots — ambas series (pos/neg en paralelo, solo puntos válidos)
        p.setBrush(QBrush(QColor(danger_hex)))
        p.setPen(Qt.PenStyle.NoPen)
        for i, v in enumerate(self._data_previous):
            if v is None:
                continue
            x = ml + (i / max(1, len(self._data_previous) - 1)) * cw
            y = mt + ch - (v / 10.0) * ch
            p.drawEllipse(QPointF(x, y), 3, 3)
        p.setBrush(QBrush(QColor(teal_hex)))
        for i, v in enumerate(self._data_current):
            if v is None:
                continue
            x = ml + (i / max(1, len(self._data_current) - 1)) * cw
            y = mt + ch - (v / 10.0) * ch
            pt = QPointF(x, y)
            r = 5 if i == self._hover_idx else 3
            p.drawEllipse(pt, r, r)

        # Leyenda discreta arriba a la derecha: ● Positivo  ● Negativo
        p.setFont(qfont("size_caption_xs"))
        fm = p.fontMetrics()
        x_cursor = w - mr
        for text, hexc in ((self.SERIES_LABELS[1], danger_hex), (self.SERIES_LABELS[0], teal_hex)):
            tw_lbl = fm.horizontalAdvance(text)
            x_cursor -= tw_lbl
            p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
            p.drawText(
                QRectF(x_cursor, 6, tw_lbl, 14),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
            x_cursor -= 10
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(hexc)))
            p.drawEllipse(QPointF(x_cursor + 3, 13), 3.0, 3.0)
            x_cursor -= 10

        # Hover tooltip
        if 0 <= self._hover_idx < len(self._data_current):
            val = self._data_current[self._hover_idx]
            if val is not None:
                x = ml + (self._hover_idx / max(1, len(self._data_current) - 1)) * cw
                y = mt + ch - (val / 10.0) * ch
                pt = QPointF(x, y)
                is_today = self._hover_idx == len(self._data_current) - 1
                tip_text = f"Hoy: {val:.1f}" if is_today else f"{val:.1f}/10"
                tw, th = 70, 22
                tx = min(pt.x() - tw / 2, w - mr - tw)
                ty = max(float(mt), pt.y() - th - 8)
                tip_bg = QColor(v3c("elevated", self._modo).name())
                tip_bg.setAlpha(220)
                tip_r = QRectF(tx, ty, tw, th)
                tip_path = QPainterPath()
                tip_path.addRoundedRect(tip_r, 4, 4)
                p.fillPath(tip_path, tip_bg)
                p.setPen(QColor(v3c("text", self._modo).name()))
                p.setFont(qfont("size_small"))
                p.drawText(tip_r, Qt.AlignmentFlag.AlignCenter, tip_text)

        # Y-axis labels — escala completa 10/5/0 (feedback owner v1.0).
        p.setFont(qfont("size_caption_xs"))
        p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
        for y_val in (10, 5, 0):
            y_pos = mt + ch - (y_val / 10.0) * ch
            p.drawText(
                QRectF(0, y_pos - 7, ml - 4, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(y_val),
            )

        # Day/Date labels
        p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
        p.setFont(qfont("size_caption"))
        n = len(self._labels)
        for i, lbl in enumerate(self._labels):
            # Selectively hide labels in monthly view to avoid overlaps
            if n > 10 and i % 5 != 0 and i != n - 1:
                continue
            x = ml + (i / max(1, n - 1)) * cw
            p.drawText(QRectF(x - 24, h - mb + 4, 48, 14), Qt.AlignmentFlag.AlignCenter, lbl)

        p.restore()
        p.end()


class _EvolucionStatCard(NMCard):
    """Métrica para mostrar estadísticas de evolución (Promedio, Máximo, Mínimo)."""
    def __init__(self, label: str, value: str, message: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self.setMinimumHeight(80)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(2)

        self._label = QLabel(label)
        self._label.setFont(eyebrow_font())
        self._label.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
        lay.addWidget(self._label)

        row = QHBoxLayout()
        row.setSpacing(6)
        self._value = QLabel(value)
        self._value.setFont(v3_font("size_h3", weight=TYPOGRAPHY["weight_semibold"], serif=True))
        self._value.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
        row.addWidget(self._value)
        row.addStretch()
        lay.addLayout(row)

        self._message = QLabel(message)
        self._message.setFont(qfont("size_caption_xs"))
        self._message.setStyleSheet(f"color: {v3c('textMuted', self._modo).name()};")
        self._message.setWordWrap(True)
        lay.addWidget(self._message)

    def set_value(self, value: str):
        self._value.setText(value or "—")

    def set_message(self, message: str):
        self._message.setText(message or "")


class ModuloEvolucion(NMModule):
    MODULE_TITLE = "Visualizador de Evolución Anímica"
    MODULE_ICON = "chart"

    def build_ui(self):
        # Setup vertical layout inside self._content
        lay = QVBoxLayout(self._content)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        # NMTabs at the top of content
        self._tabs = NMTabs(["Semanal", "Mensual"], modo=self._modo, parent=self)
        self._tabs.changed.connect(self._on_tab_changed)
        lay.addWidget(self._tabs)

        # NMChartPanel containing our custom EvolucionWaveChart
        self._chart_panel = NMChartPanel(
            t("text.module.evolucion.eyebrow", "Evolución anímica"), modo=self._modo
        )
        self._chart_panel.setMinimumHeight(220)

        self._wave_chart = EvolucionWaveChart(modo=self._modo)
        self._chart_panel.set_chart(self._wave_chart)
        lay.addWidget(self._chart_panel)

        # 4.3: sparse state cuando hay <2 registros válidos: un mensaje suave
        # centrado reemplaza al chart. Inicia oculto; se alterna en _load_tab_data.
        from PyQt6.QtCore import Qt as _Qt
        self._sparse_overlay = QLabel(
            "Necesitamos al menos 2 registros para trazar una tendencia.\n"
            "Anotá cómo te sentís hoy para empezar a ver la curva."
        )
        self._sparse_overlay.setAlignment(_Qt.AlignmentFlag.AlignCenter)
        self._sparse_overlay.setWordWrap(True)
        self._sparse_overlay.setFont(qfont("size_small"))
        self._sparse_overlay.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; "
            "background: transparent; padding: 24px;"
        )
        self._sparse_overlay.hide()
        # 4.3 fix: _canvas_lay es un QVBoxLayout — un addWidget quedaría DEBAJO
        # del chart, no superpuesto. El sparse state reemplaza al chart:
        # se alternan visibilidades (chart oculto ↔ mensaje visible) en
        # _load_tab_data, así nunca se ve el "chart gigante con un puntito".
        self._sparse_overlay.setMinimumHeight(120)
        self._chart_panel._canvas_lay.addWidget(self._sparse_overlay)

        # Stats row at the bottom
        self._stats_layout = QHBoxLayout()
        self._stats_layout.setSpacing(12)

        # Mensajes DESCRIPTIVOS, no interpretativos: la app no emite juicios
        # clínicos ni maquilla datos (decisión owner v1.0). El promedio aclara
        # que combina valencias para no leerse como "ánimo simple".
        self._stat_avg = _EvolucionStatCard(
            "Ánimo promedio",
            "—",
            "Bienestar promedio del período: combina registros positivos y negativos.",
            modo=self._modo,
        )
        self._stat_max = _EvolucionStatCard(
            "Ánimo máximo",
            "—",
            "El puntaje más alto registrado en el período.",
            modo=self._modo,
        )
        self._stat_min = _EvolucionStatCard(
            "Ánimo mínimo",
            "—",
            "El puntaje más bajo registrado en el período.",
            modo=self._modo,
        )

        self._stats_layout.addWidget(self._stat_avg)
        self._stats_layout.addWidget(self._stat_max)
        self._stats_layout.addWidget(self._stat_min)
        lay.addLayout(self._stats_layout)

        # Load initial data (weekly tab = index 0)
        self._load_tab_data(0)

    def _on_tab_changed(self, idx: int, label: str):
        self._load_tab_data(idx)

    def _load_tab_data(self, tab_idx: int):
        from shared.visual_qa import visual_qa_enabled
        from shared.utils import get_valence_series

        # El chart muestra POSITIVO vs NEGATIVO en paralelo (mismo modelo que
        # Ánimo y que el Hub); los stats siguen midiendo bienestar combinado.
        if tab_idx == 0:
            # Weekly View
            self._chart_panel.set_title(
                t("text.module.evolucion.weekly_title", "Variación del Humor Semanal")
            )
            positiva, negativa = get_valence_series(7)
            labels = ["L", "M", "M", "J", "V", "S", "D"]
            if visual_qa_enabled():
                stats_serie = [5.0, 6.0, 7.0, 8.0, 7.0, 9.0, 9.0]
            else:
                stats_serie, _, _ = self._query_weekly_data()
        else:
            # Monthly View
            self._chart_panel.set_title(
                t("text.module.evolucion.monthly_title", "Variación del Humor Mensual (30 Días)")
            )
            positiva, negativa = get_valence_series(30)
            today = dt.date.today()
            labels = [
                (today - dt.timedelta(days=offset)).strftime("%d/%m")
                for offset in range(29, -1, -1)
            ]
            if visual_qa_enabled():
                stats_serie = [float(5 + (i % 4)) for i in range(30)]
            else:
                stats_serie, _, _ = self._query_monthly_data()

        # Update chart
        self._wave_chart.set_data(positiva, negativa, labels)

        # Compute stats (ignore None) — bienestar combinado del período
        valid_vals = [v for v in stats_serie if v is not None]
        chart_points = [v for v in positiva + negativa if v is not None]

        # 4.3: sparse state — con <2 puntos válidos en el chart el mensaje
        # suave lo reemplaza (alternancia de visibilidad; ver _build).
        if hasattr(self, "_sparse_overlay"):
            sparse = len(chart_points) < 2
            self._sparse_overlay.setVisible(sparse)
            if hasattr(self, "_wave_chart"):
                self._wave_chart.setVisible(not sparse)

        if valid_vals:
            avg_val = sum(valid_vals) / len(valid_vals)
            max_val = max(valid_vals)
            min_val = min(valid_vals)

            self._stat_avg.set_value(f"{avg_val:.1f}")
            self._stat_max.set_value(f"{max_val:.0f}")
            self._stat_min.set_value(f"{min_val:.0f}")

            # Descriptivo, sin juicio clínico ("estado bajo", "contactá a tu
            # profesional") — la interpretación es del profesional, no de la
            # app (decisión owner v1.0).
            self._stat_avg.set_message(
                "Bienestar promedio del período: combina registros positivos y negativos."
            )
        else:
            self._stat_avg.set_value("—")
            self._stat_max.set_value("—")
            self._stat_min.set_value("—")
            self._stat_avg.set_message("No hay suficientes registros en este período.")

    def _query_weekly_data(self) -> tuple[list, list, list]:
        try:
            from shared.utils import get_weekly_series
            current, previous = get_weekly_series()
            labels = ["L", "M", "M", "J", "V", "S", "D"]
            return current, previous, labels
        except Exception:
            return [None] * 7, [None] * 7, ["L", "M", "M", "J", "V", "S", "D"]

    def _query_monthly_data(self) -> tuple[list, list, list]:
        try:
            import datetime as dt
            from shared.db import obtener_conexion
            con = obtener_conexion()
            today = dt.date.today()
            current, previous = [], []
            labels = []

            for offset in range(29, -1, -1):
                day = today - dt.timedelta(days=offset)
                labels.append(day.strftime("%d/%m"))
                
                # Current period (last 30 days)
                row = con.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?", (str(day),)
                ).fetchone()
                current.append(float(row[0]) if row and row[0] is not None else None)

                # Previous period (30 days prior)
                day_prev = day - dt.timedelta(days=30)
                row2 = con.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?", (str(day_prev),)
                ).fetchone()
                previous.append(float(row2[0]) if row2 and row2[0] is not None else None)

            return current, previous, labels
        except Exception:
            return [None] * 30, [None] * 30, [f"D{i+1}" for i in range(30)]

    def get_card_status(self) -> str:
        """Card status shown on Home."""
        from shared.visual_qa import visual_qa_enabled
        if visual_qa_enabled():
            return "7.2 promedio"
        try:
            import datetime as dt
            from shared.db import obtener_conexion
            con = obtener_conexion()
            # Average of last 7 days
            today = dt.date.today()
            start_date = today - dt.timedelta(days=6)
            row = con.execute(
                "SELECT AVG(puntaje) FROM termometro WHERE date(fecha) BETWEEN ? AND ?",
                (str(start_date), str(today)),
            ).fetchone()
            if row and row[0] is not None:
                return f"{float(row[0]):.1f} promedio"
        except Exception:
            pass
        return "Sin registros"

    def on_enter(self):
        # Reload current tab data when entering the module
        self._load_tab_data(self._tabs._current)

    def on_leave(self):
        pass
