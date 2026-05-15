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
from datetime import datetime

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
        linear_gradient, linear_gradient_vertical, rich_gradient, get_gradient, gradient_colors,
        noise_overlay, fx, aura_opacity,
        RADIUS_CARD, PAD_CARD, PAD_CONTAINER, GAP_CARDS,
        stylesheet_scrollarea, SessionColor, ThemeAwareWidgetMixin,
        MODULE_ICONS, nm_icon,
    )
    from shared.components_qt import (
        ThemeManager, responsive_columns, NMStreakBadge, NMWelcomeBar,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        linear_gradient, linear_gradient_vertical, rich_gradient, get_gradient, gradient_colors,
        noise_overlay, fx, aura_opacity,
        RADIUS_CARD, PAD_CARD, PAD_CONTAINER, GAP_CARDS,
        stylesheet_scrollarea, SessionColor, ThemeAwareWidgetMixin,
        MODULE_ICONS, nm_icon,
    )
    from shared.components_qt import (
        ThemeManager, responsive_columns, NMStreakBadge, NMWelcomeBar,
    )

# ── Configuración de módulos ──────────────────────────────────────────────────

MODULES_CONFIG = [
    {"id": "animo",       "icon": "animo",       "title": "Ánimo",
     "desc": "Registrá tu estado emocional · 1 min"},
    {"id": "respiracion", "icon": "respiracion", "title": "Respirar",
     "desc": "Respiración guiada 4-7-8 · 3/5/10 min"},
    {"id": "registro",    "icon": "registro_tcc","title": "Registro TCC",
     "desc": "Pensamientos automáticos · 4 pasos"},
    {"id": "rutina",      "icon": "rutina",      "title": "Rutina",
     "desc": "Tareas del día · Mañana/Tarde/Noche"},
    {"id": "actividades", "icon": "actividades", "title": "Actividades",
     "desc": "Sugerencias según tu ánimo actual"},
    {"id": "timer",       "icon": "timer",       "title": "Timer",
     "desc": "Temporizador de actividades"},
    {"id": "avisos",      "icon": "avisos",      "title": "Avisos",
     "desc": "Recordatorios · funcionan en background"},
]


def _dot_color(idx: int, modo: str) -> str:
    """Color del gradiente teal→violet según posición del módulo."""
    grad = gradient_colors(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[-1], t)


# ── Mini-ring de progreso ─────────────────────────────────────────────────────

