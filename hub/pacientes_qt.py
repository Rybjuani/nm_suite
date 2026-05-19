"""
hub/pacientes_qt.py — Vista detallada de paciente (PyQt6)

Tabs como pills: Registros | Asignar | Banco | IA
- Registros: tabla de datos + pyqtgraph spline + exportar PDF
- Asignar: formulario tarea + recordatorio remoto
- Banco: CRUD banco de actividades + IA autocompletar
- IA: resumen, sugerencias, generar tarea

Toda la lógica de DB/Supabase preservada exacta de pacientes.py.
"""

import os
import sys
import threading
from datetime import datetime, timezone

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QObject
from PyQt6 import sip
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTabWidget, QTextEdit, QSizePolicy, QComboBox,
    QApplication, QPushButton,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput,
        NMProgressBar, NMToggle, NMToast, NMSkeleton, ThemeManager, h_spacer,
        NMProgressLine, NMFeaturedCard, NMModuleRing, NMTypingDots,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, qfont_mono, interpolate_color,
        apply_chart_theme,
        get_gradient, gradient_colors, stylesheet_lineedit, stylesheet_textedit,
        stylesheet_tabwidget, stylesheet_combobox, stylesheet_scrollarea,
        sp,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_SMALL, RADIUS_PILL, PAD_CONTAINER, PAD_CARD,
        GAP_CARDS, GAP_ELEMENTS, CATEGORY_COLORS,
        # v3
        v3c, V3_SP, V3_RD,
    )
    from shared.theme import CATEGORY_COLORS, TYPOGRAPHY
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput,
        NMProgressBar, NMToggle, NMToast, NMSkeleton, ThemeManager, h_spacer,
        NMProgressLine, NMFeaturedCard, NMModuleRing, NMTypingDots,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, qfont_mono, interpolate_color,
        apply_chart_theme,
        get_gradient, gradient_colors, stylesheet_lineedit, stylesheet_textedit,
        stylesheet_tabwidget, stylesheet_combobox, stylesheet_scrollarea,
        sp,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_SMALL, RADIUS_PILL, PAD_CONTAINER, PAD_CARD,
        GAP_CARDS, GAP_ELEMENTS,
        v3c, V3_SP, V3_RD,
    )
    from shared.theme import CATEGORY_COLORS, TYPOGRAPHY


# ── v3 surface helpers ──────────────────────────────────────────────────────

def _v3_surface(modo: str) -> str:
    """Surface color v3 con awareness dark/light."""
    return v3c("surfaceSolid" if "dark" in norm_modo(modo) else "surface",
                modo).name()


def _v3_elevated(modo: str) -> str:
    return v3c("elevatedSolid" if "dark" in norm_modo(modo) else "elevated",
                modo).name()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _card_frame(modo: str) -> QFrame:
    """Frame card v3 — superficie + border `borderSoft` + radius lg (14) + sombra."""
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect

    surface = _v3_surface(modo)
    border = v3c("borderSoft", modo).name()
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {surface};
            border-radius: {V3_RD['lg']}px;
            border: 1px solid {border};
        }}
    """)
    # Sombra v3 — sin esta, las cards en light son indistinguibles del fondo
    is_dark = "dark" in norm_modo(modo)
    shadow = QGraphicsDropShadowEffect(f)
    if is_dark:
        shadow.setBlurRadius(30); shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 115))
    else:
        shadow.setBlurRadius(16); shadow.setOffset(0, 6)
        shadow.setColor(QColor(15, 23, 42, 22))
    f.setGraphicsEffect(shadow)
    return f


def _row_item(text: str, modo: str) -> QFrame:
    """Row item v3 — fondo `elevated` + radius sm + texto `text2`."""
    elev = _v3_elevated(modo)
    text_color = v3c("text2", modo).name()
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {elev};
            border-radius: {V3_RD['sm']}px;
            border: none;
        }}
    """)
    lbl = QLabel(text)
    lbl.setFont(qfont("size_caption"))
    lbl.setStyleSheet(f"color: {text_color}; background: transparent;")
    lbl.setWordWrap(True)
    lay = QHBoxLayout(f)
    lay.setContentsMargins(V3_SP["sm"], V3_SP["xs"],
                             V3_SP["sm"], V3_SP["xs"])
    lay.addWidget(lbl)
    return f


# ── Gráfico de ánimo con pyqtgraph ───────────────────────────────────────────

