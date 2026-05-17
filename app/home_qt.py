"""
app/home_qt.py — Vista Home v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Inicio):

  Header        ¡Hola, [nombre]! + subtítulo + chip streak + NMToggle (theme)
  Hero card     Ring 120 + Bienestar general + número grande + estado + microcopy
  Wave chart    Evolución 7 días (NMWaveChart) en NMCard
  KPI row       3 NMCard (Sesiones / Minutos respiración / Actividades)
  Modules grid  7 ModuleCard (responsive 1/2/3 columnas)
  Bottom 3-col  Actividades recomendadas / Sesión rápida / Avisos próximos
  Footer        Cita motivacional + CTA NMButton gradient

NO modifica lógica de DB / sync / permisos (solo lectura) ni callbacks
externos (`on_module_open`, `get_status_fn`). Compatibilidad pública:
    HomeView(modo, on_module_open, get_status_fn, username, parent)
    .set_modo(modo) / .refresh_statuses() / .resizeEvent()
"""

import os
import sys
import datetime as _dt
from datetime import datetime

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    QAbstractAnimation, QPoint,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QFrame, QGraphicsOpacityEffect,
)

try:
    from shared.theme_qt import (
        C, colors, norm_modo, qfont,
        interpolate_color, gradient_colors,
        ThemeAwareWidgetMixin, SessionColor, aura_opacity,
        v3c, v3_linear_gradient, V3_SP, V3_RD,
        stylesheet_scrollarea,
    )
    from shared.theme import TYPOGRAPHY
    from shared.components_qt import (
        ThemeManager, responsive_columns,
        NMCard, NMIcon, NMModuleRing, NMButton, NMPlayButton, NMToggle,
        NMStreakBadge, NMWaveChart, NMProgressLine, NMWelcomeBar,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C, colors, norm_modo, qfont,
        interpolate_color, gradient_colors,
        ThemeAwareWidgetMixin, SessionColor, aura_opacity,
        v3c, v3_linear_gradient, V3_SP, V3_RD,
        stylesheet_scrollarea,
    )
    from shared.theme import TYPOGRAPHY
    from shared.components_qt import (
        ThemeManager, responsive_columns,
        NMCard, NMIcon, NMModuleRing, NMButton, NMPlayButton, NMToggle,
        NMStreakBadge, NMWaveChart, NMProgressLine, NMWelcomeBar,
    )

from shared.visual_qa import visual_qa_enabled


# ── Configuración de módulos (v3 con nombre de icono SVG) ─────────────────────

MODULES_CONFIG = [
    {"id": "animo",       "icon_v3": "mood",    "title": "Ánimo",
     "desc": "Registro emocional diario",     "chip": "Bienestar"},
    {"id": "respiracion", "icon_v3": "breath",  "title": "Respiración",
     "desc": "Técnicas de calma 4-7-8",        "chip": "Calma"},
    {"id": "registro",    "icon_v3": "brain",   "title": "TCC",
     "desc": "Pensamientos automáticos",        "chip": "Cognitivo"},
    {"id": "rutina",      "icon_v3": "routine", "title": "Rutina",
     "desc": "Checklist del día",                "chip": "Hábitos"},
    {"id": "actividades", "icon_v3": "run",     "title": "Actividades",
     "desc": "Activación conductual",            "chip": "Acción"},
    {"id": "timer",       "icon_v3": "timer",   "title": "Timer",
     "desc": "Sesiones de enfoque",              "chip": "Focus"},
    {"id": "avisos",      "icon_v3": "bell",    "title": "Avisos",
     "desc": "Recordatorios del día",            "chip": "Diario"},
]


def _dot_color(idx: int, modo: str) -> str:
    """Color del gradiente teal→violet según posición del módulo."""
    grad = gradient_colors(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[-1], t)


def _wellness_label(score: int) -> str:
    """Convierte un score 0-100 a etiqueta del estado de bienestar."""
    if score >= 85: return "Excelente"
    if score >= 70: return "Bueno"
    if score >= 50: return "Normal"
    if score >= 30: return "Atención"
    return "Necesita apoyo"


# ── Lectura de datos (sin escritura, fallback graceful) ──────────────────────

def _load_streak() -> int:
    """Días consecutivos con al menos un registro de ánimo."""
    if visual_qa_enabled():
        return 7
    try:
        from shared.db import obtener_conexion
        con = obtener_conexion()
        cur = con.execute(
            "SELECT DISTINCT date(fecha) AS d FROM registros_animo "
            "ORDER BY d DESC LIMIT 30"
        )
        rows = [r["d"] for r in cur.fetchall()]
        if not rows:
            return 0
        today = _dt.date.today()
        streak = 0
        for i, d_str in enumerate(rows):
            expected = today - _dt.timedelta(days=i)
            if str(expected) == d_str:
                streak += 1
            else:
                break
        return streak
    except Exception:
        return 0


