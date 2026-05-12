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

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTabWidget, QTextEdit, QSizePolicy, QComboBox,
    QApplication,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput,
        NMToast, ThemeManager, separator, styled_label,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        get_gradient, stylesheet_lineedit, stylesheet_textedit,
        stylesheet_tabwidget, stylesheet_combobox,
        RADIUS_CARD, RADIUS_BUTTON, PAD_CONTAINER, PAD_CARD,
        GAP_CARDS, GAP_ELEMENTS, CATEGORY_COLORS,
    )
    from shared.theme import CATEGORY_COLORS
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput,
        NMToast, ThemeManager, separator, styled_label,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        get_gradient, stylesheet_lineedit, stylesheet_textedit,
        stylesheet_tabwidget, stylesheet_combobox,
        RADIUS_CARD, RADIUS_BUTTON, PAD_CONTAINER, PAD_CARD,
        GAP_CARDS, GAP_ELEMENTS,
    )
    from shared.theme import CATEGORY_COLORS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _card_frame(modo: str) -> QFrame:
    c = colors(norm_modo(modo))
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {c['bg_surface']};
            border-radius: {RADIUS_CARD}px;
            border: 1px solid {c.get('border_card', c['border'])};
        }}
    """)
    return f


def _row_item(text: str, modo: str) -> QFrame:
    c = colors(norm_modo(modo))
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {c['bg_elevated']};
            border-radius: 6px;
            border: none;
        }}
    """)
    lbl = QLabel(text)
    lbl.setFont(qfont("size_caption"))
    lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
    lbl.setWordWrap(True)
    lay = QHBoxLayout(f)
    lay.setContentsMargins(8, 4, 8, 4)
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
    c = colors(modo)
    grad = get_gradient(modo)
    is_dark = "dark" in modo

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
    pg.setConfigOptions(
        background=c["bg_surface"],
        foreground=c["text_secondary"],
    )

    plot = pg.PlotWidget()
    plot.setBackground(c["bg_surface"])
    plot.setMinimumHeight(220)

    # Eje Y
    plot.setYRange(0, 11, padding=0.05)
    plot.getAxis("left").setStyle(tickTextSize=9)
    plot.getAxis("bottom").setStyle(tickTextSize=8)

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

    # Área bajo la curva con FillBetweenItem
    teal = QColor(grad[0])
    fill_color = (teal.red(), teal.green(), teal.blue(), 40)
    fill = pg.FillBetweenItem(
        pg.PlotDataItem(x_smooth, y_smooth),
        pg.PlotDataItem(x_smooth, [0] * len(x_smooth)),
        brush=pg.mkBrush(*fill_color),
    )
    plot.addItem(fill)

    # Línea principal
    pen = pg.mkPen(color=grad[0], width=2)
    plot.plot(x_smooth, y_smooth, pen=pen)

    # Puntos interactivos
    scatter = pg.ScatterPlotItem(
        x=x, y=puntajes,
        size=8, pen=pg.mkPen(None),
        brush=pg.mkBrush(grad[0]),
    )
    plot.addItem(scatter)

    # Línea de promedio
    if puntajes:
        prom = sum(puntajes) / len(puntajes)
        prom_pen = pg.mkPen(color=grad[1], width=1, style=Qt.PenStyle.DashLine)
        plot.addLine(y=prom, pen=prom_pen,
                     label=f"prom {prom:.1f}",
                     labelOpts={"color": grad[1], "size": "8pt"})

    return plot


# ── Tab: Registros ────────────────────────────────────────────────────────────

