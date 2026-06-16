"""
hub/pacientes_qt.py — Vista detallada de paciente (PyQt6)

Tabs activas: Resumen | Registros | Plan terapéutico | IA
- Resumen: actividad reciente + métricas de seguimiento
- Registros: historial de datos + gráfico de evolución + exportar PDF
- Plan terapéutico: rutina, activación, TCC, recordatorios y temporizador
- IA: borradores para revisión profesional

Toda la lógica de DB/Supabase preservada exacta de pacientes.py.
"""

import os
import re
import sys
import threading
import json
from datetime import datetime, timezone

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QDate, QSize
from PyQt6 import sip
from PyQt6.QtGui import QColor, QBrush, QLinearGradient
from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QFrame,
    QTabWidget,
    QTextEdit,
    QComboBox,
    QApplication,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QDialog,
    QCheckBox,
    QDateEdit,
    QLineEdit,
)
from shared.adaptive_layout_qt import (
    NMSegmentedPanel,
    NMResponsiveColumns,
    BP_STACK,
    configure_adaptive_window,
    apply_child_window_chrome,
    window_edge_radius,
)
from shared.qt_thread import run_on_gui

try:
    from shared.components import (
        NMModule,
        NMButton,
        NMButtonOutline,
        NMCard,
        NMInput,
        NMTextArea,
        NMProgressBar,
        NMToggle,
        NMToast,
        NMSkeleton,
        ThemeManager,
        h_spacer,
        NMFeaturedCard,
        NMModuleRing,
        NMTypingDots,
        NMSectionHeader,
        NMDivider,
        NMAvatar,
        NMBadge,
        NMElidedLabel,
        NMEmptyState,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qcolor,
        qfont,
        qfont_mono,
        interpolate_color,
        v3_font,
        apply_chart_theme,
        get_gradient,
        gradient_colors,
        stylesheet_lineedit,
        stylesheet_textedit,
        stylesheet_tabwidget,
        stylesheet_tabwidget_underline,
        stylesheet_combobox,
        stylesheet_dateedit,
        stylesheet_spinbox,
        stylesheet_scrollarea,
        sp,
        RADIUS_CARD,
        RADIUS_BUTTON,
        RADIUS_SMALL,
        RADIUS_PILL,
        PAD_CONTAINER,
        PAD_CARD,
        GAP_CARDS,
        GAP_ELEMENTS,
        # v3
        v3c,
        qcolor_to_rgba_css,
        V3_SP,
        V3_RD,
    )
    from shared.theme import CATEGORY_COLORS, TYPOGRAPHY
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMButton,
        NMButtonOutline,
        NMCard,
        NMInput,
        NMToggle,
        NMToast,
        NMSkeleton,
        ThemeManager,
        NMFeaturedCard,
        NMModuleRing,
        NMTypingDots,
        NMSectionHeader,
        NMDivider,
        NMAvatar,
        NMBadge,
        NMElidedLabel,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        v3_font,
        apply_chart_theme,
        stylesheet_textedit,
        stylesheet_tabwidget_underline,
        stylesheet_combobox,
        stylesheet_dateedit,
        stylesheet_spinbox,
        stylesheet_scrollarea,
        RADIUS_BUTTON,
        PAD_CONTAINER,
        PAD_CARD,
        GAP_CARDS,
        v3c,
        qcolor_to_rgba_css,
        V3_SP,
        V3_RD,
    )
    from shared.theme import CATEGORY_COLORS, TYPOGRAPHY


# ── v3 surface helpers ──────────────────────────────────────────────────────


def _v3_surface(modo: str) -> str:
    """Surface color v3 con awareness dark/light."""
    return v3c("surfaceSolid" if "dark" in norm_modo(modo) else "surface", modo).name()


def _v3_elevated(modo: str) -> str:
    return v3c("elevatedSolid" if "dark" in norm_modo(modo) else "elevated", modo).name()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _style_mini_pill(badge: QLabel, color: str) -> None:
    """Pill inline chica de los registros. Alto fijo + radio = mitad de la
    altura: Qt no clampa border-radius en QSS y el token pill (999) directo
    renderiza esquinas cuadradas."""
    badge.setFixedHeight(20)
    # Texto a opacidad plena (antes {color}CC=80% → atenuado, ilegible en
    # amber/teal) sobre un tinte del mismo color más presente (antes 0F=6% casi
    # transparente). Patrón chip ADN: color legible sobre su propio tinte suave.
    badge.setStyleSheet(
        f"QLabel {{ color: {color}; background: {color}26; "
        f"border: 1px solid {color}45; border-radius: 10px; padding: 0px 8px; }}"
    )


def _card_frame(modo: str) -> QFrame:
    """Frame card v3 — glassmorphism superficie + border `borderSoft` + radius lg (16)."""
    is_dark = "dark" in norm_modo(modo)
    base = v3c("surfaceSolid" if is_dark else "surface", modo)
    alpha = 150 if is_dark else 210
    surface = f"rgba({base.red()},{base.green()},{base.blue()},{alpha})"
    border = v3c("borderSoft", modo)
    border_css = f"rgba({border.red()},{border.green()},{border.blue()},{border.alpha()})"
    f = QFrame()
    f.setObjectName("NMDetailCard")
    f.setStyleSheet(f"""
        QFrame#NMDetailCard {{
            background: {surface};
            border-radius: {V3_RD["lg"]}px;
            border: 1px solid {border_css};
        }}
    """)
    return f


def _row_item(text: str, modo: str) -> QFrame:
    """Row item v3 — fondo `elevated` + radius sm + texto `text2`."""
    elev = _v3_elevated(modo)
    text_color = v3c("text2", modo).name()
    f = QFrame()
    f.setObjectName("NMDetailRowItem")
    f.setStyleSheet(f"""
        QFrame#NMDetailRowItem {{
            background: {elev};
            border-radius: {V3_RD["sm"]}px;
            border: none;
        }}
    """)
    lbl = QLabel(text)
    lbl.setFont(qfont("size_caption"))
    lbl.setStyleSheet(f"color: {text_color}; background: transparent;")
    lbl.setWordWrap(True)
    lay = QHBoxLayout(f)
    lay.setContentsMargins(V3_SP["sm"], V3_SP["xs"], V3_SP["sm"], V3_SP["xs"])
    lay.addWidget(lbl)
    return f


# ── Gráfico de ánimo con pyqtgraph ───────────────────────────────────────────