def _load_weekly_mood() -> tuple[list, list]:
    """(current_week, previous_week) — 7 valores cada uno (None = sin dato)."""
    if visual_qa_enabled():
        return [4, 5, 6, 5.5, 7, 8, 7.5], [3, 4, 5, 4.5, 6, 6.5, 7]
    try:
        from shared.db import obtener_conexion
        con = obtener_conexion()
        today = _dt.date.today()
        current, previous = [None] * 7, [None] * 7
        for i in range(7):
            d_curr = today - _dt.timedelta(days=6 - i)
            d_prev = d_curr - _dt.timedelta(days=7)
            row = con.execute(
                "SELECT AVG(valor) AS v FROM registros_animo WHERE date(fecha)=?",
                (str(d_curr),)).fetchone()
            if row and row["v"] is not None:
                current[i] = float(row["v"])
            row2 = con.execute(
                "SELECT AVG(valor) AS v FROM registros_animo WHERE date(fecha)=?",
                (str(d_prev),)).fetchone()
            if row2 and row2["v"] is not None:
                previous[i] = float(row2["v"])
        return current, previous
    except Exception:
        return [None] * 7, [None] * 7


def _wellness_from_week(weekly: list) -> int:
    """Promedia los valores no-None y mapea 0-10 → 0-100."""
    valid = [v for v in weekly if v is not None]
    if not valid:
        return 0
    return int(round((sum(valid) / len(valid)) * 10))


def _load_kpis_today() -> dict:
    """Conteos del día (sesiones timer / min respiración / actividades)."""
    if visual_qa_enabled():
        return {"sesiones": 3, "respiracion_min": 12, "actividades": 4}
    out = {"sesiones": 0, "respiracion_min": 0, "actividades": 0}
    try:
        from shared.db import obtener_conexion
        con = obtener_conexion()
        today = str(_dt.date.today())
        # Cada query es independiente — un fallo no rompe los demás
        for key, sql in (
            ("sesiones",
             "SELECT COUNT(*) AS c FROM sesiones_timer WHERE date(fecha)=?"),
            ("actividades",
             "SELECT COUNT(*) AS c FROM actividades_completadas WHERE date(fecha)=?"),
        ):
            try:
                row = con.execute(sql, (today,)).fetchone()
                out[key] = int(row["c"] if row and row["c"] is not None else 0)
            except Exception:
                pass
        try:
            row = con.execute(
                "SELECT COALESCE(SUM(duracion_segundos),0) AS s "
                "FROM sesiones_respiracion WHERE date(fecha)=?",
                (today,)).fetchone()
            out["respiracion_min"] = int(round(
                (row["s"] if row and row["s"] is not None else 0) / 60))
        except Exception:
            pass
    except Exception:
        pass
    return out


def _load_upcoming_avisos(limit: int = 3) -> list[tuple[str, str]]:
    """Próximos avisos (hora, descripción)."""
    if visual_qa_enabled():
        return [
            ("09:00", "Tomar medicación"),
            ("14:30", "Sesión con Dra. Martínez"),
            ("19:00", "Ejercicio de respiración"),
        ]
    try:
        from shared.db import obtener_conexion
        con = obtener_conexion()
        cur = con.execute(
            "SELECT hora, descripcion FROM avisos "
            "WHERE activo=1 ORDER BY hora LIMIT ?", (limit,))
        return [(r["hora"], r["descripcion"]) for r in cur.fetchall()]
    except Exception:
        return []


_RECOMMENDED = [
    ("leaf",    "Caminata corta",      "10 min al aire libre"),
    ("breath",  "Respiración 4-7-8",   "3 ciclos guiados"),
    ("note",    "Escribir 3 logros",   "Reforzar lo positivo"),
]


_QUOTES = [
    "Cada pequeño paso es un paso adelante.",
    "Hoy también es un buen día para empezar.",
    "La constancia es más poderosa que la perfección.",
    "Tu bienestar es un proyecto que merece tiempo.",
    "Lo importante no es la velocidad, es la dirección.",
    "Sentirse mal no es un fracaso, es información.",
    "El descanso también es productivo.",
]


def _daily_quote() -> str:
    """Cita rotativa según el día del año."""
    return _QUOTES[_dt.date.today().toordinal() % len(_QUOTES)]


# ── ModuleCard v3 ─────────────────────────────────────────────────────────────

