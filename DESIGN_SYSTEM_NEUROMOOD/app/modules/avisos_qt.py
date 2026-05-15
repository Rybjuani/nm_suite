"""
app/modules/avisos_qt.py — Gestión de recordatorios / avisos (PyQt6)

LÓGICA PRESERVADA EXACTA:
  _save_reminder(), _toggle_active(), _delete_reminder(),
  _guardar_silencio(), _get_autostart(), _set_autostart(),
  get_card_status()
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput, NMToggle,
        NMToast, NMProgressBar, NMSkeleton, ThemeManager, h_spacer, NMEmptyState,
        NMProgressLine, NMAvisoCard,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_PILL, RADIUS_INPUT,
        stylesheet_textedit, stylesheet_scrollarea, stylesheet_lineedit,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput, NMToggle,
        NMToast, NMProgressBar, NMSkeleton, ThemeManager, h_spacer, NMEmptyState,
        NMProgressLine, NMAvisoCard,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_PILL, RADIUS_INPUT,
        stylesheet_textedit, stylesheet_scrollarea, stylesheet_lineedit,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion


# ── Day labels (preservados exactos) ─────────────────────────────────────────

DIAS_LABELS = ["L", "M", "X", "J", "V", "S", "D"]
DIAS_FULL   = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


# ── Day pill (display-only) ───────────────────────────────────────────────────

class _DayPill(QWidget):
    """Píldora de día de la semana — solo display, sin interacción."""

    def __init__(self, label: str, active: bool, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._label = label
        self._active = active
        self._modo = norm_modo(modo)
        self.setFixedSize(26, 26)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = 13

        if self._active:
            p.setBrush(QBrush(QColor(c["accent"])))
            text_color = QColor(c["text_on_accent"])
        else:
            p.setBrush(QBrush(QColor(c["bg_elevated"])))
            text_color = QColor(c["text_tertiary"])

        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 24, 24)

        p.setPen(text_color)
        p.setFont(qfont("size_caption", bold=True))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._label)
        p.end()


# ── Day pill toggleable (for form) ────────────────────────────────────────────

class _DayPillToggle(QPushButton):
    """Píldora de día toggleable para el formulario de nuevo aviso."""

    def __init__(self, label: str, modo: str = "dark_hybrid", parent=None):
        super().__init__(label, parent)
        self._modo = norm_modo(modo)
        self._active = True  # default: all days selected
        self.setFixedSize(30, 30)
        self.setCheckable(False)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()
        self.clicked.connect(self._toggle)

    def _toggle(self):
        self._active = not self._active
        self._apply_style()

    def is_active(self) -> bool:
        return self._active

    def set_active(self, v: bool):
        self._active = v
        self._apply_style()

    def _apply_style(self):
        c = colors(self._modo)
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['accent']};
                    color: {c['text_on_accent']};
                    border-radius: {RADIUS_PILL}px;
                    border: none;
                    font-size: {TYPOGRAPHY['size_caption']}pt;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_elevated']};
                    color: {c['text_tertiary']};
                    border-radius: {RADIUS_PILL}px;
                    border: 1px solid {c.get('border_card', c['border'])};
                    font-size: {TYPOGRAPHY['size_caption']}pt;
                }}
                QPushButton:hover {{
                    border-color: {c['accent']};
                    color: {c['text_primary']};
                }}
            """)


# ── Delete button with red hover ──────────────────────────────────────────────

