"""
app/modules/rutina_qt.py — Rutina del día v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Rutina):

  Header        eyebrow
  Hero card     Ring grande del día (120) + título + descripción +
                NMButton gradient "Nueva tarea" (asume sección horaria actual)
  3-col grid    3 _SectionCard (Mañana / Tarde / Noche):
                  • Header: NMIcon temático + label + ring chico + counter "N/M"
                  • Body: lista de NMCustomCheck (tareas)
                  • Footer: NMButton ghost "+ Agregar tarea"
  Nota del día  NMDayNote (existente, sin cambios)

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  SECCIONES, _load_tasks(), _on_check(), _add_task(), _guardar_nota_text(),
  get_card_status(), schema DB (checklist_tareas, checklist_completadas),
  NMToast + checkmark animado al completar tarea.
"""

import os
import sys
from shared.crash_log import redact
import logging
import datetime as _dt

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QSizePolicy,
    QGridLayout,
    QMenu,
    QScrollArea,
)

try:
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        ThemeManager,
        NMCard,
        NMIcon,
        NMModuleRing,
        NMCustomCheck,
        NMEmptyState,
        NMProgressLine,
        NMInput,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        qcolor_to_rgba_css,
        v3c,
        V3_SP,
        V3_RD,
        stylesheet_scrollarea,
        PAD_CONTAINER,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, leer_config, conexion
    from shared.utils import fecha_hoy
    from shared.visual_qa import visual_qa_enabled, routine_sections
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
        NMModuleRing,
        NMCustomCheck,
        NMEmptyState,
    )
    from shared.theme_qt import (
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.visual_qa import visual_qa_enabled, routine_sections

from shared.remote_config import t


# ── Constantes preservadas ───────────────────────────────────────────────────

# v3: SVG icons en lugar de fa5s
SECCIONES = [
    ("manana", "text.module.rutina.section_morning", "Mañana", "sun"),
    ("tarde", "text.module.rutina.section_afternoon", "Tarde", "spark"),
    ("noche", "text.module.rutina.section_night", "Noche", "moon"),
]


# ── _HeroDayCard ─────────────────────────────────────────────────────────────

RUTINA_MODOS = {"solo_profesional", "mixto", "solo_paciente"}


def _rutina_modo() -> str:
    return "solo_profesional"


class _HeroDayCard(NMCard):
    """Hero v3: ring del progreso del día + título + descripción (sin CTA)."""

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._done = 0
        self._total = 0
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        # Compacto: el hero es solo visual; el "+ Agregar tarea" vive en cada sección.
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        lay.setSpacing(V3_SP["md"])

        self._ring = NMModuleRing(size=72, pct=0.0, modo=self._modo)
        lay.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(V3_SP["xs"])
        self._eyebrow = QLabel(t("text.module.rutina.eyebrow", "Progreso del día"))
        self._eyebrow.setFont(eyebrow_font())
        col.addWidget(self._eyebrow)
        self._title_lbl = QLabel(t("text.module.rutina.no_tasks_title", "Sin tareas configuradas"))
        self._title_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._title_lbl)
        self._desc_lbl = QLabel(t("text.module.rutina.no_tasks_desc", "Tu rutina se va construyendo paso a paso."))
        self._desc_lbl.setFont(qfont("size_small"))
        self._desc_lbl.setWordWrap(True)
        col.addWidget(self._desc_lbl)
        col.addStretch()
        lay.addLayout(col, stretch=1)

        self.setMaximumHeight(116)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._apply_hero_styles()

    def set_progress(self, done: int, total: int):
        self._done = done
        self._total = total
        if total > 0:
            pct = done / total
            self._ring.set_pct(pct)
            self._title_lbl.setText(f"{done} de {total} tareas completadas")
            self._desc_lbl.setText(
                f"{int(pct * 100)}% del día completado."
                if pct < 1.0
                else "¡Excelente! Rutina del día completa."
            )
        else:
            self._ring.set_pct(0.0)
            self._title_lbl.setText(t("text.module.rutina.no_tasks_title", "Sin tareas configuradas"))
            self._desc_lbl.setText(t("text.module.rutina.no_tasks_desc", "Tu rutina se va construyendo paso a paso."))

    def set_manual_enabled(self, enabled: bool):
        """Compatibilidad: el hero ya no tiene CTA. No-op silencioso."""
        return

    def _apply_hero_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"background: transparent;"
        )
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_hero_styles()


