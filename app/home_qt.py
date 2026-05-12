"""
app/home_qt.py — Vista Home con grid de 7 ModuleCard (PyQt6)

Características:
  - Stagger de entrada: fade-in + slide desde abajo con delay de 60ms por card
  - Mini-ring de progreso (32px) en cada card
  - Status badge pill con color semántico
  - 7ma card centrada en fila 3 (no span completo)
  - Barra de color izquierda con gradiente teal→violet por índice
"""

import os
import sys

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    QAbstractAnimation, QPoint,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath,
)
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QFrame, QGraphicsOpacityEffect,
)

try:
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        linear_gradient, get_gradient,
        RADIUS_CARD, PAD_CARD, GAP_CARDS,
    )
    from shared.components_qt import ThemeManager
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        linear_gradient, get_gradient,
        RADIUS_CARD, PAD_CARD, GAP_CARDS,
    )
    from shared.components_qt import ThemeManager

# ── Configuración de módulos ──────────────────────────────────────────────────

MODULES_CONFIG = [
    {"id": "animo",       "icon": "🎭", "title": "Ánimo",
     "desc": "Registrá tu estado emocional · 1 min"},
    {"id": "respiracion", "icon": "🌬️", "title": "Respirar",
     "desc": "Respiración guiada 4-7-8 · 3/5/10 min"},
    {"id": "registro",    "icon": "📝", "title": "Registro TCC",
     "desc": "Pensamientos automáticos · 4 pasos"},
    {"id": "rutina",      "icon": "✅", "title": "Rutina",
     "desc": "Tareas del día · Mañana/Tarde/Noche"},
    {"id": "actividades", "icon": "⚡", "title": "Actividades",
     "desc": "Sugerencias según tu ánimo actual"},
    {"id": "timer",       "icon": "⏱️", "title": "Timer",
     "desc": "Temporizador de actividades"},
    {"id": "avisos",      "icon": "🔔", "title": "Avisos",
     "desc": "Recordatorios · funcionan en background"},
]


def _dot_color(idx: int, modo: str) -> str:
    """Color del gradiente teal→violet según posición del módulo."""
    grad = get_gradient(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[1], t)


# ── Mini-ring de progreso ─────────────────────────────────────────────────────

