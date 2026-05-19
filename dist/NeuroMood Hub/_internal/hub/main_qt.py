"""
hub/main_qt.py — NeuroMood Hub (PyQt6 entry point)

Layout:
    QMainWindow
    ├── NMSidebar (200px, izquierda)
    └── área derecha
        ├── NMHeader (56px)
        └── NMFadeWidget
            ├── DashboardView
            ├── PacientesView
            ├── DetallePacienteView (se carga al seleccionar paciente)
            └── ConfigView

Toda la lógica de conexión Supabase preservada exacta.
"""

import sys
import os
import threading

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QScrollArea, QGridLayout, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QBrush, QRadialGradient
from PyQt6 import sip

from shared.theme_qt import (
    C, colors, norm_modo, qcolor, qfont, interpolate_color, SessionColor,
    get_gradient, gradient_colors, app_palette, stylesheet_base, stylesheet_scrollarea,
    obtener_ruta_recurso, aplicar_captionbar_qt,
    RADIUS_CARD, RADIUS_BUTTON, PAD_CONTAINER, PAD_CARD, GAP_CARDS,
    ThemeAwareWidgetMixin, HUB_ICONS, nm_icon,
    paint_shell_background,
)
from shared.components_qt import (
    ThemeManager, NMSidebar, NMHeader, NMFadeWidget,
    NMButton, NMButtonOutline, NMCard, NMInput, NMToast, NMSkeleton, responsive_columns,
    NMSyncOrb, NMProgressLine, NMFeaturedCard, NMModuleRing,
    NMHubSidebar, NMPatientRow, NMSettingsSection,
    NMChatBubble, NMTypingDots, NMProviderChip, NMQuickAction, NMPatientContext,
)
from shared.visual_qa import visual_qa_enabled, hub_patients, hub_module_metrics

_sb_create = None

from shared.config import supabase_url, supabase_key

_NAV_ITEMS = [
    ("dashboard", "fa5s.chart-bar", "Dashboard"),
    ("pacientes", "pacientes", "Pacientes"),
    ("config", "configuracion", "Config"),
]

_HUB_NAV_ITEMS = [
    ("pacientes", "users", "Pacientes"),
    ("dashboard", "dashboard", "Dashboard"),
    ("ia", "ai", "IA Asistente"),
    ("config", "cog", "Config"),
]

_ = _HUB_NAV_ITEMS  # primera definicion absorbida


def _disconnect_theme_tree(widget: QWidget):
    """Evita callbacks de theme_changed hacia widgets pendientes de deleteLater()."""
    tm = ThemeManager.instance()
    for obj in [widget, *widget.findChildren(QWidget)]:
        for slot_name in ("_apply_theme", "apply_theme", "_on_theme"):
            slot = getattr(obj, slot_name, None)
            if slot is None:
                continue
            try:
                tm.theme_changed.disconnect(slot)
            except (RuntimeError, TypeError):
                pass


def _apply_theme_tree(widget: QWidget, modo: str):
    """Aplica tema solo a widgets vivos, sin usar el signal global."""
    for obj in [widget, *widget.findChildren(QWidget)]:
        if sip.isdeleted(obj):
            continue
        for slot_name in ("_apply_theme", "apply_theme", "_on_theme"):
            slot = getattr(obj, slot_name, None)
            if slot is None:
                continue
            try:
                slot(modo)
            except Exception:
                pass
            break


def _get_sb():
    global _sb_create
    if _sb_create is None:
        try:
            from supabase import create_client
            _sb_create = create_client
        except ImportError:
            return None, "modulo supabase no instalado"
    url, key = supabase_url(), supabase_key()
    if not url or not key:
        return None, "credenciales no configuradas (.env)"
    try:
        return _sb_create(url, key), None
    except Exception as e:
        return None, str(e)[:60]


# ── Mini indicador de ánimo ───────────────────────────────────────────────────

class _AnimoIndicator(QWidget):
    """Círculo de 14px con color semántico del último ánimo registrado."""

    _COLORS = {
        range(1, 4):  "error",
        range(4, 7):  "warning",
        range(7, 11): "success",
    }

    def __init__(self, puntaje: int | None, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = modo
        self._puntaje = puntaje
        self.setFixedSize(14, 14)
        self._update_color()
        self.setStyleSheet("background: transparent;")
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _update_color(self):
        modo = norm_modo(self._modo)
        self._color = C("text_tertiary", modo)
        if self._puntaje is not None:
            for r, key in self._COLORS.items():
                if self._puntaje in r:
                    self._color = C(key, modo)
                    break

    def apply_theme(self, modo: str):
        self._modo = modo
        self._update_color()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 12, 12)
        p.end()


# ── DashboardView ─────────────────────────────────────────────────────────────