def _build_animo_graph(parent: QWidget, registros: list, modo: str) -> QWidget:
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

    # Datos
    puntajes = []
    fechas = []
    for r in registros:
        p = r.get("puntaje")
        f = r.get("fecha", "")[:10]
        if p is not None:
            puntajes.append(float(p))
            fechas.append(f)

    if not puntajes:
        lbl = QLabel("Sin registros de ánimo")
        lbl.setFont(qfont("size_body"))
        lbl.setStyleSheet(f"color: {c['text_tertiary']};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    # Configurar pyqtgraph con tema
    pg.setConfigOption("background", C("bg_primary", modo))
    pg.setConfigOption("foreground", C("text_primary", modo))

    plot = pg.PlotWidget()
    plot.setBackground(C("bg_primary", modo))
    plot.setMinimumHeight(220)

    # Eje Y
    plot.setYRange(0, 11, padding=0.05)
    tick_font = qfont("size_caption")
    plot.getAxis("left").setTickFont(tick_font)
    plot.getAxis("bottom").setTickFont(tick_font)

    # Etiquetas del eje X (fechas)
    x = list(range(len(puntajes)))
    step = max(1, len(fechas) // 6)
    ticks = [(i, fechas[i][-5:]) for i in range(0, len(fechas), step)]
    plot.getAxis("bottom").setTicks([ticks])

    # Interpolación spline (si hay suficientes puntos)
    if len(x) >= 4:
        try:
            from scipy.interpolate import make_interp_spline
            x_smooth = np.linspace(0, len(puntajes) - 1, len(puntajes) * 8)
            spline = make_interp_spline(x, puntajes, k=3)
            y_smooth = spline(x_smooth)
            y_smooth = np.clip(y_smooth, 0, 10)
        except ImportError:
            x_smooth = np.array(x, dtype=float)
            y_smooth = np.array(puntajes)
    else:
        x_smooth = np.array(x, dtype=float)
        y_smooth = np.array(puntajes)

    # Área bajo la curva con gradiente teal → violet
    teal_c = QColor(accent)
    violet_c = QColor(teal)
    fill_grad = QLinearGradient(0, 0, 0, 1)
    fill_grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
    fill_grad.setColorAt(0.0, QColor(teal_c.red(), teal_c.green(), teal_c.blue(), 80))
    fill_grad.setColorAt(1.0, QColor(violet_c.red(), violet_c.green(), violet_c.blue(), 10))
    fill = pg.FillBetweenItem(
        pg.PlotDataItem(x_smooth, y_smooth),
        pg.PlotDataItem(x_smooth, [0] * len(x_smooth)),
        brush=pg.mkBrush(QBrush(fill_grad)),
    )
    plot.addItem(fill)

    # Línea principal
    pen = pg.mkPen(color=accent, width=2)
    plot.plot(x_smooth, y_smooth, pen=pen)

    # Puntos interactivos
    scatter = pg.ScatterPlotItem(
        x=x, y=puntajes,
        size=8, pen=pg.mkPen(None),
        brush=pg.mkBrush(teal),
    )
    plot.addItem(scatter)

    # Línea de promedio
    if puntajes:
        prom = sum(puntajes) / len(puntajes)
        prom_pen = pg.mkPen(color=teal, width=1, style=Qt.PenStyle.DashLine)
        plot.addLine(y=prom, pen=prom_pen,
                     label=f"prom {prom:.1f}",
                     labelOpts={"color": teal})

    return plot


# ── Tab: Registros ────────────────────────────────────────────────────────────

class _TabRegistros(QWidget):
    _datos_loaded_signal = pyqtSignal(dict)

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
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, 12, PAD_CONTAINER, 12)
        layout.setSpacing(GAP_ELEMENTS)

        # Botones top
        top = QHBoxLayout()
        btn_load = NMButtonOutline("↻ Cargar datos", modo=self._modo)
        btn_load.setFixedSize(130, 30)
        btn_load.clicked.connect(self._cargar_datos)
        top.addWidget(btn_load)
        top.addStretch()
        self._btn_pdf = NMButton("Exportar PDF", modo=self._modo, width=130, height=30)
        self._btn_pdf.clicked.connect(self._exportar_pdf)
        top.addWidget(self._btn_pdf)
        layout.addLayout(top)

        # Scroll de registros
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._list_w = QWidget()
        self._list_w.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_w)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._list_w)
        layout.addWidget(self._scroll)

        # Placeholder
        ph = QLabel("Presioná '↻ Cargar datos' para ver los registros.")
        ph.setFont(qfont("size_body"))
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        self._list_layout.addWidget(ph)

    def _cargar_datos(self):
        if not self._sb or self._cargando:
            return
        self._cargando = True
        c = colors(self._modo)
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
                "animo":     ("mood_records",          "fecha,hora,puntaje,nota",                20),
                "resp":      ("breathing_sessions",    "fecha,hora,tecnica,duracion_minutos",     15),
                "pens":      ("thought_records",       "fecha,hora,emocion,intensidad,pensamiento", 15),
                "checklist": ("checklist_completions", "fecha,descripcion,categoria,origen",      30),
                "timer":     ("timer_sessions",        "fecha,hora,nombre,categoria,duracion_real", 15),
                "reclog":    ("reminder_logs",         "fecha,hora,mensaje,cerrado",              15),
            }
            for clave, (tabla, campos, lim) in tablas.items():
                try:
                    res = (self._sb.table(tabla).select(campos)
                           .eq("patient_id", self._pid)
                           .order("fecha", desc=True).limit(lim).execute())
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

    def _mostrar_registros(self, datos: dict):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                self._list_layout.removeWidget(w)
                w.deleteLater()

        c = colors(self._modo)

        def _seccion(titulo: str, filas: list, fila_fn):
            frame = _card_frame(self._modo)
            vl = QVBoxLayout(frame)
            vl.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
            vl.setSpacing(4)
            t = QLabel(titulo)
            t.setFont(qfont("size_small", bold=True))
            t.setStyleSheet(f"color: {C('accent', self._modo)}; background: transparent;")
            vl.addWidget(t)
            if not filas:
                e = QLabel("Sin registros.")
                e.setFont(qfont("size_caption"))
                e.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
                vl.addWidget(e)
            else:
                for r in filas:
                    vl.addWidget(_row_item(fila_fn(r), self._modo))
            self._list_layout.addWidget(frame)

        # Ánimo con promedio + gráfico
        animo = datos.get("animo", [])
        puntajes = [r.get("puntaje") for r in animo if r.get("puntaje") is not None]
        animo_frame = _card_frame(self._modo)
        avl = QVBoxLayout(animo_frame)
        avl.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
        avl.setSpacing(6)
        at = QLabel("Registros de ánimo")
        at.setFont(qfont("size_small", bold=True))
        at.setStyleSheet(f"color: {C('accent', self._modo)}; background: transparent;")
        avl.addWidget(at)
        if puntajes:
            prom = round(sum(puntajes) / len(puntajes), 1)

            # Stats row: label + NMModuleRing (adherencia últimos 7 días)
            stats_row = QHBoxLayout()
            pl = QLabel(
                f"Promedio: {prom}/10  |  {len(animo)} registros"
            )
            pl.setFont(qfont("size_body"))
            pl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            stats_row.addWidget(pl, stretch=1)

            distinct_days = len({r.get("fecha", "")[:10] for r in animo if r.get("fecha")})
            adherence_pct = min(1.0, distinct_days / 7)
            ring = NMModuleRing(size=48, pct=adherence_pct,
                                modo=self._modo, parent=animo_frame)
            stats_row.addWidget(ring, alignment=Qt.AlignmentFlag.AlignRight)
            avl.addLayout(stats_row)

            # Gráfico pyqtgraph
            graph = _build_animo_graph(animo_frame, animo, self._modo)
            avl.addWidget(graph)

        for r in animo[:5]:
            nota = (r.get("nota") or "")[:50]
            avl.addWidget(_row_item(
                f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                f"Ánimo: {r.get('puntaje','—')}  {nota}",
                self._modo
            ))
        self._list_layout.addWidget(animo_frame)

        _seccion("Sesiones de respiración", datos.get("resp", []),
                 lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                           f"{r.get('tecnica','?')}  ({r.get('duracion_minutos','?')} min)")
        _seccion("Registros TCC", datos.get("pens", []),
                 lambda r: f"{r.get('fecha','')[:10]}  —  {r.get('emocion','?')} "
                           f"(int.{r.get('intensidad','?')})  "
                           f"{(r.get('pensamiento') or '')[:60]}")
        _seccion("Sesiones de temporizador", datos.get("timer", []),
                 lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                           f"{(r.get('nombre') or 'Sin nombre')[:30]}  "
                           f"{(r.get('duracion_real') or 0) // 60} min")
        _seccion("Recordatorios disparados", datos.get("reclog", []),
                 lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                           f"{(r.get('mensaje') or '')[:60]}")

    def _exportar_pdf(self):
        if not self._datos_cache:
            NMToast.display(self.window(), "Cargá los datos primero.", variant="info")
            return
        self._btn_pdf.setText("Generando…")
        self._btn_pdf.setEnabled(False)
        from hub.exportar import exportar_pdf
        exportar_pdf(
            self._nombre, self._pid, self._datos_cache,
            on_done=lambda ruta: QTimer.singleShot(
                0, lambda r=ruta: self._pdf_ok(r) if not sip.isdeleted(self) else None),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda m=msg: self._pdf_error(m) if not sip.isdeleted(self) else None),
        )

    def _pdf_ok(self, ruta: str):
        self._btn_pdf.setText("Exportar PDF")
        self._btn_pdf.setEnabled(True)
        NMToast.display(self.window(), f"PDF guardado en Downloads.", variant="success")

    def _pdf_error(self, msg: str):
        self._btn_pdf.setText("Exportar PDF")
        self._btn_pdf.setEnabled(True)
        NMToast.display(self.window(), f"Error PDF: {msg[:60]}", variant="error")