class _DeleteButton(QPushButton):
    """Botón ✕ que se vuelve rojo en hover."""

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__("✕", parent)
        self._modo = norm_modo(modo)
        self._hovered = False
        self.setFixedSize(28, 28)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def _apply_style(self):
        c = colors(self._modo)
        if self._hovered:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['error']};
                    color: white;
                    border-radius: 14px;
                    border: none;
                    font-size: {TYPOGRAPHY['size_caption']}pt;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_tertiary']};
                    border-radius: 14px;
                    border: none;
                    font-size: {TYPOGRAPHY['size_caption']}pt;
                }}
                QPushButton:hover {{
                    background-color: {c['error']};
                    color: white;
                }}
            """)

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)


# ── New reminder inline panel ──────────────────────────────────────────────────

class _NuevoAvisoPanel(QWidget):
    """Panel inline para crear un nuevo recordatorio — se muestra dentro del modulo."""
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._day_pills: list[_DayPillToggle] = []
        self._build_ui()

    def _build_ui(self):
        c = colors(self._modo)

        # Fondo glass premium para el panel overlay
        self.setStyleSheet(f"""
            _NuevoAvisoPanel {{
                background-color: {c['bg_glass']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
            }}
            QLabel {{
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp("md") + sp("xs"), sp("md"), sp("md") + sp("xs"), sp("md"))
        layout.setSpacing(sp("sm") + sp("xs"))

        # Title
        title_lbl = QLabel("Nuevo aviso")
        title_lbl.setFont(qfont("size_h3", bold=True))
        title_lbl.setStyleSheet(f"color: {c['text_primary']};")
        layout.addWidget(title_lbl)

        # Hour
        row_hora = QHBoxLayout()
        lbl_hora = QLabel("Hora:")
        lbl_hora.setFont(qfont("size_body"))
        lbl_hora.setStyleSheet(f"color: {c['text_secondary']};")
        lbl_hora.setMinimumWidth(55)
        row_hora.addWidget(lbl_hora)

        self._entry_hora = NMInput("HH:MM", modo=self._modo)
        self._entry_hora.setMinimumWidth(72)
        row_hora.addWidget(self._entry_hora)
        row_hora.addStretch()
        layout.addLayout(row_hora)

        # Days
        row_dias = QHBoxLayout()
        lbl_dias = QLabel("Días:")
        lbl_dias.setFont(qfont("size_body"))
        lbl_dias.setStyleSheet(f"color: {c['text_secondary']};")
        lbl_dias.setMinimumWidth(55)
        row_dias.addWidget(lbl_dias)

        for lbl in DIAS_LABELS:
            pill = _DayPillToggle(lbl, self._modo)
            row_dias.addWidget(pill)
            self._day_pills.append(pill)
        row_dias.addStretch()
        layout.addLayout(row_dias)

        # Message
        lbl_msg = QLabel("Mensaje:")
        lbl_msg.setFont(qfont("size_body"))
        lbl_msg.setStyleSheet(f"color: {c['text_secondary']};")
        layout.addWidget(lbl_msg)

        self._entry_mensaje = NMInput("Ej: Tomar medicación", modo=self._modo)
        layout.addWidget(self._entry_mensaje)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(sp("sm"))

        btn_cancel = NMButtonOutline("Cancelar", parent=self, modo=self._modo)
        btn_cancel.setFixedHeight(36)
        btn_cancel.setMinimumWidth(90)
        btn_cancel.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(btn_cancel)

        btn_row.addStretch()

        btn_save = NMButton("Guardar", parent=self, modo=self._modo, width=90, height=36)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        self._btn_save = btn_save

        layout.addLayout(btn_row)

    def _on_save(self):
        hora    = self._entry_hora.text().strip()
        mensaje = self._entry_mensaje.text().strip()

        if not hora or not mensaje:
            return
        if ":" not in hora:
            return
        parts = hora.split(":")
        try:
            h, m = int(parts[0]), int(parts[1])
            if h < 0 or h > 23 or m < 0 or m > 59:
                return
            hora = f"{h:02d}:{m:02d}"
        except (ValueError, IndexError):
            return

        dias = ",".join(
            str(i + 1) for i, pill in enumerate(self._day_pills) if pill.is_active()
        )
        if not dias:
            dias = "1,2,3,4,5,6,7"

        # Validar que la hora no haya expirado si hoy es un día seleccionado
        import datetime as _dt
        now = _dt.datetime.now()
        dia_hoy = str(now.weekday() + 1)
        if dia_hoy in dias.split(","):
            hh, mm = int(hora[:2]), int(hora[3:])
            if hh < now.hour or (hh == now.hour and mm <= now.minute):
                NMToast.display(self.window(),
                    "La hora ya pasó. Elegí al menos 1 minuto en adelante para hoy.",
                    variant="warning", duration_ms=3000)
                return

        data = {"hora": hora, "mensaje": mensaje, "dias": dias}
        self.saved.emit(data)


# ── ModuloAvisos ──────────────────────────────────────────────────────────────

class ModuloAvisos(NMModule):
    MODULE_TITLE = "Avisos"
    MODULE_ICON  = "avisos"

    def build_ui(self):
        c = colors(self._modo)

        # ── Root layout ───────────────────────────────────────────────────────
        root = QVBoxLayout(self._content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NMProgressLine — ultra-thin 2px top border ────────────────────────
        self._progress_line = NMProgressLine(total=1, current=0,
                                             modo=self._modo, parent=self._content)
        root.addWidget(self._progress_line)

        # ── Inner content (padded) ────────────────────────────────────────────
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(PAD_CONTAINER, sp("sm") + sp("xs"),
                                        PAD_CONTAINER, sp("sm") + sp("xs"))
        inner_layout.setSpacing(sp("sm"))
        root.addWidget(inner, stretch=1)
        root = inner_layout  # redirect further additions to padded inner

        # ── Top bar ───────────────────────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        lbl_tus = QLabel("Tus recordatorios")
        lbl_tus.setFont(qfont("size_body"))
        lbl_tus.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        top_layout.addWidget(lbl_tus)

        self._reminder_count_lbl = QLabel("")
        self._reminder_count_lbl.setFont(qfont("size_caption"))
        self._reminder_count_lbl.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent;"
        )
        top_layout.addWidget(self._reminder_count_lbl)
        top_layout.addStretch()

        root.addWidget(top_bar)

        # ── Banner informativo (accent border, QLabel) ────────────────────────
        banner = QFrame()
        banner.setObjectName("Banner")
        banner.setStyleSheet(f"""
            QFrame#Banner {{
                background-color: {c['bg_elevated']};
                border-radius: {RADIUS_INPUT}px;
                border: 1px solid {c['accent']};
            }}
        """)
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(sp("sm") + sp("xs"), sp("sm"), sp("sm") + sp("xs"), sp("sm"))

        banner_lbl = QLabel(
            "Los avisos funcionan aunque cierres la app; "
            "se minimiza a la bandeja del sistema."
        )
        banner_lbl.setFont(qfont("size_small"))
        banner_lbl.setWordWrap(True)
        banner_lbl.setStyleSheet(f"color: {c['accent']}; background: transparent;")
        banner_layout.addWidget(banner_lbl)
        root.addWidget(banner)

        # ── Scroll area for reminder list ─────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        self._list_content = QWidget()
        self._list_content.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_content)
        self._list_layout.setContentsMargins(0, 0, sp("sm"), 0)
        self._list_layout.setSpacing(GAP_ELEMENTS)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._list_content)
        root.addWidget(self._scroll, stretch=1)

        # ── FAB "+" floating action button ───────────────────────────────────
        fab_row = QHBoxLayout()
        fab_row.setContentsMargins(0, sp("sm"), 0, 0)
        fab_row.addStretch()
        self._fab_btn = NMButton("+", parent=self._content,
                                  modo=self._modo, width=50, height=50)
        self._fab_btn.clicked.connect(self._show_form)
        self._fab_btn.setStyleSheet(
            self._fab_btn.styleSheet() + f" border-radius: 25px;"
        )
        fab_row.addWidget(self._fab_btn)
        root.addLayout(fab_row)

        # ── Opciones del sistema ──────────────────────────────────────────────
        self._build_opciones(root)

        # ── Load reminders ────────────────────────────────────────────────────
        self._load_reminders()

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        # NMProgressLine auto-handles theme via ThemeManager
        self._load_reminders()
        self.update()

    # ── Load reminders ─────────────────────────────────────────────────────

    def _load_reminders(self):
        # Clear list
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                self._list_layout.removeWidget(w)
                w.deleteLater()

        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT id, hora, mensaje, dias, activo "
                "FROM recordatorios ORDER BY hora"
            ).fetchall()
            conn.close()
        except Exception:
            rows = []

        if not rows:
            if hasattr(self, "_progress_line"):
                self._progress_line.set_progress(0, 1)
            if hasattr(self, "_reminder_count_lbl"):
                self._reminder_count_lbl.setText("")
            self._list_layout.addWidget(NMEmptyState(
                "fa5s.bell",
                "Sin avisos configurados",
                "Usá el botón + para agregar recordatorios.",
                self._list_content,
            ))
            return

        for row in rows:
            self._build_reminder_card(row)

        # Update progress line
        total = len(rows)
        active = sum(1 for r in rows if (r["activo"] if hasattr(r, "keys") else r[4]))
        if hasattr(self, "_progress_line"):
            self._progress_line.set_progress(active, total)
        if hasattr(self, "_reminder_count_lbl"):
            self._reminder_count_lbl.setText(
                f"  {active}/{total} activos" if total > 0 else ""
            )

    def _build_reminder_card(self, row):
        c = colors(self._modo)
        rec_id = row["id"] if hasattr(row, "keys") else row[0]
        hora   = row["hora"] if hasattr(row, "keys") else row[1]
        msg    = row["mensaje"] if hasattr(row, "keys") else row[2]
        dias   = row["dias"] if hasattr(row, "keys") else row[3]
        activo = bool(row["activo"] if hasattr(row, "keys") else row[4])
        status = NMAvisoCard.STATUS_ACTIVE if activo else NMAvisoCard.STATUS_EXPIRED

        # Wrapper frame for the full card (including actions + days)
        wrapper = QFrame()
        wrapper.setStyleSheet("QFrame { background: transparent; }")
        wrapper_lay = QVBoxLayout(wrapper)
        wrapper_lay.setContentsMargins(0, 0, 0, 0)
        wrapper_lay.setSpacing(2)

        # Action row: delete + toggle aligned right (above the card)
        action_row = QHBoxLayout()
        action_row.setSpacing(sp("xs"))
        action_row.addStretch()

        del_btn = _DeleteButton(self._modo, wrapper)
        del_btn.clicked.connect(lambda checked=False, rid=rec_id, wr=wrapper:
                                self._delete_reminder(rid, wr))
        action_row.addWidget(del_btn)

        toggle = NMToggle(wrapper, self._modo)
        toggle.setChecked(activo)
        toggle.toggled.connect(lambda checked, rid=rec_id: self._toggle_active(rid, checked))
        action_row.addWidget(toggle)
        wrapper_lay.addLayout(action_row)

        # NMAvisoCard — premium display with monospaced time + status pill
        aviso_card = NMAvisoCard(hora, msg, status=status,
                                  modo=self._modo, parent=wrapper)
        wrapper_lay.addWidget(aviso_card)

        # Days pills row
        dias_str = dias if dias else "1,2,3,4,5,6,7"
        dias_activos = set(dias_str.split(","))
        days_row = QHBoxLayout()
        days_row.setContentsMargins(sp("md"), sp("xs") // 2, sp("md"), sp("xs") // 2)
        days_row.setSpacing(sp("xs"))
        days_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i, lbl in enumerate(DIAS_LABELS, start=1):
            is_active = str(i) in dias_activos
            pill = _DayPill(lbl, is_active, self._modo, wrapper)
            days_row.addWidget(pill)
        days_row.addStretch()
        wrapper_lay.addLayout(days_row)

        self._list_layout.addWidget(wrapper)

    # ── _toggle_active (lógica preservada exacta) ─────────────────────────────

    def _toggle_active(self, rec_id: int, checked: bool):
        try:
            conn = obtener_conexion()
            conn.execute(
                "UPDATE recordatorios SET activo = ? WHERE id = ?",
                (1 if checked else 0, rec_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Failed to save reminder")

    # ── _delete_reminder (lógica preservada exacta) ───────────────────────────

    def _delete_reminder(self, rec_id: int, card_widget: QWidget):
        try:
            conn = obtener_conexion()
            conn.execute("DELETE FROM recordatorios WHERE id = ?", (rec_id,))
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Failed to delete reminder %s", rec_id)
        self._list_layout.removeWidget(card_widget)
        card_widget.deleteLater()

    # ── Show form (inline panel) ────────────────────────────────────────────────

    def _show_form(self):
        # Solo permitir un panel a la vez
        for i in range(self._list_layout.count()):
            item = self._list_layout.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, _NuevoAvisoPanel):
                self._list_layout.removeWidget(w)
                w.deleteLater()
                break
        panel = _NuevoAvisoPanel(self._content, self._modo)
        panel.saved.connect(lambda data: (self._save_reminder(data), self._list_layout.removeWidget(panel), panel.deleteLater()))
        panel.cancelled.connect(lambda: (self._list_layout.removeWidget(panel), panel.deleteLater()))
        self._list_layout.insertWidget(0, panel)

    def _handle_new_reminder_saved(self, panel: QWidget, data: dict):
        self._save_reminder(data)
        if hasattr(panel, "_btn_save") and hasattr(panel._btn_save, "play_success"):
            panel._btn_save.play_success()
        self._list_layout.removeWidget(panel)
        panel.deleteLater()

    # ── _save_reminder (lógica preservada exacta, adaptada para dict) ─────────

    def _save_reminder(self, data: dict):
        hora    = data["hora"]
        mensaje = data["mensaje"]
        dias    = data["dias"]

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO recordatorios (hora, mensaje, dias, activo) "
                "VALUES (?, ?, ?, 1)",
                (hora, mensaje, dias),
            )
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Failed to save reminder")

        self._load_reminders()

    # ── Opciones del sistema ──────────────────────────────────────────────────

    def _build_opciones(self, parent_layout: QVBoxLayout):
        c = colors(self._modo)

        frame = QFrame()
        frame.setObjectName("OpcionesCard")
        frame.setStyleSheet(f"""
            QFrame#OpcionesCard {{
                background-color: {c['bg_surface']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
            }}
        """)
        inner_layout = QVBoxLayout(frame)
        inner_layout.setContentsMargins(
            sp("md") - sp("xs") // 2,
            sp("sm") + sp("xs"),
            sp("md") - sp("xs") // 2,
            sp("sm") + sp("xs"),
        )
        inner_layout.setSpacing(sp("sm") + sp("xs") // 2)

        # Title
        title_lbl = QLabel("Opciones")
        title_lbl.setFont(qfont("size_body", bold=True))
        title_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        inner_layout.addWidget(title_lbl)

        # ── Horario de silencio ────────────────────────────────────────────
        sil_ini, sil_fin = self._leer_silencio()

        sil_row = QHBoxLayout()
        sil_row.setSpacing(sp("sm"))

        sil_lbl = QLabel("Silencio:")
        sil_lbl.setFont(qfont("size_body"))
        sil_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        sil_row.addWidget(sil_lbl)

        self._entry_sil_ini = NMInput("22:00", modo=self._modo)
        self._entry_sil_ini.setMinimumWidth(64)
        self._entry_sil_ini.setFixedHeight(32)
        if sil_ini:
            self._entry_sil_ini.setText(sil_ini)
        sil_row.addWidget(self._entry_sil_ini)

        arrow_lbl = QLabel("→")
        arrow_lbl.setFont(qfont("size_small"))
        arrow_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        sil_row.addWidget(arrow_lbl)

        self._entry_sil_fin = NMInput("08:00", modo=self._modo)
        self._entry_sil_fin.setMinimumWidth(64)
        self._entry_sil_fin.setFixedHeight(32)
        if sil_fin:
            self._entry_sil_fin.setText(sil_fin)
        sil_row.addWidget(self._entry_sil_fin)

        btn_apply = NMButtonOutline("Aplicar", modo=self._modo)
        btn_apply.setFixedHeight(32)
        btn_apply.setMinimumWidth(68)
        btn_apply.clicked.connect(self._guardar_silencio)
        sil_row.addWidget(btn_apply)
        self._btn_apply_silencio = btn_apply
        sil_row.addStretch()

        inner_layout.addLayout(sil_row)

        # ── Iniciar con Windows ────────────────────────────────────────────
        win_row = QHBoxLayout()
        win_row.setSpacing(sp("sm"))

        win_lbl = QLabel("Iniciar con Windows")
        win_lbl.setFont(qfont("size_body"))
        win_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        win_row.addWidget(win_lbl)
        win_row.addStretch()

        self._autostart_toggle = NMToggle(frame, self._modo)
        self._autostart_toggle.setChecked(self._get_autostart())
        self._autostart_toggle.toggled.connect(
            lambda checked: self._set_autostart(checked)
        )
        win_row.addWidget(self._autostart_toggle)

        inner_layout.addLayout(win_row)
        parent_layout.addWidget(frame)

    # ── Silence logic (lógica preservada exacta) ──────────────────────────────

    def _leer_silencio(self):
        try:
            conn = obtener_conexion()
            ini = conn.execute(
                "SELECT valor FROM config WHERE clave='silencio_inicio'"
            ).fetchone()
            fin = conn.execute(
                "SELECT valor FROM config WHERE clave='silencio_fin'"
            ).fetchone()
            conn.close()
            return (
                (ini[0] if isinstance(ini, tuple) else ini["valor"]) if ini else "",
                (fin[0] if isinstance(fin, tuple) else fin["valor"]) if fin else "",
            )
        except Exception:
            return "", ""

    def _guardar_silencio(self):
        ini = self._entry_sil_ini.text().strip()
        fin = self._entry_sil_fin.text().strip()
        for val in (ini, fin):
            if val and (":" not in val):
                return
        try:
            conn = obtener_conexion()
            for clave, valor in (("silencio_inicio", ini), ("silencio_fin", fin)):
                if valor:
                    conn.execute(
                        "INSERT INTO config (clave, valor) VALUES (?, ?) "
                        "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                        (clave, valor),
                    )
                else:
                    conn.execute("DELETE FROM config WHERE clave=?", (clave,))
            conn.commit()
            conn.close()
            if hasattr(self, "_btn_apply_silencio") and hasattr(self._btn_apply_silencio, "play_success"):
                self._btn_apply_silencio.play_success()
        except Exception:
            _log.exception("Failed to save config %s", clave)

    # ── Autostart (lógica preservada exacta) ──────────────────────────────────

    def _get_autostart(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            )
            winreg.QueryValueEx(key, "NeuroMood")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _set_autostart(self, activar: bool):
        try:
            import winreg, sys as _sys
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            if activar:
                exe = _sys.executable if getattr(_sys, "frozen", False) else _sys.argv[0]
                winreg.SetValueEx(key, "NeuroMood", 0, winreg.REG_SZ, f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(key, "NeuroMood")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            _log.exception("Failed to update autostart registry")

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._load_reminders()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM recordatorios WHERE activo = 1"
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} activo{'s' if n > 1 else ''}"
        except Exception:
            _log.exception("Failed to get card status for avisos")
        return ""
