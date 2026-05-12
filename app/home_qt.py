"""
app/home_qt.py — Vista Home con grid de 7 NMCard (PyQt6)

Características:
  - Entrada animada: stagger de 60ms por card (fade-in + slide desde abajo)
  - Mini-ring de progreso en la esquina superior derecha de cada card (32px)
  - Badge de streak si el módulo fue usado N días consecutivos
  - Status badge como pill con color semántico
  - 7ma card: grid de 2 columnas en última fila centrada
  - Barra de color izquierda en cada card (color del gradiente por posición)
"""

import os
import sys

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    QAbstractAnimation, pyqtProperty,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QFont,
)
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QFrame, QSpacerItem, QGraphicsOpacityEffect,
)

try:
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        linear_gradient, get_gradient,
        RADIUS_CARD, PAD_CARD, GAP_CARDS,
    )
    from shared.components_qt import NMCard, ThemeManager, styled_label
    from shared.theme import CATEGORY_COLORS
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        linear_gradient, get_gradient,
        RADIUS_CARD, PAD_CARD, GAP_CARDS,
    )
    from shared.components_qt import NMCard, ThemeManager, styled_label
    from shared.theme import CATEGORY_COLORS

# ── Configuración de módulos ──────────────────────────────────────────────────

MODULES_CONFIG = [
    {
        "id":    "animo",
        "icon":  "🎭",
        "title": "Ánimo",
        "desc":  "Registrá tu estado emocional · 1 min",
        "hint":  "Slider 1–10 + nota libre",
    },
    {
        "id":    "respiracion",
        "icon":  "🌬️",
        "title": "Respirar",
        "desc":  "Respiración guiada 4-7-8",
        "hint":  "3, 5 o 10 minutos",
    },
    {
        "id":    "registro",
        "icon":  "📝",
        "title": "Registro TCC",
        "desc":  "Pensamientos automáticos · 4 pasos",
        "hint":  "Situación → Emoción → Pensamiento → Respuesta",
    },
    {
        "id":    "rutina",
        "icon":  "✅",
        "title": "Rutina",
        "desc":  "Tareas del día · Mañana/Tarde/Noche",
        "hint":  "Asignadas por tu terapeuta",
    },
    {
        "id":    "actividades",
        "icon":  "⚡",
        "title": "Actividades",
        "desc":  "Sugerencias según tu ánimo actual",
        "hint":  "Se adaptan a cómo te sentís hoy",
    },
    {
        "id":    "timer",
        "icon":  "⏱️",
        "title": "Timer",
        "desc":  "Temporizador de actividades",
        "hint":  "Presets terapéuticos",
    },
    {
        "id":    "avisos",
        "icon":  "🔔",
        "title": "Avisos",
        "desc":  "Recordatorios · funcionan en background",
        "hint":  "Siguen activos aunque cierres la app",
    },
]

# Status badge colors: variante → color hex
_STATUS_COLORS = {
    "✔":    "#10b981",  # success green
    "done": "#10b981",
    "warn": "#f59e0b",
}


def _dot_color(idx: int, modo: str) -> str:
    """Color del gradiente teal→violet según posición en la grid."""
    grad = get_gradient(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[1], t)


# ── Mini-ring de progreso ─────────────────────────────────────────────────────