def _build_animo_graph(
    parent: QWidget, registros: list, modo: str, compact: bool = False
) -> QWidget:
    """
    PlotWidget pyqtgraph con curva suavizada, área bajo la curva
    con gradiente teal→transparente, puntos interactivos con tooltip.
    """
    try:
        import pyqtgraph as pg
        import numpy as np
    except ImportError:
        lbl = QLabel("pyqtgraph no instalado")
        lbl.setFont(qfont("size_body"))
        c = colors(norm_modo(modo))
        lbl.setStyleSheet(f"color: {c['text_tertiary']};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    modo = norm_modo(modo)
    apply_chart_theme(modo)
    c = colors(modo)
    accent = C("accent", modo)
    teal = C("teal", modo)

    # Datos: ordenar cronológicamente. Registro pos/neg SEPARADO (v1.0):
    # cada punto lleva su valencia y la intensidad CRUDA — "tristeza 10" se
    # grafica como negativo fuerte, no como bienestar 1.
    points = []
    for r in registros:
        p = r.get("puntaje")
        if p is None:
            continue
        fecha = (r.get("fecha") or r.get("created_at") or "")[:10]
        hora = r.get("hora") or r.get("created_at") or ""
        valencia = r.get("valencia") or "neutral"
        intensidad = r.get("intensidad")
        if intensidad is None:
            intensidad = (11 - float(p)) if valencia == "negativa" else float(p)
        points.append((fecha, hora, float(intensidad), valencia))
    points.sort(key=lambda item: (item[0] or "9999-99-99", item[1] or ""))
    puntajes = [p for _, _, p, _ in points]
    fechas = [fecha or "—" for fecha, _, _, _ in points]
    pos_idx = [i for i, pt in enumerate(points) if pt[3] != "negativa"]
    pos_vals = [points[i][2] for i in pos_idx]
    neg_idx = [i for i, pt in enumerate(points) if pt[3] == "negativa"]
    neg_vals = [points[i][2] for i in neg_idx]

    if not puntajes:
        lbl = QLabel("Sin registros de ánimo")
        lbl.setFont(qfont("size_body"))
        lbl.setStyleSheet(f"color: {c['text_tertiary']};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    # Configurar pyqtgraph con tema
    pg.setConfigOption("background", "transparent")
    pg.setConfigOption("foreground", v3c("text", modo).name())

    class _StaticPlot(pg.PlotWidget):
        """Gráfico clínico de LECTURA (informe owner v1.0, frente 4): la
        rueda del mouse NO hace zoom/pan — se ignora y propaga al scroll de
        la página. setMouseEnabled(False) solo no alcanza: pyqtgraph igual
        consume el wheel y congela el scroll del contenedor."""

        def wheelEvent(self, ev):  # noqa: N802 (Qt override)
            ev.ignore()

    plot = _StaticPlot()
    plot.setBackground("transparent")
    # Estático de lectura: sin zoom/pan, sin menú contextual (en inglés),
    # sin botón de autoescala, sin robar foco.
    plot.setMouseEnabled(x=False, y=False)
    try:
        plot.getPlotItem().setMenuEnabled(False)
        plot.getPlotItem().hideButtons()
    except Exception:
        pass
    plot.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    if compact:
        # Antes capeado a 124: en el Resumen la card daba ~200px y el chart
        # quedaba "colapsado" con espacio muerto debajo. Lo dejamos crecer para
        # llenar la card (expandido y redistribuido — pedido owner).
        plot.setMinimumHeight(132)
        plot.setMaximumHeight(172)
    else:
        # Registros (Fase 4): gráfico menos dominante para que la lista de
        # registros quede visible sin scroll inicial. Antes 156-176px empujaba
        # las filas fuera del viewport 960×600.
        plot.setMinimumHeight(132)
        plot.setMaximumHeight(148)

    # Eje Y — padding inferior y altura del eje X suficientes para que la
    # etiqueta "0" no se recorte (feedback owner v1.0: en la mayoría de los
    # diagramas el 0 quedaba cortado). En compact el rango baja a -1.9 para
    # que las fechas (TextItems) entren DEBAJO de la línea de base 0 sin
    # pisarse con el área rellena ni recortarse.
    if compact:
        plot.setYRange(-1.9, 11, padding=0)
    else:
        plot.setYRange(0, 11, padding=0.08)
    tick_font = qfont("size_caption_xs" if compact else "size_caption")
    plot.getAxis("left").setTickFont(tick_font)
    bottom_axis = plot.getAxis("bottom")
    bottom_axis.setTickFont(tick_font)
    bottom_axis.setHeight(20 if compact else 40)
    bottom_axis.setStyle(showValues=not compact, tickTextOffset=6)

    # Etiquetas del eje X (fechas) — UNA por día: varios registros del mismo
    # día caían en índices distintos y el eje mostraba "06-10 06-10"
    # superpuesto (informe owner v1.0, frente 4).
    step = max(1, (len(fechas) - 1) // 5)
    tick_indexes = sorted(set(range(0, len(fechas), step)) | {0, len(fechas) - 1})
    ticks = []
    prev_label = None
    for i in tick_indexes:
        # "DD/MM" legible (es-AR) en vez del "MM-DD" ISO crudo, que leía técnico.
        f = fechas[i]
        label = f"{f[8:10]}/{f[5:7]}" if len(f) >= 10 and f != "—" else "—"
        if label == prev_label:
            continue
        ticks.append((i, label))
        prev_label = label
    bottom_axis.setTicks([ticks])

    def _smooth(idx: list, vals: list):
        """Spline suave por serie (>=4 puntos); si no, lineal cruda."""
        if len(idx) >= 4:
            try:
                from scipy.interpolate import make_interp_spline

                xs = np.linspace(idx[0], idx[-1], max(len(idx) * 8, 16))
                spline = make_interp_spline(idx, vals, k=3)
                return xs, np.clip(spline(xs), 0, 10)
            except ImportError:
                pass
        return np.array(idx, dtype=float), np.array(vals)

    danger = C("danger", modo)

    # ── Serie POSITIVA: área teal→violet + línea + puntos ────────────────
    if pos_vals:
        xs_p, ys_p = _smooth(pos_idx, pos_vals)
        teal_c = QColor(accent)
        violet_c = QColor(teal)
        fill_grad = QLinearGradient(0, 0, 0, 1)
        fill_grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        fill_grad.setColorAt(0.0, QColor(teal_c.red(), teal_c.green(), teal_c.blue(), 80))
        fill_grad.setColorAt(1.0, QColor(violet_c.red(), violet_c.green(), violet_c.blue(), 10))
        fill = pg.FillBetweenItem(
            pg.PlotDataItem(xs_p, ys_p),
            pg.PlotDataItem(xs_p, [0] * len(xs_p)),
            brush=pg.mkBrush(QBrush(fill_grad)),
        )
        plot.addItem(fill)
        plot.plot(xs_p, ys_p, pen=pg.mkPen(color=accent, width=1.5))
        plot.addItem(
            pg.ScatterPlotItem(
                x=pos_idx, y=pos_vals, size=8, pen=pg.mkPen(None), brush=pg.mkBrush(teal)
            )
        )
    # ── Serie NEGATIVA: línea cálida sin área (no compite, se distingue) ─
    if neg_vals:
        xs_n, ys_n = _smooth(neg_idx, neg_vals)
        plot.plot(xs_n, ys_n, pen=pg.mkPen(color=danger, width=1.5))
        plot.addItem(
            pg.ScatterPlotItem(
                x=neg_idx, y=neg_vals, size=8, pen=pg.mkPen(None), brush=pg.mkBrush(danger)
            )
        )
    if compact:
        label_color = v3c("text2", modo).name()
        for x_value, label in ticks:
            axis_label = pg.TextItem(label, color=label_color, anchor=(0.5, 0.0))
            axis_label.setFont(tick_font)
            # Bajo la línea de base 0 (el rango compact reserva -1.9): antes
            # quedaban pintadas SOBRE el borde del área rellena y se leían
            # como gráfico recortado.
            axis_label.setPos(x_value, -0.15)
            plot.addItem(axis_label)

    # Leyenda Positivo/Negativo: las dos series corren en paralelo y sin
    # rótulo no se distinguían (feedback owner). Dot en el color de serie,
    # texto en tinta secundaria.
    container = QWidget(parent)
    container.setStyleSheet("background: transparent;")
    cont_lay = QVBoxLayout(container)
    cont_lay.setContentsMargins(0, 0, 0, 0)
    cont_lay.setSpacing(0)
    cont_lay.addWidget(plot)
    legend_row = QHBoxLayout()
    legend_row.setContentsMargins(6, 4, 6, 2)
    legend_row.setSpacing(12)
    legend_row.addStretch()
    ink2 = v3c("text2", modo).name()
    for serie_lbl, serie_color in (("Positivo", teal), ("Negativo", danger)):
        lbl = QLabel(
            f'<span style="color:{serie_color}">●</span> '
            f'<span style="color:{ink2}">{serie_lbl}</span>'
        )
        lbl.setFont(qfont("size_caption_xs"))
        lbl.setStyleSheet("background: transparent;")
        legend_row.addWidget(lbl)
    cont_lay.addLayout(legend_row)
    return container


# ── Tab: Resumen ──────────────────────────────────────────────────────────────


class _TabResumen(QWidget):
    """Dashboard clínico unificado (2 columnas) alineado al mockup S10."""

    def __init__(self, modo: str, sb, pid: str, nombre: str, datos_ref, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._datos_ref = datos_ref
        self._setup()
        self._datos_ref.changed.connect(self._on_datos_loaded)

    def _setup(self):
        colors(self._modo)
        self._sp = V3_SP

        _outer = QVBoxLayout(self)
        _outer.setContentsMargins(0, 0, 0, 0)
        _outer.setSpacing(0)
        _content = QWidget()
        _content.setStyleSheet("background: transparent;")
        # Red anti-solape: a 960x600 la columna izquierda (chart 200 + nota +
        # actividad) supera el alto disponible y Qt comprimía bajo mínimo —
        # se recortaban los títulos (la tilde de "Últimos" desaparecía).
        # Scroll calmo solo cuando falta alto.
        _res_scroll = QScrollArea()
        _res_scroll.setWidgetResizable(True)
        _res_scroll.setFrameShape(QFrame.Shape.NoFrame)
        _res_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        _res_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        _res_scroll.setWidget(_content)
        _outer.addWidget(_res_scroll)

        main_lay = QHBoxLayout(_content)
        # M3 premium: más aire entre columnas y arriba/abajo (cards no apretadas).
        main_lay.setContentsMargins(self._sp["lg"], self._sp["sm"], self._sp["lg"], self._sp["sm"])
        main_lay.setSpacing(self._sp["md"])

        # Columna Izquierda (1.6fr)
        left = QVBoxLayout()
        left.setSpacing(self._sp["sm"])

        # 1. Chart Card
        self._chart_card = NMCard(modo=self._modo, clickable=False)
        self._chart_card.setMinimumHeight(204)
        cc_lay = QVBoxLayout(self._chart_card)
        cc_lay.setContentsMargins(self._sp["md"], self._sp["xs"], self._sp["md"], self._sp["xs"])
        cc_lay.setSpacing(0)
        cc_lay.addWidget(NMSectionHeader("Evolución anímica", "Últimos 30 días", modo=self._modo))
        cc_lay.itemAt(0).widget()._title.setFont(v3_font("size_h2", weight=600, serif=True))

        self._chart_placeholder = QWidget()
        self._chart_placeholder.setMinimumHeight(152)
        self._chart_placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._chart_lay = QVBoxLayout(self._chart_placeholder)
        self._chart_lay.setContentsMargins(0, 0, 0, 0)
        cc_lay.addWidget(self._chart_placeholder, stretch=1)
        left.addWidget(self._chart_card)

        # 2. Nota Clínica
        from shared.visual_qa import visual_qa_enabled

        note_sub = "18 oct" if visual_qa_enabled() else "—"
        note_text = (
            '"Refiere insomnio de mantenimiento. Trabajamos psicoeducación sobre rumiación nocturna. '
            'Pauté registro pensamiento y respiración 4-7-8 antes de dormir."'
            if visual_qa_enabled()
            else "Sin notas todavía."
        )
        self._note_card = NMCard(modo=self._modo, clickable=False)
        nc_lay = QVBoxLayout(self._note_card)
        nc_lay.setContentsMargins(self._sp["md"], self._sp["xs"], self._sp["md"], self._sp["xs"])
        self._note_header = NMSectionHeader("Última nota", note_sub, modo=self._modo)
        self._note_header._title.setFont(v3_font("size_h2", weight=600, serif=True))
        nc_lay.addWidget(self._note_header)
        self._lbl_note = QLabel(note_text)
        self._lbl_note.setWordWrap(True)
        # Newsreader / Serif para notas clínicas premium
        self._lbl_note.setFont(qfont("size_body"))
        self._lbl_note.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent; line-height: 1.5;"
        )
        nc_lay.addWidget(self._lbl_note)
        left.addWidget(self._note_card)

        # 3. Actividad
        self._act_card = NMCard(modo=self._modo, clickable=False)
        ac_lay = QVBoxLayout(self._act_card)
        ac_lay.setContentsMargins(self._sp["md"], self._sp["xs"], self._sp["md"], self._sp["xs"])
        ac_lay.addWidget(NMSectionHeader("Actividad del paciente", "Reciente", modo=self._modo))
        ac_lay.itemAt(0).widget()._title.setFont(v3_font("size_h2", weight=600, serif=True))
        self._act_list = QVBoxLayout()
        self._act_list.setSpacing(2)
        ac_lay.addLayout(self._act_list)
        left.addWidget(self._act_card)

        left.addStretch()
        main_lay.addLayout(left, stretch=16)

        # Columna Derecha (1fr)
        right = QVBoxLayout()
        right.setSpacing(self._sp["sm"])

        # 1. Bio / Info
        self._bio_card = NMCard(modo=self._modo, clickable=False)
        bc_lay = QVBoxLayout(self._bio_card)
        bc_lay.setContentsMargins(self._sp["md"], self._sp["xs"], self._sp["md"], self._sp["xs"])
        bc_lay.setSpacing(6)
        # "PERFIL" y no "DATOS BIO": lenguaje clínico-humano, no jerga de ficha
        # técnica (informe owner v1.0: nada de rótulos de developer).
        bc_lay.addWidget(NMSectionHeader("Perfil", "Paciente", modo=self._modo))
        bc_lay.itemAt(0).widget()._title.setFont(v3_font("size_h2", weight=600, serif=True))

        age_text = (
            "41 años · paciente desde mar 2024"
            if visual_qa_enabled()
            else "Se completa con la actividad del paciente en la Suite."
        )
        age = QLabel(age_text)
        age.setFont(qfont("size_caption"))
        age.setStyleSheet(f"color: {v3c('text2', self._modo).name()};")
        bc_lay.addWidget(age)

        bc_lay.addWidget(NMDivider(modo=self._modo))

        tags_lay = QHBoxLayout()
        tags_lay.setSpacing(6)
        from shared.components import NMBadge

        if visual_qa_enabled():
            tags_lay.addWidget(NMBadge("Depresión", modo=self._modo))
            tags_lay.addWidget(NMBadge("Sueño", modo=self._modo))
        else:
            tags_lay.addWidget(NMBadge("Sin datos", modo=self._modo))
        tags_lay.addStretch()
        bc_lay.addLayout(tags_lay)
        right.addWidget(self._bio_card)

        # 2. Featured / Metrics
        self._featured_card = NMFeaturedCard(modo=self._modo)
        right.addWidget(self._featured_card)

        # 3. Legal Status
        self._legal_card = NMCard(modo=self._modo, clickable=False)
        lc_lay = QVBoxLayout(self._legal_card)
        lc_lay.setContentsMargins(self._sp["md"], self._sp["xs"], self._sp["md"], self._sp["xs"])
        lc_lay.setSpacing(6)
        lc_lay.addWidget(NMSectionHeader("Estado legal", "Consentimiento", modo=self._modo))
        lc_lay.itemAt(0).widget()._title.setFont(v3_font("size_h2", weight=600, serif=True))

        self._lbl_legal = QLabel("Consultando...")
        self._lbl_legal.setWordWrap(True)
        self._lbl_legal.setFont(qfont("size_caption"))
        self._lbl_legal.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
        # La constancia muestra 3 líneas (estado / aceptado / versiones) que
        # pueden envolver a 4 en columnas angostas: reservar 4.2 líneas para
        # que NINGÚN texto legal quede cortado/comprimido (informe owner v1.0).
        self._lbl_legal.setMinimumHeight(
            int(self._lbl_legal.fontMetrics().lineSpacing() * 4.2)
        )
        lc_lay.addWidget(self._lbl_legal)



        right.addWidget(self._legal_card)

        right.addStretch()
        main_lay.addLayout(right, stretch=10)

    @property
    def lbl_legal(self):
        return self._lbl_legal



    def _on_datos_loaded(self, cache: dict):
        # Actualizar gráfico
        registros = cache.get("animo", [])
        while self._chart_lay.count():
            self._chart_lay.takeAt(0).widget().deleteLater()

        graph = _build_animo_graph(self, registros, self._modo, compact=True)
        self._chart_lay.addWidget(graph)

        # Actualizar actividad dinámicamente desde el caché
        while self._act_list.count():
            item = self._act_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    item.layout().takeAt(0).widget().deleteLater()

        from shared.visual_qa import visual_qa_enabled

        if visual_qa_enabled():
            actividades = [
                'Diario · "Otra noche sin dormir" · hoy 03:14',
                "Registro de ánimo 2/10 · hoy 08:12",
                "Respiración 4-7-8 · ayer 23:40",
            ]
        else:
            import datetime as dt_mod
            hoy_str = dt_mod.date.today().isoformat()
            ayer_str = (dt_mod.date.today() - dt_mod.timedelta(days=1)).isoformat()

            def format_dia(fecha, hora):
                f = (fecha or "")[:10]
                h = f" {hora[:5]}" if hora else ""
                if f == hoy_str:
                    return f"hoy{h}"
                elif f == ayer_str:
                    return f"ayer{h}"
                elif len(f) == 10 and f[4] == "-":
                    return f"{f[8:10]}/{f[5:7]}{h}"
                return f"{f}{h}"

            actividades_reales = []

            # 1. Animo
            for r in cache.get("animo", []):
                fecha = r.get("fecha") or ""
                hora = r.get("hora") or ""
                score = r.get("puntaje")
                if fecha and score is not None:
                    actividades_reales.append((
                        fecha,
                        hora,
                        f"Registro de ánimo {score}/10 · {format_dia(fecha, hora)}"
                    ))

            # 2. Resp
            for r in cache.get("resp", []):
                fecha = r.get("fecha") or ""
                hora = r.get("hora") or ""
                tec = r.get("tecnica") or "Respiración"
                dur = r.get("duracion_minutos") or 0
                if fecha:
                    actividades_reales.append((
                        fecha,
                        hora,
                        f"Respiración {tec} ({dur} min) · {format_dia(fecha, hora)}"
                    ))

            # 3. Pensamientos
            for r in cache.get("pens", []):
                fecha = r.get("fecha") or ""
                hora = r.get("hora") or ""
                emo = r.get("emocion") or "Pensamiento"
                if fecha:
                    actividades_reales.append((
                        fecha,
                        hora,
                        f"Registro de pensamiento ({emo}) · {format_dia(fecha, hora)}"
                    ))

            # 4. Timer
            for r in cache.get("timer", []):
                fecha = r.get("fecha") or ""
                hora = r.get("hora") or ""
                nombre = r.get("nombre") or "Actividad"
                dur = (r.get("duracion_real") or 0) // 60
                if fecha:
                    actividades_reales.append((
                        fecha,
                        hora,
                        f"Temporizador: {nombre} ({dur} min) · {format_dia(fecha, hora)}"
                    ))

            # 5. Checklist
            for r in cache.get("checklist", []):
                fecha = r.get("fecha") or ""
                desc = r.get("descripcion") or "Tarea completada"
                if fecha:
                    actividades_reales.append((
                        fecha,
                        "",
                        f"Checklist: {desc} · {format_dia(fecha, '')}"
                    ))

            # 6. Activacion
            for r in cache.get("activacion", []):
                fecha = r.get("fecha") or ""
                hora = r.get("hora") or ""
                act = r.get("actividad") or "Activación"
                res = r.get("resultado") or ""
                if fecha:
                    actividades_reales.append((
                        fecha,
                        hora,
                        f"Activación: {act} ({res}) · {format_dia(fecha, hora)}"
                    ))

            # Ordenar por fecha y hora descendente
            actividades_reales.sort(key=lambda x: (x[0], x[1]), reverse=True)

            if actividades_reales:
                actividades = [item[2] for item in actividades_reales[:3]]
            else:
                actividades = ["Sin actividad reciente."]

        for text in actividades:
            lbl = QLabel(text)
            lbl.setFont(qfont("size_caption"))
            lbl.setStyleSheet(f"color: {v3c('text2', self._modo).name()}; padding: 6px 0;")
            self._act_list.addWidget(lbl)
            self._act_list.addWidget(NMDivider(modo=self._modo, alpha=40))

        # Actualizar NMFeaturedCard con promedio de ánimo calculado
        self._refresh_featured_card(cache)

        # Actualizar Última nota con la última nota escrita por el paciente
        if not visual_qa_enabled():
            animo = cache.get("animo", [])
            ultima_nota = None
            fecha_nota = ""
            for r in animo:
                nota_val = r.get("nota")
                if nota_val and isinstance(nota_val, str) and nota_val.strip():
                    ultima_nota = nota_val.strip()
                    fecha_nota = r.get("fecha") or ""
                    break

            if ultima_nota:
                self._lbl_note.setText(f'"{ultima_nota}"')
                if fecha_nota:
                    try:
                        parts = fecha_nota.split("-")
                        if len(parts) == 3:
                            meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                            dia = int(parts[2])
                            mes_idx = int(parts[1]) - 1
                            if 0 <= mes_idx < 12:
                                fecha_lbl = f"{dia} {meses[mes_idx]}"
                            else:
                                fecha_lbl = f"{dia}/{parts[1]}"
                        else:
                            fecha_lbl = fecha_nota
                    except Exception:
                        fecha_lbl = fecha_nota
                    self._note_header.set_title(fecha_lbl)
                else:
                    self._note_header.set_title("Reciente")
            else:
                self._lbl_note.setText("Sin notas todavía.")
                self._note_header.set_title("—")

    def _refresh_featured_card(self, cache: dict):
        """Computa promedio de ánimo y actualiza NMFeaturedCard si hay datos."""
        if not hasattr(self, "_featured_card"):
            return
        animo = cache.get("animo", [])
        con_puntaje = [r for r in animo if r.get("puntaje") is not None]
        if not con_puntaje:
            return

        def _fecha_key(r):
            return r.get("fecha") or r.get("creado_en") or ""

        ordenados = sorted(con_puntaje, key=_fecha_key, reverse=True)
        recientes = [r["puntaje"] for r in ordenados[:7]]
        prom = sum(recientes) / len(recientes)

        emoji = "😞" if prom < 4 else "😐" if prom < 7 else "😊"
        self._featured_card.set_score(round(prom, 1), emoji)

        previos = [r["puntaje"] for r in ordenados[7:14]]
        if previos:
            self._featured_card.set_delta(round(prom - sum(previos) / len(previos), 1))
        else:
            self._featured_card.set_delta(None)

        # Sparkline de tendencia (orden cronológico) para que la card muestre la
        # serie de ánimo en lugar de dejar un vacío bajo el score. Misma señal que
        # usa la card del dashboard; <2 puntos no renderiza línea y queda oculto.
        serie = [r["puntaje"] for r in reversed(ordenados[:7])]
        if len(serie) >= 2:
            self._featured_card.set_series(serie)
        # Desglose pos/neg de los recientes (intensidad cruda por valencia):
        # el índice combinado no oculta los registros negativos.
        _rec = ordenados[: len(recientes)]
        _pos = [
            r.get("intensidad") if r.get("intensidad") is not None else r["puntaje"]
            for r in _rec
            if (r.get("valencia") or "neutral") != "negativa"
        ]
        _neg = [
            r.get("intensidad")
            if r.get("intensidad") is not None
            else 11 - r["puntaje"]
            for r in _rec
            if (r.get("valencia") or "neutral") == "negativa"
        ]
        _partes = [f"{len(con_puntaje)} registros"]
        if _pos:
            _partes.append(f"positivo {sum(_pos) / len(_pos):.1f}")
        if _neg:
            _partes.append(f"negativo {sum(_neg) / len(_neg):.1f}")
        self._featured_card.set_meta(" · ".join(_partes))

    def _apply_theme(self, modo: str):
        self._modo = modo
        # Re-render? For now enough with CSS
        pass


# ── Tab: Registros ────────────────────────────────────────────────────────────


class _TabRegistros(QWidget):
    _datos_loaded_signal = pyqtSignal(dict)
    _PDF_SECCIONES = [
        ("animo", "Termómetro Emocional"),
        ("resp", "Guía de Respiración Animada"),
        ("pens", "Registro de Pensamientos (TCC)"),
        ("checklist", "Checklist de Rutina Diaria"),
        ("timer", "Temporizador de Actividades"),
        ("reclog", "Recordatorios de Bienestar"),
        ("activacion", "Asistente de Activación Conductual"),
    ]

    def __init__(self, modo: str, sb, pid: str, nombre: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._datos_cache: dict = {}
        self._cargando = False
        self._datos_loaded_signal.connect(self._on_datos_loaded)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        layout.setSpacing(V3_SP["md"])

        # Botones top
        top = QHBoxLayout()
        btn_load = NMButton("Actualizar datos", modo=self._modo, variant="primary", size="sm", width=132)
        btn_load.setFixedHeight(32)
        btn_load.setMinimumWidth(130)
        btn_load.clicked.connect(self._cargar_datos)
        top.addWidget(btn_load)
        top.addStretch()
        # Acción secundaria (outline, no gradient): exportar no es el gesto
        # principal de la pestaña (informe owner v1.0, Registros).
        self._btn_pdf = NMButton("Exportar PDF", modo=self._modo, variant="secondary", size="sm", width=130)
        self._btn_pdf.setFixedHeight(32)
        self._btn_pdf.setMinimumWidth(130)
        self._btn_pdf.clicked.connect(self._exportar_pdf)
        top.addWidget(self._btn_pdf)
        layout.addLayout(top)

        # Scroll de registros
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._list_w = QWidget()
        self._list_w.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_w)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(12)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._list_w)
        layout.addWidget(self._scroll)

        # Placeholder
        ph = NMEmptyState(
            "users",
            "Registros del paciente",
            "Cargá el historial para ver las métricas de evolución.",
            cta_primary="Actualizar datos",
            parent=self
        )
        ph.cta_primary_clicked.connect(self._cargar_datos)
        self._list_layout.addWidget(ph)

    def _cargar_datos(self):
        from shared.visual_qa import visual_qa_enabled

        if visual_qa_enabled():
            datos = {
                "animo": [
                    {
                        "fecha": "2026-05-23",
                        "hora": "08:12",
                        "puntaje": 7,
                        "nota": "Me siento tranquilo y en control",
                    },
                    {
                        "fecha": "2026-05-22",
                        "hora": "09:00",
                        "puntaje": 6,
                        "nota": "Estable con leves fluctuaciones",
                    },
                    {
                        "fecha": "2026-05-21",
                        "hora": "10:15",
                        "puntaje": 8,
                        "nota": "Muy bien hoy, alta energia y foco",
                    },
                    {
                        "fecha": "2026-05-20",
                        "hora": "08:30",
                        "puntaje": 4,
                        "nota": "Un poco ansioso y con insomnio previo",
                    },
                    {
                        "fecha": "2026-05-19",
                        "hora": "09:45",
                        "puntaje": 7,
                        "nota": "Buen dia, logre caminar 30 minutos",
                    },
                ],
                "resp": [
                    {
                        "fecha": "2026-05-22",
                        "hora": "23:40",
                        "tecnica": "4-7-8",
                        "duracion_minutos": 5,
                    },
                    {
                        "fecha": "2026-05-20",
                        "hora": "22:15",
                        "tecnica": "Caja",
                        "duracion_minutos": 8,
                    },
                ],
                "pens": [
                    {
                        "fecha": "2026-05-22",
                        "hora": "14:30",
                        "emocion": "Tristeza",
                        "intensidad": 8,
                        "pensamiento": "Siento que no puedo terminar mis tareas a tiempo y fallaré a todos.",
                    },
                    {
                        "fecha": "2026-05-20",
                        "hora": "18:00",
                        "emocion": "Ansiedad",
                        "intensidad": 6,
                        "pensamiento": "Preocupación excesiva por la reunión de evaluación de mañana.",
                    },
                ],
                "checklist": [],
                "timer": [
                    {
                        "fecha": "2026-05-22",
                        "hora": "16:00",
                        "nombre": "Foco Trabajo",
                        "duracion_real": 1500,
                    },
                    {
                        "fecha": "2026-05-21",
                        "hora": "11:20",
                        "nombre": "Meditación Guiada",
                        "duracion_real": 600,
                    },
                ],
                "reclog": [
                    {
                        "fecha": "2026-05-22",
                        "hora": "12:00",
                        "mensaje": "Es hora de tomar tu pausa activa de 5 minutos.",
                    },
                    {
                        "fecha": "2026-05-21",
                        "hora": "09:00",
                        "mensaje": "Completar el registro de animo diario en la aplicacion.",
                    },
                ],
                "activacion": [
                    {
                        "fecha": "2026-05-22",
                        "hora": "18:30",
                        "energia": 6,
                        "actividad": "Caminata 20 min",
                        "resultado": "hice",
                    },
                    {
                        "fecha": "2026-05-21",
                        "hora": "11:00",
                        "energia": 3,
                        "actividad": "Llamar a un amigo",
                        "resultado": "no pude",
                    },
                ],
            }
            self._on_datos_loaded(datos)
            return

        if not self._sb or self._cargando:
            return
        self._cargando = True
        colors(self._modo)
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                self._list_layout.removeWidget(w)
                w.deleteLater()
        # NMSkeleton loaders mientras carga
        for _ in range(5):
            sk = NMSkeleton(width=240, height=16, radius=4, modo=self._modo)
            self._list_layout.addWidget(sk)

        def _fetch():
            datos = {}
            tablas = {
                "animo": (
                    "mood_records",
                    "fecha,hora,puntaje,nota,emocion,valencia,intensidad",
                    20,
                ),
                "resp": ("breathing_sessions", "fecha,hora,tecnica,duracion_minutos", 15),
                "pens": ("thought_records", "fecha,hora,emocion,intensidad,pensamiento", 15),
                "checklist": ("checklist_completions", "fecha,descripcion,categoria,origen", 30),
                "timer": ("timer_sessions", "fecha,hora,nombre,categoria,duracion_real", 15),
                "reclog": ("reminder_logs", "fecha,hora,mensaje,cerrado", 15),
                "activacion": (
                    "activation_results",
                    "fecha,hora,energia,actividad,resultado",
                    20,
                ),
                "dbt": (
                    "dbt_practice_records",
                    "fecha,hora,skill_id,skill_version,familia,necesidad,malestar_antes,malestar_despues,resultado,duracion_seg,nota,created_at",
                    30,
                ),
            }
            for clave, (tabla, campos, lim) in tablas.items():
                try:
                    res = (
                        self._sb.table(tabla)
                        .select(campos)
                        .eq("patient_id", self._pid)
                        .order("fecha", desc=True)
                        .limit(lim)
                        .execute()
                    )
                    datos[clave] = res.data or []
                except Exception:
                    datos[clave] = []
            self._datos_loaded_signal.emit(datos)

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_datos_loaded(self, datos: dict):
        if sip.isdeleted(self):
            return
        self._datos_ref.cache = datos
        self._datos_cache = datos
        self._cargando = False
        self._datos_ref.changed.emit(datos)
        self._mostrar_registros(datos)

    def _render_registro_row(self, tipo: str, r: dict) -> QFrame:
        from shared.theme_qt import v3c

        row = QFrame()
        row.setObjectName("RecordRow")
        row.setStyleSheet(f"""
            QFrame#RecordRow {{
                background: {v3c("surface", self._modo).name()};
                border: 1px solid {qcolor_to_rgba_css(v3c("borderSoft", self._modo))};
                border-radius: 8px;
            }}
            QFrame#RecordRow:hover {{
                background: {v3c("surface_2", self._modo).name()};
                border: 1px solid {qcolor_to_rgba_css(v3c("borderStrong", self._modo))};
            }}
        """)

        lay = QHBoxLayout(row)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(16)

        fecha_str = r.get("fecha", "")[:10]
        # "DD/MM/AAAA" legible (es-AR) en vez del ISO crudo "AAAA-MM-DD".
        if len(fecha_str) == 10 and fecha_str[4] == "-":
            fecha_str = f"{fecha_str[8:10]}/{fecha_str[5:7]}/{fecha_str[0:4]}"
        hora_str = r.get("hora", "")[:5]

        time_lay = QVBoxLayout()
        time_lay.setSpacing(2)

        lbl_fecha = QLabel(fecha_str)
        lbl_fecha.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_medium"]))
        lbl_fecha.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        time_lay.addWidget(lbl_fecha)

        if hora_str:
            lbl_hora = QLabel(hora_str)
            lbl_hora.setFont(qfont("size_caption"))
            lbl_hora.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
            time_lay.addWidget(lbl_hora)

        time_widget = QWidget()
        time_widget.setStyleSheet("background: transparent;")
        time_widget.setLayout(time_lay)
        time_widget.setFixedWidth(110)
        lay.addWidget(time_widget)

        content_lay = QVBoxLayout()
        content_lay.setSpacing(4)

        if tipo == "animo":
            score = r.get("puntaje", "—")
            nota = r.get("nota") or ""
            # Registro pos/neg separado: el badge muestra el lado REAL del
            # registro ("Negativo 9 · Tristeza"), no el bienestar invertido.
            valencia = r.get("valencia") or "neutral"
            emocion = r.get("emocion") or ""
            intensidad = r.get("intensidad")
            if intensidad is None:
                try:
                    intensidad = (
                        11 - int(score) if valencia == "negativa" else int(score)
                    )
                except Exception:
                    intensidad = score

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)

            lbl_title = QLabel("Termómetro Emocional")
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            if valencia == "negativa":
                _lado = "Negativo"
            elif valencia == "positiva":
                _lado = "Positivo"
            else:
                _lado = "Ánimo"
            _detalle = f" · {emocion}" if emocion else ""
            badge = QLabel(f"{_lado} {intensidad}/10{_detalle}")
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))

            if valencia == "negativa":
                color = v3c("danger", self._modo).name()
            else:
                try:
                    _iv = int(intensidad)
                    color = (
                        v3c("teal", self._modo).name()
                        if _iv >= 7
                        else v3c("amber", self._modo).name()
                        if _iv >= 4
                        else v3c("primary", self._modo).name()
                    )
                except Exception:
                    color = v3c("primary", self._modo).name()

            _style_mini_pill(badge, color)
            top_lay.addWidget(badge)
            top_lay.addStretch()
            content_lay.addLayout(top_lay)

            if nota:
                lbl_nota = QLabel(f'"{nota}"')
                lbl_nota.setFont(qfont("size_small"))
                lbl_nota.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; font-style: italic; background: transparent;"
                )
                lbl_nota.setWordWrap(True)
                content_lay.addWidget(lbl_nota)

        elif tipo == "resp":
            tecnica = r.get("tecnica", "Desconocida")
            duracion = r.get("duracion_minutos", "?")

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)

            lbl_title = QLabel(f"Guía de Respiración Animada: {tecnica}")
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            badge = QLabel(f"{duracion} min")
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            color = v3c("teal", self._modo).name()
            _style_mini_pill(badge, color)
            top_lay.addWidget(badge)
            top_lay.addStretch()
            content_lay.addLayout(top_lay)

        elif tipo == "pens":
            emocion = r.get("emocion", "?")
            intensidad = r.get("intensidad", "?")
            pensamiento = r.get("pensamiento", "")

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)

            lbl_title = QLabel(f"Registro de Pensamientos (TCC): {emocion}")
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            badge = QLabel(f"Intensidad: {intensidad}/10")
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            color = v3c("accent", self._modo).name()
            _style_mini_pill(badge, color)
            top_lay.addWidget(badge)
            top_lay.addStretch()
            content_lay.addLayout(top_lay)

            if pensamiento:
                lbl_pens = QLabel(pensamiento)
                lbl_pens.setFont(qfont("size_small"))
                lbl_pens.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; background: transparent;"
                )
                lbl_pens.setWordWrap(True)
                content_lay.addWidget(lbl_pens)

        elif tipo == "timer":
            nombre = r.get("nombre") or "Sin nombre"
            duracion_real = r.get("duracion_real") or 0
            mins = duracion_real // 60

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)

            lbl_title = QLabel(f"Temporizador de Actividades: {nombre}")
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            badge = QLabel(f"{mins} min")
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            color = v3c("primary", self._modo).name()
            _style_mini_pill(badge, color)
            top_lay.addWidget(badge)
            top_lay.addStretch()
            content_lay.addLayout(top_lay)

        elif tipo == "reclog":
            mensaje = r.get("mensaje") or ""

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)

            lbl_title = QLabel("Recordatorios de Bienestar")
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            badge = QLabel("Notificación")
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            color = v3c("amber", self._modo).name()
            _style_mini_pill(badge, color)
            top_lay.addWidget(badge)
            top_lay.addStretch()
            content_lay.addLayout(top_lay)

            if mensaje:
                lbl_msg = QLabel(mensaje)
                lbl_msg.setFont(qfont("size_small"))
                lbl_msg.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; background: transparent;"
                )
                lbl_msg.setWordWrap(True)
                content_lay.addWidget(lbl_msg)

        elif tipo == "activacion":
            actividad = r.get("actividad") or "Actividad"
            resultado = (r.get("resultado") or "").lower()
            energia = r.get("energia")

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)
            lbl_title = QLabel(actividad)
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            hecho = resultado in ("hice", "hecha", "hecho", "completada", "si", "sí")
            badge_txt = "Hizo" if hecho else "No pudo"
            color = v3c("teal" if hecho else "amber", self._modo).name()
            badge = QLabel(badge_txt)
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            _style_mini_pill(badge, color)
            top_lay.addWidget(badge)
            top_lay.addStretch()
            if energia is not None:
                lbl_e = QLabel(f"Energía {energia}/10")
                lbl_e.setFont(qfont("size_caption"))
                lbl_e.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; background: transparent;"
                )
                top_lay.addWidget(lbl_e)
            content_lay.addLayout(top_lay)

        elif tipo == "dbt":
            DBT_SKILLS_TITLES = {
                "mind_observe": "Observar y describir",
                "mind_wise": "Mente sabia",
                "distress_stop": "STOP",
                "distress_senses": "Autocalma con los sentidos",
                "emotion_facts": "Verificar los hechos",
                "emotion_opposite": "Acción opuesta",
                "interpersonal_dearman": "DEAR MAN",
                "interpersonal_givefast": "GIVE / FAST",
            }
            DBT_FAMILY_TITLES = {
                "mindfulness": "Mindfulness",
                "distress_tolerance": "Tolerancia al malestar",
                "emotion_regulation": "Regulación emocional",
                "interpersonal_effectiveness": "Efectividad interpersonal"
            }
            DBT_RESULT_LABELS = {
                "ayudo": "Me ayudó",
                "parcial": "Un poco",
                "no_esta_vez": "No esta vez",
                "sin_evaluar": "Sin evaluar"
            }

            skill_id = r.get("skill_id", "")
            title = DBT_SKILLS_TITLES.get(skill_id, skill_id)
            familia = r.get("familia") or ""
            fam_title = DBT_FAMILY_TITLES.get(familia, familia.capitalize())
            dur_seg = r.get("duracion_seg") or 0
            mins = max(1, dur_seg // 60)
            antes = r.get("malestar_antes")
            despues = r.get("malestar_despues")
            resultado = r.get("resultado") or "sin_evaluar"
            res_label = DBT_RESULT_LABELS.get(resultado, "Sin evaluar")
            nota = r.get("nota") or ""

            top_lay = QHBoxLayout()
            top_lay.setSpacing(8)

            lbl_title = QLabel(f"Práctica DBT: {title}")
            lbl_title.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            top_lay.addWidget(lbl_title)

            # Badge for result
            res_color = {
                "ayudo": v3c("teal", self._modo).name(),
                "parcial": v3c("amber", self._modo).name(),
                "no_esta_vez": v3c("danger", self._modo).name(),
                "sin_evaluar": v3c("bg_subtle", self._modo).name()
            }.get(resultado, v3c("bg_subtle", self._modo).name())

            badge = QLabel(res_label)
            badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            _style_mini_pill(badge, res_color)
            top_lay.addWidget(badge)

            # Duration badge
            dur_badge = QLabel(f"{mins} min")
            dur_badge.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
            _style_mini_pill(dur_badge, v3c("primary", self._modo).name())
            top_lay.addWidget(dur_badge)

            top_lay.addStretch()

            # Malestar comparison
            if antes is not None or despues is not None:
                antes_str = str(antes) if antes is not None else "—"
                despues_str = str(despues) if despues is not None else "—"
                lbl_malestar = QLabel(f"Malestar: {antes_str} → {despues_str}")
                lbl_malestar.setFont(qfont("size_caption"))
                lbl_malestar.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; background: transparent;"
                )
                top_lay.addWidget(lbl_malestar)

            content_lay.addLayout(top_lay)

            # Familia + Necesidad subtitle
            necesidad = r.get("necesidad") or ""
            sub_text = f"Familia: {fam_title}"
            if necesidad:
                sub_text += f" · Necesidad: {necesidad}"
            lbl_sub = QLabel(sub_text)
            lbl_sub.setFont(qfont("size_caption"))
            lbl_sub.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
            content_lay.addWidget(lbl_sub)

            if nota:
                lbl_nota = QLabel(f'"{nota}"')
                lbl_nota.setFont(qfont("size_small"))
                lbl_nota.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; font-style: italic; background: transparent;"
                )
                lbl_nota.setWordWrap(True)
                content_lay.addWidget(lbl_nota)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_widget.setLayout(content_lay)
        lay.addWidget(content_widget, stretch=1)

        return row

    def _mostrar_registros(self, datos: dict):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                self._list_layout.removeWidget(w)
                w.deleteLater()

        c = colors(self._modo)

        def _seccion(titulo: str, filas: list, tipo: str):
            frame = NMCard(modo=self._modo, clickable=False)
            vl = QVBoxLayout(frame)
            vl.setContentsMargins(PAD_CARD, 14, PAD_CARD, 14)
            vl.setSpacing(10)

            t = QLabel(titulo)
            t.setFont(qfont("size_heading_m", weight=TYPOGRAPHY["weight_semibold"]))
            t.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
            vl.addWidget(t)

            if not filas:
                e = QLabel("Sin registros en esta seccion.")
                e.setFont(qfont("size_caption"))
                e.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
                vl.addWidget(e)
            else:
                for r in filas:
                    vl.addWidget(self._render_registro_row(tipo, r))
            self._list_layout.addWidget(frame)

        # Ánimo con promedio + gráfico
        animo = datos.get("animo", [])
        puntajes = [r.get("puntaje") for r in animo if r.get("puntaje") is not None]
        animo_frame = NMCard(modo=self._modo, clickable=False)
        avl = QVBoxLayout(animo_frame)
        avl.setContentsMargins(PAD_CARD, 14, PAD_CARD, 14)
        avl.setSpacing(10)

        at = QLabel("Termómetro Emocional")
        at.setFont(qfont("size_heading_m", weight=TYPOGRAPHY["weight_semibold"]))
        at.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        avl.addWidget(at)

        if puntajes:
            prom = round(sum(puntajes) / len(puntajes), 1)

            # Stats row: label + NMModuleRing
            stats_row = QHBoxLayout()
            pl = QLabel(f"Promedio: {prom}/10  |  {len(animo)} registros")
            pl.setFont(qfont("size_body"))
            pl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            stats_row.addWidget(pl, stretch=1)

            distinct_days = len({r.get("fecha", "")[:10] for r in animo if r.get("fecha")})
            adherence_pct = min(1.0, distinct_days / 7)
            # Ring de adherencia explicado (Fase 4): antes el "71%" flotaba sin
            # contexto. Ahora lleva caption "Adherencia 7d" y tooltip con el
            # detalle (N de 7 días con registro).
            ring_wrap = QWidget()
            ring_wrap.setStyleSheet("background: transparent;")
            rwl = QVBoxLayout(ring_wrap)
            rwl.setContentsMargins(0, 0, 0, 0)
            rwl.setSpacing(2)
            ring = NMModuleRing(size=44, pct=adherence_pct, modo=self._modo, parent=ring_wrap)
            rwl.addWidget(ring, alignment=Qt.AlignmentFlag.AlignHCenter)
            ring_cap = QLabel("Adherencia 7d")
            ring_cap.setFont(qfont("size_caption_xs"))
            ring_cap.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            ring_cap.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            ring_cap.setToolTip(f"{distinct_days} de 7 días con registro")
            rwl.addWidget(ring_cap)
            stats_row.addWidget(ring_wrap, alignment=Qt.AlignmentFlag.AlignRight)
            avl.addLayout(stats_row)

            # Gráfico pyqtgraph
            graph = _build_animo_graph(animo_frame, animo, self._modo)
            avl.addWidget(graph)

        for r in animo[:5]:
            avl.addWidget(self._render_registro_row("animo", r))
        self._list_layout.addWidget(animo_frame)

        _seccion("Guía de Respiración Animada", datos.get("resp", []), "resp")
        _seccion("Registro de Pensamientos (TCC)", datos.get("pens", []), "pens")
        _seccion("Temporizador de Actividades", datos.get("timer", []), "timer")
        _seccion("Recordatorios de Bienestar", datos.get("reclog", []), "reclog")
        _seccion("Asistente de Activación Conductual", datos.get("activacion", []), "activacion")

        # Prácticas DBT
        dbt_records = datos.get("dbt", [])
        dbt_frame = NMCard(modo=self._modo, clickable=False)
        dvl = QVBoxLayout(dbt_frame)
        dvl.setContentsMargins(PAD_CARD, 14, PAD_CARD, 14)
        dvl.setSpacing(10)

        dt = QLabel("Prácticas DBT")
        dt.setFont(qfont("size_heading_m", weight=TYPOGRAPHY["weight_semibold"]))
        dt.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        dvl.addWidget(dt)

        if not dbt_records:
            e = QLabel("Sin registros de prácticas DBT.")
            e.setFont(qfont("size_caption"))
            e.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            dvl.addWidget(e)
        else:
            DBT_SKILLS_TITLES = {
                "mind_observe": "Observar y describir",
                "mind_wise": "Mente sabia",
                "distress_stop": "STOP",
                "distress_senses": "Autocalma con los sentidos",
                "emotion_facts": "Verificar los hechos",
                "emotion_opposite": "Acción opuesta",
                "interpersonal_dearman": "DEAR MAN",
                "interpersonal_givefast": "GIVE / FAST",
            }
            DBT_FAMILY_TITLES = {
                "mindfulness": "Mindfulness",
                "distress_tolerance": "Tolerancia al malestar",
                "emotion_regulation": "Regulación emocional",
                "interpersonal_effectiveness": "Efectividad interpersonal"
            }

            # Calculate metrics
            total_practices = len(dbt_records)

            # Count families and skills
            families_count = {}
            skills_count = {}
            diffs = []
            for r in dbt_records:
                fam = r.get("familia") or ""
                skill = r.get("skill_id") or ""
                families_count[fam] = families_count.get(fam, 0) + 1
                skills_count[skill] = skills_count.get(skill, 0) + 1

                antes = r.get("malestar_antes")
                despues = r.get("malestar_despues")
                if antes is not None and despues is not None:
                    diffs.append(antes - despues)

            # Most used skill and family
            most_used_skill_id = max(skills_count, key=skills_count.get) if skills_count else None
            most_used_skill_title = DBT_SKILLS_TITLES.get(most_used_skill_id, most_used_skill_id) if most_used_skill_id else "Ninguna"

            most_used_fam_id = max(families_count, key=families_count.get) if families_count else None
            most_used_fam_title = DBT_FAMILY_TITLES.get(most_used_fam_id, most_used_fam_id.upper()) if most_used_fam_id else "Ninguna"

            stats_text = f"Total: {total_practices} prácticas  |  Familia más activa: {most_used_fam_title}  |  Habilidad más usada: {most_used_skill_title}"

            if diffs:
                avg_diff = round(sum(diffs) / len(diffs), 1)
                sign = "+" if avg_diff > 0 else ""
                stats_text += f"\nReducción prom. malestar (Autoinforme): {sign}{avg_diff} pts ({len(diffs)} pares completos)"
            else:
                stats_text += "\nReducción prom. malestar (Autoinforme): sin suficientes datos"

            lbl_stats = QLabel(stats_text)
            lbl_stats.setFont(qfont("size_caption"))
            lbl_stats.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;")
            lbl_stats.setWordWrap(True)
            dvl.addWidget(lbl_stats)

            # Render rows
            for r in dbt_records[:10]:
                dvl.addWidget(self._render_registro_row("dbt", r))

        self._list_layout.addWidget(dbt_frame)

    def _exportar_pdf(self):
        if not self._datos_cache:
            NMToast.display(self.window(), "Cargá los datos primero.", variant="info")
            return
        self._abrir_modal_exportacion()

    def _fechas_disponibles(self) -> list[str]:
        fechas = []
        for filas in self._datos_cache.values():
            if not isinstance(filas, list):
                continue
            for row in filas:
                fecha = (row.get("fecha") or "")[:10]
                if fecha:
                    fechas.append(fecha)
        return sorted(set(fechas))

    def _qdate_from_iso(self, value: str) -> QDate:
        try:
            y, m, d = [int(x) for x in value.split("-")]
            return QDate(y, m, d)
        except Exception:
            return QDate.currentDate()
    def _abrir_modal_exportacion(self):
        # 3.4: QDialog + NMDialogScaffold (mismo chrome/densidad que el Hub).
        # Antes usaba QDialog + apply_child_window_chrome con widgets crudos y
        # QSS hardcodeado. Ahora: scaffold temado, NMCard para secciones,
        # NMInput para filename, date fields con stylesheet_dateedit (theme-aware).
        dialog = QDialog(self, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setWindowTitle("Exportar informe")
        dialog.setModal(True)
        configure_adaptive_window(
            dialog,
            default_size=QSize(460, 560),
            min_size=QSize(400, 500),
        )
        from shared.adaptive_layout_qt import apply_native_rounded_corners
        apply_native_rounded_corners(dialog)

        def _center():
            dialog.adjustSize()
            p = dialog.parentWidget()
            if p:
                p_rect = p.rect()
                p_global = p.mapToGlobal(p_rect.topLeft())
                x = p_global.x() + (p_rect.width() - dialog.width()) // 2
                y = p_global.y() + (p_rect.height() - dialog.height()) // 2
                dialog.move(x, y)
        def _show_event(event):
            QDialog.showEvent(dialog, event)
            _center()
        dialog.showEvent = _show_event

        # Fondo opaco theme-aware (en light: surface; en dark: surfaceSolid).
        is_dark = "dark" in self._modo
        card_bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = qcolor_to_rgba_css(v3c("borderStrong" if is_dark else "border", self._modo))
        dialog.setStyleSheet(
            f"QDialog {{ background: {card_bg}; border: 1px solid {border}; "
            f"border-radius: {window_edge_radius()}px; }}"
            f"QLabel {{ color: {v3c('text', self._modo).name()}; background: transparent; }}"
            f"QCheckBox {{ color: {v3c('text', self._modo).name()}; background: transparent; "
            "spacing: 8px; padding: 4px 0; }"
            f"QCheckBox::indicator {{ width: 18px; height: 18px; "
            f"border: 1.5px solid {qcolor_to_rgba_css(v3c('borderStrong', self._modo))}; "
            f"border-radius: 5px; background: {v3c('bg', self._modo).name()}; }}"
            f"QCheckBox::indicator:checked {{ "
            f"background: {v3c('teal', self._modo).name()}; "
            f"border-color: {v3c('teal', self._modo).name()}; }}"
        )

        root_lay = QVBoxLayout(dialog)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        from shared.components import NMDialogScaffold

        scaffold = NMDialogScaffold(
            title="Exportar informe",
            eyebrow="Informe PDF",
            modo=self._modo,
            parent=dialog,
        )
        try:
            scaffold._close_btn.clicked.disconnect()
        except Exception:
            pass
        scaffold._close_btn.clicked.connect(dialog.reject)
        root_lay.addWidget(scaffold)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["md"])

        # ── Card de secciones ─────────────────────────────────────────────
        sections_card = NMCard(modo=self._modo)
        sec_lay = QVBoxLayout(sections_card)
        sec_lay.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        sec_lay.setSpacing(2)

        sec_header = QLabel("Secciones a incluir")
        sec_header.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        sec_header.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        sec_lay.addWidget(sec_header)
        sec_lay.addSpacing(V3_SP["xs"])

        checks: dict[str, QCheckBox] = {}
        for key, label in self._PDF_SECCIONES:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setFont(qfont("size_small"))
            checks[key] = cb
            sec_lay.addWidget(cb)

        lay.addWidget(sections_card)

        # ── Rango de fechas ───────────────────────────────────────────────
        fechas = self._fechas_disponibles()
        min_date = self._qdate_from_iso(fechas[0]) if fechas else QDate.currentDate()
        max_date = self._qdate_from_iso(fechas[-1]) if fechas else QDate.currentDate()

        date_card = NMCard(modo=self._modo)
        date_lay = QVBoxLayout(date_card)
        date_lay.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        date_lay.setSpacing(V3_SP["sm"])

        date_header = QLabel("Rango de fechas")
        date_header.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        date_header.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        date_lay.addWidget(date_header)

        date_row = QHBoxLayout()
        date_row.setSpacing(V3_SP["sm"])

        desde_col = QVBoxLayout()
        desde_col.setSpacing(4)
        desde_lbl = QLabel("Desde")
        desde_lbl.setFont(qfont("size_caption"))
        desde_lbl.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        desde_col.addWidget(desde_lbl)
        desde = QDateEdit()
        desde.setCalendarPopup(True)
        desde.setDisplayFormat("yyyy-MM-dd")
        desde.setDate(min_date)
        desde.setMinimumHeight(34)
        desde.setStyleSheet(stylesheet_dateedit(self._modo))
        desde_col.addWidget(desde)
        date_row.addLayout(desde_col)

        hasta_col = QVBoxLayout()
        hasta_col.setSpacing(4)
        hasta_lbl = QLabel("Hasta")
        hasta_lbl.setFont(qfont("size_caption"))
        hasta_lbl.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        hasta_col.addWidget(hasta_lbl)
        hasta = QDateEdit()
        hasta.setCalendarPopup(True)
        hasta.setDisplayFormat("yyyy-MM-dd")
        hasta.setDate(max_date)
        hasta.setMinimumHeight(34)
        hasta.setStyleSheet(stylesheet_dateedit(self._modo))
        hasta_col.addWidget(hasta)
        date_row.addLayout(hasta_col)

        date_lay.addLayout(date_row)
        lay.addWidget(date_card)

        # ── Nombre de archivo ────────────────────────────────────────────
        file_lbl = QLabel("Nombre de archivo")
        file_lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        file_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        lay.addWidget(file_lbl)

        nombre_seg = "".join(c for c in self._nombre if c.isalnum() or c in " _-")
        filename = NMInput(
            placeholder="Nombre del archivo",
            modo=self._modo,
            max_length=80,
        )
        filename.setText(
            f"NeuroMood_{nombre_seg}_{QDate.currentDate().toString('yyyyMMdd')}.pdf"
        )
        lay.addWidget(filename)

        scaffold.set_body(body)
        scaffold.add_action("Cancelar", role="ghost", callback=dialog.reject)
        btn_export = scaffold.add_action("Exportar", role="primary", callback=lambda: None)

        def _confirmar():
            secciones = [key for key, cb in checks.items() if cb.isChecked()]
            self._exportar_pdf_con_opciones(
                secciones=secciones,
                fecha_desde=desde.date().toString("yyyy-MM-dd"),
                fecha_hasta=hasta.date().toString("yyyy-MM-dd"),
                nombre_archivo=filename.text().strip(),
            )
            dialog.accept()

        btn_export.clicked.connect(_confirmar)
        dialog.exec()

    def _exportar_pdf_con_opciones(
        self, secciones: list[str], fecha_desde: str, fecha_hasta: str, nombre_archivo: str
    ):
        self._btn_pdf.setText("Generando…")
        self._btn_pdf.setEnabled(False)
        from hub.exportar import exportar_pdf

        exportar_pdf(
            self._nombre,
            self._pid,
            self._datos_cache,
            on_done=lambda ruta: run_on_gui(
                lambda r=ruta: self._pdf_ok(r) if not sip.isdeleted(self) else None
            ),
            on_error=lambda msg: run_on_gui(
                lambda m=msg: self._pdf_error(m) if not sip.isdeleted(self) else None
            ),
            secciones=secciones,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            nombre_archivo=nombre_archivo,
        )

    def _pdf_ok(self, ruta: str):
        self._btn_pdf.setText("Exportar PDF")
        self._btn_pdf.setEnabled(True)
        NMToast.display(self.window(), "PDF guardado en Downloads.", variant="success")

    def _pdf_error(self, msg: str):
        self._btn_pdf.setText("Exportar PDF")
        self._btn_pdf.setEnabled(True)
        NMToast.display(self.window(), f"Error PDF: {msg[:60]}", variant="error")