# ── _SectionCard ─────────────────────────────────────────────────────────────


class _SectionCard(NMCard):
    """Card v3 para una sección de rutina (Mañana / Tarde / Noche).

    Composición:
      Header: NMIcon temático + label + counter "N/M" + NMModuleRing(40)
      Body:   QVBoxLayout que el módulo padre llena con NMCustomCheck
      Footer: NMButton ghost "+ Agregar tarea"
    """

    add_requested = pyqtSignal(str)  # emite la key de sección

    def __init__(self, key: str, label: str, icon_name: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._key = key
        self._label = label
        self._icon_name = icon_name
        self._build()
        self.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        lay.setSpacing(V3_SP["sm"])

        head = QHBoxLayout()
        head.setSpacing(V3_SP["md"])
        self._icon = NMIcon(self._icon_name, size=24, color_key="teal", modo=self._modo)
        head.addWidget(self._icon)
        self._title = QLabel(self._label)
        self._title.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        head.addWidget(self._title)
        head.addStretch()
        self._count_lbl = QLabel("0/0")
        self._count_lbl.setFont(qfont_mono(10, bold=False))
        head.addWidget(self._count_lbl)
        self._ring = NMModuleRing(size=40, pct=0.0, modo=self._modo)
        head.addWidget(self._ring)
        lay.addLayout(head)

        # Body: scroll interno para acumular tareas sin deformer la card.
        self._body_scroll = QScrollArea(self)
        self._body_scroll.setWidgetResizable(True)
        self._body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._body_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._body_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        # El body llena todo el alto disponible (stretch=1) y el "+ Agregar
        # tarea" queda pinneado al fondo. Antes un setMaximumHeight(260) capaba
        # la lista y dejaba el botón flotando en el medio con espacio muerto
        # abajo cuando se acumulaban tareas (feedback owner). Sin tope, la lista
        # se extiende y scrollea calma.
        self._body_scroll.setMinimumHeight(104)
        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(1)
        self._body_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._body_scroll.setWidget(self._body)
        lay.addWidget(self._body_scroll, stretch=1)

        # Footer: secondary visible para descubribilidad en columnas vacías
        self._add_btn = NMButton(
            t("text.module.rutina.add_task_btn", "+ Agregar tarea"),
            variant="secondary", size="sm", modo=self._modo, width=0
        )
        self._add_btn.clicked.connect(lambda: self.add_requested.emit(self._key))
        lay.addWidget(self._add_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        self._apply_section_styles()

    # ── API pública usada por el módulo ──────────────────────────────────────

    def body_layout(self) -> QVBoxLayout:
        return self._body_lay

    def section_key(self) -> str:
        return self._key

    def set_progress(self, done: int, total: int):
        if total > 0:
            self._ring.set_pct(done / total)
            self._count_lbl.setText(f"{done}/{total}")
        else:
            self._ring.set_pct(0.0)
            self._count_lbl.setText("0/0")

    def set_manual_enabled(self, enabled: bool):
        self._add_btn.setVisible(enabled)

    def show_add_inline(self, on_save):
        """Inserta una fila inline (input tematizado + botón check) al final del body."""
        try:
            _log.debug(f"show_add_inline called, modo={getattr(self, '_modo', 'N/A')}")
            form = QFrame()
            form.setObjectName("AddForm")
            form_lay = QHBoxLayout(form)
            form_lay.setContentsMargins(V3_SP["sm"], V3_SP["sm"], V3_SP["sm"], V3_SP["sm"])
            form_lay.setSpacing(V3_SP["sm"])
            entry = NMInput(
                placeholder=t("text.module.rutina.new_task_placeholder", "Nueva tarea…"),
                modo=self._modo,
            )
            entry.setMinimumHeight(34)
            entry.setMaximumHeight(38)
            form_lay.addWidget(entry, stretch=1)
            btn = NMButton("✓", variant="gradient", size="sm", modo=self._modo, width=36)
            btn.setEnabled(False)
            form_lay.addWidget(btn)

            form.setStyleSheet(
                f"#AddForm {{ background: {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                f"border-radius: 10px; }}"
            )
            self._body_lay.addWidget(form)
            entry.setFocus()

            # El body scrollea (max 168px): si las tareas llenan el viewport el
            # form nace fuera de vista. Forzar el layout y bajar al fondo (el
            # form siempre es el último hijo del body).
            def _reveal():
                self._body_lay.activate()
                self._body.adjustSize()
                sb = self._body_scroll.verticalScrollBar()
                sb.setValue(sb.maximum())

            _reveal()
            QTimer.singleShot(0, _reveal)

            committed = False

            def _on_text_changed(txt: str):
                btn.setEnabled(bool(txt.strip()))

            def _close_form():
                self._body_lay.removeWidget(form)
                form.setParent(None)
                form.deleteLater()

            def _commit():
                nonlocal committed
                if committed:
                    return
                txt = entry.text().strip()
                if not txt:
                    return
                committed = True
                _close_form()
                on_save(self._key, txt, btn)

            entry.textChanged.connect(_on_text_changed)
            btn.clicked.connect(_commit)
            entry.returnPressed.connect(_commit)
        except Exception as e:
            _log.error(redact(f"Error in show_add_inline: {e}"))
            import traceback

            traceback.print_exc()

    # ── styles / theme ───────────────────────────────────────────────────────

    def _apply_section_styles(self):
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._count_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_section_styles()


