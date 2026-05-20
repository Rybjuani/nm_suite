"""
app/home_qt.py — Vista Home v3 Premium (PyQt6)

Layout a 1440x900:
  QHBoxLayout
  ├── _SidePanel (220px fijo) — saludo grande, estado emocional, próxima sesión
  └── _ContentArea (stretch)
      ├── Eyebrow "TUS MÓDULOS"
      └── QGridLayout de ModuleCards (3 cols)

API pública: HomeView(modo, on_module_open, get_status_fn, username, parent)
             .set_modo(modo) / .refresh_statuses() / .resizeEvent()
"""

import logging
import os
import sys
from datetime import datetime

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    QAbstractAnimation, QPoint, pyqtSignal, QSize,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QRadialGradient, QLinearGradient,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QSizePolicy, QGraphicsOpacityEffect, QSpacerItem,
)

try:
    from shared.theme_qt import (
        C, colors, norm_modo, qfont,
        interpolate_color, gradient_colors,
        ThemeAwareWidgetMixin, SessionColor, aura_opacity,
        v3c, V3_SP, V3_RD,
    )
    from shared.theme import TYPOGRAPHY, V3_RADIUS, V3_SHADOWS
    from shared.components_qt import (
        ThemeManager, responsive_columns,
        NMIcon, NMModuleRing,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C, colors, norm_modo, qfont,
        interpolate_color, gradient_colors,
        ThemeAwareWidgetMixin, SessionColor, aura_opacity,
        v3c, V3_SP, V3_RD,
    )
    from shared.theme import TYPOGRAPHY, V3_RADIUS, V3_SHADOWS
    from shared.components_qt import (
        ThemeManager, responsive_columns,
        NMIcon, NMModuleRing,
    )

from shared.visual_qa import visual_qa_enabled


# ── Módulos ───────────────────────────────────────────────────────────────────

MODULES_CONFIG = [
    {"id": "animo",       "icon_v3": "mood",    "title": "Ánimo",
     "desc": "Registro emocional diario",     "chip": "Bienestar"},
    {"id": "respiracion", "icon_v3": "breath",  "title": "Respiración",
     "desc": "Técnicas de calma 4-7-8",        "chip": "Calma"},
    {"id": "registro",    "icon_v3": "brain",   "title": "TCC",
     "desc": "Pensamientos automáticos",        "chip": "Cognitivo"},
    {"id": "rutina",      "icon_v3": "routine", "title": "Rutina",
     "desc": "Checklist del día",               "chip": "Hábitos"},
    {"id": "actividades", "icon_v3": "run",     "title": "Actividades",
     "desc": "Activación conductual",           "chip": "Acción"},
    {"id": "timer",       "icon_v3": "timer",   "title": "Timer",
     "desc": "Sesiones de enfoque",             "chip": "Focus"},
    {"id": "avisos",      "icon_v3": "bell",    "title": "Avisos",
     "desc": "Recordatorios del día",           "chip": "Diario"},
]


def _dot_color(idx: int, modo: str) -> str:
    """Color degradado teal→violet según posición del módulo."""
    grad = gradient_colors(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[-1], t)


# ── _SidePanel ────────────────────────────────────────────────────────────────