class _TabIA(QWidget):
    def __init__(self, modo: str, sb, pid: str, nombre: str, datos_cache_ref, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._datos_ref = datos_cache_ref
        self._ia_request_seq = 0
        self._ia_active_request: tuple[int, str] | None = None
        datos_cache_ref.changed.connect(self._on_datos_changed)
        self._setup()

    def _on_datos_changed(self, datos: dict):
        pass  # IA reads datos_ref.cache on demand

    def _setup(self):
        from shared.components import NMAIDisclaimer, NMBadge

        colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        layout.setSpacing(V3_SP["xs"])

        # Disclaimer clínico permanente (HANDOFF §6) — fuera del scroll, siempre
        # visible: la IA solo genera borradores que requieren validación.
        self._disclaimer = NMAIDisclaimer(modo=self._modo)
        layout.addWidget(self._disclaimer)

        # ── Resumen ───────────────────────────────────────────────────────────
        # Mínimo honesto: header 22 + textarea 80 + fila de botones 36 +
        # márgenes 24 + spacings 24 = 186. Con 176 la grilla comprimía bajo
        # mínimo y el botón "Generar resumen" quedaba pintado SOBRE el área
        # de texto (botones solapados en la captura del tab IA).
        card_res = NMCard(modo=self._modo, clickable=False)
        card_res.setMinimumHeight(168)
        vl_res = QVBoxLayout(card_res)
        vl_res.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_res.setSpacing(8)
        head_res = QHBoxLayout()
        head_res.setSpacing(8)
        lbl_res = QLabel("Resumen de evolución")
        lbl_res.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lbl_res.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        head_res.addWidget(lbl_res)
        head_res.addStretch()
        self._badge_resumen = NMBadge("Borrador", tone="patient", modo=self._modo)
        self._badge_resumen.setVisible(False)
        head_res.addWidget(self._badge_resumen)
        self._meta_resumen = self._mk_ia_meta()
        head_res.addWidget(self._meta_resumen)
        vl_res.addLayout(head_res)
        self._txt_resumen = NMTextArea(placeholder="El resumen aparecerá aquí…", modo=self._modo, min_height=64, font_key="size_small")
        self._txt_resumen.setReadOnly(True)
        vl_res.addWidget(self._txt_resumen)
        row_res = QHBoxLayout()
        self._btn_resumen = NMButton("Generar resumen", modo=self._modo, size="sm", width=160)
        self._btn_resumen.clicked.connect(self._generar_resumen)
        row_res.addWidget(self._btn_resumen)
        # Acciones canon del bloque IA (ADN tablero 06): Editar + Guardar como
        # nota. Aparecen recien con el borrador generado (sin acciones
        # prematuras — informe owner v1.0).
        self._btn_edit_res = NMButtonOutline("Editar", modo=self._modo, size="sm")
        self._btn_edit_res.clicked.connect(
            lambda: self._toggle_edit(self._txt_resumen, self._btn_edit_res)
        )
        self._btn_edit_res.setVisible(False)
        row_res.addWidget(self._btn_edit_res)
        self._btn_nota_res = NMButtonOutline("Guardar como nota", modo=self._modo, size="sm")
        self._btn_nota_res.clicked.connect(
            lambda: self._guardar_nota("Resumen de evolución", self._txt_resumen.toPlainText())
        )
        self._btn_nota_res.setVisible(False)
        row_res.addWidget(self._btn_nota_res)
        self._btn_copy_res = NMButtonOutline("Copiar", modo=self._modo, size="sm")
        self._btn_copy_res.setFixedWidth(80)
        self._btn_copy_res.clicked.connect(
            lambda: QApplication.clipboard().setText(self._txt_resumen.toPlainText())
        )
        self._btn_copy_res.setVisible(False)
        row_res.addWidget(self._btn_copy_res)
        row_res.addStretch()
        vl_res.addLayout(row_res)

        # NMTypingDots: visible during IA generation
        self._typing_dots = NMTypingDots(modo=self._modo, parent=card_res)
        self._typing_dots.hide()
        vl_res.addWidget(self._typing_dots, alignment=Qt.AlignmentFlag.AlignLeft)

        # ── Sugerencias ───────────────────────────────────────────────────────
        card_sug = NMCard(modo=self._modo, clickable=False)
        card_sug.setMinimumHeight(168)
        vl_sug = QVBoxLayout(card_sug)
        vl_sug.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_sug.setSpacing(8)
        head_sug = QHBoxLayout()
        head_sug.setSpacing(8)
        lbl_sug = QLabel("Sugerencias de acción")
        lbl_sug.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lbl_sug.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        head_sug.addWidget(lbl_sug)
        head_sug.addStretch()
        self._badge_sug = NMBadge("Borrador", tone="patient", modo=self._modo)
        self._badge_sug.setVisible(False)
        head_sug.addWidget(self._badge_sug)
        self._meta_sug = self._mk_ia_meta()
        head_sug.addWidget(self._meta_sug)
        vl_sug.addLayout(head_sug)
        # Bloque IA canon (tablero 06): el borrador vive en un area editable,
        # no en filas decorativas — mismo patron que Resumen y Tarea.
        self._txt_sug = NMTextArea(
            placeholder="Presioná 'Generar sugerencias' para obtener acciones concretas.",
            modo=self._modo,
            min_height=64,
            font_key="size_small",
        )
        self._txt_sug.setReadOnly(True)
        vl_sug.addWidget(self._txt_sug, stretch=1)
        row_sug = QHBoxLayout()
        self._btn_sugerencias = NMButton(
            "Generar sugerencias", modo=self._modo, size="sm", width=180
        )
        self._btn_sugerencias.clicked.connect(self._generar_sugerencias)
        row_sug.addWidget(self._btn_sugerencias)
        self._btn_edit_sug = NMButtonOutline("Editar", modo=self._modo, size="sm")
        self._btn_edit_sug.clicked.connect(
            lambda: self._toggle_edit(self._txt_sug, self._btn_edit_sug)
        )
        self._btn_edit_sug.setVisible(False)
        row_sug.addWidget(self._btn_edit_sug)
        self._btn_nota_sug = NMButtonOutline("Guardar como nota", modo=self._modo, size="sm")
        self._btn_nota_sug.clicked.connect(
            lambda: self._guardar_nota("Sugerencias de acción", self._txt_sug.toPlainText())
        )
        self._btn_nota_sug.setVisible(False)
        row_sug.addWidget(self._btn_nota_sug)
        row_sug.addStretch()
        vl_sug.addLayout(row_sug)

        # ── Generar tarea ─────────────────────────────────────────────────────
        card_tarea = NMCard(modo=self._modo, clickable=False)
        vl_t = QVBoxLayout(card_tarea)
        vl_t.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_t.setSpacing(8)
        head_t = QHBoxLayout()
        head_t.setSpacing(8)
        lbl_t = QLabel("Generar tarea personalizada")
        lbl_t.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lbl_t.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        head_t.addWidget(lbl_t)
        head_t.addStretch()
        self._badge_tarea = NMBadge("Borrador", tone="patient", modo=self._modo)
        self._badge_tarea.setVisible(False)
        head_t.addWidget(self._badge_tarea)
        self._meta_tarea = self._mk_ia_meta()
        head_t.addWidget(self._meta_tarea)
        vl_t.addLayout(head_t)
        self._ent_ctx = NMInput(
            "Ej: paciente con ansiedad leve, mejoró en respiración…",
            modo=self._modo,
            max_length=300,
        )
        vl_t.addWidget(self._ent_ctx)
        self._txt_tarea = NMTextArea(placeholder="", modo=self._modo, min_height=48, font_key="size_small")
        self._txt_tarea.setReadOnly(True)
        self._txt_tarea.setVisible(False)
        vl_t.addWidget(self._txt_tarea)
        row_t = QHBoxLayout()
        self._btn_tarea = NMButton("Generar", modo=self._modo, size="sm", width=100)
        self._btn_tarea.clicked.connect(self._generar_tarea)
        row_t.addWidget(self._btn_tarea)
        self._btn_edit_t = NMButtonOutline("Editar", modo=self._modo, size="sm")
        self._btn_edit_t.clicked.connect(
            lambda: self._toggle_edit(self._txt_tarea, self._btn_edit_t)
        )
        self._btn_edit_t.setVisible(False)
        row_t.addWidget(self._btn_edit_t)
        self._btn_nota_t = NMButtonOutline("Guardar como nota", modo=self._modo, size="sm")
        self._btn_nota_t.clicked.connect(
            lambda: self._guardar_nota("Tarea personalizada", self._txt_tarea.toPlainText())
        )
        self._btn_nota_t.setVisible(False)
        row_t.addWidget(self._btn_nota_t)
        self._btn_copy_t = NMButtonOutline("Copiar", modo=self._modo, size="sm")
        self._btn_copy_t.setFixedWidth(80)
        self._btn_copy_t.clicked.connect(
            lambda: QApplication.clipboard().setText(self._txt_tarea.toPlainText())
        )
        self._btn_copy_t.setVisible(False)
        row_t.addWidget(self._btn_copy_t)
        row_t.addStretch()
        vl_t.addLayout(row_t)

        # ── Asignación sugerida (reorganización owner v1.0) ──────────────────
        # La IA genera UN borrador de asignación por módulo (Recordatorios /
        # Temporizador / Rutina / Activación). NUNCA asigna sola: la escritura
        # ocurre recién con "Aprobar y asignar" del profesional.
        card_asig = NMCard(modo=self._modo, clickable=False)
        vl_asig = QVBoxLayout(card_asig)
        vl_asig.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_asig.setSpacing(8)
        head_a = QHBoxLayout()
        head_a.setSpacing(8)
        lbl_a = QLabel("Asignación sugerida")
        lbl_a.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        lbl_a.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        head_a.addWidget(lbl_a)
        head_a.addStretch()
        self._badge_asig = NMBadge("Borrador", tone="patient", modo=self._modo)
        self._badge_asig.setVisible(False)
        head_a.addWidget(self._badge_asig)
        self._meta_asig = self._mk_ia_meta()
        head_a.addWidget(self._meta_asig)
        vl_asig.addLayout(head_a)

        row_mod = QHBoxLayout()
        row_mod.setSpacing(8)
        self._combo_asig = QComboBox()
        self._combo_asig.setStyleSheet(stylesheet_combobox(self._modo))
        self._combo_asig.wheelEvent = lambda event: event.ignore()
        for label, key in (
            ("Recordatorios de Bienestar", "avisos"),
            ("Temporizador de Actividades", "timer"),
            ("Checklist de Rutina Diaria", "rutina"),
            ("Asistente de Activación Conductual", "actividades"),
        ):
            self._combo_asig.addItem(label, key)
        row_mod.addWidget(self._combo_asig, stretch=1)
        row_mod.addSpacing(12)
        self._btn_asig_gen = NMButton(
            "Generar borrador", modo=self._modo, size="sm", width=150
        )
        self._btn_asig_gen.clicked.connect(self._generar_asignacion)
        row_mod.addWidget(self._btn_asig_gen)
        vl_asig.addLayout(row_mod)

        self._txt_asig = NMTextArea(
            placeholder="Elegí un módulo y generá un borrador. Lo revisás, lo editás "
            "si hace falta, y recién al aprobarlo se asigna al paciente.",
            modo=self._modo,
            min_height=54,
            font_key="size_small",
        )
        self._txt_asig.setReadOnly(True)
        vl_asig.addWidget(self._txt_asig)

        row_aa = QHBoxLayout()
        self._btn_asig_edit = NMButtonOutline("Editar", modo=self._modo, size="sm")
        self._btn_asig_edit.clicked.connect(
            lambda: self._toggle_edit(self._txt_asig, self._btn_asig_edit)
        )
        self._btn_asig_edit.setVisible(False)
        row_aa.addWidget(self._btn_asig_edit)
        self._btn_asig_ok = NMButton(
            "Aprobar y asignar", modo=self._modo, size="sm", width=160
        )
        self._btn_asig_ok.clicked.connect(self._aprobar_asignacion)
        self._btn_asig_ok.setVisible(False)
        row_aa.addWidget(self._btn_asig_ok)
        self._btn_asig_no = NMButtonOutline("Descartar", modo=self._modo, size="sm")
        self._btn_asig_no.clicked.connect(self._descartar_asignacion)
        self._btn_asig_no.setVisible(False)
        row_aa.addWidget(self._btn_asig_no)
        row_aa.addStretch()
        vl_asig.addLayout(row_aa)

        # Una sola columna: con las acciones canon del bloque IA (Editar +
        # Guardar como nota + Copiar) dos columnas no entran a 960 sin cortar
        # la card derecha. El overflow vertical lo absorbe el scroll calmo.
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(V3_SP["sm"])
        grid.setVerticalSpacing(V3_SP["sm"])
        grid.addWidget(card_res, 0, 0)
        grid.addWidget(card_sug, 1, 0)
        grid.addWidget(card_asig, 2, 0)
        grid.addWidget(card_tarea, 3, 0)
        grid.setColumnStretch(0, 1)
        # Red anti-solape: si la ventana no llega al presupuesto vertical de
        # las 3 cards, scroll calmo en vez de compresión bajo mínimo (Qt
        # superpone físicamente los widgets en ese caso). El disclaimer queda
        # FUERA del scroll: siempre visible.
        _ia_content = QWidget()
        _ia_content.setStyleSheet("background: transparent;")
        _ia_cl = QVBoxLayout(_ia_content)
        _ia_cl.setContentsMargins(0, 0, 0, 0)
        _ia_cl.addLayout(grid)
        _ia_scroll = QScrollArea()
        _ia_scroll.setWidgetResizable(True)
        _ia_scroll.setFrameShape(QFrame.Shape.NoFrame)
        _ia_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        _ia_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        _ia_scroll.setWidget(_ia_content)
        self._ia_scroll = _ia_scroll  # referencia para QA (scroll a la card de asignación)
        layout.addWidget(_ia_scroll, stretch=1)

        from shared.visual_qa import visual_qa_enabled

        if visual_qa_enabled():
            self._qa_seed_draft()

    def _mk_ia_meta(self) -> QLabel:
        """Meta de bloque IA — VACÍA (Fase 6: reducir ruido borrador/generado/
        editable). El aviso de borrador vive una sola vez en el banner superior y
        cada bloque ya conserva su chip 'Borrador' + botón 'Editar'; el mono
        'generado · editable' repetido ×4 era redundante. Se mantiene el QLabel
        (vacío, 0px) para no tocar los ~9 call sites que togglean su visibilidad."""
        lbl = QLabel("")
        lbl.setFont(qfont_mono(TYPOGRAPHY["size_caption"]))
        lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        lbl.setVisible(False)
        return lbl

    def _toggle_edit(self, textarea, btn):
        """Editar <-> Listo: el borrador IA siempre es editable a demanda."""
        if textarea.isReadOnly():
            textarea.setReadOnly(False)
            textarea.setFocus()
            btn.setText("Listo")
        else:
            textarea.setReadOnly(True)
            btn.setText("Editar")

    def _guardar_nota(self, titulo: str, txt: str):
        """'Guardar como nota' canon: SIN persistencia clinica canonica para
        borradores IA, queda como estado local de UI (decision del plan ADN —
        no se inventa escritura clinica)."""
        txt = (txt or "").strip()
        if not txt:
            return
        if not hasattr(self, "_notas_locales"):
            self._notas_locales = []
        self._notas_locales.append((titulo, txt))
        NMToast.display(
            self.window(),
            "Borrador guardado como nota local de esta sesión.",
            variant="success",
        )

    def _qa_seed_draft(self):
        """Puebla borradores demo (solo NM_VISUAL_QA) para QA del estado
        'borrador' con disclaimer + badge, fiel a capture 05. No llama a la IA."""
        self._resumen_ok(
            "La paciente muestra una mejora sostenida del ánimo en las últimas "
            "tres semanas (+1.8). La adherencia a respiración es alta; el registro "
            "TCC sugiere disparadores en contextos laborales. Posible foco de "
            "sesión: reestructuración ante evaluación social."
        )
        self._sugerencias_ok(
            "Reforzar práctica de respiración 4-7-8 antes de reuniones.\n"
            "Asignar registro TCC ante eventos sociales.\n"
            "Revisar patrón de sueño en la próxima sesión."
        )
        self._asig_ok("hora: 21:30\nmensaje: Pausa breve de respiración antes de dormir.")
        self._tarea_ok("Caminata consciente de 20 min, 3×/semana, con registro de ánimo posterior.")

    def _set_inputs_enabled(self, enabled: bool):
        self._btn_resumen.setEnabled(enabled)
        self._btn_sugerencias.setEnabled(enabled)
        if hasattr(self, "_btn_tarea"):
            self._btn_tarea.setEnabled(enabled)
        if hasattr(self, "_btn_asig_gen"):
            self._btn_asig_gen.setEnabled(enabled)
            self._combo_asig.setEnabled(enabled)
        self._ent_ctx.setEnabled(enabled)

    def _begin_ai_request(self, kind: str) -> int:
        self._ia_request_seq += 1
        rid = self._ia_request_seq
        self._ia_active_request = (rid, kind)
        QTimer.singleShot(90000, lambda r=rid, k=kind: self._ai_request_timeout(r, k))
        return rid

    def _accept_ai_request(self, rid: int, kind: str) -> bool:
        if self._ia_active_request != (rid, kind):
            return False
        self._ia_active_request = None
        return True

    def _ai_request_timeout(self, rid: int, kind: str):
        if sip.isdeleted(self) or self._ia_active_request != (rid, kind):
            return
        self._ia_active_request = None
        msg = "IA no disponible momentaneamente"
        if kind == "resumen":
            self._resumen_err(msg)
        elif kind == "sugerencias":
            self._sugerencias_err(msg)
        elif kind == "asignacion":
            self._asig_err(msg)
        else:
            self._tarea_err(msg)

    def _generar_resumen(self):
        datos = self._datos_ref.cache
        if not datos or not any(datos.get(k) for k in ("animo", "resp", "pens", "checklist")):
            NMToast.display(
                self.window(),
                "Cargá los datos del paciente primero (Tab Registros).",
                variant="info",
            )
            return
        self._set_inputs_enabled(False)
        self._btn_resumen.setText("Generando…")
        self._badge_resumen.setVisible(False)
        self._btn_copy_res.setVisible(False)
        self._txt_resumen.setPlainText("")
        if hasattr(self, "_typing_dots"):
            self._typing_dots.show()
            self._typing_dots.start()
        from hub.ia_asistente import resumir_evolucion

        rid = self._begin_ai_request("resumen")
        resumir_evolucion(
            datos,
            self._nombre,
            on_result=lambda txt: run_on_gui(
                lambda t=txt, r=rid: (
                    self._resumen_ok(t)
                    if not sip.isdeleted(self) and self._accept_ai_request(r, "resumen")
                    else None
                ),
            ),
            on_error=lambda msg: run_on_gui(
                lambda m=msg, r=rid: (
                    self._resumen_err(m)
                    if not sip.isdeleted(self) and self._accept_ai_request(r, "resumen")
                    else None
                ),
            ),
            patient_id=self._pid,
        )

    def _resumen_ok(self, txt: str):
        self._set_inputs_enabled(True)
        self._btn_resumen.setText("Generar resumen")
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        # Aire entre las 3 secciones rotuladas del prompt (estructura clinica
        # legible, no bloque denso).
        txt = (txt or "").strip()
        for _sec in ("Señales a observar:", "Posible foco:"):
            txt = txt.replace("\n" + _sec, "\n\n" + _sec)
        self._txt_resumen.setPlainText(txt)
        has = bool(txt.strip())
        self._badge_resumen.setVisible(has)
        self._meta_resumen.setVisible(has)
        self._btn_edit_res.setVisible(has)
        self._btn_nota_res.setVisible(has)
        self._btn_copy_res.setVisible(has)

    def _resumen_err(self, msg: str):
        self._set_inputs_enabled(True)
        self._btn_resumen.setText("Generar resumen")
        self._badge_resumen.setVisible(False)
        self._meta_resumen.setVisible(False)
        self._btn_edit_res.setVisible(False)
        self._btn_nota_res.setVisible(False)
        self._btn_copy_res.setVisible(False)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        self._txt_resumen.setPlainText(msg)

    def _generar_sugerencias(self):
        datos = self._datos_ref.cache
        if not datos:
            NMToast.display(self.window(), "Cargá los datos del paciente primero.", variant="info")
            return
        self._set_inputs_enabled(False)
        self._btn_sugerencias.setText("Generando…")
        self._badge_sug.setVisible(False)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.show()
            self._typing_dots.start()
        from hub.ia_asistente import sugerir_acciones

        rid = self._begin_ai_request("sugerencias")
        sugerir_acciones(
            datos,
            self._nombre,
            on_result=lambda txt: run_on_gui(
                lambda t=txt, r=rid: (
                    self._sugerencias_ok(t)
                    if not sip.isdeleted(self)
                    and self._accept_ai_request(r, "sugerencias")
                    else None
                ),
            ),
            on_error=lambda msg: run_on_gui(
                lambda m=msg, r=rid: (
                    self._sugerencias_err(m)
                    if not sip.isdeleted(self)
                    and self._accept_ai_request(r, "sugerencias")
                    else None
                ),
            ),
            patient_id=self._pid,
        )

    def _sugerencias_ok(self, txt: str):
        self._set_inputs_enabled(True)
        self._btn_sugerencias.setText("Generar sugerencias")
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        lineas = [ln.strip() for ln in (txt or "").splitlines() if ln.strip()]
        self._txt_sug.setPlainText("\n".join(lineas))
        has = bool(lineas)
        self._badge_sug.setVisible(has)
        self._meta_sug.setVisible(has)
        self._btn_edit_sug.setVisible(has)
        self._btn_nota_sug.setVisible(has)

    def _sugerencias_err(self, msg: str):
        self._set_inputs_enabled(True)
        self._btn_sugerencias.setText("Generar sugerencias")
        self._badge_sug.setVisible(False)
        self._meta_sug.setVisible(False)
        self._btn_edit_sug.setVisible(False)
        self._btn_nota_sug.setVisible(False)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        NMToast.display(self.window(), msg, variant="error")

    def _generar_tarea(self):
        ctx = self._ent_ctx.text().strip()
        if not ctx:
            return
        self._set_inputs_enabled(False)
        self._txt_tarea.setVisible(True)
        self._txt_tarea.setPlainText("Generando…")
        self._badge_tarea.setVisible(False)
        self._meta_tarea.setVisible(False)
        self._btn_edit_t.setVisible(False)
        self._btn_nota_t.setVisible(False)
        self._btn_copy_t.setVisible(False)
        from hub.ia_asistente import generar_tarea

        rid = self._begin_ai_request("tarea")
        generar_tarea(
            ctx,
            on_result=lambda txt: run_on_gui(
                lambda t=txt, r=rid: (
                    self._tarea_ok(t)
                    if not sip.isdeleted(self) and self._accept_ai_request(r, "tarea")
                    else None
                ),
            ),
            on_error=lambda msg: run_on_gui(
                lambda m=msg, r=rid: (
                    self._tarea_err(m)
                    if not sip.isdeleted(self) and self._accept_ai_request(r, "tarea")
                    else None
                ),
            ),
            patient_id=self._pid,
        )

    def _tarea_ok(self, txt: str):
        self._set_inputs_enabled(True)
        has = bool((txt or "").strip())
        self._txt_tarea.setVisible(True)
        self._txt_tarea.setPlainText(txt)
        self._badge_tarea.setVisible(has)
        self._meta_tarea.setVisible(has)
        self._btn_edit_t.setVisible(has)
        self._btn_nota_t.setVisible(has)
        self._btn_copy_t.setVisible(has)

    def _tarea_err(self, msg: str):
        self._set_inputs_enabled(True)
        self._txt_tarea.setVisible(True)
        self._txt_tarea.setPlainText(msg)
        self._badge_tarea.setVisible(False)
        self._meta_tarea.setVisible(False)
        self._btn_edit_t.setVisible(False)
        self._btn_nota_t.setVisible(False)
        self._btn_copy_t.setVisible(False)

    # ── Asignación sugerida (IA genera; el profesional aprueba) ──────────────

    def _generar_asignacion(self):
        datos = self._datos_ref.cache
        if not datos or not any(datos.get(k) for k in ("animo", "resp", "pens", "checklist")):
            NMToast.display(
                self.window(),
                "Cargá los datos del paciente primero (Tab Registros).",
                variant="info",
            )
            return
        modulo = self._combo_asig.currentData()
        self._set_inputs_enabled(False)
        self._btn_asig_gen.setText("Generando…")
        self._set_asig_draft_visible(False)
        self._txt_asig.setReadOnly(True)
        self._btn_asig_edit.setText("Editar")
        self._txt_asig.setPlainText("")
        from hub.ia_asistente import generar_asignacion

        rid = self._begin_ai_request("asignacion")
        generar_asignacion(
            modulo,
            datos,
            self._nombre,
            on_result=lambda txt: run_on_gui(
                lambda t=txt, r=rid: (
                    self._asig_ok(t)
                    if not sip.isdeleted(self) and self._accept_ai_request(r, "asignacion")
                    else None
                ),
            ),
            on_error=lambda msg: run_on_gui(
                lambda m=msg, r=rid: (
                    self._asig_err(m)
                    if not sip.isdeleted(self) and self._accept_ai_request(r, "asignacion")
                    else None
                ),
            ),
            patient_id=self._pid,
        )

    def _set_asig_draft_visible(self, visible: bool):
        self._badge_asig.setVisible(visible)
        self._meta_asig.setVisible(visible)
        self._btn_asig_edit.setVisible(visible)
        self._btn_asig_ok.setVisible(visible)
        self._btn_asig_no.setVisible(visible)

    def _asig_ok(self, txt: str):
        self._set_inputs_enabled(True)
        self._btn_asig_gen.setText("Generar borrador")
        lineas = [ln.strip().lstrip("•-* ") for ln in (txt or "").splitlines() if ln.strip()]
        self._txt_asig.setPlainText("\n".join(lineas))
        self._set_asig_draft_visible(bool(lineas))

    def _asig_err(self, msg: str):
        self._set_inputs_enabled(True)
        self._btn_asig_gen.setText("Generar borrador")
        self._txt_asig.setPlainText(msg)
        self._set_asig_draft_visible(False)

    def _descartar_asignacion(self):
        self._txt_asig.setReadOnly(True)
        self._btn_asig_edit.setText("Editar")
        self._txt_asig.setPlainText("")
        self._set_asig_draft_visible(False)

    @staticmethod
    def _parse_asignacion(texto: str) -> dict:
        """Parsea las líneas 'clave: valor' del borrador (tolerante)."""
        campos: dict[str, str] = {}
        for ln in (texto or "").splitlines():
            if ":" not in ln:
                continue
            k, v = ln.split(":", 1)
            campos[k.strip().lower()] = v.strip().strip("\"'")
        return campos

    def _aprobar_asignacion(self):
        if not self._sb:
            NMToast.display(self.window(), "Sin conexión — no se puede asignar.", variant="error")
            return
        modulo = self._combo_asig.currentData()
        campos = self._parse_asignacion(self._txt_asig.toPlainText())
        try:
            if modulo == "avisos":
                hora = campos.get("hora", "")
                mensaje = campos.get("mensaje", "")[:150]
                if not re.match(r"^\d{2}:\d{2}$", hora) or not mensaje:
                    raise ValueError("El borrador necesita 'hora: HH:MM' y 'mensaje: …'.")
                self._sb.table("assigned_reminders").insert({
                    "patient_id": self._pid,
                    "hora": hora,
                    "mensaje": mensaje,
                    "dias": "1,2,3,4,5,6,7",
                    "activa": True,
                }).execute()
            elif modulo == "timer":
                nombre = campos.get("nombre", "")[:24]
                cat = (campos.get("categoria", "") or "Timer")[:20]
                mins = int(campos.get("minutos", "0") or 0)
                if not nombre or not (1 <= mins <= 180):
                    raise ValueError("El borrador necesita 'nombre' y 'minutos' entre 1 y 180.")
                self._sb.table("timer_presets_remote").insert({
                    "scope": f"patient:{self._pid}",
                    "name": nombre,
                    "duracion_seg": mins * 60,
                    "categoria": cat,
                    "activo": True,
                }).execute()
            elif modulo == "rutina":
                tarea = campos.get("tarea", "")[:100]
                sec = campos.get("seccion", "manana").lower()
                sec = {"mañana": "manana"}.get(sec, sec)
                if sec not in ("manana", "tarde", "noche"):
                    sec = "manana"
                if not tarea:
                    raise ValueError("El borrador necesita 'tarea: …'.")
                self._sb.table("assigned_tasks").insert({
                    "patient_id": self._pid,
                    "descripcion": tarea,
                    "seccion": sec,
                    "activa": True,
                }).execute()
            elif modulo == "actividades":
                nombre = campos.get("nombre", "")[:50]
                desc = campos.get("descripcion", "")[:120]
                cat = campos.get("categoria", "Autocuidado").capitalize()
                if cat not in ("Autocuidado", "Social", "Físico", "Productivo"):
                    cat = "Autocuidado"
                if not nombre:
                    raise ValueError("El borrador necesita 'nombre: …'.")
                self._sb.table("patient_activities").insert({
                    "patient_id": self._pid,
                    "nombre": nombre,
                    "descripcion": desc,
                    "categoria": cat,
                    "animo_min": 1,
                    "animo_max": 10,
                    "activa": True,
                }).execute()
            else:
                raise ValueError(f"Módulo no asignable: {modulo}")
        except ValueError as e:
            NMToast.display(self.window(), str(e), variant="error")
            return
        except Exception as e:
            NMToast.display(self.window(), f"Error al asignar: {str(e)[:50]}", variant="error")
            return
        NMToast.display(
            self.window(),
            f"Asignado a {self._combo_asig.currentText()} ✓",
            variant="success",
        )
        self._descartar_asignacion()


# ── Shared state between TabRegistros and TabIA ────────────────────────────────


class _DatosRef(QObject):
    """Objeto de estado compartido limpio entre Registros e IA."""

    changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.cache: dict = {}


# ── DetallePacienteView ───────────────────────────────────────────────────────


class DetallePacienteView(QWidget):
    """Panel completo de detalle de paciente con shell premium y tabs clínicas."""

    back_requested = pyqtSignal()
    _legal_loaded_signal = pyqtSignal(object, object)

    def __init__(self, modo: str, sb, paciente_id: str, paciente_nombre: str, parent=None):
        super().__init__(parent)
        self._legal_loaded_signal.connect(self._on_legal_loaded)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = paciente_id
        self._nombre = paciente_nombre
        self._datos_ref = _DatosRef()
        self.setObjectName("DetallePacienteView")
        self.setAccessibleName(f"DetallePacienteView patient_id={self._pid}")
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _setup(self):
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # (Se eliminó la NMProgressLine de 2px del tope: al seleccionar un
        # paciente se leía como una línea que separaba la titlebar de la ventana
        # principal — pedido owner.)

        # Patient hero shell — alto reducido: el header lo paga TODA tab y el
        # contenido se recortaba abajo (H12/H21). Menos padding/avatar libera
        # ~18px de viewport para resumen/registros/ia/plan sin perder jerarquía.
        top = NMCard(modo=self._modo, clickable=False, glow=False)
        top.setMinimumHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(18, 10, 18, 10)
        tl.setSpacing(14)

        self._btn_back = NMButton("Volver", variant="ghost", size="sm", modo=self._modo, width=92)
        self._btn_back.setFixedHeight(32)
        self._btn_back.clicked.connect(self.back_requested.emit)
        tl.addWidget(self._btn_back, alignment=Qt.AlignmentFlag.AlignTop)

        initials = "".join(w[0] for w in (self._nombre or "?").split()[:2]).upper()
        self._avatar = NMAvatar(
            initials=initials or "P", size=40, color_seed=self._pid or self._nombre, modo=self._modo
        )
        tl.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self._lbl_eyebrow = QLabel("Paciente")
        self._lbl_eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        text_col.addWidget(self._lbl_eyebrow)

        # NMElidedLabel: a 960px el hero no tiene ancho para nombre + subtítulo
        # + 3 chips; los labels ceden con "…" en vez de empujar los chips a
        # geometrías bajo-mínimo (Qt los superpone físicamente en ese caso).
        self._lbl_name = NMElidedLabel(self._nombre)
        self._lbl_name.setFont(v3_font("size_h2", weight=600, serif=True))
        text_col.addWidget(self._lbl_name)

        # Texto corto: "del paciente" era redundante (eyebrow PACIENTE + nombre
        # arriba) y a 960px forzaba elisión permanente.
        self._lbl_meta = NMElidedLabel("Seguimiento profesional")
        self._lbl_meta.setAccessibleName(f"Seguimiento profesional del paciente ID {self._pid}")
        self._lbl_meta.setFont(qfont("size_caption"))
        self._lbl_meta.setWordWrap(False)
        text_col.addWidget(self._lbl_meta)

        tl.addLayout(text_col, stretch=1)

        chips_col = QVBoxLayout()
        chips_col.setContentsMargins(0, 0, 0, 0)
        chips_col.setSpacing(6)

        self._chip_row = QHBoxLayout()
        self._chip_row.setContentsMargins(0, 0, 0, 0)
        self._chip_row.setSpacing(10)
        # Si el hero se queda sin ancho, los chips NO deben comprimirse unos
        # contra otros: el stretch inicial absorbe y los empuja a la derecha.
        self._chip_row.addStretch()
        # 5.1: lenguaje neutral — "Riesgo bajo" afirma una verdad clínica que el
        # demo no valida. "Sin alerta activa" describe el estado de la app
        # (no se generaron alertas), no diagnostica al paciente. "5d racha"
        # se mantiene como señal operativa (cuántos días lleva registrando),
        # no como juicio clínico.
        self._chip_semana = NMBadge("Semana 12", tone="patient", modo=self._modo)
        self._chip_riesgo = NMBadge("Sin alerta activa", tone="neutral", modo=self._modo)
        # "racha" no se usa en Argentina (feedback owner) → "progreso".
        self._chip_racha = NMBadge("Progreso 5d", tone="completed", modo=self._modo)
        self._chip_row.addWidget(self._chip_semana)
        self._chip_row.addWidget(self._chip_riesgo)
        self._chip_row.addWidget(self._chip_racha)
        chips_col.addLayout(self._chip_row)
        # ("Vista activa en NeuroMood Hub" eliminado: redundante y ocupaba
        # espacio — informe owner v1.0, detalle de paciente.)

        tl.addLayout(chips_col)
        top_wrap = QWidget()
        top_wrap.setStyleSheet("background: transparent;")
        top_lay = QVBoxLayout(top_wrap)
        top_lay.setContentsMargins(12, 4, 12, 2)
        top_lay.setSpacing(0)
        top_lay.addWidget(top)
        layout.addWidget(top_wrap)

        # Tab shell
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(stylesheet_tabwidget_underline(self._modo))
        self._tabs.setDocumentMode(True)
        self._tabs.setUsesScrollButtons(False)
        self._tabs.tabBar().setElideMode(Qt.TextElideMode.ElideNone)

        # Instanciar tabs. Arquitectura canónica (informe owner v1.0 frente 7):
        # lo por-paciente vive acá — "Plan terapéutico" consolida temporizador/
        # recordatorios/rutina/activación/TCC/textos (antes vista global
        # "Presets" + vista global "Textos"). El catálogo global de actividades
        # (ex tab "Banco") se mudó a Personalización global.
        from hub.plan_terapeutico import PlanTerapeuticoTab

        self._tab_resumen = _TabResumen(
            self._modo, self._sb, self._pid, self._nombre, self._datos_ref
        )
        self._tab_reg = _TabRegistros(self._modo, self._sb, self._pid, self._nombre)
        self._tab_plan = PlanTerapeuticoTab(self._modo, self._sb, self._pid, self._nombre)
        self._tab_ia = _TabIA(self._modo, self._sb, self._pid, self._nombre, self._datos_ref)

        # Compartir datos_cache entre Registros e IA via _DatosRef
        self._tab_reg._datos_ref = self._datos_ref

        self._tabs.addTab(self._tab_resumen, "Resumen")
        self._tabs.addTab(self._tab_reg, "Registros")
        self._tabs.addTab(self._tab_plan, "Plan terapéutico")
        self._tabs.addTab(self._tab_ia, "IA")

        tabs_wrap = QWidget()
        tabs_wrap.setStyleSheet("background: transparent;")
        tabs_lay = QVBoxLayout(tabs_wrap)
        tabs_lay.setContentsMargins(12, 0, 12, 4)
        tabs_lay.setSpacing(0)
        tabs_lay.addWidget(self._tabs)
        layout.addWidget(tabs_wrap, stretch=1)

        self._load_legal_consent()

    def _load_legal_consent(self):
        from shared.visual_qa import visual_qa_enabled

        if visual_qa_enabled():
            mock_consent = {
                "status": "vigente",
                "accepted_at_utc": "2026-05-20T12:00:00Z",
                "disclaimer_version": "v1.0",
                "privacy_version": "v1.0",
                "neuromood_suite_version": "1.0.0",
                "disclaimer_text_hash": "abc123xyz789",
                "privacy_text_hash": "xyz789abc123",
                "consent_scope": "professional",
                "product_name": "NeuroMood Suite",
                "instalador_suite_version": "1.0.0",
            }
            self._set_legal_consent(mock_consent, "vigente")
            # Auto-load mock patient records in QA mode for immediate summary tab updates
            self._tab_reg._cargar_datos()
            return

        if not self._sb:
            self._set_legal_consent(None, "pendiente")
            return

        def _fetch():
            try:
                res = (
                    self._sb.table("legal_consents")
                    .select(
                        "status,accepted_at_utc,disclaimer_version,privacy_version,neuromood_suite_version,disclaimer_text_hash,privacy_text_hash,consent_scope,product_name,instalador_suite_version"
                    )
                    .eq("patient_id", self._pid)
                    .order("accepted_at_utc", desc=True)
                    .limit(1)
                    .execute()
                )
                data = getattr(res, "data", None) or []
                consent = data[0] if data else None
                self._legal_loaded_signal.emit(consent, None)
            except Exception:
                self._legal_loaded_signal.emit(None, "pendiente")

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_legal_loaded(self, consent: object, fallback_status: object):
        if sip.isdeleted(self):
            return
        self._set_legal_consent(
            consent if isinstance(consent, dict) else None,
            fallback_status if isinstance(fallback_status, str) else None,
        )

    def _set_legal_consent(self, consent: dict | None, fallback_status: str | None):
        self._legal_consent = consent
        c = colors(self._modo)
        status = (consent or {}).get("status") or fallback_status or "pendiente"
        accepted = (consent or {}).get("accepted_at_utc") or "Sin constancia remota"
        disc = (consent or {}).get("disclaimer_version") or "—"
        priv = (consent or {}).get("privacy_version") or "—"
        suite_v = (consent or {}).get("neuromood_suite_version") or "—"
        h = (consent or {}).get("disclaimer_text_hash") or "—"

        lbl = self._tab_resumen.lbl_legal

        # Gating granular de consentimiento: no deshabilitamos el QTabWidget completo.
        # Mantener siempre accesible la pestaña "Resumen" (index 0) para que el profesional
        # entienda el estado legal, deshabilitando solo pestañas clínicas.
        if status == "vigente":
            color = c["success"]
            prefix = "Consentimiento vigente"
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(True)
                for i in range(self._tabs.count()):
                    self._tabs.setTabEnabled(i, True)
        elif status == "desactualizado":
            color = c["warning"]
            prefix = "Requiere nueva aceptación"
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(True)
                self._tabs.setTabEnabled(0, True)  # Resumen accesible
                for i in range(1, self._tabs.count()):
                    self._tabs.setTabEnabled(i, False)  # Clínicas deshabilitadas
                if self._tabs.currentIndex() > 0:
                    self._tabs.setCurrentIndex(0)
        elif status == "revocado":
            color = c["error"]
            prefix = "Consentimiento revocado"
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(True)
                self._tabs.setTabEnabled(0, True)  # Resumen accesible
                for i in range(1, self._tabs.count()):
                    self._tabs.setTabEnabled(i, False)  # Clínicas deshabilitadas
                if self._tabs.currentIndex() > 0:
                    self._tabs.setCurrentIndex(0)
        else:
            color = c["error"]
            prefix = "Consentimiento pendiente"
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(True)
                self._tabs.setTabEnabled(0, True)  # Resumen accesible
                for i in range(1, self._tabs.count()):
                    self._tabs.setTabEnabled(i, False)  # Clínicas deshabilitadas
                if self._tabs.currentIndex() > 0:
                    self._tabs.setCurrentIndex(0)

        hash_short = h[:16] if h != "—" else h
        # 5.1: constancia legal en líneas etiquetadas — antes era una línea con
        # pipes que se cortaba en 960×600. Compacta (4 líneas): a 600px de alto
        # la card del Resumen no tiene lugar para más sin recortar el texto.
        accepted_view = accepted
        if "T" in accepted:
            # ISO → lectura humana corta; la constancia PDF conserva el valor
            # completo con segundos y zona.
            # Solo fecha y hora local-legible, sin sufijo técnico "UTC" (la
            # constancia PDF conserva el timestamp ISO completo con zona).
            accepted_view = accepted.replace("T", " ")[:16]
        lbl.setText(
            f"{prefix}\n"
            f"Aceptado: {accepted_view}\n"
            f"Aviso {disc} · Privacidad {priv} · Suite {suite_v}"
        )
        # El hash y el timestamp ISO completos viven en la constancia PDF
        # ("Ver constancia"); en la card no entran sin recortarse a 960×600.
        lbl.setToolTip(f"Aceptado (ISO): {accepted}\nHash: {hash_short}")
        lbl.setStyleSheet(f"color: {color}; background: transparent;")



    @staticmethod
    def _parse_fecha(s) -> datetime | None:
        if not s:
            return None
        try:
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _dias_desde(s) -> str:
        dt = DetallePacienteView._parse_fecha(s)
        if dt is None:
            return "—"
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        d = (now - dt).days
        if d == 0:
            return "hoy"
        if d == 1:
            return "1 día"
        return f"{d} días"

    @staticmethod
    def _semanas_desde(s) -> int:
        dt = DetallePacienteView._parse_fecha(s)
        if dt is None:
            return 0
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(1, (now - dt).days // 7)

    def _update_featured(self, datos: dict):
        """Update NMFeaturedCard when patient data loads."""
        if not hasattr(self, "_featured_card") or sip.isdeleted(self._featured_card):
            return
        animo = datos.get("animo", [])
        con_puntaje = [r for r in animo if r.get("puntaje") is not None]
        if not con_puntaje:
            return

        # Ordenar por fecha desc
        def _fecha_key(r):
            return r.get("fecha") or r.get("creado_en") or ""

        ordenados = sorted(con_puntaje, key=_fecha_key, reverse=True)

        recientes = [r["puntaje"] for r in ordenados[:7]]
        previos = [r["puntaje"] for r in ordenados[7:14]]
        prom = sum(recientes) / len(recientes)

        emoji = "😞" if prom < 4 else "😐" if prom < 7 else "😊"
        self._featured_card.set_score(round(prom, 1), emoji)

        # Delta vs semana anterior
        if previos:
            prom_prev = sum(previos) / len(previos)
            self._featured_card.set_delta(round(prom - prom_prev, 1))
        else:
            self._featured_card.set_delta(None)

        # Meta line
        fecha_primera = _fecha_key(ordenados[-1])
        fecha_ultima = _fecha_key(ordenados[0])
        semanas = self._semanas_desde(fecha_primera)
        dias_ult = self._dias_desde(fecha_ultima)
        self._featured_card.set_meta(
            f"{semanas} semana{'s' if semanas != 1 else ''} en programa · Última sesión: hace {dias_ult}"
        )

        # Tags derivados de datos
        tags = []
        if prom >= 7:
            tags.append(("Progreso alto", "teal"))
        elif prom < 4:
            tags.append(("Requiere atención", "violet"))
        if len(ordenados) >= 21:
            tags.append(("Constancia", "accent"))
        self._featured_card.set_tags(tags)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        apply_chart_theme(self._modo)
        self.setStyleSheet("background: transparent;")
        self._tabs.setStyleSheet(stylesheet_tabwidget_underline(self._modo))
        ink1 = v3c("text", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self._lbl_eyebrow.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._lbl_name.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._lbl_meta.setStyleSheet(f"color: {ink2}; background: transparent;")