class _TabRegistros(QWidget):
    def __init__(self, modo: str, sb, pid: str, nombre: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._datos_cache: dict = {}
        self._cargando = False
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
        self._btn_pdf = NMButton("⬇ Exportar PDF", modo=self._modo, width=130, height=30)
        self._btn_pdf.clicked.connect(self._exportar_pdf)
        top.addWidget(self._btn_pdf)
        layout.addLayout(top)

        # Scroll de registros
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("background: transparent; border: none;")
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
            if item.widget():
                item.widget().deleteLater()
        loading = QLabel("Cargando…")
        loading.setFont(qfont("size_body"))
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        self._list_layout.addWidget(loading)

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
            self._datos_cache = datos
            self._cargando = False
            QTimer.singleShot(0, lambda: self._mostrar_registros(datos))

        threading.Thread(target=_fetch, daemon=True).start()

    def _mostrar_registros(self, datos: dict):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
            pl = QLabel(
                f"Promedio: {prom}/10  |  {len(animo)} registros"
            )
            pl.setFont(qfont("size_body"))
            pl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            avl.addWidget(pl)

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
            NMToast.show(self.window(), "Cargá los datos primero.", variant="info")
            return
        self._btn_pdf.setText("Generando…")
        self._btn_pdf.setEnabled(False)
        from hub.exportar import exportar_pdf
        exportar_pdf(
            self._nombre, self._pid, self._datos_cache,
            on_done=lambda ruta: QTimer.singleShot(
                0, lambda: self._pdf_ok(ruta)),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda: self._pdf_error(msg)),
        )

    def _pdf_ok(self, ruta: str):
        self._btn_pdf.setText("⬇ Exportar PDF")
        self._btn_pdf.setEnabled(True)
        NMToast.show(self.window(), f"PDF guardado en Downloads.", variant="success")

    def _pdf_error(self, msg: str):
        self._btn_pdf.setText("⬇ Exportar PDF")
        self._btn_pdf.setEnabled(True)
        NMToast.show(self.window(), f"Error PDF: {msg[:60]}", variant="error")


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
        self._entry_rec_hora.setFixedWidth(90)
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
            NMToast.show(self.window(),
                         f"Tarea '{tarea[:30]}' asignada.", variant="success")
        except Exception as e:
            NMToast.show(self.window(), str(e)[:80], variant="error")

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
            NMToast.show(self.window(), "Recordatorio enviado.", variant="success")
        except Exception as e:
            NMToast.show(self.window(), str(e)[:80], variant="error")


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
        self._list_scroll.setStyleSheet("background: transparent; border: none;")
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
            NMToast.show(self.window(), f"'{nombre}' añadida al banco.", variant="success")
        except Exception as e:
            NMToast.show(self.window(), str(e)[:80], variant="error")

    def _cargar_banco(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
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
            row_f.setFixedHeight(44)
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

            btn_del = QLabel("✕")
            btn_del.setFont(qfont("size_caption"))
            btn_del.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            rid = r["id"]
            btn_del.mousePressEvent = lambda _, _rid=rid: self._eliminar(int(_rid))
            rl.addWidget(btn_del)
            self._list_layout.addWidget(row_f)

    def _eliminar(self, rid: int):
        if not self._sb:
            return
        try:
            self._sb.table("activity_bank").delete().eq("id", rid).execute()
            self._cargar_banco()
        except Exception as e:
            NMToast.show(self.window(), str(e)[:80], variant="error")

    def _ia_completar(self):
        nombre = self._ent_nombre.text().strip()
        if not nombre:
            return
        self._ent_desc.setText("Generando con IA…")
        from hub.ia_asistente import autocompletar_actividad
        autocompletar_actividad(
            nombre,
            on_result=lambda txt: QTimer.singleShot(0, lambda: self._ia_ok(txt)),
            on_error=lambda msg: QTimer.singleShot(0, lambda: self._ia_err(msg)),
        )

    def _ia_ok(self, txt: str):
        self._ent_desc.setText(txt)

    def _ia_err(self, msg: str):
        self._ent_desc.clear()
        NMToast.show(self.window(), f"IA no disponible: {msg[:60]}", variant="error")


# ── Tab: IA ───────────────────────────────────────────────────────────────────

class _TabIA(QWidget):
    def __init__(self, modo: str, sb, pid: str, nombre: str,
                 datos_cache_ref: dict, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._datos_ref = datos_cache_ref
        self._setup()

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
        self._txt_resumen.setFixedHeight(90)
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
        datos = self._datos_ref.get("_datos_cache", {})
        if not datos:
            NMToast.show(self.window(),
                         "Cargá los datos del paciente primero (Tab Registros).",
                         variant="info")
            return
        self._btn_resumen.setText("Generando…")
        self._btn_resumen.setEnabled(False)
        self._txt_resumen.setPlainText("Consultando IA…")
        from hub.ia_asistente import resumir_evolucion
        resumir_evolucion(
            datos, self._nombre,
            on_result=lambda txt: QTimer.singleShot(
                0, lambda: self._resumen_ok(txt)),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda: self._resumen_err(msg)),
        )

    def _resumen_ok(self, txt: str):
        self._btn_resumen.setText("Generar resumen")
        self._btn_resumen.setEnabled(True)
        self._txt_resumen.setPlainText(txt)

    def _resumen_err(self, msg: str):
        self._btn_resumen.setText("Generar resumen")
        self._btn_resumen.setEnabled(True)
        self._txt_resumen.setPlainText(f"Error: {msg}")

    def _generar_sugerencias(self):
        datos = self._datos_ref.get("_datos_cache", {})
        if not datos:
            NMToast.show(self.window(),
                         "Cargá los datos del paciente primero.",
                         variant="info")
            return
        self._btn_sugerencias.setText("Generando…")
        self._btn_sugerencias.setEnabled(False)
        from hub.ia_asistente import sugerir_acciones
        sugerir_acciones(
            datos, self._nombre,
            on_result=lambda txt: QTimer.singleShot(
                0, lambda: self._sugerencias_ok(txt)),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda: self._sugerencias_err(msg)),
        )

    def _sugerencias_ok(self, txt: str):
        self._btn_sugerencias.setText("Generar sugerencias")
        self._btn_sugerencias.setEnabled(True)
        c = colors(self._modo)
        while self._sug_layout.count():
            item = self._sug_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
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
        NMToast.show(self.window(), f"IA: {msg[:60]}", variant="error")

    def _generar_tarea(self):
        ctx = self._ent_ctx.text().strip()
        if not ctx:
            return
        self._lbl_tarea_gen.setText("Generando…")
        from hub.ia_asistente import generar_tarea
        generar_tarea(
            ctx,
            on_result=lambda txt: QTimer.singleShot(
                0, lambda: self._lbl_tarea_gen.setText(txt)),
            on_error=lambda msg: QTimer.singleShot(
                0, lambda: self._lbl_tarea_gen.setText(f"Error: {msg[:60]}")),
        )


