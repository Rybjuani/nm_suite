"""
app/modules/actividades_qt.py — Activación conductual v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Actividades):

  Header          eyebrow + NMMoodContextHeader (banner mood actual)
  Categorías      _CategoriesCard con 6 mini-rings (NMIcon dentro), filtro live
  Sugeridas       Row 3 _SuggestedCard (NMCard glow + icono grande + badge cat +
                  intensidad dots + botones Hice / No pude)
  Otras opciones  _ActivityRow tabla con NMIcon + nombre + chip cat + rango
                  ánimo + intensidad + NMPlayButton

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  _FALLBACK_ACTIVIDADES, _get_last_mood(), _get_activities(),
  _register_result() (INSERT INTO activacion), get_card_status(), on_enter,
  visual_qa fixtures (activity_suggestions, last_mood).
"""

import os
import sys
import logging
import math

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMCard, NMIcon, NMPlayButton, NMModuleRing,
        NMMoodContextHeader, NMEmptyState, NMSegmentedChoice,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        interpolate_color, v3c, v3_mode, V3_SP, V3_RD,
        stylesheet_scrollarea, PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY, CATEGORY_COLORS, V3_GRADIENTS
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import (
        visual_qa_enabled, last_mood as qa_last_mood, activity_suggestions,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMCard, NMIcon, NMPlayButton, NMModuleRing,
        NMMoodContextHeader, NMEmptyState, NMSegmentedChoice,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        interpolate_color, v3c, v3_mode, V3_SP, V3_RD,
        stylesheet_scrollarea, PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY, CATEGORY_COLORS, V3_GRADIENTS
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import (
        visual_qa_enabled, last_mood as qa_last_mood, activity_suggestions,
    )


# ── Fallback activities (preservado exacto) ──────────────────────────────────

_FALLBACK_ACTIVIDADES = [
    {"nombre": "Caminata corta",    "descripcion": "Salí 10 minutos a caminar sin destino fijo.",          "categoria": "Física"},
    {"nombre": "Escuchar música",   "descripcion": "Elegí una canción que te guste y escuchala con atención.", "categoria": "Placer"},
    {"nombre": "Orden breve",       "descripcion": "Ordená un cajón o superficie pequeña.",                 "categoria": "Maestría"},
    {"nombre": "Respiración",       "descripcion": "3 minutos de respiración consciente.",                  "categoria": "Autocuidado"},
    {"nombre": "Contacto social",   "descripcion": "Mandá un mensaje breve a alguien.",                     "categoria": "Social"},
    {"nombre": "Hidratación",       "descripcion": "Tomá un vaso de agua.",                                 "categoria": "Autocuidado"},
]


# ── Categorías y mapeo de iconos SVG ────────────────────────────────────────

# 6 categorías canónicas (CATEGORY_COLORS) con icono SVG
_CATEGORY_ORDER = [
    ("Autocuidado", "heart"),
    ("Física",      "run"),
    ("Cognitiva",   "brain"),
    ("Placer",      "spark"),
    ("Social",      "users"),
    ("Maestría",    "trophy"),
]


def _intensity_for(name: str) -> int:
    """Asigna intensidad determinística 1-3 según hash del nombre."""
    return (abs(hash(name)) % 3) + 1


# ── _CategoryRingTile ────────────────────────────────────────────────────────

class _CategoryRingTile(QWidget):
    """Mini-ring con icono dentro + label debajo + count.

    Clickeable: emite ``clicked(category)`` con el nombre canónico.
    """

    clicked = pyqtSignal(str)

    def __init__(self, category: str, icon_name: str,
                 count: int = 0, total: int = 0,
                 modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._category = category
        self._icon_name = icon_name
        self._count = count
        self._total = max(total, 1)
        self._modo = norm_modo(modo)
        self._selected = False
        self._hover = False
        self.setFixedSize(96, 110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_selected(self, selected: bool):
        if selected != self._selected:
            self._selected = selected
            self.update()

    def category(self) -> str:
        return self._category

    def set_count(self, count: int, total: int):
        self._count = count
        self._total = max(total, 1)
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit(self._category)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Ring
        ring_size = 64
        cx = self.width() / 2
        cy = 36
        pen_w = 5
        r = ring_size / 2 - pen_w
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)

        # Track
        p.setPen(QPen(v3c("borderSoft", self._modo), pen_w,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Progreso (con gradient firma) — proporcional al count/total
        pct = min(self._count / self._total, 1.0)
        if pct > 0.001:
            stops = V3_GRADIENTS[v3_mode(self._modo)]
            segs = 32
            for i in range(segs):
                seg_frac = i / segs
                if seg_frac >= pct:
                    break
                color = self._interp_stops(stops, (seg_frac + 1 / segs / 2))
                pen = QPen(color, pen_w, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.FlatCap)
                p.setPen(pen)
                a0 = 90 - seg_frac * 360
                seg_span_deg = (1 / segs) * 360
                if seg_frac + 1 / segs > pct:
                    seg_span_deg *= (pct - seg_frac) * segs
                p.drawArc(rect, int(a0 * 16), int(-seg_span_deg * 16))

        # Hover/selected ring outer glow
        if self._selected or self._hover:
            cat_color = QColor(CATEGORY_COLORS.get(self._category,
                                                   v3c("teal", self._modo).name()))
            cat_color.setAlpha(110 if self._selected else 70)
            p.setPen(QPen(cat_color, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r + 4, r + 4)

        # Label debajo
        p.setPen(QPen(v3c("text" if self._selected else "text2",
                          self._modo)))
        p.setFont(qfont("size_caption",
                         weight=TYPOGRAPHY["weight_semibold"]
                         if self._selected else TYPOGRAPHY["weight_medium"]))
        text_rect = QRectF(0, 78, self.width(), 16)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._category)

        # Count debajo del label
        p.setPen(QPen(v3c("text3", self._modo)))
        p.setFont(qfont_mono(9, bold=False))
        count_rect = QRectF(0, 94, self.width(), 14)
        p.drawText(count_rect, Qt.AlignmentFlag.AlignCenter,
                   f"{self._count} activ.")
        p.end()

    def _interp_stops(self, stops, t):
        t = max(0.0, min(1.0, t))
        for i in range(len(stops) - 1):
            h0, t0 = stops[i]
            h1, t1 = stops[i + 1]
            if t0 <= t <= t1:
                local = (t - t0) / max(1e-9, t1 - t0)
                return QColor(interpolate_color(h0, h1, local))
        return QColor(stops[-1][0])

    # NMIcon no se puede pintar bien dentro del paintEvent (es un QLabel).
    # Lo dibujamos como pixmap manualmente:
    def showEvent(self, event):
        super().showEvent(event)
        # Render icon como pixmap y guardarlo para drawPixmap en paintEvent.
        # (Ya está manejado: dibujamos el icono via NMIcon como child overlay)
        if not hasattr(self, "_icon_widget"):
            try:
                self._icon_widget = NMIcon(
                    self._icon_name, size=22,
                    color=v3c("teal", self._modo).name(),
                    modo=self._modo, parent=self)
                self._icon_widget.move(
                    int((self.width() - 22) / 2),
                    int(36 - 22 / 2))
                self._icon_widget.show()
            except Exception:
                pass


# ── _CategoriesCard ─────────────────────────────────────────────────────────

class _CategoriesCard(NMCard):
    """Card v3 con 6 mini-rings de categorías (filtro live)."""

    category_changed = pyqtSignal(str)   # "" = sin filtro

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._tiles: list[_CategoryRingTile] = []
        self._selected_cat: str = ""
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["sm"])

        self._eyebrow = QLabel("CATEGORÍAS")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)

        row = QHBoxLayout()
        row.setSpacing(V3_SP["sm"])
        row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        for cat, icon_name in _CATEGORY_ORDER:
            tile = _CategoryRingTile(cat, icon_name,
                                      count=0, total=1, modo=self._modo)
            tile.clicked.connect(self._on_tile_clicked)
            row.addWidget(tile)
            self._tiles.append(tile)
        lay.addLayout(row)
        self._apply_cat_styles()

    def update_counts(self, all_activities: list[dict]):
        """Cuenta por categoría a partir de la lista completa de actividades."""
        total = max(len(all_activities), 1)
        per_cat = {cat: 0 for cat, _ in _CATEGORY_ORDER}
        for act in all_activities:
            cat = act.get("categoria", "Autocuidado")
            if cat in per_cat:
                per_cat[cat] += 1
        for tile in self._tiles:
            tile.set_count(per_cat.get(tile.category(), 0), total)

    def _on_tile_clicked(self, cat: str):
        # Toggle: si ya estaba seleccionado, deseleccionar (limpiar filtro)
        if self._selected_cat == cat:
            self._selected_cat = ""
        else:
            self._selected_cat = cat
        for tile in self._tiles:
            tile.set_selected(tile.category() == self._selected_cat)
        self.category_changed.emit(self._selected_cat)

    def selected_category(self) -> str:
        return self._selected_cat

    def _apply_cat_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        for tile in self._tiles:
            tile._modo = self._modo
            if hasattr(tile, "_icon_widget"):
                tile._icon_widget._modo = self._modo
                tile._icon_widget._render()
            tile.update()
        self._apply_cat_styles()


# ── _IntensityDots ───────────────────────────────────────────────────────────

class _IntensityDots(QWidget):
    """3 dots — los primeros N (1-3) coloreados con accent, resto borderSoft."""

    def __init__(self, level: int = 2, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._level = max(0, min(3, level))
        self._modo = norm_modo(modo)
        self.setFixedSize(36, 12)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_level(self, level: int):
        self._level = max(0, min(3, level))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        on_color = v3c("teal", self._modo)
        off_color = v3c("borderSoft", self._modo)
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(3):
            cx = 4 + i * 12
            cy = 6
            p.setBrush(QBrush(on_color if i < self._level else off_color))
            p.drawEllipse(QPointF(cx, cy), 3, 3)
        p.end()


# ── _SuggestedCard (3 en row) ───────────────────────────────────────────────

class _SuggestedCard(NMCard):
    """Card sugerida v3 — NMIcon grande + título + chip cat + intensidad + botones."""

    completed = pyqtSignal(str)   # nombre
    skipped = pyqtSignal(str)

    def __init__(self, act: dict, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=True)
        self._act = dict(act)
        self._nombre = self._act.get("nombre", "Actividad")
        self._categoria = self._act.get("categoria", "Autocuidado")
        self._descripcion = self._act.get("descripcion", "")
        self._completed_flag = False
        # Halo color por categoría
        self.set_accent(CATEGORY_COLORS.get(
            self._categoria, v3c("teal", self._modo).name()))
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["sm"])

        # Top: icono grande + chip cat
        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        icon_name = dict(_CATEGORY_ORDER).get(self._categoria, "spark")
        self._icon = NMIcon(icon_name, size=36,
                             color=CATEGORY_COLORS.get(
                                 self._categoria,
                                 v3c("teal", self._modo).name()),
                             modo=self._modo)
        top.addWidget(self._icon)
        top.addStretch()
        self._chip = QLabel(self._categoria)
        self._chip.setFont(qfont("size_caption_xs",
                                  weight=TYPOGRAPHY["weight_semibold"]))
        self._chip.setContentsMargins(8, 2, 8, 2)
        top.addWidget(self._chip)
        lay.addLayout(top)

        # Título + descripción
        self._title_lbl = QLabel(self._nombre)
        self._title_lbl.setFont(qfont("size_h3",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        self._title_lbl.setWordWrap(True)
        lay.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(self._descripcion)
        self._desc_lbl.setFont(qfont("size_caption"))
        self._desc_lbl.setWordWrap(True)
        lay.addWidget(self._desc_lbl)

        lay.addStretch()

        # Footer: intensidad dots + botones
        footer = QHBoxLayout()
        footer.setSpacing(V3_SP["sm"])
        self._intensity = _IntensityDots(_intensity_for(self._nombre),
                                          modo=self._modo)
        footer.addWidget(self._intensity)
        footer.addStretch()
        self._btn_no = NMButton("No pude", variant="ghost", size="sm",
                                 modo=self._modo, width=90)
        self._btn_no.clicked.connect(lambda: self.skipped.emit(self._nombre))
        footer.addWidget(self._btn_no)
        self._btn_yes = NMButton("Hice esto", variant="gradient",
                                  size="sm", modo=self._modo, width=110)
        self._btn_yes.clicked.connect(lambda: self.completed.emit(self._nombre))
        footer.addWidget(self._btn_yes)
        lay.addLayout(footer)

        self._apply_sug_styles()

    def set_completed(self, completed: bool):
        self._completed_flag = bool(completed)
        if completed:
            self._btn_yes.setEnabled(False)
            self._btn_no.setEnabled(False)
            self._title_lbl.setText("✓ " + self._nombre)

    def set_done(self, resultado: str):
        """Alias del API existente para activity cards."""
        self.set_completed(resultado == "hecha")

    def _apply_sug_styles(self):
        cat_color = CATEGORY_COLORS.get(
            self._categoria, v3c("teal", self._modo).name())
        qc = QColor(cat_color)
        bg_rgba = f"rgba({qc.red()},{qc.green()},{qc.blue()},36)"
        self._chip.setStyleSheet(
            f"color: {cat_color}; background: {bg_rgba}; "
            f"border-radius: 8px;")
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._intensity._modo = self._modo
        self._intensity.update()
        self._apply_sug_styles()


# ── _ActivityRow ────────────────────────────────────────────────────────────

class _ActivityRow(QWidget):
    """Fila de tabla "Otras opciones": icono + nombre + cat chip + rango + dots + play."""

    play_clicked = pyqtSignal(str)   # nombre

    def __init__(self, act: dict, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._act = act
        self._nombre = act.get("nombre", "Actividad")
        self._categoria = act.get("categoria", "Autocuidado")
        self._animo_min = act.get("animo_min")
        self._animo_max = act.get("animo_max")
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["sm"], V3_SP["xs"] + 2,
                                V3_SP["sm"], V3_SP["xs"] + 2)
        lay.setSpacing(V3_SP["sm"])

        icon_name = dict(_CATEGORY_ORDER).get(self._categoria, "spark")
        self._icon = NMIcon(icon_name, size=20,
                             color=CATEGORY_COLORS.get(
                                 self._categoria,
                                 v3c("teal", self._modo).name()),
                             modo=self._modo)
        lay.addWidget(self._icon)

        self._name_lbl = QLabel(self._nombre)
        self._name_lbl.setFont(qfont("size_small"))
        lay.addWidget(self._name_lbl, stretch=1)

        # Chip categoría
        self._cat_lbl = QLabel(self._categoria)
        self._cat_lbl.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        self._cat_lbl.setContentsMargins(8, 2, 8, 2)
        lay.addWidget(self._cat_lbl)

        # Rango ánimo
        if self._animo_min is not None and self._animo_max is not None:
            rango_txt = f"{self._animo_min}–{self._animo_max}"
        else:
            rango_txt = "1–10"
        self._rango_lbl = QLabel(rango_txt)
        self._rango_lbl.setFont(qfont_mono(10, bold=False))
        self._rango_lbl.setFixedWidth(50)
        lay.addWidget(self._rango_lbl)

        # Intensidad
        self._intensity = _IntensityDots(_intensity_for(self._nombre),
                                          modo=self._modo)
        lay.addWidget(self._intensity)

        # Play button
        self._play = NMPlayButton(icon_name="play", size="sm",
                                    modo=self._modo)
        self._play.clicked.connect(lambda: self.play_clicked.emit(self._nombre))
        lay.addWidget(self._play)

        self._apply_row_styles()

    def _apply_row_styles(self):
        cat_color = CATEGORY_COLORS.get(
            self._categoria, v3c("teal", self._modo).name())
        qc = QColor(cat_color)
        bg_rgba = f"rgba({qc.red()},{qc.green()},{qc.blue()},36)"
        self._cat_lbl.setStyleSheet(
            f"color: {cat_color}; background: {bg_rgba}; border-radius: 8px;")
        self._name_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        self._rango_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")


# ── ModuloActividades v3 ────────────────────────────────────────────────────

class ModuloActividades(NMModule):
    MODULE_TITLE = "Actividades"
    MODULE_ICON  = "actividades"

    def build_ui(self):
        self._all_activities: list[dict] = []
        self._current_filter: str = ""
        self._suggested_cards: list[_SuggestedCard] = []
        self._row_widgets: list[_ActivityRow] = []

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(self._scroll)

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll.setWidget(self._scroll_content)

        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                                 V3_SP["xl"], V3_SP["xl"])
        self._scroll_layout.setSpacing(V3_SP["lg"])
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._load_suggestions()

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self.update()

    # ── load ──────────────────────────────────────────────────────────────────

    def _load_suggestions(self):
        # Clear scroll
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                self._scroll_layout.removeWidget(w)
                w.setParent(None)
                w.deleteLater()

        self._all_activities = []
        self._suggested_cards = []
        self._row_widgets = []

        # 1. Eyebrow
        self._eyebrow = QLabel("ACTIVIDADES")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._scroll_layout.addWidget(self._eyebrow)

        # 2. Mood context header
        animo = self._get_last_mood()
        if animo is None:
            self._scroll_layout.addWidget(NMEmptyState(
                "fa5s.running",
                "Sin sugerencias",
                "Registrá tu ánimo primero para recibir sugerencias.",
            ))
            return

        self._mood_header = NMMoodContextHeader(score=animo, modo=self._modo)
        self._scroll_layout.addWidget(self._mood_header)

        # 3. Load activities
        self._all_activities = self._get_activities(animo)
        if not self._all_activities:
            self._scroll_layout.addWidget(NMEmptyState(
                "fa5s.running",
                "Sin sugerencias",
                "Tu terapeuta aún no ha cargado actividades para este ánimo.",
            ))
            return

        # 4. Categories card
        self._categories = _CategoriesCard(modo=self._modo)
        self._categories.update_counts(self._all_activities)
        self._categories.category_changed.connect(self._on_category_filter)
        self._scroll_layout.addWidget(self._categories)

        # 5. Sugeridas section (3 cards)
        self._sug_title = QLabel("SUGERIDAS PARA VOS")
        self._sug_title.setFont(qfont("size_caption_xs",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        self._sug_title.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._scroll_layout.addWidget(self._sug_title)

        self._sug_row_widget = QWidget()
        self._sug_row_widget.setStyleSheet("background: transparent;")
        self._sug_row = QHBoxLayout(self._sug_row_widget)
        self._sug_row.setContentsMargins(0, 0, 0, 0)
        self._sug_row.setSpacing(V3_SP["md"])
        self._scroll_layout.addWidget(self._sug_row_widget)

        # 6. Otras opciones tabla
        self._otras_title = QLabel("OTRAS OPCIONES")
        self._otras_title.setFont(qfont("size_caption_xs",
                                         weight=TYPOGRAPHY["weight_semibold"]))
        self._otras_title.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._otras_title.setContentsMargins(0, V3_SP["sm"], 0, 0)
        self._scroll_layout.addWidget(self._otras_title)

        self._otras_card = NMCard(modo=self._modo, clickable=False)
        self._otras_lay = QVBoxLayout(self._otras_card)
        self._otras_lay.setContentsMargins(V3_SP["md"], V3_SP["sm"],
                                            V3_SP["md"], V3_SP["sm"])
        self._otras_lay.setSpacing(2)
        self._scroll_layout.addWidget(self._otras_card)

        # 7. Footer count label
        self._footer_lbl = QLabel("")
        self._footer_lbl.setFont(qfont("size_caption"))
        self._footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._scroll_layout.addWidget(self._footer_lbl)

        self._rebuild_lists("")

    def _on_category_filter(self, cat: str):
        self._current_filter = cat
        self._rebuild_lists(cat)

    def _rebuild_lists(self, cat: str):
        # Clear suggested row
        while self._sug_row.count():
            item = self._sug_row.takeAt(0)
            w = item.widget()
            if w:
                self._sug_row.removeWidget(w)
                w.deleteLater()
        # Clear otras
        while self._otras_lay.count():
            item = self._otras_lay.takeAt(0)
            w = item.widget()
            if w:
                self._otras_lay.removeWidget(w)
                w.deleteLater()

        activities = self._all_activities
        if cat:
            activities = [a for a in activities if a.get("categoria", "") == cat]

        if not activities:
            empty = QLabel(f"No hay actividades en \"{cat}\".")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sug_row.addWidget(empty)
            self._footer_lbl.setText("")
            return

        # 3 sugeridas (primeras 3)
        suggested = activities[:3]
        for act in suggested:
            card = _SuggestedCard(act, modo=self._modo)
            card.completed.connect(
                lambda n, cd=card: self._register_result(n, "hecha", cd, None))
            card.skipped.connect(
                lambda n, cd=card: self._register_result(n, "no_pude", cd, None))
            if visual_qa_enabled() and act.get("done"):
                card.set_done("hecha")
            self._sug_row.addWidget(card, stretch=1)
            self._suggested_cards.append(card)
        # Stretch fill si menos de 3
        for _ in range(3 - len(suggested)):
            self._sug_row.addStretch(1)

        # Otras opciones (resto)
        others = activities[3:]
        if not others:
            empty = QLabel("Sin opciones adicionales.")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._otras_lay.addWidget(empty)
        else:
            for i, act in enumerate(others):
                row = _ActivityRow(act, modo=self._modo)
                row.play_clicked.connect(
                    lambda n, r=row: self._register_result(n, "hecha", r, None))
                self._otras_lay.addWidget(row)
                self._row_widgets.append(row)
                # Separador
                if i < len(others) - 1:
                    sep = QFrame()
                    sep.setFrameShape(QFrame.Shape.HLine)
                    sep.setFixedHeight(1)
                    sep.setStyleSheet(
                        f"background-color: {v3c('borderSoft', self._modo).name()};")
                    self._otras_lay.addWidget(sep)

        n = len(activities)
        self._footer_lbl.setText(
            f"{n} actividad{'es' if n != 1 else ''} sugerida{'s' if n != 1 else ''}")

    # ── _register_result (lógica preservada exacta) ──────────────────────────

    def _register_result(self, nombre: str, resultado: str, card_widget,
                         seg: NMSegmentedChoice | None):
        animo = self._get_last_mood()
        if visual_qa_enabled():
            if hasattr(card_widget, "set_done"):
                try:
                    card_widget.set_done(resultado)
                except Exception:
                    pass
            return
        if animo is None:
            NMToast.display(
                self.window(),
                "Registrá tu ánimo primero para asociar esta actividad a tu estado actual.",
                variant="info", duration_ms=3000)
            return

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), animo, animo, nombre, resultado),
            )
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Operation failed")

        if hasattr(card_widget, "set_accent"):
            color_map = {
                "hecha":   v3c("success", self._modo).name(),
                "no_pude": v3c("danger", self._modo).name(),
            }
            card_widget.set_accent(color_map.get(
                resultado, v3c("teal", self._modo).name()))
        if hasattr(card_widget, "play_success"):
            card_widget.play_success()
        if hasattr(card_widget, "set_completed") and resultado == "hecha":
            card_widget.set_completed(True)

        labels = {"hecha": "Hecha", "no_pude": "No se pudo"}
        NMToast.display(
            self.window(),
            f"Actividad \"{nombre}\": {labels.get(resultado, resultado)}",
            variant="success" if resultado == "hecha" else "info",
            duration_ms=2000)

    # ── Data access (lógica preservada) ─────────────────────────────────────

    def _get_last_mood(self):
        if visual_qa_enabled():
            return qa_last_mood()
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro "
                "WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                return row[0] if isinstance(row, tuple) else row["puntaje"]
        except Exception:
            _log.exception("Operation failed")
        return None

    def _get_activities(self, animo: int) -> list:
        if visual_qa_enabled():
            return activity_suggestions()
        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT nombre, descripcion, categoria, animo_min, animo_max "
                "FROM activacion_actividades "
                "WHERE activa = 1 AND animo_min <= ? AND animo_max >= ? "
                "ORDER BY RANDOM() LIMIT 12",
                (animo, animo),
            ).fetchall()
            conn.close()
            if rows:
                return [dict(r) for r in rows]
        except Exception:
            _log.exception("Operation failed")

        # Fallback heurístico (preservado)
        if animo <= 3:
            pool = [a for a in _FALLBACK_ACTIVIDADES if a["categoria"] in ("Autocuidado", "Placer")]
        elif animo <= 6:
            pool = _FALLBACK_ACTIVIDADES[:]
        else:
            pool = [a for a in _FALLBACK_ACTIVIDADES if a["categoria"] in ("Física", "Maestría", "Social")]
        if not pool:
            pool = _FALLBACK_ACTIVIDADES
        return pool[:]

    # ── Hooks ────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._load_suggestions()

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "5 actividades"
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM activacion WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} actividad{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
