"""
app/home_qt.py — Vista Home v3 (PyQt6)

Grid responsivo de 7 módulos. Sin scroll en ventana maximizada.
API pública: HomeView(modo, on_module_open, get_status_fn, username, parent)
             .set_modo(modo) / .refresh_statuses() / .resizeEvent()
"""

import logging
import os
import sys

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    QAbstractAnimation, QPoint, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QGraphicsOpacityEffect,
)

try:
    from shared.theme_qt import (
        C, colors, norm_modo, qfont,
        interpolate_color, gradient_colors,
        ThemeAwareWidgetMixin, SessionColor, aura_opacity,
        v3c, V3_SP, V3_RD,
    )
    from shared.theme import TYPOGRAPHY
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
    from shared.theme import TYPOGRAPHY
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

        self.setMinimumHeight(120)
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
                                  V3_SP["lg"], V3_SP["lg"])
        layout.setSpacing(V3_SP["sm"])

        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._icon = NMIcon(self._config["icon_v3"], size=48,
                            color=self._accent, modo=self._modo)
        top.addWidget(self._icon)
        top.addStretch()
        self._chip = QLabel(self._config.get("chip", ""))
        self._chip.setFont(qfont("size_caption_xs",
                                  weight=TYPOGRAPHY["weight_semibold"]))
        self._chip.setContentsMargins(8, 2, 8, 2)
        top.addWidget(self._chip)
        layout.addLayout(top)

        self._title_lbl = QLabel(self._config["title"])
        self._title_lbl.setFont(qfont("size_h3",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        layout.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(self._config["desc"])
        self._desc_lbl.setFont(qfont("size_caption"))
        self._desc_lbl.setWordWrap(True)
        layout.addWidget(self._desc_lbl)

        layout.addStretch()

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
            f"color: {chip_fg}; background: {chip_bg}; border-radius: 8px;")

    # ── status badge ──────────────────────────────────────────────────────────

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
    """Vista Home v3 — grid de 7 módulos, sin scroll."""

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

        body = QVBoxLayout(self)
        body.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["xl"])
        body.setSpacing(V3_SP["md"])

        self._modules_title = QLabel("TUS MÓDULOS")
        self._modules_title.setFont(
            qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._modules_title.setContentsMargins(V3_SP["xs"], 0, V3_SP["xs"], 0)
        body.addWidget(self._modules_title)

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

        body.addLayout(self._grid, stretch=1)

        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 60)

    # ── grid responsive ───────────────────────────────────────────────────────

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
        num_rows = (n + cols - 1) // cols
        for r in range(num_rows):
            self._grid.setRowStretch(r, 1)
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if not card:
                continue
            row = idx // cols
            col = idx % cols
            # Séptima card centrada en columna 1 si cols=3 y es la única de su fila
            if cols == 3 and idx == n - 1 and n % cols == 1:
                col = 1
            self._grid.addWidget(card, row, col)

    # ── API pública ───────────────────────────────────────────────────────────

    def refresh_statuses(self):
        self._sync_availability()
        for card in self._cards.values():
            card.refresh()

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

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for card in self._cards.values():
            card._apply_theme(self._modo)
        self._modules_title.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
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
