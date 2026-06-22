"""
app/modules/avisos_qt.py — Recordatorios v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Recordatorios):

  Header        eyebrow
  Search row    3 step pills filtro ("Todos / Activos / Hoy") + búsqueda
  Grid 3-col    _ReminderCardV3 (NMCard) con NMIcon grande coloreado por
                categoría inferida + chip cat + nombre + hora chip mono +
                frecuencia + status badge + NMButton "Completar"
  Opciones      Card de silencio (horario) + autostart (Windows registry)

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  _save_reminder(), _toggle_active(), _delete_reminder(),
  _leer_silencio(), _guardar_silencio(),
  get_card_status(), schema DB ``recordatorios`` y ``config``.
"""

import os
import sys
import datetime
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QSizePolicy,
)

try:
    from shared.components import (
        NMModule,
        NMButton,
        NMCard,
        NMInput,
        NMSearchInput,
        NMToast,
        NMEmptyState,
        NMIcon,
    )
    from shared.theme_qt import (
        C,
        norm_modo,
        qfont,
        qcolor_to_rgba_css,
        v3c,
        V3_SP,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, leer_config, conexion
    from shared.visual_qa import visual_qa_enabled, reminder_rows
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButton,
        NMCard,
        NMInput,
        NMSearchInput,
        NMToast,
        NMEmptyState,
        NMIcon,
    )
    from shared.theme_qt import (
        C,
        norm_modo,
        qfont,
        v3c,
        V3_SP,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.visual_qa import visual_qa_enabled, reminder_rows

from shared.remote_config import t


# ── Day labels (preservados) ────────────────────────────────────────────────

DIAS_LABELS = ["L", "M", "X", "J", "V", "S", "D"]
# Canónico en shared (lo consume también el Hub); re-export para compatibilidad.
DIAS_FULL = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


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
    if any(k in m for k in ("ejerci", "yoga", "camin", "estira", "correr", "gimnasio", "gym")):
        return ("Actividad", "run", "teal")
    if any(
        k in m
        for k in (
            "comer",
            "comida",
            "almuerz",
            "almorz",
            "cena",
            "cenar",
            "desayun",
            "merienda",
            "merendar",
        )
    ):
        return ("Comida", "spark", "warning")
    if any(
        k in m
        for k in ("trabajo", "trabajar", "estudio", "estudiar", "tarea", "reunión", "reunion")
    ):
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

    today = _dt.datetime.now().weekday() + 1  # 1=Lunes
    return str(today) in dias.split(",")


def _bool_config(key: str, default: bool = True) -> bool:
    try:
        value = leer_config(key, "1" if default else "0")
    except Exception:
        return default
    text = str(value).strip().lower()
    if text in ("0", "false", "no", "off"):
        return False
    if text in ("1", "true", "yes", "on"):
        return True
    return default


def _load_support_messages() -> dict[str, list[str]]:
    patient_id = ""
    try:
        patient_id = leer_config("patient_id", "").strip()
    except Exception:
        pass
    scopes = []
    if patient_id:
        scopes.append(f"patient:{patient_id}")
    scopes.append("global")

    conn = None
    try:
        conn = obtener_conexion()
        for scope in scopes:
            rows = conn.execute(
                "SELECT categoria, mensaje FROM support_messages_cache "
                "WHERE scope = ? ORDER BY categoria, id",
                (scope,),
            ).fetchall()
            grouped: dict[str, list[str]] = {}
            for row in rows:
                categoria = row["categoria"] if hasattr(row, "keys") else row[0]
                mensaje = row["mensaje"] if hasattr(row, "keys") else row[1]
                if not mensaje:
                    continue
                grouped.setdefault(str(categoria or "Recordatorio"), []).append(str(mensaje))
            if grouped:
                return grouped
    except Exception:
        _log.exception("Failed to load support messages cache")
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    return {}


# ── _StepPill (filtro tabs) ─────────────────────────────────────────────────

_AVISOS_FILTER_PILL_HEIGHT = 32
_AVISOS_FILTER_PILL_RADIUS = _AVISOS_FILTER_PILL_HEIGHT // 2
_AVISOS_FILTER_PILL_CONTENT_HEIGHT = _AVISOS_FILTER_PILL_HEIGHT - 2


class _StepPill(QPushButton):
    """Step pill toggleable — usado para tabs filtro (Todos/Activos/Hoy).

    ``segmented=True`` renderiza la pill sin borde propio para vivir dentro de
    un contenedor segmentado (track surface2 + radio pill), tal como el frame
    de Avisos del prototipo polido.
    """

    def __init__(self, label: str, active: bool = False, modo: str = "dark_hybrid", segmented: bool = False, parent=None):
        super().__init__(label, parent)
        self._modo = norm_modo(modo)
        self._active = active
        self._segmented = segmented
        self.setFixedHeight(_AVISOS_FILTER_PILL_HEIGHT)
        self.setMinimumWidth(70)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(label)
        self.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._refresh()

    def set_active(self, active: bool):
        if active != self._active:
            self._active = active
            self._refresh()

    def _refresh(self):
        height = _AVISOS_FILTER_PILL_CONTENT_HEIGHT
        radius = _AVISOS_FILTER_PILL_RADIUS
        brand_line = qcolor_to_rgba_css(v3c("brandLine", self._modo))
        if self._active and self._segmented:
            self.setStyleSheet(
                f"QPushButton {{ background: {v3c('surface', self._modo).name()}; "
                f"color: {v3c('text', self._modo).name()}; "
                f"border: 1px solid {brand_line}; border-radius: {radius}px; "
                f"padding: 0px 14px; min-height: {height}px; max-height: {height}px; }}"
            )
        elif self._active:
            _p = QColor(v3c("primary", self._modo))
            self.setStyleSheet(
                f"QPushButton {{ background: {_p.name()}; "
                f"color: {v3c('primary_ink', self._modo).name()}; "
                f"border: 1px solid transparent; border-radius: {radius}px; "
                f"padding: 0px 14px; min-height: {height}px; max-height: {height}px; }}"
            )
        elif self._segmented:
            # Inactivo dentro del track segmentado: transparente, sin borde.
            self.setStyleSheet(
                f"QPushButton {{ background: transparent; "
                f"color: {v3c('text2', self._modo).name()}; "
                f"border: 1px solid transparent; border-radius: {radius}px; "
                f"padding: 0px 14px; min-height: {height}px; max-height: {height}px; }}"
                f"QPushButton:hover {{ "
                f"color: {v3c('text', self._modo).name()}; "
                f"background: {v3c('surface', self._modo).name()}; }}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{ background: transparent; "
                f"color: {v3c('text2', self._modo).name()}; "
                f"border: 1px solid {C('borderSoft', self._modo)}; "
                f"border-radius: {radius}px; padding: 0px 14px; "
                f"min-height: {height}px; max-height: {height}px; }}"
                f"QPushButton:hover {{ "
                f"border-color: {v3c('teal', self._modo).name()}; "
                f"color: {v3c('text', self._modo).name()}; }}"
            )


# ── _ReminderCardV3 ─────────────────────────────────────────────────────────


class _ReminderCardV3(QFrame):
    """Row v3 de recordatorio de 48px de alto: icono + mensaje + chip cat + hora + freq + status + Completar."""

    completed = pyqtSignal(int)  # rec_id
    deleted = pyqtSignal(int)
    toggled = pyqtSignal(int, bool)

    def __init__(self, row, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
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

        # Altura MÍNIMA, no fija (auditoría v1.0): el mensaje viene del Hub
        # (hasta 150 caracteres) y con wordwrap puede envolver a 2-3 líneas;
        # con altura fija el texto se recortaba o pisaba la fila de metadatos.
        self.setMinimumHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._build()
        self._apply_card_styles()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)

        # Icon
        self._icon = NMIcon(
            self._icon_name,
            size=18,
            color=v3c(self._color_token, self._modo).name(),
            modo=self._modo,
        )
        lay.addWidget(self._icon)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(4)

        # Mensaje (título)
        self._msg_lbl = QLabel(self._mensaje)
        self._msg_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._msg_lbl.setWordWrap(True)
        content.addWidget(self._msg_lbl)

        meta = QHBoxLayout()
        meta.setSpacing(8)
        # Sans suave, sin monospace: el mono con caja tintada se leía técnico
        # ("texto duro de developer"), peor en light (informe owner v1.0).
        self._meta_lbl = QLabel(f"{self._cat_name} · {self._hora}")
        self._meta_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        meta.addWidget(self._meta_lbl)
        self._freq_lbl = QLabel(_format_frequency(self._dias))
        self._freq_lbl.setFont(qfont("size_caption_xs"))
        meta.addWidget(self._freq_lbl)
        meta.addStretch()
        content.addLayout(meta)
        lay.addLayout(content, stretch=1)

        # Status badge
        self._status_lbl = QLabel("")
        self._status_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._status_lbl.setContentsMargins(10, 0, 10, 0)
        # Pill real (ADN): alto fijo + radio = mitad; si el label se estira a
        # la altura de la fila queda rect redondeado fuera de canon.
        self._status_lbl.setFixedHeight(22)
        lay.addWidget(self._status_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Completar button
        self._btn_done = NMButton(
            t("text.module.avisos.complete_btn", "Completar"),
            variant="secondary", size="sm", modo=self._modo, width=98
        )
        self._btn_done.setFixedHeight(28)
        # Conserva el ancho aunque se oculte (filas completadas): mantiene la
        # columna de badges alineada con las filas pendientes (ver _apply_card_styles).
        _sp = self._btn_done.sizePolicy()
        _sp.setRetainSizeWhenHidden(True)
        self._btn_done.setSizePolicy(_sp)
        self._btn_done.clicked.connect(lambda: self.completed.emit(self._id))
        lay.addWidget(self._btn_done)

    def _apply_card_styles(self):
        line_color = C("borderSoft", self._modo)
        text_color = v3c("text", self._modo).name()
        hover_bg = v3c("surface2", self._modo).name()
        bg = v3c("surfaceSolid" if "dark" in self._modo else "surface", self._modo).name()
        hover_border = v3c("teal", self._modo).name()

        self.setStyleSheet(
            f"_ReminderCardV3 {{ border: 1px solid {line_color}; border-radius: 14px; "
            f"background: {bg}; }}"
            f"_ReminderCardV3:hover {{ background: {hover_bg}; border-color: {hover_border}; }}"
            f"QLabel {{ background: transparent; color: {text_color}; }}"
        )

        # Metadatos — color de categoría a texto desnudo, sin caja tintada:
        # la caja + mono se leía como rótulo técnico (informe owner v1.0).
        cat_color = v3c(self._color_token, self._modo).name()
        self._meta_lbl.setStyleSheet(f"color: {cat_color}; background: transparent;")

        # Frecuencia
        self._freq_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )

        # Status badge
        if self._done:
            stat_color = v3c("success", self._modo).name()
            stat_text = "Completado"
        elif not self._activo:
            stat_color = v3c("ink_secondary", self._modo).name()
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
            f"color: {stat_color}; background: {bg_stat}; border-radius: 11px;"
        )
        if self._done:
            # Sin duplicación visual Completado/Hecho (Fase 10): el estado ya lo
            # comunica el badge "Completado"; se oculta el botón "Hecho"
            # redundante (no hay acción posible sobre un aviso ya completado).
            self._btn_done.setVisible(False)
        else:
            self._btn_done.setVisible(True)
            self._btn_done.setText(t("text.module.avisos.complete_btn", "Completar"))
            self._btn_done.setEnabled(self._activo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._apply_card_styles()


# ── ModuloAvisos v3 ─────────────────────────────────────────────────────────


class ModuloAvisos(NMModule):
    MODULE_TITLE = "Recordatorios"
    MODULE_ICON = "avisos"

    def build_ui(self):
        self._search_query: str = ""
        self._current_filter: str = "todos"  # "todos" | "activos" | "hoy"
        self._all_rows: list = []

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        outer.addWidget(body)

        lay = QVBoxLayout(body)
        # Gaps verticales xs: el stack (filtros+lista+silencio) entra en 960×600.
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        lay.setSpacing(V3_SP["xs"])

        # 1. Header eyebrow (sin CTA "+ Nuevo aviso": los recordatorios los
        # determina el profesional desde el Hub; el paciente solo los lee/marca).
        header_row = QHBoxLayout()
        header_row.setSpacing(V3_SP["md"])
        self._eyebrow = QLabel(t("text.module.avisos.eyebrow", "Recordatorios"))
        self._eyebrow.setFont(eyebrow_font())
        header_row.addWidget(self._eyebrow)
        self._eyebrow.hide()  # BL-07: título de módulo ahora en la titlebar
        header_row.addStretch()
        lay.addLayout(header_row)

        # 2. Filtros + búsqueda, como el mockup de Recordatorios.
        # Polish visual: pills agrupadas en un track segmentado (surface2 +
        # radio pill), con search compacto a la derecha.
        _TRACK_H = _AVISOS_FILTER_PILL_HEIGHT + 8  # 40px — track = pill + 4px inset top+bottom
        self._filter_segment = QFrame()
        self._filter_segment.setObjectName("FilterSegment")
        self._filter_segment.setStyleSheet(self._segment_qss(self._modo))
        self._filter_segment.setFixedHeight(_TRACK_H)
        seg_lay = QHBoxLayout(self._filter_segment)
        seg_lay.setContentsMargins(4, 4, 4, 4)
        seg_lay.setSpacing(4)
        self._filter_pills: dict[str, _StepPill] = {}
        for key, label in (
            ("todos", t("text.module.avisos.filter_all", "Todos")),
            ("activos", t("text.module.avisos.filter_active", "Activos")),
            ("hoy", t("text.module.avisos.filter_today", "Hoy")),
        ):
            pill = _StepPill(label, active=(key == "todos"), modo=self._modo, segmented=True)
            pill.setMinimumWidth(70)
            pill.setFixedHeight(_AVISOS_FILTER_PILL_HEIGHT)
            pill.clicked.connect(lambda _, k=key: self._on_filter_changed(k))
            self._filter_pills[key] = pill
            seg_lay.addWidget(pill)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(V3_SP["sm"])
        filter_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(self._filter_segment)
        self._search_input = NMSearchInput(
            t("text.module.avisos.search_placeholder", "Buscar recordatorio…"),
            modo=self._modo,
        )
        self._search_input.setMinimumWidth(220)
        self._search_input.setMaximumWidth(340)
        self._search_input.setFixedHeight(_TRACK_H)
        self._search_input.text_changed.connect(self._on_search)
        self._search_edit = self._search_input._edit
        filter_row.addWidget(self._search_input, stretch=1)
        lay.addLayout(filter_row)

        # 3. Vertical list with scroll
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._list_widget)
        lay.addWidget(self._scroll, stretch=1)

        # 4. P2.H: footer "_DayProgressCard" eliminado (la supervisión es del Hub;
        # el paciente ya ve "N/M" en cada card de recordatorio).

        # 5. Opciones: solo silencio (autostart ya no se usa).
        if not visual_qa_enabled():
            self._build_opciones(lay)

        self._apply_text_styles()
        self._load_reminders()

    def _apply_text_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"background: transparent;"
        )
        # Handoff §5: serif display for title if needed, but RECORDATORIOS is eyebrow
        # If we had a main title here it would be serif.

    def _segment_qss(self, modo: str) -> str:
        """Track del filtro segmentado Todos/Activos/Hoy (surface2 + radio pill)."""
        m = norm_modo(modo)
        return (
            f"#FilterSegment {{ background: {v3c('surface2', m).name()}; "
            f"border: 1px solid {C('borderSoft', m)}; "
            f"border-radius: 999px; }}"
        )

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_eyebrow"):
            self._apply_text_styles()
        for pill in getattr(self, "_filter_pills", {}).values():
            pill._modo = self._modo
            pill._refresh()
        if hasattr(self, "_filter_segment"):
            self._filter_segment.setStyleSheet(self._segment_qss(self._modo))
        if hasattr(self, "_search_input"):
            self._search_input._apply_theme(self._modo)
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
                    "SELECT id, hora, mensaje, dias, activo FROM recordatorios ORDER BY hora"
                ).fetchall()
                conn.close()
            except Exception:
                self._all_rows = []
        # P2.H: ya no hay footer de progreso del día (la supervisión es del Hub).
        self._render_reminders()

    def _row_get(self, row, key, idx):
        return row[key] if hasattr(row, "keys") else row[idx]

    def _render_reminders(self):
        # Clear grid
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        rows = list(self._all_rows)
        # Search filter
        if self._search_query:
            rows = [
                r
                for r in rows
                if self._search_query in self._row_get(r, "mensaje", 2).lower()
                or self._search_query in self._row_get(r, "hora", 1).lower()
            ]
        # Tab filter
        if self._current_filter == "activos":
            rows = [r for r in rows if self._row_get(r, "activo", 4)]
        elif self._current_filter == "hoy":
            rows = [
                r
                for r in rows
                if self._row_get(r, "activo", 4) and _is_today(self._row_get(r, "dias", 3) or "")
            ]

        if not rows:
            empty_msg = (
                t("text.module.avisos.empty_title", "Sin recordatorios asignados")
                if not self._all_rows
                else t("text.module.avisos.empty_filter_title", "Sin resultados con esos filtros")
            )
            empty_sub = (
                t(
                    "text.module.avisos.empty_desc",
                    "Tu profesional configura tus recordatorios de bienestar desde el Hub.",
                )
                if not self._all_rows
                else t("text.module.avisos.empty_filter_desc", "Probá cambiar los filtros.")
            )
            empty = NMEmptyState("bell", empty_msg, empty_sub, parent=self._list_widget)
            # 4.2: empty state centrado verticalmente dentro del scroll (no
            # alineado al top como una fila más). El AlignTop del layout (modo
            # lista) anularía los stretches y comprimiría el NMEmptyState a su
            # sizeHint (título pisando el ícono, subtítulo cortado): se
            # neutraliza mientras no haya filas.
            self._list_layout.setAlignment(Qt.AlignmentFlag(0))
            self._list_layout.addStretch(1)
            self._list_layout.addWidget(empty)
            self._list_layout.addStretch(1)
            # 4.2: la card de Silencio no aporta cuando no hay recordatorios
            # (el paciente no tiene avisos que silenciar). Ocultarla para que
            # el empty state domine el viewport y no compita por altura.
            if hasattr(self, "_silencio_card"):
                self._silencio_card.setVisible(bool(self._all_rows))
            return

        # 4.2: con recordatorios, mostrar la card de Silencio y restaurar el
        # empaquetado al top de la lista.
        if hasattr(self, "_silencio_card"):
            self._silencio_card.setVisible(True)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for row in rows:
            card = _ReminderCardV3(row, modo=self._modo)
            card.completed.connect(self._on_completar)
            self._list_layout.addWidget(card)

    # ── Acciones de cards ────────────────────────────────────────────────────

    def _on_completar(self, rec_id: int):
        """'Completar' deactiva el aviso (interpretación v3 del README)."""
        saved = self._toggle_active(rec_id, False)
        self._load_reminders()
        if saved:
            self._sync_inmediato_background()
        NMToast.display(self.window(), "Aviso completado", variant="success", duration_ms=1500)

    # ── _toggle_active (lógica preservada exacta) ───────────────────────────

    def _toggle_active(self, rec_id: int, checked: bool):
        if visual_qa_enabled():
            self._load_reminders()
            return False
        completado_en = None
        if not checked:
            completado_en = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            with conexion() as conn:
                try:
                    conn.execute(
                        "UPDATE recordatorios SET activo = ?, completado_en = ? WHERE id = ?",
                        (1 if checked else 0, completado_en, rec_id),
                    )
                except Exception as e:
                    if "completado_en" not in str(e):
                        raise
                    conn.execute(
                        "UPDATE recordatorios SET activo = ? WHERE id = ?",
                        (1 if checked else 0, rec_id),
                    )
            return True
        except Exception:
            _log.exception("Failed to save reminder")
            return False

    def _sync_inmediato_background(self):
        if visual_qa_enabled():
            return
        try:
            from shared import sync as sync_module

            sync_module.sync_inmediato_background()
        except Exception:
            _log.exception("Failed to trigger immediate sync after reminder completion")

    # ── _delete_reminder (lógica preservada exacta) ─────────────────────────

    def _delete_reminder(self, rec_id: int):
        if visual_qa_enabled():
            self._load_reminders()
            return
        try:
            with conexion() as conn:
                conn.execute("DELETE FROM recordatorios WHERE id = ?", (rec_id,))
        except Exception:
            _log.exception("Failed to delete reminder %s", rec_id)
        self._load_reminders()

    # ── Opciones del sistema (silencio + autostart) ─────────────────────────

    def _build_opciones(self, parent_layout: QVBoxLayout):
        """Card OPCIONES: solo el horario de silencio (autostart eliminado)."""
        opts_card = NMCard(modo=self._modo, clickable=False)
        opts_lay = QVBoxLayout(opts_card)
        opts_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        opts_lay.setSpacing(V3_SP["sm"])

        opts_eyebrow = QLabel(t("text.module.avisos.silence_eyebrow", "Silencio"))
        opts_eyebrow.setFont(eyebrow_font())
        opts_eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"background: transparent;"
        )
        opts_lay.addWidget(opts_eyebrow)
        self._opts_eyebrow = opts_eyebrow

        # Silencio
        sil_ini, sil_fin = self._leer_silencio()
        sil_row = QHBoxLayout()
        sil_row.setSpacing(V3_SP["sm"])
        sil_lbl = QLabel(t("text.module.avisos.silence_label", "Horario de silencio"))
        sil_lbl.setFont(qfont("size_small"))
        sil_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        sil_row.addWidget(sil_lbl)
        sil_row.addStretch()
        self._entry_sil_ini = NMInput("22:00", modo=self._modo)
        self._entry_sil_ini.setFixedSize(70, 32)
        if sil_ini:
            self._entry_sil_ini.setText(sil_ini)
        sil_row.addWidget(self._entry_sil_ini)
        arrow = QLabel("→")
        arrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        sil_row.addWidget(arrow)
        self._entry_sil_fin = NMInput("08:00", modo=self._modo)
        self._entry_sil_fin.setFixedSize(70, 32)
        if sil_fin:
            self._entry_sil_fin.setText(sil_fin)
        sil_row.addWidget(self._entry_sil_fin)
        btn_apply = NMButton(
            t("text.module.avisos.apply_btn", "Aplicar"),
            variant="secondary", size="sm", modo=self._modo, width=80
        )
        btn_apply.clicked.connect(self._guardar_silencio)
        self._btn_apply_silencio = btn_apply
        sil_row.addWidget(btn_apply)
        opts_lay.addLayout(sil_row)

        # 4.2: exponer la card de Silencio para poder ocultarla cuando no hay
        # recordatorios (el empty state domina el viewport sin competencia).
        self._silencio_card = opts_card
        parent_layout.addWidget(opts_card)

    # ── Silencio (lógica preservada exacta) ─────────────────────────────────

    def _leer_silencio(self):
        try:
            conn = obtener_conexion()
            ini = conn.execute("SELECT valor FROM config WHERE clave='silencio_inicio'").fetchone()
            fin = conn.execute("SELECT valor FROM config WHERE clave='silencio_fin'").fetchone()
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
            with conexion() as conn:
                for clave, valor in (("silencio_inicio", ini), ("silencio_fin", fin)):
                    if valor:
                        conn.execute(
                            "INSERT INTO config (clave, valor) VALUES (?, ?) "
                            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                            (clave, valor),
                        )
                    else:
                        conn.execute("DELETE FROM config WHERE clave=?", (clave,))
            if hasattr(self._btn_apply_silencio, "play_success"):
                self._btn_apply_silencio.play_success()
        except Exception:
            _log.exception("Failed to save silencio config")

    # ── Hooks ────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._load_reminders()

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "4 activos"
        try:
            conn = obtener_conexion()
            row = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE activo = 1").fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} activo{'s' if n > 1 else ''}"
        except Exception:
            _log.exception("Failed to get card status for avisos")
        return ""