# ── Tab: Asignar ──────────────────────────────────────────────────────────────

class _TabAsignar(QWidget):
    def __init__(self, modo: str, sb, pid: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._setup()

    def _setup(self):
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, 12, PAD_CONTAINER, 12)
        layout.setSpacing(GAP_CARDS)

        # ── Asignar tarea ─────────────────────────────────────────────────────
        card_r = _card_frame(self._modo)
        vl_r = QVBoxLayout(card_r)
        vl_r.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_r.setSpacing(8)
        QLabel_bold = QLabel("Asignar tarea de rutina")
        QLabel_bold.setFont(qfont("size_body", bold=True))
        QLabel_bold.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        vl_r.addWidget(QLabel_bold)
        self._entry_tarea = NMInput("Descripción de la tarea…", modo=self._modo)
        vl_r.addWidget(self._entry_tarea)
        row_r = QHBoxLayout()
        lbl_sec = QLabel("Sección:")
        lbl_sec.setFont(qfont("size_small"))
        lbl_sec.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        row_r.addWidget(lbl_sec)
        self._combo_sec = QComboBox()
        self._combo_sec.addItems(["manana", "tarde", "noche"])
        self._combo_sec.setFixedSize(130, 32)
        self._combo_sec.setStyleSheet(stylesheet_combobox(self._modo))
        row_r.addWidget(self._combo_sec)
        row_r.addStretch()
        btn_asignar = NMButton("Asignar tarea", modo=self._modo, width=130, height=32)
        btn_asignar.clicked.connect(self._asignar_tarea)
        row_r.addWidget(btn_asignar)
        vl_r.addLayout(row_r)
        layout.addWidget(card_r)

        # ── Recordatorio remoto ───────────────────────────────────────────────
        card_rec = _card_frame(self._modo)
        vl_rec = QVBoxLayout(card_rec)
        vl_rec.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_rec.setSpacing(8)
        lbl_rec = QLabel("Enviar recordatorio remoto")
        lbl_rec.setFont(qfont("size_body", bold=True))
        lbl_rec.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        vl_rec.addWidget(lbl_rec)
        self._entry_rec_msg = NMInput("Mensaje del recordatorio…", modo=self._modo)
        vl_rec.addWidget(self._entry_rec_msg)
        row_rec = QHBoxLayout()
        lbl_hora = QLabel("Hora (HH:MM):")
        lbl_hora.setFont(qfont("size_small"))
        lbl_hora.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        row_rec.addWidget(lbl_hora)
        self._entry_rec_hora = NMInput("22:00", modo=self._modo)
        self._entry_rec_hora.setMinimumWidth(80)
        row_rec.addWidget(self._entry_rec_hora)
        row_rec.addStretch()
        btn_enviar = NMButton("Enviar", modo=self._modo, width=100, height=32)
        btn_enviar.clicked.connect(self._asignar_recordatorio)
        row_rec.addWidget(btn_enviar)
        vl_rec.addLayout(row_rec)
        layout.addWidget(card_rec)
        layout.addStretch()

    def _asignar_tarea(self):
        if not self._sb:
            return
        tarea = self._entry_tarea.text().strip()
        if not tarea:
            return
        seccion = self._combo_sec.currentText()
        try:
            self._sb.table("assigned_tasks").insert({
                "patient_id":  self._pid,
                "descripcion": tarea,
                "seccion":     seccion,
            }).execute()
            self._entry_tarea.clear()
            NMToast.display(self.window(),
                         f"Tarea '{tarea[:30]}' asignada.", variant="success")
        except Exception as e:
            NMToast.display(self.window(), str(e)[:80], variant="error")

    def _asignar_recordatorio(self):
        if not self._sb:
            return
        msg = self._entry_rec_msg.text().strip()
        hora = self._entry_rec_hora.text().strip()
        if not msg or not hora:
            return
        try:
            self._sb.table("assigned_reminders").insert({
                "patient_id": self._pid,
                "mensaje":    msg,
                "hora":       hora,
                "dias":       "1,2,3,4,5,6,7",
                "activa":     True,
            }).execute()
            self._entry_rec_msg.clear()
            self._entry_rec_hora.clear()
            NMToast.display(self.window(), "Recordatorio enviado.", variant="success")
        except Exception as e:
            NMToast.display(self.window(), str(e)[:80], variant="error")