class ModuleCard(ThemeAwareWidgetMixin, QWidget):
    """Card de módulo v3 — surface limpia, NMIcon SVG, NMModuleRing v3.

    Hover: border-color borderSoft → borderStrong (sin scale, sin glow extra).
    """

    def __init__(self, config: dict, idx: int, modo: str,
                 on_click, get_status_fn, parent=None):
        super().__init__(parent)
        self._config = config
        self._idx = idx
        self._modo = norm_modo(modo)
        self._on_click = on_click
        self._get_status = get_status_fn
        self._accent = _dot_color(idx, modo)
        self._hover = False
        self._disabled = False
        self._disabled_reason = ""

        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Minimum)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(0.0)
        self.setGraphicsEffect(self._eff)

        self._build_ui()
        self._connect_theme()

    # ── build ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                  V3_SP["lg"], V3_SP["lg"])
        layout.setSpacing(V3_SP["sm"])

        # Top: icono SVG + chip subcontexto
        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._icon = NMIcon(self._config["icon_v3"], size=36,
                            color_key="text", modo=self._modo)
        top.addWidget(self._icon)
        top.addStretch()
        self._chip = QLabel(self._config.get("chip", ""))
        self._chip.setFont(qfont("size_caption_xs",
                                  weight=TYPOGRAPHY["weight_semibold"]))
        self._chip.setContentsMargins(8, 2, 8, 2)
        top.addWidget(self._chip)
        layout.addLayout(top)

        # Título + descripción
        self._title_lbl = QLabel(self._config["title"])
        self._title_lbl.setFont(qfont("size_h3",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        layout.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(self._config["desc"])
        self._desc_lbl.setFont(qfont("size_caption"))
        self._desc_lbl.setWordWrap(True)
        layout.addWidget(self._desc_lbl)

        layout.addStretch()

        # Bottom: badge status + mini ring v3
        bottom = QHBoxLayout()
        bottom.setSpacing(V3_SP["sm"])
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption",
                                   weight=TYPOGRAPHY["weight_semibold"]))
        self._badge.setContentsMargins(8, 3, 8, 3)
        bottom.addWidget(self._badge)
        bottom.addStretch()
        self._ring = NMModuleRing(size=32, pct=0.0, modo=self._modo)
        bottom.addWidget(self._ring)
        layout.addLayout(bottom)

        self._apply_styles()
        self._refresh_status()

    def _apply_styles(self):
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        chip_bg = v3c("borderSoft", self._modo).name()
        chip_fg = v3c("text2", self._modo).name()
        self._chip.setStyleSheet(
            f"color: {chip_fg}; background: {chip_bg}; "
            f"border-radius: 8px;")

    # ── status badge ─────────────────────────────────────────────────────────

    def _pill_style(self, color_hex: str, alpha_bg: float = 0.14) -> str:
        c = QColor(color_hex)
        a = int(alpha_bg * 255)
        return (
            f"color: {color_hex}; "
            f"background-color: rgba({c.red()},{c.green()},{c.blue()},{a}); "
            f"border-radius: 10px; padding: 2px 8px;")

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        if self._disabled:
            self._badge.setText("No disponible")
            self._badge.setStyleSheet(
                self._pill_style(C("warning", self._modo)))
            self._ring.set_pct(0.0)
            return
        if status:
            mid = self._config["id"]
            low = status.lower()
            if "completo" in low:
                color = C("success", self._modo)
            elif ("progreso" in low or "listos" in low or "/" in status):
                color = C("warning", self._modo)
            elif mid == "avisos":
                color = C("warning", self._modo)
            elif mid == "timer":
                color = C("accent", self._modo)
            elif mid == "rutina":
                if status.startswith("✓"):
                    color = C("success", self._modo)
                elif "/" in status:
                    color = C("warning", self._modo)
                else:
                    color = C("teal", self._modo)
            else:
                color = C("teal", self._modo)
            self._badge.setText(status)
            self._badge.setStyleSheet(self._pill_style(color))
        else:
            self._badge.setText("")
            self._badge.setStyleSheet("background: transparent;")
        self._update_ring(status)

    def _update_ring(self, status: str = None):
        if status is None:
            status = self._get_status(self._config["id"])
        if not status:
            self._ring.set_pct(0.0)
            return
        clean = status.replace("✓", "").replace("✔", "").strip()
        if "En progreso" in clean:
            self._ring.set_pct(0.65 if self._config["id"] == "animo" else 0.50)
        elif clean == "Activo":
            self._ring.set_pct(0.84)
        elif clean == "Completo":
            self._ring.set_pct(1.0)
        elif "3 hoy" in clean:
            self._ring.set_pct(0.70)
        elif "45 min" in clean:
            self._ring.set_pct(0.75)
        elif "2/5" in clean:
            self._ring.set_pct(0.40)
        elif "/" in clean:
            try:
                parts = clean.split("/")
                done = int(parts[0].strip())
                total = int(parts[1].strip().split()[0])
                self._ring.set_pct(done / total if total > 0 else 0.0)
            except Exception:
                self._ring.set_pct(0.0)
        elif self._config["id"] != "avisos":
            self._ring.set_pct(1.0)
        else:
            self._ring.set_pct(0.0)

    # ── paint v3 ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = "dark" in self._modo
        r = V3_RD["lg"]
        w, h = self.width(), self.height()
        rect = QRectF(0, 0, w, h)

        surface_key = "surfaceSolid" if is_dark else "surface"
        p.setBrush(QBrush(v3c(surface_key, self._modo)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        border_key = ("borderStrong"
                      if (self._hover and self.isEnabled() and not self._disabled)
                      else "borderSoft")
        p.setPen(QPen(v3c(border_key, self._modo), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        if self._disabled:
            p.fillRect(rect, QColor(255, 255, 255, 20 if is_dark else 80))
        p.end()

    # ── eventos ──────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if (not self._disabled
                and event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.pos())):
            self._on_click(self._config["id"])
        super().mouseReleaseEvent(event)

    # ── stagger anim de entrada ──────────────────────────────────────────────

    def animate_enter(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
        if self._eff is None:
            return
        anim_fade = QPropertyAnimation(self._eff, b"opacity", self)
        anim_fade.setDuration(320)
        anim_fade.setStartValue(0.0)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_fade_done():
            if self._eff is not None:
                self._eff.deleteLater()
                self._eff = None
            self.setGraphicsEffect(None)

        anim_fade.finished.connect(_on_fade_done)
        anim_fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        orig_y = self.y()
        self.move(self.x(), orig_y + 20)
        anim_move = QPropertyAnimation(self, b"pos", self)
        anim_move.setDuration(320)
        anim_move.setStartValue(QPoint(self.x(), self.y()))
        anim_move.setEndValue(QPoint(self.x(), orig_y))
        anim_move.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_move.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _dot_color(self._idx, self._modo)
        self._icon._modo = self._modo
        self._icon._render()
        self._apply_styles()
        self._ring._modo = self._modo
        self._ring.update()
        if self._eff is None or self._eff.opacity() >= 1.0:
            if self._eff is not None:
                self._eff.deleteLater()
                self._eff = None
            self.setGraphicsEffect(None)
        self._refresh_status()
        self.update()

    def refresh(self):
        self._refresh_status()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        self.setCursor(Qt.CursorShape.ForbiddenCursor if state
                       else Qt.CursorShape.PointingHandCursor)
        self._refresh_status()
        self.update()


# ── Hero · Wellness card ─────────────────────────────────────────────────────

class _HeroCard(NMCard):
    """Hero v3: ring 120 + 'Bienestar general' + número grande + estado."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._score = 0
        self._build()

    def _build(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                             V3_SP["xl"], V3_SP["xl"])
        h.setSpacing(V3_SP["xl"])

        # Ring grande
        self._ring = NMModuleRing(size=120, pct=0.0, modo=self._modo)
        h.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Cluster derecho
        col = QVBoxLayout()
        col.setSpacing(4)
        self._eyebrow = QLabel("BIENESTAR GENERAL")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._eyebrow)

        num_row = QHBoxLayout()
        num_row.setSpacing(10)
        num_row.setAlignment(Qt.AlignmentFlag.AlignBaseline)
        self._num_lbl = QLabel("—")
        self._num_lbl.setFont(qfont("size_display",
                                     weight=TYPOGRAPHY["weight_bold"]))
        num_row.addWidget(self._num_lbl)
        self._state_lbl = QLabel("Sin datos")
        self._state_lbl.setFont(qfont("size_h2",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        num_row.addWidget(self._state_lbl)
        num_row.addStretch()
        col.addLayout(num_row)

        self._micro_lbl = QLabel(
            "Calculado a partir de tu actividad de los últimos 7 días.")
        self._micro_lbl.setFont(qfont("size_small"))
        self._micro_lbl.setWordWrap(True)
        col.addWidget(self._micro_lbl)
        col.addStretch()

        h.addLayout(col, stretch=1)
        self._apply_text_styles()

    def set_score(self, score: int):
        self._score = max(0, min(100, int(score)))
        self._ring.set_pct(self._score / 100.0)
        if self._score == 0:
            self._num_lbl.setText("—")
            self._state_lbl.setText("Sin datos")
        else:
            self._num_lbl.setText(str(self._score))
            self._state_lbl.setText(_wellness_label(self._score))
        self._apply_text_styles()

    def _apply_text_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        self._num_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self._state_lbl.setStyleSheet(
            f"color: {v3c('teal', self._modo).name()}; background: transparent;")
        self._micro_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_text_styles()


# ── KPI card ─────────────────────────────────────────────────────────────────

class _KpiCard(NMCard):
    """KPI v3: icono + label + valor + barra de progreso fina (NMProgressLine)."""

    def __init__(self, icon_name: str, label: str,
                 value: str, pct: float = 0.0,
                 modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._icon_name = icon_name
        self._label_text = label
        self._value_text = value
        self._pct = max(0.0, min(1.0, pct))
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                               V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["sm"])

        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._icon = NMIcon(self._icon_name, size=24,
                            color_key="teal", modo=self._modo)
        top.addWidget(self._icon)
        self._label_lbl = QLabel(self._label_text)
        self._label_lbl.setFont(qfont("size_small"))
        top.addWidget(self._label_lbl)
        top.addStretch()
        lay.addLayout(top)

        self._value_lbl = QLabel(self._value_text)
        self._value_lbl.setFont(qfont("size_h2",
                                       weight=TYPOGRAPHY["weight_bold"]))
        lay.addWidget(self._value_lbl)

        self._bar = NMProgressLine(modo=self._modo)
        self._bar.set_progress(self._pct)
        lay.addWidget(self._bar)

        self._apply_kpi_styles()

    def set_value(self, value: str, pct: float):
        self._value_text = value
        self._pct = max(0.0, min(1.0, pct))
        self._value_lbl.setText(value)
        self._bar.set_progress(self._pct)

    def _apply_kpi_styles(self):
        self._label_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        self._value_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._icon._modo = self._modo
        self._icon._render()
        self._bar._modo = self._modo
        self._bar.update()
        self._apply_kpi_styles()


# ── NMProgressLine helper: el componente actual no tiene set_progress(float).
#    Adaptador inline para no tocar components_qt.py de nuevo.

if not hasattr(NMProgressLine, "set_progress"):
    def _np_set_progress(self, pct: float):
        pct = max(0.0, min(1.0, float(pct)))
        # NMProgressLine usa (total, current) — simular con escala 100
        self._total = 100
        self._current = int(round(pct * 100))
        self.update()
    NMProgressLine.set_progress = _np_set_progress


# ── Bottom 3-col cards ───────────────────────────────────────────────────────

class _RecommendationsCard(NMCard):
    """Lista 3 items con NMIcon + título + descripción + NMPlayButton."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                               V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["md"])

        self._eyebrow = QLabel("RECOMENDADAS")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)

        for icon_name, title, desc in _RECOMMENDED:
            row = QHBoxLayout()
            row.setSpacing(V3_SP["sm"])
            icon = NMIcon(icon_name, size=24, color_key="teal",
                          modo=self._modo)
            row.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)
            col = QVBoxLayout()
            col.setSpacing(0)
            t = QLabel(title)
            t.setFont(qfont("size_small",
                             weight=TYPOGRAPHY["weight_semibold"]))
            d = QLabel(desc)
            d.setFont(qfont("size_caption"))
            col.addWidget(t)
            col.addWidget(d)
            row.addLayout(col, stretch=1)
            play = NMPlayButton(icon_name="play", size="sm",
                                modo=self._modo)
            row.addWidget(play, alignment=Qt.AlignmentFlag.AlignVCenter)
            wrap = QWidget()
            wrap.setLayout(row)
            lay.addWidget(wrap)
            # Mantener refs para theme
            wrap._icon = icon
            wrap._title = t
            wrap._desc = d
            wrap._play = play
        lay.addStretch()
        self._apply_rec_styles()

    def _apply_rec_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        for child in self.findChildren(QLabel):
            if child is self._eyebrow:
                continue
            # Diferenciar título vs descripción por font weight
            if child.font().weight() >= 600:
                child.setStyleSheet(
                    f"color: {v3c('text', self._modo).name()}; background: transparent;")
            else:
                child.setStyleSheet(
                    f"color: {v3c('text2', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_rec_styles()


class _QuickSessionCard(NMCard):
    """Sesión rápida: ring + NMPlayButton centrado."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                               V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["sm"])
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._eyebrow = QLabel("SESIÓN RÁPIDA")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        self._eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._eyebrow)

        # Ring grande con icono centrado (simulado con NMModuleRing al 0% + botón)
        center = QWidget()
        center_lay = QVBoxLayout(center)
        center_lay.setContentsMargins(0, V3_SP["sm"], 0, V3_SP["sm"])
        center_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_lay.setSpacing(V3_SP["sm"])
        self._ring = NMModuleRing(size=96, pct=0.0, modo=self._modo)
        center_lay.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignCenter)
        self._play = NMPlayButton(icon_name="play", size="lg",
                                   modo=self._modo)
        center_lay.addWidget(self._play, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(center)

        self._micro = QLabel("5 minutos de focus")
        self._micro.setFont(qfont("size_small"))
        self._micro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._micro)
        lay.addStretch()
        self._apply_qs_styles()

    def _apply_qs_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        self._micro.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._ring._modo = self._modo
        self._ring.update()
        self._apply_qs_styles()


class _AvisosCard(NMCard):
    """Lista próximos 3 avisos: hora (mono) + descripción."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                               V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["sm"])
        self._eyebrow = QLabel("PRÓXIMOS AVISOS")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)
        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(V3_SP["xs"] + 2)
        lay.addLayout(self._items_layout)
        lay.addStretch()
        self.set_avisos(_load_upcoming_avisos())
        self._apply_av_styles()

    def set_avisos(self, items: list[tuple[str, str]]):
        # Clear
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            w = child.widget()
            if w:
                w.deleteLater()
        if not items:
            empty = QLabel("Sin avisos próximos.")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            self._items_layout.addWidget(empty)
            return
        for hora, desc in items[:3]:
            row = QHBoxLayout()
            row.setSpacing(V3_SP["sm"])
            time_lbl = QLabel(hora)
            try:
                from shared.theme_qt import qfont_mono
                time_lbl.setFont(qfont_mono(10, bold=False))
            except Exception:
                time_lbl.setFont(qfont("size_small"))
            time_lbl.setStyleSheet(
                f"color: {v3c('teal', self._modo).name()}; "
                f"background: transparent;")
            time_lbl.setFixedWidth(54)
            row.addWidget(time_lbl)
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(qfont("size_small"))
            desc_lbl.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; "
                f"background: transparent;")
            desc_lbl.setWordWrap(True)
            row.addWidget(desc_lbl, stretch=1)
            wrap = QWidget()
            wrap.setLayout(row)
            self._items_layout.addWidget(wrap)

    def _apply_av_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_av_styles()
        self.set_avisos(_load_upcoming_avisos())