class DashboardView(ThemeAwareWidgetMixin, QWidget):
    def __init__(self, modo: str, pacientes: list, sb,
                 on_select_patient, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._pacientes = pacientes
        self._sb = sb
        self._on_select = on_select_patient
        self._setup()
        self._connect_theme()

    def paintEvent(self, event):
        """Aura radial dinámica de fondo."""
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        sc = SessionColor.instance()
        grad = QRadialGradient(w * 0.2, h * 0.5, w * 0.85)
        grad.setColorAt(0, sc.aura_qcolor(self._modo))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRect(self.rect())
        p.end()

    def _setup(self):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")
        self._grid_cols = 0

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        # ── NMProgressLine: ultra-thin 2px gradient header bar ────────────────
        _prog_line = NMProgressLine(total=1, current=1, modo=self._modo, parent=self)
        outer.addWidget(_prog_line)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(GAP_CARDS)

        # Título
        n = len(self._pacientes)
        title = QLabel(
            "Ana Martínez · Semana 12"
            if visual_qa_enabled()
            else f"Dashboard  —  {n} paciente{'s' if n != 1 else ''}"
        )
        title.setFont(qfont("size_h2", bold=True))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        layout.addWidget(title)

        if self._pacientes:
            scores = [p.get("last_mood") for p in self._pacientes if p.get("last_mood") is not None]
            avg = 7.2 if visual_qa_enabled() else (sum(scores) / len(scores) if scores else 7.0)
            emoji = "😄" if avg >= 8 else ("🙂" if avg >= 6 else "😐")
            featured = NMFeaturedCard(modo=self._modo)
            featured.set_score(avg, emoji)
            featured.set_delta(0.8 if visual_qa_enabled() else None)
            featured.set_meta(
                "12 semanas en programa · Última sesión: hace 2 días"
                if visual_qa_enabled()
                else f"{n} pacientes vinculados · ultima sincronizacion visual"
            )
            featured.set_tags(
                [("Ansiedad", "teal"), ("TCC", "accent"), ("Progreso alto", "violet")]
                if visual_qa_enabled()
                else [("Adherencia alta", "teal"), ("Riesgo bajo", "accent"), ("Agenda al dia", "violet")]
            )

            # Layout 2 columnas: Featured izquierda + Metrics apilados derecha
            two_col = QHBoxLayout()
            two_col.setSpacing(GAP_CARDS)
            two_col.addWidget(featured, stretch=3)

            metrics_col = QVBoxLayout()
            metrics_col.setSpacing(GAP_CARDS)
            for label, pct in hub_module_metrics():
                card = NMCard(modo=self._modo)
                card.setMinimumHeight(72)
                inner = QHBoxLayout(card)
                inner.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
                inner.setSpacing(10)
                inner.addWidget(NMModuleRing(size=44, pct=pct, modo=self._modo))
                txt = QVBoxLayout()
                name = QLabel(label)
                name.setFont(qfont("size_body", bold=True))
                name.setStyleSheet(
                    f"color: {c['text_primary']}; background: transparent;")
                meta = QLabel("actividad semanal")
                meta.setFont(qfont("size_caption"))
                meta.setStyleSheet(
                    f"color: {c['text_tertiary']}; background: transparent;")
                txt.addWidget(name)
                txt.addWidget(meta)
                inner.addLayout(txt, stretch=1)
                metrics_col.addWidget(card)
            two_col.addLayout(metrics_col, stretch=2)
            layout.addLayout(two_col)

            if visual_qa_enabled():
                recent = QLabel("Actividad reciente")
                recent.setFont(qfont("size_body", bold=True))
                recent.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
                layout.addWidget(recent)
                for text in [
                    "●  Respiración completada — 4-7-8 · 5 ciclos\n    Hoy 10:32",
                    "●  Registro de ánimo — 7/10 \"Buen día\"\n    Hoy 09:15",
                    "●  TCC · Paso 3 completado\n    Ayer 16:44",
                ]:
                    row = QLabel(text)
                    row.setFont(qfont("size_caption"))
                    row.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
                    layout.addWidget(row)
                layout.addStretch()
                return

        if not self._pacientes:
            empty = QLabel(
                "Sin pacientes registrados.\n"
                "Usa la seccion Pacientes para vincular."
            )
            empty.setFont(qfont("size_body"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            layout.addWidget(empty)
            layout.addStretch()
            return

        # Grid responsive
        self._dash_grid = QGridLayout()
        self._dash_grid.setSpacing(GAP_CARDS)
        layout.addLayout(self._dash_grid)
        self._dash_cards: list[tuple[NMCard, dict]] = []

        grad = gradient_colors(self._modo)

        for i, p in enumerate(self._pacientes):
            nombre = p.get("patient_name") or p.get("patient_id", "—")
            pid = p.get("patient_id", "")
            t = (i % 3) / 2
            card_accent = interpolate_color(grad[0], grad[-1], t)

            card = NMCard(accent_color=card_accent, clickable=True, modo=self._modo)
            card.setMinimumHeight(120)
            card.clicked.connect(
                lambda checked=False, _pid=pid, _n=nombre:
                    self._on_select(_pid, _n)
            )

            inner = QVBoxLayout()
            inner.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
            inner.setSpacing(4)

            top_row = QHBoxLayout()
            name_lbl = QLabel(nombre)
            name_lbl.setFont(qfont("size_body", bold=True))
            name_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(name_lbl)
            top_row.addStretch()

            puntaje = p.get("last_mood") if "last_mood" in p else None
            ind = _AnimoIndicator(puntaje, self._modo)
            ind.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(ind)
            inner.addLayout(top_row)

            id_lbl = QLabel(f"ID: {pid[:14]}…" if len(pid) > 14 else pid)
            id_lbl.setFont(qfont("size_caption"))
            id_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            id_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner.addWidget(id_lbl)
            inner.addStretch()

            btn = NMButton("Ver detalle", modo=self._modo, width=100, height=30)
            btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)

            card_inner = QWidget(card)
            card_inner.setStyleSheet("background: transparent;")
            card_inner.setLayout(inner)
            card_inner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.addWidget(card_inner)

            self._dash_cards.append((card, p))

        self._rebuild_dash_grid()
        layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_cols = responsive_columns(self.width(), min_card_width=250)
        if new_cols != self._grid_cols and hasattr(self, '_dash_cards'):
            self._grid_cols = new_cols
            self._rebuild_dash_grid()

    def _rebuild_dash_grid(self):
        if not hasattr(self, '_dash_cards') or not self._dash_cards:
            return
        cols = max(1, self._grid_cols or responsive_columns(self.width(), min_card_width=250))
        for i in reversed(range(self._dash_grid.count())):
            item = self._dash_grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        for c in range(cols):
            self._dash_grid.setColumnStretch(c, 1)
        for i, (card, _) in enumerate(self._dash_cards):
            row = i // cols
            col = i % cols
            self._dash_grid.addWidget(card, row, col)
        return

        # Grid de cards 3 columnas
        grid = QGridLayout()
        grid.setSpacing(GAP_CARDS)
        for col in range(3):
            grid.setColumnStretch(col, 1)

        grad = gradient_colors(self._modo)

        for i, p in enumerate(self._pacientes):
            nombre = p.get("patient_name") or p.get("patient_id", "—")
            pid = p.get("patient_id", "")
            t = (i % 3) / 2
            card_accent = interpolate_color(grad[0], grad[-1], t)

            card = NMCard(accent_color=card_accent, clickable=True, modo=self._modo)
            card.setMinimumHeight(120)
            card.clicked.connect(
                lambda checked=False, _pid=pid, _n=nombre:
                    self._on_select(_pid, _n)
            )

            inner = QVBoxLayout()
            inner.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
            inner.setSpacing(4)

            # Fila top: nombre + indicador ánimo
            top_row = QHBoxLayout()
            name_lbl = QLabel(nombre)
            name_lbl.setFont(qfont("size_body", bold=True))
            name_lbl.setStyleSheet(
                f"color: {c['text_primary']}; background: transparent;"
            )
            name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(name_lbl)
            top_row.addStretch()

            # Indicador de animo (ultimo puntaje si existe en los datos)
            puntaje = p.get("last_mood") if "last_mood" in p else None
            ind = _AnimoIndicator(puntaje, self._modo)
            ind.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(ind)
            inner.addLayout(top_row)

            # ID truncado
            id_lbl = QLabel(f"ID: {pid[:14]}…" if len(pid) > 14 else pid)
            id_lbl.setFont(qfont("size_caption"))
            id_lbl.setStyleSheet(
                f"color: {c['text_tertiary']}; background: transparent;"
            )
            id_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner.addWidget(id_lbl)

            inner.addStretch()

            btn = NMButton("Ver detalle", modo=self._modo, width=100, height=30)
            btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)

            # Montar inner en card
            card_inner = QWidget(card)
            card_inner.setStyleSheet("background: transparent;")
            card_inner.setLayout(inner)
            card_inner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.addWidget(card_inner)

            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")


# ── PacientesView ─────────────────────────────────────────────────────────────

class PacientesView(QWidget):
    """Hub > Pacientes Dashboard v3.

    Layout:
      Header: eyebrow "PACIENTES" + título "Pacientes (N)" + CTA "+ Nuevo"
      Search NMCard: NMInput + 3 filter pills (Todos/Activos/Sin registros/Atención)
      NMCard tabla: NMPatientRow × N con avatar + nombre + adherencia ring
    """

    def __init__(self, modo: str, pacientes: list, on_select, on_refresh, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._pacientes = pacientes
        self._on_select = on_select
        self._on_refresh = on_refresh
        self._search_query: str = ""
        self._current_filter: str = "todos"
        self._setup()

    def _setup(self):
        from shared.theme_qt import v3c, V3_SP, V3_RD
        from shared.theme import TYPOGRAPHY as _TY

        self._v3c = v3c
        self._sp = V3_SP
        self._rd = V3_RD
        self._ty = _TY

        self.setStyleSheet(
            f"background: {v3c('bgAlt' if 'dark' in self._modo else 'bg', self._modo).name()};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                    V3_SP["xl"], V3_SP["xl"])
        layout.setSpacing(V3_SP["lg"])

        # 1. Header
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._eyebrow = QLabel("PACIENTES")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=_TY["weight_semibold"]))
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        title_col.addWidget(self._eyebrow)
        n_pacientes = len(self._pacientes)
        self._title_lbl = QLabel(f"Pacientes vinculados ({n_pacientes})")
        self._title_lbl.setFont(qfont("size_h1", weight=_TY["weight_bold"]))
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        title_col.addWidget(self._title_lbl)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_sync = NMButton("Sincronizar", variant="ghost", size="sm",
                              modo=self._modo, width=110)
        btn_sync.clicked.connect(self._on_refresh)
        header_row.addWidget(btn_sync)
        btn_new = NMButton("+ Nuevo paciente", variant="gradient",
                             size="sm", modo=self._modo, width=160)
        header_row.addWidget(btn_new)
        layout.addLayout(header_row)

        # 2. Search + filter pills card
        search_card = NMCard(modo=self._modo, clickable=False, glow=False)
        sc_lay = QVBoxLayout(search_card)
        sc_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"],
                                    V3_SP["lg"], V3_SP["md"])
        sc_lay.setSpacing(V3_SP["sm"])
        search_row = QHBoxLayout()
        search_row.setSpacing(V3_SP["md"])
        from shared.theme_qt import stylesheet_lineedit
        self._search_edit = QLineEdit() if False else None  # placeholder
        # Use NMInput for consistency
        self._search_edit = NMInput("Buscar paciente por nombre o ID…",
                                      modo=self._modo)
        self._search_edit.setFixedHeight(36)
        self._search_edit.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_edit, stretch=2)

        # 4 filter pills (al estilo step pills del módulo Avisos)
        self._filter_pills: dict[str, NMButtonOutline] = {}
        for key, label in (("todos", "Todos"),
                            ("activos", "Activos"),
                            ("sin", "Sin registros"),
                            ("atencion", "Atención")):
            pill = NMButtonOutline(label, modo=self._modo,
                                     toggleable=False, size="sm")
            pill.setFixedSize(100, 30)
            pill.clicked.connect(
                lambda _, k=key: self._on_filter(k))
            self._filter_pills[key] = pill
            if key == "todos":
                pill.set_active(True)
            search_row.addWidget(pill)
        sc_lay.addLayout(search_row)
        layout.addWidget(search_card)

        # 3. Tabla NMCard con NMPatientRow × N
        table_card = NMCard(modo=self._modo, clickable=False, glow=False)
        tc_lay = QVBoxLayout(table_card)
        tc_lay.setContentsMargins(V3_SP["md"], V3_SP["sm"],
                                    V3_SP["md"], V3_SP["sm"])
        tc_lay.setSpacing(2)
        self._table_card = table_card
        self._table_lay = tc_lay
        layout.addWidget(table_card, stretch=1)

        self._render_rows()

    def _on_search(self, text: str):
        self._search_query = text.lower().strip()
        self._render_rows()

    def _on_filter(self, key: str):
        self._current_filter = key
        for k, pill in self._filter_pills.items():
            pill.set_active(k == key)
        self._render_rows()

    def _render_rows(self):
        v3c = self._v3c
        # Clear
        while self._table_lay.count():
            item = self._table_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        rows = list(self._pacientes)
        if self._search_query:
            q = self._search_query
            rows = [p for p in rows
                     if q in (p.get("patient_name") or "").lower()
                     or q in (p.get("patient_id") or "").lower()]
        if self._current_filter == "atencion":
            rows = [p for p in rows
                     if float(p.get("adherence", 1.0)) < 0.40]
        elif self._current_filter == "sin":
            rows = [p for p in rows if not p.get("last_session")]
        # "activos" deja todos por ahora (sin campo "activo" canónico)

        if not rows:
            empty = QLabel("No hay pacientes que coincidan.")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 24, 0, 24)
            self._table_lay.addWidget(empty)
            return

        for i, p in enumerate(rows):
            nombre = p.get("patient_name") or "—"
            pid = p.get("patient_id", "")
            subtitle = (
                f"Última sesión: {p.get('last_session', 'hace 2 días')}"
                if visual_qa_enabled()
                else f"ID: {pid[:16]}"
            )
            row = NMPatientRow(
                nombre, subtitle,
                pct=float(p.get("adherence", 0.75)),
                selected=False,
                modo=self._modo,
            )
            row.clicked.connect(
                lambda _pid=pid, _n=nombre: self._on_select(_pid, _n))
            self._table_lay.addWidget(row)
            # Separador entre filas (excepto última)
            if i < len(rows) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet(
                    f"background-color: {v3c('borderSoft', self._modo).name()};")
                self._table_lay.addWidget(sep)


