"""
app/modules/avisos_qt.py — Recordatorios v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Recordatorios):

  Header        eyebrow
  Search card   NMCard con NMInput búsqueda + 3 step pills filtro
                ("Todos / Activos / Hoy")
  Grid 3-col    _ReminderCardV3 (NMCard) con NMIcon grande coloreado por
                categoría inferida + chip cat + nombre + hora chip mono +
                frecuencia + status badge + NMButton "Completar"
  Footer        _DayProgressCard con progress bar de avisos activos vs total
  Opciones      Card de silencio (horario) + autostart (Windows registry)

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  _save_reminder(), _toggle_active(), _delete_reminder(),
  _leer_silencio(), _guardar_silencio(), _get_autostart(), _set_autostart(),
  get_card_status(), schema DB ``recordatorios`` y ``config``,
  _NuevoAvisoPanel (form inline preservado con tokens v3).
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QLineEdit, QSizePolicy,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput, NMToggle,
        NMToast, NMProgressBar, NMSkeleton, ThemeManager, NMEmptyState,
        NMProgressLine, NMIcon, NMPlayButton,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_scrollarea, stylesheet_lineedit,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.visual_qa import visual_qa_enabled, reminder_rows
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMInput, NMToggle,
        NMToast, NMProgressBar, NMSkeleton, ThemeManager, NMEmptyState,
        NMProgressLine, NMIcon, NMPlayButton,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_scrollarea, stylesheet_lineedit,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.visual_qa import visual_qa_enabled, reminder_rows


# ── Day labels (preservados) ────────────────────────────────────────────────

DIAS_LABELS = ["L", "M", "X", "J", "V", "S", "D"]
DIAS_FULL = ["Lunes", "Martes", "Miércoles", "Jueves",
              "Viernes", "Sábado", "Domingo"]


# ── Categorización inferida ─────────────────────────────────────────────────

def _categorize(msg: str) -> tuple[str, str, str]:
    """Infiere (categoria, icon_v3, color_token) según keywords del mensaje."""
    m = (msg or "").lower()
    if any(k in m for k in ("medic", "remedio", "pastilla", "pildora")):
        return ("Salud", "medicine", "danger")
    if any(k in m for k in ("agua", "hidrat", "beber")):
        return ("Hidratación", "water", "cyan")
    if any(k in m for k in ("respir", "calma", "medit", "mindful")):
        return ("Calma", "leaf", "teal")
    if any(k in m for k in ("ejerci", "yoga", "camin", "estira", "correr",
                              "gimnasio", "gym")):
        return ("Actividad", "run", "teal")
    if any(k in m for k in ("comer", "comida", "almuerz", "almorz",
                              "cena", "cenar", "desayun", "merienda",
                              "merendar")):
        return ("Comida", "spark", "warning")
    if any(k in m for k in ("trabajo", "trabajar", "estudio", "estudiar",
                              "tarea", "reunión", "reunion")):
        return ("Trabajo", "bookmark", "violet")
    if any(k in m for k in ("dormir", "acostar", "sueño", "sueno", "noche")):
        return ("Descanso", "moon", "violet")
    if any(k in m for k in ("terap", "doctor", "psico", "médic", "medic")):
        return ("Terapia", "therapy", "violet")
    return ("Recordatorio", "bell", "text2")


def _format_frequency(dias: str) -> str:
    """Convierte '1,2,3,4,5' → 'Lun a Vie', etc."""
    if not dias:
        return "Todos los días"
    try:
        parts = sorted({int(d) for d in dias.split(",") if d.strip()})
    except ValueError:
        return "Todos los días"
    if parts == [1, 2, 3, 4, 5, 6, 7]:
        return "Todos los días"
    if parts == [1, 2, 3, 4, 5]:
        return "Lun a Vie"
    if parts == [6, 7]:
        return "Fin de semana"
    return ", ".join(DIAS_LABELS[i - 1] for i in parts)


def _is_today(dias: str) -> bool:
    """True si el día actual está en la lista."""
    if not dias:
        return True
    import datetime as _dt
    today = _dt.datetime.now().weekday() + 1   # 1=Lunes
    return str(today) in dias.split(",")


# ── _DayPillToggle (preservado para form) ───────────────────────────────────

class _DayPillToggle(QPushButton):
    """Pill clickable v3 — toggleable. Usado en _NuevoAvisoPanel."""

    def __init__(self, label: str, modo: str = "dark_hybrid", parent=None):
        super().__init__(label, parent)
        self._modo = norm_modo(modo)
        self._active = False
        self.setCheckable(False)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_small",
                           weight=TYPOGRAPHY["weight_bold"]))
        self.clicked.connect(self._toggle)
        self._refresh()

    def is_active(self) -> bool:
        return self._active

    def _toggle(self):
        self._active = not self._active
        self._refresh()

    def _refresh(self):
        if self._active:
            grad_from = v3c("gradFrom", self._modo).name()
            grad_to = v3c("gradTo", self._modo).name()
            color = v3c("bg", self._modo).name()
            self.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {grad_from}, stop:1 {grad_to}); "
                f"color: {color}; border: none; "
                f"border-radius: 18px; }}")
        else:
            self.setStyleSheet(
                f"QPushButton {{ background: transparent; "
                f"color: {v3c('text2', self._modo).name()}; "
                f"border: 1px solid {v3c('borderStrong', self._modo).name()}; "
                f"border-radius: 18px; }}"
                f"QPushButton:hover {{ "
                f"border-color: {v3c('teal', self._modo).name()}; "
                f"color: {v3c('text', self._modo).name()}; }}")


# ── _NuevoAvisoPanel (form inline preservado) ───────────────────────────────

class _NuevoAvisoPanel(QWidget):
    """Form inline para crear un nuevo recordatorio v3."""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._day_pills: list[_DayPillToggle] = []
        self._build_ui()

    def _build_ui(self):
        is_dark = "dark" in self._modo
        bg_key = "surfaceSolid" if is_dark else "surface"
        self.setStyleSheet(
            f"_NuevoAvisoPanel {{ background: {v3c(bg_key, self._modo).name()}; "
            f"border: 1px solid {v3c('borderStrong', self._modo).name()}; "
            f"border-radius: {V3_RD['lg']}px; }}"
            f"QLabel {{ background: transparent; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                   V3_SP["xl"], V3_SP["lg"])
        layout.setSpacing(V3_SP["md"])

        title = QLabel("Nuevo aviso")
        title.setFont(qfont("size_h3",
                            weight=TYPOGRAPHY["weight_bold"]))
        title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()};")
        layout.addWidget(title)

        # Hora
        row_hora = QHBoxLayout()
        lbl_hora = QLabel("Hora:")
        lbl_hora.setFont(qfont("size_body"))
        lbl_hora.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()};")
        lbl_hora.setMinimumWidth(55)
        row_hora.addWidget(lbl_hora)
        self._entry_hora = NMInput("HH:MM", modo=self._modo)
        self._entry_hora.setMinimumWidth(80)
        row_hora.addWidget(self._entry_hora)
        row_hora.addStretch()
        layout.addLayout(row_hora)

        # Días
        row_dias = QHBoxLayout()
        lbl_dias = QLabel("Días:")
        lbl_dias.setFont(qfont("size_body"))
        lbl_dias.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()};")
        lbl_dias.setMinimumWidth(55)
        row_dias.addWidget(lbl_dias)
        for lbl in DIAS_LABELS:
            pill = _DayPillToggle(lbl, self._modo)
            row_dias.addWidget(pill)
            self._day_pills.append(pill)
        row_dias.addStretch()
        layout.addLayout(row_dias)

        # Mensaje
        lbl_msg = QLabel("Mensaje:")
        lbl_msg.setFont(qfont("size_body"))
        lbl_msg.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()};")
        layout.addWidget(lbl_msg)
        self._entry_mensaje = NMInput("Ej: Tomar medicación", modo=self._modo)
        layout.addWidget(self._entry_mensaje)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(V3_SP["sm"])
        btn_cancel = NMButton("Cancelar", variant="ghost", size="md",
                                parent=self, modo=self._modo, width=100)
        btn_cancel.clicked.connect(lambda _=False: self.cancelled.emit())
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_save = NMButton("Guardar", variant="gradient", size="md",
                              parent=self, modo=self._modo, width=120)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        self._btn_save = btn_save
        layout.addLayout(btn_row)

    def _on_save(self):
        try:
            hora = self._entry_hora.text().strip()
            mensaje = self._entry_mensaje.text().strip()
            if not hora or not mensaje or ":" not in hora:
                NMToast.display(self.window(),
                    "Completá la hora y el mensaje.",
                    variant="warning", duration_ms=3000)
                return
            parts = hora.split(":")
            try:
                h, m = int(parts[0]), int(parts[1])
                if h < 0 or h > 23 or m < 0 or m > 59:
                    NMToast.display(self.window(),
                        "Hora inválida. Formato: HH:MM (00-23:00-59).",
                        variant="error", duration_ms=3000)
                    return
                hora = f"{h:02d}:{m:02d}"
            except (ValueError, IndexError):
                NMToast.display(self.window(),
                    "Hora inválida. Usá formato HH:MM.",
                    variant="error", duration_ms=3000)
                return
            dias = ",".join(
                str(i + 1) for i, p in enumerate(self._day_pills) if p.is_active())
            if not dias:
                dias = "1,2,3,4,5,6,7"
            # Validar hora no expirada hoy
            import datetime as _dt
            now = _dt.datetime.now()
            dia_hoy = str(now.weekday() + 1)
            if dia_hoy in dias.split(","):
                try:
                    hh, mm = int(hora[:2]), int(hora[3:])
                    if hh < now.hour or (hh == now.hour and mm <= now.minute):
                        NMToast.display(self.window(),
                            "La hora ya pasó. Elegí al menos 1 minuto en adelante para hoy.",
                            variant="warning", duration_ms=3000)
                        return
                except (ValueError, IndexError) as e:
                    _log.warning(f"Error parsing hour in validation: {e}")
            # Validar que al menos un día sea futuro o hoy
            dias_futuros = []
            for d in dias.split(","):
                d_num = int(d)
                # Los días de la semana: 1=lunes, 7=domingo
                dias_futuros.append(d_num >= now.weekday() + 1 or d_num <= (now.weekday() + 1) % 7 + 1)
            if not any(dias_futuros):
                NMToast.display(self.window(),
                    "Los días seleccionados ya pasaron. Elegí días futuros.",
                    variant="warning", duration_ms=3000)
                return
            self.saved.emit({"hora": hora, "mensaje": mensaje, "dias": dias})
        except Exception as e:
            _log.error(f"Error in _on_save: {e}")
            import traceback
            traceback.print_exc()
            NMToast.display(self.window(),
                "Error al guardar el aviso. Verificá los datos.",
                variant="error", duration_ms=3000)


# ── _StepPill (filtro tabs) ─────────────────────────────────────────────────

class _StepPill(QPushButton):
    """Step pill toggleable — usado para tabs filtro (Todos/Activos/Hoy)."""

    def __init__(self, label: str, active: bool = False,
                 modo: str = "dark_hybrid", parent=None):
        super().__init__(label, parent)
        self._modo = norm_modo(modo)
        self._active = active
        self.setFixedHeight(32)
        self.setMinimumWidth(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_small",
                           weight=TYPOGRAPHY["weight_semibold"]))
        self._refresh()

    def set_active(self, active: bool):
        if active != self._active:
            self._active = active
            self._refresh()

    def _refresh(self):
        if self._active:
            gf = v3c("gradFrom", self._modo).name()
            gt = v3c("gradTo", self._modo).name()
            self.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {gf}, stop:1 {gt}); "
                f"color: {v3c('bg', self._modo).name()}; "
                f"border: none; border-radius: 16px; padding: 0 16px; }}")
        else:
            self.setStyleSheet(
                f"QPushButton {{ background: transparent; "
                f"color: {v3c('text2', self._modo).name()}; "
                f"border: 1px solid {v3c('borderStrong', self._modo).name()}; "
                f"border-radius: 16px; padding: 0 16px; }}"
                f"QPushButton:hover {{ "
                f"border-color: {v3c('teal', self._modo).name()}; "
                f"color: {v3c('text', self._modo).name()}; }}")


# ── _ReminderCardV3 ─────────────────────────────────────────────────────────

class _ReminderCardV3(NMCard):
    """Card v3 de recordatorio — icono grande coloreado + chip cat + hora mono + freq + status + Completar."""

    completed = pyqtSignal(int)   # rec_id
    deleted = pyqtSignal(int)
    toggled = pyqtSignal(int, bool)

    def __init__(self, row, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        # Normalizar acceso a row
        if hasattr(row, "keys"):
            self._id = row["id"]
            self._hora = row["hora"]
            self._mensaje = row["mensaje"]
            self._dias = row["dias"] or ""
            self._activo = bool(row["activo"])
            self._done = bool(row.get("done", False)) if hasattr(row, "get") else False
        else:
            self._id = row[0]
            self._hora = row[1]
            self._mensaje = row[2]
            self._dias = row[3] or ""
            self._activo = bool(row[4])
            self._done = False
        self._cat_name, self._icon_name, self._color_token = _categorize(self._mensaje)
        # Halo del color de la categoría
        self.set_accent(v3c(self._color_token, self._modo).name())
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["md"])

        # Top: icono grande + delete button
        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._icon = NMIcon(self._icon_name, size=36,
                             color=v3c(self._color_token, self._modo).name(),
                             modo=self._modo)
        top.addWidget(self._icon)
        top.addStretch()
        self._cat_chip = QLabel(self._cat_name)
        self._cat_chip.setFont(qfont("size_caption_xs",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        self._cat_chip.setContentsMargins(8, 2, 8, 2)
        top.addWidget(self._cat_chip)
        lay.addLayout(top)

        # Mensaje (título)
        self._msg_lbl = QLabel(self._mensaje)
        self._msg_lbl.setFont(qfont("size_h3",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        self._msg_lbl.setWordWrap(True)
        lay.addWidget(self._msg_lbl)

        # Hora chip + frecuencia
        meta_row = QHBoxLayout()
        meta_row.setSpacing(V3_SP["sm"])
        self._hora_chip = QLabel(self._hora)
        self._hora_chip.setFont(qfont_mono(11, bold=False))
        self._hora_chip.setContentsMargins(8, 2, 8, 2)
        meta_row.addWidget(self._hora_chip)
        self._freq_lbl = QLabel(_format_frequency(self._dias))
        self._freq_lbl.setFont(qfont("size_small"))
        meta_row.addWidget(self._freq_lbl)
        meta_row.addStretch()
        lay.addLayout(meta_row)

        # Status badge + completar button
        bottom = QHBoxLayout()
        bottom.setSpacing(V3_SP["sm"])
        self._status_lbl = QLabel("")
        self._status_lbl.setFont(qfont("size_caption_xs",
                                        weight=TYPOGRAPHY["weight_semibold"]))
        self._status_lbl.setContentsMargins(8, 2, 8, 2)
        bottom.addWidget(self._status_lbl)
        bottom.addStretch()
        self._btn_done = NMButton("Completar", variant="ghost", size="sm",
                                    modo=self._modo, width=110)
        self._btn_done.clicked.connect(
            lambda: self.completed.emit(self._id))
        bottom.addWidget(self._btn_done)
        lay.addLayout(bottom)

        self._apply_card_styles()

    def _apply_card_styles(self):
        # Chip categoría
        cat_color = v3c(self._color_token, self._modo).name()
        qc = QColor(cat_color)
        bg_rgba = f"rgba({qc.red()},{qc.green()},{qc.blue()},36)"
        self._cat_chip.setStyleSheet(
            f"color: {cat_color}; background: {bg_rgba}; border-radius: 8px;")
        # Hora chip
        teal = v3c("teal", self._modo).name()
        qt_ = QColor(teal)
        bg_hora = f"rgba({qt_.red()},{qt_.green()},{qt_.blue()},36)"
        self._hora_chip.setStyleSheet(
            f"color: {teal}; background: {bg_hora}; border-radius: 8px;")
        # Frecuencia
        self._freq_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        # Mensaje
        self._msg_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        # Status badge
        if self._done:
            stat_color = v3c("success", self._modo).name()
            stat_text = "Completado"
        elif not self._activo:
            stat_color = v3c("text3", self._modo).name()
            stat_text = "Pausado"
        elif _is_today(self._dias):
            stat_color = v3c("warning", self._modo).name()
            stat_text = "Hoy"
        else:
            stat_color = v3c("teal", self._modo).name()
            stat_text = "Activo"
        qs = QColor(stat_color)
        bg_stat = f"rgba({qs.red()},{qs.green()},{qs.blue()},36)"
        self._status_lbl.setText(stat_text)
        self._status_lbl.setStyleSheet(
            f"color: {stat_color}; background: {bg_stat}; "
            f"border-radius: 8px;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self.set_accent(v3c(self._color_token, self._modo).name())
        self._apply_card_styles()


# ── _DayProgressCard (footer) ───────────────────────────────────────────────

class _DayProgressCard(NMCard):
    """Footer v3: progreso de avisos activos vs total del día."""

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._active = 0
        self._total = 0
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["xl"])
        col = QVBoxLayout()
        col.setSpacing(4)
        self._eyebrow = QLabel("PROGRESO DEL DÍA")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._eyebrow)
        self._stat_lbl = QLabel("0 de 0 activos")
        self._stat_lbl.setFont(qfont("size_h3",
                                      weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._stat_lbl)
        self._bar = NMProgressLine(modo=self._modo)
        self._bar.set_progress(0.0)
        col.addWidget(self._bar)
        lay.addLayout(col, stretch=1)
        self._apply_dp_styles()

    def set_stats(self, active: int, total: int):
        self._active = active
        self._total = total
        self._stat_lbl.setText(f"{active} de {total} activos")
        self._bar.set_progress(active / total if total else 0.0)

    def _apply_dp_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._stat_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._bar._modo = self._modo
        self._bar.update()
        self._apply_dp_styles()


# ── ModuloAvisos v3 ─────────────────────────────────────────────────────────

class ModuloAvisos(NMModule):
    MODULE_TITLE = "Recordatorios"
    MODULE_ICON  = "avisos"

    def build_ui(self):
        self._search_query: str = ""
        self._current_filter: str = "todos"   # "todos" | "activos" | "hoy"
        self._all_rows: list = []

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

        # 1. Header eyebrow + acciones
        header_row = QHBoxLayout()
        self._eyebrow = QLabel("RECORDATORIOS")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        header_row.addWidget(self._eyebrow)
        header_row.addStretch()
        self._btn_new = NMButton("+ Nuevo aviso", variant="gradient",
                                  size="sm", modo=self._modo, width=140)
        self._btn_new.clicked.connect(self._show_form)
        header_row.addWidget(self._btn_new)
        lay.addLayout(header_row)

        # 2. Search + filter pills card
        search_card = NMCard(modo=self._modo, clickable=False)
        sc_lay = QVBoxLayout(search_card)
        sc_lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                   V3_SP["xl"], V3_SP["lg"])
        sc_lay.setSpacing(V3_SP["md"])

        # Search input + filter pills (mismo row)
        search_row = QHBoxLayout()
        search_row.setSpacing(V3_SP["lg"])
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Buscar aviso por nombre u hora…")
        self._search_edit.setStyleSheet(stylesheet_lineedit(self._modo))
        self._search_edit.setFixedHeight(36)
        self._search_edit.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_edit, stretch=2)

        # Filter step pills
        self._filter_pills: dict[str, _StepPill] = {}
        for key, label in (("todos", "Todos"),
                           ("activos", "Activos"),
                           ("hoy", "Hoy")):
            pill = _StepPill(label, active=(key == "todos"),
                              modo=self._modo)
            pill.clicked.connect(
                lambda _, k=key: self._on_filter_changed(k))
            self._filter_pills[key] = pill
            search_row.addWidget(pill)
        sc_lay.addLayout(search_row)
        lay.addWidget(search_card)
        self._search_card = search_card

        # 3. Form inline placeholder (insertado dinámicamente con _show_form)
        self._form_placeholder = QWidget()
        self._form_placeholder_lay = QVBoxLayout(self._form_placeholder)
        self._form_placeholder_lay.setContentsMargins(0, 0, 0, 0)
        self._form_placeholder_lay.setSpacing(0)
        lay.addWidget(self._form_placeholder)

        # 4. Grid 3-col
        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QGridLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(V3_SP["xl"])
        for col in range(3):
            self._list_layout.setColumnStretch(col, 1)
        lay.addWidget(self._list_widget)

        # 5. Footer day progress card
        self._day_progress = _DayProgressCard(modo=self._modo)
        lay.addWidget(self._day_progress)

        # 6. Opciones (silencio + autostart)
        if not visual_qa_enabled():
            self._build_opciones(lay)

        self._apply_text_styles()
        self._load_reminders()

    def _apply_text_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_search_edit"):
            self._search_edit.setStyleSheet(stylesheet_lineedit(self._modo))
        if hasattr(self, "_eyebrow"):
            self._apply_text_styles()
        for pill in getattr(self, "_filter_pills", {}).values():
            pill._modo = self._modo
            pill._refresh()
        self._load_reminders()
        self.update()

    # ── Filtros ───────────────────────────────────────────────────────────────

    def _on_search(self, text: str):
        self._search_query = text.lower().strip()
        self._render_reminders()

    def _on_filter_changed(self, key: str):
        self._current_filter = key
        for k, pill in self._filter_pills.items():
            pill.set_active(k == key)
        self._render_reminders()

    # ── Carga / render ───────────────────────────────────────────────────────

    def _load_reminders(self):
        if visual_qa_enabled():
            self._all_rows = reminder_rows()
        else:
            try:
                conn = obtener_conexion()
                self._all_rows = conn.execute(
                    "SELECT id, hora, mensaje, dias, activo "
                    "FROM recordatorios ORDER BY hora"
                ).fetchall()
                conn.close()
            except Exception:
                self._all_rows = []
        # Update day progress
        total = len(self._all_rows)
        if visual_qa_enabled():
            active = sum(1 for r in self._all_rows if r.get("done"))
        else:
            active = sum(
                1 for r in self._all_rows
                if (r["activo"] if hasattr(r, "keys") else r[4])
            )
        if hasattr(self, "_day_progress"):
            self._day_progress.set_stats(active, total)
        self._render_reminders()

    def _row_get(self, row, key, idx):
        return row[key] if hasattr(row, "keys") else row[idx]

    def _render_reminders(self):
        # Clear grid
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        rows = list(self._all_rows)
        # Search filter
        if self._search_query:
            rows = [
                r for r in rows
                if self._search_query in self._row_get(r, "mensaje", 2).lower()
                or self._search_query in self._row_get(r, "hora", 1).lower()
            ]
        # Tab filter
        if self._current_filter == "activos":
            rows = [r for r in rows if self._row_get(r, "activo", 4)]
        elif self._current_filter == "hoy":
            rows = [
                r for r in rows
                if self._row_get(r, "activo", 4)
                and _is_today(self._row_get(r, "dias", 3) or "")
            ]

        if not rows:
            empty_msg = ("Sin avisos configurados"
                         if not self._all_rows
                         else "Sin resultados con esos filtros")
            empty_sub = (
                "Usá el botón \"+ Nuevo aviso\" para empezar."
                if not self._all_rows
                else "Probá cambiar los filtros o la búsqueda.")
            empty = NMEmptyState(
                "fa5s.bell", empty_msg, empty_sub, self._list_widget)
            self._list_layout.addWidget(empty, 0, 0, 1, 3)
            return

        for i, row in enumerate(rows):
            card = _ReminderCardV3(row, modo=self._modo)
            card.completed.connect(self._on_completar)
            r = i // 3
            c = i % 3
            self._list_layout.addWidget(card, r, c)

    # ── Acciones de cards ────────────────────────────────────────────────────

    def _on_completar(self, rec_id: int):
        """'Completar' deactiva el aviso (interpretación v3 del README)."""
        self._toggle_active(rec_id, False)
        self._load_reminders()
        NMToast.display(self.window(), "Aviso completado",
                         variant="success", duration_ms=1500)

    # ── _toggle_active (lógica preservada exacta) ───────────────────────────

    def _toggle_active(self, rec_id: int, checked: bool):
        if visual_qa_enabled():
            self._load_reminders()
            return
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

    # ── _delete_reminder (lógica preservada exacta) ─────────────────────────

    def _delete_reminder(self, rec_id: int):
        if visual_qa_enabled():
            self._load_reminders()
            return
        try:
            conn = obtener_conexion()
            conn.execute("DELETE FROM recordatorios WHERE id = ?", (rec_id,))
            conn.commit()
            conn.close()
        except Exception:
            _log.exception("Failed to delete reminder %s", rec_id)
        self._load_reminders()

    # ── Show form inline ─────────────────────────────────────────────────────

    def _show_form(self):
        # Solo un panel a la vez
        while self._form_placeholder_lay.count():
            item = self._form_placeholder_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        panel = _NuevoAvisoPanel(self._content, self._modo)
        panel.saved.connect(self._on_form_saved)
        panel.cancelled.connect(self._on_form_cancelled)
        self._form_placeholder_lay.addWidget(panel)
        self._current_panel = panel

    def _on_form_saved(self, data: dict):
        self._save_reminder(data)
        self._on_form_cancelled()
        NMToast.display(self.window(), "Aviso guardado",
                         variant="success", duration_ms=1500)

    def _on_form_cancelled(self):
        while self._form_placeholder_lay.count():
            item = self._form_placeholder_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    # ── _save_reminder (lógica preservada exacta) ───────────────────────────

    def _save_reminder(self, data: dict):
        if visual_qa_enabled():
            self._load_reminders()
            return
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO recordatorios (hora, mensaje, dias, activo) "
                "VALUES (?, ?, ?, 1)",
                (data["hora"], data["mensaje"], data["dias"]),
            )
            conn.commit()
            conn.close()
            try:
                from shared.sync import sync_inmediato_background
                sync_inmediato_background()
            except Exception:
                pass
        except Exception:
            _log.exception("Failed to save reminder")
        self._load_reminders()

    # ── Opciones del sistema (silencio + autostart) ─────────────────────────

    def _build_opciones(self, parent_layout: QVBoxLayout):
        opts_card = NMCard(modo=self._modo, clickable=False)
        opts_lay = QVBoxLayout(opts_card)
        opts_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"],
                                     V3_SP["lg"], V3_SP["md"])
        opts_lay.setSpacing(V3_SP["sm"])

        opts_eyebrow = QLabel("OPCIONES DEL SISTEMA")
        opts_eyebrow.setFont(qfont("size_caption_xs",
                                    weight=TYPOGRAPHY["weight_semibold"]))
        opts_eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        opts_lay.addWidget(opts_eyebrow)
        self._opts_eyebrow = opts_eyebrow

        # Silencio
        sil_ini, sil_fin = self._leer_silencio()
        sil_row = QHBoxLayout()
        sil_row.setSpacing(V3_SP["sm"])
        sil_lbl = QLabel("Horario de silencio")
        sil_lbl.setFont(qfont("size_small"))
        sil_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        sil_row.addWidget(sil_lbl)
        sil_row.addStretch()
        self._entry_sil_ini = NMInput("22:00", modo=self._modo)
        self._entry_sil_ini.setFixedSize(70, 32)
        if sil_ini:
            self._entry_sil_ini.setText(sil_ini)
        sil_row.addWidget(self._entry_sil_ini)
        arrow = QLabel("→")
        arrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        sil_row.addWidget(arrow)
        self._entry_sil_fin = NMInput("08:00", modo=self._modo)
        self._entry_sil_fin.setFixedSize(70, 32)
        if sil_fin:
            self._entry_sil_fin.setText(sil_fin)
        sil_row.addWidget(self._entry_sil_fin)
        btn_apply = NMButton("Aplicar", variant="secondary",
                              size="sm", modo=self._modo, width=80)
        btn_apply.clicked.connect(self._guardar_silencio)
        self._btn_apply_silencio = btn_apply
        sil_row.addWidget(btn_apply)
        opts_lay.addLayout(sil_row)

        # Autostart
        auto_row = QHBoxLayout()
        auto_row.setSpacing(V3_SP["sm"])
        auto_lbl = QLabel("Iniciar con Windows")
        auto_lbl.setFont(qfont("size_small"))
        auto_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        auto_row.addWidget(auto_lbl)
        auto_row.addStretch()
        self._autostart_toggle = NMToggle(parent=opts_card, modo=self._modo)
        self._autostart_toggle.setChecked(self._get_autostart())
        self._autostart_toggle.toggled.connect(
            lambda checked: self._set_autostart(checked))
        auto_row.addWidget(self._autostart_toggle)
        opts_lay.addLayout(auto_row)

        parent_layout.addWidget(opts_card)

    # ── Silencio (lógica preservada exacta) ─────────────────────────────────

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
            for clave, valor in (("silencio_inicio", ini),
                                  ("silencio_fin", fin)):
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
            if hasattr(self._btn_apply_silencio, "play_success"):
                self._btn_apply_silencio.play_success()
        except Exception:
            _log.exception("Failed to save silencio config")

    # ── Autostart (lógica preservada exacta) ────────────────────────────────

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
            import winreg
            import sys as _sys
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            if activar:
                exe = _sys.executable if getattr(_sys, "frozen", False) else _sys.argv[0]
                winreg.SetValueEx(key, "NeuroMood", 0, winreg.REG_SZ,
                                   f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(key, "NeuroMood")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            _log.exception("Failed to update autostart registry")

    # ── Hooks ────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._load_reminders()

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "4 activos"
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