# ── ModuloRutina v3 ──────────────────────────────────────────────────────────


class ModuloRutina(NMModule):
    MODULE_TITLE = "Rutina"
    MODULE_ICON = "rutina"

    def build_ui(self):
        self._rutina_modo = _rutina_modo()
        self._manual_enabled = self._rutina_modo != "solo_profesional"
        self._task_checks: dict[int, NMCustomCheck] = {}
        self._task_done: dict[int, bool] = {}
        self._task_section: dict[int, str] = {}
        self._section_cards: dict[str, _SectionCard] = {}

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        outer.addWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        # 1. Hero Day Card (Ring grande del día, sin CTA — el "+ Agregar tarea"
        # vive en cada sección para evitar duplicación y solapamiento).
        self._hero_card = _HeroDayCard(modo=self._modo)
        self._hero_card.set_manual_enabled(self._manual_enabled)
        lay.addWidget(self._hero_card)

        # 2. Empty state (oculta cuando hay tareas)
        self._empty_state = NMEmptyState(
            "routine",
            t("text.module.rutina.empty_title", "Sin rutina asignada"),
            t("text.module.rutina.empty_desc", "Tu terapeuta te enviara actividades pronto."),
            parent=body,
        )
        self._empty_state.hide()
        lay.addWidget(self._empty_state)

        # 4. Grid responsive de _SectionCard
        self._sections_grid_widget = QWidget()
        self._sections_grid_widget.setStyleSheet("background: transparent;")
        self._sections_grid = QGridLayout(self._sections_grid_widget)
        self._sections_grid.setContentsMargins(0, 0, 0, 0)
        self._sections_grid.setHorizontalSpacing(V3_SP["sm"])
        self._sections_grid.setVerticalSpacing(V3_SP["sm"])
        self._section_order: list[_SectionCard] = []
        for key, text_key, label, icon_name in SECCIONES:
            label = t(text_key, label)
            card = _SectionCard(key, label, icon_name, modo=self._modo)
            card.add_requested.connect(self._on_section_add)
            card.set_manual_enabled(self._manual_enabled)
            self._section_cards[key] = card
            self._section_order.append(card)
        lay.addWidget(self._sections_grid_widget)
        self._relayout_sections()

        self._apply_text_styles()
        self._load_tasks()
        QTimer.singleShot(0, self._relayout_sections)

    def _relayout_sections(self):
        if not hasattr(self, "_sections_grid"):
            return
        while self._sections_grid.count():
            item = self._sections_grid.takeAt(0)
            w = item.widget()
            if w:
                self._sections_grid.removeWidget(w)
        width = self._sections_grid_widget.width() if hasattr(self, "_sections_grid_widget") else self.width()
        cols = 3 if width >= 900 else 2 if width >= 680 else 1
        for c in range(3):
            self._sections_grid.setColumnStretch(c, 1 if c < cols else 0)
        for idx, card in enumerate(self._section_order):
            self._sections_grid.addWidget(card, idx // cols, idx % cols)

    def _compact_task_check(self, cb: NMCustomCheck) -> NMCustomCheck:
        cb.setMinimumHeight(28)
        cb.setMaximumHeight(30)
        cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = cb.layout()
        if layout is not None:
            layout.setContentsMargins(0, 2, 0, 2)
            layout.setSpacing(6)
        label = getattr(cb, "_label", None)
        if label is not None:
            label.setWordWrap(False)
            label.setFont(qfont("size_caption"))
        return cb

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_sections()

    def _apply_text_styles(self):
        pass  # Manejado internamente por las cards

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_hero_card"):
            self._hero_card._modo = self._modo
            self._hero_card._apply_theme(self._modo)
        # Re-check estilos de cada checkbox (asegurar)
        for tid, cb in getattr(self, "_task_checks", {}).items():
            done = self._task_done.get(tid, False)
            try:
                cb.set_checked(done)
            except Exception:
                pass
        self.update()

    # ── load tasks (lógica preservada exacta) ────────────────────────────────

    def _load_tasks(self):
        self._rutina_modo = _rutina_modo()
        self._manual_enabled = self._rutina_modo != "solo_profesional"
        if hasattr(self, "_hero_card"):
            self._hero_card.set_manual_enabled(self._manual_enabled)
        for card in self._section_cards.values():
            card.set_manual_enabled(self._manual_enabled)
        self._task_checks.clear()
        self._task_done.clear()
        self._task_section.clear()

        # Limpiar bodies
        for key, card in self._section_cards.items():
            layout = card.body_layout()
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    layout.removeWidget(w)
                    w.deleteLater()

        if visual_qa_enabled():
            self._load_visual_qa_tasks()
            return

        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            for key, _, _, _ in SECCIONES:
                if self._rutina_modo == "solo_profesional":
                    tareas = conn.execute(
                        "SELECT id, descripcion, COALESCE(origen, 'manual') AS origen "
                        "FROM checklist_tareas "
                        "WHERE seccion = ? AND COALESCE(origen, 'manual') <> 'manual' "
                        "ORDER BY orden",
                        (key,),
                    ).fetchall()
                else:
                    tareas = conn.execute(
                        "SELECT id, descripcion, COALESCE(origen, 'manual') AS origen "
                        "FROM checklist_tareas WHERE seccion = ? ORDER BY orden",
                        (key,),
                    ).fetchall()

                completadas = set()
                if tareas:
                    ids = [str(t["id"]) for t in tareas]
                    rows = conn.execute(
                        f"SELECT tarea_id FROM checklist_completadas "
                        f"WHERE fecha = ? AND tarea_id IN ({','.join('?' * len(ids))})",
                        [hoy] + [int(i) for i in ids],
                    ).fetchall()
                    completadas = {r["tarea_id"] for r in rows}

                card = self._section_cards[key]
                layout = card.body_layout()
                seen_ids: set[int] = set()
                for tarea in tareas:
                    tid = tarea["id"]
                    if tid in seen_ids:
                        continue
                    seen_ids.add(tid)
                    done = tid in completadas
                    self._task_done[tid] = done
                    self._task_section[tid] = key
                    cb = self._compact_task_check(
                        NMCustomCheck(tarea["descripcion"], checked=done, modo=self._modo)
                    )
                    cb.toggled.connect(
                        lambda state, t=tid, checkbox=cb: self._on_check(t, checkbox)
                    )
                    self._add_task_row(layout, cb, tarea["origen"] == "manual")
                    self._task_checks[tid] = cb

                done_count = sum(1 for t in tareas if t["id"] in completadas)
                total = len(tareas)
                card.set_progress(done_count, total)
            conn.close()
        except Exception:
            _log.exception("Operation failed")

        self._refresh_hero()
        has_tasks = bool(self._task_checks)
        self._hero_card.setVisible(has_tasks)
        self._empty_state.setVisible(not has_tasks)
        for card in self._section_cards.values():
            card.setVisible(has_tasks)
        QTimer.singleShot(0, self._relayout_sections)

    def _add_task_row(self, layout, cb, is_manual: bool):
        """Agrega una tarea sin exponer el origen paciente/profesional en la UI."""
        layout.addWidget(cb)

    def _load_visual_qa_tasks(self):
        # Idempotencia defensiva: aunque _load_tasks() ya limpia, este método
        # puede invocarse desde otros contextos. Garantizamos un estado limpio
        # antes de poblar para que llamadas repetidas no dupliquen items.
        self._task_checks.clear()
        self._task_done.clear()
        self._task_section.clear()
        for _key, _card in self._section_cards.items():
            _layout = _card.body_layout()
            while _layout.count():
                _item = _layout.takeAt(0)
                _w = _item.widget()
                if _w:
                    _w.setParent(None)
                    _layout.removeWidget(_w)
                    _w.deleteLater()

        fixtures = routine_sections()
        for key, _, _, _ in SECCIONES:
            tareas = fixtures.get(key, [])
            card = self._section_cards[key]
            layout = card.body_layout()
            seen_ids: set[int] = set()
            for tarea in tareas:
                tid = int(tarea["id"])
                if tid in seen_ids:  # dedup-by-id por si la fixture trae duplicados
                    continue
                seen_ids.add(tid)
                done = bool(tarea.get("done"))
                self._task_done[tid] = done
                self._task_section[tid] = key
                cb = self._compact_task_check(
                    NMCustomCheck(tarea["descripcion"], checked=done, modo=self._modo)
                )
                cb.toggled.connect(lambda state, t=tid, checkbox=cb: self._on_check(t, checkbox))
                self._add_task_row(layout, cb, str(tarea.get("origen", "")) == "manual")
                self._task_checks[tid] = cb
            done_count = sum(1 for t in tareas if t.get("done"))
            total = len(tareas)
            card.set_progress(done_count, total)
        self._refresh_hero()
        has_tasks = bool(self._task_checks)
        self._hero_card.setVisible(has_tasks)
        self._empty_state.setVisible(not has_tasks)
        for card in self._section_cards.values():
            card.setVisible(has_tasks)
        QTimer.singleShot(0, self._relayout_sections)

    # ── on_check (lógica preservada) ─────────────────────────────────────────

    def _on_check(self, tarea_id: int, checkbox: NMCustomCheck):
        checked = checkbox.isChecked()
        if not checked:
            # Una tarea completada NO se desmarca el mismo día (decisión owner
            # v1.0): el registro del día queda firme; mañana vuelve desmarcada
            # sola porque las completadas se guardan por fecha.
            checkbox.set_checked(True)  # set_checked no re-emite toggled
            NMToast.display(
                self.window(),
                "Completada por hoy · mañana se renueva",
                variant="info",
                duration_ms=2200,
            )
            return
        if visual_qa_enabled():
            self._task_done[tarea_id] = checked
            checkbox.set_checked(checked)
            self._refresh_hero()
            self._update_section_progress()
            return
        hoy = fecha_hoy()
        try:
            with conexion() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO checklist_completadas (tarea_id, fecha) VALUES (?, ?)",
                    (tarea_id, hoy),
                )
                NMToast.display(
                    self.window(), "Tarea completada", variant="success", duration_ms=1500
                )
            # Sonido de logro al completar un ítem (capacidad pedida por el
            # owner para Checklist de Rutina Diaria). Async, no bloquea la UI.
            try:
                from shared.sounds import play_achievement

                play_achievement()
            except Exception:
                pass
            try:
                from shared.sync import sync_inmediato_background

                sync_inmediato_background()
            except Exception:
                pass
        except Exception:
            _log.exception("Operation failed")

        self._task_done[tarea_id] = checked
        checkbox.set_checked(checked)
        self._refresh_hero()
        self._update_section_progress()

    # ── progress refresh ─────────────────────────────────────────────────────

    def _refresh_hero(self):
        total = len(self._task_done)
        done = sum(1 for v in self._task_done.values() if v)
        if hasattr(self, "_hero_card"):
            self._hero_card.set_progress(done, total)

    def _update_section_progress(self):
        if visual_qa_enabled():
            for key, _, _, _ in SECCIONES:
                ids = [tid for tid, s in self._task_section.items() if s == key]
                total = len(ids)
                done = sum(1 for tid in ids if self._task_done.get(tid))
                if key in self._section_cards:
                    self._section_cards[key].set_progress(done, total)
            return
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            for key, _, _, _ in SECCIONES:
                if key not in self._section_cards:
                    continue
                if getattr(self, "_rutina_modo", "mixto") == "solo_profesional":
                    tareas = conn.execute(
                        "SELECT id FROM checklist_tareas "
                        "WHERE seccion = ? AND COALESCE(origen, 'manual') <> 'manual'",
                        (key,),
                    ).fetchall()
                else:
                    tareas = conn.execute(
                        "SELECT id FROM checklist_tareas WHERE seccion = ?", (key,)
                    ).fetchall()
                total = len(tareas)
                if total == 0:
                    self._section_cards[key].set_progress(0, 0)
                    continue
                ids = [t["id"] for t in tareas]
                done = conn.execute(
                    f"SELECT COUNT(*) FROM checklist_completadas "
                    f"WHERE fecha = ? AND tarea_id IN ({','.join('?' * len(ids))})",
                    [hoy] + ids,
                ).fetchone()[0]
                self._section_cards[key].set_progress(done, total)
            conn.close()
        except Exception:
            _log.exception("Operation failed")

    # ── add task (lógica preservada) ─────────────────────────────────────────

    def _on_section_add(self, seccion_key: str):
        """Click en '+ Agregar tarea' de una card de sección."""
        try:
            if not getattr(self, "_manual_enabled", True):
                return
            card = self._section_cards.get(seccion_key)
            if card is None:
                return
            card.show_add_inline(self._add_task)
        except Exception as e:
            _log.error(redact(f"Error in _on_section_add: {e}"))
            import traceback

            traceback.print_exc()

    def _add_task(self, seccion: str, descripcion: str, save_button=None):
        descripcion = descripcion.strip()
        if not descripcion:
            return
        if not getattr(self, "_manual_enabled", True):
            return
        if visual_qa_enabled():
            self._load_tasks()
            return
        try:
            with conexion() as conn:
                max_orden = conn.execute(
                    "SELECT COALESCE(MAX(orden), 0) FROM checklist_tareas WHERE seccion = ?",
                    (seccion,),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO checklist_tareas (seccion, descripcion, orden, origen) "
                    "VALUES (?, ?, ?, 'manual')",
                    (seccion, descripcion, max_orden + 1),
                )
            if save_button is not None and hasattr(save_button, "play_success"):
                save_button.play_success()
        except Exception:
            _log.exception("Operation failed")
        self._load_tasks()

    # ── Hooks NMModule ───────────────────────────────────────────────────────

    def on_enter(self):
        self._load_tasks()

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "8/10"
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            if _rutina_modo() == "solo_profesional":
                total = conn.execute(
                    "SELECT COUNT(*) FROM checklist_tareas "
                    "WHERE COALESCE(origen, 'manual') <> 'manual'"
                ).fetchone()[0]
                done = conn.execute(
                    "SELECT COUNT(*) FROM checklist_completadas cc "
                    "JOIN checklist_tareas ct ON cc.tarea_id = ct.id "
                    "WHERE cc.fecha = ? AND COALESCE(ct.origen, 'manual') <> 'manual'",
                    (hoy,),
                ).fetchone()[0]
            else:
                total = conn.execute("SELECT COUNT(*) FROM checklist_tareas").fetchone()[0]
                done = conn.execute(
                    "SELECT COUNT(*) FROM checklist_completadas WHERE fecha = ?", (hoy,)
                ).fetchone()[0]
            conn.close()
            if total > 0:
                return f"{done}/{total}"
        except Exception:
            _log.exception("Operation failed")
        return ""