# ── ConfigView ────────────────────────────────────────────────────────────────

class ConfigView(QWidget):
    def __init__(self, modo: str, on_toggle_theme, on_reconnect, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sync_orb_cfg: NMSyncOrb | None = None
        self._sync_status_lbl: QLabel | None = None
        self._sync_time_lbl: QLabel | None = None
        self._setup(on_toggle_theme, on_reconnect)

    def set_sync_state(self, state: str):
        """Update the connection orb state: 'ok' | 'error' | 'syncing'."""
        from shared.theme_qt import v3c
        if self._sync_orb_cfg is not None and not sip.isdeleted(self._sync_orb_cfg):
            self._sync_orb_cfg.set_state(state)
        _labels = {
            "ok":      ("Sincronizado",  v3c("success", self._modo).name()),
            "error":   ("Sin conexión",  v3c("danger",  self._modo).name()),
            "syncing": ("Conectando…",   v3c("warning", self._modo).name()),
        }
        text, color = _labels.get(state,
            ("Desconocido", v3c("text3", self._modo).name()))
        if self._sync_status_lbl and not sip.isdeleted(self._sync_status_lbl):
            self._sync_status_lbl.setText(text)
            self._sync_status_lbl.setStyleSheet(
                f"color: {color}; background: transparent;")
        if self._sync_time_lbl and not sip.isdeleted(self._sync_time_lbl):
            import datetime as _datetime
            now = _datetime.datetime.now().strftime("%H:%M")
            self._sync_time_lbl.setText(f"Última verificación: {now}")

    def _setup(self, on_toggle_theme, on_reconnect):
        from shared.theme_qt import v3c, V3_SP, V3_RD
        from shared.theme import TYPOGRAPHY as _TY

        self.setStyleSheet(
            f"background: {v3c('bgAlt' if 'dark' in self._modo else 'bg', self._modo).name()};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                    V3_SP["xl"], V3_SP["xl"])
        layout.setSpacing(V3_SP["lg"])

        # 1. Header eyebrow + título
        self._eyebrow = QLabel("CONFIGURACIÓN")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=_TY["weight_semibold"]))
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        layout.addWidget(self._eyebrow)

        title = QLabel("Ajustes del Hub")
        title.setFont(qfont("size_h1", weight=_TY["weight_bold"]))
        title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        layout.addWidget(title)

        # 2. Sync hero card (orb + status + botón sincronizar)
        sync_card = NMCard(modo=self._modo, clickable=False, glow=True)
        sync_card_layout = QHBoxLayout(sync_card)
        sync_card_layout.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                              V3_SP["xl"], V3_SP["lg"])
        sync_card_layout.setSpacing(V3_SP["lg"])

        self._sync_orb_cfg = NMSyncOrb(state="syncing", size=28,
                                        modo=self._modo, parent=sync_card)
        sync_card_layout.addWidget(self._sync_orb_cfg,
                                    alignment=Qt.AlignmentFlag.AlignVCenter)

        sync_text_col = QVBoxLayout()
        sync_text_col.setSpacing(2)
        sync_eyebrow = QLabel("ESTADO DE CONEXIÓN")
        sync_eyebrow.setFont(qfont("size_caption_xs",
                                     weight=_TY["weight_semibold"]))
        sync_eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        sync_text_col.addWidget(sync_eyebrow)
        self._sync_status_lbl = QLabel("Conectando…")
        self._sync_status_lbl.setFont(qfont("size_h2",
                                             weight=_TY["weight_bold"]))
        self._sync_status_lbl.setStyleSheet(
            f"color: {v3c('warning', self._modo).name()}; "
            f"background: transparent;")
        sync_text_col.addWidget(self._sync_status_lbl)
        self._sync_time_lbl = QLabel("Verificando…")
        self._sync_time_lbl.setFont(qfont("size_caption"))
        self._sync_time_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;")
        sync_text_col.addWidget(self._sync_time_lbl)
        sync_card_layout.addLayout(sync_text_col, stretch=1)

        btn_sync_card = NMButton("Sincronizar ahora", variant="gradient",
                                   size="md", modo=self._modo, width=170)
        btn_sync_card.clicked.connect(on_reconnect)
        sync_card_layout.addWidget(btn_sync_card,
                                     alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(sync_card)

        # 3. Grid 2×2 cards (Supabase / Apariencia / Seguridad / Log sync)
        grid = QGridLayout()
        grid.setSpacing(V3_SP["md"])
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # Conexión Supabase
        conn_sec = NMSettingsSection("Conexión Supabase", modo=self._modo)
        if visual_qa_enabled():
            conn_sec.add_row("URL", "https://xyz.supabase.co")
            conn_sec.add_row("API Key", "••••••••••4f3a")
            conn_sec.add_row("Auto-sync", "Activado")
        else:
            conn_sec.add_row("Configuración", "Automática")
            conn_sec.add_row("Credenciales",
                              "Protegidas" if supabase_url() and supabase_key()
                              else "No incluidas")
            conn_sec.add_row("Auto-sync", "Activado")
        grid.addWidget(conn_sec, 0, 0)

        # Apariencia
        app_sec = NMSettingsSection("Apariencia", modo=self._modo)
        btn_theme = NMButton("Cambiar tema", variant="secondary",
                               size="sm", modo=self._modo, width=130)
        btn_theme.clicked.connect(on_toggle_theme)
        app_sec.add_row("Tema", btn_theme)
        app_sec.add_row("Densidad", "Normal")
        app_sec.add_row("Idioma", "Español (AR)")
        app_sec.add_row("Proveedor IA", "Groq · llama3-70b")
        grid.addWidget(app_sec, 0, 1)

        # Seguridad
        sec_sec = NMSettingsSection("Seguridad", modo=self._modo)
        sec_sec.add_row("Cifrado local", "AES-256")
        sec_sec.add_row("Bloqueo automático", "Después de 30 min")
        sec_sec.add_row("PIN de acceso", "No configurado")
        grid.addWidget(sec_sec, 1, 0)

        # Log sync
        log_sec = NMSettingsSection("Log de sincronización", modo=self._modo)
        _clr_ok   = v3c("success", self._modo).name()
        _clr_teal = v3c("teal",    self._modo).name()
        _clr_warn = v3c("warning", self._modo).name()
        if visual_qa_enabled():
            log_sec.add_log(
                f"<span style='color:{_clr_ok}'>✓</span> 14:23:01 — Sync completada · 12 pacientes<br>"
                f"<span style='color:{_clr_teal}'>↻</span> 14:23:00 — Conectando a Supabase…<br>"
                f"<span style='color:{_clr_ok}'>✓</span> 14:10:44 — Backup local generado<br>"
                f"<span style='color:{_clr_warn}'>⚠</span> 13:12:08 — Timeout (reintentado ok)"
            )
        else:
            log_sec.add_log(
                f"<span style='color:{_clr_ok}'>✓</span> Listo para sincronizar<br>"
                f"<span style='color:{_clr_teal}'>↻</span> Esperando conexión"
            )
        grid.addWidget(log_sec, 1, 1)
        layout.addLayout(grid)
        layout.addStretch()


# ── NeuroMoodHub ────────────────────────────────────────────────────────────

class IAAssistantView(ThemeAwareWidgetMixin, QWidget):
    """Vista global IA Asistente del Hub, alineada al mockup S11."""
    def __init__(self, modo: str, paciente_nombre: str = "", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._paciente_nombre = paciente_nombre or "Sin paciente"
        self._setup()
        self._connect_theme()

    def _setup(self):
        from shared.theme_qt import v3c, V3_SP
        from shared.theme import TYPOGRAPHY as _TY

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        chat = QWidget()
        chat.setStyleSheet("background: transparent;")
        chat_l = QVBoxLayout(chat)
        chat_l.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                    V3_SP["xl"], V3_SP["lg"])
        chat_l.setSpacing(V3_SP["sm"])
        outer.addWidget(chat, stretch=1)

        # Header v3: eyebrow + título h1 + provider chip
        header_col = QVBoxLayout()
        header_col.setSpacing(2)
        eyebrow = QLabel("ASISTENTE CLÍNICO")
        eyebrow.setFont(qfont("size_caption_xs",
                                weight=_TY["weight_semibold"]))
        eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        header_col.addWidget(eyebrow)
        title_row = QHBoxLayout()
        self._title = QLabel("IA Asistente")
        self._title.setFont(qfont("size_h1",
                                    weight=_TY["weight_bold"]))
        title_row.addWidget(self._title)
        title_row.addStretch()
        self._provider = NMProviderChip("IA verificando", "syncing", self._modo)
        title_row.addWidget(self._provider)
        header_col.addLayout(title_row)
        chat_l.addLayout(header_col)

        self._messages_scroll = QScrollArea()
        self._messages_scroll.setWidgetResizable(True)
        self._messages_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._messages_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._messages_w = QWidget()
        self._messages_w.setStyleSheet("background: transparent;")
        self._messages_l = QVBoxLayout(self._messages_w)
        self._messages_l.setContentsMargins(0, 0, 8, 0)
        self._messages_l.setSpacing(4)
        self._messages_scroll.setWidget(self._messages_w)
        chat_l.addWidget(self._messages_scroll, stretch=1)

        self._add_bubble(
            "Hola, Doctor García. He analizado los datos de Ana de las últimas 2 semanas. ¿Desea un resumen o tiene alguna pregunta específica?"
            if visual_qa_enabled()
            else "Hola. Puedo ayudarte a resumir evolucion, revisar patrones y proponer acciones para el paciente seleccionado.",
            "left",
        )
        self._add_bubble(
            "¿Cómo estuvo su ánimo esta semana comparado con la anterior?"
            if visual_qa_enabled()
            else "Analiza el animo reciente y sugeri proximos pasos.",
            "right",
        )
        self._add_bubble(
            "El promedio de ánimo esta semana fue 7.2/10, comparado con 6.4/10 la semana anterior. Hay una tendencia positiva (+12.5%). Los días de mayor puntaje coinciden con sesiones de respiración registradas."
            if visual_qa_enabled()
            else "El panel queda listo para trabajar con los datos cargados desde Registros. Las respuestas mantienen criterio clinico y no reemplazan supervision profesional.",
            "left",
        )
        self._typing = NMTypingDots(self._modo)
        self._typing.hide()
        self._messages_l.addWidget(self._typing, alignment=Qt.AlignmentFlag.AlignLeft)
        self._messages_l.addStretch()

        quick = QHBoxLayout()
        quick.setSpacing(8)
        for text in [
            "Analizar animo reciente",
            "Proponer actividades",
            "Revisar distorsiones",
        ]:
            btn = NMQuickAction(text, self._modo)
            btn.clicked.connect(lambda checked=False, t=text: self._quick(t))
            quick.addWidget(btn)
        chat_l.addLayout(quick)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._input = NMInput("Escribe tu consulta...", modo=self._modo)
        input_row.addWidget(self._input, stretch=1)
        self._send = NMButton("Enviar", modo=self._modo, width=90, height=36)
        self._send.clicked.connect(self._send_message)
        input_row.addWidget(self._send)
        chat_l.addLayout(input_row)

        self._context = NMPatientContext(self._paciente_nombre, self._modo)
        outer.addWidget(self._context)
        self._update_provider()
        self._apply_theme(self._modo)

    def _add_bubble(self, text: str, side: str):
        bubble = NMChatBubble(text, side=side, modo=self._modo)
        self._messages_l.addWidget(bubble)
        return bubble

    def _quick(self, text: str):
        self._input.setText(text)
        self._send_message()

    def _send_message(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._send.setEnabled(False)
        self._add_bubble(text, "right")
        self._typing.show()
        self._typing.start()

        try:
            import hub.ia_asistente as ia
        except Exception:
            QTimer.singleShot(180, self._ia_unavailable)
            return

        sistema = (
            "Sos un asistente clínico para terapeutas de salud mental. "
            "Ayudás a analizar datos de seguimiento de pacientes: ánimo, respiración, "
            "checklist, pensamientos TCC. Respondés de forma concisa en lenguaje "
            "clínico profesional. Nunca hacés diagnósticos ni recomendás medicación. "
            f"Paciente en contexto: {self._paciente_nombre}."
        )
        ia._llamar(
            text,
            sistema,
            on_result=lambda r: QTimer.singleShot(0, lambda: self._on_ia_result(r)),
            on_error=lambda e: QTimer.singleShot(0, lambda: self._on_ia_error(e)),
        )

    def _on_ia_result(self, text: str):
        if sip.isdeleted(self):
            return
        self._typing.stop()
        self._typing.hide()
        self._send.setEnabled(True)
        self._add_bubble(text, "left")
        QTimer.singleShot(50, self._scroll_bottom)

    def _on_ia_error(self, msg: str):
        if sip.isdeleted(self):
            return
        self._typing.stop()
        self._typing.hide()
        self._send.setEnabled(True)
        self._add_bubble(msg, "left")

    def _ia_unavailable(self):
        if sip.isdeleted(self):
            return
        self._typing.stop()
        self._typing.hide()
        self._send.setEnabled(True)
        self._add_bubble("Módulo IA no disponible. Verificá que las dependencias estén instaladas.", "left")

    def _scroll_bottom(self):
        if sip.isdeleted(self):
            return
        sb = self._messages_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_patient(self, nombre: str):
        self._paciente_nombre = nombre or "Sin paciente"
        if hasattr(self, "_context"):
            self._context.set_patient(self._paciente_nombre)

    def _update_provider(self):
        if visual_qa_enabled():
            self._provider.set_status("Groq · llama3", "ok")
            return
        try:
            import hub.ia_asistente as ia
            msg = ia.status_msg()
        except Exception:
            msg = "IA no disponible"
        state = "ok" if "disponible" in msg else ("syncing" if "verificando" in msg else "error")
        self._provider.set_status(msg.replace("IA disponible via ", ""), state)

    def _apply_theme(self, modo: str):
        from shared.theme_qt import v3c
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        self.setStyleSheet(
            f"background: {v3c('bgAlt' if is_dark else 'bg', self._modo).name()};")
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        if hasattr(self, "_messages_scroll"):
            self._messages_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))


