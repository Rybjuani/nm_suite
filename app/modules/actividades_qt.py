"""
app/modules/actividades_qt.py — Activación conductual v3 (PyQt6)

Estructura actual (Suite > Actividades):

  Categorías      _CategoriesCard con mini-rings y filtro live
  Actividades     Grid unificado de _SuggestedCard con botones Hice / No pude

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  _get_last_mood(), _get_activities(),
  _register_result() (INSERT INTO activacion), get_card_status(), on_enter,
  visual_qa fixtures (activity_suggestions, last_mood).
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QGridLayout,
    QScrollArea,
)

try:
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        NMCard,
        NMIcon,
        NMEmptyState,
        NMSegmentedChoice,
        NMTabs,
        NMSectionHeader,
        NMPageHeader,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        qfont_mono,
        interpolate_color,
        v3c,
        v3_mode,
        V3_SP,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY, V3_GRADIENTS
    from shared.db import obtener_conexion, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import (
        visual_qa_enabled,
        last_mood as qa_last_mood,
        activity_suggestions,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        NMCard,
        NMIcon,
        NMEmptyState,
        NMSegmentedChoice,
        NMTabs,
        NMSectionHeader,
        NMPageHeader,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        qfont_mono,
        interpolate_color,
        v3c,
        v3_mode,
        V3_SP,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY, V3_GRADIENTS
    from shared.db import obtener_conexion, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import (
        visual_qa_enabled,
        last_mood as qa_last_mood,
        activity_suggestions,
    )
from shared.remote_config import t




# ── Categorías y mapeo de iconos SVG ────────────────────────────────────────

# 6 categorías canónicas (CATEGORY_COLORS) con icono SVG
_CATEGORY_ORDER = [
    ("Autocuidado", "heart"),
    ("Física", "run"),
    ("Cognitiva", "brain"),
    ("Placer", "spark"),
    ("Social", "users"),
    ("Maestría", "trophy"),
]

_CATEGORY_TEXT_KEYS = {
    "Autocuidado": "text.module.actividades.category_autocuidado",
    "Física": "text.module.actividades.category_fisica",
    "Cognitiva": "text.module.actividades.category_cognitiva",
    "Placer": "text.module.actividades.category_placer",
    "Social": "text.module.actividades.category_social",
    "Maestría": "text.module.actividades.category_maestria",
}


def _category_label(cat: str) -> str:
    canon = _cat_canon(cat)
    key = _CATEGORY_TEXT_KEYS.get(canon)
    return t(key, canon) if key else canon


def _intensity_for(name: str) -> int:
    """Asigna intensidad determinística 1-3 según hash del nombre."""
    return (abs(hash(name)) % 3) + 1


def _cat_canon(cat: str) -> str:
    """Normaliza variantes sin tilde guardadas en datos viejos.

    Sin esto, una actividad con categoria "Fisica" mostraba el badge sin
    tilde, caía al icono fallback (el dict canónico solo tiene "Física") y
    NO matcheaba el filtro de categoría."""
    return {"Fisica": "Física", "Maestria": "Maestría"}.get(cat, cat)


def _cat_color(cat: str, modo: str) -> str:
    cmap = {
        "Física": "warning",
        "Placer": "accent",
        "Maestría": "violet",
        "Social": "cyan",
        "Autocuidado": "success",
        "Cognitiva": "accent",
    }
    return v3c(cmap.get(_cat_canon(cat), "teal"), modo).name()


# ── _CategoryRingTile ────────────────────────────────────────────────────────


class _CategoryRingTile(QWidget):
    """Mini-ring con icono dentro + label debajo + count.

    Clickeable: emite ``clicked(category)`` con el nombre canónico.
    """

    clicked = pyqtSignal(str)

    def __init__(
        self,
        category: str,
        icon_name: str,
        count: int = 0,
        total: int = 0,
        modo: str = "dark_hybrid",
        parent=None,
    ):
        super().__init__(parent)
        self._category = category
        self._icon_name = icon_name
        self._count = count
        self._total = max(total, 1)
        self._modo = norm_modo(modo)
        self._selected = False
        self._hover = False
        self.setFixedSize(96, 116)
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
        p.setPen(
            QPen(
                v3c("borderSoft", self._modo), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap
            )
        )
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
                pen = QPen(color, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
                p.setPen(pen)
                a0 = 90 - seg_frac * 360
                seg_span_deg = (1 / segs) * 360
                if seg_frac + 1 / segs > pct:
                    seg_span_deg *= (pct - seg_frac) * segs
                p.drawArc(rect, int(a0 * 16), int(-seg_span_deg * 16))

        # Hover/selected ring outer glow
        if self._selected or self._hover:
            cat_color = QColor(_cat_color(self._category, self._modo))
            cat_color.setAlpha(110 if self._selected else 70)
            p.setPen(QPen(cat_color, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r + 4, r + 4)

        # Label debajo
        p.setPen(QPen(v3c("text" if self._selected else "text2", self._modo)))
        p.setFont(
            qfont(
                "size_caption",
                weight=TYPOGRAPHY["weight_semibold"]
                if self._selected
                else TYPOGRAPHY["weight_medium"],
            )
        )
        text_rect = QRectF(0, 80, self.width(), 16)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, _category_label(self._category))

        # Count debajo del label
        p.setPen(QPen(v3c("ink_secondary", self._modo)))
        p.setFont(qfont_mono(9, bold=False))
        count_rect = QRectF(0, 98, self.width(), 14)
        p.drawText(count_rect, Qt.AlignmentFlag.AlignCenter, f"{self._count} activ.")
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
                    self._icon_name,
                    size=22,
                    color=_cat_color(self._category, self._modo),
                    modo=self._modo,
                    parent=self,
                )
                self._icon_widget.move(int((self.width() - 22) / 2), int(36 - 22 / 2))
                self._icon_widget.show()
            except Exception:
                pass


# ── _CategoriesCard ─────────────────────────────────────────────────────────


class _CategoriesCard(NMCard):
    """Card v3 con 6 mini-rings de categorías (filtro live)."""

    category_changed = pyqtSignal(str)  # "" = sin filtro

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._tiles: list[_CategoryRingTile] = []
        self._selected_cat: str = ""
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["md"])

        self._eyebrow = QLabel(t("text.module.actividades.categories_eyebrow", "Categorías"))
        self._eyebrow.setFont(eyebrow_font())
        lay.addWidget(self._eyebrow)

        row = QHBoxLayout()
        row.setSpacing(V3_SP["lg"])
        row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        for cat, icon_name in _CATEGORY_ORDER:
            tile = _CategoryRingTile(cat, icon_name, count=0, total=1, modo=self._modo)
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
            cat = _cat_canon(act.get("categoria", "Autocuidado"))
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
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"background: transparent;"
        )

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
        self.setFixedSize(48, 16)
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
            cx = 8 + i * 16
            cy = 8
            p.setBrush(QBrush(on_color if i < self._level else off_color))
            p.drawEllipse(QPointF(cx, cy), 4, 4)
        p.end()


# ── _SuggestedCard (3 en row) ───────────────────────────────────────────────


class _SuggestedCard(NMCard):
    """Card sugerida v3 — NMIcon grande + título + chip cat + intensidad + botones."""

    completed = pyqtSignal(str)  # nombre
    skipped = pyqtSignal(str)

    def __init__(self, act: dict, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._act = dict(act)
        self._nombre = self._act.get("nombre", "Actividad")
        self._categoria = _cat_canon(self._act.get("categoria", "Autocuidado"))
        self._descripcion = self._act.get("descripcion", "")
        self._completed_flag = False
        # Mínimo sin tope rígido (auditoría v1.0): título y descripción vienen
        # del Hub con wordwrap; el MaximumHeight=176 anterior recortaba texto
        # con descripciones de 3+ líneas. Vertical FIXED = exactamente su
        # sizeHint: crece con el contenido pero el layout NO la estira a
        # llenar el alto libre (quedaban cards gigantes vacías).
        self.setMinimumSize(208, 176)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Halo color por categoría
        self.set_accent(_cat_color(self._categoria, self._modo))
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Top: icono grande + chip cat
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(4)
        icon_name = dict(_CATEGORY_ORDER).get(self._categoria, "spark")
        self._icon = NMIcon(
            icon_name, size=18, color=_cat_color(self._categoria, self._modo), modo=self._modo
        )
        top.addWidget(self._icon)
        top.addStretch()
        self._chip = QLabel(_category_label(self._categoria))
        self._chip.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._chip.setContentsMargins(6, 1, 6, 1)
        top.addWidget(self._chip)
        lay.addLayout(top)

        # Título + descripción
        self._title_lbl = QLabel(self._nombre)
        self._title_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        lay.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(self._descripcion)
        self._desc_lbl.setFont(qfont("size_caption_xs"))
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setMinimumHeight(40)
        # Tope más alto (52→84): descripciones del Hub de 3-4 líneas se
        # recortaban a mitad de línea. La card acompaña (ya no es fija).
        self._desc_lbl.setMaximumHeight(84)
        self._desc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay.addWidget(self._desc_lbl)

        lay.addStretch()

        # Footer: intensidad dots + botones
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        self._intensity = _IntensityDots(_intensity_for(self._nombre), modo=self._modo)
        footer.addWidget(self._intensity)
        footer.addStretch()
        self._btn_no = NMButton(
            t("text.module.actividades.btn_not_done", "No pude"),
            variant="secondary", size="sm", modo=self._modo, width=78
        )
        self._btn_no.clicked.connect(lambda: self.skipped.emit(self._nombre))
        footer.addWidget(self._btn_no)
        # "Hice" y "No pude" con jerarquía EQUIVALENTE (Fase 10): antes "Hice"
        # era variant="primary" (gradient dominante) y empujaba al usuario hacia
        # el "éxito". En activación conductual ambas respuestas son válidas y
        # honestas → ambos botones secondary, mismo peso visual, se distinguen
        # por la etiqueta.
        self._btn_yes = NMButton(
            t("text.module.actividades.btn_done", "Hice"),
            variant="secondary", size="sm", modo=self._modo, width=78
        )
        self._btn_yes.clicked.connect(lambda: self.completed.emit(self._nombre))
        footer.addWidget(self._btn_yes)
        lay.addLayout(footer)

        self._apply_sug_styles()

    def set_completed(self, completed: bool):
        self._completed_flag = bool(completed)
        if completed:
            self._btn_yes.setEnabled(False)
            self._btn_no.setEnabled(False)
            self._btn_yes.setText(t("text.module.actividades.btn_done_state", "Hecho"))
            self._title_lbl.setText(self._nombre)

    def set_done(self, resultado: str):
        """Alias del API existente para activity cards."""
        self.set_completed(resultado == "hecha")

    def _apply_sug_styles(self):
        cat_color = _cat_color(self._categoria, self._modo)
        qc = QColor(cat_color)
        bg_rgba = f"rgba({qc.red()},{qc.green()},{qc.blue()},36)"
        self._chip.setText(_category_label(self._categoria))
        self._chip.setStyleSheet(
            f"color: {cat_color}; background: {bg_rgba}; border-radius: 10px;"
        )
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._intensity._modo = self._modo
        self._intensity.update()
        self._apply_sug_styles()


# ── ModuloActividades v3 ────────────────────────────────────────────────────


class ModuloActividades(NMModule):
    MODULE_TITLE = "Actividades"
    MODULE_ICON = "actividades"

    def build_ui(self):
        self._all_activities: list[dict] = []
        self._current_filter: str = ""
        self._suggested_cards: list[_SuggestedCard] = []

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        # Scroll REAL (informe owner v1.0): sin tope de 3 actividades, muchas
        # asignaciones del Hub envuelven en filas y la página scrollea calma
        # en vez de comprimirse/superponerse. (El nombre _scroll_content era
        # aspiracional: el widget no estaba dentro de ningún QScrollArea.)
        from shared.theme_qt import stylesheet_scrollarea as _ss_scroll

        _scroll = QScrollArea()
        _scroll.setWidgetResizable(True)
        _scroll.setFrameShape(QFrame.Shape.NoFrame)
        _scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        _scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        _scroll.setStyleSheet(_ss_scroll(self._modo))
        _scroll.setWidget(self._scroll_content)
        outer.addWidget(_scroll, stretch=1)

        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        self._scroll_layout.setSpacing(V3_SP["sm"])
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Footer FIJO (fuera del scroll): historial + conteo, pinned al fondo
        # como el panel "Registros previos" de Registro TCC. Antes vivían dentro
        # del scroll y "flotaban" arriba/abajo según cuántas actividades hubiera;
        # ahora la lista de actividades se queda con todo el alto disponible.
        self._footer_holder = QWidget()
        self._footer_holder.setStyleSheet("background: transparent;")
        self._footer_layout = QVBoxLayout(self._footer_holder)
        self._footer_layout.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], V3_SP["sm"])
        self._footer_layout.setSpacing(V3_SP["xs"])
        outer.addWidget(self._footer_holder)

        self._load_suggestions()

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_category_tabs"):
            self._category_tabs._apply_theme(self._modo)
        if hasattr(self, "_filter_header"):
            self._filter_header._apply_theme(self._modo)
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

        # Clear footer fijo (historial + conteo): se reconstruye en cada recarga.
        if hasattr(self, "_footer_layout"):
            while self._footer_layout.count():
                fitem = self._footer_layout.takeAt(0)
                fw = fitem.widget()
                if fw:
                    self._footer_layout.removeWidget(fw)
                    fw.setParent(None)
                    fw.deleteLater()

        self._all_activities = []
        self._suggested_cards = []
        self._hidden_card_ids: set[int] = set()

        # 1. Header de módulo — NMPageHeader gestiona su propio tema
        # BL-07: título de módulo ahora en la titlebar; se conserva oculto.
        self._page_header = NMPageHeader("Actividades", modo=self._modo)
        self._scroll_layout.addWidget(self._page_header)
        self._page_header.hide()

        # 2. Load activities (sin MoodContextHeader — info ya está en Ánimo)
        animo = self._get_last_mood()
        if animo is None:
            self._scroll_layout.addWidget(
                NMEmptyState(
                    "run",
                    t("text.module.actividades.empty_no_mood_title", "Sin sugerencias"),
                    t(
                        "text.module.actividades.empty_no_mood_desc",
                        "Registrá tu ánimo primero para recibir sugerencias.",
                    ),
                )
            )
            return

        self._all_activities = self._get_activities(animo)
        if not self._all_activities:
            self._scroll_layout.addWidget(
                NMEmptyState(
                    "run",
                    t("text.module.actividades.empty_no_mood_title", "Sin sugerencias"),
                    t(
                        "text.module.actividades.empty_no_activities_desc",
                        "Tu terapeuta aún no ha cargado actividades para este ánimo.",
                    ),
                )
            )
            return

        # 3. Filtros como tabs pill del design system
        filter_card = NMCard(modo=self._modo, clickable=False, glow=False)
        filter_lay = QVBoxLayout(filter_card)
        filter_lay.setContentsMargins(V3_SP["md"], V3_SP["xs"], V3_SP["md"], V3_SP["xs"])
        filter_lay.setSpacing(V3_SP["xs"])
        self._filter_header = NMSectionHeader(
            t("text.module.actividades.categories_eyebrow", "Categorías"),
            t("text.module.actividades.categories_help", "Elegí una familia de actividades"),
            modo=self._modo,
        )
        filter_lay.addWidget(self._filter_header)
        self._category_tabs = NMTabs(
            [t("text.module.actividades.filter_all", "Todas")]
            + [_category_label(cat) for cat, _ in _CATEGORY_ORDER],
            variant="filter",
            modo=self._modo,
        )
        self._category_tabs.changed.connect(self._on_category_tab_changed)
        filter_lay.addWidget(self._category_tabs)
        self._scroll_layout.addWidget(filter_card)
        self._categories_card = filter_card

        # 4. Grid unificado de actividades
        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(V3_SP["sm"])
        self._grid_layout.setVerticalSpacing(V3_SP["sm"])
        self._scroll_layout.addWidget(self._grid_container)

        # 5. Footer count
        self._footer_lbl = QLabel("")
        self._footer_lbl.setFont(qfont("size_caption"))
        self._footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._footer_layout.addWidget(self._footer_lbl)

        self._rebuild_lists("")

    def _build_featured_card(self, animo: int) -> NMCard:
        """Card featured removida en P2-G (duplicaba el 'hecho' por card). Se conserva
        el método como no-op para no romper callers externos; el módulo solo usa
        ahora el grid unificado de _SuggestedCard."""
        return NMCard(modo=self._modo, clickable=False, glow=False)

    def _on_category_filter(self, cat: str):
        self._current_filter = cat
        self._rebuild_lists(cat)

    def _on_category_tab_changed(self, index: int, label: str):
        if index <= 0:
            self._on_category_filter("")
            return
        try:
            self._on_category_filter(_CATEGORY_ORDER[index - 1][0])
        except IndexError:
            self._on_category_filter("")

    def _rebuild_lists(self, cat: str):
        # Limpiar grid unificado
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._suggested_cards.clear()

        activities = self._all_activities
        if cat:
            activities = [a for a in activities if _cat_canon(a.get("categoria", "")) == cat]

        if not activities:
            display_cat = _category_label(cat) if cat else t("text.module.actividades.filter_all", "Todas")
            empty = QLabel(f'No hay actividades en "{display_cat}".')
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 3)
            self._footer_lbl.setText("")
            return

        # Grid unificado responsive: TODAS las actividades como _SuggestedCard,
        # en filas que envuelven (el cuerpo del módulo ya scrollea calmo).
        # Antes había un tope duro de 3: si el profesional cargaba muchas
        # actividades desde el Hub, el paciente nunca las veía (informe owner
        # v1.0 — Activación debe soportar muchos registros sin romperse).
        cols = self._activity_columns()
        for col in range(3):
            self._grid_layout.setColumnStretch(col, 1 if col < cols else 0)
        for i, act in enumerate(activities):
            card = _SuggestedCard(act, modo=self._modo)
            card.completed.connect(lambda n, cd=card: self._register_result(n, "hecha", cd, None))
            card.skipped.connect(lambda n, cd=card: self._register_result(n, "no_pude", cd, None))
            if visual_qa_enabled() and act.get("done"):
                card.set_done("hecha")
            self._grid_layout.addWidget(card, i // cols, i % cols)
            self._suggested_cards.append(card)

        n = len(activities)
        self._footer_lbl.setText(
            f"{n} actividad{'es' if n != 1 else ''} sugerida{'s' if n != 1 else ''}"
        )

    def _activity_columns(self) -> int:
        width = max(360, self._scroll_content.width() if hasattr(self, "_scroll_content") else self.width())
        if width >= 900:
            return 3
        if width >= 620:
            return 2
        return 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_grid_layout") and self._all_activities:
            self._rebuild_lists(self._current_filter)

    # ── _register_result (lógica preservada exacta) ──────────────────────────

    def _register_result(
        self, nombre: str, resultado: str, card_widget, seg: NMSegmentedChoice | None
    ):
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
                variant="info",
                duration_ms=3000,
            )
            return

        try:
            with conexion() as conn:
                # RA-1 (reauditoría UI-first): el módulo Actividades no captura
                # energía por separado. Antes, _register_result copiaba `animo`
                # como `energia` — inferencia falsa (en Behavioral Activation
                # energía y ánimo son dimensiones distintas: ansiedad = ánimo
                # bajo + energía alta; relajado cansado = ánimo alto + energía
                # baja). El dato llegaba al Hub como autoinforme real.
                #
                # Solución: NO escribir `energia`. SQLite aplica NULL (la
                # columna se hizo nullable vía migración _migrar_activacion_energia_null).
                # El sync (RA-1 shared/sync.py) no la envía a Supabase.
                # El Hub (RA-1 hub/pacientes_qt.py) no la pide.
                # La columna física se conserva por compatibilidad con datos
                # históricos; los registros nuevos llegan sin energia.
                conn.execute(
                    "INSERT INTO activacion (fecha, hora, animo, actividad, resultado) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (fecha_hoy(), hora_actual(), animo, nombre, resultado),
                )
            # RB-5: disparar sync inmediato para que la activación conductual
            # llegue al Hub sin quedar pendiente hasta el próximo sync.
            # Mismo patrón que timer_qt._save_session y animo_qt._registrar.
            try:
                from shared.sync import sync_inmediato_background

                sync_inmediato_background()
            except Exception:
                pass
        except Exception:
            _log.exception("Operation failed")

        # P2-G: ocultar la card al elegir hice/no-pude (evita duplicar el "hecho"
        # por card) y alimentar el mini-historial visible al paciente.
        if card_widget is not None:
            card_widget.setVisible(False)
            try:
                card_widget.deleteLater()
            except Exception:
                pass
        if hasattr(card_widget, "set_accent"):
            color_map = {
                "hecha": v3c("success", self._modo).name(),
                "no_pude": v3c("danger", self._modo).name(),
            }
            card_widget.set_accent(color_map.get(resultado, v3c("teal", self._modo).name()))
        if hasattr(card_widget, "play_success"):
            card_widget.play_success()
        if hasattr(card_widget, "set_completed") and resultado == "hecha":
            card_widget.set_completed(True)

        labels = {"hecha": "Hecha", "no_pude": "No se pudo"}
        NMToast.display(
            self.window(),
            f'Actividad "{nombre}": {labels.get(resultado, resultado)}',
            variant="success" if resultado == "hecha" else "info",
            duration_ms=2000,
        )

    # ── Data access (lógica preservada) ─────────────────────────────────────

    def _get_last_mood(self):
        if visual_qa_enabled():
            return qa_last_mood()
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),),
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

        # Sin actividades precargadas: las actividades las asigna el
        # profesional desde el Hub. Si no hay, se muestra el empty state.
        return []

    # ── Hooks ────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._load_suggestions()

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "5 actividades"
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM activacion WHERE fecha = ?", (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} actividad{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
