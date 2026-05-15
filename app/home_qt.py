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
        linear_gradient, linear_gradient_vertical, get_gradient, gradient_colors,
        noise_overlay, fx,
        RADIUS_CARD, PAD_CARD, PAD_CONTAINER, GAP_CARDS,
        stylesheet_scrollarea, SessionColor, ThemeAwareWidgetMixin,
        MODULE_ICONS, nm_icon,
    )
    from shared.components_qt import ThemeManager, responsive_columns
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        linear_gradient, linear_gradient_vertical, get_gradient, gradient_colors,
        noise_overlay, fx,
        RADIUS_CARD, PAD_CARD, PAD_CONTAINER, GAP_CARDS,
        stylesheet_scrollarea, SessionColor, ThemeAwareWidgetMixin,
        MODULE_ICONS, nm_icon,
    )
    from shared.components_qt import ThemeManager, responsive_columns

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
    grad = gradient_colors(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[-1], t)


# ── Mini-ring de progreso ─────────────────────────────────────────────────────

class _MiniRing(QWidget):
    """Arco de 32×32px que muestra progreso 0.0–1.0."""

    def __init__(self, parent=None, color: str = "#6366f1"):
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

class ModuleCard(ThemeAwareWidgetMixin, QWidget):
    """
    Card con barra izquierda de color gradiente, mini-ring, badge de status,
    sombra real, hover lift, animación de entrada stagger (fade + slide Y).
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
        self._session = SessionColor.instance()
        self._hover = False
        self._disabled = False
        self._disabled_reason = ""

        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(0.0)
        self.setGraphicsEffect(self._eff)

        self._build_ui()
        self._connect_theme()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def _build_ui(self):
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CARD, 14, PAD_CARD, 14)
        layout.setSpacing(8)

        # Fila top: icono + badge + ring
        top = QHBoxLayout()
        top.setSpacing(6)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setPixmap(self._icon_pixmap())
        icon_lbl.setStyleSheet("background: transparent;")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(icon_lbl)
        self._icon_lbl = icon_lbl
        top.addStretch()
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption"))
        self._badge.setStyleSheet("background: transparent;")
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(self._badge)
        self._ring = _MiniRing(self, self._accent)
        top.addWidget(self._ring)
        layout.addLayout(top)

        # Título
        title = QLabel(self._config["title"])
        title.setFont(qfont("size_h3", bold=True))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        title.setWordWrap(True)
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(title)
        self._title_lbl = title

        # Descripción
        desc = QLabel(self._config["desc"])
        desc.setFont(qfont("size_caption"))
        desc.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        desc.setWordWrap(True)
        desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        desc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(desc)
        self._desc_lbl = desc

        self._refresh_status()

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        c = colors(self._modo)
        if status:
            color = C("success", self._modo)
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

        # Barra izquierda con gradiente vertical teal -> violet
        bar_w = 5
        bar_grad = linear_gradient_vertical(
            QRectF(0, 0, bar_w, h),
            self._session.qcolor(self._modo, 180),
            self._session.qcolor(self._modo, 40),
        )
        bar = QPainterPath()
        bar.addRoundedRect(QRectF(0, 0, bar_w, h), r // 2, r // 2)
        p.fillPath(bar, QBrush(bar_grad))

        # Hover glow dinámico (session color)
        if self._hover and not self._disabled:
            glow_c = self._session.glow_qcolor(self._modo)
            glow_r = r + int(fx("card_glow_radius", self._modo))
            glow_opacity = float(fx("card_glow_opacity", self._modo))
            for layer in range(3):
                alpha = int(glow_c.alpha() * max(0.0, glow_opacity - layer * 0.08))
                if alpha <= 0:
                    continue
                gc = QColor(glow_c)
                gc.setAlpha(alpha)
                glow_pen = QPen(gc, max(1, int(fx("card_glow_radius", self._modo) / 3)) + layer * 2)
                p.setPen(glow_pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(
                    QRectF(1 - layer, 1 - layer,
                           self.width() - 2 + layer * 2,
                           self.height() - 2 + layer * 2),
                    glow_r, glow_r,
                )

        noise_overlay(
            p,
            QRectF(5, 0, w - 5, h),
            opacity=float(fx("noise_opacity", self._modo)),
            modo=self._modo,
        )
        if self._disabled:
            p.fillPath(path, QBrush(QColor(255, 255, 255, 80 if "light" in self._modo else 20)))
        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if not self._disabled and event.button() == Qt.MouseButton.LeftButton:
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self._disabled and event.button() == Qt.MouseButton.LeftButton:
            if self.rect().contains(event.pos()):
                self._on_click(self._config["id"])
        super().mouseReleaseEvent(event)

    def animate_enter(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
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

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _dot_color(self._idx, self._modo)
        c = colors(self._modo)
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._desc_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        self._icon_lbl.setPixmap(self._icon_pixmap())
        self._ring._color = self._accent
        self._ring.update()
        if self._eff is None or self._eff.opacity() >= 1.0:
            if self._eff is not None:
                self._eff.deleteLater()
                self._eff = None
            self.setGraphicsEffect(None)
        self._refresh_status()
        self.update()

    def _icon_pixmap(self):
        icon_key = "registro_tcc" if self._config["id"] == "registro" else self._config["id"]
        return nm_icon(icon_key, C("accent", self._modo), size=32).pixmap(32, 32)

    def refresh(self):
        self._refresh_status()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        self.setCursor(Qt.CursorShape.ForbiddenCursor if state else Qt.CursorShape.PointingHandCursor)
        self.update()


# ── HomeView ──────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    """Grid de 7 ModuleCard con grid responsive (1/2/3 columnas)."""

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
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._grid_cols = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area para overflow vertical
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(self._scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._scroll.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 20, 0, 20)
        container_layout.setSpacing(10)

        title_lbl = QLabel("Herramientas")
        title_lbl.setFont(qfont("size_h2", bold=True))
        title_lbl.setStyleSheet(f"color: {C('text_primary', self._modo)}; background: transparent;")
        container_layout.addWidget(title_lbl)

        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setVerticalSpacing(int(GAP_CARDS * 1.4))
        self._grid.setHorizontalSpacing(GAP_CARDS)
        container_layout.addLayout(self._grid)

        # Crear todas las cards
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = ModuleCard(
                cfg, idx, self._modo,
                on_click=self._open_cb,
                get_status_fn=self._get_status,
            )
            self._cards[cfg["id"]] = card

        self._rebuild_grid()

        # Animar entrada con stagger
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 60)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_cols = responsive_columns(self.width())
        if new_cols != self._grid_cols:
            self._grid_cols = new_cols
            self._rebuild_grid()

    def _rebuild_grid(self):
        cols = max(1, self._grid_cols or responsive_columns(self.width()))
        # Limpiar grid manteniendo los widgets
        for i in reversed(range(self._grid.count())):
            item = self._grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)

        # Reconfigurar columnas
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)

        # Reubicar cards en el nuevo grid
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                row = idx // cols
                col = idx % cols
                self._grid.addWidget(card, row, col)
        self._grid.setRowStretch(0, 1)

    def refresh_statuses(self):
        for card in self._cards.values():
            card.refresh()

    def _is_module_available(self, module_id: str) -> bool:
        permission_keys = {
            "rutina": "perm_checklist_manual",
            "actividades": "perm_checklist_activacion",
            "timer": "perm_temporizador_manual",
            "avisos": "perm_recordatorios_manual",
        }
        key = permission_keys.get(module_id)
        if not key:
            return True
        try:
            from shared.db import leer_config
            return leer_config(key, "1") != "0"
        except Exception:
            return True

    def set_modo(self, modo: str):
        self._apply_theme(modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        c = colors(self._modo)
        p.fillRect(self.rect(), QColor(c["bg_primary"]))
        p.end()