class _SidePanel(QWidget):
    """Panel lateral izquierdo: saludo grande + estado emocional + next session."""

    _WIDTH = 240

    def __init__(self, username: str, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._username = username
        self.setFixedWidth(self._WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._build_ui()

    # ── build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["xl"], V3_SP["xxl"],
                                  V3_SP["md"], V3_SP["xl"])
        layout.setSpacing(0)

        # ── Greeting block ────────────────────────────────────────────────────
        greet_block = QWidget()
        greet_block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        gb_lay = QVBoxLayout(greet_block)
        gb_lay.setContentsMargins(0, 0, 0, 0)
        gb_lay.setSpacing(V3_SP["xs"])

        self._time_lbl = QLabel(self._time_of_day())
        self._time_lbl.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))

        self._name_lbl = QLabel(self._first_name())
        self._name_lbl.setFont(qfont("size_h1", weight=TYPOGRAPHY["weight_bold"]))
        self._name_lbl.setWordWrap(True)

        self._sub_lbl = QLabel("¿Cómo te encontrás\nhoy?")
        self._sub_lbl.setFont(qfont("size_small"))
        self._sub_lbl.setWordWrap(True)

        gb_lay.addWidget(self._time_lbl)
        gb_lay.addSpacing(V3_SP["xs"])
        gb_lay.addWidget(self._name_lbl)
        gb_lay.addSpacing(2)
        gb_lay.addWidget(self._sub_lbl)
        layout.addWidget(greet_block)

        layout.addSpacing(V3_SP["xl"])

        # ── Divider ───────────────────────────────────────────────────────────
        self._div1 = QFrame()
        self._div1.setFixedHeight(1)
        layout.addWidget(self._div1)

        layout.addSpacing(V3_SP["lg"])

        # ── Wellbeing mini-card ───────────────────────────────────────────────
        well_block = QWidget()
        well_block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        wb_lay = QVBoxLayout(well_block)
        wb_lay.setContentsMargins(0, 0, 0, 0)
        wb_lay.setSpacing(V3_SP["xs"])

        self._well_eyebrow = QLabel("BIENESTAR HOY")
        self._well_eyebrow.setFont(qfont("size_caption_xs",
                                         weight=TYPOGRAPHY["weight_semibold"]))

        self._well_status = QLabel("Registrá tu ánimo\npara comenzar")
        self._well_status.setFont(qfont("size_small"))
        self._well_status.setWordWrap(True)

        wb_lay.addWidget(self._well_eyebrow)
        wb_lay.addSpacing(V3_SP["xs"])
        wb_lay.addWidget(self._well_status)
        layout.addWidget(well_block)

        layout.addSpacing(V3_SP["lg"])

        # ── Divider ───────────────────────────────────────────────────────────
        self._div2 = QFrame()
        self._div2.setFixedHeight(1)
        layout.addWidget(self._div2)

        layout.addSpacing(V3_SP["lg"])

        # ── Next session block ────────────────────────────────────────────────
        sess_block = QWidget()
        sess_block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        sb_lay = QVBoxLayout(sess_block)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(V3_SP["xs"])

        self._sess_eyebrow = QLabel("PRÓXIMA SESIÓN")
        self._sess_eyebrow.setFont(qfont("size_caption_xs",
                                         weight=TYPOGRAPHY["weight_semibold"]))

        self._sess_lbl = QLabel("Sin sesión\nprogramada")
        self._sess_lbl.setFont(qfont("size_small"))
        self._sess_lbl.setWordWrap(True)

        sb_lay.addWidget(self._sess_eyebrow)
        sb_lay.addSpacing(V3_SP["xs"])
        sb_lay.addWidget(self._sess_lbl)
        layout.addWidget(sess_block)

        layout.addStretch()

        # ── App brand mark at bottom ──────────────────────────────────────────
        self._brand_lbl = QLabel("NeuroMood Suite")
        self._brand_lbl.setFont(qfont("size_caption_xs"))
        layout.addWidget(self._brand_lbl)

        self._apply_styles()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _first_name(self) -> str:
        name = (self._username or "Paciente").strip() or "Paciente"
        return name.split()[0].capitalize()

    def _time_of_day(self) -> str:
        h = datetime.now().hour
        if 5 <= h < 12:
            return "Buenos días,"
        if 12 <= h < 20:
            return "Buenas tardes,"
        return "Buenas noches,"

    # ── styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        is_dark = "dark" in self._modo
        accent  = v3c("accent", self._modo)
        text    = v3c("text", self._modo)
        muted   = v3c("textMuted", self._modo)
        # Eyebrow labels: use text2 so they're legible at 10pt in both modes
        eyebrow = v3c("text2", self._modo)
        text3   = v3c("text3", self._modo)
        # Divider: use border token at reduced alpha
        div_c   = v3c("border", self._modo)
        div_alpha = 50 if is_dark else 90

        self._time_lbl.setStyleSheet(
            f"color: {accent.name()}; background: transparent; "
            f"letter-spacing: 0.3px;")
        self._name_lbl.setStyleSheet(
            f"color: {text.name()}; background: transparent;")
        self._sub_lbl.setStyleSheet(
            f"color: {muted.name()}; background: transparent;")

        div_css = (f"background-color: rgba({div_c.red()},{div_c.green()},"
                   f"{div_c.blue()},{div_alpha});")
        self._div1.setStyleSheet(div_css)
        self._div2.setStyleSheet(div_css)

        self._well_eyebrow.setStyleSheet(
            f"color: {eyebrow.name()}; background: transparent; "
            f"letter-spacing: 1px;")
        self._well_status.setStyleSheet(
            f"color: {muted.name()}; background: transparent;")

        self._sess_eyebrow.setStyleSheet(
            f"color: {eyebrow.name()}; background: transparent; "
            f"letter-spacing: 1px;")
        self._sess_lbl.setStyleSheet(
            f"color: {muted.name()}; background: transparent;")

        self._brand_lbl.setStyleSheet(
            f"color: {text3.name()}; background: transparent;")

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._time_lbl.setText(self._time_of_day())
        self._apply_styles()

    def update_wellbeing(self, status_text: str):
        """Update the wellbeing status from today's mood record."""
        if status_text:
            self._well_status.setText(status_text)
        else:
            self._well_status.setText("Registrá tu ánimo\npara comenzar")

    # ── paint — glass panel with full-height separator ───────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = "dark" in self._modo
        w, h = float(self.width()), float(self.height())

        # Solid fill using token values (no translucency issues in Qt rasterizer)
        if is_dark:
            # Deep navy: bgAlt token = #121b2d, slightly more opaque for sidebar
            fill = QColor(14, 22, 38, 230)
        else:
            # Warm cream: slightly darker than bg to distinguish from content
            fill = QColor(245, 241, 232, 245)  # #f5f1e8-ish, fully opaque
        p.fillRect(QRectF(0, 0, w, h), QBrush(fill))

        # Full-height right-edge separator — accent-tinted in dark, stone in light
        sep_c = v3c("border", self._modo)
        if is_dark:
            sep_c.setAlpha(70)
        else:
            sep_c.setAlpha(120)
        p.setPen(QPen(sep_c, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(int(w) - 1, 0, int(w) - 1, int(h))

        p.end()


# ── ModuleCard ────────────────────────────────────────────────────────────────

class ModuleCard(ThemeAwareWidgetMixin, QWidget):
    """Card de módulo v3 con NMIcon SVG y NMModuleRing."""

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

        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(0.0)
        self.setGraphicsEffect(self._eff)

        self._build_ui()
        self._connect_theme()

    # ── build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                  V3_SP["lg"], V3_SP["md"])
        layout.setSpacing(V3_SP["xs"])

        # Top row: icon + chip
        top = QHBoxLayout()
        top.setSpacing(V3_SP["xs"])
        self._icon = NMIcon(self._config["icon_v3"], size=40,
                            color=self._accent, modo=self._modo)
        top.addWidget(self._icon)
        top.addStretch()
        self._chip = QLabel(self._config.get("chip", ""))
        self._chip.setFont(qfont("size_caption_xs",
                                  weight=TYPOGRAPHY["weight_semibold"]))
        self._chip.setContentsMargins(6, 2, 6, 2)
        top.addWidget(self._chip)
        layout.addLayout(top)

        layout.addSpacing(V3_SP["xs"])

        # Title
        self._title_lbl = QLabel(self._config["title"])
        self._title_lbl.setFont(qfont("size_h3",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        layout.addWidget(self._title_lbl)

        # Description
        self._desc_lbl = QLabel(self._config["desc"])
        self._desc_lbl.setFont(qfont("size_caption"))
        self._desc_lbl.setWordWrap(True)
        layout.addWidget(self._desc_lbl)

        layout.addStretch()

        # Bottom row: badge + ring
        bottom = QHBoxLayout()
        bottom.setSpacing(V3_SP["xs"])
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption",
                                   weight=TYPOGRAPHY["weight_semibold"]))
        self._badge.setContentsMargins(6, 2, 6, 2)
        bottom.addWidget(self._badge)
        bottom.addStretch()
        self._ring = NMModuleRing(size=28, pct=0.0, modo=self._modo)
        bottom.addWidget(self._ring)
        layout.addLayout(bottom)

        self._apply_styles()
        self._refresh_status()

    def _apply_styles(self):
        is_dark = "dark" in self._modo
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;")
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;")
        # Chip bg: warm tint in light (#f0e8d4 ≈ sand-teal), purple tint in dark
        accent = v3c("accent", self._modo)
        if is_dark:
            chip_bg = v3c("accentSoft", self._modo)
        else:
            # Warm sand tint instead of cold mint — more coherent with ivory palette
            chip_bg = QColor(0xec, 0xe8, 0xd8, 200)  # warm sand at 78% opacity
        self._chip.setStyleSheet(
            f"color: {accent.name()}; "
            f"background-color: rgba({chip_bg.red()},{chip_bg.green()},{chip_bg.blue()},{chip_bg.alpha()}); "
            f"border-radius: 6px;")

    # ── status badge ──────────────────────────────────────────────────────────

    def _pill_style(self, color_hex: str, alpha_bg: float = 0.14) -> str:
        c = QColor(color_hex)
        a = int(alpha_bg * 255)
        return (
            f"color: {color_hex}; "
            f"background-color: rgba({c.red()},{c.green()},{c.blue()},{a}); "
            f"border-radius: 8px; padding: 2px 6px;")

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        if self._disabled:
            self._badge.setText("No disponible")
            self._badge.setStyleSheet(self._pill_style(C("warning", self._modo)))
            self._ring.set_pct(0.0)
            return
        if status:
            mid = self._config["id"]
            low = status.lower()
            if "completo" in low:
                color = C("success", self._modo)
            elif "progreso" in low or "listos" in low or "/" in status:
                color = C("warning", self._modo)
            elif mid == "avisos":
                color = C("warning", self._modo)
            elif mid == "timer":
                color = C("accent", self._modo)
            elif mid == "rutina":
                color = (C("success", self._modo) if status.startswith("✓")
                         else C("warning", self._modo) if "/" in status
                         else C("teal", self._modo))
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
        r = float(V3_RD["lg"])
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        # Surface fill
        # Light: warm white (#fcfaf6) — slightly warm, distinct from ivory bg
        # Dark: solid dark navy with alpha
        if is_dark:
            surf = v3c("surfaceSolid", self._modo)  # #121c2d
            surf.setAlpha(220)
        else:
            surf = QColor(0xfc, 0xfa, 0xf6, 255)  # warm white — #fcfaf6
        p.setBrush(QBrush(surf))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Hover: full-width accent top bar (4px, solid alpha)
        is_active = self._hover and self.isEnabled() and not self._disabled
        if is_active:
            accent_c = QColor(self._accent)
            accent_c.setAlpha(90 if is_dark else 110)
            p.fillRect(QRectF(0, 0, w, 4.0), QBrush(accent_c))
            # Clip corners on top bar
            # (acceptable approximation — no extra path needed at 4px height)

        # Border — accent-tinted on hover for both modes
        if is_active:
            border_c = QColor(self._accent)
            border_c.setAlpha(160 if is_dark else 140)
        else:
            border_c = v3c("border", self._modo)
            if not is_dark:
                # Light mode border: use borderStrong for more visible card edges
                border_c = v3c("borderStrong", self._modo)
        p.setPen(QPen(border_c, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        # Disabled overlay
        if self._disabled:
            p.fillRect(rect, QColor(255, 255, 255, 15 if is_dark else 60))
        p.end()

    # ── eventos ───────────────────────────────────────────────────────────────

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

    # ── animación de entrada ──────────────────────────────────────────────────

    def animate_enter(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
        if self._eff is None:
            return
        anim_fade = QPropertyAnimation(self._eff, b"opacity", self)
        anim_fade.setDuration(300)
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
        self.move(self.x(), orig_y + 16)
        anim_move = QPropertyAnimation(self, b"pos", self)
        anim_move.setDuration(300)
        anim_move.setStartValue(QPoint(self.x(), self.y()))
        anim_move.setEndValue(QPoint(self.x(), orig_y))
        anim_move.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_move.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _dot_color(self._idx, self._modo)
        self._icon._color = self._accent
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


# ── HomeView ──────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    """Vista Home v3 Premium — sidebar + grid de 7 módulos, sin scroll."""

    _theme_switch_requested = pyqtSignal(bool)

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

        # Root horizontal: sidebar | content
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._side = _SidePanel(self._username, self._modo, self)
        root.addWidget(self._side)

        # ── Content area ──────────────────────────────────────────────────────
        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(V3_SP["xxl"], V3_SP["xl"],
                                       V3_SP["xl"], V3_SP["lg"])
        content_lay.setSpacing(V3_SP["xs"])

        # Section eyebrow
        eyebrow_row = QHBoxLayout()
        eyebrow_row.setSpacing(0)
        self._modules_title = QLabel("TUS MÓDULOS")
        self._modules_title.setFont(
            qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        eyebrow_row.addWidget(self._modules_title)
        eyebrow_row.addStretch()
        content_lay.addLayout(eyebrow_row)

        content_lay.addSpacing(V3_SP["xs"])

        # Grid of module cards
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setVerticalSpacing(V3_SP["md"])
        self._grid.setHorizontalSpacing(V3_SP["md"])

        for idx, cfg in enumerate(MODULES_CONFIG):
            card = ModuleCard(cfg, idx, self._modo,
                              on_click=self._open_cb,
                              get_status_fn=self._get_status)
            self._cards[cfg["id"]] = card

        self._sync_availability()
        self._rebuild_grid()

        content_lay.addLayout(self._grid, stretch=1)
        root.addWidget(content, stretch=1)

        # Staggered entrance
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 55)

        # Apply initial token styles
        self._apply_theme(self._modo)

    # ── grid responsive ───────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Content area width = total - sidebar width
        content_w = max(1, self.width() - _SidePanel._WIDTH)
        new_cols = responsive_columns(content_w, min_card_width=240, max_columns=4)
        if new_cols != self._grid_cols:
            self._grid_cols = new_cols
            self._rebuild_grid()

    def _rebuild_grid(self):
        content_w = max(1, self.width() - _SidePanel._WIDTH)
        cols = max(1, self._grid_cols or responsive_columns(
            content_w, min_card_width=240, max_columns=4))
        for i in reversed(range(self._grid.count())):
            item = self._grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        n = len(MODULES_CONFIG)
        num_rows = (n + cols - 1) // cols
        for r in range(num_rows):
            self._grid.setRowStretch(r, 1)
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if not card:
                continue
            row = idx // cols
            col = idx % cols
            # Last card centered when it's alone in its row
            if idx == n - 1 and (n % cols) == 1:
                col = (cols - 1) // 2
            self._grid.addWidget(card, row, col)

    # ── API pública ───────────────────────────────────────────────────────────

    def refresh_statuses(self):
        self._sync_availability()
        for card in self._cards.values():
            card.refresh()
        # Update wellbeing status in sidebar from mood module
        animo_status = self._get_status("animo")
        self._side.update_wellbeing(animo_status)

    def set_modo(self, modo: str):
        self._apply_theme(modo)

    def _greeting_text(self) -> str:
        name = (self._username or "Paciente").strip() or "Paciente"
        hour = datetime.now().hour
        if 5 <= hour < 12:
            prefix = "Buen dia"
        elif 12 <= hour < 20:
            prefix = "Buenas tardes"
        else:
            prefix = "Buenas noches"
        return f"{prefix}, {name}"

    def _subtitle_text(self) -> str:
        return "Elegí un módulo para registrar cómo venís y sostener tu rutina."

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

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for card in self._cards.values():
            card._apply_theme(self._modo)
        self._side.apply_theme(self._modo)
        # Section eyebrow
        # Eyebrow: use text2 so it's legible at small size in both modes
        self._modules_title.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"letter-spacing: 1px; background: transparent;")
        self.update()

    # ── fondo ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        from shared.theme_qt import paint_shell_background
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_shell_background(p, QRectF(self.rect()), self._modo)
        w, h = self.width(), self.height()
        alpha = int(aura_opacity(self._modo) * 255 * 0.4)
        aura_c = self._session.qcolor(self._modo, alpha)
        aura = QRadialGradient(QPointF(w * 0.18, h * 0.50), w * 0.85)
        aura.setColorAt(0.0, aura_c)
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), aura)
        p.end()