# ── DetallePacienteView ───────────────────────────────────────────────────────

class DetallePacienteView(QWidget):
    """Panel completo de detalle de paciente con QTabWidget como pills."""

    back_requested = pyqtSignal()

    def __init__(self, modo: str, sb, paciente_id: str, paciente_nombre: str,
                 parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = paciente_id
        self._nombre = paciente_nombre
        # Referencia compartida de datos para que IA los lea
        self._datos_ref: dict = {}
        self._setup()

    def _setup(self):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Título
        top = QWidget()
        top.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(PAD_CONTAINER, 12, PAD_CONTAINER, 8)
        t = QLabel(f"📋  {self._nombre}")
        t.setFont(qfont("size_h3", bold=True))
        t.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        tl.addWidget(t)
        layout.addWidget(top)

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

        # Compartir datos_cache entre Registros e IA
        self._tab_reg._datos_cache = self._datos_ref
        # Monkey-patch para que al cargar datos en Registros, IA los vea
        orig_mostrar = self._tab_reg._mostrar_registros
        def _patched_mostrar(datos: dict):
            self._datos_ref["_datos_cache"] = datos
            orig_mostrar(datos)
        self._tab_reg._mostrar_registros = _patched_mostrar

        self._tabs.addTab(self._tab_reg,   "Registros")
        self._tabs.addTab(self._tab_asig,  "Asignar")
        self._tabs.addTab(self._tab_banco, "Banco")
        self._tabs.addTab(self._tab_ia,    "IA")

        layout.addWidget(self._tabs)