class _MiniRing(QWidget):
    """Arco de 32×32px que muestra progreso 0.0–1.0."""

    def __init__(self, parent=None, color: str = "#00d4c8"):
        super().__init__(parent)
        self._progress = 0.0
        self._color = color
        self.setFixedSize(32, 32)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

    def set_progress(self, v: float):
        self._progress = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, event):
        if self._progress <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = 12
        cx, cy = 16, 16
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        pen_track = QPen(QColor(80, 80, 80, 80), 3, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.drawEllipse(rect)
        pen_fill = QPen(QColor(self._color), 3, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap)
        p.setPen(pen_fill)
        p.drawArc(rect, 90 * 16, int(-self._progress * 360 * 16))
        p.end()


# ── Card del módulo ───────────────────────────────────────────────────────────

class ModuleCard(QWidget):
    """
    Card con barra izquierda de color gradiente, mini-ring, badge de status,
    animación de entrada stagger (fade + slide Y).
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

        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(0.0)
        self.setGraphicsEffect(self._eff)

        self._build_ui()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _build_ui(self):
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(4)

        # Fila top: icono + badge
        top = QHBoxLayout()
        top.setSpacing(6)
        icon_lbl = QLabel(self._config["icon"])
        icon_lbl.setFont(qfont("size_emoji_sm"))
        icon_lbl.setStyleSheet("background: transparent; color: white;")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(icon_lbl)
        top.addStretch()
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption"))
        self._badge.setStyleSheet("background: transparent;")
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(self._badge)
        layout.addLayout(top)

        # Título
        title = QLabel(self._config["title"])
        title.setFont(qfont("size_h3", bold=True))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(title)
        self._title_lbl = title

        # Descripción
        desc = QLabel(self._config["desc"])
        desc.setFont(qfont("size_caption"))
        desc.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        desc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(desc)
        self._desc_lbl = desc

        # Mini-ring (absoluto)
        self._ring = _MiniRing(self, self._accent)
        self._ring.move(self.width() - 40, 8)

        self._refresh_status()

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        c = colors(self._modo)
        if status:
            color = "#10b981"
            if "activo" in status:
                color = C("accent", self._modo)
            self._badge.setText(status)
            self._badge.setStyleSheet(
                f"color: {color}; background: transparent;"
                f"font-size: 9pt; font-weight: bold;"
            )
        else:
            self._badge.setText("")
        self._update_ring(status)

    def _update_ring(self, status: str = None):
        if status is None:
            status = self._get_status(self._config["id"])
        if not status:
            self._ring.set_progress(0)
            return
        if "/" in status and "✔" in status:
            try:
                parts = status.split("/")
                done = int(parts[0].strip())
                total = int(parts[1].replace("✔", "").strip())
                self._ring.set_progress(done / total if total > 0 else 0)
            except Exception:
                self._ring.set_progress(1.0 if "✔" in status else 0)
        elif "✔" in status:
            self._ring.set_progress(1.0)
        else:
            self._ring.set_progress(0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = RADIUS_CARD
        w, h = self.width(), self.height()

        # Fondo
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, QBrush(QColor(c["bg_surface"])))

        # Borde
        p.setPen(QPen(QColor(c.get("border_card", c["border"])), 1))
        p.drawPath(path)

        # Barra izquierda
        bar = QPainterPath()
        bar.addRoundedRect(QRectF(0, r, 4, h - 2 * r), 0, 0)
        bar.addRoundedRect(QRectF(0, 0, 4, r), r, r)
        bar.addRoundedRect(QRectF(0, h - r, 4, r), r, r)
        p.fillPath(bar, QBrush(QColor(self._accent)))
        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ring.move(self.width() - 38, 8)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_click(self._config["id"])

    def animate_enter(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
        anim_fade = QPropertyAnimation(self._eff, b"opacity", self)
        anim_fade.setDuration(320)
        anim_fade.setStartValue(0.0)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        orig_y = self.y()
        self.move(self.x(), orig_y + 20)
        anim_move = QPropertyAnimation(self, b"pos", self)
        anim_move.setDuration(320)
        anim_move.setStartValue(QPoint(self.x(), self.y()))
        anim_move.setEndValue(QPoint(self.x(), orig_y))
        anim_move.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_move.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _dot_color(self._idx, self._modo)
        c = colors(self._modo)
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._desc_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        self._ring._color = self._accent
        self._ring.update()
        self._refresh_status()
        self.update()

    def refresh(self):
        self._refresh_status()
        self.update()


# ── HomeView ──────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    """Grid de 7 ModuleCard con animación de entrada escalonada (stagger 60ms)."""

    def __init__(self, modo: str = "dark_hybrid",
                 on_module_open=None, get_status_fn=None,
                 parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._open_cb = on_module_open or (lambda mid: None)
        self._get_status = get_status_fn or (lambda mid: "")
        self._cards: dict[str, ModuleCard] = {}
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _setup(self):
        c = colors(self._modo)
        self.setStyleSheet(f"HomeView {{ background: {c['bg_primary']}; }}")

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        grid = QGridLayout(container)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setSpacing(GAP_CARDS)
        for col in range(3):
            grid.setColumnStretch(col, 1)

        # Cards 0–5 en grid 3 columnas
        for idx in range(6):
            cfg = MODULES_CONFIG[idx]
            row, col = idx // 3, idx % 3
            card = ModuleCard(
                cfg, idx, self._modo,
                on_click=self._open_cb,
                get_status_fn=self._get_status,
            )
            grid.addWidget(card, row, col)
            self._cards[cfg["id"]] = card

        # Card 7 centrada sola en fila 2
        cfg7 = MODULES_CONFIG[6]
        card7 = ModuleCard(
            cfg7, 6, self._modo,
            on_click=self._open_cb,
            get_status_fn=self._get_status,
        )
        card7.setMaximumWidth(380)
        grid.addWidget(card7, 2, 1, Qt.AlignmentFlag.AlignHCenter)
        self._cards[cfg7["id"]] = card7

        grid.setRowStretch(3, 1)

        # Animar entrada con stagger
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 60)

    def refresh_statuses(self):
        for card in self._cards.values():
            card.refresh()

    def set_modo(self, modo: str):
        self._apply_theme(modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(f"HomeView {{ background: {c['bg_primary']}; }}")