# ── Tab: Banco ────────────────────────────────────────────────────────────────

class _TabBanco(QWidget):
    def __init__(self, modo: str, sb, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._setup()

    def _setup(self):
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, 12, PAD_CONTAINER, 12)
        layout.setSpacing(GAP_ELEMENTS)

        # Formulario nueva actividad
        form = _card_frame(self._modo)
        fl = QVBoxLayout(form)
        fl.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        fl.setSpacing(8)
        t = QLabel("Nueva actividad")
        t.setFont(qfont("size_body", bold=True))
        t.setStyleSheet(f"color: {C('accent', self._modo)}; background: transparent;")
        fl.addWidget(t)
        self._ent_nombre = NMInput("Nombre de la actividad…", modo=self._modo)
        fl.addWidget(self._ent_nombre)
        self._ent_desc = NMInput("Descripción breve…", modo=self._modo)
        fl.addWidget(self._ent_desc)
        row_form = QHBoxLayout()
        lbl_cat = QLabel("Categoría:")
        lbl_cat.setFont(qfont("size_small"))
        lbl_cat.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        row_form.addWidget(lbl_cat)
        self._cmb_cat = QComboBox()
        self._cmb_cat.addItems(list(CATEGORY_COLORS.keys()))
        self._cmb_cat.setFixedSize(150, 32)
        self._cmb_cat.setStyleSheet(stylesheet_combobox(self._modo))
        row_form.addWidget(self._cmb_cat)
        lbl_animo = QLabel("Ánimo:")
        lbl_animo.setFont(qfont("size_small"))
        lbl_animo.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        row_form.addWidget(lbl_animo)
        self._cmb_animo = QComboBox()
        self._cmb_animo.addItems(["1-4 (bajo)", "4-7 (medio)", "7-10 (alto)"])
        self._cmb_animo.setCurrentIndex(1)
        self._cmb_animo.setFixedSize(130, 32)
        self._cmb_animo.setStyleSheet(stylesheet_combobox(self._modo))
        row_form.addWidget(self._cmb_animo)
        row_form.addStretch()
        fl.addLayout(row_form)
        # Botones IA + Agregar
        btn_row = QHBoxLayout()
        btn_ia = NMButtonOutline("✦ IA: completar", modo=self._modo)
        btn_ia.setFixedSize(160, 32)
        btn_ia.clicked.connect(self._ia_completar)
        btn_row.addWidget(btn_ia)
        btn_row.addStretch()
        btn_add = NMButton("Agregar actividad", modo=self._modo, width=160, height=32)
        btn_add.clicked.connect(self._agregar)
        btn_row.addWidget(btn_add)
        fl.addLayout(btn_row)
        layout.addWidget(form)

        # Lista de actividades
        self._list_scroll = QScrollArea()
        self._list_scroll.setWidgetResizable(True)
        self._list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._list_w = QWidget()
        self._list_w.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_w)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_scroll.setWidget(self._list_w)
        layout.addWidget(self._list_scroll)

        self._cargar_banco()

    def _animo_rango(self) -> tuple:
        sel = self._cmb_animo.currentText()
        if "bajo" in sel:   return 1, 4
        if "alto" in sel:   return 7, 10
        return 4, 7

    def _agregar(self):
        if not self._sb:
            return
        nombre = self._ent_nombre.text().strip()
        if not nombre:
            return
        desc = self._ent_desc.text().strip()
        cat = self._cmb_cat.currentText()
        animo_min, animo_max = self._animo_rango()
        try:
            self._sb.table("activity_bank").insert({
                "nombre": nombre, "descripcion": desc,
                "categoria": cat, "animo_min": animo_min,
                "animo_max": animo_max, "activa": True,
            }).execute()
            self._ent_nombre.clear()
            self._ent_desc.clear()
            self._cargar_banco()
            NMToast.display(self.window(), f"'{nombre}' añadida al banco.", variant="success")
        except Exception as e:
            NMToast.display(self.window(), str(e)[:80], variant="error")

    def _cargar_banco(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                self._list_layout.removeWidget(w)
                w.deleteLater()
        if not self._sb:
            return
        try:
            res = self._sb.table("activity_bank").select(
                "id,nombre,descripcion,categoria,animo_min,animo_max,activa"
            ).order("categoria").execute()
            rows = res.data or []
        except Exception:
            rows = []

        c = colors(self._modo)
        if not rows:
            lbl = QLabel("El banco está vacío.")
            lbl.setFont(qfont("size_body"))
            lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            self._list_layout.addWidget(lbl)
            return

        for r in rows:
            cat = r.get("categoria", "")
            cat_color = CATEGORY_COLORS.get(cat, C("accent", self._modo))
            row_f = QFrame()
            row_f.setMinimumHeight(36)
            row_f.setStyleSheet(f"""
                QFrame {{
                    background: {c['bg_surface']};
                    border-radius: {RADIUS_BUTTON}px;
                    border: 1px solid {c.get('border_card', c['border'])};
                }}
            """)
            rl = QHBoxLayout(row_f)
            rl.setContentsMargins(8, 0, 8, 0)
            rl.setSpacing(8)

            # Dot de categoría
            dot = QLabel("●")
            dot.setFont(qfont("size_caption"))
            dot.setStyleSheet(f"color: {cat_color}; background: transparent;")
            dot.setFixedWidth(14)
            rl.addWidget(dot)

            info = QLabel(
                f"{r.get('nombre','')}  ·  [{cat}]  ·  "
                f"ánimo {r.get('animo_min',0)}–{r.get('animo_max',10)}"
            )
            info.setFont(qfont("size_small"))
            col = c["text_primary"] if r.get("activa", True) else c["text_tertiary"]
            info.setStyleSheet(f"color: {col}; background: transparent;")
            rl.addWidget(info, stretch=1)

            rid = r.get("id")
            if rid is None:
                continue
            btn_del = QPushButton("✕")
            btn_del.setFont(qfont("size_caption"))
            btn_del.setFlat(True)
            btn_del.setFixedSize(24, 24)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(f"""
                QPushButton {{
                    color: {c['text_tertiary']};
                    background: transparent;
                    border: none;
                    border-radius: {RADIUS_PILL}px;
                }}
                QPushButton:hover {{
                    color: {c['text_on_accent']};
                    background: {c['error']};
                }}
            """)
            btn_del.clicked.connect(lambda _, _rid=rid: self._eliminar(int(_rid)))
            rl.addWidget(btn_del)
            self._list_layout.addWidget(row_f)

    def _eliminar(self, rid: int):
        if not self._sb:
            return
        try:
            self._sb.table("activity_bank").delete().eq("id", rid).execute()
            self._cargar_banco()
        except Exception as e:
            NMToast.display(self.window(), str(e)[:80], variant="error")

    def _ia_completar(self):
        nombre = self._ent_nombre.text().strip()
        if not nombre:
            return
        self._ent_desc.setText("Generando con IA…")
        from hub.ia_asistente import autocompletar_actividad
        autocompletar_actividad(
            nombre,
            on_result=lambda txt: QTimer.singleShot(0, lambda t=txt: self._ia_ok(t) if not sip.isdeleted(self) else None),
            on_error=lambda msg: QTimer.singleShot(0, lambda m=msg: self._ia_err(m) if not sip.isdeleted(self) else None),
        )

    def _ia_ok(self, txt: str):
        self._ent_desc.setText(txt)

    def _ia_err(self, msg: str):
        self._ent_desc.clear()
        import hub.ia_asistente as ia
        NMToast.display(self.window(), ia.status_msg(), variant="error")


# ── Tab: IA ───────────────────────────────────────────────────────────────────

class _TabIA(QWidget):
    def __init__(self, modo: str, sb, pid: str, nombre: str,
                 datos_cache_ref, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._datos_ref = datos_cache_ref
        datos_cache_ref.changed.connect(self._on_datos_changed)
        self._setup()

    def _on_datos_changed(self, datos: dict):
        pass  # IA reads datos_ref.cache on demand

    def _setup(self):
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, 12, PAD_CONTAINER, 12)
        layout.setSpacing(GAP_CARDS)

        # ── Resumen ───────────────────────────────────────────────────────────
        card_res = _card_frame(self._modo)
        vl_res = QVBoxLayout(card_res)
        vl_res.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_res.setSpacing(8)
        lbl_res = QLabel("Resumen de evolución")
        lbl_res.setFont(qfont("size_body", bold=True))
        lbl_res.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        vl_res.addWidget(lbl_res)
        self._txt_resumen = QTextEdit()
        self._txt_resumen.setMinimumHeight(80)
        self._txt_resumen.setReadOnly(True)
        self._txt_resumen.setPlaceholderText("El resumen aparecerá aquí…")
        self._txt_resumen.setStyleSheet(stylesheet_textedit(self._modo))
        vl_res.addWidget(self._txt_resumen)
        row_res = QHBoxLayout()
        self._btn_resumen = NMButton("Generar resumen", modo=self._modo, width=160, height=32)
        self._btn_resumen.clicked.connect(self._generar_resumen)
        row_res.addWidget(self._btn_resumen)
        btn_copy_res = NMButtonOutline("Copiar", modo=self._modo)
        btn_copy_res.setFixedSize(80, 32)
        btn_copy_res.clicked.connect(
            lambda: QApplication.clipboard().setText(self._txt_resumen.toPlainText())
        )
        row_res.addWidget(btn_copy_res)
        row_res.addStretch()
        vl_res.addLayout(row_res)

        # NMTypingDots: visible during IA generation
        self._typing_dots = NMTypingDots(modo=self._modo, parent=card_res)
        self._typing_dots.hide()
        vl_res.addWidget(self._typing_dots, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(card_res)

        # ── Sugerencias ───────────────────────────────────────────────────────
        card_sug = _card_frame(self._modo)
        vl_sug = QVBoxLayout(card_sug)
        vl_sug.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_sug.setSpacing(8)
        lbl_sug = QLabel("Sugerencias de acción")
        lbl_sug.setFont(qfont("size_body", bold=True))
        lbl_sug.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        vl_sug.addWidget(lbl_sug)
        self._frame_sug = QWidget()
        self._frame_sug.setStyleSheet("background: transparent;")
        self._sug_layout = QVBoxLayout(self._frame_sug)
        self._sug_layout.setContentsMargins(0, 0, 0, 0)
        self._sug_layout.setSpacing(4)
        ph = QLabel("Presioná 'Generar sugerencias' para obtener acciones concretas.")
        ph.setFont(qfont("size_small"))
        ph.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        self._sug_layout.addWidget(ph)
        vl_sug.addWidget(self._frame_sug)
        self._btn_sugerencias = NMButton("Generar sugerencias", modo=self._modo,
                                          width=180, height=32)
        self._btn_sugerencias.clicked.connect(self._generar_sugerencias)
        vl_sug.addWidget(self._btn_sugerencias, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card_sug)

        # ── Generar tarea ─────────────────────────────────────────────────────
        card_tarea = _card_frame(self._modo)
        vl_t = QVBoxLayout(card_tarea)
        vl_t.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        vl_t.setSpacing(8)
        lbl_t = QLabel("Generar tarea personalizada")
        lbl_t.setFont(qfont("size_body", bold=True))
        lbl_t.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        vl_t.addWidget(lbl_t)
        self._ent_ctx = NMInput(
            "Ej: paciente con ansiedad leve, mejoró en respiración…",
            modo=self._modo
        )
        vl_t.addWidget(self._ent_ctx)
        self._lbl_tarea_gen = QLabel("")
        self._lbl_tarea_gen.setFont(qfont("size_body"))
        self._lbl_tarea_gen.setWordWrap(True)
        self._lbl_tarea_gen.setStyleSheet(
            f"color: {C('accent', self._modo)}; background: transparent;"
        )
        vl_t.addWidget(self._lbl_tarea_gen)
        row_t = QHBoxLayout()
        btn_gen = NMButton("Generar", modo=self._modo, width=100, height=32)
        btn_gen.clicked.connect(self._generar_tarea)
        row_t.addWidget(btn_gen)
        btn_copy_t = NMButtonOutline("Copiar", modo=self._modo)
        btn_copy_t.setFixedSize(80, 32)
        btn_copy_t.clicked.connect(
            lambda: QApplication.clipboard().setText(self._lbl_tarea_gen.text())
        )
        row_t.addWidget(btn_copy_t)
        row_t.addStretch()
        vl_t.addLayout(row_t)
        layout.addWidget(card_tarea)
        layout.addStretch()

    def _generar_resumen(self):
        datos = self._datos_ref.cache
        if not datos or not any(
            datos.get(k) for k in ("animo", "resp", "pens", "checklist")
        ):
            NMToast.display(self.window(),
                         "Cargá los datos del paciente primero (Tab Registros).",
                         variant="info")
            return
        self._btn_resumen.setText("Generando…")
        self._btn_resumen.setEnabled(False)
        self._txt_resumen.setPlainText("")
        if hasattr(self, "_typing_dots"):
            self._typing_dots.show()
            self._typing_dots.start()
        from hub.ia_asistente import resumir_evolucion
        resumir_evolucion(
            datos, self._nombre,
            on_result=lambda txt: QTimer.singleShot(
                0, lambda t=txt: self._resumen_ok(t) if not sip.isdeleted(self) else None),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda m=msg: self._resumen_err(m) if not sip.isdeleted(self) else None),
        )

    def _resumen_ok(self, txt: str):
        self._btn_resumen.setText("Generar resumen")
        self._btn_resumen.setEnabled(True)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        self._txt_resumen.setPlainText(txt)

    def _resumen_err(self, msg: str):
        self._btn_resumen.setText("Generar resumen")
        self._btn_resumen.setEnabled(True)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        self._txt_resumen.setPlainText(msg)

    def _generar_sugerencias(self):
        datos = self._datos_ref.cache
        if not datos:
            NMToast.display(self.window(),
                         "Cargá los datos del paciente primero.",
                         variant="info")
            return
        self._btn_sugerencias.setText("Generando…")
        self._btn_sugerencias.setEnabled(False)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.show()
            self._typing_dots.start()
        from hub.ia_asistente import sugerir_acciones
        sugerir_acciones(
            datos, self._nombre,
            on_result=lambda txt: QTimer.singleShot(
                0, lambda t=txt: self._sugerencias_ok(t) if not sip.isdeleted(self) else None),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda m=msg: self._sugerencias_err(m) if not sip.isdeleted(self) else None),
        )

    def _sugerencias_ok(self, txt: str):
        self._btn_sugerencias.setText("Generar sugerencias")
        self._btn_sugerencias.setEnabled(True)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        c = colors(self._modo)
        while self._sug_layout.count():
            item = self._sug_layout.takeAt(0)
            w = item.widget()
            if w:
                self._sug_layout.removeWidget(w)
                w.deleteLater()
        for linea in txt.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            fila = QFrame()
            fila.setStyleSheet(f"""
                QFrame {{
                    background: {c['bg_elevated']};
                    border-radius: {RADIUS_BUTTON}px;
                    border: none;
                }}
            """)
            fl = QHBoxLayout(fila)
            fl.setContentsMargins(8, 6, 8, 6)
            lbl = QLabel(linea)
            lbl.setFont(qfont("size_small"))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            fl.addWidget(lbl, stretch=1)
            btn_ap = NMButton("Aplicar", modo=self._modo, width=70, height=28)
            btn_ap.clicked.connect(
                lambda _, l=linea: QApplication.clipboard().setText(l)
            )
            fl.addWidget(btn_ap)
            self._sug_layout.addWidget(fila)

    def _sugerencias_err(self, msg: str):
        self._btn_sugerencias.setText("Generar sugerencias")
        self._btn_sugerencias.setEnabled(True)
        if hasattr(self, "_typing_dots"):
            self._typing_dots.stop()
            self._typing_dots.hide()
        NMToast.display(self.window(), msg, variant="error")

    def _generar_tarea(self):
        ctx = self._ent_ctx.text().strip()
        if not ctx:
            return
        self._lbl_tarea_gen.setText("Generando…")
        from hub.ia_asistente import generar_tarea
        generar_tarea(
            ctx,
            on_result=lambda txt: QTimer.singleShot(
                0, lambda t=txt: self._lbl_tarea_gen.setText(t) if not sip.isdeleted(self) else None),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda m=msg: self._lbl_tarea_gen.setText(m) if not sip.isdeleted(self) else None),
        )