class _ShellWidget(QWidget):
    """Central widget con fondo shell v3: gradiente + blobs."""
    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = modo

    def set_shell_modo(self, modo: str):
        self._modo = modo
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        paint_shell_background(p, QRectF(self.rect()), self._modo)
        p.end()


class NeuroMoodHub(ThemeAwareWidgetMixin, QMainWindow):
    _patients_loaded_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._patients_loaded_signal.connect(self._on_pacientes_loaded)
        self._modo = "dark_hybrid"
        self._sb = None
        self._pacientes: list = []
        self._paciente_id: str | None = None
        self._paciente_nombre: str = ""
        self._current_view = "pacientes"

        ThemeManager.instance().switch_mode(self._modo)

        self.setWindowTitle("NeuroMood Hub")
        self.setMinimumSize(QSize(1120, 760))
        self.resize(QSize(1360, 920))
        self._center()
        self._apply_icon()
        self._apply_initial_style()
        self._build_ui()

        QTimer.singleShot(
            120,
            lambda: aplicar_captionbar_qt(self, self._modo)
            if not sip.isdeleted(self) else None,
        )
        QTimer.singleShot(350, self._init_connection)
        self._ia_status_timer = QTimer(self)
        self._ia_status_timer.setInterval(30000)
        self._ia_status_timer.timeout.connect(self._update_ia_status)
        self._ia_status_timer.start()
        self._update_ia_status()
        self._connect_theme()

    # ── Ventana ───────────────────────────────────────────────────────────────

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        target_w = min(1100, int(screen.width() * 0.75))
        target_h = min(720, int(screen.height() * 0.82))
        if target_w < self.minimumWidth():
            target_w = self.minimumWidth()
        if target_h < self.minimumHeight():
            target_h = self.minimumHeight()
        self.resize(QSize(target_w, target_h))
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def _apply_icon(self):
        ico = obtener_ruta_recurso("NM_icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

    def _apply_initial_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    def _apply_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = _ShellWidget(modo=self._modo)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = NMHubSidebar(_HUB_NAV_ITEMS, active=self._current_view,
                                     modo=self._modo, parent=central)
        self._sidebar.set_footer("Sin paciente")

        # ── Sidebar footer: NMSyncOrb + collapse toggle ───────────────────────
        footer = QWidget()
        footer.setStyleSheet("background: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 8, 12, 12)
        footer_layout.setSpacing(8)

        self._sync_orb = NMSyncOrb(state="syncing", size=12, modo=self._modo, parent=footer)
        footer_layout.addWidget(self._sync_orb, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._sync_orb_label = QLabel("Conectando…")
        self._sync_orb_label.setFont(qfont("size_caption"))
        c = colors(self._modo)
        self._sync_orb_label.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent;"
        )
        footer_layout.addWidget(self._sync_orb_label, stretch=1)

        self._btn_collapse = NMButtonOutline("", modo=self._modo)
        self._btn_collapse.setFixedSize(26, 26)
        self._btn_collapse.setIcon(nm_icon("arrowLeft", C("text3", self._modo), size=12))
        self._btn_collapse.clicked.connect(self._toggle_sidebar)
        footer_layout.addWidget(self._btn_collapse, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._sidebar._layout.addWidget(footer)
        self._sidebar_collapsed = False

        self._sidebar.nav_clicked.connect(self._on_nav)
        main_layout.addWidget(self._sidebar)

        # Área derecha
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        main_layout.addWidget(right)

        # Header
        self._header = NMHeader(right, modo=self._modo)
        self._header.theme_toggle.connect(self._toggle_theme)
        rl.addWidget(self._header)

        # Status label en header
        c = colors(self._modo)
        self._lbl_status = QLabel("Conectando…")
        self._lbl_status.setFont(qfont("size_caption"))
        self._lbl_status.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent;"
        )
        # Insertar en el header layout
        header_layout = self._header.layout()
        if header_layout:
            header_layout.insertWidget(1, self._lbl_status)

        self._lbl_ia_status = QLabel("IA: verificando")
        self._lbl_ia_status.setFont(qfont("size_caption"))
        header_layout = self._header.layout()
        if header_layout:
            header_layout.insertWidget(2, self._lbl_ia_status)

        # Stack
        self._stack = NMFadeWidget(right)
        rl.addWidget(self._stack)

        # Vistas iniciales
        self._refresh_all_views()

    def _refresh_all_views(self):
        """Recrea todas las vistas con los datos actuales."""
        # Limpiar stack
        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            _disconnect_theme_tree(w)
            w.deleteLater()

        self._view_dashboard = DashboardView(
            self._modo, self._pacientes, self._sb,
            on_select_patient=self._select_patient,
        )
        self._view_pacientes = PacientesView(
            self._modo, self._pacientes,
            on_select=self._select_patient,
            on_refresh=self._cargar_pacientes,
        )
        self._view_config = ConfigView(
            self._modo,
            on_toggle_theme=self._toggle_theme,
            on_reconnect=self._reconnect,
        )
        self._view_ia = IAAssistantView(
            self._modo,
            paciente_nombre=self._paciente_nombre or "Sin paciente",
        )

        self._stack.addWidget(self._view_dashboard)
        self._stack.addWidget(self._view_pacientes)
        self._stack.addWidget(self._view_ia)
        self._stack.addWidget(self._view_config)

        views = {
            "dashboard": self._view_dashboard,
            "pacientes":  self._view_pacientes,
            "ia":         self._view_ia,
            "config":     self._view_config,
        }
        target = views.get(self._current_view, self._view_dashboard)
        self._stack.setCurrentWidget(target)
        self._sidebar.set_active(self._current_view)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _on_nav(self, item_id: str):
        self._current_view = item_id
        self._header.set_back_action(None)
        self._header.set_context_title("")
        self._lbl_status.show()
        self._lbl_ia_status.show()
        views = {
            "dashboard": self._view_dashboard,
            "pacientes":  self._view_pacientes,
            "ia":         self._view_ia,
            "config":     self._view_config,
        }
        if item_id in views:
            QStackedWidget.setCurrentWidget(self._stack, views[item_id])
            if hasattr(self._stack, "_animating"):
                self._stack._animating = False
            self._sidebar.set_active(item_id)

    def _select_patient(self, pid: str, nombre: str):
        self._paciente_id = pid
        self._paciente_nombre = nombre
        if hasattr(self, "_view_ia"):
            self._view_ia.set_patient(nombre)

        # Cargar vista de detalle
        from hub.pacientes_qt import DetallePacienteView
        detalle = DetallePacienteView(
            modo=self._modo, sb=self._sb,
            paciente_id=pid, paciente_nombre=nombre,
        )
        detalle.back_requested.connect(self._back_to_dashboard)

        self._stack.addWidget(detalle)
        self._stack.setCurrentWidget(detalle)
        self._current_view = "detalle"

        self._header.set_back_action(self._back_to_dashboard)
        self._header.set_context_title(nombre[:24], "pacientes")
        self._lbl_status.hide()
        self._lbl_ia_status.hide()
        self._lbl_status.setText(nombre[:24])
        self._lbl_status.setStyleSheet(
            f"color: {C('text_primary', self._modo)}; background: transparent;"
        )

    def _back_to_dashboard(self):
        self._current_view = "dashboard"
        self._stack.setCurrentWidget(self._view_dashboard)
        self._sidebar.set_active("dashboard")
        self._header.set_back_action(None)
        self._header.set_context_title("")
        self._lbl_status.show()
        self._lbl_ia_status.show()

    # ── Conexión (lógica preservada exacta) ───────────────────────────────────

    def _init_connection(self):
        if visual_qa_enabled():
            self._activate_visual_qa_hub()
            return
        self._sb, motivo = _get_sb()
        c = colors(self._modo)
        if self._sb:
            # Verificar conexión real
            _verify_err = None
            try:
                res = self._sb.table("patients").select("patient_id", count="exact").execute()
                if hasattr(res, 'data'):
                    self._lbl_status.setText("● Conectado")
                    self._lbl_status.setStyleSheet(
                        f"color: {c['success']}; background: transparent;"
                    )
                    if hasattr(self, "_sync_orb"):
                        self._sync_orb.set_state("ok")
                    if hasattr(self, "_sync_orb_label"):
                        self._sync_orb_label.setText("Conectado")
                        self._sync_orb_label.setStyleSheet(
                            f"color: {c['success']}; background: transparent;"
                        )
                    if hasattr(self, "_view_config"):
                        self._view_config.set_sync_state("ok")
                    self._cargar_pacientes()
                    return
            except Exception as _e:
                _verify_err = str(_e)[:60]
            self._sb = None
        _detail = motivo or _verify_err or 'verificación fallida'
        self._lbl_status.setText(f"● Sin conexión: {_detail}")
        self._lbl_status.setStyleSheet(
            f"color: {c['error']}; background: transparent;"
        )
        if hasattr(self, "_sync_orb"):
            self._sync_orb.set_state("error")
        if hasattr(self, "_sync_orb_label"):
            self._sync_orb_label.setText("Sin conexión")
            self._sync_orb_label.setStyleSheet(
                f"color: {c['error']}; background: transparent;"
            )
        if hasattr(self, "_view_config"):
            self._view_config.set_sync_state("error")

    def _cargar_pacientes(self):
        if visual_qa_enabled():
            self._on_pacientes_loaded(hub_patients())
            return
        if not self._sb:
            return

        def _fetch():
            try:
                res = (self._sb.table("patients")
                       .select("patient_id,patient_name")
                       .execute())
                pats = res.data or []
            except Exception:
                pats = []
            self._patients_loaded_signal.emit(pats)

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_pacientes_loaded(self, pats: list):
        self._pacientes = pats
        self._refresh_all_views()

    def _activate_visual_qa_hub(self):
        c = colors(self._modo)
        self._sb = None
        self._pacientes = hub_patients()
        if self._pacientes:
            self._paciente_id = self._pacientes[0]["patient_id"]
            self._paciente_nombre = self._pacientes[0]["patient_name"]
        if hasattr(self, "_sidebar"):
            self._sidebar.set_footer("Dr. Garcia")
        self._lbl_status.setText("● Demo visual")
        self._lbl_status.setStyleSheet(
            f"color: {c['teal']}; background: transparent;"
        )
        if hasattr(self, "_sync_orb"):
            self._sync_orb.set_state("ok")
        if hasattr(self, "_sync_orb_label"):
            self._sync_orb_label.setText("Demo visual")
            self._sync_orb_label.setStyleSheet(
                f"color: {c['teal']}; background: transparent;"
            )
        if hasattr(self, "_view_config"):
            self._view_config.set_sync_state("ok")
        self._refresh_all_views()

    def _update_ia_status(self):
        if not hasattr(self, "_lbl_ia_status") or sip.isdeleted(self._lbl_ia_status):
            return
        if visual_qa_enabled():
            c = colors(self._modo)
            self._lbl_ia_status.setText("IA: demo visual")
            self._lbl_ia_status.setStyleSheet(
                f"color: {c['teal']}; background: transparent;"
            )
            return
        try:
            import hub.ia_asistente as ia
            msg = ia.status_msg()
        except Exception:
            msg = "IA no disponible"
        c = colors(self._modo)
        ok = "disponible via" in msg
        pending = "verificando" in msg
        color = c["success"] if ok else (c["warning"] if pending else c["text_tertiary"])
        self._lbl_ia_status.setText(msg)
        self._lbl_ia_status.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

    def _reconnect(self):
        if visual_qa_enabled():
            self._activate_visual_qa_hub()
            NMToast.display(self, "Demo visual recargado", variant="success", duration_ms=1600)
            return
        self._sb, motivo = _get_sb()
        c = colors(self._modo)
        if hasattr(self, "_sync_orb"):
            self._sync_orb.set_state("syncing")
        if hasattr(self, "_sync_orb_label"):
            self._sync_orb_label.setText("Reconectando…")
            self._sync_orb_label.setStyleSheet(
                f"color: {c['text_tertiary']}; background: transparent;"
            )
        if self._sb:
            try:
                res = self._sb.table("patients").select("patient_id", count="exact").execute()
                if hasattr(res, 'data'):
                    self._lbl_status.setText("● Conectado")
                    self._lbl_status.setStyleSheet(
                        f"color: {c['success']}; background: transparent;"
                    )
                    if hasattr(self, "_sync_orb"):
                        self._sync_orb.set_state("ok")
                    if hasattr(self, "_sync_orb_label"):
                        self._sync_orb_label.setText("Conectado")
                        self._sync_orb_label.setStyleSheet(
                            f"color: {c['success']}; background: transparent;"
                        )
                    if hasattr(self, "_view_config"):
                        self._view_config.set_sync_state("ok")
                    self._cargar_pacientes()
                    NMToast.display(self, "Conexión restablecida", variant="success", duration_ms=2000)
                    return
            except Exception:
                pass
            self._sb = None
        self._lbl_status.setText(f"● Error: {motivo or 'verificación fallida'}")
        self._lbl_status.setStyleSheet(
            f"color: {c['error']}; background: transparent;"
        )
        if hasattr(self, "_sync_orb"):
            self._sync_orb.set_state("error")
        if hasattr(self, "_sync_orb_label"):
            self._sync_orb_label.setText("Sin conexión")
            self._sync_orb_label.setStyleSheet(
                f"color: {c['error']}; background: transparent;"
            )
        if hasattr(self, "_view_config"):
            self._view_config.set_sync_state("error")
        NMToast.display(self, f"No se pudo conectar: {motivo or 'verificación fallida'}", variant="error")

    # ── Sidebar collapse ──────────────────────────────────────────────────────

    def _toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        if self._sidebar_collapsed:
            self._sidebar.setFixedWidth(48)
            self._sync_orb_label.hide()
            self._btn_collapse.setIcon(nm_icon("arrowRight", C("text3", self._modo), size=12))
        else:
            self._sidebar.setFixedWidth(240)
            self._sync_orb_label.show()
            self._btn_collapse.setIcon(nm_icon("arrowLeft", C("text3", self._modo), size=12))

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._modo = "light_hybrid" if "dark" in self._modo else "dark_hybrid"
        ThemeManager.instance()._modo = self._modo
        self._apply_theme(self._modo)
        QTimer.singleShot(
            50,
            lambda: aplicar_captionbar_qt(self, self._modo)
            if not sip.isdeleted(self) else None,
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()
        cw = self.centralWidget()
        if isinstance(cw, _ShellWidget):
            cw.set_shell_modo(self._modo)
        if hasattr(self, "_sidebar"):
            self._sidebar._apply_theme(self._modo)
        if hasattr(self, "_header"):
            self._header._apply_theme(self._modo)
        if hasattr(self, "_lbl_status"):
            c = colors(self._modo)
            self._lbl_status.setStyleSheet(
                f"color: {c['text_tertiary']}; background: transparent;"
            )
        if hasattr(self, "_lbl_ia_status"):
            self._update_ia_status()
        if hasattr(self, "_sync_orb_label"):
            c = colors(self._modo)
            self._sync_orb_label.setStyleSheet(
                f"color: {c['text_tertiary']}; background: transparent;"
            )
        if hasattr(self, "_stack"):
            self._refresh_all_views()

    def closeEvent(self, event):
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    from shared.crash_log import setup as _crash_setup
    _crash_setup("hub")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood Hub")
    # AA_UseHighDpiPixmaps fue eliminado en PyQt6 6.x — DPI se maneja automáticamente
    window = NeuroMoodHub()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
