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
  get_card_status(), schema DB (checklist_tareas, checklist_completadas,
  checklist_notas_dia), winsound.Beep al completar tarea.
"""

import os
import sys
import logging
import datetime as _dt

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit, QSizePolicy, QGridLayout,
)
from PyQt6.QtGui import QColor

try:
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMCard, NMIcon, NMModuleRing, NMDayNote,
        NMCustomCheck, NMEmptyState, NMProgressLine,
        responsive_columns,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, leer_config
    from shared.utils import fecha_hoy
    from shared.visual_qa import visual_qa_enabled, routine_sections
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMCard, NMIcon, NMModuleRing, NMDayNote,
        NMCustomCheck, NMEmptyState, NMProgressLine,
        responsive_columns,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, leer_config
    from shared.utils import fecha_hoy
    from shared.visual_qa import visual_qa_enabled, routine_sections


# ── Constantes preservadas ───────────────────────────────────────────────────

# v3: SVG icons en lugar de fa5s
SECCIONES = [
    ("manana", "Mañana", "sun"),
    ("tarde",  "Tarde",  "spark"),
    ("noche",  "Noche",  "moon"),
]


# ── _HeroDayCard ─────────────────────────────────────────────────────────────

RUTINA_MODOS = {"solo_profesional", "mixto", "solo_paciente"}


def _rutina_modo() -> str:
    try:
        modo = leer_config("rutina_modo", "mixto").strip()
    except Exception:
        modo = "mixto"
    return modo if modo in RUTINA_MODOS else "mixto"


class _HeroDayCard(NMCard):
    """Hero v3: ring 120 del progreso del día + título + descripción + CTA."""

    new_task_requested = pyqtSignal()

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._done = 0
        self._total = 0
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["xxl"], V3_SP["xl"],
                                V3_SP["xxl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["xl"])

        self._ring = NMModuleRing(size=120, pct=0.0, modo=self._modo)
        lay.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(4)
        self._eyebrow = QLabel("PROGRESO DEL DÍA")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._eyebrow)
        self._title_lbl = QLabel("Sin tareas configuradas")
        self._title_lbl.setFont(qfont("size_h2",
                                       weight=TYPOGRAPHY["weight_bold"]))
        col.addWidget(self._title_lbl)
        self._desc_lbl = QLabel("Tu rutina se va construyendo paso a paso.")
        self._desc_lbl.setFont(qfont("size_small"))
        self._desc_lbl.setWordWrap(True)
        col.addWidget(self._desc_lbl)
        col.addStretch()
        lay.addLayout(col, stretch=1)

        self._cta = NMButton("Nueva tarea", variant="gradient",
                              size="md", modo=self._modo, width=160)
        self._cta.clicked.connect(lambda _=False: self.new_task_requested.emit())
        lay.addWidget(self._cta, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._apply_hero_styles()

    def set_progress(self, done: int, total: int):
        self._done = done
        self._total = total
        if total > 0:
            pct = done / total
            self._ring.set_pct(pct)
            self._title_lbl.setText(f"{done} de {total} tareas completadas")
            self._desc_lbl.setText(
                f"{int(pct * 100)}% del día completado." if pct < 1.0
                else "¡Excelente! Rutina del día completa.")
        else:
            self._ring.set_pct(0.0)
            self._title_lbl.setText("Sin tareas configuradas")
            self._desc_lbl.setText(
                "Agregá una primera tarea para empezar tu rutina.")

    def set_manual_enabled(self, enabled: bool):
        self._cta.setVisible(enabled)

    def _apply_hero_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;")

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

    add_requested = pyqtSignal(str)   # emite la key de sección

    def __init__(self, key: str, label: str, icon_name: str,
                 modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._key = key
        self._label = label
        self._icon_name = icon_name
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["lg"])

        head = QHBoxLayout()
        head.setSpacing(V3_SP["md"])
        self._icon = NMIcon(self._icon_name, size=24, color_key="teal",
                             modo=self._modo)
        head.addWidget(self._icon)
        self._title = QLabel(self._label)
        self._title.setFont(qfont("size_h3",
                                   weight=TYPOGRAPHY["weight_semibold"]))
        head.addWidget(self._title)
        head.addStretch()
        self._count_lbl = QLabel("0/0")
        self._count_lbl.setFont(qfont_mono(10, bold=False))
        head.addWidget(self._count_lbl)
        self._ring = NMModuleRing(size=40, pct=0.0, modo=self._modo)
        head.addWidget(self._ring)
        lay.addLayout(head)

        # Body: layout vertical para tareas
        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(V3_SP["xs"])
        self._body_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.addWidget(self._body, stretch=1)

        # Footer: botón ghost "+ Agregar tarea"
        self._add_btn = NMButton("+ Agregar tarea", variant="ghost",
                                  size="sm", modo=self._modo, width=0)
        self._add_btn.clicked.connect(
            lambda: self.add_requested.emit(self._key))
        lay.addWidget(self._add_btn)

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
        """Inserta una fila inline (input + botón check) al final del body."""
        try:
            _log.debug(f"show_add_inline called, modo={getattr(self, '_modo', 'N/A')}")
            form = QFrame()
            form.setObjectName("AddForm")
            form_lay = QHBoxLayout(form)
            form_lay.setContentsMargins(V3_SP["sm"], V3_SP["sm"],
                                         V3_SP["sm"], V3_SP["sm"])
            form_lay.setSpacing(V3_SP["md"])
            entry = QLineEdit()
            entry.setPlaceholderText("Nueva tarea…")
            entry.setFont(qfont("size_body"))
            entry.setFixedHeight(32)
            entry.setStyleSheet(
                f"QLineEdit {{ background: {v3c('bg', self._modo).name()}; "
                f"color: {v3c('text', self._modo).name()}; "
                f"border: 1px solid {v3c('borderStrong', self._modo).name()}; "
                f"border-radius: 8px; padding: 0 8px; }}"
                f"QLineEdit:focus {{ border-color: "
                f"{v3c('teal', self._modo).name()}; }}")
            form_lay.addWidget(entry, stretch=1)
            btn = NMButton("✓", variant="gradient", size="sm",
                            modo=self._modo, width=36)
            form_lay.addWidget(btn)

            form.setStyleSheet(
                f"#AddForm {{ background: {v3c('borderSoft', self._modo).name()}; "
                f"border-radius: 10px; }}")
            self._body_lay.addWidget(form)
            entry.setFocus()

            def _commit():
                txt = entry.text().strip()
                if not txt:
                    return
                self._body_lay.removeWidget(form)
                form.deleteLater()
                on_save(self._key, txt, btn)

            btn.clicked.connect(_commit)
            entry.returnPressed.connect(_commit)
        except Exception as e:
            _log.error(f"Error in show_add_inline: {e}")
            import traceback
            traceback.print_exc()

    # ── styles / theme ───────────────────────────────────────────────────────

    def _apply_section_styles(self):
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        self._count_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")

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
    MODULE_ICON  = "rutina"

    def build_ui(self):
        self._rutina_modo = _rutina_modo()
        self._manual_enabled = self._rutina_modo != "solo_profesional"
        self._task_checks: dict[int, NMCustomCheck] = {}
        self._task_done:   dict[int, bool] = {}
        self._task_section: dict[int, str] = {}
        self._section_cards: dict[str, _SectionCard] = {}

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(scroll)
        self._scroll = scroll

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        scroll.setWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["lg"])

        # 1. Hero Day Card (Ring grande del día)
        self._hero_card = _HeroDayCard(modo=self._modo)
        self._hero_card.new_task_requested.connect(self._on_new_task_hero)
        self._hero_card.set_manual_enabled(self._manual_enabled)
        lay.addWidget(self._hero_card)

        # 2. Empty state (oculta cuando hay tareas)
        self._empty_state = NMEmptyState(
            "fa5s.list-check",
            "Sin rutina asignada",
            "Tu terapeuta te enviará actividades pronto, o podés agregarlas "
            "vos manualmente con el botón de cada sección.",
            parent=body,
        )
        self._empty_state.hide()
        lay.addWidget(self._empty_state)

        # 4. Grid responsive de _SectionCard
        self._sections_grid_widget = QWidget()
        self._sections_grid_widget.setStyleSheet("background: transparent;")
        self._sections_grid = QGridLayout(self._sections_grid_widget)
        self._sections_grid.setContentsMargins(0, 0, 0, 0)
        self._sections_grid.setHorizontalSpacing(V3_SP["md"])
        self._sections_grid.setVerticalSpacing(V3_SP["md"])
        self._section_order: list[_SectionCard] = []
        for key, label, icon_name in SECCIONES:
            card = _SectionCard(key, label, icon_name, modo=self._modo)
            card.add_requested.connect(self._on_section_add)
            card.set_manual_enabled(self._manual_enabled)
            self._section_cards[key] = card
            self._section_order.append(card)
        lay.addWidget(self._sections_grid_widget)
        self._relayout_sections()

        # 5. Nota del día (NMDayNote ya existente)
        self._build_nota_dia(lay)

        self._apply_text_styles()
        self._load_tasks()

    def _relayout_sections(self):
        if not hasattr(self, "_sections_grid"):
            return
        while self._sections_grid.count():
            item = self._sections_grid.takeAt(0)
            w = item.widget()
            if w:
                self._sections_grid.removeWidget(w)
        width = max(
            360,
            self._scroll.viewport().width() if hasattr(self, "_scroll") else self.width(),
        )
        cols = responsive_columns(width, min_card_width=330, max_columns=3)
        for idx, card in enumerate(self._section_order):
            self._sections_grid.addWidget(card, idx // cols, idx % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_sections()

    def _apply_text_styles(self):
        pass  # Manejado internamente por las cards

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_nota_txt") and self._nota_txt is not None:
            try:
                self._nota_txt.setStyleSheet(stylesheet_textedit(self._modo))
            except Exception:
                pass
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
                    layout.removeWidget(w)
                    w.deleteLater()

        if visual_qa_enabled():
            self._load_visual_qa_tasks()
            return

        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            for key, _, _ in SECCIONES:
                if self._rutina_modo == "solo_profesional":
                    tareas = conn.execute(
                        "SELECT id, descripcion, COALESCE(origen, 'manual') AS origen "
                        "FROM checklist_tareas "
                        "WHERE seccion = ? AND COALESCE(origen, 'manual') <> 'manual' "
                        "ORDER BY orden",
                        (key,)
                    ).fetchall()
                else:
                    tareas = conn.execute(
                        "SELECT id, descripcion, COALESCE(origen, 'manual') AS origen "
                        "FROM checklist_tareas WHERE seccion = ? ORDER BY orden",
                        (key,)
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
                    cb = NMCustomCheck(tarea["descripcion"],
                                        checked=done, modo=self._modo)
                    cb.setEnabled(not done)
                    cb.toggled.connect(
                        lambda state, t=tid, checkbox=cb: self._on_check(t, checkbox))
                    if tarea["origen"] == "manual":
                        row = QWidget()
                        row.setStyleSheet("background: transparent;")
                        row_lay = QHBoxLayout(row)
                        row_lay.setContentsMargins(0, 0, 0, 0)
                        row_lay.setSpacing(V3_SP["xs"])
                        row_lay.addWidget(cb, stretch=1)
                        badge = QLabel("Personal")
                        badge.setFont(qfont("size_caption_xs",
                                             weight=TYPOGRAPHY["weight_semibold"]))
                        badge.setContentsMargins(V3_SP["sm"], 2, V3_SP["sm"], 2)
                        badge.setStyleSheet(
                            f"color: {v3c('text3', self._modo).name()}; "
                            f"border: 1px solid {v3c('borderSoft', self._modo).name()}; "
                            "border-radius: 8px; background: transparent;"
                        )
                        row_lay.addWidget(badge)
                        layout.addWidget(row)
                    else:
                        layout.addWidget(cb)
                    self._task_checks[tid] = cb

                done_count = sum(1 for t in tareas if t["id"] in completadas)
                total = len(tareas)
                card.set_progress(done_count, total)
            conn.close()
        except Exception:
            _log.exception("Operation failed")

        self._refresh_hero()
        has_tasks = bool(self._task_checks)
        self._empty_state.setVisible(not has_tasks)
        for card in self._section_cards.values():
            card.setVisible(has_tasks)

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
                    _layout.removeWidget(_w)
                    _w.deleteLater()

        fixtures = routine_sections()
        for key, _, _ in SECCIONES:
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
                cb = NMCustomCheck(tarea["descripcion"],
                                    checked=done, modo=self._modo)
                cb.toggled.connect(
                    lambda state, t=tid, checkbox=cb: self._on_check(t, checkbox))
                layout.addWidget(cb)
                self._task_checks[tid] = cb
            done_count = sum(1 for t in tareas if t.get("done"))
            total = len(tareas)
            card.set_progress(done_count, total)
        self._refresh_hero()
        has_tasks = bool(self._task_checks)
        self._empty_state.setVisible(not has_tasks)
        for card in self._section_cards.values():
            card.setVisible(has_tasks)

    # ── on_check (lógica preservada) ─────────────────────────────────────────

    def _on_check(self, tarea_id: int, checkbox: NMCustomCheck):
        checked = checkbox.isChecked()
        if visual_qa_enabled():
            self._task_done[tarea_id] = checked
            checkbox.set_checked(checked)
            self._refresh_hero()
            self._update_section_progress()
            return
        hoy = fecha_hoy()
        try:
            conn = obtener_conexion()
            if checked:
                conn.execute(
                    "INSERT OR IGNORE INTO checklist_completadas "
                    "(tarea_id, fecha) VALUES (?, ?)",
                    (tarea_id, hoy),
                )
                checkbox.setEnabled(False)
                self._play_beep()
                NMToast.display(self.window(), "Tarea completada",
                                 variant="success", duration_ms=1500)
            else:
                conn.execute(
                    "DELETE FROM checklist_completadas "
                    "WHERE tarea_id = ? AND fecha = ?",
                    (tarea_id, hoy),
                )
            conn.commit()
            conn.close()
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

    def _play_beep(self):
        try:
            import winsound
            winsound.Beep(1200, 80)
        except Exception:
            _log.exception("Operation failed")

    # ── progress refresh ─────────────────────────────────────────────────────

    def _refresh_hero(self):
        total = len(self._task_done)
        done = sum(1 for v in self._task_done.values() if v)
        if hasattr(self, "_hero_card"):
            self._hero_card.set_progress(done, total)

    def _update_section_progress(self):
        if visual_qa_enabled():
            for key, _, _ in SECCIONES:
                ids = [tid for tid, s in self._task_section.items() if s == key]
                total = len(ids)
                done = sum(1 for tid in ids if self._task_done.get(tid))
                if key in self._section_cards:
                    self._section_cards[key].set_progress(done, total)
            return
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            for key, _, _ in SECCIONES:
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
            _log.error(f"Error in _on_section_add: {e}")
            import traceback
            traceback.print_exc()

    def _on_new_task_hero(self):
        """Click en CTA del hero: añadir a la sección horaria actual."""
        if not getattr(self, "_manual_enabled", True):
            return
        hour = _dt.datetime.now().hour
        if hour < 12:
            key = "manana"
        elif hour < 19:
            key = "tarde"
        else:
            key = "noche"
        self._on_section_add(key)

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
            conn = obtener_conexion()
            max_orden = conn.execute(
                "SELECT COALESCE(MAX(orden), 0) FROM checklist_tareas WHERE seccion = ?",
                (seccion,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO checklist_tareas (seccion, descripcion, orden, origen) "
                "VALUES (?, ?, ?, 'manual')",
                (seccion, descripcion, max_orden + 1),
            )
            conn.commit()
            conn.close()
            if save_button is not None and hasattr(save_button, "play_success"):
                save_button.play_success()
        except Exception:
            _log.exception("Operation failed")
        self._load_tasks()

    # ── nota del día (lógica preservada) ─────────────────────────────────────

    def _build_nota_dia(self, parent_layout: QVBoxLayout):
        existing_note: str | None = None
        if visual_qa_enabled():
            existing_note = "Día estable, energía alta y buena adherencia a la rutina."
        else:
            try:
                conn = obtener_conexion()
                row = conn.execute(
                    "SELECT nota FROM checklist_notas_dia WHERE fecha = ?",
                    (fecha_hoy(),)
                ).fetchone()
                conn.close()
                if row and row[0]:
                    existing_note = row[0]
            except Exception:
                _log.exception("Operation failed")

        locked = existing_note is not None
        lock_reason = "Nota guardada para hoy" if locked else ""

        self._day_note = NMDayNote(
            locked=locked, lock_reason=lock_reason, modo=self._modo)
        if existing_note:
            self._day_note.set_note(existing_note)
        self._day_note.note_changed.connect(self._guardar_nota_text)
        # Compatibilidad con _on_theme: nombrar attribute si el día_note expone textarea
        self._nota_txt = getattr(self._day_note, "_text", None)
        parent_layout.addWidget(self._day_note)

    def _guardar_nota_text(self, text: str):
        nota = text.strip()
        if not nota:
            return
        if visual_qa_enabled():
            if hasattr(self, "_day_note"):
                self._day_note.set_locked(True, "Nota guardada para hoy")
            NMToast.display(self.window(), "Nota guardada en demo visual",
                             variant="success", duration_ms=1600)
            return
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO checklist_notas_dia (fecha, nota) VALUES (?, ?) "
                "ON CONFLICT(fecha) DO UPDATE SET nota = excluded.nota",
                (fecha_hoy(), nota),
            )
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Operation failed")
            return
        if hasattr(self, "_day_note"):
            self._day_note.set_locked(True, "Nota guardada para hoy")
        NMToast.display(self.window(), "Nota guardada",
                         variant="success", duration_ms=2000)

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
                    (hoy,)
                ).fetchone()[0]
            else:
                total = conn.execute(
                    "SELECT COUNT(*) FROM checklist_tareas"
                ).fetchone()[0]
                done = conn.execute(
                    "SELECT COUNT(*) FROM checklist_completadas WHERE fecha = ?",
                    (hoy,)
                ).fetchone()[0]
            conn.close()
            if total > 0:
                return f"{done}/{total}"
        except Exception:
            _log.exception("Operation failed")
        return ""