class _MiniRing(QWidget):
    """Arco de 28×28px que muestra progreso 0.0–1.0 (mockup: svg 28x28 r=10)."""

    def __init__(self, parent=None, color: str = "#6366f1", modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._progress = 0.0
        self._color = color
        self._modo = norm_modo(modo)
        self.setFixedSize(28, 28)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

    def set_progress(self, v: float):
        self._progress = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = 10
        cx, cy = 14, 14
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        track = QColor(C("progress_track", self._modo))
        track.setAlpha(130 if "dark" in self._modo else 190)
        pen_track = QPen(track, 3, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.drawEllipse(rect)
        if self._progress <= 0:
            p.end()
            return
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
        layout.setContentsMargins(PAD_CARD + 3, 14, PAD_CARD, 14)
        layout.setSpacing(8)

        # Fila top: icono + badge + ring
        top = QHBoxLayout()
        top.setSpacing(6)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setPixmap(self._icon_pixmap())
        icon_lbl.setStyleSheet("background: transparent;")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(icon_lbl)
        self._icon_lbl = icon_lbl
        top.addStretch()
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption", bold=True))
        self._badge.setStyleSheet("background: transparent;")
        self._badge.setContentsMargins(6, 2, 6, 2)
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top.addWidget(self._badge)
        self._ring = _MiniRing(self, self._accent, self._modo)
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

    def _pill_style(self, color_hex: str, alpha_bg: float = 0.14) -> str:
        """Genera stylesheet de pill badge con fondo semitransparente."""
        c = QColor(color_hex)
        bg_r, bg_g, bg_b = c.red(), c.green(), c.blue()
        a = int(alpha_bg * 255)
        return (
            f"color: {color_hex}; "
            f"background-color: rgba({bg_r},{bg_g},{bg_b},{a}); "
            f"border-radius: 10px; "
            f"padding: 2px 7px; "
            f"font-size: 10pt;"
        )

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        if self._disabled:
            self._badge.setText("No disponible")
            self._badge.setStyleSheet(
                self._pill_style(C("warning", self._modo))
            )
            self._ring.set_progress(0)
            return
        if status:
            mid = self._config["id"]
            if mid == "avisos":
                color = C("warning", self._modo)
            elif "✓" in status or "Listo" in status or "Completo" in status:
                color = C("success", self._modo)
            elif "/" in status:
                color = C("teal", self._modo)
            else:
                color = C("accent", self._modo)
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
            self._ring.set_progress(0)
            return
        clean = status.replace("✓", "").replace("✔", "").replace("âœ”", "").strip()
        if "/" in clean:
            try:
                parts = clean.split("/")
                done = int(parts[0].strip())
                total = int(parts[1].strip().split()[0])
                self._ring.set_progress(done / total if total > 0 else 0)
            except Exception:
                self._ring.set_progress(0)
        elif self._config["id"] != "avisos":
            self._ring.set_progress(1.0)
        else:
            self._ring.set_progress(0)
        return

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

        # Barra izquierda 3px con gradiente (mockup: .mod-accent width:3px)
        bar_w = 3
        bar_grad = rich_gradient(QRectF(0, 0, bar_w, h), self._modo, angle=90)
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
            QRectF(3, 0, w - 3, h),
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
        self._ring._modo = self._modo
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
        return nm_icon(icon_key, C("accent", self._modo), size=24).pixmap(24, 24)

    def refresh(self):
        self._refresh_status()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        self.setCursor(Qt.CursorShape.ForbiddenCursor if state else Qt.CursorShape.PointingHandCursor)
        self._refresh_status()
        self.update()


# ── HomeView ──────────────────────────────────────────────────────────────────

class HomeView(QWidget):
    """Grid de 7 ModuleCard con grid responsive (1/2/3 columnas)."""

    def __init__(self, modo: str = "dark_hybrid",
                 on_module_open=None, get_status_fn=None, username: str = "",
                 parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._open_cb = on_module_open or (lambda mid: None)
        self._get_status = get_status_fn or (lambda mid: "")
        self._username = username
        self._cards: dict[str, ModuleCard] = {}
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _setup(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._grid_cols  = 0
        self._session    = SessionColor.instance()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(PAD_CONTAINER, 18, PAD_CONTAINER + 10, 10)
        header_layout.setSpacing(4)

        # Fila: título + streak badge
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self._title_lbl = QLabel("Herramientas")
        self._title_lbl.setFont(qfont("size_h2", bold=True))
        self._title_lbl.setStyleSheet(f"color: {C('text_primary', self._modo)}; background: transparent;")
        title_row.addWidget(self._title_lbl)
        self._streak_badge = NMStreakBadge(self._load_streak(), self._modo)
        title_row.addWidget(self._streak_badge)
        title_row.addStretch()
        header_layout.addLayout(title_row)

        # Welcome bar (saludo + fecha)
        self._welcome_bar = NMWelcomeBar(self._modo)
        header_layout.addWidget(self._welcome_bar)

        outer.addWidget(header)

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
        container_layout.setContentsMargins(PAD_CONTAINER, 8, PAD_CONTAINER + 14, 24)
        container_layout.setSpacing(10)

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
        self._sync_availability()

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

    def _load_streak(self) -> int:
        """Calcula los días consecutivos con al menos un registro de ánimo."""
        try:
            from shared.db import obtener_conexion
            import datetime as dt
            con = obtener_conexion()
            cur = con.execute(
                "SELECT DISTINCT date(fecha) AS d FROM registros_animo "
                "ORDER BY d DESC LIMIT 30"
            )
            rows = [r["d"] for r in cur.fetchall()]
            if not rows:
                return 0
            today = dt.date.today()
            streak = 0
            for i, d_str in enumerate(rows):
                expected = today - dt.timedelta(days=i)
                if str(expected) == d_str:
                    streak += 1
                else:
                    break
            return streak
        except Exception:
            return 0

    def _greeting_text(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            prefix = "Buenos dias"
        elif hour < 20:
            prefix = "Buenas tardes"
        else:
            prefix = "Buenas noches"
        name = (self._username or "Paciente").strip() or "Paciente"
        return f"{prefix}, {name}"

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
                if cols == 3 and idx == len(MODULES_CONFIG) - 1 and len(MODULES_CONFIG) % cols == 1:
                    col = 1
                self._grid.addWidget(card, row, col)
        self._grid.setRowStretch(0, 1)

    def refresh_statuses(self):
        self._sync_availability()
        for card in self._cards.values():
            card.refresh()

    def _disabled_reason(self, module_id: str) -> str:
        reasons = {
            "rutina": "Tu profesional desactivo la rutina manual.",
            "actividades": "Tu profesional desactivo las actividades manuales.",
            "timer": "Tu profesional desactivo el temporizador manual.",
            "avisos": "Tu profesional desactivo los recordatorios manuales.",
        }
        return reasons.get(module_id, "Modulo no disponible.")

    def _sync_availability(self):
        for module_id, card in self._cards.items():
            available = self._is_module_available(module_id)
            card.set_disabled(not available, self._disabled_reason(module_id) if not available else "")

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
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._title_lbl.setStyleSheet(f"color: {C('text_primary', self._modo)}; background: transparent;")
        self._welcome_bar._apply_theme(self._modo)
        self._streak_badge._apply_theme(self._modo)
        for card in self._cards.values():
            card._apply_theme(self._modo)
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QRadialGradient
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        p.fillRect(self.rect(), QColor(c["bg_primary"]))
        # SessionColor aura radial (centro-izquierda)
        w, h  = self.width(), self.height()
        alpha = int(aura_opacity(self._modo) * 255)
        aura_c = self._session.qcolor(self._modo, alpha)
        aura = QRadialGradient(QPointF(w * 0.18, h * 0.50), w * 0.85)
        aura.setColorAt(0.0, aura_c)
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), aura)
        p.end()