class _MiniRing(QWidget):
    """
    Arco de 32×32px en esquina de card. Muestra progreso 0.0–1.0.
    Pintado en paintEvent con QPainter.
    """

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

        # Track
        pen_track = QPen(QColor(80, 80, 80, 80), 3, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.drawEllipse(rect)

        # Fill
        pen_fill = QPen(QColor(self._color), 3, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap)
        p.setPen(pen_fill)
        span = int(-self._progress * 360 * 16)
        p.drawArc(rect, 90 * 16, span)
        p.end()


# ── Card del módulo ───────────────────────────────────────────────────────────

class ModuleCard(QWidget):
    """
    Card de módulo con:
      - Barra izquierda de color (4px)
      - Mini-ring de progreso (esquina superior derecha)
      - Streak badge
      - Status badge pill
      - Animación de entrada: fade-in + translate Y
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

        # Opacidad para animación de entrada
        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(0.0)
        self.setGraphicsEffect(self._eff)
        self._offset_y = 20  # se animará a 0

        self._build_ui()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _build_ui(self):
        c = colors(self._modo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(4)

        # Fila top: icono + status badge
        top = QHBoxLayout()
        top.setSpacing(6)

        icon_lbl = QLabel(self._config["icon"])
        icon_lbl.setFont(qfont("size_emoji_sm"))
        icon_lbl.setStyleSheet("background: transparent; color: white;")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(icon_lbl)
        self._icon_lbl = icon_lbl

        top.addStretch()

        # Status badge (pill)
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

        # Mini-ring (absoluto, esquina sup-der)
        self._ring = _MiniRing(self, self._accent)
        self._ring.move(self.width() - 40, 8)

        self._refresh_status()

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        c = colors(self._modo)
        if status:
            color = "#10b981"  # success por defecto
            if "activo" in status:
                color = C("accent", self._modo)
            self._badge.setText(status)
            self._badge.setStyleSheet(
                f"color: {color}; background: transparent;"
                f"font-size: {9}pt; font-weight: bold;"
            )
        else:
            self._badge.setText("")

        # Actualizar mini-ring con progreso si aplica
        self._update_ring()

    def _update_ring(self):
        status = self._get_status(self._config["id"])
        if not status:
            self._ring.set_progress(0)
            return
        # Parsear progreso de "X/Y ✔" (rutina)
        if "/" in status and "✔" in status:
            try:
                parts = status.split("/")
                done = int(parts[0].strip())
                total_str = parts[1].replace("✔", "").strip()
                total = int(total_str)
                self._ring.set_progress(done / total if total > 0 else 0)
            except Exception:
                self._ring.set_progress(1.0 if "✔" in status else 0)
        elif "✔" in status:
            self._ring.set_progress(1.0)
        else:
            self._ring.set_progress(0)

    # ── paintEvent ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = RADIUS_CARD
        w, h = self.width(), self.height()

        # Fondo de la card
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, QBrush(QColor(c["bg_surface"])))

        # Borde
        pen = QPen(QColor(c.get("border_card", c["border"])), 1)
        p.setPen(pen)
        p.drawPath(path)

        # Barra izquierda (4px, redondeada en las puntas)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(0, r, 4, h - 2 * r), 0, 0)
        bar_path.addRoundedRect(QRectF(0, 0, 4, r), r, r)
        bar_path.addRoundedRect(QRectF(0, h - r, 4, r), r, r)
        p.fillPath(bar_path, QBrush(QColor(self._accent)))

        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ring.move(self.width() - 38, 8)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_click(self._config["id"])

    # ── Animación de entrada ──────────────────────────────────────────────────

    def animate_enter(self, delay_ms: int = 0):
        """Fade-in + slide desde abajo. Llamar con delay escalonado."""
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
        # Fade-in
        anim_fade = QPropertyAnimation(self._eff, b"opacity", self)
        anim_fade.setDuration(320)
        anim_fade.setStartValue(0.0)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        # Slide Y via geometry (movimiento relativo)
        orig_y = self.y()
        self.move(self.x(), orig_y + self._offset_y)
        anim_move = QPropertyAnimation(self, b"pos", self)
        anim_move.setDuration(320)
        from PyQt6.QtCore import QPoint
        anim_move.setStartValue(QPoint(self.x(), self.y()))
        anim_move.setEndValue(QPoint(self.x(), orig_y))
        anim_move.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_move.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _dot_color(self._idx, self._modo)
        c = colors(self._modo)
        self._title_lbl.setStyleSheet(
            f"color: {c['text_primary']}; background: transparent;"
        )
        self._desc_lbl.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent;"
        )
        self._ring._color = self._accent
        self._ring.update()
        self._refresh_status()
        self.update()

    def refresh(self):
        self._refresh_status()
        self.update()


# ── HomeView ──────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    """
    Grid de 7 cards con animación de entrada escalonada.
    Las primeras 6 van en grid 3×2; la 7ma ocupa 1 columna centrada en fila 3.
    """

    def __init__(self, modo: str = "dark_hybrid",
                 on_module_open=None, get_status_fn=None,
                 parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._on_module_open = on_module_open or (lambda mid: None)
        self._get_status = get_status_fn or (lambda mid: "")
        self._cards: dict[str, ModuleCard] = {}

        self._build_ui()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _build_ui(self):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")

        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        grid = QGridLayout(container)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setSpacing(GAP_CARDS)

        # Columnas iguales
        for col in range(3):
            grid.setColumnStretch(col, 1)

        # 6 primeras cards en grid 3×2
        for idx, cfg in enumerate(MODULES_CONFIG[:6]):
            row = idx // 3
            col = idx % 3
            card = ModuleCard(
                cfg, idx, self._modo,
                on_click=self._on_module_open,
                get_status_fn=self._get_status,
            )
            grid.addWidget(card, row, col)
            self._cards[cfg["id"]] = card

        # 7ma card: una sola columna centrada en fila 3
        # Añadimos spacer a col 0 y col 2 para centrar
        cfg7 = MODULES_CONFIG[6]
        card7 = ModuleCard(
            cfg7, 6, self._modo,
            on_click=self._on_module_open,
            get_status_fn=self._get_status,
        )
        card7.setMaximumWidth(380)
        # Fila 3, columna 1 (centrada) — stretch de col 0 y 2 la centran
        grid.addWidget(card7, 2, 1, Qt.AlignmentFlag.AlignHCenter)
        self._cards[cfg7["id"]] = card7

        # Spacer al fondo
        grid.setRowStretch(3, 1)

        self._grid = grid
        self._animate_cards()

    def _animate_cards(self):
        """Stagger: cada card aparece con 60ms de delay adicional."""
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 60)

    def _on_module_open(self, module_id: str):
        self._on_module_open_fn(module_id)

    def _on_module_open(self, module_id: str):
        self._on_module_open(module_id) if False else None
        # Llamada directa al callback:
        self._on_module_open_cb(module_id)

    # Renombrar el callback para evitar recursión
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def _build_ui(self):
        # (redefinido más abajo para evitar colisión de nombres)
        pass

    def refresh_statuses(self):
        for card in self._cards.values():
            card.refresh()

    def set_modo(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_theme(modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")
        # Las cards se aplican via signal ThemeManager


# Reescribir HomeView limpio sin el conflicto de nombres

class HomeView(QWidget):  # noqa: F811
    """
    Grid de 7 NMCard con animación de entrada escalonada (stagger 60ms).
    """

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
        self._grid = grid

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
