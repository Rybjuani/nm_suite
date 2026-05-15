"""
app/modules/rutina_qt.py — Checklist de rutina diaria (PyQt6)

LÓGICA PRESERVADA EXACTA:
  SECCIONES, _load_tasks(), _on_check(), _add_task(), _guardar_nota(),
  get_card_status()
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt, QTimer,
)
from PyQt6.QtGui import (
    QColor, QFont,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QTextEdit, QLineEdit, QSizePolicy,
    QPushButton,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMProgressBar, NMToast,
        ThemeManager, h_spacer, NMEmptyState, NMRoutineSection, NMDayNote,
        NMCustomCheck,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor, nm_icon,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
        RADIUS_INPUT, RADIUS_SMALL,
        stylesheet_textedit, stylesheet_scrollarea,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMProgressBar, NMToast,
        ThemeManager, h_spacer, NMEmptyState, NMRoutineSection, NMDayNote,
        NMCustomCheck,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor, nm_icon,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
        RADIUS_INPUT, RADIUS_SMALL,
        stylesheet_textedit, stylesheet_scrollarea,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy


# ── Secciones (preservadas exactas) ──────────────────────────────────────────

SECCIONES = [
    ("manana", "Mañana", "fa5s.sun"),
    ("tarde",  "Tarde",  "fa5s.cloud-sun"),
    ("noche",  "Noche",  "fa5s.moon"),
]

# Maps SECCIONES key → NMRoutineSection section_type
_SECTION_TYPE = {
    "manana": "morning",
    "tarde":  "afternoon",
    "noche":  "night",
}


# ── ModuloRutina ──────────────────────────────────────────────────────────────

class ModuloRutina(NMModule):
    MODULE_TITLE = "Rutina"
    MODULE_ICON  = "rutina"

    def build_ui(self):
        self._section_collapsed: dict[str, bool] = {}
        self._section_bodies:    dict[str, QWidget] = {}
        self._section_progs:     dict[str, NMProgressBar] = {}
        self._section_count_lbl: dict[str, QLabel] = {}
        self._section_frames:    dict[str, QFrame] = {}
        self._task_checks:       dict[int, NMCustomCheck] = {}  # tarea_id → row
        self._task_done:         dict[int, bool] = {}       # tarea_id → bool

        c = colors(self._modo)

        # ── Root layout inside self._content ─────────────────────────────────
        root = QVBoxLayout(self._content)
        root.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                PAD_CONTAINER, PAD_CONTAINER)
        root.setSpacing(sp("sm"))

        # Badge summary
        self._badge_lbl = QLabel("Sin tareas configuradas")
        self._badge_lbl.setFont(qfont("size_body", bold=True))
        self._badge_lbl.setStyleSheet(
            f"color: {c['accent']}; background: transparent;"
        )
        root.addWidget(self._badge_lbl)
        root.addSpacing(10)

        # ── Scroll area ───────────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, sp("sm"), 0)
        self._scroll_layout.setSpacing(GAP_CARDS)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._scroll_content)
        root.addWidget(self._scroll)

        # ── Build section frames ──────────────────────────────────────────────
        self._empty_state = NMEmptyState(
            "fa5s.list-check",
            "Sin rutina asignada",
            "Tu terapeuta te enviará actividades pronto.",
            self._scroll_content,
        )
        self._empty_state.hide()
        self._scroll_layout.addWidget(self._empty_state)

        for key, label, icon in SECCIONES:
            self._build_section(key, label, icon)

        # ── Nota del día ──────────────────────────────────────────────────────
        self._build_nota_dia()

        # ── Load tasks ────────────────────────────────────────────────────────
        self._load_tasks()

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_nota_txt"):
            self._nota_txt.setStyleSheet(stylesheet_textedit(self._modo))
        for prog in getattr(self, "_section_progs", {}).values():
            prog._apply_theme(self._modo)
        # Re-aplicar estilos a todos los checkboxes
        for tid, cb in getattr(self, "_task_checks", {}).items():
            done = self._task_done.get(tid, False)
            cb.set_checked(done)
        self.update()

    # ── Section building ─────────────────────────────────────────────────────

    def _build_section(self, key: str, label: str, icon: str):
        c = colors(self._modo)
        section_type = _SECTION_TYPE.get(key, "morning")

        # Premium collapsible section with tinted gradient header
        sec = NMRoutineSection(section_type, label, modo=self._modo,
                               parent=self._scroll_content)
        self._section_frames[key] = sec  # stored for visibility toggle in _load_tasks

        cl = sec.content_layout()

        # Count + add-task row inside content area
        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(sp("sm"))

        count_lbl = QLabel("")
        count_lbl.setFont(qfont("size_small"))
        count_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        self._section_count_lbl[key] = count_lbl
        controls_row.addWidget(count_lbl)

        controls_row.addStretch()

        add_btn = NMButton("+", modo=self._modo, width=30, height=30)
        add_btn.clicked.connect(lambda checked=False, k=key: self._show_add_form(k))
        controls_row.addWidget(add_btn)
        cl.addLayout(controls_row)

        # Thin progress bar
        prog = NMProgressBar(height=4, modo=self._modo)
        cl.addWidget(prog)
        self._section_progs[key] = prog

        # Task body — plain widget that _load_tasks populates
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, sp("xs") // 2, 0, 0)
        body_layout.setSpacing(sp("xs") // 2)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        cl.addWidget(body)
        self._section_bodies[key] = body

        self._scroll_layout.addWidget(sec)

    # ── Load tasks from DB (lógica preservada exacta) ────────────────────────

    def _load_tasks(self):
        self._task_checks.clear()
        self._task_done.clear()

        # Clear existing task widgets in each section
        for key in self._section_bodies:
            body = self._section_bodies[key]
            layout = body.layout()
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    layout.removeWidget(w)
                    w.deleteLater()

        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()

            for key, _, _ in SECCIONES:
                tareas = conn.execute(
                    "SELECT id, descripcion FROM checklist_tareas "
                    "WHERE seccion = ? ORDER BY orden",
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

                body = self._section_bodies[key]
                layout = body.layout()
                c = colors(self._modo)

                for tarea in tareas:
                    tid = tarea["id"]
                    done = tid in completadas
                    self._task_done[tid] = done

                    cb = NMCustomCheck(tarea["descripcion"], checked=done, modo=self._modo)
                    cb.setEnabled(not done)
                    cb.toggled.connect(
                        lambda state, t=tid, checkbox=cb: self._on_check(t, checkbox)
                    )
                    layout.addWidget(cb)
                    self._task_checks[tid] = cb

                # Update section count label and progress bar
                done_count = sum(1 for t in tareas if t["id"] in completadas)
                total = len(tareas)
                count_lbl = self._section_count_lbl[key]
                count_lbl.setText(f"{done_count}/{total}" if total > 0 else "")
                if key in self._section_progs and total > 0:
                    self._section_progs[key].animate_to(done_count / total)
                elif key in self._section_progs:
                    self._section_progs[key].animate_to(0.0)

            conn.close()
        except Exception:
            _log.exception("Operation failed")

        self._update_badge()
        has_tasks = bool(self._task_checks)
        if hasattr(self, "_empty_state"):
            self._empty_state.setVisible(not has_tasks)
        for frame in getattr(self, "_section_frames", {}).values():
            frame.setVisible(has_tasks)

    # ── on_check (lógica preservada exacta) ─────────────────────────────────

    def _on_check(self, tarea_id: int, checkbox: NMCustomCheck):
        checked = checkbox.isChecked()
        hoy = fecha_hoy()
        try:
            conn = obtener_conexion()
            if checked:
                conn.execute(
                    "INSERT OR IGNORE INTO checklist_completadas "
                    "(tarea_id, fecha) VALUES (?, ?)",
                    (tarea_id, hoy),
                )
                checkbox.setEnabled(False)  # deshabilitar hasta el día siguiente
                self._play_beep()
                top = self.window()
                NMToast.display(top, "Tarea completada ✔", variant="success", duration_ms=1500)
            else:
                conn.execute(
                    "DELETE FROM checklist_completadas "
                    "WHERE tarea_id = ? AND fecha = ?",
                    (tarea_id, hoy),
                )
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Operation failed")

        self._task_done[tarea_id] = checked
        # Update checkbox style for line-through effect
        checkbox.set_checked(checked)
        self._update_badge()
        self._update_section_progress()

    def _play_beep(self):
        try:
            import winsound
            winsound.Beep(1200, 80)
        except Exception:
            _log.exception("Operation failed")

    def _update_badge(self):
        total = len(self._task_done)
        done  = sum(1 for v in self._task_done.values() if v)
        c = colors(self._modo)
        if total > 0:
            self._badge_lbl.setText(f"{done}/{total} completadas")
        else:
            self._badge_lbl.setText("Sin tareas configuradas")

    def _update_section_progress(self):
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            for key, _, _ in SECCIONES:
                if key not in self._section_progs:
                    continue
                tareas = conn.execute(
                    "SELECT id FROM checklist_tareas WHERE seccion = ?", (key,)
                ).fetchall()
                total = len(tareas)
                if total == 0:
                    self._section_progs[key].animate_to(0.0)
                    if key in self._section_count_lbl:
                        self._section_count_lbl[key].setText("")
                    continue
                ids = [t["id"] for t in tareas]
                done = conn.execute(
                    f"SELECT COUNT(*) FROM checklist_completadas "
                    f"WHERE fecha = ? AND tarea_id IN ({','.join('?' * len(ids))})",
                    [hoy] + ids,
                ).fetchone()[0]
                self._section_progs[key].animate_to(done / total)
                if key in self._section_count_lbl:
                    self._section_count_lbl[key].setText(f"{done}/{total}")
            conn.close()
        except Exception:
            _log.exception("Operation failed")

    # ── Add task inline form ──────────────────────────────────────────────────

    def _show_add_form(self, seccion: str):
        c = colors(self._modo)
        body = self._section_bodies[seccion]
        layout = body.layout()

        form = QFrame()
        form.setObjectName("AddForm")
        form.setStyleSheet(f"""
            QFrame#AddForm {{
                background-color: {c['bg_elevated']};
                border-radius: {RADIUS_INPUT}px;
                border: none;
            }}
        """)
        form_layout = QHBoxLayout(form)
        form_layout.setContentsMargins(sp("sm"), sp("sm") - sp("xs") // 2, sp("sm"), sp("sm") - sp("xs") // 2)
        form_layout.setSpacing(sp("sm") - sp("xs") // 2)

        entry = QLineEdit()
        entry.setPlaceholderText("Nueva tarea...")
        entry.setFont(qfont("size_body"))
        entry.setFixedHeight(32)
        entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_accent'] if 'border_accent' in c else c['accent']};
                border-radius: {RADIUS_SMALL}px;
                padding: 0 {sp('sm') + sp('xs') // 2}px;
            }}
            QLineEdit:focus {{
                border-color: {c['accent']};
            }}
        """)
        form_layout.addWidget(entry)

        btn_save = NMButton("✓", modo=self._modo, width=32, height=32)
        btn_save.clicked.connect(
            lambda: self._add_task(seccion, entry.text(), form, btn_save)
        )
        form_layout.addWidget(btn_save)

        entry.returnPressed.connect(
            lambda: self._add_task(seccion, entry.text(), form)
        )

        layout.addWidget(form)
        entry.setFocus()

    # ── _add_task (lógica preservada exacta) ─────────────────────────────────

    def _add_task(self, seccion: str, descripcion: str, form_widget: QWidget, save_button: QWidget | None = None):
        descripcion = descripcion.strip()
        if not descripcion:
            return
        try:
            conn = obtener_conexion()
            max_orden = conn.execute(
                "SELECT COALESCE(MAX(orden), 0) FROM checklist_tareas WHERE seccion = ?",
                (seccion,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO checklist_tareas (seccion, descripcion, orden) "
                "VALUES (?, ?, ?)",
                (seccion, descripcion, max_orden + 1),
            )
            conn.commit()
            conn.close()
            if save_button is not None and hasattr(save_button, "play_success"):
                save_button.play_success()
        except Exception:
            _log.exception("Operation failed")
        layout = form_widget.parentWidget().layout() if form_widget.parentWidget() else None
        if layout is not None:
            layout.removeWidget(form_widget)
        form_widget.deleteLater()
        self._load_tasks()

    # ── Nota del día ─────────────────────────────────────────────────────────

    def _build_nota_dia(self):
        # Check if note already saved today → locked state
        existing_note: str | None = None
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
        lock_reason = "Nota guardada para hoy ✓" if locked else ""

        self._day_note = NMDayNote(
            locked=locked, lock_reason=lock_reason,
            modo=self._modo, parent=self._scroll_content,
        )
        if existing_note:
            self._day_note.set_note(existing_note)
        self._day_note.note_changed.connect(self._guardar_nota_text)
        self._scroll_layout.addWidget(self._day_note)

    def _guardar_nota_text(self, text: str):
        """Called by NMDayNote.note_changed — saves note and locks the card."""
        nota = text.strip()
        if not nota:
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
            self._day_note.set_locked(True, "Nota guardada para hoy ✓")
        NMToast.display(self.window(), "Nota guardada ✓", variant="success", duration_ms=2000)

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._load_tasks()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
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