# ── Shared state between TabRegistros and TabIA ────────────────────────────────

class _DatosRef(QObject):
    """Objeto de estado compartido limpio entre Registros e IA."""
    changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.cache: dict = {}


# ── DetallePacienteView ───────────────────────────────────────────────────────

class DetallePacienteView(QWidget):
    """Panel completo de detalle de paciente con QTabWidget como pills."""

    back_requested = pyqtSignal()
    _legal_loaded_signal = pyqtSignal(object, object)

    def __init__(self, modo: str, sb, paciente_id: str, paciente_nombre: str,
                 parent=None):
        super().__init__(parent)
        self._legal_loaded_signal.connect(self._on_legal_loaded)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = paciente_id
        self._nombre = paciente_nombre
        self._datos_ref = _DatosRef()
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _setup(self):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── NMProgressLine: 2px gradient line at top ──────────────────────────
        self._progress_line = NMProgressLine(total=1, current=1,
                                             modo=self._modo, parent=self)
        layout.addWidget(self._progress_line)

        # Título
        top = QWidget()
        top.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(PAD_CONTAINER, 12, PAD_CONTAINER, 8)
        t = QLabel(self._nombre)
        t.setFont(qfont("size_h3", bold=True))
        t.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        tl.addWidget(t)
        layout.addWidget(top)

        # ── NMFeaturedCard: mood summary above tabs ───────────────────────────
        self._featured_card = NMFeaturedCard(modo=self._modo, parent=self)
        # Wrap in padded container
        fc_wrapper = QWidget()
        fc_wrapper.setStyleSheet("background: transparent;")
        fc_layout = QHBoxLayout(fc_wrapper)
        fc_layout.setContentsMargins(PAD_CONTAINER, 0, PAD_CONTAINER, sp("sm"))
        fc_layout.addWidget(self._featured_card)
        layout.addWidget(fc_wrapper)

        # Wire data signal to update featured card when records load
        self._datos_ref.changed.connect(self._update_featured)

        self._legal_consent: dict | None = None
        legal_wrapper = QWidget()
        legal_wrapper.setStyleSheet("background: transparent;")
        legal_layout = QHBoxLayout(legal_wrapper)
        legal_layout.setContentsMargins(PAD_CONTAINER, 0, PAD_CONTAINER, sp("sm"))
        self._legal_card = NMCard(modo=self._modo)
        legal_inner = QHBoxLayout(self._legal_card)
        legal_inner.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        legal_inner.setSpacing(12)
        legal_text = QVBoxLayout()
        legal_title = QLabel("Estado legal / Consentimiento")
        legal_title.setFont(qfont("size_body", bold=True))
        legal_title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._legal_status = QLabel("Consultando consentimiento...")
        self._legal_status.setWordWrap(True)
        self._legal_status.setFont(qfont("size_caption"))
        self._legal_status.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        legal_text.addWidget(legal_title)
        legal_text.addWidget(self._legal_status)
        legal_inner.addLayout(legal_text, stretch=1)
        self._btn_consent_pdf = NMButton("Descargar constancia", modo=self._modo, width=170, height=30)
        self._btn_consent_pdf.setEnabled(False)
        self._btn_consent_pdf.clicked.connect(self._descargar_constancia_consentimiento)
        legal_inner.addWidget(self._btn_consent_pdf, alignment=Qt.AlignmentFlag.AlignTop)
        legal_layout.addWidget(self._legal_card)
        layout.addWidget(legal_wrapper)
        self._load_legal_consent()

        # QTabWidget con stylesheet pills
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(stylesheet_tabwidget(self._modo))

        # Instanciar tabs
        self._tab_reg = _TabRegistros(self._modo, self._sb,
                                       self._pid, self._nombre)
        self._tab_asig = _TabAsignar(self._modo, self._sb, self._pid)
        self._tab_banco = _TabBanco(self._modo, self._sb)
        self._tab_ia = _TabIA(self._modo, self._sb,
                               self._pid, self._nombre,
                               self._datos_ref)

        # Compartir datos_cache entre Registros e IA via _DatosRef
        self._tab_reg._datos_ref = self._datos_ref

        self._tabs.addTab(self._tab_reg,   "Registros")
        self._tabs.addTab(self._tab_asig,  "Asignar")
        self._tabs.addTab(self._tab_banco, "Banco")
        self._tabs.addTab(self._tab_ia,    "IA")

        layout.addWidget(self._tabs)

    def _load_legal_consent(self):
        if not self._sb:
            self._set_legal_consent(None, "pendiente")
            return

        def _fetch():
            try:
                res = (self._sb.table("legal_consents")
                       .select("status,accepted_at_utc,disclaimer_version,privacy_version,neuromood_suite_version,disclaimer_text_hash,privacy_text_hash,consent_scope,product_name,instalador_suite_version")
                       .eq("patient_id", self._pid)
                       .order("accepted_at_utc", desc=True)
                       .limit(1)
                       .execute())
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
        if status == "vigente":
            color = c["success"]
            prefix = "Consentimiento vigente"
            self._btn_consent_pdf.setEnabled(True)
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(True)
        elif status == "desactualizado":
            color = c["warning"]
            prefix = "Requiere nueva aceptación"
            self._btn_consent_pdf.setEnabled(bool(consent))
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(False)
        elif status == "revocado":
            color = c["error"]
            prefix = "Consentimiento revocado"
            self._btn_consent_pdf.setEnabled(bool(consent))
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(False)
        else:
            color = c["error"]
            prefix = "Consentimiento pendiente"
            self._btn_consent_pdf.setEnabled(False)
            if hasattr(self, "_tabs"):
                self._tabs.setEnabled(False)
        self._legal_status.setText(
            f"{prefix} · UTC: {accepted} · Aviso: {disc} · Privacidad: {priv} · Suite: {suite_v} · Hash: {h[:16] if h != '—' else h}"
        )
        self._legal_status.setStyleSheet(f"color: {color}; background: transparent;")

    def _descargar_constancia_consentimiento(self):
        if not self._legal_consent:
            NMToast.display(self.window(), "No hay constancia remota disponible.", variant="warning")
            return
        try:
            from hub.exportar import generar_constancia_consentimiento
            ruta = generar_constancia_consentimiento(self._nombre, self._pid, self._legal_consent)
            try:
                os.startfile(ruta)
            except Exception:
                pass
            NMToast.display(self.window(), "Constancia de consentimiento generada.", variant="success")
        except Exception as e:
            NMToast.display(self.window(), f"No se pudo generar la constancia: {str(e)[:90]}", variant="error")

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
        previos   = [r["puntaje"] for r in ordenados[7:14]]
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
        fecha_ultima  = _fecha_key(ordenados[0])
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
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")
        self._tabs.setStyleSheet(stylesheet_tabwidget(self._modo))