class _FooterQuoteCard(NMCard):
    """Cita motivacional + CTA gradient (NMButton)."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=True)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["lg"])
        lay.setSpacing(V3_SP["lg"])
        col = QVBoxLayout()
        col.setSpacing(4)
        self._eyebrow = QLabel("PARA HOY")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._eyebrow)
        self._quote = QLabel(_daily_quote())
        self._quote.setFont(qfont("size_h3",
                                   weight=TYPOGRAPHY["weight_semibold"]))
        self._quote.setWordWrap(True)
        col.addWidget(self._quote)
        lay.addLayout(col, stretch=1)
        self._cta = NMButton("Comenzar el día", variant="gradient",
                              size="md", modo=self._modo, width=160)
        lay.addWidget(self._cta, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._apply_fq_styles()

    def _apply_fq_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        self._quote.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_fq_styles()


# ── HomeView ─────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    """Vista Home v3 — hero, wave chart, KPIs, módulos grid, bottom 3-col, footer."""

    def __init__(self, modo: str = "dark_hybrid",
                 on_module_open=None, get_status_fn=None,
                 username: str = "", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._open_cb = on_module_open or (lambda mid: None)
        self._get_status = get_status_fn or (lambda mid: "")
        self._username = username
        self._cards: dict[str, ModuleCard] = {}
        self._grid_cols = 0
        self._session = SessionColor.instance()
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    # ── setup ─────────────────────────────────────────────────────────────────

    def _setup(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(self._scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._scroll.setWidget(container)

        body = QVBoxLayout(container)
        body.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                 V3_SP["xl"], V3_SP["xl"])
        body.setSpacing(V3_SP["lg"])

        # 1. Welcome bar (no header — global NMHeader handles greeting + toggle)
        self._welcome_bar = NMWelcomeBar(self._modo)
        body.addWidget(self._welcome_bar)

        # 2. Hero
        self._hero = _HeroCard(self._modo)
        body.addWidget(self._hero)

        # 3. Wave chart card
        wave_card = NMCard(modo=self._modo, clickable=False, glow=False)
        wlay = QVBoxLayout(wave_card)
        wlay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                 V3_SP["lg"], V3_SP["lg"])
        wlay.setSpacing(V3_SP["sm"])
        self._wave_title = QLabel("EVOLUCIÓN 7 DÍAS")
        self._wave_title.setFont(qfont("size_caption_xs",
                                        weight=TYPOGRAPHY["weight_semibold"]))
        wlay.addWidget(self._wave_title)
        self._wave = NMWaveChart(modo=self._modo)
        wlay.addWidget(self._wave)
        body.addWidget(wave_card)
        self._wave_card = wave_card

        # 4. KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(V3_SP["md"])
        self._kpi_sessions = _KpiCard(
            "timer", "Sesiones de hoy", "0", pct=0.0, modo=self._modo)
        self._kpi_breath = _KpiCard(
            "lungs", "Minutos de respiración", "0", pct=0.0, modo=self._modo)
        self._kpi_activities = _KpiCard(
            "spark", "Actividades completadas", "0", pct=0.0, modo=self._modo)
        for k in (self._kpi_sessions, self._kpi_breath, self._kpi_activities):
            kpi_row.addWidget(k, stretch=1)
        body.addLayout(kpi_row)

        # 5. Modules grid
        modules_title = QLabel("TUS MÓDULOS")
        modules_title.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        modules_title.setContentsMargins(V3_SP["xs"], V3_SP["sm"],
                                          V3_SP["xs"], 0)
        body.addWidget(modules_title)
        self._modules_title = modules_title

        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setVerticalSpacing(V3_SP["md"])
        self._grid.setHorizontalSpacing(V3_SP["md"])
        body.addLayout(self._grid)

        for idx, cfg in enumerate(MODULES_CONFIG):
            card = ModuleCard(cfg, idx, self._modo,
                              on_click=self._open_cb,
                              get_status_fn=self._get_status)
            self._cards[cfg["id"]] = card
        self._sync_availability()
        self._rebuild_grid()

        # 6. Bottom 3-col
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(V3_SP["md"])
        self._rec_card = _RecommendationsCard(self._modo)
        self._quick_card = _QuickSessionCard(self._modo)
        self._avisos_card = _AvisosCard(self._modo)
        for c in (self._rec_card, self._quick_card, self._avisos_card):
            bottom_row.addWidget(c, stretch=1)
        body.addLayout(bottom_row)

        # 7. Footer quote
        self._footer = _FooterQuoteCard(self._modo)
        body.addWidget(self._footer)

        # Wave + score initial fetch
        self._refresh_data()

        # Stagger anim de las module cards
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 60)

    def _build_header(self) -> QHBoxLayout:
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(V3_SP["md"])

        # Bloque izq: título + subtítulo
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        self._title_lbl = QLabel(self._greeting_text())
        self._title_lbl.setFont(qfont("size_h1",
                                       weight=TYPOGRAPHY["weight_bold"]))
        left_col.addWidget(self._title_lbl)
        self._subtitle_lbl = QLabel(self._subtitle_text())
        self._subtitle_lbl.setFont(qfont("size_small"))
        left_col.addWidget(self._subtitle_lbl)
        top.addLayout(left_col, stretch=1)

        # Bloque der: streak + theme toggle
        right_col = QHBoxLayout()
        right_col.setSpacing(V3_SP["md"])
        right_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._streak_badge = NMStreakBadge(_load_streak(), self._modo)
        right_col.addWidget(self._streak_badge,
                            alignment=Qt.AlignmentFlag.AlignVCenter)
        self._theme_toggle = NMToggle(modo=self._modo)
        self._theme_toggle.setChecked("dark" in self._modo)
        self._theme_toggle.toggled.connect(self._on_theme_toggled)
        toggle_label = QLabel("Modo oscuro")
        toggle_label.setFont(qfont("size_small"))
        right_col.addWidget(toggle_label,
                            alignment=Qt.AlignmentFlag.AlignVCenter)
        self._toggle_label = toggle_label
        right_col.addWidget(self._theme_toggle,
                            alignment=Qt.AlignmentFlag.AlignVCenter)
        top.addLayout(right_col)
        self._apply_header_styles()
        return top

    def _on_theme_toggled(self, checked: bool):
        new_modo = "dark_hybrid" if checked else "light_hybrid"
        ThemeManager.instance().switch_mode(new_modo)

    def _apply_header_styles(self):
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        self._toggle_label.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent;")

    # ── data refresh ──────────────────────────────────────────────────────────

    def _refresh_data(self):
        curr, prev = _load_weekly_mood()
        self._wave.set_data(curr, prev)
        score = _wellness_from_week(curr)
        self._hero.set_score(score)
        # KPIs
        kpis = _load_kpis_today()
        sess = kpis["sesiones"]
        breath = kpis["respiracion_min"]
        acts = kpis["actividades"]
        self._kpi_sessions.set_value(str(sess), min(sess / 5.0, 1.0))
        self._kpi_breath.set_value(f"{breath} min", min(breath / 20.0, 1.0))
        self._kpi_activities.set_value(str(acts), min(acts / 6.0, 1.0))

    # ── grid rebuild ──────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_cols = responsive_columns(self.width())
        if new_cols != self._grid_cols:
            self._grid_cols = new_cols
            self._rebuild_grid()

    def _rebuild_grid(self):
        cols = max(1, self._grid_cols or responsive_columns(self.width()))
        for i in reversed(range(self._grid.count())):
            item = self._grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        n = len(MODULES_CONFIG)
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if not card:
                continue
            row = idx // cols
            col = idx % cols
            # 7° card centrada en última fila si cols=3
            if cols == 3 and idx == n - 1 and n % cols == 1:
                col = 1
            self._grid.addWidget(card, row, col)

    # ── texto del header ──────────────────────────────────────────────────────

    def _greeting_text(self) -> str:
        name = (self._username or "Paciente").strip() or "Paciente"
        return f"¡Hola, {name}!"

    def _subtitle_text(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "Buenos días — empezá el día con calma."
        if hour < 20:
            return "Buenas tardes — un momento para vos."
        return "Buenas noches — cerremos bien el día."

    # ── API pública ───────────────────────────────────────────────────────────

    def refresh_statuses(self):
        self._sync_availability()
        for card in self._cards.values():
            card.refresh()
        self._refresh_data()
        if hasattr(self, "_streak_badge") and self._streak_badge is not None:
            self._streak_badge._days = _load_streak()
            self._streak_badge._apply_theme(self._modo)
        self._avisos_card.set_avisos(_load_upcoming_avisos())

    def set_modo(self, modo: str):
        self._apply_theme(modo)

    # ── permisos ──────────────────────────────────────────────────────────────

    def _disabled_reason(self, module_id: str) -> str:
        return {
            "rutina":      "Tu profesional desactivó la rutina manual.",
            "actividades": "Tu profesional desactivó las actividades manuales.",
            "timer":       "Tu profesional desactivó el temporizador manual.",
            "avisos":      "Tu profesional desactivó los recordatorios manuales.",
        }.get(module_id, "Módulo no disponible.")

    def _sync_availability(self):
        for module_id, card in self._cards.items():
            available = self._is_module_available(module_id)
            card.set_disabled(not available,
                              self._disabled_reason(module_id) if not available else "")

    def _is_module_available(self, module_id: str) -> bool:
        if visual_qa_enabled():
            return True
        permission_keys = {
            "rutina":      "perm_checklist_manual",
            "actividades": "perm_checklist_activacion",
            "timer":       "perm_temporizador_manual",
            "avisos":      "perm_recordatorios_manual",
        }
        key = permission_keys.get(module_id)
        if not key:
            return True
        try:
            from shared.db import leer_config
            return leer_config(key, "1") != "0"
        except Exception:
            return True

    # ── theme switch ──────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_title_lbl") and self._title_lbl is not None:
            self._title_lbl.setText(self._greeting_text())
        if hasattr(self, "_subtitle_lbl") and self._subtitle_lbl is not None:
            self._subtitle_lbl.setText(self._subtitle_text())
        # Theme toggle y streak ahora en NMHeader global — no duplicar
        if hasattr(self, "_streak_badge") and self._streak_badge is not None:
            self._streak_badge._apply_theme(self._modo)
        for card in self._cards.values():
            card._apply_theme(self._modo)
        # Section titles
        for lbl in (self._wave_title, self._modules_title):
            lbl.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
        self.update()

    # ── fondo ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        # Use shell background (gradient + 3 blobs teal/violet/cyan) — consistente
        # con NeuroMoodApp shell. Sin esto, HomeView taparía los blobs del shell
        # padre con un fill opaco.
        from shared.theme_qt import paint_shell_background
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_shell_background(p, QRectF(self.rect()), self._modo)
        # Aura SessionColor sutil encima (50% de opacidad para no competir
        # con los blobs del shell)
        w, h = self.width(), self.height()
        alpha = int(aura_opacity(self._modo) * 255 * 0.4)
        aura_c = self._session.qcolor(self._modo, alpha)
        aura = QRadialGradient(QPointF(w * 0.18, h * 0.50), w * 0.85)
        aura.setColorAt(0.0, aura_c)
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), aura)
        p.end()
