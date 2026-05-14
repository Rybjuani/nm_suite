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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QScrollArea, QFrame, QTextEdit, QLineEdit, QSizePolicy,
    QPushButton,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMProgressBar, NMToast,
        ThemeManager, h_spacer,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
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
        ThemeManager, h_spacer,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
        stylesheet_textedit, stylesheet_scrollarea,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy


# ── Secciones (preservadas exactas) ──────────────────────────────────────────

SECCIONES = [
    ("manana", "Mañana", "🌅"),
    ("tarde",  "Tarde",  "☀️"),
    ("noche",  "Noche",  "🌙"),
]


# ── ModuloRutina ──────────────────────────────────────────────────────────────

class ModuloRutina(NMModule):
    MODULE_TITLE = "Rutina"
    MODULE_ICON  = "✅"

    def build_ui(self):
        self._section_collapsed: dict[str, bool] = {}
        self._section_bodies:    dict[str, QWidget] = {}
        self._section_progs:     dict[str, NMProgressBar] = {}
        self._section_count_lbl: dict[str, QLabel] = {}
        self._task_checks:       dict[int, QCheckBox] = {}  # tarea_id → QCheckBox
        self._task_done:         dict[int, bool] = {}       # tarea_id → bool

        c = colors(self._modo)

        # ── Root layout inside self._content ─────────────────────────────────
        root = QVBoxLayout(self._content)
        root.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                PAD_CONTAINER, PAD_CONTAINER)
        root.setSpacing(8)

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
        self._scroll_layout.setContentsMargins(0, 0, 8, 0)
        self._scroll_layout.setSpacing(GAP_CARDS)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._scroll_content)
        root.addWidget(self._scroll)

        # ── Build section frames ──────────────────────────────────────────────
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
            cb.setStyleSheet(self._checkbox_stylesheet(done))
        self.update()

    # ── Section building ─────────────────────────────────────────────────────

    def _build_section(self, key: str, label: str, icon: str):
        c = colors(self._modo)
        self._section_collapsed[key] = False

        # Card frame
        frame = QFrame()
        frame.setObjectName("SectionCard")
        frame.setStyleSheet(f"""
            QFrame#SectionCard {{
                background-color: {c['bg_surface']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 8, 12, 12)
        frame_layout.setSpacing(4)

        # Header row
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Clickable title button
        title_btn = QPushButton(f"{icon}  {label}")
        title_btn.setFont(qfont("size_h3", bold=True))
        title_btn.setFlat(True)
        title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        title_btn.setStyleSheet(f"""
            QPushButton {{
                color: {c['text_primary']};
                background: transparent;
                text-align: left;
                border: none;
                padding: 4px 0;
            }}
            QPushButton:hover {{
                color: {c['accent']};
            }}
        """)
        title_btn.clicked.connect(lambda checked=False, k=key: self._toggle_section(k))
        header_layout.addWidget(title_btn)

        # Count label
        count_lbl = QLabel("")
        count_lbl.setFont(qfont("size_small"))
        count_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        header_layout.addWidget(count_lbl)
        self._section_count_lbl[key] = count_lbl

        header_layout.addStretch()

        # Add button
        add_btn = QPushButton("+")
        add_btn.setFont(qfont("size_body", bold=True))
        add_btn.setFixedSize(30, 30)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                color: {c['text_primary']};
                background-color: {c['bg_elevated']};
                border-radius: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: {c['text_on_accent']};
            }}
        """)
        add_btn.clicked.connect(lambda checked=False, k=key: self._show_add_form(k))
        header_layout.addWidget(add_btn)

        frame_layout.addWidget(header)

        # Progress bar (4px)
        prog = NMProgressBar(height=4, modo=self._modo)
        frame_layout.addWidget(prog)
        self._section_progs[key] = prog

        # Body (task list)
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 4, 0, 0)
        body_layout.setSpacing(2)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        frame_layout.addWidget(body)
        self._section_bodies[key] = body

        self._scroll_layout.addWidget(frame)

    def _toggle_section(self, key: str):
        body = self._section_bodies[key]
        collapsed = self._section_collapsed[key]
        body.setVisible(collapsed)
        self._section_collapsed[key] = not collapsed

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
                if item.widget():
                    item.widget().deleteLater()

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

                    cb = QCheckBox(tarea["descripcion"])
                    cb.setFont(qfont("size_body"))
                    cb.setChecked(done)
                    cb.setEnabled(not done)
                    cb.setStyleSheet(self._checkbox_stylesheet(done))
                    cb.stateChanged.connect(
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

    def _checkbox_stylesheet(self, done: bool) -> str:
        c = colors(self._modo)
        text_color = c["text_tertiary"] if done else c["text_primary"]
        # line-through when done
        decoration = "line-through" if done else "none"
        return f"""
            QCheckBox {{
                color: {text_color};
                background: transparent;
                spacing: 8px;
                text-decoration: {decoration};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {c['border']};
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['accent']};
                border-color: {c['accent']};
                image: none;
            }}
            QCheckBox::indicator:hover {{
                border-color: {c['accent']};
            }}
        """

    # ── on_check (lógica preservada exacta) ─────────────────────────────────

    def _on_check(self, tarea_id: int, checkbox: QCheckBox):
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
                NMToast.show(top, "Tarea completada ✔", variant="success", duration_ms=1500)
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
        checkbox.setStyleSheet(self._checkbox_stylesheet(checked))
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
                border-radius: 8px;
                border: none;
            }}
        """)
        form_layout = QHBoxLayout(form)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(6)

        entry = QLineEdit()
        entry.setPlaceholderText("Nueva tarea...")
        entry.setFont(qfont("size_body"))
        entry.setFixedHeight(32)
        entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_accent'] if 'border_accent' in c else c['accent']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 13pt;
            }}
            QLineEdit:focus {{
                border-color: {c['accent']};
            }}
        """)
        form_layout.addWidget(entry)

        btn_save = NMButton("✓", modo=self._modo, width=32, height=32)
        btn_save.clicked.connect(
            lambda: self._add_task(seccion, entry.text(), form)
        )
        form_layout.addWidget(btn_save)

        entry.returnPressed.connect(
            lambda: self._add_task(seccion, entry.text(), form)
        )

        layout.addWidget(form)
        entry.setFocus()

    # ── _add_task (lógica preservada exacta) ─────────────────────────────────

    def _add_task(self, seccion: str, descripcion: str, form_widget: QWidget):
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
        except Exception:
            _log.exception("Operation failed")
        layout = form_widget.parentWidget().layout() if form_widget.parentWidget() else None
        if layout is not None:
            layout.removeWidget(form_widget)
        form_widget.deleteLater()
        self._load_tasks()

    # ── Nota del día ─────────────────────────────────────────────────────────

    def _build_nota_dia(self):
        c = colors(self._modo)

        frame = QFrame()
        frame.setObjectName("NotaCard")
        frame.setStyleSheet(f"""
            QFrame#NotaCard {{
                background-color: {c['bg_surface']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(14, 12, 14, 12)
        frame_layout.setSpacing(6)

        title_lbl = QLabel("📓  Nota del día")
        title_lbl.setFont(qfont("size_body", bold=True))
        title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        frame_layout.addWidget(title_lbl)

        self._nota_txt = QTextEdit()
        self._nota_txt.setMinimumHeight(60)
        self._nota_txt.setStyleSheet(stylesheet_textedit(self._modo))
        self._nota_txt.focusOutEvent = self._nota_focus_out
        frame_layout.addWidget(self._nota_txt)

        # Load saved note
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT nota FROM checklist_notas_dia WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0]:
                self._nota_txt.setPlainText(row[0])
                self._nota_txt.setReadOnly(True)
        except Exception:
            _log.exception("Operation failed")

        btn_save = NMButtonOutline("Guardar nota", modo=self._modo)
        btn_save.clicked.connect(self._guardar_nota)
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_row.addWidget(btn_save)
        frame_layout.addLayout(save_row)

        self._scroll_layout.addWidget(frame)

    def _nota_focus_out(self, event):
        self._guardar_nota()
        QTextEdit.focusOutEvent(self._nota_txt, event)

    # ── _guardar_nota (lógica preservada exacta) ─────────────────────────────

    def _guardar_nota(self):
        nota = self._nota_txt.toPlainText().strip()
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

        # Feedback + deshabilitar hasta el día siguiente
        self._nota_txt.setReadOnly(True)
        self._nota_txt.setStyleSheet(stylesheet_textedit(self._modo))
        NMToast.show(self.window(), "Nota guardada ✓", variant="success", duration_ms=2000)

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
                return f"{done}/{total} ✔"
        except Exception:
            _log.exception("Operation failed")
        return ""
